"""Actual DATA result freeze only; no runner/test imports or author acceptance."""
from pathlib import Path
import hashlib
import json
import os

OUT=Path(__file__).resolve().parent
CAPTURE=OUT.parent
PREP=CAPTURE.parent

def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(name,value):
 fd=os.open(OUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:f.write(json.dumps(value,indent=2)+'\n')

api=[]
for p in sorted(CAPTURE.glob('original-tool-*-receipt.json')):
 p.chmod(0o600);api.append(pin(p))
execution=json.loads((CAPTURE/'execution.json').read_text())
before=json.loads((CAPTURE/'sources-before.json').read_text())
after=json.loads((CAPTURE/'sources-after.json').read_text())
scopes=[];named=[]
plan=json.loads((PREP/'control-plan.json').read_text())
for entry in execution['scopes']:
 p=Path(entry['execution']['path']);r=json.loads(p.read_text())
 scope=next(s for s in plan['separateScopes'] if s['name']==entry['scope'])
 actual_names=scope.get('expectedClassCases')
 if scope['name']!='source-custody-and-host-inventory':actual_names=json.loads(Path(r['stdout']['path']).read_text())['cases']
 named.append({'scope':entry['scope'],'actualObservedCount':r['observedCount'],'actualNamedPartitions':r['observedPartitions'],'actualNamedCases':actual_names,'rawStdout':r['stdout'],'rawStderr':r['stderr'],'nameEvidenceMeaning':'Python class/case names were exactly matched by the capture against actual verbose stderr; Node names are actual stdout cases. Raw evidence preserved.'})
 scopes.append({'scope':entry['scope'],'receipt':pin(p),'actualArgv':r['argv'],'expected':r['expectedCount'],'observed':r['observedCount'],'partitions':r['observedPartitions'],'naturalExit':r['naturalExit'],'exitCode':r['exitCode'],'signal':r['signal'],'reaped':r['reaped'],'stdoutEOF':r['stdoutEOF'],'stderrEOF':r['stderrEOF'],'forceRequested':r['forceRequested'],'firstError':r['firstError'],'secondaryErrors':r['secondaryErrors'],'truncated':r['truncated'],'elapsedNanoseconds':r['elapsedNanoseconds'],'sourceUnchanged':r['sourceUnchanged'],'captureMatched':r['captureMatched'],'controlResultAcceptedByAuthor':r['controlResultAcceptedByAuthor'],'rawModes':{k:oct(Path(r[k]['path']).stat().st_mode&0o777) for k in ('stdout','stderr')}})
save('named-scope-results.json',{'schema':'e02-transport-source2-actual-named-scope-results-v1','scopes':named,'meaning':'Three distinct current synthetic DATA/model scopes; source1 hadzero runs, no historical pass transfer. Not real guard/network/relay/runtime qualification.'})
manifest=[pin(p) for p in sorted(CAPTURE.rglob('*')) if p.is_file() and not p.is_relative_to(OUT)]
save('raw-artifact-manifest.json',{'schema':'e02-transport-source2-actual-data-artifact-manifest-v1','files':manifest,'originalCaptureManifest':pin(CAPTURE/'result-artifact-manifest.json'),'originalApiObjects':api,'futureReviewerFilesExcluded':True,'noSelfHash':True})
save('subject.json',{'schema':'e02-transport-source2-actual18-27-6-data-result-subject-v1','actor':'/root/ordinary_api35_source','author':'/root/ordinary_api35_source','operator':'/root/ordinary_api35_source','state':'WRITES_STOPPED_PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY','scope':'THREE_CURRENT_SYNTHETIC_DATA_MODEL_SCOPES_ONLY','sourceSubject':pin(PREP/'subject.json'),'configuration':pin(PREP/'proposed-run-config.json'),'runnerSubject':pin(CAPTURE/'runner-subject.json'),'runner':pin(CAPTURE/'capture-controls.py'),'controlPlan':pin(CAPTURE/'control-plan.json'),'rootAcknowledgement':pin(CAPTURE/'coordinator-acknowledgement.json'),'sourceAndCaptureReviewRecords':before['sourceAndCaptureReviewRecords'],'sourcesBefore':pin(CAPTURE/'sources-before.json'),'sourcesAfter':pin(CAPTURE/'sources-after.json'),'frozenInputCount':len(before['frozenInputs']),'wholeSourceUnchanged':before==after,'actualInstalledMembershipCounts':{k:len(v) for k,v in before['installedMembership'].items()},'execution':pin(CAPTURE/'execution.json'),'separateActualScopes':scopes,'namedScopeResults':pin(OUT/'named-scope-results.json'),'rawArtifactManifest':pin(OUT/'raw-artifact-manifest.json'),'originalExternalApiResponses':api,'actualToolAssociation':{'launchTool':'tools.exec_command','launchChunkId':'91a8be','sessionId':72535,'pollChunkIds':['153e0a','6e8fb4'],'completionTool':'tools.write_stdin','completionChunkId':'6e8fb4','actualReturnedExitCode':0,'unavailableApiFieldsInvented':False},'controlResultAcceptedByAuthor':False,'independentResultReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY','noRetry':True,'noSourceFixAfterAttempt':True,'guard29NotReexecuted':True,'oldSource1ControlsExecuted':0,'currentScopesAreActualNewExecutionsNotCarry':True,'retentionMeaning':'Each child60s plus original3s cleanup, stdout1MiB/stderr256KiB post-capture retention/refusal; not streaming memory cap.','realGuardNetworkDockerRelayAndroidSdkNativeRustExecuted':False,'diagnosticRuntimeGrantOrLeaseCreated':False,'canonicalE02':'PARTIAL22_UNCHANGED','stockE04E06Unlocked':False,'architecturalBlockersUnchanged':['Q01','Q08','Q13','Q15','Q27'],'remaining':['Actual independent same-result-subject QA/security.','Fresh current environment/admission and exact root finite diagnostic release.','One actual noAndroid PUB/query phase/outcome/owned-cleanup observation; no such run claimed.']})
print(json.dumps({'state':'WRITES_STOPPED','subject':pin(OUT/'subject.json'),'manifest':pin(OUT/'raw-artifact-manifest.json'),'namedScopes':pin(OUT/'named-scope-results.json'),'counts':[s['observed'] for s in scopes],'allNatural0NoForceErrorTruncation':all(s['naturalExit'] and s['exitCode']==0 and s['signal'] is None and s['reaped'] and s['stdoutEOF'] and s['stderrEOF'] and not s['forceRequested'] and s['firstError'] is None and not s['secondaryErrors'] and not any(s['truncated'].values()) for s in scopes),'wholeSourceUnchanged':before==after},indent=2))
