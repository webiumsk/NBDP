"""Source-prepared, read-only E02 supplementary evidence checker; never E02 PASS.

Exact external review hashes and actual independent review are the authenticity
boundary. This code checks consistency; it cannot manufacture Android witnesses.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import stat
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
DATA_LIMIT = 16 * 1024 * 1024
FILE_LIMIT = 512 * 1024 * 1024
SAFE = 9007199254740991
CLIENT_COMMIT = 'e6f464a1179def75274512b3c5bab921de3bf3d8'
CLIENT_APK = (165860063, '5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5')
A = '79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
B = 'c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5'
MATRIX = set(itertools.product(('js-to-rust', 'rust-to-js'), ('incoming', 'archive'), ('strfry', 'rs-relay')))


class Refusal(ValueError):
    pass


class Mismatch(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refusal(message)


def equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def closed(value, fields):
    need(type(value) is dict and set(value) == set(fields.split()), 'CLOSED_KEYS')


def integer(value, low=0, high=SAFE):
    need(type(value) is int and low <= value <= high, 'SAFE_INTEGER')


def text(value, maximum=65536):
    need(type(value) is str and len(value.encode('utf-8', 'strict')) <= maximum, 'BOUNDED_TEXT')


def hex64(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'HEX64')


def loads(raw):
    need(type(raw) is bytes and len(raw) <= DATA_LIMIT, 'DATA_BOUND')
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def number(token):
        need(token != '-0', 'NEGATIVE_ZERO')
        value = int(token)
        integer(value, -SAFE)
        return value
    def fraction(_):
        raise Refusal('INTEGER_JSON_ONLY')
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                       parse_int=number, parse_float=fraction, parse_constant=fraction)
    todo = [(value, 0)]
    count = 0
    while todo:
        item, depth = todo.pop()
        count += 1
        need(depth <= 48 and count <= 100000, 'JSON_STRUCTURE_BOUND')
        if type(item) is str:
            item.encode('utf-8', 'strict')
        elif type(item) is dict:
            todo.extend((x, depth + 1) for x in [*item.keys(), *item.values()])
        elif type(item) is list:
            todo.extend((x, depth + 1) for x in item)
    return value


class Files:
    """Remember original pins, stream large inputs, never refresh after drift."""
    def __init__(self):
        self.pins = {}
        self.bytes = 0

    def checked(self, descriptor, data=False):
        closed(descriptor, 'path bytes sha256')
        integer(descriptor['bytes'], 0, DATA_LIMIT if data else FILE_LIMIT)
        hex64(descriptor['sha256'])
        path = Path(descriptor['path'])
        need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'CANONICAL_FILE')
        previous = self.pins.get(str(path))
        need(previous is None or equal(previous, descriptor), 'CONFLICTING_ORIGINAL_PIN')
        need(len(self.pins) < 2048 or previous is not None, 'FILE_INVENTORY_BOUND')
        need(previous is not None or self.bytes + descriptor['bytes'] <= 2 * 1024 ** 3, 'TOTAL_INPUT_BOUND')
        h = hashlib.sha256()
        count = 0
        chunks = []
        with path.open('rb') as handle:
            before = os.fstat(handle.fileno())
            need(stat.S_ISREG(before.st_mode) and before.st_size == descriptor['bytes'], 'FILE_TYPE_SIZE')
            for chunk in iter(lambda: handle.read(1048576), b''):
                h.update(chunk)
                count += len(chunk)
                if data:
                    chunks.append(chunk)
            after = os.fstat(handle.fileno())
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        need(identity(before) == identity(after) and count == descriptor['bytes']
             and h.hexdigest() == descriptor['sha256'], 'ORIGINAL_FILE_DRIFT')
        if previous is None:
            self.bytes += descriptor['bytes']
        self.pins[str(path)] = dict(descriptor)
        return b''.join(chunks) if data else descriptor

    def doc(self, descriptor):
        return loads(self.checked(descriptor, data=True))

    def external(self, path, sha):
        hex64(sha)
        p = Path(path)
        d = dict(path=str(p), bytes=p.stat().st_size, sha256=sha)
        self.checked(d, data=True)
        return d

    def current(self):
        for descriptor in list(self.pins.values()):
            self.checked(descriptor)


def rumor(value):
    closed(value, 'id pubkey created_at kind tags content')
    hex64(value['id'])
    hex64(value['pubkey'])
    integer(value['created_at'])
    need(value['kind'] == 14 and type(value['kind']) is int, 'INNER_KIND14_ONLY')
    text(value['content'])
    need(type(value['tags']) is list and len(value['tags']) <= 64, 'RUMOR_TAGS')
    for tag in value['tags']:
        need(type(tag) is list and 1 <= len(tag) <= 8, 'TAG_SHAPE')
        for part in tag:
            text(part)
    array = [0, value['pubkey'], value['created_at'], value['kind'], value['tags'], value['content']]
    raw = json.dumps(array, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    need(hashlib.sha256(raw).hexdigest() == value['id'], 'RECOMPUTED_INNER_ID')
    return value


def client_export(value):
    """Normalize only the pinned client's optional empty unsigned signature."""
    need(type(value) is dict, 'CLIENT_EXPORT_OBJECT')
    if 'sig' in value:
        closed(value, 'id pubkey created_at kind tags content sig')
        need(type(value['sig']) is str and value['sig'] == '', 'CLIENT_EXPORT_EMPTY_SIGNATURE_ONLY')
        value = {key: part for key, part in value.items() if key != 'sig'}
    return rumor(value)


