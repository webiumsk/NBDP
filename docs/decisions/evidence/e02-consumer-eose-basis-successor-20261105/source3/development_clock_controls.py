"""Exercise only four new clock predicates on temporary Source-reader copies.

No final Source packet, helper proof, current binding or API request is issued.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_coupled as builder


def main():
    reader = builder.Reader()
    path = builder.OWNED.parent / 'root-consumer-control-clock-selection.json'
    pin, _ = reader.read(path)
    if pin['sha256'] != builder.CLOCK_SHA:
        raise ValueError('EXACT_ROOT_CLOCK_SELECTION')
    record = reader.doc(pin)
    source = builder.PREDECESSOR / 'source'
    body = (source / 'consumer.py').read_bytes()
    values = builder.assignments(body)
    with tempfile.TemporaryDirectory(prefix='nbdp-coupled-clock-predicates-') as temporary:
        root = Path(temporary)
        for name in values['RUNTIME_FILES']:
            content = (source / name).read_bytes()
            if name == 'consumer.py':
                content = builder.install_clock_source(content, pin, record, values['CONTROL_FILES'])
            (root / name).write_bytes(content)
        tests = root / 'test_source_bindings.py'
        tests.write_bytes(builder.add_clock_controls((source / tests.name).read_bytes()))
        sys.path.insert(0, str(root))
        spec = importlib.util.spec_from_file_location('clock_binding_predicates', tests)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        names = [
            'test_root_selected_authority_clock_is120_seconds_once',
            'test_other_twelve_pure_group_clocks_remain63_seconds',
            'test_clock_metadata_duplicates_omissions_substitution_and_authority_refused',
            'test_unknown_control_group_cannot_inherit_another_clock']
        suite = unittest.TestSuite(module.CurrentSourceBindings(name) for name in names)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        reader.recheck()
        if not result.wasSuccessful() or result.testsRun != 4:
            return 2
        print(json.dumps(dict(schema='e02-consumer-source2-clock-development-result-v1',
            checks=4, scope='TEMPORARY_READER_SOURCE_AND_PURE_REQUEST_PREDICATES_ONLY',
            actualToolRequests=0, canonicalModelsExecuted=0, finalFreezeIssued=False,
            operationalHelperBodiesRead=0, runtimeAuthorized=False)))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
