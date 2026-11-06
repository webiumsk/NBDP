"""Pure continuity/fit adapter for externally loaded exact collector modules.

No IO/tools/subprocesses, registration, RootFailstop construction or monitor is
performed here. Root authenticates module pins, original API provenance and the
permanent run quarantine, and retains this exact live object through final F.
history.validate_prefix's internally fresh gate is only a structural check.
"""
import hashlib
import shlex
from native_metadata import (need, equal, closed, integer, pin_shape, pin_bytes,
                             encoded, canonical_request, complete_origin)
from current_bindings import CURRENT, COLLECTOR_POLICY

DATA_PARENT = '/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual'
KINDS = ('lease', 'plan', 'gate', 'grant', 'api-request', 'api-frame', 'diagnostic')


def collector_request(run, operation, operands):
    need(type(run) is str and len(run) == 32 and all(c in '0123456789abcdef' for c in run), 'RUN_ID')
    need(operation in ('reserve', 'record', 'copy', 'status') and type(operands) is list and
         all(type(word) is str for word in operands), 'CLOSED_COLLECTOR_REQUEST_COMPONENTS')
    if operation in ('reserve', 'status'):
        equal(operands, [])
    prefix = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'LC_ALL=C.UTF-8',
              '/usr/bin/timeout', '--signal=KILL', '10s',
              '/home/peterhorvath/.miniforge3/bin/python3.13', '-I', '-B',
              CURRENT['operationalCollector']['path']]
    request = dict(COLLECTOR_POLICY, cmd=shlex.join(prefix + [operation, '--run-id', run] + operands))
    canonical_request('COLLECTOR7', request)
    return request


def strict_ack(ack, operation):
    """Add exact primitive domains; keep accepted Source2 ACK/state algebra."""
    if operation == 'reserve':
        closed(ack, ('reservation', 'reservedInsideMetadataBytes', 'metadataOwnerBytes',
                     'payloadAvailableBytes', 'grantIssued'))
        pin_shape(ack['reservation'])
        for key, expected in (('reservedInsideMetadataBytes', 65536), ('metadataOwnerBytes', 8388608),
                              ('payloadAvailableBytes', 49152), ('grantIssued', False)):
            equal(ack[key], expected)
    elif operation == 'status':
        closed(ack, ('state', 'historicalIO', 'reservedBytes', 'ledgerPrechargedBytes',
                     'payloadUsedBytes', 'recordCount', 'physicalBytes'))
        equal(ack['state'], 'CURRENT_STRUCTURAL_CUSTODY_ONLY')
        equal(ack['historicalIO'], 'UNKNOWN')
        for key in ('reservedBytes', 'ledgerPrechargedBytes', 'payloadUsedBytes', 'recordCount', 'physicalBytes'):
            integer(ack[key], 0)
    else:
        closed(ack, ('index', 'store', 'proof', 'payloadUsedBytes', 'reservedBytes', 'metadataOwnerBytes'))
        for key in ('index', 'payloadUsedBytes', 'reservedBytes', 'metadataOwnerBytes'):
            integer(ack[key], 0)
        pin_shape(ack['proof'])
        need(ack['store'] in ('data', 'repo'), 'EXACT_ACK_STORE')
    return ack


