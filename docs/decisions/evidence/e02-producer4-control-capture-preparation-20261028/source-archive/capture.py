"""SOURCE draft only; NULL final SOURCE2 bindings refuse before target imports/launch."""
import hashlib,json,os,pathlib,re,selectors,signal,stat,subprocess,sys,time
from explicit_inputs import need,closed,read_expected,metadata,decode_metadata,snapshot_files,snapshot_memberships
HERE=pathlib.Path(__file__).resolve().parent
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
# Final replacement requires a separately frozen/reviewed successor. JSON alone
# cannot turn this draft into authority, even if readiness is edited.
PINNED_PRODUCER_SOURCE=None
PINNED_SOURCE2_ACCEPTANCE=None
SCRIPTS=['test_guard_client.mjs','test_guard_transport_boundaries.mjs','test_capture_allocation.mjs','test_controller_emission.mjs','test_observation_model.mjs','test_guard_helper.py','test_capture_parent.py','test_public_identity_metadata.py','test_producer2_source.py','test_producer3_bindings.py']

def pin(p):
 p=pathlib.Path(p);s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_size<=16777216,'OWNED_SMALL_CAPTURE_OUTPUT');raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=oct(stat.S_IMODE(s.st_mode)))
def put(root,name,value):
 need(pathlib.Path(name).name==name,'FIXED_OUTPUT_NAME');raw=value if type(value) is bytes else (json.dumps(value,indent=2)+'\n').encode();need(len(raw)<=16777216,'OUTPUT_METADATA_CAP')
 fd=os.open(root/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw)


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

# Closed, file-specific proposed output contracts. Final SOURCE2 verification
# must confirm each exact definition/success loop and contract before freeze.
JS_SHAPES={
 'test_guard_client.mjs':dict(scope='PRODUCER4_MOCK_FRESH_GUARD_SCHEDULER_ONLY',keys='scope definitions executed realHelperExecuted realClockOrSDKObserved clientRowsQualified',false=['realHelperExecuted','realClockOrSDKObserved'],zero=['clientRowsQualified']),
 'test_guard_transport_boundaries.mjs':dict(scope='PRODUCER4_MOCK_GUARD_TRANSPORT_BOUNDARIES_ONLY',keys='scope definitions executed realHelperExecuted realTimerObserved processReapAttested clientRowsQualified',false=['realHelperExecuted','realTimerObserved','processReapAttested'],zero=['clientRowsQualified']),
 'test_capture_allocation.mjs':dict(scope='PRODUCER4_PURE_CAPTURE_ALLOCATION_MODELS_ONLY',keys='scope definitions executed realWritesObserved realHelperExecuted wholeConsumerQualified atomicGlobalFenceClaimed',false=['realWritesObserved','realHelperExecuted','wholeConsumerQualified','atomicGlobalFenceClaimed'],zero=[]),
 'test_controller_emission.mjs':dict(scope='ACTUAL_PRODUCTION_CONTROLLER_EMITTER_WITH_FAKE_WRITER_ONLY',keys='scope checks realHelperExecuted realStdoutWritten clientRowsQualified',false=['realHelperExecuted','realStdoutWritten'],zero=['clientRowsQualified'])}

def parse_outcome(scope,result,stdout,stderr):
    need(result['exitCode']==0 and result['reaped'] is True and result['eof']==dict(stdout=True,stderr=True) and result['fault'] is None and result['groupClosure'] is None and result['groupClosureFault'] is None,'NATURAL_EXACT_OWNED_SCOPE')
    count=scope['count'];name=scope['scope'];need(type(count) is int and count>0,'FINAL_COUNT_REQUIRED')
    if name.endswith('.py'):
        need(stdout==b'','QUIET_PYTHON_STDOUT_EMPTY')
        m=re.fullmatch(rb'([.]+)\n-{70}\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n',stderr)
        need(m and len(m[1])==int(m[2])==count,'EXACT_QUIET_NO_SKIP_UNITTEST_COUNT')
        need(type(scope['definitionNames']) is list and len(scope['definitionNames'])==count and len(set(scope['definitionNames']))==count,'EXACT_SOURCE_DEFINED_METHODS')
        return dict(scope=name,count=count,membershipMeaning='QUIET_DOTS_COUNT_WITH_FROZEN_SOURCE_METHOD_NAMES_NOT_RAW_NAME_PRINTING',sourceNames=scope['definitionNames'],allOk=True)
    need(stderr==b'' and stdout.endswith(b'\n') and stdout.count(b'\n')==1,'ONE_COMPLETE_NODE_JSON_LINE')
    value=decode_metadata(stdout)
    if name=='test_observation_model.mjs':
        closed(value,'schema ok checks cases scope');need(value['schema']=='e02-producer4-observation-model-controls-v1' and value['scope']=='SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME' and value['ok'] is True and value['checks']==count,'EXACT_OBSERVATION_MODEL_SHAPE');need(value['cases']==scope['definitionNames'] and len(value['cases'])==count,'ALL_SOURCE_NAMED_OBSERVATION_CASES')
    else:
        rule=JS_SHAPES[name];closed(value,rule['keys']);need(value['scope']==rule['scope'],'EXACT_NODE_SCOPE')
        for k in rule['false']:need(value[k] is False,'EXACT_FALSE_MODEL_LIMIT')
        for k in rule['zero']:need(type(value[k]) is int and value[k]==0,'NO_CLIENT_QUALIFICATION')
        if name=='test_controller_emission.mjs':need(value['checks']==count,'EXACT_CONTROLLER_SUCCESS_LOOP_COUNT')
        else:need(value['definitions']==value['executed']==count,'ALL_REVIEWED_DEFINITIONS_SUCCESS_LOOP')
    return dict(scope=name,count=count,membershipMeaning='FROZEN_SCRIPT_ALL_BODIES_SUCCESS_LOOP_PLUS_EXACT_STDOUT_NOT_INDEPENDENT_PER_BODY_ATTESTATION',actualNodeSummary=value,allOk=True)

