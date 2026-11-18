from pathlib import Path
import os,json,hashlib,stat,subprocess,shutil,time
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');P=R/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2';O=P/'runtime-preparation-r2';O.mkdir(mode=0o700,exist_ok=False)
def pin(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def save(n,v):
 p=O/n;fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(v,f,indent=2);f.write('\n')
 return pin(p)
def load(p):return json.loads(Path(p).read_bytes())
def checked(d):assert pin(d['path'])==d,d['path'];return Path(d['path'])
source=pin(P/'subject.json');assert source['sha256']=='aece375c76f20d8c738d34e57feb19e50c2ccfc28cb09ffc9347481d2f526b85'
config=load(P/'proposed-run-config.json');config_pin=pin(P/'proposed-run-config.json');assert config_pin['sha256']=='8b91d376814e192b765aba2549f42d185594b8785ecbfac54589f2fc2422dca5'
inputs=P/'current-controls-r1/frozen-inputs.json';inv=load(inputs)
for d in inv['files']:checked(d)
assert len(inv['files'])==920
for d in config['sourceAndDependencyPins']:checked(d)
for name in ['guardBundleInventory','relayConfig']:checked(config[name])
bundle=load(config['guardBundleInventory']['path']);base=Path(config['guardBundleRoot']);seen=set()
for p in base.rglob('*'):
 assert not p.is_symlink(),str(p)
 if p.is_file():seen.add(p.relative_to(base).as_posix())
 else:assert p.is_dir(),str(p)
assert seen==set(bundle['files']) and len(seen)==522
for name,d in bundle['files'].items():
 q=pin(base/name);assert q['bytes']==d['bytes'] and q['sha256']==d['sha256'],name
proto=R/'experiments/prototypes/e02_transport_query_diagnostic_v2';tree=load(proto/'dependency-tree.json');root=Path(tree['sourceRoot']);actual=dict(directories=[],files=[],symlinks=[])
def walk(p):
 for q in sorted(p.iterdir()):
  n=q.relative_to(root).as_posix();s=q.lstat()
  if stat.S_ISLNK(s.st_mode):actual['symlinks'].append(dict(path=n,link=os.readlink(q),target=q.resolve(strict=True).relative_to(root).as_posix()))
  elif stat.S_ISDIR(s.st_mode):actual['directories'].append(n);walk(q)
  else:assert stat.S_ISREG(s.st_mode);actual['files'].append(n)
walk(root)
for k in ['directories','files']:assert sorted(actual[k])==tree[k],k
assert sorted(actual['symlinks'],key=lambda x:x['path'])==tree['symlinks']
fixture=load(proto/'fixture-plan.json')
for d in fixture['dependencyFiles']:
 q=pin(d['source']);assert q['bytes']==d['bytes'] and q['sha256']==d['sha256']
acc=P/'current-controls-r1/results-r1/acceptance.json';a=load(acc);assert a['decision']=='ACCEPT_SCOPED_51_DATA_RESULTS_ONLY' and a['sourceSubject']==source and a['actualScopes']==[18,27,6]
for d in a['reviews']:
 rr=load(checked(d));assert rr['decision']=='ACCEPT_SCOPED_51_DATA_RESULTS_ONLY'
assert {load(d['path'])['role'] for d in a['reviews']}=={'qa','security'}
dc=O/'docker-config';dc.mkdir(mode=0o700);fd=os.open(dc/'config.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(fd,b'{}\n');os.close(fd)
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','DOCKER_HOST':'unix:///var/run/docker.sock','DOCKER_CONFIG':str(dc)};images=[]
for image in [config['runtimeImage'],config['relayImage']]:
 argv=['docker','image','inspect','--format','{{.Id}}',image];r=subprocess.run(argv,env=env,capture_output=True,timeout=15);assert r.returncode==0 and r.stdout.decode().strip()==image
 images.append(dict(argv=argv,exit=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode()))
r=subprocess.run(['docker','version','--format','{{.Client.Version}} {{.Server.Version}}'],env=env,capture_output=True,timeout=15);assert r.returncode==0
mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if len(line.split())>=2 and line.split()[1].isdigit()};free=shutil.disk_usage('/tmp').free;aff=len(os.sched_getaffinity(0))
save('resource-observations.json',dict(observedAtUtcNs=time.time_ns(),freeBytes=free,memAvailableBytes=mem['MemAvailable'],affinityCpuCount=aff))
assert free>=8*1024**3 and mem['MemAvailable']>=2688*1024**2 and aff>=8
out=Path('/tmp/nbdp-e02-transport-query-diagnostic-v2/runs')/config['runId'];assert not out.exists()
v=dict(schema='nbdp-query-source2-fresh-runtime-admission-v1',actor='/root',observedAtUtcNs=time.time_ns(),sourceSubject=source,configuration=config_pin,controlAcceptance=pin(acc),frozenInputs=pin(inputs),verifiedFrozenInputs=920,guardBundleManifest=config['guardBundleInventory'],guardBundleFiles=522,guardBundleExactRegularMembership=True,installedTree=pin(proto/'dependency-tree.json'),installedCounts=dict(files=816,directories=65,symlinks=2),images=images,dockerVersion=dict(exit=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode()),resources=dict(outputFilesystem='/tmp',freeBytes=free,memAvailableBytes=mem['MemAvailable'],affinityCpuCount=aff,coordinatorConservativeFloors=dict(freeBytes=8*1024**3,memAvailableBytes=2688*1024**2,affinityCpuCount=8)),freshOutput=str(out),diagnosticExecuted=False,containersCreated=False,leaseCreated=False,scope='Read-only source/tree/bundle/image/resource verification. No project imports, protocol/native/Android execution or runtime grant; not resource minima/peaks/health proof.')
d=save('fresh-admission.json',v);save('preflight-source.json',pin(Path(__file__).resolve()));print(json.dumps(d))
