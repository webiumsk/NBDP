"""Pure closed capture contracts. No filesystem, clock, process or target imports."""
import json,math,re
from decimal import Decimal
from pathlib import PurePosixPath

FILES=('test_guard_client.mjs','test_guard_transport_boundaries.mjs','test_capture_allocation.mjs','test_controller_emission.mjs','test_observation_model.mjs','test_guard_helper.py','test_capture_parent.py','test_public_identity_metadata.py','test_producer2_source.py','test_producer3_bindings.py')
MODEL_KEYS=('asyncGuard','transportBoundaries','captureAllocation','controllerEmission','observation','helperProtocolPythonMethods','parentCapturePythonMethods','publicIdentityPythonMethods','sourceWiringPythonMethods','rebuiltArtifactPythonMethods')
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
LIMITS={'childSeconds':60,'childAbsoluteReapSeconds':3,'stdoutBytes':1048576,'stderrBytes':262144,'rawFileBytes':2147483648,'parsedMetadataBytes':16777216,'hostFiles':20000,'controllerSeconds':1200,'outerSeconds':1203,'snapshotPoolSeconds':480}
LEDGER={'snapshots':480,'children':630,'metadataCleanup':30,'reserve':60}
SOURCE_DECISION='ACCEPT_PRODUCER4_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'
CAPTURE_DECISION='ACCEPT_PRODUCER4_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY'
ADMISSION_DECISION='ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY'
REQUIRED_KNOWN_ACTORS=('/root', '/root/r5_plan_fix', '/root/producer4_nonblocking_source', '/root/completion_wrapper', '/root/completion3_final', '/root/android_health_implementer', '/root/ordinary_api35_source', '/root/consumer3_preparation', '/root/producer3_capture', '/root/r5', '/root/whole_consumer_fixture')
ROOT_KNOWN_ACTORS_PIN={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-control-capture-preparation-20261028/root-known-actors.json', 'bytes': 1338, 'sha256': '7d6d9b6046e6ab69e146d8127ef6d22fbc9c97a910d605f513279675cd6c0fe3'}
ACK_KEYS='schema actor executionAuthorized scope producerSource producerSourceAcceptance producerReviews captureSource captureSourceAcceptance captureReviews admissionPlan admissionData admissionDataAcceptance admissionReviews sourceBirth actorContext inputManifest plan clockSelection requestContract runtimeBindings authors operators noRetry'

def need(v,m):
    if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_KEYS')
def pin(d):
    closed(d,'path bytes sha256');need(type(d['path']) is str and d['path'].startswith('/') and str(PurePosixPath(d['path']))==d['path'] and '..' not in PurePosixPath(d['path']).parts and '\0' not in d['path'],'CANONICAL_PIN_PATH');need(type(d['bytes']) is int and 0<=d['bytes']<=2147483648 and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'EXACT_PIN');return d
def actors(value):
    need(type(value) is list and value and all(type(a) is str and (a=='/root' or a.startswith('/root/')) for a in value),'DECLARED_ACTORS');return set(value)
def counts(source,control):
    need(source['schema']=='e02-ordinary-producer4-source-subject-v1' and source['version']=='SOURCE4','CURRENT_SOURCE4_ONLY');need(source['runtimeSourceCount']==22 and len(source['runtimeSources'])==22,'EXACT22_RUNTIME_WORKERS');need(all(type(source[k]) is int and source[k]==0 for k in ('modelsExecuted','helperExecutions','roleExecutions','ordinaryRowsQualified')) and source['runtimeReady'] is False,'SOURCE_DEFINITIONS_NOT_PRIOR_EXECUTION')
    closed(source['modelsDefined'],' '.join(MODEL_KEYS));values=[source['modelsDefined'][k] for k in MODEL_KEYS];need(all(type(n) is int and 0<n<=10000 for n in values),'CURRENT_DECLARED_POSITIVE_COUNTS')
    js=control['selectedJavaScriptDefinitions'];py=control['pythonDefinitions'];need([r['file'] for r in js]==list(FILES[:5]),'EXACT_FIVE_JS_SELECTION');indexed={r['file']:r for r in py};need(len(indexed)==len(py),'UNIQUE_PYTHON_DECLARATION')
    need([r['expandedDefinitions'] for r in js]+[indexed[n]['methodDefinitions'] for n in FILES[5:]]==values,'SOURCE_CONTROL_COUNTS_JOIN');return values
def reviews(records,pins,subject,decision,forbidden):
    need(type(records) is list and type(pins) is list and len(records)==len(pins)==2 and pins[0]!=pins[1],'TWO_ORDERED_REVIEW_PINS');sessions=[]
    for role,r,p in zip(('qa','security'),records,pins):
        pin(p);closed(r,'role session decision subject');need(r['role']==role and r['subject']==subject and r['decision']==decision,'EXACT_REVIEW_SUBJECT_ROLE_DECISION');need(type(r['session']) is str and r['session'].startswith('/root/') and r['session'] not in forbidden,'INDEPENDENT_REVIEWER');sessions.append(r['session'])
    need(sessions[0]!=sessions[1],'DISTINCT_QA_SECURITY')

def validate_acceptances(ack,source,control,method,admission_plan,records,context):
    closed(ack,ACK_KEYS);need(ack['schema']=='e02-producer4-control-capture-root-ack-v1' and ack['actor']=='/root' and ack['executionAuthorized'] is True and ack['scope']=='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY' and ack['noRetry'] is True,'ONE_EXTERNAL_ROOT_ACK')
    for k in ('producerSource','producerSourceAcceptance','captureSource','captureSourceAcceptance','admissionPlan','admissionData','admissionDataAcceptance','sourceBirth','actorContext','inputManifest','plan','clockSelection','requestContract','runtimeBindings'):pin(ack[k])
    values=counts(source,control);total=sum(values)
    need(method['schema']=='e02-producer4-control-capture-code-subject-v1' and method['producerSource']==ack['producerSource'] and method['codeOnly'] is True,'EXACT_CAPTURE_CODE_SOURCE4_JOIN')
    closed(context,'schema producerSource captureSource sourceBirth participants participantProofs');need(context['schema']=='e02-producer4-capture-current-actor-context-v1' and context['producerSource']==ack['producerSource'] and context['captureSource']==ack['captureSource'] and context['sourceBirth']==ack['sourceBirth'],'EXACT_EXTERNALLY_PINNED_ACTOR_CONTEXT')
    known=records['knownActors'];closed(known,'schema actor scope producerSource knownActors provenance semantics sourceAccepted executionAuthorized')
    need(method['knownActors']==ROOT_KNOWN_ACTORS_PIN and known['schema']=='e02-root-capture-known-actors-v1' and known['actor']=='/root' and known['scope']=='CURRENT_PRODUCER4_PURE_CONTROL_CAPTURE_AND_ADMISSION' and known['producerSource']==ack['producerSource'],'EXACT_REQUIRED_ROOT_KNOWN_ACTOR_AUTHORITY')
    required=actors(known['knownActors']);need(required==set(REQUIRED_KNOWN_ACTORS),'COMPLETE_REQUIRED_ELEVEN_KNOWN_ACTORS')
    need(required<=actors(context['participants']),'CONTEXT_INCLUDES_EVERY_ROOT_KNOWN_ACTOR')
    # Close the complete union BEFORE accepting any of the three review pairs.
    union=required|{'/root','/root/r5_plan_fix','/root/producer4_nonblocking_source','/root/completion_wrapper'}|actors(context['participants'])|actors(ack['authors'])|actors(ack['operators'])|actors(method['authors'])|actors(records['admissionSubject']['authors'])|actors(records['admissionSubject']['operators'])
    union|=actors(source['sourceContributors'])|{source['author'],source['coordinator'],source['predecessorAuthor']}
    need(type(context['participantProofs']) is list and context['participantProofs'],'ACTUAL_ACTOR_DERIVATION_PROOFS_REQUIRED')
    s=records['producerAcceptance'];closed(s,'schema actor decision subject reviews modelsDefined runtimeWorkerCount modelsExecuted helperExecutions roleExecutions runtimeReady runtimeReleased scope')
    need(s['schema']=='e02-root-current-producer4-source-acceptance-v1' and s['actor']=='/root' and s['decision']==SOURCE_DECISION and s['subject']==ack['producerSource'] and s['reviews']==ack['producerReviews'],'EXACT_ISSUED_PRODUCER_ACCEPTANCE')
    need(s['modelsDefined']==total and type(s['modelsDefined']) is int and s['runtimeWorkerCount']==22 and all(type(s[k]) is int and s[k]==0 for k in ('modelsExecuted','helperExecutions','roleExecutions')) and s['runtimeReady'] is False and s['runtimeReleased'] is False and s['scope']=='EXACT_CURRENT_SOURCE_AND_CONTROL_DEFINITIONS_ONLY','SOURCE_ONLY_NOT_DATA_OR_RUNTIME')
    reviews(records['producerReviews'],ack['producerReviews'],ack['producerSource'],'ACCEPT_PRODUCER4_SOURCE4_AND_'+str(total)+'_CONTROL_DEFINITIONS_ONLY',union)
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
    need(clock['schema']=='e02-root-control-capture-clock-source-selection-v1' and clock['actor']=='/root' and clock['controllerSeconds']==1200 and clock['outerKillSeconds']==1203 and clock['sharedInputSnapshotPoolSeconds']==480 and clock['maximumSerialScopes']==10 and clock['eachScopeSeconds']==60 and clock['eachOwnedTerminationReserveSeconds']==3 and clock['sumSeconds']==1200,'ROOT_SELECTED_CLOCK_SOURCE')
    need([s['scope'] for s in plan['scopes']]==list(FILES) and plan['countsSeparate']==counts(source,control),'TEN_CURRENT_SCOPES_NO_PREDECESSOR_TRANSFER')
    by_name={PurePosixPath(d['path']).name:d for d in source['sources']};need(len(by_name)==len(source['sources']),'UNIQUE_SOURCE_NAMES');node=plan['tools']['node'];python=plan['tools']['python']
    need(node['path']=='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node' and python['path']=='/home/peterhorvath/.miniforge3/bin/python3.13','FIXED_HOST_INTERPRETERS')
    need(set(plan['tools'])=={'node','python','timeout','env'} and plan['tools']['timeout']['path']=='/usr/bin/timeout' and plan['tools']['env']['path']=='/usr/bin/env','CLOSED_TOOLS_NO_EXTRA_TARGET')
    roots={str(PurePosixPath(by_name[name]['path']).parent) for name in FILES};need(len(roots)==1,'ONE_EXPLICIT_SELECTED_MODEL_ROOT');model_root=next(iter(roots))
    for i,s in enumerate(plan['scopes']):
        closed(s,'scope source argv cwd count definitionNames format');need(s['source']==by_name[FILES[i]] and s['count']==plan['countsSeparate'][i] and s['cwd']==model_root,'CURRENT_SELECTED_SOURCE_COUNT_WORKDIR')
        need(s['argv']==([node['path'],s['source']['path']] if i<5 else [python['path'],'-I','-B',s['source']['path']]),'EXACT_CHILD_ARGV')
    need(manifest['schema']=='e02-producer4-explicit-host-input-manifest-v1' and manifest['producerSource']==ack['producerSource'] and manifest['closedSourceSubjectKeys']==sorted(source) and manifest['controlPlan']==source['controlPlan'],'EXACT_CLOSED_SOURCE_INPUT_CONTRACT')
    index={x['pin']['path']:x['pin'] for x in manifest['files']};need(len(index)==len(manifest['files'])==manifest['actualInputCount'] and 1<=len(index)<=20000,'EXACT_CURRENT_INPUT_COUNT')
    for d in source['sources']+source['runtimeSources']+list(source['configurations'].values())+list(plan['tools'].values())+method['sources']:
        need(index.get(d['path'])==d,'ALL_DECLARED_CODE_WORKERS_CONFIGS_TOOLS_PROTECTED')
    need(set(source['configurations'])=={'incoming','archive'},'BOTH_ROLE_CONFIGURATIONS')
    need(plan['outputRoot'] is not None and type(plan['outputRoot']) is str and plan['outputRoot'].startswith('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-'),'FRESH_OWNED_CAPTURE_OUTPUT_NAMESPACE')

def checked_write(writer,raw):
    need(type(raw) is bytes,'RAW_OUTPUT_BYTES');n=writer(raw);need(type(n) is int and n==len(raw),'SHORT_OR_UNKNOWN_WRITE_REFUSES_NO_REPAIR');return n

def _request(plan,ack_sha,here):
    import shlex
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',plan['tools']['timeout']['path'],'--signal=KILL','1203s',plan['tools']['python']['path'],'-I','-B',here+'/capture.py','--execute-once','--root-ack-sha',ack_sha]
    return dict(cmd=shlex.join(argv),workdir=here,login=False,yield_time_ms=1000,max_output_tokens=2000)
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

def validate_origin(origin,expected,operators):
    closed(origin,'schema operator launch polls');need(origin['schema']=='e02-actual-tool-custody-v1' and origin['operator'] in operators and type(origin['polls']) is list and len(origin['polls'])<=128,'ACTUAL_ROOT_API_ORIGIN');session=None;terminal=False;outputs=[]
    for i,frame in enumerate([origin['launch'],*origin['polls']]):
        closed(frame,'toolName actualArguments unmodifiedResponse');need(not terminal,'NO_DUPLICATE_AFTER_TERMINAL');a=frame['actualArguments'];r=frame['unmodifiedResponse'];need(type(r) is dict,'UNMODIFIED_API_OBJECT')
        if i==0:need(frame['toolName']=='tools.exec_command' and a==expected and set(a)==set('cmd workdir login yield_time_ms max_output_tokens'.split()),'EXACT_FIVE_KEY_FOREGROUND_REQUEST')
        else:need(frame['toolName']=='tools.write_stdin' and a['session_id']==session and a.get('chars','')=='' and set(a)<=set('session_id chars yield_time_ms max_output_tokens'.split()),'GENUINE_SAME_SESSION_ALL_POLLS')
        if r.get('exit_code') is not None:need(r['exit_code']==0 and (r.get('session_id') is None or r['session_id']==session),'NATURAL_OUTER_TERMINAL0');terminal=True
        else:
            need(type(r.get('session_id')) is int and r['session_id']>0,'REAL_YIELDED_SESSION');session=session or r['session_id'];need(session==r['session_id'],'SAME_SESSION_RESPONSE')
        if 'output' in r:need(type(r['output']) is str and len(r['output'].encode())<=16777216,'BOUNDED_ACTUAL_API_OUTPUT');outputs.append(r['output'])
    need(terminal,'COMPLETE_TERMINAL_ORIGIN_REQUIRED');return ''.join(outputs)
