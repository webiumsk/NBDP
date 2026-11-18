"""SOURCE ONLY: finite isolated transport diagnostic, no Android or service on import."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import time
import uuid
HERE=Path(__file__).resolve().parent
REPO=Path('/home/peterhorvath/apps/bitcoin/NBDP')
LAB=Path('/tmp/nbdp-e02-transport-query-diagnostic-v2')
ROLES=('anchor','rs-relay','fixture')
RUNTIME='sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f'
RELAY='sha256:fe586a0bc68edefb553a62d21983de469128f7cb785bfcc2ef7c82dbf1cded82'
LIMITS={'anchor':(128,64,1),'rs-relay':(512,128,1),'fixture':(1024,128,1)}
PY=['/guard-python/lib/ld-linux-x86-64.so.2','--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s']
LOG_OPTIONS=['--log-driver','local','--log-opt','max-size=16m','--log-opt','max-file=1','--log-opt','compress=false']
SCOPE='E02_TRANSPORT_QUERY_DIAGNOSTIC_V2_ONLY_NO_ANDROID_NO_E02_COMPLETION'


def need(value, message):
    if not value:
        raise RuntimeError(message)

def strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'Duplicate JSON metadata')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: need(False, 'Nonfinite metadata'))

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1048576):
            h.update(chunk)
    return h.hexdigest()

def pin(path):
    path = Path(path)
    need(path.is_absolute() and not path.is_symlink() and path.resolve(strict=True) == path
         and path.is_file(), 'Canonical regular input required: ' + str(path))
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}

def checked(descriptor):
    need(set(descriptor) == {'path', 'bytes', 'sha256'}, 'Closed file pin required')
    need(pin(descriptor['path']) == descriptor, 'Pinned bytes changed: ' + descriptor['path'])
    return Path(descriptor['path'])

def put(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path)

def jsonbytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')

def exact_cid_absent(result, cid):
    """Accept only the CLI's complete exact-CID inspect-not-found response.

    Case is flexible in the ASCII diagnostic prefix, never in CID identity.
    Only the two observed inspect-not-found forms are accepted; other daemon,
    connectivity, permission and mixed diagnostics are not absence evidence.
    The independently observed Docker29 inspect responses print [] on stdout.
    """
    if not re.fullmatch('[0-9a-f]{64}', cid) or result.returncode != 1:
        return False
    if result.stdout.strip() != b'[]':
        return False
    return re.fullmatch(rb'(?i:error: no such object: |error response from daemon: no such container: )'
                        + re.escape(cid.encode('ascii')),
                        result.stderr.rstrip(b'\r\n')) is not None

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def finalize(out, base, primary_error, cleanup):
    """Retain the first failure; cleanup/retention failures never become exit0."""
    secondary = list(cleanup.get('errors', []))
    if any(row.get('error') or row.get('errors') or not row.get('absenceConfirmed')
           for row in cleanup.get('rows', [])) and not secondary:
        secondary.append('Cleanup row failed or exact absence uncertain')
    if not cleanup.get('ok') and not secondary:
        secondary.append('Cleanup incomplete or absence uncertain')
    error = primary_error
    if error is None and secondary:
        error = secondary.pop(0)
    value = dict(base, executionState='FAILED_UNQUALIFIED' if error else 'PARTIAL',
                 error=error, secondaryErrors=secondary, cleanup=cleanup)
    try:
        put(out / 'supervisor-result.json', jsonbytes(value))
    except BaseException as failure:
        # The foreground caller retains stderr when filesystem evidence fails.
        value['executionState'] = 'FAILED_UNQUALIFIED'
        if value['error'] is None:
            value['error'] = 'Final result retention failed: ' + repr(failure)
        else:
            value['secondaryErrors'].append('Final result retention failed: ' + repr(failure))
        sys.stderr.write(json.dumps(value, ensure_ascii=True) + '\n')
        return 2
    return 2 if error else 0

def run_service(lease, argv, timeout, env, stdout=None, stderr=None):
    """Forward actual captured service bytes on failure, then re-raise it.

    Failed capture forwarding is secondary and cannot mask the original child
    failure. Both streams are attempted independently; no fixture replacement.
    """
    stdout = sys.stdout.buffer if stdout is None else stdout
    stderr = sys.stderr.buffer if stderr is None else stderr
    def forward(result):
        failures = []
        for stream, key in ((stdout, 'stdout'), (stderr, 'stderr')):
            try:
                stream.write(result[key]); stream.flush()
            except BaseException as error:
                failures.append(key + ': ' + repr(error))
        return failures
    try:
        result = lease.run_checked(argv, timeout, env)
    except BaseException:
        result = getattr(lease, 'last_result', None)
        if result is not None:
            failures = forward(result)
            if failures:
                try:
                    sys.stderr.write('Secondary service capture forwarding failure: ' + repr(failures) + '\n')
                except BaseException:
                    pass
        raise
    failures = forward(result)
    need(not failures, 'Service capture forwarding failed: ' + repr(failures))
    need(result['exit'] == 0 and result['error'] is None and result['reaped']
         and not result['forced'], 'Owned service failed')

class Runtime:
    def __init__(self, config, config_pin, release_pin, out, guard, lease, fixture):
        self.plan, self.plan_pin, self.release_pin = config, config_pin, release_pin
        self.out, self.run_root, self.guard, self.lease = out, out, guard, lease
        self.fixture_plan, self.ids, self.intents, self.sequence = fixture, {}, {}, 0
        self.inputs_sealed = False
        self.host_env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'LANG': 'C.UTF-8',
                         'HOME': str(out / 'docker-config'), 'DOCKER_CONFIG': str(out / 'docker-config'),
                         'DOCKER_HOST': 'unix:///var/run/docker.sock'}
        self.docker = '/usr/bin/docker'
        self.lease_sha = digest(out / 'session/lease.json')

    def check(self):
        now = self.lease.check()
        if self.inputs_sealed:
            checked(self.plan_pin); checked(self.release_pin)
            for d in self.plan['sourceAndDependencyPins']:
                staged = pin(self.out / 'input' / Path(d['path']).name)
                need(staged['sha256'] == d['sha256'] and staged['bytes'] == d['bytes'], 'Immutable staged source drift')
            self.lease.check()
        return now

    def sleep(self, seconds):
        return self.lease.sleep(seconds)

    def put_bytes(self, relative, raw):
        self.check()
        path = PurePosixPath(relative)
        need(not path.is_absolute() and '..' not in path.parts and len(raw) <= 16777216, 'Bounded own output only')
        result = put(self.out / path, raw)
        self.check()
        return result

    def put_json(self, relative, value):
        return self.put_bytes(relative, jsonbytes(value))

    def command(self, args, timeout=30):
        self.check()
        self.sequence += 1
        name = 'commands/%04d' % self.sequence
        try:
            result = self.lease.run_checked([self.docker, *args], timeout, self.host_env)
        except BaseException:
            result = getattr(self.lease, 'last_result', None)
            if result:
                self.record_command(name, result)  # Evidence retention only, even after refusal.
            raise
        self.record_command(name, result)
        need(result['exit'] == 0 and result['error'] is None and result['reaped']
             and not result['forced'] and result['stdoutEOF'] and result['stderrEOF'], 'Unqualified Docker command')
        self.check()
        return result['stdout']

    def record_command(self, name, result):
        value = dict(result)
        for stream in ('stdout', 'stderr'):
            value[stream] = put(self.out / (name + '.' + stream), value[stream])
        put(self.out / (name + '.json'), jsonbytes(value))

    def guest(self, role, payload, timeout=30):
        self.check()
        self.inspect(role)
        return self.command(['exec', self.ids[role], *PY, '/input/lease_guard.py',
                             'exec', self.lease_sha, *payload], timeout)

    def fixture(self, operation):
        need(operation in ('prepare', 'status', 'publish'), 'Fixed fixture operations')
        self.check()
        self.inspect('fixture')
        raw = self.command(['exec', self.ids['fixture'], '/usr/local/bin/node', '/input/fixture.mjs', operation], 55)
        self.check()
        return raw

    def inspect(self, role):
        rows = strict(self.command(['inspect', self.ids[role]]))
        need(len(rows) == 1, 'One exact container required')
        data = rows[0]
        self.validate_owned(role, data)
        need(data['State']['Running'] is True, 'Owned service exited')
        return data

    def validate_identity(self, role, data):
        """Cleanup authority is exact identity, independent of failed isolation."""
        entry = self.intents[role]
        need(re.fullmatch('[0-9a-f]{64}', data['Id'])
             and (role not in self.ids or data['Id'] == self.ids[role])
             and data['Name'] == '/' + entry['name']
             and all(data['Config']['Labels'].get(k) == v for k, v in entry['labels'].items())
             and data['Image'] == entry['image'], 'Exact CID/image/creation ownership mismatch')

    def validate_owned(self, role, data):
        self.validate_identity(role, data)
        entry = self.intents[role]
        hc = data['HostConfig']
        expected_network = 'none' if role == 'anchor' else 'container:' + self.ids['anchor']
        memory, pids, cpus = LIMITS[role]
        need(hc['NetworkMode'] == expected_network and not hc['Privileged'] and not hc.get('PortBindings')
             and not hc.get('CapAdd') and hc['ReadonlyRootfs'] and 'ALL' in hc['CapDrop']
             and any('no-new-privileges' in x for x in hc['SecurityOpt'])
             and hc['Memory'] == memory * 1048576 and hc['MemorySwap'] == memory * 1048576
             and hc['PidsLimit'] == pids and hc['NanoCpus'] == cpus * 1000000000,
             'Actual container isolation/resource mismatch')
        env = dict(value.split('=', 1) for value in data['Config']['Env'] if '=' in value)
        need(not any(k in env for k in ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY')),
             'No host GUI/clipboard bridge environment')
        need(env.get('NBDP_LEASE_SHA256') == self.lease_sha
             and env.get('NBDP_FIXTURE_PLAN_SHA256') == digest(HERE / 'fixture-plan.json')
             and env.get('NBDP_MINIMUM_RUN_CONFIG_SHA256') == self.plan_pin['sha256'], 'Exact original service guard environment')
        need(data['Config']['Entrypoint'] == [PY[0]] and data['Config']['Cmd'] == entry['command']
             and data['Config']['User'] == str(os.getuid()) + ':' + str(os.getgid()), 'Actual entrypoint/user mismatch')
        actual_mounts = {(m['Source'], m['Destination'], m['RW']) for m in data['Mounts'] if m['Type'] == 'bind'}
        need(actual_mounts == set(tuple(x) for x in entry['mounts']), 'Actual input mount allowlist mismatch')
        devices = hc.get('Devices') or []
        need(devices == [], 'No devices/SDK/Android in diagnostic')

    def start(self, role):
        need(role in ROLES, 'Only three diagnostic roles allowed')
        self.check()
        image = RELAY if role == 'rs-relay' else RUNTIME
        nonce = uuid.uuid4().hex
        entry = {'name': 'nbdp-e02-' + self.plan['runId'] + '-' + role,
                 'image': image, 'labels': {'nbdp.run': self.plan['runId'],
                 'nbdp.role': role, 'nbdp.creation': nonce}, 'mounts': []}
        mounts = entry['mounts']
        def mount(source, target, writable=False):
            source = Path(source).resolve(strict=True)
            need(',' not in str(source), 'Simple canonical bind source required')
            mounts.append([str(source), target, writable])
        mount(self.out / 'input', '/input')
        mount(self.out / 'session/lease.json', '/session/lease.json')
        mount(self.out / 'session/control', '/session/control', True)
        mount(self.plan['guardBundleRoot'], '/guard-python')
        if role == 'rs-relay':
            mount(self.plan['relayConfig']['path'], '/src/config.toml')
            mount(self.out / 'relay-data', '/data', True)
        if role == 'fixture':
            mount(self.out / 'session/fixtures', '/session/fixtures', True)
            mount(REPO / 'experiments/node_modules', '/input/node_modules')
            for d in self.fixture_plan['pins'].values():
                mount(d['source'], d['path'])
        memory, pids, cpus = LIMITS[role]
        args = ['create', '--pull=never', '--name', entry['name'], '--network', 'none' if role == 'anchor' else 'container:' + self.ids['anchor'],
                '--user', str(os.getuid()) + ':' + str(os.getgid()), '--cap-drop', 'ALL', '--security-opt',
                'no-new-privileges', '--read-only', '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m',
                '--cpus', str(cpus), '--memory', str(memory) + 'm', '--memory-swap', str(memory) + 'm',
                '--pids-limit', str(pids), '--init', *LOG_OPTIONS,
                '--entrypoint', PY[0], '--workdir', '/src' if role == 'rs-relay' else '/input']
        for key, value in entry['labels'].items():
            args += ['--label', key + '=' + value]
        environment = dict(self.guard.ENV, NBDP_LEASE_SHA256=self.lease_sha,
                           NBDP_FIXTURE_PLAN_SHA256=digest(HERE / 'fixture-plan.json'),
                           NBDP_MINIMUM_RUN_CONFIG_SHA256=self.plan_pin['sha256'])
        for key, value in environment.items():
            args += ['--env', key + '=' + value]
        for source, target, writable in mounts:
            args += ['--mount', 'type=bind,src=' + source + ',dst=' + target + ('' if writable else ',readonly')]
        entry['command'] = [*PY[1:], '/input/supervisor.py', '--guest', role]
        self.intents[role] = entry  # Intent precedes creation; cleanup can reconcile an interrupted response.
        self.put_json('ownership/' + role + '-intent.json', entry)
        cid = self.command([*args, image, *entry['command']]).decode().strip()
        need(re.fullmatch('[0-9a-f]{64}', cid), 'Exact returned CID required')
        self.ids[role] = cid
        self.put_json('ownership/' + role + '-cid.json', {'id': cid})
        self.command(['start', cid])
        self.put_json('ownership/' + role + '-initial-inspect.json', self.inspect(role))

    def cleanup(self):
        """Expiry exception: only inspect/log/remove exact verified owned CIDs.

        No process-group signals, name-only removals, mass stops or prune. Docker
        handles exact immutable CIDs. This is bounded best effort, never PASS.
        """
        rows, errors = [], []
        def call(args):
            r = subprocess.run([self.docker, *args], stdin=subprocess.DEVNULL, capture_output=True,
                               env=self.host_env, timeout=8)
            need(len(r.stdout) <= 16777216 and len(r.stderr) <= 262144, 'Cleanup output bound')
            return r
        def fault(row, phase, error):
            message = phase + ': ' + repr(error)
            row['errors'].append(message)
            errors.append(row['role'] + ': ' + message)
        def retain(row, suffix, raw):
            try:
                put(self.out / ('cleanup/' + row['role'] + '-' + suffix), raw)
            except BaseException as error:
                fault(row, 'retain-' + suffix, error)
        for role in reversed(ROLES):
            if role not in self.intents:
                continue
            entry = self.intents[role]
            row = {'role': role, 'exactOwnedCleanupOnly': True, 'errors': [],
                   'identityVerified': False, 'absenceConfirmed': False}
            try:
                r = call(['inspect', self.ids.get(role, entry['name'])])
                retain(row, 'inspect.stdout', r.stdout)
                retain(row, 'inspect.stderr', r.stderr)
                row['inspectExit'] = r.returncode
                need(r.returncode == 0, 'Cannot prove exact owned container; no removal')
                data = strict(r.stdout)
                need(len(data) == 1 and re.fullmatch('[0-9a-f]{64}', data[0]['Id']), 'One exact cleanup identity')
                self.validate_identity(role, data[0])
                self.ids[role] = data[0]['Id']
                row.update(cid=self.ids[role], identityVerified=True)
            except BaseException as error:
                fault(row, 'ownership-inspect', error)
            if row['identityVerified']:
                cid = row['cid']
                # Failed runtime isolation must be reported, but cannot revoke
                # cleanup authority over this exact already-owned immutable ID.
                try:
                    self.validate_owned(role, data[0])
                except BaseException as error:
                    fault(row, 'isolation-diagnostic', error)
                try:
                    log = call(['logs', cid])
                    row['logsExit'] = log.returncode
                    retain(row, 'logs.stdout', log.stdout)
                    retain(row, 'logs.stderr', log.stderr)
                    need(log.returncode == 0, 'Owned log collection failed')
                except BaseException as error:
                    fault(row, 'logs-diagnostic', error)
                # Independent attempts: failed log/write/rm cannot skip absence
                # inspection. A foreign or uncertain identity never reaches rm.
                try:
                    removed = call(['rm', '-f', cid])
                    row['removeExit'] = removed.returncode
                    retain(row, 'remove.stdout', removed.stdout)
                    retain(row, 'remove.stderr', removed.stderr)
                    need(removed.returncode == 0, 'Exact-owned removal failed')
                except BaseException as error:
                    fault(row, 'remove', error)
                try:
                    after = call(['inspect', cid])
                    row['afterInspectExit'] = after.returncode
                    retain(row, 'after-inspect.stdout', after.stdout)
                    retain(row, 'after-inspect.stderr', after.stderr)
                    need(exact_cid_absent(after, cid),
                         'Removal not independently observed for exact CID')
                    row['absenceConfirmed'] = True
                except BaseException as error:
                    fault(row, 'absence', error)
            if row['errors']:
                row['error'] = row['errors'][0]
            rows.append(row)
        summary = {'ok': not errors and all(row['absenceConfirmed'] for row in rows),
                   'rows': rows, 'errors': errors}
        try:
            evidence = put(self.out / 'cleanup/result.json', jsonbytes(summary))
        except BaseException as error:
            errors.append('cleanup-result-retention: ' + repr(error))
            summary['ok'] = False
            evidence = None
        return dict(summary, evidence=evidence)

def dependency_relative(value):
    need(type(value) is str and value and not value.startswith('/')
         and all(part not in ('','.','..') for part in value.split('/')), 'Canonical dependency relative path')
    return value


def dependency_snapshot(root):
    root=Path(root)
    need(root.is_absolute() and root.resolve(strict=True)==root and not root.is_symlink(),'Canonical dependency root')
    actual={'directories':[],'files':[],'symlinks':[]}
    def walk(folder):
        for p in sorted(folder.iterdir()):
            rel=dependency_relative(p.relative_to(root).as_posix())
            if p.is_symlink():
                target=p.resolve(strict=True)
                need(target.is_relative_to(root) and target!=root,'Dependency symlink escape')
                actual['symlinks'].append({'path':rel,'link':str(p.readlink()),'target':dependency_relative(target.relative_to(root).as_posix())})
            elif p.is_dir():actual['directories'].append(rel);walk(p)
            elif p.is_file():actual['files'].append(rel)
            else:raise RuntimeError('Dependency special file')
    walk(root)
    for name in ('directories','files'):actual[name].sort()
    actual['symlinks'].sort(key=lambda v:v['path'])
    return actual


def verify_dependency_inventory(fixture,tree,root):
    need(type(tree) is dict and set(tree)=={'schema','sourceRoot','runtimeRoot','directories','files','symlinks'},'Closed dependency tree keys')
    need(tree['schema']=='e02-transport-dependency-tree-v2' and tree['runtimeRoot']=='/input/node_modules','Closed dependency tree')
    actual=dependency_snapshot(root)
    need(actual=={k:tree[k] for k in ('directories','files','symlinks')},'Dependency exact membership')
    descriptors=fixture['dependencyFiles']
    need(type(descriptors) is list and len(descriptors)==len(actual['files'])
         and len({d['path'] for d in descriptors})==len(descriptors),'Dependency descriptor membership')
    expected=[]
    for d in descriptors:
        need(set(d)=={'source','path','bytes','sha256'} and d['path'].startswith(tree['runtimeRoot']+'/'),'Closed runtime dependency descriptor')
        rel=dependency_relative(d['path'][len(tree['runtimeRoot'])+1:]);expected.append(rel)
        need(d['source']==tree['sourceRoot']+'/'+rel,'Dependency source/runtime mapping')
        p=Path(root)/rel
        checked({'path':str(p),'bytes':d['bytes'],'sha256':d['sha256']})
    need(sorted(expected)==actual['files'],'All regular dependency members')
    return {'schema':'e02-transport-dependency-check-v2','files':len(actual['files']),
            'directories':len(actual['directories']),'symlinks':len(actual['symlinks']),'exact':True}


def source_pins():
    return [pin(HERE/name) for name in ('supervisor.py','lease_guard.py','fixture.mjs',
        'exchange.mjs','strict-json.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json',
        'fixture-plan.json','publish-frame.json','query-frame.json')]


def verify_config(config):
    need(set(config)=={'schema','scope','runId','originalLeaseSeconds','runtimeImage','relayImage',
        'sourceAndDependencyPins','guardBundleRoot','guardBundleInventory','relayConfig'},'Closed diagnostic config')
    need(config['schema']=='e02-transport-query-diagnostic-config-v2' and config['scope']==SCOPE,'Diagnostic scope only')
    need(config['runtimeImage']==RUNTIME and config['relayImage']==RELAY,'Original exact images')
    need(re.fullmatch('[0-9a-f]{32}',config['runId']) and type(config['originalLeaseSeconds']) is int
        and 60<=config['originalLeaseSeconds']<=1800,'Original finite lease without renewal')
    need(config['sourceAndDependencyPins']==source_pins(),'Exact current diagnostic sources/inputs')
    need(config['guardBundleRoot']=='/tmp/nbdp-e02-minimal-rs-v7/guard-python','Exact existing guard root')
    bundle=strict(checked(config['guardBundleInventory']).read_bytes())
    for name,d in bundle['files'].items():
        p=Path(config['guardBundleRoot'])/name
        need(p.resolve(strict=True).is_relative_to(Path(config['guardBundleRoot']))
            and not p.is_symlink() and p.stat().st_size==d['bytes'] and digest(p)==d['sha256'],'Guard bundle drift')
    checked(config['relayConfig'])
    fixture=strict((HERE/'fixture-plan.json').read_bytes())
    need(fixture['schema']=='e02-transport-query-diagnostic-fixture-v2' and fixture['scenario']=='BASELINE_ONE_PUB_THEN_EXACT_QUERY'
        and fixture['limits']=={'messageBytes':262144,'captureBytes':16777216,'networkTimeoutMilliseconds':10000,
                              'handshakeTimeoutMilliseconds':3000,'controlTimeoutMilliseconds':45000},'Original fixed diagnostic limits')
    tree=strict((HERE/'dependency-tree.json').read_bytes())
    need(tree['sourceRoot']==str(REPO/'experiments/node_modules'),'Fixed canonical installed dependency root')
    verify_dependency_inventory(fixture,tree,REPO/'experiments/node_modules')
    need(fixture['pins']=={},'No crypto/native/SDK mounts')
    return fixture


def guest(role):
    need(role in ROLES,'No Android or arbitrary service role')
    guard=load_module('diag_guest_guard','/input/lease_guard.py')
    lease=guard.Lease('/session/lease.json',os.environ['NBDP_LEASE_SHA256'],'/session/control')
    lease.check()
    config_raw=Path('/input/run-config.json').read_bytes()
    need(hashlib.sha256(config_raw).hexdigest()==os.environ['NBDP_MINIMUM_RUN_CONFIG_SHA256'],'Exact original diagnostic config')
    env=dict(guard.ENV,NBDP_LEASE_SHA256=os.environ['NBDP_LEASE_SHA256'],
        NBDP_FIXTURE_PLAN_SHA256=os.environ['NBDP_FIXTURE_PLAN_SHA256'],
        NBDP_MINIMUM_RUN_CONFIG_SHA256=os.environ['NBDP_MINIMUM_RUN_CONFIG_SHA256'])
    signal.signal(signal.SIGTERM,lambda *_:lease.revoke('Owned service interrupted'))
    signal.signal(signal.SIGINT,lambda *_:lease.revoke('Owned service interrupted'))
    if role=='anchor':
        while True:lease.sleep(1)
    elif role=='rs-relay':run_service(lease,['/src/target/release/nostr-rs-relay','--db','/data'],1800,env)
    else:run_service(lease,['/usr/local/bin/node','/input/fixture.mjs','serve'],1800,env)


def execute(config_path,config_sha,release_path,release_sha,out):
    cp,rp=pin(config_path),pin(release_path)
    need(cp['sha256']==config_sha and rp['sha256']==release_sha,'External config/release hashes')
    config,release=strict(config_path.read_bytes()),strict(release_path.read_bytes())
    fixture=verify_config(config)
    need(set(release)=={'schema','runId','scope','config','sourceSubject','sourceQaReview','sourceSecurityReview',
        'controlAcceptance','freshAdmission','operator','issuedAtUtcNs','notAfterUtcNs'},'Closed root diagnostic release')
    need(release['schema']=='e02-transport-query-diagnostic-release-v2' and release['scope']==SCOPE
        and release['runId']==config['runId'] and release['config']==cp and release['operator']=='/root','Exact separately authorized root role')
    for key in ('sourceSubject','sourceQaReview','sourceSecurityReview','controlAcceptance','freshAdmission'):checked(release[key])
    need(type(release['issuedAtUtcNs']) is int and type(release['notAfterUtcNs']) is int
        and release['issuedAtUtcNs']<=time.time_ns()<release['notAfterUtcNs'],'Actual release interval')
    need(out==LAB/'runs'/config['runId'] and not out.exists(),'Fresh exclusive diagnostic output')
    guard=load_module('diag_host_guard',HERE/'lease_guard.py')
    out.mkdir(parents=True,mode=0o700)
    for directory in ('input','session/control','session/fixtures','relay-data','docker-config'):
        (out/directory).mkdir(parents=True,mode=0o700)
    put(out/'docker-config/config.json',b'{}\n')
    value=guard.issue(config['runId'],config['originalLeaseSeconds'])
    need(value['deadlineUtcNs']<=release['notAfterUtcNs'],'Original diagnostic deadline inside root release')
    lp=put(out/'session/lease.json',jsonbytes(value))
    lease=guard.Lease(lp['path'],lp['sha256'],out/'session/control')
    runtime=Runtime(config,cp,rp,out,guard,lease,fixture)
    signal.signal(signal.SIGTERM,lambda *_:lease.revoke('Coordinator interrupted'))
    signal.signal(signal.SIGINT,lambda *_:lease.revoke('Coordinator interrupted'))
    error=None
    try:
        for d in config['sourceAndDependencyPins']:
            runtime.put_bytes('input/'+Path(d['path']).name,checked(d).read_bytes())
        runtime.put_bytes('input/run-config.json',config_path.read_bytes())
        (out/'input/node_modules').mkdir(mode=0o700)
        runtime.inputs_sealed=True
        for role in ROLES:runtime.start(role)
        for _ in range(40):
            runtime.check()
            if (out/'session/fixtures/serve-ready.json').is_file():break
            runtime.sleep(.25)
        else:raise RuntimeError('Diagnostic control socket not ready under fixed bounded source wait')
        prepared=runtime.fixture('prepare')
        runtime.put_bytes('evidence/prepare-reply.json',prepared)
        raw=runtime.fixture('publish')  # Original55s command ceiling; one attempt only.
        runtime.put_bytes('evidence/diagnostic-reply.json',raw)
        result=strict(raw)
        need(result['ok'] is True and result['result']['state']=='BASELINE_PUB_QUERY_OBSERVED','Full exact diagnostic result')
        runtime.check()
    except BaseException as exc:
        error=repr(exc)
        try:lease.revoke('Diagnostic stopped: '+error)
        except BaseException:pass
    finally:
        dependency_end=None;dependency_end_error=None
        try:cleanup=runtime.cleanup()
        except BaseException as exc:cleanup={'ok':False,'rows':[],'evidence':None,'errors':[repr(exc)]}
        try:
            boundary=verify_dependency_inventory(fixture,strict((HERE/'dependency-tree.json').read_bytes()),REPO/'experiments/node_modules')
            dependency_end=put(out/'dependency-end-boundary.json',jsonbytes({'ok':True,'result':boundary}))
        except BaseException as boundary_error:
            dependency_end_error=repr(boundary_error)
            if error is None:error='Dependency end boundary: '+repr(boundary_error)
            else:
                try:put(out/'dependency-end-boundary-error.json',jsonbytes({'error':repr(boundary_error),'primaryErrorPreserved':error}))
                except BaseException:pass
        return finalize(out,{'schema':'e02-transport-query-diagnostic-result-v2','runId':config['runId'],
            'config':cp,'release':rp,'lease':lp,'scope':SCOPE,'canonicalE02Changed':False,
            'ordinaryClientQualified':False,'dependencyEndBoundary':dependency_end,
            'dependencyEndBoundaryError':dependency_end_error},error,cleanup)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guest',choices=ROLES)
    parser.add_argument('--config',type=Path);parser.add_argument('--config-sha')
    parser.add_argument('--release',type=Path);parser.add_argument('--release-sha')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.guest:return guest(args.guest) or 0
    need(all((args.config,args.config_sha,args.release,args.release_sha,args.out)),'Exact external diagnostic grant required')
    return execute(args.config,args.config_sha,args.release,args.release_sha,args.out)


if __name__=='__main__':
    try:code=main()
    except BaseException as error:sys.stderr.write(type(error).__name__+': '+str(error)[:4096]+'\n');code=2
    raise SystemExit(code)
