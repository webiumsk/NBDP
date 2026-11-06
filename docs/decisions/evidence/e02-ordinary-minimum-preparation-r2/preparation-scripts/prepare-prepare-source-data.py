from pathlib import Path
import json, shutil, hashlib, ast, uuid
R=Path('/home/peterhorvath/apps/bitcoin/NBDP')
OLD=R/'experiments/prototypes/e02_ordinary_minimum_v1'
DIAG=R/'experiments/prototypes/e02_transport_query_diagnostic_v2'
NEW=R/'experiments/prototypes/e02_ordinary_minimum_v2'
E=R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2'
assert not NEW.exists() and not E.exists()
NEW.mkdir(); E.mkdir()
def save(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def pin(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
# Copy only owned source files into a distinct namespace; original bytes untouched.
for p in OLD.iterdir():
 if p.is_file() and p.name!='encode-public-scalar1.mjs':shutil.copyfile(p,NEW/p.name)
for n in ['exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json']:
 shutil.copyfile(DIAG/n,NEW/n)
# Fixed public-scalar NIP19 format materialization, stdlib only. No keys from users,
# package import, signing, encryption, module evaluation or runtime experiment.
alphabet='qpzry9x8gf2tvdw0s3jn54khce6mua7l'
def polymod(v):
 c=1
 for x in v:
  top=c>>25;c=((c&0x1ffffff)<<5)^x
  for i,g in enumerate([0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3]):
   if (top>>i)&1:c^=g
 return c
def encode_scalar(n):
 bits=''.join(format(x,'08b') for x in n.to_bytes(32,'big'));bits+='0'*((-len(bits))%5)
 words=[int(bits[i:i+5],2) for i in range(0,len(bits),5)]
 prefix=[ord(x)>>5 for x in 'nsec']+[0]+[ord(x)&31 for x in 'nsec']
 checksum=polymod(prefix+words+[0]*6)^1
 return 'nsec1'+''.join(alphabet[x] for x in words)+''.join(alphabet[(checksum>>(5*(5-i)))&31] for i in range(6))
values={str(n):{'scalarHex':format(n,'064x'),'nsec':encode_scalar(n)} for n in [1,2]}
# Materialization cross-check only: exact two existing actual driver operands, not
# test/module execution. Future independently reviewed decode regressions required.
driver=(OLD/'android_driver.py').read_text()
for x in values.values():assert x['nsec'] in driver and len(x['nsec'])==63
save(E/'public-scalar-format-data.json',dict(schema='e02-producer2-public-scalar-format-data-v1',operation='STDLIB_FIXED_PUBLIC_SCALAR_NIP19_FORMAT_ONLY',inputs=[1,2],values=values,implementationSources=[pin(R/'experiments/node_modules/nostr-tools/lib/esm/nip19.js'),pin(R/'experiments/node_modules/@scure/base/index.js')],crossCheck='Exact existing scalar1 format DATA and unchanged actual driver scalar1/scalar2 operands; not crypto/runtime interoperability'))
# Namespace/schema literals only in copied UI/test/source metadata. No UI method changes.
replacements=[('e02_ordinary_minimum_v1','e02_ordinary_minimum_v2'),('e02-ordinary-minimum-v1','e02-ordinary-minimum-v2'),('e02-ordinary-minimum-rs-two-role-v1','e02-ordinary-minimum-rs-two-role-v2'),('E02_ORDINARY_MINIMUM_RS_TWO_ROLE_WINDOW_ONLY','E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY')]
# Versioned DTOs, raw wire-row schema deliberately NOT renamed.
for name in ['ordinary-minimum-role-runtime-plan','ordinary-minimum-role-release','ordinary-minimum-role-supervisor-result','ordinary-minimum-fixture-plan','ordinary-minimum-ui-plan','ordinary-minimum-profile-plan','minimum-prepared','minimum-role-driver-result','minimum-transport','minimum-validated-wire-record','minimum-publish-intent','minimum-publication-window','minimum-producer-validation','minimum-stage-publication','minimum-fixture-command']:
 replacements.append(('e02-'+name+'-v1','e02-'+name+'-v2'))
for p in NEW.iterdir():
 if not p.is_file() or p.name in ['exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json']:continue
 s=p.read_text()
 for a,b in replacements:s=s.replace(a,b)
 p.write_text(s)
for n in ['minimum-plan.json','ui-plan.json','fixture-plan.json']:
 p=NEW/n;d=json.loads(p.read_bytes())
 for role,scalar in [('incoming',2),('archive',1)]:d['roles'][role]['nsec']=values[str(scalar)]['nsec']
 if n=='fixture-plan.json':
  for x in d['oracles'].values():
   x['source']=str(NEW/Path(x['source']).name)
  d['dependencyTree']={'path':'/input/dependency-tree.json',**{k:v for k,v in pin(NEW/'dependency-tree.json').items() if k!='path'}}
  d['captureScope']='ONE shared aggregate16777216-byte ceiling across capture.jsonl and phase-trace.jsonl; sticky poison, checked single writes, no retries.'
 save(p,d)
prov=json.loads((R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/oracle-provenance.json').read_bytes())
prov['schema']='e02-minimum-frozen-oracle-input-provenance-v2'
for role,scalar in [('incoming',2),('archive',1)]:prov['roles'][role]['nsec']=values[str(scalar)]['nsec']
prov['producer1FailedWindowDonation']=0
prov['formatData']=pin(E/'public-scalar-format-data.json')
save(E/'oracle-provenance.json',prov)
# Reuse host dependency closure functions byte-for-byte.
s=(NEW/'supervisor.py').read_text();d=(DIAG/'supervisor.py').read_text()
a=d.index('def dependency_relative(');b=d.index('\ndef source_pins(',a)
s=s.replace('def source_pins():',d[a:b]+'\n\ndef source_pins():',1)
s=s.replace("'minimum-plan.json', 'business-rumor.json', 'chat-rumor.json')", "'minimum-plan.json', 'business-rumor.json', 'chat-rumor.json',\n            'exchange.mjs', 'phase-writer.mjs', 'dependency-tree.mjs', 'dependency-tree.json',\n            'capture-budget.mjs', 'exchange-adapter.mjs')")
a=s.index("    dependencies = REPO / 'experiments/node_modules'",s.index('def verify_config'))
b=s.index('    # Preserve source-specific provenance.',a)
s=s[:a]+"    verify_dependency_inventory(fixture, strict((HERE / 'dependency-tree.json').read_bytes()),\n                                REPO / 'experiments/node_modules')\n"+s[b:]
# End host boundary after cleanup, before final result; error is first-failure preserving.
needle="        final_code = finalize(out, {'schema': 'e02-ordinary-minimum-role-supervisor-result-v2',"
assert needle in s
s=s.replace(needle,"        try:\n            verify_dependency_inventory(fixture, strict((HERE / 'dependency-tree.json').read_bytes()),\n                                        REPO / 'experiments/node_modules')\n        except BaseException as failure:\n            if error is None:\n                error = 'End dependency closure failed: ' + repr(failure)\n            else:\n                cleanup.setdefault('errors', []).append('End dependency closure failed: ' + repr(failure))\n        "+needle.lstrip())
(NEW/'supervisor.py').write_text(s)
save(E/'preparation-operations.json',dict(schema='e02-producer2-source-materialization-operations-v1',operations=['Distinct copied sources; old roots preserved','Fixed public scalar1/scalar2 Bech32 metadata regeneration using stdlib only','Byte-identical accepted diagnostic exchange/phase-writer/dependency-tree modules','Byte-identical three Python dependency functions inserted into new supervisor','Namespace/DTO changes, same raw proxy schema'],testsRun=0,moduleEvaluation=False,experimentsRun=0,executionGrant=False))
print(json.dumps({'new':str(NEW),'evidence':str(E),'scalar2Characters':len(values['2']['nsec'])}))
