"""Fixed LOCAL outer monitor; importing starts no work.

SOURCE ONLY until actual independent monitor review and a fresh external root
LOCAL grant. This file creates no grant and imports no project module. The one
fixed qualification child performs actual full admission and then two native
jobs. This trusted-interface monitor is not hostile-host containment.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import time

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = ROOT / 'docs/decisions/evidence/e06-local-fonly-primary-execution-r2'
PREP = ROOT / 'docs/decisions/evidence/e06-local-fonly-primary-preparation-r2'
EVIDENCE = ROOT / 'docs/decisions/evidence'
SOURCE = ROOT / 'experiments/prototypes/e06_relay_https_negative_v1'
ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC',
       'WS_NO_BUFFER_UTIL': '1', 'WS_NO_UTF_8_VALIDATE': '1'}
PINS = {
    'config': {'path': str(HERE / 'qualification-config.json'), 'bytes': 2141,
               'sha256': '538fc931bf82d1507736acd23a98069878201105af8d6e2189f8e0bde0e7bf45'},
    'core': {'path': str(PREP / 'configuration-core.json'), 'bytes': 1864,
             'sha256': '8011833c10a16e58bc2d84e68ab8886e3593e8bc6b074125c8c8ef2f43236518'},
    'worker': {'path': str(PREP / 'worker-config.json'), 'bytes': 114239,
               'sha256': 'fd681b2448333c65b4c717d863b8ed0c840cfb054aa747a6a477a9bc4f8ec22b'},
    'configurationApproval': {'path': str(HERE / 'configuration-approval.json'), 'bytes': 3008,
                              'sha256': 'cf24d9b9fae7e00ae912943243d956693966b9273054e73c0ed0f81488319bed'},
    'configurationQa': {'path': str(HERE / 'configuration-qa-review.json'), 'bytes': 1545,
                        'sha256': 'f52c93e2fc0ccec9794c127357de95c31db82321016feab08d9eb435c8b5577b'},
    'configurationSecurity': {'path': str(HERE / 'configuration-security-review.json'), 'bytes': 1563,
                              'sha256': 'fef8d8fb9a26ed02a26614418d2fca9c037e57e71b5cea83240efd86532dd2e1'},
    'workflow': {'path': str(HERE / 'workflow-prerequisites.json'), 'bytes': 2600,
                 'sha256': 'ce3560af4728eabdb84780b71e38a0317373152ac4d56e4095578122b445588d'},
    'pair': {'path': str(EVIDENCE / 'e06-inventory-enforcement-matrix-qa-r1/pair-acceptance.json'),
             'bytes': 1971, 'sha256': '535d9cb3d30cedc4e1e35d4f54b35ad270adf8d1df4fc62a760136bd6d531c69'},
    'sourceClosure': {'path': str(EVIDENCE / 'e06-qualification-current-source-r3/source-closure.json'),
                      'bytes': 102080, 'sha256': '76cfc1d55602c4c18f7adabde2b67679f3d828517a4cf4abefdf13d57029b100'},
    'sourceApproval': {'path': str(EVIDENCE / 'e06-qualification-current-source-r3/source-approval.json'),
                       'bytes': 107717, 'sha256': 'e3e41bb6bae55d80702f9002cc99c72ad3a6345405a5043d3123dcafcbea685e'},
    'controlApproval': {'path': str(EVIDENCE / 'e06-current-controls-r2/control-approval.json'),
                        'bytes': 1488, 'sha256': 'c2c6d2b97ba4f25dbbb9074c079cd3ad29cbf9fa23aac709b31a97a273c0f5ee'},
    'python': {'path': '/home/peterhorvath/.miniforge3/bin/python3.13', 'bytes': 32959480,
               'sha256': '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'},
    'qualification': {'path': str(SOURCE / 'qualification.py'), 'bytes': 31089,
                      'sha256': '13e9ebf74caa8c473296b009ce66be1c5f02a469f7b2e90ca4cace20a0d175aa'},
    'admission': {'path': str(SOURCE / 'admission.py'), 'bytes': 53263,
                  'sha256': '24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'},
    'runner': {'path': str(SOURCE / 'runner.py'), 'bytes': 27072,
               'sha256': '7ea2ce4721fdc3e5d7f3b53c289d4f017937a5e66c49ae2a6a7ad4b7e5dde655'},
    'qualificationSchema': {'path': str(SOURCE / 'qualification-schemas.json'), 'bytes': 133680,
                            'sha256': 'dcbbbd2c9b84d5cd477718896f287f8abc6f6574e148a04421bc3a9043157a2b'}
}
REVIEWERS = {'qa': '/root/transport_evidence_qa', 'security': '/root/attachment_profile_security'}
PAIR_DECISIONS = {'qa': 'ACCEPT_REAL_INPUT_GATE_MATRIX_PRIMARY_QA_PAIR_ONLY',
                  'security': 'ACCEPT_ACTUAL_CALLER_MEMORY_MATRIX_PAIR_ONLY'}
EXPECTED_AUTHORS = ['/root', '/root/e06_local_configuration', '/root/local_monitor_controls']
OUTPUT = HERE / 'outer-actual'
NATIVE_OUTPUT = Path('/tmp/e6n-fonly-primary-9df61b3f71ac')
TOTAL_SECONDS = 1800
CLEANUP_RESERVE_SECONDS = 30
CAPS = {'stdout': 33554432, 'stderr': 1048576}
MAX_JSON = 33554432


class Refusal(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refusal(message)


def closed(value, keys):
    need(type(value) is dict and set(value) == set(keys), 'CLOSED_KEYS')


def equal(left, right):
    return json.dumps(left, sort_keys=True, separators=(',', ':')) == json.dumps(
        right, sort_keys=True, separators=(',', ':'))


def strict(raw):
    need(type(raw) is bytes and len(raw) <= MAX_JSON, 'JSON_BOUND')
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def integer(token):
        need(token != '-0', 'NEGATIVE_ZERO')
        value = int(token)
        need(abs(value) <= 9007199254740991, 'SAFE_INTEGER')
        return value
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                       parse_int=integer, parse_float=lambda _: need(False, 'INTEGER_JSON_ONLY'),
                       parse_constant=lambda _: need(False, 'NONFINITE_JSON'))
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        need(depth <= 64 and count <= 100000, 'JSON_STRUCTURE_BOUND')
        if type(item) is str:
            need(not any(0xd800 <= ord(c) <= 0xdfff for c in item), 'UNICODE_SCALAR')
        elif type(item) is dict:
            pending.extend((v, depth + 1) for v in [*item.keys(), *item.values()])
        elif type(item) is list:
            pending.extend((v, depth + 1) for v in item)
    return value


def descriptor(path, live=lambda: None):
    live()
    path = Path(path)
    need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(),
         'CANONICAL_ORIGINAL_FILE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    size = 0
    with os.fdopen(fd, 'rb') as handle:
        before = os.fstat(handle.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size <= 536870912, 'BOUNDED_REGULAR_ORIGINAL')
        while block := handle.read(1048576):
            live()
            size += len(block)
            digest.update(block)
        after = os.fstat(handle.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(identity(before) == identity(after) and size == before.st_size, 'ORIGINAL_CHANGED_DURING_HASH')
    live()
    return dict(path=str(path), bytes=size, sha256=digest.hexdigest())


class Originals:
    def __init__(self, live):
        self.live = live
        self.pins = {}
        self.bytes = 0

    def remember(self, pin):
        closed(pin, ('path', 'bytes', 'sha256'))
        need(type(pin['path']) is str and type(pin['bytes']) is int
             and 0 <= pin['bytes'] <= 536870912 and type(pin['sha256']) is str
             and re.fullmatch('[0-9a-f]{64}', pin['sha256']), 'DESCRIPTOR_SHAPE')
        previous = self.pins.get(pin['path'])
        if previous is None:
            need(len(self.pins) < 2048 and self.bytes + pin['bytes'] <= 4294967296,
                 'ORIGINAL_INVENTORY_BOUND')
            need(descriptor(pin['path'], self.live) == pin, 'ORIGINAL_PIN_MISMATCH:' + pin['path'])
            self.pins[pin['path']] = dict(pin)
            self.bytes += pin['bytes']
        else:
            need(previous == pin, 'CONFLICTING_ORIGINAL_PIN')
        return pin

    def doc(self, pin):
        self.remember(pin)
        need(pin['bytes'] <= MAX_JSON, 'BOUNDED_DATA_DOCUMENT')
        raw = Path(pin['path']).read_bytes()
        need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
             'DOCUMENT_READ_PIN_MISMATCH')
        self.live()
        return strict(raw)

    def actual_descriptors(self, value):
        # Only caller-selected current authority/worker documents are traversed.
        # Never expand historical reports, schema placeholders or negative vectors.
        if type(value) is dict:
            if set(value) == {'path', 'bytes', 'sha256'}:
                self.remember(value)
            else:
                for item in value.values():
                    self.actual_descriptors(item)
        elif type(value) is list:
            for item in value:
                self.actual_descriptors(item)

    def recheck(self):
        for pin in self.pins.values():
            need(descriptor(pin['path'], self.live) == pin, 'ORIGINAL_SOURCE_OR_INPUT_DRIFT:' + pin['path'])


def preflight(args, originals):
    need(Path(__file__).resolve(strict=True) == HERE / 'monitor.py', 'FIXED_MONITOR_PATH')
    need(re.fullmatch('[0-9a-f]{64}', args.monitor_sha)
         and re.fullmatch('[0-9a-f]{64}', args.release_sha), 'TRUSTED_EXTERNAL_SHA_OPERANDS')
    own = descriptor(Path(__file__), originals.live)
    need(own['sha256'] == args.monitor_sha, 'EXTERNAL_MONITOR_SHA')
    originals.remember(own)
    need(sys.flags.isolated == 1 and sys.dont_write_bytecode is True
         and Path(sys.executable).resolve(strict=True) == Path(PINS['python']['path']),
         'FIXED_ISOLATED_OUTER_INTERPRETER')
    for pin in PINS.values():
        originals.remember(pin)
    config = originals.doc(PINS['config'])
    core = originals.doc(PINS['core'])
    worker = originals.doc(PINS['worker'])
    approval = originals.doc(PINS['configurationApproval'])
    workflow = originals.doc(PINS['workflow'])
    source = originals.doc(PINS['sourceClosure'])
    source_approval = originals.doc(PINS['sourceApproval'])
    controls = originals.doc(PINS['controlApproval'])
    need(len(source) == 449 and len({d['path'] for d in source}) == 449
         and equal(worker['sourceClosure'], source), 'EXACT_CURRENT449_SOURCE')
    for pin in source:
        originals.remember(pin)
    need(config['workerConfig'] == PINS['worker'] and config['sourceApproval'] == PINS['sourceApproval']
         and config['controlAcceptance'] == PINS['controlApproval']
         and config['configurationAcceptance'] == PINS['configurationApproval']
         and equal({k: v for k, v in config.items() if k != 'configurationAcceptance'}, core),
         'EXACT_FINAL_CONFIGURATION_AND_CORE')
    need(config['runId'] == worker['runId'] == '9df61b3f71ac'
         and config['runRole'] == worker['runRole'] == 'primary'
         and config['executionSession'] == worker['executionSession'] == '/root'
         and config['primaryAcceptance'] is None and worker['outputRoot'] == str(NATIVE_OUTPUT)
         and worker['environment'] == ENV, 'EXACT_PRIMARY_PROFILE')
    need(approval['schema'] == 'n02316-local-configuration-approval-v1'
         and approval['decision'] == 'ACCEPT_CONFIGURATION_ONLY'
         and equal(approval['configuration'], core) and approval['authors'] == EXPECTED_AUTHORS,
         'GENUINE_EXACT_CORE_APPROVAL')
    need(source_approval['decision'] == 'ACCEPT_SOURCE_ONLY'
         and equal(source_approval['sourceClosure'], source)
         and controls['decision'] == 'ACCEPT_CONTROLS_ONLY'
         and controls['sourceApproval'] == PINS['sourceApproval'], 'CURRENT_SOURCE_CONTROL_AUTHORITY')
    for pack, decision, subject_pin in ((source_approval, 'ACCEPT_SOURCE_ONLY', PINS['sourceClosure']),
                                        (controls, 'ACCEPT_CONTROLS_ONLY', controls['actualControlEvidence']),
                                        (approval, 'ACCEPT_CONFIGURATION_ONLY', PINS['core'])):
        need(len(pack['reviews']) == 2 and {r['role'] for r in pack['reviews']} == {'qa', 'security'},
             'TWO_REAL_APPROVAL_ROLES')
        for row in pack['reviews']:
            need(row['session'] == REVIEWERS[row['role']] and row['decision'] == decision
                 and row['subject'] == subject_pin and row['session'] not in pack['authors'],
                 'EXACT_NONAUTHOR_APPROVAL_JOIN')
            originals.remember(row['subject'])
    evidence = originals.doc(controls['actualControlEvidence'])
    need(evidence['sourceApproval'] == PINS['sourceApproval']
         and equal(evidence['sourceClosure'], source) and evidence['finalIntegrity'] is True,
         'ACTUAL_CURRENT_CONTROL_EVIDENCE_JOIN')
    for role, key in (('qa', 'configurationQa'), ('security', 'configurationSecurity')):
        report = originals.doc(PINS[key])
        need(report['role'] == role and report['reviewer'] == report['session'] == REVIEWERS[role]
             and report['decision'] == 'ACCEPT_CONFIGURATION_ONLY' and report['findings'] == []
             and report['subject'] == PINS['core'] and report['workerConfig'] == PINS['worker'],
             'ACTUAL_CONFIGURATION_REPORT_JOIN')
    need(workflow['configurationReviews'] == {'qa': PINS['configurationQa'], 'security': PINS['configurationSecurity']}
         and workflow['configurationApproval'] == PINS['configurationApproval']
         and workflow['finalConfiguration'] == PINS['config']
         and workflow['pairedInputMatrixAcceptance'] == PINS['pair'], 'ACTUAL_WORKFLOW_RECORD_JOIN')
    pair = originals.doc(PINS['pair'])
    need(pair['decision'] == 'ACCEPT_PRIMARY_QA_CALLER_MEMORY_MATRIX_PAIR_ONLY'
         and pair['casesPerRun'] == 76 and pair['actualQaOperator'] == '/root/android_health_qa',
         'QUALIFIED_INPUT_MATRIX_PAIR')
    for role, session in (('primary', '/root'), ('qa', '/root/android_health_qa')):
        observed = originals.doc(pair[role])
        need(observed['runRole'] == role and observed['executionSession'] == session
             and observed['qualified'] is True and observed['firstError'] is None
             and observed['secondaryErrors'] == [] and observed['actualRows'] == observed['expectedRows'] == 76
             and observed['allowedAdmissionImports'] == 1 and observed['nativeJobs'] == 0
             and observed['sourceApproval'] == PINS['sourceApproval']
             and observed['sourceClosure'] == PINS['sourceClosure']
             and observed['controlApproval'] == PINS['controlApproval']
             and len(observed['sideEffectAttempts']) == 8
             and all(type(v) is int and v == 0 for v in observed['sideEffectAttempts'].values())
             and len(observed['rows']) == 76, 'ACTUAL_COMPLETE_PAIRED_MATRIX')
        for row in observed['rows']:
            need(row['state'] == 'EXECUTED' and row['matched'] is True, 'ACTUAL_PAIRED_ROW_COMPLETENESS')
            originals.remember(row['observation'])
    originals.remember(pair['actualQaToolAssociation'])
    for role, pin in pair['independentNonoperatorReviews'].items():
        report = originals.doc(pin)
        need(report['role'] == role and report['reviewer'] == REVIEWERS[role]
             and report['decision'] == PAIR_DECISIONS[role] and report['findings'] == []
             and report['subject'] == pair['qa'], 'ACTUAL_NONOPERATOR_PAIR_REVIEW')
    # Hash actual direct descriptors only; no recursive historical graph expansion.
    for value in (worker, core, source_approval, controls, evidence, approval, workflow):
        originals.actual_descriptors(value)
    schema = originals.doc(PINS['qualificationSchema'])
    release_pin = descriptor(Path(args.release), originals.live)
    need(release_pin['sha256'] == args.release_sha, 'EXTERNAL_FRESH_LOCAL_RELEASE_SHA')
    release = originals.doc(release_pin)
    closed(release, schema['workerDefinitions']['localRelease']['record'])
    need(release == dict(schema='n02316-local-qualification-release-v1',
                        decision='RELEASE_EXACT_LOCAL_F_ONLY_RUN_ONLY', rootSession='/root',
                        executionSession='/root', runRole='primary', config=PINS['config'],
                        workerConfig=PINS['worker'], sourceApproval=PINS['sourceApproval'],
                        controlAcceptance=PINS['controlApproval'],
                        configurationAcceptance=PINS['configurationApproval']), 'EXACT_EXTERNAL_ROOT_LOCAL_GRANT')
    need(not os.path.lexists(OUTPUT) and not os.path.lexists(NATIVE_OUTPUT), 'FRESH_MONITOR_AND_NATIVE_OUTPUT')
    need(HERE.resolve(strict=True) == HERE and HERE.is_dir() and HERE.stat().st_uid == os.getuid(),
         'OWNED_EXECUTION_DIRECTORY')
    originals.recheck()
    argv = [PINS['python']['path'], '-I', '-B', PINS['qualification']['path'], PINS['config']['path'],
            PINS['config']['sha256'], release_pin['path'], release_pin['sha256'], '/root', 'primary']
    return own, release_pin, argv


def write_file(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return descriptor(path)


def run(args):
    started = time.monotonic()
    total_deadline = started + TOTAL_SECONDS
    active_deadline = total_deadline - CLEANUP_RESERVE_SECONDS
    interrupted = []
    def live():
        need(not interrupted, 'MONITOR_INTERRUPTED')
        need(time.monotonic() < active_deadline, 'MONITOR_ACTIVE_DEADLINE')
    originals = Originals(live)
    own, release_pin, argv = preflight(args, originals)
    OUTPUT.mkdir(mode=0o700)
    record = dict(schema='e06-local-fixed-outer-monitor-v1', actor='/root', argv=argv, cwd=str(ROOT),
                  environment=dict(ENV), stdin='DEVNULL_EMPTY_BYTES', monitor=own,
                  configuration=PINS['config'], release=release_pin, workflow=PINS['workflow'],
                  launchAttempted=False, acquisition='NOT_ACQUIRED', pid=None,
                  pidMeaning='PID in the tool execution namespace, not an asserted host PID',
                  exit=None, reaped=False, stdoutEOF=False, stderrEOF=False, forced=False,
                  timedOut=False, signals=[], firstError=None, secondaryErrors=[],
                  observedBytes={'stdout': 0, 'stderr': 0}, retainedBytes={'stdout': 0, 'stderr': 0},
                  caps=dict(CAPS), originalPinsCurrent=None, nativeOutputExists=False,
                  nativeExecution='UNKNOWN', candidateResult=None)
    streams = {}
    selector = None
    process = None
    exited = None
    old_handlers = {}
    def fault(error):
        fact = dict(type=type(error).__name__, message=str(error)[:4096])
        if record['firstError'] is None:
            record['firstError'] = fact
        elif len(record['secondaryErrors']) < 32:
            record['secondaryErrors'].append(fact)
    def observe_owned():
        need(process is not None and process.returncode is None, 'UNREAPED_OWNED_CHILD_REQUIRED')
        return os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    def pump(timeout):
        try:
            events = selector.select(timeout)
        except BaseException as error:
            fault(error)
            return
        for key, _ in events:
            name = key.data
            try:
                block = os.read(key.fd, 65536)
            except BlockingIOError:
                continue
            except BaseException as error:
                fault(error)
                continue
            if not block:
                record[name + 'EOF'] = True
                try:
                    selector.unregister(key.fileobj)
                except BaseException as error:
                    fault(error)
                try:
                    key.fileobj.close()
                except BaseException as error:
                    fault(error)
                continue
            record['observedBytes'][name] += len(block)
            keep = block[:max(0, CAPS[name] - record['retainedBytes'][name])]
            if keep:
                try:
                    written = streams[name].write(keep)
                    if type(written) is int and 0 <= written <= len(keep):
                        record['retainedBytes'][name] += written
                    need(written == len(keep), 'FULL_CAPTURE_FILE_WRITE')
                except BaseException as error:
                    # A storage failure may make capture unqualified, but must
                    # not prevent the independent owned cleanup stages.
                    fault(error)
            if len(keep) != len(block):
                fault(Refusal('OUTER_' + name.upper() + '_BOUND'))
    try:
        for name in ('stdout', 'stderr'):
            fd = os.open(OUTPUT / (name + '.bin'), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            streams[name] = os.fdopen(fd, 'wb')
        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, lambda value, frame: interrupted.append(value) if not interrupted else None)
        live()
        record['launchAttempted'] = True
        process = subprocess.Popen(argv, cwd=ROOT, env=ENV, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, bufsize=0)
        record.update(acquisition='ACQUIRED', pid=process.pid)
        selector = selectors.DefaultSelector()
        for name, pipe in (('stdout', process.stdout), ('stderr', process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, name)
        while True:
            live()
            exited = observe_owned()
            if exited is not None and record['stdoutEOF'] and record['stderrEOF']:
                break
            pump(min(0.1, max(0, active_deadline - time.monotonic())))
            if record['firstError'] is not None:
                break
    except BaseException as error:
        if isinstance(error, Refusal) and str(error) == 'MONITOR_ACTIVE_DEADLINE':
            record['timedOut'] = True
        fault(error)
    finally:
        # Keep the Popen child unreaped until every possible owned-group signal.
        if process is not None:
            try:
                exited = observe_owned()
                complete = exited is not None and record['stdoutEOF'] and record['stderrEOF']
                stages = [(signal.SIGINT, 20), (signal.SIGTERM, 5), (signal.SIGKILL, 5)]
                for signum, allowance in stages:
                    if complete:
                        break
                    observe_owned()  # ECHILD/ownership loss refuses before signalling.
                    try:
                        os.killpg(process.pid, signum)
                        record['signals'].append(signum)
                        record['forced'] = True
                    except ProcessLookupError:
                        pass
                    until = min(total_deadline, time.monotonic() + allowance)
                    while time.monotonic() < until:
                        if selector is not None:
                            pump(min(0.1, max(0, until - time.monotonic())))
                        exited = observe_owned()
                        complete = exited is not None and record['stdoutEOF'] and record['stderrEOF']
                        if complete:
                            break
                if exited is not None:
                    record['exit'] = process.wait(timeout=0)
                    record['reaped'] = True
                else:
                    fault(Refusal('OUTER_CHILD_NOT_REAPED_WITHIN_BOUND'))
            except BaseException as error:
                fault(error)
            # There is no signal path after the reap above.
            for pipe in (process.stdout, process.stderr):
                try:
                    if pipe is not None:
                        pipe.close()
                except BaseException as error:
                    fault(error)
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                fault(error)
        for name, handle in streams.items():
            try:
                handle.flush()
                os.fsync(handle.fileno())
            except BaseException as error:
                fault(error)
            finally:
                try:
                    handle.close()
                except BaseException as error:
                    fault(error)
        for signum, handler in old_handlers.items():
            try:
                signal.signal(signum, handler)
            except BaseException as error:
                fault(error)
    if process is not None and record['exit'] not in (None, 0) and record['firstError'] is None:
        fault(Refusal('QUALIFICATION_CHILD_NONZERO_EXIT'))
    record['captureComplete'] = (record['stdoutEOF'] and record['stderrEOF']
                                 and record['observedBytes'] == record['retainedBytes'])
    for name in ('stdout', 'stderr'):
        path = OUTPUT / (name + '.bin')
        try:
            record[name] = descriptor(path) if path.is_file() and not path.is_symlink() else None
        except BaseException as error:
            record[name] = None
            fault(error)
    record['nativeOutputExists'] = os.path.lexists(NATIVE_OUTPUT)
    if not record['launchAttempted'] or record['acquisition'] != 'ACQUIRED':
        record['nativeExecution'] = 'NOT_EXECUTED_NO_QUALIFICATION_CHILD'
    elif (record['reaped'] and not record['forced'] and record['exit'] not in (None, 0)
          and record['captureComplete'] and record['observedBytes']['stdout'] == 0
          and not record['nativeOutputExists']):
        record['nativeExecution'] = 'NOT_EXECUTED_SOURCE_PATH_SUPPORTED_PRE_NATIVE_FAILURE'
    elif record['nativeOutputExists']:
        record['nativeExecution'] = 'LOCAL_OUTPUT_PRESENT_REQUIRES_INDEPENDENT_GRAPH_REVIEW'
    else:
        record['nativeExecution'] = 'UNKNOWN_UNQUALIFIED'
    if record['captureComplete'] and record['observedBytes']['stdout'] > 0:
        try:
            raw = (OUTPUT / 'stdout.bin').read_bytes()
            need(raw.endswith(b'\n') and raw.count(b'\n') == 1, 'ONE_LOCAL_RESULT_JSONL')
            candidate = strict(raw[:-1])
            need(type(candidate) is dict and candidate.get('schema') == 'n02316-local-run-capture-v1'
                 and candidate.get('runId') == '9df61b3f71ac'
                 and candidate.get('runRole') == 'primary' and candidate.get('executionSession') == '/root'
                 and candidate.get('config') == PINS['config'] and candidate.get('release') == release_pin,
                 'LOCAL_RESULT_CONTEXT')
            if record['exit'] == 0:
                need(candidate.get('status') == 'MATCHED', 'NATURAL_ZERO_WITHOUT_DECLARED_MATCHED_RESULT')
            record['candidateResult'] = {key: candidate.get(key) for key in
                ('schema', 'status', 'counts', 'error', 'secondaryErrors', 'notExecuted')}
        except BaseException as error:
            fault(error)
    elif record['exit'] == 0:
        fault(Refusal('NATURAL_ZERO_WITHOUT_COMPLETE_LOCAL_REPLY'))
    try:
        originals.recheck()
        record['originalPinsCurrent'] = True
    except BaseException as error:
        record['originalPinsCurrent'] = False
        fault(error)
    record['verifiedOriginalInputs'] = list(originals.pins.values())
    record['receivedInterruptSignals'] = list(interrupted)
    record['elapsedMilliseconds'] = int((time.monotonic() - started) * 1000)
    record['externalCeilingSeconds'] = TOTAL_SECONDS
    record['cleanupReserveSeconds'] = CLEANUP_RESERVE_SECONDS
    record['monitorExit'] = 0 if (record['exit'] == 0 and record['reaped'] and record['captureComplete']
        and not record['forced'] and record['firstError'] is None and record['secondaryErrors'] == []
        and record['originalPinsCurrent'] is True) else 2
    record['limits'] = ['Actual outer lifecycle/capture only; candidate LOCAL result remains unreviewed.',
        'Pre-native NOT_EXECUTED classification combines known unchanged source order and actual empty/output-absence facts.',
        'Forced or uncertain cleanup does not attest absence of escaped/separate-session descendants.',
        'No hard realtime, hostile-host or OS containment; no canonical E06 PASS or blocker closure.']
    try:
        execution = write_file(OUTPUT / 'execution.json', (json.dumps(record, indent=2) + '\n').encode())
    except BaseException as error:
        fault(error)
        fallback = dict(schema='e06-local-outer-record-write-failure-v1', firstError=record['firstError'],
                        secondaryErrors=record['secondaryErrors'], childExit=record['exit'],
                        reaped=record['reaped'], forced=record['forced'],
                        nativeExecution=record['nativeExecution'])
        os.write(2, (json.dumps(fallback)[:16384] + '\n').encode('utf-8', 'backslashreplace'))
        return 2
    print(json.dumps(dict(execution=execution, monitorExit=record['monitorExit'], childExit=record['exit'],
                          nativeExecution=record['nativeExecution'], independentResultReviewRequired=True)))
    return record['monitorExit']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--monitor-sha', required=True)
    parser.add_argument('--release', required=True)
    parser.add_argument('--release-sha', required=True)
    return run(parser.parse_args())


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BaseException as error:
        if isinstance(error, SystemExit):
            raise
        # Failed DATA admission occurs before child creation and is not a LOCAL
        # gate observation. The external workflow must retain this actual reply.
        os.write(2, ('MONITOR_PREFLIGHT_OR_CAPTURE_FAILURE: ' + type(error).__name__ + ': '
                     + str(error))[:16384].encode('utf-8', 'backslashreplace') + b'\n')
        sys.exit(2)
