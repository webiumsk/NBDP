"""MOCK definitions only. No genuine source/review/API/SDK/process evidence.

Future explicit unittest invocation is required; author does not run/import this.
"""
import copy,hashlib,json,pathlib,subprocess,sys,types,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:
 import contracts as c
 import capture
 import outputs
 import explicit_inputs as inputs
finally:sys.path.pop(0)

OBSERVATION_SOURCE_NAMES=['one-shared-cap-across-two-streams', 'exact-boundary-two-streams-acknowledged-not-physical', 'short-prefix-once-poisons-both-streams', 'zero-prefix-known-zero-throw-prefix-unknown', 'invalid-count-family-poison-no-second-write', 'closed-stream-fds-and-original-upper-bound', 'accepted-phase-writer-preserves-known-short-prefix', 'phase-then-proxy-consumes-same-budget', 'guard-once-entry-exit-and-no-action-on-refusal', 'guard-refusal-preserved-over-retention-failure', 'entry-and-success-retention-failure-prevent-action', 'callback-first-fault-and-closed-late-inert', 'upstream-send-exact-buffer-callback-and-no-extra-guard', 'proxy-send-error-kept-if-observation-sink-fails', 'proxy-intent-write-failure-never-sends', 'proxy-mutated-buffer-refuses-callback-completion', 'adapter-query-preserves-exact112-byte-operands-and-raw-join', 'adapter-raw-is-after-original-guard-before-parse', 'adapter-denied-backend-guard-context-no-raw-or-parse', 'adapter-raw-sink-fault-before-send-or-before-parse-refuses']

