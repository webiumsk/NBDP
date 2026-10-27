"""DRAFT NOT READY: fixed three-package SDKmanager install inside owned container.

The outer exact-CID controller and root release own execution authority. This
inner program never grants consent from an actor string or an unreviewed plan.
"""
import argparse
import codecs
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import shutil
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prompt import Prompt,approved_from_xml,reject_stderr_prompt,initial_consent,dispatch_once

SDK=Path('/sdk');USER=Path('/user');OUTPUT=Path('/output')
PACKAGES=['platforms;android-37.0','build-tools;36.0.0','ndk;30.0.16248370']
COMMAND=['/bootstrap/cmdline-tools/22.0/bin/sdkmanager','--sdk_root=/sdk','--channel=0','--install',*PACKAGES]
ENV={'PATH':'/jdk/bin:/usr/bin:/bin','JAVA_HOME':'/jdk','HOME':'/user/home','ANDROID_USER_HOME':'/user/android',
    'XDG_CACHE_HOME':'/user/cache','XDG_CONFIG_HOME':'/user/config','TMPDIR':'/user/tmp','ANDROID_HOME':'/sdk','ANDROID_SDK_ROOT':'/sdk',
    'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','JAVA_TOOL_OPTIONS':'-Xmx768m -XX:MaxMetaspaceSize=256m -XX:ActiveProcessorCount=2 -Duser.home=/user/home -Djava.io.tmpdir=/user/tmp'}
CAPS={'stdout':16777216,'stderr':4194304}


def need(ok,why):
    if not ok:raise ValueError(why)


def pin(path):
    path=Path(path);need(path.is_absolute() and '..' not in path.parts,'CANONICAL_INPUT_PATH')
    for q in (path,*path.parents):need(not q.is_symlink(),'SYMLINK_INPUT')
    with path.open('rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=2147483648,'REGULAR_BOUNDED_INPUT')
        h=hashlib.sha256();count=0
        while chunk:=f.read(1048576):h.update(chunk);count+=len(chunk)
        after=os.fstat(f.fileno())
    key=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    need(key(before)==key(after)==key(path.stat()),'INPUT_DRIFT')
    return dict(path=str(path),bytes=count,sha256=h.hexdigest())


def checked(d):
    need(type(d) is dict and set(d)=={'path','bytes','sha256'} and type(d['bytes']) is int and pin(d['path'])==d,'EXACT_INPUT_PIN')
    return Path(d['path'])


def doc(path):
    raw=Path(path).read_bytes();need(len(raw)<=16777216,'METADATA_BOUND')
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs)


def record(name,value):
    raw=(json.dumps(value,indent=2)+'\n').encode();need(len(raw)<=1048576,'OUTPUT_METADATA_BOUND')
    fd=os.open(OUTPUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:need(f.write(raw)==len(raw),'SHORT_JOURNAL_WRITE');f.flush();os.fsync(f.fileno())
    fd=os.open(OUTPUT,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)


def usage():
    count=0;total=0
    for root in (SDK,USER,OUTPUT):
        for base,dirs,files in os.walk(root,followlinks=False):
            for name in dirs+files:
                path=Path(base)/name;st=path.lstat();count+=1;need(count<=200000,'WRITABLE_TREE_MEMBER_CAP')
                if stat.S_ISLNK(st.st_mode):need(path.resolve(strict=True).is_relative_to(root),'WRITABLE_LINK_ESCAPE')
                else:need(stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode),'WRITABLE_SPECIAL_FILE')
                if stat.S_ISREG(st.st_mode):total+=st.st_size;need(total<=8589934592,'WRITABLE_TREE_BYTE_CAP')
    return dict(members=count,regularBytes=total,meaning='Cooperative sampled tree budget, not an atomic aggregate quota or resource peak.')


def leader_exited(child):
    # WNOWAIT deliberately retains the unreaped leader PID until owned-group
    # signals complete. No unrelated host PID or a reaped/reused PID is signaled.
    return os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is not None


