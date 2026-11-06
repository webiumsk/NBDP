"""Bounded exact negative-evidence copying only. No experiment/import/service execution."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

OUT=Path(__file__).resolve().parent
ROOT=Path('/Data/nbdp-e02-tooling-20261027/ordinary-minimum-r3/runs/9d8bad6df86fc113f87e14e2974f9019')
SRC=Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
E=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence')
SCHED=E/'e02-incoming-collection-scheduling-20261028'
MAX_FILES=20000
MAX_BYTES=536870912
MAX_FILE_BYTES=16777216
CHUNK=1048576
SUBTREES=['commands','ownership','cleanup','session','ui','evidence']
REFS=['incoming-original-tool-origin.json','incoming-root-role-release.json','incoming-negative-lifecycle-acceptance.json','incoming-negative-qa.json','incoming-negative-security.json','incoming-exact-generated-request.json','incoming-fresh-resource-admission.json','fresh-resource-original-tool-origin.json','concrete-incoming/proposal.json','concrete-incoming/concrete-qa.json','concrete-incoming/concrete-security.json','decision.json','method-architect.json','method-security.json']
NSEC=re.compile(rb'nsec1[023456789acdefghjklmnpqrstuvwxyz]+')
RAW_KEYS=[b'BEGIN PRIVATE KEY',b'BEGIN OPENSSH PRIVATE KEY',b'BEGIN RSA PRIVATE KEY',b'BEGIN EC PRIVATE KEY']

def load(p):return json.loads(Path(p).read_bytes())
def identity(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def row(s):return dict(mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,gid=s.st_gid,device=str(s.st_dev),inode=str(s.st_ino),mtimeNs=str(s.st_mtime_ns),ctimeNs=str(s.st_ctime_ns))
def need(v,m):
    if not v:raise ValueError(m)
def no_links(p):
    for q in [p,*p.parents]:need(not stat.S_ISLNK(q.lstat().st_mode),'NO_SYMLINK:'+str(q))
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(name,v):
    p=OUT/name
    with p.open('xb') as f:f.write((json.dumps(v,indent=2)+'\n').encode())
    return pin(p)
def selected_tree(root):
    found=[]
    for base,dirs,files in os.walk(root,followlinks=False):
        dirs.sort();files.sort()
        for n in dirs:need(stat.S_ISDIR((Path(base)/n).lstat().st_mode),'NO_SPECIAL_SUBDIRECTORY')
        for n in files:
            p=Path(base)/n;need(stat.S_ISREG(p.lstat().st_mode),'NO_SPECIAL_SELECTED_FILE:'+str(p));found.append(p)
    return found

def copy_exact(source,target,allowed_nsec):
    no_links(source);before=source.lstat();need(stat.S_ISREG(before.st_mode) and before.st_size<=MAX_FILE_BYTES,'REGULAR_BOUNDED_FILE_ONLY')
    fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    count=0;digest=hashlib.sha256();body=bytearray()
    try:
        need(identity(os.fstat(fd))==identity(before),'OPEN_IDENTITY_DRIFT')
        while True:
            b=os.read(fd,CHUNK)
            if not b:break
            count+=len(b);need(count<=before.st_size and count<=MAX_FILE_BYTES,'BOUNDED_COPY_READ');digest.update(b);body.extend(b)
        need(identity(os.fstat(fd))==identity(before),'HANDLE_CHANGED_DURING_COPY')
    finally:os.close(fd)
    need(identity(source.lstat())==identity(before) and count==before.st_size,'PATH_CHANGED_DURING_COPY');no_links(source)
    if source.suffix!='.png':
        need(not any(k in body for k in RAW_KEYS),'UNEXPECTED_PRIVATE_KEY_ARMOR_NO_QUALIFICATION')
        tokens=set(NSEC.findall(body));need(tokens<=allowed_nsec,'UNEXPECTED_NSEC_NO_QUALIFICATION')
    else:tokens=set()
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with target.open('xb') as dst:
        os.chmod(target,0o600);dst.write(body)
    sha=digest.hexdigest();copy_pin=pin(target);need(copy_pin['bytes']==count and copy_pin['sha256']==sha,'COPY_BYTES_MISMATCH')
    return dict(original=dict(path=str(source),bytes=count,sha256=sha),copy=copy_pin,originalMetadata=row(before),sourceStableDuringCopy=True,knownPublicFixtureNsecDigests=sorted(hashlib.sha256(t).hexdigest() for t in tokens))

def main():
    need(not (OUT/'manifest.json').exists() and not (OUT/'copies').exists(),'FRESH_DESTINATION_ONLY')
    config=load(ROOT/'input/run-config.json');expected=config['sourceAndDependencyPins'];need(len(expected)==16,'EXACT16_WORKERS')
    fixture=load(SRC/'fixture-plan.json');publicScalars=[v['scalar'] for v in fixture['roles'].values()]
    need(len(publicScalars)==2 and all(type(n) is int and 1<=n<=3 for n in publicScalars),'ONLY_ALREADY_PUBLIC_SMALL_FIXTURE_SCALARS')
    allowed_nsec={v['nsec'].encode() for v in fixture['roles'].values()};need(len(allowed_nsec)==2,'EXACT_TWO_KNOWN_FIXTURE_KEYS')
    selected=[ROOT/'supervisor-result.json']
    for name in SUBTREES:selected.extend(selected_tree(ROOT/name))
    staged=[ROOT/'input'/Path(d['path']).name for d in expected]
    selected+=staged+[ROOT/'input/run-config.json']
    commands=[p for p in selected if p.parent==ROOT/'commands'];need(len(commands)==1182,'EXACT394_JSON_AND788_STREAMS')
    for i in range(1,395):
        for suffix in ['json','stdout','stderr']:need(ROOT/'commands'/f'{i:04d}.{suffix}' in commands,'COMPLETE_COMMAND_TRIPLETS')
    selected=sorted(set(selected));references=[SCHED/n for n in REFS]
    need(len(selected)+len(references)<=MAX_FILES,'FILE_LIMIT');total=sum(p.lstat().st_size for p in selected+references);need(total<=MAX_BYTES,'TOTAL_BYTE_LIMIT')
    for d,p in zip(expected,staged):need(pin(p)=={**d,'path':str(p)},'STAGED_WORKER_NOT_EXACT_EXPECTED_BYTES:'+p.name)
    result=load(ROOT/'supervisor-result.json');acceptance=load(SCHED/'incoming-negative-lifecycle-acceptance.json')
    need(result['executionState']=='FAILED_UNQUALIFIED' and acceptance['subject']==pin(ROOT/'supervisor-result.json'),'EXACT_NEGATIVE_SUBJECT')
    need(acceptance['decision']=='ACCEPT_NEGATIVE_RUN_LIFECYCLE_AND_EXACT_OWNED_CLEANUP_ONLY' and acceptance['ordinaryRowsQualified']==0,'NEGATIVE_ONLY')
    need(len(result['cleanup']['rows'])==4 and len({r['cid'] for r in result['cleanup']['rows']})==4,'FOUR_DISTINCT_OWNED_CIDS')
    rows=[]
    for p in selected:rows.append(copy_exact(p,OUT/'copies/run'/p.relative_to(ROOT),allowed_nsec))
    for p in references:rows.append(copy_exact(p,OUT/'copies/root-evidence'/p.relative_to(SCHED),allowed_nsec))
    need(sum(r['original']['bytes'] for r in rows)==total,'EXACT_TOTAL')
    unknown_input=[]
    selected_input=set(staged+[ROOT/'input/run-config.json'])
    for p in sorted((ROOT/'input').iterdir()):
        if p not in selected_input:
            s=p.lstat();unknown_input.append(dict(path=str(p),bytes=s.st_size,mode=oct(stat.S_IMODE(s.st_mode)),context='Zero-length bind-mount placeholder; not the mounted original. Native/APK/SDK bytes excluded regardless of placeholder size.'))
    need(all(r['bytes']==0 for r in unknown_input),'UNEXPECTED_NONEMPTY_UNSELECTED_INPUT')
    exclusions=save('selection-and-exclusions.json',dict(schema='e02-incoming14-negative-preservation-selection-v1',runRoot=str(ROOT),scope='Exact allowlisted regular files only, not whole filesystem/AVD/container/SDK preservation.',includedSubtrees=SUBTREES,includedRootFiles=['supervisor-result.json'],stagedTextWorkers=[dict(expected=d,actualStaged=pin(p)) for d,p in zip(expected,staged)],runConfig=pin(ROOT/'input/run-config.json'),excludedSubtrees=[dict(path=str(ROOT/name),reason=reason,descended=False,bodyRead=False,copied=False) for name,reason in [('android-state','Private Android app/AVD/key/runtime state; no private key bytes or binary images.'),('docker-config','Private Docker configuration/credentials; excluded without file inspection.'),('relay-data','Relay databases/runtime storage; not raw command evidence.')]],excludedInputPlaceholders=unknown_input,externalBinariesAndImages='No SDK/APK/native/AVD/image/relay database/Docker private config bytes selected or copied; external descriptors/command arguments may identify their paths.',maximumFiles=MAX_FILES,maximumTotalBytes=MAX_BYTES,maximumCopyChunkBytes=CHUNK,copyPermissions='Copies0600, directories0700; original modes/UID/GID/identity retained in manifest only.',pngAssessment='38 PNGs from isolated synthetic public-fixture login/profile/relay UI, retained with38 companionXMLs and exact public key source binding; no OCR or claim of scanning image pixels for secrets.',secretAssessment=dict(scope='Known text records/inputs/XML plus original intentionally public fixed scalar role source; no private state directories read.',fixtureSource=pin(SRC/'fixture-plan.json'),smallPublicScalarIntegers=publicScalars,allowedNsecDigests=sorted(hashlib.sha256(t).hexdigest() for t in allowed_nsec),unknownNsecFound=False,privateKeyArmorFound=False,redactionApplied=False,limits='This is a bounded selected-evidence assessment, not a complete forensic secret scan. XML password attributes are UI metadata; screenshot scope is the synthetic fixture account.')))
    manifest=save('manifest.json',dict(schema='e02-incoming14-negative-exact-file-preservation-manifest-v1',author='/root/r5_plan_fix',coordinator='/root',runId=result['runId'],ordinaryRole='incoming',state='FAILED_UNQUALIFIED_NEGATIVE_EVIDENCE_ONLY',copies=rows,fileCount=len(rows),runFileCount=len(selected),rootEvidenceFileCount=len(references),totalBytes=total,commandJsonCount=394,commandStreamCount=788,uiXmlCount=38,uiPngCount=38,stagedTextWorkerCount=16,selection=exclusions,supervisorSubject=pin(ROOT/'supervisor-result.json'),rootNegativeAcceptance=pin(SCHED/'incoming-negative-lifecycle-acceptance.json'),originalToolOrigin=pin(SCHED/'incoming-original-tool-origin.json'),rootGrant=pin(SCHED/'incoming-root-role-release.json'),observedOwnedCids=[dict(role=r['role'],cid=r['cid'],absenceReported=r['absenceConfirmed']) for r in result['cleanup']['rows']],wholeInputPostrunCustody=dict(state='PENDING_NOT_CLAIMED_BY_THIS_PACKAGE',actualOutcome=None,authority='Root owns separately authorized current postrun check; this copier does not execute it.'),qualification=dict(ordinaryRowsQualified=0,latestAttemptDisposition='NO_CONTRIBUTION',all14AttemptQualification='NO_QUALIFIED_ROWS_ROOT_DECLARED_CONTEXT_NOT_14_ARCHIVES_REVERIFIED_HERE',canonicalE02='PARTIAL22_UNCHANGED',rootCause='UNKNOWN',modelOrRuntimeExecutionByPreserver=0,archiveRoleOrRetryAuthorized=False),bounds=dict(maximumFiles=MAX_FILES,maximumBytes=MAX_BYTES),sourceRootUnchangedByCopier=True))
    review=save('review-packet.json',dict(schema='e02-incoming14-negative-preservation-review-packet-v1',author='/root/r5_plan_fix',scope='Byte-exact preservation/selection review only; no own approval of lifecycle, privacy or run qualification.',manifest=manifest,selection=exclusions,preservationScript=pin(__file__),independentQa=None,independentSecurity=None,wholeInputPostrunCustody='PENDING',ordinaryRowsQualified=0,modelsExecuted=0,experimentsExecuted=0,gitOrStateChanges=False))
    save('entrypoint.json',dict(schema='e02-incoming14-negative-preservation-entrypoint-v1',manifest=manifest,reviewPacket=review,fileCount=len(rows),totalBytes=total,independentReview='PENDING',wholeInputPostrunCustody='PENDING',ordinaryRowsQualified=0))
    print(json.dumps(dict(manifest=manifest,reviewPacket=review,files=len(rows),bytes=total,selectedRunFiles=len(selected),rootEvidenceFiles=len(references),postrun='PENDING',ordinaryRowsQualified=0)))
if __name__=='__main__':main()
