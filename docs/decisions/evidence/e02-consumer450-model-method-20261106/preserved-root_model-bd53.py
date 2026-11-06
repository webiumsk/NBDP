import datetime
import hashlib
import json
import os
import re
import shlex
import stat
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EV = ROOT / 'docs/decisions/evidence'
SOURCE = EV / 'e02-consumer-eose-basis-successor-20261105/source3/coupled-r1'
REVIEW = EV / 'e02-consumer-eose-basis-successor-20261105/review-coupled-r1'
OUT = EV / 'e02-consumer450-model-actual-20261106/r1'
METHOD = EV / 'e02-consumer450-model-method-20261106'
CLOCK_SELECTION = EV / 'e02-consumer-eose-basis-successor-20261105/root-consumer-control-clock-selection.json'
READ_ADMISSION = METHOD / 'root-readonly-operands.json'
FLAGS = {'truncated', 'output_truncated', 'interrupted', 'error', 'isError'}
RESPONSE = {'chunk_id', 'wall_time_seconds', 'exit_code', 'original_token_count', 'output', 'session_id'} | FLAGS

def pin(p):
    p = Path(p); raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def checked(p):
    assert type(p) is dict and set(p) == {'path', 'bytes', 'sha256'}
    assert p['sha256'] not in DENIED_CURRENT, 'CURRENT_HELPER_IDENTITY_FORBIDDEN'
    if p['sha256'] in {q['sha256'] for q in ALLOWED_OLD.values()} or '/producer4-helper-probe-actual-' in p['path']:
        assert ALLOWED_OLD.get(p['path']) == p, 'EXACT_ADMITTED_HISTORICAL_MODEL_OPERAND_ONLY'
    assert '65d8116b77bc0af1a108122ec28cfcea' not in p['path']
    assert type(p['bytes']) is int and pin(p['path']) == p, p
    return p

def pairs(items):
    d = {}
    for k, v in items:
        assert k not in d, 'DUPLICATE_KEY'; d[k] = v
    return d

def load(p):
    raw = Path(p).read_bytes(); assert len(raw) <= 16777216
    return json.loads(raw, object_pairs_hook=pairs, parse_float=Decimal,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def doc(p):
    return load(checked(p)['path'])

def write(p, value):
    assert not p.exists(), p
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return pin(p)

def snapshot(rows):
    result = []
    for p in rows:
        checked(p); f = Path(p['path']); s = f.stat()
        assert f.is_file() and not f.is_symlink()
        result.append(dict(pin=p, mode=stat.S_IMODE(s.st_mode), uid=s.st_uid, gid=s.st_gid,
                           device=str(s.st_dev), inode=str(s.st_ino),
                           mtimeNs=str(s.st_mtime_ns), ctimeNs=str(s.st_ctime_ns)))
    return dict(schema='e02-consumer6-current-inputs-v1', rows=result)

def request(group):
    argv = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'LC_ALL=C.UTF-8',
            '/usr/bin/timeout', '--signal=KILL', str(CLOCKS[group['name']]) + 's', *group['argv']]
    return dict(cmd=shlex.join(argv), workdir=group['cwd'], login=False, yield_time_ms=1000, max_output_tokens=20000)

