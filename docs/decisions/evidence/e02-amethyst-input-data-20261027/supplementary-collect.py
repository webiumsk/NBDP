"""Read-only acquired-input DATA comparison. No Git, tools or build execution."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from datetime import datetime, timezone

ROOT=Path('/tmp/nbdp-amethyst-rebuild-20261026')
HERE=Path('/tmp/nbdp-amethyst-build-inputs-20261027')
COMMIT='e6f464a1179def75274512b3c5bab921de3bf3d8'
TREE='11a90777c85c71912594612f42d9807004834f67'
ERRORS=[]


def need(value,message):
    if not value:raise ValueError(message)


def equal(actual,expected,message):
    if actual!=expected:ERRORS.append(message)
    return actual==expected


def file(path,algorithms=('sha256',),maximum=2147483648):
    path=Path(path);need(path.is_absolute(),'ABSOLUTE_INPUT')
    for p in (path,*path.parents):need(not p.is_symlink(),'SYMLINK_INPUT:'+str(path))
    hashes={a:hashlib.new(a) for a in algorithms};count=0
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:
        before=os.fstat(stream.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=maximum,'REGULAR_BOUNDED_INPUT')
        while b:=stream.read(1048576):
            count+=len(b);need(count<=maximum,'INPUT_BYTES_BOUND')
            for h in hashes.values():h.update(b)
        after=os.fstat(stream.fileno())
    fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    need(tuple(getattr(before,k) for k in fields)==tuple(getattr(after,k) for k in fields),'INPUT_CHANGED:'+str(path))
    return dict(path=str(path),bytes=count,sha256=hashes['sha256'].hexdigest()),{a:h.hexdigest() for a,h in hashes.items()}


def document(path):
    descriptor,_=file(path,maximum=67108864)
    raw=Path(path).read_bytes();need(len(raw)==descriptor['bytes'] and hashlib.sha256(raw).hexdigest()==descriptor['sha256'],'DOCUMENT_PIN_DRIFT')
    return json.loads(raw),descriptor


def write(name,value):
    path=HERE/name;raw=(json.dumps(value,indent=2)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        need(stream.write(raw)==len(raw),'SHORT_REPORT_WRITE');stream.flush();os.fsync(stream.fileno())
    return file(path)[0]


def tree(destination):
    actual=[];links=[]
    need(destination.is_dir() and not destination.is_symlink(),'REGULAR_ACQUIRED_ROOT')
    equal(stat.S_IMODE(destination.stat().st_mode),0o700,'DESTINATION_ROOT_MODE:'+str(destination))
    for path in sorted(destination.rglob('*')):
        need(len(actual)<200000,'TREE_MEMBERS_BOUND')
        rel=str(path.relative_to(destination));st=path.lstat()
        if stat.S_ISLNK(st.st_mode):
            target=os.readlink(path);resolved=path.resolve(strict=True)
            need(resolved.is_relative_to(destination.resolve()),'ACQUIRED_LINK_ESCAPE:'+rel)
            actual.append(dict(path=rel,kind='symlink',target=target));links.append(dict(path=rel,target=target,internal=True))
        elif stat.S_ISDIR(st.st_mode):actual.append(dict(path=rel,kind='dir',mode=oct(stat.S_IMODE(st.st_mode))))
        else:
            need(stat.S_ISREG(st.st_mode),'ACQUIRED_SPECIAL_FILE:'+rel)
            p,_=file(path);actual.append(dict(path=rel,kind='file',bytes=p['bytes'],sha256=p['sha256'],mode=oct(stat.S_IMODE(st.st_mode))))
    return actual,links


def archive_projection(receipt,actual,destination):
    members=receipt['archiveMembers'];need(len(members)<=200000,'RECORDED_ARCHIVE_MEMBER_BOUND')
    by_path={r['path']:r for r in actual};projected={};roots=set();hardlinks=[]
    for row in members:
        p=PurePosixPath(row['path'])
        need(not p.is_absolute() and str(p)==row['path'] and '..' not in p.parts and '.' not in p.parts,'ARCHIVE_MEMBER_PATH')
        roots.add(p.parts[0]);rel=str(PurePosixPath(*p.parts[1:]))
        if rel=='.':continue
        need(rel not in projected,'DUPLICATE_ARCHIVE_RELATIVE_MEMBER');projected[rel]=row
    equal(len(roots),1,'ONE_RECORDED_ARCHIVE_ROOT')
    expected=set(projected)
    for rel in list(expected):
        for parent in PurePosixPath(rel).parents:
            if str(parent)!='.':expected.add(str(parent))
    membership=equal(set(by_path),expected,'ARCHIVE_CURRENT_TREE_MEMBERSHIP:'+str(destination))
    for rel in expected:
        if rel not in by_path:continue
        current=by_path[rel];original=projected.get(rel)
        if original is None:equal(current,dict(path=rel,kind='dir',mode='0o700'),'IMPLICIT_DIRECTORY:'+rel);continue
        kind=original['kind']
        if kind=='dir':equal(current,dict(path=rel,kind='dir',mode='0o700'),'NORMALIZED_DIRECTORY:'+rel)
        elif kind=='symlink':equal(current,dict(path=rel,kind='symlink',target=original['target']),'ARCHIVE_SYMLINK:'+rel)
        elif kind=='file':
            equal(current['kind'],'file','ARCHIVE_FILE_KIND:'+rel);equal(current.get('bytes'),original['bytes'],'ARCHIVE_FILE_SIZE:'+rel)
            equal(current.get('mode'),oct(int(original['mode'],8)&0o755),'NORMALIZED_FILE_MODE:'+rel)
        elif kind=='hardlink':
            target=PurePosixPath(original['target']);target_rel=str(PurePosixPath(*target.parts[1:]))
            left,right=destination/rel,destination/target_rel
            same=(left.stat().st_dev,left.stat().st_ino)==(right.stat().st_dev,right.stat().st_ino)
            equal(same,True,'ARCHIVE_HARDLINK_IDENTITY:'+rel);hardlinks.append(dict(path=rel,target=target_rel,sameCurrentInode=same))
        else:ERRORS.append('RECORDED_SPECIAL_ARCHIVE_MEMBER:'+rel)
    return dict(recordedMembers=len(members),currentMembershipMatches=membership,hardlinks=hardlinks,
        meaning='Recorded extraction member projection compared with current files/modes/links; archives not reparsed or reextracted here')


def artifact(item):
    identifier=item['id'];start=len(ERRORS)
    fetch,fetch_pin=document(ROOT/'output/acquisition'/(identifier+'-fetch.json'))
    suffix='-extraction-r2.json' if identifier=='platform' else '-extraction.json'
    extracted,extracted_pin=document(ROOT/'output/acquisition'/(identifier+suffix))
    destination=Path(extracted['destination']);expected=ROOT/item['destination']
    if identifier=='platform':expected=expected/'android-37.0'
    equal(destination,expected,'EXACT_DESTINATION:'+identifier)
    archive,hashes=file(ROOT/'cache'/(identifier+'.archive'),('sha256',item['algorithm']))
    checks={
      'officialBytes':equal(archive['bytes'],item['bytes'],'PUBLISHED_ARCHIVE_SIZE:'+identifier),
      'officialDigest':equal(hashes[item['algorithm']],item['digest'],'PUBLISHED_ARCHIVE_DIGEST:'+identifier),
      'fetchArchive':equal(archive,fetch['archive'],'FETCH_ARCHIVE_PIN:'+identifier),
      'extractArchive':equal(archive,extracted['archive'],'EXTRACTION_ARCHIVE_PIN:'+identifier),
      'fetchMeasuredSha256':equal(hashes['sha256'],fetch['measuredSha256'],'FETCH_MEASURED_SHA256:'+identifier),
      'fetchPublishedAlgorithm':equal(fetch['publishedAlgorithm'],item['algorithm'],'FETCH_PUBLISHED_ALGORITHM:'+identifier),
      'fetchPublishedDigest':equal(fetch['publishedDigest'],item['digest'],'FETCH_PUBLISHED_DIGEST:'+identifier),
      'fetchToolsNotExecuted':equal(fetch['toolsExecuted'],False,'FETCH_TOOL_FLAG:'+identifier),
      'extractToolsNotExecuted':equal(extracted['toolsExecuted'],False,'EXTRACT_TOOL_FLAG:'+identifier)}
    actual,links=tree(destination)
    checks['exactReceiptInventory']=equal(actual,extracted['inventory'],'COMPLETE_RECEIPT_TREE_BYTES_MODES_LINKS:'+identifier)
    projection=archive_projection(extracted,actual,destination)
    inventory_pin=write(identifier+'-current-inventory.json',dict(destination=str(destination),rows=actual,links=links))
    kinds={kind:sum(r['kind']==kind for r in actual) for kind in ('file','dir','symlink')}
    return dict(id=identifier,fetchReceipt=fetch_pin,extractionReceipt=extracted_pin,archive=archive,
        official=dict(url=item['url'],bytes=item['bytes'],algorithm=item['algorithm'],digest=item['digest']),
        checks=checks,properties=extracted['properties'],currentInventory=inventory_pin,counts=kinds,
        regularFileBytes=sum(r.get('bytes',0) for r in actual),allCurrentSymlinksInternal=all(r['internal'] for r in links),
        archiveProjection=projection,mismatches=ERRORS[start:],toolsExecuted=False)


def main():
    os.umask(0o077);plan,plan_pin=document(ROOT/'preparation/acquisition-plan.json')
    rows=[]
    for item in plan['artifacts']:
        try:rows.append(artifact(item))
        except Exception as error:
            ERRORS.append(item['id']+':'+type(error).__name__+':'+str(error));rows.append(dict(id=item['id'],state='DATA_CHECK_FAILED'))
    source,source_receipt=document(ROOT/'output/source-archive.json')
    source_archive,_=file(ROOT/'output/source.tar');equal(source_archive,source['archive'],'SOURCE_ARCHIVE_PIN')
    equal(source['before'],source['after'],'SOURCE_BEFORE_AFTER_RECORDED_CLEAN')
    equal(source['before'],dict(commit=COMMIT,tree=TREE,status=''),'SOURCE_EXACT_COMMIT_TREE')
    failure,failure_pin=document(ROOT/'output/acquisition/platform-extract-FAILED.json')
    equal(failure['error'],'ValueError:EXPECTED_PLATFORM_API','ORIGINAL_PLATFORM_FAILURE_UNCHANGED')
    old_properties,_=file(ROOT/'tools/.stage-platform/android-37.0/source.properties')
    equal(old_properties['bytes'],343,'OLD_PLATFORM_PROPERTY_BYTES')
    equal(old_properties['sha256'],'fa89029fc0cee414cb5e44a37cd3033771217eeecb5086577bb6d9b1b03b5b5f','OLD_PLATFORM_PROPERTY_PIN')
    source1,source1_pin=document(ROOT/'preparation/subject.json')
    source2,source2_pin=document(ROOT/'preparation-r2/subject.json')
    for subject in (source1,source2):
        for descriptor in subject['sources']:equal(file(descriptor['path'])[0],descriptor,'FROZEN_SOURCE_INPUT:'+descriptor['path'])
    canonical=ROOT/'output/acquisition/platform-extraction.json';absent=not canonical.exists() and not canonical.is_symlink()
    equal(absent,True,'CANONICAL_PLATFORM_RECEIPT_COPY_MUST_STAY_ABSENT')
    api=Path('/tmp/nbdp-amethyst-acquisition-original-tool-receipts-20261027.json')
    api_raw=api.read_bytes();api_pin,_=file(api);need(hashlib.sha256(api_raw).hexdigest()==api_pin['sha256'],'API_ORIGIN_READ_DRIFT')
    snapshot=write('original-api-receipts-at-report.json',json.loads(api_raw))
    report=dict(schema='nbdp-amethyst-build-input-data-report-v1',author='/root/consumer3_preparation',
        collectedAtUtc=datetime.now(timezone.utc).isoformat(),state='CURRENT_DATA_CHECKS_MATCH_PENDING_INDEPENDENT_REVIEW' if not ERRORS else 'DATA_MISMATCH_NO_ADMISSION',
        acquisitionPlan=plan_pin,artifacts=rows,sourceArchiveReceipt=source_receipt,sourceArchive=source_archive,
        recordedSourceBefore=source['before'],recordedSourceAfter=source['after'],gitExecutedByCollector=False,
        platformLineage=dict(source1=source1_pin,source2=source2_pin,originalFailure=failure_pin,oldStageProperties=old_properties,
            failurePreserved=True,sourceFields='Actual stable37.0/revision2/version17/ext22/base/preview0; strict SOURCE2 parser, not archive edits',
            canonicalPlatformReceiptCopy=dict(path=str(canonical),state='ABSENT' if absent else 'UNEXPECTED_PRESENT',createdByCollector=False)),
        originalApiReceipts=api_pin,originalApiSemanticCopy=snapshot,
        mismatches=ERRORS,independentlyAccepted=False,grantCreated=False,toolsExecuted=False,buildExecuted=False,
        dataCollectorExecuted=True,canonicalE02='PARTIAL22_UNCHANGED',
        limits=['Current retained trees were fully reread/hashed and compared with actual extraction receipt inventories.',
          'Archive bytes were rehashed against published digests and retained fetch/extraction SHA256 pins; archive member data not reparsed/reextracted.',
          'Original API/session correspondence remains a coordinator-authenticated evidence input; this collector does not authenticate provider identities.',
          'No acquired tool, Git operation, build, client observation, independent acceptance or runtime grant follows.'])
    result=write('report.json',report);print(json.dumps(dict(report=result,mismatches=ERRORS,toolsExecuted=False)))


if __name__=='__main__':main()
