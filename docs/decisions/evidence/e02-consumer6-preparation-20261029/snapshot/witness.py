"""Externally anchored provenance and actual lifecycle joins, DATA inspection only.

The coordinator must authenticate session/tool origins outside this program and
pin the origin envelope at invocation. This module verifies that exact envelope;
it cannot turn operator-authored JSON into independent review.
"""
from pathlib import Path
import re
from strict import I64, closed, equal, hx, integer, need, same, text
from wire import PROFILE


def actors(values):
    need(type(values) is list and values and len(values) <= 128 and len(set(values)) == len(values), 'ACTOR_LIST')
    for value in values:
        text(value, 256)
        need(value.startswith('/root'), 'ACTOR_SESSION_NAME')
    return set(values)


class Origin:
    def __init__(self, files, value, forbidden):
        closed(value, 'schema profileId method candidate history windowSubjects attemptSubjects legacyContexts reviews tools provenanceLimit')
        equal(value['schema'], 'e02-minimum-origin-envelope-v1'); equal(value['profileId'], PROFILE)
        equal(value['provenanceLimit'], 'EXTERNALLY_AUTHENTICATED_COORDINATOR_TRANSCRIPTION_NOT_PORTABLE_ATTESTATION')
        self.files, self.value, self.forbidden = files, value, forbidden
        need(type(value['reviews']) is list and len(value['reviews']) <= 64, 'REVIEW_BOUND')
        self.used = set()

    def reviews(self, subject, kind, required=('qa', 'security')):
        for role in required:
            matches = [r for r in self.value['reviews'] if same(r.get('subject'), subject)
                       and r.get('kind') == kind and r.get('role') == role]
            need(len(matches) == 1, 'EXACT_INDEPENDENT_REVIEW:' + kind + ':' + role)
            row = matches[0]
            closed(row, 'kind role actor session subject decision findings review rawSessionEvidence visualChecks')
            text(row['actor'], 256); text(row['session'], 256)
            need(row['actor'] not in self.forbidden and row['session'] not in self.forbidden,
                 'AUTHOR_OPERATOR_REVIEW_LAUNDERING')
            equal(row['actor'], row['session'], 'ACTUAL_REVIEW_SESSION_ID')
            equal(row['decision'], 'ACCEPT_EXACT_SCOPED_EVIDENCE')
            need(type(row['findings']) is list and len(row['findings']) <= 1, 'REVIEW_FINDING_BOUND')
            for finding in row['findings']:
                closed(finding, 'id severity classification disposition actualDispositionEvidence')
                need(kind == 'SOURCE', 'UNRESOLVED_EVIDENCE_REVIEW_FINDING')
                text(finding['id'], 256)
                equal(finding['severity'], 'LOW')
                equal(finding['classification'], 'NONOPERATIVE_UNUSED_PLAN_NSEC')
                equal(finding['disposition'], 'ACCEPTED_WITHOUT_RUNTIME_INPUT_CHANGE')
                need(self.files.read(finding['actualDispositionEvidence']), 'ACTUAL_INDEPENDENT_DISPOSITION_REQUIRED')
            # Raw reports vary by real reviewer; never rewrite/fabricate their schemas.
            self.files.read(row['review']); self.files.read(row['rawSessionEvidence'])
            need(row['review']['bytes'] > 0 and row['rawSessionEvidence']['bytes'] > 0, 'EMPTY_ACTUAL_REVIEW')
            if kind == 'WINDOW':
                equal(row['visualChecks'], ['actual-account-gui', 'tor-off-saved-reopened',
                      'all-window-selected-note-pngs', 'helper-clear-copy-capture-custody'])
            else:
                equal(row['visualChecks'], [])
            self.used.add((subject['path'], kind, role))
        if len(required) == 2:
            rows = [r for r in self.value['reviews'] if same(r.get('subject'), subject) and r.get('kind') == kind]
            need(len({r['session'] for r in rows}) == 2, 'REVIEWS_MUST_BE_INDEPENDENT_SESSIONS')
            need(len({r['review']['sha256'] for r in rows}) == 2 and
                 len({r['rawSessionEvidence']['sha256'] for r in rows}) == 2, 'DISTINCT_ACTUAL_REVIEW_ORIGINS')

    def tool(self, descriptor, subject):
        entries = [r for r in self.value['tools'] if same(r.get('witness'), descriptor)]
        need(len(entries) == 1, 'AUTHENTIC_ACTUAL_TOOL_WITNESS_REQUIRED')
        entry = entries[0]
        closed(entry, 'witness operator launchSession launchResponse completionResponse')
        need(entry['operator'] in self.forbidden, 'TOOL_OPERATOR_DISCLOSURE')
        value = self.files.doc(descriptor)
        closed(value, 'schema runId operator interpreter argv startedUtcNs finishedUtcNs launchSession launchResponse completionResponse naturalExitCode transcript')
        equal(value['schema'], 'e02-minimum-outer-witness-v1'); equal(value['runId'], subject['runId'])
        for key in ('operator', 'launchSession', 'launchResponse', 'completionResponse'):
            equal(value[key], entry[key])
        integer(value['startedUtcNs'], 0, I64); integer(value['finishedUtcNs'], value['startedUtcNs'], I64)
        equal(value['naturalExitCode'], 0)
        for key in ('launchResponse', 'completionResponse', 'transcript'):
            need(self.files.read(value[key]), 'EMPTY_TOOL_RESPONSE')
        self.files.read(value['interpreter'], 67108864)
        argv = value['argv']
        need(type(argv) is list and all(type(a) is str for a in argv), 'ACTUAL_ARGV')
        # Keep actual fixed argument order rather than normalizing history.
        need(argv[:3] in ([value['interpreter']['path'], '-I', '-B'],), 'FIXED_ISOLATED_PYTHON_FLAGS')
        equal(argv, [value['interpreter']['path'], '-I', '-B', subject['supervisorSource']['path'],
              '--config', subject['runConfig']['path'], '--config-sha', subject['runConfig']['sha256'],
              '--release', subject['runRelease']['path'], '--release-sha', subject['runRelease']['sha256'],
              '--out', subject['outputRoot']], 'EXACT_ACTUAL_LAUNCH_ARGV')
        return value


