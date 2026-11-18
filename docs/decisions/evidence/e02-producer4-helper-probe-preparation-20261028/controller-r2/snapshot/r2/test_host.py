"""Unexecuted SOURCE controls for actual Host source/intent/probe decisions.

All bytes,522 guard members,65 RPC pairs and266 observations are synthetic.
Path alias queries/walk/raw reads are mocked in memory. These controls do not
establish real guard custody, OS-handle safety, Docker isolation or helper/pipe
lifecycle. Host.verify, sources, intent/create_args and validate_probe are real.
"""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r1')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load('probe_host_control_subject', Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2/host.py'))
C = load('probe_host_core_control_subject', ROOT / 'controller.py')
NS = 1_000_000_000
PLAN_SHA = 'a' * 64
INSTANCE = 'b' * 32


def descriptor(path, raw):
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def make_plan():
    return {'runId': '1' * 32, 'creationNonce': '2' * 32,
            'name': 'nbdp-helper-probe-' + '1' * 32 + '-' + '2' * 32,
            'uidGid': '1000:1000', 'inputRoot': '/memory/staged',
            'controlRoot': '/memory/control', 'outputRoot': '/memory/output',
            'lease': descriptor('/memory/original-lease.json', b'synthetic lease'),
            'guardRoot': '/tmp/nbdp-e02-minimal-rs-v7/guard-python',
            'source8': [descriptor('/memory/source/' + n, ('synthetic ' + n).encode()) for n in C.SOURCE_NAMES]}


def make_host(value, constants=None):
    host = H.Host(C, None, constants or {}, {}, {}, {}, {}, SimpleNamespace(sample=lambda: None))
    host.output = Path(value['outputRoot'])
    return host


class SourceMemory:
    def __init__(self):
        self.plan = make_plan()
        self.root = Path(self.plan['guardRoot'])
        self.raw, self.modes = {}, {}
        self.aliases = set()
        self.checked, self.reads = [], []
        for d in self.plan['source8']:
            self.raw[d['path']] = ('synthetic ' + Path(d['path']).name).encode()
            self.modes[d['path']] = 0o640
            staged = str(Path(self.plan['inputRoot']) / Path(d['path']).name)
            self.raw[staged], self.modes[staged] = self.raw[d['path']], 0o600
        files = {}
        self.members = ['member-%03d' % n for n in range(522)]
        for n, name in enumerate(self.members):
            raw = ('guard member %d' % n).encode()
            path = str(self.root / 'bin' / name)
            self.raw[path], self.modes[path] = raw, 0o755 if n % 2 else 0o644
            files['bin/' + name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                   'mode': self.modes[path]}
        raw = C.encoded({'fileCount': 522, 'files': files})
        self.plan['guardManifest'] = descriptor('/memory/guard-manifest.json', raw)
        self.raw['/memory/guard-manifest.json'], self.modes['/memory/guard-manifest.json'] = raw, 0o600
        self.host = make_host(self.plan, {'sourceModes': {n: 0o640 for n in C.SOURCE_NAMES}})
        self.staged_names = list(C.SOURCE_NAMES)

    def check(self):
        self.checked.append(True)

    def raw_read(self, path, cap, check=lambda: None):
        # Exercise real safe()/verify() decisions over fake path properties;
        # regular-handle/no-follow behavior remains Host.raw_read's own scope.
        path = str(H.safe(path))
        check()
        self.reads.append(path)
        raw = self.raw[path]
        if len(raw) > cap:
            raise ValueError('MOCK_RAW_READ_CAP')
        return raw, self.modes[path]

    def walk(self, root, followlinks):
        assert str(root) == str(self.root) and followlinks is False
        return [(str(self.root), ['bin'], []), (str(self.root / 'bin'), [], list(self.members))]

    def iterdir(self, path):
        assert str(path) == self.plan['inputRoot']
        return iter(Path(path) / n for n in self.staged_names)

    def run(self, staged=False):
        with patch.object(H, 'raw_read', self.raw_read), patch.object(H.os, 'walk', self.walk), \
             patch.object(Path, 'is_symlink', lambda path: str(path) in self.aliases), \
             patch.object(Path, 'iterdir', lambda path: self.iterdir(path)):
            return self.host.sources(self.plan, self.check, staged=staged)


