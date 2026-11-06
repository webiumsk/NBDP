"""SOURCE-only OS-fake controls through the production capture function.

All process/FD/clock/signal/selector operations below are injected memory fakes.
These definitions cannot establish actual EOF, Popen reap or container DATA.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r1')
spec = importlib.util.spec_from_file_location('probe_finite_controls_subject', ROOT / 'finite_child.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
NS = 1_000_000_000


class Pipe:
    def __init__(self, name):
        self.name, self.closed = name, False

    def fileno(self):
        return self.name

    def close(self):
        self.closed = True


class Fake:
    def __init__(self):
        self.now, self.end = 100 * NS, 130 * NS
        self.rows = {'stdout': [b'ok', b''], 'stderr': [b'']}
        self.signals, self.waits, self.writes = [], [], []
        self.spawned, self.selector_closed = 0, False
        self.selector_error = self.spawn_error = self.select_error = None
        self.read_hook = self.wait_hook = None
        self.child = SimpleNamespace(pid=42, returncode=None, stdout=Pipe('stdout'), stderr=Pipe('stderr'))
        self.child.wait = self.wait
        self.mapping = {}

    def check(self):
        if self.now >= self.end:
            raise ValueError('FAKE_ABSOLUTE_PHASE_EXPIRED')
        return self.end - self.now

    def selector(self):
        if self.selector_error:
            raise self.selector_error
        return self

    def register(self, pipe, event, data):
        self.mapping[pipe.name] = SimpleNamespace(fileobj=pipe, fd=pipe.name, data=data)

    def unregister(self, pipe):
        del self.mapping[pipe.name]

    def get_map(self):
        return self.mapping

    def select(self, timeout):
        if self.select_error:
            raise self.select_error
        return [(key, 1) for key in list(self.mapping.values())]

    def close(self):
        self.selector_closed = True

    def popen(self, argv, **options):
        self.spawned += 1
        self.options = options
        if self.spawn_error:
            raise self.spawn_error
        return self.child

    def read(self, fd, amount):
        if self.read_hook:
            self.read_hook(fd)
        return self.rows[fd].pop(0)

    def wait(self, timeout):
        self.waits.append(timeout)
        if self.wait_hook:
            return self.wait_hook(timeout)
        self.child.returncode = 0
        return 0

    def signal(self, child, ownership):
        assert child is self.child and child.returncode is None
        self.signals.append(dict(ownership))
        return {'status': 'SYNTHETIC_SIGNAL'}

    def run(self, **changes):
        options = dict(run_ns=8 * NS, ends={}, check=self.check, finish_check=self.check,
                       capture=lambda name, raw: self.writes.append((name, raw)), target=False, ordinal=1,
                       environment={'SYNTHETIC': '1'}, cwd='/synthetic', popen=self.popen, selector=self.selector,
                       mono=lambda: self.now, read=self.read, getpgid=lambda pid: pid, getsid=lambda pid: pid,
                       signal_group=self.signal, set_blocking=lambda fd, state: None)
        options.update(changes)
        return F.capture(['/synthetic/cli'], **options)


class FiniteControls(unittest.TestCase):
    def test_actual_capture_natural_zero_actual_fake_eof_separate_streams(self):
        fake = Fake()
        result = fake.run()
        self.assertEqual(result['stdout'], b'ok')
        self.assertTrue(result['stdoutEOF'] and result['stderrEOF'] and result['reaped'])
        self.assertIsNone(result['fault'])
        self.assertIsNone(result['groupClosure'])
        self.assertEqual(fake.signals, [])
        self.assertEqual(fake.writes, [('stdout', b'ok'), ('stderr', b'')])
        self.assertTrue(fake.options['start_new_session'])

    def test_selector_failure_precedes_popen(self):
        fake = Fake()
        fake.selector_error = OSError('SELECTOR')
        with self.assertRaisesRegex(OSError, 'SELECTOR'):
            fake.run()
        self.assertEqual(fake.spawned, 0)

    def test_spawn_failure_does_not_claim_owned_child(self):
        fake = Fake()
        fake.spawn_error = OSError('SPAWN')
        result = fake.run()
        self.assertFalse(result['reaped'])
        self.assertFalse(result['stdoutEOF'])
        self.assertEqual(fake.signals, [])
        self.assertTrue(fake.selector_closed)

    def test_select_fault_signals_retained_unreaped_group_before_wait(self):
        fake = Fake()
        fake.select_error = OSError('SELECT')
        result = fake.run()
        self.assertEqual(len(fake.signals), 1)
        self.assertEqual(fake.signals[0]['pid'], 42)
        self.assertIn('SELECT', result['fault'])
        self.assertFalse(result['stdoutEOF'])
        self.assertTrue(result['reaped'])

    def test_stream_bound_fails_without_truncation_or_fake_eof(self):
        fake = Fake()
        fake.rows['stdout'] = [b'x' * 8192] * 33 + [b'']
        result = fake.run()
        self.assertEqual(len(result['stdout']), 262144)
        self.assertIn('CAPTURE_STREAM_LIMIT', result['fault'])
        self.assertFalse(result['stdoutEOF'])
        self.assertEqual(len(fake.signals), 1)

    def test_stderr_limit_is_4096_for_target(self):
        fake = Fake()
        fake.rows['stderr'] = [b'x' * 4097]
        result = fake.run(target=True, run_ns=55 * NS)
        self.assertIn('CAPTURE_STREAM_LIMIT', result['fault'])
        self.assertEqual(result['stderr'], b'')

    def test_phase_expiry_never_sends_late_group_signal(self):
        fake = Fake()
        fake.read_hook = lambda fd: setattr(fake, 'now', fake.end)
        result = fake.run()
        self.assertEqual(fake.signals, [])
        self.assertEqual(fake.waits, [0])
        self.assertFalse(result['stderrEOF'])
        self.assertIn('FAKE_ABSOLUTE_PHASE_EXPIRED', result['fault'])

    def test_single_reap_deadline_not_renewed_after_wait_timeout(self):
        fake = Fake()
        calls = []
        def wait(timeout):
            calls.append(timeout)
            fake.now += int(timeout * NS)
            raise TimeoutError('REAP')
        fake.wait_hook = wait
        result = fake.run()
        self.assertFalse(result['reaped'])
        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual(calls[0], 0)
        self.assertEqual(calls[1], 0)
        self.assertLessEqual(result['reapDeadlineMonoNs'], 103 * NS)

    def test_owned_session_mismatch_cannot_signal_foreign_group(self):
        fake = Fake()
        def guarded_signal(child, owned):
            if owned['sid'] != child.pid:
                raise ValueError('FOREIGN_GROUP')
            return fake.signal(child, owned)
        result = fake.run(getsid=lambda pid: pid + 1, signal_group=guarded_signal)
        self.assertEqual(fake.signals, [])
        self.assertIn('ACTUAL_SESSION_GROUP', result['fault'])

    def test_forced_pipe_close_never_becomes_eof(self):
        fake = Fake()
        fake.select_error = OSError('PIPE_CAPTURE_FAILURE')
        result = fake.run()
        self.assertTrue(fake.child.stdout.closed and fake.child.stderr.closed)
        self.assertFalse(result['stdoutEOF'] or result['stderrEOF'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