def client(value, files):
    closed(value, 'commit apk package versionName versionCode')
    need(value['commit'] == CLIENT_COMMIT and value['package'] == 'com.vitorpamplona.amethyst.debug'
         and value['versionName'] == '1.17.0-DEBUG' and type(value['versionCode']) is int
         and value['versionCode'] == 462, 'EXACT_PINNED_CLIENT')
    need((value['apk']['bytes'], value['apk']['sha256']) == CLIENT_APK, 'EXACT_CLIENT_APK')
    files.checked(value['apk'])


def prerequisites(value, files):
    closed(value, 'E01 E02')
    for name, count, status in [('E01', 140, 'PASS'), ('E02', 22, 'PARTIAL')]:
        pin = value[name]
        need(pin['path'] == str(ROOT / 'experiments/results' / (name + '.json')), 'FIXED_CANONICAL_PREREQUISITE')
        # Historical machine records contain fractional timings; they remain opaque
        # hash-bound records rather than being accepted by the integer-only reader.
        raw = files.checked(pin, data=True)
        record = json.loads(raw)
        need(record['experiment'] == name and record['status'] == status and record['exit_status'] == 0
             and len(record['tests']) == count and all(row['ok'] is True for row in record['tests']), 'CURRENT_CANONICAL_SCOPE')
        mandatory = [row for row in record['skipped'] if row['mandatory'] is True]
        need((not mandatory) if name == 'E01' else
             len(mandatory) == 1 and mandatory[0]['scope'] == 'Amethyst ordinary-client rendering', 'MANDATORY_SCOPE_RETAINED')
        for relative, sha in record['source_sha256'].items():
            path = ROOT / 'experiments' / relative
            need(path.resolve(strict=True).is_relative_to(ROOT / 'experiments'), 'PREREQUISITE_SOURCE_PATH')
            files.checked(dict(path=str(path), bytes=path.stat().st_size, sha256=sha))
        binary = Path(record['environment']['rust_binary'])
        binary = binary if binary.is_absolute() else ROOT / 'experiments' / binary
        files.checked(dict(path=str(binary), bytes=binary.stat().st_size,
                           sha256=record['environment']['rust_binary_sha256']))


