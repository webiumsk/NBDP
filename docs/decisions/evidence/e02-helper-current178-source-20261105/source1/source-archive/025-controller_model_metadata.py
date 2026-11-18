"""Bounded, typed coordinator metadata for current controller MODEL5.

No target imports, subprocesses, Docker or API dispatch. Root alone selects
externally pinned inputs and enforces actual fresh/sequential/once dispatch.
This reader proves only the stated metadata predicates, never native custody
authentication, inner PID/reap/EOF, helper success or ordinary qualification.
"""
import ast
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import sys
import time

REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE = REPO / 'docs/decisions/evidence'
HERE = Path(__file__).resolve().parent
DATA = 16_777_216
RAW = 2_147_483_648
OUTPUT = 1_048_576
SAFE = 9_007_199_254_740_991
I64 = 9_223_372_036_854_775_807
DEPTH = 64
METADATA_DEPTH = 48
NODES = 250_000
FILES = 20_000
PREFIX = '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-'
PYTHON = '/home/peterhorvath/.miniforge3/bin/python3.13'
TOOLS = (PYTHON, '/usr/bin/timeout', '/usr/bin/env')
DESIGN_CONTRIBUTORS = (
    '/root', '/root/collector_typed_qa_1592707b',
    '/root/collector_typed_security_1592707b', '/root/controller_model_metadata_source2')
CONTRACT = dict(
    path=str(EVIDENCE / 'e02-producer4-helper-probe-preparation-20261028/current-controller-acceptance-contract.json'),
    bytes=3204, sha256='5d882ebdf7e3df7b72f941df2ff0ef561f4f221fde5771af5ce7c8e2d7d2d437')
REVIEW_FILES = ('acceptance.json', 'qa-review.json', 'security-review.json',
                'qa-findings.json', 'security-findings.json',
                'review-agent-birth-record.json', 'complete-freeze.json')
MODEL_KEYS = {'cmd', 'workdir', 'login', 'yield_time_ms', 'max_output_tokens'}
POLL_KEYS = {'session_id', 'chars', 'yield_time_ms', 'max_output_tokens'}
FLAGS = {'truncated', 'output_truncated', 'interrupted', 'error', 'isError'}
RESPONSE_KEYS = {'chunk_id', 'wall_time_seconds', 'exit_code', 'original_token_count',
                 'output', 'session_id'} | FLAGS
JOB_KEYS = {'schema', 'actor', 'source', 'sourceAcceptance', 'sourceReviewRoot',
            'controlPlan', 'version', 'modelsDefined', 'countsSeparate', 'requests',
            'inputsBefore', 'protectedInputs', 'snapshotDescriptors', 'outputRoot',
            'actualRequestFamily', 'method', 'noRetry', 'rootRelease',
            'executionAuthorized'}


class Refusal(ValueError):
    pass


def need(value, reason):
    if not value:
        raise Refusal(reason)


def closed(value, keys):
    need(type(value) is dict and set(value) == set(keys), 'CLOSED_KEYS')
    return value


def integer(value, lo=0, hi=SAFE):
    need(type(value) is int and lo <= value <= hi, 'INTEGER_DOMAIN')
    return value


def text(value, maximum=DATA):
    need(type(value) is str, 'TEXT_TYPE')
    need(len(value.encode('utf8', 'strict')) <= maximum, 'TEXT_BOUND')
    return value


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def equal(a, b, reason='TYPED_VALUE_MISMATCH'):
    need(same(a, b), reason)


def safe_path(value):
    value = text(str(value) if isinstance(value, Path) else value, 4096)
    path = Path(value)
    need(path.is_absolute() and path.anchor == '/' and str(path) == value and
         '..' not in path.parts and '\x00' not in value, 'CANONICAL_ABSOLUTE_PATH')
    return path


def pin_shape(value):
    closed(value, ('path', 'bytes', 'sha256'))
    safe_path(value['path'])
    integer(value['bytes'], 0, RAW)
    need(type(value['sha256']) is str and
         re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None, 'SHA256_DOMAIN')
    return value


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mode,
            value.st_mtime_ns, value.st_ctime_ns, value.st_uid, value.st_gid,
            value.st_nlink)


def read(path, maximum=DATA):
    """Bound size before reading, refuse ancestor/leaf links and observe drift."""
    path = safe_path(path)
    integer(maximum, 0, RAW)
    directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:-1]:
            following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=directory)
            os.close(directory)
            directory = following
        before = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        need(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, 'PRE_READ_BOUND')
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        blocks, length = [], 0
        try:
            need(identity(os.fstat(fd)) == identity(before), 'OPEN_IDENTITY')
            while True:
                block = os.read(fd, min(65_536, maximum - length + 1))
                if not block:
                    break
                length += len(block)
                need(length <= maximum, 'READ_BOUND')
                blocks.append(block)
            need(identity(os.fstat(fd)) == identity(before), 'READ_IDENTITY')
        finally:
            os.close(fd)
        after = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        need(identity(after) == identity(before) and length == before.st_size, 'PATH_IDENTITY')
        return b''.join(blocks), before
    finally:
        os.close(directory)


