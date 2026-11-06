"""Finite once-only consumer5 pure DATA capture; SOURCE review only until root release.
Core child PIPE/session/absolute-reap functions are copied exactly from9465dbfe.
No model/runtime occurs on import. No SDK/Android/native/network/client claim.
"""
import hashlib,json,os,pathlib,re,selectors,signal,stat,subprocess,sys,time
HERE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/consumer5-control-capture-preparation-r1')
OUTPUT=HERE/'actual'
GRANT=HERE/'coordinator-acknowledgement.json'
ROOT=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP')
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
ACTOR='/root/r5_plan_fix'


def need(v,m):
    if not v:raise ValueError(m)

def safe(p):
    p=pathlib.Path(p);need(p.is_absolute() and '..' not in p.parts,'CANONICAL_PATH')
    for q in (p,*p.parents):need(not q.is_symlink(),'SYMLINK_PATH')
    return p

def pin(p):
    p=safe(p);initial=p.lstat()
    need(stat.S_ISREG(initial.st_mode) and initial.st_size<=8589934592,'REGULAR_BOUNDED_INPUT')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);h=hashlib.sha256();n=0
    def identity(v):return (v.st_dev,v.st_ino,v.st_mode,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
    with os.fdopen(fd,'rb') as f:
        opened=os.fstat(f.fileno());need(stat.S_ISREG(opened.st_mode) and identity(opened)==identity(initial),'OPENED_REGULAR_IDENTITY')
        while block:=f.read(1048576):n+=len(block);need(n<=8589934592,'PIN_BOUND');h.update(block)
        need(identity(os.fstat(f.fileno()))==identity(initial) and n==initial.st_size,'INPUT_CHANGED_DURING_READ')
    need(identity(p.lstat())==identity(initial),'INPUT_CHANGED_AFTER_READ')
    return dict(path=str(p),bytes=n,sha256=h.hexdigest(),mode=oct(initial.st_mode&0o777))

def descriptor(p):return {k:v for k,v in pin(p).items() if k!='mode'}

def checked(d):need(type(d) is dict and set(d)=={'path','bytes','sha256'} and descriptor(d['path'])==d,'EXACT_PIN');return safe(d['path'])

def load(p):
    raw=safe(p).read_bytes();need(len(raw)<=16777216,'METADATA_BOUND')
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_KEY');out[k]=v
        return out
    def reject(_):raise ValueError('INTEGER_METADATA_ONLY')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=reject,parse_float=reject)

def put(root,name,value):
    raw=value if type(value) is bytes else (json.dumps(value,indent=2)+'\n').encode()
    with (root/name).open('xb') as f:f.write(raw)

def signal_owned_group(p,ownership):
    # The retained Popen leader has not been poll()/wait()-reaped before fault
    # signalling. Even an exited zombie leader reserves its PID/PGID, preventing
    # reuse while descendants may keep the group's PIPE descriptors open.
    need(ownership['ownedPopenHandle'] is True and ownership['startNewSession'] is True and ownership['pid']==p.pid==ownership['groupId']==ownership['sessionId'] and p.returncode is None,'UNREAPED_OWNED_GROUP_REQUIRED')
    try:
        os.killpg(ownership['groupId'],signal.SIGKILL)
        return dict(groupId=ownership['groupId'],signal='SIGKILL',status='SIGNALLED_BEFORE_LEADER_REAP',leaderReapedBeforeSignal=False)
    except ProcessLookupError:
        return dict(groupId=ownership['groupId'],signal='SIGKILL',status='OWNED_GROUP_ABSENT',leaderReapedBeforeSignal=False)

