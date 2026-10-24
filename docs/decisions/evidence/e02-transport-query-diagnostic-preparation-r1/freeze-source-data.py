"""Source/AST/JSON/pin freeze only; no project import, Node, tests or runtime."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import os
import uuid

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP');P=ROOT/'experiments/prototypes/e02_transport_query_diagnostic_v1'
E=ROOT/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r1'
B=ROOT/'experiments/prototypes/e02_ordinary_minimum_v1'
OLD_PREP=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1'
FAIL=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1'
DIAG=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-relay-diagnosis-r1'

def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(p,v):
 p=Path(p);p.write_text(v if type(v) is str else json.dumps(v,indent=2)+'\n');p.chmod(0o600)
def check(d):
 if pin(d['path'])!=d:raise ValueError('Read-only original pin drift')
def funcs(tree):
 result={}
 def visit(body,prefix=''):
  for n in body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    result[prefix+n.name]=ast.dump(n,include_attributes=False)
    if isinstance(n,ast.ClassDef):visit(n.body,prefix+n.name+'.')
 visit(tree.body);return result

old_subject=json.loads((OLD_PREP/'subject.json').read_text())
protected=list(old_subject['sources'])
protected += [pin(OLD_PREP/'subject.json'),pin(OLD_PREP/'proposed-incoming-run-config.json'),pin(FAIL/'subject-r2.json'),pin(FAIL/'failure-facts-r2.json'),pin(FAIL/'preservation-index.json'),pin(DIAG/'subject.json'),pin(DIAG/'REPORT.md')]
for d in protected:check(d)
write(E/'protected-inputs-before.json',{'schema':'e02-transport-diagnostic-protected-snapshot-v1','files':protected})
old_plan=json.loads((B/'fixture-plan.json').read_text());old_config=json.loads((OLD_PREP/'proposed-incoming-run-config.json').read_text())
for d in old_plan['dependencyFiles']:
 if pin(d['source'])!={k:d[k] for k in ('bytes','sha256')}|{'path':d['source']}:raise ValueError('Existing dependency drift')
fixture={'schema':'e02-transport-query-diagnostic-fixture-v1','scenario':'BASELINE_ONE_PUB_THEN_EXACT_QUERY','backendUrl':'ws://127.0.0.1:8080','output':'/session/fixtures','eventId':'1203eaed1d1c6fd2d3fe9600209c3bc2036e68e9a7b79bb8b720989d06b844da','publish':pin(P/'publish-frame.json'),'query':pin(P/'query-frame.json'),'limits':{'messageBytes':262144,'captureBytes':16777216,'networkTimeoutMilliseconds':10000,'handshakeTimeoutMilliseconds':3000,'controlTimeoutMilliseconds':45000},'pins':{},'dependencyFiles':old_plan['dependencyFiles'],'nodeVersion':'v22.18.0','wsVersion':'8.18.3','modeledBackgroundBurst':'DEFERRED_NOT_IMPLEMENTED_OR_GRANTED','scope':'DIAGNOSTIC_ONLY_NO_ANDROID_APP_OR_E02_COMPLETION'}
write(P/'fixture-plan.json',fixture)
names=('supervisor.py','lease_guard.py','fixture.mjs','exchange.mjs','strict-json.mjs','fixture-plan.json','publish-frame.json','query-frame.json')
config={'schema':'e02-transport-query-diagnostic-config-v1','scope':'E02_TRANSPORT_QUERY_DIAGNOSTIC_ONLY_NO_ANDROID_NO_E02_COMPLETION','runId':uuid.uuid4().hex,'originalLeaseSeconds':300,'runtimeImage':old_config['runtimeImage'],'relayImage':old_config['relayImage'],'sourceAndDependencyPins':[pin(P/n) for n in names],'guardBundleRoot':old_config['guardBundleRoot'],'guardBundleInventory':old_config['guardBundleInventory'],'relayConfig':old_config['relayConfig']}
if (E/'proposed-run-config.json').exists():config['runId']=json.loads((E/'proposed-run-config.json').read_text())['runId']
if (Path('/tmp/nbdp-e02-transport-query-diagnostic-v1/runs')/config['runId']).exists():raise ValueError('Candidate output exists')
write(E/'proposed-run-config.json',config)
# Full Python typed AST/function comparison; parser only, no import/compilation.
changes=[]
for name in ('supervisor.py','lease_guard.py'):
 before=ast.parse((B/name).read_text());after=ast.parse((P/name).read_text())
 a,b=ast.dump(before,indent=2,include_attributes=False),ast.dump(after,indent=2,include_attributes=False)
 write(E/(name+'.typed-ast-before.json'),{'source':pin(B/name),'tree':a});write(E/(name+'.typed-ast-after.json'),{'source':pin(P/name),'tree':b})
 write(E/(name+'.typed-ast.diff'),''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(B/name),tofile=str(P/name))))
 fa,fb=funcs(before),funcs(after)
 changes.append({'file':name,'before':pin(B/name),'after':pin(P/name),'unchangedFunctions':[n for n in fb if fa.get(n)==fb[n]],'changedOrAddedFunctions':[n for n in fb if fa.get(n)!=fb[n]],'removedFunctions':[n for n in fa if n not in fb]})
for p in P.glob('*.py'):ast.parse(p.read_text())
write(E/'typed-function-diff.json',{'schema':'e02-transport-diagnostic-python-function-diff-v1','files':changes,'method':'stdlib ast.parse/dump only; no imports or runtime'})
# Preserve original source exchange with the new instrumented sibling side by side.
s=(B/'fixture.mjs').read_text();a=s.index(' async function exchange(');b=s.index(' async function prepare(',a)
write(E/'original-exchange-source.mjs',s[a:b])
write(E/'instrumented-exchange.diff',''.join(difflib.unified_diff(s[a:b].splitlines(True),(P/'exchange.mjs').read_text().splitlines(True),fromfile=str(B/'fixture.mjs')+':exchange',tofile=str(P/'exchange.mjs'))))
write(E/'full-source.diff',''.join(''.join(difflib.unified_diff((B/p.name).read_text().splitlines(True) if (B/p.name).exists() else [],p.read_text().splitlines(True),fromfile=str(B/p.name) if (B/p.name).exists() else '/dev/null',tofile=str(p))) for p in sorted(P.iterdir()) if p.is_file()))
counts={p.name:sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(ast.parse(p.read_text()))) for p in P.glob('test*.py')}
write(E/'static-source-checks.json',{'schema':'e02-transport-diagnostic-static-partition-v1','allPythonSyntaxParsedWithoutImport':True,'pythonTestDefinitions':counts,'nodeEngineParseOrImport':False,'guardBytesUnchanged':(P/'lease_guard.py').read_bytes()==(B/'lease_guard.py').read_bytes(),'threeRolesOnly':['anchor','rs-relay','fixture'],'noAdbSnapshotOrSdkMountBranches':'Runtime.adb/snapshot removed; start has no Android branch; all devices refused. Borrowed guard ENV has dormant old SDK path strings only.','limitsUnchanged':fixture['limits'],'parentFixtureCommandSeconds':55,'proposedLeaseSeconds':300,'maximumOriginalLeaseSeconds':1800,'knownSourceModelDifferences':['Context dependency injection only for targeted fake model; real runtime context hard-bound internally.','Raw phase evidence before guard grants no action; terminal callbacks context only.','Persist partial outcome on reject instead of losing it; original timers/guard/query unchanged.'],'publicExactFrameInputs':[fixture['publish'],fixture['query']],'noNsecOrKeyOrNonceInput':True,'allControlsRuntimeAndProbesExecuted':0})
write(E/'guard-scope-link.json',{'schema':'e02-transport-diagnostic-unchanged-guard-scope-link-v1','original':pin(B/'lease_guard.py'),'current':pin(P/'lease_guard.py'),'priorActualAcceptedScope':pin(OLD_PREP/'unchanged-guard-scope-link.json'),'scope':'PRIOR_BYTE_IDENTICAL_GUARD29_ONLY_NOT_NEW_EXECUTION','newDiagnosticSourceAndModelControls':'PENDING_ACTUAL_REVIEW_AND_EXECUTION','ordinaryClientOrDiagnosticRuntimeQualified':False})
write(E/'control-plan.json',{'schema':'e02-transport-query-diagnostic-source-control-plan-v1','state':'PREPARED_NOT_EXECUTED_REQUIRES_INDEPENDENT_SOURCE_QA_SECURITY_AND_ROOT_INSTRUCTION','author':'/root/ordinary_api35_source','separateScopes':[{'name':'source-custody-mock','argv':['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(P/'test_source_controls.py')],'plannedChecks':10,'timeoutSeconds':60},{'name':'fake-socket-phase-model','argv':['/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node',str(P/'test_exchange_model.mjs')],'plannedChecks':20,'timeoutSeconds':60}],'capturePolicy':'Trusted finite child, raw0600, actual lifecycle/source/input/interpreter before-after, first failure stop/no retry; original API objects separately retained; stdout1MiB/stderr256KiB post-capture retention not streaming cap.','modelScope':'Actual exchange function with fake WS/guard/clock/timers only; source/custody model imports only definitions. No real guard issue, protocol crypto/native, network, Docker, Android or SDK.','prerequisitesForLaterRuntime':['Actual independent SOURCE acceptance + executed current10/20 meaningful controls + independent result acceptance.','Exact current runtime/rs image, Node/ws/dependencies/guard-bundle/relay config and exact public frame pins.','Fresh isolated root300s candidate release/admission/operator/custody; original network10s/handshake3s/control45s/command55s/maxlease1800s unchanged.','NoAndroid baseline only; raw phase/partial errors/commands/owned3CID cleanup and actual original tool responses.'],'laterRuntimeCommand':['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(P/'supervisor.py'),'--config',str(E/'proposed-run-config.json'),'--config-sha','EXACT_CONFIG_SHA','--release','ACTUAL_FUTURE_ROOT_RELEASE','--release-sha','ACTUAL_FUTURE_RELEASE_SHA','--out','/tmp/nbdp-e02-transport-query-diagnostic-v1/runs/'+config['runId']],'noGrantLeaseOrRuntimeMaterialized':True,'optionalModeledBurst':'DEFERRED_SEPARATE_CASE_NOT_IMPLEMENTED_OR_AUTHORIZED_HERE'})
write(E/'README.md','''# Transport query diagnostic SOURCE preparation r1

Only the new prototype and this preparation prefix were written. Original
minimum source/failure/correction/diagnosis, E06 and shared state/Git remain
unchanged. This profile is a single no-Android public PUB/REQ diagnostic, not
another ordinary-client attempt or canonical completion. No NSEC/key/nonce input
or unused malformed plan literal was copied. Exact signed outer/query bytes are
reused, never newly encrypted/signed.

The original lease/finite command/identity/custody/cleanup code is reused and
fully compared by typed AST. Android paths are removed from the supervisor route;
three original isolated roles remain. Instrumented exchange persists bounded
phase/refusal/partial-outcome evidence while retaining actual synchronous guard
and original10s/3s/45s/55s/1800s limits. Proposed300s lease is DATA only; root grant,
lease issue, images/services and runtime remain absent. See prototype CONTRACT.

Ten source/custody and20 fake-socket model definitions are prepared NOT RUN.
Python ast.parse is syntax/DATA only; no worker/test/Node import or compilation,
Docker/probe/guard/native/SDK/Android/crypto/network/diagnostic occurred. Node/ws
and guard bundle are existing pinned prerequisites, not installed or executed.
Source/control/runtime QA/security remains actual future work, not author approval.
''')
for d in protected:check(d)
write(E/'protected-inputs-after.json',{'schema':'e02-transport-diagnostic-protected-snapshot-v1','files':protected})
write(E/'preparation-execution.json',{'schema':'e02-transport-diagnostic-source-preparation-record-v1','actor':'/root/ordinary_api35_source','sourceGenerators':[pin(E/'prepare-supervisor-source.py'),pin(E/'supervisor-new-entrypoints.txt')],'freezeScript':pin(Path(__file__).resolve()),'actions':'Owned source extraction/text edits + stdlib AST/JSON/hash/copy only','nodeExecuted':False,'workerOrTestImport':False,'testsOrRuntimeOrProbes':0,'grantOrLeaseIssued':False,'independentReview':'PENDING_ACTUAL_OTHER_AGENTS'})
sources=[pin(p) for p in sorted(P.iterdir()) if p.is_file()]
artifacts=[pin(p) for p in sorted(E.iterdir()) if p.is_file() and p.name not in ('subject.json','artifact-manifest.json')]
write(E/'subject.json',{'schema':'e02-transport-query-diagnostic-source-subject-v1','author':'/root/ordinary_api35_source','coordinator':'/root','state':'WRITES_STOPPED_SOURCE_ONLY_PENDING_ACTUAL_INDEPENDENT_QA_SECURITY','scope':config['scope'],'sources':sources,'preparationArtifacts':artifacts,'configuration':pin(E/'proposed-run-config.json'),'contract':pin(P/'CONTRACT.md'),'controlPlan':pin(E/'control-plan.json'),'typedFunctionDiff':pin(E/'typed-function-diff.json'),'instrumentedExchangeDiff':pin(E/'instrumented-exchange.diff'),'originalFailure':pin(FAIL/'subject-r2.json'),'boundedDiagnosis':pin(DIAG/'subject.json'),'preparedScopes':{'sourceCustody':10,'fakeSocketModel':20},'actualControlsAndRuntimeExecuted':0,'rootGrantOrLeaseCreated':False,'ordinaryAppObservedOrQualified':False,'optionalBurst':'DEFERRED_NOT_IMPLEMENTED','canonicalE02':'PARTIAL22_UNCHANGED','architecturalBlockersUnchanged':['Q01','Q08','Q13','Q15','Q27'],'remaining':['Actual independent same-source QA/security.','Current targeted10/20 controls and independent result acceptance.','Fresh exact300s diagnostic root grant/current image/dependency/bundle/admission evidence.','Actual noAndroid PUB/query phase/refusal/owned-cleanup evidence and nonoperator review.'],'noOriginalSourceOrGateChanges':True})
write(E/'artifact-manifest.json',{'schema':'e02-transport-diagnostic-source-artifact-manifest-v1','files':[pin(p) for p in sorted(E.iterdir()) if p.is_file() and p.name!='artifact-manifest.json'],'excludesSelf':True})
for folder in (P,E):
 for p in folder.iterdir():
  if p.is_file():p.chmod(0o600)
print(json.dumps({'state':'WRITES_STOPPED','subject':pin(E/'subject.json'),'config':pin(E/'proposed-run-config.json'),'contract':pin(P/'CONTRACT.md'),'controlPlan':pin(E/'control-plan.json'),'typedFunctionDiff':pin(E/'typed-function-diff.json'),'exchangeDiff':pin(E/'instrumented-exchange.diff'),'counts':counts,'actualTestsRuntimeProbes':0},indent=2))
