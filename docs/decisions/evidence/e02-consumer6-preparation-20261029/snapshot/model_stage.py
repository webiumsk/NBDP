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