def pin(path):
    path = safe_path(path)
    data, _ = read(path, RAW if str(path) in TOOLS else DATA)
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def verified_bytes(expected):
    pin_shape(expected)
    maximum = RAW if expected['path'] in TOOLS else DATA
    need(expected['bytes'] <= maximum, 'NAMED_RAW_TOOL_BOUND')
    data, _ = read(Path(expected['path']), maximum)
    equal(dict(path=expected['path'], bytes=len(data), sha256=hashlib.sha256(data).hexdigest()),
          expected, 'EXPECTED_PIN_CHANGED')
    return data


def preflight_json(raw, api=False):
    """Bound allocations before json.loads, including structural nesting."""
    need(type(raw) is bytes and len(raw) <= DATA, 'JSON_BYTES_BOUND')
    value = raw.decode('utf8', 'strict')
    nesting, nodes, quoted, escaped, token = 0, 0, False, False, False
    for char in value:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            nodes += 1
            quoted, token = True, False
        elif char in '{[':
            nesting += 1
            nodes += 1
            token = False
            need(nesting <= (DEPTH if api else METADATA_DEPTH) + 1, 'JSON_PRE_DEPTH')
        elif char in '}]':
            nesting -= 1
            token = False
        elif char.isspace() or char in ',:':
            token = False
        elif not token:
            nodes += 1
            token = True
        need(nodes <= NODES, 'JSON_PRE_NODES')
    return value


def wall_path(path):
    return (path == ('launch', 'unmodifiedResponse', 'wall_time_seconds') or
            len(path) == 4 and path[0] == 'polls' and type(path[1]) is int and
            path[2:] == ('unmodifiedResponse', 'wall_time_seconds'))


def validate_tree(value, api=False):
    schema = value.get('schema') if type(value) is dict else None
    snapshot_schema = (type(schema) is str and
                       re.fullmatch('e02-controller[1-9][0-9]*-current-inputs-v1', schema))
    stack, count = [(value, (), 0)], 0
    while stack:
        item, path, depth = stack.pop()
        count += 1
        need(depth <= (DEPTH if api else METADATA_DEPTH) and count <= NODES, 'JSON_STRUCTURE_BOUND')
        if type(item) is dict:
            for key, child in item.items():
                text(key)
                count += 1
                need(count <= NODES, 'JSON_NODE_BOUND')
                stack.append((child, path + (key,), depth + 1))
        elif type(item) is list:
            stack.extend((child, path + (i,), depth + 1) for i, child in enumerate(item))
        elif type(item) is str:
            text(item)
        elif type(item) is int:
            timestamp = (snapshot_schema and len(path) == 3 and path[0] == 'rows'
                         and type(path[1]) is int and path[2] in ('mtimeNs', 'ctimeNs'))
            integer(item, -I64 if timestamp else -SAFE, I64 if timestamp else SAFE)
        elif type(item) in (float, Decimal):
            need(api and wall_path(path), 'ONLY_API_WALL_FLOAT')
            finite = item.is_finite() if type(item) is Decimal else math.isfinite(item)
            need(finite and item >= 0, 'FINITE_NONNEGATIVE_WALL')
        else:
            need(item is None or type(item) is bool, 'JSON_VALUE_TYPE')
    return value


def decode_json(raw, api=False):
    value = preflight_json(raw, api)
    def pairs(items):
        result = {}
        for key, child in items:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = child
        return result
    def number(token):
        need(token != '-0', 'NEGATIVE_ZERO')
        return integer(int(token), -I64, I64)
    def forbidden(_):
        raise Refusal('NONFINITE_JSON')
    try:
        result = json.loads(value, object_pairs_hook=pairs, parse_int=number,
                            parse_float=Decimal, parse_constant=forbidden)
    except (json.JSONDecodeError, RecursionError, OverflowError) as error:
        raise Refusal('INVALID_BOUNDED_JSON') from error
    return validate_tree(result, api)


def doc(path, api=False):
    data, _ = read(path, DATA)
    return decode_json(data, api)


def verified_doc(expected, api=False):
    need(pin_shape(expected)['bytes'] <= DATA, 'JSON_PIN_BOUND')
    return decode_json(verified_bytes(expected), api)


def put(path, value):
    path = safe_path(path)
    data = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    decode_json(data)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(data) == len(data), 'ONE_COMPLETE_METADATA_WRITE')
    return pin(path)


