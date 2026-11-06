"""Pure temporary-files and read-only authority refusals; no final freeze."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_coupled as builder


class CoupledPreparationControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='nbdp-coupled-preparation-model-')
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, body=b'example\n'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        path.chmod(0o600)
        return builder.descriptor(path, body)

    def test_exact_pin_and_unchanged_recheck(self):
        pin = self.write('source')
        reader = builder.Reader()
        self.assertEqual(reader.read(pin['path'], pin)[1], b'example\n')
        reader.recheck()

    def test_wrong_hash_refuses_actual_bytes(self):
        pin = self.write('source')
        pin['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'EXACT_EXPECTED_INPUT_PIN'):
            builder.Reader().read(pin['path'], pin)

    def test_mode_is_checked_on_actual_source(self):
        pin = self.write('source')
        with self.assertRaisesRegex(ValueError, 'EXACT_SOURCE_MODE'):
            builder.Reader().read(pin['path'], pin, 0o664)

    def test_same_bytes_path_replacement_refuses_recheck(self):
        pin = self.write('source')
        reader = builder.Reader()
        reader.read(pin['path'], pin)
        replacement = self.root / 'replacement'
        replacement.write_bytes(b'example\n')
        os.replace(replacement, pin['path'])
        with self.assertRaisesRegex(ValueError, 'FINAL_SOURCE_INPUT_IDENTITY'):
            reader.recheck()

    def test_symlink_parent_refused_before_target_read(self):
        real = self.root / 'real'
        real.mkdir()
        (real / 'source').write_bytes(b'x')
        (self.root / 'alias').symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'NO_SYMLINK_READ_ALIAS'):
            builder.Reader().read(self.root / 'alias/source', dict(path=str(self.root / 'alias/source'), bytes=1, sha256=hashlib.sha256(b'x').hexdigest()))

    def test_fifo_refused_before_open(self):
        fifo = self.root / 'fifo'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'BOUNDED_REGULAR_SOURCE_OR_METADATA'):
            builder.Reader().read(fifo, dict(path=str(fifo), bytes=0, sha256=hashlib.sha256(b'').hexdigest()))

    def test_duplicate_json_keys_refused(self):
        pin = self.write('metadata', b'{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_METADATA_KEY'):
            builder.Reader().doc(pin)

    def test_metadata_float_and_nonfinite_refused(self):
        for index, body in enumerate((b'{"x":0.5}', b'{"x":NaN}', b'{"x":Infinity}')):
            pin = self.write('metadata-' + str(index), body)
            with self.assertRaisesRegex(ValueError, 'INTEGER_ONLY_SOURCE_METADATA'):
                builder.Reader().doc(pin)

    def test_operational_body_path_refused_before_stat(self):
        missing = self.root / 'probe-root-custody-actual/never-real/S18.json'
        with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_BODY_FORBIDDEN'):
            builder.Reader().read(missing)

    def test_root24_children_remain_opaque_descriptors(self):
        child = dict(path=str(self.root / 'probe-root-custody-actual/never-real/S18.json'),
                     bytes=1, sha256='a' * 64)
        pin = self.write('root24.json', json.dumps(dict(actor='/root', subject=child,
                        rootRelease=child, reviews=[])).encode())
        reader = builder.Reader()
        closure = builder.Closure(reader)
        doc = closure.doc(pin, 'originalHelper/Root24', 'GOVERNANCE')
        closure.pair(doc, 'originalHelper/Root24')
        self.assertEqual(set(reader.observed), {pin['path']})
        self.assertFalse(Path(child['path']).exists())

    def test_manifest_cannot_smuggle_operational_helper_body(self):
        child = dict(path=str(self.root / 'producer4-helper-probe-actual-forbidden/S18.json'),
                     bytes=1, sha256='a' * 64)
        pin = self.write('manifest.json', json.dumps(dict(files=[child])).encode())
        closure = builder.Closure(builder.Reader())
        with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_BODY_FORBIDDEN'):
            closure.manifest(pin, 'pureControls/raw')

    def test_exact_opaque_expected_pin_is_preserved_without_stat_or_body_read(self):
        pin = dict(path=str(self.root / 'producer4-helper-probe-actual-old-negative/absent.raw'),
                   bytes=3, sha256='a' * 64)
        reader = builder.Reader()
        closure = builder.Closure(reader)
        closure.opaque = {pin['path']: pin}
        closure.add(pin, 'baseline/explicitOldNegative')
        self.assertEqual(closure.rows[pin['path']], pin)
        self.assertEqual(reader.observed, {})
        self.assertEqual(closure.uses[pin['path']][0]['kind'], 'HISTORICAL_NEGATIVE_OPERATIONAL_OPAQUE')
        self.assertFalse(closure.uses[pin['path']][0]['physicalReadDuringSource'])
        self.assertFalse(Path(pin['path']).exists())

    def test_opaque_exception_cannot_widen_to_substituted_hash_or_other_body(self):
        pin = dict(path=str(self.root / 'producer4-helper-probe-actual-old-negative/absent.raw'),
                   bytes=3, sha256='a' * 64)
        reader = builder.Reader()
        closure = builder.Closure(reader)
        closure.opaque = {pin['path']: pin}
        changed = dict(pin, sha256='b' * 64)
        with self.assertRaisesRegex(ValueError, 'EXACT_ROOT_OPAQUE_HISTORICAL_NEGATIVE_PIN'):
            closure.add(changed, 'baseline/substituted')
        other = dict(pin, path=str(self.root / 'producer4-helper-probe-actual-other/absent.raw'))
        with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_BODY_FORBIDDEN'):
            closure.add(other, 'baseline/notAdmitted')
        self.assertEqual(reader.observed, {})

    def test_only_two_diagnosed_request_fixture_methods_change(self):
        source = builder.PREDECESSOR / 'source/test_request_families.py'
        before = source.read_bytes()
        after = builder.adapt_request_fixture(before)
        old, new = builder.methods(before), builder.methods(after)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({name for name in old if old[name] != new[name]}, {
            'CurrentRequestFamilyModels.test_current_accepted_r10_178_model_data_is_consumed_without_activation',
            'CurrentRequestFamilyModels.test_actual_current_producer_reader_binds_ab6_native4ce_and_fresh_e01'})
        self.assertIn(b'consumer.HELPER_PRODUCER, consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT', after)
        self.assertIn(b"'FIXTURE_EOSE_QUEUE_CALLER_R1'", after)

    def test_static_runtime_graph_is_derived_without_importing_readers(self):
        source = builder.PREDECESSOR / 'source'
        values = builder.assignments((source / 'consumer.py').read_bytes())
        code = sorted((*values['RUNTIME_FILES'], *values['CONTROL_FILES'], *builder.EXTRAS))
        bodies = {name: (source / name).read_bytes() for name in code}
        graph, contracts = builder.static_import_closure(bodies, values['RUNTIME_FILES'])
        self.assertEqual(graph['runtimeCount'], 16)
        self.assertEqual(graph['runtime'], graph['consumerReachable'])
        self.assertEqual(set(graph['graph']['capture_outputs']), {'capture_contracts', 'strict'})
        self.assertEqual(set(graph['graph']['ordinary_capture_outputs']), {'ordinary_capture_contracts', 'strict'})
        self.assertTrue(contracts)
        self.assertNotIn('consumer', sys.modules)

    def test_unknown_import_is_not_widened_to_ambient_dependency(self):
        source = builder.PREDECESSOR / 'source'
        values = builder.assignments((source / 'consumer.py').read_bytes())
        code = sorted((*values['RUNTIME_FILES'], *values['CONTROL_FILES'], *builder.EXTRAS))
        bodies = {name: (source / name).read_bytes() for name in code}
        bodies['capture_outputs.py'] += b'\nimport invented_ambient_dependency\n'
        with self.assertRaisesRegex(ValueError, 'NO_AMBIENT_IMPORT'):
            builder.static_import_closure(bodies, values['RUNTIME_FILES'])

    def test_missing_final_selector_refuses_before_any_output(self):
        scope_raw = builder.SCOPE.read_bytes()
        entry = builder.PREDECESSOR / 'entrypoint.UNBOUND.json'
        spec = {key: None for key in builder.SPEC_KEYS}
        spec.update(schema='e02-root-consumer-coupled-source3-spec-v1', actor='/root',
            rootScope=builder.descriptor(builder.SCOPE, scope_raw),
            predecessor=builder.descriptor(entry, entry.read_bytes()))
        spec_pin = self.write('missing-spec.json', json.dumps(spec).encode())
        output = builder.OWNED / 'MUST-NOT-BE-CREATED-BY-MISSING-SPEC'
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, 'MANDATORY_GENUINE_FINAL_SELECTOR'):
            builder.build(spec_pin, output)
        self.assertFalse(output.exists())

    def test_all_seven_renamed_operational_hashes_refuse_before_stat_or_open(self):
        reader = builder.Reader()
        with mock.patch.object(Path, 'lstat', side_effect=AssertionError('STAT_BEFORE_DENIAL')) as stats, \
             mock.patch.object(builder.os, 'open', side_effect=AssertionError('OPEN_BEFORE_DENIAL')) as opens:
            for index, sha in enumerate(sorted(builder.DENIED_OPERATIONAL_HASHES)):
                path = self.root / ('renamed-' + str(index) + '.json')
                pin = dict(path=str(path), bytes=1, sha256=sha)
                with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_HASH_FORBIDDEN_BEFORE_READ'):
                    reader.read(path, pin)
            self.assertEqual(stats.call_count, 0)
            self.assertEqual(opens.call_count, 0)

    def test_poisoned_last_capability_refuses_whole_list_before_any_reads(self):
        reader = builder.Reader(require_pre_admission=True)
        safe = dict(path=str(self.root / 'safe.json'), bytes=1, sha256='a' * 64)
        bad = dict(path=str(self.root / 'renamed-last.json'), bytes=1,
                   sha256=next(iter(builder.DENIED_OPERATIONAL_HASHES)))
        with mock.patch.object(Path, 'lstat', side_effect=AssertionError('STAT_BEFORE_FULL_ADMISSION')), \
             mock.patch.object(builder.os, 'open', side_effect=AssertionError('OPEN_BEFORE_FULL_ADMISSION')):
            with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_HASH_FORBIDDEN_BEFORE_READ'):
                reader.admit([safe, bad])
        self.assertEqual(reader.capabilities, {})
        self.assertEqual(reader.observed, {})

    def test_expected_pin_without_full_preadmission_cannot_open(self):
        reader = builder.Reader(require_pre_admission=True)
        pin = dict(path=str(self.root / 'not-admitted.json'), bytes=1, sha256='a' * 64)
        with mock.patch.object(Path, 'lstat', side_effect=AssertionError('STAT_BEFORE_ADMISSION')), \
             mock.patch.object(builder.os, 'open', side_effect=AssertionError('OPEN_BEFORE_ADMISSION')):
            with self.assertRaisesRegex(ValueError, 'SOURCE_INPUT_NOT_PREADMITTED'):
                reader.read(pin['path'], pin)

    def test_renamed_operational_spec_refuses_before_any_bootstrap_or_read(self):
        pin = dict(path=str(self.root / 'renamed-spec.json'), bytes=1,
                   sha256=next(iter(builder.DENIED_OPERATIONAL_HASHES)))
        output = builder.OWNED / 'MUST-NOT-BE-CREATED-BY-OPERATIONAL-SPEC'
        with mock.patch.object(Path, 'lstat', side_effect=AssertionError('STAT_BEFORE_SPEC_DENIAL')), \
             mock.patch.object(builder.os, 'open', side_effect=AssertionError('OPEN_BEFORE_SPEC_DENIAL')):
            with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_HASH_FORBIDDEN_BEFORE_READ'):
                builder.build(pin, output)

    def test_root_opaque_expected_rows_never_become_physical_capabilities(self):
        reader = builder.Reader(require_pre_admission=True)
        pins = list(builder.OPAQUE_EXPECTED_FROM_ROOT.values())
        reader.admit(pins)
        self.assertEqual(reader.capabilities, {})
        with mock.patch.object(Path, 'lstat', side_effect=AssertionError('STAT_OF_OPAQUE_BODY')), \
             mock.patch.object(builder.os, 'open', side_effect=AssertionError('OPEN_OF_OPAQUE_BODY')):
            for pin in pins:
                with self.assertRaisesRegex(ValueError, 'OPERATIONAL_HELPER_BODY_FORBIDDEN'):
                    reader.read(pin['path'], pin)


if __name__ == '__main__':
    unittest.main()
