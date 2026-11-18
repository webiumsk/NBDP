"""Pure current helper metadata rendering; no IO, clocks or authority issuance.

Root supplies genuine original receipt bytes/registered pins. The source/control
context validates exact reviewed selections, not platform authenticity. Actual
account/lease/failstop identity, current-input approval, fit and one-use runtime
authorization remain external Root obligations. No mutable readiness flag can
replace the accepted source/control context.
"""
import copy
import hashlib
import re
import shlex
from native_metadata import (need, closed, integer, equal, pin_shape, pin_bytes,
                             encoded, verified_value, decode_original_lease,
                             canonical_request)
from current_bindings import (CURRENT, HOST_POLICY, CAPTURE_POLICY,
                              TRUE_AUTHORS, EXCLUSIONS, TEMPLATES_PATH,
                              CURRENT_PLAN_BASE, RUNTIME_SOURCES, HOST_SOURCE, SOURCE_MODES)

DATA_PARENT = '/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual'
RUNTIME_PARENT = '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-actual-r1'
GENERIC_KINDS = ('producerData', 'sourceQa', 'sourceSecurity', 'controlData', 'concreteInput')
PLAN_KEYS = set('schema scope runId creationNonce name uidGid inputRoot controlRoot outputRoot dockerConfig lease source8 guardManifest guardRoot tools expectedImageConfigSha256'.split())
VERDICT_DECISION = 'ACCEPT_CURRENT_CONCRETE_INPUTS_FOR_ONE_HELPER_PROBE_ONLY'
SOURCE_DECISION = 'ACCEPT_CURRENT_HELPER_METHOD_RENDER_SOURCE_ONLY'
CONTROL_DECISION = 'ACCEPT_CURRENT_HELPER_METHOD_RENDER_PURE_CONTROL_DATA_ONLY'


def fixed_contract(fixed):
    equal(fixed['schema'], 'e02-helper-current178-render-templates-v1')
    equal(fixed['rawSourceGates'], dict(producerSource=CURRENT['producerSource'],
                                       controllerSource=CURRENT['controllerSource']))
    equal(fixed['dataSubjectBindings'], fixed['rawSourceGates'])
    equal(fixed['compiledControllerBindings']['acceptedProducerSubject'], CURRENT['producerSource'])
    equal(fixed['compiledControllerBindings']['source8'], fixed['planWithoutGates']['source8'])
    equal(fixed['compiledControllerBindings']['sourceModes'], SOURCE_MODES)
    equal(fixed['planWithoutGates'], CURRENT_PLAN_BASE)
    equal(fixed['controllerRuntimeSources'], RUNTIME_SOURCES)
    equal(fixed['hostSource'], HOST_SOURCE)
    need(all(type(mode) is int and mode == 0o664 for mode in
             fixed['compiledControllerBindings']['sourceModes'].values()), 'EXACT_SOURCE0664')
    equal(fixed['hostPolicy'], HOST_POLICY)
    equal(fixed['capturePolicy'], CAPTURE_POLICY)
    for value in fixed['authorities'].values():
        pin_shape(value)
    need(fixed['hostSource'] in fixed['controllerRuntimeSources'] and
         fixed['hostSource']['path'].endswith('/host.py'), 'EXACT_HOST_SOURCE')
    equal(fixed['trueAuthors'], TRUE_AUTHORS)
    equal(fixed['conservativeReviewerExclusions'], EXCLUSIONS)
    equal(fixed['authorities']['producerDataAcceptance'], CURRENT['producerDataAcceptance'])
    equal(fixed['authorities']['controllerDataAcceptance'], CURRENT['controllerDataAcceptance'])
    equal(fixed['authorities']['controllerSourceAcceptance'], CURRENT['controllerSourceAcceptance'])
    equal(fixed['authorities']['collectorSourceAcceptance'], CURRENT['collectorSourceAcceptance'])
    equal(fixed['authorities']['collectorDataAcceptance'], CURRENT['collectorDataAcceptance'])
    closed(fixed['genericGateTemplates'], GENERIC_KINDS)
    for kind, gate in fixed['genericGateTemplates'].items():
        closed(gate, ('schema', 'kind', 'actor', 'decision', 'subject', 'evidence', 'scope'))
        equal(gate['schema'], 'e02-one-cid-helper-probe-gate-v1')
        equal(gate['kind'], kind)
        equal(gate['decision'], None)
        equal(gate['scope'], 'ONE_OWNED_HELPER_PROBE_ONLY')
        if kind == 'concreteInput':
            equal(gate['subject'], None)
            equal(gate['evidence'], None)
        else:
            equal(gate['subject'], fixed['rawSourceGates'][
                'producerSource' if kind == 'producerData' else 'controllerSource'])
            authority = dict(producerData='producerDataAcceptance', controlData='controllerDataAcceptance',
                             sourceQa='sourceQaReview', sourceSecurity='sourceSecurityReview')[kind]
            equal(gate['evidence'], fixed['authorities'][authority])
    closed(fixed['planWithoutGates'], PLAN_KEYS)
    equal(fixed['immutableOperationalBounds']['rootSlotBytes'], 65536)
    equal(fixed['immutableOperationalBounds']['payloadBytes'], 49152)
    equal(fixed['immutableOperationalBounds']['prepaidLedgerBytes'], 16384)
    equal(fixed['immutableOperationalBounds']['maximumWrites'], 64)
    equal(fixed['actualRootRunId'], None)
    equal(fixed['actualOriginalLease'], None)
    equal(fixed['actualReservedAccount'], None)
    equal(fixed['actualRootRelease'], None)
    equal(fixed['runtimeAuthorized'], False)
    return fixed


