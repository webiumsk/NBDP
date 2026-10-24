"""DATA-only exact-copy archive builder; requires a later explicit closed-input freeze.

No project imports, experiments, services, subprocesses or Git operations.
Only this fixed publication directory receives new exclusive regular files.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import stat
import sys
import tarfile

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = ROOT / 'docs/decisions/evidence/transport-runtime-progress-publication-r5'
ROOT_PATHS = ('docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r1', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2', 'docs/decisions/evidence/e02-completion-preparation-r1', 'docs/decisions/evidence/e02-minimum-runtime-preparation-r1', 'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1', 'docs/decisions/evidence/e02-ordinary-minimum-relay-diagnosis-r1', 'docs/decisions/evidence/e02-owned-avd-overlay-reclamation-r7', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r5', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r6', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r7', 'docs/decisions/evidence/e06-strace-containment-controls-r4', 'docs/decisions/evidence/e06-strace-containment-controls-r5', 'docs/decisions/evidence/e06-strace-containment-controls-r6', 'docs/decisions/evidence/e06-strace-transient-source-research-r1', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2', 'experiments/prototypes/e02_completion_v1')

ARCHIVE = HERE / 'completed-runtime-evidence.tar.gz'
SOURCE_INPUTS = {'build_archive.py', 'selection-plan.json', 'README-source.md',
                 'source-preparation-api.json', 'source-preparation-output.txt'}
OUTPUTS = {'selection.json', 'completed-runtime-evidence.tar.gz', 'archive-index.json',
           'archive-verification.json', 'normal-core-suggestion.json'}
FORBIDDEN_SUFFIXES = {'.apk', '.aab', '.zip', '.gz', '.tgz', '.tar', '.xz', '.7z',
    '.img', '.qcow2', '.pem', '.key', '.jks', '.p12', '.keystore', '.so', '.dex',
    '.db', '.sqlite', '.sqlite3'}
MAX_FILE = 100_000_000
MAX_TOTAL = 250_000_000
MAX_FILES = 10000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_relative(value):
    require(isinstance(value, str) and value and '\x00' not in value, 'Bad path string')
    path = Path(value)
    require(not path.is_absolute() and all(x not in {'', '.', '..'} for x in value.split('/')),
            'Unsafe path: ' + value)
    require(path.as_posix() == value and '\\' not in value, 'Noncanonical path: ' + value)
    value.encode('ascii')
    return path


def snapshot(path):
    require(path.is_relative_to(ROOT), 'Outside repository')
    require(path.resolve() == path, 'Symlinked path')
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and 0 <= s.st_size <= MAX_FILE, 'Not bounded regular file')
    return dict(device=s.st_dev, inode=s.st_ino, bytes=s.st_size,
                mode=stat.S_IMODE(s.st_mode), uid=s.st_uid, gid=s.st_gid,
                nlink=s.st_nlink, mtimeNs=s.st_mtime_ns, ctimeNs=s.st_ctime_ns)


def describe(path):
    before = snapshot(path)
    h = hashlib.sha256()
    length = 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as handle:
        s = os.fstat(handle.fileno())
        require((s.st_dev, s.st_ino) == (before['device'], before['inode']), 'Open inode drift')
        while block := handle.read(1024**2):
            length += len(block)
            require(length <= MAX_FILE, 'File grew beyond bound')
            h.update(block)
    require(snapshot(path) == before and length == before['bytes'], 'Source changed while read')
    return dict(path=str(path), bytes=length, sha256=h.hexdigest()), before


def private_output(path):
    require(path.parent == HERE and HERE.resolve() == HERE, 'Output outside owned directory')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    return os.fdopen(fd, 'wb')


def write_json(name, value):
    require(name in OUTPUTS, 'Unassigned output')
    with private_output(HERE / name) as handle:
        handle.write((json.dumps(value, indent=2) + '\n').encode())
        handle.flush()
        os.fsync(handle.fileno())


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def read_object(path):
    descriptor, before = describe(path)
    raw = path.read_bytes()
    require(describe(path) == (descriptor, before), 'Manifest drift')
    value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    require(isinstance(value, dict), 'Expected JSON object')
    return value, descriptor


def verify_freeze():
    require(sys.argv[1:] == ['--build-after-explicit-freeze'], 'SOURCE ONLY: explicit later freeze required')
    require(HERE.is_dir() and HERE.resolve() == HERE, 'Owned directory unavailable')
    expected = SOURCE_INPUTS | {'freeze-authorization.json'}
    require({p.name for p in HERE.iterdir()} == expected, 'Unexpected or existing package outputs')
    plan, plan_pin = read_object(HERE / 'selection-plan.json')
    require(plan.get('roots') == list(ROOT_PATHS), 'Selection plan differs from fixed roots')
    freeze, freeze_pin = read_object(HERE / 'freeze-authorization.json')
    require(set(freeze) == {'schema', 'actor', 'state', 'roots', 'script', 'selectionPlan',
                          'allRootOwnersWritesStopped', 'priorPackagesReadOnly', 'scope', 'transcribedBy', 'provenance'}, 'Freeze schema')
    require(freeze['schema'] == 'nbdp-progress-publication-freeze-transcription-v1' and freeze['actor'] == '/root', 'Freeze actor/schema')
    require(freeze['state'] == 'CLOSED_INPUTS_WRITES_STOPPED' and freeze['allRootOwnersWritesStopped'] is True,
            'Inputs remain active')
    require(freeze['transcribedBy'] == '/root/local_monitor_controls'
            and freeze['provenance']['kind'] == 'ACTUAL_COORDINATOR_MAILBOX_TASK_TRANSCRIPTION'
            and freeze['provenance']['selfAcceptance'] is False, 'Truthful delegated freeze provenance')
    require(freeze['roots'] == list(ROOT_PATHS), 'Freeze roots mismatch')
    require(freeze['script'] == describe(HERE / 'build_archive.py')[0], 'Freeze script pin mismatch')
    require(freeze['selectionPlan'] == plan_pin, 'Freeze selection pin mismatch')
    require(freeze['priorPackagesReadOnly'] is True and freeze['scope'] == 'DATA_ARCHIVE_ONLY', 'Scope mismatch')
    return freeze_pin


def enumerate_roots():
    members = []
    roots = []
    total = 0
    for relative_root in ROOT_PATHS:
        root = ROOT / safe_relative(relative_root)
        require(root.is_dir() and root.resolve() == root and not root.is_symlink(), 'Missing or linked fixed root: ' + str(root))
        count = size = 0
        for path in sorted(root.rglob('*')):
            s = path.lstat()
            require(path.resolve() == path, 'Symlinked member')
            if stat.S_ISDIR(s.st_mode):
                continue
            require(stat.S_ISREG(s.st_mode), 'Special source member')
            require(path.suffix.lower() not in FORBIDDEN_SUFFIXES, 'Forbidden binary/archive/key body: ' + str(path))
            name = path.name.lower()
            require(not (name == 'current-official-license-text.txt' or name in {'license', 'license.txt', 'license.xml', 'licenses'}),
                    'External full license body requires separate disposition')
            relative = path.relative_to(ROOT).as_posix()
            safe_relative(relative)
            descriptor, file_stat = describe(path)
            archive_path = 'repository/' + relative
            # USTAR encoding is checked before creation, without PAX fallback.
            probe = tarfile.TarInfo(archive_path)
            probe.tobuf(format=tarfile.USTAR_FORMAT, encoding='ascii', errors='strict')
            members.append(dict(archivePath=archive_path, original=descriptor, originalStat=file_stat))
            count += 1
            size += descriptor['bytes']
            total += descriptor['bytes']
            require(len(members) <= MAX_FILES and total <= MAX_TOTAL, 'Package bound exceeded')
        require(count > 0, 'Empty fixed root')
        roots.append(dict(path=str(root), relativePath=relative_root, includedFiles=count, includedLogicalBytes=size))
    members.sort(key=lambda row: row['archivePath'])
    require(len({r['archivePath'] for r in members}) == len(members), 'Duplicate member path')
    return members, roots


def build_archive(members):
    with private_output(ARCHIVE) as raw:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=9, fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT,
                              encoding='ascii', errors='strict') as bundle:
                for row in members:
                    path = Path(row['original']['path'])
                    require(snapshot(path) == row['originalStat'], 'Pre-archive source drift')
                    member = tarfile.TarInfo(row['archivePath'])
                    member.size = row['original']['bytes']
                    member.mode = 0o600
                    member.uid = member.gid = member.mtime = 0
                    member.uname = member.gname = ''
                    member.type = tarfile.REGTYPE
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    with os.fdopen(fd, 'rb') as source:
                        s = os.fstat(source.fileno())
                        require((s.st_dev, s.st_ino) == (row['originalStat']['device'], row['originalStat']['inode']), 'Archive-open inode drift')
                        bundle.addfile(member, source)
                    require(snapshot(path) == row['originalStat'], 'Post-archive source drift')
        raw.flush()
        os.fsync(raw.fileno())


def verify_archive(members):
    expected = {row['archivePath']: row for row in members}
    seen = []
    total = 0
    with ARCHIVE.open('rb') as source:
        header = source.read(10)
    require(header[:4] == b'\x1f\x8b\x08\x00' and header[4:8] == b'\0' * 4,
            'Unexpected gzip header, filename flag or timestamp')
    with tarfile.open(ARCHIVE, 'r|gz', encoding='ascii', errors='strict') as bundle:
        require(not bundle.pax_headers, 'Global PAX metadata')
        for member in bundle:
            require(member.name in expected and member.name not in seen, 'Unexpected/duplicate tar member')
            row = expected[member.name]
            safe_relative(member.name)
            require(member.type == tarfile.REGTYPE and not member.pax_headers and member.linkname == '', 'Nonregular/PAX/link member')
            require((member.uid, member.gid, member.mtime, member.mode) == (0, 0, 0, 0o600), 'Tar metadata differs')
            require(member.uname == member.gname == '' and member.size == row['original']['bytes'], 'Tar identity/size differs')
            h = hashlib.sha256()
            length = 0
            source = bundle.extractfile(member)
            require(source is not None, 'Missing regular member stream')
            with source:
                while block := source.read(1024**2):
                    length += len(block)
                    h.update(block)
            require(length == row['original']['bytes'] and h.hexdigest() == row['original']['sha256'], 'Tar bytes differ')
            seen.append(member.name)
            total += length
    require(seen == sorted(expected), 'Member set or sorted order differs')
    for row in members:
        require(describe(Path(row['original']['path'])) == (row['original'], row['originalStat']), 'Original bytes/stat drift')
    return dict(members=len(seen), logicalBytes=total, sortedMembers=True,
        allArchiveAndOriginalHashesMatch=True, regular0600Only=True, zeroUidGidMtime=True,
        noLinksOrSpecialMembers=True, noPax=True, noUnsafePaths=True,
        gzipEmptyFilenameZeroMtime=True)


CORE_PATHS = ('docs/decisions/evidence/e02-completion-preparation-r1/README.md', 'docs/decisions/evidence/e02-completion-preparation-r1/current-controls-r1/results-r1/acceptance.json', 'docs/decisions/evidence/e02-completion-preparation-r1/source-review-disposition.json', 'docs/decisions/evidence/e02-completion-preparation-r1/subject.json', 'docs/decisions/evidence/e02-minimum-runtime-preparation-r1/bridge-acceptance.json', 'docs/decisions/evidence/e02-minimum-runtime-preparation-r1/readiness-subject.json', 'docs/decisions/evidence/e02-minimum-runtime-preparation-r1/source-controls-subject.json', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r1/README.md', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r1/review-disposition.json', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r1/subject.json', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/README.md', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/current-controls-r1/results-r1/acceptance.json', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/source-review-disposition.json', 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/subject.json', 'docs/decisions/evidence/e02-ordinary-minimum-relay-diagnosis-r1/source-evidence-map.json', 'docs/decisions/evidence/e02-ordinary-minimum-relay-diagnosis-r1/subject.json', 'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1/README.md', 'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1/acceptance.json', 'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1/qa-review.json', 'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1/security-review.json', 'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1/subject-r2.json', 'docs/decisions/evidence/e02-owned-avd-overlay-reclamation-r7/result.json', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r5/PLAN.md', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r5/subject.json', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r6/PLAN.md', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r6/subject.json', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r7/PLAN.md', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r7/controls-external-r1/actual-qa-decisions.json', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r7/controls-external-r1/actual-security-decisions.json', 'docs/decisions/evidence/e06-request-phase-diagnostic-source-r7/subject.json', 'docs/decisions/evidence/e06-strace-containment-controls-r4/real-seven-outer-r1/actual-result-qa-review.json', 'docs/decisions/evidence/e06-strace-containment-controls-r4/real-seven-outer-r1/actual-result-security-review.json', 'docs/decisions/evidence/e06-strace-containment-controls-r4/real-seven-outer-r1/review-disposition.json', 'docs/decisions/evidence/e06-strace-containment-controls-r4/real-seven-outer-r1/runtime-results.json', 'docs/decisions/evidence/e06-strace-containment-controls-r4/real-seven-outer-r1/subject.json', 'docs/decisions/evidence/e06-strace-containment-controls-r5/real-seven-outer-r1/actual-result-qa-review.json', 'docs/decisions/evidence/e06-strace-containment-controls-r5/real-seven-outer-r1/actual-result-security-review.json', 'docs/decisions/evidence/e06-strace-containment-controls-r5/real-seven-outer-r1/review-disposition.json', 'docs/decisions/evidence/e06-strace-containment-controls-r5/real-seven-outer-r1/runtime-results.json', 'docs/decisions/evidence/e06-strace-containment-controls-r5/real-seven-outer-r1/subject.json', 'docs/decisions/evidence/e06-strace-containment-controls-r6/real-seven-outer-r1/review-disposition.json', 'docs/decisions/evidence/e06-strace-containment-controls-r6/real-seven-outer-r1/runtime-results.json', 'docs/decisions/evidence/e06-strace-containment-controls-r6/real-seven-outer-r1/subject.json', 'docs/decisions/evidence/e06-strace-transient-source-research-r1/report.json', 'experiments/prototypes/e02_completion_v1/CONTRACT.md', 'experiments/prototypes/e02_completion_v1/README.md', 'experiments/prototypes/e02_completion_v1/data.mjs', 'experiments/prototypes/e02_completion_v1/profile.json', 'experiments/prototypes/e02_completion_v1/run-config-template.json', 'experiments/prototypes/e02_completion_v1/runner.mjs', 'experiments/prototypes/e02_completion_v1/test_data.mjs', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/CONTRACT.md', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/README.md', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/consumer.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/gui.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/strict.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/test_data_controls.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/wire.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v1/witness.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/CONTRACT.md', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/README.md', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/consumer.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/gui.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/strict.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/test_data_controls.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/wire.py', 'experiments/prototypes/e02_ordinary_minimum_consumer_v2/witness.py')

def suggested_core(members):
    available = {Path(row['original']['path']).relative_to(ROOT).as_posix() for row in members}
    require(set(CORE_PATHS) <= available, 'Suggested core absent from exact archive')
    return list(CORE_PATHS)


def main():
    freeze = verify_freeze()
    members, roots = enumerate_roots()
    size = sum(r['original']['bytes'] for r in members)
    common = dict(actor='/root/local_monitor_controls', roots=roots,
                  memberCount=len(members), logicalBytes=size, excluded=[])
    write_json('selection.json', dict(schema='nbdp-progress-archive-selection-v2', **common,
        freeze=freeze, constraints=dict(fixedRootsOnly=True, externalReferentsNotCopied=True,
        previousPublicationPackagesNotRepacked=True, mutableCurrentIndexesExcluded=True,
        sourceDiffAndPatchKeptOnlyInsideArchive=True)))
    build_archive(members)
    archive_pin = describe(ARCHIVE)[0]
    write_json('archive-index.json', dict(schema='nbdp-runtime-progress-archive-index-v2', **common,
        archive=archive_pin, members=members, freeze=freeze,
        archiveMetadata=dict(mode='0600', uid=0, gid=0, mtime=0, format='USTAR',
                             gzipFilename='', gzipMtime=0, pax=False),
        limits=['File-copy counts are not distinct experiments, tests or assertions.',
                'Original modes/stats are explicit. Archived0600 does not restore original0640 negative fixtures or0664 preparation source modes and is not portable replay.',
                'External binaries and tool/SDK referents remain outside this inspection-only copy.',
                'Authority/config/runtime records are historical evidence only; external origins and grants are not renewed.',
                'Packaging grants no experiment authority, PASS, gate closure or independent acceptance.']))
    verification = verify_archive(members)
    after_members, after_roots = enumerate_roots()
    require((after_members, after_roots) == (members, roots), 'Original membership/stat/hash drift')
    require(describe(HERE / 'freeze-authorization.json')[0] == freeze, 'Freeze manifest drift')
    verification.update(schema='nbdp-runtime-progress-archive-verification-v2', actor='/root/local_monitor_controls',
        archive=archive_pin, index=describe(HERE / 'archive-index.json')[0],
        originalMembershipUnchanged=True, excludedFiles=0, sourceEvaluation=False,
        experimentsExecuted=0, projectImports=0, gitMutations=0, publication=False,
        scope='DATA serialization/archive/hash validation only.')
    write_json('archive-verification.json', verification)
    write_json('normal-core-suggestion.json', dict(schema='nbdp-normal-core-suggestion-v2',
        status='SUGGESTION_ONLY_NOT_STAGED', files=suggested_core(members),
        limits=['No actual-run/raw nested streams or diff/patch normal-tree suggestions.',
                'Readable entrypoints are suggestions; coordinator must verify links and scope.',
                'Historical grants are evidence only, never authority to execute them.']))
    print(json.dumps(dict(archive=archive_pin, verification=verification)))


if __name__ == '__main__':
    main()
