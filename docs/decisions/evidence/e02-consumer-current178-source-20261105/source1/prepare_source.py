"""Bounded SOURCE preparation only. Never imports or executes consumer code."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil

REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE = REPO / 'docs/decisions/evidence'
OWNED = Path(__file__).resolve().parent
SOURCE = OWNED / 'source'
BASE = EVIDENCE / 'e02-consumer266-source-preparation-20261104/r2/source'
SCOPE_PATH = EVIDENCE / 'e02-goal-resume-20261104/consumer-current178-root-scope-20261105.json'
SCOPE = json.loads(SCOPE_PATH.read_bytes())
TUPLE = SCOPE['currentTuple']
ACTOR = '/root/consumer_current178_source'


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')
    return pin(path)


def replace_assign(text, changes):
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    replacements = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in changes:
                replacements.append((node.lineno - 1, node.end_lineno, name + ' = ' + repr(changes[name]) + '\n'))
    assert {node.targets[0].id for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in changes} == set(changes)
    for start, end, value in reversed(replacements):
        lines[start:end] = [value]
    return ''.join(lines)


def replace_function(text, name, body):
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = text.splitlines(keepends=True)
    lines[node.lineno - 1:node.end_lineno] = [body.rstrip() + '\n']
    return ''.join(lines)


def baseline_assignments(name):
    tree = ast.parse((BASE / name).read_bytes())
    return {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
            and isinstance(n.value, (ast.Constant, ast.Dict, ast.List, ast.Tuple))}


def method_inventory(path):
    tree = ast.parse(path.read_bytes())
    return [(c.name + '.' + m.name, ast.dump(m, include_attributes=False))
            for c in tree.body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]


def setup():
    assert pin(SCOPE_PATH)['sha256'] == '101ad3f34c69eaffcc0f1c5f6a9af876bdae45ffc40ef4f4d0aaf65b52db75c2'
    assert SCOPE['owner'] == ACTOR and SCOPE['ownedWritableRoot'] == str(OWNED)
    for key in ('producerSource', 'producerSourceAcceptance', 'producerData', 'producerDataAcceptance',
                'controllerSource', 'controllerSourceAcceptance', 'controllerData', 'controllerDataAcceptance',
                'collectorSource', 'collectorSourceAcceptance', 'collectorData', 'collectorDataAcceptance',
                'strictMetadataMethod', 'strictMetadataMethodAcceptance', 'host7Policy'):
        expected = TUPLE[key]
        assert pin(Path(expected['path'])) == expected
    SOURCE.mkdir(parents=True, exist_ok=True)
    for item in BASE.iterdir():
        if item.is_file():
            shutil.copyfile(item, SOURCE / item.name)
    (OWNED / 'contracts').mkdir(exist_ok=True)
    contract_path = EVIDENCE / 'e02-consumer6-preparation-20261029/current-consumer-acceptance-contract.json'
    contract = json.loads(contract_path.read_bytes())
    contract['requirements'] = [line.replace('accepted260', 'accepted current266').replace('producer22/61/34802/sourceAcceptance and actual260Root43ff', 'producer22/64/d422/currentSourceAcceptance and actual266Root91a0') for line in contract['requirements']]
    contract['editorialSuccessor'] = dict(previous=pin(contract_path), scope='Current266/64 editorial references only; closed keys/literals/decisions and dynamic counts unchanged.')
    return save(OWNED / 'contracts/current-consumer-acceptance-contract.json', contract)


def patch_consumer(contract_pin):
    producer = json.loads(Path(TUPLE['producerSource']['path']).read_bytes())
    by_name = {Path(x['path']).name: x for x in producer['sources']}
    bindings = json.loads(Path(by_name['rebuilt-artifact-bindings.json']['path']).read_bytes())
    constants = baseline_assignments('consumer.py')
    runtimes = constants['RUNTIME_FILES'] + ('request_families.py', 'collector_contracts.py')
    controls = constants['CONTROL_FILES'] + ('test_request_families.py',)
    code = (SOURCE / 'consumer.py').read_text()
    changes = dict(PRODUCER_SHA=TUPLE['producerSource']['sha256'], CURRENT_PRODUCER=TUPLE['producerSource'],
        CURRENT_SOURCE_PLAN=producer['controlPlan'], CURRENT_GUARD_DTO=producer['typedContract'],
        CURRENT_EXPORT_CONTRACT=by_name['EXPORT-CONTRACT.md'], CURRENT_ARTIFACT_BINDINGS=by_name['rebuilt-artifact-bindings.json'],
        CURRENT_AMETHYST_APK=bindings['amethystApk'], CURRENT_HELPER_APK=bindings['helperApk'],
        CURRENT_CONFIGURATIONS=list(producer['configurations'].values()), CURRENT_WORKERS=producer['runtimeSources'],
        CURRENT_PRODUCER_SOURCE_ACCEPTANCE=TUPLE['producerSourceAcceptance'],
        CURRENT_CAPTURE_SOURCE=TUPLE['producerCaptureSource'], CURRENT_CAPTURE_SOURCE_ACCEPTANCE=TUPLE['producerCaptureSourceAcceptance'],
        CURRENT_ADMISSION_DATA_ACCEPTANCE=TUPLE['producerAdmissionDataAcceptance'],
        CURRENT_PRODUCER_CONTROL_DATA=TUPLE['producerData'], CURRENT_PRODUCER_CONTROL_ACCEPTANCE=TUPLE['producerDataAcceptance'],
        CURRENT_CONTROL_ACTORS=sorted(set(constants['CURRENT_CONTROL_ACTORS']) | set(SCOPE['knownPrerequisiteActors']) | {ACTOR, '/root/root_failstop_bridge_source'}),
        CURRENT_CONSUMER_ACCEPTANCE_CONTRACT=contract_pin, RUNTIME_FILES=runtimes, CONTROL_FILES=controls)
    capture_contract = Path(TUPLE['producerCaptureSource']['path']).parent / 'contracts/current-producer-data-acceptance-contract-266.json'
    changes['CURRENT_DATA_ACCEPTANCE_CONTRACT'] = pin(capture_contract)
    helper_contract = EVIDENCE / 'e02-helper-current178-source-20261105/source1/helper-probe-data-acceptance-contract.json'
    helper_pin = pin(helper_contract)
    assert helper_pin['bytes'] == 3325 and helper_pin['sha256'] == '14f859491411c84ec03bc552f0be287269f6ff94a9d4b43cf7cdf22e650fdacc'
    previous_helper = json.loads(Path(constants['CURRENT_HELPER_PROBE_ACCEPTANCE_CONTRACT']['path']).read_bytes())
    current_helper = json.loads(helper_contract.read_bytes())
    for key in ('closedKeys', 'literals', 'pinKeys', 'reviews'):
        assert current_helper[key] == previous_helper[key]
    changes['CURRENT_HELPER_PROBE_ACCEPTANCE_CONTRACT'] = helper_pin
    code = replace_assign(code, changes)
    code = code.replace('import probe_adapter\n', 'import probe_adapter\nimport request_families\nimport collector_contracts\n')
    code = code.replace('actual=cc.validate_origin(api,row[\'request\'],data[\'operators\'])', "actual=cc.validate_origin(api,row['request'],data['operators'],family='MODEL5')")
    code = code.replace("'EXACT_CURRENT_PRODUCER4_SOURCE4_LEASE_DECODE_R1'", "'EXACT_CURRENT_PRODUCER4_SOURCE4_CURRENT_ARTIFACT_BINDINGS'")
    code = code.replace("'EXACT_CURRENT12_RUNTIME_PINS'", "'EXACT_CURRENT_RUNTIME_PINS'")
    collector_contract = prepare_collector_contract()
    extra = dict(CURRENT_NATIVE=bindings['rustBinary'], CURRENT_NATIVE_ACCEPTANCE=bindings['nativeBuildAcceptance'],
                 CURRENT_E01_REPORT=bindings['acceptedE01'], CURRENT_E01_ACCEPTANCE=bindings['acceptedE01Acceptance'],
                 CURRENT_COLLECTOR_SOURCE=TUPLE['collectorSource'], CURRENT_COLLECTOR_SOURCE_ACCEPTANCE=TUPLE['collectorSourceAcceptance'],
                 CURRENT_COLLECTOR_DATA=TUPLE['collectorData'], CURRENT_COLLECTOR_DATA_ACCEPTANCE=TUPLE['collectorDataAcceptance'],
                 CURRENT_COLLECTOR_PREREQUISITE_CONTRACT=collector_contract)
    marker = '_ACTIVE_BINDINGS = None'
    code = code.replace(marker, '\n'.join(k + ' = ' + repr(v) for k, v in extra.items()) + '\n\n' + marker, 1)
    body = '''def current_producer(files, descriptor):
    equal(descriptor,CURRENT_PRODUCER,'EXACT_CURRENT_PRODUCER4_SOURCE4_CURRENT_ARTIFACT_BINDINGS')
    producer=files.doc(descriptor);equal(producer['schema'],CURRENT_PRODUCER_SCHEMA)
    equal(producer['version'],'SOURCE4');equal(producer['sourceRevision'],'CURRENT_ACCEPTED_ARTIFACT_BINDINGS_R1')
    equal(producer['runtimeSourceCount'],22);equal(producer['sourceCount'],64)
    equal(producer['typedContract'],CURRENT_GUARD_DTO);equal(producer['controlPlan'],CURRENT_SOURCE_PLAN)
    equal(producer['runtimeSources'],CURRENT_WORKERS);equal(list(producer['configurations'].values()),CURRENT_CONFIGURATIONS)
    need(len(producer['sources'])==64 and len({Path(p['path']).name for p in producer['sources']})==64,'EXACT_CURRENT64_SOURCE22_WORKERS')
    for p in producer['sources']:files.read(p)
    bindings=files.doc(CURRENT_ARTIFACT_BINDINGS)
    for prefix,artifact,schema,decision in (
      ('amethyst',CURRENT_AMETHYST_APK,'nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1','ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY'),
      ('helper',CURRENT_HELPER_APK,'nbdp-actual-artifact-data-acceptance-v1','ACCEPT_REBUILT_HELPER_ARTIFACT_ONLY')):
        equal(bindings[prefix+'Apk'],artifact)
        acceptance=files.doc(bindings[prefix+'Acceptance']);equal(acceptance['schema'],schema);equal(acceptance['decision'],decision)
        equal(acceptance['artifactQualified'],True);equal(acceptance['subject'],bindings[prefix+'Provenance'])
        equal(files.doc(bindings[prefix+'Provenance'])['apk'],artifact)
    for key,expected in [('rustBinary',CURRENT_NATIVE),('nativeBuildAcceptance',CURRENT_NATIVE_ACCEPTANCE),
                         ('acceptedE01',CURRENT_E01_REPORT),('acceptedE01Acceptance',CURRENT_E01_ACCEPTANCE)]:
        equal(bindings[key],expected,'EXACT_CURRENT_NATIVE_E01_BINDING')
    native=files.doc(CURRENT_NATIVE_ACCEPTANCE)
    equal(native['schema'],'nbdp-native-build-compilation-evidence-acceptance-v1')
    equal(native['decision'],'ACCEPT_NEW_NATIVE_COMPILATION_ARTIFACT_ONLY');equal(native['binary'],CURRENT_NATIVE)
    e01=files.doc(CURRENT_E01_ACCEPTANCE)
    for key,expected in [('schema','nbdp-e01-rebuilt-native-actual-acceptance-v1'),('actor','/root'),
                         ('decision','ACCEPT_ACTUAL_E01_REPLAY_FOR_EXACT_REBUILT_NATIVE_CANDIDATE'),
                         ('report',CURRENT_E01_REPORT),('actualTests',140),('status','PASS'),
                         ('nativeSha256',CURRENT_NATIVE['sha256'])]:equal(e01[key],expected,'CURRENT_E01_PASS140_FOR_EXACT_NATIVE')
    # E01 report contains scientific duration floats. Its exact RAW bytes are
    # pinned by the current accepted receipt, never globally float-widened JSON.
    files.read(CURRENT_E01_REPORT)
    for p in CURRENT_CONFIGURATIONS:
        config=files.doc(p);equal(config['sourceAndDependencyPins'],CURRENT_WORKERS)
        equal(config['profileId'],wire.PROFILE);equal(config['scope'],RUNTIME_SCOPE)
        equal(config['amethystApk'],CURRENT_AMETHYST_APK);equal(config['helperApk'],CURRENT_HELPER_APK)
        equal(config['originalLeaseSeconds'],1800)
    return producer'''
    code = replace_function(code, 'current_producer', body)
    code = code.replace("    from current_controls import validate_data\n", "    origin.forbidden |= probe_adapter.validate_collector_authority(files, CURRENT_COLLECTOR_PREREQUISITE_CONTRACT, origin.forbidden)\n    from current_controls import validate_data\n")
    (SOURCE / 'consumer.py').write_text(code)
    return changes, runtimes, controls


def prepare_collector_contract():
    source = json.loads(Path(TUPLE['collectorSource']['path']).read_bytes())
    src = json.loads(Path(TUPLE['collectorSourceAcceptance']['path']).read_bytes())
    data = json.loads(Path(TUPLE['collectorData']['path']).read_bytes())
    acceptance = json.loads(Path(TUPLE['collectorDataAcceptance']['path']).read_bytes())
    execution = json.loads(Path(data['execution']['path']).read_bytes())
    manifest = json.loads(Path(data['rawArtifactManifest']['path']).read_bytes())
    control = next(p for p in source['sources'] if Path(p['path']).name == 'control-plan.json')
    value = dict(schema='e02-current-collector-source2-prerequisite-contract-v1', actor=ACTOR,
        source=TUPLE['collectorSource'], sourceAcceptance=TUPLE['collectorSourceAcceptance'],
        data=TUPLE['collectorData'], dataAcceptance=TUPLE['collectorDataAcceptance'], controlPlan=control,
        qualifier=TUPLE['operationalQualifier'], history=TUPLE['historyPrefix'], codec=TUPLE['losslessCollectorCodec'],
        operationalCollector=TUPLE['operationalCollector'],
        sourceAcceptanceClosedKeys=sorted(src), dataClosedKeys=sorted(data), dataAcceptanceClosedKeys=sorted(acceptance),
        sourceDecision=src['decision'], sourceReviewDecision=json.loads(Path(src['reviews'][0]['path']).read_bytes())['decision'],
        dataDecision=acceptance['decision'], dataReviewDecision=json.loads(Path(acceptance['reviews'][0]['path']).read_bytes())['decision'],
        sourceScope=src['scope'], dataScope=acceptance['scope'],
        execution=data['execution'], rawManifest=data['rawArtifactManifest'],
        modelRequest=execution['argvRequest'], stdout=execution['stdout'], stderr=execution['stderr'],
        rawFiles=manifest['files'], executionParsing='Exact RAW pin only: runnerReportedSeconds is a scientific report duration, not global JSON float permission.',
        executionAuthorized=False, actualOperationalCollectorCommands=0)
    return save(OWNED / 'contracts/current-collector-prerequisite-contract.json', value)


def patch_capture_and_probe():
    current = Path(TUPLE['producerCaptureSource']['path']).parent
    code = (current / 'contracts.py').read_text()
    code = replace_function(code, 'decode_tool_origin', '''def decode_tool_origin(raw):
    from request_families import decode_tool_origin as decode
    return decode(raw)''')
    code = replace_function(code, 'validate_origin', '''def validate_origin(origin, expected, operators, *, family):
    from request_families import validate_origin as validate
    return validate(origin, expected, operators, family=family)''')
    # Current accepted capture constants/counts/known18 are retained. Structured
    # authority equality is narrowed to the consumer's type-preserving contract.
    tree = ast.parse(code)
    class TypedEquality(ast.NodeTransformer):
        def visit_Compare(self, node):
            self.generic_visit(node)
            if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                call = ast.Call(func=ast.Name(id='same', ctx=ast.Load()), args=[node.left, node.comparators[0]], keywords=[])
                return ast.copy_location(ast.UnaryOp(op=ast.Not(), operand=call) if isinstance(node.ops[0], ast.NotEq) else call, node)
            return node
    tree = TypedEquality().visit(tree)
    ast.fix_missing_locations(tree)
    code = 'from strict import same\n' + ast.unparse(tree) + '\n'
    (SOURCE / 'capture_contracts.py').write_text(code)
    shutil.copyfile(current / 'outputs.py', SOURCE / 'capture_outputs.py')
    code = (SOURCE / 'current_controls.py').read_text()
    code = code.replace("str(Path(capture_pin['path']).parent)),ack['operators'])", "str(Path(capture_pin['path']).parent)),ack['operators'],family='PRODUCER_CAPTURE7')")
    (SOURCE / 'current_controls.py').write_text(code)
    code = (SOURCE / 'probe_adapter.py').read_text()
    code = code.replace('import capture_contracts as c', 'import capture_contracts as c\nimport request_families as families')
    old = "return dict(cmd=shlex.join(argv),workdir=str(Path(host['path']).parent),login=False,yield_time_ms=1000,max_output_tokens=2000)"
    code = code.replace(old, old[:-1] + ",**families.HOST_POLICY)")
    insertion = '''    if schema == 'e02-collector-actual-request7-typed-origin-composite-source-subject-v2':
        equal(value.get('executionAuthorized'), False, 'COLLECTOR_COMPOSITE_SOURCE_ONLY')
        need(type(value.get('sourceContributorUnion')) is list and value['sourceContributorUnion'], 'DECLARED_COMPOSITE_COLLECTOR_CREATORS')
        creators = actors(value['sourceContributorUnion'])
        need(value.get('actor') in creators, 'COMPOSITE_ACTOR_IN_UNION')
        return creators
'''
    code = code.replace("    need(False,'UNKNOWN_SOURCE_ACTOR_SCHEMA')", insertion + "    need(False,'UNKNOWN_SOURCE_ACTOR_SCHEMA')")
    code = code.replace("c.validate_origin(api,expected_request(data,controller),data['operators'])", "c.validate_origin(api,expected_request(data,controller),data['operators'],family='HOST7')")
    code = code.replace("c.validate_origin(api,controller_request(expected),data['operators'])", "c.validate_origin(api,controller_request(expected),data['operators'],family='MODEL5')")
    code += '''\n\ndef validate_collector_origin(raw, expected, operators=('/root',)):
    """Collector-specific CLI and strict present-counter family, no dispatch."""
    import collector_contracts as collector
    api = c.decode_tool_origin(raw)
    output = c.validate_origin(api, expected, operators, family='COLLECTOR7')
    words, _ = collector.command_words(expected)
    need(len(words) >= 7, 'COMPLETE_COLLECTOR_COMMAND')
    collector.command(expected, words[6])
    return collector.output_object(output)
'''
    code += (OWNED / 'collector_reader_method.txt').read_text()
    (SOURCE / 'probe_adapter.py').write_text(code)


def patch_baseline_tests(changes, runtimes):
    p = SOURCE / 'test_source_bindings.py'
    code = p.read_text().replace('5013b22644e90a82d10792c456440e34faa1b1b2a5a033ac2f29282e4f14ad92', TUPLE['producerData']['sha256']).replace('189a8564f53619210c431fa05ec9d3df90640279362b98c4e082f87b923daa5d', TUPLE['producerDataAcceptance']['sha256'])
    p.write_text(code)
    p = SOURCE / 'test_current_authority.py'
    code = replace_assign(p.read_text(), dict(CURRENT_R8_FIXTURE=dict(source=TUPLE['controllerSource'], sourceAcceptance=TUPLE['controllerSourceAcceptance'], controlAcceptance=TUPLE['controllerDataAcceptance'])))
    code = code.replace('runtimeSourceCount=12,sourceCount=', 'runtimeSourceCount=len(consumer.RUNTIME_FILES),sourceCount=')
    code = code.replace("self.assertEqual(s['runtimeSourceCount'],12)", "self.assertEqual(s['runtimeSourceCount'],len(consumer.RUNTIME_FILES))")
    code = code.replace('Exact accepted R8 SOURCE and complete168', 'Exact accepted current R10 SOURCE and complete178')
    code = code.replace('over current R8 CODE', 'over current R10 CODE')
    p.write_text(code)


def adapters():
    qpath = Path(TUPLE['operationalQualifier']['path'])
    qtext = qpath.read_text()
    qt = ast.parse(qtext)
    functions = {'need', 'closed', 'encoded', 'pin', 'command_words', 'command', 'output_object', 'decode_input'}
    constants = {'SCRIPT_PIN', 'PYTHON', 'DATA_PARENT', 'REPO_PARENT', 'PREFIX', 'KINDS', 'REQUEST_KEYS', 'JUSTIFICATION_MAX_UTF8_BYTES'}
    sections = []
    for n in qt.body:
        if isinstance(n, ast.FunctionDef) and n.name in functions or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in n.targets):
            sections.append(ast.get_source_segment(qtext, n))
    (SOURCE / 'collector_contracts.py').write_text('"""Exact finite CLI/ACK primitives from accepted typed Collector Source2. No IO."""\nimport base64,binascii,hashlib,json,math,re,shlex\n\n' + '\n\n'.join(sections) + '\n')
    mpath = Path(TUPLE['strictMetadataMethod']['path'])
    mtext = mpath.read_text()
    mt = ast.parse(mtext)
    names = {'need', 'closed', 'integer', 'text', 'same', 'equal', 'preflight_json', 'wall_path', 'validate_tree', 'decode_json', 'response_metadata'}
    reused = '\n\n'.join(ast.get_source_segment(mtext, n) for n in mt.body if isinstance(n, ast.FunctionDef) and n.name in names)
    authority = json.loads(Path(SCOPE['requestFamilyAuthority']['path']).read_bytes())
    host = authority['families']['HOST7']['exactPolicyFields']
    capture = authority['families']['PRODUCER_CAPTURE7']
    cap_code = Path(capture['contracts']).read_text()
    cap_ast = ast.parse(cap_code)
    capture_policy = next(ast.literal_eval(n.value) for n in cap_ast.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'REQUEST_POLICY' for t in n.targets))
    prefix = '''"""Four explicit request families; bounded native mechanics, no IO/dispatch.

