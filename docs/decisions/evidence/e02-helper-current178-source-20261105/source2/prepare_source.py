"""Bounded stdlib SOURCE-package generator. No module/target import or model.

Reads only the explicitly named metadata/code operands below. No daemon, input
tree walk, tool execution, lease/account/identity, fit/gzip calculation or grant.
All writes remain in this delegated new SOURCE directory.
"""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
E = HERE.parents[1]
G = E / 'e02-goal-resume-20261104'
SCOPE = G / 'helper-current178-source2-root-scope-20261105.json'
FAMILY = G / 'request-family-authority-current178-20261105.json'
MAP = G / 'helper-current178-binding-map-20261105.json'
BASE = E / 'e02-helper-concrete-render-20261104'
OLD = E / 'e02-helper-probe-current-r6-resume-20261102'
STRICT = E / 'e02-controller-current-model-preparation-20261105/source2/controller_model_metadata.py'
BRIDGE_SCOPE = G / 'root-failstop-bridge-root-scope-20261105.json'
BRIDGE_GAP = G / 'root-failstop-lifetime-gap-20261105.json'
OWNER = '/root/helper_current178_source'


def need(value, message):
    if not value:
        raise ValueError(message)


def pin(path):
    need(path.is_absolute() and not path.is_symlink(), 'EXPLICIT_FILE')
    s = path.lstat(); need(stat.S_ISREG(s.st_mode) and s.st_size <= 16777216, 'SOURCE_METADATA_ONLY')
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def doc(path):
    return json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False) + '\n').encode()


def put(name, value, raw=False):
    path = HERE / name
    need(path.is_relative_to(HERE), 'OWNED_OUTPUT_ONLY')
    data = value if raw else encoded(value)
    with path.open('xb') as stream:
        need(stream.write(data) == len(data), 'COMPLETE_SOURCE_WRITE')
    return pin(path)


def actual(expected):
    need(pin(Path(expected['path'])) == expected, 'EXACT_PINNED_CURRENT_INPUT')
    return doc(Path(expected['path']))