def lease_check(files, descriptor, run_id, release, tool):
    lease = files.doc(descriptor)
    closed(lease, 'schema runId bootId issuedUtcNs deadlineUtcNs issuedMonoNs deadlineMonoNs issuedBootNs deadlineBootNs')
    equal(lease['schema'], 'e02-single-cell-lease-v1'); equal(lease['runId'], run_id)
    text(lease['bootId'], 64)
    durations = []
    for clock in ('Utc', 'Mono', 'Boot'):
        issued, deadline = lease['issued' + clock + 'Ns'], lease['deadline' + clock + 'Ns']
        integer(issued, 0, I64); integer(deadline, issued + 1, I64)
        durations.append(deadline - issued)
    need(len(set(durations)) == 1 and 60_000_000_000 <= durations[0] <= 1_800_000_000_000,
         'ORIGINAL_LEASE_BUDGET')
    need(release['issuedAtUtcNs'] <= lease['issuedUtcNs'] < lease['deadlineUtcNs'] <= release['notAfterUtcNs'], 'GRANT_LEASE_INTERVAL')
    # Cleanup is a separately bounded exact-owned expiry exception. Do not turn
    # its legitimate post-deadline completion into a fabricated runtime renewal.
    need(tool['startedUtcNs'] <= lease['issuedUtcNs'] <= tool['finishedUtcNs'], 'ACTUAL_OUTER_LEASE_ORDER')
    return lease


COMMAND_KEYS = 'argv launchAttempt pid exit reaped forced timedOut error stdout stderr observedBytes stdoutEOF stderrEOF'


def commands(files, descriptors, root):
    need(type(descriptors) is list and 1 <= len(descriptors) <= 4096, 'COMMAND_INVENTORY_BOUND')
    result = []
    for i, descriptor in enumerate(descriptors, 1):
        equal(descriptor['path'], str(Path(root) / ('commands/%04d.json' % i)), 'COMPLETE_ORDERED_COMMAND_INVENTORY')
        c = files.doc(descriptor); closed(c, COMMAND_KEYS)
        need(type(c['argv']) is list and c['argv'] and len(c['argv']) <= 512, 'COMMAND_ARGV_BOUND')
        for a in c['argv']: text(a, 8192)
        for key in ('launchAttempt', 'reaped', 'stdoutEOF', 'stderrEOF'): equal(c[key], True)
        for key in ('forced', 'timedOut'): equal(c[key], False)
        equal(c['exit'], 0); equal(c['error'], None); integer(c['pid'], 1)
        closed(c['observedBytes'], 'stdout stderr')
        for stream in ('stdout', 'stderr'):
            raw = files.read(c[stream])
            equal(c['observedBytes'][stream], len(raw), 'COMMAND_RAW_STREAM_COUNT')
            equal(c[stream]['path'], str(Path(root) / ('commands/%04d.%s' % (i, stream))))
        result.append(c)
    return result


