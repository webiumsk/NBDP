"""Synthetic pure helper controls. Definitions only at SOURCE preparation.

Every Root-looking receipt/run in fixtures below is synthetic, never genuine
Root authority or an actual account/lease. Controller/helper/Docker execution0.
"""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import native_metadata as n
    import render_metadata as r
    import custody_bridge as c
    import generic_inputs as gi
    from current_bindings import CURRENT, HOST_POLICY, CAPTURE_POLICY
finally:
    sys.path.pop(0)

RUN = 'a' * 32
NONCE = 'b' * 32
FIXTURE_ONLY = True


def original(path, value):
    raw = n.encoded(value)
    return dict(pin=n.pin_bytes(path, raw), raw=raw)


def templates():
    return json.loads((HERE / 'templates.json').read_bytes())


def context(fixed):
    source = dict(schema='e02-helper-current178-source-subject-v1',
                  templates=n.pin_bytes(r.TEMPLATES_PATH, n.encoded(fixed)),
                  currentTuple=CURRENT, sourceContributors=fixed['trueAuthors'],
                  operators=[], modelsDefined=3, modelsExecuted=0,
                  selfApproval=False, executionAuthorized=False)
    s = original('/synthetic-fixtures/helper-source.json', source)
    reviews = [original('/synthetic-fixtures/source-' + role + '.json',
                        dict(role=role, session='/root/fixture-source-' + role,
                             decision=r.SOURCE_DECISION, subject=s['pin']))
               for role in ('qa', 'security')]
    acceptance = original('/synthetic-fixtures/source-acceptance.json', dict(
        schema='e02-root-helper-current178-source-acceptance-v1', actor='/root',
        decision=r.SOURCE_DECISION, subject=s['pin'], reviews=[x['pin'] for x in reviews],
        modelsDefined=3, modelsExecuted=0,
        scope='CURRENT_HELPER_METHOD_RENDER_SOURCE_AND_CONTROL_DEFINITIONS_ONLY', executionAuthorized=False))
    data = original('/synthetic-fixtures/control-data.json', dict(
        schema='e02-helper-current178-control-data-subject-v1', helperSource=s['pin'],
        modelsDefined=3, modelsExecuted=3, modelsPassed=3, modelsFailed=0, skipped=0,
        inputsUnchanged=True, authors=['/root'], operators=['/root'], executionAuthorized=False))
    control_reviews = [original('/synthetic-fixtures/control-' + role + '.json',
                                dict(role=role, session='/root/fixture-control-' + role,
                                     decision=r.CONTROL_DECISION, subject=data['pin']))
                       for role in ('qa', 'security')]
    control_acceptance = original('/synthetic-fixtures/control-acceptance.json', dict(
        schema='e02-root-helper-current178-control-data-acceptance-v1', actor='/root',
        decision=r.CONTROL_DECISION, subject=data['pin'], helperSource=s['pin'],
        reviews=[x['pin'] for x in control_reviews], modelsDefined=3, modelsExecuted=3,
        modelsPassed=3, modelsFailed=0, skipped=0, inputsUnchanged=True,
        scope='CURRENT_HELPER_METHOD_RENDER_PURE_CONTROL_DATA_ONLY', executionAuthorized=False))
    return dict(schema='e02-current-helper-render-context-v1', source=s, sourceAcceptance=acceptance,
                sourceReviews=reviews, controlData=data, controlAcceptance=control_acceptance,
                controlReviews=control_reviews)