def canonical_request(value):
    closed(value, MODEL_KEYS)
    text(value['cmd'], DATA)
    text(value['workdir'], 4096)
    safe_path(value['workdir'])
    need(type(value['login']) is bool and value['login'] is False, 'LOGIN_FALSE')
    integer(value['yield_time_ms'], 1)
    integer(value['max_output_tokens'], 1)
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def request(group):
    argv = list(group['argv'])
    if argv[-1] != '-v':
        argv.append('-v')
    command = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8',
               'LC_ALL=C.UTF-8', '/usr/bin/timeout', '--signal=KILL', '63s', *argv]
    result = dict(cmd=shlex.join(command), workdir=group['cwd'], login=False,
                  yield_time_ms=1000, max_output_tokens=20000)
    canonical_request(result)
    return result


def validate_snapshot(value, total, descriptors=None):
    integer(total, 1)
    validate_tree(value)
    closed(value, ('schema', 'actor', 'rows'))
    equal(value['schema'], 'e02-controller' + str(total) + '-current-inputs-v1')
    equal(value['actor'], '/root')
    need(type(value['rows']) is list and 1 <= len(value['rows']) <= FILES, 'SNAPSHOT_ROWS')
    rows = {}
    for row in value['rows']:
        closed(row, ('pin', 'mode', 'uid', 'gid', 'device', 'inode', 'mtimeNs', 'ctimeNs'))
        pin_shape(row['pin'])
        need(type(row['mode']) is str and re.fullmatch('0o[0-7]{3,4}', row['mode']), 'MODE')
        for key in ('uid', 'gid', 'device', 'inode'):
            integer(row[key], 0, SAFE)
        for key in ('mtimeNs', 'ctimeNs'):
            integer(row[key], 0, I64)
        path = row['pin']['path']
        need(path not in rows, 'DUPLICATE_SNAPSHOT_PATH')
        rows[path] = row
    if descriptors is not None:
        need(type(descriptors) is list and len(descriptors) <= FILES, 'EXPECTED_ROWS_BOUND')
        expected = {}
        for item in descriptors:
            pin_shape(item)
            need(item['path'] not in expected, 'DUPLICATE_EXPECTED_PIN')
            expected[item['path']] = item
        equal(set(rows), set(expected))
        for path, item in expected.items():
            equal(rows[path]['pin'], item, 'SNAPSHOT_EXPECTED_PIN')
    return value


def snapshot(descriptors, total):
    need(type(descriptors) is list and 1 <= len(descriptors) <= FILES, 'FINITE_PROTECTED_SET')
    rows = []
    for expected in sorted(descriptors, key=lambda x: pin_shape(x)['path']):
        data, s = read(expected['path'], RAW if expected['path'] in TOOLS else DATA)
        equal(dict(path=expected['path'], bytes=len(data), sha256=hashlib.sha256(data).hexdigest()),
              expected, 'PROTECTED_PIN_CHANGED')
        rows.append(dict(pin=expected, mode=oct(stat.S_IMODE(s.st_mode)), uid=s.st_uid,
                         gid=s.st_gid, device=s.st_dev, inode=s.st_ino,
                         mtimeNs=s.st_mtime_ns, ctimeNs=s.st_ctime_ns))
    return validate_snapshot(dict(schema='e02-controller' + str(total) + '-current-inputs-v1',
                                  actor='/root', rows=rows), total, descriptors)


def source_header(source, source_path):
    need(type(source) is dict, 'SOURCE_OBJECT')
    equal(source['schema'], 'e02-one-cid-helper-probe-controller-source-v1')
    version = source['version']
    need(type(version) is str and re.fullmatch('r[1-9][0-9]{0,3}', version), 'CURRENT_VERSION')
    equal(str(safe_path(source_path)), PREFIX + version + '/subject.json')
    for key in ('modelsExecuted', 'helperExecutions', 'probeExecutions'):
        equal(source[key], 0)
    equal(source['upstreamProducerRuntimeWorkerCount'], 22)
    equal(source['upstreamProducerModelsDefined'], 266)
    integer(source['sourceCount'], 1, FILES)
    integer(source['modelsDefined'], 1, 100_000)
    integer(source['modelGroups'], 1, 100)
    need(type(source['sources']) is list, 'SOURCE_MEMBERS')
    equal(len(source['sources']), source['sourceCount'])
    members = {}
    for item in source['sources']:
        pin_shape(item)
        need(item['path'] not in members, 'UNIQUE_SOURCE_MEMBERS')
        members[item['path']] = item
    for field, count, names in (
            ('runtimeSources', 3, {'controller.py', 'host.py', 'finite_child.py'}),
            ('guestProbeSources', 8, {'probe-guard-helper.mjs', 'guard-client.mjs',
             'guard-client-core.mjs', 'guard-wire.mjs', 'guard-helper.py',
             'lease_guard.py', 'capture-allocation.mjs', 'guard-transport-boundaries.mjs'})):
        need(type(source[field]) is list, 'RUNTIME_MEMBERS')
        equal(len(source[field]), count)
        equal({Path(p['path']).name for p in source[field]}, names)
        for item in source[field]:
            equal(members.get(pin_shape(item)['path']), item, 'RUNTIME_SOURCE_JOIN')
    equal(source['runtimeSourceCount'], 3)
    equal(source['guestProbeSourceCount'], 8)
    return members


