"""Temp-FS/mocked controls defined only; future explicit Root release required.

Imports only owned collector when that future control invocation occurs.
No real project proof, tool/API/helper/container/SDK or role is invoked.
"""
import hashlib,json,os,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:import collector as c
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
  with c.Account(self.run) as a:self.assertEqual(a.used,8);self.assertEqual(a.header['ledgerPrechargeBytes']+a.used,16392)

if __name__=='__main__':unittest.main(verbosity=2)
