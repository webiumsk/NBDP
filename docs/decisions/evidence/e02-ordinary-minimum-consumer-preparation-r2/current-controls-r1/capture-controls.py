"""Fixed once-only86 synthetic DATA capture. Requires a fresh external root ack.

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
SOURCE = ROOT / 'experiments/prototypes/e02_ordinary_minimum_consumer_v2'
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
ACTOR = '/root/android_health_implementer'
SOURCE_SHA = '1c0aa126dd62f96298dada5765a5bb8b8237ba9abd08f5405982787f8863e558'
MANIFEST_SHA = '9fc8aea6587e75d9f893e176be79c789713460793c9171563ad6477a951c79ec'
FROZEN_PLAN_SHA = '8c918b1330a274f985beec09fc916575c63954c8542f648dc8a944e7f3f878db'
ARGV = [str(PYTHON), '-I', '-B', str(SOURCE / 'test_data_controls.py')]
LIMITS = {'stdout': 1048576, 'stderr': 262144}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pin(path):
    assert path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'Canonical regular source path required'
    with path.open('rb') as stream:
        a = os.fstat(stream.fileno())
        assert stat.S_ISREG(a.st_mode) and 0 <= a.st_size <= 67108864, 'Bounded regular SOURCE/DATA only'
        raw = stream.read(67108865)
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
    assert subject['sha256'] == SOURCE_SHA, 'Exact source-v2 subject required'
    manifest = pin(PREP / 'artifact-manifest.json')
    assert manifest['sha256'] == MANIFEST_SHA, 'Original source-v2 manifest required'
    frozen_plan = pin(PREP / 'proposed-control-plan.json')
    assert frozen_plan['sha256'] == FROZEN_PLAN_SHA
    proposed = doc(PREP / 'proposed-control-plan.json')
    assert proposed['argv'] == ARGV and proposed['plannedChecks'] == 86
    assert proposed['timeoutSeconds'] == 60 and proposed['stdoutBytes'] == LIMITS['stdout'] and proposed['stderrBytes'] == LIMITS['stderr']
    control_plan = doc(HERE / 'control-plan.json')
    assert control_plan['argv'] == ARGV and control_plan['plannedChecks'] == 86
    assert control_plan['timeoutSeconds'] == 60 and control_plan['retentionBytes'] == LIMITS
    frozen_inputs = doc(HERE / 'frozen-inputs.json')
    assert frozen_inputs['schema'] == 'e02-minimum-consumer-control-frozen-inputs-v1'
    rows = frozen_inputs['files']
    assert 1 <= len(rows) <= 1024 and len({row['path'] for row in rows}) == len(rows)
    actual = [pin(Path(row['path'])) for row in rows]
    assert actual == rows, 'Full frozen SOURCE/producer/protected inputs changed'
    interpreter = pin(PYTHON)
    assert interpreter == proposed['interpreter'], 'Exact interpreter changed'
    ack_path = HERE / 'coordinator-acknowledgement.json'
    ack_pin = pin(ack_path)
    assert ack_pin['sha256'] == ack_sha and (ack_path.stat().st_mode & 0o777) == 0o600, 'External exact root acknowledgement required'
    ack = doc(ack_path)
    assert set(ack) == {'schema','actor','sourceSubject','runnerSubject','runner','controlPlan','sourceQaReview','sourceSecurityReview',
                        'pureControlsAuthorized','allowedCount','stopFirstFailure','noRetry','androidAuthorized','servicesAuthorized',
                        'cryptoOrNativeAuthorized','sdkAuthorized'}
    assert ack['schema'] == 'e02-minimum-consumer-controls-root-ack-v1' and ack['actor'] == '/root'
    assert ack['sourceSubject'] == subject and ack['allowedCount'] == 86
    for field in ('pureControlsAuthorized', 'stopFirstFailure', 'noRetry'):
        assert ack[field] is True
    for field in ('androidAuthorized', 'servicesAuthorized', 'cryptoOrNativeAuthorized', 'sdkAuthorized'):
        assert ack[field] is False
    assert ack['runner'] == pin(Path(__file__).resolve()) and ack['controlPlan'] == pin(HERE / 'control-plan.json')
    assert ack['runnerSubject'] == pin(HERE / 'runner-subject.json')
    runner_subject = doc(HERE / 'runner-subject.json')
    assert runner_subject['runner'] == ack['runner'] and runner_subject['controlPlan'] == ack['controlPlan']
    for row in runner_subject['preparationArtifacts']:
        assert pin(Path(row['path'])) == row, 'Frozen monitor preparation changed'
    reviewers, review_pins = [], []
    for field, role in (('sourceQaReview', 'qa'), ('sourceSecurityReview', 'security')):
        review_pin = ack[field]
        assert Path(review_pin['path']).parent == PREP and pin(Path(review_pin['path'])) == review_pin
        review = doc(Path(review_pin['path']))
        assert review['subject'] == subject and review['decision'] == 'ACCEPT_SOURCE_FOR_SCOPED_DATA_CONTROLS_ONLY'
        assert review['role'] == role and review['findings'] == []
        assert review['reviewer'] not in (ACTOR, '/root', '/root/ordinary_api35_source')
        reviewers.append(review['reviewer']); review_pins.append(review_pin)
    assert len(set(reviewers)) == 2, 'Actual separate nonauthor SOURCE reviewers required'
    # Actual session/tool origin correspondence is authenticated by the root's
    # external instruction and raw reports, never by these JSON strings alone.
    return dict(sourceSubject=subject, sourceManifest=manifest, frozenSourcePlan=frozen_plan,
        fullFrozenInputs=actual, interpreter=interpreter, monitor=pin(Path(__file__).resolve()),
        runnerSubject=ack['runnerSubject'], controlPlan=ack['controlPlan'],
        sourceReviewRecords=review_pins, coordinatorAcknowledgement=ack_pin)


def main():
    assert len(sys.argv) == 4 and sys.argv[1:3] == ['--execute-once', '--root-ack-sha'], 'Fixed single control invocation required'
    ack_sha = sys.argv[3]
    assert re.fullmatch('[0-9a-f]{64}', ack_sha), 'External acknowledgement hash required'
    os.umask(0o077)
    save('started.json', dict(actor=ACTOR, utc=utc(), pid=os.getpid(),
         scope='ONCE_86_SYNTHETIC_DATA_ONLY_NO_ANDROID_SDK_SERVICES_OR_CRYPTO'))
    before = after = None
    child = None
    raw = {'stdout': b'', 'stderr': b''}
    receipt = dict(schema='e02-minimum-consumer-pure-control-execution-v1', actor=ACTOR,
        parentCoordinator='/root', argv=ARGV, cwd=str(ROOT), expectedCount=86, startedUtc=utc(),
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
    match = re.search(rb'\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n\Z', raw['stderr'])
    receipt['observedCount'] = int(match[1]) if match else None
    receipt['countAndOutputShapeMatched'] = receipt['observedCount'] == 86 and raw['stdout'] == b''
    if not receipt['countAndOutputShapeMatched']:
        error('original-output-shape', ValueError('Exact86 unskipped successful unittest output and empty stdout required'))
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
    receipt['meaning'] = 'Synthetic DATA only, not genuine GUI/native/client evidence, whole-consumer acceptance, canonicalPASS, SDK or experiment authority.'
    save('execution.json', receipt)
    save('result-artifact-manifest.json', dict(schema='e02-minimum-consumer-control-result-files-v1',
        files=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file()],
        note='Original external tool API response objects are preserved immediately by the actual caller, separately from this child journal.'))
    print(json.dumps(dict(state='WRITES_STOPPED', captureMatched=receipt['captureMatched'],
                         execution=pin(HERE / 'execution.json'), independentResultReview='PENDING_ACTUAL_OTHER_AGENTS')))
    return 0 if receipt['captureMatched'] else 2


if __name__ == '__main__':
    sys.exit(main())
