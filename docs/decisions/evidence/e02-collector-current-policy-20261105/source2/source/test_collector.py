"""Temp-FS/mocked controls defined only; future explicit Root release required.

Imports only owned collector when that future control invocation occurs.
No real project proof, tool/API/helper/container/SDK or role is invoked.
"""
import base64,copy,hashlib,io,json,os,pathlib,shlex,struct,sys,tempfile,unittest,zlib
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:
 import collector as c
 import qualification as q
 import codec
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
  request=dict(cmd=shlex.join(argv),workdir=q.SCRIPT_PIN['path'].rsplit('/',1)[0],login=False,yield_time_ms=1000,max_output_tokens=2000,sandbox_permissions='require_escalated',justification='Synthetic exact request7 collector custody control only.')
  raw=q.encoded(request);reservation=dict(path=q.DATA_PARENT+'/'+self.run+'/reservation.json',bytes=500,sha256='a'*64)
  row=dict(request=request,requestPin=dict(path='/MOCK/approved-request.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),expectedProof=reservation)
  plan=dict(schema='e02-root-collector-approved-command-sequence-v1',runId=self.run,collectorScript=q.SCRIPT_PIN,commands=[row])
  ack=dict(reservation=reservation,reservedInsideMetadataBytes=65536,metadataOwnerBytes=8388608,payloadAvailableBytes=49152,grantIssued=False)
  origin=dict(schema='e02-actual-tool-custody-v1',operator='/root',launch=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(output=json.dumps(ack)+'\n',exit_code=0,original_token_count=40,wall_time_seconds=0.01)),polls=[])
  return plan,[origin]
 def _root_denies_failed_command_forever(self,op='record',kind='lease',name='complete'):
  plan,origins=self._root_history();argv=[q.PYTHON,'-I','-B',q.SCRIPT_PIN['path'],op,'--run-id',self.run]
  if op=='record':argv+=['--kind',kind,'--name',name]
  request=dict(plan['commands'][0]['request'],cmd=shlex.join(argv));raw=q.encoded(request);expected=None if op=='status' else dict(path=q.DATA_PARENT+'/'+self.run+'/'+kind+'--'+name,bytes=0,sha256=hashlib.sha256(b'').hexdigest())
  plan['commands'].append(dict(request=request,requestPin=dict(path='/MOCK/failed-command.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),expectedProof=expected))
  failed=dict(schema='e02-actual-tool-custody-v1',operator='/root',launch=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(exit_code=1,output='MOCK_ACTUAL_BOUNDARY_FAILURE',original_token_count=12,wall_time_seconds=0.01)),polls=[]);origins.append(failed)
  gate=q.RootFailstop(self.run,fixture_mode=True);self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])
  # Even a later terminal0 receipt/structurally valid status cannot repair the
  # failed exact command sequence or Root's permanently unqualified runId.
  if op=='status':ack=dict(state='CURRENT_STRUCTURAL_CUSTODY_ONLY',historicalIO='UNKNOWN',reservedBytes=65536,ledgerPrechargedBytes=16384,payloadUsedBytes=0,recordCount=0,physicalBytes=500)
  else:ack=dict(index=1,store='data',proof=expected,payloadUsedBytes=0,reservedBytes=65536,metadataOwnerBytes=8388608)
  origins[-1]['launch']['unmodifiedResponse'].update(exit_code=0,output=json.dumps(ack)+'\n')
  self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertFalse(q.RootFailstop(self.run,previously_unqualified=True,fixture_mode=True).evaluate(plan,origins)['collectorCommandsQualified'])
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
  plan,origins=self._root_history();gate=q.RootFailstop(self.run,fixture_mode=True);self.assertTrue(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertFalse(gate.evaluate(plan,origins)['runtimeAuthorized'])
  plan,origins=self._root_history();terminal=origins[0]['launch']['unmodifiedResponse'];origins[0]['launch']['unmodifiedResponse']=dict(session_id=91,output='',original_token_count=0,wall_time_seconds=0.01);origins[0]['polls']=[dict(toolName='tools.write_stdin',actualArguments=dict(session_id=91,chars='',max_output_tokens=2000),unmodifiedResponse=terminal)]
  self.assertTrue(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,origins)['collectorCommandsQualified'])
 def test_root_missing_nonzero_truncated_unknown_wrong_request_and_poll_receipts_deny(self):
  mutations=[lambda p,o:o.clear(),lambda p,o:o[0]['launch']['unmodifiedResponse'].__setitem__('exit_code',2),lambda p,o:o[0]['launch']['unmodifiedResponse'].__setitem__('output_truncated',True),lambda p,o:o[0]['launch']['unmodifiedResponse'].pop('original_token_count'),lambda p,o:o[0]['launch'].__setitem__('actualArguments',dict(p['commands'][0]['request'],login=True)),lambda p,o:o[0]['launch']['unmodifiedResponse'].__setitem__('output','{'),lambda p,o:p['commands'][0]['requestPin'].__setitem__('sha256','0'*64)]
  for mutate in mutations:
   plan,origins=self._root_history();mutate(plan,origins)
   with self.subTest(mutation=str(mutate)):self.assertFalse(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,origins)['collectorCommandsQualified'])
  plan,origins=self._root_history();origins[0]['launch']['unmodifiedResponse']=dict(session_id=91,output='',original_token_count=0,wall_time_seconds=0.01);origins[0]['polls']=[dict(toolName='tools.write_stdin',actualArguments=dict(session_id=92),unmodifiedResponse=dict(exit_code=0,output='{}',original_token_count=1,wall_time_seconds=0.01))]
  self.assertFalse(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,origins)['collectorCommandsQualified'])
 def test_structural_status_cannot_replace_or_erase_unknown_command_custody(self):
  self.init()
  with c.Account(self.run) as a:status=c.structural_status(a)
  plan,origins=self._root_history();origins[0]['launch']['unmodifiedResponse']['output']=json.dumps(status)+'\n';gate=q.RootFailstop(self.run,fixture_mode=True);self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])
  plan,origins=self._root_history();self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])


 def _command_row(self,words,expected):
  request=dict(cmd=shlex.join([q.PYTHON,'-I','-B',q.SCRIPT_PIN['path'],*words]),workdir=q.SCRIPT_PIN['path'].rsplit('/',1)[0],login=False,yield_time_ms=1000,max_output_tokens=2000,sandbox_permissions='require_escalated',justification='Synthetic exact request7 collector custody control only.');raw=q.encoded(request)
  return dict(request=request,requestPin=dict(path='/MOCK/approved-'+str(len(raw))+'.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),expectedProof=expected)
 def _origin_ack(self,row,ack):return dict(schema='e02-actual-tool-custody-v1',operator='/root',launch=dict(toolName='tools.exec_command',actualArguments=row['request'],unmodifiedResponse=dict(output=json.dumps(ack)+'\n',exit_code=0,original_token_count=80,wall_time_seconds=0.01)),polls=[])
 def _memory_history(self):
  plan,origins=self._root_history();raw=b'GATE';digest=hashlib.sha256(raw).hexdigest();proof=dict(path=q.DATA_PARENT+'/'+self.run+'/gate--one',bytes=4,sha256=digest)
  row=self._command_row(['record','--run-id',self.run,'--kind','gate','--name','one','--input-base64',base64.b64encode(raw).decode()],proof);plan['commands'].append(row);origins.append(self._origin_ack(row,dict(index=1,store='data',proof=proof,payloadUsedBytes=4,reservedBytes=65536,metadataOwnerBytes=8388608)))
  retained=dict(path=q.REPO_PARENT+'/'+self.run+'/copy--retained',bytes=4,sha256=digest);row=self._command_row(['copy','--run-id',self.run,'--source-index','1','--store','repo','--name','retained'],retained);plan['commands'].append(row);origins.append(self._origin_ack(row,dict(index=2,store='repo',proof=retained,payloadUsedBytes=8,reservedBytes=65536,metadataOwnerBytes=8388608)))
  charge1=dict(i=1,n=4,t='data',p='gate--one',h=digest,s=None);charge2=dict(i=2,n=4,t='repo',p='copy--retained',h=digest,s=1);physical=500+8+len(q.encoded(charge1))+len(q.encoded(charge2));row=self._command_row(['status','--run-id',self.run],None);plan['commands'].append(row);origins.append(self._origin_ack(row,dict(state='CURRENT_STRUCTURAL_CUSTODY_ONLY',historicalIO='UNKNOWN',reservedBytes=65536,ledgerPrechargedBytes=16384,payloadUsedBytes=8,recordCount=2,physicalBytes=physical)))
  return plan,origins
 def _with_clean_prefix(self,plan,origins):
  plan,origins=copy.deepcopy((plan,origins))
  for row,origin in zip(plan['commands'],origins):
   row['request']['cmd']=shlex.join(list(q.PREFIX)+shlex.split(row['request']['cmd']));raw=q.encoded(row['request']);row['requestPin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());origin['launch']['actualArguments']=copy.deepcopy(row['request'])
  return plan,origins
 def test_actual_cli_base64_nonempty_memory_route_and_exact_root_qualifier(self):
  payload=b'ACTUAL_MEMORY\x00\xff';text=base64.b64encode(payload).decode();acks=[]
  def call(args):
   with patch('builtins.print',side_effect=lambda text:acks.append(json.loads(text))):c.main(args)
  call(['reserve','--run-id',self.run])
  with patch.object(c,'supplied_bytes',side_effect=AssertionError('NO_STAGING_OR_STDIN')):call(['record','--run-id',self.run,'--kind','gate','--name','memory','--input-base64',text])
  self.assertEqual((self.data/self.run/'gate--memory').read_bytes(),payload);self.assertEqual(set(p.name for p in self.base.iterdir()),{'data','repo'})
  with patch.object(q,'DATA_PARENT',str(self.data)),patch.object(q,'REPO_PARENT',str(self.repo)):
   r1=self._command_row(['reserve','--run-id',self.run],acks[0]['reservation']);r2=self._command_row(['record','--run-id',self.run,'--kind','gate','--name','memory','--input-base64',text],acks[1]['proof']);plan=dict(schema='e02-root-collector-approved-command-sequence-v1',runId=self.run,collectorScript=q.SCRIPT_PIN,commands=[r1,r2]);self.assertTrue(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,[self._origin_ack(r1,acks[0]),self._origin_ack(r2,acks[1])])['collectorCommandsQualified'])
 def test_bad_canonical_base64_refuses_before_charge_or_proof(self):
  for value in ('AB==','Zg=','Zg===','Z g==','_-==','é','Zg==\n'):
   self.run=hashlib.md5(value.encode()).hexdigest();self.init();events=[];real=c.exact_write
   with patch.object(c,'exact_write',side_effect=lambda fd,name,raw:(events.append(name),real(fd,name,raw))[1]):
    with self.assertRaises((c.Refusal,ValueError)):c.main(['record','--run-id',self.run,'--kind','gate','--name','bad','--input-base64',value])
   self.assertEqual(events,['failure.json']);self.assertFalse((self.data/self.run/'charge-01.json').exists())
 def test_base64_oversize_remaining_refuses_before_charge_and_write(self):
  self.init()
  with c.Account(self.run) as a:a.record('plan','fill',b'x'*(c.PAYLOAD-1))
  with self.assertRaises(c.Refusal):c.main(['record','--run-id',self.run,'--kind','gate','--name','over','--input-base64',base64.b64encode(b'xx').decode()])
  self.assertFalse((self.data/self.run/'charge-02.json').exists());self.assertFalse((self.data/self.run/'gate--over').exists())
 def test_actual_parser_excludes_staging_plus_base64_and_qualifier_bad_memory(self):
  with patch.object(c,'Account') as account,patch.object(c.sys,'stderr',io.StringIO()):
   with self.assertRaises(SystemExit):c.main(['record','--run-id',self.run,'--kind','gate','--name','one','--input','/MOCK/input','--input-base64','QQ=='])
   account.assert_not_called()
  plan,origins=self._memory_history();row=plan['commands'][1];words=shlex.split(row['request']['cmd']);words[-1]='AB==';row['request']['cmd']=shlex.join(words);raw=q.encoded(row['request']);row['requestPin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());origins[1]['launch']['actualArguments']=row['request'];self.assertFalse(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,origins)['collectorCommandsQualified'])
  plan,origins=self._memory_history();prefixed,receipts=self._with_clean_prefix(plan,origins);result=q.RootFailstop(run_id=self.run).evaluate(prefixed,receipts);self.assertTrue(result['collectorCommandsQualified']);self.assertFalse(result['fixtureOnly'])
  self.assertFalse(q.RootFailstop(run_id=self.run).evaluate(plan,origins)['collectorCommandsQualified']);self.assertTrue(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,origins)['fixtureOnly'])
  changes=[(0,'/bin/env'),(1,'-I'),(2,'path=/usr/bin:/bin'),(3,'LANG=C'),(4,'LC_ALL=C'),(5,'/bin/timeout'),(6,'--signal=TERM'),(7,'11s'),(7,'10S'),(8,'/usr/bin/python3')]
  for position,value in changes:
   bad,frames=self._with_clean_prefix(plan,origins);row=bad['commands'][0];words=shlex.split(row['request']['cmd']);words[position]=value;row['request']['cmd']=shlex.join(words);raw=q.encoded(row['request']);row['requestPin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());frames[0]['launch']['actualArguments']=copy.deepcopy(row['request'])
   with self.subTest(prefixPosition=position,value=value):self.assertFalse(q.RootFailstop(run_id=self.run).evaluate(bad,frames)['collectorCommandsQualified'])
  bad,frames=self._with_clean_prefix(plan,origins);row=bad['commands'][0];row['request']['workdir']='/MOCK/other';raw=q.encoded(row['request']);row['requestPin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());frames[0]['launch']['actualArguments']=copy.deepcopy(row['request']);self.assertFalse(q.RootFailstop(run_id=self.run).evaluate(bad,frames)['collectorCommandsQualified'])
 def test_all_three_closed_ack_schemas_missing_extra_substituted_pins_and_counters(self):
  plan,origins=self._memory_history();self.assertTrue(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,origins)['collectorCommandsQualified'])
  for index in (0,1,2,3):
   ack=json.loads(origins[index]['launch']['unmodifiedResponse']['output']);variants=[]
   for key in ack:
    bad=copy.deepcopy(ack);del bad[key];variants.append(bad)
   bad=copy.deepcopy(ack);bad['extra']=False;variants.append(bad)
   if index==0:
    for value in ({},dict(ack['reservation'],path='/MOCK/other'),dict(ack['reservation'],sha256='0'*64)):
     bad=copy.deepcopy(ack);bad['reservation']=value;variants.append(bad)
   elif index in (1,2):
    for value in ({},dict(ack['proof'],path='/MOCK/wrong'),dict(ack['proof'],sha256='0'*64)):
     bad=copy.deepcopy(ack);bad['proof']=value;variants.append(bad)
    for key,value in (('index',9),('store','wrong'),('payloadUsedBytes',0),('reservedBytes',True)):
     bad=copy.deepcopy(ack);bad[key]=value;variants.append(bad)
   else:
    for key in ('physicalBytes','recordCount','payloadUsedBytes'):
     bad=copy.deepcopy(ack);bad[key]+=1;variants.append(bad)
   for bad in variants:
    changed=copy.deepcopy(origins);changed[index]['launch']['unmodifiedResponse']['output']=json.dumps(bad)+'\n'
    with self.subTest(index=index,keys=sorted(bad)):self.assertFalse(q.RootFailstop(self.run,fixture_mode=True).evaluate(plan,changed)['collectorCommandsQualified'])
 def test_codec_deterministic_exact_raw_roundtrip_and_restored_root_qualification(self):
  direct,frames=self._memory_history();clean,cleanframes=self._with_clean_prefix(direct,frames)
  for plan,origins,fixture in ((direct,frames,True),(clean,cleanframes,False)):
   restored=[]
   for i,origin in enumerate(origins):
    raw=json.dumps(origin,indent=2).encode()+b'\n';path=codec.DATA+'/'+self.run+'/api-frame--origin'+str(i)+'.gz';blob,index=codec.encode_api(raw,path);self.assertEqual((blob,index),codec.encode_api(raw,path));again,obj=codec.restore_api(blob,index);self.assertEqual(again,raw);self.assertEqual(obj,origin);restored.append(obj)
   result=q.RootFailstop(run_id=self.run,fixture_mode=fixture).evaluate(plan,restored);self.assertTrue(result['collectorCommandsQualified']);self.assertEqual(result['fixtureOnly'],fixture)
 def test_codec_restore_bomb_and_declared_oversize_refuse_before_json(self):
  plan,origins=self._memory_history();raw=json.dumps(origins[0]).encode();path=codec.DATA+'/'+self.run+'/api-frame--bomb.gz';blob,index=codec.encode_api(raw,path);bad=copy.deepcopy(index);bad['restored']['bytes']=codec.RESTORED_MAX+1
  with patch.object(codec.zlib,'decompressobj',side_effect=AssertionError('BOUND_BEFORE_DECODE')):
   with self.assertRaises(ValueError):codec.restore_api(blob,bad)
  large=b' '*(codec.RESTORED_MAX+1);co=zlib.compressobj(9,zlib.DEFLATED,-zlib.MAX_WBITS);bomb=b'\x1f\x8b\x08\x00'+b'\x00'*4+b'\x02\xff'+co.compress(large)+co.flush()+struct.pack('<II',zlib.crc32(large)&0xffffffff,len(large));bad=copy.deepcopy(index);bad['compressed'].update(bytes=len(bomb),sha256=hashlib.sha256(bomb).hexdigest());bad['restored']['bytes']=codec.RESTORED_MAX
  with patch.object(codec,'origin',side_effect=AssertionError('BOMB_NEVER_JSON')):
   with self.assertRaises(ValueError):codec.restore_api(bomb,bad)
 def test_codec_hash_trailing_concatenation_truncation_and_wrong_purpose(self):
  plan,origins=self._memory_history();raw=json.dumps(origins[0]).encode();path=codec.DATA+'/'+self.run+'/api-frame--one.gz';blob,index=codec.encode_api(raw,path)
  for changed in (blob+b'TRAILING',blob+blob,blob[:-1]):
   bad=copy.deepcopy(index);bad['compressed'].update(bytes=len(changed),sha256=hashlib.sha256(changed).hexdigest())
   with self.assertRaises((ValueError,zlib.error)):codec.restore_api(changed,bad)
  for side in ('compressed','restored'):
   bad=copy.deepcopy(index);bad[side]['sha256']='0'*64
   with self.assertRaises(ValueError):codec.restore_api(blob,bad)
  bad_origin=copy.deepcopy(origins[0]);bad_origin['launch']['actualArguments']['cmd']='/usr/local/bin/node /input/probe-guard-helper.mjs'
  with self.assertRaises(ValueError):codec.encode_api(json.dumps(bad_origin).encode(),path)
  clean,frames=self._with_clean_prefix(plan,origins)
  for position,value in ((2,'PATH=/tmp'),(5,'/bin/timeout'),(6,'--signal=TERM'),(7,'11s')):
   bad_origin=copy.deepcopy(frames[0]);words=shlex.split(bad_origin['launch']['actualArguments']['cmd']);words[position]=value;bad_origin['launch']['actualArguments']['cmd']=shlex.join(words)
   with self.subTest(codecPrefixPosition=position),self.assertRaises(ValueError):codec.encode_api(json.dumps(bad_origin).encode(),path)


if __name__=='__main__':unittest.main(verbosity=2)
