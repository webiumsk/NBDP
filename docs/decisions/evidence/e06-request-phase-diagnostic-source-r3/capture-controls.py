"""SOURCE ONLY. Finite private capture of thirteen reviewed Python fixture controls.

No Node, strace, attach, project admission or diagnostic workload is invoked.
External actual source review/authorization must precede evaluating this helper.
"""
from pathlib import Path
import hashlib
import json
import os
import selectors
import signal
import stat
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
TEST=HERE/'test_observer.py'
EXPECTED_PYTHON={'path':'/home/peterhorvath/.miniforge3/bin/python3.13','bytes':32959480,
 'sha256':'5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
CAPS={'stdout':1048576,'stderr':1048576}
EXTERNAL_SECONDS=25
ACTIVE_SECONDS=23
CLEANUP_SECONDS=2

def pin(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def private_file(p):
    s=p.lstat()
    assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_uid==os.getuid()
    assert stat.S_IMODE(s.st_mode)==0o600

def exclusive(p):
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    return os.fdopen(fd,'wb',buffering=0)

def snapshot_paths(expected):
    """Full canonical paths are identities; basenames are never inventory keys."""
    observed={}
    for actual_path,expected_pin in expected.items():
        p=Path(actual_path)
        assert p.is_absolute() and p.resolve(strict=True)==p and not p.is_symlink()
        assert expected_pin['path']==actual_path
        observed[actual_path]=pin(p)
    assert len(observed)==len(expected)
    return observed

def main():
    started=time.monotonic();deadline=started+ACTIVE_SECONDS;total=started+EXTERNAL_SECONDS
    assert pin(Path(sys.executable).resolve())==EXPECTED_PYTHON
    for name in ('controls-actual-r1','suite-stdout.bin','suite-stderr.bin','suite-execution.json'):
        assert not os.path.lexists(HERE/name),name
    subject_path=HERE/'subject.json';subject=json.loads(subject_path.read_bytes())
    expected={d['path']:d for d in subject['files']}
    assert len(expected)==len(subject['files']) and subject['scope']=='DIAGNOSTIC_REAL_REQUEST_PHASE_ONLY'
    expected[str(subject_path)]=pin(subject_path)
    for path,d in expected.items():
        p=Path(path);assert p.parent in (HERE, HERE.parent/'e06-local-fonly-primary-preparation-r3', HERE.parent/'e06-local-fonly-primary-execution-r3', HERE.parent/'e06-request-phase-diagnostic-source-r1', HERE.parent/'e06-request-phase-diagnostic-source-r2', HERE.parent/'e06-strace-containment-controls-r1', HERE.parent/'e06-strace-containment-controls-r2') and p.resolve(strict=True)==p
        private_file(p);assert pin(p)==d
        assert time.monotonic()<deadline
    before=snapshot_paths(expected)
    assert str(Path(__file__).resolve()) in expected and str(TEST) in expected
    argv=[sys.executable,'-I','-B',str(TEST)]
    streams={name:exclusive(HERE/('suite-'+name+'.bin')) for name in CAPS}
    counts=dict.fromkeys(CAPS,0);observed=dict.fromkeys(CAPS,0);eof=dict.fromkeys(CAPS,False)
    write_state=dict.fromkeys(CAPS,'WRITABLE')
    first=None;secondary=[];forced=False;signals=[];reaped=False;child=None;selector=None;exit_code=None
    def fault(error):
        nonlocal first
        item={'type':type(error).__name__,'message':str(error)[:4096]}
        if first is None:first=item
        elif len(secondary)<16:secondary.append(item)
    def observe():
        assert child is not None and child.returncode is None and not reaped
        return os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
    def pump(delay):
        for key,_ in selector.select(delay):
            name=key.data
            try:b=os.read(key.fd,65536)
            except BlockingIOError:continue
            if not b:eof[name]=True;selector.unregister(key.fileobj);continue
            observed[name]+=len(b);keep=b[:max(0,CAPS[name]-counts[name])]
            if keep and write_state[name]=='WRITABLE':
                try:
                    n=streams[name].write(keep)
                    if type(n) is int and 0<=n<=len(keep):counts[name]+=n
                    if n!=len(keep):raise OSError('SUITE_SHORT_CAPTURE_WRITE')
                except BaseException:
                    write_state[name]='POISONED_FAILED_OR_UNCERTAIN';raise
            if len(keep)!=len(b):raise ValueError('SUITE_'+name.upper()+'_BOUND')
    try:
        child=subprocess.Popen(argv,cwd=HERE,env=ENV,stdin=subprocess.DEVNULL,
          stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,bufsize=0)
        selector=selectors.DefaultSelector()
        for name,pipe in [('stdout',child.stdout),('stderr',child.stderr)]:
            os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,name)
        while True:
            if time.monotonic()>=deadline:raise TimeoutError('SUITE_ACTIVE_CAPTURE_BOUND')
            if observe() is not None and all(eof.values()):break
            pump(min(.05,max(0,deadline-time.monotonic())))
    except BaseException as error:fault(error)
    finally:
        if child is not None:
            try:
                exited=observe();complete=exited is not None and all(eof.values())
                cleanup_deadline=min(time.monotonic()+CLEANUP_SECONDS,total)
                for signum,seconds in [(signal.SIGTERM,1),(signal.SIGKILL,1)]:
                    if complete:break
                    observe()
                    try:os.killpg(child.pid,signum);signals.append(int(signum));forced=True
                    except ProcessLookupError:pass
                    until=min(cleanup_deadline,time.monotonic()+seconds)
                    while time.monotonic()<until:
                        try:
                            if selector is not None:pump(min(.05,max(0,until-time.monotonic())))
                        except BaseException as error:fault(error)
                        exited=observe();complete=exited is not None and all(eof.values())
                        if complete:break
                if exited is not None:exit_code=child.wait(timeout=0);reaped=True
                else:raise TimeoutError('SUITE_CHILD_NOT_REAPED_IN_BOUND')
            except BaseException as error:fault(error)
        if selector is not None:selector.close()
        if child is not None:
            for pipe in (child.stdout,child.stderr):
                try:pipe.close()
                except BaseException as error:fault(error)
        for handle in streams.values():
            try:handle.flush();os.fsync(handle.fileno())
            except BaseException as error:fault(error)
            finally:handle.close()
    raw={name:pin(HERE/('suite-'+name+'.bin')) for name in CAPS}
    for name,d in raw.items():
        private_file(Path(d['path']));counts[name]=d['bytes']
        if d['bytes']>CAPS[name]:fault(ValueError('FINAL_SUITE_CAPTURE_CAP'))
    after=snapshot_paths(before)
    record={'schema':'e06-startup-prefix-owned-child-suite-capture-v2','operator':'/root/local_monitor_controls',
      'argv':argv,'cwd':str(HERE),'stdin':'DEVNULL_ZERO_BYTES','environment':ENV,
      'interpreter':EXPECTED_PYTHON,'captureSource':pin(Path(__file__).resolve()),'source':pin(TEST),
      'frozenBefore':before,'frozenAfter':after,'exit':exit_code,'reaped':reaped,'forced':forced,
      'signals':signals,'stdoutEOF':eof['stdout'],'stderrEOF':eof['stderr'],
      'firstError':first,'secondaryErrors':secondary,'observedBytes':observed,'retainedBytes':counts,
      'writeState':write_state,
      'raw':raw,'streamCaps':CAPS,'externalCeilingSeconds':EXTERNAL_SECONDS,
      'activeCeilingSeconds':ACTIVE_SECONDS,'cleanupCeilingSeconds':CLEANUP_SECONDS,
      'elapsedNs':int((time.monotonic()-started)*1000000000),
      'artifactMode':'EXCLUSIVE_REGULAR_0600_NOFOLLOW_FLUSH_FSYNC',
      'limits':['Fixture controls only; no Node/strace/LOCAL or runtime interoperability.',
        'Forced outer capture cannot attest escaped/separate-session descendant absence.',
        'Python deadline checks do not hard-preempt blocked kernel/filesystem calls.',
        'Suite exit0 is not independent acceptance or a canonical experiment PASS.']}
    path=HERE/'suite-execution.json'
    with exclusive(path) as f:
        serialized=(json.dumps(record,indent=2)+'\n').encode()
        written=f.write(serialized)
        if written!=len(serialized):raise OSError('COMPLETE_SUITE_EXECUTION_RECORD_WRITE_REQUIRED')
        f.flush();os.fsync(f.fileno())
    private_file(path)
    print(json.dumps({'execution':pin(path),'suiteExit':exit_code,'independentReviewRequired':True}))
    return 0 if exit_code==0 and reaped and not forced and first is None and all(eof.values()) and before==after else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except BaseException as error:
        if isinstance(error,SystemExit):raise
        os.write(2,('CONTROL_CAPTURE_FAILURE: '+type(error).__name__+': '+str(error))[:16384].encode('utf-8','backslashreplace')+b'\n')
        raise SystemExit(2)
