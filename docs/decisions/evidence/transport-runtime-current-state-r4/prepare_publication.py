"""One-shot DATA/provenance inspection and explicit index selection; no experiments."""
from pathlib import Path
import base64, hashlib, json, math, os, re, subprocess

R=Path('/home/peterhorvath/apps/bitcoin/NBDP')
E=R/'docs/decisions/evidence'
O=E/'transport-runtime-current-state-r4'
BASE='d2ef3097e1b700ef1ad874399424cb44084831cf'
G=['git','--git-dir=/tmp/nbdp-publish-repo/.git','--work-tree='+str(R)]

def git(*args,check=True):
    return subprocess.run(G+list(args),cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)

def pin(p):
    p=Path(p);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def save(name,value):
    p=O/name;fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    return pin(p)

def pairs(rows):
    out={}
    for k,v in rows:
        assert k not in out,('DUPLICATE_JSON_KEY',k)
        out[k]=v
    return out

def strict(p):
    def finite(x):
        v=float(x);assert math.isfinite(v),('NONFINITE_JSON_NUMBER',str(p));return v
    return json.loads(p.read_bytes(),object_pairs_hook=pairs,
      parse_float=finite,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

assert git('rev-parse','HEAD').stdout.decode().strip()==BASE
assert not git('diff','--cached','--name-only').stdout,'PRESERVE_NONEMPTY_USER_INDEX'
P5=E/'transport-runtime-progress-publication-r5'
assert pin(P5/'subject.json')['sha256']=='a3d501b867b43e85729ed574a90638136c6f99e22fe7c3f2985373960bbad9f6'
selection=set(strict(P5/'normal-core-suggestion.json')['files'])
closed=[P5,E/'e02-transport-query-diagnostic-preparation-r1',
 R/'experiments/prototypes/e02_transport_query_diagnostic_v1',
 E/'e06-terminal-custody-assessment-r1',E/'e06-cgroup-boundary-proposal-r1',O]
for root in closed:
    for p in root.rglob('*'):
        assert not p.is_symlink()
        if p.is_file():selection.add(str(p.relative_to(R)))
selection.update(['docs/PROJECT_STATE.md','docs/ROADMAP.md',
 'docs/research/experimental-validation-summary.md',
 'docs/research/transport-gate-readiness-2026-10-23.md'])
tracked=set(git('ls-files','-z').stdout.decode().split('\0'))
pattern=re.compile(r'\[[^\]]*\]\(([^\s)]+)\)')
links=[]
for _ in range(20):
    extra=set();links=[]
    for name in sorted(selection):
        p=R/name
        if p.suffix!='.md':continue
        for target in pattern.findall(p.read_text()):
            if target.startswith(('http:','https:','mailto:','#')):continue
            q=(p.parent/target.split('#')[0].strip('<>')).resolve()
            assert q.exists(),('MISSING_LOCAL_LINK',name,target)
            assert q==R or R in q.parents,('LINK_OUTSIDE_REPOSITORY',name,target)
            rel=str(q.relative_to(R))
            links.append(dict(source=name,target=target,resolved=rel))
            if q.is_file() and rel not in selection and rel not in tracked:extra.add(rel)
    if not extra:break
    assert not any('e02_transport_query_diagnostic_v2' in x or 'diagnostic-preparation-r2' in x for x in extra)
    selection.update(extra)
else:raise AssertionError('LINK_CLOSURE_LIMIT')
selection={name for name in selection if name not in tracked or
 (R/name).read_bytes()!=git('show',BASE+':'+name).stdout}

canonical=[];unique={};entries=0
for i in range(1,7):
    p=R/f'experiments/results/E{i:02}.json';v=strict(p)
    assert p.read_bytes()==git('show',BASE+':'+str(p.relative_to(R))).stdout
    for name,digest in v['source_sha256'].items():
        q=R/'experiments'/name;actual=pin(q)
        assert actual['sha256']==digest,('CANONICAL_PROVENANCE',str(q))
        unique[str(q)]=actual;entries+=1
    canonical.append(dict(record=pin(p),status=v['status'],sourceEntries=len(v['source_sha256'])))
assert entries==116 and len(unique)==26
native=E/'e06-qualification-current-source-r3/source-closure.json'
native_rows=strict(native);assert len(native_rows)==449
for d in native_rows:assert pin(d['path'])==d,('CURRENT449',d['path'])
json_count=0
for name in selection:
    p=R/name;assert p.resolve(strict=True)==p and p.is_file() and not p.is_symlink()
    if p.suffix=='.json':strict(p);json_count+=1

core=sorted(selection)
pathfile=Path('/tmp/nbdp-r4-publication-core-paths.nul')
pathfile.write_bytes(b''.join(x.encode()+b'\0' for x in core))
git('add','--pathspec-from-file='+str(pathfile),'--pathspec-file-nul')
assert set(git('diff','--cached','--name-only','-z').stdout.decode().rstrip('\0').split('\0'))==set(core)
w=git('diff','--cached','--check',check=False)
offenders=sorted(set(re.findall(r'^([^\n]+?):\d+: ',w.stdout.decode(),re.M)))
allowed={str((E/'e02-transport-query-diagnostic-preparation-r1'/n).relative_to(R)) for n in
 ['full-source.diff','instrumented-exchange.diff','lease_guard.py.typed-ast.diff','supervisor.py.typed-ast.diff']}
assert set(offenders)<=allowed,('UNEXPECTED_WHITESPACE_DIAGNOSTIC',offenders)
assert w.returncode in [0,2] and not w.stderr
checks=[]
checks.append(save('provenance-check.json',dict(schema='nbdp-publication-provenance-only-v1',
 canonicalRecords=canonical,canonicalEntries=entries,uniqueCanonicalFiles=list(unique.values()),
 currentNativeClosure=pin(native),currentNativeMembers=449,currentNativeHashesMatch=True,
 limits='Hash inspection only; no runtime/build PASS transfer or experiment execution.')))
checks.append(save('link-and-json-check.json',dict(schema='nbdp-publication-readable-links-v1',
 localLinks=links,localLinksCount=len(links),strictJsonFiles=json_count,
 limits='Selected readable file links close over this selection or prior Git files; external JSON descriptor referents may remain indexed in P5 or external prerequisites.')))
checks.append(save('whitespace-check.json',dict(schema='nbdp-literal-artifact-whitespace-disposition-v1',
 exit=w.returncode,stdoutRawBase64=base64.b64encode(w.stdout).decode(),
 stdoutBytes=len(w.stdout),stdoutSha256=hashlib.sha256(w.stdout).hexdigest(),
 stderrRawBase64=base64.b64encode(w.stderr).decode(),offendingFiles=offenders,
 exceptions=[pin(R/x) for x in offenders],
 reason='Frozen literal diff artifacts retain original bytes; these diagnostics are disclosed, not code fixes or a blanket whitespace exemption. All other selected staged paths are clean.')))
for d in checks:selection.add(str(Path(d['path']).relative_to(R)))
pathfile.write_bytes(b''.join(x.encode()+b'\0' for x in sorted(selection)))
git('add','--pathspec-from-file='+str(pathfile),'--pathspec-file-nul')
files=[pin(R/x) for x in sorted(selection)]
subject=save('publication-subject.json',dict(schema='nbdp-reviewable-evidence-extension-subject-v1',
 actor='/root',baseCommit=BASE,branch=git('branch','--show-current').stdout.decode().strip(),
 files=files,coreFiles=len(files),subjectIsAdditionalFile=True,
 p5Package=pin(P5/'subject.json'),criterionProposal=pin(E/'e06-cgroup-boundary-proposal-r1/subject.json'),
 canonicalStatus=['PASS140','PARTIAL22','PASS19','NOT_EXECUTED0','PASS25','NOT_EXECUTED0'],
 blockers=['Q01','Q08','Q13','Q15','Q27'],experimentsExecutedByThisCheck=False,
 independentPublicationReview='PENDING_ACTUAL_OTHER_QA_AND_SECURITY_SESSIONS',
 permittedPostReviewMetadata=['actual-publication-qa-review.json','actual-publication-security-review.json','acceptance.json'],
 excludedActiveWork=['experiments/prototypes/e02_transport_query_diagnostic_v2','docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2','Future Docker-boundary implementation/capability/runtime'],
 limits=['P5 archive copies are not new tests or portable replay authority.','Negative SOURCE/HOST/runtime evidence remains negative; no canonical promotion or method adoption by publication.','Actual reviewer correspondence is an external root trust input; hashes alone do not authenticate sessions.','No merge/SDK/kind/NIP/production authority.']))
git('add','--',str(Path(subject['path']).relative_to(R)))
assert len(git('diff','--cached','--name-only','-z').stdout.decode().rstrip('\0').split('\0'))==len(files)+1
print(json.dumps(dict(subject=subject,coreFiles=len(files),stagedBeforeReviews=len(files)+1,
 localLinks=len(links),strictJsonFiles=json_count,whitespaceExceptions=offenders)))
