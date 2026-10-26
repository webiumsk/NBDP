"""SOURCE ONLY: modeled guard faults. No process, strace or Node is launched.

Fake proc identities/pidfds model safety ownership, not actual kernel semantics.
These regressions do not count among the7 actual pinned-strace cases.
"""
from pathlib import Path
import importlib.util,json,os,signal,subprocess,sys,types,unittest
from unittest.mock import patch,MagicMock
HERE=Path(__file__).resolve().parent
OUT=HERE/'pure-guard-actual-r1'
def module():
 spec=importlib.util.spec_from_file_location('guard_pure_fixture',HERE/'guard.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def save(name,v):
 b=(json.dumps(v,indent=2)+'\n').encode();fd=os.open(OUT/(name+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())

class GuardFaultControls(unittest.TestCase):
 def cleanup_model(self,kind):
  m=module();root=93000;pid=93001;state={'alive':True,'reaped':False};signals=[]
  row={'pid':pid,'ppid':root,'uid':os.getuid(),'starttime':123456,'session':pid,'cmdline':b'owned-synthetic-fixture\0'.hex()}
  owner=m.SafetyOwner(root,999999999999)
  handle=types.SimpleNamespace(pid=pid)
  def wait(timeout=0):
   self.assertFalse(state['alive']);self.assertFalse(state['reaped']);state['reaped']=True;return -9
  handle.wait=wait
  def census(*args):return [] if state['reaped'] else [dict(row)]
  def identity(p):
   self.assertEqual(p,pid)
   if state['reaped']:raise FileNotFoundError()
   return dict(row)
  def send(*args):
   self.assertFalse(state['reaped']);signals.append(args);state['alive']=False
  def waitid(*args):return None if state['alive'] else types.SimpleNamespace(si_pid=pid)
  def waitpid(p,flags):
   self.assertEqual(p,pid);self.assertFalse(state['alive']);state['reaped']=True;return pid,9
  def kids(p):return [pid] if p==root and not state['reaped'] else []
  pidfd_failure=OSError('SYNTHETIC_PIDFD_OPEN_FAILURE') if kind=='pidfd' else None
  with patch.object(m.subprocess,'Popen',return_value=handle),patch.object(m,'ancestry_tree',side_effect=census),\
       patch.object(m,'identity',side_effect=identity),patch.object(m,'children',side_effect=kids),\
       patch.object(m.os,'pidfd_open',side_effect=pidfd_failure,return_value=401),\
       patch.object(m.Path,'read_text',return_value='Pid:\t93001\n'),patch.object(m,'exited',side_effect=lambda fd:not state['alive']),\
       patch.object(m.signal,'pidfd_send_signal',side_effect=send),patch.object(m.os,'kill',side_effect=send),\
       patch.object(m.os,'waitid',side_effect=waitid),patch.object(m.os,'waitpid',side_effect=waitpid),\
       patch.object(m.time,'sleep',return_value=None):
   if kind=='identity':
    with patch.object(owner,'census',side_effect=ValueError('SYNTHETIC_IDENTITY_FAILURE')):
     with self.assertRaises(ValueError):owner.launch(['synthetic-owned-fixture'])
    self.assertEqual(len(owner.handles),1)
   elif kind=='unregistered':owner.census()  # Actual descendant never had any ready JSON or registration.
   else:owner.launch(['synthetic-owned-fixture'])
   self.assertTrue(owner.cleanup());self.assertTrue(owner.fallback)
  self.assertTrue(state['reaped']);self.assertGreaterEqual(len(signals),1)
  self.assertTrue(all(v['reaped'] for v in owner.known.values()))
  self.assertTrue(all(not v['registered'] for v in owner.known.values()))
  save('cleanup-'+kind,{'model':'FAKE_KERNEL_NO_LIVE_PROCESSES','initial':row,'signals':signals,'events':owner.events,
    'faults':owner.faults,'fallbackAlwaysFail':owner.fallback,'reaped':state['reaped']})

 def test_01_Popen_failure_preserves_failure_and_runs_empty_census_cleanup(self):
  m=module();owner=m.SafetyOwner(93000,999999999999)
  with patch.object(m.subprocess,'Popen',side_effect=OSError('SYNTHETIC_POPEN_FAILURE')):
   with self.assertRaises(OSError):owner.launch(['synthetic'])
  self.assertEqual(owner.handles,[])
  with patch.object(m,'ancestry_tree',return_value=[]) as census,patch.object(m,'children',return_value=[]),patch.object(m.time,'sleep',return_value=None):
   self.assertTrue(owner.cleanup());self.assertGreaterEqual(census.call_count,2)
  self.assertTrue(owner.fallback);save('popen-failure',{'noHandleReturned':True,'completeEmptyCensusCleanup':True,'alwaysFail':True})
 def test_02_pidfd_failure_retains_actual_launch_handle_and_cleanup(self):self.cleanup_model('pidfd')
 def test_03_identity_failure_afterPopen_retains_handle_and_cleanup(self):self.cleanup_model('identity')
 def test_04_unregistered_descendant_is_censused_signalled_reaped_and_FAIL(self):self.cleanup_model('unregistered')
 def test_05_ready_ACK_write_failure_does_not_discard_owner(self):
  m=module();row={'pid':93001,'starttime':123};runner=types.SimpleNamespace(pid=93001)
  held={'identity':row};owner=types.SimpleNamespace(register=MagicMock(return_value=held));registered={}
  out=MagicMock();(out.__truediv__.return_value).exists.return_value=True
  with patch.object(m,'read',return_value={'pid':93001}),patch.object(m,'identity',return_value=row),\
       patch.object(m,'put',side_effect=OSError('SYNTHETIC_ACK_WRITE_FAILURE')):
   with self.assertRaises(OSError):m.process_registrations(out,owner,runner,'deadline',registered)
  self.assertIs(registered['runner'],held);owner.register.assert_called_once()
  save('ready-write-failure',{'registeredOwnerRetainedBeforeFailedACK':True,'fallbackRequired':True})
 def test_06_missing_registration_hits_absolute_ready_cutoff(self):
  m=module()
  with self.assertRaisesRegex(ValueError,'REGISTRATION_READY_DEADLINE'):m.enforce_times(0,3.01,False,None,None)
  save('missing-registration',{'now':3.01,'ready':False,'refused':True})
 def test_07_corrupt_registration_JSON_is_refused_without_cleanup_dependency(self):
  m=module();p=OUT/'corrupt-registration.json';fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(b'{"pid":93001,"pid":93002}\n')
  with self.assertRaisesRegex(ValueError,'DUPLICATE_METADATA_KEY'):m.read(p)
  save('corrupt-refused',{'duplicateReadyJSONRefused':True,'cleanupOwnershipIndependentOfJSON':True})
 def test_08_late_registration_remains_fail_even_if_then_present(self):
  m=module()
  with self.assertRaisesRegex(ValueError,'REGISTRATION_READY_DEADLINE'):m.enforce_times(0,3.5,False,None,None)
  save('late-registration',{'lateReadyAt':3.5,'refused':True})
 def test_09_late_capture_receipt_is_fail_despite_dead_tracees(self):
  m=module()
  with self.assertRaisesRegex(ValueError,'LATE_CAPTURE_RECEIPT'):m.enforce_times(0,7.1,True,7.1,7.2)
  save('late-capture',{'receipt':7.1,'absence':7.2,'refused':True})
 def test_10_selfexpiry_belowguard_and_lateabsence_both_refused(self):
  m=module()
  with patch.object(m,'FAULT_SELF_EXPIRY_SECONDS',8):
   with self.assertRaisesRegex(ValueError,'FAULT_LIFETIME_MUST_EXCEED_WHOLE_GUARD'):m.enforce_times(0,1,True,1,None)
  with self.assertRaisesRegex(ValueError,'LATE_OWNED_ABSENCE'):m.enforce_times(0,8,True,6,8)
  save('selfexpiry',{'old8sConfigurationRefused':True,'late8sAbsenceRefused':True,'newLifetime':m.FAULT_SELF_EXPIRY_SECONDS})
 def test_11_reaped_or_reused_identity_never_signalled(self):
  m=module();owner=m.SafetyOwner(93000,999999999999)
  v={'identity':{'pid':93001,'ppid':93000,'uid':os.getuid(),'starttime':123},'fd':None,'reaped':True}
  with patch.object(m.os,'kill') as kill,patch.object(m.signal,'pidfd_send_signal') as send:
   with self.assertRaisesRegex(ValueError,'NO_POST_REAP_SIGNAL'):owner.send(v,signal.SIGKILL,'fixture')
   v['reaped']=False
   with patch.object(m,'identity',return_value={**v['identity'],'starttime':124}):
    with self.assertRaisesRegex(ValueError,'DIRECT_UNREAPED_FALLBACK_IDENTITY'):owner.send(v,signal.SIGKILL,'fixture')
   kill.assert_not_called();send.assert_not_called()
  v['fd']=401;owner.known={(93001,123):v}
  with patch.object(m,'identity',return_value={**v['identity'],'starttime':124}),patch.object(m,'exited',return_value=True),patch.object(m.os,'waitid') as waitid:
   owner.reap();waitid.assert_not_called();self.assertTrue(v['reaped'])
  save('no-reused-reaped-signals',{'bothRefused':True,'signals':0})


 def acquisition_rejection(self,kind):
  m=module();owner=m.SafetyOwner(93000,999999999999)
  row={'pid':93001,'ppid':93000,'uid':os.getuid(),'starttime':123,'session':93001,'cmdline':b'owned-fixture\0'.hex()}
  other={**row,'starttime':124} if kind=='reuse' else {**row,'uid':row['uid']+1}
  failure=OSError('SYNTHETIC_IDENTITY_EXCEPTION') if kind=='identity-exception' else ProcessLookupError('SYNTHETIC_IDENTITY_VANISHED')
  identities=[other] if kind in ('reuse','uid') else [dict(row),dict(row)]
  if kind in ('identity-exception','identity-vanished'):identities=[failure]
  fdinfo='Pid:\t-1\n' if kind=='fdinfo-mismatch' else 'Pid:\t93001\n'
  with patch.object(m,'ancestry_tree',return_value=[row]),patch.object(m.os,'pidfd_open',return_value=401),\
       patch.object(m,'identity',side_effect=identities),patch.object(m.Path,'read_text',return_value=fdinfo) as info,\
       patch.object(m.os,'close') as close,patch.object(m.signal,'pidfd_send_signal') as signal_fd,patch.object(m.os,'kill') as numeric:
   if kind=='fdinfo-exception':info.side_effect=OSError('SYNTHETIC_FDINFO_EXCEPTION')
   owner.census();held=owner.known[(93001,123)]
   self.assertIsNone(held['fd']);self.assertTrue(held['acquisitionFailed']);self.assertTrue(owner.faults)
   close.assert_called_once_with(401)
   with self.assertRaisesRegex(ValueError,'REJECTED_ACQUISITION_NOT_SIGNALABLE'):owner.send(held,signal.SIGKILL,'synthetic')
   signal_fd.assert_not_called();numeric.assert_not_called();owner.close();close.assert_called_once_with(401)
  save('acquisition-'+kind,{'model':'SYNTHETIC_NO_REAL_PROCESS','initial':row,'fdCommitted':False,'closedProvisionalExactlyOnce':True,
   'signals':0,'events':owner.events,'firstFailure':owner.faults[0]})
 def test_12_open_returned_reusedPID_descriptor_is_closed_unsignalable(self):self.acquisition_rejection('reuse')
 def test_13_open_returned_changedUID_descriptor_is_closed_unsignalable(self):self.acquisition_rejection('uid')
 def test_14_identity_exception_or_vanished_afteropen_closes_without_signal(self):
  self.acquisition_rejection('identity-exception');self.acquisition_rejection('identity-vanished')
 def test_15_fdinfo_mismatch_or_exception_closes_without_signal(self):
  self.acquisition_rejection('fdinfo-mismatch');self.acquisition_rejection('fdinfo-exception')
 def test_16_persistentcensus_failure_still_kills_reapsknown_and_staysFAIL(self):
  m=module();root=93000;pid=93001;owner=m.SafetyOwner(root,.25)
  state={'alive':True,'reaped':False,'clock':0};signals=[]
  row={'pid':pid,'ppid':root,'uid':os.getuid(),'starttime':123,'session':pid,'cmdline':b'owned-fixture\0'.hex()}
  def wait(timeout=0):
   self.assertFalse(state['alive']);self.assertFalse(state['reaped']);state['reaped']=True;return -9
  handle=types.SimpleNamespace(pid=pid,wait=wait)
  def send(fd,sig,*args):
   self.assertEqual(fd,401);self.assertFalse(state['reaped']);signals.append({'pidfd':fd,'signal':int(sig)});state['alive']=False
  def clock():state['clock']+=.01;return state['clock']
  def identity(p):
   if state['reaped']:raise FileNotFoundError()
   return dict(row)
  with patch.object(m.subprocess,'Popen',return_value=handle),patch.object(m,'ancestry_tree',return_value=[row]) as census,\
       patch.object(m,'identity',side_effect=identity),patch.object(m,'children',side_effect=lambda p:[] if state['reaped'] else [pid]),\
       patch.object(m.os,'pidfd_open',return_value=401),patch.object(m.Path,'read_text',return_value='Pid:\t93001\n'),\
       patch.object(m,'exited',side_effect=lambda fd:not state['alive']),patch.object(m.signal,'pidfd_send_signal',side_effect=send),\
       patch.object(m.os,'waitid',side_effect=lambda *a:None if state['alive'] else types.SimpleNamespace(si_pid=pid)),\
       patch.object(m.os,'kill') as numeric,patch.object(m.time,'monotonic',side_effect=clock),patch.object(m.time,'sleep',return_value=None),\
       patch.object(m.os,'close') as close:
   owner.launch(['synthetic-owned-child']);self.assertEqual(len(owner.handles),1)
   self.assertEqual(owner.known[(pid,123)]['fd'],401)
   census.side_effect=OSError('SYNTHETIC_PERSISTENT_CENSUS_FAILURE')
   self.assertFalse(owner.cleanup());self.assertTrue(owner.censusUncertain);self.assertTrue(owner.fallback)
   self.assertTrue(state['reaped']);self.assertEqual(signals,[{'pidfd':401,'signal':int(signal.SIGKILL)}]);numeric.assert_not_called()
   self.assertEqual(owner.faults[0]['message'],'SYNTHETIC_PERSISTENT_CENSUS_FAILURE')
   self.assertTrue(owner.handles[0]['reaped']);owner.close();close.assert_called_once_with(401)
  save('persistent-census-failure',{'model':'SYNTHETIC_NO_REAL_PROCESS','knownChildKilledAndReaped':True,'signals':signals,
    'completeAbsenceQualified':False,'censusUncertain':owner.censusUncertain,'fallbackAlwaysFail':owner.fallback,
    'events':owner.events,'firstFailure':owner.faults[0],'secondaryFailures':owner.faults[1:]})

if __name__=='__main__':OUT.mkdir(mode=0o700,exist_ok=False);unittest.main(verbosity=2)
