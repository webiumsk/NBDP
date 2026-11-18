"""SOURCE2-only stdlib preparation. Never imports or executes project targets."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EXPECTED=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-current-policy-20261105/source2')
PRE=ROOT.with_name('source1')
EVIDENCE=ROOT.parents[1]
REV=EVIDENCE/'e02-collector-current-policy-review-20261105'
SCOPE=EVIDENCE/'e02-goal-resume-20261104/collector-policy-source2-root-scope-20261105.json'
BASE=Path('/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r5')
ACTOR='/root/helper_policy_source7'
DIAGNOSIS='/root/collector_policy_security_553c5bfd'

def pin(path):
 raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(name,data):
 path=ROOT/name;assert path.is_relative_to(ROOT);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data.encode() if isinstance(data,str) else data);return pin(path)
def save(name,value):return write(name,json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def once(text,old,new):
 assert text.count(old)==1,old
 return text.replace(old,new)
def methods(text):
 tree=ast.parse(text)
 return {c.name+'.'+f.name:ast.dump(f,include_attributes=False) for c in tree.body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')}
def functions(text):
 return {f.name:ast.dump(f,include_attributes=False) for f in ast.parse(text).body if isinstance(f,(ast.FunctionDef,ast.ClassDef))}

TYPED_TESTS=r'''"""SEC-01 SOURCE2 regression definitions. No actual execution is implied."""
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
'''

CONTRACT='''# Collector actual-request7 SOURCE2 typed-origin remediation

Source1 is immutable and unaccepted. Its independent QA positive verdict and
security HOLD remain preserved. SEC-01 found Python equality aliases JSON false
with0 and int with float/bool. Source1's launch comparison checked args==expected
without validating the separately copied actual request. Those are distinct raw
JSON values and must not qualify complete expected/actual custody.

Source2 validates BOTH the full expected and full actual launch with the same
command() validator, including its closed seven keys, strict login/numeric types,
fixed policy, UTF8 bound, exact pinned CLI and existing operation rules. It then
compares the whole canonical encoded requests, preserving JSON type distinctions.
Neither raw origins nor request values are changed, normalized or projected.
The canonical expected requestPin remains a separate preexisting Root check.

Polls retain exactly the old permitted fieldset/session/empty-chars route. Actual
poll session_id now requires exact positive int before same-session equality.
Optional yield_time_ms requires exact int; omission still uses the existing API
default and no numeric wait limit or operational clock is increased. Poll max
output tokens retains the existing exact-int/count-cap guard. Optional terminal
response session_id, when non-null, requires exact int plus the same session;
this closes the analogous float/bool alias. Running response sessions were already
strict positive ints. Complete launch/allpoll/session/terminal0/truncation checks
and permanent runId failstop remain. None of this authenticates supplied origins.

The Source2 composite uses its own source-subject.json absolute path and external
whole bytes/hash. History imports the same Source2 qualifier; no old qualifier or
old Source pin is selected. No self-hash cycle is introduced. All Source1 66 named
controls remain semantically preserved. All original50 named method bodies stay
AST-identical; one later Source-path assertion necessarily changes source1 to
source2. Added definitions use separately copied actualArguments and cover the
three diagnosed aliases in direct/yielded/preF/finalF/permanent-failstop paths,
poll and response session types and valid unchanged inputs. Actual current count
is statically derived; none of the controls has run and no historical result moves.

Unchanged R4 operational collector CLI, local collector, codec and account/ledger
engines remain pinned. Seven API keys/fixed require_escalated/nonblank1..1024 UTF8
justification remain. Whole raw policy values stay in expected/actual history;
metadata never enters Docker argv/env. Existing65536 physical/16384 ledger/49152
payload/64 writes/10s limits and all charged duplicates remain. Request-growth
and Base64 formulas are retained conservatively; no compressed or whole fit is
asserted. There is no added operation/write/slot/sidecar solely from request shape.

Prefix/envelope freeze precedes deriving F request/pin/hash/origin. F members are
excluded from prefix. F's complete actual launch/allpoll/terminal0 remains solely
the genuine platform witness; no physical own-F origin/index/status/copy/CLI or
rescue after F is allowed. Same remaining slot and existing actual RootFailstop
are mandatory. Root concrete review must establish the actual full finite cut
and permanent quarantine; supplied JSON cannot detect omitted later platform calls.

Source2 grants no current Source/DATA acceptance, controls, lease, identity,
helper/role runtime or release and binds no unissued final component acceptance.
Independent QA and security reviewers must be born after freeze and exclude all
current contributors including the SEC-01 diagnosis contributor. Fresh reviewed
whole Source and separately released complete current controls/DATA precede
current controller/helper/consumer successors, concrete full-chain fit and one-use
Root runtime release. Source1/HOLD and all earlier failures remain retained. E02
stays PARTIAL22; no Q06/Q24 or Q01/Q08/Q13/Q15/Q27 gate is closed here.
'''

def main():
 assert ROOT==EXPECTED
 scope=json.loads(SCOPE.read_bytes());assert scope['actor']=='/root' and scope['ownedRoot']==str(ROOT) and scope['modelExecutionAuthorized'] is False
 before=[pin(p) for p in sorted(PRE.rglob('*')) if p.is_file()];assert len(before)==30
 review_before=[pin(p) for p in sorted(REV.glob('*.json'))]
 negative=json.loads((REV/'security-findings.json').read_bytes());assert negative['reviewer']==DIAGNOSIS and negative['finding']['id']=='SEC-01'
 disposition=json.loads((REV/'source1-disposition.json').read_bytes());assert disposition['source1Accepted'] is False
 for p in sorted((PRE/'source').glob('*.py')):write('source/'+p.name,p.read_bytes())
 source=ROOT/'source'
 qual=(source/'qualification.py').read_text()
 qual=once(qual,"  if i==0:need(frame['toolName']=='tools.exec_command' and args==expected,'EXACT_PINNED_LAUNCH')", "  if i==0:\n   need(frame['toolName']=='tools.exec_command','EXACT_PINNED_LAUNCH')\n   expected_words,_route=command_words(expected);need(len(expected_words)>=7,'COMPLETE_PINNED_EXPECTED_REQUEST')\n   command(expected,expected_words[6]);command(args,expected_words[6])\n   need(encoded(args)==encoded(expected),'EXACT_TYPED_WHOLE_PINNED_LAUNCH')")
 qual=once(qual,"and args.get('session_id')==session and args.get('chars','')==''", "and type(args.get('session_id')) is int and args['session_id']>0 and args['session_id']==session and args.get('chars','')=='' and ('yield_time_ms' not in args or type(args['yield_time_ms']) is int)")
 qual=once(qual,"or response['session_id']==session),'ACTUAL_TERMINAL0'", "or (type(response['session_id']) is int and response['session_id']==session)),'ACTUAL_TERMINAL0'")
 write('source/qualification.py',qual)
 hist=(source/'history_prefix.py').read_text();hist=once(hist,str(PRE/'source-subject.json'),str(ROOT/'source-subject.json'));write('source/history_prefix.py',hist)
 policy=(source/'test_request_policy.py').read_text();policy=once(policy,str(PRE/'source-subject.json'),str(ROOT/'source-subject.json'));write('source/test_request_policy.py',policy)
 write('source/test_typed_origin.py',TYPED_TESTS)
 oldnames={};original50={};groups=[];names=[];changed_old_methods=[]
 for p in sorted((PRE/'source').glob('test_*.py')):
  old=methods(p.read_bytes());new=methods((source/p.name).read_bytes())
  assert methods(p.read_text().replace(str(PRE/'source-subject.json'),str(ROOT/'source-subject.json')))==new
  oldnames.update(old)
  changed_old_methods.extend(name for name in old if old[name]!=new[name])
 for name in ('test_collector.py','test_history_prefix.py'):
  old=methods((BASE/name).read_bytes());assert old==methods((source/name).read_bytes());original50.update(old)
 assert len(original50)==50 and len(oldnames)==66 and changed_old_methods==['HistoryPolicyControls.test_new_composite_path_and_same_exact7_qualifier_required']
 for p in sorted(p for p in source.glob('test_*.py') if p.name!='test_source7.py'):
  defined=sorted(methods(p.read_bytes()));names.extend(defined);groups.append(dict(source=pin(p),caseNames=defined,defined=len(defined)))
 assert len(names)==len(set(names)) and set(oldnames)<=set(names)
 count=len(names)
 runner=(source/'test_source7.py').read_text();runner=once(runner,'ACTUAL_REQUEST7_SOURCE1','ACTUAL_REQUEST7_SOURCE2');runner=once(runner,' import test_request_policy\n',' import test_request_policy\n import test_typed_origin\n');runner=once(runner,'loader.loadTestsFromModule(test_request_policy)])','loader.loadTestsFromModule(test_request_policy),loader.loadTestsFromModule(test_typed_origin)])');runner=once(runner,'result.testsRun==66','result.testsRun=='+str(count));write('source/test_source7.py',runner)
 write('CONTRACT.md',CONTRACT)
 contributors=sorted(set(json.loads((PRE/'lineage.json').read_bytes())['sourceContributorUnion'])|{DIAGNOSIS,ACTOR,'/root'})
 evidence_names=('security-findings.json','source1-disposition.json','json-alias-demonstration-origin.json','qa-review.json','security-review.json','complete-freeze.json')
 save('preservation.json',dict(schema='e02-collector-policy-source2-predecessor-preservation-v1',source1FilesBefore=before,source1Immutable=True,source1Accepted=False,source1ModelsExecuted=0,source1NamedDefinitions=66,source1QApositiveAndSecurityHOLDPreserved=True,reviewEvidenceObserved=review_before,negativeEvidence=[pin(REV/name) for name in evidence_names],noSourceApprovalOrResultTransfer=True))
 save('lineage.json',dict(schema='e02-collector-policy-source2-lineage-v1',actor=ACTOR,rootScope=pin(SCOPE),predecessorSubject=pin(PRE/'source-subject.json'),predecessorEntrypoint=pin(PRE/'review-entrypoint.json'),predecessorManifest=pin(PRE/'snapshot-manifest.json'),diagnosisContributor=DIAGNOSIS,negativeEvidence=[pin(REV/name) for name in evidence_names],sourceContributorUnion=contributors,reviewerExclusions=contributors,independentReviewersMustBeBornAfterFreeze=True,noOldSourceApprovalTransfer=True,noOldControlResultTransfer=True,sourceAcceptance=None,controlData=None,currentProducerControllerHelperConsumerAcceptancesBound=False,identityLeaseGrantIssued=False))
 request=json.loads((PRE/'request-policy.json').read_bytes());request['schema']='e02-collector-actual-request7-typed-origin-policy-v2';request.update(actualAndExpectedBothUseCompleteCommandValidation=True,wholeExpectedActualEquality='Exact canonical encoded JSON bytes; preserves type distinctions',rawOriginMutation=False,pollTypes=dict(session_id='Exact positive int; same previously established session',yield_time_ms='Optional exact int; omission/default and prior clock allowances unchanged',max_output_tokens='Existing exact-int/count-cap guard unchanged',chars='Existing empty chars route and permitted fieldset unchanged'),terminalResponseSession='Absent/null or exact int equal to the established yielded session');save('request-policy.json',request)
 budget=json.loads((PRE/'budget-contract.json').read_bytes());budget['schema']='e02-collector-request7-typed-origin-budget-contract-v2';budget['predecessorBudget']=pin(PRE/'budget-contract.json');budget['source2RemediationChangesStoredRequestShape']=False;budget['source2RemediationChangesNumericWaitLimits']=False;save('budget-contract.json',budget)
 save('control-plan.json',dict(schema='e02-collector-policy-source2-unexecuted-control-plan-v1',groups=groups,caseNames=names,modelsDefined=count,source1NamesPreserved=66,originalNamesPreserved=50,newNames=count-66,modelsExecuted=0,targetControlsExecuted=0,helperExecutions=0,collectorCommandsExecuted=0,argv=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(source/'test_source7.py')],cwd=str(source),runner=pin(source/'test_source7.py'),runnerRequires=dict(testsRun=count,skips=0,failures=0,errors=0),approvedInvocation=None,sourceApproval=None,rootRelease=None,actualControlData=None))
 coverage={
  'SEC-01_actual_login0':['TypedOriginControls.test_direct_actual_login0_against_pinned_false_refuses'],
  'SEC-01_actual_yield_float':['TypedOriginControls.test_direct_actual_yield_float_against_pinned_int_refuses'],
  'SEC-01_actual_bool_yield1':['TypedOriginControls.test_direct_actual_boolean_yield_against_pinned_int1_refuses'],
  'SEC-01_yielded_permanentfailstop':['TypedOriginControls.test_yielded_actual_only_type_aliases_refuse_and_failstop_permanently'],
  'unchanged_positive_and_raw':['TypedOriginControls.test_valid_separately_copied_typed7_direct_yielded_preserves_originals'],
  'whole_canonical_comparison':['TypedOriginControls.test_distinct_valid_actual_values_fail_whole_canonical_equality'],
  'poll_session_types':['TypedOriginControls.test_actual_poll_session_float_and_boolean_aliases_refuse'],
  'poll_yield_types':['TypedOriginControls.test_actual_poll_optional_yield_requires_exact_int_without_clock_extension'],
  'existing_poll_cap_types':['TypedOriginControls.test_actual_poll_max_tokens_retains_existing_exact_int_guard'],
  'terminal_response_session_types':['TypedOriginControls.test_terminal_response_session_float_boolean_aliases_refuse'],
  'pref_restore':['HistoryTypedOriginControls.test_pref_restore_actual_only_type_aliases_refuse'],
  'pref_permanentfailstop':['HistoryTypedOriginControls.test_pref_alias_failure_permanently_denies_later_corrected_final_proof'],
  'finalf_direct':['HistoryTypedOriginControls.test_finalf_direct_actual_only_aliases_permanently_refuse'],
  'finalf_yielded':['HistoryTypedOriginControls.test_finalf_yielded_actual_only_aliases_permanently_refuse'],
  'pref_finalf_same_poll_guards':['HistoryTypedOriginControls.test_pref_and_finalf_poll_type_guards_reach_same_new_qualifier'],
 }
 assert all(set(v)<=set(names) for v in coverage.values())
 save('requirements-and-coverage.json',dict(schema='e02-collector-policy-source2-requirements-coverage-v1',rootScope=pin(SCOPE),source1Coverage=pin(PRE/'requirements-and-coverage.json'),source1CaseNames=sorted(oldnames),original50CaseNames=sorted(original50),newCaseNames=sorted(set(names)-set(oldnames)),coverage=coverage,sourcePathAssertionAdaptation=changed_old_methods,sourcePathAssertionChange='Only source1 to source2 in absolute expected composite Source subject path; same positive/negative assertions.',suppliedJSONCannotAuthenticateCustodyOrDetectOmittedPlatformCalls=True,controlsExecuted=0,executionAuthorized=False))
 save('input-read-map.json',dict(schema='e02-collector-policy-source2-input-read-map-v1',method='SOURCE generator read operands only; all exact external bytes read for hashes, listed subsets also parsed/copied for preparation. No target module imports or execution.',rootScope=pin(SCOPE),predecessorWholePacketReadForPreservation=before,predecessorSourceModulesCopied=[pin(p) for p in sorted((PRE/'source').glob('*.py'))],predecessorMetadataParsed=[pin(PRE/name) for name in ('lineage.json','request-policy.json','budget-contract.json','source-subject.json')],source1ReviewEvidenceReadForPreservation=review_before,reviewEvidenceParsedForDiagnosis=[pin(REV/name) for name in ('security-findings.json','source1-disposition.json')],historicalOperandsReadForExactInvariance=[pin(BASE/name) for name in ('test_collector.py','test_history_prefix.py','collector.py','codec.py')],derivedSourceReadForASTAndHash=[pin(p) for p in sorted(source.glob('*.py'))],futureModuleResolution=dict(historyPrefix='Source2 source/history_prefix.py imports this same Source2 source/qualification.py',wholeControlRunner='Source2 source/test_source7.py explicitly selects its own directory before local module imports; this runner has not executed',operationalCLI='R4 collector remains pinned; no R4/R5 qualifier selected'),inputHashEqualityDoesNotGrantSourceOrRuntimeApproval=True))
 qa=functions((PRE/'source/qualification.py').read_bytes());qb=functions((source/'qualification.py').read_bytes());assert {k:v for k,v in qa.items() if k!='complete_origin'}=={k:v for k,v in qb.items() if k!='complete_origin'}
 assert functions((PRE/'source/history_prefix.py').read_bytes())==functions((source/'history_prefix.py').read_bytes())
 for name in ('collector.py','codec.py'):assert (source/name).read_bytes()==(PRE/'source'/name).read_bytes()==(BASE/name).read_bytes()
 assert all(pin(Path(d['path']))==d for d in before+review_before)
 pyfiles=sorted(source.glob('*.py'))+[Path(__file__)]
 for p in pyfiles:ast.parse(p.read_bytes(),filename=str(p))
 save('static-invariance.json',dict(schema='e02-collector-policy-source2-static-invariance-v1',method='Own stdlib copy/read/hash/JSON/AST/difflib only; no project imports or target execution.',pythonFiles=[pin(p) for p in pyfiles],astParseOnly=True,targetCompilationPerformed=False,original50NamedMethodASTBodiesIdentical=True,source1Named66SemanticsPreserved=True,source1Named65MethodASTBodiesIdentical=True,oneVersionPathAssertionRebound=changed_old_methods,qualifierFunctionsClassesUnchangedExceptCompleteOrigin=sorted(k for k in qa if k!='complete_origin'),historyAllFunctionsASTIdentical=True,historyGlobalChange='Only SOURCE_PATH source1 to source2; caller still supplies exact external Source2 whole descriptor.',unchangedCollector=pin(source/'collector.py'),unchangedCodec=pin(source/'codec.py'),rootFailstopAccountLedgerAckEngineUnchanged=True,source1PreservedFiles=before,source1ReviewsPreserved=review_before,modelsDefined=count,modelsExecuted=0,targetImports=0,targetCommands=0,executionAuthorized=False))
 diffrows=[]
 diffpaths=sorted(list(source.glob('*.py'))+[p for p in ROOT.glob('*') if p.is_file() and p.name not in ('source-subject.json','snapshot-manifest.json','review-entrypoint.json','full-diff-index.json')])
 for p in diffpaths:
  rel=p.relative_to(ROOT);previous=PRE/rel;old=previous.read_text() if previous.exists() else '';new=p.read_text();delta=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(previous) if previous.exists() else '/dev/null',tofile=str(p)))
  diffrows.append(dict(predecessor=pin(previous) if previous.exists() else None,current=pin(p),changed=old.encode()!=p.read_bytes(),completeUnifiedDiff=write('diffs/'+str(rel).replace('/','__')+'.diff',delta)))
 save('full-diff-index.json',dict(schema='e02-collector-policy-source2-full-diff-index-v1',files=diffrows,allCodeTestsGeneratorContractAndNonrecursiveMetadataIncluded=True,exclusions='Subject/manifest/entrypoint/full-diff-index itself have complete whole JSON content and are pinned downstream; no self-referential diff.',predecessorWholeSourcePreservation=pin(ROOT/'preservation.json')))
 payload=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in ('source-subject.json','snapshot-manifest.json','review-entrypoint.json')]
 subject=save('source-subject.json',dict(schema='e02-collector-actual-request7-typed-origin-composite-source-subject-v2',version='ACTUAL_REQUEST7_SOURCE2_20261105',actor=ACTOR,canonicalQ=['Q06','Q24'],scope='SOURCE_ONLY_SEC01_TYPED_ACTUAL_ORIGIN_REMEDIATION',sourceContributorUnion=contributors,reviewerExclusions=contributors,sources=[pin(p) for p in payload],rootScope=pin(SCOPE),negativePredecessor=pin(PRE/'source-subject.json'),operationalCollector=json.loads((PRE/'source-subject.json').read_bytes())['operationalCollector'],localCollector=pin(source/'collector.py'),operationalQualifier=pin(source/'qualification.py'),historyPrefixSource=pin(source/'history_prefix.py'),losslessPerOriginCodec=pin(source/'codec.py'),modelsDefined=count,modelsExecuted=0,source1NamedDefinitionsPreserved=66,original50NamedDefinitionsPreserved=True,sourceApproval=None,dataApproval=None,concreteRelease=None,helperAcceptance=None,executionAuthorized=False,selfApproval=False,canonicalE02Changed=False))
 manifest=save('snapshot-manifest.json',dict(schema='e02-collector-policy-source2-packet-manifest-v1',root=str(ROOT),files=[pin(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in ('snapshot-manifest.json','review-entrypoint.json')],excludesSelfAndEntrypoint=True,graphOrder='Code/generator + immutable external evidence -> metadata/diffs -> diff index -> subject -> manifest -> entrypoint; no acceptance/grant edges.',noRuntimeData=True))
 entry=save('review-entrypoint.json',dict(schema='e02-collector-policy-source2-review-entrypoint-v1',actor=ACTOR,sourceSubject=subject,snapshotManifest=manifest,sourceContributorUnion=contributors,reviewerExclusions=contributors,diagnosis='SEC-01 MEDIUM Source1 HOLD preserved; candidate remediation only, no self approval.',modelsDefined=count,modelsExecuted=0,sourceOnly=True,targetImports=0,targetCommandsExecuted=0,collectorCommandsExecuted=0,codecCommandsExecuted=0,historyPrefixCommandsExecuted=0,helperExecutions=0,ordinaryRoles=0,sourceAcceptance=None,controlData=None,rootGrant=None,executionAuthorized=False,selfApproval=False,independentReviewersMustBeBornAfterFreeze=True,reviewRequired=['Fresh independent QA','Fresh independent security'],currentProducerControllerHelperConsumerAcceptancesBound=False))
 assert all(pin(Path(d['path']))==d for d in before+review_before)
 print(json.dumps(dict(entrypoint=entry,subject=subject,manifest=manifest,modelsDefined=count,source1NamedDefinitionsPreserved=66,newNames=count-66,source1FilesPreserved=len(before),source1ReviewFilesPreserved=len(review_before),sourceContributors=contributors),indent=2))

if __name__=='__main__':main()
