from pathlib import Path
import ast,base64,hashlib,json,os,re,subprocess,urllib.parse
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');E=R/'docs/decisions/evidence';D=E/'transport-runtime-current-state-r3'
G=['git','--git-dir=/tmp/nbdp-publish-repo/.git','--work-tree='+str(R)]
def pin(p):
 b=p.read_bytes();return dict(path=str(p.relative_to(R)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def save(p,v):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(v,f,indent=2);f.write('\n')
old=D/'publication-subject-r2.json';assert pin(old)['sha256']=='e4afc9b1a33bff1fac5a98627bf8e0950db80a54f2f7378d0345b01ea72220b9'
v=json.loads(old.read_text())
for d in v['files']+[pin(old)]:assert pin(R/d['path'])==d
for role,session in [('qa','/root/p4_publication_qa'),('security','/root/p4_publication_security')]:
 findings=[dict(id='QA-PUBLICATION-WHITESPACE-DISPOSITION-001',severity='MEDIUM',evidence='Raw diagnostic output itself adds36 whitespace warnings; all-path staged check73/4, earlier disposition37/3 incomplete.',requiredFix='Keep raw bytes, explicitly include fourth exception and correct counts; check all other paths0.')] if role=='qa' else [dict(id='SEC-PUBLICATION-MINIMUM-NSEC-METADATA-001',severity='LOW',evidence='Four documentary inputs carry65-character unused incoming NSEC; actual driver uses correct63-character publicscalar2.',requiredFix='Visible additive disposition with actual operand and versioned encoding-consistency task; no frozen source rewrite.'),dict(id='SEC-PUBLICATION-STALE-METHOD-STATE-002',severity='LOW',evidence='Readiness still says minimum method not implemented/executed despite SOURCE/mock acceptance.',requiredFix='Distinguish accepted SOURCE/mock scopes from unqualified runtime/consumer/reconciliation.')]
 save(D/('actual-held-r2-'+role+'-review.json'),dict(schema='nbdp-actual-independent-review-transcription-v1',transcribedBy='/root',reviewer=session,role=role,decision='HOLD',subject=pin(old),findings=findings,limits=['Exact prior-stage publication review; no tests/imports/runtime/edits by reviewer.','No frozen evidence or source activation approved.']))
src=R/'experiments/prototypes/e02_ordinary_minimum_v1';driver=src/'android_driver.py';tree=ast.parse(driver.read_text())
correct=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='NSEC' for x in n.targets))
assert len(correct)==63
badfiles=[src/'minimum-plan.json',src/'ui-plan.json',src/'fixture-plan.json',E/'e02-ordinary-minimum-preparation-r1/oracle-provenance.json']
bad=set()
for p in badfiles:bad.update(x for x in re.findall(r'nsec1[023456789acdefghjklmnpqrstuvwxyz]+',p.read_text()) if len(x)==65)
assert len(bad)==1;malformed=bad.pop();assert hashlib.sha256(malformed.encode()).hexdigest()=='3cf12c327fe62e329783b028d94e1410d3e4ac5db3eebdf13cd72ad9c8bd2e2c'
metadata=D/'minimum-input-metadata-disposition.json'
save(metadata,dict(schema='nbdp-minimum-documentary-input-disposition-v1',actor='/root',finding='SEC-PUBLICATION-MINIMUM-NSEC-METADATA-001',severity='LOW',documentaryFiles=[pin(p) for p in badfiles],unusedMalformedLiteral=dict(value=malformed,length=65,sha256=hashlib.sha256(malformed.encode()).hexdigest()),operativeRuntimeInput=dict(value=correct,length=63,sha256=hashlib.sha256(correct.encode()).hexdigest(),driver=pin(driver),publicDisposableScalar=2),disposition='Preserve frozen source/results. Supervisor consumes role/account/peer/window and driver consumes its exact63-character ROLE_SPECS operand. The65-character documentary literal is not an executed input and must not be copied or silently normalized. Consumer independently binds actual driver operand/account GUI/wire. No actual wrong account or credential leak demonstrated.',futureTask=dict(owner='implementer, independently reviewed by QA/security',task='Versioned correction of documentary NSEC fields with checksum/payload/length and exact driver-input equality DATA regression.',prerequisites='Preserve current frozen SOURCE and accepted actual scopes; no receipt retargeting.',acceptance='All revised role encodings are valid and exactly match the actual driver operands; no old metadata or runtime result rewritten.'),runtimeAuthorized=False,canonicalStatusChanged=False))
docrels=['docs/PROJECT_STATE.md','docs/ROADMAP.md','docs/research/experimental-validation-summary.md','docs/research/transport-gate-readiness-2026-10-23.md','docs/research/amethyst-control-runbook.md']
before=[]
for i,rel in enumerate(docrels):
 p=R/rel;oldpin=pin(p);copy=D/('held-r2-document-'+str(i+1)+'.md.txt');fd=os.open(copy,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(p.read_bytes())
 before.append(dict(previousOrigin=oldpin,preservedCopy=pin(copy)))
p=R/docrels[0];t=p.read_text();t=t.replace('One fresh13 capture/3 path/16 guard-model/14 admission batch is the next scoped task after explicit root release; no R3/R4 controls or live activation are claimed in this checkpoint.','The [actual fresh batch](decisions/evidence/e06-request-phase-diagnostic-source-r4/controls-external-r1/failed-batch-disposition.json) then completed13+3 with independent acceptance, but guard16 produced7passes/9errors during mock installation; admission14 remained NOT_EXECUTED after the first failed suite. No retry or live activation occurred. The separate [read-only HOST inspection](decisions/evidence/e06-pidfd-host-feature-inspection-r1/result.json) confirms the exact Python lacks the two pidfd APIs there too, while glibc2.39 exposes their symbols. No pidfd or signal was invoked by that inspection. A new SOURCE-only adapter proposal is under preparation; symbol availability is not runtime containment proof.')
t+='''\nCurrent LOW metadata debt: an unused65-character incoming NSEC remains in four frozen documentary inputs; the actual driver uses the correct63-character public scalar2 operand. The [explicit disposition](decisions/evidence/transport-runtime-current-state-r3/minimum-input-metadata-disposition.json) preserves originals, names the operative input and assigns a versioned encoding-consistency correction. The strict consumer does not consume the malformed literal. No actual wrong account, secret disclosure or cryptographic flaw is established.\n''';p.write_text(t)
p=R/docrels[1];t=p.read_text().replace('held pending actual SOURCE4 qualification of the source-reviewed pidfd-custody/census-cleanup fixes; older expiry/registration history remains visible.','held after actual SOURCE4 guard16 produced7passes/9mock-installation errors; admission14 was not executed. Actual13+3 passed separately. HOST read-only inspection confirms missing Python pidfd APIs and available libc symbols; a new SOURCE-only adapter proposal is next, before meaningful model/real7 qualification. Older failures remain visible.');p.write_text(t)
p=R/docrels[2];t=p.read_text();t+='''\nSubsequent SOURCE4 actual batch: independently accepted13+3 only; guard16 retained7passes/9mock-installation errors, admission14 NOT_EXECUTED, no retry/live strace/Node. The exact read-only HOST probe confirms missing Python pidfd APIs and present glibc symbols, without calling them. A versioned SOURCE-only adapter is under preparation. The current metadata disposition also names an unused malformed65-character plan NSEC; actual driver/account input remains the correct63-character public fixture.\n''';p.write_text(t)
p=R/docrels[3];t=p.read_text().replace('the new method is not implemented/executed or a PASS','new producer SOURCE and mock/metadata scopes are accepted, while actual role windows, strict consumer and full reconciliation remain incomplete; no PASS')
t+='''\nThe separately released SOURCE4 batch subsequently stopped:13+3 passed with independent acceptance; guard16 had7passes/9mock-installation errors, leaving all five new security families unqualified. Admission14 NOT_EXECUTED, no retry, actual strace/Node0. [Failed-batch evidence](../decisions/evidence/e06-request-phase-diagnostic-source-r4/controls-external-r1/failed-batch-disposition.json) and [HOST API inspection](../decisions/evidence/e06-pidfd-host-feature-inspection-r1/result.json) define the next task: implementer prepares a versioned standard-libc adapter SOURCE and meaningful models, QA/security review, then one explicitly released fresh batch. Existing ownership/timing/real7 gates stay intact. No Product Owner input is currently needed.\n\nThe [LOW documentary NSEC disposition](../decisions/evidence/transport-runtime-current-state-r3/minimum-input-metadata-disposition.json) distinguishes an unused malformed plan literal from the correct actual driver operand and assigns a versioned encoding-consistency fix. Frozen source and accepted mock results remain unchanged; no runtime wrong-account claim.\n''';p.write_text(t)
p=R/docrels[4];t=p.read_text();t+='''\nDo not copy the unused65-character incoming NSEC in old plan/provenance fields. The [metadata disposition](../decisions/evidence/transport-runtime-current-state-r3/minimum-input-metadata-disposition.json) pins the actual63-character public driver operand and the future versioned consistency repair. Actual account GUI, source input, wire roles and export binding remain mandatory; the consumer does not silently normalize malformed plan data.\n''';p.write_text(t)
save(D/'current-document-delta-r3.json',dict(schema='nbdp-preserved-publication-document-delta-v1',actor='/root',supersededSubject=pin(old),preservedBefore=before,current=[pin(R/p) for p in docrels],reason='Resolve current wording/LOW metadata finding and record completed independently reviewed SOURCE4 partial failure plus separate HOST inspection.'))
core={d['path']:pin(R/d['path']) for d in v['files']};core[str(old.relative_to(R))]=pin(old)
for root in [E/'e06-request-phase-diagnostic-source-r4',E/'e06-pidfd-host-feature-inspection-r1',D]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.relative_to(R).parts:core[str(p.relative_to(R))]=pin(p)
script=D/'publication-resolution-r3.py';script.write_bytes(Path(__file__).read_bytes());script.chmod(0o600);core[str(script.relative_to(R))]=pin(script)
for i in range(0,len(core),50):subprocess.run(G+['add','--']+sorted(core)[i:i+50],check=True)
check=subprocess.run(G+['diff','--cached','--check'],capture_output=True);assert check.returncode==2 and check.stderr==b''
rows=[]
for line in check.stdout.decode().splitlines():
 m=re.fullmatch(r'(.+):([0-9]+): (trailing whitespace|new blank line at EOF)\.',line)
 if m:rows.append(dict(path=m[1],line=int(m[2]),kind=m[3]))
exceptions=set(json.loads((D/'whitespace-disposition.json').read_text())['excludedPaths'])|{str((D/'initial-staged-whitespace-check.stdout').relative_to(R))}
assert {r['path'] for r in rows}==exceptions and len(rows)==73,(len(rows),{r['path'] for r in rows})
other=subprocess.run(G+['diff','--cached','--check','--','.']+[':(exclude)'+p for p in sorted(exceptions)],capture_output=True);assert other.returncode==0 and not other.stdout and not other.stderr
f=D/'whitespace-disposition-r3.json';save(f,dict(schema='nbdp-whitespace-disposition-r3',actor='/root',supersededDisposition=pin(D/'whitespace-disposition.json'),actualDiagnosticCount=len(rows),exceptionPaths=sorted(exceptions),diagnostics=rows,originalCheck=dict(exit=2,stdoutBytes=len(check.stdout),stdoutSha256=hashlib.sha256(check.stdout).hexdigest(),stdoutBase64=base64.b64encode(check.stdout).decode()),allOtherStagedPathsCheckExit=0,reason='Fourth raw diagnostic artifact preserves literal whitespace itself. Four explicit exceptions cover two literal diff artifacts, their preserved raw diagnostic, and one already-frozen source line34 trailing space. No frozen evidence/source normalized.'))
core[str(f.relative_to(R))]=pin(f)
plain={d['path']:d for d in json.loads((D/'initial-preparation-refusal.json').read_text())['rawFixtureExceptions']}
for p in (E/'e06-request-phase-diagnostic-source-r4/snapshot-controls-actual-r1').rglob('*.json'):
 try:json.loads(p.read_bytes())
 except json.JSONDecodeError:plain[str(p.relative_to(R))]=pin(p)
assert len(plain)==6
def pairs(items):
 d={}
 for k,v in items:assert k not in d;d[k]=v
 return d
count=0;links=0
for rel in sorted(core):
 p=R/rel
 if rel in plain:assert pin(p)==plain[rel]
 elif p.suffix=='.json':json.loads(p.read_bytes(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));count+=1
 if p.suffix=='.md':
  for href in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   u=urllib.parse.urlsplit(href.strip('<>'))
   if u.scheme or u.netloc or not u.path:continue
   tr=str((p.parent/urllib.parse.unquote(u.path)).resolve().relative_to(R));links+=1
   assert tr in core or subprocess.run(G+['cat-file','-e','HEAD:'+tr],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,(rel,href)
audit=D/'static-validation-r3.json';save(audit,dict(schema='nbdp-publication-r3-static-audit-v1',actor='/root',structuredJsonParsedBeforeThisAudit=count,exactPlainTextRegressionOperands=list(plain.values()),activeLocalLinks=links,whitespaceDisposition=pin(f),canonicalSixUnchanged=True,scope='New read/hash/JSON/link/stage audit only; no experiment invocation.'))
core[str(audit.relative_to(R))]=pin(audit)
w=dict(v);w.update(files=[core[p] for p in sorted(core)],coreFileCount=len(core),state='FROZEN_R3_FOR_INDEPENDENT_DRAFT_PUBLICATION_REVIEW',supersededUnacceptedSubject=pin(old),preservedCurrentDocumentDelta=pin(D/'current-document-delta-r3.json'),whitespaceDisposition=pin(f),metadataDisposition=pin(metadata),validation=pin(audit),heldScopes={'e06SourceR4':'Actual13+3 accepted only; guard16 seven passes/nine mock-installation errors, admission14 not executed; real7/Node held.'},excludedActiveScopes=['Active minimum standalone consumer','Active SOURCE5/libc adapter proposal','Future Android role windows, real7/Node/LOCAL','Unrelated initial user work and SDK/APK/image/key bodies'])
w['actualAcceptedNewScopes']=dict(v['actualAcceptedNewScopes'],e06ObserverR4Pure=[13,3])
w['limits']=[x for x in v['limits'] if 'Three explicit whitespace' not in x]+['Four explicit whitespace exceptions/73diagnostics; all other staged paths check0. Unused malformed documentary NSEC LOW is explicitly dispositioned; actual source input remains correct.']
subject=D/'publication-subject-r3.json';save(subject,w)
paths=sorted(set(core)|{str(subject.relative_to(R))});Path('/tmp/nbdp-next-runtime-checkpoint-paths.txt').write_text('\n'.join(paths)+'\n')
for i in range(0,len(paths),50):subprocess.run(G+['add','--']+paths[i:i+50],check=True)
changed=subprocess.check_output(G+['diff','--cached','--name-only'],text=True).splitlines();assert set(changed)==set(paths)
for p in w['files']+[pin(subject)]:
 assert pin(R/p['path'])==p
 b=subprocess.check_output(G+['show',':'+p['path']]);assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
print(json.dumps(dict(subject=pin(subject),coreFiles=len(core),selectedIncludingSubject=len(paths),stagedChangedFiles=len(changed),jsonChecked=count,links=links,whitespaceExceptions=4,whitespaceDiagnostics=73,plainTextNegativeOperands=6,activeConsumerSource5Excluded=True)))
