"""Temp-FS/mocked controls defined only; future explicit Root release required.

Imports only owned collector when that future control invocation occurs.
No real project proof, tool/API/helper/container/SDK or role is invoked.
"""
import copy,hashlib,json,os,pathlib,shlex,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:
 import collector as c
 import qualification as q
finally:sys.path.pop(0)

class CollectorControls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='root-custody-MOCK-');self.base=pathlib.Path(self.tmp.name);self.data=self.base/'data';self.repo=self.base/'repo';self.run='1'*32
  self.a=patch.object(c,'DATA_PARENT',self.data);self.b=patch.object(c,'REPO_PARENT',self.repo);self.a.start();self.b.start()
 def tearDown(self):self.a.stop();self.b.stop();self.tmp.cleanup()
 def init(self):return c.reserve(self.run)
 def physical(self):return sum(p.stat().st_size for root in (self.data,self.repo) for p in root.rglob('*') if p.is_file())
 def test_full_same8mib_precharge_durable_before_first_original(self):
  self.init();root=self.data/self.run;header=json.loads((root/'reservation.json').read_bytes());self.assertEqual(header['reservedBytes'],65536);self.assertEqual(header['metadataOwnerBytes'],8388608);self.assertEqual(header['ledgerPrechargeBytes'],16384);self.assertEqual(set(p.name for p in root.iterdir()),{'reservation.json'})
  events=[];real=c.exact_write
  def observed(fd,name,raw):events.append(name);return real(fd,name,raw)
  with c.Account(self.run) as account,patch.object(c,'exact_write',side_effect=observed):
   account.record('lease','one.json',b'FIRST_CONTROL_ORIGINAL')
  self.assertEqual(events,['charge-01.json','lease--one.json']);self.assertLessEqual(self.physical(),65536)
 def test_every_data_and_repository_duplicate_charged_exact_bytes(self):
  self.init();raw=b'\x00TRUE_RAW_API\n\xff'
  with c.Account(self.run) as a:
   one=a.record('api-frame','original',raw);two=a.copy(one['index'],'repo','retained');three=a.copy(one['index'],'data','duplicate');self.assertEqual(a.used,3*len(raw));self.assertEqual(two['proof']['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(three['proof']['bytes'],len(raw))
  self.assertEqual((self.repo/self.run/'copy--retained').read_bytes(),raw)
  with c.Account(self.run) as a:self.assertEqual(a.used,3*len(raw));self.assertEqual(len(a.rows),3)
 def test_exact_payload_boundary_fits_with_all_ledger_overhead(self):
  self.init()
  with c.Account(self.run) as a:a.record('plan','max',b'x'*c.PAYLOAD);self.assertEqual(a.used,49152)
  self.assertLessEqual(self.physical(),65536)
 def test_aggregate_oversize_refuses_before_charge_or_proof_open(self):
  self.init()
  with c.Account(self.run) as a:
   a.record('plan','near',b'x'*(c.PAYLOAD-1));events=[];real=c.exact_write
   with patch.object(c,'exact_write',side_effect=lambda fd,name,raw:(events.append(name),real(fd,name,raw))[1]):
    with self.assertRaises(c.Refusal):a.record('grant','over',b'xx')
   self.assertEqual(events,['failure.json']);self.assertFalse((self.data/self.run/'charge-02.json').exists());self.assertFalse((self.data/self.run/'grant--over').exists())
  self.assertLessEqual(self.physical(),65536)
 def test_failure_sticky_in_same_object_and_after_reopen(self):
  self.init()
  with c.Account(self.run) as a:
   with self.assertRaises(c.Refusal):a.record('plan','over',b'x'*(c.PAYLOAD+1))
   marker=(self.data/self.run/'failure.json').read_bytes()
   with self.assertRaises(c.Refusal):a.record('lease','later',b'')
   self.assertEqual((self.data/self.run/'failure.json').read_bytes(),marker)
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
 def test_duplicate_never_overwrites_original_or_refunds(self):
  self.init()
  with c.Account(self.run) as a:
   a.record('lease','one',b'ORIGINAL')
   with self.assertRaises(c.Refusal):a.record('lease','one',b'REPLACEMENT')
   self.assertEqual(a.used,len(b'ORIGINAL'));self.assertEqual((self.data/self.run/'lease--one').read_bytes(),b'ORIGINAL')
 def test_short_write_keeps_full_charge_and_never_repairs(self):
  self.init();real=os.write;proof_calls=[]
  with c.Account(self.run) as a:
   def short(fd,raw):
    if raw==b'CONTROL_PROOF':proof_calls.append(raw);return real(fd,raw[:3])
    return real(fd,raw)
   with patch.object(c.os,'write',side_effect=short):
    with self.assertRaises(c.Refusal):a.record('grant','short',b'CONTROL_PROOF')
   self.assertEqual(a.used,len(b'CONTROL_PROOF'));self.assertEqual(proof_calls,[b'CONTROL_PROOF']);self.assertEqual((self.data/self.run/'grant--short').read_bytes(),b'CON')
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
 def test_enospc_sticky_even_when_failure_marker_cannot_persist(self):
  self.init();real=c.exact_write
  with c.Account(self.run) as a:
   def broken(fd,name,raw):
    if name.startswith('charge-'):return real(fd,name,raw)
    raise OSError(28,'MOCK_ENOSPC')
   with patch.object(c,'exact_write',side_effect=broken):
    with self.assertRaises(OSError):a.record('diagnostic','fault',b'RAW')
   self.assertEqual(a.used,3)
  # Durable pending charge rejects on reopen even without failure.json.
  self.assertFalse((self.data/self.run/'failure.json').exists())
  with self.assertRaises(FileNotFoundError):
   with c.Account(self.run):pass
 def test_failed_charge_write_never_opens_control_original(self):
  self.init();events=[];real=c.exact_write
  with c.Account(self.run) as a:
   def broken(fd,name,raw):
    events.append(name)
    if name.startswith('charge-'):raise OSError(28,'MOCK_CHARGE_FAILURE')
    return real(fd,name,raw)
   with patch.object(c,'exact_write',side_effect=broken):
    with self.assertRaises(OSError):a.record('lease','never',b'LEASE')
   self.assertNotIn('lease--never',events);self.assertFalse((self.data/self.run/'lease--never').exists())
 def test_maximum64_records_includes_zero_byte_controls(self):
  self.init()
  with c.Account(self.run) as a:
   for i in range(64):a.record('diagnostic','zero%02d'%i,b'')
   with self.assertRaises(c.Refusal):a.record('diagnostic','sixtyfive',b'')
  self.assertLessEqual(self.physical(),65536)
 def test_path_traversal_and_unregistered_copy_refuse_without_proof(self):
  for name in ('../outside','/absolute','nested/path',''):
   with self.subTest(name=name):
    # Each rejected operation poisons its own fresh synthetic run.
    self.run=hashlib.md5(name.encode()).hexdigest();self.init()
    with c.Account(self.run) as a:
     with self.assertRaises(c.Refusal):a.record('plan',name,b'RAW')
    self.assertFalse((self.data/self.run/'charge-01.json').exists())
  self.run='f'*32;self.init()
  with c.Account(self.run) as a:
   with self.assertRaises(c.Refusal):a.copy(1,'repo','foreign')
 def test_file_symlink_and_unaccounted_file_refuse(self):
  self.init();outside=self.base/'outside';outside.write_bytes(b'UNTOUCHED');os.symlink(outside,self.data/self.run/'lease--trap')
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
  self.assertEqual(outside.read_bytes(),b'UNTOUCHED')
 def test_root_permissions_and_identity_swap_refuse(self):
  self.init();os.chmod(self.repo/self.run,0o755)
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
  os.chmod(self.repo/self.run,0o700)
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
  self.run='3'*32;self.init()
  with c.Account(self.run) as a:
   root=self.repo/self.run;root.rename(self.repo/'detached');root.mkdir(mode=0o700)
   with self.assertRaises(c.Refusal):a.record('plan','mustnotwrite',b'RAW')
   self.assertFalse((self.data/self.run/'charge-01.json').exists());self.assertEqual(list(root.iterdir()),[])
 def test_changed_registered_proof_or_account_contract_refuse(self):
  self.init()
  with c.Account(self.run) as a:a.record('api-request','one',b'ORIGINAL')
  (self.data/self.run/'api-request--one').write_bytes(b'CHANGED')
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
  self.run='2'*32;self.init();p=self.data/self.run/'reservation.json';h=json.loads(p.read_bytes());h['reservedBytes']=65537;p.write_bytes(c.raw_json(h))
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
 def test_copy_cannot_bypass_budget_with_equal_digest_or_second_store(self):
  self.init()
  with c.Account(self.run) as a:
   r=a.record('api-frame','halfplus',b'x'*(c.PAYLOAD//2+1))
   with self.assertRaises(c.Refusal):a.copy(r['index'],'repo','samebytes')
   self.assertFalse((self.repo/self.run/'copy--samebytes').exists());self.assertEqual(a.used,c.PAYLOAD//2+1)
 def test_supplied_readonly_file_exact_bytes_and_size_bound(self):
  p=self.base/'supplied';p.write_bytes(b'OPAQUE\x00\xff');self.assertEqual(c.supplied_bytes(str(p),8),b'OPAQUE\x00\xff')
  with self.assertRaises(c.Refusal):c.supplied_bytes(str(p),7)
  q=self.base/'link';q.symlink_to(p)
  with self.assertRaises(c.Refusal):c.supplied_bytes(str(q),8)
 def test_extra_file_between_operations_refuses_before_next_proof(self):
  self.init()
  with c.Account(self.run) as a:
   a.record('gate','first',b'FIRST')
   extra=self.repo/self.run/'unregistered';extra.write_bytes(b'FOREIGN')
   with self.assertRaises(c.Refusal):a.record('lease','next',b'LEASE')
   self.assertFalse((self.data/self.run/'charge-02.json').exists());self.assertFalse((self.data/self.run/'lease--next').exists())
 def test_registered_proof_hardlink_alias_refuses(self):
  self.init()
  with c.Account(self.run) as a:a.record('gate','one',b'GATE')
  os.link(self.data/self.run/'gate--one',self.base/'unaccounted-alias')
  with self.assertRaises(c.Refusal):
   with c.Account(self.run):pass
 def test_one_use_reservation_never_resets_ledger(self):
  self.init();before=(self.data/self.run/'reservation.json').read_bytes()
  with self.assertRaises(c.Refusal):self.init()
  self.assertEqual((self.data/self.run/'reservation.json').read_bytes(),before)
 def test_readonly_status_accounts_all_physical_original_copy_ledger_bytes(self):
  self.init()
  with c.Account(self.run) as a:
   r=a.record('gate','one',b'GATE');a.copy(r['index'],'repo','same')
  paths=c.run_paths(self.run);actual=sum(p.stat().st_size for root in paths.values() for p in root.iterdir());self.assertEqual(actual,self.physical());self.assertLessEqual(actual,65536)
  with c.Account(self.run) as a:
   self.assertEqual(a.used,8);self.assertEqual(a.header['ledgerPrechargeBytes']+a.used,16392);status=c.structural_status(a);self.assertEqual(status['state'],'CURRENT_STRUCTURAL_CUSTODY_ONLY');self.assertEqual(status['historicalIO'],'UNKNOWN');self.assertNotIn('failed',status)


 def _root_history(self):
  argv=[q.PYTHON,'-I','-B',q.SCRIPT_PIN['path'],'reserve','--run-id',self.run]
  request=dict(cmd=shlex.join(argv),workdir=q.SCRIPT_PIN['path'].rsplit('/',1)[0],login=False,yield_time_ms=1000,max_output_tokens=2000)
  raw=q.encoded(request);row=dict(request=request,requestPin=dict(path='/MOCK/approved-request.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
  plan=dict(schema='e02-root-collector-approved-command-sequence-v1',runId=self.run,collectorScript=q.SCRIPT_PIN,commands=[row])
  ack=dict(reservedInsideMetadataBytes=65536,metadataOwnerBytes=8388608,payloadAvailableBytes=49152,grantIssued=False)
  origin=dict(schema='e02-actual-tool-custody-v1',operator='/root',launch=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(output=json.dumps(ack)+'\n',exit_code=0,original_token_count=40,wall_time_seconds=0.01)),polls=[])
  return plan,[origin]
 def _root_denies_failed_command_forever(self,op='record',kind='lease',name='complete'):
  plan,origins=self._root_history();argv=[q.PYTHON,'-I','-B',q.SCRIPT_PIN['path'],op,'--run-id',self.run]
  if op=='record':argv+=['--kind',kind,'--name',name]
  request=dict(plan['commands'][0]['request'],cmd=shlex.join(argv));raw=q.encoded(request);plan['commands'].append(dict(request=request,requestPin=dict(path='/MOCK/failed-command.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
  failed=dict(schema='e02-actual-tool-custody-v1',operator='/root',launch=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(exit_code=1,output='MOCK_ACTUAL_BOUNDARY_FAILURE',original_token_count=12,wall_time_seconds=0.01)),polls=[]);origins.append(failed)
  gate=q.RootFailstop(self.run);self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])
  # Even a later terminal0 receipt/structurally valid status cannot repair the
  # failed exact command sequence or Root's permanently unqualified runId.
  if op=='status':ack=dict(state='CURRENT_STRUCTURAL_CUSTODY_ONLY',historicalIO='UNKNOWN')
  else:ack=dict(index=1,proof={},payloadUsedBytes=20,reservedBytes=65536,metadataOwnerBytes=8388608)
  origins[-1]['launch']['unmodifiedResponse'].update(exit_code=0,output=json.dumps(ack)+'\n')
  self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertFalse(q.RootFailstop(self.run,previously_unqualified=True).evaluate(plan,origins)['collectorCommandsQualified'])
 def _lost_postwrite_error(self,stage):
  self.init();real_exact=c.exact_write;real_open=os.open;real_write=os.write;real_fsync=os.fsync;real_close=os.close;real_fstat=os.fstat;names={};written=set()
  def opening(name,*args,**kw):
   fd=real_open(name,*args,**kw);names[fd]=name;written.discard(fd);return fd
  def writing(fd,raw):
   n=real_write(fd,raw);written.add(fd);return n
  def syncing(fd):
   if stage=='fsync' and names.get(fd)=='lease--complete' and fd in written:raise OSError('MOCK_AFTER_FULL_WRITE_FSYNC')
   return real_fsync(fd)
  def closing(fd):
   name=names.pop(fd,None);was=fd in written;written.discard(fd);real_close(fd)
   if stage=='close' and name=='lease--complete' and was:raise OSError('MOCK_AFTER_FULL_WRITE_CLOSE')
  def checking(fd):
   if stage=='postcheck' and names.get(fd)=='lease--complete' and fd in written:raise OSError('MOCK_AFTER_FULL_WRITE_POSTCHECK')
   return real_fstat(fd)
  def exact(fd,name,raw):
   if name=='failure.json':raise OSError('MOCK_MARKER_UNAVAILABLE')
   return real_exact(fd,name,raw)
  with c.Account(self.run) as a:
   with patch.object(c.os,'open',side_effect=opening),patch.object(c.os,'write',side_effect=writing),patch.object(c.os,'fsync',side_effect=syncing),patch.object(c.os,'close',side_effect=closing),patch.object(c.os,'fstat',side_effect=checking),patch.object(c,'exact_write',side_effect=exact):
    with self.assertRaises(OSError):a.record('lease','complete',b'COMPLETE_PROOF_BYTES')
    self.assertIsNotNone(a.failed);self.assertEqual(a.used,len(b'COMPLETE_PROOF_BYTES'))
   self.assertFalse((self.data/self.run/'failure.json').exists())
  # Full expected bytes/charge can reopen structurally; that is the preserved
  # R1 counterexample, not permission to restore command history or runtime.
  with c.Account(self.run) as a:
   result=c.structural_status(a);self.assertEqual(result['state'],'CURRENT_STRUCTURAL_CUSTODY_ONLY');self.assertEqual(result['historicalIO'],'UNKNOWN');self.assertNotIn('failed',result)
  self._root_denies_failed_command_forever()
 def test_full_write_then_fsync_fault_marker_unavailable_is_history_unknown(self):self._lost_postwrite_error('fsync')
 def test_full_write_then_close_fault_marker_unavailable_is_history_unknown(self):self._lost_postwrite_error('close')
 def test_full_write_then_postcheck_fault_marker_unavailable_is_history_unknown(self):self._lost_postwrite_error('postcheck')
 def test_precharge_open_and_marker_failure_cannot_be_requalified_by_status(self):
  self.init();real_open=os.open;real_exact=c.exact_write
  def opening(name,*args,**kw):
   if name=='charge-01.json':raise OSError('MOCK_CHARGE_OPEN_FAILURE')
   return real_open(name,*args,**kw)
  def exact(fd,name,raw):
   if name=='failure.json':raise OSError('MOCK_MARKER_UNAVAILABLE')
   return real_exact(fd,name,raw)
  with c.Account(self.run) as a:
   with patch.object(c.os,'open',side_effect=opening),patch.object(c,'exact_write',side_effect=exact):
    with self.assertRaises(OSError):a.record('plan','unwritten',b'PLAN')
   self.assertIsNotNone(a.failed);self.assertEqual(a.used,0)
  with c.Account(self.run) as a:self.assertEqual(c.structural_status(a)['historicalIO'],'UNKNOWN')
  self._root_denies_failed_command_forever(kind='plan',name='unwritten')
 def test_output_acknowledgement_failure_is_root_failstop_even_after_clean_close(self):
  self.init()
  with patch('builtins.print',side_effect=BrokenPipeError('MOCK_ACK_FAILURE')):
   with self.assertRaises(BrokenPipeError):c.main(['status','--run-id',self.run])
  with c.Account(self.run) as a:self.assertEqual(c.structural_status(a)['historicalIO'],'UNKNOWN')
  self._root_denies_failed_command_forever(op='status')
 def test_root_pure_predicate_accepts_complete_direct_and_same_session_mock_custody(self):
  plan,origins=self._root_history();gate=q.RootFailstop(self.run);self.assertTrue(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertFalse(gate.evaluate(plan,origins)['runtimeAuthorized'])
  plan,origins=self._root_history();terminal=origins[0]['launch']['unmodifiedResponse'];origins[0]['launch']['unmodifiedResponse']=dict(session_id=91,output='',original_token_count=0,wall_time_seconds=0.01);origins[0]['polls']=[dict(toolName='tools.write_stdin',actualArguments=dict(session_id=91,chars='',max_output_tokens=2000),unmodifiedResponse=terminal)]
  self.assertTrue(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified'])
 def test_root_missing_nonzero_truncated_unknown_wrong_request_and_poll_receipts_deny(self):
  mutations=[lambda p,o:o.clear(),lambda p,o:o[0]['launch']['unmodifiedResponse'].__setitem__('exit_code',2),lambda p,o:o[0]['launch']['unmodifiedResponse'].__setitem__('output_truncated',True),lambda p,o:o[0]['launch']['unmodifiedResponse'].pop('original_token_count'),lambda p,o:o[0]['launch'].__setitem__('actualArguments',dict(p['commands'][0]['request'],login=True)),lambda p,o:o[0]['launch']['unmodifiedResponse'].__setitem__('output','{'),lambda p,o:p['commands'][0]['requestPin'].__setitem__('sha256','0'*64)]
  for mutate in mutations:
   plan,origins=self._root_history();mutate(plan,origins)
   with self.subTest(mutation=str(mutate)):self.assertFalse(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified'])
  plan,origins=self._root_history();origins[0]['launch']['unmodifiedResponse']=dict(session_id=91,output='',original_token_count=0,wall_time_seconds=0.01);origins[0]['polls']=[dict(toolName='tools.write_stdin',actualArguments=dict(session_id=92),unmodifiedResponse=dict(exit_code=0,output='{}',original_token_count=1,wall_time_seconds=0.01))]
  self.assertFalse(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified'])
 def test_structural_status_cannot_replace_or_erase_unknown_command_custody(self):
  self.init()
  with c.Account(self.run) as a:status=c.structural_status(a)
  plan,origins=self._root_history();origins[0]['launch']['unmodifiedResponse']['output']=json.dumps(status)+'\n';gate=q.RootFailstop(self.run);self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])
  plan,origins=self._root_history();self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])

if __name__=='__main__':unittest.main(verbosity=2)