def sampled_live_group(child):
    live=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():continue
        try:
            value=(path/'stat').read_text();end=value.rfind(')');fields=value[end+2:].split()
            if int(fields[2])==child.pid and fields[0] not in ('Z','X'):live.append(int(path.name))
        except FileNotFoundError:continue
    return live


def terminate_owned(child,deadline):
    steps=[]
    # This numeric PGID is solely the fresh, still-unreaped setsid child group,
    # in the isolated container PID namespace. No general PID cleanup exists.
    if child.stdin is not None and not child.stdin.closed:child.stdin.close()
    for sig,grace in ((signal.SIGTERM,5),(signal.SIGKILL,5)):
        live=sampled_live_group(child)
        if not live:break
        need(time.monotonic()+grace<deadline,'FINITE_GROUP_CLEANUP_RESERVE')
        os.killpg(child.pid,sig);steps.append(dict(signal=sig.name,sampledBefore=live))
        stop=time.monotonic()+grace
        while time.monotonic()<stop and sampled_live_group(child):time.sleep(0.05)
    need(not sampled_live_group(child),'OWNED_GROUP_STILL_LIVE')
    need(time.monotonic()+10<deadline,'FINITE_REAP_RESERVE')
    code=child.wait(timeout=10)
    return dict(steps=steps,leaderReaped=True,returnCode=code,sampledLiveGroupAfter=[],hostileAtomicClosureClaimed=False)


def local_metadata():
    expected={'platforms/android-37.0':('platforms;android-37.0',('2','0','0')),
        'build-tools/36.0.0':('build-tools;36.0.0',('36','0','0')),'ndk/30.0.16248370':('ndk;30.0.16248370',('30','0','16248370'))}
    rows=[];found=[]
    def name(e):return e.tag.rsplit('}',1)[-1]
    for relative,(package,revision) in expected.items():
        xml=SDK/relative/'package.xml';root=ET.fromstring(xml.read_bytes())
        local=[e for e in root.iter() if name(e)=='localPackage'];need(len(local)==1 and local[0].attrib['path']==package,'EXACT_LOCAL_PACKAGE_ID')
        rev=[e for e in local[0] if name(e)=='revision'];need(len(rev)==1,'ONE_PACKAGE_REVISION')
        values={name(e):e.text for e in rev[0]};need(set(values).issubset({'major','minor','micro'}) and
            tuple(values.get(k,'0') for k in ('major','minor','micro'))==revision,'EXACT_PACKAGE_REVISION')
        licenses=[e.attrib.get('ref') for e in local[0] if name(e)=='uses-license'];need(licenses==['android-sdk-license'],'EXACT_PACKAGE_LICENSE_REFERENCE')
        if package=='platforms;android-37.0':
            api=[e.text for e in local[0].iter() if name(e)=='api-level'];need(api==['37.0'],'EXACT_PLATFORM_API_37_0')
        rows.append(dict(package=package,packageXml=pin(xml),sourceProperties=pin(SDK/relative/'source.properties')));found.append(xml)
    need(set(SDK.rglob('package.xml'))==set(found),'NO_OTHER_PACKAGE_METADATA')
    marker=SDK/'licenses/android-sdk-license';need(marker.is_file() and not marker.is_symlink(),'ACTUAL_SDKMANAGER_LICENSE_FILE_REQUIRED')
    return dict(packages=rows,actualGeneratedLicenseFile=pin(marker),meaning='SDKmanager-generated files only, never handwritten. Full installed inventory and metadata interpretation require separate independent DATA review.')


