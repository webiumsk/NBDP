"""Root once-only exact official archive acquisition; no acquired tools run."""
import hashlib,json,os,pathlib,selectors,signal,subprocess,time
os.umask(0o077)
BASE=pathlib.Path('/tmp/nbdp-e02-sdkmanager-install-20261027-preparation')
HERE=pathlib.Path(__file__).resolve().parent
def pin(p):
    p=pathlib.Path(p);assert p.is_file() and not p.is_symlink()
    h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def put(n,d):
    with (HERE/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
    release=json.loads((HERE/'root-release.json').read_text())
    assert release['executionAuthorized'] is True and release['scope']=='ONE_FIXED_CMDLINE22_ARCHIVE_FETCH_AND_EXTRACTION_ONLY'
    assert release['caller']==pin(__file__)
    for d in release['inputs']:assert pin(d['path'])==d
    for d in release['reviews']:assert pin(d['path'])==d
    for p in (BASE/'cache/cmdline-tools.archive',BASE/'cache/cmdline-tools.partial',BASE/'bootstrap/cmdline-tools/22.0',BASE/'bootstrap/.stage-cmdline-tools',BASE/'output/acquisition'):
        assert not p.exists() and not p.is_symlink()
    argv=['/usr/bin/timeout','--signal=TERM','--kill-after=3s','1800s','/usr/bin/python3.12','-I','-B',str(BASE/'acquire.py'),'--plan-sha','3e7d4f81f4d99b1d1563c4e5cbdf4679562bc3978493ff22ec9f61deb4aaafb8']
    assert release['argv']==argv
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    put('request.json',dict(argv=argv,cwd=str(BASE),environment=env,startedUtcNs=time.time_ns(),release=pin(HERE/'root-release.json'),retryAuthorized=False))
    start=time.monotonic();p=subprocess.Popen(argv,cwd=BASE,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    put('child.json',dict(pid=p.pid,ownedPopenHandle=True))
    sel=selectors.DefaultSelector();buffers={};eof={};fault=None
    for name,pipe,cap in [('stdout',p.stdout,65536),('stderr',p.stderr,262144)]:
        os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,(name,cap));buffers[name]=bytearray();eof[name]=False
    while sel.get_map():
        if time.monotonic()-start>1805:fault='CAPTURE_WALL_TIMEOUT';break
        for key,_ in sel.select(.1):
            name,cap=key.data;b=os.read(key.fd,8192)
            if not b:sel.unregister(key.fileobj);eof[name]=True;continue
            if len(buffers[name])+len(b)>cap:fault='CAPTURE_LIMIT';break
            buffers[name].extend(b)
        if fault:break
    if fault:os.killpg(p.pid,signal.SIGKILL)
    code=p.wait(timeout=5)
    for name,b in buffers.items():
        with (HERE/(name+'.raw')).open('xb') as f:f.write(b)
    after=[pin(d['path']) for d in release['inputs']]
    result=dict(exitCode=code,reaped=True,eof=eof,fault=fault,durationSeconds=time.monotonic()-start,inputsBefore=release['inputs'],inputsAfter=after,inputsUnchanged=release['inputs']==after,stdout=pin(HERE/'stdout.raw'),stderr=pin(HERE/'stderr.raw'),noAcquiredToolsInvoked=True,licenseConsentPerformed=False,retryAuthorized=False,snapshotNotRaceFree=True)
    put('result.json',result)
    print(json.dumps({k:result[k] for k in ('exitCode','reaped','eof','fault','durationSeconds','inputsUnchanged')}))
    return 0 if code==0 and not fault and all(eof.values()) and result['inputsUnchanged'] else 2
if __name__=='__main__':raise SystemExit(main())
