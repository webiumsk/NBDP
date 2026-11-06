"""Standalone minimum ordinary-client evidence consumer; never canonical E02 PASS.

Invocation reads only bounded explicitly pinned DATA. It does not execute a
producer, SDK, Android, crypto, network, subprocess, tests or evidence payloads.
"""
import argparse
import hashlib
import ipaddress
from pathlib import Path
import re
import stat
import sys

# Direct-script execution under -I is supported without trusting cwd/PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from strict import Files, I64, Refusal, closed, equal, hx, integer, json_bytes, need, pin_shape, same, text
import gui
import wire
import observer
from witness import Origin, actors, cleanup_check, commands, lease_check, ownership

PRODUCER_SHA = 'ef91dc64189d7c47a4b4539c4dacd93a4c5c760da8f98bf1b203040bba6eeffd'
CONTRACT_SHA = '7fd7b71898584b4b9f90fbe9ae4601df0d1b9f3dfdc995012dfd63824fba9bfc'
ADOPTION_SHA = '2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287'
ACTUAL35_SHA = 'aedd45eb01e6120856a8d97e8fa9811e750531ea5c3f23df8b65d302b8a8bd6c'
CONFIG_KEYS = 'runtimeImage relayImage sdkRoot amethystApk helperApk schema scope profileId ordinaryRole windowId account peer runId originalLeaseSeconds sourceAndDependencyPins sdkInventory guardBundleInventory guardBundleRoot relayConfig state canonicalE02'
WINDOW_KEYS = 'schema profileId ordinaryRole windowId runId outputRoot authors operators sourceSubject supervisorSource runConfig runRelease resource sourceControls outer lease driver supervisor commands ui proxy phase readOnlyMountBindings graphFiles excludedFiles sourcePolicyObservations'
DRIVER_KEYS = 'schema profileId windowId ordinaryRole runId runConfig runRelease executionState accountIdentityGUI expectedAccountPubkey accountIdentityQualification torConfigurationGUI environmentAnrEvidence allUICaptures fixtureCalls observations limits canonicalE02Changed'
OBS_KEYS = 'id state selection uiPng uiXml rawClientRumor clipboardClear visibleMatchingTextNodeCount duplicateObservation expectedRumor publication actualNewAppFrameObserved originalGuestToHostBindings subscriptionStatus subscriptionStatusReply subscriptionStatusCall subscriptionStatusCommand custodySegment'


def external(files, path, sha):
    hx(sha)
    p = Path(path)
    descriptor = dict(path=str(p), bytes=p.stat().st_size, sha256=sha)
    files.read(descriptor)
    return descriptor


def provenance(files, candidate, history, origin_value):
    forbidden = actors(candidate['authors']) | actors(candidate['operators'])
    need(type(history['attempts']) is list and 2 <= len(history['attempts']) <= 128, 'WHOLE_ATTEMPT_HISTORY_BOUND')
    equal([a['subject'] for a in history['attempts']], origin_value['attemptSubjects'], 'EXTERNALLY_CLOSED_ATTEMPT_INVENTORY')
    equal(history['legacyContexts'], origin_value['legacyContexts'], 'LEGACY_HISTORY_OMISSION')
    attempt_docs, seen = [], set()
    for row in history['attempts']:
        closed(row, 'subject disposition classification reason')
        need(row['disposition'] in ('CONTRIBUTE_WHOLE_WINDOW', 'NO_CONTRIBUTION'), 'ATTEMPT_DISPOSITION')
        text(row['classification'], 128); text(row['reason'], 8192)
        attempt = files.doc(row['subject'])
        closed(attempt, 'schema profileId attemptId ordinaryRole runId windowSubject rawOutcome authors operators sourceSubject outcomeClassification')
        equal(attempt['schema'], 'e02-minimum-attempt-subject-v1'); equal(attempt['profileId'], wire.PROFILE)
        need(attempt['attemptId'] not in seen, 'DUPLICATE_HISTORY_ATTEMPT'); seen.add(attempt['attemptId'])
        need(attempt['ordinaryRole'] in wire.STAGES, 'ATTEMPT_ROLE')
        need(re.fullmatch('[0-9a-f]{32}', attempt['runId']), 'ATTEMPT_RUNID')
        forbidden |= actors(attempt['authors']) | actors(attempt['operators'])
        files.read(attempt['rawOutcome']); files.read(attempt['sourceSubject'])
        equal(row['classification'], attempt['outcomeClassification'])
        if row['disposition'] == 'CONTRIBUTE_WHOLE_WINDOW':
            need(attempt['windowSubject'] is not None and row['classification'] == 'COMPLETE_PENDING_INDEPENDENT_QUALIFICATION', 'FAILED_WINDOW_CANNOT_DONATE_ROWS')
        else:
            need(attempt['windowSubject'] is None, 'EXCLUDED_ATTEMPT_CANNOT_DONATE_WINDOW')
        attempt_docs.append((row, attempt))
    # Legacy packages are context only; all relevant authors/operators remain in
    # the union, including failed runs and consumer/control/source authors.
    for legacy in history['legacyContexts']:
        closed(legacy, 'subject authors operators meaning')
        forbidden |= actors(legacy['authors']) | actors(legacy['operators'])
        equal(legacy['meaning'], 'HISTORICAL_CONTEXT_NO_ROW_DONATION')
        files.read(legacy['subject'])
    return forbidden, attempt_docs


