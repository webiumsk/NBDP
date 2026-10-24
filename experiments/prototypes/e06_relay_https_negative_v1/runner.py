"""SOURCE ONLY. Isolated10-cell N02/N03/N16 runner; importing starts nothing.

The original OwnedCase interval is byte-identical. N never interprets S04 as
acquisition: every case and local-native adapter uses phase_progress=None.
Only later exact external releases permit admission or execution.
"""
import hashlib
import errno
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ADMISSION={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/admission.py', 'bytes': 53263, 'sha256': '24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'}
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
     'WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'}
PYTHON={'path':'/home/peterhorvath/.miniforge3/bin/python3.13','bytes':32959480,
 'sha256':'5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
A=None

def init_owned_case_io(admission_module):
    """LOCAL and TARGET initialize only the same fixed checked source module."""
    global A
    path=Path(ADMISSION['path']);raw=path.read_bytes()
    if str(path.resolve(strict=True))!=str(path) or path.is_symlink() or len(raw)!=ADMISSION['bytes'] or hashlib.sha256(raw).hexdigest()!=ADMISSION['sha256']:
        raise ValueError('FIXED_ADMISSION_PIN')
    if Path(admission_module.__file__).resolve(strict=True)!=path:
        raise ValueError('FIXED_ADMISSION_MODULE_IDENTITY')
    A=admission_module
    return A

def bootstrap():
    source=Path(ADMISSION['path']);raw=source.read_bytes()
    if source.resolve(strict=True)!=source or source.is_symlink() or len(raw)!=ADMISSION['bytes'] or hashlib.sha256(raw).hexdigest()!=ADMISSION['sha256']:
        raise ValueError('FIXED_ADMISSION_PIN')
    if dict(os.environ)!=ENV:raise ValueError('EXACT_OUTER_ENVIRONMENT')
    if Path(sys.executable).resolve(strict=True)!=Path(PYTHON['path']):raise ValueError('FIXED_OUTER_PYTHON')
    digest=hashlib.sha256();size=0
    with open(PYTHON['path'],'rb') as handle:
        while block:=handle.read(1048576):digest.update(block);size+=len(block)
    if size!=PYTHON['bytes'] or digest.hexdigest()!=PYTHON['sha256']:raise ValueError('FIXED_OUTER_PYTHON_PIN')
    spec=importlib.util.spec_from_file_location('_n02316_fixed_admission',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    init_owned_case_io(module)
    A.need(A.equal(A.descriptor(sys.executable),A.PYTHON),'FIXED_OUTER_PYTHON_PIN')
    return A

def error_fact(exc):
    return {'name':type(exc).__name__[:1024],'message':str(exc)[:16384],
            'code':None,'stack':None}

def put_bytes(p,raw):
    A.need(type(raw) is bytes and len(raw)<=33554432,'EVIDENCE_WRITE_BOUND')
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as handle:handle.write(raw);handle.flush();os.fsync(fd)
    finally:os.close(fd)
    parent=os.open(Path(p).parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(parent)
    finally:os.close(parent)
    return A.descriptor(p)

def put_json(p,value):
    return put_bytes(p,(json.dumps(value,ensure_ascii=True,separators=(',',':'))+'\n').encode())

def one_line(raw):
    A.need(type(raw) is bytes and len(raw)<=16777216 and raw.endswith(b'\n') and raw.count(b'\n')==1,'EXACT_ONE_JSONL')
    return A.loads(raw[:-1])

def pure_group_signal_allowed(ownership,observation,returncode):
    """Actual signal gate: a fresh WNOWAIT child observation, before any reap."""
    return ownership=='HELD' and observation in ('RUNNING','EXITED') and returncode is None


def pure_phase_timeout(now_ns,window_deadline_ns,anchors):
    """Non-rebased monotonic policy; completion cannot erase an overdue interval."""
    if now_ns>=window_deadline_ns:return 'CASE_OUTER_DEADLINE'
    for name,seconds in (('acquisition',150),('consumer',120)):
        v=anchors[name]
        if v['startedNs'] is not None:
            end=v['completedNs'] if v['completedNs'] is not None else now_ns
            if end-v['startedNs']>=seconds*1000000000:return 'CASE_'+name.upper()+'_DEADLINE'
    return None


class OwnedCase:
    """Owned Popen, WNOWAIT observations, no post-reap numeric group operations.

    Only HELD permits signals, each preceded by fresh waitid(WNOWAIT). REAPING
    is latched BEFORE the sole consuming waitid. ECHILD/ambiguous observation
    loses ownership: never guess a process/group from its numeric identifier.
    Cleanup keeps the leader unreaped until every possible group signal ends.
    The six optional I/O seams serve inert controls, never frame/CLI input.
    """
    def __init__(self,argv,directory,env,deadline,current,phase_progress=None,io=None):
        self.argv=list(argv);self.directory=directory;self.env=dict(env);self.deadline=deadline;self.current=current
        self.process=None;self.selector=None;self.streams={k:None for k in ('stdin','stdout','stderr')}
        self.total={'stdout':0,'stderr':0};self.out={k:bytearray() for k in self.total}
        self.limits={'stdout':16777216,'stderr':65536};self.ownership='NOT_ACQUIRED';self.observation=None
        self.primary=None;self.secondary=[];self.secondary_bytes=0;self.secondary_overflow=False
        self.receipt=None;self.capture_complete=False;self.phase_progress=phase_progress
        self.phase={'windowDeadlineNs':int(deadline*1000000000),'lastObservationNs':None,'maxObservationGapNs':0,
                    'timeoutCause':None,'anchors':{n:{'startedNs':None,'completedNs':None,'startSource':None,'completionSource':None}
                    for n in ('acquisition','consumer')},'observations':[],
                    'meaning':'Parent first-observed fixed source-owned pathname creation; internal entry/durability times UNKNOWN. No hard realtime/host-stall or escaped-descendant guarantee.'}
        self.io={'waitid':os.waitid,'killpg':os.killpg,'clockNs':time.monotonic_ns,
                 'writeBytes':put_bytes,'writeJSON':put_json,'stderr':lambda b:os.write(2,b)}
        if io is not None:
            if set(io)!=set(self.io) or not all(callable(v) for v in io.values()):raise ValueError('CLOSED_INERT_IO_SEAMS')
            self.io=dict(io)
        self.life={'launchAttempt':False,'acquisition':'NOT_ATTEMPTED','pid':None,'exitCode':None,'signal':None,
                   'reaped':False,'stdoutEOF':False,'stderrEOF':False,'timedOut':False,'forced':False,'error':None}
    def primary_error(self,exc):
        if self.primary is None:self.primary=error_fact(exc);self.life['error']=dict(self.primary)
    def secondary_error(self,owner,exc):
        row={'owner':str(owner)[:256],'error':error_fact(exc)};size=len(json.dumps(row).encode())
        if len(self.secondary)<16 and self.secondary_bytes+size<=131072:self.secondary.append(row);self.secondary_bytes+=size
        else:self.secondary_overflow=True
    def attempt(self,owner,fn):
        try:return True,fn()
        except BaseException as exc:self.secondary_error(owner,exc);return False,None
    def observe_owned(self):
        if self.ownership!='HELD':return 'UNKNOWN'
        if self.process is None or self.process.returncode is not None:
            self.ownership='UNKNOWN';raise ValueError('OWNERSHIP_ENDED_OUTSIDE_SUPERVISOR')
        try:r=self.io['waitid'](os.P_PID,self.process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
        except BaseException as exc:
            self.ownership='UNKNOWN'
            # ECHILD is loss of ownership, never proof of cleanup/reap by this owner.
            if isinstance(exc,ChildProcessError) or isinstance(exc,OSError) and exc.errno==errno.ECHILD:
                raise ValueError('CHILD_OWNERSHIP_UNKNOWN_ECHILD') from exc
            raise
        if r is not None and r.si_pid!=self.process.pid:
            self.ownership='UNKNOWN';raise ValueError('CHILD_OBSERVATION_IDENTITY')
        self.observation=r;return 'EXITED' if r is not None else 'RUNNING'
    def signal_owned_group(self,number):
        observation=self.observe_owned()
        if not pure_group_signal_allowed(self.ownership,observation,self.process.returncode if self.process else None):
            raise ValueError('NO_RETAINED_GROUP_SIGNAL_AUTHORITY')
        self.life['forced']=True
        # The exact child remains unreaped during every allowed group operation.
        self.io['killpg'](self.process.pid,number)
    def reap_exited(self):
        if self.observe_owned()!='EXITED':return False
        self.ownership='REAPING'  # BEFORE the consuming syscall, including interruption/error paths.
        try:r=self.io['waitid'](os.P_PID,self.process.pid,os.WEXITED|os.WNOHANG)
        except BaseException:
            self.ownership='UNKNOWN';raise
        if r is None or r.si_pid!=self.process.pid:
            self.ownership='UNKNOWN';raise ValueError('REAP_OUTCOME_UNKNOWN')
        if r.si_code==os.CLD_EXITED:code=r.si_status;sig=None;returncode=code
        elif r.si_code in (os.CLD_KILLED,os.CLD_DUMPED):code=None;sig=signal.Signals(r.si_status).name;returncode=-r.si_status
        else:self.ownership='UNKNOWN';raise ValueError('REAP_STATUS_UNKNOWN')
        self.process.returncode=returncode
        self.life.update(reaped=True,exitCode=code,signal=sig);self.ownership='REAPED';return True
    def watch_phases(self):
        now=self.io['clockNs']();previous=self.phase['lastObservationNs']
        if previous is not None:self.phase['maxObservationGapNs']=max(self.phase['maxObservationGapNs'],now-previous)
        self.phase['lastObservationNs']=now
        cause=pure_phase_timeout(now,self.phase['windowDeadlineNs'],self.phase['anchors'])
        if cause:self.phase['timeoutCause']=cause;self.life['timedOut']=True;raise TimeoutError(cause)
        if self.phase_progress is not None:
            case,ident=self.phase_progress
            # S04 pathname creation conservatively includes reservation, imports and acquisition.
            # S05 starts the consumer interval; S06 completion includes its owned cleanup.
            for suffix in ('S04','S05','S06'):
                file=case/(ident+'-'+suffix+'.json')
                if not file.exists():continue
                st=file.lstat()
                if file.is_symlink() or not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o600:
                    raise ValueError('SOURCE_OWNED_PHASE_PATH')
                if any(row['source']==str(file) for row in self.phase['observations']):continue
                self.phase['observations'].append({'source':str(file),'firstObservedNs':now,'sizeAtObservation':st.st_size})
                acquisition=self.phase['anchors']['acquisition'];consumer=self.phase['anchors']['consumer']
                if suffix=='S04':acquisition.update(startedNs=now,startSource=str(file))
                elif suffix=='S05':
                    if acquisition['startedNs'] is None:raise ValueError('ACQUISITION_PHASE_ORIGIN_MISSING')
                    acquisition.update(completedNs=now,completionSource=str(file));consumer.update(startedNs=now,startSource=str(file))
                else:
                    if consumer['startedNs'] is None:raise ValueError('CONSUMER_PHASE_ORIGIN_MISSING')
                    consumer.update(completedNs=now,completionSource=str(file))
            cause=pure_phase_timeout(now,self.phase['windowDeadlineNs'],self.phase['anchors'])
            if cause:self.phase['timeoutCause']=cause;self.life['timedOut']=True;raise TimeoutError(cause)
    def read_key(self,key):
        name=key.data
        try:raw=os.read(key.fileobj.fileno(),65536)
        except BaseException:
            self.total[name]=None  # Interrupted/error read cannot certify its byte accounting.
            raise
        if not raw:
            self.life[name+'EOF']=True;self.selector.unregister(key.fileobj);return
        if self.total[name] is not None:self.total[name]+=len(raw)
        remaining=max(0,self.limits[name]-len(self.out[name]));self.out[name].extend(raw[:remaining])
        if self.total[name] is None or self.total[name]>self.limits[name]:raise ValueError('CASE_OUTER_STREAM_BOUND')
    def pump(self,seconds,cleanup=False):
        if self.selector is None:return
        if cleanup:
            ok,events=self.attempt('cleanup:selector-select',lambda:self.selector.select(seconds))
            if not ok:return
            for key,_ in events:self.attempt('cleanup:pipe-read:'+key.data,lambda key=key:self.read_key(key))
        else:
            for key,_ in self.selector.select(seconds):self.read_key(key)
    def all_eof(self):return self.life['stdoutEOF'] and self.life['stderrEOF']
    def cleanup(self):
        if self.ownership=='REAPING':self.ownership='UNKNOWN'  # Consuming syscall may already have completed.
        if self.process is not None and self.ownership=='HELD':
            ok,observation=self.attempt('cleanup:initial-WNOWAIT',self.observe_owned)
            if ok and not (observation=='EXITED' and self.all_eof()):
                self.attempt('cleanup:owned-SIGTERM',lambda:self.signal_owned_group(signal.SIGTERM))
                self.cleanup_until(2)
                if self.ownership=='HELD':
                    ok,observation=self.attempt('cleanup:post-TERM-WNOWAIT',self.observe_owned)
                    if ok and not (observation=='EXITED' and self.all_eof()):
                        self.attempt('cleanup:owned-SIGKILL',lambda:self.signal_owned_group(signal.SIGKILL));self.cleanup_until(5)
            if self.ownership=='HELD':
                ok,reaped=self.attempt('cleanup:final-reap',self.reap_exited)
                if ok and not reaped:self.secondary_error('cleanup:unreaped-child',ValueError('OWNED_CHILD_STILL_UNREAPED'))
        # No signal path exists below this point; bounded drain and all closes are independent.
        until=self.io['clockNs']()+2000000000;turns=0
        while self.selector is not None and not self.all_eof() and self.io['clockNs']()<until and turns<4096:
            turns+=1;self.pump(0.05,True)
        if self.process is not None:
            for name in ('stdin','stdout','stderr'):
                self.attempt('cleanup:pipe-close:'+name,lambda name=name:self.close_pipe(name))
        if self.selector is not None:self.attempt('cleanup:selector-close',self.selector.close)
        if self.process is not None and (self.ownership!='REAPED' or not self.all_eof()):
            self.secondary_error('cleanup:ownership-or-EOF',ValueError('OWNED_CLEANUP_NOT_CONFIRMED'))
    def cleanup_until(self,seconds):
        until=self.io['clockNs']()+seconds*1000000000;turns=0
        while self.ownership=='HELD' and self.io['clockNs']()<until and turns<4096:
            turns+=1;self.pump(0.05,True)
            ok,observation=self.attempt('cleanup:WNOWAIT',self.observe_owned)
            if not ok or observation=='EXITED' and self.all_eof():break
    def close_pipe(self,name):
        pipe=getattr(self.process,name,None)
        if pipe is not None and not pipe.closed:pipe.close()
    def capture(self):
        # Attempt every raw stream even after earlier storage/capture failures.
        for name,raw in [('stdin',b''),*[(k,bytes(v)) for k,v in self.out.items()]]:
            ok,d=self.attempt('capture:raw:'+name,lambda name=name,raw=raw:self.io['writeBytes'](self.directory/(name+'.bin'),raw))
            if ok:self.streams[name]=d
        self.capture_complete=all(self.streams.values())
        if (self.secondary or self.secondary_overflow or not self.capture_complete) and self.life['error'] is None:
            self.life['error']=error_fact(ValueError('OUTER_CLEANUP_OR_CAPTURE_UNQUALIFIED'))
        self.record={'schema':'i4-python-owned-case-v2','argv':self.argv,'cwd':str(self.directory),'environment':self.env,
                     'lifecycle':dict(self.life),'ownership':self.ownership,'primaryError':self.primary,
                     'secondaryErrors':list(self.secondary),'secondaryOverflow':self.secondary_overflow,'captureComplete':self.capture_complete,
                     'streams':dict(self.streams),'observedBytes':dict(self.total),'retainedBytes':{k:len(v) for k,v in self.out.items()},'phaseMonitor':self.phase}
        ok,d=self.attempt('capture:receipt',lambda:self.io['writeJSON'](self.directory/'receipt.json',self.record))
        if ok:self.receipt=d
        else:
            self.capture_complete=False
            if self.life['error'] is None:self.life['error']=error_fact(ValueError('OUTER_RECEIPT_CAPTURE_UNQUALIFIED'))
            # Fixed fallback is bounded diagnostic evidence, not a substituted receipt.
            b=(json.dumps({'schema':'i4-outer-receipt-capture-failure-v1','primary':self.primary,'ownership':self.ownership,
                           'secondary':self.secondary,'overflow':self.secondary_overflow,'qualified':False})+'\n').encode()
            self.attempt('capture:bounded-stderr-fallback',lambda:self.io['stderr'](b[:8192]))
    def run(self):
        try:
            self.current();self.life.update(launchAttempt=True,acquisition='UNKNOWN')
            self.process=subprocess.Popen(self.argv,cwd=self.directory,env=self.env,stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,bufsize=0)
            self.ownership='HELD';self.life.update(acquisition='ACQUIRED',pid=self.process.pid)
            self.process.stdin.close();self.selector=selectors.DefaultSelector()
            for name in self.out:
                pipe=getattr(self.process,name);os.set_blocking(pipe.fileno(),False);self.selector.register(pipe,selectors.EVENT_READ,name)
            while True:
                self.watch_phases();observation=self.observe_owned()
                if observation=='EXITED' and self.all_eof():break
                self.pump(0.1)
            self.reap_exited()
        except BaseException as exc:self.primary_error(exc)
        finally:
            # Even unexpected cleanup failures cannot bypass all raw receipt writes.
            self.attempt('cleanup:outer-guard',self.cleanup)
            ok,_=self.attempt('capture:outer-guard',self.capture)
            if not ok:
                self.capture_complete=False
                if self.life['error'] is None:self.life['error']=error_fact(ValueError('OUTER_CAPTURE_UNQUALIFIED'))
                self.attempt('capture:last-bounded-diagnostic',lambda:self.io['stderr'](b'I4_OUTER_CAPTURE_UNQUALIFIED\n'))
        return bytes(self.out['stdout'])


def load_checker(ctx):
    mapping=A.closure(ctx['sourceClosure']);pin=A.descriptor(HERE/'checker.py');A.member(mapping,pin)
    spec=importlib.util.spec_from_file_location('_n02316_admitted_checker',pin['path'])
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.A=A
    return module.Checker(ctx)


def run(ctx):
    A.need(ctx['mode']=='TARGET','TARGET_ONLY_CONTEXT')
    m=ctx['manifest'];out=Path(ctx['output']);out.mkdir(mode=0o700)
    started=time.monotonic();deadline=started+1500
    capture={'schema':'n02316-python-capture-v1','qualified':False,'manifest':ctx['manifestDescriptor'],
      'release':ctx['releaseDescriptor'],'cases':[],'notExecuted':[],'labCleanup':None,
      'finalIntegrity':False,'errors':[],'limits':['SHARED_HOST_HARNESS_INPUTS','FINITE_N02_N03_N16_ONLY',
      'NO_ACQUISITION_ORIGINAL_RECEIPT_BUSINESS_EFFECTS_GLOBAL_FINALITY_FS_WHOLE_E06',
      'HOST_PID_REAP_AND_ESCAPED_DESCENDANT_CONTAINMENT_UNKNOWN']}
    lab=None;entered=False;failure=None;all_evidence={};checker=None
    inputs=[ctx['manifestDescriptor'],ctx['releaseDescriptor'],*m['workerInputs'].values()]
    def current():
        A.need(time.monotonic()<deadline,'PHASE_DEADLINE');A.closure(ctx['sourceClosure'])
        ctx['recheckAuthorityEvidence']()
        for d in inputs:A.need(A.equal(A.descriptor(d['path']),d),'ORIGINAL_RUN_INPUT_DRIFT')
        for d in all_evidence.values():A.checked(d)
    try:
        current();put_json(out/'admission.json',{'manifest':ctx['manifestDescriptor'],
          'release':ctx['releaseDescriptor'],'sourceClosure':ctx['sourceClosure']})
        checker=load_checker(ctx)
        # The same immutable relay supervisor and two images; no TLS/HTTP/browser.
        protected=A.document(A.DATA['protected-deltas.json'])
        positive=A.document(protected['baselineClosure']);mapping=A.closure(ctx['sourceClosure'])
        old_path=str(ROOT/'experiments/prototypes/e06_relay_metadata_v1/selection.json')
        old_d=next(d for d in positive if d['path']==old_path);A.member(mapping,old_d)
        old=A.document(old_d);provenance=old['relayProvenance'];assets=provenance['assets']
        for d in [assets['supervisor'],assets['strfryConfig'],assets['rsRelayConfig'],
                  provenance['dockerToolReference'],A.PYTHON]:
            A.member(mapping,d);A.need(A.equal(A.descriptor(d['path']),d),'CURRENT_LAB_INPUT');inputs.append(d)
        inputs.append(old_d);current()
        spec=importlib.util.spec_from_file_location('_n02316_exact_isolated_relay_lab',assets['supervisor']['path'])
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        A.need(A.equal(helper.IMAGES,provenance['imageIds'])
          and A.equal(helper.PORTS,{'strfry':(17777,7777),'rs-relay':(18081,8080)}),'FIXED_LAB_IMAGES_ENDPOINTS')
        config={'scope':'CURRENT_CARRIER_TWO_RELAY_LAB_ONLY','execution_allowed':True,'run_id':m['runId'],
          'files':{'supervisor':assets['supervisor'],'python':A.PYTHON,'docker':provenance['dockerToolReference'],
          'strfry_config':assets['strfryConfig'],'rs_relay_config':assets['rsRelayConfig']}}
        lab=helper.RelayLab(config,out/'lab');tick=time.monotonic();lab.__enter__();entered=True
        capture['labStartupMilliseconds']=round((time.monotonic()-tick)*1000)
        A.need(capture['labStartupMilliseconds']<=360000,'LAB_STARTUP_BOUND')
        selection=A.document(A.DATA['selection-map.json']);defs=ctx['definitions']
        for cell in selection['cells']:
            current();lab.assert_healthy();ident=cell['cellId'];case=out/ident;case.mkdir(mode=0o700)
            monitor=case/'outer-monitor';monitor.mkdir(mode=0o700)
            frame={'schema':'n02316-case-private-frame-v1','lane':'LAB-N-02-03-16','cellId':ident,
              'windowId':cell['windowId'],'manifest':ctx['manifestDescriptor'],'release':ctx['releaseDescriptor'],
              'workerData':m['workerInputs'][ident],'output':str(case)}
            A.validate(frame,'@frame',defs);fd=put_json(case/'frame.json',frame)
            argv=[A.NODE['path'],str(HERE/'case.mjs'),fd['path'],fd['sha256']]
            child=OwnedCase(argv,monitor,ENV,min(deadline,time.monotonic()+240),current,phase_progress=None)
            row={'cellId':ident,'frame':fd,'qualified':False,'outer':None,'reply':None,'comparison':None,'error':None}
            capture['cases'].append(row)
            try:
                raw=child.run();row['outer']=child.receipt
                A.need(raw!=b'','NO_CASE_CLI_REPLY');row['reply']=one_line(raw)
                A.validate(row['reply'],'@caseCLIReply',defs)
                result=checker.check_case(cell,row)
                row['comparison']=put_json(case/'outer-comparison.json',result);row['qualified']=True
                all_evidence.update(checker.verified)
                for d in [fd,row['comparison'],child.receipt,*child.streams.values()]:
                    A.need(d is not None,'COMPLETE_OUTER_CAPTURE_GRAPH');all_evidence[d['path']]=d
                current();lab.assert_healthy()
            except BaseException as exc:row['error']=error_fact(exc);raise
    except BaseException as exc:failure=exc;capture['errors'].append(error_fact(exc))
    finally:
        # RelayLab.__enter__ already preserves/cleans startup failure. Do not
        # repeat cleanup or overwrite that original negative evidence.
        if entered:
            tick=time.monotonic()
            try:lab.__exit__(type(failure) if failure else None,failure,None)
            except BaseException as exc:capture['errors'].append(error_fact(exc))
            capture['labCleanupMilliseconds']=round((time.monotonic()-tick)*1000)
            if capture['labCleanupMilliseconds']>60000:
                capture['errors'].append(error_fact(ValueError('FINAL_LAB_CLEANUP_BOUND')))
        try:
            pin=A.descriptor(out/'lab'/'cleanup.json');v=A.document(pin);capture['labCleanup']=pin
            all_evidence[pin['path']]=pin
            A.need(v['qualified'] is True and v['problems']==[] and v['uncertain_creates']==[],
                   'ACTUAL_OWNED_LAB_CLEANUP')
        except BaseException as exc:capture['errors'].append(error_fact(exc))
        try:
            current();capture['finalIntegrity']=True
        except BaseException as exc:capture['errors'].append(error_fact(exc))
        selected=A.document(A.DATA['selection-map.json'])['orderedCells'];done={r['cellId'] for r in capture['cases']}
        capture['notExecuted']=[{'cellId':c,'reason':'EARLIER_FAILURE'} for c in selected if c not in done]
        capture['elapsedMilliseconds']=round((time.monotonic()-started)*1000)
        if not capture['errors'] and checker is not None:
            try:capture['comparison']=checker.check_run(capture)
            except BaseException as exc:capture['errors'].append(error_fact(exc))
        capture['qualified']=not capture['errors'] and not capture['notExecuted'] and len(capture['cases'])==10 \
          and all(r['qualified'] for r in capture['cases']) and capture['finalIntegrity']
        # Preserve rejected/partial raw artifacts; no overwrite or oracle substitution.
        try:
            files=[];total=0
            for p in sorted(out.rglob('*')):
                A.need(not p.is_symlink(),'OWNED_OUTPUT_NO_SYMLINK')
                if p.is_file():
                    d=A.descriptor(p);total+=d['bytes']
                    A.need(len(files)<2048 and total<=33554432,'OWNED_EVIDENCE_PACK_BOUND');files.append(d)
            capture['artifactManifest']=put_json(out/'artifact-manifest.json',
              {'schema':'n02316-owned-output-inventory-v1','files':files,'bytes':total,
              'excludes':['artifact-manifest.json','capture.json'],
              'meaning':'Pre-finalization owned files; final capture/inventory separately pinned.'})
        except BaseException as exc:capture['errors'].append(error_fact(exc));capture['qualified']=False
        put_json(out/'capture.json',capture)
    return 0 if capture['qualified'] else 1


def main(argv):
    if len(argv)!=7:raise ValueError('CLI runner.py MANIFEST SHA RELEASE SHA EXECUTION_SESSION primary|qa')
    module=bootstrap();ctx=module.verify(argv[1],argv[2],argv[3],argv[4],argv[5],argv[6])
    return run(ctx)


if __name__=='__main__':
    try:code=main(sys.argv)
    except BaseException as exc:sys.stderr.write(type(exc).__name__+': '+str(exc)[:16384]+'\n');code=2
    raise SystemExit(code)
