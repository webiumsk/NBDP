"""Minimum-profile wire, generation and native-result DATA joins; no crypto run."""
import base64
import hashlib
from strict import closed, equal, hx, integer, json_bytes, loads, need, same, text, validate_numbers

PROFILE = 'e02-ordinary-minimum-rs-two-role-v3'
A = '79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
B = 'c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5'
BUSINESS = 'e2b4accf597c65d5a3749f44551545f2be430a0ac3ddfb4cf694c9d12ae6df14'
CHAT = 'f335fb5dbee6dda9fff841581bfa552584dd56782ff100ce0912a4708f0de71f'
STAGES = {'incoming': ('incoming-business', 'incoming-ordinary-chat'),
          'archive': ('archive-business', 'archive-identical-replay', 'archive-fresh-wrap-replay')}
ACCOUNTS = {'incoming': B, 'archive': A}
WINDOWS = {'incoming': 'incoming-b', 'archive': 'archive-a'}
APP = 'ACTUAL_APP_SOCKET_FRAME'
QUERY = 'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'


def rumor(value):
    closed(value, 'id pubkey created_at kind tags content')
    hx(value['id']); equal(value['pubkey'], A); integer(value['created_at'])
    equal(value['kind'], 14); equal(value['tags'], [['p', B]])
    text(value['content'])
    digest = hashlib.sha256(json_bytes([0, A, value['created_at'], 14, value['tags'], value['content']])).hexdigest()
    equal(value['id'], digest, 'NIP01_ID')
    return value


def export(raw, expected):
    value = validate_numbers(loads(raw))
    if type(value) is dict and set(value) == set(expected) | {'sig'}:
        equal(value['sig'], '', 'ONLY_EMPTY_SIG_REPRESENTATION')
        value = {k: v for k, v in value.items() if k != 'sig'}
    rumor(value)
    equal(value, expected, 'CLIENT_INNER_MISMATCH')
    return value


def stage(role, index):
    name = STAGES[role][index]
    return dict(id=name, index=index, oracle='chat' if name == 'incoming-ordinary-chat' else 'business',
                dispatch=role == 'incoming' and index == 0,
                normalizedRole='chat' if name == 'incoming-ordinary-chat' else role,
                identicalReplay=name == 'archive-identical-replay',
                freshWrap=name != 'archive-identical-replay',
                requiresNewAppFrame=name != 'archive-identical-replay')


def signed(event, account):
    closed(event, 'id pubkey created_at kind tags content sig')
    hx(event['id']); hx(event['pubkey']); hx(event['sig'], 128)
    integer(event['created_at']); equal(event['kind'], 1059)
    equal(event['tags'], [['p', account]]); text(event['content'], 262144)
    equal(event['id'], hashlib.sha256(json_bytes([0, event['pubkey'], event['created_at'],
          1059, event['tags'], event['content']])).hexdigest(), 'OUTER_NIP01_ID')


def decode64(value):
    text(value, 349528)
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError('STRICT_BASE64') from error
    need(len(raw) <= 262144 and base64.b64encode(raw).decode() == value, 'CANONICAL_BASE64')
    return raw


def frame(raw):
    result = validate_numbers(loads(raw))
    need(type(result) is list and result and type(result[0]) is str, 'NOSTR_FRAME')
    todo = [(result, 0)]
    while todo:
        item, depth = todo.pop()
        need(depth <= 32, 'WIRE_DEPTH_BOUND')
        if type(item) is dict: todo.extend((v, depth + 1) for v in item.values())
        if type(item) is list: todo.extend((v, depth + 1) for v in item)
    return result


def generation(value, filters=False):
    closed(value, 'connection subscription requestSequence eoseSequence' + (' filters' if filters else ''))
    integer(value['connection'], 1, 64); text(value['subscription'], 262144)
    integer(value['requestSequence'], 1, 262144); integer(value['eoseSequence'], 1, 262144)
    need(value['requestSequence'] < value['eoseSequence'], 'EOSE_AFTER_REQ')
    return {k: v for k, v in value.items() if k != 'filters'}