def validate_groups(source, plan, bodies):
    equal(plan['schema'], 'e02-one-cid-helper-probe-controller-controls-v1')
    groups = plan['groups']
    need(type(groups) is list and 1 <= len(groups) <= 100, 'FINITE_GROUPS')
    need(len({g['name'] for g in groups}) == len(groups), 'UNIQUE_GROUPS')
    by_path = {item['path']: item for item in source['sources']}
    version = int(source['version'][1:])
    counts = []
    for group in groups:
        closed(group, ('name', 'source', 'format', 'argv', 'cwd', 'count', 'expectedNames'))
        text(group['name'], 256)
        equal(by_path.get(pin_shape(group['source'])['path']), group['source'])
        body = bodies[group['source']['path']]
        need(type(body) is bytes and len(body) <= DATA, 'BOUNDED_AST_SOURCE')
        tree = ast.parse(body, filename=group['source']['path'])
        names = [c.name + '.' + m.name for c in tree.body if isinstance(c, ast.ClassDef)
                 for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]
        equal(group['expectedNames'], names, 'EXACT_AST_NAMES')
        integer(group['count'], 1, 10_000)
        equal(group['count'], len(names))
        equal(group['format'], 'VERBOSE_UNITTEST_NAMED')
        cwd = str(safe_path(group['cwd']))
        match = re.fullmatch(re.escape(PREFIX) + 'r([1-9][0-9]{0,3})', cwd)
        need(match is not None and 1 <= int(match[1]) <= version, 'CURRENT_OR_PREDECESSOR_CWD')
        need(any(Path(p).parent == Path(cwd) for p in by_path), 'CWD_DECLARED_MEMBER')
        base = [PYTHON, '-I', '-B', group['source']['path']]
        need(same(group['argv'], base) or same(group['argv'], base + ['-v']), 'EXACT_MODEL_ARGV')
        request(group)
        counts.append(group['count'])
    equal(source['modelsDefined'], sum(counts))
    equal(source['modelGroups'], len(groups))
    if 'modelsDefined' in plan:
        equal(plan['modelsDefined'], sum(counts))
    return counts


def validate_acceptance(acceptance, source_pin, source, rule):
    closed(acceptance, rule['closedKeys'])
    for key, value in rule['literals'].items():
        equal(acceptance[key], value, 'EXACT_SOURCE_ACCEPTANCE_LITERAL')
    equal(acceptance['subject'], pin_shape(source_pin), 'SOURCE_ACCEPTANCE_PIN')
    equal(acceptance['modelsDefined'], integer(source['modelsDefined'], 1))
    equal(acceptance['modelGroups'], integer(source['modelGroups'], 1))
    need(type(acceptance['reviews']) is list and len(acceptance['reviews']) == 2, 'SOURCE_REVIEW_PAIR')


def actors(source):
    result = set(DESIGN_CONTRIBUTORS)
    for key in ('author', 'coordinator'):
        if key in source:
            result.add(text(source[key], 4096))
    for key in ('sourceContributors', 'reviewerExclusions', 'operators', 'sourcePreparationOperators'):
        if key in source:
            need(type(source[key]) is list, 'ACTOR_LIST')
            result.update(text(x, 4096) for x in source[key])
    return result


def exact_membership(root, expected):
    root = safe_path(root)
    need(type(expected) is list and len(expected) <= FILES, 'MEMBERSHIP_BOUND')
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in root.parts[1:]:
            following = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
    finally:
        os.close(descriptor)
    declared, directories = set(), {str(root)}
    for value in expected:
        path = safe_path(value)
        need(path.is_relative_to(root), 'OWNED_MEMBERSHIP_PATH')
        need(str(path) not in declared, 'UNIQUE_MEMBERSHIP_PATH')
        declared.add(str(path))
        for parent in path.parents:
            if parent == root:
                break
            need(parent.is_relative_to(root), 'DECLARED_PARENT_NAMESPACE')
            directories.add(str(parent))
    actual = set()
    for directory, folders, names in os.walk(root, followlinks=False):
        for name in folders:
            child = Path(directory) / name
            need(str(child) in directories and not child.is_symlink(),
                 'NO_EXTRA_OR_ALIASED_MEMBERSHIP_DIRECTORY')
        for name in names:
            path = Path(directory) / name
            need(stat.S_ISREG(path.lstat().st_mode), 'REGULAR_MEMBERSHIP')
            actual.add(str(path))
            need(len(actual) <= FILES, 'MEMBERSHIP_FILE_BOUND')
    equal(actual, declared, 'COMPLETE_SOURCE_MEMBERSHIP')


