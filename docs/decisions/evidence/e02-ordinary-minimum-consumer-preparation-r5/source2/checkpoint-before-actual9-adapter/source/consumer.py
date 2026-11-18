"""Standalone minimum ordinary-client evidence consumer; never canonical E02 PASS.

Invocation reads only bounded explicitly pinned DATA. It does not execute a
producer, SDK, Android, crypto, network, subprocess, tests or evidence payloads.
"""
import argparse
import hashlib
import ipaddress
from pathlib import Path
import re
import stat
import sys

# Direct-script execution under -I is supported without trusting cwd/PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from strict import Files, I64, Refusal, closed, equal, hx, integer, json_bytes, need, pin_shape, same, text
import gui
import wire
import observer
from witness import Origin, actors, cleanup_check, commands, lease_check, ownership

PRODUCER_SHA = '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'
CONTRACT_SHA = '7fd7b71898584b4b9f90fbe9ae4601df0d1b9f3dfdc995012dfd63824fba9bfc'
ADOPTION_SHA = '2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287'
RUNTIME_SCOPE = 'E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY'
DRAFT_FINAL_ADAPTER_READY = False
CURRENT_PRODUCER_SCHEMA = 'e02-ordinary-minimum-producer3-source-subject-v1'
CURRENT_PRODUCER = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/subject.json', 'bytes': 12116, 'sha256': '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'}
CURRENT_SOURCE_PACKET = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/source-packet.json', 'bytes': 15807, 'sha256': 'bd2e2e330984fe739045f2259e38b66a64fe6074d222b6dcd1d8d244c9b3fe46'}
CURRENT_SOURCE_PLAN = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/control-plan.json', 'bytes': 5183, 'sha256': 'cf0351831f88dff7685bc53cd8977962526529b65bf13aeb740ef7c7ba0487d6'}
CURRENT_SOURCE_INPUTS = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/source-input-manifest.json', 'bytes': 870396, 'sha256': 'c9c80039e0af9af4124c00bc87d42a94fcfa2dfa0e8216187b5404856e473ddc'}
CURRENT_AMETHYST_APK = {'path': '/Data/nbdp-e02-tooling-20261027/amethyst-build-r8/output/build/rebuilt-fdroid-debug-0.apk', 'bytes': 165860063, 'sha256': '368255b938e8fc72bf603a3f08dee29938e6c73e43ca6471a13ee1bc9ee0b4be'}
CURRENT_HELPER_APK = {'path': '/tmp/nbdp-e02-clipboard-helper-rebuild-20261027/build-r2/clipboard-capture.apk', 'bytes': 16787, 'sha256': '589031766a4be1cbd4e6a93b1b8d8af5db616d8dc51bcc7dd408a7f0a954b73e'}
CURRENT_ARTIFACT_BINDINGS = {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/rebuilt-artifact-bindings.json', 'bytes': 5086, 'sha256': '778a136c5eaf6ca15fc61d1b3c3ff1368648faa40761506762c0d901f4ba1071'}
CURRENT_CONFIGURATIONS = [{'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/incoming-run-config.json', 'bytes': 5596, 'sha256': 'cec7ee4aa2701eb8430434345454526bbcdfd35d2fe500e8b766db52939f3023'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/archive-run-config.json', 'bytes': 5594, 'sha256': '171e59d0b76050e8e4cde0ab1252dcdae93763d2aaf880e875025eb126131052'}]
CURRENT_WORKERS = [{'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/supervisor.py', 'bytes': 50396, 'sha256': 'aaafa4856ad7f84163271bdada6824289fed40c1f68f64ae86f4cd0d2f2aa665'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/lease_guard.py', 'bytes': 14846, 'sha256': 'd396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/android_driver.py', 'bytes': 49018, 'sha256': '0ee6b53f8ac2d8e5e12af8acc57cf30e47c030589eb617b3c0d2f405e52518af'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/ui-plan.json', 'bytes': 1482, 'sha256': 'd5bcb4f3fd8e13ce919181a406af9f5c5f05953bcb1056e9075883ce1604e5b8'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/fixture.mjs', 'bytes': 34130, 'sha256': '041d980db40f2c22f2e231303ff89ed5be59dedae90bb278e891304246a74746'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/fixture-plan.json', 'bytes': 251444, 'sha256': '71e3716fe6cffa6c02c69149ece20b18816eb49fe51ee380bedfa356103f7917'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/minimum-plan.json', 'bytes': 1562, 'sha256': '6b348f638d6afd934ce858e9a1eb862c02e2e80a00773bc2d21613d4743cab78'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/business-rumor.json', 'bytes': 910, 'sha256': '8bb0efcf8cc5a503e8f653885503958520f1a069066e549cd60dec7128d25291'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/chat-rumor.json', 'bytes': 384, 'sha256': 'f796df4b3ad76f832248fb60bdfb0d134a830257e95c0559b44d4fce0a900dc5'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/exchange.mjs', 'bytes': 5446, 'sha256': '1951d91b9d02e3ca2250fd19367748bc42d04ae724f0e8cbf862d2404dfaec80'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/phase-writer.mjs', 'bytes': 2085, 'sha256': 'bcfb3338d1ab8cbb20709f6add09a2e7be01a270f48271112e3aa3a76743cead'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/dependency-tree.mjs', 'bytes': 2842, 'sha256': '0b574a14e591abc1908f4733908001d8ea1ab5698da8991e618ca26714eeded3'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/dependency-tree.json', 'bytes': 35599, 'sha256': '0536b9b0f6a127e3e43fd19bf5df0e3110b5c437e1a2c22c76e1a3e8dcc4f07f'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/capture-budget.mjs', 'bytes': 3474, 'sha256': '6d3ba9a24716e9f770cbfc5933454854eb4dd6530f7c886026f418e7f971c1f1'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/exchange-adapter.mjs', 'bytes': 1509, 'sha256': '69e0e8ab2c48dd7c682948fb8633fd024ff29e6c1b9af9f8fbedde2a9c7b6546'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/proxy-observer.mjs', 'bytes': 1045, 'sha256': 'da8c393eff510c4859bea02f3ad222178a89529bb1d3b02c1667815324a45a52'}]
CURRENT_CAPTURE_BINDINGS = {'capture-a': {'producerSource': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/subject.json', 'bytes': 12116, 'sha256': '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'}, 'testSource': [{'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/test_observation_model.mjs', 'bytes': 11018, 'sha256': 'd35a4736d44ebddbf8b733eb82e457ea1d4482078b7316e90938f2612cbb68bb'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/test_public_identity_metadata.py', 'bytes': 4489, 'sha256': 'd1b070b79b5673c0f05fbe3c75a70c5739de8cdb06e38183fe99c7a872d66ff4'}, {'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/test_producer2_source.py', 'bytes': 4999, 'sha256': 'd5d2aa047e1832d34e991c0ca073ff63abb10930e161972d04e202a9576a0b1e'}], 'inputClosure': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3/capture-a/frozen-inputs.json', 'bytes': 755058, 'sha256': '3d3b9f2e9446a40036e4fc3999c504f7b39bdc0de390bf572fb1ffa3a03a7aed'}, 'plan': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3/capture-a/control-plan.json', 'bytes': 7100, 'sha256': '9ac32b48c2f8d95d5508d76f01451b820993e58ad84b59148543c53a681208f7'}, 'release': None, 'capture': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3/subject.json', 'bytes': 7081, 'sha256': 'e103370b6e1f9b6e2f1a133f9c7653cb29612a04b02f7f4f3032d16b9f424c1e'}, 'originalToolResponses': None, 'result': None, 'acceptance': None, 'qaReview': None, 'securityReview': None, 'admissionModelAcceptance': None, 'upstreamRootACK': None}, 'capture-b': {'producerSource': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/subject.json', 'bytes': 12116, 'sha256': '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'}, 'testSource': [{'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3/test_producer3_bindings.py', 'bytes': 15095, 'sha256': 'd6747f408d455fa657b435bd5305378a1ea536d17baa125f4dbdc4089421a589'}], 'inputClosure': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3/capture-b/frozen-inputs.json', 'bytes': 755058, 'sha256': '3d3b9f2e9446a40036e4fc3999c504f7b39bdc0de390bf572fb1ffa3a03a7aed'}, 'plan': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3/capture-b/control-plan.json', 'bytes': 4375, 'sha256': '9274e48cae49b51f85501f506daa07da1bb40fb409724037214caa22e2a80cfc'}, 'release': None, 'capture': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3/subject.json', 'bytes': 7081, 'sha256': 'e103370b6e1f9b6e2f1a133f9c7653cb29612a04b02f7f4f3032d16b9f424c1e'}, 'originalToolResponses': None, 'result': None, 'acceptance': None, 'qaReview': None, 'securityReview': None, 'admissionModelAcceptance': None, 'upstreamRootACK': None}}
CURRENT_AUTHORITY_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-data-contract-20261028/contract.json', 'bytes': 7195, 'sha256': '441165a0212a6e806c03790b61a3135451ab76477b6a685d234207b8a264a10d'}
CURRENT_CONTROL_ACTORS = None
CURRENT_ADMISSION_MODEL_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-data-contract-20261028/model-subject-contract.json', 'bytes': 3852, 'sha256': '4ffaab275275a8782b5cc3a82a84087f5541f1c9b8b7b8e026f23a96caed6367'}
CURRENT_SOURCE_CAPTURE_DECISIONS = {'source': {'qa': 'ACCEPT_PRODUCER3_SOURCE_FOR_FRESH35_AND_SEPARATE3_CONTROLS_ONLY', 'security': 'ACCEPT_FINAL_PRODUCER3_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'}, 'capture': {'qa': 'ACCEPT_PRODUCER3_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY', 'security': 'ACCEPT_PRODUCER3_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY'}}
CURRENT_EXPERIMENT_REPOSITORY = '/home/peterhorvath/apps/bitcoin/NBDP'
CURRENT_READ_TREE_ROOTS = [('/tmp/nbdp-e02-api35-fixture-r2/sdk', 434), ('/tmp/nbdp-e02-minimal-rs-v7/guard-python', 522)]

CONFIG_KEYS = 'runtimeImage relayImage sdkRoot amethystApk helperApk schema scope profileId ordinaryRole windowId account peer runId originalLeaseSeconds sourceAndDependencyPins sdkInventory guardBundleInventory guardBundleRoot relayConfig state canonicalE02'
WINDOW_KEYS = 'schema profileId ordinaryRole windowId runId outputRoot authors operators sourceSubject supervisorSource runConfig runRelease resource sourceControls outer lease driver supervisor commands ui proxy phase readOnlyMountBindings graphFiles excludedFiles sourcePolicyObservations'
DRIVER_KEYS = 'schema profileId windowId ordinaryRole runId runConfig runRelease executionState accountIdentityGUI expectedAccountPubkey accountIdentityQualification torConfigurationGUI environmentAnrEvidence allUICaptures fixtureCalls observations limits canonicalE02Changed'
OBS_KEYS = 'id state selection uiPng uiXml rawClientRumor clipboardClear visibleMatchingTextNodeCount duplicateObservation expectedRumor publication actualNewAppFrameObserved originalGuestToHostBindings subscriptionStatus subscriptionStatusReply subscriptionStatusCall subscriptionStatusCommand custodySegment'


