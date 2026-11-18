"""Snapshot unbound consumer CODE/definitions; never issue DATA or activation.

Canonical coupled Source requires genuine Root-supplied producer286/capture
DATA and the completed basis. This records an explicitly unbound snapshot and
refuses overwriting one. No project module or evidence payload is imported.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
AUTHOR = '/root/consumer_eose_basis_source'

def pin(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('SOURCE_REGULAR_FILE_REQUIRED')
    raw = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def literals():
    result = {}
    for node in ast.parse((SOURCE / 'consumer.py').read_bytes()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try: result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError): pass
    return result

def methods(raw):
    return [cls.name + '.' + method.name for cls in ast.parse(raw).body
            if isinstance(cls, ast.ClassDef) for method in cls.body
            if isinstance(method, ast.FunctionDef) and method.name.startswith('test_')]

def snapshot(output):
    output = Path(output)
    if not output.is_absolute() or not output.is_relative_to(ROOT) or output == SOURCE or output.exists():
        raise ValueError('FRESH_OWNED_SNAPSHOT_DIRECTORY_REQUIRED')
    values = literals(); runtime = values['RUNTIME_FILES']; controls = values['CONTROL_FILES']
    members, missing, groups = [], [], []
    for path in sorted(SOURCE.iterdir()):
        if path.is_symlink(): raise ValueError('NO_SOURCE_SYMLINK')
        if path.is_file() and path.suffix in ('.py', '.txt', '.md'):
            if path.suffix == '.py': ast.parse(path.read_bytes(), filename=str(path))
            members.append(dict(pin=pin(path), mode=stat.S_IMODE(path.stat().st_mode)))
    for name in runtime + controls:
        if not (SOURCE / name).is_file(): missing.append(name)
    for name in controls:
        path = SOURCE / name
        if path.is_file():
            names = methods(path.read_bytes())
            groups.append(dict(name=name, source=pin(path), count=len(names), definitionNames=names))
    value = dict(schema='e02-consumer-eose-unbound-code-snapshot-v1', author=AUTHOR,
        state='UNBOUND_CODE_AND_DEFINITIONS_ONLY', sourceRoot=str(SOURCE),
        runtimeFiles=list(runtime), controlFiles=list(controls), members=members,
        missingMembers=missing, groups=groups, modelsDefined=sum(g['count'] for g in groups),
        canonicalModelsExecuted=0, completedBasisIssued=False, finalSourceFreezeReady=False,
        runtimeBindingIssued=False, executionAuthorized=False)
    output.mkdir(); (output / 'snapshot.json').write_text(json.dumps(value, sort_keys=True, indent=2) + chr(10))
    return pin(output / 'snapshot.json')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unbound-output', required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot(args.unbound_output), sort_keys=True))

if __name__ == '__main__': main()
