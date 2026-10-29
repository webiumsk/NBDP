"""Root post-build read-only reconciliation using exact frozen definitions."""
import hashlib,importlib.util,json,os,pathlib,resource,stat,time
os.umask(0o077);resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,67108864))
HERE=pathlib.Path(__file__).resolve().parent;OUT=HERE/'post-checks-r1';OUT.mkdir(mode=0o700)
BASE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r7')
ROOT=pathlib.Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-r7')
def put(n,d):
    b=(json.dumps(d,indent=2)+'\n').encode();assert len(b)<=67108864
    with (OUT/n).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return dict(path=str(OUT/n),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load_defs(path,name,expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
start=time.monotonic()
guard=load_defs(BASE/'supervisor-source/supervise_build.py','frozen_supervisor','79dee6482e31a97040013f7ffa8f260f5dc5055c64cfbc17ad1ed4268b54d587')
inside=load_defs(BASE/'preparation/build_inside.py','frozen_inside','2b7d6b95197185c681c1226054542a4412af4bbbda97a15ffbd1b50db30fe5a2')
inside.SOURCE=ROOT/'user/work/source'
try:
    before=json.loads((ROOT/'output/build/workcopy-before.json').read_text());after=inside.snapshot();after_pin=put('external-workcopy-after.json',after)
    changed=[p for p,v in before.items() if after.get(p)!=v]
    modules={str(pathlib.Path(p).parent) for p in before if pathlib.Path(p).name in ('build.gradle','build.gradle.kts')}
    output_prefixes=tuple(str(pathlib.PurePosixPath(module)/folder)
                          for module in modules for folder in ('build','.gradle','.kotlin','.cxx'))
    def output_allowed(p):
        return any(p==prefix or p.startswith(prefix+'/') for prefix in output_prefixes)
    unplanned=sorted(p for p in after.keys()-before.keys() if not output_allowed(p))
    equality=put('external-source-equality.json',dict(actor='/root',originalFilesUnchanged=not changed,changedOriginalFiles=changed,unplannedNewFiles=unplanned,beforeRows=len(before),afterRows=len(after),afterInventory=after_pin,scope='Separate root post-build read-only observation using frozen snapshot/output-classification; independent acceptance stillrequired'))
    template=json.loads((HERE/'review-template.json').read_text())['release']
    sdk=guard.doc(template['installedSdkInventory']);guard.tool_inventory(sdk)
    for row in sdk['symlinkModes']:
        p=pathlib.Path(sdk['destination'])/row['path'];assert stat.S_ISLNK(p.lstat().st_mode) and oct(stat.S_IMODE(p.lstat().st_mode))==row['mode']
    sdk_root=pathlib.Path(sdk['destination']);assert sdk_root.stat().st_uid==1000
    for row in sdk['inventory']:assert (sdk_root/row['path']).lstat().st_uid==1000
    guard.tool_inventory(guard.doc(template['jdkExtraction']))
    assert guard.pin(pathlib.Path(template['sourceArchive']['path']))==template['sourceArchive']
    assert guard.pin(pathlib.Path(template['sourceArchiveReceipt']['path']))==template['sourceArchiveReceipt']
    for key in ('installedSdkInventory','installedSdkMetadata','installedSdkConsent','installedSdkAcceptance'):guard.checked(template[key])
    key_root=ROOT/'user'
    assert not key_root.is_symlink() and key_root.resolve(strict=True)==key_root
    keys=[];scanned=0
    for p in key_root.rglob('*'):
        scanned+=1;assert scanned<=200000,'KEY_SCAN_MEMBER_BOUND'
        if p.suffix not in ('.keystore','.jks'):continue
        assert len(keys)<16,'KEY_COUNT_BOUND'
        initial=p.lstat()
        assert stat.S_ISREG(initial.st_mode) and initial.st_uid==1000 and stat.S_IMODE(initial.st_mode)==0o600,'KEY_PRIVATE_REGULAR_ONLY'
        assert p.resolve(strict=True).is_relative_to(key_root),'KEY_CONTAINMENT'
        for ancestor in (p,*p.parents):
            assert not ancestor.is_symlink(),'KEY_SYMLINK_REFUSED'
            if ancestor==key_root:break
        assert 0<initial.st_size<=1048576,'KEY_SIZE_BOUND'
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as stream:
            before_key=os.fstat(stream.fileno());count=0;digest=hashlib.sha256()
            assert (before_key.st_dev,before_key.st_ino,before_key.st_size,before_key.st_mtime_ns,before_key.st_ctime_ns)==(initial.st_dev,initial.st_ino,initial.st_size,initial.st_mtime_ns,initial.st_ctime_ns),'KEY_OPEN_DRIFT'
            while block:=stream.read(65536):
                count+=len(block);assert count<=1048576,'KEY_STREAM_BOUND';digest.update(block)
            after_key=os.fstat(stream.fileno())
        assert count==initial.st_size and (after_key.st_dev,after_key.st_ino,after_key.st_size,after_key.st_mtime_ns,after_key.st_ctime_ns)==(initial.st_dev,initial.st_ino,initial.st_size,initial.st_mtime_ns,initial.st_ctime_ns),'KEY_READ_DRIFT'
        keys.append(dict(relativePath=str(p.relative_to(key_root)),bytes=count,sha256=digest.hexdigest(),mode=oct(stat.S_IMODE(initial.st_mode))))
    keys.sort(key=lambda value:value['relativePath'])
    result=dict(actor='/root',state='POST_BUILD_DATA_CAPTURED_PENDING_INDEPENDENT_REVIEW',sourceEquality=equality,sdkCompleteInventoryBytesModesLinksAndUidsUnchanged=True,sdkMembers=len(sdk['inventory']),jdkCompleteInventoryUnchanged=True,sourceArchiveAndReceiptUnchanged=True,acceptedSdkEvidenceUnchanged=True,privateDebugKeyDescriptors=keys,privateKeysCopied=False,elapsedSeconds=time.monotonic()-start,qualification='Pure root read-only source/input reconciliation; actual artifact and terminal lifecycle reviewed separately')
    put('result.json',result);print(json.dumps(result))
except BaseException as error:
    put('FAILED.json',dict(error=type(error).__name__+':'+str(error)[:2048],elapsedSeconds=time.monotonic()-start,qualification='Postcheckincomplete/noqualification/noretry'));raise
