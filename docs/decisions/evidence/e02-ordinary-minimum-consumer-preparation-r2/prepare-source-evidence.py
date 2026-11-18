"""One-shot stdlib SOURCE-only AST/hash/diff capture. Never import/test a project."""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path

REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
OLD = REPO / 'experiments/prototypes/e02_ordinary_minimum_consumer_v1'
SOURCE = REPO / 'experiments/prototypes/e02_ordinary_minimum_consumer_v2'
PREVIOUS = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r1'
OUT = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2'
PRODUCER = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/subject.json'
DISPOSITION = REPO / 'docs/decisions/evidence/transport-runtime-current-state-r3/minimum-input-metadata-disposition.json'


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def write(name, raw):
    fd = os.open(OUT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return pin(OUT / name)


def put(name, value):
    return write(name, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())


def functions(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[node.name + '.' + child.name] = ast.dump(child, include_attributes=False)
    return result


def main():
    original_copy = json.loads((OUT / 'version-copy-provenance.json').read_bytes())
    for row in original_copy['files']:
        assert pin(Path(row['original']['path'])) == row['original']
        assert pin(Path(row['preserved']['path'])) == row['preserved']
        assert row['original']['sha256'] == row['preserved']['sha256']
    assert pin(PRODUCER)['sha256'] == '296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4'
    producer = json.loads(PRODUCER.read_bytes())
    protected = [Path(p['path']) for p in producer['sources'] + producer['configurations']]
    protected += [PRODUCER, DISPOSITION,
                  REPO / 'experiments/prototypes/e02_ordinary_control_aggregate_v1/aggregate.py',
                  REPO / 'experiments/prototypes/e02_ordinary_control_aggregate_v1/INTERFACE.md',
                  REPO / 'experiments/prototypes/e02_ordinary_control_evidence_v1/consumer.py',
                  REPO / 'experiments/prototypes/e02_ordinary_control_evidence_v1/INTERFACE.md']
    before = [pin(p) for p in protected]
    for expected in producer['sources'] + producer['configurations']:
        assert pin(Path(expected['path'])) == expected
    put('protected-inputs-before.json', dict(schema='e02-minimum-consumer-protected-inputs-v2', files=before))
    expected_changed = {'consumer.py': [], 'strict.py': [], 'witness.py': [],
                        'gui.py': ['selection'], 'wire.py': ['publication', 'validation'],
                        'test_data_controls.py': ['publication_data']}
    ast_rows, prepared, original_tests = [], [], []
    for path in sorted(SOURCE.glob('*.py')):
        tree = ast.parse(path.read_bytes(), filename=str(path))
        previous = ast.parse((OLD / path.name).read_bytes())
        a, b = functions(previous), functions(tree)
        changed = sorted(k for k in a if k in b and a[k] != b[k])
        added = sorted(k for k in b if k not in a)
        removed = sorted(k for k in a if k not in b)
        assert changed == expected_changed[path.name] and not removed
        if path.name in ('consumer.py', 'strict.py', 'witness.py'):
            assert path.read_bytes() == (OLD / path.name).read_bytes()
        if path.name == 'gui.py': assert added == ['private_room_footer']
        if path.name == 'wire.py': assert added == ['candidate_app_frame']
        tests = [k for k in b if k.startswith('PureDataControls.test_')]
        prior_tests = [k for k in a if k.startswith('PureDataControls.test_')]
        prepared += tests; original_tests += prior_tests
        assert all(a[k] == b[k] for k in prior_tests)
        imports = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import): imports.extend(v.name for v in n.names)
            if isinstance(n, ast.ImportFrom): imports.append(n.module)
        assert not {'subprocess', 'socket', 'requests', 'urllib', 'importlib'} & set(imports)
        ast_rows.append(dict(source=pin(path), astParsed=True, existingFunctionsChanged=changed,
                             addedFunctions=added, removedFunctions=removed,
                             unaffectedFunctionCount=sum(k in b and a[k] == b[k] for k in a),
                             byteIdenticalToV1=path.read_bytes() == (OLD / path.name).read_bytes(),
                             imports=sorted(set(imports))))
    assert len(prepared) == 86 and len(original_tests) == 54
    static = put('static-ast-function-diff.json', dict(schema='e02-minimum-consumer-v2-static-ast-v1',
        operation='STDLIB_AST_SOURCE_HASH_ONLY_NO_PROJECT_IMPORT', files=ast_rows,
        original54TestMethodBodiesUnchanged=True, preparedTestCount=86, addedTestCount=32,
        preparedTestMethods=prepared, executedTestCount=0,
        fullPositiveWholeConsumeGraph=False, newNormativeGate=False,
        caveat='Source syntax/diff is not runtime correctness, independent approval or an executed control.'))
    diffs = []
    for path in sorted(SOURCE.iterdir()):
        if path.is_file():
            diffs.extend(difflib.unified_diff((OLD / path.name).read_text().splitlines(True),
                         path.read_text().splitlines(True), fromfile=str(OLD / path.name), tofile=str(path)))
    diff = write('full-source.diff', ''.join(diffs).encode())
    python = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
    interpreter = pin(python)
    assert interpreter['sha256'] == '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'
    plan = put('proposed-control-plan.json', dict(schema='e02-minimum-consumer-pure-control-plan-v2',
        state='PREPARED_NOT_EXECUTED_NO_AUTHORITY', interpreter=interpreter,
        argv=[str(python), '-I', '-B', str(SOURCE / 'test_data_controls.py')], plannedChecks=86,
        timeoutSeconds=60, stdoutBytes=1048576, stderrBytes=262144,
        sourceReviewRequired=['actual-independent-qa', 'actual-independent-security'],
        actualControlOutputDirectory=str(OUT / 'actual-controls'),
        allowedEffects='Owned Python/tempfile synthetic DATA only; no producer import, Android, SDK, Node, crypto, network, Docker or protocol runtime.',
        captureRequirements=['Explicit root instruction after same-frozen-subject SOURCE QA/security acceptance.',
            'One finite foreground attempt; exact source/interpreter/monitor pins before and after.',
            'Exclusive0600 raw streams; genuine API lifecycle/timing/tool fields only; preserve first failure, no silent fix/retry.',
            'Actual independent control-result review precedes later activation.'], executed=False))
    after = [pin(p) for p in protected]
    assert before == after
    for row in original_copy['files']: assert pin(Path(row['original']['path'])) == row['original']
    preserved = put('protected-inputs-after.json', dict(schema='e02-minimum-consumer-protected-inputs-v2',
         files=after, currentProtectedUnchanged=True, originalV1NineteenFilesUnchanged=True))
    subject = put('subject.json', dict(schema='e02-minimum-consumer-source-subject-v2',
        author='/root/android_health_implementer', scope='SOURCE_ONLY_NARROW_THREE_FINDING_REMEDIATION',
        state='WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_SOURCE_QA_SECURITY',
        profileId='e02-ordinary-minimum-rs-two-role-v1', sources=[pin(p) for p in sorted(SOURCE.iterdir()) if p.is_file()],
        originalV1Subject=pin(PREVIOUS / 'subject.json'),
        actualPriorQaReview=pin(PREVIOUS / 'actual-source-qa-review.json'),
        actualPriorSecurityReview=pin(PREVIOUS / 'actual-source-security-review.json'),
        actualPriorHold=pin(PREVIOUS / 'review-disposition.json'),
        preservedV1=pin(OUT / 'version-copy-provenance.json'), producerSubject=pin(PRODUCER),
        nonoperativeMetadataDisposition=pin(DISPOSITION), typedAstDiff=static, fullSourceDiff=diff,
        controlPlan=plan, preservedProtected=preserved, preparationScript=pin(Path(__file__).resolve()),
        addressedFindingIds=['QA-E02-CONSUMER-COMPOSER-001','SEC-E02-MIN-CONSUMER-COMPOSER-002',
            'QA-E02-CONSUMER-RPC-WRAPPER-002','SEC-E02-MIN-CONSUMER-RPC-001','QA-E02-CONSUMER-CANDIDATE-003'],
        claims='SOURCE correction prepared only; findings are not independently resolved by the author.',
        unchanged=['All input schemas/producer pins/bounds/gates/old8 profile/canonical status.',
            'consumer.py, strict.py and witness.py byte-identical; all54 original test bodies unchanged.'],
        preparedDataControls=86, executedDataControls=0, experimentsExecuted=False, grantsWritten=False,
        sharedFilesEdited=False, fullPositiveWholeConsumeGraph=False,
        remainingGaps=['Actual same-source independent QA/security review.',
            'All86 synthetic DATA definitions remain unexecuted; no positive runtime acceptance.',
            'Full positive whole consume() path remains unexercised; later genuine complete evidence needs independent review before canonical claims.',
            'Authentic root/history/outer/resource/origin wrappers and two complete actual role windows remain future inputs.',
            'Canonical current primary matrix and integration remain separately mandatory.'],
        canonicalE02='PARTIAL22_UNCHANGED', blockers=['Q01','Q08','Q13','Q15','Q27']))
    artifacts = put('artifact-manifest.json', dict(schema='e02-minimum-consumer-preparation-artifacts-v2',
         files=[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()]))
    print(json.dumps(dict(state='WRITES_STOPPED', subject=subject, artifactManifest=artifacts,
                         static=static, diff=diff, controlPlan=plan, prepared=86, executed=0), indent=2))


if __name__ == '__main__':
    main()
