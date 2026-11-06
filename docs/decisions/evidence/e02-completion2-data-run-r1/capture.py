"""Once-only foreground capture of reviewed, fixed synthetic DATA tests.

Uses communicate() buffering. Retention ceilings are checked after capture and
are not streaming memory limits. Timeout/failure stops the remaining scopes.
This runner does not create runtime authority or start Android/Docker/network.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'experiments/prototypes/e02_completion_v2'
INTERPRETER = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')


def pin(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('REGULAR_INPUT_REQUIRED:' + str(path))
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def check(pins):
    for expected in pins:
        if pin(expected['path']) != expected:
            raise ValueError('INPUT_DRIFT:' + expected['path'])


def write(name, value, raw=False):
    data = value if raw else (json.dumps(value, indent=2) + '\n').encode()
    fd = os.open(HERE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        written = stream.write(data)
        if written != len(data):
            raise OSError('SHORT_CAPTURE_WRITE')
        stream.flush()
        os.fsync(stream.fileno())
    return pin(HERE / name)


def main():
    if len(sys.argv) != 2:
        raise ValueError('EXTERNAL_PLAN_SHA256_REQUIRED')
    planned = pin(HERE / 'plan.json')
    if planned['sha256'] != sys.argv[1]:
        raise ValueError('EXTERNAL_PLAN_MISMATCH')
    plan = json.loads((HERE / 'plan.json').read_bytes())
    if set(plan) != {'schema', 'scope', 'inputs', 'commands', 'limits', 'release'}:
        raise ValueError('CLOSED_PLAN_REQUIRED')
    if plan['schema'] != 'nbdp-completion2-fixed-data-capture-v1' or plan['scope'] != 'SYNTHETIC_DATA_ONLY':
        raise ValueError('FIXED_DATA_SCOPE_REQUIRED')
    if plan['limits'] != {'commandSeconds': 60, 'stdoutRetainedBytes': 1048576, 'stderrRetainedBytes': 262144}:
        raise ValueError('FIXED_LIMITS_REQUIRED')
    allowed = {'test_data.mjs', 'test_controls_adapter.mjs'}
    if not plan['commands'] or len(plan['commands']) > 2:
        raise ValueError('FIXED_NONEMPTY_COMMANDS_REQUIRED')
    seen = set()
    for command in plan['commands']:
        if set(command) != {'name', 'argv', 'expectedCases'} or command['name'] not in allowed or command['name'] in seen:
            raise ValueError('FIXED_DISTINCT_SCOPES_REQUIRED')
        seen.add(command['name'])
        if command['argv'] != [str(INTERPRETER), str(SOURCE / command['name'])]:
            raise ValueError('FIXED_ARGV_REQUIRED')
        if type(command['expectedCases']) is not int or command['expectedCases'] < 1:
            raise ValueError('POSITIVE_CASE_COUNT_REQUIRED')
    check(plan['inputs'])
    release = plan['release']
    if set(release) != {'path', 'bytes', 'sha256'}:
        raise ValueError('ROOT_RELEASE_PIN_REQUIRED')
    check([release])
    grant = json.loads(Path(release['path']).read_bytes())
    frozen_batch = {key: plan[key] for key in ('schema', 'scope', 'inputs', 'commands', 'limits')}
    if (grant.get('decision') != 'RELEASE_ONE_FIXED_COMPLETION2_DATA_BATCH'
            or grant.get('runner') != pin(__file__) or grant.get('batch') != frozen_batch):
        raise ValueError('EXACT_ROOT_RELEASE_REQUIRED')
    # Exclusive marker makes a second invocation refuse before any test starts.
    write('started.json', {'plan': planned, 'pid': os.getpid(), 'startedUtcNs': time.time_ns()})
    results = []
    failure = None
    for command in plan['commands']:
        row = {'name': command['name'], 'argv': command['argv'], 'expectedCases': command['expectedCases'],
               'startedUtcNs': time.time_ns(), 'exitCode': None, 'timeout': False,
               'naturalExit': False, 'reaped': False, 'stdoutEOF': False, 'stderrEOF': False}
        results.append(row)
        started = time.monotonic_ns()
        try:
            check(plan['inputs'])
            child = subprocess.run(command['argv'], cwd=SOURCE, input=b'', capture_output=True, timeout=60,
                                   env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'})
            row.update(exitCode=child.returncode, naturalExit=child.returncode >= 0,
                       reaped=True, stdoutEOF=True, stderrEOF=True)
            row['stdoutCapturedBytes'] = len(child.stdout)
            row['stderrCapturedBytes'] = len(child.stderr)
            row['stdout'] = write(command['name'] + '.stdout', child.stdout[:1048576], raw=True)
            row['stderr'] = write(command['name'] + '.stderr', child.stderr[:262144], raw=True)
            if len(child.stdout) > 1048576 or len(child.stderr) > 262144:
                row['truncated'] = True
                raise ValueError('POST_CAPTURE_RETENTION_CEILING_EXCEEDED')
            row['truncated'] = False
            check(plan['inputs'])
            if child.returncode != 0:
                raise ValueError('TEST_PROCESS_FAILED')
        except subprocess.TimeoutExpired as exc:
            # subprocess.run kills and waits for its direct child. Descendant
            # closure/complete EOF are deliberately UNKNOWN on this path.
            row.update(timeout=True, reaped=True, stdoutEOF=None, stderrEOF=None)
            row['partialStdout'] = write(command['name'] + '.partial.stdout', (exc.output or b'')[:1048576], raw=True)
            row['partialStderr'] = write(command['name'] + '.partial.stderr', (exc.stderr or b'')[:262144], raw=True)
            failure = 'TIMEOUT_UNQUALIFIED'; break
        except Exception as exc:
            failure = type(exc).__name__ + ':' + str(exc); break
        finally:
            row['elapsedWallNs'] = time.monotonic_ns() - started
    result = {'schema': 'nbdp-completion2-fixed-data-result-v1', 'plan': planned, 'commands': results,
              'failure': failure, 'remainingScopesExecuted': False,
              'scope': 'SYNTHETIC_DATA_ONLY', 'ordinaryRows': 0, 'e02': 'PARTIAL22_UNCHANGED',
              'retentionMeaning': 'communicate() memory buffering; post-capture ceilings, not streaming memory bounds',
              'resultAcceptance': 'PENDING_INDEPENDENT_QA_SECURITY'}
    receipt = write('execution.json', result)
    print(json.dumps({'execution': receipt, 'failure': failure}), flush=True)
    return 0 if failure is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