def _review_pair(records, subject, decision, forbidden):
    need(type(records) is list and len(records) == 2, 'TWO_ACTUAL_REVIEW_RECORDS')
    sessions, pins = set(), []
    for role, record in zip(('qa', 'security'), records):
        value = verified_value(record)
        closed(value, ('role', 'session', 'decision', 'subject'))
        equal(value['role'], role)
        equal(value['decision'], decision)
        equal(value['subject'], subject)
        actor_list([value['session']], 'TYPED_REVIEW_SESSION', False)
        need(value['session'] != '/root' and
             value['session'] not in forbidden and value['session'] not in sessions,
             'ACTUAL_DISTINCT_INDEPENDENT_REVIEWERS')
        sessions.add(value['session'])
        pins.append(record['pin'])
    return pins


def actor_list(values, label, allow_empty=True):
    """Actor vectors are exact unique lists, never strings/tuples/set aliases."""
    need(type(values) is list and (allow_empty or len(values) > 0), label)
    need(all(type(x) is str and len(x) <= 256 and
             re.fullmatch(r'/root(?:/[A-Za-z0-9_-]+)*', x) for x in values), label)
    need(len(values) == len(set(values)), label)
    return frozenset(values)


def actor_closure(fixed, context):
    """Derive every named Source/design/control actor before ANY review pair.

    Explicit typed selectors only; no global JSON projection or actor discovery.
    Both authenticated original subjects are decoded before reviewers are used.
    """
    fixed_contract(fixed)
    closed(context, ('schema', 'source', 'sourceAcceptance', 'sourceReviews',
                     'controlData', 'controlAcceptance', 'controlReviews'))
    equal(context['schema'], 'e02-current-helper-render-context-v1')
    source, data = verified_value(context['source']), verified_value(context['controlData'])
    equal(source['schema'], 'e02-helper-current178-source-subject-v1')
    equal(data['schema'], 'e02-helper-current178-control-data-subject-v1')
    authors = actor_list(TRUE_AUTHORS, 'IMMUTABLE_TRUE_AUTHORS', False)
    exclusions = actor_list(EXCLUSIONS, 'IMMUTABLE_EXCLUSIONS', False)
    operators = frozenset()
    # Required Source selectors match the real Source subject, including design
    # contributors. Additional explicit design/operator selectors are typed too.
    for field in ('author', 'coordinator'):
        need(field in source, 'SOURCE_ACTOR_SELECTOR')
    for field in ('sourceContributors', 'operators', 'reviewerExclusions'):
        need(field in source, 'SOURCE_ACTOR_SELECTOR')
    for field in ('authors', 'operators'):
        need(field in data, 'CONTROL_ACTOR_SELECTOR')
    actor_list(data['operators'], 'CONTROL_ACTUAL_OPERATORS', False)
    for value in (source, data):
        for field in ('author', 'actor', 'coordinator'):
            if field in value:
                authors |= actor_list([value[field]], 'TYPED_' + field, False)
        for field in ('authors', 'sourceContributors', 'designContributors', 'sourceContributorUnion'):
            if field in value:
                authors |= actor_list(value[field], 'TYPED_' + field,
                                      field not in ('authors', 'sourceContributors'))
        for field in ('operators', 'sourcePreparationOperators'):
            if field in value:
                operators |= actor_list(value[field], 'TYPED_' + field)
        if 'reviewerExclusions' in value:
            exclusions |= actor_list(value['reviewerExclusions'], 'TYPED_reviewerExclusions')
    return source, data, authors, operators, exclusions | authors | operators


