"""Defined only: one pure source/AST integration regression; no build imports."""
import ast
import json
from pathlib import Path
import unittest
OLD=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r4')
NEW=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r5')

class PlanStateIntegration(unittest.TestCase):
    def test_actual_plan_state_matches_unchanged_supervisor_admission(self):
        old_main=next(n for n in ast.parse((OLD/'supervisor-source/supervise_build.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        new_main=next(n for n in ast.parse((NEW/'supervisor-source/supervise_build.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        self.assertEqual(ast.dump(old_main,include_attributes=False),ast.dump(new_main,include_attributes=False))
        checks=[n for n in ast.walk(new_main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='INSTALLED_SDK_BINDING_NOT_READY']
        self.assertEqual(len(checks),1)
        comparison=checks[0].args[0]
        self.assertIsInstance(comparison,ast.Compare)
        self.assertEqual(ast.dump(comparison.left),ast.dump(ast.parse("plan_reference['state']",mode='eval').body))
        self.assertEqual(len(comparison.ops),1)
        self.assertIsInstance(comparison.ops[0],ast.Eq)
        self.assertEqual(len(comparison.comparators),1)
        expected=ast.literal_eval(comparison.comparators[0])
        self.assertEqual(expected,'SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_ROOT_RELEASE')
        self.assertEqual(json.loads((NEW/'supervisor-source/plan.json').read_text())['state'],expected)
        self.assertNotEqual(json.loads((OLD/'supervisor-source/plan.json').read_text())['state'],expected)

if __name__=='__main__':unittest.main(verbosity=2)
