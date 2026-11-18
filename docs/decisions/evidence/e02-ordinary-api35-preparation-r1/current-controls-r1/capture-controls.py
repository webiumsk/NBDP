"""Finite once-only five-scope control capture; no Android/service activation."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = Path(__file__).resolve().parent
E = HERE.parent
S = ROOT / 'experiments/prototypes/e02_ordinary_client_api35_v1'
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
ACTOR = '/root/ordinary_api35_source'
TIMEOUT_SECONDS = 90
CAPTURE_LIMIT_BYTES = 1024 * 1024
SUBJECT_SHA = 'ff877c4c7cbb59551e9a8bf0d13c837c285b3429812516b39091ece9c406d3c7'
CONFIG_SHA = '4756736d5214b23f1b56ca063e124b0924e13d9fdd41656cf69c0eb7de6344b4'
PYTHON_SHA = '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'
NODE_SHA = 'ccacb2d6d87ba6d118b2bffc1ae33747a05cc5fc6b1f1ec4fc1d420b687e952d'
SCOPES = [
    ('guard', 29, [str(PYTHON), '-I', '-B', str(S / 'test_lease_guard.py')]),
    ('cleanup', 24, [str(PYTHON), '-I', '-B', str(S / 'test_cleanup.py')]),
    ('ui', 38, [str(PYTHON), '-I', '-B', str(S / 'test_android_driver.py')]),
    ('fixture', 27, [str(NODE), str(S / 'test_fixture.mjs')]),
    ('consumer', 14, [str(PYTHON), '-I', '-B', str(ROOT / 'experiments/prototypes/e02_ordinary_control_evidence_v1/test_consumer.py')]),
]
STATIC_INPUTS = [
    ROOT / 'docs/decisions/evidence/e02-ordinary-client-resume-r1/ui-source-r1-before-tor-modal-fix/ui/ui-005-tor-off-selected.xml',
    ROOT / 'docs/decisions/evidence/e02-ordinary-client-resume-r1/ui-source-r1-before-tor-modal-fix/ui/ui-001-login-start.xml',
    ROOT / 'docs/decisions/evidence/e02-ordinary-client-resume-r1/ui-source-r2-before-os-anr-handler/ui/ui-007-login-settle.xml',
    ROOT / 'docs/decisions/evidence/e02-ordinary-client-resume-r1/ui-source-r4-before-visible-identity-fix/ui/ui-010-whole-disposable-identity.xml',
    ROOT / 'docs/decisions/evidence/e02-ordinary-client-resume-r1/source-r6-before-loopback-listener-fix/listeners.txt',
]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, value):
    fd = os.open(HERE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def snapshot():
    subject = json.loads((E / 'subject.json').read_text())
    descriptor = pin(E / 'subject.json')
    assert descriptor['sha256'] == SUBJECT_SHA
    sources = [pin(Path(row['path'])) for row in subject['sources']]
    assert len(sources) == 21 and sources == subject['sources']
    config = pin(E / 'proposed-run-config.json')
    assert config == subject['configuration'] and config['sha256'] == CONFIG_SHA
    python, node = pin(PYTHON), pin(NODE)
    assert python['sha256'] == PYTHON_SHA and node['sha256'] == NODE_SHA
    return {'subject': descriptor, 'sources': sources, 'configuration': config,
            'interpreters': {'python': python, 'node': node},
            'archivedReadOnlyControlData': [pin(path) for path in STATIC_INPUTS],
            'captureRunner': pin(Path(__file__).resolve()),
            'controlPlan': pin(HERE / 'control-plan.json'),
            'coordinatorAcknowledgement': pin(HERE / 'coordinator-acknowledgement.json')}


def one(name, expected, argv):
    before = snapshot()
    save(name + '-sources-before.json', before)
    receipt = {'schema': 'e02-ordinary-api35-pure-scope-execution-v1', 'scope': name,
               'actor': ACTOR, 'session': ACTOR, 'parentCoordinator': '/root',
               'argv': argv, 'cwd': str(ROOT), 'expectedSeparateCount': expected,
               'startedUtc': utc(), 'timeoutSeconds': TIMEOUT_SECONDS,
               'captureLimitPerStreamBytes': CAPTURE_LIMIT_BYTES,
               'forceRequested': False, 'forceReason': None, 'error': None,
               'exitCode': None, 'signal': None, 'reaped': False,
               'naturalExit': False, 'stdoutEof': False, 'stderrEof': False,
               'stdoutTruncated': False, 'stderrTruncated': False,
               'observedCount': None, 'sourcesUnchanged': False,
               'controlResultAcceptedByAuthor': False,
               'meaning': 'Pure control execution only; no Android, service, actual ordinary-client observation or canonical promotion.'}
    started = time.monotonic_ns()
    child = None
    raw_streams = {'stdout': b'', 'stderr': b''}
    try:
        env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TMPDIR': str(HERE / 'tmp')}
        receipt['environment'] = env
        child = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=True, close_fds=True)
        receipt['pid'] = child.pid
        try:
            out, err = child.communicate(timeout=TIMEOUT_SECONDS)
            receipt['naturalExit'] = True
        except subprocess.TimeoutExpired:
            receipt['forceRequested'] = True
            receipt['forceReason'] = 'Finite child deadline exceeded'
            os.killpg(child.pid, signal.SIGKILL)
            out, err = child.communicate(timeout=3)
        raw_streams = {'stdout': out, 'stderr': err}
        receipt['reaped'] = child.returncode is not None
        receipt['exitCode'] = child.returncode if child.returncode >= 0 else None
        receipt['signal'] = -child.returncode if child.returncode < 0 else None
        receipt['stdoutEof'] = receipt['stderrEof'] = True
    except BaseException as error:
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        if child is not None and child.poll() is None:
            receipt['forceRequested'] = True
            receipt['forceReason'] = 'Capture exception'
            try:
                os.killpg(child.pid, signal.SIGKILL)
                out, err = child.communicate(timeout=3)
                raw_streams = {'stdout': out, 'stderr': err}
                receipt['reaped'] = child.returncode is not None
                receipt['stdoutEof'] = receipt['stderrEof'] = True
            except BaseException as cleanup_error:
                receipt['cleanupError'] = type(cleanup_error).__name__ + ': ' + str(cleanup_error)
    finally:
        for stream_name, raw in raw_streams.items():
            fd = os.open(HERE / (name + '.' + stream_name), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as output:
                output.write(raw[:CAPTURE_LIMIT_BYTES])
            receipt[stream_name + 'Truncated'] = len(raw) > CAPTURE_LIMIT_BYTES
        receipt['finishedUtc'] = utc()
        receipt['elapsedNanoseconds'] = time.monotonic_ns() - started
        receipt['observedStreamBytes'] = {name: len(raw) for name, raw in raw_streams.items()}
    try:
        after = snapshot()
        save(name + '-sources-after.json', after)
        receipt['sourcesUnchanged'] = before == after
        stdout = (HERE / (name + '.stdout')).read_bytes()
        stderr = (HERE / (name + '.stderr')).read_bytes()
        if name == 'fixture':
            parsed = json.loads(stdout)
            receipt['observedCount'] = parsed.get('checks')
            count_ok = (parsed == {'scope': 'PURE_FILTER_GENERATION_AND_SOURCE_SHAPE_CONTROLS_ONLY',
                'checks': expected, 'installedCryptoAPIEvaluated': False,
                'clientControlExecuted': False, 'E02Promotion': False} and not stderr)
        else:
            match = re.search(rb'\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n\Z', stderr)
            receipt['observedCount'] = int(match[1]) if match else None
            count_ok = receipt['observedCount'] == expected
        receipt['countAndOutputShapeMatched'] = count_ok
        receipt['controlResultAcceptedByAuthor'] = bool(count_ok and receipt['exitCode'] == 0
            and receipt['signal'] is None and receipt['naturalExit'] and receipt['reaped']
            and receipt['stdoutEof'] and receipt['stderrEof'] and not receipt['error']
            and not receipt['stdoutTruncated'] and not receipt['stderrTruncated']
            and receipt['sourcesUnchanged'])
    except BaseException as error:
        receipt['postCaptureError'] = type(error).__name__ + ': ' + str(error)
    for stream_name in raw_streams:
        path = HERE / (name + '.' + stream_name)
        if path.exists():
            receipt[stream_name] = pin(path)
    save(name + '-execution.json', receipt)
    return receipt


def main():
    assert sys.argv == [str(Path(__file__).resolve()), '--execute-once'], 'Explicit once-only control invocation required'
    os.umask(0o077)
    # Exclusive started record prevents any retry over successful or failed evidence.
    save('started.json', {'actor': ACTOR, 'session': ACTOR, 'utc': utc(), 'pid': os.getpid(),
         'scope': 'FIVE_PURE_CONTROLS_ONLY_NO_ANDROID_OR_SERVICES'})
    ack = json.loads((HERE / 'coordinator-acknowledgement.json').read_text())
    assert ack['sourceSubjectSha256'] == SUBJECT_SHA and ack['pureControlsAuthorized'] is True
    assert ack['qaAck'] == 'ACK_ORDINARY_API35_RESOURCE_DOCUMENTATION_CORRECTION'
    assert ack['securityAck'] == 'ACK_ORDINARY_API35_DOC_DATA_CORRECTION_ONLY'
    (HERE / 'tmp').mkdir(mode=0o700)
    save('sources-before.json', snapshot())
    results = []
    for name, expected, argv in SCOPES:
        result = one(name, expected, argv)
        results.append({'scope': name, 'expected': expected, 'observed': result['observedCount'],
                        'matched': result['controlResultAcceptedByAuthor'],
                        'receipt': pin(HERE / (name + '-execution.json'))})
        if not result['controlResultAcceptedByAuthor']:
            break
    save('sources-after.json', snapshot())
    complete = len(results) == 5 and all(row['matched'] for row in results)
    save('execution.json', {'schema': 'e02-ordinary-api35-current-pure-controls-execution-v1',
        'actor': ACTOR, 'session': ACTOR, 'state': 'WRITES_STOPPED',
        'result': 'ALL_FIVE_SEPARATE_PURE_SCOPES_COMPLETED' if complete else 'STOPPED_AT_FIRST_FAILURE',
        'scopes': results, 'remainingScopesNotExecuted': [name for name, _, _ in SCOPES[len(results):]],
        'subject': pin(E / 'subject.json'), 'configuration': pin(E / 'proposed-run-config.json'),
        'runner': pin(Path(__file__).resolve()), 'coordinatorAcknowledgement': pin(HERE / 'coordinator-acknowledgement.json'),
        'newIndependentResultReviews': 'PENDING_ACTUAL_OTHER_AGENTS',
        'noRetry': True, 'androidServicesSdkInstallsLeasesGrantsReleases': 0,
        'canonicalPromotionOrBlockerChange': False,
        'meaning': 'Each scope has its own evidence/count. Synthetic DATA/pure controls do not establish ordinary-client runtime acceptance.'})
    save('artifact-manifest.json', {'schema': 'e02-ordinary-api35-current-controls-artifact-manifest-v1',
        'artifacts': [pin(path) for path in sorted(HERE.rglob('*')) if path.is_file()],
        'limits': 'No self hash; no independent review or Android/experiment PASS.'})
    print(json.dumps({'state': 'WRITES_STOPPED', 'completeFivePureScopes': complete,
                      'execution': pin(HERE / 'execution.json'), 'scopes': results}))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
