"""Copy only the reviewed text allowlist to the isolated review checkout.

This prepares a reversible worktree; staging, independent tree review and any
publication remain separate. Current-document updates extend the published
history with a truthful checkpoint; the full local orchestration state is kept.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = Path(__file__).resolve().parent
DEST = Path('/tmp/nbdp-review-20261104')
HEAD = 'f960554a5bc3a4789ae6f85c7f390c0ed912026e'


def git(*args):
    return subprocess.check_output(['git', '-C', str(DEST), *args])


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def main():
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('status', '--porcelain') == b''
    selection_path = HERE / 'selection.UNREVIEWED.json'
    raw = selection_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '51706685f7451cddf79ebead89e44d484b4d239c73d9b59299aa1047819eea59'
    selection = json.loads(raw)
    expected = {}
    for row in selection['selectedFiles']:
        source = Path(row['pin']['path'])
        relative = row['relativePath']
        assert source == ROOT / relative and source.is_relative_to(ROOT / 'docs/decisions/evidence')
        raw = source.read_bytes()
        assert len(raw) == row['pin']['bytes'] and hashlib.sha256(raw).hexdigest() == row['pin']['sha256']
        assert blob(raw) == row['gitBlob']
        target = DEST / relative
        assert target.is_relative_to(DEST / 'docs/decisions/evidence')
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.is_symlink()
        target.write_bytes(raw)
        target.chmod(0o644)
        expected[relative] = dict(gitMode='100644', gitBlob=blob(raw), source='REVIEWED_SELECTION')
    controls = ['README.md', 'prepare_selection.py', 'selection.UNREVIEWED.json',
                'selection-reviews.json', 'prepare-selection-original-tool-origin.json', 'pr4-before.json',
                'prepare_review_tree.py']
    for name in controls:
        source = HERE / name
        relative = str(source.relative_to(ROOT))
        raw = source.read_bytes()
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o644)
        expected[relative] = dict(gitMode='100644', gitBlob=blob(raw), source='PUBLICATION_CONTROL_REQUIRES_STAGED_REVIEW')
    checkpoint = '''## Current accepted consumer checkpoint — 2026-11-06

Current consumer Source has independent QA/security and Root acceptance:37 Code files,16 runtime modules and450 definitions. One full fresh batch passed all450 named controls in13 groups with38 complete native API frames and byte-identical1601-input snapshots; paired actual DATA review and Root acceptance are complete. See the [evidence guide](decisions/evidence/e02-current450-publication-20261106/README.md), [current Source receipt](decisions/evidence/e02-consumer-eose-basis-successor-20261105/review-coupled-r1/acceptance.json) and [current DATA receipt](decisions/evidence/e02-consumer450-model-review-20261106/r1/acceptance.json).

Current admission42, ordinary-producer286 and the separate original helper266/R10 evidence are accepted. The completed helper component basis establishes Source equality/mode/import/environment declarations, not a new live helper observation. Accepted batches are not repeated or promoted to ordinary-client results.

E02 remains PARTIAL22: one qualified helper run, zero qualified ordinary windows and zero exports. Completion/wrapper correction remains under independent review and its active Source3 code is excluded. Its final Source/current models/graph, two genuine role windows, five exports, whole consumption, original primary22, independently reviewed candidate/finalize and final integration remain required. The publication is a text evidence checkpoint, not a portable execution environment. Q01/Q08/Q13/Q15/Q27, conditional Option B, baseline NIP-44 limits, parallel devices, Satflux independence and all SDK/deployment/merge restrictions remain unchanged.

The following older published checkpoints preserve history and are superseded where they describe pending prerequisites completed above.

'''
    for name in ('PROJECT_STATE.md', 'ROADMAP.md'):
        relative = 'docs/' + name
        base = git('show', HEAD + ':' + relative).decode()
        assert 'Updated 2026-10-29.' in base
        text = base.replace('Updated 2026-10-29.', 'Updated 2026-11-06.', 1)
        marker = '## Current recovery checkpoint' if name == 'PROJECT_STATE.md' else 'Current producer260 and controller104'
        position = text.index(marker)
        text = text[:position] + checkpoint + text[position:]
        raw = text.encode()
        (DEST / relative).write_bytes(raw)
        expected[relative] = dict(gitMode='100644', gitBlob=blob(raw), source='CURATED_PUBLISHED_HISTORY_CHECKPOINT_REQUIRES_STAGED_REVIEW')
    value = dict(schema='e02-root-current450-review-tree-allowlist-v1', actor='/root',
        baseHead=HEAD, checkout=str(DEST), selectionSha256=hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        files=[dict(path=path, **expected[path]) for path in sorted(expected)],
        expectedFiles=len(expected), selectedEvidenceFiles=len(selection['selectedFiles']),
        addedPublicationControls=len(controls), curatedCurrentDocuments=2,
        staged=False, publicationPerformed=False, independentStagedReviewRequired=True)
    path = HERE / 'review-tree-allowlist.json'
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    raw = path.read_bytes()
    print(json.dumps(dict(allowlist=dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
        expectedFiles=len(expected), selectedFiles=len(selection['selectedFiles']),
        controls=len(controls), currentDocuments=2, staged=False, publicationPerformed=False)))


if __name__ == '__main__':
    main()
