"""Pure closed capture contracts. No filesystem, clock, process or target imports."""
import hashlib,json,math,re
from decimal import Decimal
from pathlib import PurePosixPath

FILES=('test_guard_client.mjs', 'test_guard_transport_boundaries.mjs', 'test_capture_allocation.mjs', 'test_controller_emission.mjs', 'test_observation_model.mjs', 'test_guard_helper.py', 'test_capture_parent.py', 'test_public_identity_metadata.py', 'test_producer2_source.py', 'test_producer3_bindings.py', 'fixtureEoseCaller')
MODEL_KEYS=('asyncGuard', 'transportBoundaries', 'captureAllocation', 'controllerEmission', 'observation', 'helperProtocolPythonMethods', 'parentCapturePythonMethods', 'publicIdentityPythonMethods', 'sourceWiringPythonMethods', 'rebuiltArtifactPythonMethods', 'fixtureEoseCaller')
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
LIMITS={'childSeconds': 60, 'childAbsoluteReapSeconds': 3, 'stdoutBytes': 1048576, 'stderrBytes': 262144, 'rawFileBytes': 2147483648, 'parsedMetadataBytes': 16777216, 'hostFiles': 20000, 'controllerSeconds': 1263, 'outerSeconds': 1266, 'snapshotPoolSeconds': 480}
LEDGER={'snapshots': 480, 'children': 693, 'metadataCleanup': 30, 'reserve': 60}
SOURCE_DECISION='ACCEPT_PRODUCER_EOSE_SOURCE_AND_286_DEFINITIONS_ONLY'
CAPTURE_DECISION='ACCEPT_PRODUCER4_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY'
ADMISSION_DECISION='ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY'
REQUIRED_KNOWN_ACTORS=('/root', '/root/android_health_implementer', '/root/bridge_start_bootstrap_architecture', '/root/collector_policy_security_553c5bfd', '/root/completion3_final', '/root/completion_wrapper', '/root/consumer3_preparation', '/root/fixture_eose_queue_fix', '/root/helper_apk_binding_scope', '/root/helper_controller_source6_env', '/root/lease_fix_binding_scope', '/root/native_rebuild_prepare', '/root/ordinary_api35_source', '/root/ordinary_current266_templates', '/root/probe_r7_fresh_qa_8d291e97745f', '/root/probe_r7_fresh_security_8d291e97745f', '/root/producer286_capture_source', '/root/producer3_capture', '/root/producer4_nonblocking_source', '/root/producer_eose_successor', '/root/r5', '/root/r5_plan_fix', '/root/whole_consumer_fixture')
ROOT_KNOWN_ACTORS_PIN={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-capture-20261105/root-known-actors.json', 'bytes': 4110, 'sha256': 'a79d4482fba4ffbf1dc0a6e8719220ca74d430afd86842d6548b22a219ec20a2'}
REQUEST_KEYS=('cmd', 'workdir', 'login', 'yield_time_ms', 'max_output_tokens', 'sandbox_permissions', 'justification')
REQUEST_POLICY={'sandbox_permissions': 'require_escalated', 'justification': 'Jednorazové vykonanie prijatých 286 syntetických kontrol E02 s výsledkami v izolovanom /Data adresári podľa aktuálneho Root ACK; pôvodné limity a zákaz automatického opakovania zostávajú platné.'}
EXTERNAL_SOURCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/test_eose_queue.mjs', 'bytes': 10564, 'sha256': '8b85222b352e58feacc8d9a6cc78e9d41b6d74b931c5422384500cc91e5eac41'}
EXTERNAL_CWD='/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1'
EXTERNAL_NAMES=('baseline_actual_callback_reproduces_unrelated_eose_queue_failure', 'corrected_actual_callback_queued_eose_second', 'corrected_actual_callback_queued_eose_first', 'corrected_refuses_request_replacement', 'corrected_refuses_filter_mutation', 'corrected_refuses_subscription_close', 'corrected_refuses_subscription_added', 'corrected_refuses_extra_nonprogress_field', 'corrected_refuses_connection_close', 'corrected_refuses_connection_generation', 'corrected_refuses_app_receipt_generation', 'corrected_refuses_queued_raw_buffer_mutation', 'corrected_guard_enqueue_original_five_seconds', 'corrected_external_sticky_revocation', 'corrected_original_lease_expiry_Utc', 'corrected_original_lease_expiry_Mono', 'corrected_original_lease_expiry_Boot', 'corrected_original_owner_deadline', 'corrected_before_send_publication_invalidation_stays_fatal', 'publication_generation_still_binds_exact_eose_sequence')
EXTERNAL_FAMILY_PIN={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-eose-successor-20261105/source1/caller-regression-family.json', 'bytes': 18495, 'sha256': 'b42e86124464fe9540a069f6437cf28aeb574703d51e538411c8940b4cf7d8e0'}
EXTERNAL_CODE=[{'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/baseline/fixture.mjs', 'bytes': 45130, 'sha256': '7294668da0e4c1fe92efc11c9cc43eab8e3d1e5c1a83c9bed0d72a224463d256'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/capture-allocation.mjs', 'bytes': 7437, 'sha256': 'a86180100f6f4fee691bd177f557fbc3a4573ccc9d0f3f15ee66a32c1b8e57a7'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/capture-budget.mjs', 'bytes': 8963, 'sha256': '7e75aa2e0fcf1233a5d04cb899bde1ae6ff8a581bb8f57747e9115bf0993e312'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/dependency-tree.mjs', 'bytes': 2842, 'sha256': '0b574a14e591abc1908f4733908001d8ea1ab5698da8991e618ca26714eeded3'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/exchange-adapter.mjs', 'bytes': 1012, 'sha256': '4e03f6449defff4585b532572ca3f0ef254dc76f056079ce85c2266de9f50aef'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/exchange.mjs', 'bytes': 6662, 'sha256': 'e3e962230a7adc84c495c23b0724ad6a1c8f366dd0e0376fc53cbaf00f1eb5dc'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/fixture.mjs', 'bytes': 45613, 'sha256': '0d273eb11f9631e7be18e2cc959e3aa7f88f14441f7c6f7cfc05fa2448ee103b'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-client-core.mjs', 'bytes': 8072, 'sha256': '14be5abb1ff953d2336e841e1364acdfd8275874ffed3aef88f9a9489fac1083'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-client.mjs', 'bytes': 9308, 'sha256': '50d3dacdc0e3a008ea15bc510004ff2bf805f3de195785eb25a241f678a1dfb0'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-transport-boundaries.mjs', 'bytes': 4978, 'sha256': 'c4c5cda6107cdead8715da8bdba917a31ebabadc0249d8fba0b343a718f98068'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-wire.mjs', 'bytes': 1921, 'sha256': '8cf473b741d631f80ef785c86acf5caa9899d03206696a8f740db08878c02d8e'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/phase-writer.mjs', 'bytes': 2085, 'sha256': 'bcfb3338d1ab8cbb20709f6add09a2e7be01a270f48271112e3aa3a76743cead'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/proxy-observer.mjs', 'bytes': 4478, 'sha256': 'fb17d34d3dea46c62bf29ed537684936b3a2871643b6d4fe3c16c88ffa37d0a1'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/test_fixture.mjs', 'bytes': 3199, 'sha256': '11f9f9cd496885e6bf517a205b91cfe7dc9d95ab1451a31c21f09461d5c6d7f2'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/test_guard_client.mjs', 'bytes': 35675, 'sha256': 'dade2a486a9bfea5e89cafb2c0af33fc14c3956a0d78e456898d0c206df6efa5'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/test_minimum_fixture.mjs', 'bytes': 4852, 'sha256': 'f92aabd95b257cae2408a4e789eeb7ded8bf7979ec3723202f533f58fb92fc18'}, {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/test_eose_queue.mjs', 'bytes': 10564, 'sha256': '8b85222b352e58feacc8d9a6cc78e9d41b6d74b931c5422384500cc91e5eac41'}]
EXTERNAL_TESTED_FIXTURE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/fixture.mjs', 'bytes': 45613, 'sha256': '0d273eb11f9631e7be18e2cc959e3aa7f88f14441f7c6f7cfc05fa2448ee103b'}
EXTERNAL_FIXTURE_MODE=436
EXTERNAL_MODES={'/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/baseline/fixture.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/capture-allocation.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/capture-budget.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/dependency-tree.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/exchange-adapter.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/exchange.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/fixture.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-client-core.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-client.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-transport-boundaries.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/guard-wire.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/phase-writer.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/proxy-observer.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/test_fixture.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/test_guard_client.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/candidate/test_minimum_fixture.mjs': 436, '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-fixture-eose-queue-fix-20261105/source1/test_eose_queue.mjs': 436}

ACK_KEYS='schema actor executionAuthorized scope producerSource producerSourceAcceptance producerReviews captureSource captureSourceAcceptance captureReviews admissionPlan admissionData admissionDataAcceptance admissionReviews sourceBirth actorContext inputManifest plan clockSelection requestContract runtimeBindings authors operators noRetry'

def need(v,m):
    if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_KEYS')
def pin(d):
    closed(d,'path bytes sha256');need(type(d['path']) is str and d['path'].startswith('/') and str(PurePosixPath(d['path']))==d['path'] and '..' not in PurePosixPath(d['path']).parts and '\0' not in d['path'],'CANONICAL_PIN_PATH');need(type(d['bytes']) is int and 0<=d['bytes']<=2147483648 and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'EXACT_PIN');return d
def actors(value):
    need(type(value) is list and value and all(type(a) is str and (a=='/root' or a.startswith('/root/')) for a in value),'DECLARED_ACTORS');return set(value)
def counts(source,control):
    need(source['schema']=='e02-ordinary-producer4-source-subject-v1' and source['version']=='SOURCE4' and source['runtimeSourceCount']==22,'EXACT_CURRENT_SOURCE4_HEADER')
    need(all(type(source[k]) is int and source[k]==0 for k in ('modelsExecuted','helperExecutions','roleExecutions','ordinaryRowsQualified')) and source['runtimeReady'] is False,'SOURCE_DEFINITIONS_NOT_PRIOR_EXECUTION')
    closed(source['modelsDefined'],' '.join(MODEL_KEYS));values=[source['modelsDefined'][k] for k in MODEL_KEYS]
    need(all(type(n) is int and 0<n<=10000 for n in values),'CURRENT_DECLARED_POSITIVE_COUNTS')
    js=control['selectedJavaScriptDefinitions'];py=control['pythonDefinitions']
    need([r['file'] for r in js]==list(FILES[:5])+[EXTERNAL_SOURCE['path']],'EXACT_SIX_JS_SELECTION_WITH_EXTERNAL_SOURCE')
    indexed={r['file']:r for r in py};need(len(indexed)==len(py),'UNIQUE_PYTHON_DECLARATION')
    derived=[r['expandedDefinitions'] for r in js[:5]]+[indexed[n]['methodDefinitions'] for n in FILES[5:10]]+[js[5]['expandedDefinitions']]
    need(derived==values and values[-1]==20,'SOURCE_CONTROL_ELEVEN_COUNTS_JOIN')
    need(source['externalCallerRegressionFamily']==EXTERNAL_FAMILY_PIN and control['externalCallerRegressionFamily']==EXTERNAL_FAMILY_PIN,'EXACT_EXTERNAL_CALLER_FAMILY_AUTHORITY')
    need(source['externalControlSources']==list(EXTERNAL_CODE) and source['externalControlSourceCount']==17,'EXACT_EXTERNAL_CODE_MEMBERSHIP')
    return values
def reviews(records,pins,subject,decision,forbidden):
    need(type(records) is list and type(pins) is list and len(records)==len(pins)==2 and pins[0]!=pins[1],'TWO_ORDERED_REVIEW_PINS');sessions=[]
    for role,r,p in zip(('qa','security'),records,pins):
        pin(p);closed(r,'role session decision subject');need(r['role']==role and r['subject']==subject and r['decision']==decision,'EXACT_REVIEW_SUBJECT_ROLE_DECISION');need(type(r['session']) is str and r['session'].startswith('/root/') and r['session'] not in forbidden,'INDEPENDENT_REVIEWER');sessions.append(r['session'])
    need(sessions[0]!=sessions[1],'DISTINCT_QA_SECURITY')

def validate_acceptances(ack,source,control,method,admission_plan,records,context):
    closed(ack,ACK_KEYS);need(ack['schema']=='e02-producer4-control-capture-root-ack-v1' and ack['actor']=='/root' and ack['executionAuthorized'] is True and ack['scope']=='ONE_CURRENT_EOSE_SUCCESSOR_ELEVEN_SELECTED_PURE_CONTROL_GROUPS_ONLY' and ack['noRetry'] is True,'ONE_EXTERNAL_ROOT_ACK')
    for k in ('producerSource','producerSourceAcceptance','captureSource','captureSourceAcceptance','admissionPlan','admissionData','admissionDataAcceptance','sourceBirth','actorContext','inputManifest','plan','clockSelection','requestContract','runtimeBindings'):pin(ack[k])
    values=counts(source,control);total=sum(values)
    need(method['schema']=='e02-producer4-control-capture-code-subject-v1' and method['producerSource']==ack['producerSource'] and method['codeOnly'] is True,'EXACT_CAPTURE_CODE_SOURCE4_JOIN')
    closed(context,'schema producerSource captureSource sourceBirth participants participantProofs');need(context['schema']=='e02-producer4-capture-current-actor-context-v1' and context['producerSource']==ack['producerSource'] and context['captureSource']==ack['captureSource'] and context['sourceBirth']==ack['sourceBirth'],'EXACT_EXTERNALLY_PINNED_ACTOR_CONTEXT')
    known=records['knownActors'];closed(known,'schema actor scope producerSource knownActors provenance semantics sourceAccepted executionAuthorized')
    need(method['knownActors']==ROOT_KNOWN_ACTORS_PIN and known['schema']=='e02-root-capture-known-actors-v1' and known['actor']=='/root' and known['scope']=='CURRENT_PRODUCER_EOSE_286_PURE_CONTROL_CAPTURE_AND_ADMISSION' and known['producerSource']==ack['producerSource'],'EXACT_REQUIRED_ROOT_KNOWN_ACTOR_AUTHORITY')
    required=actors(known['knownActors']);need(required==set(REQUIRED_KNOWN_ACTORS),'COMPLETE_REQUIRED_ROOT_KNOWN_ACTORS')
    need(required<=actors(context['participants']),'CONTEXT_INCLUDES_EVERY_ROOT_KNOWN_ACTOR')
    # Close the complete union BEFORE accepting any of the three review pairs.
    union=required|{'/root','/root/r5_plan_fix','/root/producer4_nonblocking_source','/root/completion_wrapper'}|actors(context['participants'])|actors(ack['authors'])|actors(ack['operators'])|actors(method['authors'])|actors(records['admissionSubject']['authors'])|actors(records['admissionSubject']['operators'])
    union|=actors(source['sourceContributors'])|{source['author'],source['coordinator'],source['predecessorAuthor']}
    need(type(context['participantProofs']) is list and context['participantProofs'],'ACTUAL_ACTOR_DERIVATION_PROOFS_REQUIRED')
    s=records['producerAcceptance'];closed(s,'schema actor decision subject reviews modelsDefined runtimeWorkerCount modelsExecuted helperExecutions roleExecutions runtimeReady runtimeReleased scope')
    need(s['schema']=='e02-root-producer-eose-source-acceptance-v1' and s['actor']=='/root' and s['decision']==SOURCE_DECISION and s['subject']==ack['producerSource'] and s['reviews']==ack['producerReviews'],'EXACT_ISSUED_PRODUCER_ACCEPTANCE')
    need(s['modelsDefined']==total and type(s['modelsDefined']) is int and s['runtimeWorkerCount']==22 and all(type(s[k]) is int and s[k]==0 for k in ('modelsExecuted','helperExecutions','roleExecutions')) and s['runtimeReady'] is False and s['runtimeReleased'] is False and s['scope']=='EXACT_ORDINARY_EOSE_SUCCESSOR_SOURCE_AND_CONTROL_DEFINITIONS_ONLY','SOURCE_ONLY_NOT_DATA_OR_RUNTIME')
    reviews(records['producerReviews'],ack['producerReviews'],ack['producerSource'],SOURCE_DECISION,union)
    c=records['captureAcceptance'];closed(c,'schema actor decision subject reviews admissionModelsDefined admissionModelsExecuted producerSource scope executionAuthorized')
    n=len(admission_plan['caseNames']);need(type(n) is int and n>0 and len(set(admission_plan['caseNames']))==n and admission_plan['modelsDefined']==n and method['admissionModelsDefined']==n,'EXACT_FROZEN_ADMISSION_DEFINITIONS')
    need(c['schema']=='e02-root-producer4-capture-source-acceptance-v1' and c['actor']=='/root' and c['decision']==CAPTURE_DECISION and c['subject']==ack['captureSource'] and c['reviews']==ack['captureReviews'] and c['producerSource']==ack['producerSource'] and c['admissionModelsDefined']==n and c['admissionModelsExecuted']==0 and type(c['admissionModelsExecuted']) is int and c['scope']=='EXACT_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY' and c['executionAuthorized'] is False,'EXACT_CAPTURE_SOURCE_ACCEPTANCE')
    reviews(records['captureReviews'],ack['captureReviews'],ack['captureSource'],CAPTURE_DECISION,union)
    a=records['admissionAcceptance'];closed(a,'schema actor decision subject reviews captureSource producerSource admissionPlan modelsDefined modelsExecuted modelsPassed modelsFailed targetModelsExecuted helperExecutions ordinaryRoleExecutions scope executionAuthorized')
    need(a['schema']=='e02-root-producer4-capture-admission-data-acceptance-v1' and a['actor']=='/root' and a['decision']==ADMISSION_DECISION and a['subject']==ack['admissionData'] and a['reviews']==ack['admissionReviews'] and a['captureSource']==ack['captureSource'] and a['producerSource']==ack['producerSource'] and a['admissionPlan']==ack['admissionPlan'],'EXACT_CURRENT_ADMISSION_DATA')
    need(all(type(a[k]) is int and a[k]==n for k in ('modelsDefined','modelsExecuted','modelsPassed')) and all(type(a[k]) is int and a[k]==0 for k in ('modelsFailed','targetModelsExecuted','helperExecutions','ordinaryRoleExecutions')) and a['scope']=='MOCKED_CAPTURE_ADMISSION_DATA_ONLY' and a['executionAuthorized'] is False,'ALL_ADMISSION_MODELS_PASSED_ONLY')
    data=records['admissionSubject'];closed(data,'schema authors operators captureSource producerSource admissionPlan execution originalToolOrigin rawArtifactManifest inputsBefore inputsAfter inputsUnchanged modelsDefined modelsExecuted modelsPassed modelsFailed skipped truncated targetModelsExecuted helperExecutions ordinaryRoleExecutions');need(data['schema']=='e02-producer4-capture-admission-data-subject-v1' and data['captureSource']==ack['captureSource'] and data['producerSource']==ack['producerSource'] and data['admissionPlan']==ack['admissionPlan'] and data['inputsUnchanged'] is True and all(type(data[k]) is int and data[k]==n for k in ('modelsDefined','modelsExecuted','modelsPassed')) and all(type(data[k]) is int and data[k]==0 for k in ('modelsFailed','skipped','targetModelsExecuted','helperExecutions','ordinaryRoleExecutions')) and data['truncated'] is False,'COMPLETE_CURRENT_ADMISSION_SUBJECT')
    for key in ('execution','originalToolOrigin','rawArtifactManifest','inputsBefore','inputsAfter'):pin(data[key])
    reviews(records['admissionReviews'],ack['admissionReviews'],ack['admissionData'],ADMISSION_DECISION,union)
    return values,union

def validate_plan(plan,ack,source,control,method,manifest,clock):
    need(plan['schema']=='e02-producer4-control-capture-plan-v1' and plan['readiness'] is True and plan['producerSource']==ack['producerSource'] and plan['captureSource']==ack['captureSource'] and plan['inputManifest']==ack['inputManifest'] and plan['limits']==LIMITS and plan['deadlineLedger']==LEDGER,'EXACT_FINITE_CURRENT_PLAN')
    need(clock['schema']=='e02-root-control-capture-clock-source-selection-v2' and clock['actor']=='/root' and clock['controllerSeconds']==1263 and clock['outerKillSeconds']==1266 and clock['sharedInputSnapshotPoolSeconds']==480 and clock['maximumSerialScopes']==11 and clock['eachScopeSeconds']==60 and clock['eachOwnedTerminationReserveSeconds']==3 and clock['metadataAndCleanupSeconds']==30 and clock['otherReserveSeconds']==60 and clock['sumSeconds']==1263,'ROOT_SELECTED_ELEVEN_CLOCK_SOURCE')
    need([s['scope'] for s in plan['scopes']]==list(FILES) and plan['countsSeparate']==counts(source,control),'ELEVEN_CURRENT_SCOPES_NO_PREDECESSOR_TRANSFER')
    by_name={PurePosixPath(d['path']).name:d for d in source['sources']};need(len(by_name)==len(source['sources']),'UNIQUE_SOURCE_NAMES')
    node=plan['tools']['node'];python=plan['tools']['python']
    need(node['path']=='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node' and python['path']=='/home/peterhorvath/.miniforge3/bin/python3.13','FIXED_HOST_INTERPRETERS')
    need(set(plan['tools'])=={'node','python','timeout','env'} and plan['tools']['timeout']['path']=='/usr/bin/timeout' and plan['tools']['env']['path']=='/usr/bin/env','CLOSED_TOOLS_NO_EXTRA_TARGET')
    roots={str(PurePosixPath(by_name[name]['path']).parent) for name in FILES[:10]};need(len(roots)==1,'ONE_EXPLICIT_BASE_MODEL_ROOT')
    model_root=next(iter(roots));groups=control['selectedGroups']
    need(type(groups) is list and len(groups)==11 and [g['scope'] for g in groups]==list(FILES),'EXACT_REVIEWED_ELEVEN_GROUP_VECTOR')
    for i,s in enumerate(plan['scopes']):
        closed(s,'scope source argv cwd count definitionNames format')
        external=i==10;expected=EXTERNAL_SOURCE if external else by_name[FILES[i]]
        cwd=EXTERNAL_CWD if external else model_root
        argv=[node['path'],expected['path']] if i<5 or external else [python['path'],'-I','-B',expected['path']]
        need(s['source']==expected and s['count']==plan['countsSeparate'][i] and s['cwd']==cwd and s['argv']==argv,'EXACT_TYPED_SOURCE_COUNT_CWD_AND_INTERPRETER')
        g=groups[i];need(g['source']==expected and g['cwd']==cwd and g['count']==s['count'] and g['definitionNames']==s['definitionNames'],'SOURCE_PLAN_DEFINITION_VECTOR_JOIN')
        need(type(s['definitionNames']) is list and len(s['definitionNames'])==s['count'] and len(set(s['definitionNames']))==s['count'],'UNIQUE_ORDERED_DEFINITION_NAMES')
        if external:need(g['externalSourceFamily']==EXTERNAL_FAMILY_PIN and s['definitionNames']==list(EXTERNAL_NAMES) and s['format']=='EXACT_EXTERNAL_EOSE20_NODE_JSON','EXACT_EXTERNAL_NAMED_NODE_FAMILY')
    need(manifest['schema']=='e02-producer4-explicit-host-input-manifest-v1' and manifest['producerSource']==ack['producerSource'] and manifest['closedSourceSubjectKeys']==sorted(source) and manifest['controlPlan']==source['controlPlan'],'EXACT_CLOSED_SOURCE_INPUT_CONTRACT')
    index={x['pin']['path']:x for x in manifest['files']};need(len(index)==len(manifest['files'])==manifest['actualInputCount'] and 1<=len(index)<=20000,'EXACT_CURRENT_INPUT_COUNT')
    protected=source['sources']+source['runtimeSources']+source['externalControlSources']+list(source['configurations'].values())+list(plan['tools'].values())+method['sources']+[EXTERNAL_FAMILY_PIN]
    for d in protected:need(index.get(d['path'],{}).get('pin')==d,'ALL_DECLARED_CODE_EXTERNAL_WORKERS_CONFIGS_TOOLS_PROTECTED')
    need(set(source['configurations'])=={'incoming','archive'},'BOTH_ROLE_CONFIGURATIONS')
    fixture=by_name['fixture.mjs'];tested=EXTERNAL_TESTED_FIXTURE
    need(fixture['bytes']==tested['bytes'] and fixture['sha256']==tested['sha256'],'EXACT_TESTED_FIXTURE_BYTES_BIND_CURRENT_PRODUCER')
    need(index[fixture['path']]['mode']==index[tested['path']]['mode']==EXTERNAL_FIXTURE_MODE,'EXACT_TESTED_AND_CURRENT_FIXTURE_MODES')
    for d in EXTERNAL_CODE:need(index[d['path']]['mode']==EXTERNAL_MODES[d['path']],'EXACT_EXTERNAL_SOURCE_MODES')
    need(plan['outputRoot'] is not None and type(plan['outputRoot']) is str and plan['outputRoot'].startswith('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-'),'FRESH_OWNED_CAPTURE_OUTPUT_NAMESPACE')

def checked_write(writer,raw):
    need(type(raw) is bytes,'RAW_OUTPUT_BYTES');n=writer(raw);need(type(n) is int and n==len(raw),'SHORT_OR_UNKNOWN_WRITE_REFUSES_NO_REPAIR');return n

def _request(plan,ack_sha,here):
    import shlex
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',plan['tools']['timeout']['path'],'--signal=KILL','1266s',plan['tools']['python']['path'],'-I','-B',here+'/capture.py','--execute-once','--root-ack-sha',ack_sha]
    return dict(cmd=shlex.join(argv),workdir=here,login=False,yield_time_ms=1000,max_output_tokens=2000,**REQUEST_POLICY)
def expected_request(plan,ack_sha,here):
    need(type(ack_sha) is str and re.fullmatch('[0-9a-f]{64}',ack_sha),'ACTUAL_ACK_SHA');return _request(plan,ack_sha,here)
def request_template(plan,here):return _request(plan,'<ACTUAL_ROOT_ACK_SHA256>',here)

def decode_tool_origin(raw):
    need(type(raw) is bytes and len(raw)<=16777216,'BOUNDED_ORIGINAL_API_METADATA')
    def pairs(items):
        d={}
        for k,v in items:need(k not in d,'DUPLICATE_API_KEY');d[k]=v
        return d
    value=json.loads(raw.decode('utf8','strict'),object_pairs_hook=pairs,parse_float=Decimal,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_API')))
    def walk(v,path=(),depth=0):
        need(depth<=64,'API_DEPTH')
        if isinstance(v,Decimal):need((path==('launch','unmodifiedResponse','wall_time_seconds') or len(path)==4 and path[0]=='polls' and type(path[1]) is int and path[2:]==('unmodifiedResponse','wall_time_seconds')) and v.is_finite() and v>=0,'ONLY_ACTUAL_API_WALL_DURATION_FLOAT')
        elif type(v) is dict:
            for k,x in v.items():walk(x,path+(k,),depth+1)
        elif type(v) is list:
            for i,x in enumerate(v):walk(x,path+(i,),depth+1)
    walk(value);return value

def validate_request(value):
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

def validate_origin(origin,expected,operators):
    expected_bytes=canonical_request(expected)
    closed(origin,'schema operator launch polls');need(origin['schema']=='e02-actual-tool-custody-v1' and origin['operator'] in operators and type(origin['polls']) is list and len(origin['polls'])<=128,'ACTUAL_ROOT_API_ORIGIN');session=None;terminal=False;outputs=[]
    for i,frame in enumerate([origin['launch'],*origin['polls']]):
        closed(frame,'toolName actualArguments unmodifiedResponse');need(not terminal,'NO_DUPLICATE_AFTER_TERMINAL');a=frame['actualArguments'];r=frame['unmodifiedResponse'];need(type(r) is dict,'UNMODIFIED_API_OBJECT')
        if i==0:need(frame['toolName']=='tools.exec_command' and canonical_request(a)==expected_bytes,'EXACT_SEVEN_KEY_FOREGROUND_REQUEST')
        else:need(frame['toolName']=='tools.write_stdin' and valid_poll_request(a,session),'GENUINE_SAME_SESSION_ALL_POLLS')
        if r.get('exit_code') is not None:need(type(r['exit_code']) is int and r['exit_code']==0 and (r.get('session_id') is None or type(r['session_id']) is int and r['session_id']==session),'NATURAL_OUTER_TERMINAL0');terminal=True
        else:
            need(type(r.get('session_id')) is int and r['session_id']>0,'REAL_YIELDED_SESSION');session=session or r['session_id'];need(session==r['session_id'],'SAME_SESSION_RESPONSE')
        if 'output' in r:need(type(r['output']) is str and len(r['output'].encode())<=16777216,'BOUNDED_ACTUAL_API_OUTPUT');outputs.append(r['output'])
    need(terminal,'COMPLETE_TERMINAL_ORIGIN_REQUIRED');return ''.join(outputs)

def validate_external_source_names(raw,scope):
    """Frozen literal declarations, no target import or source evaluation."""
    need(type(raw) is bytes and scope['source']==EXTERNAL_SOURCE and scope['definitionNames']==list(EXTERNAL_NAMES),'EXACT_EXTERNAL_SOURCE_AND_NAMES')
    need(len(raw)==EXTERNAL_SOURCE['bytes'] and hashlib.sha256(raw).hexdigest()==EXTERNAL_SOURCE['sha256'],'EXACT_EXTERNAL_SOURCE_BYTES')
    # This exact script was independently inspected and SOURCE accepted; hash
    # binds its closed literal expansion to the frozen twenty-name vector.
    return list(EXTERNAL_NAMES)
