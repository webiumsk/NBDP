from pathlib import Path
import ast,json,hashlib,difflib,shutil
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2';C=E/'current-controls-r1';O=R/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2/current-controls-r1/capture-controls.py'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
main=pin(E/'subject.json');assert main['sha256']=='ef91dc64189d7c47a4b4539c4dacd93a4c5c760da8f98bf1b203040bba6eeffd'
actual={role:pin(E/('actual-source-'+role+'-review.json')) for role in ('qa','security')}
for role,d in actual.items():
 v=json.loads(Path(d['path']).read_bytes());assert set(v)=={'role','session','decision','subject'} and v['role']==role and v['subject']==main and v['decision']=='ACCEPT_MINIMUM_PRODUCER_SOURCE_FOR_CHANGED_CONTROLS_ONLY'
p=C/'capture-controls.py';s=p.read_text();assert 'ACCEPTED_REVIEW_DECISIONS = None' not in s
assert s.count('ACCEPT_MINIMUM_PRODUCER_SOURCE_FOR_CHANGED_CONTROLS_ONLY')==2
ast.parse(s)
inputs=json.loads((C/'frozen-inputs.json').read_bytes());by={d['path']:d for d in inputs['files']}
for d in [*actual.values(),pin(E/'source-review-disposition.json')]:by[d['path']]=d
inputs['files']=[by[k] for k in sorted(by)];inputs['actualSourceReviews']=actual;save(C/'frozen-inputs.json',inputs)
plan=json.loads((C/'control-plan.json').read_bytes());plan.update(state='FROZEN_CAPTURE_SOURCE_ONLY_PENDING_ACTUAL_INDEPENDENT_CAPTURE_REVIEW_AND_ROOT_RELEASE',runner=pin(p),actualMainSourceReviews=actual,fixedInputCount=len(by));save(C/'control-plan.json',plan)
shape=json.loads((C/'root-ack-shape.json').read_bytes());shape['actualMainSourceReviews']=actual;shape['actualMainDecisionLiteral']='ACCEPT_MINIMUM_PRODUCER_SOURCE_FOR_CHANGED_CONTROLS_ONLY';shape['permittedFutureCaptureDecisionLiteral']='ACCEPT_PRODUCER2_FIXED_CAPTURE_SOURCE_FOR_CURRENT_DATA_CONTROLS_ONLY';shape['futureCaptureAcceptanceClaimed']=False;save(C/'root-ack-shape.json',shape)
old=O.read_text();before=ast.dump(ast.parse(old),indent=2,include_attributes=False);after=ast.dump(ast.parse(s),indent=2,include_attributes=False)
(C/'capture-full-typed-ast-before.txt').write_text(before+'\n');(C/'capture-full-typed-ast-after.txt').write_text(after+'\n');(C/'capture-full-typed-ast.diff').write_text(''.join(difflib.unified_diff((before+'\n').splitlines(True),(after+'\n').splitlines(True),fromfile=str(O),tofile=str(p))))
(C/'capture-full-source.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(O),tofile=str(p))))
ot=ast.parse(old);nt=ast.parse(s);changes=[]
for name in sorted({n.name for n in ot.body if isinstance(n,ast.FunctionDef)}|{n.name for n in nt.body if isinstance(n,ast.FunctionDef)}):
 a=next((n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name==name),None);b=next((n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
 aa=ast.dump(a,include_attributes=False) if a else None;bb=ast.dump(b,include_attributes=False) if b else None
 changes.append({'function':name,'classification':'AST_IDENTICAL' if aa==bb else 'RECEIPT_LITERALS_ONLY' if name=='one_scope' else 'CHANGED_FIXED_BINDING_OR_OUTPUT_VALIDATION'})
assert all(row['astIdentical'] or row['lifecycleAstIdenticalAfterDeclaredReceiptLiteralsOnly'] for row in json.loads((C/'lifecycle-ast-carry.json').read_bytes())['functions'])
save(C/'function-diff.json',{'schema':'e02-producer2-fixed-capture-function-diff-v1','old':pin(O),'current':pin(p),'functions':changes,'noCodeEvaluation':True,'lifecycleProof':pin(C/'lifecycle-ast-carry.json'),'allAdditionsDeletionsInSourceAndTypedAstDiff':True})
shutil.copyfile('/tmp/nbdp-producer2-capture-prepare.py',C/'prepare-capture-source-data.py')
shutil.copyfile('/tmp/nbdp-producer2-capture-freeze.py',C/'freeze-capture-source-data.py')
save(C/'source-preparation-failures.json',{'schema':'e02-producer2-capture-source-preparation-failures-v1','failures':[{'stage':'Initial metadata freeze after actual main SOURCE decisions','toolChunkId':'f85ab0','exitCode':1,'error':'FileNotFoundError: coordinator-source-disposition.json','cause':'Author used an incorrect coordinator disposition filename; actual existing filename is source-review-disposition.json. No main SOURCE file was changed and no control was executed.','remediation':'Read-only file discovery; corrected new capture metadata assembly to actual filename. Original tool failure remains preserved in session.'}],'projectTestsExecuted':0,'runtimeExecuted':False})
(C/'README.md').write_text('''# Fixed producer2 current35 DATA capture SOURCE

This is SOURCE preparation only. Actual main SOURCE QA/security both accepted
`ACCEPT_MINIMUM_PRODUCER_SOURCE_FOR_CHANGED_CONTROLS_ONLY` on ef91dc...;
the exact closed four-field records are pinned. No capture reviewer decision,
root acknowledgement, test result or execution grant is fabricated.

The accepted query51 capture e710... is adapted to exact frozen20/8/7 argv,
counts/names/output shapes, current producer2/config/carry/816-file dependency
closure and SDK/guard inventory manifests. The immutable main SOURCE/old roots
remain untouched. `utc`, `pin`, `strict`, `doc`, `save`, installed membership and
Popen/communicate/timeout/exact-direct-child cleanup/raw retention AST remain
unchanged; one_scope changes only receipt schema/meaning literals. Snapshot,
output validators and batch metadata bind the changed fixed scopes. Full source
and typed AST diffs identify every addition/deletion.

Node output is a single exact closed named20 JSON result with empty stderr.
The original fixed Python argv has default unittest verbosity: exact8 or7 dots,
Ran count/OK and empty stdout; no skips/errors/extra output. Three scopes stay
separate,60s each, once only, stop firstfailure and no retry/fix. Popen.communicate
retains in memory;1MiB stdout/256KiB stderr are POST_CAPTURE retention/refusal
limits, not streaming-memory caps. Raw files/metadata are exclusive private0600.

Before/after whole batch and every scope, fixed source/config/interpreter/monitor,
actual source/capture review records/root ack and current816/65/2 membership are
pinned and checked. SDK/guard inventory JSON manifests are hashed; no SDK tool,
APK/SDK-binary JSON decode or runtime provisioning occurs. Protocol crypto,
NIP44/sign/encrypt/decrypt/nativeRust/real guard/WS/network/Android/Docker/services
are excluded. Hashing/public fixed-scalar format DATA and fake fs/guard/sockets
are expressly allowed in the defined suites only after a real root release.

The actual caller must preserve each original toolName, actualArguments and
unmodifiedResponse immediately and separately from child journals. The runner
cannot invent unavailable outer-tool lifecycle fields. CaptureMatched is only
mechanical output/source/lifecycle matching, not author acceptance. Actual
independent nonauthor/nonoperator result review remains mandatory.

All prepared source was only read/written/AST-parsed;0 tests/module evaluation,
actual guards/leases/network/SDK/services/experiments occurred. A metadata-only
preparation failed on an incorrect disposition filename; the preserved additive
record names the correction. This was not a control/runtime failure. The
root-ack shape is a schema, not an acknowledgement. Future actual capture
reports must use the explicit scoped-only acceptance literal and exact runner
subject; HOLD/unknown refuse. Only then may the coordinator create/pin an actual
ack and separately release this exact once-only runner. No runtime or canonical
E02/E04/E06 gate is unlocked by preparation or main-source decisions.
''')
artifacts=[pin(q) for q in sorted(C.iterdir()) if q.is_file() and q.name!='runner-subject.json']
subject={'schema':'e02-producer2-fixed-capture-source-subject-v1','author':'/root/ordinary_api35_source','operatorIfSeparatelyReleased':'/root/ordinary_api35_source','state':'WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_CAPTURE_SOURCE_QA_SECURITY','mainSource':main,'actualMainSourceReviews':actual,'runner':pin(p),'controlPlan':pin(C/'control-plan.json'),'frozenInputs':pin(C/'frozen-inputs.json'),'fixedInputCount':len(by),'lifecycleSource':pin(O),'lifecycleAstProof':pin(C/'lifecycle-ast-carry.json'),'typedFunctionDiff':pin(C/'function-diff.json'),'preparationArtifacts':artifacts,'plannedSeparateCounts':[20,8,7],'controlsExecuted':0,'preparedModuleEvaluation':False,'runtimeExecuted':False,'rootAcknowledgementCreated':False,'futureCaptureApprovalClaimed':False,'canonicalE02':'PARTIAL22_UNCHANGED'}
save(C/'runner-subject.json',subject)
print(json.dumps({'runnerSubject':pin(C/'runner-subject.json'),'runner':pin(p),'plan':pin(C/'control-plan.json'),'frozenInputs':pin(C/'frozen-inputs.json'),'rootAckShape':pin(C/'root-ack-shape.json'),'inputCount':len(by),'mainSourceUnchanged':pin(E/'subject.json')==main,'controlsRun':0},indent=2))
