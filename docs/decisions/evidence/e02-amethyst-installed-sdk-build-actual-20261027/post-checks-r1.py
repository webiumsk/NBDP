"""Root post-stop read-only reconciliation using exact frozen definitions."""
import hashlib,importlib.util,json,os,pathlib,resource,stat,time
os.umask(0o077);resource.setrlimit(resource.RLIMIT_FSIZE,(16777216,16777216))
HERE=pathlib.Path(__file__).resolve().parent;OUT=HERE/'post-checks-r1';OUT.mkdir(mode=0o700)
BASE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r3')
ROOT=pathlib.Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-r3')
def put(n,d):
    b=(json.dumps(d,indent=2)+'\n').encode();assert len(b)<=16777216
    with (OUT/n).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return dict(path=str(OUT/n),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load_defs(path,name,expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
start=time.monotonic()
guard=load_defs(BASE/'supervisor-source/supervise_build.py','frozen_supervisor','41d8951bae82784fcd90716bdbcbc84956072186eb3e1bd9ff280d437768572c')
inside=load_defs(BASE/'preparation/build_inside.py','frozen_inside','2ecf91a0f9959931075d4b8ac3e4f7e2337054fbcb9b9b58f53707cd1375d405')
inside.SOURCE=ROOT/'user/work/source'
try:
    before=json.loads((ROOT/'output/build/workcopy-before.json').read_text());after=inside.snapshot();after_pin=put('operator-workcopy-after.json',after)
    changed=[p for p,v in before.items() if after.get(p)!=v]
    modules={str(pathlib.Path(p).parent) for p in before if pathlib.Path(p).name in ('build.gradle','build.gradle.kts')}
    def output_allowed(p):
        return any(p==str(pathlib.PurePosixPath(module)/folder) or p.startswith(str(pathlib.PurePosixPath(module)/folder)+'/')
                   for module in modules for folder in ('build','.gradle','.kotlin','.cxx'))
    unplanned=sorted(p for p in after.keys()-before.keys() if not output_allowed(p))
    equality=put('operator-source-equality.json',dict(actor='/root',originalFilesUnchanged=not changed,changedOriginalFiles=changed,unplannedNewFiles=unplanned,beforeRows=len(before),afterRows=len(after),afterInventory=after_pin,scope='Post-stop root observation using frozen snapshot/output-classification logic; not an inner natural build result, no artifact qualification'))
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
    keys=[dict(relativePath=str(p.relative_to(ROOT/'user')),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mode=oct(p.stat().st_mode&0o777)) for p in sorted(ROOT.joinpath('user').rglob('*')) if p.is_file() and p.suffix in ('.keystore','.jks')]
    result=dict(actor='/root',state='POST_STOP_DATA_CAPTURED_PENDING_INDEPENDENT_REVIEW',sourceEquality=equality,sdkCompleteInventoryBytesModesLinksAndUidsUnchanged=True,sdkMembers=len(sdk['inventory']),jdkCompleteInventoryUnchanged=True,sourceArchiveAndReceiptUnchanged=True,acceptedSdkEvidenceUnchanged=True,privateDebugKeyDescriptors=keys,privateKeysCopied=False,elapsedSeconds=time.monotonic()-start,qualification='Failed/unqualified operator-stopped attempt, no rebuiltAPKs exported; pure read-only input/source reconciliation only')
    put('result.json',result);print(json.dumps(result))
except BaseException as error:
    put('FAILED.json',dict(error=type(error).__name__+':'+str(error)[:2048],elapsedSeconds=time.monotonic()-start,qualification='Postcheckincomplete/noqualification/noretry'));raise
