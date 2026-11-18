"""Finite, foreground-owned E02 first-cell launcher. SOURCE ONLY until reviewed.

No service, experiment, subprocess or project import occurs merely on import.
The immutable run config and a separately externally pinned root release are
required. One successful cell remains PARTIAL; no canonical record is written.
"""
import argparse
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
# Guest source is staged at /input/supervisor.py. Host-only helpers use this
# fixed authorized checkout; module initialization must also work in /input.
REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
LAB = Path('/Data/nbdp-e02-tooling-20261027/ordinary-minimum-r3')
OLD = Path('/tmp/nbdp-e02-minimal-rs-v7')
SCOPE = 'E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY'
PROFILE = 'e02-ordinary-minimum-rs-two-role-v2'
# Exact immutable reviewed metadata authority; never derived from current file bytes.
REVIEWED_RUNTIME_INPUTS = {'relayConfig': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/docker/rs-relay.toml', 'bytes': 192, 'sha256': '6775940c6258e2714a2a60793584ae549a50111154c743045a87d679af9a0b02'}, 'sdkInventory': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-api35-fixture-preparation-r2/sdk-tree.json', 'bytes': 89738, 'sha256': '5c996f67fd8aba0ea618adc7f7f9e6a2c27c641cc95910deb07bdfa8a10562a8'}, 'guardBundleInventory': {'path': '/tmp/nbdp-e02-minimal-rs-v7/records/guard-bundle-manifest.json', 'bytes': 332736, 'sha256': '9de311222ef78e20fbe05bfef32898976d80737d5d932166d23431a04a73a454'}}
RUNTIME = 'sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f'
RELAY = 'sha256:fe586a0bc68edefb553a62d21983de469128f7cb785bfcc2ef7c82dbf1cded82'
PY = ['/guard-python/lib/ld-linux-x86-64.so.2', '--inhibit-cache', '--library-path',
      '/guard-python/lib', '/guard-python/bin/python3.11', '-B', '-P', '-S', '-s']
ROLES = ('anchor', 'rs-relay', 'fixture', 'android')
LIMITS = {'anchor': (128, 64, 1), 'rs-relay': (512, 128, 1),
          'fixture': (1024, 128, 1), 'android': (8192, 512, 8)}
LOG_OPTIONS = ['--log-driver', 'local', '--log-opt', 'max-size=16m',
               '--log-opt', 'max-file=1', '--log-opt', 'compress=false']
CONFIG = '''avd.ini.encoding=UTF-8
AvdId=ordinary
avd.ini.displayname=NBDP disposable ordinary client
image.sysdir.1=system-images/android-35/default/x86_64/
abi.type=x86_64
hw.cpu.arch=x86_64
hw.cpu.ncore=4
hw.ramSize=4096
hw.lcd.width=1080
hw.lcd.height=1920
hw.lcd.density=420
hw.gpu.enabled=yes
hw.gpu.mode=lavapipe
hw.keyboard=yes
hw.audioInput=no
hw.audioOutput=no
hw.sdCard=no
hw.camera.back=none
hw.camera.front=none
disk.dataPartition.size=2048M
fastboot.forceColdBoot=yes
showDeviceFrame=no
PlayStore.enabled=false
'''
EMULATOR = ['/sdk/emulator/emulator', '-avd', 'ordinary', '-ports', '5554,5555',
            '-no-window', '-no-snapshot', '-wipe-data', '-no-audio', '-camera-back',
            'none', '-camera-front', 'none', '-gpu', 'lavapipe',
            '-memory', '4096', '-cores', '4', '-no-boot-anim', '-no-metrics',
            '-netdelay', 'none', '-netspeed', 'full', '-accel', 'on']


def need(value, message):
    if not value:
        raise RuntimeError(message)


def require_android_affinity():
    """Trial admission only; configured caps are not measured resource usage."""
    need(len(os.sched_getaffinity(0)) >= 8, 'Android resource trial requires at least8 host affinity CPUs')


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


