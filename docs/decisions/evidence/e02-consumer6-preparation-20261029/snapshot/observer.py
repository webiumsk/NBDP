"""Producer4 asynchronous observation DATA joins. No clocks, sockets, subprocess or writes.

The two retained streams are final whole-window files. A stage/state only binds
a prefix; callback-time context never replaces the original wire generations.
Acknowledged write counts are checked DATA, not physical-write attestation.
"""
from datetime import datetime
import hashlib
from pathlib import Path
import re

from strict import closed, equal, hx, integer, need, same, text
import wire
from async_guard import ALLOCATION, PROOF_LIMIT, FIELDS as GUARD_FIELDS, GuardTrace

LIMIT = PROOF_LIMIT
PROXY_GUARD_LABELS = frozenset('proxy:' + name for name in (
    'connection', 'app-message', 'app-before-upstream-send', 'upstream-open',
    'pending-before-upstream-send', 'upstream-message', 'before-app-send', 'app-send-callback'))
COMMON = 'schema sequence utc monotonicNanoseconds phase profileId windowId ordinaryRole observedAttempt'
FIELDS = {
    'GUARD_ENTRY': 'label', 'GUARD_EXIT': 'label ok error',
    'EXCHANGE_START': 'label', 'TIMER_ARMED': 'label timeoutMilliseconds',
    'SEND_INTENT': 'label eventId rawBase64',
    'SEND_INVOKE_ENTRY': 'label eventId', 'SEND_INVOKE_RETURNED': 'label eventId',
    'SEND_CALLBACK_ENTRY': 'label eventId error', 'SEND_CALLBACK_GUARD_PASSED': 'label eventId',
    'SOCKET_OPEN_CALLBACK_ENTRY': 'label', 'RAW_BACKEND_CALLBACK_ENTRY': 'label rawBase64',
    'BACKEND_MESSAGE_GUARD_PASSED': 'label messageType',
    'SOCKET_ERROR_CALLBACK_ENTRY': 'label error', 'SOCKET_CLOSE_CALLBACK_ENTRY': 'label',
    'TIMER_FIRED': 'label', 'EXCHANGE_RESOLVED': 'label elapsedNanoseconds error',
    'EXCHANGE_REJECTED': 'label elapsedNanoseconds error',
    'PROXY_CONNECTION_CALLBACK_ENTRY': 'nextConnection',
    'PROXY_SOCKET_OPEN_CALLBACK_ENTRY': 'connection origin',
    'PROXY_RAW_CALLBACK_ENTRY': 'connection origin rawBase64 binary',
    'PROXY_SEND_INVOKE_ENTRY': 'connection target bufferHash',
    'PROXY_SEND_INVOKE_RETURNED': 'connection target bufferHash',
    'PROXY_SEND_CALLBACK_ENTRY': 'connection target bufferHash error',
    'PROXY_SEND_CALLBACK_COMPLETE': 'connection target bufferHash',
    'PROXY_SOCKET_ERROR_CALLBACK_ENTRY': 'connection origin error',
    'PROXY_SOCKET_CLOSE_CALLBACK_ENTRY': 'connection origin',
}


def account_state(value,limit):
    closed(value,'limit chargedBytes intendedBytes poisoned firstError')
    equal(value['limit'],limit);equal(value['poisoned'],False);equal(value['firstError'],None)
    integer(value['chargedBytes'],0,limit);equal(value['chargedBytes'],value['intendedBytes'])


def raw_lines(files, pin):
    raw = files.read(pin, LIMIT)
    actual = files.resolved(pin)
    equal(Path(actual['path']).stat().st_mode & 0o777, 0o600, 'PRIVATE_RAW_OBSERVER_STREAM')
    need(raw and raw.endswith(b'\n'), 'COMPLETE_OBSERVER_STREAM')
    chunks = raw.splitlines(keepends=True)
    need(len(chunks) <= 262144 and all(c.endswith(b'\n') for c in chunks), 'OBSERVER_ROWS_BOUND')
    return raw, chunks