def load_profile(source_path, review_root, source_sha, acceptance_sha):
    source_path, review_root = safe_path(source_path), safe_path(review_root)
    need(review_root.is_relative_to(EVIDENCE), 'REVIEW_NAMESPACE')
    need(re.fullmatch('[0-9a-f]{64}', text(source_sha, 64)) and
         re.fullmatch('[0-9a-f]{64}', text(acceptance_sha, 64)), 'EXTERNAL_SELECTION_SHA')
    source_pin = pin(source_path)
    equal(source_pin['sha256'], source_sha, 'EXTERNAL_SOURCE_SHA')
    source = verified_doc(source_pin)
    members = source_header(source, source_path)
    acceptance_pin = pin(review_root / 'acceptance.json')
    equal(acceptance_pin['sha256'], acceptance_sha, 'EXTERNAL_ACCEPTANCE_SHA')
    acceptance = verified_doc(acceptance_pin)
    contract = verified_doc(CONTRACT)
    if 'currentControllerAcceptanceContract' in source:
        equal(source['currentControllerAcceptanceContract'], CONTRACT)
    rule = contract['source']
    validate_acceptance(acceptance, source_pin, source, rule)
    forbidden, sessions = actors(source), set()
    for role, review_pin in zip(('qa', 'security'), acceptance['reviews']):
        equal(pin_shape(review_pin)['path'], str(review_root / (role + '-review.json')))
        value = verified_doc(review_pin)
        closed(value, ('role', 'session', 'decision', 'subject'))
        equal(value['role'], role)
        equal(value['decision'], rule['reviewDecision'])
        equal(value['subject'], source_pin)
        session = text(value['session'], 4096)
        need(session not in forbidden and session not in sessions, 'INDEPENDENT_SOURCE_REVIEWS')
        sessions.add(session)
    plan_pin = pin_shape(source['controlPlan'])
    plan = verified_doc(plan_pin)
    bodies = {path: verified_bytes(item) for path, item in members.items()}
    counts = validate_groups(source, plan, bodies)
    freeze = doc(review_root / 'complete-freeze.json')
    equal(freeze['subject'], source_pin, 'CURRENT_FROZEN_SUBJECT')
    need(type(freeze['inputs']) is list and 1 <= len(freeze['inputs']) <= FILES, 'FINITE_FREEZE')
    protected = {}
    def add(item):
        pin_shape(item)
        prior = protected.setdefault(item['path'], item)
        equal(prior, item, 'CONFLICTING_PROTECTED_PIN')
    for item in freeze['inputs']:
        add(item)
    for item in source['sources']:
        need(item['path'] in protected, 'ALL_CURRENT_SOURCES_IN_FREEZE')
        equal(protected[item['path']], item)
    if 'packetFiles' in freeze:
        exact_membership(Path(freeze['entrypoint']['path']).parent, freeze['packetFiles'])
    if 'dataSourceFiles' in freeze:
        exact_membership(source_path.parent, freeze['dataSourceFiles'])
    for name in REVIEW_FILES:
        add(pin(review_root / name))
    for item in (source_pin, acceptance_pin, plan_pin, CONTRACT, pin(Path(__file__)),
                 *(pin(Path(tool)) for tool in TOOLS)):
        add(item)
    descriptors = sorted(protected.values(), key=lambda item: item['path'])
    need(len(descriptors) <= FILES, 'PROTECTED_SET_BOUND')
    return dict(source=source, sourcePin=source_pin, acceptancePin=acceptance_pin,
                plan=plan, planPin=plan_pin, counts=counts, total=sum(counts),
                descriptors=descriptors, method=pin(Path(__file__)))


def output_root(path):
    path = safe_path(path)
    need(path.is_relative_to(EVIDENCE) and path != EVIDENCE, 'MODEL_METADATA_OUTPUT_NAMESPACE')
    return path


def prepare(source_path, review_root, output_path, source_sha, acceptance_sha):
    root = output_root(output_path)
    need(not root.exists() and not root.is_symlink(), 'FRESH_OUTPUT_ONLY')
    profile = load_profile(source_path, review_root, source_sha, acceptance_sha)
    before = snapshot(profile['descriptors'], profile['total'])
    root.mkdir(mode=0o700)
    before_pin = put(root / 'before.json', before)
    requests = [put(root / ('%02d-exact-request.json' % i), request(group))
                for i, group in enumerate(profile['plan']['groups'], 1)]
    job = dict(schema='e02-root-current-controller-model-job-plan-v1', actor='/root',
               source=profile['sourcePin'], sourceAcceptance=profile['acceptancePin'],
               sourceReviewRoot=str(safe_path(review_root)), controlPlan=profile['planPin'],
               version=profile['source']['version'], modelsDefined=profile['total'],
               countsSeparate=profile['counts'], requests=requests, inputsBefore=before_pin,
               protectedInputs=len(before['rows']), snapshotDescriptors=profile['descriptors'],
               outputRoot=str(root), actualRequestFamily='MODEL5', method=profile['method'],
               noRetry=True, rootRelease=None, executionAuthorized=False)
    job_pin = put(root / 'job-plan.json', job)
    print(json.dumps(dict(jobPlan=job_pin, modelsDefined=profile['total'],
                          countsSeparate=profile['counts'], requests=len(requests),
                          protectedInputs=len(before['rows']), executionAuthorized=False)))


