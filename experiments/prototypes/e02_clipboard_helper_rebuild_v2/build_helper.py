"""Offline rebuilt disposable helper only. SOURCE prep never activates tools.

Original Java/Manifest and compiler/signing flags are preserved. Fresh acquired
tools and a fresh private debug key imply a new APK identity, never old a680e5.
Actual compilation needs separately reviewed effective tool/source/heap pins.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
JDK=Path('/tmp/nbdp-amethyst-rebuild-20261026/tools/jdk')
TOOLS=Path('/tmp/nbdp-amethyst-rebuild-20261026/tools/sdk/build-tools/36.0.0')
ANDROID_JAR=Path('/tmp/nbdp-amethyst-rebuild-20261026/tools/sdk/platforms/android-37.0/android.jar')
BASE=Path('/tmp/nbdp-e02-clipboard-helper-rebuild-20261027')
OUT=BASE/'build-r1'
EFFECTIVE_PLAN=HERE/'helper-build-plan-effective-r1.json'
PACKAGE='org.nbdp.clipboard.capture'
JVM_FLAGS='-Xmx512m -XX:MaxMetaspaceSize=256m -XX:CompressedClassSpaceSize=128m -XX:ReservedCodeCacheSize=128m'


def need(value,message):
    if not value:raise ValueError(message)


def pin(path):
    path=Path(path)
    need(path.is_absolute() and path.resolve(strict=True)==path and path.is_file(),'CANONICAL_REGULAR_INPUT_REQUIRED')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as source:
        before=os.fstat(source.fileno());need(stat.S_ISREG(before.st_mode),'REGULAR_INPUT_REQUIRED')
        size=0;digest=hashlib.sha256()
        while block:=source.read(1048576):size+=len(block);digest.update(block)
        after=os.fstat(source.fileno())
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    need(identity(before)==identity(after) and size==before.st_size,'INPUT_DRIFT_DURING_HASH')
    return dict(path=str(path),bytes=size,sha256=digest.hexdigest())


def source_paths():
    return {str(HERE/'clipboard-helper/AndroidManifest.xml'),
            str(HERE/'clipboard-helper/src/org/nbdp/clipboard/capture/CaptureActivity.java'),
            str(HERE/'build_helper.py')}


def tool_paths():
    result={str(JDK/'bin'/name) for name in ('java','javac','keytool')}
    result|={str(TOOLS/name) for name in ('aapt2','d8','zipalign','apksigner','lib/d8.jar','lib/apksigner.jar')}
    return result|{str(ANDROID_JAR)}


def descriptor(value):
    need(type(value) is dict and set(value)=={'path','bytes','sha256'},'EXACT_PIN_FIELDS_REQUIRED')
    need(type(value['path']) is str and type(value['bytes']) is int and value['bytes']>0 and
         type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']),'REAL_NONEMPTY_TOOL_SOURCE_PIN_REQUIRED')


def validate_shape(plan):
    need(type(plan) is dict and set(plan)=={'schema','scope','state','outputRoot','sources','tools','limits','jvm','toolAcceptance','wrapperHeapEvidence'},'CLOSED_REBUILT_HELPER_PLAN')
    need(plan['schema']=='e02-clipboard-helper-rebuild-plan-v2' and plan['scope']=='OFFLINE_REBUILT_HELPER_ARTIFACT_ONLY','EXACT_OFFLINE_REBUILD_SCOPE')
    need(plan['state']=='PINNED_INPUTS_REQUIRES_SEPARATE_ROOT_RELEASE','NOT_READY_EFFECTIVE_INPUTS_REQUIRED')
    for key,wanted in (('sources',source_paths()),('tools',tool_paths())):
        values=plan[key];need(type(values) is list and len(values)==len(wanted),'EXACT_SOURCE_TOOL_COUNT')
        for value in values:descriptor(value)
        need({value['path'] for value in values}==wanted,'EXACT_SOURCE_TOOL_PATH_SET')
    need(plan['outputRoot']==str(OUT),'EXACT_NEW_FRESH_OUTPUT_ROOT')
    need(plan['limits']=={'phaseSeconds':180,'commandSeconds':60},'ORIGINAL_HELPER_180_60_LIMITS')
    need(plan['jvm']==dict(javaToolOptions=JVM_FLAGS,meaning='Configured environment options; acquired wrapper command-line defaults can override heap and need separate source observation.'),'FIXED_EXPLICIT_JVM_CONFIGURATION')
    descriptor(plan['toolAcceptance']);descriptor(plan['wrapperHeapEvidence'])


def validate_inputs(plan):
    validate_shape(plan)
    for value in [*plan['sources'],*plan['tools'],plan['toolAcceptance'],plan['wrapperHeapEvidence']]:
        need(pin(value['path'])==value,'ACTUAL_BUILD_INPUT_PIN_MISMATCH')
    wrappers=json.loads(Path(plan['wrapperHeapEvidence']['path']).read_bytes())
    need(wrappers['schema']=='e02-helper-wrapper-heap-source-observation-v1','ACTUAL_WRAPPER_SOURCE_OBSERVATION_REQUIRED')
    tool_by_path={value['path']:value for value in plan['tools']}
    need(set(wrappers['wrappers'])=={'d8','apksigner'},'BOTH_WRAPPER_HEAP_OBSERVATIONS_REQUIRED')
    for name,row in wrappers['wrappers'].items():
        need(row['tool']==tool_by_path[str(TOOLS/name)] and row['flagsUnchanged'] is True,'EXACT_REVIEWED_WRAPPER_SOURCE_BINDING')
        need(type(row['effectiveHeapMiBFromSource']) is int and row['effectiveHeapMiBFromSource'] in (512,1024),
             'EFFECTIVE_WRAPPER_HEAP_UNRESOLVED_OR_NEEDS_VERSIONED_REVIEW')
        need(row['notRuntimeMeasured'] is True,'SOURCE_HEAP_OBSERVATION_NOT_MEASUREMENT')
    return wrappers


def write(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as output:
        need(output.write(raw)==len(raw),'SHORT_ARTIFACT_WRITE');output.flush();os.fsync(output.fileno())
    return pin(path)


def command_plan(out):
    """Original CLI/order/flags; only fixed tool/source/output paths changed."""
    java=HERE/'clipboard-helper/src/org/nbdp/clipboard/capture/CaptureActivity.java'
    unsigned=out/'unsigned.apk';apk=out/'clipboard-capture.apk'
    return [
        [JDK/'bin/javac','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',ANDROID_JAR,'-d',out/'classes',java],
        [TOOLS/'d8','--min-api','26','--lib',ANDROID_JAR,'--output',out/'dex',out/'classes/org/nbdp/clipboard/capture/CaptureActivity.class'],
        [TOOLS/'aapt2','link','--manifest',HERE/'clipboard-helper/AndroidManifest.xml','-I',ANDROID_JAR,'--min-sdk-version','26','--target-sdk-version','36','--version-code','1','--version-name','0.1','-o',unsigned],
        [TOOLS/'zipalign','-p','4',unsigned,out/'aligned.apk'],
        [JDK/'bin/keytool','-genkeypair','-keystore',out/'debug.keystore','-storepass','android','-keypass','android','-alias','nbdp-lab-debug','-dname','CN=NBDP Disposable Clipboard Lab','-keyalg','RSA','-keysize','2048','-validity','2'],
        [TOOLS/'apksigner','sign','--ks',out/'debug.keystore','--ks-pass','pass:android','--key-pass','pass:android','--ks-key-alias','nbdp-lab-debug','--out',apk,out/'aligned.apk'],
        [TOOLS/'apksigner','verify','--print-certs',apk],
        [TOOLS/'aapt2','dump','badging',apk]]


def main(argv):
    need(len(argv)==3 and Path(argv[1])==EFFECTIVE_PLAN,'EXACT_SEPARATELY_REVIEWED_EFFECTIVE_PLAN_REQUIRED')
    os.umask(0o077)
    plan_pin=pin(Path(argv[1]));need(plan_pin['sha256']==argv[2],'EXTERNAL_EFFECTIVE_PLAN_HASH')
    plan=json.loads(Path(argv[1]).read_bytes());wrappers=validate_inputs(plan)
    inputs=[plan_pin,*plan['sources'],*plan['tools'],plan['toolAcceptance'],plan['wrapperHeapEvidence']]
    need(not OUT.exists() and not OUT.is_symlink(),'FRESH_REBUILT_HELPER_OUTPUT_REQUIRED')
    for path in (BASE,*BASE.parents):need(not path.is_symlink(),'OUTPUT_PARENT_SYMLINK_REFUSED')
    BASE.mkdir(mode=0o700,exist_ok=True);OUT.mkdir(mode=0o700)
    for name in ('classes','dex','tmp','user'):(OUT/name).mkdir(mode=0o700)
    started=time.clock_gettime(time.CLOCK_BOOTTIME);expires=started+180
    env={'PATH':str(JDK/'bin')+':/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','JAVA_HOME':str(JDK),
        'TMPDIR':str(OUT/'tmp'),'JAVA_TOOL_OPTIONS':'-Duser.home='+str(OUT/'user')+' '+JVM_FLAGS}
    commands=[]
    result=dict(schema='e02-clipboard-helper-rebuild-result-v2',plan=plan_pin,status='FAILED',commands=commands,
        apk=None,error=None,controlExecuted=False,artifactIdentity='REBUILT_NEW_DEBUG_IDENTITY_NO_OLD_APK_HASH_TRANSFER',
        configuredJavaToolOptions=env['JAVA_TOOL_OPTIONS'],wrapperHeapSourceObservation=wrappers,
        effectiveJvmHeapRuntimeMeasured=False,sdkmanagerOrLicenseConsent=False,networkRequired=False)
    def current():
        need(time.clock_gettime(time.CLOCK_BOOTTIME)<expires,'ORIGINAL_HELPER_PHASE_EXPIRED')
        for value in inputs:need(pin(value['path'])==value,'CURRENT_BUILD_INPUT_DRIFT')
    def run(args):
        current();number=len(commands)+1
        row=dict(argv=list(map(str,args)),exit=None,stdout=None,stderr=None);commands.append(row)
        remaining=expires-time.clock_gettime(time.CLOCK_BOOTTIME)
        try:
            child=subprocess.run(row['argv'],cwd=OUT,env=env,input=b'',capture_output=True,timeout=min(60,remaining))
        except subprocess.TimeoutExpired as error:
            row['outcome']='TIMEOUT_EXIT_UNKNOWN'
            row['stdout']=write(OUT/('command-%02d.stdout'%number),error.output or b'')
            row['stderr']=write(OUT/('command-%02d.stderr'%number),error.stderr or b'')
            raise
        row['exit']=child.returncode
        row['stdout']=write(OUT/('command-%02d.stdout'%number),child.stdout)
        row['stderr']=write(OUT/('command-%02d.stderr'%number),child.stderr)
        current();need(child.returncode==0,'HELPER_COMMAND_FAILED_RAW_OUTPUTS_RETAINED')
    try:
        rows=command_plan(OUT)
        for args in rows[:3]:run(args)
        current()
        with zipfile.ZipFile(OUT/'unsigned.apk','a',compression=zipfile.ZIP_STORED) as archive:
            archive.write(OUT/'dex/classes.dex','classes.dex')
        for args in rows[3:]:
            run(args)
            if args[0]==JDK/'bin/keytool':os.chmod(OUT/'debug.keystore',0o600)
        current();key=OUT/'debug.keystore'
        need(stat.S_IMODE(key.stat().st_mode)==0o600,'PRIVATE_FRESH_DEBUG_KEY_REQUIRED')
        badging=Path(commands[7]['stdout']['path']).read_text()
        need(re.search(r"^package: name='org\.nbdp\.clipboard\.capture' versionCode='1' versionName='0\.1'(?: |$)",badging,re.MULTILINE),
             'ACTUAL_EXPECTED_HELPER_PACKAGE_VERSION')
        need(Path(commands[6]['stdout']['path']).stat().st_size>0,'ACTUAL_SIGNING_CERTIFICATE_REPORT_REQUIRED')
        result.update(apk=pin(OUT/'clipboard-capture.apk'),status='BUILT_REBUILT_HELPER_ARTIFACT_ONLY',
            privateKeystoreDescriptor=pin(key),privateKeystoreExported=False,
            signingCertificateReport=commands[6]['stdout'],packageVersionReport=commands[7]['stdout'],
            actualPackage=PACKAGE,actualVersionCode=1,actualVersionName='0.1')
    except BaseException as error:result['error']=type(error).__name__+':'+str(error)[:4096]
    result['elapsedMilliseconds']=round((time.clock_gettime(time.CLOCK_BOOTTIME)-started)*1000)
    receipt=write(OUT/'build-result.json',(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(dict(receipt=receipt,status=result['status'],apk=result['apk'],privateKeysExported=False)),flush=True)
    return 0 if result['status']=='BUILT_REBUILT_HELPER_ARTIFACT_ONLY' else 2


if __name__=='__main__':raise SystemExit(main(sys.argv))