def control_evidence(files, descriptor, origin):
    value = files.doc(descriptor)
    closed(value, 'schema profileId authors operators producerSubject executedScopes unchangedScopes componentCarry producerActual35 consumerSource consumerControls')
    equal(value['schema'], 'e02-minimum-controls-subject-v2'); equal(value['profileId'], wire.PROFILE)
    equal(value['producerSubject']['sha256'], PRODUCER_SHA)
    names = {'observation-model': 20, 'public-identity-metadata': 8, 'producer2-source-wiring': 7}
    need(type(value['executedScopes']) is list and {r['name'] for r in value['executedScopes']} == set(names)
         and len(value['executedScopes']) == len(names), 'EXACT_CHANGED_CONTROLS')
    for row in value['executedScopes']:
        closed(row, 'name count skips result sourceBefore sourceAfter stdout stderr')
        equal(row['count'], names[row['name']]); equal(row['skips'], 0)
        equal(row['sourceBefore'], row['sourceAfter'])
        need(type(row['sourceBefore']) is list and row['sourceBefore'], 'CONTROL_SOURCE_PINS')
        for pin in row['sourceBefore']: files.read(pin, 67108864)
        for key in ('result', 'stdout', 'stderr'): files.read(row[key])
    need(type(value['unchangedScopes']) is list and len(value['unchangedScopes']) == 1, 'GUARD_CARRY_ONLY')
    carry = value['unchangedScopes'][0]
    closed(carry, 'name count oldSource currentSource actualResult acceptance meaning')
    equal(carry['name'], 'guard'); equal(carry['count'], 29)
    equal(carry['meaning'], 'BYTE_IDENTICAL_CARRY_NOT_NEW_EXECUTION')
    equal((carry['oldSource']['bytes'], carry['oldSource']['sha256']), (carry['currentSource']['bytes'], carry['currentSource']['sha256']))
    for key in ('oldSource', 'currentSource', 'actualResult', 'acceptance'): files.read(carry[key])
    producer = files.doc(value['producerSubject'])
    equal(value['componentCarry'], producer['componentCarry'], 'EXACT_PRODUCER_COMPONENT_CARRY')
    component = files.doc(value['componentCarry'])
    for pair in component['modules']:
        equal(pair['classification'], 'BYTE_IDENTICAL')
        equal(files.read(pair['original']), files.read(pair['current']), 'UNCHANGED_CARRIED_COMPONENT')
    for key in ('source', 'actualControls', 'actualAcceptance', 'bridgeAcceptance'):
        if key in component['ordinaryBaseline']: files.read(component['ordinaryBaseline'][key])
    for key in ('source', 'actualControls', 'actualAcceptance', 'runtimeAcceptance'):
        if key in component['diagnosticBaseline']: files.read(component['diagnosticBaseline'][key])
    for descriptor in component['functionProofs']: files.read(descriptor)
    equal(value['producerActual35']['sha256'], ACTUAL35_SHA, 'FROZEN_ACCEPTED_ACTUAL35_RESULT')
    actual = files.doc(value['producerActual35'])
    equal(actual['schema'], 'e02-producer2-actual35-data-result-subject-v1')
    equal(actual['producerSource'], value['producerSubject'])
    equal(actual['actualCountsSeparate'], [20, 8, 7])
    equal(actual['allNatural0NoForceNoErrorNoTruncation'], True)
    equal(actual['sourceUnchangedBeforeAfterEveryScopeAndOverall'], True)
    equal(actual['ordinaryClientRows'], 0)
    separate = files.doc(actual['separateScopes'])['scopes']
    equal([r['scope'] for r in separate], list(names), 'ACTUAL35_SEPARATE_SCOPE_MEMBERSHIP')
    for row, scoped in zip(value['executedScopes'], separate):
        equal(row['name'], scoped['scope']); equal(row['count'], scoped['count'])
        equal(row['result'], scoped['execution']); equal(row['stdout'], scoped['stdout']); equal(row['stderr'], scoped['stderr'])
        execution = files.doc(row['result'])
        equal(execution['expectedCount'], row['count']); equal(execution['observedCount'], row['count'])
        equal(execution['exitCode'], 0); equal(execution['signal'], None)
        for key in ('naturalExit', 'reaped', 'stdoutEOF', 'stderrEOF', 'sourceUnchanged'): equal(execution[key], True)
        equal(execution['forceRequested'], False); equal(execution['firstError'], None); equal(execution['secondaryErrors'], [])
        equal(execution['truncated'], {'stdout': False, 'stderr': False})
    # The result subject preserves its original pre-review state. Independent
    # acceptance comes from actual external origins, not rewriting that state.
    origin.reviews(value['producerActual35'], 'CONTROL')
    files.read(value['consumerSource']); files.read(value['consumerControls'])
    origin.reviews(descriptor, 'CONTROL')
    return value


def graph(files, subject):
    root = Path(subject['outputRoot'])
    need(root.is_absolute() and root.name == subject['runId'], 'EXACT_FRESH_OUTPUT_ROOT')
    need(type(subject['graphFiles']) is list and len(subject['graphFiles']) <= 20000, 'GRAPH_FILES_BOUND')
    paths = set()
    for descriptor in subject['graphFiles']:
        p = pin_shape(descriptor)
        need(p.is_relative_to(root) and str(p) not in paths, 'GRAPH_PATH_ALIAS')
        paths.add(str(p)); files.read(descriptor, 67108864)
    exclusions = subject['excludedFiles']
    need(type(exclusions) is list and len(exclusions) <= 20000, 'EXCLUSION_BOUND')
    for item in exclusions:
        closed(item, 'path reason')
        p = Path(item['path'])
        need(p.is_relative_to(root) and str(p) not in paths, 'EXCLUSION_ALIAS')
        need(item['reason'] in ('DISPOSABLE_DISK_IMAGE', 'PRIVATE_RUNTIME_KEY', 'SDK_APK_INPUT', 'RAW_APPLICATION_DATABASE'), 'CLOSED_EXCLUSION_REASON')
        need(not any(part in p.parts for part in ('commands', 'ui', 'evidence', 'session', 'cleanup', 'ownership')), 'PROOF_CANNOT_BE_EXCLUDED')
    return paths


