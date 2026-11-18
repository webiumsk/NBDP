"""One-time SOURCE metadata preparation. No target imports or executions.

Inherited expected descriptors remain independent immutable declarations. This
does not re-observe SDK/artifact/runtime bytes or transfer any previous DATA.
Only explicitly named current small source/authority files are read here.
"""
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat

BASE = Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r1/source4')
D = Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r2/source4-lease-r1')
R = Path('/home/peterhorvath/apps/bitcoin/NBDP')
E = R / 'docs/decisions/evidence'
OUT = E / 'e02-producer4-266-capture-preparation-20261029/source-r1'
UP = E / 'e02-producer4-control-capture-preparation-20261028'
PRODUCER = Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r5-source4-lease-r1/subject.json')
AC = E / 'e02-producer-lease-r1-source-acceptance-20261029'
METHOD = E / 'e02-producer-original-lease-decoding-correction-20261029'
EXPECTED = [129, 33, 29, 16, 20, 10, 11, 8, 7, 3]
os.umask(0o077)

def need(value, message):
    if not value:
        raise ValueError(message)

def small_bytes(path):
    path = Path(path)
    need(path.is_absolute() and not path.is_symlink(), 'EXPLICIT_REGULAR_METADATA')
    for parent in path.parents:
        need(not parent.is_symlink(), 'NO_ANCESTOR_LINK')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= 16777216, 'SMALL_SOURCE_METADATA_ONLY')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    def identity(s):
        return (s.st_dev, s.st_ino, s.st_size, s.st_mode, s.st_uid, s.st_gid, s.st_mtime_ns, s.st_ctime_ns)
    try:
        need(identity(os.fstat(fd)) == identity(before), 'OPEN_IDENTITY')
        data = bytearray()
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            data.extend(block)
            need(len(data) <= before.st_size, 'DECLARED_SMALL_BOUND')
        need(identity(os.fstat(fd)) == identity(before), 'HANDLE_IDENTITY')
    finally:
        os.close(fd)
    need(identity(path.lstat()) == identity(before) and len(data) == before.st_size, 'PATH_IDENTITY')
    return bytes(data)

def pin(path):
    data = small_bytes(path)
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

def read(path):
    return json.loads(small_bytes(path))

def verify(descriptor):
    need(pin(descriptor['path']) == descriptor, 'EXPECTED_METADATA_PIN:' + descriptor['path'])
    return descriptor

