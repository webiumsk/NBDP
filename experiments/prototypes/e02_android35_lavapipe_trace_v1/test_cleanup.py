"""Prepared mocked cleanup controls; never Docker/Android/native experiments.

Author prepares source only; independent review/root execution is required.
"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('supervisor.py')
spec = importlib.util.spec_from_file_location('e02_cleanup_subject', SOURCE)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
CID = 'c' * 64


class MockDocker:
    def __init__(self, data, remove_exit=0, log_failure=False, absent_response=None):
        self.data, self.remove_exit, self.log_failure = data, remove_exit, log_failure
        self.absent_response = absent_response
        self.calls, self.inspect_count = [], 0

    def __call__(self, argv, **unused):
        args = argv[1:]
        self.calls.append(args)
        if args[0] == 'inspect':
            self.inspect_count += 1
            if self.inspect_count == 1 or self.remove_exit:
                return subprocess.CompletedProcess(argv, 0, json.dumps([self.data]).encode(), b'')
            if self.absent_response is not None:
                code, stdout, stderr = self.absent_response
                return subprocess.CompletedProcess(argv, code, stdout, stderr)
            return subprocess.CompletedProcess(argv, 1, b'[]\n', b'Error: No such object: ' + CID.encode() + b'\n')
        if args == ['logs', CID]:
            if self.log_failure:
                return subprocess.CompletedProcess(argv, 0, b'x' * (16777216 + 1), b'')
            return subprocess.CompletedProcess(argv, 0, b'actual mocked logs', b'')
        if args == ['rm', '-f', CID]:
            return subprocess.CompletedProcess(argv, self.remove_exit, b'', b'forced removal error' if self.remove_exit else b'')
        raise AssertionError('Unexpected mocked Docker command: ' + repr(args))


class CleanupTests(unittest.TestCase):
    def runtime(self, out, foreign=False):
        runtime = subject.Runtime.__new__(subject.Runtime)
        runtime.out, runtime.docker, runtime.host_env = out, '/not-executed/docker', {}
        runtime.ids, runtime.lease_sha = {'anchor': CID}, 'd' * 64
        entry = {'name': 'nbdp-e02-' + 'a' * 32 + '-anchor', 'image': subject.RUNTIME,
                 'labels': {'nbdp.run': 'a' * 32, 'nbdp.role': 'anchor', 'nbdp.creation': 'b' * 32},
                 'command': ['fixed-command'], 'mounts': []}
        runtime.intents = {'anchor': entry}
        labels = dict(entry['labels'])
        if foreign:
            labels['nbdp.creation'] = 'f' * 32
        data = {'Id': CID, 'Name': '/' + entry['name'], 'Image': subject.RUNTIME,
                'Config': {'Labels': labels, 'Env': ['NBDP_LEASE_SHA256=' + runtime.lease_sha,
                    'NBDP_FIXTURE_PLAN_SHA256=' + subject.digest(subject.HERE / 'fixture-plan.json')],
                    'Entrypoint': [subject.PY[0]], 'Cmd': entry['command'],
                    'User': str(os.getuid()) + ':' + str(os.getgid())},
                'HostConfig': {'NetworkMode': 'none', 'Privileged': False, 'PortBindings': {},
                    'CapAdd': [], 'ReadonlyRootfs': True, 'CapDrop': ['ALL'],
                    'SecurityOpt': ['no-new-privileges'], 'Memory': 128 * 1048576,
                    'MemorySwap': 128 * 1048576, 'PidsLimit': 64, 'NanoCpus': 1000000000,
                    'Devices': [], 'CgroupnsMode': 'private', 'CgroupParent': ''}, 'Mounts': []}
        return runtime, data

    def test_log_write_failure_still_removes_owned_cid_and_checks_absence(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            runtime, data = self.runtime(Path(directory)); docker = MockDocker(data)
            original_put = subject.put
            def failed_log(path, raw):
                if str(path).endswith('-logs.stdout'):
                    raise OSError('injected diagnostic write failure')
                return original_put(path, raw)
            with patch.object(subject.subprocess, 'run', docker), patch.object(subject, 'put', side_effect=failed_log):
                result = runtime.cleanup()
            self.assertIn(['rm', '-f', CID], docker.calls)
            self.assertEqual(docker.calls[-1], ['inspect', CID])
            self.assertTrue(result['rows'][0]['absenceConfirmed'])
            self.assertFalse(result['ok']); self.assertTrue(result['errors'])

    def test_log_bound_failure_still_attempts_removal(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            runtime, data = self.runtime(Path(directory)); docker = MockDocker(data, log_failure=True)
            with patch.object(subject.subprocess, 'run', docker):
                result = runtime.cleanup()
            self.assertIn(['rm', '-f', CID], docker.calls)
            self.assertTrue(result['rows'][0]['absenceConfirmed']); self.assertFalse(result['ok'])

    def test_isolation_mismatch_does_not_block_exact_identity_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            runtime, data = self.runtime(Path(directory)); data['HostConfig']['Privileged'] = True
            docker = MockDocker(data)
            with patch.object(subject.subprocess, 'run', docker):
                result = runtime.cleanup()
            self.assertIn(['rm', '-f', CID], docker.calls)
            self.assertTrue(result['rows'][0]['identityVerified'])
            self.assertTrue(result['rows'][0]['absenceConfirmed']); self.assertFalse(result['ok'])

    def test_foreign_creation_nonce_never_removes(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            runtime, data = self.runtime(Path(directory), foreign=True); docker = MockDocker(data)
            with patch.object(subject.subprocess, 'run', docker):
                result = runtime.cleanup()
            self.assertFalse(any(args[0] == 'rm' for args in docker.calls))
            self.assertFalse(result['rows'][0]['identityVerified']); self.assertFalse(result['ok'])

    def test_cleanup_failure_forces_failed_outer_and_preserves_primary(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            out = Path(directory); runtime, data = self.runtime(out); docker = MockDocker(data, remove_exit=1)
            driver = subject.put(out / 'driver-result.json', b'raw-driver-evidence')
            with patch.object(subject.subprocess, 'run', docker):
                cleanup = runtime.cleanup()
            self.assertEqual(docker.calls[-1], ['inspect', CID])
            self.assertEqual(subject.finalize(out, {'schema': 'test'}, 'original driver failure', cleanup), 2)
            record = subject.strict((out / 'supervisor-result.json').read_bytes())
            self.assertEqual(record['executionState'], 'FAILED_UNQUALIFIED')
            self.assertEqual(record['error'], 'original driver failure'); self.assertTrue(record['secondaryErrors'])
            self.assertEqual(subject.pin(out / 'driver-result.json'), driver)

    def test_unqualified_row_cannot_be_reported_as_partial(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            out = Path(directory)
            cleanup = {'ok': True, 'errors': [], 'rows': [{'error': 'failure', 'absenceConfirmed': False}]}
            self.assertEqual(subject.finalize(out, {}, None, cleanup), 2)
            self.assertEqual(subject.strict((out / 'supervisor-result.json').read_bytes())['executionState'], 'FAILED_UNQUALIFIED')

    def test_final_result_write_failure_never_returns_zero(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            with (patch.object(subject, 'put', side_effect=OSError('injected final write failure')),
                  contextlib.redirect_stderr(io.StringIO()) as stderr):
                code = subject.finalize(Path(directory), {}, None, {'ok': True, 'errors': [], 'rows': []})
            self.assertEqual(code, 2)
            self.assertIn('FAILED_UNQUALIFIED', stderr.getvalue())

    def test_guest_module_initialization_at_input_has_no_actions(self):
        namespace = {'__file__': '/input/supervisor.py', '__name__': 'e02_inert_guest_import'}
        with patch.object(subject.subprocess, 'run') as run, patch.object(subject.subprocess, 'Popen') as popen:
            exec(compile(SOURCE.read_bytes(), '/input/supervisor.py', 'exec'), namespace)
        self.assertEqual(namespace['HERE'], Path('/input'))
        run.assert_not_called(); popen.assert_not_called()

    def test_observed_lowercase_exact_cid_absence_is_confirmed(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            runtime, data = self.runtime(Path(directory))
            response = (1, b'[]\n', b'error: no such object: ' + CID.encode() + b'\n')
            docker = MockDocker(data, absent_response=response)
            with patch.object(subject.subprocess, 'run', docker):
                result = runtime.cleanup()
            self.assertTrue(result['ok']); self.assertTrue(result['rows'][0]['absenceConfirmed'])
            self.assertIn(['rm', '-f', CID], docker.calls)

    def test_observed_container_not_found_and_case_variations_confirm_exact_cid(self):
        for prefix in (b'Error response from daemon: No such container: ',
                       b'error response from daemon: no such container: ',
                       b'ERROR: NO SUCH OBJECT: '):
            with self.subTest(prefix=prefix):
                value = subprocess.CompletedProcess([], 1, b'[]\n', prefix + CID.encode() + b'\n')
                self.assertTrue(subject.exact_cid_absent(value, CID))

    def test_exact_absence_rejects_daemon_wrong_cid_partial_or_mixed_errors(self):
        bad = [
            (1, b'[]', b'Cannot connect to the Docker daemon'),
            (1, b'[]', b'Error response from daemon: permission denied'),
            (1, b'[]', b'Error response from daemon: no such object: ' + CID.encode()),
            (1, b'[]', b'error: no such object: ' + b'f' * 64),
            (1, b'[]', b'error: no such object: ' + CID[:12].encode()),
            (1, b'[]', b'error: no such object: ' + CID.encode() + b'\npermission denied'),
            (0, b'[]', b'error: no such object: ' + CID.encode()),
            (2, b'[]', b'error: no such object: ' + CID.encode()),
            (1, b'[{"Id":"unexpected"}]', b'error: no such object: ' + CID.encode()),
            (1, b'', b'error: no such object: ' + CID.encode()),
        ]
        for code, stdout, stderr in bad:
            with self.subTest(code=code, stdout=stdout, stderr=stderr):
                value = subprocess.CompletedProcess([], code, stdout, stderr)
                self.assertFalse(subject.exact_cid_absent(value, CID))

    def test_daemon_failure_after_removal_remains_failed(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-cleanup-') as directory:
            out = Path(directory); runtime, data = self.runtime(out)
            docker = MockDocker(data, absent_response=(1, b'', b'Cannot connect to the Docker daemon'))
            with patch.object(subject.subprocess, 'run', docker):
                result = runtime.cleanup()
            self.assertIn(['rm', '-f', CID], docker.calls)
            self.assertFalse(result['rows'][0]['absenceConfirmed']); self.assertFalse(result['ok'])
            self.assertEqual(subject.finalize(out, {}, None, result), 2)

    def test_bounded_local_logging_disables_incompatible_compression(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-create-') as directory:
            out = Path(directory); runtime, _ = self.runtime(out)
            for name in ('input', 'session/control'):
                (out / name).mkdir(parents=True)
            (out / 'session/lease.json').write_bytes(b'synthetic-not-executed')
            runtime.plan = {'runId': 'a' * 32}; runtime.guard = SimpleNamespace(ENV={})
            runtime.check = lambda: None; runtime.put_json = lambda *args: None
            runtime.inspect = lambda role: {'mocked': role}
            calls = []
            def command(args):
                calls.append(args)
                return CID.encode() if args[0] == 'create' else b''
            runtime.command = command
            runtime.start('anchor')
            created = calls[0]
            self.assertEqual(created[0], 'create'); self.assertIn('--pull=never', created)
            self.assertEqual(created[created.index('--log-driver')+1], 'local')
            options = dict(created[i+1].split('=', 1)
                           for i, value in enumerate(created) if value == '--log-opt')
            self.assertEqual(options, {'max-size': '16m', 'max-file': '1', 'compress': 'false'})

    def test_service_failure_forwards_actual_binary_captures_and_preserves_exception(self):
        original = RuntimeError('original owned service timeout')
        result = {'stdout': b'actual-service-out\x00\xff', 'stderr': b'actual-service-err\n'}
        class FailedLease:
            last_result = result
            def run_checked(self, *args):
                raise original
        stdout, stderr = io.BytesIO(), io.BytesIO()
        with self.assertRaises(RuntimeError) as caught:
            subject.run_service(FailedLease(), ['not-executed'], 1800, {}, stdout, stderr)
        self.assertIs(caught.exception, original)
        self.assertEqual(stdout.getvalue(), result['stdout']); self.assertEqual(stderr.getvalue(), result['stderr'])

    def test_secondary_capture_write_failure_still_forwards_other_stream_and_keeps_primary(self):
        original = RuntimeError('original owned service refusal')
        class FailedLease:
            last_result = {'stdout': b'actual-out', 'stderr': b'actual-err'}
            def run_checked(self, *args):
                raise original
        class FailedOutput:
            def write(self, raw):
                raise OSError('injected capture forwarding failure')
        stderr = io.BytesIO()
        with contextlib.redirect_stderr(io.StringIO()) as secondary:
            with self.assertRaises(RuntimeError) as caught:
                subject.run_service(FailedLease(), ['not-executed'], 1800, {}, FailedOutput(), stderr)
        self.assertIs(caught.exception, original); self.assertEqual(stderr.getvalue(), b'actual-err')
        self.assertIn('Secondary service capture forwarding failure', secondary.getvalue())

    def test_observed_namespace_listener_forms_are_accepted_with_valid_ports(self):
        actual = [
            ('0.0.0.0:8080', '0.0.0.0:*'), ('127.0.0.1:17777', '0.0.0.0:*'),
            ('127.0.0.1:6402', '0.0.0.0:*'), ('127.0.0.1:40817', '0.0.0.0:*'),
            ('127.0.0.1:5037', '0.0.0.0:*'), ('127.0.0.1:5554', '0.0.0.0:*'),
            ('127.0.0.1:5555', '0.0.0.0:*'), ('[::1]:46217', '[::]:*'),
            ('[::1]:45203', '[::]:*'), ('[::ffff:127.0.0.1]:46217', '*:*'),
            ('[::1]:5555', '[::]:*'), ('[::1]:5554', '[::]:*'),
            ('[::1]:40817', '[::]:*'), ('[::1]:34081', '[::]:*'),
            ('[::]:8080', '[::]:*'), ('127.0.0.1:1', '0.0.0.0:*'), ('[::1]:65535', '[::]:*')]
        raw = ''.join('LISTEN 0 128 ' + local + ' ' + peer + '\n' for local, peer in actual).encode()
        rows = subject.validate_namespace_listeners(raw)
        self.assertEqual([row['endpoint'] for row in rows], [local for local, peer in actual])
        self.assertEqual(rows[9]['scope'], 'namespace-loopback')
        self.assertEqual(rows[0]['scope'], 'relay-wildcard')

    def test_archived_actual14_listener_rows_parse(self):
        saved = subject.REPO / 'docs/decisions/evidence/e02-ordinary-client-resume-r1/source-r6-before-loopback-listener-fix/listeners.txt'
        self.assertEqual(len(subject.validate_namespace_listeners(saved.read_bytes())), 14)

    def test_malformed_nonloopback_and_arbitrary_wildcard_listeners_are_refused(self):
        for local in ('192.168.1.1:8080', '10.0.0.1:5555', '[2001:db8::1]:5555',
                      '[::ffff:192.168.1.1]:5555', '0.0.0.0:5555', '[::]:5555', '*:8080',
                      'localhost:5555', '::1:5555', '[::1%lo]:5555', '127.0.0.1:0',
                      '[::1]:65536', '127.0.0.1:-1', '127.0.0.1:01', '127.0.0.1:655350',
                      '[127.0.0.1]:5555', '127.0.0.999:5555', '127.0.0.1:5555junk'):
            with self.subTest(local=local), self.assertRaises((RuntimeError, ValueError)):
                subject.validate_namespace_listeners(('LISTEN 0 128 ' + local + ' *:*\n').encode())

    def test_malformed_ss_rows_are_refused(self):
        for raw in (b'', b'\n', b'LISTEN 0 128 127.0.0.1:5555\n',
                    b'LISTEN 0 128 127.0.0.1:5555 *:* extra\n',
                    b'ESTAB 0 128 127.0.0.1:5555 *:*\n', b'LISTEN -1 128 127.0.0.1:5555 *:*\n',
                    b'LISTEN 0 128 127.0.0.1:5555 192.168.1.1:*\n', b'\xff'):
            with self.subTest(raw=raw), self.assertRaises((RuntimeError, ValueError)):
                subject.validate_namespace_listeners(raw)

    def test_only_lo_namespace_with_actual_loopback_addresses_is_accepted(self):
        lo = {'ifname': 'lo', 'flags': ['LOOPBACK', 'UP', 'LOWER_UP'], 'addr_info': [
            {'family': 'inet', 'local': '127.0.0.1', 'prefixlen': 8, 'scope': 'host'},
            {'family': 'inet6', 'local': '::1', 'prefixlen': 128, 'scope': 'host'}]}
        subject.validate_namespace_addresses(json.dumps([lo]).encode())
        bad = [[], [lo, {'ifname': 'eth0'}], [lo, lo], [{'ifname': 'eth0'}],
               [dict(lo, flags=['UP'])], [dict(lo, addr_info=[])],
               [dict(lo, addr_info=[{'family': 'inet', 'local': '10.0.0.1', 'prefixlen': 8, 'scope': 'host'}])]]
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises((RuntimeError, ValueError)):
                subject.validate_namespace_addresses(json.dumps(rows).encode())

    def test_invalid_namespace_stops_before_listener_probe_install_or_ui(self):
        calls = []
        class Runtime:
            def guest(self, role, tokens, timeout):
                calls.append(('probe', tokens))
                return b'[{"ifname":"eth0"}]'
            def put_bytes(self, *args):
                pass
            def put_json(self, *args):
                pass
            def adb(self, *args):
                calls.append(('install', args))
            def ui(self):
                calls.append(('ui',))
        runtime = Runtime()
        with self.assertRaises(RuntimeError):
            subject.qualify_namespace(runtime)
            runtime.adb(['install', '--no-streaming', '/artifact.apk'])
            runtime.ui()
        self.assertEqual(calls, [('probe', ['probe', 'ip', '-j', 'addr'])])

    def test_android_trial_generated_caps_and_guest_configuration_agree(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-e02-android-caps-') as directory:
            out = Path(directory); runtime, _ = self.runtime(out)
            for name in ('input', 'session/control', 'session/fixtures', 'android-state', 'sdk'):
                (out / name).mkdir(parents=True)
            (out / 'session/lease.json').write_bytes(b'synthetic-not-executed')
            for name in ('artifact.apk', 'helper.apk'):
                (out / name).write_bytes(b'synthetic-not-installed')
            runtime.plan = {'runId': 'a' * 32, 'sdkRoot': str(out / 'sdk'),
                            'amethystApk': {'path': str(out / 'artifact.apk')},
                            'helperApk': {'path': str(out / 'helper.apk')}}
            runtime.guard = SimpleNamespace(ENV={})
            runtime.check = lambda: None; runtime.put_json = lambda *args: None
            runtime.inspect = lambda role: {'mocked': role}; calls = []
            def command(args):
                calls.append(args)
                return ('e' * 64).encode() if args[0] == 'create' else b''
            runtime.command = command
            original_stat = subject.os.stat
            def stat(path, *args, **kwargs):
                if os.fspath(path) == '/dev/kvm':
                    return SimpleNamespace(st_gid=123)
                return original_stat(path, *args, **kwargs)
            with patch.object(subject.os, 'stat', side_effect=stat):
                runtime.start('android')
            created = calls[0]
            for option, expected in (('--memory', '8192m'), ('--memory-swap', '8192m'),
                                     ('--cpus', '8'), ('--pids-limit', '512'), ('--cgroupns', 'private'),
                                     ('--network', 'container:' + CID)):
                self.assertEqual(created[created.index(option)+1], expected)
            self.assertIn('--pull=never', created)
            config = dict(line.split('=', 1) for line in subject.CONFIG.splitlines())
            self.assertEqual(config['hw.ramSize'], '4096'); self.assertEqual(config['hw.cpu.ncore'], '4')
            self.assertEqual(subject.EMULATOR[subject.EMULATOR.index('-memory')+1], config['hw.ramSize'])
            self.assertEqual(subject.EMULATOR[subject.EMULATOR.index('-cores')+1], config['hw.cpu.ncore'])
            self.assertEqual({k: v for k, v in subject.LIMITS.items() if k != 'android'},
                             {'anchor': (128, 64, 1), 'rs-relay': (512, 128, 1), 'fixture': (1024, 128, 1)})
            self.assertEqual(sum(value[0] for value in subject.LIMITS.values()), 9856)
            # Actual strict inspector accepts quota8 and rejects otherwise
            # identical4/7/9 CPU snapshots; no Docker/SDK process is run.
            intent = runtime.intents['android']
            data = {'Id': runtime.ids['android'], 'Name': '/' + intent['name'], 'Image': intent['image'],
                'Config': {'Labels': dict(intent['labels']), 'Env': [
                    'NBDP_LEASE_SHA256=' + runtime.lease_sha,
                    'NBDP_FIXTURE_PLAN_SHA256=' + subject.digest(subject.HERE / 'fixture-plan.json')],
                    'Entrypoint': [subject.PY[0]], 'Cmd': intent['command'],
                    'User': str(os.getuid()) + ':' + str(os.getgid())},
                'HostConfig': {'NetworkMode': 'container:' + CID, 'Privileged': False,
                    'PortBindings': {}, 'CapAdd': [], 'ReadonlyRootfs': True, 'CapDrop': ['ALL'],
                    'SecurityOpt': ['no-new-privileges'], 'Memory': 8192 * 1048576,
                    'MemorySwap': 8192 * 1048576, 'PidsLimit': 512, 'NanoCpus': 8000000000,
                    'CgroupnsMode': 'private', 'CgroupParent': '',
                    'Devices': [{'PathOnHost':'/dev/kvm','PathInContainer':'/dev/kvm','CgroupPermissions':'rw'}]},
                'Mounts': [{'Type':'bind','Source':source,'Destination':target,'RW':rw}
                    for source,target,rw in intent['mounts']]}
            runtime.validate_owned('android', data)
            for quota in (4000000000, 7000000000, 9000000000):
                changed = json.loads(json.dumps(data)); changed['HostConfig']['NanoCpus'] = quota
                with self.assertRaisesRegex(RuntimeError, 'isolation/resource mismatch'):
                    runtime.validate_owned('android', changed)


    def test_android_cpu8_trial_affinity_refuses_seven_before_later_actions(self):
        calls = []
        with patch.object(subject.os, 'sched_getaffinity', return_value={0, 1, 2, 3, 4, 5, 6}) as affinity:
            with self.assertRaisesRegex(RuntimeError, 'at least8'):
                subject.require_android_affinity()
                calls.append('lease-or-service-forbidden')
        affinity.assert_called_once_with(0); self.assertEqual(calls, [])

    def test_android_cpu8_trial_affinity_accepts_eight_without_expanding_admission(self):
        with patch.object(subject.os, 'sched_getaffinity', return_value={0, 1, 2, 3, 4, 5, 6, 7}) as affinity:
            subject.require_android_affinity()
        affinity.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