def require_current_source_profile():
    """Known source pins alone never activate pending actual control authority."""
    need(DRAFT_FINAL_ADAPTER_READY is True, 'CONSUMER5_SOURCE2_NULL_NOT_READY_REQUIRES_CURRENT_DATA')
    need(CURRENT_AUTHORITY_CONTRACT is not None and CURRENT_CONTROL_ACTORS is not None
         and CURRENT_ADMISSION_MODEL_CONTRACT is not None, 'CURRENT_API_ACCEPTANCE_ACTORS_AND_CONTRACT_REQUIRED')
    need(all(value is not None for nodes in CURRENT_CAPTURE_BINDINGS.values() for value in nodes.values()),
         'ALL_A_B_CAPTURE_SOURCE_INPUT_PLAN_ROOT_RELEASE_TOOL_RESULT_INDEPENDENT_ACCEPTANCE_REQUIRED')


def external(files, path, sha):
    hx(sha)
    p = Path(path)
    descriptor = dict(path=str(p), bytes=p.stat().st_size, sha256=sha)
    files.read(descriptor)
    return descriptor


def provenance(files, candidate, history, origin_value):
    forbidden = actors(candidate['authors']) | actors(candidate['operators'])
    need(type(history['attempts']) is list and 2 <= len(history['attempts']) <= 128, 'WHOLE_ATTEMPT_HISTORY_BOUND')
    equal([a['subject'] for a in history['attempts']], origin_value['attemptSubjects'], 'EXTERNALLY_CLOSED_ATTEMPT_INVENTORY')
    equal(history['legacyContexts'], origin_value['legacyContexts'], 'LEGACY_HISTORY_OMISSION')
    attempt_docs, seen = [], set()
    for row in history['attempts']:
        closed(row, 'subject disposition classification reason')
        need(row['disposition'] in ('CONTRIBUTE_WHOLE_WINDOW', 'NO_CONTRIBUTION'), 'ATTEMPT_DISPOSITION')
        text(row['classification'], 128); text(row['reason'], 8192)
        attempt = files.doc(row['subject'])
        closed(attempt, 'schema profileId attemptId ordinaryRole runId windowSubject rawOutcome authors operators sourceSubject outcomeClassification')
        equal(attempt['schema'], 'e02-minimum-attempt-subject-v1'); equal(attempt['profileId'], wire.PROFILE)
        need(attempt['attemptId'] not in seen, 'DUPLICATE_HISTORY_ATTEMPT'); seen.add(attempt['attemptId'])
        need(attempt['ordinaryRole'] in wire.STAGES, 'ATTEMPT_ROLE')
        need(re.fullmatch('[0-9a-f]{32}', attempt['runId']), 'ATTEMPT_RUNID')
        forbidden |= actors(attempt['authors']) | actors(attempt['operators'])
        files.read(attempt['rawOutcome']); files.read(attempt['sourceSubject'])
        equal(row['classification'], attempt['outcomeClassification'])
        if row['disposition'] == 'CONTRIBUTE_WHOLE_WINDOW':
            need(attempt['windowSubject'] is not None and row['classification'] == 'COMPLETE_PENDING_INDEPENDENT_QUALIFICATION', 'FAILED_WINDOW_CANNOT_DONATE_ROWS')
        else:
            need(attempt['windowSubject'] is None, 'EXCLUDED_ATTEMPT_CANNOT_DONATE_WINDOW')
        attempt_docs.append((row, attempt))
    # Legacy packages are context only; all relevant authors/operators remain in
    # the union, including failed runs and consumer/control/source authors.
    for legacy in history['legacyContexts']:
        closed(legacy, 'subject authors operators meaning')
        forbidden |= actors(legacy['authors']) | actors(legacy['operators'])
        equal(legacy['meaning'], 'HISTORICAL_CONTEXT_NO_ROW_DONATION')
        files.read(legacy['subject'])
    return forbidden, attempt_docs


def current_producer(files, descriptor):
    equal(descriptor, CURRENT_PRODUCER, 'EXACT_CURRENT_PRODUCER_SOURCE2')
    producer = files.doc(descriptor)
    equal(producer['schema'], CURRENT_PRODUCER_SCHEMA)
    equal(producer['typedContract']['sha256'], CONTRACT_SHA)
    equal(producer['controlPlan'], CURRENT_SOURCE_PLAN)
    equal(producer['sourceDataInputClosure'], CURRENT_SOURCE_INPUTS)
    equal(producer['configurations'], CURRENT_CONFIGURATIONS)
    equal(producer['artifactBindings'], CURRENT_ARTIFACT_BINDINGS)
    need(producer['runtimeSourceCount'] == 16 and len(producer['sources']) == 31, 'CURRENT_31_SOURCE_16_WORKERS')
    by_name = {Path(p['path']).name: p for p in producer['sources']}
    need(len(by_name) == 31, 'UNIQUE_PRODUCER_SOURCE_NAMES')
    for p in producer['sources']: files.read(p)
    bindings = files.doc(producer['artifactBindings'])
    equal(bindings['amethystApk'], CURRENT_AMETHYST_APK)
    equal(bindings['helperApk'], CURRENT_HELPER_APK)
    for prefix, schema, decision in (
        ('amethyst', 'nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1', 'ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY'),
        ('helper', 'nbdp-actual-artifact-data-acceptance-v1', 'ACCEPT_REBUILT_HELPER_ARTIFACT_ONLY')):
        acceptance = files.doc(bindings[prefix + 'Acceptance'])
        equal(acceptance['schema'], schema); equal(acceptance['decision'], decision)
        need(acceptance['artifactQualified'] is True, 'EXACT_TRUE_ARTIFACT_QUALIFICATION')
        equal(acceptance['subject'], bindings[prefix + 'Provenance'])
        equal(files.doc(bindings[prefix + 'Provenance'])['apk'], bindings[prefix + 'Apk'])
    for descriptor in producer['configurations']:
        config = files.doc(descriptor)
        equal(config['sourceAndDependencyPins'], CURRENT_WORKERS)
        equal(config['amethystApk'], CURRENT_AMETHYST_APK)
        equal(config['helperApk'], CURRENT_HELPER_APK)
    return producer


def capture_output(files, scope, receipt):
    """Validate retained child streams, independently of the outer tool API."""
    raw = {name: files.read(receipt[name]) for name in ('stdout', 'stderr')}
    equal(receipt['observedStreamBytes'], {name: len(value) for name, value in raw.items()})
    equal(receipt['truncated'], {'stdout': False, 'stderr': False})
    need(len(raw['stdout']) <= 1048576 and len(raw['stderr']) <= 262144, 'POST_CAPTURE_RETENTION_LIMIT')
    if scope['name'] != 'observation-model':
        need(scope['name'] in ('public-identity-metadata','producer2-source-wiring','rebuilt-artifact-bindings'), 'EXACT_CURRENT_PYTHON_SCOPE_NAME')
        equal(raw['stdout'], b'')
        match = re.fullmatch(rb'([.]+)\n-{70}\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n', raw['stderr'])
        need(match and len(match[1]) == scope['count'] and int(match[2]) == scope['count'], 'EXACT_QUIET_PYTHON_OUTPUT')
        equal(receipt['observedPartitions'], {scope['name']: scope['count']})
    else:
        equal(raw['stderr'], b'')
        need(raw['stdout'].endswith(b'\n') and raw['stdout'].count(b'\n') == 1, 'EXACT_NODE_ONE_LINE')
        from strict import loads
        value = loads(raw['stdout'])
        closed(value, 'schema ok checks cases scope')
        equal(value['schema'], 'e02-producer2-observation-model-controls-v1')
        equal(value['ok'], True); equal(value['checks'], 20)
        equal(value['scope'], 'SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME')
        equal(value['cases'], scope['expectedCases'])
        equal(receipt['observedPartitions'], {'shared-budget-guard-proxy-and-exchange-adapter-models': 20})


def capture_child(files, scope, row, capture_root, artifact_index):
    closed(row, 'scope expected observed partitions captureMatched execution')
    equal(row['scope'], scope['name']); equal(row['expected'], scope['count'])
    equal(row['observed'], scope['count']); equal(row['captureMatched'], True)
    folder = Path(capture_root) / 'scopes' / scope['name']
    equal(row['execution']['path'], str(folder / 'execution.json'))
    receipt = files.doc(row['execution'])
    equal(receipt['schema'], 'e02-producer3-pure-scope-execution-v1')
    equal(receipt['actor'], '/root/producer3_capture'); equal(receipt['parentCoordinator'], '/root')
    equal(receipt['argv'], scope['argv']); equal(receipt['cwd'], CURRENT_EXPERIMENT_REPOSITORY)
    equal(receipt['expectedCount'], scope['count']); equal(receipt['observedCount'], scope['count'])
    equal(receipt['timeoutSeconds'], 60)
    equal(receipt['retentionBytes'], {'stdout': 1048576, 'stderr': 262144})
    equal(receipt['retentionMeaning'], 'POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP')
    integer(receipt['pid'], 1); integer(receipt['elapsedNanoseconds'], 0, 63000000000)
    equal(receipt['exitCode'], 0); equal(receipt['signal'], None)
    for key in ('reaped', 'naturalExit', 'stdoutEOF', 'stderrEOF', 'sourceUnchanged',
                'countAndOutputShapeMatched', 'captureMatched'): equal(receipt[key], True)
    equal(receipt['forceRequested'], False); equal(receipt['forceReason'], None)
    equal(receipt['firstError'], None); equal(receipt['secondaryErrors'], [])
    equal(receipt['controlResultAcceptedByAuthor'], False)
    equal(receipt['state'], 'WRITES_STOPPED')
    equal(receipt['result'], 'SCOPED_DATA_CAPTURE_MATCHED_PENDING_INDEPENDENT_REVIEW')
    equal(row['partitions'], receipt['observedPartitions'])
    for stream in ('stdout', 'stderr'): equal(receipt[stream]['path'], str(folder / ('data.' + stream)))
    capture_output(files, scope, receipt)
    before = files.doc(artifact_index[str(folder / 'sources-before.json')])
    after = files.doc(artifact_index[str(folder / 'sources-after.json')])
    equal(before, after, 'EVERY_SCOPE_FULL_BEFORE_AFTER_UNCHANGED')
    return before


