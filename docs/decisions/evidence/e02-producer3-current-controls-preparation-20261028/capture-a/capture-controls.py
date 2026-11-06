"""SOURCE ONLY: once-only producer3 pure-control capture. Never import for review.

Derived from accepted 18876-byte capture SHA70d5b7992c6e4317a0d47a585e400fa0c51240f85b0a74a7075bc1675bd3e85a.
communicate retains output in memory; retention bounds are POST_CAPTURE only.
Pending freeze/review/root release is represented by None, which fails closed.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE = Path(__file__).resolve().parent
CAPTURE = HERE
PREP = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028'
SOURCE = Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
ACTOR = '/root/producer3_capture'
MODE = 'capture-a'
SOURCE_SHA = None
MANIFEST_SHA = None
FROZEN_PLAN_SHA = None
ACCEPTED_REVIEW_DECISIONS = None  # Actual independent decisions required before source freeze.
LIMITS = {'stdout':1048576,'stderr':262144}
COUNTS = {'capture-a':[20,8,7], 'capture-b':[3]}
NAMES = {'capture-a':['observation-model','public-identity-metadata','producer2-source-wiring'],
         'capture-b':['producer3-bindings']}
def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pin(path):
    assert path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'Canonical regular source path required'
    with path.open('rb') as stream:
        a = os.fstat(stream.fileno())
        assert stat.S_ISREG(a.st_mode) and 0 <= a.st_size <= 8589934592, 'Bounded regular SOURCE/DATA only'
        digest=hashlib.sha256();size=0
        while True:
            block=stream.read(1048576)
            if not block:break
            size+=len(block);assert size<=8589934592
            digest.update(block)
        b = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    assert identity(a) == identity(b) and size == a.st_size, 'Input identity drift'
    return {'path': str(path), 'bytes': size, 'sha256': digest.hexdigest()}


def strict(raw):
    assert len(raw) <= 16777216, 'Metadata bound'
    def pairs(items):
        value = {}
        for key, item in items:
            assert key not in value, 'Duplicate metadata key'
            value[key] = item
        return value
    def invalid(_):
        raise ValueError('Nonfinite metadata')
    return json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=invalid)


def doc(path):
    assert pin(path)['bytes']<=16777216, 'Metadata bound before allocation'
    return strict(path.read_bytes())


def save(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    fd = os.open(HERE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def installed_membership():
    tree=doc(SOURCE/'dependency-tree.json');root=Path(tree['sourceRoot'])
    assert root==ROOT/'experiments/node_modules' and root.resolve(strict=True)==root
    actual={'directories':[],'files':[],'symlinks':[]}
    def walk(folder):
        for p in sorted(folder.iterdir()):
            rel=p.relative_to(root).as_posix()
            if p.is_symlink():
                target=p.resolve(strict=True);assert target.is_relative_to(root) and target!=root
                actual['symlinks'].append({'path':rel,'link':str(p.readlink()),'target':target.relative_to(root).as_posix()})
            elif p.is_dir():actual['directories'].append(rel);walk(p)
            elif p.is_file():actual['files'].append(rel)
            else:raise ValueError('Installed special file')
    walk(root)
    for k in ('directories','files'):actual[k].sort()
    actual['symlinks'].sort(key=lambda x:x['path'])
    assert actual=={k:tree[k] for k in ('directories','files','symlinks')}
    assert len(actual['files'])==816 and len(actual['directories'])==65 and len(actual['symlinks'])==2
    return actual


def read_tree(spec):
    """Hash actual SDK/guard regular-file bytes, not inventory JSON alone."""
    root=Path(spec['root'])
    assert root.is_absolute() and root.resolve(strict=True)==root and root.is_dir()
    rows=[]
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            assert not (Path(folder)/name).is_symlink(), 'Tree directory link refused'
        for name in files:
            p=Path(folder)/name
            assert not p.is_symlink(), 'Tree file link refused'
            d=pin(p);d['relativePath']=p.relative_to(root).as_posix()
            d['mode']=stat.S_IMODE(p.stat().st_mode);rows.append(d)
    rows.sort(key=lambda d:d['relativePath'])
    assert len(rows)==spec['count'] and rows==spec['files'], 'Actual full read-tree drift'
    return {'root':str(root),'count':len(rows),'files':rows}


def snapshot(ack_sha):
    assert MODE in COUNTS and all(re.fullmatch('[0-9a-f]{64}',v or '') for v in
        (SOURCE_SHA,MANIFEST_SHA,FROZEN_PLAN_SHA)), 'Pending final source pins; no execution'
    assert isinstance(ACCEPTED_REVIEW_DECISIONS,dict), 'Pending independent SOURCE decisions'
    source=pin(PREP/'subject.json');assert source['sha256']==SOURCE_SHA
    manifest=pin(PREP/'artifact-manifest.json');assert manifest['sha256']==MANIFEST_SHA
    source_plan=pin(PREP/'control-plan.json');assert source_plan['sha256']==FROZEN_PLAN_SHA
    plan=doc(CAPTURE/'control-plan.json');original_plan=doc(PREP/'control-plan.json')
    assert plan['schema']=='e02-producer3-fixed-control-capture-plan-v1' and plan['captureId']==MODE
    scopes=plan['separateScopes']
    assert [s['name'] for s in scopes]==NAMES[MODE] and [s['count'] for s in scopes]==COUNTS[MODE]
    original={s['name']:s for s in original_plan['separateScopes']}
    for s in scopes:
        o=original[s['name']]
        assert (o['name'],o['argv'],o['plannedChecks'],o['namedCases'])==(s['name'],s['argv'],s['count'],s['expectedCases'])
        assert s['timeoutSeconds']==o['timeoutSeconds']==60
        assert o['stdoutRetentionBytes']==LIMITS['stdout'] and o['stderrRetentionBytes']==LIMITS['stderr']
    inputs=doc(CAPTURE/'frozen-inputs.json');assert inputs['schema']=='e02-producer3-control-frozen-inputs-v1'
    expected=inputs['files'];assert 1<=len(expected)<=4096 and len({d['path'] for d in expected})==len(expected)
    assert inputs['actualInputCount']==len(expected) and inputs['sourceSubject']==source
    actual=[pin(Path(d['path'])) for d in expected];assert actual==expected
    required=inputs['requiredCoverage']
    assert set(required)=={'finalSubjectManifestPlan','all16Workers','all4Tests','runtimeFixtureBindings',
        'bothConfigurations','acceptedApkHelperNativeE01','provenanceAcceptances','original19',
        'diagnosticV2','oldV1ReadOperands','interpreters','baselineScalarAndOracle'}
    indexed={d['path']:d for d in expected}
    for group,descriptors in required.items():
        assert descriptors and all(indexed.get(d['path'])==d for d in descriptors), 'Missing closure category:'+group
    assert len(required['all16Workers'])==16 and len(required['all4Tests'])==4 and len(required['bothConfigurations'])==2
    assert pin(NODE)==inputs['node'] and pin(PYTHON)==inputs['python']
    trees=inputs['fullReadTrees'];assert [s['count'] for s in trees]==[434,522]
    actual_trees=[read_tree(s) for s in trees]
    membership=installed_membership()
    ack_path=CAPTURE/'coordinator-acknowledgement.json';ack_pin=pin(ack_path)
    assert ack_pin['sha256']==ack_sha and stat.S_IMODE(ack_path.stat().st_mode)==0o600
    ack=doc(ack_path)
    assert ack['schema']=='e02-producer3-controls-root-ack-v1' and ack['actor']=='/root'
    assert ack['captureId']==MODE and ack['sourceSubject']==source and ack['allowedScopes']==dict(zip(NAMES[MODE],COUNTS[MODE]))
    assert ack['runner']==pin(Path(__file__).resolve()) and ack['controlPlan']==pin(CAPTURE/'control-plan.json')
    assert ack['runnerSubject']==pin(CAPTURE/'runner-subject.json')
    assert ack['frozenInputs']==pin(CAPTURE/'frozen-inputs.json')
    for key in ('pureControlsAuthorized','stopFirstFailure','noRetry'):assert ack[key] is True
    for key in ('ordinaryRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized','servicesAuthorized','protocolCryptoOrNativeAuthorized','sdkAuthorized','roleMaterializationAuthorized'):assert ack[key] is False
    rs=doc(CAPTURE/'runner-subject.json');assert rs['runner']==ack['runner'] and rs['controlPlan']==ack['controlPlan']
    assert rs['frozenInputs']==ack['frozenInputs'] and rs['captureId']==MODE
    for d in rs['preparationArtifacts']:assert pin(Path(d['path']))==d
    reviews=[];sessions=[]
    for prefix,subject in (('source',source),('capture',ack['runnerSubject'])):
        for role,title in (('qa','Qa'),('security','Security')):
            d=ack[prefix+title+'Review'];assert pin(Path(d['path']))==d
            if prefix=='source':assert d==inputs['actualSourceReviews'][role]
            r=doc(Path(d['path']))
            assert r['role']==role and r['subject']==subject and r['decision']==ack[prefix+title+'Decision']
            assert type(r['session']) is str and r['session'].startswith('/root/') and r['session'] not in (ACTOR,'/root','/root/r5_plan_fix')
            assert r['decision'] in ACCEPTED_REVIEW_DECISIONS[prefix][role]
            sessions.append(r['session']);reviews.append(d)
    # Each source/capture review pair must have independent QA/security authors.
    assert sessions[0]!=sessions[1] and sessions[2]!=sessions[3]
    return {'sourceSubject':source,'sourceManifest':manifest,'frozenSourcePlan':source_plan,
        'frozenInputs':actual,'fullActualReadTrees':actual_trees,'installedMembership':membership,
        'interpreters':{'python':inputs['python'],'node':inputs['node']},'monitor':pin(Path(__file__).resolve()),
        'runnerSubject':ack['runnerSubject'],'controlPlan':ack['controlPlan'],
        'sourceAndCaptureReviewRecords':reviews,'coordinatorAcknowledgement':ack_pin,
        'inputManifest':pin(CAPTURE/'frozen-inputs.json')}


def output_shape(scope,raw):
    if scope['name'] in ('public-identity-metadata','producer2-source-wiring','producer3-bindings'):
        assert raw['stdout']==b''
        # Fixed original argv has default unittest verbosity. Exact dots/count/
        # OK, no skip/failure/error/extra output is permitted.
        match=re.fullmatch(rb'([.]+)\n-{70}\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n',raw['stderr'])
        assert match and len(match[1])==scope['count'] and int(match[2])==scope['count']
        return scope['count'],{scope['name']:scope['count']}
    assert scope['name']=='observation-model'
    assert raw['stderr']==b'' and raw['stdout'].endswith(b'\n') and raw['stdout'].count(b'\n')==1
    value=strict(raw['stdout'])
    assert set(value)=={'schema','ok','checks','cases','scope'}
    assert value['schema']=='e02-producer2-observation-model-controls-v1' and value['ok'] is True
    assert value['scope']=='SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME'
    assert type(value['checks']) is int and value['checks']==scope['count']==20
    assert value['cases']==scope['expectedCases'] and len(value['cases'])==20 and len(set(value['cases']))==20
    return 20,{'shared-budget-guard-proxy-and-exchange-adapter-models':20}


def one_scope(scope,ack_sha):
    # These are local immutable bindings. Global HERE/CAPTURE remains the reviewed
    # plan/root-ack directory; original observer AST uses local output HERE/ARGV.
    HERE=CAPTURE/'scopes'/scope['name'];HERE.mkdir(parents=True,mode=0o700)
    ARGV=scope['argv']
    def save(name,value):
        return globals()['save']('scopes/'+scope['name']+'/'+name,value)
    before = after = None
    child = None
    raw = {'stdout': b'', 'stderr': b''}
    receipt = dict(schema='e02-producer3-pure-scope-execution-v1', actor=ACTOR,
        parentCoordinator='/root', argv=ARGV, cwd=str(ROOT), expectedCount=scope['count'], startedUtc=utc(),
        timeoutSeconds=60, retentionBytes=LIMITS, retentionMeaning='POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP',
        pid=None, exitCode=None, signal=None, reaped=False, naturalExit=False, stdoutEOF=False, stderrEOF=False,
        forceRequested=False, forceReason=None, firstError=None, secondaryErrors=[], sourceUnchanged=False,
        observedCount=None, countAndOutputShapeMatched=False, captureMatched=False,
        controlResultAcceptedByAuthor=False, independentResultReview='PENDING_ACTUAL_OTHER_AGENTS')
    start = None
    def error(label, exc):
        value = label + ':' + type(exc).__name__ + ':' + str(exc)[:2048]
        if receipt['firstError'] is None: receipt['firstError'] = value
        else: receipt['secondaryErrors'].append(value)
    try:
        before = snapshot(ack_sha)
        save('sources-before.json', before)
        (HERE / 'tmp').mkdir(mode=0o700)
        env = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(HERE / 'tmp')}
        receipt['environment'] = env
        start = time.monotonic_ns()
        child = subprocess.Popen(ARGV, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        receipt['pid'] = child.pid
        try:
            out, err = child.communicate(timeout=60)
            raw = {'stdout':out, 'stderr':err}
            receipt['naturalExit'] = True
            receipt['stdoutEOF'] = receipt['stderrEOF'] = True
        except subprocess.TimeoutExpired as exc:
            raw = {'stdout':exc.output or b'', 'stderr':exc.stderr or b''}
            error('original-deadline', exc)
            receipt['forceRequested'] = True; receipt['forceReason'] = 'Exact owned child deadline exceeded'
            child.kill()
            out, err = child.communicate(timeout=3)
            raw = {'stdout':out, 'stderr':err}
            receipt['stdoutEOF'] = receipt['stderrEOF'] = True
        receipt['reaped'] = child.returncode is not None
        if child.returncode is not None:
            receipt['exitCode'] = child.returncode if child.returncode >= 0 else None
            receipt['signal'] = -child.returncode if child.returncode < 0 else None
            if child.returncode != 0:
                error('original-child-exit', RuntimeError(str(child.returncode)))
    except BaseException as exc:
        error('capture', exc)
        if child is not None and child.poll() is None:
            receipt['forceRequested'] = True; receipt['forceReason'] = receipt['forceReason'] or 'Capture exception'
            try:
                child.kill()
                out, err = child.communicate(timeout=3)
                raw = {'stdout':out, 'stderr':err}
                receipt['stdoutEOF'] = receipt['stderrEOF'] = True
                receipt['reaped'] = child.returncode is not None
                if child.returncode is not None:
                    receipt['exitCode'] = child.returncode if child.returncode >= 0 else None
                    receipt['signal'] = -child.returncode if child.returncode < 0 else None
            except BaseException as cleanup_error:
                error('exact-owned-cleanup', cleanup_error)
    finally:
        receipt['finishedUtc'] = utc(); receipt['elapsedNanoseconds'] = None if start is None else time.monotonic_ns() - start
        receipt['observedStreamBytes'] = {name:len(data) for name,data in raw.items()}
        receipt['truncated'] = {name:len(data) > LIMITS[name] for name,data in raw.items()}
        for name, truncated in receipt['truncated'].items():
            if truncated:
                error('post-capture-retention-overflow-' + name, ValueError(str(len(raw[name]))))
        for name,data in raw.items():
            try:
                fd = os.open(HERE / ('data.' + name), os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd,'wb') as stream:
                    stream.write(data[:LIMITS[name]]); stream.flush(); os.fsync(stream.fileno())
                receipt[name] = pin(HERE / ('data.' + name))
            except BaseException as retain_error:
                error('raw-retention-' + name, retain_error)
    try:
        count,partitions=output_shape(scope,raw)
        receipt['observedCount']=count;receipt['observedPartitions']=partitions
        receipt['countAndOutputShapeMatched']=True
    except BaseException as exc:error('original-output-shape',exc)
    try:
        after = snapshot(ack_sha)
        save('sources-after.json', after)
        receipt['sourceUnchanged'] = before is not None and before == after
    except BaseException as exc:
        error('post-capture-source-check', exc)
    receipt['captureMatched'] = bool(receipt['countAndOutputShapeMatched'] and receipt['exitCode'] == 0
        and receipt['signal'] is None and receipt['reaped'] and receipt['naturalExit']
        and receipt['stdoutEOF'] and receipt['stderrEOF'] and not receipt['forceRequested']
        and receipt['firstError'] is None and not receipt['secondaryErrors']
        and not any(receipt['truncated'].values()) and receipt['sourceUnchanged'])
    receipt['state'] = 'WRITES_STOPPED'
    receipt['result'] = 'SCOPED_DATA_CAPTURE_MATCHED_PENDING_INDEPENDENT_REVIEW' if receipt['captureMatched'] else 'STOPPED_AT_FIRST_FAILURE_NO_RETRY'
    receipt['meaning'] = 'Synthetic DATA/model and fixed-public NIP19 encoding/checksum/hash metadata only; no actual guard/network/primary/consumer/runtime/NIP44/sign/encrypt/decrypt/native/client execution or external/canonicalPASS, SDK or experiment authority.'
    save('execution.json', receipt)
    return receipt,pin(HERE/'execution.json')


def main():
    assert len(sys.argv)==4 and sys.argv[1:3]==['--execute-once','--root-ack-sha']
    ack_sha=sys.argv[3];assert re.fullmatch('[0-9a-f]{64}',ack_sha)
    # Fail before any once-only marker when pins/reviews are unresolved.
    before=snapshot(ack_sha)
    os.umask(0o077)
    save('started.json',{'actor':ACTOR,'utc':utc(),'pid':os.getpid(),'captureId':MODE,'scope':'ONCE_FIXED_DATA_ONLY'})
    save('sources-before.json',before)
    scopes=doc(CAPTURE/'control-plan.json')['separateScopes']
    results=[];after=None;terminal_error=None
    try:
        for scope in scopes:
            result,descriptor=one_scope(scope,ack_sha)
            results.append({'scope':scope['name'],'expected':scope['count'],'observed':result['observedCount'],
                'partitions':result.get('observedPartitions'),'captureMatched':result['captureMatched'],'execution':descriptor})
            if not result['captureMatched']:break
        after=snapshot(ack_sha);save('sources-after.json',after)
    except BaseException as exc:
        terminal_error=type(exc).__name__+':'+str(exc)[:2048]
    matched=len(results)==len(scopes) and all(r['captureMatched'] for r in results) and before==after and terminal_error is None
    save('execution.json',{'schema':'e02-producer3-current-control-execution-v1','actor':ACTOR,'captureId':MODE,
        'state':'WRITES_STOPPED','result':'FIXED_DATA_SCOPES_MATCHED_PENDING_REVIEW' if matched else 'STOPPED_FIRST_FAILURE_NO_RETRY',
        'sourceSubject':before['sourceSubject'],'runnerSubject':before['runnerSubject'],'runner':before['monitor'],
        'controlPlan':before['controlPlan'],'rootAcknowledgement':before['coordinatorAcknowledgement'],'scopes':results,
        'remainingNotExecuted':[s['name'] for s in scopes[len(results):]],'sourceUnchanged':before==after,'terminalError':terminal_error,
        'noRetry':True,'controlResultAcceptedByAuthor':False,'independentResultReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY',
        'noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices':True})
    save('result-artifact-manifest.json',{'schema':'e02-producer3-current-control-artifact-manifest-v1','captureId':MODE,
        'files':[pin(p) for p in sorted(CAPTURE.rglob('*')) if p.is_file()],
        'originalApiResponses':'Actual caller separately persists exact toolName/actualArguments/unmodifiedResponse. Direct terminal or all polls of genuine same yielded handle; child EOF/reap are independent.'})
    print(json.dumps({'state':'WRITES_STOPPED','captureId':MODE,'captureMatched':matched,'execution':pin(CAPTURE/'execution.json'),'scopes':results}))
    return 0 if matched else 2


if __name__=='__main__':sys.exit(main())
