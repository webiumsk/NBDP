"""SOURCE-only tests of actual R2 RAW-tool decisions, never real executables.

Synthetic incremental zero streams model the DECLARED lengths32959480/47353290;
FakeDigest counts bytes/nonzero bytes and hashes that small synthetic summary.
This does not validate the actual Python/Docker binary hashes or execute them.
The production verifier/phase functions are not replaced. Only their OS reads,
stat/alias queries, digest port and unrelated metadata/source gates are mocked.
No real file, process, Docker, guard or helper is used by these controls.
"""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2')
REUSED = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r1')
REAL_SHA256 = hashlib.sha256


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


H = load('raw_tool_host_control_subject', HERE / 'host.py')
C = load('raw_tool_core_control_subject', REUSED / 'controller.py')
LENGTHS = {H.PYTHON: 32959480, H.DOCKER: 47353290}


def synthetic_sha(size, nonzero=0):
    return REAL_SHA256(('SYNTHETIC_ZERO_STREAM:%d:%d' % (size, nonzero)).encode()).hexdigest()


class FakeDigest:
    def __init__(self):
        self.size, self.nonzero = 0, 0

    def update(self, block):
        self.size += len(block)
        self.nonzero += len(block) - block.count(b'\0')

    def hexdigest(self):
        return synthetic_sha(self.size, self.nonzero)


def digest_factory(data=None):
    # Actual small JSON metadata hashes retain genuine hashlib semantics.
    return FakeDigest() if data is None else REAL_SHA256(data)


def pin(path, raw):
    return {'path': str(path), 'bytes': len(raw), 'sha256': REAL_SHA256(raw).hexdigest()}


class StreamPorts:
    def __init__(self):
        self.tools = {key: {'path': path, 'bytes': LENGTHS[path], 'sha256': synthetic_sha(LENGTHS[path])}
                      for key, path in (('python', H.PYTHON), ('docker', H.DOCKER))}
        self.initial_changes = {}
        self.open_changes = {}
        self.final_fd_changes = {}
        self.final_path_changes = {}
        self.aliases = set()
        self.opens, self.closes, self.reads = [], [], []
        self.handles, self.lstats = {}, {}
        self.open_error = self.read_error = self.close_error = None
        self.check_error_at = None
        self.checks = 0
        self.deadline_error = ValueError('SYNTHETIC_ABSOLUTE_CLOCK_EXHAUSTED')
        self.stream_lengths = dict(LENGTHS)
        self.corrupt_bytes = False

    def check(self):
        self.checks += 1
        if self.checks == self.check_error_at:
            raise self.deadline_error
        return 1

    def snapshot(self, path, changes=None):
        value = dict(st_dev=1, st_ino=100 if path == H.PYTHON else 101, st_size=LENGTHS[path],
                     st_mode=stat.S_IFREG | 0o755, st_mtime_ns=123, st_ctime_ns=456,
                     st_nlink=1, st_uid=1000, st_gid=1000)
        value.update(changes or {})
        return SimpleNamespace(**value)

    def lstat(self, path):
        path = str(path)
        assert path in LENGTHS, 'No foreign path may reach raw OS admission'
        count = self.lstats.get(path, 0) + 1
        self.lstats[path] = count
        changes = self.initial_changes if count % 2 else self.final_path_changes
        return self.snapshot(path, changes)

    def open(self, path, flags):
        path = str(path)
        assert path in LENGTHS
        self.opens.append((path, flags))
        assert flags == os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        if self.open_error is not None:
            raise self.open_error
        fd = 100 + len(self.opens)
        self.handles[fd] = dict(path=path, position=0, fstats=0, reads=0)
        return fd

    def fstat(self, fd):
        handle = self.handles[fd]
        handle['fstats'] += 1
        changes = self.open_changes if handle['fstats'] == 1 else self.final_fd_changes
        return self.snapshot(handle['path'], changes)

    def read(self, fd, size):
        handle = self.handles[fd]
        handle['reads'] += 1
        assert 1 <= size <= 65536
        self.reads.append((handle['path'], size, handle['position']))
        if self.read_error is not None:
            raise self.read_error
        length = self.stream_lengths[handle['path']]
        count = min(size, max(0, length - handle['position']))
        handle['position'] += count
        return (b'X' if self.corrupt_bytes else b'\0') * count

    def close(self, fd):
        self.closes.append(fd)
        if self.close_error is not None:
            raise self.close_error

    def patched(self):
        stack = ExitStack()
        stack.enter_context(patch.object(Path, 'is_symlink', lambda path: str(path) in self.aliases))
        stack.enter_context(patch.object(Path, 'lstat', lambda path: self.lstat(path)))
        stack.enter_context(patch.object(H.os, 'open', self.open))
        stack.enter_context(patch.object(H.os, 'fstat', self.fstat))
        stack.enter_context(patch.object(H.os, 'read', self.read))
        stack.enter_context(patch.object(H.os, 'close', self.close))
        stack.enter_context(patch.object(H.hashlib, 'sha256', digest_factory))
        return stack

    def one(self, descriptor=None):
        with self.patched():
            return H.verify_raw_tool(descriptor or self.tools['python'], self.check)


