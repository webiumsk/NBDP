"""PREPARED NOT EXECUTED: complete model window graph and field refusals.

All fake authority, resource, process, native, GUI and network operands are
synthetic DATA. No externally authenticated reviewer/session is claimed.
The real consumer.window validators are not patched or replaced.
"""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest

# Explicit source-bound fixture directory supports isolated -I direct execution.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import whole_window


class WholeWindowDataControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(os.environ.get('NBDP_MODEL_CONSUMER_DIR',
            '/Data/nbdp-e02-tooling-20261027/ordinary-consumer-preparation-r5-source2'))
        cls.producer = Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
        cls.modules = whole_window.components(cls.source)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nbdp-synthetic-whole-window-model-')
        self.root = Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def model(self, role='incoming'):
        return whole_window.Model(self.root, self.modules, self.producer, role).build()

    def subject(self, model, change):
        value = model.doc(model.subject_pin)
        change(value)
        model.subject_pin = model.put(model.subject_pin['path'], value)
        # DATA origin is re-bound to the deliberately modified model subject;
        # this does not claim a new real review and does not alter validators.
        for row in model.origin.value['reviews']:
            if row['kind'] == 'WINDOW': row['subject'] = model.subject_pin
        return value

    def artifact(self, model, descriptor, change):
        old = copy.deepcopy(descriptor)
        value = model.doc(old); change(value)
        new = model.put(old['path'], value)
        def walk(item):
            if item == old: return copy.deepcopy(new)
            if isinstance(item, dict): return {k:walk(v) for k,v in item.items()}
            if isinstance(item, list): return [walk(v) for v in item]
            return item
        self.subject(model, lambda subject: subject.update(walk(subject)))
        return new

    def test_complete_two_role_windows_with_five_exports(self):
        models = whole_window.build_two_roles(self.root, self.modules, self.producer)
        results = [model.inspect() for model in models]
        self.assertEqual([r['role'] for r in results], ['incoming', 'archive'])
        self.assertEqual([r['exports'] for r in results], [2, 3])
        self.assertLessEqual(results[0]['finished'], results[1]['started'])
        self.assertFalse(results[0]['cids'] & results[1]['cids'])
        self.assertNotEqual(results[0]['runId'], results[1]['runId'])

    def test_whole_graph_preserves_actual_frozen_scope_and_source_guard_vocabulary(self):
        model = self.model()
        source = (self.producer / 'fixture.mjs').read_text()
        self.assertIn("check('proxy:app-before-upstream-send')", source)
        self.assertEqual(model.runtime_scope, model.original_config['scope'])
        self.assertEqual(model.actual_proxy_labels, set(self.modules['observer'].PROXY_GUARD_LABELS))
        self.assertEqual(model.inspect()['exports'], 2)

    def test_complete_graph_failed_driver_has_no_export_contribution(self):
        model = self.model()
        self.artifact(model, model.driver_pin, lambda v:v.update(executionState='FAILED'))
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'VALUE_MISMATCH'):
            model.inspect()

    def test_complete_graph_nonzero_supervisor_error_cannot_donate_early_rows(self):
        model = self.model()
        self.artifact(model, model.supervisor_pin, lambda v:v.update(error='SYNTHETIC_LATE_FAILURE'))
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'VALUE_MISMATCH'):
            model.inspect()

    def test_complete_graph_omitted_final_phase_member_refused(self):
        model = self.model()
        self.subject(model, lambda v:v.update(graphFiles=[p for p in v['graphFiles'] if p['path'] != v['phase']['path']]))
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'FINAL_PHASE_MEMBER_REQUIRED'):
            model.inspect()

    def test_complete_graph_unknown_source_policy_effect_claim_refused(self):
        model = self.model()
        self.subject(model, lambda v:v['sourcePolicyObservations'].update(businessEffectsMeasured=True))
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'VALUE_MISMATCH'):
            model.inspect()

    def test_complete_graph_late_unlisted_proof_file_refused(self):
        model = self.model()
        model.raw('evidence/synthetic-late-unlisted.json', b'{"synthetic":true}')
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'OMITTED_WHOLE_WINDOW_PROOF'):
            model.inspect()

    def test_complete_graph_sticky_revoke_refused(self):
        model = self.model()
        # Put the marker in the already inventoried graph; the sticky semantics,
        # not a missing graph entry, must reject it.
        revoked = model.raw('session/control/REVOKED', b'SYNTHETIC_MODEL_REVOCATION')
        self.subject(model, lambda v:v['graphFiles'].append(revoked))
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'STICKY_REVOKED_WINDOW'):
            model.inspect()

    def test_complete_graph_operator_cannot_be_window_reviewer(self):
        model = self.model()
        row = next(r for r in model.origin.value['reviews'] if r['kind'] == 'WINDOW' and r['role'] == 'qa')
        row['actor'] = row['session'] = whole_window.MODEL_ACTOR
        with self.assertRaisesRegex(self.modules['strict'].Refusal, 'AUTHOR_OPERATOR_REVIEW_LAUNDERING'):
            model.inspect()


if __name__ == '__main__':
    unittest.main(verbosity=2)