def finish_owned(p,ownership,fault,job_deadline_ns):
    # ONE absolute reap deadline, initialized once. Every wait, including an
    # immediate retry after KILL, uses only its remaining time, never a new3s.
    reap_deadline_ns=min(job_deadline_ns+3000000000,time.monotonic_ns()+3000000000)
    closure=None;closure_fault=None;code=None;reaped=False
    def close_group():
        nonlocal closure,closure_fault
        try:closure=signal_owned_group(p,ownership)
        except BaseException as error:closure_fault=type(error).__name__+':'+str(error)
    def wait_remaining():return p.wait(timeout=max(0,(reap_deadline_ns-time.monotonic_ns())/1e9))
    if fault is not None:close_group() # Independent of leader liveness; no poll().
    try:code=wait_remaining();reaped=True
    except subprocess.TimeoutExpired:
        fault=fault or 'REAP_TIMEOUT'
        if closure is None and closure_fault is None:close_group()
        try:code=wait_remaining();reaped=True
        except subprocess.TimeoutExpired:fault=fault or 'OWNED_CHILD_NOT_REAPED'
        except BaseException as error:closure_fault=closure_fault or type(error).__name__+':'+str(error)
    except BaseException as error:
        fault=fault or type(error).__name__+':'+str(error)
        if closure is None and closure_fault is None:close_group()
        try:code=wait_remaining();reaped=True
        except subprocess.TimeoutExpired:pass
        except BaseException as error:closure_fault=closure_fault or type(error).__name__+':'+str(error)
    if not reaped:fault=fault or 'OWNED_CHILD_NOT_REAPED'
    if closure_fault:fault=fault or 'OWNED_GROUP_CLOSURE_ERROR'
    return dict(exitCode=code,reaped=reaped,fault=fault,reapDeadlineMonotonicNs=reap_deadline_ns,groupClosure=closure,groupClosureFault=closure_fault)

def capture_scope(root,scope,index):
    stem='%02d-'%index+scope['scope'];put(root,stem+'-request.json',dict(argv=scope['argv'],cwd=scope['cwd'],environment=ENV,stdin='DEVNULL',transport='CHILD_PIPES_OUTER_API_SEPARATE',seconds=60,reapSeconds=3))
    start=time.monotonic_ns();job_deadline_ns=start+60000000000
    sel=selectors.DefaultSelector() # Failure here occurs before any owned child exists.
    ownership=dict(pid=None,groupId=None,sessionId=None,startNewSession=True,ownedPopenHandle=True,leaderOwnership='RETAINED_UNPOLLED_UNREAPED_POPEN_UNTIL_GROUP_FAULT_SIGNAL')
    buffers={'stdout':bytearray(),'stderr':bytearray()};eof={'stdout':False,'stderr':False};fault=None
    try:p=subprocess.Popen(scope['argv'],cwd=scope['cwd'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env=ENV)
    except BaseException:
        sel.close();raise
    try:
        ownership['pid']=ownership['groupId']=ownership['sessionId']=p.pid
        ownership['observedGroupId']=os.getpgid(p.pid);ownership['observedSessionId']=os.getsid(p.pid)
        need(ownership['observedGroupId']==ownership['observedSessionId']==p.pid,'ACTUAL_OWNED_SESSION_GROUP_IDENTITY')
        put(root,stem+'-owned-child.json',ownership)
        for name,pipe,cap in [('stdout',p.stdout,1048576),('stderr',p.stderr,262144)]:
            os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,(name,cap))
        while sel.get_map():
            if time.monotonic_ns()>job_deadline_ns:fault='TIMEOUT';break
            for key,_ in sel.select(.05):
                name,cap=key.data;block=os.read(key.fd,8192)
                if not block:sel.unregister(key.fileobj);eof[name]=True;continue
                if len(buffers[name])+len(block)>cap:fault='CAPTURE_LIMIT';break
                buffers[name].extend(block)
            if fault:break
    except BaseException as error:fault=fault or type(error).__name__+':'+str(error)
    # No poll()/wait() occurs before fault closure. An exited leader cannot hide
    # descendants that still hold stdout/stderr open. No EOF is synthesized.
    custody=finish_owned(p,ownership,fault,job_deadline_ns)
    finished=time.monotonic_ns();sel.close();p.stdout.close();p.stderr.close()
    put(root,stem+'.stdout.raw',bytes(buffers['stdout']));put(root,stem+'.stderr.raw',bytes(buffers['stderr']))
    result=dict(scope=scope['scope'],argv=scope['argv'],eof=eof,elapsedNs=finished-start,stdout=pin(root/(stem+'.stdout.raw')),stderr=pin(root/(stem+'.stderr.raw')),pipeEofScope='ACTUAL_OWNED_CHILD_PIPES_ONLY_NOT_OUTER_API',ownership=ownership,**custody)
    put(root,stem+'-result.json',result)
    return result,bytes(buffers['stdout']),bytes(buffers['stderr'])

