from pathlib import Path
import gzip,hashlib,io,json,stat,tarfile,sys
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence';O=E/'transport-gate-runtime-publication-r1'
sets={
 'e06-control-and-input-runtime': ['e06-policy-marker-remediation-r1','e06-qualification-inventory-refresh-r1','e06-qualification-current-source-r1','e06-qualification-current-source-r2','e06-qualification-current-source-r3','e06-current-controls-r1','e06-current-controls-r2','e06-current-marker-controls-r1','e06-current-marker-controls-r2','e06-inventory-enforcement-r1','e06-inventory-enforcement-r2','e06-inventory-enforcement-r3','e06-opaque-inventory-remediation-r1','e06-opaque-inventory-controls-r1','e06-inventory-enforcement-matrix-r1'],
 'e02-health-and-aggregate': ['e02-android-anr-diagnosis-r1','e02-android-health-preparation-r1','e02-android-health-preparation-r2','e02-android-health-runtime-r1','e02-ordinary-aggregate-original-review-r1','e02-ordinary-aggregate-remediation-r1','e02-ordinary-aggregate-controls-r1']}
name=sys.argv[1];assert name in sets;roots=[E/x for x in sets[name]]
for p in roots:assert p.is_dir() and not p.is_symlink()
files=sorted(p for root in roots for p in root.rglob('*') if p.is_file());assert len(files)==len(set(files)) and len(files)<=10000
assert sum(p.stat().st_size for p in files)<=200*1024**2
def pin(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
archive=O/(name+'.tar.gz');assert not archive.exists();entries=[]
with archive.open('xb') as raw:
 with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for p in files:
    assert p.resolve(strict=True)==p and not p.is_symlink() and stat.S_ISREG(p.stat().st_mode)
    assert p.suffix not in ('.apk','.pem','.key','.keystore','.qcow2','.img','.so') and p.stat().st_size<=64*1024**2
    before=pin(p);b=p.read_bytes();assert len(b)==before['bytes'] and hashlib.sha256(b).hexdigest()==before['sha256'];n='repository/'+p.relative_to(R).as_posix();t=tarfile.TarInfo(n);t.size=len(b);t.mode=0o600;t.uid=t.gid=t.mtime=0;t.uname=t.gname='';tf.addfile(t,io.BytesIO(b));assert pin(p)==before;entries.append(dict(archivePath=n,original=before))
f=O/(name+'-index.json');assert not f.exists();f.write_text(json.dumps(dict(schema='nbdp-bounded-supplement-publication-v1',scope=name,archive=pin(archive),roots=[str(p.relative_to(R)) for p in roots],members=entries,counts=dict(files=len(entries),logicalBytes=sum(x['original']['bytes'] for x in entries)),limits=['Originalscope/findings/failuresandactualsource-specificacceptancespreserved; publicationisnotfreshapproval.','NoSDK/APK/AVDdisk/tool/TLSkeys/credentials; source/runtimegraphsretainexternaloriginalrequirements.','Archivecontainsrepositorymirrors, nottrustedrelocation; currentexactreviewedconfig/releaserequiredfornewruns.']),indent=2)+'\n');print(json.dumps({'archive':pin(archive),'index':pin(f),'files':len(entries)}))
