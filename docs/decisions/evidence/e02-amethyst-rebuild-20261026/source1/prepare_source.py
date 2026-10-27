"""Proposed future source-archive step; no checkout/global configuration writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/tmp/nbdp-amethyst-rebuild-20261026')
COMMIT = 'e6f464a1179def75274512b3c5bab921de3bf3d8'
TREE = '11a90777c85c71912594612f42d9807004834f67'
ENV = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
       'GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'1'}


def git(*args):
    return subprocess.run(['/usr/bin/git','-C',str(ROOT/'source'),*args],env=ENV,
        input=b'',capture_output=True,timeout=60,check=True).stdout


def main():
    before = dict(commit=git('rev-parse','HEAD').decode().strip(),tree=git('rev-parse','HEAD^{tree}').decode().strip(),
                  status=git('status','--porcelain=v1','--untracked-files=all').decode())
    if before != dict(commit=COMMIT,tree=TREE,status=''): raise ValueError('EXACT_CLEAN_SOURCE_REQUIRED')
    entries=git('ls-tree','-r','-l','-z',COMMIT).split(b'\0')
    sizes=[]
    for entry in entries:
        if not entry:continue
        fields=entry.split(b'\t',1)[0].split()
        if len(fields)!=4 or fields[0] not in (b'100644',b'100755') or fields[1]!=b'blob':
            raise ValueError('SOURCE_LINK_SUBMODULE_OR_SPECIAL_REQUIRES_REVIEW')
        sizes.append(int(fields[3]))
    if len(sizes)>200000 or sum(sizes)>1073741824:raise ValueError('PINNED_SOURCE_SIZE_ADMISSION')
    path = ROOT / 'output/source.tar'
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        result = subprocess.run(['/usr/bin/git','-C',str(ROOT/'source'),'archive','--format=tar',COMMIT],
            env=ENV,input=b'',stdout=stream,stderr=subprocess.PIPE,timeout=120,check=False)
        stream.flush(); os.fsync(stream.fileno())
    if result.returncode != 0: raise ValueError('SOURCE_ARCHIVE_FAILED:'+result.stderr.decode(errors='replace')[:512])
    after = dict(commit=git('rev-parse','HEAD').decode().strip(),tree=git('rev-parse','HEAD^{tree}').decode().strip(),
                 status=git('status','--porcelain=v1','--untracked-files=all').decode())
    if before != after: raise ValueError('ORIGINAL_CHECKOUT_CHANGED')
    h=hashlib.sha256();count=0
    with path.open('rb') as stream:
        while block:=stream.read(1048576):
            count+=len(block)
            if count>2147483648: raise ValueError('SOURCE_ARCHIVE_BOUND')
            h.update(block)
    record=dict(schema='nbdp-amethyst-source-archive-v1',before=before,after=after,
        archive=dict(path=str(path),bytes=count,sha256=h.hexdigest()),
        meaning='Git archive of exact commit; excludes .git configuration/credentials; no source edits or build execution')
    fd=os.open(ROOT/'output/source-archive.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(record,stream,indent=2);stream.write('\n')


if __name__=='__main__':main()