def validate_namespace_addresses(raw):
    """Actual private network inventory must expose only the loopback device."""
    need(type(raw) is bytes and len(raw) <= 1048576, 'Bounded actual namespace inventory required')
    rows = strict(raw)
    need(type(rows) is list and len(rows) == 1 and type(rows[0]) is dict
         and rows[0].get('ifname') == 'lo', 'Private namespace must expose only one loopback interface')
    interface = rows[0]
    need(type(interface.get('flags')) is list and len(interface['flags']) <= 32
         and all(type(flag) is str for flag in interface['flags'])
         and 'LOOPBACK' in interface['flags'], 'Actual typed LOOPBACK flags required')
    addresses = interface.get('addr_info')
    need(type(addresses) is list and 0 < len(addresses) <= 16, 'Actual loopback address inventory required')
    for entry in addresses:
        need(type(entry) is dict and type(entry.get('local')) is str and '%' not in entry['local'],
             'Unzoned numeric loopback address required')
        address = ipaddress.ip_address(entry['local'])
        need(address.is_loopback and entry.get('family') == ('inet' if address.version == 4 else 'inet6')
             and entry.get('scope') == 'host' and type(entry.get('prefixlen')) is int
             and entry['prefixlen'] == (8 if address.version == 4 else 128), 'Unexpected namespace address')


def classify_listener_endpoint(local):
    """Strict numeric endpoint; APIs may exist inside the isolated namespace."""
    need(type(local) is str and '%' not in local, 'Unzoned numeric listener required')
    match = re.fullmatch(r'\[([^\[\]]+)\]:([1-9][0-9]{0,4})', local)
    if match:
        address = ipaddress.IPv6Address(match[1]); port = int(match[2])
    else:
        match = re.fullmatch(r'([0-9.]+):([1-9][0-9]{0,4})', local)
        need(match is not None, 'Malformed listener endpoint')
        address = ipaddress.IPv4Address(match[1]); port = int(match[2])
    need(1 <= port <= 65535, 'Listener port out of range')
    mapped = address.ipv4_mapped if address.version == 6 else None
    loopback = address.is_loopback or mapped is not None and mapped.is_loopback
    relay = local in ('0.0.0.0:8080', '[::]:8080')
    need(loopback or relay, 'Nonloopback listener outside exact relay bind')
    return {'endpoint': local, 'address': str(address), 'port': port,
            'scope': 'namespace-loopback' if loopback else 'relay-wildcard'}


def validate_namespace_listeners(raw):
    need(type(raw) is bytes and len(raw) <= 1048576, 'Bounded actual listener inventory required')
    lines = raw.decode('ascii', 'strict').splitlines()
    need(0 < len(lines) <= 4096, 'Nonempty bounded listener inventory required')
    rows = []
    for line in lines:
        fields = line.split()
        need(len(fields) == 5 and fields[0] == 'LISTEN'
             and all(re.fullmatch('[0-9]{1,10}', value) and int(value) <= 4294967295 for value in fields[1:3])
             and fields[4] in ('0.0.0.0:*', '[::]:*', '*:*'), 'Malformed actual ss listener row')
        rows.append(classify_listener_endpoint(fields[3]))
    return rows


def qualify_namespace(runtime):
    """Inventory gate precedes listeners and any caller's install/UI phase."""
    addresses = runtime.guest('android', ['probe', 'ip', '-j', 'addr'], 15)
    runtime.put_bytes('evidence/network-addresses.json', addresses)
    validate_namespace_addresses(addresses)
    listeners = runtime.guest('android', ['probe', 'ss', '-H', '-lnt'], 15)
    runtime.put_bytes('evidence/listeners.txt', listeners)
    runtime.put_json('evidence/listener-classification.json', validate_namespace_listeners(listeners))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    return [pin(HERE / name) for name in ('supervisor.py', 'lease_guard.py',
            'android_driver.py', 'ui-plan.json', 'fixture.mjs', 'fixture-plan.json',
            'minimum-plan.json', 'business-rumor.json', 'chat-rumor.json',
            'exchange.mjs', 'phase-writer.mjs', 'dependency-tree.mjs', 'dependency-tree.json',
            'capture-budget.mjs', 'exchange-adapter.mjs', 'proxy-observer.mjs')]