def origin_output(origin, expected):
    assert set(origin) == {'schema', 'operator', 'launch', 'polls'}
    assert origin['schema'] == 'e02-actual-tool-custody-v1' and origin['operator'] == '/root'
    assert type(origin['polls']) is list and len(origin['polls']) <= 128
    output = []; session = None; terminal = False
    for i, frame in enumerate([origin['launch'], *origin['polls']]):
        assert not terminal and set(frame) == {'toolName', 'actualArguments', 'unmodifiedResponse'}
        a, r = frame['actualArguments'], frame['unmodifiedResponse']
        assert type(r) is dict and set(r) <= RESPONSE
        if i == 0:
            assert frame['toolName'] == 'tools.exec_command' and a == expected
            assert type(a['login']) is bool and a['login'] is False
        else:
            assert frame['toolName'] == 'tools.write_stdin' and set(a) <= {'session_id', 'chars', 'yield_time_ms', 'max_output_tokens'}
            assert type(a['session_id']) is int and a['session_id'] == session
            assert 'chars' not in a or a['chars'] == ''
            assert all(type(a[k]) is int and a[k] > 0 for k in ('yield_time_ms', 'max_output_tokens') if k in a)
        assert all(type(r[k]) is bool and r[k] is False for k in FLAGS if k in r)
        w = r['wall_time_seconds']; assert type(w) in (int, Decimal) and w >= 0
        if isinstance(w, Decimal): assert w.is_finite() and not w.is_signed()
        cap = a.get('max_output_tokens', 10000)
        if 'original_token_count' in r: assert type(r['original_token_count']) is int and 0 <= r['original_token_count'] <= cap
        text = r['output']; assert type(text) is str and len(text.encode()) <= 1048576
        output.append(text)
        code = r.get('exit_code'); active = r.get('session_id')
        if code is None:
            assert type(active) is int and active > 0
            if session is None: session = active
            assert active == session
        else:
            assert type(code) is int and code == 0 and active is None; terminal = True
    assert terminal
    raw = ''.join(output).encode(); assert len(raw) <= 1048576
    return raw

# Source-selected fixed clocks and separately issued two-operand read admission.
clock_policy = load(CLOCK_SELECTION)
assert pin(CLOCK_SELECTION)['sha256'] == 'af211c44c3218c0cc71a882fbaddc78959571962e6198ef98546374417d89f16'
CLOCKS = {g['name']:g['outerKillSeconds'] for g in clock_policy['groups']}
assert len(CLOCKS) == len(clock_policy['groups']) == 13
assert all(type(v) is int and v == (120 if k == 'test_current_authority.py' else 63) for k,v in CLOCKS.items())
admission = load(READ_ADMISSION)
assert set(admission) == {'schema','actor','scope','operands','sourceFreeze','physicalReadsAuthorized','modelExecutionAuthorized','helperRuntimeAuthorized'}
assert admission['schema'] == 'e02-root-consumer-historical-negative-model-read-admission-v1'
assert admission['actor'] == '/root' and admission['scope'] == 'TWO_EXACT_HISTORICAL_NEGATIVE_MODEL_OPERANDS_ONLY'
assert admission['physicalReadsAuthorized'] is True and admission['modelExecutionAuthorized'] is False and admission['helperRuntimeAuthorized'] is False
assert admission['sourceFreeze'] == pin(REVIEW / 'complete-freeze.json')
assert len(admission['operands']) == 2
ALLOWED_OLD = {p['path']:p for p in admission['operands']}
assert admission['operands'] == load(REVIEW / 'complete-freeze.json')['opaqueExpectedInputs']
DENIED_CURRENT = {
 '786ffa958ed73a04b36537969973522b15867aa5051cfa8127cf533d84deb84b',
 '3712e08db8d52c813a1e6ba6c7fe151e97fe3284fb36c00c8c1c0d79ef036a38',
 '938124c7f4d4da4f8a84a98e6f1eeb756024f720e2908bf9d37ea05a0263aa02',
 'ab29043bb9c535b5e1ccd95b8625834043a3064bb86b2a1c1fc0b3c8f20674b7',
 '6ef4c69d724875277e4b11127f923f327dcc3864a2beac434619cef656529efa',
 '26c46563fbbe53107a25ed7177862a07c4ff5f289476e146bcdba525a2d1ec2e',
 'ca1817971cd4188a6caacc700d54df3351056da7a09a8d56bea918912fc60de9'}

