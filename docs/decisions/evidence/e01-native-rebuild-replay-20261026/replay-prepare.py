"""Copy and describe E01 inputs only. Never execute project code or native tools."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

HERE = Path(__file__).resolve().parent
SOURCE = Path('/home/peterhorvath/apps/bitcoin/NBDP/experiments')
LAB = HERE / 'lab'
NATIVE = Path('/tmp/nbdp-rust-rebuild-20261026/target/debug/nbdp-experiment-rust')

def pin(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Canonical regular file required: ' + str(path))
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1048576), b''):
            digest.update(chunk)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('Input changed during hashing')
    return {'path':str(path), 'bytes':after.st_size, 'sha256':digest.hexdigest()}

def tree(root):
    rows = []
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root).as_posix()
        mode = oct(stat.S_IMODE(path.lstat().st_mode))
        if path.is_symlink():
            target = path.resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError('Symlink escapes copied closure: ' + str(path))
            rows.append({'path':rel, 'type':'symlink', 'mode':mode, 'link':str(path.readlink()), 'target':target.relative_to(root).as_posix()})
        elif path.is_dir():
            rows.append({'path':rel, 'type':'directory', 'mode':mode})
        elif path.is_file():
            value = pin(path)
            rows.append({'path':rel, 'type':'file', 'mode':mode, 'bytes':value['bytes'], 'sha256':value['sha256']})
        else:
            raise ValueError('Special input file')
    return rows

def save(name, value):
    path = HERE / name
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    return pin(path)

def main():
    if LAB.exists():
        raise ValueError('Fresh lab required; never replace a prior preparation')
    LAB.mkdir(mode=0o700)
    experiments = LAB / 'experiments'
    experiments.mkdir(mode=0o700)
    status, missing = 'SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_RELEASE', []
    copied = []
    for name in ('shared', 'e01-envelope', 'node_modules'):
        src, dst = SOURCE / name, experiments / name
        if not src.is_dir():
            missing.append(str(src)); continue
        before = tree(src)
        shutil.copytree(src, dst, symlinks=True)
        after, actual = tree(src), tree(dst)
        if before != after or before != actual:
            raise ValueError('Copied tree mismatch: ' + name)
        copied.append({'sourceRoot':str(src), 'destinationRoot':str(dst), 'members':len(actual), 'exactByteModeMembershipAndSymlinkCopy':True})
    for name in ('package.json', 'package-lock.json', 'fixtures/nip44.vectors.json', 'fixtures/README.md', 'fixtures/research-input-manifest.json', 'docker/strfry.conf', 'docker/rs-relay.toml'):
        src, dst = SOURCE / name, experiments / name
        if not src.is_file():
            missing.append(str(src)); continue
        before = pin(src)
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(src, dst)
        after, actual = pin(src), pin(dst)
        if before != after or any(before[k] != actual[k] for k in ('bytes','sha256')):
            raise ValueError('Copied file mismatch: ' + name)
    historical = SOURCE / 'results/E01.json'
    historical_pin = pin(historical)
    old = json.loads(historical.read_bytes())
    comparisons = []
    for rel, expected in old['source_sha256'].items():
        actual = pin(experiments / rel)
        comparisons.append({'relativePath':rel, 'historicalSha256':expected, 'copied':actual, 'equal':actual['sha256']==expected})
    if len(comparisons) != 19 or not all(row['equal'] for row in comparisons):
        status = 'NOT_READY'
    if NATIVE.is_file() and not NATIVE.is_symlink():
        native_before = pin(NATIVE)
        (LAB / 'native').mkdir(mode=0o700)
        native = LAB / 'native/nbdp-experiment-rust'
        shutil.copy2(NATIVE, native)
        native_after, native_pin = pin(NATIVE), pin(native)
        if native_before != native_after or any(native_before[k] != native_pin[k] for k in ('bytes','sha256')):
            raise ValueError('Native build changed during snapshot')
    else:
        native_pin = None
        missing.append(str(NATIVE))
    tools = {}
    for name, path in {'node':'/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node', 'timeout':'/usr/bin/timeout', 'chromeProbeDisabled':'/usr/bin/false', 'python':'/usr/bin/python3.12'}.items():
        try:
            tools[name] = pin(path)
        except (OSError, ValueError):
            missing.append(path)
    for name in ('results', 'fixtures/generated'):
        (experiments / name).mkdir(mode=0o700)
    for name in ('home', 'tmp'):
        (LAB / name).mkdir(mode=0o700)
    inventory = save('input-inventory.json', {'schema':'nbdp-e01-replay-copy-inventory-v1', 'root':str(LAB), 'rows':tree(LAB), 'copiedTrees':copied})
    comparison = save('historical-comparison.json', {'historicalReport':historical_pin, 'historicalStatus':old['status'], 'historicalCount':len(old['tests']), 'historicalSkips':old['skipped'], 'sourceCount':len(comparisons), 'comparisons':comparisons, 'allEqual':all(row['equal'] for row in comparisons), 'historicalRustSha256':old['environment']['rust_binary_sha256'], 'newRustSha256':native_pin['sha256'] if native_pin else None, 'newNativeRuntimeNotExecuted':True})
    if missing:
        status = 'NOT_READY'
    argv = [tools['timeout']['path'], '--signal=TERM', '--kill-after=2s', '240s', tools['node']['path'], 'shared/run.mjs', 'E01'] if all(k in tools for k in ('timeout','node')) else None
    environment = {'PATH':'/usr/bin:/bin','HOME':str(LAB/'home'),'TMPDIR':str(LAB/'tmp'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','NBDP_CHROME':'/usr/bin/false', 'NBDP_RUST_BIN':native_pin['path'] if native_pin else 'MISSING'}
    plan = save('plan.json', {'schema':'nbdp-e01-isolated-replay-source-plan-v1', 'state':status, 'scope':'SOURCE_AND_DATA_PREPARATION_ONLY_NO_TEST_OR_NATIVE_EXECUTION', 'lab':str(LAB), 'cwd':str(experiments), 'inputInventory':inventory, 'historicalComparison':comparison, 'launcher':pin(HERE/'launch.py'), 'preparationSource':pin(Path(__file__).resolve()), 'tools':tools, 'native':native_pin, 'nativeSourceDeclaration':{'operation':'source', 'expectedReplyValueEqualsExactFile':pin(experiments/'shared/rust/src/main.rs'), 'implementation':'include_str!("main.rs")', 'sourceReplyObserved':False, 'buildAcceptanceRequired':True}, 'maximumTestSeconds':240, 'terminationGraceSeconds':2, 'argv':argv, 'environment':environment, 'missing':missing, 'outcomeRequired':{'status':'PASS','tests':140,'failures':0,'mandatorySkips':0,'nativeSha256':native_pin['sha256'] if native_pin else None,'all19HistoricalSourcePinsEqual':True}, 'isolation':{'workingCopyOnly':True, 'originalCanonicalRunnerAndTestBytesUnchanged':True, 'writes':'Only fresh lab results/, fixtures/generated/, home/ and tmp/', 'noNetworkCallsInE01Scope':True,'kernelNetworkIsolationEstablished':False,'noRelaysAndroidServicesOrBrowser':True,'chromeMetadata':'Original version probe intentionally receives /usr/bin/false; result is unavailable, no browser launched.'}, 'runtimeEvidenceLimitations':['GNU timeout is an external wall bound, not portable descendant-lifecycle attestation.','Root must preserve actual foreground tool responses and inspect final outcome/cleanup; no lifecycle facts are fabricated by this launcher.','New native build acceptance, independent exact SOURCE QA/security and fresh externally pinned root release are mandatory before launch.','No current E01 PASS, SDK permission or canonical record replacement follows from preparation.']})
    print(json.dumps({'state':status,'plan':plan,'inventory':inventory,'historicalComparison':comparison,'missing':missing}))

if __name__ == '__main__':
    main()
