"""Prepared bounded SOURCE/DATA integration controls, no experiment execution.

AST/source checks verify wiring not transport correctness. Original accepted
component controls carry only on byte-identical functions/modules.
"""
import ast
import hashlib
import json
from pathlib import Path
import unittest
HERE = Path(__file__).resolve().parent
OLD = Path('/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e02_ordinary_minimum_v1')
DIAG = Path('/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e02_transport_query_diagnostic_v2')


def function_ast(path, name):
    tree = ast.parse(path.read_text())
    return ast.dump(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name), include_attributes=False)


class Producer2SourceBindings(unittest.TestCase):
    def test_all_three_accepted_modules_byte_identical(self):
        for name in ['exchange.mjs', 'phase-writer.mjs', 'dependency-tree.mjs', 'dependency-tree.json', 'lease_guard.py']:
            self.assertEqual((HERE / name).read_bytes(), (DIAG / name).read_bytes())

    def test_host_full_inventory_functions_identical(self):
        for name in ['dependency_relative', 'dependency_snapshot', 'verify_dependency_inventory']:
            self.assertEqual(function_ast(HERE / 'supervisor.py', name), function_ast(DIAG / 'supervisor.py', name))

    def test_preimport_and_end_dependency_boundaries_wired(self):
        source = (HERE / 'fixture.mjs').read_text()
        self.assertLess(source.index("verifyDependencyTree('/input/node_modules'"), source.index("await import('./transport.mjs')"))
        self.assertIn("verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);socket.end", source)
        self.assertIn("check();verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);need(response.ok", source)
        tree = ast.parse((HERE / 'supervisor.py').read_text())
        for name in ['verify_config', 'execute']:
            fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'verify_dependency_inventory' for n in ast.walk(fn)))

    def test_complete_staged_modules_and_tree_pin(self):
        tree = ast.parse((HERE / 'supervisor.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'source_pins')
        names = {n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and type(n.value) is str}
        for name in ['exchange.mjs', 'phase-writer.mjs', 'capture-budget.mjs', 'proxy-observer.mjs', 'exchange-adapter.mjs', 'dependency-tree.mjs', 'dependency-tree.json']:
            self.assertIn(name, names)
        plan = json.loads((HERE / 'fixture-plan.json').read_bytes())
        raw = (HERE / 'dependency-tree.json').read_bytes()
        self.assertEqual(plan['dependencyTree'], {'path': '/input/dependency-tree.json', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

    def test_same_original_guard_invocation_body(self):
        def body(source, name):
            text = source.read_text(); start = text.index('function ' + name + '(){'); end = text.index('\n}', start)
            return text[text.index('\n', start):end]
        self.assertEqual(body(HERE / 'fixture.mjs', 'guardCheck'), body(OLD / 'fixture.mjs', 'check'))

    def test_frozen_oracles_and_exact_query_no_baseline_payload(self):
        for name in ['business-rumor.json', 'chat-rumor.json']:
            self.assertEqual((HERE / name).read_bytes(), (OLD / name).read_bytes())
        source = (HERE / 'fixture.mjs').read_text()
        self.assertIn('const initial=T.wrap(rumors.business,from,spec.account)', source)
        self.assertIn('T.wrap(rumors.chat,from,B)', source)
        self.assertIn('T.wrap(rumors.business,from,A)', source)
        self.assertIn("exchange(null,{ids:[event.id],limit:1},stage.id+'-query')", source)
        self.assertNotIn('publish-frame.json', source)

    def test_original_android_and_transport_limits(self):
        old = ast.parse((OLD / 'supervisor.py').read_text()); new = ast.parse((HERE / 'supervisor.py').read_text())
        for name in ['CONFIG', 'EMULATOR', 'LIMITS', 'ROLES', 'RUNTIME', 'RELAY', 'PY', 'LOG_OPTIONS']:
            def assignment(tree):
                return ast.dump(next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)), include_attributes=False)
            self.assertEqual(assignment(old), assignment(new))
        limits = json.loads((HERE / 'fixture-plan.json').read_bytes())['limits']
        self.assertEqual(limits, json.loads((OLD / 'fixture-plan.json').read_bytes())['limits'])
        self.assertEqual(limits['captureBytes'], 16777216)
        self.assertEqual(limits['networkTimeoutMilliseconds'], 10000)


if __name__ == '__main__':
    unittest.main()
