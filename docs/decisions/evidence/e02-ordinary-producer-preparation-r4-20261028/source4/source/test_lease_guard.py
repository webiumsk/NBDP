"""Bounded local controls only: no Docker, ADB, emulator or host clock mutation.

Four original pure controls plus small owned Python child lifecycle regressions.
Execution remains a separate root-authorized step after exact source review.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os
import sys


path = Path(__file__).with_name('lease_guard.py')
spec = importlib.util.spec_from_file_location('e02_tested_lease_guard', path)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class Clock:
    def __init__(self):
        self.value = {'Utc': 1_800_000_000 * guard.NS, 'Mono': 100 * guard.NS,
                      'Boot': 100 * guard.NS, 'bootId': 'synthetic-boot'}
    def __call__(self): return dict(self.value)
    def advance(self, seconds):
        for kind in ('Utc', 'Mono', 'Boot'): self.value[kind] += seconds * guard.NS


class LeaseBoundaryTests(unittest.TestCase):
    def test_only_exact_cold_boot_wait_and_pinned_install_have180s_ceiling(self):
        self.assertTrue(guard.allowed_adb(['wait-for-device']))
        self.assertEqual(guard.adb_timeout(['wait-for-device']), 180)
        self.assertEqual(guard.adb_timeout(['install', '--no-streaming', '/artifact.apk']), 180)
        for args in (['shell', 'getprop', 'sys.boot_completed'],
                     ['install', '-t', '--no-streaming', '/helper.apk'],
                     ['exec-out', 'screencap', '-p'], ['reverse', 'tcp:17777', 'tcp:17777']):
            self.assertTrue(guard.allowed_adb(args)); self.assertEqual(guard.adb_timeout(args), 30)
        self.assertFalse(guard.allowed_adb(['wait-for-device', '--unexpected']))
        self.assertEqual(guard.adb_timeout(['wait-for-device', '--unexpected']), 30)

    def test_expiry_on_final_coherent_retry_dispatches_zero_payload_and_sticks(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-sample-') as directory:
            lease, clock = self.make(Path(directory)); calls = []
            base = clock.value['Utc']; elapsed = 60 * guard.NS
            # The discarded first sample was before expiry; only the second,
            # complete sample may reach the original immutable deadline checks.
            utc = [base + elapsed - 100000000, base + elapsed - 100000000, base + elapsed - 40000000,
                   base + elapsed, base + elapsed, base + elapsed + 1000000]
            with (patch.object(guard.time, 'time_ns', side_effect=utc),
                  patch.object(guard.time, 'monotonic_ns', side_effect=[clock.value['Mono'] + elapsed - 100000000,
                      clock.value['Mono'] + elapsed - 100000000, clock.value['Mono'] + elapsed - 40000000,
                      clock.value['Mono'] + elapsed, clock.value['Mono'] + elapsed,
                      clock.value['Mono'] + elapsed + 1000000]),
                  patch.object(guard.time, 'clock_gettime_ns', side_effect=[clock.value['Boot'] + elapsed - 100000000,
                                                                              clock.value['Boot'] + elapsed]),
                  patch.object(guard.Path, 'read_text', side_effect=['synthetic-boot',
                      'monotonic 0 0\nboottime 0 0\n', 'synthetic-boot', 'monotonic 0 0\nboottime 0 0\n'])):
                lease.clock = guard.sample
                with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('forbidden'))
            lease.clock = clock
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('later-forbidden'))
            self.assertEqual(calls, []); self.assertTrue((lease.control / 'REVOKED').exists())

    def test_exhausted_sample_retries_revoke_before_payload_and_stay_revoked(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-sample-') as directory:
            lease, clock = self.make(Path(directory)); calls = []; base = clock.value['Utc']
            lease.check(); previous = dict(lease.previous)
            utc = [base, base+1, base+50000001, base+60000000, base+60000001, base+110000001,
                   base+120000000, base+120000001, base+170000001]
            with (patch.object(guard.time, 'time_ns', side_effect=utc),
                  patch.object(guard.time, 'monotonic_ns', return_value=clock.value['Mono']),
                  patch.object(guard.time, 'clock_gettime_ns', return_value=clock.value['Boot']),
                  patch.object(guard.Path, 'read_text', side_effect=['synthetic-boot',
                      'monotonic 0 0\nboottime 0 0\n'] * 3)):
                lease.clock = guard.sample
                with self.assertRaisesRegex(guard.LeaseDenied, 'after 3 attempts'):
                    lease.dispatch(lambda: calls.append('forbidden'))
            self.assertEqual(lease.previous, previous, 'Discarded samples cannot advance accepted clock history')
            lease.clock = clock
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('later-forbidden'))
            self.assertEqual(calls, []); self.assertTrue((lease.control / 'REVOKED').exists())

    def assert_final_retry_refused(self, previous_seconds, deltas, reason):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-sample-') as directory:
            lease, clock = self.make(Path(directory)); initial = dict(clock.value); calls = []
            clock.advance(previous_seconds); lease.check(); previous = dict(lease.previous)
            final = {kind: initial[kind] + deltas[kind] for kind in ('Utc', 'Mono', 'Boot')}
            utc = [previous['Utc'], previous['Utc'] + 1, previous['Utc'] + 50000001,
                   final['Utc'], final['Utc'], final['Utc'] + 1]
            mono = [previous['Mono'], previous['Mono'] + 1, previous['Mono'] + 50000001,
                    final['Mono'], final['Mono'], final['Mono'] + 1]
            with (patch.object(guard.time, 'time_ns', side_effect=utc),
                  patch.object(guard.time, 'monotonic_ns', side_effect=mono),
                  patch.object(guard.time, 'clock_gettime_ns', side_effect=[previous['Boot'], final['Boot']]),
                  patch.object(guard.Path, 'read_text', side_effect=['synthetic-boot',
                      'monotonic 0 0\nboottime 0 0\n'] * 2)):
                lease.clock = guard.sample
                with self.assertRaisesRegex(guard.LeaseDenied, reason):
                    lease.dispatch(lambda: calls.append('forbidden'))
            self.assertEqual(lease.previous, previous, 'Refused final sample cannot advance accepted history')
            self.assertTrue((lease.control / 'REVOKED').exists())
            lease.clock = clock
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('later-forbidden'))
            self.assertEqual(calls, [])

    def test_interrupted_retry_final_resumption_gap_refuses_zero_payload_sticky(self):
        self.assert_final_retry_refused(0, {kind: 16 * guard.NS for kind in ('Utc', 'Mono', 'Boot')},
                                       'unobserved resumption gap')

    def test_interrupted_retry_final_previous_clock_rollback_refuses_zero_payload_sticky(self):
        self.assert_final_retry_refused(2, {kind: guard.NS for kind in ('Utc', 'Mono', 'Boot')},
                                       'clock rollback')

    def test_interrupted_retry_final_utc_boot_drift_refuses_zero_payload_sticky(self):
        self.assert_final_retry_refused(0, {'Utc': guard.NS, 'Mono': 0, 'Boot': 0}, 'UTC/boottime drift')

    def assert_metadata_delay(self, seconds, reason=None, changed_boot=False):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-proc-delay-') as directory:
            lease, clock = self.make(Path(directory)); lease.check(); previous = dict(lease.previous)
            original = lease.path.read_bytes(); calls = []; metadata_count = 0
            def metadata(*args, **kwargs):
                nonlocal metadata_count
                metadata_count += 1
                if metadata_count % 2:
                    clock.advance(seconds)
                    return 'changed-boot' if changed_boot else 'synthetic-boot'
                return 'monotonic 0 0\nboottime 0 0\n'
            with (patch.object(guard.Path, 'read_text', side_effect=metadata),
                  patch.object(guard.time, 'time_ns', side_effect=lambda: clock.value['Utc']),
                  patch.object(guard.time, 'monotonic_ns', side_effect=lambda: clock.value['Mono']),
                  patch.object(guard.time, 'clock_gettime_ns', side_effect=lambda _: clock.value['Boot'])):
                lease.clock = guard.sample
                if reason:
                    with self.assertRaisesRegex(guard.LeaseDenied, reason):
                        lease.dispatch(lambda: calls.append('forbidden'))
                else:
                    lease.dispatch(lambda: calls.append('accepted'))
            self.assertEqual(lease.path.read_bytes(), original, 'Metadata delay cannot renew original deadlines')
            if reason:
                self.assertEqual(metadata_count, 2, 'Invalid final clocks must refuse before dispatch, no retry')
                self.assertEqual(lease.previous, previous)
                self.assertTrue((lease.control / 'REVOKED').exists())
                lease.clock = clock
                with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('later-forbidden'))
                self.assertEqual(calls, [])
            else:
                self.assertEqual(metadata_count, 4, 'Each boundary must reread metadata, no clock retry')
                self.assertEqual(calls, ['accepted'])
                self.assertEqual(lease.previous['Boot'], previous['Boot'] + 2 * seconds * guard.NS)
                self.assertFalse((lease.control / 'REVOKED').exists())

    def test_metadata_delay_within_original_budget_is_charged_without_clock_retry(self):
        self.assert_metadata_delay(1)

    def test_metadata_delay_cannot_extend_original_expiry(self):
        self.assert_metadata_delay(60, 'original deadline/clock refused')

    def test_metadata_delay_over_resumption_gap_refuses_zero_payload(self):
        self.assert_metadata_delay(16, 'unobserved resumption gap')

    def test_changed_boot_after_metadata_delay_refuses_zero_payload(self):
        self.assert_metadata_delay(1, 'boot identity changed', changed_boot=True)

    def make(self, root):
        clock = Clock(); data = guard.issue('a' * 32, 60, clock)
        path = root / 'lease.json'; raw = (json.dumps(data) + '\n').encode(); path.write_bytes(raw)
        control = root / 'control'; control.mkdir()
        return guard.Lease(path, hashlib.sha256(raw).hexdigest(), control, clock), clock

    def test_nominal_original_lease_dispatch(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-inert-') as directory:
            lease, clock = self.make(Path(directory)); calls = []
            clock.advance(1)
            self.assertEqual(lease.dispatch(lambda: calls.append('payload') or 'actual-result'), 'actual-result')
            self.assertEqual(calls, ['payload'])
            self.assertFalse((lease.control / 'REVOKED').exists())

    def test_already_expired_dispatches_no_payload(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-inert-') as directory:
            lease, clock = self.make(Path(directory)); calls = []
            clock.advance(60)
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('forbidden'))
            self.assertEqual(calls, [])
            self.assertTrue((lease.control / 'REVOKED').exists())

    def test_expiry_during_wait_never_accepts_or_dispatches_later(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-inert-') as directory:
            lease, clock = self.make(Path(directory)); calls = []
            def in_flight():
                calls.append('already-in-flight'); clock.advance(60)
                return 'must-not-be-accepted'
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(in_flight)
            clock.advance(-60)
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('later-forbidden'))
            self.assertEqual(calls, ['already-in-flight'])
            self.assertTrue((lease.control / 'REVOKED').exists())

    def test_explicit_revoke_is_sticky_after_wait(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-inert-') as directory:
            lease, clock = self.make(Path(directory)); calls = []
            def in_flight():
                calls.append('already-in-flight')
                (lease.control / 'REVOKED').write_text('inert explicit revoke\n')
                return 'must-not-be-accepted'
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(in_flight)
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: calls.append('later-forbidden'))
            self.assertEqual(calls, ['already-in-flight'])

    def test_resumption_gap_inside_total_budget_revokes(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-inert-') as directory:
            lease, clock = self.make(Path(directory)); lease.check(); clock.advance(16)
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: self.fail('payload after gap'))

    def test_clock_rollback_inside_original_window_revokes(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-inert-') as directory:
            lease, clock = self.make(Path(directory)); clock.advance(2); lease.check()
            clock.value['Mono'] -= guard.NS
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: self.fail('payload after rollback'))

    def test_owned_child_natural_exit_reaped_full_eof(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-child-') as directory:
            lease, _ = self.make(Path(directory))
            with patch.object(guard.os, 'killpg', wraps=os.killpg) as kill:
                result = lease.run_checked([sys.executable, '-I', '-c',
                    "import sys;sys.stdout.write('actual-out');sys.stderr.write('actual-err')"], 3, {'PATH': '/usr/bin:/bin'})
            self.assertEqual(result['stdout'], b'actual-out'); self.assertEqual(result['stderr'], b'actual-err')
            self.assertEqual(result['exit'], 0); self.assertTrue(result['reaped'])
            self.assertTrue(result['stdoutEOF'] and result['stderrEOF']); self.assertFalse(result['forced'])
            kill.assert_not_called()

    def failed_child_is_sticky(self, code, timeout):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-child-') as directory:
            lease, _ = self.make(Path(directory)); sentinel = []
            original_kill = os.killpg
            def owned_signal(pid, sig):
                self.assertTrue((lease.control / 'REVOKED').exists(), 'Sticky refusal must precede cancellation')
                # WNOWAIT keeps even an exited leader owned until final wait.
                os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                return original_kill(pid, sig)
            with patch.object(guard.os, 'killpg', side_effect=owned_signal):
                with self.assertRaises(guard.LeaseDenied):
                    lease.run_checked([sys.executable, '-I', '-c', code], timeout, {'PATH': '/usr/bin:/bin'})
            self.assertTrue(lease.last_result['reaped'])
            self.assertTrue((lease.control / 'REVOKED').exists())
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: sentinel.append('forbidden'))
            self.assertEqual(sentinel, [])
            return lease.last_result

    def test_owned_child_timeout_sticky_before_later_payload(self):
        result = self.failed_child_is_sticky('import time;time.sleep(10)', .15)
        self.assertTrue(result['timedOut']); self.assertTrue(result['forced'])

    def test_owned_child_capture_failure_sticky_before_later_payload(self):
        result = self.failed_child_is_sticky("import sys;sys.stderr.buffer.write(b'x'*300000);sys.stderr.flush()", 3)
        self.assertIn('capture exceeded', result['error'])
        self.assertLessEqual(len(result['stderr']), 262144)

    def test_owned_child_nonzero_exit_sticky(self):
        result = self.failed_child_is_sticky('raise SystemExit(7)', 3)
        self.assertEqual(result['exit'], 7)

    def test_post_reap_expiry_never_signals_reaped_numeric_pid(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-child-') as directory:
            lease, clock = self.make(Path(directory)); original = guard.subprocess.Popen
            class ReapThenExpire(original):
                def wait(self, *args, **kwargs):
                    value = super().wait(*args, **kwargs)
                    clock.advance(60)
                    return value
            with patch.object(guard.subprocess, 'Popen', ReapThenExpire), patch.object(guard.os, 'killpg') as kill:
                with self.assertRaises(guard.LeaseDenied):
                    lease.run_checked([sys.executable, '-I', '-c', 'pass'], 3, {'PATH': '/usr/bin:/bin'})
            self.assertTrue(lease.last_result['reaped']); self.assertEqual(lease.last_result['exit'], 0)
            kill.assert_not_called()
            with self.assertRaises(guard.LeaseDenied): lease.dispatch(lambda: self.fail('later payload'))


class ClockSamplingTests(unittest.TestCase):
    OFFSETS = 'monotonic 0 0\nboottime 0 0\n'

    def test_proc_checks_precede_outermost_monotonic_clock_only_bracket(self):
        order = []; metadata_count = 0
        def mono():
            order.append('mono'); return 100
        def utc():
            order.append('utc'); return 200
        def boot(clock_id):
            self.assertEqual(clock_id, guard.time.CLOCK_BOOTTIME)
            order.append('boot'); return 300
        def metadata(*args, **kwargs):
            nonlocal metadata_count
            order.append('proc'); metadata_count += 1
            return 'synthetic-boot' if metadata_count == 1 else self.OFFSETS
        with (patch.object(guard.time, 'monotonic_ns', side_effect=mono),
              patch.object(guard.time, 'time_ns', side_effect=utc),
              patch.object(guard.time, 'clock_gettime_ns', side_effect=boot),
              patch.object(guard.Path, 'read_text', side_effect=metadata)):
            guard.sample()
        self.assertEqual(order, ['proc', 'proc', 'mono', 'utc', 'utc', 'mono', 'boot', 'utc', 'mono'])

    def test_overlong_attempt_is_discarded_and_full_fresh_retry_returned(self):
        with (patch.object(guard.time, 'time_ns', side_effect=[100, 101, 50000101, 60000000, 60000001, 60000002]) as utc,
              patch.object(guard.time, 'monotonic_ns', side_effect=[110, 111, 50000111, 221, 222, 223]) as mono,
              patch.object(guard.time, 'clock_gettime_ns', side_effect=[333, 444]) as boot,
              patch.object(guard.Path, 'read_text', side_effect=['first-boot', self.OFFSETS,
                                                                 'fresh-boot', self.OFFSETS]) as metadata):
            result = guard.sample()
        self.assertEqual(result, {'Utc': 60000001, 'Mono': 222, 'Boot': 444, 'bootId': 'fresh-boot'})
        self.assertEqual((utc.call_count, mono.call_count, boot.call_count, metadata.call_count), (6, 6, 2, 4))

    def test_long_monotonic_bracket_cannot_be_hidden_by_short_wall_bracket(self):
        with (patch.object(guard.time, 'time_ns', side_effect=[100, 101, 102, 200, 201, 202]) as utc,
              patch.object(guard.time, 'monotonic_ns', side_effect=[100, 101, 50000101,
                                                                     60000000, 60000001, 60000002]),
              patch.object(guard.time, 'clock_gettime_ns', side_effect=[300, 400]),
              patch.object(guard.Path, 'read_text', side_effect=['discarded', self.OFFSETS,
                                                                 'fresh', self.OFFSETS])):
            result = guard.sample()
        self.assertEqual(result['Utc'], 201); self.assertEqual(result['bootId'], 'fresh')
        self.assertEqual(utc.call_count, 6)

    def test_three_overlong_attempts_fail_closed_without_fourth(self):
        utc_values = [0, 1, 50000001, 60000000, 60000001, 110000001,
                      120000000, 120000001, 170000001]
        with (patch.object(guard.time, 'time_ns', side_effect=utc_values) as utc,
              patch.object(guard.time, 'monotonic_ns', return_value=100),
              patch.object(guard.time, 'clock_gettime_ns', return_value=100),
              patch.object(guard.Path, 'read_text', side_effect=['same-boot', self.OFFSETS] * 3) as metadata):
            with self.assertRaisesRegex(guard.LeaseDenied, 'after 3 attempts'): guard.sample()
        self.assertEqual(utc.call_count, 9); self.assertEqual(metadata.call_count, 6)

    def test_exact50ms_bracket_remains_accepted(self):
        with (patch.object(guard.time, 'time_ns', side_effect=[100, 101, 50000100]) as utc,
              patch.object(guard.time, 'monotonic_ns', return_value=200),
              patch.object(guard.time, 'clock_gettime_ns', return_value=300),
              patch.object(guard.Path, 'read_text', side_effect=['same-boot', self.OFFSETS])):
            self.assertEqual(guard.sample()['Utc'], 101)
        self.assertEqual(utc.call_count, 3)

    def test_negative_bracket_is_immediate_failure_without_retry(self):
        with (patch.object(guard.time, 'time_ns', side_effect=[100, 101, 99]) as utc,
              patch.object(guard.time, 'monotonic_ns', return_value=200),
              patch.object(guard.time, 'clock_gettime_ns', return_value=300),
              patch.object(guard.Path, 'read_text', side_effect=['same-boot', self.OFFSETS]) as metadata):
            with self.assertRaisesRegex(guard.LeaseDenied, 'bracket rollback'): guard.sample()
        self.assertEqual(utc.call_count, 3); self.assertEqual(metadata.call_count, 2)

    def test_invalid_namespace_is_not_retried(self):
        with (patch.object(guard.time, 'time_ns', side_effect=[100, 101]) as utc,
              patch.object(guard.time, 'monotonic_ns', return_value=200),
              patch.object(guard.time, 'clock_gettime_ns', return_value=300),
              patch.object(guard.Path, 'read_text', side_effect=['same-boot', 'monotonic 1 0\nboottime 0 0\n']) as metadata):
            with self.assertRaisesRegex(guard.LeaseDenied, 'namespace'): guard.sample()
        self.assertEqual(utc.call_count, 0); self.assertEqual(metadata.call_count, 2)

    def test_metadata_read_failure_is_not_retried(self):
        with (patch.object(guard.time, 'time_ns', side_effect=[100, 101]) as utc,
              patch.object(guard.time, 'monotonic_ns', return_value=200),
              patch.object(guard.time, 'clock_gettime_ns', return_value=300),
              patch.object(guard.Path, 'read_text', side_effect=OSError('injected boot read failure')) as metadata):
            with self.assertRaisesRegex(OSError, 'boot read failure'): guard.sample()
        self.assertEqual(utc.call_count, 0); self.assertEqual(metadata.call_count, 1)


if __name__ == '__main__': unittest.main()
