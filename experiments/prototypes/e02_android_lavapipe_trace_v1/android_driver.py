"""Before-install early/postboot trace only; importing starts nothing.

No APK installation, activity intent, identity/login/input/fixture/clipboard or
ANR action is available. Trace support and correlation remain separate: raw
latest traces, process lists or UI titles never prove a matching PID/reason/stack.
"""
import json
import re
import sys
import time
import xml.etree.ElementTree as ET

EARLY_BUDGET_SECONDS = 30
BUDGET_SECONDS = 180
LATE_DELAY_SECONDS = 5
SCOPE = 'ANDROID_LAVAPIPE_TRACE_ONLY_NO_INSTALL_OR_INTENT'


def need(value, message):
    if not value:
        raise RuntimeError(message)


def optional_status(raw):
    text = raw.decode('utf-8', 'strict')
    lines = text.splitlines()
    if lines and lines[-1] == 'NBDP_OPTIONAL_UNAVAILABLE':
        return {'status': 'UNKNOWN_UNAVAILABLE', 'originalReadExit': None}
    match = re.fullmatch(r'NBDP_OPTIONAL_READ_FAILED:([1-9][0-9]{0,2})', lines[-1]) if lines else None
    if match:
        return {'status': 'UNKNOWN_READ_FAILED', 'originalReadExit': int(match[1])}
    need(lines and not any('NBDP_OPTIONAL_' in line for line in lines), 'Malformed optional metric wrapper output')
    return {'status': 'CAPTURED', 'originalReadExit': 0}


def anr_titles(raw):
    need(type(raw) is bytes and len(raw) <= 8388608, 'Bounded raw UI XML')
    tree = ET.fromstring(raw)
    need(tree.tag == 'hierarchy', 'Actual hierarchy required')
    # Observation only: no title/package/class grants an action or success.
    return [node.get('text', '') for node in tree.iter('node')
            if node.get('resource-id') == 'android:id/alertTitle'
            and "isn't responding" in node.get('text', '')]


def trace_observation(raw):
    """Conservative stdout classification; raw stderr also needs actual review.

    Explicit marker recognition never confirms support, matching identity or the
    reason/stack for the visible ANR. Candidate output may be unrelated/latest.
    Empty stdout is not inferred to mean no entries or a healthy process.
    """
    result = {'runtimeSupport': 'UNKNOWN', 'availability': 'UNKNOWN_EMPTY',
              'matchingAnr': 'UNKNOWN', 'pid': 'UNKNOWN', 'reason': 'UNKNOWN',
              'stack': 'UNKNOWN', 'requiresRawStderrReview': True}
    try:
        text = raw.decode('utf-8', 'strict').strip().lower()
    except UnicodeError:
        result['availability'] = 'UNKNOWN_NON_UTF8'; return result
    if not text:
        return result
    if any(token in text for token in ('permission denial', 'permission denied', 'requires android.permission')):
        result['availability'] = 'UNKNOWN_PERMISSION_DENIED'
    elif any(token in text for token in ('unknown command', 'unknown option', 'unrecognized command', 'not supported')):
        result['availability'] = 'UNKNOWN_EXPLICIT_UNSUPPORTED'
    elif '(contents lost)' in text:
        result['availability'] = 'UNKNOWN_CONTENTS_LOST'
    elif any(token in text for token in ('(nothing)', 'no entries', 'no anr', 'no traces')):
        result['availability'] = 'UNKNOWN_EXPLICIT_NO_ENTRY'
    else:
        result['availability'] = 'CANDIDATE_UNMATCHED'
    return result


