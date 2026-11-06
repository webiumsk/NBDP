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
PREP = ROOT / 'docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2'
SOURCE = Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
ACTOR = '/root/producer3_capture'
MODE = 'capture-a'
SOURCE_SHA = '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'
MANIFEST_SHA = 'bd2e2e330984fe739045f2259e38b66a64fe6074d222b6dcd1d8d244c9b3fe46'
FROZEN_PLAN_SHA = 'cf0351831f88dff7685bc53cd8977962526529b65bf13aeb740ef7c7ba0487d6'
ACCEPTED_REVIEW_DECISIONS = {
    'source': {'qa':('ACCEPT_PRODUCER3_SOURCE_FOR_FRESH35_AND_SEPARATE3_CONTROLS_ONLY',),
        'security':('ACCEPT_FINAL_PRODUCER3_SOURCE_AND_CONTROL_DEFINITIONS_ONLY',)},
    'capture': {'qa':('ACCEPT_PRODUCER3_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY',),
        'security':('ACCEPT_PRODUCER3_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY',)}}
# Source enums above were actually received; capture enums specify the required
# future review decision and do not claim an actual review or release.
LIMITS = {'stdout':1048576,'stderr':262144}
READ_TREE_ROOTS = [
    {'root':'/tmp/nbdp-e02-api35-fixture-r2/sdk','count':434},
    {'root':'/tmp/nbdp-e02-minimal-rs-v7/guard-python','count':522}]
COUNTS = {'capture-a':[20,8,7], 'capture-b':[3]}
NAMES = {'capture-a':['observation-model','public-identity-metadata','producer2-source-wiring'],
         'capture-b':['rebuilt-artifact-bindings']}
NODE_CASES = [
    'one-shared-cap-across-two-streams','exact-boundary-two-streams-acknowledged-not-physical',
    'short-prefix-once-poisons-both-streams','zero-prefix-known-zero-throw-prefix-unknown',
    'invalid-count-family-poison-no-second-write','closed-stream-fds-and-original-upper-bound',
    'accepted-phase-writer-preserves-known-short-prefix','phase-then-proxy-consumes-same-budget',
    'guard-once-entry-exit-and-no-action-on-refusal','guard-refusal-preserved-over-retention-failure',
    'entry-and-success-retention-failure-prevent-action','callback-first-fault-and-closed-late-inert',
    'upstream-send-exact-buffer-callback-and-no-extra-guard','proxy-send-error-kept-if-observation-sink-fails',
    'proxy-intent-write-failure-never-sends','proxy-mutated-buffer-refuses-callback-completion',
    'adapter-query-preserves-exact112-byte-operands-and-raw-join','adapter-raw-is-after-original-guard-before-parse',
    'adapter-denied-backend-guard-context-no-raw-or-parse','adapter-raw-sink-fault-before-send-or-before-parse-refuses']
def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pin(path):
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    before=path.lstat()
    assert stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode) and 0<=before.st_size<=8589934592
    assert path.is_absolute() and path.resolve(strict=True)==path, 'Canonical regular source path required'
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        a=os.fstat(fd)
        assert stat.S_ISREG(a.st_mode) and 0<=a.st_size<=8589934592 and identity(before)==identity(a)
        digest=hashlib.sha256();size=0
        with os.fdopen(fd,'rb',closefd=False) as stream:
            while True:
                block=stream.read(1048576)
                if not block:break
                size+=len(block);assert size<=8589934592
                digest.update(block)
        b=os.fstat(fd)
    finally:os.close(fd)
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


