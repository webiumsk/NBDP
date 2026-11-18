"""SOURCE PREPARATION ONLY: complete window DATA fixtures, never runtime evidence.

The builder exercises the shared strict consumer._window_data() body with actual Files,
Origin, wire, observer and GUI validators. Every process/tool/review/socket/PNG
operand it creates is synthetic DATA. The fixture cannot authenticate a run and
must never be submitted to the production-facing evidence CLI as real evidence.

It deliberately does NOT exercise consume(): consume pins a genuine immutable
producer/control closure whose missing external operands cannot be fabricated.
Execution requires a separate coordinator release after source review.
"""
import base64
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


SOURCE_NAMES = ('supervisor.py', 'lease_guard.py', 'android_driver.py', 'ui-plan.json',
    'fixture.mjs', 'fixture-plan.json', 'minimum-plan.json', 'business-rumor.json',
    'chat-rumor.json', 'exchange.mjs', 'phase-writer.mjs', 'dependency-tree.mjs',
    'dependency-tree.json', 'capture-budget.mjs', 'exchange-adapter.mjs', 'proxy-observer.mjs',
    'guard-helper.py','guard-wire.mjs','guard-client-core.mjs','guard-client.mjs',
    'guard-transport-boundaries.mjs','capture-allocation.mjs')
MODEL_ACTOR = '/root/SYNTHETIC_MODEL_OPERATOR_NOT_AN_ACTUAL_SESSION'


def components(consumer_dir):
    """Import only at explicitly released execution time, never source preparation."""
    folder = Path(consumer_dir).resolve()
    if folder!=Path(__file__).resolve().parent or not folder.is_dir():
        raise ValueError('EXPLICIT_CONSUMER_SOURCE_DIRECTORY_REQUIRED')
    names = ('strict', 'wire', 'gui', 'witness', 'observer', 'consumer', 'test_data_controls', 'model_stage')
    for name in names:
        if name in sys.modules:
            raise ValueError('MODEL_REQUIRES_FRESH_PROCESS_WITHOUT_PRELOADED_CONSUMER_MODULES')
    sys.path.insert(0, str(folder))
    result = {name: importlib.import_module(name) for name in names}
    for name, module in result.items():
        if Path(module.__file__).resolve().parent != folder:
            raise ValueError('CONSUMER_MODULE_SOURCE_ESCAPE:' + name)
    return result


