"""Root foreground, once-only release materialization and exact bounded launch."""
import hashlib,json,os,pathlib,resource,subprocess,time
os.umask(0o077)
HERE=pathlib.Path(__file__).resolve().parent
BASE=pathlib.Path('/tmp/nbdp-e02-primary-replay-20261027-preparation')
def pin(p):
    p=pathlib.Path(p)
    assert p.is_file() and not p.is_symlink()
    h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def put(name,data):
    with (HERE/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
def main():
    t=json.loads((HERE/'release-template.json').read_text())
    auth=json.loads((HERE/'coordinator-runtime-authorization.json').read_text())
    assert auth['executionAuthorized'] is True and auth['scope']=='ONE_CURRENT_ORIGINAL_PRIMARY22_ONLY'
    assert auth['caller']==pin(__file__) and auth['template']==pin(HERE/'release-template.json')
    for d in auth['reviews']:assert pin(d['path'])==d
    assert not (HERE/'root-release.json').exists() and not (HERE/'outer-request.json').exists()
    for key in ('plan','sourceSubject','sourceQa','sourceSecurity','modelAcceptance','inputAcceptance'):
        assert pin(t[key]['path'])==t[key]
    for d in json.loads(pathlib.Path(t['sourceSubject']['path']).read_text())['sources']:
        assert pin(d['path'])==d
    plan=json.loads(pathlib.Path(t['plan']['path']).read_text())
    for d in plan['tools'].values():assert pin(d['path'])==d
    assert t['executionAuthorized'] is True and t['scope']=='CURRENT_ORIGINAL_PRIMARY22_ONLY'
    assert not (BASE/('attempt-'+t['runId'])).exists()
    t['issuedAtUtcNs']=time.time_ns();t['notAfterUtcNs']=t['issuedAtUtcNs']+600*10**9
    put('root-release.json',t);release=pin(HERE/'root-release.json')
    argv=['/usr/bin/timeout','--signal=TERM','--kill-after=3s','597s','/usr/bin/python3.12','-I','-B',str(BASE/'launch.py'),'--plan-sha',t['plan']['sha256'],'--release',release['path'],'--release-sha',release['sha256']]
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    put('outer-request.json',dict(argv=argv,cwd=str(BASE),environment=env,release=release,startedUtcNs=time.time_ns(),retryAuthorized=False))
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    start=time.monotonic()
    with (HERE/'outer.stdout').open('xb') as out,(HERE/'outer.stderr').open('xb') as err:
        p=subprocess.Popen(argv,cwd=BASE,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True,preexec_fn=limits)
        put('outer-child.json',dict(pid=p.pid,ownedPopenHandle=True))
        code=p.wait(timeout=605)
    put('outer-result.json',dict(exitCode=code,reaped=True,durationSeconds=time.monotonic()-start,stdout=pin(HERE/'outer.stdout'),stderr=pin(HERE/'outer.stderr'),cleanupMustBeReviewed=True,retryAuthorized=False,attemptPath=str(BASE/('attempt-'+t['runId']))))
    print(json.dumps(dict(exitCode=code,attemptPath=str(BASE/('attempt-'+t['runId'])),durationSeconds=time.monotonic()-start)))
    return code
if __name__=='__main__':raise SystemExit(main())