def reviews(rows,subject,decision,forbidden):
    need(type(rows) is dict and set(rows)=={'qa','security'},'EXACT_INDEPENDENT_PAIR')
    sessions=[]
    for role in ('qa','security'):
        value=load(checked(rows[role]));need(set(value)=={'role','session','decision','subject'},'CLOSED_ACTUAL_REVIEW')
        need(value['role']==role and value['subject']==subject and value['decision']==decision,'EXACT_ACTUAL_REVIEW_BINDING')
        need(type(value['session']) is str and value['session'].startswith('/root/') and value['session'] not in forbidden,'AUTHOR_OPERATOR_CANNOT_REVIEW')
        sessions.append(value['session'])
    need(len(set(sessions))==2 and rows['qa']['sha256']!=rows['security']['sha256'],'DISTINCT_QA_SECURITY')

def admission():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.argv[:3]==[str(HERE/'capture.py'),'--execute-once','--root-ack-sha'] and len(sys.argv)==4 and re.fullmatch('[0-9a-f]{64}',sys.argv[3]),'EXACT_ISOLATED_ONCE_ENTRY')
    method_pin=descriptor(HERE/'method-source.json');method=load(method_pin['path'])
    plan_pin=descriptor(HERE/'plan.json');plan=load(plan_pin['path']);manifest_pin=descriptor(HERE/'input-manifest.json');manifest=load(manifest_pin['path'])
    need(method['schema']=='e02-consumer5-capture-method-source-v1' and method['plan']==plan_pin and method['inputManifest']==manifest_pin,'EXACT_FROZEN_METHOD')
    for d in method['sources']:checked(d)
    need(descriptor(HERE/'capture.py') in method['sources'],'SELF_CODE_PIN_REQUIRED')
    need(plan['schema']=='e02-consumer5-fixed-control-capture-plan-v1' and plan['consumerSource']==method['consumerSource'] and plan['consumerPacket']==method['consumerPacket'],'CURRENT_CONSUMER_METHOD_JOIN')
    need(plan['inputManifest']==manifest_pin and plan['environment']==ENV and plan['scopeCounts']==[86,36,8,9],'FIXED_INPUTS_ENV_COUNTS')
    need(plan['limits']==dict(childSeconds=60,absoluteChildReapSeconds=3,stdoutBytes=1048576,stderrBytes=262144,outerSeconds=297) and plan['stopFirstFailure'] is True and plan['noRetry'] is True,'UNCHANGED_FINITE_BUDGETS')
    source=load(checked(plan['consumerSource']));packet=load(checked(plan['consumerPacket']));sourceplan=load(checked(plan['consumerControlPlan']))
    need(source['schema']=='e02-ordinary-minimum-consumer5-source-subject-v1' and source['sourceCount']==14 and len(source['sources'])==14 and packet['subject']==plan['consumerSource'] and packet['sources']==source['sources'],'EXACT_CURRENT14_SOURCE')
    need(source['controlPlan']==plan['consumerControlPlan'] and method['consumerSource']==plan['consumerSource'],'CURRENT_SOURCE_PLAN_JOIN')
    need(str(pathlib.Path(sys.executable).resolve())==sourceplan['interpreter']['path'],'PINNED_PYTHON')
    request=load(HERE/'outer-request-template.json')
    need(request==plan['outerRequestTemplate']==sourceplan['outerRequestTemplate'] and set(request)=={'cmd','workdir','login','yield_time_ms','max_output_tokens'} and request['login'] is False,'FIVE_KEY_FROZEN_OUTER_REQUEST')
    need(plan['rootAcknowledgementPath']==str(GRANT) and plan['outputRoot']==str(OUTPUT),'FIXED_ROOT_ACK_OUTPUT')
    need(len(plan['scopes'])==4,'FOUR_ONLY_SEQUENTIAL_SCOPES')
    for scope,s in zip(plan['scopes'],sourceplan['scopes']):
        need(set(scope)=={'scope','argv','cwd','count','expectedNames','source','format'},'CLOSED_SCOPE')
        need(scope['scope']==s['name'] and scope['source']==s['source'] and scope['argv']==s['argv'] and scope['cwd']==s['cwd'] and scope['count']==s['count'] and scope['expectedNames']==sorted(s['exactDefinedNames']) and scope['format']=='VERBOSE_UNITTEST_NAMED','EXACT_SOURCE_RESOLVED_CASES_ARGV')
    need(manifest['schema']=='e02-consumer5-capture-known-inputs-v1' and manifest['sdkTreeIncluded'] is False and manifest['fullRuntimeClientClosureClaimed'] is False,'KNOWN_SOURCE_CLOSURE_ONLY')
    paths=[checked(d) for d in manifest['files']]
    need(len(paths)==manifest['actualInputCount'] and len(set(paths))==len(paths),'EXACT_UNIQUE_INPUTS')
    for d in source['sources']:need(checked(d) in paths,'ALL14_CURRENT_MODULES')
    paths.extend([safe(HERE/name) for name in ('capture.py','plan.json','input-manifest.json','outer-request-template.json','method-source.json')])
    grant_pin=descriptor(GRANT);need(grant_pin['sha256']==sys.argv[3],'ACTUAL_EXTERNAL_ACK_DIGEST')
    grant=load(GRANT)
    need(set(grant)==set('schema actor executionAuthorized purpose consumerSource methodSource plan inputManifest outerRequest authors operators consumerSourceReviews captureSourceReviews noRetry runtimeAuthorized servicesAuthorized sdkAuthorized nativeAuthorized androidAuthorized'.split()),'CLOSED_EXTERNAL_ROOT_ACK')
    need(grant['schema']=='e02-consumer5-control-capture-root-ack-v1' and grant['actor']=='/root' and grant['executionAuthorized'] is True and grant['purpose']=='ONE_FIXED_CONSUMER5_86_36_8_9_DATA_BATCH_ONLY' and grant['consumerSource']==plan['consumerSource'] and grant['methodSource']==method_pin and grant['plan']==plan_pin and grant['inputManifest']==manifest_pin and grant['outerRequest']==descriptor(HERE/'outer-request-template.json') and grant['noRetry'] is True,'EXACT_FINITE_EXTERNAL_AUTHORITY')
    need(all(grant[k] is False for k in ('runtimeAuthorized','servicesAuthorized','sdkAuthorized','nativeAuthorized','androidAuthorized')),'NO_RUNTIME_SDK_SERVICES_AUTHORITY')
    need(type(grant['authors']) is list and type(grant['operators']) is list and grant['authors'] and grant['operators'] and all(type(a) is str and a.startswith('/root') for a in grant['authors']+grant['operators']),'DECLARED_ACTUAL_ACTORS')
    need(ACTOR in grant['authors'] and all(a in grant['authors'] for a in method['sourceAuthors']),'ALL_CAPTURE_SOURCE_AUTHORS_DECLARED')
    forbidden=set(grant['authors']+grant['operators']+[ACTOR,'/root',source['author'],source['coordinator'],'/root/producer3_capture','/root/r5','/root/completion_wrapper'])
    reviews(grant['consumerSourceReviews'],plan['consumerSource'],'ACCEPT_EXACT_SOURCE_CODE_AND_CONTROL_DEFINITIONS_ONLY',forbidden)
    reviews(grant['captureSourceReviews'],method_pin,'ACCEPT_CONSUMER5_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY',forbidden)
    for pair in (grant['consumerSourceReviews'],grant['captureSourceReviews']):
        paths.extend(checked(d) for d in pair.values())
    paths.append(checked(grant_pin));paths=list(dict.fromkeys(paths))
    need(not OUTPUT.exists() and not OUTPUT.is_symlink(),'ONE_USE_FRESH_OUTPUT_NO_RETRY')
    return plan,paths,grant,grant_pin,method_pin