def revalidate_job(job_path, job_sha):
    job_path = safe_path(job_path)
    job_pin = pin(job_path)
    equal(job_pin['sha256'], text(job_sha, 64), 'EXTERNALLY_SELECTED_JOB_SHA')
    job = verified_doc(job_pin)
    closed(job, JOB_KEYS)
    equal(job['schema'], 'e02-root-current-controller-model-job-plan-v1')
    equal(job['actor'], '/root')
    equal(job['executionAuthorized'], False)
    equal(job['rootRelease'], None)
    equal(job['noRetry'], True)
    equal(job['actualRequestFamily'], 'MODEL5')
    root = output_root(job['outputRoot'])
    equal(str(job_path), str(root / 'job-plan.json'))
    source_pin, acceptance_pin = pin_shape(job['source']), pin_shape(job['sourceAcceptance'])
    profile = load_profile(source_pin['path'], job['sourceReviewRoot'], source_pin['sha256'],
                           acceptance_pin['sha256'])
    for key, value in (('source', profile['sourcePin']), ('sourceAcceptance', profile['acceptancePin']),
                       ('controlPlan', profile['planPin']), ('version', profile['source']['version']),
                       ('modelsDefined', profile['total']), ('countsSeparate', profile['counts']),
                       ('snapshotDescriptors', profile['descriptors']), ('method', profile['method'])):
        equal(job[key], value, 'JOB_CURRENT_AUTHORITY_JOIN')
    equal(job['protectedInputs'], len(profile['descriptors']))
    need(type(job['requests']) is list and len(job['requests']) == len(profile['counts']), 'ALL_REQUESTS')
    for i, (item, group) in enumerate(zip(job['requests'], profile['plan']['groups']), 1):
        equal(pin_shape(item)['path'], str(root / ('%02d-exact-request.json' % i)))
        actual = verified_doc(item)
        equal(canonical_request(actual), canonical_request(request(group)), 'WHOLE_MODEL5_REQUEST')
    equal(pin_shape(job['inputsBefore'])['path'], str(root / 'before.json'))
    before = validate_snapshot(verified_doc(job['inputsBefore']), profile['total'], profile['descriptors'])
    equal(snapshot(profile['descriptors'], profile['total']), before, 'CURRENT_EXPECTED_INPUTS_UNCHANGED')
    return job, profile, before, job_pin


def observe(job_path, job_sha):
    job, profile, before, _ = revalidate_job(job_path, job_sha)
    result = put(Path(job['outputRoot']) / 'after.json', before)
    print(json.dumps(dict(after=result, protectedInputs=len(before['rows']), unchanged=True)))


def release_value(job, job_pin, now):
    integer(now, 0)
    return dict(schema='e02-root-controller-current-mock-release-v1', actor='/root',
                issuedAtUtcMillis=now, notAfterUtcMillis=now + 600000,
                startAllowanceSeconds=120, controllerSource=job['source'],
                controllerSourceAcceptance=job['sourceAcceptance'], controlPlan=job['controlPlan'],
                inputsBefore=job['inputsBefore'], requests=job['requests'], jobPlan=job_pin,
                modelsDefined=job['modelsDefined'], countsSeparate=job['countsSeparate'],
                maximumExecutionsPerGroup=1, groupsSequential=True, stopOnFirstFailure=True,
                noRetry=True, perGroupKillSeconds=63,
                scope='API_ONLY_MOCK_OR_READ_ONLY_MODELS_NO_TARGET_RUNTIME',
                actualRequestFamily='MODEL5', innerPidReapEofAttested=False,
                guardHelperExecutionsAuthorized=0, dockerExecutionsAuthorized=0,
                ordinaryRoleExecutionsAuthorized=0, executionAuthorized=True)


def validate_release(value, job, job_pin):
    need(type(value) is dict, 'RELEASE_OBJECT')
    now = integer(value.get('issuedAtUtcMillis'), 0)
    equal(value, release_value(job, job_pin, now), 'EXACT_TYPED_CURRENT_RELEASE')