def p(name):return dict(path='/MOCK/'+name,bytes=1,sha256='a'*64)
def fixture():
 source_pin=p('metadata-overlay/subject.json');method_pin=p('capture/code-subject.json');admission_pin=p('admission/subject.json');ap=p('admission/plan.json')
 ack=dict(schema='e02-producer4-control-capture-root-ack-v1',actor='/root',executionAuthorized=True,scope='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY',producerSource=source_pin,producerSourceAcceptance=p('source/accept.json'),producerReviews=[p('source/qa'),p('source/security')],captureSource=method_pin,captureSourceAcceptance=p('capture/accept.json'),captureReviews=[p('capture/qa'),p('capture/security')],admissionPlan=ap,admissionData=admission_pin,admissionDataAcceptance=p('admission/accept.json'),admissionReviews=[p('admission/qa'),p('admission/security')],sourceBirth=p('source/lineage'),actorContext=p('source/actors'),inputManifest=p('capture/inputs'),plan=p('capture/plan'),clockSelection=p('capture/clocks'),requestContract=p('capture/request'),runtimeBindings=p('capture/runtime-bindings'),authors=['/root/mock-coordinator'],operators=['/root/mock-operator'],noRetry=True)
 testpins=[p('source4/'+n) for n in c.FILES];workers=[p('source4/worker%02d.py'%i) for i in range(22)];cfgs={'incoming':p('source4/incoming.json'),'archive':p('source4/archive.json')}
 source=dict(schema='e02-ordinary-producer4-source-subject-v1',version='SOURCE4',runtimeSourceCount=22,runtimeSources=workers,sources=testpins+workers,configurations=cfgs,modelsDefined=dict.fromkeys(c.MODEL_KEYS,2),modelsExecuted=0,helperExecutions=0,roleExecutions=0,ordinaryRowsQualified=0,runtimeReady=False,author='/root/mock-source',coordinator='/root',predecessorAuthor='/root/mock-predecessor',sourceContributors=['/root/mock-source'],controlPlan=p('overlay/control-plan'))
 control=dict(selectedJavaScriptDefinitions=[dict(file=n,expandedDefinitions=2) for n in c.FILES[:5]],pythonDefinitions=[dict(file=n,methodDefinitions=2) for n in c.FILES[5:]])
 known=dict(schema='e02-root-capture-known-actors-v1',actor='/root',scope='CURRENT_PRODUCER4_PURE_CONTROL_CAPTURE_AND_ADMISSION',producerSource=source_pin,knownActors=list(c.REQUIRED_KNOWN_ACTORS),provenance=p('known/provenance'),semantics='MOCK_ROOT_AUTHORITY_ONLY',sourceAccepted=False,executionAuthorized=False)
 method=dict(knownActors=c.ROOT_KNOWN_ACTORS_PIN,schema='e02-producer4-control-capture-code-subject-v1',producerSource=source_pin,codeOnly=True,authors=['/root/mock-capture'],admissionModelsDefined=3,sources=[p('capture/capture.py')])
 admission_plan=dict(caseNames=['MOCK_ONE','MOCK_TWO','MOCK_THREE'],modelsDefined=3)
 def pair(subject,decision,kind):return [dict(role=role,session='/root/mock-'+kind+'-'+role,decision=decision,subject=subject) for role in ('qa','security')]
 s=dict(schema='e02-root-current-producer4-source-acceptance-v1',actor='/root',decision=c.SOURCE_DECISION,subject=source_pin,reviews=ack['producerReviews'],modelsDefined=20,runtimeWorkerCount=22,modelsExecuted=0,helperExecutions=0,roleExecutions=0,runtimeReady=False,runtimeReleased=False,scope='EXACT_CURRENT_SOURCE_AND_CONTROL_DEFINITIONS_ONLY')
 cap=dict(schema='e02-root-producer4-capture-source-acceptance-v1',actor='/root',decision=c.CAPTURE_DECISION,subject=method_pin,reviews=ack['captureReviews'],admissionModelsDefined=3,admissionModelsExecuted=0,producerSource=source_pin,scope='EXACT_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY',executionAuthorized=False)
 a=dict(schema='e02-root-producer4-capture-admission-data-acceptance-v1',actor='/root',decision=c.ADMISSION_DECISION,subject=admission_pin,reviews=ack['admissionReviews'],captureSource=method_pin,producerSource=source_pin,admissionPlan=ap,modelsDefined=3,modelsExecuted=3,modelsPassed=3,modelsFailed=0,targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0,scope='MOCKED_CAPTURE_ADMISSION_DATA_ONLY',executionAuthorized=False)
 data=dict(schema='e02-producer4-capture-admission-data-subject-v1',authors=['/root/mock-admission-author'],operators=['/root/mock-operator'],captureSource=method_pin,producerSource=source_pin,admissionPlan=ap,execution=p('admission/execution'),originalToolOrigin=p('admission/origin'),rawArtifactManifest=p('admission/raw'),inputsBefore=p('admission/before'),inputsAfter=p('admission/after'),inputsUnchanged=True,modelsDefined=3,modelsExecuted=3,modelsPassed=3,modelsFailed=0,skipped=0,truncated=False,targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0)
 records=dict(knownActors=known,producerAcceptance=s,captureAcceptance=cap,admissionAcceptance=a,admissionSubject=data,producerReviews=pair(source_pin,'ACCEPT_PRODUCER4_SOURCE4_AND_20_CONTROL_DEFINITIONS_ONLY','source'),captureReviews=pair(method_pin,c.CAPTURE_DECISION,'capture'),admissionReviews=pair(admission_pin,c.ADMISSION_DECISION,'admission'))
 context=dict(schema='e02-producer4-capture-current-actor-context-v1',producerSource=source_pin,captureSource=method_pin,sourceBirth=ack['sourceBirth'],participants=list(c.REQUIRED_KNOWN_ACTORS)+['/root/mock-known-source'],participantProofs=[dict(actor='/root/mock-known-source',authority=p('known/source'),selector='/author')])
 tools={k:p('tools/'+k) for k in ('node','python','timeout','env')};tools['node']['path']='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node';tools['python']['path']='/home/peterhorvath/.miniforge3/bin/python3.13';tools['timeout']['path']='/usr/bin/timeout';tools['env']['path']='/usr/bin/env'
 scopes=[dict(scope=n,source=d,argv=[tools['node']['path'],d['path']] if i<5 else [tools['python']['path'],'-I','-B',d['path']],cwd='/MOCK/source4',count=2,definitionNames=['MOCK_A','MOCK_B'],format='MOCK') for i,(n,d) in enumerate(zip(c.FILES,testpins))]
 plan=dict(schema='e02-producer4-control-capture-plan-v1',readiness=True,producerSource=source_pin,captureSource=method_pin,inputManifest=ack['inputManifest'],limits=copy.deepcopy(c.LIMITS),deadlineLedger=copy.deepcopy(c.LEDGER),scopes=scopes,countsSeparate=[2]*10,tools=tools,outputRoot='/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-MOCK/capture')
 files=source['sources']+list(cfgs.values())+list(tools.values())+method['sources'];manifest=dict(schema='e02-producer4-explicit-host-input-manifest-v1',producerSource=source_pin,closedSourceSubjectKeys=sorted(source),controlPlan=source['controlPlan'],files=[dict(pin=d,mode=420,role='SOURCE',origin='MOCK') for d in files],actualInputCount=len(files))
 clock=dict(schema='e02-root-control-capture-clock-source-selection-v1',actor='/root',controllerSeconds=1200,outerKillSeconds=1203,sharedInputSnapshotPoolSeconds=480,maximumSerialScopes=10,eachScopeSeconds=60,eachOwnedTerminationReserveSeconds=3,sumSeconds=1200)
 return dict(ack=ack,source=source,control=control,method=method,admission_plan=admission_plan,records=records,context=context,plan=plan,manifest=manifest,clock=clock)