def outcome(scope,result,stdout,stderr):
    need(result['exitCode']==0 and result['reaped'] is True and result['fault'] is None and result['eof']=={'stdout':True,'stderr':True} and result['groupClosure'] is None and result['groupClosureFault'] is None,'NATURAL_ZERO_NO_FORCE_ERROR_FULL_ACTUAL_CHILD_EOF')
    need(stdout==b'','PYTHON_STDOUT_EMPTY');text=stderr.decode('utf-8','strict');lines=text.splitlines();names=[]
    for line in lines:
        m=re.fullmatch(r'(test_\w+) \(__main__\.(\w+)\.(test_\w+)\) \.\.\. ok',line)
        if m:need(m[1]==m[3],'NAMED_TEST_JOIN');names.append(m[2]+'.'+m[3])
    need(names==scope['expectedNames'] and len(names)==scope['count'],'EXACT_SORTED_UNITTEST_MEMBERSHIP_NO_SKIPS')
    prefix=''.join(line+'\n' for line in lines[:len(names)])
    need(all(re.fullmatch(r'test_\w+ \(__main__\.\w+\.test_\w+\) \.\.\. ok',line) for line in lines[:len(names)]),'NO_EXTRA_PYTHON_PREFIX')
    need(re.fullmatch(r'\n-{70}\nRan '+str(scope['count'])+r' tests in [0-9]+\.[0-9]+s\n\nOK\n',text[len(prefix):]),'EXACT_VERBOSE_UNITTEST_SUMMARY_NO_SKIP_OR_ERROR')
    return dict(scope=scope['scope'],count=len(names),names=names,allOk=True)

