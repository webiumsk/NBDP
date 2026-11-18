"""Proposed container-only build. Requires separate reviewed root execution.

Container must be exact pinned image/user/caps/resources/mounts/network. Root
owns finite outer supervision and exact container cleanup after any outcome.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tarfile
import time

WORK=Path('/work'); SOURCE=WORK/'source'; OUT=Path('/output')
JDK=Path('/jdk'); SDK=Path('/sdk')


def require(value,message):
    if not value:raise ValueError(message)


def pin(path):
    h=hashlib.sha256();count=0
    with path.open('rb') as stream:
        while block:=stream.read(1048576):h.update(block);count+=len(block)
    return dict(bytes=count,sha256=h.hexdigest(),mode=stat.S_IMODE(path.stat().st_mode))


def snapshot():
    result={}
    for path in sorted(SOURCE.rglob('*')):
        require(len(result)<200000,'BUILD_TREE_MEMBER_BOUND')
        rel=str(path.relative_to(SOURCE))
        if path.is_symlink():
            require(path.resolve(strict=True).is_relative_to(SOURCE),'BUILD_LINK_ESCAPE')
            result[rel]=dict(symlink=os.readlink(path))
        elif path.is_file():result[rel]=pin(path)
        elif not path.is_dir():raise ValueError('BUILD_SPECIAL_FILE')
    return result


def source_archive():
    require(not SOURCE.exists(),'FRESH_BUILD_WORKCOPY_REQUIRED')
    SOURCE.mkdir(mode=0o700)
    receipt=json.loads(Path('/input/source-archive.json').read_text())
    actual=pin(Path('/input/source.tar'))
    require({k:actual[k] for k in ('bytes','sha256')}=={k:receipt['archive'][k] for k in ('bytes','sha256')},'SOURCE_ARCHIVE_PIN')
    require(receipt['before']==receipt['after']==dict(commit='e6f464a1179def75274512b3c5bab921de3bf3d8',
        tree='11a90777c85c71912594612f42d9807004834f67',status=''),'ORIGINAL_SOURCE_PROVENANCE')
    total=0;seen=set()
    with tarfile.open('/input/source.tar','r:') as archive:
        for info in archive:
            p=PurePosixPath(info.name)
            require(not p.is_absolute() and str(p)==info.name and '..' not in p.parts
                and '\\' not in info.name and p not in seen and len(seen)<200000,'SOURCE_MEMBER_PATH')
            seen.add(p);require(info.isdir() or info.isfile(),'SOURCE_LINK_OR_SPECIAL_REFUSED')
            total+=info.size;require(info.size<=536870912 and total<=2147483648,'SOURCE_ARCHIVE_EXPANSION_BOUND')
            target=SOURCE/str(p)
            if info.isdir():target.mkdir(parents=True,exist_ok=True,mode=0o700);continue
            target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with archive.extractfile(info) as src,os.fdopen(fd,'wb') as dst:
                shutil.copyfileobj(src,dst,1048576)
                dst.flush();os.fsync(dst.fileno())
            require(target.stat().st_size==info.size,'EXACT_SOURCE_MEMBER_SIZE')
            os.chmod(target,info.mode&0o755)
    require(not (SOURCE/'.git').exists(),'NO_GIT_CONFIG_IN_BUILD')


def write(name,value):
    fd=os.open(OUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def main():
    os.umask(0o077)
    require(os.getuid()==1000 and os.environ.get('GRADLE_USER_HOME')=='/cache/gradle','ISOLATED_BUILD_USER_CACHE')
    require(os.environ.get('JAVA_TOOL_OPTIONS')=='-Duser.home=/work/user','ISOLATED_JDK_USER_HOME')
    require(os.environ.get('ANDROID_USER_HOME')=='/work/user/.android','ISOLATED_ANDROID_USER_HOME')
    user=WORK/'user';require(not user.exists(),'FRESH_USER_HOME_NO_KEYS_MAVENLOCAL')
    user.mkdir(mode=0o700)
    (user/'.m2/repository').mkdir(parents=True,mode=0o700)
    (user/'.android').mkdir(mode=0o700)
    require(not Path('/cache/gradle').exists(),'FRESH_GRADLE_CACHE_REQUIRED')
    source_archive();before=snapshot();write('workcopy-before.json',before)
    require((SDK/'build-tools/36.0.0/apksigner').is_file(),'PINNED_BUILD_TOOLS_LAYOUT')
    require((SDK/'ndk/30.0.16248370/source.properties').is_file(),'PINNED_NDK_LAYOUT')
    require((SDK/'platforms/android-37.0/android.jar').is_file(),'PINNED_PLATFORM_LAYOUT')
    argv=['/bin/sh',str(SOURCE/'gradlew'),':amethyst:assembleFdroidDebug','-PdisableAbiSplits=true',
        '--no-daemon','--max-workers=1',
        '-Dorg.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=768m -Dfile.encoding=UTF-8 -Duser.home=/work/user',
        '-Pkotlin.daemon.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=512m',
        '-x','spotlessApply','-x',':installGitHook',
        '-Pkotlin.compiler.execution.strategy=in-process','--info']
    write('build-command.json',dict(argv=argv,sourceCommit='e6f464a1179def75274512b3c5bab921de3bf3d8',
        signing='Fresh isolated debug identity only; no old APK hash/release signature claim'))
    started=time.monotonic();error=None;code=None
    try:
        with (OUT/'build.stdout').open('xb') as stdout,(OUT/'build.stderr').open('xb') as stderr:
            child=subprocess.run(argv,cwd=SOURCE,env=dict(os.environ),input=b'',stdout=stdout,stderr=stderr,timeout=3600)
            code=child.returncode
    except Exception as exc:error=type(exc).__name__+':'+str(exc)[:1024]
    after=snapshot();write('workcopy-after.json',after)
    changed=[p for p,v in before.items() if after.get(p)!=v]
    modules={str(Path(p).parent) for p in before if Path(p).name in ('build.gradle','build.gradle.kts')}
    output_prefixes=tuple(str(PurePosixPath(module)/folder)
                          for module in modules for folder in ('build','.gradle','.kotlin','.cxx'))
    def output_allowed(p):
        return any(p==prefix or p.startswith(prefix+'/') for prefix in output_prefixes)
    unplanned=[p for p in after.keys()-before.keys() if not output_allowed(p)]
    write('source-equality.json',dict(originalFilesUnchanged=not changed,changedOriginalFiles=changed,
        unplannedNewFiles=unplanned,allowedNewRoots='Known Gradle module build/.gradle/.kotlin/.cxx only; never original-file changes'))
    state='BUILD_FAILED' if code!=0 or error else 'BUILT_PENDING_APK_VALIDATION'
    write('build-result.json',dict(state=state,exitCode=code,error=error,elapsedWallSeconds=time.monotonic()-started,
        originalFilesUnchanged=not changed,unplannedNewFiles=unplanned,sourceLinkedNotReproducibleClaim=True,
        runtimeClientQualified=False,requiresRootContainerCleanup=True))
    require(code==0 and error is None and not changed and not unplanned,'BUILD_OR_SOURCE_EQUALITY_FAILED')
    apks=sorted((SOURCE/'amethyst/build/outputs/apk/fdroid/debug').glob('*.apk'))
    require(1<=len(apks)<=8,'EXPECTED_FDROID_DEBUG_APKS')
    rows=[]
    for i,apk in enumerate(apks):
        destination=OUT/('rebuilt-fdroid-debug-'+str(i)+'.apk');require(not destination.exists(),'FRESH_APK_OUTPUT')
        shutil.copyfile(apk,destination);os.chmod(destination,0o600)
        with (OUT/('apk-'+str(i)+'-signature.txt')).open('xb') as signature:
            signed=subprocess.run([str(SDK/'build-tools/36.0.0/apksigner'),'verify','--verbose','--print-certs',str(destination)],
                input=b'',stdout=signature,stderr=subprocess.STDOUT,timeout=60)
        require(signed.returncode==0,'APK_SIGNATURE_VERIFY_FAILED')
        with (OUT/('apk-'+str(i)+'-badging.txt')).open('xb') as badging:
            details=subprocess.run([str(SDK/'build-tools/36.0.0/aapt'),'dump','badging',str(destination)],
                input=b'',stdout=badging,stderr=subprocess.STDOUT,timeout=60)
        require(details.returncode==0,'APK_BADGING_FAILED')
        text=(OUT/('apk-'+str(i)+'-badging.txt')).read_text()
        require("name='com.vitorpamplona.amethyst.debug'" in text and 'application-debuggable' in text,'EXPECTED_DEBUG_APPLICATION')
        rows.append(dict(path=str(destination),**pin(destination),signatureReport='apk-'+str(i)+'-signature.txt'))
    keys=list(user.rglob('*.keystore'))+list(user.rglob('*.jks'))
    require(keys,'FRESH_LAB_DEBUG_KEY_METADATA_REQUIRED')
    for key in keys:os.chmod(key,0o600)
    write('rebuilt-apks.json',dict(apks=rows,debugKeyMetadata=[dict(relativePath=str(k.relative_to(user)),**pin(k)) for k in keys],
        keysExported=False,oldApkIdentityClaimed=False,ordinaryClientRowsQualified=0))


if __name__=='__main__':main()
