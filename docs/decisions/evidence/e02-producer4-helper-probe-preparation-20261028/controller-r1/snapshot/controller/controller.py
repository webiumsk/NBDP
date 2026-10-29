"""One-CID SOURCE preparation. Import defines functions only; no execution grant.

The injected ports are the production orchestration boundaries, not a second
controller. OS implementation lives in host.py. Outer API evidence is external.
"""
import hashlib
import json
import re

NS = 1_000_000_000
ROOT_CUSTODY_RESERVATION = 65_536
IMAGE = 'sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f'
SOURCE_NAMES = ('probe-guard-helper.mjs', 'guard-client.mjs', 'guard-client-core.mjs',
                'guard-wire.mjs', 'guard-helper.py', 'lease_guard.py',
                'capture-allocation.mjs', 'guard-transport-boundaries.mjs')
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
GUEST_ENV = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/tmp', 'TMPDIR': '/tmp',
             'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC',
             'PYTHONHOME': '/guard-python', 'OPENSSL_CONF': '/dev/null',
             'OPENSSL_MODULES': '/guard-python/lib/openssl-modules-disabled'}
PLAN_KEYS = set('schema scope runId creationNonce name uidGid inputRoot controlRoot outputRoot dockerConfig lease source8 guardManifest guardRoot tools expectedImageConfigSha256 gates'.split())
GATE_KEYS = set('producerSource producerData controllerSource sourceQa sourceSecurity controlData concreteInput'.split())


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def strict(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, 'DUPLICATE_JSON_KEY')
            out[key] = value
        return out
    def reject(_):
        raise ValueError('INTEGER_JSON_REQUIRED')
    return json.loads(raw, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)


def closed_plan(plan):
    need(type(plan) is dict and set(plan) == PLAN_KEYS, 'CLOSED_PLAN')
    need(plan['schema'] == 'e02-one-cid-helper-probe-plan-v1' and
         plan['scope'] == 'ONE_OWNED_HELPER_PROBE_ONLY', 'SCOPE')
    need(type(plan['gates']) is dict and set(plan['gates']) == GATE_KEYS and
         all(type(v) is dict for v in plan['gates'].values()), 'NULL_OR_MISSING_GATE')
    need(re.fullmatch('[0-9a-f]{32}', plan['runId'] or '') and
         re.fullmatch('[0-9a-f]{32}', plan['creationNonce'] or ''), 'FRESH_NONCE_IDS')
    need(plan['name'] == 'nbdp-helper-probe-' + plan['runId'] + '-' + plan['creationNonce'], 'EXACT_NAME')
    need(re.fullmatch('[0-9]+:[0-9]+', plan['uidGid'] or ''), 'UID_GID')
    need(re.fullmatch('[0-9a-f]{64}', plan['expectedImageConfigSha256'] or ''), 'IMAGE_CONFIG_REQUIRED')
    need(type(plan['source8']) is list and len(plan['source8']) == 8 and
         [v['path'].rsplit('/', 1)[-1] for v in plan['source8']] == list(SOURCE_NAMES), 'CLOSED_SOURCE8')
    need(plan['guardRoot'] == '/tmp/nbdp-e02-minimal-rs-v7/guard-python', 'FIXED_GUARD_ROOT')
    return plan


class ByteLedger:
    """Precharges all physical writes and copies; never refunds or repairs."""
    def __init__(self):
        self.used = {'attached': 0, 'metadata': 0}
        self.first = None

    def poison(self, error):
        if self.first is None:
            self.first = error
        return self.first

    def charge(self, owner, size):
        try:
            if self.first is not None:
                raise self.first
            need(owner in self.used and type(size) is int and size >= 0, 'CLOSED_BYTE_CHARGE')
            need(self.used[owner] + size <= 8_388_608 and sum(self.used.values()) + size <= 16_777_216,
                 'PHYSICAL_PROOF_LIMIT')
            self.used[owner] += size
        except BaseException as error:
            raise self.poison(error)

    def write(self, sink, owner, name, raw):
        try:
            need(type(raw) is bytes, 'PROOF_BYTES')
            self.charge(owner, len(raw))
            sink(name, raw)  # Exclusive, single write. Partial/error remains charged.
        except BaseException as error:
            raise self.poison(error)


def identity(data, intent, cid):
    need(type(data) is dict and re.fullmatch('[0-9a-f]{64}', cid or '') and data['Id'] == cid and
         data['Name'] == '/' + intent['name'] and data['Image'] == IMAGE and
         all(data['Config']['Labels'].get(k) == v for k, v in intent['labels'].items()),
         'IMMUTABLE_IDENTITY_MISMATCH')


