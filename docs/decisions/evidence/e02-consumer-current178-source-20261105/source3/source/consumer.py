"""Current consumer6 minimum ordinary-client evidence consumer; never canonical E02 PASS.

Invocation reads only bounded explicitly pinned DATA. It does not execute a
producer, SDK, Android, crypto, network, subprocess, tests or evidence payloads.
"""
import argparse
import ast
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
import strict
import async_guard
import parent_allocation
import capture_contracts
import capture_outputs
import current_controls
import probe_adapter
import request_families
import collector_contracts
from witness import Origin, actors, cleanup_check, commands, lease_check, ownership

# Current accepted producer266 DATA. Actual helper/consumer/window anchors remain unissued.
PRODUCER_SHA = 'd4229ef2ddf77e79a8f1a9990ea174db4c3dba9e7f2012ed42589d857be443b5'
CONTRACT_SHA = '48c683bf4c1fe23189ed9b8e0a386aa7f46346f3407dab239eb7270883603ebb'
ADOPTION_SHA = '2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287'
RUNTIME_SCOPE = 'E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V3_WINDOW_ONLY'
DRAFT_FINAL_ADAPTER_READY = False
CURRENT_PRODUCER_SCHEMA = 'e02-ordinary-producer4-source-subject-v1'
CURRENT_PRODUCER = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/subject.json', 'bytes': 41959, 'sha256': 'd4229ef2ddf77e79a8f1a9990ea174db4c3dba9e7f2012ed42589d857be443b5'}
CURRENT_SOURCE_PLAN = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/control-plan.json', 'bytes': 28451, 'sha256': '9aef9389217ced7f0b3f36fef265ca871f6b1faafb330e212764d13ff1654bcb'}
CURRENT_GUARD_DTO = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/guard-dto-contract.json', 'bytes': 14223, 'sha256': '33e3e1e9f0aab82238683563e2f7d4c15e6e8f736e5e7fdeb2722344f5b5feb6'}
CURRENT_EXPORT_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/EXPORT-CONTRACT.md', 'bytes': 43900, 'sha256': '48c683bf4c1fe23189ed9b8e0a386aa7f46346f3407dab239eb7270883603ebb'}
CURRENT_AMETHYST_APK = {'path': '/Data/nbdp-e02-tooling-20261027/amethyst-build-r8/output/build/rebuilt-fdroid-debug-0.apk', 'bytes': 165860063, 'sha256': '368255b938e8fc72bf603a3f08dee29938e6c73e43ca6471a13ee1bc9ee0b4be'}
CURRENT_HELPER_APK = {'path': '/Data/nbdp-e02-tooling-20261027/clipboard-helper-current-build-20261105/clipboard-capture.apk', 'bytes': 16787, 'sha256': 'ab6e2628677d563fe3214e92ef1f25942aaf5e720de974db77bd4927beca2f83'}
CURRENT_ARTIFACT_BINDINGS = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/rebuilt-artifact-bindings.json', 'bytes': 5403, 'sha256': '6ba218be6e2b4b1b5a5e41bbcc04ae28d9fc592b05698d1afb436e1e2c45727b'}
CURRENT_CONFIGURATIONS = [{'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/incoming-run-config.json', 'bytes': 7999, 'sha256': 'f3214436e47697639352411cc5f92a4cd3087bbacd46ca7c4b50800c8256062f'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/archive-run-config.json', 'bytes': 7997, 'sha256': 'e63effb83579dbcec4034476406bfadd401bcce74870be11fddea03c12fc80b3'}]
CURRENT_WORKERS = [{'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/supervisor.py', 'bytes': 58020, 'sha256': '211c06f76625c59f2980ef3a9e3c57d03c5aca37474ae530837f728269eed0c9'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/lease_guard.py', 'bytes': 14846, 'sha256': 'd396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/android_driver.py', 'bytes': 49174, 'sha256': '6db92e1232eaf88860ab39a0ba1d027c330c6ac0917ec530f18754d3e0e97d85'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/ui-plan.json', 'bytes': 1482, 'sha256': '5beed690b07722aaa6a4bb3115b3b62da1c8b079d581325f26ad53bd66727f3a'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/fixture.mjs', 'bytes': 45130, 'sha256': '7294668da0e4c1fe92efc11c9cc43eab8e3d1e5c1a83c9bed0d72a224463d256'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/fixture-plan.json', 'bytes': 251848, 'sha256': '34ce27f72bfe98ee6f4488e8cc248ed351822d1ec31c9cca851cb9308fd9e4d1'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/minimum-plan.json', 'bytes': 1562, 'sha256': 'f82b59a6fadf311da81916b85e8e9ec399ad94004e54c07fbc4cfbed46d9205c'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/business-rumor.json', 'bytes': 910, 'sha256': '8bb0efcf8cc5a503e8f653885503958520f1a069066e549cd60dec7128d25291'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/chat-rumor.json', 'bytes': 384, 'sha256': 'f796df4b3ad76f832248fb60bdfb0d134a830257e95c0559b44d4fce0a900dc5'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/exchange.mjs', 'bytes': 6662, 'sha256': 'e3e962230a7adc84c495c23b0724ad6a1c8f366dd0e0376fc53cbaf00f1eb5dc'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/phase-writer.mjs', 'bytes': 2085, 'sha256': 'bcfb3338d1ab8cbb20709f6add09a2e7be01a270f48271112e3aa3a76743cead'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/dependency-tree.mjs', 'bytes': 2842, 'sha256': '0b574a14e591abc1908f4733908001d8ea1ab5698da8991e618ca26714eeded3'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/dependency-tree.json', 'bytes': 35599, 'sha256': '0536b9b0f6a127e3e43fd19bf5df0e3110b5c437e1a2c22c76e1a3e8dcc4f07f'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/capture-budget.mjs', 'bytes': 8963, 'sha256': '7e75aa2e0fcf1233a5d04cb899bde1ae6ff8a581bb8f57747e9115bf0993e312'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/exchange-adapter.mjs', 'bytes': 1012, 'sha256': '4e03f6449defff4585b532572ca3f0ef254dc76f056079ce85c2266de9f50aef'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/proxy-observer.mjs', 'bytes': 4478, 'sha256': 'fb17d34d3dea46c62bf29ed537684936b3a2871643b6d4fe3c16c88ffa37d0a1'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/guard-helper.py', 'bytes': 6219, 'sha256': '743e0ed269445a4d59407336e399d1c7bd46c5337408b157e9ef85773e2157cf'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/guard-wire.mjs', 'bytes': 1921, 'sha256': '8cf473b741d631f80ef785c86acf5caa9899d03206696a8f740db08878c02d8e'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/guard-client-core.mjs', 'bytes': 8072, 'sha256': '14be5abb1ff953d2336e841e1364acdfd8275874ffed3aef88f9a9489fac1083'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/guard-client.mjs', 'bytes': 9308, 'sha256': '50d3dacdc0e3a008ea15bc510004ff2bf805f3de195785eb25a241f678a1dfb0'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/guard-transport-boundaries.mjs', 'bytes': 4978, 'sha256': 'c4c5cda6107cdead8715da8bdba917a31ebabadc0249d8fba0b343a718f98068'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/capture-allocation.mjs', 'bytes': 7437, 'sha256': 'a86180100f6f4fee691bd177f557fbc3a4573ccc9d0f3f15ee66a32c1b8e57a7'}]
CURRENT_PRODUCER_SOURCE_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifact-source-review-20261105/acceptance.json', 'bytes': 1212, 'sha256': '277c4b31273e8e4c703a7fec54f5311ed159e4995d351a3c9017687006b51cdb'}
CURRENT_CAPTURE_SOURCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-capture-20261105/source1/capture/code-subject.json', 'bytes': 8987, 'sha256': '1a2bfdc92a68270d0712d7ad0f2107d407847c633d78869cdb0ed09bd343a719'}
CURRENT_CAPTURE_SOURCE_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-capture-review-20261105/acceptance.json', 'bytes': 1403, 'sha256': '4c162f496912bcd9b8b96ca4f4468306265ca6d51a0d879825693067930ea762'}
CURRENT_ADMISSION_DATA_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-current-capture-admission33-model-20261105/acceptance.json', 'bytes': 2029, 'sha256': '5f266908363e444969dbae24e588d67d912c2c9c9d6c1b83ff16afdcee794165'}
CURRENT_DATA_ACCEPTANCE_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-capture-20261105/source1/capture/contracts/current-producer-data-acceptance-contract-266.json', 'bytes': 2947, 'sha256': '17fea039fdcc88c5aa325e083337a702e8ae37852ae297adaebf3d39bc185fb9'}
CURRENT_CONTROL_ACTORS = ['/root', '/root/collector_policy_security_553c5bfd', '/root/collector_r4_fresh_security_bcf7ccfa57b4', '/root/collector_r5_fresh_qa_c05985fce1ea', '/root/collector_r5_fresh_security_c05985fce1ea', '/root/collector_typed_qa_1592707b', '/root/collector_typed_security_1592707b', '/root/completion_wrapper', '/root/consumer266_source', '/root/consumer6_s4_fresh_qa_6716777dfdd7', '/root/consumer6_s4_fresh_security_6716777dfdd7', '/root/consumer6_source', '/root/consumer_current178_source', '/root/consumer_source2_qa_70b36984', '/root/consumer_source2_security_70b36984', '/root/consumer_source_qa_e0e55c4e', '/root/consumer_source_security_e0e55c4e', '/root/controller_current_source_r9', '/root/controller_model_metadata_source2', '/root/controller_r9_qa_e7c43daa', '/root/controller_r9_security_e7c43daa', '/root/guard_recovery_source', '/root/helper_apk_binding_scope', '/root/helper_controller_source6_env', '/root/helper_env_removal_sources', '/root/helper_policy_source7', '/root/helper_r6_binding', '/root/lease_fix_binding_scope', '/root/native_rebuild_prepare', '/root/probe_concrete_path_composition', '/root/probe_r6_fresh_qa_d81b6f3ae5d8', '/root/probe_r6_fresh_security_d81b6f3ae5d8', '/root/probe_r7_fresh_qa_8d291e97745f', '/root/probe_r7_fresh_security_8d291e97745f', '/root/producer4_nonblocking_source', '/root/r5_plan_fix', '/root/root_failstop_bridge_source']
CURRENT_PRODUCER_CONTROL_DATA = {'path': '/Data/nbdp-e02-tooling-20261027/assembled/subject.json', 'bytes': 3653, 'sha256': 'e4a2b8da6d5aee04e08f98ebb508957a3639ec32c0cfe9a3089983a16e3a5e9e'}
CURRENT_PRODUCER_CONTROL_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-current-producer266-data-20261105/acceptance.json', 'bytes': 3716, 'sha256': '91a00b4ec693c7c776a031849d61ab676ceaeed4262085ba0a6fc1b6e81b2d6f'}
CURRENT_HELPER_PROBE_DATA = None
CURRENT_HELPER_PROBE_ACCEPTANCE = None

CURRENT_HELPER_PROBE_ACCEPTANCE_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-helper-current178-source-20261105/source1/helper-probe-data-acceptance-contract.json', 'bytes': 3325, 'sha256': '14f859491411c84ec03bc552f0be287269f6ff94a9d4b43cf7cdf22e650fdacc'}
CURRENT_HELPER_PROBE_SHAPE_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-helper-probe-preparation-20261028/helper-probe-data-shape-contract.json', 'bytes': 2257, 'sha256': 'f1540a48582132fd8fa14a302df66defc0baed4354e347c4ed47f7630a32059b'}

CURRENT_CONSUMER_ACCEPTANCE_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-current178-source-20261105/source3/contracts/current-consumer-acceptance-contract.json', 'bytes': 4612, 'sha256': '468996d45865499784f17762a33f698f1f82877628af7b803cbb94f170d3b674'}
HISTORICAL_HELPER_CONTROLLER_SOURCE = {'path': '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r4/subject.json', 'bytes': 18686, 'sha256': '5b2e78aa6780c0983f5bc1990d8e1490b03a74860c754951826a9120ce782a26'}
HISTORICAL_HELPER_CONTROLLER_SOURCE_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-controller-r4-source-acceptance-20261029/acceptance.json', 'bytes': 1231, 'sha256': 'b10881f06dc0aacae0989cbcf1a9336222f3a51581feefdbc01d59f2efab83c8'}
HISTORICAL_HELPER_CONTROLLER_CONTROL_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-controller-r4-model104-actual-20261029/acceptance.json', 'bytes': 2096, 'sha256': 'f9aed9dbe356ff0ffa74b932b091ae7d057d7a9498cc1e6e8e495b2ae16bd761'}

CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-helper-probe-preparation-20261028/current-controller-acceptance-contract.json', 'bytes': 3204, 'sha256': '5d882ebdf7e3df7b72f941df2ff0ef561f4f221fde5771af5ce7c8e2d7d2d437'}

CURRENT_NATIVE = {'path': '/Data/nbdp-e02-tooling-20261027/native-rebuild-20261104/a7f5f03265b6f8facb3b1670c716c847/artifact/nbdp-experiment-rust', 'bytes': 24100272, 'sha256': '4ce385c5b1a713b35d58d787d94fbc298d139aa2e813daec15b2e99289cefd86'}
CURRENT_NATIVE_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-native-rebuild-review-20261105/r1-native-build-acceptance.json', 'bytes': 2139, 'sha256': 'c6723c5692b17108221a3c9502ea66ae411e8eaf821db7b67f66fa431a533a59'}
CURRENT_E01_REPORT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e01-native-current-replay-20261105/actual/E01.json', 'bytes': 33643, 'sha256': 'c9af82d05b4741dafdbed10789b80793b0bd8fbb2916d3a8e17f9066bba57f3e'}
CURRENT_E01_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e01-native-current-replay-20261105/actual-acceptance.json', 'bytes': 2453, 'sha256': '55362e2bcc3a1aaf854d5714c853ec941634ff5abca80bcff75398832a3e4eb6'}
CURRENT_COLLECTOR_SOURCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-current-policy-20261105/source2/source-subject.json', 'bytes': 13573, 'sha256': '35ad47f9563814903a6f0ac088084431fe33dd8ab431de643341545852c79be9'}
CURRENT_COLLECTOR_SOURCE_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-current-policy-review-20261105/source2/acceptance.json', 'bytes': 1224, 'sha256': '3365ed3a2761adb656768f7b2980b67667510e91ce459be9be9fb3a3e7405bb9'}
CURRENT_COLLECTOR_DATA = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-typed81-model-20261105/subject.json', 'bytes': 2839, 'sha256': '314e2d4e6c46e673bc33fbfc729c76e85de09c72bc9e25386fafe425897d92d0'}
CURRENT_COLLECTOR_DATA_ACCEPTANCE = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-typed81-model-20261105/acceptance.json', 'bytes': 2117, 'sha256': 'cdc427fed141908e61f36d0edc3abdbae6e1890d2c07fce59e1e95f135802673'}
CURRENT_COLLECTOR_PREREQUISITE_CONTRACT = {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-current178-source-20261105/source3/contracts/current-collector-prerequisite-contract.json', 'bytes': 8594, 'sha256': '19132d969f4f29aca3cc4919132b22c57221923001f6ecd84f350ff189f0539f'}

_ACTIVE_BINDINGS = None
BINDING_KEYS = 'schema actor producerSource producerSourceAcceptance producerControlData producerControlAcceptance helperProbeData helperProbeAcceptance controllerSource controllerSourceAcceptance controllerControlDataAcceptance consumerSource consumerSourceAcceptance consumerControlData consumerControlAcceptance incomingWindow archiveWindow ordinaryExports readiness issued executionAuthorized'

CONFIG_KEYS = 'runtimeImage relayImage sdkRoot amethystApk helperApk schema scope profileId ordinaryRole windowId account peer runId originalLeaseSeconds sourceAndDependencyPins sdkInventory guardBundleInventory guardBundleRoot relayConfig state canonicalE02'
WINDOW_KEYS = 'schema profileId ordinaryRole windowId runId outputRoot authors operators sourceSubject supervisorSource runConfig runRelease resource sourceControls outer lease driver supervisor commands ui proxy phase readOnlyMountBindings graphFiles excludedFiles sourcePolicyObservations'
DRIVER_KEYS = 'schema profileId windowId ordinaryRole runId runConfig runRelease executionState accountIdentityGUI expectedAccountPubkey accountIdentityQualification torConfigurationGUI environmentAnrEvidence allUICaptures fixtureCalls observations limits canonicalE02Changed'
OBS_KEYS = 'id state selection uiPng uiXml rawClientRumor clipboardClear visibleMatchingTextNodeCount duplicateObservation expectedRumor publication actualNewAppFrameObserved originalGuestToHostBindings subscriptionStatus subscriptionStatusReply subscriptionStatusCall subscriptionStatusCommand custodySegment'


def require_current_source_profile():
    need(_ACTIVE_BINDINGS is not None and DRAFT_FINAL_ADAPTER_READY is True,
         'CONSUMER6_SOURCE_ONLY_NO_CURRENT_RUNTIME_BINDINGS')
    need(all(p is not None for p in (CURRENT_PRODUCER_CONTROL_DATA,CURRENT_PRODUCER_CONTROL_ACCEPTANCE,
         CURRENT_HELPER_PROBE_DATA,CURRENT_HELPER_PROBE_ACCEPTANCE)), 'CURRENT266_AND_ACTUAL_HELPER_PROBE_DATA_REQUIRED')


# Fixed CODE membership; mutable authority/bindings are separate acyclic leaves.
RUNTIME_FILES = ('consumer.py', 'strict.py', 'wire.py', 'gui.py', 'witness.py', 'observer.py', 'async_guard.py', 'parent_allocation.py', 'capture_contracts.py', 'capture_outputs.py', 'current_controls.py', 'probe_adapter.py', 'request_families.py', 'collector_contracts.py')
CONTROL_FILES = ('test_data_controls.py', 'test_async_guard.py', 'test_parent_allocation.py', 'test_observer_v3.py', 'test_source_bindings.py', 'test_current_controls.py', 'test_probe_adapter.py', 'test_whole_window.py', 'test_current_authority.py', 'test_request_families.py', 'test_import_closure.py')
CODE_FILES = tuple(sorted((*RUNTIME_FILES,*CONTROL_FILES,'model_stage.py','whole_window.py',
    'prepare_consumer_edit.py','prepare_observer_edit.py','strict_raw_method.txt',
    'whole_window_methods.txt','current_authority_methods.txt','README.md')))
CONTROL_DATA_KEYS = 'schema authors operators consumerSource consumerSourceAcceptance controlPlan producerSource producerControlAcceptance execution originalToolOrigin rawArtifactManifest countsSeparate modelsDefined modelsExecuted modelsPassed modelsFailed skipped truncated inputsUnchanged helperExecutions dockerExecutions ordinaryRoleExecutions ordinaryRowsQualified'
CONTROL_EXECUTION_KEYS = 'schema consumerSource controlPlan groups countsSeparate modelsExecuted modelsPassed modelsFailed skipped truncated inputsBefore inputsAfter inputsUnchanged scope innerPidReapEofAttested'
CONTROL_GROUP_KEYS = 'name source count definitionNames request originalToolOrigin rawOutput exitCode scope innerPidReapEofAttested'


def current_code_profile(files,descriptor):
    """Verify external subject against actual current loaded CODE and test bytes."""
    import ast
    source=files.doc(descriptor)
    equal(source['schema'],'e02-ordinary-consumer6-source-subject-v1');equal(source['version'],'SOURCE4')
    here=Path(__file__).resolve().parent;equal(source['sourceRoot'],str(here),'RUNNING_CURRENT_CONSUMER_SOURCE_ROOT')
    equal(source['sourceCount'],len(CODE_FILES));equal(source['runtimeSourceCount'],len(RUNTIME_FILES))
    declared=source['sources'];need(type(declared) is list,'CLOSED_CURRENT_CODE_MEMBER_LIST')
    by_name={Path(p['path']).name:p for p in declared}
    equal(len(by_name),len(declared));equal(sorted(by_name),list(CODE_FILES),'EXACT_CURRENT_DECLARED_CODE_AND_MODELS')
    bodies={}
    for name in CODE_FILES:
        p=by_name[name];pin_shape(p);equal(p['path'],str(here/name),'EXACT_CURRENT_MEMBER_PATH')
        bodies[name]=files.read(p)
    equal(source['runtimeSources'],[by_name[name] for name in RUNTIME_FILES],'EXACT_CURRENT_RUNTIME_PINS')
    for name in RUNTIME_FILES:
        module=sys.modules[__name__] if name=='consumer.py' else sys.modules.get(name[:-3])
        need(module is not None and Path(module.__file__).resolve()==here/name,'ACTUAL_LOADED_RUNTIME_MODULE_PATH:'+name)
    equal(source['producerSource'],CURRENT_PRODUCER);equal(source['producerControlAcceptance'],CURRENT_PRODUCER_CONTROL_ACCEPTANCE)
    equal(source['producerRuntimeWorkerCount'],22);equal(source['producerSourceMemberCount'],64)
    plan=files.doc(source['controlPlan']);equal(plan['schema'],'e02-consumer6-model-control-plan-v1')
    groups=plan['groups'];equal([g['name'] for g in groups],list(CONTROL_FILES),'ALL_CURRENT_ORDERED_CONTROL_GROUPS')
    counts=[]
    for group in groups:
        closed(group,'name source count definitionNames argv cwd format definitionScope')
        name=group['name'];equal(group['source'],by_name[name]);equal(group['cwd'],str(here))
        equal(group['argv'],['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(here/name),'-v'])
        tree=ast.parse(bodies[name],filename=str(here/name))
        methods=[cls.name+'.'+method.name for cls in tree.body if isinstance(cls,ast.ClassDef)
            for method in cls.body if isinstance(method,ast.FunctionDef) and method.name.startswith('test_')]
        equal(group['definitionNames'],methods,'ACTUAL_CURRENT_SOURCE_METHOD_PARTITION')
        integer(group['count'],1,10000);equal(group['count'],len(methods))
        equal(group['format'],'EXACT_VERBOSE_UNITTEST_NAMES');counts.append(group['count'])
    total=sum(counts);equal(source['modelsDefined'],{g['name']:g['count'] for g in groups})
    equal(source['modelDefinitions'],total);equal(source['modelGroups'],len(groups))
    equal(plan['modelsDefined'],total);equal(plan['modelsExecuted'],0)
    return source,plan,counts,total


def named_unittest_output(raw,group):
    """All named successes, exact count/trailer; skip/failure/truncation refuses."""
    need(type(raw) is bytes and len(raw)<=1048576,'BOUNDED_MODEL_API_OUTPUT')
    text_value=raw.decode('utf8','strict')
    trailer=re.search(r'\n\n-{70}\nRan ([0-9]+) tests? in [0-9]+(?:\.[0-9]+)?s\n\nOK\n\Z',text_value)
    need(trailer is not None and int(trailer[1])==group['count'],'EXACT_COMPLETE_NAMED_UNITTEST_TRAILER')
    lines=text_value[:trailer.start()].splitlines();names=[]
    for line in lines:
        match=re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*) \(__main__\.([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_][A-Za-z_0-9]*)\) \.\.\. ok',line)
        need(match is not None and match[1]==match[3],'EVERY_CURRENT_MODEL_NAMED_SUCCESS')
        names.append(match[2]+'.'+match[3])
    equal(names,sorted(group['definitionNames']),'ALL_CURRENT_MODEL_NAMES_ONCE')


def current_control_request(group):
    import shlex
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
        '/usr/bin/timeout','--signal=KILL','63s',*group['argv']]
    return dict(cmd=shlex.join(argv),workdir=group['cwd'],login=False,yield_time_ms=1000,max_output_tokens=20000)


def control_actor_union(files,value):
    from probe_adapter import source_actors,data_actors,participant_union
    source=files.doc(value['consumerSource']);data=files.doc(value['consumerControlData'])
    probe=files.doc(value['helperProbeData'])
    triple={key:value[key] for key in ('controllerSource','controllerSourceAcceptance','controllerControlDataAcceptance')}
    for key,expected in triple.items():pin_shape(expected);equal(probe[key],expected,'EXACT_EXTERNAL_CURRENT_CONTROLLER_TRIPLE')
    union=set(CURRENT_CONTROL_ACTORS)|source_actors(source)|data_actors(data)
    union|=participant_union(files,probe,union)
    probe_adapter.validate_controller_authority(files,triple,CURRENT_PRODUCER,CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT,union)
    return union


def validate_current_consumer_authority(files,value):
    """Actual current self/partition/typed acceptances before readiness activation."""
    import capture_contracts as cc
    contract=files.doc(CURRENT_CONSUMER_ACCEPTANCE_CONTRACT)
    source,plan,counts,total=current_code_profile(files,value['consumerSource'])
    source_acceptance=files.doc(value['consumerSourceAcceptance']);data=files.doc(value['consumerControlData']);acceptance=files.doc(value['consumerControlAcceptance'])
    union=control_actor_union(files,value)  # Complete union BEFORE either pair.
    src=contract['source'];closed(source_acceptance,' '.join(src['closedKeys']))
    for k,v in src['literals'].items():equal(source_acceptance[k],v,'EXACT_CURRENT_CONSUMER_SOURCE_ACCEPTANCE')
    for k,v in [('subject',value['consumerSource']),('producerSource',CURRENT_PRODUCER),('producerControlAcceptance',CURRENT_PRODUCER_CONTROL_ACCEPTANCE),('runtimeSourceCount',len(RUNTIME_FILES)),('sourceCount',source['sourceCount']),('modelsDefined',total)]:equal(source_acceptance[k],v,'CURRENT_SOURCE_PARTITION_JOIN')
    cc.reviews([files.doc(p) for p in source_acceptance['reviews']],source_acceptance['reviews'],value['consumerSource'],src['reviewDecision'],union)
    closed(data,CONTROL_DATA_KEYS);equal(data['schema'],contract['data']['subjectSchema'])
    for k,v in [('consumerSource',value['consumerSource']),('consumerSourceAcceptance',value['consumerSourceAcceptance']),('controlPlan',source['controlPlan']),('producerSource',CURRENT_PRODUCER),('producerControlAcceptance',CURRENT_PRODUCER_CONTROL_ACCEPTANCE),('countsSeparate',counts),('modelsDefined',total),('modelsExecuted',total),('modelsPassed',total),('modelsFailed',0),('skipped',0),('truncated',False),('inputsUnchanged',True),('helperExecutions',0),('dockerExecutions',0),('ordinaryRoleExecutions',0),('ordinaryRowsQualified',0)]:equal(data[k],v,'CURRENT_COMPLETE_CONTROL_DATA_JOIN')
    rule=contract['data'];closed(acceptance,' '.join(rule['closedKeys']))
    for k,v in rule['literals'].items():equal(acceptance[k],v,'EXACT_CURRENT_CONSUMER_CONTROL_ACCEPTANCE')
    for k,v in [('subject',value['consumerControlData']),('consumerSource',value['consumerSource']),('consumerSourceAcceptance',value['consumerSourceAcceptance']),('controlPlan',source['controlPlan']),('producerSource',CURRENT_PRODUCER),('producerControlAcceptance',CURRENT_PRODUCER_CONTROL_ACCEPTANCE),('countsSeparate',counts),('modelsDefined',total),('modelsExecuted',total),('modelsPassed',total)]:equal(acceptance[k],v,'CURRENT_ROOT_DATA_SOURCE_AND_PARTITION_JOIN')
    cc.reviews([files.doc(p) for p in acceptance['reviews']],acceptance['reviews'],value['consumerControlData'],rule['reviewDecision'],union)
    execution=files.doc(data['execution']);closed(execution,CONTROL_EXECUTION_KEYS)
    for k,v in [('schema','e02-consumer6-control-execution-v1'),('consumerSource',value['consumerSource']),('controlPlan',source['controlPlan']),('countsSeparate',counts),('modelsExecuted',total),('modelsPassed',total),('modelsFailed',0),('skipped',0),('truncated',False),('inputsUnchanged',True),('scope','API_ONLY_MOCK_OR_READ_ONLY_MODELS_NO_TARGET_RUNTIME'),('innerPidReapEofAttested',False)]:equal(execution[k],v,'ACTUAL_CURRENT_MODEL_EXECUTION_JOIN')
    before=files.doc(execution['inputsBefore']);after=files.doc(execution['inputsAfter']);equal(before,after,'EXACT_EXPECTED_INPUTS_UNCHANGED')
    closed(before,'schema rows');equal(before['schema'],'e02-consumer6-current-inputs-v1')
    need(type(before['rows']) is list and before['rows'],'EXPLICIT_EXPECTED_MODEL_INPUT_SNAPSHOT')
    rows={r['pin']['path']:r for r in before['rows']};equal(len(rows),len(before['rows']))
    for row in before['rows']:
        closed(row,'pin mode uid gid device inode mtimeNs ctimeNs');pin_shape(row['pin']);integer(row['mode'],0,4095);integer(row['uid']);integer(row['gid'])
        for field in ('device','inode','mtimeNs','ctimeNs'):need(type(row[field]) is str and re.fullmatch(r'[0-9]{1,24}',row[field]),'EXACT_SNAPSHOT_IDENTITY_DECIMAL')
    declared_inputs=files.doc(source['inputManifest'])
    required=[*source['sources'],source['controlPlan'],source['inputManifest'],value['consumerSource'],value['consumerSourceAcceptance'],*declared_inputs['fixedSourceAndCurrentDataOperands']]
    for p in required:
        need(p['path'] in rows,'EVERY_CURRENT_CODE_TEST_PLAN_INPUT_SNAPSHOTTED');equal(rows[p['path']]['pin'],p,'EXPECTED_INPUT_HASH_NOT_OBSERVED_BASELINE')
    origin_index=files.doc(data['originalToolOrigin']);closed(origin_index,'schema origins')
    equal(origin_index['schema'],'e02-consumer6-control-api-index-v1');equal(len(origin_index['origins']),len(plan['groups']))
    groups=execution['groups'];equal(len(groups),len(plan['groups']))
    manifest=files.doc(data['rawArtifactManifest']);closed(manifest,'schema files originalToolOrigin')
    equal(manifest['schema'],'e02-consumer6-control-raw-manifest-v1');equal(manifest['originalToolOrigin'],data['originalToolOrigin'])
    need(type(manifest['files']) is list and 1<=len(manifest['files'])<=20000,'FINITE_CURRENT_CONTROL_RAW_MANIFEST')
    index={p['path']:p for p in manifest['files']};equal(len(index),len(manifest['files']))
    need(data['rawArtifactManifest']['path'] not in index,'NO_CURRENT_CONTROL_MANIFEST_SELF_CYCLE')
    for p in manifest['files']:files.read(p)
    for p in [data['execution'],data['originalToolOrigin'],execution['inputsBefore'],execution['inputsAfter']]:equal(index.get(p['path']),p,'ALL_CURRENT_PROOF_MANIFEST_MEMBERS')
    for expected,row,entry in zip(plan['groups'],groups,origin_index['origins']):
        closed(row,CONTROL_GROUP_KEYS);closed(entry,'group origin')
        for k,v in [('name',expected['name']),('source',expected['source']),('count',expected['count']),('definitionNames',expected['definitionNames']),('request',current_control_request(expected)),('exitCode',0),('scope','API_ONLY_MOCK_OR_READ_ONLY_MODELS_NO_TARGET_RUNTIME'),('innerPidReapEofAttested',False)]:equal(row[k],v,'ORDERED_CURRENT_API_MODEL_GROUP')
        equal(entry['group'],row['name']);equal(entry['origin'],row['originalToolOrigin'])
        for p in (row['originalToolOrigin'],row['rawOutput']):equal(index.get(p['path']),p,'COMPLETE_GROUP_RAW_MANIFEST_MEMBER')
        api=cc.decode_tool_origin(files.read(row['originalToolOrigin']))
        actual=cc.validate_origin(api,row['request'],data['operators'],family='MODEL5').encode('utf8')
        equal(files.read(row['rawOutput']),actual,'COMPLETE_GENUINE_GROUP_API_OUTPUT')
        named_unittest_output(actual,expected)
    return source,plan,counts,total,union


def bind_current_profile(files,descriptor):
    """External Root SHA-bound DATA leaf, excluded from frozen CODE to avoid cycles."""
    global _ACTIVE_BINDINGS,DRAFT_FINAL_ADAPTER_READY,CURRENT_HELPER_PROBE_DATA,CURRENT_HELPER_PROBE_ACCEPTANCE
    need(_ACTIVE_BINDINGS is None,'ONE_EXTERNAL_BINDINGS_ACTIVATION_PER_PROCESS')
    value=files.doc(descriptor);closed(value,BINDING_KEYS)
    equal(value['schema'],'e02-consumer6-runtime-bindings-v1');equal(value['actor'],'/root')
    equal(value['readiness'],True,'UNREADY_BINDINGS_REFUSE_BEFORE_TARGET_READS');equal(value['issued'],True)
    equal(value['executionAuthorized'],False,'DATA_INSPECTION_NOT_RUNTIME_RELEASE')
    for key,expected in [('producerSource',CURRENT_PRODUCER),('producerSourceAcceptance',CURRENT_PRODUCER_SOURCE_ACCEPTANCE),('producerControlData',CURRENT_PRODUCER_CONTROL_DATA),('producerControlAcceptance',CURRENT_PRODUCER_CONTROL_ACCEPTANCE)]:equal(value[key],expected,'EXACT_CURRENT_SOURCE_AND_ACTUAL266_BINDING')
    for key in BINDING_KEYS.split()[2:-3]:
        if key!='ordinaryExports':pin_shape(value[key])
    need(type(value['ordinaryExports']) is list and len(value['ordinaryExports'])==5,'FIVE_ACTUAL_EXPORT_PINS_REQUIRED')
    for p in value['ordinaryExports']:pin_shape(p)
    validate_current_consumer_authority(files,value)
    _ACTIVE_BINDINGS=value;CURRENT_HELPER_PROBE_DATA=value['helperProbeData'];CURRENT_HELPER_PROBE_ACCEPTANCE=value['helperProbeAcceptance'];DRAFT_FINAL_ADAPTER_READY=True
    return value


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
    return producer


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



def control_evidence(files,descriptor,origin):
    require_current_source_profile()
    value=files.doc(descriptor)
    closed(value,'schema profileId authors operators producerSubject producerControls helperProbe consumerSource consumerControls')
    equal(value['schema'],'e02-minimum-controls-subject-v4');equal(value['profileId'],wire.PROFILE)
    equal(value['producerSubject'],CURRENT_PRODUCER)
    equal(value['producerControls'],dict(subject=CURRENT_PRODUCER_CONTROL_DATA,acceptance=CURRENT_PRODUCER_CONTROL_ACCEPTANCE))
    equal(value['helperProbe'],dict(subject=CURRENT_HELPER_PROBE_DATA,acceptance=CURRENT_HELPER_PROBE_ACCEPTANCE))
    origin.forbidden|=actors(value['authors'])|actors(value['operators'])|actors(CURRENT_CONTROL_ACTORS)
    own_source=files.doc(value['consumerSource']);own_controls=files.doc(value['consumerControls'])
    origin.forbidden|=actors(own_source['sourceContributors'])|{own_source['author'],own_source['coordinator']}|actors(own_controls['authors'])|actors(own_controls['operators'])
    # Close the entire current helper/consumer union before every current review pair.
    probe=files.doc(value['helperProbe']['subject'])
    from probe_adapter import participant_union,validate as validate_probe
    origin.forbidden|=participant_union(files,probe,origin.forbidden)
    origin.forbidden |= probe_adapter.validate_collector_authority(files, CURRENT_COLLECTOR_PREREQUISITE_CONTRACT, origin.forbidden)
    from current_controls import validate_data
    validate_data(files,value['producerControls'],origin,CURRENT_PRODUCER,CURRENT_PRODUCER_SOURCE_ACCEPTANCE,
        CURRENT_CAPTURE_SOURCE,CURRENT_CAPTURE_SOURCE_ACCEPTANCE,CURRENT_ADMISSION_DATA_ACCEPTANCE,CURRENT_DATA_ACCEPTANCE_CONTRACT)
    validate_probe(files,value['helperProbe'],origin,CURRENT_PRODUCER,CURRENT_PRODUCER_CONTROL_ACCEPTANCE,CURRENT_HELPER_PROBE_ACCEPTANCE_CONTRACT,CURRENT_HELPER_PROBE_SHAPE_CONTRACT,expected_controller=dict(source=_ACTIVE_BINDINGS['controllerSource'],sourceAcceptance=_ACTIVE_BINDINGS['controllerSourceAcceptance'],controlAcceptance=_ACTIVE_BINDINGS['controllerControlDataAcceptance']))
    origin.reviews(value['helperProbe']['subject'],'HELPER_PROBE')
    equal(value['consumerSource'],_ACTIVE_BINDINGS['consumerSource']);equal(value['consumerControls'],_ACTIVE_BINDINGS['consumerControlData'])
    for key in ('consumerSource','consumerControls'):files.read(value[key])
    origin.reviews(value['consumerSource'],'CONSUMER_SOURCE');origin.reviews(value['consumerControls'],'CONSUMER_CONTROL')
    origin.reviews(descriptor,'CONTROL')
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
        equal(c['schema'], 'e02-minimum-fixture-call-v2'); equal(c['profileId'], wire.PROFILE)
        equal(c['windowId'], driver['windowId']); equal(c['ordinal'], ordinal)
        need(c['operation'] in ('prepare', 'status', 'publish'), 'CLOSED_FIXTURE_OPERATION')
        seq = c['commandSequence']; integer(seq, last + 1, len(command_rows)); last = seq
        equal(files.doc(c['command']), command_rows[seq - 1]); calls[seq] = (descriptor, c)
        argv = command_rows[seq - 1]['argv']
        need(len(argv)==8 and argv[:3]==['/usr/bin/docker','exec','--env'] and
             argv[3]=='NBDP_CONTROLLER_AUDIT_SLOT='+str(ordinal) and
             argv[5:]==['/usr/local/bin/node','/input/fixture.mjs',c['operation']],'ACTUAL_FIXED_ASSIGNED_SLOT_FIXTURE_COMMAND')
        equal(c['reply'],command_rows[seq-1]['stdout'],'EXACT_SHARED_RPC_REPLY_PIN')
        equal(files.read(c['reply']), files.read(command_rows[seq - 1]['stdout']))
        reply = files.doc(c['reply'])
        closed(reply, 'schema profileId windowId operation caseId ok result guardController')
        equal(reply['schema'], 'e02-minimum-fixture-command-v3'); equal(reply['profileId'], wire.PROFILE)
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


def window(files,descriptor,candidate,origin,producer):
    require_current_source_profile()
    return _window_data(files,descriptor,candidate,origin,producer)


def _window_data(files, descriptor, candidate, origin, producer):
    """Shared strict window DATA validator; synthetic controls call this body only.

    Real contribution always goes through consume/current authority/window gates.
    """
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
    need(any(same(s['runConfig'], p) for p in producer['configurations'].values()), 'FROZEN_REVIEWED_ROLE_CONFIGURATION')
    equal(config['schema'], 'e02-ordinary-minimum-role-runtime-plan-v2')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId'): equal(config[key], s[key])
    equal(config['account'], wire.ACCOUNTS[role]); equal(config['peer'], wire.A if role == 'incoming' else wire.B)
    integer(config['originalLeaseSeconds'], 60, 1800)
    source_by_name = {Path(p['path']).name: p for p in producer['sources']}
    expected_sources = producer['runtimeSources']
    equal(len(expected_sources),22,'WHOLE_CURRENT22_WORKERS')
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
    from parent_allocation import validate_parent
    helper_pin=next(p for p in producer['runtimeSources'] if Path(p['path']).name=='guard-helper.py')
    controller_instances=validate_parent(files,s,command_rows,calls,helper_pin)
    proxy = wire.Proxy(files, s['proxy'])
    trace = observer.Trace(files, s, proxy)
    need(trace.guards.instance not in controller_instances,'DISTINCT_SERVE_AND_CONTROLLER_HELPER_INSTANCES')
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
                cids=cids, started=tool['startedUtcNs'], finished=tool['finishedUtcNs'], exports=len(observations),
                exportPins=[files.resolved(obs['rawClientRumor']) for obs in observations])


def consume(files, manifest_pin, origin_pin, bindings_pin=None):
    if bindings_pin is not None:bind_current_profile(files,bindings_pin)
    require_current_source_profile()
    manifest = files.doc(manifest_pin)
    closed(manifest, 'schema profileId candidate history windows')
    equal(manifest['schema'], 'e02-minimum-consumption-manifest-v1'); equal(manifest['profileId'], wire.PROFILE)
    equal(manifest['windows'],[_ACTIVE_BINDINGS['incomingWindow'],_ACTIVE_BINDINGS['archiveWindow']],'ROOT_CLOSED_TWO_CURRENT_WINDOWS')
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
    equal([p for row in results for p in row['exportPins']],_ACTIVE_BINDINGS['ordinaryExports'],'EXACT_FIVE_CURRENT_ORIGINAL_EXPORTS')
    for key in ('runId', 'outputRoot', 'grant', 'lease'):
        need(not same(results[0][key], results[1][key]), 'FRESH_SEPARATE_ROLE_WINDOWS')
    need(results[0]['finished'] <= results[1]['started'], 'SEQUENTIAL_CLEANUP_BARRIER')
    need(not results[0]['cids'] & results[1]['cids'], 'REUSED_CONTAINER_STATE')
    files.recheck()
    return dict(schema='e02-minimum-consumption-result-v2', state='SUPPLEMENTAL_DATA_CONSISTENT_WITH_EXTERNALLY_AUTHENTICATED_ORIGINS',
                profileId=wire.PROFILE, wholeWindows=2, selectedExports=5, selectedNoteContexts=3, uniqueRumorIds=2,
                canonicalE02Changed=False, canonicalE02='PARTIAL22_UNCHANGED', primaryMatrixQualified=False,
                businessEffectsMeasured=False, sdkRuntimeAdmission=False, portableProcessAttestation=False,
                sourceProfile='PRODUCER4_SOURCE4_22_WORKERS_ASYNC_FRESH_GUARD' ,
                perCommandClockChronology='UNKNOWN_NOT_RECORDED', evidenceFiles=len(files.pins), evidenceBytes=files.total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True); parser.add_argument('--manifest-sha', required=True)
    parser.add_argument('--origin', required=True); parser.add_argument('--origin-sha', required=True)
    parser.add_argument('--read-root', action='append', required=True)
    parser.add_argument('--bindings',required=True);parser.add_argument('--bindings-sha',required=True)
    args = parser.parse_args()
    try:
        files = Files(args.read_root)
        manifest_pin = external(files, args.manifest, args.manifest_sha)
        origin_pin = external(files, args.origin, args.origin_sha)
        bindings_pin=external(files,args.bindings,args.bindings_sha)
        result = consume(files, manifest_pin, origin_pin,bindings_pin)
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as error:
        result = dict(schema='e02-minimum-consumption-result-v2', state='REFUSED_NO_CONTRIBUTION',
                      reason=type(error).__name__ + ':' + str(error)[:2048], canonicalE02Changed=False,
                      contributingWholeWindows=0, contributingExports=0)
        print(json_bytes(result).decode()); return 2
    print(json_bytes(result).decode()); return 0


if __name__ == '__main__':
    sys.exit(main())
