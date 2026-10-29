"""One concrete reviewed SDK install dispatch. Only root materializes its lease."""
import hashlib,json,os,pathlib,resource,subprocess,time
os.umask(0o077)
HERE=pathlib.Path(__file__).resolve().parent
CTRL=pathlib.Path('/Data/nbdp-e02-tooling-20261027/controller-r3')
def pin(p):
    p=pathlib.Path(p);assert p.is_file() and not p.is_symlink()
    h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def put(n,d):
    with (HERE/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
    t=json.loads((HERE/'release-template.json').read_text())
    a=json.loads((HERE/'coordinator-authorization.json').read_text())
    assert a['executionAuthorized'] is True and a['scope']=='ONE_EXACT_THREE_PACKAGE_SDK_INSTALL_ONLY'
    assert a['caller']==pin(__file__) and a['template']==pin(HERE/'release-template.json') and a['tools']==pin(HERE/'caller-tools.json')
    for d in a['reviews']:assert pin(d['path'])==d
    for d in json.loads((HERE/'caller-tools.json').read_text()):assert pin(d['path'])==d
    assert not (HERE/'root-release.json').exists() and not (HERE/'request.json').exists()
    assert t['executionAuthorized'] is True and t['scope']=='EXACT_THREE_PACKAGE_SDK_INSTALL_ONLY'
    assert t['controllerSubject']['path']==str(CTRL/'subject.json')
    for name in ('plan','controllerSubject','installSubject','installPlan','sdkLicenseDecision','jdkExtraction','bootstrapExtraction','inputBundleInventory'):
        assert pin(t[name]['path'])==t[name]
    for name in ('sourceReviews','prerequisiteAcceptances'):
        for d in t[name]:assert pin(d['path'])==d
    for name in ('controllerSubject','installSubject'):
        for d in json.loads(pathlib.Path(t[name]['path']).read_text())['sources']:assert pin(d['path'])==d
    assert not (CTRL/('attempt-'+t['runId'])).exists() and not (CTRL/'writable-r1').exists()
    t['issuedAtUtcNs']=time.time_ns();t['notAfterUtcNs']=t['issuedAtUtcNs']+1200*10**9
    put('root-release.json',t);release=pin(HERE/'root-release.json')
    argv=['/usr/bin/timeout','--signal=TERM','--kill-after=3s','1197s','/usr/bin/python3.12','-I','-B',str(CTRL/'controller.py'),'--release',release['path'],'--release-sha',release['sha256']]
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    put('request.json',dict(argv=argv,cwd=str(CTRL),environment=env,release=release,startedUtcNs=time.time_ns(),retryAuthorized=False))
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    start=time.monotonic()
    with (HERE/'outer.stdout').open('xb') as out,(HERE/'outer.stderr').open('xb') as err:
        p=subprocess.Popen(argv,cwd=CTRL,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True,preexec_fn=limits)
        put('child.json',dict(pid=p.pid,ownedPopenHandle=True))
        code=p.wait(timeout=1205)
    d=dict(exitCode=code,reaped=True,durationSeconds=time.monotonic()-start,stdout=pin(HERE/'outer.stdout'),stderr=pin(HERE/'outer.stderr'),attemptPath=str(CTRL/('attempt-'+t['runId'])),newWritableRoot=str(CTRL/'writable-r1'),independentInstallationAndConsentReviewRequired=True,retryAuthorized=False)
    put('result.json',d)
    print(json.dumps({k:d[k] for k in ('exitCode','reaped','durationSeconds','attemptPath','newWritableRoot')}))
    return code
if __name__=='__main__':raise SystemExit(main())
