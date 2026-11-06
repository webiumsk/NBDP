"""SOURCE-only launcher; requires independently reviewed plan and root release."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

HERE = Path(__file__).resolve().parent

def need(value, why):
    if not value:
        raise ValueError(why)

def pin(path):
    path = Path(path)
    need(path.is_absolute() and path.resolve(strict=True)==path and path.is_file() and not path.is_symlink(), 'canonical regular input')
    h = hashlib.sha256()
    with path.open('rb') as handle:
        before=os.fstat(handle.fileno())
        for chunk in iter(lambda:handle.read(1048576),b''): h.update(chunk)
        after=os.fstat(handle.fileno())
    identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    need(identity(before)==identity(after)==identity(path.stat()),'input changed during hash')
    return {'path':str(path),'bytes':after.st_size,'sha256':h.hexdigest()}

def checked(d):
    need(type(d) is dict and set(d)=={'path','bytes','sha256'} and pin(d['path'])==d,'exact descriptor')
    return Path(d['path'])

def doc(path):
    raw=Path(path).read_bytes()
    need(len(raw)<=16777216,'bounded metadata')
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate metadata key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'nonfinite metadata'))

def snapshot(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix();mode=oct(stat.S_IMODE(p.lstat().st_mode))
        if p.is_symlink():
            target=p.resolve(strict=True);need(target.is_relative_to(root),'symlink escape')
            rows.append({'path':rel,'type':'symlink','mode':mode,'link':str(p.readlink()),'target':target.relative_to(root).as_posix()})
        elif p.is_dir():rows.append({'path':rel,'type':'directory','mode':mode})
        elif p.is_file():
            d=pin(p);rows.append({'path':rel,'type':'file','mode':mode,'bytes':d['bytes'],'sha256':d['sha256']})
        else:raise ValueError('special input')
    return rows

def main(args):
    need(len(args)==4,'PLAN EXTERNAL_PLAN_SHA RELEASE EXTERNAL_RELEASE_SHA')
    plan_path,plan_sha,release_path,release_sha=args
    plan_pin,release_pin=pin(plan_path),pin(release_path)
    need(plan_pin['sha256']==plan_sha and release_pin['sha256']==release_sha,'external root pins')
    p,r=doc(plan_path),doc(release_path)
    need(p['schema']=='nbdp-e01-isolated-replay-source-plan-v1' and p['state']=='SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_RELEASE' and not p['missing'],'ready exact SOURCE plan')
    need(set(r)==set('schema executionAuthorized plan qaReview securityReview nativeBuildAcceptance issuedAtUtcMillis notAfterUtcMillis maximumTestSeconds'.split()),'closed root release')
    need(r['schema']=='nbdp-e01-isolated-replay-root-release-v1' and r['executionAuthorized'] is True and r['plan']==plan_pin,'exact root authorization')
    for k in ('qaReview','securityReview','nativeBuildAcceptance'):checked(r[k])
    now=time.time_ns()//1000000
    need(type(r['issuedAtUtcMillis']) is int and type(r['notAfterUtcMillis']) is int and r['issuedAtUtcMillis']<=now and now+242000<=r['notAfterUtcMillis']<=r['issuedAtUtcMillis']+600000,'fresh bounded root release')
    need(r['maximumTestSeconds']==p['maximumTestSeconds']==240 and p['terminationGraceSeconds']==2,'original proposed wall bound')
    need(checked(p['launcher'])==Path(__file__).resolve(),'reviewed exact launcher')
    for d in p['tools'].values():checked(d)
    checked(p['native']);checked(p['nativeSourceDeclaration']['expectedReplyValueEqualsExactFile'])
    checked(p['preparationSource']);checked(p['historicalComparison'])
    inventory=doc(checked(p['inputInventory']))
    root=Path(p['lab']);need(root==HERE/'lab' and root.resolve(strict=True)==root,'fixed fresh lab')
    need(inventory['root']==str(root) and snapshot(root)==inventory['rows'],'complete unchanged copied input closure')
    comparison=doc(checked(p['historicalComparison']))
    need(comparison['allEqual'] is True and comparison['sourceCount']==19,'all historical canonical source pins')
    cwd=root/'experiments';need(p['cwd']==str(cwd),'fixed cwd')
    need(not any((cwd/'results').iterdir()) and not any((cwd/'fixtures/generated').iterdir()),'fresh untouched output directories')
    argv=[p['tools']['timeout']['path'],'--signal=TERM','--kill-after=2s','240s',p['tools']['node']['path'],'shared/run.mjs','E01']
    need(p['argv']==argv,'fixed E01 only command')
    expected_env={'PATH':'/usr/bin:/bin','HOME':str(root/'home'),'TMPDIR':str(root/'tmp'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','NBDP_CHROME':'/usr/bin/false','NBDP_RUST_BIN':p['native']['path']}
    need(p['environment']==expected_env,'closed loader-free environment')
    os.chdir(cwd)
    os.execve(argv[0],argv,expected_env)

if __name__=='__main__':
    main(sys.argv[1:])
