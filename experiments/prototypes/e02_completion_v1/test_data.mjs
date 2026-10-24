// PREPARED synthetic DATA controls. Never execute runner, consumer, crypto or relay.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {SKIP,RELAYS,EXPECTED,primaryShape,ordinaryShape,wireFixtures,criteria,reviews,json,pin} from './data.mjs';
const cases=[];const check=(name,f)=>{f();cases.push(name);};const clone=v=>structuredClone(v);
const raw={experiment:'E02',status:'PARTIAL',tests:EXPECTED.map(name=>({name,ok:true,duration_ms:0.25})),observations:[{kind14:'UTF-8 JSON survives transport without changing NIP17 plain-text content',ordinary_clients:'NBDP interpretation/renderer compatibility not established',authority:'synthetic pinned peer enrollment only; organizational authority not resolved',relays:RELAYS}],skipped:[clone(SKIP)]};
const ordinary={schema:'e02-minimum-consumption-result-v1',state:'SUPPLEMENTAL_DATA_CONSISTENT_WITH_EXTERNALLY_AUTHENTICATED_ORIGINS',profileId:'e02-ordinary-minimum-rs-two-role-v1',wholeWindows:2,selectedExports:5,selectedNoteContexts:3,uniqueRumorIds:2,canonicalE02Changed:false,canonicalE02:'PARTIAL22_UNCHANGED',primaryMatrixQualified:false,businessEffectsMeasured:false,sdkRuntimeAdmission:false,portableProcessAttestation:false,nonoperativeMetadataFinding:'KNOWN_UNUSED_INCOMING_PLAN_NSEC_65_CHARS_NOT_NORMALIZED_NOT_RUNTIME_INPUT',perCommandClockChronology:'UNKNOWN_NOT_RECORDED',evidenceFiles:1,evidenceBytes:1};
check('exact-original22-partial-skip-observation',()=>primaryShape(raw));
for(const [name,edit] of [
 ['missing-check',r=>r.tests.pop()],['duplicate-check',r=>r.tests[0]=clone(r.tests[1])],['wrong-order',r=>r.tests.reverse()],['failure',r=>r.tests[0].ok=false],['typed-ok',r=>r.tests[0].ok='true'],['hidden-error',r=>r.tests[0].error='retained failure'],['nonfinite-duration',r=>r.tests[0].duration_ms=Infinity],['missing-skip',r=>r.skipped=[]],['skip-demoted',r=>r.skipped[0].mandatory=false],['unknown-skip',r=>r.skipped.push({scope:'other',reason:'x',mandatory:true})],['unknown-scope',r=>r.skipped[0].scope='other'],['changed-literal-reason',r=>r.skipped[0].reason='now resolved'],['raw-pass-mutation',r=>r.status='PASS'],['missing-observation',r=>r.observations=[]],['rewritten-ordinary-claim',r=>r.observations[0].ordinary_clients='PASS'],['public-relay',r=>r.observations[0].relays=['wss://example.invalid']],['different-experiment',r=>r.experiment='E01']]){
 check('refuse-primary-'+name,()=>{const r=clone(raw);edit(r);assert.throws(()=>primaryShape(r));});
}
check('exact-consumer-summary-is-still-supplemental',()=>ordinaryShape(ordinary));
for(const [key,value] of [['state','REFUSED_NO_CONTRIBUTION'],['wholeWindows',1],['selectedExports',4],['selectedNoteContexts',5],['uniqueRumorIds',3],['canonicalE02Changed',true],['primaryMatrixQualified',true],['businessEffectsMeasured',true],['sdkRuntimeAdmission',true],['portableProcessAttestation',true],['perCommandClockChronology','MEASURED'],['evidenceFiles',0]]){
 check('refuse-ordinary-'+key,()=>assert.throws(()=>ordinaryShape({...ordinary,[key]:value})));
}
check('extra-result-approval-key-refuses',()=>assert.throws(()=>ordinaryShape({...ordinary,approved:true})));
check('criterion-map-does-not-mutate-skipped-primary',()=>{const before=JSON.stringify(raw);const c=criteria(raw,ordinary);assert.equal(c.state,'READY_FOR_INDEPENDENT_COMPLETION_REVIEW');assert.equal(c.resolvedScope,SKIP.scope);assert.equal(JSON.stringify(raw),before);assert.equal(raw.status,'PARTIAL');assert.equal(raw.skipped[0].mandatory,true);});
const A='79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798',B='c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5';
const wires=Array.from({length:4},(_,i)=>{const from=i<2?A:B,to=i<2?B:A,role=i%2?'archive':'incoming',rumor={id:(i<2?'a':'b').repeat(64),pubkey:from,kind:14,created_at:1,tags:[['p',to]],content:'SYNTHETIC_DATA_NOT_CRYPTO_VALIDATED'};return {direction:i<2?'js-to-rust':'rust-to-js',role,rumor,event:{id:String(i+1).padStart(64,'0'),kind:1059,tags:[['p',role==='archive'?from:to]],content:'SYNTHETIC_CIPHERTEXT_NOT_ENCRYPTED'}};});
const report=clone(raw);for(const row of wires)for(const url of RELAYS)report.tests.find(t=>t.name===row.direction+'/'+row.role+'/'+url).data={envelope_id:(row.direction==='js-to-rust'?10:11).toString(16).padStart(64,'0'),rumor_id:row.rumor.id,frame_bytes:Buffer.byteLength(JSON.stringify(['EVENT',row.event])),outer_p:row.event.tags[0][1]};
check('four-direction-role-fixture-report-join',()=>wireFixtures(wires,report));
for(const [name,edit] of [['missing-role',w=>w.pop()],['wrong-direction',w=>w[0].direction='rust-to-js'],['wrong-inner-recipient',w=>w[1].rumor.tags=[['p',A]]],['wrong-self-outer',w=>w[1].event.tags=[['p',B]]],['different-self-rumor',w=>w[1].rumor.content='changed'],['report-frame-byte-drift',(_w,r)=>r.tests[4].data.frame_bytes++]]){
 check('refuse-fixture-'+name,()=>{const w=clone(wires),r=clone(report);edit(w,r);assert.throws(()=>wireFixtures(w,r));});
}
check('DATA-parser-allows-real-fractional-duration',()=>assert.deepEqual(json(Buffer.from('{"duration_ms":0.25}')),{duration_ms:0.25}));
for(const [name,text] of [['duplicate-key','{"x":1,"x":2}'],['escaped-duplicate','{"x":1,"\\u0078":2}'],['nonfinite','{"x":1e999}'],['negative-zero','{"x":-0}'],['deep','['.repeat(65)+'0'+']'.repeat(65)]])check('refuse-json-'+name,()=>assert.throws(()=>json(Buffer.from(text))));
// Fake review DATA below tests refusal mechanics only; never actual agent acceptance.
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'nbdp-completion-data-'));
try{
 const file=(n,raw)=>{const p=path.join(temp,n);fs.writeFileSync(p,raw,{mode:0o600});return pin(p);};
 const subject=file('subject','SYNTHETIC_REVIEW_SUBJECT');const envelope={schema:'e02-completion-review-origin-v1',subject,reviews:['qa','security'].map(role=>({role,actor:'/root/synthetic-'+role,session:'/root/synthetic-'+role,subject,decision:'ACCEPT_EXACT_COMPLETION_EVIDENCE',findings:[],report:file(role+'-report','SYNTHETIC_'+role),rawSessionEvidence:file(role+'-session','NOT_REAL_SESSION_'+role)})),provenanceLimit:'EXTERNALLY_AUTHENTICATED_REAL_AGENT_SESSIONS_NOT_PORTABLE_ATTESTATION'};
 check('synthetic-review-shape-is-not-origin-authentication',()=>reviews(envelope,subject,['/root/operator']));
 for(const [name,edit] of [['missing-security',r=>r.reviews.pop()],['operator-as-reviewer',r=>{r.reviews[0].actor=r.reviews[0].session='/root/operator';}],['same-session',r=>{r.reviews[1].actor=r.reviews[1].session=r.reviews[0].actor;}],['unresolved-finding',r=>r.reviews[0].findings=[{severity:'LOW'}]],['wrong-subject',r=>r.subject={...subject,sha256:'0'.repeat(64)}],['ad-hoc-boolean',r=>r.approved=true],['wrong-decision',r=>r.reviews[0].decision='APPROVED']]){
  check('refuse-review-'+name,()=>{const r=clone(envelope);edit(r);assert.throws(()=>reviews(r,subject,['/root/operator']));});
 }
}finally{fs.rmSync(temp,{recursive:true});}
console.log(JSON.stringify({scope:'E02_COMPLETION_SYNTHETIC_DATA_ONLY',checks:cases.length,cases,primaryExecuted:false,consumerExecuted:false,cryptoExecuted:false,completionPassClaimed:false}));
