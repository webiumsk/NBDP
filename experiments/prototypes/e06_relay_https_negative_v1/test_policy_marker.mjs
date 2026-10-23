// Prepared SOURCE/local-file controls only. No TARGET, LOCAL, relay or native run.
// Tests use the actual private prerequisite prelude and marker clause, extracted
// without a production test export. Unrelated historical prerequisite tails and
// full source-closure/release validation are deliberately outside this test.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {checked, closed, descriptor, equal, need} from './protocol.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const source=fs.readFileSync(path.join(here,'protocol.mjs'),'utf8');
const schemas=JSON.parse(fs.readFileSync(path.join(here,'qualification-schemas.json')));
const policy=schemas.fixedSourcePrerequisites.candidateE02Policy;
const adopted=checked(policy);
const start='function fixedPrerequisites(x){\n';
const begin=source.indexOf(start);
const end=source.indexOf(' const pv=historical(',begin);
assert.ok(begin>=0&&end>begin,'Exact production prerequisite prelude required');
const prelude=source.slice(begin+start.length,end);
const clause=source.match(/^ const candidatePolicyText=checked\(fixed\.candidateE02Policy\)\.toString\(\);\n need\(candidatePolicyText\.includes\('ADOPTED_TECHNICAL_POLICY'\)&&candidatePolicyText\.includes\('transport-sub-evidence-v1'\),'ADOPTED_CANDIDATE_E02_POLICY'\);$/m);
assert.ok(clause,'Exact production policy clause required');
const member=source.match(/^function requireMember\(map,d\)\{[^\n]+\}$/m);
const opaque=source.match(/^function opaque\(d\)\{[^\n]+\}$/m);
assert.ok(member&&opaque,'Actual membership and pin checks required');
const check=new vm.Script(member[0]+'\n'+opaque[0]+'\n(function(x){\n'+prelude+clause[0]+'\n})',
  {filename:'actual-policy-prerequisite-slice'}).runInNewContext({
    checked,closed,descriptor,equal,need,rememberVerifiedEvidence(){},
  });

function context(pin=policy){return {
  qschemas:{fixedSourcePrerequisites:{candidateE02Policy:pin}},
  manifest:{prerequisites:{candidateE02Policy:pin}},
  map:new Map([[pin.path,pin]]),
};}
function refused(fn,code){assert.throws(fn,error=>error.code===code);}
function temporary(raw,action){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'e06-policy-marker-'));
  const file=path.join(dir,'policy.txt');
  try{fs.writeFileSync(file,raw,{mode:0o600});action(descriptor(file),file);}
  finally{fs.rmSync(dir,{recursive:true,force:true});}
}

test('exact pinned adopted policy passes its source prerequisite slice',()=>{
  assert.equal(policy.bytes,3073);
  assert.equal(policy.sha256,'0ed885e41d3cbb2d38af33cdd060e5ad5bea3327d0ce2a4306c123c170a15a25');
  assert.equal(adopted.includes(Buffer.from('ADOPTED_TECHNICAL_POLICY=transport-sub-evidence-v1')),false);
  check(context());
});

// Rebound temporary pins isolate marker refusal only. They do NOT model a
// permitted replacement for the immutable production qualification-schema pin.
for(const [label,raw] of [
  ['missing adoption marker','transport-sub-evidence-v1'],
  ['wrong adoption marker','PROPOSED_TECHNICAL_POLICY transport-sub-evidence-v1'],
  ['missing policy name','ADOPTED_TECHNICAL_POLICY'],
  ['wrong policy version','ADOPTED_TECHNICAL_POLICY transport-sub-evidence-v2'],
])test(label+' refuses',()=>temporary(raw,pin=>{
  refused(()=>check(context(pin)),'ADOPTED_CANDIDATE_E02_POLICY');
}));

test('missing closure reference refuses before policy acceptance',()=>{
  const x=context();x.map.clear();
  refused(()=>check(x),'MISSING_OR_DRIFTED_MEMBER');
});

test('drifted closure pin refuses',()=>{
  const x=context();x.map.set(policy.path,{...policy,sha256:'0'.repeat(64)});
  refused(()=>check(x),'MISSING_OR_DRIFTED_MEMBER');
});

test('wrong content hash refuses even with internally matching descriptor references',()=>{
  const pin={...policy,sha256:'0'.repeat(64)};
  refused(()=>check(context(pin)),'EVIDENCE_SOURCE_OR_INPUT_DRIFT');
});

test('swapped manifest prerequisite refuses',()=>{
  const x=context();x.manifest.prerequisites.candidateE02Policy={...policy,sha256:'0'.repeat(64)};
  refused(()=>check(x),'EXACT_N_PREREQUISITE');
});

test('file bytes changed after pinning refuse',()=>temporary(adopted,(pin,file)=>{
  fs.appendFileSync(file,'\nchanged');
  refused(()=>check(context(pin)),'EVIDENCE_SOURCE_OR_INPUT_DRIFT');
}));
