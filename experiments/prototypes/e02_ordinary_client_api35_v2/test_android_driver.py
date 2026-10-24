"""Pure XML/runtime controls; no Android, services, clipboard or fixture publication.

The original failed UI XML is immutable input. Execution is a separate root step.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


SOURCE = Path(__file__).with_name('android_driver.py')
spec = importlib.util.spec_from_file_location('e02_tested_android_driver', SOURCE)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
ACTUAL_MODAL = SOURCE.resolve().parents[3] / (
    'docs/decisions/evidence/e02-ordinary-client-resume-r1/'
    'ui-source-r1-before-tor-modal-fix/ui/ui-005-tor-off-selected.xml')
ACTUAL_MODAL_SHA = '389421b9ba7e0c873483c26e7e15110ec175d3715cde88555f6269d2d88ef10c'
ACTUAL_SETTINGS_ANR = SOURCE.resolve().parents[3] / (
    'docs/decisions/evidence/e02-ordinary-client-resume-r1/'
    'ui-source-r2-before-os-anr-handler/ui/ui-007-login-settle.xml')
ACTUAL_SETTINGS_ANR_SHA = 'd1e65a208e4eff2ab22d89c3f2dccba47df2567993870cac05f29a48af902e14'
ACTUAL_SYSTEM_UI_ANR = ACTUAL_MODAL.with_name('ui-001-login-start.xml')
ACTUAL_SYSTEM_UI_ANR_SHA = '9f9456e297c717b05a3a00901f5200d7f147cf1783746b153b0725e6b67e601d'
ACTUAL_MASKED_LOGIN = SOURCE.resolve().parents[3] / (
    'docs/decisions/evidence/e02-ordinary-client-resume-r1/'
    'ui-source-r4-before-visible-identity-fix/ui/ui-010-whole-disposable-identity.xml')
ACTUAL_MASKED_LOGIN_SHA = '14e7bc6f1967913a5219059478a7b1f8fcb246a08dafc5553850ba0cd1ae350f'
API35_DIAGNOSIS = SOURCE.resolve().parents[3] / 'docs/decisions/evidence/e02-ordinary-api35-preparation-r2/diagnosis-inputs'
API35_LOGIN_PINS = {
    False: ('ui-007-tor-saved-state-closed.xml', '05ee5f4e7fb6675258bac165f3c284d08a2808a9641ac204e25b8066af552b14'),
    True: ('ui-008-public-identity-visible.xml', '7e7fca5cad0cf63376c7b9c5d5fbe38fef08f2921042a342ec56d58f8b558203'),
}


def node(parent, text='', bounds='[10,10][200,70]', **attributes):
    values = {'text': text, 'bounds': bounds, 'package': driver.APP,
              'enabled': 'true', 'clickable': 'false', 'content-desc': '',
              'class': 'android.widget.TextView'}
    values.update(attributes)
    return ET.SubElement(parent, 'node', values)


def screen(labels=(), identity=None, save_bounds='[850,80][1020,150]'):
    tree = ET.Element('hierarchy')
    for label in labels:
        node(tree, label, save_bounds if label == 'Save' else '[40,200][500,280]')
    if 'Active Tor Engine' in labels:
        node(tree, bounds='[711,194][1041,362]', **{'class': 'android.widget.Spinner'})
    if identity is not None:
        field = node(tree, identity, '[100,500][900,600]', **{'class': 'android.widget.EditText', 'password': 'false'})
        button = node(field, bounds='[750,510][850,590]', clickable='true', **{'class': 'android.view.View'})
        node(button, bounds='[770,520][830,580]', **{'class': 'android.view.View', 'content-desc': 'Show Password'})
        node(button, bounds='[750,510][850,590]', **{'class': 'android.widget.Button'})
    return ET.tostring(tree)


def modal():
    raw = ACTUAL_MODAL.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ACTUAL_MODAL_SHA:
        raise AssertionError('Original failed modal fixture drifted')
    return raw


def settings_anr():
    raw = ACTUAL_SETTINGS_ANR.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ACTUAL_SETTINGS_ANR_SHA:
        raise AssertionError('Original failed Settings ANR fixture drifted')
    return raw


def masked_login():
    raw = ACTUAL_MASKED_LOGIN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ACTUAL_MASKED_LOGIN_SHA:
        raise AssertionError('Actual masked identity fixture drifted')
    return raw


def visible_login(text='', description='Show Password'):
    # Synthetic UI response only; never an actual Android observation.
    tree = ET.fromstring(masked_login())
    field = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
    field.set('password', 'false')
    field.set('text', text)
    next(n for n in tree.iter('node') if n.get('content-desc') == 'Hide Password').set('content-desc', description)
    return ET.tostring(tree)


def actual_api35_login(shown):
    name, expected = API35_LOGIN_PINS[shown]
    raw = (API35_DIAGNOSIS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise AssertionError('Original API35 failed-run identity fixture drifted')
    return raw


def source_shown_login(text=''):
    # Synthetic post-input response derived from actual empty shown-state XML.
    # This does not claim any real client accepted or rendered the input.
    tree = ET.fromstring(actual_api35_login(True))
    field = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
    field.set('text', text)
    return ET.tostring(tree)


class MockRuntime:
    def __init__(self, out, snapshots):
        self.out = out
        self.snapshots = list(snapshots)
        self.snapshot_names = []
        self.adb_calls = []
        self.sleeps = []
        self.checks = 0
        self.records = {}
        self.denied = False
        self.deny_at = None

    def check(self):
        self.checks += 1
        if self.denied or self.checks == self.deny_at:
            raise ValueError('Mock lease refused')

    def put_bytes(self, name, raw):
        path = self.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def put_json(self, name, value):
        self.records[name] = value
        return self.put_bytes(name, json.dumps(value).encode())

    def snapshot(self, name):
        self.snapshot_names.append(name)
        if not self.snapshots:
            raise AssertionError('Unexpected additional snapshot')
        return {'xml': self.put_bytes(name + '.xml', self.snapshots.pop(0)),
                'png': self.put_bytes(name + '.png', b'pure mock; not a real PNG')}

    def adb(self, args):
        self.adb_calls.append(list(args))
        return b'Success' if args == ['shell', 'pm', 'clear', driver.APP] else b''

    def sleep(self, seconds):
        self.sleeps.append(seconds)


class TorPopupControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='nbdp-e02-ui-pure-')
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)

    def ui(self, snapshots, allowed=True):
        runtime = MockRuntime(self.out, snapshots)
        ui = driver.UI(runtime)
        ui.tor_popup_allowed = allowed
        return ui, runtime

    def test_actual_late_popup_keeps_before_after_and_looks_up_fresh_save(self):
        ui, runtime = self.ui([screen(['Off']), modal(),
                               screen(['Privacy Options', 'Active Tor Engine', 'Save'],
                                      save_bounds='[800,90][1000,170]'), screen(['Login'])])
        ui.refresh('tor-engine-menu')
        ui.click('Off', 'tor-off-selected')
        self.assertEqual(ui.one('Save').get('bounds'), '[800,90][1000,170]')
        ui.click('Save', 'login-tor-saved')
        self.assertEqual(runtime.adb_calls[1], ['shell', 'input', 'tap', '645', '1067'])
        self.assertEqual(runtime.adb_calls[2], ['shell', 'input', 'tap', '900', '130'])
        self.assertEqual(runtime.snapshot_names, ['ui-001-tor-engine-menu', 'ui-002-tor-off-selected',
                                                'ui-003-tor-failure-dismissed', 'ui-004-login-tor-saved'])
        self.assertEqual(driver.read(ui.captures[1]['xml']), modal())
        self.assertEqual(ui.tor_dismissals, 1)

    def test_full_login_explicitly_saves_reopens_and_records_visual_limit(self):
        login = screen(['Adjust Tor Settings', 'Login'], identity='')
        privacy = screen(['Privacy Options', 'Active Tor Engine', 'Save'])
        home = ET.Element('hierarchy')
        node(home, **{'content-desc': 'Your Profile Picture'})
        ui, runtime = self.ui([login, privacy, screen(['Off', 'Internal', 'Orbot']), modal(),
                               privacy, login, privacy, login, login,
                               screen(['Adjust Tor Settings', 'Login'], identity=driver.NSEC),
                               ET.tostring(home)], allowed=False)
        receipt = driver.login(ui)
        record = runtime.records['evidence/tor-configuration-gui.json']
        self.assertEqual(record['torFailureDismissals'], 1)
        self.assertIn('reopened', record['savedStateReopened']['xml']['path'])
        self.assertIn('independent visual Off verification', ' '.join(record['limits']))
        self.assertEqual(driver.loads(driver.read(receipt)), record)
        self.assertFalse(ui.tor_popup_allowed)
        self.assertFalse(ui.environment_anr_allowed)
        # All input remains the one pre-existing fixed public synthetic nsec.
        self.assertEqual([a for a in runtime.adb_calls if a[:3] == ['shell', 'input', 'text']],
                         [['shell', 'input', 'text', driver.NSEC]])

    def assert_refused_without_action(self, raw, reason):
        ui, runtime = self.ui([raw])
        with self.assertRaisesRegex(ValueError, reason):
            ui.refresh('refusal')
        self.assertEqual(runtime.adb_calls, [])
        self.assertEqual(len(ui.captures), 1)

    def test_each_missing_modal_label_refuses(self):
        expected = (driver.TOR_FAILURE_TITLE, driver.TOR_FAILURE_BODY) + driver.TOR_FAILURE_CHOICES
        for value in expected:
            with self.subTest(missing=value):
                tree = ET.fromstring(modal())
                for parent in tree.iter():
                    for child in list(parent):
                        if child.get('text') == value:
                            parent.remove(child)
                # A separate private output avoids reusing immutable capture names.
                with tempfile.TemporaryDirectory(dir=self.out) as directory:
                    ui, runtime = self.ui([ET.tostring(tree)])
                    runtime.out = Path(directory)
                    with self.assertRaisesRegex(ValueError, 'Incomplete or duplicate'):
                        ui.refresh('partial')
                    self.assertEqual(runtime.adb_calls, [])

    def test_unknown_warning_refuses(self):
        tree = ET.fromstring(modal())
        next(n for n in tree.iter('node') if n.get('text') == driver.TOR_FAILURE_BODY).set('text', 'Different warning')
        self.assert_refused_without_action(ET.tostring(tree), 'Incomplete or duplicate')

    def test_extra_unknown_button_refuses(self):
        tree = ET.fromstring(modal())
        node(tree, 'Unknown action', clickable='true')
        self.assert_refused_without_action(ET.tostring(tree), 'Unrecognized')

    def test_duplicate_label_refuses(self):
        tree = ET.fromstring(modal())
        node(tree, driver.TOR_FAILURE_TITLE)
        self.assert_refused_without_action(ET.tostring(tree), 'Incomplete or duplicate')

    def test_extra_unlabeled_clickable_control_refuses(self):
        tree = ET.fromstring(modal())
        node(tree, clickable='true')
        self.assert_refused_without_action(ET.tostring(tree), 'Exact Tor failure button set')

    def test_out_of_display_button_bounds_refuse(self):
        tree = ET.fromstring(modal())
        next(n for n in tree.iter('node') if n.get('clickable') == 'true').set('bounds', '[0,0][1081,1920]')
        self.assert_refused_without_action(ET.tostring(tree), 'outside reviewed display')

    def test_disabled_or_foreign_modal_refuses(self):
        for attribute, value in [('package', 'foreign.app'), ('enabled', 'false')]:
            with self.subTest(attribute=attribute), tempfile.TemporaryDirectory(dir=self.out) as directory:
                tree = ET.fromstring(modal())
                next(n for n in tree.iter('node') if n.get('text') == driver.TOR_FAILURE_TITLE).set(attribute, value)
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(directory)
                with self.assertRaisesRegex(ValueError, 'Foreign or disabled'):
                    ui.refresh('foreign-disabled')
                self.assertEqual(runtime.adb_calls, [])

    def test_unknown_dialog_gets_no_fallback_action(self):
        ui, runtime = self.ui([screen(['Unknown warning', 'Unknown action'])])
        ui.refresh('unknown-dialog')
        with self.assertRaisesRegex(ValueError, 'exactly one current UI control: Save'):
            ui.click('Save', 'must-not-happen')
        self.assertEqual(runtime.adb_calls, [])

    def test_known_popup_outside_login_settings_refuses(self):
        ui, runtime = self.ui([modal()], allowed=False)
        with self.assertRaisesRegex(ValueError, 'outside known login/settings'):
            ui.refresh('outside-settings')
        self.assertEqual(runtime.adb_calls, [])

    def test_popup_surviving_one_dismissal_is_not_retried(self):
        ui, runtime = self.ui([modal(), modal()])
        with self.assertRaisesRegex(ValueError, 'still present; no repeat'):
            ui.refresh('persistent-popup')
        self.assertEqual(len(runtime.adb_calls), 1)
        self.assertEqual(len(ui.captures), 2)

    def test_dismissal_action_and_after_capture_budgets_refuse_before_tap(self):
        for field, value in [('tor_dismissals', 2), ('actions', 120), ('serial', 139)]:
            with self.subTest(budget=field), tempfile.TemporaryDirectory(dir=self.out) as directory:
                ui, runtime = self.ui([modal()])
                runtime.out = Path(directory)
                setattr(ui, field, value)
                with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                    ui.refresh('budget-refusal')
                self.assertEqual(runtime.adb_calls, [])

    def test_final_allowed_action_and_capture_do_not_extend_original_limits(self):
        ui, runtime = self.ui([modal(), screen(['Save'])])
        ui.actions, ui.serial = 119, 138
        ui.refresh('last-allowed')
        self.assertEqual((ui.actions, ui.serial), (120, 140))
        with self.assertRaisesRegex(ValueError, 'Finite UI action'):
            ui.click('Save', 'disallowed-save')
        self.assertEqual(len(runtime.adb_calls), 1)
        with self.assertRaisesRegex(ValueError, 'Finite named UI capture'):
            ui.refresh('disallowed-capture')
        self.assertEqual(len(runtime.snapshot_names), 2)

    def test_lease_refusal_permits_no_snapshot_or_action(self):
        ui, runtime = self.ui([modal()])
        runtime.denied = True
        with self.assertRaisesRegex(ValueError, 'Mock lease refused'):
            ui.refresh('expired')
        self.assertEqual(runtime.adb_calls, [])
        self.assertEqual(runtime.snapshot_names, [])

    def test_lease_refusal_immediately_before_dismissal_dispatches_nothing(self):
        ui, runtime = self.ui([modal()])
        runtime.deny_at = 3  # before capture, after capture, then before tap
        with self.assertRaisesRegex(ValueError, 'Mock lease refused'):
            ui.refresh('lease-before-tap')
        self.assertEqual(runtime.adb_calls, [])
        self.assertEqual(len(ui.captures), 1)


class OSAnrControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='nbdp-e02-anr-pure-')
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)

    def ui(self, snapshots, allowed=True):
        runtime = MockRuntime(self.out, snapshots)
        ui = driver.UI(runtime)
        ui.environment_anr_allowed = allowed
        ui.tor_popup_allowed = allowed
        return ui, runtime

    def test_actual_settings_anr_over_tor_waits_then_handles_exact_tor(self):
        ui, runtime = self.ui([settings_anr(), modal(), screen(['Adjust Tor Settings', 'Login'])])
        ui.refresh('login-settle')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '540', '1059'],
                                            ['shell', 'input', 'tap', '645', '1067']])
        self.assertEqual((ui.environment_anr_waits, ui.tor_dismissals), (1, 1))
        self.assertEqual(len(ui.captures), 3)
        self.assertEqual(driver.read(ui.captures[0]['xml']), settings_anr())
        self.assertEqual(driver.read(ui.captures[1]['xml']), modal())
        record = driver.loads(driver.read(ui.environment_anr_evidence[0]['afterWaitObservation']))
        self.assertEqual(record['title'], "Settings isn't responding")
        self.assertEqual(record['action'], 'Wait')
        self.assertEqual(record['before'], ui.captures[0])
        self.assertEqual(record['after'], ui.captures[1])
        self.assertEqual(record['classification'], 'ENVIRONMENT_ANR_OBSERVATION')
        self.assertEqual(record['resourceCause'], 'UNPROVEN')
        self.assertEqual(record['osHealthAfterWait'], 'UNKNOWN')
        self.assertEqual(record['businessCompatibilityOutcome'], 'NOT_ASSESSED')

    def test_system_ui_title_same_android_structure_uses_only_wait(self):
        raw = ACTUAL_SYSTEM_UI_ANR.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ACTUAL_SYSTEM_UI_ANR_SHA)
        ui, runtime = self.ui([raw, screen(['Adjust Tor Settings'])])
        ui.refresh('system-ui-anr')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '540', '1059']])
        self.assertEqual(driver.loads(driver.read(ui.environment_anr_evidence[0]['afterWaitObservation']))['title'],
                         "System UI isn't responding")

    def test_tor_dismissal_may_reveal_one_os_anr(self):
        ui, runtime = self.ui([modal(), settings_anr(), screen(['Save'])])
        ui.refresh('tor-first')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '645', '1067'],
                                            ['shell', 'input', 'tap', '540', '1059']])
        self.assertEqual(len(ui.environment_anr_evidence), 1)
        self.assertEqual(len(ui.captures), 3)

    def test_persistent_anr_retains_explicit_evidence_and_refuses_second_wait(self):
        ui, runtime = self.ui([settings_anr(), settings_anr()])
        with self.assertRaisesRegex(ValueError, 'still present after one Wait'):
            ui.refresh('persistent-anr')
        self.assertEqual(len(runtime.adb_calls), 1)
        self.assertEqual(len(ui.captures), 2)
        self.assertEqual(len(ui.environment_anr_evidence), 1)

    def test_unknown_and_amethyst_anrs_refuse(self):
        for title in ("Amethyst isn't responding", "Unknown isn't responding"):
            with self.subTest(title=title), tempfile.TemporaryDirectory(dir=self.out) as directory:
                raw = settings_anr().replace(b"Settings isn't responding", title.encode())
                ui, runtime = self.ui([raw])
                runtime.out = Path(directory)
                with self.assertRaisesRegex(ValueError, 'Unknown or duplicate OS ANR title'):
                    ui.refresh('unknown-anr')
                self.assertEqual(runtime.adb_calls, [])

    def test_partial_duplicate_foreign_disabled_and_bad_ancestry_refuse(self):
        for variant in ('partial', 'duplicate', 'foreign', 'disabled', 'ancestry', 'resource', 'bounds'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(dir=self.out) as directory:
                tree = ET.fromstring(settings_anr())
                wait = next(n for n in tree.iter('node') if n.get('text') == 'Wait')
                if variant == 'partial':
                    for parent in tree.iter():
                        if wait in list(parent):
                            parent.remove(wait)
                elif variant == 'duplicate':
                    node(tree, "Settings isn't responding", package='android')
                elif variant == 'foreign':
                    wait.set('package', driver.APP)
                elif variant == 'disabled':
                    wait.set('enabled', 'false')
                elif variant == 'ancestry':
                    next(n for n in tree.iter('node') if n.get('resource-id') == 'android:id/parentPanel').set('resource-id', 'unknown')
                elif variant == 'resource':
                    wait.set('resource-id', 'android:id/aerr_close')
                else:
                    wait.set('bounds', '[0,0][1081,1920]')
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(directory)
                with self.assertRaises(ValueError):
                    ui.refresh('malformed-anr')
                self.assertEqual(runtime.adb_calls, [])

    def test_anr_outside_login_settings_refuses(self):
        ui, runtime = self.ui([settings_anr()], allowed=False)
        with self.assertRaisesRegex(ValueError, 'outside known login/settings'):
            ui.refresh('outside-login')
        self.assertEqual(runtime.adb_calls, [])

    def test_action_capture_and_two_wait_budgets_refuse_before_dispatch(self):
        for field, value in [('environment_anr_waits', 2), ('actions', 120), ('serial', 139)]:
            with self.subTest(budget=field), tempfile.TemporaryDirectory(dir=self.out) as directory:
                ui, runtime = self.ui([settings_anr()])
                runtime.out = Path(directory)
                setattr(ui, field, value)
                with self.assertRaisesRegex(ValueError, 'OS ANR wait/capture/action budget exhausted'):
                    ui.refresh('anr-budget')
                self.assertEqual(runtime.adb_calls, [])

    def test_third_separate_os_anr_never_gets_an_action(self):
        ui, runtime = self.ui([settings_anr(), screen(['Login']), settings_anr(), screen(['Login']), settings_anr()])
        ui.refresh('first-anr')
        ui.refresh('second-anr')
        with self.assertRaisesRegex(ValueError, 'budget exhausted'):
            ui.refresh('third-anr')
        self.assertEqual(len(runtime.adb_calls), 2)
        self.assertEqual(len(ui.environment_anr_evidence), 2)
        self.assertEqual(len(ui.captures), 5)

    def test_lease_refusal_before_wait_dispatches_no_action(self):
        ui, runtime = self.ui([settings_anr()])
        runtime.deny_at = 3
        with self.assertRaisesRegex(ValueError, 'Mock lease refused'):
            ui.refresh('anr-expired')
        self.assertEqual(runtime.adb_calls, [])
        self.assertEqual(len(ui.captures), 1)
        decision = driver.loads(driver.read(ui.environment_anr_evidence[0]['decision']))
        self.assertEqual(decision['executionState'], 'DECISION_ONLY')
        self.assertIsNone(ui.environment_anr_evidence[0]['afterWaitObservation'])


class IdentityVisibilityControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='nbdp-e02-identity-pure-')
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)

    def ui(self, snapshots):
        runtime = MockRuntime(self.out, snapshots)
        return driver.UI(runtime), runtime

    def test_actual_masked_hide_label_toggles_unique_current_eye_once(self):
        ui, runtime = self.ui([masked_login(), visible_login()])
        ui.refresh('actual-masked')
        field = ui.visible_identity_field()
        self.assertEqual(field.get('password'), 'false')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '909', '900']])
        self.assertEqual(ui.identity_visibility_toggles, 1)
        self.assertEqual(driver.read(ui.captures[0]['xml']), masked_login())
        self.assertEqual(len(ui.captures), 2)

    def test_actual_shown_state_with_password_semantics_is_not_toggled_again(self):
        # Replaces v1's incorrect equation of password metadata with masking.
        # Its original source/assertion is preserved byte-exact in v1/history.
        ui, runtime = self.ui([actual_api35_login(True)])
        ui.refresh('actual-shown-state')
        self.assertEqual(ui.visible_identity_field().get('password'), 'true')
        self.assertEqual(runtime.adb_calls, [])
        self.assertEqual(ui.identity_visibility_toggles, 0)

    def test_contradictory_unpassworded_metadata_and_hidden_eye_refuses(self):
        # The pinned source's Hide Password means its hidden state, so v1's
        # synthetic contradictory case cannot establish a shown field.
        ui, runtime = self.ui([visible_login(description='Hide Password')])
        ui.refresh('contradictory-state')
        with self.assertRaisesRegex(ValueError, 'Contradictory identity'):
            ui.visible_identity_field()
        self.assertEqual(runtime.adb_calls, [])
        self.assertEqual(ui.identity_visibility_toggles, 0)

    def test_full_observed_nsec_required_after_typing(self):
        ui, runtime = self.ui([visible_login(), visible_login(driver.NSEC)])
        ui.refresh('ready-for-identity')
        ui.input_text(driver.NSEC, 'whole-disposable-identity')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', driver.NSEC]])
        self.assertEqual(ui.identity_controls()[0].get('text'), driver.NSEC)

    def test_masked_field_refuses_before_typing(self):
        ui, runtime = self.ui([masked_login()])
        ui.refresh('still-masked')
        with self.assertRaisesRegex(ValueError, 'unmasked before typing'):
            ui.input_text(driver.NSEC, 'must-not-type')
        self.assertEqual(runtime.adb_calls, [])

    def test_partial_bullets_wrong_or_empty_text_never_count_as_whole_input(self):
        for observed in (driver.NSEC[:-1], '\u2022' * len(driver.NSEC), '', 'nsec1wrong'):
            with self.subTest(observed=observed), tempfile.TemporaryDirectory(dir=self.out) as directory:
                ui, runtime = self.ui([visible_login(), visible_login(observed)])
                runtime.out = Path(directory)
                ui.refresh('before-incomplete')
                with self.assertRaisesRegex(ValueError, 'whole intended value'):
                    ui.input_text(driver.NSEC, 'incomplete-identity')
                self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', driver.NSEC]])

    def test_remasking_after_typing_refuses_even_if_text_claims_exact_nsec(self):
        tree = ET.fromstring(masked_login())
        next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText').set('text', driver.NSEC)
        ui, runtime = self.ui([visible_login(), ET.tostring(tree)])
        ui.refresh('before-remasking')
        with self.assertRaisesRegex(ValueError, 'unmasked after typing'):
            ui.input_text(driver.NSEC, 'remasked')
        self.assertEqual(len(runtime.adb_calls), 1)

    def test_persistently_masked_field_refuses_after_single_toggle(self):
        ui, runtime = self.ui([masked_login(), masked_login()])
        ui.refresh('persistent-mask')
        with self.assertRaisesRegex(ValueError, 'remains masked after one'):
            ui.visible_identity_field()
        self.assertEqual(len(runtime.adb_calls), 1)
        with self.assertRaisesRegex(ValueError, 'budget exhausted'):
            ui.visible_identity_field()
        self.assertEqual(len(runtime.adb_calls), 1)

    def test_unknown_duplicate_foreign_disabled_or_detached_eye_refuses(self):
        for variant in ('unknown', 'duplicate', 'foreign', 'disabled', 'detached', 'bounds', 'password', 'login-anchor'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(dir=self.out) as directory:
                tree = ET.fromstring(masked_login())
                eye = next(n for n in tree.iter('node') if n.get('content-desc') == 'Hide Password')
                if variant == 'unknown':
                    eye.set('content-desc', 'Unknown eye')
                elif variant == 'duplicate':
                    node(tree, **{'content-desc': 'Show Password'})
                elif variant == 'foreign':
                    eye.set('package', 'foreign.app')
                elif variant == 'disabled':
                    eye.set('enabled', 'false')
                elif variant == 'detached':
                    for parent in tree.iter():
                        if eye in list(parent):
                            parent.remove(eye)
                            break
                    tree.append(eye)
                elif variant == 'bounds':
                    eye.set('bounds', '[0,0][1081,1920]')
                elif variant == 'password':
                    next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText').attrib.pop('password')
                else:
                    next(n for n in tree.iter('node') if n.get('text') == 'Login').set('text', 'Unknown login')
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(directory)
                ui.refresh('unknown-identity-control')
                with self.assertRaises(ValueError):
                    ui.visible_identity_field()
                self.assertEqual(runtime.adb_calls, [])

    def test_duplicate_login_field_refuses(self):
        tree = ET.fromstring(masked_login())
        node(tree, **{'class': 'android.widget.EditText', 'password': 'true'})
        ui, runtime = self.ui([ET.tostring(tree)])
        ui.refresh('duplicate-fields')
        with self.assertRaisesRegex(ValueError, 'single login field'):
            ui.visible_identity_field()
        self.assertEqual(runtime.adb_calls, [])

    def test_visibility_action_and_capture_budgets_refuse_before_tap(self):
        for field, value in [('identity_visibility_toggles', 1), ('actions', 120), ('serial', 140)]:
            with self.subTest(budget=field), tempfile.TemporaryDirectory(dir=self.out) as directory:
                ui, runtime = self.ui([masked_login()])
                runtime.out = Path(directory)
                ui.refresh('before-visibility-budget')
                setattr(ui, field, value)
                with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                    ui.visible_identity_field()
                self.assertEqual(runtime.adb_calls, [])

    def test_lease_refusal_before_eye_action_dispatches_nothing(self):
        ui, runtime = self.ui([masked_login()])
        ui.refresh('eye-before-expiry')
        runtime.denied = True
        with self.assertRaisesRegex(ValueError, 'Mock lease refused'):
            ui.visible_identity_field()
        self.assertEqual(runtime.adb_calls, [])

    def test_actual_api35_hide_to_show_transition_preserves_password_semantics(self):
        ui, runtime = self.ui([actual_api35_login(False), actual_api35_login(True)])
        ui.refresh('actual-api35-before')
        field = ui.visible_identity_field()
        self.assertEqual(field.get('password'), 'true')
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '846', '900']])
        self.assertEqual(ui.identity_visibility_toggles, 1)
        self.assertEqual(driver.read(ui.captures[0]['xml']), actual_api35_login(False))
        self.assertEqual(driver.read(ui.captures[1]['xml']), actual_api35_login(True))

    def test_password_semantics_true_requires_exact_whole_public_input_and_receipt(self):
        ui, runtime = self.ui([actual_api35_login(True), source_shown_login(driver.NSEC)])
        ui.refresh('source-shown-before-input')
        ui.input_text(driver.NSEC, 'source-shown-whole-input')
        record = runtime.records['evidence/public-identity-visibility.json']
        self.assertEqual(record['beforeAccessibilityPassword'], 'true')
        self.assertEqual(record['afterAccessibilityPassword'], 'true')
        self.assertEqual(record['afterEyeDescription'], 'Show Password')
        self.assertTrue(record['wholePublicNsecObserved'])
        self.assertEqual(record['beforeInput'], ui.captures[0])
        self.assertEqual(record['afterInput'], ui.captures[1])
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', driver.NSEC]])

    def test_password_semantics_true_never_accepts_partial_masked_or_wrong_value(self):
        for observed in (driver.NSEC[:-1], '\u2022' * len(driver.NSEC), '', 'nsec1wrong'):
            with self.subTest(observed=observed), tempfile.TemporaryDirectory(dir=self.out) as directory:
                ui, runtime = self.ui([actual_api35_login(True), source_shown_login(observed)])
                runtime.out = Path(directory)
                ui.refresh('shown-before-wrong-value')
                with self.assertRaisesRegex(ValueError, 'whole intended value'):
                    ui.input_text(driver.NSEC, 'shown-wrong-value')
                self.assertNotIn('evidence/public-identity-visibility.json', runtime.records)
                self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', driver.NSEC]])

    def test_changed_field_or_button_identity_refuses_after_input(self):
        for owner, key in (('field', 'resource-id'), ('field', 'index'), ('button', 'resource-id')):
            with self.subTest(owner=owner, key=key), tempfile.TemporaryDirectory(dir=self.out) as directory:
                tree = ET.fromstring(source_shown_login(driver.NSEC))
                field = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
                eye = next(n for n in field.iter('node') if n.get('content-desc') == 'Show Password')
                button = next(n for n in field.iter('node') if n is not field and n.get('clickable') == 'true' and eye in list(n))
                (field if owner == 'field' else button).set(key, 'changed-control')
                ui, runtime = self.ui([actual_api35_login(True), ET.tostring(tree)])
                runtime.out = Path(directory)
                ui.refresh('before-changed-field')
                with self.assertRaisesRegex(ValueError, 'field structure changed'):
                    ui.input_text(driver.NSEC, 'after-changed-field')
                self.assertEqual(len(runtime.adb_calls), 1)

    def test_changed_field_identity_after_eye_tap_refuses_without_second_action(self):
        tree = ET.fromstring(actual_api35_login(True))
        next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText').set('resource-id', 'changed-field')
        ui, runtime = self.ui([actual_api35_login(False), ET.tostring(tree)])
        ui.refresh('before-changed-eye-field')
        with self.assertRaisesRegex(ValueError, 'field structure changed'):
            ui.visible_identity_field()
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'tap', '846', '900']])

    def test_unknown_password_metadata_refuses_even_with_known_shown_eye(self):
        for value in ('', 'TRUE', 'unknown'):
            with self.subTest(value=value), tempfile.TemporaryDirectory(dir=self.out) as directory:
                tree = ET.fromstring(actual_api35_login(True))
                next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText').set('password', value)
                ui, runtime = self.ui([ET.tostring(tree)])
                runtime.out = Path(directory)
                ui.refresh('unknown-password-metadata')
                with self.assertRaisesRegex(ValueError, 'actual login password state'):
                    ui.visible_identity_field()
                self.assertEqual(runtime.adb_calls, [])

    def test_shown_eye_foreign_duplicate_or_changed_structure_refuses_postinput(self):
        for variant in ('foreign', 'duplicate', 'extra-child'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory(dir=self.out) as directory:
                tree = ET.fromstring(source_shown_login(driver.NSEC))
                eye = next(n for n in tree.iter('node') if n.get('content-desc') == 'Show Password')
                button = next(n for n in tree.iter('node') if eye in list(n))
                if variant == 'foreign':
                    eye.set('package', 'foreign.app')
                elif variant == 'duplicate':
                    node(tree, **{'content-desc': 'Show Password'})
                else:
                    node(button, **{'class': 'android.widget.Button'})
                ui, runtime = self.ui([actual_api35_login(True), ET.tostring(tree)])
                runtime.out = Path(directory)
                ui.refresh('before-malformed-shown-eye')
                with self.assertRaises(ValueError):
                    ui.input_text(driver.NSEC, 'after-malformed-shown-eye')
                self.assertEqual(len(runtime.adb_calls), 1)

    def test_multiline_bounds_reflow_still_requires_same_closed_field_and_whole_value(self):
        tree = ET.fromstring(source_shown_login(driver.NSEC))
        field = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
        field.set('bounds', '[173,825][908,1100]')
        ui, runtime = self.ui([actual_api35_login(True), ET.tostring(tree)])
        ui.refresh('before-text-reflow')
        ui.input_text(driver.NSEC, 'after-text-reflow')
        self.assertEqual(ui.identity_controls()[0].get('text'), driver.NSEC)
        self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', driver.NSEC]])

    def test_eye_or_whole_value_change_after_keyboard_dismissal_refuses(self):
        typed = ET.fromstring(source_shown_login(driver.NSEC))
        node(typed, **{'package': 'com.android.inputmethod.latin'})
        for final in (source_shown_login('nsec1wrong'),
                      source_shown_login(driver.NSEC).replace(b'Show Password', b'Hide Password')):
            with self.subTest(final=final), tempfile.TemporaryDirectory(dir=self.out) as directory:
                ui, runtime = self.ui([actual_api35_login(True), ET.tostring(typed), final])
                runtime.out = Path(directory)
                ui.refresh('before-keyboard-dismissal')
                with self.assertRaisesRegex(ValueError, 'survive keyboard dismissal'):
                    ui.input_text(driver.NSEC, 'typed-before-dismissal')
                self.assertEqual(runtime.adb_calls, [['shell', 'input', 'text', driver.NSEC], ['shell', 'input', 'keyevent', '4']])


if __name__ == '__main__':
    unittest.main()
