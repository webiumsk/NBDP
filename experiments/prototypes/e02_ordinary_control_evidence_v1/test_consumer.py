"""SOURCE-PREPARED synthetic DATA controls, never Android/Nostr runtime evidence.

Do not run until independent source review and coordinator release. Fixtures
deliberately contain fake validation results, helper APK/receipts and PNG data.
Only externally trusted actual observation reviews can authorize real evidence.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('e02_supplement_control_subject', HERE / 'consumer.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


class SyntheticDataControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nbdp-e02-data-controls-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.counter = 0
        self.files = C.Files()
        self.body = {'protocol': 'NBDP/experiment', 'version': 1, 'from': C.A,
                     'to': C.B, 'note': 'CONTROL_FIXTURE_faktúra_𐐀_only'}
        self.rumor = self.make_rumor(self.body)
        self.expected = dict(id='js-to-rust-incoming-rs-relay', direction='js-to-rust',
            role='incoming', relay='rs-relay', account=C.B, peer=C.A,
            rumor=self.doc(self.rumor), visibleToken='CONTROL_FIXTURE_faktúra_𐐀_only', dispatch=True)
        self.raw = self.doc(self.rumor, pretty=True)
        self.wire = self.doc(dict(kind=1059, id='f' * 64, tags=[['p', C.B]]))
        wire_text = Path(self.wire['path']).read_text()
        request = dict(op='validate', wire=wire_text, secret='0' * 63 + '2',
                       role='incoming', expectedSender=C.A)
        result = dict(ok=True, decrypts=[1, 1], value=dict(rumor=self.rumor, role='incoming', dispatch=True))
        self.proof = dict(schema='e02-ordinary-transport-v1',
            frame=self.doc(['EVENT', 'CONTROL_FIXTURE_subscription', json.loads(wire_text)]),
            wire=self.wire, jsRequest=self.doc(request), rustRequest=self.doc(request),
            jsResult=self.doc(result), rustResult=self.doc(result))
        self.helper = dict(schema='e02-clipboard-capture-v1', caseId=self.expected['id'],
            action='CAPTURE', status='CAPTURED', mime='text/plain',
            bytes=self.raw['bytes'], sha256=self.raw['sha256'], elapsedRealtimeNanos=7,
            foregroundFocus=True, wallClockMillis=8, clipboardItemCount=1, clipboardTimestamp=6)
        self.selection = dict(schema='e02-ordinary-selection-v1',
            observationId=self.expected['id'], account=C.B, peer=C.A, rumorId=self.rumor['id'],
            action='COPY_RAW_JSON', method='ANDROID_LOCAL_FOREGROUND',
            helperPackage='org.nbdp.clipboard.capture',
            helperArtifact=self.put(b'CONTROL_FIXTURE_NOT_AN_APK'),
            helperReceipt=self.doc(self.helper), capturedMonotonicNs=9)
        self.row = dict(id=self.expected['id'], status='COMPLETE', transport=self.doc(self.proof),
            selection=self.doc(self.selection), uiPng=self.put(b'\x89PNG\r\n\x1a\n' + b'0' * 32),
            uiXml=self.put(('<hierarchy><node text="' + self.expected['visibleToken'] + '"/></hierarchy>').encode()),
            rawClientRumor=self.raw, error=None)

    def put(self, raw):
        self.counter += 1
        p = self.root / (str(self.counter) + '.bin')
        p.write_bytes(raw)
        return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def doc(self, value, pretty=False):
        return self.put(json.dumps(value, ensure_ascii=False,
                        indent=2 if pretty else None, separators=None if pretty else (',', ':')).encode())

    @staticmethod
    def make_rumor(body):
        r = dict(pubkey=C.A, created_at=1, kind=14, tags=[['p', C.B]],
                 content=json.dumps(body, ensure_ascii=False, separators=(',', ':')))
        array = [0, r['pubkey'], r['created_at'], r['kind'], r['tags'], r['content']]
        r['id'] = hashlib.sha256(json.dumps(array, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        return r

    def inspect(self, row=None):
        return C.inspect_observation(self.row if row is None else row, self.expected, self.files)

    def test_pretty_json_utf8_and_whole_data_join(self):
        self.assertEqual(self.inspect(), 'COMPLETE')
        self.assertNotEqual(Path(self.raw['path']).read_bytes(), Path(self.expected['rumor']['path']).read_bytes())

    def test_client_export_empty_signature_only_preserves_raw_pin(self):
        raw = self.doc(dict(self.rumor, sig=''), pretty=True)
        receipt = self.doc(dict(self.helper, bytes=raw['bytes'], sha256=raw['sha256']))
        row = dict(self.row, rawClientRumor=raw,
                   selection=self.doc(dict(self.selection, helperReceipt=receipt)))
        self.assertEqual(self.inspect(row), 'COMPLETE')
        self.assertEqual(self.files.pins[raw['path']], raw)
        self.assertEqual(json.loads(Path(raw['path']).read_bytes())['sig'], '')
        with self.assertRaisesRegex(C.Refusal, 'CLOSED_KEYS'):
            C.rumor(dict(self.rumor, sig=''))
        proof = copy.deepcopy(self.proof)
        result = json.loads(Path(proof['jsResult']['path']).read_text())
        result['value']['rumor']['sig'] = ''
        proof['jsResult'], proof['rustResult'] = self.doc(result), self.doc(result)
        with self.assertRaisesRegex(C.Refusal, 'ACTUAL_VALIDATED_INNER_AND_ROLE'):
            self.inspect(dict(row, transport=self.doc(proof)))

    def test_client_export_nonempty_null_nonstring_and_extra_fields_refuse(self):
        values = [dict(self.rumor, sig=value) for value in ('a' * 128, None, 0, False, [])]
        values += [dict(self.rumor, sig='', extra='ignored'), dict(self.rumor, extra='ignored')]
        for value in values:
            raw = self.doc(value)
            receipt = self.doc(dict(self.helper, bytes=raw['bytes'], sha256=raw['sha256']))
            row = dict(self.row, rawClientRumor=raw,
                       selection=self.doc(dict(self.selection, helperReceipt=receipt)))
            with self.subTest(value=value), self.assertRaises(C.Refusal):
                self.inspect(row)

    def test_changed_actual_inner_is_failure_even_when_its_id_is_valid(self):
        changed = self.make_rumor(dict(self.body, note='CONTROL_FIXTURE_altered'))
        row = dict(self.row, rawClientRumor=self.doc(changed))
        with self.assertRaisesRegex(C.Mismatch, 'RETAINED_RUMOR'):
            self.inspect(row)

    def test_boolean_integer_extra_field_and_duplicate_json_refuse(self):
        values = [b'{"n":-0}', b'{"n":1.0}', b'{"n":9007199254740992}',
                  b'{"a":1,"a":2}', b'{"s":"\\ud800"}', b'NaN']
        for raw in values:
            with self.subTest(raw=raw), self.assertRaises((C.Refusal, UnicodeError)):
                C.loads(raw)
        self.assertFalse(C.equal({'n': 0}, {'n': False}))
        with self.assertRaises(C.Refusal):
            C.rumor(dict(self.rumor, created_at=True))
        with self.assertRaises(C.Refusal):
            C.rumor(dict(self.rumor, extra='ignored'))

    def test_file_drift_and_symlink_refuse(self):
        pin = self.put(b'original')
        self.files.checked(pin)
        Path(pin['path']).write_bytes(b'changed!')
        with self.assertRaises(C.Refusal):
            self.files.current()
        link = self.root / 'alias'
        link.symlink_to(Path(self.raw['path']))
        with self.assertRaises(C.Refusal):
            C.Files().checked(dict(self.raw, path=str(link)))

    def test_file_data_and_aggregate_bounds_remain_distinct(self):
        with self.assertRaisesRegex(C.Refusal, 'SAFE_INTEGER'):
            C.Files().checked(dict(self.raw, bytes=C.FILE_LIMIT + 1))
        with self.assertRaisesRegex(C.Refusal, 'SAFE_INTEGER'):
            C.Files().checked(dict(self.raw, bytes=C.DATA_LIMIT + 1), data=True)
        full = C.Files()
        full.bytes = 2 * 1024 ** 3
        with self.assertRaisesRegex(C.Refusal, 'TOTAL_INPUT_BOUND'):
            full.checked(self.raw)

    def test_delivered_frame_and_both_requests_are_joined(self):
        proof = copy.deepcopy(self.proof)
        request = json.loads(Path(proof['rustRequest']['path']).read_text())
        proof['rustRequest'] = self.doc(dict(request, role='archive'))
        with self.assertRaisesRegex(C.Refusal, 'BOTH_ACTUAL_REQUEST'):
            self.inspect(dict(self.row, transport=self.doc(proof)))

    def test_both_validator_results_and_dispatch_type_are_whole(self):
        proof = copy.deepcopy(self.proof)
        result = json.loads(Path(proof['rustResult']['path']).read_text())
        result['value']['dispatch'] = 1
        proof['rustResult'] = self.doc(result)
        with self.assertRaisesRegex(C.Refusal, 'BOTH_ACTUAL_VALIDATION'):
            self.inspect(dict(self.row, transport=self.doc(proof)))

    def test_helper_receipt_stale_clipboard_and_wrong_role_refuse(self):
        for changed in (dict(self.helper, sha256='0' * 64),
                        dict(self.helper, foregroundFocus=False),
                        dict(self.helper, clipboardItemCount=2)):
            selection = dict(self.selection, helperReceipt=self.doc(changed))
            with self.subTest(changed=changed), self.assertRaisesRegex(C.Refusal, 'HELPER_RAW'):
                self.inspect(dict(self.row, selection=self.doc(selection)))
        with self.assertRaisesRegex(C.Refusal, 'ACTUAL_SELECTED_NOTE'):
            self.inspect(dict(self.row, selection=self.doc(dict(self.selection, account=C.A))))

    def test_screenshot_or_fixture_decryption_cannot_replace_raw_export(self):
        with self.assertRaises((C.Refusal, TypeError)):
            self.inspect(dict(self.row, rawClientRumor=None))
        with self.assertRaisesRegex(C.Mismatch, 'RENDERED_CONTENT'):
            self.inspect(dict(self.row, uiXml=self.put(b'<hierarchy><node text="Hello"/></hierarchy>')))

    def test_one_complete_slice_stays_partial_and_missing_rows_visible(self):
        config = self.doc({'mode': 'CONTROL_FIXTURE_CONFIG'})
        release = self.doc({'mode': 'CONTROL_FIXTURE_NOT_A_RELEASE'})
        plan_pin = self.doc({'mode': 'CONTROL_FIXTURE_PLAN_SUBJECT'})
        ids = [self.expected['id']] + ['CONTROL_FIXTURE_missing_' + str(i) for i in range(7)]
        plan = dict(runId='control_fixture', operator='/root/control_operator',
            client={'mode': 'CONTROL_FIXTURE_NOT_A_CLIENT'}, runConfig=config, runRelease=release,
            expected=[self.expected] + [dict(self.expected, id=i) for i in ids[1:]])
        receipt = self.doc(dict(runId=plan['runId'], runConfig=config, runRelease=release))
        capture = dict(schema='e02-ordinary-capture-v1', runId=plan['runId'], operator=plan['operator'],
            plan=plan_pin, client=plan['client'], executionState='PARTIAL', runConfig=config,
            runRelease=release, driverReceipt=receipt, observations=[self.row])
        value = C.inspect_capture(plan, plan_pin, capture, self.files)
        self.assertEqual(value['status'], 'PARTIAL')
        self.assertEqual(value['missingObservationIds'], ids[1:])
        self.assertFalse(value['canonicalE02Changed'])
        with self.assertRaisesRegex(C.Refusal, 'NO_FALSE_COMPLETE'):
            C.inspect_capture(plan, plan_pin, dict(capture, executionState='COMPLETE'), C.Files())

    def test_all_complete_rows_preserve_partial_capture_header(self):
        config, release, plan_pin = [self.doc({'mode': 'CONTROL_FIXTURE_' + name})
                                     for name in ('CONFIG', 'NOT_A_RELEASE', 'PLAN_SUBJECT')]
        expected, rows = [], []
        for index in range(8):
            row_id = 'control-fixture-' + str(index)
            expected.append(dict(self.expected, id=row_id))
            row = dict(self.row, id=row_id)
            for key in ('transport', 'uiPng', 'uiXml', 'rawClientRumor'):
                row[key] = self.put(Path(row[key]['path']).read_bytes())
            receipt = self.doc(dict(self.helper, caseId=row_id,
                bytes=row['rawClientRumor']['bytes'], sha256=row['rawClientRumor']['sha256']))
            row['selection'] = self.doc(dict(self.selection, observationId=row_id, helperReceipt=receipt))
            rows.append(row)
        plan = dict(runId='control_fixture', operator='/root/control_operator',
            client={'mode': 'CONTROL_FIXTURE_NOT_A_CLIENT'}, runConfig=config,
            runRelease=release, expected=expected)
        receipt = self.doc(dict(runId=plan['runId'], runConfig=config, runRelease=release))
        capture = dict(schema='e02-ordinary-capture-v1', runId=plan['runId'], operator=plan['operator'],
            plan=plan_pin, client=plan['client'], executionState='PARTIAL', runConfig=config,
            runRelease=release, driverReceipt=receipt, observations=rows)
        value = C.inspect_capture(plan, plan_pin, capture, C.Files())
        self.assertEqual(value['status'], 'PARTIAL')
        self.assertEqual(value['matchedObservationIds'], [row['id'] for row in expected])
        self.assertEqual(value['missingObservationIds'], [])
        self.assertFalse(value['canonicalE02Changed'])
        complete = C.inspect_capture(plan, plan_pin, dict(capture, executionState='COMPLETE'), C.Files())
        self.assertEqual(complete['status'], 'MATCHED_SUPPLEMENT_ONLY')

    def test_external_hash_missing_and_self_operator_review_refuse(self):
        with self.assertRaises(C.Refusal):
            C.Files().external(self.raw['path'], '0' * 64)
        plan_pin, capture_pin = self.doc({'CONTROL_FIXTURE': 'plan'}), self.doc({'CONTROL_FIXTURE': 'capture'})
        plan = dict(authors=['/root/control_author'], operator='/root/control_operator')
        capture = dict(observations=[self.row])
        reviews = []
        for role in ('qa', 'security'):
            r = dict(schema='e02-ordinary-observation-review-v1', role=role,
                session='/root/control_' + role, decision='ACCEPT_ORDINARY_CLIENT_OBSERVATIONS_ONLY',
                plan=plan_pin, subject=capture_pin, acceptedObservationIds=[self.row['id']], findings=[])
            reviews.append((role, self.doc(r)))
        C.actual_reviews(plan, plan_pin, capture, capture_pin, reviews, C.Files())
        wrong = json.loads(Path(reviews[0][1]['path']).read_text())
        wrong['subject'] = plan_pin
        with self.assertRaisesRegex(C.Refusal, 'EXACT_ACTUAL_REVIEW_SUBJECT'):
            C.actual_reviews(plan, plan_pin, capture, capture_pin,
                             [('qa', self.doc(wrong)), reviews[1]], C.Files())
        r = json.loads(Path(reviews[0][1]['path']).read_text())
        r['session'] = plan['operator']
        reviews[0] = ('qa', self.doc(r))
        with self.assertRaisesRegex(C.Refusal, 'INDEPENDENT_NONAUTHOR'):
            C.actual_reviews(plan, plan_pin, capture, capture_pin, reviews, C.Files())


if __name__ == '__main__':
    print('SYNTHETIC_DATA_CONTROLS_ONLY: no Android, Nostr validation or E02 qualification.')
    unittest.main()