def cleanup_check(files, result, root):
    closed(result, 'ok rows errors evidence'); equal(result['ok'], True); equal(result['errors'], [])
    original = files.doc(result['evidence'])
    equal(original, {k: result[k] for k in ('ok', 'rows', 'errors')})
    rows = result['rows']
    need(type(rows) is list and len(rows) == 4 and {r['role'] for r in rows} == {'anchor', 'android', 'fixture', 'rs-relay'}, 'ALL_FOUR_OWNED_CLEANUP')
    cids = set()
    for row in rows:
        closed(row, 'role exactOwnedCleanupOnly errors identityVerified absenceConfirmed inspectExit cid logsExit removeExit afterInspectExit')
        for key in ('exactOwnedCleanupOnly', 'identityVerified', 'absenceConfirmed'): equal(row[key], True)
        equal(row['errors'], [])
        for key in ('inspectExit', 'logsExit', 'removeExit'): equal(row[key], 0)
        equal(row['afterInspectExit'], 1, 'ACTUAL_ABSENCE_EXIT')
        hx(row['cid']); need(row['cid'] not in cids, 'DISTINCT_OWNED_CIDS'); cids.add(row['cid'])
        prefix = str(Path(root) / 'cleanup' / row['role'])
        raw = lambda suffix: files.read(files.pins[prefix + suffix])
        inspected = files.doc(files.pins[prefix + '-inspect.stdout'])
        need(type(inspected) is list and len(inspected) == 1, 'ACTUAL_CLEANUP_INSPECT')
        equal(inspected[0]['Id'], row['cid'])
        equal(inspected[0]['Config']['Labels']['nbdp.role'], row['role'])
        equal(inspected[0]['Config']['Labels']['nbdp.run'], Path(root).name)
        equal(raw('-inspect.stderr'), b''); equal(raw('-remove.stderr'), b'')
        equal(raw('-remove.stdout').strip(), row['cid'].encode())
        equal(raw('-after-inspect.stdout').strip(), b'[]')
        need(re.fullmatch(rb'(?i:error: no such object: |error response from daemon: no such container: )'
                         + re.escape(row['cid'].encode()), raw('-after-inspect.stderr').rstrip(b'\r\n')),
             'ACTUAL_EXACT_CID_ABSENCE_RAW')
    return cids


PY = ['/guard-python/lib/ld-linux-x86-64.so.2', '--inhibit-cache', '--library-path',
      '/guard-python/lib', '/guard-python/bin/python3.11', '-B', '-P', '-S', '-s']
LIMITS = {'anchor': (128, 64, 1), 'rs-relay': (512, 128, 1), 'fixture': (1024, 128, 1), 'android': (8192, 512, 8)}


def allowed_adb(args, role):
    """Closed frozen-profile DATA grammar, never dispatches an ADB command."""
    package, helper = 'com.vitorpamplona.amethyst.debug', 'org.nbdp.clipboard.capture'
    if args in (['wait-for-device'], ['reverse', 'tcp:17777', 'tcp:17777'], ['reverse', '--list'],
                ['install', '--no-streaming', '/artifact.apk'], ['install', '-t', '--no-streaming', '/helper.apk'],
                ['exec-out', 'screencap', '-p']): return True
    if len(args) == 5 and args[:4] == ['exec-out', 'run-as', helper, 'cat']:
        return args[4] in ['files/captures/' + stage + suffix for stage in
                          (('incoming-business', 'incoming-ordinary-chat') if role == 'incoming' else
                           ('archive-business', 'archive-identical-replay', 'archive-fresh-wrap-replay'))
                          for suffix in ('.clear.json', '.receipt.json', '.raw.json')]
    if not args or args[0] != 'shell': return False
    a = args[1:]
    if a in (['uiautomator', 'dump', '/sdcard/nbdp-window.xml'], ['cat', '/sdcard/nbdp-window.xml'], ['date', '-u'],
             ['monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1'],
             ['pm', 'clear', helper], ['pm', 'clear', package],
             ['am', 'start', '-W', '-n', package + '/com.vitorpamplona.amethyst.ui.MainActivity'],
             ['pm', 'path', package], ['pm', 'path', helper]): return True
    if len(a) == 2 and a[0] == 'getprop': return a[1] in ('sys.boot_completed', 'ro.build.fingerprint', 'ro.build.version.sdk')
    if len(a) == 8 and a[:7] == ['am', 'start', '-W', '-n', helper + '/.CaptureActivity', '--es', 'caseId']:
        return a[7] in (('incoming-business', 'incoming-ordinary-chat') if role == 'incoming' else
                        ('archive-business', 'archive-identical-replay', 'archive-fresh-wrap-replay'))
    if len(a) < 3 or a[0] != 'input': return False
    op, values = a[1], a[2:]
    if op in ('tap', 'swipe'):
        return len(values) == (2 if op == 'tap' else 5) and all(re.fullmatch('[0-9]{1,4}', x) and int(x) <= 5000 for x in values)
    if op == 'text':
        nsec = ('nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqpqptcfk2' if role == 'incoming' else
                'nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqsmhltgl')
        return values in ([nsec], ['ws://localhost:17777'])
    return op == 'keyevent' and values in ([x] for x in ('4', '61', '66', '67', '111'))