ROW_FIELDS = {
    'OPEN': 'connection userAgent', 'APP_TO_RELAY': 'connection rawBase64',
    'RELAY_TO_APP': 'connection rawBase64 publicationGeneration publicationAttempt',
    'APP_SOCKET_SEND_COMPLETE': 'connection sourceSequence publicationGeneration publicationAttempt',
    'CLOSE': 'connection', 'PUBLICATION_GENERATION_INVALIDATED': 'connection reason gate',
    'PRODUCER_TO_RELAY': 'exchangeLabel rawBase64 frame', 'RELAY_TO_PRODUCER': 'exchangeLabel rawBase64',
    'PUBLICATION_INTENT': 'stageId eventId attempt',
    'PUBLICATION_WINDOW_CLOSED': 'stageId eventId attempt intentSequence actualNewAppFrameObserved candidateAppFrameSeen elapsedNanoseconds',
}


class Proxy:
    def __init__(self, files, descriptor):
        self.rows = files.jsonl(descriptor)
        self.frames = {}
        for i, row in enumerate(self.rows, 1):
            direction = row.get('direction')
            need(direction in ROW_FIELDS, 'PROXY_DIRECTION')
            closed(row, 'schema sequence utc direction ' + ROW_FIELDS[direction])
            equal(row['schema'], 'e02-minimum-proxy-row-v1'); equal(row['sequence'], i)
            text(row['utc'], 64)
            if 'connection' in row:
                integer(row['connection'], 1, 64)
            if 'rawBase64' in row:
                raw = decode64(row['rawBase64'])
                self.frames[i] = (raw, frame(raw))
                if direction == 'PRODUCER_TO_RELAY':
                    equal(files.read(row['frame']), raw, 'ACTUAL_BACKEND_BUFFER_CAPTURE')
            if 'publicationGeneration' in row and row['publicationGeneration'] is not None:
                generation(row['publicationGeneration'])
            if 'exchangeLabel' in row:
                import re
                need(re.fullmatch('[a-z0-9-]{1,48}', row['exchangeLabel']), 'EXCHANGE_LABEL')

    def row(self, seq, direction):
        integer(seq, 1, len(self.rows))
        row = self.rows[seq - 1]
        equal(row['direction'], direction, 'PROXY_SEQUENCE_DIRECTION')
        return row

    def gate(self, gate, event, before, until):
        gen = generation(gate, True)
        req = self.row(gen['requestSequence'], 'APP_TO_RELAY')
        eose = self.row(gen['eoseSequence'], 'RELAY_TO_APP')
        equal(req['connection'], gen['connection']); equal(eose['connection'], gen['connection'])
        reqframe = self.frames[req['sequence']][1]
        need(len(reqframe) >= 3 and reqframe[:2] == ['REQ', gen['subscription']], 'ACTUAL_APP_REQ')
        equal(reqframe[2:], gate['filters'], 'ACTUAL_FILTER_BYTES')
        equal(self.frames[eose['sequence']][1], ['EOSE', gen['subscription']], 'ACTUAL_APP_EOSE')
        need(gen['eoseSequence'] < before, 'EOSE_BEFORE_PUBLICATION')
        opens = [r for r in self.rows[:req['sequence'] - 1] if r.get('connection') == gen['connection'] and r['direction'] == 'OPEN']
        need(len(opens) == 1 and not any(r['direction'] == 'CLOSE' and r.get('connection') == gen['connection']
             for r in self.rows[opens[0]['sequence']:req['sequence']]), 'LIVE_OPEN_CONNECTION')
        need(any(type(f) is dict and type(f.get('kinds')) is list and 1059 in f['kinds']
                 and type(f.get('#p')) is list and event['tags'][0][1] in f['#p']
                 and self.matches_filter(f, event) for f in gate['filters']), 'MATCHING_ACTUAL_FILTER')
        for row in self.rows[gen['requestSequence']:until]:
            if row.get('connection') != gen['connection']:
                continue
            need(row['direction'] not in ('CLOSE', 'PUBLICATION_GENERATION_INVALIDATED'), 'STALE_GENERATION')
            pair = self.frames.get(row['sequence'])
            if pair:
                f = pair[1]
                need(not (len(f) > 1 and f[1] == gen['subscription'] and
                          ((row['direction'] == 'APP_TO_RELAY' and f[0] in ('REQ', 'CLOSE')) or
                           (row['direction'] == 'RELAY_TO_APP' and (f[0] == 'CLOSED' or
                            f[0] == 'EOSE' and row['sequence'] != gen['eoseSequence'])))), 'CHANGED_REQ_EOSE')
        return gen

    @staticmethod
    def matches_filter(f, event):
        # Preserve all actual filter constraints; unknown constraints cannot qualify.
        for key, value in f.items():
            if key == 'limit':
                integer(value, 1); continue
            if key in ('since', 'until'):
                integer(value)
                if (key == 'since' and event['created_at'] < value) or (key == 'until' and event['created_at'] > value):
                    return False
            elif key in ('ids', 'authors', 'kinds'):
                need(type(value) is list and value, 'FILTER_ARRAY')
                target = event[{'ids': 'id', 'authors': 'pubkey', 'kinds': 'kind'}[key]]
                if key == 'kinds':
                    if target not in value: return False
                elif not any(type(v) is str and target.startswith(v) for v in value): return False
            elif key.startswith('#') and len(key) == 2:
                need(type(value) is list and value, 'TAG_FILTER_ARRAY')
                if not any(len(t) > 1 and t[0] == key[1:] and t[1] in value for t in event['tags']): return False
            else:
                return False
        return True