def release(job_path, job_sha):
    job, _, _, job_pin = revalidate_job(job_path, job_sha)
    value = release_value(job, job_pin, time.time_ns() // 1_000_000)
    print(json.dumps(dict(release=put(Path(job['outputRoot']) / 'root-release.json', value))))


def response_metadata(response, cap):
    need(type(response) is dict and set(response) <= RESPONSE_KEYS, 'DECLARED_NATIVE_RESPONSE_KEYS')
    integer(cap, 1)
    for key in FLAGS:
        # These flags are optional native metadata. Never repair/coerce them.
        need(key not in response or type(response[key]) is bool and response[key] is False,
             'NO_NEGATIVE_OR_UNKNOWN_API_FLAG')
    need('wall_time_seconds' in response, 'NATIVE_WALL_REQUIRED')
    wall = response['wall_time_seconds']
    need(type(wall) in (int, float, Decimal), 'WALL_NUMBER_TYPE')
    if type(wall) is int:
        integer(wall, 0)
    else:
        need((wall.is_finite() if type(wall) is Decimal else math.isfinite(wall)) and wall >= 0,
             'FINITE_NONNEGATIVE_WALL')
    if 'original_token_count' in response:
        integer(response['original_token_count'], 0, cap)
    # original_token_count is optional in the native API schema. Absence stays
    # absent; this optional counter alone never establishes completeness.
    if 'chunk_id' in response:
        need(bool(text(response['chunk_id'], 256)), 'CHUNK_ID')
    if 'exit_code' in response and response['exit_code'] is not None:
        integer(response['exit_code'], -SAFE, SAFE)
    if 'session_id' in response and response['session_id'] is not None:
        integer(response['session_id'], 1)
    need('output' in response, 'NATIVE_OUTPUT_REQUIRED')
    text(response['output'], OUTPUT)


def complete_origin(origin, expected):
    validate_tree(origin, api=True)
    closed(origin, ('schema', 'operator', 'launch', 'polls'))
    equal(origin['schema'], 'e02-actual-tool-custody-v1')
    equal(origin['operator'], '/root')
    expected_bytes = canonical_request(expected)
    need(type(origin['polls']) is list and len(origin['polls']) <= 128, 'FINITE_ACTUAL_POLLS')
    session, terminal, outputs, total = None, False, [], 0
    for i, frame in enumerate([origin['launch'], *origin['polls']]):
        closed(frame, ('toolName', 'actualArguments', 'unmodifiedResponse'))
        need(not terminal, 'NO_FRAME_AFTER_TERMINAL')
        arguments, response = frame['actualArguments'], frame['unmodifiedResponse']
        if i == 0:
            equal(frame['toolName'], 'tools.exec_command')
            equal(canonical_request(arguments), expected_bytes, 'WHOLE_ACTUAL_MODEL5')
            cap = arguments['max_output_tokens']
        else:
            equal(frame['toolName'], 'tools.write_stdin')
            need(type(arguments) is dict and set(arguments) <= POLL_KEYS, 'DECLARED_POLL_FIELDS')
            integer(arguments.get('session_id'), 1)
            equal(arguments['session_id'], session, 'SAME_SESSION_ARGUMENT')
            need('chars' not in arguments or type(arguments['chars']) is str and arguments['chars'] == '',
                 'READ_ONLY_POLL')
            for key in ('yield_time_ms', 'max_output_tokens'):
                if key in arguments:
                    integer(arguments[key], 1)
            cap = arguments.get('max_output_tokens', 10000)  # Native poll default.
        response_metadata(response, cap)
        if response.get('exit_code') is None:
            integer(response.get('session_id'), 1)
            session = session or response['session_id']
            equal(response['session_id'], session, 'SAME_SESSION_RESPONSE')
        else:
            equal(response['exit_code'], 0, 'NATURAL_API_TERMINAL0')
            need(response.get('session_id') is None or
                 type(response['session_id']) is int and response['session_id'] == session,
                 'TERMINAL_SESSION')
            terminal = True
        output = response.get('output', '').encode('utf8', 'strict')
        total += len(output)
        need(total <= OUTPUT, 'WHOLE_API_OUTPUT_BOUND')
        outputs.append(output)
    need(terminal, 'COMPLETE_TERMINAL_REQUIRED')
    return b''.join(outputs)


def named_output(raw, group):
    need(type(raw) is bytes and len(raw) <= OUTPUT, 'BOUNDED_NAMED_OUTPUT')
    integer(group['count'], 1, 10000)
    value = raw.decode('utf8', 'strict')
    trailer = re.search(r'\n\n-{70}\nRan ([0-9]+) tests? in ([0-9]+(?:\.[0-9]+)?)s\n\nOK\n\Z', value)
    need(trailer is not None and int(trailer[1]) == group['count'], 'COMPLETE_NAMED_TRAILER')
    names = []
    for line in value[:trailer.start()].splitlines():
        match = re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*) \(__main__\.([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_][A-Za-z_0-9]*)\) \.\.\. ok', line)
        need(match is not None and match[1] == match[3], 'EVERY_NAMED_SUCCESS')
        names.append(match[2] + '.' + match[3])
    equal(names, sorted(group['expectedNames']), 'ALL_NAMES_ONCE')
    return names, trailer[2]