class PhaseMemory:
    """Real three Host phase functions, opaque source/gate checks kept separate."""
    def __init__(self, ports):
        self.ports = ports
        self.events, self.sinks = [], []
        self.metadata = {}
        self.lease_raw = b'synthetic original immutable lease'
        self.subject_pin = pin('/memory/controller-subject.json', b'subject')
        self.producer_pin = pin('/memory/producer-subject.json', b'producer')
        run, nonce = '1' * 32, '2' * 32
        self.plan = dict(schema='e02-one-cid-helper-probe-plan-v1', scope='ONE_OWNED_HELPER_PROBE_ONLY',
                         runId=run, creationNonce=nonce, name='nbdp-helper-probe-' + run + '-' + nonce,
                         uidGid='1000:1000', inputRoot='/memory/input', controlRoot='/memory/control',
                         outputRoot='/memory/output', dockerConfig='/memory/docker',
                         lease=pin('/memory/original-lease.json', self.lease_raw),
                         source8=[pin('/memory/source/' + name, b'source') for name in C.SOURCE_NAMES],
                         guardManifest=copy.deepcopy(H.GUARD_MANIFEST),
                         guardRoot='/tmp/nbdp-e02-minimal-rs-v7/guard-python',
                         tools=copy.deepcopy(ports.tools), expectedImageConfigSha256='a' * 64,
                         gates={'producerSource': self.producer_pin, 'controllerSource': self.subject_pin})
        concrete = {'scope': 'CURRENT_CONCRETE_INPUTS', 'sha256': REAL_SHA256(C.encoded(
                    {k: v for k, v in self.plan.items() if k != 'gates'})).hexdigest()}
        evidence = pin('/memory/evidence.json', b'evidence')
        for key in ('producerData', 'sourceQa', 'sourceSecurity', 'controlData', 'concreteInput'):
            actor = '/root/independent_' + key
            subject = self.producer_pin if key == 'producerData' else concrete if key == 'concreteInput' else self.subject_pin
            raw = C.encoded(dict(schema='e02-one-cid-helper-probe-gate-v1', kind=key, actor=actor,
                                 decision='ACCEPT', subject=subject, evidence=evidence,
                                 scope='ONE_OWNED_HELPER_PROBE_ONLY'))
            descriptor = pin('/memory/gate-' + key + '.json', raw)
            self.plan['gates'][key] = descriptor
            self.metadata[descriptor['path']] = raw
        self.metadata.update({evidence['path']: b'evidence', self.producer_pin['path']: b'producer',
                              self.subject_pin['path']: b'subject', self.plan['lease']['path']: self.lease_raw})
        plan_pin = pin('/memory/plan.json', b'plan')
        constants = dict(source8=self.plan['source8'], acceptedProducerSubject=self.producer_pin,
                         sourceContributors=['/root/tool_source_author'])
        release = dict(plan=plan_pin, subject=self.subject_pin, gates=self.plan['gates'],
                       authors=['/root/tool_source_author'], operators=['/root'])
        self.host = H.Host(C, None, constants, plan_pin, self.subject_pin, {}, release,
                           SimpleNamespace(sample=lambda: None))
        self.host.output = Path(self.plan['outputRoot'])
        self.host.staged = True
        self.host.ledger = C.ByteLedger()
        self.host.controller_sources = [pin('/memory/' + name, b'code') for name in ('controller.py', 'host.py', 'finite_child.py')]
        self.metadata.update({d['path']: b'code' for d in self.host.controller_sources})

    def verify_metadata(self, descriptor, check=lambda: None, cap=8388608):
        assert descriptor['path'] not in LENGTHS, 'Tools MUST take actual streaming verifier'
        check()
        return self.metadata[descriptor['path']]

    def raw_metadata(self, path, cap, check=lambda: None):
        assert str(path) == '/memory/output/lease.json'
        check()
        return self.lease_raw, 0o600

    def sources(self, plan, check, staged=False):
        check()
        self.events.append(('unrelated-source-check', staged))

    def run(self, phase):
        with self.ports.patched(), patch.object(H, 'verify', self.verify_metadata), \
             patch.object(H, 'raw_read', self.raw_metadata), \
             patch.object(H, 'private_roots', lambda plan: self.events.append('private-roots')), \
             patch.object(H.os, 'getuid', lambda: 1000), patch.object(H.os, 'getgid', lambda: 1000), \
             patch.object(self.host, 'sources', self.sources), \
             patch.object(self.host, 'sink', lambda name, raw: self.sinks.append((name, raw))), \
             patch.object(Path, 'read_bytes', lambda path: self.lease_raw if str(path) == '/memory/output/lease.json' else None), \
             patch.object(Path, 'iterdir', lambda path: iter(())):
            if phase == 'admit':
                return self.host.admit(self.plan, 'a' * 64, self.ports.check)
            if phase == 'before_target':
                return self.host.before_target(self.plan, self.ports.check)
            if phase == 'postread':
                return self.host.postread(self.plan, self.ports.check)
            raise AssertionError('Unknown phase')


