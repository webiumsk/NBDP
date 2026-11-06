"""Read/hash/inspect current inputs only. No role grant, SDK tool or VM start."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, stat, subprocess, sys, time

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE = ROOT / 'docs/decisions/evidence'
HERE = Path(__file__).resolve().parent
PRODUCER = Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
SOURCE = EVIDENCE / 'e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2/subject.json'
CONFIG = SOURCE.parent.parent / 'incoming-run-config.json'
FROZEN = EVIDENCE / 'e02-producer3-current-controls-preparation-20261028/source4/capture-a/frozen-inputs.json'
OUT = HERE / 'input-preflight-r1'

def pin(path):
    path = Path(path)
    assert path.is_absolute() and path.resolve(strict=True) == path
    assert all(not item.is_symlink() for item in (path, *path.parents))
    first = path.lstat()
    assert stat.S_ISREG(first.st_mode) and first.st_size <= 2147483648
    identity = lambda s: (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    digest = hashlib.sha256(); count = 0
    with os.fdopen(os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK), 'rb') as stream:
        assert identity(os.fstat(stream.fileno())) == identity(first)
        while block := stream.read(1048576):
            count += len(block); assert count <= 2147483648; digest.update(block)
        assert identity(os.fstat(stream.fileno())) == identity(first)
    assert identity(path.lstat()) == identity(first) and count == first.st_size
    return dict(path=str(path), bytes=count, sha256=digest.hexdigest())

def checked(expected):
    assert set(expected) == {'path','bytes','sha256'} and pin(expected['path']) == expected
    return Path(expected['path'])

def save(name, value):
    with (OUT/name).open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')

def main():
    assert sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 1
    os.umask(0o077); started = time.time_ns()
    assert pin(SOURCE)['sha256'] == '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'
    assert pin(CONFIG)['sha256'] == 'cec7ee4aa2701eb8430434345454526bbcdfd35d2fe500e8b766db52939f3023'
    subject = json.loads(SOURCE.read_bytes()); config = json.loads(CONFIG.read_bytes())
    assert config['ordinaryRole'] == 'incoming' and config['runId'] == '9d8bad6df86fc113f87e14e2974f9019'
    assert config['originalLeaseSeconds'] == 1800
    for row in subject['sources']: checked(row)
    before = [pin(row['path']) for row in subject['sources']]
    controller = next(row for row in subject['sources'] if row['path'] == str(PRODUCER/'supervisor.py'))
    checked(controller)
    spec = importlib.util.spec_from_file_location('reviewed_current_producer_preflight', controller['path'])
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.verify_config(config)  # Reviewed read/hash validation, no execute/guest/materialize call.
    assert pin(FROZEN)['sha256'] == 'f9faea2fbae382dbd3bc7d9c9d6d77bd1b47988920b38afce28991f59784ecff'
    trees = []
    for tree in json.loads(FROZEN.read_bytes())['fullReadTrees']:
        base = Path(tree['root']); actual_files = []; directories = []
        for path in sorted(base.rglob('*')):
            assert not path.is_symlink()
            if path.is_dir(): directories.append(str(path.relative_to(base))); continue
            row = pin(path); actual_files.append(dict(row,relativePath=str(path.relative_to(base)),mode=stat.S_IMODE(path.stat().st_mode)))
        assert actual_files == tree['files'] and len(actual_files) == tree['count']
        trees.append(dict(root=str(base),regularFiles=len(actual_files),directories=directories,exactFileModeMembership=True))
    OUT.mkdir(mode=0o700,exist_ok=False)
    docker_config = OUT/'private-docker-config'; docker_config.mkdir(mode=0o700)
    (docker_config/'config.json').write_text('{}\n')
    env = dict(PATH='/usr/bin:/bin',LANG='C.UTF-8',LC_ALL='C.UTF-8',DOCKER_CONFIG=str(docker_config))
    images = []
    for image in (config['runtimeImage'],config['relayImage']):
        argv = ['/usr/bin/docker','--host','unix:///var/run/docker.sock','image','inspect','--format','{{.Id}}',image]
        result = subprocess.run(argv,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        assert len(result.stdout) <= 1048576 and len(result.stderr) <= 262144
        images.append(dict(argv=argv,exitCode=result.returncode,stdout=result.stdout.decode('utf-8'),stderr=result.stderr.decode('utf-8')))
        assert result.returncode == 0 and result.stdout.decode().strip() == image and result.stderr == b''
    assert [pin(row['path']) for row in subject['sources']] == before
    lab = Path('/Data/nbdp-e02-tooling-20261027/ordinary-minimum-r3')
    target = lab/'runs'/config['runId']; assert not os.path.lexists(target)
    fd = os.open('/dev/kvm',os.O_RDWR|os.O_CLOEXEC)
    try: assert stat.S_ISCHR(os.fstat(fd).st_mode)
    finally: os.close(fd)
    mem = next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
    free = shutil.disk_usage(lab).free; cpus = sorted(os.sched_getaffinity(0))
    value = dict(schema='nbdp-minimum-current-input-verification-v1',actor='/root',context='SUPPORTED_HOST',role='incoming',startedUtcNs=started,finishedUtcNs=time.time_ns(),sourceSubject=pin(SOURCE),configuration=pin(CONFIG),sdkIndex=pin(Path(config['sdkInventory']['path'])),sdkRegularFiles=434,sdkHashModeMembershipMatched=True,guardRegularFiles=522,guardHashModeMembershipMatched=True,trees=trees,apk=config['amethystApk'],helper=config['helperApk'],images=images,kvmReadWriteOpened=True,kvmVmCreated=False,actualOutput=str(target),measuredFilesystemAncestor=str(lab),filesystemDevice=lab.stat().st_dev,availableDiskBytes=free,memAvailableBytes=mem,affinityCpus=cpus,resourceRequirementsMet=free>=8589934592 and mem>=12884901888 and len(cpus)>=8,roleGrantIssued=False,limits=['Actual read/hash/inspect/open-existing-device admission only; no SDK/native validator command, new container, Android, relay, role, VM or experiment.','Original source31/worker16/Node816+65dirs+2links/canonical19+E02/provenance assertions verified by unchanged reviewed producer.','Fresh resource measurement still required immediately before any separately approved role grant.'])
    save('verification.json',value); save('source-before.json',before)
    (OUT/'verification.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(verification=pin(OUT/'verification.json'),resourceRequirementsMet=value['resourceRequirementsMet'],noGrantOrRuntime=True)))

if __name__ == '__main__': main()
