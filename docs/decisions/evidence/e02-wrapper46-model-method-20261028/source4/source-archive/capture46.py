"""SOURCE-only prepared finite46 capture. Requires external exact root release.
Selector/Popen/PIPE custody derives from accepted capture-r2.py; never executes on import.
"""
import hashlib,json,os,pathlib,re,selectors,signal,stat,subprocess,sys,time
HERE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/wrapper46-model-method-preparation-r4')
R3=pathlib.Path('/Data/nbdp-e02-tooling-20261027/completion-primary-wrapper-preparation-r4')
SCOPE='E02_WRAPPER_R4_REVIEW_EXPIRY_IDENTITY_DISPATCH_ORIGIN'
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
PYTHON='/home/peterhorvath/.miniforge3/bin/python3.13'
NODE='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'
OUTPUT=pathlib.Path('/Data/nbdp-e02-tooling-20261027/wrapper46-model-actual-r4/capture')
GRANT=OUTPUT.parent/'root-release.json'

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

def admission():
    need(sys.flags.isolated and sys.dont_write_bytecode and str(pathlib.Path(sys.executable).resolve())==PYTHON and sys.argv==[str(HERE/'capture46.py')],'EXACT_ISOLATED_HARNESS')
    plan_pin=descriptor(HERE/'plan.json');plan=load(plan_pin['path']);subject_pin=descriptor(HERE/'method-source.json');subject=load(subject_pin['path']);manifest_pin=descriptor(HERE/'code-manifest.json');manifest=load(manifest_pin['path'])
    need(plan['schema']=='e02-wrapper46-pure-model-capture-plan-v4' and plan['scopeVersion']==SCOPE and plan['scopeCounts']==[6,13,16,11] and plan['modelsDefined']==46,'EXACT46_SCOPE')
    need(plan['environment']==ENV and plan['limits']==dict(childSeconds=60,childReapSeconds=3,stdoutBytes=1048576,stderrBytes=262144,outerSeconds=297,outerSignal='KILL'),'EXACT_CAPTURE_LIMITS_ENV')
    need(set(plan['outerRequest'])=={'cmd','workdir','yield_time_ms','max_output_tokens','login'} and plan['outerRequest']['login'] is False,'COMPLETE_FIVE_KEY_REQUEST_LOGIN_FALSE')
    need(plan['outerRequestTemplate']==descriptor(HERE/'outer-request-template.json') and plan['outerRequest']==load(HERE/'outer-request-template.json'),'EXACT_FROZEN_ROOT_OUTER_REQUEST')
    need(plan['rootReleasePath']==str(GRANT) and plan['outputRoot']==str(OUTPUT) and plan['r3Root']==str(R3),'FIXED_OUTPUT_AND_SOURCE')
    need(plan['tools']['python']['path']==PYTHON and plan['tools']['node']['path']==NODE,'EXACT_TOOLS')
    need(subject['schema']=='e02-wrapper46-model-method-source-v4' and subject['plan']==plan_pin and subject['codeManifest']==manifest_pin,'EXACT_METHOD_SOURCE')
    for d in subject['sources']:checked(d)
    need(descriptor(HERE/'capture46.py') in subject['sources'] and descriptor(HERE/'invoke-origin11.mjs') in subject['sources'],'REVIEWED_HARNESS_BOOTSTRAP')
    need(manifest['schema']=='e02-wrapper46-known-code-inputs-v1' and manifest['scope']=='KNOWN_CODE_ONLY_NOT_RECURSIVE_RUNTIME_SDK_CLIENT_CLOSURE','KNOWN_CODE_CLOSURE')
    paths=[checked(d) for d in manifest['inputs']]+[checked(subject_pin),checked(manifest_pin)]
    need(len(paths)==len(set(paths)),'NO_DUPLICATE_CODE_INPUTS')
    need(all(p.is_relative_to(HERE) or p.is_relative_to(R3) or str(p) in manifest['fixedExternalCodePaths'] for p in paths),'FIXED_PROTECTED_CODE_PATHS')
    need(descriptor(R3/'model-plan.json')==manifest['r3ModelPlan'],'EXACT_R3_MODEL_PLAN')
    r3packet=load(checked(plan['r3SourcePacket']));need(plan['r3SourcePacket']['sha256']=='ddac89d2e5e79f8fc60361184c437ff4b6f2181ba31868b607c72d7deb428feb','APPROVED_R4_CODE_ONLY_SUBJECT')
    for d in r3packet['sources']:checked(d);need(safe(d['path']) in paths,'ALL_FROZEN_R3_CODE_PROTECTED')
    for d in plan['tools'].values():checked(d);need(safe(d['path']) in paths,'TOOLS_PROTECTED')
    need(len(plan['scopes'])==4,'FOUR_SEQUENTIAL_SCOPES')
    scripts=['test_render_data.py','test_wrapper_models.py','test_r3_decision_paths.py']
    for i,scope in enumerate(plan['scopes']):
        need(scope['count']==[6,13,16,11][i] and len(scope['expectedNames'])==scope['count'] and len(set(scope['expectedNames']))==scope['count'] and scope['cwd']==str(R3),'EXACT_NAMED_SCOPE')
        expected=[PYTHON,'-I','-B',str(R3/scripts[i])] if i<3 else [NODE,str(HERE/'invoke-origin11.mjs')]
        need(scope['argv']==expected and scope['format']==('VERBOSE_UNITTEST_NAMED' if i<3 else 'NODE_ACTUAL_MODEL_ROWS'),'EXACT_FROZEN_CHILD_COMMAND')
    # External actual root authority is checked, not synthesized by this method.
    grant_pin=descriptor(GRANT);grant=load(grant_pin['path'])
    need(set(grant)==set('schema actor executionAuthorized scope methodSource plan codeManifest outerRequest authors operators sourceReviews'.split()),'CLOSED_EXTERNAL_ROOT_RELEASE')
    need(grant['schema']=='e02-wrapper46-external-root-release-v1' and grant['actor']=='/root' and grant['executionAuthorized'] is True and grant['scope']=='ONE_SEQUENTIAL_CAPTURE6_13_16_11_PURE_MODELS_ONLY' and grant['methodSource']==subject_pin and grant['plan']==plan_pin and grant['codeManifest']==manifest_pin and grant['outerRequest']==descriptor(HERE/'outer-request-template.json'),'EXACT_EXTERNAL_ROOT_AUTHORITY')
    need(type(grant['authors']) is list and type(grant['operators']) is list and len(grant['operators'])>0 and all(type(a) is str and a.startswith('/root') for a in [*grant['authors'],*grant['operators']]),'ACTUAL_ROOT_AUTHORS_OPERATORS')
    need(type(grant['sourceReviews']) is list and len(grant['sourceReviews'])==2,'TWO_EXTERNAL_ACTUAL_SOURCE_REVIEWS')
    for d in grant['sourceReviews']:checked(d)
    need(not OUTPUT.exists() and not OUTPUT.is_symlink(),'ONE_USE_FRESH_OUTPUT_REQUIRED')
    return plan,paths,grant,grant_pin

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

