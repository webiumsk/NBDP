"""Freeze an actually built consumer packet for independent Source review.

Only the finite readmap and files inside its newly created packet are selected.
The two historical negative descriptors stay expected-only at this Source gate.
This does not execute consumer models or accept the Source.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = HERE.parent
PACKET = FAMILY / 'source3/coupled-r1'
REVIEW = FAMILY / 'review-coupled-r1'


def pin(path):
    path = Path(path)
    assert path.is_absolute() and path.is_file() and not path.is_symlink()
    body = path.read_bytes()
    return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def doc(value):
    assert pin(value['path']) == value
    return json.loads(Path(value['path']).read_text())


def main():
    entry_pin = json.loads((HERE / 'builder.stdout.json').read_text())
    assert entry_pin['path'] == str(PACKET / 'entrypoint.COUPLED.json')
    entry = doc(entry_pin)
    source = doc(entry['subject'])
    plan = doc(source['controlPlan'])
    readmap = doc(entry['readMap'])
    manifest = doc(source['inputManifest'])
    concrete = json.loads((HERE / 'concrete-plan.UNRELEASED.json').read_text())
    execution = json.loads((HERE / 'execution.json').read_text())
    assert execution['exitCode'] == 0 and execution['plan'] == pin(HERE / 'concrete-plan.UNRELEASED.json')
    assert entry['rootSpec'] == concrete['spec']
    assert source['sourceCount'] == len(source['sources']) == 37
    assert source['runtimeSourceCount'] == len(source['runtimeSources']) == 16
    counts = [g['count'] for g in plan['groups']]
    assert len(counts) == source['modelGroups'] == 13
    assert sum(counts) == plan['modelsDefined'] == source['modelDefinitions'] == 450
    assert source['modelsDefined'] == {g['name']: g['count'] for g in plan['groups']}
    assert source['modelsExecuted'] == plan['modelsExecuted'] == 0
    opaque = manifest['opaqueHistoricalNegativeOperands']
    assert len(opaque) == 2
    opaque_by_path = {p['path']: p for p in opaque}
    selected = {}

    def add(value):
        assert set(value) == {'path', 'bytes', 'sha256'}
        old = selected.get(value['path'])
        assert old is None or old == value
        if opaque_by_path.get(value['path']) == value:
            return
        assert '/producer4-helper-probe-actual-' not in value['path']
        assert '65d8116b77bc0af1a108122ec28cfcea' not in value['path']
        assert pin(value['path']) == value
        selected[value['path']] = value

    for row in readmap['rows']:
        add(row['pin'])
    packet_files = []
    for path in sorted(PACKET.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            value = pin(path)
            add(value)
            packet_files.append(value)
    for path in ('concrete-plan.UNRELEASED.json', 'execution.json', 'actual-tool-origin.json',
                 'root-release.json', 'builder.stdout.json', 'builder.stderr.raw'):
        add(pin(HERE / path))
    add(pin(__file__))
    exclusions = sorted(set(source['sourceContributors']) | {source['author'], source['coordinator'],
                         source['predecessorAuthor'], '/root'})
    assert len(exclusions) == 75
    value = dict(schema='e02-root-coupled-consumer-source-complete-freeze-v1', actor='/root',
        subject=entry['subject'], entrypoint=entry_pin, controlPlan=source['controlPlan'],
        archive=entry['archive'], readMap=entry['readMap'], preservation=entry['preservation'],
        inputs=[selected[p] for p in sorted(selected)], packetFiles=packet_files,
        opaqueExpectedInputs=opaque, sourceContributors=source['sourceContributors'],
        reviewerExclusions=exclusions, codeMembers=37, runtimeMembers=16,
        countsSeparate=counts, modelsDefined=sum(counts), modelsExecuted=0,
        actualSourceBuild=pin(HERE / 'execution.json'), executionAuthorized=False,
        meaning='Actual finite Source-only build; independent final SOURCE review required. '
                'Two historical negative bodies remain unread until separately admitted canonical models. '
                'No helper/ordinary/runtime or DATA acceptance.')
    REVIEW.mkdir(exist_ok=True)
    output = REVIEW / 'complete-freeze.json'
    with output.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
    print(json.dumps(dict(freeze=pin(output), subject=entry['subject'],
        physicalInputs=len(selected), packetFiles=len(packet_files), opaqueExpectedOnly=2,
        modelsDefined=sum(counts), canonicalModelsExecuted=0)))


if __name__ == '__main__':
    main()
