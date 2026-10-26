"""Offline disposable helper artifact preparation; no Android/control activation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
JDK = Path('/tmp/nbdp-e02-android-artifact/toolchains/jdk21')
TOOLS = Path('/tmp/nbdp-e02-android-artifact/sdk/build-tools/36.0.0')
ANDROID_JAR = Path('/tmp/nbdp-e02-android-artifact/sdk/platforms/android-37.0/android.jar')
BASE = Path('/tmp/nbdp-e02-ordinary-client-v1')
PACKAGE = 'org.nbdp.clipboard.capture'


def pin(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_file():
        raise ValueError('Canonical regular input required')
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1048576), b''):
            h.update(chunk)
            size += len(chunk)
    return dict(path=str(path), bytes=size, sha256=h.hexdigest())


def write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return pin(path)


def main(argv):
    if len(argv) != 3 or Path(argv[1]) != HERE / 'helper-build-plan.json':
        raise ValueError('CLI build_helper.py EXACT_PLAN EXTERNAL_SHA')
    plan_pin = pin(Path(argv[1]))
    if plan_pin['sha256'] != argv[2]:
        raise ValueError('External plan pin mismatch')
    plan = json.loads(Path(argv[1]).read_bytes())
    if set(plan) != {'schema', 'scope', 'outputRoot', 'sources', 'tools', 'limits'}:
        raise ValueError('Closed helper plan required')
    if plan['schema'] != 'e02-clipboard-helper-build-plan-v1' or plan['scope'] != 'OFFLINE_HELPER_ARTIFACT_ONLY':
        raise ValueError('Exact helper build scope required')
    wanted = {str(HERE / 'clipboard-helper/AndroidManifest.xml'),
              str(HERE / 'clipboard-helper/src/org/nbdp/clipboard/capture/CaptureActivity.java'),
              str(HERE / 'build_helper.py')}
    if {p['path'] for p in plan['sources']} != wanted:
        raise ValueError('Exact helper source set required')
    expected_tools = {str(JDK / ('bin/' + name)) for name in ('java', 'javac', 'keytool')}
    expected_tools |= {str(TOOLS / name) for name in ('aapt2', 'd8', 'zipalign', 'apksigner',
                                                    'lib/d8.jar', 'lib/apksigner.jar')}
    expected_tools.add(str(ANDROID_JAR))
    if {p['path'] for p in plan['tools']} != expected_tools:
        raise ValueError('Exact offline tools required')
    inputs = [plan_pin, *plan['sources'], *plan['tools']]
    for original in inputs:
        if pin(original['path']) != original:
            raise ValueError('Original build input drift')
    out = Path(plan['outputRoot'])
    if out != BASE / 'helper-build-20261023a' or out.exists() or out.is_symlink():
        raise ValueError('Fresh exact helper output required')
    if plan['limits'] != {'phaseSeconds': 180, 'commandSeconds': 60}:
        raise ValueError('Fixed finite build limits required')
    BASE.mkdir(mode=0o700, exist_ok=True)
    out.mkdir(mode=0o700)
    for name in ('classes', 'dex', 'tmp', 'user'):
        (out / name).mkdir(mode=0o700)
    started = time.clock_gettime(time.CLOCK_BOOTTIME)
    expires = started + 180
    env = {'PATH': str(JDK / 'bin') + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
           'LC_ALL': 'C.UTF-8', 'JAVA_HOME': str(JDK), 'TMPDIR': str(out / 'tmp'),
           'JAVA_TOOL_OPTIONS': '-Duser.home=' + str(out / 'user')}
    commands = []
    result = {'schema': 'e02-clipboard-helper-build-result-v1', 'plan': plan_pin,
              'status': 'FAILED', 'commands': commands, 'apk': None,
              'controlExecuted': False, 'error': None}

    def current():
        if time.clock_gettime(time.CLOCK_BOOTTIME) >= expires:
            raise TimeoutError('Original helper build phase expired')
        for original in inputs:
            if pin(original['path']) != original:
                raise ValueError('Original build input drift')

    def run(args):
        current()
        row = {'argv': list(map(str, args)), 'exit': None, 'stdout': None, 'stderr': None}
        commands.append(row)
        remaining = expires - time.clock_gettime(time.CLOCK_BOOTTIME)
        number = len(commands)
        try:
            child = subprocess.run(row['argv'], cwd=out, env=env, input=b'',
                                   capture_output=True, timeout=min(60, remaining))
        except subprocess.TimeoutExpired as error:
            row['outcome'] = 'TIMEOUT_EXIT_UNKNOWN'
            row['stdout'] = write(out / ('command-%02d.stdout' % number), error.output or b'')
            row['stderr'] = write(out / ('command-%02d.stderr' % number), error.stderr or b'')
            raise
        row['exit'] = child.returncode
        row['stdout'] = write(out / ('command-%02d.stdout' % number), child.stdout)
        row['stderr'] = write(out / ('command-%02d.stderr' % number), child.stderr)
        current()
        if child.returncode:
            raise ValueError('Helper build command failed; raw outputs retained')

    try:
        java = HERE / 'clipboard-helper/src/org/nbdp/clipboard/capture/CaptureActivity.java'
        run([JDK / 'bin/javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8',
             '-bootclasspath', ANDROID_JAR, '-d', out / 'classes', java])
        run([TOOLS / 'd8', '--min-api', '26', '--lib', ANDROID_JAR, '--output', out / 'dex',
             out / 'classes/org/nbdp/clipboard/capture/CaptureActivity.class'])
        unsigned = out / 'unsigned.apk'
        run([TOOLS / 'aapt2', 'link', '--manifest', HERE / 'clipboard-helper/AndroidManifest.xml',
             '-I', ANDROID_JAR, '--min-sdk-version', '26', '--target-sdk-version', '36',
             '--version-code', '1', '--version-name', '0.1', '-o', unsigned])
        current()
        with zipfile.ZipFile(unsigned, 'a', compression=zipfile.ZIP_STORED) as archive:
            archive.write(out / 'dex/classes.dex', 'classes.dex')
        run([TOOLS / 'zipalign', '-p', '4', unsigned, out / 'aligned.apk'])
        run([JDK / 'bin/keytool', '-genkeypair', '-keystore', out / 'debug.keystore',
             '-storepass', 'android', '-keypass', 'android', '-alias', 'nbdp-lab-debug',
             '-dname', 'CN=NBDP Disposable Clipboard Lab', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '2'])
        apk = out / 'clipboard-capture.apk'
        run([TOOLS / 'apksigner', 'sign', '--ks', out / 'debug.keystore', '--ks-pass', 'pass:android',
             '--key-pass', 'pass:android', '--ks-key-alias', 'nbdp-lab-debug', '--out', apk, out / 'aligned.apk'])
        run([TOOLS / 'apksigner', 'verify', '--print-certs', apk])
        run([TOOLS / 'aapt2', 'dump', 'badging', apk])
        current()
        result['apk'] = pin(apk)
        result['status'] = 'BUILT_HELPER_ARTIFACT_ONLY'
    except BaseException as error:
        result['error'] = type(error).__name__ + ': ' + str(error)[:4096]
    result['elapsedMilliseconds'] = round((time.clock_gettime(time.CLOCK_BOOTTIME) - started) * 1000)
    receipt = write(out / 'build-result.json', (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({'receipt': receipt, 'status': result['status'], 'apk': result['apk']}))
    return 0 if result['status'] == 'BUILT_HELPER_ARTIFACT_ONLY' else 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