def inspect_for_intent(intent):
    inherited = dict(v.split('=', 1) for v in intent['imageEnvironment'])
    inherited.update(v.split('=', 1) for v in intent['environment'])
    return {'Config': {'User': intent['uidGid'], 'Entrypoint': ['/usr/local/bin/node'],
                       'Cmd': ['/input/probe-guard-helper.mjs'], 'WorkingDir': '/input',
                       'Env': [k + '=' + v for k, v in inherited.items()]},
            'HostConfig': {'NetworkMode': 'none', 'IpcMode': 'private', 'ReadonlyRootfs': True,
                           'Privileged': False, 'CapDrop': ['ALL'], 'SecurityOpt': ['no-new-privileges'],
                           'Memory': 1073741824, 'MemorySwap': 1073741824, 'NanoCpus': 1000000000,
                           'PidsLimit': 128, 'Init': True, 'LogConfig': {'Type': 'none', 'Config': {}},
                           'Tmpfs': {'/tmp': 'rw,nosuid,nodev,noexec,size=16m'}},
            'Mounts': [{'Type': 'bind', 'Source': a, 'Destination': b, 'RW': c} for a, b, c in intent['mounts']],
            'NetworkSettings': {'Ports': {}}}


def fresh_trace():
    plan = make_plan()
    initial = {'Utc': 1000 * NS, 'Mono': 2000 * NS, 'Boot': 3000 * NS}
    lease = {'bootId': 'synthetic-boot'}
    for k, value in initial.items():
        lease['issued' + k + 'Ns'] = value - NS
        lease['deadline' + k + 'Ns'] = value + 1800 * NS
    helper = next(d for d in plan['source8'] if d['path'].endswith('/guard-helper.py'))
    launch = ['--inhibit-cache', '--library-path', '/guard-python/lib', '/guard-python/bin/python3.11',
              '-B', '-P', '-S', '-s', '/input/guard-helper.py', INSTANCE, plan['lease']['sha256'],
              str(helper['bytes']), helper['sha256']]
    rows = []
    def row(name, **fields):
        rows.append({'name': name, 'fields': {'helperInstance': INSTANCE, **fields}})
    row('GUARD_HELPER_LAUNCH', executable='/guard-python/lib/ld-linux-x86-64.so.2', argv=launch)
    row('GUARD_HELPER_CREATED', pid=321)
    for index in range(1, 66):
        close = index == 65
        seq = str(index)
        label = 'owner-close' if close else 'probe:warm-' + str(index - 1)
        now = {k: v + index * 1_000_000 for k, v in initial.items()}
        request = {'schema': 'e02-fresh-guard-request-v1', 'operation': 'CLOSE' if close else 'CHECK',
                   'instance': INSTANCE, 'runId': plan['runId'], 'leaseSha256': plan['lease']['sha256'],
                   'sequence': seq, 'label': label,
                   'contextSha256': hashlib.sha256(b'' if close else str(index - 1).encode()).hexdigest()}
        request_raw = C.encoded(request)
        clocks = None if close else {**{k: str(v + 500) for k, v in now.items()}, 'bootId': lease['bootId']}
        reply = {**request, 'schema': 'e02-fresh-guard-response-v1', 'requestSha256': hashlib.sha256(request_raw).hexdigest(),
                 'ok': True, 'clocks': clocks}
        row('GUARD_ENTRY', label=label, guardSequence=seq, enqueueMonoNs=str(now['Mono']))
        row('GUARD_RPC_REQUEST', label=label, guardSequence=seq,
            rawBase64=base64.b64encode(request_raw).decode(), enqueueMonoNs=str(now['Mono']),
            decisionDeadlineMonoNs=str(now['Mono'] + 5 * NS), enqueueUtcLowerNs=str(now['Utc']),
            enqueueBootLowerNs=str(now['Boot']), decisionDeadlineUtcNs=str(now['Utc'] + 5 * NS),
            decisionDeadlineBootNs=str(now['Boot'] + 5 * NS))
        row('GUARD_RPC_REPLY', guardSequence=seq, rawBase64=base64.b64encode(C.encoded(reply)).decode())
        row('GUARD_EXIT', label=label, guardSequence=seq, ok=True, error=None, consumed=True,
            consumedUtcUpperNs=str(now['Utc'] + 1000), consumedMonoNs=str(now['Mono'] + 1000),
            consumedBootUpperNs=str(now['Boot'] + 1000))
    row('GUARD_HELPER_STDOUT_EOF')
    row('GUARD_HELPER_STDERR_EOF')
    row('GUARD_HELPER_EXIT', code=0, signal=None)
    row('GUARD_HELPER_CLOSE', code=0, signal=None, stdoutEOF=True, stderrEOF=True, exitSeen=True)
    value = {'schema': 'e02-owned-fresh-guard-latency-probe-v1', 'checks': 64, 'timerMilliseconds': 10,
             'elapsedNanoseconds': '100000000', 'clientRowsQualified': 0, 'relayCause': 'UNKNOWN',
             'scope': 'OWNED_HELPER_LATENCY_TIMER_DISPATCH_ONLY', 'durationsNanoseconds': ['1000'] * 64,
             'timerRows': [{'monoNs': str(initial['Mono']), 'gapNs': '0'},
                           {'monoNs': str(initial['Mono'] + 10_000_000), 'gapNs': '10000000'}],
             'guardController': {'schema': 'e02-controller-guard-audit-v1', 'reservationIndex': None,
                                 'instance': INSTANCE, 'scope': 'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',
                                 'runId': plan['runId'], 'leaseSha256': plan['lease']['sha256'],
                                 'configurationSha256': PLAN_SHA, 'observations': rows}}
    return value, plan, lease