def source_context(fixed, context):
    """Original raw/pin pairs bind actual accepted Source and pure control DATA.

    Root externally authenticates genuine provenance; this issues no acceptance.
    The full immutable/actual actor union exists before either review pair.
    """
    source, data, authors, operators, forbidden = actor_closure(fixed, context)
    acceptance = verified_value(context['sourceAcceptance'])
    equal(source['templates'], pin_bytes(TEMPLATES_PATH, encoded(fixed)))
    equal(source['currentTuple'], CURRENT)
    equal(source['selfApproval'], False)
    equal(source['executionAuthorized'], False)
    equal(source['modelsExecuted'], 0)
    source_pins = _review_pair(context['sourceReviews'], context['source']['pin'], SOURCE_DECISION, forbidden)
    closed(acceptance, ('schema', 'actor', 'decision', 'subject', 'reviews',
                        'modelsDefined', 'modelsExecuted', 'scope', 'executionAuthorized'))
    equal(acceptance['schema'], 'e02-root-helper-current178-source-acceptance-v1')
    equal(acceptance['actor'], '/root')
    equal(acceptance['decision'], SOURCE_DECISION)
    equal(acceptance['subject'], context['source']['pin'])
    equal(acceptance['reviews'], source_pins)
    equal(acceptance['modelsDefined'], integer(source['modelsDefined'], 1, 10000))
    equal(acceptance['modelsExecuted'], 0)
    equal(acceptance['scope'], 'CURRENT_HELPER_METHOD_RENDER_SOURCE_AND_CONTROL_DEFINITIONS_ONLY')
    equal(acceptance['executionAuthorized'], False)
    equal(data['helperSource'], context['source']['pin'])
    for key in ('modelsDefined', 'modelsExecuted', 'modelsPassed'):
        equal(data[key], source['modelsDefined'])
    equal(data['modelsFailed'], 0)
    equal(data['skipped'], 0)
    equal(data['inputsUnchanged'], True)
    equal(data['executionAuthorized'], False)
    control_pins = _review_pair(context['controlReviews'], context['controlData']['pin'],
                                CONTROL_DECISION, forbidden)
    receipt = verified_value(context['controlAcceptance'])
    closed(receipt, ('schema', 'actor', 'decision', 'subject', 'helperSource', 'reviews',
                     'modelsDefined', 'modelsExecuted', 'modelsPassed', 'modelsFailed',
                     'skipped', 'inputsUnchanged', 'scope', 'executionAuthorized'))
    equal(receipt['schema'], 'e02-root-helper-current178-control-data-acceptance-v1')
    equal(receipt['actor'], '/root')
    equal(receipt['decision'], CONTROL_DECISION)
    equal(receipt['subject'], context['controlData']['pin'])
    equal(receipt['helperSource'], context['source']['pin'])
    equal(receipt['reviews'], control_pins)
    for key in ('modelsDefined', 'modelsExecuted', 'modelsPassed', 'modelsFailed', 'skipped', 'inputsUnchanged'):
        equal(receipt[key], data[key])
    equal(receipt['scope'], 'CURRENT_HELPER_METHOD_RENDER_PURE_CONTROL_DATA_ONLY')
    equal(receipt['executionAuthorized'], False)
    return source