def fixture_calls(files, driver, command_rows):
    pins = driver['fixtureCalls']
    need(type(pins) is list and 1 <= len(pins) <= 64, 'FIXTURE_CALL_BOUND')
    calls, last = {}, 0
    for ordinal, descriptor in enumerate(pins, 1):
        c = files.doc(descriptor)
        closed(c, 'schema profileId windowId operation ordinal commandSequence command reply')
        equal(c['schema'], 'e02-minimum-fixture-call-v1'); equal(c['profileId'], wire.PROFILE)
        equal(c['windowId'], driver['windowId']); equal(c['ordinal'], ordinal)
        need(c['operation'] in ('prepare', 'status', 'publish'), 'CLOSED_FIXTURE_OPERATION')
        seq = c['commandSequence']; integer(seq, last + 1, len(command_rows)); last = seq
        equal(files.doc(c['command']), command_rows[seq - 1]); calls[seq] = (descriptor, c)
        argv = command_rows[seq - 1]['argv']
        need(len(argv) == 6 and argv[:2] == ['/usr/bin/docker', 'exec'] and
             argv[3:] == ['/usr/local/bin/node', '/input/fixture.mjs', c['operation']], 'ACTUAL_FIXED_FIXTURE_COMMAND')
        equal(files.read(c['reply']), files.read(command_rows[seq - 1]['stdout']))
        reply = files.doc(c['reply'])
        closed(reply, 'schema profileId windowId operation caseId ok result')
        equal(reply['schema'], 'e02-minimum-fixture-command-v2'); equal(reply['profileId'], wire.PROFILE)
        equal(reply['windowId'], driver['windowId']); equal(reply['operation'], c['operation'])
        equal(reply['caseId'], 'minimum-two-role-rs'); equal(reply['ok'], True)
        result = reply['result']
        if c['operation'] == 'prepare':
            closed(result, 'profileId windowId ordinaryRole expected prepared inboxes')
            equal(result['ordinaryRole'], driver['ordinaryRole'])
        elif c['operation'] == 'status':
            closed(result, 'profileId windowId stageId stageIndex complete ready gate captureSequence scope')
            idx = result['stageIndex']; integer(idx, 0, len(wire.STAGES[driver['ordinaryRole']]))
            expected_stage = wire.STAGES[driver['ordinaryRole']][idx] if idx < len(wire.STAGES[driver['ordinaryRole']]) else None
            equal(result['stageId'], expected_stage); equal(result['complete'], expected_stage is None)
            equal(result['ready'], result['gate'] is not None)
            if result['gate'] is not None: wire.generation(result['gate'], True)
            integer(result['captureSequence'], 0, 262144)
            equal(result['scope'], 'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT')
        else:
            closed(result, 'profileId windowId stage publication publicationWindow validation producerValidation actualNewAppFrameObserved')
            record = files.doc(result['publication'])
            for key in ('stage', 'publicationWindow', 'validation', 'producerValidation', 'actualNewAppFrameObserved'):
                equal(result[key], record[key], 'PUBLISH_REPLY_ACTUAL_RECORD')
        equal(result['profileId'], wire.PROFILE); equal(result['windowId'], driver['windowId'])
    actual = {i for i, c in enumerate(command_rows, 1) if '/input/fixture.mjs' in c['argv'] and c['argv'][-1] in ('prepare', 'status', 'publish')}
    equal(set(calls), actual, 'OMITTED_FIXTURE_CALL')
    operations = [c['operation'] for _, c in calls.values()]
    equal(operations.count('prepare'), 1); equal(operations[0], 'prepare')
    equal(operations.count('publish'), len(wire.STAGES[driver['ordinaryRole']]))
    return calls


def preparation_join(files, calls, candidate, role, proxy):
    first = next(iter(calls.values()))[1]
    prepared_result = files.doc(first['reply'])['result']
    p = files.doc(prepared_result['prepared'])
    closed(p, 'schema profileId windowId role rumors events expected')
    equal(p['schema'], 'e02-minimum-prepared-v2'); equal(p['profileId'], wire.PROFILE)
    equal(p['windowId'], wire.WINDOWS[role]); equal(p['role'], role)
    closed(p['rumors'], 'business chat')
    for name in ('business', 'chat'): equal(p['rumors'][name], files.doc(candidate['oracles'][name]))
    equal(p['expected'], prepared_result['expected'])
    equal(set(p['expected']), set(wire.STAGES[role]))
    need(type(p['events']) is list and len(p['events']) == len(wire.STAGES[role]), 'FINITE_PREPARED_OUTERS')
    for index, name in enumerate(wire.STAGES[role]):
        spec = wire.stage(role, index); expected = p['expected'][name]
        closed(expected, 'stage rumor content'); equal(expected['stage'], spec)
        equal(files.doc(expected['rumor']), p['rumors'][spec['oracle']])
        equal(files.read(expected['content']), p['rumors'][spec['oracle']]['content'].encode('utf-8'))
        wire.signed(p['events'][index], wire.ACCOUNTS[role])
    if role == 'archive':
        equal(p['events'][0], p['events'][1]); need(p['events'][2]['id'] != p['events'][0]['id'], 'PREPARED_FRESH_WRAP')
    inboxes = files.doc(prepared_result['inboxes'])
    closed(inboxes, 'events ack received eose sentFrames elapsedNanoseconds')
    need(type(inboxes['events']) is list and len(inboxes['events']) == 2, 'BOTH_CURRENT_INBOXES')
    equal(inboxes['received'], []); equal(inboxes['eose'], None)
    integer(inboxes['elapsedNanoseconds'], 0, 1800000000000)
    need(len(inboxes['ack']) == len(inboxes['sentFrames']) == 2, 'TWO_REAL_INBOX_SEND_ACKS')
    outgoing = [r for r in proxy.rows if r.get('exchangeLabel') == 'prepare-inboxes' and r['direction'] == 'PRODUCER_TO_RELAY']
    incoming = [r for r in proxy.rows if r.get('exchangeLabel') == 'prepare-inboxes' and r['direction'] == 'RELAY_TO_PRODUCER']
    equal(len(outgoing), 2)
    for i, (event, account) in enumerate(zip(inboxes['events'], (wire.A, wire.B))):
        closed(event, 'id pubkey created_at kind tags content sig')
        equal(event['pubkey'], account); equal(event['kind'], 10050); equal(event['tags'], [['relay', 'ws://127.0.0.1:17777']]); equal(event['content'], '')
        integer(event['created_at']); hx(event['sig'], 128)
        equal(event['id'], hashlib.sha256(json_bytes([0, account, event['created_at'], 10050, event['tags'], ''])).hexdigest())
        sent = inboxes['sentFrames'][i]
        closed(sent, 'frame eventId messageType sendInvoked sendCallbackCompleted callbackBufferHash')
        equal(sent['eventId'], event['id']); equal(sent['messageType'], 'EVENT')
        equal(sent['sendInvoked'], True); equal(sent['sendCallbackCompleted'], True)
        raw = files.read(sent['frame']); equal(wire.frame(raw), ['EVENT', event])
        equal(sent['callbackBufferHash'], hashlib.sha256(raw).hexdigest())
        equal(wire.decode64(outgoing[i]['rawBase64']), raw)
        matching = [a for a in inboxes['ack'] if a['frame'][1] == event['id']]
        need(len(matching) == 1, 'ONE_INBOX_ACK')
        ack = matching[0]; closed(ack, 'rawBase64 frame')
        equal(wire.frame(wire.decode64(ack['rawBase64'])), ack['frame'])
        need(len(ack['frame']) == 4 and ack['frame'][:3] == ['OK', event['id'], True], 'INBOX_REAL_OK')
        need(any(r['rawBase64'] == ack['rawBase64'] for r in incoming), 'INBOX_ACK_IN_RAW_PROXY')
    return p