def isolation(data, intent):
    hc, config = data['HostConfig'], data['Config']
    need(hc['NetworkMode'] == 'none' and hc['IpcMode'] == 'private' and hc['ReadonlyRootfs'] is True and
         hc['Privileged'] is False and not hc.get('PortBindings') and not hc.get('CapAdd') and
         hc['CapDrop'] == ['ALL'] and hc['SecurityOpt'] == ['no-new-privileges'] and
         hc['Memory'] == hc['MemorySwap'] == 1_073_741_824 and hc['NanoCpus'] == 1_000_000_000 and
         hc['PidsLimit'] == 128 and hc['Init'] is True and not hc.get('Devices') and
         not hc.get('DeviceRequests') and hc['LogConfig'] == {'Type': 'none', 'Config': {}} and
         hc['Tmpfs'] == {'/tmp': 'rw,nosuid,nodev,noexec,size=16m'}, 'ISOLATION')
    need(config['User'] == intent['uidGid'] and config['Entrypoint'] == ['/usr/local/bin/node'] and
         config['Cmd'] == ['/input/probe-guard-helper.mjs'] and config['WorkingDir'] == '/input', 'COMMAND_USER')
    def env_map(rows):
        need(type(rows) is list and all(type(x) is str and '=' in x for x in rows), 'ENVIRONMENT_ROWS')
        pairs = [x.split('=', 1) for x in rows]
        need(len({x[0] for x in pairs}) == len(pairs), 'NO_DUPLICATE_ENVIRONMENT')
        return dict(pairs)
    expected = {**env_map(intent['imageEnvironment']), **env_map(intent['environment'])}
    need(env_map(config['Env']) == expected and not any(k in expected for k in
         ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY', 'ANDROID_HOME',
          'ANDROID_SDK_ROOT', 'ANDROID_AVD_HOME')), 'EXACT_GUEST_ENVIRONMENT')
    mounts = data['Mounts']
    need(len(mounts) == 4 and all(m['Type'] == 'bind' for m in mounts) and
         {(m['Source'], m['Destination'], m['RW']) for m in mounts} == set(map(tuple, intent['mounts'])),
         'EXACT_FOUR_MOUNTS')
    need(not data.get('NetworkSettings', {}).get('Ports'), 'NO_PORTS')


def absent(result, cid):
    return (result['code'] == 1 and result['stdout'].strip() == b'[]' and
            re.fullmatch(rb'(?i:error: no such object: |error response from daemon: no such container: )' +
                         re.escape(cid.encode()), result['stderr'].rstrip(b'\r\n')) is not None and natural(result))


def natural(result):
    return (result['fault'] is None and result['reaped'] is True and result['stdoutEOF'] is True and
            result['stderrEOF'] is True and result['groupClosure'] is None)