class ExistingRootCustody:
    """One live accepted q.RootFailstop instance; never reopen/replace/reset it."""
    def __init__(self, run, qualification, history, existing_root_failstop):
        # q/history are Root-loaded from the exact immutable pins in read-map.
        # Pure dependency injection is not authentication of those supplied modules.
        equal(qualification.SCRIPT_PIN, CURRENT['operationalCollector'])
        equal(history.SOURCE_PATH, CURRENT['collectorSource']['path'])
        need(history.q is qualification, 'EXACT_SAME_QUALIFIER_HISTORY_PEER')
        need(type(existing_root_failstop) is qualification.RootFailstop, 'EXACT_EXISTING_ROOT_FAILSTOP_CLASS')
        equal(existing_root_failstop.run, run)
        equal(existing_root_failstop.fixture_mode, False)
        equal(existing_root_failstop.denied, False)
        self.q, self.history, self.run = qualification, history, run
        self.gate = self._original_gate = existing_root_failstop
        self.phase = 'OPEN'
        self._frozen = None
        self._model = None

    def _live(self, phase):
        need(self.gate is self._original_gate, 'SAME_ACTUAL_GATE_OBJECT_REQUIRED')
        need(type(self.gate) is self.q.RootFailstop, 'EXACT_ACTUAL_GATE_CLASS')
        equal(self.gate.run, self.run)
        equal(self.gate.fixture_mode, False)
        equal(self.gate.denied, False, 'PERMANENT_ROOT_DENIAL')
        equal(self.phase, phase, 'EXACT_FINAL_CUT_PHASE')

    def _deny(self, error):
        # Even replacement of the public gate pointer cannot clear the retained
        # genuine object's denial. Root must also preserve runId quarantine.
        self._original_gate.denied = True
        if self._original_gate.first is None:
            self._original_gate.first = type(error).__name__ + ':' + str(error)
        self.phase = 'DENIED'
        raise error

    def evaluate_prefix(self, plan, origins):
        try:
            self._live('OPEN')
            closed(plan, ('schema', 'runId', 'collectorScript', 'commands'))
            equal(plan['schema'], 'e02-root-collector-approved-command-sequence-v1')
            equal(plan['runId'], self.run)
            equal(plan['collectorScript'], CURRENT['operationalCollector'])
            need(type(plan['commands']) is list and type(origins) is list and
                 len(plan['commands']) == len(origins), 'COMPLETE_PREFIX')
            model = dict(used=0, rows=[], physical=0)
            for row, origin in zip(plan['commands'], origins):
                closed(row, ('request', 'requestPin', 'expectedProof'))
                complete_origin('COLLECTOR7', origin, row['request'], ['/root'])
                operation = self.q.command(row['request'], self.run)
                ack = strict_ack(self.q.complete_origin(origin, row['request']), operation)
                self.q.exact_ack(operation, row['request'], row['expectedProof'], ack, self.run, model)
            result = self._original_gate.evaluate(plan, origins)
            equal(result['collectorCommandsQualified'], True)
            equal(result['fixtureOnly'], False)
            self._model = model
            return dict(payloadUsedBytes=model['used'], remainingPayloadBytes=49152 - model['used'],
                        writesUsed=len(model['rows']), remainingWrites=64 - len(model['rows']),
                        physicalBytes=model['physical'], reservedBytes=65536,
                        historicalSuccessThroughPrefix=True, finalAccountClosed=False)
        except BaseException as error:
            return self._deny(error)

    def freeze(self, prefix, remaining_payload_bytes, remaining_writes):
        """Only Root may invoke on actual prefix after all pre-F physical writes."""
        try:
            self._live('OPEN')
            closed(prefix, ('schema', 'runId', 'collectorSource', 'expectedCommands', 'origins'))
            equal(prefix['schema'], self.history.BODY_SCHEMA)
            equal(prefix['runId'], self.run)
            equal(prefix['collectorSource'], CURRENT['collectorSource'])
            plan = dict(schema='e02-root-collector-approved-command-sequence-v1', runId=self.run,
                        collectorScript=CURRENT['operationalCollector'], commands=prefix['expectedCommands'])
            counters = self.evaluate_prefix(plan, prefix['origins'])
            equal(integer(remaining_payload_bytes, 0, 49152), counters['remainingPayloadBytes'])
            equal(integer(remaining_writes, 1, 64), counters['remainingWrites'])
            envelope = self.history.freeze_prefix(prefix, self.run, CURRENT['collectorSource'], remaining_payload_bytes)
            # This is a future actual calculation, not a Source-stage estimate.
            need(len(envelope) <= remaining_payload_bytes, 'F_PAYLOAD_SAME_SLOT')
            self._frozen = envelope
            self.phase = 'PREFIX_FROZEN'
            return envelope
        except BaseException as error:
            return self._deny(error)

    def final_row(self, request_pin_path, request, expected_proof):
        """Derive in memory only, after envelope freeze; never retain own F."""
        try:
            self._live('PREFIX_FROZEN')
            equal(pin_shape(expected_proof), dict(path=self.history.final_path(self.run),
                  bytes=len(self._frozen), sha256=hashlib.sha256(self._frozen).hexdigest()))
            canonical_request('COLLECTOR7', request)
            words, route = self.q.command_words(request)
            equal(route, 'ROOT_CLEANENV_KILL10S')
            equal(self.q.command(request, self.run), 'record')
            equal(words[7:12], ['--kind', 'diagnostic', '--name', self.history.FINAL_NAME, '--input-base64'])
            equal(len(words), 13)
            equal(self.q.decode_input(words[12], 49152), self._frozen)
            return dict(request=request, requestPin=pin_bytes(request_pin_path, encoded(request)),
                        expectedProof=expected_proof)
        except BaseException as error:
            return self._deny(error)

    def finish(self, envelope, final_row, actual_final_platform_origin):
        """Final platform witness only; no function here writes/copies a proof."""
        try:
            self._live('PREFIX_FROZEN')
            equal(envelope, self._frozen, 'SAME_FROZEN_PREFIX_ENVELOPE')
            complete_origin('COLLECTOR7', actual_final_platform_origin,
                            final_row['request'], ['/root'])
            result = self.history.qualify_with_final_witness(envelope, self.run,
                      CURRENT['collectorSource'], final_row, actual_final_platform_origin,
                      self._original_gate)
            equal(result['collectorCommandsQualified'], True)
            equal(self.gate is self._original_gate, True)
            self.phase = 'FINAL_QUALIFIED'
            return result
        except BaseException as error:
            return self._deny(error)


