"""Reproducible SOURCE-only consumer5 draft; never import project modules/run tests."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import os
import shutil

os.umask(0o077)
REPO=Path('/home/peterhorvath/apps/bitcoin/NBDP')
OLD=REPO/'experiments/prototypes/e02_ordinary_minimum_consumer_v4'
SOURCE=Path('/Data/nbdp-e02-tooling-20261027/ordinary-consumer-preparation-r5')
OUT=Path(__file__).resolve().parent
EVIDENCE=REPO/'docs/decisions/evidence'


def pin(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def write(name,value):
    raw=(json.dumps(value,indent=2)+'\n').encode() if not isinstance(value,bytes) else value
    with (OUT/name).open('xb') as stream:stream.write(raw)
    return pin(OUT/name)


if SOURCE.exists():raise ValueError('FRESH_CONSUMER5_DRAFT_ROOT_REQUIRED')
original=[pin(p) for p in sorted(OLD.iterdir()) if p.is_file()]
if len(original)!=14:raise ValueError('EXACT_14_CONSUMER4_SOURCE_FILES_REQUIRED')
SOURCE.mkdir(mode=0o700)
for descriptor in original:shutil.copyfile(descriptor['path'],SOURCE/Path(descriptor['path']).name)
helper_bindings=json.loads(Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r3-corrected-r1/rebuilt-artifact-bindings.json').read_text())
helper=helper_bindings['helperApk'];helper_origin=helper_bindings['helperProvenance'];helper_acceptance=helper_bindings['helperAcceptance']
for descriptor in [helper,helper_origin,helper_acceptance]:
    if pin(descriptor['path'])!=descriptor:raise ValueError('CURRENT_ACCEPTED_HELPER_DRIFT')
source=(SOURCE/'consumer.py').read_text()
replacements={
"PRODUCER_SHA = 'ef91dc64189d7c47a4b4539c4dacd93a4c5c760da8f98bf1b203040bba6eeffd'":"PRODUCER_SHA = None  # Final producer3 subject is not available.",
"CONTRACT_SHA = '7fd7b71898584b4b9f90fbe9ae4601df0d1b9f3dfdc995012dfd63824fba9bfc'":"CONTRACT_SHA = None  # Bind the actual final producer contract.",
"ACTUAL35_SHA = 'aedd45eb01e6120856a8d97e8fa9811e750531ea5c3f23df8b65d302b8a8bd6c'":"ACTUAL35_SHA = None  # New once-only current producer35 result required.",
"    equal(actual['schema'], 'e02-producer2-actual35-data-result-subject-v1')":"    equal(actual['schema'], CURRENT_ACTUAL35_SCHEMA)",
"    equal(producer['schema'], 'e02-ordinary-minimum-producer2-source-subject-v1')":"    equal(producer['schema'], CURRENT_PRODUCER_SCHEMA)",
"    equal(config['amethystApk']['bytes'], 165860063)\n    equal(config['amethystApk']['sha256'], '5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5')\n    equal(config['helperApk']['sha256'], 'a680e513a9b36cab634620507b77bba36532ce13acb465a860c7bef60d23ec20')":"    equal(config['amethystApk'], CURRENT_AMETHYST_APK, 'EXACT_CURRENT_ACCEPTED_AMETHYST_ARTIFACT')\n    equal(config['helperApk'], CURRENT_HELPER_APK, 'EXACT_CURRENT_ACCEPTED_HELPER_ARTIFACT')",
}
for before,after in replacements.items():
    if source.count(before)!=1:raise ValueError('SOURCE_ANCHOR_REQUIRED:'+before[:60])
    source=source.replace(before,after)
needed=['producerSource','testSource','inputClosure','plan','release','capture','originalToolResponses','result','acceptance','qaReview','securityReview']
constants="\n# Explicit unfinished SOURCE profile; filling pins alone cannot activate this draft.\nDRAFT_FINAL_ADAPTER_READY = False\nCURRENT_PRODUCER_SCHEMA = None\nCURRENT_ACTUAL35_SCHEMA = None\nCURRENT_AMETHYST_APK = None\nCURRENT_HELPER_APK = "+repr(helper)+"\nREBUILT_CONTROL_INPUTS = "+repr({name:None for name in needed})+"\n"
anchor="RUNTIME_SCOPE = 'E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY'\n"
if source.count(anchor)!=1:raise ValueError('SCOPE_ANCHOR_REQUIRED')
source=source.replace(anchor,anchor+constants)
gate='''\n\ndef require_current_source_profile():
    """Fail closed until actual producer35/3 adapter is rendered and reviewed."""
    need(DRAFT_FINAL_ADAPTER_READY is True, 'CONSUMER5_DRAFT_NULL_NOT_READY_REQUIRES_FINAL_SOURCE_ADAPTER')
    need(all(value is not None for value in (PRODUCER_SHA, CONTRACT_SHA, ACTUAL35_SHA,
         CURRENT_PRODUCER_SCHEMA, CURRENT_ACTUAL35_SCHEMA, CURRENT_AMETHYST_APK)), 'CURRENT_PRODUCER_AND_ARTIFACT_PINS_REQUIRED')
    need(all(value is not None for value in REBUILT_CONTROL_INPUTS.values()), 'ALL_REBUILT3_SOURCE_INPUT_PLAN_RELEASE_TOOL_RESULT_ACCEPTANCE_REQUIRED')
'''
source=source.replace('\n\ndef external(',gate+'\n\ndef external(',1)
for signature in ['def control_evidence(files, descriptor, origin):','def window(files, descriptor, candidate, origin, producer):','def consume(files, manifest_pin, origin_pin):']:
    if source.count(signature)!=1:raise ValueError('ADMISSION_FUNCTION_REQUIRED')
    source=source.replace(signature,signature+'\n    require_current_source_profile()',1)
(SOURCE/'consumer.py').write_text(source)
# Current source and fixture paths stay explicitly unbound until final producer facts.
p=SOURCE/'test_source_bindings.py';text=p.read_text()
text=text.replace("PRODUCER = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/subject.json'", "PRODUCER = None  # Actual final producer3 subject path is not available.")
text=text.replace('        raw = PRODUCER.read_bytes()',"        self.assertIsNotNone(PRODUCER, 'CONSUMER5_FINAL_PRODUCER_SOURCE_REQUIRED')\n        raw = Path(PRODUCER).read_bytes()")
p.write_text(text)
p=SOURCE/'test_whole_window.py';text=p.read_text()
text=text.replace("'/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e02_ordinary_minimum_consumer_v4'",repr(str(SOURCE)))
text=text.replace("        cls.producer = Path('/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e02_ordinary_minimum_v2')", "        cls.producer = None  # Actual immutable producer3 snapshot path required.\n        if cls.producer is None: raise ValueError('CONSUMER5_FINAL_WHOLE_WINDOW_PRODUCER_REQUIRED')")
p.write_text(text)
(SOURCE/'README.md').write_text('''# Consumer5 staged SOURCE draft\n\nNULL_NOT_READY. This fourteen-file draft preserves consumer4 and all prior negative evidence. No final producer/current35/3-control or Amethyst facts are available. Source admissions refuse before old DATA can be reused; there is no final subject, model readiness or execution authority.\n\nThe preparation map outside this source root lists exact remaining patch/real-data joins. Actual new3 capture schemas/tool responses are not invented. The final adapter must be rendered from genuine current SOURCE/input/plan/release/capture/original-tool/result/independent-acceptance evidence and independently reviewed before the draft gate can be replaced. Filling pins alone cannot activate the draft.\n\nThe actual helper is current589031. Old Amethyst/helper literals and producer/actual35 hashes are removed. Runtime profileV2, two role windows, five exports, GUI/wire/observer/lease/cleanup/oracle criteria remain. Whole-window and source test paths are explicitly unbound where final producer facts are absent. No imports, tests, runtime or grants occurred.\n''')
# Preserve full criterion contract while disclosing that binding edits are staged.
p=SOURCE/'CONTRACT.md';p.write_text('DRAFT CONSUMER5 SOURCE: binding/producer/control references below are retained historical criteria context until the genuine current adapter is rendered. This draft refuses all admission; no final subject or test execution exists.\n\n'+p.read_text())
files=sorted(p for p in SOURCE.iterdir() if p.is_file())
if len(files)!=14:raise ValueError('EXACT_14_DRAFT_SOURCE_FILES_REQUIRED')
counts=[];syntax=[]
for name in ['test_data_controls.py','test_observer.py','test_source_bindings.py','test_whole_window.py']:
    parsed=ast.parse((SOURCE/name).read_text());names=[v.name for v in ast.walk(parsed) if isinstance(v,ast.FunctionDef) and v.name.startswith('test_')]
    counts.append(dict(source=pin(SOURCE/name),count=len(names),exactDefinedNames=names))
if [row['count'] for row in counts]!=[86,36,8,9]:raise ValueError('ORIGINAL_TOP_LEVEL_TEST_SCOPE_COUNTS_REQUIRED')
for path in files:
    if path.suffix=='.py':ast.parse(path.read_text());syntax.append(pin(path))
for descriptor in original:
    if pin(descriptor['path'])!=descriptor:raise ValueError('ORIGINAL_CONSUMER4_CHANGED')
preserved=write('preserved-consumer4-sources.json',dict(schema='e02-consumer5-preserved-source-v1',sources=original,unchanged=True))
known=[pin(EVIDENCE/'e02-ordinary-minimum-consumer-preparation-r4/subject.json'),pin(EVIDENCE/'e02-consumer4-data-run-r1/acceptance.json'),pin(EVIDENCE/'e02-final-mile-map-20261028/mapping.json'),helper,helper_origin,helper_acceptance]
missing={name:None for name in ['producerSubject','producerSubjectSchema','producerContract','producerActual35','producerActual35Schema','producerActual35Acceptance','producerSourceReviews','amethystApk','amethystProvenance','amethystAcceptance']}
missing['producerRebuilt3']={name:None for name in needed}
inputs=write('draft-input-manifest.json',dict(schema='e02-consumer5-draft-source-inputs-v1',state='NULL_NOT_READY_NOT_FINAL_SOURCE',knownInputs=known,missingCurrentInputs=missing,sourceFiles=[pin(p) for p in files],runtimeSdkUnchanged='/tmp/nbdp-e02-api35-fixture-r2/sdk',guardMembers=522,oldCurrentResultTransfer=False))
plan=write('preparation-map.json',dict(schema='e02-consumer5-staged-preparation-map-v1',state='DRAFT_ONLY_NO_EXECUTION_OR_FINAL_SUBJECT',order=['Actual Amethyst artifact/source/acceptance','Actual immutable producer3 source/contract/bothconfigs/16workers/fixture bindings','Fresh current producer20/8/7 result with source35 join and actual independent acceptance','Separately SOURCE-reviewed new3 capture SOURCE/input/plan/release/originaltool/result/acceptance','Render new3 consumer adapter using genuine exact schemas and tool-response shapes','Replace all explicit NULL bindings and finalize14source/whole-window/source-test closure','Independent final SOURCE reviews then fixed86/36/8/9 DATA and independent acceptance','Completion successor after final consumer freeze; genuine role windows/exports/wholeconsume/primary/finalize remain'],producer35=dict(executedScopes={'observation-model':20,'public-identity-metadata':8,'producer2-source-wiring':7},required='current actual35.producerSource == actual producer3 subject; all source-before/after/rawstream/naturalexit/actualtool/review checks preserved; no historical transfer'),rebuilt3=dict(status='UNRENDERED_REQUIRED_EXACT_ACTUAL_DAG',requiredNodes=needed,candidateControlFieldProposal='producerRebuiltControls',codeRenderPoints=['control_evidence closed metadata DTO and required new3 prerequisite','new3 exact source/test/inputs/capture plan/release to current producer and immutable input closure','exact real result3 named tests/natural0/reap/fullEOF/no truncation/source unchanged beforeafter','original actual outer structured tool receipt agreement; never fabricate nested/direct-tool origins','exact independent acceptance/QA/security subject joins and independent origin checks'],forbidden='No optional/skipped node may qualify. No invented source/acceptance/capture/result/tool schema. DRAFT_FINAL_ADAPTER_READY remainsFalse until final actual adapter SOURCE is implemented/reviewed.'),artifactJoins=dict(amethyst=None,helper=helper,required='exact config artifact descriptors match actual independently accepted producer bindings, API35SDK434/image/guard522 unchanged; no legacy5165/a680 fallback'),sourceSchema=None,actual35Schema=None,sourceCount=14,runtimeStagedProducerCount=16,wholeWindowProducerSnapshot=None,sourceTestProducerSubject=None,controlScopes=[86,36,8,9],controlsExecuted=0,coverageGap='Whole-window positives are not full top-level consume positives; immutable current candidate/history/origin/control graph and genuine runtime remain required.'))
controls=write('proposed-control-plan-draft.json',dict(schema='e02-consumer5-draft-control-definitions-v1',state='NOT_READY_NULL_SOURCE_AND_ADAPTER_NO_EXECUTION_AUTHORITY',scopes=counts,controlsExecuted=0,requires='Real producer/current35/new3/APK bindings, completed actual adapter, full final SOURCE review, separate finite current model capture/root release and independent DATA review',priorFourScopesRerun=False))
patch=''.join(''.join(difflib.unified_diff((OLD/p.name).read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(OLD/p.name),tofile=str(p))) for p in files)
diff=write('staged-source.diff',patch.encode())
static=write('static-draft-checks.json',dict(schema='e02-consumer5-draft-static-checks-v1',syntax=syntax,method='ast.parse and source byte/hash comparison only',importsExecuted=False,modelsExecuted=0,runtimeExecuted=False,sourceCount=14,originalConsumer4Unchanged=True,finalSubjectCreated=False))
pointer=write('draft-pointer.json',dict(schema='e02-consumer5-draft-pointer-v1',state='UNFROZEN_NULL_NOT_READY_STAGED_PATCH_NOT_FINAL_SOURCE',sourceRoot=str(SOURCE),sourceFiles=[pin(p) for p in files],sourceCount=14,preservedSources=preserved,inputs=inputs,preparationMap=plan,controlDefinitions=controls,fullDiff=diff,staticChecks=static,preparationScript=pin(__file__),modelsExecuted=0,finalSubjectCreated=False,runtimeOrGrantCreated=False,ordinaryRowsQualified=0))
print(json.dumps(dict(pointer=pointer,sourceRoot=str(SOURCE),sourceCount=14,definedScopes=[row['count'] for row in counts],modelsExecuted=0,finalSubjectCreated=False)))