def healthy_state(value, phase_lines, proxy_lines, phase_end, proxy_end, last_phase=True):
    """Check a healthy emitted prefix snapshot against exact retained line bytes."""
    closed(value, 'schema budget phase allocation serviceDiagnostics serviceHeaderPrepaidBytes'); equal(value['schema'], 'e02-minimum-observer-state-v3')
    equal(value['allocation'], ALLOCATION);equal(value['serviceHeaderPrepaidBytes'],4096)
    account_state(value['serviceDiagnostics'],4096)
    integer(phase_end, 1, len(phase_lines)); integer(proxy_end, 0, len(proxy_lines))
    phase_raw = b''.join(phase_lines[:phase_end]); proxy_raw = b''.join(proxy_lines[:proxy_end])
    p, b = value['phase'], value['budget']
    closed(p, 'sequence intendedTotalBytes acknowledgedTotalBytes physicalBytes physicalMeaning poisoned firstError lastAttempt')
    closed(b, 'schema limit intendedTotalBytes acknowledgedTotalBytes streams poisoned firstError physicalBytes physicalMeaning lastAttempt allocationAccount')
    account_state(b['allocationAccount'],PROOF_LIMIT)
    equal(b['schema'], 'e02-minimum-aggregate-capture-budget-v3'); equal(b['limit'], LIMIT)
    for state in (p, b):
        equal(state['poisoned'], False); equal(state['firstError'], None); equal(state['physicalBytes'], None)
        integer(state['intendedTotalBytes'], 0, LIMIT); integer(state['acknowledgedTotalBytes'], 0, LIMIT)
        equal(state['intendedTotalBytes'], state['acknowledgedTotalBytes'])
    equal(p['physicalMeaning'], 'NOT_INDEPENDENTLY_MEASURED_ACKNOWLEDGED_PREFIX_IS_NOT_PHYSICAL_ATTESTATION')
    equal(b['physicalMeaning'], 'ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION')
    equal(p['sequence'], phase_end); equal(p['acknowledgedTotalBytes'], len(phase_raw))
    equal(b['acknowledgedTotalBytes'], len(phase_raw) + len(proxy_raw))
    need(b['allocationAccount']['chargedBytes']>=b['intendedTotalBytes'],'SERVICE_ACCOUNT_COVERS_BOTH_STREAMS')
    equal(b['streams'], {'phase': {'intended': len(phase_raw), 'acknowledged': len(phase_raw)},
                         'proxy': {'intended': len(proxy_raw), 'acknowledged': len(proxy_raw)}})
    a = p['lastAttempt']
    closed(a, 'sequence phase intendedBytes writeInvoked reportedCount acknowledgedBytes acknowledgedPrefixBase64 physicalBytes error')
    equal(a['sequence'], phase_end)
    from strict import loads
    equal(a['phase'], loads(phase_lines[phase_end - 1])['phase'])
    for key in ('intendedBytes', 'reportedCount', 'acknowledgedBytes'): equal(a[key], len(phase_lines[phase_end - 1]))
    equal(wire.decode64(a['acknowledgedPrefixBase64']), phase_lines[phase_end - 1])
    equal(a['writeInvoked'], True); equal(a['physicalBytes'], None); equal(a['error'], None)
    a = b['lastAttempt']
    closed(a, 'stream intendedBytes writeInvoked reportedCount acknowledgedBytes acknowledgedPrefixSha256 physicalBytes error')
    need(a['stream'] in ('phase', 'proxy'), 'CLOSED_LAST_CAPTURE_STREAM')
    if last_phase: equal(a['stream'], 'phase')
    lines = phase_lines[:phase_end] if a['stream'] == 'phase' else proxy_lines[:proxy_end]
    need(lines, 'LAST_CAPTURE_ROW_EXISTS')
    for key in ('intendedBytes', 'reportedCount', 'acknowledgedBytes'): equal(a[key], len(lines[-1]))
    equal(a['acknowledgedPrefixSha256'], hashlib.sha256(lines[-1]).hexdigest())
    equal(a['writeInvoked'], True); equal(a['physicalBytes'], None); equal(a['error'], None)