def outcome(scope,result,stdout,stderr):
    need(result['exitCode']==0 and result['reaped'] is True and result['fault'] is None and all(result['eof'].values()),'NATURAL_ZERO_REAP_FULL_CHILD_EOF_REQUIRED')
    if scope['format']=='VERBOSE_UNITTEST_NAMED':
        need(stdout==b'','PYTHON_STDOUT_EMPTY');text=stderr.decode('utf-8');lines=text.splitlines();names=[]
        for line in lines:
            m=re.fullmatch(r'(test_\w+) \(__main__\.(\w+)\.(test_\w+)\) \.\.\. ok',line)
            if m:need(m[1]==m[3],'NAMED_TEST_JOIN');names.append(m[2]+'.'+m[3])
        need(names==scope['expectedNames'],'ALL_EXACT_NAMED_PYTHON_TESTS')
        prefix=''.join(line+'\n' for line in lines[:len(names)])
        need(all(re.fullmatch(r'test_\w+ \(__main__\.\w+\.test_\w+\) \.\.\. ok',line) for line in lines[:len(names)]),'NO_UNEXPECTED_PYTHON_PREFIX')
        suffix=text[len(prefix):]
        need(re.fullmatch(r'\n-+\nRan '+str(scope['count'])+r' tests in [0-9]+\.[0-9]+s\n\nOK\n',suffix),'EXACT_VERBOSE_UNITTEST_OUTCOME')
        return dict(scope=scope['scope'],modelsExecuted=len(names),names=names,allOk=True)
    need(stderr==b'','NODE_STDERR_EMPTY');value=json.loads(stdout)
    need(set(value)==set('schema scopeVersion modelsDefined modelsExecuted models elapsedNs'.split()) and value['schema']=='e02-wrapper-origin11-actual-model-result-v1' and value['scopeVersion']==SCOPE and value['modelsDefined']==value['modelsExecuted']==11,'ACTUAL11_NODE_ROWS')
    need(type(value['elapsedNs']) is int and value['elapsedNs']>=0 and type(value['models']) is list and len(value['models'])==11,'INTEGER_ACTUAL_NODE_ELAPSED')
    need([row['name'] for row in value['models']]==scope['expectedNames'] and all(set(row)=={'name','ok','elapsedNs'} and row['ok'] is True and type(row['elapsedNs']) is int and row['elapsedNs']>=0 for row in value['models']),'ALL11_ACTUALLY_INVOKED_OUTCOMES')
    return dict(scope=scope['scope'],modelsExecuted=11,names=scope['expectedNames'],allOk=True,actualNodeResult=value)