def inspect_plan(plan, files):
    closed(plan, 'schema runId operator authors client sources prerequisites runConfig runRelease expected')
    need(plan['schema'] == 'e02-ordinary-plan-v1', 'PLAN_SCHEMA')
    text(plan['runId'], 96)
    need(re.fullmatch('[a-z0-9][a-z0-9_-]{0,95}', plan['runId']) is not None, 'RUN_ID')
    text(plan['operator'], 256)
    need(type(plan['authors']) is list and 1 <= len(plan['authors']) <= 16, 'AUTHORS')
    for name in plan['authors']:
        text(name, 256)
    client(plan['client'], files)
    prerequisites(plan['prerequisites'], files)
    need(type(plan['sources']) is list and 1 <= len(plan['sources']) <= 256, 'SOURCE_CLOSURE')
    for pin in plan['sources']:
        files.checked(pin)
    for key in ('runConfig', 'runRelease'):
        files.doc(plan[key])
    need(type(plan['expected']) is list and len(plan['expected']) == 8, 'REVIEWED_EIGHT_ROW_SCOPE')
    triples = set()
    ids = set()
    for row in plan['expected']:
        closed(row, 'id direction role relay account peer rumor visibleToken dispatch')
        text(row['id'], 96)
        need(re.fullmatch('[a-z0-9][a-z0-9_-]{0,95}', row['id']) is not None and row['id'] not in ids, 'UNIQUE_OBSERVATION_ID')
        ids.add(row['id'])
        triple = (row['direction'], row['role'], row['relay'])
        need(triple in MATRIX and triple not in triples, 'UNIQUE_MATRIX_CELL')
        triples.add(triple)
        sender, recipient = (A, B) if row['direction'] == 'js-to-rust' else (B, A)
        account, peer = (recipient, sender) if row['role'] == 'incoming' else (sender, recipient)
        need((row['account'], row['peer']) == (account, peer) and type(row['dispatch']) is bool
             and row['dispatch'] == (row['role'] == 'incoming'), 'EXACT_DISPOSABLE_ROLE')
        expected = rumor(files.doc(row['rumor']))
        recipients = [tag[1] for tag in expected['tags'] if tag[0] == 'p' and len(tag) >= 2]
        body = loads(expected['content'].encode('utf-8'))
        need(expected['pubkey'] == sender and recipients == [recipient]
             and type(body) is dict and body.get('protocol') == 'NBDP/experiment'
             and body.get('from') == sender and body.get('to') == recipient, 'BUSINESS_ENVELOPE_EXPECTED')
        text(row['visibleToken'], 256)
        need(len(row['visibleToken']) >= 8 and row['visibleToken'] in expected['content'], 'EXPECTED_VISIBLE_TOKEN')
    need(triples == MATRIX, 'EXACT_REVIEWED_MATRIX')


