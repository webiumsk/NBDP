"""Prepared DATA definitions only: public scalar NIP19 formatting consistency.

No signing/encryption/curve operation, user key input, SDK, process or service.
"""
import ast
import json
from pathlib import Path
import unittest
HERE = Path(__file__).resolve().parent
REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
PREP = REPO / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2'
ABC = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'


def decode_public_nsec(value, scalar):
    if type(value) is not str or len(value) != 63 or not value.startswith('nsec1'):
        raise ValueError('Exact whole lowercase NIP19 nsec required')
    try:
        words = [ABC.index(c) for c in value[5:]]
    except ValueError:
        raise ValueError('Bech32 alphabet') from None
    checksum = 1
    for word in [3, 3, 3, 3, 0, 14, 19, 5, 3] + words:
        top, checksum = checksum >> 25, ((checksum & 0x1ffffff) << 5) ^ word
        for bit, generator in enumerate((0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)):
            if top & (1 << bit):
                checksum ^= generator
    if checksum != 1:
        raise ValueError('Bech32 checksum')
    value_bits = 0
    for word in words[:-6]:
        value_bits = (value_bits << 5) | word
    if value_bits & 15:
        raise ValueError('Nonzero Bech32 padding')
    payload = (value_bits >> 4).to_bytes(32, 'big')
    if scalar not in (1, 2) or payload != scalar.to_bytes(32, 'big'):
        raise ValueError('Fixed public scalar payload')
    return payload


class PublicIdentityMetadata(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((PREP / 'public-scalar-format-data.json').read_bytes())['values']

    def test_whole_checksum_payload_both_public_scalars(self):
        for scalar in (1, 2):
            value = self.data[str(scalar)]
            self.assertEqual(decode_public_nsec(value['nsec'], scalar).hex(), value['scalarHex'])

    def test_four_metadata_operands_equal_unchanged_driver(self):
        tree = ast.parse((HERE / 'android_driver.py').read_text())
        literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) is str}
        for path in [HERE / 'minimum-plan.json', HERE / 'fixture-plan.json', HERE / 'ui-plan.json', PREP / 'oracle-provenance.json']:
            roles = json.loads(path.read_bytes())['roles']
            for role, scalar in [('incoming', 2), ('archive', 1)]:
                operand = roles[role]['nsec']
                self.assertEqual(operand, self.data[str(scalar)]['nsec'])
                self.assertIn(operand, literals)
                decode_public_nsec(operand, scalar)

    def test_historical_65_character_operand_refused_preserved(self):
        old = json.loads((REPO / 'experiments/prototypes/e02_ordinary_minimum_v1/minimum-plan.json').read_bytes())['roles']['incoming']['nsec']
        self.assertEqual(len(old), 65)
        with self.assertRaisesRegex(ValueError, 'Exact whole'):
            decode_public_nsec(old, 2)

    def test_checksum_corruption_refused(self):
        value = self.data['2']['nsec']
        with self.assertRaisesRegex(ValueError, 'checksum'):
            decode_public_nsec(value[:-1] + ('q' if value[-1] != 'q' else 'p'), 2)

    def test_valid_other_payload_refused(self):
        with self.assertRaisesRegex(ValueError, 'payload'):
            decode_public_nsec(self.data['1']['nsec'], 2)

    def test_whitespace_case_truncation_never_normalized(self):
        value = self.data['2']['nsec']
        for wrong in [' ' + value, value.upper(), value[:-1], value + 'q', value.replace('nsec1', 'npub1')]:
            with self.assertRaises(ValueError):
                decode_public_nsec(wrong, 2)

    def test_non_bech32_glyph_refused(self):
        value = self.data['2']['nsec']
        with self.assertRaisesRegex(ValueError, 'alphabet'):
            decode_public_nsec(value[:8] + 'i' + value[9:], 2)

    def test_new_plan_keeps_scalar_roles_and_whole_value(self):
        plan = json.loads((HERE / 'minimum-plan.json').read_bytes())
        self.assertEqual(plan['profileId'], 'e02-ordinary-minimum-rs-two-role-v3')
        self.assertEqual(plan['roles']['incoming']['scalar'], 2)
        self.assertEqual(plan['roles']['archive']['scalar'], 1)
        self.assertEqual(plan['maximumRoleWindows'], 2)
        self.assertEqual(plan['perWindowOriginalLeaseSeconds'], 1800)
        self.assertFalse(plan['canonicalPass'])


if __name__ == '__main__':
    unittest.main()
