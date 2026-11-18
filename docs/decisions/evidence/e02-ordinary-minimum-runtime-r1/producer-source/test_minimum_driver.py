"""Prepared pure role/navigation/export controls; never actual UI observations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1'
SPEC = importlib.util.spec_from_file_location('minimum_prepared_ui_base_controls', HERE / 'test_android_driver.py')
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
driver = base.driver


def navigation_fixture(number):
    descriptors = json.loads((EVIDENCE / 'navigation-fixtures.json').read_text())['files']
    row = next(row for row in descriptors if Path(row['path']).name.startswith('ui-' + number) and row['path'].endswith('.xml'))
    raw = Path(row['path']).read_bytes()
    if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise AssertionError('Frozen negative-history navigation DATA changed')
    return raw


def chat_screen(token='NBDP/experiment'):
    tree = ET.Element('hierarchy')
    base.node(tree, **{'content-desc': 'Back', 'class': 'android.view.View'})
    field = base.node(tree, bounds='[20,1400][1000,1550]', **{'class': 'android.widget.EditText'})
    base.node(field, 'Message', '[40,1420][300,1490]')
    base.node(tree, token, '[100,500][850,700]')
    return ET.tostring(tree)


class MinimumRoleNavigationControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nbdp-minimum-role-controls-')
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)

    def ui(self, snapshots, role='incoming'):
        runtime = base.MockRuntime(self.out, snapshots)
        runtime.plan['ordinaryRole'] = role
        runtime.plan['helperApk'] = {'path': '/CONTROL_FIXTURE_NOT_AN_APK', 'bytes': 0, 'sha256': '0' * 64}
        return driver.UI(runtime), runtime

    def test_unknown_role_refuses_before_any_adb(self):
        runtime = base.MockRuntime(self.out, [])
        runtime.plan['ordinaryRole'] = 'other'
        with self.assertRaisesRegex(ValueError, 'Closed minimum account role'):
            driver.UI(runtime)
        self.assertEqual(runtime.adb_calls, [])

    def test_archive_types_only_exact_whole_public_scalar1_nsec(self):
        value = driver.ROLE_SPECS['archive']['nsec']
        ui, runtime = self.ui([base.actual_structure_login(False), base.source_shown_login(value)], 'archive')
        ui.refresh('archive-source-shown')
        ui.input_text(value, 'archive-whole-public-key')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', value]])
        self.assertEqual(runtime.records['evidence/public-identity-visibility.json']['afterEyeDescription'], 'Show Password')

    def test_other_role_nsec_never_enters_current_window(self):
        for role, other in [('incoming', 'archive'), ('archive', 'incoming')]:
            with self.subTest(role=role):
                ui, runtime = self.ui([], role)
                with self.assertRaisesRegex(ValueError, 'Only fixed public synthetic identity'):
                    ui.input_text(driver.ROLE_SPECS[other]['nsec'], 'wrong-role')
                self.assertEqual(runtime.adb_calls, [])

    def test_archive_partial_masked_or_wrong_input_never_counts_as_complete(self):
        value = driver.ROLE_SPECS['archive']['nsec']
        for wrong in (value[:-1], '\u2022' * len(value), driver.NSEC):
            with self.subTest(wrong=wrong), tempfile.TemporaryDirectory(dir=self.out) as child:
                ui, runtime = self.ui([base.actual_structure_login(False), base.source_shown_login(wrong)], 'archive')
                runtime.out = Path(child)
                ui.refresh('before-wrong-archive-key')
                with self.assertRaisesRegex(ValueError, 'whole intended value'):
                    ui.input_text(value, 'wrong-archive-key')
                self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', value]])

    def test_helper_cannot_export_another_role_stage(self):
        ui, runtime = self.ui([], 'incoming')
        with self.assertRaisesRegex(ValueError, 'Closed role helper operation'):
            driver.helper(ui, 'CLEAR', 'archive-business')
        self.assertEqual(runtime.adb_calls, [])

    def test_chat_context_uses_message_composer_not_optional_calling_feature(self):
        ui, runtime = self.ui([chat_screen()])
        ui.refresh('known-chat-no-call-button')
        driver.chat_context(ui)
        self.assertFalse(ui.find('Voice call', True))
        self.assertEqual(runtime.adb_calls, [])

    def test_chat_context_rejects_foreign_or_nonempty_composer(self):
        for key, value in [('package', 'foreign.app'), ('text', 'unexpected-composer-input')]:
            with self.subTest(key=key), tempfile.TemporaryDirectory(dir=self.out) as child:
                tree = ET.fromstring(chat_screen())
                next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText').set(key, value)
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(child)
                ui.refresh('invalid-composer')
                with self.assertRaises(ValueError):
                    driver.chat_context(ui)
                self.assertEqual(runtime.adb_calls, [])

    def test_known_recipient_inbox_warning_is_read_only_room_branch(self):
        tree = ET.fromstring(chat_screen())
        tree.remove(next(n for n in tree if n.get('class') == 'android.widget.EditText'))
        base.node(tree, 'DM inbox relays not found. Messages cannot be delivered until they configure their relay list.',
                  '[20,1400][1000,1550]')
        ui, runtime = self.ui([ET.tostring(tree)])
        ui.refresh('room-warning-with-real-note')
        self.assertEqual(driver.chat_context(ui), 'RECIPIENT_DM_RELAYS_WARNING_READ_ONLY')
        self.assertEqual(runtime.adb_calls, [])

    def test_recipient_warning_without_expected_note_does_not_identify_room(self):
        tree = ET.fromstring(chat_screen('unrelated-content'))
        tree.remove(next(n for n in tree if n.get('class') == 'android.widget.EditText'))
        base.node(tree, 'DM inbox relays not found. Messages cannot be delivered until they configure their relay list.')
        ui, runtime = self.ui([ET.tostring(tree)])
        ui.refresh('warning-is-not-room-proof')
        with self.assertRaisesRegex(ValueError, 'Actual expected note'):
            driver.chat_context(ui)
        self.assertEqual(runtime.adb_calls, [])

    def relay_screen(self, url=driver.URL, extra_neighbor=False):
        tree = ET.Element('hierarchy')
        base.node(tree, 'Relay Settings', '[50,40][700,110]')
        base.node(tree, 'Local Relays', '[50,200][700,260]')
        field = base.node(tree, url, '[50,400][1000,550]', **{'class': 'android.widget.EditText'})
        base.node(field, 'Add a Relay', '[70,405][400,445]')
        button = base.node(field, bounds='[800,450][980,530]', clickable='true', **{'class': 'android.view.View'})
        base.node(button, 'Add', '[825,465][955,515]')
        if extra_neighbor:
            base.node(tree, 'Add', '[825,565][955,615]')
        return tree

    def test_local_add_uses_only_trailing_button_of_exact_typed_editor(self):
        ui, runtime = self.ui([ET.tostring(self.relay_screen(extra_neighbor=True))])
        ui.refresh('multiple-relay-add-labels')
        button = driver.local_relay_add_button(ui)
        self.assertEqual(button.get('bounds'), '[800,450][980,530]')
        self.assertEqual(runtime.adb_calls, [])

    def test_neighbor_section_field_or_wrong_local_url_refuses_before_add(self):
        for wrong_url, different_section in [('ws://wrong:17777', False), (driver.URL, True)]:
            with self.subTest(wrong=wrong_url), tempfile.TemporaryDirectory(dir=self.out) as child:
                tree = self.relay_screen(url=wrong_url)
                if different_section:
                    base.node(tree, 'Trusted Relays', '[50,300][700,350]')
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(child)
                ui.refresh('wrong-relay-editor')
                with self.assertRaises(ValueError):
                    driver.local_relay_add_button(ui)
                self.assertEqual(runtime.adb_calls, [])

    def test_local_add_foreign_or_detached_button_never_gets_clicked(self):
        for detached in (False, True):
            with self.subTest(detached=detached), tempfile.TemporaryDirectory(dir=self.out) as child:
                tree = self.relay_screen()
                field = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
                label = next(n for n in field.iter('node') if n.get('text') == 'Add')
                if detached:
                    parent = next(n for n in field.iter('node') if label in list(n))
                    parent.remove(label)
                    tree.append(label)
                else:
                    label.set('package', 'foreign.app')
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(child)
                ui.refresh('unowned-add-button')
                with self.assertRaises(ValueError):
                    driver.local_relay_add_button(ui)
                self.assertEqual(runtime.adb_calls, [])

    def test_actual_feeds_header_accepts_observed_two_pixel_section_clip(self):
        ui, runtime = self.ui([navigation_fixture('022')])
        ui.refresh('actual-frozen-expanded-feeds')
        header = driver.expanded_feeds_header(ui)
        self.assertEqual(header.get('bounds'), '[66,1161][906,1264]')
        self.assertEqual(runtime.adb_calls, [])

    def test_feeds_partial_viewport_does_not_invent_collapsed_state_or_action(self):
        tree = ET.fromstring(navigation_fixture('022'))
        for parent in tree.iter('node'):
            for child in list(parent):
                if child.get('text') == 'Pictures':
                    parent.remove(child)
        ui, runtime = self.ui([ET.tostring(tree)])
        ui.refresh('partial-expanded-anchors')
        self.assertIsNone(driver.expanded_feeds_header(ui))
        self.assertEqual(runtime.adb_calls, [])

    def test_feeds_foreign_duplicate_or_unowned_header_never_gets_a_click(self):
        for variant in ('foreign', 'duplicate', 'detached'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(dir=self.out) as child:
                tree = ET.fromstring(navigation_fixture('022'))
                label = next(n for n in tree.iter('node') if n.get('text') == 'Feeds')
                if variant == 'foreign':
                    label.set('package', 'foreign.app')
                elif variant == 'duplicate':
                    base.node(tree, 'Feeds')
                else:
                    parent = next(n for n in tree.iter('node') if label in list(n))
                    parent.remove(label)
                    tree.append(label)
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(child)
                ui.refresh('invalid-feeds-header')
                with self.assertRaises(ValueError):
                    driver.expanded_feeds_header(ui)
                self.assertEqual(runtime.adb_calls, [])

    def test_one_known_feeds_collapse_then_actual_system_gate(self):
        after = ET.fromstring(navigation_fixture('022'))
        base.node(after, 'System', '[66,1280][848,1330]')
        ui, runtime = self.ui([navigation_fixture('022'), ET.tostring(after)])
        ui.refresh('before-one-collapse')
        driver.seek_system(ui)
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '486', '1212']])
        self.assertEqual(runtime.records['evidence/feeds-collapse-gui.json']['actions'], 1)

    def test_system_seek_does_not_repeat_feeds_toggle_or_increase_seven_scrolls(self):
        ui, runtime = self.ui([navigation_fixture('022')] * 10)
        ui.refresh('before-exhausted-system-seek')
        with self.assertRaisesRegex(ValueError, 'bounded System seek'):
            driver.seek_system(ui)
        self.assertEqual(len([row for row in runtime.adb_calls if row[:3] == ['shell', 'input', 'tap']]), 1)
        self.assertEqual(len([row for row in runtime.adb_calls if row[:3] == ['shell', 'input', 'swipe']]), 7)

    def test_initial_ambiguous_note_refuses_but_replay_records_visible_matches(self):
        tree = ET.fromstring(chat_screen())
        base.node(tree, 'NBDP/experiment', '[100,800][850,1000]')
        ui, runtime = self.ui([ET.tostring(tree)])
        ui.refresh('two-matching-text-nodes')
        with self.assertRaisesRegex(ValueError, 'match count'):
            driver.select_note(ui, 'NBDP/experiment', False)
        selected, rows = driver.select_note(ui, 'NBDP/experiment', True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(selected.get('bounds'), '[100,800][850,1000]')
        self.assertEqual(runtime.adb_calls, [])

    def test_replay_ambiguous_equal_bottom_never_selects_arbitrarily(self):
        tree = ET.fromstring(chat_screen())
        base.node(tree, 'NBDP/experiment', '[100,500][850,700]')
        ui, runtime = self.ui([ET.tostring(tree)])
        ui.refresh('ambiguous-duplicate-position')
        with self.assertRaisesRegex(ValueError, 'Unique actual lowest'):
            driver.select_note(ui, 'NBDP/experiment', True)
        self.assertEqual(runtime.adb_calls, [])

    def export_case(self, observed, expected):
        raw = json.dumps(observed, ensure_ascii=False).encode()
        ui, runtime = self.ui([chat_screen(), chat_screen(), base.screen(['More Options']),
                               base.screen(['Copy raw JSON']), chat_screen()])
        original = runtime.adb
        def adb(args):
            if args[:3] == ['exec-out', 'run-as', driver.HELPER]:
                runtime.adb_calls.append(list(args))
                return raw
            return original(args)
        runtime.adb = adb
        def helper(subject, action, case_id):
            value = {'status': 'EMPTY_SENTINEL_SET', 'wallClockMillis': 1} if action == 'CLEAR' else {
                'status': 'CAPTURED', 'mime': 'text/plain', 'clipboardItemCount': 1,
                'clipboardTimestamp': 2, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            return value, runtime.put_json('synthetic-helper-' + action + '.json', value)
        ui.refresh('synthetic-export-start')
        with patch.object(driver, 'helper', helper):
            return driver.export_note(ui, {'id': 'incoming-business', 'index': 0}, 'NBDP/experiment', expected), runtime

    def test_export_preserves_whole_frozen_six_fields_and_original_ordered_tags(self):
        expected = json.loads((HERE / 'business-rumor.json').read_text())
        result, runtime = self.export_case(dict(expected, sig=''), expected)
        raw = Path(result['rawClientRumor']['path']).read_bytes()
        self.assertEqual(json.loads(raw), dict(expected, sig=''))
        selection = runtime.records['evidence/incoming-business/selection.json']
        self.assertEqual(selection['originalOrderedTags'], expected['tags'])
        self.assertEqual(result['duplicateObservation']['globalDuplicateBubbleCountStatus'], 'UNKNOWN_UNMEASURED')
        self.assertFalse(any(row[:3] == ['shell', 'input', 'text'] for row in runtime.adb_calls))

    def test_export_wrong_inner_recipient_content_or_signature_never_becomes_retention(self):
        expected = json.loads((HERE / 'business-rumor.json').read_text())
        for patch_value in ({'tags': [['p', driver.PEER]]}, {'content': 'mutated'}, {'sig': 'not-empty'}):
            with self.subTest(patch=patch_value), tempfile.TemporaryDirectory(dir=self.out) as child:
                previous = self.out
                self.out = Path(child)
                try:
                    with self.assertRaisesRegex(ValueError, 'whole six-field|empty unsigned'):
                        self.export_case(dict(expected, **patch_value), expected)
                finally:
                    self.out = previous


if __name__ == '__main__':
    unittest.main()
