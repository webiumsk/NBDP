"""Prepare a finite reviewed-evidence selection; do not copy, stage or publish.

Only repository evidence paths in the accepted consumer Source closure and
explicit current Source/Data review families are eligible. External runtime
operands, binary archives and unreviewed completion implementations stay out.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE = ROOT / 'docs/decisions/evidence'
HERE = Path(__file__).resolve().parent
CONSUMER = EVIDENCE / 'e02-consumer-eose-basis-successor-20261105'
METHOD = EVIDENCE / 'e02-consumer450-model-method-20261106'
DATA = EVIDENCE / 'e02-consumer450-model-actual-20261106/r1'
REVIEW = EVIDENCE / 'e02-consumer450-model-review-20261106/r1'
CHECKOUT = Path('/tmp/nbdp-review-20261104')
HEAD = 'f960554a5bc3a4789ae6f85c7f390c0ed912026e'
FORBIDDEN = {
    '786ffa958ed73a04b36537969973522b15867aa5051cfa8127cf533d84deb84b',
    '3712e08db8d52c813a1e6ba6c7fe151e97fe3284fb36c00c8c1c0d79ef036a38',
    '938124c7f4d4da4f8a84a98e6f1eeb756024f720e2908bf9d37ea05a0263aa02',
    'ab29043bb9c535b5e1ccd95b8625834043a3064bb86b2a1c1fc0b3c8f20674b7',
    '6ef4c69d724875277e4b11127f923f327dcc3864a2beac434619cef656529efa',
    '26c46563fbbe53107a25ed7177862a07c4ff5f289476e146bcdba525a2d1ec2e',
    'ca1817971cd4188a6caacc700d54df3351056da7a09a8d56bea918912fc60de9',
    'a1dea229914c3b1baeac31a66d963958583c7d3780dfa6822553d355bc0d90f8',
    '255e940d083dfdaf013b30af3f4387adea611d84765c513b34492660bcd87218'}


def descriptor(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def main():
    selected = {}
    omitted = {}
    external = []
    freeze = json.loads((CONSUMER / 'review-coupled-r1/complete-freeze.json').read_text())
    candidates = {p['path']: p for p in freeze['inputs']}
    for p in freeze['opaqueExpectedInputs']:
        external.append(dict(pin=p, reason='Historical operational expected-only operand; never publication input'))
    families = [CONSUMER, METHOD, DATA, REVIEW]
    for family in families:
        for path in sorted(family.rglob('*')):
            assert not path.is_symlink()
            if path.is_file():
                # These explicit families contain Source/pure-control evidence;
                # no operational helper-body family is traversed.
                raw = path.read_bytes()
                value = descriptor(path, raw)
                old = candidates.get(str(path))
                assert old is None or old == value, ('changed frozen input', path)
                candidates[str(path)] = value
    tree_raw = subprocess.check_output(['git', '-C', str(CHECKOUT), 'ls-tree', '-rz', '--full-tree', HEAD])
    old_tree = {}
    for row in tree_raw.split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            old_tree[name.decode()] = dict(mode=mode, kind=kind, oid=oid)
    for name in sorted(candidates):
        expected = candidates[name]
        assert expected['sha256'] not in FORBIDDEN, 'Protected identity not a publication capability'
        path = Path(name)
        if not path.is_relative_to(EVIDENCE):
            external.append(dict(pin=expected, reason='External runtime or non-evidence operand; descriptor only'))
            continue
        assert 'e02-completion-eose-successor-20261106' not in path.parts
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        assert descriptor(path, raw) == expected
        relative = str(path.relative_to(ROOT))
        try:
            text = raw.decode('utf8', 'strict')
            assert '\x00' not in text
        except (UnicodeError, AssertionError):
            omitted[relative] = dict(pin=expected, reason='Binary/non-UTF8 artifact; preserve exact descriptor, no whole-archive publication claim')
            continue
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        prior = old_tree.get(relative)
        selected[relative] = dict(pin=expected, relativePath=relative, gitMode='100644', gitBlob=blob,
            alreadyAtPublishedHead=prior is not None and prior['kind'] == 'blob' and prior['oid'] == blob and prior['mode'] == '100644')
    value = dict(schema='e02-root-current450-reviewed-evidence-publication-selection-v1', actor='/root',
        publishedBaseHead=HEAD, reviewCheckout=str(CHECKOUT),
        sourceAcceptance=descriptor(CONSUMER / 'review-coupled-r1/acceptance.json', (CONSUMER / 'review-coupled-r1/acceptance.json').read_bytes()),
        dataAcceptance=descriptor(REVIEW / 'acceptance.json', (REVIEW / 'acceptance.json').read_bytes()),
        selectedFiles=[selected[p] for p in sorted(selected)], omittedBinaries=[omitted[p] for p in sorted(omitted)],
        externalExpectedOperands=external, selectedFileCount=len(selected),
        changedFiles=sum(not row['alreadyAtPublishedHead'] for row in selected.values()),
        selectedBytes=sum(row['pin']['bytes'] for row in selected.values()),
        scope='Accepted current consumer450 Source/DATA and finite dependency evidence; preserves rejected historical Source as negative evidence only. No completion Source3 implementation, SDK, runtime binaries or operational helper payload publication.',
        portableRuntimeImageClaimed=False, actualIntegrationPromoted=False, publicationPerformed=False,
        independentPublicationReviewRequired=True, automaticMergeAuthorized=False)
    output = HERE / 'selection.UNREVIEWED.json'
    with output.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(selection=descriptor(output, output.read_bytes()), selected=len(selected),
        changed=value['changedFiles'], bytes=value['selectedBytes'], omittedBinaries=len(omitted),
        externalOperands=len(external), publicationPerformed=False)))


if __name__ == '__main__':
    main()
