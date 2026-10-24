"""Post-control DATA inventory only; never imports runner/tests or approves results."""
from pathlib import Path
import hashlib
import json
import os

HERE=Path(__file__).resolve().parent
OUT=HERE/'results-r1'
E=HERE.parent
ACTOR='/root/ordinary_api35_source'

def pin(p):
    p=Path(p);raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def save(name,value):
    fd=os.open(OUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:stream.write(json.dumps(value,indent=2)+'\n')

OUT.mkdir(mode=0o700)
# Only metadata changes for newly authored outer response files; bytes retained.
for name in ('original-tool-launch-receipt.json','original-tool-poll-01-receipt.json'):
    (HERE/name).chmod(0o600)
execution=json.loads((HERE/'execution.json').read_text())
receipts=[]
for row in execution['scopes']:
    receipt=json.loads(Path(row['receipt']['path']).read_text())
    receipts.append({'scope':row['scope'],'expected':row['expected'],'observed':row['observed'],'receipt':pin(Path(row['receipt']['path'])),'exitCode':receipt['exitCode'],'signal':receipt['signal'],'naturalExit':receipt['naturalExit'],'reaped':receipt['reaped'],'stdoutEof':receipt['stdoutEof'],'stderrEof':receipt['stderrEof'],'forceRequested':receipt['forceRequested'],'error':receipt['error'],'elapsedNanoseconds':receipt['elapsedNanoseconds'],'sourcesUnchanged':receipt['sourcesUnchanged'],'stdoutTruncated':receipt['stdoutTruncated'],'stderrTruncated':receipt['stderrTruncated']})
source_before=json.loads((HERE/'sources-before.json').read_text())
source_after=json.loads((HERE/'sources-after.json').read_text())
artifacts=[pin(p) for p in sorted(HERE.rglob('*')) if p.is_file() and not p.is_relative_to(OUT)]
save('artifact-manifest.json',{'schema':'e02-minimum-current-control-closed-result-artifact-manifest-v1','actor':ACTOR,'files':artifacts,'includesOriginalCaptureManifestUnmodified':pin(HERE/'artifact-manifest.json'),'futureReviewsExcluded':'Explicit point-in-time member list; later coordinator/QA/security files are not retroactively members.','noSelfHash':True})
save('subject.json',{'schema':'e02-minimum-current-pure-control-result-subject-v1','author':ACTOR,'operator':ACTOR,'session':ACTOR,'coordinator':'/root','state':'WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_QA_SECURITY_RESULT_REVIEW','frozenProducerSubject':pin(E/'subject.json'),'runnerSourceSubject':pin(HERE/'runner-subject.json'),'execution':pin(HERE/'execution.json'),'closedResultArtifactManifest':pin(OUT/'artifact-manifest.json'),'coordinatorAcknowledgement':pin(HERE/'coordinator-acknowledgement.json'),'originalOuterToolReceipts':[pin(HERE/'original-tool-launch-receipt.json'),pin(HERE/'original-tool-poll-01-receipt.json')],'actualToolAssociation':{'launchTool':'tools.exec_command','launchChunkId':'8fe43f','sessionId':64511,'completionTool':'tools.write_stdin','completionChunkId':'b8c456','actualReturnedExitCode':0,'portableApiFieldsInvented':False},'separateExecutedScopes':receipts,'wholeSnapshotBefore':pin(HERE/'sources-before.json'),'wholeSnapshotAfter':pin(HERE/'sources-after.json'),'wholeSnapshotsEqual':source_before==source_after,'all112FrozenDescriptorsAnd14ArchivedInputsPerScopeAlsoChecked':True,'mechanicalCaptureFieldMeaning':'The inherited controlResultAcceptedByAuthor field means only mechanical count/output/lifecycle/source equality matching. It is not independent result acceptance or authority to activate Android.','unchangedPriorScopeOnly':{'guard':29},'unchangedGuardLink':pin(E/'unchanged-guard-scope-link.json'),'oldConsumer14ExecutedOrCarriedAsMinimumConsumer':False,'noRetry':True,'androidSdkServicesCryptoMainNativeLeasesGrantsExecuted':False,'canonicalE02':'PARTIAL22_UNCHANGED','architecturalBlockersUnchanged':['Q01','Q08','Q13','Q15','Q27'],'actualIndependentResultReviews':'PENDING_OTHER_AGENTS_NOT_AUTHORED_BY_OPERATOR','remaining':['Actual independent same-result-subject QA/security acceptance.','New root-owned strict whole-history consumer SOURCE and controls.','Fresh per-role resource grants and actual client windows, current independent primary workload and canonical integration.']})
print(json.dumps({'state':'WRITES_STOPPED','resultSubject':pin(OUT/'subject.json'),'manifest':pin(OUT/'artifact-manifest.json'),'separateCounts':{r['scope']:r['observed'] for r in receipts},'allNaturalExit0NoForceErrorTruncation':all(r['naturalExit'] and r['exitCode']==0 and r['signal'] is None and r['reaped'] and r['stdoutEof'] and r['stderrEof'] and not r['forceRequested'] and r['error'] is None and not r['stdoutTruncated'] and not r['stderrTruncated'] for r in receipts),'wholeSnapshotsEqual':source_before==source_after},indent=2))