mode = sys.argv[1]
if mode == 'prepare':
    assert not OUT.exists(); OUT.mkdir(parents=True)
    freeze_pin = pin(REVIEW / 'complete-freeze.json'); freeze = doc(freeze_pin)
    assert freeze_pin['sha256'] == 'e715cff2da70388b7ec37ea50020ad10fab4d1869dcd51a30670d71ca1233eb4'
    source_pin = freeze['subject']; source = doc(source_pin); plan = doc(source['controlPlan'])
    N = plan['modelsDefined']
    assert type(N) is int and N == source['modelDefinitions'] == sum(g['count'] for g in plan['groups'])
    assert [g['name'] for g in plan['groups']] == list(CLOCKS)
    assert source['sourceCount'] == 37 and source['runtimeSourceCount'] == 16
    assert source['modelsDefined'] == {g['name']:g['count'] for g in plan['groups']}
    receipt_pin = pin(REVIEW / 'acceptance.json'); receipt = doc(receipt_pin)
    contract = load(SOURCE / 'contracts/current-consumer-acceptance-contract.json')['source']
    assert set(receipt) == set(contract['closedKeys'])
    for k, v in contract['literals'].items(): assert type(receipt[k]) is type(v) and receipt[k] == v
    assert receipt['subject'] == source_pin and receipt['modelsDefined'] == N
    assert len(receipt['reviews']) == 2
    for role, p in zip(('qa', 'security'), receipt['reviews']):
        review = doc(p); assert set(review) == {'role', 'session', 'decision', 'subject'}
        assert review['role'] == role and review['subject'] == source_pin and review['decision'] == contract['reviewDecision']
        assert review['session'] not in freeze['reviewerExclusions']
    requests = [write(OUT / f'{i:02d}-exact-request.json', request(g)) for i, g in enumerate(plan['groups'], 1)]
    protected = {p['path']: p for p in [*freeze['inputs'], freeze_pin, receipt_pin, *receipt['reviews'], *requests, pin(__file__), pin(READ_ADMISSION), pin(CLOCK_SELECTION), *freeze['opaqueExpectedInputs']]}
    protected = [protected[k] for k in sorted(protected)]
    before = write(OUT / 'before.json', snapshot(protected))
    job = write(OUT / 'job.json', dict(schema='e02-root-consumer450-model-job-v1', actor='/root',
        consumerSource=source_pin, consumerSourceAcceptance=receipt_pin, controlPlan=source['controlPlan'],
        completeFreeze=freeze_pin, inputsBefore=before, protectedInputs=protected, requests=requests,
        countsSeparate=[g['count'] for g in plan['groups']], modelsDefined=N, modelsExecuted=0,
        scope='API_ONLY_MOCK_OR_READ_ONLY_MODELS_NO_TARGET_RUNTIME', executionAuthorized=False))
    print(json.dumps({'job': job, 'protectedInputs': len(protected), 'groups': len(requests)}))
elif mode == 'release':
    job_pin = pin(OUT / 'job.json'); job = doc(job_pin)
    N = job['modelsDefined']
    assert snapshot(job['protectedInputs']) == doc(job['inputsBefore'])
    release = dict(schema='e02-root-consumer6-current-model-release-v1', actor='/root',
        issuedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(), startAllowanceSeconds=120,
        job=job_pin, consumerSource=job['consumerSource'], consumerSourceAcceptance=job['consumerSourceAcceptance'],
        controlPlan=job['controlPlan'], inputsBefore=job['inputsBefore'], requests=job['requests'],
        modelsDefined=N, countsSeparate=job['countsSeparate'], maximumExecutionsPerGroup=1,
        groupsSequential=True, stopOnFirstFailure=True, noRetry=True, oldGrantReuseAuthorized=False,
        historicalResultTransferred=False, outerKillSecondsByName=CLOCKS, controlClockSelection=pin(CLOCK_SELECTION),
        scope=job['scope'], innerPidReapEofAttested=False, helperExecutionsAuthorized=0,
        dockerExecutionsAuthorized=0, ordinaryRoleExecutionsAuthorized=0, executionAuthorized=True)
    print(json.dumps({'release': write(OUT / 'root-release.json', release)}))
