"""Derive the current Root model metadata method from its accepted predecessor.

No model, selected proof, subprocess or runtime executes during this edit.
"""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'e02-consumer352-model-method-20261105/root_model.py'
body = OLD.read_text()


def change(before, after):
    global body
    assert body.count(before) == 1, before
    body = body.replace(before, after)


change("SOURCE = EV / 'e02-consumer-current178-source-20261105/source3'",
       "SOURCE = EV / 'e02-consumer-eose-basis-successor-20261105/source3/coupled-r1'")
change("REVIEW = EV / 'e02-consumer-current178-source-review-20261105/source3'",
       "REVIEW = EV / 'e02-consumer-eose-basis-successor-20261105/review-coupled-r1'")
change("OUT = EV / 'e02-consumer352-model-actual-20261105/r1'",
       "OUT = EV / 'e02-consumer450-model-actual-20261106/r1'\nMETHOD = EV / 'e02-consumer450-model-method-20261106'\nCLOCK_SELECTION = EV / 'e02-consumer-eose-basis-successor-20261105/root-consumer-control-clock-selection.json'\nREAD_ADMISSION = METHOD / 'root-readonly-operands.json'")
change("'63s', *group['argv']", "str(CLOCKS[group['name']]) + 's', *group['argv']")
change("assert freeze_pin['sha256'] == '3deb691bb467e5967dc3391be0fae2985bde16b95fbb167631805e672ad4aa67'",
       "assert freeze_pin['sha256'] == 'e715cff2da70388b7ec37ea50020ad10fab4d1869dcd51a30670d71ca1233eb4'")
change("source_pin = freeze['subject']; source = doc(source_pin); plan = doc(source['controlPlan'])",
       "source_pin = freeze['subject']; source = doc(source_pin); plan = doc(source['controlPlan'])\n    N = plan['modelsDefined']\n    assert type(N) is int and N == source['modelDefinitions'] == sum(g['count'] for g in plan['groups'])\n    assert [g['name'] for g in plan['groups']] == list(CLOCKS)\n    assert source['sourceCount'] == 37 and source['runtimeSourceCount'] == 16\n    assert source['modelsDefined'] == {g['name']:g['count'] for g in plan['groups']}")
change("receipt['modelsDefined'] == 352", "receipt['modelsDefined'] == N")
change("doc(source['currentConsumerAcceptanceContract'])['source']",
       "load(SOURCE / 'contracts/current-consumer-acceptance-contract.json')['source']")
change("*requests, pin(__file__)]", "*requests, pin(__file__), pin(READ_ADMISSION), pin(CLOCK_SELECTION), *freeze['opaqueExpectedInputs']]")
change("READ_ADMISSION = METHOD / 'root-readonly-operands.json'",
       "READ_ADMISSION = METHOD / 'root-readonly-operands.json'\nMODEL_TOOLS = [Path('/home/peterhorvath/.miniforge3/bin/python3.13'), Path('/usr/bin/env'), Path('/usr/bin/timeout')]")
change("p = Path(p); raw = p.read_bytes()",
       "p = Path(p)\n    info = p.lstat()\n    assert p.is_absolute() and stat.S_ISREG(info.st_mode) and info.st_size <= 67108864\n    raw = p.read_bytes()")
change("*freeze['opaqueExpectedInputs']]", "*freeze['opaqueExpectedInputs'], *[pin(p) for p in MODEL_TOOLS]]")
change("schema='e02-root-consumer352-model-job-v1'", "schema='e02-root-consumer450-model-job-v1'")
change("job_pin = pin(OUT / 'job.json'); job = doc(job_pin)",
       "job_pin = pin(OUT / 'job.json'); job = doc(job_pin)\n    N = job['modelsDefined']")
change("perGroupKillSeconds=63,", "outerKillSecondsByName=CLOCKS, controlClockSelection=pin(CLOCK_SELECTION),")
change("job = load(OUT / 'job.json'); source = doc(job['consumerSource']); plan = doc(job['controlPlan'])",
       "job = load(OUT / 'job.json'); source = doc(job['consumerSource']); plan = doc(job['controlPlan'])\n    N = job['modelsDefined']")
for field in ('modelsDefined', 'modelsExecuted', 'modelsPassed'):
    body = body.replace(field + '=352', field + '=N')
body = body.replace("'modelsPassed': 352", "'modelsPassed': N")
policy = '''# Source-selected fixed clocks and separately issued two-operand read admission.
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

'''
change('mode = sys.argv[1]\n', policy + 'mode = sys.argv[1]\n')
change("assert type(p['bytes']) is int and pin(p['path']) == p, p",
       "assert p['sha256'] not in DENIED_CURRENT, 'CURRENT_HELPER_IDENTITY_FORBIDDEN'\n    if p['sha256'] in {q['sha256'] for q in ALLOWED_OLD.values()} or '/producer4-helper-probe-actual-' in p['path']:\n        assert ALLOWED_OLD.get(p['path']) == p, 'EXACT_ADMITTED_HISTORICAL_MODEL_OPERAND_ONLY'\n    assert '65d8116b77bc0af1a108122ec28cfcea' not in p['path']\n    assert type(p['bytes']) is int and pin(p['path']) == p, p")
change('def origin_output(origin, expected):\n', '''def origin_output(origin, expected):
    def whole_request(value):
        assert type(value) is dict and set(value) == {'cmd', 'workdir', 'login', 'yield_time_ms', 'max_output_tokens'}
        assert type(value['cmd']) is str and value['cmd']
        assert type(value['workdir']) is str and Path(value['workdir']).is_absolute()
        assert type(value['login']) is bool and value['login'] is False
        assert type(value['yield_time_ms']) is int and value['yield_time_ms'] > 0
        assert type(value['max_output_tokens']) is int and value['max_output_tokens'] > 0
    whole_request(expected)
''')
change('        if i == 0:\n', '        if i == 0:\n            whole_request(a)\n')
change("    assert len(receipt['reviews']) == 2\n", "    assert len(receipt['reviews']) == 2\n    assert len({(p['path'], p['bytes'], p['sha256']) for p in receipt['reviews']}) == 2\n    source_review_sessions = []\n")
change("        assert review['session'] not in freeze['reviewerExclusions']\n", "        assert review['session'] not in freeze['reviewerExclusions']\n        assert type(review['session']) is str and review['session'].startswith('/root/') and len(review['session']) > len('/root/')\n        source_review_sessions.append(review['session'])\n    assert len(set(source_review_sessions)) == 2\n")
tree = ast.parse(body)
assert not any(isinstance(n, ast.Constant) and type(n.value) is int and n.value == 352 for n in ast.walk(tree))
with (HERE / 'root_model.py').open('x') as stream:
    stream.write(body)
print('Created syntax-valid unexecuted current model metadata method; final Source acceptance/read admission mandatory.')