def verify_rebuilt_artifacts(bindings=None):
    """Host DATA binding only; no tools, native or APK code is executed."""
    bindings = strict((HERE / 'rebuilt-artifact-bindings.json').read_bytes()) if bindings is None else bindings
    need(bindings['state'] == 'SOURCE_BOUND_REQUIRES_REVIEW_AND_ROLE_RELEASE'
         and all(bindings[k] is not None for k in ('amethystApk','amethystProvenance','amethystAcceptance','amethystAcceptanceDecision')),
         'New accepted Amethyst APK is NULL_NOT_READY; no historical artifact fallback')
    need(bindings['schema'] == 'e02-ordinary-rebuilt-artifact-bindings-v1'
         and bindings['runtimeSourceCount'] == 16, 'Exact rebuilt producer binding scope')
    for key in ('amethystApk','amethystProvenance','amethystAcceptance','helperApk','helperProvenance','helperAcceptance','rustBinary','acceptedE01','acceptedE01Acceptance','originalCanonicalE01'):
        checked(bindings[key])
    apk_origin = strict(checked(bindings['amethystProvenance']).read_bytes())
    apk_acceptance = strict(checked(bindings['amethystAcceptance']).read_bytes())
    need(apk_origin['apk'] == bindings['amethystApk'] and apk_acceptance['subject'] == bindings['amethystProvenance']
         and bindings['amethystAcceptanceDecision'] == 'ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY'
         and apk_acceptance['decision'] == 'ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY'
         and apk_acceptance['schema'] == 'nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1'
         and apk_acceptance.get('artifactQualified') is True, 'Actual accepted rebuilt APK provenance join')
    helper_origin = strict(checked(bindings['helperProvenance']).read_bytes())
    helper_acceptance = strict(checked(bindings['helperAcceptance']).read_bytes())
    need(helper_origin['apk'] == bindings['helperApk'] and helper_acceptance['subject'] == bindings['helperProvenance']
         and helper_acceptance['decision'] == 'ACCEPT_REBUILT_HELPER_ARTIFACT_ONLY'
         and helper_acceptance['schema'] == 'nbdp-actual-artifact-data-acceptance-v1'
         and helper_acceptance.get('artifactQualified') is True, 'Actual accepted rebuilt helper join')
    e01 = strict(checked(bindings['acceptedE01']).read_bytes())
    original = strict(checked(bindings['originalCanonicalE01']).read_bytes())
    acceptance = strict(checked(bindings['acceptedE01Acceptance']).read_bytes())
    need(e01['status'] == 'PASS' and len(e01['tests']) == 140 and all(t['ok'] is True for t in e01['tests'])
         and e01['skipped'] == [] and len(e01['source_sha256']) == 19
         and e01['source_sha256'] == original['source_sha256'] == bindings['expectedOriginal19Sources'], 'Exact original19 source PASS140 E01 binding')
    need(e01['environment']['rust_binary_sha256'] == bindings['rustBinary']['sha256']
         and bindings['rustBinary']['sha256'] == '4ce385c5b1a713b35d58d787d94fbc298d139aa2e813daec15b2e99289cefd86'
         and acceptance['nativeSha256'] == bindings['rustBinary']['sha256'] and acceptance['report'] == bindings['acceptedE01']
         and acceptance['decision'] == 'ACCEPT_ACTUAL_E01_REPLAY_FOR_EXACT_REBUILT_NATIVE_CANDIDATE', 'Current accepted E01/native equality')
    for relative, expected in e01['source_sha256'].items():
        path = REPO / 'experiments' / relative
        need(not path.is_symlink() and digest(path) == expected, 'Current original19 E01 source drift')
    runtime = strict((HERE / 'runtime-plan.json').read_bytes())
    fixture = strict((HERE / 'fixture-plan.json').read_bytes())
    need(runtime['amethystApk'] == bindings['amethystApk'] and runtime['helperApk'] == bindings['helperApk']
         and runtime['sdkRoot'] == bindings['runtimeSdk'] == '/tmp/nbdp-e02-api35-fixture-r2/sdk'
         and runtime['runtimeImage'] == bindings['runtimeImage'] == RUNTIME, 'Runtime-only SDK434/image and exact rebuilt APK/helper')
    for key, value in (('rustBinary',bindings['rustBinary']),('e01',bindings['acceptedE01'])):
        need({k: fixture['pins'][key][k if k != 'path' else 'source'] for k in ('path','bytes','sha256')} == value, 'Exact host/runtime native/E01 staged source join')
    need({k: fixture['pins']['rebuiltBindings'][k if k != 'path' else 'source'] for k in ('path','bytes','sha256')} == pin(HERE / 'rebuilt-artifact-bindings.json'), 'Hash-bound supplemental artifact DATA')
    return bindings


