"""Complete finite capture implementation; final SOURCE4 bindings remain disabled."""
import ast,hashlib,json,os,pathlib,re,selectors,signal,stat,subprocess,sys,time
HERE=pathlib.Path(__file__).resolve().parent
# -I deliberately removes script-dir lookup. Bootstrap only reviewed peer CODE,
# never a target/source directory or environment-supplied import path.
sys.path.insert(0,str(HERE))
try:
    from explicit_inputs import read_expected,metadata,decode_metadata,snapshot_files,snapshot_memberships
    from contracts import *
    from outputs import parse_outcome
finally:sys.path.pop(0)
CODE_READY=True
CURRENT_PRODUCER_SOURCE={'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r4-source4-metadata-r1/subject.json', 'bytes': 30532, 'sha256': '34802f702c863e5cd81e865eec5de7736615ceffc683a8a9f9eb4192e857e66e'}
CURRENT_PRODUCER_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-source4-acceptance-20261028/acceptance.json', 'bytes': 1143, 'sha256': 'b1ab95f20cd608024c7b4dee011063c760d35109aa20a0dca3d1c1aa81098312'}
CLOCK_SELECTION={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-control-capture-preparation-20261028/root-clock-source-selection.json', 'bytes': 1389, 'sha256': '7d24541af6dab3cca55baf588ce4bc4daf03f31b5d2bc00f3fd76f897a6216c1'}
ACTIVE_DEADLINE=None

def pin(p):
 p=pathlib.Path(p);first=p.lstat();need(stat.S_ISREG(first.st_mode) and first.st_size<=16777216,'OWNED_REGULAR_SMALL_OUTPUT');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  raw=os.read(fd,first.st_size+1);need(len(raw)==first.st_size,'COMPLETE_OWNED_FILE')
 finally:os.close(fd)
 return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=oct(stat.S_IMODE(first.st_mode)))