def capture_inputs(files, descriptor, producer, plan):
    inputs = files.doc(descriptor)
    closed(inputs, 'schema sourceSubject sourceManifest sourceControlPlan node python actualSourceReviews requiredCoverage files actualInputCount maximumInputCount fullReadTrees scope')
    equal(inputs['schema'], 'e02-producer3-control-frozen-inputs-v1')
    equal(inputs['sourceSubject'], CURRENT_PRODUCER); equal(inputs['sourceManifest'], CURRENT_SOURCE_PACKET)
    equal(inputs['sourceControlPlan'], CURRENT_SOURCE_PLAN)
    equal(inputs['maximumInputCount'], 4096)
    integer(inputs['actualInputCount'], 1, 4096); equal(len(inputs['files']), inputs['actualInputCount'])
    indexed = {d['path']: d for d in inputs['files']}
    need(len(indexed) == len(inputs['files']), 'UNIQUE_CURRENT_CAPTURE_CLOSURE')
    for d in inputs['files']:
        closed(d, 'path bytes sha256'); hx(d['sha256']); integer(d['bytes'], 0, 8589934592)
        path = Path(text(d['path'],4096))
        need(path.is_absolute() and '..' not in path.parts and str(path) == d['path'], 'CURRENT_INPUT_CANONICAL_DESCRIPTOR')
    required = inputs['requiredCoverage']
    closed(required, 'finalSubjectManifestPlan all16Workers all4Tests runtimeFixtureBindings bothConfigurations acceptedApkHelperNativeE01 provenanceAcceptances original19 diagnosticV2 oldV1ReadOperands interpreters baselineScalarAndOracle')
    for group in required.values():
        need(type(group) is list and group, 'NONEMPTY_EXACT_COVERAGE_CATEGORY')
        for d in group: equal(indexed.get(d['path']), d)
    equal(required['finalSubjectManifestPlan'], [CURRENT_PRODUCER, CURRENT_SOURCE_PACKET, CURRENT_SOURCE_PLAN])
    equal(required['all16Workers'], CURRENT_WORKERS); equal(required['bothConfigurations'], CURRENT_CONFIGURATIONS)
    source_plan = files.doc(CURRENT_SOURCE_PLAN)
    equal(required['all4Tests'], [s['source'] for s in source_plan['scopes']])
    equal(required['interpreters'], [inputs['node'], inputs['python']])
    for key in ('node', 'python'): equal(inputs[key], source_plan[key])
    for d in producer['sources']: equal(indexed.get(d['path']), d)
    equal(indexed.get(CURRENT_SOURCE_INPUTS['path']), CURRENT_SOURCE_INPUTS)
    for row in files.doc(CURRENT_SOURCE_INPUTS)['files']:
        d = {key:row[key] for key in ('path','bytes','sha256')}
        equal(indexed.get(d['path']), d, 'ALL_PRODUCER_DECLARED_READ_INPUTS')
    trees = inputs['fullReadTrees']
    need(type(trees) is list and len(trees) == 2, 'EXACT_TWO_FULL_READ_TREES')
    for tree, (root, count) in zip(trees, CURRENT_READ_TREE_ROOTS):
        closed(tree, 'root count files'); equal(tree['root'], root); equal(tree['count'], count)
        equal(len(tree['files']), count)
        for row in tree['files']:
            closed(row, 'path bytes sha256 relativePath mode')
            d = {k: row[k] for k in ('path', 'bytes', 'sha256')}
            equal(indexed.get(d['path']), d)
            equal(str(Path(root) / row['relativePath']), row['path'])
            need(not Path(row['relativePath']).is_absolute() and '..' not in Path(row['relativePath']).parts, 'TREE_MEMBER_ESCAPE')
    equal(plan['actualInputCount'], inputs['actualInputCount'])
    return inputs


