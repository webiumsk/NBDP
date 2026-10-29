"""SOURCE-only fixed monitor preparation: AST/hash/diff, no helper/test import."""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = Path(__file__).resolve().parent
PREP = HERE.parent
SOURCE = ROOT / 'experiments/prototypes/e02_ordinary_minimum_consumer_v2'
PREVIOUS = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/current-controls-r1/capture-controls.py'
PRODUCER = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/subject.json'


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def write(name, raw):
    fd = os.open(HERE / name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return pin(HERE / name)


def put(name, value):
    return write(name, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())


def closure(value, out):
    if type(value) is dict:
        if set(value) == {'path', 'bytes', 'sha256'}:
            prior = out.get(value['path'])
            assert prior is None or prior == value, 'Conflicting pinned source operand'
            out[value['path']] = value
        else:
            for item in value.values(): closure(item, out)
    elif type(value) is list:
        for item in value: closure(item, out)


def functions(tree):
    return {n.name:ast.dump(n, include_attributes=False) for n in tree.body
            if isinstance(n, (ast.FunctionDef,ast.AsyncFunctionDef))}


def main():
    subject = pin(PREP / 'subject.json')
    assert subject['bytes'] == 6892 and subject['sha256'] == '1c0aa126dd62f96298dada5765a5bb8b8237ba9abd08f5405982787f8863e558'
    manifest = pin(PREP / 'artifact-manifest.json')
    assert manifest['sha256'] == '9fc8aea6587e75d9f893e176be79c789713460793c9171563ad6477a951c79ec'
    original_plan = pin(PREP / 'proposed-control-plan.json')
    assert original_plan['sha256'] == '8c918b1330a274f985beec09fc916575c63954c8542f648dc8a944e7f3f878db'
    assert pin(PRODUCER)['sha256'] == '296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4'
    # These are exactly the reviewed source/manifest/protected snapshot payloads.
    # Do not recursively interpret arbitrary source/config JSON as runtime grants
    # or dereference SDK/APK/image/tool assets that this pure suite never reads.
    documents = [PREP / name for name in ('subject.json','artifact-manifest.json',
        'protected-inputs-before.json','protected-inputs-after.json','version-copy-provenance.json')]
    documents += [PRODUCER]
    pinned = {}
    for path in documents:
        d = pin(path); pinned[d['path']] = d
        closure(json.loads(path.read_bytes()), pinned)
    interpreter = json.loads((PREP / 'proposed-control-plan.json').read_bytes())['interpreter']
    pinned[interpreter['path']] = interpreter
    pinned[str(PREVIOUS)] = pin(PREVIOUS)
    for row in pinned.values():
        path = Path(row['path'])
        assert path.is_absolute() and not path.is_symlink() and path.resolve(strict=True) == path
        assert path.suffix not in ('.apk','.zip','.img','.qcow2','.key'), 'No SDK/APK/image/private key body in pure source closure'
        assert pin(path) == row, 'Frozen source/control input drift'
    frozen = put('frozen-inputs.json', dict(schema='e02-minimum-consumer-control-frozen-inputs-v1',
        files=[pinned[k] for k in sorted(pinned)],
        meaning='Exact descriptors in reviewed source-v2 subject/manifest/protected/version-copy and frozen producer subject, plus interpreter/previous monitor. These are source/evidence inputs; no SDK/APK asset replay or arbitrary recursive config expansion.'))
    old = PREVIOUS.read_bytes(); current = (HERE / 'capture-controls.py').read_bytes()
    a, b = ast.parse(old), ast.parse(current)
    fa, fb = functions(a), functions(b)
    ast_report = put('monitor-typed-ast-diff.json', dict(schema='e02-minimum-consumer-capture-ast-diff-v1',
        previousMonitor=pin(PREVIOUS), currentMonitor=pin(HERE / 'capture-controls.py'),
        byteEqual=False, astParsedOnly=True, functionsUnchanged=[k for k in fa if k in fb and fa[k] == fb[k]],
        functionsChanged=[k for k in fa if k in fb and fa[k] != fb[k]],
        functionsRemoved=[k for k in fa if k not in fb], functionsAdded=[k for k in fb if k not in fa],
        declaredDeltas=['Five Python/Node scopes reduced to exact one Python86 DATA scope; same60s deadline.',
            'Exact frozen stdout1MiB/stderr256KiB post-capture retention; no streaming-memory cap claim.',
            'Only owned direct Popen.kill on failure, no process-group signal; suite has no subprocess/service effects.',
            'Externally hash-bound root acknowledgement and actual accepted same-source nonauthor reviews required.',
            'Full frozen current consumer/producer/protected inputs and interpreter/monitor/reviews/rootack checked before/after.',
            'CaptureMatched is mechanical; author never issues independent control acceptance.',
            'Coordinator-assigned current-controls-r1 storage replaces unexecuted template actual-controls path, no source-plan edit.'],
        helperImported=False, testsExecuted=0))
    diff = write('monitor-full-source.diff', ''.join(difflib.unified_diff(old.decode().splitlines(True),
        current.decode().splitlines(True), fromfile=str(PREVIOUS), tofile=str(HERE / 'capture-controls.py'))).encode())
    plan = put('control-plan.json', dict(schema='e02-minimum-consumer-fixed-control-capture-plan-v1',
        state='PREPARED_NOT_EXECUTED_NO_ROOT_ACKNOWLEDGEMENT_OR_RELEASE_BY_AUTHOR', actor='/root/android_health_implementer',
        sourceSubject=subject, sourceManifest=manifest, frozenSourcePlan=original_plan,
        runner=pin(HERE / 'capture-controls.py'), frozenInputs=frozen, interpreter=interpreter,
        argv=[interpreter['path'],'-I','-B',str(SOURCE / 'test_data_controls.py')], plannedChecks=86,
        timeoutSeconds=60, retentionBytes={'stdout':1048576,'stderr':262144},
        retentionMeaning='POST_CAPTURE_FILE_PREFIX_LIMITS_NOT_STREAMING_MEMORY_OR_CGROUP_CAPS',
        onceInvocation=[interpreter['path'],'-I','-B',str(HERE / 'capture-controls.py'),
            '--execute-once','--root-ack-sha','ACTUAL_EXTERNAL_ROOT_ACK_SHA256_REQUIRED_NOT_YET_ISSUED'],
        outputStorageDelta=dict(proposedTemplate=str(PREP / 'actual-controls'), rootAssigned=str(HERE),
            meaning='Explicit root-assigned evidence namespace only; original source plan unchanged.'),
        coordinatorAcknowledgementSchema={
            'schema':'e02-minimum-consumer-controls-root-ack-v1','actor':'/root',
            'sourceSubject':'exact sourceSubject Pin','runnerSubject':'exact runner-subject.json Pin',
            'runner':'exact capture-controls.py Pin','controlPlan':'exact control-plan.json Pin',
            'sourceQaReview':'actual accepted QA report Pin in parent preparation directory',
            'sourceSecurityReview':'actual accepted security report Pin in parent preparation directory',
            'pureControlsAuthorized':'true only after actual root instruction','allowedCount':86,
            'stopFirstFailure':True,'noRetry':True,'androidAuthorized':False,'servicesAuthorized':False,
            'cryptoOrNativeAuthorized':False,'sdkAuthorized':False},
        acknowledgementPath=str(HERE / 'coordinator-acknowledgement.json'), acknowledgementMode='0600',
        externalToolReceipts='Actual caller preserves original response objects immediately during execution; no invented lifecycle/tool fields.',
        fullPositiveWholeConsumeGap=True, independentResultsPending=True, noSdkAndroidNodeNativeCryptoNetworkServices=True,
        executed=False))
    # Recheck every actually read immutable source/evidence input before freeze.
    for row in pinned.values(): assert pin(Path(row['path'])) == row
    artifacts = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file()]
    runner_subject = put('runner-subject.json', dict(schema='e02-minimum-consumer-fixed-capture-source-subject-v1',
        state='WRITES_STOPPED_PENDING_ROOT_INSPECTION_AND_EXACT_RELEASE_NO_EXECUTION',
        author='/root/android_health_implementer', sourceSubject=subject, sourceManifest=manifest,
        runner=pin(HERE / 'capture-controls.py'), controlPlan=plan, frozenInputs=frozen,
        previousMonitor=pin(PREVIOUS), typedAstDiff=ast_report, fullSourceDiff=diff,
        preparationArtifacts=artifacts, frozenInputCount=len(pinned),
        sourceTestsPrepared=86, sourceTestsExecuted=0, originalV1AndHoldsUnchanged=True,
        fullPositiveWholeConsumeGap=True, independentApprovalIssuedByAuthor=False,
        noRootAcknowledgementOrExperimentGrantAuthored=True))
    final = put('preparation-artifact-manifest.json', dict(schema='e02-minimum-consumer-capture-preparation-artifacts-v1',
        files=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file()]))
    print(json.dumps(dict(state='WRITES_STOPPED', runner=pin(HERE / 'capture-controls.py'),
                         runnerSubject=runner_subject, controlPlan=plan, frozenInputs=frozen,
                         preparationManifest=final, frozenInputCount=len(pinned), executed=0),indent=2))


if __name__ == '__main__':
    main()
