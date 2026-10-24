from pathlib import Path
import hashlib,json,os,stat,time,re
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');S=R/'experiments/prototypes/e06_relay_https_negative_v1';A=R/'docs/decisions/evidence/invoice-authenticated-carrier/e06-https-acquisition-preparation-r1';O=R/'docs/decisions/evidence/e06-qualification-current-source-r3';PINS={'path','bytes','sha256'}
def need(v,m):
 if not v:raise RuntimeError(m)
def load(p):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate JSON');d[k]=v
  return d
 return json.loads(p.read_bytes(),object_pairs_hook=pairs)
def pin(p):
 need(p.is_absolute() and p.resolve(strict=True)==p and not p.is_symlink() and stat.S_ISREG(p.stat().st_mode),'canonical regular file')
 need(p.stat().st_size<=536870912,'bounded file')
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(d):need(type(d)is dict and set(d)==PINS and pin(Path(d['path']))==d,'pin drift '+str(d.get('path')));return Path(d['path'])
def write(p,v):
 raw=(json.dumps(v,indent=2)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return pin(p)
expected={'qualification-schemas.json':(133680,'dcbbbd2c9b84d5cd477718896f287f8abc6f6574e148a04421bc3a9043157a2b'),'admission.py':(53263,'24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'),'qualification.py':(31089,'13e9ebf74caa8c473296b009ce66be1c5f02a469f7b2e90ca4cace20a0d175aa'),'runner.py':(27072,'7ea2ce4721fdc3e5d7f3b53c289d4f017937a5e66c49ae2a6a7ad4b7e5dde655'),'controls.py':(9591,'9572676fe54f206201e29229b3b8f256a0d53f1fba8c654b7c21ff91c041e7be'),'protocol.mjs':(73552,'8ceb004085d7c86dd2a1cf7f0b8009975ad807c2172d8bd0c7b455b12a3cdceb')}
for n,(size,sha) in expected.items():d=pin(S/n);need(d['bytes']==size and d['sha256']==sha,'worker source changed '+n)
need(not O.exists(),'fresh evidence directory');O.mkdir(mode=0o700)
rows={};origins={};stages=[];schema_shapes=[]
def remember(d,origin):
 need(type(d)is dict and set(d)==PINS and type(d['path'])is str and Path(d['path']).is_absolute() and type(d['bytes'])is int and 0<=d['bytes']<=536870912 and type(d['sha256'])is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'closed actual file descriptor')
 if d['path'] in rows:need(rows[d['path']]==d,'conflicting live descriptor '+d['path'])
 rows[d['path']]=d;origins.setdefault(d['path'],[]).append(origin)
def addgroup(values,name):
 for d in values:remember(d,name)
 stages.append({'group':name,'totalUnique':len(rows)})
prot=load(S/'protected-deltas.json');baseline=load(checked(prot['baselineClosure']));need(len(baseline)==378,'protected baseline378');addgroup(baseline,'protected378')
inert=load(A/'composition-negative-freeze-r2/source-data-closure.json');need(len(inert)==12,'inert12');addgroup(inert,'inert12')
names=['protocol.mjs','case.mjs','wire.mjs','metadata_loader.mjs','wire_controls.mjs','qualification.py','admission.py','runner.py','checker.py','controls.py','IMPLEMENTATION.md','qualification-schemas.json','test_policy_marker.mjs'];addgroup([pin(S/n) for n in names],'current executable12 and marker test')
plan=A/'composition-negative-native-qualification-plan-r2';mat=A/'composition-negative-native-inputs-r2';inventory=load(plan/'inputs.json');need(len(inventory)==57,'57 roles');addgroup(list(inventory.values()),'current57role inventory')
addgroup([pin(plan/n) for n in ['PLAN.md','inputs.json','plan-data-closure.json','static-checks.json','independent-qa-review.json','independent-security-review.json','acceptance.json']],'explicit current plan7')
addgroup([pin(mat/n) for n in ['request.jsonl','JS.expected.json','RUST.expected.json','derivation.json','static-checks.json','independent-qa-review.json','independent-security-review.json','acceptance.json']],'explicit current materialization8')
def walk(v,origin,pointer=''):
 if type(v)is dict:
  if set(v)==PINS:
   if type(v['path'])is str and Path(v['path']).is_absolute():remember(v,origin)
   else:schema_shapes.append({'origin':origin,'pointer':pointer,'schemaShape':v})
  else:
   for key,child in v.items():walk(child,origin,pointer+'/'+key.replace('~','~0').replace('/','~1'))
 elif type(v)is list:
  for i,child in enumerate(v):walk(child,origin,pointer+'/'+str(i))
for d in inert:
 if d['path'].endswith('.json'):walk(load(checked(d)),'direct descriptor in inert JSON '+d['path'])
walk(load(S/'qualification-schemas.json'),'direct descriptor in current qualification schema');stages.append({'group':'direct descriptors in inert and current schema only','totalUnique':len(rows)})
need(len(rows)==449,'expected independently derived449 path set')
for d in rows.values():checked(d)
for rel,d in prot['wholeSourcePins'].items():need(pin(R/rel)==dict(path=str(R/rel),**d),'whole source invariant '+rel)
for interval in prot['protectedIntervals']:
 raw=(R/interval['source']).read_bytes()[interval['startByte']:interval['endByteExclusive']];need(len(raw)==interval['bytes'] and hashlib.sha256(raw).hexdigest()==interval['sha256'],'protected interval')
old=load(A/'composition-negative-implementation-r2/source-closure.json');oldmap={d['path']:d for d in old};result=[rows[k] for k in sorted(rows)];closure=write(O/'source-closure.json',result)
manifest={'schema':'e06-current-source-root-manifest-v1','actor':'/root','executionReleased':False,'sourceClosure':closure,'stages':stages,'memberOrigins':origins,'nonFileSchemaShapes':schema_shapes,'historicalExpansionBoundary':'Historical reports/acceptances/static data are opaque whole-file pins; only inert JSON and current qualification-schema descriptor objects are traversed. No recursive history authority refresh.','deltaFromHistorical443':{'removed':[oldmap[k] for k in sorted(set(oldmap)-set(rows))],'added':[rows[k] for k in sorted(set(rows)-set(oldmap))],'changed':[{'before':oldmap[k],'after':rows[k]} for k in sorted(set(rows)&set(oldmap)) if rows[k]!=oldmap[k]]},'protected':{'baselineMembers':378,'inertMembers':12,'wholeSourcePins':len(prot['wholeSourcePins']),'intervals':len(prot['protectedIntervals']),'allMatch':True},'sourceFreezer':pin(Path(__file__)),'limits':['DATA-only current hash freeze, no project imports/source evaluation/tests/native/relay/crypto execution.','No SOURCE/CONTROL/LOCAL/TARGET release; independent complete-source review remains required.','Old source/runtime acceptance is historical and does not transfer.']};m=write(O/'root-manifest.json',manifest);print(json.dumps({'closure':closure,'manifest':m,'count':len(rows),'stages':stages,'deltaCounts':{k:len(v) for k,v in manifest['deltaFromHistorical443'].items()}}))