def run(p,started):
    deadline=started+1050;body_end=started+1020
    first=None;secondary=[];child=None;selector=None;outputs={};counts={k:0 for k in CAPS};eofs={k:False for k in CAPS}
    consent=initial_consent();cleanup=None;metadata=None;last_usage=None;capture_overrun=None
    def fault(why):
        nonlocal first
        if first is None:first=why
        else:secondary.append(why)
    try:
        need(p['state']=='SOURCE_ONLY_REQUIRES_OUTER_ROOT_RELEASE','DRAFT_NOT_READY')
        need(p['argv']==COMMAND and p['environment']==ENV,'FIXED_SUPPORTED_INSTALL_ONLY')
        need(set(p['inputs'])=={'repositoryXml','approvedRawLicense','archiveDataAcceptance','promptMappingAcceptance','versionProbeAcceptance','normalizerSource','promptSource','userDecision'},'EXACT_REVIEWED_INPUT_MEMBERSHIP')
        for d in [*p['inputs'].values(),*p['sourceFiles'],*p['toolFiles']]:checked(d)
        archive=doc(checked(p['inputs']['archiveDataAcceptance']));probe=doc(checked(p['inputs']['versionProbeAcceptance']))
        need(archive['decision']=='ACCEPT_ACTUAL_CMDLINE22_ARCHIVE_DATA_ONLY' and archive['sha256']=='4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583','ACCEPTED_EXACT_ARCHIVE_DATA')
        need(p['inputs']['promptMappingAcceptance']==p['inputs']['versionProbeAcceptance'] and probe['decision']=='ACCEPT_ACTUAL_JDK21_CMDLINE22_VERSION_AND_SPECIFIC_PRESENTATION_METHOD_MAPPING'
             and probe['version']=='22.0' and probe['jdk']=='21.0.13+9' and probe['licenseResponseSent'] is False and probe['packageInstallRequested'] is False,'ACCEPTED_SPECIFIC_VERSION_AND_PROMPT_MAPPING')
        decision=doc(checked(p['inputs']['userDecision']))
        need(decision['licenseConsentAuthorized'] is True and decision['userReplyVerbatim']=='true'
             and decision['exactLicenseText']['sha256']==p['approvedRawLicenseSha256'],'EXACT_RECORDED_USER_DECISION')
        xml=checked(p['inputs']['repositoryXml']).read_bytes();approved,expected=approved_from_xml(xml)
        need(checked(p['inputs']['approvedRawLicense']).read_bytes()==approved.encode(),'EXACT_APPROVED_RAW_TEXT_FILE')
        need(shutil.disk_usage(SDK).free>=17179869184,'SIXTEEN_GIB_FRESH_DISK_ADMISSION')
        for path in (SDK,USER,OUTPUT):need(path.is_dir() and not path.is_symlink() and not any(path.iterdir()),'FRESH_PRIVATE_WRITABLE_ROOTS')
        for path in ('home','android','cache','config','tmp'):(USER/path).mkdir(mode=0o700)
        gate=Prompt(expected);err_decoder=codecs.getincrementaldecoder('utf-8')('strict');err_text=''
        record('installation-request.json',dict(argv=COMMAND,environment=ENV,inputs=p['inputs'],bodySeconds=1020,totalInnerSeconds=1050,rawCaps=CAPS,licenseExpectedDisplayBytes=len(expected.encode()),licenseExpectedDisplaySha256=hashlib.sha256(expected.encode()).hexdigest(),expectedMappingIsLossy=True,rawLicenseSha256=p['approvedRawLicenseSha256']))
        for stream in CAPS:outputs[stream]=(OUTPUT/('sdkmanager.'+stream)).open('xb')
        need(time.monotonic()+30<body_end,'BODY_BUDGET_AFTER_PREFLIGHT')
        child=subprocess.Popen(COMMAND,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV,cwd=SDK,
            start_new_session=True,bufsize=0)
        need(os.getpgid(child.pid)==child.pid,'FRESH_OWNED_UNREAPED_PROCESS_GROUP')
        selector=selectors.DefaultSelector()
        for stream in CAPS:
            pipe=getattr(child,stream);os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,stream)
        next_scan=0
        while True:
            now=time.monotonic();need(now<body_end,'INSTALL_BODY_TIMEOUT')
            if now>=next_scan:last_usage=usage();next_scan=now+1
            for key,_ in selector.select(timeout=min(0.1,body_end-now)):
                stream=key.data;raw=os.read(key.fileobj.fileno(),65536)
                if not raw:
                    selector.unregister(key.fileobj);eofs[stream]=True
                    if stream=='stdout':gate.feed(b'',final=True)
                    else:reject_stderr_prompt(err_text+err_decoder.decode(b'',final=True))
                    continue
                if counts[stream]+len(raw)>CAPS[stream]:
                    allowance=CAPS[stream]-counts[stream]
                    need(outputs[stream].write(raw[:allowance])==allowance,'SHORT_RAW_PREFIX_CAPTURE');outputs[stream].flush();counts[stream]+=allowance
                    capture_overrun=dict(stream=stream,observedChunkBytes=len(raw),preservedPrefixBytes=allowance)
                    raise ValueError('RAW_'+stream.upper()+'_CAP')
                need(outputs[stream].write(raw)==len(raw),'SHORT_RAW_CAPTURE');outputs[stream].flush();counts[stream]+=len(raw)
                if stream=='stderr':
                    err_text+=err_decoder.decode(raw,final=False);reject_stderr_prompt(err_text)
                elif gate.feed(raw):
                    dispatch_once(gate,consent,record,child.stdin.write,child.stdin.flush,child.stdin.close)
            if leader_exited(child) and all(eofs.values()):break
        need(consent['sentJournalCommitted'],'ONE_APPROVED_CONSENT_WAS_NOT_SENT')
    except BaseException as e:fault(type(e).__name__+':'+str(e)[:2048])
    finally:
        if child is not None:
            try:cleanup=terminate_owned(child,deadline)
            except BaseException as e:fault('GROUP_CLEANUP:'+type(e).__name__+':'+str(e)[:2048])
        if selector is not None:selector.close()
        if child is not None:
            for pipe in (child.stdout,child.stderr):
                if pipe is not None:pipe.close()
        for stream,f in outputs.items():
            try:f.flush();os.fsync(f.fileno());f.close()
            except BaseException as e:fault('RAW_CLOSE:'+type(e).__name__+':'+str(e)[:2048])
        if first is None:
            try:
                need(cleanup['returnCode']==0 and all(eofs.values()),'NATURAL_ZERO_AND_BOTH_RAW_EOF_REQUIRED')
                need(time.monotonic()+5<deadline,'INSTALLED_METADATA_BUDGET')
                metadata=local_metadata();last_usage=usage();need(time.monotonic()<deadline,'INNER_TOTAL_BUDGET')
            except BaseException as e:fault('INSTALLED_METADATA:'+type(e).__name__+':'+str(e)[:2048])
        result=dict(state='SDKMANAGER_FINISHED_PENDING_INDEPENDENT_INSTALLED_DATA_REVIEW' if first is None else 'FAILED_OR_UNQUALIFIED_NO_RETRY',firstFault=first,secondary=secondary,
            packages=PACKAGES,consent=dict(consent,flushAndSentRecorded=consent['flushReturned'] and consent['sentJournalCommitted'],
                consumption='UNKNOWN' if consent['stdinWriteInvoked'] else 'NO_STDIN_WRITE_INVOKED',installationSuccessIndependent=True),cleanup=cleanup,rawBytes=counts,rawEOF=eofs,captureOverrun=capture_overrun,
            raw={k:pin(OUTPUT/('sdkmanager.'+k)) for k in outputs},installedMetadata=metadata,lastSampledUsage=last_usage,
            oldSdkJdkModified=False,privateKeysUsed=False,androidClientExecuted=False,canonicalE02Changed=False,hostileAtomicClosureClaimed=False,
            qualification='Installation candidate only; independent full actual DATA acceptance and versioned build binding remain mandatory.')
        record('installation-result.json',result);print(json.dumps(result),flush=True)
    return 0 if first is None else 2


def main():
    started=time.monotonic();os.umask(0o077);a=argparse.ArgumentParser();a.add_argument('--plan',required=True);a.add_argument('--plan-sha',required=True);args=a.parse_args()
    need(args.plan=='/prep/install-plan.json' and pin(args.plan)['sha256']==args.plan_sha,'EXTERNAL_EXACT_INNER_PLAN_PIN')
    need(sys.flags.isolated and sys.dont_write_bytecode and os.getuid()!=0,'NONROOT_ISOLATED_INNER_PYTHON')
    return run(doc(args.plan),started)


if __name__=='__main__':raise SystemExit(main())
