"""SOURCE-only definitions for the real Controller with memory-only fake ports.

No Docker, helper, process, file, sleep or real clock is used by these controls.
An independently admitted runner may later load this module and run unittest.
Fake admission/probe validation checks orchestration, not Host pin verification or
actual inner-helper validation. CLI lifecycle flags below are simulated facts,
never evidence that a real process was reaped or that real pipes reached EOF.
"""
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path

_ROOT = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r1')
_SPEC = importlib.util.spec_from_file_location('probe_controller_control_subject', _ROOT / 'controller.py')
C = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(C)
NS = 1_000_000_000
CID = 'c' * 64
PLAN_SHA = 'a' * 64
IMAGE_CONFIG = {'Entrypoint': ['/usr/local/bin/node'], 'Env': ['PATH=/usr/local/bin:/usr/bin:/bin']}


def plan():
    run, nonce = '1' * 32, '2' * 32
    return dict(schema='e02-one-cid-helper-probe-plan-v1', scope='ONE_OWNED_HELPER_PROBE_ONLY',
                runId=run, creationNonce=nonce, name='nbdp-helper-probe-' + run + '-' + nonce,
                uidGid='1000:1000', inputRoot='/owned/input', controlRoot='/owned/control',
                outputRoot='/owned/output', dockerConfig='/owned/docker',
                lease={'path': '/owned/lease.json', 'bytes': 1, 'sha256': '3' * 64},
                source8=[{'path': '/expected/' + n, 'bytes': 1, 'sha256': '4' * 64} for n in C.SOURCE_NAMES],
                guardManifest={'path': '/expected/manifest.json', 'bytes': 1, 'sha256': '5' * 64},
                guardRoot='/tmp/nbdp-e02-minimal-rs-v7/guard-python', tools={},
                expectedImageConfigSha256=hashlib.sha256(C.encoded(IMAGE_CONFIG)).hexdigest(),
                gates={k: {'synthetic': True} for k in C.GATE_KEYS})


def cli_result(stdout=b'', stderr=b'', code=0, **changes):
    value = dict(code=code, stdout=stdout, stderr=stderr, fault=None, reaped=True,
                 stdoutEOF=True, stderrEOF=True, groupClosure=None,
                 ownership={'synthetic': True}, elapsedNs=0, reapDeadlineMonoNs=0)
    value.update(changes)
    return value


class TripleClock:
    def __init__(self):
        self.now = {'Utc': 1000 * NS, 'Mono': 2000 * NS, 'Boot': 3000 * NS, 'bootId': 'synthetic-boot'}

    def sample(self):
        return dict(self.now)

    def advance(self, amount):
        for key in ('Utc', 'Mono', 'Boot'):
            self.now[key] += amount


