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
CASE = 'js-to-rust-incoming-rs'
NSEC = 'nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqpqptcfk2'
ACCOUNT = 'c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5'
PEER = '79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
URL = 'ws://localhost:17777'
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
    runtime.put_bytes('evidence/fixture-' + operation + '-reply.json', raw)
    value = loads(raw)
    need(value['schema'] == 'e02-fixture-command-v1' and value['operation'] == operation
         and value['caseId'] == CASE and value['ok'] is True, 'Exact successful fixture operation required')
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
        need(value in (NSEC, URL), 'Only fixed public synthetic identity/local URL may be typed')
        if value == NSEC:
            field, button, shown = self.identity_visibility()
            need(shown, 'Public identity must be visibly unmasked before typing')
            before_input = self.current
            before_subject = self.identity_control_subject(field, button)
            before_password = field.get('password')
        self.adb(['shell', 'input', 'text', value])
        self.refresh(label)
        if value == NSEC:
            field, button, shown = self.identity_visibility()
            need(shown, 'Public identity must remain visibly unmasked after typing')
            need(self.identity_control_subject(field, button) == before_subject,
                 'Identity field structure changed across public input')
        edits = [n for n in self.nodes() if n.get('class') == 'android.widget.EditText' and n.get('text') == value]
        need(len(edits) == 1, 'Actual input field must contain the whole intended value')
        if value == NSEC:
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
            if value == NSEC:
                field, button, shown = self.identity_visibility()
                need(shown and self.identity_control_subject(field, button) == before_subject
                     and field.get('text') == NSEC,
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
    ui.input_text(NSEC, 'whole-disposable-identity')
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


def local_relay(ui):
    ui.click('Your Profile Picture', 'relay-drawer', True)
    ui.scroll_to('System', 'Close navigation menu')
    if not ui.find('Relays'):
        ui.click('System', 'system-expanded')
    ui.scroll_to('Relays', 'Close navigation menu')
    ui.click('Relays', 'relay-settings')
    ui.scroll_to('Local Relays', 'Relay Settings', editable_below=True)
    heading = ui.one('Local Relays')
    threshold = ui.bounds(heading)[3]
    below = [n for n in ui.nodes() if n.get('class') == 'android.widget.EditText' and ui.bounds(n)[1] > threshold]
    need(bool(below), 'Local relay field must be visible below its heading')
    field = min(below, key=lambda n: ui.bounds(n)[1])
    for other in ('Trusted Relays', 'Search Relays', 'Indexer Relays'):
        for node in ui.find(other):
            need(not threshold < ui.bounds(node)[1] < ui.bounds(field)[1], 'Adjacent relay section is not Local Relays')
    ui.tap(field, 'local-relay-field')
    ui.input_text(URL, 'local-relay-url')
    field = next(n for n in ui.nodes() if n.get('class') == 'android.widget.EditText' and n.get('text') == URL)
    center = sum(ui.bounds(field)[1::2]) // 2
    adds = [n for n in ui.find('Add') if abs(sum(ui.bounds(n)[1::2])//2 - center) <= 100]
    need(len(adds) == 1, 'Only Add in actual Local Relays row may be used')
    ui.tap(adds[0], 'local-relay-added')
    need(ui.find('localhost:17777') or ui.find('Relay localhost:17777', True), 'Actual local relay row missing')
    ui.click('Save', 'local-relay-saved')
    ui.click('Messages', 'messages', True)
    ui.click('New Requests', 'new-requests')


def helper(ui, action):
    ui.adb(['shell', 'am', 'start', '-W', '-n', HELPER_COMPONENT, '--es', 'caseId', CASE])
    ui.refresh('helper-' + action.lower())
    ui.click('Clear clipboard' if action == 'CLEAR' else 'Capture clipboard', 'helper-' + action.lower() + '-result')
    suffix = '.clear.json' if action == 'CLEAR' else '.receipt.json'
    raw = ui.adb(['exec-out', 'run-as', HELPER, 'cat', 'files/captures/' + CASE + suffix])
    value = loads(raw)
    need(value['schema'] == 'e02-clipboard-capture-v1' and value['caseId'] == CASE
         and value['action'] == action and value['foregroundFocus'] is True, 'Actual focused helper receipt required')
    descriptor = ui.runtime.put_bytes('evidence/helper-' + action.lower() + '.json', raw)
    return value, descriptor


def run(runtime):
    runtime.check()
    plan = loads((HERE / 'ui-plan.json').read_bytes())
    need(plan['caseId'] == CASE and plan['account'] == ACCOUNT and plan['peer'] == PEER
         and plan['localRelay'] == URL and plan['scope'] == 'ONE_REAL_ENVELOPE_FIRST_SLICE_ONLY', 'Fixed UI slice required')
    prepared = fixture(runtime, 'prepare')
    expected_pin = mapped(runtime, prepared['expectedRumor'])
    expected = loads(read(expected_pin))
    content_pin = mapped(runtime, prepared['expectedContent'])
    need(read(content_pin).decode('utf-8') == expected['content'] and expected['pubkey'] == PEER
         and expected['kind'] == 14 and expected['tags'] == [['p', ACCOUNT]], 'Canonical incoming envelope subject required')
    need(plan['visibleToken'] in expected['content'], 'Actual envelope must contain the declared UI token')
    ui = UI(runtime)
    tor_ui = login(ui)
    account_ui = own_identity(ui)
    local_relay(ui)
    need(not ui.find(plan['visibleToken'], contains=True), 'Fresh input already rendered before publication')
    for _ in range(20):
        status_raw = runtime.fixture('status')
        status = loads(status_raw)
        need(status['schema'] == 'e02-fixture-command-v1' and status['operation'] == 'status'
             and status['ok'] is True and status['caseId'] == CASE, 'Exact live subscription status required')
        if status['result']['ready'] is True:
            runtime.put_bytes('evidence/subscription-status.json', status_raw)
            break
        runtime.sleep(2)
    else:
        raise ValueError('No actual matching app REQ/EOSE; nothing published')
    published = fixture(runtime, 'publish')
    for _ in range(12):
        ui.refresh('await-real-envelope')
        if ui.find(plan['visibleToken'], contains=True):
            break
        runtime.sleep(2)
    else:
        raise ValueError('Actual envelope was not rendered')
    previews = ui.find(plan['visibleToken'], contains=True)
    need(len(previews) == 1, 'Unique current incoming conversation preview required')
    ui.tap(previews[0], 'actual-conversation')
    need(ui.find('Back', True) and ui.find('Voice call', True), 'Recognized chat conversation required')
    cleared, clear_pin = helper(ui, 'CLEAR')
    need(cleared['status'] == 'EMPTY_SENTINEL_SET', 'Guest clipboard was not cleared')
    ui.key_back('return-selected-note')
    selected = ui.current
    notes = ui.find(plan['visibleToken'], contains=True)
    need(len(notes) == 1, 'Select one real note, not cached/duplicate content')
    x, y, right, bottom = ui.bounds(notes[0])
    center_x, center_y = (x+right)//2, (y+bottom)//2
    ui.adb(['shell', 'input', 'swipe', str(center_x), str(center_y), str(center_x), str(center_y), '700'])
    ui.refresh('message-action-sheet')
    ui.click('More Options', 'expanded-message-actions')
    ui.click('Copy raw JSON', 'real-copy-raw-json')
    captured, helper_pin = helper(ui, 'CAPTURE')
    need(captured['status'] == 'CAPTURED' and captured['mime'] == 'text/plain'
         and captured['clipboardItemCount'] == 1 and captured['clipboardTimestamp'] >= cleared['wallClockMillis'], 'Fresh copied text required')
    raw = ui.adb(['exec-out', 'run-as', HELPER, 'cat', 'files/captures/' + CASE + '.raw.json'])
    need(len(raw) <= 65536 and captured['bytes'] == len(raw)
         and captured['sha256'] == hashlib.sha256(raw).hexdigest(), 'Whole captured UTF-8 custody required')
    exported = loads(raw)
    if type(exported) is dict and set(exported) == set(expected) | {'sig'}:
        need(type(exported['sig']) is str and exported['sig'] == '', 'Only empty unsigned export signature permitted')
        exported = {key: value for key, value in exported.items() if key != 'sig'}
    need(equal(exported, expected), 'Actual client export differs from expected whole inner rumor')
    raw_pin = runtime.put_bytes('evidence/client-raw-rumor.json', raw)
    transport_original = mapped(runtime, published['transport'])
    transport = loads(read(transport_original, 16777216))
    need(transport['schema'] == 'e02-ordinary-transport-v1', 'Actual received-wire transport proof required')
    transport = dict(transport, **{k: mapped(runtime, v) for k, v in transport.items() if k != 'schema'})
    transport_pin = runtime.put_json('evidence/transport-host-paths.json', transport)
    selection = runtime.put_json('evidence/selection.json', {
        'schema': 'e02-ordinary-selection-v1', 'observationId': CASE, 'account': ACCOUNT,
        'peer': PEER, 'rumorId': expected['id'], 'action': 'COPY_RAW_JSON',
        'method': 'ANDROID_LOCAL_FOREGROUND', 'helperPackage': HELPER,
        'helperArtifact': runtime.plan['helperApk'], 'helperReceipt': helper_pin,
        'capturedMonotonicNs': time.monotonic_ns()})
    runtime.check()
    return {'schema': 'e02-first-slice-driver-result-v1', 'runId': runtime.plan['runId'],
        'runConfig': runtime.plan_pin, 'runRelease': runtime.release_pin,
        'executionState': 'PARTIAL', 'accountIdentityGUI': account_ui,
        'torConfigurationGUI': tor_ui,
        'environmentAnrEvidence': ui.environment_anr_evidence,
        'expectedRumor': expected_pin, 'originalTransport': transport_original,
        'clipboardClear': clear_pin, 'allUICaptures': ui.captures,
        'observations': [{'id': CASE, 'status': 'COMPLETE', 'transport': transport_pin,
            'selection': selection, 'uiPng': selected['png'], 'uiXml': selected['xml'],
            'rawClientRumor': raw_pin, 'error': None}],
        'limits': ['One actual first slice only; seven proposed coverage rows remain missing.',
                   'GUI captures are sequential, not atomic. Account public profile needs independent decoding.',
                   'Ordinary JSON rendering/export is not a business-dispatch/approval capability.'],
        'canonicalE02Changed': False}
