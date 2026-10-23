"""Diagnostic-only driver; import performs no work.

Exactly one activity intent, no identity/input/login/fixture/clipboard operation.
The first ANR is retained as environment failure while bounded read-only capture
continues before final revocation. Absence in this finite window proves no health
or compatibility guarantee. Actual command receipts remain the lifecycle source.
"""
import json
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ET

BUDGET_SECONDS = 180
LATE_DELAY_SECONDS = 5


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


def run(runtime, clock=time.monotonic):
    started = clock()
    deadline = started + BUDGET_SECONDS
    runtime.diagnostic_deadline = deadline
    report = {'schema': 'e02-android-health-observation-v1',
              'scope': 'ANDROID_HEALTH_DIAGNOSTIC_ONLY_NO_LOGIN_OR_TRANSPORT',
              'diagnosticOnly': True, 'ordinaryControlQualified': False,
              'phaseBudgetSeconds': BUDGET_SECONDS, 'startedMonotonicNs': int(started * 1000000000),
              'environmentStatus': 'UNKNOWN', 'firstEnvironmentError': None,
              'firstError': None, 'secondaryErrors': [], 'observations': [],
              'activityIntents': 0, 'identityInputs': 0, 'loginActions': 0,
              'fixtureOperations': 0, 'clipboardOperations': 0,
              'limits': ['A bounded observation window does not establish healthy OS or an ANR cause.',
                         'Cgroup values measure the entire owned Android container, not one emulator process.',
                         'No ordinary-client compatibility or canonical E02 acceptance.']}
    def remaining():
        runtime.check()
        value = deadline - clock()
        need(value > 0, 'Original180s diagnostic deadline expired')
        return value
    def stamp():
        return int(clock() * 1000000000)
    def capture(phase, name, operation, optional=False):
        before = stamp(); remaining()
        raw = operation()
        need(type(raw) is bytes and len(raw) <= 8388608, 'Bounded actual diagnostic output')
        ended = stamp()
        pin = runtime.put_bytes('diagnostics/' + phase + '-' + name + '.bin', raw)
        row = {'phase': phase, 'id': name, 'startedMonotonicNs': before,
               'endedMonotonicNs': ended, 'raw': pin, 'status': 'CAPTURED'}
        if optional:
            row.update(optional_status(raw))
        report['observations'].append(row)
        remaining()
        return raw
    def adb(args):
        # Outer Docker commands are capped by Runtime.command against the same
        # original phase deadline, including nested identity inspections.
        allowance = min(10, remaining() - 5)
        need(allowance > 0, 'Insufficient original diagnostic command budget')
        return runtime.adb(list(args), timeout=allowance)
    def metrics(phase):
        cgroup = capture(phase, 'private-cgroup', lambda: runtime.guest(
            'android', ['diagnostic-cgroup', 'snapshot-v1'], min(15, remaining())))
        value = json.loads(cgroup)
        need(value.get('schema') == 'e02-private-cgroup-diagnostic-v1'
             and value.get('status') in ('CAPTURED', 'UNKNOWN', 'UNKNOWN_PARTIAL'), 'Explicit private cgroup status required')
        report['observations'][-1]['metricStatus'] = value['status']
        for name, args, optional in runtime.guard.HEALTH_READS:
            capture(phase, name, lambda args=args: adb(args), optional)
    def ui(phase):
        capture(phase, 'uiautomator', lambda: adb(runtime.guard.HEALTH_UI[0]))
        raw = capture(phase, 'ui-xml', lambda: adb(runtime.guard.HEALTH_UI[1]))
        titles = anr_titles(raw)
        report['observations'][-1]['observedAnrTitles'] = titles
        if titles and report['firstEnvironmentError'] is None:
            report['firstEnvironmentError'] = 'Observed Android ANR: ' + titles[0]
            report['environmentStatus'] = 'ENVIRONMENT_FAILURE'
        png = capture(phase, 'ui-png', lambda: adb(runtime.guard.HEALTH_UI[2]))
        need(png.startswith(b'\x89PNG\r\n\x1a\n'), 'Actual PNG required')
    try:
        metrics('baseline'); ui('baseline')
        capture('start', 'intent', lambda: adb(runtime.guard.HEALTH_START))
        report['activityIntents'] += 1
        report['activityStartMeaning'] = 'INTENT_DISPATCHED_ONLY; no -W/startup-duration/readiness claim'
        metrics('immediate-post'); ui('immediate-post')
        need(remaining() > LATE_DELAY_SECONDS + 5, 'Original late observation budget absent')
        runtime.sleep(LATE_DELAY_SECONDS)
        remaining()
        for name, args, _ in runtime.guard.HEALTH_READS[:2]:
            capture('late', name, lambda args=args: adb(args))
        ui('late')
        report['endedMonotonicNs'] = stamp()
        report['observationWindowMeaning'] = 'Actual timestamps only; no asserted healthy stabilization interval'
        remaining()
    except BaseException as exc:
        report['firstError'] = type(exc).__name__ + ': ' + str(exc)[:2048]
        try:
            runtime.retain_diagnostic_partial(report)
        except BaseException as secondary:
            # Preserve the original raised failure; evidence-only retention may
            # fail and does not permit a new guest command after revocation.
            sys.stderr.write('Secondary diagnostic journal failure: ' + repr(secondary) + '\n')
        raise
    runtime.retain_diagnostic_partial(report)
    return report