def inspect_observation(row, expected, files):
    closed(row, 'id status transport selection uiPng uiXml rawClientRumor error')
    need(row['id'] == expected['id'] and row['status'] in ('COMPLETE', 'PARTIAL', 'FAILED'), 'OBSERVATION_SCOPE_STATUS')
    if row['error'] is not None:
        text(row['error'], 4096)
    if row['status'] != 'COMPLETE':
        for key in ('transport', 'selection', 'uiPng', 'uiXml', 'rawClientRumor'):
            if row[key] is not None:
                files.checked(row[key])
        return row['status']
    need(row['error'] is None, 'COMPLETE_WITHOUT_ERROR')
    original = rumor(files.doc(expected['rumor']))
    retained = client_export(files.doc(row['rawClientRumor']))
    if not equal(original, retained):
        raise Mismatch('ACTUAL_CLIENT_RETAINED_RUMOR_DIFFERS')
    proof = files.doc(row['transport'])
    closed(proof, 'schema frame wire jsRequest rustRequest jsResult rustResult')
    need(proof['schema'] == 'e02-ordinary-transport-v1', 'TRANSPORT_SCHEMA')
    frame = files.doc(proof['frame'])
    wire = files.doc(proof['wire'])
    need(type(frame) is list and len(frame) == 3 and frame[0] == 'EVENT'
         and type(frame[1]) is str and bool(frame[1]) and equal(frame[2], wire), 'ACTUAL_RECEIVED_EVENT_JOIN')
    need(type(wire) is dict and wire.get('kind') == 1059 and wire.get('tags') == [['p', expected['account']]], 'ACTUAL_DELIVERY_RECIPIENT')
    wire_text = files.checked(proof['wire'], data=True).decode('utf-8', 'strict')
    request = dict(op='validate', wire=wire_text,
                   secret=('0' * 63) + ('1' if expected['account'] == A else '2'),
                   role=expected['role'], expectedSender=original['pubkey'])
    need(equal(files.doc(proof['jsRequest']), request)
         and equal(files.doc(proof['rustRequest']), request), 'BOTH_ACTUAL_REQUEST_WIRE_ROLE_JOIN')
    js = files.doc(proof['jsResult'])
    rust = files.doc(proof['rustResult'])
    need(equal(js, rust) and js.get('ok') is True and equal(js.get('decrypts'), [1, 1]), 'BOTH_ACTUAL_VALIDATION_RESULTS')
    value = js['value']
    need(equal(value.get('rumor'), original) and value.get('role') == expected['role']
         and type(value.get('dispatch')) is bool and value['dispatch'] == expected['dispatch'], 'ACTUAL_VALIDATED_INNER_AND_ROLE')
    selection = files.doc(row['selection'])
    closed(selection, 'schema observationId account peer rumorId action method helperPackage helperArtifact helperReceipt capturedMonotonicNs')
    need(selection['schema'] == 'e02-ordinary-selection-v1' and selection['observationId'] == row['id']
         and (selection['account'], selection['peer']) == (expected['account'], expected['peer'])
         and selection['rumorId'] == original['id'] and selection['action'] == 'COPY_RAW_JSON'
         and selection['method'] == 'ANDROID_LOCAL_FOREGROUND'
         and selection['helperPackage'] == 'org.nbdp.clipboard.capture', 'ACTUAL_SELECTED_NOTE_JOIN')
    integer(selection['capturedMonotonicNs'], 1)
    files.checked(selection['helperArtifact'])
    receipt = files.doc(selection['helperReceipt'])
    closed(receipt, 'schema caseId action status mime bytes sha256 elapsedRealtimeNanos foregroundFocus wallClockMillis clipboardItemCount clipboardTimestamp')
    need(receipt['schema'] == 'e02-clipboard-capture-v1' and receipt['caseId'] == row['id']
         and receipt['action'] == 'CAPTURE' and receipt['status'] == 'CAPTURED'
         and receipt['mime'] == 'text/plain' and receipt['foregroundFocus'] is True
         and type(receipt['clipboardItemCount']) is int and receipt['clipboardItemCount'] == 1
         and receipt['bytes'] == row['rawClientRumor']['bytes']
         and receipt['sha256'] == row['rawClientRumor']['sha256'], 'HELPER_RAW_BYTES_RECEIPT_JOIN')
    for key in ('bytes', 'elapsedRealtimeNanos', 'wallClockMillis', 'clipboardTimestamp'):
        integer(receipt[key], 1 if key == 'elapsedRealtimeNanos' else 0)
    need(receipt['bytes'] <= 65536, 'HELPER_RAW_BOUND')
    png = files.checked(row['uiPng'], data=True)
    need(png.startswith(b'\x89PNG\r\n\x1a\n') and len(png) >= 33, 'PNG_CAPTURE_FORMAT_ONLY')
    xml = files.checked(row['uiXml'], data=True)
    need(b'<!DOCTYPE' not in xml and b'<!ENTITY' not in xml, 'NO_XML_ENTITIES')
    tree = ET.fromstring(xml)
    need(tree.tag == 'hierarchy', 'ANDROID_HIERARCHY')
    labels = [part for node in tree.iter() for key, part in node.attrib.items() if key in ('text', 'content-desc')]
    if not any(expected['visibleToken'] in part for part in labels):
        raise Mismatch('EXPECTED_RENDERED_CONTENT_TOKEN_ABSENT')
    return 'COMPLETE'


