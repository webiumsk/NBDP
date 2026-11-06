"""SOURCE-only explicit host input custody. No traversal by descriptor shape/suffix."""
import hashlib,json,os,re,stat,time
from pathlib import Path
RAW_LIMIT=2147483648
PARSED_LIMIT=16777216
FILE_LIMIT=20000
TREE_ROOTS=[('/tmp/nbdp-e02-api35-fixture-r2/sdk',434),('/tmp/nbdp-e02-minimal-rs-v7/guard-python',522)]
DEP_ROOT='/home/peterhorvath/apps/bitcoin/NBDP/experiments/node_modules'
def need(v,m):
    if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_METADATA_KEYS')
def safe(p):
    original=str(p);p=Path(p);need(p.is_absolute() and str(p)==original==os.path.normpath(original),'CANONICAL_HOST_PATH');original.encode('utf8','strict')
    for q in [p,*p.parents]:need(not stat.S_ISLNK(q.lstat().st_mode),'NO_HOST_SYMLINK')
    return p
def identity(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def pin_shape(d):
    closed(d,'path bytes sha256');need(type(d['bytes']) is int and 0<=d['bytes']<=RAW_LIMIT and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'BOUNDED_EXACT_RAW_DESCRIPTOR');return safe(d['path'])
def read_expected(d,deadline_ns,metadata=False,expected_mode=None):
    p=pin_shape(d);need(not metadata or d['bytes']<=PARSED_LIMIT,'METADATA_LIMIT_BEFORE_ALLOCATION');first=p.lstat();need(stat.S_ISREG(first.st_mode) and first.st_size==d['bytes'],'EXPECTED_REGULAR_SIZE')
    if expected_mode is not None:need(stat.S_IMODE(first.st_mode)==expected_mode,'EXPECTED_MODE')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);digest=hashlib.sha256();n=0;body=bytearray() if metadata else None
    try:
        need(identity(os.fstat(fd))==identity(first),'OPEN_IDENTITY_DRIFT')
        while True:
            need(time.monotonic_ns()<deadline_ns,'INPUT_CUSTODY_DEADLINE');b=os.read(fd,1048576)
            if not b:break
            n+=len(b);need(n<=d['bytes'] and n<=RAW_LIMIT,'RAW_READ_BOUND');digest.update(b)
            if metadata:body.extend(b)
        need(identity(os.fstat(fd))==identity(first),'HANDLE_IDENTITY_DRIFT')
    finally:os.close(fd)
    need(identity(p.lstat())==identity(first) and n==d['bytes'] and digest.hexdigest()==d['sha256'],'EXACT_EXPECTED_PIN_NOT_OBSERVED_BASELINE');safe(p)
    row=dict(pin=d,mode=stat.S_IMODE(first.st_mode),uid=first.st_uid,gid=first.st_gid,device=str(first.st_dev),inode=str(first.st_ino),mtimeNs=str(first.st_mtime_ns),ctimeNs=str(first.st_ctime_ns))
    return row,bytes(body) if metadata else None
def decode_metadata(raw):
    need(type(raw) is bytes and len(raw)<=PARSED_LIMIT,'PARSED_METADATA_BOUND')
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_METADATA_KEY');out[k]=v
        return out
    def reject(_):raise ValueError('NONINTEGER_OR_NONFINITE_METADATA')
    value=json.loads(raw.decode('utf8','strict'),object_pairs_hook=pairs,parse_float=reject,parse_constant=reject)
    count=0
    def walk(v,depth):
        nonlocal count
        count+=1;need(depth<=64 and count<=250000,'METADATA_STRUCTURE_BOUND')
        if type(v) is dict:
            for x in v.values():walk(x,depth+1)
        elif type(v) is list:
            for x in v:walk(x,depth+1)
    walk(value,0);return value
