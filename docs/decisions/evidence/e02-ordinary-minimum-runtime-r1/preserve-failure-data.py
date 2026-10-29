"""Completed-run read/hash/copy only. No tools, project imports or experiments."""
from pathlib import Path
import hashlib
import json
import os
import re
import stat

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
RUN=Path('/tmp/nbdp-e02-ordinary-minimum-v1/runs/1c09035e6a7e469a9449cdfa9764725a')
PREP=ROOT/'docs/decisions/evidence/e02-minimum-runtime-preparation-r1'
SOURCE=ROOT/'experiments/prototypes/e02_ordinary_minimum_v1'
SOURCE_PREP=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1'
OUT=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1'
INDEX=[];EXCLUDED=[]

def sha(b):return hashlib.sha256(b).hexdigest()
def info(s):return {'device':s.st_dev,'inode':s.st_ino,'size':s.st_size,'mode':oct(s.st_mode&0o7777),'uid':s.st_uid,'gid':s.st_gid,'mtimeNs':s.st_mtime_ns,'ctimeNs':s.st_ctime_ns}
def save(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def j(name,v):save(OUT/name,(json.dumps(v,indent=2)+'\n').encode())
def pin(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def copy(p,target,group,expected=None):
    a=p.lstat()
    if not stat.S_ISREG(a.st_mode) or p.resolve()!=p:raise ValueError('Noncanonical regular proof input:'+str(p))
    if a.st_size>16777216:raise ValueError('Proof file bound:'+str(p))
    b=p.read_bytes();z=p.lstat()
    if info(a)!=info(z) or len(b)!=a.st_size:raise ValueError('Finished proof input drift:'+str(p))
    original={'path':str(p),'bytes':len(b),'sha256':sha(b)}
    if expected is not None and original!=expected:raise ValueError('Source pin drift:'+str(p))
    save(target,b)
    INDEX.append({'group':group,'original':original,'originalStat':info(a),'preserved':pin(target),'preservedMode':oct(target.stat().st_mode&0o777),'originalStableBeforeAfter':True})
def exclude(p,reason):
    s=p.lstat();EXCLUDED.append({'originalPath':str(p),'reason':reason,'type':'directory' if stat.S_ISDIR(s.st_mode) else 'symlink' if stat.S_ISLNK(s.st_mode) else 'socket' if stat.S_ISSOCK(s.st_mode) else 'file','originalStat':info(s),'contentReadOrCopied':False})

# Explicit top-level capability closure; never descend into AVD/storage/keys/cache.
allowed={'commands','ui','evidence','session','cleanup','ownership','input'}
for p in sorted(RUN.iterdir()):
    if p.is_file() and p.name=='supervisor-result.json':copy(p,OUT/'run'/p.name,'FINISHED_RUN')
    elif p.name in allowed and p.is_dir() and not p.is_symlink():
        for parent,dirs,files in os.walk(p,followlinks=False):
            folder=Path(parent)
            for name in list(dirs):
                q=folder/name
                if q.is_symlink():exclude(q,'UNFOLLOWED_SYMLINK');dirs.remove(name)
            for name in sorted(files):
                q=folder/name
                if q.is_symlink() or not q.is_file():exclude(q,'NONREGULAR_SOCKET_OR_SYMLINK_NOT_EVIDENCE_BYTES')
                elif any(k in name.lower() for k in ('adbkey','id_rsa','id_ed25519')):exclude(q,'PRIVATE_RUNTIME_ADB_IDENTITY_NOT_BUNDLED')
                elif name.endswith(('.db','.sqlite','.sqlite3','.qcow2','.img','.lock')):exclude(q,'DATABASE_DISK_CACHE_OR_LOCK_NOT_BUNDLED')
                else:copy(q,OUT/'run'/q.relative_to(RUN),'FINISHED_RUN')
    else:exclude(p,'ALL_AVD_DISK_CACHE_SDK_APK_RELAY_DATABASE_DOCKER_PRIVATE_RUNTIME_STATE_EXCLUDED')

# All original coordinator preparation/launch/poll/resource/release records,
# including frozen bridge inputs; private Docker config is explicitly excluded.
for parent,dirs,files in os.walk(PREP,followlinks=False):
    folder=Path(parent)
    for name in list(dirs):
        q=folder/name
        if q.is_symlink() or name=='private-docker-config':exclude(q,'PRIVATE_DOCKER_RUNTIME_CONFIGURATION_NOT_BUNDLED');dirs.remove(name)
    for name in sorted(files):
        q=folder/name
        if q.is_file() and not q.is_symlink():copy(q,OUT/'coordinator-preparation'/q.relative_to(PREP),'ORIGINAL_COORDINATOR_RECORD')
        else:exclude(q,'UNFOLLOWED_NONREGULAR_COORDINATOR_FILE')

producer=json.loads((SOURCE_PREP/'subject.json').read_text())
copy(SOURCE_PREP/'subject.json',OUT/'source-authority/producer-subject.json','FROZEN_SOURCE_AUTHORITY')
for d in producer['sources']:
    p=Path(d['path']);copy(p,OUT/'producer-source'/p.relative_to(SOURCE),'FROZEN_PRODUCER_SOURCE',d)
for n in ('proposed-incoming-run-config.json','proposed-archive-run-config.json','navigation-source-audit.json','oracle-provenance.json','execution-control-plan.json'):
    copy(SOURCE_PREP/n,OUT/'source-authority'/n,'FROZEN_SOURCE_AUTHORITY')
fixture=json.loads((SOURCE/'fixture-plan.json').read_text())
external=[]
for label,d in fixture['pins'].items():
    p=Path(d['source']);expected={'path':str(p),'bytes':d['bytes'],'sha256':d['sha256']}
    if p.suffix in ('.mjs','.rs','.json','.toml','.md') and d['bytes']<=16777216:
        copy(p,OUT/'primary-pinned-inputs'/(label+'-'+p.name),'FROZEN_PRIMARY_SOURCE_OR_RECORD',expected)
    else:external.append({'pin':expected,'reason':'PINNED_EXTERNAL_INTERPRETER_OR_NATIVE_BINARY_PREREQUISITE_NOT_BUNDLED','contentCopied':False})
for d in fixture['dependencyFiles']:
    external.append({'pin':{'path':d['source'],'bytes':d['bytes'],'sha256':d['sha256']},'reason':'INSTALLED_DEPENDENCY_PIN_RETAINED_IN_FROZEN_FIXTURE_PLAN_NOT_BUNDLED','contentCopied':False})
# SDK/APK/helper are pinned prerequisites, never copied into this failure packet.
config=json.loads((SOURCE_PREP/'proposed-incoming-run-config.json').read_text())
for key in ('amethystApk','helperApk','sdkInventory','guardBundleInventory'):
    external.append({'pin':config[key],'reason':'PINNED_SDK_APK_GUARD_BUNDLE_PREREQUISITE_NOT_BUNDLED','contentCopied':False})

result=json.loads((RUN/'supervisor-result.json').read_text())
command_paths=sorted((RUN/'commands').glob('*.json'))
ui_pngs=sorted((RUN/'ui').glob('*.png'));ui_xmls=sorted((RUN/'ui').glob('*.xml'))
first=[]
for p in command_paths:
    value=json.loads(p.read_text())
    if value.get('exitCode') not in (None,0):first.append({'receipt':pin(p),'exitCode':value.get('exitCode'),'sequence':value.get('sequence'),'stderr':value.get('stderr')})
j('preservation-index.json',{'schema':'e02-minimum-incoming-failure-preservation-index-v1','actor':'/root/ordinary_api35_source','runRoot':str(RUN),'files':INDEX,'originalsModified':False,'publicSyntheticScalar1And2Retained':True})
j('excluded-inputs.json',{'schema':'e02-minimum-failure-explicit-exclusions-v1','excludedRuntimePaths':EXCLUDED,'externalPinnedPrerequisitesNotBundled':external,'policy':'No AVD/disk/cache/SDK/APK/private ADB key/database bytes copied. Pins/reference metadata are not portable runtime artifacts.'})
j('failure-facts.json',{'schema':'e02-minimum-incoming-actual-failure-facts-v1','runId':RUN.name,'supervisor':pin(OUT/'run/supervisor-result.json'),'actualExecutionState':result['executionState'],'actualSupervisorError':result['error'],'actualSecondaryErrors':result['secondaryErrors'],'actualCommandReceipts':len(command_paths),'actualPngCount':len(ui_pngs),'actualXmlCount':len(ui_xmls),'nonzeroCommandReceipts':first,'actualCleanup':result['cleanup'],'driverResultPresent':(RUN/'driver-result.json').exists(),'ordinaryContribution':'ZERO_FAILED_WHOLE_WINDOW_CANNOT_DONATE_EARLY_STEPS','archiveExecuted':False,'canonicalE02':'PARTIAL22_UNCHANGED','stockE04E06Unlocked':False,'independentFailureReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY','runtimeActionByPreserver':False})
readme='''# Actual minimum incoming failure r1

This packet mirrors the FINISHED/FAILED_UNQUALIFIED incoming window and its
original coordinator launch/poll/release/resource records. Source/config/raw
commands/UI/proxy/fixture/cleanup bytes are indexed against original paths,
SHA256, mode/stat and stable before/after identity. Mirrored files are0600;
original files remain unchanged. Explicit exclusions retain all AVD/disks/cache/
SDK/APKs/private ADB identities/databases outside this packet. External tool/
dependency pins are prerequisites, not a portable replay environment.

The failed whole window contributes ZERO ordinary rows. Publication/APP frame
proof does not substitute for missing selected client rendering/export. No
archive grant or retry is provided. Root's original API objects are distinct
from process/command journals; no portable process attestation is invented.
Independent QA/security acceptance of this actual failure is pending. E02 remains
PARTIAL22; existing gates and architecture blockers remain unchanged.
'''
save(OUT/'README.md',readme.encode())
j('subject.json',{'schema':'e02-minimum-incoming-failure-subject-v1','author':'/root/ordinary_api35_source','operator':'/root','state':'WRITES_STOPPED_PRESERVED_ACTUAL_FAILED_UNQUALIFIED_PENDING_INDEPENDENT_REVIEW','runId':RUN.name,'facts':pin(OUT/'failure-facts.json'),'index':pin(OUT/'preservation-index.json'),'exclusions':pin(OUT/'excluded-inputs.json'),'sourceSubject':pin(OUT/'source-authority/producer-subject.json'),'mirrorFileCount':len(INDEX),'originalApiReceipts':[row['preserved'] for row in INDEX if 'incoming-original-tool-' in row['original']['path']],'noRetryArchiveExperimentOrSourceFix':True,'ordinaryRowsQualified':0,'canonicalE02':'PARTIAL22_UNCHANGED','architecturalBlockersUnchanged':['Q01','Q08','Q13','Q15','Q27']})
j('artifact-manifest.json',{'schema':'e02-minimum-incoming-failure-artifact-manifest-v1','files':[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'],'manifestExcludesSelf':True})
print(json.dumps({'state':'WRITES_STOPPED_FAILURE_PRESERVED','subject':pin(OUT/'subject.json'),'index':pin(OUT/'preservation-index.json'),'manifest':pin(OUT/'artifact-manifest.json'),'copiedFiles':len(INDEX),'commandReceipts':len(command_paths),'png':len(ui_pngs),'xml':len(ui_xmls),'nonzeroCommands':len(first)},indent=2))
