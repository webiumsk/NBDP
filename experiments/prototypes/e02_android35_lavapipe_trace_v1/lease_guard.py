"""SOURCE PREPARATION: immutable one-use E02 lease; no services on import.

UTC, MONOTONIC and BOOTTIME deadlines include setup and cannot be renewed. A
process-local observation gap or clock rollback revokes. No shared clock lock is
held across a child. Cleanup cannot run while the host itself cannot execute.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time

NS = 1000000000
SCHEMA = 'e02-single-cell-lease-v1'
KEYS = {'schema', 'runId', 'issuedUtcNs', 'deadlineUtcNs', 'issuedMonoNs',
        'deadlineMonoNs', 'issuedBootNs', 'deadlineBootNs', 'bootId'}
PACKAGE = 'com.vitorpamplona.amethyst.debug'
HELPER = 'org.nbdp.clipboard.capture'
ADB = '/sdk/platform-tools/adb'
ENV = {'PATH': '/sdk/emulator:/sdk/platform-tools:/usr/local/bin:/usr/bin:/bin',
       'LANG': 'C.UTF-8', 'HOME': '/state/home', 'ANDROID_HOME': '/sdk',
       'ANDROID_SDK_ROOT': '/sdk', 'ANDROID_USER_HOME': '/state/android',
       'ANDROID_AVD_HOME': '/state/avd', 'TMPDIR': '/tmp',
       'PYTHONHOME': '/guard-python', 'OPENSSL_CONF': '/dev/null',
       'OPENSSL_MODULES': '/guard-python/lib/openssl-modules-disabled'}


class LeaseDenied(RuntimeError):
    pass


def strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise LeaseDenied('duplicate metadata key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(LeaseDenied('nonfinite metadata')))


def sample():
    """Fresh proc identity/offset checks, then a clock-only coherent bracket.

    Metadata stability assumes the reviewed paths, dropped capabilities and no
    privileged host/setns adversary; this is not hostile-host time attestation.
    Proc I/O delay is charged by subsequent fresh clocks and original lease checks.
    """
    # A scheduling interruption may invalidate one bracket, never its deadline.
    # Discard that entire attempt; no metadata or clock values are reused.
    for _ in range(3):
        boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        offsets = [line.split() for line in Path('/proc/self/timens_offsets').read_text().splitlines()]
        if offsets != [['monotonic', '0', '0'], ['boottime', '0', '0']]:
            raise LeaseDenied('nonzero or unknown time namespace offsets')
        before_mono = time.monotonic_ns()
        before = time.time_ns()
        result = {'Utc': time.time_ns(), 'Mono': time.monotonic_ns(),
                  'Boot': time.clock_gettime_ns(time.CLOCK_BOOTTIME), 'bootId': boot_id}
        after, after_mono = time.time_ns(), time.monotonic_ns()
        if not before <= result['Utc'] <= after or not before_mono <= result['Mono'] <= after_mono:
            raise LeaseDenied('clock sample bracket rollback')
        # UTC changes cannot hide a scheduling stall in the monotonic bracket.
        if after - before <= 50_000_000 and after_mono - before_mono <= 50_000_000:
            return result
    raise LeaseDenied('interrupted clock sample after 3 attempts')


def issue(run_id, seconds, clock=sample):
    if not re.fullmatch('[0-9a-f]{32}', run_id) or type(seconds) is not int or not 60 <= seconds <= 1800:
        raise LeaseDenied('one bounded reviewed lease required')
    now = clock()
    value = {'schema': SCHEMA, 'runId': run_id, 'bootId': now['bootId']}
    for kind in ('Utc', 'Mono', 'Boot'):
        value['issued' + kind + 'Ns'] = now[kind]
        value['deadline' + kind + 'Ns'] = now[kind] + seconds * NS
    return value


# Exact optional scripts are immutable argv operands, never format strings.
PRESSURE_READS = {
    'pressure-cpu': 'if [ -r /proc/pressure/cpu ]; then cat /proc/pressure/cpu; nbdp_read_exit=$?; if [ "$nbdp_read_exit" -ne 0 ]; then echo NBDP_OPTIONAL_READ_FAILED:$nbdp_read_exit; fi; else echo NBDP_OPTIONAL_UNAVAILABLE; fi',
    'pressure-memory': 'if [ -r /proc/pressure/memory ]; then cat /proc/pressure/memory; nbdp_read_exit=$?; if [ "$nbdp_read_exit" -ne 0 ]; then echo NBDP_OPTIONAL_READ_FAILED:$nbdp_read_exit; fi; else echo NBDP_OPTIONAL_UNAVAILABLE; fi',
    'pressure-io': 'if [ -r /proc/pressure/io ]; then cat /proc/pressure/io; nbdp_read_exit=$?; if [ "$nbdp_read_exit" -ne 0 ]; then echo NBDP_OPTIONAL_READ_FAILED:$nbdp_read_exit; fi; else echo NBDP_OPTIONAL_UNAVAILABLE; fi',
}
# Fixed read-only trace operations; no paths/flags/scripts are caller supplied.
EARLY_BOOT_READS = (
    ('uptime', ('shell', 'cat', '/proc/uptime'), False),
    ('logcat-events', ('shell', 'logcat', '-b', 'events', '-d', '-v', 'epoch'), False),
    ('logcat-system', ('shell', 'logcat', '-b', 'system', '-d', '-v', 'epoch'), False),
)
HEALTH_READS = (
    ('logcat-events', ('shell', 'logcat', '-b', 'events', '-d', '-v', 'epoch'), False),
    ('logcat-system', ('shell', 'logcat', '-b', 'system', '-d', '-v', 'epoch'), False),
    ('uptime', ('shell', 'cat', '/proc/uptime'), False),
    ('lastanr', ('shell', 'dumpsys', '-t', '5', 'activity', 'lastanr'), False),
    ('lastanr-traces', ('shell', 'dumpsys', '-t', '5', 'activity', 'lastanr-traces'), False),
    ('dropbox-system-app-anr', ('shell', 'dumpsys', '-t', '5', 'dropbox', '--print', 'system_app_anr'), False),
    ('processes', ('shell', 'ps', '-A', '-o', 'PID,NAME'), False),
    ('cpuinfo', ('shell', 'dumpsys', '-t', '5', 'cpuinfo'), False),
    ('meminfo', ('shell', 'cat', '/proc/meminfo'), False),
    ('pressure-cpu', ('shell', PRESSURE_READS['pressure-cpu']), True),
    ('pressure-memory', ('shell', PRESSURE_READS['pressure-memory']), True),
    ('pressure-io', ('shell', PRESSURE_READS['pressure-io']), True),
)
HEALTH_UI = (('shell', 'uiautomator', 'dump', '/sdcard/nbdp-window.xml'),
             ('shell', 'cat', '/sdcard/nbdp-window.xml'), ('exec-out', 'screencap', '-p'))
RENDERER_READS = (
    ('renderer-logcat-main', ('shell', 'logcat', '-b', 'main', '-d', '-v', 'epoch'), False),
    ('renderer-surfaceflinger', ('shell', 'dumpsys', '-t', '5', 'SurfaceFlinger'), False),
)
EMULATOR_SERVICE = ('/sdk/emulator/emulator', '-avd', 'ordinary', '-ports', '5554,5555',
    '-no-window', '-no-snapshot', '-wipe-data', '-no-audio', '-camera-back',
    'none', '-camera-front', 'none', '-gpu', 'lavapipe', '-memory', '4096',
    '-cores', '4', '-no-boot-anim', '-no-metrics', '-netdelay', 'none',
    '-netspeed', 'full', '-accel', 'on')
EMULATOR_STREAMS = (('emulator.stdout', 8388608), ('emulator.stderr', 262144))


def allowed_adb(args):
    """Boot-trace-only argv: no install, activity intent, input or helper."""
    if type(args) is not list or not all(type(x) is str for x in args):
        return False
    exact = [('wait-for-device',), *HEALTH_UI,
             *(row[1] for row in HEALTH_READS), *(row[1] for row in EARLY_BOOT_READS),
             *(row[1] for row in RENDERER_READS)]
    if tuple(args) in exact:
        return True
    return len(args) == 3 and args[:2] == ['shell', 'getprop'] and args[2] in (
        'sys.boot_completed', 'ro.build.fingerprint', 'ro.build.version.sdk')


def adb_timeout(args):
    """Only the original boot wait has180s; diagnostic children remain10s."""
    return 180 if args == ['wait-for-device'] else 10


def health_cgroup(lease):
    """Optional snapshot of this private container cgroup, never a host path.

    Docker admission separately requires actual CgroupnsMode=private and no
    CgroupParent. No arbitrary path is accepted. Missing/denied optional data is
    UNKNOWN; original lease failures always propagate instead of being caught.
    Values describe the whole Android container, including emulator/guard/ADB,
    not one emulator process or a maximum/peak consumption measurement.
    """
    started = time.monotonic_ns()
    result = {'schema': 'e02-private-cgroup-diagnostic-v1',
              'measuredProcessScope': 'Entire owned Android Docker container cgroup',
              'status': 'UNKNOWN', 'startedMonotonicNs': started, 'files': {}}
    def read_fixed(path, bound=65536):
        lease.check()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            chunks = bytearray()
            while len(chunks) <= bound:
                lease.check()
                block = os.read(fd, min(8192, bound + 1 - len(chunks)))
                if not block:
                    break
                chunks.extend(block)
            raw = bytes(chunks)
        finally:
            os.close(fd)
        lease.check()
        if len(raw) > bound:
            raise OSError('Optional cgroup snapshot bound exceeded')
        return raw.decode('utf-8', 'strict')
    try:
        own = read_fixed('/proc/self/cgroup')
        mountinfo = read_fixed('/proc/self/mountinfo')
        matching = []
        for line in mountinfo.splitlines():
            words = line.split()
            if len(words) >= 10 and words[4] == '/sys/fs/cgroup':
                sep = words.index('-')
                if words[3] == '/' and words[sep + 1] == 'cgroup2' and 'ro' in words[5].split(','):
                    matching.append(line)
                else:
                    raise OSError('Optional cgroup mount is not private read-only root cgroup2')
        if own != '0::/\n' or len(matching) != 1:
            raise OSError('Optional private cgroup2 root not established')
        result.update(status='VALIDATED_PRIVATE_ROOT', selfCgroup=own, mountinfo=matching[0])
        for name in ('cpu.stat', 'memory.events', 'memory.current'):
            try:
                text = read_fixed('/sys/fs/cgroup/' + name)
                result['files'][name] = {'status': 'CAPTURED', 'raw': text}
            except (OSError, UnicodeError) as exc:
                result['files'][name] = {'status': 'UNKNOWN', 'error': type(exc).__name__ + ': ' + str(exc)[:512]}
        result['status'] = 'CAPTURED' if all(v['status'] == 'CAPTURED' for v in result['files'].values()) else 'UNKNOWN_PARTIAL'
    except (OSError, UnicodeError, ValueError) as exc:
        result['status'] = 'UNKNOWN'
        result['error'] = type(exc).__name__ + ': ' + str(exc)[:512]
    lease.check()
    result['endedMonotonicNs'] = time.monotonic_ns()
    return result


class _EmulatorCapture:
    """Private fixed live spool. No caller path or increased capture budget.

    This disposable local filesystem is not hostile-host attestation. Writes
    retain the acquired prefix even during owned cancellation after revocation.
    Each chunk is fsynced before continuing; hard realtime is not guaranteed.
    """
    def __init__(self):
        self.fds = {}; self.written = {'stdout': 0, 'stderr': 0}
        session = directory = None; failure = None
        try:
            session = os.open('/session', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            directory = os.open('fixtures', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=session)
            info = os.fstat(directory)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                raise LeaseDenied('Private emulator spool directory required')
            for name, _ in EMULATOR_STREAMS:
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
                self.fds[name.split('.')[1]] = fd
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                    raise LeaseDenied('Exclusive private regular emulator spool required')
        except BaseException as exc:
            failure = exc
        finally:
            for fd in (directory, session):
                if fd is not None:
                    try: os.close(fd)
                    except OSError as exc:
                        if failure is None: failure = exc
        if failure is not None:
            for fd in self.fds.values():
                try: os.close(fd)
                except OSError: pass
            self.fds.clear()
            raise failure

    def write(self, stream, raw):
        if type(stream) is not str or stream not in self.fds or type(raw) is not bytes:
            raise LeaseDenied('Closed emulator spool stream required')
        bound = 8388608 if stream == 'stdout' else 262144
        if len(raw) + self.written[stream] > bound:
            raise LeaseDenied('Fixed emulator spool bound exceeded')
        offset = 0
        while offset < len(raw):
            count = os.write(self.fds[stream], raw[offset:])
            if count <= 0: raise OSError('Emulator spool short write')
            offset += count; self.written[stream] += count
        os.fsync(self.fds[stream])

    def close(self):
        errors = []
        for stream, fd in list(self.fds.items()):
            try: os.close(fd)
            except OSError as exc: errors.append(stream + ': ' + repr(exc))
        self.fds.clear()
        if errors: raise OSError('Emulator spool close: ' + repr(errors))


class Lease:
    def __init__(self, path, expected_sha, control, clock=sample):
        self.path, self.expected_sha, self.control = Path(path), expected_sha, Path(control)
        self.clock, self.previous, self.revoked = clock, None, False

    def revoke(self, reason):
        self.revoked = True
        try:
            fd = os.open(self.control / 'REVOKED', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as out: out.write((str(reason)[:2048] + '\n').encode()); out.flush(); os.fsync(out.fileno())
        except FileExistsError: pass
        raise LeaseDenied(str(reason))

    def check(self):
        if self.revoked or os.path.lexists(self.control / 'REVOKED'): self.revoke('sticky revocation')
        try:
            raw = self.path.read_bytes()
            if len(raw) > 8192 or hashlib.sha256(raw).hexdigest() != self.expected_sha or self.path.is_symlink(): raise LeaseDenied('original lease drift')
            p = strict(raw)
            if type(p) is not dict or set(p) != KEYS or p['schema'] != SCHEMA or not re.fullmatch('[0-9a-f]{32}', p['runId']): raise LeaseDenied('closed lease metadata')
            budget = p['deadlineBootNs'] - p['issuedBootNs']
            if type(budget) is not int or not 60 * NS <= budget <= 1800 * NS: raise LeaseDenied('lease budget')
            now = self.clock()
            if now['bootId'] != p['bootId']: raise LeaseDenied('boot identity changed')
            for kind in ('Utc', 'Mono', 'Boot'):
                initial, end = p['issued' + kind + 'Ns'], p['deadline' + kind + 'Ns']
                if type(initial) is not int or type(end) is not int or end - initial != budget or not initial <= now[kind] < end: raise LeaseDenied('original deadline/clock refused')
                if self.previous and now[kind] < self.previous[kind]: raise LeaseDenied('clock rollback')
            if abs((now['Utc'] - p['issuedUtcNs']) - (now['Boot'] - p['issuedBootNs'])) > 500_000_000: raise LeaseDenied('UTC/boottime drift')
            if self.previous and now['Boot'] - self.previous['Boot'] > 15 * NS: raise LeaseDenied('unobserved resumption gap')
            self.previous = now
            return now
        except (LeaseDenied, OSError, ValueError, KeyError, TypeError) as exc: self.revoke(exc)

    def sleep(self, seconds):
        if type(seconds) not in (float, int) or not 0 <= seconds <= 30: self.revoke('bounded sleep required')
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.check(); time.sleep(min(.1, max(0, end - time.monotonic())))
        self.check()

    def dispatch(self, action):
        self.check()
        result = action()
        self.check()
        return result

    def run_checked(self, argv, timeout, env, cwd=None, *, emulator_capture=False):
        """Popen remains unreaped until all possible owned group signals end."""
        if type(timeout) not in (int, float) or not 0 < timeout <= 1800: self.revoke('finite command timeout required')
        self.last_result = None
        if type(emulator_capture) is not bool or (emulator_capture and (type(argv) is not list or tuple(argv) != EMULATOR_SERVICE or cwd is not None)):
            self.revoke('Fixed emulator service capture only')
        def execute():
            p = None; held = False; selector = selectors.DefaultSelector(); capture = None
            output = {'stdout': bytearray(), 'stderr': bytearray()}; total = dict(stdout=0, stderr=0)
            eof = {'stdout': False, 'stderr': False}
            record = {'argv': argv, 'launchAttempt': False, 'pid': None, 'exit': None,
                      'reaped': False, 'forced': False, 'timedOut': False, 'error': None}
            deadline = time.monotonic() + timeout
            def observe():
                if not held or p.returncode is not None: raise LeaseDenied('owned process identity lost')
                return os.waitid(os.P_PID, p.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            def pump(wait):
                for key, _ in selector.select(wait):
                    data = os.read(key.fd, 65536)
                    if not data: eof[key.data] = True; selector.unregister(key.fileobj); continue
                    name = key.data; total[name] += len(data)
                    bound = 8 * 1024 * 1024 if name == 'stdout' else 262144
                    prefix = data[:max(0, bound - len(output[name]))]
                    output[name].extend(prefix)
                    if capture is not None: capture.write(name, prefix)
                    if total[name] > bound: raise LeaseDenied('bounded command capture exceeded')
            try:
                self.check(); record['launchAttempt'] = True
                if emulator_capture: capture = _EmulatorCapture()
                p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, bufsize=0)
                held = True; record['pid'] = p.pid
                for name in output:
                    stream = getattr(p, name); os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, name)
                while True:
                    self.check()
                    if time.monotonic() >= deadline: record['timedOut'] = True; raise LeaseDenied('command deadline')
                    exited = observe()
                    if exited is not None and not selector.get_map(): break
                    pump(.1)
            except BaseException as exc:
                record['error'] = type(exc).__name__ + ': ' + str(exc)[:2048]
                # Persist refusal BEFORE cancellation; a later queued dispatch
                # cannot run even if this child failure was caught by caller.
                try: self.revoke('owned command failed: ' + record['error'])
                except BaseException: pass
            finally:
                if p is not None and held:
                    try:
                        if record['error']:
                            observe()
                            try: os.killpg(p.pid, signal.SIGTERM); record['forced'] = True
                            except ProcessLookupError: pass
                            end = time.monotonic() + 2
                            while time.monotonic() < end:
                                if observe() is not None and not selector.get_map(): break
                                try: pump(.1)
                                except BaseException: break
                            # Leader is still retained WNOWAIT, even if exited.
                            observe()
                            try: os.killpg(p.pid, signal.SIGKILL); record['forced'] = True
                            except ProcessLookupError: pass
                            end = time.monotonic() + 1
                            while selector.get_map() and time.monotonic() < end:
                                try: pump(.05)
                                except BaseException: break
                        record['exit'] = p.wait(timeout=3); held = False; record['reaped'] = True
                    except BaseException as exc:
                        record['error'] = record['error'] or ('cleanup: ' + repr(exc))
                selector.close()
                if p is not None:
                    for name in output:
                        try: getattr(p, name).close()
                        except OSError: pass
                if capture is not None:
                    try: capture.close()
                    except BaseException as exc:
                        if record['error'] is None: record['error'] = 'capture close: ' + repr(exc)
                        else: record['captureSecondaryErrors'] = ['capture close: ' + repr(exc)]
            record.update(stdout=bytes(output['stdout']), stderr=bytes(output['stderr']), observedBytes=total,
                          stdoutEOF=eof['stdout'], stderrEOF=eof['stderr'])
            self.last_result = record
            if record['error'] or record['exit'] != 0 or not record['reaped'] or record['forced']:
                self.revoke(record['error'] or 'owned command exited unsuccessfully')
            return record
        return self.dispatch(execute)


def main(argv):
    if len(argv) < 3: raise LeaseDenied('check SHA or exec SHA adb TOKENS')
    mode, expected = argv[1:3]
    lease = Lease('/session/lease.json', expected, '/session/control')
    if mode == 'check' and len(argv) == 3: lease.check(); return 0
    if mode != 'exec' or len(argv) < 5: raise LeaseDenied('fixed in-container action refused')
    kind, args = argv[3], argv[4:]
    if kind == 'diagnostic-cgroup' and args == ['snapshot-v1']:
        value = lease.dispatch(lambda: health_cgroup(lease))
        sys.stdout.buffer.write((json.dumps(value, sort_keys=True) + '\n').encode('utf-8'))
        return 0
    if kind == 'adb' and allowed_adb(args):
        command = [ADB, '-s', 'emulator-5554', *args]
        timeout = adb_timeout(args)
    elif kind == 'probe' and args in (['ss', '-H', '-lnt'], ['ip', '-j', 'addr']):
        command, timeout = ['/usr/bin/' + args[0], *args[1:]], 10
    else: raise LeaseDenied('fixed in-container action refused')
    try:
        result = lease.run_checked(command, timeout, dict(ENV, NBDP_LEASE_SHA256=expected))
    except LeaseDenied:
        result = lease.last_result
        if result is not None:
            sys.stdout.buffer.write(result['stdout']); sys.stderr.buffer.write(result['stderr'])
        raise
    sys.stdout.buffer.write(result['stdout']); sys.stderr.buffer.write(result['stderr'])
    if result['error'] or not result['reaped'] or result['forced']: raise LeaseDenied(result['error'] or 'unqualified owned child')
    return result['exit']


if __name__ == '__main__':
    try: code = main(sys.argv)
    except BaseException as error: sys.stderr.write(type(error).__name__ + ': ' + str(error)[:2048] + '\n'); code = 124
    raise SystemExit(code)
