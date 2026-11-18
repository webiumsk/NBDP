"""DEFINED ONLY: six pure literal-property models. No tool/archive/network access."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import acquire

GOOD=b'Pkg.Revision=22.0\nPkg.Path=cmdline-tools;22.0\nPkg.Desc=Android SDK Command-line Tools\n'


class CommandlineProperties(unittest.TestCase):
    def test_exact_revision_and_package_positive(self):
        self.assertEqual(acquire.commandline_properties(GOOD)['Pkg.Revision'],'22.0')

    def test_comment_and_absent_optional_path_preserve_metadata(self):
        # Archive identity/version are mandatory. Pkg.Path is checked if published,
        # never synthesized into the returned actual properties.
        raw=b'# official properties comment\n'+GOOD.replace(b'Pkg.Path=cmdline-tools;22.0\n',b'')
        self.assertNotIn('Pkg.Path',acquire.commandline_properties(raw))

    def test_wrong_or_normalized_revision_refused(self):
        for revision in (b'21.0',b'22',b'22.00',b'22.0.0',b'022.0',b'22.1'):
            with self.subTest(revision=revision),self.assertRaises(ValueError):
                acquire.commandline_properties(GOOD.replace(b'Pkg.Revision=22.0',b'Pkg.Revision='+revision))

    def test_foreign_published_path_or_description_refused(self):
        for raw in (GOOD.replace(b'cmdline-tools;22.0',b'cmdline-tools;21.0'),GOOD.replace(b'Android SDK Command-line Tools',b'Other Tools')):
            with self.subTest(raw=raw),self.assertRaises(ValueError):acquire.commandline_properties(raw)

    def test_duplicate_keys_refused(self):
        with self.assertRaises(ValueError):acquire.commandline_properties(GOOD+b'Pkg.Revision=22.0\n')

    def test_unknown_format_control_and_encoding_refused(self):
        for raw in (b'',GOOD.replace(b'=',b':',1),GOOD+b'bad\x00=value\n',GOOD.replace(b'22.0',b'22.0 ',1),GOOD+b'Pkg.Other=\xff\n'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):acquire.commandline_properties(raw)


if __name__=='__main__':unittest.main(verbosity=2)
