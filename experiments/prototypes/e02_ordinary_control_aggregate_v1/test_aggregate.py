"""SOURCE-PREPARED SYNTHETIC DATA CONTROLS ONLY; no runtime or review evidence.

No test was run by the author. All child/tool/crypto/helper/review artifacts below
are deliberately fake, conspicuously named temporary DATA fixtures. Tests patch
only expensive exact-APK and canonical-prerequisite admission, not the validators
under test. No subprocess, Docker, Android, crypto validation or external review
is executed. Source review and separate coordinator test release are required.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('e02_aggregate_data_subject', HERE / 'aggregate.py')
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


class SyntheticDataControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nbdp-e02-aggregate-SYNTHETIC-DATA-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sequence = 0
        self.evaluation_sequence = 0
        self.rumor_suffix = ''
        self.consumer_pin = self.pin(A.CONSUMER)
        self.C = A.load_consumer(self.consumer_pin)
        self.basis = self.put(self.root / 'SYNTHETIC_DATA_COMMON_SOURCE.bin', b'SYNTHETIC_DATA_NOT_EXECUTED')
        self.client = dict(commit=self.C.CLIENT_COMMIT,
            apk=self.put(self.root / 'SYNTHETIC_DATA_NOT_AN_APK.bin', b'SYNTHETIC_DATA_NOT_AN_APK'),
            package='com.vitorpamplona.amethyst.debug', versionName='1.17.0-DEBUG', versionCode=462)
        self.prerequisites = {name: self.doc(self.root / ('SYNTHETIC_DATA_NOT_' + name + '.json'),
                                             {'SYNTHETIC_DATA_NO_CANONICAL_EXECUTION': name}) for name in ('E01', 'E02')}
        self.candidate = dict(schema='e02-ordinary-aggregate-candidate-v1', id='SYNTHETIC_DATA_NOT_RUNTIME',
            client=self.client, prerequisites=self.prerequisites, basis=[self.basis],
            scope='ORDINARY_KIND14_EIGHT_CELL_SUPPLEMENT_ONLY')
        self.candidate_pin = self.doc(self.root / 'SYNTHETIC_DATA_candidate.json', self.candidate)
        self.raw_review = self.put(self.root / 'SYNTHETIC_DATA_NO_REVIEW_OCCURRED.txt',
                                  b'SYNTHETIC DATA ONLY. No independent review or execution occurred.')

    @staticmethod
    def pin(path):
        raw = path.read_bytes()
        return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def put(self, path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
        return self.pin(path)

    def doc(self, path, value):
        return self.put(path, json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode())

    @staticmethod
    def get(pin):
        return json.loads(Path(pin['path']).read_bytes())

    @staticmethod
    def rewrite(pin, value):
        # Unit fixture mutation before inspection, never an original runtime edit.
        path = Path(pin['path'])
        path.write_bytes(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode())
        return SyntheticDataControls.pin(path)

    @staticmethod
    def guest(pin):
        return dict(pin, path='/session/fixtures/' + Path(pin['path']).name)

    def rumor(self, direction):
        sender, recipient = (self.C.A, self.C.B) if direction == 'js-to-rust' else (self.C.B, self.C.A)
        body = dict(protocol='NBDP/experiment', version=1, **{'from': sender, 'to': recipient},
                    note='SYNTHETIC_DATA_faktúra_𐐀_NOT_RUNTIME' + self.rumor_suffix)
        value = dict(pubkey=sender, created_at=1700000001, kind=14, tags=[['p', recipient]],
                     content=json.dumps(body, ensure_ascii=False, separators=(',', ':')))
        serialized = [0, value['pubkey'], value['created_at'], 14, value['tags'], value['content']]
        value['id'] = hashlib.sha256(json.dumps(serialized, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        return value

    def member(self, cell=('js-to-rust', 'incoming', 'rs-relay')):
        self.sequence += 1
        run_id = '%032x' % self.sequence
        root = self.root / run_id
        root.mkdir()
        direction, role, relay = cell
        scope = 'SYNTHETIC_DATA_' + '_'.join(cell)
        source_pins = []
        for name in ('supervisor.py', 'lease_guard.py', 'android_driver.py', 'ui-plan.json', 'fixture.mjs', 'fixture-plan.json'):
            source = self.put(root / 'SYNTHETIC_DATA_sources' / name, ('SYNTHETIC_DATA_NOT_EXECUTED_' + name).encode())
            source_pins.append(source)
            self.put(root / 'input' / name, Path(source['path']).read_bytes())
        all_sources = source_pins + [self.basis]
        opaque = self.doc(root / 'SYNTHETIC_DATA_opaque.json', {'SYNTHETIC_DATA_ONLY': True})
        config = dict(schema='e02-single-cell-runtime-plan-v1', scope=scope,
            runtimeImage='SYNTHETIC_DATA_NOT_AN_IMAGE', relayImage='SYNTHETIC_DATA_NOT_AN_IMAGE',
            sdkRoot='SYNTHETIC_DATA_NOT_AN_SDK', amethystApk=self.client['apk'],
            helperApk=self.put(root / 'SYNTHETIC_DATA_helper.bin', b'SYNTHETIC_DATA_NOT_HELPER_APK'),
            runId=run_id, originalLeaseSeconds=1800, sourceAndDependencyPins=source_pins,
            sdkInventory=opaque, guardBundleInventory=opaque, guardBundleRoot='SYNTHETIC_DATA_NOT_A_GUARD',
            relayConfig=opaque, state='SYNTHETIC_DATA_NO_EXECUTION', canonicalE02='PARTIAL22_UNCHANGED')
        config_pin = self.doc(root / 'SYNTHETIC_DATA_config.json', config)
        subject = dict(schema='e02-first-cell-complete-source-config-subject-v1', revision=1,
            coordinator='SYNTHETIC_DATA_OPERATOR', scope=scope, sources=all_sources,
            proposedRunConfig=config_pin, priorSubject=opaque, actualPreparationEvidence=[opaque],
            cleanupMockControls='SYNTHETIC_DATA_NOT_EXECUTED', guardLocalControls='SYNTHETIC_DATA_NOT_EXECUTED',
            consumerDataControls='SYNTHETIC_DATA_NOT_EXECUTED', fixturePureControls='SYNTHETIC_DATA_NOT_EXECUTED',
            rootRelease='SYNTHETIC_DATA_NOT_A_RELEASE', leaseIssued=False,
            DockerLabActions='SYNTHETIC_DATA_NONE', AndroidActions=0, uiControls='SYNTHETIC_DATA_NOT_EXECUTED')
        subject_pin = self.doc(root / 'SYNTHETIC_DATA_source-subject.json', subject)
        source_reviews = {}
        for reviewer_role in ('qa', 'security'):
            source_reviews[reviewer_role] = self.doc(root / ('SYNTHETIC_DATA_source_' + reviewer_role + '.json'),
                dict(reviewer='SYNTHETIC_DATA_SOURCE_' + reviewer_role, role=reviewer_role,
                     decision='ACCEPT_EXACT_FIRST_CELL_SOURCE_CONFIG_ONLY', subject=subject_pin,
                     configuration=config_pin, findings=[]))
        release = dict(schema='e02-first-cell-release-v1', executionAuthorized=True,
            rootSession='SYNTHETIC_DATA_OPERATOR', executionSession='SYNTHETIC_DATA_OPERATOR',
            runId=run_id, scope=scope, runConfig=config_pin, sourceSubject=subject_pin,
            notAfterUtcNs=1700001800000000000, qaReview=source_reviews['qa'],
            securityReview=source_reviews['security'], guardRegressionEvidence=opaque,
            limits='SYNTHETIC_DATA_NO_RELEASE_OR_REVIEW_OCCURRED')
        release_pin = self.doc(root / 'SYNTHETIC_DATA_release.json', release)
        lease = dict(schema='e02-single-cell-lease-v1', runId=run_id, bootId='SYNTHETIC_DATA_BOOT',
            issuedUtcNs=1700000000000000000, deadlineUtcNs=1700001800000000000,
            issuedMonoNs=1000000, deadlineMonoNs=1800001000000,
            issuedBootNs=3000000, deadlineBootNs=1800003000000)
        lease_pin = self.doc(root / 'session/lease.json', lease)
        expected_rows = []
        for target in sorted(A.MATRIX):
            d, r, l = target
            rumor = self.rumor(d)
            sender, recipient = rumor['pubkey'], rumor['tags'][0][1]
            account, peer = (recipient, sender) if r == 'incoming' else (sender, recipient)
            name = 'expected-rumor.json' if target == cell else 'plan-' + '-'.join(target) + '.json'
            rumor_pin = self.doc(root / 'session/fixtures' / name, rumor)
            expected_rows.append(dict(id='-'.join(target), direction=d, role=r, relay=l,
                account=account, peer=peer, rumor=rumor_pin,
                visibleToken='SYNTHETIC_DATA_faktúra_𐐀_NOT_RUNTIME', dispatch=r == 'incoming'))
        expected = next(row for row in expected_rows if tuple(row[k] for k in ('direction', 'role', 'relay')) == cell)
        rumor = self.get(expected['rumor'])
        sender, recipient = rumor['pubkey'], rumor['tags'][0][1]
        wire = dict(kind=1059, id='f' * 64, tags=[['p', expected['account']]], content='SYNTHETIC_DATA_NOT_ENCRYPTED')
        other = dict(wire, id='e' * 64, tags=[['p', sender if expected['account'] == recipient else recipient]])
        events = [wire, other] if role == 'incoming' else [other, wire]
        frozen = self.doc(root / 'session/fixtures/expected.json', dict(schema='e02-first-cell-expected-v1',
            caseId=expected['id'], direction=direction, role=role, relay=relay, senderPub=sender,
            recipientPub=recipient, envelope=json.loads(rumor['content']), rumor=rumor,
            createdUTC='SYNTHETIC_DATA_TIMESTAMP_ONLY'))
        prepared = self.doc(root / 'session/fixtures/prepared.json', dict(schema='e02-first-cell-prepared-v1',
            caseId=expected['id'], senderPub=sender, recipientPub=recipient, rumor=rumor, events=events,
            expected=self.guest(frozen)))
        content = self.put(root / 'session/fixtures/expected-content.txt', rumor['content'].encode())
        inboxes = self.doc(root / 'session/fixtures/inboxes.json', {'SYNTHETIC_DATA_NOT_INBOXES': True})
        prepare_reply = self.doc(root / 'evidence/fixture-prepare-reply.json', dict(schema='e02-fixture-command-v1',
            operation='prepare', caseId=expected['id'], ok=True,
            result={key: self.guest(pin) for key, pin in dict(expected=frozen,
                expectedRumor=expected['rumor'], expectedContent=content, prepared=prepared, inboxes=inboxes).items()}))
        wire_pin = self.doc(root / 'session/fixtures/wire.json', wire)
        wire_text = Path(wire_pin['path']).read_text()
        request = dict(op='validate', wire=wire_text, secret='0' * 63 + ('1' if expected['account'] == self.C.A else '2'),
                       role=role, expectedSender=sender)
        validation = dict(ok=True, decrypts=[1, 1], value=dict(rumor=rumor, role=role, dispatch=role == 'incoming'))
        proof = dict(schema='e02-ordinary-transport-v1',
            frame=self.doc(root / 'session/fixtures/frame.json', ['EVENT', 'SYNTHETIC_DATA_SUBSCRIPTION', wire]),
            wire=wire_pin, jsRequest=self.doc(root / 'session/fixtures/js-request.json', request),
            rustRequest=self.doc(root / 'session/fixtures/rust-request.json', request),
            jsResult=self.doc(root / 'session/fixtures/js-result.json', validation),
            rustResult=self.doc(root / 'session/fixtures/rust-result.json', validation))
        original_proof = self.doc(root / 'session/fixtures/consumer-transport.json',
            {'schema': proof['schema'], **{key: self.guest(pin) for key, pin in proof.items() if key != 'schema'}})
        proof_pin = self.doc(root / 'evidence/transport-host-paths.json', proof)
        raw_pin = self.put(root / 'evidence/client-raw-rumor.json',
                           json.dumps(dict(rumor, sig=''), ensure_ascii=False, indent=2).encode())
        clear_pin = self.doc(root / 'evidence/helper-clear.json', dict(schema='e02-clipboard-capture-v1',
            caseId=expected['id'], action='CLEAR', foregroundFocus=True, elapsedRealtimeNanos=100,
            wallClockMillis=1000, status='EMPTY_SENTINEL_SET'))
        helper_pin = self.doc(root / 'evidence/helper-capture.json', dict(schema='e02-clipboard-capture-v1',
            caseId=expected['id'], action='CAPTURE', foregroundFocus=True, elapsedRealtimeNanos=200,
            wallClockMillis=2000, status='CAPTURED', mime='text/plain', bytes=raw_pin['bytes'],
            sha256=raw_pin['sha256'], clipboardItemCount=1, clipboardTimestamp=1500))
        selection = self.doc(root / 'evidence/selection.json', dict(schema='e02-ordinary-selection-v1',
            observationId=expected['id'], account=expected['account'], peer=expected['peer'], rumorId=rumor['id'],
            action='COPY_RAW_JSON', method='ANDROID_LOCAL_FOREGROUND', helperPackage='org.nbdp.clipboard.capture',
            helperArtifact=config['helperApk'], helperReceipt=helper_pin, capturedMonotonicNs=2000000))
        png = self.put(root / 'ui/SYNTHETIC_DATA.png', b'\x89PNG\r\n\x1a\n' + b'SYNTHETIC_DATA_NOT_AN_IMAGE' * 2)
        xml = self.put(root / 'ui/SYNTHETIC_DATA.xml',
                       '<hierarchy><node text="SYNTHETIC_DATA_faktúra_𐐀_NOT_RUNTIME"/></hierarchy>'.encode())
        observation = dict(id=expected['id'], status='COMPLETE', transport=proof_pin,
            selection=selection, uiPng=png, uiXml=xml, rawClientRumor=raw_pin, error=None)
        driver = dict(schema='e02-first-slice-driver-result-v1', runId=run_id, runConfig=config_pin,
            runRelease=release_pin, executionState='PARTIAL',
            accountIdentityGUI=dict(preview=dict(png=png, xml=xml), observedPublicProfileText=['SYNTHETIC_DATA_NOT_PROFILE'],
                                    meaning='SYNTHETIC_DATA_NOT_RUNTIME'),
            torConfigurationGUI=opaque, environmentAnrEvidence=[], expectedRumor=expected['rumor'],
            originalTransport=original_proof, clipboardClear=clear_pin, allUICaptures=[dict(png=png, xml=xml)],
            observations=[observation], limits=['SYNTHETIC_DATA_NOT_RUNTIME'], canonicalE02Changed=False)
        driver_pin = self.doc(root / 'driver-result.json', driver)
        plan = dict(schema='e02-ordinary-plan-v1', runId=run_id, operator='SYNTHETIC_DATA_OPERATOR',
            authors=['SYNTHETIC_DATA_AUTHOR'], client=self.client, sources=all_sources,
            prerequisites=self.prerequisites, runConfig=config_pin, runRelease=release_pin, expected=expected_rows)
        plan_pin = self.doc(root / 'SYNTHETIC_DATA_plan.json', plan)
        capture_pin = self.doc(root / 'SYNTHETIC_DATA_capture.json', dict(schema='e02-ordinary-capture-v1',
            runId=run_id, operator=plan['operator'], plan=plan_pin, client=self.client,
            executionState='PARTIAL', runConfig=config_pin, runRelease=release_pin,
            driverReceipt=driver_pin, observations=[observation]))
        cleanup = dict(ok=True, rows=[dict(role=r, exactOwnedCleanupOnly=True, errors=[], identityVerified=True,
            absenceConfirmed=True, inspectExit=0, cid=('%064x' % (i + 1)), logsExit=0,
            removeExit=0, afterInspectExit=1) for i, r in enumerate(('android', 'fixture', 'anchor', relay))], errors=[])
        cleanup_pin = self.doc(root / 'cleanup/result.json', cleanup)
        supervisor_pin = self.doc(root / 'supervisor-result.json', dict(schema='e02-first-cell-supervisor-result-v1',
            runId=run_id, runConfig=config_pin, runRelease=release_pin, lease=lease_pin,
            canonicalE02Changed=False, limits=['SYNTHETIC_DATA_NOT_RUNTIME'], executionState='PARTIAL',
            error=None, secondaryErrors=[], cleanup=dict(cleanup, evidence=cleanup_pin)))
        command_streams = {name: self.put(root / ('commands/0001.' + name), b'SYNTHETIC_DATA_NOT_A_CHILD_STREAM')
                           for name in ('stdout', 'stderr')}
        command = self.doc(root / 'commands/0001.json', dict(argv=['SYNTHETIC_DATA_NO_CHILD_EXECUTED'],
            launchAttempt=True, pid=1, exit=0, reaped=True, forced=False, timedOut=False, error=None,
            **command_streams, observedBytes={k: v['bytes'] for k, v in command_streams.items()},
            stdoutEOF=True, stderrEOF=True))
        final = self.doc(root / 'SYNTHETIC_DATA_NOT_TOOL_RESULT.json', {'SYNTHETIC_DATA_NO_TOOL_EXECUTED': True})
        outer_pin = self.doc(root / 'SYNTHETIC_DATA_outer.json', dict(schema='e02-outer-tool-completion-v1',
            runId=run_id, runConfig=config_pin, runRelease=release_pin, launchTool='SYNTHETIC_DATA_LAUNCH',
            launchSession='SYNTHETIC_DATA_SESSION', finalTool='SYNTHETIC_DATA_FINAL', finalSession='SYNTHETIC_DATA_SESSION',
            argv=['python3', '-I', '-B', source_pins[0]['path'], '--config', config_pin['path'], '--config-sha', config_pin['sha256'],
                  '--release', release_pin['path'], '--release-sha', release_pin['sha256'], '--out', str(root)],
            finalToolResult=final, exit=0, sessionFinished=True, interruptionSent=False,
            terminateSent=False, timeoutSent=False, completionProof='ACTUAL_FINAL_TOOL_RESULT'))
        return dict(schema='e02-ordinary-run-member-v1', runId=run_id, runRoot=str(root),
            operator=plan['operator'], authors=plan['authors'], candidate=self.candidate_pin, client=self.client,
            cell=dict(direction=direction, role=role, relay=relay), sourceSubject=subject_pin,
            runConfig=config_pin, runRelease=release_pin, lease=lease_pin, supervisor=supervisor_pin,
            outer=outer_pin, driver=driver_pin, plan=plan_pin, capture=capture_pin,
            fixturePrepare=prepare_reply, commandReceipts=[command])

    def entry(self, member, classification='QUALIFIED'):
        root = Path(member['runRoot'])
        contribute = classification == 'QUALIFIED'
        member_pin = self.doc(root / 'SYNTHETIC_DATA_member.json', member)
        capture = self.get(member['capture']) if member['capture'] is not None else {'observations': []}
        whole, observations = {}, {}
        for role in ('qa', 'security'):
            value = dict(schema='e02-ordinary-whole-run-review-v1', role=role, session='SYNTHETIC_DATA_WHOLE_' + role,
                decision='ACCEPT_QUALIFIED_RUN_FOR_SUPPLEMENT_ONLY' if contribute else 'ACCEPT_EXCLUSION_RECORD_ONLY',
                member=member_pin, **{k: member[k] for k in ('outer', 'supervisor', 'driver', 'capture', 'candidate', 'sourceSubject')},
                acceptedObservationIds=[r['id'] for r in capture['observations']] if contribute else [],
                classification=classification, findings=[], rawReviewEvidence=self.raw_review)
            whole[role] = self.doc(root / ('SYNTHETIC_DATA_whole_' + role + '.json'), value)
            if contribute:
                observations[role] = self.doc(root / ('SYNTHETIC_DATA_observation_' + role + '.json'),
                    dict(schema='e02-ordinary-observation-review-v1', role=role, session='SYNTHETIC_DATA_OBSERVATION_' + role,
                         decision='ACCEPT_ORDINARY_CLIENT_OBSERVATIONS_ONLY', plan=member['plan'], subject=member['capture'],
                         acceptedObservationIds=[r['id'] for r in capture['observations']], findings=[]))
        return dict(member=member_pin, disposition='CONTRIBUTE' if contribute else 'EXCLUDE', classification=classification,
                    reason=None if contribute else 'SYNTHETIC_DATA_EXCLUSION_NOT_RUNTIME', reviews=whole,
                    observationReviews=observations if contribute else None)

    def evaluate(self, entries, inventory_sessions=None):
        self.evaluation_sequence += 1
        prefix = 'SYNTHETIC_DATA_inventory_%d' % self.evaluation_sequence
        inventory = dict(schema='e02-ordinary-aggregate-inventory-v1', evidenceType='SYNTHETIC_DATA_CONTROLS_ONLY',
            operator='SYNTHETIC_DATA_OPERATOR', authors=['SYNTHETIC_DATA_AUTHOR'], candidate=self.candidate_pin,
            consumer=self.consumer_pin, runs=entries)
        inventory_pin = self.doc(self.root / (prefix + '.json'), inventory)
        reviews = {}
        for role in ('qa', 'security'):
            session = (inventory_sessions or {}).get(role, 'SYNTHETIC_DATA_INVENTORY_' + role)
            reviews[role] = self.doc(self.root / (prefix + '_' + role + '.json'),
                dict(schema='e02-ordinary-aggregate-inventory-review-v1', role=role,
                     session=session,
                     decision='ACCEPT_COMPLETE_CANDIDATE_ATTEMPT_INVENTORY_ONLY', inventory=inventory_pin,
                     candidate=self.candidate_pin, completeAttemptInventory=True, findings=[], rawReviewEvidence=self.raw_review))
        budget = A.Budget()
        with patch.object(self.C, 'client') as client_gate, patch.object(self.C, 'prerequisites') as prerequisites_gate:
            result = A.evaluate(inventory, inventory_pin, reviews, A.file_reader(self.C, budget), self.C, budget)
        self.assertTrue(client_gate.called)
        self.assertTrue(prerequisites_gate.called)
        self.assertEqual(result['evidenceType'], 'SYNTHETIC_DATA_CONTROLS_ONLY')
        return result

    def inspect(self, member):
        budget = A.Budget()
        with patch.object(self.C, 'client'), patch.object(self.C, 'prerequisites'):
            return A.inspect_member(member, self.candidate, A.file_reader(self.C, budget), self.C)

    def test_synthetic_complete_matrix_is_only_data_consistency_and_headers_stay_partial(self):
        value = self.evaluate([self.entry(self.member(cell)) for cell in sorted(A.MATRIX)])
        self.assertEqual(value['status'], 'DATA_CONSISTENCY_ONLY')
        self.assertEqual(value['matrixState'], 'MATRIX_MATCHED_SUPPLEMENT_ONLY')
        self.assertEqual(value['missingCells'], [])
        self.assertTrue(all(row['captureHeader'] == row['originalConsumerStatus'] == 'PARTIAL' for row in value['runs']))
        self.assertFalse(value['canonicalE02Changed'])
        self.assertEqual(value['canonicalStatus'], 'PARTIAL22_UNCHANGED')

    def test_single_synthetic_member_leaves_seven_missing_cells(self):
        value = self.evaluate([self.entry(self.member())])
        self.assertEqual(value['status'], 'PARTIAL')
        self.assertEqual(len(value['missingCells']), 7)

    def test_failed_whole_run_cannot_donate_its_earlier_complete_row(self):
        member = self.member()
        supervisor = self.get(member['supervisor'])
        supervisor.update(executionState='FAILED_UNQUALIFIED', error='SYNTHETIC_DATA_LATER_FAILURE')
        member['supervisor'] = self.rewrite(member['supervisor'], supervisor)
        with self.assertRaisesRegex(A.Refusal, 'NO_FAILED_DONATION'):
            self.inspect(member)
        value = self.evaluate([self.entry(member)])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')
        self.assertEqual(len(value['missingCells']), 8)

    def test_swapped_release_run_join_refuses(self):
        member = self.member()
        release = self.get(member['runRelease']); release['runId'] = 'f' * 32
        member['runRelease'] = self.rewrite(member['runRelease'], release)
        with self.assertRaises(A.Refusal):
            self.inspect(member)

    def test_missing_release_refuses(self):
        member = self.member(); member['runRelease'] = None
        with self.assertRaises((A.Refusal, self.C.Refusal, TypeError)):
            self.inspect(member)

    def test_missing_or_unqualified_cleanup_refuses(self):
        member = self.member()
        supervisor = self.get(member['supervisor']); supervisor['cleanup']['rows'].pop()
        member['supervisor'] = self.rewrite(member['supervisor'], supervisor)
        with self.assertRaisesRegex(A.Refusal, 'WHOLE_RUN_CLEANUP'):
            self.inspect(member)

    def test_outer_interruption_timeout_or_unknown_completion_refuses(self):
        member = self.member()
        original = self.get(member['outer'])
        for key, value in [('exit', 2), ('sessionFinished', False), ('interruptionSent', True),
                           ('terminateSent', True), ('timeoutSent', True), ('completionProof', 'UNKNOWN')]:
            with self.subTest(field=key):
                changed = dict(original, **{key: value})
                pin = self.doc(Path(member['runRoot']) / ('SYNTHETIC_DATA_outer_' + key + '.json'), changed)
                with self.assertRaisesRegex(A.Refusal, 'NATURAL_TOOL_COMPLETION'):
                    A.inspect_outer(changed, member, A.file_reader(self.C, A.Budget()),
                                    self.get(member['runConfig'])['sourceAndDependencyPins'][0])

    def test_outer_argv_or_session_swap_refuses(self):
        member = self.member(); value = self.get(member['outer'])
        value['argv'][7] = '0' * 64
        with self.assertRaisesRegex(A.Refusal, 'EXACT_OUTER_ARGV'):
            A.inspect_outer(value, member, A.file_reader(self.C, A.Budget()),
                            self.get(member['runConfig'])['sourceAndDependencyPins'][0])
        value = self.get(member['outer']); value['finalSession'] = 'SYNTHETIC_DATA_OTHER_SESSION'
        with self.assertRaisesRegex(A.Refusal, 'SAME_OUTER_SESSION'):
            A.inspect_outer(value, member, A.file_reader(self.C, A.Budget()),
                            self.get(member['runConfig'])['sourceAndDependencyPins'][0])

    def test_exact_reviewed_isolated_argv_accepts_only_two_named_interpreters(self):
        member = self.member(); value = self.get(member['outer'])
        source = self.get(member['runConfig'])['sourceAndDependencyPins'][0]
        self.assertEqual(value['argv'][:3], ['python3', '-I', '-B'])
        self.assertEqual(len(value['argv']), 14)
        for interpreter in ('python3', '/usr/bin/python3'):
            with self.subTest(interpreter=interpreter):
                changed = copy.deepcopy(value); changed['argv'][0] = interpreter
                A.inspect_outer(changed, member, A.file_reader(self.C, A.Budget()), source)

    def test_missing_reordered_changed_or_extra_flags_and_interpreters_refuse(self):
        member = self.member(); value = self.get(member['outer']); argv = value['argv']
        source = self.get(member['runConfig'])['sourceAndDependencyPins'][0]
        variants = {
            'old13token-B-only': [argv[0], *argv[2:]],
            'missing-B': [*argv[:2], *argv[3:]],
            'reordered-flags': [argv[0], '-B', '-I', *argv[3:]],
            'changed-isolation-flag': [argv[0], '-E', *argv[2:]],
            'extra-flag': [*argv[:3], '-P', *argv[3:]],
            'other-bare-interpreter': ['python3.11', *argv[1:]],
            'other-absolute-interpreter': ['/bin/python3', *argv[1:]],
            'changed-authority-sha': [*argv[:7], '0' * 64, *argv[8:]],
            'changed-supervisor': [*argv[:3], '/tmp/SYNTHETIC_DATA_other_supervisor.py', *argv[4:]],
        }
        for name, changed_argv in variants.items():
            with self.subTest(variant=name), self.assertRaisesRegex(A.Refusal, 'EXACT_OUTER_ARGV'):
                A.inspect_outer(dict(value, argv=changed_argv), member,
                                A.file_reader(self.C, A.Budget()), source)

    def test_duplicate_or_conflicting_contributing_cells_refuse_without_selection(self):
        value = self.evaluate([self.entry(self.member()), self.entry(self.member())])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')
        self.assertEqual(len(value['conflictingCells']), 1)
        self.assertEqual(len(value['runs']), 2)

    def test_conflicting_whole_contents_for_same_cell_are_not_resolved_by_selection(self):
        first = self.entry(self.member())
        self.rumor_suffix = '_SYNTHETIC_DATA_DIFFERENT_VALID_CONTENT'
        second = self.entry(self.member())
        value = self.evaluate([first, second])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')
        self.assertEqual(len(value['conflictingCells']), 1)

    def test_missing_whole_run_review_refuses_and_donates_nothing(self):
        entry = self.entry(self.member()); entry['reviews']['security'] = None
        value = self.evaluate([entry])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')
        self.assertEqual(len(value['missingCells']), 8)

    def test_inventory_review_excludes_undisclosed_member_authors_and_operators(self):
        # Each identity is deliberately omitted from the inventory's own authors
        # and operator, reproducing the source finding without claiming a review.
        for classification in ('QUALIFIED', 'ENVIRONMENT_FAILURE'):
            for identity_kind in ('author', 'operator'):
                with self.subTest(disposition=classification, identity=identity_kind):
                    member = self.member()
                    omitted = 'SYNTHETIC_DATA_OMITTED_MEMBER_' + identity_kind
                    if identity_kind == 'author':
                        member['authors'] = [omitted]
                    else:
                        member['operator'] = omitted
                    entry = self.entry(member, classification)
                    with self.assertRaisesRegex(A.Refusal, 'INDEPENDENT_INVENTORY_REVIEWERS'):
                        self.evaluate([entry], inventory_sessions={'qa': omitted})

    def test_inventory_review_requires_member_disclosure_even_for_exclusions(self):
        for variant in ('empty-authors', 'missing-authors', 'empty-operator', 'missing-operator'):
            with self.subTest(variant=variant):
                member = self.member()
                entry = self.entry(member, 'ENVIRONMENT_FAILURE')
                disclosed = self.get(entry['member'])
                if variant == 'empty-authors':
                    disclosed['authors'] = []
                elif variant == 'missing-authors':
                    disclosed.pop('authors')
                elif variant == 'empty-operator':
                    disclosed['operator'] = ''
                else:
                    disclosed.pop('operator')
                entry['member'] = self.rewrite(entry['member'], disclosed)
                with self.assertRaises(A.Refusal):
                    self.evaluate([entry])

    def test_independent_inventory_review_accepts_disclosed_excluded_member_identities(self):
        member = self.member()
        member['authors'] = ['SYNTHETIC_DATA_SEPARATE_MEMBER_AUTHOR']
        member['operator'] = 'SYNTHETIC_DATA_SEPARATE_MEMBER_OPERATOR'
        value = self.evaluate([self.entry(member, 'ENVIRONMENT_FAILURE')], inventory_sessions={
            'qa': 'SYNTHETIC_DATA_INDEPENDENT_INVENTORY_QA',
            'security': 'SYNTHETIC_DATA_INDEPENDENT_INVENTORY_SECURITY'})
        self.assertEqual(value['status'], 'PARTIAL')
        self.assertEqual(value['runs'][0]['status'], 'EXCLUDED_VISIBLE')
        self.assertEqual(value['evidenceType'], 'SYNTHETIC_DATA_CONTROLS_ONLY')

    def test_missing_existing_v1_observation_review_refuses(self):
        entry = self.entry(self.member()); entry['observationReviews']['qa'] = None
        value = self.evaluate([entry])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')
        self.assertEqual(len(value['missingCells']), 8)

    def test_actual_review_cannot_be_self(self):
        member = self.member(); entry = self.entry(member)
        review = self.get(entry['reviews']['qa']); review['session'] = member['operator']
        entry['reviews']['qa'] = self.rewrite(entry['reviews']['qa'], review)
        value = self.evaluate([entry])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')

    def test_whole_review_swapped_subject_refuses(self):
        member = self.member(); entry = self.entry(member)
        review = self.get(entry['reviews']['qa']); review['outer'] = member['supervisor']
        entry['reviews']['qa'] = self.rewrite(entry['reviews']['qa'], review)
        value = self.evaluate([entry])
        self.assertEqual(value['status'], 'QUALIFICATION_REFUSED')
        self.assertEqual(len(value['missingCells']), 8)

    def test_excluded_environment_failure_stays_visible_and_cannot_donate(self):
        member = self.member(); member['driver'] = member['capture'] = None
        value = self.evaluate([self.entry(member, 'ENVIRONMENT_FAILURE')])
        self.assertEqual(value['status'], 'PARTIAL')
        self.assertEqual(value['runs'][0]['status'], 'EXCLUDED_VISIBLE')
        self.assertEqual(len(value['missingCells']), 8)

    def test_excluded_reproducible_compatibility_failure_is_never_selection_hidden(self):
        failed = self.entry(self.member(), 'COMPATIBILITY_FAILURE')
        matched = self.entry(self.member())
        value = self.evaluate([failed, matched])
        self.assertEqual(value['status'], 'FAIL')
        self.assertEqual(value['failedRunIds'], [self.get(failed['member'])['runId']])
        self.assertEqual(len(value['runs']), 2)

    def test_altered_whole_raw_inner_is_failure_even_with_valid_new_id(self):
        member = self.member()
        driver = self.get(member['driver']); capture = self.get(member['capture'])
        row = copy.deepcopy(driver['observations'][0]); raw = self.get(row['rawClientRumor'])
        raw.pop('sig', None); raw['content'] += 'SYNTHETIC_DATA_ALTERED'
        serialization = [0, raw['pubkey'], raw['created_at'], raw['kind'], raw['tags'], raw['content']]
        raw['id'] = hashlib.sha256(json.dumps(serialization, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        row['rawClientRumor'] = self.rewrite(row['rawClientRumor'], raw)
        driver['observations'] = [row]
        member['driver'] = self.rewrite(member['driver'], driver)
        capture.update(driverReceipt=member['driver'], observations=[row])
        member['capture'] = self.rewrite(member['capture'], capture)
        with self.assertRaisesRegex(self.C.Mismatch, 'RETAINED_RUMOR'):
            self.inspect(member)
        value = self.evaluate([self.entry(member)])
        self.assertEqual(value['status'], 'FAIL')
        self.assertEqual(len(value['missingCells']), 8)

    def test_omitted_child_receipt_or_child_forced_exit_refuses(self):
        member = self.member()
        receipt = self.get(member['commandReceipts'][0]); receipt['forced'] = True
        member['commandReceipts'][0] = self.rewrite(member['commandReceipts'][0], receipt)
        with self.assertRaisesRegex(A.Refusal, 'EVERY_SUPERVISOR_CHILD_NATURAL_ZERO'):
            self.inspect(member)
        member['commandReceipts'] = []
        with self.assertRaises((A.Refusal, self.C.Refusal)):
            self.inspect(member)

    def test_extended_lease_refuses(self):
        member = self.member(); lease = self.get(member['lease'])
        lease['deadlineUtcNs'] += 1
        member['lease'] = self.rewrite(member['lease'], lease)
        with self.assertRaisesRegex(A.Refusal, 'NONRENEWED_ORIGINAL_LEASE'):
            self.inspect(member)

    def test_revoked_lease_never_donates(self):
        member = self.member()
        marker = Path(member['runRoot']) / 'session/control/REVOKED'
        marker.parent.mkdir()
        marker.write_bytes(b'SYNTHETIC_DATA_REVOKED')
        with self.assertRaisesRegex(A.Refusal, 'REVOKED_RUN_CANNOT_CONTRIBUTE'):
            self.inspect(member)

    def test_old_partial_header_cannot_be_rewritten_complete(self):
        member = self.member(); driver = self.get(member['driver']); driver['executionState'] = 'COMPLETE'
        member['driver'] = self.rewrite(member['driver'], driver)
        with self.assertRaisesRegex(A.Refusal, 'ORIGINAL_LIMITED_DRIVER_HEADER'):
            self.inspect(member)

    def test_metadata_ns_allowance_is_named_only_and_never_relaxes_v1(self):
        ns = 1700000000000000000
        self.assertEqual(A.loads_metadata(('{"deadlineUtcNs":%d}' % ns).encode())['deadlineUtcNs'], ns)
        for raw in (('{"created_at":%d}' % ns).encode(), ('{"capturedMonotonicNs":%d}' % ns).encode(),
                    b'{"n":1.0}', b'{"n":-0}', b'{"n":1,"n":2}', b'{"s":"\\ud800"}', b'NaN'):
            with self.subTest(raw=raw), self.assertRaises((A.Refusal, UnicodeError)):
                A.loads_metadata(raw)
        with self.assertRaises(self.C.Refusal):
            self.C.loads(('{"deadlineUtcNs":%d}' % ns).encode())

    def test_unknown_member_key_and_swapped_source_copy_refuse(self):
        member = self.member()
        with self.assertRaisesRegex(A.Refusal, 'CLOSED_KEYS'):
            A.member_shape(dict(member, unknown=True))
        copied = Path(member['runRoot']) / 'input/android_driver.py'
        copied.write_bytes(b'SYNTHETIC_DATA_SWAPPED_SOURCE')
        with self.assertRaises(self.C.Refusal):
            self.inspect(member)


if __name__ == '__main__':
    unittest.main()
