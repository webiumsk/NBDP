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
S = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v1'
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
ACTOR = '/root/ordinary_api35_source'
TIMEOUT_SECONDS = 60
CAPTURE_LIMIT_BYTES = 1024 * 1024
SUBJECT_SHA = '296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4'
FROZEN_PLAN_SHA = 'dce8eab9bd5436a933d9661b74fb30b1b7dceff64339a22168f378a3d0a2bee2'
SCOPES = [
    ('cleanup', 29, [str(PYTHON), '-I', '-B', str(S / 'test_cleanup.py')]),
    ('ui-regression', 49, [str(PYTHON), '-I', '-B', str(S / 'test_android_driver.py')]),
    ('minimum-ui', 21, [str(PYTHON), '-I', '-B', str(S / 'test_minimum_driver.py')]),
    ('fixture-regression', 27, [str(NODE), str(S / 'test_fixture.mjs')]),
    ('minimum-fixture', 43, [str(NODE), str(S / 'test_minimum_fixture.mjs')]),
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


def descriptor_closure(value, out=None):
    if out is None:
        out = {}
    if type(value) is dict:
        if set(value) == {'path', 'bytes', 'sha256'}:
            prior = out.get(value['path'])
            assert prior is None or prior == value, 'Conflicting frozen descriptor'
            out[value['path']] = value
        else:
            for item in value.values():
                descriptor_closure(item, out)
    elif type(value) is list:
        for item in value:
            descriptor_closure(item, out)
    return out


def snapshot():
    subject = json.loads((E / 'subject.json').read_text())
    descriptor = pin(E / 'subject.json')
    assert descriptor['sha256'] == SUBJECT_SHA
    closure = descriptor_closure(subject)
    assert len(closure) == 112, 'Whole original frozen subject closure required'
    actual = [pin(Path(path)) for path in sorted(closure)]
    assert all(row == closure[row['path']] for row in actual), 'Frozen SOURCE/DATA changed'
    frozen_plan_pin = pin(E / 'execution-control-plan.json')
    assert frozen_plan_pin['sha256'] == FROZEN_PLAN_SHA
    frozen_plan = json.loads((E / 'execution-control-plan.json').read_text())
    assert [(r['name'], r['plannedChecks'], r['argv']) for r in frozen_plan['separateScopes']] == SCOPES
    assert all(r['timeoutSeconds'] == TIMEOUT_SECONDS for r in frozen_plan['separateScopes'])
    interpreters = {k: pin(Path(d['path'])) for k, d in frozen_plan['interpreters'].items()}
    assert interpreters == frozen_plan['interpreters']
    data = json.loads((E / 'control-inputs.json').read_text())
    inputs = data['oldTenArchivedUiData'] + data['newFrozenFeedsData']
    assert len(inputs) == 14 and all(pin(Path(d['path'])) == d for d in inputs)
    acknowledgement = json.loads((HERE / 'coordinator-acknowledgement.json').read_text())
    assert acknowledgement['sourceSubjectSha256'] == SUBJECT_SHA
    assert acknowledgement['actor'] == '/root' and acknowledgement['pureControlsAuthorized'] is True
    assert acknowledgement['actualSourceQaAccepted'] is True and acknowledgement['actualSourceSecurityAccepted'] is True
    assert acknowledgement['runner'] == pin(Path(__file__).resolve())
    assert acknowledgement['controlPlan'] == pin(HERE / 'control-plan.json')
    review_pins = [acknowledgement['sourceQaReview'], acknowledgement['sourceSecurityReview']]
    assert all(pin(Path(d['path'])) == d for d in review_pins)
    return {'subject': descriptor, 'all112FrozenDescriptors': actual,
            'configurations': subject['configurations'], 'interpreters': interpreters,
            'archivedReadOnlyControlData': inputs,
            'captureRunner': pin(Path(__file__).resolve()),
            'controlPlan': pin(HERE / 'control-plan.json'), 'frozenControlPlan': frozen_plan_pin,
            'sourceReviewRecords': review_pins,
            'coordinatorAcknowledgement': pin(HERE / 'coordinator-acknowledgement.json')}


def output_shape(name, expected, stdout, stderr):
    if name in ('cleanup', 'ui-regression', 'minimum-ui'):
        match = re.search(rb'\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n\Z', stderr)
        count = int(match[1]) if match else None
        return count, count == expected and stdout == b''
    assert stderr == b'', 'Pure Node controls require empty stderr'
    assert stdout.endswith(b'\n') and stdout.count(b'\n') == 1, 'One actual JSON output line required'
    def pairs(items):
        out = {}
        for key, value in items:
            assert key not in out, 'Duplicate output JSON key'
            out[key] = value
        return out
    value = json.loads(stdout, object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite output')))
    assert type(value) is dict and type(value['checks']) is int
    if name == 'fixture-regression':
        assert set(value) == {'scope','checks','installedCryptoAPIEvaluated','clientControlExecuted','E02Promotion'}
        assert value['scope'] == 'PURE_FILTER_GENERATION_AND_SOURCE_SHAPE_CONTROLS_ONLY'
        assert all(value[k] is False for k in ('installedCryptoAPIEvaluated','clientControlExecuted','E02Promotion'))
    else:
        assert name == 'minimum-fixture'
        assert set(value) == {'scope','checks','cases','cryptoExecuted','actualClientExecuted','canonicalPromotion'}
        assert value['scope'] == 'MINIMUM_ROLE_REPLAY_ORIGIN_METADATA_CONTROLS_ONLY'
        assert all(value[k] is False for k in ('cryptoExecuted','actualClientExecuted','canonicalPromotion'))
        cases = value['cases']
        assert type(cases) is list and len(cases) == expected
        assert all(type(s) is str and 1 <= len(s) <= 160 for s in cases) and len(set(cases)) == len(cases)
    return value['checks'], value['checks'] == expected


def one(name, expected, argv):
    before = snapshot()
    save(name + '-sources-before.json', before)
    receipt = {'schema': 'e02-minimum-pure-scope-execution-v1', 'scope': name,
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
        observed, count_ok = output_shape(name, expected, stdout, stderr)
        receipt['observedCount'] = observed
        receipt['countAndOutputShapeMatched'] = count_ok
        receipt['controlResultAcceptedByAuthor'] = bool(count_ok and receipt['exitCode'] == 0
            and receipt['signal'] is None and receipt['naturalExit'] and receipt['reaped']
            and receipt['stdoutEof'] and receipt['stderrEof'] and not receipt['error']
            and not receipt['stdoutTruncated'] and not receipt['stderrTruncated']
            and not receipt['forceRequested'] and receipt['sourcesUnchanged'])
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
         'scope': 'FIVE_CHANGED_PURE_CONTROLS_ONLY_NO_ANDROID_OR_SERVICES'})
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
    save('execution.json', {'schema': 'e02-minimum-current-pure-controls-execution-v1',
        'actor': ACTOR, 'session': ACTOR, 'state': 'WRITES_STOPPED',
        'result': 'ALL_FIVE_CHANGED_SEPARATE_PURE_SCOPES_COMPLETED' if complete else 'STOPPED_AT_FIRST_FAILURE',
        'scopes': results, 'remainingScopesNotExecuted': [name for name, _, _ in SCOPES[len(results):]],
        'subject': pin(E / 'subject.json'), 'configurations': [pin(E / ('proposed-' + role + '-run-config.json')) for role in ('incoming','archive')],
        'runner': pin(Path(__file__).resolve()), 'coordinatorAcknowledgement': pin(HERE / 'coordinator-acknowledgement.json'),
        'newIndependentResultReviews': 'PENDING_ACTUAL_OTHER_AGENTS',
        'noRetry': True, 'androidServicesSdkInstallsLeasesGrantsReleases': 0,
        'unchangedScopesNotReexecuted': {'guard': 29},
        'unchangedScopeLink': pin(E / 'unchanged-guard-scope-link.json'),
        'canonicalPromotionOrBlockerChange': False,
        'meaning': 'Each scope has its own evidence/count. Synthetic DATA/pure controls do not establish ordinary-client runtime acceptance.'})
    save('artifact-manifest.json', {'schema': 'e02-minimum-current-controls-artifact-manifest-v1',
        'artifacts': [pin(path) for path in sorted(HERE.rglob('*')) if path.is_file()],
        'limits': 'No self hash; no independent review or Android/experiment PASS.'})
    print(json.dumps({'state': 'WRITES_STOPPED', 'completeFiveChangedPureScopes': complete,
                      'execution': pin(HERE / 'execution.json'), 'scopes': results}))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
