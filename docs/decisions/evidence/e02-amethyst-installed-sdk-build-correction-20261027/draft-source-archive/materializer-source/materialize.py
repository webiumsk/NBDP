"""One preauthorized fixed build dispatch. SOURCE preparation grants nothing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

HERE=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-r4/materializer')
SOURCE=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r4/supervisor-source')
WORK=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-r4/controller')
PYTHON='/home/peterhorvath/.miniforge3/bin/python3.13'
PINNED=None  # DRAFT: prior-negative/post-input DATA and explicit method adoption required.

CLOCKS={'issuedAtUtcNs','notAfterUtcNs'}
RELEASE_KEYS=set('schema actor executionAuthorized scope runId issuedAtUtcNs notAfterUtcNs supervisorSubject buildPreparationSubject sourceReviews prerequisiteAcceptances sourceArchive sourceArchiveReceipt jdkExtraction installedSdkInventory installedSdkMetadata installedSdkConsent installedSdkAcceptance networkId networkLabels meaning'.split())
SDK_RELEASE_FIELDS=('jdkExtraction','installedSdkInventory','installedSdkMetadata','installedSdkConsent','installedSdkAcceptance')


def need(ok,message):
    if not ok:raise ValueError(message)


def load(raw):
    def pairs(items):
        d={}
        for k,v in items:need(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
        return d
    def reject(value):raise ValueError('NO_FLOAT_OR_NONFINITE')
    def integer(value):need(value!='-0','NEGATIVE_ZERO');return int(value)
    return json.loads(raw.decode('utf-8','strict'),object_pairs_hook=pairs,parse_int=integer,parse_float=reject,parse_constant=reject)


def pin_shape(d):
    need(type(d) is dict and set(d)=={'path','bytes','sha256'},'CLOSED_PIN')
    p=Path(d['path']);need(p.is_absolute() and str(p)==d['path'] and '..' not in p.parts,'CANONICAL_PIN_PATH')
    need(type(d['bytes']) is int and 0<=d['bytes']<=2147483648 and re.fullmatch('[0-9a-f]{64}',d['sha256']),'PIN_DOMAIN')
    return p


def checked(d,keep=False):
    p=pin_shape(d);need(not keep or d['bytes']<=4194304,'TEMPLATE_SIZE_BOUND');chunks=[]
    for q in (p,*p.parents):need(not q.is_symlink(),'SYMLINK_PIN')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size==d['bytes'],'REGULAR_EXACT_PIN')
        h=hashlib.sha256();count=0
        while b:=f.read(1048576):
            count+=len(b);need(count<=d['bytes'],'PIN_SIZE_BOUND');h.update(b)
            if keep:chunks.append(b)
        after=os.fstat(f.fileno())
    fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    need(tuple(getattr(before,k) for k in fields)==tuple(getattr(after,k) for k in fields) and h.hexdigest()==d['sha256'],'PIN_DRIFT')
    return b''.join(chunks) if keep else None


def pins(value):
    if type(value) is dict:
        if set(value)=={'path','bytes','sha256'}:yield value
        else:
            for v in value.values():yield from pins(v)
    elif type(value) is list:
        for v in value:yield from pins(v)


def sdk_release_shape(release):
    need('extractions' not in release and all(key in release for key in SDK_RELEASE_FIELDS),'INSTALLED_SDK_RELEASE_MEMBERSHIP')
    for key in SDK_RELEASE_FIELDS:pin_shape(release[key])
    need(release['installedSdkAcceptance'] in release['prerequisiteAcceptances'],'WHOLE_SDK_DATA_ACCEPTANCE_MANDATORY')
    need(len({release[key]['path'] for key in SDK_RELEASE_FIELDS})==len(SDK_RELEASE_FIELDS),'DISTINCT_JDK_SDK_EVIDENCE_SUBJECTS')


def validate(t):
    need(type(t) is dict and set(t)=={'schema','actor','decision','expectedOutput','release','metadata'},'FIXED_TEMPLATE_KEYS')
    need(t['schema']=='nbdp-amethyst-one-build-dispatch-template-v1' and t['actor']=='/root'
        and t['decision']=='AUTHORIZE_ONE_FIXED_AMETHYST_BUILD_DISPATCH','ACTUAL_ROOT_AUTHORIZED_TEMPLATE_REQUIRED')
    r=t['release'];need(type(r) is dict and set(r)==RELEASE_KEYS,'EXACT_RELEASE_KEYS')
    need(r['schema']=='nbdp-amethyst-build-only-root-release-v1' and r['actor']=='/root'
        and r['executionAuthorized'] is True and r['scope']=='FIXED_AMETHYST_BUILD_ONLY','FIXED_BUILD_AUTHORITY')
    need(type(r['runId']) is str and re.fullmatch('[0-9a-f]{32}',r['runId']),'PREDETERMINED_RUNID')
    need(t['expectedOutput']==str(WORK/('attempt-'+r['runId'])),'FIXED_SUPERVISOR_OUTPUT')
    need(r['supervisorSubject']==PINNED[2] and all(r[k] is None for k in CLOCKS),'FIXED_TARGET_NULL_CLOCK_SLOTS')
    def concrete(v):return v is not None and (all(concrete(x) for x in v.values()) if type(v) is dict else all(concrete(x) for x in v) if type(v) is list else True)
    need(concrete({k:v for k,v in r.items() if k not in CLOCKS}) and concrete(t['metadata']),'CONCRETE_PREREQUISITES_REQUIRED')
    need(type(r['sourceReviews']) is list and len(r['sourceReviews'])==2 and type(r['prerequisiteAcceptances']) is list
        and len(r['prerequisiteAcceptances'])>=3 and type(t['metadata']) is list and len(t['metadata'])>=3,'REAL_REVIEW_DATA_PINS_REQUIRED')
    need(re.fullmatch('[0-9a-f]{64}',r['networkId']),'FIXED_NETWORK_ID')
    sdk_release_shape(r)
    for d in [r[k] for k in ('supervisorSubject','buildPreparationSubject','sourceArchive','sourceArchiveReceipt')]+r['sourceReviews']+r['prerequisiteAcceptances']+[r[k] for k in ('jdkExtraction','installedSdkInventory','installedSdkMetadata','installedSdkConsent','installedSdkAcceptance')]+t['metadata']:pin_shape(d)
    return r


def fresh(r,now):
    need(type(now) is int and 0<now<=9223372036854775807-2400*10**9,'EXACT_NS_CLOCK')
    live=dict(r,issuedAtUtcNs=now,notAfterUtcNs=now+2400*10**9)
    need({k:v for k,v in live.items() if k not in CLOCKS}=={k:v for k,v in r.items() if k not in CLOCKS},'PAYLOAD_CHANGED')
    return live


def write_once(path,raw,opener=os.open):
    fd=opener(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:need(f.write(raw)==len(raw),'SHORT_ONCE_WRITE');f.flush();os.fsync(f.fileno())


def main():
    need(PINNED is not None,'INSTALLED_SDK_SOURCE_DATA_BINDING_NOT_READY')
    os.umask(0o077);p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template-sha',required=True);a=p.parse_args()
    need(str(Path(sys.executable).resolve())==PYTHON and sys.flags.isolated and sys.dont_write_bytecode,'FIXED_ISOLATED_INTERPRETER')
    path=HERE/'root-authorized-template.json';need(path.stat().st_size<=4194304,'TEMPLATE_SIZE_BOUND')
    d=dict(path=str(path),bytes=path.stat().st_size,sha256=a.template_sha);t=load(checked(d,keep=True));r=validate(t)
    for q in [*PINNED,*pins(r),*t['metadata']]:checked(q)
    need(not Path(t['expectedOutput']).exists() and not Path(t['expectedOutput']).is_symlink()
        and not (HERE/'live-release.json').exists(),'FRESH_JOB_AND_GRANT_REQUIRED')
    write_once(HERE/'dispatch-marker.json',json.dumps(dict(template=d,runId=r['runId'],state='CONSUMED_ONCE_BEFORE_DISPATCH')).encode())
    live=fresh(r,time.time_ns());raw=(json.dumps(live,indent=2)+'\n').encode();write_once(HERE/'live-release.json',raw)
    fd=os.open(HERE,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
    sha=hashlib.sha256(raw).hexdigest()
    os.execve(PYTHON,[PYTHON,'-I','-B',str(SOURCE/'supervise_build.py'),'--release',str(HERE/'live-release.json'),'--release-sha',sha],
        {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'})


if __name__=='__main__':main()