Pure decoder/type/response functions are AST-exact from accepted method5e4a.
MODEL5 optional token metadata never widens strict operational COLLECTOR7.
"""
from decimal import Decimal
import json, math, re
from strict import Refusal
DATA=16777216
OUTPUT=1048576
SAFE=9007199254740991
I64=9223372036854775807
DEPTH=64
METADATA_DEPTH=48
NODES=250000
FLAGS={'truncated','output_truncated','interrupted','error','isError'}
RESPONSE_KEYS={'chunk_id','wall_time_seconds','exit_code','original_token_count','output','session_id'}|FLAGS
POLL_KEYS={'session_id','chars','yield_time_ms','max_output_tokens'}
FAMILIES=('MODEL5','HOST7','COLLECTOR7','PRODUCER_CAPTURE7')
KEYS5={'cmd','workdir','login','yield_time_ms','max_output_tokens'}
KEYS7=KEYS5|{'sandbox_permissions','justification'}
'''
    prefix += 'HOST_POLICY=' + repr({k: host[k] for k in ('sandbox_permissions', 'justification')}) + '\n'
    prefix += 'CAPTURE_POLICY=' + repr(capture_policy) + '\n\n'
    suffix = '''
def decode_tool_origin(raw):
    return decode_json(raw, api=True)


def canonical_request(value, family):
    need(family in FAMILIES, 'EXPLICIT_KNOWN_REQUEST_FAMILY')
    closed(value, KEYS5 if family == 'MODEL5' else KEYS7)
    text(value['cmd'], DATA);text(value['workdir'],4096)
    need(value['cmd'] and value['workdir'].startswith('/') and '\\x00' not in value['cmd'] + value['workdir'], 'REQUEST_TEXT_DOMAINS')
    need(type(value['login']) is bool and value['login'] is False, 'EXACT_LOGIN_FALSE')
    integer(value['yield_time_ms'],1,10000);integer(value['max_output_tokens'],1,20000)
    if family in ('HOST7','PRODUCER_CAPTURE7'):
        policy = HOST_POLICY if family == 'HOST7' else CAPTURE_POLICY
        for key, expected in policy.items():equal(value[key],expected,'EXACT_FAMILY_POLICY')
    elif family == 'COLLECTOR7':
        import collector_contracts as collector
        words,route=collector.command_words(value)
        equal(route,'ROOT_CLEANENV_KILL10S','OPERATIONAL_COLLECTOR_REQUIRES_CLEANENV')
        need(len(words)>=7,'COMPLETE_COLLECTOR_COMMAND')
        collector.command(value,words[6])
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('utf8')


def validate_origin(origin, expected, operators, *, family):
    """Read a whole native origin in one explicitly selected immutable family."""
    validate_tree(origin,api=True)
    closed(origin,('schema','operator','launch','polls'))
    equal(origin['schema'],'e02-actual-tool-custody-v1')
    need(type(operators) in (list,tuple,set) and operators and origin['operator'] in operators,'DECLARED_ACTUAL_OPERATOR')
    text(origin['operator'],4096)
    if family=='COLLECTOR7':equal(origin['operator'],'/root','OPERATIONAL_COLLECTOR_ROOT_OPERATOR')
    expected_bytes=canonical_request(expected,family)
    maximum_polls=16 if family=='COLLECTOR7' else 128
    need(type(origin['polls']) is list and len(origin['polls'])<=maximum_polls,'FINITE_ACTUAL_POLLS')
    session,terminal,outputs,total=None,False,[],0
    for i,frame in enumerate([origin['launch'],*origin['polls']]):
        closed(frame,('toolName','actualArguments','unmodifiedResponse'))
        need(not terminal,'NO_FRAME_AFTER_TERMINAL')
        arguments,response=frame['actualArguments'],frame['unmodifiedResponse']
        if i==0:
            equal(frame['toolName'],'tools.exec_command')
            equal(canonical_request(arguments,family),expected_bytes,'WHOLE_ACTUAL_REQUEST_FAMILY')
            cap=arguments['max_output_tokens']
        else:
            equal(frame['toolName'],'tools.write_stdin')
            need(type(arguments) is dict and set(arguments)<=POLL_KEYS,'DECLARED_POLL_FIELDS')
            integer(arguments.get('session_id'),1);equal(arguments['session_id'],session,'SAME_SESSION_ARGUMENT')
            need('chars' not in arguments or type(arguments['chars']) is str and arguments['chars']=='','READ_ONLY_POLL')
            for key in ('yield_time_ms','max_output_tokens'):
                if key in arguments:integer(arguments[key],1)
            cap=arguments.get('max_output_tokens',10000)
        response_metadata(response,cap)
        if family=='COLLECTOR7':
            need('original_token_count' in response,'COLLECTOR_PRESENT_NATIVE_COUNTER_REQUIRED')
            integer(response['original_token_count'],0,cap)
        if response.get('exit_code') is None:
            integer(response.get('session_id'),1)
            session=session or response['session_id'];equal(response['session_id'],session,'SAME_SESSION_RESPONSE')
        else:
            equal(response['exit_code'],0,'NATURAL_API_TERMINAL0')
            need(response.get('session_id') is None or type(response['session_id']) is int and response['session_id']==session,'TERMINAL_SESSION')
            terminal=True
        output=response['output']
        need(not any(marker in output for marker in ('tokens truncated','Warning: truncated output','Output exceeded the available','[output truncated]')),'NO_TRUNCATION_MARKER')
        total+=len(output.encode('utf8','strict'))
        need(total<=(65536 if family=='COLLECTOR7' else OUTPUT),'WHOLE_API_OUTPUT_BOUND')
        outputs.append(output)
    need(terminal,'COMPLETE_TERMINAL_REQUIRED')
    return ''.join(outputs)
'''
    (SOURCE / 'request_families.py').write_text(prefix + reused + '\n\n' + suffix)
    return dict(nativePrimitivesSource=pin(mpath), nativePrimitiveNames=sorted(names),
                collectorPrimitivesSource=pin(qpath), collectorPrimitiveNames=sorted(functions),
                semantics='Exact copied pure functions; family dispatch is explicit new code and requires independent SOURCE review. No external source imports or runtime calls.')


def main():
    contract = setup()
    changes, runtimes, controls = patch_consumer(contract)
    patch_capture_and_probe()
    patch_baseline_tests(changes, runtimes)
    reuse = adapters()
    save(OWNED / 'immutable-validation-reuse.json', reuse)
    save(OWNED / 'current-inputs.json', dict(controllerSource=TUPLE['controllerSource'],
        controllerSourceAcceptance=TUPLE['controllerSourceAcceptance'],
        controllerControlDataAcceptance=TUPLE['controllerDataAcceptance']))
    save(OWNED / 'preparation-stage.json', dict(schema='e02-consumer-current178-source-preparation-stage-v1', actor=ACTOR,
        sourceRoot=str(SOURCE), runtimeFiles=list(runtimes), controlFiles=list(controls),
        currentTuple=TUPLE, rootScope=pin(SCOPE_PATH), executionAuthorized=False,
        phase='CODE_AND_DEFINITIONS_UNDER_PREPARATION_NO_IMPORTS_OR_MODELS'))
    print(json.dumps(dict(sourceRoot=str(SOURCE), runtimeFiles=len(runtimes), controls=len(controls), targetImports=0, modelsExecuted=0)))


if __name__ == '__main__':
    main()
