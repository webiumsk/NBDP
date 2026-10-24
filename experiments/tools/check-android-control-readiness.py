#!/usr/bin/env python3
"""Read-only Android preparation probe; never executes an E02 control."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

GIB = 1024 ** 3
ROOT = Path(__file__).resolve().parents[2]
SDK = Path('/tmp/nbdp-e02-ingress-runtime/sdk')
ARTIFACT = Path('/tmp/nbdp-e02-android-artifact')
APK = ARTIFACT / 'source/amethyst/build/outputs/apk/fdroid/debug/amethyst-fdroid-debug.apk'
APK_BYTES = 165860063
APK_SHA = '5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5'
SOURCE = 'e6f464a1179def75274512b3c5bab921de3bf3d8'
MANIFEST_SHA = '7a05ade74647386345283b9f4a182894bba845890bdf32160f855e16fcfe79ae'
METADATA = {
    'platform-tools/source.properties': (38, '2dccd788c0234d8cf7f7457377e57f57527a86a629c6ed54feb8af0f549dac38'),
    'emulator/source.properties': (103, 'ba13085f647fb8389a4d06a1de0e4104ac4e841733e50f67223ac230e1ce685a'),
    'system-images/android-36/default/x86_64/source.properties':
        (319, '1a6e7c0b326c24c28ba501aa5ada247dd9fb0f087b662865f7bc649991fe74d1'),
}


def checked_file(path, size, digest):
    if path.resolve(strict=True) != path or path.is_symlink():
        raise ValueError('Noncanonical input path')
    h = hashlib.sha256()
    count = 0
    with path.open('rb') as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size != size:
            raise ValueError('Unexpected file type/size')
        for chunk in iter(lambda: handle.read(1048576), b''):
            h.update(chunk)
            count += len(chunk)
        after = os.fstat(handle.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if identity(before) != identity(after) or count != size or h.hexdigest() != digest:
        raise ValueError('Input changed or hash mismatched')
    return {'path': str(path), 'bytes': count, 'sha256': digest}


def artifact_check():
    apk = checked_file(APK, APK_BYTES, APK_SHA)
    path = ARTIFACT / 'records/artifact-manifest.json'
    manifest = checked_file(path, 1768, MANIFEST_SHA)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('Manifest changed while reading')
    value = json.loads(raw)
    expected = (value['sourceCommit'] == SOURCE and value['sourceClean'] is True
                and value['buildExit'] == 0 and value['apk'] == apk
                and value['package'] == 'com.vitorpamplona.amethyst.debug'
                and value['versionName'] == '1.17.0-DEBUG' and value['versionCode'] == 462
                and 'x86_64' in value['nativeABIs'])
    return expected, {'apk': apk, 'buildManifest': manifest,
                      'meaning': 'Source-linked cached artifact, not runtime interoperability.'}


def sdk_check():
    pins = [checked_file(SDK / name, size, digest)
            for name, (size, digest) in METADATA.items()]
    required = ['platform-tools/adb', 'emulator/emulator']
    image = 'system-images/android-36/default/x86_64/'
    required += [image + name for name in ('system.img', 'vendor.img', 'ramdisk.img',
                                          'kernel-ranchu', 'encryptionkey.img')]
    paths = [SDK / name for name in required]
    present = all(p.is_file() and not p.is_symlink() and p.resolve() == p
                  and os.access(p, os.R_OK) for p in paths)
    executable = all(os.access(SDK / name, os.X_OK) for name in required[:2])
    return present and executable, {'metadataPins': pins, 'requiredFiles': required,
                                    'meaning': 'Presence/metadata only; no full SDK qualification or tool execution.'}


def disk_check():
    facts = []
    for path in (ROOT, Path('/tmp')):
        info = os.statvfs(path)
        facts.append({'path': str(path), 'device': path.stat().st_dev,
                      'availableBytes': info.f_bavail * info.f_frsize})
    return all(row['availableBytes'] >= 6 * GIB for row in facts), facts


def memory_check():
    values = {line.split(':')[0]: int(line.split()[1]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines()
              if line.startswith(('MemAvailable:', 'MemTotal:'))}
    return values['MemAvailable'] >= 12 * GIB, values


def kvm_check():
    fd = os.open('/dev/kvm', os.O_RDWR | os.O_CLOEXEC)
    try:
        character_device = stat.S_ISCHR(os.fstat(fd).st_mode)
    finally:
        os.close(fd)
    return character_device, {'openedReadWrite': True, 'ioctlIssued': False}


def docker_check():
    argv = ['/usr/bin/docker', '--host', 'unix:///var/run/docker.sock', '--config',
            '/tmp/nbdp-android-readiness-20261023/docker-readonly-no-config',
            'version', '--format', '{{.Server.Version}}']
    result = subprocess.run(argv, capture_output=True, text=True, timeout=12,
                            env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
    return result.returncode == 0 and bool(result.stdout.strip()), {
        'argv': argv, 'exit': result.returncode, 'stdout': result.stdout[:2048],
        'stderr': result.stderr[:2048], 'endpoint': 'Explicit local Unix socket only'}


def main():
    checks = []
    for name, function in (('artifact', artifact_check), ('sdk', sdk_check),
                           ('persistentSpace', disk_check), ('memory', memory_check),
                           ('kvm', kvm_check), ('dockerServer', docker_check)):
        try:
            passed, facts = function()
            checks.append({'check': name, 'passed': passed is True, 'facts': facts})
        except Exception as error:
            checks.append({'check': name, 'passed': False,
                           'error': type(error).__name__ + ': ' + str(error)[:2048]})
    ready = len(sys.argv) == 1 and all(row['passed'] for row in checks)
    print(json.dumps({'schema': 'nbdp-android-control-readiness-v1',
        'status': 'READY_FOR_REVIEWED_PREPARATION' if ready else 'PREPARATION_BLOCKED',
        'executionScope': 'Current process namespace/permissions; sandbox failures do not establish host absence.',
        'argumentsAccepted': len(sys.argv) == 1, 'checks': checks,
        'guards': {'persistentFreeBytes': 6 * GIB, 'memAvailableBytes': 12 * GIB,
                   'meaning': 'Retained reviewed boot-driver guards, not an empirical minimum or measured peak.'},
        'controlExecuted': False, 'E02Promotion': False,
        'remainingGate': 'Exact UI/raw-content/tag-export harness, isolated input plan, independent review and actual control evidence remain mandatory.'},
        separators=(',', ':')))
    return 0 if ready else 2


if __name__ == '__main__':
    raise SystemExit(main())