def write(path, value):
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
    data = value if type(value) is bytes else (json.dumps(value, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(data) == len(data), 'ONE_EXACT_PREPARATION_WRITE')
    return pin(path)

def literals(path):
    result = {}
    for node in ast.parse(small_bytes(path)).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result

def functions(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(small_bytes(path)).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

need(not (OUT / 'review-entrypoint.json').exists() and not (D / 'capture.py').exists(), 'NO_FROZEN_OVERWRITE_OR_RETRY')
sp = pin(PRODUCER)
need(sp['bytes'] == 35901 and sp['sha256'] == 'fe619502879cd18a7c1e5be36891f679497406c56a4a60b36368595f9bfb897e', 'EXACT_CURRENT_PRODUCER')
source = read(PRODUCER)
ap = pin(AC / 'acceptance.json')
need(ap['sha256'] == '494d8ee2aae851fc7210fb7a2a1f8f14fd2910ee5a24faa3bad5ae529b369b62', 'EXACT_ISSUED_SOURCE_ACK')
lineage = pin(AC / 'acceptance-lineage.json')
need(lineage['sha256'] == '523a7a0cd74b2f6d3969ac9ac652a27b1a718363c98799f2681e6a15474ba3a5', 'EXACT_ISSUED_LINEAGE')
known_pin = pin(METHOD / 'root-known-actors-lease-r1.json')
need(known_pin['sha256'] == 'f3a04eab1043982315a1c1cf093b5fc4fbc4465d55332f50994e262e15f554b2', 'EXACT_ROOT_KNOWN_ACTOR_AUTHORITY')
known = read(known_pin['path'])
need(len(known['knownActors']) == len(set(known['knownActors'])) == 15 and known['producerSource'] == sp, 'EXACT_FIFTEEN')
old_constants = literals(BASE / 'contracts.py')
need(set(old_constants['REQUIRED_KNOWN_ACTORS']) <= set(known['knownActors']), 'ALL_OLD_ELEVEN_REMAIN_REQUIRED')
data_contract = pin(METHOD / 'current-producer-data-acceptance-contract-266.json')
need(data_contract['sha256'] == '17fea039fdcc88c5aa325e083337a702e8ae37852ae297adaebf3d39bc185fb9', 'EXACT_CURRENT266_FUTURE_DATA_CONTRACT')
need(read(data_contract['path'])['literals']['countsSeparate'] == EXPECTED, 'CONTRACT_CURRENT_COUNTS')
clock = pin(UP / 'root-clock-source-selection.json')
verify(source['controlPlan'])
control = read(source['controlPlan']['path'])
counts = [source['modelsDefined'][key] for key in old_constants['MODEL_KEYS']]
need(counts == EXPECTED and sum(counts) == 266 and source['sourceCount'] == len(source['sources']) == 64, 'ACTUAL_266_AND_64_SOURCE')
need(source['runtimeSourceCount'] == len(source['runtimeSources']) == 22 and source['version'] == 'SOURCE4'
     and source['sourceRevision'] == 'ORIGINAL_LEASE_DECODE_REMEDIATION_R1', 'EXACT_CURRENT_SOURCE_PROFILE_REVISION')
acceptance = read(ap['path'])
need(acceptance['subject'] == sp and acceptance['modelsDefined'] == 266, 'CURRENT_SOURCE_ACCEPTANCE_JOIN')
reviews = acceptance['reviews']
for descriptor in reviews:
    verify(descriptor)
for i, descriptor in enumerate(reviews):
    row = read(descriptor['path'])
    need(row['role'] == ('qa', 'security')[i] and row['subject'] == sp
         and row['decision'] == 'ACCEPT_PRODUCER4_SOURCE4_AND_266_CONTROL_DEFINITIONS_ONLY', 'EXACT_ORDERED_SOURCE_REVIEW')

# All executable code is copied from the accepted predecessor; no module import.
code_names = ['assemble.py', 'capture.py', 'contracts.py', 'explicit_inputs.py', 'outputs.py', 'request-from-plan.py', 'test_admission.py']
diffs = []
for name in code_names:
    old = small_bytes(BASE / name).decode()
    new = old
    if name == 'capture.py':
        old_source = next(line for line in old.splitlines() if line.startswith('CURRENT_PRODUCER_SOURCE='))
        old_acceptance = next(line for line in old.splitlines() if line.startswith('CURRENT_PRODUCER_ACCEPTANCE='))
        new = new.replace(old_source, 'CURRENT_PRODUCER_SOURCE=' + repr(sp))
        new = new.replace(old_acceptance, 'CURRENT_PRODUCER_ACCEPTANCE=' + repr(ap) + '\nCURRENT_SOURCE_LINEAGE=' + repr(lineage))
        old_join = "ack['producerSourceAcceptance']==CURRENT_PRODUCER_ACCEPTANCE and ack['clockSelection']==CLOCK_SELECTION"
        new_join = "ack['producerSourceAcceptance']==CURRENT_PRODUCER_ACCEPTANCE and ack['sourceBirth']==CURRENT_SOURCE_LINEAGE and ack['clockSelection']==CLOCK_SELECTION"
        need(new.count(old_join) == 1, 'ONE_PREEXISTING_LINEAGE_JOIN_LOCATION')
        new = new.replace(old_join, new_join)
    elif name == 'contracts.py':
        previous = next(line for line in old.splitlines() if line.startswith('REQUIRED_KNOWN_ACTORS='))
        new = new.replace(previous, 'REQUIRED_KNOWN_ACTORS=' + repr(tuple(known['knownActors'])))
        previous = next(line for line in old.splitlines() if line.startswith('ROOT_KNOWN_ACTORS_PIN='))
        new = new.replace(previous, 'ROOT_KNOWN_ACTORS_PIN=' + repr(known_pin))
        new = new.replace('COMPLETE_REQUIRED_ELEVEN_KNOWN_ACTORS', 'COMPLETE_REQUIRED_FIFTEEN_KNOWN_ACTORS')
    elif name == 'test_admission.py':
        before = "self._node_exact_and_mutations('test_guard_client.mjs',123,dict(scope='PRODUCER4_MOCK_FRESH_GUARD_SCHEDULER_ONLY',definitions=123,executed=123,"
        after = "self._node_exact_and_mutations('test_guard_client.mjs',129,dict(scope='PRODUCER4_MOCK_FRESH_GUARD_SCHEDULER_ONLY',definitions=129,executed=129,"
        need(new.count(before) == 1, 'ONE_GUARD_POSITIVE_FIXTURE_CHANGE')
        new = new.replace(before, after)
    compile(ast.parse(new), str(D / name), 'exec')
    write(D / name, new.encode())
    diffs.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=str(BASE / name), tofile=str(D / name)))

