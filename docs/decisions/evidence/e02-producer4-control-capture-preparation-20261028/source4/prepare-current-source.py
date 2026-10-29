"""Bounded metadata/source preparation only. Never import or execute target code.

Input selection is an explicit reviewed manifest union and named authority fields.
This script hashes declared raw bytes, never copies binaries, keys or SDK trees.
"""
import ast,hashlib,json,os,pathlib,re,shlex,stat,time
R=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP')
E=R/'docs/decisions/evidence'
D=pathlib.Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r1/source4')
OUT=E/'e02-producer4-control-capture-preparation-20261028/source4'
UP=E/'e02-producer4-control-capture-preparation-20261028'
S=pathlib.Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r4-source4-metadata-r1/subject.json')
AC=E/'e02-producer4-source4-acceptance-20261028'
start=time.monotonic();seen={};coverage={};authority_docs={}

def need(v,m):
 if not v:raise ValueError(m)
def raw_pin(p,expected=None):
 p=pathlib.Path(p);need(p.is_absolute() and str(p)==os.path.normpath(str(p)),'CANONICAL')
 for q in [p,*p.parents]:need(not q.is_symlink(),'NO_SYMLINK:'+str(q))
 st=p.lstat();need(stat.S_ISREG(st.st_mode) and st.st_size<=2147483648,'RAW_REGULAR_2G:'+str(p))
 need(not any(v in str(p).lower() for v in ('.keystore','.jks','android-state','docker-config','relay-data')),'EXCLUDED_SENSITIVE_PATH')
 h=hashlib.sha256();n=0;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 def identity(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 try:
  need(identity(os.fstat(fd))==identity(st),'OPEN_DRIFT')
  while True:
   b=os.read(fd,1048576)
   if not b:break
   n+=len(b);need(n<=st.st_size and n<=2147483648,'STREAM_BOUND');h.update(b)
  need(identity(os.fstat(fd))==identity(st),'FD_DRIFT')
 finally:os.close(fd)
 need(identity(p.lstat())==identity(st) and n==st.st_size,'PATH_DRIFT')
 pin=dict(path=str(p),bytes=n,sha256=h.hexdigest())
 need(expected is None or pin==expected,'EXPECTED_PIN_MISMATCH:'+str(p))
 return pin,stat.S_IMODE(st.st_mode)
def jread(p):
 p=pathlib.Path(p);need(p.stat().st_size<=16777216,'NAMED_METADATA_16M:'+str(p));return json.loads(p.read_text())
def write(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);need(not p.exists(),'NO_OVERWRITE:'+str(p));raw=x if isinstance(x,bytes) else (json.dumps(x,indent=2)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:need(f.write(raw)==len(raw),'SHORT_WRITE')
 return raw_pin(p)[0]
def add(d,role,origin,category=None):
 need(set(d)=={'path','bytes','sha256'},'EXACT_DESCRIPTOR');path=d['path']
 if path in seen:need(seen[path]['pin']==d,'NO_CONFLICT:'+path)
 else:
  p,mode=raw_pin(path,d);seen[path]=dict(pin=p,mode=mode,role=role,origin=origin);need(len(seen)<=20000,'MAX_FILES')
 if category is not None:
  group=coverage.setdefault(category,[])
  if d not in group:group.append(d)
 return d
def addpath(p,role,origin,category=None):return add(raw_pin(p)[0],role,origin,category)
def authority(d,origin,category='namedMetadataAuthorities'):
 add(d,'METADATA_AUTHORITY',origin,category);x=jread(d['path']);authority_docs[d['path']]=x;return x

def ast_literals(p):
 tree=ast.parse(p.read_text());values={}
 for n in tree.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:values[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 return values
# Refuse changing previous frozen results or partially rerunning preparation.
need(not (OUT/'review-entrypoint.json').exists(),'FROZEN_ENTRY_EXISTS')
source=jread(S);sp=raw_pin(S)[0];ap=raw_pin(AC/'acceptance.json')[0];clock=raw_pin(UP/'root-clock-source-selection.json')[0]
need(sp['sha256']=='34802f702c863e5cd81e865eec5de7736615ceffc683a8a9f9eb4192e857e66e' and ap['sha256']=='b1ab95f20cd608024c7b4dee011063c760d35109aa20a0dca3d1c1aa81098312','CURRENT_ACCEPTED_SOURCE_ONLY')
# Last CODE binding change; activation remains separately gated own metadata.
p=D/'capture.py';text=p.read_text();need('CODE_READY=True' in text,'BOUND_PREDECESSOR_CODE')
text=text.replace('CODE_READY=False\nCURRENT_PRODUCER_SOURCE=None\nCURRENT_PRODUCER_ACCEPTANCE=None\nCLOCK_SELECTION=None','CODE_READY=True\nCURRENT_PRODUCER_SOURCE='+repr(sp)+'\nCURRENT_PRODUCER_ACCEPTANCE='+repr(ap)+'\nCLOCK_SELECTION='+repr(clock))
p.write_text(text);os.chmod(p,0o600)
modules=sorted(D.glob('*.py'))
for p in modules:compile(ast.parse(p.read_text()),str(p),'exec')
const=ast_literals(D/'contracts.py');files=const['FILES'];keys=const['MODEL_KEYS'];limits=const['LIMITS'];ledger=const['LEDGER']
counts=[source['modelsDefined'][k] for k in keys];need(counts==[123,33,29,16,20,10,11,8,7,3] and sum(counts)==260,'ACTUAL260')
cases=[c.name+'.'+f.name for c in ast.parse((D/'test_admission.py').read_text()).body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')];need(len(cases)==21,'ACTUAL21_DEFINED')
known_pin=raw_pin(UP/'root-known-actors.json')[0]
contract_pins=[known_pin,write(D/'contracts/root-known-actors.json',(UP/'root-known-actors.json').read_bytes())]
for name in ('producer-source-acceptance-contract.json','capture-source-acceptance-contract.json','capture-admission-data-acceptance-contract.json','root-clock-source-selection.json'):
 contract_pins.append(write(D/'contracts'/name,(UP/name).read_bytes()))
admission_plan=write(D/'admission-plan.json',dict(schema='e02-producer4-capture-admission-plan-v1',caseNames=cases,modelsDefined=len(cases),source=raw_pin(D/'test_admission.py')[0],producerSource=sp,modelsExecuted=0,scope='PURE_MOCKED_CAPTURE_ADMISSION_ONLY',targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0,sourceReviewRequired=True,releaseRequired=True))
code_pins=[raw_pin(p)[0] for p in modules]+contract_pins+[admission_plan,raw_pin(pathlib.Path(__file__).resolve())[0]]
method=write(D/'code-subject.json',dict(schema='e02-producer4-control-capture-code-subject-v1',authors=['/root/r5_plan_fix'],producerSource=sp,knownActors=known_pin,codeOnly=True,sources=code_pins,admissionModelsDefined=21,admissionModelsExecuted=0,targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0,excludedMutableMetadata=['execution-plan','reviews','acceptances','root-ack','runtime-output'],sourceReadiness='REQUIRES_INDEPENDENT_SOURCE_REVIEW_AND_SEPARATE_ADMISSION_DATA',selfApproval=False))
# Explicit baseline selection is input provenance only, never old DATA transfer.
bp=E/'e02-producer3-current-controls-preparation-20261028/source4/capture-a/frozen-inputs.json';baseline=jread(bp)
for d in baseline['files']:
 path=d['path'];role='BASELINE_READ'
 if path.startswith('/tmp/nbdp-e02-api35-fixture-r2/sdk/'):role='SDK_FILE'
 elif path.startswith('/tmp/nbdp-e02-minimal-rs-v7/guard-python/'):role='GUARD_FILE'
 elif path.startswith(str(R/'experiments/node_modules')+'/'):role='NODE_DEP_FILE'
 add(d,role,'EXPLICIT_ACCEPTED_PRODUCER3_SOURCE4_1889_INPUT_BASELINE_ONLY')
addpath(bp,'METADATA_AUTHORITY','BASELINE_SELECTION_AUTHORITY','baselineInputAuthority')
for name,group in baseline['requiredCoverage'].items():
 for d in group:add(d,seen[d['path']]['role'],'EXPLICIT_BASELINE_NAMED_READ', 'baseline_'+name)
add(sp,'METADATA_AUTHORITY','CURRENT_ACCEPTED_METADATA_R1_SUBJECT','currentSubjectControlPlan')
add(source['controlPlan'],'METADATA_AUTHORITY','CURRENT_OVERLAY_CONTROLPLAN','currentSubjectControlPlan')
for d in source['sources']:add(d,'SOURCE','CURRENT_SOURCE_DECLARED61','allCurrentSourceMembers')
for d in source['runtimeSources']:add(d,'SOURCE','CURRENT_RUNTIME22','all22RuntimeWorkers')
for d in source['configurations'].values():add(d,'METADATA_AUTHORITY','CURRENT_BOTH_ROLE_CONFIGS','bothCurrentConfigurations')
for d in code_pins:add(d,'SOURCE','CURRENT_CAPTURE_IMMUTABLE_CODE','allCaptureCodeAndAdmissionDefinitions')
addpath(E/'e02-producer4-capture-source3-fresh-reviewer-freeze-20261028/findings-and-disposition.json','METADATA_AUTHORITY','PRESERVED_SOURCE3_HOLD_FINDINGS','predecessorHoldAuthority')
for name in ('acceptance.json','qa.json','security.json','lineage.json'):authority(raw_pin(AC/name)[0],'CURRENT_ROOT_ACCEPTANCE_AND_LINEAGE','currentAcceptedSourceAuthority')
lineage=jread(AC/'lineage.json')
for key in ('sourceFreeze','birthEvidence','fullSubstantiveReview','metadataEntry'):authority(lineage[key],'EXPLICIT_ROOT_LINEAGE_'+key,'currentAcceptedSourceAuthority')
entry=jread(lineage['metadataEntry']['path'])
for key in ('packet','archiveManifest','source3Findings','predecessorPreservation','metadataCorrection'):add(entry[key],'METADATA_AUTHORITY','EXPLICIT_ENTRY_'+key,'currentAcceptedSourceAuthority')
for key in ('originalProducer3Source','latestFailedRunContext','predecessorSource','originalLeaseCore','terminalAliasAudit','source1Preservation','source1Source2Preservation','source1Source2Source3Preservation'):
 if key in source and type(source[key]) is dict:add(source[key],'METADATA_AUTHORITY','EXPLICIT_CURRENT_SOURCE_'+key,'currentLineageAndOriginalCore')
for d in source['methodAdoptions'] if type(source['methodAdoptions']) is list else source['methodAdoptions'].values():
 if type(d) is dict and set(d)=={'path','bytes','sha256'}:add(d,'METADATA_AUTHORITY','EXPLICIT_METHOD_ADOPTION','currentLineageAndOriginalCore')
for d in source['dataPrerequisitesOnly'].values():add(d,'ARTIFACT','EXPLICIT_SOURCE_PREREQUISITE','currentRuntimePrerequisites')
by_name={pathlib.Path(d['path']).name:d for d in source['sources']};bindings=authority(by_name['rebuilt-artifact-bindings.json'],'CURRENT_REBUILT_BINDINGS')
for key in ('amethystApk','amethystProvenance','amethystAcceptance','helperApk','helperProvenance','helperAcceptance','rustBinary','acceptedE01','acceptedE01Acceptance','originalCanonicalE01'):
 add(bindings[key],'NATIVE' if key=='rustBinary' else 'ARTIFACT','EXPLICIT_BINDINGS_'+key,'currentArtifactNativeE01')
# Original19 expectedSource map contains hashes; explicitly use reviewed baseline rows.
for d in baseline['requiredCoverage']['original19']:add(d,'CANONICAL','ORIGINAL19_E01_SOURCE_EQUALITY','original19')
amethyst=authority(bindings['amethystProvenance'],'CURRENT_APK_SOURCE_LINKED_ORIGIN')
for key in ('controller','innerBuild','innerSourceEquality','postcheck','externalSourceEquality','rebuiltMetadata','signature','badging','actualTextCopies','launch','terminal','rootAuthorization','modelData','clockData','installedSdkData'):
 add(amethyst[key],'OPAQUE_PREREQUISITE','EXPLICIT_AMETHYST_'+key,'amethystNamedProvenance')
# Copy descriptors are HOST byte operands only. Their original/guest/archive/template
# descriptors are context, not recursively traversed. 26MiB inventories stay opaque.
copy_manifest=authority(amethyst['actualTextCopies'],'NAMED_APK_TEXT_COPY_MANIFEST')
for row in copy_manifest['copies']:add(row['copy'],'OPAQUE_PREREQUISITE','EXPLICIT_APK_RETAINED_COPY_ONLY','amethystRetainedProvenanceBytes')
helper=authority(bindings['helperProvenance'],'CURRENT_HELPER_ORIGIN')
for key in ('buildResult','outerToolReceipt','before','after'):add(helper[key],'OPAQUE_PREREQUISITE','EXPLICIT_HELPER_'+key,'helperNamedProvenance')
for row in helper['retainedCopies']:
 d=row.get('copy',row.get('retained')) if isinstance(row,dict) else None
 need(type(d) is dict and set(d)=={'path','bytes','sha256'},'EXPLICIT_HELPER_COPY_SCHEMA');add(d,'OPAQUE_PREREQUISITE','EXPLICIT_HELPER_RETAINED_COPY_ONLY','helperNamedProvenance')
# Fixed interpreter/finite wrapper tools. No command/tool is executed.
tools={k:baseline[k] for k in ('node','python')}
tools.update({k:raw_pin('/usr/bin/'+k)[0] for k in ('timeout','env')})
for d in tools.values():add(d,'TOOL','FIXED_HOST_TOOL','hostTools')
# Complete tree membership, including directories and the two reviewed safe links.
trees_authority=E/'e02-ordinary-minimum-producer-final-preparation-r3-20261028/source-input-trees.json';trees=jread(trees_authority);addpath(trees_authority,'METADATA_AUTHORITY','FIXED_TREE_MEMBERSHIP_AUTHORITY','fullMembershipAuthorities')
def walk(root,links=False):
 root=pathlib.Path(root);need(not root.is_symlink(),'NO_ROOT_LINK');out=dict(files=[],directories=[],symlinks=[]);n=0
 for base,dirs,names in os.walk(root,followlinks=False):
  for name in sorted(dirs+names):
   n+=1;need(n<=40000,'TREE_MEMBERSHIP_BOUND');p=pathlib.Path(base)/name;st=p.lstat();rel=p.relative_to(root).as_posix()
   if stat.S_ISLNK(st.st_mode):
    need(links,'NO_SDK_GUARD_LINK');target=p.resolve(strict=True);need(target.is_relative_to(root) and target.is_file(),'CONTAINED_REGULAR_DEP_LINK');out['symlinks'].append(dict(path=rel,link=str(p.readlink()),target=target.relative_to(root).as_posix()))
   elif stat.S_ISDIR(st.st_mode):out['directories'].append(dict(path=rel,mode=stat.S_IMODE(st.st_mode)))
   elif stat.S_ISREG(st.st_mode):out['files'].append(dict(path=rel,mode=stat.S_IMODE(st.st_mode)))
   else:raise ValueError('TREE_SPECIAL:'+str(p))
 for rows in out.values():rows.sort(key=lambda r:r['path'])
 return out
fulltrees=[]
for key,count in (('sdk',434),('guard',522)):
 spec=trees[key];actual=walk(spec['root']);expected=dict(files=[],directories=[],symlinks=[])
 for row in spec['members']:expected['files' if row['type']=='file' else 'directories'].append(dict(path=row['path'],mode=int(row['mode'],8)))
 for rows in expected.values():rows.sort(key=lambda r:r['path'])
 need(actual==expected and len(actual['files'])==count,'REVIEWED_FULL_TREE_NAMES_MODE:'+key)
 fulltrees.append(dict(root=spec['root'],regularFiles=count,membership=actual));add(spec['authority'],'METADATA_AUTHORITY','FIXED_'+key+'_TREE_AUTHORITY','fullMembershipAuthorities')
 for row in actual['files']:
  target=spec['root']+'/'+row['path'];need(target in seen and seen[target]['mode']==row['mode'],'ALL_TREE_HASHES_PRESENT:'+target)
node_spec=authority(by_name['dependency-tree.json'],'CURRENT_NODE_DEPENDENCY_TREE');dep=walk(node_spec['sourceRoot'],True)
need([r['path'] for r in dep['files']]==sorted(node_spec['files']) and [r['path'] for r in dep['directories']]==sorted(node_spec['directories']) and dep['symlinks']==sorted(node_spec['symlinks'],key=lambda r:r['path']),'EXACT_NODE_MEMBERSHIP')
need([len(dep[k]) for k in ('files','directories','symlinks')]==[816,65,2],'NODE816_65_2')
for row in dep['files']:need(node_spec['sourceRoot']+'/'+row['path'] in seen,'ALL816_STREAMED')
# Explicit producer/prerequisite participant selectors; no arbitrary recursive DAG.
proofs=[];participants=set()
def actor_fields(d,fields):
 x=authority(d,'EXPLICIT_ACTOR_AUTHORITY','actorProofAuthorities')
 for field in fields:
  if field not in x:continue
  v=x[field];values=list(enumerate(v)) if type(v) is list else [(None,v)]
  for index,actor in values:
   if type(actor) is str and (actor=='/root' or actor.startswith('/root/')):
    selector='/'+field+('' if index is None else '/'+str(index));proof=dict(actor=actor,authority=d,selector=selector)
    if proof not in proofs:proofs.append(proof)
    participants.add(actor)
actor_fields(known_pin,['knownActors'])
actor_fields(sp,['author','coordinator','sourceContributors','predecessorAuthor'])
for key in ('predecessorSource','originalProducer3Source'):actor_fields(source[key],['author','coordinator','sourceContributors','predecessorAuthor','authors','operators'])
actor_fields(method,['authors']);actor_fields(bindings['amethystProvenance'],['actor']);actor_fields(bindings['helperProvenance'],['actor']);actor_fields(bindings['acceptedE01Acceptance'],['actor']);actor_fields(raw_pin(AC/'lineage.json')[0],['actor'])
for p in (E/'e02-producer3-current-controls-preparation-20261028/source4/subject.json',E/'e02-producer3-controls-actual-20261028-r2/capture-a/subject.json',E/'e02-producer3-controls-actual-20261028-r2/capture-b/subject.json'):
 actor_fields(raw_pin(p)[0],['authors','operators','author','coordinator'])
context=write(D/'actor-context.json',dict(schema='e02-producer4-capture-current-actor-context-v1',producerSource=sp,captureSource=method,sourceBirth=raw_pin(AC/'lineage.json')[0],participants=sorted(participants),participantProofs=proofs))
# Actor context, CODE subject, plan and actual ACK are deferred input authorities;
# they are not inserted into CODE.sources and cannot cause selfhash cycles.
manifest=write(D/'input-manifest.json',dict(schema='e02-producer4-explicit-host-input-manifest-v1',producerSource=sp,closedSourceSubjectKeys=sorted(source),controlPlan=source['controlPlan'],files=[seen[k] for k in sorted(seen)],actualInputCount=len(seen),maximumInputCount=20000,requiredCoverage=coverage,fullTrees=fulltrees,nodeDependencies=dict(root=node_spec['sourceRoot'],membership=dep),baselineInputAuthority=raw_pin(bp)[0],scope='EXPLICIT_SELECTED_SOURCE_AND_NAMED_READ_OPERANDS_PLUS_FULL_SDK_GUARD_NODE_TREES',baselineDataTransferClaimed=False,privateKeysRead=False,opaqueRawMeaning='Raw inputs are uniformly streamed; named metadata alone is decoded <=16MiB. No descriptor-shaped recursion.'))
scopes=[]
for i,(name,count) in enumerate(zip(files,counts)):
 d=by_name[name];text=pathlib.Path(d['path']).read_text();names=None
 if i>=5:
  tree=ast.parse(text);names=[c.name+'.'+f.name for c in tree.body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')];need(len(names)==count,'AST_PY_COUNT:'+name)
 elif i==4:names=re.findall(r"await test\('([^']+)'",text);need(len(names)==count,'OBS_NAMES')
 scopes.append(dict(scope=name,source=d,argv=([tools['node']['path'],d['path']] if i<5 else [tools['python']['path'],'-I','-B',d['path']]),cwd=str(pathlib.Path(d['path']).parent),count=count,definitionNames=names,format='EXACT_SELECTED_NODE_JSON' if i<5 else 'QUIET_UNITTEST_NO_SKIPS'))
plan=dict(schema='e02-producer4-control-capture-plan-v1',readiness=False,producerSource=sp,captureSource=method,inputManifest=manifest,limits=limits,deadlineLedger=ledger,scopes=scopes,countsSeparate=counts,tools=tools,outputRoot=None,requiredCoverage=coverage,clockSelection=clock,producerSourcePacket=entry['packet'],actualSourceReviewPins=[raw_pin(AC/n)[0] for n in ('qa.json','security.json')],captureSourceReviews=None,captureSourceAcceptance=None,admissionDataAcceptance=None,rootAcknowledgement=None,scope='SOURCE_PREPARATION_ONLY_NO_EXECUTION_AUTHORITY')
request=dict(cmd=shlex.join(['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','1203s',tools['python']['path'],'-I','-B',str(D/'capture.py'),'--execute-once','--root-ack-sha','<ACTUAL_ROOT_ACK_SHA256>']),workdir=str(D),login=False,yield_time_ms=1000,max_output_tokens=2000)
request_pin=write(D/'request-template.json',request);plan_pin=write(D/'execution-plan.json',plan)
binding=write(D/'runtime-bindings.json',dict(schema='e02-producer4-capture-runtime-bindings-v1',readiness=False,producerSource=sp,producerAcceptance=ap,captureSourceAcceptance=None,admissionDataAcceptance=None,rootAcknowledgement=None))
ack={k:None for k in const['ACK_KEYS'].split()};ack.update(schema='e02-producer4-control-capture-root-ack-v1',actor='/root',executionAuthorized=False,scope='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY',producerSource=sp,producerSourceAcceptance=ap,producerReviews=[raw_pin(AC/n)[0] for n in ('qa.json','security.json')],captureSource=method,admissionPlan=admission_plan,sourceBirth=raw_pin(AC/'lineage.json')[0],actorContext=context,inputManifest=manifest,plan=plan_pin,clockSelection=clock,requestContract=request_pin,runtimeBindings=binding,authors=['/root/r5_plan_fix'],operators=None,noRetry=True)
ack_pin=write(D/'root-ack-template.json',ack)
# Source equivalence is CODE evidence only. Capture tail is explicitly adapted.
accepted_core=pathlib.Path('/Data/nbdp-e02-tooling-20261027/wrapper46-model-method-preparation-r3/capture46.py')
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=funcs(accepted_core),funcs(D/'capture.py');equal={n:a[n]==b[n] for n in ('signal_owned_group','finish_owned','capture_scope')}
need(equal['signal_owned_group'] and equal['finish_owned'],'TWO_LIFECYCLE_FUNCTION_AST_UNCHANGED')
reuse=write(D/'lifecycle-source-comparison.json',dict(schema='e02-producer4-capture-core-source-equivalence-v1',acceptedCore=raw_pin(accepted_core)[0],acceptedLimitedData=raw_pin(E/'e02-wrapper-capture-admission9-actual-20261028/acceptance.json')[0],currentCapture=raw_pin(D/'capture.py')[0],functionAstEqual=equal,scope='Two functions identical. capture_scope changes stream/result retention and producer4 output adapter; no whole-method or historical DATA transfer.',modelsExecuted=0))
# Archive only owned text SOURCE/metadata, never SDK/APK/native/private bytes.
archives=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  d=raw_pin(p)[0];need(d['bytes']<=16777216,'ONLY_SMALL_SOURCE_COPY');copy=write(OUT/'copies'/p.relative_to(D),p.read_bytes());archives.append(dict(original=d,copy=copy))
archive_pin=write(OUT/'archive-manifest.json',dict(schema='e02-producer4-capture-source-archive-v1',copies=archives,originalsPreserved=True,binaryCopies=0))
summary=dict(inputFiles=len(seen),inputBytes=sum(r['pin']['bytes'] for r in seen.values()),largestInput=max((r['pin'] for r in seen.values()),key=lambda d:d['bytes']),sdkFiles=434,guardFiles=522,nodeFiles=816,nodeDirectories=65,nodeSafeLinks=2,sourceMembers=len(source['sources']),runtimeWorkers=22,selectedGroups=10,targetDefinitions=260,admissionDefinitions=21,allExecutions=0,archiveCopies=len(archives))
packet=write(OUT/'source-packet.json',dict(schema='e02-producer4-capture-source-packet-v1',author='/root/r5_plan_fix',producerSource=sp,producerAcceptance=ap,codeSubject=method,admissionPlan=admission_plan,inputManifest=manifest,executionPlan=plan_pin,rootAckTemplate=ack_pin,requestTemplate=request_pin,runtimeBindings=binding,actorContext=context,actorContextScope='Closed six-field SOURCE proposal with closed three-field actual known-selector actor proof rows. Root lineage selects actual birthEvidence, and is not a birth envelope.',lifecycleComparison=reuse,archiveManifest=archive_pin,summary=summary,predecessorHold=raw_pin(E/'e02-producer4-capture-source3-fresh-reviewer-freeze-20261028/findings-and-disposition.json')[0],readiness=False,captureSourceReviews=None,captureSourceAcceptance=None,admissionData=None,admissionDataAcceptance=None,rootGrant=None,remainingGates=['Independent current capture SOURCE/code/input/actor/clock review','Separate pre-released actual21 mocked admission capture and independent DATA acceptance','Root concrete fresh output/actors/reviewed plan/input/once ACK render and independent readiness review','Only then one exact foreground ten-scope capture plus truthful all-response API collection and separate assembler/DATA review'],historicalDataTransferClaimed=False))
entrypin=write(OUT/'review-entrypoint.json',dict(schema='e02-producer4-capture-source-review-entrypoint-v1',packet=packet,codeSubject=method,inputManifest=manifest,admissionPlan=admission_plan,executionPlan=plan_pin,rootAckTemplate=ack_pin,summary=summary,sourceOnly=True,readiness=False,modelsExecuted=0,helperExecutions=0,ordinaryRolesExecuted=0))
print(json.dumps(dict(entrypoint=entrypin,packet=packet,codeSubject=method,inputManifest=manifest,summary=summary,preparationElapsedSeconds=time.monotonic()-start)))
