"""SOURCE-only hashing/AST/diff packet. Never imports project modules."""
from pathlib import Path
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
SOURCE = ROOT / 'experiments/prototypes/e02_ordinary_minimum_consumer_v4'
OLD = ROOT / 'experiments/prototypes/e02_ordinary_minimum_consumer_v3'
HERE = Path(__file__).resolve().parent


def pin(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def put(name, value, raw=False):
    payload = value.encode() if raw else (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    path = HERE / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream: stream.write(payload)
    return pin(path)


preserved = json.loads((HERE / 'preserved-v3-source-pins.json').read_text())
for before in preserved['pins']:
    assert pin(before['path']) == before, 'Frozen consumer3 source changed'
sources = [pin(p) for p in sorted(SOURCE.iterdir()) if p.is_file()]
syntax, controls, full_diff, function_changes = [], [], [], []
for p in sorted(SOURCE.iterdir()):
    if not p.is_file(): continue
    after = p.read_text(); old = OLD / p.name; before = old.read_text() if old.exists() else ''
    full_diff.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile=str(old) if old.exists() else '/dev/null', tofile=str(p)))
    if p.suffix != '.py': continue
    tree = ast.parse(after, filename=str(p)); syntax.append(dict(path=str(p), result='AST_PARSE_ONLY_NO_IMPORT_OR_EXECUTION'))
    old_functions = {} if not old.exists() else {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(before).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    current = {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    function_changes.append(dict(path=str(p), unchanged=[n for n in current if old_functions.get(n) == current[n]],
        changed=[n for n in current if n in old_functions and old_functions[n] != current[n]], added=[n for n in current if n not in old_functions]))
    if p.name.startswith('test_'):
        names = [c.name + '.' + n.name for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
        controls.append(dict(source=pin(p), count=len(names), exactDefinedNames=names, meaning='STATIC_DEFINITIONS_NOT_EXECUTED', executed=0))

inputs = []
paths = [
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/subject.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/source-review-disposition.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/next-consumer-contract-inputs.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/component-carry-matrix.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/current-controls-r1/results-r1/subject.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/current-controls-r1/results-r1/acceptance.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/current-controls-r1/results-r1/actual-result-qa-review.json',
 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/current-controls-r1/results-r1/actual-result-security-review.json',
 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/subject.json',
 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/source-review-disposition.json',
 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/current-controls-r1/results-r1/subject.json',
 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r2/current-controls-r1/results-r1/acceptance.json',
 'docs/decisions/evidence/e02-ordinary-minimum-profile-proposal-r1/coordinator-adoption.json',
 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r3/subject.json',
 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r4/whole-window-integration.json',
 'docs/research/required-experiments.md',
 'experiments/prototypes/e02_ordinary_minimum_v2/EXPORT-CONTRACT.md',
]
for rel in paths: inputs.append(pin(ROOT / rel))
producer = json.loads((ROOT / paths[0]).read_text())
for row in producer['sources'] + producer['configurations']:
    assert pin(row['path']) == row
    if not any(p['path'] == row['path'] for p in inputs): inputs.append(row)
python = pin(Path('/home/peterhorvath/.miniforge3/bin/python3.13'))
config = json.loads(Path(producer['configurations'][0]['path']).read_text())
fixture = json.loads((ROOT / 'experiments/prototypes/e02_ordinary_minimum_v2/fixture-plan.json').read_text())
missing = []
for kind, path in [('historicalRustBinary', fixture['pins']['rustBinary']['source']),
                   ('historicalGuardBundleManifest', config['guardBundleInventory']['path']),
                   ('sdkRoot', config['sdkRoot']), ('amethystApk', config['amethystApk']['path']),
                   ('helperApk', config['helperApk']['path'])]:
    exists = Path(path).exists()
    missing.append(dict(kind=kind, path=path, existsAtSourcePreparation=exists,
        status='NOT_READY' if not exists else 'EXISTS_NOT_RUNTIME_QUALIFIED',
        actualPin=pin(path) if exists and Path(path).is_file() else None))
input_pin = put('input-manifest.json', dict(schema='e02-consumer4-source-inputs-v1', inputs=inputs, interpreter=python,
    runtimeOperands=missing, missingOperandMeaning='Historical DATA acceptance never creates current runtime bytes/authority'))
static_pin = put('static-source-checks.json', dict(schema='e02-consumer4-static-source-v1', syntax=syntax,
    importedProjectModules=False, executedControls=0, runtimeExecuted=False))
diff_pin = put('full-source.diff', ''.join(full_diff), True)
ast_pin = put('ast-function-changes.json', dict(schema='e02-consumer4-ast-function-change-v1', files=function_changes))
plan_pin = put('proposed-control-plan.json', dict(schema='e02-consumer4-proposed-data-controls-v1', state='SOURCE_ONLY_NOT_EXECUTION_AUTHORITY',
    interpreter=python, scopes=controls, commands=[[python['path'], '-I', '-B', row['source']['path']] for row in controls],
    timeoutSecondsEach=60, retainedStdoutBytes=1048576, retainedStderrBytes=262144,
    captureRequired='Separate reviewed bounded foreground capture with actual root once-release and original API receipts; no silent retry',
    actualExecutions=0, allowed='Owned stdlib/tempfile public synthetic DATA only',
    excluded=['producer', 'Android', 'Docker', 'relay', 'network', 'native Rust', 'cryptography', 'SDK', 'completion'],
    coverageGap='Prepared complete incoming/archive window graphs plus observer/publication positives; no full top-level consume() model because genuine immutable external pin closure cannot be fabricated. Independent coverage assessment before activation.'))
readme_pin = put('README.md', '# Consumer4 SOURCE packet\n\n'
    'New version bound to frozen producer2. Held consumer3 and frozen producer2 files are unchanged.\n'
    'Input pins, complete source diff and AST function changes are included. Source parsing\n'
    'is not project module evaluation or executed controls. Defined controls remain unrun.\n\n'
    'Review scope is DATA SOURCE readiness only. No current runtime closure, SDK admission,\n'
    'client rows or canonical PASS follows. External runtime prerequisites are\n'
    'reported with fresh present/missing status. Positive incoming/archive window graphs\n'
    'are prepared with real unpatched evaluators; top-level consume() coverage remains open.\n\n'
    'Actual independent QA/security SOURCE review and a separately reviewed root-released\n'
    'capture precede any DATA control execution. Completion2 is not implemented here.\n', True)
subject = dict(schema='e02-ordinary-minimum-consumer4-source-subject-v1', author='/root/consumer3_preparation', coordinator='/root',
    state='WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_SOURCE_QA_SECURITY', scope='SOURCE_ONLY_PRODUCER2_DATA_CONSUMER_NO_EXECUTION',
    profileId='e02-ordinary-minimum-rs-two-role-v2', preparedAtUtc=datetime.now(timezone.utc).isoformat(),
    producerSubject=pin(ROOT / paths[0]), sources=sources, inputs=input_pin,
    preparationScript=pin(__file__), preparationFailures=pin(HERE / 'preparation-failures.json'), remediation=pin(HERE / 'remediation-scope.json'),
    preservedOriginalSource=pin(HERE / 'preserved-v3-source-pins.json'), fullSourceDiff=diff_pin,
    typedAstChanges=ast_pin, syntaxOnly=static_pin, controlPlan=plan_pin, readme=readme_pin,
    definedControlScopes=[row['count'] for row in controls], controlsExecuted=0, importedProjectModules=False,
    runtimeStatus='NOT_READY', missingRuntimeOperands=missing,
    wholeConsumerPositiveGraph='NOT_PREPARED_IMMUTABLE_EXTERNAL_PIN_CLOSURE_LIMIT',
    wholeWindowPositiveGraph='PREPARED_INCOMING_AND_ARCHIVE_NOT_EXECUTED', integratedObserverPublicationPositiveGraph='PREPARED_NOT_EXECUTED',
    completion2Implemented=False, actualClientRows=0, canonicalE02='PARTIAL22_UNCHANGED',
    sdkAuthorized=False, authorApprovesOwnSourceOrResults=False,
    requiredNext=['Independent exact-subject SOURCE QA/security', 'Separate reviewed capture/root release before one DATA batch',
      'Independent exact-result QA/security', 'Independent assessment of remaining whole-consume coverage limit and genuine runtime prerequisites before activation'])
subject_pin = put('subject.json', subject)
print(json.dumps(dict(subject=subject_pin, sourceFiles=len(sources), controlDefinitions=subject['definedControlScopes'],
    controlsExecuted=0, originalFilesUnchanged=True, runtimeStatus='NOT_READY')))
