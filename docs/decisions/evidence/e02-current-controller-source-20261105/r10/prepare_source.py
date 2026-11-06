"""Bounded stdlib-only R10 SOURCE2 preparation, never import/run target modules.

Only NEW R10 Data and repository packet roots are writable. Every source edge
is explicitly selected; no recursive descriptor discovery or runtime grant.
"""
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat

ACTOR = '/root/controller_current_source_r9'
REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE = REPO / 'docs/decisions/evidence'
OUT = EVIDENCE / 'e02-current-controller-source-20261105/r10'
OLD = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r9')
NEW = OLD.with_name('producer4-helper-probe-controller-preparation-r10')
R1 = OLD.with_name('producer4-helper-probe-controller-preparation-r1')
SCOPE = EVIDENCE / 'e02-goal-resume-20261104/controller-source2-r10-root-scope-20261105.json'
QUALIFIER = EVIDENCE / 'e02-collector-current-policy-20261105/source2/source/qualification.py'
COLLECTOR_PLAN = QUALIFIER.parent.parent / 'control-plan.json'
R8_SOURCE_ACCEPTANCE = EVIDENCE / 'e02-probe-controller-r8-source-acceptance-20261029/acceptance.json'
R8_DATA_ACCEPTANCE = EVIDENCE / 'e02-probe-controller-r8-model168-actual-20261029/acceptance.json'
MODEL5_ORIGINAL = EVIDENCE / 'e02-probe-controller-r8-model168-actual-20261029/01-exact-request.json'
PYTHON = '/home/peterhorvath/.miniforge3/bin/python3.13'


def read(path):
    p = Path(path)
    info = p.lstat()
    assert stat.S_ISREG(info.st_mode) and not p.is_symlink() and info.st_size <= 16777216
    raw = p.read_bytes()
    assert len(raw) == info.st_size
    return raw


def pin(path):
    raw = read(path)
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def doc(path):
    return json.loads(read(path))


def put(path, value, raw=False):
    assert path.is_relative_to(NEW) or path.is_relative_to(OUT)
    data = value if raw else (json.dumps(value, indent=2) + '\n').encode()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        assert stream.write(data) == len(data)
    if path.is_relative_to(NEW):
        os.chmod(path, 0o444)
    return pin(path)


def tests(path):
    tree = ast.parse(read(path), filename=str(path))
    return {cls.name + '.' + method.name: ast.dump(method, include_attributes=False)
            for cls in tree.body if isinstance(cls, ast.ClassDef)
            for method in cls.body if isinstance(method, ast.FunctionDef) and method.name.startswith('test_')}