def finalize(job_path, job_sha, release_sha):
    job, profile, before, job_pin = revalidate_job(job_path, job_sha)
    root = Path(job['outputRoot'])
    release_pin = pin(root / 'root-release.json')
    equal(release_pin['sha256'], text(release_sha, 64), 'EXTERNAL_RELEASE_SHA')
    validate_release(verified_doc(release_pin), job, job_pin)
    after = validate_snapshot(doc(root / 'after.json'), profile['total'], profile['descriptors'])
    equal(before, after, 'EXACT_BEFORE_AFTER')
    rows, origins, pending = [], [], []
    for i, group in enumerate(profile['plan']['groups'], 1):
        origin_path = root / ('%02d-original-tool-origin.json' % i)
        origin_pin = pin(origin_path)
        output = complete_origin(verified_doc(origin_pin, api=True), request(group))
        names, seconds = named_output(output, group)
        raw_path = root / ('%02d-raw-output.txt' % i)
        need(not raw_path.exists() and not raw_path.is_symlink(), 'FRESH_OUTPUT_RETENTION')
        origins.append(origin_pin)
        pending.append((raw_path, output))
        rows.append(dict(group=group['name'], modelsExecuted=group['count'],
                         modelsPassed=group['count'], modelsFailed=0, actualNames=names,
                         reportedSeconds=seconds, terminalExitCode=0,
                         originalToolOrigin=origin_pin,
                         rawOutput=dict(path=str(raw_path), bytes=len(output),
                                        sha256=hashlib.sha256(output).hexdigest())))
    for path, raw in pending:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            need(stream.write(raw) == len(raw), 'ONE_COMPLETE_RAW_METADATA_WRITE')
    total = profile['total']
    execution = dict(schema='e02-probe-controller-' + profile['source']['version'] + '-' + str(total) + '-mock-execution-v1',
                     actor='/root', groups=rows, modelsDefined=total, modelsExecuted=total,
                     modelsPassed=total, modelsFailed=0, skipped=0, truncated=False,
                     inputsUnchanged=True, protectedInputs=job['protectedInputs'], actualApiOnly=True,
                     innerPidReapEofAttested=False, guardHelperExecutions=0,
                     dockerExecutions=0, ordinaryRoleExecutions=0)
    execution_pin = put(root / 'execution.json', execution)
    members = sorted(root.iterdir())
    need(len(members) <= FILES, 'RAW_MEMBERS_BOUND')
    manifest = dict(schema='e02-controller' + str(total) + '-mock-raw-artifact-manifest-v1',
                    actor='/root', files=[pin(p) for p in members],
                    semantics='Exact selected MODEL5 requests, unmodified complete native API frames, exact named outputs and model metadata. Optional token count is neither invented nor sole completeness evidence. Root dispatch freshness/sequential/once provenance remains external. No target helper/PID/reap/EOF/ordinary claim.')
    manifest_pin = put(root / 'raw-artifact-manifest.json', manifest)
    subject = dict(schema='e02-probe-controller-mock-control-data-subject-v1',
                   authors=list(DESIGN_CONTRIBUTORS), operators=['/root'],
                   controllerSource=job['source'], controllerSourceAcceptance=job['sourceAcceptance'],
                   controlPlan=job['controlPlan'], rootRelease=release_pin, execution=execution_pin,
                   originalToolOrigins=origins, rawArtifactManifest=manifest_pin,
                   inputsBefore=job['inputsBefore'], inputsAfter=pin(root / 'after.json'),
                   inputsUnchanged=True, countsSeparate=job['countsSeparate'], modelsDefined=total,
                   modelsExecuted=total, modelsPassed=total, modelsFailed=0, skipped=0,
                   truncated=False, guardHelperExecutions=0, dockerExecutions=0,
                   ordinaryRoleExecutions=0, ordinaryRowsQualified=0,
                   innerPidReapEofAttested=False, executionAuthorized=False)
    print(json.dumps(dict(subject=put(root / 'subject.json', subject), modelsPassed=total,
                          countsSeparate=profile['counts'], actualRequestFamily='MODEL5',
                          helperExecutions=0)))


def main(args):
    if len(args) == 6 and args[0] == 'prepare':
        prepare(Path(args[1]), Path(args[3]), Path(args[5]), args[2], args[4])
    elif len(args) == 3 and args[0] == 'observe':
        observe(Path(args[1]), args[2])
    elif len(args) == 3 and args[0] == 'release':
        release(Path(args[1]), args[2])
    elif len(args) == 4 and args[0] == 'finalize':
        finalize(Path(args[1]), args[2], args[3])
    else:
        raise Refusal('EXACT_EXTERNALLY_SHA_BOUND_METADATA_ARGUMENTS')


if __name__ == '__main__':
    main(sys.argv[1:])