def full_chain_fit(registered_rows, reservation_bytes, pending_payload_lengths,
                   remaining_proof_payload_bytes, remaining_proof_writes):
    """Exact supplied-byte arithmetic; never a guarantee about unknown output.

    Root passes every physical record/copy charge row, including duplicates.
    Registered rows are the actual canonical collector ledger rows. Future
    payload lengths must be exact or conservative externally accepted bounds.
    """
    integer(reservation_bytes, 1, 1024)
    need(type(registered_rows) is list and type(pending_payload_lengths) is list, 'EXPLICIT_FINITE_FIT_INPUTS')
    need(len(registered_rows) <= 64 and len(pending_payload_lengths) <= 64, 'FINITE_FIT_COUNTS')
    used, physical = 0, reservation_bytes
    for i, row in enumerate(registered_rows, 1):
        closed(row, ('i', 'n', 't', 'p', 'h', 's'))
        equal(row['i'], i)
        integer(row['n'], 0, 49152)
        need(row['t'] in ('data', 'repo') and type(row['p']) is str and type(row['h']) is str,
             'CLOSED_CHARGE_ROW')
        need(len(row['p'].encode('utf8', 'strict')) <= 128 and len(row['h']) == 64 and
             all(c in '0123456789abcdef' for c in row['h']), 'CHARGE_NAME_HASH_BOUND')
        need(row['s'] is None or type(row['s']) is int and 1 <= row['s'] < i,
             'EXACT_PRIOR_COPY_INDEX_OR_NULL')
        need(len(encoded(row)) <= 224, 'ORIGINAL_CHARGE_ROW_BOUND')
        used += row['n']
        physical += row['n'] + len(encoded(row))
    for value in pending_payload_lengths:
        integer(value, 0, 49152)
    integer(remaining_proof_payload_bytes, 0, 49152)
    integer(remaining_proof_writes, 0, 64)
    writes = len(registered_rows) + len(pending_payload_lengths) + remaining_proof_writes
    payload = used + sum(pending_payload_lengths) + remaining_proof_payload_bytes
    #224 per not-yet-written row is the existing precharged ledger bound.
    physical_bound = physical + sum(pending_payload_lengths) + remaining_proof_payload_bytes + \
                     224 * (len(pending_payload_lengths) + remaining_proof_writes)
    need(writes <= 64 and payload <= 49152 and physical_bound <= 65536, 'WHOLE_SINGLE_SLOT_FIT')
    return dict(registeredPayloadBytes=used, payloadBoundBytes=payload,
                physicalBoundBytes=physical_bound, writesBound=writes,
                prepaidLedgerBytes=16384, reservedBytes=65536,
                boundMeaning='EXACT_REGISTERED_PLUS_DECLARED_REMAINING_BOUNDS_NOT_UNKNOWN_GZIP_GUARANTEE')
