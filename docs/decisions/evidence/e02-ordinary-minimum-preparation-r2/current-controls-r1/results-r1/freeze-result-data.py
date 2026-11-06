"""Freeze actual captured DATA results only; no suite import/re-execution."""
from pathlib import Path
import json,hashlib,stat
R=Path('/home/peterhorvath/apps/bitcoin/NBDP')
C=R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/current-controls-r1'
E=C.parent
OUT=C/'results-r1'

def pin(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def save(p,v):
    raw=(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode()
    fd=__import__('os').open(p,__import__('os').O_WRONLY|__import__('os').O_CREAT|__import__('os').O_EXCL,0o600)
    with __import__('os').fdopen(fd,'wb') as stream:stream.write(raw)

def doc(p):return json.loads(p.read_bytes())

execution=doc(C/'execution.json');plan=doc(C/'control-plan.json');rootAck=doc(C/'coordinator-acknowledgement.json')
assert len(execution['scopes'])==3 and [r['observed'] for r in execution['scopes']]==[20,8,7]
assert execution['sourceUnchanged'] and not execution['remainingNotExecuted']
assert (C/'sources-before.json').read_bytes()==(C/'sources-after.json').read_bytes()
scopes=[]
for row,definition in zip(execution['scopes'],plan['separateScopes']):
    p=Path(row['execution']['path']);value=doc(p);folder=p.parent
    assert value['captureMatched'] and value['exitCode']==0 and value['signal'] is None
    assert all(value[k] for k in ['naturalExit','reaped','stdoutEOF','stderrEOF','sourceUnchanged'])
    assert not value['forceRequested'] and value['firstError'] is None and not value['secondaryErrors']
    assert not any(value['truncated'].values())
    assert (folder/'sources-before.json').read_bytes()==(folder/'sources-after.json').read_bytes()
    raw=folder/'data.stdout';err=folder/'data.stderr'
    assert stat.S_IMODE(raw.stat().st_mode)==stat.S_IMODE(err.stat().st_mode)==0o600
    actual=doc(raw)['cases'] if row['scope']=='observation-model' else None
    if actual is not None:assert actual==definition['expectedCases']
    scopes.append({'scope':row['scope'],'count':row['observed'],'execution':pin(p),
        'argv':value['argv'],'stdout':pin(raw),'stderr':pin(err),
        'runtimePrintedCaseNames':actual,
        'sourceResolvedCaseMembership':definition['expectedCases'],
        'membershipMeaning':'NODE_PRINTED_EXACT_NAMED_CASES' if actual is not None else 'FIXED_PINNED_SOURCE_UNITTEST_MEMBERSHIP_NOT_VERBOSE_RUNTIME_NAMES; actual quiet output supplies exact dots/Ran count/OK only',
        'startedUtc':value['startedUtc'],'finishedUtc':value['finishedUtc'],
        'capturedElapsedNanoseconds':value['elapsedNanoseconds'],
        'elapsedMeaning':'Trusted capture span includes before-snapshot; not measured test-only time/CPU/network',
        'naturalExit':True,'exitCode':0,'signal':None,'reaped':True,'stdoutEOF':True,'stderrEOF':True,
        'forceRequested':False,'firstError':None,'secondaryErrors':[],'truncated':False,'sourceUnchanged':True,
        'captureMatchedMechanicalOnly':True,'authorAcceptedResult':False})
save(OUT/'separate-scope-results.json',{'schema':'e02-producer2-actual35-separate-data-scopes-v1','scopes':scopes,'countsSeparate':[20,8,7],'oldSuitesRerun':False,'actualRuntimeOrClientRows':0,'independentResultReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY'})
receipts=[pin(C/n) for n in ['original-tool-launch-receipt.json','original-tool-poll-01-receipt.json','original-tool-poll-02-receipt.json']]
launch=doc(Path(receipts[0]['path']));last=doc(Path(receipts[-1]['path']))
assert launch['unmodifiedResponse']['session_id']==85766 and last['unmodifiedResponse']['exit_code']==0
save(OUT/'original-tool-origin.json',{'schema':'e02-producer2-actual35-original-tool-origin-v1','actualOperator':'/root/ordinary_api35_source','rootCoordinator':'/root','actualSessionId':85766,'launchChunkId':launch['unmodifiedResponse']['chunk_id'],'pollChunkIds':[doc(Path(d['path']))['unmodifiedResponse']['chunk_id'] for d in receipts[1:]],'finalOuterExitCode':0,'originalObjects':receipts,'meaning':'Exact original toolName/actualArguments/unmodifiedResponse stored immediately by caller, separately from child journals; no synthesized missing portable lifecycle fields.'})
files=[]
for p in sorted(C.rglob('*')):
    if p.is_file() and not p.is_relative_to(OUT):
        files.append({**pin(p),'mode':oct(stat.S_IMODE(p.stat().st_mode))})
save(OUT/'raw-artifact-manifest.json',{'schema':'e02-producer2-actual35-raw-artifact-manifest-v1','files':files,'excludes':['results-r1 subtree including this manifest/subject and later independent review records'],'note':'Initial runner manifest predates final outer poll object; this additive frozen manifest includes the immediately retained launch/poll01/poll02 originals. No original artifact was rewritten.'})
subject={'schema':'e02-producer2-actual35-data-result-subject-v1','author':'/root/ordinary_api35_source','operator':'/root/ordinary_api35_source','coordinator':'/root','state':'WRITES_STOPPED_PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY',
 'scope':'CURRENT_20_OBSERVATION_MODELS_8_PUBLIC_FORMAT_7_SOURCE_WIRING_ONLY',
 'producerSource':pin(E/'subject.json'),'producerContract':pin(R/'experiments/prototypes/e02_ordinary_minimum_v2/EXPORT-CONTRACT.md'),
 'runnerSubject':pin(C/'runner-subject.json'),'runner':pin(C/'capture-controls.py'),'controlPlan':pin(C/'control-plan.json'),
 'rootAcknowledgement':pin(C/'coordinator-acknowledgement.json'),'actualReviewRecords':[pin(E/'actual-source-qa-review.json'),pin(E/'actual-source-security-review.json'),pin(C/'capture-qa-review.json'),pin(C/'capture-security-review.json')],
 'execution':pin(C/'execution.json'),'separateScopes':pin(OUT/'separate-scope-results.json'),'rawArtifactManifest':pin(OUT/'raw-artifact-manifest.json'),'originalToolOrigin':pin(OUT/'original-tool-origin.json'),
 'overallSourcesBefore':pin(C/'sources-before.json'),'overallSourcesAfter':pin(C/'sources-after.json'),'frozenInputManifest':pin(C/'frozen-inputs.json'),'fixedInputCount':957,
 'actualCountsSeparate':[20,8,7],'allNatural0NoForceNoErrorNoTruncation':True,'sourceUnchangedBeforeAfterEveryScopeAndOverall':True,'completeInstalledMembership':'816 regular files/65 directories/2 pinned in-tree symlinks before/after each scope and overall',
 'nodeNames':'Actual20 exact names emitted in JSON','pythonNames':'Source-resolved pinned8/7 unittest membership; quiet raw counts/dots/OK, not invented verbose runtime names',
 'privateRawMode':'0600','retentionMeaning':'Popen.communicate in-memory capture;1MiB/256KiB post-capture raw retention/refusal, not streaming memory limits',
 'originalOuterSessionId':85766,'originalOuterFinalExitCode':0,'reruns':0,'oldComponentSuitesExecuted':0,
 'actualGuardOrNetwork':False,'protocolSigningEncryptionDecryptionOrNativeRust':False,'sdkAndroidDockerServices':False,'leaseOrRuntimeGrantCreated':False,'ordinaryClientRows':0,
 'permittedFormatWork':'Fixed public NIP19 encoding/checksum/hash metadata and fake fs/WS/guard only',
 'consumer3ImplementedOrExecuted':False,'completion2ImplementedOrExecuted':False,'controlResultAcceptedByAuthor':False,'independentResultReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY',
 'canonicalE02':'PARTIAL22_UNCHANGED','stockE04E06Unlocked':False,'architecturalBlockersChanged':False}
save(OUT/'subject.json',subject)
print(json.dumps({'subject':pin(OUT/'subject.json'),'execution':subject['execution'],'manifest':subject['rawArtifactManifest'],'scopeResults':subject['separateScopes'],'actualCountsSeparate':[20,8,7],'originalOuterSessionId':85766,'originalOuterExitCode':0,'authorAccepted':False},indent=2))
