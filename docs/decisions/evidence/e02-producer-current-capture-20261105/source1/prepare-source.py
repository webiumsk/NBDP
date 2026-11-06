"""Bounded SOURCE copy/typed expected-input preparation only; no project imports."""
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat

R = Path('/home/peterhorvath/apps/bitcoin/NBDP')
E = R / 'docs/decisions/evidence'
OUT = E / 'e02-producer-current-capture-20261105/source1'
CAP = OUT / 'capture'
BASE = Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r2/source4-lease-r1')
SCOPE = E / 'e02-goal-resume-20261104/capture-successor-root-scope-20261105.json'
FORENSIC = E / 'e02-goal-resume-20261104/current-capture-input-forensic-report-20261105.json'
TYPE_SCOPE = E / 'e02-goal-resume-20261104/capture-request-type-preservation-supplement-20261105.json'
ASSERT_SCOPE = E / 'e02-goal-resume-20261104/capture-request-assertion-clarification-20261105.json'
CAPTURE_KNOWN = E / 'e02-producer-current-capture-root-authority-20261105/root-known-actors.json'
TYPE_DESIGNER = '/root/collector_policy_security_553c5bfd'
OLD_RENDER = E / 'e02-producer4-266-capture-ready-r2-20261029/render.py'
ACTOR = '/root/native_rebuild_prepare'
ENGINES = ['assemble.py', 'capture.py', 'contracts.py', 'explicit_inputs.py', 'outputs.py', 'request-from-plan.py', 'test_admission.py']
MEM = {}
READS = {}
MODES = {}


def need(value, message):
    if not value:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def shape(pin):
    need(type(pin) is dict and set(pin) == {'path', 'bytes', 'sha256'}, 'EXACT_EXPLICIT_DESCRIPTOR')
    path = Path(pin['path'])
    need(path.is_absolute() and str(path) == os.path.normpath(str(path)) and '..' not in path.parts
         and type(pin['bytes']) is int and 0 <= pin['bytes'] <= 2147483648, 'CLOSED_CANONICAL_DECLARED_OPERAND')
    return path


