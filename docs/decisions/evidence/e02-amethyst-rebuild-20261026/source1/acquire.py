"""Fixed tool acquisition/extraction. Execution needs separate root release.

No tool binaries are executed. Archives, partials and failures are retained.
The source checkout, global configuration and SDK license state are untouched.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import ssl
import stat
import tarfile
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = Path('/tmp/nbdp-amethyst-rebuild-20261026')
PLAN = ROOT / 'preparation/acquisition-plan.json'
RESULTS = ROOT / 'output/acquisition'


def require(value, message):
    if not value: raise ValueError(message)


def private(path):
    path = Path(path)
    require(path.is_relative_to(ROOT) and not path.is_symlink(), 'OWNED_PATH_REQUIRED')
    for p in (path, *path.parents):
        if p == ROOT.parent: break
        require(not p.is_symlink(), 'SYMLINK_COMPONENT')
    return path


def create(path, mode=0o600):
    return os.open(private(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)


def digest(path):
    h = hashlib.sha256(); count = 0
    fd = os.open(private(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno()); require(stat.S_ISREG(before.st_mode), 'REGULAR_FILE')
        while block := stream.read(1048576): h.update(block); count += len(block)
        after = os.fstat(stream.fileno())
        require(tuple(getattr(before,k) for k in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns'))
            == tuple(getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns')), 'FILE_CHANGED_DURING_READ')
    return dict(path=str(path), bytes=count, sha256=h.hexdigest())


def record(path, value):
    raw = (json.dumps(value, indent=2) + '\n').encode()
    with os.fdopen(create(path), 'wb') as stream:
        require(stream.write(raw) == len(raw), 'SHORT_RECORD_WRITE'); stream.flush(); os.fsync(stream.fileno())


def url_allowed(url, hosts):
    p = urllib.parse.urlsplit(url)
    require(p.scheme == 'https' and p.hostname in hosts and p.port in (None, 443)
        and p.username is None and p.password is None and not p.fragment, 'CLOSED_PUBLIC_HTTPS_URL')
    return p


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, item, deadline): self.item, self.deadline, self.history = item, deadline, []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require(time.monotonic() < self.deadline, 'ACQUISITION_DEADLINE')
        require(len(self.history) < self.item['redirects'], 'REDIRECT_NOT_ALLOWED')
        target = urllib.parse.urljoin(req.full_url, newurl); parsed = url_allowed(target, self.item['allowedHosts'])
        # Signed public asset query strings are not copied into logs.
        self.history.append(dict(status=code, host=parsed.hostname, path=parsed.path))
        return urllib.request.Request(target, method='GET', headers={'User-Agent':'NBDP-isolated-lab-acquisition'})


def fetch(item, limits):
    final = ROOT / 'cache' / (item['id'] + '.archive'); partial = final.with_suffix('.partial')
    require(not final.exists(), 'ARCHIVE_ALREADY_EXISTS_NO_RETRY')
    require(shutil.disk_usage(ROOT / 'cache').free >= limits['freeDiskBeforeAcquisition'], 'FRESH_DISK_ADMISSION')
    deadline = time.monotonic() + limits['downloadSeconds']
    redirects = Redirects(item, deadline)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()), redirects)
    url_allowed(item['url'], item['allowedHosts'])
    expected = hashlib.new(item['algorithm']); sha256 = hashlib.sha256(); total = 0
    request = urllib.request.Request(item['url'], method='GET', headers={'User-Agent':'NBDP-isolated-lab-acquisition'})
    with os.fdopen(create(partial), 'wb') as stream:
        with opener.open(request, timeout=limits['httpOperationSeconds']) as response:
            require(response.status == 200, 'FULL_HTTP200_REQUIRED')
            require(response.headers.get('Content-Encoding', 'identity') == 'identity', 'NO_CONTENT_TRANSFORMATION')
            length = response.headers.get('Content-Length')
            require(length is None or length == str(item['bytes']), 'EXACT_CONTENT_LENGTH')
            while True:
                require(time.monotonic() < deadline, 'ACQUISITION_DEADLINE')
                block = response.read1(limits['chunkBytes'])
                if not block: break
                total += len(block); require(total <= item['bytes'], 'ARCHIVE_SIZE_CEILING')
                expected.update(block); sha256.update(block)
                require(stream.write(block) == len(block), 'SHORT_ARCHIVE_WRITE')
        require(time.monotonic() < deadline and total == item['bytes'], 'EXACT_ARCHIVE_SIZE')
        require(expected.hexdigest() == item['digest'], 'PUBLISHED_CHECKSUM_MISMATCH')
        stream.flush(); os.fsync(stream.fileno())
    # Fresh private root and exclusive partial; final is never overwritten.
    require(not final.exists(), 'FINAL_ARCHIVE_EXISTS'); os.rename(partial, final)
    record(RESULTS / (item['id'] + '-fetch.json'),
        dict(archive=digest(final), publishedAlgorithm=item['algorithm'], publishedDigest=item['digest'],
             measuredSha256=sha256.hexdigest(), redirects=redirects.history, toolsExecuted=False))


def name(value, limits):
    require(isinstance(value, str) and 0 < len(value) <= limits['pathCharacters'], 'ARCHIVE_PATH_BOUND')
    value = value[:-1] if value.endswith('/') else value
    p = PurePosixPath(value)
    require(value and not p.is_absolute() and str(p) == value and '\\' not in value
        and all(x not in ('', '.', '..') for x in p.parts)
        and not any(ord(c) < 32 or ord(c) == 127 for c in value), 'ARCHIVE_PATH_ESCAPE_OR_ALIAS')
    return p


def target_path(member, target, hard, limits):
    require(isinstance(target, str) and 0 < len(target.encode()) <= limits['linkTargetBytes']
        and not target.startswith('/') and '\\' not in target and not any(ord(c) < 32 for c in target), 'LINK_TARGET')
    parts = [] if hard else list(member.parent.parts)
    for segment in target.split('/'):
        if segment in ('', '.'): continue
        if segment == '..':
            require(parts, 'LINK_ESCAPE'); parts.pop()
        else: parts.append(segment)
    require(parts, 'LINK_ROOT_OR_ESCAPE')
    return PurePosixPath(*parts)


def validate_members(rows, item, limits):
    require(len(rows) <= limits['archiveMembers'], 'ARCHIVE_MEMBER_COUNT')
    members, total = {}, 0
    for row in rows:
        p = row['path']; require(p not in members, 'DUPLICATE_ARCHIVE_MEMBER')
        require(row['kind'] in ('file', 'dir', 'symlink', 'hardlink'), 'SPECIAL_ARCHIVE_MEMBER')
        require(0 <= row['bytes'] <= item['singleFileBytes'], 'ARCHIVE_SINGLE_FILE_BOUND')
        total += row['bytes']; require(total <= item['expandedBytes'], 'ARCHIVE_TOTAL_EXPANSION_BOUND')
        members[p] = row
    for p in list(members):
        for parent in p.parents:
            if str(parent) == '.': continue
            if parent in members: require(members[parent]['kind'] == 'dir', 'LINK_OR_FILE_AS_PARENT')
            else: members[parent] = dict(path=parent, kind='dir', bytes=0, mode=0o755)
    require(len(members) <= limits['archiveMembers'], 'EXPANDED_DIRECTORY_COUNT')
    def resolve(p, seen=()):
        require(len(seen) <= limits['linkHops'] and p not in seen, 'LINK_CYCLE_OR_DEPTH')
        require(p in members, 'DANGLING_LINK')
        row = members[p]
        if row['kind'] in ('symlink', 'hardlink'):
            t = target_path(p, row['target'], row['kind'] == 'hardlink', limits)
            require(t in members, 'LINK_TARGET_OUTSIDE_ARCHIVE')
            if row['kind'] == 'hardlink': require(members[t]['kind'] == 'file', 'HARDLINK_REQUIRES_DIRECT_REGULAR_TARGET')
            return resolve(t, (*seen, p))
        return p
    for p, row in members.items():
        if row['kind'] in ('symlink', 'hardlink'): resolve(p)
    roots = {p.parts[0] for p in members}; require(len(roots) == 1, 'ONE_ARCHIVE_ROOT_REQUIRED')
    return members, next(iter(roots)), total


@contextmanager
def opened_archive(path, item, deadline):
    fd = os.open(private(path), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        state = os.fstat(stream.fileno())
        require(stat.S_ISREG(state.st_mode) and state.st_size == item['bytes'], 'PINNED_ARCHIVE_LENGTH')
        expected = hashlib.new(item['algorithm']); before = hashlib.sha256()
        while block := stream.read(1048576):
            require(time.monotonic() < deadline, 'EXTRACTION_DEADLINE')
            expected.update(block); before.update(block)
        require(expected.hexdigest() == item['digest'], 'PINNED_ARCHIVE_DIGEST')
        stream.seek(0)
        archive = tarfile.open(fileobj=stream, mode='r:gz') if item['format'] == 'tar' else zipfile.ZipFile(stream)
        first = None
        try: yield archive
        except BaseException as error:
            first = error; raise
        finally:
            try:
                archive.close(); stream.seek(0); after = hashlib.sha256()
                while block := stream.read(1048576):
                    require(time.monotonic() < deadline, 'EXTRACTION_DEADLINE')
                    after.update(block)
                require(before.digest() == after.digest(), 'ARCHIVE_CHANGED_DURING_EXTRACTION')
            except Exception as secondary:
                if first is None: raise
                first.add_note('Archive cleanup/check secondary: '+type(secondary).__name__)


def extract(item, limits):
    deadline = time.monotonic() + limits['downloadSeconds']
    archive_path = ROOT / 'cache' / (item['id'] + '.archive')
    stage = ROOT / 'tools' / ('.stage-' + item['id']); private(stage).mkdir(mode=0o700)
    rows = []
    with opened_archive(archive_path, item, deadline) as archive:
        if item['format'] == 'tar':
            for info in archive:
                require(time.monotonic() < deadline, 'EXTRACTION_DEADLINE')
                require(len(rows) < limits['archiveMembers'], 'ARCHIVE_MEMBER_COUNT')
                kind = 'file' if info.isfile() else 'dir' if info.isdir() else 'symlink' if info.issym() else 'hardlink' if info.islnk() else 'special'
                rows.append(dict(path=name(info.name, limits), kind=kind, bytes=info.size, mode=info.mode,
                    target=info.linkname, info=info))
        else:
            for info in archive.infolist():
                require(time.monotonic() < deadline and len(rows) < limits['archiveMembers'], 'EXTRACTION_DEADLINE_OR_MEMBERS')
                require(info.filename == info.orig_filename, 'ZIP_NAME_NORMALIZATION_REFUSED')
                mode = info.external_attr >> 16; kindbits = stat.S_IFMT(mode)
                kind = 'dir' if info.is_dir() else 'symlink' if kindbits == stat.S_IFLNK else 'file' if kindbits in (0, stat.S_IFREG) else 'special'
                require(info.flag_bits & 1 == 0, 'NO_ENCRYPTED_ZIP')
                target = ''
                if kind == 'symlink':
                    require(info.file_size <= limits['linkTargetBytes'], 'ZIP_LINK_BODY_BOUND')
                    target = archive.read(info).decode('utf-8', 'strict')
                rows.append(dict(path=name(info.filename, limits), kind=kind, bytes=info.file_size,
                    mode=mode or (0o755 if kind == 'dir' else 0o644), target=target, info=info))
        members, top, expanded = validate_members(rows, item, limits)
        for p, row in sorted(members.items(), key=lambda pair: len(pair[0].parts)):
            if row['kind'] == 'dir': private(stage / p).mkdir(mode=0o700, exist_ok=True)
        for p, row in members.items():
            require(time.monotonic() < deadline, 'EXTRACTION_DEADLINE')
            if row['kind'] != 'file': continue
            reader = archive.extractfile(row['info']) if item['format'] == 'tar' else archive.open(row['info'])
            with reader, os.fdopen(create(stage / p), 'wb') as stream:
                copied = 0
                while block := reader.read(limits['chunkBytes']):
                    require(time.monotonic() < deadline, 'EXTRACTION_DEADLINE')
                    copied += len(block); require(copied <= row['bytes'], 'EXPANDED_FILE_SIZE_CEILING')
                    require(stream.write(block) == len(block), 'SHORT_EXTRACT_WRITE')
                require(copied == row['bytes'], 'EXACT_EXPANDED_SIZE')
                stream.flush(); os.fsync(stream.fileno())
            os.chmod(stage / p, row['mode'] & 0o755)
        for p, row in members.items():
            if row['kind'] == 'symlink': os.symlink(row['target'], private(stage / p))
            elif row['kind'] == 'hardlink': os.link(stage / target_path(p, row['target'], True, limits), private(stage / p), follow_symlinks=False)
        base = stage / top
        for p in base.rglob('*'):
            if p.is_symlink(): require(p.resolve(strict=True).is_relative_to(base.resolve()), 'EXTRACTED_LINK_ESCAPE')
    actual = inventory(base, deadline)
    destination = ROOT / item['destination']
    properties = None
    if item['id'] == 'jdk':
        release = (base / 'release').read_text()
        require('JAVA_VERSION="21.0.13"' in release, 'EXPECTED_JDK_RELEASE')
    else:
        raw = (base / 'source.properties').read_text(); properties = {}
        for line in raw.splitlines():
            if '=' in line:
                key, value = line.split('=', 1); properties[key.strip()] = value.strip()
        if item['id'] == 'platform':
            require(properties.get('AndroidVersion.ApiLevel') == '37', 'EXPECTED_PLATFORM_API')
            require(properties.get('Pkg.Path', 'platforms;android-37.0') == 'platforms;android-37.0', 'EXACT_PLATFORM_PACKAGE_PATH')
            destination = destination / 'android-37.0'
        else: require(properties.get('Pkg.Revision') == ('36.0.0' if item['id'] == 'build-tools' else '30.0.16248370'), 'EXPECTED_SDK_PACKAGE_REVISION')
    private(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    require(not destination.exists(), 'FRESH_TOOL_DESTINATION_REQUIRED')
    os.rename(base, destination)
    record(RESULTS / (item['id'] + '-extraction.json'), dict(archive=digest(archive_path),
        destination=str(destination), properties=properties, inventory=actual, expandedBytes=expanded,
        archiveMembers=[dict(path=str(r['path']),kind=r['kind'],bytes=r['bytes'],mode=oct(r['mode']),target=r.get('target')) for r in rows],
        modes='Directories private0700; regular modes archive &0755; links preserved safely; no tools executed', toolsExecuted=False))


def inventory(root, deadline):
    rows = []
    for path in sorted(root.rglob('*')):
        require(time.monotonic() < deadline, 'EXTRACTION_INVENTORY_DEADLINE')
        rel = str(path.relative_to(root)); st = path.lstat()
        if path.is_symlink(): rows.append(dict(path=rel,kind='symlink',target=os.readlink(path)))
        elif path.is_dir(): rows.append(dict(path=rel,kind='dir',mode=oct(stat.S_IMODE(st.st_mode))))
        else:
            require(path.is_file(), 'NO_SPECIAL_EXTRACTED_FILES')
            d = digest(path); rows.append(dict(path=rel,kind='file',bytes=d['bytes'],sha256=d['sha256'],mode=oct(stat.S_IMODE(st.st_mode))))
    return rows


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('phase',choices=('fetch','extract'))
    p.add_argument('artifact',choices=('jdk','platform','build-tools','ndk')); p.add_argument('--plan-sha',required=True)
    args = p.parse_args(); require(digest(PLAN)['sha256'] == args.plan_sha, 'EXTERNAL_PLAN_SHA_REQUIRED')
    plan = json.loads(PLAN.read_bytes()); require(plan['root'] == str(ROOT), 'FIXED_ACQUISITION_ROOT')
    item = next(row for row in plan['artifacts'] if row['id'] == args.artifact)
    require(item['algorithm'] in ('sha1','sha256') and re.fullmatch('[0-9a-f]{'+str(40 if item['algorithm']=='sha1' else 64)+'}',item['digest']), 'EXPLICIT_DIGEST_ALGORITHM')
    private(RESULTS).mkdir(mode=0o700,exist_ok=True)
    try:
        (fetch if args.phase == 'fetch' else extract)(item,plan['limits'])
    except Exception as error:
        try:
            record(RESULTS / (args.artifact+'-'+args.phase+'-FAILED.json'),
                dict(error=type(error).__name__+':'+str(error)[:2048],state='FAILED_NO_RETRY',toolsExecuted=False,
                     utc=datetime.now(timezone.utc).isoformat()))
        except Exception as retention:
            import sys
            print(json.dumps(dict(first=type(error).__name__,retention=type(retention).__name__)),file=sys.stderr)
        raise


if __name__ == '__main__': main()