def plan_fixture(fixed, ctx):
    lease = dict(schema='e02-single-cell-lease-v1', runId=RUN,
                 bootId='11111111-2222-3333-4444-555555555555')
    for clock in ('Utc', 'Mono', 'Boot'):
        lease['issued' + clock + 'Ns'] = 1000000000000000000
        lease['deadline' + clock + 'Ns'] = 1000001800000000000
    raw = (json.dumps(lease, sort_keys=True, separators=(',', ':')) + '\n').encode()
    lease_pin = n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/lease--original.json', raw)
    ack = dict(reservation=n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/reservation.json', b'FIXTURE'),
               reservedInsideMetadataBytes=65536, metadataOwnerBytes=8388608,
               payloadAvailableBytes=49152, grantIssued=False)
    plan = r.plan_without_gates(fixed, ctx, RUN, NONCE, lease_pin, raw, ack)
    roster = r.roster(fixed, ['/root'])
    subject = r.concrete_subject(plan)
    compact = dict(schema='e02-root-helper-probe-concrete-inputs-v1', actor='/root',
                   decision=r.VERDICT_DECISION, subject=subject,
                   reviews=[dict(role=role, session='/root/fixture-concrete-' + role,
                                 decision=r.VERDICT_DECISION, subject=subject)
                            for role in ('qa', 'security')])
    compact_pin = n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/gate--concrete-review.json', n.encoded(compact))
    return plan, roster, compact, compact_pin


def direct(request, output='OK\n', count=1, session=None):
    response = dict(exit_code=0, output=output, wall_time_seconds=0.01)
    if count is not None:
        response['original_token_count'] = count
    if session is not None:
        response['session_id'] = session
    return dict(schema='e02-actual-tool-custody-v1', operator='/root',
                launch=dict(toolName='tools.exec_command', actualArguments=request,
                            unmodifiedResponse=response), polls=[])


def model_request():
    return dict(cmd='synthetic-model', workdir='/synthetic-fixtures', login=False,
                yield_time_ms=1000, max_output_tokens=20000)


