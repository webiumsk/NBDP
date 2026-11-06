"""Pure bounded metadata and explicit native request families.

Selected strict primitives are AST-identical to accepted metadata method5e4a.
No IO, target imports, clocks, subprocesses, authority issuance or API dispatch.
Caller Root authenticates actual provenance; structure alone is not authenticity.
"""
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
DATA=16_777_216
RAW=2_147_483_648
OUTPUT=1_048_576
SAFE=9_007_199_254_740_991
I64=9_223_372_036_854_775_807
DEPTH=64
METADATA_DEPTH=48
NODES=250_000
FLAGS={'truncated','output_truncated','interrupted','error','isError'}
RESPONSE_KEYS={'chunk_id','wall_time_seconds','exit_code','original_token_count','output','session_id'}|FLAGS
POLL_KEYS={'session_id','chars','yield_time_ms','max_output_tokens'}
MODEL_KEYS={'cmd','workdir','login','yield_time_ms','max_output_tokens'}
SEVEN_KEYS=MODEL_KEYS|{'sandbox_permissions','justification'}
FAMILIES=('MODEL5','HOST7','COLLECTOR7','PRODUCER_CAPTURE7')
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


def encoded(value):
    validate_tree(value)
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('utf8')


def pin_bytes(path, raw):
    safe_path(path)
    need(type(raw) is bytes and len(raw) <= DATA, 'BOUNDED_PIN_BYTES')
    return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def canonical_request(family, value, policy=None):
    need(family in FAMILIES, 'EXPLICIT_KNOWN_REQUEST_FAMILY')
    closed(value, MODEL_KEYS if family == 'MODEL5' else SEVEN_KEYS)
    text(value['cmd'], DATA)
    safe_path(value['workdir'])
    equal(value['login'], False, 'LOGIN_FALSE_TYPED')
    integer(value['yield_time_ms'], 1, 10000)
    integer(value['max_output_tokens'], 1, 20000)
    if family != 'MODEL5':
        equal(value['sandbox_permissions'], 'require_escalated')
        justification = text(value['justification'], 1024)
        need(bool(justification.strip()), 'NONBLANK_JUSTIFICATION')
    if family in ('HOST7', 'PRODUCER_CAPTURE7'):
        need(type(policy) is dict, 'EXACT_CURRENT_FAMILY_POLICY_REQUIRED')
        closed(policy, SEVEN_KEYS - {'cmd'})
        for key, expected in policy.items():
            equal(value[key], expected, 'EXACT_CURRENT_FAMILY_POLICY')
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf8')


def complete_origin(family, origin, expected, operators, policy=None):
    """Pure native-frame validation; Root supplies genuinely complete frames."""
    validate_tree(origin, api=True)
    closed(origin, ('schema', 'operator', 'launch', 'polls'))
    equal(origin['schema'], 'e02-actual-tool-custody-v1')
    need(type(operators) is list and origin['operator'] in operators,
         'ACTUAL_DISCLOSED_OPERATOR')
    expected_bytes = canonical_request(family, expected, policy)
    maximum_polls = 16 if family == 'COLLECTOR7' else 128
    need(type(origin['polls']) is list and len(origin['polls']) <= maximum_polls,
         'FINITE_COMPLETE_NATIVE_POLLS')
    session, terminal, outputs, total = None, False, [], 0
    for i, frame in enumerate([origin['launch'], *origin['polls']]):
        closed(frame, ('toolName', 'actualArguments', 'unmodifiedResponse'))
        need(not terminal, 'NO_FRAME_AFTER_TERMINAL')
        args, response = frame['actualArguments'], frame['unmodifiedResponse']
        if i == 0:
            equal(frame['toolName'], 'tools.exec_command')
            equal(canonical_request(family, args, policy), expected_bytes,
                  'WHOLE_ACTUAL_FAMILY_REQUEST')
            cap = args['max_output_tokens']
        else:
            equal(frame['toolName'], 'tools.write_stdin')
            need(type(args) is dict and set(args) <= POLL_KEYS, 'POLL_KEYS')
            integer(args.get('session_id'), 1)
            equal(args['session_id'], session, 'SAME_SESSION_ARGUMENT')
            need('chars' not in args or type(args['chars']) is str and args['chars'] == '',
                 'READ_ONLY_EMPTY_POLL')
            for key in ('yield_time_ms', 'max_output_tokens'):
                if key in args:
                    integer(args[key], 1)
            cap = args.get('max_output_tokens', 10000)
        response_metadata(response, cap)
        if family == 'COLLECTOR7':
            # This operational family deliberately retains Source2's stricter
            # present-counter requirement; no MODEL5 fallback or fabrication.
            need('original_token_count' in response, 'COLLECTOR_PRESENT_COUNTER')
        if response.get('exit_code') is None:
            integer(response.get('session_id'), 1)
            session = session or response['session_id']
            equal(response['session_id'], session, 'SAME_SESSION_RESPONSE')
        else:
            equal(response['exit_code'], 0, 'NATURAL_TERMINAL0')
            need(response.get('session_id') is None or
                 type(response['session_id']) is int and response['session_id'] == session,
                 'TERMINAL_SESSION')
            terminal = True
        output = response['output'].encode('utf8', 'strict')
        total += len(output)
        bound = 65536 if family == 'COLLECTOR7' else OUTPUT
        need(total <= bound, 'WHOLE_NATIVE_OUTPUT_BOUND')
        need(not any(marker in response['output'] for marker in
                     ('tokens truncated', 'Warning: truncated output',
                      'Output exceeded the available', '[output truncated]')),
             'NO_TRUNCATION_MARKER')
        outputs.append(output)
    need(terminal, 'COMPLETE_TERMINAL_REQUIRED')
    return b''.join(outputs)


def decode_original_lease(raw, run):
    """Only the closed original lease fields admit I64 clocks here."""
    need(type(raw) is bytes and len(raw) <= 8192, 'SMALL_ORIGINAL_LEASE')
    source = preflight_json(raw)
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'DUPLICATE_LEASE_KEY')
            result[key] = value
        return result
    def number(token):
        need(token != '-0', 'NEGATIVE_ZERO_LEASE')
        return integer(int(token), 0, I64)
    def reject(_):
        raise Refusal('INTEGER_ORIGINAL_LEASE_ONLY')
    lease = json.loads(source, object_pairs_hook=pairs, parse_int=number,
                       parse_float=reject, parse_constant=reject)
    closed(lease, ('schema', 'runId', 'bootId', 'issuedUtcNs', 'issuedMonoNs',
                   'issuedBootNs', 'deadlineUtcNs', 'deadlineMonoNs', 'deadlineBootNs'))
    equal(lease['schema'], 'e02-single-cell-lease-v1')
    equal(lease['runId'], run)
    need(type(run) is str and re.fullmatch('[0-9a-f]{32}', run), 'RUN_ID')
    need(type(lease['bootId']) is str and
         re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', lease['bootId']),
         'BOOT_ID')
    for clock in ('Utc', 'Mono', 'Boot'):
        start, end = lease['issued' + clock + 'Ns'], lease['deadline' + clock + 'Ns']
        integer(start, 0, I64)
        integer(end, 0, I64)
        equal(end - start, 1800 * 1000000000, 'ORIGINAL_NONRENEWABLE_1800')
    return lease


def verified_value(record, api=False):
    """Consume supplied original bytes and descriptor, never read or normalize."""
    closed(record, ('pin', 'raw'))
    pin_shape(record['pin'])
    equal(pin_bytes(record['pin']['path'], record['raw']), record['pin'], 'ORIGINAL_BYTES_PIN')
    return decode_json(record['raw'], api=api)