def current_capture(files, nodes, mode, origin, producer):
    """No skipped prerequisite, old result or count-equivalent scope can qualify."""
    closed(nodes, 'producerSource testSource inputClosure plan release capture originalToolResponses result acceptance qaReview securityReview admissionModelAcceptance upstreamRootACK')
    need(all(value is not None for value in nodes.values()), 'ALL_CURRENT_CAPTURE_NODES_REQUIRED')
    equal(nodes, CURRENT_CAPTURE_BINDINGS[mode], 'EXACT_FROZEN_CURRENT_CAPTURE_DAG')
    equal(nodes['producerSource'], CURRENT_PRODUCER)
    source_plan = files.doc(CURRENT_SOURCE_PLAN)
    chosen = source_plan['scopes'][:3] if mode == 'capture-a' else source_plan['scopes'][3:]
    equal(nodes['testSource'], [s['source'] for s in chosen])
    data = files.doc(nodes['result'])
    contract = files.doc(CURRENT_AUTHORITY_CONTRACT)
    closed(data, ' '.join(contract['dataSubject']['requiredKeys']))
    equal(data['schema'], 'e02-producer3-actual-control-data-subject-v1')
    equal(data['captureId'], mode); equal(data['producerSource'], CURRENT_PRODUCER)
    equal(data['producerContract'], CURRENT_SOURCE_PACKET); equal(data['captureSource'], nodes['capture'])
    equal(data['controlPlan'], nodes['plan']); equal(data['rootAcknowledgement'], nodes['release'])
    equal(data['frozenInputs'], nodes['inputClosure']); equal(data['originalToolOrigin'], nodes['originalToolResponses'])
    equal(data['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
    equal(data['coordinator'], '/root'); equal(data['state'], contract['dataSubject']['state'])
    equal(data['operators'], ['/root'])
    forbidden = actors(data['authors']) | actors(data['operators'])
    need({'/root', '/root/producer3_capture'} <= forbidden, 'CURRENT_CAPTURE_ACTORS_REQUIRED')
    origin.forbidden |= forbidden | actors(CURRENT_CONTROL_ACTORS)
    group = contract['groups'][mode]
    capture_source = files.doc(nodes['capture'])
    equal(capture_source['schema'], 'e02-producer3-bound-capture-source-subject-v1')
    equal(capture_source['producerSource'], CURRENT_PRODUCER)
    equal(capture_source['producerContract'], CURRENT_SOURCE_PACKET)
    equal(capture_source['normativeDataContract'], CURRENT_AUTHORITY_CONTRACT)
    selected_capture = capture_source['captures'][mode]
    equal(selected_capture['runner'], data['captureScript'])
    equal(selected_capture['controlPlan'], nodes['plan']); equal(selected_capture['frozenInputs'], nodes['inputClosure'])
    equal(data['scopeNames'], group['scopeNames']); equal(data['countsSeparate'], group['counts'])
    for key in ('allNatural0NoForceNoErrorNoTruncation', 'sourceUnchangedBeforeAfterEveryScopeAndOverall', 'completeInstalledMembership'): equal(data[key], True)
    equal(data['pythonNamesMeaning'], contract['dataSubject']['pythonNamesMeaning'])
    equal(data['retentionMeaning'], contract['dataSubject']['retentionMeaning'])
    equal(data['runtimeAuthorized'], False); equal(data['ordinaryRowsQualified'], 0)
    equal(data['canonicalE02'], 'PARTIAL22_UNCHANGED')
    plan = files.doc(nodes['plan'])
    equal(plan['schema'], 'e02-producer3-fixed-control-capture-plan-v1'); equal(plan['captureId'], mode)
    equal(plan['sourceSubject'], CURRENT_PRODUCER); equal(plan['sourceManifest'], CURRENT_SOURCE_PACKET)
    equal(plan['frozenSourcePlan'], CURRENT_SOURCE_PLAN); equal(plan['runner'], data['captureScript'])
    equal(plan['rawRetentionBytes'], {'stdout': 1048576, 'stderr': 262144})
    equal(plan['timeoutSeconds'], 60); equal(plan['cleanupReapSeconds'], 3)
    for key in ('stopFirstFailure', 'noRetry'): equal(plan[key], True)
    scopes = plan['separateScopes']
    equal([(s['name'], s['count']) for s in scopes], [(s['scope'], s['count']) for s in chosen])
    for scope, source_scope in zip(scopes, chosen):
        closed(scope, 'name argv count expectedCases timeoutSeconds')
        equal(scope['timeoutSeconds'], 60)
        argv = [source_plan['node']['path'], source_scope['source']['path']] if scope['name'] == 'observation-model' else [source_plan['python']['path'], '-I', '-B', source_scope['source']['path']]
        equal(scope['argv'], argv)
        if scope['name'] != 'observation-model': equal(scope['expectedCases'], source_scope['exactDefinedPythonNames'])
    inputs = capture_inputs(files, nodes['inputClosure'], producer, plan)
    equal(data['fixedInputCount'], inputs['actualInputCount'])
    execution = files.doc(data['execution'])
    closed(execution, 'schema actor captureId state result sourceSubject runnerSubject runner sourceManifest frozenSourcePlan frozenInputs captureSource admissionModelAcceptance controlPlan rootAcknowledgement scopes remainingNotExecuted sourceUnchanged terminalError noRetry controlResultAcceptedByAuthor independentResultReview noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices')
    equal(execution['schema'], 'e02-producer3-current-control-execution-v1'); equal(execution['captureId'], mode)
    equal(execution['sourceSubject'], CURRENT_PRODUCER); equal(execution['runner'], data['captureScript'])
    equal(execution['controlPlan'], nodes['plan']); equal(execution['rootAcknowledgement'], nodes['release'])
    equal(execution['runnerSubject'], selected_capture['runnerSubject'])
    equal(execution['sourceManifest'], CURRENT_SOURCE_PACKET); equal(execution['frozenSourcePlan'], CURRENT_SOURCE_PLAN)
    equal(execution['frozenInputs'], nodes['inputClosure']); equal(execution['captureSource'], nodes['capture'])
    equal(execution['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
    equal(execution['actor'], '/root/producer3_capture'); equal(execution['state'], 'WRITES_STOPPED')
    equal(execution['result'], 'FIXED_DATA_SCOPES_MATCHED_PENDING_REVIEW')
    for key in ('sourceUnchanged', 'noRetry', 'noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices'): equal(execution[key], True)
    equal(execution['controlResultAcceptedByAuthor'], False)
    equal(execution['remainingNotExecuted'], []); equal(execution['terminalError'], None)
    equal(len(execution['scopes']), len(scopes))
    capture_root = Path(nodes['plan']['path']).parent
    manifest = files.doc(data['rawArtifactManifest'])
    closed(manifest, 'schema captureId files originalApiResponses')
    equal(manifest['schema'], 'e02-producer3-current-control-artifact-manifest-v1')
    equal(manifest['captureId'], mode)
    artifact_index = {d['path']:d for d in manifest['files']}
    need(len(artifact_index) == len(manifest['files']) and len(artifact_index) <= 4096, 'RAW_ARTIFACT_MEMBERSHIP')
    snapshots = [capture_child(files, scope, row, capture_root, artifact_index) for scope, row in zip(scopes, execution['scopes'])]
    overall_before = files.doc(data['overallSourcesBefore']); overall_after = files.doc(data['overallSourcesAfter'])
    equal(overall_before, overall_after, 'OVERALL_FULL_SOURCE_SNAPSHOT_UNCHANGED')
    for snap in snapshots + [overall_before, overall_after]:
        equal(snap['sourceSubject'], CURRENT_PRODUCER); equal(snap['sourceManifest'], CURRENT_SOURCE_PACKET)
        equal(snap['frozenSourcePlan'], CURRENT_SOURCE_PLAN); equal(snap['monitor'], data['captureScript'])
        equal(snap['runnerSubject'], execution['runnerSubject']); equal(snap['controlPlan'], nodes['plan'])
        equal(snap['coordinatorAcknowledgement'], nodes['release']); equal(snap['inputManifest'], nodes['inputClosure'])
        equal(snap['frozenInputs'], inputs['files']); equal(snap['fullActualReadTrees'], inputs['fullReadTrees'])
        equal(snap['captureSource'], nodes['capture']); equal(snap['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
        equal(snap['sourceAndCaptureReviewRecords'], data['sourceReviews'] + data['captureReviews'])
        equal(snap['interpreters'], {'python':inputs['python'],'node':inputs['node']})
        model_acceptance = files.doc(nodes['admissionModelAcceptance'])
        equal(snap['admissionModelDataSubject'], model_acceptance['subject'])
        equal(snap['admissionModelReviews'], model_acceptance['reviews'])
        tree_pin = next(d for d in producer['sources'] if Path(d['path']).name == 'dependency-tree.json')
        tree = files.doc(tree_pin)
        equal(snap['installedMembership'], {k:tree[k] for k in ('directories','files','symlinks')})
        equal([len(snap['installedMembership'][k]) for k in ('files','directories','symlinks')], [816,65,2])
    # These methods are SOURCE-staged separately from the already literal child
    # schema. No absent contract or generic truthy acceptance may admit a result.
    capture_authority(files, nodes, data, execution, inputs, origin)
    return data


def capture_data_reviews(files, descriptors, subject, decision, origin):
    need(type(descriptors) is list and len(descriptors) == 2, 'CURRENT_EXACT_QA_SECURITY_PAIR')
    roles, sessions = set(), set()
    for descriptor in descriptors:
        review = files.doc(descriptor)
        closed(review, 'role session decision subject')
        need(review['role'] in ('qa', 'security') and review['role'] not in roles, 'CURRENT_EXACT_REVIEW_ROLE')
        text(review['session'], 256)
        need(review['session'].startswith('/root/') and review['session'] not in origin.forbidden,
             'CURRENT_DATA_AUTHOR_OPERATOR_CANNOT_REVIEW')
        equal(review['subject'], subject); equal(review['decision'], decision)
        roles.add(review['role']); sessions.add(review['session'])
    equal(roles, {'qa', 'security'}); need(len(sessions) == 2, 'DISTINCT_CURRENT_REVIEW_SESSIONS')
    need(descriptors[0]['sha256'] != descriptors[1]['sha256'], 'DISTINCT_CURRENT_REVIEW_DOCUMENTS')


def capture_authority(files, nodes, data, execution, inputs, origin):
    need(CURRENT_AUTHORITY_CONTRACT is not None, 'CURRENT_ACTUAL_AUTHORITY_CONTRACT_UNRENDERED')
    contract = files.doc(CURRENT_AUTHORITY_CONTRACT)
    equal(contract['schema'], 'e02-producer3-planned-data-contract-v1')
    capture_admission_models(files, nodes, data, origin)
    capture_root_ack(files, nodes, data, execution, inputs, origin)
    capture_original_tool(files, nodes, data, origin)
    manifest = files.doc(data['rawArtifactManifest'])
    closed(manifest, 'schema captureId files originalApiResponses')
    equal(manifest['schema'], 'e02-producer3-current-control-artifact-manifest-v1')
    equal(manifest['captureId'], data['captureId'])
    need(type(manifest['files']) is list and 1 <= len(manifest['files']) <= 4096, 'CURRENT_ARTIFACT_MEMBERSHIP_BOUND')
    indexed = {d['path']: d for d in manifest['files']}
    need(len(indexed) == len(manifest['files']), 'UNIQUE_CURRENT_RAW_ARTIFACT_PATHS')
    for key in ('execution', 'overallSourcesBefore', 'overallSourcesAfter', 'frozenInputs', 'controlPlan', 'captureScript', 'rootAcknowledgement'):
        d = data[key]; equal(indexed.get(d['path']), d, 'CURRENT_RAW_ARTIFACT_REQUIRED_MEMBER')
    for row in execution['scopes']:
        d = row['execution']; equal(indexed.get(d['path']), d)
        receipt = files.doc(d)
        for key in ('stdout', 'stderr'):
            p = receipt[key]; equal(indexed.get(p['path']), p)
    acceptance = files.doc(nodes['acceptance'])
    closed(acceptance, ' '.join(contract['dataAcceptance']['requiredKeys']))
    equal(acceptance['schema'], 'e02-producer3-actual-control-data-acceptance-v1')
    equal(acceptance['actor'], '/root'); equal(acceptance['subject'], nodes['result'])
    group = contract['groups'][data['captureId']]
    equal(acceptance['decision'], group['decision']); equal(acceptance['captureId'], data['captureId'])
    equal(acceptance['countsSeparate'], group['counts']); equal(acceptance['runtimeAuthorized'], False)
    equal(acceptance['ordinaryRowsQualified'], 0); equal(acceptance['canonicalE02'], 'PARTIAL22_UNCHANGED')
    equal(acceptance['reviews'], [nodes['qaReview'], nodes['securityReview']])
    capture_data_reviews(files, acceptance['reviews'], nodes['result'], group['decision'], origin)
    # External authenticated origins remain mandatory in addition to four-key
    # pinned review transcriptions. JSON authorship alone proves no identity.
    origin.reviews(nodes['result'], 'CONTROL')


def capture_admission_models(files, nodes, data, origin):
    contract = files.doc(CURRENT_AUTHORITY_CONTRACT)
    acceptance = files.doc(nodes['admissionModelAcceptance'])
    closed(acceptance, ' '.join(contract['model9Acceptance']['requiredKeys']))
    equal(acceptance['schema'], 'e02-producer3-capture-admission-model-acceptance-v1')
    equal(acceptance['actor'], '/root')
    equal(acceptance['decision'], 'ACCEPT_ACTUAL_PRODUCER3_CAPTURE_9_ADMISSION_MODELS_ONLY')
    equal(acceptance['captureSource'], nodes['capture']); equal(acceptance['countsSeparate'], [9])
    equal(acceptance['runtimeAuthorized'], False); equal(acceptance['ordinaryRowsQualified'], 0)
    need(CURRENT_ADMISSION_MODEL_CONTRACT is not None, 'CURRENT_MODEL9_SUBJECT_CONTRACT_REQUIRED')
    model_contract = files.doc(CURRENT_ADMISSION_MODEL_CONTRACT)
    equal(model_contract['schema'], 'e02-producer3-planned-model-subject-contract-v1')
    equal(model_contract['baseContractSha256'], CURRENT_AUTHORITY_CONTRACT['sha256'])
    subject = files.doc(acceptance['subject'])
    closed(subject, ' '.join(model_contract['modelDataSubject']['requiredKeys']))
    equal(subject['schema'], 'e02-producer3-capture-admission-model-data-subject-v1')
    equal(subject['state'], 'WRITES_STOPPED_PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY')
    equal(subject['coordinator'], '/root'); equal(subject['operators'], ['/root'])
    origin.forbidden |= actors(subject['authors']) | actors(subject['operators'])
    capture_source = files.doc(nodes['capture'])
    equal(subject['captureSource'], nodes['capture'])
    equal(subject['modelSource'], capture_source['modelSource'])
    equal(subject['bothInputScopes'], [capture_source['captures'][mode]['runner'] for mode in ('capture-a','capture-b')])
    equal(subject['countsSeparate'], [9]); equal(subject['allNatural0NoForceNoErrorNoTruncation'], True)
    equal(subject['inputsUnchanged'], True); equal(subject['runtimeAuthorized'], False); equal(subject['ordinaryRowsQualified'], 0)
    for key in model_contract['modelDataSubject']['pinFields']: files.read(subject[key])
    equal(files.read(subject['overallSourcesBefore']), files.read(subject['overallSourcesAfter']))
    equal(nodes['upstreamRootACK'], subject['rootAcknowledgement'])
    closed(acceptance['reviews'], 'qa security')
    capture_data_reviews(files, [acceptance['reviews']['qa'], acceptance['reviews']['security']], acceptance['subject'], acceptance['decision'], origin)
    # The exact upstream root ACK pin is frozen in the consumer DAG and the
    # independently reviewed model subject. No unrelated ACK can be substituted.
    files.read(nodes['upstreamRootACK'])
    origin.reviews(acceptance['subject'], 'CONTROL')


def capture_original_tool(files, nodes, data, origin):
    """Original outer API custody; pipeEOF/reap comes only from capture_child."""
    import decimal
    import json
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_ORIGINAL_API_KEY'); result[key] = value
        return result
    def number(token):
        need(token != '-0', 'ORIGINAL_API_NEGATIVE_ZERO')
        return integer(int(token), -I64, I64)
    def invalid(_):
        need(False, 'ORIGINAL_API_NONFINITE')
    def fraction(token):
        need(len(token) <= 128, 'ORIGINAL_API_DECIMAL_BOUND')
        value = decimal.Decimal(token)
        need(value.is_finite() and not (value.is_zero() and value.is_signed()), 'ORIGINAL_API_DECIMAL_DOMAIN')
        return value
    value = json.loads(files.read(nodes['originalToolResponses']).decode('utf-8', 'strict'),
        object_pairs_hook=pairs, parse_float=fraction, parse_int=number, parse_constant=invalid)
    stack, count = [(value, ())], 0
    while stack:
        item, path = stack.pop(); count += 1
        need(len(path) <= 48 and count <= 250000, 'ORIGINAL_API_STRUCTURE_BOUND')
        if type(item) is decimal.Decimal:
            need(path == ('launch', 'unmodifiedResponse', 'wall_time_seconds') or
                 (len(path) == 4 and path[0] == 'polls' and type(path[1]) is int and path[2:] == ('unmodifiedResponse', 'wall_time_seconds')),
                 'DECIMAL_ONLY_ORIGINAL_API_WALL_TIME')
        elif type(item) is str: text(item, 16777216)
        elif type(item) is dict: stack.extend((v, path + (k,)) for k,v in item.items())
        elif type(item) is list: stack.extend((v, path + (i,)) for i,v in enumerate(item))
    closed(value, 'schema operator launch polls'); equal(value['schema'], 'e02-actual-tool-custody-v1')
    equal(value['operator'], '/root'); need(value['operator'] in origin.forbidden, 'CURRENT_API_OPERATOR_DISCLOSURE')
    need(type(value['polls']) is list and len(value['polls']) <= 128, 'CURRENT_API_POLL_BOUND')
    def response(frame, tool):
        closed(frame, 'toolName actualArguments unmodifiedResponse'); equal(frame['toolName'], tool)
        r = frame['unmodifiedResponse']
        need(type(r) is dict and {'output', 'wall_time_seconds'} <= set(r)
             and set(r) <= {'chunk_id', 'exit_code', 'output', 'session_id', 'wall_time_seconds', 'original_token_count'}, 'ORIGINAL_API_RESPONSE_SHAPE')
        text(r['output'], 16777216)
        duration = r['wall_time_seconds']
        need(type(duration) is int or (type(duration) is decimal.Decimal and duration.is_finite()), 'ORIGINAL_API_WALL_TIME_TYPE')
        need(0 <= duration <= 10000000 and not (type(duration) is decimal.Decimal and duration.is_signed()), 'ORIGINAL_API_WALL_TIME_DOMAIN')
        if 'chunk_id' in r: text(r['chunk_id'], 256)
        if 'original_token_count' in r: integer(r['original_token_count'])
        if r.get('session_id') is not None: integer(r['session_id'], 1)
        if r.get('exit_code') is not None: integer(r['exit_code'], -255, 255)
        return r
    first = response(value['launch'], 'tools.exec_command')
    import shlex
    plan = files.doc(nodes['plan'])
    closed(plan['rootAckArgument'], 'meaning placeholder')
    equal(plan['rootAckArgument']['meaning'], 'DERIVE_HEX_SHA256_FROM_ACTUAL_EXTERNAL_ACK_FILE')
    equal(plan['rootAckArgument']['placeholder'], '__ACTUAL_ROOT_ACK_SHA256__')
    placeholder = plan['rootAckArgument']['placeholder']
    template = plan['outerRequestTemplate']
    closed(template, 'cmd workdir login yield_time_ms max_output_tokens')
    need(template['cmd'].count(placeholder) == 1, 'ONE_ACK_DIGEST_PLACEHOLDER')
    request = dict(template, cmd=template['cmd'].replace(placeholder, nodes['release']['sha256']))
    equal(request['workdir'], CURRENT_EXPERIMENT_REPOSITORY); equal(request['login'], False)
    equal(request['yield_time_ms'], 1000); equal(request['max_output_tokens'], 10000)
    argv = [nodes['release']['sha256'] if token == placeholder else token for token in plan['outerArgvTemplate']]
    equal(shlex.split(request['cmd']), argv, 'EXACT_CAPTURE_OUTER_TOKENIZATION')
    source_plan = files.doc(CURRENT_SOURCE_PLAN)
    equal(argv[:8], ['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','297'])
    equal(argv[8:], [source_plan['python']['path'],'-I','-B',data['captureScript']['path'],
                     '--execute-once','--root-ack-sha',nodes['release']['sha256']])
    equal(plan['onceCommandPrefix'], argv[8:-1])
    equal(value['launch']['actualArguments'], request, 'EXACT_CAPTURE_APPROVED_OUTER_API_REQUEST')
    outputs = [first['output']]
    if first.get('exit_code') is not None:
        equal(first['exit_code'], 0); equal(first.get('session_id'), None); equal(value['polls'], [])
    else:
        session = first.get('session_id'); integer(session, 1)
        need(value['polls'], 'ALL_GENUINE_SAME_SESSION_POLLS_REQUIRED')
        for index, frame in enumerate(value['polls']):
            r = response(frame, 'tools.write_stdin')
            outputs.append(r['output'])
            args = frame['actualArguments']; closed(args, 'session_id chars yield_time_ms max_output_tokens')
            equal(args['session_id'], session); equal(args['chars'], '')
            integer(args['yield_time_ms'], 1, 300000); integer(args['max_output_tokens'], 1, 10000)
            if index == len(value['polls']) - 1:
                equal(r.get('exit_code'), 0); equal(r.get('session_id'), None)
            else:
                equal(r.get('exit_code'), None); equal(r.get('session_id'), session)
    from strict import loads
    raw = ''.join(outputs).encode('utf-8', 'strict')
    need(raw.endswith(b'\n') and raw.count(b'\n') == 1, 'EXACT_ORIGINAL_API_CAPTURE_SUMMARY')
    summary = loads(raw)
    closed(summary, 'state captureId captureMatched execution scopes')
    equal(summary['state'], 'WRITES_STOPPED'); equal(summary['captureId'], data['captureId'])
    equal(summary['captureMatched'], True); equal(summary['execution'], data['execution'])
    equal(summary['scopes'], files.doc(data['execution'])['scopes'])
    # An authenticated CONTROL origin additionally binds this pinned document;
    # no claimed inner API/PID/EOF field is admitted into the closed envelope.


def capture_root_ack(files, nodes, data, execution, inputs, origin):
    ack = files.doc(nodes['release'])
    closed(ack, 'schema actor captureId sourceSubject runnerSubject runner controlPlan frozenInputs sourceQaReview sourceSecurityReview sourceQaDecision sourceSecurityDecision captureQaReview captureSecurityReview captureQaDecision captureSecurityDecision pureControlsAuthorized allowedScopes stopFirstFailure noRetry ordinaryRuntimeAuthorized primaryAuthorized consumerAuthorized androidAuthorized servicesAuthorized protocolCryptoOrNativeAuthorized sdkAuthorized roleMaterializationAuthorized admissionModelAcceptance')
    equal(ack['schema'], 'e02-producer3-controls-root-ack-v2'); equal(ack['actor'], '/root')
    equal(ack['captureId'], execution['captureId']); equal(ack['sourceSubject'], CURRENT_PRODUCER)
    equal(ack['runnerSubject'], execution['runnerSubject']); equal(ack['runner'], data['captureScript'])
    equal(ack['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
    equal(ack['controlPlan'], nodes['plan']); equal(ack['frozenInputs'], nodes['inputClosure'])
    names = {'capture-a': {'observation-model': 20, 'public-identity-metadata': 8, 'producer2-source-wiring': 7},
             'capture-b': {'rebuilt-artifact-bindings': 3}}
    equal(ack['allowedScopes'], names[execution['captureId']])
    for key in ('pureControlsAuthorized', 'stopFirstFailure', 'noRetry'): equal(ack[key], True)
    for key in ('ordinaryRuntimeAuthorized', 'primaryAuthorized', 'consumerAuthorized', 'androidAuthorized',
                'servicesAuthorized', 'protocolCryptoOrNativeAuthorized', 'sdkAuthorized', 'roleMaterializationAuthorized'): equal(ack[key], False)
    runner = files.doc(execution['runnerSubject'])
    for key in ('runner', 'controlPlan', 'frozenInputs', 'captureId'): equal(runner[key], ack[key])
    for d in runner['preparationArtifacts']: files.read(d)
    for prefix, subject in (('source', CURRENT_PRODUCER), ('capture', execution['runnerSubject'])):
        sessions = []
        for role, title in (('qa', 'Qa'), ('security', 'Security')):
            descriptor = ack[prefix + title + 'Review']
            if prefix == 'source': equal(descriptor, inputs['actualSourceReviews'][role])
            review = files.doc(descriptor)
            closed(review, 'role session decision subject')
            equal(review['role'], role); equal(review['subject'], subject)
            equal(review['decision'], ack[prefix + title + 'Decision'])
            need(CURRENT_SOURCE_CAPTURE_DECISIONS is not None, 'CURRENT_REVIEW_DECISIONS_UNRENDERED')
            equal(review['decision'], CURRENT_SOURCE_CAPTURE_DECISIONS[prefix][role])
            text(review['session'], 256)
            need(review['session'].startswith('/root/') and review['session'] not in origin.forbidden,
                 'CURRENT_CAPTURE_SOURCE_AUTHOR_OPERATOR_REVIEW_LAUNDERING')
            sessions.append(review['session'])
        need(sessions[0] != sessions[1], 'DISTINCT_CURRENT_QA_SECURITY_SESSIONS')
    equal(data['sourceReviews'], [ack['sourceQaReview'], ack['sourceSecurityReview']])
    equal(data['captureReviews'], [ack['captureQaReview'], ack['captureSecurityReview']])


def control_evidence(files, descriptor, origin):
    require_current_source_profile()
    value = files.doc(descriptor)
    closed(value, 'schema profileId authors operators producerSubject producerCaptureA producerCaptureB componentCarry unchangedScopes consumerSource consumerControls')
    equal(value['schema'], 'e02-minimum-controls-subject-v3'); equal(value['profileId'], wire.PROFILE)
    producer = current_producer(files, value['producerSubject'])
    # Close the actor union across BOTH groups and their upstream model DATA
    # before reviewing either group. Later groups cannot hide a reviewer who is
    # already an author/operator of other newly admitted DATA.
    origin.forbidden |= actors(value['authors']) | actors(value['operators']) | actors(CURRENT_CONTROL_ACTORS)
    for field in ('producerCaptureA', 'producerCaptureB'):
        nodes = value[field]
        actual = files.doc(nodes['result'])
        origin.forbidden |= actors(actual['authors']) | actors(actual['operators'])
        model_acceptance = files.doc(nodes['admissionModelAcceptance'])
        model = files.doc(model_acceptance['subject'])
        origin.forbidden |= actors(model['authors']) | actors(model['operators'])
    current_capture(files, value['producerCaptureA'], 'capture-a', origin, producer)
    current_capture(files, value['producerCaptureB'], 'capture-b', origin, producer)
    # Existing unchanged guard/component custody remains supplemental history;
    # none can replace either current capture or donate ordinary rows.
    equal(value['componentCarry'], producer['componentCarry'])
    component = files.doc(value['componentCarry'])
    for pair in component['modules']:
        equal(pair['classification'], 'BYTE_IDENTICAL')
        equal(files.read(pair['original']), files.read(pair['current']))
    need(type(value['unchangedScopes']) is list and len(value['unchangedScopes']) == 1, 'GUARD_CARRY_ONLY')
    carry = value['unchangedScopes'][0]
    closed(carry, 'name count oldSource currentSource actualResult acceptance meaning')
    equal(carry['name'], 'guard'); equal(carry['count'], 29)
    equal(carry['meaning'], 'BYTE_IDENTICAL_CARRY_NOT_NEW_EXECUTION')
    equal(files.read(carry['oldSource']), files.read(carry['currentSource']))
    for key in ('actualResult', 'acceptance'): files.read(carry[key])
    for key in ('source', 'actualControls', 'actualAcceptance', 'bridgeAcceptance'):
        if key in component['ordinaryBaseline']: files.read(component['ordinaryBaseline'][key])
    for key in ('source', 'actualControls', 'actualAcceptance', 'runtimeAcceptance'):
        if key in component['diagnosticBaseline']: files.read(component['diagnosticBaseline'][key])
    for d in component['functionProofs']: files.read(d)
    files.read(value['consumerSource']); files.read(value['consumerControls'])
    origin.reviews(descriptor, 'CONTROL')
    return value

def graph(files, subject):
    root = Path(subject['outputRoot'])
    need(root.is_absolute() and root.name == subject['runId'], 'EXACT_FRESH_OUTPUT_ROOT')
    need(type(subject['graphFiles']) is list and len(subject['graphFiles']) <= 20000, 'GRAPH_FILES_BOUND')
    paths = set()
    for descriptor in subject['graphFiles']:
        p = pin_shape(descriptor)
        need(p.is_relative_to(root) and str(p) not in paths, 'GRAPH_PATH_ALIAS')
        paths.add(str(p)); files.read(descriptor, 67108864)
    exclusions = subject['excludedFiles']
    need(type(exclusions) is list and len(exclusions) <= 20000, 'EXCLUSION_BOUND')
    for item in exclusions:
        closed(item, 'path reason')
        p = Path(item['path'])
        need(p.is_relative_to(root) and str(p) not in paths, 'EXCLUSION_ALIAS')
        need(item['reason'] in ('DISPOSABLE_DISK_IMAGE', 'PRIVATE_RUNTIME_KEY', 'SDK_APK_INPUT', 'RAW_APPLICATION_DATABASE'), 'CLOSED_EXCLUSION_REASON')
        need(not any(part in p.parts for part in ('commands', 'ui', 'evidence', 'session', 'cleanup', 'ownership')), 'PROOF_CANNOT_BE_EXCLUDED')
    return paths


def fixture_calls(files, driver, command_rows):
    pins = driver['fixtureCalls']
    need(type(pins) is list and 1 <= len(pins) <= 64, 'FIXTURE_CALL_BOUND')
    calls, last = {}, 0
    for ordinal, descriptor in enumerate(pins, 1):
        c = files.doc(descriptor)
        closed(c, 'schema profileId windowId operation ordinal commandSequence command reply')
        equal(c['schema'], 'e02-minimum-fixture-call-v1'); equal(c['profileId'], wire.PROFILE)
        equal(c['windowId'], driver['windowId']); equal(c['ordinal'], ordinal)
        need(c['operation'] in ('prepare', 'status', 'publish'), 'CLOSED_FIXTURE_OPERATION')
        seq = c['commandSequence']; integer(seq, last + 1, len(command_rows)); last = seq
        equal(files.doc(c['command']), command_rows[seq - 1]); calls[seq] = (descriptor, c)
        argv = command_rows[seq - 1]['argv']
        need(len(argv) == 6 and argv[:2] == ['/usr/bin/docker', 'exec'] and
             argv[3:] == ['/usr/local/bin/node', '/input/fixture.mjs', c['operation']], 'ACTUAL_FIXED_FIXTURE_COMMAND')
        equal(files.read(c['reply']), files.read(command_rows[seq - 1]['stdout']))
        reply = files.doc(c['reply'])
        closed(reply, 'schema profileId windowId operation caseId ok result')
        equal(reply['schema'], 'e02-minimum-fixture-command-v2'); equal(reply['profileId'], wire.PROFILE)
        equal(reply['windowId'], driver['windowId']); equal(reply['operation'], c['operation'])
        equal(reply['caseId'], 'minimum-two-role-rs'); equal(reply['ok'], True)
        result = reply['result']
        if c['operation'] == 'prepare':
            closed(result, 'profileId windowId ordinaryRole expected prepared inboxes')
            equal(result['ordinaryRole'], driver['ordinaryRole'])
        elif c['operation'] == 'status':
            closed(result, 'profileId windowId stageId stageIndex complete ready gate captureSequence scope')
            idx = result['stageIndex']; integer(idx, 0, len(wire.STAGES[driver['ordinaryRole']]))
            expected_stage = wire.STAGES[driver['ordinaryRole']][idx] if idx < len(wire.STAGES[driver['ordinaryRole']]) else None
            equal(result['stageId'], expected_stage); equal(result['complete'], expected_stage is None)
            equal(result['ready'], result['gate'] is not None)
            if result['gate'] is not None: wire.generation(result['gate'], True)
            integer(result['captureSequence'], 0, 262144)
            equal(result['scope'], 'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT')
        else:
            closed(result, 'profileId windowId stage publication publicationWindow validation producerValidation actualNewAppFrameObserved')
            record = files.doc(result['publication'])
            for key in ('stage', 'publicationWindow', 'validation', 'producerValidation', 'actualNewAppFrameObserved'):
                equal(result[key], record[key], 'PUBLISH_REPLY_ACTUAL_RECORD')
        equal(result['profileId'], wire.PROFILE); equal(result['windowId'], driver['windowId'])
    actual = {i for i, c in enumerate(command_rows, 1) if '/input/fixture.mjs' in c['argv'] and c['argv'][-1] in ('prepare', 'status', 'publish')}
    equal(set(calls), actual, 'OMITTED_FIXTURE_CALL')
    operations = [c['operation'] for _, c in calls.values()]
    equal(operations.count('prepare'), 1); equal(operations[0], 'prepare')
    equal(operations.count('publish'), len(wire.STAGES[driver['ordinaryRole']]))
    return calls


def preparation_join(files, calls, candidate, role, proxy):
    first = next(iter(calls.values()))[1]
    prepared_result = files.doc(first['reply'])['result']
    p = files.doc(prepared_result['prepared'])
    closed(p, 'schema profileId windowId role rumors events expected')
    equal(p['schema'], 'e02-minimum-prepared-v2'); equal(p['profileId'], wire.PROFILE)
    equal(p['windowId'], wire.WINDOWS[role]); equal(p['role'], role)
    closed(p['rumors'], 'business chat')
    for name in ('business', 'chat'): equal(p['rumors'][name], files.doc(candidate['oracles'][name]))
    equal(p['expected'], prepared_result['expected'])
    equal(set(p['expected']), set(wire.STAGES[role]))
    need(type(p['events']) is list and len(p['events']) == len(wire.STAGES[role]), 'FINITE_PREPARED_OUTERS')
    for index, name in enumerate(wire.STAGES[role]):
        spec = wire.stage(role, index); expected = p['expected'][name]
        closed(expected, 'stage rumor content'); equal(expected['stage'], spec)
        equal(files.doc(expected['rumor']), p['rumors'][spec['oracle']])
        equal(files.read(expected['content']), p['rumors'][spec['oracle']]['content'].encode('utf-8'))
        wire.signed(p['events'][index], wire.ACCOUNTS[role])
    if role == 'archive':
        equal(p['events'][0], p['events'][1]); need(p['events'][2]['id'] != p['events'][0]['id'], 'PREPARED_FRESH_WRAP')
    inboxes = files.doc(prepared_result['inboxes'])
    closed(inboxes, 'events ack received eose sentFrames elapsedNanoseconds')
    need(type(inboxes['events']) is list and len(inboxes['events']) == 2, 'BOTH_CURRENT_INBOXES')
    equal(inboxes['received'], []); equal(inboxes['eose'], None)
    integer(inboxes['elapsedNanoseconds'], 0, 1800000000000)
    need(len(inboxes['ack']) == len(inboxes['sentFrames']) == 2, 'TWO_REAL_INBOX_SEND_ACKS')
    outgoing = [r for r in proxy.rows if r.get('exchangeLabel') == 'prepare-inboxes' and r['direction'] == 'PRODUCER_TO_RELAY']
    incoming = [r for r in proxy.rows if r.get('exchangeLabel') == 'prepare-inboxes' and r['direction'] == 'RELAY_TO_PRODUCER']
    equal(len(outgoing), 2)
    for i, (event, account) in enumerate(zip(inboxes['events'], (wire.A, wire.B))):
        closed(event, 'id pubkey created_at kind tags content sig')
        equal(event['pubkey'], account); equal(event['kind'], 10050); equal(event['tags'], [['relay', 'ws://127.0.0.1:17777']]); equal(event['content'], '')
        integer(event['created_at']); hx(event['sig'], 128)
        equal(event['id'], hashlib.sha256(json_bytes([0, account, event['created_at'], 10050, event['tags'], ''])).hexdigest())
        sent = inboxes['sentFrames'][i]
        closed(sent, 'frame eventId messageType sendInvoked sendCallbackCompleted callbackBufferHash')
        equal(sent['eventId'], event['id']); equal(sent['messageType'], 'EVENT')
        equal(sent['sendInvoked'], True); equal(sent['sendCallbackCompleted'], True)
        raw = files.read(sent['frame']); equal(wire.frame(raw), ['EVENT', event])
        equal(sent['callbackBufferHash'], hashlib.sha256(raw).hexdigest())
        equal(wire.decode64(outgoing[i]['rawBase64']), raw)
        matching = [a for a in inboxes['ack'] if a['frame'][1] == event['id']]
        need(len(matching) == 1, 'ONE_INBOX_ACK')
        ack = matching[0]; closed(ack, 'rawBase64 frame')
        equal(wire.frame(wire.decode64(ack['rawBase64'])), ack['frame'])
        need(len(ack['frame']) == 4 and ack['frame'][:3] == ['OK', event['id'], True], 'INBOX_REAL_OK')
        need(any(r['rawBase64'] == ack['rawBase64'] for r in incoming), 'INBOX_ACK_IN_RAW_PROXY')
    return p


def status_join(files, obs, spec, role, command_rows, calls, publication):
    status = obs['subscriptionStatus']
    closed(status, 'profileId windowId stageId stageIndex complete ready gate captureSequence scope')
    equal(status['profileId'], wire.PROFILE); equal(status['windowId'], wire.WINDOWS[role])
    equal(status['stageId'], spec['id']); equal(status['stageIndex'], spec['index'])
    equal(status['complete'], False); equal(status['ready'], True)
    equal(status['scope'], 'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT')
    equal(status['gate'], publication['gate'], 'STATUS_PUBLICATION_CURRENT_GATE')
    integer(status['captureSequence'], status['gate']['eoseSequence'], 262144)
    call = files.doc(obs['subscriptionStatusCall'])
    seq = call['commandSequence']; need(seq in calls, 'STATUS_IN_FULL_FIXTURE_CALLS')
    equal(calls[seq][0], obs['subscriptionStatusCall']); equal(call['operation'], 'status')
    equal(call['command'], obs['subscriptionStatusCommand']); equal(call['reply'], obs['subscriptionStatusReply'])
    equal(files.doc(call['reply'])['result'], status)
    equal(files.doc(obs['subscriptionStatusCommand']), command_rows[seq - 1])
    need(obs['custodySegment']['commandSequenceFirst'] <= seq <= obs['custodySegment']['commandSequenceLast'], 'STATUS_IN_STAGE_CUSTODY')


def guest_observations(files, root, command_rows):
    def observed(name, tail):
        descriptor = files.pins[str(Path(root) / 'evidence' / name)]
        raw = files.read(descriptor)
        matches = [c for c in command_rows if gui.adb_tail(c) == tail]
        need(len(matches) == 1, 'ONE_ACTUAL_PROPERTY_PROBE')
        equal(raw, files.read(matches[0]['stdout']))
        return raw
    equal(observed('ro.build.version.sdk.txt', ['shell', 'getprop', 'ro.build.version.sdk']).strip(), b'35')
    equal(observed('ro.build.fingerprint.txt', ['shell', 'getprop', 'ro.build.fingerprint']).strip(),
          b'Android/sdk_phone64_x86_64/emu64x:15/AE3A.240806.019/12368160:userdebug/test-keys')
    rows = files.doc(files.pins[str(Path(root) / 'evidence/network-addresses.json')])
    for relative, payload in (('network-addresses.json', ['probe', 'ip', '-j', 'addr']),
                              ('listeners.txt', ['probe', 'ss', '-H', '-lnt'])):
        probes = [c for c in command_rows if c['argv'][-4:] == payload]
        need(len(probes) == 1, 'ONE_ACTUAL_NAMESPACE_PROBE')
        descriptor = files.pins[str(Path(root) / 'evidence' / relative)]
        equal(files.read(descriptor), files.read(probes[0]['stdout']), 'ACTUAL_NAMESPACE_RAW_STREAM')
    need(type(rows) is list and len(rows) == 1 and rows[0].get('ifname') == 'lo', 'ACTUAL_PRIVATE_LOOPBACK_ONLY')
    interface = rows[0]
    need(type(interface.get('flags')) is list and 'LOOPBACK' in interface['flags'], 'ACTUAL_LOOPBACK_FLAGS')
    entries = interface.get('addr_info')
    need(type(entries) is list and 1 <= len(entries) <= 16, 'ACTUAL_LOOPBACK_ADDRESSES')
    for e in entries:
        text(e['local'], 64); need('%' not in e['local'], 'UNZONED_LOOPBACK')
        address = ipaddress.ip_address(e['local'])
        need(address.is_loopback and e['family'] == ('inet' if address.version == 4 else 'inet6')
             and e['scope'] == 'host' and e['prefixlen'] == (8 if address.version == 4 else 128), 'LOOPBACK_ADDRESS_DOMAIN')
    listeners = files.read(files.pins[str(Path(root) / 'evidence/listeners.txt')]).decode('ascii', 'strict').splitlines()
    need(1 <= len(listeners) <= 4096, 'ACTUAL_LISTENERS')
    for line in listeners:
        fields = line.split()
        need(len(fields) == 5 and fields[0] == 'LISTEN' and fields[4] in ('0.0.0.0:*', '[::]:*', '*:*'), 'LISTENER_ROW')
        need(all(re.fullmatch('[0-9]{1,10}', n) and int(n) <= 4294967295 for n in fields[1:3]), 'LISTENER_QUEUE_DOMAIN')
        match = re.fullmatch(r'(?:\[([^\[\]]+)\]|([0-9.]+)):([1-9][0-9]{0,4})', fields[3])
        need(match is not None, 'NUMERIC_LISTENER')
        address = ipaddress.ip_address(match[1] or match[2]); integer(int(match[3]), 1, 65535)
        mapped = address.ipv4_mapped if address.version == 6 else None
        need(address.is_loopback or mapped is not None and mapped.is_loopback
             or fields[3] in ('0.0.0.0:8080', '[::]:8080'), 'NO_UNEXPECTED_NONLOOPBACK_LISTENER')


def window(files, descriptor, candidate, origin, producer):
    require_current_source_profile()
    s = files.doc(descriptor); closed(s, WINDOW_KEYS)
    equal(s['schema'], 'e02-minimum-window-subject-v1'); equal(s['profileId'], wire.PROFILE)
    role = s['ordinaryRole']; need(role in wire.STAGES, 'WINDOW_ROLE')
    equal(s['windowId'], wire.WINDOWS[role]); need(re.fullmatch('[0-9a-f]{32}', s['runId']), 'WINDOW_RUNID')
    equal(s['sourceSubject'], candidate['producerSubject'])
    root = s['outputRoot']; files.window(root)
    paths = graph(files, s)
    # Exact /input mounts must derive from frozen producer fixture-plan pins.
    fixture = files.doc(next(p for p in producer['sources'] if Path(p['path']).name == 'fixture-plan.json'))
    equal(fixture['schema'], 'e02-ordinary-minimum-fixture-plan-v2')
    equal(fixture['profileId'], wire.PROFILE)
    expected_mounts = {p['path']: p for p in fixture['pins'].values()}
    equal(len(s['readOnlyMountBindings']), len(expected_mounts))
    equal({b['guest']['path'] for b in s['readOnlyMountBindings']}, set(expected_mounts))
    for b in s['readOnlyMountBindings']:
        closed(b, 'guest host')
        source = expected_mounts[b['guest']['path']]
        equal(b['host'], {'path': source['source'], 'bytes': source['bytes'], 'sha256': source['sha256']})
        files.binding(b['guest'], b['host'], root)
    config = files.doc(s['runConfig']); closed(config, CONFIG_KEYS)
    need(any(same(s['runConfig'], p) for p in producer['configurations']), 'FROZEN_REVIEWED_ROLE_CONFIGURATION')
    equal(config['schema'], 'e02-ordinary-minimum-role-runtime-plan-v2')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId'): equal(config[key], s[key])
    equal(config['account'], wire.ACCOUNTS[role]); equal(config['peer'], wire.A if role == 'incoming' else wire.B)
    integer(config['originalLeaseSeconds'], 60, 1800)
    source_by_name = {Path(p['path']).name: p for p in producer['sources']}
    expected_sources = [source_by_name[name] for name in ('supervisor.py', 'lease_guard.py', 'android_driver.py', 'ui-plan.json',
                       'fixture.mjs', 'fixture-plan.json', 'minimum-plan.json', 'business-rumor.json', 'chat-rumor.json',
                       'exchange.mjs', 'phase-writer.mjs', 'dependency-tree.mjs', 'dependency-tree.json',
                       'capture-budget.mjs', 'exchange-adapter.mjs', 'proxy-observer.mjs')]
    equal(config['sourceAndDependencyPins'], expected_sources, 'CURRENT_SOURCE_CONFIG_PROVENANCE')
    equal(s['supervisorSource'], source_by_name['supervisor.py'])
    for pin in expected_sources:
        raw = files.read(pin)
        staged = dict(pin, path=str(Path(root) / 'input' / Path(pin['path']).name))
        equal(files.read(staged), raw, 'STAGED_CURRENT_SOURCE')
        need(staged['path'] in paths, 'STAGED_SOURCE_IN_WHOLE_GRAPH')
    equal(config['runtimeImage'], 'sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f')
    equal(config['relayImage'], 'sha256:fe586a0bc68edefb553a62d21983de469128f7cb785bfcc2ef7c82dbf1cded82')
    equal(config['sdkRoot'], '/tmp/nbdp-e02-api35-fixture-r2/sdk')
    equal(config['scope'], RUNTIME_SCOPE)
    equal(config['canonicalE02'], 'PARTIAL22_UNCHANGED')
    equal(config['amethystApk'], CURRENT_AMETHYST_APK, 'EXACT_CURRENT_ACCEPTED_AMETHYST_ARTIFACT')
    equal(config['helperApk'], CURRENT_HELPER_APK, 'EXACT_CURRENT_ACCEPTED_HELPER_ARTIFACT')
    # SDK/APK assets remain external pinned prerequisites; inspecting their index
    # is not build attestation, current admission or a bundled replay image.
    files.read(config['sdkInventory']); files.read(config['guardBundleInventory']); files.read(config['relayConfig'])
    release = files.doc(s['runRelease'])
    closed(release, 'schema executionAuthorized rootSession executionSession runId scope profileId ordinaryRole windowId runConfig sourceSubject issuedAtUtcNs notAfterUtcNs qaReview securityReview guardRegressionEvidence freshResourceAdmission resourcePrerequisite limits')
    equal(release['schema'], 'e02-ordinary-minimum-role-release-v2')
    equal(release['executionAuthorized'], True); equal(release['runConfig'], s['runConfig'])
    equal(release['sourceSubject'], candidate['producerSubject']); equal(release['scope'], config['scope'])
    need(release['rootSession'] in origin.forbidden and release['executionSession'] in origin.forbidden, 'DECLARED_ACTUAL_GRANT_OPERATOR')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId'): equal(release[key], s[key])
    integer(release['issuedAtUtcNs'], 0, I64); integer(release['notAfterUtcNs'], release['issuedAtUtcNs'], I64)
    for key in ('qaReview', 'securityReview', 'guardRegressionEvidence'): files.read(release[key])
    for key, reviewer_role in (('qaReview', 'qa'), ('securityReview', 'security')):
        reviewed = [r for r in origin.value['reviews'] if r['kind'] == 'SOURCE' and r['role'] == reviewer_role
                    and same(r['subject'], candidate['producerSubject'])]
        need(len(reviewed) == 1, 'RELEASE_CURRENT_SOURCE_REVIEW')
        equal(release[key], reviewed[0]['review'], 'GRANT_ACTUAL_SOURCE_ACCEPTANCE_JOIN')
    tool = origin.tool(s['outer'], s)
    lease = lease_check(files, s['lease'], s['runId'], release, tool)
    resource = files.doc(s['resource'])
    closed(resource, 'schema runId measuredAtUtcNs outputFilesystem freeBytes memAvailableBytes affinityCpus kvmAccessible rawReceipt sourceIndex actualAdmissionMeaning')
    equal(resource['schema'], 'e02-minimum-resource-witness-v1'); equal(resource['runId'], s['runId'])
    need(resource['measuredAtUtcNs'] <= release['issuedAtUtcNs'] <= lease['issuedUtcNs'], 'RESOURCE_BEFORE_GRANT')
    equal(resource['outputFilesystem'], root)
    integer(resource['freeBytes'], 8 * 1024 ** 3); integer(resource['memAvailableBytes'], 12 * 1024 ** 3)
    integer(resource['affinityCpus'], 8); equal(resource['kvmAccessible'], True)
    equal(resource['sourceIndex'], config['sdkInventory']); files.read(resource['rawReceipt'])
    equal(resource['rawReceipt'], release['freshResourceAdmission']); files.read(release['resourcePrerequisite'])
    equal(resource['actualAdmissionMeaning'], 'ACTUAL_CURRENT_ADMISSION_NOT_MINIMUM_OR_PEAK_OR_GUEST_HEALTH')
    equal(s['sourceControls'], candidate['sourceControls'])
    command_rows = commands(files, s['commands'], root)
    owned_cids = ownership(files, s, config, fixture, command_rows)
    guest_observations(files, root, command_rows)
    ui_start = [i for i, c in enumerate(command_rows, 1) if gui.adb_tail(c) == ['shell', 'pm', 'clear', gui.APP]]
    need(len(ui_start) == 1, 'FRESH_ONCE_APP_CLEAR')
    snapshot_tails = (['shell', 'uiautomator', 'dump', '/sdcard/nbdp-window.xml'],
                      ['shell', 'cat', '/sdcard/nbdp-window.xml'], ['exec-out', 'screencap', '-p'])
    ui_actions = [i for i, c in enumerate(command_rows, 1) if i >= ui_start[0]
                  and gui.adb_tail(c) is not None and gui.adb_tail(c) not in snapshot_tails]
    need(len(ui_actions) <= 120, 'ORIGINAL_WHOLE_UI_ACTION_CAP')
    driver = files.doc(s['driver']); closed(driver, DRIVER_KEYS)
    equal(driver['schema'], 'e02-minimum-role-driver-result-v2')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId', 'runConfig', 'runRelease'): equal(driver[key], s[key])
    equal(driver['executionState'], 'PARTIAL'); equal(driver['canonicalE02Changed'], False)
    equal(driver['expectedAccountPubkey'], wire.ACCOUNTS[role])
    equal(driver['accountIdentityQualification'], 'ACTUAL_NPROFILE_INDEPENDENT_DECODE_AND_REVIEW_REQUIRED')
    equal(driver['allUICaptures'], s['ui']); gui.captures(files, s['ui'], command_rows)
    gui.account(files, driver['accountIdentityGUI'], role)
    tor = files.doc(driver['torConfigurationGUI'])
    equal(tor['schema'], 'e02-tor-configuration-gui-v1')
    for key in ('selectedOff', 'firstSaveReturnedToLogin', 'savedStateReopened', 'secondSaveReturnedToLogin'):
        need(any(same(tor[key], c) for c in s['ui']), 'TOR_ACTUAL_UI_INVENTORY')
    integer(tor['torFailureDismissals'], 0, 2)
    need(type(driver['environmentAnrEvidence']) is list and len(driver['environmentAnrEvidence']) <= 2, 'BOUNDED_RETAINED_ANR')
    for row in driver['environmentAnrEvidence']:
        closed(row, 'decision afterWaitObservation')
        need(row['afterWaitObservation'] is not None, 'PARTIAL_OS_RECOVERY_CANNOT_QUALIFY')
        files.doc(row['decision']); files.doc(row['afterWaitObservation'])
    supervisor = files.doc(s['supervisor'])
    closed(supervisor, 'schema runId profileId ordinaryRole windowId runConfig runRelease lease canonicalE02Changed limits executionState error secondaryErrors cleanup')
    equal(supervisor['schema'], 'e02-ordinary-minimum-role-supervisor-result-v2')
    for key in ('runId', 'profileId', 'ordinaryRole', 'windowId', 'runConfig', 'runRelease', 'lease'): equal(supervisor[key], s[key])
    equal(supervisor['executionState'], 'PARTIAL'); equal(supervisor['error'], None); equal(supervisor['secondaryErrors'], [])
    equal(supervisor['canonicalE02Changed'], False)
    cids = cleanup_check(files, supervisor['cleanup'], root)
    equal(cids, owned_cids, 'CLEANUP_MATCHES_ALL_ACTUAL_OWNERS')
    # No early observation contributes until whole lifecycle has qualified.
    calls = fixture_calls(files, driver, command_rows)
    proxy = wire.Proxy(files, s['proxy'])
    trace = observer.Trace(files, s, proxy)
    need(not any(r['direction'] == 'PUBLICATION_GENERATION_INVALIDATED' for r in proxy.rows), 'RETAINED_STICKY_GENERATION_FAILURE')
    labels = {'prepare-inboxes', *(sid + suffix for sid in wire.STAGES[role] for suffix in ('-publish', '-query'))}
    need(all(r.get('exchangeLabel') in labels for r in proxy.rows if 'exchangeLabel' in r), 'CLOSED_WHOLE_BACKEND_HISTORY')
    need(not any(Path(p).name.startswith(('serve-error', 'command-error')) for p in paths
                 if Path(p).is_relative_to(Path(root) / 'session/fixtures')), 'RETAINED_FIXTURE_FAILURE')
    prepared = preparation_join(files, calls, candidate, role, proxy)
    inboxes = files.doc(files.doc(next(iter(calls.values()))[1]['reply'])['result']['inboxes'])
    trace.exchange('prepare-inboxes', {k: v for k, v in inboxes.items() if k != 'events'})
    observations = driver['observations']
    need(type(observations) is list, 'OBSERVATION_ARRAY')
    equal([o['id'] for o in observations], list(wire.STAGES[role]), 'EXACT_ORDERED_ROLE_STAGES')
    previous_command, previous_ui, previous_time = 0, 0, -1
    events, sent = [], []
    previous_phase = 0
    for index, obs in enumerate(observations):
        closed(obs, OBS_KEYS); spec = wire.stage(role, index)
        equal(obs['state'], 'EXPORTED_PENDING_INDEPENDENT_WHOLE_RUN_REVIEW')
        expected = files.doc(obs['expectedRumor']); wire.rumor(expected)
        equal(expected, files.doc(candidate['oracles'][spec['oracle']]), 'SHARED_FROZEN_EXPECTATION')
        bindings = obs['originalGuestToHostBindings']
        need(type(bindings) is list and len(bindings) <= 512
             and len({b['guest']['path'] for b in bindings}) == len(bindings), 'UNIQUE_ORIGINAL_GUEST_BINDINGS')
        for binding in bindings:
            closed(binding, 'guest host'); files.binding(binding['guest'], binding['host'], root)
        publication = files.doc(obs['publication'])
        equal(publication['event'], prepared['events'][index], 'PUBLISHED_CURRENT_PREPARED_OUTER')
        published_calls = [c for _, c in calls.values() if c['operation'] == 'publish' and
                           same(files.doc(c['reply'])['result']['publication'], obs['publication'])]
        need(len(published_calls) == 1 and obs['custodySegment']['commandSequenceFirst'] <= published_calls[0]['commandSequence']
             <= obs['custodySegment']['commandSequenceLast'], 'ACTUAL_PUBLISH_IN_STAGE_CUSTODY')
        event, send = wire.publication(files, proxy, publication, expected, spec, role)
        phase_first, phase_last = trace.stage(publication)
        need(phase_first > previous_phase, 'FRESH_NONOVERLAPPING_STAGE_PHASES')
        previous_phase = phase_last
        native_record = files.doc(publication['validation']['validation'])
        for key in ('rustBinary', 'rustSource'):
            actual_input = fixture['pins'][key]
            equal(native_record[key], {k: actual_input[k] for k in ('path', 'bytes', 'sha256')}, 'CURRENT_NATIVE_FIXTURE_BINDING')
        equal(obs['actualNewAppFrameObserved'], publication['actualNewAppFrameObserved'])
        status_join(files, obs, spec, role, command_rows, calls, publication)
        custody = gui.selection(files, obs, expected, spec, role, command_rows, s['ui'], config['helperApk'])
        equal(custody['uiActionCountBefore'], sum(i < custody['commandSequenceFirst'] for i in ui_actions), 'ACTUAL_STAGE_ACTION_COUNT_BEFORE')
        equal(custody['uiActionCountAfter'], sum(i <= custody['commandSequenceLast'] for i in ui_actions), 'ACTUAL_STAGE_ACTION_COUNT_AFTER')
        need(custody['commandSequenceFirst'] > previous_command and custody['uiCaptureSerialFirst'] > previous_ui, 'FRESH_NONOVERLAPPING_STAGE_CUSTODY')
        previous_command, previous_ui = custody['commandSequenceLast'], custody['uiCaptureSerialLast']
        selected_time = files.doc(obs['selection'])['capturedMonotonicNs']
        need(selected_time > previous_time, 'FRESH_SELECTION_HOST_CLOCK_ORDER'); previous_time = selected_time
        events.append(event); sent.append(send)
    if role == 'archive':
        equal(events[0], events[1]); equal(sent[0], sent[1], 'IDENTICAL_ACTUAL_SENT_EVENT_BYTES')
        need(events[2]['id'] != events[0]['id'], 'FRESH_WRAP_OUTER_ID')
    # Exact proof roots are complete filesystem inventories, including late proxy
    # history and guard flags. This never enumerates userdata or SDK trees.
    for directory in ('commands', 'ui', 'evidence', 'session', 'cleanup', 'ownership'):
        folder = Path(root) / directory
        need(folder.is_dir() and not folder.is_symlink(), 'PROOF_ROOT_MISSING')
        visited = 0
        for p in folder.rglob('*'):
            visited += 1
            need(visited <= 40000, 'PROOF_TREE_VISITS_BOUND')
            need(not p.is_symlink(), 'PROOF_TREE_SYMLINK')
            mode = p.lstat().st_mode
            if stat.S_ISREG(mode):
                need(str(p) in paths, 'OMITTED_WHOLE_WINDOW_PROOF')
            elif not stat.S_ISDIR(mode):
                need(stat.S_ISSOCK(mode) and p == Path(root) / 'session/fixtures/control.sock', 'UNPLANNED_PROOF_SPECIAL_FILE')
    need(not (Path(root) / 'session/control/REVOKED').exists(), 'STICKY_REVOKED_WINDOW')
    for pin in (s['driver'], s['supervisor'], s['lease'], s['proxy'], s['phase'], *s['commands']):
        need(pin['path'] in paths, 'OPERAND_NOT_IN_WINDOW_GRAPH')
    equal(s['sourcePolicyObservations'], {'clockPolicy': 'SOURCE_ENFORCED_THREE_DOMAINS_ORIGINAL_LEASE',
          'perCommandClockChronology': 'UNKNOWN_NOT_RECORDED', 'sdkAssetsBundled': False,
          'guestHealth': 'UNKNOWN', 'businessEffectsMeasured': False})
    origin.reviews(descriptor, 'WINDOW')
    return dict(role=role, runId=s['runId'], outputRoot=root, grant=s['runRelease'], lease=s['lease'],
                cids=cids, started=tool['startedUtcNs'], finished=tool['finishedUtcNs'], exports=len(observations))


def consume(files, manifest_pin, origin_pin):
    require_current_source_profile()
    manifest = files.doc(manifest_pin)
    closed(manifest, 'schema profileId candidate history windows')
    equal(manifest['schema'], 'e02-minimum-consumption-manifest-v1'); equal(manifest['profileId'], wire.PROFILE)
    candidate = files.doc(manifest['candidate'])
    closed(candidate, 'schema profileId authors operators producerSubject producerContract adoption oracles sourceControls primaryEvidenceReferences scope')
    equal(candidate['schema'], 'e02-minimum-candidate-v1'); equal(candidate['profileId'], wire.PROFILE)
    equal(candidate['scope'], 'SUPPLEMENTAL_ORDINARY_JS_RS_ONLY_NOT_CANONICAL_E02_PASS')
    equal(candidate['producerSubject']['sha256'], PRODUCER_SHA)
    equal(candidate['producerContract']['sha256'], CONTRACT_SHA)
    equal(candidate['adoption']['sha256'], ADOPTION_SHA)
    producer = current_producer(files, candidate['producerSubject'])
    files.read(candidate['producerContract'])
    adoption = files.doc(candidate['adoption'])
    equal(adoption['decision'], 'ADOPT_DISTINCT_CRITERION_PRESERVING_MINIMUM_LAB_PROFILE_ONLY')
    for key in ('executionGranted', 'canonicalPass', 'canonicalMandatoryScopeChanged', 'dependencyGateChanged', 'architectureOrBlockersChanged'):
        equal(adoption[key], False)
    closed(candidate['oracles'], 'business chat')
    for name, expected_id in (('business', wire.BUSINESS), ('chat', wire.CHAT)):
        oracle = wire.rumor(files.doc(candidate['oracles'][name])); equal(oracle['id'], expected_id)
        frozen = next(p for p in producer['sources'] if Path(p['path']).name == name + '-rumor.json')
        equal(candidate['oracles'][name], frozen)
    history = files.doc(manifest['history'])
    closed(history, 'schema profileId declaredScope authors operators attempts legacyContexts')
    equal(history['schema'], 'e02-minimum-attempt-inventory-v1'); equal(history['profileId'], wire.PROFILE)
    equal(history['declaredScope'], 'ALL_MINIMUM_ATTEMPTS_AND_RELEVANT_LEGACY_NEGATIVE_CONTEXTS_THROUGH_THIS_INVENTORY')
    origin_value = files.doc(origin_pin)
    forbidden, attempts = provenance(files, candidate, history, origin_value)
    forbidden |= {'/root/android_health_implementer', '/root/consumer3_preparation', producer['author'], producer['coordinator']}
    forbidden |= actors(history['authors']) | actors(history['operators'])
    for p in manifest['windows']:
        s = files.doc(p); forbidden |= actors(s['authors']) | actors(s['operators'])
    controls = files.doc(candidate['sourceControls'])
    forbidden |= actors(controls['authors']) | actors(controls['operators'])
    forbidden |= actors(CURRENT_CONTROL_ACTORS)
    origin = Origin(files, origin_value, forbidden)
    equal(origin_value['method'], candidate['adoption']); equal(origin_value['candidate'], manifest['candidate'])
    equal(origin_value['history'], manifest['history']); equal(origin_value['windowSubjects'], manifest['windows'])
    origin.reviews(candidate['producerSubject'], 'SOURCE')
    control_evidence(files, candidate['sourceControls'], origin)
    origin.reviews(manifest['history'], 'HISTORY')
    contributing_attempts = [a for r, a in attempts if r['disposition'] == 'CONTRIBUTE_WHOLE_WINDOW']
    contributing = [a['windowSubject'] for a in contributing_attempts]
    equal(contributing, manifest['windows'], 'EXACT_WHOLE_WINDOW_MEMBERSHIP')
    need(len(contributing) == 2, 'EXACT_TWO_WINDOWS')
    for attempt in contributing_attempts:
        subject = files.doc(attempt['windowSubject'])
        for key in ('ordinaryRole', 'runId', 'sourceSubject'): equal(attempt[key], subject[key], 'ATTEMPT_WINDOW_LINEAGE')
        equal(attempt['rawOutcome'], subject['supervisor'], 'ACTUAL_WHOLE_ATTEMPT_OUTCOME')
    # Primary references are pinned context, never a primary-PASS assertion here.
    for p in candidate['primaryEvidenceReferences']: files.read(p)
    results = [window(files, p, candidate, origin, producer) for p in contributing]
    equal([r['role'] for r in results], ['incoming', 'archive'])
    for key in ('runId', 'outputRoot', 'grant', 'lease'):
        need(not same(results[0][key], results[1][key]), 'FRESH_SEPARATE_ROLE_WINDOWS')
    need(results[0]['finished'] <= results[1]['started'], 'SEQUENTIAL_CLEANUP_BARRIER')
    need(not results[0]['cids'] & results[1]['cids'], 'REUSED_CONTAINER_STATE')
    files.recheck()
    return dict(schema='e02-minimum-consumption-result-v2', state='SUPPLEMENTAL_DATA_CONSISTENT_WITH_EXTERNALLY_AUTHENTICATED_ORIGINS',
                profileId=wire.PROFILE, wholeWindows=2, selectedExports=5, selectedNoteContexts=3, uniqueRumorIds=2,
                canonicalE02Changed=False, canonicalE02='PARTIAL22_UNCHANGED', primaryMatrixQualified=False,
                businessEffectsMeasured=False, sdkRuntimeAdmission=False, portableProcessAttestation=False,
                nonoperativeMetadataFinding='PRODUCER3_CURRENT_REBUILT_ARTIFACT_SOURCE2_OLD_FINDING_PRESERVED',
                perCommandClockChronology='UNKNOWN_NOT_RECORDED', evidenceFiles=len(files.pins), evidenceBytes=files.total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True); parser.add_argument('--manifest-sha', required=True)
    parser.add_argument('--origin', required=True); parser.add_argument('--origin-sha', required=True)
    parser.add_argument('--read-root', action='append', required=True)
    args = parser.parse_args()
    try:
        files = Files(args.read_root)
        manifest_pin = external(files, args.manifest, args.manifest_sha)
        origin_pin = external(files, args.origin, args.origin_sha)
        result = consume(files, manifest_pin, origin_pin)
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as error:
        result = dict(schema='e02-minimum-consumption-result-v2', state='REFUSED_NO_CONTRIBUTION',
                      reason=type(error).__name__ + ':' + str(error)[:2048], canonicalE02Changed=False,
                      contributingWholeWindows=0, contributingExports=0)
        print(json_bytes(result).decode()); return 2
    print(json_bytes(result).decode()); return 0


if __name__ == '__main__':
    sys.exit(main())