def roster(fixed, actual_operators, additional_authors=(), context=None):
    """Construct a complete declaration; consuming boundaries always revalidate."""
    fixed_contract(fixed)
    need(type(additional_authors) in (tuple, list), 'ADDITIONAL_AUTHORS_LIST')
    authors = actor_list(TRUE_AUTHORS, 'IMMUTABLE_TRUE_AUTHORS', False)
    authors |= actor_list(list(additional_authors), 'ADDITIONAL_AUTHORS')
    operators = actor_list(actual_operators, 'ACTUAL_OPERATORS', False)
    exclusions = actor_list(EXCLUSIONS, 'IMMUTABLE_EXCLUSIONS', False)
    if context is not None:
        source_context(fixed, context)
        _, _, required_authors, required_operators, forbidden = actor_closure(fixed, context)
        authors |= required_authors
        operators |= required_operators
        exclusions |= forbidden
    need('/root' in operators, 'ACTUAL_ROOT_OPERATOR')
    return dict(authors=sorted(authors), operators=sorted(operators),
                concreteReviewerExclusions=sorted(exclusions | authors | operators))


def validate_roster(fixed, context, actor_roster):
    """Caller lists may add disclosed actors but cannot reduce real closure."""
    source_context(fixed, context)
    _, _, required_authors, required_operators, forbidden = actor_closure(fixed, context)
    closed(actor_roster, ('authors', 'operators', 'concreteReviewerExclusions'))
    authors = actor_list(actor_roster['authors'], 'CONCRETE_AUTHORS', False)
    operators = actor_list(actor_roster['operators'], 'CONCRETE_OPERATORS', False)
    exclusions = actor_list(actor_roster['concreteReviewerExclusions'], 'CONCRETE_EXCLUSIONS', False)
    need(required_authors <= authors and required_operators <= operators and '/root' in operators,
         'COMPLETE_IMMUTABLE_AND_ACTUAL_ACTOR_ROSTER')
    need(exclusions == forbidden | authors | operators, 'EXACT_COMPLETE_REVIEWER_EXCLUSIONS')
    # A newly disclosed concrete participant must not retrospectively become an
    # independent Source/control reviewer. Recheck both full original pairs.
    _review_pair(context['sourceReviews'], context['source']['pin'], SOURCE_DECISION, exclusions)
    _review_pair(context['controlReviews'], context['controlData']['pin'], CONTROL_DECISION, exclusions)
    return actor_roster


def plan_without_gates(fixed, context, run, nonce, lease_pin, lease_raw, reservation_ack):
    source_context(fixed, context)
    need(type(run) is str and re.fullmatch('[0-9a-f]{32}', run) and
         run not in fixed['permanentlyUnavailableRunIds'], 'FRESH_ROOT_RUN')
    need(type(nonce) is str and re.fullmatch('[0-9a-f]{32}', nonce), 'ROOT_NONCE')
    closed(reservation_ack, ('reservation', 'reservedInsideMetadataBytes', 'metadataOwnerBytes',
                             'payloadAvailableBytes', 'grantIssued'))
    pin_shape(reservation_ack['reservation'])
    equal(reservation_ack['reservation']['path'], DATA_PARENT + '/' + run + '/reservation.json')
    for key, expected in (('reservedInsideMetadataBytes', 65536), ('metadataOwnerBytes', 8388608),
                          ('payloadAvailableBytes', 49152), ('grantIssued', False)):
        equal(reservation_ack[key], expected, 'GENUINE_EXACT_RESERVE_ACK')
    equal(pin_shape(lease_pin), pin_bytes(DATA_PARENT + '/' + run + '/lease--original.json', lease_raw))
    decode_original_lease(lease_raw, run)
    root = RUNTIME_PARENT + '/' + run
    plan = copy.deepcopy(fixed['planWithoutGates'])
    plan.update(runId=run, creationNonce=nonce, name='nbdp-helper-probe-' + run + '-' + nonce,
                inputRoot=root + '/input', controlRoot=root + '/control', outputRoot=root + '/output',
                dockerConfig=root + '/docker-config', lease=copy.deepcopy(lease_pin))
    closed(plan, PLAN_KEYS)
    return plan