def status_join(files, obs, spec, role, command_rows, calls, publication):
    status = obs['subscriptionStatus']
    closed(status, 'profileId windowId stageId stageIndex complete ready gate captureSequence scope')
    equal(status['profileId'], wire.PROFILE); equal(status['windowId'], wire.WINDOWS[role])
    equal(status['stageId'], spec['id']); equal(status['stageIndex'], spec['index'])
    equal(status['complete'], False); equal(status['ready'], True)
    equal(status['scope'], 'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT')
    equal(status['gate'], publication['gate'], 'STATUS_PUBLICATION_CURRENT_GATE')
    integer(status['captureSequence'], status['gate']['eoseSequence'], 262144)
    call = files.doc(obs['subscriptionStatusCall'])
    seq = call['commandSequence']; need(seq in calls, 'STATUS_IN_FULL_FIXTURE_CALLS')
    equal(calls[seq][0], obs['subscriptionStatusCall']); equal(call['operation'], 'status')
    equal(call['command'], obs['subscriptionStatusCommand']); equal(call['reply'], obs['subscriptionStatusReply'])
    equal(files.doc(call['reply'])['result'], status)
    equal(files.doc(obs['subscriptionStatusCommand']), command_rows[seq - 1])
    need(obs['custodySegment']['commandSequenceFirst'] <= seq <= obs['custodySegment']['commandSequenceLast'], 'STATUS_IN_STAGE_CUSTODY')


def guest_observations(files, root, command_rows):
    def observed(name, tail):
        descriptor = files.pins[str(Path(root) / 'evidence' / name)]
        raw = files.read(descriptor)
        matches = [c for c in command_rows if gui.adb_tail(c) == tail]
        need(len(matches) == 1, 'ONE_ACTUAL_PROPERTY_PROBE')
        equal(raw, files.read(matches[0]['stdout']))
        return raw
    equal(observed('ro.build.version.sdk.txt', ['shell', 'getprop', 'ro.build.version.sdk']).strip(), b'35')
    equal(observed('ro.build.fingerprint.txt', ['shell', 'getprop', 'ro.build.fingerprint']).strip(),
          b'Android/sdk_phone64_x86_64/emu64x:15/AE3A.240806.019/12368160:userdebug/test-keys')
    rows = files.doc(files.pins[str(Path(root) / 'evidence/network-addresses.json')])
    for relative, payload in (('network-addresses.json', ['probe', 'ip', '-j', 'addr']),
                              ('listeners.txt', ['probe', 'ss', '-H', '-lnt'])):
        probes = [c for c in command_rows if c['argv'][-4:] == payload]
        need(len(probes) == 1, 'ONE_ACTUAL_NAMESPACE_PROBE')
        descriptor = files.pins[str(Path(root) / 'evidence' / relative)]
        equal(files.read(descriptor), files.read(probes[0]['stdout']), 'ACTUAL_NAMESPACE_RAW_STREAM')
    need(type(rows) is list and len(rows) == 1 and rows[0].get('ifname') == 'lo', 'ACTUAL_PRIVATE_LOOPBACK_ONLY')
    interface = rows[0]
    need(type(interface.get('flags')) is list and 'LOOPBACK' in interface['flags'], 'ACTUAL_LOOPBACK_FLAGS')
    entries = interface.get('addr_info')
    need(type(entries) is list and 1 <= len(entries) <= 16, 'ACTUAL_LOOPBACK_ADDRESSES')
    for e in entries:
        text(e['local'], 64); need('%' not in e['local'], 'UNZONED_LOOPBACK')
        address = ipaddress.ip_address(e['local'])
        need(address.is_loopback and e['family'] == ('inet' if address.version == 4 else 'inet6')
             and e['scope'] == 'host' and e['prefixlen'] == (8 if address.version == 4 else 128), 'LOOPBACK_ADDRESS_DOMAIN')
    listeners = files.read(files.pins[str(Path(root) / 'evidence/listeners.txt')]).decode('ascii', 'strict').splitlines()
    need(1 <= len(listeners) <= 4096, 'ACTUAL_LISTENERS')
    for line in listeners:
        fields = line.split()
        need(len(fields) == 5 and fields[0] == 'LISTEN' and fields[4] in ('0.0.0.0:*', '[::]:*', '*:*'), 'LISTENER_ROW')
        need(all(re.fullmatch('[0-9]{1,10}', n) and int(n) <= 4294967295 for n in fields[1:3]), 'LISTENER_QUEUE_DOMAIN')
        match = re.fullmatch(r'(?:\[([^\[\]]+)\]|([0-9.]+)):([1-9][0-9]{0,4})', fields[3])
        need(match is not None, 'NUMERIC_LISTENER')
        address = ipaddress.ip_address(match[1] or match[2]); integer(int(match[3]), 1, 65535)
        mapped = address.ipv4_mapped if address.version == 6 else None
        need(address.is_loopback or mapped is not None and mapped.is_loopback
             or fields[3] in ('0.0.0.0:8080', '[::]:8080'), 'NO_UNEXPECTED_NONLOOPBACK_LISTENER')