def metadata(d,deadline_ns):return decode_metadata(read_expected(d,deadline_ns,True)[1])
def snapshot_files(manifest,deadline_ns):
    need(type(manifest['files']) is list and 1<=len(manifest['files'])<=FILE_LIMIT,'FINITE_EXPLICIT_INPUT_SET');rows=[];seen=set()
    for item in manifest['files']:
        closed(item,'pin mode role origin');d=item['pin'];need(d['path'] not in seen,'UNIQUE_HOST_INPUT');seen.add(d['path']);need(type(item['mode']) is int and 0<=item['mode']<=4095,'EXPECTED_FROZEN_MODE')
        need(item['role'] in ('SOURCE','TOOL','SDK_FILE','GUARD_FILE','NODE_DEP_FILE','CANONICAL','NATIVE','ARTIFACT','OPAQUE_PREREQUISITE','BASELINE_READ','METADATA_AUTHORITY'),'CODE_DEFINED_INPUT_ROLE')
        # Role never exempts a HOST file from uniform streaming. Only explicit
        # metadata() calls parse named <=16MiB authority files.
        rows.append(read_expected(d,deadline_ns,False,item['mode'])[0])
    return rows
def tree_members(root,deadline_ns,allow_dependency_links=False):
    root=safe(root);need(root.is_dir(),'TREE_DIRECTORY');result=dict(files=[],directories=[],symlinks=[]);visits=0
    for base,dirs,files in os.walk(root,followlinks=False):
        for name in sorted(dirs+files):
            visits+=1;need(visits<=40000 and time.monotonic_ns()<deadline_ns,'TREE_VISIT_OR_TIME_BOUND');p=Path(base)/name;s=p.lstat();rel=p.relative_to(root).as_posix()
            if stat.S_ISLNK(s.st_mode):
                need(allow_dependency_links,'NO_SDK_GUARD_LINK');target=p.resolve(strict=True);need(target.is_relative_to(root) and target!=root and target.is_file(),'EXPLICIT_SAFE_DEPENDENCY_LINK');result['symlinks'].append(dict(path=rel,link=str(p.readlink()),target=target.relative_to(root).as_posix()))
            elif stat.S_ISDIR(s.st_mode):result['directories'].append(dict(path=rel,mode=stat.S_IMODE(s.st_mode)))
            elif stat.S_ISREG(s.st_mode):result['files'].append(dict(path=rel,mode=stat.S_IMODE(s.st_mode)))
            else:raise ValueError('UNPLANNED_TREE_SPECIAL_FILE')
    for rows in result.values():rows.sort(key=lambda r:r['path'])
    return result
def snapshot_memberships(manifest,deadline_ns):
    need(len(manifest['fullTrees'])==2,'SDK_AND_GUARD_REQUIRED');out=[];indexed={x['pin']['path']:x for x in manifest['files']}
    for spec,(root,count) in zip(manifest['fullTrees'],TREE_ROOTS):
        closed(spec,'root regularFiles membership');need(spec['root']==root and spec['regularFiles']==count,'EXACT_DECLARED_SDK_GUARD_TREE');actual=tree_members(root,deadline_ns);need(actual==spec['membership'] and len(actual['files'])==count,'FULL_TREE_MEMBER_MODE_MATCH')
        role='SDK_FILE' if count==434 else 'GUARD_FILE';required={root+'/'+r['path'] for r in actual['files']};need(required=={p for p,x in indexed.items() if x['role']==role},'ALL_TREE_BYTES_IN_STREAMED_FILE_SET')
        for r in actual['files']:need(indexed[root+'/'+r['path']]['mode']==r['mode'],'TREE_MODE_TO_EXPECTED_FILE_JOIN')
        out.append(dict(root=root,membership=actual))
    dep=manifest['nodeDependencies'];closed(dep,'root membership');need(dep['root']==DEP_ROOT,'EXACT_NODE_DEPENDENCY_ROOT');actual=tree_members(DEP_ROOT,deadline_ns,True);need(actual==dep['membership'] and [len(actual[k]) for k in ('files','directories','symlinks')]==[816,65,2],'EXACT_NODE816_DIR65_SAFE_LINK2')
    need({DEP_ROOT+'/'+r['path'] for r in actual['files']}=={p for p,x in indexed.items() if x['role']=='NODE_DEP_FILE'},'ALL816_DEPENDENCY_BYTES_IN_STREAMED_FILE_SET');out.append(dict(root=DEP_ROOT,membership=actual));return out
