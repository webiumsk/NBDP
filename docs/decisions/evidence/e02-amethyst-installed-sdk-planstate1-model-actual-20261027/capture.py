import hashlib,json,os,pathlib,selectors,signal,subprocess,time
os.umask(0o077)
base=pathlib.Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r5')
out=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-amethyst-installed-sdk-planstate1-model-actual-20261027')
out.mkdir(mode=0o700)
def pin(p):
    p=pathlib.Path(p);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),mode=oct(p.stat().st_mode&0o777))
subject=json.loads((base/'subject.json').read_text())
paths=[base/'subject.json',*[pathlib.Path(d['path']) for d in subject['sources']],pathlib.Path('/usr/bin/python3.12')]
operands=json.loads((base/'model-plan.json').read_text())['directFileOperands']
paths=list(dict.fromkeys(paths+[pathlib.Path(d['path']) for d in operands]))
before=[pin(p) for p in paths]
assert any(d['path']==str(base/'model-plan.json') and d['sha256']=='33a4d9e06833df8e6652cbe5cec3ba9e3f10105880445033cf3767d742048d04' for d in before)
argv=['/usr/bin/python3.12','-I','-B',str(base/'test_plan_state.py')]
release=dict(actor='/root',executionAuthorized=True,scope='Exactly once fixed1 pure source/AST planstate admission regression; explicit4fileoperands only; no imports/SDK/Gradle/runtime',argv=argv,inputsBefore=before,seconds=15,stdoutBytes=65536,stderrBytes=262144,sourceReviews=['source-qa.json','source-security.json'],snapshotNotRaceFree=True)
(out/'root-release.json').write_text(json.dumps(release,indent=2)+'\n')
start=time.monotonic();p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'})
sel=selectors.DefaultSelector();buffers={};eof={};fault=None
for name,pipe,cap in [('stdout',p.stdout,65536),('stderr',p.stderr,262144)]:
    os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,(name,cap));buffers[name]=bytearray();eof[name]=False
while sel.get_map():
    if time.monotonic()-start>15: fault='TIMEOUT';break
    for key,_ in sel.select(.05):
        name,cap=key.data;b=os.read(key.fd,8192)
        if not b:sel.unregister(key.fileobj);eof[name]=True;continue
        if len(buffers[name])+len(b)>cap:fault='CAPTURE_LIMIT';break
        buffers[name].extend(b)
    if fault:break
if fault:
    os.killpg(p.pid,signal.SIGKILL)
code=p.wait(timeout=3)
for name,b in buffers.items():(out/(name+'.raw')).write_bytes(b)
after=[pin(q) for q in paths]
result=dict(argv=argv,exitCode=code,reaped=True,eof=eof,fault=fault,durationSeconds=time.monotonic()-start,inputsBefore=before,inputsAfter=after,inputsUnchanged=before==after,stdout=pin(out/'stdout.raw'),stderr=pin(out/'stderr.raw'),scope='Actual pure model DATA only; no Docker/native/proxy/client execution',snapshotNotRaceFree=True)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('exitCode','reaped','eof','fault','durationSeconds','inputsUnchanged')}))
assert code==0 and not fault and all(eof.values()) and before==after
