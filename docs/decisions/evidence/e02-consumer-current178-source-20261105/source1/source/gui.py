"""Read-only XML, NIP19 and exact helper custody checks; visual review is external."""
import hashlib
import re
import xml.etree.ElementTree as ET
from strict import I64, closed, equal, integer, need, same, text
from wire import A, B, ACCOUNTS, PROFILE, WINDOWS, export

APP = 'com.vitorpamplona.amethyst.debug'
HELPER = 'org.nbdp.clipboard.capture'
WARNING = 'DM inbox relays not found. Messages cannot be delivered until they configure their relay list.'


def xml(files, descriptor):
    raw = files.read(descriptor, 2097152)
    need(b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw, 'XML_ENTITY_DECLARATION')
    tree = ET.fromstring(raw)
    need(tree.tag == 'hierarchy' and len(list(tree.iter())) < 10000, 'XML_STRUCTURE_BOUND')
    return list(tree.iter('node'))


def image(files, descriptor):
    raw = files.read(descriptor, 8388608)
    need(raw.startswith(b'\x89PNG\r\n\x1a\n'), 'ACTUAL_PNG_REQUIRED')


def bounds(node):
    match = re.fullmatch(r'\[(\d{1,4}),(\d{1,4})\]\[(\d{1,4}),(\d{1,4})\]', node.get('bounds', ''))
    need(match is not None, 'BOUNDED_UI_RECT')
    rect = list(map(int, match.groups()))
    need(0 <= rect[0] < rect[2] <= 5000 and 0 <= rect[1] < rect[3] <= 5000, 'UI_RECT_DOMAIN')
    return rect


def enabled(node):
    return node.get('package') == APP and node.get('enabled') == 'true'


def private_room_footer(nodes):
    """Match frozen producer chat_context ownership, not TextView descendants."""
    warnings = [n for n in nodes if n.get('text') == WARNING]
    labels = [n for n in nodes if n.get('text') == 'Message']
    need(not (labels and warnings), 'AMBIGUOUS_PRIVATE_ROOM_FOOTER')
    if warnings:
        need(len(warnings) == 1 and enabled(warnings[0]), 'EXACT_READ_ONLY_DM_WARNING')
        bounds(warnings[0])
        return 'RECIPIENT_DM_RELAYS_WARNING_READ_ONLY'
    need(len(labels) == 1 and enabled(labels[0]), 'PRIVATE_MESSAGE_COMPOSER')
    fields = [n for n in nodes if n.get('class') == 'android.widget.EditText'
              and labels[0] in list(n.iter('node'))]
    need(len(fields) == 1 and enabled(fields[0]) and not fields[0].get('text'), 'EMPTY_OWNED_COMPOSER')
    bounds(fields[0])
    return 'EMPTY_COMPOSER_READ_ONLY'


def nprofile(value):
    """NIP19 Bech32 checksum and TLV, no public-key cryptography or network.

    Decode the actual complete GUI token; no fixture-prefix matching. Unknown
    TLV types are retained/skipped as NIP19 extensions, type0 is unique32bytes.
    """
    text(value, 4096)
    need(value == value.lower() and value.startswith('nprofile1'), 'NPROFILE_LOWERCASE_HRP')
    alphabet = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
    try:
        data = [alphabet.index(c) for c in value[len('nprofile1'):]]
    except ValueError as error:
        raise ValueError('NPROFILE_CHARSET') from error
    need(len(data) >= 7, 'NPROFILE_LENGTH')
    hrp = 'nprofile'
    checksum = 1
    for n in [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp] + data:
        top, checksum = checksum >> 25, ((checksum & 0x1ffffff) << 5) ^ n
        for i, generator in enumerate((0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)):
            if (top >> i) & 1: checksum ^= generator
    equal(checksum, 1, 'NPROFILE_BECH32_CHECKSUM')
    acc, bits, out = 0, 0, bytearray()
    for n in data[:-6]:
        acc = ((acc << 5) | n) & 0xfff
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 255)
    need(bits < 5 and (acc << (8 - bits)) & 255 == 0, 'NPROFILE_PADDING')
    cursor, keys = 0, []
    while cursor < len(out):
        need(cursor + 2 <= len(out), 'NPROFILE_TLV_HEADER')
        kind, size = out[cursor:cursor + 2]; cursor += 2
        need(cursor + size <= len(out), 'NPROFILE_TLV_LENGTH')
        item = bytes(out[cursor:cursor + size]); cursor += size
        if kind == 0:
            need(size == 32, 'NPROFILE_PUBLIC_KEY_LENGTH'); keys.append(item.hex())
        elif kind == 1:
            item.decode('utf-8', 'strict')
    need(len(keys) == 1, 'NPROFILE_UNIQUE_PUBLIC_KEY')
    return keys[0]