class Model:
    """Owned local files with real byte/hash pins; no mocked Files methods."""
    def __init__(self, root, modules, producer_dir, role):
        self.base, self.m, self.role = Path(root), modules, role
        self.producer_dir = Path(producer_dir).resolve()
        self.w, self.g, self.s = modules['wire'], modules['gui'], modules['strict']
        self.run_id = ('1' if role == 'incoming' else '2') * 32
        self.root = self.base / self.run_id
        for name in ('commands', 'ui', 'evidence', 'session/fixtures', 'session/control', 'cleanup', 'ownership', 'input'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.cids = {name: hashlib.sha256((self.run_id + name).encode()).hexdigest()
                     for name in modules['witness'].LIMITS}
        self.command_pins, self.command_rows, self.ui, self.fixture_call_pins = [], [], [], []
        self.phase_rows, self.proxy_rows = [], []
        self.marker = 'SYNTHETIC_DATA_ONLY_NO_ACTUAL_PROCESS_TOOL_OR_REVIEW'

    def raw(self, path, value):
        path = Path(path)
        if not path.is_absolute(): path = self.root / path
        if not path.is_relative_to(self.base): raise ValueError('MODEL_WRITE_ESCAPE')
        path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, 'wb') as stream: stream.write(value)
        return self.pin(path)

    def put(self, path, value): return self.raw(path, self.s.json_bytes(value))

    @staticmethod
    def pin(path):
        path = Path(path); raw = path.read_bytes()
        return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def read(self, pin): return Path(pin['path']).read_bytes()
    def doc(self, pin): return json.loads(self.read(pin))

    def command(self, argv, stdout=b''):
        index = len(self.command_rows) + 1
        if isinstance(stdout, dict): stdout = self.read(stdout)
        if not isinstance(stdout, bytes): raise TypeError('MODEL_COMMAND_STDOUT_BYTES')
        out = self.raw('commands/%04d.stdout' % index, stdout)
        err = self.raw('commands/%04d.stderr' % index, b'')
        row = dict(argv=argv, launchAttempt=True, pid=10000 + index, exit=0, reaped=True,
                   forced=False, timedOut=False, error=None, stdout=out, stderr=err,
                   observedBytes=dict(stdout=len(stdout), stderr=0), stdoutEOF=True, stderrEOF=True)
        descriptor = self.put('commands/%04d.json' % index, row)
        self.command_rows.append(row); self.command_pins.append(descriptor)
        return index, descriptor, out

    def adb(self, tail, stdout=b''):
        prefix = [*self.m['witness'].PY, '/input/lease_guard.py', 'exec', self.lease_pin['sha256']]
        return self.command(['/usr/bin/docker', 'exec', self.cids['android'], *prefix, 'adb', *tail], stdout)

    def probe(self, tail, stdout):
        prefix = [*self.m['witness'].PY, '/input/lease_guard.py', 'exec', self.lease_pin['sha256']]
        return self.command(['/usr/bin/docker', 'exec', self.cids['android'], *prefix, *tail], stdout)

    def phase(self, name, context=None, **fields):
        row = dict(schema='e02-transport-query-phase-v2', sequence=len(self.phase_rows) + 1,
                   utc='2026-10-26T00:00:00.000Z', monotonicNanoseconds=str(len(self.phase_rows) + 1),
                   phase=name, profileId=self.w.PROFILE, windowId=self.w.WINDOWS[self.role],
                   ordinaryRole=self.role, observedAttempt=copy.deepcopy(context), **fields)
        self.phase_rows.append(row)
        return row

    def guard(self, label, context=None):
        self.phase('GUARD_ENTRY', context, label=label)
        self.phase('GUARD_EXIT', context, label=label, ok=True, error=None)

    def proxy(self, direction, **fields):
        row = dict(schema='e02-minimum-proxy-row-v1', sequence=len(self.proxy_rows) + 1,
                   utc='2026-10-26T00:00:00.000Z', direction=direction, **fields)
        self.proxy_rows.append(row)
        return row

    def state(self, phase_end=None, proxy_end=None):
        phase_end = len(self.phase_rows) if phase_end is None else phase_end
        proxy_end = len(self.proxy_rows) if proxy_end is None else proxy_end
        phase = [self.s.json_bytes(r) + b'\n' for r in self.phase_rows[:phase_end]]
        proxy = [self.s.json_bytes(r) + b'\n' for r in self.proxy_rows[:proxy_end]]
        pbytes, rbytes, last = sum(map(len, phase)), sum(map(len, proxy)), phase[-1]
        from async_guard import ALLOCATION,PROOF_LIMIT
        retained=sum(p.stat().st_size for p in (self.root/'session/fixtures').rglob('*') if p.is_file() and p not in {self.root/'session/fixtures'/name for name in ('capture.jsonl','phase-trace.jsonl','observer-final-state.json')})
        charged=pbytes+rbytes+retained+65536
        return dict(schema='e02-minimum-observer-state-v3',allocation=ALLOCATION,serviceHeaderPrepaidBytes=4096,serviceDiagnostics=dict(limit=4096,chargedBytes=0,intendedBytes=0,poisoned=False,firstError=None),
            budget=dict(schema='e02-minimum-aggregate-capture-budget-v3', limit=self.m['observer'].LIMIT,
                intendedTotalBytes=pbytes + rbytes, acknowledgedTotalBytes=pbytes + rbytes,
                streams=dict(phase=dict(intended=pbytes, acknowledged=pbytes), proxy=dict(intended=rbytes, acknowledged=rbytes)),
                poisoned=False, firstError=None, physicalBytes=None,
                physicalMeaning='ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION',
                allocationAccount=dict(limit=PROOF_LIMIT,chargedBytes=charged,intendedBytes=charged,poisoned=False,firstError=None),
                lastAttempt=dict(stream='phase', intendedBytes=len(last), writeInvoked=True, reportedCount=len(last),
                    acknowledgedBytes=len(last), acknowledgedPrefixSha256=hashlib.sha256(last).hexdigest(), physicalBytes=None, error=None)),
            phase=dict(sequence=phase_end, intendedTotalBytes=pbytes, acknowledgedTotalBytes=pbytes,
                physicalBytes=None, physicalMeaning='NOT_INDEPENDENTLY_MEASURED_ACKNOWLEDGED_PREFIX_IS_NOT_PHYSICAL_ATTESTATION',
                poisoned=False, firstError=None, lastAttempt=dict(sequence=phase_end, phase=self.phase_rows[phase_end - 1]['phase'],
                    intendedBytes=len(last), writeInvoked=True, reportedCount=len(last), acknowledgedBytes=len(last),
                    acknowledgedPrefixBase64=base64.b64encode(last).decode(), physicalBytes=None, error=None)))

    def source_contract(self):
        """Use actual frozen scope and guard literals, not a duplicated imagined DTO."""
        cfg_path = self.producer_dir / (self.role + '-run-config.json')
        self.original_config = json.loads(cfg_path.read_bytes())
        self.runtime_scope = self.original_config['scope']
        source = (self.producer_dir / 'fixture.mjs').read_text()
        self.actual_proxy_labels = set(re.findall(r"serviceGuard\('(proxy:[^']+)'", source)) - {'proxy:server-create'}
        declared = set(self.m['observer'].PROXY_GUARD_LABELS)
        if self.actual_proxy_labels != declared:
            raise ValueError('SOURCE_DERIVED_GUARD_VOCABULARY_MISMATCH')
        if self.runtime_scope != self.m['consumer'].RUNTIME_SCOPE:
            raise ValueError('SOURCE_DERIVED_RUNTIME_SCOPE_MISMATCH')

    def source_inputs(self):
        self.source_contract()
        source_root = self.base / ('synthetic-producer-' + self.role)
        self.native_source = self.raw(source_root / 'model-rust-source.rs', b'SYNTHETIC_DATA_NOT_A_PRODUCER')
        self.native_binary = self.raw(source_root / 'model-rust-binary', b'SYNTHETIC_NOT_EXECUTED')
        fixture = copy.deepcopy(json.loads((self.producer_dir / 'fixture-plan.json').read_bytes()))
        fixture['pins'] = {}
        for name, pin, guest in (('rustSource', self.native_source, '/input/rust-source.rs'),
                                 ('rustBinary', self.native_binary, '/input/rust-binary')):
            fixture['pins'][name] = dict(path=guest, source=pin['path'], bytes=pin['bytes'], sha256=pin['sha256'])
        self.fixture, self.sources = fixture, []
        for name in SOURCE_NAMES:
            raw = self.s.json_bytes(fixture) if name == 'fixture-plan.json' else (self.producer_dir / name).read_bytes()
            self.sources.append(self.raw(source_root / name, raw))
            self.raw('input/' + name, raw)
        self.source_by_name = {Path(p['path']).name: p for p in self.sources}
        self.producer_pin = self.put(source_root / 'synthetic-producer-subject.json',
            dict(schema='SYNTHETIC_MODEL_PRODUCER_NOT_THE_REAL_HASH_PINNED_PRODUCER', marker=self.marker))
        cfg = copy.deepcopy(self.original_config)
        cfg.update(runId=self.run_id, sourceAndDependencyPins=self.sources)
        for key in ('sdkInventory', 'guardBundleInventory', 'relayConfig'):
            cfg[key] = self.put(source_root / (key + '.json'), dict(marker=self.marker, purpose=key))
        self.config, self.config_pin = cfg, self.put(source_root / 'synthetic-run-config.json', cfg)
        self.producer = dict(sources=self.sources,runtimeSources=self.sources,configurations={self.role:self.config_pin})
        self.controls_pin = self.put(source_root / 'synthetic-controls.json', dict(marker=self.marker))
        self.candidate = dict(producerSubject=self.producer_pin, sourceControls=self.controls_pin,
            oracles={key: self.source_by_name[key + '-rumor.json'] for key in ('business', 'chat')})

    def reviews(self, subject, kind):
        rows = []
        for role in ('qa', 'security'):
            actor = '/root/SYNTHETIC_' + role.upper() + '_MODEL_NOT_ACTUAL_REVIEW'
            suffix = kind.lower() + '-' + role
            # These are deliberately model strings, never coordinator transcripts.
            review = self.raw(self.base / self.role / (suffix + '-model-review.txt'), (self.marker + ':REVIEW:' + suffix).encode())
            raw = self.raw(self.base / self.role / (suffix + '-model-origin.txt'), (self.marker + ':ORIGIN:' + suffix).encode())
            rows.append(dict(kind=kind, role=role, actor=actor, session=actor, subject=subject,
                decision='ACCEPT_EXACT_SCOPED_EVIDENCE', findings=[], review=review, rawSessionEvidence=raw,
                visualChecks=['actual-account-gui', 'tor-off-saved-reopened', 'all-window-selected-note-pngs',
                              'helper-clear-copy-capture-custody'] if kind == 'WINDOW' else []))
        return rows

    def admission(self):
        self.source_reviews = self.reviews(self.producer_pin, 'SOURCE')
        raw = self.raw(self.base / self.role / 'synthetic-admission.txt', self.marker.encode())
        ns = 1000000000000 if self.role == 'incoming' else 3000000000000
        lease = dict(schema='e02-single-cell-lease-v1', runId=self.run_id, bootId='synthetic-model-boot',
            issuedUtcNs=ns + 10, deadlineUtcNs=ns + 1800000000010,
            issuedMonoNs=10, deadlineMonoNs=1800000000010, issuedBootNs=10, deadlineBootNs=1800000000010)
        self.lease_pin = self.put('session/lease.json', lease)
        release = dict(schema='e02-ordinary-minimum-role-release-v2', executionAuthorized=True,
            rootSession=MODEL_ACTOR, executionSession=MODEL_ACTOR, runId=self.run_id, scope=self.runtime_scope,
            profileId=self.w.PROFILE, ordinaryRole=self.role, windowId=self.w.WINDOWS[self.role],
            runConfig=self.config_pin, sourceSubject=self.producer_pin, issuedAtUtcNs=ns,
            notAfterUtcNs=ns + 1800000000020, qaReview=self.source_reviews[0]['review'],
            securityReview=self.source_reviews[1]['review'], guardRegressionEvidence=raw,
            freshResourceAdmission=raw, resourcePrerequisite=raw, limits=self.marker)
        self.release_pin = self.put(self.base / self.role / 'synthetic-release-model.json', release)
        resource = dict(schema='e02-minimum-resource-witness-v1', runId=self.run_id,
            measuredAtUtcNs=ns - 1, outputFilesystem=str(self.root), freeBytes=8 * 1024 ** 3,
            memAvailableBytes=12 * 1024 ** 3, affinityCpus=8, kvmAccessible=True, rawReceipt=raw,
            sourceIndex=self.config['sdkInventory'], actualAdmissionMeaning='ACTUAL_CURRENT_ADMISSION_NOT_MINIMUM_OR_PEAK_OR_GUEST_HEALTH')
        self.resource_pin = self.put('evidence/synthetic-resource-model.json', resource)
        self.ns = ns

    def containers(self):
        fixture_pin = self.source_by_name['fixture-plan.json']
        for role, cid in self.cids.items():
            mounts = [[str(self.root / 'input'), '/input', False], [str(self.root / 'session/lease.json'), '/session/lease.json', False],
                      [str(self.root / 'session/control'), '/session/control', True]]
            if role == 'android': mounts += [[self.config['sdkRoot'], '/sdk', False],
                [self.config['amethystApk']['path'], '/artifact.apk', False], [self.config['helperApk']['path'], '/helper.apk', False],
                [str(self.root / 'android-state'), '/state', True]]
            if role == 'rs-relay': mounts += [[self.config['guardBundleRoot'], '/guard-python', False],
                [self.config['relayConfig']['path'], '/src/config.toml', False], [str(self.root / 'relay-data'), '/data', True]]
            if role == 'fixture': mounts += [[str(self.root / 'session/fixtures'), '/session/fixtures', True],
                ['/home/peterhorvath/apps/bitcoin/NBDP/experiments/node_modules', '/input/node_modules', False],
                *[[p['source'], p['path'], False] for p in self.fixture['pins'].values()]]
            image = self.config['relayImage'] if role == 'rs-relay' else self.config['runtimeImage']
            labels = {'nbdp.run': self.run_id, 'nbdp.role': role, 'nbdp.creation': '3' * 32}
            name = 'nbdp-e02-' + self.run_id + '-' + role
            command = [*self.m['witness'].PY[1:], '/input/supervisor.py', '--guest', role]
            self.put('ownership/' + role + '-intent.json', dict(name=name, image=image, labels=labels, mounts=mounts, command=command))
            self.put('ownership/' + role + '-cid.json', dict(id=cid))
            memory, pids, cpus = self.m['witness'].LIMITS[role]
            inspect = dict(Id=cid, Name='/' + name, Image=image, Config=dict(Labels=labels, User='1000:1000',
                Entrypoint=[self.m['witness'].PY[0]], Cmd=command, Env=['NBDP_LEASE_SHA256=' + self.lease_pin['sha256'],
                    'NBDP_MINIMUM_RUN_CONFIG_SHA256=' + self.config_pin['sha256'], 'NBDP_FIXTURE_PLAN_SHA256=' + fixture_pin['sha256']]),
                HostConfig=dict(NetworkMode='none' if role == 'anchor' else 'container:' + self.cids['anchor'],
                    Privileged=False, PortBindings={}, CapAdd=[], ReadonlyRootfs=True, CapDrop=['ALL'],
                    SecurityOpt=['no-new-privileges'], Memory=memory * 1048576, MemorySwap=memory * 1048576,
                    PidsLimit=pids, NanoCpus=cpus * 1000000000,
                    Devices=[dict(PathOnHost='/dev/kvm', PathInContainer='/dev/kvm', CgroupPermissions='rw')] if role == 'android' else []),
                State=dict(Running=True), Mounts=[dict(Type='bind', Source=a, Destination=b, RW=c) for a, b, c in mounts])
            self.put('ownership/' + role + '-initial-inspect.json', inspect)
            self.command(['/usr/bin/docker', 'create', '--name', name, '--user', '1000:1000', image, *command], cid.encode() + b'\n')
            self.command(['/usr/bin/docker', 'start', cid], cid.encode() + b'\n')
        for name, tail, raw in (
            ('ro.build.version.sdk.txt', ['shell', 'getprop', 'ro.build.version.sdk'], b'35\n'),
            ('ro.build.fingerprint.txt', ['shell', 'getprop', 'ro.build.fingerprint'],
             b'Android/sdk_phone64_x86_64/emu64x:15/AE3A.240806.019/12368160:userdebug/test-keys\n')):
            self.raw('evidence/' + name, raw); self.adb(tail, raw)
        network = self.s.json_bytes([dict(ifname='lo', flags=['LOOPBACK'], addr_info=[dict(local='127.0.0.1', family='inet', scope='host', prefixlen=8)])])
        self.raw('evidence/network-addresses.json', network); self.probe(['probe', 'ip', '-j', 'addr'], network)
        listeners = b'LISTEN 0 128 127.0.0.1:17777 0.0.0.0:*\n'
        self.raw('evidence/listeners.txt', listeners); self.probe(['probe', 'ss', '-H', '-lnt'], listeners)
        self.adb(['shell', 'pm', 'clear', self.g.APP])

    def prepare(self):
        self.inboxes = []
        sent, ack = [], []
        label = 'prepare-inboxes'
        self.guard('exchange:' + label + ':exchange-entry')
        self.phase('EXCHANGE_START', label=label)
        self.phase('TIMER_ARMED', label=label, timeoutMilliseconds=10000)
        self.phase('SOCKET_OPEN_CALLBACK_ENTRY', label=label)
        self.guard('exchange:' + label + ':socket-open')
        for i, account in enumerate((self.w.A, self.w.B)):
            event = dict(pubkey=account, created_at=1, kind=10050, tags=[['relay', 'ws://127.0.0.1:17777']], content='', sig='0' * 128)
            event['id'] = hashlib.sha256(self.s.json_bytes([0, account, 1, 10050, event['tags'], ''])).hexdigest()
            self.inboxes.append(event)
            raw = self.s.json_bytes(['EVENT', event]); b64 = base64.b64encode(raw).decode()
            frame = self.raw('session/fixtures/' + label + '-%d-sent-frame.json' % i, raw)
            self.guard('exchange:' + label + ':send-before')
            self.phase('SEND_INTENT', label=label, eventId=event['id'], rawBase64=b64)
            self.proxy('PRODUCER_TO_RELAY', exchangeLabel=label, rawBase64=b64, frame=frame)
            self.phase('SEND_INVOKE_ENTRY', label=label, eventId=event['id'])
            self.phase('SEND_INVOKE_RETURNED', label=label, eventId=event['id'])
            self.phase('SEND_CALLBACK_ENTRY', label=label, eventId=event['id'], error=None)
            self.guard('exchange:' + label + ':send-callback')
            self.phase('SEND_CALLBACK_GUARD_PASSED', label=label, eventId=event['id'])
            sent.append(dict(frame=frame, eventId=event['id'], messageType='EVENT', sendInvoked=True,
                             sendCallbackCompleted=True, callbackBufferHash=hashlib.sha256(raw).hexdigest()))
            response = ['OK', event['id'], True, self.marker]
            b64 = base64.b64encode(self.s.json_bytes(response)).decode()
            self.phase('RAW_BACKEND_CALLBACK_ENTRY', label=label, rawBase64=b64)
            self.guard('exchange:' + label + ':backend-message')
            self.proxy('RELAY_TO_PRODUCER', exchangeLabel=label, rawBase64=b64)
            self.phase('BACKEND_MESSAGE_GUARD_PASSED', label=label, messageType='OK')
            ack.append(dict(rawBase64=b64, frame=response))
        self.inbox_result = dict(events=self.inboxes, ack=ack, received=[], eose=None, sentFrames=sent, elapsedNanoseconds=100)
        self.phase('EXCHANGE_RESOLVED', label=label, elapsedNanoseconds=100, error=None)
        self.put('session/fixtures/' + label + '-outcome.json', dict(label=label,
            **{k:v for k,v in self.inbox_result.items() if k != 'events'}, error=None, secondaryRetentionErrors=[], observer=self.state()))
        self.inbox_pin = self.put('session/fixtures/inboxes.json', self.inbox_result)

    def combine_stage(self, index):
        """Compose existing reviewed local publication graph; rebase all clocks/joins."""
        sid = self.w.STAGES[self.role][index]
        stage_root = self.root / 'session/fixtures/model-stage-data' / sid
        stage_root.mkdir(parents=True)
        fresh = self.role == 'archive' and index == 2
        data = self.m['model_stage'].graph(stage_root, self.role, index,
            not (self.role == 'archive' and index == 1), event_content='synthetic-fresh-wrap-placeholder' if fresh else None)
        _, window, _, record, expected, spec, role = data
        # Real frozen oracle bytes are used for rendered/export comparison. The
        # helper's normalized synthetic fixture must use these exact bytes too.
        real_expected = self.doc(self.candidate['oracles'][spec['oracle']])
        if expected != real_expected:
            self.rewrite_oracle(stage_root, expected, real_expected)
            record = self.replace_value(record, expected, real_expected)
            expected = real_expected
        local_proxy = [json.loads(line) for line in Path(window['proxy']['path']).read_bytes().splitlines()]
        local_phase = [json.loads(line) for line in Path(window['phase']['path']).read_bytes().splitlines()]
        proxy_offset, phase_offset, connection = len(self.proxy_rows), len(self.phase_rows), index + 1
        def rebase(value, context=''):
            if isinstance(value, list): return [rebase(x, context) for x in value]
            if not isinstance(value, dict): return value
            out = {}
            for key, val in value.items():
                if key in ('connection', 'nextConnection') and isinstance(val, int): out[key] = connection
                elif key in ('sequence', 'requestSequence', 'eoseSequence', 'sourceSequence', 'sentSequence', 'rowSequence', 'intentSequence', 'closeSequence') and isinstance(val, int):
                    out[key] = val + proxy_offset
                else: out[key] = rebase(val, key)
            return out
        self.proxy_rows += [rebase(row) for row in local_proxy]
        for row in local_phase:
            row = rebase(row)
            row['sequence'] = len(self.phase_rows) + 1
            row['monotonicNanoseconds'] = str(row['sequence'])
            self.phase_rows.append(row)
        record = rebase(record)
        # Re-pin the external DTOs whose sequences or canonical oracle changed.
        for key in ('intent', 'publicationWindow'):
            path = Path(record[key]['path'])
            value = rebase(json.loads(path.read_bytes()))
            if key == 'intent': self.pending_intents.append((record, key, value, path))
            record[key] = self.put(path, value)
        for key, suffix in (('publication', '-publish'), ('query', '-query')):
            label = sid + suffix
            old = json.loads((stage_root / 'session/fixtures' / (label + '-outcome.json')).read_bytes())
            phase_end = old['observer']['phase']['sequence'] + phase_offset
            local_proxy_bytes = old['observer']['budget']['streams']['proxy']['acknowledged']
            count, size = 0, 0
            for row in local_proxy:
                if size >= local_proxy_bytes: break
                size += len(self.s.json_bytes(row)) + 1; count += 1
            if size != local_proxy_bytes: raise ValueError('MODEL_LOCAL_PREFIX_BOUNDARY')
            self.put('session/fixtures/' + label + '-outcome.json', dict(label=label, **record[key],
                error=None, secondaryRetentionErrors=[], observer=self.state(phase_end, proxy_offset + count)))
        record['observation'] = dict(schema='e02-minimum-stage-observation-range-v2',
            phaseStartSequence=record['observation']['phaseStartSequence'] + phase_offset,
            phaseEndSequence=len(self.phase_rows), proxyEndSequence=len(self.proxy_rows), observer=self.state(),
            phaseTracePath='/session/fixtures/phase-trace.jsonl', proxyCapturePath='/session/fixtures/capture.jsonl',
            streamPins='FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS')
        native_pin = record['validation']['validation']; native = self.doc(native_pin)
        for name in ('rustBinary', 'rustSource'):
            p = self.fixture['pins'][name]
            native[name] = {k: p[k] for k in ('path', 'bytes', 'sha256')}
        record['validation']['validation'] = self.put(native_pin['path'], native)
        return record, expected, spec

    @staticmethod
    def replace_value(value, old, new):
        if value == old: return copy.deepcopy(new)
        try:
            old_envelope, new_envelope = json.loads(old['content']), json.loads(new['content'])
        except (KeyError, TypeError, json.JSONDecodeError):
            old_envelope = new_envelope = None
        if old_envelope is not None and value == old_envelope:
            return copy.deepcopy(new_envelope)
        if isinstance(value, dict): return {k: Model.replace_value(v, old, new) for k, v in value.items()}
        if isinstance(value, list): return [Model.replace_value(v, old, new) for v in value]
        if value == old.get('content'): return new['content']
        if value == old.get('id'): return new['id']
        return value

    def rewrite_oracle(self, root, old, new):
        """Rebuild nested pinned JSON references bottom-up, never forge a hash."""
        paths = sorted((p for p in root.rglob('*') if p.is_file()), key=lambda p: str(p))
        prior = {str(p): self.pin(p) for p in paths}
        replacements = {}
        def transform(value):
            if isinstance(value, dict) and set(value) == {'path', 'bytes', 'sha256'} and value['path'] in replacements:
                return replacements[value['path']]
            return self.replace_value(value, old, new)
        # All helper descriptors point to an acyclic file graph. Iterate at most
        # its depth; source preparation never executes this builder.
        for _ in range(16):
            changed = False
            for p in paths:
                raw = p.read_bytes()
                try:
                    if p.suffix == '.jsonl': values = [json.loads(x) for x in raw.splitlines()]
                    elif p.suffix == '.json': values = json.loads(raw)
                    else: continue
                except (UnicodeDecodeError, json.JSONDecodeError): continue
                def walk(v):
                    v = transform(v)
                    if isinstance(v, dict): return {k: walk(x) for k,x in v.items()}
                    if isinstance(v, list): return [walk(x) for x in v]
                    if isinstance(v, str):
                        # Native request.wire strings contain outer DATA only;
                        # source echo and base64 wire frames do not contain rumor.
                        return v
                    return v
                value = walk(values)
                newraw = b''.join(self.s.json_bytes(v) + b'\n' for v in value) if p.suffix == '.jsonl' else self.s.json_bytes(value)
                if newraw != raw: self.raw(p, newraw); changed = True
                replacements[str(p)] = self.pin(p)
            if not changed: break
        else: raise ValueError('MODEL_REFERENCE_REPIN_DID_NOT_CONVERGE')
        # The in-memory stage record is repaired by caller and descriptor pins
        # are resolved against actual updated bytes when final record is stored.
        self.changed_pins = {k: v for k,v in replacements.items() if v != prior[k]}

    def repin_tree(self, value):
        if isinstance(value, dict) and set(value) == {'path', 'bytes', 'sha256'} and Path(value['path']).is_file():
            return self.pin(value['path'])
        if isinstance(value, dict): return {k:self.repin_tree(v) for k,v in value.items()}
        if isinstance(value, list): return [self.repin_tree(v) for v in value]
        return value

    def wire_graph(self):
        self.prepare(); self.pending_intents, self.stages = [], []
        for index in range(len(self.w.STAGES[self.role])):
            record, expected, spec = self.combine_stage(index)
            self.stages.append([record, expected, spec])
        expected_map = {}
        for record, expected, spec in self.stages:
            name = spec['id']
            expected_map[name] = dict(stage=spec, rumor=self.candidate['oracles'][spec['oracle']],
                                     content=self.raw('session/fixtures/' + name + '-oracle-content.txt', expected['content'].encode()))
        self.prepared = dict(schema='e02-minimum-prepared-v2', profileId=self.w.PROFILE,
            windowId=self.w.WINDOWS[self.role], role=self.role,
            rumors={key:self.doc(pin) for key,pin in self.candidate['oracles'].items()},
            events=[r[0]['event'] for r in self.stages], expected=expected_map)
        self.prepared_pin = self.put('session/fixtures/prepared.json', self.prepared)
        for record, key, value, path in self.pending_intents:
            value['prepared'] = self.prepared_pin; record[key] = self.put(path, value)
        self.upgrade_async_service()
        self.proxy_pin = self.raw('session/fixtures/capture.jsonl', b''.join(self.s.json_bytes(r) + b'\n' for r in self.proxy_rows))
        self.phase_pin = self.raw('session/fixtures/phase-trace.jsonl', b''.join(self.s.json_bytes(r) + b'\n' for r in self.phase_rows))
        self.put('session/fixtures/observer-final-state.json',dict(observer=self.state(),snapshotTiming='BEFORE_THIS_FINAL_RECORD_WRITE',error=None,secondaryErrors=[],normalOwnedHelperClose=True))

    def parent_allocation_metadata(self):
        from async_guard import ALLOCATION
        binding_sha=hashlib.sha256(self.s.json_bytes(self.sources)).hexdigest()
        self.put('capture-allocation-header.json',dict(schema='e02-controller-capture-parent-allocation-v1',actor='/root',runId=self.run_id,runConfig=self.config_pin,sourceBindingsSha256=binding_sha,originalLeaseSha256=self.lease_pin['sha256'],allocation=ALLOCATION,ledgerRoot=str(self.root/'controller-audit-reservations'),ledgerBoundary='HOST_ONLY_OUTSIDE_FIXTURE_WRITABLE_MOUNTS',prechargedServiceBytes=8388608,controllerReservationsRefundable=False))
        count=len(self.fixture_call_pins)
        self.put('capture-allocation-status.json',dict(schema='e02-controller-capture-parent-status-v1',runId=self.run_id,controllerAttempts=count,controllerPoolPrechargedBytes=count*131072,servicePrechargedBytes=8388608,globalMaximumBytes=16777216,headerPrechargedLimit=4096,noRefunds=True,scope='CONSISTENCY_ONLY_NOT_POSTHOC_ADMISSION'))

    def upgrade_async_service(self):
        """Convert MODEL template events into fresh exact v3 retained DATA.

        No previous result is reused: every raw RPC, context hash, sequence,
        parent command and byte pin is newly modeled. This is synthetic fixture
        construction, not an authentic source run or historical evidence repair.
        """
        old=self.phase_rows;self.phase_rows=[];mapping={};counter=0
        instance=hashlib.sha256((self.run_id+':service').encode()).hexdigest()[:32]
        helper=self.source_by_name['guard-helper.py'];lease=self.doc(self.lease_pin)
        callback_names={'RAW_BACKEND_CALLBACK_ENTRY','SOCKET_OPEN_CALLBACK_ENTRY','SEND_CALLBACK_ENTRY','PROXY_CONNECTION_CALLBACK_ENTRY','PROXY_SOCKET_OPEN_CALLBACK_ENTRY','PROXY_RAW_CALLBACK_ENTRY','PROXY_SEND_CALLBACK_ENTRY'}
        def emit(name,fields,context=None):return self.phase(name,context,**fields)
        def previous_raw(i,label):
            if label.startswith('exchange:'):
                exchange,point=label[len('exchange:'):].rsplit(':',1)
                if point in ('exchange-entry','socket-open','constructor'):return exchange.encode()
                event='RAW_BACKEND_CALLBACK_ENTRY' if point=='backend-message' else 'SEND_INTENT'
                choices=[r for r in (old[i+2:] if point=='send-before' else old[:i]) if r['phase']==event and r.get('label')==exchange]
                if choices:return base64.b64decode(choices[-1 if point!='send-before' else 0]['rawBase64'])
            if label.startswith('proxy:'):
                origin='APP' if label in ('proxy:app-message','proxy:app-before-upstream-send','proxy:pending-before-upstream-send') else 'RELAY'
                choices=[r for r in old[:i] if r['phase']=='PROXY_RAW_CALLBACK_ENTRY' and r.get('origin')==origin]
                if label in ('proxy:app-send-callback','proxy:before-app-send','proxy:app-before-upstream-send','proxy:pending-before-upstream-send'):
                    signals=[r for r in (old[:i] if label=='proxy:app-send-callback' else old[i+2:]) if r['phase']==('PROXY_SEND_CALLBACK_ENTRY' if label=='proxy:app-send-callback' else 'PROXY_SEND_INVOKE_ENTRY')]
                    if signals:
                        signal=signals[-1] if label=='proxy:app-send-callback' else signals[0]
                        choices=[r for r in choices if hashlib.sha256(base64.b64decode(r['rawBase64'])).hexdigest()==signal['bufferHash']]
                if choices:return base64.b64decode(choices[-1]['rawBase64'])
            return self.s.json_bytes({'mode':'serve'})
        def begin(label,context,observed):
            nonlocal counter
            counter+=1;sequence=str(counter)
            emit('GUARD_ENTRY',dict(helperInstance=instance,label=label,guardSequence=sequence,enqueueMonoNs='100'),observed)
            if counter==1:
                emit('GUARD_HELPER_LAUNCH',dict(helperInstance=instance,executable='/guard-python/lib/ld-linux-x86-64.so.2',argv=['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/guard-helper.py',instance,self.lease_pin['sha256'],str(helper['bytes']),helper['sha256']]),observed)
                emit('GUARD_HELPER_CREATED',dict(helperInstance=instance,pid=12345),observed)
            operation='CLOSE' if label=='owner-close' else 'CHECK'
            request=dict(schema='e02-fresh-guard-request-v1',operation=operation,instance=instance,runId=self.run_id,leaseSha256=self.lease_pin['sha256'],sequence=sequence,label=label,contextSha256=hashlib.sha256(context).hexdigest())
            raw=self.s.json_bytes(request)+b'\n'
            emit('GUARD_RPC_REQUEST',dict(helperInstance=instance,label=label,guardSequence=sequence,rawBase64=base64.b64encode(raw).decode(),enqueueMonoNs='100',decisionDeadlineMonoNs='5000000100',enqueueUtcLowerNs=str(lease['issuedUtcNs']+100),enqueueBootLowerNs='100',decisionDeadlineUtcNs=str(lease['issuedUtcNs']+5000000100),decisionDeadlineBootNs='5000000100'),observed)
            reply=dict(request,schema='e02-fresh-guard-response-v1',requestSha256=hashlib.sha256(raw).hexdigest(),ok=True,clocks=None if operation=='CLOSE' else dict(Utc=str(lease['issuedUtcNs']+200),Mono='200',Boot='200',bootId=lease['bootId']))
            emit('GUARD_RPC_REPLY',dict(helperInstance=instance,guardSequence=sequence,rawBase64=base64.b64encode(self.s.json_bytes(reply)+b'\n').decode()),observed)
            return sequence
        def end(label,sequence,observed):
            return emit('GUARD_EXIT',dict(helperInstance=instance,label=label,guardSequence=sequence,ok=True,error=None,consumed=True,consumedUtcUpperNs=str(lease['issuedUtcNs']+300),consumedMonoNs='300',consumedBootUpperNs='300'),observed)
        i=0
        while i<len(old):
            row=old[i]
            if row['phase']!='GUARD_ENTRY':
                fields={k:v for k,v in row.items() if k not in ('schema','sequence','utc','monotonicNanoseconds','phase','profileId','windowId','ordinaryRole','observedAttempt')}
                mapping[row['sequence']]=emit(row['phase'],fields,row['observedAttempt'])['sequence'];i+=1;continue
            if i+1>=len(old) or old[i+1]['phase']!='GUARD_EXIT':raise ValueError('MODEL_TEMPLATE_GUARD_PAIR_REQUIRED')
            label=row['label'];label='flow:original-01' if label=='original-unlabeled' else label
            observed=row['observedAttempt'];mapping[row['sequence']]=len(self.phase_rows)+1
            token=begin(label,previous_raw(i,label),observed)
            j=i+2
            while j<len(old) and old[j]['phase'] not in callback_names and old[j]['phase']!='GUARD_ENTRY':
                effect=old[j]
                if effect['phase']=='GUARD_EXIT':raise ValueError('ORPHAN_MODEL_TEMPLATE_EXIT')
                fields={k:v for k,v in effect.items() if k not in ('schema','sequence','utc','monotonicNanoseconds','phase','profileId','windowId','ordinaryRole','observedAttempt')}
                mapping[effect['sequence']]=emit(effect['phase'],fields,effect['observedAttempt'])['sequence'];j+=1
            mapping[old[i+1]['sequence']]=end(label,token,observed)['sequence'];i=j
        token=begin('owner-close',b'',None);end('owner-close',token,None)
        emit('GUARD_HELPER_STDOUT_EOF',dict(helperInstance=instance));emit('GUARD_HELPER_STDERR_EOF',dict(helperInstance=instance))
        emit('GUARD_HELPER_EXIT',dict(helperInstance=instance,code=0,signal=None));emit('GUARD_HELPER_CLOSE',dict(helperInstance=instance,code=0,signal=None,stdoutEOF=True,stderrEOF=True,exitSeen=True))
        # Repin fresh MODEL snapshots after final global/local sequence expansion.
        for record,expected,spec in self.stages:
            value=record['observation'];first=mapping[value['phaseStartSequence']];last=mapping[value['phaseEndSequence']]
            value.update(phaseStartSequence=first,phaseEndSequence=last,observer=self.state(last,value['proxyEndSequence']))
        labels=['prepare-inboxes']+[sid+suffix for sid in self.w.STAGES[self.role] for suffix in ('-publish','-query')]
        for label in labels:
            path=self.root/'session/fixtures'/(label+'-outcome.json');value=self.doc(self.pin(path));oldstate=value['observer'];newend=mapping[oldstate['phase']['sequence']]
            acknowledged=oldstate['budget']['streams']['proxy']['acknowledged'];count=0;size=0
            for row in self.proxy_rows:
                if size>=acknowledged:break
                size+=len(self.s.json_bytes(row))+1;count+=1
            if size!=acknowledged:raise ValueError('MODEL_GLOBAL_PROXY_PREFIX_BOUNDARY')
            value['observer']=self.state(newend,count);self.put(path,value)

    def fixture_call(self,operation,result):
        from async_guard import ALLOCATION
        from test_async_guard import baseline
        index=len(self.fixture_call_pins)+1
        instance=hashlib.sha256((self.run_id+':controller:'+str(index)).encode()).hexdigest()[:32]
        checks=[(label,self.s.json_bytes({'mode':operation})) for label in ('startup:plan','controller:socket-create','controller:connect','controller:response')]
        audit_rows=baseline(checks=checks)
        audit_rows=[r for r in audit_rows if r['name'].startswith('GUARD_')]
        helper=self.source_by_name['guard-helper.py'];lease=self.doc(self.lease_pin)
        # Rebind every mock RPC to THIS exact modeled original lease/helper.
        for row in audit_rows:
            fields=row['fields'];fields['helperInstance']=instance
            if row['name']=='GUARD_HELPER_LAUNCH':fields['argv'][-4:]=[instance,self.lease_pin['sha256'],str(helper['bytes']),helper['sha256']]
            if row['name'] in ('GUARD_RPC_REQUEST','GUARD_RPC_REPLY'):
                value=json.loads(base64.b64decode(fields['rawBase64']));value.update(instance=instance,runId=self.run_id,leaseSha256=self.lease_pin['sha256'])
                if row['name']=='GUARD_RPC_REQUEST':last=self.s.json_bytes(value)+b'\n'
                else:
                    value['requestSha256']=hashlib.sha256(last).hexdigest()
                    if value['clocks'] is not None:value['clocks']=dict(Utc=str(lease['issuedUtcNs']+200),Mono='200',Boot='200',bootId=lease['bootId'])
                fields['rawBase64']=base64.b64encode(self.s.json_bytes(value)+b'\n').decode()
            if row['name']=='GUARD_RPC_REQUEST':
                fields['enqueueUtcLowerNs']=str(lease['issuedUtcNs']+100);fields['decisionDeadlineUtcNs']=str(lease['issuedUtcNs']+5000000100)
            if row['name']=='GUARD_EXIT':fields['consumedUtcUpperNs']=str(lease['issuedUtcNs']+300)
        audit=dict(schema='e02-controller-guard-audit-v1',reservationIndex=index,instance=instance,scope='ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',runId=self.run_id,leaseSha256=self.lease_pin['sha256'],configurationSha256=self.config_pin['sha256'],observations=audit_rows)
        reply=dict(schema='e02-minimum-fixture-command-v3',profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],operation=operation,caseId='minimum-two-role-rs',ok=True,result=result,guardController=audit)
        binding_sha=hashlib.sha256(self.s.json_bytes(self.sources)).hexdigest()
        reserve=dict(schema='e02-controller-audit-parent-reservation-v1',actor='/root',index=index,operation=operation,runId=self.run_id,runConfig=self.config_pin,originalLeaseSha256=self.lease_pin['sha256'],sourceBindingsSha256=binding_sha,slotBytes=131072,proofBytes=122880,ledgerBytes=4096,diagnosticsBytes=4096,poolPrechargedBytes=index*131072,refundAllowed=False)
        self.put('controller-audit-reservations/%02d-reserved.json'%index,reserve)
        seq,command,stdout=self.command(['/usr/bin/docker','exec','--env','NBDP_CONTROLLER_AUDIT_SLOT='+str(index),self.cids['fixture'],'/usr/local/bin/node','/input/fixture.mjs',operation],self.s.json_bytes(reply))
        value=dict(schema='e02-minimum-fixture-call-v2',profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],operation=operation,ordinal=index,commandSequence=seq,command=command,reply=stdout)
        descriptor=self.put('evidence/model-fixture-call-%02d.json'%index,value);self.fixture_call_pins.append(descriptor)
        self.put('controller-audit-reservations/%02d-result.json'%index,dict(schema='e02-controller-audit-parent-completion-v1',index=index,runId=self.run_id,operation=operation,commandSequence=seq,command=command,stdout=stdout,helperInstance=instance,encodedAuditContributionBytes=len(b',"guardController":'+self.s.json_bytes(audit)+b'}\n'),state='NATURAL_COMPLETE_REQUIRES_WHOLE_CONSUMER'))
        return descriptor,command,stdout

    def screen(self, tree):
        serial = len(self.ui) + 1
        xml = self.raw('ui/ui-%03d-synthetic.xml' % serial, ET.tostring(tree))
        png = self.raw('ui/ui-%03d-synthetic.png' % serial, b'\x89PNG\r\n\x1a\n' + self.marker.encode() + str(serial).encode())
        self.adb(['shell', 'cat', '/sdcard/nbdp-window.xml'], xml)
        self.adb(['exec-out', 'screencap', '-p'], png)
        capture = dict(xml=xml, png=png); self.ui.append(capture)
        return capture

    def node(self, parent, label='', package=None, kind='android.widget.TextView', rect='[10,10][300,50]', desc=''):
        return ET.SubElement(parent, 'node', {'text':label, 'package':package or self.g.APP,
            'class':kind, 'enabled':'true', 'bounds':rect, 'content-desc':desc})

    def helper_screen(self):
        tree=ET.Element('hierarchy')
        self.node(tree,'Clear clipboard',self.g.HELPER,'android.widget.Button','[10,10][100,50]')
        self.node(tree,'Capture clipboard',self.g.HELPER,'android.widget.Button','[10,60][100,100]')
        return tree

    def identity(self):
        # Public-only NIP19 encoding, not cryptographic signing/key generation.
        key=bytes.fromhex(self.w.ACCOUNTS[self.role]); payload=bytes([0,32])+key
        values=[]; acc=bits=0
        for b in payload:
            acc=(acc<<8)|b; bits+=8
            while bits>=5: bits-=5; values.append((acc>>bits)&31)
        if bits: values.append((acc<<(5-bits))&31)
        hrp='nprofile'; checksum=1
        for value in [ord(c)>>5 for c in hrp]+[0]+[ord(c)&31 for c in hrp]+values+[0]*6:
            top,checksum=checksum>>25,((checksum&0x1ffffff)<<5)^value
            for i,generator in enumerate((0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3)):
                if (top>>i)&1: checksum^=generator
        checksum^=1; alphabet='qpzry9x8gf2tvdw0s3jn54khce6mua7l'
        token=hrp+'1'+''.join(alphabet[n] for n in values+[(checksum>>(5*(5-i)))&31 for i in range(6)])
        tree=ET.Element('hierarchy'); self.node(tree,token)
        capture=self.screen(tree)
        self.identity_value=dict(preview=capture,observedPublicProfileText=[token],meaning=self.marker)
        tor={key:capture for key in ('selectedOff','firstSaveReturnedToLogin','savedStateReopened','secondSaveReturnedToLogin')}
        self.tor_pin=self.put('evidence/synthetic-tor-model.json',dict(schema='e02-tor-configuration-gui-v1',torFailureDismissals=0,**tor))

    def action_count(self, last=None):
        last=len(self.command_rows) if last is None else last
        snapshots=(['shell','uiautomator','dump','/sdcard/nbdp-window.xml'],['shell','cat','/sdcard/nbdp-window.xml'],['exec-out','screencap','-p'])
        clear=next(i for i,r in enumerate(self.command_rows,1) if self.g.adb_tail(r)==['shell','pm','clear',self.g.APP])
        return sum(i>=clear and i<=last and self.g.adb_tail(r) is not None and self.g.adb_tail(r) not in snapshots for i,r in enumerate(self.command_rows,1))

    def selection(self, record, expected, spec):
        sid=spec['id']; first=len(self.command_rows)+1; ui_first=len(self.ui)+1
        before=self.action_count()
        status=dict(profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],stageId=sid,stageIndex=spec['index'],
            complete=False,ready=True,gate=record['gate'],captureSequence=record['gate']['eoseSequence'],scope='SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT')
        status_call,status_command,status_reply=self.fixture_call('status',status)
        record=self.repin_tree(record)
        publication=self.put('session/fixtures/'+sid+'-publication.json',record)
        publish_result=dict(profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],stage=spec,publication=publication,
            **{k:record[k] for k in ('publicationWindow','validation','producerValidation','actualNewAppFrameObserved')})
        self.fixture_call('publish',publish_result)
        self.screen(self.helper_screen()); self.adb(['shell','input','tap','55','30'])
        clear=dict(schema='e02-clipboard-capture-v1',caseId=sid,action='CLEAR',foregroundFocus=True,
            elapsedRealtimeNanos=100+spec['index']*10,wallClockMillis=100+spec['index']*10,status='EMPTY_SENTINEL_SET')
        clear_pin=self.put('evidence/'+sid+'/helper-clear.json',clear)
        prefix='files/captures/'+sid
        self.adb(['exec-out','run-as',self.g.HELPER,'cat',prefix+'.clear.json'],clear_pin)
        tree=ET.Element('hierarchy'); self.node(tree,desc='Back')
        self.node(tree,expected['content'],rect='[10,100][200,150]')
        edit=self.node(tree,kind='android.widget.EditText'); self.node(edit,'Message')
        selected=self.screen(tree)
        self.adb(['shell','input','swipe','105','125','105','125','700'])
        tree=ET.Element('hierarchy'); self.node(tree,'More Options',rect='[20,200][120,240]')
        self.screen(tree); self.adb(['shell','input','tap','70','220'])
        tree=ET.Element('hierarchy'); self.node(tree,'Copy raw JSON',rect='[20,250][120,290]')
        self.screen(tree); self.adb(['shell','input','tap','70','270'])
        self.screen(self.helper_screen()); self.adb(['shell','input','tap','55','80'])
        raw=self.s.json_bytes(expected); raw_pin=self.raw('evidence/'+sid+'/client-raw-rumor.json',raw)
        capture=dict(schema='e02-clipboard-capture-v1',caseId=sid,action='CAPTURE',foregroundFocus=True,
            elapsedRealtimeNanos=101+spec['index']*10,wallClockMillis=101+spec['index']*10,status='CAPTURED',
            mime='text/plain',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),clipboardItemCount=1,clipboardTimestamp=101+spec['index']*10)
        cap_pin=self.put('evidence/'+sid+'/helper-capture.json',capture)
        self.adb(['exec-out','run-as',self.g.HELPER,'cat',prefix+'.receipt.json'],cap_pin)
        self.adb(['exec-out','run-as',self.g.HELPER,'cat',prefix+'.raw.json'],raw_pin)
        selected_record=dict(schema='e02-minimum-selection-v1',profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],
            observationId=sid,account=self.w.ACCOUNTS[self.role],peer=self.w.A if self.role=='incoming' else self.w.B,
            originalAuthor=self.w.A,originalOrderedTags=[['p',self.w.B]],rumorId=expected['id'],action='COPY_RAW_JSON',
            method='ANDROID_LOCAL_FOREGROUND',helperPackage=self.g.HELPER,helperArtifact=self.config['helperApk'],helperReceipt=cap_pin,
            capturedMonotonicNs=1000+spec['index'],selectedGui=selected,
            matchingVisibleTextNodes=[dict(bounds=[10,100,200,150],text=expected['content'])],limits=self.marker)
        selection=self.put('evidence/'+sid+'/selection.json',selected_record)
        custody=dict(commandSequenceFirst=first,commandSequenceLast=len(self.command_rows),uiCaptureSerialFirst=ui_first,
            uiCaptureSerialLast=len(self.ui),uiActionCountBefore=before,uiActionCountAfter=self.action_count(),uiCaptures=self.ui[ui_first-1:])
        return dict(id=sid,state='EXPORTED_PENDING_INDEPENDENT_WHOLE_RUN_REVIEW',selection=selection,uiPng=selected['png'],
            uiXml=selected['xml'],rawClientRumor=raw_pin,clipboardClear=clear_pin,visibleMatchingTextNodeCount=1,
            duplicateObservation=dict(scope='CURRENT_VISIBLE_MATCHING_TEXT_NODES_ONLY',visibleMatchingTextNodeCount=1,
                globalDuplicateBubbleCount=None,globalDuplicateBubbleCountStatus='UNKNOWN_UNMEASURED',businessEffectsMeasured=False),
            expectedRumor=self.candidate['oracles'][spec['oracle']],publication=publication,
            actualNewAppFrameObserved=record['actualNewAppFrameObserved'],originalGuestToHostBindings=[],subscriptionStatus=status,
            subscriptionStatusReply=status_reply,subscriptionStatusCall=status_call,subscriptionStatusCommand=status_command,custodySegment=custody)

    def cleanup(self):
        rows=[]
        for role,cid in self.cids.items():
            inspected=[dict(Id=cid,Config=dict(Labels={'nbdp.role':role,'nbdp.run':self.run_id}))]
            self.put('cleanup/'+role+'-inspect.stdout',inspected)
            for suffix,raw in (('-inspect.stderr',b''),('-remove.stderr',b''),('-remove.stdout',cid.encode()+b'\n'),
                ('-after-inspect.stdout',b'[]\n'),('-after-inspect.stderr',b'Error: No such object: '+cid.encode()+b'\n')):
                self.raw('cleanup/'+role+suffix,raw)
            rows.append(dict(role=role,exactOwnedCleanupOnly=True,errors=[],identityVerified=True,absenceConfirmed=True,
                inspectExit=0,cid=cid,logsExit=0,removeExit=0,afterInspectExit=1))
        original=dict(ok=True,rows=rows,errors=[])
        return dict(**original,evidence=self.put('cleanup/synthetic-cleanup.json',original))

    def build(self):
        self.source_inputs(); self.admission(); self.containers(); self.wire_graph(); self.identity()
        self.fixture_call('prepare',dict(profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],ordinaryRole=self.role,
            expected=self.prepared['expected'],prepared=self.prepared_pin,inboxes=self.inbox_pin))
        observations=[self.selection(*stage) for stage in self.stages]
        self.parent_allocation_metadata()
        driver=dict(schema='e02-minimum-role-driver-result-v2',profileId=self.w.PROFILE,windowId=self.w.WINDOWS[self.role],
            ordinaryRole=self.role,runId=self.run_id,runConfig=self.config_pin,runRelease=self.release_pin,
            executionState='PARTIAL',accountIdentityGUI=self.identity_value,expectedAccountPubkey=self.w.ACCOUNTS[self.role],
            accountIdentityQualification='ACTUAL_NPROFILE_INDEPENDENT_DECODE_AND_REVIEW_REQUIRED',torConfigurationGUI=self.tor_pin,
            environmentAnrEvidence=[],allUICaptures=self.ui,fixtureCalls=self.fixture_call_pins,observations=observations,
            limits=self.marker,canonicalE02Changed=False)
        self.driver_pin=self.put('evidence/synthetic-driver-result.json',driver)
        supervisor=dict(schema='e02-ordinary-minimum-role-supervisor-result-v2',runId=self.run_id,profileId=self.w.PROFILE,
            ordinaryRole=self.role,windowId=self.w.WINDOWS[self.role],runConfig=self.config_pin,runRelease=self.release_pin,
            lease=self.lease_pin,canonicalE02Changed=False,limits=self.marker,executionState='PARTIAL',error=None,
            secondaryErrors=[],cleanup=self.cleanup())
        self.supervisor_pin=self.put('evidence/synthetic-supervisor-result.json',supervisor)
        interpreter=self.raw(self.base/self.role/'synthetic-interpreter-not-executable',self.marker.encode())
        launch=self.raw(self.base/self.role/'synthetic-launch.txt',(self.marker+':LAUNCH').encode())
        completion=self.raw(self.base/self.role/'synthetic-completion.txt',(self.marker+':COMPLETE').encode())
        outer=dict(schema='e02-minimum-outer-witness-v1',runId=self.run_id,operator=MODEL_ACTOR,interpreter=interpreter,
            argv=[interpreter['path'],'-I','-B',self.source_by_name['supervisor.py']['path'],'--config',self.config_pin['path'],
                  '--config-sha',self.config_pin['sha256'],'--release',self.release_pin['path'],'--release-sha',self.release_pin['sha256'],'--out',str(self.root)],
            startedUtcNs=self.ns-2,finishedUtcNs=self.ns+1800000000015,launchSession='SYNTHETIC_NO_ACTUAL_TOOL_SESSION',
            launchResponse=launch,completionResponse=completion,naturalExitCode=0,
            transcript=self.raw(self.base/self.role/'synthetic-transcript.txt',self.marker.encode()))
        self.outer_pin=self.put(self.base/self.role/'synthetic-outer-witness.json',outer)
        graph=[self.pin(p) for p in sorted(self.root.rglob('*')) if p.is_file()]
        bindings=[]
        for p in self.fixture['pins'].values():
            bindings.append(dict(guest={k:p[k] for k in ('path','bytes','sha256')},host=dict(path=p['source'],bytes=p['bytes'],sha256=p['sha256'])))
        subject=dict(schema='e02-minimum-window-subject-v1',profileId=self.w.PROFILE,ordinaryRole=self.role,
            windowId=self.w.WINDOWS[self.role],runId=self.run_id,outputRoot=str(self.root),authors=[MODEL_ACTOR],operators=[MODEL_ACTOR],
            sourceSubject=self.producer_pin,supervisorSource=self.source_by_name['supervisor.py'],runConfig=self.config_pin,
            runRelease=self.release_pin,resource=self.resource_pin,sourceControls=self.controls_pin,outer=self.outer_pin,
            lease=self.lease_pin,driver=self.driver_pin,supervisor=self.supervisor_pin,commands=self.command_pins,ui=self.ui,
            proxy=self.proxy_pin,phase=self.phase_pin,readOnlyMountBindings=bindings,graphFiles=graph,excludedFiles=[],
            sourcePolicyObservations=dict(clockPolicy='SOURCE_ENFORCED_THREE_DOMAINS_ORIGINAL_LEASE',perCommandClockChronology='UNKNOWN_NOT_RECORDED',
                sdkAssetsBundled=False,guestHealth='UNKNOWN',businessEffectsMeasured=False))
        self.subject_pin=self.put(self.base/self.role/'synthetic-window-subject.json',subject)
        placeholder=self.raw(self.base/self.role/'synthetic-origin-placeholder.txt',self.marker.encode())
        origin=dict(schema='e02-minimum-origin-envelope-v1',profileId=self.w.PROFILE,method=placeholder,candidate=placeholder,
            history=placeholder,windowSubjects=[self.subject_pin],attemptSubjects=[],legacyContexts=[],reviews=self.source_reviews+self.reviews(self.subject_pin,'WINDOW'),
            tools=[dict(witness=self.outer_pin,operator=MODEL_ACTOR,launchSession=outer['launchSession'],launchResponse=launch,completionResponse=completion)],
            provenanceLimit='EXTERNALLY_AUTHENTICATED_COORDINATOR_TRANSCRIPTION_NOT_PORTABLE_ATTESTATION')
        # This Origin instance validates synthetic DATA structure only. The test
        # never presents its rows as actual externally authenticated observations.
        files=self.s.Files([str(self.base)])
        self.files=files
        self.origin=self.m['witness'].Origin(files,origin,{MODEL_ACTOR})
        return self

    def inspect(self):
        return self.m['consumer']._window_data(self.files,self.subject_pin,self.candidate,self.origin,self.producer)


def build_two_roles(root, modules, producer_dir):
    """Return model windows only; no invocation of real consume() or producers."""
    return [Model(root,modules,producer_dir,role).build() for role in ('incoming','archive')]