class FakePorts:
    """All port effects are memory-only; hooks exercise actual Controller branches."""
    def __init__(self):
        self.clock = TripleClock()
        self.commands, self.writes, self.events, self.revocations = [], [], [], []
        self.removed = False
        self.started = False
        self.admit_error = self.stage_error = self.post_error = None
        self.stage_ticks = []
        self.cli_hook = None
        self.inspect_mutate = None
        self.result_mutate = None
        self.sink_error_name = None
        self.sink_error = OSError('SHORT_IMMUTABLE_WRITE_NO_REPAIR')
        self.validated = 0
        self.postreads = 0
        self.intent_value = None
        self.last_check = None
        self.existing_names = set()
        self.cidfile_verified = []
        self.cidfile_error = None
        self.post_remaining = None
        self.revoked = None
        self.before_target_error = None
        self.before_target_calls = 0

    def sample(self):
        return self.clock.sample()

    def check_lease(self):
        self.events.append('lease')
        if self.revoked is not None:
            self.events.append('lease-denied-after-revoke')
            raise ValueError('STICKY_LEASE_REVOCATION') from self.revoked
        return self.sample()

    def admit(self, value, sha, check):
        self.events.append('admit')
        check()
        if self.admit_error:
            raise self.admit_error
        assert sha == PLAN_SHA

    def stage(self, value, ledger, check):
        self.events.append('stage')
        for amount in self.stage_ticks:
            self.clock.advance(amount)
            check()
        if self.stage_error:
            raise self.stage_error
        check()

    def before_target(self, value, check):
        self.before_target_calls += 1
        self.events.append('before-target')
        check()
        if self.before_target_error is not None:
            raise self.before_target_error

    def intent(self, value, sha):
        self.intent_value = dict(name=value['name'], uidGid=value['uidGid'],
                                 labels={'nbdp.run': value['runId'], 'nbdp.role': 'helper-probe',
                                         'nbdp.creation': value['creationNonce']},
                                 environment=['PATH=/usr/local/bin:/usr/bin:/bin', 'HOME=/tmp'],
                                 mounts=[['/owned/input', '/input', False],
                                         [value['guardRoot'], '/guard-python', False],
                                         ['/owned/lease.json', '/session/lease.json', False],
                                         ['/owned/control', '/session/control', True]])
        return self.intent_value

    def create_args(self, intent):
        return ['create', '--name', intent['name'], C.IMAGE]

    def verify_cidfile(self, cid, check):
        self.cidfile_verified.append(cid)
        check()
        assert cid == CID
        if self.cidfile_error:
            raise self.cidfile_error

    def inspect_row(self):
        i = self.intent_value
        row = dict(Id=CID, Name='/' + i['name'], Image=C.IMAGE,
                   Config=dict(Labels=dict(i['labels']), User=i['uidGid'],
                               Entrypoint=['/usr/local/bin/node'], Cmd=['/input/probe-guard-helper.mjs'],
                               WorkingDir='/input', Env=[k + '=' + v for k, v in
                                   {**dict(x.split('=', 1) for x in i.get('imageEnvironment', [])),
                                    **dict(x.split('=', 1) for x in i['environment'])}.items()]),
                   HostConfig=dict(NetworkMode='none', IpcMode='private', ReadonlyRootfs=True,
                                   Privileged=False, PortBindings={}, CapAdd=[], CapDrop=['ALL'],
                                   SecurityOpt=['no-new-privileges'], Memory=1073741824,
                                   MemorySwap=1073741824, NanoCpus=1000000000, PidsLimit=128,
                                   Init=True, Devices=[], DeviceRequests=[],
                                   LogConfig={'Type': 'none', 'Config': {}},
                                   Tmpfs={'/tmp': 'rw,nosuid,nodev,noexec,size=16m'}),
                   Mounts=[dict(Source=s, Destination=d, RW=rw, Type='bind') for s, d, rw in i['mounts']],
                   NetworkSettings={'Ports': {}},
                   State=dict(Status='exited' if self.started else 'created', Running=False,
                              ExitCode=0, OOMKilled=False))
        if self.inspect_mutate:
            self.inspect_mutate(row, self.started)
        return row

    def cli(self, args, **kwargs):
        call = dict(args=list(args), at=self.sample(), **kwargs)
        self.commands.append(call)
        self.events.append(tuple(args))
        kwargs['check']()
        if self.cli_hook:
            self.cli_hook(args, kwargs)
        if args[:2] == ['image', 'inspect']:
            result = cli_result(C.encoded([{'Id': C.IMAGE, 'Config': IMAGE_CONFIG}]))
        elif args[0] == 'create':
            result = cli_result((CID + '\n').encode())
        elif args[0] == 'start':
            self.started = True
            result = cli_result(b'{"simulatedProbe":true}\n')
        elif args[0] == 'rm':
            self.removed = True
            result = cli_result((CID + '\n').encode())
        elif args[0] == 'inspect' and self.removed:
            result = cli_result(b'[]\n', ('Error: No such object: ' + CID + '\n').encode(), 1)
        elif args[0] == 'inspect':
            result = cli_result(C.encoded([self.inspect_row()]))
        else:
            raise AssertionError('Unexpected CLI action ' + repr(args))
        if self.result_mutate:
            self.result_mutate(args, result)
        kwargs['finish_check']()
        kwargs['capture']('stdout', result['stdout'])
        kwargs['capture']('stderr', result['stderr'])
        return result

    def sink(self, name, raw):
        self.writes.append((name, raw))
        if name in self.existing_names:
            raise FileExistsError('O_EXCL_DUPLICATE_OUTPUT')
        self.existing_names.add(name)
        if name == self.sink_error_name:
            raise self.sink_error

    def revoke(self, error):
        self.revocations.append(error)
        if self.revoked is None:
            self.revoked = error

    def validate_probe(self, raw, value, sha):
        self.validated += 1
        assert raw == b'{"simulatedProbe":true}\n' and sha == PLAN_SHA

    def postread(self, value, check):
        self.postreads += 1
        self.post_remaining = check()
        if self.post_error:
            raise self.post_error


