"""DEFINED ONLY: three pure source/AST command-remediation regressions."""
import ast
import copy
from pathlib import Path
import unittest
NEW=Path(__file__).resolve().parent
OLD=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r3')


def tree(root,relative):return ast.parse((root/relative).read_text())


def argv_node(t):
    main=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    return next(n for n in ast.walk(main) if isinstance(n,ast.Assign) and
        any(isinstance(v,ast.Name) and v.id=='argv' for v in n.targets))


def definitions(t):
    return {n.name:ast.dump(n,include_attributes=False) for n in t.body
        if isinstance(n,(ast.FunctionDef,ast.ClassDef))}


class CommandCorrection(unittest.TestCase):
    def test_exact_task_exclusions_are_the_only_argv_addition(self):
        a=argv_node(tree(OLD,'preparation/build_inside.py')).value
        b=argv_node(tree(NEW,'preparation/build_inside.py')).value
        self.assertEqual([ast.literal_eval(v) for v in b.elts[-4:]],['-x','spotlessApply','-x',':installGitHook'])
        self.assertEqual(ast.dump(ast.List(elts=b.elts[:-4],ctx=ast.Load()),include_attributes=False),
            ast.dump(a,include_attributes=False))

    def test_entire_original_build_and_source_guards_are_unchanged(self):
        a=tree(OLD,'preparation/build_inside.py');b=copy.deepcopy(tree(NEW,'preparation/build_inside.py'))
        argv_node(b).value.elts=argv_node(b).value.elts[:-4]
        self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))

    def test_sdk_and_lifecycle_functions_and_prior_seven_models_are_unchanged(self):
        for path in ('supervisor-source/supervise_build.py','materializer-source/materialize.py'):
            with self.subTest(path=path):self.assertEqual(definitions(tree(OLD,path)),definitions(tree(NEW,path)))
        path='supervisor-source/test_installed_sdk_bindings.py'
        self.assertEqual((OLD/path).read_bytes(),(NEW/path).read_bytes())


if __name__=='__main__':unittest.main(verbosity=2)
