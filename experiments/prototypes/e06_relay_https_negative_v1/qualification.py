"""SOURCE ONLY: separately released two-job local F-only qualification.

No import performs work. No target runtime gate is bypassed by this distinct
local entry. Native work, controls and this driver have NOT been executed.
Expected replies stay in this outer checker; the JS helper reads worker data only.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import time

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE=ROOT/'experiments/prototypes/e06_relay_https_negative_v1'
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
     'WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'}
PYTHON={'path':'/home/peterhorvath/.miniforge3/bin/python3.13','bytes':32959480,
        'sha256':'5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
# Fixed source pin supplied after the independent admission author stopped writes.
# Later independent source approval covers this SAME complete derivative closure.
ADMISSION={'path':str(HERE/'admission.py'),'bytes':53263,
           'sha256':'24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'}
A=None
R=None


def standalone_descriptor(file):
    p=Path(file)
    if not p.is_absolute() or str(p.resolve(strict=True))!=str(p) or p.is_symlink() or not p.is_file():
        raise ValueError('FIXED_CANONICAL_SOURCE')
    digest=hashlib.sha256();size=0
    with p.open('rb') as handle:
        before=os.fstat(handle.fileno())
        while block:=handle.read(1048576):size+=len(block);digest.update(block)
        after=os.fstat(handle.fileno())
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns) or size!=before.st_size:
        raise ValueError('SOURCE_CHANGED_WHILE_HASHING')
    return {'path':str(p),'bytes':size,'sha256':digest.hexdigest()}


def bootstrap():
    """Fixed trusted source first; no caller-selected Python module or CLI."""
    global A
    if dict(os.environ)!=ENV:raise ValueError('EXACT_OUTER_ENVIRONMENT')
    if Path(sys.executable).resolve(strict=True)!=Path(PYTHON['path']) or standalone_descriptor(PYTHON['path'])!=PYTHON:
        raise ValueError('FIXED_OUTER_INTERPRETER')
    if standalone_descriptor(ADMISSION['path'])!=ADMISSION:raise ValueError('FIXED_ADMISSION_PIN')
    spec=importlib.util.spec_from_file_location('_n02316_fixed_qualification_admission',ADMISSION['path'])
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);A=module
    return A


def load_runner(ctx):
    """Only the fixed same-derivative runner after full source admission."""
    global R
    A.need(callable(ctx['recheckAuthorityEvidence']),'ADMITTED_AUTHORITY_RECHECK')
    ctx['recheckAuthorityEvidence']()
    matches=[d for d in ctx['sourceClosure'] if d['path']==str(HERE/'runner.py')]
    A.need(len(matches)==1 and A.equal(A.descriptor(HERE/'runner.py'),matches[0]),'CURRENT_FIXED_RUNNER_PIN')
    spec=importlib.util.spec_from_file_location('_n02316_fixed_qualification_runner',HERE/'runner.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.init_owned_case_io(A);R=module;ctx['recheckAuthorityEvidence']();return module


def owned_native_type(runner):
    """Add one-request stdin discipline without changing protected OwnedCase.

    The base keeps actual Popen/WNOWAIT ownership, no post-reap signal path,
    bounded independent cleanup and source-owned observation limitations.
    This narrow subclass changes only RPC driving and honest stdin capture.
    """
    class OwnedNativeCapture(runner.OwnedCase):
        def __init__(self,argv,directory,env,deadline,current,request,meta,definitions):
            super().__init__(argv,directory,env,deadline,current,phase_progress=None)
            self.request=request;self.written=0;self.request_descriptor=None
            self.times={k:None for k in ('launchStartedNs','acquiredNs','requestStartedNs','requestCompletedNs',
                                         'replyCompletedNs','stdinClosedNs','exitObservedNs','terminalCompletedNs')}
            self.input_complete=False;self.meta=meta;self.definitions=definitions;self.evidence=[]
            self.phase_receipts={k:None for k in ('launch','response','terminal')}
        def timing(self):
            start=self.times['launchStartedNs'];response=self.times['replyCompletedNs'];end=self.times['terminalCompletedNs']
            return {'startedMonotonicMs':None if start is None else start//1000000,
                    'responseMonotonicMs':None if response is None else response//1000000,
                    'terminalMonotonicMs':None if end is None else end//1000000,
                    'elapsedMilliseconds':None if start is None or end is None else (end-start)//1000000}
        def emit_phase(self,phase):
            streams={}
            for name,raw in [('stdin',self.request[:self.written]),*[(k,bytes(v)) for k,v in self.out.items()]]:
                streams[name]=runner.put_bytes(self.directory/(phase+'.'+name+'.bin'),raw);self.evidence.append(streams[name])
            value={'schema':'n02316-local-native-spawn-v1',**self.meta,'phase':phase,'argv':self.argv,
                   'cwd':str(self.directory),'environment':self.env,'streams':streams,
                   'lifecycle':dict(self.life),'timing':self.timing()}
            A.validate(value,'@localSpawnReceipt',self.definitions)
            self.phase_receipts[phase]=runner.put_json(self.directory/(phase+'-receipt.json'),value);self.evidence.append(self.phase_receipts[phase])
        def capture(self):
            # Preserve actual written prefix on failure, never a planned zero.
            for name,raw in [('stdin',self.request[:self.written]),*[(k,bytes(v)) for k,v in self.out.items()]]:
                ok,d=self.attempt('capture:raw:'+name,lambda name=name,raw=raw:runner.put_bytes(self.directory/(name+'.bin'),raw))
                if ok:self.streams[name]=d;self.evidence.append(d)
            self.capture_complete=all(self.streams.values()) and self.request_descriptor is not None
            if (self.secondary or self.secondary_overflow or not self.capture_complete) and self.life['error'] is None:
                self.life['error']=runner.error_fact(ValueError('LOCAL_CLEANUP_OR_CAPTURE_UNQUALIFIED'))
            self.record={'schema':'n02316-python-owned-local-native-v1','argv':self.argv,'cwd':str(self.directory),'environment':self.env,
                         'lifecycle':dict(self.life),'ownership':self.ownership,'primaryError':self.primary,
                         'secondaryErrors':list(self.secondary),'secondaryOverflow':self.secondary_overflow,
                         'captureComplete':self.capture_complete,'streams':dict(self.streams),
                         'request':self.request_descriptor,'inputComplete':self.input_complete,'writtenBytes':self.written,
                         'observedBytes':dict(self.total),'retainedBytes':{k:len(v) for k,v in self.out.items()},
                         'timing':dict(self.times),'phaseMonitor':self.phase}
            ok,d=self.attempt('capture:receipt',lambda:runner.put_json(self.directory/'receipt.json',self.record))
            if ok:self.receipt=d;self.evidence.append(d)
            else:
                self.capture_complete=False
                if self.life['error'] is None:self.life['error']=runner.error_fact(ValueError('LOCAL_RECEIPT_CAPTURE_UNQUALIFIED'))
                fallback=(json.dumps({'schema':'n02316-local-capture-failure-v1','primary':self.primary,
                                     'ownership':self.ownership,'secondary':self.secondary,'overflow':self.secondary_overflow,
                                     'qualified':False})+'\n').encode()
                self.attempt('capture:bounded-stderr-fallback',lambda:os.write(2,fallback[:8192]))
            self.attempt('capture:terminal-phase',lambda:self.emit_phase('terminal'))
        def run(self):
            try:
                A.need(type(self.request) is bytes and 0<len(self.request)<=131072 and self.request.endswith(b'\n')
                       and self.request.count(b'\n')==1,'EXACT_ONE_REQUEST_JSONL')
                self.request_descriptor=runner.put_bytes(self.directory/'request.jsonl',self.request);self.evidence.append(self.request_descriptor)
                self.current();self.times['launchStartedNs']=time.monotonic_ns()
                self.life.update(launchAttempt=True,acquisition='UNKNOWN')
                self.process=subprocess.Popen(self.argv,cwd=self.directory,env=self.env,stdin=subprocess.PIPE,
                                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,bufsize=0)
                self.ownership='HELD';self.life.update(acquisition='ACQUIRED',pid=self.process.pid)
                self.times['acquiredNs']=time.monotonic_ns()
                if self.times['acquiredNs']-self.times['launchStartedNs']>=15000000000:
                    self.life['timedOut']=True;raise TimeoutError('NATIVE_START_DEADLINE')
                self.selector=selectors.DefaultSelector()
                for name in self.out:
                    pipe=getattr(self.process,name);os.set_blocking(pipe.fileno(),False);self.selector.register(pipe,selectors.EVENT_READ,name)
                os.set_blocking(self.process.stdin.fileno(),False)
                self.selector.register(self.process.stdin,selectors.EVENT_WRITE,'stdin-write')
                self.emit_phase('launch')
                self.times['requestStartedNs']=time.monotonic_ns()
                reply_deadline=min(self.deadline,self.times['requestStartedNs']/1e9+15)
                terminal_deadline=None
                while True:
                    self.watch_phases();observation=self.observe_owned();now=time.monotonic()
                    if observation=='EXITED' and self.times['exitObservedNs'] is None:self.times['exitObservedNs']=time.monotonic_ns()
                    if self.times['exitObservedNs'] is not None and not self.all_eof() and time.monotonic_ns()-self.times['exitObservedNs']>=2000000000:
                        self.life['timedOut']=True;raise TimeoutError('NATIVE_PIPE_DRAIN_DEADLINE')
                    if terminal_deadline is None:
                        if now>=reply_deadline:self.life['timedOut']=True;raise TimeoutError('NATIVE_COMBINED_WRITE_REPLY_DEADLINE')
                    elif now>=terminal_deadline:
                        self.life['timedOut']=True;raise TimeoutError('NATIVE_TERMINAL_DEADLINE')
                    if observation=='EXITED' and self.all_eof():
                        A.need(self.times['replyCompletedNs'] is not None and self.input_complete,'EARLY_NATIVE_EXIT')
                        break
                    for key,_ in self.selector.select(0.05):
                        if key.data=='stdin-write':
                            try:count=os.write(self.process.stdin.fileno(),self.request[self.written:])
                            except BlockingIOError:continue
                            A.need(count>0,'NATIVE_STDIN_WRITE');self.written+=count
                            if self.written==len(self.request):
                                self.selector.unregister(self.process.stdin);self.input_complete=True
                                self.times['requestCompletedNs']=time.monotonic_ns()
                        else:
                            self.read_key(key)
                            A.need(key.data!='stdout' or not self.out['stdout'] or self.input_complete,'REPLY_BEFORE_REQUEST_FLUSH')
                    stdout=bytes(self.out['stdout'])
                    if b'\n' in stdout:
                        A.need(self.input_complete,'REPLY_BEFORE_REQUEST_FLUSH')
                        A.need(stdout.count(b'\n')==1 and stdout.endswith(b'\n'),'EXTRA_OR_PENDING_NATIVE_REPLY')
                        if self.times['replyCompletedNs'] is None:
                            self.times['replyCompletedNs']=time.monotonic_ns()
                            if self.times['replyCompletedNs']/1e9>=reply_deadline:
                                self.life['timedOut']=True;raise TimeoutError('NATIVE_COMBINED_WRITE_REPLY_DEADLINE')
                            self.emit_phase('response')
                            # Owner observes a sole complete reply while stdin remains open.
                            # Close exactly once; native must then terminate naturally within5s.
                            self.current();self.watch_phases();A.need(self.observe_owned()=='RUNNING','NATIVE_NOT_OWNED_QUIESCENT')
                            self.close_pipe('stdin');self.times['stdinClosedNs']=time.monotonic_ns()
                            terminal_deadline=min(self.deadline,self.times['stdinClosedNs']/1e9+5)
                    A.need(not self.out['stderr'],'NATIVE_STDERR_NOT_EMPTY')
                A.need(self.reap_exited(),'NATIVE_OWNED_REAP')
                self.times['terminalCompletedNs']=time.monotonic_ns()
                if terminal_deadline is None or self.times['terminalCompletedNs']/1e9>=terminal_deadline:
                    self.life['timedOut']=True;raise TimeoutError('NATIVE_TERMINAL_DEADLINE')
                self.current()
            except BaseException as exc:
                if isinstance(exc,TimeoutError):self.life['timedOut']=True
                self.primary_error(exc)
            finally:
                self.attempt('cleanup:outer-guard',self.cleanup)
                ok,_=self.attempt('capture:outer-guard',self.capture)
                if not ok:
                    self.capture_complete=False
                    if self.life['error'] is None:self.life['error']=runner.error_fact(ValueError('LOCAL_CAPTURE_UNQUALIFIED'))
                    self.attempt('capture:last-bounded-diagnostic',lambda:os.write(2,b'N02316_LOCAL_CAPTURE_UNQUALIFIED\n'))
            return bytes(self.out['stdout'])
    return OwnedNativeCapture


def first_difference(a,b,pointer=''):
    """Typed whole object comparison; no selected-field success projection."""
    if type(a) is not type(b):return pointer or '/'
    if type(a) is dict:
        if set(a)!=set(b):return (pointer or '')+'/<keys>'
        for key in sorted(a):
            diff=first_difference(a[key],b[key],pointer+'/'+key.replace('~','~0').replace('/','~1'))
            if diff is not None:return diff
    elif type(a) is list:
        if len(a)!=len(b):return (pointer or '')+'/<length>'
        for i,(x,y) in enumerate(zip(a,b)):
            diff=first_difference(x,y,pointer+'/'+str(i))
            if diff is not None:return diff
    elif a!=b:return pointer or '/'
    return None


def run_local(ctx):
    A.need(A is not None and ctx['mode']=='LOCAL_F_ONLY','FIXED_ADMITTED_LOCAL_CONTEXT')
    runner=load_runner(ctx);Capture=owned_native_type(runner)
    cfg=ctx['config'];wc=ctx['workerConfig'];defs=ctx['definitions']
    for name in ('localCapture','localJobCapture','localComparison','localSpawnReceipt','localJSBinding'):
        A.need(name in defs,'COMPLETE_LOCAL_CAPTURE_SCHEMA')
    started=time.monotonic_ns();phase_deadline=started/1e9+1500
    root=Path(ctx['output']);A.need(str(root)==wc['outputRoot'],'ADMITTED_OUTPUT_ROOT')
    source=[dict(d) for d in ctx['sourceClosure']]
    request=A.checked(wc['request'])
    A.need(len(request)<=131072 and request.endswith(b'\n') and request.count(b'\n')==1,'ONE_MATERIALIZED_REQUEST_JSONL')
    candidate=A.document(cfg['candidate'])
    A.need(A.equal(A.loads(request[:-1]),candidate['N02']['requestCandidate']),'ENTIRE_SOURCE_CANDIDATE_REQUEST')
    expected={}
    for backend in ('JS','RUST'):
        expected[backend]=A.document(cfg['expectedReplies'][backend])
        A.need(A.equal(expected[backend],candidate['N02']['expectedByBackend'][backend])
               and type(expected[backend]) is dict and len(expected[backend])==13,'FULL_THIRTEEN_KEY_BACKEND_EXPECTED')
    no_effects={k:0 for k in ('relayJobs','httpsListeners','acquisitionConnections','httpGets','consumerCalls',
                              'browserLaunches','attachmentEncryptions','receipts','businessEffects')}
    counters=('metadataRequests','metadataReplies','dValidations','fValidations')
    total={k:0 for k in counters};jobs=[];not_executed=[];run_error=None;secondary=[]
    run_integrity={'sourceCurrent':None,'inputsCurrent':None,'evidenceComplete':None}
    all_clean=True;all_job_evidence=True;overall='MATCHED';scheduled=set();original_outputs=[];owner=None;clean=None
    def current():
        if time.monotonic()>=phase_deadline:raise TimeoutError('LOCAL_ORIGINAL_PHASE_DEADLINE')
        for d in source:A.need(A.equal(A.descriptor(d['path']),d),'LOCAL_ORIGINAL_SOURCE_DRIFT')
        ctx['recheckAuthorityEvidence']()
        A.need(A.equal(A.checked(wc['request']),request),'LOCAL_ORIGINAL_REQUEST_DRIFT')
        for backend in ('JS','RUST'):
            A.need(A.equal(A.document(cfg['expectedReplies'][backend]),expected[backend]),'LOCAL_ORIGINAL_EXPECTED_DRIFT')
        if time.monotonic()>=phase_deadline:raise TimeoutError('LOCAL_ORIGINAL_PHASE_DEADLINE')
    def save(file,value,shape):
        A.validate(value,'@'+shape,defs);return runner.put_json(file,value)
    def fact(exc):return runner.error_fact(exc)
    def collect_artifacts():
        rows=[]
        for file in sorted(root.rglob('*')):
            st=file.lstat()
            A.need(st.st_uid==os.getuid() and not file.is_symlink() and str(file.resolve(strict=True))==str(file),'OWNED_LOCAL_ARTIFACT')
            if stat.S_ISDIR(st.st_mode):
                A.need(file.parent==root and file.name in ('Q-JS','Q-RUST') and stat.S_IMODE(st.st_mode)==0o700,'CLOSED_LOCAL_JOB_DIRECTORY');continue
            A.need(stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and len(rows)<2048,'BOUNDED_OWNED_LOCAL_ARTIFACT')
            rows.append(A.descriptor(file))
        return rows
    current();A.need(not root.exists(),'FRESH_LOCAL_OUTPUT_ROOT');root.mkdir(mode=0o700)
    A.private_dir(root)
    try:
        for index,plan in enumerate(wc['jobs']):
            if overall!='MATCHED':
                not_executed.append({'jobId':plan['jobId'],'status':'NOT_EXECUTED','reason':'EARLIER_FAILURE'});continue
            directory=Path(plan['output']);backend=plan['backend'];job_id=plan['jobId'];scheduled.add(job_id)
            A.need(job_id==('Q-JS','Q-RUST')[index] and backend==('JS','RUST')[index]
                   and directory==root/job_id,'EXACT_TWO_SEQUENTIAL_FRESH_JOBS')
            binding_desc=None;owner=None;reply_desc=None;sidecar_desc=None;comparison_desc=None
            job_error=None;job_secondary=[];status='UNQUALIFIED';comparison_status='NOT_EXECUTED'
            counts={k:0 for k in counters};integrity={'sourceCurrent':None,'inputsCurrent':None,'evidenceComplete':None}
            clean=None;request_equal=None;reply_equal=None;difference=None;comparison_error=None
            try:
                current();A.need(time.monotonic()<phase_deadline,'NO_LATE_LOCAL_JOB')
                directory.mkdir(mode=0o700);A.private_dir(directory)
                if backend=='JS':
                    binding={'schema':'n02316-local-js-binding-v1','jobId':job_id,'backend':backend,
                             'workerConfig':ctx['workerConfigDescriptor'],'config':ctx['configDescriptor'],
                             'release':ctx['releaseDescriptor'],'sourceApproval':cfg['sourceApproval'],
                             'configurationAcceptance':cfg['configurationAcceptance'],'request':wc['request'],
                             'scope':wc['scope'],'fFixture':wc['fFixture'],'metadataEntry':wc['tools']['jsMetadata'],
                             'closure':source,'output':str(directory),'maxRequests':1}
                    binding_desc=save(directory/'binding.json',binding,'localJSBinding');original_outputs.append(binding_desc)
                    argv=[wc['tools']['node']['path'],str(HERE/'metadata_loader.mjs'),binding_desc['path'],binding_desc['sha256']]
                    tool=wc['tools']['node']
                else:argv=[wc['tools']['nativeRust']['path']];tool=wc['tools']['nativeRust']
                meta={'runId':cfg['runId'],'runRole':cfg['runRole'],'executionSession':cfg['executionSession'],
                      'jobId':job_id,'backend':backend,'tool':tool}
                current();owner=Capture(argv,directory,ENV,min(phase_deadline,time.monotonic()+240),current,request,meta,defs)
                stdout=owner.run();original_outputs.extend(owner.evidence)
                # The complete actual reply remains evidence before any whole comparison.
                # JS failure-sidecar may retain a reply which its successful channel refused.
                sidecar_path=directory/'native-reply.jsonl'
                if backend=='JS' and sidecar_path.exists():
                    A.need(not sidecar_path.is_symlink() and stat.S_IMODE(sidecar_path.lstat().st_mode)==0o600,'OWNED_NATIVE_SIDECAR')
                    sidecar_desc=A.descriptor(sidecar_path);original_outputs.append(sidecar_desc)
                raw=stdout
                if sidecar_desc is not None:
                    sidecar=A.checked(sidecar_desc)
                    if not raw:raw=sidecar
                reply_desc=owner.streams['stdout'] if stdout else sidecar_desc
                request_equal=owner.input_complete and owner.written==len(request)
                if owner.streams['stdin'] is not None:
                    request_equal=request_equal and A.checked(owner.streams['stdin'])==request
                else:request_equal=None
                counts['metadataRequests']=1 if owner.input_complete else (0 if not owner.life['launchAttempt'] else None)
                counts['metadataReplies']=None;counts['dValidations']=None;counts['fValidations']=None
                if not owner.life['launchAttempt']:counts={k:0 for k in counters}
                decoded=None
                try:
                    A.need(raw.endswith(b'\n') and raw.count(b'\n')==1 and len(raw)<=16777216,'ONE_COMPLETE_NATIVE_REPLY')
                    decoded=A.loads(raw[:-1]);counts['metadataReplies']=1
                    observed=decoded.get('validationCallCounts') if type(decoded) is dict else None
                    if type(observed) is dict and set(observed)=={'D','F'}:
                        for key,field in (('D','dValidations'),('F','fValidations')):
                            if type(observed[key]) is int and observed[key] in (0,1):counts[field]=observed[key]
                    difference=first_difference(decoded,expected[backend]);reply_equal=difference is None
                    comparison_status='MATCHED' if request_equal is True and reply_equal else 'FAIL'
                    if request_equal is not True:difference='/request'
                except BaseException as exc:comparison_error=fact(exc);comparison_status='UNQUALIFIED'
                comparison={'schema':'n02316-local-whole-comparison-v1','runId':cfg['runId'],'jobId':job_id,'backend':backend,
                            'candidate':cfg['candidate'],'sourceApproval':cfg['sourceApproval'],'request':owner.request_descriptor or wc['request'],
                            'expectedRequest':wc['request'],'reply':reply_desc,'expectedReply':cfg['expectedReplies'][backend],
                            'requestByteEqual':request_equal,'replyWholeEqual':reply_equal,'firstDifference':difference,
                            'status':comparison_status,'error':comparison_error}
                comparison_desc=save(directory/'comparison.json',comparison,'localComparison');original_outputs.append(comparison_desc)
                # Lifecycle qualification is separate from value equality; no compilation or
                # expected JSON can substitute for natural process/raw evidence.
                A.natural(owner.life)
                A.need(owner.capture_complete and owner.receipt is not None and owner.secondary==[] and not owner.secondary_overflow
                       and all(owner.phase_receipts.values()) and owner.out['stderr']==b'','COMPLETE_OWNED_LOCAL_CAPTURE')
                if backend=='JS':A.need(sidecar_desc is not None and A.checked(sidecar_desc)==stdout,'JS_SUCCESS_SIDECAR_STDOUT_EQUAL')
                if comparison_status=='MATCHED':
                    A.need(counts=={'metadataRequests':1,'metadataReplies':1,'dValidations':0,'fValidations':1},'MEASURED_EXACT_F_ONLY_COUNTS')
                current();integrity={'sourceCurrent':True,'inputsCurrent':True,'evidenceComplete':True};clean=True
                status=comparison_status
                if status!='MATCHED':job_error=comparison_error or fact(ValueError('ACTUAL_WHOLE_NATIVE_MISMATCH'))
            except BaseException as exc:
                job_error=owner.primary if owner is not None and owner.primary is not None else fact(exc)
                if owner is not None:
                    clean=(owner.life['acquisition']=='ACQUIRED' and owner.life['reaped'] is True
                           and owner.life['stdoutEOF'] is True and owner.life['stderrEOF'] is True
                           and owner.life['forced'] is False and owner.life['timedOut'] is False
                           and owner.secondary==[] and not owner.secondary_overflow and owner.capture_complete)
                    for row in owner.secondary:job_secondary.append(row['error'])
                else:clean=True  # No child acquisition was attempted by this scoped job.
                status='UNQUALIFIED'
                try:current();integrity.update(sourceCurrent=True,inputsCurrent=True)
                except BaseException as drift:
                    integrity.update(sourceCurrent=None,inputsCurrent=None);job_secondary.append(fact(drift))
                integrity['evidenceComplete']=False
                if owner is not None and owner.life['launchAttempt'] and not owner.input_complete:
                    counts={k:None for k in counters}
            if status=='NOT_EXECUTED':status='UNQUALIFIED'
            cleanup_problems=list(job_secondary)
            if clean is not True and job_error is not None:cleanup_problems.append(job_error)
            row={'schema':'n02316-local-job-capture-v1','runId':cfg['runId'],'runRole':cfg['runRole'],
                 'executionSession':cfg['executionSession'],'jobId':job_id,'backend':backend,
                 'candidate':cfg['candidate'],'sourceApproval':cfg['sourceApproval'],'config':ctx['configDescriptor'],
                 'workerConfig':ctx['workerConfigDescriptor'],'release':ctx['releaseDescriptor'],'binding':binding_desc,
                 'request':wc['request'],'reply':reply_desc,'sidecar':sidecar_desc,
                 'launchReceipt':None if owner is None else owner.phase_receipts['launch'],
                 'responseReceipt':None if owner is None else owner.phase_receipts['response'],
                 'terminalReceipt':None if owner is None else owner.phase_receipts['terminal'],
                 'comparison':comparison_desc,'counts':counts,'noEffects':dict(no_effects),
                 'cleanup':{'qualified':clean,'problems':cleanup_problems[:32]},'integrity':integrity,
                 'status':status,'error':job_error,'secondaryErrors':job_secondary[:32]}
            # Directory creation/capture failure is still a failed run, never a retry.
            jobs.append(save(directory/'job.json',row,'localJobCapture'));original_outputs.append(jobs[-1])
            for key in counters:total[key]=None if total[key] is None or counts[key] is None else total[key]+counts[key]
            all_clean=all_clean and clean is True;all_job_evidence=all_job_evidence and integrity['evidenceComplete'] is True
            if status!='MATCHED':overall=status;run_error=job_error
        current();run_integrity.update(sourceCurrent=True,inputsCurrent=True,evidenceComplete=all_job_evidence and len(jobs)==2 and not not_executed)
    except BaseException as exc:
        run_error=run_error or fact(exc);overall='UNQUALIFIED';run_integrity['evidenceComplete']=False
        if owner is not None:all_clean=all_clean and clean is True
        try:current();run_integrity.update(sourceCurrent=True,inputsCurrent=True)
        except BaseException as drift:
            run_integrity.update(sourceCurrent=None,inputsCurrent=None);secondary.append(fact(drift))
        known=set(scheduled)|{row['jobId'] for row in not_executed}
        if len(jobs)<len(scheduled):total={k:None for k in counters}
        for plan in wc['jobs']:
            if plan['jobId'] not in known:not_executed.append({'jobId':plan['jobId'],'status':'NOT_EXECUTED','reason':'EARLIER_FAILURE'})
    artifacts=[]
    try:
        for d in original_outputs:A.need(A.equal(A.descriptor(d['path']),d),'ORIGINAL_LOCAL_OUTPUT_DRIFT')
        artifacts=collect_artifacts();current()
    except BaseException as exc:
        run_error=run_error or fact(exc);secondary.append(fact(exc));overall='UNQUALIFIED';run_integrity.update(sourceCurrent=None,inputsCurrent=None,evidenceComplete=False)
    ended=time.monotonic_ns()
    if len(jobs)!=2 or not_executed or any(v is None for v in total.values()):
        if overall=='MATCHED':overall='UNQUALIFIED';run_error=run_error or fact(ValueError('INCOMPLETE_TWO_BACKEND_RUN'))
    result={'schema':'n02316-local-run-capture-v1','runId':cfg['runId'],'runRole':cfg['runRole'],
            'executionSession':cfg['executionSession'],'config':ctx['configDescriptor'],'workerConfig':ctx['workerConfigDescriptor'],
            'release':ctx['releaseDescriptor'],'candidate':cfg['candidate'],'sourceApproval':cfg['sourceApproval'],
            'orderedJobs':['Q-JS','Q-RUST'],'jobs':jobs,'notExecuted':not_executed,'counts':total,'noEffects':no_effects,
            'environment':dict(ENV),'outputRoot':str(root),'artifacts':artifacts,'integrity':run_integrity,
            'cleanup':{'qualified':all_clean,'problems':secondary[:32]},'outerLifecycle':None,
            'timing':{'startedMonotonicMs':started//1000000,'responseMonotonicMs':None,
                      'terminalMonotonicMs':ended//1000000,'elapsedMilliseconds':(ended-started)//1000000},
            'status':overall,'error':run_error,'secondaryErrors':secondary[:32]}
    A.validate(result,'@localCapture',defs)
    runner.put_json(root/'capture.json',result)
    return result


def main():
    A=bootstrap();A.need(len(sys.argv)==7,'CLI CONFIG SHA RELEASE SHA SESSION ROLE')
    ctx=A.verify_qualification(*sys.argv[1:]);result=run_local(ctx)
    raw=(json.dumps(result,ensure_ascii=True,separators=(',',':'))+'\n').encode()
    offset=0
    while offset<len(raw):
        n=os.write(1,raw[offset:]);A.need(n>0,'FULL_LOCAL_REPLY_WRITE');offset+=n
    return 0 if result['status']=='MATCHED' else 1


if __name__=='__main__':
    try:sys.exit(main())
    except BaseException as exc:
        if isinstance(exc,SystemExit):raise
        os.write(2,(type(exc).__name__+': '+str(exc))[:16384].encode('utf-8','backslashreplace')+b'\n');sys.exit(1)