def concrete_subject(plan):
    closed(plan, PLAN_KEYS)
    return dict(scope='CURRENT_CONCRETE_INPUTS', sha256=hashlib.sha256(encoded(plan)).hexdigest())


def validate_concrete_receipt(fixed, context, value, subject, actor_roster):
    validate_roster(fixed, context, actor_roster)
    closed(value, ('schema', 'actor', 'decision', 'subject', 'reviews'))
    equal(value['schema'], 'e02-root-helper-probe-concrete-inputs-v1')
    equal(value['actor'], '/root')
    equal(value['decision'], VERDICT_DECISION)
    equal(value['subject'], subject)
    need(type(value['reviews']) is list and len(value['reviews']) == 2, 'TWO_CONCRETE_VERDICTS')
    sessions = set()
    for role, verdict in zip(('qa', 'security'), value['reviews']):
        closed(verdict, ('role', 'session', 'decision', 'subject'))
        equal(verdict['role'], role)
        equal(verdict['decision'], VERDICT_DECISION)
        equal(verdict['subject'], subject)
        session = verdict['session']
        need(type(session) is str and session.startswith('/root/') and
             session not in actor_roster['concreteReviewerExclusions'] and session not in sessions,
             'ACTUAL_INDEPENDENT_CONCRETE_VERDICTS')
        sessions.add(session)


def generic_gate_values(fixed, context, plan_without, actor_roster, receipt, registered_receipt):
    validate_roster(fixed, context, actor_roster)
    subject = concrete_subject(plan_without)
    validate_concrete_receipt(fixed, context, receipt, subject, actor_roster)
    equal(pin_shape(registered_receipt), pin_bytes(DATA_PARENT + '/' + plan_without['runId'] +
                                                  '/gate--concrete-review.json', encoded(receipt)))
    gates = copy.deepcopy(fixed['genericGateTemplates'])
    for kind, gate in gates.items():
        gate['decision'] = 'ACCEPT'
        if kind == 'concreteInput':
            gate.update(subject=subject, evidence=copy.deepcopy(registered_receipt))
        if kind in ('sourceQa', 'sourceSecurity'):
            need(gate['actor'] not in actor_roster['authors'] + actor_roster['operators'],
                 'INDEPENDENT_CONTROLLER_SOURCE_GATE')
    return gates


def bind_registered_gates(fixed, context, plan_without, gate_values, registered_gate_pins,
                          actor_roster, concrete_receipt, registered_concrete_receipt):
    validate_roster(fixed, context, actor_roster)
    closed(plan_without, PLAN_KEYS)
    closed(gate_values, GENERIC_KINDS)
    closed(registered_gate_pins, GENERIC_KINDS)
    equal(gate_values, generic_gate_values(fixed, context, plan_without, actor_roster,
                                         concrete_receipt, registered_concrete_receipt),
          'REVALIDATE_ACTUAL_CONCRETE_RECEIPT_AND_ALL_GATE_VALUES')
    gates = copy.deepcopy(fixed['rawSourceGates'])
    for kind in GENERIC_KINDS:
        value = gate_values[kind]
        closed(value, ('schema', 'kind', 'actor', 'decision', 'subject', 'evidence', 'scope'))
        equal(value['decision'], 'ACCEPT')
        equal(value['kind'], kind)
        expected = dict(fixed['genericGateTemplates'][kind])
        expected['decision'] = 'ACCEPT'
        if kind == 'concreteInput':
            expected.update(subject=concrete_subject(plan_without), evidence=value['evidence'])
            equal(value['actor'], '/root')
            pin_shape(value['evidence'])
        equal(value, expected, 'EXACT_RENDERED_REGISTERED_GATE')
        equal(pin_shape(registered_gate_pins[kind]), pin_bytes(DATA_PARENT + '/' + plan_without['runId'] +
                  '/gate--' + kind + '.json', encoded(value)))
        gates[kind] = copy.deepcopy(registered_gate_pins[kind])
    plan = copy.deepcopy(plan_without)
    plan['gates'] = gates
    return plan


