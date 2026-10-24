"""Prepared controls: owned Python child/mock filesystem only, never Android.

Source author does not execute these controls. A separate root release follows
independent exact source review. Fixed emulator argv is mapped only in tests to
an owned Python child; this does not prove emulator/backend interoperability.
"""
import ast
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import time
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location('lavapipe_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


guard = load('lease_guard'); supervisor = load('supervisor'); driver = load('android_driver')


class LavapipeTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-lavapipe-pure-') as value:
            root = Path(value); (root / 'fixtures').mkdir(mode=0o700)
            control = root / 'control'; control.mkdir(mode=0o700)
            clock = lambda: {'Utc': 1000000000000, 'Mono': 1000000000000,
                             'Boot': 1000000000000, 'bootId': 'synthetic'}
            raw = json.dumps(guard.issue('a' * 32, 60, clock=clock)).encode()
            (root / 'lease.json').write_bytes(raw)
            lease = guard.Lease(root / 'lease.json', hashlib.sha256(raw).hexdigest(), control, clock)
            real_open = os.open
            def mapped(path, flags, mode=0o777, *, dir_fd=None):
                if path == '/session': path = str(root)
                return real_open(path, flags, mode, dir_fd=dir_fd)
            with patch.object(guard.os, 'open', side_effect=mapped):
                yield root, lease

    @contextmanager
    def python_child(self, script):
        original = guard.subprocess.Popen; children = []
        def popen(argv, **kwargs):
            self.assertEqual(tuple(argv), guard.EMULATOR_SERVICE)
            child = original([sys.executable, '-I', '-B', '-c', script], **kwargs)
            children.append(child)
            return child
        with patch.object(guard.subprocess, 'Popen', side_effect=popen):
            yield children

    def test_api35_is_only_os_fixture_delta_and_old_renderer_resources_unchanged(self):
        old = HERE.parent / 'e02_android_lavapipe_trace_v1'
        tree = ast.parse((old / 'supervisor.py').read_text())
        values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                  if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                  and n.targets[0].id in ('EMULATOR', 'CONFIG', 'LIMITS')}
        expected = list(values['EMULATOR']); expected[expected.index('-gpu') + 1] = 'lavapipe'
        self.assertEqual(supervisor.EMULATOR, expected)
        self.assertEqual(supervisor.CONFIG, values['CONFIG'].replace('android-36', 'android-35'))
        self.assertEqual(supervisor.LIMITS, values['LIMITS'])
        self.assertEqual(tuple(supervisor.EMULATOR), guard.EMULATOR_SERVICE)
        self.assertEqual(supervisor.LIMITS['android'], (8192, 512, 8))
        self.assertIn('hw.cpu.ncore=4\nhw.ramSize=4096\n', supervisor.CONFIG)
        self.assertEqual((driver.EARLY_BUDGET_SECONDS, driver.BUDGET_SECONDS), (30, 180))

    def test_only_literal_emulator_capture_can_open_fixed_spool(self):
        variants = [list(guard.EMULATOR_SERVICE) + ['-verbose'], ['sh', '-c', 'emulator'],
                    [sys.executable, '-c', 'pass']]
        for argv in variants:
            with self.fixture() as (root, lease), patch.object(guard, '_EmulatorCapture') as capture:
                with self.assertRaisesRegex(guard.LeaseDenied, 'Fixed emulator'):
                    lease.run_checked(argv, 1, {}, emulator_capture=True)
                capture.assert_not_called(); self.assertTrue(lease.revoked)
                self.assertFalse((root / 'fixtures/emulator.stdout').exists())
        for invalid in (1, 'true', None):
            with self.fixture() as (_, lease), patch.object(guard, '_EmulatorCapture') as capture:
                with self.assertRaises(guard.LeaseDenied):
                    lease.run_checked(list(guard.EMULATOR_SERVICE), 1, {}, emulator_capture=invalid)
                capture.assert_not_called()

    def test_prefix_is_on_disk_before_owned_child_exits_and_both_streams_survive(self):
        with self.fixture() as (root, lease):
            ack = root / 'owned-test-prefix-observed'
            script = ("import os,time;from pathlib import Path\n"
                      "os.write(1,b'live-out');os.write(2,b'live-err')\n"
                      "end=time.monotonic()+4\n"
                      "while not Path(" + repr(str(ack)) + ").exists() and time.monotonic()<end: time.sleep(.01)\n")
            with self.python_child(script) as children:
                observed = []; real_write = guard._EmulatorCapture.write
                def inspect_prefix(capture, stream, raw):
                    real_write(capture, stream, raw)
                    self.assertEqual((root / 'fixtures' / ('emulator.' + stream)).read_bytes(), raw)
                    observed.append((stream, os.waitid(os.P_PID, children[0].pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)))
                    if {x[0] for x in observed} == {'stdout', 'stderr'}: ack.write_bytes(b'owned-control-only')
                with patch.object(guard._EmulatorCapture, 'write', inspect_prefix):
                    result = lease.run_checked(list(guard.EMULATOR_SERVICE), 5, {}, emulator_capture=True)
                self.assertEqual({x[0] for x in observed}, {'stdout', 'stderr'})
                self.assertTrue(all(x[1] is None for x in observed))
                self.assertEqual(result['stdout'], b'live-out'); self.assertEqual(result['stderr'], b'live-err')
                self.assertEqual(result['exit'], 0); self.assertTrue(result['reaped'])
                self.assertFalse(result['forced']); self.assertIsNone(result['error'])
                for name, _ in guard.EMULATOR_STREAMS:
                    info = (root / 'fixtures' / name).stat()
                    self.assertTrue(stat.S_ISREG(info.st_mode)); self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)

    def test_overflow_preserves_exact_bounded_prefix_and_sticky_owned_cleanup(self):
        for stream, fd, cap in [('stdout', 1, 8388608), ('stderr', 2, 262144)]:
            with self.fixture() as (root, lease), self.python_child(
                'import os,time;os.write(' + str(fd) + ',b"x"*' + str(cap + 1) + ');time.sleep(1)'
            ):
                with self.assertRaises(guard.LeaseDenied):
                    lease.run_checked(list(guard.EMULATOR_SERVICE), 5, {}, emulator_capture=True)
                self.assertEqual((root / 'fixtures' / ('emulator.' + stream)).stat().st_size, cap)
                self.assertIn('bounded command capture exceeded', (root / 'control/REVOKED').read_text())
                self.assertTrue(lease.last_result['reaped']); self.assertTrue(lease.last_result['forced'])
                with self.assertRaisesRegex(guard.LeaseDenied, 'sticky'): lease.check()

    def test_spool_write_fault_preserves_first_error_then_reaps_owned_child(self):
        with self.fixture() as (root, lease), self.python_child("import os,time;os.write(1,b'prefix');time.sleep(1)"):
            with patch.object(guard._EmulatorCapture, 'write', side_effect=OSError('first spool write fault')):
                with self.assertRaisesRegex(guard.LeaseDenied, 'first spool write fault'):
                    lease.run_checked(list(guard.EMULATOR_SERVICE), 2, {}, emulator_capture=True)
            self.assertTrue(lease.last_result['reaped']); self.assertTrue(lease.last_result['forced'])
            self.assertIn('first spool write fault', (root / 'control/REVOKED').read_text())

    def test_secondary_spool_close_fault_cannot_replace_original_write_error(self):
        with self.fixture() as (root, lease), self.python_child("import os,time;os.write(1,b'prefix');time.sleep(1)"):
            real_close = guard._EmulatorCapture.close
            def close(capture):
                real_close(capture); raise OSError('secondary close fault')
            with (patch.object(guard._EmulatorCapture, 'write', side_effect=OSError('first write fault')),
                  patch.object(guard._EmulatorCapture, 'close', close)):
                with self.assertRaisesRegex(guard.LeaseDenied, 'first write fault'):
                    lease.run_checked(list(guard.EMULATOR_SERVICE), 2, {}, emulator_capture=True)
            self.assertIn('first write fault', lease.last_result['error'])
            self.assertIn('secondary close fault', str(lease.last_result['captureSecondaryErrors']))
            self.assertNotIn('secondary close fault', (root / 'control/REVOKED').read_text())

    def test_real_spool_fsync_fault_revokes_and_preserves_child_prefix_in_result(self):
        with self.fixture() as (root, lease), self.python_child("import os,time;os.write(1,b'prefix');time.sleep(1)"):
            real_sync = guard.os.fsync; faulted = []
            def fsync(fd):
                # The actual new spool uses os.write; revocation's fdopen writer
                # still needs its own fsync to preserve the original failure.
                if not faulted:
                    faulted.append(fd); raise OSError('first spool fsync fault')
                return real_sync(fd)
            with patch.object(guard.os, 'fsync', side_effect=fsync):
                with self.assertRaisesRegex(guard.LeaseDenied, 'first spool fsync fault'):
                    lease.run_checked(list(guard.EMULATOR_SERVICE), 2, {}, emulator_capture=True)
            self.assertEqual(lease.last_result['stdout'], b'prefix')
            self.assertEqual((root / 'fixtures/emulator.stdout').read_bytes(), b'prefix')
            self.assertTrue(lease.last_result['reaped']); self.assertTrue(lease.last_result['forced'])
            self.assertIn('first spool fsync fault', (root / 'control/REVOKED').read_text())

    def test_preexisting_symlink_and_unprivate_directory_refuse_before_child_launch(self):
        for variant in ('existing', 'symlink', 'mode'):
            with self.fixture() as (root, lease), patch.object(guard.subprocess, 'Popen') as child:
                if variant == 'existing': (root / 'fixtures/emulator.stdout').write_bytes(b'original')
                elif variant == 'symlink': (root / 'fixtures/emulator.stdout').symlink_to(root / 'foreign')
                else: (root / 'fixtures').chmod(0o755)
                with self.assertRaises(guard.LeaseDenied):
                    lease.run_checked(list(guard.EMULATOR_SERVICE), 1, {}, emulator_capture=True)
                child.assert_not_called(); self.assertTrue(lease.revoked)
                self.assertFalse((root / 'foreign').exists())
                if variant == 'existing': self.assertEqual((root / 'fixtures/emulator.stdout').read_bytes(), b'original')

    def test_disabled_capture_preserves_existing_default_child_behavior(self):
        with self.fixture() as (_, lease), patch.object(guard, '_EmulatorCapture') as capture:
            result = lease.run_checked([sys.executable, '-I', '-B', '-c', 'print("default")'], 2, {})
            capture.assert_not_called(); self.assertEqual(result['stdout'], b'default\n')
            self.assertIsNone(result['error']); self.assertFalse(result['forced'])

    def test_renderer_reads_are_exact_mandatory_and_backend_not_assumed(self):
        for name, args, optional in guard.RENDERER_READS:
            self.assertTrue(guard.allowed_adb(list(args))); self.assertEqual(guard.adb_timeout(list(args)), 10)
            self.assertFalse(optional); self.assertFalse(guard.allowed_adb(list(args) + ['--unexpected']))
        for args in (['shell', 'dumpsys', '-t', '10', 'SurfaceFlinger'],
                     ['shell', 'logcat', '-b', 'main', '-d', '-v', 'threadtime'],
                     ['shell', 'sh', '-c', 'dumpsys SurfaceFlinger'], ['shell', 'setprop', 'debug.hwui.renderer', 'skiagl']):
            self.assertFalse(guard.allowed_adb(args))
        fakes = load('test_diagnostic'); runtime = fakes.FakeRuntime()
        report = driver.run(runtime, clock=lambda: runtime.now)
        self.assertEqual(report['requestedRenderer'], 'lavapipe')
        self.assertEqual(report['effectiveBackend'], 'UNKNOWN'); self.assertEqual(report['effectiveVendor'], 'UNKNOWN')
        calls = runtime.calls
        prefix = next(i for i, x in enumerate(calls) if x[0] == 'emulator-prefixes')
        last_trace = max(i for i, x in enumerate(calls[:prefix]) if x[0] == 'adb')
        ui = next(i for i, x in enumerate(calls) if x[0] == 'adb' and x[1] == list(guard.HEALTH_UI[0]))
        self.assertLess(last_trace, prefix); self.assertLess(prefix, ui)

    def test_actual_prefix_reader_rejects_missing_overflow_symlink_and_preserves_zero_dispatch(self):
        for variant in ('missing', 'overflow', 'symlink', 'mode', 'valid'):
            with tempfile.TemporaryDirectory(prefix='nbdp-live-prefix-pure-') as value:
                root = Path(value); (root / 'session/fixtures').mkdir(parents=True, mode=0o700)
                directory = root / 'session/fixtures'
                for name, _ in guard.EMULATOR_STREAMS:
                    path = directory / name; path.write_bytes(b'live'); path.chmod(0o600)
                path = directory / 'emulator.stderr'
                if variant == 'missing': path.unlink()
                elif variant == 'overflow':
                    with path.open('wb') as out: out.truncate(262145)
                elif variant == 'symlink': path.unlink(); path.symlink_to(root / 'foreign')
                elif variant == 'mode': path.chmod(0o644)
                runtime = supervisor.Runtime.__new__(supervisor.Runtime)
                runtime.out = root; runtime.guard = guard; runtime.check = lambda: None
                runtime.diagnostic_deadline = time.monotonic() + 15
                revocations = []; runtime.lease = SimpleNamespace(revoke=lambda reason: revocations.append(reason))
                if variant == 'valid':
                    self.assertEqual(runtime.emulator_prefixes(), {'stdout': b'live', 'stderr': b'live'})
                    self.assertEqual(revocations, [])
                else:
                    with self.assertRaises((OSError, RuntimeError)): runtime.emulator_prefixes()
                    self.assertEqual(len(revocations), 1)


if __name__ == '__main__':
    unittest.main()