class TracePhase:
    """One-use phase cap; original lease always encloses both separate phases."""
    def __init__(self, runtime, phase, seconds, clock):
        need(type(phase) is str and type(seconds) is int
             and (phase, seconds) in (('early', 30), ('postboot', 180)), 'Fixed independent trace phase budget')
        runtime.check()
        need(not hasattr(runtime, 'diagnostic_deadline'), 'Previous trace phase still active')
        ledger = getattr(runtime, 'trace_phase_deadlines', {})
        need(type(ledger) is dict and phase not in ledger, 'Trace phase cannot be renewed or repeated')
        self.runtime, self.clock, self.phase = runtime, clock, phase
        self.started = clock(); self.deadline = self.started + seconds
        ledger[phase] = self.deadline
        runtime.trace_phase_deadlines = ledger
        runtime.diagnostic_deadline = self.deadline
        self.report = {'schema': 'e02-android-lavapipe-trace-observation-v1', 'phase': phase,
            'scope': SCOPE, 'diagnosticOnly': True, 'ordinaryControlQualified': False,
            'phaseBudgetSeconds': seconds, 'startedMonotonicNs': int(self.started * 1000000000),
            'phaseDeadlineMonotonicNs': int(self.deadline * 1000000000),
            'completed': False, 'environmentStatus': 'UNKNOWN', 'firstEnvironmentError': None,
            'firstError': None, 'secondaryErrors': [], 'observations': [],
            'apkInstalls': 0, 'activityIntents': 0, 'identityInputs': 0,
            'loginActions': 0, 'fixtureOperations': 0, 'clipboardOperations': 0,
            'traceCorrelation': 'UNKNOWN',
            'requestedRenderer': 'lavapipe', 'effectiveBackend': 'UNKNOWN',
            'effectiveVendor': 'UNKNOWN', 'backendEvidence': 'REQUIRES_INDEPENDENT_RAW_REVIEW',
            'limits': ['Before-install trace only; no ordinary-client or canonical qualification.',
                       'Latest trace/DropBox entry may be unrelated; PID/reason/stack need independent raw correlation.',
                       'Title/process-list/focus reasons do not establish matching ANR identity or stack.',
                       'Whole Android container cgroup metrics, not emulator-only or peak/minimum proof.',
                       'No observed ANR in a bounded window does not establish healthy OS.']}
    def remaining(self):
        self.runtime.check()
        need(self.runtime.trace_phase_deadlines.get(self.phase) == self.deadline
             and getattr(self.runtime, 'diagnostic_deadline', None) == self.deadline,
             'Original trace phase deadline changed')
        value = self.deadline - self.clock()
        need(value > 0, 'Original trace phase deadline expired')
        return value
    def stamp(self):
        return int(self.clock() * 1000000000)
    def adb(self, args):
        allowance = min(10, self.remaining() - 5)
        need(allowance > 0, 'Insufficient original trace command budget')
        return self.runtime.adb(list(args), timeout=allowance)
    def capture(self, checkpoint, name, operation, optional=False):
        before = self.stamp(); self.remaining()
        raw = operation()
        need(type(raw) is bytes and len(raw) <= 8388608, 'Bounded actual trace output')
        ended = self.stamp()
        pin = self.runtime.put_bytes('diagnostics/' + checkpoint + '-' + name + '.bin', raw)
        row = {'phase': checkpoint, 'id': name, 'startedMonotonicNs': before,
               'endedMonotonicNs': ended, 'raw': pin, 'status': 'CAPTURED'}
        if optional:
            row.update(optional_status(raw))
        if name in ('lastanr', 'lastanr-traces', 'dropbox-system-app-anr'):
            row['traceObservation'] = trace_observation(raw)
        if name == 'processes':
            row['processSnapshotMeaning'] = 'Guest PID/name snapshot only; no inferred UI/ANR PID match'
        self.report['observations'].append(row)
        self.remaining()
        return raw
    def metrics(self, checkpoint):
        raw = self.capture(checkpoint, 'private-cgroup', lambda: self.runtime.guest(
            'android', ['diagnostic-cgroup', 'snapshot-v1'], min(15, self.remaining())))
        value = json.loads(raw)
        need(value.get('schema') == 'e02-private-cgroup-diagnostic-v1'
             and value.get('status') in ('CAPTURED', 'UNKNOWN', 'UNKNOWN_PARTIAL'), 'Explicit private cgroup status required')
        self.report['observations'][-1]['metricStatus'] = value['status']
        for name, args, optional in self.runtime.guard.HEALTH_READS:
            self.capture(checkpoint, name, lambda args=args: self.adb(args), optional)
    def ui(self, checkpoint):
        self.capture(checkpoint, 'uiautomator', lambda: self.adb(self.runtime.guard.HEALTH_UI[0]))
        raw = self.capture(checkpoint, 'ui-xml', lambda: self.adb(self.runtime.guard.HEALTH_UI[1]))
        titles = anr_titles(raw)
        self.report['observations'][-1]['observedAnrTitles'] = titles
        if titles and self.report['firstEnvironmentError'] is None:
            self.report['firstEnvironmentError'] = 'Observed Android ANR: ' + titles[0]
            self.report['environmentStatus'] = 'ENVIRONMENT_FAILURE'
        png = self.capture(checkpoint, 'ui-png', lambda: self.adb(self.runtime.guard.HEALTH_UI[2]))
        need(png.startswith(b'\x89PNG\r\n\x1a\n'), 'Actual PNG required')
    def renderer(self, checkpoint):
        # Existing trace prefix is acquired first. These are mandatory raw reads;
        # unsupported/empty output stays UNKNOWN, command failure still revokes.
        self.remaining()
        prefixes = self.runtime.emulator_prefixes()
        need(type(prefixes) is dict and set(prefixes) == {'stdout', 'stderr'}, 'Fixed emulator stream prefixes required')
        for stream in ('stdout', 'stderr'):
            self.capture(checkpoint, 'emulator-' + stream, lambda stream=stream: prefixes[stream])
        for name, args, optional in self.runtime.guard.RENDERER_READS:
            self.capture(checkpoint, name, lambda args=args: self.adb(args), optional)
    def finish(self):
        self.remaining()
        self.report['endedMonotonicNs'] = self.stamp()
        self.report['completed'] = True
        self.report['observationWindowMeaning'] = 'Actual timestamps only; no readiness/stability guarantee'
        self.runtime.retain_diagnostic_partial(self.report)
        return self.report
    def failure(self, exc):
        self.report['firstError'] = type(exc).__name__ + ': ' + str(exc)[:2048]
        self.report['endedMonotonicNs'] = self.stamp()
        try:
            self.runtime.retain_diagnostic_partial(self.report)
        except BaseException as secondary:
            sys.stderr.write('Secondary trace journal failure: ' + repr(secondary) + '\n')
    def release_cap(self):
        # Clearing this completed/failed phase cap does not alter the original
        # lease or ledger. The same named phase can never be opened again.
        if getattr(self.runtime, 'diagnostic_deadline', None) == self.deadline:
            del self.runtime.diagnostic_deadline


def early(runtime, clock=time.monotonic):
    phase = TracePhase(runtime, 'early', EARLY_BUDGET_SECONDS, clock)
    try:
        for name, args, optional in runtime.guard.EARLY_BOOT_READS:
            phase.capture('early-adb-before-boot-wait', name, lambda args=args: phase.adb(args), optional)
        return phase.finish()
    except BaseException as exc:
        phase.failure(exc); raise
    finally:
        phase.release_cap()


def run(runtime, clock=time.monotonic):
    phase = TracePhase(runtime, 'postboot', BUDGET_SECONDS, clock)
    try:
        phase.metrics('before-install'); phase.renderer('before-install'); phase.ui('before-install')
        need(phase.remaining() > LATE_DELAY_SECONDS + 5, 'Original late observation budget absent')
        runtime.sleep(LATE_DELAY_SECONDS)
        phase.remaining()
        phase.metrics('late'); phase.renderer('late'); phase.ui('late')
        return phase.finish()
    except BaseException as exc:
        phase.failure(exc); raise
    finally:
        phase.release_cap()