def main():
    os.umask(0o077);plan,paths,grant,grant_pin=admission();before=[pin(p) for p in paths]
    safe(OUTPUT).mkdir(mode=0o700) # Exclusive fixed one-use output; never overwrite.
    put(OUTPUT,'admission.json',dict(plan=descriptor(HERE/'plan.json'),methodSource=descriptor(HERE/'method-source.json'),rootRelease=grant_pin,inputsBefore=before,authors=grant['authors'],operators=grant['operators'],scope='KNOWN_PROTECTED_CODE_ONLY',snapshotNotRaceFree=True))
    started=time.monotonic_ns();results=[];outcomes=[];fault=None
    try:
        for i,scope in enumerate(plan['scopes'],1):
            result,stdout,stderr=capture_scope(OUTPUT,scope,i);results.append(result)
            actual=outcome(scope,result,stdout,stderr);outcomes.append(actual)
    except BaseException as error:fault=type(error).__name__+':'+str(error)
    after=None
    try:after=[pin(p) for p in paths];need(after==before,'PROTECTED_CODE_CHANGED')
    except BaseException as error:fault=fault or type(error).__name__+':'+str(error)
    finished=time.monotonic_ns();total=sum(row['modelsExecuted'] for row in outcomes)
    summary=dict(schema='e02-wrapper-pure-model-result-v2',sourceSubject=plan['r3SourcePacket'],scopeVersion=SCOPE,modelsExecuted=total,exitCode=0 if fault is None and total==46 and after==before else 2,state='ACTUAL46_PURE_MODELS_PENDING_INDEPENDENT_DATA_REVIEW' if fault is None and total==46 else 'FAILED_OR_UNQUALIFIED_NO_RETRY',authors=grant['authors'],operators=grant['operators'],scopeCounts=[row['modelsExecuted'] for row in outcomes],modelsExecutedQualified=total,scopesAttempted=len(results),captures=results,outcomes=outcomes,fault=fault,elapsedNs=finished-started,inputsBefore=before,inputsAfter=after,inputsUnchanged=after==before,scope='KNOWN_CODE_AND_MOCKED_DECISION_PATHS_ONLY_NOT_RUNTIME_INTEROPERABILITY',rootRelease=grant_pin,outerApiOrigin='MUST_BE_RECORDED_SEPARATELY_BY_ROOT',canonicalE02Changed=False,ordinaryQualified=False,snapshotNotRaceFree=True)
    put(OUTPUT,'result.json',summary)
    print(json.dumps(dict(result=descriptor(OUTPUT/'result.json'),state=summary['state'],scopeCounts=summary['scopeCounts'],modelsExecutedQualified=total,fault=fault,inputsUnchanged=after==before,elapsedNs=summary['elapsedNs'])))
    return 0 if fault is None and total==46 and after==before else 2
if __name__=='__main__':raise SystemExit(main())
