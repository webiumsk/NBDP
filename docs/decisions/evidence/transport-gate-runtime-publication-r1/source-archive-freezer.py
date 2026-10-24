from pathlib import Path
import gzip,hashlib,io,json,os,stat,tarfile
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence';O=E/'transport-gate-runtime-publication-r1';O.mkdir(mode=0o700,exist_ok=True)
closure=E/'e06-qualification-current-source-r3/source-closure.json';members=json.loads(closure.read_bytes());included=[];excluded=[]
for d in members:
 p=Path(d['path'])
 if p.is_relative_to(R):included.append((p,p.relative_to(R).as_posix(),d))
 else:excluded.append(d)
def pin(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
archive=O/'e06-source-graph-repository-files.tar.gz';assert not archive.exists();entries=[]
with archive.open('xb') as raw:
 with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for p,rel,expected in sorted(included,key=lambda x:x[1]):
    assert not p.is_symlink() and p.resolve(strict=True)==p and stat.S_ISREG(p.stat().st_mode)
    b=p.read_bytes();assert len(b)==expected['bytes'] and hashlib.sha256(b).hexdigest()==expected['sha256'],rel
    n='repository/'+rel;t=tarfile.TarInfo(n);t.size=len(b);t.mode=0o600;t.uid=t.gid=t.mtime=0;t.uname=t.gname='';tf.addfile(t,io.BytesIO(b));entries.append(dict(archivePath=n,original=expected))
index=dict(schema='nbdp-bounded-source-publication-v1',scope='Byte-identical repository members of the current449 E06 graph; not an independently portable runtime installation.',sourceClosure=pin(closure),archive=pin(archive),included=entries,excludedExternalOriginals=excluded,counts=dict(included=len(entries),excludedExternal=len(excluded)),limits=['No tool/Chrome/SDK/APK/native executable/TLS key distribution. External originals remain required at exact pinned paths for local qualification.','Historical absolute paths and expired grants are evidence, not replay authority. Fresh reviewed configuration and release remain required.','Repository-member archive restores exact candidate sources/data for inspection; it does not relocate trusted authority or grant experiment execution.','Unrelated preexisting untracked files are not staged by this archive operation.'])
f=O/'e06-source-archive-index.json';assert not f.exists();f.write_text(json.dumps(index,indent=2)+'\n');print(json.dumps({'archive':pin(archive),'index':pin(f),'counts':index['counts']}))