class NativeFamilies(unittest.TestCase):
    def test_model5_direct_and_optional_counter_preserve_absence(self):
        request = model_request()
        origin = direct(request, count=None)
        before = copy.deepcopy(origin)
        self.assertEqual(n.complete_origin('MODEL5', origin, request, ['/root']), b'OK\n')
        self.assertEqual(origin, before)
        self.assertNotIn('original_token_count', origin['launch']['unmodifiedResponse'])

    def test_same_session_yielded_origin_requires_every_frame(self):
        request = model_request()
        origin = direct(request)
        origin['launch']['unmodifiedResponse'] = dict(session_id=44, output='O', wall_time_seconds=1, original_token_count=1)
        origin['polls'] = [dict(toolName='tools.write_stdin', actualArguments=dict(session_id=44, chars='', max_output_tokens=20),
                                unmodifiedResponse=dict(exit_code=0, output='K\n', wall_time_seconds=0.1, original_token_count=1))]
        self.assertEqual(n.complete_origin('MODEL5', origin, request, ['/root']), b'OK\n')
        origin['polls'][0]['actualArguments']['session_id'] = 45
        with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])

    def test_no_frames_after_terminal(self):
        request = model_request(); origin = direct(request)
        origin['polls'] = [copy.deepcopy(origin['launch'])]
        with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])

    def test_all_explicit_negative_flags_refused(self):
        for flag in n.FLAGS:
            for bad in (True, 0, None, 'false'):
                request = model_request(); origin = direct(request)
                origin['launch']['unmodifiedResponse'][flag] = bad
                with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])

    def test_plain_integer_request_and_terminal_domains(self):
        for field, bad in (('login', 0), ('yield_time_ms', True), ('max_output_tokens', 20000.0)):
            request = model_request(); changed = dict(request); changed[field] = bad
            with self.assertRaises(ValueError): n.complete_origin('MODEL5', direct(changed), request, ['/root'])
        request = model_request(); origin = direct(request); origin['launch']['unmodifiedResponse']['exit_code'] = False
        with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])

    def test_counter_caps_bind_actual_poll_not_launch(self):
        request = model_request(); origin = direct(request, count=20001)
        with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])
        origin = direct(request); origin['launch']['unmodifiedResponse'] = dict(session_id=44, output='', wall_time_seconds=1)
        origin['polls'] = [dict(toolName='tools.write_stdin', actualArguments=dict(session_id=44, max_output_tokens=1),
                               unmodifiedResponse=dict(exit_code=0, output='OK\n', wall_time_seconds=1, original_token_count=2))]
        with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])

    def test_collector7_missing_counter_is_operational_refusal(self):
        request = c.collector_request(RUN, 'reserve', [])
        with self.assertRaises(ValueError): n.complete_origin('COLLECTOR7', direct(request, count=None), request, ['/root'])
        self.assertEqual(n.complete_origin('COLLECTOR7', direct(request), request, ['/root']), b'OK\n')

    def test_host7_exact_current_policy_and_no_model_projection(self):
        request = dict(HOST_POLICY, cmd='synthetic-host')
        self.assertEqual(n.complete_origin('HOST7', direct(request), request, ['/root'], HOST_POLICY), b'OK\n')
        with self.assertRaises(ValueError): n.complete_origin('MODEL5', direct(request), request, ['/root'])
        changed = dict(request); changed['justification'] += ' changed'
        with self.assertRaises(ValueError): n.complete_origin('HOST7', direct(changed), request, ['/root'], HOST_POLICY)

    def test_capture7_is_distinct_from_host7(self):
        request = dict(CAPTURE_POLICY, cmd='synthetic-capture')
        self.assertEqual(n.complete_origin('PRODUCER_CAPTURE7', direct(request), request, ['/root'], CAPTURE_POLICY), b'OK\n')
        with self.assertRaises(ValueError): n.complete_origin('HOST7', direct(request), request, ['/root'], HOST_POLICY)

    def test_duplicate_nonfinite_nonwall_float_and_negativezero_refused(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1.0}', b'{"x":-0}'):
            with self.assertRaises(ValueError): n.decode_json(raw)

    def test_only_finite_api_wall_fraction_is_permitted(self):
        raw = b'{"launch":{"unmodifiedResponse":{"wall_time_seconds":0.125}}}'
        self.assertIn('launch', n.decode_json(raw, api=True))
        for value in (-1, True, '0.1'):
            request = model_request(); origin = direct(request)
            origin['launch']['unmodifiedResponse']['wall_time_seconds'] = value
            with self.assertRaises(ValueError): n.complete_origin('MODEL5', origin, request, ['/root'])

    def test_byte_and_depth_bounds_precede_positive_decode(self):
        with self.assertRaises(ValueError): n.decode_json(b' ' * (n.DATA + 1))
        with self.assertRaises(ValueError): n.decode_json(b'[' * 65 + b'0' + b']' * 65)


