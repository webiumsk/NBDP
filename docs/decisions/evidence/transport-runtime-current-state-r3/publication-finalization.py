from pathlib import Path
import hashlib,json,os,re,subprocess
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');D=R/'docs/decisions/evidence/transport-runtime-current-state-r3'
G=['git','--git-dir=/tmp/nbdp-publish-repo/.git','--work-tree='+str(R)]
def pin(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(R)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,d):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(d,f,indent=2);f.write('\n')
old=D/'publication-subject.json';v=json.loads(old.read_text())
for d in v['files']+[pin(old)]:
 assert pin(R/d['path'])==d
 b=subprocess.check_output(G+['show',':'+d['path']]);assert len(b)==d['bytes'] and hashlib.sha256(b).hexdigest()==d['sha256']
result=subprocess.run(G+['diff','--cached','--check'],capture_output=True)
assert result.returncode==2 and result.stderr==b''
raw=D/'initial-staged-whitespace-check.stdout'
fd=os.open(raw,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb') as f:f.write(result.stdout)
rows=[]
for line in result.stdout.decode().splitlines():
 m=re.fullmatch(r'(.+):([0-9]+): (trailing whitespace|new blank line at EOF)\.',line)
 if m:rows.append(dict(path=m[1],line=int(m[2]),kind=m[3]))
expected={'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/current-controls-r1/capture-full-source.diff','docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/full-source.diff','experiments/prototypes/e02_ordinary_minimum_v1/fixture.mjs'}
assert {d['path'] for d in rows}==expected
assert [d for d in rows if d['path'].endswith('fixture.mjs')]==[dict(path='experiments/prototypes/e02_ordinary_minimum_v1/fixture.mjs',line=34,kind='trailing whitespace')]
args=G+['diff','--cached','--check','--','.']+[':(exclude)'+p for p in sorted(expected)]
other=subprocess.run(args,capture_output=True);assert other.returncode==0 and not other.stdout and not other.stderr
report=D/'whitespace-disposition.json'
save(report,dict(schema='nbdp-frozen-artifact-whitespace-disposition-v1',actor='/root',initialAttempt=dict(launchTool='9f1a6b',session=4979,completionTool='0ab751',exitCode=1,reason='Strict all-path git whitespace check returned2 after staging; no commit or experiment.'),raw=pin(raw),diagnostics=rows,excludedPaths=sorted(expected),allOtherStagedPathsCheckExit=0,reason='Two literal unified-diff evidence artifacts preserve context-line spaces and original source whitespace. One already-reviewed source line34 has a nonfunctional trailing space. Frozen source/results remain byte-exact; this exception is disclosed for independent review rather than rewriting accepted provenance.',sourceWhitespaceRemaining='One trailing-space line34 only; no runtime correctness claim or source normalization.',canonicalStatusChanged=False))
finalizer=D/'publication-finalization.py';finalizer.write_bytes(Path(__file__).read_bytes());finalizer.chmod(0o600)
core={d['path']:d for d in v['files']}
for p in [old,raw,report,finalizer]:core[str(p.relative_to(R))]=pin(p)
w=dict(v);w['files']=[core[p] for p in sorted(core)];w['coreFileCount']=len(core);w['state']='FROZEN_R2_FOR_INDEPENDENT_DRAFT_PUBLICATION_REVIEW';w['supersededUnacceptedSubject']=pin(old);w['whitespaceDisposition']=pin(report);w['limits']=v['limits']+['Three explicit whitespace-check paths retained: two literal diff artifacts and one frozen nonfunctional source trailing space; all other staged paths check0.']
subject=D/'publication-subject-r2.json';save(subject,w)
paths=sorted(set(core)|{str(subject.relative_to(R))})
Path('/tmp/nbdp-next-runtime-checkpoint-paths.txt').write_text('\n'.join(paths)+'\n')
for i in range(0,len(paths),50):subprocess.run(G+['add','--']+paths[i:i+50],check=True)
changed=subprocess.check_output(G+['diff','--cached','--name-only'],text=True).splitlines();assert set(changed)<=set(paths)
for p in w['files']+[pin(subject)]:
 b=subprocess.check_output(G+['show',':'+p['path']]);assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
print(json.dumps(dict(subject=pin(subject),coreFiles=len(core),selectedIncludingSubject=len(paths),stagedChangedFiles=len(changed),trackedUnchanged=len(paths)-len(changed),whitespaceDiagnosticCount=len(rows),whitespaceExceptionPaths=len(expected),allOtherPathsCheckExit=0,activeConsumerAndNewSource4ControlsExcluded=True)))
