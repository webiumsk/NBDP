// DATA contracts only. No primary/consumer/module/service execution on import.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
export const ROOT='/home/peterhorvath/apps/bitcoin/NBDP', EXP=ROOT+'/experiments';
export const PROFILE='E02_EXTERNAL_COMPLETION_V2';
export const ORDINARY_SHA=null; // Actual final producer3 source required.
export const CONSUMER_SHA=null; // Actual final consumer5 source required.
export const ADOPTION_SHA='2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287';
export const SKIP={scope:'Amethyst ordinary-client rendering',reason:'No isolated Android runtime/client installation; adapter ordinary-chat dispatch was exercised. Canonical ordinary-client rendering control was NOT EXECUTED; no ecosystem UI result claimed.',mandatory:true};
export const RELAYS=['ws://127.0.0.1:17777','ws://127.0.0.1:18081'];
export const EXPECTED=[...['79be667e','c6047f94'].flatMap(p=>RELAYS.map(u=>'inbox-publication/'+p+'/'+u)),...['js-to-rust','rust-to-js'].flatMap(d=>['incoming','archive'].flatMap(r=>RELAYS.map(u=>d+'/'+r+'/'+u))),...['ordinary-chat','foreign-protocol','unsupported-version','mandatory-extension','malformed-discriminator'].map(s=>'dispatch/'+s),...['file-stub-first','envelope-stub-first','both-file-first','both-envelope-first','repeated-stubs'].map(s=>'stub-reordering/'+s)];
export function need(v,m){assert.ok(v,m);}
export function closed(v,keys){need(v&&typeof v==='object'&&!Array.isArray(v),'object');assert.deepEqual(Object.keys(v).sort(),keys.split(' ').sort());return v;}
export function eq(a,b){assert.deepEqual(a,b);}
export function regular(p){need(typeof p==='string'&&path.isAbsolute(p)&&path.resolve(p)===p,'canonical absolute path');for(let q=p;;q=path.dirname(q)){need(!fs.lstatSync(q).isSymbolicLink(),'symlink component');if(q==='/')break;}need(fs.statSync(p).isFile(),'regular file');return p;}
export function pin(p){regular(p);const b=fs.readFileSync(p);need(b.length<=268435456,'file bound');return {path:p,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')};}
export function checked(d){closed(d,'path bytes sha256');need(Number.isSafeInteger(d.bytes)&&d.bytes>=0&&/^[0-9a-f]{64}$/.test(d.sha256),'pin domain');eq(pin(d.path),d);return fs.readFileSync(d.path);}
export function json(raw){
 // Duplicate-key/depth scanner derived from unchanged transport.strictJSON;
 // DATA accepts finite fractional duration_ms, unlike integer-only wire JSON.
 need(Buffer.isBuffer(raw)&&raw.length<=16777216,'JSON byte bound');const s=new TextDecoder('utf-8',{fatal:true}).decode(raw),stack=[];
 for(let i=0;i<s.length;i++){const c=s[i];if(c==='"'){const a=i++;while(i<s.length){if(s[i]==='\\'){i+=2;continue;}if(s[i]==='"')break;i++;}let j=i+1;while(/\s/.test(s[j]??'X'))j++;if(s[j]===':'){const f=stack.at(-1);need(f?.type==='{','JSON object key');const key=JSON.parse(s.slice(a,i+1));need(!f.keys.has(key),'duplicate JSON key');f.keys.add(key);}}else if(c==='{'||c==='['){stack.push({type:c,keys:new Set()});need(stack.length<=64,'JSON depth');}else if(c==='}'||c===']'){const f=stack.pop();need(f?.type===(c==='}'?'{':'['),'JSON nesting');}}
 need(stack.length===0,'closed JSON');const v=JSON.parse(s);const todo=[v];let n=0;while(todo.length){const a=todo.pop();need(++n<=250000,'JSON node bound');if(typeof a==='number')need(Number.isFinite(a)&&!Object.is(a,-0),'finite JSON number');if(a&&typeof a==='object')todo.push(...Object.values(a));}return v;
}
export const doc=d=>json(checked(d));
export function primaryShape(r){
 closed(r,'experiment status tests observations skipped');eq(r.experiment,'E02');eq(r.status,'PARTIAL');need(Array.isArray(r.tests)&&r.tests.length===22,'all22 primary checks');eq(r.tests.map(t=>t.name),EXPECTED);need(r.tests.every(t=>t.ok===true&&Number.isFinite(t.duration_ms)&&t.duration_ms>=0&&!Object.hasOwn(t,'error')),'primary failure');eq(r.skipped,[SKIP]);need(Array.isArray(r.observations)&&r.observations.length===1,'original observation');eq(r.observations[0],{kind14:'UTF-8 JSON survives transport without changing NIP17 plain-text content',ordinary_clients:'NBDP interpretation/renderer compatibility not established',authority:'synthetic pinned peer enrollment only; organizational authority not resolved',relays:RELAYS});return r;
}
export function wireFixtures(raw,primary){
 primaryShape(primary);need(Array.isArray(raw)&&raw.length===4,'four original peer/self wire fixtures');const A='79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798',B='c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5';
 for(let i=0;i<4;i++){const row=closed(raw[i],'direction role event rumor'),direction=i<2?'js-to-rust':'rust-to-js',role=i%2?'archive':'incoming',from=i<2?A:B,to=i<2?B:A,local=role==='archive'?from:to;eq(row.direction,direction);eq(row.role,role);eq(row.rumor.pubkey,from);eq(row.rumor.tags,[['p',to]]);eq(row.event.kind,1059);eq(row.event.tags,[['p',local]]);need(/^[0-9a-f]{64}$/.test(row.rumor.id)&&/^[0-9a-f]{64}$/.test(row.event.id),'real wire identifiers');if(role==='archive')eq(row.rumor,raw[i-1].rumor);
 for(const url of RELAYS){const t=primary.tests.find(t=>t.name===direction+'/'+role+'/'+url);eq(t.data,{envelope_id:(i<2?10:11).toString(16).padStart(64,'0'),rumor_id:row.rumor.id,frame_bytes:Buffer.byteLength(JSON.stringify(['EVENT',row.event])),outer_p:local});}}
 return raw;
}
export function ordinaryShape(r){
 closed(r,'schema state profileId wholeWindows selectedExports selectedNoteContexts uniqueRumorIds canonicalE02Changed canonicalE02 primaryMatrixQualified businessEffectsMeasured sdkRuntimeAdmission portableProcessAttestation nonoperativeMetadataFinding perCommandClockChronology evidenceFiles evidenceBytes');eq(r.schema,'e02-minimum-consumption-result-v2');eq(r.state,'SUPPLEMENTAL_DATA_CONSISTENT_WITH_EXTERNALLY_AUTHENTICATED_ORIGINS');eq(r.profileId,'e02-ordinary-minimum-rs-two-role-v2');eq([r.wholeWindows,r.selectedExports,r.selectedNoteContexts,r.uniqueRumorIds],[2,5,3,2]);for(const k of ['canonicalE02Changed','primaryMatrixQualified','businessEffectsMeasured','sdkRuntimeAdmission','portableProcessAttestation'])eq(r[k],false);eq(r.canonicalE02,'PARTIAL22_UNCHANGED');eq(r.nonoperativeMetadataFinding,'PRODUCER2_PUBLIC_SCALAR_METADATA_CORRECTED_OLD_FINDING_PRESERVED');eq(r.perCommandClockChronology,'UNKNOWN_NOT_RECORDED');need(Number.isSafeInteger(r.evidenceFiles)&&r.evidenceFiles>0&&Number.isSafeInteger(r.evidenceBytes)&&r.evidenceBytes>0,'real read inventory');return r;
}
export function criteria(primary,ordinary){primaryShape(primary);ordinaryShape(ordinary);return {primaryChecks:22,resolvedScope:SKIP.scope,rawPrimaryStatus:'PARTIAL',rawMandatorySkipRetained:true,ordinaryWindows:2,actualClientExports:5,selectedNoteContexts:3,uniqueRumorIds:2,canonicalCriteria:['signed-inboxes-both-identities-both-relays','independent-js-rust-both-directions-peer-self','same-envelope-schema-dispatch','unknown-features-chat-no-incoming-archive-effect','stub-order-replay-zero-effects','ordinary-selected-render-content-private-tag-retention-and-self-replay'],state:'READY_FOR_INDEPENDENT_COMPLETION_REVIEW'};}
export function reviews(envelope,subject,forbidden){
 closed(envelope,'schema subject reviews provenanceLimit');eq(envelope.schema,'e02-completion-review-origin-v2');eq(envelope.subject,subject);eq(envelope.provenanceLimit,'EXTERNALLY_AUTHENTICATED_REAL_AGENT_SESSIONS_NOT_PORTABLE_ATTESTATION');need(Array.isArray(envelope.reviews)&&envelope.reviews.length===2,'two actual reviews');const actors=[];
 for(const role of ['qa','security']){const rows=envelope.reviews.filter(r=>r.role===role);eq(rows.length,1);const r=closed(rows[0],'role actor session subject decision findings report rawSessionEvidence');eq(r.subject,subject);eq(r.actor,r.session);need(typeof r.actor==='string'&&r.actor.startsWith('/root/')&&!forbidden.includes(r.actor),'independent nonauthor/operator');eq(r.decision,'ACCEPT_EXACT_COMPLETION_EVIDENCE');eq(r.findings,[]);need(checked(r.report).length>0&&checked(r.rawSessionEvidence).length>0,'actual raw review/session evidence');actors.push(r.actor);}
 need(new Set(actors).size===2,'independent sessions');need(envelope.reviews[0].report.sha256!==envelope.reviews[1].report.sha256&&envelope.reviews[0].rawSessionEvidence.sha256!==envelope.reviews[1].rawSessionEvidence.sha256,'distinct raw origins');return envelope;
}

// Exact historical E01/native equality is never weakened by a profile repin.
export function nativePrerequisite(e01,binary){
 eq(e01.environment.rust_binary_sha256,binary.sha256);
 need(/^[0-9a-f]{64}$/.test(binary.sha256),'exact native prerequisite SHA');
 return binary;
}
