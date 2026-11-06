"""New actual-request7 definitions only; zero execution in SOURCE preparation."""
import copy,hashlib,json,unittest
import qualification as q
import codec
import history_prefix as h
import test_collector as baseline
import test_history_prefix as historical

def repin(row):
 raw=q.encoded(row['request']);row['requestPin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def yielded(origin):
 terminal=copy.deepcopy(origin['launch']['unmodifiedResponse'])
 origin['launch']['unmodifiedResponse']=dict(session_id=91,output='',original_token_count=0,wall_time_seconds=0.01)
 origin['polls']=[dict(toolName='tools.write_stdin',actualArguments=dict(session_id=91,chars='',max_output_tokens=2000),unmodifiedResponse=terminal)]

class PolicyControls(unittest.TestCase):
 def setUp(self):
  self.f=baseline.CollectorControls();self.f.run='1'*32;self.run=self.f.run
 def fixture(self):return self.f._with_clean_prefix(*self.f._root_history())
 def denied(self,plan,origins):
  good,goodorigins=self.fixture();gate=q.RootFailstop(self.run)
  self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertTrue(gate.denied)
  self.assertFalse(gate.evaluate(good,goodorigins)['collectorCommandsQualified'])
 def test_actual7_direct_and_complete_same_session_yielded_accept(self):
  for asynchronous in (False,True):
   plan,origins=self.fixture();request=plan['commands'][0]['request'];self.assertEqual(set(request),set(q.REQUEST_KEYS))
   self.assertEqual(request['sandbox_permissions'],'require_escalated');self.assertTrue(request['justification'])
   if asynchronous:yielded(origins[0])
   result=q.RootFailstop(self.run).evaluate(plan,origins);self.assertTrue(result['collectorCommandsQualified']);self.assertFalse(result['fixtureOnly']);self.assertFalse(result['runtimeAuthorized'])
 def test_missing_policy_and_historical5_matching_expected_origin_refuse(self):
  for missing in (('sandbox_permissions',),('justification',),('sandbox_permissions','justification')):
   plan,origins=self.fixture();row=plan['commands'][0]
   for key in missing:del row['request'][key]
   repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request']);self.denied(plan,origins)
 def test_matching_wrong_sandbox_expected_and_origin_refuse(self):
  for wrong in ('use_default','require_escalated ',None,False,1):
   plan,origins=self.fixture();row=plan['commands'][0];row['request']['sandbox_permissions']=wrong;repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request']);self.denied(plan,origins)
 def test_matching_empty_nonstring_or_overbound_justification_refuse(self):
  for wrong in ('',' \t\n',None,False,1024,'a'*1025,'é'*513,'\ud800'):
   plan,origins=self.fixture();row=plan['commands'][0];row['request']['justification']=wrong;repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request']);self.denied(plan,origins)
 def test_utf8_bound_accepts_without_trimming_or_normalizing(self):
  for value in ('é'*512,'  bounded exact justification\n','"quoted" \\ path'):
   plan,origins=self.fixture();row=plan['commands'][0];row['request']['justification']=value;repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request']);before=q.encoded(row['request'])
   self.assertTrue(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified']);self.assertEqual(row['request']['justification'],value);self.assertEqual(q.encoded(row['request']),before)
 def test_changed_actual_policy_only_refuses_and_failstop_is_permanent(self):
  for key,value in (('sandbox_permissions','use_default'),('justification','changed actual justification')):
   plan,origins=self.fixture();origins[0]['launch']['actualArguments'][key]=value;self.denied(plan,origins)
 def test_whole_request_pin_includes_every_policy_byte(self):
  for key,value in (('sandbox_permissions','use_default'),('justification','changed expected and actual')):
   plan,origins=self.fixture();row=plan['commands'][0];row['request'][key]=value;origins[0]['launch']['actualArguments']=copy.deepcopy(row['request']);gate=q.RootFailstop(self.run);result=gate.evaluate(plan,origins)
   self.assertFalse(result['collectorCommandsQualified']);self.assertIn('EXACT_APPROVED_REQUEST_PIN',result['firstFault']);self.assertTrue(gate.denied)
 def test_unknown_extra_shell_tty_prefix_rule_and_other_keys_refuse(self):
  for key,value in (('shell','bash'),('tty',False),('prefix_rule',['python']),('extra',None)):
   plan,origins=self.fixture();row=plan['commands'][0];row['request'][key]=value;repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request']);self.denied(plan,origins)
 def test_raw7_codec_exact_roundtrip_and_policy_mutation_is_not_hidden(self):
  plan,origins=self.fixture();row=plan['commands'][0];row['request']['justification']='  Exact é "quote" \\ bytes\n';repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request'])
  raw=json.dumps(origins[0],ensure_ascii=False,indent=3).encode()+b'\n\n';path=codec.DATA+'/'+self.run+'/api-frame--actual7.gz'
  blob,index=codec.encode_api(raw,path);restored,obj=codec.restore_api(blob,index);self.assertEqual(restored,raw);self.assertEqual(obj,origins[0]);self.assertTrue(q.RootFailstop(self.run).evaluate(plan,[obj])['collectorCommandsQualified'])
  changed=copy.deepcopy(origins[0]);changed['launch']['actualArguments']['justification']+='changed';other=json.dumps(changed,ensure_ascii=False,indent=3).encode()+b'\n\n';blob,index=codec.encode_api(other,path);restored,obj=codec.restore_api(blob,index);self.assertEqual(restored,other);self.denied(plan,[obj])

class HistoryPolicyControls(unittest.TestCase):
 def setUp(self):
  self.f=historical.HistoryControls();self.f.setUp();self.run=self.f.run;self.source=self.f.source
 def test_pref_actual_policy_tamper_refuses_without_projection(self):
  for key,value in (('sandbox_permissions','use_default'),('justification','changed preF actual')):
   body,_=self.f.fixture();body['origins'][0]['launch']['actualArguments'][key]=value
   with self.assertRaises(ValueError):h.restore_prefix(self.f.frame(body),self.run,self.source)
 def test_pref_matching_wrong_policy_repin_and_unknown_extra_refuse(self):
  for key,value in (('sandbox_permissions','use_default'),('justification',''),('extra',False)):
   body,_=self.f.fixture();row=body['expectedCommands'][0];row['request'][key]=value;repin(row);body['origins'][0]['launch']['actualArguments']=copy.deepcopy(row['request'])
   with self.assertRaises(ValueError):h.freeze_prefix(body,self.run,self.source,49144)
 def test_finalf_actual_policy_tamper_permanently_denies_existing_gate(self):
  for key,value in (('sandbox_permissions','use_default'),('justification','changed F actual')):
   _,envelope=self.f.fixture();row,origin=self.f.final(envelope);bad=copy.deepcopy(origin);bad['launch']['actualArguments'][key]=value;gate=q.RootFailstop(self.run)
   self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,bad,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,gate)['collectorCommandsQualified'])
 def test_finalf_matching_wrong_policy_historical5_extra_and_stale_pin_refuse(self):
  for mutation in ('sandbox','blank','historical5','extra','stale'):
   _,envelope=self.f.fixture();row,origin=self.f.final(envelope)
   if mutation=='sandbox':row['request']['sandbox_permissions']='use_default'
   elif mutation=='blank':row['request']['justification']=''
   elif mutation=='historical5':
    del row['request']['sandbox_permissions'];del row['request']['justification']
   elif mutation=='extra':row['request']['prefix_rule']=[]
   else:row['request']['justification']='changed without repin'
   if mutation!='stale':repin(row)
   origin['launch']['actualArguments']=copy.deepcopy(row['request']);gate=q.RootFailstop(self.run);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied)
 def test_finalf_complete_yielded7_preserves_frozen_prefix_and_platform_only_witness(self):
  body,envelope=self.f.fixture();frozen=bytes(envelope);row,origin=self.f.final(envelope);yielded(origin)
  self.assertTrue(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,q.RootFailstop(self.run))['collectorCommandsQualified']);self.assertEqual(envelope,frozen);self.assertEqual(h.restore_prefix(envelope,self.run,self.source),body)
  self.assertEqual(set(row['request']),set(q.REQUEST_KEYS));self.assertNotIn(row['expectedProof']['sha256'].encode(),h.encoded(body));self.assertNotIn(q.encoded(row['request']),h.encoded(body))
 def test_new_composite_path_and_same_exact7_qualifier_required(self):
  self.assertIs(h.q,q);self.assertEqual(h.SOURCE_PATH,'/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-current-policy-20261105/source2/source-subject.json')
  body,_=self.f.fixture();old=dict(self.source,path='/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r5/source-subject.json');body['collectorSource']=old
  with self.assertRaises(ValueError):h.freeze_prefix(body,self.run,old,49144)
  for row,origin in zip(body['expectedCommands'],body['origins']):self.assertEqual(set(row['request']),set(q.REQUEST_KEYS));self.assertEqual(row['request'],origin['launch']['actualArguments'])
 def test_finite_cut_accepts_no_postf_argument_or_body_sidecar(self):
  body,envelope=self.f.fixture();row,origin=self.f.final(envelope)
  with self.assertRaises(TypeError):h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,q.RootFailstop(self.run),post_f_origins=[origin])
  for key in ('postFOrigins','Frequest','FrequestPin','FpayloadHash','Forigin','Findex','Fstatus'):
   bad=copy.deepcopy(body);bad[key]=origin
   with self.assertRaises(ValueError):h.freeze_prefix(bad,self.run,self.source,49144)
  # Omitted genuine platform history cannot be detected from supplied JSON;
  # Root concrete review must establish this was the actual full finite cut.
