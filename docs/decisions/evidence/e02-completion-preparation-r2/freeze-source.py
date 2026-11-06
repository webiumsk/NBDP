"""SOURCE-only pin/diff/definition indexing. No project modules evaluated."""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
import re

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
SOURCE = ROOT / 'experiments/prototypes/e02_completion_v2'
OLD = ROOT / 'experiments/prototypes/e02_completion_v1'
HERE = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def write(name, value, raw=False):
    payload = value.encode() if raw else (json.dumps(value, indent=2) + '\n').encode()
    path = HERE / name
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream: stream.write(payload)
    return pin(path)


preserved = json.loads((HERE / 'preserved-completion1-source-pins.json').read_text())
for row in preserved['pins']: assert pin(row['path']) == row, 'Frozen completion1 changed'
profile = json.loads((SOURCE / 'profile.json').read_text())
consumer = json.loads(Path(profile['consumerSubject']['path']).read_text())
producer = json.loads(Path(profile['producerSubject']['path']).read_text())
for row in consumer['sources'] + producer['sources'] + producer['configurations']:
    assert pin(row['path']) == row, 'Frozen producer/consumer bytes changed'

sources = [pin(path) for path in sorted(SOURCE.iterdir()) if path.is_file()]
diff = []
for row in sources:
    path = Path(row['path']); old = OLD / path.name
    before = old.read_text() if old.exists() else ''
    diff.extend(difflib.unified_diff(before.splitlines(True), path.read_text().splitlines(True),
        fromfile=str(old) if old.exists() else '/dev/null', tofile=str(path)))
diff_pin = write('full-source.diff', ''.join(diff), True)

old_result = ROOT / 'docs/decisions/evidence/e02-completion-preparation-r1/current-controls-r1/data.stdout'
old_cases = json.loads(old_result.read_text())['cases']; assert len(old_cases) == 54
extra = [
 'exact-historical-native-prerequisite-positive-DATA',
 'rebuilt-different-native-binary-does-not-inherit-E01',
 'legacy-consumer-result-v1-refused', 'legacy-minimum-profile-v1-refused',
 'old-unused-metadata-marker-cannot-stand-for-producer2',
]
adapter_source = (SOURCE / 'test_controls_adapter.mjs').read_text()
blocks = re.findall(r"for\(const \[name,change\] of \[(.*?)\]\)check\('([^']+)'", adapter_source, re.S)
assert len(blocks) == 2
names = [[prefix + name for name in re.findall(r"\['([^']+)',", block)] for block, prefix in blocks]
adapter_cases = ['positive-four-separate-synthetic-control-scopes', *names[0],
    'positive-synthetic-original-api-envelope-shape-only', *names[1]]
assert len(adapter_cases) == 41
definition_pin = write('defined-controls.json', dict(schema='e02-completion2-source-control-definitions-v1',
    scopes=[dict(name='original-version-native-data', source=pin(SOURCE / 'test_data.mjs'),
                 definedCount=59, cases=old_cases + extra, legacy54DefinitionReference=pin(old_result)),
            dict(name='consumer139-adapter-tool-data', source=pin(SOURCE / 'test_controls_adapter.mjs'),
                 definedCount=41, cases=adapter_cases)], actualExecutions=0,
    meaning='Source definitions and preserved earlier names only; no new test/module execution'))
plan_pin = write('control-plan.json', dict(schema='e02-completion2-proposed-controls-v1',
    node=profile['node'], definitions=definition_pin,
    commands=[[profile['node']['path'], str(SOURCE / name)] for name in ('test_data.mjs','test_controls_adapter.mjs')],
    expectedCountsSeparate=[59,41], timeoutSecondsEach=60,
    stdoutRetainedBytes=1048576, stderrRetainedBytes=262144,
    allowed='Owned tempfile/public synthetic DATA and builtin modules only',
    prohibited=['runner evaluation', 'consumer', 'primary', 'native', 'cryptography', 'relay', 'Android', 'SDK', 'runtime'],
    executionAuthorized=False, controlsExecuted=0,
    next='Independent exact SOURCE QA/security then separately reviewed foreground capture/root release'))

observed = []
for name in ('rustBinary','node','python','timeout'):
    expected = profile[name]; path = Path(expected['path']); exists = path.exists()
    actual = pin(path) if exists and path.is_file() else None
    observed.append(dict(name=name, expected=expected, actual=actual,
        status='ABSENT_NOT_READY' if actual is None else 'MATCHED_BYTES_NOT_RUNTIME_QUALIFICATION' if actual == expected else 'MISMATCH_NOT_READY'))