def admit_read_trees(trees,indexed):
    assert type(trees) is list and len(trees)==len(READ_TREE_ROOTS)
    seen=set()
    for spec,required_root in zip(trees,READ_TREE_ROOTS):
        assert type(spec) is dict and set(spec)=={'root','count','files'}
        assert type(spec['root']) is str and type(spec['count']) is int
        assert {'root':spec['root'],'count':spec['count']}==required_root, 'Wrong ordered read-tree root/count'
        assert type(spec['files']) is list and len(spec['files'])==spec['count']
        for row in spec['files']:
            assert type(row) is dict and set(row)=={'path','bytes','sha256','relativePath','mode'}
            rel=Path(row['relativePath'])
            assert not rel.is_absolute() and '..' not in rel.parts and str(Path(spec['root'])/rel)==row['path']
            assert row['path'] not in seen;seen.add(row['path'])
            descriptor={k:row[k] for k in ('path','bytes','sha256')}
            assert indexed.get(row['path'])==descriptor, 'Read-tree row absent from exact frozen file closure'


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
    manifest=pin(PREP/'source-packet.json');assert manifest['sha256']==MANIFEST_SHA
    source_plan=pin(PREP/'control-plan.json');assert source_plan['sha256']==FROZEN_PLAN_SHA
    plan=doc(CAPTURE/'control-plan.json');original_plan=doc(PREP/'control-plan.json')
    assert plan['schema']=='e02-producer3-fixed-control-capture-plan-v1' and plan['captureId']==MODE
    assert plan['rawRetentionBytes']==LIMITS and plan['timeoutSeconds']==60 and plan['cleanupReapSeconds']==3
    assert plan['stopFirstFailure'] is True and plan['noRetry'] is True
    scopes=plan['separateScopes']
    assert [s['name'] for s in scopes]==NAMES[MODE] and [s['count'] for s in scopes]==COUNTS[MODE]
    assert original_plan['schema']=='e02-producer3-final-source-control-plan-v1'
    assert original_plan['sourceRoot']==str(SOURCE)
    assert original_plan['limits']=={'commandSeconds':60,'directChildReapSeconds':3,
        'stdoutRetentionBytes':LIMITS['stdout'],'stderrRetentionBytes':LIMITS['stderr']}
    original={s['scope']:s for s in original_plan['scopes']}
    assert list(original)==NAMES['capture-a']+NAMES['capture-b']
    for s in scopes:
        o=original[s['name']]
        argv=[str(NODE),o['source']['path']] if s['name']=='observation-model' else [str(PYTHON),'-I','-B',o['source']['path']]
        assert s['argv']==argv and s['count']==o['count'] and s['timeoutSeconds']==60
        assert pin(Path(o['source']['path']))==o['source']
        assert s['expectedCases']==(NODE_CASES if s['name']=='observation-model' else o['exactDefinedPythonNames'])
    inputs=doc(CAPTURE/'frozen-inputs.json');assert inputs['schema']=='e02-producer3-control-frozen-inputs-v1'
    assert inputs['sourceManifest']==manifest and inputs['sourceControlPlan']==source_plan
    assert plan['sourceSubject']==source and plan['sourceManifest']==manifest and plan['frozenSourcePlan']==source_plan
    expected=inputs['files'];assert 1<=len(expected)<=4096 and len({d['path'] for d in expected})==len(expected)
    indexed={d['path']:d for d in expected};trees=inputs['fullReadTrees'];admit_read_trees(trees,indexed)
    assert inputs['actualInputCount']==len(expected) and inputs['sourceSubject']==source
    actual=[pin(Path(d['path'])) for d in expected];assert actual==expected
    required=inputs['requiredCoverage']
    assert set(required)=={'finalSubjectManifestPlan','all16Workers','all4Tests','runtimeFixtureBindings',
        'bothConfigurations','acceptedApkHelperNativeE01','provenanceAcceptances','original19',
        'diagnosticV2','oldV1ReadOperands','interpreters','baselineScalarAndOracle'}
    for group,descriptors in required.items():
        assert descriptors and all(indexed.get(d['path'])==d for d in descriptors), 'Missing closure category:'+group
    assert len(required['all16Workers'])==16 and len(required['all4Tests'])==4 and len(required['bothConfigurations'])==2
    assert pin(NODE)==inputs['node'] and pin(PYTHON)==inputs['python']
    assert original_plan['node']==inputs['node'] and original_plan['python']==inputs['python']
    subject_doc=doc(PREP/'subject.json');packet=doc(PREP/'source-packet.json')
    assert subject_doc['schema']=='e02-ordinary-minimum-producer3-source-subject-v1'
    assert packet['subject']==source and packet['sourceRoot']==str(SOURCE) and packet['sources']==subject_doc['sources']
    assert subject_doc['controlPlan']==source_plan and subject_doc['runtimeSourceCount']==16
    assert required['finalSubjectManifestPlan']==[source,manifest,source_plan]
    assert required['bothConfigurations']==subject_doc['configurations']
    source_pins={d['path']:d for d in subject_doc['sources']};assert len(source_pins)==len(subject_doc['sources'])
    for d in subject_doc['sources']:assert indexed.get(d['path'])==d
    configs=[doc(Path(d['path'])) for d in subject_doc['configurations']]
    assert all(pin(Path(d['path']))==d for d in subject_doc['configurations'])
    workers=configs[0]['sourceAndDependencyPins']
    assert workers==configs[1]['sourceAndDependencyPins']==required['all16Workers'] and len(workers)==16
    assert all(source_pins.get(d['path'])==d for d in workers)
    test_pins=[s['source'] for s in original_plan['scopes']]
    assert required['all4Tests']==test_pins and all(source_pins.get(d['path'])==d for d in test_pins)
    assert [Path(d['path']).name for d in test_pins]==['test_observation_model.mjs','test_public_identity_metadata.py','test_producer2_source.py','test_producer3_bindings.py']
    assert all(Path(d['path']).parent==SOURCE for d in workers+test_pins)
    assert required['interpreters']==[inputs['node'],inputs['python']]
    declared=subject_doc['sourceDataInputClosure'];assert pin(Path(declared['path']))==declared and indexed.get(declared['path'])==declared
    for row in doc(Path(declared['path']))['files']:
        d={k:row[k] for k in ('path','bytes','sha256')}
        assert indexed.get(d['path'])==d, 'Missing producer-declared actual read operand'
    for name in ('E01.json','E02.json'):
        record=ROOT/'experiments/results'/name
        assert indexed.get(str(record))==pin(record)
        canonical_sources=[]
        for relative,expected_sha in doc(record)['source_sha256'].items():
            rel=Path(relative);assert not rel.is_absolute() and '..' not in rel.parts
            operand=ROOT/'experiments'/rel;d=pin(operand)
            assert d['sha256']==expected_sha and indexed.get(str(operand))==d, 'Missing canonical source operand'
            canonical_sources.append(d)
        if name=='E01.json':assert required['original19']==canonical_sources and len(canonical_sources)==19
    assert required['baselineScalarAndOracle']==[pin(ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2'/name)
        for name in ('public-scalar-format-data.json','oracle-provenance.json')]
    actual_trees=[read_tree(s) for s in trees]
    for tree in actual_trees:
        for row in tree['files']:
            descriptor={k:row[k] for k in ('path','bytes','sha256')}
            assert indexed.get(row['path'])==descriptor, 'Read-tree row absent from exact frozen file closure'
    membership=installed_membership()
    ack_path=CAPTURE/'coordinator-acknowledgement.json';ack_pin=pin(ack_path)
    assert ack_pin['sha256']==ack_sha and stat.S_IMODE(ack_path.stat().st_mode)==0o600
    ack=doc(ack_path)
    assert set(ack)=={'schema','actor','captureId','sourceSubject','runnerSubject','runner','controlPlan',
        'frozenInputs','sourceQaReview','sourceSecurityReview','sourceQaDecision','sourceSecurityDecision',
        'captureQaReview','captureSecurityReview','captureQaDecision','captureSecurityDecision',
        'pureControlsAuthorized','allowedScopes','stopFirstFailure','noRetry',
        'ordinaryRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized',
        'servicesAuthorized','protocolCryptoOrNativeAuthorized','sdkAuthorized','roleMaterializationAuthorized',
        'admissionModelAcceptance'}
    assert ack['schema']=='e02-producer3-controls-root-ack-v2' and ack['actor']=='/root'
    assert ack['captureId']==MODE and ack['sourceSubject']==source and ack['allowedScopes']==dict(zip(NAMES[MODE],COUNTS[MODE]))
    assert ack['runner']==pin(Path(__file__).resolve()) and ack['controlPlan']==pin(CAPTURE/'control-plan.json')
    assert ack['runnerSubject']==pin(CAPTURE/'runner-subject.json')
    assert ack['frozenInputs']==pin(CAPTURE/'frozen-inputs.json')
    for key in ('pureControlsAuthorized','stopFirstFailure','noRetry'):assert ack[key] is True
    for key in ('ordinaryRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized','servicesAuthorized','protocolCryptoOrNativeAuthorized','sdkAuthorized','roleMaterializationAuthorized'):assert ack[key] is False
    rs=doc(CAPTURE/'runner-subject.json');assert rs['runner']==ack['runner'] and rs['controlPlan']==ack['controlPlan']
    assert rs['frozenInputs']==ack['frozenInputs'] and rs['captureId']==MODE
    for d in rs['preparationArtifacts']:assert pin(Path(d['path']))==d
    combined=pin(CAPTURE.parent/'subject.json')
    combined_doc=doc(CAPTURE.parent/'subject.json')
    assert combined_doc['schema']=='e02-producer3-bound-capture-source-subject-v1'
    assert combined_doc['producerSource']==source and combined_doc['producerContract']==manifest
    assert combined_doc['captures'][MODE]=={'runner':ack['runner'],'runnerSubject':ack['runnerSubject'],
        'controlPlan':ack['controlPlan'],'frozenInputs':ack['frozenInputs']}
    assert combined_doc['modelSource']==pin(CAPTURE.parent/'test_admission_models.py')
    model_pin=ack['admissionModelAcceptance'];assert pin(Path(model_pin['path']))==model_pin
    models=doc(Path(model_pin['path']))
    assert set(models)=={'schema','actor','decision','subject','captureSource','reviews','countsSeparate','runtimeAuthorized','ordinaryRowsQualified'}
    assert models['schema']=='e02-producer3-capture-admission-model-acceptance-v1' and models['actor']=='/root'
    assert models['decision']=='ACCEPT_ACTUAL_PRODUCER3_CAPTURE_9_ADMISSION_MODELS_ONLY'
    assert models['captureSource']==combined and models['countsSeparate']==[9]
    assert models['runtimeAuthorized'] is False and models['ordinaryRowsQualified']==0
    assert pin(Path(models['subject']['path']))==models['subject']
    assert set(models['reviews'])=={'qa','security'}
    model_reviewers=[]
    for role,d in models['reviews'].items():
        assert pin(Path(d['path']))==d;r=doc(Path(d['path']))
        assert set(r)=={'role','session','decision','subject'} and r['role']==role
        assert r['subject']==models['subject'] and r['decision']=='ACCEPT_ACTUAL_PRODUCER3_CAPTURE_9_ADMISSION_MODELS_ONLY'
        assert r['session'].startswith('/root/') and r['session'] not in ('/root',ACTOR,'/root/r5_plan_fix')
        model_reviewers.append(r['session'])
    assert len(set(model_reviewers))==2
    reviews=[];sessions=[]
    for prefix,subject in (('source',source),('capture',ack['runnerSubject'])):
        for role,title in (('qa','Qa'),('security','Security')):
            d=ack[prefix+title+'Review'];assert pin(Path(d['path']))==d
            if prefix=='source':assert d==inputs['actualSourceReviews'][role]
            r=doc(Path(d['path']))
            assert set(r)=={'role','session','decision','subject'}, 'Closed independent review record required'
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
        'inputManifest':pin(CAPTURE/'frozen-inputs.json'),'captureSource':combined,'admissionModelAcceptance':model_pin,
        'admissionModelDataSubject':models['subject'],'admissionModelReviews':models['reviews']}


def output_shape(scope,raw):
    if scope['name'] in ('public-identity-metadata','producer2-source-wiring','rebuilt-artifact-bindings'):
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
        startedUtcMeaning='SCOPE_START_BEFORE_INPUT_SNAPSHOT',childStartedUtc=None,
        elapsedMeaning='CHILD_LAUNCH_BRACKET_THROUGH_COMMUNICATE_OR_OWNED_REAP_EXCLUDES_BEFORE_SNAPSHOT',
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
        receipt['childStartedUtc']=utc();start = time.monotonic_ns()
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
        'sourceManifest':before['sourceManifest'],'frozenSourcePlan':before['frozenSourcePlan'],
        'frozenInputs':before['inputManifest'],'captureSource':before['captureSource'],
        'admissionModelAcceptance':before['admissionModelAcceptance'],
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
