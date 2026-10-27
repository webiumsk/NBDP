"""PREPARED NOT EXECUTED: observed-byte-bound stable API37.0 parser models."""
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import acquire

EXPECTED_SHA = 'fa89029fc0cee414cb5e44a37cd3033771217eeecb5086577bb6d9b1b03b5b5f'


class ExactPlatformProperties(unittest.TestCase):
    def setUp(self):
        self.raw=(Path(__file__).parent/'actual-platform-source.properties').read_bytes()
        self.assertEqual(len(self.raw),343)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),EXPECTED_SHA)

    def change(self,key,value):
        lines=self.raw.decode().splitlines();matches=[i for i,v in enumerate(lines) if v.startswith(key+'=')]
        self.assertEqual(len(matches),1);lines[matches[0]]=key+'='+value
        return ('\n'.join(lines)+'\n').encode()

    def refuse(self,key,value):
        with self.assertRaises(ValueError):acquire.platform_properties(self.change(key,value))

    def test_observed_exact_stable37_0_positive(self):
        p=acquire.platform_properties(self.raw)
        self.assertEqual(p['AndroidVersion.ApiLevel'],'37.0')
        self.assertEqual(p['Pkg.Revision'],'2')
        self.assertEqual(p['Platform.Version'],'17')
    def test_wrong_major_refused(self):self.refuse('AndroidVersion.ApiLevel','36.0')
    def test_wrong_minor_refused(self):self.refuse('AndroidVersion.ApiLevel','37.1')
    def test_legacy_integer_api_refused(self):self.refuse('AndroidVersion.ApiLevel','37')
    def test_extra_component_refused(self):self.refuse('AndroidVersion.ApiLevel','37.0.0')
    def test_leading_zero_major_refused(self):self.refuse('AndroidVersion.ApiLevel','037.0')
    def test_leading_zero_minor_refused(self):self.refuse('AndroidVersion.ApiLevel','37.00')
    def test_exponent_api_refused(self):self.refuse('AndroidVersion.ApiLevel','3.7e1')
    def test_spaced_api_refused(self):self.refuse('AndroidVersion.ApiLevel',' 37.0')
    def test_future_or_preview_codename_refused(self):self.refuse('AndroidVersion.CodeName','Preview')
    def test_platform_codename_refused(self):self.refuse('Platform.CodeName','Preview')
    def test_preview_sdk_refused(self):self.refuse('AndroidVersion.PreviewSdkInt','1')
    def test_preview_format_refused(self):self.refuse('AndroidVersion.PreviewSdkInt','0.0')
    def test_wrong_revision_refused(self):self.refuse('Pkg.Revision','3')
    def test_revision_float_format_refused(self):self.refuse('Pkg.Revision','2.0')
    def test_wrong_platform_version_refused(self):self.refuse('Platform.Version','16')
    def test_nonbase_extension_package_refused(self):self.refuse('AndroidVersion.IsBaseSdk','false')
    def test_different_extension_refused(self):self.refuse('AndroidVersion.ExtensionLevel','23')
    def test_beta_field_refused(self):self.refuse('AndroidVersion.BetaVersion','1')
    def test_duplicate_api_key_refused(self):
        with self.assertRaises(ValueError):acquire.platform_properties(self.raw+b'AndroidVersion.ApiLevel=37.0\n')
    def test_missing_version_refused(self):
        with self.assertRaises(ValueError):acquire.platform_properties(b'Pkg.Revision=2\n')
    def test_escaped_key_format_refused(self):
        with self.assertRaises(ValueError):acquire.platform_properties(self.raw.replace(b'AndroidVersion.ApiLevel',b'AndroidVersion.Api\\Level'))
    def test_control_line_format_refused(self):
        with self.assertRaises(ValueError):acquire.platform_properties(self.raw.replace(b'\n',b'\r\n'))
    def test_nonbytes_input_refused(self):
        with self.assertRaises(ValueError):acquire.platform_properties(self.raw.decode())


if __name__=='__main__':unittest.main(verbosity=2)