def raw(path, metadata=True):
    path = Path(path)
    if path in MEM:
        return MEM[path]
    if path in READS:
        return READS[path]
    for parent in (path, *path.parents):
        need(not parent.is_symlink(), 'NO_DECLARED_INPUT_ALIAS')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and (not metadata or before.st_size <= 16777216), 'BOUNDED_METADATA_ONLY')
    with path.open('rb') as handle:
        value = handle.read(16777217)
    after = path.lstat()
    need(len(value) == before.st_size and all(getattr(before, k) == getattr(after, k)
         for k in ('st_dev', 'st_ino', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'STABLE_DECLARED_METADATA')
    READS[path] = value
    MODES[path] = stat.S_IMODE(after.st_mode)
    return value


def pin(path):
    path = Path(path)
    value = raw(path)
    return dict(path=str(path), bytes=len(value), sha256=hashlib.sha256(value).hexdigest())


def verify(descriptor):
    path = shape(descriptor)
    if path in MEM or path in READS:
        need(pin(path) == descriptor, 'EXPECTED_DECLARED_METADATA_PIN')
        return
    for parent in (path, *path.parents):
        need(not parent.is_symlink(), 'NO_RAW_INPUT_ALIAS')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size == descriptor['bytes'], 'EXPECTED_DECLARED_RAW_SIZE')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    after = path.lstat()
    need(digest.hexdigest() == descriptor['sha256'] and all(getattr(before, k) == getattr(after, k)
         for k in ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_mtime_ns', 'st_ctime_ns')), 'EXACT_NEW_EXPECTED_RAW_PIN')
    MODES[path] = stat.S_IMODE(after.st_mode)


def doc(path, expected=None):
    value = raw(path)
    if expected is not None:
        need(pin(path) == expected, 'EXACT_TYPED_METADATA_PIN')
    def pairs(items):
        result = {}
        for key, child in items:
            need(key not in result, 'NO_DUPLICATE_TYPED_KEYS')
            result[key] = child
        return result
    return json.loads(value, object_pairs_hook=pairs)


def put(path, value):
    path = Path(path)
    need(path.is_relative_to(OUT) and path not in MEM and not path.exists(), 'ONLY_NEW_OWNED_SOURCE_OUTPUT')
    MEM[path] = value if type(value) is bytes else encode(value)
    MODES[path] = 0o600
    return pin(path)


def constants(value):
    result = {}
    for node in ast.parse(value).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (TypeError, ValueError):
                pass
    return result


def functions(value):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(value).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def methods(value):
    return [c.name + '.' + f.name for c in ast.parse(value).body if isinstance(c, ast.ClassDef)
            for f in c.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')]


def main():
    need(Path(__file__).resolve() == OUT / 'prepare-source.py' and not CAP.exists()
         and not (OUT / 'review-entrypoint.json').exists(), 'NEW_SOURCE_PACKET_ONLY')
    scope, forensic = doc(SCOPE), doc(FORENSIC)
    need(scope['owner'] == ACTOR and scope['ownedRoot'] == str(OUT) and not scope['admissionOrProducerControlsAuthorized'], 'ROOT_SOURCE_ONLY_SCOPE')
    producer_pin, acceptance_pin, lineage_pin, producer_known_pin = [scope[key] for key in
        ('acceptedProducerSource', 'producerSourceAcceptance', 'sourceLineage', 'knownActors')]
    known_pin = pin(CAPTURE_KNOWN)
    need(known_pin['sha256'] == '94fd5716503e40b7472e8432e768e6e381bb71ded02bdae47523affc8fe25673', 'ACTUAL_ROOT_CAPTURE_KNOWN18_OVERRIDE')
    producer = doc(producer_pin['path'], producer_pin)
    accepted = doc(acceptance_pin['path'], acceptance_pin)
    lineage = doc(lineage_pin['path'], lineage_pin)
    known = doc(known_pin['path'], known_pin)
    need(accepted['subject'] == producer_pin and lineage['acceptance'] == acceptance_pin
         and known['producerSource'] == producer_pin and len(known['knownActors']) == 18
         and set(doc(producer_known_pin['path'], producer_known_pin)['knownActors']) <= set(known['knownActors']), 'CURRENT_ISSUED_PRODUCER_LINEAGE_AND_CAPTURE_KNOWN18')
    baseline_pin = forensic['baseline']
    baseline = doc(baseline_pin['path'], baseline_pin)
    need(len(baseline['files']) == baseline['actualInputCount'] == 2175, 'EXACT_PREDECESSOR2175')
    all_old = {row['pin']['path']: copy.deepcopy(row) for row in baseline['files']}
    removed = {row['path']: row for row in forensic['supersededExternalAliases']}
    need(len(all_old) == 2175 and len(removed) == 6, 'SIX_ENUMERATED_ALIASES_ONLY')
    for path, item in removed.items():
        expected = dict(pin={key: item[key] for key in ('path', 'bytes', 'sha256')},
                        mode=int(item['mode'], 8), role=item['role'], origin=item['origin'])
        need(all_old[path] == expected, 'FORENSIC_EXACT_OLD_ROW')
    retained = {path: row for path, row in all_old.items() if path not in removed}
    need(len(retained) == 2169, 'EXACT_RETAINED2169')
    seen = copy.deepcopy(retained)
    selections, coverage = [], {}

    def add(descriptor, selector, group, role='METADATA_AUTHORITY'):
        path = shape(descriptor)
        need(str(path) not in removed, 'NEVER_REINTRODUCE_SUPERSEDED_ALIAS')
        if str(path) in seen:
            need(seen[str(path)]['pin'] == descriptor, 'DUPLICATE_PATH_PIN_CONFLICT:' + str(path))
        else:
            verify(descriptor)
            mode = MODES[path]
            seen[str(path)] = dict(pin=descriptor, mode=mode, role=role, origin=selector)
        if group:
            target = coverage.setdefault(group, [])
            if descriptor not in target:
                target.append(descriptor)
        selections.append(dict(selector=selector, pin=descriptor, role=role, coverageGroup=group))
        return descriptor

    def metadata(descriptor, selector, group, schema=None):
        add(descriptor, selector, group)
        value = doc(descriptor['path'], descriptor)
        if schema:
            need(value.get('schema') == schema, 'TYPED_SCHEMA:' + selector)
        return value

    def named(document, fields, prefix, group, role='METADATA_AUTHORITY'):
        for field in fields:
            add(document[field], prefix + '/' + field, group, role)

    code_before = {name: raw(BASE / name) for name in ENGINES}
    old_const = constants(code_before['contracts.py'])
    policy = {key: scope['actualRequestPolicy'][key] for key in ('sandbox_permissions', 'justification')}
    request_keys = scope['actualRequestPolicy']['keys']
    contracts = code_before['contracts.py'].decode()
    for key, value in [('REQUIRED_KNOWN_ACTORS', tuple(known['knownActors'])), ('ROOT_KNOWN_ACTORS_PIN', known_pin)]:
        original = next(line for line in contracts.splitlines() if line.startswith(key + '='))
        contracts = contracts.replace(original, key + '=' + repr(value), 1)
    contracts = contracts.replace("'COMPLETE_REQUIRED_FIFTEEN_KNOWN_ACTORS'", "'COMPLETE_REQUIRED_EIGHTEEN_KNOWN_ACTORS'")
    marker = "ACK_KEYS="
    index = contracts.index(marker)
    contracts = contracts[:index] + 'REQUEST_KEYS=' + repr(tuple(request_keys)) + '\nREQUEST_POLICY=' + repr(policy) + '\n' + contracts[index:]
    original = 'return dict(cmd=shlex.join(argv),workdir=here,login=False,yield_time_ms=1000,max_output_tokens=2000)'
    need(contracts.count(original) == 1, 'ONE_REQUEST_CONSTRUCTOR')
    contracts = contracts.replace(original, original[:-1] + ',**REQUEST_POLICY)', 1)
    contracts = contracts.replace("set(a)==set('cmd workdir login yield_time_ms max_output_tokens'.split())", 'set(a)==set(REQUEST_KEYS)')
    contracts = contracts.replace("'EXACT_FIVE_KEY_FOREGROUND_REQUEST'", "'EXACT_SEVEN_KEY_FOREGROUND_REQUEST'")
    marker = 'def validate_origin(origin,expected,operators):\n'
    need(contracts.count(marker) == 1, 'ONE_ACTUAL_ORIGIN_VALIDATOR')
    typed_requests = '''def validate_request(value):
    closed(value,' '.join(REQUEST_KEYS))
    need(type(value['cmd']) is str and type(value['workdir']) is str and type(value['login']) is bool and value['login'] is False,'ACTUAL_REQUEST_STRING_AND_BOOLEAN_TYPES')
    need(type(value['yield_time_ms']) is int and value['yield_time_ms']>0 and type(value['max_output_tokens']) is int and value['max_output_tokens']>0,'ACTUAL_REQUEST_PLAIN_INTEGER_TYPES')
    need(all(type(value[k]) is str and value[k]==v for k,v in REQUEST_POLICY.items()),'EXACT_ROOT_REQUEST_POLICY_BYTES')
    return value
def canonical_request(value):
    validate_request(value)
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('utf8')
def valid_poll_request(value,session):
    need(type(value) is dict and set(value)<=set('session_id chars yield_time_ms max_output_tokens'.split()),'DECLARED_POLL_FIELDS_ONLY')
    need(type(value.get('session_id')) is int and value['session_id']>0 and value['session_id']==session,'POLL_SESSION_PLAIN_INTEGER_IDENTITY')
    need('chars' not in value or type(value['chars']) is str and value['chars']=='','POLL_READ_ONLY_EMPTY_STRING')
    for key in ('yield_time_ms','max_output_tokens'):
        need(key not in value or type(value[key]) is int and value[key]>0,'POLL_PLAIN_POSITIVE_INTEGER_TYPES')
    return True

'''
    contracts = contracts.replace(marker, typed_requests + marker + '    expected_bytes=canonical_request(expected)\n')
    contracts = contracts.replace('a==expected and set(a)==set(REQUEST_KEYS)', 'canonical_request(a)==expected_bytes')
    original_poll = "a['session_id']==session and a.get('chars','')=='' and set(a)<=set('session_id chars yield_time_ms max_output_tokens'.split())"
    need(contracts.count(original_poll) == 1, 'ONE_TYPED_POLL_BOUNDARY')
    contracts = contracts.replace(original_poll, 'valid_poll_request(a,session)', 1)
    original_terminal = "r['exit_code']==0 and (r.get('session_id') is None or r['session_id']==session)"
    need(contracts.count(original_terminal) == 1, 'ONE_TYPED_TERMINAL_BOUNDARY')
    contracts = contracts.replace(original_terminal, "type(r['exit_code']) is int and r['exit_code']==0 and (r.get('session_id') is None or type(r['session_id']) is int and r['session_id']==session)", 1)
    capture = code_before['capture.py'].decode()
    for key, value in [('CURRENT_PRODUCER_SOURCE', producer_pin), ('CURRENT_PRODUCER_ACCEPTANCE', acceptance_pin), ('CURRENT_SOURCE_LINEAGE', lineage_pin)]:
        original = next(line for line in capture.splitlines() if line.startswith(key + '='))
        capture = capture.replace(original, key + '=' + repr(value), 1)
    capture = capture.replace('    from outputs import parse_outcome\n', '    from outputs import parse_outcome\n    from input_authority import validate_expected_authority\n', 1)
    marker = "    docs['knownActors']=metadata(ROOT_KNOWN_ACTORS_PIN,deadline)\n"
    need(capture.count(marker) == 1, 'ONE_NAMED_AUTHORITY_LOAD_BOUNDARY')
    capture = capture.replace(marker, marker + "    docs['inputAuthority']=metadata(docs['inputManifest']['currentExpectedInputAuthority'],deadline)\n    docs['baselineInputManifest']=metadata(docs['inputAuthority']['baselineManifest'],deadline)\n")
    marker = "    need(manifest['requiredCoverage']==plan['requiredCoverage'],'EXACT_CLOSED_COVERAGE_GROUPS')\n"
    capture = capture.replace(marker, marker + "    validate_expected_authority(docs['inputAuthority'],docs['baselineInputManifest'],manifest)\n")
    capture = capture.replace("'EXACT_ACYCLIC_FIVE_KEY_REQUEST_TEMPLATE'", "'EXACT_ACYCLIC_SEVEN_KEY_REQUEST_TEMPLATE'")
    admission = code_before['test_admission.py'].decode()
    original = "set('cmd workdir login yield_time_ms max_output_tokens'.split())"
    need(admission.count(original) == 1, 'ONLY_AUTHORIZED_OLD5_ASSERTION')
    admission = admission.replace(original, "set('cmd workdir login yield_time_ms max_output_tokens sandbox_permissions justification'.split())", 1)
    additions = raw(OUT / 'admission-additions.fragment').decode()
    marker = "if __name__=='__main__':unittest.main(verbosity=2)"
    need(admission.count(marker) == 1, 'EXACT_ADMISSION_ENTRY')
    admission = admission.replace(marker, additions + '\n' + marker)
    for name in ENGINES:
        value = {'contracts.py': contracts.encode(), 'capture.py': capture.encode(), 'test_admission.py': admission.encode()}.get(name, code_before[name])
        ast.parse(value, filename=name)
        put(CAP / name, value)
    put(CAP / 'input_authority.py', raw(OUT / 'input_authority.py'))
    original_renderer = raw(OLD_RENDER).decode()
    helpers = original_renderer[original_renderer.index('def need('):original_renderer.index("need(not (OUT / 'review-entrypoint.json')")]
    renderer_header = '"""Owned metadata-only current readiness renderer. No installation, process or target imports."""\nimport copy,hashlib,json,os,pathlib,secrets,shlex,stat,sys\n'
    renderer_header += 'OWNED_ROOT=pathlib.Path(' + repr(str(OUT)) + ')\nHERE=OWNED_ROOT/\'capture\'\n'
    for key, value in [('PRODUCER_PIN', producer_pin), ('PRODUCER_ACCEPTANCE', acceptance_pin), ('LINEAGE_PIN', lineage_pin), ('KNOWN_PIN', known_pin), ('REQUEST_KEYS', request_keys), ('REQUEST_POLICY', policy)]:
        renderer_header += key + '=' + repr(value) + '\n'
    renderer = (renderer_header + '\n' + helpers + raw(OUT / 'ready-render-main.fragment').decode()).encode()
    ast.parse(renderer)
    renderer_pin = put(OUT / 'render_ready.py', renderer)
    need(all(functions(original_renderer)[key] == functions(renderer)[key] for key in ('need', 'encode', 'pin_bytes', 'read', 'doc', 'put')), 'ORIGINAL_READY_R2_HELPERS_BYTE_AST_LINEAGE')
    new_const = constants(MEM[CAP / 'contracts.py'])
    need(new_const['LIMITS'] == old_const['LIMITS'] and new_const['LEDGER'] == old_const['LEDGER'] and list(new_const['REQUEST_KEYS']) == request_keys, 'ALL_ORIGINAL_CLOCKS_CAPS_AND_EXACT7')
    old_names, case_names = methods(code_before['test_admission.py']), methods(MEM[CAP / 'test_admission.py'])
    need(len(old_names) == 21 and case_names[:21] == old_names and len(case_names) == len(set(case_names)), 'ALL_ORIGINAL21_NAMES_RETAINED')
    old_tests = {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(code_before['test_admission.py'])) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')}
    new_tests = {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(MEM[CAP / 'test_admission.py'])) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')}
    need([name for name in old_tests if old_tests[name] != new_tests[name]] == ['test_exact_five_key_direct_and_same_session_original_api'], 'ONLY_ROOT_AUTHORIZED_KEYSET_ASSERTION_CHANGES')

    bindings = doc(next(d['path'] for d in producer['sources'] if Path(d['path']).name == 'rebuilt-artifact-bindings.json'))
    native_binary, helper_apk = bindings['rustBinary'], bindings['helperApk']
    replacements = {path: native_binary if item.get('replacement') == native_binary['path'] else helper_apk
                    for path, item in removed.items() if item.get('replacement')}
    for key, rows in baseline['requiredCoverage'].items():
        coverage[key] = []
        for descriptor in rows:
            current = replacements.get(descriptor['path'], descriptor)
            need(current['path'] not in removed, 'NO_DANGLING_REMOVED_BASELINE_COVERAGE')
            if current not in coverage[key]:
                coverage[key].append(current)
    current_groups = ['allCurrentSourceMembers', 'all22RuntimeWorkers', 'bothCurrentConfigurations', 'currentSubjectControlPlan',
        'allCaptureCodeAndAdmissionDefinitions', 'currentAcceptedSourceAuthority', 'currentLineageAndOriginalCore',
        'currentRuntimePrerequisites', 'currentArtifactNativeE01', 'actorProofAuthorities']
    for key in current_groups:
        coverage[key] = []
    for descriptor in producer['sources']:
        add(descriptor, 'CURRENT_PRODUCER_SELECTED_SOURCE64', 'allCurrentSourceMembers', 'SOURCE')
    for descriptor in producer['runtimeSources']:
        add(descriptor, 'CURRENT_PRODUCER_RUNTIME22', 'all22RuntimeWorkers', 'SOURCE')
    for descriptor in producer['configurations'].values():
        add(descriptor, 'CURRENT_BOTH_ROOT_CANDIDATE_CONFIGURATIONS', 'bothCurrentConfigurations')
    for descriptor in (producer_pin, producer['controlPlan']):
        add(descriptor, 'CURRENT_SOURCE_SUBJECT_CONTROL', 'currentSubjectControlPlan')
    add(baseline_pin, 'IMMUTABLE_PREDECESSOR2175_AUTHORITY', 'inheritedExpectedDeclarations')
    for path in (SCOPE, FORENSIC, TYPE_SCOPE, ASSERT_SCOPE):
        add(pin(path), 'ROOT_BOUNDED_METHOD_SCOPE_AND_FORENSIC_PROPOSAL', 'currentInputMethodProvenance')
    add(producer_known_pin, 'IMMUTABLE_PRODUCER_KNOWN17_PRECEDES_LATER_CAPTURE18', 'currentInputMethodProvenance')
    for descriptor in [acceptance_pin, lineage_pin, known_pin, lineage['completeFreeze'], lineage['reviewerBirth']] + accepted['reviews']:
        add(descriptor, 'ACTUAL_CURRENT_PRODUCER_ROOT_AUTHORITY', 'currentAcceptedSourceAuthority')
    add(known_pin, 'ALL_ACTUAL_CAPTURE_KNOWN18_FIELD_PROOFS', 'actorProofAuthorities')
    for key in ('predecessorSource', 'originalProducer3Source', 'originalLeaseCore', 'latestFailedRunContext', 'fullSourceDiff', 'sourceLineage'):
        add(producer[key], 'NAMED_SOURCE_LINEAGE_' + key, 'currentLineageAndOriginalCore')
    for descriptor in producer['methodAdoptions']:
        add(descriptor, 'NAMED_APPROVED_SOURCE_METHOD', 'currentLineageAndOriginalCore')
    for descriptor in producer['dataPrerequisitesOnly'].values():
        add(descriptor, 'CURRENT_RUNTIME_PREREQUISITE', 'currentRuntimePrerequisites', 'ARTIFACT')
    for key in ('amethystApk', 'amethystProvenance', 'amethystAcceptance', 'helperApk', 'helperProvenance',
                'helperAcceptance', 'rustBinary', 'acceptedE01', 'acceptedE01Acceptance', 'originalCanonicalE01', 'nativeBuildAcceptance'):
        add(bindings[key], 'NAMED_CURRENT_BINDING/' + key, 'currentArtifactNativeE01', 'ARTIFACT' if key in ('amethystApk', 'helperApk', 'rustBinary') else 'METADATA_AUTHORITY')
    # Typed finite accepted artifact tables; never recursively follow descriptors.
    hacc = metadata(bindings['helperAcceptance'], 'CLIPBOARD/acceptance', 'currentClipboardEvidence', 'nbdp-actual-artifact-data-acceptance-v1')
    need(hacc['subject'] == bindings['helperProvenance'], 'CURRENT_HELPER_CANONICAL_SUBJECT')
    for descriptor in hacc['reviews']:
        add(descriptor, 'CLIPBOARD/actualReviews', 'currentClipboardEvidence')
    helper = metadata(hacc['subject'], 'CLIPBOARD/canonical12Subject', 'currentClipboardEvidence')
    need(len(helper) == 12 and helper['apk'] == helper_apk and len(helper['retainedCopies']) == 18, 'EXACT_CANONICAL12_AND18_REPOSITORY_COPIES')
    named(helper, ['buildResult', 'outerToolReceipt', 'before', 'after'], 'CLIPBOARD/subject', 'currentClipboardEvidence')
    for index, row in enumerate(helper['retainedCopies']):
        need(set(row) == {'source', 'repositoryCopy'}, 'CORRECT_REPOSITORY_COPY_SELECTOR')
        add(row['repositoryCopy'], 'CLIPBOARD/retainedCopies/' + str(index) + '/repositoryCopy', 'currentClipboardEvidence', 'OPAQUE_PREREQUISITE')
    hentry_path = E / 'e02-clipboard-helper-current-build-20261105/review-entrypoint.json'
    hentry = metadata(pin(hentry_path), 'CLIPBOARD/currentReviewEntrypoint', 'currentClipboardEvidence')
    named(hentry, ['rootBuildRelease', 'actualBuildOrigin', 'sourceAndClosureAcceptance', 'externalAdmissionAdoption',
        'preservation', 'publicCopyOrigin', 'publicCopyReceipt', 'qaVerificationRelease'], 'CLIPBOARD/entrypoint', 'currentClipboardEvidence')
    add(hentry['repositoryPublicMirror'], 'CLIPBOARD/entrypoint/repositoryPublicMirror', 'currentClipboardEvidence', 'ARTIFACT')
    for name in ['result.json', 'preflight.json', 'apksigner-platform-origin.json', 'aapt2-platform-origin.json', 'apksigner-tool-output.txt', 'aapt2-tool-output.txt']:
        path = E / 'e02-clipboard-helper-current-build-20261105/independent-qa' / name
        add(pin(path), 'CLIPBOARD/actualIndependentVerifierData/' + name, 'currentClipboardEvidence', 'OPAQUE_PREREQUISITE')
    nacc = metadata(bindings['nativeBuildAcceptance'], 'NATIVE/acceptance', 'currentNativeEvidence', 'nbdp-native-build-compilation-evidence-acceptance-v1')
    need(nacc['binary'] == native_binary, 'CURRENT_INDEPENDENT_NATIVE_SNAPSHOT')
    native = metadata(nacc['subject'], 'NATIVE/artifactSubject', 'currentNativeEvidence')
    for descriptor in nacc['reviews']:
        add(descriptor, 'NATIVE/actualReviews', 'currentNativeEvidence')
    named(native, ['concreteInputSubject', 'concreteAcceptance', 'rootBuildRelease', 'artifactSnapshot', 'artifactSnapshotOrigin',
        'rawObserverDisposition', 'actualDependencyProvenance', 'sourceAndToolBefore', 'sourceAndToolAfter',
        'postInputObservationOrigin', 'rawPreservation'], 'NATIVE/subject', 'currentNativeEvidence')
    need(len(native['actualDockerOrigins']) == 9 and len(native['actualOperationalHostOrigins']) == 3, 'EXACT9_DOCKER3_HOST_ORIGINS')
    for key in ('actualDockerOrigins', 'actualOperationalHostOrigins'):
        for name, descriptor in native[key].items():
            add(descriptor, 'NATIVE/' + key + '/' + name, 'currentNativeEvidence')
    preservation = metadata(native['rawPreservation'], 'NATIVE/actualPreservation', 'currentNativeEvidence')
    need(len(preservation['copies']) == 27, 'EXACT27_NATIVE_REPOSITORY_COPIES')
    for index, row in enumerate(preservation['copies']):
        add(row['repositoryCopy'], 'NATIVE/copies/' + str(index) + '/repositoryCopy', 'currentNativeEvidence', 'OPAQUE_PREREQUISITE')
    if preservation['publicBinaryRepositoryCopy'] not in (None, False):
        add(preservation['publicBinaryRepositoryCopy'], 'NATIVE/publicBinaryRepositoryCopy', 'currentNativeEvidence', 'NATIVE')
    eacc = metadata(bindings['acceptedE01Acceptance'], 'E01/acceptance', 'currentE01Evidence', 'nbdp-e01-rebuilt-native-actual-acceptance-v1')
    need(eacc['report'] == bindings['acceptedE01'] and eacc['nativeSha256'] == native_binary['sha256'], 'CURRENT_ACCEPTED_E01_NATIVE_JOIN')
    e01 = metadata(eacc['subject'], 'E01/actualSubject', 'currentE01Evidence')
    for descriptor in eacc['reviews']:
        add(descriptor, 'E01/actualReviews', 'currentE01Evidence')
    named(e01, ['plan', 'release', 'originalToolReceipts', 'inputAfter', 'sourceInventory', 'stdout', 'stderr', 'reportCopy'], 'E01/subject', 'currentE01Evidence')
    epreserve_path = E / 'e01-native-current-replay-20261105/actual/preservation.json'
    epreserve = metadata(pin(epreserve_path), 'E01/currentPreservation', 'currentE01Evidence')
    need(len(epreserve['copies']) == 6, 'EXACT6_E01_COPIES')
    for index, row in enumerate(epreserve['copies']):
        need(set(row) == {'source', 'copy'}, 'E01_COPY_SELECTOR_IS_SEPARATE_TYPED_SCHEMA')
        add(row['copy'], 'E01/copies/' + str(index) + '/copy', 'currentE01Evidence', 'OPAQUE_PREREQUISITE')
    eplan = metadata(e01['plan'], 'E01/plan', 'currentE01Evidence', 'nbdp-e01-isolated-replay-source-plan-v1')
    named(eplan, ['launcher', 'preparationSource', 'historicalComparison', 'inputInventory'], 'E01/plan', 'currentE01Evidence')
    for name, descriptor in eplan['tools'].items():
        add(descriptor, 'E01/tools/' + name, 'currentE01Evidence', 'TOOL')
    # Historical aliases are removed only as live operands. Their exact durable rows remain.
    supersessions = []
    for path, item in removed.items():
        historical = item.get('durableHistoricalSameBytesRow')
        if historical:
            need(historical in retained and retained[historical]['pin']['bytes'] == item['bytes']
                 and retained[historical]['pin']['sha256'] == item['sha256'], 'ORIGINAL_HISTORICAL_BYTES_RETAINED_WITH_OWN_MODE')
            replacement = retained[historical]['pin']
        else:
            replacement = replacements[path]
        supersessions.append(dict(before=all_old[path], observed=item['observed'], replacement=replacement,
            durableHistoricalRow=retained[historical] if historical else None,
            semantics='Only enumerated live alias superseded; historical repository rows keep their original descriptor/mode. No recursive embedded operand lookup.'))
    contributors = put(CAP / 'contributors.json', dict(schema='e02-current-capture-contributors-v1', author=ACTOR,
        authors=sorted(set(doc(BASE / 'code-subject.json')['authors']) | {ACTOR, '/root/helper_apk_binding_scope', TYPE_DESIGNER}),
        inheritedRequiredActors=list(old_const['REQUIRED_KNOWN_ACTORS']), currentRequiredActors=known['knownActors'],
        producerContributors=producer['sourceContributors'], knownActors=known_pin, requestScope=pin(SCOPE),
        noReviewerFabricated=True, unknownHistoricalAuthorship='UNKNOWN', executionAuthorized=False))
    admission_plan = put(CAP / 'admission-plan.json', dict(schema='e02-producer4-capture-admission-plan-v1',
        caseNames=case_names, modelsDefined=len(case_names), source=pin(CAP / 'test_admission.py'), producerSource=producer_pin,
        modelsExecuted=0, scope='PURE_MOCKED_CAPTURE_ADMISSION_ONLY', targetModelsExecuted=0,
        helperExecutions=0, ordinaryRoleExecutions=0, sourceReviewRequired=True, releaseRequired=True))
    contract_sources = []
    for name in ['producer-source-acceptance-contract.json', 'capture-source-acceptance-contract.json',
                 'capture-admission-data-acceptance-contract.json', 'root-clock-source-selection.json',
                 'current-producer-data-acceptance-contract-266.json']:
        contract_sources.append(put(CAP / 'contracts' / name, raw(BASE / 'contracts' / name)))
    contract_sources += [known_pin, put(CAP / 'contracts/root-known-actors.json', raw(known_pin['path']))]
    source_files = [pin(CAP / name) for name in ENGINES + ['input_authority.py']] + contract_sources + [contributors, admission_plan,
        pin(Path(__file__).resolve()), renderer_pin, pin(OUT / 'request_preflight.py'), pin(OUT / 'input_authority.py'),
        pin(OUT / 'admission-additions.fragment'), pin(OUT / 'ready-render-main.fragment'), pin(OUT / 'initial-preparation-failure.json'), pin(OUT / 'pre-type-hardening/preservation-map.json')]
    for descriptor in source_files:
        add(descriptor, 'CURRENT_CAPTURE_CODE_OR_ADMISSION_SOURCE', 'allCaptureCodeAndAdmissionDefinitions', 'SOURCE')
    authors = doc(CAP / 'contributors.json')['authors']
    need(set(authors) | set(producer['sourceContributors']) <= set(known['knownActors']), 'ACTUAL_SOURCE_CREATORS_KNOWN18')
    # Read-site projection names current selectors, never assumes recursive JSON operands.
    projection = dict(
        captureLoadBundle='Named ACK/Root/source/control/config/actor/plan/request/binding authorities; sidecar and pinned baseline explicitly loaded. Dynamic own method/plan/ACK authorities remain external expected_authorities, no hash cycle.',
        captureSnapshots='Every static manifest row is uniformly read_expected streamed before/after each scope; source role never exempts bytes. Existing full SDK434/guard522/Node membership checks unchanged.',
        currentProducerRuntime='Exactly the current producer bindings named11 metadata/artefact fields, fixture/native/E01/oracles/config22 and original19; no build cache/toolchain/private-keystore or arbitrary descriptor recursion.',
        historicalSourceOperands='All2169 retained old rows, old source/test negative metadata and byte-identical historical helper copies remain expected, regardless of whether nested strings look like removed descriptors.',
        clipboardCopies='retainedCopies[*].repositoryCopy only, exactly18. Never source alias, copy or retained field fallback.',
        nativeCopies='preservation.copies[*].repositoryCopy only, exactly27; rawCargoOutput/hardlink path context only.',
        e01Copies='actual preservation copies[*].copy only, exactly6; plan named fields/tools only, no lab inventory descriptor recursion.',
        exclusions='Private key paths, build-result guest/source/privateKeystoreDescriptor, native rawCargoOutput and embedded descriptor-shaped context are never automatically read operands.')
    additional = [seen[path] for path in sorted(seen) if path not in retained]
    authority = put(CAP / 'expected-input-authority.json', dict(schema='e02-producer4-current-expected-input-authority-v1',
        author=ACTOR, scope=pin(SCOPE), forensicPlanningReference=pin(FORENSIC), state='FROZEN_SOURCE_PROPOSAL_REQUIRES_INDEPENDENT_ACCEPTANCE',
        baselineManifest=baseline_pin, baselineRowCount=2175, supersessions=supersessions, retainedRowCount=2169,
        retainedRowsSha256=hashlib.sha256(json.dumps([retained[path] for path in sorted(retained)], sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        additionalRows=additional, projectedRowCountExcludingSelf=len(seen), selfMode=0o600, coverage=coverage,
        typedSelectors=selections, readSiteProjection=projection, wholeInputQualified=False, executionAuthorized=False))
    # Self pin is external to its own JSON, keeping authority/method/manifest acyclic.
    seen[authority['path']] = dict(pin=authority, mode=0o600, role='METADATA_AUTHORITY', origin='CURRENT_FINITE_EXPECTED_INPUT_AUTHORITY')
    coverage = copy.deepcopy(coverage)
    coverage['currentExpectedInputAuthority'] = [authority]
    method_sources = source_files + [authority]
    method = put(CAP / 'code-subject.json', dict(schema='e02-producer4-control-capture-code-subject-v1', authors=authors,
        producerSource=producer_pin, knownActors=known_pin, codeOnly=True, sources=method_sources,
        admissionModelsDefined=len(case_names), admissionModelsExecuted=0, targetModelsExecuted=0,
        helperExecutions=0, ordinaryRoleExecutions=0,
        excludedMutableMetadata=['execution-plan', 'reviews', 'acceptances', 'root-ack', 'runtime-output'],
        sourceReadiness='REQUIRES_FRESH_INDEPENDENT_SOURCE_REVIEW_AND_SEPARATE_ADMISSION_DATA', sourceReady=False,
        expectedInputAuthority=authority, requestPolicyScope=pin(SCOPE), selfApproval=False))
    proofs = [dict(actor=actor, authority=known_pin, selector='/knownActors/' + str(index)) for index, actor in enumerate(known['knownActors'])]
    context = put(CAP / 'actor-context.json', dict(schema='e02-producer4-capture-current-actor-context-v1',
        producerSource=producer_pin, captureSource=method, sourceBirth=lineage_pin,
        participants=list(known['knownActors']), participantProofs=proofs))
    manifest = put(CAP / 'input-manifest.json', dict(schema='e02-producer4-explicit-host-input-manifest-v1',
        producerSource=producer_pin, closedSourceSubjectKeys=sorted(producer), controlPlan=producer['controlPlan'],
        files=[seen[path] for path in sorted(seen)], actualInputCount=len(seen), maximumInputCount=20000,
        requiredCoverage=coverage, fullTrees=baseline['fullTrees'], nodeDependencies=baseline['nodeDependencies'],
        baselineInputAuthority=baseline_pin, currentExpectedInputAuthority=authority,
        scope='EXACT2169_RETAINED_PLUS_TYPED_CURRENT_ADDITIONS_NO_INPUT_QUALIFICATION', baselineDataTransferClaimed=False,
        privateKeysRead=False, opaqueRawMeaning='All rows are uniformly streamed by unchanged guards. Metadata preparation is not whole-input acceptance.'))
    old_plan = doc(BASE / 'execution-plan.json')
    control = doc(producer['controlPlan']['path'], producer['controlPlan'])
    counts = [producer['modelsDefined'][key] for key in old_const['MODEL_KEYS']]
    scopes = []
    for index, group in enumerate(control['selectedGroups']):
        descriptor = group['source']
        scopes.append(dict(scope=group['scope'], source=descriptor,
            argv=[old_plan['tools']['node']['path'], descriptor['path']] if index < 5 else [old_plan['tools']['python']['path'], '-I', '-B', descriptor['path']],
            cwd=group['cwd'], count=group['count'], definitionNames=group['definitionNames'],
            format='EXACT_SELECTED_NODE_JSON' if index < 5 else 'QUIET_UNITTEST_NO_SKIPS'))
    need([row['count'] for row in scopes] == counts == [129, 33, 29, 16, 20, 10, 11, 8, 7, 3], 'EXACT_CURRENT_TEN_GROUP266')
    clock = old_plan['clockSelection']
    plan = put(CAP / 'execution-plan.json', dict(schema='e02-producer4-control-capture-plan-v1', readiness=False,
        producerSource=producer_pin, captureSource=method, inputManifest=manifest, limits=new_const['LIMITS'], deadlineLedger=new_const['LEDGER'],
        scopes=scopes, countsSeparate=counts, tools=old_plan['tools'], outputRoot=None, requiredCoverage=coverage,
        clockSelection=clock, actualSourceReviewPins=accepted['reviews'], captureSourceReviews=None,
        captureSourceAcceptance=None, admissionDataAcceptance=None, rootAcknowledgement=None, scope='SOURCE_PREPARATION_ONLY_NO_EXECUTION_AUTHORITY'))
    argv = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'LC_ALL=C.UTF-8', '/usr/bin/timeout',
        '--signal=KILL', '1203s', old_plan['tools']['python']['path'], '-I', '-B', str(CAP / 'capture.py'), '--execute-once', '--root-ack-sha', '<ACTUAL_ROOT_ACK_SHA256>']
    request = put(CAP / 'request-template.json', dict(cmd=shlex.join(argv), workdir=str(CAP), login=False,
        yield_time_ms=1000, max_output_tokens=2000, **policy))
    binding = put(CAP / 'runtime-bindings.json', dict(schema='e02-producer4-capture-runtime-bindings-v1', readiness=False,
        producerSource=producer_pin, producerAcceptance=acceptance_pin, captureSourceAcceptance=None,
        admissionDataAcceptance=None, rootAcknowledgement=None))
    ack = {key: None for key in old_const['ACK_KEYS'].split()}
    ack.update(schema='e02-producer4-control-capture-root-ack-v1', actor='/root', executionAuthorized=False,
        scope='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY', producerSource=producer_pin,
        producerSourceAcceptance=acceptance_pin, producerReviews=accepted['reviews'], captureSource=method,
        admissionPlan=admission_plan, sourceBirth=lineage_pin, actorContext=context, inputManifest=manifest, plan=plan,
        clockSelection=clock, requestContract=request, runtimeBindings=binding, authors=authors, operators=None, noRetry=True)
    ack_pin = put(CAP / 'root-ack.UNISSUED.json', ack)
    changed_functions = [key for key, value in functions(code_before['capture.py']).items() if value != functions(MEM[CAP / 'capture.py'])[key]]
    need(changed_functions == ['load_bundle', 'validate_bundle'], 'ONLY_NAMED_AUTHORITY_AND_REQUEST_JOIN_FUNCTIONS_CHANGE')
    unchanged_engines = [name for name in ENGINES if MEM[CAP / name] == code_before[name]]
    need(set(unchanged_engines) == {'assemble.py', 'explicit_inputs.py', 'outputs.py', 'request-from-plan.py'}, 'EXACT_FOUR_ENGINE_FILES_BYTE_IDENTICAL')
    diffs = ''.join(line for name in ENGINES if MEM[CAP / name] != code_before[name]
        for line in difflib.unified_diff(code_before[name].decode().splitlines(True), MEM[CAP / name].decode().splitlines(True), fromfile=str(BASE / name), tofile=str(CAP / name)))
    diffs += ''.join(difflib.unified_diff(original_renderer.splitlines(True), renderer.decode().splitlines(True), fromfile=str(OLD_RENDER), tofile=str(OUT / 'render_ready.py')))
    diff_pin = put(OUT / 'source.diff', diffs.encode())
    invariance = put(OUT / 'invariance-and-delta.json', dict(schema='e02-current-capture-source-invariance-and-delta-v1',
        author=ACTOR, baselineManifest=baseline_pin, originalRows=2175, supersededRows=6, retainedRows=2169,
        newUniqueRowsExcludingAuthority=len(additional), authorityRows=1, actualManifestRows=len(seen),
        originalBaselineUnchanged=pin(baseline_pin['path']) == baseline_pin,
        unchangedEngineFiles=unchanged_engines, changedCaptureFunctionAsts=changed_functions,
        unchangedLifecycleFunctionAsts=[key for key in ('signal_owned_group', 'finish_owned', 'capture_scope', 'execute', 'snapshot', 'expected_authorities') if functions(code_before['capture.py'])[key] == functions(MEM[CAP / 'capture.py'])[key]],
        allLimitsIdentical=True, allSdkGuardNodeMembershipsIdentical=True, tenGroupsCounts=counts,
        oldAdmissionNames=old_names, currentAdmissionNames=case_names, old21NamesRetained=True,
        onlyChangedOldTestAssertion='Retained historical test_exact_five_key_direct_and_same_session_original_api now asserts exact7 instead of exact5, as explicitly authorized. Every other old assertion/function body unchanged.',
        newAdmissionDefinitions=len(case_names) - 21, admissionDefined=len(case_names), admissionExecuted=0,
        rendererPredecessor=pin(OLD_RENDER), rendererReadWriteHelperFunctionsAstIdentical=True,
        sourceDiff=diff_pin, actualRequestKeys=request_keys, requestPolicy=policy,
        requestTypeSupplement=pin(TYPE_SCOPE), assertionClarification=pin(ASSERT_SCOPE),
        currentCaptureKnownActorCount=len(known['knownActors']), currentCaptureKnownActorAuthority=known_pin,
        producerKnown17Unchanged=producer_known_pin,
        typeHardening='Strict plain JSON request/poll/terminal types plus whole canonical encoded request equality. Stored original dictionaries/raw metadata remain untouched. Decoder Decimal wall-duration whitelist unchanged.',
        preTypeUnreviewedPacketPreservation=pin(OUT / 'pre-type-hardening/preservation-map.json'),
        wholeInputQualified=False, projectImportsExecuted=False, controlsExecuted=0, sourceReady=False,
        selfApproval=False, currentCaptureSourceAcceptance=None, currentAdmissionDataAcceptance=None, rootAck=None))
    put(OUT / 'README.md', b'''# Current capture SOURCE proposal

SOURCE only. Exact predecessor2175 stays pinned; six enumerated obsolete live aliases are superseded and2169 rows retain their full descriptor/mode/role/origin. Typed finite accepted artifact/native/E01/producer/Root/code additions determine the new total. Whole-input qualification remains false. Never transfer2175/2195/2201 counts or prior266/admission/controller results.

capture/expected-input-authority.json declares the exact projection and read-site coverage; input_authority.py checks it against the pinned predecessor and current manifest without exempting any role. Existing SDK434/guard522/Node membership, uniform streaming, lifecycle/parser engines and480/1200/1203/ten60+3 budgets are unchanged. No arbitrary descriptor recursion, private-key read or cache/toolchain traversal occurs.

Actual requests have exactly seven keys with Root's exact sandbox/justification policy. Plain JSON types and whole canonical encoded request equality reject bool/int/float aliases; poll and terminal API identities/status retain declared types. Original dictionaries/raw records are never modified. The decoder wall-duration-only Decimal restriction remains unchanged. request-from-plan.py stays byte-identical and remains the only actual request materializer. Do not reconstruct/strip/project the JSON or replace the SHA sentinel manually. Equivalent shell argv with an extra quoted SHA still fails exact-request admission. No shell/tty/prefix_rule extension is authorized.

All original21 admission method names remain. The sole authorized old assertion change is exact5 to exact7 in its historical named method; all other original bodies/assertions remain unchanged. New full7/authority cases are definitions only. render_ready.py is a metadata-only successor of the preserved repo ready-r2 renderer with exact original read/write helper lineage. It creates no Data directory, installs no binding or ACK and issues no authority. request_preflight.py is separately releasable synthetic predicate checking only, never an API submitter.

Current source/admission/runtime bindings, output IDs and Root ACK are unissued. Source reviews, fresh admission DATA, concrete whole-input/readiness/actor review and one-use Root ACK precede actual266 capture/assembly/DATA review. All failures and original code remain preserved. E02 PARTIAL22 and all project blockers remain unchanged.

Current capture uses actual Root known18, preserving producer-only known17 unchanged. The later collector-policy diagnosis author is a capture contributor/exclusion. The generated but unreviewed pre-type-hardening packet remains byte-preserved under pre-type-hardening/ with an explicit original-to-preserved mapping. Embedded original-path descriptors there describe that earlier observation only; they are historical context, never current selectors or recursively read operands.
''')
    # Archive every immutable source/metadata member, not referenced operational payloads.
    archive_targets = [path for path in MEM if path.is_relative_to(CAP)] + [OUT / 'render_ready.py', OUT / 'invariance-and-delta.json', OUT / 'source.diff']
    copies = []
    for index, path in enumerate(archive_targets, 1):
        copied = put(OUT / 'source-archive' / ('%03d-' % index + path.name), MEM[path])
        copies.append(dict(original=pin(path), copy=copied))
    entry = put(OUT / 'review-entrypoint.json', dict(schema='e02-current-producer-capture-source-review-entrypoint-v1',
        author=ACTOR, state='FROZEN_SOURCE_ONLY_PENDING_FRESH_INDEPENDENT_QA_SECURITY', rootScope=pin(SCOPE), forensicPlanningReference=pin(FORENSIC),
        producerSource=producer_pin, producerSourceAcceptance=acceptance_pin, producerLineage=lineage_pin, knownActors=known_pin,
        codeSubject=method, expectedInputAuthority=authority, inputManifest=manifest, executionPlan=plan,
        admissionPlan=admission_plan, actualInputCount=len(seen), retainedRows=2169, addedRows=len(additional),
        admissionDefinitions=len(case_names), admissionExecuted=0, producerDefinitions=sum(counts), producerExecuted=0,
        requestContract=request, unissuedAck=ack_pin, readinessRenderer=renderer_pin, requestPreflight=pin(OUT / 'request_preflight.py'),
        diff=diff_pin, invariance=invariance, copies=copies, sourceReady=False, runtimeReady=False, executionAuthorized=False,
        captureSourceAcceptance=None, admissionDataAcceptance=None, concreteRootAck=None, operationalOutputRoot=None,
        helperExecutions=0, ordinaryRoleExecutions=0, wholeInputQualified=False, selfApproval=False,
        manifestPinnedExternally=True, canonicalE02='PARTIAL22_UNCHANGED'))
    authoring = [Path(__file__).resolve(), OUT / 'input_authority.py', OUT / 'request_preflight.py', OUT / 'admission-additions.fragment', OUT / 'ready-render-main.fragment', OUT / 'initial-preparation-failure.json']
    history = sorted(path for path in (OUT / 'pre-type-hardening').rglob('*') if path.is_file())
    packet = put(OUT / 'archive-manifest.json', dict(schema='e02-current-capture-source-packet-manifest-v1', entrypoint=entry,
        files=[pin(path) for path in sorted(MEM)] + [pin(path) for path in authoring + history],
        actualFilesExcludingManifest=len(MEM) + len(authoring) + len(history),
        historicalContextOnlyRoot=str(OUT / 'pre-type-hardening'),
        sourceOnly=True, operationalCopies=0, executionAuthorized=False))
    need(len(MEM) <= 100 and sum(len(value) for value in MEM.values()) <= 16777216, 'FINITE_OWNED_SOURCE_OUTPUT')
    # All metadata derivation finishes before any output write.
    for path in MEM:
        need(not path.exists() and not path.is_symlink(), 'NO_OUTPUT_OVERWRITE')
    for path, value in MEM.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as handle:
            need(handle.write(value) == len(value), 'ONE_EXACT_SOURCE_WRITE')
    print(json.dumps(dict(entrypoint=entry, codeSubject=method, expectedInputAuthority=authority, inputManifest=manifest,
        manifest=packet, retainedRows=2169, addedRows=len(additional), actualInputCount=len(seen), methodSources=len(method_sources),
        admissionDefined=len(case_names), targetDefined=sum(counts), modelsExecuted=0, sourceReady=False)))


if __name__ == '__main__':
    main()
