from pathlib import Path
import hashlib,json,os,stat,subprocess,time,shutil,sys
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence';B=E/'e02-minimum-runtime-preparation-r1';P=E/'e02-ordinary-minimum-preparation-r1'
role=sys.argv[1];assert role in ('incoming','archive')
D=B/(role+'-preflight-r1');D.mkdir(mode=0o700)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while block:=f.read(8*1024*1024):h.update(block)
 return h.hexdigest()
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
def checked(v):
 p=Path(v['path']);assert not p.is_symlink() and p.is_file() and pin(p)==v,v
 return p
def save(name,value):
 fd=os.open(D/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2);f.write('\n')
started=time.time_ns();s=json.loads((P/'subject.json').read_text());assert pin(P/'subject.json')['sha256']=='296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4'
cfg=P/('proposed-'+role+'-run-config.json');config=json.loads(cfg.read_text());assert config['ordinaryRole']==role
for row in s['sources']:checked(row)
for row in config['sourceAndDependencyPins']:checked(row)
for name in ['amethystApk','helperApk','sdkInventory','guardBundleInventory','relayConfig']:checked(config[name])
sdk=Path(config['sdkRoot']);inventory=json.loads(Path(config['sdkInventory']['path']).read_text());rows=[]
for p in sorted(sdk.rglob('*')):
 if p.is_symlink():
  assert p.resolve(strict=True).is_relative_to(sdk);rows.append(dict(path=str(p.relative_to(sdk)),symlink=str(p.readlink())))
 elif p.is_file():
  a=p.stat();h=digest(p);b=p.stat();assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_mode)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_mode)
  rows.append(dict(path=str(p.relative_to(sdk)),size=b.st_size,mode=oct(stat.S_IMODE(b.st_mode)),sha256=h))
 else:assert p.is_dir()
assert rows==inventory['files'];assert sum('sha256' in row for row in rows)==434
client=D/'private-docker-config';client.mkdir(mode=0o700);fd=os.open(client/'config.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write('{}\n')
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','DOCKER_CONFIG':str(client)};images=[]
for image in [config['runtimeImage'],config['relayImage']]:
 argv=['/usr/bin/docker','--host','unix:///var/run/docker.sock','image','inspect','--format','{{.Id}}',image]
 child=subprocess.run(argv,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
 images.append(dict(argv=argv,exitCode=child.returncode,stdout=child.stdout.decode(),stderr=child.stderr.decode()))
 assert child.returncode==0 and child.stdout.decode().strip()==image
fd=os.open('/dev/kvm',os.O_RDWR|os.O_CLOEXEC);device=os.fstat(fd);assert stat.S_ISCHR(device.st_mode);os.close(fd)
lab=Path('/tmp/nbdp-e02-ordinary-minimum-v1');lab.mkdir(mode=0o700,exist_ok=True);out=lab/'runs'/config['runId'];assert not os.path.lexists(out)
mem=next(int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))
free=shutil.disk_usage(lab).free;cpus=sorted(os.sched_getaffinity(0))
save('verification.json',dict(schema='nbdp-minimum-current-input-verification-v1',actor='/root',context='SUPPORTED_HOST',role=role,startedUtcNs=started,finishedUtcNs=time.time_ns(),sourceSubject=pin(P/'subject.json'),configuration=pin(cfg),sdkIndex=pin(Path(config['sdkInventory']['path'])),sdkRegularFiles=434,sdkHashModeMembershipMatched=True,apk=config['amethystApk'],helper=config['helperApk'],images=images,kvmReadWriteOpened=True,kvmVmCreated=False,actualOutput=str(out),measuredFilesystemAncestor=str(lab),filesystemDevice=lab.stat().st_dev,availableDiskBytes=free,memAvailableBytes=mem,affinityCpus=cpus,resourceRequirementsMet=(free>=8*1024**3 and mem>=12*1024**3 and len(cpus)>=8),roleGrantIssued=False,limits=['Read/hash/inspect/open-existing-device only; no Android guest, new Docker container, VM, relay, identity or experiment was started.','Current input/admission probe only, not minimum/peak or guest-health proof. Grant issuance requires a separate fresh resource measurement.']))
raw=Path(__file__).read_bytes();fd=os.open(D/'verification.py',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb') as f:f.write(raw)
print(json.dumps({'verification':pin(D/'verification.json'),'diskFreeBytes':free,'memAvailableBytes':mem,'affinityCpuCount':len(cpus),'kvmOpened':True,'sdk434Matched':True,'noGrantOrRuntime':True}))