class RawToolControls(unittest.TestCase):
    def test_declared_python_and_docker_above16mib_stream_positive_no_retained_binary(self):
        ports = StreamPorts()
        self.assertEqual([ports.tools[k]['bytes'] for k in ('python', 'docker')], [32959480, 47353290])
        self.assertTrue(all(d['bytes'] > 16777216 for d in ports.tools.values()))
        with ports.patched():
            result = H.verify_raw_tools(ports.tools, ports.check)
        self.assertEqual(result, [ports.tools['python'], ports.tools['docker']])
        self.assertTrue(all(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'} for row in result))
        self.assertEqual(len(ports.closes), 2)
        for path in LENGTHS:
            handle = next(v for v in ports.handles.values() if v['path'] == path)
            self.assertEqual(handle['position'], LENGTHS[path])
            self.assertEqual([r[1] for r in ports.reads if r[0] == path][-1], 1)
        self.assertLessEqual(max(r[1] for r in ports.reads), 65536)
        self.assertGreater(ports.checks, 3 * len(ports.reads))

    def test_raw2gib_ceiling_is_separate_from_metadata_and_proof_caps(self):
        ports = StreamPorts()
        descriptor = dict(ports.tools['python'], bytes=2147483649)
        with self.assertRaisesRegex(ValueError, 'DECLARED_RAW_TOOL2GIB'):
            ports.one(descriptor)
        self.assertEqual(ports.opens, [])
        self.assertEqual(ports.reads, [])
        self.assertEqual(H.RAW_TOOL_LIMIT, 2147483648)
        self.assertEqual(H.RAW_TOOL_CHUNK, 65536)
        # Parsed authority stays capped at8MiB here, not widened to RAW.
        with self.assertRaisesRegex(ValueError, 'BOUNDED_PIN'):
            H.verify(dict(descriptor, bytes=32959480))

    def test_foreign_path_closed_pin_and_wrong_tool_slot_rejected_before_open(self):
        for kind in ('foreign', 'extra', 'missing', 'slot'):
            with self.subTest(kind=kind):
                ports = StreamPorts()
                with ports.patched():
                    with self.assertRaisesRegex(ValueError, 'DECLARED_RAW_TOOL2GIB|CLOSED_RAW_TOOL_PIN|EXACT_TWO_RAW_TOOLS'):
                        if kind == 'slot':
                            H.verify_raw_tools({'python': ports.tools['docker'], 'docker': ports.tools['python']}, ports.check)
                        else:
                            d = dict(ports.tools['python'])
                            if kind == 'foreign': d['path'] = '/foreign/python'
                            elif kind == 'extra': d['extra'] = True
                            else: del d['sha256']
                            H.verify_raw_tool(d, ports.check)
                self.assertEqual(ports.opens, [])

    def test_declared_size_wrong_before_open(self):
        ports = StreamPorts()
        with self.assertRaisesRegex(ValueError, 'RAW_TOOL_EXPECTED_REGULAR_SIZE'):
            ports.one(dict(ports.tools['python'], bytes=32959479))
        self.assertEqual(ports.opens, [])

    def test_nonregular_and_hardlink_before_open(self):
        for changes in ({'st_mode': stat.S_IFIFO | 0o600}, {'st_mode': stat.S_IFDIR | 0o700}, {'st_nlink': 2}):
            with self.subTest(changes=changes):
                ports = StreamPorts()
                ports.initial_changes = changes
                with self.assertRaisesRegex(ValueError, 'RAW_TOOL_EXPECTED_REGULAR_SIZE'):
                    ports.one()
                self.assertEqual(ports.opens, [])
                self.assertEqual(ports.reads, [])

    def test_path_and_ancestor_symlink_before_open(self):
        for path in (H.PYTHON, str(Path(H.PYTHON).parent)):
            with self.subTest(alias=path):
                ports = StreamPorts()
                ports.aliases.add(path)
                with self.assertRaisesRegex(ValueError, 'NO_PATH_SYMLINK'):
                    ports.one()
                self.assertEqual(ports.opens, [])

    def test_open_failure_has_no_close_of_unowned_descriptor(self):
        ports = StreamPorts()
        ports.open_error = PermissionError('SYNTHETIC_OPEN_DENIED')
        with self.assertRaises(PermissionError) as caught:
            ports.one()
        self.assertIs(caught.exception, ports.open_error)
        self.assertEqual(ports.closes, [])
        self.assertEqual(ports.reads, [])

    def test_opened_identity_each_field_refuses_before_read_and_closes(self):
        for field in ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink', 'st_uid', 'st_gid'):
            with self.subTest(field=field):
                ports = StreamPorts()
                value = getattr(ports.snapshot(H.PYTHON), field)
                ports.open_changes = {field: value + 1}
                with self.assertRaisesRegex(ValueError, 'RAW_TOOL_OPENED_IDENTITY'):
                    ports.one()
                self.assertEqual(ports.reads, [])
                self.assertEqual(len(ports.closes), 1)

    def test_final_fd_and_path_identity_each_field_and_close(self):
        for target in ('fd', 'path'):
            for field in ('st_dev', 'st_ino', 'st_size', 'st_mode', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink', 'st_uid', 'st_gid'):
                with self.subTest(target=target, field=field):
                    ports = StreamPorts()
                    changes = {field: getattr(ports.snapshot(H.PYTHON), field) + 1}
                    if target == 'fd': ports.final_fd_changes = changes
                    else: ports.final_path_changes = changes
                    with self.assertRaisesRegex(ValueError, 'RAW_TOOL_FINAL_FD_IDENTITY|RAW_TOOL_FINAL_PATH_IDENTITY'):
                        ports.one()
                    self.assertEqual(len(ports.closes), 1)

    def test_wrong_expected_hash_or_stream_bytes_refuses(self):
        for kind in ('expected', 'bytes'):
            with self.subTest(kind=kind):
                ports = StreamPorts()
                d = dict(ports.tools['python'])
                if kind == 'expected': d['sha256'] = 'f' * 64
                else: ports.corrupt_bytes = True
                with self.assertRaisesRegex(ValueError, 'RAW_TOOL_EXPECTED_SHA_LENGTH'):
                    ports.one(d)
                self.assertEqual(len(ports.closes), 1)

    def test_premature_eof_and_exact_length_plus_one_growth_refused(self):
        for delta in (-1, 1):
            with self.subTest(delta=delta):
                ports = StreamPorts()
                ports.stream_lengths[H.PYTHON] += delta
                with self.assertRaisesRegex(ValueError, 'RAW_TOOL_EXPECTED_SHA_LENGTH|RAW_TOOL_STREAM_LENGTH'):
                    ports.one()
                self.assertEqual(len(ports.closes), 1)
                if delta == 1:
                    self.assertEqual(ports.reads[-1][1], 1)

    def test_clock_failure_before_open_and_after_first_read(self):
        for check_at in (1, 2, 3, 4, 5):
            with self.subTest(check=check_at):
                ports = StreamPorts()
                ports.check_error_at = check_at
                with self.assertRaises(ValueError) as caught:
                    ports.one()
                self.assertIs(caught.exception, ports.deadline_error)
                self.assertEqual(len(ports.closes), 0 if check_at <= 2 else 1)
                self.assertLessEqual(len(ports.reads), 1)

    def test_read_error_and_close_error_preserve_original_first_fault(self):
        ports = StreamPorts()
        ports.read_error = OSError('SYNTHETIC_READ_FAILURE')
        ports.close_error = OSError('SYNTHETIC_CLOSE_FAILURE')
        with self.assertRaises(OSError) as caught:
            ports.one()
        self.assertIs(caught.exception, ports.read_error)
        self.assertEqual(len(ports.closes), 1)

    def test_successful_stream_close_error_still_refuses(self):
        ports = StreamPorts()
        ports.close_error = OSError('SYNTHETIC_CLOSE_FAILURE')
        with self.assertRaises(OSError) as caught:
            ports.one()
        self.assertIs(caught.exception, ports.close_error)
        self.assertEqual(len(ports.closes), 1)

    def test_open_identity_error_not_replaced_by_close_failure(self):
        ports = StreamPorts()
        ports.open_changes = {'st_uid': 2000}
        ports.close_error = OSError('SYNTHETIC_CLOSE_FAILURE')
        with self.assertRaisesRegex(ValueError, 'RAW_TOOL_OPENED_IDENTITY'):
            ports.one()
        self.assertEqual(len(ports.closes), 1)

    def test_all_three_actual_host_phases_admit_declared_large_tools(self):
        for phase in ('admit', 'before_target', 'postread'):
            with self.subTest(phase=phase):
                ports = StreamPorts()
                memory = PhaseMemory(ports)
                memory.run(phase)
                self.assertEqual([p for p, flags in ports.opens], [H.PYTHON, H.DOCKER])
                self.assertEqual(len(ports.closes), 2)
                self.assertEqual({v['path']: v['position'] for v in ports.handles.values()}, LENGTHS)
                self.assertTrue(memory.events)
                if phase == 'postread':
                    self.assertEqual([name for name, raw in memory.sinks], ['source-after.json'])

    def test_each_host_phase_refuses_tool_hash_drift_through_real_verifier(self):
        for phase in ('admit', 'before_target', 'postread'):
            with self.subTest(phase=phase):
                ports = StreamPorts()
                # Construct consistent synthetic gate/concrete metadata around
                # the wrong expected tool hash, then exercise real raw custody.
                ports.tools['python']['sha256'] = 'f' * 64
                memory = PhaseMemory(ports)
                with self.assertRaisesRegex(ValueError, 'RAW_TOOL_EXPECTED_SHA_LENGTH'):
                    memory.run(phase)
                self.assertEqual([p for p, flags in ports.opens], [H.PYTHON])
                self.assertEqual(len(ports.closes), 1)
                self.assertEqual(memory.sinks, [])

    def test_each_host_phase_refuses_tool_deadline_after_read_with_owned_close(self):
        for phase in ('admit', 'before_target', 'postread'):
            with self.subTest(phase=phase):
                ports = StreamPorts()
                memory = PhaseMemory(ports)
                original_read = ports.read
                def expire_after_read(fd, size):
                    block = original_read(fd, size)
                    ports.check_error_at = ports.checks + 1
                    return block
                ports.read = expire_after_read
                with self.assertRaises(ValueError) as caught:
                    memory.run(phase)
                self.assertIs(caught.exception, ports.deadline_error)
                self.assertEqual(len(ports.reads), 1)
                self.assertEqual(len(ports.closes), 1)
                self.assertEqual(memory.sinks, [])

    def test_each_phase_reopens_and_remeasures_tools_no_cached_success(self):
        ports = StreamPorts()
        memory = PhaseMemory(ports)
        memory.run('admit')
        memory.run('before_target')
        ports.corrupt_bytes = True
        with self.assertRaisesRegex(ValueError, 'RAW_TOOL_EXPECTED_SHA_LENGTH'):
            memory.run('postread')
        self.assertEqual([p for p, flags in ports.opens], [H.PYTHON, H.DOCKER, H.PYTHON, H.DOCKER, H.PYTHON])
        self.assertEqual(len(ports.closes), 5)
        self.assertEqual(memory.sinks, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
