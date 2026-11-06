import hashlib,json,os,pathlib,selectors,signal,subprocess,time
os.umask(0o077)
base=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3')
out=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-capture-admission9-actual-20261028')
out.mkdir(mode=0o700)
def pin(p):
    p=pathlib.Path(p);h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):n+=len(b);h.update(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest(),mode=oct(p.stat().st_mode&0o777))
subject=json.loads((base/'subject.json').read_text())
method=json.loads((base/'admission9-method.json').read_text())
paths=[base/n for n in ('subject.json','source-packet.json','test_admission_models.py','capture-template.py','assemble-source-only.py','admission9-method.json','source-qa.json','source-security.json')]
for mode in ('capture-a','capture-b'):
    paths.extend(base/mode/n for n in ('capture-controls.py','runner-subject.json','control-plan.json','frozen-inputs.json'))
paths.extend(pathlib.Path(v) for v in ('/usr/bin/env','/usr/bin/timeout','/home/peterhorvath/.miniforge3/bin/python3.13'))
paths.extend(pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-data-contract-20261028')/n for n in ('contract.json','model-subject-contract.json'))
paths=list(dict.fromkeys(paths));before=[pin(p) for p in paths]
assert pin(base/'subject.json')['sha256']=='e103370b6e1f9b6e2f1a133f9c7653cb29612a04b02f7f4f3032d16b9f424c1e'
assert pin(base/'test_admission_models.py')['sha256']=='5f57204e46147976d6137618fd67d19ce8585294905ed5fb94a22f1479e25417'
argv=method['argv']
release=dict(actor='/root',executionAuthorized=True,scope='Exactlyonce9pureadmissionbodies; fixedreviewedargv asCHILD, outerPythonfinitecapturehonestlyseparate; no controls/SDK/native/Android/services',argv=argv,inputsBefore=before,seconds=60,stdoutBytes=1048576,stderrBytes=262144,sourceReviews=[pin(base/'source-qa.json'),pin(base/'source-security.json')],snapshotNotRaceFree=True)
(out/'root-release.json').write_text(json.dumps(release,indent=2)+'\n')
start=time.monotonic();p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'})
sel=selectors.DefaultSelector();buffers={};eof={};fault=None
for name,pipe,cap in [('stdout',p.stdout,1048576),('stderr',p.stderr,262144)]:
    os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,(name,cap));buffers[name]=bytearray();eof[name]=False
while sel.get_map():
    if time.monotonic()-start>60: fault='TIMEOUT';break
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
result=dict(argv=argv,exitCode=code,reaped=True,eof=eof,fault=fault,durationSeconds=time.monotonic()-start,inputsBefore=before,inputsAfter=after,inputsUnchanged=before==after,stdout=pin(out/'stdout.raw'),stderr=pin(out/'stderr.raw'),scope='Actual9pureadmissionmodels only; no20/8/7/3controlorDocker/native/proxy/clientexecution',snapshotNotRaceFree=True)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('exitCode','reaped','eof','fault','durationSeconds','inputsUnchanged')}))
assert code==0 and not fault and all(eof.values()) and before==after
import re
assert buffers['stdout']==b'' and re.fullmatch(rb'\.{9}\n-+\nRan 9 tests in [0-9]+\.[0-9]+s\n\nOK\n',bytes(buffers['stderr'])), 'EXACT_NINE_QUIET_OUTCOME_REQUIRED'
