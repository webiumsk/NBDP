from pathlib import Path
import hashlib, json, os, re, subprocess, urllib.parse, datetime

R=Path('/home/peterhorvath/apps/bitcoin/NBDP')
E=R/'docs/decisions/evidence'
D=E/'transport-runtime-current-state-r3'
G=['git','--git-dir=/tmp/nbdp-publish-repo/.git','--work-tree='+str(R)]
PARENT='62b13d889b9149f779d9f258e1a038203f64da93'
def pin(p):
    b=p.read_bytes()
    return {'path':str(p.relative_to(R)), 'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,v):
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f: json.dump(v,f,indent=2); f.write('\n')
def pairs(rows):
    d={}
    for k,v in rows:
        assert k not in d,('Duplicate JSON key',k)
        d[k]=v
    return d
assert subprocess.check_output(G+['rev-parse','HEAD'],text=True).strip()==PARENT
assert not subprocess.check_output(G+['diff','--cached','--name-only'],text=True).strip()
assert D.is_dir() and {p.name for p in D.iterdir()}=={'initial-rejected-publication-preparation.py','initial-preparation-refusal.json'}
(D/'publication-preparation.py').write_bytes(Path(__file__).read_bytes())
(D/'publication-preparation.py').chmod(0o600)
S=set(['docs/PROJECT_STATE.md','docs/ROADMAP.md','docs/research/experimental-validation-summary.md','docs/research/transport-gate-readiness-2026-10-23.md','docs/research/amethyst-control-runbook.md'])
S.update(json.loads((E/'transport-runtime-progress-publication-r4/normal-core-suggestion.json').read_text())['files'])
roots=['transport-runtime-progress-publication-r4','e06-request-phase-diagnostic-source-r1','e06-request-phase-diagnostic-source-r2','e06-request-phase-diagnostic-source-r3','e06-request-phase-diagnostic-source-r4','e06-strace-containment-controls-r1','e06-strace-containment-controls-r2','e06-strace-containment-controls-r3','e06-local-fonly-primary-preparation-r3','e06-local-fonly-primary-execution-r3','e02-ordinary-minimum-preparation-r1']
for name in roots:
    for p in (E/name).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.relative_to(R).parts:
            S.add(str(p.relative_to(R)))
for p in (R/'experiments/prototypes/e02_ordinary_minimum_v1').rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts: S.add(str(p.relative_to(R)))
S.update(str((D/name).relative_to(R)) for name in ['publication-preparation.py','initial-rejected-publication-preparation.py','initial-preparation-refusal.json'])
canonical=[]; allpins={}; entries=0
for p in sorted((R/'experiments/results').glob('E0[1-6].json')):
    assert subprocess.check_output(G+['show','HEAD:'+str(p.relative_to(R))])==p.read_bytes()
    x=json.loads(p.read_bytes(),object_pairs_hook=pairs)
    canonical.append({'record':pin(p),'status':x['status'],'actualHistoricalChecks':len(x['tests'])})
    for rel,h in x['source_sha256'].items():
        entries+=1
        assert rel not in allpins or allpins[rel]==h
        allpins[rel]=h
for rel,h in allpins.items(): assert hashlib.sha256((R/'experiments'/rel).read_bytes()).hexdigest()==h
assert entries==116 and len(allpins)==26
jsoncount=0; hrefs=[]
raw_exceptions={d['path']:d for d in json.loads((D/'initial-preparation-refusal.json').read_text())['rawFixtureExceptions']}
for rel in sorted(S):
    p=R/rel
    assert p.is_file() and not p.is_symlink(),rel
    if rel in raw_exceptions:
        assert pin(p)==raw_exceptions[rel],rel
    elif p.suffix=='.json':
        json.loads(p.read_bytes(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
        jsoncount+=1
    if p.suffix=='.md':
        for href in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            u=urllib.parse.urlsplit(href.strip('<>'))
            if u.scheme or u.netloc or not u.path:continue
            target=(p.parent/urllib.parse.unquote(u.path)).resolve()
            assert target.is_relative_to(R),(rel,href)
            tr=str(target.relative_to(R))
            if tr not in S:
                assert subprocess.run(G+['cat-file','-e','HEAD:'+tr],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,(rel,href)
            hrefs.append({'from':rel,'target':tr})
validation={'schema':'nbdp-checkpoint-static-validation-v1','actor':'/root','parent':PARENT,'performedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonicalRecords':canonical,'canonicalProvenanceEntries':entries,'uniqueCanonicalSourceFiles':26,'allCanonicalBytesMatchParent':True,'jsonFilesParsedBeforeValidationMetadata':jsoncount,'duplicateJsonKeysRejected':True,'exactPinnedPlainTextRegressionOperands':list(raw_exceptions.values()),'localLinks':hrefs,'linkCount':len(hrefs),'experimentEntrypointsInvoked':0,'scope':'Read/hash/JSON/link verification only; not new experiment, runtime or independent review.'}
save(D/'static-validation.json',validation)
S.add(str((D/'static-validation.json').relative_to(R)))
subject={'schema':'nbdp-runtime-checkpoint-publication-subject-v1','actor':'/root','state':'FROZEN_FOR_INDEPENDENT_DRAFT_PUBLICATION_REVIEW','parent':PARENT,'files':[pin(R/p) for p in sorted(S)],'coreFileCount':len(S),'canonicalResultsChanged':False,'actualAcceptedNewScopes':{'e02MinimumMocksMetadata':[29,49,21,27,43],'e06ObserverR2Pure':[13,3],'p4PackageCopies':1894},'heldScopes':{'e06SourceR3':'HIGH unvalidated pidfd custody and MEDIUM persistent census cleanup; no execution','e06SourceR4':'Independent SOURCE acceptance only; actual46 controls/live7/Node excluded from this checkpoint'},'excludedActiveScopes':['e02_ordinary_minimum_consumer_v1 and its preparation','Future SOURCE4 controls/strace/Node and later ordinary role windows','Unrelated initial user work and SDK/APK/image/key inputs'],'limits':['No ordinary-client runtime qualification or canonical PASS promotion.','Known source HOLD history preserved; publishing a source snapshot does not authorize activation.','Original six results and all116 provenance entries unchanged.','Archives are indexed evidence copies, not distinct tests or a portable replay image.','Source-backed navigation remains runtime-unvalidated; no automatic merge/SDK/production/blocker closure.'],'validation':pin(D/'static-validation.json')}
save(D/'publication-subject.json',subject)
paths=sorted(S|{str((D/'publication-subject.json').relative_to(R))})
Path('/tmp/nbdp-next-runtime-checkpoint-paths.txt').write_text('\n'.join(paths)+'\n')
for i in range(0,len(paths),50): subprocess.run(G+['add','--']+paths[i:i+50],check=True)
subprocess.run(G+['diff','--cached','--check'],check=True)
changed=subprocess.check_output(G+['diff','--cached','--name-only'],text=True).splitlines()
assert set(changed)<=set(paths)
for p in subject['files']+[pin(D/'publication-subject.json')]:
    b=subprocess.check_output(G+['show',':'+p['path']])
    assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
print(json.dumps({'subject':pin(D/'publication-subject.json'),'coreFiles':len(S),'selectedIncludingSubject':len(paths),'stagedChangedFiles':len(changed),'alreadyTrackedUnchanged':len(paths)-len(changed),'jsonChecked':jsoncount,'links':len(hrefs),'canonicalEntries':entries,'uniqueCanonicalSourceFiles':len(allpins)}))