def callables(path):
    tree = ast.parse(read(path), filename=str(path))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            found[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    found[node.name + '.' + child.name] = ast.dump(child, include_attributes=False)
    return found






CONTRACT = '''# SOURCE10: current accepted artifact and typed collector bindings

This is unexecuted SOURCE preparation for E02/Q06/Q07/Q09/Q24. The current
producer SOURCE4 revision CURRENT_ACCEPTED_ARTIFACT_BINDINGS_R1 contains64
source members/22 runtime workers and has accepted fresh266 pure-control DATA.
Collector Source2 and its81 MOCK controls are accepted prerequisites. These
facts release no controller model, helper, lease, account or ordinary role.

The R8 controller.py and exact R1 finite_child.py remain byte-identical.
Host changes only the fixed HERE literal to R10; every Host callable AST is
unchanged. Current test-module loads select R10. Explicit legacy R1/R6 inputs,
failed-run metadata and both operational fixtures retain their original paths.
All174 R9 test names and method ASTs (including168 baseline) remain. Existing six controls cover the
current Source2 qualifier/operational R4 separation, full7/legacy5 boundaries,
Python-equal typed aliases, exact policy/justification and selected source modes.
The complete current partition/N is derived from its final AST, with zero runs.

R9 was held for copying the producer's structured modelsDefined dictionary into\nscalar count fields. Its complete frozen SOURCE and both negative reviews remain\nunchanged. The actual generator boundary now derives plain-int266 only from\nselectedDefinitionCount, checks the strict10-part selectedCountsSeparate and\nactual accepted current266 receipt, and supplies both generated scalar fields.\nNew definitions exercise the same generator helper and generated fields, with\ndictionary/bool/float/count/partition disagreement refusals. No producer map or\nconsumer predicate changes; no174 result transfer.\n\nRoot explicitly selected all eight current producer source modes0664. Their
code bytes equal the R8 guest8. Host still enforces exact declared source modes;
the separate staged copies must remain0600. No accepted producer file is
rewritten or chmodded. Old0444 authority remains historical in R8. Guard522,
descriptor hashes, exact source membership, no-alias checks and all staging
checks remain unchanged.

Lease-composition tests load the exact accepted Source2 qualification.py from
the repository separately from the unchanged operational R4 collector.py.
Synthetic collector requests preserve all7 fields, require_escalated and a
bounded nonblank justification. Synthetic origins are fixtureOnly and never
actual collector registration. The operational Host future family is separately
declared HOST7; its whole request/policy is not passed to Docker argv/env.
Historical HOST5 and actual MODEL5 remain distinct. No universal seven-field
decoder, policy projection or fields stripped from actual originals is allowed.
The old HOST5 skeleton stays historical; the new Host7 skeleton has no cmd,
no plan/release/grant and cannot run. Whole-chain fit remains unproven.

One-sample admission/fixed target ends, fresh later checks, four bare Android
environment removal markers, clean child environment and all SDK/UI forbids
remain. Bootstrap30, nominal target55 including cleanup2, reserve3/envelope58,
target88, cleanup136, postread156, controller180, outer183 and original lease1800
remain exact. The65536 physical slot stays inside metadata8MiB/aggregate16MiB,
with49152 payload/16384 prepaid ledger/64 writes. Final F remains external
platform-only; no physical post-F own-origin/index/status/copy/rescue is allowed.

Finite source/read edges are explicit and deduplicated by whole path. Two
historical operational fixtures remain referenced in place and never copied.
The archive contains source/governance metadata only. All predecessor pins,
current accepted prerequisite pins and exact copies are verified by the bounded
stdlib generator without importing target code or executing model bodies.

Current controller QA/security/source/DATA/concrete/release gates are unissued;
fresh independent post-freeze review and a separate full currentN model release
must precede DATA acceptance. Accepted positive helper DATA is still required
before completion/wrapper implementation. All original Goal criteria remain;
E02 stays PARTIAL22. Q01/Q08/Q13/Q15/Q27, no SDK/deployment/Satflux/NIP/kind/merge
rules are unchanged. This packet is not self-approval or execution authority.
'''


def selected_producer_count(producer, accepted_receipt):
    """One strict count-domain boundary used by generation and future models.

    The caller pins the full current producer and actual accepted Root receipt.
    This method does not authenticate a receipt or grant runtime authority.
    The producer's structured modelsDefined map remains untouched.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(type(producer) is dict and type(accepted_receipt) is dict, 'COUNT_INPUT_OBJECTS')
    count = producer.get('selectedDefinitionCount')
    require(type(count) is int and count == 266, 'PLAIN_INTEGER_SELECTED_PRODUCER266')
    partition = producer.get('selectedCountsSeparate')
    require(type(partition) is list and len(partition) == 10 and
            all(type(value) is int and value > 0 for value in partition),
            'PLAIN_INTEGER_SELECTED_PARTITION')
    require(sum(partition) == count, 'SELECTED_PARTITION_TOTAL_EQUALS_SCALAR')
    accepted_partition = accepted_receipt.get('countsSeparate')
    require(type(accepted_partition) is list and len(accepted_partition) == 10 and
            all(type(value) is int and value > 0 for value in accepted_partition),
            'PLAIN_INTEGER_ACCEPTED_PARTITION')
    require(partition == accepted_partition and sum(accepted_partition) == count,
            'CURRENT_ACCEPTED_PARTITION_EXACT_ORDER_AND_TOTAL')
    for field, expected in (('modelsExecuted', count), ('modelsPassed', count), ('modelsFailed', 0)):
        actual = accepted_receipt.get(field)
        require(type(actual) is int and actual == expected, 'PLAIN_INTEGER_ACCEPTED_' + field)
    return count


COUNT_TESTS = '\n\nclass CurrentProducerCountMetadataControls(unittest.TestCase):\n    """Actual generator metadata boundary; definitions only until Root releases models."""\n    def boundary_and_inputs(self):\n        generator = load(\'current_source2_count_metadata_subject\', Path(\'/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-current-controller-source-20261105/r10/prepare_source.py\'))\n        producer = json.loads(Path(\'/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/subject.json\').read_bytes())\n        receipt = json.loads(Path(\'/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-current-producer266-data-20261105/acceptance.json\').read_bytes())\n        return generator.selected_producer_count, producer, receipt\n\n    def test_actual_generated_constants_and_subject_are_plain266_from_same_boundary(self):\n        boundary, producer, receipt = self.boundary_and_inputs()\n        original_map = copy.deepcopy(producer[\'modelsDefined\'])\n        value = boundary(producer, receipt)\n        self.assertIs(type(value), int)\n        self.assertEqual(value, 266)\n        constants = json.loads((H.HERE / \'constants.json\').read_bytes())\n        subject = json.loads((H.HERE / \'subject.json\').read_bytes())\n        for actual in (constants[\'producerModelsDefined\'], subject[\'upstreamProducerModelsDefined\']):\n            self.assertIs(type(actual), int)\n            self.assertEqual(actual, value)\n        self.assertIs(type(producer[\'modelsDefined\']), dict)\n        self.assertEqual(producer[\'modelsDefined\'], original_map)\n\n    def test_actual_count_boundary_refuses_dictionary_boolean_float_or_disagreeing_scalar(self):\n        boundary, producer, receipt = self.boundary_and_inputs()\n        for bad in (copy.deepcopy(producer[\'modelsDefined\']), True, False, 266.0, \'266\', 265, 267):\n            with self.subTest(value=repr(bad)):\n                altered = copy.deepcopy(producer)\n                altered[\'selectedDefinitionCount\'] = bad\n                with self.assertRaisesRegex(ValueError, \'PLAIN_INTEGER_SELECTED_PRODUCER266\'):\n                    boundary(altered, receipt)\n\n    def test_actual_count_boundary_refuses_partition_container_type_aliases_or_disagreement(self):\n        boundary, producer, receipt = self.boundary_and_inputs()\n        baseline = producer[\'selectedCountsSeparate\']\n        bad_partitions = [dict(enumerate(baseline)), True, 266.0, tuple(baseline), [],\n                          [float(baseline[0]), *baseline[1:]],\n                          [True, *baseline[1:]],\n                          [baseline[0] + 1, *baseline[1:]],\n                          [baseline[1], baseline[0], *baseline[2:]]]\n        for bad in bad_partitions:\n            with self.subTest(value=repr(bad)):\n                altered = copy.deepcopy(producer)\n                altered[\'selectedCountsSeparate\'] = bad\n                with self.assertRaises(ValueError):\n                    boundary(altered, receipt)\n\n    def test_actual_count_boundary_refuses_accepted_receipt_type_aliases_or_count_disagreement(self):\n        boundary, producer, receipt = self.boundary_and_inputs()\n        cases = [(\'modelsExecuted\', {\'count\': 266}), (\'modelsExecuted\', True),\n                 (\'modelsExecuted\', 266.0), (\'modelsPassed\', 265), (\'modelsFailed\', False),\n                 (\'countsSeparate\', dict(enumerate(receipt[\'countsSeparate\']))),\n                 (\'countsSeparate\', True), (\'countsSeparate\', 266.0),\n                 (\'countsSeparate\', [float(receipt[\'countsSeparate\'][0]), *receipt[\'countsSeparate\'][1:]]),\n                 (\'countsSeparate\', [receipt[\'countsSeparate\'][1], receipt[\'countsSeparate\'][0],\n                                     *receipt[\'countsSeparate\'][2:]])]\n        for field, bad in cases:\n            with self.subTest(field=field, value=repr(bad)):\n                altered = copy.deepcopy(receipt)\n                altered[field] = bad\n                with self.assertRaises(ValueError):\n                    boundary(producer, altered)\n'

def main():
    scope = doc(SCOPE)
    assert pin(SCOPE)['sha256'] == '530781445fbfd498347b541d68958c6fc21c7bde769b75c765043f9522c43219'
    assert scope['assignedOwner'] == ACTOR and scope['implementationAuthorized'] is True
    assert scope['modelsAuthorized'] is scope['executionAuthorized'] is False
    assert not NEW.exists() and not NEW.is_symlink()
    before = [pin(p) for p in sorted(OLD.iterdir())]
    assert pin(OLD / 'subject.json') == scope['immutableNegativeR9']
    for key in ('bindingMap', 'modeSelection', 'currentProducerSource', 'currentProducerSourceAcceptance',
                'currentProducer266Data', 'currentProducer266Acceptance', 'currentCollectorSource',
                'currentCollectorSourceAcceptance', 'currentCollector81Acceptance', 'controllerAcceptanceContract'):
        assert pin(Path(scope[key]['path'])) == scope[key]
    old = doc(OLD / 'subject.json')
    negative_disposition = doc(Path(scope['negativeR9Disposition']['path']))
    assert pin(Path(scope['negativeR9Disposition']['path'])) == scope['negativeR9Disposition']
    assert pin(Path(negative_disposition['freeze']['path'])) == negative_disposition['freeze']
    negative_frozen = doc(Path(negative_disposition['freeze']['path']))
    assert len(negative_frozen['inputs']) == 156
    assert all(pin(Path(item['path'])) == item for item in negative_frozen['inputs'])
    assert all(pin(Path(p['path'])) == p for p in old['sources'])
    producer = doc(Path(scope['currentProducerSource']['path']))
    producer_names = {Path(p['path']).name: p for p in producer['sources']}
    collector = doc(Path(scope['currentCollectorSource']['path']))
    collector_source_receipt = doc(Path(scope['currentCollectorSourceAcceptance']['path']))
    collector_data_receipt = doc(Path(scope['currentCollector81Acceptance']['path']))
    producer_data_receipt = doc(Path(scope['currentProducer266Acceptance']['path']))
    producer_count = selected_producer_count(producer, producer_data_receipt)
    constants = doc(OLD / 'constants.json')
    contributors = sorted(set(constants['sourceContributors']) | set(producer['sourceContributors']) |
                          set(collector['sourceContributorUnion']) | {ACTOR, '/root', '/root/helper_apk_binding_scope'})
    contributors = sorted(set(contributors) | {'/root/controller_r9_qa_e7c43daa', '/root/controller_r9_security_e7c43daa'})
    exclusions = sorted(set(scope['reviewerExclusions']) | set(contributors) | {'/root/controller_model_metadata_source2'})
    constants['acceptedProducerSubject'] = scope['currentProducerSource']
    constants['acceptedProducerSourceOnly'] = scope['currentProducerSourceAcceptance']
    constants['source8'] = [producer_names[Path(p['path']).name] for p in constants['source8']]
    constants['sourceModes'] = {Path(p['path']).name: 0o664 for p in constants['source8']}
    constants['sourceContributors'] = contributors
    constants['reviewerExclusions'] = exclusions
    constants['producerSourceRevision'] = 'CURRENT_ACCEPTED_ARTIFACT_BINDINGS_R1'
    constants['producerModelsDefined'] = producer_count
    constants['scope'] = 'CURRENT_SOURCE_ONLY_NO_CONTROLLER_OR_RUNTIME_DATA_TRANSFER'
    NEW.mkdir(mode=0o700)
    constant_pin = put(NEW / 'constants.json', constants)
    owned_code = ['controller.py', 'host.py', 'test_controller.py', 'test_host.py', 'test_raw_tools.py',
                  'test_lease_composition.py', 'test_environment_removal.py', 'test_atomic_target_admission.py']
    for name in owned_code:
        raw = read(OLD / name)
        if name != 'controller.py':
            raw = raw.replace(str(OLD).encode(), str(NEW).encode())
        if name == 'test_host.py':
            text = raw.decode()
            needle = "\n\nif __name__ == '__main__':"
            assert text.count(needle) == 1
            raw = text.replace(needle, COUNT_TESTS + needle).encode()
        ast.parse(raw, filename=str(NEW / name))
        compile(raw, str(NEW / name), 'exec')
        put(NEW / name, raw, raw=True)
    assert read(NEW / 'controller.py') == read(OLD / 'controller.py')
    assert callables(NEW / 'host.py') == callables(OLD / 'host.py')
    contract_pin = put(NEW / 'CONTRACT-R10.md', CONTRACT.encode(), raw=True)
    groups = []
    method_audit = []
    group_paths = [NEW / 'test_controller.py', NEW / 'test_host.py', R1 / 'test_finite_child.py',
                   NEW / 'test_raw_tools.py', NEW / 'test_lease_composition.py',
                   NEW / 'test_environment_removal.py', NEW / 'test_atomic_target_admission.py']
    old_groups = doc(OLD / 'control-plan.json')['groups']
    for old_group, path in zip(old_groups, group_paths):
        previous = tests(Path(old_group['source']['path']))
        current = tests(path)
        assert set(previous) <= set(current)
        assert all(previous[k] == current[k] for k in previous)
        method_audit.append(dict(name=old_group['name'], priorSource=old_group['source'], currentSource=pin(path),
                                 retained=len(previous), added=[k for k in current if k not in previous],
                                 changedPriorMethodASTs=[], removed=[]))
        groups.append(dict(name=path.stem, source=pin(path), format='VERBOSE_UNITTEST_NAMED',
                           argv=[PYTHON, '-I', '-B', str(path)], cwd=str(NEW),
                           count=len(current), expectedNames=list(current)))
    assert sum(x['retained'] for x in method_audit) == 174
    counts = [x['count'] for x in groups]
    fixtures = old['readOnlyOperationalFixtures']
    plan_pin = put(NEW / 'control-plan.json', dict(
        schema='e02-one-cid-helper-probe-controller-controls-v1', version='r10', author=ACTOR,
        contributors=contributors, scope='CURRENT_PRODUCTION_DECISIONS_WITH_SYNTHETIC_MEMORY_PORTS_AND_REFERENCED_LEGACY_FIXTURES',
        groups=groups, groupCount=len(groups), modelsDefined=sum(counts), priorDefinitionCount=174,
        newCurrentBindingDefinitions=sum(counts)-174, modelsExecuted=0, actualControlData=None,
        actualCaptureSource=None, captureRootRelease=None,
        allowedNow='AST_JSON_PREPARATION_ONLY_NO_TARGET_IMPORT_OR_MODEL_EXECUTION',
        readOnlyOperationalFixtures=fixtures, physicalOperationalFixtureCopies=0,
        requestFamily='MODEL5_DISTINCT_FROM_OPERATIONAL_HOST7_AND_COLLECTOR7',
        limits='Synthetic controls only; no real helper/Docker/ordinary qualification.'))
    outer = doc(OLD / 'outer-tokens-skeleton.json')
    outer['tokens'] = [str(NEW / 'host.py') if x == str(OLD / 'host.py') else x for x in outer['tokens']]
    outer_pin = put(NEW / 'outer-tokens-skeleton.json', outer)
    policy_keys = ['cmd', 'workdir', 'login', 'yield_time_ms', 'max_output_tokens', 'sandbox_permissions', 'justification']
    justification = 'Môžem raz vykonať prijatý izolovaný E02 helper probe s aktuálnou jednorazovou Root release, pôvodnými limitmi a úplnou evidenciou? Bez opakovania, SDK a bežných klientov.'
    skeleton = dict(cmd=None, workdir=str(NEW), login=False, yield_time_ms=1000, max_output_tokens=2000,
                    sandbox_permissions='require_escalated', justification=justification)
    host7_pin = put(NEW / 'outer-request7-skeleton.json', skeleton)
    policy_pin = put(NEW / 'outer-request7-policy.json', dict(
        schema='e02-current-controller-operational-host7-request-policy-v1', author=ACTOR,
        requestFamily='HOST7', closedRequestKeys=policy_keys,
        fieldTypes=dict(cmd='str', workdir='str', login='bool_false', yield_time_ms='positive_plain_int',
                        max_output_tokens='positive_plain_int', sandbox_permissions='str', justification='str'),
        exactFields={k: v for k, v in skeleton.items() if k != 'cmd'},
        cmdRule='Only canonical full command derived from current outerTokens plus actual plan/release paths/hashes; no reconstruction of a received actual request.',
        outerTokens=outer_pin, requestSkeleton=host7_pin,
        historicalHost5=pin(R1 / 'outer-request-skeleton.json'),
        separateModelFamily=dict(name='MODEL5', keys=policy_keys[:5], policy='Preserve actual whole default-policy model request; no blanket operational7 extension.'),
        historicalModel5Original=pin(MODEL5_ORIGINAL),
        separateCollectorFamily=dict(name='COLLECTOR7', qualifier=pin(QUALIFIER),
                                     policy='Collector-specific exact current Source2 reader, never a universal Host/model decoder.'),
        policyMetadataNeverEntersDockerArgvOrEnv=True, actualRequest=None,
        actualPlan=None, actualRelease=None, executionAuthorized=False))
    diff_text = ''
    for name in owned_code + ['constants.json']:
        diff_text += ''.join(difflib.unified_diff(read(OLD / name).decode().splitlines(True),
                                                 read(NEW / name).decode().splitlines(True),
                                                 fromfile=str(OLD / name), tofile=str(NEW / name)))
    diff_pin = put(NEW / 'r9-r10-source.diff', diff_text.encode(), raw=True)
    delta_pin = put(NEW / 'delta-proof.json', dict(
        schema='e02-current-controller-r10-explicit-delta-v1', author=ACTOR,
        predecessor=scope['immutableNegativeR9'], rootScope=pin(SCOPE), modeSelection=scope['modeSelection'],
        hostCallableASTsUnchanged=True, hostTopLevelOnlyChange='HERE literal r9 to r10',
        controllerCoreByteIdentical=True, unchangedFiniteChild=pin(R1 / 'finite_child.py'),
        all174PriorMethodsASTIdentical=True, all168BaselineMethodsRetained=True, testMethodAudit=method_audit,
        sourceModesDelta=dict(historicalExpected='0444', selectedCurrent='0664', stagedUnchanged='0600',
                              authority=scope['modeSelection'], acceptedProducerChmodded=False),
        currentQualifier=pin(QUALIFIER), operationalCollector=pin(Path(collector['operationalCollector']['path'])) if 'operationalCollector' in collector else pin(Path('/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r4/collector.py')),
        requestFamilies=['MODEL5', 'HOST7', 'COLLECTOR7'],
        originalClocksResourcesIsolationAccountingCleanupUnchanged=True,
        operationalFixturesCopied=0, modelsDefined=sum(counts), modelsExecuted=0, executionAuthorized=False))
    preservation_pin = put(NEW / 'preservation.json', dict(
        schema='e02-current-controller-r10-predecessor-preservation-v1', author=ACTOR,
        predecessor=scope['immutableNegativeR9'], predecessorFiles=before,
        predecessorSourceInputs=old['sources'], allPredecessorPinsUnchanged=True,
        negativePredecessorFreeze=negative_disposition['freeze'], negativeFrozenPinsUnchanged=156,
        historicalInPlaceAuthorityInputs=old['inPlaceBindingAuthorityInputs'],
        currentProducerData=scope['currentProducer266Data'], currentProducerDataAcceptance=scope['currentProducer266Acceptance'],
        currentCollector81Acceptance=scope['currentCollector81Acceptance'],
        readOnlyOperationalFixtures=fixtures, physicalOperationalFixtureCopies=0,
        prior168DataTransferred=False, prior174DataTransferred=False, priorCollector50DataTransferred=False,
        acceptedSourcesChanged=False, executionAuthorized=False))
    prerequisites = [SCOPE] + [Path(scope[k]['path']) for k in (
        'bindingMap', 'modeSelection', 'currentProducerSource', 'currentProducerSourceAcceptance',
        'currentProducer266Data', 'currentProducer266Acceptance', 'currentCollectorSource',
        'currentCollectorSourceAcceptance', 'currentCollector81Acceptance', 'controllerAcceptanceContract')]
    # Named accepted peer operands only, never recursively walk JSON pins.
    prerequisites += [Path(collector_data_receipt['subject']['path']),
                      COLLECTOR_PLAN, QUALIFIER,
                      QUALIFIER.with_name('history_prefix.py'), QUALIFIER.with_name('codec.py')]
    for receipt in (collector_source_receipt, collector_data_receipt, producer_data_receipt):
        prerequisites += [Path(x['path']) for x in receipt['reviews']]
    prerequisites += [Path(old['predecessorSourceAcceptance']['path']), OLD / 'subject.json',
                      R8_SOURCE_ACCEPTANCE, R8_DATA_ACCEPTANCE, MODEL5_ORIGINAL]
    prerequisites += [Path(scope['negativeR9Disposition']['path']), Path(scope['predecessorScope']['path']),
                      *[Path(x['path']) for x in scope['negativeR9Reviews']],
                      *[Path(x['path']) for x in scope['negativeR9Findings']]]
    negative_disposition = doc(Path(scope['negativeR9Disposition']['path']))
    prerequisites += [Path(negative_disposition['freeze']['path']), OUT / 'write_source2_generator.py']
    external_edges = [pin(p) for p in sorted(set(prerequisites))]
    read_map_pin = put(NEW / 'read-map.json', dict(
        schema='e02-current-controller-r10-finite-read-map-v1', author=ACTOR,
        generator=pin(OUT / 'prepare_source.py'),
        runtimeReads=dict(hostBootstrap='Exact current plan/release/subject/constants/runtime3 and explicitly named gates; original Host behavior unchanged.',
                          guestSources=constants['source8'], guardManifest='Original exact guard522 and332736-byte manifest checks unchanged.'),
        currentTestImports=dict(host=pin(NEW / 'host.py'), controller=pin(NEW / 'controller.py'),
                                qualifier=pin(QUALIFIER), operationalCollector=pin(Path('/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r4/collector.py'))),
        explicitlySelectedPrerequisiteMetadata=external_edges,
        historicalFixturesReferencedOnly=fixtures,
        scalarCountBoundary=dict(source=pin(OUT / 'prepare_source.py'), callable='selected_producer_count',
                                 selectedCountOperand='producer.selectedDefinitionCount',
                                 selectedPartitionOperand='producer.selectedCountsSeparate',
                                 acceptedCountOperand='current accepted Root266 receipt',
                                 tests='CurrentProducerCountMetadataControls uses the same actual function; definitions unexecuted'),
        negativePredecessor=scope['immutableNegativeR9'], negativeDisposition=scope['negativeR9Disposition'],
        recursionPolicy='No recursive descriptor/JSON/source-tree discovery; source paths are a finite explicit old-membership replacement map plus named additions.',
        countsPolicy='Unique whole absolute path membership and final AST names/groups only.',
        historicalRequestFamiliesRemainDistinct=True, targetImports=0, modelsExecuted=0,
        executionAuthorized=False))
    static_pin = put(NEW / 'static-preparation.json', dict(
        schema='e02-current-controller-r10-static-preparation-v1', author=ACTOR,
        sourceAst=[dict(source=pin(NEW / name), result='PARSED_COMPILED_NO_EVALUATION') for name in owned_code],
        currentDefinitionCounts=counts, modelsDefined=sum(counts), priorDefinitionsRetained=174,
        selectedUpstreamProducerCount=producer_count, selectedUpstreamProducerCountType='PLAIN_INT',
        originalHostCallableASTsUnchanged=True, controllerCoreByteIdentical=True,
        currentSourceModes='0664_EXACT_ROOT_SELECTED', stagedSourceModes='0600_UNCHANGED',
        generator=pin(OUT / 'prepare_source.py'), allPredecessorPinsVerified=True,
        targetImports=0, modelsExecuted=0, helperExecutions=0, dockerExecutions=0,
        collectorCommandsExecuted=0, roleExecutions=0, syntaxIsRuntimeEvidence=False,
        operationalFixtureCopies=0, executionAuthorized=False))
    replacements = {str(OLD / name): NEW / name for name in owned_code + [
        'constants.json', 'control-plan.json', 'outer-tokens-skeleton.json',
        'delta-proof.json', 'preservation.json', 'static-preparation.json',
        'read-map.json', 'outer-request7-policy.json', 'outer-request7-skeleton.json']}
    replacements[str(OLD / 'CONTRACT-R9.md')] = NEW / 'CONTRACT-R10.md'
    replacements[str(OLD / 'r8-r9-source.diff')] = NEW / 'r9-r10-source.diff'
    replacements[str(Path('/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r4/qualification.py'))] = QUALIFIER
    old_guest_names = {Path(x['path']).name for x in old['guestProbeSources']}
    for item in old['guestProbeSources']:
        replacements[item['path']] = Path(producer_names[Path(item['path']).name]['path'])
    replacements[str(OUT.parent / 'r9/prepare_source.py')] = OUT / 'prepare_source.py'
    selected = {str(replacements.get(x['path'], Path(x['path']))): replacements.get(x['path'], Path(x['path'])) for x in old['sources']}
    additions = [NEW / 'read-map.json', NEW / 'outer-request7-policy.json', NEW / 'outer-request7-skeleton.json',
                 OUT / 'prepare_source.py', *prerequisites]
    for path in additions:
        selected[str(path)] = path
    source_pins = [pin(selected[key]) for key in sorted(selected)]
    fixture_paths = {p['path'] for p in fixtures}
    assert fixture_paths <= set(selected)
    declared_source_count = len(source_pins) - len(fixtures)
    assert all(Path(x['path']).name in old_guest_names for x in constants['source8'])
    support = [pin(QUALIFIER) if x['path'].endswith('/probe-root-custody-collector-preparation-r4/qualification.py') else x for x in old['testSupportSources']]
    subject = copy.deepcopy(old)
    subject.update(
        author=ACTOR, sourceContributors=contributors, sourcePreparationOperators=[ACTOR], operators=[],
        state='FROZEN_SOURCE10_CURRENT_ACCEPTED_ARTIFACT_TYPED_COLLECTOR_AND_SCALAR_COUNT_CORRECTION_PENDING_INDEPENDENT_REVIEW',
        version='r10', sourceRevision='CURRENT_ACCEPTED_ARTIFACT_TYPED_REQUEST7_SCALAR266_BINDINGS_R2',
        runtimeSources=[pin(NEW / 'controller.py'), pin(NEW / 'host.py'), pin(R1 / 'finite_child.py')],
        guestProbeSources=constants['source8'], constants=constant_pin,
        upstreamProducerSubject=scope['currentProducerSource'],
        upstreamProducerSourceAcceptance=scope['currentProducerSourceAcceptance'],
        upstreamProducerSourceRevision='CURRENT_ACCEPTED_ARTIFACT_BINDINGS_R1',
        upstreamProducerSourceMemberCount=producer['sourceCount'], upstreamProducerRuntimeWorkerCount=22,
        upstreamProducerModelsDefined=producer_count,
        currentProducerPureDataAcceptance=scope['currentProducer266Acceptance'],
        currentProducerPureDataSubject=scope['currentProducer266Data'],
        knownCollectorSource=scope['currentCollectorSource'],
        currentCollectorSourceAcceptance=scope['currentCollectorSourceAcceptance'],
        currentCollector81DataAcceptance=scope['currentCollector81Acceptance'],
        currentCollector81DataSubject=collector_data_receipt['subject'],
        currentCollectorControlPlan=pin(COLLECTOR_PLAN), currentCollectorQualifier=pin(QUALIFIER),
        controlPlan=plan_pin, contract=contract_pin, deltaProof=delta_pin, sourceDiff=diff_pin,
        preservation=preservation_pin, staticPreparation=static_pin, readMap=read_map_pin,
        rootScope=pin(SCOPE), currentSourceModeAuthority=scope['modeSelection'],
        operationalHostRequestPolicy=policy_pin, operationalHostRequestSkeleton=host7_pin,
        outerTokensSkeleton=outer_pin, sources=source_pins, sourceCount=len(source_pins),
        declaredSourceMemberCount=declared_source_count, readOnlyOperationalFixtureMemberCount=len(fixtures),
        sourceMembershipPolicy='Finite unique whole-path closure: current SOURCE/governance/prerequisite metadata plus2 explicitly referenced operational fixtures; fixtures excluded from physical copies. Exact counts derive this final membership.',
        modelsDefined=sum(counts), modelGroups=len(groups), modelsExecuted=0,
        predecessorSubject=scope['immutableNegativeR9'],
        predecessorSourceAcceptance=None, negativePredecessor=scope['immutableNegativeR9'],
        negativePredecessorDisposition=scope['negativeR9Disposition'],
        acceptedSourceBaseline=scope['immutablePredecessor'], acceptedSourceBaselineAcceptance=pin(R8_SOURCE_ACCEPTANCE),
        historicalAcceptedPredecessorR8ControlData=pin(R8_DATA_ACCEPTANCE),
        historicalPredecessorInPlaceAuthorityInputs=old['inPlaceBindingAuthorityInputs'],
        inPlaceBindingAuthorityInputs=external_edges,
        testSupportSources=support, testSupportSourceCount=len(support),
        reviewerExclusions=exclusions, currentControllerSourceQa=None, currentControllerSourceSecurity=None,
        currentControllerControlDataAcceptance=None, currentConcreteInputAcceptance=None,
        concreteRootRelease=None, finalMethodBindings=copy.deepcopy(old['finalMethodBindings']), readiness=False, runtimeReady=False,
        executionAuthorized=False, rootGrantIssued=False, selfApproval=False, sourceAccepted=False,
        all174PriorDefinitionNamesAndMethodBodiesRetained=True, all168PriorDefinitionNamesAndMethodBodiesRetained=True, prior168DataTransferred=False, prior174DataTransferred=False,
        newCurrentBindingDefinitions=sum(counts)-174, bindingOnlySuccessor=False,
        productionCodeChanged=True, productionCallableASTsChanged=False,
        productionBindingChanged=True, currentCollectorTyped81TransferredAsControllerData=False,
        scalarCountBoundary=dict(generator=pin(OUT / 'prepare_source.py'), callable='selected_producer_count',
                                 selectedScalar=producer_count, structuredProducerMapChanged=False),
        conservativeCurrentMetadataMethodExclusion=dict(actor='/root/controller_model_metadata_source2',
            reason='Separately owned current Root metadata-method author excluded conservatively, not relabeled as this SOURCE writer.'),
        remainingGates=['Fresh independent currentR10 SOURCE QA/security outside complete creator/design/operator union',
                        'Separate complete current AST-derived N model release/current input snapshots/full genuine MODEL5 custody and independent DATA acceptance',
                        'Current helper method/renderer/consumer contracts/full65536 slot fit and exact current inputs/concrete independent reviews',
                        'Fresh original lease/account/one-use helper release and independently accepted actual positive helper DATA',
                        'Original ordinary-role/five-export/full-consumption/primary22/integration/PR criteria remain'])
    subject_pin = put(NEW / 'subject.json', subject)
    copies = []
    for index, item in enumerate([*source_pins, subject_pin], 1):
        if item['path'] in fixture_paths:
            continue
        source = Path(item['path'])
        destination = OUT / 'source-archive' / ('%03d-' % index + source.name)
        copy_pin = put(destination, read(source), raw=True)
        assert copy_pin['bytes'] == item['bytes'] and copy_pin['sha256'] == item['sha256']
        copies.append(dict(source=item, repositoryCopy=copy_pin))
    archive_pin = put(OUT / 'archive.json', dict(
        schema='e02-current-controller-r10-exact-source-archive-v1', author=ACTOR,
        copies=copies, originalSubject=subject_pin, originalSourceMembers=len(source_pins),
        declaredSourceMembers=declared_source_count, operationalFixturesReferencedOnly=fixtures,
        physicalOperationalFixtureCopies=0, originalPinsNotRebound=True,
        copiedFiles=len(copies), copiedBytes=sum(x['source']['bytes'] for x in copies),
        modelsExecuted=0, executionAuthorized=False))
    entry = dict(schema='e02-current-controller-r10-source-review-entrypoint-v1', author=ACTOR,
                 subject=subject_pin, archive=archive_pin, rootScope=pin(SCOPE), bindingMap=scope['bindingMap'],
                 modeSelection=scope['modeSelection'], currentProducerDataAcceptance=scope['currentProducer266Acceptance'],
                 currentCollectorSourceAcceptance=scope['currentCollectorSourceAcceptance'],
                 currentCollector81Acceptance=scope['currentCollector81Acceptance'],
                 deltaProof=delta_pin, sourceDiff=diff_pin, preservation=preservation_pin, readMap=read_map_pin,
                 controlPlan=plan_pin, acceptanceContract=scope['controllerAcceptanceContract'],
                 sourceMembers=len(source_pins), declaredSourceMembers=declared_source_count,
                 operationalFixtures=len(fixtures), operationalFixtureCopies=0,
                 runtimeSources=3, guestProbeSources=8, modelGroups=len(groups), countsSeparate=counts,
                 modelsDefined=sum(counts), priorNamesAndASTsRetained=174, newDefinitions=sum(counts)-174,
                 modelsExecuted=0, targetImports=0, collectorCommandsExecuted=0, helperExecutions=0,
                 dockerExecutions=0, ordinaryRoleExecutions=0, sourceContributors=contributors,
                 reviewerExclusions=exclusions, reviewCopies=len(copies), sourceAccepted=False,
                 independentReviews=None, readiness=False, executionAuthorized=False)
    entry_pin = put(OUT / 'review-entrypoint.json', entry)
    assert all(pin(Path(x['path'])) == x for x in before)
    assert all(pin(Path(x['path'])) == x for x in old['sources'])
    assert all(pin(Path(x['path'])) == x for x in source_pins)
    assert all(pin(Path(item['path'])) == item for item in negative_frozen['inputs'])
    for path in NEW.iterdir():
        if path.suffix == '.json':
            doc(path)
        elif path.suffix == '.py':
            ast.parse(read(path), filename=str(path))
            compile(read(path), str(path), 'exec')
    print(json.dumps(dict(entrypoint=entry_pin, subject=subject_pin, archive=archive_pin,
                          sourceMembers=len(source_pins), declaredSourceMembers=declared_source_count,
                          countsSeparate=counts, modelsDefined=sum(counts), modelsExecuted=0,
                          reviewCopies=len(copies), excludedActors=len(exclusions),
                          hostCallableASTsUnchanged=True, coreByteIdentical=True,
                          all174PriorTestMethodASTsRetained=True)))


if __name__ == '__main__':
    main()