def window(files, descriptor, candidate, origin, producer):
    s = files.doc(descriptor); closed(s, WINDOW_KEYS)
    equal(s['schema'], 'e02-minimum-window-subject-v1'); equal(s['profileId'], wire.PROFILE)
    role = s['ordinaryRole']; need(role in wire.STAGES, 'WINDOW_ROLE')
    equal(s['windowId'], wire.WINDOWS[role]); need(re.fullmatch('[0-9a-f]{32}', s['runId']), 'WINDOW_RUNID')
    equal(s['sourceSubject'], candidate['producerSubject'])
    root = s['outputRoot']; files.window(root)
    paths = graph(files, s)
    # Exact /input mounts must derive from frozen producer fixture-plan pins.
    fixture = files.doc(next(p for p in producer['sources'] if Path(p['path']).name == 'fixture-plan.json'))
    equal(fixture['schema'], 'e02-ordinary-minimum-fixture-plan-v2')
    equal(fixture['profileId'], wire.PROFILE)
    expected_mounts = {p['path']: p for p in fixture['pins'].values()}
    equal(len(s['readOnlyMountBindings']), len(expected_mounts))
    equal({b['guest']['path'] for b in s['readOnlyMountBindings']}, set(expected_mounts))
    for b in s['readOnlyMountBindings']:
        closed(b, 'guest host')
        source = expected_mounts[b['guest']['path']]
        equal(b['host'], {'path': source['source'], 'bytes': source['bytes'], 'sha256': source['sha256']})
        files.binding(b['guest'], b['host'], root)
    config = files.doc(s['runConfig']); closed(config, CONFIG_KEYS)
    need(any(same(s['runConfig'], p) for p in producer['configurations']), 'FROZEN_REVIEWED_ROLE_CONFIGURATION')
    equal(config['schema'], 'e02-ordinary-minimum-role-runtime-plan-v2')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId'): equal(config[key], s[key])
    equal(config['account'], wire.ACCOUNTS[role]); equal(config['peer'], wire.A if role == 'incoming' else wire.B)
    integer(config['originalLeaseSeconds'], 60, 1800)
    source_by_name = {Path(p['path']).name: p for p in producer['sources']}
    expected_sources = [source_by_name[name] for name in ('supervisor.py', 'lease_guard.py', 'android_driver.py', 'ui-plan.json',
                       'fixture.mjs', 'fixture-plan.json', 'minimum-plan.json', 'business-rumor.json', 'chat-rumor.json',
                       'exchange.mjs', 'phase-writer.mjs', 'dependency-tree.mjs', 'dependency-tree.json',
                       'capture-budget.mjs', 'exchange-adapter.mjs', 'proxy-observer.mjs')]
    equal(config['sourceAndDependencyPins'], expected_sources, 'CURRENT_SOURCE_CONFIG_PROVENANCE')
    equal(s['supervisorSource'], source_by_name['supervisor.py'])
    for pin in expected_sources:
        raw = files.read(pin)
        staged = dict(pin, path=str(Path(root) / 'input' / Path(pin['path']).name))
        equal(files.read(staged), raw, 'STAGED_CURRENT_SOURCE')
        need(staged['path'] in paths, 'STAGED_SOURCE_IN_WHOLE_GRAPH')
    equal(config['runtimeImage'], 'sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f')
    equal(config['relayImage'], 'sha256:fe586a0bc68edefb553a62d21983de469128f7cb785bfcc2ef7c82dbf1cded82')
    equal(config['sdkRoot'], '/tmp/nbdp-e02-api35-fixture-r2/sdk')
    equal(config['scope'], 'E02_ORDINARY_MINIMUM_RS_TWO_ROLE_WINDOW_ONLY')
    equal(config['canonicalE02'], 'PARTIAL22_UNCHANGED')
    equal(config['amethystApk']['bytes'], 165860063)
    equal(config['amethystApk']['sha256'], '5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5')
    equal(config['helperApk']['sha256'], 'a680e513a9b36cab634620507b77bba36532ce13acb465a860c7bef60d23ec20')
    # SDK/APK assets remain external pinned prerequisites; inspecting their index
    # is not build attestation, current admission or a bundled replay image.
    files.read(config['sdkInventory']); files.read(config['guardBundleInventory']); files.read(config['relayConfig'])
    release = files.doc(s['runRelease'])
    closed(release, 'schema executionAuthorized rootSession executionSession runId scope profileId ordinaryRole windowId runConfig sourceSubject issuedAtUtcNs notAfterUtcNs qaReview securityReview guardRegressionEvidence freshResourceAdmission resourcePrerequisite limits')
    equal(release['schema'], 'e02-ordinary-minimum-role-release-v2')
    equal(release['executionAuthorized'], True); equal(release['runConfig'], s['runConfig'])
    equal(release['sourceSubject'], candidate['producerSubject']); equal(release['scope'], config['scope'])
    need(release['rootSession'] in origin.forbidden and release['executionSession'] in origin.forbidden, 'DECLARED_ACTUAL_GRANT_OPERATOR')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId'): equal(release[key], s[key])
    integer(release['issuedAtUtcNs'], 0, I64); integer(release['notAfterUtcNs'], release['issuedAtUtcNs'], I64)
    for key in ('qaReview', 'securityReview', 'guardRegressionEvidence'): files.read(release[key])
    for key, reviewer_role in (('qaReview', 'qa'), ('securityReview', 'security')):
        reviewed = [r for r in origin.value['reviews'] if r['kind'] == 'SOURCE' and r['role'] == reviewer_role
                    and same(r['subject'], candidate['producerSubject'])]
        need(len(reviewed) == 1, 'RELEASE_CURRENT_SOURCE_REVIEW')
        equal(release[key], reviewed[0]['review'], 'GRANT_ACTUAL_SOURCE_ACCEPTANCE_JOIN')
    tool = origin.tool(s['outer'], s)
    lease = lease_check(files, s['lease'], s['runId'], release, tool)
    resource = files.doc(s['resource'])
    closed(resource, 'schema runId measuredAtUtcNs outputFilesystem freeBytes memAvailableBytes affinityCpus kvmAccessible rawReceipt sourceIndex actualAdmissionMeaning')
    equal(resource['schema'], 'e02-minimum-resource-witness-v1'); equal(resource['runId'], s['runId'])
    need(resource['measuredAtUtcNs'] <= release['issuedAtUtcNs'] <= lease['issuedUtcNs'], 'RESOURCE_BEFORE_GRANT')
    equal(resource['outputFilesystem'], root)
    integer(resource['freeBytes'], 8 * 1024 ** 3); integer(resource['memAvailableBytes'], 12 * 1024 ** 3)
    integer(resource['affinityCpus'], 8); equal(resource['kvmAccessible'], True)
    equal(resource['sourceIndex'], config['sdkInventory']); files.read(resource['rawReceipt'])
    equal(resource['rawReceipt'], release['freshResourceAdmission']); files.read(release['resourcePrerequisite'])
    equal(resource['actualAdmissionMeaning'], 'ACTUAL_CURRENT_ADMISSION_NOT_MINIMUM_OR_PEAK_OR_GUEST_HEALTH')
    equal(s['sourceControls'], candidate['sourceControls'])
    command_rows = commands(files, s['commands'], root)
    owned_cids = ownership(files, s, config, fixture, command_rows)
    guest_observations(files, root, command_rows)
    ui_start = [i for i, c in enumerate(command_rows, 1) if gui.adb_tail(c) == ['shell', 'pm', 'clear', gui.APP]]
    need(len(ui_start) == 1, 'FRESH_ONCE_APP_CLEAR')
    snapshot_tails = (['shell', 'uiautomator', 'dump', '/sdcard/nbdp-window.xml'],
                      ['shell', 'cat', '/sdcard/nbdp-window.xml'], ['exec-out', 'screencap', '-p'])
    ui_actions = [i for i, c in enumerate(command_rows, 1) if i >= ui_start[0]
                  and gui.adb_tail(c) is not None and gui.adb_tail(c) not in snapshot_tails]
    need(len(ui_actions) <= 120, 'ORIGINAL_WHOLE_UI_ACTION_CAP')
    driver = files.doc(s['driver']); closed(driver, DRIVER_KEYS)
    equal(driver['schema'], 'e02-minimum-role-driver-result-v2')
    for key in ('profileId', 'ordinaryRole', 'windowId', 'runId', 'runConfig', 'runRelease'): equal(driver[key], s[key])
    equal(driver['executionState'], 'PARTIAL'); equal(driver['canonicalE02Changed'], False)
    equal(driver['expectedAccountPubkey'], wire.ACCOUNTS[role])
    equal(driver['accountIdentityQualification'], 'ACTUAL_NPROFILE_INDEPENDENT_DECODE_AND_REVIEW_REQUIRED')
    equal(driver['allUICaptures'], s['ui']); gui.captures(files, s['ui'], command_rows)
    gui.account(files, driver['accountIdentityGUI'], role)
    tor = files.doc(driver['torConfigurationGUI'])
    equal(tor['schema'], 'e02-tor-configuration-gui-v1')
    for key in ('selectedOff', 'firstSaveReturnedToLogin', 'savedStateReopened', 'secondSaveReturnedToLogin'):
        need(any(same(tor[key], c) for c in s['ui']), 'TOR_ACTUAL_UI_INVENTORY')
    integer(tor['torFailureDismissals'], 0, 2)
    need(type(driver['environmentAnrEvidence']) is list and len(driver['environmentAnrEvidence']) <= 2, 'BOUNDED_RETAINED_ANR')
    for row in driver['environmentAnrEvidence']:
        closed(row, 'decision afterWaitObservation')
        need(row['afterWaitObservation'] is not None, 'PARTIAL_OS_RECOVERY_CANNOT_QUALIFY')
        files.doc(row['decision']); files.doc(row['afterWaitObservation'])
    supervisor = files.doc(s['supervisor'])
    closed(supervisor, 'schema runId profileId ordinaryRole windowId runConfig runRelease lease canonicalE02Changed limits executionState error secondaryErrors cleanup')
    equal(supervisor['schema'], 'e02-ordinary-minimum-role-supervisor-result-v2')
    for key in ('runId', 'profileId', 'ordinaryRole', 'windowId', 'runConfig', 'runRelease', 'lease'): equal(supervisor[key], s[key])
    equal(supervisor['executionState'], 'PARTIAL'); equal(supervisor['error'], None); equal(supervisor['secondaryErrors'], [])
    equal(supervisor['canonicalE02Changed'], False)
    cids = cleanup_check(files, supervisor['cleanup'], root)
    equal(cids, owned_cids, 'CLEANUP_MATCHES_ALL_ACTUAL_OWNERS')
    # No early observation contributes until whole lifecycle has qualified.
    calls = fixture_calls(files, driver, command_rows)
    proxy = wire.Proxy(files, s['proxy'])
    trace = observer.Trace(files, s, proxy)
    need(not any(r['direction'] == 'PUBLICATION_GENERATION_INVALIDATED' for r in proxy.rows), 'RETAINED_STICKY_GENERATION_FAILURE')
    labels = {'prepare-inboxes', *(sid + suffix for sid in wire.STAGES[role] for suffix in ('-publish', '-query'))}
    need(all(r.get('exchangeLabel') in labels for r in proxy.rows if 'exchangeLabel' in r), 'CLOSED_WHOLE_BACKEND_HISTORY')
    need(not any(Path(p).name.startswith(('serve-error', 'command-error')) for p in paths
                 if Path(p).is_relative_to(Path(root) / 'session/fixtures')), 'RETAINED_FIXTURE_FAILURE')
    prepared = preparation_join(files, calls, candidate, role, proxy)
    inboxes = files.doc(files.doc(next(iter(calls.values()))[1]['reply'])['result']['inboxes'])
    trace.exchange('prepare-inboxes', {k: v for k, v in inboxes.items() if k != 'events'})
    observations = driver['observations']
    need(type(observations) is list, 'OBSERVATION_ARRAY')
    equal([o['id'] for o in observations], list(wire.STAGES[role]), 'EXACT_ORDERED_ROLE_STAGES')
    previous_command, previous_ui, previous_time = 0, 0, -1
    events, sent = [], []
    previous_phase = 0
    for index, obs in enumerate(observations):
        closed(obs, OBS_KEYS); spec = wire.stage(role, index)
        equal(obs['state'], 'EXPORTED_PENDING_INDEPENDENT_WHOLE_RUN_REVIEW')
        expected = files.doc(obs['expectedRumor']); wire.rumor(expected)
        equal(expected, files.doc(candidate['oracles'][spec['oracle']]), 'SHARED_FROZEN_EXPECTATION')
        bindings = obs['originalGuestToHostBindings']
        need(type(bindings) is list and len(bindings) <= 512
             and len({b['guest']['path'] for b in bindings}) == len(bindings), 'UNIQUE_ORIGINAL_GUEST_BINDINGS')
        for binding in bindings:
            closed(binding, 'guest host'); files.binding(binding['guest'], binding['host'], root)
        publication = files.doc(obs['publication'])
        equal(publication['event'], prepared['events'][index], 'PUBLISHED_CURRENT_PREPARED_OUTER')
        published_calls = [c for _, c in calls.values() if c['operation'] == 'publish' and
                           same(files.doc(c['reply'])['result']['publication'], obs['publication'])]
        need(len(published_calls) == 1 and obs['custodySegment']['commandSequenceFirst'] <= published_calls[0]['commandSequence']
             <= obs['custodySegment']['commandSequenceLast'], 'ACTUAL_PUBLISH_IN_STAGE_CUSTODY')
        event, send = wire.publication(files, proxy, publication, expected, spec, role)
        phase_first, phase_last = trace.stage(publication)
        need(phase_first > previous_phase, 'FRESH_NONOVERLAPPING_STAGE_PHASES')
        previous_phase = phase_last
        native_record = files.doc(publication['validation']['validation'])
        for key in ('rustBinary', 'rustSource'):
            actual_input = fixture['pins'][key]
            equal(native_record[key], {k: actual_input[k] for k in ('path', 'bytes', 'sha256')}, 'CURRENT_NATIVE_FIXTURE_BINDING')
        equal(obs['actualNewAppFrameObserved'], publication['actualNewAppFrameObserved'])
        status_join(files, obs, spec, role, command_rows, calls, publication)
        custody = gui.selection(files, obs, expected, spec, role, command_rows, s['ui'], config['helperApk'])
        equal(custody['uiActionCountBefore'], sum(i < custody['commandSequenceFirst'] for i in ui_actions), 'ACTUAL_STAGE_ACTION_COUNT_BEFORE')
        equal(custody['uiActionCountAfter'], sum(i <= custody['commandSequenceLast'] for i in ui_actions), 'ACTUAL_STAGE_ACTION_COUNT_AFTER')
        need(custody['commandSequenceFirst'] > previous_command and custody['uiCaptureSerialFirst'] > previous_ui, 'FRESH_NONOVERLAPPING_STAGE_CUSTODY')
        previous_command, previous_ui = custody['commandSequenceLast'], custody['uiCaptureSerialLast']
        selected_time = files.doc(obs['selection'])['capturedMonotonicNs']
        need(selected_time > previous_time, 'FRESH_SELECTION_HOST_CLOCK_ORDER'); previous_time = selected_time
        events.append(event); sent.append(send)
    if role == 'archive':
        equal(events[0], events[1]); equal(sent[0], sent[1], 'IDENTICAL_ACTUAL_SENT_EVENT_BYTES')
        need(events[2]['id'] != events[0]['id'], 'FRESH_WRAP_OUTER_ID')
    # Exact proof roots are complete filesystem inventories, including late proxy
    # history and guard flags. This never enumerates userdata or SDK trees.
    for directory in ('commands', 'ui', 'evidence', 'session', 'cleanup', 'ownership'):
        folder = Path(root) / directory
        need(folder.is_dir() and not folder.is_symlink(), 'PROOF_ROOT_MISSING')
        visited = 0
        for p in folder.rglob('*'):
            visited += 1
            need(visited <= 40000, 'PROOF_TREE_VISITS_BOUND')
            need(not p.is_symlink(), 'PROOF_TREE_SYMLINK')
            mode = p.lstat().st_mode
            if stat.S_ISREG(mode):
                need(str(p) in paths, 'OMITTED_WHOLE_WINDOW_PROOF')
            elif not stat.S_ISDIR(mode):
                need(stat.S_ISSOCK(mode) and p == Path(root) / 'session/fixtures/control.sock', 'UNPLANNED_PROOF_SPECIAL_FILE')
    need(not (Path(root) / 'session/control/REVOKED').exists(), 'STICKY_REVOKED_WINDOW')
    for pin in (s['driver'], s['supervisor'], s['lease'], s['proxy'], s['phase'], *s['commands']):
        need(pin['path'] in paths, 'OPERAND_NOT_IN_WINDOW_GRAPH')
    equal(s['sourcePolicyObservations'], {'clockPolicy': 'SOURCE_ENFORCED_THREE_DOMAINS_ORIGINAL_LEASE',
          'perCommandClockChronology': 'UNKNOWN_NOT_RECORDED', 'sdkAssetsBundled': False,
          'guestHealth': 'UNKNOWN', 'businessEffectsMeasured': False})
    origin.reviews(descriptor, 'WINDOW')
    return dict(role=role, runId=s['runId'], outputRoot=root, grant=s['runRelease'], lease=s['lease'],
                cids=cids, started=tool['startedUtcNs'], finished=tool['finishedUtcNs'], exports=len(observations))