def materialize(destination, run_id, seconds, ordinary_role):
    """Prepare bytes only; does not issue a lease, import workers or start Docker."""
    verify_rebuilt_artifacts()
    need(re.fullmatch('[0-9a-f]{32}', run_id) and 60 <= seconds <= 1800, 'Fresh bounded run identity')
    old = strict((HERE / 'runtime-plan.json').read_bytes())
    config = {k: old[k] for k in ('schema', 'scope', 'runtimeImage', 'relayImage',
              'sdkRoot', 'amethystApk', 'helperApk')}
    minimum = strict((HERE / 'minimum-plan.json').read_bytes())
    need(ordinary_role in ('incoming', 'archive'), 'Closed separately granted role required')
    role = minimum['roles'][ordinary_role]
    config.update(profileId=PROFILE, ordinaryRole=ordinary_role, windowId=role['windowId'],
                  account=role['account'], peer=role['peer'],
                  runId=run_id, originalLeaseSeconds=seconds,
                  sourceAndDependencyPins=source_pins(),
                  sdkInventory=pin(REPO / 'docs/decisions/evidence/e02-api35-fixture-preparation-r2/sdk-tree.json'),
                  guardBundleInventory=pin(OLD / 'records/guard-bundle-manifest.json'),
                  guardBundleRoot=str(OLD / 'guard-python'),
                  relayConfig=pin(REPO / 'experiments/docker/rs-relay.toml'),
                  state='PINNED_CANDIDATE_REQUIRES_SEPARATE_REVIEW_AND_RELEASE',
                  canonicalE02='PARTIAL22_UNCHANGED')
    return put(destination, jsonbytes(config))