def ownership(files, subject, config, fixture, rows):
    """Join actual IDs, intent, strict inspect, mounts and finite command grammar."""
    root = Path(subject['outputRoot'])
    def doc(relative): return files.doc(files.pins[str(root / relative)])
    owned, entries = {}, {}
    for role in LIMITS:
        intent = doc('ownership/' + role + '-intent.json')
        closed(intent, 'name image labels mounts command')
        closed(intent['labels'], 'nbdp.run nbdp.role nbdp.creation')
        equal(intent['labels']['nbdp.run'], subject['runId']); equal(intent['labels']['nbdp.role'], role)
        need(re.fullmatch('[0-9a-f]{32}', intent['labels']['nbdp.creation']), 'CREATION_NONCE')
        equal(intent['name'], 'nbdp-e02-' + subject['runId'] + '-' + role)
        equal(intent['image'], config['relayImage'] if role == 'rs-relay' else config['runtimeImage'])
        equal(intent['command'], [*PY[1:], '/input/supervisor.py', '--guest', role])
        cid = doc('ownership/' + role + '-cid.json'); closed(cid, 'id'); hx(cid['id'])
        need(cid['id'] not in owned, 'CID_REUSE'); owned[cid['id']] = role; entries[role] = (cid['id'], intent)
    anchor = entries['anchor'][0]
    for role, (cid, entry) in entries.items():
        expected = [[str(root / 'input'), '/input', False], [str(root / 'session/lease.json'), '/session/lease.json', False],
                    [str(root / 'session/control'), '/session/control', True]]
        if role == 'android':
            expected += [[config['sdkRoot'], '/sdk', False], [config['amethystApk']['path'], '/artifact.apk', False],
                         [config['helperApk']['path'], '/helper.apk', False], [str(root / 'android-state'), '/state', True]]
        if role == 'rs-relay':
            expected += [[config['guardBundleRoot'], '/guard-python', False], [config['relayConfig']['path'], '/src/config.toml', False],
                         [str(root / 'relay-data'), '/data', True]]
        if role == 'fixture':
            expected += [[str(root / 'session/fixtures'), '/session/fixtures', True],
                         ['/home/peterhorvath/apps/bitcoin/NBDP/experiments/node_modules', '/input/node_modules', False]]
            expected += [[p['source'], p['path'], False] for p in fixture['pins'].values()]
        equal(entry['mounts'], expected, 'EXACT_FROZEN_MOUNTS')
        inspections = [doc('ownership/' + role + '-initial-inspect.json')]
        for c in rows:
            if c['argv'] == ['/usr/bin/docker', 'inspect', cid]:
                actual = files.doc(c['stdout']); need(len(actual) == 1, 'ONE_ACTUAL_INSPECT'); inspections.append(actual[0])
        for d in inspections:
            equal(d['Id'], cid); equal(d['Name'], '/' + entry['name']); equal(d['Image'], entry['image'])
            for key, value in entry['labels'].items(): equal(d['Config']['Labels'][key], value)
            hc = d['HostConfig']; memory, pids, cpus = LIMITS[role]
            equal(hc['NetworkMode'], 'none' if role == 'anchor' else 'container:' + anchor)
            for key in ('Privileged',): equal(hc[key], False)
            need(not hc.get('PortBindings') and not hc.get('CapAdd'), 'NO_NETWORK_OR_EXTRA_CAPS')
            equal(hc['ReadonlyRootfs'], True); need('ALL' in hc['CapDrop'], 'DROP_ALL_CAPS')
            need(any('no-new-privileges' in x for x in hc['SecurityOpt']), 'NO_NEW_PRIVILEGES')
            equal(hc['Memory'], memory * 1048576); equal(hc['MemorySwap'], memory * 1048576)
            equal(hc['PidsLimit'], pids); equal(hc['NanoCpus'], cpus * 1000000000)
            equal(d['State']['Running'], True)
            equal(d['Config']['Entrypoint'], [PY[0]]); equal(d['Config']['Cmd'], entry['command'])
            need(re.fullmatch('[1-9][0-9]{0,9}:[0-9]{1,10}', d['Config']['User']), 'ACTUAL_NONROOT_USER')
            env = dict(v.split('=', 1) for v in d['Config']['Env'] if '=' in v)
            need(not any(k in env for k in ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY')), 'NO_HOST_GUI_CLIPBOARD_BRIDGE')
            equal(env['NBDP_LEASE_SHA256'], subject['lease']['sha256'])
            equal(env['NBDP_MINIMUM_RUN_CONFIG_SHA256'], subject['runConfig']['sha256'])
            fixture_pin = next(p for p in config['sourceAndDependencyPins'] if Path(p['path']).name == 'fixture-plan.json')
            equal(env['NBDP_FIXTURE_PLAN_SHA256'], fixture_pin['sha256'])
            equal(sorted((m['Source'], m['Destination'], m['RW']) for m in d['Mounts'] if m['Type'] == 'bind'),
                  sorted(tuple(m) for m in expected), 'ACTUAL_MOUNT_SET')
            equal(hc.get('Devices') or [], [{'PathOnHost': '/dev/kvm', 'PathInContainer': '/dev/kvm', 'CgroupPermissions': 'rw'}] if role == 'android' else [])
    creates, starts = set(), set()
    for c in rows:
        argv = c['argv']; need(argv[0] == '/usr/bin/docker' and len(argv) >= 3, 'CLOSED_DOCKER_JOURNAL')
        op = argv[1]
        if op == 'inspect':
            need(len(argv) == 3 and argv[2] in owned, 'EXACT_OWNED_INSPECT')
        elif op == 'start':
            need(len(argv) == 3 and argv[2] in owned and argv[2] not in starts, 'EXACT_ONCE_START'); starts.add(argv[2])
        elif op == 'create':
            cid = files.read(c['stdout']).decode().strip()
            need(cid in owned and cid not in creates, 'EXACT_ONCE_CREATE'); creates.add(cid)
            entry = entries[owned[cid]][1]
            need('--name' in argv and argv[argv.index('--name') + 1] == entry['name'], 'CREATE_NAME_JOIN')
            initial = doc('ownership/' + owned[cid] + '-initial-inspect.json')
            need('--user' in argv and argv[argv.index('--user') + 1] == initial['Config']['User'], 'CREATE_ACTUAL_USER_JOIN')
            equal(argv[-len(entry['command']) - 1:], [entry['image'], *entry['command']])
        elif op == 'exec':
            if len(argv)==8 and argv[2]=='--env':
                need(re.fullmatch(r'NBDP_CONTROLLER_AUDIT_SLOT=(?:[1-9]|[1-5][0-9]|6[0-4])',argv[3]) is not None,'CLOSED_ASSIGNED_AUDIT_SLOT')
                need(argv[4] in owned and owned[argv[4]]=='fixture','EXACT_OWNED_CONTROLLER_EXEC')
                equal(argv[5:7],['/usr/local/bin/node','/input/fixture.mjs'])
                need(argv[7] in ('prepare','status','publish'),'CLOSED_FIXTURE_EXEC')
                continue
            need(argv[2] in owned, 'EXACT_OWNED_EXEC'); role = owned[argv[2]]
            prefix = [*PY, '/input/lease_guard.py', 'exec', subject['lease']['sha256']]
            equal(argv[3:3 + len(prefix)], prefix, 'EXACT_GUEST_GUARD')
            payload = argv[3 + len(prefix):]
            need(role == 'android' and payload, 'EXACT_ANDROID_GUARD')
            need((payload[0] == 'adb' and allowed_adb(payload[1:], subject['ordinaryRole'])) or
                 payload in (['probe', 'ip', '-j', 'addr'], ['probe', 'ss', '-H', '-lnt']), 'CLOSED_GUEST_PAYLOAD')
        else:
            need(False, 'UNPLANNED_DOCKER_OPERATION')
    equal(creates, set(owned)); equal(starts, set(owned))
    return set(owned)
