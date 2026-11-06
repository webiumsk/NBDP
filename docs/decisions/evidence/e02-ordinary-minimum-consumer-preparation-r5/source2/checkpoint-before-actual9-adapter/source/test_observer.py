"""PREPARED NOT EXECUTED: synthetic integrated observer/wire DATA controls.

No producer, cryptographic library, Docker, SDK, socket or real approval runs.
This positive is a complete observer+publication graph; it deliberately does
not claim coverage of consumer.consume's whole two-window GUI/tool graph.
"""
import base64
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strict
import wire
import observer
from test_data_controls import publication_data, pin


def graph(root, role='incoming', index=0, observed=True, late=False, event_content=None):
    files, old_proxy, record, expected, spec, role = publication_data(root, role, index, observed,
        late_candidate=late, event_content=event_content)
    output = root / 'session' / 'fixtures'; output.mkdir(parents=True)
    def put(name, value, raw=False):
        return pin(output / name, value if raw else strict.json_bytes(value))
    proxy_rows = copy.deepcopy(old_proxy.rows)
    for key, suffix in (('publication', '-publish'), ('query', '-query')):
        old = record[key]['sentFrames'][0]['frame']
        new = put(spec['id'] + suffix + '-0-sent-frame.json', files.read(old), True)
        record[key]['sentFrames'][0]['frame'] = new
        for row in proxy_rows:
            if row['direction'] == 'PRODUCER_TO_RELAY' and row['exchangeLabel'] == spec['id'] + suffix:
                row['frame'] = new
    lines, phases, context = [], [], None
    outcomes = {}
    proxy_prefix = 0
    def phase(name, **fields):
        row = dict(schema='e02-transport-query-phase-v2', sequence=len(phases) + 1,
            utc='2026-10-26T00:00:00.000Z', monotonicNanoseconds=str(len(phases) + 1), phase=name,
            profileId=wire.PROFILE, windowId=wire.WINDOWS[role], ordinaryRole=role,
            observedAttempt=copy.deepcopy(context), **fields)
        phases.append(row); lines.append(strict.json_bytes(row) + b'\n'); return row
    def guard(label):
        phase('GUARD_ENTRY', label=label); phase('GUARD_EXIT', label=label, ok=True, error=None)
    def state():
        phase_raw = b''.join(lines)
        raw_proxy = b''.join(strict.json_bytes(r) + b'\n' for r in proxy_rows[:proxy_prefix])
        last = lines[-1]; pcount, rcount = len(phase_raw), len(raw_proxy)
        return dict(schema='e02-minimum-observer-state-v2',
            budget=dict(schema='e02-minimum-aggregate-capture-budget-v2', limit=observer.LIMIT,
                intendedTotalBytes=pcount + rcount, acknowledgedTotalBytes=pcount + rcount,
                streams=dict(phase=dict(intended=pcount, acknowledged=pcount), proxy=dict(intended=rcount, acknowledged=rcount)),
                poisoned=False, firstError=None, physicalBytes=None,
                physicalMeaning='ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION',
                lastAttempt=dict(stream='phase', intendedBytes=len(last), writeInvoked=True, reportedCount=len(last),
                    acknowledgedBytes=len(last), acknowledgedPrefixSha256=hashlib.sha256(last).hexdigest(), physicalBytes=None, error=None)),
            phase=dict(sequence=len(phases), intendedTotalBytes=pcount, acknowledgedTotalBytes=pcount,
                physicalBytes=None, physicalMeaning='NOT_INDEPENDENTLY_MEASURED_ACKNOWLEDGED_PREFIX_IS_NOT_PHYSICAL_ATTESTATION',
                poisoned=False, firstError=None, lastAttempt=dict(sequence=len(phases), phase=phases[-1]['phase'],
                    intendedBytes=len(last), writeInvoked=True, reportedCount=len(last), acknowledgedBytes=len(last),
                    acknowledgedPrefixBase64=base64.b64encode(last).decode(), physicalBytes=None, error=None)))
    first = None
    for row in proxy_rows:
        direction = row['direction']
        if direction == 'PUBLICATION_INTENT':
            first = len(phases) + 1; guard('original-unlabeled'); context = record['attempt']
        if direction == 'OPEN':
            phase('PROXY_CONNECTION_CALLBACK_ENTRY', nextConnection=row['connection']); guard('proxy:connection')
        if direction in ('APP_TO_RELAY', 'RELAY_TO_APP'):
            origin = 'APP' if direction == 'APP_TO_RELAY' else 'RELAY'
            phase('PROXY_RAW_CALLBACK_ENTRY', connection=row['connection'], origin=origin, rawBase64=row['rawBase64'], binary=False)
            guard('proxy:app-message' if origin == 'APP' else 'proxy:upstream-message')
            proxy_prefix = row['sequence']
            target = 'RELAY' if origin == 'APP' else 'APP'
            fields = dict(connection=row['connection'], target=target,
                bufferHash=hashlib.sha256(wire.decode64(row['rawBase64'])).hexdigest())
            if target == 'APP': fields['sourceSequence'] = row['sequence']
            guard('proxy:app-before-upstream-send' if target == 'RELAY' else 'proxy:before-app-send')
            phase('PROXY_SEND_INVOKE_ENTRY', **fields, bytes=len(wire.decode64(row['rawBase64'])))
            phase('PROXY_SEND_INVOKE_RETURNED', **fields)
            if target == 'RELAY':
                phase('PROXY_SEND_CALLBACK_ENTRY', **fields, error=None)
                phase('PROXY_SEND_CALLBACK_COMPLETE', **fields)
        if direction == 'PRODUCER_TO_RELAY':
            label = row['exchangeLabel']; raw = wire.decode64(row['rawBase64']); event_id = wire.frame(raw)[1].get('id') if wire.frame(raw)[0] == 'EVENT' else None
            guard('exchange:' + label + ':exchange-entry'); phase('EXCHANGE_START', label=label)
            phase('TIMER_ARMED', label=label, timeoutMilliseconds=10000)
            phase('SOCKET_OPEN_CALLBACK_ENTRY', label=label); guard('exchange:' + label + ':socket-open')
            guard('exchange:' + label + ':send-before'); phase('SEND_INTENT', label=label, eventId=event_id, rawBase64=row['rawBase64'])
            proxy_prefix = row['sequence']
            phase('SEND_INVOKE_ENTRY', label=label, eventId=event_id)
            phase('SEND_INVOKE_RETURNED', label=label, eventId=event_id)
            phase('SEND_CALLBACK_ENTRY', label=label, eventId=event_id, error=None)
            guard('exchange:' + label + ':send-callback'); phase('SEND_CALLBACK_GUARD_PASSED', label=label, eventId=event_id)
        elif direction == 'RELAY_TO_PRODUCER':
            label = row['exchangeLabel']
            phase('RAW_BACKEND_CALLBACK_ENTRY', label=label, rawBase64=row['rawBase64']); guard('exchange:' + label + ':backend-message')
            proxy_prefix = row['sequence']
            phase('BACKEND_MESSAGE_GUARD_PASSED', label=label, messageType=wire.frame(wire.decode64(row['rawBase64']))[0])
            key = 'query' if label.endswith('-query') else 'publication'
            if key == 'publication' or wire.frame(wire.decode64(row['rawBase64']))[0] == 'EOSE':
                result = record[key]
                phase('EXCHANGE_RESOLVED', label=label, elapsedNanoseconds=result['elapsedNanoseconds'], error=None)
                outcomes[label] = dict(label=label, **copy.deepcopy(result), error=None, secondaryRetentionErrors=[], observer=state())
        elif direction == 'APP_SOCKET_SEND_COMPLETE':
            source = proxy_rows[row['sourceSequence'] - 1]
            phase('PROXY_SEND_CALLBACK_ENTRY', connection=row['connection'], target='APP',
                bufferHash=hashlib.sha256(wire.decode64(source['rawBase64'])).hexdigest(),
                sourceSequence=row['sourceSequence'], error=None)
            guard('proxy:app-send-callback'); proxy_prefix = row['sequence']
            phase('PROXY_SEND_CALLBACK_COMPLETE', connection=row['connection'], target='APP',
                bufferHash=hashlib.sha256(wire.decode64(source['rawBase64'])).hexdigest(),
                sourceSequence=row['sourceSequence'], sentSequence=row['sequence'])
        proxy_prefix = row['sequence']
    guard('original-unlabeled')
    record['observation'] = dict(schema='e02-minimum-stage-observation-range-v2', phaseStartSequence=first,
        phaseEndSequence=len(phases), proxyEndSequence=len(proxy_rows), observer=state(),
        phaseTracePath='/session/fixtures/phase-trace.jsonl', proxyCapturePath='/session/fixtures/capture.jsonl',
        streamPins='FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS')
    proxy_pin = put('capture.jsonl', b''.join(strict.json_bytes(r) + b'\n' for r in proxy_rows), True)
    phase_pin = put('phase-trace.jsonl', b''.join(lines), True)
    for label, outcome in outcomes.items(): put(label + '-outcome.json', outcome)
    def members():
        return [dict(path=str(p), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(output.iterdir())]
    window = dict(outputRoot=str(root), profileId=wire.PROFILE, windowId=wire.WINDOWS[role], ordinaryRole=role,
        proxy=proxy_pin, phase=phase_pin, graphFiles=members())
    return files, window, wire.Proxy(files, proxy_pin), record, expected, spec, role


class ObserverControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nbdp-consumer3-observer-model-')
        self.root = Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def inspect(self, data):
        files, window, proxy, record, expected, spec, role = data
        wire.publication(files, proxy, record, expected, spec, role)
        trace = observer.Trace(files, window, proxy); trace.stage(record)
        return trace

    def test_positive_integrated_publication_observer_whole_streams(self):
        self.inspect(graph(self.root))

    def test_positive_archive_identical_query_observer(self):
        self.inspect(graph(self.root, 'archive', 1, False))

    def test_positive_archive_fresh_wrap_delivery_observer(self):
        self.inspect(graph(self.root, 'archive', 2, True))

    def test_positive_late_raw_callback_history_is_kept(self):
        self.inspect(graph(self.root, 'archive', 1, False, True))

    def mutate_stage(self, mutate):
        data = graph(self.root); mutate(data[3]['observation'])
        with self.assertRaises((strict.Refusal, KeyError, TypeError)): self.inspect(data)

    def test_poisoned_budget_refused(self): self.mutate_stage(lambda v: v['observer']['budget'].update(poisoned=True))
    def test_poisoned_phase_refused(self): self.mutate_stage(lambda v: v['observer']['phase'].update(poisoned=True))
    def test_first_shared_fault_refused(self): self.mutate_stage(lambda v: v['observer']['budget'].update(firstError='SHORT_CAPTURE_WRITE'))
    def test_first_phase_fault_refused(self): self.mutate_stage(lambda v: v['observer']['phase'].update(firstError='SHORT_PHASE_WRITE'))
    def test_two_separate_capture_limits_refused(self): self.mutate_stage(lambda v: v['observer']['budget'].update(limit=observer.LIMIT * 2))
    def test_partial_reported_write_count_refused(self): self.mutate_stage(lambda v: v['observer']['phase']['lastAttempt'].update(reportedCount=1))
    def test_unknown_write_count_refused(self): self.mutate_stage(lambda v: v['observer']['budget']['lastAttempt'].update(reportedCount=None))
    def test_physical_attestation_invention_refused(self): self.mutate_stage(lambda v: v['observer']['budget'].update(physicalBytes=1))
    def test_mutable_stage_stream_pins_refused(self): self.mutate_stage(lambda v: v.update(streamPins='STAGE_COPY'))
    def test_cross_window_phase_path_refused(self): self.mutate_stage(lambda v: v.update(phaseTracePath='/session/other/phase-trace.jsonl'))
    def test_stage_phase_prefix_drift_refused(self): self.mutate_stage(lambda v: v.update(phaseEndSequence=v['phaseEndSequence'] - 1))
    def test_proxy_prefix_drift_refused(self): self.mutate_stage(lambda v: v.update(proxyEndSequence=v['proxyEndSequence'] - 1))
    def test_stage_start_after_exchange_refused(self): self.mutate_stage(lambda v: v.update(phaseStartSequence=v['phaseEndSequence']))
    def test_extra_stage_field_refused(self): self.mutate_stage(lambda v: v.update(untrusted=True))
    def test_shared_stream_sum_drift_refused(self): self.mutate_stage(lambda v: v['observer']['budget']['streams']['proxy'].update(acknowledged=0))
    def test_wrong_prefix_hash_refused(self): self.mutate_stage(lambda v: v['observer']['budget']['lastAttempt'].update(acknowledgedPrefixSha256='0' * 64))

    def rewrite(self, data, path, value, jsonl=False):
        raw = b''.join(strict.json_bytes(r) + b'\n' for r in value) if jsonl else strict.json_bytes(value)
        path.write_bytes(raw)
        descriptor = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        window = data[1]
        window['graphFiles'] = [descriptor if p['path'] == str(path) else p for p in window['graphFiles']]
        if window['phase']['path'] == str(path): window['phase'] = descriptor

    def change_phases(self, mutate):
        data = graph(self.root); path = Path(data[1]['phase']['path'])
        rows = [strict.loads(line) for line in path.read_bytes().splitlines()]; mutate(rows)
        for i, row in enumerate(rows, 1): row['sequence'] = i
        self.rewrite(data, path, rows, True)
        with self.assertRaises(strict.Refusal): self.inspect(data)

    def test_old_profile_phase_refused(self): self.change_phases(lambda rows: rows[0].update(profileId='e02-ordinary-minimum-rs-two-role-v1'))
    def test_unknown_phase_refused(self): self.change_phases(lambda rows: rows[-1].update(phase='UNREVIEWED_PHASE'))
    def test_monotonic_backwards_refused(self): self.change_phases(lambda rows: rows[-1].update(monotonicNanoseconds='0'))
    def test_unqualified_late_guard_failure_refused(self): self.change_phases(lambda rows: rows[-1].update(ok=False, error='EXPIRED_LEASE'))
    def test_missing_app_callback_phase_refused(self): self.change_phases(lambda rows: rows.__setitem__(slice(None), [r for r in rows if r['phase'] != 'PROXY_SEND_CALLBACK_COMPLETE' or r['target'] != 'APP']))
    def test_proxy_complete_without_invoke_refused(self): self.change_phases(lambda rows: rows.__setitem__(slice(None), [r for r in rows if r['phase'] != 'PROXY_SEND_INVOKE_ENTRY']))

    def test_omitted_outcome_member_refused(self):
        data = graph(self.root)
        data[1]['graphFiles'] = [p for p in data[1]['graphFiles'] if not p['path'].endswith('-query-outcome.json')]
        with self.assertRaises(strict.Refusal): self.inspect(data)

    def test_outcome_retention_failure_refused(self):
        data = graph(self.root); path = self.root / 'session/fixtures/incoming-business-query-outcome.json'
        value = strict.loads(path.read_bytes()); value['secondaryRetentionErrors'] = [{'stage': 'write', 'error': 'SINK_FAILED'}]
        self.rewrite(data, path, value)
        with self.assertRaises(strict.Refusal): self.inspect(data)

    def test_outcome_poisoned_state_refused(self):
        data = graph(self.root); path = self.root / 'session/fixtures/incoming-business-query-outcome.json'
        value = strict.loads(path.read_bytes()); value['observer']['budget']['poisoned'] = True
        self.rewrite(data, path, value)
        with self.assertRaises(strict.Refusal): self.inspect(data)

    def test_unhealthy_final_state_refused(self):
        data = graph(self.root); path = self.root / 'session/fixtures/observer-final-state.json'
        descriptor = pin(path, strict.json_bytes(dict(observer=data[3]['observation']['observer'], error='FIRST_FAULT', secondaryErrors=[])))
        data[1]['graphFiles'].append(descriptor)
        with self.assertRaises(strict.Refusal): self.inspect(data)

    def test_world_readable_observer_stream_refused(self):
        data = graph(self.root); Path(data[1]['phase']['path']).chmod(0o644)
        with self.assertRaises(strict.Refusal): self.inspect(data)

    def reordered_send(self, order):
        data = graph(self.root); path = Path(data[1]['phase']['path'])
        rows = [strict.loads(line) for line in path.read_bytes().splitlines()]
        label = 'incoming-business-publish'
        start = next(i for i, row in enumerate(rows) if row['phase'] == 'SEND_INVOKE_ENTRY' and row['label'] == label)
        original = rows[start:start + 6]
        self.assertEqual([r['phase'] for r in original], ['SEND_INVOKE_ENTRY', 'SEND_INVOKE_RETURNED',
            'SEND_CALLBACK_ENTRY', 'GUARD_ENTRY', 'GUARD_EXIT', 'SEND_CALLBACK_GUARD_PASSED'])
        rows[start:start + 6] = [original[i] for i in order]
        for i, row in enumerate(rows, 1): row['sequence'] = i; row['monotonicNanoseconds'] = str(i)
        self.rewrite(data, path, rows, True)
        return data

    def test_send_callback_before_invoke_refused(self):
        with self.assertRaisesRegex(strict.Refusal, 'SEND_INVOKE_CALLBACK_GUARD_ORDER'):
            self.inspect(self.reordered_send([2, 3, 4, 5, 0, 1]))

    def test_guard_passed_before_callback_refused(self):
        with self.assertRaisesRegex(strict.Refusal, 'SEND_INVOKE_CALLBACK_GUARD_ORDER'):
            self.inspect(self.reordered_send([0, 1, 5, 2, 3, 4]))

    def test_guard_passed_before_original_guard_pair_refused(self):
        with self.assertRaisesRegex(strict.Refusal, 'SEND_PASSED_AFTER_ORIGINAL_GUARD_PAIR'):
            self.inspect(self.reordered_send([0, 1, 2, 5, 3, 4]))

    def test_return_before_invoke_refused(self):
        with self.assertRaisesRegex(strict.Refusal, 'SEND_RETURN_AFTER_INVOKE'):
            self.inspect(self.reordered_send([1, 0, 2, 3, 4, 5]))

    def test_valid_callback_before_send_invoke_returned_is_retained(self):
        self.inspect(self.reordered_send([0, 2, 3, 4, 5, 1]))


if __name__ == '__main__': unittest.main(verbosity=2)