def verify_config(config):
    bindings = verify_rebuilt_artifacts()
    need(config['amethystApk'] == bindings['amethystApk'] and config['helperApk'] == bindings['helperApk'],
         'Role configuration artifacts differ from accepted rebuilt bindings')
    need(config['sdkRoot'] == bindings['runtimeSdk'] and config['runtimeImage'] == bindings['runtimeImage'],
         'Role configuration runtime SDK/image differs from accepted rebuilt bindings')
    need(all(config[name] == expected for name, expected in REVIEWED_RUNTIME_INPUTS.items()),
         'Role configuration metadata differs from immutable reviewed blueprint')
    need(config['schema'] == 'e02-ordinary-minimum-role-runtime-plan-v2' and config['scope'] == SCOPE,
         'Fixed first slice only')
    need(config['profileId'] == PROFILE and config['ordinaryRole'] in ('incoming', 'archive'),
         'Fixed adopted minimum profile and role required')
    minimum = strict((HERE / 'minimum-plan.json').read_bytes())
    role = minimum['roles'][config['ordinaryRole']]
    need(minimum['profileId'] == PROFILE and config['windowId'] == role['windowId']
         and config['account'] == role['account'] and config['peer'] == role['peer'],
         'Exact fixed account/window bindings required')
    need(config['runtimeImage'] == RUNTIME and config['relayImage'] == RELAY, 'Exact cached images only')
    need(re.fullmatch('[0-9a-f]{32}', config['runId']) and type(config['originalLeaseSeconds']) is int
         and 60 <= config['originalLeaseSeconds'] <= 1800, 'Immutable finite run required')
    need(config['sourceAndDependencyPins'] == source_pins(), 'Current full worker source pins required')
    for name in ('amethystApk', 'helperApk', 'relayConfig', 'sdkInventory', 'guardBundleInventory'):
        checked(config[name])
    need(config['sdkRoot'] == '/tmp/nbdp-e02-api35-fixture-r2/sdk'
         and config['guardBundleRoot'] == str(OLD / 'guard-python'), 'Fixed cached roots')
    # Exact SDK file inventory includes modes and safe in-tree symlinks.
    inventory = strict(checked(config['sdkInventory']).read_bytes())
    root = Path(config['sdkRoot'])
    rows = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            need(path.resolve(strict=True).is_relative_to(root), 'SDK symlink escapes')
            rows.append({'path': str(path.relative_to(root)), 'symlink': str(path.readlink())})
        elif path.is_file():
            rows.append({'path': str(path.relative_to(root)), 'size': path.stat().st_size,
                         'mode': oct(path.stat().st_mode & 0o777), 'sha256': digest(path)})
        else:
            need(path.is_dir(), 'Unexpected SDK special file')
    need(rows == inventory['files'], 'SDK installed inventory changed')
    bundle = strict(checked(config['guardBundleInventory']).read_bytes())
    for name, descriptor in bundle['files'].items():
        path = Path(config['guardBundleRoot']) / name
        need(path.resolve(strict=True).is_relative_to(Path(config['guardBundleRoot']))
             and not path.is_symlink() and path.stat().st_size == descriptor['bytes']
             and digest(path) == descriptor['sha256'], 'Guard interpreter bundle changed')
    fixture = strict((HERE / 'fixture-plan.json').read_bytes())
    for descriptor in [*fixture['pins'].values(), *fixture['oracles'].values()]:
        checked({k: descriptor[k] if k != 'path' else descriptor['source']
                 for k in ('path', 'bytes', 'sha256')})
    verify_dependency_inventory(fixture, strict((HERE / 'dependency-tree.json').read_bytes()),
                                REPO / 'experiments/node_modules')
    # Preserve source-specific provenance. Historical PASS is not copied onto changes.
    for record in ('E01.json', 'E02.json'):
        value = strict((REPO / 'experiments/results' / record).read_bytes())
        for relative, expected in value['source_sha256'].items():
            path = REPO / 'experiments' / relative
            need(not path.is_symlink() and digest(path) == expected, 'Canonical prerequisite provenance drift')
    return fixture


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

    def map_session_pin(self, descriptor):
        path = PurePosixPath(descriptor['path'])
        need(path.is_relative_to('/session/fixtures') and '..' not in path.parts, 'Fixed fixture mapping')
        result = dict(descriptor, path=str(self.out / 'session/fixtures' / path.relative_to('/session/fixtures')))
        checked(result)
        return result

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

    def adb(self, args, timeout=30):
        need(self.guard.allowed_adb(args), 'Closed ADB allowlist refused')
        ceiling = self.guard.adb_timeout(args)
        need(0 < timeout <= ceiling, 'Fixed ADB ceiling')
        return self.guest('android', ['adb', *args], timeout + 5)

    def fixture(self, operation):
        need(operation in ('prepare', 'status', 'publish'), 'Fixed fixture operations')
        self.check()
        self.inspect('fixture')
        raw = self.command(['exec', self.ids['fixture'], '/usr/local/bin/node', '/input/fixture.mjs', operation], 55)
        self.check()
        return raw

    def snapshot(self, name):
        need(re.fullmatch('[a-z0-9-]{1,64}', name), 'Named snapshot required')
        self.adb(['shell', 'uiautomator', 'dump', '/sdcard/nbdp-window.xml'])
        xml = self.adb(['shell', 'cat', '/sdcard/nbdp-window.xml'])
        png = self.adb(['exec-out', 'screencap', '-p'])
        need(png.startswith(b'\x89PNG\r\n\x1a\n') and b'<hierarchy' in xml, 'Actual UI bytes required')
        return {'xml': self.put_bytes('ui/' + name + '.xml', xml),
                'png': self.put_bytes('ui/' + name + '.png', png)}

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
        need(devices == ([{'PathOnHost': '/dev/kvm', 'PathInContainer': '/dev/kvm',
                          'CgroupPermissions': 'rw'}] if role == 'android' else []), 'Exact KVM device only')

    def start(self, role):
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
        if role == 'rs-relay':
            mount(self.plan['guardBundleRoot'], '/guard-python')
            mount(self.plan['relayConfig']['path'], '/src/config.toml')
            mount(self.out / 'relay-data', '/data', True)
        if role == 'fixture':
            mount(self.out / 'session/fixtures', '/session/fixtures', True)
            mount(REPO / 'experiments/node_modules', '/input/node_modules')
            for d in self.fixture_plan['pins'].values():
                mount(d['source'], d['path'])
        if role == 'android':
            mount(self.plan['sdkRoot'], '/sdk')
            mount(self.plan['amethystApk']['path'], '/artifact.apk')
            mount(self.plan['helperApk']['path'], '/helper.apk')
            mount(self.out / 'android-state', '/state', True)
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
        if role == 'android':
            args += ['--device', '/dev/kvm:/dev/kvm:rw', '--group-add', str(os.stat('/dev/kvm').st_gid)]
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


