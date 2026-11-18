"""Typed Source-mapping receipt admission and unchanged finite reader verifier.

No authority is issued here. All DATA reads use the caller's pre-admitted
Source-only reader; operational helper and opaque negative bodies are denied.
"""
import ast
import copy
from decimal import Decimal
import importlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import re
import shlex
import sys
import sysconfig

METHOD_MEMBERS = ('README.md', 'bootstrap_strict.py', 'build_package.py',
                  'policy.json', 'prepare_mapping.py', 'test_prepare.py')
METHOD_SPEC_KEYS = ('schema actor scope issued executionAuthorized helperSource readerSubject template '
    'designAcceptance root24Governance closureGovernance actorAuthority callerClosure callerClosureEvidence '
    'ordinary inputFiles').split()
RESULT_KEYS = ('schema state author basisIssued executionAuthorized rootIssuanceRequired '
    'prospectiveCompletedStateUsedOnlyInMemory sourceMappingMetadataVerified actualS18M4Verified '
    'completedBasis draftBasis sourceVerification readClosure rootApprovedSpec helperSource').split()
REQUEST_KEYS = ('cmd', 'workdir', 'login', 'yield_time_ms', 'max_output_tokens')
ROOT_PYTHON = '/home/peterhorvath/.miniforge3/bin/python3.13'
SOURCE_INPUT_KINDS = {'READER_CODE', 'SOURCE', 'GOVERNANCE', 'PURE_CONTROL_METADATA'}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def equal(a, b, reason):
    need(same(a, b), reason)


def closed(value, keys, reason):
    need(type(value) is dict and set(value) == set(keys), reason)


def descriptor(value):
    closed(value, ('path', 'bytes', 'sha256'), 'MAPPING_PIN_KEYS')
    need(type(value['path']) is str and Path(value['path']).is_absolute(), 'MAPPING_PIN_PATH')
    need(type(value['bytes']) is int and 0 <= value['bytes'] <= 16777216, 'MAPPING_PIN_BOUND')
    need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'MAPPING_PIN_SHA')
    return value


def review_pair(files, pins, subject, decision, forbidden):
    need(type(pins) is list and len(pins) == 2, 'MAPPING_TWO_ORDERED_REVIEWS')
    sessions = []
    for role, pin in zip(('qa', 'security'), pins):
        descriptor(pin)
        value = files.doc(pin)
        closed(value, ('role', 'session', 'decision', 'subject'), 'MAPPING_CLOSED_REVIEW')
        equal(value['role'], role, 'MAPPING_ORDERED_REVIEW_ROLE')
        equal(value['subject'], subject, 'MAPPING_REVIEW_PREPARATION_RESULT_SUBJECT')
        equal(value['decision'], decision, 'MAPPING_EXACT_REVIEW_DECISION')
        need(type(value['session']) is str and value['session'].startswith('/root/')
             and value['session'] not in forbidden, 'MAPPING_REVIEWER_INDEPENDENCE')
        sessions.append(value['session'])
    need(len(set(sessions)) == 2, 'MAPPING_DISTINCT_REVIEW_SESSIONS')


def expected_request(spec_pin, method_pin, stdout_pin, stderr_pin):
    for pin in (spec_pin, method_pin, stdout_pin, stderr_pin):
        descriptor(pin)
    here = str(Path(method_pin['path']).parent)
    argv = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'LC_ALL=C.UTF-8', 'TZ=UTC',
        '/usr/bin/timeout', '--signal=TERM', '--kill-after=2s', '60s', ROOT_PYTHON, '-I', '-B',
        here + '/prepare_mapping.py', '--spec', spec_pin['path'], '--spec-bytes', str(spec_pin['bytes']),
        '--spec-sha256', spec_pin['sha256'], '--helper-source-bytes', str(method_pin['bytes']),
        '--helper-source-sha256', method_pin['sha256']]
    cmd = ('set -C\numask 077\nexec ' + shlex.join(argv) + ' > ' + shlex.quote(stdout_pin['path'])
           + ' 2> ' + shlex.quote(stderr_pin['path']))
    return dict(cmd=cmd, workdir=here, login=False, yield_time_ms=1000, max_output_tokens=2000)