def event(value, name, index=0):
    return [r['fields'] for r in value['guardController']['observations'] if r['name'] == name][index]


def change_wire(value, name, changes, index=0):
    fields = event(value, name, index)
    wire = H.strict(base64.b64decode(fields['rawBase64']))
    wire.update(changes)
    fields['rawBase64'] = base64.b64encode(C.encoded(wire)).decode()


# R2 entry-only binding delta: host.py is R2; controller.py/finite_child.py remain exact R1.
class EntryMemory:
    """Only the real main() pre-import rejection path; no successful grant."""
    def __init__(self):
        self.raw, self.reads = {}, []
        self.plan = {'runId': '1' * 32, 'creationNonce': '2' * 32,
                     'gates': {key: descriptor('/memory/' + key, b'gate-not-read') for key in C.GATE_KEYS}}
        self.runtime = []
        for name in ('controller.py', 'host.py', 'finite_child.py'):
            path = str(H.HERE / name if name == 'host.py' else ROOT / name)
            raw = ('synthetic reviewed code ' + name + '\n').encode()
            self.raw[path] = raw
            self.runtime.append(descriptor(path, raw))
        subject = {'schema': 'e02-one-cid-helper-probe-controller-source-v1',
                   'runtimeSources': self.runtime,
                   'constants': descriptor('/memory/constants.json', b'not-read')}
        subject_raw = C.encoded(subject)
        self.raw['/memory/source-subject.json'] = subject_raw
        self.subject_pin = descriptor('/memory/source-subject.json', subject_raw)
        self.release = {'schema': 'e02-one-cid-helper-probe-root-release-v1', 'actor': '/root',
                        'executionAuthorized': True, 'runId': self.plan['runId'],
                        'creationNonce': self.plan['creationNonce'], 'subject': self.subject_pin,
                        'plan': None, 'gates': self.plan['gates'],
                        'authors': ['/root/completion_wrapper'], 'operators': ['/root'],
                        'outerCustodyReservationBytes': 65536}

    def documents(self):
        raw = C.encoded(self.plan)
        self.raw['/memory/plan.json'] = raw
        plan_pin = descriptor('/memory/plan.json', raw)
        self.release['plan'] = plan_pin
        raw = C.encoded(self.release)
        self.raw['/memory/release.json'] = raw
        release_pin = descriptor('/memory/release.json', raw)
        return plan_pin, release_pin

    def raw_read(self, path, cap, check=lambda: None):
        check()
        path = str(path)
        self.reads.append(path)
        if path not in self.raw:
            raise AssertionError('Unexpected pre-import raw read: ' + path)
        raw = self.raw[path]
        if len(raw) > cap:
            raise AssertionError('Unexpected admission cap')
        return raw, 0o600

    def reject(self, test, pattern, wrong_sha=None):
        plan_pin, release_pin = self.documents()
        args = ['--plan', plan_pin['path'], '--plan-sha', plan_pin['sha256'],
                '--root-release', release_pin['path'], '--root-release-sha', release_pin['sha256']]
        if wrong_sha is not None:
            args[args.index(wrong_sha) + 1] = '0' * 64
        clock = {'Utc': 1000 * NS, 'Mono': 2000 * NS, 'Boot': 3000 * NS, 'bootId': 'synthetic-boot'}
        fake_sys = SimpleNamespace(flags=SimpleNamespace(isolated=True),
                                   dont_write_bytecode=True, executable=H.PYTHON)
        with patch.object(H, 'raw_read', self.raw_read), \
             patch.object(H, 'bootstrap_sample', lambda: dict(clock)), \
             patch.object(H, 'sys', fake_sys), \
             patch.object(Path, 'resolve', lambda path: Path(H.PYTHON)), \
             patch.object(Path, 'is_symlink', lambda path: False), \
             patch.object(H, 'import_pinned', side_effect=AssertionError('NO_REVIEWED_IMPORT_ALLOWED')) as imports, \
             patch.object(H.Host, 'cli', side_effect=AssertionError('NO_DOCKER_ALLOWED')) as cli, \
             patch.object(H, 'private_roots', side_effect=AssertionError('NO_ROOT_CREATION_ADMISSION')) as roots:
            with test.assertRaisesRegex(ValueError, pattern):
                H.main(args)
            imports.assert_not_called()
            cli.assert_not_called()
            roots.assert_not_called()


