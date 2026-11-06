"""Exercise six new runtime failed-inventory predicates using memory fixtures.

Temporary reader Source only. No original outcomes, helper proofs, windows or
current runtime bindings are opened or executed by these tests.
"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_coupled as builder


def main():
    reader = builder.Reader()
    path = builder.OWNED.parent / 'root-required-failed-inventory-selection.json'
    pin, _ = reader.read(path)
    builder.need(pin['sha256'] == builder.FAILED_SHA, 'EXACT_ROOT_RUNTIME_FAILURE_SELECTION')
    policy = reader.doc(pin)
    source = builder.PREDECESSOR / 'source'
    body = (source / 'consumer.py').read_bytes()
    values = builder.assignments(body)
    with tempfile.TemporaryDirectory(prefix='nbdp-required-failed-inventory-predicates-') as temporary:
        root = Path(temporary)
        for name in values['RUNTIME_FILES']:
            content = (source / name).read_bytes()
            if name == 'consumer.py':
                content = builder.install_failed_inventory_source(content, pin, policy)
            (root / name).write_bytes(content)
        tests = root / 'test_data_controls.py'
        tests.write_bytes(builder.add_failed_inventory_controls((source / tests.name).read_bytes()))
        sys.path.insert(0, str(root))
        spec = importlib.util.spec_from_file_location('failed_inventory_predicates', tests)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.RequiredFailedInventoryControls)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        reader.recheck()
        builder.need(result.testsRun == 6 and result.wasSuccessful(), 'ALL_SIX_FAILED_INVENTORY_PREDICATES')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