elif mode == 'finalize':
    job = load(OUT / 'job.json'); source = doc(job['consumerSource']); plan = doc(job['controlPlan'])
    N = job['modelsDefined']
    after_value = snapshot(job['protectedInputs']); assert after_value == doc(job['inputsBefore'])
    after = write(OUT / 'after.json', after_value); groups = []; origins = []
    for i, g in enumerate(plan['groups'], 1):
        expected = doc(job['requests'][i - 1]); assert expected == request(g)
        origin_pin = pin(OUT / f'{i:02d}-original-tool-origin.json'); raw = origin_output(doc(origin_pin), expected)
        text = raw.decode('utf8', 'strict')
        trailer = re.search(r'\n\n-{70}\nRan ([0-9]+) tests? in [0-9]+(?:\.[0-9]+)?s\n\nOK\n\Z', text)
        assert trailer and int(trailer[1]) == g['count'], g['name']
        names = []
        for line in text[:trailer.start()].splitlines():
            m = re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*) \(__main__\.([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_][A-Za-z_0-9]*)\) \.\.\. ok', line)
            assert m and m[1] == m[3], line; names.append(m[2] + '.' + m[3])
        assert names == sorted(g['definitionNames'])
        output_path = OUT / f'{i:02d}-raw-output.txt'; assert not output_path.exists(); output_path.write_bytes(raw)
        groups.append(dict(name=g['name'], source=g['source'], count=g['count'], definitionNames=g['definitionNames'],
            request=expected, originalToolOrigin=origin_pin, rawOutput=pin(output_path), exitCode=0,
            scope=job['scope'], innerPidReapEofAttested=False))
        origins.append(dict(group=g['name'], origin=origin_pin))
    execution = write(OUT / 'execution.json', dict(schema='e02-consumer6-control-execution-v1',
        consumerSource=job['consumerSource'], controlPlan=job['controlPlan'], groups=groups,
        countsSeparate=job['countsSeparate'], modelsExecuted=N, modelsPassed=N, modelsFailed=0,
        skipped=0, truncated=False, inputsBefore=job['inputsBefore'], inputsAfter=after,
        inputsUnchanged=True, scope=job['scope'], innerPidReapEofAttested=False))
    index = write(OUT / 'api-index.json', dict(schema='e02-consumer6-control-api-index-v1', origins=origins))
    raw_files = [pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
    manifest = write(OUT / 'raw-artifact-manifest.json', dict(schema='e02-consumer6-control-raw-manifest-v1', files=raw_files, originalToolOrigin=index))
    subject = dict(schema='e02-consumer6-current-control-data-subject-v1', authors=['/root'], operators=['/root'],
        consumerSource=job['consumerSource'], consumerSourceAcceptance=job['consumerSourceAcceptance'],
        controlPlan=job['controlPlan'], producerSource=source['producerSource'], producerControlAcceptance=source['producerControlAcceptance'],
        execution=execution, originalToolOrigin=index, rawArtifactManifest=manifest,
        countsSeparate=job['countsSeparate'], modelsDefined=N, modelsExecuted=N, modelsPassed=N,
        modelsFailed=0, skipped=0, truncated=False, inputsUnchanged=True, helperExecutions=0,
        dockerExecutions=0, ordinaryRoleExecutions=0, ordinaryRowsQualified=0)
    assert set(subject) == set(load(SOURCE / 'contracts/frozen-closed-contracts.json')['dataSubjectClosedKeys'])
    print(json.dumps({'subject': write(OUT / 'subject.json', subject), 'modelsPassed': N,
                      'protectedInputsUnchanged': len(job['protectedInputs'])}))
else:
    raise ValueError('Unknown mode')