def consume(files, manifest_pin, origin_pin):
    manifest = files.doc(manifest_pin)
    closed(manifest, 'schema profileId candidate history windows')
    equal(manifest['schema'], 'e02-minimum-consumption-manifest-v1'); equal(manifest['profileId'], wire.PROFILE)
    candidate = files.doc(manifest['candidate'])
    closed(candidate, 'schema profileId authors operators producerSubject producerContract adoption oracles sourceControls primaryEvidenceReferences scope')
    equal(candidate['schema'], 'e02-minimum-candidate-v1'); equal(candidate['profileId'], wire.PROFILE)
    equal(candidate['scope'], 'SUPPLEMENTAL_ORDINARY_JS_RS_ONLY_NOT_CANONICAL_E02_PASS')
    equal(candidate['producerSubject']['sha256'], PRODUCER_SHA)
    equal(candidate['producerContract']['sha256'], CONTRACT_SHA)
    equal(candidate['adoption']['sha256'], ADOPTION_SHA)
    producer = files.doc(candidate['producerSubject'])
    equal(producer['schema'], 'e02-ordinary-minimum-producer2-source-subject-v1')
    for p in producer['sources']: files.read(p)
    files.read(candidate['producerContract'])
    adoption = files.doc(candidate['adoption'])
    equal(adoption['decision'], 'ADOPT_DISTINCT_CRITERION_PRESERVING_MINIMUM_LAB_PROFILE_ONLY')
    for key in ('executionGranted', 'canonicalPass', 'canonicalMandatoryScopeChanged', 'dependencyGateChanged', 'architectureOrBlockersChanged'):
        equal(adoption[key], False)
    closed(candidate['oracles'], 'business chat')
    for name, expected_id in (('business', wire.BUSINESS), ('chat', wire.CHAT)):
        oracle = wire.rumor(files.doc(candidate['oracles'][name])); equal(oracle['id'], expected_id)
        frozen = next(p for p in producer['sources'] if Path(p['path']).name == name + '-rumor.json')
        equal(candidate['oracles'][name], frozen)
    history = files.doc(manifest['history'])
    closed(history, 'schema profileId declaredScope authors operators attempts legacyContexts')
    equal(history['schema'], 'e02-minimum-attempt-inventory-v1'); equal(history['profileId'], wire.PROFILE)
    equal(history['declaredScope'], 'ALL_MINIMUM_ATTEMPTS_AND_RELEVANT_LEGACY_NEGATIVE_CONTEXTS_THROUGH_THIS_INVENTORY')
    origin_value = files.doc(origin_pin)
    forbidden, attempts = provenance(files, candidate, history, origin_value)
    forbidden |= {'/root/android_health_implementer', '/root/consumer3_preparation', producer['author'], producer['coordinator']}
    forbidden |= actors(history['authors']) | actors(history['operators'])
    for p in manifest['windows']:
        s = files.doc(p); forbidden |= actors(s['authors']) | actors(s['operators'])
    controls = files.doc(candidate['sourceControls'])
    forbidden |= actors(controls['authors']) | actors(controls['operators'])
    origin = Origin(files, origin_value, forbidden)
    equal(origin_value['method'], candidate['adoption']); equal(origin_value['candidate'], manifest['candidate'])
    equal(origin_value['history'], manifest['history']); equal(origin_value['windowSubjects'], manifest['windows'])
    origin.reviews(candidate['producerSubject'], 'SOURCE')
    control_evidence(files, candidate['sourceControls'], origin)
    origin.reviews(manifest['history'], 'HISTORY')
    contributing_attempts = [a for r, a in attempts if r['disposition'] == 'CONTRIBUTE_WHOLE_WINDOW']
    contributing = [a['windowSubject'] for a in contributing_attempts]
    equal(contributing, manifest['windows'], 'EXACT_WHOLE_WINDOW_MEMBERSHIP')
    need(len(contributing) == 2, 'EXACT_TWO_WINDOWS')
    for attempt in contributing_attempts:
        subject = files.doc(attempt['windowSubject'])
        for key in ('ordinaryRole', 'runId', 'sourceSubject'): equal(attempt[key], subject[key], 'ATTEMPT_WINDOW_LINEAGE')
        equal(attempt['rawOutcome'], subject['supervisor'], 'ACTUAL_WHOLE_ATTEMPT_OUTCOME')
    # Primary references are pinned context, never a primary-PASS assertion here.
    for p in candidate['primaryEvidenceReferences']: files.read(p)
    results = [window(files, p, candidate, origin, producer) for p in contributing]
    equal([r['role'] for r in results], ['incoming', 'archive'])
    for key in ('runId', 'outputRoot', 'grant', 'lease'):
        need(not same(results[0][key], results[1][key]), 'FRESH_SEPARATE_ROLE_WINDOWS')
    need(results[0]['finished'] <= results[1]['started'], 'SEQUENTIAL_CLEANUP_BARRIER')
    need(not results[0]['cids'] & results[1]['cids'], 'REUSED_CONTAINER_STATE')
    files.recheck()
    return dict(schema='e02-minimum-consumption-result-v2', state='SUPPLEMENTAL_DATA_CONSISTENT_WITH_EXTERNALLY_AUTHENTICATED_ORIGINS',
                profileId=wire.PROFILE, wholeWindows=2, selectedExports=5, selectedNoteContexts=3, uniqueRumorIds=2,
                canonicalE02Changed=False, canonicalE02='PARTIAL22_UNCHANGED', primaryMatrixQualified=False,
                businessEffectsMeasured=False, sdkRuntimeAdmission=False, portableProcessAttestation=False,
                nonoperativeMetadataFinding='PRODUCER2_PUBLIC_SCALAR_METADATA_CORRECTED_OLD_FINDING_PRESERVED',
                perCommandClockChronology='UNKNOWN_NOT_RECORDED', evidenceFiles=len(files.pins), evidenceBytes=files.total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True); parser.add_argument('--manifest-sha', required=True)
    parser.add_argument('--origin', required=True); parser.add_argument('--origin-sha', required=True)
    parser.add_argument('--read-root', action='append', required=True)
    args = parser.parse_args()
    try:
        files = Files(args.read_root)
        manifest_pin = external(files, args.manifest, args.manifest_sha)
        origin_pin = external(files, args.origin, args.origin_sha)
        result = consume(files, manifest_pin, origin_pin)
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as error:
        result = dict(schema='e02-minimum-consumption-result-v2', state='REFUSED_NO_CONTRIBUTION',
                      reason=type(error).__name__ + ':' + str(error)[:2048], canonicalE02Changed=False,
                      contributingWholeWindows=0, contributingExports=0)
        print(json_bytes(result).decode()); return 2
    print(json_bytes(result).decode()); return 0


if __name__ == '__main__':
    sys.exit(main())