def account(files, value, role):
    closed(value, 'preview observedPublicProfileText meaning')
    closed(value['preview'], 'png xml')
    image(files, value['preview']['png'])
    nodes = xml(files, value['preview']['xml'])
    actual = [n.get('text') for n in nodes if 'nprofile1' in n.get('text', '')]
    equal(actual, value['observedPublicProfileText'], 'ACTUAL_PROFILE_GUI_TEXT')
    need(actual, 'PROFILE_GUI_PRESENT')
    tokens = set()
    for label in actual:
        tokens.update(re.findall(r'nprofile1[023456789acdefghjklmnpqrstuvwxyz]+', label))
    need(len(tokens) == 1, 'UNIQUE_COMPLETE_NPROFILE_GUI')
    equal(nprofile(next(iter(tokens))), ACCOUNTS[role], 'WRONG_LOGGED_IN_ACCOUNT')


def helper_receipt(files, descriptor, action, case_id):
    v = files.doc(descriptor)
    fields = 'schema caseId action foregroundFocus elapsedRealtimeNanos wallClockMillis status'
    if action == 'CAPTURE': fields += ' mime bytes sha256 clipboardItemCount clipboardTimestamp'
    closed(v, fields)
    equal(v['schema'], 'e02-clipboard-capture-v1'); equal(v['action'], action)
    equal(v['caseId'], case_id); equal(v['foregroundFocus'], True)
    integer(v['elapsedRealtimeNanos'], 0, I64); integer(v['wallClockMillis'])
    equal(v['status'], 'EMPTY_SENTINEL_SET' if action == 'CLEAR' else 'CAPTURED')
    if action == 'CAPTURE':
        equal(v['mime'], 'text/plain'); equal(v['clipboardItemCount'], 1)
        integer(v['clipboardTimestamp']); integer(v['bytes'], 1, 65536)
    return v


def adb_tail(command):
    argv = command['argv']
    # Exact owned guard marker; raw words in Docker labels are not ADB actions.
    try:
        start = argv.index('adb', argv.index('/input/lease_guard.py') + 1)
    except ValueError:
        return None
    return argv[start + 1:]


def captures(files, values, command_rows):
    need(type(values) is list and 1 <= len(values) <= 140, 'COMPLETE_UI_BOUND')
    seen, prior = set(), -1
    for i, value in enumerate(values, 1):
        closed(value, 'png xml'); image(files, value['png']); xml(files, value['xml'])
        for kind in ('png', 'xml'):
            need(value[kind]['path'] not in seen, 'STALE_UI_CAPTURE_ALIAS'); seen.add(value[kind]['path'])
            need(re.search(r'/ui/ui-%03d-[a-z0-9-]+\.%s$' % (i, kind), value[kind]['path']), 'UI_SERIAL_ORDER')
        matches = [j for j, c in enumerate(command_rows) if adb_tail(c) == ['exec-out', 'screencap', '-p']
                   and c['stdout']['sha256'] == value['png']['sha256'] and c['stdout']['bytes'] == value['png']['bytes']]
        # Identical screenshots may legitimately repeat. Join by chronological raw
        # capture sequence, rather than forbidding repeated screenshot hashes.
        candidates = [j for j in matches if j > prior]
        need(candidates, 'ACTUAL_ADB_SCREENSHOT_STREAM')
        at = min(candidates)
        xmlmatches = [j for j in range(prior + 1, at) if adb_tail(command_rows[j]) == ['shell', 'cat', '/sdcard/nbdp-window.xml']
                      and command_rows[j]['stdout']['sha256'] == value['xml']['sha256']
                      and command_rows[j]['stdout']['bytes'] == value['xml']['bytes']]
        need(xmlmatches, 'ACTUAL_ADB_XML_STREAM')
        prior = at
    return seen


