"""Fixed once-only20/8/7 synthetic DATA capture. Requires a fresh external root ack.

Popen.communicate retains output in memory until completion. Byte limits below
are post-capture file retention/refusal limits, NOT streaming memory/resource
caps. These finite trusted Python/Node suites create no child services or descendants.
Only its exact owned direct Popen child may be killed on a capture failure.
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
PREP = HERE.parent
SOURCE = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v2'
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
ACTOR = '/root/ordinary_api35_source'
CAPTURE = HERE
SOURCE_SHA = 'ef91dc64189d7c47a4b4539c4dacd93a4c5c760da8f98bf1b203040bba6eeffd'
MANIFEST_SHA = '60d55e830b4dce27ec1392b9c827e4f0ce28d2f8c6d3266e0405969fdd46d53f'
FROZEN_PLAN_SHA = '58c4ec1a81f723ff5657cadce489b07dc9c62ace2f185752b5d2a81b313678eb'
LIMITS = {'stdout':1048576,'stderr':262144}
ACCEPTED_REVIEW_DECISIONS = {
    'source': {'qa': ('ACCEPT_MINIMUM_PRODUCER_SOURCE_FOR_CHANGED_CONTROLS_ONLY',),
               'security': ('ACCEPT_MINIMUM_PRODUCER_SOURCE_FOR_CHANGED_CONTROLS_ONLY',)},
    'capture': {'qa': ('ACCEPT_PRODUCER2_FIXED_CAPTURE_SOURCE_FOR_CURRENT_DATA_CONTROLS_ONLY',),
                'security': ('ACCEPT_PRODUCER2_FIXED_CAPTURE_SOURCE_FOR_CURRENT_DATA_CONTROLS_ONLY',)}}
# Source decisions above are ACTUAL received decisions. Capture values define
# the sole permitted future scoped decision, not a claim it has been received.


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pin(path):
    assert path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), 'Canonical regular source path required'
    with path.open('rb') as stream:
        a = os.fstat(stream.fileno())
        assert stat.S_ISREG(a.st_mode) and 0 <= a.st_size <= 268435456, 'Bounded regular SOURCE/DATA only'
        raw = stream.read(268435457)
        b = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    assert identity(a) == identity(b) and len(raw) == a.st_size, 'Input identity drift'
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


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
    pin(path)
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


def snapshot(ack_sha):
    source=pin(PREP/'subject.json');assert source['sha256']==SOURCE_SHA
    manifest=pin(PREP/'artifact-manifest.json');assert manifest['sha256']==MANIFEST_SHA
    frozen_plan=pin(PREP/'execution-control-plan.json');assert frozen_plan['sha256']==FROZEN_PLAN_SHA
    plan=doc(PREP/'execution-control-plan.json');current_plan=doc(CAPTURE/'control-plan.json')
    assert len(plan['separateScopes'])==len(current_plan['separateScopes'])==3
    for original,current in zip(plan['separateScopes'],current_plan['separateScopes']):
        assert (original['name'],original['argv'],original['plannedChecks'],original['namedCases'])==(current['name'],current['argv'],current['count'],current['expectedCases'])
        assert original['timeoutSeconds']==current['timeoutSeconds']==60
        assert original['stdoutRetentionBytes']==LIMITS['stdout'] and original['stderrRetentionBytes']==LIMITS['stderr']
    inputs=doc(CAPTURE/'frozen-inputs.json');assert inputs['schema']=='e02-producer2-control-frozen-inputs-v1'
    expected=inputs['files'];assert 1<=len(expected)<=4096 and len({d['path'] for d in expected})==len(expected)
    actual=[pin(Path(d['path'])) for d in expected];assert actual==expected
    assert inputs['sourceSubject']==source
    assert [pin(PREP/('proposed-'+role+'-run-config.json')) for role in ('incoming','archive')]==inputs['configurations']
    assert pin(NODE)==inputs['node'] and pin(PYTHON)==inputs['python']
    membership=installed_membership()
    ack_path=CAPTURE/'coordinator-acknowledgement.json';ack_pin=pin(ack_path)
    assert ack_pin['sha256']==ack_sha and ack_path.stat().st_mode&0o777==0o600
    ack=doc(ack_path)
    assert set(ack)=={'schema','actor','sourceSubject','runnerSubject','runner','controlPlan',
        'sourceQaReview','sourceSecurityReview','sourceQaDecision','sourceSecurityDecision',
        'captureQaReview','captureSecurityReview','captureQaDecision','captureSecurityDecision',
        'pureControlsAuthorized','allowedScopes','stopFirstFailure','noRetry',
        'ordinaryRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized',
        'servicesAuthorized','protocolCryptoOrNativeAuthorized','sdkAuthorized'}
    assert ack['schema']=='e02-producer2-controls-root-ack-v1' and ack['actor']=='/root'
    assert ack['sourceSubject']==source and ack['allowedScopes']=={s['name']:s['count'] for s in current_plan['separateScopes']}
    assert ack['runner']==pin(Path(__file__).resolve()) and ack['controlPlan']==pin(CAPTURE/'control-plan.json')
    assert ack['runnerSubject']==pin(CAPTURE/'runner-subject.json')
    for key in ('pureControlsAuthorized','stopFirstFailure','noRetry'):assert ack[key] is True
    for key in ('ordinaryRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized','servicesAuthorized','protocolCryptoOrNativeAuthorized','sdkAuthorized'):assert ack[key] is False
    rs=doc(CAPTURE/'runner-subject.json');assert rs['runner']==ack['runner'] and rs['controlPlan']==ack['controlPlan']
    for d in rs['preparationArtifacts']:assert pin(Path(d['path']))==d
    reviews=[]
    for prefix,subject,parent in (('source',source,PREP),('capture',ack['runnerSubject'],CAPTURE)):
        sessions=[]
        for role,title in (('qa','Qa'),('security','Security')):
            d=ack[prefix+title+'Review'];assert Path(d['path']).parent==parent and pin(Path(d['path']))==d
            if prefix=='source':assert d==inputs['actualSourceReviews'][role]
            r=doc(Path(d['path']));assert set(r)=={'role','session','decision','subject'}
            assert r['role']==role and r['subject']==subject and r['decision']==ack[prefix+title+'Decision']
            assert type(r['session']) is str and r['session'].startswith('/root/') and r['session'] not in (ACTOR,'/root')
            assert r['decision'] in ACCEPTED_REVIEW_DECISIONS[prefix][role]
            sessions.append(r['session']);reviews.append(d)
        assert len(set(sessions))==2
    return {'sourceSubject':source,'sourceManifest':manifest,'frozenSourcePlan':frozen_plan,
        'frozenInputs':actual,'installedMembership':membership,'configurations':inputs['configurations'],
        'interpreters':{'python':inputs['python'],'node':inputs['node']},'monitor':pin(Path(__file__).resolve()),
        'runnerSubject':ack['runnerSubject'],'controlPlan':ack['controlPlan'],
        'sourceAndCaptureReviewRecords':reviews,'coordinatorAcknowledgement':ack_pin,
        'inputManifest':pin(CAPTURE/'frozen-inputs.json')}


def output_shape(scope,raw):
    if scope['name'] in ('public-identity-metadata','producer2-source-wiring'):
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
    receipt = dict(schema='e02-producer2-pure-scope-execution-v1', actor=ACTOR,
        parentCoordinator='/root', argv=ARGV, cwd=str(ROOT), expectedCount=scope['count'], startedUtc=utc(),
        timeoutSeconds=60, retentionBytes=LIMITS, retentionMeaning='POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP',
        pid=None, exitCode=None, signal=None, reaped=False, naturalExit=False, stdoutEOF=False, stderrEOF=False,
        forceRequested=False, forceReason=None, firstError=None, secondaryErrors=[], sourceUnchanged=False,
        observedCount=None, countAndOutputShapeMatched=False, captureMatched=False,
        controlResultAcceptedByAuthor=False, independentResultReview='PENDING_ACTUAL_OTHER_AGENTS')
    start = time.monotonic_ns()
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
        receipt['finishedUtc'] = utc(); receipt['elapsedNanoseconds'] = time.monotonic_ns() - start
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
    os.umask(0o077)
    save('started.json',{'actor':ACTOR,'utc':utc(),'pid':os.getpid(),'scope':'ONCE_FIXED_20_8_7_DATA_ONLY'})
    before=snapshot(ack_sha);save('sources-before.json',before)
    scopes=doc(CAPTURE/'control-plan.json')['separateScopes'];assert [s['count'] for s in scopes]==[20,8,7]
    results=[]
    for scope in scopes:
        result,descriptor=one_scope(scope,ack_sha)
        results.append({'scope':scope['name'],'expected':scope['count'],'observed':result['observedCount'],
            'partitions':result.get('observedPartitions'),'captureMatched':result['captureMatched'],'execution':descriptor})
        if not result['captureMatched']:break
    after=snapshot(ack_sha);save('sources-after.json',after)
    matched=len(results)==3 and all(r['captureMatched'] for r in results) and before==after
    save('execution.json',{'schema':'e02-producer2-current-control-execution-v1','actor':ACTOR,
        'state':'WRITES_STOPPED','result':'ALL_THREE_DATA_SCOPES_MATCHED_PENDING_REVIEW' if matched else 'STOPPED_FIRST_FAILURE_NO_RETRY',
        'sourceSubject':pin(PREP/'subject.json'),'runnerSubject':pin(CAPTURE/'runner-subject.json'),
        'runner':pin(Path(__file__).resolve()),'controlPlan':pin(CAPTURE/'control-plan.json'),
        'rootAcknowledgement':pin(CAPTURE/'coordinator-acknowledgement.json'),'scopes':results,
        'remainingNotExecuted':[s['name'] for s in scopes[len(results):]],'sourceUnchanged':before==after,
        'noRetry':True,'controlResultAcceptedByAuthor':False,'independentResultReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY',
        'noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices':True})
    save('result-artifact-manifest.json',{'schema':'e02-producer2-current-control-artifact-manifest-v1',
        'files':[pin(p) for p in sorted(CAPTURE.rglob('*')) if p.is_file()],
        'originalApiResponses':'Actual caller separately persists exact original toolName/arguments/response immediately.'})
    print(json.dumps({'state':'WRITES_STOPPED','captureMatched':matched,'execution':pin(CAPTURE/'execution.json'),'scopes':results}))
    return 0 if matched else 2


if __name__=='__main__':sys.exit(main())
