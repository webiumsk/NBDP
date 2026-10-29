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


def allowed_adb(args):
    """Closed synthetic guest commands; no generic shell/URI/clipboard input."""
    if args in (['wait-for-device'], ['reverse', 'tcp:17777', 'tcp:17777'],
                ['reverse', '--list'], ['install', '--no-streaming', '/artifact.apk'],
                ['install', '-t', '--no-streaming', '/helper.apk'], ['exec-out', 'screencap', '-p']): return True
    if len(args) == 5 and args[:3] == ['exec-out', 'run-as', HELPER] and args[3] == 'cat':
        return re.fullmatch(r'files/captures/[a-z0-9-]{1,48}\.(raw\.json|receipt\.json|clear\.json)', args[4]) is not None
    if not args or args[0] != 'shell': return False
    a = args[1:]
    if a in (['uiautomator', 'dump', '/sdcard/nbdp-window.xml'],
             ['cat', '/sdcard/nbdp-window.xml'], ['date', '-u'],
             ['monkey', '-p', PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1'],
             ['pm', 'clear', HELPER], ['pm', 'clear', PACKAGE],
             ['am', 'start', '-W', '-n', PACKAGE + '/com.vitorpamplona.amethyst.ui.MainActivity']): return True
    if len(a) == 2 and a[0] == 'getprop': return a[1] in ('sys.boot_completed', 'ro.build.fingerprint', 'ro.build.version.sdk')
    if a in (['pm', 'path', PACKAGE], ['pm', 'path', HELPER]): return True
    if len(a) == 8 and a[:7] == ['am', 'start', '-W', '-n', HELPER + '/.CaptureActivity', '--es', 'caseId']:
        return re.fullmatch('[a-z0-9-]{1,48}', a[7]) is not None
    if len(a) < 3 or a[0] != 'input': return False
    op, values = a[1], a[2:]
    if op in ('tap', 'swipe'):
        return len(values) == (2 if op == 'tap' else 5) and all(re.fullmatch('[0-9]{1,4}', x) and int(x) <= 5000 for x in values)
    if op == 'text': return len(values) == 1 and len(values[0]) <= 256 and re.fullmatch('[a-zA-Z0-9:/._-]+', values[0]) is not None
    return op == 'keyevent' and len(values) == 1 and values[0] in ('4', '61', '66', '67', '111')


def adb_timeout(args):
    """Only the exact cold-boot wait and pinned Amethyst install get180s."""
    return 180 if args in (['wait-for-device'], ['install', '--no-streaming', '/artifact.apk']) else 30


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

    def run_checked(self, argv, timeout, env, cwd=None):
        """Popen remains unreaped until all possible owned group signals end."""
        if type(timeout) not in (int, float) or not 0 < timeout <= 1800: self.revoke('finite command timeout required')
        self.last_result = None
        def execute():
            p = None; held = False; selector = selectors.DefaultSelector()
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
                    output[name].extend(data[:max(0, bound - len(output[name]))])
                    if total[name] > bound: raise LeaseDenied('bounded command capture exceeded')
            try:
                self.check(); record['launchAttempt'] = True
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
