"""Nine DEFINED/zero executed SOURCE2 admission controls; separate future scope.

These definitions do not import capture/producer modules. If separately authorized
later, selected source helper AST definitions are compiled in an explicit stdlib
namespace. Only local disposable filesystem fixtures and metadata are exercised;
no child/service/native/crypto/SDK/runtime/grant operations occur. These are not
part of the producer's unchanged20/8/7 or separate3 suites.
"""
import ast
import copy
import hashlib
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
EXPECTED_ROOTS=[{'root':'/tmp/nbdp-e02-api35-fixture-r2/sdk','count':434},
                {'root':'/tmp/nbdp-e02-minimal-rs-v7/guard-python','count':522}]


def helper(file,name):
    tree=ast.parse((HERE/file).read_text())
    definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(definitions)==1
    namespace={'os':os,'stat':stat,'hashlib':hashlib,'Path':Path,'READ_TREE_ROOTS':copy.deepcopy(EXPECTED_ROOTS)}
    exec(compile(ast.Module(body=definitions,type_ignores=[]),str(HERE/file),'exec'),namespace)
    return namespace[name]


def tree_fixture():
    trees=copy.deepcopy(EXPECTED_ROOTS);indexed={}
    for tree in trees:
        tree['files']=[]
        for index in range(tree['count']):
            rel='synthetic-'+str(index)
            row={'path':tree['root']+'/'+rel,'bytes':index,'sha256':'0'*64,'relativePath':rel,'mode':0o644}
            tree['files'].append(row);indexed[row['path']]={k:row[k] for k in ('path','bytes','sha256')}
    return trees,indexed


class Source2AdmissionModels(unittest.TestCase):
    def pins(self):
        return [helper('capture-template.py','pin'),helper('assemble-source-only.py','pin')]

    def refuse_without_open(self,path):
        for pin in self.pins():
            with self.subTest(helper=pin.__code__.co_filename):
                with mock.patch.object(os,'open',side_effect=RuntimeError('OPEN_MUST_NOT_BE_CALLED')) as opened:
                    with self.assertRaises(AssertionError):pin(path)
                    opened.assert_not_called()

    def test_valid_regular_stream_and_exact_nonblocking_nofollow_flags(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'regular';raw=b'a'*1048576+b'xyz';path.write_bytes(raw)
            expected={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            original_open=os.open
            for pin in self.pins():
                with self.subTest(helper=pin.__code__.co_filename):
                    with mock.patch.object(os,'open',wraps=original_open) as opened:
                        self.assertEqual(pin(path),expected)
                        self.assertEqual(opened.call_args.args[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)

    def test_fifo_refused_before_open(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fifo';os.mkfifo(path);self.refuse_without_open(path)

    def test_symlink_refused_before_open(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'target';target.write_bytes(b'x')
            path=Path(folder)/'link';path.symlink_to(target);self.refuse_without_open(path)

    def test_oversize_refused_before_open_without_allocating_body(self):
        fake=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_size=8589934593)
        with mock.patch.object(Path,'lstat',return_value=fake):self.refuse_without_open(Path('/synthetic-oversize'))

    def test_special_socket_and_device_refused_before_open(self):
        for mode in (stat.S_IFSOCK,stat.S_IFCHR,stat.S_IFBLK,stat.S_IFDIR):
            with self.subTest(mode=mode):
                fake=SimpleNamespace(st_mode=mode|0o600,st_size=0)
                with mock.patch.object(Path,'lstat',return_value=fake):self.refuse_without_open(Path('/synthetic-special'))

    def test_open_race_to_symlink_refused_before_stream(self):
        for pin in self.pins():
            with self.subTest(helper=pin.__code__.co_filename),tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'regular';path.write_bytes(b'x');target=Path(folder)/'target';target.write_bytes(b'y')
                original_open=os.open
                def replace_then_open(*args,**kwargs):
                    path.unlink();path.symlink_to(target);return original_open(*args,**kwargs)
                with mock.patch.object(os,'open',side_effect=replace_then_open),mock.patch.object(os,'fdopen') as streamed:
                    with self.assertRaises(OSError):pin(path)
                    streamed.assert_not_called()

    def test_exact_roots_accept_and_wrong_duplicate_reversed_refuse(self):
        admit_roots=helper('assemble-source-only.py','admit_tree_roots')
        admit_trees=helper('capture-template.py','admit_read_trees')
        admit_roots(copy.deepcopy(EXPECTED_ROOTS));trees,indexed=tree_fixture();admit_trees(trees,indexed)
        variants=[]
        wrong=copy.deepcopy(EXPECTED_ROOTS);wrong[0]['root']='/tmp/count-equivalent-alternate';variants.append(wrong)
        duplicate=copy.deepcopy(EXPECTED_ROOTS);duplicate[1]['root']=duplicate[0]['root'];variants.append(duplicate)
        variants.append(list(reversed(copy.deepcopy(EXPECTED_ROOTS))))
        for roots in variants:
            with self.subTest(roots=roots):
                with self.assertRaises(AssertionError):admit_roots(roots)
                changed=copy.deepcopy(trees)
                for current,root in zip(changed,roots):current.update(root)
                with self.assertRaises(AssertionError):admit_trees(changed,indexed)

    def test_omitted_or_mismatched_flat_row_refused(self):
        admit=helper('capture-template.py','admit_read_trees');trees,indexed=tree_fixture()
        first=trees[0]['files'][0]['path']
        omitted=copy.deepcopy(indexed);del omitted[first]
        changed=copy.deepcopy(indexed);changed[first]['sha256']='1'*64
        for flat in (omitted,changed):
            with self.subTest(flatCount=len(flat)):
                with self.assertRaises(AssertionError):admit(trees,flat)

    def test_closed_root_tree_row_shapes_and_relative_membership(self):
        admit_roots=helper('assemble-source-only.py','admit_tree_roots')
        roots=copy.deepcopy(EXPECTED_ROOTS);roots[0]['extraAuthority']=True
        with self.assertRaises(AssertionError):admit_roots(roots)
        admit=helper('capture-template.py','admit_read_trees');trees,indexed=tree_fixture()
        variants=[]
        unknown=copy.deepcopy(trees);unknown[0]['extraAuthority']=True;variants.append(unknown)
        missing=copy.deepcopy(trees);missing[0]['files'].pop();variants.append(missing)
        duplicate=copy.deepcopy(trees);duplicate[0]['files'][1]=copy.deepcopy(duplicate[0]['files'][0]);variants.append(duplicate)
        escaping=copy.deepcopy(trees);escaping[0]['files'][0]['relativePath']='../outside';variants.append(escaping)
        for value in variants:
            with self.subTest(value=value[0].get('extraAuthority','row')):
                with self.assertRaises(AssertionError):admit(value,indexed)


if __name__=='__main__':unittest.main(verbosity=1)
