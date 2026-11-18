"""Targeted HISTORY_PREFIX pure mocked controls. No actual tool/API/FS evidence."""
import base64,copy,hashlib,json,shlex,struct,unittest,zlib
from unittest.mock import patch
import history_prefix as h
import qualification as q
import test_collector as baseline

class HistoryControls(unittest.TestCase):
 def setUp(self):
  self.run='1'*32;self.source=dict(path=h.SOURCE_PATH,bytes=20000,sha256='b'*64);self.f=baseline.CollectorControls();self.f.run=self.run
 def fixture(self):
  p,o=self.f._memory_history();p,o=self.f._with_clean_prefix(p,o)
  body=dict(schema=h.BODY_SCHEMA,runId=self.run,collectorSource=self.source,expectedCommands=p['commands'],origins=o)
  envelope=h.freeze_prefix(body,self.run,self.source,49152-8)
  return body,envelope
 def frame(self,body=None,raw=None,header_change=None,canonical_header=True):
  if raw is None:raw=h.encoded(body)
  header=dict(schema=h.HEADER_SCHEMA,purpose='HISTORY_PREFIX',runId=self.run,collectorSource=self.source,decodedBytes=len(raw),decodedSha256=hashlib.sha256(raw).hexdigest(),payloadSchema=h.BODY_SCHEMA)
  if header_change:header_change(header)
  head=h.encoded(header) if canonical_header else json.dumps(header,indent=2).encode()
  co=zlib.compressobj(9,zlib.DEFLATED,-zlib.MAX_WBITS);g=b'\x1f\x8b\x08\x00'+b'\x00'*4+b'\x02\xff'+co.compress(raw)+co.flush()+struct.pack('<II',zlib.crc32(raw)&0xffffffff,len(raw))
  return h.MAGIC+struct.pack('>I',len(head))+head+g
 def final(self,envelope):
  proof=dict(path=h.final_path(self.run),bytes=len(envelope),sha256=hashlib.sha256(envelope).hexdigest())
  row=self.f._command_row(['record','--run-id',self.run,'--kind','diagnostic','--name',h.FINAL_NAME,'--input-base64',base64.b64encode(envelope).decode()],proof)
  words,_=q.command_words(row['request']);row['request']['cmd']=shlex.join(list(q.PREFIX)+words);raw=q.encoded(row['request']);row['requestPin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  ack=dict(index=3,store='data',proof=proof,payloadUsedBytes=8+len(envelope),reservedBytes=65536,metadataOwnerBytes=8388608)
  return row,self.f._origin_ack(row,ack)
 def test_roundtrip_canonical_prefix_plus_genuine_shaped_final_root_composition(self):
  body,envelope=self.fixture();self.assertEqual(h.restore_prefix(envelope,self.run,self.source),body);self.assertEqual(envelope,h.freeze_prefix(body,self.run,self.source,49152-8))
  row,origin=self.final(envelope);result=h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,q.RootFailstop(self.run));self.assertTrue(result['collectorCommandsQualified']);self.assertFalse(result['runtimeAuthorized']);self.assertFalse(result['fixtureOnly']);self.assertNotIn(row['expectedProof']['sha256'],h.encoded(body).decode())
 def test_wrong_header_purpose_schema_run_source_and_framing_length(self):
  body,envelope=self.fixture()
  for key,value in [('purpose','OTHER'),('schema','OTHER'),('runId','2'*32),('collectorSource',dict(self.source,sha256='0'*64)),('payloadSchema','OTHER')]:
   bad=self.frame(body,header_change=lambda x,k=key,v=value:x.__setitem__(k,v))
   with self.subTest(key=key),self.assertRaises(ValueError):h.restore_prefix(bad,self.run,self.source)
  for bad in (b'BAD'+envelope,h.MAGIC+struct.pack('>I',h.HEADER_MAX+1)+b'x'*20,h.MAGIC+b'\x00',envelope[:len(h.MAGIC)+4]):
   with self.assertRaises(ValueError):h.restore_prefix(bad,self.run,self.source)
 def test_duplicate_noncanonical_and_extra_header_fields_refused(self):
  body,envelope=self.fixture();n=struct.unpack('>I',envelope[len(h.MAGIC):len(h.MAGIC)+4])[0];offset=len(h.MAGIC)+4;header=envelope[offset:offset+n];g=envelope[offset+n:]
  duplicate=header.rstrip()[:-1]+b',"purpose":"HISTORY_PREFIX"}\n';bad=h.MAGIC+struct.pack('>I',len(duplicate))+duplicate+g
  for v in (bad,self.frame(body,canonical_header=False),self.frame(body,header_change=lambda x:x.__setitem__('selfCompressedPin',{}))):
   with self.assertRaises(ValueError):h.restore_prefix(v,self.run,self.source)
 def test_single_member_crc_trailing_concatenation_and_truncation(self):
  body,envelope=self.fixture();n=struct.unpack('>I',envelope[len(h.MAGIC):len(h.MAGIC)+4])[0];offset=len(h.MAGIC)+4+n;g=envelope[offset:];corrupt=envelope[:-6]+bytes([envelope[-6]^1])+envelope[-5:]
  for bad in (envelope+b'TRAILING',envelope+g,envelope[:-1],corrupt):
   with self.assertRaises((ValueError,zlib.error)):h.restore_prefix(bad,self.run,self.source)
 def test_declared_decoded_bound_refuses_before_decompress_and_json(self):
  body,_=self.fixture();bad=self.frame(body,header_change=lambda x:x.__setitem__('decodedBytes',h.RESTORED_MAX+1))
  with patch.object(h.zlib,'decompressobj',side_effect=AssertionError('NO_DECODE')):
   with self.assertRaises(ValueError):h.restore_prefix(bad,self.run,self.source)
 def test_actual_compression_bomb_refuses_before_body_json(self):
  raw=b' '*(h.RESTORED_MAX+1);bad=self.frame(raw=raw,header_change=lambda x:x.__setitem__('decodedBytes',h.RESTORED_MAX));real=h.strict;seen=[]
  def only_header(data,*args):
   seen.append(len(data));self.assertLessEqual(len(data),h.HEADER_MAX);return real(data,*args)
  with patch.object(h,'strict',side_effect=only_header):
   with self.assertRaises(ValueError):h.restore_prefix(bad,self.run,self.source)
  self.assertEqual(len(seen),1)
 def test_exact_decoded_length_and_sha_required(self):
  body,_=self.fixture()
  for key,value in (('decodedSha256','0'*64),('decodedBytes',1),('decodedBytes',True)):
   with self.assertRaises(ValueError):h.restore_prefix(self.frame(body,header_change=lambda x,k=key,v=value:x.__setitem__(k,v)),self.run,self.source)
 def test_body_duplicate_noncanonical_unknown_and_own_hash_field_refused(self):
  body,_=self.fixture();raw=h.encoded(body);duplicate=raw.rstrip()[:-1]+b',"runId":"'+self.run.encode()+b'"}\n'
  for bad in (self.frame(raw=duplicate),self.frame(raw=json.dumps(body,indent=2).encode()),self.frame(dict(body,Frequest={})),self.frame(dict(body,FpayloadHash='0'*64))):
   with self.assertRaises(ValueError):h.restore_prefix(bad,self.run,self.source)
 def test_wrong_body_run_source_order_store_and_request_receipt_join(self):
  body,_=self.fixture()
  def wrong_store(x):
   origin=x['origins'][2];ack=json.loads(origin['launch']['unmodifiedResponse']['output']);ack['store']='data';origin['launch']['unmodifiedResponse']['output']=json.dumps(ack)+'\n'
  changes=[lambda x:x.__setitem__('runId','2'*32),lambda x:x.__setitem__('collectorSource',dict(self.source,sha256='0'*64)),lambda x:x['expectedCommands'].reverse(),lambda x:x['origins'].reverse(),wrong_store]
  for change in changes:
   bad=copy.deepcopy(body);change(bad)
   with self.assertRaises(ValueError):h.restore_prefix(self.frame(bad),self.run,self.source)
 def test_own_final_request_expected_pin_and_origin_forbidden_in_prefix(self):
  body,envelope=self.fixture();row,origin=self.final(envelope);bad=copy.deepcopy(body);bad['expectedCommands'].append(row);bad['origins'].append(origin)
  with self.assertRaises(ValueError):h.freeze_prefix(bad,self.run,self.source,49152)
  bad=copy.deepcopy(body);bad['expectedCommands'][1]['expectedProof']['path']=h.final_path(self.run)
  with self.assertRaises(ValueError):h.freeze_prefix(bad,self.run,self.source,49152)
 def test_final_witness_missing_unknown_nonzero_truncated_and_pin_substitution(self):
  _body,envelope=self.fixture();row,origin=self.final(envelope)
  changes=[lambda x:x['launch']['unmodifiedResponse'].__setitem__('exit_code',1),lambda x:x['launch']['unmodifiedResponse'].__setitem__('output_truncated',True),lambda x:x['launch']['unmodifiedResponse'].pop('original_token_count'),lambda x:x['launch']['actualArguments'].__setitem__('login',True),lambda x:x['launch']['unmodifiedResponse'].__setitem__('output','{}')]
  for change in changes:
   bad=copy.deepcopy(origin);change(bad);gate=q.RootFailstop(self.run);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,bad,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied)
  bad=copy.deepcopy(row);bad['expectedProof']['sha256']='0'*64;self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,bad,origin,q.RootFailstop(self.run))['collectorCommandsQualified'])
  self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,None,q.RootFailstop(self.run))['collectorCommandsQualified'])
 def test_final_failure_permanent_even_when_envelope_physically_complete(self):
  _body,envelope=self.fixture();row,origin=self.final(envelope);bad=copy.deepcopy(origin);bad['launch']['unmodifiedResponse']['exit_code']=2;gate=q.RootFailstop(self.run)
  self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,bad,gate)['collectorCommandsQualified']);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,gate)['collectorCommandsQualified']);self.assertGreater(len(envelope),0)
 def test_existing_root_quarantine_and_direct_fixture_cannot_authorize_final(self):
  _body,envelope=self.fixture();row,origin=self.final(envelope)
  for gate in (q.RootFailstop(self.run,previously_unqualified=True),q.RootFailstop(self.run,fixture_mode=True)):
   self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,gate)['collectorCommandsQualified'])
 def test_same_existing_remaining_slot_enforced_no_separate_index(self):
  body,envelope=self.fixture()
  for remaining in (len(envelope)-1,0,49153,True):
   with self.assertRaises(ValueError):h.freeze_prefix(body,self.run,self.source,remaining)
  self.assertIs(type(envelope),bytes);self.assertLessEqual(len(envelope)+8,49152)
