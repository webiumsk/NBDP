from pathlib import Path
import os,json,stat,hashlib,subprocess,shutil
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');run=Path('/tmp/nbdp-e02-ordinary-client-api35-v1/runs/c0fb2643c4c8453091db09bdd36aad5c');image=run/'android-state/avd/ordinary.avd/userdata-qemu.img.qcow2';P=R/'docs/decisions/evidence/e02-owned-avd-overlay-reclamation-r4';P.mkdir(mode=0o700,exist_ok=False)
def descriptor(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def save(name,v):
 fd=os.open(P/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
result=run/'supervisor-result.json';assert descriptor(result)['sha256']=='5ed98d534869f1257fa02d429c15ed0f1f1a0a761b5140fa3d4f77a5d3b2ad92';v=json.loads(result.read_bytes());assert v['executionState']=='FAILED_UNQUALIFIED' and v['cleanup']['ok'] and len(v['cleanup']['rows'])==4
accept=R/'docs/decisions/evidence/e02-ordinary-api35-runtime-r1/acceptance.json';assert json.loads(accept.read_bytes())['ordinaryCellQualified'] is False
checks=[]
for row in v['cleanup']['rows']:
 assert row['absenceConfirmed'] and row['identityVerified']
 c=subprocess.run(['docker','inspect',row['cid']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15);assert c.returncode==1 and c.stdout.strip()==b'[]' and c.stderr.decode().strip().lower()=='error: no such object: '+row['cid'];checks.append(dict(cid=row['cid'],exit=c.returncode,stdout=c.stdout.decode(),stderr=c.stderr.decode()))
for p in (image,*image.parents):assert not p.is_symlink()
s=image.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==1000 and s.st_gid==1000 and s.st_size==856293376
f=subprocess.run(['fuser',str(image)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15);assert f.returncode==1 and not f.stdout and not f.stderr
profiles=[descriptor(run/'android-state/avd/ordinary.avd'/name) for name in ('config.ini','hardware-qemu.ini')]
before=dict(schema='nbdp-owned-overlay-reclamation-before-v1',actor='/root',target=descriptor(image),device=s.st_dev,inode=s.st_ino,ownerUid=s.st_uid,ownerGid=s.st_gid,nlink=s.st_nlink,allocatedBytes=s.st_blocks*512,mtimeNs=s.st_mtime_ns,mode=oct(s.st_mode),holderCheck=dict(exit=f.returncode,stdout='',stderr=''),exactContainersAbsent=checks,preservedProfiles=profiles,actualFailure=descriptor(result),independentAcceptance=descriptor(accept),freeBefore=shutil.disk_usage(run).free,limits='Onlythisfinishedowneddisposableuserdataimage; allrepositorysource/raw/UI/keys/configs/otheruserfilespreserved. Excludedfromimmutableevidencecopy; oldexclusionmetadataremainhistorical.')
save('before.json',before)
t=image.lstat();assert (t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns,t.st_nlink)==(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink);assert not image.is_symlink();image.unlink();assert not image.exists()
for d in profiles:assert descriptor(Path(d['path']))==d
save('result.json',dict(schema='nbdp-owned-overlay-reclamation-result-v1',actor='/root',before=descriptor(P/'before.json'),removed=before['target'],profilesPreserved=True,freeAfter=shutil.disk_usage(run).free,requiredFreshFutureAdmissionBytes=8589934592,experimentExecuted=False,limits='No source/gate/lease/profile/userdataoutsideexactownedtarget changed; actualfuturegrantstillrequiresfreshresourceadmission.'))
print(json.dumps(json.loads((P/'result.json').read_bytes())))