def declared_selection(source,control,scopes,tools):
    need([s['scope'] for s in scopes]==SCRIPTS and len(scopes)==10,'ONLY_TEN_SELECTED_GROUPS')
    js=control['selectedJavaScriptDefinitions'];py=control['pythonDefinitions'];need([r['file'] for r in js]==SCRIPTS[:5],'EXACT_DECLARED_JS_SELECTION')
    py_by_name={r['file']:r for r in py};need(len(py_by_name)==len(py),'UNIQUE_DECLARED_PYTHON_GROUP')
    by_name={pathlib.Path(d['path']).name:d for d in source['sources']};need(len(by_name)==len(source['sources']),'UNIQUE_FINAL_SOURCE_BASENAMES')
    for i,s in enumerate(scopes):
        closed(s,'scope source argv cwd count definitionNames format');need(s['source']==by_name[s['scope']],'CURRENT_SUBJECT_TEST_MEMBER')
        declared=js[i]['expandedDefinitions'] if i<5 else py_by_name[s['scope']]['methodDefinitions'];need(type(s['count']) is int and s['count']==declared and declared>0,'DERIVE_CURRENT_COUNT_NEVER200_TRANSFER')
        expected=[tools['node']['path'],s['source']['path']] if i<5 else [tools['python']['path'],'-I','-B',s['source']['path']]
        need(s['argv']==expected,'EXACT_CURRENT_TEST_ARGV_NO_WRAPPER_ALIAS')

def admission(argv):
    # Intentionally before target metadata reads, SDK/guard enumeration, output
    # creation, selected target imports or Popen. This draft can never execute.
    need(PINNED_PRODUCER_SOURCE is not None and PINNED_SOURCE2_ACCEPTANCE is not None,'FINAL_ACCEPTED_SOURCE2_UNBOUND_DRAFT_REFUSAL')
    need(argv[:1]==['--execute-once'] and len(argv)==3 and argv[1]=='--root-ack-sha' and re.fullmatch('[0-9a-f]{64}',argv[2]),'EXACT_ONCE_ACK_SHA_ARGV')
    deadline=time.monotonic_ns()+1200000000000
    ack_path=HERE/'coordinator-acknowledgement.json';ack_row=pin(ack_path);need(ack_row['sha256']==argv[2],'EXACT_EXTERNALLY_ISSUED_ROOT_ACK')
    ack=decode_metadata(ack_path.read_bytes())
    closed(ack,'schema actor executionAuthorized source sourceAcceptance methodSource plan inputManifest outerRequest authors operators sourceReviews captureReviews noRetry')
    need(ack['schema']=='e02-producer4-control-capture-root-ack-v1' and ack['actor']=='/root' and ack['executionAuthorized'] is True and ack['noRetry'] is True,'ONE_EXTERNAL_ROOT_AUTHORITY')
    need(ack['source']==PINNED_PRODUCER_SOURCE and ack['sourceAcceptance']==PINNED_SOURCE2_ACCEPTANCE,'ACTUAL_ACCEPTED_SOURCE2_ONLY')
    plan=metadata(ack['plan'],deadline);need(plan['readiness'] is True and plan['sourceContractReady'] is True,'FROZEN_REVIEWED_FINAL_PLAN_REQUIRED')
    source=metadata(ack['source'],deadline);acceptance=metadata(ack['sourceAcceptance'],deadline);need(acceptance['subject']==ack['source'],'EXACT_SOURCE_ACCEPTANCE_SUBJECT')
    method=metadata(ack['methodSource'],deadline);need(method['source']==ack['source'] and method['plan']==ack['plan'] and method['inputManifest']==ack['inputManifest'],'EXTERNAL_METHOD_PLAN_JOIN')
    manifest=metadata(ack['inputManifest'],deadline);need(manifest['source']==ack['source'] and manifest['controlPlan']==source['controlPlan'],'CURRENT_INPUT_AUTHORITY_JOIN')
    control=metadata(source['controlPlan'],deadline);declared_selection(source,control,plan['scopes'],plan['tools'])
    need(plan['scopes'][0]['cwd']==str(pathlib.Path(ack['source']['path']).parent) and all(s['cwd']==plan['scopes'][0]['cwd'] for s in plan['scopes']),'EXACT_REVIEWED_SOURCE_WORKDIR')
    for d in method['sources']:read_expected(d,deadline)
    # Complete SOURCE2 review/actor/schema/bootstrap closure is a finalization
    # dependency, explicitly blocked below until exact actual records arrive.
    need(plan['actorAndReviewContract'] is not None and plan['closedInputContract'] is not None and plan['requestContract'] is not None,'FINAL_SOURCE2_CONCRETE_CONTRACTS_REQUIRED')
    raise ValueError('SOURCE_DRAFT_FINAL_ADMISSION_NOT_IMPLEMENTED_NO_TARGET_EXECUTION')

def main(argv):
    admission(argv)
    # Final implementation must be rendered/reviewed after actual accepted
    # SOURCE2. No partially implemented admission may reach a target launch.
    raise ValueError('NO_FINAL_RUN_IMPLEMENTATION_IN_PREPARATION')

if __name__=='__main__':main(sys.argv[1:])
