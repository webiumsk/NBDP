"""One root-authorized, fresh guarded full-CID stop; controller owns cleanup."""
import hashlib,importlib.util,json,os,pathlib,resource,subprocess,time
os.umask(0o077)
HERE=pathlib.Path(__file__).resolve().parent
BASE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r3')
SOURCE=BASE/'supervisor-source/supervise_build.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='41d8951bae82784fcd90716bdbcbc84956072186eb3e1bd9ff280d437768572c'
a=json.loads((HERE/'authorization.json').read_text())
assert a['executionAuthorized'] is True and a['scope']=='ONE_FRESH_GUARDED_EXACT_OWNED_CONTAINER_STOP_ONLY'
cid=a['cid'];run=a['runId'];network='acf4c0e2d847dedb7841a18c0713ba9b58ad680d686c2d43d95612f54ff6ff9b'
assert cid=='b54aaa41431940d61be299ff3ac32fd5cfb2bba81850ccf22f5a70b25af11e4e' and run=='ac42a6574b749180898382ce8cba2afd'
spec=importlib.util.spec_from_file_location('fixed_owned_guard',SOURCE);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
plan=json.loads((BASE/'preparation/build-plan.json').read_text())
assert hashlib.sha256((BASE/'preparation/build-plan.json').read_bytes()).hexdigest()=='97bb6e92f4ab0ccde47b3327a94b6ae3cce3978458ab3155d33c6abb0abfb424'
(HERE/'docker-config').mkdir(mode=0o700)
def put(name,d):
    with (HERE/name).open('x') as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def pin(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def call(label,args):
    argv=['/usr/bin/timeout','--signal=TERM','--kill-after=3s','25s','/usr/bin/docker',*args]
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','DOCKER_CONFIG':str(HERE/'docker-config')}
    put(label+'-request.json',dict(actor='/root',argv=argv,environment=env,operatorIntervention=True))
    def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    out=HERE/(label+'.stdout');err=HERE/(label+'.stderr');start=time.monotonic()
    with out.open('xb') as o,err.open('xb') as e:
        p=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=o,stderr=e,env=env,preexec_fn=limits,check=False)
    result=dict(actor='/root',exitCode=p.returncode,elapsedSeconds=time.monotonic()-start,stdout=pin(out),stderr=pin(err),operatorIntervention=True)
    put(label+'-result.json',result);return result,out,err
inspection,out,err=call('inspect-fullcid',['inspect','--type','container',cid])
assert inspection['exitCode']==0 and err.read_bytes()==b''
d=guard.owned_identity(json.loads(out.read_bytes()),cid,run,plan,network)
put('fresh-owned-identity.json',dict(cid=cid,runId=run,image=d['Image'],state=d['State'],guardSourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),allFrozenOwnershipConfigMountNetworkResourceChecksPassed=True))
if d['State']['Running'] is True:
    stopped,_,_=call('stop-fullcid',['stop','--time','10',cid])
    put('result.json',dict(actor='/root',state='OPERATOR_STOP_ISSUED_PENDING_ORIGINAL_CONTROLLER_FINAL_RECONCILIATION',cid=cid,stopExitCode=stopped['exitCode'],retryAuthorized=False,goalContinues=True))
else:put('result.json',dict(actor='/root',state='ALREADY_NOT_RUNNING_NO_STOP_ISSUED',cid=cid,retryAuthorized=False,goalContinues=True))
print((HERE/'result.json').read_text(),end='')
