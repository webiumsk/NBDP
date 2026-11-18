"""Two fixed read-only tool probes; no package installation or license response."""
import hashlib,json,os,pathlib,selectors,signal,subprocess,time,stat
os.umask(0o077)
HERE=pathlib.Path(__file__).resolve().parent
def pin(p):
    p=pathlib.Path(p);assert p.is_file() and not p.is_symlink()
    h=hashlib.sha256();n=0
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b);n+=len(b)
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def put(n,d):
    with (HERE/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def verify_tree(receipt):
    d=json.loads(pathlib.Path(receipt['path']).read_text());root=pathlib.Path(d['destination']);actual=[]
    for p in sorted(root.rglob('*')):
        rel=str(p.relative_to(root));mode=oct(stat.S_IMODE(p.lstat().st_mode))
        if p.is_symlink():actual.append(dict(path=rel,kind='symlink',target=os.readlink(p)))
        elif p.is_dir():actual.append(dict(path=rel,kind='dir',mode=mode))
        else:
            q=pin(p);actual.append(dict(path=rel,kind='file',bytes=q['bytes'],sha256=q['sha256'],mode=mode))
    assert actual==d['inventory']
    return dict(receipt=receipt,root=str(root),rows=len(actual),exact=True)
def capture(command,env):
    name,argv=command['name'],command['argv'];start=time.monotonic()
    put(name+'-request.json',dict(argv=argv,cwd=str(HERE),environment=env,startedUtcNs=time.time_ns(),stdin='DEVNULL_NO_RESPONSE'))
    p=subprocess.Popen(argv,cwd=HERE,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    sel=selectors.DefaultSelector();buffers={};eof={};fault=None
    for key,pipe,cap in [('stdout',p.stdout,1048576),('stderr',p.stderr,262144)]:
        os.set_blocking(pipe.fileno(),False);sel.register(pipe,selectors.EVENT_READ,(key,cap));buffers[key]=bytearray();eof[key]=False
    while sel.get_map():
        if time.monotonic()-start>30:fault='PROBE_TIMEOUT';break
        for key,_ in sel.select(.05):
            name2,cap=key.data;b=os.read(key.fd,8192)
            if not b:sel.unregister(key.fileobj);eof[name2]=True;continue
            if len(buffers[name2])+len(b)>cap:fault='PROBE_CAPTURE_LIMIT';break
            buffers[name2].extend(b)
        if fault:break
    if fault:os.killpg(p.pid,signal.SIGKILL)
    code=p.wait(timeout=3)
    for key,b in buffers.items():
        with (HERE/(name+'.'+key)).open('xb') as f:f.write(b)
    d=dict(exitCode=code,reaped=True,eof=eof,fault=fault,durationSeconds=time.monotonic()-start,stdout=pin(HERE/(name+'.stdout')),stderr=pin(HERE/(name+'.stderr')))
    put(name+'-result.json',d)
    assert code==0 and not fault and all(eof.values())
    if name=='version':assert bytes(buffers['stdout']).rstrip(b'\r\n')==b'22.0'
def main():
    p=json.loads((HERE/'plan.json').read_text());r=json.loads((HERE/'root-release.json').read_text())
    assert r['executionAuthorized'] is True and r['scope']=='TWO_FIXED_JDK21_CMDLINE22_READ_ONLY_PROBES_ONLY'
    assert r['source']==pin(__file__) and r['plan']==pin(HERE/'plan.json')
    for d in [*p['inputs'],*r['reviews']]:assert pin(d['path'])==d
    assert len(p['commands'])==2 and [c['name'] for c in p['commands']]==['javap','version']
    assert not (HERE/'before.json').exists()
    put('before.json',dict(inputs=p['inputs'],trees=[verify_tree(d) for d in p['trees']]))
    root=pathlib.Path(p['freshRoot']);assert not root.exists() and not root.is_symlink();root.mkdir(mode=0o700)
    for directory in p['freshDirectories']:
        q=pathlib.Path(directory);assert not q.exists() and not q.is_symlink();q.mkdir(mode=0o700,parents=True)
    first=None
    try:
        for command in p['commands']:capture(command,p['environment'])
    except BaseException as e:first=type(e).__name__+':'+str(e)
    finally:
        after=[pin(d['path']) for d in p['inputs']]
        unchanged=after==p['inputs'];trees=[verify_tree(d) for d in p['trees']]
        put('result.json',dict(firstFault=first,inputsAfter=after,inputsUnchanged=unchanged,treesAfter=trees,licenseResponseSent=False,packageInstallRequested=False,sdkmanagerVersionOnly=True,snapshotsNotRaceFree=True))
    assert first is None and unchanged
    print(json.dumps(dict(state='PROBES_COMPLETED_PENDING_INDEPENDENT_DATA_REVIEW',licenseResponseSent=False,packageInstallRequested=False)))
if __name__=='__main__':main()