const = literals(D / 'contracts.py')
need(const['LIMITS'] == old_constants['LIMITS'] and const['LEDGER'] == old_constants['LEDGER'], 'ALL_CLOCK_LIMIT_CONSTANTS_IDENTICAL')
need(set(const['REQUIRED_KNOWN_ACTORS']) == set(known['knownActors']), 'CODE_EXACT_ROOT_FIFTEEN')
base_methods = [n.name + '.' + f.name for n in ast.parse(small_bytes(BASE / 'test_admission.py')).body if isinstance(n, ast.ClassDef)
                for f in n.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')]
cases = [n.name + '.' + f.name for n in ast.parse(small_bytes(D / 'test_admission.py')).body if isinstance(n, ast.ClassDef)
         for f in n.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')]
need(cases == base_methods and len(cases) == 21, 'EXACT_TWENTY_ONE_NAMES_RETAINED')
by_name = {Path(d['path']).name: d for d in source['sources']}
need(len(by_name) == 64, 'UNIQUE_CURRENT_SOURCE_FILENAMES')
for descriptor in source['sources'] + source['runtimeSources'] + list(source['configurations'].values()):
    verify(descriptor)

contract_pins = [known_pin, write(D / 'contracts/root-known-actors.json', small_bytes(known_pin['path']))]
for name in ('producer-source-acceptance-contract.json', 'capture-source-acceptance-contract.json', 'capture-admission-data-acceptance-contract.json', 'root-clock-source-selection.json'):
    contract_pins.append(write(D / 'contracts' / name, small_bytes(BASE / 'contracts' / name)))
contract_pins += [data_contract, write(D / 'contracts/current-producer-data-acceptance-contract-266.json', small_bytes(data_contract['path']))]
contributors = write(D / 'contributors.json', dict(
    schema='e02-producer4-266-capture-contributors-v1', author='/root/r5_plan_fix', coordinator='/root',
    reusedLifecycleCreator='/root/completion_wrapper', captureAuthors=['/root', '/root/r5_plan_fix', '/root/completion_wrapper'],
    inheritedRequiredEleven=list(old_constants['REQUIRED_KNOWN_ACTORS']), currentRequiredFifteen=known['knownActors'],
    currentProducerContributors=source['sourceContributors'], currentRootKnownAuthority=known_pin,
    scope='Explicit current/inherited declared creator-design union; unknown historical authorship remains UNKNOWN. Verification-only reviewers are not silently converted to implementation authors.',
    allReviewPairs='Current required fifteen plus every actually declared source/capture/admission author/operator are closed before the first review pair.',
    executionAuthorized=False))
admission_plan = write(D / 'admission-plan.json', dict(
    schema='e02-producer4-capture-admission-plan-v1', caseNames=cases, modelsDefined=21,
    source=pin(D / 'test_admission.py'), producerSource=sp, modelsExecuted=0,
    scope='PURE_MOCKED_CAPTURE_ADMISSION_ONLY', targetModelsExecuted=0, helperExecutions=0,
    ordinaryRoleExecutions=0, sourceReviewRequired=True, releaseRequired=True))
code_pins = [pin(D / name) for name in code_names] + contract_pins + [contributors, admission_plan, pin(Path(__file__).resolve())]
method = write(D / 'code-subject.json', dict(
    schema='e02-producer4-control-capture-code-subject-v1', authors=['/root', '/root/r5_plan_fix', '/root/completion_wrapper'],
    producerSource=sp, knownActors=known_pin, codeOnly=True, sources=code_pins,
    admissionModelsDefined=21, admissionModelsExecuted=0, targetModelsExecuted=0,
    helperExecutions=0, ordinaryRoleExecutions=0,
    excludedMutableMetadata=['execution-plan', 'reviews', 'acceptances', 'root-ack', 'runtime-output'],
    sourceReadiness='REQUIRES_INDEPENDENT_SOURCE_REVIEW_AND_SEPARATE_ADMISSION_DATA', selfApproval=False))

# Inherit immutable expected raw declarations/memberships, not observed runtime DATA.
# No SDK/APK/native/opaque inventory body is read or copied by preparation.
baseline_manifest_pin = pin(BASE / 'input-manifest.json')
baseline = read(BASE / 'input-manifest.json')
seen = {item['pin']['path']: copy.deepcopy(item) for item in baseline['files']}
need(len(seen) == baseline['actualInputCount'], 'UNIQUE_INDEPENDENT_BASELINE_DECLARATIONS')
coverage = {name: copy.deepcopy(rows) for name, rows in baseline['requiredCoverage'].items() if name.startswith('baseline_')}
coverage['inheritedExpectedDeclarations'] = [baseline_manifest_pin]

def add(descriptor, role, origin, group):
    path = descriptor['path']
    if path in seen:
        need(seen[path]['pin'] == descriptor, 'NO_CHANGED_PIN_ADOPTED_AS_BASELINE:' + path)
    else:
        verify(descriptor)
        seen[path] = dict(pin=descriptor, mode=stat.S_IMODE(Path(path).lstat().st_mode), role=role, origin=origin)
    if group:
        values = coverage.setdefault(group, [])
        if descriptor not in values:
            values.append(descriptor)

add(baseline_manifest_pin, 'METADATA_AUTHORITY', 'INDEPENDENT_IMMUTABLE_EXPECTED_INPUT_AUTHORITY_NOT_RUNTIME_DATA', None)
for descriptor in source['sources']:
    add(descriptor, 'SOURCE', 'CURRENT_DECLARED_SOURCE64', 'allCurrentSourceMembers')
for descriptor in source['runtimeSources']:
    add(descriptor, 'SOURCE', 'CURRENT_RUNTIME22', 'all22RuntimeWorkers')
for descriptor in source['configurations'].values():
    add(descriptor, 'METADATA_AUTHORITY', 'CURRENT_BOTH_ROLE_CONFIGURATIONS', 'bothCurrentConfigurations')
for descriptor in [sp, source['controlPlan']]:
    add(descriptor, 'METADATA_AUTHORITY', 'CURRENT_SOURCE_SUBJECT_AND_CONTROL_PLAN', 'currentSubjectControlPlan')
for descriptor in code_pins:
    add(descriptor, 'SOURCE', 'CURRENT_CAPTURE_IMMUTABLE_CODE', 'allCaptureCodeAndAdmissionDefinitions')
for descriptor in [ap, lineage] + reviews:
    add(descriptor, 'METADATA_AUTHORITY', 'EXACT_ISSUED_CURRENT_SOURCE_AUTHORITIES', 'currentAcceptedSourceAuthority')
lineage_doc = read(lineage['path'])
for key in ('completeFreeze', 'reviewerBirth'):
    add(lineage_doc[key], 'METADATA_AUTHORITY', 'EXPLICIT_CURRENT_ROOT_LINEAGE_' + key, 'currentAcceptedSourceAuthority')
for key in ('predecessorSource', 'originalProducer3Source', 'originalLeaseCore', 'latestFailedRunContext'):
    add(source[key], 'METADATA_AUTHORITY', 'EXPLICIT_CURRENT_SOURCE_' + key, 'currentLineageAndOriginalCore')
for descriptor in source['methodAdoptions']:
    add(descriptor, 'METADATA_AUTHORITY', 'EXPLICIT_CURRENT_METHOD_ADOPTION', 'currentLineageAndOriginalCore')
for descriptor in source['dataPrerequisitesOnly'].values():
    # Existing raw artifact/sdk descriptors must already be independently declared.
    need(descriptor['path'] in seen and seen[descriptor['path']]['pin'] == descriptor, 'UNCHANGED_RAW_PREREQUISITE_HAS_INDEPENDENT_EXPECTED_PIN')
    add(descriptor, seen[descriptor['path']]['role'], 'EXACT_UNCHANGED_RAW_PREREQUISITE', 'currentRuntimePrerequisites')
bindings = read(by_name['rebuilt-artifact-bindings.json']['path'])
for key in ('amethystApk', 'amethystProvenance', 'amethystAcceptance', 'helperApk', 'helperProvenance', 'helperAcceptance', 'rustBinary', 'acceptedE01', 'acceptedE01Acceptance', 'originalCanonicalE01'):
    descriptor = bindings[key]
    need(descriptor['path'] in seen and seen[descriptor['path']]['pin'] == descriptor, 'INDEPENDENT_ARTIFACT_NATIVE_E01_DECLARATION')
    add(descriptor, seen[descriptor['path']]['role'], 'CURRENT_UNCHANGED_ARTIFACT_NATIVE_E01_BINDING', 'currentArtifactNativeE01')

# Known identities use only actual explicit selectors. CODE/context/ACK stay acyclic.
proofs = []
participants = set()
def actor_fields(descriptor, fields):
    document = read(descriptor['path'])
    add(descriptor, 'METADATA_AUTHORITY', 'NAMED_CURRENT_ACTOR_AUTHORITY', 'actorProofAuthorities')
    for field in fields:
        if field not in document:
            continue
        value = document[field]
        values = list(enumerate(value)) if type(value) is list else [(None, value)]
        for index, actor in values:
            if type(actor) is str and (actor == '/root' or actor.startswith('/root/')):
                proof = dict(actor=actor, authority=descriptor, selector='/' + field + ('' if index is None else '/' + str(index)))
                if proof not in proofs:
                    proofs.append(proof)
                participants.add(actor)

actor_fields(known_pin, ['knownActors'])
actor_fields(sp, ['author', 'coordinator', 'sourceContributors', 'predecessorAuthor', 'operators'])
actor_fields(lineage, ['actor'])
for key in ('predecessorSource', 'originalProducer3Source'):
    actor_fields(source[key], ['author', 'coordinator', 'sourceContributors', 'predecessorAuthor', 'authors', 'operators'])
need(set(known['knownActors']) <= participants, 'ALL_FIFTEEN_PROVED_BEFORE_REVIEW')
context = write(D / 'actor-context.json', dict(
    schema='e02-producer4-capture-current-actor-context-v1', producerSource=sp,
    captureSource=method, sourceBirth=lineage, participants=sorted(participants), participantProofs=proofs))
manifest = write(D / 'input-manifest.json', dict(
    schema='e02-producer4-explicit-host-input-manifest-v1', producerSource=sp,
    closedSourceSubjectKeys=sorted(source), controlPlan=source['controlPlan'],
    files=[seen[key] for key in sorted(seen)], actualInputCount=len(seen), maximumInputCount=20000,
    requiredCoverage=coverage, fullTrees=baseline['fullTrees'], nodeDependencies=baseline['nodeDependencies'],
    baselineInputAuthority=baseline_manifest_pin,
    scope='EXPLICIT_FROZEN_EXPECTED_INPUT_DECLARATIONS_PLUS_CURRENT64_AND_CAPTURE_CODE; ALL_FRESH_ACTUAL_CUSTODY_IS_A_FUTURE_RELEASED_CAPTURE',
    baselineDataTransferClaimed=False, privateKeysRead=False,
    opaqueRawMeaning='Every declared HOST raw input is uniformly streamed before/after each future scope. Preparation inherits immutable expected descriptors only; no descriptor-shaped recursion or opaque JSON body parsing.'))

scopes = []
for index, (name, count) in enumerate(zip(const['FILES'], counts)):
    descriptor = by_name[name]
    text = small_bytes(descriptor['path']).decode()
    names = None
    if index >= 5:
        names = [c.name + '.' + f.name for c in ast.parse(text).body if isinstance(c, ast.ClassDef)
                 for f in c.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')]
        need(len(names) == count, 'EXACT_SELECTED_PYTHON_DEFINITION_NAMES')
    elif index == 4:
        names = re.findall(r"await test\('([^']+)'", text)
        need(len(names) == count, 'EXACT_SELECTED_OBSERVATION_NAMES')
    tools = read(BASE / 'execution-plan.json')['tools']
    scopes.append(dict(scope=name, source=descriptor,
        argv=[tools['node']['path'], descriptor['path']] if index < 5 else [tools['python']['path'], '-I', '-B', descriptor['path']],
        cwd=str(Path(descriptor['path']).parent), count=count, definitionNames=names,
        format='EXACT_SELECTED_NODE_JSON' if index < 5 else 'QUIET_UNITTEST_NO_SKIPS'))
plan = dict(schema='e02-producer4-control-capture-plan-v1', readiness=False,
    producerSource=sp, captureSource=method, inputManifest=manifest, limits=const['LIMITS'],
    deadlineLedger=const['LEDGER'], scopes=scopes, countsSeparate=counts, tools=tools,
    outputRoot=None, requiredCoverage=coverage, clockSelection=clock,
    actualSourceReviewPins=reviews, captureSourceReviews=None, captureSourceAcceptance=None,
    admissionDataAcceptance=None, rootAcknowledgement=None, scope='SOURCE_PREPARATION_ONLY_NO_EXECUTION_AUTHORITY')
request = dict(cmd=shlex.join(['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'LC_ALL=C.UTF-8',
    '/usr/bin/timeout', '--signal=KILL', '1203s', tools['python']['path'], '-I', '-B', str(D / 'capture.py'),
    '--execute-once', '--root-ack-sha', '<ACTUAL_ROOT_ACK_SHA256>']), workdir=str(D), login=False,
    yield_time_ms=1000, max_output_tokens=2000)
request_pin = write(D / 'request-template.json', request)
plan_pin = write(D / 'execution-plan.json', plan)
binding = write(D / 'runtime-bindings.json', dict(schema='e02-producer4-capture-runtime-bindings-v1',
    readiness=False, producerSource=sp, producerAcceptance=ap, captureSourceAcceptance=None,
    admissionDataAcceptance=None, rootAcknowledgement=None))
ack = {key: None for key in const['ACK_KEYS'].split()}
ack.update(schema='e02-producer4-control-capture-root-ack-v1', actor='/root', executionAuthorized=False,
    scope='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY', producerSource=sp,
    producerSourceAcceptance=ap, producerReviews=reviews, captureSource=method, admissionPlan=admission_plan,
    sourceBirth=lineage, actorContext=context, inputManifest=manifest, plan=plan_pin, clockSelection=clock,
    requestContract=request_pin, runtimeBindings=binding, authors=['/root', '/root/r5_plan_fix', '/root/completion_wrapper'],
    operators=None, noRetry=True)
ack_pin = write(D / 'root-ack-template.json', ack)

before_functions = functions(BASE / 'capture.py')
after_functions = functions(D / 'capture.py')
need(set(before_functions) == set(after_functions), 'NO_LIFECYCLE_FUNCTION_ADDED_OR_REMOVED')
changed_functions = [name for name in before_functions if before_functions[name] != after_functions[name]]
need(changed_functions == ['validate_bundle'], 'ONLY_EXPLICIT_CURRENT_LINEAGE_JOIN_CHANGES_FUNCTION_AST')
unchanged_files = [name for name in code_names if small_bytes(BASE / name) == small_bytes(D / name)]
need(set(unchanged_files) == {'assemble.py', 'explicit_inputs.py', 'outputs.py', 'request-from-plan.py'}, 'EXACT_FOUR_UNCHANGED_MODULES')
diff_pin = write(OUT / 'source.diff', ''.join(diffs).encode())
reuse = write(D / 'lifecycle-source-comparison.json', dict(
    schema='e02-producer4-capture-lease-r1-source-equivalence-v1', predecessorCapture=pin(BASE / 'capture.py'),
    currentCapture=pin(D / 'capture.py'), predecessorMethod=pin(BASE / 'code-subject.json'),
    threePredecessorFunctionAstEqual={name:before_functions[name] == after_functions[name] for name in ('signal_owned_group', 'finish_owned', 'capture_scope')},
    unchangedModules=unchanged_files, changedCaptureFunctions=changed_functions,
    scope='Exact predecessor CODE equivalence only. No historical whole capture21/producer260 DATA transfer.', modelsExecuted=0))
delta = write(OUT / 'binding-and-ast-delta.json', dict(
    schema='e02-producer4-266-capture-binding-delta-v1', author='/root/r5_plan_fix', sourceDiff=diff_pin,
    predecessorMethod=pin(BASE / 'code-subject.json'), currentMethod=method,
    exactCurrentProducer=sp, producerSourceAcceptance=ap, pinnedLineage=lineage, knownActors=known_pin,
    limitsIdentical=const['LIMITS'] == old_constants['LIMITS'], ledgerIdentical=const['LEDGER'] == old_constants['LEDGER'],
    captureCodeDelta='Two producer/SOURCE constants; added CURRENT_SOURCE_LINEAGE constant and exact ack.sourceBirth conjunct in unchanged validate_bundle admission boundary. All other function ASTs unchanged.',
    contractsCodeDelta='Exact required15 actor constant and pinned Root authority replace old11/old pin. Only diagnostic ELEVEN becomes FIFTEEN inside validate_acceptances; the full union remains before all three ordered QA/security pairs.',
    admissionDefinitionDelta='Exactly21 original top-level names/assertions retained. Legacy method test_exact_guard123_schema_and_mutations now tests actual129 positive/mutations. Legacy test_each_eleven_known_helpers_rejected_in_each_six_review_slots iterates actual15, so90 actor/slot negatives replace66 without adding a definition. Other bodies/negative fixtures unchanged.',
    expectedInputPreparation='Inherited immutable2083 expected descriptors/membership authority plus explicit current64/22/config/SOURCE/lineage/capture declarations; no SDK/APK/native scan or runtime data is adopted as a baseline here.',
    knownActorOldElevenRetained=True, unknownHistoricalAuthorship='UNKNOWN',
    lifecycleComparison=reuse, actualTargetArgv='Pinned Node and exact current script only; five Python scripts keep -I -B. No new flags.',
    admissionDefined=21, admissionExecuted=0, targetDefined=266, targetExecuted=0,
    helperExecuted=0, ordinaryRolesExecuted=0, rootGrant=None))

# Durable SOURCE copies only: never copy referenced old operational proof payloads.
archive_sources = [Path(descriptor['path']) for descriptor in code_pins] + [D / name for name in (
    'code-subject.json', 'actor-context.json', 'input-manifest.json', 'execution-plan.json', 'runtime-bindings.json',
    'request-template.json', 'root-ack-template.json', 'lifecycle-source-comparison.json')]
archive_sources = list(dict.fromkeys(archive_sources))
copies = []
for index, path in enumerate(archive_sources, 1):
    target = OUT / 'source-archive' / ('%03d-' % index + path.name)
    copied = write(target, small_bytes(path))
    original = pin(path)
    need(copied['bytes'] == original['bytes'] and copied['sha256'] == original['sha256'], 'EXACT_SOURCE_COPY')
    copies.append(dict(original=original, copy=copied))
archive = write(OUT / 'archive-manifest.json', dict(schema='e02-producer4-capture-source-archive-v1',
    scope='IMMUTABLE_CURRENT_SOURCE_AND_PREPARATION_METADATA_ONLY_NO_BINARY_OR_OPERATIONAL_FIXTURE_COPY', copies=copies))
summary = dict(sourceMembers=64, runtimeWorkers=22, selectedGroups=10, targetDefinitions=266,
    countsSeparate=EXPECTED, admissionDefinitions=21, expectedStaticInputs=len(seen),
    expectedInputSource='Independent immutable predecessor declarations plus exact new small Source/authority descriptors; actual fresh before/after custody is a future released run.',
    sdkDeclaredFiles=434, guardDeclaredFiles=522, nodeDeclaredFiles=816, nodeDeclaredDirectories=65,
    nodeDeclaredSafeLinks=2, sourceArchiveCopies=len(copies), allExecutionsByPreparation=0)
packet = write(OUT / 'source-packet.json', dict(schema='e02-producer4-capture-source-packet-v1',
    author='/root/r5_plan_fix', producerSource=sp, producerAcceptance=ap, producerReviews=reviews,
    sourceBirth=lineage, knownActors=known_pin, current266DataContract=data_contract,
    codeSubject=method, admissionPlan=admission_plan, inputManifest=manifest, executionPlan=plan_pin,
    rootAckTemplate=ack_pin, requestTemplate=request_pin, runtimeBindings=binding, actorContext=context,
    contributorManifest=contributors, bindingDelta=delta, lifecycleComparison=reuse, archiveManifest=archive,
    summary=summary, readiness=False, captureSourceReviews=None, captureSourceAcceptance=None,
    admissionData=None, admissionDataAcceptance=None, actual266DataAcceptance=None, rootGrant=None,
    remainingGates=['Fresh independent exact current capture SOURCE review',
        'Separate Root release and one current21 admission execution plus independent DATA acceptance',
        'Root actual current input/concrete output/request/once-ACK binding and independent readiness review',
        'Separate Root release for whole266 ten-scope capture and genuine external API custody/assembler/independent DATA'],
    historicalDataTransferClaimed=False, operationalProofCopies=0))
entrypoint = write(OUT / 'review-entrypoint.json', dict(schema='e02-producer4-capture-source-review-entrypoint-v1',
    packet=packet, codeSubject=method, inputManifest=manifest, admissionPlan=admission_plan,
    executionPlan=plan_pin, rootAckTemplate=ack_pin, summary=summary, sourceOnly=True, readiness=False,
    modelsExecuted=0, helperExecutions=0, ordinaryRolesExecuted=0))
print(json.dumps(dict(entrypoint=entrypoint, packet=packet, codeSubject=method,
    admissionPlan=admission_plan, inputManifest=manifest, summary=summary, writesStopped=True), indent=2))
