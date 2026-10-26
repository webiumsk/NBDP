from pathlib import Path
import gzip,hashlib,io,json,stat,tarfile
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence';O=E/'transport-gate-runtime-publication-r1';root=E/'e02-ordinary-client-resume-r1'
files=sorted(p for p in root.rglob('*') if p.is_file());assert len(files)<=10000 and sum(p.stat().st_size for p in files)<=100*1024**2
archive=O/'e02-raw-attempts-and-readiness.tar.gz';assert not archive.exists();entries=[]
def pin(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
with archive.open('xb') as raw:
 with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for p in files:
    assert p.resolve(strict=True)==p and not p.is_symlink() and stat.S_ISREG(p.stat().st_mode)
    assert p.suffix not in ('.apk','.pem','.key','.keystore','.qcow2','.img') and p.stat().st_size<=32*1024**2
    before=pin(p);b=p.read_bytes();assert len(b)==before['bytes'] and hashlib.sha256(b).hexdigest()==before['sha256'];name='repository/'+p.relative_to(R).as_posix();t=tarfile.TarInfo(name);t.size=len(b);t.mode=0o600;t.uid=t.gid=t.mtime=0;t.uname=t.gname='';tf.addfile(t,io.BytesIO(b));assert pin(p)==before;entries.append(dict(archivePath=name,original=before))
f=O/'e02-raw-archive-index.json';assert not f.exists();f.write_text(json.dumps(dict(schema='nbdp-bounded-raw-publication-v1',scope='All current coordinator-owned E02 readiness/control-preparation and nine negative attempt selected raw graphs, including historical failures.',archive=pin(archive),members=entries,counts=dict(files=len(entries),logicalBytes=sum(x['original']['bytes'] for x in entries)),limits=['All nine ordinary-client attempts remain FAILED_UNQUALIFIED; archive membership is not acceptance.','No APK/debugkeystore/SDK/AVDdisk/credentials are distributed. All identity content uses declared public disposable test keys.','Runtime records retain original absolute paths; archive contains repository mirrors. It is not a fresh release or self-contained environment.']),indent=2)+'\n');print(json.dumps({'archive':pin(archive),'index':pin(f),'members':len(entries)}))
