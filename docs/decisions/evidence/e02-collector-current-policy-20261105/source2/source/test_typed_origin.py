"""SEC-01 SOURCE2 regression definitions. No actual execution is implied."""
import copy,unittest
import qualification as q
import history_prefix as h
import test_collector as baseline
import test_history_prefix as historical
from test_request_policy import repin,yielded

ALIASES=(('login',False,0),('yield_time_ms',1000,1000.0),('yield_time_ms',1,True))

class TypedOriginControls(unittest.TestCase):
 def setUp(self):
  self.f=baseline.CollectorControls();self.f.run='1'*32;self.run=self.f.run
 def fixture(self):return self.f._with_clean_prefix(*self.f._root_history())
 def alias(self,key,expected,actual,asynchronous=False):
  plan,origins=self.fixture();row=plan['commands'][0];row['request'][key]=expected;repin(row);origins[0]['launch']['actualArguments']=copy.deepcopy(row['request'])
  if asynchronous:yielded(origins[0])
  good=copy.deepcopy(origins);bad=copy.deepcopy(origins);bad[0]['launch']['actualArguments'][key]=actual
  self.assertEqual(bad[0]['launch']['actualArguments'],row['request']);self.assertNotEqual(q.encoded(bad[0]['launch']['actualArguments']),q.encoded(row['request']))
  original=q.encoded(bad);gate=q.RootFailstop(self.run);result=gate.evaluate(plan,bad);self.assertFalse(result['collectorCommandsQualified']);self.assertTrue(gate.denied);self.assertFalse(gate.evaluate(plan,good)['collectorCommandsQualified']);self.assertEqual(q.encoded(bad),original)
 def test_direct_actual_login0_against_pinned_false_refuses(self):self.alias('login',False,0)
 def test_direct_actual_yield_float_against_pinned_int_refuses(self):self.alias('yield_time_ms',1000,1000.0)
 def test_direct_actual_boolean_yield_against_pinned_int1_refuses(self):self.alias('yield_time_ms',1,True)
 def test_yielded_actual_only_type_aliases_refuse_and_failstop_permanently(self):
  for key,expected,actual in ALIASES:
   with self.subTest(key=key,actual=repr(actual)):self.alias(key,expected,actual,True)
 def test_valid_separately_copied_typed7_direct_yielded_preserves_originals(self):
  for asynchronous in (False,True):
   plan,origins=self.fixture();origins=copy.deepcopy(origins)
   if asynchronous:yielded(origins[0])
   before=q.encoded((plan,origins));result=q.RootFailstop(self.run).evaluate(plan,origins);self.assertTrue(result['collectorCommandsQualified']);self.assertFalse(result['runtimeAuthorized']);self.assertEqual(q.encoded((plan,origins)),before)
 def test_distinct_valid_actual_values_fail_whole_canonical_equality(self):
  for key,value in (('yield_time_ms',1001),('max_output_tokens',2001),('justification','changed but individually valid justification')):
   plan,origins=self.fixture();origins[0]['launch']['actualArguments'][key]=value;gate=q.RootFailstop(self.run);result=gate.evaluate(plan,origins);self.assertFalse(result['collectorCommandsQualified']);self.assertIn('EXACT_TYPED_WHOLE_PINNED_LAUNCH',result['firstFault']);self.assertTrue(gate.denied)
 def test_actual_poll_session_float_and_boolean_aliases_refuse(self):
  for expected,actual in ((91,91.0),(1,True)):
   plan,origins=self.fixture();yielded(origins[0]);origins[0]['launch']['unmodifiedResponse']['session_id']=expected;origins[0]['polls'][0]['actualArguments']['session_id']=actual;gate=q.RootFailstop(self.run)
   self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertTrue(gate.denied);origins[0]['polls'][0]['actualArguments']['session_id']=expected;self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])
 def test_actual_poll_optional_yield_requires_exact_int_without_clock_extension(self):
  for value in (1000.0,True,None,'1000'):
   plan,origins=self.fixture();yielded(origins[0]);origins[0]['polls'][0]['actualArguments']['yield_time_ms']=value;self.assertFalse(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified'])
  for value in (None,1000):
   plan,origins=self.fixture();yielded(origins[0])
   if value is not None:origins[0]['polls'][0]['actualArguments']['yield_time_ms']=value
   self.assertTrue(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified'])
 def test_actual_poll_max_tokens_retains_existing_exact_int_guard(self):
  for value in (2000.0,True,None,'2000'):
   plan,origins=self.fixture();yielded(origins[0]);poll=origins[0]['polls'][0];poll['actualArguments']['max_output_tokens']=value;poll['unmodifiedResponse']['original_token_count']=0
   self.assertFalse(q.RootFailstop(self.run).evaluate(plan,origins)['collectorCommandsQualified'])
 def test_terminal_response_session_float_boolean_aliases_refuse(self):
  for expected,actual in ((91,91.0),(1,True)):
   plan,origins=self.fixture();yielded(origins[0]);origin=origins[0];origin['launch']['unmodifiedResponse']['session_id']=expected;origin['polls'][0]['actualArguments']['session_id']=expected;origin['polls'][0]['unmodifiedResponse']['session_id']=actual;gate=q.RootFailstop(self.run)
   self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified']);self.assertTrue(gate.denied);origin['polls'][0]['unmodifiedResponse']['session_id']=expected;self.assertFalse(gate.evaluate(plan,origins)['collectorCommandsQualified'])

class HistoryTypedOriginControls(unittest.TestCase):
 def setUp(self):
  self.f=historical.HistoryControls();self.f.setUp();self.run=self.f.run;self.source=self.f.source
 def pref_alias(self,key,expected,actual):
  body,_=self.f.fixture();row=body['expectedCommands'][0];row['request'][key]=expected;repin(row);body['origins'][0]['launch']['actualArguments']=copy.deepcopy(row['request']);good=copy.deepcopy(body);body['origins'][0]['launch']['actualArguments'][key]=actual
  return good,body
 def final_alias(self,envelope,key,expected,actual,asynchronous=False):
  row,origin=self.f.final(envelope);row['request'][key]=expected;repin(row);origin['launch']['actualArguments']=copy.deepcopy(row['request'])
  if asynchronous:yielded(origin)
  good=copy.deepcopy(origin);bad=copy.deepcopy(origin);bad['launch']['actualArguments'][key]=actual
  return row,good,bad
 def test_pref_restore_actual_only_type_aliases_refuse(self):
  for key,expected,actual in ALIASES:
   good,bad=self.pref_alias(key,expected,actual);raw=h.encoded(bad)
   with self.assertRaises(ValueError):h.restore_prefix(self.f.frame(bad),self.run,self.source)
   self.assertEqual(h.encoded(bad),raw);self.assertEqual(h.restore_prefix(h.freeze_prefix(good,self.run,self.source,49144),self.run,self.source),good)
 def test_pref_alias_failure_permanently_denies_later_corrected_final_proof(self):
  for key,expected,actual in ALIASES:
   good,bad=self.pref_alias(key,expected,actual);bad_envelope=self.f.frame(bad);badrow,badorigin=self.f.final(bad_envelope);gate=q.RootFailstop(self.run)
   self.assertFalse(h.qualify_with_final_witness(bad_envelope,self.run,self.source,badrow,badorigin,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied)
   envelope=h.freeze_prefix(good,self.run,self.source,49144);row,origin=self.f.final(envelope);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,gate)['collectorCommandsQualified'])
 def test_finalf_direct_actual_only_aliases_permanently_refuse(self):
  for key,expected,actual in ALIASES:
   _,envelope=self.f.fixture();row,good,bad=self.final_alias(envelope,key,expected,actual);before=h.encoded(bad);gate=q.RootFailstop(self.run)
   self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,bad,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,good,gate)['collectorCommandsQualified']);self.assertEqual(h.encoded(bad),before)
 def test_finalf_yielded_actual_only_aliases_permanently_refuse(self):
  for key,expected,actual in ALIASES:
   _,envelope=self.f.fixture();row,good,bad=self.final_alias(envelope,key,expected,actual,True);gate=q.RootFailstop(self.run)
   self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,bad,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,good,gate)['collectorCommandsQualified'])
 def test_pref_and_finalf_poll_type_guards_reach_same_new_qualifier(self):
  for field,value in (('session_id',91.0),('yield_time_ms',1000.0),('yield_time_ms',True),('max_output_tokens',2000.0)):
   body,_=self.f.fixture();yielded(body['origins'][0]);body['origins'][0]['polls'][0]['actualArguments'][field]=value
   with self.assertRaises(ValueError):h.restore_prefix(self.f.frame(body),self.run,self.source)
   _,envelope=self.f.fixture();row,origin=self.f.final(envelope);yielded(origin);origin['polls'][0]['actualArguments'][field]=value;gate=q.RootFailstop(self.run);self.assertFalse(h.qualify_with_final_witness(envelope,self.run,self.source,row,origin,gate)['collectorCommandsQualified']);self.assertTrue(gate.denied)