def main():
    os.umask(0o077);plan,paths,grant,grant_pin,method_pin=admission();before=[pin(p) for p in paths]
    safe(OUTPUT).mkdir(mode=0o700)
    put(OUTPUT,'admission.json',dict(consumerSource=plan['consumerSource'],captureSource=method_pin,controlPlan=descriptor(HERE/'plan.json'),rootAcknowledgement=grant_pin,authors=grant['authors'],operators=grant['operators'],inputsBefore=before,snapshotNotRaceFree=True))
    started=time.monotonic_ns();captures=[];outcomes=[];fault=None
    try:
        for i,scope in enumerate(plan['scopes'],1):
            need([pin(p) for p in paths]==before,'INPUT_CHANGED_BEFORE_SCOPE')
            result,stdout,stderr=capture_scope(OUTPUT,scope,i);captures.append(result)
            outcomes.append(outcome(scope,result,stdout,stderr))
            need([pin(p) for p in paths]==before,'INPUT_CHANGED_AFTER_SCOPE')
    except BaseException as error:fault=type(error).__name__+':'+str(error)
    after=None
    try:after=[pin(p) for p in paths];need(after==before,'INPUT_CHANGED_OVERALL')
    except BaseException as error:fault=fault or type(error).__name__+':'+str(error)
    counts=[row['count'] for row in outcomes];matched=fault is None and counts==[86,36,8,9] and after==before
    result=dict(schema='e02-consumer5-current-control-capture-result-v1',consumerSource=plan['consumerSource'],consumerPacket=plan['consumerPacket'],captureSource=method_pin,controlPlan=descriptor(HERE/'plan.json'),rootAcknowledgement=grant_pin,authors=grant['authors'],operators=grant['operators'],state='WRITES_STOPPED_PENDING_INDEPENDENT_DATA_QA_SECURITY' if matched else 'FAILED_OR_UNQUALIFIED_NO_RETRY',scopeCounts=counts,expectedCounts=[86,36,8,9],captures=captures,outcomes=outcomes,fault=fault,elapsedNs=time.monotonic_ns()-started,inputsBefore=before,inputsAfter=after,inputsUnchanged=after==before,exitCode=0 if matched else 2,snapshotNotRaceFree=True,scope='PURE_SYNTHETIC_CONSUMER_DATA_ONLY_NO_CLIENT_INTEROPERABILITY',outerApiOrigin='ACTUAL_ROOT_RESPONSES_RECORDED_SEPARATELY_NOT_INNER_API_OR_OUTER_EOF',runtimeAuthorized=False,ordinaryRowsQualified=0,canonicalE02='PARTIAL22_UNCHANGED')
    put(OUTPUT,'result.json',result)
    put(OUTPUT,'raw-artifact-manifest.json',dict(schema='e02-consumer5-control-raw-artifact-manifest-v1',files=[descriptor(p) for p in sorted(OUTPUT.iterdir()) if p.is_file()]))
    print(json.dumps(dict(result=descriptor(OUTPUT/'result.json'),state=result['state'],scopeCounts=counts,fault=fault,inputsUnchanged=after==before)))
    return 0 if matched else 2

if __name__=='__main__':raise SystemExit(main())
