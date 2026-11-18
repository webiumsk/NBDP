"""Final producer SOURCE metadata/read-only input hashing; never runs controls."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import os
import stat
import time

os.umask(0o077)
REPO=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=REPO/'docs/decisions/evidence'
OLD=Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r3-corrected-r1')
SOURCE=Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
OUT=Path(__file__).resolve().parent
BASELINE=REPO/'experiments/prototypes/e02_ordinary_minimum_v2'
START=time.monotonic()


def pin(p):
    p=Path(p);assert p.is_absolute() and not p.is_symlink() and p.is_file()
    h=hashlib.sha256();count=0
    with p.open('rb') as f:
        while b:=f.read(1048576):count+=len(b);h.update(b)
    return dict(path=str(p),bytes=count,sha256=h.hexdigest())


def put(name,value):
    b=(json.dumps(value,indent=2)+'\n').encode() if not isinstance(value,bytes) else value
    with (OUT/name).open('xb') as f:f.write(b)
    return pin(OUT/name)


def defs(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}


original=[pin(p) for p in sorted(OLD.rglob('*')) if p.is_file()]
sources=[pin(p) for p in sorted(SOURCE.iterdir()) if p.is_file()]
assert len(sources)==31
configs=[pin(OUT/(role+'-run-config.json')) for role in ('incoming','archive')]
bindings=json.loads((SOURCE/'rebuilt-artifact-bindings.json').read_text())
assert all(bindings[k] is not None for k in ('amethystApk','amethystProvenance','amethystAcceptance','amethystAcceptanceDecision'))
assert bindings['state']=='SOURCE_BOUND_REQUIRES_REVIEW_AND_ROLE_RELEASE'
worker_names=('supervisor.py','lease_guard.py','android_driver.py','ui-plan.json','fixture.mjs','fixture-plan.json','minimum-plan.json','business-rumor.json','chat-rumor.json','exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json','capture-budget.mjs','exchange-adapter.mjs','proxy-observer.mjs')
workers=[pin(SOURCE/name) for name in worker_names]
for d in configs:
    value=json.loads(Path(d['path']).read_text());assert value['sourceAndDependencyPins']==workers and value['originalLeaseSeconds']==1800 and value['amethystApk']==bindings['amethystApk'] and value['helperApk']==bindings['helperApk']
assert len({json.loads(Path(d['path']).read_text())['runId'] for d in configs})==2
scopes=[]
for name,count,scope in [('test_observation_model.mjs',20,'observation-model'),('test_public_identity_metadata.py',8,'public-identity-metadata'),('test_producer2_source.py',7,'producer2-source-wiring'),('test_producer3_bindings.py',3,'rebuilt-artifact-bindings')]:
    names=[]
    if name.endswith('.py'):
        parsed=ast.parse((SOURCE/name).read_text())
        for cls in parsed.body:
            if isinstance(cls,ast.ClassDef):names += [cls.name+'.'+fn.name for fn in cls.body if isinstance(fn,ast.FunctionDef) and fn.name.startswith('test_')]
        assert len(names)==count
    scopes.append(dict(scope=scope,count=count,source=pin(SOURCE/name),exactDefinedPythonNames=names,format='NODE_JSON' if name.endswith('.mjs') else 'QUIET_UNITTEST_DOTS',captureGroup='CURRENT35' if count!=3 else 'SEPARATE_REBUILT3'))
control_plan=put('control-plan.json',dict(schema='e02-producer3-final-source-control-plan-v1',state='DEFINED_ONLY_REQUIRES_INDEPENDENT_SOURCE_AND_SEPARATE_CAPTURE_SOURCE_REVIEW',sourceRoot=str(SOURCE),python=pin('/home/peterhorvath/.miniforge3/bin/python3.13'),node=pin('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'),scopes=scopes,current35Counts=[20,8,7],rebuiltBindingCount=3,twoSeparateOnceOnlyCaptures=True,controlsExecuted=0,historicalResultsTransferred=False,quietChoice='New final generation only explicitly uses unittest.main(verbosity=1) for3; exact source definitions remain named/pinned; original verbose pre-APK SOURCE and earlier planned parser requirement remain historical.',limits=dict(commandSeconds=60,directChildReapSeconds=3,stdoutRetentionBytes=262144,stderrRetentionBytes=1048576),limitsMeaning='Capture SOURCE must specify exact effective caps and post-capture retention semantics; no streaming-memory or60s-sufficiency claim.',requires=['Independent exact producer SOURCE QA/security','Separately frozen/reviewed current35 and separate3 capture SOURCE/current input manifest','Root one-use finite DATA capture releases','Actual counts/streams/tool custody/full unchanged inputs and independent acceptance'],excluded=['Android/SDK tools','native binary execution','services','real crypto','runtime role grants','ordinary-client qualification']))
functions_before=defs(OLD/'supervisor.py');functions_after=defs(SOURCE/'supervisor.py')
assert set(functions_before)==set(functions_after)
changed=[name for name in functions_before if functions_before[name]!=functions_after[name]]
assert changed==['verify_rebuilt_artifacts']
for name in worker_names:
    if name not in ('supervisor.py','fixture-plan.json'):assert (SOURCE/name).read_bytes()==(OLD/name).read_bytes(),name
for name in ['test_observation_model.mjs','test_public_identity_metadata.py','test_producer2_source.py']:assert (SOURCE/name).read_bytes()==(OLD/name).read_bytes()
original_blueprint=next(x for x in ast.parse((SOURCE/'supervisor.py').read_text()).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REVIEWED_RUNTIME_INPUTS' for t in x.targets))
blueprint=ast.literal_eval(original_blueprint.value)
legacy_source=json.loads((E/'e02-ordinary-minimum-preparation-r2/subject.json').read_text())
for d in legacy_source['configurations']:
    c=json.loads(Path(d['path']).read_text());assert {k:c[k] for k in blueprint}==blueprint
proof=put('source-equivalence.json',dict(schema='e02-producer3-final-source-equivalence-v1',baselineProducer2Subject=pin(E/'e02-ordinary-minimum-preparation-r2/subject.json'),correctedPreApkSourcePacket=pin(E/'e02-ordinary-minimum-preparation-r3-corrected-r1/source-packet.json'),correctedPreApkReviewSupplement=pin(E/'e02-ordinary-minimum-preparation-r3-corrected-r1/review-input-supplement.json'),actualAcceptedArtifactBindings=pin(E/'e02-amethyst-clock90-r8-actual-20261028/accepted-producer-bindings.json'),allOriginalPreApkFiles=original,changedExecutableFunctionsVersusCorrectedPreApk=changed,change='Missing acceptance/provenance authority members now refuse through existing explicit RuntimeError guard using .get; exact fixed decisions/schemas/True qualification and caller/immutable-metadata joins unchanged.',runtimeClassAndEveryOtherFunctionAstIdentical=True,allOtherWorkerBytesUnchanged=True,publicScalarAndOriginalWiringTestBytesUnchanged=True,threeTestMethodsExpandedWithinExistingCount=True,quietVerbosity=1,actualControlExecutions=0,noHistoricalQualificationTransfer=True))
# Existing consumer DTO calls this componentCarry; it records source equality only,
# not permission to inherit a historical control execution.
modules=[]
for name in ['android_driver.py','lease_guard.py','fixture.mjs','exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json','capture-budget.mjs','exchange-adapter.mjs','proxy-observer.mjs','business-rumor.json','chat-rumor.json','minimum-plan.json','ui-plan.json']:
    assert (BASELINE/name).read_bytes()==(SOURCE/name).read_bytes()
    modules.append(dict(original=pin(BASELINE/name),current=pin(SOURCE/name),classification='BYTE_IDENTICAL'))
matrix=put('component-matrix.json',dict(schema='e02-producer3-source-equivalence-matrix-v1',state='SOURCE_CONTEXT_ONLY_FRESH_CURRENT_CONTROLS_REQUIRED',modules=modules,functionProofs=[proof],ordinaryBaseline=dict(source=pin(E/'e02-ordinary-minimum-preparation-r2/subject.json'),meaning='SOURCE_HISTORY_ONLY_NO_EXECUTION_TRANSFER'),diagnosticBaseline=dict(source=pin(E/'e02-transport-query-diagnostic-preparation-r2/subject.json'),meaning='SOURCE_HISTORY_ONLY_NO_EXECUTION_TRANSFER'),requiredCurrentScopes=[20,8,7,3],currentControlExecutions=0,historicalControlCarry=False))
# Union of actual current DATA read operands. Source subject/closure self-edges
# are added downstream by capture assembly, avoiding a self-hashing cycle.
files={}
def add(d):
    assert set(d)=={'path','bytes','sha256'}
    old=files.get(d['path']);assert old is None or old==d
    files[d['path']]=d
for d in sources+configs+[control_plan,proof,matrix,pin(__file__),pin(OUT/'materialization-plan.json'),pin(OUT/'materialization-original-tools.json')]:add(d)
for key in ('amethystApk','amethystProvenance','amethystAcceptance','helperApk','helperProvenance','helperAcceptance','rustBinary','acceptedE01','acceptedE01Acceptance','originalCanonicalE01'):add(bindings[key])
fixture=json.loads((SOURCE/'fixture-plan.json').read_text())
for d in [*fixture['pins'].values(),*fixture['oracles'].values(),*fixture['dependencyFiles']]:add(dict(path=d['source'],bytes=d['bytes'],sha256=d['sha256']))
for rel,sha in bindings['expectedOriginal19Sources'].items():
    d=pin(REPO/'experiments'/rel);assert d['sha256']==sha;add(d)
for name,d in blueprint.items():add(d)
for directory,names in [('experiments/prototypes/e02_transport_query_diagnostic_v2',['exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json','lease_guard.py','supervisor.py']),('experiments/prototypes/e02_ordinary_minimum_v1',['fixture.mjs','supervisor.py','business-rumor.json','chat-rumor.json','fixture-plan.json','minimum-plan.json'])]:
    for name in names:add(pin(REPO/directory/name))
for name in ['public-scalar-format-data.json','oracle-provenance.json']:add(pin(E/'e02-ordinary-minimum-preparation-r2'/name))
for path in ['/home/peterhorvath/.miniforge3/bin/python3.13','/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node']:add(pin(path))
for d in legacy_source['configurations']:add(d)
for path in [E/'e02-producer3-anticipatory-review-20261028/qa-findings.json',E/'e02-producer3-anticipatory-review-20261028/security-findings.json']:add(pin(path))
# Full positive verify_config read trees: derive leaf authority from the immutable
# reviewed SDK/guard inventories, never current-file self-certification.
sdk_config=json.loads(Path(configs[0]['path']).read_text());sdk=Path(sdk_config['sdkRoot']);guard=Path(sdk_config['guardBundleRoot'])
sdk_index=json.loads(Path(blueprint['sdkInventory']['path']).read_text());guard_index=json.loads(Path(blueprint['guardBundleInventory']['path']).read_text())
sdk_expected={};guard_expected={}
for row in sdk_index['files']:
    assert 'symlink' not in row
    d=dict(path=str(sdk/row['path']),bytes=row['size'],sha256=row['sha256']);add(d);sdk_expected[row['path']]=d
for name,row in guard_index['files'].items():
    d=dict(path=str(guard/name),bytes=row['bytes'],sha256=row['sha256']);add(d);guard_expected[name]=d
assert len(sdk_expected)==434 and len(guard_expected)==522
# This is read-only SOURCE input reconciliation, not a control or role execution.
observed=[]
for path,d in sorted(files.items()):
    assert pin(path)==d,path
    st=Path(path).stat();observed.append(dict(**d,mode=oct(stat.S_IMODE(st.st_mode))))

def tree_rows(root,expected):
    rows=[];seen=set()
    for path in sorted(root.rglob('*')):
        rel=str(path.relative_to(root));mode=oct(stat.S_IMODE(path.lstat().st_mode))
        if path.is_symlink():
            assert path.resolve(strict=True).is_relative_to(root)
            rows.append(dict(path=rel,type='symlink',mode=mode,target=str(path.readlink())))
        elif path.is_dir():rows.append(dict(path=rel,type='directory',mode=mode))
        else:
            assert path.is_file() and rel in expected,(root,rel)
            seen.add(rel);rows.append(dict(path=rel,type='file',mode=mode,bytes=expected[rel]['bytes'],sha256=expected[rel]['sha256']))
    assert seen==set(expected)
    return rows
sdk_rows=tree_rows(sdk,sdk_expected);guard_rows=tree_rows(guard,guard_expected)
trees=put('source-input-trees.json',dict(schema='e02-producer3-current-readonly-input-trees-v1',meaning='Current SOURCE preparation observation/immutable inventory reconciliation, not race-free custody, model execution or Android admission. Capture must rejoin fresh before/after.',sdk=dict(root=str(sdk),authority=blueprint['sdkInventory'],regularFiles=434,members=sdk_rows),guard=dict(root=str(guard),authority=blueprint['guardBundleInventory'],regularFiles=522,members=guard_rows)))
add(trees)
manifest=put('source-input-manifest.json',dict(schema='e02-producer3-final-source-inputs-v1',scope='CURRENT_SOURCE_AND_DECLARED_CONTROL_READ_OPERANDS_NOT_EXECUTION',files=[files[k] for k in sorted(files)],count=len(files),preparationCurrentByteModeObservations=observed,positiveConfigTreeObservation=trees,interpreter=pin('/home/peterhorvath/.miniforge3/bin/python3.13'),node=pin('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'),runtimeWorkerCount=16,sdkRegularFiles=434,guardRegularFiles=522,materializationOnlyInvocations=2,controlsExecuted=0,sourceSubjectSelfEdge='Downstream capture assembler must add final producer subject, this manifest, capture SOURCE/plan/release/interpreters and all own read operands; derive actual closed count <=4096, never reuse old957.',raceFreeOrRuntimeCustodyClaim=False))
full_diff=put('final-source.diff',''.join(''.join(difflib.unified_diff((OLD/name).read_text().splitlines(True),(SOURCE/name).read_text().splitlines(True),fromfile=str(OLD/name),tofile=str(SOURCE/name))) for name in ['supervisor.py','test_producer3_bindings.py','fixture-plan.json','runtime-plan.json','rebuilt-artifact-bindings.json','README.md']).encode())
syntax=[]
for d in sources:
    p=Path(d['path'])
    if p.suffix=='.py':ast.parse(p.read_text());syntax.append(d)
static=put('static-source-checks.json',dict(schema='e02-producer3-final-static-source-checks-v1',method='ast.parse/hash/JSON/source comparison and readonly input-tree hashing only; no controls or project-module imports during this metadata script',syntax=syntax,sourceFiles=31,workerFiles=16,controlsExecuted=0,actualConfigMaterializations=2,roleRuntimeExecuted=False,roleGrantsCreated=False))
subject=put('subject.json',dict(schema='e02-ordinary-minimum-producer3-source-subject-v1',author='/root/r5_plan_fix',coordinator='/root',state='WRITES_STOPPED_PENDING_INDEPENDENT_SOURCE_QA_SECURITY',profileId='e02-ordinary-minimum-rs-two-role-v2',scope='CURRENT_REBUILT_ARTIFACT_PRODUCER_SOURCE_ONLY_NO_EXECUTION_AUTHORITY',sources=sources,runtimeSourceCount=16,configurations=configs,typedContract=pin(SOURCE/'EXPORT-CONTRACT.md'),controlPlan=control_plan,componentCarry=matrix,pythonTypedAstCarry=proof,sourceDataInputClosure=manifest,artifactBindings=pin(SOURCE/'rebuilt-artifact-bindings.json'),fullSourceDiff=full_diff,syntaxOnly=static,definedControlScopes=[20,8,7,3],currentProjectControlsExecuted=0,materializationOnlyInvocations=2,actualRuntimeOrExperiments=False,rootGrantOrLeaseCreated=False,historicalControlQualificationTransfer=False,oldSourcePreserved=True,oldFailedWholeWindowDonation=False,authorApprovesOwnResults=False,canonicalE02='PARTIAL22_UNCHANGED',architecturalBlockersUnchanged=['Q01','Q08','Q13','Q15','Q27'],remainingPrerequisites=['Independent producer SOURCE review','Separately reviewed fresh35 and separate3 capture SOURCE and complete actual input closure/root finite DATA release','Independent actual control DATA acceptance','Current consumer/completion source/control bindings then genuine role windows/exports/wholeconsume/final-profile primary/integration'],productOwnerInputRequired=False))
for d in original:assert pin(d['path'])==d
assert not Path('/Data/nbdp-e02-tooling-20261027/ordinary-minimum-r3').exists()
packet=put('source-packet.json',dict(schema='e02-producer3-final-source-packet-v1',author='/root/r5_plan_fix',state='FROZEN_SOURCE_PENDING_QA_SECURITY_NO_CONTROL_OR_RUNTIME_AUTHORITY',subject=subject,sourceRoot=str(SOURCE),sources=sources,workerSources=workers,configurations=configs,controlPlan=control_plan,sourceInputManifest=manifest,inputTreeObservation=trees,sourceEquivalence=proof,componentMatrix=matrix,acceptedArtifactBindings=pin(E/'e02-amethyst-clock90-r8-actual-20261028/accepted-producer-bindings.json'),actualMaterializationTools=pin(OUT/'materialization-original-tools.json'),sourcePreparationScript=pin(__file__),staticChecks=static,definedControlScopes=[20,8,7,3],controlModelsExecuted=0,materializationOnlyInvocations=2,runtimeOrGrantCreated=False,originalCorrectedPreApkFilesUnchanged=True,remainingGaps=['Independent final SOURCE review','Capture-agent final current35 and separate3 SOURCE/schema/completeinput/once-release review; no current capture is released by this producer subject','Actual control DATA and independent acceptance','Consumer/completion/render and genuine ordinary-client evidence'],preparationElapsedSeconds=time.monotonic()-START))
print(json.dumps(dict(subject=subject,packet=packet,sourceRoot=str(SOURCE),controlPlan=control_plan,inputManifest=manifest,inputCount=len(files),sdkFiles=434,guardFiles=522,scopes=[20,8,7,3],controlsExecuted=0,materializations=2,roleRuntime=False)))
