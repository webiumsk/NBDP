"""Finite byte-DATA restoration only. No SDK/program/service is invoked.

Prepared source requires independent review and a separate root release. TLS
downloads, safe ZIP validation and extraction run only from main(). Existing
inputs/evidence are never changed; failed attempts remain for inspection.
"""
import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import signal
import ssl
import stat
import struct
import time
import urllib.request
import zipfile

WORK = Path('/tmp/nbdp-sdk-restoration-20261026-r2')
DEST = Path('/tmp/nbdp-e02-api35-fixture-r2/sdk')
INVENTORY = Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-api35-fixture-preparation-r2/sdk-tree.json')
INVENTORY_SHA = '5c996f67fd8aba0ea618adc7f7f9e6a2c27c641cc95910deb07bdfa8a10562a8'
CHUNK = 1048576


def need(value, message):
    if not value: raise ValueError(message)


def canonical(value, directory=False):
    need(type(value) is str and value and '\\' not in value and ':' not in value and
         '\x00' not in value and all(ord(c) >= 32 and ord(c) != 127 for c in value), 'UNSAFE_MEMBER_NAME')
    name = value[:-1] if directory and value.endswith('/') else value
    p = PurePosixPath(name)
    need(not p.is_absolute() and all(x not in ('', '.', '..') for x in name.split('/')) and str(p) == name, 'NONCANONICAL_MEMBER_NAME')
    return name


def directory(path, create=False):
    """Open each absolute component without following symlinks; caller closes FD."""
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'ABSOLUTE_DIRECTORY_REQUIRED')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for name in path.parts[1:]:
            if create:
                try: os.mkdir(name, 0o700, dir_fd=fd)
                except FileExistsError: pass
            new = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = new
        return fd
    except BaseException:
        os.close(fd); raise


def hash_file(path):
    digest = hashlib.sha256(); count = 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'REGULAR_INPUT_REQUIRED')
        while block := stream.read(CHUNK): count += len(block); digest.update(block)
        after = os.fstat(stream.fileno())
    identity = lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
    need(identity(before) == identity(after) and count == before.st_size, 'INPUT_CHANGED_WHILE_HASHING')
    return dict(path=str(path), bytes=count, sha256=digest.hexdigest())


class Deadline:
    def __init__(self, seconds, work_seconds):
        start = time.monotonic()
        self.total_end = start + seconds
        self.end = start + work_seconds
        signal.signal(signal.SIGALRM, self.expired)
        self.arm(self.end)

    @staticmethod
    def expired(*_): raise TimeoutError('FINITE_RESTORATION_DEADLINE')

    def arm(self, end):
        remaining = min(end, self.end) - time.monotonic()
        need(remaining > 0, 'RESTORATION_DEADLINE')
        signal.setitimer(signal.ITIMER_REAL, remaining)

    def check(self): need(time.monotonic() < self.end, 'RESTORATION_DEADLINE')

    def failure_receipt(self):
        # Reserve within the original global deadline, never renew work time.
        remaining = min(5, self.total_end - time.monotonic())
        need(remaining > 0, 'GLOBAL_DEADLINE_NO_RECEIPT_TIME')
        signal.setitimer(signal.ITIMER_REAL, remaining)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): raise ValueError('HTTP_REDIRECT_REFUSED')


