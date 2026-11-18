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


def publication_data(root, role='incoming', index=0, observed=True):
    """Fabricated DATA joins only: no signing/encryption/execution/review claim."""
    files = strict.Files([str(root)])
    def put(name, value, raw=False):
        return pin(root / name, value if raw else strict.json_bytes(value))
    spec = wire.stage(role, index)
    expected = inner('{"protocol":"NBDP/experiment","synthetic":true}') if spec['oracle'] == 'business' else inner()
    event = dict(pubkey=wire.A, created_at=1, kind=1059, tags=[['p', wire.ACCOUNTS[role]]], content='synthetic-encrypted-placeholder', sig='0' * 128)
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
        forwarded = row('RELAY_TO_APP', connection=1, rawBase64=b64(strict.json_bytes(['EVENT', 'actual-sub', event])), publicationGeneration=gen, publicationAttempt=attempt)
        callback = row('APP_SOCKET_SEND_COMPLETE', connection=1, sourceSequence=forwarded['sequence'], publicationGeneration=gen, publicationAttempt=attempt)
        delivery = dict(connection=1, subscription='actual-sub', rowSequence=forwarded['sequence'], sentSequence=callback['sequence'],
                        forwardGeneration=gen, completionGeneration=gen, forwardAttempt=attempt, completionAttempt=attempt)
    close = row('PUBLICATION_WINDOW_CLOSED', stageId=spec['id'], eventId=event['id'], attempt=attempt,
                intentSequence=intentseq, actualNewAppFrameObserved=observed, candidateAppFrameSeen=observed, elapsedNanoseconds=100)
    querysent = put('query-sent.json', strict.json_bytes(['REQ', 'e02-owned-query', {'ids': [event['id']], 'limit': 1}]), True)
    row('PRODUCER_TO_RELAY', exchangeLabel=spec['id'] + '-query', rawBase64=b64(files.read(querysent)), frame=querysent)
    qr = dict(rawBase64=b64(strict.json_bytes(['EVENT', 'e02-owned-query', event])), frame=['EVENT', 'e02-owned-query', event])
    qe = dict(rawBase64=b64(b'["EOSE","e02-owned-query"]'), frame=['EOSE', 'e02-owned-query'])
    for reply in (qr, qe): row('RELAY_TO_PRODUCER', exchangeLabel=spec['id'] + '-query', rawBase64=reply['rawBase64'])
    proxy_pin = put('capture.jsonl', b''.join(strict.json_bytes(r) + b'\n' for r in rows), True)
    proxy = wire.Proxy(files, proxy_pin)
    def sentrow(p, message):
        return dict(frame=p, eventId=event['id'] if message == 'EVENT' else None, messageType=message,
                    sendInvoked=True, sendCallbackCompleted=True, callbackBufferHash=p['sha256'])
    publication = dict(ack=[ack], received=[], eose=None, sentFrames=[sentrow(sent, 'EVENT')], elapsedNanoseconds=100)
    query = dict(ack=[], received=[qr], eose=qe, sentFrames=[sentrow(querysent, 'REQ')], elapsedNanoseconds=100)
    prepared = put('prepared.json', dict(rumors={spec['oracle']: expected}, events=[event] * (index + 1)))
    intent = put('intent.json', dict(schema='e02-minimum-publish-intent-v1', profileId=wire.PROFILE,
                 windowId=wire.WINDOWS[role], stage=spec, attempt=attempt, intentSequence=intentseq, prepared=prepared, gate=gate, issuedUTC='2026-10-24T00:00:00.000Z'))
    origin = wire.APP if observed else wire.QUERY
    window = put('window.json', dict(schema='e02-minimum-publication-window-v1', profileId=wire.PROFILE,
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
    transport = put('transport.json', dict(schema='e02-minimum-transport-v1', frame=framepin, wire=wirepin, jsRequest=jsr, rustRequest=rr, jsResult=js, rustResult=rust))
    src = put('rust-source.rs', b'SYNTHETIC_DATA_NOT_A_PRODUCER', True)
    binary = put('rust-binary', b'SYNTHETIC_NOT_EXECUTED', True)
    stdin = put('stdin.jsonl', strict.json_bytes({'op': 'source'}) + b'\n' + strict.json_bytes(request) + b'\n', True)
    stdout = put('stdout.jsonl', strict.json_bytes({'ok': True, 'value': files.read(src).decode()}) + b'\n' + strict.json_bytes(normalized) + b'\n', True)
    stderr = put('stderr.bin', b'', True)
    validation = put('validation.json', dict(schema='e02-minimum-validated-wire-record-v1', profileId=wire.PROFILE,
        windowId=wire.WINDOWS[role], stageId=spec['id'], origin=origin, clientReceiptEstablished=observed,
        transport=transport, rustBinary=binary, rustSource=src, rustInput=stdin, rustStdout=stdout, rustStderr=stderr,
        rustExit=0, rustSignal=None, actualQueriedEvent=event, js=normalized, rust=normalized,
        clientRetention='NOT_ESTABLISHED_BY_TRANSPORT_VALIDATION'))
    producer = put('producer.json', dict(schema='e02-minimum-producer-validation-v1', stageId=spec['id'], actualPublishedEvent=event,
        result=normalized, meaning='SYNTHETIC_DATA_ONLY'))
    record = dict(schema='e02-minimum-stage-publication-v1', profileId=wire.PROFILE, windowId=wire.WINDOWS[role], stage=spec,
        attempt=attempt, intent=intent, publicationWindow=window, gate=gate, publication=publication, query=query, event=event,
        actualNewAppFrameObserved=observed, delivery=delivery, validation=dict(transport=transport, validation=validation),
        producerValidation=producer, clientRetention='UNVERIFIED_REQUIRES_FRESH_CLIENT_SELECTION_EXPORT', validationOrigin=origin,
        replayLimit=None if observed else 'SYNTHETIC bounded interval, not client receipt')
    return files, proxy, record, expected, spec, role


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

    def test_actor_union_and_same_session_review_refused(self):
        subject = dict(path=str(self.root / 'subject'), bytes=0, sha256='0' * 64)
        row = dict(kind='WINDOW', role='qa', actor='/root/operator', session='/root/operator', subject=subject,
                   decision='ACCEPT_EXACT_SCOPED_EVIDENCE', findings=[], review=subject, rawSessionEvidence=subject, visualChecks=[])
        value = dict(schema='e02-minimum-origin-envelope-v1', profileId=wire.PROFILE, method=subject, candidate=subject,
                     history=subject, windowSubjects=[], attemptSubjects=[], legacyContexts=[], reviews=[row], tools=[],
                     provenanceLimit='EXTERNALLY_AUTHENTICATED_COORDINATOR_TRANSCRIPTION_NOT_PORTABLE_ATTESTATION')
        origin = witness.Origin(self.files, value, {'/root/operator'})
        with self.assertRaises(strict.Refusal): origin.reviews(subject, 'WINDOW', ('qa',))

    def test_missing_entire_history_witness_refused(self):
        history = dict(attempts=[], legacyContexts=[])
        with self.assertRaises(strict.Refusal): consumer.provenance(self.files, dict(authors=['/root/a'], operators=['/root/o']), history, {})

    def test_failed_window_no_partial_export_contribution(self):
        # A producer-shaped early export is never accepted in place of a whole
        # consumer manifest/history/window graph.
        p = pin(self.root / 'failed-window.json', strict.json_bytes(dict(schema='e02-minimum-role-driver-result-v1',
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
