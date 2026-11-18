"""Pure local-filesystem expected-mode regressions; no operational inputs.

Every file used here is created in a TemporaryDirectory. Syscall interception
introduces deterministic metadata/path races without a helper or subprocess.
"""
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strict
from strict import DATA, FILE, Files, Refusal


class ExpectedModeReaderModels(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / 'source.bin'
        self.body = b'explicit synthetic source bytes\n'
        self.path.write_bytes(self.body)
        self.path.chmod(0o664)
        self.pin = self.descriptor(self.path)
        self.files = Files([str(self.root)])

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def descriptor(path):
        body = path.read_bytes()
        return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())

    def replacement(self, mode=0o664):
        other = self.root / 'replacement.bin'
        other.write_bytes(self.body)
        other.chmod(mode)
        os.replace(other, self.path)

    def intercept_stat(self, on_call):
        original = strict.os.fstat
        calls = [0]
        def observe(fd):
            value = original(fd)
            calls[0] += 1
            on_call(calls[0])
            return value
        return patch.object(strict.os, 'fstat', side_effect=observe)

    def test_exact_0664_and_full_recheck(self):
        self.assertEqual(self.files.read_mode(self.pin, 0o664), self.body)
        self.assertEqual(self.files.expected_modes[str(self.path)], 0o664)
        self.files.recheck()
        self.assertEqual(self.files.total, len(self.body))

    def test_keyword_mode_uses_same_bounded_reader(self):
        self.assertEqual(self.files.read(self.pin, expected_mode=0o664), self.body)
        self.assertEqual(self.files.read(self.pin), self.body)
        self.assertEqual(self.files.total, len(self.body))

    def test_default_reader_does_not_invent_expected_mode(self):
        self.path.chmod(0o600)
        self.assertEqual(self.files.read(self.pin), self.body)
        self.assertEqual(self.files.expected_modes, {})
        self.files.recheck()

    def test_wrong_actual_mode_refuses(self):
        self.path.chmod(0o644)
        with self.assertRaisesRegex(Refusal, 'EXPECTED_FILE_MODE'):
            self.files.read_mode(self.pin, 0o664)
        self.assertEqual(self.files.expected_modes, {})
        self.assertEqual(self.files.pins, {})

    def test_equal_declared_pair_does_not_mask_wrong_actual_modes(self):
        other = self.root / 'new-source.bin'
        other.write_bytes(self.body)
        for path in (self.path, other):
            path.chmod(0o644)
            declared = dict(pin=self.descriptor(path), expectedMode=0o664)
            with self.subTest(path=path.name), self.assertRaisesRegex(Refusal, 'EXPECTED_FILE_MODE'):
                Files([str(self.root)]).read_mode(declared['pin'], declared['expectedMode'])

    def test_mode_domain_rejects_bool_string_none_and_out_of_range(self):
        for mode in (True, False, '0o664', None, -1, 0o10000):
            with self.subTest(mode=mode), self.assertRaisesRegex(Refusal, 'INTEGER_DOMAIN'):
                self.files.read_mode(self.pin, mode)

    def test_keyword_mode_domain_refuses_non_integer(self):
        with self.assertRaisesRegex(Refusal, 'INTEGER_DOMAIN'):
            self.files.read(self.pin, expected_mode=True)

    def test_conflicting_expected_modes_refuse_before_new_open(self):
        self.files.read_mode(self.pin, 0o664)
        with patch.object(Files, '_open_file', side_effect=AssertionError('OPEN_AFTER_CONFLICT')):
            with self.assertRaisesRegex(Refusal, 'EXPECTED_MODE_CONFLICT'):
                self.files.read_mode(self.pin, 0o644)

    def test_later_chmod_refuses_default_read(self):
        self.files.read_mode(self.pin, 0o664)
        self.path.chmod(0o644)
        with self.assertRaisesRegex(Refusal, 'EXPECTED_FILE_MODE'):
            self.files.read(self.pin)

    def test_later_chmod_refuses_recheck(self):
        self.files.read_mode(self.pin, 0o664)
        self.path.chmod(0o600)
        with self.assertRaisesRegex(Refusal, 'EXPECTED_FILE_MODE'):
            self.files.recheck()

    def test_restored_mode_still_refuses_changed_identity(self):
        self.files.read_mode(self.pin, 0o664)
        self.path.chmod(0o644)
        self.path.chmod(0o664)
        with self.assertRaisesRegex(Refusal, 'EXPECTED_MODE_IDENTITY_DRIFT'):
            self.files.recheck()

    def test_same_bytes_new_inode_refuses_continuity(self):
        self.files.read_mode(self.pin, 0o664)
        self.replacement()
        with self.assertRaisesRegex(Refusal, 'EXPECTED_MODE_IDENTITY_DRIFT'):
            self.files.recheck()

    def test_mode_change_between_before_and_after_stat_refuses(self):
        with self.intercept_stat(lambda n: self.path.chmod(0o644) if n == 1 else None):
            with self.assertRaisesRegex(Refusal, 'HASH_IDENTITY_DRIFT'):
                self.files.read_mode(self.pin, 0o664)

    def test_same_content_path_replacement_during_read_refuses(self):
        with self.intercept_stat(lambda n: self.replacement() if n == 2 else None):
            with self.assertRaisesRegex(Refusal, 'HASH_IDENTITY_DRIFT'):
                self.files.read_mode(self.pin, 0o664)

    def test_mode_change_at_canonical_reopen_refuses(self):
        original = Files._open_file
        calls = [0]
        def observe(path):
            calls[0] += 1
            if calls[0] == 2:
                self.path.chmod(0o644)
            return original(path)
        with patch.object(Files, '_open_file', side_effect=observe):
            with self.assertRaisesRegex(Refusal, 'HASH_IDENTITY_DRIFT'):
                self.files.read_mode(self.pin, 0o664)

    def test_final_symlink_refuses(self):
        linked = self.root / 'linked.bin'
        linked.symlink_to(self.path)
        bad = dict(self.pin, path=str(linked))
        with self.assertRaises(OSError):
            self.files.read_mode(bad, 0o664)

    def test_ancestor_symlink_refuses(self):
        folder = self.root / 'real'
        folder.mkdir()
        target = folder / 'source.bin'
        target.write_bytes(self.body)
        target.chmod(0o664)
        link = self.root / 'alias'
        link.symlink_to(folder, target_is_directory=True)
        bad = dict(self.descriptor(target), path=str(link / target.name))
        with self.assertRaises(OSError):
            self.files.read_mode(bad, 0o664)

    def test_ancestor_replaced_with_symlink_during_read_refuses(self):
        folder = self.root / 'current'
        folder.mkdir()
        target = folder / 'source.bin'
        target.write_bytes(self.body)
        target.chmod(0o664)
        descriptor = self.descriptor(target)
        def mutate(n):
            if n == 2:
                old = self.root / 'old'
                folder.rename(old)
                folder.symlink_to(old, target_is_directory=True)
        with self.intercept_stat(mutate), self.assertRaises(OSError):
            self.files.read_mode(descriptor, 0o664)

    def test_raw_verification_preserves_constraint_and_recheck(self):
        self.files.read_mode(self.pin, 0o664)
        self.assertEqual(self.files.verify_raw(self.pin), len(self.body))
        self.assertEqual(self.files.expected_modes[str(self.path)], 0o664)
        self.files.recheck()
        self.path.chmod(0o644)
        with self.assertRaisesRegex(Refusal, 'EXPECTED_FILE_MODE'):
            self.files.verify_raw(self.pin)

    def test_raw_first_then_mode_constraint_is_retained(self):
        self.files.verify_raw(self.pin)
        self.files.read_mode(self.pin, 0o664)
        self.replacement()
        with self.assertRaisesRegex(Refusal, 'EXPECTED_MODE_IDENTITY_DRIFT'):
            self.files.recheck()

    def test_guest_alias_shares_exact_host_mode_constraint(self):
        guest = dict(self.pin, path='/input/synthetic-source')
        self.files.binding(guest, self.pin, str(self.root))
        self.assertEqual(self.files.read_mode(guest, 0o664), self.body)
        self.assertEqual(set(self.files.expected_modes), {str(self.path)})
        self.path.chmod(0o644)
        with self.assertRaisesRegex(Refusal, 'EXPECTED_FILE_MODE'):
            self.files.read(self.pin)

    def test_hash_and_size_checks_remain_mandatory(self):
        for descriptor in (dict(self.pin, sha256='a' * 64), dict(self.pin, bytes=self.pin['bytes'] + 1)):
            with self.subTest(descriptor=descriptor), self.assertRaises(Refusal):
                self.files.read_mode(descriptor, 0o664)

    def test_read_and_pin_caps_remain_unchanged(self):
        self.assertEqual((DATA, FILE), (16777216, 67108864))
        with self.assertRaisesRegex(Refusal, 'PIN_ADMISSION'):
            self.files.read_mode(self.pin, 0o664, maximum=1)
        with self.assertRaisesRegex(Refusal, 'INTEGER_DOMAIN'):
            self.files.read_mode(dict(self.pin, bytes=FILE + 1), 0o664, maximum=FILE + 1)


if __name__ == '__main__':
    unittest.main()
