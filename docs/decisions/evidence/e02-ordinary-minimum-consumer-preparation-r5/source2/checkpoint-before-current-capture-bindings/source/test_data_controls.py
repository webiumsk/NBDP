"""PREPARED, NOT EXECUTED: targeted pure DATA controls, never client evidence.

Only owned tempfile files/stdlib are used. No project producer is imported. A
positive synthetic value means DATA consistency only, never authentic execution.
"""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strict
import wire
import gui
import witness
import consumer


def pin(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def inner(content='NBDP harmless ordinary chat control — faktúra 𐐀'):
    value = dict(pubkey=wire.A, created_at=1, kind=14, tags=[['p', wire.B]], content=content)
    value['id'] = hashlib.sha256(strict.json_bytes([0, value['pubkey'], 1, 14, value['tags'], content])).hexdigest()
    return value


def publication_data(root, role='incoming', index=0, observed=True, candidate_payload=None,
                     late_candidate=False, event_content=None):
    """Fabricated DATA joins only: no signing/encryption/execution/review claim."""
    files = strict.Files([str(root)])
    def put(name, value, raw=False):
        return pin(root / name, value if raw else strict.json_bytes(value))
    spec = wire.stage(role, index)
    expected = inner('{"protocol":"NBDP/experiment","synthetic":true}') if spec['oracle'] == 'business' else inner()
    event = dict(pubkey=wire.A, created_at=1, kind=1059, tags=[['p', wire.ACCOUNTS[role]]], content='synthetic-encrypted-placeholder', sig='0' * 128)
    if event_content is not None:
        strict.text(event_content, 262144); event['content'] = event_content
    event['id'] = hashlib.sha256(strict.json_bytes([0, event['pubkey'], 1, 1059, event['tags'], event['content']])).hexdigest()
    attempt = dict(epoch=index + 1, stageId=spec['id'])
    gen = dict(connection=1, subscription='actual-sub', requestSequence=2, eoseSequence=3)
    gate = dict(gen, filters=[{'kinds': [1059], '#p': [wire.ACCOUNTS[role]]}])
    rows = []
    def row(direction, **fields):
        r = dict(schema='e02-minimum-proxy-row-v1', sequence=len(rows) + 1, utc='2026-10-24T00:00:00.000Z', direction=direction, **fields)
        rows.append(r); return r
    def b64(value): return base64.b64encode(value).decode()
    row('OPEN', connection=1, userAgent='SYNTHETIC_DATA_ONLY')
    row('APP_TO_RELAY', connection=1, rawBase64=b64(strict.json_bytes(['REQ', 'actual-sub', *gate['filters']])))
    row('RELAY_TO_APP', connection=1, rawBase64=b64(b'["EOSE","actual-sub"]'), publicationGeneration=None, publicationAttempt=None)
    intentseq = row('PUBLICATION_INTENT', stageId=spec['id'], eventId=event['id'], attempt=attempt)['sequence']
    sent = put('sent.json', strict.json_bytes(['EVENT', event]), True)
    row('PRODUCER_TO_RELAY', exchangeLabel=spec['id'] + '-publish', rawBase64=b64(files.read(sent)), frame=sent)
    ack = dict(rawBase64=b64(strict.json_bytes(['OK', event['id'], True, 'synthetic'])), frame=['OK', event['id'], True, 'synthetic'])
    row('RELAY_TO_PRODUCER', exchangeLabel=spec['id'] + '-publish', rawBase64=ack['rawBase64'])
    delivery = None
    if observed:
        payload = dict(event, **candidate_payload) if candidate_payload is not None else event
        forwarded = row('RELAY_TO_APP', connection=1, rawBase64=b64(strict.json_bytes(['EVENT', 'actual-sub', payload])), publicationGeneration=gen, publicationAttempt=attempt)
        callback = row('APP_SOCKET_SEND_COMPLETE', connection=1, sourceSequence=forwarded['sequence'], publicationGeneration=gen, publicationAttempt=attempt)
        delivery = dict(connection=1, subscription='actual-sub', rowSequence=forwarded['sequence'], sentSequence=callback['sequence'],
                        forwardGeneration=gen, completionGeneration=gen, forwardAttempt=attempt, completionAttempt=attempt)
    elif candidate_payload is not None and not late_candidate:
        # Deliberately false query-only claim: producer counts selected EVENT ID
        # even when its payload changed and no callback completed.
        row('RELAY_TO_APP', connection=1, rawBase64=b64(strict.json_bytes(['EVENT', 'actual-sub', dict(event, **candidate_payload)])),
            publicationGeneration=gen, publicationAttempt=attempt)
    close = row('PUBLICATION_WINDOW_CLOSED', stageId=spec['id'], eventId=event['id'], attempt=attempt,
                intentSequence=intentseq, actualNewAppFrameObserved=observed, candidateAppFrameSeen=observed, elapsedNanoseconds=100)
    querysent = put('query-sent.json', strict.json_bytes(['REQ', 'e02-owned-query', {'ids': [event['id']], 'limit': 1}]), True)
    row('PRODUCER_TO_RELAY', exchangeLabel=spec['id'] + '-query', rawBase64=b64(files.read(querysent)), frame=querysent)
    qr = dict(rawBase64=b64(strict.json_bytes(['EVENT', 'e02-owned-query', event])), frame=['EVENT', 'e02-owned-query', event])
    qe = dict(rawBase64=b64(b'["EOSE","e02-owned-query"]'), frame=['EOSE', 'e02-owned-query'])
    for reply in (qr, qe): row('RELAY_TO_PRODUCER', exchangeLabel=spec['id'] + '-query', rawBase64=reply['rawBase64'])
    if late_candidate:
        row('RELAY_TO_APP', connection=1, rawBase64=b64(strict.json_bytes(['EVENT', 'actual-sub', dict(event, **(candidate_payload or {}))])),
            publicationGeneration=None, publicationAttempt=None)
    proxy_pin = put('capture.jsonl', b''.join(strict.json_bytes(r) + b'\n' for r in rows), True)
    proxy = wire.Proxy(files, proxy_pin)
    def sentrow(p, message):
        return dict(frame=p, eventId=event['id'] if message == 'EVENT' else None, messageType=message,
                    sendInvoked=True, sendCallbackCompleted=True, callbackBufferHash=p['sha256'])
    publication = dict(ack=[ack], received=[], eose=None, sentFrames=[sentrow(sent, 'EVENT')], elapsedNanoseconds=100)
    query = dict(ack=[], received=[qr], eose=qe, sentFrames=[sentrow(querysent, 'REQ')], elapsedNanoseconds=100)
    prepared = put('prepared.json', dict(rumors={spec['oracle']: expected}, events=[event] * (index + 1)))
    intent = put('intent.json', dict(schema='e02-minimum-publish-intent-v2', profileId=wire.PROFILE,
                 windowId=wire.WINDOWS[role], stage=spec, attempt=attempt, intentSequence=intentseq, prepared=prepared, gate=gate, issuedUTC='2026-10-24T00:00:00.000Z'))
    origin = wire.APP if observed else wire.QUERY
    window = put('window.json', dict(schema='e02-minimum-publication-window-v2', profileId=wire.PROFILE,
                 windowId=wire.WINDOWS[role], stageId=spec['id'], eventId=event['id'], attempt=attempt,
                 intentSequence=intentseq, closeSequence=close['sequence'], actualNewAppFrameObserved=observed,
                 candidateAppFrameSeen=observed, elapsedNanoseconds=100, clock='NODE_PROCESS_HRTIME_MONOTONIC', origin=origin))
    actual_raw = strict.json_bytes(['EVENT', 'actual-sub', event]) if observed else wire.decode64(qr['rawBase64'])
    framepin = put('frame.json', actual_raw, True)
    wirepin = put('wire.json', strict.json_bytes(event), True)
    request = dict(op='validate', wire=strict.json_bytes(event).decode(), secret=('2' if role == 'incoming' else '1').zfill(64), role=role, expectedSender=wire.A)
    value = dict(rumor=expected, dispatch=spec['dispatch'], role=spec['normalizedRole'])
    if spec['oracle'] == 'business': value['envelope'] = json.loads(expected['content'])
    normalized = dict(ok=True, value=value, decrypts=[1, 1])
    jsr = put('js-request.json', request); rr = put('rust-request.json', request)
    js = put('js-result.json', normalized); rust = put('rust-result.json', normalized)
    transport = put('transport.json', dict(schema='e02-minimum-transport-v2', frame=framepin, wire=wirepin, jsRequest=jsr, rustRequest=rr, jsResult=js, rustResult=rust))
    src = put('rust-source.rs', b'SYNTHETIC_DATA_NOT_A_PRODUCER', True)
    binary = put('rust-binary', b'SYNTHETIC_NOT_EXECUTED', True)
    stdin = put('stdin.jsonl', strict.json_bytes({'op': 'source'}) + b'\n' + strict.json_bytes(request) + b'\n', True)
    stdout = put('stdout.jsonl', strict.json_bytes({'ok': True, 'value': files.read(src).decode()}) + b'\n' + strict.json_bytes({'ok': True, 'value': normalized}) + b'\n', True)
    stderr = put('stderr.bin', b'', True)
    validation = put('validation.json', dict(schema='e02-minimum-validated-wire-record-v2', profileId=wire.PROFILE,
        windowId=wire.WINDOWS[role], stageId=spec['id'], origin=origin, clientReceiptEstablished=observed,
        transport=transport, rustBinary=binary, rustSource=src, rustInput=stdin, rustStdout=stdout, rustStderr=stderr,
        rustExit=0, rustSignal=None, actualQueriedEvent=event, js=normalized, rust=normalized,
        clientRetention='NOT_ESTABLISHED_BY_TRANSPORT_VALIDATION'))
    producer = put('producer.json', dict(schema='e02-minimum-producer-validation-v2', stageId=spec['id'], actualPublishedEvent=event,
        result=normalized, meaning='SYNTHETIC_DATA_ONLY'))
    record = dict(observation={}, schema='e02-minimum-stage-publication-v2', profileId=wire.PROFILE, windowId=wire.WINDOWS[role], stage=spec,
        attempt=attempt, intent=intent, publicationWindow=window, gate=gate, publication=publication, query=query, event=event,
        actualNewAppFrameObserved=observed, delivery=delivery, validation=dict(transport=transport, validation=validation),
        producerValidation=producer, clientRetention='UNVERIFIED_REQUIRES_FRESH_CLIENT_SELECTION_EXPORT', validationOrigin=origin,
        replayLimit=None if observed else 'SYNTHETIC bounded interval, not client receipt')
    return files, proxy, record, expected, spec, role


def selection_data(root, footer='owned', include_back=True):
    """Synthetic source-backed XML/action DATA, never an actual Android frame."""
    files = strict.Files([str(root)])
    def put(relative, value, raw=False):
        path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
        return pin(path, value if raw else strict.json_bytes(value))
    def node(parent, label='', package=gui.APP, kind='android.widget.TextView', enabled=True,
             rectangle='[10,10][300,50]', description=''):
        return ET.SubElement(parent, 'node', {'text': label, 'package': package, 'class': kind,
            'enabled': 'true' if enabled else 'false', 'bounds': rectangle, 'content-desc': description})
    def hierarchy(): return ET.Element('hierarchy')
    def helper_screen():
        tree = hierarchy()
        node(tree, 'Clear clipboard', gui.HELPER, 'android.widget.Button', rectangle='[10,10][100,50]')
        node(tree, 'Capture clipboard', gui.HELPER, 'android.widget.Button', rectangle='[10,60][100,100]')
        return tree
    expected, spec, role = inner(), wire.stage('incoming', 1), 'incoming'
    sid = spec['id']; directory = 'evidence/' + sid + '/'
    tree = hierarchy()
    if include_back: node(tree, description='Back')
    node(tree, expected['content'], rectangle='[10,100][200,150]')
    if footer.startswith('warning'):
        package = 'foreign.app' if footer == 'warning-foreign' else gui.APP
        node(tree, gui.WARNING, package=package, enabled=footer != 'warning-disabled')
        if footer == 'warning-duplicate': node(tree, gui.WARNING)
        if footer == 'warning-and-label': node(tree, 'Message')
    elif footer != 'missing':
        owner = node(tree, 'already entered' if footer == 'nonempty' else '',
                     package='foreign.app' if footer == 'foreign' else gui.APP,
                     kind='android.widget.EditText', enabled=footer != 'disabled')
        if footer == 'ambiguous': owner = node(owner, kind='android.widget.EditText')
        node(tree if footer == 'detached' else owner, 'Message',
             package='foreign.app' if footer == 'foreign-label' else gui.APP, enabled=footer != 'disabled-label')
    more, copy_menu = hierarchy(), hierarchy()
    node(more, 'More Options', rectangle='[20,200][120,240]')
    node(copy_menu, 'Copy raw JSON', rectangle='[20,250][120,290]')
    screens = [helper_screen(), tree, more, copy_menu, helper_screen()]
    all_ui = []
    for i, screen in enumerate(screens, 1):
        all_ui.append(dict(xml=put('ui/ui-%03d-synthetic.xml' % i, ET.tostring(screen), True),
                           png=put('ui/ui-%03d-synthetic.png' % i, b'\x89PNG\r\n\x1a\nSYNTHETIC_DATA_ONLY_' + str(i).encode(), True)))
    raw = strict.json_bytes(expected)
    raw_pin = put(directory + 'client-raw-rumor.json', raw, True)
    cleared = dict(schema='e02-clipboard-capture-v1', caseId=sid, action='CLEAR', foregroundFocus=True,
                   elapsedRealtimeNanos=100, wallClockMillis=100, status='EMPTY_SENTINEL_SET')
    captured = dict(schema='e02-clipboard-capture-v1', caseId=sid, action='CAPTURE', foregroundFocus=True,
                   elapsedRealtimeNanos=101, wallClockMillis=101, status='CAPTURED', mime='text/plain',
                   bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), clipboardItemCount=1, clipboardTimestamp=101)
    clear_pin = put(directory + 'helper-clear.json', cleared); helper_pin = put(directory + 'helper-capture.json', captured)
    helper_apk = dict(path=str(root / 'synthetic-unread-helper.apk'), bytes=1, sha256='0' * 64)
    selected = all_ui[1]
    selection = put(directory + 'selection.json', dict(schema='e02-minimum-selection-v1', profileId=wire.PROFILE,
        windowId='incoming-b', observationId=sid, account=wire.B, peer=wire.A, originalAuthor=wire.A,
        originalOrderedTags=[['p', wire.B]], rumorId=expected['id'], action='COPY_RAW_JSON',
        method='ANDROID_LOCAL_FOREGROUND', helperPackage=gui.HELPER, helperArtifact=helper_apk,
        helperReceipt=helper_pin, capturedMonotonicNs=1000, selectedGui=selected,
        matchingVisibleTextNodes=[dict(bounds=[10,100,200,150], text=expected['content'])],
        limits='SYNTHETIC_DATA_ONLY_NOT_RUNTIME_GUI'))
    rows = []
    def command(tail, stdout):
        rows.append(dict(argv=['/usr/bin/docker', 'exec', 'synthetic-owned-cid', '/input/lease_guard.py',
                              'exec', 'synthetic-lease', 'adb', *tail], stdout=stdout))
    def empty(name): return put('synthetic-streams/' + name, b'', True)
    command(['exec-out', 'screencap', '-p'], all_ui[0]['png'])
    command(['shell', 'input', 'tap', '55', '30'], empty('clear-tap'))
    prefix = 'files/captures/' + sid
    command(['exec-out', 'run-as', gui.HELPER, 'cat', prefix + '.clear.json'], clear_pin)
    command(['exec-out', 'screencap', '-p'], selected['png'])
    command(['shell', 'input', 'swipe', '105', '125', '105', '125', '700'], empty('longpress'))
    command(['exec-out', 'screencap', '-p'], all_ui[2]['png'])
    command(['shell', 'input', 'tap', '70', '220'], empty('more-tap'))
    command(['exec-out', 'screencap', '-p'], all_ui[3]['png'])
    command(['shell', 'input', 'tap', '70', '270'], empty('copy-tap'))
    command(['exec-out', 'screencap', '-p'], all_ui[4]['png'])
    command(['shell', 'input', 'tap', '55', '80'], empty('capture-tap'))
    command(['exec-out', 'run-as', gui.HELPER, 'cat', prefix + '.receipt.json'], helper_pin)
    command(['exec-out', 'run-as', gui.HELPER, 'cat', prefix + '.raw.json'], raw_pin)
    custody = dict(commandSequenceFirst=1, commandSequenceLast=13, uiCaptureSerialFirst=1,
        uiCaptureSerialLast=5, uiActionCountBefore=0, uiActionCountAfter=8, uiCaptures=all_ui)
    observation = dict(selection=selection, uiPng=selected['png'], uiXml=selected['xml'], rawClientRumor=raw_pin,
        clipboardClear=clear_pin, visibleMatchingTextNodeCount=1, custodySegment=custody,
        duplicateObservation=dict(scope='CURRENT_VISIBLE_MATCHING_TEXT_NODES_ONLY', visibleMatchingTextNodeCount=1,
            globalDuplicateBubbleCount=None, globalDuplicateBubbleCountStatus='UNKNOWN_UNMEASURED', businessEffectsMeasured=False))
    return files, observation, expected, spec, role, rows, all_ui, helper_apk


class PureDataControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nbdp-minimum-consumer-data-')
        self.root = Path(self.temp.name)
        self.files = strict.Files([str(self.root)])

    def tearDown(self):
        self.temp.cleanup()

    def test_positive_exact_six_field_unicode_export(self):
        value = inner(); self.assertEqual(wire.export(strict.json_bytes(value), value), value)

    def test_positive_empty_sig_client_representation_only(self):
        value = inner(); self.assertEqual(wire.export(strict.json_bytes(dict(value, sig='')), value), value)

    def test_nonempty_sig_refused(self):
        value = inner()
        with self.assertRaises(strict.Refusal): wire.export(strict.json_bytes(dict(value, sig='0' * 128)), value)

    def test_extra_client_field_refused(self):
        value = inner()
        with self.assertRaises(strict.Refusal): wire.export(strict.json_bytes(dict(value, source='fixture')), value)

    def test_changed_content_even_with_recomputed_id_refused(self):
        with self.assertRaises(strict.Refusal): wire.export(strict.json_bytes(inner('changed')), inner())

    def test_changed_ordered_tags_refused(self):
        value = inner(); value['tags'] = [['p', wire.B], ['x', 'extra']]
        with self.assertRaises(strict.Refusal): wire.export(strict.json_bytes(value), inner())

    def test_unicode_normalization_is_not_applied(self):
        with self.assertRaises(strict.Refusal): wire.export(strict.json_bytes(inner('e\u0301')), inner('é'))

    def test_duplicate_json_keys_refused(self):
        with self.assertRaises(strict.Refusal): strict.loads(b'{"x":1,"x":2}')

    def test_invalid_utf8_refused(self):
        with self.assertRaises(UnicodeError): strict.loads(b'{"x":"\xff"}')

    def test_nonfinite_float_and_negative_zero_refused(self):
        for value in (b'NaN', b'1.0', b'-0'):
            with self.subTest(value=value), self.assertRaises(strict.Refusal): strict.loads(value)

    def test_boolean_is_not_integer(self):
        with self.assertRaises(strict.Refusal): strict.integer(True)
        self.assertFalse(strict.same(True, 1))

    def test_selection_i64_positive_exact_path(self):
        value = {'schema': 'e02-minimum-selection-v1', 'capturedMonotonicNs': 1792807041018412788}
        self.assertEqual(strict.validate_numbers(value), value)

    def test_lease_all_six_i64_fields_positive(self):
        value = dict(schema='e02-single-cell-lease-v1')
        for clock in ('Utc', 'Mono', 'Boot'):
            for prefix in ('issued', 'deadline'): value[prefix + clock + 'Ns'] = 1792807041018412788
        self.assertEqual(strict.validate_numbers(value), value)

    def test_ns_name_does_not_widen_wire(self):
        with self.assertRaises(strict.Refusal): strict.validate_numbers({'capturedMonotonicNs': strict.SAFE + 1})

    def test_nested_schema_cannot_widen_parent(self):
        with self.assertRaises(strict.Refusal):
            strict.validate_numbers({'schema': 'other', 'nested': {'schema': 'e02-minimum-selection-v1', 'capturedMonotonicNs': strict.SAFE + 1}})

    def test_unrelated_field_in_registered_schema_stays_safe(self):
        with self.assertRaises(strict.Refusal):
            strict.validate_numbers({'schema': 'e02-minimum-selection-v1', 'other': strict.SAFE + 1})

    def test_i64_overflow_refused(self):
        with self.assertRaises(strict.Refusal): strict.loads(str(strict.I64 + 1).encode())

    def test_wire_timestamp_not_widened(self):
        value = inner(); value['created_at'] = strict.SAFE + 1
        with self.assertRaises(strict.Refusal): wire.rumor(value)

    def test_file_positive_then_drift_refused(self):
        p = pin(self.root / 'evidence.json', b'{}'); self.assertEqual(self.files.doc(p), {})
        (self.root / 'evidence.json').write_bytes(b'[]')
        with self.assertRaises(strict.Refusal): self.files.read(p)

    def test_duplicate_pin_alias_refused(self):
        p = pin(self.root / 'evidence.json', b'{}'); self.files.read(p)
        with self.assertRaises(strict.Refusal): self.files.read(dict(p, sha256='0' * 64))

    def test_symlink_file_and_component_refused(self):
        p = pin(self.root / 'original', b'{}')
        (self.root / 'alias').symlink_to(self.root / 'original')
        with self.assertRaises(OSError): self.files.read(dict(p, path=str(self.root / 'alias')))
        (self.root / 'directory').mkdir(); (self.root / 'linkdir').symlink_to(self.root / 'directory')
        q = pin(self.root / 'directory' / 'record', b'{}')
        with self.assertRaises(OSError): self.files.read(dict(q, path=str(self.root / 'linkdir' / 'record')))

    def test_guest_mapping_positive_and_crosswindow_refusal(self):
        (self.root / 'session/fixtures').mkdir(parents=True)
        p = pin(self.root / 'session/fixtures/actual.json', b'{}')
        self.files.window(self.root)
        guest = dict(p, path='/session/fixtures/actual.json')
        self.assertEqual(self.files.doc(guest), {})
        with self.assertRaises(strict.Refusal): self.files.binding(guest, dict(p, path=str(self.root / 'other/actual.json')), self.root)

    def test_guest_binding_conflict_refused(self):
        p = dict(path='/session/fixtures/a.json', bytes=2, sha256=hashlib.sha256(b'{}').hexdigest())
        host = dict(p, path=str(self.root / 'session/fixtures/a.json'))
        self.files.binding(p, host, self.root)
        with self.assertRaises(strict.Refusal): self.files.binding(p, dict(host, sha256='0' * 64), self.root)

    def test_unbound_input_and_outside_root_refused(self):
        p = dict(path='/input/unbound.json', bytes=0, sha256=hashlib.sha256(b'').hexdigest())
        with self.assertRaises(strict.Refusal): self.files.read(p)
        with self.assertRaises(strict.Refusal): self.files.read(dict(p, path='/not-owned.json'))

    def test_raw_base64_positive_and_invalid_refused(self):
        raw = b'["EOSE","actual"]'; encoded = base64.b64encode(raw).decode()
        self.assertEqual(wire.decode64(encoded), raw)
        with self.assertRaises(ValueError): wire.decode64(encoded + '\n')

    def test_proxy_sequence_omission_refused(self):
        row = dict(schema='e02-minimum-proxy-row-v1', sequence=2, utc='2026-10-24T00:00:00.000Z', direction='OPEN', connection=1, userAgent='synthetic')
        p = pin(self.root / 'proxy.jsonl', strict.json_bytes(row) + b'\n')
        with self.assertRaises(strict.Refusal): wire.Proxy(self.files, p)

    def test_proxy_unknown_direction_refused(self):
        row = dict(schema='e02-minimum-proxy-row-v1', sequence=1, utc='', direction='SYNTHETIC_FRAME')
        with self.assertRaises(strict.Refusal): wire.Proxy(self.files, pin(self.root / 'proxy.jsonl', strict.json_bytes(row) + b'\n'))

    def test_role_stage_contract_and_archive_inner_recipient(self):
        self.assertEqual(len(wire.STAGES['incoming']), 2); self.assertEqual(len(wire.STAGES['archive']), 3)
        self.assertFalse(wire.stage('archive', 1)['requiresNewAppFrame'])
        self.assertTrue(wire.stage('archive', 2)['requiresNewAppFrame'])
        self.assertEqual(wire.ACCOUNTS['archive'], wire.A)
        self.assertEqual(wire.rumor(inner())['tags'], [['p', wire.B]])

    def test_actual_public_api35_nprofile_vector(self):
        # Frozen public scalar2 GUI vector, not a new client observation.
        self.assertEqual(gui.nprofile('nprofile1qqsvvprlj3q76ltdxpz5qm54cp7dshrh3e9cemeu5746czdet3cfaeg6hkryv'), wire.B)

    def test_nprofile_checksum_and_truncation_refused(self):
        for value in ('nprofile1qqsvvprlj3q76ltdxpz5qm54cp7dshrh3e9cemeu5746czdet3cfaeg6hkryq', 'nprofile1qqs'):
            with self.subTest(value=value), self.assertRaises(ValueError): gui.nprofile(value)

    def test_fixture_json_text_and_clipboard_inputs_refused(self):
        self.assertFalse(witness.allowed_adb(['shell', 'input', 'text', 'business_fixture'], 'incoming'))
        self.assertFalse(witness.allowed_adb(['shell', 'cmd', 'clipboard', 'set', '{}'], 'incoming'))
        self.assertFalse(witness.allowed_adb(['shell', 'sh', '-c', 'echo fixture'], 'incoming'))

    def test_crossrole_helper_case_refused(self):
        self.assertFalse(witness.allowed_adb(['exec-out', 'run-as', gui.HELPER, 'cat', 'files/captures/archive-business.raw.json'], 'incoming'))

    def test_exact_synthetic_identity_allowed_but_wrong_role_refused(self):
        nsec = 'nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqpqptcfk2'
        self.assertTrue(witness.allowed_adb(['shell', 'input', 'text', nsec], 'incoming'))
        self.assertFalse(witness.allowed_adb(['shell', 'input', 'text', nsec], 'archive'))

    def test_unknown_json_schema_cannot_claim_window(self):
        p = pin(self.root / 'manifest.json', strict.json_bytes({'schema': 'old-eight-profile'}))
        with self.assertRaises(strict.Refusal): consumer.consume(self.files, p, p)
        # SOURCE2 subcases remain inside the original86-method scope. Synthetic
        # quiet streams are parser inputs, never actual tool/control receipts.
        for index, (count, dots, output_count, suffix, good) in enumerate([
            (3, 3, 3, b'OK\n', True), (8, 8, 8, b'OK\n', True), (7, 7, 7, b'OK\n', True),
            (3, 2, 3, b'OK\n', False), (3, 3, 7, b'OK\n', False),
            (3, 3, 3, b'OK (skipped=1)\n', False), (3, 3, 3, b'FAILED (failures=1)\n', False)]):
            with self.subTest(captureQuietParser=index):
                stdout = pin(self.root / ('capture-%d.stdout' % index), b'')
                raw = b'.' * dots + b'\n' + b'-' * 70 + b'\nRan ' + str(output_count).encode() + b' tests in 0.001s\n\n' + suffix
                stderr = pin(self.root / ('capture-%d.stderr' % index), raw)
                name = {3:'rebuilt-artifact-bindings', 8:'public-identity-metadata', 7:'producer2-source-wiring'}[count]
                scope = dict(name=name, count=count)
                receipt = dict(stdout=stdout, stderr=stderr, observedStreamBytes=dict(stdout=0, stderr=len(raw)),
                    truncated=dict(stdout=False, stderr=False), observedPartitions={name:count})
                if good: consumer.capture_output(self.files, scope, receipt)
                else:
                    with self.assertRaises(strict.Refusal): consumer.capture_output(self.files, scope, receipt)

        # Explicitly SYNTHETIC helper inputs, not actual API/evidence receipts.
        # This checks the custody predicate only, never current_capture admission.
        from types import SimpleNamespace
        plan_pin = consumer.CURRENT_CAPTURE_BINDINGS['capture-b']['plan']
        plan = strict.loads(Path(plan_pin['path']).read_bytes())
        ack = pin(self.root / 'SYNTHETIC-model-ack.json', b'{"SYNTHETIC":"NOT_AN_ACTUAL_ROOT_ACK"}')
        execution = pin(self.root / 'SYNTHETIC-model-execution.json', strict.json_bytes({'scopes':[]}))
        data = dict(captureId='capture-b', captureScript=plan['runner'], execution=execution)
        request = dict(plan['outerRequestTemplate'], cmd=plan['outerRequestTemplate']['cmd'].replace('__ACTUAL_ROOT_ACK_SHA256__', ack['sha256']))
        summary = strict.json_bytes(dict(state='WRITES_STOPPED', captureId='capture-b', captureMatched=True, execution=execution, scopes=[])).decode() + '\n'
        terminal = dict(output=summary, wall_time_seconds=0.125, exit_code=0)
        direct = dict(schema='e02-actual-tool-custody-v1', operator='/root',
            launch=dict(toolName='tools.exec_command', actualArguments=request, unmodifiedResponse=terminal), polls=[])
        yielded = copy.deepcopy(direct)
        yielded['launch']['unmodifiedResponse'] = dict(output='', wall_time_seconds=0.001, session_id=501)
        yielded['polls'] = [dict(toolName='tools.write_stdin',
            actualArguments=dict(session_id=501, chars='', yield_time_ms=1000, max_output_tokens=10000), unmodifiedResponse=terminal)]
        mutations = []
        def variant(label, value, change, good=False):
            item=copy.deepcopy(value); change(item); mutations.append((label,item,good))
        variant('direct-terminal',direct,lambda v:None,True)
        variant('same-session-terminal-poll',yielded,lambda v:None,True)
        variant('missing-polls',yielded,lambda v:v.update(polls=[]))
        variant('wrong-session',yielded,lambda v:v['polls'][0]['actualArguments'].update(session_id=502))
        variant('nonempty-poll-input',yielded,lambda v:v['polls'][0]['actualArguments'].update(chars='x'))
        variant('nonzero-terminal',direct,lambda v:v['launch']['unmodifiedResponse'].update(exit_code=2))
        variant('fake-inner-api-EOF',direct,lambda v:v['launch']['unmodifiedResponse'].update(stdoutEOF=True))
        variant('command-substitution',direct,lambda v:v['launch']['actualArguments'].update(cmd='/usr/bin/true'))
        variant('workdir-substitution',direct,lambda v:v['launch']['actualArguments'].update(workdir='/tmp'))
        variant('duplicate-poll-after-terminal',yielded,lambda v:v['polls'].append(copy.deepcopy(v['polls'][0])))
        variant('fraction-outside-wall-time',direct,lambda v:v['launch']['unmodifiedResponse'].update(exit_code=0.0))
        for index,(label,value,good) in enumerate(mutations):
            with self.subTest(SYNTHETIC_custody_predicate=label):
                descriptor=pin(self.root / ('SYNTHETIC-custody-%d.json' % index), strict.json_bytes(value))
                nodes=dict(plan=plan_pin, release=ack, originalToolResponses=descriptor)
                files=strict.Files([str(self.root), str(Path(plan_pin['path']).parent), str(Path(consumer.CURRENT_SOURCE_PLAN['path']).parent)])
                if good: consumer.capture_original_tool(files,nodes,data,SimpleNamespace(forbidden={'/root'}))
                else:
                    with self.assertRaises(strict.Refusal): consumer.capture_original_tool(files,nodes,data,SimpleNamespace(forbidden={'/root'}))
        # Narrow legacy metadata exception: only root durationSeconds admits a
        # decimal; protocol DATA and every other execution field stay integral.
        model=dict(argv=[],exitCode=0,reaped=True,eof=dict(stdout=True,stderr=True),fault=None,
            durationSeconds=0.25,inputsBefore=[],inputsAfter=[],inputsUnchanged=True,
            stdout={},stderr={},scope='SYNTHETIC_DECODER_ONLY',snapshotNotRaceFree=True)
        for index,(changes,good) in enumerate([
            ({},True),({'durationSeconds':True},False),({'durationSeconds':64.0},False),
            ({'exitCode':0.0},False),({'eof':{'stdout':0.5,'stderr':True}},False)]):
            with self.subTest(SYNTHETIC_model_duration_decoder=index):
                value=dict(model,**changes)
                descriptor=pin(self.root/('SYNTHETIC-model-duration-%d.json'%index),strict.json_bytes(value))
                if good:consumer.model_execution_record(self.files,descriptor)
                else:
                    with self.assertRaises(strict.Refusal):consumer.model_execution_record(self.files,descriptor)


    def test_actor_union_and_same_session_review_refused(self):
        subject = dict(path=str(self.root / 'subject'), bytes=0, sha256='0' * 64)
        row = dict(kind='WINDOW', role='qa', actor='/root/operator', session='/root/operator', subject=subject,
                   decision='ACCEPT_EXACT_SCOPED_EVIDENCE', findings=[], review=subject, rawSessionEvidence=subject, visualChecks=[])
        value = dict(schema='e02-minimum-origin-envelope-v1', profileId=wire.PROFILE, method=subject, candidate=subject,
                     history=subject, windowSubjects=[], attemptSubjects=[], legacyContexts=[], reviews=[row], tools=[],
                     provenanceLimit='EXTERNALLY_AUTHENTICATED_COORDINATOR_TRANSCRIPTION_NOT_PORTABLE_ATTESTATION')
        origin = witness.Origin(self.files, value, {'/root/operator'})
        with self.assertRaises(strict.Refusal): origin.reviews(subject, 'WINDOW', ('qa',))

        # The new closed four-key DATA review helper uses synthetic DATA only.
        from types import SimpleNamespace
        decision='ACCEPT_CURRENT_PRODUCER3_REBUILT_BINDINGS3_DATA_ONLY'
        target=pin(self.root/'SYNTHETIC-review-target',b'SYNTHETIC_NOT_ACTUAL_CAPTURE')
        for index,(qa_actor,sec_actor,change,good) in enumerate([
            ('/root/SYNTHETIC_QA','/root/SYNTHETIC_SEC',None,True),
            ('/root/operator','/root/SYNTHETIC_SEC',None,False),
            ('/root/SYNTHETIC_QA','/root/SYNTHETIC_QA',None,False),
            ('/root/SYNTHETIC_QA','/root/SYNTHETIC_SEC','HOLD',False)]):
            with self.subTest(SYNTHETIC_current_capture_reviews=index):
                documents=[dict(role=role,session=session,decision=change or decision,subject=target)
                    for role,session in [('qa',qa_actor),('security',sec_actor)]]
                pins=[pin(self.root/('SYNTHETIC-review-%d-%d.json'%(index,i)),strict.json_bytes(value))
                    for i,value in enumerate(documents)]
                if good:consumer.capture_data_reviews(self.files,pins,target,decision,SimpleNamespace(forbidden={'/root/operator'}))
                else:
                    with self.assertRaises(strict.Refusal):consumer.capture_data_reviews(self.files,pins,target,decision,SimpleNamespace(forbidden={'/root/operator'}))

    def test_missing_entire_history_witness_refused(self):
        history = dict(attempts=[], legacyContexts=[])
        with self.assertRaises(strict.Refusal): consumer.provenance(self.files, dict(authors=['/root/a'], operators=['/root/o']), history, {})

    def test_failed_window_no_partial_export_contribution(self):
        # A producer-shaped early export is never accepted in place of a whole
        # consumer manifest/history/window graph.
        p = pin(self.root / 'failed-window.json', strict.json_bytes(dict(schema='e02-minimum-role-driver-result-v2',
                executionState='FAILED_UNQUALIFIED', observations=[dict(id='incoming-business')])) )
        with self.assertRaises(strict.Refusal): consumer.consume(self.files, p, p)

    def test_positive_app_wire_and_native_data_joins(self):
        data = publication_data(self.root)
        wire.publication(*data)

    def test_positive_identical_query_origin_is_not_client_receipt(self):
        data = publication_data(self.root, 'archive', 1, False)
        wire.publication(*data)
        self.assertIsNone(data[2]['delivery']); self.assertEqual(data[2]['validationOrigin'], wire.QUERY)

    def test_query_origin_for_required_initial_stage_refused(self):
        data = publication_data(self.root, 'incoming', 0, False)
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_query_origin_for_required_fresh_wrap_refused(self):
        data = publication_data(self.root, 'archive', 2, False)
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_stale_delivery_attempt_refused(self):
        data = publication_data(self.root)
        data[2]['delivery']['completionAttempt'] = dict(epoch=2, stageId='incoming-ordinary-chat')
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_stale_delivery_eose_generation_refused(self):
        data = publication_data(self.root)
        data[2]['delivery']['completionGeneration'] = dict(data[2]['gate'], eoseSequence=2)
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_send_callback_buffer_hash_mismatch_refused(self):
        data = publication_data(self.root)
        data[2]['publication']['sentFrames'][0]['callbackBufferHash'] = '0' * 64
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_send_callback_not_completed_refused(self):
        data = publication_data(self.root)
        data[2]['publication']['sentFrames'][0]['sendCallbackCompleted'] = False
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_copied_forward_frame_without_current_callback_refused(self):
        data = publication_data(self.root)
        data[2]['delivery']['sentSequence'] = data[2]['delivery']['rowSequence']
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_wrong_archive_outer_recipient_refused(self):
        data = publication_data(self.root, 'archive', 1, False)
        data[2]['event']['tags'] = [['p', wire.B]]
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def history_data(self):
        source = pin(self.root / 'source-subject.json', b'{"meaning":"SYNTHETIC_DATA_ONLY"}')
        attempts = []
        for i, role in enumerate(('incoming', 'archive', 'incoming')):
            outcome = pin(self.root / ('outcome-%d.json' % i), strict.json_bytes({'syntheticFailure': i == 2}))
            value = dict(schema='e02-minimum-attempt-subject-v1', profileId=wire.PROFILE, attemptId='synthetic-%d' % i,
                ordinaryRole=role, runId=('%032x' % (i + 1)), windowSubject=source if i < 2 else None,
                rawOutcome=outcome, authors=['/root/source-author-%d' % i], operators=['/root/operator-%d' % i],
                sourceSubject=source, outcomeClassification='COMPLETE_PENDING_INDEPENDENT_QUALIFICATION' if i < 2 else 'FAILED_UNQUALIFIED')
            subject = pin(self.root / ('attempt-%d.json' % i), strict.json_bytes(value))
            attempts.append(dict(subject=subject, disposition='CONTRIBUTE_WHOLE_WINDOW' if i < 2 else 'NO_CONTRIBUTION',
                                 classification=value['outcomeClassification'], reason='SYNTHETIC_DATA_ONLY'))
        legacy = dict(subject=source, authors=['/root/legacy-author'], operators=['/root/legacy-operator'], meaning='HISTORICAL_CONTEXT_NO_ROW_DONATION')
        history = dict(attempts=attempts, legacyContexts=[legacy])
        origin = dict(attemptSubjects=[r['subject'] for r in attempts], legacyContexts=[legacy])
        return dict(authors=['/root/consumer-author'], operators=['/root']), history, origin

    def test_positive_history_union_includes_failed_and_legacy_operators(self):
        forbidden, rows = consumer.provenance(self.files, *self.history_data())
        self.assertEqual(len(rows), 3)
        self.assertIn('/root/operator-2', forbidden); self.assertIn('/root/source-author-2', forbidden)
        self.assertIn('/root/legacy-operator', forbidden)

    def test_omitted_failed_attempt_rejected_by_external_inventory(self):
        candidate, history, origin = self.history_data(); history['attempts'] = history['attempts'][:2]
        with self.assertRaises(strict.Refusal): consumer.provenance(self.files, candidate, history, origin)

    def test_omitted_legacy_context_rejected(self):
        candidate, history, origin = self.history_data(); history['legacyContexts'] = []
        with self.assertRaises(strict.Refusal): consumer.provenance(self.files, candidate, history, origin)

    def test_failed_attempt_row_donation_refused(self):
        candidate, history, origin = self.history_data()
        history['attempts'][2]['disposition'] = 'CONTRIBUTE_WHOLE_WINDOW'
        with self.assertRaises(strict.Refusal): consumer.provenance(self.files, candidate, history, origin)

    def test_positive_actual_command_record_data_and_force_failure(self):
        (self.root / 'commands').mkdir()
        stdout = pin(self.root / 'commands/0001.stdout', b'[]\n')
        stderr = pin(self.root / 'commands/0001.stderr', b'')
        value = dict(argv=['/usr/bin/docker', 'inspect', '0' * 64], launchAttempt=True, pid=100,
             exit=0, reaped=True, forced=False, timedOut=False, error=None, stdout=stdout, stderr=stderr,
             observedBytes=dict(stdout=3, stderr=0), stdoutEOF=True, stderrEOF=True)
        p = pin(self.root / 'commands/0001.json', strict.json_bytes(value))
        self.assertEqual(witness.commands(self.files, [p], self.root), [value])
        value['forced'] = True
        q = dict(p, sha256=hashlib.sha256(strict.json_bytes(value)).hexdigest(), bytes=len(strict.json_bytes(value)))
        (self.root / 'commands/0001.json').write_bytes(strict.json_bytes(value))
        with self.assertRaises(strict.Refusal): witness.commands(strict.Files([str(self.root)]), [q], self.root)

    def source_finding_data(self):
        def proof(name): return pin(self.root / name, b'SYNTHETIC_DATA_ONLY_NOT_ACTUAL_REVIEW')
        subject = proof('reviewed-subject')
        finding = dict(id='retained-actual-finding-id', severity='LOW', classification='NONOPERATIVE_UNUSED_PLAN_NSEC',
                       disposition='ACCEPTED_WITHOUT_RUNTIME_INPUT_CHANGE', actualDispositionEvidence=proof('disposition'))
        row = dict(kind='SOURCE', role='qa', actor='/root/independent-qa', session='/root/independent-qa', subject=subject,
                   decision='ACCEPT_EXACT_SCOPED_EVIDENCE', findings=[finding], review=proof('review'),
                   rawSessionEvidence=proof('session-origin'), visualChecks=[])
        value = dict(schema='e02-minimum-origin-envelope-v1', profileId=wire.PROFILE, method=subject, candidate=subject,
                     history=subject, windowSubjects=[], attemptSubjects=[], legacyContexts=[], reviews=[row], tools=[],
                     provenanceLimit='EXTERNALLY_AUTHENTICATED_COORDINATOR_TRANSCRIPTION_NOT_PORTABLE_ATTESTATION')
        return witness.Origin(self.files, value, {'/root/operator'}), subject, finding

    def test_known_nonoperative_low_preserved_with_actual_disposition_operand(self):
        origin, subject, finding = self.source_finding_data()
        origin.reviews(subject, 'SOURCE', ('qa',))
        self.assertEqual(finding['id'], 'retained-actual-finding-id')

    def test_medium_source_finding_cannot_use_nonoperative_exception(self):
        origin, subject, finding = self.source_finding_data(); finding['severity'] = 'MEDIUM'
        with self.assertRaises(strict.Refusal): origin.reviews(subject, 'SOURCE', ('qa',))

    def test_selection_positive_owned_edittext_ancestor(self):
        data = selection_data(self.root)
        self.assertEqual(gui.selection(*data)['commandSequenceLast'], 13)

    def test_selection_foreign_edittext_ancestor_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'foreign'))

    def test_selection_disabled_edittext_ancestor_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'disabled'))

    def test_selection_nonempty_edittext_ancestor_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'nonempty'))

    def test_selection_detached_message_label_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'detached'))

    def test_selection_ambiguous_edittext_ancestors_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'ambiguous'))

    def test_selection_foreign_message_label_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'foreign-label'))

    def test_selection_disabled_message_label_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'disabled-label'))

    def test_selection_positive_exact_source_dm_warning(self):
        gui.selection(*selection_data(self.root, 'warning'))

    def test_selection_foreign_warning_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'warning-foreign'))

    def test_selection_disabled_warning_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'warning-disabled'))

    def test_selection_duplicate_warning_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'warning-duplicate'))

    def test_selection_warning_and_message_label_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'warning-and-label'))

    def test_selection_no_composer_or_warning_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'missing'))

    def test_selection_warning_without_back_context_refused(self):
        with self.assertRaises(strict.Refusal): gui.selection(*selection_data(self.root, 'warning', include_back=False))

    def native_reply_fixture(self, mode):
        data = publication_data(self.root)
        files, _, record, _, _, _ = data
        value = files.doc(record['validation']['validation'])
        source = dict(ok=True, value=files.read(value['rustSource']).decode('utf-8'))
        normalized = copy.deepcopy(value['rust'])
        correct = dict(ok=True, value=normalized)
        second = {'correct': correct, 'unwrapped': normalized, 'error': dict(ok=False, error='SYNTHETIC_RPC_ERROR'),
            'extra': dict(correct, error=None), 'wrong': dict(ok=True, value=False),
            'double': dict(ok=True, value=correct), 'missing': dict(ok=True)}
        if mode in second:
            replies = [source, second[mode]]
        elif mode == 'one': replies = [source]
        elif mode == 'three': replies = [source, correct, correct]
        elif mode == 'zero': replies = []
        elif mode == 'missing-source': replies = [correct, correct]
        else: raise ValueError('Closed synthetic RPC case')
        raw = b''.join(strict.json_bytes(v) + b'\n' for v in replies)
        value['rustStdout'] = pin(self.root / 'changed-rpc-stdout.jsonl', raw)
        record['validation']['validation'] = pin(self.root / 'changed-rpc-validation.json', strict.json_bytes(value))
        return data

    def test_native_actual_nested_rpc_envelope_positive(self):
        wire.publication(*self.native_reply_fixture('correct'))

    def test_native_unwrapped_rpc_reply_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('unwrapped'))

    def test_native_error_rpc_reply_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('error'))

    def test_native_extra_rpc_envelope_key_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('extra'))

    def test_native_wrong_rpc_value_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('wrong'))

    def test_native_double_rpc_envelope_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('double'))

    def test_native_missing_rpc_value_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('missing'))

    def test_native_missing_second_rpc_line_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('one'))

    def test_native_extra_rpc_line_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('three'))

    def test_native_zero_rpc_lines_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('zero'))

    def test_native_missing_source_echo_refused(self):
        with self.assertRaises(strict.Refusal): wire.publication(*self.native_reply_fixture('missing-source'))

    def test_identical_query_same_id_altered_payload_candidate_refused(self):
        data = publication_data(self.root, 'archive', 1, False, candidate_payload={'content': 'changed'})
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_identical_query_same_id_altered_tags_candidate_refused(self):
        data = publication_data(self.root, 'archive', 1, False, candidate_payload={'tags': [['p', wire.B]]})
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_identical_query_exact_candidate_uncompleted_callback_refused(self):
        data = publication_data(self.root, 'archive', 1, False, candidate_payload={})
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_qualified_delivery_same_id_altered_payload_refused(self):
        data = publication_data(self.root, candidate_payload={'content': 'changed'})
        with self.assertRaises(strict.Refusal): wire.publication(*data)

    def test_late_same_id_altered_payload_is_retained_not_interval_absence(self):
        data = publication_data(self.root, 'archive', 1, False, candidate_payload={'content': 'late changed'}, late_candidate=True)
        wire.publication(*data)
        self.assertEqual(data[1].rows[-1]['direction'], 'RELAY_TO_APP')
        self.assertEqual(data[1].frames[len(data[1].rows)][1][2]['content'], 'late changed')

    def test_candidate_predicate_selected_id_not_whole_payload(self):
        gate = dict(connection=1, subscription='actual-sub')
        value = ['EVENT', 'actual-sub', {'id': 'a' * 64, 'content': 'different'}]
        self.assertTrue(wire.candidate_app_frame(value, 1, gate, 'a' * 64))
        self.assertFalse(wire.candidate_app_frame(value, 2, gate, 'a' * 64))
        self.assertFalse(wire.candidate_app_frame(['EVENT', 'other', value[2]], 1, gate, 'a' * 64))
        self.assertFalse(wire.candidate_app_frame(value, 1, gate, 'b' * 64))


if __name__ == '__main__':
    unittest.main(verbosity=2)