def selection(files, observation, expected, spec, role, command_rows, all_ui, helper_apk):
    sid = spec['id']
    s = files.doc(observation['selection'])
    closed(s, 'schema profileId windowId observationId account peer originalAuthor originalOrderedTags rumorId action method helperPackage helperArtifact helperReceipt capturedMonotonicNs selectedGui matchingVisibleTextNodes limits')
    equal(s['schema'], 'e02-minimum-selection-v1'); equal(s['profileId'], PROFILE)
    equal(s['windowId'], WINDOWS[role]); equal(s['observationId'], sid)
    equal(s['account'], ACCOUNTS[role]); equal(s['peer'], A if role == 'incoming' else B)
    equal(s['originalAuthor'], A); equal(s['originalOrderedTags'], [['p', B]]); equal(s['rumorId'], expected['id'])
    equal(s['action'], 'COPY_RAW_JSON'); equal(s['method'], 'ANDROID_LOCAL_FOREGROUND')
    equal(s['helperPackage'], HELPER); equal(s['helperArtifact'], helper_apk)
    for descriptor, leaf in ((observation['selection'], 'selection.json'),
                             (observation['rawClientRumor'], 'client-raw-rumor.json'),
                             (observation['clipboardClear'], 'helper-clear.json'),
                             (s['helperReceipt'], 'helper-capture.json')):
        need(descriptor['path'].endswith('/evidence/' + sid + '/' + leaf), 'FRESH_STAGE_EXPORT_PATH')
    integer(s['capturedMonotonicNs'], 0, I64)
    equal(s['selectedGui'], {'png': observation['uiPng'], 'xml': observation['uiXml']})
    need(any(same(s['selectedGui'], v) for v in all_ui), 'SELECTED_GUI_IN_FULL_INVENTORY')
    nodes = xml(files, observation['uiXml'])
    token = 'NBDP harmless ordinary chat control' if spec['oracle'] == 'chat' else 'NBDP/experiment'
    actual_nodes = [n for n in nodes if token in n.get('text', '')]
    need(actual_nodes and all(enabled(n) for n in actual_nodes), 'ACTUAL_RENDERED_AMETHYST_NOTE')
    visible = [{'bounds': bounds(n), 'text': n.get('text')} for n in actual_nodes]
    equal(s['matchingVisibleTextNodes'], visible)
    maximum = 3 if spec['index'] > 0 and role == 'archive' else 1
    need(1 <= len(visible) <= maximum, 'VISIBLE_MATCH_COUNT')
    need(sum(v['bounds'][3] == max(x['bounds'][3] for x in visible) for v in visible) == 1, 'AMBIGUOUS_LOWEST_NOTE')
    back = [n for n in nodes if n.get('content-desc') == 'Back' and enabled(n)]
    need(len(back) == 1, 'KNOWN_PRIVATE_ROOM_BACK')
    private_room_footer(nodes)
    equal(observation['visibleMatchingTextNodeCount'], len(visible))
    equal(observation['duplicateObservation'], dict(scope='CURRENT_VISIBLE_MATCHING_TEXT_NODES_ONLY',
          visibleMatchingTextNodeCount=len(visible), globalDuplicateBubbleCount=None,
          globalDuplicateBubbleCountStatus='UNKNOWN_UNMEASURED', businessEffectsMeasured=False))
    raw = files.read(observation['rawClientRumor'], 65536); export(raw, expected)
    cleared = helper_receipt(files, observation['clipboardClear'], 'CLEAR', sid)
    captured = helper_receipt(files, s['helperReceipt'], 'CAPTURE', sid)
    need(captured['elapsedRealtimeNanos'] > cleared['elapsedRealtimeNanos']
         and captured['wallClockMillis'] >= cleared['wallClockMillis']
         and captured['clipboardTimestamp'] >= cleared['wallClockMillis'], 'FRESH_HELPER_CLOCK_CUSTODY')
    equal(captured['bytes'], len(raw)); equal(captured['sha256'], hashlib.sha256(raw).hexdigest())
    custody = observation['custodySegment']
    closed(custody, 'commandSequenceFirst commandSequenceLast uiCaptureSerialFirst uiCaptureSerialLast uiActionCountBefore uiActionCountAfter uiCaptures')
    first, last = custody['commandSequenceFirst'], custody['commandSequenceLast']
    integer(first, 1, len(command_rows)); integer(last, first, len(command_rows))
    start, finish = custody['uiCaptureSerialFirst'], custody['uiCaptureSerialLast']
    integer(start, 1, len(all_ui)); integer(finish, start, len(all_ui))
    equal(custody['uiCaptures'], all_ui[start - 1:finish])
    integer(custody['uiActionCountBefore'], 0, 120); integer(custody['uiActionCountAfter'], custody['uiActionCountBefore'], 120)
    tails = [(i + 1, adb_tail(c)) for i, c in enumerate(command_rows) if first <= i + 1 <= last]
    tails = [(i, t) for i, t in tails if t is not None]
    # Exact actual helper CLEAR/receipt and CAPTURE/raw reads in this closed stage.
    prefix = 'files/captures/' + sid
    clear_reads = [i for i, t in tails if t == ['exec-out', 'run-as', HELPER, 'cat', prefix + '.clear.json']]
    cap_reads = [i for i, t in tails if t == ['exec-out', 'run-as', HELPER, 'cat', prefix + '.receipt.json']]
    raw_reads = [i for i, t in tails if t == ['exec-out', 'run-as', HELPER, 'cat', prefix + '.raw.json']]
    need(len(clear_reads) == len(cap_reads) == len(raw_reads) == 1 and clear_reads[0] < cap_reads[0] < raw_reads[0], 'HELPER_CLEAR_CAPTURE_READ_ORDER')
    for i, descriptor in ((clear_reads[0], observation['clipboardClear']), (cap_reads[0], s['helperReceipt']), (raw_reads[0], observation['rawClientRumor'])):
        equal(files.read(command_rows[i - 1]['stdout']), files.read(descriptor), 'HELPER_ACTUAL_RAW_STREAM')
    # Source command lineage plus independent same-graph visual review establish
    # menu/copy actions. No fixture JSON or host clipboard command is admissible.
    bottom = max(v['bounds'][3] for v in visible)
    chosen = next(v['bounds'] for v in visible if v['bounds'][3] == bottom)
    cx, cy = (chosen[0] + chosen[2]) // 2, (chosen[1] + chosen[3]) // 2
    longpress = [(i, t) for i, t in tails if clear_reads[0] < i < cap_reads[0] and
                 t == ['shell', 'input', 'swipe', str(cx), str(cy), str(cx), str(cy), '700']]
    need(len(longpress) == 1, 'ACTUAL_SELECTED_NOTE_LONG_PRESS')
    def actual_button_tap(label, package, after, before):
        matches = []
        for capture in custody['uiCaptures']:
            controls = [n for n in xml(files, capture['xml']) if n.get('text') == label
                        and n.get('package') == package and n.get('enabled') == 'true']
            if len(controls) != 1: continue
            rect = bounds(controls[0]); x, y = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
            screenshots = [i + 1 for i, c in enumerate(command_rows) if after < i + 1 < before
                           and adb_tail(c) == ['exec-out', 'screencap', '-p'] and
                           c['stdout']['sha256'] == capture['png']['sha256']]
            for screenshot in screenshots:
                # The next UI input action must select this actual source-bound
                # control, rather than an arbitrary coordinate elsewhere.
                later = [(i, t) for i, t in tails if screenshot < i < before and t[:2] == ['shell', 'input']]
                if later and later[0][1] == ['shell', 'input', 'tap', str(x), str(y)]: matches.append(later[0][0])
        unique = sorted(set(matches)); need(len(unique) == 1, 'ACTUAL_ORDERED_BUTTON_TAP:' + label)
        return unique[0]
    actual_button_tap('Clear clipboard', HELPER, first - 1, clear_reads[0])
    more = actual_button_tap('More Options', APP, longpress[0][0], cap_reads[0])
    copied = actual_button_tap('Copy raw JSON', APP, more, cap_reads[0])
    actual_button_tap('Capture clipboard', HELPER, copied, cap_reads[0])
    return custody
