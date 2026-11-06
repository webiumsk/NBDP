"""Finite host adapter for the one-CID controller. No experiment on import.

Bootstrap accepts only externally pinned plan/release, verifies reviewed code
before loading it, and refuses all NULL skeleton gates before Docker or staging.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
import time

PYTHON = '/home/peterhorvath/.miniforge3/bin/python3.13'
DOCKER = '/usr/bin/docker'
HERE = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2')
REUSED = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r1')
RAW_TOOL_LIMIT = 2_147_483_648
RAW_TOOL_CHUNK = 65_536
GUARD_MANIFEST = {'path': '/tmp/nbdp-e02-minimal-rs-v7/records/guard-bundle-manifest.json',
                  'bytes': 332736, 'sha256': '9de311222ef78e20fbe05bfef32898976d80737d5d932166d23431a04a73a454'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def safe(path):
    p = Path(path)
    need(p.is_absolute() and '..' not in p.parts and ',' not in str(p), 'ABSOLUTE_SIMPLE_PATH')
    for q in (p, *p.parents):
        need(not q.is_symlink(), 'NO_PATH_SYMLINK')
    return p


def raw_read(path, cap, check=lambda: None):
    p = safe(path)
    first = p.lstat()
    need(stat.S_ISREG(first.st_mode) and first.st_nlink == 1 and first.st_size <= cap, 'BOUNDED_UNALIASED_REGULAR')
    def ident(st):
        return (st.st_dev, st.st_ino, st.st_size, st.st_mode, st.st_mtime_ns, st.st_ctime_ns, st.st_nlink)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    blocks = []
    with os.fdopen(fd, 'rb', buffering=0) as stream:
        need(ident(os.fstat(stream.fileno())) == ident(first), 'OPENED_IDENTITY')
        while True:
            check()
            block = stream.read(65536)
            if not block:
                break
            blocks.append(block)
            need(sum(map(len, blocks)) <= cap, 'READ_BOUND')
        need(ident(os.fstat(stream.fileno())) == ident(first), 'READ_IDENTITY_DRIFT')
    need(ident(p.lstat()) == ident(first), 'PATH_IDENTITY_DRIFT')
    return b''.join(blocks), stat.S_IMODE(first.st_mode)


def verify(descriptor, check=lambda: None, cap=8_388_608):
    need(type(descriptor) is dict and set(descriptor) == {'path', 'bytes', 'sha256'}, 'CLOSED_PIN')
    need(type(descriptor['bytes']) is int and 0 <= descriptor['bytes'] <= cap and
         re.fullmatch('[0-9a-f]{64}', descriptor['sha256'] or ''), 'BOUNDED_PIN')
    raw, _ = raw_read(descriptor['path'], cap, check)
    need(len(raw) == descriptor['bytes'] and hashlib.sha256(raw).hexdigest() == descriptor['sha256'], 'EXPECTED_PIN_DRIFT')
    return raw


def verify_raw_tool(descriptor, check=lambda: None):
    """RAW opaque executable authority, never JSON, copied bytes or execution.

    Only the two declared fixed paths are admitted. At most one64KiB block is
    held; original absolute clocks are checked before/after each read/hash and
    identity observation. The RAW2GiB ceiling grants no physical-proof budget.
    """
    need(type(descriptor) is dict and set(descriptor) == {'path', 'bytes', 'sha256'}, 'CLOSED_RAW_TOOL_PIN')
    need(type(descriptor['path']) is str and descriptor['path'] in (PYTHON, DOCKER) and type(descriptor['bytes']) is int and
         0 < descriptor['bytes'] <= RAW_TOOL_LIMIT and type(descriptor['sha256']) is str and
         re.fullmatch('[0-9a-f]{64}', descriptor['sha256']), 'DECLARED_RAW_TOOL2GIB')
    check()
    path = safe(descriptor['path'])
    initial = path.lstat()
    need(stat.S_ISREG(initial.st_mode) and initial.st_nlink == 1 and
         initial.st_size == descriptor['bytes'], 'RAW_TOOL_EXPECTED_REGULAR_SIZE')
    def ident(value):
        return (value.st_dev, value.st_ino, value.st_size, value.st_mode, value.st_mtime_ns,
                value.st_ctime_ns, value.st_nlink, value.st_uid, value.st_gid)
    fd, first, result = None, None, None
    try:
        check()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        need(ident(os.fstat(fd)) == ident(initial), 'RAW_TOOL_OPENED_IDENTITY')
        digest, size = hashlib.sha256(), 0
        while True:
            check()
            # One extra byte detects growth beyond the exact expected length.
            block = os.read(fd, min(RAW_TOOL_CHUNK, descriptor['bytes'] - size + 1))
            check()
            if not block:
                break
            size += len(block)
            need(size <= descriptor['bytes'] and size <= RAW_TOOL_LIMIT, 'RAW_TOOL_STREAM_LENGTH')
            digest.update(block)
            check()
        need(size == descriptor['bytes'] and digest.hexdigest() == descriptor['sha256'], 'RAW_TOOL_EXPECTED_SHA_LENGTH')
        check()
        need(ident(os.fstat(fd)) == ident(initial), 'RAW_TOOL_FINAL_FD_IDENTITY')
        need(ident(path.lstat()) == ident(initial), 'RAW_TOOL_FINAL_PATH_IDENTITY')
        check()
        result = dict(descriptor)  # No binary bytes are returned or retained.
    except BaseException as error:
        first = error
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except BaseException as error:
                first = first or error
    if first is not None:
        raise first
    check()  # Close time also belongs to the same original caller deadline.
    return result


def verify_raw_tools(tools, check=lambda: None):
    need(type(tools) is dict and set(tools) == {'python', 'docker'} and
         tools['python']['path'] == PYTHON and tools['docker']['path'] == DOCKER, 'EXACT_TWO_RAW_TOOLS')
    return [verify_raw_tool(tools[key], check) for key in ('python', 'docker')]


def strict(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, 'DUPLICATE_JSON_KEY')
            out[key] = value
        return out
    def reject(_):
        raise ValueError('INTEGER_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)


def pin(path):
    raw, _ = raw_read(path, 8_388_608)
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def exclusive(path, raw):
    fd = os.open(safe(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    first = None
    try:
        need(stat.S_ISREG(os.fstat(fd).st_mode), 'PROOF_REGULAR')
        need(os.write(fd, raw) == len(raw), 'SHORT_IMMUTABLE_WRITE_NO_REPAIR')
        os.fsync(fd)
        need(os.fstat(fd).st_size == len(raw), 'PHYSICAL_WRITE_LENGTH')
    except BaseException as error:
        first = error
    finally:
        try:
            os.close(fd)
        except BaseException as error:
            first = first or error
    if first is not None:
        raise first


def import_pinned(name, descriptor, check=lambda: None):
    verify(descriptor, check)
    spec = importlib.util.spec_from_file_location(name, descriptor['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    check()
    return module


def private_roots(plan):
    roots = [safe(plan[k]) for k in ('inputRoot', 'controlRoot', 'outputRoot', 'dockerConfig')]
    need(len(set(roots)) == 4 and all(not a.is_relative_to(b) for a in roots for b in roots if a != b),
         'DISJOINT_PRIVATE_ROOTS')
    need(all(not p.exists() for p in roots), 'FRESH_ONE_USE_ROOTS')
    parent = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1') / plan['runId']
    need(all(p.parent == parent for p in roots) and stat.S_IMODE(parent.stat().st_mode) == 0o700 and
         parent.stat().st_uid == os.getuid(), 'FIXED_PRIVATE_CONCRETE_PARENT')
    return roots


def bootstrap_sample():
    # Metadata/source admission is inside T0+30, including pre-import bootstrap.
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    need([line.split() for line in Path('/proc/self/timens_offsets').read_text().splitlines()] ==
         [['monotonic', '0', '0'], ['boottime', '0', '0']], 'ZERO_TIME_NAMESPACE')
    return {'Utc': time.time_ns(), 'Mono': time.monotonic_ns(),
            'Boot': time.clock_gettime_ns(time.CLOCK_BOOTTIME), 'bootId': boot}


class Host:
    def __init__(self, core, finite, constants, plan_pin, subject_pin, release_pin, release, original):
        self.core, self.finite, self.constants = core, finite, constants
        self.plan_pin, self.subject_pin, self.release_pin, self.release = plan_pin, subject_pin, release_pin, release
        self.original = original
        self.sample = original.sample
        self.lease = None
        self.staged = False
        self.attached_names = set()

    def check_lease(self):
        need(self.lease is not None, 'ORIGINAL_LEASE_INSTALLED')
        return self.lease.check()

    def revoke(self, error):
        if self.lease is not None:
            self.lease.revoke(error)

    def admit(self, plan, plan_sha, check):
        check()
        need(self.core.closed_plan(plan) is plan, 'CLOSED_PLAN')
        need(plan['source8'] == self.constants['source8'] and plan['guardManifest'] == GUARD_MANIFEST,
             'FIXED_ACCEPTED_SOURCE_AND_GUARD_AUTHORITY')
        need(plan['gates']['producerSource'] == self.constants['acceptedProducerSubject'], 'ACCEPTED_PRODUCER_SUBJECT')
        need(plan['gates']['controllerSource'] == self.subject_pin,
             'CURRENT_CONTROLLER_RELEASE')
        need(self.release['plan'] == self.plan_pin and self.release['subject'] == self.subject_pin and
             self.release['gates'] == plan['gates'], 'EXACT_RELEASE_BINDINGS')
        # External Root is responsible for the authenticity of these separately
        # reviewed acceptance receipts. No historical acceptance is substituted.
        for key, descriptor in plan['gates'].items():
            verify(descriptor, check)
        need(type(self.release['authors']) is list and type(self.release['operators']) is list and
             set(self.constants['sourceContributors']).issubset(self.release['authors']) and
             len(self.release['operators']) > 0 and all(type(x) is str and x.startswith('/root') for x in
             self.release['authors'] + self.release['operators']), 'ACTUAL_AUTHOR_OPERATOR_UNION')
        for kind in ('producerData', 'sourceQa', 'sourceSecurity', 'controlData', 'concreteInput'):
            receipt = strict(verify(plan['gates'][kind], check))
            need(set(receipt) == {'schema', 'kind', 'actor', 'decision', 'subject', 'evidence', 'scope'} and
                 receipt['schema'] == 'e02-one-cid-helper-probe-gate-v1' and receipt['kind'] == kind and
                 receipt['decision'] == 'ACCEPT' and receipt['scope'] == 'ONE_OWNED_HELPER_PROBE_ONLY', 'CLOSED_GATE_RECEIPT')
            concrete = {'scope': 'CURRENT_CONCRETE_INPUTS', 'sha256': hashlib.sha256(self.core.encoded(
                {k: v for k, v in plan.items() if k != 'gates'})).hexdigest()}
            expected = (plan['gates']['producerSource'] if kind == 'producerData' else
                        concrete if kind == 'concreteInput' else self.subject_pin)
            need(receipt['subject'] == expected, 'CURRENT_GATE_SUBJECT')
            verify(receipt['evidence'], check)  # Exact underlying actual review/DATA, no old DATA transfer.
            if kind in ('sourceQa', 'sourceSecurity'):
                need(type(receipt['actor']) is str and receipt['actor'].startswith('/root/') and
                     receipt['actor'] not in self.release['authors'] + self.release['operators'], 'INDEPENDENT_REVIEWER')
        qa = strict(verify(plan['gates']['sourceQa'], check))
        sec = strict(verify(plan['gates']['sourceSecurity'], check))
        need(qa['actor'] != sec['actor'], 'DISTINCT_QA_SECURITY')
        need(plan['tools'].keys() == {'python', 'docker'} and plan['tools']['python']['path'] == PYTHON and
             plan['tools']['docker']['path'] == DOCKER, 'EXACT_HOST_TOOLS')
        verify_raw_tools(plan['tools'], check)
        need(plan['uidGid'] == str(os.getuid()) + ':' + str(os.getgid()), 'ACTUAL_UID_GID')
        private_roots(plan)
        self.sources(plan, check)

    def sources(self, plan, check, staged=False):
        for descriptor in plan['source8']:
            raw = verify(descriptor, check)
            name = Path(descriptor['path']).name
            _, mode = raw_read(descriptor['path'], 8_388_608, check)
            need(mode == self.constants['sourceModes'][name], 'EXPECTED_SOURCE_MODE')
            if staged:
                other, staged_mode = raw_read(Path(plan['inputRoot']) / name, 8_388_608, check)
                need(other == raw and staged_mode == 0o600, 'STAGED_SOURCE_DRIFT')
        if staged:
            need(sorted(p.name for p in Path(plan['inputRoot']).iterdir()) == sorted(self.core.SOURCE_NAMES),
                 'STAGED_EXACT_EIGHT_MEMBERS')
        manifest = strict(verify(plan['guardManifest'], check))
        need(manifest['fileCount'] == len(manifest['files']) == 522, 'GUARD522')
        expected_directories = {'.'}
        for member in manifest['files']:
            expected_directories.update(str(p) for p in Path(member).parents)
        root = safe(plan['guardRoot'])
        found = []
        for directory, subdirs, files in os.walk(root, followlinks=False):
            check()
            need(str(Path(directory).relative_to(root)) in expected_directories, 'NO_UNDECLARED_GUARD_DIRECTORY')
            for name in subdirs:
                need(not (Path(directory) / name).is_symlink(), 'GUARD_NO_DIRECTORY_ALIAS')
                need(str((Path(directory) / name).relative_to(root)) in expected_directories, 'NO_UNDECLARED_GUARD_DIRECTORY')
            for name in files:
                path = Path(directory) / name
                member = str(path.relative_to(root))
                need(member in manifest['files'], 'NO_UNDECLARED_GUARD_MEMBER')
                expected = manifest['files'][member]
                raw, mode = raw_read(path, 8_388_608, check)
                need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'] and
                     mode == expected['mode'], 'GUARD_MEMBER_PIN_OR_MODE')
                found.append(member)
        need(set(found) == set(manifest['files']), 'EXACT_GUARD_MEMBERSHIP')

    def stage(self, plan, ledger, check):
        check()
        self.ledger = ledger
        # Original immutable Lease.revoke retains at most2048 Unicode codepoints
        # plus newline:8193 UTF8 bytes, inside metadata8MiB, not another cap.
        ledger.charge('metadata', 8193)
        # All folders are exclusive, owner-private, and were admitted as absent.
        for key in ('outputRoot', 'inputRoot', 'controlRoot', 'dockerConfig'):
            check()
            safe(plan[key]).mkdir(mode=0o700)
        self.output = Path(plan['outputRoot'])
        for name, value in (('plan.json', self.plan_pin), ('subject.json', self.subject_pin), ('root-release.json', self.release_pin)):
            raw = verify(value, check)
            ledger.write(self.sink, 'metadata', name, raw)
        for descriptor in plan['source8']:
            raw = verify(descriptor, check)
            ledger.write(lambda name, data: exclusive(Path(plan['inputRoot']) / name, data),
                         'metadata', Path(descriptor['path']).name, raw)
        lease_raw = verify(plan['lease'], check, 8192)
        ledger.write(self.sink, 'metadata', 'lease.json', lease_raw)
        self.staged = True
        self.sources(plan, check, staged=True)
        ledger.write(self.sink, 'metadata', 'source-before.json', self.core.encoded(
            {'source8': plan['source8'], 'guardManifest': plan['guardManifest'], 'guardMembersVerified': 522,
             'stagedMembersVerified': 8, 'scope': 'EXPECTED_PINS_NOT_BASELINE_SUBSTITUTION'}))

    def sink(self, name, raw):
        need(re.fullmatch('[a-zA-Z0-9._-]{1,100}', name), 'SIMPLE_PROOF_NAME')
        exclusive(self.output / name, raw)

    def intent(self, plan, plan_sha):
        environment = {**self.core.GUEST_ENV, 'NBDP_LEASE_SHA256': plan['lease']['sha256'],
                       'NBDP_MINIMUM_RUN_CONFIG_SHA256': plan_sha}
        return {'name': plan['name'], 'labels': {'nbdp.run': plan['runId'], 'nbdp.role': 'helper-probe',
                                               'nbdp.creation': plan['creationNonce']},
                'cidfile': str(self.output / 'container.cid'),
                'uidGid': plan['uidGid'], 'environment': [k + '=' + v for k, v in environment.items()],
                'mounts': [[plan['inputRoot'], '/input', False], [plan['guardRoot'], '/guard-python', False],
                           [str(self.output / 'lease.json'), '/session/lease.json', False],
                           [plan['controlRoot'], '/session/control', True]]}

    def create_args(self, intent):
        args = ['create', '--pull=never', '--name', intent['name'], '--cidfile', intent['cidfile'], '--network', 'none', '--ipc', 'private',
                '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--user', intent['uidGid'],
                '--cpus', '1', '--memory', '1024m', '--memory-swap', '1024m', '--pids-limit', '128', '--init',
                '--log-driver', 'none', '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=16m', '--workdir', '/input',
                '--entrypoint', '/usr/local/bin/node']
        for key, value in intent['labels'].items():
            args += ['--label', key + '=' + value]
        for source, target, writable in intent['mounts']:
            args += ['--mount', 'type=bind,src=' + source + ',dst=' + target + ('' if writable else ',readonly')]
        for value in intent['environment']:
            args += ['--env', value]
        return args + [self.core.IMAGE, '/input/probe-guard-helper.mjs']

    def verify_cidfile(self, cid, check):
        raw, mode = raw_read(self.output / 'container.cid', 65, check)
        need(raw in (cid.encode(), cid.encode() + b'\n') and mode & 0o077 == 0, 'EXACT_CIDFILE_NO_ALIAS')

    def cli(self, args, **options):
        need(self.staged, 'NO_DOCKER_BEFORE_ADMISSION_STAGE')
        if options['target']:
            self.attached_names = {f"cli-{options['ordinal']}-stdout.raw", f"cli-{options['ordinal']}-stderr.raw"}
        environment = {**self.core.ENV, 'DOCKER_CONFIG': self.plan['dockerConfig']}
        return self.finite.capture([DOCKER, *args], environment=environment, cwd=str(self.output), **options)

    def before_target(self, plan, check):
        self.sources(plan, check, staged=True)
        for descriptor in self.controller_sources:
            verify(descriptor, check)
        verify_raw_tools(plan['tools'], check)
        raw, _ = raw_read(self.output / 'lease.json', 8192, check)
        need(raw == verify(plan['lease'], check, 8192), 'BEFORE_TARGET_ORIGINAL_LEASE')

    def postread(self, plan, check):
        if self.staged:
            self.sources(plan, check, staged=True)
            for descriptor in self.controller_sources:
                verify(descriptor, check)
            verify_raw_tools(plan['tools'], check)
            need((self.output / 'lease.json').read_bytes() == verify(plan['lease'], check, 8192), 'LEASE_COPY_DRIFT')
            actual = {'attached': 0, 'metadata': 0}
            for key in ('inputRoot', 'controlRoot', 'outputRoot', 'dockerConfig'):
                root = safe(plan[key])
                for path in root.iterdir():
                    check()
                    need(not path.is_dir(), 'NO_UNDECLARED_OUTPUT_DIRECTORY')
                    if key == 'inputRoot':
                        need(path.name in self.core.SOURCE_NAMES, 'EXACT_STAGED_SOURCE_NAMES')
                    elif key == 'controlRoot':
                        need(path.name == 'REVOKED', 'REVOCATION_ONLY_CONTROL')
                    elif key == 'dockerConfig':
                        raise ValueError('NO_UNDECLARED_DOCKER_CONFIG_PROOF')
                    raw, mode = raw_read(path, 8_388_608, check)
                    need(mode & 0o077 == 0, 'PRIVATE_PHYSICAL_PROOF')
                    owner = 'attached' if key == 'outputRoot' and path.name in self.attached_names else 'metadata'
                    actual[owner] += len(raw)
            need(all(actual[k] <= self.ledger.used[k] <= 8_388_608 for k in actual) and
                 sum(actual.values()) <= 16_777_216, 'ACTUAL_PHYSICAL_PROOF_ACCOUNTING')
            self.ledger.write(self.sink, 'metadata', 'source-after.json', self.core.encoded(
                {'source8': plan['source8'], 'guardManifest': plan['guardManifest'], 'guardMembersVerified': 522,
                 'physicalBytesBeforeThisReceiptAndFinalResult': actual, 'snapshotNotRaceFree': True}))

    def validate_probe(self, raw, plan, plan_sha):
        validate_probe(raw, plan, plan_sha, self.core, strict(verify(plan['lease'], cap=8192)))


def validate_probe(raw, plan, plan_sha, core, lease):
    """Closed guest result and fresh65 raw-RPC custody; no backend/UI claim."""
    value = strict(raw)
    need(set(value) == set('schema checks timerMilliseconds elapsedNanoseconds clientRowsQualified relayCause scope durationsNanoseconds timerRows guardController'.split()) and
         value['schema'] == 'e02-owned-fresh-guard-latency-probe-v1' and value['checks'] == 64 and
         value['timerMilliseconds'] == 10 and value['clientRowsQualified'] == 0 and value['relayCause'] == 'UNKNOWN' and
         value['scope'] == 'OWNED_HELPER_LATENCY_TIMER_DISPATCH_ONLY' and
         all(type(value[k]) is int for k in ('checks', 'timerMilliseconds', 'clientRowsQualified')), 'CLOSED_GUEST_PROBE')
    decimal = lambda x: type(x) is str and re.fullmatch('(0|[1-9][0-9]{0,23})', x)
    need(decimal(value['elapsedNanoseconds']) and int(value['elapsedNanoseconds']) < 55 * core.NS and
         type(value['durationsNanoseconds']) is list and len(value['durationsNanoseconds']) == 64 and
         all(decimal(x) and int(x) < 5 * core.NS for x in value['durationsNanoseconds']) and
         sum(map(int, value['durationsNanoseconds'])) <= int(value['elapsedNanoseconds']),
         'EXACT64_DURATIONS')
    need(type(value['timerRows']) is list and 0 < len(value['timerRows']) <= 5500 and
         all(set(x) == {'monoNs', 'gapNs'} and decimal(x['monoNs']) and decimal(x['gapNs']) for x in value['timerRows']),
         'ACTUAL_TIMER_GAPS_NO_PRECISION_THRESHOLD')
    for before, after in zip(value['timerRows'], value['timerRows'][1:]):
        need(int(after['monoNs']) >= int(before['monoNs']) and
             int(after['monoNs']) - int(before['monoNs']) == int(after['gapNs']), 'TIMER_GAP_JOIN')
    audit = value['guardController']
    need(set(audit) == set('schema reservationIndex instance scope runId leaseSha256 configurationSha256 observations'.split()) and
         audit['schema'] == 'e02-controller-guard-audit-v1' and audit['reservationIndex'] is None and
         audit['scope'] == 'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION' and audit['runId'] == plan['runId'] and
         audit['leaseSha256'] == plan['lease']['sha256'] and audit['configurationSha256'] == plan_sha and
         re.fullmatch('[0-9a-f]{32}', audit['instance'] or ''), 'BOUND_NODE_HELPER_AUDIT')
    import base64
    entries, requests, replies, exits = [], [], [], []
    lifecycle = {}
    positions = {'GUARD_ENTRY': [], 'GUARD_RPC_REQUEST': [], 'GUARD_RPC_REPLY': [], 'GUARD_EXIT': []}
    field_keys = {
        'GUARD_ENTRY': 'helperInstance label guardSequence enqueueMonoNs',
        'GUARD_RPC_REQUEST': 'helperInstance label guardSequence rawBase64 enqueueMonoNs decisionDeadlineMonoNs enqueueUtcLowerNs enqueueBootLowerNs decisionDeadlineUtcNs decisionDeadlineBootNs',
        'GUARD_RPC_REPLY': 'helperInstance guardSequence rawBase64',
        'GUARD_EXIT': 'helperInstance label guardSequence ok error consumed consumedUtcUpperNs consumedMonoNs consumedBootUpperNs',
        'GUARD_HELPER_LAUNCH': 'helperInstance executable argv',
        'GUARD_HELPER_CREATED': 'helperInstance pid',
        'GUARD_HELPER_STDOUT_EOF': 'helperInstance',
        'GUARD_HELPER_STDERR_EOF': 'helperInstance',
        'GUARD_HELPER_EXIT': 'helperInstance code signal',
        'GUARD_HELPER_CLOSE': 'helperInstance code signal stdoutEOF stderrEOF exitSeen'}
    allowed = {'GUARD_ENTRY', 'GUARD_RPC_REQUEST', 'GUARD_RPC_REPLY', 'GUARD_EXIT', 'GUARD_HELPER_LAUNCH',
               'GUARD_HELPER_CREATED', 'GUARD_HELPER_STDOUT_EOF', 'GUARD_HELPER_STDERR_EOF',
               'GUARD_HELPER_EXIT', 'GUARD_HELPER_CLOSE'}
    need(type(audit['observations']) is list and len(audit['observations']) == 266, 'BOUNDED_EXACT_SUCCESS_ROWS')
    for position, row in enumerate(audit['observations']):
        need(set(row) == {'name', 'fields'} and row['name'] in allowed and
             row['fields'].get('helperInstance') == audit['instance'], 'CLOSED_SUCCESS_OBSERVATION')
        name, fields = row['name'], row['fields']
        need(set(fields) == set(field_keys[name].split()), 'CLOSED_OBSERVATION_FIELDS')
        if name in positions:
            positions[name].append(position)
        if name == 'GUARD_ENTRY':
            entries.append(fields)
        elif name == 'GUARD_RPC_REQUEST':
            requests.append(fields)
        elif name == 'GUARD_RPC_REPLY':
            replies.append(fields)
        elif name == 'GUARD_EXIT':
            exits.append(fields)
        else:
            need(name not in lifecycle, 'NO_DUPLICATE_HELPER_LIFECYCLE')
            lifecycle[name] = fields
    need(len(entries) == len(requests) == len(replies) == len(exits) == 65 and
         set(lifecycle) == allowed - {'GUARD_ENTRY', 'GUARD_RPC_REQUEST', 'GUARD_RPC_REPLY', 'GUARD_EXIT'}, 'FRESH65_LIFECYCLE')
    for index, (entry, request_row, reply_row, commit) in enumerate(zip(entries, requests, replies, exits), 1):
        i = index - 1
        need(positions['GUARD_ENTRY'][i] < positions['GUARD_RPC_REQUEST'][i] < positions['GUARD_RPC_REPLY'][i] < positions['GUARD_EXIT'][i] and
             (index == 65 or positions['GUARD_EXIT'][i] < positions['GUARD_ENTRY'][i + 1]), 'ONE_USE_TRACE_ORDER')
        request_raw = base64.b64decode(request_row['rawBase64'], validate=True)
        reply_raw = base64.b64decode(reply_row['rawBase64'], validate=True)
        request, reply = strict(request_raw), strict(reply_raw)
        label, operation = ('owner-close', 'CLOSE') if index == 65 else ('probe:warm-' + str(index - 1), 'CHECK')
        context = b'' if index == 65 else str(index - 1).encode()
        need(set(request) == set('schema operation instance runId leaseSha256 sequence label contextSha256'.split()) and
             request == {'schema': 'e02-fresh-guard-request-v1', 'operation': operation, 'instance': audit['instance'],
                         'runId': plan['runId'], 'leaseSha256': plan['lease']['sha256'], 'sequence': str(index),
                         'label': label, 'contextSha256': hashlib.sha256(context).hexdigest()}, 'EXACT_REQUEST_CONTEXT')
        need(len(request_raw) <= 1024 and request_raw.endswith(b'\n') and len(reply_raw) <= 2048 and reply_raw.endswith(b'\n') and
             set(reply) == set('schema operation instance runId leaseSha256 sequence label contextSha256 requestSha256 ok clocks'.split()) and
             reply['schema'] == 'e02-fresh-guard-response-v1' and reply['ok'] is True and
             reply['requestSha256'] == hashlib.sha256(request_raw).hexdigest() and
             all(reply[k] == request[k] for k in ('operation', 'instance', 'runId', 'leaseSha256', 'sequence', 'label', 'contextSha256')),
             'ONE_USE_BOUND_REPLY')
        need(all(x['guardSequence'] == str(index) for x in (entry, request_row, reply_row, commit)) and
             entry['label'] == request_row['label'] == commit['label'] == label and commit['ok'] is True and
             commit['consumed'] is True and commit['error'] is None, 'EXACT_CONSUMED65')
        need((reply['clocks'] is None) if index == 65 else
             (set(reply['clocks']) == {'Utc', 'Mono', 'Boot', 'bootId'} and all(decimal(reply['clocks'][k]) for k in ('Utc', 'Mono', 'Boot'))),
             'CLOSE_NULL_OR_FRESH_CLOCKS')
        need(all(decimal(request_row[k]) for k in ('enqueueMonoNs', 'decisionDeadlineMonoNs', 'enqueueUtcLowerNs',
             'enqueueBootLowerNs', 'decisionDeadlineUtcNs', 'decisionDeadlineBootNs')) and
             all(decimal(commit[k]) for k in ('consumedUtcUpperNs', 'consumedMonoNs', 'consumedBootUpperNs')), 'DECIMAL_BOUND_CLOCKS')
        for initial, end, consumed in (('enqueueMonoNs', 'decisionDeadlineMonoNs', 'consumedMonoNs'),
                                      ('enqueueUtcLowerNs', 'decisionDeadlineUtcNs', 'consumedUtcUpperNs'),
                                      ('enqueueBootLowerNs', 'decisionDeadlineBootNs', 'consumedBootUpperNs')):
            need(int(request_row[end]) == int(request_row[initial]) + 5 * core.NS and
                 int(request_row[initial]) <= int(commit[consumed]) < int(request_row[end]), 'INCLUSIVE_FRESH5_COMMIT')
        need(entry['enqueueMonoNs'] == request_row['enqueueMonoNs'], 'ENQUEUE_JOIN')
        for kind, consumed in (('Utc', 'consumedUtcUpperNs'), ('Mono', 'consumedMonoNs'), ('Boot', 'consumedBootUpperNs')):
            need(lease['issued' + kind + 'Ns'] <= int(commit[consumed]) < lease['deadline' + kind + 'Ns'], 'ORIGINAL_LEASE_COMMIT')
            if index != 65:
                need(reply['clocks']['bootId'] == lease['bootId'] and lease['issued' + kind + 'Ns'] <=
                     int(reply['clocks'][kind]) <= int(commit[consumed]), 'FRESH_ORIGINAL_CORE_CLOCK')
    for event in ('GUARD_HELPER_EXIT', 'GUARD_HELPER_CLOSE'):
        need(type(lifecycle[event]['code']) is int and lifecycle[event]['code'] == 0 and lifecycle[event]['signal'] is None,
             'NATURAL_HELPER_ZERO')
    close = lifecycle['GUARD_HELPER_CLOSE']
    need(close['stdoutEOF'] is True and close['stderrEOF'] is True and close['exitSeen'] is True and
         type(lifecycle['GUARD_HELPER_CREATED']['pid']) is int and lifecycle['GUARD_HELPER_CREATED']['pid'] > 0,
         'HONEST_HELPER_EOF_EXIT_CLOSE')
    launch = lifecycle['GUARD_HELPER_LAUNCH']
    helper = next(d for d in plan['source8'] if d['path'].endswith('/guard-helper.py'))
    need(launch['executable'] == '/guard-python/lib/ld-linux-x86-64.so.2' and launch['argv'] ==
         ['--inhibit-cache', '--library-path', '/guard-python/lib', '/guard-python/bin/python3.11', '-B', '-P', '-S', '-s',
          '/input/guard-helper.py', audit['instance'], plan['lease']['sha256'], str(helper['bytes']), helper['sha256']],
         'EXACT_ORIGINAL_FACTORY_LAUNCH')


def main(argv=None):
    started = bootstrap_sample()
    previous = started
    def phase_check():
        nonlocal previous
        now = bootstrap_sample()
        need(now['bootId'] == started['bootId'] and all(previous[k] <= now[k] < started[k] + 30_000_000_000
             for k in ('Utc', 'Mono', 'Boot')) and now['Boot'] - previous['Boot'] <= 15_000_000_000,
             'BOOTSTRAP_ABSOLUTE30_OR_CLOCK')
        need(abs((now['Utc'] - started['Utc']) - (now['Boot'] - started['Boot'])) <= 500_000_000,
             'BOOTSTRAP_UTC_BOOT_DRIFT')
        previous = now
    parser = argparse.ArgumentParser()
    for name in ('plan', 'plan-sha', 'root-release', 'root-release-sha'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    need(sys.flags.isolated and sys.dont_write_bytecode and str(Path(sys.executable).resolve()) == PYTHON,
         'EXACT_ISOLATED_HOST_PYTHON')
    # No Docker, import of target sources, mkdir or grant consumption until
    # closed final gates, exact external plan/release and controller code match.
    def bootstrap_pin(path):
        raw, _ = raw_read(path, 8_388_608, phase_check)
        return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    plan_pin, release_pin = bootstrap_pin(safe(args.plan)), bootstrap_pin(safe(args.root_release))
    need(plan_pin['sha256'] == args.plan_sha and release_pin['sha256'] == args.root_release_sha, 'EXTERNAL_ROOT_PINS')
    plan, release = strict(verify(plan_pin, phase_check)), strict(verify(release_pin, phase_check))
    need(type(plan.get('gates')) is dict and all(type(x) is dict for x in plan['gates'].values()), 'NULL_GATE_NO_DOCKER')
    need(set(release) == set('schema actor executionAuthorized runId creationNonce subject plan gates authors operators outerCustodyReservationBytes'.split()) and
         release['schema'] == 'e02-one-cid-helper-probe-root-release-v1' and release['actor'] == '/root' and
         release['executionAuthorized'] is True and release['runId'] == plan['runId'] and
         release['creationNonce'] == plan['creationNonce'] and release['plan'] == plan_pin and
         type(release['outerCustodyReservationBytes']) is int and release['outerCustodyReservationBytes'] == 65536,
         'EXTERNAL_ONE_USE_ROOT_RELEASE')
    subject = strict(verify(release['subject'], phase_check))
    need(subject['schema'] == 'e02-one-cid-helper-probe-controller-source-v1' and len(subject['runtimeSources']) == 3 and
         {Path(d['path']).name for d in subject['runtimeSources']} == {'controller.py', 'host.py', 'finite_child.py'}, 'EXACT_MINIMAL_CODE')
    for descriptor in subject['runtimeSources']:
        expected = HERE / 'host.py' if Path(descriptor['path']).name == 'host.py' else REUSED / Path(descriptor['path']).name
        need(Path(descriptor['path']) == expected, 'FIXED_CONTROLLER_ROOT')
        verify(descriptor, phase_check)
    need(bootstrap_pin(HERE / 'host.py') in subject['runtimeSources'], 'SELF_PIN')
    constants = strict(verify(subject['constants'], phase_check))
    need(constants['methodAdoption']['sha256'] == '15d7741fea900925894116eea3021cae73be0317ed31e84018434f17883ee635', 'EXACT_METHOD_ADOPTION')
    verify(constants['methodAdoption'], phase_check)
    core = import_pinned('helper_probe_controller', next(d for d in subject['runtimeSources'] if d['path'].endswith('/controller.py')), phase_check)
    core.closed_plan(plan)
    private_roots(plan)  # Before original Lease can even attempt sticky writes.
    finite = import_pinned('helper_probe_child', next(d for d in subject['runtimeSources'] if d['path'].endswith('/finite_child.py')), phase_check)
    original_pin = next(d for d in constants['source8'] if d['path'].endswith('/lease_guard.py'))
    original = import_pinned('helper_probe_original_lease', original_pin, phase_check)
    host = Host(core, finite, constants, plan_pin, release['subject'], release_pin, release, original)
    host.controller_sources = subject['runtimeSources']
    host.plan = plan
    lease_raw = verify(plan['lease'], phase_check, cap=8192)
    _, lease_mode = raw_read(plan['lease']['path'], 8192, phase_check)
    need(lease_mode == 0o600 and Path(plan['lease']['path']).parent == Path(plan['outputRoot']).parent and
         Path(plan['lease']['path']).stat().st_uid == os.getuid(), 'OWNED_PRIVATE_ORIGINAL_LEASE')
    lease = strict(lease_raw)
    need(lease['runId'] == plan['runId'] and all(lease['issued' + k + 'Ns'] <= started[k] and
         lease['deadline' + k + 'Ns'] - lease['issued' + k + 'Ns'] == 1800 * core.NS for k in ('Utc', 'Mono', 'Boot')),
         'ORIGINAL1800_NONRENEWABLE_LEASE')
    host.lease = original.Lease(plan['lease']['path'], plan['lease']['sha256'], plan['controlRoot'])
    now = host.check_lease()
    need(all(lease['deadline' + k + 'Ns'] - now[k] >= 183 * core.NS for k in ('Utc', 'Mono', 'Boot')), 'PRESTAGING183_LEASE_REMAINING')
    # Exact outputRoot creates one-use authority; it is never reused or repaired.
    phase_check()
    os.umask(0o077)
    controller = core.Controller(plan, plan_pin['sha256'], host, t0=started)
    result = controller.run()
    return 0 if result['qualified'] else 2


if __name__ == '__main__':
    try:
        exit_code = main()
    except BaseException:
        # No uncharged traceback stream. Root separately retains the actual
        # terminal/API origin and cannot accept missing immutable result proof.
        exit_code = 2
    raise SystemExit(exit_code)