def decode_native(raw):
    """Preserve native duration decimals only at their genuine response paths."""
    need(type(raw) is bytes and len(raw) <= 16777216, 'MAPPING_NATIVE_BYTES_BOUND')
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'MAPPING_DUPLICATE_NATIVE_KEY')
            value[key] = item
        return value
    def number(token):
        need(token != '-0', 'MAPPING_NATIVE_NEGATIVE_ZERO')
        value = int(token)
        need(-9223372036854775808 <= value <= 9223372036854775807, 'MAPPING_NATIVE_INTEGER_DOMAIN')
        return value
    def constant(_):
        raise ValueError('MAPPING_NONFINITE_NATIVE')
    value = json.loads(raw.decode('utf8', 'strict'), object_pairs_hook=pairs,
        parse_int=number, parse_float=Decimal, parse_constant=constant)
    def walk(item, path=(), depth=0):
        need(depth <= 64, 'MAPPING_NATIVE_DEPTH')
        if isinstance(item, Decimal):
            allowed = (path == ('launch', 'unmodifiedResponse', 'wall_time_seconds')
                or len(path) == 4 and path[0] == 'polls' and type(path[1]) is int
                and path[2:] == ('unmodifiedResponse', 'wall_time_seconds'))
            need(allowed and item.is_finite() and item >= 0, 'MAPPING_NATIVE_DURATION_FLOAT_ONLY')
        elif type(item) is dict:
            for key, child in item.items():
                walk(child, path + (key,), depth + 1)
        elif type(item) is list:
            for index, child in enumerate(item):
                walk(child, path + (index,), depth + 1)
    walk(value)
    return value


def validate_native(origin, request):
    closed(request, REQUEST_KEYS, 'MAPPING_WHOLE_MODEL5_REQUEST')
    need(type(request['cmd']) is str and type(request['workdir']) is str
         and request['login'] is False and type(request['login']) is bool
         and type(request['yield_time_ms']) is int and request['yield_time_ms'] == 1000
         and type(request['max_output_tokens']) is int and request['max_output_tokens'] == 2000,
         'MAPPING_MODEL5_REQUEST_TYPES')
    closed(origin, ('schema', 'operator', 'launch', 'polls'), 'MAPPING_CLOSED_NATIVE_ORIGIN')
    equal(origin['schema'], 'e02-actual-tool-custody-v1', 'MAPPING_NATIVE_ORIGIN_SCHEMA')
    equal(origin['operator'], '/root', 'MAPPING_ACTUAL_ROOT_OPERATOR')
    need(type(origin['polls']) is list and len(origin['polls']) <= 128, 'MAPPING_FINITE_SAME_HANDLE_POLLS')
    session = None
    terminal = False
    output = []
    for index, frame in enumerate([origin['launch'], *origin['polls']]):
        need(not terminal, 'MAPPING_NO_FRAME_AFTER_TERMINAL')
        closed(frame, ('toolName', 'actualArguments', 'unmodifiedResponse'), 'MAPPING_NATIVE_FRAME')
        args = frame['actualArguments']
        response = frame['unmodifiedResponse']
        need(type(response) is dict, 'MAPPING_COMPLETE_NATIVE_RESPONSE')
        if 'wall_time_seconds' in response:
            need(type(response['wall_time_seconds']) in (int, Decimal)
                 and response['wall_time_seconds'] >= 0, 'MAPPING_NATIVE_WALL_DURATION_TYPE')
        if 'original_token_count' in response:
            need(type(response['original_token_count']) is int
                 and 0 <= response['original_token_count'] <= request['max_output_tokens'],
                 'MAPPING_NATIVE_OPTIONAL_COUNTER_TYPE_AND_BOUND')
        if index == 0:
            equal(frame['toolName'], 'tools.exec_command', 'MAPPING_NATIVE_EXEC_LAUNCH')
            equal(args, request, 'MAPPING_EXACT_UNMODIFIED_FIVE_FIELD_REQUEST')
        else:
            equal(frame['toolName'], 'tools.write_stdin', 'MAPPING_NATIVE_SAME_HANDLE_POLL')
            need(type(args) is dict and set(args) <= {'session_id', 'chars', 'yield_time_ms', 'max_output_tokens'},
                 'MAPPING_EMPTY_POLL_FIELDS_ONLY')
            need(type(args.get('session_id')) is int and args['session_id'] == session and session > 0,
                 'MAPPING_EXACT_SAME_HANDLE')
            need('chars' not in args or args['chars'] == '' and type(args['chars']) is str,
                 'MAPPING_NO_POLL_INPUT')
            for field in ('yield_time_ms', 'max_output_tokens'):
                need(field not in args or type(args[field]) is int and args[field] > 0,
                     'MAPPING_POLL_INTEGER_TYPES')
        for field in ('truncated', 'is_truncated', 'output_truncated', 'timed_out', 'timeout', 'forced', 'force_killed'):
            need(field not in response or response[field] is False, 'MAPPING_NATIVE_NO_PARTIAL_OR_FORCED_RESULT')
        if response.get('exit_code') is not None:
            need(type(response['exit_code']) is int and response['exit_code'] == 0,
                 'MAPPING_NATURAL_TERMINAL_ZERO')
            need(response.get('session_id') is None or type(response['session_id']) is int
                 and response['session_id'] == session, 'MAPPING_TERMINAL_HANDLE_IDENTITY')
            terminal = True
        else:
            need(type(response.get('session_id')) is int and response['session_id'] > 0,
                 'MAPPING_REAL_LIVE_HANDLE')
            session = session or response['session_id']
            need(response['session_id'] == session, 'MAPPING_LIVE_HANDLE_IDENTITY')
        if 'output' in response:
            need(type(response['output']) is str and len(response['output'].encode()) <= 16777216,
                 'MAPPING_COMPLETE_BOUNDED_NATIVE_OUTPUT')
            output.append(response['output'])
    need(terminal, 'MAPPING_COMPLETE_TERMINAL_ORIGIN_REQUIRED')
    equal(''.join(output), '', 'MAPPING_REDIRECTED_NATIVE_STDOUT_IS_EMPTY')


