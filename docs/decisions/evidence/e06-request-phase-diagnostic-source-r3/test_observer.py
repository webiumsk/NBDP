"""SOURCE ONLY: thirteen pure controls, never Node or strace.

Ten real owned-Python-child capture cases plus three DATA/privacy/namespace/mode
controls. Fixtures substitute argv/ROOT/caps/deadlines only. They do not emulate
actual ptrace EXITKILL or prove descendant containment. All artifacts persist.
"""
from pathlib import Path
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().with_name('observer.py')
CONTROL_ROOT=SOURCE.parent/'controls-actual-r1'

def save(p,value):
    raw=(json.dumps(value,indent=2)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def module():
    spec=importlib.util.spec_from_file_location('real_request_observer_fixture',SOURCE)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class ObserverControls(unittest.TestCase):
    def capture_case(self,kind,write_fault=None):
        m=module();out=CONTROL_ROOT/kind;out.mkdir(mode=0o700);r,w=os.pipe2(os.O_CLOEXEC)
        prefix=f"import os,time,sys; os.write({w},b'prefix\\n'); "
        if kind=='natural-zero':code=f"import os,sys; x=sys.stdin.buffer.read(); os.write({w},b'stdin='+str(len(x)).encode()+b'\\n'); os.write(1,b'fixture-monitor-summary\\n')"
        elif kind=='natural-two':code=prefix+"os.write(2,b'fixture-local-refusal\\n'); raise SystemExit(2)"
        elif kind=='timeout':code=prefix+'time.sleep(8)'
        elif kind=='interrupt':code=prefix+f'time.sleep(.05); os.kill({os.getpid()},2) if os.getppid()=={os.getpid()} else None; time.sleep(8)'
        elif kind=='trace-cap':code=f"import os,time; os.write({w},b'T'*8192); time.sleep(8)"
        elif kind=='stdout-cap':code=prefix+"os.write(1,b'O'*2048); time.sleep(8)"
        elif kind=='stderr-cap':code=prefix+"os.write(2,b'E'*2048); time.sleep(8)"
        elif kind=='write-before':code=prefix+'time.sleep(8)'
        elif kind in ('short-positive','prefix-exception'):code=f"import os,time; os.write({w},b'P'*32768); time.sleep(8)"
        else:raise AssertionError('Unknown owned fixture')
        argv=[sys.executable,'-I','-B','-c',code];events=[];calls=[];state={'reaped':False}
        save(out/'fixture-input.json',{'case':kind,'argv':argv,'writeFault':write_fault,'activeFixtureSeconds':2,
          'cleanupFixtureSeconds':'.5','fixtureCaps':{'trace':1024,'stdout':256,'stderr':512},
          'meaning':'Owned Python child/synthetic trace only; no Node/strace/LOCAL or actual EXITKILL claim.'})
        original_wait=subprocess.Popen.wait;original_killpg=os.killpg;original_fdopen=os.fdopen
        def wait(p,*a,**k):
            rc=original_wait(p,*a,**k);state['reaped']=True;events.append({'op':'reaped','exit':rc});return rc
        def killpg(pid,sig):
            self.assertFalse(state['reaped'],'No signal after reap');events.append({'op':'signal','signal':int(sig)});return original_killpg(pid,sig)
        class FaultWrite:
            def __init__(self,h):self.h=h
            def write(self,b):
                calls.append({'requested':len(b),'fault':write_fault})
                if write_fault=='before':raise OSError('FIXTURE_WRITE_FAILURE')
                n=self.h.write(b[:128]);self.h.flush();calls[-1]['persisted']=n
                if write_fault=='short-positive':return n
                raise OSError('FIXTURE_PREFIX_THEN_EXCEPTION')
            def fileno(self):return self.h.fileno()
            def flush(self):return self.h.flush()
            def close(self):return self.h.close()
        def fdopen(fd,*a,**k):
            h=original_fdopen(fd,*a,**k)
            if write_fault and a and a[0]=='wb' and os.readlink('/proc/self/fd/'+str(fd))==str(out/'trace.bin'):return FaultWrite(h)
            return h
        started=time.monotonic()
        try:
            with patch.object(m,'ROOT',out),patch.object(m,'ACTIVE_SECONDS',2),patch.object(m,'CLEANUP_SECONDS',.5),\
                 patch.object(m,'CAPS',{'trace':1024,'stdout':256,'stderr':512}),\
                 patch.object(m.subprocess.Popen,'wait',wait),patch.object(m.os,'killpg',killpg),patch.object(m.os,'fdopen',fdopen):
                record=m.capture(argv,r,w,out,started,started+2,started+2.5)
            save(out/'capture-result.json',record)
        except BaseException as error:
            save(out/'capture-exception.json',{'type':type(error).__name__,'message':str(error)});raise
        finally:save(out/'lifecycle-events.json',{'events':events,'writeCalls':calls,'reaped':state['reaped']})
        raw={n:(out/(n+'.bin')).read_bytes() for n in ['trace','stdout','stderr']}
        self.assertTrue(record['reaped']);self.assertTrue(all(record['eof'].values()))
        self.assertEqual(events[-1]['op'],'reaped');pos=next(i for i,v in enumerate(events) if v['op']=='reaped')
        self.assertFalse(any(v['op']=='signal' for v in events[pos+1:]))
        with self.assertRaises(ProcessLookupError):os.kill(record['pid'],0)
        for n,limit in {'trace':1024,'stdout':256,'stderr':512}.items():
            self.assertEqual(record['retainedBytes'][n],len(raw[n]));self.assertEqual(record['raw'][n]['bytes'],len(raw[n]))
            self.assertLessEqual(len(raw[n]),limit)
        self.assertFalse(record['nativeCleanupQualified'])
        self.assertEqual(record['traceeContainment'],'UNKNOWN_REQUIRES_ACTUAL_NATIVE_AND_TRACE_GRAPH_REVIEW')
        self.assertEqual(record['killOnExit'],'REQUESTED_NOT_HOST_ATTESTED')
        return record,raw,calls

    def test_01_natural_zero_zero_stdin(self):
        r,b,_=self.capture_case('natural-zero');self.assertEqual(r['exit'],0);self.assertFalse(r['forced'])
        self.assertIsNone(r['firstError']);self.assertTrue(r['captureComplete']);self.assertEqual(b['trace'],b'stdin=0\n')
        self.assertEqual(b['stdout'],b'fixture-monitor-summary\n');self.assertEqual(b['stderr'],b'')

    def test_02_natural_two_is_preserved_not_success(self):
        r,b,_=self.capture_case('natural-two');self.assertEqual(r['exit'],2);self.assertFalse(r['forced'])
        self.assertIsNone(r['firstError']);self.assertTrue(r['captureComplete']);self.assertEqual(b['stderr'],b'fixture-local-refusal\n')

    def test_03_timeout_prefix_cleanup_unqualified(self):
        r,b,_=self.capture_case('timeout');self.assertTrue(r['timedOut']);self.assertTrue(r['forced'])
        self.assertEqual(r['firstError']['message'],'OBSERVER_ACTIVE_DEADLINE');self.assertEqual(b['trace'],b'prefix\n')

    def test_04_owned_interrupt_preserves_first_fault(self):
        r,b,_=self.capture_case('interrupt');self.assertTrue(r['forced'])
        self.assertEqual(r['firstError']['message'],'OBSERVER_INTERRUPTED');self.assertIn(int(signal.SIGINT),r['receivedSignals'])
        self.assertEqual(b['trace'],b'prefix\n')

    def test_05_trace_cap(self):
        r,b,_=self.capture_case('trace-cap');self.assertTrue(r['forced']);self.assertEqual(r['firstError']['message'],'DIAGNOSTIC_TRACE_CAP')
        self.assertEqual(len(b['trace']),1024);self.assertGreater(r['observedBytes']['trace'],1024)

    def test_06_stdout_cap(self):
        r,b,_=self.capture_case('stdout-cap');self.assertTrue(r['forced']);self.assertEqual(r['firstError']['message'],'DIAGNOSTIC_STDOUT_CAP')
        self.assertEqual(len(b['stdout']),256);self.assertGreater(r['observedBytes']['stdout'],256)

    def test_07_stderr_cap(self):
        r,b,_=self.capture_case('stderr-cap');self.assertTrue(r['forced']);self.assertEqual(r['firstError']['message'],'DIAGNOSTIC_STDERR_CAP')
        self.assertEqual(len(b['stderr']),512);self.assertGreater(r['observedBytes']['stderr'],512)

    def test_08_write_failure_before_data(self):
        r,b,c=self.capture_case('write-before','before');self.assertEqual(r['firstError']['message'],'FIXTURE_WRITE_FAILURE')
        self.assertEqual(b['trace'],b'');self.assertEqual(len(c),1);self.assertTrue(r['forced'])
        self.assertEqual(r['writeState']['trace'],'POISONED_FAILED_OR_UNCERTAIN')

    def test_09_short_positive_prefix_accounted_once(self):
        r,b,c=self.capture_case('short-positive','short-positive');self.assertEqual(r['firstError']['message'],'COMPLETE_CAPTURE_WRITE')
        self.assertEqual(r['acknowledgedWriteBytes']['trace'],128);self.assertEqual(r['retainedBytes']['trace'],128)
        self.assertEqual(b['trace'],b'P'*128);self.assertEqual(len(c),1);self.assertTrue(r['forced'])
        self.assertEqual(r['writeState']['trace'],'POISONED_FAILED_OR_UNCERTAIN');self.assertFalse(r['captureComplete'])

    def test_10_prefix_exception_accounted_by_actual_file(self):
        r,b,c=self.capture_case('prefix-exception','prefix-exception');self.assertEqual(r['firstError']['message'],'FIXTURE_PREFIX_THEN_EXCEPTION')
        self.assertEqual(r['acknowledgedWriteBytes']['trace'],0);self.assertEqual(r['retainedBytes']['trace'],128)
        self.assertEqual(b['trace'],b'P'*128);self.assertEqual(len(c),1);self.assertTrue(r['forced'])
        self.assertEqual(r['writeState']['trace'],'POISONED_FAILED_OR_UNCERTAIN');self.assertFalse(r['captureComplete'])

    def test_11_privacy_raw_read_write_and_no_attach_or_dump(self):
        m=module();out=CONTROL_ROOT/'privacy';out.mkdir(mode=0o700);m.trace_policy(list(m.TRACE_OPTIONS))
        variants=[m.TRACE_OPTIONS[:-1]+['raw=read,pread64,readv'],m.TRACE_OPTIONS+['-v'],m.TRACE_OPTIONS+['-p','1'],m.TRACE_OPTIONS+['-e','write=all']]
        for x in variants:
            with self.assertRaises(m.Refusal):m.trace_policy(x)
        save(out/'result.json',{'testedInvalidPolicies':variants,'allRefused':True,'actualTracing':False})

    def test_12_host_namespace_mismatch_is_not_normalized(self):
        m=module();out=CONTROL_ROOT/'host-context';out.mkdir(mode=0o700)
        host={'uid':1000,'gid':1000,'uidMap':'identity','gidMap':'identity','userNamespace':'host','mountNamespace':'host'}
        managed={**host,'uidMap':'managed','gidMap':'managed','userNamespace':'managed'}
        m.require_host(host,dict(host))
        with self.assertRaises(m.Refusal):m.require_host(host,managed)
        save(out/'result.json',{'hostFixture':host,'managedFixture':managed,'mismatchRefused':True,'actualHostProbe':False})

    def test_13_owned_regular_0600_guard_refuses_new_0640_fixture(self):
        m=module();out=CONTROL_ROOT/'private-mode';out.mkdir(mode=0o700)
        for name,mode in [('private',0o600),('unsafe',0o640)]:
            fd=os.open(out/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
            os.fchmod(fd,mode)  # Only this fresh owned fixture; stable under stricter umask.
            with os.fdopen(fd,'wb') as f:f.write(b'fixture\n')
        m.owned(out/'private')
        with self.assertRaises(m.Refusal):m.owned(out/'unsafe')
        save(out/'result.json',{'newPrivateAccepted':True,'newUnsafeModeRefused':True,'existingModesChanged':False})

if __name__=='__main__':
    CONTROL_ROOT.mkdir(mode=0o700,exist_ok=False);unittest.main(verbosity=2)