class Trace:
    def __init__(self, files, window, proxy):
        self.files, self.window, self.proxy = files, window, proxy
        self.lease=files.doc(window['lease'])
        config=files.doc(window['runConfig'])
        self.helper_pin=next(p for p in config['sourceAndDependencyPins'] if Path(p['path']).name=='guard-helper.py')
        root = Path(window['outputRoot'])
        required = str(root / 'session/fixtures/phase-trace.jsonl')
        members = {p['path']: p for p in window['graphFiles']}
        need(required in members, 'FINAL_PHASE_MEMBER_REQUIRED')
        equal(window['phase'], members[required], 'FINAL_PHASE_MEMBER_PIN')
        equal(window['proxy']['path'], str(root / 'session/fixtures/capture.jsonl'), 'FINAL_PROXY_MEMBER_PATH')
        equal(window['proxy'], members[window['proxy']['path']], 'FINAL_PROXY_MEMBER_PIN')
        raw, self.phase_lines = raw_lines(files, window['phase'])
        proxy_raw, self.proxy_lines = raw_lines(files, window['proxy'])
        need(len(raw) + len(proxy_raw) <= LIMIT, 'ONE_AGGREGATE_STREAM_BOUND')
        self.rows = files.jsonl(window['phase'])
        equal(len(self.rows), len(self.phase_lines)); equal(len(proxy.rows), len(self.proxy_lines))
        labels = {'prepare-inboxes', *(s + suffix for s in wire.STAGES[window['ordinaryRole']] for suffix in ('-publish', '-query'))}
        previous = -1
        for i, row in enumerate(self.rows, 1):
            name = row.get('phase'); need(name in FIELDS or name in GUARD_FIELDS, 'CLOSED_PHASE_NAME')
            keys = COMMON + ' ' + (GUARD_FIELDS[name] if name in GUARD_FIELDS else FIELDS[name])
            if name.startswith('PROXY_SEND_'):
                if row.get('target') == 'APP': keys += ' sourceSequence'
                if name == 'PROXY_SEND_INVOKE_ENTRY': keys += ' bytes'
                if name == 'PROXY_SEND_CALLBACK_COMPLETE' and row.get('target') == 'APP': keys += ' sentSequence'
            closed(row, keys)
            equal(row['schema'], 'e02-transport-query-phase-v2'); equal(row['sequence'], i)
            equal(row['profileId'], wire.PROFILE); equal(row['windowId'], window['windowId'])
            equal(row['ordinaryRole'], window['ordinaryRole'])
            need(re.fullmatch(r'(?:0|[1-9][0-9]{0,24})', row['monotonicNanoseconds']), 'PHASE_MONOTONIC_STRING')
            now = int(row['monotonicNanoseconds']); need(now >= previous, 'PHASE_MONOTONIC_ORDER'); previous = now
            need(type(row['utc']) is str and row['utc'].endswith('Z'), 'PHASE_UTC')
            datetime.fromisoformat(row['utc'].replace('Z', '+00:00'))
            context = row['observedAttempt']
            if context is not None:
                closed(context, 'epoch stageId'); need(context['stageId'] in wire.STAGES[window['ordinaryRole']], 'PHASE_CONTEXT_STAGE')
                equal(context['epoch'], wire.STAGES[window['ordinaryRole']].index(context['stageId']) + 1)
            if 'label' in row:
                text(row['label'], 128)
                if name not in GUARD_FIELDS: need(row['label'] in labels, 'CLOSED_EXCHANGE_PHASE_LABEL')
                else:
                    exact={'owner-close','watchdog:tick','startup:plan','startup:transport-import','startup:transport-import-complete','startup:nostr-import','startup:verify-event-api','startup:ws-import','startup:streams','proxy:server-create','control:listen','control:ready','control:command','control:response',*PROXY_GUARD_LABELS,*(f'flow:original-{n:02d}' for n in range(1,16)),*(f'exchange:{label}:{point}' for label in labels for point in ('exchange-entry','constructor','socket-open','send-before','send-callback','backend-message'))}
                    need(row['label'] in exact,'CLOSED_ACTUAL_SOURCE_GUARD_LABEL')
            if 'connection' in row: integer(row['connection'], 1, 64)
            if 'nextConnection' in row: integer(row['nextConnection'], 1, 64)
            if 'rawBase64' in row: wire.decode64(row['rawBase64'])
            if 'bufferHash' in row: hx(row['bufferHash'])
            if 'eventId' in row and row['eventId'] is not None: hx(row['eventId'])
            if 'bytes' in row: integer(row['bytes'], 0, 262144)
            if 'target' in row: need(row['target'] in ('APP', 'RELAY'), 'PROXY_TARGET')
            if 'origin' in row: need(row['origin'] in ('APP', 'RELAY'), 'PROXY_ORIGIN')
            if 'binary' in row: equal(row['binary'], False)
            if 'error' in row: equal(row['error'], None, 'WHOLE_PHASE_FAILURE')
            need(name not in ('TIMER_FIRED', 'EXCHANGE_REJECTED', 'SOCKET_ERROR_CALLBACK_ENTRY',
                 'SOCKET_CLOSE_CALLBACK_ENTRY', 'PROXY_SOCKET_ERROR_CALLBACK_ENTRY'), 'WHOLE_PHASE_FAILURE')
            if name == 'TIMER_ARMED': equal(row['timeoutMilliseconds'], 10000)
            if name in ('EXCHANGE_RESOLVED', 'EXCHANGE_REJECTED'): integer(row['elapsedNanoseconds'], 0, 1800000000000)
        self.labels = labels
        self.callback_guards=set()
        self.guards=GuardTrace(self.rows,self.lease,window['lease']['sha256'],window['runId'],self.helper_pin,window['runConfig']['sha256'])
        self._whole_wire_join()
        self._proxy_send_chains()
        final = root / 'session/fixtures/observer-final-state.json'
        need(str(final) in members,'WHOLE_NORMAL_FINAL_OBSERVER_REQUIRED')
        if str(final) in members:
            value = files.doc(members[str(final)]); closed(value, 'observer snapshotTiming error secondaryErrors normalOwnedHelperClose')
            equal(value['snapshotTiming'],'BEFORE_THIS_FINAL_RECORD_WRITE');equal(value['normalOwnedHelperClose'],True)
            equal(value['error'], None); equal(value['secondaryErrors'], [])
            service_members=[d for d in window['graphFiles'] if Path(d['path']).is_relative_to(root/'session/fixtures')]
            retained_before=sum(d['bytes'] for d in service_members if d['path']!=str(final))
            charged=value['observer']['budget']['allocationAccount']['chargedBytes']
            need(retained_before<=charged and charged+members[str(final)]['bytes']<=PROOF_LIMIT,'ALL_RETAINED_SERVICE_PROOF_IN_SAME_SHARE')
            healthy_state(value['observer'], self.phase_lines, self.proxy_lines, len(self.rows), len(proxy.rows), False)

    def _whole_wire_join(self):
        """Each retained raw callback must join the corresponding original raw row."""
        backend = [(r['label'], r['rawBase64']) for r in self.rows if r['phase'] == 'RAW_BACKEND_CALLBACK_ENTRY']
        equal(backend, [(r['exchangeLabel'], r['rawBase64']) for r in self.proxy.rows if r['direction'] == 'RELAY_TO_PRODUCER'], 'WHOLE_BACKEND_RAW_PHASE_JOIN')
        sends = [(r['label'], r['rawBase64']) for r in self.rows if r['phase'] == 'SEND_INTENT']
        equal(sends, [(r['exchangeLabel'], r['rawBase64']) for r in self.proxy.rows if r['direction'] == 'PRODUCER_TO_RELAY'], 'WHOLE_SENT_PHASE_JOIN')
        for origin, direction, guard in (('APP', 'APP_TO_RELAY', 'proxy:app-message'), ('RELAY', 'RELAY_TO_APP', 'proxy:upstream-message')):
            rows = [r for r in self.rows if r['phase'] == 'PROXY_RAW_CALLBACK_ENTRY' and r['origin'] == origin]
            equal([(r['connection'], r['rawBase64']) for r in rows],
                  [(r['connection'], r['rawBase64']) for r in self.proxy.rows if r['direction'] == direction], 'WHOLE_PROXY_RAW_PHASE_JOIN')
            for row in rows: self.guard_after(row['sequence'],guard,wire.decode64(row['rawBase64']))
        for row in (r for r in self.rows if r['phase'] == 'RAW_BACKEND_CALLBACK_ENTRY'):
            label='exchange:'+row['label']+':backend-message'
            item=self.guard_after(row['sequence'],label,wire.decode64(row['rawBase64']))
            passed=[(j,r) for j,r in enumerate(self.rows) if r['phase']=='BACKEND_MESSAGE_GUARD_PASSED' and r['label']==row['label'] and item['reply']<j<item['exit']]
            need(len(passed)==1,'RAW_PARSE_FRESH_GUARD_EFFECT_REQUIRED')
            self.guards.effect(passed[0][0],label,wire.decode64(row['rawBase64']),before=row['sequence']-1)
            equal(passed[0][1]['messageType'],wire.frame(wire.decode64(row['rawBase64']))[0],'RAW_GUARD_PARSE_ORDER')
        completions = [r for r in self.rows if r['phase'] == 'PROXY_SEND_CALLBACK_COMPLETE' and r['target'] == 'APP']
        equal([(r['connection'], r['sourceSequence'], r['sentSequence']) for r in completions],
              [(r['connection'], r['sourceSequence'], r['sequence']) for r in self.proxy.rows if r['direction'] == 'APP_SOCKET_SEND_COMPLETE'], 'WHOLE_APP_CALLBACK_PHASE_JOIN')
        for row in completions:
            source = self.proxy.row(row['sourceSequence'], 'RELAY_TO_APP')
            equal(row['bufferHash'], hashlib.sha256(wire.decode64(source['rawBase64'])).hexdigest())

    def guard_after(self, sequence, label, context):
        # Callback rows may interleave; request identity/context and consumed fence
        # determine causality. Global sequence remains independent of guardSequence.
        digest=hashlib.sha256(context).hexdigest()
        matches=[item for item in self.guards.items.values() if item['entry']>=sequence
            and item['requestValue']['label']==label
            and item['requestValue']['contextSha256']==digest]
        need(matches,'CALLBACK_REQUIRES_FRESH_ASYNC_GUARD')
        item=min(matches,key=lambda x:x['entry'])
        need(item['entry'] not in self.callback_guards,'EACH_CALLBACK_HAS_ITS_OWN_FRESH_RPC');self.callback_guards.add(item['entry'])
        equal(self.rows[sequence-1]['observedAttempt'],item['entryFields']['observedAttempt'],'CALLBACK_GUARD_STAGE_CONTEXT')
        return item

    def _proxy_send_chains(self):
        pending = {}
        for row in self.rows:
            if not row['phase'].startswith('PROXY_SEND_'): continue
            key = (row['connection'], row['target'], row['bufferHash'], row.get('sourceSequence'))
            queue = pending.setdefault(key, [])
            if row['phase'] == 'PROXY_SEND_INVOKE_ENTRY':
                if row['target'] == 'APP':
                    source = self.proxy.row(row['sourceSequence'], 'RELAY_TO_APP')
                    raw = wire.decode64(source['rawBase64'])
                    equal(row['connection'], source['connection'])
                    equal(row['bytes'], len(raw)); equal(row['bufferHash'], hashlib.sha256(raw).hexdigest())
                    self.guards.effect(row['sequence']-1,'proxy:before-app-send',raw)
                queue.append({'entry': row, 'returned': False, 'callback': False, 'complete': False})
                continue
            field = {'PROXY_SEND_INVOKE_RETURNED': 'returned', 'PROXY_SEND_CALLBACK_ENTRY': 'callback',
                     'PROXY_SEND_CALLBACK_COMPLETE': 'complete'}[row['phase']]
            choices = [q for q in queue if not q[field]]
            need(choices, 'PROXY_SEND_WITHOUT_MATCHING_INVOCATION')
            item = choices[0]; item[field] = True
            if field == 'complete' and row['target']=='APP':
                source=self.proxy.row(row['sourceSequence'],'RELAY_TO_APP')
                callbacks=[r for r in self.rows if r['phase']=='PROXY_SEND_CALLBACK_ENTRY' and r['connection']==row['connection'] and r['target']=='APP' and r.get('sourceSequence')==row['sourceSequence']]
                need(len(callbacks)==1,'ONE_APP_SEND_CALLBACK')
                self.guards.effect(row['sequence']-1,'proxy:app-send-callback',wire.decode64(source['rawBase64']),before=callbacks[0]['sequence']-1)
            if field == 'complete': need(item['callback'], 'PROXY_COMPLETION_REQUIRES_SUCCESS_CALLBACK')
        need(all(q['returned'] for queue in pending.values() for q in queue), 'PROXY_SEND_RETURN_REQUIRED')

    def state(self, value, proxy_end=None):
        phase_end = value['phase']['sequence']
        if proxy_end is None:
            acknowledged = value['budget']['streams']['proxy']['acknowledged']
            total, proxy_end = 0, 0
            for line in self.proxy_lines:
                if total >= acknowledged: break
                total += len(line); proxy_end += 1
            equal(total, acknowledged, 'PROXY_PREFIX_EXACT_ROW_BOUNDARY')
        healthy_state(value, self.phase_lines, self.proxy_lines, phase_end, proxy_end)

    def exchange(self, label, result):
        start = [r for r in self.rows if r['phase'] == 'EXCHANGE_START' and r['label'] == label]
        terminal = [r for r in self.rows if r['phase'] == 'EXCHANGE_RESOLVED' and r['label'] == label]
        need(len(start) == len(terminal) == 1, 'EXACT_EXCHANGE_PHASE_SPAN')
        first, last = start[0]['sequence'], terminal[0]['sequence']; need(first < last, 'EXCHANGE_PHASE_ORDER')
        rows = [r for r in self.rows[first - 1:last] if r.get('label') == label]
        equal(sum(r['phase'] == 'TIMER_ARMED' for r in rows), 1)
        equal(sum(r['phase'] == 'SOCKET_OPEN_CALLBACK_ENTRY' for r in rows), 1)
        for sent in result['sentFrames']:
            raw = self.files.read(sent['frame']); event_id = sent['eventId']
            intent = [r for r in rows if r['phase'] == 'SEND_INTENT' and r['eventId'] == event_id]
            need(len(intent) == 1, 'EXACT_SENT_PHASE_INTENT'); equal(wire.decode64(intent[0]['rawBase64']), raw)
            equal(Path(sent['frame']['path']).name, label + '-' + str(result['sentFrames'].index(sent)) + '-sent-frame.json', 'IMMUTABLE_SENT_FRAME_PATH')
            send_phases = {}
            for name in ('SEND_INVOKE_ENTRY', 'SEND_INVOKE_RETURNED', 'SEND_CALLBACK_ENTRY', 'SEND_CALLBACK_GUARD_PASSED'):
                selected = [r for r in rows if r['phase'] == name and r['eventId'] == event_id]
                need(len(selected) == 1 and intent[0]['sequence'] < selected[0]['sequence'], 'SEND_PHASE_CALLBACK_JOIN')
                send_phases[name] = selected[0]
            callback = send_phases['SEND_CALLBACK_ENTRY']
            need(send_phases['SEND_INVOKE_ENTRY']['sequence'] < send_phases['SEND_INVOKE_RETURNED']['sequence'], 'SEND_RETURN_AFTER_INVOKE')
            need(send_phases['SEND_INVOKE_ENTRY']['sequence'] < callback['sequence']
                 < send_phases['SEND_CALLBACK_GUARD_PASSED']['sequence'], 'SEND_INVOKE_CALLBACK_GUARD_ORDER')
            self.guards.effect(send_phases['SEND_CALLBACK_GUARD_PASSED']['sequence']-1,'exchange:'+label+':send-callback',raw,before=callback['sequence']-1)
            self.guards.effect(intent[0]['sequence']-1,'exchange:'+label+':send-before',raw)
        outcome_path = str(Path(self.window['outputRoot']) / 'session/fixtures' / (label + '-outcome.json'))
        members = {p['path']: p for p in self.window['graphFiles']}; need(outcome_path in members, 'IMMUTABLE_OUTCOME_MEMBER_REQUIRED')
        outcome = self.files.doc(members[outcome_path])
        closed(outcome, 'label elapsedNanoseconds ack received eose sentFrames error secondaryRetentionErrors observer')
        equal(outcome['label'], label); equal(outcome['error'], None); equal(outcome['secondaryRetentionErrors'], [])
        for key in ('elapsedNanoseconds', 'ack', 'received', 'eose', 'sentFrames'): equal(outcome[key], result[key], 'ACTUAL_OUTCOME_RESULT_JOIN')
        equal(terminal[0]['elapsedNanoseconds'], result['elapsedNanoseconds'])
        equal(outcome['observer']['phase']['sequence'], last); self.state(outcome['observer'])
        return first, last

    def stage(self, record):
        value = record['observation']
        closed(value, 'schema phaseStartSequence phaseEndSequence proxyEndSequence observer phaseTracePath proxyCapturePath streamPins')
        equal(value['schema'], 'e02-minimum-stage-observation-range-v2')
        equal(value['phaseTracePath'], '/session/fixtures/phase-trace.jsonl')
        equal(value['proxyCapturePath'], '/session/fixtures/capture.jsonl')
        equal(value['streamPins'], 'FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS')
        first, last = value['phaseStartSequence'], value['phaseEndSequence']
        integer(first, 1, len(self.rows)); integer(last, first, len(self.rows))
        equal(value['observer']['phase']['sequence'], last); self.state(value['observer'], value['proxyEndSequence'])
        ranges = [self.exchange(record['stage']['id'] + suffix, record[key]) for suffix, key in (('-publish', 'publication'), ('-query', 'query'))]
        need(first <= ranges[0][0] < ranges[0][1] < ranges[1][0] < ranges[1][1] <= last, 'STAGE_EXCHANGE_PHASE_RANGES')
        need(value['proxyEndSequence'] >= self.files.doc(record['publicationWindow'])['closeSequence'], 'STAGE_PROXY_PREFIX_CLOSED')
        attempt = record['attempt']
        for start, end in ranges:
            equal([r['observedAttempt'] for r in self.rows[start - 1:end]], [attempt] * (end - start + 1), 'STAGE_CALLBACK_CONTEXT_JOIN')
        return first, last