def guest(role):
    """Fixed service entrypoints. Every nested payload has the original lease."""
    need(role in ROLES, 'Fixed owned role only')
    guard = load_module('e02_guest_guard', '/input/lease_guard.py')
    lease = guard.Lease('/session/lease.json', os.environ['NBDP_LEASE_SHA256'], '/session/control')
    lease.check()
    env = dict(guard.ENV, NBDP_LEASE_SHA256=os.environ['NBDP_LEASE_SHA256'],
               NBDP_FIXTURE_PLAN_SHA256=os.environ['NBDP_FIXTURE_PLAN_SHA256'],
               NBDP_MINIMUM_RUN_CONFIG_SHA256=os.environ['NBDP_MINIMUM_RUN_CONFIG_SHA256'])
    signal.signal(signal.SIGTERM, lambda *_: lease.revoke('Owned service interrupted'))
    signal.signal(signal.SIGINT, lambda *_: lease.revoke('Owned service interrupted'))
    def run(argv, timeout):
        run_service(lease, argv, timeout, env)
    if role == 'anchor':
        while True:
            lease.sleep(1)
    if role == 'rs-relay':
        run(['/src/target/release/nostr-rs-relay', '--db', '/data'], 1800)
    elif role == 'fixture':
        run(['/usr/local/bin/node', '/input/fixture.mjs', 'serve'], 1800)
    else:
        lease.check()
        fd = os.open('/dev/kvm', os.O_RDWR); os.close(fd)
        state = Path('/state')
        for relative in ('home', 'android', 'avd/ordinary.avd'):
            lease.dispatch(lambda p=state / relative: p.mkdir(parents=True, exist_ok=False, mode=0o700))
        lease.dispatch(lambda: put(state / 'avd/ordinary.ini', b'avd.ini.encoding=UTF-8\npath=/state/avd/ordinary.avd\npath.rel=avd/ordinary.avd\ntarget=android-35\n'))
        lease.dispatch(lambda: put(state / 'avd/ordinary.avd/config.ini', CONFIG.encode()))
        run(['/sdk/platform-tools/adb', '-L', 'tcp:localhost:5037', 'start-server'], 15)
        run(EMULATOR, 1800)