def main():
    scope, families, mapping = doc(SCOPE), doc(FAMILY), doc(MAP)
    need(scope['owner'] == OWNER and scope['ownedWritableRoot'] == str(HERE), 'EXACT_ROOT_ASSIGNMENT')
    need(pin(SCOPE)['sha256'] == 'a21d31ec165fb9a0d6e798462a8bdeb0a37add22cd07644477ac1d35f620334d', 'ROOT_SCOPE_PIN')
    need(pin(FAMILY)['sha256'] == 'd84c074354b8b63f28b1b7f4857de4e6382d5ffe923749aabac9fadd7a81d07c', 'ROOT_FAMILY_PIN')
    need(pin(MAP)['sha256'] == '9a448aef65d1975b03e9387808a5c0b39d3746b1034383998ef9ae37c101e8af', 'ROOT_MAP_PIN')
    current = scope['currentTuple']
    producer, psource, pdata = actual(current['producerSource']), actual(current['producerSourceAcceptance']), actual(current['producerDataAcceptance'])
    controller, csource, cdata = actual(current['controllerSource']), actual(current['controllerSourceAcceptance']), actual(current['controllerDataAcceptance'])
    collector, qsource, qdata = actual(current['collectorSource']), actual(current['collectorSourceAcceptance']), actual(current['collectorDataAcceptance'])
    need(psource['subject'] == current['producerSource'] and pdata['producerSource'] == current['producerSource'], 'CURRENT_PRODUCER_JOINS')
    need(type(pdata['modelsPassed']) is int and pdata['modelsPassed'] == 266, 'ACTUAL_CURRENT266')
    need(csource['subject'] == current['controllerSource'] and cdata['controllerSource'] == current['controllerSource'], 'CURRENT_CONTROLLER_JOINS')
    need(type(controller['upstreamProducerModelsDefined']) is int and controller['upstreamProducerModelsDefined'] == 266, 'CURRENT_UPSTREAM_SCALAR266')
    need(type(cdata['modelsPassed']) is int and cdata['modelsPassed'] == 178, 'ACTUAL_CURRENT178')
    need(qsource['subject'] == current['collectorSource'] and qdata['collectorSource'] == current['collectorSource'], 'CURRENT_TYPED_COLLECTOR_JOINS')
    need(type(qdata['modelsPassed']) is int and qdata['modelsPassed'] == 81, 'ACTUAL_CURRENT81')
    constants = actual(controller['constants'])
    need(all(type(x) is int and x == 0o664 for x in constants['sourceModes'].values()), 'EXACT_SOURCE0664_AUTHORITY')
    host = next(d for d in controller['runtimeSources'] if Path(d['path']).name == 'host.py')
    host_policy = families['families']['HOST7']['exactPolicyFields']
    capture_origin = actual(current['producerOriginalToolOrigin'])
    capture_request = capture_origin['launch']['actualArguments']
    need(set(capture_request) == {'cmd','workdir','login','yield_time_ms','max_output_tokens','sandbox_permissions','justification'}, 'ACTUAL_CAPTURE7')
    capture_policy = {k: v for k, v in capture_request.items() if k != 'cmd'}
    collector_policy = dict(workdir=str(Path(current['operationalCollector']['path']).parent), login=False,
                            yield_time_ms=1000, max_output_tokens=2000, sandbox_permissions='require_escalated',
                            justification='Môžem raz vykonať presne prijatý E02 Root custody príkaz v izolovanom účte s pôvodnými limitmi a úplnou evidenciou? Bez opakovania a bez produkčných údajov.')
    diagnostics = {'/root/helper_source_qa_19b50833', '/root/helper_source_security_19b50833'}
    authors = sorted(set(scope['knownPrerequisiteActors']) | {OWNER} | diagnostics)
    exclusions = sorted(set(scope['reviewerExclusions']) | {'/root/root_failstop_bridge_source'})
    need(len(exclusions) == 41 and set(authors) <= set(exclusions), 'ACTUAL_SOURCE2_ACTOR_UNION')
    fixed = doc(BASE / 'templates.json')
    plan_base = fixed['planWithoutGates']
    plan_base['source8'] = constants['source8']
    binding_literals = dict(CURRENT=current, HOST_POLICY=host_policy, CAPTURE_POLICY=capture_policy,
                            COLLECTOR_POLICY=collector_policy, TRUE_AUTHORS=authors, EXCLUSIONS=exclusions,
                            TEMPLATES_PATH=str(HERE / 'templates.json'), CURRENT_PLAN_BASE=plan_base,
                            RUNTIME_SOURCES=controller['runtimeSources'], HOST_SOURCE=host,
                            SOURCE_MODES=constants['sourceModes'])
    text = '"""Exact immutable SOURCE literals; no IO or authority issuance."""\n'
    text += '\n'.join(name + ' = ' + repr(value) for name, value in binding_literals.items()) + '\n'
    put('current_bindings.py', text.encode(), raw=True)
    fixed['schema'] = 'e02-helper-current178-render-templates-v1'
    fixed['actor'] = OWNER
    fixed['rawSourceGates'] = dict(producerSource=current['producerSource'], controllerSource=current['controllerSource'])
    fixed['dataSubjectBindings'] = copy.deepcopy(fixed['rawSourceGates'])
    fixed['compiledControllerBindings'] = dict(acceptedProducerSubject=current['producerSource'],
                                              source8=constants['source8'], sourceModes=constants['sourceModes'])
    fixed['controllerRuntimeSources'], fixed['hostSource'] = controller['runtimeSources'], host
    fixed['trueAuthors'], fixed['conservativeReviewerExclusions'] = authors, exclusions
    fixed['hostPolicy'], fixed['capturePolicy'], fixed['collectorPolicy'] = host_policy, capture_policy, collector_policy
    fixed['authorities'] = dict(producerSourceAcceptance=current['producerSourceAcceptance'],
        producerDataAcceptance=current['producerDataAcceptance'], controllerSourceAcceptance=current['controllerSourceAcceptance'],
        controllerDataAcceptance=current['controllerDataAcceptance'], collectorSourceAcceptance=current['collectorSourceAcceptance'],
        collectorDataAcceptance=current['collectorDataAcceptance'], sourceQaReview=csource['reviews'][0],
        sourceSecurityReview=csource['reviews'][1], captureSourceAcceptance=current['producerCaptureSourceAcceptance'],
        admissionDataAcceptance=current['producerAdmissionDataAcceptance'])
    for kind, value in fixed['genericGateTemplates'].items():
        value['decision'] = None
        if kind == 'concreteInput':
            value['subject'] = value['evidence'] = None
        else:
            value['subject'] = current['producerSource' if kind == 'producerData' else 'controllerSource']
            key = dict(producerData='producerDataAcceptance', controlData='controllerDataAcceptance',
                       sourceQa='sourceQaReview', sourceSecurity='sourceSecurityReview')[kind]
            value['evidence'] = fixed['authorities'][key]
            value['actor'] = doc(Path(value['evidence']['path'])).get('session', '/root')
    fixed['rootReleaseTemplate']['subject'] = current['controllerSource']
    fixed['rootReleaseTemplate']['authors'] = authors
    fixed['rootReleaseTemplate']['executionAuthorized'] = None
    helper = fixed['helperSubject18Template']
    for key in ('producerSource','producerDataAcceptance','controllerSource','controllerSourceAcceptance'):
        helper[key] = current[key]
    helper['controllerControlDataAcceptance'] = current['controllerDataAcceptance']
    helper['collectorSourceAcceptance'] = current['collectorSourceAcceptance']
    helper['collectorControlDataAcceptance'] = current['collectorDataAcceptance']
    helper['authors'], helper['operators'], helper['qualified'] = authors, [], None
    fixed['genericObservedRows'] = None
    fixed['freshGenericInputObservation'] = None
    fixed['genericObservationMeaning'] = 'SOURCE definition only; old538 observation remains historical and does not qualify current inputs.'
    fixed['executionReadiness'] = 'SOURCE_ONLY_EXTERNAL_ACCEPTED_SOURCE_AND_CONTROLS_CONTEXT_REQUIRED'
    fixed['finalAuthorityBundleAcceptance'] = None
    fixed['baselineOnlyReason'] = 'Current exact tuple is selected, but Source/control/current-input/fit/actualRoot registration/runtime gates remain unissued.'
    fixed['bridgeDependency'] = dict(source=None, sourceAcceptance=None, controlDataAcceptance=None,
                                   actualForegroundSession=None, actualLiveGateIdentity=None,
                                   required=True, owner='/root/root_failstop_bridge_source',
                                   rootScope=pin(BRIDGE_SCOPE), gapEvidence=pin(BRIDGE_GAP))
    put('templates.json', fixed)
    old_contract_path = E / 'e02-producer4-helper-probe-preparation-20261028/helper-probe-data-acceptance-contract.json'
    helper_contract = doc(old_contract_path)
    helper_contract['dataSubjectMinimumJoins']['producerDataAcceptance'] = 'Exact accepted current266 DATA operand'
    put('helper-probe-data-acceptance-contract.json', helper_contract)
    need(pin(HERE/'helper-probe-data-acceptance-contract.json')['sha256'] == '14f859491411c84ec03bc552f0be287269f6ff94a9d4b43cf7cdf22e650fdacc', 'UNCHANGED_ROOT24_EDITORIAL_BYTES')
    interfaces = mapping['minimalClosedInterfaces']
    context_contract = dict(schema='e02-current-helper-source-control-context-contract-v1', actor=OWNER,
        source=dict(schema='e02-root-helper-current178-source-acceptance-v1',
                    decision='ACCEPT_CURRENT_HELPER_METHOD_RENDER_SOURCE_ONLY',
                    closedKeys=['schema','actor','decision','subject','reviews','modelsDefined','modelsExecuted','scope','executionAuthorized'],
                    scope='CURRENT_HELPER_METHOD_RENDER_SOURCE_AND_CONTROL_DEFINITIONS_ONLY', modelsExecuted=0, executionAuthorized=False),
        controls=dict(schema='e02-root-helper-current178-control-data-acceptance-v1',
                      decision='ACCEPT_CURRENT_HELPER_METHOD_RENDER_PURE_CONTROL_DATA_ONLY',
                      closedKeys=['schema','actor','decision','subject','helperSource','reviews','modelsDefined','modelsExecuted','modelsPassed','modelsFailed','skipped','inputsUnchanged','scope','executionAuthorized'],
                      subjectSchema='e02-helper-current178-control-data-subject-v1',
                      scope='CURRENT_HELPER_METHOD_RENDER_PURE_CONTROL_DATA_ONLY', executionAuthorized=False),
        note='Unissued contract only. Root authenticates real mailbox/native provenance and supplies original raw/pin pairs. Source/template flag changes never substitute actual independent Source/control receipts.',
        actorSelectors=dict(sourceRequired=['author','coordinator','sourceContributors','operators','reviewerExclusions'],
            controlRequired=['authors','operators'],
            optionalTypedScalars=['author','actor','coordinator'],
            optionalTypedVectors=['authors','sourceContributors','designContributors','sourceContributorUnion','operators','sourcePreparationOperators','reviewerExclusions']),
        actorRule='Full fixed TRUE_AUTHORS/EXCLUSIONS plus both authenticated subjects and declared concrete participants precedes all review pairs; all consuming boundaries revalidate complete typed lists. Source/control pairs are rechecked against new declarations. No caller subset or empty closure.',
        actualSourceAcceptance=None, actualControlDataAcceptance=None, executionAuthorized=False)
    put('source-control-acceptance-contract.json', context_contract)
    method = dict(schema='e02-current-helper178-method-contract-v1', author=OWNER,
                  currentTuple=current, immutableInterfaces=interfaces,
                  immutableBounds=fixed['immutableOperationalBounds'], clocks=mapping['fitAndFinalCut']['clocks'],
                  genericInputSpecPath=str(HERE / 'generic-input-source.json'),
                  actorClosure='render_metadata.actor_closure/validate_roster; full typed immutable+Source/design/controlData union before any pair, then every generic/bind/concrete/Root11/HOST7 boundary.',
                  collectorNativeByteRoute='Future accepted foreground bridge validates raw native origin bytes with strict bounded metadata, then uses exact accepted losslessCollectorCodec.origin(raw), then accepted qualification/history with same q/module/livegate. No Decimal forwarding/global cast/repair. Positive fractional wall direct/yielded integration control required in separate bridge DATA.',
                  requestFamilies=families, bridgeDependency=fixed['bridgeDependency'],
                  rootObligations=['Authenticate all genuine native frames, ACKs, actual independent verdicts and one live RootFailstop object/module class throughout the same foreground session.',
                      'No newrun operation/copy before actualRESERVE; each original/duplicate charged exactlyonce in same slot.',
                      'Original1800lease/current privatepaths/input/daemon/image/identity/policy/concrete acceptance/fullfit and oneuseRootrelease remain independently required.',
                      'M4/S18 and everyphysical artifact precede finalF. Freeze prefix/envelope before constructing ownF row. No ownF pin/origin/index/status/copy/postF CLI or second slot/refund.'],
                  runtimeAudit=dict(freshChecks=64, closeCalls=1, joins=65, auditObservations=266,
                                    controllerMockControls=178, countsAreDifferentDomains=True),
                  actualHelperData=None, actualRootRelease=None, executionAuthorized=False)
    put('method-contract.json', method)
    recipe = doc(BASE / 'render-recipe.json')
    recipe.update(schema='e02-helper-current178-source-render-recipe-v1', author=OWNER,
                  state='SOURCE_ONLY_REQUIRES_INDEPENDENT_SOURCE_CONTROLS_CURRENT_INPUTS_AND_ROOT_RUNTIME_GATES',
                  genericObservedRows=None, snapshotCountClarification='Current expected rows derive generic-input-source.json; historical538 is not current observation.',
                  historyAPIs=dict(qualification=current['operationalQualifier']['path'], historyPrefix=current['historyPrefix']['path'],
                                  rootFailstop='ONE_GENUINE_EXISTING_OBJECT_IN_ACCEPTED_FOREGROUND_ROOT_BRIDGE_NO_REINSTANTIATION',
                                  evaluate='ExistingRootCustody.evaluate_prefix with the same externally supplied q/history class objects.',
                                  freeze='ExistingRootCustody.freeze on complete actual pre-F prefix and exactremainingpayload/writes.',
                                  final='ExistingRootCustody.finish in memory on platform-onlyfinalF chain; actualRootbridge must retain identicalgate.'),
                  bridgeDependency=fixed['bridgeDependency'])
    recipe['collector']['requestClosedKeys'] = sorted(families['families']['COLLECTOR7']['keys'])
    recipe['collector']['requestValues'] = dict(collector_policy, cmd=None)
    recipe['steps'] = [dict(id=i, action=value) for i, value in enumerate([
        'Root accepts exact helperSource and completepurecontrols, currentproducer266/controller178/typedcollector81 and strictrequestfamilies. Never transfer oldtuple results.',
        'Root authenticates complete creator/operator/exclusion closure and actualacceptedforegroundbridge/source/controls/livegate session; death/lost/EOF or denial permanentlyquarantines run.',
        'Only Root chooses fresh identity/nonce, checks allpermanentquarantines/privatepaths andfirstRESERVE precharges single65536slot. Preserve full genuine Collector7 ACK/origin inlivegate.',
        'Root issues realUTC/MONO/BOOT original1800lease once afterRESERVE, registers exactbytes canonicallease--original; no renewals. Owned0700parent only, fourHost leaves absent.',
        'Root supplies actualsource/controlcontext toplan_without_gates, actualreserveACK/registeredlease; concrete_subject is exact16fieldpregatehash.',
        'Fresh declaredwholeinputs/guard522/tools/image/daemon/namespace/privatepaths/originallease and genuine independentcompact5/two4keyconcreteverdicts. ThisSource performs no observations.',
        'Register compactreceipt/fiveexactgenericgates/plan usingauthenticACKs; purebind revalidates allgatebytes and compactreceipt. Allrecord/copy bytes and ledgerwrites charged, nohiddenoperations.',
        'Compute exactfullphysicalchain+remainingcontrollerplainHostorigin+M4+S18+history/F bounds and originalleasewindow before any actualRootruntimegrant. Unknownfit or missinglivegate refuses.',
        'PureRootrelease template remainsnull; Rootalone issues actualoneuse11keyrelease afterallgates, registers it, renderscompleteHOST7 usingacceptedR10policy andoriginal183sCLI; executeonce withcompletegenuineAPIcustody.',
        'AfteractualHost outcome rootauthenticates expectedhashes/identity/ownCIDcleanup/naturallifecycle/64CHECK+1CLOSE/266observations; accountplainHostorigin andpreF M4/S18 without ownF/selfmember.',
        'SameactualRootFailstop evaluatescompleteallCollector7prefix; everyunqualifiedoperationstaysdenied despite structuralreopen. Deriveexactremainingpayload/writes fromactualACKs, nocounterfabrication.',
        'Freeze exactprefix/envelope, thenconstructownF request/expectedpin inmemory only. Submit exactlylastdiagnosticF once. Complete finalplatformlaunch/allpolls/terminal0 is theonlyF witness; no postFphysicalfiles/copies/status/CLI.',
        'Sameactualgate qualifiesfinalwitness inmemory; Rootquarantinesanyfailure/loss. IndependentactualhelperDATA and Root24 acceptance precedecompletion/wrapper andlatercurrentconsumeractivation/tworoles/fiveexports/fullprimary22/reviewedintegration.'
    ])]
    put('render-recipe.json', recipe)
    permission = dict(schema='e02-helper-current178-request-permission-source-v1', author=OWNER,
        selectedHostRequestKeys=families['families']['HOST7']['keys'], policy=host_policy,
        separateHelpProbeRequired=False, actualPreflightRequest=None, actualApprovalResult=None,
        rule='Actualsupportedrequire_escalated fields are retained in complete HOST7. No --help probe or prefix persistence is assumed. Any actualpermission/admission original or duplicate is explicitlycharged in sameaccount and cannot authorize target byitself.',
        executionAuthorized=False)
    put('permission-preflight.json', permission)
    # Static expected rows are metadata derivation only, never actual stat/hash
    # observation of runtime/guard/tool operands.
    expected = {}
    def row(d, mode, role):
        previous = expected.setdefault(d['path'], dict(pin=d, mode=mode, role=role))
        need(previous['pin'] == d and previous['mode'] == mode, 'UNIQUE_EXPECTED_PATH_DOMAIN')
    model_before = actual(current['controllerDataBefore'])
    before_modes = {x['pin']['path']: x['mode'] for x in model_before['rows']}
    for d in controller['runtimeSources']: row(d, before_modes[d['path']], 'R10_HOST_RUNTIME')
    for d in constants['source8']: row(d, oct(constants['sourceModes'][Path(d['path']).name]), 'CURRENT_GUEST8')
    guard_manifest = plan_base['guardManifest']; guard = actual(guard_manifest)
    for name, value in guard['files'].items():
        row(dict(path=plan_base['guardRoot'] + '/' + name, bytes=value['bytes'], sha256=value['sha256']), oct(value['mode']), 'GUARD522')
    # The expected guard-manifest mode is an accepted recorded observation,
    # not a new runtime observation by this SOURCE generator.
    psubject = actual(current['producerData']); execution = actual(psubject['execution']); psnapshot = actual(execution['overallBefore'])
    observed_modes = {x['pin']['path']: x['mode'] for x in psnapshot['rows']}
    row(guard_manifest, observed_modes[guard_manifest['path']], 'GUARD_MANIFEST')
    for d in plan_base['tools'].values(): row(d, observed_modes.get(d['path'], '0o755'), 'HOST_TOOLS')
    capture_plan = actual(psubject['plan'])
    for key in ('env', 'timeout'):
        d = capture_plan['tools'][key]; row(d, observed_modes[d['path']], 'OUTER_CLI_TOOLS')
    runtime_rows = len(expected)
    authority_keys = ['producerSource','producerSourceAcceptance','producerData','producerDataAcceptance',
        'producerCaptureSource','producerCaptureSourceAcceptance','producerAdmissionDataAcceptance',
        'controllerSource','controllerSourceAcceptance','controllerControlPlan','controllerData','controllerDataAcceptance',
        'collectorSource','collectorSourceAcceptance','collectorData','collectorDataAcceptance','operationalQualifier',
        'historyPrefix','losslessCollectorCodec','strictMetadataMethodSource','strictMetadataMethodAcceptance','host7Policy','host7Skeleton','sourceModeAuthority']
    for key in authority_keys:
        d = current[key]; row(d, oct(stat.S_IMODE(Path(d['path']).stat().st_mode)), 'CURRENT_AUTHORITY_' + key)
    # Canonical membership is derived from the accepted manifest names only.
    guard_dirs = set()
    for name in guard['files']:
        parts = Path(name).parts
        guard_dirs.update('/'.join(parts[:i]) for i in range(1, len(parts)))
    spec = dict(schema='e02-current-helper-generic-input-source-v1', author=OWNER,
                files=sorted(expected.values(), key=lambda x: x['pin']['path']),
                runtimeInputCount=runtime_rows, authorityInputCount=len(expected)-runtime_rows,
                expectedFileCount=len(expected), observedFileCount=None,
                memberships=[dict(root=plan_base['guardRoot'], files=sorted(guard['files']), directories=sorted(guard_dirs))],
                actualCurrentObservation=None, actualDaemonImageObservation=None,
                actualOriginalLease=None, actualPrivatePaths=None, executionAuthorized=False,
                observationRequirement='Separate reviewedRootobserver must obtain wholecurrentfile/mode/namespaceidentity/membership/tool/image/daemon/privatepath/lease proof. ThisSource walks no runtime tree.')
    put('generic-input-source.json', spec)
    tree = ast.parse((HERE/'test_helpers.py').read_bytes())
    names = [c.name+'.'+m.name for c in tree.body if isinstance(c, ast.ClassDef) for m in c.body
             if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]
    plan = dict(schema='e02-helper-current178-pure-control-plan-v1', author=OWNER,
                groups=[dict(name='test_helpers', source=pin(HERE/'test_helpers.py'), format='VERBOSE_UNITTEST_NAMED',
                             argv=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(HERE/'test_helpers.py'),'-v'],
                             cwd=str(HERE), count=len(names), expectedNames=names)],
                modelsDefined=len(names), modelsExecuted=0, targetImports=0, executionAuthorized=False)
    put('control-plan.json', plan)
    # Finite explicit preservation/read set, never arbitrary descriptor recursion.
    inputs = {}
    def add(d):
        need(pin(Path(d['path'])) == d, 'EXACT_SOURCE_READ_OPERAND')
        need(inputs.setdefault(d['path'],d) == d, 'NO_CONFLICTING_SOURCE_READ_OPERAND')
    for p in [SCOPE,FAMILY,MAP,BRIDGE_SCOPE,BRIDGE_GAP,STRICT,old_contract_path]: add(pin(p))
    for p in sorted(BASE.iterdir()):
        if p.is_file(): add(pin(p))
    for p in sorted(OLD.iterdir()):
        if p.is_file(): add(pin(p))
    for key in authority_keys: add(current[key])
    for d in [*controller['runtimeSources'],*constants['source8'],controller['constants'],guard_manifest,
              current['operationalCollector'],current['producerOriginalToolOrigin'],current['controllerDataBefore'],
              psubject['execution'],execution['overallBefore'],psubject['plan'],
              *psource['reviews'],*pdata['reviews'],*csource['reviews'],*cdata['reviews'],*qsource['reviews'],*qdata['reviews']]: add(d)
    negative_freeze = actual(scope['negativePredecessorFreeze'])
    need(len(negative_freeze['inputs']) == 201, 'COMPLETE_NEGATIVE_PREDECESSOR_FREEZE201')
    for d in negative_freeze['inputs']: add(d)
    negative_descriptors = [scope['negativePredecessor'], scope['negativePredecessorFreeze'],
        scope['negativeDisposition'], scope['predecessorScope'], *scope['negativeReviews'], *scope['negativeFindings']]
    for d in negative_descriptors: add(d)
    predecessor_tests = Path(scope['negativePredecessor']['path']).parent/'test_helpers.py'
    previous_tree = ast.parse(predecessor_tests.read_bytes())
    previous_names = [c.name+'.'+m.name for c in previous_tree.body if isinstance(c,ast.ClassDef)
        for m in c.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_')]
    need(len(previous_names) == 38 and set(previous_names) <= set(names), 'ALL38_PREDECESSOR_MODEL_NAMES_PRESERVED')
    strict_names = ['need','closed','integer','text','same','equal','safe_path','pin_shape','preflight_json','wall_path','validate_tree','decode_json','response_metadata']
    strict_trees = [ast.parse(p.read_bytes()) for p in (STRICT,HERE/'native_metadata.py')]
    strict_maps = [{f.name: ast.dump(f,include_attributes=False) for f in t.body if isinstance(f,ast.FunctionDef)} for t in strict_trees]
    need(all(strict_maps[0][n] == strict_maps[1][n] for n in strict_names), 'ALL13_STRICT_AST_IDENTICAL')
    preservation = dict(schema='e02-helper-current178-source2-preservation-v1', author=OWNER,
        negativePredecessor=scope['negativePredecessor'], completeFreeze=scope['negativePredecessorFreeze'],
        all201Inputs=negative_freeze['inputs'], unchangedInputs=201,
        disposition=scope['negativeDisposition'], reviews=scope['negativeReviews'], findings=scope['negativeFindings'],
        originalQaDecision='ACCEPT_SOURCE_ONLY', originalSecurityDecision='HOLD',
        originalFinding='MEDIUM incomplete Source/control actor closure and caller-controlled concrete reviewer exclusions',
        preserved38Names=previous_names, newModelNames=sorted(set(names)-set(previous_names)),
        strictAstIdenticalFunctions=strict_names, unchangedRoot24=pin(HERE/'helper-probe-data-acceptance-contract.json'),
        runtimeSourcesUnchanged=controller['runtimeSources'], guest8Unchanged=constants['source8'],
        source2ApprovalUnissued=True, modelsExecuted=0, noResultTransfer=True, executionAuthorized=False)
    put('preservation.json', preservation)
    for p in sorted(HERE.iterdir()):
        if p.is_file(): add(pin(p))
    read_map = dict(schema='e02-helper-current178-finite-read-map-v1', author=OWNER,
        selectedInputDescriptors=sorted(inputs.values(),key=lambda x:x['path']),
        nativePrimitives=dict(source=pin(STRICT), exactASTFunctions=['need','closed','integer','text','same','equal','safe_path','pin_shape','preflight_json','wall_path','validate_tree','decode_json','response_metadata']),
        rendererInputs='Only exact external raw/pin source/controlctx and Root-authenticated registeredaccount/lease/ACK/verdict/gate/plan/release values; never recursivelydiscover operands.',
        collectorInputs='ExactlyacceptedSource2qualification/history/codec and unchanged operationalR4collector, allnamedpins; sameqmodule/class identity, Rootexternalbridge/source+control+livehandle mandatory.',
        runtimeInputDefinition=pin(HERE/'generic-input-source.json'),
        sourceOnlyCounterMeaning='Metadata counts derive finiteexplicitsets; guard/tool inputs are declaredmetadata only, not observed/rehashed or executed.',
        targetImports=0, modelsExecuted=0, executionAuthorized=False)
    put('read-map.json', read_map)
    diff = ''.join(difflib.unified_diff((BASE/'render_metadata.py').read_text().splitlines(True),
                        (HERE/'render_metadata.py').read_text().splitlines(True), fromfile='preserved-R8-renderer', tofile='current178-renderer'))
    put('renderer-source.diff', diff.encode(), raw=True)
    delta = dict(schema='e02-helper-current178-source-delta-v1', author=OWNER,
        predecessorRenderer=pin(BASE/'render_metadata.py'), currentRenderer=pin(HERE/'render_metadata.py'),
        changes=['Source2 corrects preserved Source1 security HOLD: complete typed Source/design/controlData actor union before any pair; every caller roster consuming boundary revalidates immutable/actual closure.',
                 'Preserves all201 negative predecessor pins and QA ACCEPT/security HOLD; adds actual-function actor regression definitions without execution/result transfer.',
                 'Exactcurrenttuple266/R10_178/typed81 selectors andauthenticcurrentSource/controlcontext.',
                 'Typedwhole4family/nativeAPI/ACK/lease/gate checks, RootSource2presentCollectorCounter refusal.',
                 'Pureexisting-livegate strongidentity/finalF adapter andexplicitactualforegroundbridge dependency.',
                 'ExplicitfinitecurrentgenericSource andfuturefit/cut contracts; zeroRootIO/runtime/authorities.'],
        immutableRuntimeSources=controller['runtimeSources'], guest8=constants['source8'],
        runtimeCodeChanged=False, runtimeAuditObservations=266, controllerControlsPrerequisite=178,
        noOriginalNegativeOverwritten=True, modelsExecuted=0, actualFit=None, actualBridgeSession=None, executionAuthorized=False)
    put('delta.json', delta)
    # Archive only named eligible SOURCE/governance operands; operational data
    # fixtures are not enumerated or copied by this generator.
    archive_dir=HERE/'source-archive'; archive_dir.mkdir(mode=0o700)
    for p in [HERE/'read-map.json',HERE/'renderer-source.diff',HERE/'delta.json']:add(pin(p))
    copies=[]
    for i,d in enumerate(sorted(inputs.values(),key=lambda x:x['path']),1):
        dest=archive_dir/('%03d-'%i+Path(d['path']).name)
        with dest.open('xb') as stream:need(stream.write(Path(d['path']).read_bytes())==d['bytes'],'EXACT_ARCHIVE_COPY')
        copies.append(dict(source=d,repositoryCopy=pin(dest)))
    archive=dict(schema='e02-helper-current178-source-archive-v1',author=OWNER,copies=copies,copiedFiles=len(copies),
                 copiedBytes=sum(x['source']['bytes'] for x in copies),operationalFixtureCopies=0,
                 originalPathsNotRebound=True,modelsExecuted=0,executionAuthorized=False)
    put('archive.json',archive)
    subject=dict(schema='e02-helper-current178-source-subject-v1',author=OWNER,coordinator='/root',
        sourceContributors=authors,designContributors=sorted(diagnostics),operators=[],reviewerExclusions=exclusions,currentTuple=current,
        negativePredecessor=scope['negativePredecessor'],negativeDisposition=scope['negativeDisposition'],
        preservation=pin(HERE/'preservation.json'),
        templates=pin(HERE/'templates.json'),renderer=pin(HERE/'render_metadata.py'),
        nativeMetadata=pin(HERE/'native_metadata.py'),custodyAdapter=pin(HERE/'custody_bridge.py'),
        genericPredicate=pin(HERE/'generic_inputs.py'),genericInputSource=pin(HERE/'generic-input-source.json'),
        methodContract=pin(HERE/'method-contract.json'),sourceControlContract=pin(HERE/'source-control-acceptance-contract.json'),
        helperDataContract=pin(HERE/'helper-probe-data-acceptance-contract.json'),
        controlPlan=pin(HERE/'control-plan.json'),readMap=pin(HERE/'read-map.json'),archive=pin(HERE/'archive.json'),
        sourceInputs=sorted(inputs.values(),key=lambda x:x['path']),sourceCount=len(inputs),
        modelsDefined=len(names),modelGroups=1,modelsExecuted=0,targetImports=0,
        sourceAccepted=False,independentReviews=None,selfApproval=False,
        actualHelperData=None,actualRootRunId=None,actualOriginalLease=None,actualAccount=None,
        actualConcreteVerdicts=None,actualFit=None,actualRootRelease=None,actualFinalFWitness=None,
        bridgeDependency=fixed['bridgeDependency'],completionWrapperImplemented=False,
        scope='CURRENT_HELPER_METHOD_RENDER_SOURCE_AND_CONTROL_DEFINITIONS_ONLY',executionAuthorized=False)
    put('subject.json',subject)
    entry=dict(schema='e02-helper-current178-source-review-entrypoint-v1',author=OWNER,subject=pin(HERE/'subject.json'),
        rootScope=pin(SCOPE),requestFamilyAuthority=pin(FAMILY),bindingMap=pin(MAP),
        negativePredecessor=scope['negativePredecessor'],negativeFreeze=scope['negativePredecessorFreeze'],
        negativeDisposition=scope['negativeDisposition'],negativeReviews=scope['negativeReviews'],
        negativeFindings=scope['negativeFindings'],preservation=pin(HERE/'preservation.json'),
        currentTuple=current,sourceMembers=len(inputs),physicalSourceOnlyFiles=None,
        archive=pin(HERE/'archive.json'),copiedFiles=len(copies),copiedBytes=archive['copiedBytes'],
        modelsDefined=len(names),modelsExecuted=0,targetImports=0,
        actualRendererInvocations=0,actualCollectorCalls=0,actualSizingExperiments=0,
        independentReviewRequired=True,sourceAccepted=False,executionAuthorized=False,
        freezeRequirement='Root completefreeze includes allactualphysicalfiles plus namedinputpins andpostpreparationnativeorigin. Place future review/acceptance outside immutableSource2 root.')
    put('review-entrypoint.json',entry)
    print(json.dumps(dict(entrypoint=pin(HERE/'review-entrypoint.json'),subject=pin(HERE/'subject.json'),
                          sourceInputs=len(inputs),archiveCopies=len(copies),modelsDefined=len(names),
                          runtimeExpectedInputs=runtime_rows,fullExpectedInputs=len(expected),
                          reviewerExclusions=len(exclusions),modelsExecuted=0)))


if __name__ == '__main__':
    main()
