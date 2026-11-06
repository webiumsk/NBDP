"""SOURCE2 data/AST/pin freeze only. Never imports workers or runs controls."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re
import uuid

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
P=ROOT/'experiments/prototypes/e02_transport_query_diagnostic_v2'
B=ROOT/'experiments/prototypes/e02_transport_query_diagnostic_v1'
E=ROOT/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2'
OLD=ROOT/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r1'
MODULES=ROOT/'experiments/node_modules'

def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_text(v if type(v) is str else json.dumps(v,indent=2)+'\n');p.chmod(0o600)
def checked(d):
 if pin(d['path'])!=d:raise ValueError('Protected source drift:'+d['path'])
def funcs(tree):
 out={}
 def scan(body,prefix=''):
  for n in body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    out[prefix+n.name]=ast.dump(n,include_attributes=False)
    if isinstance(n,ast.ClassDef):scan(n.body,prefix+n.name+'.')
 scan(tree.body);return out

v1=json.loads((OLD/'subject.json').read_text())
protected=[*v1['sources'],pin(OLD/'subject.json'),pin(OLD/'proposed-run-config.json')]
for name in ('actual-source-qa-review.json','actual-source-security-review.json','source-review-disposition.json'):
 p=OLD/name;protected.append(pin(p));write(E/'preserved-v1-reviews'/name,p.read_text())
for d in json.loads((OLD/'protected-inputs-after.json').read_text())['files']:
 if d['path'] not in {x['path'] for x in protected}:protected.append(d)
for d in protected:checked(d)
write(E/'protected-inputs-before.json',{'schema':'e02-transport-source2-protected-inputs-v1','files':protected})

# Exact current baseline tree, with pre-existing known regular membership only.
fixture=json.loads((B/'fixture-plan.json').read_text());tree={'schema':'e02-transport-dependency-tree-v2','sourceRoot':str(MODULES),'runtimeRoot':'/input/node_modules','directories':[],'files':[],'symlinks':[]}
def walk(folder):
 for p in sorted(folder.iterdir()):
  rel=p.relative_to(MODULES).as_posix()
  if p.is_symlink():
   target=p.resolve(strict=True)
   if not target.is_relative_to(MODULES) or target==MODULES:raise ValueError('Installed symlink escape')
   tree['symlinks'].append({'path':rel,'link':str(p.readlink()),'target':target.relative_to(MODULES).as_posix()})
  elif p.is_dir():tree['directories'].append(rel);walk(p)
  elif p.is_file():tree['files'].append(rel)
  else:raise ValueError('Installed special file')
walk(MODULES)
for k in ('directories','files'):tree[k].sort()
tree['symlinks'].sort(key=lambda v:v['path'])
expected=sorted(d['path'].removeprefix('/input/node_modules/') for d in fixture['dependencyFiles'])
if tree['files']!=expected or len(expected)!=816:raise ValueError('Regular membership differs from original approved816')
for d in fixture['dependencyFiles']:
 checked({'path':d['source'],'bytes':d['bytes'],'sha256':d['sha256']})
write(P/'dependency-tree.json',tree)
fixture['schema']='e02-transport-query-diagnostic-fixture-v2'
fixture['publish']=pin(P/'publish-frame.json');fixture['query']=pin(P/'query-frame.json')
fixture['dependencyClosure']='EXACT_REGULAR_DIRECTORY_SYMLINK_SOURCE_RUNTIME_MAPPING_V2'
write(P/'fixture-plan.json',fixture)
config=json.loads((OLD/'proposed-run-config.json').read_text());config['schema']='e02-transport-query-diagnostic-config-v2';config['scope']='E02_TRANSPORT_QUERY_DIAGNOSTIC_V2_ONLY_NO_ANDROID_NO_E02_COMPLETION'
config['runId']=json.loads((E/'proposed-run-config.json').read_text())['runId'] if (E/'proposed-run-config.json').exists() else uuid.uuid4().hex
names=('supervisor.py','lease_guard.py','fixture.mjs','exchange.mjs','strict-json.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json','fixture-plan.json','publish-frame.json','query-frame.json')
config['sourceAndDependencyPins']=[pin(P/n) for n in names]
if (Path('/tmp/nbdp-e02-transport-query-diagnostic-v2/runs')/config['runId']).exists():raise ValueError('Fresh output already exists')
write(E/'proposed-run-config.json',config)
changes=[]
for p in sorted(P.glob('*.py')):
 new=ast.parse(p.read_text());old=ast.parse((B/p.name).read_text())
 a,b=ast.dump(old,indent=2,include_attributes=False),ast.dump(new,indent=2,include_attributes=False)
 write(E/(p.name+'.typed-ast-before.json'),{'source':pin(B/p.name),'tree':a});write(E/(p.name+'.typed-ast-after.json'),{'source':pin(p),'tree':b})
 write(E/(p.name+'.typed-ast.diff'),''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(B/p.name),tofile=str(p))))
 fa,fb=funcs(old),funcs(new);changes.append({'file':p.name,'before':pin(B/p.name),'after':pin(p),'unchangedFunctions':[n for n in fb if fa.get(n)==fb[n]],'changedOrAddedFunctions':[n for n in fb if fa.get(n)!=fb[n]],'removedFunctions':[n for n in fa if n not in fb]})
write(E/'typed-function-diff.json',{'schema':'e02-transport-query-source2-function-diff-v1','method':'stdlib AST parse/dump only; no worker import/test execution','files':changes})
write(E/'full-source.diff',''.join(''.join(difflib.unified_diff((B/p.name).read_text().splitlines(True) if (B/p.name).exists() else [],p.read_text().splitlines(True),fromfile=str(B/p.name) if (B/p.name).exists() else '/dev/null',tofile=str(p))) for p in sorted(P.iterdir()) if p.is_file()))
write(E/'exchange-v1-to-v2.diff',''.join(difflib.unified_diff((B/'exchange.mjs').read_text().splitlines(True),(P/'exchange.mjs').read_text().splitlines(True),fromfile=str(B/'exchange.mjs'),tofile=str(P/'exchange.mjs'))))
py=ast.parse((P/'test_source_controls.py').read_text())
python_cases={n.name:[m.name for m in n.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_')] for n in py.body if isinstance(n,ast.ClassDef)}
model_cases=re.findall(r"await test\('([^']+)'",(P/'test_exchange_model.mjs').read_text())
guest_cases=re.findall(r"^test\('([^']+)'",(P/'test_dependency_tree.mjs').read_text(),re.M)
if sum(map(len,python_cases.values()))!=18 or len(model_cases)!=27 or len(guest_cases)!=6:raise ValueError('Prepared definition count mismatch')
legacy_py=funcs(ast.parse((B/'test_source_controls.py').read_text()));new_py=funcs(py)
old_py_tests=[n for n in legacy_py if '.test_' in n]
if len(old_py_tests)!=10 or not all(legacy_py[n]==new_py[n] for n in old_py_tests):raise ValueError('Preserve original ten test bodies')
old_model_lines=[line for line in (B/'test_exchange_model.mjs').read_text().splitlines() if line.startswith('await test(')]
new_text=(P/'test_exchange_model.mjs').read_text();unchanged_model_lines=[line for line in old_model_lines if line in new_text]
write(E/'control-definition-provenance.json',{'schema':'e02-transport-source2-current-definition-provenance-v1','oldSource1ControlsExecuted':0,'currentPythonCases':python_cases,'currentModelCases':model_cases,'currentGuestTreeCases':guest_cases,'originalPythonTestBodiesUnchanged':len(old_py_tests),'originalModelBodiesTextUnchanged':len(unchanged_model_lines),'versionedModelExpectation':'Original late-callback-context test is preserved in v1; v2 requires inert late callbacks, no post-terminal writes/actions.','oldModelHelpersChanged':'New fault injection and termination counter; all current scopes need new execution, no historical pass transfer.','priorGuard29OnlyByteBoundCarry':pin(OLD/'guard-scope-link.json'),'actualCurrentControlsExecuted':0})
qa=json.loads((OLD/'actual-source-qa-review.json').read_text());sec=json.loads((OLD/'actual-source-security-review.json').read_text())
write(E/'remediation-map.json',{'schema':'e02-transport-source2-remediation-map-v1','originalSourceSubject':pin(OLD/'subject.json'),'actualPriorQa':pin(OLD/'actual-source-qa-review.json'),'actualPriorSecurity':pin(OLD/'actual-source-security-review.json'),'actualHoldDisposition':pin(OLD/'source-review-disposition.json'),'originalFindings':[*(f for f in qa['findings']),*(f for f in sec['findings'])],'sourceCorrections':[{'family':'DEPENDENCY_CLOSURE','files':['supervisor.py','dependency-tree.mjs','dependency-tree.json','fixture.mjs'],'evidence':'Exact host/source-relative816 regular65dirs2knownsymlinks; before activation/guest dynamic import and guest/host end-boundaries; extras/missing/escape/special/mapping/changed controls.'},{'family':'TERMINAL_RETENTION','files':['exchange.mjs','fixture.mjs'],'evidence':'One terminal claim; incoming first fault preserved, retention secondary; independent finally terminate/reject; active callback sink boundaries; inert late callbacks; no outside timeout settlement.'},{'family':'PHASE_SHORT_WRITE','files':['phase-writer.mjs','fixture.mjs'],'evidence':'One checked writeSync; poison on partial/invalid/throw/overflow; acknowledged prefix/count distinct from physical UNKNOWN; no repair/retry/send/query/success after poison.'}],'authorResolutionClaim':'NONE_SOURCE_PREPARED_ONLY_REQUIRES_ACTUAL_INDEPENDENT_REVIEW','runtimeOccurrenceOrVulnerabilityClaimed':False})
write(E/'static-source-checks.json',{'schema':'e02-transport-source2-static-checks-v1','guardBytesUnchanged':(P/'lease_guard.py').read_bytes()==(B/'lease_guard.py').read_bytes(),'exactPublishAndQueryBytesUnchanged':all((P/n).read_bytes()==(B/n).read_bytes() for n in ('publish-frame.json','query-frame.json')),'sameOriginalLimits':fixture['limits'],'unchangedLeaseSeconds':config['originalLeaseSeconds'],'sameImages':{k:config[k] for k in ('runtimeImage','relayImage')},'dependencyTreeCounts':{k:len(tree[k]) for k in ('files','directories','symlinks')},'allCurrentPythonSyntaxParsed':True,'sixNodeCheckCommands':'Syntax only, original API responses retained separately; no project module evaluation/import or test/runtime.','syntaxToolReceipts':pin(E/'syntax-only-original-tool-receipts.json'),'preparedScopes':{'pythonSourceCustody10PlusInventory8':18,'fakeSocketLegacy20PlusNewFaultFamilies7':27,'guestInventoryFamilies':6},'controlsRuntimeImportsServicesLeasesExecuted':0,'lateCallbacks':'Version2 observer behavior: no writes/actions after terminal claim; no protocol timer/operand change.'})
base=ROOT/'docs/decisions/evidence/e02-completion-preparation-r1/current-controls-r1/capture-controls.py'
write(E/'control-plan.json',{'schema':'e02-transport-source2-current-control-plan-v1','state':'PREPARED_NOT_EXECUTED_PENDING_ACTUAL_SOURCE_QA_SECURITY_AND_ROOT_RELEASE','author':'/root/ordinary_api35_source','reuseExistingCaptureSource':pin(base),'captureApproach':'Narrow fixed-scope adaptation of existing finite direct-child capture only; no new monitor/framework. Raw0600, source/config/inputs/interpreters before-after, original external API objects separate from child journals, first failure stop/no retry.','rawRetentionBytes':{'stdout':1048576,'stderr':262144},'retentionMeaning':'Post-capture refusal/retention, NOT streaming memory cap.','separateScopes':[{'name':'source-custody-and-host-inventory','argv':['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(P/'test_source_controls.py')],'count':18,'partitions':{'unchangedPriorDefinitionBodies':10,'newInventoryFamilies':8},'expectedClassCases':python_cases,'timeoutSeconds':60},{'name':'fake-socket-and-physical-prefix-model','argv':['/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node',str(P/'test_exchange_model.mjs')],'count':27,'partitions':{'priorScopeCasesIncludingVersionedLateBehavior':20,'newFaultFamilies':7},'expectedCases':model_cases,'timeoutSeconds':60},{'name':'guest-dependency-inventory-data','argv':['/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node',str(P/'test_dependency_tree.mjs')],'count':6,'expectedCases':guest_cases,'timeoutSeconds':60}],'priorActualSource1Controls':0,'unchangedDefinitionIsNotExecutedCarry':True,'modelsDoNotImportOptionalModulesOrRunActualGuardNetwork':True,'laterRuntimePrerequisites':['Actual independent same-frozen-source QA/security acceptance.','Once-only actual18/27/6 current DATA/model checks and actual independent result acceptance.','Exact fresh config/current tree/images/bundle/admission and separate root finite grant.','One noAndroid public PUB/REQ attempt with phase/outcome/custody/end-boundary/owned cleanup and nonoperator review.'],'noCurrentRuntimeGrantOrLease':True})
write(E/'README.md','''# Transport query diagnostic SOURCE2

SOURCE1 remains HOLD after actual independent QA/security, with zero controls or
runtime. This sibling preserves its exact source/config/reviews and negative
facts. Source2 prepares the three bounded remediation families in remediation-map;
the author does not approve resolution. Original protocol deadlines, public frame
bytes, guard/ownership/cgroup/cleanup and baseline-only scope remain unchanged.

Exact dependency tree is816regular/65dirs/2known in-tree .bin symlinks. Host and
guest admission/end-boundaries reject additions/optional bufferutil, missing or
changed members, aliases/escapes/specials. Terminal finally cleanup/settlement is
independent of observation writes, preserves the first incoming fault and records
retention failures as secondary. One-write acknowledgement checks poison short/
invalid/failed observations; acknowledged prefix/count is not physical attestation.
Late callbacks are versioned inert observations after terminal claim.

Prepared18 Python (10old bodies+8inventory),27 model (20prior-scope cases+7focused
fault families),6guest-tree DATA families remain NOT RUN. Prior SOURCE1 controls
never ran, so there is no execution carry for these definitions. Only unchanged
guard29 has its explicit old byte-bound scope link. Synthetic files/modules in
models are inert and never imported; models use fake sockets/guards/timers and
check terminal settlement without an outside timeout. No real guard or services.

Six Node --check processes actually ran and returned0 as STATIC SYNTAX ONLY;
their original API objects are preserved. No project module import/evaluation,
test suite, crypto/native Rust/guard, Docker/relay/Android/SDK/runtime, lease or
root grant ran here. Stdlib Python AST/JSON/hash and metadata source operations
are not runtime interoperability. Publication/old source/current449 graph/shared
state/Git were not edited. Actual independent SOURCE review and meaningful current
controls still precede any fresh isolated diagnostic grant.
''')
for d in protected:checked(d)
write(E/'protected-inputs-after.json',{'schema':'e02-transport-source2-protected-inputs-v1','files':protected})
write(E/'preparation-execution.json',{'schema':'e02-transport-source2-preparation-record-v1','actor':'/root/ordinary_api35_source','actions':'Owned version copy/text SOURCE edits, metadata inventory, stdlib AST/hash/JSON/diff only;6explicit syntax-only Node --check commands','syntaxOriginalToolResponses':pin(E/'syntax-only-original-tool-receipts.json'),'testsOrRuntimeExecuted':0,'projectImportsEvaluated':False,'optionalModulesImported':False,'grantOrLeaseCreated':False,'authorFindingAcceptance':False,'script':pin(Path(__file__).resolve())})
sources=[pin(p) for p in sorted(P.iterdir()) if p.is_file()]
artifacts=[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ('subject.json','artifact-manifest.json')]
write(E/'subject.json',{'schema':'e02-transport-query-diagnostic-source-subject-v2','author':'/root/ordinary_api35_source','coordinator':'/root','state':'WRITES_STOPPED_SOURCE2_PENDING_ACTUAL_INDEPENDENT_QA_SECURITY','sources':sources,'preparationArtifacts':artifacts,'configuration':pin(E/'proposed-run-config.json'),'contract':pin(P/'CONTRACT.md'),'controlPlan':pin(E/'control-plan.json'),'remediationMap':pin(E/'remediation-map.json'),'priorSource1Subject':pin(OLD/'subject.json'),'priorActualHold':pin(OLD/'source-review-disposition.json'),'typedFunctionDiff':pin(E/'typed-function-diff.json'),'fullSourceDiff':pin(E/'full-source.diff'),'exchangeDiff':pin(E/'exchange-v1-to-v2.diff'),'preparedCurrentScopes':{'sourceCustodyInventory':18,'fakeSocketWriterModels':27,'guestInventoryData':6},'actualCurrentControlsExecuted':0,'syntaxOnlyNodeProcesses':6,'actualDiagnosticRuntimeOrProbes':False,'rootGrantOrLeaseCreated':False,'source1AndOriginalFailureBytesPreserved':True,'findingResolutionClaimedByAuthor':False,'optionalBurst':'DEFERRED_NOT_IMPLEMENTED','canonicalE02':'PARTIAL22_UNCHANGED','stockE04E06Unlocked':False,'architecturalBlockersUnchanged':['Q01','Q08','Q13','Q15','Q27']})
write(E/'artifact-manifest.json',{'schema':'e02-transport-source2-artifact-manifest-v1','files':[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'],'excludesSelf':True})
for folder in (P,E):
 for p in folder.rglob('*'):
  if p.is_file():p.chmod(0o600)
  elif p.is_dir():p.chmod(0o700)
print(json.dumps({'state':'WRITES_STOPPED','subject':pin(E/'subject.json'),'config':pin(E/'proposed-run-config.json'),'contract':pin(P/'CONTRACT.md'),'plan':pin(E/'control-plan.json'),'diff':pin(E/'full-source.diff'),'tree':pin(P/'dependency-tree.json'),'counts':{'python':18,'model':27,'guestTree':6},'actualTestsRuntime':0},indent=2))