class SourceFiles:
    """Exact method-declared modes over the consumer's finite nine-denial reader."""
    def __init__(self, reader, rows, basis_pin):
        self.reader = reader
        self.rows = {row['pin']['path']: row for row in rows}
        self.basis_pin = basis_pin

    def read(self, pin, maximum=16777216, *, expected_mode=None):
        descriptor(pin)
        need(pin['bytes'] <= maximum, 'MAPPING_PUBLIC_READ_BOUND')
        row = self.rows.get(pin['path'])
        if row is None:
            equal(pin, self.basis_pin, 'MAPPING_NO_UNDECLARED_PUBLIC_VERIFIER_READ')
            need(expected_mode is None, 'MAPPING_BASIS_METADATA_HAS_NO_SOURCE_MODE')
            return self.reader.read(pin['path'], pin)[1]
        equal(row['pin'], pin, 'MAPPING_EXACT_PUBLIC_VERIFIER_CAPABILITY')
        if expected_mode is not None:
            equal(row['mode'], expected_mode, 'MAPPING_DECLARED_SOURCE_MODE')
        return self.reader.read(pin['path'], pin, row['mode'])[1]

    def read_mode(self, pin, mode, maximum=16777216):
        return self.read(pin, maximum, expected_mode=mode)

    def doc(self, pin):
        # The unchanged verifier uses its own strict values and schema checks.
        return sys.modules['strict'].validate_numbers(sys.modules['strict'].loads(self.read(pin)))

    def recheck(self):
        self.reader.recheck()


class PinnedReaderFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, bodies):
        self.bodies = bodies

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.bodies:
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        pin, body = self.bodies[module.__name__]
        module.__file__ = pin['path']
        exec(compile(body, pin['path'], 'exec'), module.__dict__)


