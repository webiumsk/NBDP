"""Concrete metadata candidate renderer only; no target imports or execution.

Writes disjoint owned candidates. Never installs HERE activation metadata or mints
an actual grant. Its true-valued ACK is explicitly UNISSUED review material.
"""
import ast,copy,hashlib,json,os,pathlib,secrets,stat
R=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence'
HERE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r1/source4')
D=pathlib.Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-final-bindings-preparation-r1')
OUT=E/'e02-producer4-control-capture-preparation-20261028/final-bindings-r1'
CAP=E/'e02-producer4-capture-source4-acceptance-20261028';PROD=E/'e02-producer4-source4-acceptance-20261028';ADM=E/'e02-producer4-capture-admission21-canonical-r1-20261028'

def need(v,m):
 if not v:raise ValueError(m)
def encode(x):return (json.dumps(x,indent=2)+'\n').encode()
def pin_bytes(path,raw):return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def ident(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(path,expected=None):
 p=pathlib.Path(path);need(p.is_absolute() and str(p)==os.path.normpath(str(p)),'CANONICAL_METADATA_PATH')
 for q in (p,*p.parents):need(not q.is_symlink(),'NO_METADATA_SYMLINK')
 first=p.lstat();need(stat.S_ISREG(first.st_mode) and first.st_size<=16777216,'NAMED_SMALL_METADATA_ONLY')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  opened=os.fstat(fd);need(ident(opened)==ident(first),'METADATA_OPEN_IDENTITY');parts=[];n=0
  while True:
   b=os.read(fd,1048576)
   if not b:break
   n+=len(b);need(n<=first.st_size,'BOUNDED_METADATA');parts.append(b)
  need(ident(os.fstat(fd))==ident(opened),'METADATA_HANDLE_DRIFT')
 finally:os.close(fd)
 need(ident(p.lstat())==ident(first),'METADATA_PATH_DRIFT');raw=b''.join(parts);d=pin_bytes(p,raw);need(expected is None or d==expected,'EXPECTED_METADATA_DESCRIPTOR');return d,raw

def doc(path,expected=None):
 d,raw=read(path,expected)
 def pairs(items):
  x={}
  for k,v in items:need(k not in x,'DUPLICATE_KEY');x[k]=v
  return x
 return d,json.loads(raw,object_pairs_hook=pairs)
def put(path,value):
 p=pathlib.Path(path);raw=value if isinstance(value,bytes) else encode(value);need(len(raw)<=16777216,'OWN_SMALL_CANDIDATE');need(not p.exists() and not p.is_symlink(),'NO_CANDIDATE_OVERWRITE');fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:need(f.write(raw)==len(raw),'ONE_COMPLETE_METADATA_WRITE')
 return pin_bytes(p,raw)
def closed(v,fields):need(type(v) is dict and set(v)==set(fields.split()),'CLOSED_METADATA_FIELDS')
need(not (OUT/'review-entrypoint.json').exists(),'FROZEN_CANDIDATE_EXISTS')
packetpin,packet=doc(E/'e02-producer4-control-capture-preparation-20261028/source4/source-packet.json')
methodpin,method=doc(HERE/'code-subject.json',packet['codeSubject']);sourcepin,source=doc(packet['producerSource']['path'],packet['producerSource'])
need(methodpin['sha256']=='eff0594e20268670588e03948dd6bc7f9b14a6b91b55e7eb11e9ad11fe61e822' and sourcepin['sha256']=='34802f702c863e5cd81e865eec5de7736615ceffc683a8a9f9eb4192e857e66e','EXACT_ACCEPTED_SOURCE_ONLY')
cap_pin,cap=doc(CAP/'acceptance.json');prod_pin,prod=doc(PROD/'acceptance.json');adm_pin,adm=doc(ADM/'acceptance.json');data_pin,data=doc(ADM/'subject.json',adm['subject'])
need(cap_pin['sha256']=='59e8cf818cd5e367b85de5e63c86d84e6c88395f75d29187ecffa9601d1894c4' and adm_pin['sha256']=='5c2cd0767fba10bf5196591887db61aa54566cec24ebe7cda38e248680ed9700','ACTUAL_ROOT_ACCEPTANCE_PINS')
need(data_pin['sha256']=='872570129fd20bd06e15f8ce600072f8cb74bf9547d22295fd29a6181f2a7369','CANONICAL_ACTUAL21_ENVELOPE_ONLY')
closed(adm,'schema actor decision subject reviews captureSource producerSource admissionPlan modelsDefined modelsExecuted modelsPassed modelsFailed targetModelsExecuted helperExecutions ordinaryRoleExecutions scope executionAuthorized')
need(adm['schema']=='e02-root-producer4-capture-admission-data-acceptance-v1' and adm['actor']=='/root' and adm['decision']=='ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY' and adm['executionAuthorized'] is False,'DATA_ACCEPTANCE_IS_NOT_GRANT')
need(adm['captureSource']==methodpin and adm['producerSource']==sourcepin and adm['admissionPlan']==packet['admissionPlan'] and [adm[k] for k in ('modelsDefined','modelsExecuted','modelsPassed')]==[21]*3 and all(adm[k]==0 for k in ('modelsFailed','targetModelsExecuted','helperExecutions','ordinaryRoleExecutions')),'EXACT_CURRENT21_ONLY')
contextpin,context=doc(packet['actorContext']['path'],packet['actorContext']);manifestpin,manifest=doc(packet['inputManifest']['path'],packet['inputManifest']);oldplanpin,plan=doc(packet['executionPlan']['path'],packet['executionPlan']);requestpin,request=doc(packet['requestTemplate']['path'],packet['requestTemplate']);oldbindingpin,oldbinding=doc(HERE/'runtime-bindings.json',packet['runtimeBindings']);oldackpin,ack=doc(packet['rootAckTemplate']['path'],packet['rootAckTemplate'])
need(oldbinding['readiness'] is False,'ORIGINAL_ACTIVATION_REMAINS_FALSE')
newauthorities=[]
def authority(d):
 _,x=doc(d['path'],d)
 if d not in newauthorities:newauthorities.append(d)
 return x
# Root lineage and actual birth envelopes remain distinct recorded authorities.
prod_lineage_pin,prod_lineage=doc(PROD/'lineage.json');cap_lineage_pin,cap_lineage=doc(CAP/'lineage.json')
for lineage_pin,lineage,birthkey in ((prod_lineage_pin,prod_lineage,'birthEvidence'),(cap_lineage_pin,cap_lineage,'birth')):
 authority(lineage_pin)
 for key in ('sourceFreeze',birthkey):authority(lineage[key])
 birth=authority(lineage[birthkey]);need(birth['schema']=='e02-genuine-post-freeze-reviewer-birth-evidence-v1' and birth['sourceFreeze']==lineage['sourceFreeze'],'ACTUAL_POST_FREEZE_BIRTH_JOIN')
 for key in ('clockBefore','clockAfter'):authority(birth[key])
 for d,selector in ((lineage_pin,'/actor'),(lineage[birthkey],'/actor')):
  proof=dict(actor='/root',authority=d,selector=selector)
  if proof not in context['participantProofs']:context['participantProofs'].append(proof)
# Data authors/operators are actual declared contributors; reviewer identities are
# not inferred as authors from birth/custody descriptions.
for key in ('authors','operators'):
 for i,actor in enumerate(data[key]):
  proof=dict(actor=actor,authority=data_pin,selector='/'+key+'/'+str(i))
  if proof not in context['participantProofs']:context['participantProofs'].append(proof)
  if actor not in context['participants']:context['participants'].append(actor)
context['participants']=sorted(set(context['participants']));known=authority(method['knownActors']);need(set(known['knownActors'])<=set(context['participants']),'ALL_ELEVEN_KNOWN_ACTORS')
# Close contributors/operators before reading and admitting any review pair.
forbidden=set(context['participants'])|set(method['authors'])|set(data['authors'])|set(data['operators'])|set(source['sourceContributors'])|{source['author'],source['coordinator'],source['predecessorAuthor'],'/root','/root/r5_plan_fix'}
for acceptance,subject,decision in ((prod,sourcepin,'ACCEPT_PRODUCER4_SOURCE4_AND_260_CONTROL_DEFINITIONS_ONLY'),(cap,methodpin,'ACCEPT_PRODUCER4_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY'),(adm,data_pin,'ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY')):
 need(len(acceptance['reviews'])==2,'TWO_ORDERED_RAW_REVIEWS');sessions=[]
 for role,d in zip(('qa','security'),acceptance['reviews']):
  review=authority(d);closed(review,'role session decision subject');need(review['role']==role and review['subject']==subject and review['decision']==decision and review['session'] not in forbidden,'ACTUAL_INDEPENDENT_ROLE_SUBJECT_LITERAL');sessions.append(review['session'])
 need(sessions[0]!=sessions[1],'DISTINCT_QA_SECURITY')
for d in (prod_pin,cap_pin,adm_pin,data_pin):authority(d)
for key in ('execution','rawArtifactManifest','inputsBefore','inputsAfter'):authority(data[key])
# Original API metadata permits raw wall-time floats; its bytes are pinned only.
read(data['originalToolOrigin']['path'],data['originalToolOrigin']);newauthorities.append(data['originalToolOrigin'])
for proof in context['participantProofs']:
 x=authority(proof['authority'])
 for key in proof['selector'][1:].split('/'):
  key=key.replace('~1','/').replace('~0','~');x=x[int(key)] if isinstance(x,list) else x[key]
 need(x==proof['actor'],'ACTUAL_KNOWN_ACTOR_SELECTOR')
contextpin=put(D/'actor-context.json',context)
# Explicit extra named metadata only. No SDK/Node/native/binary rehash or walk;
# declared old expected bytes/membership remain unchanged and capture revalidates.
files={r['pin']['path']:r for r in manifest['files']};extra=[]
for d in newauthorities+[contextpin]:
 if d['path'] in files:need(files[d['path']]['pin']==d,'NO_STATIC_INPUT_SUBSTITUTION')
 else:
  read(d['path'],d);mode=stat.S_IMODE(pathlib.Path(d['path']).stat().st_mode);files[d['path']]=dict(pin=d,mode=mode,role='METADATA_AUTHORITY',origin='EXACT_CURRENT_ACCEPTANCE_BIRTH_ADMISSION_ACTOR_PROOF');extra.append(d)
manifest['files']=[files[k] for k in sorted(files)];manifest['actualInputCount']=len(files);manifest['requiredCoverage']['currentFinalBindingAuthorities']=extra;need(len(files)<=20000,'ALL_METADATA_PLUS_DECLARED_LIMIT')
newmanifestpin=put(D/'input-manifest.json',manifest)
# Fresh output parent is empty0700. The run directory remains absent. Its sibling
# original API and assembled files are created later only by Root actual custody.
parent=pathlib.Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-'+secrets.token_hex(16));need(not parent.exists(),'FRESH_ACTUAL_PARENT');parent.mkdir(mode=0o700)
plan.update(readiness=True,inputManifest=newmanifestpin,outputRoot=str(parent/'run'),requiredCoverage=manifest['requiredCoverage'],captureSourceReviews=cap['reviews'],captureSourceAcceptance=cap_pin,admissionDataAcceptance=adm_pin,rootAcknowledgement='EXTERNAL_ROOT_ONE_USE_GRANT_PENDING',scope='READY_METADATA_CANDIDATE_NOT_EXECUTION_AUTHORITY')
need(plan['countsSeparate']==[123,33,29,16,20,10,11,8,7,3] and sum(plan['countsSeparate'])==260 and plan['limits']['controllerSeconds']==1200 and plan['limits']['outerSeconds']==1203 and plan['limits']['snapshotPoolSeconds']==480,'UNCHANGED_TEN_GROUP_CLOCKS')
planpin=put(D/'execution-plan.json',plan)
binding=dict(schema='e02-producer4-capture-runtime-bindings-v1',readiness=True,producerSource=sourcepin,producerAcceptance=prod_pin,captureSourceAcceptance=cap_pin,admissionDataAcceptance=adm_pin,rootAcknowledgement='EXTERNALLY_SHA_BOUND_AT_LAUNCH')
bindingpin=put(D/'runtime-bindings.CANDIDATE.json',binding)
# This projected descriptor is labelled, and becomes actual ONLY after Root
# installs the exact candidate bytes at the CODE-required original HERE path.
projected=pin_bytes(HERE/'runtime-bindings.json',encode(binding))
ack.update(executionAuthorized=True,captureSourceAcceptance=cap_pin,captureReviews=cap['reviews'],admissionData=data_pin,admissionDataAcceptance=adm_pin,admissionReviews=adm['reviews'],actorContext=contextpin,inputManifest=newmanifestpin,plan=planpin,runtimeBindings=projected,authors=['/root/r5_plan_fix','/root'],operators=['/root'])
ackpin=put(D/'root-ack.UNISSUED.json',ack);requestpin2=put(D/'request-template.json',request)
need(requestpin2['sha256']==requestpin['sha256'],'EXACT_FROZEN_PARENT_REQUEST_TEMPLATE')
# No actual ACK hash/request or Root release is generated here.
report=dict(schema='e02-producer4-capture-final-binding-candidate-v1',author='/root/r5_plan_fix',status='READY_CANDIDATE_REQUIRES_INDEPENDENT_CONCRETE_REVIEW_AND_ROOT_RELEASE',captureSource=methodpin,producerSource=sourcepin,captureSourceAcceptance=cap_pin,admissionDataAcceptance=adm_pin,actorContext=contextpin,inputManifest=newmanifestpin,executionPlan=planpin,runtimeBindingCandidate=bindingpin,projectedInstalledRuntimeBinding=projected,rootAckUnissuedCandidate=ackpin,rootAckInstalledPath=str(HERE/'coordinator-acknowledgement.json'),originalRuntimeBindingPreserved=oldbindingpin,requestContract=requestpin,outputParent=str(parent),outputParentMode='0o700',runDirectoryAbsent=True,originalApiPath=str(parent/'original-tool-origin.json'),assembledSibling=str(parent/'assembled'),staticInputs=len(files),staticInputBytes=sum(r['pin']['bytes'] for r in files.values()),declaredRawTreeBytesFreshlyRevalidated=False,metadataInputsHashChecked=True,admissionModelsPreviouslyPassed=21,targetControlsExecutedByRenderer=0,helperExecutions=0,ordinaryRoles=0,actualGrant=None,actualApi=None,grantIssued=False,installationPerformed=False,originalFrozenCodeChanged=False,notes=['The UNISSUED ACK candidate intentionally contains executionAuthorized true for concrete review; it is not installed or issued.','Projected runtime descriptor is not claimed actual until Root installs and verifies exact candidate bytes.','Root alone creates actual ACK0600/O_EXCL, derives its actual SHA once and substitutes the exact request sentinel; no manual flags/TZ/TERM overrides.'])
reportpin=put(D/'candidate.json',report)
copyrows=[]
for p in sorted(D.iterdir()):
 d,raw=read(p);c=put(OUT/p.name,raw);copyrows.append(dict(original=d,copy=c))
entry=put(OUT/'review-entrypoint.json',dict(schema='e02-producer4-capture-final-binding-review-entrypoint-v1',candidate=reportpin,copies=copyrows,producerSource=sourcepin,captureSource=methodpin,captureSourceAcceptance=cap_pin,admissionDataAcceptance=adm_pin,actualRootGrant=None,executionAuthorized=False))
print(json.dumps(dict(entrypoint=entry,candidate=reportpin,plan=planpin,unissuedAck=ackpin,inputManifest=newmanifestpin,runtimeCandidate=bindingpin,projectedRuntimeBinding=projected,outputRoot=plan['outputRoot'],staticInputs=len(files))))