def inspect_capture(plan, plan_pin, capture, files):
    closed(capture, 'schema runId operator plan client executionState runConfig runRelease driverReceipt observations')
    need(capture['schema'] == 'e02-ordinary-capture-v1' and capture['runId'] == plan['runId']
         and capture['operator'] == plan['operator'] and equal(capture['plan'], plan_pin)
         and equal(capture['client'], plan['client']), 'EXACT_PLAN_CLIENT_OPERATOR')
    for key in ('runConfig', 'runRelease'):
        need(equal(capture[key], plan[key]), 'SAME_EXACT_RUN_AUTHORITY')
    receipt = files.doc(capture['driverReceipt'])
    need(type(receipt) is dict and receipt.get('runId') == plan['runId']
         and equal(receipt.get('runConfig'), plan['runConfig'])
         and equal(receipt.get('runRelease'), plan['runRelease']), 'PINNED_DRIVER_AUTHORITY_JOIN')
    need(capture['executionState'] in ('COMPLETE', 'PARTIAL', 'FAILED', 'NOT_EXECUTED')
         and type(capture['observations']) is list and len(capture['observations']) <= 8, 'CAPTURE_EXECUTION_STATE')
    expected = {row['id']: row for row in plan['expected']}
    seen = set()
    used = set()
    completed = []
    failed = []
    for row in capture['observations']:
        need(type(row) is dict and row.get('id') in expected and row['id'] not in seen, 'UNIQUE_CAPTURED_PLAN_ID')
        seen.add(row['id'])
        for key in ('transport', 'selection', 'uiPng', 'uiXml', 'rawClientRumor'):
            if row.get(key) is not None:
                path = row[key]['path']
                need(path not in used, 'DISTINCT_OWNED_OBSERVATION_ARTIFACT_PATHS')
                used.add(path)
        state = inspect_observation(row, expected[row['id']], files)
        if state == 'COMPLETE':
            completed.append(row['id'])
        elif state == 'FAILED':
            failed.append(row['id'])
    ordered = [row['id'] for row in plan['expected'] if row['id'] in seen]
    need(ordered == [row['id'] for row in capture['observations']], 'PLAN_OBSERVATION_ORDER')
    missing = [row['id'] for row in plan['expected'] if row['id'] not in completed]
    need(capture['executionState'] != 'NOT_EXECUTED' or not seen, 'NO_EXECUTION_MEANS_NO_OBSERVATIONS')
    need(capture['executionState'] != 'COMPLETE' or not missing, 'NO_FALSE_COMPLETE_SCOPE')
    if failed or capture['executionState'] == 'FAILED':
        status = 'FAIL'
    elif capture['executionState'] == 'PARTIAL':
        status = 'PARTIAL'
    else:
        status = 'NOT_EXECUTED' if not seen else ('PARTIAL' if missing else 'MATCHED_SUPPLEMENT_ONLY')
    return dict(status=status, matchedObservationIds=completed, failedObservationIds=failed,
                missingObservationIds=missing, canonicalE02Changed=False,
                meaning='Supplement consistency only; no canonical PASS or runtime authenticity from hashes alone.')


def actual_reviews(plan, plan_pin, capture, capture_pin, reviews, files):
    need(len(reviews) == 2, 'TWO_ACTUAL_REVIEWS')
    sessions = set()
    roles = set()
    for role, pin in reviews:
        review = files.doc(pin)
        closed(review, 'schema role session decision plan subject acceptedObservationIds findings')
        need(review['schema'] == 'e02-ordinary-observation-review-v1' and review['role'] == role
             and review['decision'] == 'ACCEPT_ORDINARY_CLIENT_OBSERVATIONS_ONLY'
             and equal(review['plan'], plan_pin) and equal(review['subject'], capture_pin)
             and equal(review['acceptedObservationIds'], [row['id'] for row in capture['observations']])
             and review['findings'] == [], 'EXACT_ACTUAL_REVIEW_SUBJECT_AND_SCOPE')
        text(review['session'], 256)
        need(review['session'] not in plan['authors'] and review['session'] != plan['operator']
             and review['session'] not in sessions and role not in roles, 'INDEPENDENT_NONAUTHOR_NONOPERATOR_REVIEW')
        sessions.add(review['session'])
        roles.add(role)
    need(roles == {'qa', 'security'}, 'DISTINCT_QA_SECURITY_ROLES')


def main(argv):
    need(len(argv) == 9, 'CLI PLAN PLAN_SHA CAPTURE CAPTURE_SHA QA_REVIEW QA_SHA SECURITY_REVIEW SECURITY_SHA')
    files = Files()
    plan_pin, capture_pin, qa, security = [files.external(argv[i], argv[i + 1]) for i in (1, 3, 5, 7)]
    plan, capture = files.doc(plan_pin), files.doc(capture_pin)
    inspect_plan(plan, files)
    actual_reviews(plan, plan_pin, capture, capture_pin, [('qa', qa), ('security', security)], files)
    result = inspect_capture(plan, plan_pin, capture, files)
    files.current()
    print(json.dumps(dict(schema='e02-ordinary-supplement-result-v1', plan=plan_pin,
                         capture=capture_pin, **result), separators=(',', ':')))
    return 0 if result['status'] == 'MATCHED_SUPPLEMENT_ONLY' else (1 if result['status'] == 'FAIL' else 2)


if __name__ == '__main__':
    try:
        code = main(sys.argv)
    except Mismatch as exc:
        print(json.dumps(dict(status='FAIL', error=str(exc), canonicalE02Changed=False)))
        code = 1
    except (Refusal, OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        print(json.dumps(dict(status='QUALIFICATION_REFUSED', error=str(exc)[:4096], canonicalE02Changed=False)))
        code = 2
    raise SystemExit(code)