def validate_public_basis(reader, rows, reader_subject_pin, basis_pin, template_pin,
                          design_pin, ordinary, forbidden):
    """Load verified immutable16 Source members and call the unchanged API."""
    subject = reader.doc(reader_subject_pin)
    equal(subject['schema'], 'e02-ordinary-consumer6-source-subject-v1', 'MAPPING_FROZEN_READER_SCHEMA')
    equal(subject['version'], 'SOURCE5', 'MAPPING_FROZEN_READER_VERSION')
    members = subject['runtimeSources']
    need(type(members) is list and len(members) == subject['runtimeSourceCount'] == 16,
         'MAPPING_EXACT_FROZEN_SIXTEEN_READER_MEMBERS')
    index = {row['pin']['path']: row for row in rows}
    bodies = {}
    for pin in members:
        descriptor(pin)
        name = Path(pin['path']).stem
        need(name not in bodies and Path(pin['path']).parent == Path(subject['sourceRoot']),
             'MAPPING_EXACT_FROZEN_READER_PATHS')
        row = index.get(pin['path'])
        need(row is not None and row['kind'] == 'READER_CODE' and row['pin'] == pin,
             'MAPPING_AUTHENTICATED_READER_CODE_CAPABILITY')
        bodies[name] = (pin, reader.read(pin['path'], pin, row['mode'])[1])
    constants = {}
    for node in ast.parse(bodies['consumer'][1]).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    equal([Path(pin['path']).name for pin in members], list(constants['RUNTIME_FILES']),
          'MAPPING_FROZEN_READER_LITERAL_ORDER')
    need(not (set(bodies) & set(sys.modules)), 'MAPPING_FRESH_FROZEN_READER_NAMESPACE')
    finder = PinnedReaderFinder(bodies)
    previous_path = list(sys.path)
    stdlib = Path(sysconfig.get_path('stdlib')).resolve()
    permitted = {stdlib, stdlib / 'lib-dynload', stdlib.parent / ('python' + str(sys.version_info.major)
                 + str(sys.version_info.minor) + '.zip')}
    sys.path[:] = [p for p in sys.path if p and Path(p).resolve() in permitted]
    sys.meta_path.insert(0, finder)
    try:
        module = importlib.import_module('probe_adapter')
        for name in set(bodies) & set(sys.modules):
            equal(sys.modules[name].__file__, bodies[name][0]['path'], 'MAPPING_ACTUAL_LOADED_FROZEN_CODE')
        files = SourceFiles(reader, rows, basis_pin)
        checked, union = module.validate_component_basis(files, basis_pin, template_pin,
                                                         design_pin, ordinary, forbidden)
        equal(checked, reader.doc(basis_pin), 'MAPPING_UNCHANGED_PUBLIC_VERIFIER_BASIS')
        equal(sorted(union), sorted(forbidden), 'MAPPING_EXACT_COMPLETE_FROZEN_ACTOR_UNION')
        files.recheck()
        return checked
    finally:
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        for name in bodies:
            sys.modules.pop(name, None)
        sys.path[:] = previous_path