class ControllerControls(unittest.TestCase):
    def subject(self, ports=None):
        p = ports or FakePorts()
        return C.Controller(plan(), PLAN_SHA, p), p

    def assert_cleanup(self, result, p):
        self.assertEqual(result['cleanup'], {'removed': True, 'absence': True, 'unknownIdentity': False})
        rm = [v for v in p.commands if v['args'][0] == 'rm']
        self.assertEqual([v['args'] for v in rm], [['rm', '--force', CID]])
        index = p.commands.index(rm[0])
        self.assertEqual(p.commands[index - 1]['args'], ['inspect', CID])
        self.assertEqual(p.commands[index + 1]['args'], ['inspect', CID])

    def test_exact_success_is_probe_only_with_owned_cleanup(self):
        c, p = self.subject()
        result = c.run()
        self.assertTrue(result['qualified'])
        self.assert_cleanup(result, p)
        self.assertEqual([v['args'][0] for v in p.commands], ['image', 'create', 'inspect', 'start', 'inspect', 'rm', 'inspect'])
        self.assertEqual(p.validated, 1)
        self.assertEqual(p.postreads, 1)
        self.assertEqual(p.cidfile_verified, [CID])
        self.assertEqual(p.post_remaining, 20 * NS)
        self.assertEqual(result['ordinaryRowsQualified'], 0)
        self.assertEqual(result['backendCause'], 'UNKNOWN')
        self.assertIsNone(result['outerApiEvidence'])
        self.assertEqual(p.revocations, [])
        self.assertEqual(p.before_target_calls, 1)
        self.assertLess(p.events.index('before-target'), p.events.index(('start', '--attach', CID)))
        self.assertLessEqual(sum(result['chargedPhysicalBytes'].values()), 16777216)
        self.assertTrue(all(x <= 8388608 for x in result['chargedPhysicalBytes'].values()))

    def test_root_custody65536_is_reserved_inside_metadata8mib_at_construction(self):
        c, p = self.subject()
        self.assertEqual(C.ROOT_CUSTODY_RESERVATION, 65536)
        self.assertEqual(c.ledger.used, {'attached': 0, 'metadata': 65536})
        self.assertEqual(p.writes, [])
        c.ledger.charge('metadata', 8388608 - 65536)
        self.assertEqual(c.ledger.used['metadata'], 8388608)
        with self.assertRaisesRegex(ValueError, 'PHYSICAL_PROOF_LIMIT'):
            c.ledger.charge('metadata', 1)
        self.assertEqual(c.ledger.used['metadata'], 8388608)

    def test_before_target_source_drift_owns_cleanup_but_never_starts(self):
        c, p = self.subject()
        p.before_target_error = ValueError('BEFORE_TARGET_EXPECTED_SOURCE_DRIFT')
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.before_target_error)
        self.assertEqual(p.before_target_calls, 1)
        self.assertEqual(c.cid, CID)
        self.assertEqual(p.cidfile_verified, [CID])
        self.assertFalse(p.started)
        self.assertEqual(p.validated, 0)
        self.assert_cleanup(result, p)
        self.assertIs(p.revoked, c.first)

    def test_create_raw_and_lifecycle_retention_fault_preserve_known_cid_under_sticky_revoke(self):
        for name in ('cli-2-stdout.raw', 'cli-2-lifecycle.json'):
            with self.subTest(retention=name):
                c, p = self.subject()
                p.sink_error_name = name
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertEqual(c.cid, CID)
                self.assertIs(c.first, p.sink_error)
                self.assertIs(c.ledger.first, p.sink_error)
                self.assertIs(p.revoked, p.sink_error)
                self.assertEqual(p.revocations, [p.sink_error])
                self.assertIn('lease-denied-after-revoke', p.events)
                self.assertFalse(p.started)
                self.assertEqual(sum(v['args'][0] == 'create' for v in p.commands), 1)
                self.assert_cleanup(result, p)
                with self.assertRaisesRegex(ValueError, 'STICKY_LEASE_REVOCATION') as denied:
                    p.check_lease()
                self.assertIs(denied.exception.__cause__, p.sink_error)
                self.assertEqual(p.sample()['bootId'], c.t0['bootId'])
                self.assertEqual(sum(n == name for n, _ in p.writes), 1)

    def test_target_retention_fault_blocks_probe_parser_and_candidate_commit(self):
        for name in ('cli-4-stdout.raw', 'cli-4-lifecycle.json'):
            with self.subTest(retention=name):
                c, p = self.subject()
                p.sink_error_name = name
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertTrue(p.started)
                self.assertIs(c.first, p.sink_error)
                self.assertIs(p.revoked, p.sink_error)
                self.assertEqual(p.validated, 0)
                self.assertFalse(c.target_candidate)
                self.assert_cleanup(result, p)

    def test_each_null_gate_refuses_before_any_cli(self):
        for key in C.GATE_KEYS:
            with self.subTest(gate=key):
                value, p = plan(), FakePorts()
                value['gates'][key] = None
                with self.assertRaisesRegex(ValueError, 'NULL_OR_MISSING_GATE'):
                    C.Controller(value, PLAN_SHA, p)
                self.assertEqual(p.commands, [])
                self.assertEqual(p.writes, [])

    def test_source_admission_fault_prevents_stage_and_create(self):
        c, p = self.subject()
        p.admit_error = ValueError('EXPECTED_SOURCE_PIN_DRIFT')
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.admit_error)
        self.assertEqual(p.commands, [])
        self.assertNotIn('stage', p.events)
        self.assertEqual(p.postreads, 1)

    def test_stage_fault_prevents_image_create_and_target(self):
        c, p = self.subject()
        p.stage_error = ValueError('SOURCE_MEMBER_OR_MODE_DRIFT')
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.stage_error)
        self.assertEqual(p.commands, [])

    def test_isolation_failures_still_fresh_owned_remove_and_absence(self):
        changes = [lambda r: r['HostConfig'].update(NetworkMode='bridge'),
                   lambda r: r['Config'].update(User='0:0'),
                   lambda r: r['Mounts'][0].update(RW=True),
                   lambda r: r['HostConfig'].update(Memory=2),
                   lambda r: r['HostConfig'].update(ReadonlyRootfs=False)]
        for change in changes:
            with self.subTest(mutation=changes.index(change)):
                c, p = self.subject()
                p.inspect_mutate = lambda row, started: change(row)
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertFalse(p.started)
                self.assert_cleanup(result, p)

    def test_each_immutable_identity_mismatch_forbids_remove(self):
        changes = [('cid', lambda r: r.update(Id='d' * 64)),
                   ('name', lambda r: r.update(Name='/foreign')),
                   ('image', lambda r: r.update(Image='sha256:' + 'd' * 64))]
        for key in ('nbdp.run', 'nbdp.role', 'nbdp.creation'):
            changes.append((key, lambda r, k=key: r['Config']['Labels'].update({k: 'foreign'})))
        for label, change in changes:
            with self.subTest(identity=label):
                c, p = self.subject()
                p.inspect_mutate = lambda row, started: change(row)
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertTrue(result['cleanup']['unknownIdentity'])
                self.assertFalse(p.started)
                self.assertFalse(any(v['args'][0] == 'rm' for v in p.commands))
                self.assertIn('IMMUTABLE_IDENTITY_MISMATCH', result['error'])

    def test_identity_becomes_foreign_only_at_cleanup_no_remove(self):
        c, p = self.subject()
        p.inspect_mutate = lambda row, started: row.update(Name='/replaced') if started else None
        result = c.run()
        self.assertTrue(p.started)
        self.assertFalse(result['qualified'])
        self.assertTrue(result['cleanup']['unknownIdentity'])
        self.assertFalse(any(v['args'][0] == 'rm' for v in p.commands))

    def test_inspection_capture_sink_fault_keeps_returned_identity_for_cleanup(self):
        c, p = self.subject()
        p.sink_error_name = 'cli-3-stdout.raw'
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.sink_error)
        self.assertIs(c.ledger.first, p.sink_error)
        self.assertFalse(p.started)
        self.assert_cleanup(result, p)
        self.assertEqual(sum(n == p.sink_error_name for n, _ in p.writes), 1)
        self.assertEqual(p.revocations, [p.sink_error])

    def test_cleanup_capture_sink_fault_still_remove_and_absence(self):
        c, p = self.subject()
        p.sink_error_name = 'cli-5-stdout.raw'
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.sink_error)
        self.assert_cleanup(result, p)

    def test_final_result_retention_cannot_acquire_late_success(self):
        c, p = self.subject()
        p.sink_error_name = 'result.json'
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.sink_error)
        self.assert_cleanup(result, p)

    def test_unknown_creation_has_no_retry_name_remove_or_start(self):
        variants = [dict(stdout=b'partial'), dict(code=2), dict(stderr=b'creation warning')]
        for changes in variants:
            with self.subTest(changes=changes):
                c, p = self.subject()
                p.result_mutate = lambda args, result: result.update(changes) if args[0] == 'create' else None
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertEqual(result['cleanup'], {'removed': False, 'absence': False, 'unknownIdentity': True})
                self.assertEqual(sum(v['args'][0] == 'create' for v in p.commands), 1)
                self.assertFalse(any(v['args'][0] in ('rm', 'start') for v in p.commands))
                self.assertIsNone(c.cid)

    def test_phase30_crossed_during_stage_refuses_all_cli(self):
        c, p = self.subject()
        p.stage_ticks = [10 * NS, 10 * NS, 10 * NS]
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIn('ABSOLUTE_DEADLINE', result['error'])
        self.assertEqual(p.commands, [])
        self.assertEqual(c.phase0['Boot'], c.t0['Boot'] + 30 * NS)

    def test_first_phase_remaining3_or_less_refuses_before_cli(self):
        for remain in (0, 1, 3 * NS):
            with self.subTest(remaining=remain):
                c, p = self.subject()
                for _ in range(2):
                    p.clock.advance(10 * NS)
                    c.remaining(c.phase0)
                p.clock.advance(10 * NS - remain)
                with self.assertRaisesRegex(ValueError, 'ABSOLUTE_DEADLINE|NO_BOUNDED_CHILD_FITS'):
                    c.command(['image', 'inspect', C.IMAGE], c.phase0)
                self.assertEqual(p.commands, [])

    def test_first_phase8_plus_single3_is_clamped_to_original_end(self):
        for remain, expected in ((11 * NS, 8 * NS), (7 * NS, 4 * NS), (3 * NS + 1, 1)):
            with self.subTest(remaining=remain):
                c, p = self.subject()
                for _ in range(2):
                    p.clock.advance(10 * NS)
                    c.remaining(c.phase0)
                p.clock.advance(10 * NS - remain) if remain <= 10 * NS else None
                # For R=11 start at19, not a new phase lease.
                if remain == 11 * NS:
                    c, p = self.subject()
                    p.clock.advance(10 * NS)
                    c.remaining(c.phase0)
                    p.clock.advance(9 * NS)
                c.command(['image', 'inspect', C.IMAGE], c.phase0)
                call = p.commands[0]
                self.assertEqual(call['run_ns'], expected)
                self.assertEqual(call['ends'], c.phase0)
                self.assertLessEqual(call['run_ns'] + 3 * NS, remain)

    def test_phase_expiry_after_create_routes_exact_cleanup_without_target(self):
        c, p = self.subject()
        def delay(args, kw):
            if args[0] == 'inspect' and not p.started and len(p.commands) == 3:
                for _ in range(3):
                    p.clock.advance(10 * NS)
                    kw['check']()
        p.cli_hook = delay
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertFalse(p.started)
        self.assert_cleanup(result, p)

    def test_target_budget_is_exact55_and_never_extended_by_lease(self):
        c, p = self.subject()
        result = c.run()
        target = next(v for v in p.commands if v['target'])
        self.assertEqual(target['run_ns'], 55 * NS)
        self.assertEqual(target['ends'], {k: c.t0[k] + 58 * NS for k in c.end})
        self.assertTrue(result['qualified'])
        self.assertLess(target['ends']['Boot'], c.end['Boot'])

    def test_target55_includes_last2_not_an_extra_cleanup_extension(self):
        c, p = self.subject()
        def duration(args, kw):
            if args[0] == 'start':
                for seconds in (10, 10, 10, 10, 10, 3, 2):
                    p.clock.advance(seconds * NS)
                    kw['check']()
        p.cli_hook = duration
        result = c.run()
        self.assertTrue(result['qualified'])
        target = next(v for v in p.commands if v['target'])
        self.assertEqual(p.clock.now['Boot'] - target['at']['Boot'], 55 * NS)
        self.assertEqual(target['run_ns'], 55 * NS)
        self.assert_cleanup(result, p)

    def test_target_cannot_borrow_reap_reserve_or_renew_phase(self):
        c, p = self.subject()
        def duration(args, kw):
            if args[0] == 'start':
                for seconds in (10, 10, 10, 10, 10, 8):
                    p.clock.advance(seconds * NS)
                    kw['finish_check']()
        p.cli_hook = duration
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIn('ABSOLUTE_DEADLINE', result['error'])
        self.assertEqual(sum(v['target'] for v in p.commands), 1)
        self.assertEqual(p.validated, 0)
        self.assert_cleanup(result, p)

    def test_target_less_than_full55_refuses_before_cli(self):
        c, p = self.subject()
        ends = {k: c.t0[k] + 58 * NS - 1 for k in c.end}
        with self.assertRaisesRegex(ValueError, 'FULL_TARGET55_REQUIRED'):
            c.command(['start', '--attach', CID], ends, target=True)
        self.assertEqual(p.commands, [])

    def test_actual_cli_nonzero_or_stderr_disqualifies_and_cleans(self):
        for changes in (dict(code=2), dict(stderr=b'helper stderr')):
            with self.subTest(changes=changes):
                c, p = self.subject()
                p.result_mutate = lambda args, r: r.update(changes) if args[0] == 'start' else None
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertIn('PROBE_CHILD_EXIT_STDERR', result['error'])
                self.assertEqual(p.validated, 0)
                self.assert_cleanup(result, p)

    def test_actual_cli_fault_reap_each_eof_and_forced_group_are_distinct_denials(self):
        variants = [dict(fault='timeout'), dict(reaped=False), dict(stdoutEOF=False),
                    dict(stderrEOF=False), dict(groupClosure={'signal': 'SIGKILL'})]
        for changes in variants:
            with self.subTest(changes=changes):
                c, p = self.subject()
                p.result_mutate = lambda args, r: r.update(changes) if args[0] == 'start' else None
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertIn('ACTUAL_CHILD_NATURAL_REAP_EOF_REQUIRED', result['error'])
                self.assert_cleanup(result, p)

    def test_terminal_nonzero_running_oom_still_owned_remove(self):
        changes = [dict(Status='running', Running=True), dict(ExitCode=2), dict(OOMKilled=True)]
        for change in changes:
            with self.subTest(state=change):
                c, p = self.subject()
                p.inspect_mutate = lambda row, started: row['State'].update(change) if started else None
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertIn('TERMINAL_CONTAINER_ZERO', result['error'])
                self.assert_cleanup(result, p)

    def test_rm_failure_still_independently_attempts_absence(self):
        c, p = self.subject()
        p.result_mutate = lambda args, r: r.update(code=2) if args[0] == 'rm' else None
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertFalse(result['cleanup']['removed'])
        self.assertTrue(result['cleanup']['absence'])
        self.assertEqual(p.commands[-1]['args'], ['inspect', CID])

    def test_absence_requires_exact_raw_receipt_and_lifecycle(self):
        variants = [dict(stdout=b''), dict(stderr=b'No such container'), dict(code=0),
                    dict(stderr=('Error: No such object: ' + 'e' * 64).encode()), dict(stdoutEOF=False)]
        for changes in variants:
            with self.subTest(changes=changes):
                c, p = self.subject()
                p.result_mutate = lambda args, r: r.update(changes) if p.removed and args[0] == 'inspect' else None
                result = c.run()
                self.assertFalse(result['qualified'])
                self.assertTrue(result['cleanup']['removed'])
                self.assertFalse(result['cleanup']['absence'])

    def test_cleanup_deadline_has_no_late_rm_and_no_extra_reserve(self):
        c, p = self.subject()
        def delay(args, kw):
            if args[0] == 'inspect' and len(p.commands) == 5:
                self.assertEqual(kw['ends'], {k: c.t0[k] + 48 * NS for k in c.end})
                for seconds in (10, 10, 10, 10, 8):
                    p.clock.advance(seconds * NS)
                    kw['finish_check']()
        p.cli_hook = delay
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertTrue(result['cleanup']['unknownIdentity'])
        self.assertFalse(any(v['args'][0] == 'rm' for v in p.commands))
        self.assertIn('ABSOLUTE_DEADLINE', result['error'])

    def test_cleanup_cap136_preserves_original_controller180(self):
        c, p = self.subject()
        c.cid = CID
        c.intent = p.intent(c.plan, PLAN_SHA)
        # Advance with actual remaining() observations, never invent a rollback.
        for _ in range(12):
            p.clock.advance(10 * NS)
            c.remaining(c.end, active=False)
        result = c.cleanup()
        self.assertTrue(result['absence'])
        self.assertTrue(all(v['ends'] == {k: c.t0[k] + 136 * NS for k in c.end} for v in p.commands))
        self.assertEqual(c.end, {k: c.t0[k] + 180 * NS for k in c.end})

    def test_duplicate_immutable_output_poison_refuses_create_without_repair(self):
        c, p = self.subject()
        p.existing_names.add('creation-intent.json')
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIsInstance(c.first, FileExistsError)
        self.assertIs(c.ledger.first, c.first)
        self.assertEqual(sum(n == 'creation-intent.json' for n, _ in p.writes), 1)
        self.assertFalse(any(v['args'][0] in ('create', 'start', 'rm') for v in p.commands))
        self.assertEqual(p.revocations, [c.first])

    def test_cidfile_verification_fault_keeps_known_cid_for_owned_cleanup(self):
        c, p = self.subject()
        p.cidfile_error = ValueError('EXACT_CIDFILE_BYTES_OR_IDENTITY')
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.cidfile_error)
        self.assertEqual(p.cidfile_verified, [CID])
        self.assertFalse(p.started)
        self.assert_cleanup(result, p)
        self.assertGreaterEqual(c.ledger.used['metadata'], 65)

    def test_bootstrap_t0_is_not_reset_after_source_admission_time(self):
        p = FakePorts()
        original = p.sample()
        p.clock.advance(10 * NS)
        c = C.Controller(plan(), PLAN_SHA, p, t0=original)
        self.assertEqual(c.t0, original)
        self.assertEqual(c.remaining(c.phase0), 20 * NS)
        p.stage_ticks = [10 * NS, 10 * NS]
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIn('ABSOLUTE_DEADLINE', result['error'])
        self.assertEqual(p.commands, [])
        self.assertEqual(c.end, {k: original[k] + 180 * NS for k in c.end})

    def test_postread20_deadline_is_strict_after_successful_owned_cleanup(self):
        c, p = self.subject()
        def bounded_postread(value, check):
            p.postreads += 1
            self.assertEqual(check(), 20 * NS)
            p.clock.advance(10 * NS)
            self.assertEqual(check(), 10 * NS)
            p.clock.advance(10 * NS)
            check()
        p.postread = bounded_postread
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIn('ABSOLUTE_DEADLINE', result['error'])
        self.assert_cleanup(result, p)
        self.assertEqual(p.postreads, 1)

    def test_source_postread_drift_disqualifies_after_cleanup(self):
        c, p = self.subject()
        p.post_error = ValueError('EXPECTED_SOURCE_POSTREAD_DRIFT')
        result = c.run()
        self.assertFalse(result['qualified'])
        self.assertIs(c.first, p.post_error)
        self.assert_cleanup(result, p)
        self.assertEqual(p.postreads, 1)

    def test_clock_rollback_boot_swap_utc_drift_and_gap_refuse_before_cli(self):
        changes = [dict(Mono=-1), dict(bootId='foreign'), dict(Utc=NS), dict(Boot=16 * NS, Mono=16 * NS, Utc=16 * NS)]
        for change in changes:
            with self.subTest(clock=change):
                c, p = self.subject()
                for key, amount in change.items():
                    if key == 'bootId':
                        p.clock.now[key] = amount
                    else:
                        p.clock.now[key] += amount
                with self.assertRaisesRegex(ValueError, 'CLOCK_ROLLBACK|BOOT_IDENTITY|UTC_BOOT_DRIFT|RESUMPTION_GAP'):
                    c.command(['image', 'inspect', C.IMAGE], c.phase0)
                self.assertEqual(p.commands, [])

    def test_byte_ledger_exact16mib_two8mib_owners_and_no_refund(self):
        ledger, writes = C.ByteLedger(), []
        ledger.charge('attached', 8388608)
        ledger.charge('metadata', 8388608)
        self.assertEqual(sum(ledger.used.values()), 16777216)
        with self.assertRaisesRegex(ValueError, 'PHYSICAL_PROOF_LIMIT'):
            ledger.write(lambda *a: writes.append(a), 'metadata', 'excess', b'x')
        self.assertEqual(writes, [])
        self.assertEqual(ledger.used, {'attached': 8388608, 'metadata': 8388608})

    def test_byte_ledger_each_owner8mib_limit_and_sticky_first_fault(self):
        for owner in ('attached', 'metadata'):
            with self.subTest(owner=owner):
                ledger, writes = C.ByteLedger(), []
                ledger.charge(owner, 8388608)
                with self.assertRaises(ValueError) as raised:
                    ledger.write(lambda *a: writes.append(a), owner, 'excess', b'x')
                first = raised.exception
                with self.assertRaises(ValueError) as repeated:
                    ledger.write(lambda *a: writes.append(a), 'metadata' if owner == 'attached' else 'attached', 'later', b'')
                self.assertIs(repeated.exception, first)
                self.assertIs(ledger.first, first)
                self.assertEqual(writes, [])

    def test_byte_ledger_sink_short_or_enospc_poison_no_retry_no_refund(self):
        for text in ('SHORT_IMMUTABLE_WRITE_NO_REPAIR', 'ENOSPC'):
            with self.subTest(error=text):
                ledger, writes, error = C.ByteLedger(), [], OSError(text)
                def sink(name, raw):
                    writes.append((name, raw))
                    raise error
                with self.assertRaises(OSError) as caught:
                    ledger.write(sink, 'metadata', 'proof', b'123')
                self.assertIs(caught.exception, error)
                self.assertEqual(ledger.used['metadata'], 3)
                with self.assertRaises(OSError) as again:
                    ledger.write(sink, 'metadata', 'proof', b'123')
                self.assertIs(again.exception, error)
                self.assertEqual(writes, [('proof', b'123')])
                self.assertEqual(ledger.used['metadata'], 3)


if __name__ == '__main__':
    unittest.main()
