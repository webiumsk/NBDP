"""Build an inspection-only deterministic copy of the assigned closed evidence.

This script imports no project module and executes no experiment or Git command.
It writes only its own publication directory and refuses existing output files.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import stat
import tarfile

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = ROOT / 'docs/decisions/evidence/transport-runtime-progress-publication-r2'
ARCHIVE = HERE / 'completed-runtime-evidence.tar.gz'
EVIDENCE_NAMES = (
    'e02-android-boot-trace-preparation-r1',
    'e02-android-boot-trace-runtime-r1',
    'e02-android-renderer-research-r1',
    'e02-owned-avd-overlay-reclamation-r1',
    'e02-owned-avd-overlay-reclamation-r2',
    'e02-android-lavapipe-preparation-r1',
    'e02-android-lavapipe-runtime-r1',
    'e02-api35-fixture-preparation-r1',
    'e02-api35-fixture-preparation-r2',
    'e06-local-monitor-controls-r1',
    'e06-local-fonly-primary-preparation-r1',
    'e06-local-fonly-primary-execution-r1',
    'e06-local-fonly-primary-runtime-r1',
    'e06-local-authority-mode-remediation-r1',
    'e06-local-fonly-primary-preparation-r2',
    'e06-local-fonly-primary-execution-r2',
    'e06-local-fonly-primary-runtime-r2',
    'e06-js-startup-prefix-diagnostic-r1',
    'e06-js-startup-prefix-diagnostic-r2',
    'e06-js-startup-prefix-diagnostic-r3',
)
ROOTS = tuple(ROOT / 'experiments/prototypes' / name for name in (
    'e02_android_boot_trace_v1', 'e02_android_lavapipe_trace_v1',
)) + tuple(ROOT / 'docs/decisions/evidence' / name for name in EVIDENCE_NAMES)
LICENSE_ROOTS = {'e02-api35-fixture-preparation-r1', 'e02-api35-fixture-preparation-r2'}
FORBIDDEN_SUFFIXES = {'.apk', '.zip', '.img', '.qcow2', '.pem', '.key', '.jks', '.p12', '.keystore'}


def private_output(path):
    assert path.parent == HERE and path.resolve() == path
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    return os.fdopen(fd, 'wb')


def write_json(name, value):
    raw = (json.dumps(value, indent=2) + '\n').encode()
    with private_output(HERE / name) as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def snapshot(path):
    s = path.lstat()
    assert stat.S_ISREG(s.st_mode) and not path.is_symlink() and path.resolve() == path
    assert path.is_relative_to(ROOT) and 0 <= s.st_size <= 32 * 1024**2
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
        assert (s.st_dev, s.st_ino) == (before['device'], before['inode'])
        while block := handle.read(1024**2):
            length += len(block)
            h.update(block)
    assert snapshot(path) == before and length == before['bytes']
    return dict(path=str(path), bytes=length, sha256=h.hexdigest()), before


def enumerate_roots():
    included = []
    excluded = []
    rows = []
    for root in ROOTS:
        assert root.is_dir() and root.resolve() == root and not root.is_symlink()
        count = size = 0
        for path in sorted(root.rglob('*')):
            s = path.lstat()
            if stat.S_ISDIR(s.st_mode):
                assert not path.is_symlink()
                continue
            assert stat.S_ISREG(s.st_mode) and not path.is_symlink(), path
            descriptor, file_stat = describe(path)
            if root.name in LICENSE_ROOTS and path.name == 'current-official-license-text.txt':
                excluded.append(dict(original=descriptor, originalStat=file_stat,
                                     reason='Full official license text retained locally; not redistributed in this inspection bundle. Fixture metadata preserves its descriptor and technical identity result.'))
                continue
            assert path.suffix.lower() not in FORBIDDEN_SUFFIXES, path
            relative = path.relative_to(ROOT).as_posix()
            archive_path = 'repository/' + relative
            assert not Path(archive_path).is_absolute() and '..' not in Path(archive_path).parts
            included.append(dict(archivePath=archive_path, original=descriptor, originalStat=file_stat))
            count += 1
            size += descriptor['bytes']
        rows.append(dict(path=str(root), relativePath=root.relative_to(ROOT).as_posix(),
                         includedFiles=count, includedLogicalBytes=size))
    included.sort(key=lambda row: row['archivePath'])
    assert len({row['archivePath'] for row in included}) == len(included)
    assert len(excluded) == 2 and len(included) <= 2500
    assert sum(row['original']['bytes'] for row in included) <= 64 * 1024**2
    return included, excluded, rows


def archive_members(members):
    with private_output(ARCHIVE) as raw:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=9, fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as bundle:
                for row in members:
                    path = Path(row['original']['path'])
                    assert snapshot(path) == row['originalStat']
                    member = tarfile.TarInfo(row['archivePath'])
                    member.size = row['original']['bytes']
                    member.mode = 0o600
                    member.uid = member.gid = member.mtime = 0
                    member.uname = member.gname = ''
                    member.type = tarfile.REGTYPE
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                    with os.fdopen(fd, 'rb') as source:
                        s = os.fstat(source.fileno())
                        assert (s.st_dev, s.st_ino) == (row['originalStat']['device'], row['originalStat']['inode'])
                        bundle.addfile(member, source)
                    assert snapshot(path) == row['originalStat']
        raw.flush()
        os.fsync(raw.fileno())


def verify_archive(members):
    expected = {row['archivePath']: row for row in members}
    seen = set()
    total = 0
    with tarfile.open(ARCHIVE, 'r:gz') as bundle:
        for member in bundle:
            assert member.name in expected and member.name not in seen
            row = expected[member.name]
            assert member.isfile() and not member.issym() and not member.islnk()
            assert member.name.startswith('repository/') and '..' not in Path(member.name).parts
            assert (member.uid, member.gid, member.mtime, member.mode) == (0, 0, 0, 0o600)
            assert member.uname == member.gname == '' and member.size == row['original']['bytes']
            h = hashlib.sha256()
            length = 0
            source = bundle.extractfile(member)
            assert source is not None
            with source:
                while block := source.read(1024**2):
                    length += len(block)
                    h.update(block)
            assert length == row['original']['bytes'] and h.hexdigest() == row['original']['sha256']
            seen.add(member.name)
            total += length
    assert seen == set(expected)
    # Re-read every original. Tar verification alone cannot attest that the
    # frozen source paths still refer to those same bytes and metadata.
    for row in members:
        descriptor, file_stat = describe(Path(row['original']['path']))
        assert descriptor == row['original'] and file_stat == row['originalStat']
    return dict(members=len(seen), logicalBytes=total, allArchiveAndOriginalHashesMatch=True,
                sortedMembers=True, regular0600Only=True, zeroUidGidMtime=True,
                noLinksOrSpecialMembers=True, noUnsafePaths=True)


def suggested_normal_core(members):
    names = {
        'README.md', 'subject.json', 'acceptance.json', 'control-acceptance.json',
        'independent-qa-review.json', 'independent-security-review.json',
        'independent-researcher-correlation.json', 'initial-review-history.json',
        'source-qa-review.json', 'source-security-review.json',
        'source-qa-rationale.json', 'source-security-rationale.json',
        'failed-controls-qa-review.json', 'failed-controls-security-review.json',
        'actual-controls-qa-review.json', 'actual-controls-security-review.json',
        'actual-preflight-refusal.json', 'configuration-core.json', 'worker-config.json',
        'configuration-approval.json', 'qualification-config.json',
        'configuration-qa-review.json', 'configuration-security-review.json',
        'monitor.py', 'monitor-PLAN.md', 'monitor-subject.json', 'monitor-static.json',
        'workflow-prerequisites.json', 'activation-readiness.json',
        'sdk-tree.json', 'result.json', 'outcome-addendum.json',
        'license-identity-addendum.json', 'metadata-provenance.json',
    }
    selected = []
    for row in members:
        path = Path(row['original']['path'])
        if path.is_relative_to(ROOT / 'experiments/prototypes'):
            selected.append(path.relative_to(ROOT).as_posix())
            continue
        relative = path.relative_to(ROOT / 'docs/decisions/evidence')
        if len(relative.parts) == 2 and (path.name in names or path.name.startswith('exact-root-')):
            selected.append(path.relative_to(ROOT).as_posix())
    return sorted(selected)


def main():
    assert HERE.is_dir() and HERE.resolve() == HERE
    assert set(path.name for path in HERE.iterdir()) == {'build_archive.py'}
    members, excluded, roots = enumerate_roots()
    write_json('selection.json', dict(schema='nbdp-progress-archive-selection-v1',
        actor='/root/progress_archive_implementer', roots=roots,
        includedFiles=len(members), includedLogicalBytes=sum(row['original']['bytes'] for row in members),
        excluded=excluded, constraints=dict(projectIndexesExcluded=True,
            activeStartupR4Excluded=True, activeAndroid35ProfileExcluded=True,
            sixPriorArchivesNotRepacked=True, noExternalReferentsCopied=True)))
    archive_members(members)
    archive_pin, _ = describe(ARCHIVE)
    write_json('archive-index.json', dict(schema='nbdp-runtime-progress-archive-index-v1',
        actor='/root/progress_archive_implementer', archive=archive_pin,
        memberCount=len(members), logicalBytes=sum(row['original']['bytes'] for row in members),
        roots=roots, members=members, excluded=excluded,
        archiveMetadata=dict(mode='0600', uid=0, gid=0, mtime=0,
                             format='USTAR', gzipFilename='', gzipMtime=0),
        limits=['File copies, not unique experiments, controls or assertions.',
                'Original modes/stats remain in this index; tar600 does not alter historical files.',
                'External SDK/tool/archive inputs remain local and are not a portable replay image.',
                'Packaging does not establish conformance, current execution authority or independent review.']))
    verification = verify_archive(members)
    # Confirm selection membership, including the two explicitly excluded texts.
    after_members, after_excluded, after_roots = enumerate_roots()
    assert members == after_members and excluded == after_excluded and roots == after_roots
    verification.update(schema='nbdp-runtime-progress-archive-verification-v1',
        actor='/root/progress_archive_implementer', archive=archive_pin,
        index=describe(HERE / 'archive-index.json')[0], originalMembershipUnchanged=True,
        excludedFiles=len(excluded), sourceEvaluation=False, experimentsExecuted=0,
        projectImports=0, gitMutations=0, scope='DATA serialization/archive/hash validation only.')
    write_json('archive-verification.json', verification)
    write_json('normal-core-suggestion.json', dict(schema='nbdp-normal-core-suggestion-v1',
        actor='/root/progress_archive_implementer', status='SUGGESTION_ONLY_NOT_STAGED',
        files=suggested_normal_core(members),
        limits=['Coordinator must select/stage/review explicitly.',
                'No actual-run/raw stream/patch/diff members suggested as normal tree duplicates.',
                'Suggested README links may retain archival context; validate current normal-tree navigation separately.']))
    print(json.dumps(dict(archive=archive_pin, verification=verification,
                          selection=describe(HERE / 'selection.json')[0])))


if __name__ == '__main__':
    main()