def validate_mapping_receipt(reader, spec, values, participants, contract):
    """All structural, provenance, transformation and real Source facts gates."""
    evidence = spec['basisVerificationEvidence']
    need(type(evidence) is list and len(evidence) == 1, 'EXACT_ONE_TYPED_MAPPING_RECEIPT')
    receipt_pin = descriptor(evidence[0])
    receipt = reader.doc(receipt_pin)
    closed(receipt, contract['receipt']['exactKeys'], 'CLOSED_FIFTEEN_KEY_MAPPING_RECEIPT')
    for key, literal in contract['receipt']['literals'].items():
        equal(receipt[key], literal, 'MAPPING_RECEIPT_LITERAL:' + key)
    for key in contract['receipt']['pinKeys']:
        descriptor(receipt[key])
    equal(receipt['subject'], spec['helperComponentBasis'], 'MAPPING_RECEIPT_EXACT_COMPLETED_BASIS')
    approved = contract['approvedMethod']
    equal(receipt['methodSource'], approved['code'], 'MAPPING_APPROVED_METHOD_CODE_PIN')
    equal(receipt['methodSourceAcceptance'], approved['sourceAcceptance'], 'MAPPING_APPROVED_METHOD_SOURCE_RECEIPT')
    method = reader.doc(receipt['methodSource'])
    closed(method, ('schema author scope sourceCount sources modelsDefined modelsExecuted '
                   'executionAuthorized bootstrapByteIdentical').split(), 'MAPPING_CLOSED_METHOD_SOURCE')
    equal(method['schema'], 'e02-helper-component-basis-preparation-code-v1', 'MAPPING_METHOD_SCHEMA')
    equal(method['scope'], 'SOURCE_PREPARATION_ONLY_NO_ISSUANCE', 'MAPPING_METHOD_SCOPE')
    equal(method['executionAuthorized'], False, 'MAPPING_METHOD_NO_RUNTIME_GRANT')
    equal(method['modelsExecuted'], 0, 'MAPPING_METHOD_DEFINITIONS_ONLY')
    equal(method['sourceCount'], 6, 'MAPPING_SIX_SOURCE_METHOD_MEMBERS')
    equal(method['bootstrapByteIdentical'], True, 'MAPPING_UNCHANGED_BOUNDED_BOOTSTRAP')
    sources = method['sources']
    equal([Path(pin['path']).name for pin in sources], list(METHOD_MEMBERS), 'MAPPING_EXACT_METHOD_CODE_INVENTORY')
    method_root = Path(receipt['methodSource']['path']).parent
    for pin in sources:
        descriptor(pin)
        equal(Path(pin['path']).parent, method_root, 'MAPPING_CLOSED_METHOD_CODE_ROOT')
        reader.read(pin['path'], pin)
    forbidden = set(participants) | {method['author'], '/root'}
    method_ack = reader.doc(receipt['methodSourceAcceptance'])
    closed(method_ack, approved['sourceAcceptanceExactKeys'], 'MAPPING_CLOSED_METHOD_ACCEPTANCE')
    for key, expected in dict(schema=approved['sourceAcceptanceSchema'], actor='/root',
        decision=approved['sourceAcceptanceDecision'], subject=receipt['methodSource'],
        modelsDefined=method['modelsDefined'], sourceMappingExecutions=0,
        completedBasisIssued=False, scope='METADATA_ONLY_SOURCE_MAPPING_PREPARATION_CODE_AND_DEFINITIONS_ONLY',
        executionAuthorized=False).items():
        equal(method_ack[key], expected, 'MAPPING_METHOD_ACCEPTANCE_JOIN:' + key)
    review_pair(reader, method_ack['reviews'], receipt['methodSource'], approved['sourceReviewDecision'], forbidden)
    preparation = reader.doc(receipt['preparationSpec'])
    closed(preparation, METHOD_SPEC_KEYS, 'MAPPING_EXACT_PREPARATION_SPEC_KEYS')
    for key, expected in dict(schema='e02-helper-component-basis-preparation-spec-v2', actor='/root',
        scope='VERIFY_ORIGINAL_HELPER_COMPONENT_SOURCE_MAPPING_ONLY', issued=True,
        executionAuthorized=False, helperSource=receipt['methodSource'],
        template=values['CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE'],
        designAcceptance=values['CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE'],
        actorAuthority=spec['actorAuthority'], callerClosure=spec['callerClosure'],
        callerClosureEvidence=spec['callerClosureEvidence']).items():
        equal(preparation[key], expected, 'MAPPING_PREPARATION_SPEC_JOIN:' + key)
    template = reader.doc(preparation['template'])
    equal(preparation['root24Governance'], template['originalBasis']['helperDataAcceptance'],
          'MAPPING_ORIGINAL_ROOT24_GOVERNANCE')
    ordinary = dict(producerSource=values['CURRENT_PRODUCER'],
        producerSourceAcceptance=values['CURRENT_PRODUCER_SOURCE_ACCEPTANCE'],
        producerControlData=spec['producerControlData'], producerControlAcceptance=spec['producerControlAcceptance'],
        captureSource=spec['captureSource'], captureSourceAcceptance=spec['captureSourceAcceptance'],
        admissionDataAcceptance=spec['admissionDataAcceptance'], controlPlan=values['CURRENT_SOURCE_PLAN'],
        countsSeparate=[129,33,29,16,20,10,11,8,7,3,20], modelsDefined=286)
    equal(preparation['ordinary'], ordinary, 'MAPPING_EXACT_GENUINE_ORDINARY_TUPLE')
    policy = reader.doc(next(pin for pin in sources if Path(pin['path']).name == 'policy.json'))
    for key in ('readerSubject', 'template', 'designAcceptance', 'root24Governance',
                'closureGovernance', 'actorAuthority', 'callerClosure', 'callerClosureEvidence'):
        equal(preparation[key], policy[key], 'MAPPING_FROZEN_METHOD_POLICY:' + key)
    bootstrap = next(pin for pin in sources if Path(pin['path']).name == 'bootstrap_strict.py')
    equal({key: bootstrap[key] for key in ('bytes', 'sha256')},
          {key: policy['bootstrapSource'][key] for key in ('bytes', 'sha256')},
          'MAPPING_FROZEN_BOUNDED_BOOTSTRAP_IDENTICAL')
    rows = preparation['inputFiles']
    need(type(rows) is list and 1 <= len(rows) <= 20000, 'MAPPING_FINITE_INPUT_CAPABILITIES')
    paths = set()
    for row in rows:
        closed(row, ('pin', 'mode', 'kind'), 'MAPPING_TYPED_INPUT_CAPABILITY')
        pin = descriptor(row['pin'])
        need(pin['path'] not in paths and type(row['mode']) is int and 0 <= row['mode'] <= 0o7777
             and row['kind'] in SOURCE_INPUT_KINDS, 'MAPPING_UNIQUE_TYPED_MODE_CAPABILITIES')
        paths.add(pin['path'])
    # Atomic caller-side admission checks all nine denials before any row read.
    if getattr(reader, 'require_pre_admission', False):
        need(all(reader.capabilities.get(row['pin']['path']) == row['pin'] for row in rows),
             'MAPPING_METHOD_ROWS_ALREADY_IN_ROOT_CONSUMER_CAPABILITIES')
    reader.admit([row['pin'] for row in rows])
    execution = reader.doc(receipt['execution'])
    closed(execution, contract['execution']['exactKeys'], 'CLOSED_NINE_KEY_MAPPING_EXECUTION')
    for key, literal in contract['execution']['literals'].items():
        equal(execution[key], literal, 'MAPPING_EXECUTION_LITERAL:' + key)
    for key in ('preparationSpec', 'methodSource', 'originalToolOrigin'):
        equal(execution[key], receipt[key], 'MAPPING_EXECUTION_RECEIPT_JOIN:' + key)
    equal(execution['stdout'], receipt['preparationResult'], 'MAPPING_RESULT_EXACT_STDOUT_FILE')
    descriptor(execution['stderr'])
    equal(reader.read(execution['stderr']['path'], execution['stderr'])[1], b'', 'MAPPING_COMPLETE_EMPTY_STDERR')
    request = expected_request(receipt['preparationSpec'], receipt['methodSource'],
                               receipt['preparationResult'], execution['stderr'])
    equal(execution['request'], request, 'MAPPING_EXACT_REVIEWED_CANONICAL_MODEL5_REQUEST')
    native_raw = reader.read(receipt['originalToolOrigin']['path'], receipt['originalToolOrigin'])[1]
    validate_native(decode_native(native_raw), request)
    result = reader.doc(receipt['preparationResult'])
    closed(result, RESULT_KEYS, 'MAPPING_CLOSED_ACTUAL_PREPARATION_RESULT')
    equal(result['schema'], contract['preparationResult']['schema'], 'MAPPING_RESULT_SCHEMA')
    for key, literal in contract['preparationResult']['required'].items():
        equal(result[key], literal, 'MAPPING_RESULT_UNISSUED_LITERAL:' + key)
    equal(result['rootApprovedSpec'], receipt['preparationSpec'], 'MAPPING_RESULT_APPROVED_SPEC')
    equal(result['helperSource'], receipt['methodSource'], 'MAPPING_RESULT_ACCEPTED_METHOD')
    equal(result['author'], method['author'], 'MAPPING_RESULT_METHOD_AUTHOR')
    equal(result['readClosure'], sorted(rows, key=lambda row: row['pin']['path']), 'MAPPING_COMPLETE_ACTUAL_READ_CLOSURE')
    draft = result['draftBasis']
    closed(draft, template, 'MAPPING_CLOSED_SIXTEEN_DRAFT_BASIS')
    transformation = contract['completedBasisTransformation']
    for key, value in transformation['fromValues'].items():
        equal(draft[key], value, 'MAPPING_DRAFT_IS_UNISSUED:' + key)
    completed = copy.deepcopy(draft)
    completed.update(transformation['toValues'])
    basis = reader.doc(spec['helperComponentBasis'])
    equal(completed, basis, 'MAPPING_EXACT_THREE_VALUE_ROOT_COMPLETION_ONLY')
    equal(result['sourceVerification'], basis['sourceVerification'], 'MAPPING_RESULT_FACTS_MATCH_COMPLETED_BASIS')
    # Inspect descriptors for cycles without following any additional operand.
    banned = {receipt_pin['path'], spec['helperComponentBasis']['path']}
    def no_reference(value):
        if type(value) is dict:
            if set(value) == {'path', 'bytes', 'sha256'}:
                need(value['path'] not in banned, 'MAPPING_NO_RECEIPT_OR_BASIS_BACK_EDGE')
            for child in value.values():
                no_reference(child)
        elif type(value) is list:
            for child in value:
                no_reference(child)
    for value in (draft, preparation):
        no_reference(value)
    review_pair(reader, receipt['reviews'], receipt['preparationResult'],
                contract['reviewEnvelope']['decision'], forbidden)
    checked = validate_public_basis(reader, rows, preparation['readerSubject'], spec['helperComponentBasis'],
        preparation['template'], preparation['designAcceptance'], ordinary, forbidden)
    reader.recheck()
    equal(checked, basis, 'MAPPING_ALL_TYPED_AND_RECOMPUTED_FACTS_AGREE')
    return receipt_pin