def exchange(files, proxy, value, event, label, query=False):
    closed(value, 'ack received eose sentFrames elapsedNanoseconds')
    integer(value['elapsedNanoseconds'], 0, 1800000000000)
    sent = value['sentFrames']
    need(type(sent) is list and len(sent) == 1, 'ONE_ACTUAL_SEND')
    item = sent[0]
    closed(item, 'frame eventId messageType sendInvoked sendCallbackCompleted callbackBufferHash')
    equal(item['sendInvoked'], True); equal(item['sendCallbackCompleted'], True)
    raw = files.read(item['frame'], 262144)
    equal(hashlib.sha256(raw).hexdigest(), item['callbackBufferHash'], 'SEND_BUFFER_CALLBACK_HASH')
    actual = frame(raw)
    if query:
        equal(item['messageType'], 'REQ'); equal(item['eventId'], None)
        equal(actual, ['REQ', 'e02-owned-query', {'ids': [event['id']], 'limit': 1}])
    else:
        equal(item['messageType'], 'EVENT'); equal(item['eventId'], event['id'])
        equal(actual, ['EVENT', event])
    outgoing = [r for r in proxy.rows if r['direction'] == 'PRODUCER_TO_RELAY' and r['exchangeLabel'] == label]
    need(len(outgoing) == 1, 'ONE_BACKEND_SEND_ROW')
    equal(decode64(outgoing[0]['rawBase64']), raw)
    incoming = [proxy.frames[r['sequence']][0] for r in proxy.rows
                if r['direction'] == 'RELAY_TO_PRODUCER' and r['exchangeLabel'] == label]
    need(type(value['ack']) is list and type(value['received']) is list, 'EXCHANGE_ARRAYS')
    for reply in value['ack'] + value['received'] + ([value['eose']] if value['eose'] is not None else []):
        closed(reply, 'rawBase64 frame')
        equal(frame(decode64(reply['rawBase64'])), reply['frame'])
        need(decode64(reply['rawBase64']) in incoming, 'REPLY_IN_ACTUAL_BACKEND_CAPTURE')
    if query:
        equal(value['ack'], [])
        need(len(value['received']) == 1 and value['eose'] is not None, 'ACTUAL_QUERY_EVENT_EOSE')
        equal(value['received'][0]['frame'], ['EVENT', 'e02-owned-query', event])
        equal(value['eose']['frame'], ['EOSE', 'e02-owned-query'])
    else:
        equal(value['received'], []); equal(value['eose'], None)
        need(len(value['ack']) == 1, 'ONE_PUBLISH_ACK')
        ack = value['ack'][0]['frame']
        need(len(ack) == 4 and ack[:3] == ['OK', event['id'], True] and type(ack[3]) is str, 'ACTUAL_PUBLISH_OK')
    return raw


def normalized(value, expected, spec):
    closed(value, 'ok value decrypts')
    equal(value['ok'], True)
    equal(value['decrypts'], [1, 1], 'TWO_VALIDATED_DECRYPT_LAYERS')
    v = value['value']
    closed(v, 'rumor dispatch role' + (' envelope' if spec['oracle'] == 'business' else ''))
    equal(v['rumor'], expected); equal(v['role'], spec['normalizedRole']); equal(v['dispatch'], spec['dispatch'])
    if spec['oracle'] == 'business':
        equal(v['envelope'], validate_numbers(loads(expected['content'].encode())))
    else:
        need('envelope' not in v, 'CHAT_HAS_NO_BUSINESS_ENVELOPE')