def descriptor(p):return {k:v for k,v in pin(p).items() if k!='mode'}
def put(root,name,value):
 need(ACTIVE_DEADLINE is None or time.monotonic_ns()<ACTIVE_DEADLINE,'WHOLE1200_OUTPUT_DEADLINE')
 need(pathlib.Path(name).name==name,'FIXED_OUTPUT_NAME');raw=value if type(value) is bytes else (json.dumps(value,indent=2)+'\n').encode();need(len(raw)<=16777216,'OUTPUT_BOUND')
 fd=os.open(root/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:checked_write(f.write,raw);f.flush()
 need(ACTIVE_DEADLINE is None or time.monotonic_ns()<ACTIVE_DEADLINE,'WHOLE1200_OUTPUT_DEADLINE')


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
    retention=[]
    for name,raw in [('stdout',bytes(buffers['stdout'])),('stderr',bytes(buffers['stderr']))]:
        try:put(root,stem+'.'+name+'.raw',raw)
        except BaseException as error:retention.append(name+':'+repr(error))
    def retained(name):
        p=root/(stem+'.'+name+'.raw')
        try:return pin(p)
        except BaseException:return None
    if retention:custody['fault']=custody['fault'] or 'RETENTION_ERROR'
    result=dict(scope=scope['scope'],argv=scope['argv'],eof=eof,elapsedNs=finished-start,stdout=retained('stdout'),stderr=retained('stderr'),pipeEofScope='ACTUAL_OWNED_CHILD_PIPES_ONLY_NOT_OUTER_API',ownership=ownership,retentionErrors=retention,**custody)
    try:put(root,stem+'-result.json',result)
    except BaseException as error:result['retentionErrors'].append('result:'+repr(error));result['fault']=result['fault'] or 'RETENTION_ERROR'
    return result,bytes(buffers['stdout']),bytes(buffers['stderr'])

class SnapshotPool:
    def __init__(self,start,clock=time.monotonic_ns):
        self.clock=clock;self.end=start+1200000000000;self.remaining=480000000000
    def deadline(self,remaining_scopes):
        now=self.clock();reserve=remaining_scopes*63000000000+30000000000
        need(self.remaining>0 and self.end-now>reserve,'FULL_REMAINING_SNAPSHOT_AND_CHILD_BUDGET')
        return min(now+self.remaining,self.end-reserve)
    def run(self,remaining_scopes,fn):
        start=self.clock();deadline=self.deadline(remaining_scopes)
        try:return fn(deadline)
        finally:
            elapsed=self.clock()-start;self.remaining-=elapsed
            need(elapsed>=0 and self.remaining>=0 and self.clock()<=self.end,'SHARED480_GLOBAL1200_EXHAUSTED')
    def admit_child(self,remaining_scopes):
        need(remaining_scopes>=1 and self.end-self.clock()>=remaining_scopes*63000000000+self.remaining+30000000000,'NO_SHORTENED_OR_RENEWED_CHILD_CLOCK')

def load_bundle(ack,deadline):
    docs={}
    for name in ('producerSource','producerSourceAcceptance','captureSource','captureSourceAcceptance','admissionPlan','admissionData','admissionDataAcceptance','sourceBirth','actorContext','inputManifest','plan','clockSelection','requestContract','runtimeBindings'):
        docs[name]=metadata(ack[name],deadline)
    docs['control']=metadata(docs['producerSource']['controlPlan'],deadline)
    docs['configs']=[metadata(d,deadline) for d in docs['producerSource']['configurations'].values()]
    for s in docs['plan']['scopes']:
        raw=read_expected(s['source'],deadline,True)[1]
        if s['scope'].endswith('.py'):
            tree=ast.parse(raw.decode('utf8','strict'));names=[c.name+'.'+f.name for c in tree.body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')]
            need(names==s['definitionNames'] and len(names)==s['count'],'ACTUAL_FROZEN_PYTHON_AST_NAMES')
        elif s['scope']=='test_observation_model.mjs':
            names=re.findall(r"await test\('([^']+)'",raw.decode('utf8','strict'));need(names==s['definitionNames'] and len(names)==s['count'] and len(set(names))==len(names),'FROZEN_OBSERVATION_SOURCE_NAMES')
    proofs=[]
    for proof in docs['actorContext']['participantProofs']:
        closed(proof,'actor authority selector');value=metadata(proof['authority'],deadline)
        need(type(proof['selector']) is str and proof['selector'].startswith('/'),'EXPLICIT_ACTOR_POINTER')
        for token in proof['selector'][1:].split('/'):
            key=token.replace('~1','/').replace('~0','~');value=value[int(key)] if type(value) is list else value[key]
        need(value==proof['actor'] and proof['actor'] in docs['actorContext']['participants'],'ACTUAL_KNOWN_ACTOR_FIELD_PROOF');proofs.append(proof['actor'])
    need(set(proofs)==set(docs['actorContext']['participants']),'COMPLETE_CONTEXT_ACTOR_PROOFS')
    records={'producerAcceptance':docs['producerSourceAcceptance'],'captureAcceptance':docs['captureSourceAcceptance'],'admissionAcceptance':docs['admissionDataAcceptance'],'admissionSubject':docs['admissionData']}
    for key in ('producerReviews','captureReviews','admissionReviews'):records[key]=[metadata(d,deadline) for d in ack[key]]
    return docs,records

def validate_bundle(ack,docs,records,ack_sha):
    need(ack['producerSource']==CURRENT_PRODUCER_SOURCE and ack['producerSourceAcceptance']==CURRENT_PRODUCER_ACCEPTANCE and ack['clockSelection']==CLOCK_SELECTION,'FINAL_PINNED_SOURCE4_ACCEPTANCE_CLOCK_ONLY')
    state=docs['runtimeBindings'];closed(state,'schema readiness producerSource producerAcceptance captureSourceAcceptance admissionDataAcceptance rootAcknowledgement');need(state['schema']=='e02-producer4-capture-runtime-bindings-v1' and state['readiness'] is True and state['producerSource']==ack['producerSource'] and state['producerAcceptance']==ack['producerSourceAcceptance'] and state['captureSourceAcceptance']==ack['captureSourceAcceptance'] and state['admissionDataAcceptance']==ack['admissionDataAcceptance'],'ALL_GENUINE_RUNTIME_BINDINGS')
    # The binding leaf never contains its own ACK hash: that would cycle.
    need(state['rootAcknowledgement']=='EXTERNALLY_SHA_BOUND_AT_LAUNCH','ACYCLIC_EXTERNAL_ACK_BINDING')
    source,method,plan,manifest=docs['producerSource'],docs['captureSource'],docs['plan'],docs['inputManifest']
    values,union=validate_acceptances(ack,source,docs['control'],method,docs['admissionPlan'],records,docs['actorContext'])
    validate_plan(plan,ack,source,docs['control'],method,manifest,docs['clockSelection'])
    need(docs['requestContract']==request_template(plan,str(HERE)),'EXACT_ACYCLIC_FIVE_KEY_REQUEST_TEMPLATE')
    birth=docs['sourceBirth'];need(birth['schema']=='e02-root-producer4-source4-acceptance-lineage-v1' and birth['actor']=='/root' and birth['acceptance']==ack['producerSourceAcceptance'],'ROOT_PINNED_SOURCE_BIRTH_LINEAGE')
    need(manifest['requiredCoverage']==plan['requiredCoverage'],'EXACT_CLOSED_COVERAGE_GROUPS')
    index={x['pin']['path']:x for x in manifest['files']}
    for key,group in manifest['requiredCoverage'].items():
        need(type(group) is list and group,'NONEMPTY_REQUIRED_INPUT_CATEGORY')
        for d in group:need(index.get(d['path'],{}).get('pin')==d,'REQUIRED_CATEGORY_TARGET_IS_PROTECTED')
    for cfg in docs['configs']:need(cfg['sourceAndDependencyPins']==source['runtimeSources'] and cfg['originalLeaseSeconds']==1800,'BOTH_EXACT22_CURRENT_SOURCE_CONFIGS')
    need(len(method['sources'])==len({d['path'] for d in method['sources']}) and descriptor(HERE/'capture.py') in method['sources'],'SELF_CODE_MEMBER')
    need(method['excludedMutableMetadata']==['execution-plan','reviews','acceptances','root-ack','runtime-output'],'CODE_ONLY_NO_HASH_CYCLE')
    return values,union

def expected_authorities(ack,docs):
    # These externally pinned leaves are deliberately outside the static CODE
    # manifest where including own method/plan/ACK would form a hash cycle.
    values=[ack[k] for k in ('producerSource','producerSourceAcceptance','captureSource','captureSourceAcceptance','admissionPlan','admissionData','admissionDataAcceptance','sourceBirth','actorContext','inputManifest','plan','clockSelection','requestContract','runtimeBindings')]
    for key in ('producerReviews','captureReviews','admissionReviews'):values.extend(ack[key])
    values.append(descriptor(HERE/'coordinator-acknowledgement.json'))
    for proof in docs['actorContext']['participantProofs']:values.append(proof['authority'])
    for key in ('execution','originalToolOrigin','rawArtifactManifest','inputsBefore','inputsAfter'):values.append(docs['admissionData'][key])
    seen={}
    for d in values:
        if d['path'] in seen:need(seen[d['path']]==d,'NO_AUTHORITY_PATH_SUBSTITUTION')
        seen[d['path']]=d
    return [seen[k] for k in sorted(seen)]

def snapshot(manifest,authorities,deadline):
    rows=snapshot_files(manifest,deadline);memberships=snapshot_memberships(manifest,deadline)
    indexed={r['pin']['path']:r for r in rows}
    for d in authorities:
        row,_=read_expected(d,deadline)
        if d['path'] in indexed:need(indexed[d['path']]==row,'AUTHORITY_EXPECTED_ROW_JOIN')
        else:indexed[d['path']]=row
    need(len(indexed)<=20000,'TOTAL_HOST_FILES_INCLUDING_EXTERNAL_AUTHORITIES')
    return dict(rows=[indexed[k] for k in sorted(indexed)],memberships=memberships,snapshotNotRaceFree=True)

def execute(ack,ack_pin,docs,values,pool,before):
    plan=docs['plan'];root=pathlib.Path(plan['outputRoot']);need(not root.exists() and not root.is_symlink(),'FRESH_ONE_USE_OUTPUT')
    root.mkdir(mode=0o700);put(root,'overall-before.json',before)
    scopes=[];outcomes=[];first=None;after=None;authorities=expected_authorities(ack,docs)
    try:
        for i,s in enumerate(plan['scopes'],1):
            current=pool.run(11-i,lambda d:snapshot(docs['inputManifest'],authorities,d));need(current==before,'EVERY_EXPECTED_INPUT_BEFORE_EACH_SCOPE');put(root,'%02d-before.json'%i,current)
            pool.admit_child(11-i);row,stdout,stderr=capture_scope(root,s,i);scopes.append(row)
            current=pool.run(10-i,lambda d:snapshot(docs['inputManifest'],authorities,d));put(root,'%02d-after.json'%i,current);need(current==before,'EVERY_EXPECTED_INPUT_AFTER_EACH_SCOPE')
            outcomes.append(parse_outcome(s,row,stdout,stderr))
        after=pool.run(0,lambda d:snapshot(docs['inputManifest'],authorities,d));put(root,'overall-after.json',after);need(after==before,'OVERALL_EXPECTED_CUSTODY')
    except BaseException as error:first=repr(error)
    result=dict(schema='e02-producer4-current-control-execution-v1',authors=docs['captureSource']['authors'],operators=ack['operators'],producerSource=ack['producerSource'],captureSource=ack['captureSource'],rootAcknowledgement=ack_pin,plan=ack['plan'],inputManifest=ack['inputManifest'],countsSeparate=values,scopes=scopes,outcomes=outcomes,remainingNotExecuted=[s['scope'] for s in plan['scopes'][len(scopes):]],firstFault=first,sourceUnchanged=after==before if after is not None else False,overallBefore=descriptor(root/'overall-before.json'),overallAfter=descriptor(root/'overall-after.json') if (root/'overall-after.json').exists() else None,elapsedNs=pool.clock()-(pool.end-1200000000000),exitCode=0 if first is None and len(outcomes)==10 else 2,outerApiOrigin='ACTUAL_ROOT_RESPONSES_MUST_BE_RETAINED_EXTERNALLY_NOT_INNER_PID_REAP_OR_EOF',ordinaryRowsQualified=0,canonicalE02='PARTIAL22_UNCHANGED')
    put(root,'result.json',result)
    # File list is exact flat owned proof output, never a recursive source DAG.
    files=[]
    for p in sorted(root.iterdir()):need(p.is_file() and not p.is_symlink(),'ONLY_OWNED_FLAT_REGULAR_OUTPUT');files.append(descriptor(p))
    put(root,'raw-artifact-manifest.json',dict(schema='e02-producer4-control-raw-artifact-manifest-v1',files=files,originalToolOrigin=None,outerApiMeaning='External complete genuine launch/allpolls will be added by separately called assembler.'))
    print(json.dumps(dict(result=descriptor(root/'result.json'),rawManifest=descriptor(root/'raw-artifact-manifest.json'),exitCode=result['exitCode'])))
    return result['exitCode']

def require_runtime_ready():
    # All preparation versions fail BEFORE any target metadata/SDK walk/output
    # or Popen. Final CODE binding/render/review is a separately authorized step.
    need(CODE_READY is True and CURRENT_PRODUCER_SOURCE is not None and CURRENT_PRODUCER_ACCEPTANCE is not None and CLOCK_SELECTION is not None,'NULL_FINAL_SOURCE4_BINDINGS_REFUSE_BEFORE_TARGET_READS')
    local=HERE/'runtime-bindings.json';need(local.is_file() and not local.is_symlink() and local.stat().st_size<=16777216,'OWN_SMALL_BINDING_METADATA');state=decode_metadata(local.read_bytes());need(state['readiness'] is True and state['captureSourceAcceptance'] is not None and state['admissionDataAcceptance'] is not None,'NULL_CAPTURE_ACCEPTANCE_DATA_GRANT_REFUSE_BEFORE_TARGET_READS')
    return local

def main(argv):
    global ACTIVE_DEADLINE
    local=require_runtime_ready()
    need(sys.flags.isolated and sys.dont_write_bytecode and argv[:2]==['--execute-once','--root-ack-sha'] and len(argv)==3 and re.fullmatch('[0-9a-f]{64}',argv[2]),'EXACT_ISOLATED_ONCE_INVOCATION')
    start=time.monotonic_ns();pool=SnapshotPool(start);ACTIVE_DEADLINE=pool.end
    ap=descriptor(HERE/'coordinator-acknowledgement.json');need(ap['sha256']==argv[2] and stat.S_IMODE((HERE/'coordinator-acknowledgement.json').stat().st_mode)==0o600,'ACTUAL_EXTERNAL_ROOT_ACK_SHA_MODE')
    ack=metadata(ap,pool.deadline(10));docs,records=pool.run(10,lambda d:load_bundle(ack,d));values,_=validate_bundle(ack,docs,records,argv[2]);authorities=expected_authorities(ack,docs)
    need(ack['runtimeBindings']==descriptor(local),'ROOT_ACK_PINS_ACTUAL_RUNTIME_BINDINGS')
    out=pathlib.Path(docs['plan']['outputRoot']);need(not out.exists() and not out.is_symlink(),'NO_OUTPUT_OVERWRITE_OR_RETRY')
    for item in docs['inputManifest']['files']:need(not pathlib.Path(item['pin']['path']).is_relative_to(out),'NO_OUTPUT_AS_PROTECTED_INPUT')
    before=pool.run(10,lambda d:snapshot(docs['inputManifest'],authorities,d));return execute(ack,ap,docs,values,pool,before)

if __name__=='__main__':sys.exit(main(sys.argv[1:]))
