"""SOURCE ONLY: read-only, externally reviewed multi-run E02 supplement adapter.

No experiment activation, canonical writes or project imports at module load.
New normalized witnesses are proposed contracts, never claims about old records.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import types
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
CONSUMER = ROOT / 'experiments/prototypes/e02_ordinary_control_evidence_v1/consumer.py'
SAFE = 9007199254740991
I64 = 9223372036854775807
TIME_FIELDS = {'notAfterUtcNs', 'issuedUtcNs', 'deadlineUtcNs', 'issuedMonoNs',
               'deadlineMonoNs', 'issuedBootNs', 'deadlineBootNs'}
MATRIX = {(direction, role, relay) for direction in ('js-to-rust', 'rust-to-js')
          for role in ('incoming', 'archive') for relay in ('rs-relay', 'strfry')}


class Refusal(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refusal(message)


def closed(value, fields):
    need(type(value) is dict and set(value) == set(fields.split()), 'CLOSED_KEYS')


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def text(value, maximum=4096):
    need(type(value) is str and 0 < len(value.encode('utf-8', 'strict')) <= maximum, 'BOUNDED_NONEMPTY_TEXT')


def integer(value, maximum=SAFE, minimum=0):
    need(type(value) is int and minimum <= value <= maximum, 'INTEGER_BOUND')


def loads_metadata(raw):
    """Signed64 only in the seven named runtime metadata time fields.

    Never used for wire, rumor, helper, selection or v1 observation JSON.
    """
    need(type(raw) is bytes and len(raw) <= 16 * 1024 ** 2, 'METADATA_DATA_BOUND')
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'DUPLICATE_JSON_KEY')
            value[key] = item
        return value
    def number(token):
        need(token != '-0', 'NEGATIVE_ZERO')
        value = int(token)
        need(-I64 <= value <= I64, 'SIGNED64_BOUND')
        return value
    def fraction(_):
        raise Refusal('INTEGER_JSON_ONLY')
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                       parse_int=number, parse_float=fraction, parse_constant=fraction)
    todo, count = [(value, None, 0)], 0
    while todo:
        item, field, depth = todo.pop()
        count += 1
        need(depth <= 48 and count <= 100000, 'JSON_STRUCTURE_BOUND')
        if type(item) is int:
            integer(item, I64 if field in TIME_FIELDS else SAFE, -I64 if field in TIME_FIELDS else -SAFE)
        elif type(item) is str:
            item.encode('utf-8', 'strict')
        elif type(item) is dict:
            todo.extend((part, key, depth + 1) for key, part in item.items())
            todo.extend((key, None, depth + 1) for key in item)
        elif type(item) is list:
            todo.extend((part, None, depth + 1) for part in item)
    return value


def load_consumer(pin):
    """Execute only exact verified bytes of the fixed, unchanged v1 validator."""
    closed(pin, 'path bytes sha256')
    need(pin['path'] == str(CONSUMER), 'FIXED_V1_CONSUMER_PATH')
    integer(pin['bytes'], 16 * 1024 ** 2)
    need(type(pin['sha256']) is str and re.fullmatch('[a-f0-9]{64}', pin['sha256']), 'SHA256')
    path = CONSUMER
    need(path.resolve(strict=True) == path and not path.is_symlink(), 'CANONICAL_CONSUMER')
    with path.open('rb') as handle:
        before = os.fstat(handle.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size == pin['bytes'], 'CONSUMER_TYPE_SIZE')
        raw = handle.read(16 * 1024 ** 2 + 1)
        after = os.fstat(handle.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(identity(before) == identity(after) and len(raw) == pin['bytes']
         and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'CONSUMER_DRIFT')
    module = types.ModuleType('e02_aggregate_pinned_v1_consumer')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


class Budget:
    """Preserve v1 per-run bounds; additionally bound the entire union of runs."""
    def __init__(self):
        self.pins, self.bytes = {}, 0

    def admit(self, pin):
        closed(pin, 'path bytes sha256')
        integer(pin['bytes'], 512 * 1024 ** 2)
        previous = self.pins.get(pin['path'])
        need(previous is None or same(previous, pin), 'CONFLICTING_AGGREGATE_ORIGINAL_PIN')
        if previous is None:
            need(len(self.pins) < 16384 and self.bytes + pin['bytes'] <= 2 * 1024 ** 3,
                 'AGGREGATE_FILE_BYTE_BOUND')
            self.pins[pin['path']] = dict(pin)
            self.bytes += pin['bytes']


def file_reader(consumer, budget):
    class RunFiles(consumer.Files):
        def checked(self, descriptor, data=False):
            budget.admit(descriptor)
            return super().checked(descriptor, data=data)
    return RunFiles()


def metadata(files, pin):
    return loads_metadata(files.checked(pin, data=True))


def checked_list(files, rows, maximum=256):
    need(type(rows) is list and 1 <= len(rows) <= maximum, 'BOUNDED_PIN_LIST')
    paths = set()
    for pin in rows:
        files.checked(pin)
        need(pin['path'] not in paths, 'UNIQUE_PIN_PATHS')
        paths.add(pin['path'])


def joined(pin, rows):
    need(any(same(pin, item) for item in rows), 'EXACT_SOURCE_PIN_JOIN')


def member_shape(member):
    closed(member, 'schema runId runRoot operator authors candidate client cell sourceSubject runConfig runRelease lease supervisor outer driver plan capture fixturePrepare commandReceipts')
    need(member['schema'] == 'e02-ordinary-run-member-v1', 'MEMBER_SCHEMA')
    need(type(member['runId']) is str and re.fullmatch('[0-9a-f]{32}', member['runId']), 'FINITE_FRESH_RUN_ID')
    text(member['runRoot'])
    root = Path(member['runRoot'])
    need(root.is_absolute() and root.resolve(strict=True) == root and root.is_dir()
         and root.name == member['runId'], 'CANONICAL_DISTINCT_RUN_ROOT')
    text(member['operator'], 256)
    need(type(member['authors']) is list and 1 <= len(member['authors']) <= 16, 'MEMBER_AUTHORS')
    for author in member['authors']:
        text(author, 256)
    closed(member['cell'], 'direction role relay')
    cell = tuple(member['cell'][key] for key in ('direction', 'role', 'relay'))
    need(cell in MATRIX, 'FIXED_MATRIX_CELL')
    return root, cell


def inspect_outer(outer, member, files, supervisor_source):
    closed(outer, 'schema runId runConfig runRelease launchTool launchSession finalTool finalSession argv finalToolResult exit sessionFinished interruptionSent terminateSent timeoutSent completionProof')
    need(outer['schema'] == 'e02-outer-tool-completion-v1'
         and outer['runId'] == member['runId'], 'OUTER_RUN_JOIN')
    for key in ('runConfig', 'runRelease'):
        need(same(outer[key], member[key]), 'OUTER_AUTHORITY_JOIN')
    for key in ('launchTool', 'launchSession', 'finalTool', 'finalSession'):
        text(outer[key], 256)
    need(outer['launchSession'] == outer['finalSession'], 'SAME_OUTER_SESSION')
    argv = outer['argv']
    need(type(argv) is list and len(argv) == 14 and argv[0] in ('python3', '/usr/bin/python3')
         and argv[1:] == ['-I', '-B', supervisor_source['path'], '--config', member['runConfig']['path'],
            '--config-sha', member['runConfig']['sha256'], '--release', member['runRelease']['path'],
            '--release-sha', member['runRelease']['sha256'], '--out', member['runRoot']], 'EXACT_OUTER_ARGV')
    need(type(outer['finalToolResult']['bytes']) is int and outer['finalToolResult']['bytes'] > 0, 'NONEMPTY_ACTUAL_FINAL_TOOL_RESULT')
    files.checked(outer['finalToolResult'])  # Opaque actual tool JSON/text, not a fabricated child receipt.
    need(type(outer['exit']) is int and outer['exit'] == 0 and outer['sessionFinished'] is True
         and outer['interruptionSent'] is False and outer['terminateSent'] is False
         and outer['timeoutSent'] is False and outer['completionProof'] == 'ACTUAL_FINAL_TOOL_RESULT',
         'ACTUAL_NATURAL_TOOL_COMPLETION_REQUIRED')


def inspect_cleanup(supervisor, member, files):
    cleanup = supervisor['cleanup']
    closed(cleanup, 'ok rows errors evidence')
    need(cleanup['ok'] is True and cleanup['errors'] == [] and type(cleanup['rows']) is list
         and len(cleanup['rows']) == 4, 'QUALIFIED_WHOLE_RUN_CLEANUP')
    saved = metadata(files, cleanup['evidence'])
    closed(saved, 'ok rows errors')
    need(same(saved, {key: cleanup[key] for key in ('ok', 'rows', 'errors')}), 'SAVED_CLEANUP_JOIN')
    roles, cids = set(), set()
    for row in cleanup['rows']:
        closed(row, 'role exactOwnedCleanupOnly errors identityVerified absenceConfirmed inspectExit cid logsExit removeExit afterInspectExit')
        need(row['role'] not in roles and row['cid'] not in cids, 'UNIQUE_OWNED_CLEANUP')
        roles.add(row['role']); cids.add(row['cid'])
        need(type(row['cid']) is str and re.fullmatch('[a-f0-9]{64}', row['cid']), 'EXACT_OWNED_CID')
        need(row['exactOwnedCleanupOnly'] is True and row['identityVerified'] is True
             and row['absenceConfirmed'] is True and row['errors'] == [], 'OWNERSHIP_AND_ABSENCE_REQUIRED')
        for key, value in [('inspectExit', 0), ('logsExit', 0), ('removeExit', 0), ('afterInspectExit', 1)]:
            need(type(row[key]) is int and row[key] == value, 'QUALIFIED_CLEANUP_EXIT')
    need(roles == {'android', 'fixture', 'anchor', member['cell']['relay']}, 'ALL_FOUR_OWNED_ROLES')


def inspect_commands(member, files):
    rows = member['commandReceipts']
    checked_list(files, rows, 512)
    root = Path(member['runRoot']) / 'commands'
    actual = sorted(str(path) for path in root.glob('*.json'))
    expected = [str(root / ('%04d.json' % (index + 1))) for index in range(len(rows))]
    need(actual == expected == [pin['path'] for pin in rows], 'COMPLETE_ORDERED_COMMAND_INVENTORY')
    for pin in rows:
        row = metadata(files, pin)
        closed(row, 'argv launchAttempt pid exit reaped forced timedOut error stdout stderr observedBytes stdoutEOF stderrEOF')
        need(type(row['argv']) is list and bool(row['argv']), 'ACTUAL_CHILD_ARGV')
        for token in row['argv']:
            text(token)
        integer(row['pid'], minimum=1)
        need(row['launchAttempt'] is True and type(row['exit']) is int and row['exit'] == 0
             and row['reaped'] is True and row['forced'] is False and row['timedOut'] is False
             and row['error'] is None and row['stdoutEOF'] is True and row['stderrEOF'] is True,
             'EVERY_SUPERVISOR_CHILD_NATURAL_ZERO_REQUIRED')
        closed(row['observedBytes'], 'stdout stderr')
        for stream in ('stdout', 'stderr'):
            need(Path(row[stream]['path']).parent == root, 'OWNED_CHILD_STREAM')
            files.checked(row[stream])
            need(type(row['observedBytes'][stream]) is int
                 and row['observedBytes'][stream] == row[stream]['bytes'], 'WHOLE_CHILD_STREAM_CUSTODY')


def inspect_lease(value, member, release, config):
    closed(value, 'schema runId bootId issuedUtcNs deadlineUtcNs issuedMonoNs deadlineMonoNs issuedBootNs deadlineBootNs')
    need(value['schema'] == 'e02-single-cell-lease-v1' and value['runId'] == member['runId'], 'LEASE_RUN_JOIN')
    text(value['bootId'], 256)
    need(type(config['originalLeaseSeconds']) is int and config['originalLeaseSeconds'] == 1800, 'ORIGINAL_1800S_LEASE')
    integer(release['notAfterUtcNs'], I64, 1)
    for kind in ('Utc', 'Mono', 'Boot'):
        start, end = value['issued' + kind + 'Ns'], value['deadline' + kind + 'Ns']
        integer(start, I64, 1); integer(end, I64, 1)
        need(end - start == 1800 * 1000000000, 'NONRENEWED_ORIGINAL_LEASE')
    need(value['deadlineUtcNs'] <= release['notAfterUtcNs'], 'LEASE_INSIDE_ROOT_RELEASE')
    marker = Path(member['runRoot']) / 'session/control/REVOKED'
    need(not marker.exists() and not marker.is_symlink(), 'REVOKED_RUN_CANNOT_CONTRIBUTE')


def inspect_source_authority(member, files):
    config = metadata(files, member['runConfig'])
    closed(config, 'schema scope runtimeImage relayImage sdkRoot amethystApk helperApk runId originalLeaseSeconds sourceAndDependencyPins sdkInventory guardBundleInventory guardBundleRoot relayConfig state canonicalE02')
    need(config['schema'] == 'e02-single-cell-runtime-plan-v1' and config['runId'] == member['runId']
         and config['canonicalE02'] == 'PARTIAL22_UNCHANGED', 'CURRENT_RUN_CONFIG')
    need(same(config['amethystApk'], member['client']['apk']), 'EXACT_CONFIG_CLIENT')
    for key in ('amethystApk', 'helperApk', 'sdkInventory', 'guardBundleInventory', 'relayConfig'):
        files.checked(config[key])
    checked_list(files, config['sourceAndDependencyPins'])
    subject = metadata(files, member['sourceSubject'])
    closed(subject, 'schema revision coordinator scope sources proposedRunConfig priorSubject actualPreparationEvidence cleanupMockControls guardLocalControls consumerDataControls fixturePureControls rootRelease leaseIssued DockerLabActions AndroidActions uiControls')
    need(subject['schema'] == 'e02-first-cell-complete-source-config-subject-v1'
         and same(subject['proposedRunConfig'], member['runConfig']) and subject['scope'] == config['scope'], 'SOURCE_SUBJECT_CONFIG_JOIN')
    checked_list(files, subject['sources'])
    checked_list(files, subject['actualPreparationEvidence'])
    files.checked(subject['priorSubject'])
    sources = config['sourceAndDependencyPins']
    for source in sources:
        joined(source, subject['sources'])
        copy = dict(source, path=str(Path(member['runRoot']) / 'input' / Path(source['path']).name))
        files.checked(copy)
    names = [Path(pin['path']).name for pin in sources]
    need(len(names) == len(set(names)) and all(name in names for name in
         ('supervisor.py', 'lease_guard.py', 'android_driver.py', 'ui-plan.json', 'fixture.mjs', 'fixture-plan.json')), 'ACTIVATED_SIX_SOURCE_COPIES')
    supervisor_source = next(pin for pin in sources if Path(pin['path']).name == 'supervisor.py')
    release = metadata(files, member['runRelease'])
    closed(release, 'schema executionAuthorized rootSession executionSession runId scope runConfig sourceSubject notAfterUtcNs qaReview securityReview guardRegressionEvidence limits')
    need(release['schema'] == 'e02-first-cell-release-v1' and release['executionAuthorized'] is True
         and release['runId'] == member['runId'] and release['scope'] == config['scope']
         and same(release['runConfig'], member['runConfig'])
         and same(release['sourceSubject'], member['sourceSubject']), 'EXACT_RELEASE_SOURCE_CONFIG_JOIN')
    text(release['rootSession'], 256)
    need(release['executionSession'] == member['operator'], 'ACTUAL_RELEASE_EXECUTION_OPERATOR')
    files.checked(release['guardRegressionEvidence'])
    source_reviewers = set()
    allowed = set('reviewer role decision attribution subject configuration controlReadiness findings verified resolvedFindings conditions limits'.split())
    for role, key in [('qa', 'qaReview'), ('security', 'securityReview')]:
        review = metadata(files, release[key])
        need(type(review) is dict and set(review) <= allowed
             and review.get('role') == role and review.get('decision') == 'ACCEPT_EXACT_FIRST_CELL_SOURCE_CONFIG_ONLY'
             and same(review.get('subject'), member['sourceSubject'])
             and same(review.get('configuration'), member['runConfig']) and review.get('findings') == [], 'ACTUAL_SOURCE_REVIEW_JOIN')
        session = review.get('reviewer'); text(session, 256)
        need(session not in source_reviewers and session not in member['authors']
             and session != member['operator'], 'INDEPENDENT_SOURCE_REVIEWERS')
        source_reviewers.add(session)
    return config, release, subject, supervisor_source


def inspect_plan(plan, member, candidate, files, consumer, subject):
    # Versioned adapter: preserve every v1 plan validation while reading only the
    # actual runtime metadata through the separate named-time-field reader.
    closed(plan, 'schema runId operator authors client sources prerequisites runConfig runRelease expected')
    need(plan['schema'] == 'e02-ordinary-plan-v1' and plan['runId'] == member['runId']
         and plan['operator'] == member['operator'] and same(plan['authors'], member['authors'])
         and same(plan['client'], member['client']), 'MEMBER_PLAN_IDENTITY_JOIN')
    for key in ('runConfig', 'runRelease'):
        need(same(plan[key], member[key]), 'MEMBER_PLAN_AUTHORITY_JOIN')
    consumer.client(plan['client'], files)
    need(same(plan['prerequisites'], candidate['prerequisites']), 'CANDIDATE_PREREQUISITES')
    consumer.prerequisites(plan['prerequisites'], files)
    checked_list(files, plan['sources'])
    need(same(plan['sources'], subject['sources']), 'FULL_PLAN_SOURCE_SUBJECT_JOIN')
    for pin in candidate['basis']:
        joined(pin, plan['sources'])
    need(type(plan['expected']) is list and len(plan['expected']) == 8, 'REVIEWED_EIGHT_ROW_SCOPE')
    seen, ids = set(), set()
    for row in plan['expected']:
        closed(row, 'id direction role relay account peer rumor visibleToken dispatch')
        text(row['id'], 96)
        need(re.fullmatch('[a-z0-9][a-z0-9_-]{0,95}', row['id']) and row['id'] not in ids, 'UNIQUE_OBSERVATION_ID')
        ids.add(row['id'])
        cell = tuple(row[key] for key in ('direction', 'role', 'relay'))
        need(cell in MATRIX and cell not in seen, 'UNIQUE_MATRIX_CELL')
        seen.add(cell)
        sender, recipient = (consumer.A, consumer.B) if row['direction'] == 'js-to-rust' else (consumer.B, consumer.A)
        account, peer = (recipient, sender) if row['role'] == 'incoming' else (sender, recipient)
        need((row['account'], row['peer']) == (account, peer) and type(row['dispatch']) is bool
             and row['dispatch'] == (row['role'] == 'incoming'), 'EXACT_DISPOSABLE_ROLE')
        rumor = consumer.rumor(files.doc(row['rumor']))
        recipients = [tag[1] for tag in rumor['tags'] if tag[0] == 'p' and len(tag) >= 2]
        body = consumer.loads(rumor['content'].encode())
        need(rumor['pubkey'] == sender and recipients == [recipient] and type(body) is dict
             and body.get('protocol') == 'NBDP/experiment' and body.get('from') == sender
             and body.get('to') == recipient, 'BUSINESS_ENVELOPE_EXPECTED')
        text(row['visibleToken'], 256)
        need(len(row['visibleToken']) >= 8 and row['visibleToken'] in rumor['content'], 'EXPECTED_VISIBLE_TOKEN')
    need(seen == MATRIX, 'EXACT_EIGHT_CELL_MATRIX')


def mapped(pin, member, files):
    original = PurePosixPath(pin['path'])
    need(original.is_relative_to('/session/fixtures') and '..' not in original.parts, 'FIXTURE_NAMESPACE')
    result = dict(pin, path=str(Path(member['runRoot']) / 'session/fixtures' / original.relative_to('/session/fixtures')))
    files.checked(result)
    return result


def inspect_first_slice_lineage(member, driver, expected, row, config, lease, files, consumer):
    reply = files.doc(member['fixturePrepare'])
    closed(reply, 'schema operation caseId ok result')
    need(reply['schema'] == 'e02-fixture-command-v1' and reply['operation'] == 'prepare'
         and reply['caseId'] == row['id'] and reply['ok'] is True, 'ACTUAL_PREPARE_REPLY')
    result = reply['result']
    closed(result, 'expected expectedRumor expectedContent prepared inboxes')
    mapped_result = {key: mapped(pin, member, files) for key, pin in result.items()}
    need(same(mapped_result['expectedRumor'], expected['rumor'])
         and same(driver['expectedRumor'], expected['rumor']), 'PREPARED_EXPECTED_DRIVER_JOIN')
    original = consumer.rumor(files.doc(expected['rumor']))
    need(files.checked(mapped_result['expectedContent'], data=True) == original['content'].encode('utf-8'), 'WHOLE_PREPARED_CONTENT')
    prepared = files.doc(mapped_result['prepared'])
    closed(prepared, 'schema caseId senderPub recipientPub rumor events expected')
    need(prepared['schema'] == 'e02-first-cell-prepared-v1' and prepared['caseId'] == row['id']
         and same(prepared['rumor'], original)
         and same(mapped(prepared['expected'], member, files), mapped_result['expected']), 'ACTUAL_PREPARED_RUMOR_JOIN')
    sender = original['pubkey']
    recipient = next(tag[1] for tag in original['tags'] if tag[0] == 'p')
    frozen = files.doc(mapped_result['expected'])
    closed(frozen, 'schema caseId direction role relay senderPub recipientPub envelope rumor createdUTC')
    need(frozen['schema'] == 'e02-first-cell-expected-v1' and frozen['caseId'] == row['id']
         and all(frozen[key] == expected[key] for key in ('direction', 'role', 'relay'))
         and frozen['senderPub'] == prepared['senderPub'] == sender
         and frozen['recipientPub'] == prepared['recipientPub'] == recipient
         and same(frozen['rumor'], original)
         and same(frozen['envelope'], consumer.loads(original['content'].encode('utf-8'))), 'WHOLE_FROZEN_EXPECTATION_JOIN')
    text(frozen['createdUTC'], 96)
    proof = files.doc(row['transport'])
    wire = files.doc(proof['wire'])
    need(type(prepared['events']) is list and len(prepared['events']) == 2
         and any(same(wire, event) for event in prepared['events'])
         and all(type(event) is dict and event.get('kind') == 1059 for event in prepared['events'])
         and [event.get('tags') for event in prepared['events']] == [[['p', recipient]], [['p', sender]]],
         'ACTUAL_WIRE_IS_PREPARED_WRAP')
    need(lease['issuedUtcNs'] // 1000000000 <= original['created_at'] <= lease['deadlineUtcNs'] // 1000000000,
         'FRESH_RUMOR_INSIDE_ORIGINAL_LEASE')
    original_proof = files.doc(driver['originalTransport'])
    closed(original_proof, 'schema frame wire jsRequest rustRequest jsResult rustResult')
    rebound = {'schema': original_proof['schema'], **{key: mapped(pin, member, files)
               for key, pin in original_proof.items() if key != 'schema'}}
    need(same(proof, rebound), 'UNCHANGED_ORIGINAL_TRANSPORT_MAPPING')
    selection = files.doc(row['selection'])
    need(same(selection['helperArtifact'], config['helperApk']), 'EXACT_RUN_HELPER_ARTIFACT')
    need(lease['issuedMonoNs'] <= selection['capturedMonotonicNs'] <= lease['deadlineMonoNs'], 'HOST_SELECTION_INSIDE_HOST_MONOTONIC_LEASE')
    cleared = files.doc(driver['clipboardClear'])
    closed(cleared, 'schema caseId action foregroundFocus elapsedRealtimeNanos wallClockMillis status')
    need(cleared['schema'] == 'e02-clipboard-capture-v1' and cleared['caseId'] == row['id']
         and cleared['action'] == 'CLEAR' and cleared['status'] == 'EMPTY_SENTINEL_SET'
         and cleared['foregroundFocus'] is True, 'ACTUAL_FOCUSED_CLIPBOARD_CLEAR')
    for key in ('elapsedRealtimeNanos', 'wallClockMillis'):
        consumer.integer(cleared[key], 1)
    receipt = files.doc(selection['helperReceipt'])
    need(receipt['clipboardTimestamp'] >= cleared['wallClockMillis']
         and receipt['elapsedRealtimeNanos'] >= cleared['elapsedRealtimeNanos'], 'FRESH_GUEST_CLIPBOARD_CUSTODY')
    for pin, relative in ((driver['clipboardClear'], 'evidence/helper-clear.json'),
                          (selection['helperReceipt'], 'evidence/helper-capture.json'),
                          (row['rawClientRumor'], 'evidence/client-raw-rumor.json'),
                          (row['selection'], 'evidence/selection.json')):
        need(pin['path'] == str(Path(member['runRoot']) / relative), 'ACTUAL_DRIVER_OWNED_RAW_LINEAGE')
    # Guest elapsed/wall clocks are never compared to the host monotonic clock.
    captures = driver['allUICaptures']
    need(type(captures) is list and 1 <= len(captures) <= 140, 'ORIGINAL_UI_CAPTURE_LIMIT')
    seen = set()
    for capture in captures:
        closed(capture, 'png xml')
        for pin in capture.values():
            need(pin['path'] not in seen and Path(pin['path']).parent == Path(member['runRoot']) / 'ui', 'OWNED_DISTINCT_UI_CAPTURE')
            seen.add(pin['path']); files.checked(pin)
    need(any(same(capture, {'png': row['uiPng'], 'xml': row['uiXml']}) for capture in captures), 'SELECTED_UI_IN_ACTUAL_DRIVER_CAPTURES')
    files.doc(driver['torConfigurationGUI'])
    closed(driver['accountIdentityGUI'], 'preview observedPublicProfileText meaning')
    closed(driver['accountIdentityGUI']['preview'], 'png xml')
    need(any(same(capture, driver['accountIdentityGUI']['preview']) for capture in captures), 'ACTUAL_ACCOUNT_GUI_CAPTURE')
    need(type(driver['environmentAnrEvidence']) is list and len(driver['environmentAnrEvidence']) <= 2, 'BOUNDED_ENVIRONMENT_ANR_RECORDS')
    for event in driver['environmentAnrEvidence']:
        closed(event, 'decision afterWaitObservation')
        files.doc(event['decision']); files.doc(event['afterWaitObservation'])


def inspect_member(member, candidate, files, consumer):
    root, cell = member_shape(member)
    config, release, subject, supervisor_source = inspect_source_authority(member, files)
    lease = metadata(files, member['lease'])
    need(member['lease']['path'] == str(root / 'session/lease.json'), 'OWNED_ORIGINAL_LEASE')
    inspect_lease(lease, member, release, config)
    supervisor = metadata(files, member['supervisor'])
    closed(supervisor, 'schema runId runConfig runRelease lease canonicalE02Changed limits executionState error secondaryErrors cleanup')
    need(supervisor['schema'] == 'e02-first-cell-supervisor-result-v1'
         and supervisor['runId'] == member['runId'] and supervisor['executionState'] == 'PARTIAL'
         and supervisor['error'] is None and supervisor['secondaryErrors'] == []
         and supervisor['canonicalE02Changed'] is False, 'WHOLE_RUN_MUST_QUALIFY_NO_FAILED_DONATION')
    for key in ('runConfig', 'runRelease', 'lease'):
        need(same(supervisor[key], member[key]), 'SUPERVISOR_AUTHORITY_JOIN')
    need(member['supervisor']['path'] == str(root / 'supervisor-result.json'), 'OWNED_SUPERVISOR_RESULT')
    inspect_cleanup(supervisor, member, files)
    inspect_outer(metadata(files, member['outer']), member, files, supervisor_source)
    inspect_commands(member, files)
    driver = files.doc(member['driver'])
    closed(driver, 'schema runId runConfig runRelease executionState accountIdentityGUI torConfigurationGUI environmentAnrEvidence expectedRumor originalTransport clipboardClear allUICaptures observations limits canonicalE02Changed')
    need(member['driver']['path'] == str(root / 'driver-result.json')
         and driver['schema'] == 'e02-first-slice-driver-result-v1' and driver['runId'] == member['runId']
         and driver['executionState'] == 'PARTIAL' and driver['canonicalE02Changed'] is False,
         'ORIGINAL_LIMITED_DRIVER_HEADER')
    for key in ('runConfig', 'runRelease'):
        need(same(driver[key], member[key]), 'DRIVER_AUTHORITY_JOIN')
    plan, capture = files.doc(member['plan']), files.doc(member['capture'])
    inspect_plan(plan, member, candidate, files, consumer, subject)
    need(same(capture['driverReceipt'], member['driver']) and same(capture['observations'], driver['observations'])
         and capture['executionState'] == 'PARTIAL' and len(capture['observations']) == 1,
         'UNREWRITTEN_WHOLE_FIRST_SLICE_CAPTURE')
    result = consumer.inspect_capture(plan, member['plan'], capture, files)
    row = capture['observations'][0]
    expected = next(item for item in plan['expected'] if item['id'] == row['id'])
    need(tuple(expected[key] for key in ('direction', 'role', 'relay')) == cell, 'DECLARED_ACTUAL_CELL_JOIN')
    need(result['status'] == 'PARTIAL' and result['matchedObservationIds'] == [row['id']], 'ONE_COMPLETE_REVIEWABLE_FIRST_SLICE')
    inspect_first_slice_lineage(member, driver, expected, row, config, lease, files, consumer)
    return plan, capture, row, result


def whole_run_reviews(entry, member, files):
    closed(entry['reviews'], 'qa security')
    sessions = set()
    for role in ('qa', 'security'):
        value = metadata(files, entry['reviews'][role])
        closed(value, 'schema role session decision member outer supervisor driver capture candidate sourceSubject acceptedObservationIds classification findings rawReviewEvidence')
        need(value['schema'] == 'e02-ordinary-whole-run-review-v1' and value['role'] == role, 'ACTUAL_WHOLE_RUN_REVIEW_SCHEMA')
        for key in ('outer', 'supervisor', 'driver', 'capture', 'candidate', 'sourceSubject'):
            need(same(value[key], member[key]), 'WHOLE_REVIEW_ARTIFACT_JOIN')
        need(same(value['member'], entry['member']) and value['classification'] == entry['classification'], 'WHOLE_REVIEW_MEMBER_SCOPE')
        session = value['session']; text(session, 256)
        need(session not in sessions and session not in member['authors'] and session != member['operator'], 'INDEPENDENT_ACTUAL_WHOLE_RUN_REVIEWERS')
        sessions.add(session)
        need(type(value['findings']) is list and len(value['findings']) <= 64, 'BOUNDED_REVIEW_FINDINGS')
        for finding in value['findings']:
            text(finding)
        need(type(value['rawReviewEvidence']['bytes']) is int and value['rawReviewEvidence']['bytes'] > 0, 'NONEMPTY_ACTUAL_REVIEW_EVIDENCE')
        files.checked(value['rawReviewEvidence'])
        if entry['disposition'] == 'CONTRIBUTE':
            need(value['decision'] == 'ACCEPT_QUALIFIED_RUN_FOR_SUPPLEMENT_ONLY' and value['findings'] == [], 'QUALIFIED_RUN_REVIEW_REQUIRED')
            capture = files.doc(member['capture'])
            need(same(value['acceptedObservationIds'], [row['id'] for row in capture['observations']]), 'WHOLE_REVIEW_EXACT_OBSERVATIONS')
        else:
            need(value['decision'] == 'ACCEPT_EXCLUSION_RECORD_ONLY' and value['acceptedObservationIds'] == [], 'EXCLUSIONS_CANNOT_DONATE_ROWS')


def inventory_reviews(review_pins, inventory_pin, inventory, files):
    closed(review_pins, 'qa security')
    need(type(inventory['runs']) is list and len(inventory['runs']) <= 64, 'FINITE_ATTEMPT_INVENTORY')
    prohibited = set(inventory['authors']) | {inventory['operator']}
    # Disclosure is mandatory for every member, including excluded attempts.
    # The inventory's own author list cannot hide a member author/operator.
    for entry in inventory['runs']:
        closed(entry, 'member disposition classification reason reviews observationReviews')
        member = metadata(files, entry['member'])
        member_shape(member)
        prohibited.update(member['authors'])
        prohibited.add(member['operator'])
    sessions = set()
    for role in ('qa', 'security'):
        value = metadata(files, review_pins[role])
        closed(value, 'schema role session decision inventory candidate completeAttemptInventory findings rawReviewEvidence')
        need(value['schema'] == 'e02-ordinary-aggregate-inventory-review-v1' and value['role'] == role
             and value['decision'] == 'ACCEPT_COMPLETE_CANDIDATE_ATTEMPT_INVENTORY_ONLY'
             and same(value['inventory'], inventory_pin) and same(value['candidate'], inventory['candidate'])
             and value['completeAttemptInventory'] is True and value['findings'] == [], 'ACTUAL_COMPLETE_INVENTORY_REVIEW')
        text(value['session'], 256)
        need(value['session'] not in sessions and value['session'] not in prohibited,
             'INDEPENDENT_INVENTORY_REVIEWERS')
        need(type(value['rawReviewEvidence']['bytes']) is int and value['rawReviewEvidence']['bytes'] > 0, 'NONEMPTY_ACTUAL_INVENTORY_REVIEW_EVIDENCE')
        sessions.add(value['session']); files.checked(value['rawReviewEvidence'])


def evaluate(inventory, inventory_pin, reviews, files, consumer, budget):
    closed(inventory, 'schema evidenceType operator authors candidate consumer runs')
    need(inventory['schema'] == 'e02-ordinary-aggregate-inventory-v1', 'INVENTORY_SCHEMA')
    need(inventory['evidenceType'] in ('ACTUAL_RUNTIME', 'SYNTHETIC_DATA_CONTROLS_ONLY'), 'EXPLICIT_EVIDENCE_TYPE')
    text(inventory['operator'], 256)
    need(type(inventory['authors']) is list and 1 <= len(inventory['authors']) <= 16, 'INVENTORY_AUTHORS')
    for author in inventory['authors']:
        text(author, 256)
    files.checked(inventory['consumer'])
    candidate = files.doc(inventory['candidate'])
    closed(candidate, 'schema id client prerequisites basis scope')
    need(candidate['schema'] == 'e02-ordinary-aggregate-candidate-v1'
         and candidate['scope'] == 'ORDINARY_KIND14_EIGHT_CELL_SUPPLEMENT_ONLY', 'CANDIDATE_SCHEMA_SCOPE')
    text(candidate['id'], 96)
    consumer.client(candidate['client'], files)
    consumer.prerequisites(candidate['prerequisites'], files)
    checked_list(files, candidate['basis'])
    inventory_reviews(reviews, inventory_pin, inventory, files)
    need(type(inventory['runs']) is list and len(inventory['runs']) <= 64, 'FINITE_ATTEMPT_INVENTORY')
    rows, cells, seen_ids, seen_roots, conflicts, refused, failures = [], {}, set(), set(), [], [], []
    for entry in inventory['runs']:
        closed(entry, 'member disposition classification reason reviews observationReviews')
        need(entry['disposition'] in ('CONTRIBUTE', 'EXCLUDE')
             and entry['classification'] in ('QUALIFIED', 'ENVIRONMENT_FAILURE', 'COMPATIBILITY_FAILURE', 'UNQUALIFIED'), 'EXPLICIT_ATTEMPT_DISPOSITION')
        if entry['disposition'] == 'EXCLUDE':
            text(entry['reason'])
        else:
            need(entry['reason'] is None and entry['classification'] == 'QUALIFIED', 'CONTRIBUTOR_DECLARATION')
        run_files = file_reader(consumer, budget)
        member = metadata(run_files, entry['member'])
        root, cell = member_shape(member)
        need(member['runId'] not in seen_ids and str(root) not in seen_roots, 'DISTINCT_FINITE_RUN_MEMBERS')
        seen_ids.add(member['runId']); seen_roots.add(str(root))
        need(same(member['candidate'], inventory['candidate']) and same(member['client'], candidate['client']), 'EXACT_CANDIDATE_CLIENT_MEMBER_JOIN')
        row = dict(runId=member['runId'], member=entry['member'], cell=list(cell),
                   disposition=entry['disposition'], classification=entry['classification'], reason=entry['reason'])
        matched_cell = None
        try:
            whole_run_reviews(entry, member, run_files)
            if entry['disposition'] == 'EXCLUDE':
                need(entry['observationReviews'] is None, 'EXCLUSION_HAS_NO_ACCEPTED_OBSERVATIONS')
                for key in ('candidate', 'sourceSubject', 'runConfig', 'runRelease', 'lease', 'supervisor', 'outer', 'driver', 'plan', 'capture', 'fixturePrepare'):
                    if member[key] is not None:
                        run_files.checked(member[key])
                row['status'] = 'EXCLUDED_VISIBLE'
                if entry['classification'] == 'COMPATIBILITY_FAILURE':
                    failures.append(member['runId'])
            else:
                plan, capture, observation, result = inspect_member(member, candidate, run_files, consumer)
                closed(entry['observationReviews'], 'qa security')
                consumer.actual_reviews(plan, member['plan'], capture, member['capture'],
                    [(role, entry['observationReviews'][role]) for role in ('qa', 'security')], run_files)
                row.update(status='MATCHED_ROW_SUPPLEMENT_ONLY', captureHeader=capture['executionState'],
                           originalConsumerStatus=result['status'], observationId=observation['id'])
                matched_cell = cell
            run_files.current()
            if matched_cell is not None:
                if cell in cells:
                    conflicts.append(dict(cell=list(cell), runs=[cells[cell], member['runId']]))
                else:
                    cells[cell] = member['runId']
        except consumer.Mismatch as error:
            row.update(status='FAIL', error=str(error)); failures.append(member['runId'])
        except (Refusal, consumer.Refusal, OSError, ValueError, TypeError, KeyError, StopIteration, ET.ParseError) as error:
            row.update(status='QUALIFICATION_REFUSED', error=str(error)[:4096]); refused.append(member['runId'])
        rows.append(row)
    missing = [list(cell) for cell in sorted(MATRIX - set(cells))]
    status = ('FAIL' if failures else 'QUALIFICATION_REFUSED' if refused or conflicts else
              'PARTIAL' if missing else 'MATRIX_MATCHED_SUPPLEMENT_ONLY')
    files.current()
    # Final aggregate union recheck includes earlier runs, not only the final member.
    for pin in list(budget.pins.values()):
        file_reader(consumer, Budget()).checked(pin)
    matrix_state = status
    if inventory['evidenceType'] == 'SYNTHETIC_DATA_CONTROLS_ONLY' and status == 'MATRIX_MATCHED_SUPPLEMENT_ONLY':
        status = 'DATA_CONSISTENCY_ONLY'
    return dict(schema='e02-ordinary-aggregate-result-v1', status=status, matrixState=matrix_state,
        evidenceType=inventory['evidenceType'], inventory=inventory_pin,
        runs=rows, missingCells=missing, conflictingCells=conflicts, failedRunIds=failures,
        refusedRunIds=refused, canonicalE02Changed=False, canonicalStatus='PARTIAL22_UNCHANGED',
        fullMatrixAndCanonicalIntegration='PENDING_SEPARATE_REVIEW',
        meaning='Supplement consistency only. External actual independent reviews remain the authenticity boundary; no canonical PASS, skip removal, architectural closure or SDK authority.')


def main(argv):
    need(len(argv) == 7, 'CLI INVENTORY INVENTORY_SHA QA_INVENTORY_REVIEW QA_SHA SECURITY_INVENTORY_REVIEW SECURITY_SHA')
    # Bootstrap only bounded metadata and the exact fixed consumer; the inventory
    # hash and both review hashes are independently known external operands.
    path = Path(argv[1])
    need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'CANONICAL_INVENTORY')
    with path.open('rb') as handle:
        before = os.fstat(handle.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size <= 16 * 1024 ** 2, 'REGULAR_BOUNDED_INVENTORY')
        raw = handle.read(16 * 1024 ** 2 + 1)
        after = os.fstat(handle.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(identity(before) == identity(after) and len(raw) == before.st_size, 'INVENTORY_READ_DRIFT')
    need(hashlib.sha256(raw).hexdigest() == argv[2], 'EXTERNAL_INVENTORY_SHA')
    inventory = loads_metadata(raw)
    consumer = load_consumer(inventory['consumer'])
    budget = Budget(); files = file_reader(consumer, budget)
    inventory_pin = files.external(argv[1], argv[2])
    reviews = {role: files.external(argv[index], argv[index + 1])
               for role, index in [('qa', 3), ('security', 5)]}
    result = evaluate(inventory, inventory_pin, reviews, files, consumer, budget)
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
    return 0 if result['status'] == 'MATRIX_MATCHED_SUPPLEMENT_ONLY' else 1 if result['status'] == 'FAIL' else 2


if __name__ == '__main__':
    try:
        code = main(sys.argv)
    except (ValueError, OSError, KeyError, TypeError, ET.ParseError) as error:
        print(json.dumps(dict(status='QUALIFICATION_REFUSED', error=str(error)[:4096], canonicalE02Changed=False)))
        code = 2
    raise SystemExit(code)
