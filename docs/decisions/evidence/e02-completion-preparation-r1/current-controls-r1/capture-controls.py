"""Fixed once-only54 synthetic DATA capture. Requires a fresh external root ack.

Popen.communicate retains output in memory until completion. Byte limits below
are post-capture file retention/refusal limits, NOT streaming memory/resource
caps. This finite trusted Python suite creates no child services or descendants.
Only its exact owned direct Popen child may be killed on a capture failure.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = Path(__file__).resolve().parent
PREP = HERE.parent
SOURCE = ROOT / 'experiments/prototypes/e02_completion_v1'
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
ACTOR = '/root/ordinary_api35_source'
SOURCE_SHA = 'b5b230d20f3ff571f6282ee3d529308f75127e9536e13bcf6a38b3b2981afd99'
MANIFEST_SHA = '1abe95a30971e8cef59726a54e1062c32da667539ec41930a327a61acfac1624'
FROZEN_PLAN_SHA = 'df9bc4705affa71551b3ac9ad8066e9ae904e619c702d4184b04c32aabfbf7ca'
ARGV = [str(NODE), str(SOURCE / 'test_data.mjs')]
LIMITS = {'stdout':1048576,'stderr':262144}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pin(path):
    assert path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'Canonical regular source path required'
    with path.open('rb') as stream:
        a = os.fstat(stream.fileno())
        assert stat.S_ISREG(a.st_mode) and 0 <= a.st_size <= 268435456, 'Bounded regular SOURCE/DATA only'
        raw = stream.read(268435457)
        b = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    assert identity(a) == identity(b) and len(raw) == a.st_size, 'Input identity drift'
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def strict(raw):
    assert len(raw) <= 16777216, 'Metadata bound'
    def pairs(items):
        value = {}
        for key, item in items:
            assert key not in value, 'Duplicate metadata key'
            value[key] = item
        return value
    def invalid(_):
        raise ValueError('Nonfinite metadata')
    return json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=invalid)


def doc(path):
    pin(path)
    return strict(path.read_bytes())


def save(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    fd = os.open(HERE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def snapshot(ack_sha):
    subject = pin(PREP / 'subject.json')
    assert subject['sha256'] == SOURCE_SHA, 'Exact completion source required'
    manifest = pin(PREP / 'artifact-manifest.json')
    assert manifest['sha256'] == MANIFEST_SHA
    frozen_plan = pin(PREP / 'control-plan.json')
    assert frozen_plan['sha256'] == FROZEN_PLAN_SHA
    proposed = doc(PREP / 'control-plan.json')
    assert proposed['argv'] == ARGV and proposed['plannedChecks'] == 54
    assert proposed['timeoutSeconds'] == 60 and proposed['rawRetentionBytes'] == LIMITS
    control_plan = doc(HERE / 'control-plan.json')
    assert control_plan['argv'] == ARGV and control_plan['plannedChecks'] == 54
    assert control_plan['timeoutSeconds'] == 60 and control_plan['retentionBytes'] == LIMITS
    profile = doc(SOURCE / 'profile.json')
    assert len(profile['dependencies']) == 816
    protected = doc(PREP / 'protected-inputs-after.json')
    assert len(protected['files']) == 51
    assert doc(PREP / 'protected-inputs-before.json') == protected
    frozen_inputs = doc(HERE / 'frozen-inputs.json')
    assert frozen_inputs['schema'] == 'e02-completion-control-frozen-inputs-v1'
    rows = frozen_inputs['files']
    assert 1 <= len(rows) <= 4096 and len({row['path'] for row in rows}) == len(rows)
    actual = [pin(Path(row['path'])) for row in rows]
    assert actual == rows, 'Full frozen input closure changed'
    by_path = {row['path']:row for row in rows}
    for expected in [*proposed['sourceInputs'],*profile['dependencies'],*protected['files']]:
        assert by_path[expected['path']] == expected, 'Required source/dependency/protected input omitted'
    interpreters = {'node':pin(NODE),'python':pin(PYTHON)}
    assert interpreters == {'node':profile['node'],'python':profile['python']}
    assert interpreters['node'] == proposed['node']
    ack_path = HERE / 'coordinator-acknowledgement.json'
    ack_pin = pin(ack_path)
    assert ack_pin['sha256'] == ack_sha and (ack_path.stat().st_mode & 0o777) == 0o600
    ack = doc(ack_path)
    assert set(ack) == {'schema','actor','sourceSubject','runnerSubject','runner','controlPlan',
        'sourceQaReview','sourceSecurityReview','sourceQaDecision','sourceSecurityDecision',
        'pureControlsAuthorized','allowedCount','stopFirstFailure','noRetry','primaryAuthorized',
        'consumerAuthorized','androidAuthorized','servicesAuthorized','cryptoOrNativeAuthorized','sdkAuthorized'}
    assert ack['schema'] == 'e02-completion-controls-root-ack-v1' and ack['actor'] == '/root'
    assert ack['sourceSubject'] == subject and ack['allowedCount'] == 54
    for key in ('pureControlsAuthorized','stopFirstFailure','noRetry'):
        assert ack[key] is True
    for key in ('primaryAuthorized','consumerAuthorized','androidAuthorized','servicesAuthorized','cryptoOrNativeAuthorized','sdkAuthorized'):
        assert ack[key] is False
    assert ack['runner'] == pin(Path(__file__).resolve()) and ack['controlPlan'] == pin(HERE / 'control-plan.json')
    assert ack['runnerSubject'] == pin(HERE / 'runner-subject.json')
    runner_subject = doc(HERE / 'runner-subject.json')
    assert runner_subject['runner'] == ack['runner'] and runner_subject['controlPlan'] == ack['controlPlan']
    for row in runner_subject['preparationArtifacts']:
        assert pin(Path(row['path'])) == row
    sessions, review_pins = [], []
    for field, decision_field, role in (('sourceQaReview','sourceQaDecision','qa'),('sourceSecurityReview','sourceSecurityDecision','security')):
        review_pin = ack[field]
        assert Path(review_pin['path']).parent == PREP and pin(Path(review_pin['path'])) == review_pin
        review = doc(Path(review_pin['path']))
        assert set(review) == {'role','session','decision','subject'}, 'Actual closed4 SOURCE record only'
        assert review['subject'] == subject and review['role'] == role
        assert type(ack[decision_field]) is str and review['decision'] == ack[decision_field]
        # The root binds the actual accepted scoped decision after both genuine
        # independent sessions return; this checker never interprets a future result.
        assert review['session'] not in (ACTOR,'/root','/root/android_health_implementer')
        assert type(review['session']) is str and review['session'].startswith('/root/')
        sessions.append(review['session']);review_pins.append(review_pin)
    assert len(set(sessions)) == 2
    return dict(sourceSubject=subject, sourceManifest=manifest, frozenSourcePlan=frozen_plan,
        fullFrozenInputs=actual, interpreters=interpreters, monitor=pin(Path(__file__).resolve()),
        runnerSubject=ack['runnerSubject'],controlPlan=ack['controlPlan'],
        sourceReviewRecords=review_pins,coordinatorAcknowledgement=ack_pin,
        frozenInputManifest=pin(HERE / 'frozen-inputs.json'))


def main():
    assert len(sys.argv) == 4 and sys.argv[1:3] == ['--execute-once', '--root-ack-sha'], 'Fixed single control invocation required'
    ack_sha = sys.argv[3]
    assert re.fullmatch('[0-9a-f]{64}', ack_sha), 'External acknowledgement hash required'
    os.umask(0o077)
    save('started.json', dict(actor=ACTOR, utc=utc(), pid=os.getpid(),
         scope='ONCE_54_SYNTHETIC_DATA_ONLY_NO_PRIMARY_CONSUMER_ANDROID_SDK_SERVICES_CRYPTO'))
    before = after = None
    child = None
    raw = {'stdout': b'', 'stderr': b''}
    receipt = dict(schema='e02-completion-pure-control-execution-v1', actor=ACTOR,
        parentCoordinator='/root', argv=ARGV, cwd=str(ROOT), expectedCount=54, startedUtc=utc(),
        timeoutSeconds=60, retentionBytes=LIMITS, retentionMeaning='POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP',
        pid=None, exitCode=None, signal=None, reaped=False, naturalExit=False, stdoutEOF=False, stderrEOF=False,
        forceRequested=False, forceReason=None, firstError=None, secondaryErrors=[], sourceUnchanged=False,
        observedCount=None, countAndOutputShapeMatched=False, captureMatched=False,
        controlResultAcceptedByAuthor=False, independentResultReview='PENDING_ACTUAL_OTHER_AGENTS')
    start = time.monotonic_ns()
    def error(label, exc):
        value = label + ':' + type(exc).__name__ + ':' + str(exc)[:2048]
        if receipt['firstError'] is None: receipt['firstError'] = value
        else: receipt['secondaryErrors'].append(value)
    try:
        before = snapshot(ack_sha)
        save('sources-before.json', before)
        (HERE / 'tmp').mkdir(mode=0o700)
        env = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(HERE / 'tmp')}
        receipt['environment'] = env
        child = subprocess.Popen(ARGV, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        receipt['pid'] = child.pid
        try:
            out, err = child.communicate(timeout=60)
            raw = {'stdout':out, 'stderr':err}
            receipt['naturalExit'] = True
            receipt['stdoutEOF'] = receipt['stderrEOF'] = True
        except subprocess.TimeoutExpired as exc:
            raw = {'stdout':exc.output or b'', 'stderr':exc.stderr or b''}
            error('original-deadline', exc)
            receipt['forceRequested'] = True; receipt['forceReason'] = 'Exact owned child deadline exceeded'
            child.kill()
            out, err = child.communicate(timeout=3)
            raw = {'stdout':out, 'stderr':err}
            receipt['stdoutEOF'] = receipt['stderrEOF'] = True
        receipt['reaped'] = child.returncode is not None
        if child.returncode is not None:
            receipt['exitCode'] = child.returncode if child.returncode >= 0 else None
            receipt['signal'] = -child.returncode if child.returncode < 0 else None
            if child.returncode != 0:
                error('original-child-exit', RuntimeError(str(child.returncode)))
    except BaseException as exc:
        error('capture', exc)
        if child is not None and child.poll() is None:
            receipt['forceRequested'] = True; receipt['forceReason'] = receipt['forceReason'] or 'Capture exception'
            try:
                child.kill()
                out, err = child.communicate(timeout=3)
                raw = {'stdout':out, 'stderr':err}
                receipt['stdoutEOF'] = receipt['stderrEOF'] = True
                receipt['reaped'] = child.returncode is not None
                if child.returncode is not None:
                    receipt['exitCode'] = child.returncode if child.returncode >= 0 else None
                    receipt['signal'] = -child.returncode if child.returncode < 0 else None
            except BaseException as cleanup_error:
                error('exact-owned-cleanup', cleanup_error)
    finally:
        receipt['finishedUtc'] = utc(); receipt['elapsedNanoseconds'] = time.monotonic_ns() - start
        receipt['observedStreamBytes'] = {name:len(data) for name,data in raw.items()}
        receipt['truncated'] = {name:len(data) > LIMITS[name] for name,data in raw.items()}
        for name, truncated in receipt['truncated'].items():
            if truncated:
                error('post-capture-retention-overflow-' + name, ValueError(str(len(raw[name]))))
        for name,data in raw.items():
            try:
                fd = os.open(HERE / ('data.' + name), os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd,'wb') as stream:
                    stream.write(data[:LIMITS[name]]); stream.flush(); os.fsync(stream.fileno())
                receipt[name] = pin(HERE / ('data.' + name))
            except BaseException as retain_error:
                error('raw-retention-' + name, retain_error)
    try:
        assert raw['stderr'] == b'', 'Exact empty Node stderr required'
        assert raw['stdout'].endswith(b'\n') and raw['stdout'].count(b'\n') == 1
        value = strict(raw['stdout'])
        assert set(value) == {'scope','checks','cases','primaryExecuted','consumerExecuted','cryptoExecuted','completionPassClaimed'}
        assert value['scope'] == 'E02_COMPLETION_SYNTHETIC_DATA_ONLY'
        assert type(value['checks']) is int and value['checks'] == 54
        assert type(value['cases']) is list and len(value['cases']) == 54
        assert all(type(name) is str and 1 <= len(name) <= 160 for name in value['cases'])
        assert len(set(value['cases'])) == 54
        for key in ('primaryExecuted','consumerExecuted','cryptoExecuted','completionPassClaimed'):
            assert value[key] is False
        receipt['observedCount'] = value['checks']
        receipt['countAndOutputShapeMatched'] = True
    except BaseException as exc:
        error('original-output-shape', exc)
    try:
        after = snapshot(ack_sha)
        save('sources-after.json', after)
        receipt['sourceUnchanged'] = before is not None and before == after
    except BaseException as exc:
        error('post-capture-source-check', exc)
    receipt['captureMatched'] = bool(receipt['countAndOutputShapeMatched'] and receipt['exitCode'] == 0
        and receipt['signal'] is None and receipt['reaped'] and receipt['naturalExit']
        and receipt['stdoutEOF'] and receipt['stderrEOF'] and not receipt['forceRequested']
        and receipt['firstError'] is None and not receipt['secondaryErrors']
        and not any(receipt['truncated'].values()) and receipt['sourceUnchanged'])
    receipt['state'] = 'WRITES_STOPPED'
    receipt['result'] = 'SCOPED_DATA_CAPTURE_MATCHED_PENDING_INDEPENDENT_REVIEW' if receipt['captureMatched'] else 'STOPPED_AT_FIRST_FAILURE_NO_RETRY'
    receipt['meaning'] = 'Synthetic DATA only; no primary/consumer/runtime/crypto/native/client execution or external/canonicalPASS, SDK or experiment authority.'
    save('execution.json', receipt)
    save('result-artifact-manifest.json', dict(schema='e02-completion-control-result-files-v1',
        files=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file()],
        note='Original external tool API response objects are preserved immediately by the actual caller, separately from this child journal.'))
    print(json.dumps(dict(state='WRITES_STOPPED', captureMatched=receipt['captureMatched'],
                         execution=pin(HERE / 'execution.json'), independentResultReview='PENDING_ACTUAL_OTHER_AGENTS')))
    return 0 if receipt['captureMatched'] else 2


if __name__ == '__main__':
    sys.exit(main())
