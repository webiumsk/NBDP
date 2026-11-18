"""Closed XML-driven first ordinary-client cell; no subprocesses or import-time work."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
APP = 'com.vitorpamplona.amethyst.debug'
APP_COMPONENT = APP + '/com.vitorpamplona.amethyst.ui.MainActivity'
HELPER = 'org.nbdp.clipboard.capture'
HELPER_COMPONENT = HELPER + '/.CaptureActivity'
CASE = 'minimum-two-role-rs'
PROFILE = 'e02-ordinary-minimum-rs-two-role-v2'
NSEC = 'nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqpqptcfk2'
ACCOUNT = 'c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5'
PEER = '79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
URL = 'ws://localhost:17777'
ROLE_SPECS = {
    'incoming': {'windowId': 'incoming-b', 'account': ACCOUNT, 'peer': PEER,
        'nsec': NSEC, 'tab': 'New Requests',
        'stages': ('incoming-business', 'incoming-ordinary-chat')},
    'archive': {'windowId': 'archive-a', 'account': PEER, 'peer': ACCOUNT,
        'nsec': 'nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqsmhltgl',
        'tab': 'Known', 'stages': ('archive-business', 'archive-identical-replay', 'archive-fresh-wrap-replay')},
}

TOR_FAILURE_TITLE = "Tor isn't connecting"
TOR_FAILURE_BODY = ("Amethyst couldn't finish bootstrapping Tor. Use a regular (non-Tor) connection "
                    "so the feed can load? We'll remember this choice for the next hour and re-try Tor after that.")
TOR_FAILURE_CHOICES = ('Use regular connection', 'Keep waiting')
OS_ANR_TITLES = ("Settings isn't responding", "System UI isn't responding")


def need(value, message):
    if not value:
        raise ValueError(message)


def loads(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'Duplicate JSON key')
            value[key] = item
        return value
    return json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs,
                      parse_float=lambda _: need(False, 'Integer-only new evidence'),
                      parse_constant=lambda _: need(False, 'Nonfinite JSON refused'))


def equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(equal(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def read(pin, maximum=2097152):
    need(set(pin) == {'path', 'bytes', 'sha256'}, 'Closed descriptor required')
    path = Path(pin['path'])
    need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'Canonical evidence path required')
    need(type(pin['bytes']) is int and 0 <= pin['bytes'] <= maximum, 'Bounded evidence required')
    raw = path.read_bytes()
    need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'Evidence drift')
    return raw


def fixture(runtime, operation):
    runtime.check()
    raw = runtime.fixture(operation)
    sequence = getattr(runtime, '_minimum_fixture_sequence', 0) + 1
    runtime._minimum_fixture_sequence = sequence
    reply_pin = runtime.put_bytes('evidence/fixture-%02d-%s-reply.json' % (sequence, operation), raw)
    value = loads(raw)
    spec = ROLE_SPECS[runtime.plan['ordinaryRole']]
    need(value['schema'] == 'e02-minimum-fixture-command-v2' and value['operation'] == operation
         and value['caseId'] == CASE and value['profileId'] == PROFILE
         and value['windowId'] == spec['windowId'] and value['ok'] is True,
         'Exact successful closed minimum fixture reply required')
    runtime.check()
    command_path = runtime.out / ('commands/%04d.json' % runtime.sequence)
    command_raw = command_path.read_bytes()
    need(len(command_raw) <= 2097152, 'Bounded actual fixture command receipt required')
    command_pin = {'path': str(command_path), 'bytes': len(command_raw),
                   'sha256': hashlib.sha256(command_raw).hexdigest()}
    call = {'schema': 'e02-minimum-fixture-call-v1', 'profileId': PROFILE,
            'windowId': spec['windowId'], 'operation': operation, 'ordinal': sequence,
            'commandSequence': runtime.sequence, 'command': command_pin, 'reply': reply_pin}
    call_pin = runtime.put_json('evidence/fixture-%02d-%s-call.json' % (sequence, operation), call)
    runtime._minimum_last_fixture_call = (call, call_pin)
    if not hasattr(runtime, '_minimum_fixture_calls'):
        runtime._minimum_fixture_calls = []
    runtime._minimum_fixture_calls.append(call_pin)
    runtime.check()
    return value['result']


def mapped(runtime, descriptor):
    original = PurePosixPath(descriptor['path'])
    prefix = PurePosixPath('/session/fixtures')
    need(original.is_relative_to(prefix) and '..' not in original.parts, 'Fixed fixture namespace required')
    path = runtime.out / 'session/fixtures' / original.relative_to(prefix)
    value = dict(descriptor, path=str(path))
    read(value, 16777216)
    return value


class UI:
    def __init__(self, runtime):
        self.runtime = runtime
        self.ordinary_role = runtime.plan['ordinaryRole']
        need(self.ordinary_role in ROLE_SPECS, 'Closed minimum account role required')
        self.role_spec = ROLE_SPECS[self.ordinary_role]
        self.public_nsec = self.role_spec['nsec']
        self.serial = 0
        self.actions = 0
        self.tree = None
        self.current = None
        self.captures = []
        self.tor_popup_allowed = False
        self.tor_dismissals = 0
        self.environment_anr_allowed = False
        self.environment_anr_waits = 0
        self.environment_anr_evidence = []
        self.identity_visibility_toggles = 0

    def _capture(self, label):
        self.runtime.check()
        self.serial += 1
        need(self.serial <= 140 and re.fullmatch('[a-z0-9-]{1,40}', label), 'Finite named UI capture limit')
        self.current = self.runtime.snapshot('ui-%03d-' % self.serial + label)
        raw = read(self.current['xml'])
        need(b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw, 'XML declarations refused')
        self.tree = ET.fromstring(raw)
        need(self.tree.tag == 'hierarchy' and len(list(self.tree.iter())) < 10000, 'Bounded actual UI hierarchy required')
        self.captures.append(self.current)
        self.runtime.check()
        return self.current

    def tor_popup(self):
        """Recognize only the complete observed modal; partial/ambiguous variants refuse."""
        expected = (TOR_FAILURE_TITLE, TOR_FAILURE_BODY) + TOR_FAILURE_CHOICES
        if not any(self.find(value) for value in expected):
            return None
        need(self.tor_popup_allowed, 'Tor failure popup outside known login/settings flow')
        need(all(len(self.find(value)) == 1 for value in expected), 'Incomplete or duplicate Tor failure popup')
        nodes = self.nodes()
        need(sorted(n.get('text') for n in nodes if n.get('text')) == sorted(expected)
             and all(not n.get('content-desc') for n in nodes), 'Unrecognized Tor failure popup content')
        need(all(n.get('package') == APP and n.get('enabled') == 'true' for n in nodes),
             'Foreign or disabled Tor failure popup')
        controls = [n for n in nodes if n.get('clickable') == 'true']
        need(len(controls) == 2, 'Exact Tor failure button set required')
        buttons = []
        for choice in TOR_FAILURE_CHOICES:
            label = self.one(choice)
            parents = [n for n in controls if label in list(n.iter('node'))]
            need(len(parents) == 1, 'Unique actual Tor failure button required')
            button = parents[0]
            children = [n for n in button.iter('node') if n.get('class') == 'android.widget.Button']
            need(len(children) == 1 and not children[0].get('text'), 'Recognized Tor failure button structure required')
            x, y, right, bottom = self.bounds(button)
            left_label, top_label, right_label, bottom_label = self.bounds(label)
            need(x <= left_label < right_label <= right and y <= top_label < bottom_label <= bottom,
                 'Tor failure label outside its current button')
            buttons.append(button)
        need(buttons[0] is not buttons[1], 'Distinct Tor failure buttons required')
        return buttons[0]

    def refresh(self, label):
        self._capture(label)
        self.wait_for_known_os_anr()
        button = self.tor_popup()
        if button is not None:
            # The current capture is the before evidence. Reserve an after capture
            # before dispatch, and never retry a modal that survives this action.
            need(self.tor_dismissals < 2 and self.serial < 140 and self.actions < 120,
                 'Finite Tor popup dismissal/capture/action budget exhausted')
            self.tor_dismissals += 1
            x, y, right, bottom = self.bounds(button)
            self.adb(['shell', 'input', 'tap', str((x + right) // 2), str((y + bottom) // 2)])
            self.runtime.sleep(1)
            self._capture('tor-failure-dismissed')
            self.wait_for_known_os_anr()
            need(self.tor_popup() is None, 'Tor failure popup still present; no repeat action')
        return self.current

    def environment_anr(self):
        """Only the two observed Android OS ANRs may offer a bounded Wait action."""
        nodes = self.nodes()
        if not any("isn't responding" in n.get('text', '') or n.get('resource-id') in
                   ('android:id/aerr_wait', 'android:id/aerr_close') for n in nodes):
            return None
        need(self.environment_anr_allowed, 'OS ANR outside known login/settings flow')
        titles = [n for n in nodes if n.get('text') in OS_ANR_TITLES]
        need(len(titles) == 1, 'Unknown or duplicate OS ANR title; no action')
        title = titles[0]
        expected = (title.get('text'), 'Wait', 'Close app')
        need(all(len(self.find(value)) == 1 for value in expected)
             and sorted(n.get('text') for n in nodes if n.get('text')) == sorted(expected)
             and all(not n.get('content-desc') for n in nodes), 'Incomplete or unknown OS ANR content')
        need(all(n.get('package') == 'android' and n.get('enabled') == 'true' for n in nodes),
             'OS ANR requires exact Android package and enabled controls')
        need(title.get('resource-id') == 'android:id/alertTitle'
             and title.get('class') == 'android.widget.TextView', 'Exact OS ANR title structure required')
        self.bounds(title)
        wait, close = self.one('Wait'), self.one('Close app')
        for button, resource in ((wait, 'android:id/aerr_wait'), (close, 'android:id/aerr_close')):
            need(button.get('resource-id') == resource and button.get('class') == 'android.widget.Button'
                 and button.get('clickable') == 'true', 'Exact OS ANR button structure required')
            self.bounds(button)
        controls = [n for n in nodes if n.get('clickable') == 'true']
        need(len(controls) == 2 and wait in controls and close in controls, 'Exact OS ANR button set required')
        panels = [n for n in nodes if n.get('resource-id') == 'android:id/parentPanel']
        need(len(panels) == 1 and all(n in list(panels[0].iter('node')) for n in (title, wait, close)),
             'Exact OS ANR common button/title ancestry required')
        left, top, right, bottom = self.bounds(panels[0])
        for control in (title, wait, close):
            x, y, control_right, control_bottom = self.bounds(control)
            need(left <= x < control_right <= right and top <= y < control_bottom <= bottom,
                 'OS ANR controls outside common panel bounds')
        return title.get('text'), wait

    def wait_for_known_os_anr(self):
        observed = self.environment_anr()
        if observed is None:
            return
        title, wait = observed
        need(self.environment_anr_waits < 2 and self.serial < 140 and self.actions < 120,
             'Finite OS ANR wait/capture/action budget exhausted')
        before = self.current
        self.environment_anr_waits += 1
        x, y, right, bottom = self.bounds(wait)
        decision = self.runtime.put_json('evidence/environment-anr-%02d-decision.json' % self.environment_anr_waits, {
            'schema': 'e02-environment-anr-decision-v1', 'title': title, 'action': 'Wait',
            'before': before, 'ordinal': self.environment_anr_waits, 'executionState': 'DECISION_ONLY',
            'classification': 'ENVIRONMENT_ANR_OBSERVATION', 'resourceCause': 'UNPROVEN',
            'osHealth': 'UNKNOWN', 'businessCompatibilityOutcome': 'NOT_ASSESSED'})
        row = {'decision': decision, 'afterWaitObservation': None}
        self.environment_anr_evidence.append(row)
        self.adb(['shell', 'input', 'tap', str((x + right) // 2), str((y + bottom) // 2)])
        self.runtime.sleep(1)
        self._capture('os-anr-wait-observed')
        # Retain an explicit environment record even when the fresh frame refuses.
        evidence = self.runtime.put_json('evidence/environment-anr-%02d.json' % self.environment_anr_waits, {
            'schema': 'e02-environment-anr-v1', 'title': title, 'action': 'Wait', 'decision': decision,
            'before': before, 'after': self.current, 'ordinal': self.environment_anr_waits,
            'classification': 'ENVIRONMENT_ANR_OBSERVATION', 'resourceCause': 'UNPROVEN',
            'osHealthAfterWait': 'UNKNOWN', 'businessCompatibilityOutcome': 'NOT_ASSESSED',
            'limits': ['The observation is neither a business-compatibility success nor a failure.',
                       'A single Wait and fresh capture do not prove the environment recovered.']})
        row['afterWaitObservation'] = evidence
        need(self.environment_anr() is None, 'OS ANR still present after one Wait; no repeat action')

    def nodes(self):
        return list(self.tree.iter('node'))

    def find(self, value, description=False, contains=False):
        field = 'content-desc' if description else 'text'
        return [n for n in self.nodes() if (value in n.get(field, '') if contains else n.get(field) == value)]

    def one(self, value, description=False):
        found = self.find(value, description)
        need(len(found) == 1, 'Expected exactly one current UI control: ' + value)
        return found[0]

    def bounds(self, node):
        match = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.get('bounds', ''))
        need(match is not None, 'Actual control bounds missing')
        x, y, right, bottom = map(int, match.groups())
        need(0 <= x < right <= 1080 and 0 <= y < bottom <= 1920, 'Control outside reviewed display')
        return x, y, right, bottom

    def adb(self, args):
        self.runtime.check()
        self.actions += 1
        need(self.actions <= 120, 'Finite UI action count exceeded')
        value = self.runtime.adb(args)
        self.runtime.check()
        return value

    def tap(self, node, label):
        x, y, right, bottom = self.bounds(node)
        self.adb(['shell', 'input', 'tap', str((x + right) // 2), str((y + bottom) // 2)])
        self.runtime.sleep(1)
        self.refresh(label)

    def click(self, value, label, description=False):
        self.tap(self.one(value, description), label)

    def key_back(self, label):
        self.adb(['shell', 'input', 'keyevent', '4'])
        self.runtime.sleep(1)
        self.refresh(label)

    def scroll_to(self, value, anchor, limit=7, editable_below=False):
        for _ in range(limit):
            if self.find(value):
                heading_bottom = self.bounds(self.one(value))[3]
                if not editable_below or any(n.get('class') == 'android.widget.EditText'
                    and self.bounds(n)[1] > heading_bottom for n in self.nodes()):
                    return
            need(self.find(anchor) or self.find(anchor, True), 'Unrecognized screen; no blind scroll')
            regions = [n for n in self.nodes() if n.get('scrollable') == 'true']
            need(len(regions) == 1, 'Exactly one known scroll region required')
            x, y, right, bottom = self.bounds(regions[0])
            center = (x + right) // 2
            self.adb(['shell', 'input', 'swipe', str(center), str(y + (bottom-y)*4//5),
                      str(center), str(y + (bottom-y)//4), '350'])
            self.runtime.sleep(1)
            self.refresh('known-scroll')
        need(bool(self.find(value)), 'Expected control absent after bounded scroll: ' + value)

    def input_text(self, value, label):
        need(value in (self.public_nsec, URL), 'Only fixed public synthetic identity/local URL may be typed')
        if value == self.public_nsec:
            field, button, shown = self.identity_visibility()
            need(shown, 'Public identity must be visibly unmasked before typing')
            before_input = self.current
            before_subject = self.identity_control_subject(field, button)
            before_password = field.get('password')
        self.adb(['shell', 'input', 'text', value])
        self.refresh(label)
        if value == self.public_nsec:
            field, button, shown = self.identity_visibility()
            need(shown, 'Public identity must remain visibly unmasked after typing')
            need(self.identity_control_subject(field, button) == before_subject,
                 'Identity field structure changed across public input')
        edits = [n for n in self.nodes() if n.get('class') == 'android.widget.EditText' and n.get('text') == value]
        need(len(edits) == 1, 'Actual input field must contain the whole intended value')
        if value == self.public_nsec:
            self.runtime.put_json('evidence/public-identity-visibility.json', {
                'schema': 'e02-source-bound-public-identity-visibility-v1',
                'amethystCommit': 'e6f464a1179def75274512b3c5bab921de3bf3d8',
                'keyTextFieldSourceSha256': 'a2b40ef8dbbe401397148e1e05e0557eba3d5a55592603948620363da7795b74',
                'sourceMapping': 'Show Password/VisibilityOff means showCharsKey=true and VisualTransformation.None in this exact pinned client.',
                'beforeInput': before_input, 'afterInput': self.current,
                'fieldStructuralSubject': before_subject,
                'beforeAccessibilityPassword': before_password,
                'afterAccessibilityPassword': field.get('password'),
                'afterEyeDescription': 'Show Password', 'wholePublicNsecObserved': True,
                'limits': ['Accessibility password metadata is retained and typed-checked, not treated alone as visual-mask proof.',
                           'Full-value XML equality and source-bound eye state are required; actual fresh post-input PNG still needs independent visual review.',
                           'Field geometry is validated on every capture; IME or multiline reflow is not a change of structural field identity.']})
        if any('inputmethod' in n.get('package', '') for n in self.nodes()):
            self.key_back('keyboard-dismissed')
            if value == self.public_nsec:
                field, button, shown = self.identity_visibility()
                need(shown and self.identity_control_subject(field, button) == before_subject
                     and field.get('text') == self.public_nsec,
                     'Whole visible public identity must survive keyboard dismissal')

    def identity_controls(self):
        """Recognize the actual login field and its unique descendant visibility button."""
        for label in ('Adjust Tor Settings', 'Login'):
            control = self.one(label)
            need(control.get('package') == APP and control.get('enabled') == 'true',
                 'Recognized current Amethyst login required')
        edits = [n for n in self.nodes() if n.get('class') == 'android.widget.EditText']
        need(len(edits) == 1, 'Fresh single login field required')
        field = edits[0]
        need(field.get('package') == APP and field.get('enabled') == 'true'
             and field.get('password') in ('true', 'false'), 'Known actual login password state required')
        self.bounds(field)
        eyes = self.find('Show Password', True) + self.find('Hide Password', True)
        need(len(eyes) == 1, 'Unique known identity visibility eye required')
        eye = eyes[0]
        descendants = list(field.iter('node'))
        need(eye in descendants and eye.get('class') == 'android.view.View'
             and all(n.get('package') == APP and n.get('enabled') == 'true' for n in descendants),
             'Identity eye must belong to the enabled Amethyst login field')
        parents = [n for n in descendants if n is not field and n.get('clickable') == 'true'
                   and eye in list(n.iter('node'))]
        need(len(parents) == 1 and parents[0].get('class') == 'android.view.View',
             'Unique current identity eye button ancestry required')
        button = parents[0]
        children = list(button)
        blanks = [n for n in children if n.get('class') == 'android.widget.Button' and not n.get('text')]
        need(len(children) == 2 and eye in children and len(blanks) == 1,
             'Known identity eye button structure required')
        left, top, right, bottom = self.bounds(eye)
        for container in (field, button):
            x, y, control_right, control_bottom = self.bounds(container)
            need(x <= left < right <= control_right and y <= top < bottom <= control_bottom,
                 'Identity eye outside actual login field/button bounds')
        return field, button

    def identity_visibility(self):
        """Source-specific shown state; unconditional password semantics are not masking."""
        field, button = self.identity_controls()
        eyes = [n for n in list(button) if n.get('content-desc') in ('Show Password', 'Hide Password')]
        need(len(eyes) == 1, 'Unique source-bound identity eye state required')
        shown = eyes[0].get('content-desc') == 'Show Password'
        need(field.get('password') == 'true' or shown,
             'Contradictory identity password metadata and source-bound hidden eye state')
        return field, button, shown

    def identity_control_subject(self, field, button):
        """Closed semantic field/eye shape; no persistent object identity or position."""
        keys = ('class', 'package', 'resource-id')
        return {'field': {key: field.get(key, '') for key in keys},
                'button': {key: button.get(key, '') for key in keys},
                'children': [{key: child.get(key, '') for key in keys} for child in list(button)]}

    def visible_identity_field(self):
        field, eye_button, shown = self.identity_visibility()
        if not shown:
            need(self.identity_visibility_toggles < 1 and self.serial < 140 and self.actions < 120,
                 'Finite identity visibility/capture/action budget exhausted')
            before_subject = self.identity_control_subject(field, eye_button)
            self.identity_visibility_toggles += 1
            # This exact source uses Show Password/VisibilityOff for its shown
            # state, while retaining unconditional password keyboard semantics.
            self.tap(eye_button, 'public-identity-visible')
            field, eye_button, shown = self.identity_visibility()
            need(self.identity_control_subject(field, eye_button) == before_subject,
                 'Identity field structure changed across visibility action')
        need(shown, 'Identity remains masked after one visibility action; refuse')
        return field


def login(ui):
    ui.tor_popup_allowed = True
    ui.environment_anr_allowed = True
    try:
        return _login(ui)
    finally:
        ui.tor_popup_allowed = False
        ui.environment_anr_allowed = False


def _login(ui):
    need(ui.adb(['shell', 'pm', 'clear', APP]).strip() == b'Success', 'Fresh app clear did not succeed')
    ui.adb(['shell', 'am', 'start', '-W', '-n', APP_COMPONENT])
    ui.refresh('login-start')
    for _ in range(6):
        if ui.find('Adjust Tor Settings'):
            break
        ui.runtime.sleep(1)
        ui.refresh('login-settle')
    ui.click('Adjust Tor Settings', 'privacy-options')
    heading = ui.one('Active Tor Engine')
    center = sum(ui.bounds(heading)[1::2]) // 2
    spinners = [n for n in ui.nodes() if n.get('class') == 'android.widget.Spinner']
    candidates = [n for n in spinners if abs(sum(ui.bounds(n)[1::2])//2 - center) <= 100]
    need(len(candidates) == 1, 'Unique Tor selector in actual labeled row required')
    ui.tap(candidates[0], 'tor-engine-menu')
    need(ui.find('Internal') and ui.find('Orbot'), 'Expected Tor choices required')
    ui.click('Off', 'tor-off-selected')
    need(ui.find('Privacy Options') and ui.find('Active Tor Engine'), 'Tor selection must return to actual settings')
    selected_tor = ui.current
    ui.click('Save', 'login-tor-saved')
    need(ui.find('Adjust Tor Settings') and ui.find('Login'), 'Explicit Tor Save must return to actual login')
    first_save = ui.current
    ui.click('Adjust Tor Settings', 'tor-saved-state-reopened')
    need(ui.find('Privacy Options') and ui.find('Active Tor Engine'), 'Saved Tor settings must reopen explicitly')
    saved_tor = ui.current
    ui.click('Save', 'tor-saved-state-closed')
    need(ui.find('Adjust Tor Settings') and ui.find('Login'), 'Saved Tor settings must return to actual login')
    tor_evidence = ui.runtime.put_json('evidence/tor-configuration-gui.json', {
        'schema': 'e02-tor-configuration-gui-v1', 'selectedOff': selected_tor,
        'firstSaveReturnedToLogin': first_save, 'savedStateReopened': saved_tor,
        'secondSaveReturnedToLogin': ui.current, 'torFailureDismissals': ui.tor_dismissals,
        'limits': ['The actual XML exposes an unlabeled Tor spinner, not its persisted value.',
                   'The reopened saved-state PNG requires independent visual Off verification.',
                   'GUI configuration is not network-isolation evidence.']})
    ui.tap(ui.visible_identity_field(), 'login-field-focused')
    ui.input_text(ui.public_nsec, 'whole-disposable-identity')
    ui.click('Login', 'login-submitted')
    for _ in range(8):
        if ui.find('Your Profile Picture', True):
            return tor_evidence
        ui.runtime.sleep(1)
        ui.refresh('login-await-home')
    raise ValueError('No recognized logged-in home; refuse further actions')


def own_identity(ui):
    ui.click('Your Profile Picture', 'account-drawer', True)
    ui.click('Profile', 'own-profile')
    ui.click('More Options', 'own-profile-actions', True)
    ui.click('Share', 'own-public-share')
    preview = ui.current
    observed = [n.get('text') for n in ui.nodes() if 'nprofile1' in n.get('text', '')]
    need(bool(observed), 'Actual public nprofile GUI preview required')
    ui.key_back('share-closed')
    ui.key_back('profile-closed')
    return {'preview': preview, 'observedPublicProfileText': observed,
            'meaning': 'Actual share GUI retained for independent public-key decoding; no share target opened.'}


def expanded_feeds_header(ui):
    """Exact observed two-child header and same-section expanded anchors only."""
    labels = ui.find('Feeds')
    if not labels:
        return None
    need(len(labels) == 1, 'Unique current Feeds label required')
    label = labels[0]
    parents = [n for n in ui.nodes() if label in list(n)]
    need(len(parents) == 1, 'Direct Feeds header ownership required')
    header = parents[0]
    children = list(header)
    icons = [n for n in children if n.get('content-desc') == 'Feeds' and not n.get('text')]
    need(header.get('class') == 'android.view.View' and header.get('clickable') == 'true'
         and len(children) == 2 and label in children and len(icons) == 1
         and label.get('class') == 'android.widget.TextView'
         and all(n.get('package') == APP and n.get('enabled') == 'true' for n in (header, label, icons[0])),
         'Known enabled Amethyst Feeds header structure required')
    sections = [n for n in ui.nodes() if header in list(n)]
    need(len(sections) == 1, 'Unique actual Feeds section owner required')
    section = sections[0]
    need(section.get('class') == 'android.view.View' and section.get('package') == APP
         and section.get('enabled') == 'true', 'Known actual Feeds section required')
    # The observed section clips its header by2px. Do not demand full enclosure.
    expanded = []
    for title in ('Reads', 'Pictures'):
        anchors = [n for n in section.iter('node') if n.get('text') == title]
        need(len(anchors) <= 1, 'Ambiguous same-section expanded Feeds anchor')
        if not anchors:
            return None  # No asserted expanded/collapsed state from a clipped viewport.
        need(anchors[0].get('package') == APP and anchors[0].get('enabled') == 'true',
             'Foreign or disabled same-section Feeds anchor')
        expanded.append(anchors[0])
    regions = [n for n in ui.nodes() if n.get('scrollable') == 'true']
    need(len(regions) == 1 and regions[0].get('class') == 'android.widget.ScrollView'
         and regions[0].get('package') == APP and section in list(regions[0].iter('node')),
         'Known sole drawer ScrollView ownership required')
    x, y, right, bottom = ui.bounds(header)
    sx, sy, sr, sb = ui.bounds(regions[0])
    need(sx <= (x + right) // 2 < sr and sy <= (y + bottom) // 2 < sb,
         'Actual Feeds click centre outside current drawer viewport')
    for child in children:
        left, top, cr, cb = ui.bounds(child)
        need(x <= left < cr <= right and y <= top < cb <= bottom,
             'Feeds header child outside actual clickable header')
    return header


def seek_system(ui):
    """One known Feeds collapse within original seven scroll attempts."""
    collapsed = False
    for _ in range(7):
        if ui.find('System'):
            return
        need(ui.find('Close navigation menu', True), 'Known drawer anchor required before System seek')
        if not collapsed:
            header = expanded_feeds_header(ui)
            if header is not None:
                before = ui.current
                collapsed = True
                ui.tap(header, 'feeds-collapsed-once')
                ui.runtime.put_json('evidence/feeds-collapse-gui.json', {
                    'schema': 'e02-minimum-feeds-collapse-gui-v1', 'before': before, 'after': ui.current,
                    'actions': 1, 'meaning': 'Known expanded section toggled once; no invented collapsed accessibility attribute.',
                    'limits': 'Actual System and Relays still required. Planned source-backed procedure, no global scroll/action/lease increase.'})
                if ui.find('System'):
                    return
        regions = [n for n in ui.nodes() if n.get('scrollable') == 'true']
        need(len(regions) == 1 and regions[0].get('package') == APP,
             'Exactly one current Amethyst drawer scroll region required')
        x, y, right, bottom = ui.bounds(regions[0])
        center = (x + right) // 2
        ui.adb(['shell', 'input', 'swipe', str(center), str(y + (bottom-y)*4//5),
                str(center), str(y + (bottom-y)//4), '350'])
        ui.runtime.sleep(1)
        ui.refresh('system-seek-scroll')
    need(bool(ui.find('System')), 'Expected control absent after bounded System seek')


def local_relay_field(ui, expected_text=None):
    known_control(ui, 'Relay Settings')
    heading = known_control(ui, 'Local Relays')
    threshold = ui.bounds(heading)[3]
    candidates = [n for n in ui.nodes() if n.get('class') == 'android.widget.EditText'
                  and ui.bounds(n)[1] > threshold]
    need(bool(candidates), 'Actual Local Relays editor must be visible below its heading')
    field = min(candidates, key=lambda n: ui.bounds(n)[1])
    need(field.get('package') == APP and field.get('enabled') == 'true', 'Owned Local Relays editor required')
    for title in ('Trusted Relays', 'Search Relays', 'Indexer Relays'):
        need(not any(threshold < ui.bounds(n)[1] < ui.bounds(field)[1] for n in ui.find(title)),
             'Different relay section lies before selected Local editor')
    labels = [n for n in field.iter('node') if n.get('text') == 'Add a Relay']
    need(len(labels) == 1 and labels[0].get('package') == APP and labels[0].get('enabled') == 'true',
         'Exact source-backed Add a Relay field ownership required')
    if expected_text is not None:
        need(field.get('text') == expected_text, 'Expected exact Local Relays editor value missing')
    return field


def local_relay_add_button(ui):
    field = local_relay_field(ui, URL)
    adds = [n for n in field.iter('node') if n.get('text') == 'Add']
    need(len(adds) == 1 and adds[0].get('package') == APP and adds[0].get('enabled') == 'true',
         'Only Add inside exact Local URL field may be used')
    buttons = [n for n in field.iter('node') if n is not field and n.get('clickable') == 'true'
               and adds[0] in list(n.iter('node'))]
    need(len(buttons) == 1 and buttons[0].get('class') in ('android.view.View', 'android.widget.Button')
         and buttons[0].get('package') == APP and buttons[0].get('enabled') == 'true',
         'Unique current trailing Local Add button ancestry required')
    button = buttons[0]
    x, y, right, bottom = ui.bounds(button)
    fx, fy, fr, fb = ui.bounds(field)
    need(fx <= (x+right)//2 < fr and fy <= (y+bottom)//2 < fb,
         'Actual Local Add centre outside current URL field')
    return button


def local_relay(ui):
    ui.click('Your Profile Picture', 'relay-drawer', True)
    seek_system(ui)
    if not ui.find('Relays'):
        ui.tap(known_control(ui, 'System'), 'system-expanded')
    ui.scroll_to('Relays', 'Close navigation menu')
    ui.tap(known_control(ui, 'Relays'), 'relay-settings')
    known_control(ui, 'Relay Settings')
    ui.scroll_to('Local Relays', 'Relay Settings', editable_below=True)
    ui.tap(local_relay_field(ui, ''), 'local-relay-field')
    ui.input_text(URL, 'local-relay-url')
    ui.tap(local_relay_add_button(ui), 'local-relay-added')
    field = local_relay_field(ui, '')
    heading = known_control(ui, 'Local Relays')
    top, bottom = ui.bounds(heading)[3], ui.bounds(field)[1]
    rows = [n for n in ui.find('localhost:17777') if top <= ui.bounds(n)[1] < ui.bounds(n)[3] <= bottom]
    need(len(rows) == 1 and rows[0].get('package') == APP and rows[0].get('enabled') == 'true',
         'Actual newly added LOCAL displayURL row required before its own footer')
    ui.runtime.put_json('evidence/local-relay-gui.json', {
        'schema': 'e02-minimum-local-relay-gui-v1', 'afterAdd': ui.current,
        'localDisplayUrl': 'localhost:17777', 'editorCleared': True,
        'meaning': 'Local list row/editor GUI only; later actual subscription/EOSE/wire still required.'})
    ui.tap(known_control(ui, 'Save'), 'local-relay-saved')


def helper(ui, action, case_id):
    need(case_id in ui.role_spec['stages'] and action in ('CLEAR', 'CAPTURE'), 'Closed role helper operation required')
    ui.adb(['shell', 'am', 'start', '-W', '-n', HELPER_COMPONENT, '--es', 'caseId', case_id])
    ui.refresh('helper-' + action.lower())
    ui.click('Clear clipboard' if action == 'CLEAR' else 'Capture clipboard', 'helper-' + action.lower() + '-result')
    suffix = '.clear.json' if action == 'CLEAR' else '.receipt.json'
    raw = ui.adb(['exec-out', 'run-as', HELPER, 'cat', 'files/captures/' + case_id + suffix])
    value = loads(raw)
    need(value['schema'] == 'e02-clipboard-capture-v1' and value['caseId'] == case_id
         and value['action'] == action and value['foregroundFocus'] is True, 'Actual focused helper receipt required')
    descriptor = ui.runtime.put_bytes('evidence/' + case_id + '/helper-' + action.lower() + '.json', raw)
    return value, descriptor


def known_control(ui, value, description=False):
    control = ui.one(value, description)
    need(control.get('package') == APP and control.get('enabled') == 'true',
         'Unique enabled current Amethyst control required: ' + value)
    ui.bounds(control)
    return control


def chat_context(ui, token='NBDP/experiment'):
    known_control(ui, 'Back', True)
    need(token in ('NBDP/experiment', 'NBDP harmless ordinary chat control'), 'Closed actual note anchor required')
    notes = ui.find(token, contains=True)
    need(bool(notes) and all(n.get('package') == APP and n.get('enabled') == 'true' for n in notes),
         'Actual expected note required in the known private room')
    # Calling and composer availability are conditional in the pinned source.
    warning = 'DM inbox relays not found. Messages cannot be delivered until they configure their relay list.'
    labels, warnings = ui.find('Message'), ui.find(warning)
    need(not (labels and warnings), 'Ambiguous private-room footer states')
    if warnings:
        need(len(warnings) == 1 and warnings[0].get('package') == APP
             and warnings[0].get('enabled') == 'true', 'Known missing-recipient-inbox footer required')
        ui.bounds(warnings[0])
        return 'RECIPIENT_DM_RELAYS_WARNING_READ_ONLY'
    need(len(labels) == 1 and labels[0].get('package') == APP and labels[0].get('enabled') == 'true',
         'Known source-backed private-message footer required')
    fields = [n for n in ui.nodes() if n.get('class') == 'android.widget.EditText'
              and labels[0] in list(n.iter('node'))]
    need(len(fields) == 1 and fields[0].get('package') == APP and fields[0].get('enabled') == 'true'
         and not fields[0].get('text'), 'Private chat composer ownership/empty state required')
    ui.bounds(fields[0])
    return 'EMPTY_COMPOSER_READ_ONLY'


def open_messages(ui):
    ui.tap(known_control(ui, 'Messages', True), 'minimum-messages')
    known_control(ui, 'Known')
    known_control(ui, 'New Requests')
    ui.tap(known_control(ui, ui.role_spec['tab']), 'minimum-role-tab')


def wait_subscription(ui, stage_id):
    for _ in range(20):
        status = fixture(ui.runtime, 'status')
        need(status['stageId'] == stage_id and status['windowId'] == ui.role_spec['windowId'],
             'Exact next role stage subscription status required')
        if status['ready'] is True:
            call, call_pin = ui.runtime._minimum_last_fixture_call
            return {'result': status, 'rawReply': call['reply'], 'call': call_pin, 'command': call['command']}
        ui.runtime.sleep(2)
    raise ValueError('No current matching app1059#p/EOSE; nothing published')


def select_note(ui, token, replay):
    chat_context(ui, token)
    notes = ui.find(token, contains=True)
    need(1 <= len(notes) <= (3 if replay else 1), 'Bounded actual selected-note match count required')
    need(all(n.get('package') == APP and n.get('enabled') == 'true' for n in notes),
         'Actual selected notes must belong to enabled Amethyst')
    rows = [(ui.bounds(n), n) for n in notes]
    lowest = max(bounds[3] for bounds, _ in rows)
    selected = [node for bounds, node in rows if bounds[3] == lowest]
    need(len(selected) == 1, 'Unique actual lowest matching note required; no ambiguous duplicate fallback')
    return selected[0], [{'bounds': list(bounds), 'text': node.get('text')} for bounds, node in rows]


def export_note(ui, stage, token, expected):
    case_id = stage['id']
    cleared, clear_pin = helper(ui, 'CLEAR', case_id)
    need(cleared['status'] == 'EMPTY_SENTINEL_SET', 'Guest clipboard was not cleared')
    ui.key_back('minimum-return-selected')
    note, visible_nodes = select_note(ui, token, stage['index'] > 0 and ui.ordinary_role == 'archive')
    selected = ui.current
    x, y, right, bottom = ui.bounds(note)
    cx, cy = (x+right)//2, (y+bottom)//2
    ui.adb(['shell', 'input', 'swipe', str(cx), str(cy), str(cx), str(cy), '700'])
    ui.refresh('minimum-message-actions')
    ui.tap(known_control(ui, 'More Options'), 'minimum-expanded-actions')
    ui.tap(known_control(ui, 'Copy raw JSON'), 'minimum-copy-raw')
    captured, helper_pin = helper(ui, 'CAPTURE', case_id)
    need(captured['status'] == 'CAPTURED' and captured['mime'] == 'text/plain'
         and captured['clipboardItemCount'] == 1 and captured['clipboardTimestamp'] >= cleared['wallClockMillis'],
         'Fresh real selected-note clipboard custody required')
    raw = ui.adb(['exec-out', 'run-as', HELPER, 'cat', 'files/captures/' + case_id + '.raw.json'])
    need(len(raw) <= 65536 and captured['bytes'] == len(raw)
         and captured['sha256'] == hashlib.sha256(raw).hexdigest(), 'Whole raw UTF8 custody required')
    exported = loads(raw)
    if type(exported) is dict and set(exported) == set(expected) | {'sig'}:
        need(type(exported['sig']) is str and exported['sig'] == '', 'Only empty unsigned export sig permitted')
        exported = {key: value for key, value in exported.items() if key != 'sig'}
    need(equal(exported, expected), 'Actual client export differs from frozen whole six-field inner rumor')
    raw_pin = ui.runtime.put_bytes('evidence/' + case_id + '/client-raw-rumor.json', raw)
    selection = ui.runtime.put_json('evidence/' + case_id + '/selection.json', {
        'schema': 'e02-minimum-selection-v1', 'profileId': PROFILE, 'windowId': ui.role_spec['windowId'],
        'observationId': case_id, 'account': ui.role_spec['account'], 'peer': ui.role_spec['peer'],
        'originalAuthor': expected['pubkey'], 'originalOrderedTags': expected['tags'], 'rumorId': expected['id'],
        'action': 'COPY_RAW_JSON', 'method': 'ANDROID_LOCAL_FOREGROUND', 'helperPackage': HELPER,
        'helperArtifact': ui.runtime.plan['helperApk'], 'helperReceipt': helper_pin,
        'capturedMonotonicNs': time.monotonic_ns(), 'selectedGui': selected,
        'matchingVisibleTextNodes': visible_nodes,
        'limits': 'Visible text-node matches are not global bubble counts or measured business effects. Shape and screen coordinates are not persistent object identities.'})
    return {'id': case_id, 'state': 'EXPORTED_PENDING_INDEPENDENT_WHOLE_RUN_REVIEW',
            'selection': selection, 'uiPng': selected['png'], 'uiXml': selected['xml'],
            'rawClientRumor': raw_pin, 'clipboardClear': clear_pin,
            'visibleMatchingTextNodeCount': len(visible_nodes),
            'duplicateObservation': {'scope': 'CURRENT_VISIBLE_MATCHING_TEXT_NODES_ONLY',
                'visibleMatchingTextNodeCount': len(visible_nodes),
                'globalDuplicateBubbleCount': None, 'globalDuplicateBubbleCountStatus': 'UNKNOWN_UNMEASURED',
                'businessEffectsMeasured': False}}


def map_guest_graph(runtime, value, bindings):
    if type(value) is dict:
        if set(value) == {'path', 'bytes', 'sha256'} and value['path'].startswith('/session/fixtures/'):
            mapped_pin = mapped(runtime, value)
            prior = [row for row in bindings if row['guest']['path'] == value['path']]
            need(not prior or equal(prior[0], {'guest': value, 'host': mapped_pin}), 'Divergent guest/host descriptor alias')
            if not prior:
                bindings.append({'guest': value, 'host': mapped_pin})
            return
        for item in value.values():
            map_guest_graph(runtime, item, bindings)
    elif type(value) is list:
        for item in value:
            map_guest_graph(runtime, item, bindings)


def run(runtime):
    runtime.check()
    plan = loads((HERE / 'ui-plan.json').read_bytes())
    role = runtime.plan['ordinaryRole']
    need(role in ROLE_SPECS and runtime.plan['profileId'] == PROFILE and plan['profileId'] == PROFILE,
         'Exact minimum role profile required')
    spec = ROLE_SPECS[role]
    need(runtime.plan['windowId'] == spec['windowId'] and runtime.plan['account'] == spec['account']
         and runtime.plan['peer'] == spec['peer'] and plan['localRelay'] == URL,
         'One fixed account/peer per fresh role window required')
    prepared = fixture(runtime, 'prepare')
    need(prepared['windowId'] == spec['windowId'] and prepared['ordinaryRole'] == role
         and set(prepared['expected']) == set(spec['stages']), 'Exact frozen role-stage expectations required')
    ui = UI(runtime)
    tor_ui = login(ui)
    account_ui = own_identity(ui)
    local_relay(ui)
    open_messages(ui)
    need(not ui.find(plan['businessVisibleToken'], contains=True)
         and not ui.find(plan['chatVisibleToken'], contains=True), 'Fresh role already contains declared inputs')
    observations = []
    for index, stage_id in enumerate(spec['stages']):
        command_start, ui_start, action_start = runtime.sequence + 1, ui.serial, ui.actions
        expected_pin = mapped(runtime, prepared['expected'][stage_id]['rumor'])
        expected = loads(read(expected_pin))
        need(set(expected) == {'id', 'pubkey', 'created_at', 'kind', 'tags', 'content'}
             and expected['pubkey'] == PEER and expected['kind'] == 14 and expected['tags'] == [['p', ACCOUNT]],
             'Original shared authorA/innerpB must remain unchanged in both role windows')
        token = plan['chatVisibleToken'] if stage_id == 'incoming-ordinary-chat' else plan['businessVisibleToken']
        need(token in expected['content'], 'Frozen actual note token missing')
        if index:
            ui.key_back('minimum-return-thread')
            chat_context(ui)
        status = wait_subscription(ui, stage_id)
        published = fixture(runtime, 'publish')
        stage = published['stage']
        need(stage['id'] == stage_id and stage['index'] == index
             and published['windowId'] == spec['windowId'], 'Ordered finite role stage required')
        for _ in range(12):
            ui.refresh('minimum-await-note')
            if ui.find(token, contains=True):
                break
            runtime.sleep(2)
        else:
            raise ValueError('Expected actual minimum note not rendered')
        if index == 0:
            previews = ui.find(token, contains=True)
            need(len(previews) == 1 and previews[0].get('package') == APP
                 and previews[0].get('enabled') == 'true', 'Unique actual fresh role conversation preview required')
            ui.tap(previews[0], 'minimum-actual-conversation')
            chat_context(ui, token)
        observation = export_note(ui, stage, token, expected)
        bindings = []
        map_guest_graph(runtime, published, bindings)
        publication = mapped(runtime, published['publication'])
        publication_record = loads(read(publication, 16777216))
        map_guest_graph(runtime, publication_record, bindings)
        need(publication_record['stage']['id'] == stage_id and publication_record['windowId'] == spec['windowId'],
             'Actual publication graph must match selected stage')
        observation.update(expectedRumor=expected_pin, publication=publication,
            actualNewAppFrameObserved=published['actualNewAppFrameObserved'],
            originalGuestToHostBindings=bindings, subscriptionStatus=status['result'],
            subscriptionStatusReply=status['rawReply'], subscriptionStatusCall=status['call'],
            subscriptionStatusCommand=status['command'], custodySegment={
                'commandSequenceFirst': command_start, 'commandSequenceLast': runtime.sequence,
                'uiCaptureSerialFirst': ui_start + 1, 'uiCaptureSerialLast': ui.serial,
                'uiActionCountBefore': action_start, 'uiActionCountAfter': ui.actions,
                'uiCaptures': ui.captures[ui_start:ui.serial]})
        observations.append(observation)
    runtime.check()
    return {'schema': 'e02-minimum-role-driver-result-v2', 'profileId': PROFILE,
        'windowId': spec['windowId'], 'ordinaryRole': role, 'runId': runtime.plan['runId'],
        'runConfig': runtime.plan_pin, 'runRelease': runtime.release_pin, 'executionState': 'PARTIAL',
        'accountIdentityGUI': account_ui, 'expectedAccountPubkey': spec['account'],
        'accountIdentityQualification': 'ACTUAL_NPROFILE_INDEPENDENT_DECODE_AND_REVIEW_REQUIRED',
        'torConfigurationGUI': tor_ui, 'environmentAnrEvidence': ui.environment_anr_evidence,
        'allUICaptures': ui.captures, 'fixtureCalls': runtime._minimum_fixture_calls, 'observations': observations,
        'limits': ['One complete fresh role window only; root-owned new consumer and second window/current primary workload still required.',
            'Identical replay may have no new app EVENT; retain honest absence/query lineage and actual post-replay client export.',
            'No business-effect measurement is inferred from primary dispatch eligibility or UI duplicate text nodes.',
            'No canonicalPASS, eight-profile reinterpretation, blocker closure or automatic row donation.'],
        'canonicalE02Changed': False}