class Controller:
    """ports: fresh sample/checkLease, stage/admitSources, CLI, immutable sink.

    CLI always returns actual Popen ownership/EOF/reap facts separately from
    guest helper audit. Cleanup calls are independent of proof retention.
    """
    def __init__(self, plan, plan_sha, ports, t0=None):
        self.plan, self.plan_sha, self.p = closed_plan(plan), plan_sha, ports
        self.ledger = ByteLedger()
        # Root's separately reviewed outer-API proof collector must precharge
        # all of its retained copies within this slot of the SAME metadata8MiB.
        self.ledger.charge('metadata', ROOT_CUSTODY_RESERVATION)
        self.first = None
        self.secondary = []
        self.cid = None
        self.intent = None
        self.calls = 0
        self.target_candidate = False
        self.t0 = self.p.sample() if t0 is None else t0
        self.end = {k: self.t0[k] + 180 * NS for k in ('Utc', 'Mono', 'Boot')}
        self.phase0 = {k: self.t0[k] + 30 * NS for k in self.end}
        self.previous = self.t0

    def fail(self, error):
        if self.first is None:
            self.first = error
            try:
                self.p.revoke(error)
            except BaseException as extra:
                if len(self.secondary) < 64:
                    self.secondary.append({'label': 'revoke', 'error': str(extra)[:2048]})
        elif error is not self.first and len(self.secondary) < 64:
            self.secondary.append({'label': 'secondary', 'error': str(error)[:2048]})

    def remaining(self, ends, active=True):
        now = self.p.check_lease() if active else self.p.sample()
        need(now['bootId'] == self.t0['bootId'], 'BOOT_IDENTITY')
        for k in self.end:
            need(now[k] >= self.previous[k], 'CLOCK_ROLLBACK')
        need(abs((now['Utc'] - self.t0['Utc']) - (now['Boot'] - self.t0['Boot'])) <= 500_000_000,
             'UTC_BOOT_DRIFT')
        need(now['Boot'] - self.previous['Boot'] <= 15 * NS, 'RESUMPTION_GAP')
        self.previous = now
        remaining = min(min(ends[k], self.end[k]) - now[k] for k in self.end)
        need(remaining > 0, 'ABSOLUTE_DEADLINE')
        return remaining

    def retain(self, name, value):
        try:
            raw = value if type(value) is bytes else encoded(value)
            self.ledger.write(self.p.sink, 'metadata', name, raw)
        except BaseException as error:
            self.fail(error)

    def command(self, args, ends, *, target=False, cleanup=False):
        remaining = self.remaining(ends, active=not cleanup)
        need(remaining > 3 * NS, 'NO_BOUNDED_CHILD_FITS')
        run = min((55 if target else 8) * NS, remaining - 3 * NS)
        if target:
            need(run == 55 * NS and self.first is None, 'FULL_TARGET55_REQUIRED')
        self.calls += 1
        # p.cli starts selector before child. It rechecks clocks directly before
        # spawn; retains each complete bounded stream once through this writer.
        def stream(name, raw):
            owner = 'attached' if target else 'metadata'
            try:
                self.ledger.write(self.p.sink, owner, f'cli-{self.calls}-{name}.raw', raw)
            except BaseException as error:
                # Actual returned bytes remain available for immutable identity
                # even if their one immutable proof write failed. No repair.
                self.fail(error)
        result = self.p.cli(args, run_ns=run, ends=ends, check=lambda: self.remaining(ends, active=not cleanup),
                            finish_check=lambda: self.remaining(ends, active=False),
                            capture=stream, target=target, ordinal=self.calls)
        if (args[0] == 'create' and natural(result) and result['code'] == 0 and result['stderr'] == b'' and
                re.fullmatch(b'[0-9a-f]{64}\n?', result['stdout'])):
            # Preserve known immutable creation identity BEFORE fallible receipt
            # retention/deadline checks. Its fresh cleanup inspection still must
            # prove name/image/three labels, even if phase0 just expired.
            self.cid = result['stdout'].decode().strip()
        # Retention is fallible but must not discard returned identity bytes.
        self.retain(f'cli-{self.calls}-lifecycle.json', {k: v for k, v in result.items() if k not in ('stdout', 'stderr')})
        need(natural(result), 'ACTUAL_CHILD_NATURAL_REAP_EOF_REQUIRED')
        # A retention-triggered revocation cannot discard a known returned CID.
        # Preserve the real natural result for identity/cleanup, with no active
        # target permission and still under unchanged absolute phase clocks.
        self.remaining(ends, active=not cleanup and self.first is None)
        return result

    def inspect(self, ends, cleanup=False):
        result = self.command(['inspect', self.cid], ends, cleanup=cleanup)
        need(result['code'] == 0, 'INSPECT_EXIT')
        rows = strict(result['stdout'])
        need(type(rows) is list and len(rows) == 1, 'ONE_INSPECT_ROW')
        return rows[0]

    def cleanup(self):
        if self.cid is None:
            return {'removed': False, 'absence': False, 'unknownIdentity': self.intent is not None}
        now = self.p.sample()
        ends = {k: min(self.t0[k] + 136 * NS, now[k] + 48 * NS) for k in self.end}
        removed = absence = False
        try:
            fresh = self.inspect(ends, cleanup=True)
            identity(fresh, self.intent, self.cid)  # Isolation NEVER gates cleanup.
        except BaseException as error:
            self.fail(error)
            return {'removed': False, 'absence': False, 'unknownIdentity': True}
        if self.target_candidate:
            try:
                isolation(fresh, self.intent)
                need(fresh['State']['Status'] == 'exited' and fresh['State']['Running'] is False and
                     fresh['State']['ExitCode'] == 0 and fresh['State']['OOMKilled'] is False,
                     'TERMINAL_CONTAINER_ZERO')
            except BaseException as error:
                self.fail(error)  # Terminal admission never gates exact-owned rm.
        try:
            result = self.command(['rm', '--force', self.cid], ends, cleanup=True)
            need(result['code'] == 0 and result['stdout'].strip() == self.cid.encode() and result['stderr'] == b'',
                 'EXACT_REMOVE_ACK')
            removed = True
        except BaseException as error:
            self.fail(error)
        # Independent even when rm, output persistence or other retention fails.
        try:
            result = self.command(['inspect', self.cid], ends, cleanup=True)
            need(absent(result, self.cid), 'EXACT_ABSENCE_REQUIRED')
            absence = True
        except BaseException as error:
            self.fail(error)
        return {'removed': removed, 'absence': absence, 'unknownIdentity': False}

    def run(self):
        target = None
        cleanup = {'removed': False, 'absence': False, 'unknownIdentity': False}
        try:
            self.p.admit(self.plan, self.plan_sha, lambda: self.remaining(self.phase0))
            self.p.stage(self.plan, self.ledger, lambda: self.remaining(self.phase0))
            self.remaining(self.phase0)
            image = self.command(['image', 'inspect', IMAGE], self.phase0)
            need(image['code'] == 0 and image['stderr'] == b'', 'CACHED_IMAGE_INSPECT')
            images = strict(image['stdout'])
            need(type(images) is list and len(images) == 1 and images[0]['Id'] == IMAGE and
                 hashlib.sha256(encoded(images[0]['Config'])).hexdigest() == self.plan['expectedImageConfigSha256'],
                 'EXACT_IMAGE_CONFIGURATION')
            self.intent = self.p.intent(self.plan, self.plan_sha)
            self.intent['imageEnvironment'] = images[0]['Config'].get('Env', [])
            self.retain('creation-intent.json', self.intent)
            need(self.first is None, 'INTENT_RETENTION_BEFORE_CREATE')
            self.ledger.charge('metadata', 65)  # Docker's exclusive CID file, never refunded.
            created = self.command(self.p.create_args(self.intent), self.phase0)
            # Only full returned immutable CID. Unknown creation is never retried
            # or reconciled through a mutable name-only destructive command.
            need(created['code'] == 0 and created['stderr'] == b'' and
                 re.fullmatch(b'[0-9a-f]{64}\n?', created['stdout']), 'EXACT_CREATED_CID')
            self.cid = created['stdout'].decode().strip()
            self.p.verify_cidfile(self.cid, lambda: self.remaining(self.phase0))
            data = self.inspect(self.phase0)
            identity(data, self.intent, self.cid)
            isolation(data, self.intent)
            need(data['State']['Status'] == 'created' and data['State']['Running'] is False, 'CREATED_NOT_STARTED')
            self.p.before_target(self.plan, lambda: self.remaining(self.phase0))
            self.remaining(self.phase0)
            need(self.first is None, 'NO_TARGET_AFTER_FAULT')
            now = self.p.check_lease()
            ends = {k: min(self.end[k] - 92 * NS, now[k] + 58 * NS) for k in self.end}
            target = self.command(['start', '--attach', self.cid], ends, target=True)
            need(target['code'] == 0 and target['stderr'] == b'', 'PROBE_CHILD_EXIT_STDERR')
            need(self.first is None, 'NO_PROBE_COMMIT_AFTER_RETENTION_FAULT')
            self.p.validate_probe(target['stdout'], self.plan, self.plan_sha)
            self.remaining(ends)
            self.target_candidate = True
        except BaseException as error:
            self.fail(error)
        finally:
            try:
                cleanup = self.cleanup()
            except BaseException as error:
                self.fail(error)
        try:
            now = self.p.sample()
            post_end = {k: min(self.t0[k] + 156 * NS, now[k] + 20 * NS) for k in self.end}
            self.p.postread(self.plan, lambda: self.remaining(post_end, active=False))
        except BaseException as error:
            self.fail(error)
        result = {'schema': 'e02-one-cid-helper-probe-result-v1', 'qualified': self.first is None and cleanup['absence'],
                  'error': None if self.first is None else str(self.first), 'secondaryErrors': self.secondary,
                  'cid': self.cid, 'cleanup': cleanup, 'chargedPhysicalBytes': dict(self.ledger.used),
                  'childEvidence': 'ACTUAL_HOST_POPEN_ONLY', 'outerApiEvidence': None,
                  'ordinaryRowsQualified': 0, 'backendCause': 'UNKNOWN'}
        self.retain('result.json', result)
        # The immutable receipt can say unqualified, never acquire late success
        # when final receipt retention itself failed.
        return result if self.first is None else {**result, 'qualified': False, 'error': str(self.first)}