def admit(f):return c.validate_acceptances(*[f[k] for k in ('ack','source','control','method','admission_plan','records','context')])
def planned(f):return c.validate_plan(*[f[k] for k in ('plan','ack','source','control','method','manifest','clock')])

class AdmissionDefinitions(unittest.TestCase):
 def test_mock_complete_contract_and_overlay_model_cwd(self):
  f=fixture();self.assertEqual(admit(f)[0],[2]*10);planned(f)
 def test_null_unknown_and_predecessor_source_refused(self):
  for change in (lambda f:f['ack'].__setitem__('producerSource',None),lambda f:f['source'].__setitem__('schema','UNKNOWN'),lambda f:f['source'].__setitem__('version','SOURCE3')):
   f=fixture();change(f)
   with self.assertRaises((ValueError,TypeError,KeyError)):admit(f)
 def test_exact_decisions_counts_and_source_subject(self):
  for target,key,value in [('producerAcceptance','decision','HOLD'),('captureAcceptance','decision','ACCEPT_CALLER_OVERRIDE'),('admissionAcceptance','modelsPassed',2),('producerAcceptance','subject',p('wrong'))]:
   f=fixture();f['records'][target][key]=value
   with self.assertRaises(ValueError):admit(f)
 def test_full_union_closed_before_first_review_pair(self):
  f=fixture();f['records']['admissionSubject']['authors'].append(f['records']['producerReviews'][0]['session'])
  with self.assertRaises(ValueError):admit(f)
  f=fixture();f['context']['participants']=['/tmp/unknown']
  with self.assertRaises(ValueError):admit(f)
 def test_swapped_scope_file_count_missing_input_and_wrong_clocks(self):
  for change in (lambda f:f['plan']['scopes'].reverse(),lambda f:f['plan']['scopes'][0].__setitem__('count',3),lambda f:f['manifest']['files'].pop(),lambda f:f['plan']['limits'].__setitem__('childSeconds',61)):
   f=fixture();change(f)
   with self.assertRaises(ValueError):planned(f)
 def test_exact_five_key_direct_and_same_session_original_api(self):
  f=fixture();request=c.expected_request(f['plan'],'a'*64,'/MOCK/capture');self.assertEqual(set(request),set('cmd workdir login yield_time_ms max_output_tokens sandbox_permissions justification'.split()));self.assertIn('--signal=KILL',request['cmd']);self.assertIn('1203s',request['cmd']);self.assertNotIn('TZ=',request['cmd'])
  frame=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(exit_code=0,output='MOCK_ONLY'))
  origin=dict(schema='e02-actual-tool-custody-v1',operator='/root/mock-operator',launch=frame,polls=[]);c.validate_origin(origin,request,f['ack']['operators'])
  origin['launch']['unmodifiedResponse']={'session_id':77,'output':''};origin['polls']=[dict(toolName='tools.write_stdin',actualArguments={'session_id':77,'chars':''},unmodifiedResponse={'exit_code':0,'output':'MOCK_ONLY'})];c.validate_origin(origin,request,f['ack']['operators']);origin['polls'][0]['actualArguments']['session_id']=78
  with self.assertRaises(ValueError):c.validate_origin(origin,request,f['ack']['operators'])
 def test_source_parser_extra_keys_wrong_count_skip_and_missing_eof(self):
  scope=dict(scope='test_controller_emission.mjs',count=2);row=dict(exitCode=0,reaped=True,eof=dict(stdout=True,stderr=True),fault=None,groupClosure=None,groupClosureFault=None,retentionErrors=[])
  value=dict(scope='ACTUAL_PRODUCTION_CONTROLLER_EMITTER_WITH_FAKE_WRITER_ONLY',checks=2,realHelperExecuted=False,realStdoutWritten=False,clientRowsQualified=0)
  outputs.parse_outcome(scope,row,(json.dumps(value)+'\n').encode(),b'')
  for key,v in [('extra',True),('checks',3)]:
   changed=dict(value);changed[key]=v
   with self.assertRaises(ValueError):outputs.parse_outcome(scope,row,(json.dumps(changed)+'\n').encode(),b'')
  row['eof']['stderr']=False
  with self.assertRaises(ValueError):outputs.parse_outcome(scope,row,(json.dumps(value)+'\n').encode(),b'')
  row['eof']['stderr']=True;row['reaped']=False
  with self.assertRaises(ValueError):outputs.parse_outcome(scope,row,(json.dumps(value)+'\n').encode(),b'')
  row['reaped']=True
  with self.assertRaises(ValueError):outputs.parse_outcome(dict(scope='test_guard_helper.py',count=2,definitionNames=['A.a','A.b']),row,b'',b'.s\n'+b'-'*70+b'\nRan 2 tests in 0.0s\n\nOK (skipped=1)\n')
 def test_shared_snapshot480_and_full_child60_plus3_admission(self):
  now=[0];pool=capture.SnapshotPool(0,lambda:now[0]);pool.admit_child(10);now[0]=61000000000
  with self.assertRaises(ValueError):pool.admit_child(10)
  now[0]=0;pool=capture.SnapshotPool(0,lambda:now[0])
  with self.assertRaises(ValueError):pool.run(0,lambda d:now.__setitem__(0,481000000000))
 def test_one_absolute_reap_deadline_and_fault_signal_before_reap(self):
  ticks=iter([0,1000000000,2000000000]);events=[]
  class Process:
   pid=7;returncode=None
   def wait(self,timeout):
    events.append(('wait',timeout))
    if len([e for e in events if e[0]=='wait'])==1:raise subprocess.TimeoutExpired('MOCK',timeout)
    self.returncode=0;return 0
  owner=dict(ownedPopenHandle=True,startNewSession=True,pid=7,groupId=7,sessionId=7)
  with patch.object(capture.time,'monotonic_ns',side_effect=lambda:next(ticks)),patch.object(capture.os,'killpg',side_effect=lambda *a:events.append(('kill',a))):
   r=capture.finish_owned(Process(),owner,'MOCK_FAULT',10000000000)
  self.assertEqual(events[0][0],'kill');self.assertEqual([e[1] for e in events if e[0]=='wait'],[2.0,1.0]);self.assertTrue(r['reaped'])
 def test_selector_failure_never_spawns_and_shortprefix_never_repairs(self):
  with patch.object(capture,'put'),patch.object(capture.selectors,'DefaultSelector',side_effect=RuntimeError('MOCK_SELECTOR')),patch.object(capture.subprocess,'Popen') as spawn:
   with self.assertRaises(RuntimeError):capture.capture_scope(pathlib.Path('/MOCK'),{'scope':'MOCK','argv':[],'cwd':'/MOCK'},1)
   spawn.assert_not_called()
  calls=[]
  with self.assertRaises(ValueError):c.checked_write(lambda b:(calls.append(b) or len(b)-1),b'abc')
  self.assertEqual(len(calls),1)
 def test_expected_hash_before_read_result_not_self_certified_baseline(self):
  st=types.SimpleNamespace(st_dev=1,st_ino=2,st_mode=33188,st_uid=1000,st_gid=1000,st_size=4,st_mtime_ns=1,st_ctime_ns=2);fp=types.SimpleNamespace(lstat=lambda:st)
  desc=dict(path='/MOCK/file',bytes=4,sha256=hashlib.sha256(b'GOOD').hexdigest())
  with patch.object(inputs,'safe',return_value=fp),patch.object(inputs.os,'open',return_value=42),patch.object(inputs.os,'fstat',return_value=st),patch.object(inputs.os,'close'),patch.object(inputs.os,'read',side_effect=[b'EVIL',b'']),patch.object(inputs.time,'monotonic_ns',return_value=0):
   with self.assertRaises(ValueError):inputs.read_expected(desc,1000000000)
 def test_unbound_entry_refuses_before_any_target_metadata(self):
  with patch.object(capture,'load_bundle',side_effect=AssertionError('NO_TARGET_READ')):
   with self.assertRaises(ValueError):capture.main(['--execute-once','--root-ack-sha','a'*64])


 def _node_exact_and_mutations(self,name,count,value,count_key):
  scope=dict(scope=name,count=count,definitionNames=value.get('cases'))
  row=dict(exitCode=0,reaped=True,eof=dict(stdout=True,stderr=True),fault=None,groupClosure=None,groupClosureFault=None,retentionErrors=[])
  encoded=lambda v:(json.dumps(v)+'\n').encode()
  self.assertTrue(outputs.parse_outcome(scope,row,encoded(value),b'')['allOk'])
  variants=[]
  wrong=dict(value);wrong['scope']='WRONG_PREDECESSOR_SCOPE';variants.append(wrong)
  wrong=dict(value);wrong[count_key]=count+1;variants.append(wrong)
  wrong=dict(value);wrong['unapprovedExtra']=False;variants.append(wrong)
  for key in value:
   wrong=dict(value);del wrong[key];variants.append(wrong)
  for wrong in variants:
   with self.subTest(name=name,keys=sorted(wrong)),self.assertRaises((ValueError,KeyError)):outputs.parse_outcome(scope,row,encoded(wrong),b'')
 def test_exact_guard123_schema_and_mutations(self):
  self._node_exact_and_mutations('test_guard_client.mjs',129,dict(scope='PRODUCER4_MOCK_FRESH_GUARD_SCHEDULER_ONLY',definitions=129,executed=129,realHelperExecuted=False,realClockOrSDKObserved=False,clientRowsQualified=0),'definitions')
 def test_exact_registered_transport33_schema_and_mutations(self):
  self._node_exact_and_mutations('test_guard_transport_boundaries.mjs',33,dict(scope='PRODUCER4_ACTUAL_REGISTERED_HELPER_CALLBACKS_AND_OWNED_SIGNAL_MOCKS_ONLY',definitions=33,executed=33,realHelperExecuted=False,realTimerObserved=False,processReapAttested=False,clientRowsQualified=0),'definitions')
 def test_exact_allocation29_schema_and_mutations(self):
  self._node_exact_and_mutations('test_capture_allocation.mjs',29,dict(scope='PRODUCER4_PURE_CAPTURE_ALLOCATION_MODELS_ONLY',definitions=29,executed=29,realWritesObserved=False,realHelperExecuted=False,wholeConsumerQualified=False,atomicGlobalFenceClaimed=False),'definitions')
 def test_exact_controller16_schema_and_mutations(self):
  self._node_exact_and_mutations('test_controller_emission.mjs',16,dict(scope='ACTUAL_PRODUCTION_CONTROLLER_EMITTER_WITH_FAKE_WRITER_ONLY',checks=16,realHelperExecuted=False,realStdoutWritten=False,clientRowsQualified=0),'checks')
 def test_exact_observation20_schema_and_mutations(self):
  self._node_exact_and_mutations('test_observation_model.mjs',20,dict(schema='e02-producer4-observation-model-controls-v1',ok=True,checks=20,cases=OBSERVATION_SOURCE_NAMES,scope='SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME'),'checks')
 def test_each_eleven_known_helpers_rejected_in_each_six_review_slots(self):
  for actor in c.REQUIRED_KNOWN_ACTORS:
   for pair in ('producerReviews','captureReviews','admissionReviews'):
    for index in (0,1):
     f=fixture();f['records'][pair][index]['session']=actor
     with self.subTest(actor=actor,pair=pair,index=index),self.assertRaises(ValueError):admit(f)
  # Distinct nonparticipant pairs still admit through the same implementation.
  f=fixture();self.assertEqual(admit(f)[0],[2]*10)
 def test_missing_required_actor_authority_schema_and_context_refused(self):
  changes=[lambda f:f['records'].pop('knownActors'),lambda f:f['records']['knownActors'].__setitem__('schema','UNKNOWN'),lambda f:f['records']['knownActors']['knownActors'].pop(),lambda f:f['context']['participants'].remove(c.REQUIRED_KNOWN_ACTORS[-1]),lambda f:f['method'].__setitem__('knownActors',p('caller-known-authority'))]
  for change in changes:
   f=fixture();change(f)
   with self.assertRaises((ValueError,KeyError)):admit(f)
 def _actual_execute_first_fault(self,fault,bad_snapshot):
  retained={};events=[];before={'rows':['MOCK_EXPECTED_ROWS'],'memberships':[]}
  class FakePath(pathlib.PurePosixPath):
   def exists(self):return str(self) in retained
   def is_symlink(self):return False
   def is_file(self):return self.exists()
   def mkdir(self,**kw):events.append('mkdir')
   def iterdir(self):return iter(FakePath(k) for k in retained)
  class Pool:
   end=1200000000000
   def clock(self):return 1
   def run(self,n,fn):return fn(1000)
   def admit_child(self,n):events.append(('admit',n))
  f=fixture();f['plan']['outputRoot']='/MOCK/output'
  docs=dict(plan=f['plan'],inputManifest=f['manifest'],captureSource=f['method'])
  def save(root,name,value):retained[str(root/name)]=copy.deepcopy(value)
  def desc(path):return dict(path=str(path),bytes=1,sha256='a'*64)
  def fake_scope(root,scope,index):
   events.append(('scope',index))
   for suffix in ('.stdout.raw','.stderr.raw','-result.json'):save(root,'01-retained'+suffix,b'MOCK_NEGATIVE_RECEIPT')
   return dict(scope=scope['scope'],fault=fault,stdout=desc(root/'01-retained.stdout.raw'),stderr=desc(root/'01-retained.stderr.raw')),b'NEGATIVE_STDOUT',b'NEGATIVE_STDERR'
  snapshots=[before,ValueError('POST_SNAPSHOT_DRIFT')] if bad_snapshot else [before,before]
  with patch.object(capture.pathlib,'Path',FakePath),patch.object(capture,'put',side_effect=save),patch.object(capture,'descriptor',side_effect=desc),patch.object(capture,'expected_authorities',return_value=[]),patch.object(capture,'snapshot',side_effect=snapshots),patch.object(capture,'capture_scope',side_effect=fake_scope),patch.object(capture,'parse_outcome',side_effect=AssertionError('ROW_FAULT_MUST_PRECEDE_PARSER')) as parser,patch('builtins.print'):
   self.assertEqual(capture.execute(f['ack'],p('actual-ack'),docs,[2]*10,Pool(),before),2)
  result=retained['/MOCK/output/result.json'];self.assertEqual(result['firstFault'],fault);self.assertEqual(len(result['scopes']),1);self.assertEqual(len(result['remainingNotExecuted']),9);self.assertFalse(result['sourceUnchanged']);parser.assert_not_called()
  self.assertEqual([e for e in events if isinstance(e,tuple) and e[0]=='scope'],[('scope',1)])
  self.assertEqual(len(result['secondaryFaults']),1 if bad_snapshot else 0)
  if bad_snapshot:self.assertIn('POST_SNAPSHOT_DRIFT',result['secondaryFaults'][0])
  for suffix in ('.stdout.raw','.stderr.raw','-result.json'):self.assertEqual(retained['/MOCK/output/01-retained'+suffix],b'MOCK_NEGATIVE_RECEIPT')
 def test_execute_timeout_first_cause_and_post_snapshot_secondary(self):
  for bad in (False,True):
   with self.subTest(bad_snapshot=bad):self._actual_execute_first_fault('TIMEOUT',bad)
 def test_execute_retention_first_cause_and_post_snapshot_secondary(self):
  for bad in (False,True):
   with self.subTest(bad_snapshot=bad):self._actual_execute_first_fault('RETENTION_ERROR',bad)


 def _actual7_origin(self,request,yielded=False):
  frame=dict(toolName='tools.exec_command',actualArguments=copy.deepcopy(request),unmodifiedResponse=dict(exit_code=0,output='MOCK_REQUEST7'))
  origin=dict(schema='e02-actual-tool-custody-v1',operator='/root/mock-operator',launch=frame,polls=[])
  if yielded:
   frame['unmodifiedResponse']=dict(session_id=19,output='MOCK_')
   origin['polls']=[dict(toolName='tools.write_stdin',actualArguments=dict(session_id=19,chars='',yield_time_ms=1000,max_output_tokens=2000),unmodifiedResponse=dict(exit_code=0,output='REQUEST7'))]
  return origin
 def test_actual7_direct_and_yielded_keep_both_policy_fields(self):
  f=fixture();request=c.expected_request(f['plan'],'a'*64,'/MOCK/capture')
  self.assertEqual(set(request),set(c.REQUEST_KEYS));self.assertEqual(request['sandbox_permissions'],'require_escalated');self.assertEqual(request['justification'],c.REQUEST_POLICY['justification'])
  for yielded in (False,True):self.assertEqual(c.validate_origin(self._actual7_origin(request,yielded),request,f['ack']['operators']),'MOCK_REQUEST7')
 def test_actual7_missing_or_changed_policy_is_not_projected_to_five(self):
  f=fixture();expected=c.expected_request(f['plan'],'a'*64,'/MOCK/capture')
  for key in ('sandbox_permissions','justification'):
   for mutation in ('missing','changed','null'):
    request=copy.deepcopy(expected)
    if mutation=='missing':del request[key]
    else:request[key]='CHANGED_POLICY' if mutation=='changed' else None
    for yielded in (False,True):
     with self.subTest(key=key,mutation=mutation,yielded=yielded),self.assertRaises(ValueError):c.validate_origin(self._actual7_origin(request,yielded),expected,f['ack']['operators'])
    with self.assertRaises(ValueError):c.validate_origin(self._actual7_origin(request),request,f['ack']['operators'])
 def test_actual7_extra_shell_tty_prefix_and_unknown_fields_refused(self):
  f=fixture();expected=c.expected_request(f['plan'],'a'*64,'/MOCK/capture')
  for key,value in [('shell','/bin/bash'),('tty',False),('prefix_rule',['python']),('extra',False)]:
   request={**expected,key:value}
   with self.subTest(key=key),self.assertRaises(ValueError):c.validate_origin(self._actual7_origin(request),expected,f['ack']['operators'])
 def test_actual7_quoted_sha_is_refused_even_when_shell_argv_equal(self):
  import shlex
  f=fixture();sha='a'*64;expected=c.expected_request(f['plan'],sha,'/MOCK/capture');quoted=dict(expected)
  quoted['cmd']=expected['cmd'][:-len(sha)]+"'"+sha+"'"
  self.assertEqual(shlex.split(quoted['cmd']),shlex.split(expected['cmd']))
  with self.assertRaises(ValueError):c.validate_origin(self._actual7_origin(quoted),expected,f['ack']['operators'])
 def test_actual_request_from_plan_serializes_full_actual7_dictionary(self):
  import runpy
  f=fixture();fake=types.ModuleType('capture');fake.HERE=pathlib.Path('/MOCK/capture');fake.CURRENT_PRODUCER_SOURCE=f['ack']['producerSource'];fake.CURRENT_PRODUCER_ACCEPTANCE=f['ack']['producerSourceAcceptance'];fake.require_runtime_ready=lambda:None;fake.descriptor=lambda path:dict(path=str(path),bytes=1,sha256='a'*64)
  with patch.dict(sys.modules,{'capture':fake}),patch.object(inputs,'metadata',side_effect=[f['ack'],f['plan']]),patch('builtins.print') as printed:
   namespace=runpy.run_path(str(pathlib.Path(__file__).resolve().parent/'request-from-plan.py'),run_name='REQUEST_GENERATOR_MOCK_SOURCE')
   namespace['main'](['--root-ack','/MOCK/issued-ack.json'])
  value=json.loads(printed.call_args.args[0]);self.assertEqual(value,c.expected_request(f['plan'],'a'*64,'/MOCK/capture'));self.assertEqual(set(value),set(c.REQUEST_KEYS))
 def _expected_authority_fixture(self):
  import input_authority as a
  rows=[dict(pin=p('baseline/%04d'%i),mode=420,role='BASELINE_READ',origin='MOCK_DECLARATION') for i in range(2175)]
  removed=[dict(before=row) for row in rows[:6]];retained=rows[6:];extra=dict(pin=p('new/current'),mode=384,role='METADATA_AUTHORITY',origin='MOCK_CURRENT')
  side=p('new/authority.json');coverage=dict(retained=[retained[0]['pin']],current=[extra['pin']])
  baseline=dict(files=rows,actualInputCount=2175,fullTrees=['MOCK_SDK_GUARD'],nodeDependencies=['MOCK_NODE'])
  authority=dict(schema='e02-producer4-current-expected-input-authority-v1',baselineManifest=p('baseline/manifest.json'),baselineRowCount=2175,supersessions=removed,retainedRowCount=2169,retainedRowsSha256=a.retained_digest(retained),additionalRows=[extra],projectedRowCountExcludingSelf=2170,selfMode=384,coverage=coverage,wholeInputQualified=False,executionAuthorized=False)
  manifest=dict(baselineInputAuthority=authority['baselineManifest'],currentExpectedInputAuthority=side,files=retained+[extra,dict(pin=side,mode=384,role='METADATA_AUTHORITY',origin='CURRENT_FINITE_EXPECTED_INPUT_AUTHORITY')],actualInputCount=2171,requiredCoverage={**coverage,'currentExpectedInputAuthority':[side]},fullTrees=baseline['fullTrees'],nodeDependencies=baseline['nodeDependencies'])
  return a,authority,baseline,manifest
 def test_expected_authority_exact2169_projection_and_membership_preserved(self):
  a,authority,baseline,manifest=self._expected_authority_fixture();self.assertEqual(a.validate_expected_authority(authority,baseline,manifest),2171)
  for mutate in (lambda x:x['files'].pop(),lambda x:x['files'][0].__setitem__('mode',384),lambda x:x.__setitem__('nodeDependencies',['CHANGED'])):
   changed=copy.deepcopy(manifest);mutate(changed)
   with self.assertRaises(ValueError):a.validate_expected_authority(authority,baseline,changed)
 def test_expected_authority_duplicate_path_conflict_and_removed_alias_refused(self):
  a,authority,baseline,manifest=self._expected_authority_fixture()
  for row in (manifest['files'][0],baseline['files'][0],authority['additionalRows'][0]):
   changed=copy.deepcopy(authority);changed['additionalRows'].append(copy.deepcopy(row))
   with self.assertRaises(ValueError):a.validate_expected_authority(changed,baseline,manifest)
 def test_expected_authority_coverage_cannot_dangle_or_reintroduce_removed_read(self):
  a,authority,baseline,manifest=self._expected_authority_fixture()
  for pin in (p('UNKNOWN'),baseline['files'][0]['pin']):
   changed=copy.deepcopy(authority);value=copy.deepcopy(manifest);changed['coverage']['current']=[pin];value['requiredCoverage']['current']=[pin]
   with self.assertRaises(ValueError):a.validate_expected_authority(changed,baseline,value)

 def test_actual7_direct_and_yielded_argument_types_refuse_python_aliases(self):
  f=fixture();expected=c.expected_request(f['plan'],'a'*64,'/MOCK/capture')
  for key,value in [('login',0),('yield_time_ms',1000.0),('max_output_tokens',2000.0),('cmd',[]),('workdir',None)]:
   changed={**expected,key:value}
   for yielded in (False,True):
    with self.subTest(key=key,yielded=yielded),self.assertRaises(ValueError):c.validate_origin(self._actual7_origin(changed,yielded),expected,f['ack']['operators'])
  small={**expected,'yield_time_ms':1};changed={**small,'yield_time_ms':True}
  for yielded in (False,True):
   with self.assertRaises(ValueError):c.validate_origin(self._actual7_origin(changed,yielded),small,f['ack']['operators'])
 def test_poll_session_yield_token_and_chars_keep_declared_json_types(self):
  f=fixture();expected=c.expected_request(f['plan'],'a'*64,'/MOCK/capture')
  for key,value in [('session_id',19.0),('yield_time_ms',1000.0),('max_output_tokens',2000.0),('chars',None),('yield_time_ms',True)]:
   origin=self._actual7_origin(expected,True);origin['polls'][0]['actualArguments'][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):c.validate_origin(origin,expected,f['ack']['operators'])
  origin=self._actual7_origin(expected,True);origin['launch']['unmodifiedResponse']['session_id']=1;origin['polls'][0]['actualArguments']['session_id']=True
  with self.assertRaises(ValueError):c.validate_origin(origin,expected,f['ack']['operators'])
 def test_terminal_exit_and_response_session_refuse_bool_float_aliases(self):
  f=fixture();expected=c.expected_request(f['plan'],'a'*64,'/MOCK/capture')
  for yielded in (False,True):
   for value in (False,0.0):
    origin=self._actual7_origin(expected,yielded);frame=origin['polls'][-1] if yielded else origin['launch'];frame['unmodifiedResponse']['exit_code']=value
    with self.subTest(yielded=yielded,value=value),self.assertRaises(ValueError):c.validate_origin(origin,expected,f['ack']['operators'])
  origin=self._actual7_origin(expected,True);origin['polls'][0]['unmodifiedResponse']['session_id']=19.0
  with self.assertRaises(ValueError):c.validate_origin(origin,expected,f['ack']['operators'])
  origin=self._actual7_origin(expected,True);origin['launch']['unmodifiedResponse']['session_id']=1;origin['polls'][0]['actualArguments']['session_id']=1;origin['polls'][0]['unmodifiedResponse']['session_id']=True
  with self.assertRaises(ValueError):c.validate_origin(origin,expected,f['ack']['operators'])
 def test_canonical_request_and_origin_checks_leave_original_objects_unchanged(self):
  f=fixture();expected=c.expected_request(f['plan'],'a'*64,'/MOCK/capture');origin=self._actual7_origin(expected,True);before=copy.deepcopy(origin);expected_before=copy.deepcopy(expected)
  self.assertEqual(c.validate_origin(origin,expected,f['ack']['operators']),'MOCK_REQUEST7');self.assertEqual(origin,before);self.assertEqual(expected,expected_before)
  self.assertNotEqual(json.dumps({'login':False}),json.dumps({'login':0}))
  with self.assertRaises(ValueError):c.canonical_request({**expected,'login':0})


if __name__=='__main__':unittest.main(verbosity=2)
