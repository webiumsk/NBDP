"""One-shot SOURCE evidence preparation. Stdlib AST/hash only; no project import."""
import ast
import hashlib
import json
import os
from pathlib import Path

REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
SOURCE = REPO / 'experiments/prototypes/e02_ordinary_minimum_consumer_v1'
EVIDENCE = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r1'
PRODUCER = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/subject.json'
ADOPTION = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-profile-proposal-r1/coordinator-adoption.json'
AUTHOR = '/root/android_health_implementer'


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def put(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    fd = os.open(EVIDENCE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return pin(EVIDENCE / name)


def main():
    producer_pin = pin(PRODUCER)
    assert producer_pin['bytes'] == 35766 and producer_pin['sha256'] == '296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4'
    producer = json.loads(PRODUCER.read_bytes())
    protected = [PRODUCER, ADOPTION, *[Path(p['path']) for p in producer['sources']],
                 *[Path(p['path']) for p in producer['configurations']],
                 REPO / 'experiments/prototypes/e02_ordinary_control_aggregate_v1/aggregate.py',
                 REPO / 'experiments/prototypes/e02_ordinary_control_aggregate_v1/INTERFACE.md',
                 REPO / 'experiments/prototypes/e02_ordinary_control_evidence_v1/consumer.py',
                 REPO / 'experiments/prototypes/e02_ordinary_control_evidence_v1/INTERFACE.md']
    before = [pin(p) for p in protected]
    for expected in producer['sources'] + producer['configurations']:
        assert pin(Path(expected['path'])) == expected
    assert pin(ADOPTION)['sha256'] == '2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287'
    before_pin = put('protected-inputs-before.json', dict(schema='e02-minimum-consumer-protected-inputs-v1',
        meaning='READ_ONLY_CURRENT_PROTECTED_SOURCE_SNAPSHOT_NOT_A_RUNTIME_RERUN', files=before))
    rows, tests, calls = [], [], []
    for path in sorted(SOURCE.glob('*.py')):
        tree = ast.parse(path.read_bytes(), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(a.name for a in node.names)
            if isinstance(node, ast.ImportFrom): imports.append(node.module)
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'): tests.append(node.name)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name): calls.append(node.func.id)
        assert not {'subprocess', 'socket', 'requests', 'urllib', 'importlib'} & set(imports)
        rows.append(dict(source=pin(path), astParsed=True, imports=sorted(set(imports))))
    assert not {'exec', 'eval', 'compile', '__import__'} & set(calls)
    assert len(tests) == 54 and len(set(tests)) == 54
    static_pin = put('static-source-checks.json', dict(schema='e02-minimum-consumer-static-source-v1',
        author=AUTHOR, operation='STDLIB_AST_HASH_ONLY', files=rows, preparedTestMethods=tests,
        preparedTestCount=len(tests), executedTestCount=0, projectModulesImported=False,
        androidNodeCryptoNetworkSdkServicesExecuted=False,
        limitations=['AST validity is not runtime correctness or independent review.',
                    'Targeted positives do not construct a full positive consume() graph.',
                    'Externally authenticated actual session/tool origins remain future inputs.']))
    python = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
    interpreter = pin(python)
    assert interpreter['sha256'] == '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'
    plan_pin = put('proposed-control-plan.json', dict(schema='e02-minimum-consumer-pure-control-plan-v1',
        state='PREPARED_NOT_EXECUTED_NO_AUTHORITY', sourceReviewRequired=['actual-independent-qa', 'actual-independent-security'],
        interpreter=interpreter, argv=[str(python), '-I', '-B', str(SOURCE / 'test_data_controls.py')],
        plannedChecks=54, timeoutSeconds=60, stdoutBytes=1048576, stderrBytes=262144,
        allowedEffects='Owned temporary Python DATA files only; no producer import, SDK, Android, Node, crypto, network, Docker or protocol runtime.',
        actualControlOutputDirectory=str(EVIDENCE / 'actual-controls'),
        captureRequirements=['Explicit root instruction after actual same-frozen-source QA/security acceptance.',
            'Pin full source/interpreter/monitor before and after; exclusive0600 output; one foreground attempt.',
            'Keep raw stdout/stderr, genuine available status/reap/EOF/force/timing/tool association fields.',
            'Stop first failure; no silent fix/retry. Actual result review precedes activation.'],
        executed=False))
    after = [pin(p) for p in protected]
    assert before == after
    after_pin = put('protected-inputs-after.json', dict(schema='e02-minimum-consumer-protected-inputs-v1',
        meaning='UNCHANGED_DURING_SOURCE_PREPARATION_CAPTURE_ONLY', files=after, equalsBefore=True))
    sources = [pin(p) for p in sorted(SOURCE.iterdir()) if p.is_file()]
    subject = put('subject.json', dict(schema='e02-minimum-consumer-source-subject-v1', author=AUTHOR,
        state='WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_SOURCE_QA_SECURITY',
        scope='SOURCE_ONLY_STANDALONE_MINIMUM_DATA_CONSUMER_NO_EXECUTION', profileId='e02-ordinary-minimum-rs-two-role-v1',
        sources=sources, producerSubject=producer_pin, adoption=pin(ADOPTION), staticSource=static_pin,
        controlPlan=plan_pin, protectedBefore=before_pin, protectedAfter=after_pin,
        preparationScript=pin(Path(__file__).resolve()), preparedControls=54, executedControls=0,
        experimentsExecuted=False, grantsWritten=False, sharedFilesEdited=False, oldEightProfileChanged=False,
        sourceConsistencyOnly=True, independentApprovalIssuedByAuthor=False,
        knownSourceMetadataFinding='Unused incoming NSEC65 literal retained; actual used driver constant63/account/GUI/wire bound. No normalization.',
        remainingGaps=['Actual independent QA/security source review; source correctness not established by AST.',
            'Targeted54 DATA definitions remain unexecuted; full positive whole-consumer fixture absent.',
            'Real candidate/history/window/resource/outer/origin wrappers and actual nonauthor/nonoperator same-graph reviews remain future inputs.',
            'Per-command clock samples are not emitted by the producer; exact guarded policy and actual outer/command/lease/cleanup remain distinct.',
            'Canonical current primary matrix/integration remains mandatory and unqualified here.'],
        canonicalE02='PARTIAL22_UNCHANGED', blockers=['Q01', 'Q08', 'Q13', 'Q15', 'Q27']))
    artifacts = [pin(p) for p in sorted(EVIDENCE.iterdir()) if p.is_file()]
    manifest = put('artifact-manifest.json', dict(schema='e02-minimum-consumer-preparation-artifacts-v1', files=artifacts))
    print(json.dumps(dict(state='WRITES_STOPPED', subject=subject, artifactManifest=manifest,
                          staticSource=static_pin, plan=plan_pin, preparedControls=54, executedControls=0,
                          protectedInputsUnchanged=len(before)), indent=2))


if __name__ == '__main__':
    main()