class Restore:
    def __init__(self, plan):
        self.plan = plan
        self.deadline = Deadline(plan['bounds']['globalSeconds'], plan['bounds']['workSeconds'])
        self.attempt = WORK / plan['attemptDirectory']
        self.stage = self.attempt / 'stage-sdk'
        self.remaining = plan['totals']['archiveBytes'] + plan['totals']['selectedBytes']
        self.disk_samples = 0; self.lowest_free = None; self.events = []
        self.stage_fd = self.attempt_fd = self.parent_fd = None
        self.placement_state = 'NOT_ATTEMPTED'
        self.rename_return = self.rename_errno = None

    def check(self):
        self.deadline.check()
        free = os.statvfs(WORK).f_bavail * os.statvfs(WORK).f_frsize
        self.disk_samples += 1
        self.lowest_free = free if self.lowest_free is None else min(free, self.lowest_free)
        reserve = self.plan['bounds']['retainedReserveBytes'] + self.plan['bounds']['metadataAndBlockMarginBytes']
        need(free >= reserve + self.remaining, 'RESERVE_PLUS_REMAINING_PLANNED_BYTES_REFUSED')

    def initialize(self):
        self.check()
        parent = directory(DEST.parent, create=True)
        try:
            try: os.stat(DEST.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError: pass
            else: raise FileExistsError('DESTINATION_ALREADY_EXISTS')
            self.parent_fd = parent; parent = None
            workfd = directory(WORK)
            try: os.mkdir(self.plan['attemptDirectory'], 0o700, dir_fd=workfd)
            finally: os.close(workfd)
            self.attempt_fd = directory(self.attempt)
            os.mkdir('downloads', 0o700, dir_fd=self.attempt_fd)
            os.mkdir('stage-sdk', 0o700, dir_fd=self.attempt_fd)
            self.stage_fd = directory(self.stage)
            need(os.fstat(self.stage_fd).st_dev == os.fstat(self.parent_fd).st_dev, 'SAME_FILESYSTEM_RENAME_REQUIRED')
        finally:
            if parent is not None: os.close(parent)

    def write(self, fd, block, account=True):
        view = memoryview(block)
        while view:
            self.check()
            count = os.write(fd, view)
            need(0 < count <= len(view), 'CHECKED_WRITE_REFUSED')
            if account: self.remaining -= count
            need(self.remaining >= 0, 'PLANNED_BYTES_OVERFLOW')
            view = view[count:]
        self.check()

    def receipt(self, name, value):
        need(self.attempt_fd is not None, 'ATTEMPT_NOT_INITIALIZED')
        raw = (json.dumps(value, indent=2) + '\n').encode()
        need(len(raw) <= self.plan['bounds']['maximumReceiptBytes'], 'RECEIPT_BOUND')
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.attempt_fd)
        try:
            # Receipts use the explicit metadata margin, not extraction budget.
            view = memoryview(raw)
            while view:
                count = os.write(fd, view); need(count > 0, 'RECEIPT_WRITE'); view = view[count:]
            os.fsync(fd)
        finally: os.close(fd)

    def download(self, artifact):
        self.check(); started = time.monotonic()
        self.deadline.arm(started + self.plan['bounds']['perArchiveNetworkSeconds'])
        path = self.attempt / 'downloads' / artifact['filename']
        record = dict(url=artifact['url'], expectedBytes=artifact['bytes'], bytes=0, attempts=1,
                      redirectsAllowed=False, tlsVerification=True, proxyOrAuthentication='NONE', error=None)
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
            request = urllib.request.Request(artifact['url'], headers={
                'User-Agent':'NBDP-isolated-SDK-byte-restoration/1', 'Accept-Encoding':'identity'})
            with opener.open(request, timeout=self.plan['bounds']['socketTimeoutSeconds']) as response:
                need(response.status == 200 and response.geturl() == artifact['url'], 'EXACT_HTTPS200_URL_REQUIRED')
                record['httpStatus'] = response.status
                length = response.headers.get('Content-Length')
                need(length is not None and length.isdecimal() and int(length) == artifact['bytes'], 'EXACT_CONTENT_LENGTH_REQUIRED')
                need(response.headers.get('Content-Encoding') in (None,'identity'), 'IDENTITY_TRANSFER_REQUIRED')
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                sha1, sha256 = hashlib.sha1(), hashlib.sha256()
                try:
                    while True:
                        self.check()
                        block = response.read(min(CHUNK, artifact['bytes'] + 1 - record['bytes']))
                        if not block: break
                        need(record['bytes'] + len(block) <= artifact['bytes'], 'DOWNLOAD_SIZE_OVERFLOW')
                        self.write(fd, block); record['bytes'] += len(block); sha1.update(block); sha256.update(block)
                    need(record['bytes'] == artifact['bytes'], 'DOWNLOAD_SIZE_MISMATCH')
                    need(sha1.hexdigest() == artifact['sha1'], 'OFFICIAL_ARCHIVE_SHA1_MISMATCH')
                    if artifact.get('sha256') is not None:
                        need(sha256.hexdigest() == artifact['sha256'], 'PINNED_ARCHIVE_SHA256_MISMATCH')
                    os.fsync(fd)
                    record.update(sha1=sha1.hexdigest(), sha256=sha256.hexdigest(), verified=True)
                finally: os.close(fd)
        except BaseException as error:
            record['error'] = type(error).__name__ + ':' + str(error)[:2048]
            raise
        finally:
            record['elapsedSeconds'] = time.monotonic() - started
            record['partialFilePreserved'] = path.exists()
            try:
                if record['error'] is None: self.deadline.arm(self.deadline.end)
                else: self.deadline.failure_receipt()
                self.receipt(artifact['id'] + '-download.json', record)
            except BaseException as receipt_error:
                if record['error'] is None: raise
                # A failed receipt never replaces the original network fault.
                print(json.dumps(dict(firstError=record['error'],receiptError=str(receipt_error)[:2048])),flush=True)
        return path

    def zip_entries(self, path, selected):
        """Validate the complete ZIP metadata/local extents before file extraction."""
        # Bound central-directory allocation BEFORE ZipFile parses it. These
        # fixed archives fit classic single-disk ZIP; ZIP64 is not adopted here.
        with path.open('rb') as source:
            source.seek(0,os.SEEK_END);length=source.tell()
            tail_size=min(length,65557);source.seek(length-tail_size);tail=source.read(tail_size)
            at=tail.rfind(b'PK\x05\x06')
            need(at>=0 and len(tail)-at>=22,'ZIP_EOCD_REQUIRED')
            _,disk,start_disk,disk_count,total_count,central_size,central_offset,comment_size=struct.unpack('<4s4H2IH',tail[at:at+22])
            eocd=length-tail_size+at
            need(at+22+comment_size==len(tail) and disk==start_disk==0 and disk_count==total_count and
                 0<total_count<=self.plan['bounds']['maximumZipEntries'] and total_count!=65535,'CLASSIC_SINGLE_DISK_ZIP_REQUIRED')
            need(0<central_size<=self.plan['bounds']['maximumCentralDirectoryBytes'] and
                 central_offset+central_size==eocd,'BOUNDED_CENTRAL_DIRECTORY_REQUIRED')
            if eocd>=20:
                source.seek(eocd-20);need(source.read(4)!=b'PK\x06\x07','ZIP64_NOT_ADOPTED')
        archive = zipfile.ZipFile(path)
        try:
            entries = archive.infolist(); names = set(); files = {}; ranges = []
            need(len(entries)==total_count and archive.start_dir==central_offset, 'ZIP_ENTRY_COUNT_OR_CENTRAL_OFFSET_MISMATCH')
            expected_dirs = set()
            for name in selected:
                p = PurePosixPath(name)
                expected_dirs.update(str(parent) for parent in p.parents if str(parent) != '.')
            with path.open('rb') as source:
                for info in entries:
                    self.check()
                    name = canonical(info.filename, info.is_dir())
                    need(info.filename == info.orig_filename and name not in names, 'DUPLICATE_OR_TRUNCATED_MEMBER_NAME')
                    names.add(name)
                    mode = info.external_attr >> 16; kind = stat.S_IFMT(mode)
                    need(not (mode & 0o7000) and kind in (0, stat.S_IFREG, stat.S_IFDIR), 'LINK_SPECIAL_OR_PRIVILEGED_ZIP_MEMBER')
                    need(info.flag_bits & ~0x808 == 0 and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), 'ZIP_FLAGS_OR_METHOD_REFUSED')
                    if info.is_dir():
                        need(kind in (0,stat.S_IFDIR) and name in expected_dirs and info.file_size == info.compress_size == 0, 'UNEXPECTED_DIRECTORY_MEMBER')
                    else:
                        need(kind in (0,stat.S_IFREG) and name in selected, 'UNSELECTED_REGULAR_ZIP_MEMBER')
                        need(info.file_size == selected[name]['size'], 'SELECTED_MEMBER_SIZE_MISMATCH')
                        files[name] = info
                    need(0 <= info.header_offset < archive.start_dir and info.compress_size < 2**32 and info.file_size < 2**32, 'ZIP_LOCAL_EXTENT_BOUND')
                    source.seek(info.header_offset); raw = source.read(30)
                    need(len(raw) == 30, 'TRUNCATED_LOCAL_HEADER')
                    magic,_,flags,method,_,_,crc,compressed,size,nlen,xlen = struct.unpack('<4s5H3I2H',raw)
                    local = source.read(nlen).decode('utf-8' if flags & 0x800 else 'cp437','strict')
                    need(magic == b'PK\x03\x04' and local == info.filename and flags == info.flag_bits and method == info.compress_type, 'LOCAL_CENTRAL_HEADER_MISMATCH')
                    end = info.header_offset + 30 + nlen + xlen + info.compress_size
                    if flags & 8:
                        need((crc,compressed,size) in ((0,0,0),(info.CRC,info.compress_size,info.file_size)), 'LOCAL_DESCRIPTOR_FIELDS_MISMATCH')
                        source.seek(end); descriptor = source.read(16)
                        if descriptor[:4] == b'PK\x07\x08':
                            need(len(descriptor) == 16, 'TRUNCATED_DATA_DESCRIPTOR')
                            values = struct.unpack('<3I',descriptor[4:]); end += 16
                        else:
                            need(len(descriptor) >= 12, 'TRUNCATED_DATA_DESCRIPTOR')
                            values = struct.unpack('<3I',descriptor[:12]); end += 12
                        need(values == (info.CRC,info.compress_size,info.file_size), 'DATA_DESCRIPTOR_MISMATCH')
                    else: need((crc,compressed,size) == (info.CRC,info.compress_size,info.file_size), 'LOCAL_CRC_SIZE_MISMATCH')
                    need(end <= archive.start_dir, 'LOCAL_PAYLOAD_OVERLAPS_CENTRAL_DIRECTORY')
                    ranges.append((info.header_offset,end))
            ranges.sort()
            need(all(a[1] <= b[0] for a,b in zip(ranges,ranges[1:])), 'OVERLAPPING_ZIP_LOCAL_ENTRIES')
            need(set(files) == set(selected), 'MISSING_SELECTED_ZIP_MEMBERS')
            return archive, files
        except BaseException:
            archive.close(); raise

    def extract(self, artifact, path, expected):
        selected = {row['archiveMember']:row for row in expected}
        archive, entries = self.zip_entries(path, selected)
        verified = []
        with archive:
            for name,row in selected.items():
                self.check(); relative = PurePosixPath(row['sdkPath'])
                parent = directory(self.stage.joinpath(*relative.parts[:-1]), create=True)
                try:
                    fd = os.open(relative.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                    try:
                        count=0; digest=hashlib.sha256()
                        with archive.open(entries[name]) as source:
                            while block := source.read(CHUNK):
                                need(count + len(block) <= row['size'], 'EXTRACTED_MEMBER_OVERFLOW')
                                self.write(fd,block); count += len(block); digest.update(block)
                        # ZipExtFile verifies CRC when the complete member is read.
                        need(count == row['size'] and digest.hexdigest() == row['sha256'], 'EXTRACTED_MEMBER_HASH_OR_LENGTH_MISMATCH')
                        os.fchmod(fd,int(row['mode'],8)); os.fsync(fd)
                        verified.append(dict(path=row['sdkPath'],size=count,mode=row['mode'],sha256=digest.hexdigest(),zipCrcVerified=True))
                    finally: os.close(fd)
                finally: os.close(parent)
        self.receipt(artifact['id']+'-extraction.json',dict(selectedCount=len(verified),files=verified))

    def inventory(self):
        rows=[]; visits=0
        def walk(fd, prefix=''):
            nonlocal visits
            with os.scandir(fd) as listing:
                names=sorted(entry.name for entry in listing)
            for name in names:
                self.check(); visits += 1
                need(visits <= self.plan['bounds']['maximumTreeEntries'], 'SDK_TREE_VISIT_BOUND')
                relative=prefix+name; st=os.stat(name,dir_fd=fd,follow_symlinks=False)
                if stat.S_ISDIR(st.st_mode):
                    child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                    try: walk(child,relative+'/')
                    finally: os.close(child)
                else:
                    need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, 'SDK_LINK_OR_SPECIAL_REFUSED')
                    filefd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
                    with os.fdopen(filefd,'rb') as source:
                        before=os.fstat(source.fileno());count=0;digest=hashlib.sha256()
                        while block:=source.read(CHUNK): self.check();count+=len(block);digest.update(block)
                        after=os.fstat(source.fileno())
                    identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
                    need(identity(before)==identity(after) and count==st.st_size,'SDK_FILE_CHANGED_DURING_HASH')
                    rows.append(dict(path=relative,size=count,mode=oct(stat.S_IMODE(st.st_mode)),sha256=digest.hexdigest()))
        walk(self.stage_fd)
        return sorted(rows,key=lambda row:row['path'])

    def publish(self):
        self.check()
        libc=ctypes.CDLL(None,use_errno=True)
        rename=libc.renameat2
        rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
        rename.restype=ctypes.c_int
        # The C call can complete before Python observes an interrupt. Until a
        # definite return is observed, neither absence nor placement is known.
        self.placement_state='UNKNOWN'
        result=rename(self.attempt_fd,b'stage-sdk',self.parent_fd,b'sdk',1)
        if result==0:
            # Record success before ANY post-rename operation can fail.
            self.placement_state='PLACED'
        elif result==-1:
            code=ctypes.get_errno()
            # These refusal results establish only that this invocation did not
            # place the stage. They never establish destination absence. I/O,
            # interruption and unrecognized results remain conservatively UNKNOWN.
            if code in (errno.EEXIST,errno.ENOTEMPTY,errno.ENOENT,errno.EXDEV,
                        errno.EACCES,errno.EPERM,errno.ENOTDIR,errno.ELOOP,
                        errno.EROFS,errno.ENOSYS,errno.EINVAL):
                self.placement_state='NOT_PLACED'
            self.rename_errno=code
        self.rename_return=result
        need(result==0,'ATOMIC_NOREPLACE_SDK_PLACEMENT_FAILED:'+str(self.rename_errno))
        finalfd=os.open('sdk',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=self.parent_fd)
        try:
            a,b=os.fstat(self.stage_fd),os.fstat(finalfd)
            need((a.st_dev,a.st_ino)==(b.st_dev,b.st_ino),'PLACED_DIRECTORY_IDENTITY_MISMATCH')
        finally:os.close(finalfd)
        os.fsync(self.parent_fd);self.check()

    def placement(self):
        placed=True if self.placement_state=='PLACED' else (
            False if self.placement_state in ('NOT_ATTEMPTED','NOT_PLACED') else None)
        return dict(placed=placed,placementState=self.placement_state,
            renameReportedReturn=self.rename_return,renameReportedErrno=self.rename_errno,
            placementMeaning='This attempt only; false never means destination absent. UNKNOWN/null preserves interrupted or ambiguous rename boundaries. No foreign destination is removed or overwritten.')

    def run(self, original):
        error=None
        try:
            self.initialize()
            for artifact in self.plan['archives']:
                path=self.download(artifact)
                selected=[row for row in self.plan['selected'] if row['archiveId']==artifact['id']]
                self.extract(artifact,path,selected)
            need(self.remaining==0,'PLANNED_BYTES_NOT_COMPLETE')
            observed=self.inventory()
            by_path={row['path']:row for row in observed}
            need(set(by_path)=={row['path'] for row in original['files']},'EXACT_SDK434_PATH_SET_MISMATCH')
            # The preserved index uses pathlib traversal ordering, which differs
            # from string ordering (e.g. qemu/... versus qemu-img). Reproduce its
            # exact original row order for its historical aggregate only.
            actual=[by_path[row['path']] for row in original['files']]
            need(actual==original['files'],'EXACT_SDK434_TREE_MISMATCH')
            aggregate=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            need(aggregate==original['sha256'],'ORIGINAL_SDK_AGGREGATE_MISMATCH')
            self.receipt('staged-tree.json',dict(root=str(self.stage),sha256=aggregate,files=actual))
            self.publish()
            # stage_fd still identifies the same directory after atomic rename.
            need(self.inventory()==observed,'POST_PLACEMENT_SDK_TREE_MISMATCH')
            need(hash_file(INVENTORY)['sha256']==INVENTORY_SHA,'ORIGINAL_INDEX_CHANGED')
            self.receipt('result.json',dict(state='EXACT_BYTE_DATA_RESTORED_PENDING_INDEPENDENT_REVIEW',
                destination=str(DEST),fileCount=len(actual),bytes=sum(row['size'] for row in actual),aggregate=aggregate,
                **self.placement(),sdkToolsExecuted=False,sdkmanagerOrLicenseConsent=False,serviceOrExperimentExecuted=False,
                diskSamples=self.disk_samples,minimumSampledFree=self.lowest_free,modeMeaning='Original public file modes only; directory modes are private restoration directories.'))
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc)[:2048]
            # Preserve stage/partial downloads and first fault; never remove or
            # overwrite a previously existing destination on failure.
            if self.attempt_fd is not None:
                try:
                    self.deadline.failure_receipt()
                    self.receipt('failure.json',dict(error=error,**self.placement(),remainingPlannedBytes=self.remaining,
                        partialDataPreserved=True,sdkToolsExecuted=False,minimumSampledFree=self.lowest_free))
                except BaseException as secondary:print(json.dumps(dict(firstError=error,receiptError=str(secondary)[:2048])),flush=True)
            raise
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            for fd in (self.stage_fd,self.attempt_fd,self.parent_fd):
                if fd is not None:os.close(fd)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True);parser.add_argument('--plan-sha',required=True)
    parser.add_argument('--execute-reviewed-data-restoration',action='store_true',required=True)
    args=parser.parse_args()
    need(Path(args.plan)==WORK/'plan.json','EXACT_PLAN_PATH_REQUIRED')
    need(hash_file(Path(args.plan))['sha256']==args.plan_sha,'REVIEWED_PLAN_HASH_MISMATCH')
    plan=json.loads(Path(args.plan).read_bytes())
    need(plan['schema']=='nbdp-sdk434-byte-restoration-plan-v1' and plan['scope']=='BYTE_DATA_ONLY_NO_TOOLS_OR_EXPERIMENT','RESTORATION_SCOPE')
    need(plan['inventory']['path']==str(INVENTORY) and plan['inventory']['sha256']==INVENTORY_SHA,'ORIGINAL_INDEX_PIN')
    need(hash_file(INVENTORY)==plan['inventory'],'ORIGINAL_INDEX_BYTES_HASH_MISMATCH')
    original=json.loads(INVENTORY.read_bytes())
    need(original['root']==str(DEST) and len(original['files'])==434,'ORIGINAL_SDK434_INDEX')
    expected={row['path']:row for row in original['files']}
    selected=plan['selected']
    need(len(selected)==434 and {row['sdkPath'] for row in selected}==set(expected),'EXACT_SELECTED434_MEMBERSHIP')
    archives={row['id']:row for row in plan['archives']}
    need(len(archives)==3,'EXACT_THREE_ARCHIVES')
    pairs=set()
    for row in selected:
        need(row['archiveId'] in archives,'KNOWN_ARCHIVE')
        canonical(row['sdkPath']);canonical(row['archiveMember'])
        need((row['archiveId'],row['archiveMember']) not in pairs,'DUPLICATE_SELECTED_MEMBER')
        pairs.add((row['archiveId'],row['archiveMember']))
        need({key:row[key] for key in ('size','mode','sha256')}=={key:expected[row['sdkPath']][key] for key in ('size','mode','sha256')},'SELECTED_ORIGINAL_ROW_MISMATCH')
        need(row['mode'] in ('0o664','0o755','0o644'),'CLOSED_ORIGINAL_PUBLIC_MODES')
    need(plan['totals']['archiveBytes']==sum(row['bytes'] for row in archives.values()) and
         plan['totals']['selectedBytes']==sum(row['size'] for row in selected),'TOTAL_BYTE_BOUNDS')
    for artifact in archives.values():
        need(artifact['url'].startswith('https://dl.google.com/android/repository/') and
             artifact['url'].endswith('/'+artifact['filename']) and '/' not in artifact['filename'],'EXACT_OFFICIAL_ARCHIVE_URL')
    need(plan['attemptDirectory']=='attempt-r1','EXACT_FRESH_ATTEMPT_DIRECTORY')
    Restore(plan).run(original)


if __name__=='__main__':main()
