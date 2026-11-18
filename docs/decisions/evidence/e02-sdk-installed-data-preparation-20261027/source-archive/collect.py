"""Fixed read-only QUIESCENT SDK/official-ZIP reconciliation; no SDK tools."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
import time
import zipfile

ROOT=Path('/Data/nbdp-e02-tooling-20261027/sdk-data-preparation-r1')
SDK=Path('/Data/nbdp-e02-tooling-20261027/controller-r6/writable-r1/sdk')
OUT=ROOT/'attempt-r1'
END=0;WORK_END=0;WRITTEN=0
CAP=16777216;MEMBERS=200000;TREE_BYTES=8589934592
PACKAGES=['platforms;android-37.0','build-tools;36.0.0','ndk;30.0.16248370']
ARCHIVES=[
 dict(archive=dict(path='/tmp/nbdp-amethyst-rebuild-20261026/cache/platform.archive',bytes=67281901,sha256='840b23e827f96e64aea4c89a1194aac3dc5f6bad37edb231c5c795d890330e8d'),archiveRoot='android-37.0',installedRelativeRoot='platforms/android-37.0'),
 dict(archive=dict(path='/tmp/nbdp-amethyst-rebuild-20261026/cache/build-tools.archive',bytes=63737259,sha256='5d9ac77fb6ff43d9da518a337b4fcf8f9097113df531d99ccefe80ef7ce8250b'),archiveRoot='android-16',installedRelativeRoot='build-tools/36.0.0'),
 dict(archive=dict(path='/tmp/nbdp-amethyst-rebuild-20261026/cache/ndk.archive',bytes=738633529,sha256='753611f410d002cfcd3f3dc2ef49aad532089d3180b436c060a90bf0fcb64df2'),archiveRoot='android-ndk-r30',installedRelativeRoot='ndk/30.0.16248370')]
DISPLAY_SHA='aaf80cd0aee7e569ffa8a4be1b61189c0fefccf23068e38dfafe336289b8c723'


def need(ok,why):
    if not ok:raise ValueError(why)


def tick(final=False):need(time.monotonic()<(END if final else WORK_END),'DATA_CAPTURE_DEADLINE')


def safe(path):
    path=Path(path);need(path.is_absolute() and '..' not in path.parts,'CANONICAL_PATH')
    for p in (path,*path.parents):need(not p.is_symlink(),'SYMLINK_COMPONENT')
    return path


def pin(path):
    path=safe(path);h=hashlib.sha256();count=0
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=2147483648,'REGULAR_BOUNDED_FILE')
        while chunk:=f.read(1048576):tick();h.update(chunk);count+=len(chunk)
        after=os.fstat(f.fileno())
    identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    need(identity(before)==identity(after)==identity(path.stat()) and count==before.st_size,'FILE_READ_DRIFT')
    return dict(path=str(path),bytes=count,sha256=h.hexdigest())


def checked(d):
    need(type(d) is dict and set(d)=={'path','bytes','sha256'} and type(d['bytes']) is int and pin(d['path'])==d,'EXACT_DESCRIPTOR');return Path(d['path'])


def doc(path):
    raw=Path(path).read_bytes();need(len(raw)<=CAP,'METADATA_CAP')
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs)


def write(name,raw):
    global WRITTEN
    tick(final=True);WRITTEN+=len(raw);need(WRITTEN<=CAP,'TOTAL_OUTPUT_16MIB')
    p=OUT/name;need(p.is_relative_to(OUT) and '..' not in p.parts,'OWNED_EVIDENCE_OUTPUT')
    with p.open('xb') as f:need(f.write(raw)==len(raw),'SHORT_EVIDENCE_WRITE');f.flush();os.fsync(f.fileno())
    return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def put(name,value):return write(name,(json.dumps(value,separators=(',',':'),ensure_ascii=True)+'\n').encode())


def snapshot():
    rows={};link_modes=[];total=0
    def fail(error):raise error
    for base,dirs,files in os.walk(SDK,followlinks=False,onerror=fail):
        tick()
        for name in dirs+files:
            path=Path(base)/name;relative=path.relative_to(SDK).as_posix();need('..' not in path.parts and relative not in rows,'CLOSED_TREE_MEMBERSHIP')
            st=path.lstat();mode=oct(stat.S_IMODE(st.st_mode));need(not st.st_mode&0o7000,'NO_PRIVILEGED_MODE')
            if stat.S_ISLNK(st.st_mode):
                need(path.resolve(strict=True).is_relative_to(SDK),'STRICT_FINAL_LINK_TARGET')
                row=dict(path=relative,kind='symlink',target=os.readlink(path));link_modes.append(dict(path=relative,mode=mode))
            elif stat.S_ISDIR(st.st_mode):row=dict(path=relative,kind='dir',mode=mode)
            else:
                need(stat.S_ISREG(st.st_mode),'NO_SPECIAL_FILE');q=pin(path);total+=q['bytes'];need(total<=TREE_BYTES,'SDK_TREE_8GIB')
                row=dict(path=relative,kind='file',bytes=q['bytes'],sha256=q['sha256'],mode=mode)
            rows[relative]=row;need(len(rows)<=MEMBERS,'SDK_TREE_MEMBER_CAP')
    return dict(destination=str(SDK),inventory=[rows[k] for k in sorted(rows)],symlinkModes=sorted(link_modes,key=lambda r:r['path']),regularBytes=total)


def member_name(info,top):
    need(info.filename==info.orig_filename and not info.flag_bits&1,'UNTRANSFORMED_UNENCRYPTED_ZIP_NAME')
    value=info.filename[:-1] if info.filename.endswith('/') else info.filename;p=PurePosixPath(value)
    need(value and not p.is_absolute() and str(p)==value and '\\' not in value and '..' not in p.parts and p.parts[0]==top
         and len(value)<=1024 and not any(ord(c)<32 or ord(c)==127 for c in value),'EXACT_SAFE_ARCHIVE_MEMBER')
    return p


def compare_archives(plan,tree):
    actual={r['path']:r for r in tree['inventory']};payload={};archive_results=[];overrides=[];mode_differences=[]
    generated={p+'/package.xml' for p in ('platforms/android-37.0','build-tools/36.0.0','ndk/30.0.16248370')}
    for item in plan['archives']:
        path=checked(item['archive']);before=pin(path)
        with path.open('rb') as f:
            start=os.fstat(f.fileno());seen=set();count=0;size=0
            with zipfile.ZipFile(f) as z:
                for info in z.infolist():
                    tick();p=member_name(info,item['archiveRoot']);need(str(p) not in seen,'DUPLICATE_ZIP_MEMBER');seen.add(str(p));need(len(seen)<=MEMBERS,'ZIP_MEMBER_CAP')
                    relative='/'.join((item['installedRelativeRoot'],*p.parts[1:]));mode=info.external_attr>>16;kind=stat.S_IFMT(mode)
                    need(not mode&0o7000,'NO_PRIVILEGED_ZIP_MODE')
                    if info.is_dir():need(kind in (0,stat.S_IFDIR),'ZIP_DIRECTORY_TYPE');row=dict(path=relative,kind='dir')
                    elif kind==stat.S_IFLNK:
                        need(info.file_size<=4096,'ZIP_LINK_BODY_CAP');target=z.read(info).decode('utf-8','strict');row=dict(path=relative,kind='symlink',target=target)
                    else:
                        need(kind in (0,stat.S_IFREG) and info.file_size<=2147483648,'ZIP_REGULAR_TYPE_BOUND');h=hashlib.sha256();n=0
                        with z.open(info) as src:
                            while b:=src.read(1048576):tick();n+=len(b);need(n<=info.file_size,'ZIP_EXPANSION_BOUND');h.update(b)
                        need(n==info.file_size,'ZIP_REGULAR_EXACT_LENGTH');row=dict(path=relative,kind='file',bytes=n,sha256=h.hexdigest());size+=n;need(size<=TREE_BYTES,'ZIP_EXPANDED_TREE_CAP')
                    need(relative not in payload,'CROSS_PACKAGE_PAYLOAD_COLLISION');payload[relative]=row
                    need(relative in actual,'MISSING_OFFICIAL_PAYLOAD_MEMBER');current=actual[relative]
                    if relative in generated:
                        overrides.append(dict(path=relative,disposition='SDKMANAGER_GENERATED_OR_REWRITTEN_LOCAL_PACKAGE_XML',archive=row,actual=current))
                    else:
                        need(all(current[k]==v for k,v in row.items()),'OFFICIAL_PAYLOAD_BYTES_KIND_OR_LINK_MISMATCH:'+relative)
                    if row['kind'] in ('file','dir') and mode and current.get('mode')!=oct(stat.S_IMODE(mode)):
                        mode_differences.append(dict(path=relative,zipMode=oct(stat.S_IMODE(mode)),actualMode=current.get('mode'),disposition='REQUIRES_EXPLICIT_INDEPENDENT_MODE_REVIEW'))
                    count+=1
            end=os.fstat(f.fileno());need((start.st_dev,start.st_ino,start.st_size,start.st_mtime_ns,start.st_ctime_ns)==(end.st_dev,end.st_ino,end.st_size,end.st_mtime_ns,end.st_ctime_ns),'ZIP_DESCRIPTOR_DRIFT')
        after=pin(path);need(before==after,'ZIP_BODY_CHANGED');archive_results.append(dict(archive=after,archiveRoot=item['archiveRoot'],installedRelativeRoot=item['installedRelativeRoot'],membersCompared=count,regularBytesCompared=size))
    expected_dirs=set()
    for path in payload:
        for parent in PurePosixPath(path).parents:
            if str(parent)!='.':expected_dirs.add(str(parent))
    extras=[]
    for path,row in actual.items():
        if path in payload:continue
        if row['kind']=='dir' and path in expected_dirs:disposition='IMPLICIT_PAYLOAD_PARENT_DIRECTORY'
        elif path in generated and row['kind']=='file':disposition='SDKMANAGER_GENERATED_LOCAL_PACKAGE_XML'
        elif path=='licenses/android-sdk-license' and row['kind']=='file':disposition='ACTUAL_SDKMANAGER_GENERATED_LICENSE_RECORD'
        elif path=='licenses' and row['kind']=='dir':disposition='LICENSE_RECORD_PARENT_DIRECTORY'
        elif path=='.temp' and row['kind']=='dir' and not any(p.startswith('.temp/') for p in actual):disposition='EMPTY_SDKMANAGER_TEMP_DIRECTORY'
        else:disposition='UNCLASSIFIED_EXTRA_REQUIRES_EXPLICIT_INDEPENDENT_DISPOSITION'
        extras.append(dict(path=path,kind=row['kind'],disposition=disposition))
    digest=hashlib.sha256(json.dumps([payload[k] for k in sorted(payload)],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(archives=archive_results,allPayloadBytesKindsLinksAndMembershipMatched=True,payloadMemberCount=len(payload),payloadIndexSha256=digest,generatedXmlOverrides=overrides,extras=extras,modeDifferences=mode_differences,
        independentDispositionsRequired=bool(mode_differences or any(x['disposition'].startswith('UNCLASSIFIED') for x in extras)),meaning='All actual members retained. Generated/mode/unknown extras are explicit DATA, never silently excluded or automatically accepted.')


def copy_metadata(inner,inner_pin):
    copied=[];packages=[]
    need([p['package'] for p in inner['installedMetadata']['packages']]==PACKAGES,'EXACT_METADATA_PACKAGE_LIST')
    for package in inner['installedMetadata']['packages']:
        host_package=dict(package=package['package']);packages.append(host_package)
        for key in ('packageXml','sourceProperties'):
            original=package[key];need(original['path'].startswith('/sdk/'),'INNER_ORIGIN_SDK_PATH')
            host=SDK/original['path'][5:];before=pin(host);need(all(before[k]==original[k] for k in ('bytes','sha256')),'INNER_TO_ACTUAL_METADATA_BYTE_JOIN')
            need(before['bytes']<=1048576,'GENERATED_METADATA_COPY_CAP');raw=host.read_bytes();need(pin(host)==before,'METADATA_COPY_DRIFT')
            host_package[key]=before
            label=package['package'].replace(';','_').replace('.','-')+'-'+key;copy=write('metadata/'+label,raw)
            copied.append(dict(innerOriginal=original,actualHost=before,evidenceCopy=copy,package=package['package'],role=key))
    original=inner['installedMetadata']['actualGeneratedLicenseFile'];host=SDK/'licenses/android-sdk-license';before=pin(host)
    need(all(before[k]==original[k] for k in ('bytes','sha256')) and before['bytes']<=1048576,'ACTUAL_GENERATED_LICENSE_JOIN')
    raw=host.read_bytes();copy=write('metadata/android-sdk-license.actual',raw);need(pin(host)==before,'LICENSE_COPY_DRIFT')
    copied.append(dict(innerOriginal=original,actualHost=before,evidenceCopy=copy,role='SDKMANAGER_GENERATED_LICENSE_EVIDENCE_ONLY',leadingLF=raw.startswith(b'\n'),trailingLF=raw.endswith(b'\n')))
    return dict(packages=packages,actualGeneratedLicenseFile=before,installationResult=inner_pin,copies=copied,originalEvidence=inner['installedMetadata'],sdkRoot=str(SDK),sdkWritesPerformed=False)


def main():
    global END,WORK_END
    start=time.monotonic();END=start+180;WORK_END=start+150;os.umask(0o077)
    a=argparse.ArgumentParser();a.add_argument('--plan-sha',required=True);a.add_argument('--release',required=True);a.add_argument('--release-sha',required=True);args=a.parse_args()
    pp=pin(ROOT/'plan.json');rp=pin(args.release);need(pp['sha256']==args.plan_sha and rp['sha256']==args.release_sha,'EXTERNAL_ROOT_PINS')
    p,r=doc(pp['path']),doc(rp['path']);need(p['archives']==ARCHIVES,'EXACT_THREE_OFFICIAL_ZIP_INPUTS');need(r['executionAuthorized'] is True and r['scope']=='READ_ONLY_EXACT_INSTALLED_SDK_DATA' and r['plan']==pp,'ROOT_READONLY_DATA_RELEASE')
    for key in ('qa','security','sdkLifecycleAcceptance'):checked(r[key])
    need(r['sdkLifecycleAcceptance']==p['proofs']['lifecycleAcceptance'],'ACCEPTED_EXACT_LIFECYCLE_JOIN')
    subject=doc(checked(r['sourceSubject']))
    for d in subject['sources']:checked(d)
    for d in p['proofs'].values():checked(d)
    caller=doc(p['proofs']['caller']['path']);outer=doc(p['proofs']['outer']['path']);inner=doc(p['proofs']['inner']['path'])
    need(caller['exitCode']==0 and caller['reaped'] is True and outer['state']=='INSTALL_EXIT0_PENDING_INDEPENDENT_DATA_REVIEW' and outer['firstFault'] is None and not outer['secondaryErrors']
        and outer['cleanup']=='EXACT_CID_ABSENCE_KNOWN' and re.fullmatch('[0-9a-f]{64}',outer['cid']) and outer['jobState']['Status']=='exited' and outer['jobState']['ExitCode']==0
        and outer['jobState']['Running'] is False and outer['jobState']['OOMKilled'] is False and outer['jobState']['Error']=='','SUCCESSFUL_QUIESCENT_OUTER_ORIGIN_REQUIRED')
    need(inner['state']=='SDKMANAGER_FINISHED_PENDING_INDEPENDENT_INSTALLED_DATA_REVIEW' and inner['firstFault'] is None and inner['packages']==PACKAGES and inner['cleanup']['leaderReaped'] is True
        and inner['cleanup']['returnCode']==0 and inner['rawEOF']=={'stdout':True,'stderr':True} and inner['lastSampledUsage']['phase']=='QUIESCENT' and not inner['lastSampledUsage']['samplingIncomplete'],'STRICT_FINAL_INNER_REQUIRED')
    need(outer['innerEvidence']['installation-result.json']==p['proofs']['inner'],'EXACT_INNER_OUTER_JOIN')
    for name in ('consent-attempted.json','consent-sent.json'):checked(outer['innerEvidence'][name])
    c=inner['consent'];need(c['writeReturnedBytes']==2 and all(c[k] is True for k in ('affirmativeAttempted','attemptJournalCommitted','stdinWriteInvoked','flushReturned','sent','sentJournalCommitted','flushAndSentRecorded')) and c['consumption']=='UNKNOWN','ACTUAL_ONE_Y_FACTS_RETAINED')
    need(doc(p['proofs']['request']['path'])['licenseExpectedDisplaySha256']==DISPLAY_SHA,'SAME_APPROVED_DISPLAY')
    need(p['sdkRoot']==str(SDK) and p['collector']==pin(Path(__file__).resolve()),'FIXED_SOURCE_AND_SDK')
    safe(OUT).mkdir(mode=0o700);(OUT/'metadata').mkdir(mode=0o700);first=None
    try:
        before=snapshot();inventory=put('sdk-inventory.json',before);comparison=compare_archives(p,before);matched=put('payload-comparison.json',comparison)
        metadata=put('metadata.json',copy_metadata(inner,p['proofs']['inner']));after=snapshot();need(before==after,'TWO_COMPLETE_QUIESCENT_INVENTORIES_EQUAL')
        proof_after={key:pin(d['path']) for key,d in p['proofs'].items()};need(proof_after==p['proofs'],'PROVENANCE_CHANGED')
        result=dict(state='SDK_DATA_CAPTURED_PENDING_INDEPENDENT_REVIEW',destination=str(SDK),inventory=inventory,payloadComparison=matched,metadata=metadata,consent=p['proofs']['consent'],twoCompleteInventoriesEqual=True,
            inventoryRows=len(before['inventory']),regularBytes=before['regularBytes'],sourceProofs=p['proofs'],independentDispositionsRequired=comparison['independentDispositionsRequired'],consentConsumption='UNKNOWN',
            sdkToolsExecuted=False,sdkWritesPerformed=False,licenseOrPackageMetadataManufactured=False,qualification='Point-in-time read-only DATA; independent QA/security dispositions/acceptance required, no build/client/runtime authorization or atomic custody claim.')
        put('result.json',result);print(json.dumps(result,separators=(',',':')),flush=True)
    except BaseException as error:
        first=type(error).__name__+':'+str(error)[:2048]
        put('FAILED.json',dict(state='FAILED_DATA_CAPTURE_NO_RETRY',firstFault=first,sdkWritesPerformed=False,sdkToolsExecuted=False));raise


if __name__=='__main__':main()