def candidate_app_frame(value, connection, gate, event_id):
    """Frozen producer candidate presence, separate from qualified equality."""
    return (type(value) is list and len(value) >= 3 and value[0] == 'EVENT'
            and type(value[2]) is dict and value[2].get('id') == event_id
            and connection == gate['connection'] and value[1] == gate['subscription'])


def validation(files, record, event, expected, spec, origin, actual_raw, role):
    closed(record, 'schema profileId windowId stageId origin clientReceiptEstablished transport rustBinary rustSource rustInput rustStdout rustStderr rustExit rustSignal actualQueriedEvent js rust clientRetention')
    equal(record['schema'], 'e02-minimum-validated-wire-record-v2')
    equal(record['profileId'], PROFILE); equal(record['windowId'], WINDOWS[role]); equal(record['stageId'], spec['id'])
    equal(record['origin'], origin); equal(record['clientReceiptEstablished'], origin == APP)
    equal(record['rustExit'], 0); equal(record['rustSignal'], None)
    equal(record['actualQueriedEvent'], event)
    equal(record['clientRetention'], 'NOT_ESTABLISHED_BY_TRANSPORT_VALIDATION')
    transport = files.doc(record['transport'])
    closed(transport, 'schema frame wire jsRequest rustRequest jsResult rustResult')
    equal(transport['schema'], 'e02-minimum-transport-v2')
    equal(files.read(transport['frame']), actual_raw, 'VALIDATED_ACTUAL_FRAME')
    wire = files.read(transport['wire']); equal(frame(actual_raw)[2], validate_numbers(loads(wire)))
    request = dict(op='validate', wire=wire.decode('utf-8', 'strict'), secret=('2' if role == 'incoming' else '1').zfill(64), role=role, expectedSender=A)
    equal(files.doc(transport['jsRequest']), request); equal(files.doc(transport['rustRequest']), request)
    equal(files.doc(transport['jsResult']), record['js']); equal(files.doc(transport['rustResult']), record['rust'])
    equal(record['js'], record['rust']); normalized(record['js'], expected, spec)
    requests = files.jsonl(record['rustInput'], 2)
    equal(requests, [{'op': 'source'}, request], 'EXACT_NATIVE_INPUT')
    replies = files.jsonl(record['rustStdout'], 2)
    need(len(replies) == 2, 'EXACT_NATIVE_REPLY_COUNT')
    equal(replies[0], {'ok': True, 'value': files.read(record['rustSource']).decode('utf-8', 'strict')})
    closed(replies[1], 'ok value')
    equal(replies[1]['ok'], True, 'SUCCESSFUL_NATIVE_RPC_ENVELOPE')
    equal(replies[1]['value'], record['rust'], 'NATIVE_RPC_NORMALIZED_VALUE')
    equal(files.read(record['rustStderr']), b'')
    files.read(record['rustBinary'], 67108864)


