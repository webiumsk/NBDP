"""PREPARED NOT EXECUTED: source-derived literal/DTO regressions.

Only reads the frozen producer sources/configurations as DATA, never imports or
evaluates them. Model phase rows below do not claim actual guard execution.
"""
import ast
import hashlib
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consumer
import observer
import strict
import wire
from test_observer import graph

ROOT = Path(__file__).resolve().parents[3]
PRODUCER = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/subject.json'


class ExactSourceBindings(unittest.TestCase):
    def frozen_producer(self):
        raw = PRODUCER.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), consumer.PRODUCER_SHA)
        return strict.loads(raw)

    def source(self, name):
        pin = next(p for p in self.frozen_producer()['sources'] if Path(p['path']).name == name)
        raw = Path(pin['path']).read_bytes()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (pin['bytes'], pin['sha256']))
        return raw.decode('utf-8')

    def test_all_exact_actual_proxy_guard_literals(self):
        labels = set(re.findall(r"check\('(proxy:[^']+)'\)", self.source('fixture.mjs')))
        self.assertEqual(len(labels), 8)
        self.assertEqual(labels, observer.PROXY_GUARD_LABELS)
        self.assertIn('proxy:app-before-upstream-send', labels)
        self.assertIn('proxy:pending-before-upstream-send', labels)
        self.assertIn('proxy:upstream-open', labels)
        self.assertNotIn('proxy:before-upstream-send', labels)

    def vocabulary_graph(self, label):
        temp = tempfile.TemporaryDirectory(prefix='nbdp-consumer4-source-vocabulary-')
        self.addCleanup(temp.cleanup)
        data = graph(Path(temp.name)); files, window, proxy = data[:3]
        path = Path(window['phase']['path'])
        rows = [strict.loads(line) for line in path.read_bytes().splitlines()]
        self.assertEqual([r['phase'] for r in rows[-2:]], ['GUARD_ENTRY', 'GUARD_EXIT'])
        rows[-2]['label'] = rows[-1]['label'] = label
        raw = b''.join(strict.json_bytes(row) + b'\n' for row in rows); path.write_bytes(raw)
        descriptor = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        window['phase'] = descriptor
        window['graphFiles'] = [descriptor if p['path'] == str(path) else p for p in window['graphFiles']]
        return files, window, proxy

    def test_each_source_literal_accepted_as_observation_vocabulary(self):
        labels = set(re.findall(r"check\('(proxy:[^']+)'\)", self.source('fixture.mjs')))
        for label in sorted(labels):
            with self.subTest(label=label): observer.Trace(*self.vocabulary_graph(label))

    def test_invented_short_guard_label_refused(self):
        with self.assertRaisesRegex(strict.Refusal, 'CLOSED_ORIGINAL_GUARD_LABEL'):
            observer.Trace(*self.vocabulary_graph('proxy:before-upstream-send'))

    def test_scope_and_profile_equal_actual_supervisor_constants(self):
        assignments = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(self.source('supervisor.py')).body
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in ('SCOPE', 'PROFILE')}
        self.assertEqual(assignments, {'SCOPE': consumer.RUNTIME_SCOPE, 'PROFILE': wire.PROFILE})

    def test_both_frozen_configuration_dtos_and_scope(self):
        for pin in self.frozen_producer()['configurations']:
            raw = Path(pin['path']).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (pin['bytes'], pin['sha256']))
            config = strict.loads(raw)
            self.assertEqual(set(config), set(consumer.CONFIG_KEYS.split()))
            self.assertEqual(config['scope'], consumer.RUNTIME_SCOPE)
            self.assertEqual(config['profileId'], wire.PROFILE)
            self.assertEqual(config['schema'], 'e02-ordinary-minimum-role-runtime-plan-v2')

    def test_all_sixteen_staged_source_names_equal_frozen_configs(self):
        source = ast.parse(Path(consumer.__file__).read_text())
        window = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'window')
        assignment = next(n for n in ast.walk(window) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'expected_sources' for t in n.targets))
        expected = ast.literal_eval(assignment.value.generators[0].iter)
        self.assertEqual(len(expected), 16)
        for pin in self.frozen_producer()['configurations']:
            config = strict.loads(Path(pin['path']).read_bytes())
            self.assertEqual(tuple(Path(p['path']).name for p in config['sourceAndDependencyPins']), expected)

    def test_producer_dto_schema_literals_are_explicitly_versioned(self):
        fixture = self.source('fixture.mjs')
        wire_source = Path(wire.__file__).read_text(); consumer_source = Path(consumer.__file__).read_text()
        names = ('transport', 'validated-wire-record', 'publish-intent', 'publication-window',
                 'producer-validation', 'stage-publication', 'prepared')
        for name in names:
            literal = 'e02-minimum-' + name + '-v2'
            self.assertIn(literal, fixture)
            self.assertIn(literal, wire_source + consumer_source)
        self.assertIn('e02-minimum-fixture-command-v2', fixture)
        self.assertIn('e02-minimum-fixture-command-v2', consumer_source)

    def test_only_current_release_schema_admits_registered_i64_fields(self):
        strict.validate_numbers(dict(schema='e02-ordinary-minimum-role-release-v2',
            issuedAtUtcNs=strict.SAFE + 1, notAfterUtcNs=strict.SAFE + 2))
        with self.assertRaises(strict.Refusal):
            strict.validate_numbers(dict(schema='e02-ordinary-minimum-role-release-v1', issuedAtUtcNs=strict.SAFE + 1))


if __name__ == '__main__': unittest.main(verbosity=2)
