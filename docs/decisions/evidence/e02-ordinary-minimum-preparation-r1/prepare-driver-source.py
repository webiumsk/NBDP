"""SOURCE-only closed role/UI extension; no project module import or execution."""
from pathlib import Path

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
BASE = ROOT / 'experiments/prototypes/e02_ordinary_client_api35_v3/android_driver.py'
OUT = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v1/android_driver.py'
text = BASE.read_text()
text = text.replace("CASE = 'js-to-rust-incoming-rs'", "CASE = 'minimum-two-role-rs'\nPROFILE = 'e02-ordinary-minimum-rs-two-role-v1'")
point = "URL = 'ws://localhost:17777'"
text = text.replace(point, point + """
ROLE_SPECS = {
    'incoming': {'windowId': 'incoming-b', 'account': ACCOUNT, 'peer': PEER,
        'nsec': NSEC, 'tab': 'New Requests',
        'stages': ('incoming-business', 'incoming-ordinary-chat')},
    'archive': {'windowId': 'archive-a', 'account': PEER, 'peer': ACCOUNT,
        'nsec': 'nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqsmhltgl',
        'tab': 'Known', 'stages': ('archive-business', 'archive-identical-replay', 'archive-fresh-wrap-replay')},
}
""")
text = text.replace('        self.runtime = runtime\n', """        self.runtime = runtime
        self.ordinary_role = runtime.plan['ordinaryRole']
        need(self.ordinary_role in ROLE_SPECS, 'Closed minimum account role required')
        self.role_spec = ROLE_SPECS[self.ordinary_role]
        self.public_nsec = self.role_spec['nsec']
""", 1)
a = text.index('    def input_text('); b = text.index('    def identity_controls(', a)
text = text[:a] + text[a:b].replace('NSEC', 'self.public_nsec') + text[b:]
text = text.replace("ui.input_text(NSEC, 'whole-disposable-identity')", "ui.input_text(ui.public_nsec, 'whole-disposable-identity')")
a = text.index('def fixture('); b = text.index('\ndef mapped(', a)
text = text[:a] + """def fixture(runtime, operation):
    runtime.check()
    raw = runtime.fixture(operation)
    sequence = getattr(runtime, '_minimum_fixture_sequence', 0) + 1
    runtime._minimum_fixture_sequence = sequence
    reply_pin = runtime.put_bytes('evidence/fixture-%02d-%s-reply.json' % (sequence, operation), raw)
    value = loads(raw)
    spec = ROLE_SPECS[runtime.plan['ordinaryRole']]
    need(value['schema'] == 'e02-minimum-fixture-command-v1' and value['operation'] == operation
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

""" + text[b:]
text = text.replace("    ui.scroll_to('System', 'Close navigation menu')", '    seek_system(ui)', 1)
text = text.replace("    ui.click('Messages', 'messages', True)\n    ui.click('New Requests', 'new-requests')\n", '')
text = text.replace("ui.click('System', 'system-expanded')", "ui.tap(known_control(ui, 'System'), 'system-expanded')")
text = text.replace("ui.click('Relays', 'relay-settings')", "ui.tap(known_control(ui, 'Relays'), 'relay-settings')")
a = text.index('def local_relay(')
text = text[:a] + """def expanded_feeds_header(ui):
    \"\"\"Exact observed two-child header and same-section expanded anchors only.\"\"\"
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
    \"\"\"One known Feeds collapse within original seven scroll attempts.\"\"\"
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


""" + text[a:]
a = text.index('def local_relay('); b = text.index('def helper(', a)
text = text[:a] + '''def local_relay_field(ui, expected_text=None):
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


''' + text[b:]
a = text.index('def helper('); b = text.index('\ndef run(', a)
helper = text[a:b].replace('def helper(ui, action):', "def helper(ui, action, case_id):\n    need(case_id in ui.role_spec['stages'] and action in ('CLEAR', 'CAPTURE'), 'Closed role helper operation required')")
helper = helper.replace('CASE', 'case_id').replace("'evidence/helper-' + action.lower()", "'evidence/' + case_id + '/helper-' + action.lower()")
text = text[:a] + helper + text[b:]
a = text.index('def run(')
text = text[:a] + """def known_control(ui, value, description=False):
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
    return {'schema': 'e02-minimum-role-driver-result-v1', 'profileId': PROFILE,
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
"""
OUT.write_text(text)
print('Prepared minimum driver SOURCE only; no imports, tests, Android or clipboard action executed.')