def execute(config_path, config_sha, release_path, release_sha, out):
    config_pin, release_pin = pin(config_path), pin(release_path)
    need(config_pin['sha256'] == config_sha and release_pin['sha256'] == release_sha, 'External root pins required')
    config, release = strict(config_path.read_bytes()), strict(release_path.read_bytes())
    fixture = verify_config(config)  # All source/provenance checks before dependent imports.
    need(release['schema'] == 'e02-ordinary-minimum-role-release-v2' and release['executionAuthorized'] is True
         and release['runConfig'] == config_pin and release['scope'] == SCOPE
         and release['runId'] == config['runId'] and release['profileId'] == PROFILE
         and release['ordinaryRole'] == config['ordinaryRole']
         and release['windowId'] == config['windowId'], 'Exact root first-cell release required')
    for key in ('qaReview', 'securityReview', 'guardRegressionEvidence'):
        checked(release[key])
    need(out == LAB / 'runs' / config['runId'] and not os.path.lexists(out), 'Fresh fixed own run directory')
    need(shutil.disk_usage(LAB).free >= 6 * 1024**3, 'At least6GiB persistent free required')
    available = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
    need(available >= 12 * 1024**3, 'At least12GiB MemAvailable required')
    require_android_affinity()
    need(stat.S_ISCHR(os.stat('/dev/kvm').st_mode), 'Exact KVM device required')
    guard = load_module('e02_host_guard', HERE / 'lease_guard.py')
    out.mkdir(parents=True, mode=0o700)
    for directory in ('input', 'session/control', 'session/fixtures', 'android-state', 'relay-data', 'docker-config'):
        (out / directory).mkdir(parents=True, mode=0o700)
    put(out / 'docker-config/config.json', b'{}\n')
    # Original issuance includes input staging and every subsequent resource action.
    lease_value = guard.issue(config['runId'], config['originalLeaseSeconds'])
    need(type(release['notAfterUtcNs']) is int and lease_value['deadlineUtcNs'] <= release['notAfterUtcNs'], 'Original deadline outside release')
    lease_pin = put(out / 'session/lease.json', jsonbytes(lease_value))
    lease = guard.Lease(lease_pin['path'], lease_pin['sha256'], out / 'session/control')
    runtime = Runtime(config, config_pin, release_pin, out, guard, lease, fixture)
    signal.signal(signal.SIGTERM, lambda *_: lease.revoke('Coordinator interrupted'))
    signal.signal(signal.SIGINT, lambda *_: lease.revoke('Coordinator interrupted'))
    error = None
    try:
        for descriptor in config['sourceAndDependencyPins']:
            runtime.put_bytes('input/' + Path(descriptor['path']).name, checked(descriptor).read_bytes())
        runtime.put_bytes('input/run-config.json', config_path.read_bytes())
        # Nested read-only bind targets must exist before mounting /input RO.
        for descriptor in fixture['pins'].values():
            target = out / 'input' / PurePosixPath(descriptor['path']).relative_to('/input')
            runtime.check(); put(target, b''); runtime.check()
        runtime.check(); (out / 'input/node_modules').mkdir(mode=0o700); runtime.check()
        runtime.inputs_sealed = True
        runtime.check()
        for role in ROLES:
            runtime.start(role)
        runtime.adb(['wait-for-device'], timeout=180)
        for _ in range(240):
            if runtime.adb(['shell', 'getprop', 'sys.boot_completed']).strip() == b'1':
                break
            runtime.sleep(1)
        else:
            raise RuntimeError('Guest boot phase timed out')
        qualify_namespace(runtime)
        runtime.adb(['install', '--no-streaming', '/artifact.apk'], timeout=180)
        runtime.adb(['install', '-t', '--no-streaming', '/helper.apk'])
        runtime.adb(['reverse', 'tcp:17777', 'tcp:17777'])
        runtime.put_bytes('evidence/adb-reverse.txt', runtime.adb(['reverse', '--list']))
        for property_name in ('ro.build.fingerprint', 'ro.build.version.sdk'):
            runtime.put_bytes('evidence/' + property_name + '.txt', runtime.adb(['shell', 'getprop', property_name]))
        driver = load_module('e02_first_cell_driver', out / 'input/android_driver.py')
        result = driver.run(runtime)
        runtime.put_json('driver-result.json', result)
        runtime.check()
    except BaseException as exc:
        error = repr(exc)
        try:
            lease.revoke('First-cell stopped: ' + error)
        except BaseException:
            pass
    finally:
        try:
            cleanup = runtime.cleanup()
        except BaseException as failure:
            cleanup = {'ok': False, 'rows': [], 'evidence': None,
                       'errors': ['Unexpected cleanup failure: ' + repr(failure)]}
        try:
            verify_dependency_inventory(fixture, strict((HERE / 'dependency-tree.json').read_bytes()),
                                        REPO / 'experiments/node_modules')
        except BaseException as failure:
            if error is None:
                error = 'End dependency closure failed: ' + repr(failure)
            else:
                cleanup.setdefault('errors', []).append('End dependency closure failed: ' + repr(failure))
        final_code = finalize(out, {'schema': 'e02-ordinary-minimum-role-supervisor-result-v2',
            'runId': config['runId'], 'profileId': PROFILE,
            'ordinaryRole': config['ordinaryRole'], 'windowId': config['windowId'], 'runConfig': config_pin, 'runRelease': release_pin,
            'lease': lease_pin, 'canonicalE02Changed': False,
            'limits': ['One cell only; mandatory wider matrix remains missing.',
                       'No hard realtime/suspended-host cleanup guarantee.',
                       'Independent QA/security must inspect actual results before acceptance.']}, error, cleanup)
    return final_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guest', choices=ROLES)
    parser.add_argument('--materialize', type=Path)
    parser.add_argument('--ordinary-role', choices=('incoming', 'archive'))
    parser.add_argument('--run-id')
    parser.add_argument('--seconds', type=int, default=1800)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--config-sha')
    parser.add_argument('--release', type=Path)
    parser.add_argument('--release-sha')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.guest:
        need(len(sys.argv) == 3, 'Closed guest invocation')
        guest(args.guest)
        return 0
    if args.materialize:
        need(args.run_id and not args.config and not args.release and not args.out, 'Materialize only')
        print(json.dumps(materialize(args.materialize, args.run_id, args.seconds, args.ordinary_role)))
        return 0
    need(all((args.config, args.config_sha, args.release, args.release_sha, args.out)), 'Exact externally pinned config/release/out required')
    return execute(args.config, args.config_sha, args.release, args.release_sha, args.out)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        sys.stderr.write(type(exc).__name__ + ': ' + str(exc)[:4096] + '\n')
        raise SystemExit(2)
