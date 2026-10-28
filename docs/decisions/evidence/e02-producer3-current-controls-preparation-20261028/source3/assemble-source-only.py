"""Unexecuted SOURCE assembler. No imports of producer/capture modules, no children.

Completing the input spec and running this source later requires coordinator
assignment. It creates only absent plan/input artifacts, never grants/reviews.
It is intentionally unable to turn null pending evidence into a ready packet.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
OUT=ROOT/'docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3'
PREP=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2'
SOURCE=Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')
READ_TREE_ROOTS = [
 {'root':'/tmp/nbdp-e02-api35-fixture-r2/sdk','count':434},
 {'root':'/tmp/nbdp-e02-minimal-rs-v7/guard-python','count':522}]
CATEGORIES={'finalSubjectManifestPlan','all16Workers','all4Tests','runtimeFixtureBindings',
 'bothConfigurations','acceptedApkHelperNativeE01','provenanceAcceptances','original19',
 'diagnosticV2','oldV1ReadOperands','interpreters','baselineScalarAndOracle'}


def pin(path):
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    p=Path(path);before=p.lstat()
    assert stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode) and 0<=before.st_size<=8589934592
    assert p.is_absolute() and p.resolve(strict=True)==p
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        a=os.fstat(fd);assert stat.S_ISREG(a.st_mode) and 0<=a.st_size<=8589934592 and identity(before)==identity(a)
        size=0;digest=hashlib.sha256()
        with os.fdopen(fd,'rb',closefd=False) as f:
            while True:
                block=f.read(1048576)
                if not block:break
                size+=len(block);assert size<=8589934592;digest.update(block)
        b=os.fstat(fd)
    finally:os.close(fd)
    assert identity(a)==identity(b) and size==a.st_size
    return {'path':str(p),'bytes':size,'sha256':digest.hexdigest()}


def load(path):
    assert pin(path)['bytes']<=16777216
    def pairs(rows):
        result={}
        for key,value in rows:
            assert key not in result;result[key]=value
        return result
    def nonfinite(_):raise ValueError('Nonfinite JSON')
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=nonfinite)


def checked(d):
    assert type(d) is dict and set(d)=={'path','bytes','sha256'}
    assert type(d['bytes']) is int and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256'])
    assert pin(d['path'])==d
    return d


def admit_tree_roots(roots):
    assert type(roots) is list and len(roots)==len(READ_TREE_ROOTS)
    assert all(type(item) is dict and set(item)=={'root','count'} for item in roots)
    assert all(type(item['root']) is str and type(item['count']) is int for item in roots)
    assert roots==READ_TREE_ROOTS, 'Exact ordered SDK35/guard roots/counts required'


def tree(root,count):
    root=Path(root);assert root.resolve(strict=True)==root and root.is_dir()
    rows=[]
    for folder,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:assert not (Path(folder)/name).is_symlink()
        for name in files:
            p=Path(folder)/name;assert not p.is_symlink()
            d=pin(p);d.update(relativePath=p.relative_to(root).as_posix(),mode=stat.S_IMODE(p.stat().st_mode));rows.append(d)
    rows.sort(key=lambda d:d['relativePath']);assert len(rows)==count
    return {'root':str(root),'count':count,'files':rows}


def save(path,value):
    raw=(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())


def main():
    assert sys.argv[1:2]==['--assemble-source-only'] and len(sys.argv)==3
    spec=load(sys.argv[2]);assert spec['schema']=='e02-producer3-control-freeze-input-spec-v1'
    assert spec['state']=='COMPLETE_SOURCE_INPUT_SPEC_PENDING_INDEPENDENT_REVIEW'
    source=checked(spec['sourceSubject']);assert Path(source['path'])==PREP/'subject.json'
    manifest=checked(spec['sourceManifest']);assert Path(manifest['path'])==PREP/'source-packet.json'
    sourceplan=checked(spec['sourceControlPlan']);assert Path(sourceplan['path'])==PREP/'control-plan.json'
    required=spec['requiredCoverage'];assert set(required)==CATEGORIES
    by={}
    def add(d):
        d=checked(d);assert d['path'] not in by or by[d['path']]==d;by[d['path']]=d
    for group,rows in required.items():
        assert type(rows) is list and rows,'Pending required closure category:'+group
        for d in rows:add(d)
    assert len(required['all16Workers'])==16 and len(required['all4Tests'])==4
    assert len(required['bothConfigurations'])==2 and len(required['original19'])==19
    for d in (source,manifest,sourceplan):assert d in required['finalSubjectManifestPlan']
    assert required['finalSubjectManifestPlan']==[source,manifest,sourceplan]
    subject_doc=load(source['path']);packet=load(manifest['path']);mainplan=load(sourceplan['path'])
    assert subject_doc['schema']=='e02-ordinary-minimum-producer3-source-subject-v1'
    assert packet['subject']==source and packet['sourceRoot']==str(SOURCE) and packet['sources']==subject_doc['sources']
    assert subject_doc['controlPlan']==sourceplan and subject_doc['runtimeSourceCount']==16
    assert mainplan['schema']=='e02-producer3-final-source-control-plan-v1' and mainplan['sourceRoot']==str(SOURCE)
    assert mainplan['limits']=={'commandSeconds':60,'directChildReapSeconds':3,'stdoutRetentionBytes':1048576,'stderrRetentionBytes':262144}
    assert required['bothConfigurations']==subject_doc['configurations']
    configs=[load(checked(d)['path']) for d in subject_doc['configurations']]
    workers=configs[0]['sourceAndDependencyPins']
    assert workers==configs[1]['sourceAndDependencyPins']==required['all16Workers'] and len(workers)==16
    source_pins={d['path']:d for d in subject_doc['sources']};assert len(source_pins)==len(subject_doc['sources'])
    for d in subject_doc['sources']:add(d)
    assert all(source_pins.get(d['path'])==d for d in workers)
    tests=[s['source'] for s in mainplan['scopes']]
    assert required['all4Tests']==tests and all(source_pins.get(d['path'])==d for d in tests)
    assert [Path(d['path']).name for d in tests]==['test_observation_model.mjs','test_public_identity_metadata.py','test_producer2_source.py','test_producer3_bindings.py']
    assert all(Path(d['path']).parent==SOURCE for d in workers+tests)
    assert mainplan['node']==spec['node'] and mainplan['python']==spec['python']
    assert required['interpreters']==[spec['node'],spec['python']]
    declared=checked(subject_doc['sourceDataInputClosure']);add(declared)
    for row in load(declared['path'])['files']:add({k:row[k] for k in ('path','bytes','sha256')})
    for name in ('E01.json','E02.json'):
        record=ROOT/'experiments/results'/name;add(pin(record))
        canonical_sources=[]
        for relative,expected_sha in load(record)['source_sha256'].items():
            rel=Path(relative);assert not rel.is_absolute() and '..' not in rel.parts
            d=pin(ROOT/'experiments'/rel);assert d['sha256']==expected_sha;add(d);canonical_sources.append(d)
        if name=='E01.json':assert required['original19']==canonical_sources and len(canonical_sources)==19
    assert required['baselineScalarAndOracle']==[pin(ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2'/name)
        for name in ('public-scalar-format-data.json','oracle-provenance.json')]
    for role in ('qa','security'):add(spec['actualSourceReviews'][role])
    assert spec['actualSourceReviews']['qa']!=spec['actualSourceReviews']['security']
    for d in spec['additionalReadOperands']:add(d)
    for role in ('node','python'):add(spec[role])
    # Exact operand categories only: never recursively follow accepted R8 build
    # provenance into build SDK37, 90027-row worktrees, private debug key bytes.
    roots=spec['fullReadTreeRoots']
    admit_tree_roots(roots)
    trees=[]
    for item in roots:
        current=tree(item['root'],item['count']);trees.append(current)
        for row in current['files']:add({k:row[k] for k in ('path','bytes','sha256')})
    assert len(trees)==2 and [t['count'] for t in trees]==[434,522]
    assert 1<=len(by)<=4096
    files=[by[k] for k in sorted(by)]
    frozen={'schema':'e02-producer3-control-frozen-inputs-v1','sourceSubject':source,
      'sourceManifest':manifest,'sourceControlPlan':sourceplan,'node':spec['node'],'python':spec['python'],
      'actualSourceReviews':spec['actualSourceReviews'],'requiredCoverage':required,'files':files,
      'actualInputCount':len(files),'maximumInputCount':4096,'fullReadTrees':trees,
      'scope':'EXACT_ACTUAL_CONTROL_READ_CLOSURE_NO_RECURSIVE_BUILD_TREE_OR_PRIVATE_KEY_BYTES'}
    scopes={s['scope']:s for s in mainplan['scopes']}
    expected={'capture-a':[('observation-model',20),('public-identity-metadata',8),('producer2-source-wiring',7)],
              'capture-b':[('rebuilt-artifact-bindings',3)]}
    assert list(scopes)==[name for choices in expected.values() for name,count in choices]
    outputs=[]
    for mode,choices in expected.items():
        dest=OUT/mode;runner=pin(dest/'capture-controls.py');selected=[]
        for name,count in choices:
            s=scopes[name];assert s['count']==count and checked(s['source']) in tests
            script={'observation-model':'test_observation_model.mjs','public-identity-metadata':'test_public_identity_metadata.py',
                'producer2-source-wiring':'test_producer2_source.py','rebuilt-artifact-bindings':'test_producer3_bindings.py'}[name]
            argv=[spec['node']['path'],str(SOURCE/script)] if count==20 else [spec['python']['path'],'-I','-B',str(SOURCE/script)]
            assert s['source']['path']==str(SOURCE/script)
            cases=spec['nodeExpectedCases'] if count==20 else s['exactDefinedPythonNames']
            assert len(cases)==count
            selected.append({'name':name,'argv':argv,'count':count,'expectedCases':cases,'timeoutSeconds':60})
        plan={'schema':'e02-producer3-fixed-control-capture-plan-v1','captureId':mode,
          'state':'FROZEN_SOURCE_PENDING_INDEPENDENT_CAPTURE_REVIEW_AND_ROOT_RELEASE',
          'actor':'/root/producer3_capture','sourceSubject':source,'sourceManifest':manifest,
          'frozenSourcePlan':sourceplan,'runner':runner,'separateScopes':selected,
          'rawRetentionBytes':{'stdout':1048576,'stderr':262144},
          'retentionMeaning':'POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP',
          'timeoutSeconds':60,'cleanupReapSeconds':3,'stopFirstFailure':True,'noRetry':True,
          'actualInputCount':len(files),'maximumInputCount':4096,'originalApiResponses':'ACTUAL_DIRECT_TERMINAL_OR_GENUINE_SAME_SESSION_ALL_POLLS_REQUIRED',
          'actualExecutions':0,'rootAcknowledgement':None,'captureQaReview':None,'captureSecurityReview':None}
        # Preflight both complete output sets before any file creation.
        outputs.extend([(dest/'frozen-inputs.json',frozen),(dest/'control-plan.json',plan)])
    assert all(not p.exists() and not p.is_symlink() for p,v in outputs)
    for path,value in outputs:save(path,value)
    print(json.dumps({'state':'SOURCE_ASSEMBLED_PENDING_REVIEWS_NO_GRANT','actualInputCount':len(files),'actualExecutions':0,
        'files':[pin(p) for p,v in outputs]}))


if __name__=='__main__':main()