class CurrentRenderer(unittest.TestCase):
    def setUp(self):
        self.fixed = templates(); self.ctx = context(self.fixed)

    def test_exact_current_tuple_and_plain_source_modes(self):
        self.assertIs(r.fixed_contract(self.fixed), self.fixed)
        self.assertTrue(all(type(x) is int and x == 0o664 for x in self.fixed['compiledControllerBindings']['sourceModes'].values()))

    def test_bare_readiness_flag_never_replaces_source_control_context(self):
        self.fixed['executionReadiness'] = 'FINAL_AUTHORITY_BUNDLE_ACCEPTED_FOR_ROOT_SEQUENCING'
        with self.assertRaises(ValueError): r.source_context(self.fixed, {})

    def test_original_raw_pin_context_and_independent_pairs(self):
        self.assertEqual(r.source_context(self.fixed, self.ctx)['modelsDefined'], 3)
        changed = copy.deepcopy(self.ctx); changed['source']['raw'] += b' '
        with self.assertRaises(ValueError): r.source_context(self.fixed, changed)

    def test_source_and_control_decision_alias_or_model_donation_refused(self):
        for key, field, value in (('sourceAcceptance', 'modelsExecuted', False),
                                  ('controlData', 'modelsPassed', 2),
                                  ('controlAcceptance', 'inputsUnchanged', 1)):
            changed = copy.deepcopy(self.ctx); document = n.decode_json(changed[key]['raw']); document[field] = value
            changed[key] = original(changed[key]['pin']['path'], document)
            with self.assertRaises(ValueError): r.source_context(self.fixed, changed)

    def test_source_review_creator_and_duplicate_session_refused(self):
        changed = copy.deepcopy(self.ctx)
        value = n.decode_json(changed['sourceReviews'][0]['raw']); value['session'] = '/root'
        changed['sourceReviews'][0] = original(changed['sourceReviews'][0]['pin']['path'], value)
        with self.assertRaises(ValueError): r.source_context(self.fixed, changed)

    def test_registered_original_lease_and_root_reservation_only(self):
        plan, _, _, _ = plan_fixture(self.fixed, self.ctx)
        self.assertEqual(set(plan), r.PLAN_KEYS)
        self.assertNotIn('gates', plan)
        self.assertEqual(plan['lease']['path'], r.DATA_PARENT + '/' + RUN + '/lease--original.json')

    def test_lease_renewal_fraction_bool_and_wrong_run_refused(self):
        lease = dict(schema='e02-single-cell-lease-v1', runId=RUN,
                     bootId='11111111-2222-3333-4444-555555555555')
        for clock in ('Utc', 'Mono', 'Boot'):
            lease['issued' + clock + 'Ns'] = 1; lease['deadline' + clock + 'Ns'] = 1800000000001
        self.assertEqual(n.decode_original_lease(json.dumps(lease).encode(), RUN)['runId'], RUN)
        for field, bad in (('deadlineUtcNs', 1800000000002), ('issuedMonoNs', True), ('issuedBootNs', 1.0), ('runId', 'c' * 32)):
            changed = dict(lease); changed[field] = bad
            with self.assertRaises(ValueError): n.decode_original_lease(json.dumps(changed).encode(), RUN)

    def test_actor_union_includes_additional_true_authors_and_operators(self):
        actors = r.roster(self.fixed, ['/root', '/root/fixture-operator'], ['/root/fixture-author'])
        self.assertIn('/root/fixture-author', actors['concreteReviewerExclusions'])
        self.assertIn('/root/fixture-operator', actors['concreteReviewerExclusions'])

    def test_concrete_subject_is_before_final_gate_hashes(self):
        plan, _, _, _ = plan_fixture(self.fixed, self.ctx)
        subject = r.concrete_subject(plan)
        self.assertEqual(subject['sha256'], hashlib.sha256(n.encoded(plan)).hexdigest())
        plan['gates'] = {}
        with self.assertRaises(ValueError): r.concrete_subject(plan)

    def test_actual_compact5_fourkey_verdict_order_and_independence(self):
        plan, actors, compact, _ = plan_fixture(self.fixed, self.ctx)
        r.validate_concrete_receipt(compact, r.concrete_subject(plan), actors)
        changed = copy.deepcopy(compact); changed['reviews'][1]['session'] = changed['reviews'][0]['session']
        with self.assertRaises(ValueError): r.validate_concrete_receipt(changed, r.concrete_subject(plan), actors)
        changed = copy.deepcopy(compact); changed['reviews'][0]['approval'] = True
        with self.assertRaises(ValueError): r.validate_concrete_receipt(changed, r.concrete_subject(plan), actors)

    def test_generic_receipts_bind_actual_registered_bytes(self):
        plan, actors, compact, compact_pin = plan_fixture(self.fixed, self.ctx)
        values = r.generic_gate_values(self.fixed, self.ctx, plan, actors, compact, compact_pin)
        pins = {kind: n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/gate--' + kind + '.json', n.encoded(value))
                for kind, value in values.items()}
        bound = r.bind_registered_gates(self.fixed, self.ctx, plan, values, pins, actors, compact, compact_pin)
        self.assertEqual(set(bound['gates']), set(r.GENERIC_KINDS) | {'producerSource', 'controllerSource'})
        changed = copy.deepcopy(pins); changed['controlData']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): r.bind_registered_gates(self.fixed, self.ctx, plan, values, changed, actors, compact, compact_pin)

    def test_release_template_cannot_authorize_runtime(self):
        plan, actors, compact, compact_pin = plan_fixture(self.fixed, self.ctx)
        values = r.generic_gate_values(self.fixed, self.ctx, plan, actors, compact, compact_pin)
        pins = {kind: n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/gate--' + kind + '.json', n.encoded(value)) for kind, value in values.items()}
        bound = r.bind_registered_gates(self.fixed, self.ctx, plan, values, pins, actors, compact, compact_pin)
        plan_pin = n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/plan--concrete.json', n.encoded(bound))
        release = r.root_release_template(self.fixed, self.ctx, bound, plan_pin, actors)
        self.assertIsNone(release['executionAuthorized'])
        release_pin = n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/grant--release.json', n.encoded(release))
        with self.assertRaises(ValueError): r.host_seven_key_request(self.fixed, self.ctx, plan_pin, release, release_pin)

    def test_host7_exact183_cli_and_root_registered_grant(self):
        plan, actors, compact, compact_pin = plan_fixture(self.fixed, self.ctx)
        values = r.generic_gate_values(self.fixed, self.ctx, plan, actors, compact, compact_pin)
        pins = {kind: n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/gate--' + kind + '.json', n.encoded(value)) for kind, value in values.items()}
        bound = r.bind_registered_gates(self.fixed, self.ctx, plan, values, pins, actors, compact, compact_pin)
        plan_pin = n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/plan--concrete.json', n.encoded(bound))
        release = r.root_release_template(self.fixed, self.ctx, bound, plan_pin, actors)
        # Synthetic metadata fixture only. No grant is issued or submitted.
        release['executionAuthorized'] = True
        release_pin = n.pin_bytes(r.DATA_PARENT + '/' + RUN + '/grant--release.json', n.encoded(release))
        request = r.host_seven_key_request(self.fixed, self.ctx, plan_pin, release, release_pin)
        self.assertEqual(set(request), n.SEVEN_KEYS)
        self.assertIn('183s', request['cmd'])
        self.assertEqual(request['sandbox_permissions'], 'require_escalated')


class FitAndGeneric(unittest.TestCase):
    def test_exact_fit_counts_duplicates_and_all_future_bounds(self):
        row = dict(i=1, n=10, t='data', p='gate--fixture.json', h='1' * 64, s=None)
        result = c.full_chain_fit([row], 512, [20, 20], 100, 2)
        self.assertEqual(result['payloadBoundBytes'], 150)
        self.assertEqual(result['writesBound'], 5)

    def test_fit_no_payload_ledger_borrowing_or_second_slot(self):
        with self.assertRaises(ValueError): c.full_chain_fit([], 512, [49152], 1, 1)
        with self.assertRaises(ValueError): c.full_chain_fit([], 512, [0] * 64, 0, 1)

    def test_fit_bool_float_and_copy_index_alias_refused(self):
        for value in (True, 1.0):
            with self.assertRaises(ValueError): c.full_chain_fit([], 512, [value], 0, 0)
        row = dict(i=1, n=10, t='data', p='gate--fixture.json', h='1' * 64, s=True)
        with self.assertRaises(ValueError): c.full_chain_fit([row], 512, [], 0, 0)

    def test_generic_exact_rows_membership_and_no_host_continuity_claim(self):
        pin = n.pin_bytes('/synthetic-fixtures/input.py', b'fixture')
        spec = dict(schema='e02-current-helper-generic-input-source-v1', files=[dict(pin=pin, mode='0o664', role='fixture')], memberships=[])
        row = dict(pin=pin, mode='0o664', uid=1, gid=1, device=1, inode=1, mtimeNs=10**18, ctimeNs=10**18, links=1)
        result = gi.validate_observation(spec, [row], [])
        self.assertFalse(result['runtimeAuthorized'])
        self.assertIn('NAMESPACE_LOCAL', result['observationIdentityMeaning'])
        changed = dict(row, mode='0o444')
        with self.assertRaises(ValueError): gi.validate_observation(spec, [changed], [])

    def test_generic_alias_missing_extra_or_duplicate_refused(self):
        pin = n.pin_bytes('/synthetic-fixtures/input.py', b'fixture')
        spec = dict(schema='e02-current-helper-generic-input-source-v1', files=[dict(pin=pin, mode='0o664', role='fixture')], memberships=[])
        row = dict(pin=pin, mode='0o664', uid=1, gid=1, device=1, inode=1, mtimeNs=1, ctimeNs=1, links=1)
        for rows in ([], [row, row], [dict(row, links=2)]):
            with self.assertRaises(ValueError): gi.validate_observation(spec, rows, [])


def accepted_collectors():
    """Future model-only explicit source loader; never called in preparation."""
    qpath = Path(CURRENT['operationalQualifier']['path'])
    hpath = Path(CURRENT['historyPrefix']['path'])
    for path, expected in ((qpath, CURRENT['operationalQualifier']), (hpath, CURRENT['historyPrefix'])):
        raw = path.read_bytes()
        if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError('CURRENT_PINNED_COLLECTOR_SOURCE')
    qspec = importlib.util.spec_from_file_location('qualification', qpath)
    q = importlib.util.module_from_spec(qspec)
    previous = sys.modules.get('qualification')
    sys.modules['qualification'] = q
    try:
        qspec.loader.exec_module(q)
        hspec = importlib.util.spec_from_file_location('fixture_current_history', hpath)
        h = importlib.util.module_from_spec(hspec); hspec.loader.exec_module(h)
    finally:
        if previous is None: sys.modules.pop('qualification', None)
        else: sys.modules['qualification'] = previous
    return q, h


class ExistingGateAndFinalCut(unittest.TestCase):
    def setUp(self):
        self.q, self.h = accepted_collectors()
        self.gate = self.q.RootFailstop(RUN, fixture_mode=False)
        self.bridge = c.ExistingRootCustody(RUN, self.q, self.h, self.gate)
        request = c.collector_request(RUN, 'reserve', [])
        reservation = dict(path=c.DATA_PARENT + '/' + RUN + '/reservation.json', bytes=512, sha256='1' * 64)
        ack = dict(reservation=reservation, reservedInsideMetadataBytes=65536,
                   metadataOwnerBytes=8388608, payloadAvailableBytes=49152, grantIssued=False)
        self.row = dict(request=request, requestPin=n.pin_bytes('/synthetic-fixtures/reserve-request.json', n.encoded(request)), expectedProof=reservation)
        self.origin = direct(request, output=json.dumps(ack, sort_keys=True, separators=(',', ':')) + '\n', count=20)
        self.plan = dict(schema='e02-root-collector-approved-command-sequence-v1', runId=RUN,
                         collectorScript=CURRENT['operationalCollector'], commands=[self.row])

    def test_same_actual_gate_is_retained_across_prefix(self):
        result = self.bridge.evaluate_prefix(self.plan, [self.origin])
        self.assertIs(self.bridge.gate, self.gate)
        self.assertTrue(result['historicalSuccessThroughPrefix'])
        self.assertFalse(result['finalAccountClosed'])

    def test_replacement_gate_pointer_poisons_original(self):
        self.bridge.gate = self.q.RootFailstop(RUN)
        with self.assertRaises(ValueError): self.bridge.evaluate_prefix(self.plan, [self.origin])
        self.assertTrue(self.gate.denied)
        self.assertEqual(self.bridge.phase, 'DENIED')

    def test_distinct_module_class_alias_or_subclass_refused(self):
        alias = types.SimpleNamespace(SCRIPT_PIN=self.q.SCRIPT_PIN, RootFailstop=type('OtherGate', (), {}))
        with self.assertRaises(ValueError): c.ExistingRootCustody(RUN, alias, self.h, self.gate)
        class Sub(self.q.RootFailstop): pass
        with self.assertRaises(ValueError): c.ExistingRootCustody(RUN, self.q, self.h, Sub(RUN))

    def test_missing_counter_permanent_poison_cannot_reopen(self):
        self.origin['launch']['unmodifiedResponse'].pop('original_token_count')
        with self.assertRaises(ValueError): self.bridge.evaluate_prefix(self.plan, [self.origin])
        first = self.gate.first
        self.origin['launch']['unmodifiedResponse']['original_token_count'] = 20
        with self.assertRaises(ValueError): self.bridge.evaluate_prefix(self.plan, [self.origin])
        self.assertEqual(self.gate.first, first)
        with self.assertRaises(ValueError): c.ExistingRootCustody(RUN, self.q, self.h, self.gate)

    def test_prefix_freezes_before_final_request_and_no_f_selfmember(self):
        prefix = dict(schema=self.h.BODY_SCHEMA, runId=RUN, collectorSource=CURRENT['collectorSource'],
                      expectedCommands=[self.row], origins=[self.origin])
        envelope = self.bridge.freeze(prefix, 49152, 64)
        self.assertIsInstance(envelope, bytes)
        self.assertEqual(self.bridge.phase, 'PREFIX_FROZEN')
        with self.assertRaises(ValueError): self.bridge.evaluate_prefix(self.plan, [self.origin])
        self.assertTrue(self.gate.denied)

    def test_final_witness_uses_same_gate_and_postf_operations_refuse(self):
        prefix = dict(schema=self.h.BODY_SCHEMA, runId=RUN, collectorSource=CURRENT['collectorSource'],
                      expectedCommands=[self.row], origins=[self.origin])
        envelope = self.bridge.freeze(prefix, 49152, 64)
        proof = n.pin_bytes(self.h.final_path(RUN), envelope)
        request = c.collector_request(RUN, 'record', ['--kind', 'diagnostic', '--name', self.h.FINAL_NAME,
                                                   '--input-base64', base64.b64encode(envelope).decode()])
        final_row = self.bridge.final_row('/synthetic-fixtures/F-request-memory-only.json', request, proof)
        ack = dict(index=1, store='data', proof=proof, payloadUsedBytes=len(envelope),
                   reservedBytes=65536, metadataOwnerBytes=8388608)
        final_origin = direct(request, output=json.dumps(ack, sort_keys=True, separators=(',', ':')) + '\n', count=20)
        result = self.bridge.finish(envelope, final_row, final_origin)
        self.assertTrue(result['collectorCommandsQualified'])
        self.assertIs(self.bridge.gate, self.gate)
        self.assertEqual(self.bridge.phase, 'FINAL_QUALIFIED')
        with self.assertRaises(ValueError): self.bridge.finish(envelope, final_row, final_origin)

    def test_wrong_remaining_budget_or_ownf_in_prefix_refused(self):
        prefix = dict(schema=self.h.BODY_SCHEMA, runId=RUN, collectorSource=CURRENT['collectorSource'],
                      expectedCommands=[self.row], origins=[self.origin])
        with self.assertRaises(ValueError): self.bridge.freeze(prefix, 49151, 64)
        self.assertTrue(self.gate.denied)

    def test_structural_history_new_gate_cannot_replace_actual_poison(self):
        self.gate.denied = True; self.gate.first = 'ACTUAL_PRIOR_FAULT'
        prefix = dict(schema=self.h.BODY_SCHEMA, runId=RUN, collectorSource=CURRENT['collectorSource'],
                      expectedCommands=[self.row], origins=[self.origin])
        # Structural prefix validity does not revive the actual live gate.
        self.h.validate_prefix(prefix, RUN, CURRENT['collectorSource'])
        with self.assertRaises(ValueError): self.bridge.freeze(prefix, 49152, 64)
        self.assertEqual(self.gate.first, 'ACTUAL_PRIOR_FAULT')


if __name__ == '__main__':
    unittest.main()