class HostControls(unittest.TestCase):
    def reject_trace(self, mutate, pattern=None):
        value, plan, lease = fresh_trace()
        mutate(value, plan, lease)
        with self.assertRaises((ValueError, TypeError, KeyError)) as caught:
            H.validate_probe(C.encoded(value), plan, PLAN_SHA, C, lease)
        if pattern:
            self.assertRegex(str(caught.exception), pattern)

    def test_main_each_null_gate_refuses_before_reviewed_import_or_docker(self):
        for key in C.GATE_KEYS:
            with self.subTest(gate=key):
                memory = EntryMemory()
                memory.plan['gates'][key] = None
                memory.reject(self, 'NULL_GATE_NO_DOCKER')
                self.assertNotIn('/memory/source-subject.json', memory.reads)

    def test_main_wrong_external_plan_or_release_sha_before_reviewed_import(self):
        for flag in ('--plan-sha', '--root-release-sha'):
            with self.subTest(flag=flag):
                memory = EntryMemory()
                memory.reject(self, 'EXTERNAL_ROOT_PINS', wrong_sha=flag)
                self.assertNotIn('/memory/source-subject.json', memory.reads)

    def test_main_false_root_authorization_before_reviewed_import(self):
        memory = EntryMemory()
        memory.release['executionAuthorized'] = False
        memory.reject(self, 'EXTERNAL_ONE_USE_ROOT_RELEASE')
        self.assertNotIn('/memory/source-subject.json', memory.reads)

    def test_main_each_corrupt_expected_runtime_source_pin_before_any_reviewed_import(self):
        for name in ('controller.py', 'host.py', 'finite_child.py'):
            for same_size in (False, True):
                with self.subTest(name=name, same_size=same_size):
                    memory = EntryMemory()
                    path = str(H.HERE / name if name == 'host.py' else ROOT / name)
                    original = memory.raw[path]
                    memory.raw[path] = b'X' + original[1:] if same_size else original + b'# drift\n'
                    memory.reject(self, 'EXPECTED_PIN_DRIFT')
                    self.assertIn('/memory/source-subject.json', memory.reads)
                    self.assertIn(path, memory.reads)
                    self.assertNotIn('/memory/constants.json', memory.reads)

    def test_source8_and_guard522_expected_positive(self):
        memory = SourceMemory()
        memory.run()
        self.assertEqual(len([x for x in memory.reads if '/bin/member-' in x]), 522)
        self.assertGreaterEqual(len(memory.checked), 523)
        self.assertEqual(set(C.SOURCE_NAMES), set(memory.host.constants['sourceModes']))

    def test_source_expected_hash_and_size_are_not_adopted_from_observed_bytes(self):
        for same_size in (False, True):
            with self.subTest(same_size=same_size):
                memory = SourceMemory()
                path = memory.plan['source8'][3]['path']
                memory.raw[path] = (b'X' + memory.raw[path][1:]) if same_size else memory.raw[path] + b'x'
                with self.assertRaisesRegex(ValueError, 'EXPECTED_PIN_DRIFT'):
                    memory.run()
                self.assertFalse(any('/bin/member-' in p for p in memory.reads))

    def test_source_mode_drift_rejected(self):
        memory = SourceMemory()
        memory.modes[memory.plan['source8'][0]['path']] = 0o777
        with self.assertRaisesRegex(ValueError, 'EXPECTED_SOURCE_MODE'):
            memory.run()

    def test_source_or_guard_ancestor_alias_rejected_by_actual_safe(self):
        for path in ('/memory/source', '/tmp/nbdp-e02-minimal-rs-v7'):
            with self.subTest(alias=path):
                memory = SourceMemory()
                memory.aliases.add(path)
                with self.assertRaisesRegex(ValueError, 'NO_PATH_SYMLINK'):
                    memory.run()

    def test_guard_manifest_expected_pin_drift_rejected(self):
        memory = SourceMemory()
        memory.raw[memory.plan['guardManifest']['path']] += b' '
        with self.assertRaisesRegex(ValueError, 'EXPECTED_PIN_DRIFT'):
            memory.run()

    def test_guard_manifest522_semantic_count_not_just_valid_hash(self):
        memory = SourceMemory()
        path = memory.plan['guardManifest']['path']
        manifest = H.strict(memory.raw[path])
        manifest['fileCount'] = 521
        memory.raw[path] = C.encoded(manifest)
        memory.plan['guardManifest'] = descriptor(path, memory.raw[path])
        with self.assertRaisesRegex(ValueError, 'GUARD522'):
            memory.run()

    def test_guard_member_hash_size_and_mode_drift_rejected(self):
        for kind in ('hash', 'size', 'mode'):
            with self.subTest(kind=kind):
                memory = SourceMemory()
                path = str(memory.root / 'bin' / memory.members[100])
                if kind == 'mode':
                    memory.modes[path] ^= 0o010
                elif kind == 'size':
                    memory.raw[path] += b'x'
                else:
                    memory.raw[path] = b'X' + memory.raw[path][1:]
                with self.assertRaisesRegex(ValueError, 'GUARD_MEMBER_PIN_OR_MODE'):
                    memory.run()

    def test_guard_missing_extra_and_directory_alias_rejected(self):
        for kind in ('missing', 'extra', 'alias'):
            with self.subTest(kind=kind):
                memory = SourceMemory()
                if kind == 'missing':
                    memory.members.pop()
                    pattern = 'EXACT_GUARD_MEMBERSHIP'
                elif kind == 'extra':
                    memory.members.append('undeclared')
                    pattern = 'NO_UNDECLARED_GUARD_MEMBER'
                else:
                    memory.aliases.add(str(memory.root / 'bin'))
                    pattern = 'GUARD_NO_DIRECTORY_ALIAS'
                with self.assertRaisesRegex(ValueError, pattern):
                    memory.run()

    def test_staged_exact_source_bytes_mode_and_members_positive(self):
        memory = SourceMemory()
        memory.run(staged=True)
        self.assertEqual(len([p for p in memory.reads if p.startswith('/memory/staged/')]), 8)

    def test_staged_bytes_mode_extra_and_missing_member_rejected(self):
        for kind in ('bytes', 'mode', 'extra', 'missing'):
            with self.subTest(kind=kind):
                memory = SourceMemory()
                path = str(Path(memory.plan['inputRoot']) / C.SOURCE_NAMES[0])
                if kind == 'bytes':
                    memory.raw[path] += b'x'
                elif kind == 'mode':
                    memory.modes[path] = 0o644
                elif kind == 'extra':
                    memory.staged_names.append('injected.mjs')
                else:
                    memory.staged_names.pop()
                with self.assertRaisesRegex(ValueError, 'STAGED_SOURCE_DRIFT|STAGED_EXACT_EIGHT_MEMBERS'):
                    memory.run(staged=True)

    def test_source_checks_propagate_deadline_failure(self):
        memory = SourceMemory()
        failure = ValueError('ABSOLUTE_PHASE30')
        def check():
            raise failure
        memory.check = check
        with self.assertRaises(ValueError) as caught:
            memory.run()
        self.assertIs(caught.exception, failure)
        self.assertEqual(memory.reads, [])

    def test_intent_three_labels_exact_environment_and_four_mounts(self):
        plan = make_plan()
        host = make_host(plan)
        intent = host.intent(plan, PLAN_SHA)
        self.assertEqual(intent['labels'], {'nbdp.run': plan['runId'], 'nbdp.role': 'helper-probe', 'nbdp.creation': plan['creationNonce']})
        env = dict(v.split('=', 1) for v in intent['environment'])
        self.assertEqual(env, {**C.GUEST_ENV, 'NBDP_LEASE_SHA256': plan['lease']['sha256'], 'NBDP_MINIMUM_RUN_CONFIG_SHA256': PLAN_SHA})
        self.assertEqual(intent['mounts'], [[plan['inputRoot'], '/input', False], [plan['guardRoot'], '/guard-python', False],
                                           ['/memory/output/lease.json', '/session/lease.json', False],
                                           [plan['controlRoot'], '/session/control', True]])
        self.assertEqual(intent['cidfile'], '/memory/output/container.cid')

    def test_create_args_fixed_flags_labels_mounts_env_no_extra_operand(self):
        plan = make_plan()
        host = make_host(plan)
        intent = host.intent(plan, PLAN_SHA)
        args = host.create_args(intent)
        prefix = ['create', '--pull=never', '--name', intent['name'], '--cidfile', intent['cidfile'], '--network', 'none', '--ipc', 'private',
                  '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--user', '1000:1000',
                  '--cpus', '1', '--memory', '1024m', '--memory-swap', '1024m', '--pids-limit', '128', '--init',
                  '--log-driver', 'none', '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=16m', '--workdir', '/input', '--entrypoint', '/usr/local/bin/node']
        expected = list(prefix)
        for key, val in intent['labels'].items():
            expected += ['--label', key + '=' + val]
        for source, destination, rw in intent['mounts']:
            expected += ['--mount', 'type=bind,src=' + source + ',dst=' + destination + ('' if rw else ',readonly')]
        for env in intent['environment']:
            expected += ['--env', env]
        self.assertEqual(args, expected + [C.IMAGE, '/input/probe-guard-helper.mjs'])
        self.assertEqual(args.count('--mount'), 4)
        self.assertEqual(args.count('--label'), 3)
        self.assertNotIn('/var/run/docker.sock', ' '.join(args))

    def test_isolation_inherited_cached_env_and_explicit_overrides_positive(self):
        plan = make_plan()
        intent = make_host(plan).intent(plan, PLAN_SHA)
        intent['imageEnvironment'] = ['PATH=/image/bin', 'NODE_VERSION=synthetic']
        row = inspect_for_intent(intent)
        row['Config']['Env'].reverse()  # Environment order has no identity meaning.
        C.isolation(row, intent)
        self.assertIn('NODE_VERSION=synthetic', row['Config']['Env'])
        self.assertIn('PATH=' + C.GUEST_ENV['PATH'], row['Config']['Env'])

    def test_isolation_cached_env_wrong_extra_duplicate_and_host_bridge_rejected(self):
        for kind in ('wrong', 'extra', 'duplicate', 'bridge'):
            with self.subTest(kind=kind):
                plan = make_plan()
                intent = make_host(plan).intent(plan, PLAN_SHA)
                intent['imageEnvironment'] = ['NODE_VERSION=synthetic']
                row = inspect_for_intent(intent)
                if kind == 'wrong':
                    row['Config']['Env'].remove('NODE_VERSION=synthetic')
                    row['Config']['Env'].append('NODE_VERSION=foreign')
                elif kind == 'extra':
                    row['Config']['Env'].append('UNADMITTED=extra')
                elif kind == 'duplicate':
                    row['Config']['Env'].append(row['Config']['Env'][0])
                else:
                    intent['imageEnvironment'].append('DISPLAY=:0')
                    row['Config']['Env'].append('DISPLAY=:0')
                with self.assertRaisesRegex(ValueError, 'EXACT_GUEST_ENVIRONMENT|NO_DUPLICATE_ENVIRONMENT'):
                    C.isolation(row, intent)

    def test_isolation_each_four_mount_substitution_and_added_fifth_rejected(self):
        for index in range(5):
            with self.subTest(index=index):
                plan = make_plan()
                intent = make_host(plan).intent(plan, PLAN_SHA)
                intent['imageEnvironment'] = []
                row = inspect_for_intent(intent)
                if index == 4:
                    row['Mounts'].append({'Type': 'bind', 'Source': '/foreign', 'Destination': '/foreign', 'RW': True})
                else:
                    row['Mounts'][index]['Source'] += '-foreign'
                with self.assertRaisesRegex(ValueError, 'EXACT_FOUR_MOUNTS'):
                    C.isolation(row, intent)

    def test_probe266_rows_fresh65_explicit_positive_is_synthetic_only(self):
        value, plan, lease = fresh_trace()
        rows = value['guardController']['observations']
        self.assertEqual(len(rows), 266)
        self.assertEqual(sum(r['name'] == 'GUARD_RPC_REQUEST' for r in rows), 65)
        self.assertIsNone(H.validate_probe(C.encoded(value), plan, PLAN_SHA, C, lease))
        self.assertEqual(value['clientRowsQualified'], 0)
        self.assertEqual(value['relayCause'], 'UNKNOWN')

    def test_probe_closed_top_audit_observation_and_field_keys(self):
        mutations = [lambda v: v.update(extra=True), lambda v: v['guardController'].update(extra=True),
                     lambda v: v['guardController']['observations'][0].update(extra=True),
                     lambda v: event(v, 'GUARD_ENTRY').update(extra=True)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.reject_trace(lambda v, p, l: mutate(v), 'CLOSED_')

    def test_probe_raw_request_context_sequence_and_operation_substitutions(self):
        mutations = [{'contextSha256': '0' * 64}, {'sequence': '2'}, {'label': 'other'},
                     {'operation': 'CLOSE'}, {'runId': 'e' * 32}, {'leaseSha256': 'f' * 64}]
        for changes in mutations:
            with self.subTest(changes=changes):
                self.reject_trace(lambda v, p, l: change_wire(v, 'GUARD_RPC_REQUEST', changes), 'EXACT_REQUEST_CONTEXT')

    def test_probe_raw_request_bytes_hash_join_not_just_parsed_object(self):
        def mutate(v, p, l):
            row = event(v, 'GUARD_RPC_REQUEST')
            row['rawBase64'] = base64.b64encode(base64.b64decode(row['rawBase64']) + b'\n').decode()
        self.reject_trace(mutate, 'ONE_USE_BOUND_REPLY')

    def test_probe_reply_requesthash_context_ok_and_extra_flags_rejected(self):
        for changes in ({'requestSha256': '0' * 64}, {'sequence': '2'}, {'ok': False}, {'extra': True}):
            with self.subTest(changes=changes):
                self.reject_trace(lambda v, p, l: change_wire(v, 'GUARD_RPC_REPLY', changes), 'ONE_USE_BOUND_REPLY')

    def test_probe_request_reply_raw_bounds_newline_and_invalid_base64(self):
        for name, kind in [('GUARD_RPC_REQUEST', 'large'), ('GUARD_RPC_REPLY', 'large'),
                           ('GUARD_RPC_REQUEST', 'newline'), ('GUARD_RPC_REPLY', 'newline'), ('GUARD_RPC_REQUEST', 'base64')]:
            with self.subTest(name=name, kind=kind):
                def mutate(v, p, l):
                    row = event(v, name)
                    raw = base64.b64decode(row['rawBase64'])
                    row['rawBase64'] = ('!!!' if kind == 'base64' else base64.b64encode(
                        raw.rstrip(b'\n') if kind == 'newline' else raw + b' ' * 2100 + b'\n').decode())
                self.reject_trace(mutate)

    def test_probe_each_clock5_deadline_and_consumed_boundaries_rejected(self):
        triples = [('enqueueMonoNs', 'decisionDeadlineMonoNs', 'consumedMonoNs'),
                   ('enqueueUtcLowerNs', 'decisionDeadlineUtcNs', 'consumedUtcUpperNs'),
                   ('enqueueBootLowerNs', 'decisionDeadlineBootNs', 'consumedBootUpperNs')]
        for initial, deadline, consumed in triples:
            for kind in ('deadline', 'at', 'before'):
                with self.subTest(domain=deadline, kind=kind):
                    def mutate(v, p, l):
                        req, commit = event(v, 'GUARD_RPC_REQUEST'), event(v, 'GUARD_EXIT')
                        if kind == 'deadline':
                            req[deadline] = str(int(req[deadline]) + 1)
                        else:
                            commit[consumed] = req[deadline] if kind == 'at' else str(int(req[initial]) - 1)
                    self.reject_trace(mutate, 'INCLUSIVE_FRESH5_COMMIT')

    def test_probe_close65_requires_close_context_and_null_clocks(self):
        for kind in ('operation', 'context', 'clocks'):
            with self.subTest(kind=kind):
                changes = ({'operation': 'CHECK'} if kind == 'operation' else
                           {'contextSha256': hashlib.sha256(b'64').hexdigest()} if kind == 'context' else
                           {'clocks': {'Utc': '1', 'Mono': '1', 'Boot': '1', 'bootId': 'synthetic-boot'}})
                self.reject_trace(lambda v, p, l: change_wire(v, 'GUARD_RPC_REPLY' if kind == 'clocks' else 'GUARD_RPC_REQUEST', changes, 64))

    def test_probe_clock_boot_lease_and_consumed_upper_join(self):
        for kind in ('boot', 'after', 'beforelease', 'expiredlease'):
            with self.subTest(kind=kind):
                def mutate(v, p, lease):
                    clocks = H.strict(base64.b64decode(event(v, 'GUARD_RPC_REPLY')['rawBase64']))['clocks']
                    if kind == 'boot':
                        clocks['bootId'] = 'foreign'
                    elif kind == 'after':
                        clocks['Mono'] = str(int(event(v, 'GUARD_EXIT')['consumedMonoNs']) + 1)
                    elif kind == 'beforelease':
                        clocks['Mono'] = str(lease['issuedMonoNs'] - 1)
                    else:
                        lease['deadlineMonoNs'] = int(event(v, 'GUARD_EXIT')['consumedMonoNs'])
                    change_wire(v, 'GUARD_RPC_REPLY', {'clocks': clocks})
                self.reject_trace(mutate, 'FRESH_ORIGINAL_CORE_CLOCK|ORIGINAL_LEASE_COMMIT')

    def test_probe_commit_sequence_consumed_error_and_enqueue_join(self):
        for kind in ('sequence', 'consumed', 'error', 'enqueue'):
            with self.subTest(kind=kind):
                def mutate(v, p, l):
                    commit = event(v, 'GUARD_EXIT')
                    if kind == 'sequence': commit['guardSequence'] = '2'
                    elif kind == 'consumed': commit['consumed'] = False
                    elif kind == 'error': commit['error'] = 'late failure'
                    else: event(v, 'GUARD_ENTRY')['enqueueMonoNs'] = '1'
                self.reject_trace(mutate, 'EXACT_CONSUMED65|ENQUEUE_JOIN')

    def test_probe_trace_order_missing_row_and_duplicate_lifecycle_rejected(self):
        for kind in ('order', 'missing', 'duplicate'):
            with self.subTest(kind=kind):
                def mutate(v, p, l):
                    rows = v['guardController']['observations']
                    if kind == 'order': rows[2], rows[3] = rows[3], rows[2]
                    elif kind == 'missing': rows.pop(2)
                    else: rows[-4] = copy.deepcopy(rows[-2])
                self.reject_trace(mutate, 'ONE_USE_TRACE_ORDER|BOUNDED_EXACT_SUCCESS_ROWS|NO_DUPLICATE_HELPER_LIFECYCLE')

    def test_probe_lifecycle_each_eof_exit_seen_code_signal_pid_denials(self):
        for kind in ('stdoutEOF', 'stderrEOF', 'exitSeen', 'exitcode', 'closecode', 'signal', 'pid'):
            with self.subTest(kind=kind):
                def mutate(v, p, l):
                    if kind in ('stdoutEOF', 'stderrEOF', 'exitSeen'): event(v, 'GUARD_HELPER_CLOSE')[kind] = False
                    elif kind == 'exitcode': event(v, 'GUARD_HELPER_EXIT')['code'] = 2
                    elif kind == 'closecode': event(v, 'GUARD_HELPER_CLOSE')['code'] = 2
                    elif kind == 'signal': event(v, 'GUARD_HELPER_EXIT')['signal'] = 'SIGTERM'
                    else: event(v, 'GUARD_HELPER_CREATED')['pid'] = 0
                self.reject_trace(mutate, 'NATURAL_HELPER_ZERO|HONEST_HELPER_EOF_EXIT_CLOSE')

    def test_probe_launch_source_pin_argv_and_executable_denials(self):
        for kind in ('bytes', 'hash', 'path', 'executable'):
            with self.subTest(kind=kind):
                def mutate(v, p, l):
                    launch = event(v, 'GUARD_HELPER_LAUNCH')
                    if kind == 'bytes': launch['argv'][-2] = '0'
                    elif kind == 'hash': launch['argv'][-1] = '0' * 64
                    elif kind == 'path': launch['argv'][8] = '/other/helper.py'
                    else: launch['executable'] = '/usr/bin/python'
                self.reject_trace(mutate, 'EXACT_ORIGINAL_FACTORY_LAUNCH')

    def test_probe_audit_run_lease_config_instance_and_owner_flags_bound(self):
        for key, wrong in [('runId', '0' * 32), ('leaseSha256', '0' * 64), ('configurationSha256', '0' * 64),
                           ('instance', 'invalid'), ('reservationIndex', 1), ('scope', 'Popen attestation')]:
            with self.subTest(key=key):
                self.reject_trace(lambda v, p, l: v['guardController'].update({key: wrong}), 'BOUND_NODE_HELPER_AUDIT')

    def test_probe_durations55_and5_strict_decimal_and_timer_gap_join(self):
        changes = [lambda v: v.update(elapsedNanoseconds=str(55 * NS)),
                   lambda v: v['durationsNanoseconds'].__setitem__(0, str(5 * NS)),
                   lambda v: v['durationsNanoseconds'].__setitem__(0, '01'),
                   lambda v: v['timerRows'][1].update(gapNs='1'),
                   lambda v: v['timerRows'][1].update(monoNs='1')]
        for i, change in enumerate(changes):
            with self.subTest(case=i):
                self.reject_trace(lambda v, p, l: change(v), 'EXACT64_DURATIONS|TIMER_GAP_JOIN')

    def test_probe_strict_json_duplicate_and_fraction_refused(self):
        value, plan, lease = fresh_trace()
        raw = C.encoded(value)
        for replacement in (b'"checks":64,"checks":64', b'"checks":64.0'):
            with self.subTest(replacement=replacement):
                mutated = raw.replace(b'"checks":64', replacement, 1)
                with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY|INTEGER_JSON'):
                    H.validate_probe(mutated, plan, PLAN_SHA, C, lease)


if __name__ == '__main__':
    unittest.main()