def publication(files, proxy, record, expected, spec, role):
    closed(record, 'schema profileId windowId stage attempt intent publicationWindow gate publication query event actualNewAppFrameObserved delivery validation producerValidation clientRetention validationOrigin replayLimit observation')
    need(type(record['observation']) is dict, 'OBSERVATION_RANGE_REQUIRED')
    equal(record['schema'], 'e02-minimum-stage-publication-v2'); equal(record['profileId'], PROFILE)
    equal(record['windowId'], WINDOWS[role]); equal(record['stage'], spec)
    attempt = {'epoch': spec['index'] + 1, 'stageId': spec['id']}
    equal(record['attempt'], attempt)
    event = record['event']; signed(event, ACCOUNTS[role])
    observed = record['actualNewAppFrameObserved']; need(type(observed) is bool, 'OBSERVED_BOOL')
    need(observed or not spec['requiresNewAppFrame'], 'REQUIRED_NEW_APP_FRAME')
    origin = APP if observed else QUERY; equal(record['validationOrigin'], origin)
    window = files.doc(record['publicationWindow'])
    closed(window, 'schema profileId windowId stageId eventId attempt intentSequence closeSequence actualNewAppFrameObserved candidateAppFrameSeen elapsedNanoseconds clock origin')
    equal(window['schema'], 'e02-minimum-publication-window-v2'); equal(window['profileId'], PROFILE)
    equal(window['windowId'], WINDOWS[role]); equal(window['stageId'], spec['id']); equal(window['eventId'], event['id'])
    equal(window['attempt'], attempt); equal(window['origin'], origin); equal(window['actualNewAppFrameObserved'], observed)
    equal(window['candidateAppFrameSeen'], observed); integer(window['elapsedNanoseconds'], 0, 1800000000000)
    equal(window['clock'], 'NODE_PROCESS_HRTIME_MONOTONIC')
    first, last = window['intentSequence'], window['closeSequence']
    need(1 <= first < last <= len(proxy.rows), 'SEALED_PUBLICATION_INTERVAL')
    start = proxy.row(first, 'PUBLICATION_INTENT'); end = proxy.row(last, 'PUBLICATION_WINDOW_CLOSED')
    for row in (start, end):
        equal(row['stageId'], spec['id']); equal(row['eventId'], event['id']); equal(row['attempt'], attempt)
    for key in ('intentSequence', 'actualNewAppFrameObserved', 'candidateAppFrameSeen', 'elapsedNanoseconds'):
        equal(end[key], window[key])
    intent = files.doc(record['intent'])
    closed(intent, 'schema profileId windowId stage attempt intentSequence prepared gate issuedUTC')
    equal(intent['schema'], 'e02-minimum-publish-intent-v2'); equal(intent['profileId'], PROFILE)
    equal(intent['windowId'], WINDOWS[role]); equal(intent['stage'], spec); equal(intent['attempt'], attempt)
    equal(intent['intentSequence'], first); equal(intent['gate'], record['gate'])
    prepared = files.doc(intent['prepared'])
    equal(prepared['rumors'][spec['oracle']], expected)
    equal(prepared['events'][spec['index']], event)
    gen = proxy.gate(record['gate'], event, first, last)
    sent = exchange(files, proxy, record['publication'], event, spec['id'] + '-publish')
    exchange(files, proxy, record['query'], event, spec['id'] + '-query', True)
    candidates = [r for r in proxy.rows[first:last - 1] if r['direction'] == 'RELAY_TO_APP'
                  and candidate_app_frame(proxy.frames[r['sequence']][1], r['connection'], gen, event['id'])]
    if observed:
        d = record['delivery']
        closed(d, 'connection subscription rowSequence sentSequence forwardGeneration completionGeneration forwardAttempt completionAttempt')
        equal(d['connection'], gen['connection']); equal(d['subscription'], gen['subscription'])
        for k in ('forwardGeneration', 'completionGeneration'): equal(d[k], gen)
        for k in ('forwardAttempt', 'completionAttempt'): equal(d[k], attempt)
        delivery = proxy.row(d['rowSequence'], 'RELAY_TO_APP')
        callback = proxy.row(d['sentSequence'], 'APP_SOCKET_SEND_COMPLETE')
        need(delivery in candidates and first < d['rowSequence'] < d['sentSequence'] < last, 'CURRENT_DELIVERY_CUSTODY')
        equal(proxy.frames[d['rowSequence']][1], ['EVENT', gen['subscription'], event], 'QUALIFIED_WHOLE_EVENT_EQUALITY')
        equal(callback['sourceSequence'], d['rowSequence'])
        for row in (delivery, callback):
            equal(row['connection'], gen['connection']); equal(row['publicationGeneration'], gen)
            equal(row['publicationAttempt'], attempt)
        actual_raw = proxy.frames[d['rowSequence']][0]
        equal(record['replayLimit'], None)
    else:
        equal(record['delivery'], None); equal(candidates, [], 'NO_CACHED_OR_UNCOMPLETED_FRAME')
        need(spec['identicalReplay'] and type(record['replayLimit']) is str, 'HONEST_QUERY_ONLY_LIMIT')
        actual_raw = decode64(record['query']['received'][0]['rawBase64'])
    closed(record['validation'], 'transport validation')
    v = files.doc(record['validation']['validation'])
    equal(v['transport'], record['validation']['transport'])
    validation(files, v, event, expected, spec, origin, actual_raw, role)
    producer = files.doc(record['producerValidation'])
    closed(producer, 'schema stageId actualPublishedEvent result meaning')
    equal(producer['schema'], 'e02-minimum-producer-validation-v2'); equal(producer['stageId'], spec['id'])
    equal(producer['actualPublishedEvent'], event); normalized(producer['result'], expected, spec)
    equal(record['clientRetention'], 'UNVERIFIED_REQUIRES_FRESH_CLIENT_SELECTION_EXPORT')
    return event, sent