def root_release_template(fixed, context, plan, registered_plan, actor_roster):
    validate_roster(fixed, context, actor_roster)
    closed(plan, PLAN_KEYS | {'gates'})
    closed(plan['gates'], set(GENERIC_KINDS) | {'producerSource', 'controllerSource'})
    for key, value in fixed['rawSourceGates'].items():
        equal(plan['gates'][key], value)
    equal(pin_shape(registered_plan), pin_bytes(DATA_PARENT + '/' + plan['runId'] +
                                                '/plan--concrete.json', encoded(plan)))
    value = copy.deepcopy(fixed['rootReleaseTemplate'])
    value.update(runId=plan['runId'], creationNonce=plan['creationNonce'], plan=copy.deepcopy(registered_plan),
                 gates=copy.deepcopy(plan['gates']), authors=copy.deepcopy(actor_roster['authors']),
                 operators=copy.deepcopy(actor_roster['operators']))
    equal(value['executionAuthorized'], None, 'ROOT_RUNTIME_DECISION_REMAINS_UNISSUED')
    return value


def host_seven_key_request(fixed, context, plan_pin, actual_release, release_pin):
    source_context(fixed, context)
    closed(actual_release, ('schema', 'actor', 'executionAuthorized', 'runId', 'creationNonce',
                           'subject', 'plan', 'gates', 'authors', 'operators', 'outerCustodyReservationBytes'))
    _, _, _, _, forbidden = actor_closure(fixed, context)
    # Root11 has no exclusion field. Derive it from the full immutable/actual
    # context and supplied Root11 declarations, then validate their completeness.
    declared_authors = actor_list(actual_release['authors'], 'ROOT_RELEASE_AUTHORS', False)
    declared_operators = actor_list(actual_release['operators'], 'ROOT_RELEASE_OPERATORS', False)
    validate_roster(fixed, context, dict(authors=actual_release['authors'],
        operators=actual_release['operators'],
        concreteReviewerExclusions=sorted(forbidden | declared_authors | declared_operators)))
    equal(actual_release['schema'], 'e02-one-cid-helper-probe-root-release-v1')
    equal(actual_release['actor'], '/root')
    equal(actual_release['executionAuthorized'], True)
    equal(actual_release['plan'], pin_shape(plan_pin))
    equal(actual_release['subject'], CURRENT['controllerSource'])
    equal(actual_release['gates']['controllerSource'], CURRENT['controllerSource'])
    equal(actual_release['gates']['producerSource'], CURRENT['producerSource'])
    equal(actual_release['outerCustodyReservationBytes'], 65536)
    equal(plan_pin['path'], DATA_PARENT + '/' + actual_release['runId'] + '/plan--concrete.json')
    equal(pin_shape(release_pin), pin_bytes(DATA_PARENT + '/' + actual_release['runId'] +
                                          '/grant--release.json', encoded(actual_release)))
    host, python = fixed['hostSource']['path'], fixed['planWithoutGates']['tools']['python']['path']
    argv = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'LC_ALL=C.UTF-8',
            '/usr/bin/timeout', '--signal=KILL', '183s', python, '-I', '-B', host,
            '--plan', plan_pin['path'], '--plan-sha', plan_pin['sha256'], '--root-release',
            release_pin['path'], '--root-release-sha', release_pin['sha256']]
    request = dict(HOST_POLICY, cmd=shlex.join(argv))
    canonical_request('HOST7', request, HOST_POLICY)
    return request
