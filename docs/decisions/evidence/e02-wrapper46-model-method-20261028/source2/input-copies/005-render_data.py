"""Pure closed deterministic render helpers. SOURCE preparation, no execution grant."""
import copy
from pathlib import Path
import re

CONFIG_KEYS=set('schema runId operator createdAtUtcMillis outputRoot environment ordinaryManifest ordinaryOrigin readRoots sourceSubject consumerControls'.split())
RELEASE_KEYS=set('schema phase config sourceSubject operator issuedAtUtcMillis notAfterUtcMillis sourceQa sourceSecurity input reviewOrigin primaryTool'.split())
RUNS=Path('/Data/nbdp-e02-tooling-20261027/ordinary-completion-r3/runs')
RENDER_AUTHORITY='FIXED_SAME_T0_ENV_CONFIG_AND_PRIMARY_RELEASE_ONLY'


def need(ok,message):
    if not ok:raise ValueError(message)


def pin_shape(value):
    need(type(value) is dict and set(value)=={'path','bytes','sha256'},'CLOSED_PIN')
    need(type(value['path']) is str and Path(value['path']).is_absolute() and '..' not in Path(value['path']).parts,'CANONICAL_PIN')
    need(type(value['bytes']) is int and 0<=value['bytes']<=2147483648 and type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']),'PIN_DOMAIN')
    return value


def config_intent(template,run,source,t0_ms):
    need(type(template) is dict and set(template)==CONFIG_KEYS,'CLOSED_CONFIG_TEMPLATE')
    need(template['schema']=='e02-completion-run-config-v2' and template['runId']==run and re.fullmatch('[0-9a-f]{32}',run),'FIXED_CONFIG_RUN')
    need(template['createdAtUtcMillis'] is None and template['environment'] is None,'ONLY_NULL_CONFIG_CLOCK_ENV_SLOTS')
    need(type(t0_ms) is int and 0<t0_ms<=9007199254740991,'EXACT_ACTUAL_T0')
    need(template['outputRoot']==str(RUNS/run) and template['sourceSubject']==source,'FIXED_CONFIG_SOURCE_OUTPUT')
    need(type(template['operator']) is str and template['operator'].startswith('/root'),'ROOT_OPERATOR')
    for key in ('ordinaryManifest','ordinaryOrigin','sourceSubject','consumerControls'):pin_shape(template[key])
    need(type(template['readRoots']) is list and 0<len(template['readRoots'])<=16 and all(type(p) is str and Path(p).is_absolute() and '..' not in Path(p).parts for p in template['readRoots']),'CLOSED_READ_ROOTS')
    result=copy.deepcopy(template);result['createdAtUtcMillis']=t0_ms
    need({k:v for k,v in result.items() if k!='createdAtUtcMillis'}=={k:v for k,v in template.items() if k!='createdAtUtcMillis'},'T0_ONLY_INTENT_RENDER')
    return result


def environment_slot_config(intent,environment_pin,environment,now_ms):
    need(type(intent) is dict and set(intent)==CONFIG_KEYS and intent['environment'] is None,'UNCHANGED_CONFIG_INTENT_REQUIRED')
    pin_shape(environment_pin)
    need(type(environment) is dict and set(environment)=={'schema','runId','operator','observedAtUtcMillis','relays','proxyReceipt'},'CLOSED_ACTUAL_ENVIRONMENT')
    need(environment['schema']=='e02-completion-runtime-environment-v2' and environment['runId']==intent['runId'] and environment['operator']==intent['operator'],'CURRENT_ENVIRONMENT_RUN_OPERATOR')
    need(type(intent['createdAtUtcMillis']) is int and type(environment['observedAtUtcMillis']) is int and type(now_ms) is int and 0<intent['createdAtUtcMillis']<=environment['observedAtUtcMillis']<=now_ms,'ACTUAL_T0_BEFORE_OBSERVATIONS')
    need(type(environment['relays']) is list and len(environment['relays'])==2,'TWO_ACTUAL_RELAY_INSPECTIONS')
    pin_shape(environment['proxyReceipt'])
    result=copy.deepcopy(intent);result['environment']=copy.deepcopy(environment_pin)
    need({k:v for k,v in result.items() if k!='environment'}=={k:v for k,v in intent.items() if k!='environment'},'ENVIRONMENT_SLOT_ONLY_SAME_T0')
    return result


def primary_release(template,config_pin,source,operator,reviews,now_ms,outer_expires_ms):
    need(type(template) is dict and set(template)==RELEASE_KEYS,'CLOSED_PRIMARY_RELEASE_TEMPLATE')
    need(template['schema']=='e02-completion-root-release-v2' and template['phase']=='primary','PRIMARY_PHASE_ONLY')
    need(template['config'] is None and template['issuedAtUtcMillis'] is None and template['notAfterUtcMillis'] is None,'ONLY_NULL_PRIMARY_RENDER_SLOTS')
    need(template['sourceSubject']==source and template['operator']==operator and [template['sourceQa'],template['sourceSecurity']]==reviews,'FIXED_SOURCE_OPERATOR_REVIEWS')
    need(all(template[k] is None for k in ('input','reviewOrigin','primaryTool')),'NO_ARBITRARY_INPUT_OR_REVIEW_WRITER')
    for p in [config_pin,source,*reviews]:pin_shape(p)
    need(type(now_ms) is int and type(outer_expires_ms) is int and 0<now_ms<=9007199254740991-243000 and now_ms+243000<=outer_expires_ms,'FULL_PRIMARY_ROOT_TIME_REMAINS')
    result=copy.deepcopy(template);result.update(config=copy.deepcopy(config_pin),issuedAtUtcMillis=now_ms,notAfterUtcMillis=now_ms+243000)
    need({k:v for k,v in result.items() if k not in ('config','issuedAtUtcMillis','notAfterUtcMillis')}=={k:v for k,v in template.items() if k not in ('config','issuedAtUtcMillis','notAfterUtcMillis')},'EXACT_PRIMARY_RENDER_ONLY')
    return result


def child_command(timeout,node,runner,config,release,output):
    for p in (timeout,node,runner,config,release):pin_shape(p)
    need(timeout['path']=='/usr/bin/timeout' and node['path']=='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node','FIXED_CHILD_TOOLS')
    need(Path(runner['path']).name=='runner.mjs' and 'shared/run.mjs' not in runner['path'],'CURRENT_COMPLETION_RUNNER_ONLY')
    need(type(output) is str and Path(output).is_absolute() and Path(output).name=='primary','PRIVATE_PRIMARY_OUTPUT')
    return [timeout['path'],'--signal=TERM','--kill-after=3s','240s',node['path'],runner['path'],'primary',config['path'],config['sha256'],release['path'],release['sha256'],'NONE','NONE',output]


def regular_capture_shape(code,stdout_bytes,stderr_bytes):
    need(type(code) is int and code==0,'INNER_PROCESS_NONZERO_OR_TIMEOUT')
    need(type(stdout_bytes) is int and 0<stdout_bytes<4194304 and type(stderr_bytes) is int and stderr_bytes==0,'REGULAR_FILE_CAPTURE_LIMIT_OR_STDERR')
    return 'REGULAR_FILES_NO_PIPE_EOF_OR_NODE_API_ATTESTATION'


def reserve(end,now,seconds=243):
    need(type(end) in (int,float) and type(now) in (int,float) and end-now>seconds,'FINITE_DEADLINE_RESERVE')
    return seconds


def inner_receipt(request,completion,argv,cwd,config,release,subject):
    need(type(request) is dict and set(request)==set('schema argv cwd environment startedUtcNs jobSeconds killGraceSeconds config release'.split()),'CLOSED_INNER_PROCESS_REQUEST')
    need(request['schema']=='e02-wrapper-inner-process-request-v1' and request['argv']==argv and request['cwd']==cwd and request['config']==config and request['release']==release,'EXACT_INNER_PROCESS_JOIN')
    need(request['jobSeconds']==240 and request['killGraceSeconds']==3,'EXACT_INNER_CLOCKS')
    need(type(completion) is dict and set(completion)==set('schema exitCode stdout stderr finishedUtcNs finishedUtcNsExact captureTransport pipeEofEstablished innerApiAttestation primarySubject'.split()),'NO_FABRICATED_INNER_API_PID_REAP_FIELDS')
    need(completion['schema']=='e02-wrapper-inner-process-completion-v2' and completion['captureTransport']=='REGULAR_FILES' and completion['pipeEofEstablished'] is False and completion['innerApiAttestation'] is False,'TRUTHFUL_INNER_PROCESS_CAPTURE')
    need(completion['primarySubject']==subject and request['startedUtcNs']<=completion['finishedUtcNs'],'CURRENT_INNER_SUBJECT_INTERVAL')
    need(completion['finishedUtcNsExact']==str(completion['finishedUtcNs']),'EXACT_OBSERVED_FINISH_NS')
    regular_capture_shape(completion['exitCode'],completion['stdout']['bytes'],completion['stderr']['bytes'])
    return completion


def actual_outer_responses(records,expected_arguments):
    need(type(records) is list and 1<=len(records)<=64,'BOUNDED_ACTUAL_OUTER_RESPONSES')
    session=None;terminal=False
    for i,record in enumerate(records):
        need(type(record) is dict and set(record)=={'toolName','actualArguments','unmodifiedResponse'},'CLOSED_ACTUAL_TOOL_RECORD')
        args,response=record['actualArguments'],record['unmodifiedResponse']
        need(type(args) is dict and type(response) is dict and not terminal,'UNCHANGED_RESPONSE_REQUIRED')
        if i==0:
            need(record['toolName']=='tools.exec_command' and args==expected_arguments,'EXACT_OUTER_PYTHON_API_REQUEST')
        else:need(record['toolName']=='tools.write_stdin' and args.get('session_id')==session and args.get('chars','')=='','SAME_SESSION_ONLY_EMPTY_POLLS')
        if response.get('exit_code') is not None:
            need(response['exit_code']==0,'OUTER_API_NONZERO');terminal=True
            need(response.get('session_id') in (None,session),'TERMINAL_SESSION_JOIN')
        else:
            need(type(response.get('session_id')) is int and response['session_id']>0,'ACTUAL_YIELDED_SESSION')
            if session is None:session=response['session_id']
            need(response['session_id']==session,'YIELDED_SESSION_SUBSTITUTION')
    need(terminal,'ACTUAL_TERMINAL_OUTER_RESPONSE_REQUIRED')
    return 'EXTERNALLY_AUTHENTICATED_OUTER_PYTHON_API_ONLY'


def phase_admission(release,config,now_ns):
    need(type(release) is dict and release.get('schema')=='e02-completion-root-release-v2' and release.get('phase')=='primary' and release.get('config')==config,'EXACT_CURRENT_PRIMARY_PHASE_CONFIG')
    issued,expiry=release.get('issuedAtUtcMillis'),release.get('notAfterUtcMillis')
    need(type(issued) is int and type(expiry) is int and expiry-issued==243000 and type(now_ns) is int and issued*1000000<=now_ns,'FIXED243_PHASE_CLOCKS')
    left=(expiry*1000000-now_ns)/1e9
    need(left>240,'INSUFFICIENT_STRICT_PHASE_BUDGET')
    return left-3 # Existing kill grace reserved inside phase243; no added lease.


def phase_finished(release,config,finished_ns):
    need(release.get('phase')=='primary' and release.get('config')==config and type(finished_ns) is int and release['issuedAtUtcMillis']*1000000<=finished_ns<=release['notAfterUtcMillis']*1000000,'ACTUAL_COMPLETION_BEFORE_CURRENT_PHASE_EXPIRY')
    return finished_ns


def proxy_completion(receipt):
    need(type(receipt) is dict and set(receipt)==set('returnCode reaped ownedPopenHandleOnly terminationRequested killRequested stdout stderr'.split()),'CLOSED_ACTUAL_PROXY_COMPLETION')
    need(receipt['terminationRequested'] is True and receipt['killRequested'] is False and receipt['returnCode']==0 and receipt['reaped'] is True and receipt['ownedPopenHandleOnly'] is True,'EXPECTED_GRACEFUL_SIGTERM_PROXY_COMPLETION')
    regular_capture_shape(receipt['returnCode'],receipt['stdout']['bytes'],receipt['stderr']['bytes'])
    return receipt
