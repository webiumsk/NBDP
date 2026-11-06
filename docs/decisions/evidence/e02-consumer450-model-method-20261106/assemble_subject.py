"""Recover only the missing subject from the successful, frozen450 execution.

The original assembler stopped after writing unchanged-input evidence, all raw
outputs, execution, index and manifest. Its obsolete contract alias is replaced
by the actual Source-pinned production CONTROL_DATA_KEYS literal. No model,
snapshot, raw output or existing manifest is rerun or overwritten.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence')
OUT = ROOT / 'e02-consumer450-model-actual-20261106/r1'
OWN_F_SHA = 'ca1817971cd4188a6caacc700d54df3351056da7a09a8d56bea918912fc60de9'
DENIED_BODIES = {
    OWN_F_SHA,
    '786ffa958ed73a04b36537969973522b15867aa5051cfa8127cf533d84deb84b',
    '3712e08db8d52c813a1e6ba6c7fe151e97fe3284fb36c00c8c1c0d79ef036a38',
    '938124c7f4d4da4f8a84a98e6f1eeb756024f720e2908bf9d37ea05a0263aa02',
    'ab29043bb9c535b5e1ccd95b8625834043a3064bb86b2a1c1fc0b3c8f20674b7',
    '6ef4c69d724875277e4b11127f923f327dcc3864a2beac434619cef656529efa',
    '26c46563fbbe53107a25ed7177862a07c4ff5f289476e146bcdba525a2d1ec2e',
    'a1dea229914c3b1baeac31a66d963958583c7d3780dfa6822553d355bc0d90f8',
    '255e940d083dfdaf013b30af3f4387adea611d84765c513b34492660bcd87218'}


def pin(path):
    path = Path(path)
    assert path.is_absolute() and path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(value):
    assert type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
    assert value['sha256'] not in DENIED_BODIES
    assert '65d8116b77bc0af1a108122ec28cfcea' not in value['path']
    assert '/producer4-helper-probe-actual-' not in value['path']
    assert pin(value['path']) == value
    return value


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            assert key not in result
            result[key] = value
        return result
    def no_number(value):
        raise ValueError('Subject metadata contains a noninteger number: ' + value)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs,
                      parse_float=no_number, parse_constant=no_number)


def doc(value):
    return load(checked(value)['path'])


def main():
    job_pin = pin(OUT / 'job.json')
    assert job_pin['sha256'] == '78c62c47cc0895884fe1335dc4b7423b770c69295a3784605a15234332926222'
    job = doc(job_pin)
    source = doc(job['consumerSource'])
    acceptance = doc(job['consumerSourceAcceptance'])
    assert acceptance['subject'] == job['consumerSource']
    assert acceptance['decision'] == 'ACCEPT_CURRENT_CONSUMER6_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'
    plan = doc(job['controlPlan'])
    count = plan['modelsDefined']
    assert type(count) is int and count == source['modelDefinitions'] == job['modelsDefined']
    assert count == sum(group['count'] for group in plan['groups'])
    execution_pin = pin(OUT / 'execution.json')
    execution = doc(execution_pin)
    assert execution['consumerSource'] == job['consumerSource']
    assert execution['controlPlan'] == job['controlPlan']
    for name in ('modelsExecuted', 'modelsPassed'):
        assert type(execution[name]) is int and execution[name] == count
    for name in ('modelsFailed', 'skipped'):
        assert type(execution[name]) is int and execution[name] == 0
    assert execution['inputsUnchanged'] is True and execution['truncated'] is False
    assert execution['innerPidReapEofAttested'] is False
    assert execution['countsSeparate'] == job['countsSeparate'] == [g['count'] for g in plan['groups']]
    assert len(execution['groups']) == len(plan['groups']) == 13
    assert doc(execution['inputsBefore']) == doc(execution['inputsAfter'])
    assert execution['inputsBefore'] == job['inputsBefore']
    assert len(doc(execution['inputsBefore'])['rows']) == len(job['protectedInputs']) == 1601
    manifest_pin = pin(OUT / 'raw-artifact-manifest.json')
    manifest = doc(manifest_pin)
    index_pin = pin(OUT / 'api-index.json')
    assert manifest['originalToolOrigin'] == index_pin
    paths = set()
    for value in manifest['files']:
        assert Path(value['path']).is_relative_to(OUT) and value['path'] not in paths
        assert value['path'] != manifest_pin['path']
        checked(value)
        paths.add(value['path'])
    assert all(value['path'] in paths for value in
               (execution_pin, index_pin, execution['inputsBefore'], execution['inputsAfter']))
    consumer_pin = next(value for value in source['sources'] if Path(value['path']).name == 'consumer.py')
    checked(consumer_pin)
    tree = ast.parse(Path(consumer_pin['path']).read_bytes())
    keys = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == 'CONTROL_DATA_KEYS']
    assert len(keys) == 1 and type(keys[0]) is str
    subject = dict(schema='e02-consumer6-current-control-data-subject-v1', authors=['/root'], operators=['/root'],
        consumerSource=job['consumerSource'], consumerSourceAcceptance=job['consumerSourceAcceptance'],
        controlPlan=job['controlPlan'], producerSource=source['producerSource'],
        producerControlAcceptance=source['producerControlAcceptance'], execution=execution_pin,
        originalToolOrigin=index_pin, rawArtifactManifest=manifest_pin, countsSeparate=job['countsSeparate'],
        modelsDefined=count, modelsExecuted=count, modelsPassed=count, modelsFailed=0, skipped=0,
        truncated=False, inputsUnchanged=True, helperExecutions=0, dockerExecutions=0,
        ordinaryRoleExecutions=0, ordinaryRowsQualified=0)
    assert set(subject) == set(keys[0].split()) and len(subject) == len(keys[0].split())
    path = OUT / 'subject.json'
    with path.open('x') as stream:
        json.dump(subject, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(subject=pin(path), modelsPassed=count, protectedInputsUnchanged=1601,
        actualModelGroupsRerun=0, existingEvidenceOverwritten=False)))


if __name__ == '__main__':
    main()