input_rows = [profile['consumerSubject'], profile['producerSubject'], profile['adoption'], profile['e01'],
              profile['consumerControlDefinitions'], profile['consumerControlResult'], profile['consumerControlCapture'],
              profile['consumerControlPlan'], profile['consumerControlAcceptance'], profile['consumerControlRelease'],
              profile['consumerControlToolReceipts'],
              pin(ROOT / 'docs/research/required-experiments.md'),
              pin(ROOT / 'docs/decisions/evidence/e02-completion-preparation-r1/subject.json'),
              pin(ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r4/source-review-disposition.json')]
acceptance = json.loads(Path(profile['consumerControlAcceptance']['path']).read_text())
input_rows += acceptance['reviews']
for row in input_rows: assert pin(row['path']) == row
input_pin = write('input-manifest.json', dict(schema='e02-completion2-source-inputs-v1', inputs=input_rows,
    currentObservedOperands=observed, runtimeStatus='NOT_READY',
    preservedNativeBinding='Historical E01/native hash is unchanged. A different rebuilt binary cannot inherit E01.',
    wholeConsumePositive='No actual immutable whole-consume/client graph exists; accepted139 is synthetic DATA only.'))
syntax_pin = write('syntax-only.json', dict(schema='e02-completion2-parser-only-v1',
    origin='Worker transcription of actual tools.exec_command responses; not authenticated provider logs',
    commands=[dict(argv=[profile['node']['path'],'--check',str((SOURCE / name).relative_to(ROOT))],
                   cwd=str(ROOT), exitCode=0,stdout='',stderr='')
              for name in ('data.mjs','control-data.mjs','runner.mjs','test_data.mjs','test_controls_adapter.mjs')],
    projectModulesImported=False, projectModulesEvaluated=False, testsExecuted=0, runtimeExecuted=False))
readme_pin = write('README.md', '# Completion2 SOURCE packet\n\n'
    'Completion1/producer2/consumer4 source bytes remain unchanged. New SOURCE binds\n'
    'the accepted consumer139 four-scope result, exact root plan/runner/API receipts,\n'
    'current ordinary result-v2 and original primary22/raw PARTIAL/literal skip.\n\n'
    'Definitions59/41 have not run. Parser checks do not evaluate modules. Independent\n'
    'SOURCE review and a separately reviewed root-released capture precede controls.\n'
    'Native historical E01 equality and genuine whole-consume/client inputs remain\n'
    'mandatory; no binary swap, runtime grant, canonical promotion or SDK follows.\n', True)
subject = dict(schema='e02-completion-source-subject-v2', author='/root/consumer3_preparation', coordinator='/root',
    state='WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_SOURCE_QA_SECURITY',
    preparedAtUtc=datetime.now(timezone.utc).isoformat(), sources=sources,
    preservedCompletion1=pin(HERE / 'preserved-completion1-source-pins.json'),
    producerSubject=profile['producerSubject'], consumerSubject=profile['consumerSubject'],
    acceptedConsumerData=profile['consumerControlAcceptance'], inputs=input_pin,
    fullSourceDiff=diff_pin, definedControls=definition_pin, controlPlan=plan_pin,
    syntaxOnly=syntax_pin, readme=readme_pin, preparationScript=pin(__file__),
    controlsDefinedSeparate=[59,41], controlsExecuted=0,
    projectModulesEvaluated=False, effectiveRunConfigMaterialized=False, runtimeAuthorized=False,
    runtimeStatus='NOT_READY', wholeConsumeRuntime='ABSENT', currentPrimary22Executed=False,
    canonicalE02='PARTIAL22_UNCHANGED', stockE04E06Unlocked=False,
    architecturalBlockersUnchanged=['Q01','Q08','Q13','Q15','Q27'],
    authorApprovesOwnSourceOrResults=False,
    next=['Independent exact SOURCE QA/security','Separate reviewed capture and root once release',
          'Actual controls and independent result reviews','Genuine native/E01/ordinary/relay prerequisites before any runtime'])
subject_pin = write('subject.json', subject)
print(json.dumps(dict(subject=subject_pin,sources=len(sources),controlsDefined=[59,41],controlsExecuted=0,runtimeStatus='NOT_READY')))
