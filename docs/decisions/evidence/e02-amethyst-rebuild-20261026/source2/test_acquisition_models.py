"""PREPARED, NOT EXECUTED: pure archive-policy models. No downloads/tools."""
from pathlib import Path, PurePosixPath
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import acquire


class ArchivePolicyModels(unittest.TestCase):
    limits=dict(archiveMembers=100,pathCharacters=1024,linkTargetBytes=4096,linkHops=16)
    item=dict(singleFileBytes=100,expandedBytes=200)

    def row(self,path,kind='file',size=1,target=''):
        return dict(path=PurePosixPath(path),kind=kind,bytes=size,mode=0o644,target=target)

    def inspect(self,rows):return acquire.validate_members(rows,self.item,self.limits)
    def test_regular_tree_positive(self):self.inspect([self.row('root/a'),self.row('root/b')])
    def test_internal_symlink_positive(self):self.inspect([self.row('root/a'),self.row('root/b','symlink',0,'a')])
    def test_internal_hardlink_positive(self):self.inspect([self.row('root/a'),self.row('root/b','hardlink',0,'root/a')])
    def test_absolute_path_refused(self):
        with self.assertRaises(ValueError):acquire.name('/escape',self.limits)
    def test_traversal_refused(self):
        with self.assertRaises(ValueError):acquire.name('root/../escape',self.limits)
    def test_normalized_alias_refused(self):
        with self.assertRaises(ValueError):acquire.name('root//a',self.limits)
    def test_duplicate_member_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a'),self.row('root/a')])
    def test_special_member_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a','special')])
    def test_symlink_escape_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a','symlink',0,'../../escape')])
    def test_link_cycle_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a','symlink',0,'b'),self.row('root/b','symlink',0,'a')])
    def test_link_as_directory_parent_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a','symlink',0,'b'),self.row('root/a/child'),self.row('root/b')])
    def test_single_file_ceiling_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a',size=101)])
    def test_total_expansion_ceiling_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a',size=100),self.row('root/b',size=100),self.row('root/c')])
    def test_missing_link_target_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a','symlink',0,'missing')])
    def test_hardlink_to_symlink_refused(self):
        with self.assertRaises(ValueError):self.inspect([self.row('root/a'),self.row('root/b','symlink',0,'a'),self.row('root/c','hardlink',0,'root/b')])
    def test_fixed_https_host_positive(self):acquire.url_allowed('https://dl.google.com/a',['dl.google.com'])
    def test_http_refused(self):
        with self.assertRaises(ValueError):acquire.url_allowed('http://dl.google.com/a',['dl.google.com'])
    def test_foreign_redirect_host_refused(self):
        with self.assertRaises(ValueError):acquire.url_allowed('https://example.invalid/a',['dl.google.com'])
    def test_userinfo_refused(self):
        with self.assertRaises(ValueError):acquire.url_allowed('https://user:pass@dl.google.com/a',['dl.google.com'])
    def test_nonstandard_port_refused(self):
        with self.assertRaises(ValueError):acquire.url_allowed('https://dl.google.com:8443/a',['dl.google.com'])


if __name__=='__main__':unittest.main(verbosity=2)
