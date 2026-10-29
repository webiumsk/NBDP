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

def p(name):return dict(path='/MOCK/'+name,bytes=1,sha256='a'*64)
def fixture():
 source_pin=p('metadata-overlay/subject.json');method_pin=p('capture/code-subject.json');admission_pin=p('admission/subject.json');ap=p('admission/plan.json')
 ack=dict(schema='e02-producer4-control-capture-root-ack-v1',actor='/root',executionAuthorized=True,scope='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY',producerSource=source_pin,producerSourceAcceptance=p('source/accept.json'),producerReviews=[p('source/qa'),p('source/security')],captureSource=method_pin,captureSourceAcceptance=p('capture/accept.json'),captureReviews=[p('capture/qa'),p('capture/security')],admissionPlan=ap,admissionData=admission_pin,admissionDataAcceptance=p('admission/accept.json'),admissionReviews=[p('admission/qa'),p('admission/security')],sourceBirth=p('source/lineage'),actorContext=p('source/actors'),inputManifest=p('capture/inputs'),plan=p('capture/plan'),clockSelection=p('capture/clocks'),requestContract=p('capture/request'),runtimeBindings=p('capture/runtime-bindings'),authors=['/root/mock-coordinator'],operators=['/root/mock-operator'],noRetry=True)
 testpins=[p('source4/'+n) for n in c.FILES];workers=[p('source4/worker%02d.py'%i) for i in range(22)];cfgs={'incoming':p('source4/incoming.json'),'archive':p('source4/archive.json')}
 source=dict(schema='e02-ordinary-producer4-source-subject-v1',version='SOURCE4',runtimeSourceCount=22,runtimeSources=workers,sources=testpins+workers,configurations=cfgs,modelsDefined=dict.fromkeys(c.MODEL_KEYS,2),modelsExecuted=0,helperExecutions=0,roleExecutions=0,ordinaryRowsQualified=0,runtimeReady=False,author='/root/mock-source',coordinator='/root',predecessorAuthor='/root/mock-predecessor',sourceContributors=['/root/mock-source'],controlPlan=p('overlay/control-plan'))
 control=dict(selectedJavaScriptDefinitions=[dict(file=n,expandedDefinitions=2) for n in c.FILES[:5]],pythonDefinitions=[dict(file=n,methodDefinitions=2) for n in c.FILES[5:]])
 method=dict(schema='e02-producer4-control-capture-code-subject-v1',producerSource=source_pin,codeOnly=True,authors=['/root/mock-capture'],admissionModelsDefined=3,sources=[p('capture/capture.py')])
 admission_plan=dict(caseNames=['MOCK_ONE','MOCK_TWO','MOCK_THREE'],modelsDefined=3)
 def pair(subject,decision,kind):return [dict(role=role,session='/root/mock-'+kind+'-'+role,decision=decision,subject=subject) for role in ('qa','security')]
 s=dict(schema='e02-root-current-producer4-source-acceptance-v1',actor='/root',decision=c.SOURCE_DECISION,subject=source_pin,reviews=ack['producerReviews'],modelsDefined=20,runtimeWorkerCount=22,modelsExecuted=0,helperExecutions=0,roleExecutions=0,runtimeReady=False,runtimeReleased=False,scope='EXACT_CURRENT_SOURCE_AND_CONTROL_DEFINITIONS_ONLY')
 cap=dict(schema='e02-root-producer4-capture-source-acceptance-v1',actor='/root',decision=c.CAPTURE_DECISION,subject=method_pin,reviews=ack['captureReviews'],admissionModelsDefined=3,admissionModelsExecuted=0,producerSource=source_pin,scope='EXACT_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY',executionAuthorized=False)
 a=dict(schema='e02-root-producer4-capture-admission-data-acceptance-v1',actor='/root',decision=c.ADMISSION_DECISION,subject=admission_pin,reviews=ack['admissionReviews'],captureSource=method_pin,producerSource=source_pin,admissionPlan=ap,modelsDefined=3,modelsExecuted=3,modelsPassed=3,modelsFailed=0,targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0,scope='MOCKED_CAPTURE_ADMISSION_DATA_ONLY',executionAuthorized=False)
 data=dict(schema='e02-producer4-capture-admission-data-subject-v1',authors=['/root/mock-admission-author'],operators=['/root/mock-operator'],captureSource=method_pin,producerSource=source_pin,admissionPlan=ap,execution=p('admission/execution'),originalToolOrigin=p('admission/origin'),rawArtifactManifest=p('admission/raw'),inputsBefore=p('admission/before'),inputsAfter=p('admission/after'),inputsUnchanged=True,modelsDefined=3,modelsExecuted=3,modelsPassed=3,modelsFailed=0,skipped=0,truncated=False,targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0)
 records=dict(producerAcceptance=s,captureAcceptance=cap,admissionAcceptance=a,admissionSubject=data,producerReviews=pair(source_pin,'ACCEPT_PRODUCER4_SOURCE4_AND_20_CONTROL_DEFINITIONS_ONLY','source'),captureReviews=pair(method_pin,c.CAPTURE_DECISION,'capture'),admissionReviews=pair(admission_pin,c.ADMISSION_DECISION,'admission'))
 context=dict(schema='e02-producer4-capture-current-actor-context-v1',producerSource=source_pin,captureSource=method_pin,sourceBirth=ack['sourceBirth'],participants=['/root/mock-known-source'],participantProofs=[dict(actor='/root/mock-known-source',authority=p('known/source'),selector='/author')])
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
  f=fixture();request=c.expected_request(f['plan'],'a'*64,'/MOCK/capture');self.assertEqual(set(request),set('cmd workdir login yield_time_ms max_output_tokens'.split()));self.assertIn('--signal=KILL',request['cmd']);self.assertIn('1203s',request['cmd']);self.assertNotIn('TZ=',request['cmd'])
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

if __name__=='__main__':unittest.main(verbosity=2)
