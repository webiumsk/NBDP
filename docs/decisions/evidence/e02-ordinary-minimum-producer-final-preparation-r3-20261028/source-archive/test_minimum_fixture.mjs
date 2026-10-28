// Prepared pure metadata controls only. No wrap/sign/encrypt/native/network call.
import assert from 'node:assert/strict';
import {roleSpec,stageSpec,exactInnerShape,replayBinding,attemptLineageMatches,stageDeliveryAllowed} from './fixture.mjs';
const A='79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798';
const B='c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5';
const cases=[];
function check(name,run){run();cases.push(name);}
check('incoming-account-is-B-peer-is-A',()=>assert.deepEqual([roleSpec('incoming').account,roleSpec('incoming').peer,roleSpec('incoming').scalar],[B,A,2]));
check('archive-account-is-A-original-peer-is-B',()=>assert.deepEqual([roleSpec('archive').account,roleSpec('archive').peer,roleSpec('archive').scalar],[A,B,1]));
for(const role of ['unknown','',null,2])check('refuse-unknown-role-'+String(role),()=>assert.throws(()=>roleSpec(role),/CLOSED_ROLE/));
for(const [role,index] of [['incoming',2],['archive',3],['archive',-1],['incoming',0.5],['incoming','0']])check('refuse-outside-stage-'+role+'-'+index,()=>assert.throws(()=>stageSpec(role,index),/CLOSED_STAGE_INDEX/));
for(const [role,index,id,dispatch,normalized] of [
 ['incoming',0,'incoming-business',true,'incoming'],['incoming',1,'incoming-ordinary-chat',false,'chat'],
 ['archive',0,'archive-business',false,'archive'],['archive',1,'archive-identical-replay',false,'archive'],
 ['archive',2,'archive-fresh-wrap-replay',false,'archive']]){
 check('closed-stage-'+id,()=>assert.deepEqual([stageSpec(role,index).id,stageSpec(role,index).dispatch,stageSpec(role,index).normalizedRole],[id,dispatch,normalized]));
}
const rumor={id:'a'.repeat(64),pubkey:A,created_at:1,kind:14,tags:[['p',B]],content:'SYNTHETIC_METADATA_ONLY'};
check('six-field-original-pB-shape',()=>assert.equal(exactInnerShape(rumor),true));
for(const [label,patch] of [['rewritten-inner-pA',{tags:[['p',A]]}],['wrong-author',{pubkey:B}],['extra-sig',{sig:''}],
 ['fractional-timestamp',{created_at:1.5}],['string-kind',{kind:'14'}],['reordered-private-tag',{tags:[['x','other'],['p',B]]}]]){
 check('refuse-inner-'+label,()=>assert.equal(exactInnerShape({...rumor,...patch}),false));
}
const initial={id:'b'.repeat(64),content:'ciphertext-metadata'},fresh={id:'c'.repeat(64),content:'fresh-ciphertext-metadata'};
check('identical-replay-preserves-entire-outer',()=>assert.equal(replayBinding(stageSpec('archive',1),{...initial},initial),true));
check('identical-replay-cannot-mutate-content',()=>assert.equal(replayBinding(stageSpec('archive',1),{...initial,content:'changed'},initial),false));
check('fresh-wrap-id-must-differ',()=>assert.equal(replayBinding(stageSpec('archive',2),initial,initial),false));
check('fresh-wrap-distinct-id-metadata',()=>assert.equal(replayBinding(stageSpec('archive',2),fresh,initial),true));
const attempt={epoch:1,stageId:'archive-identical-replay'};
check('same-attempt-custody',()=>assert.equal(attemptLineageMatches(attempt,{...attempt},{...attempt}),true));
for(const [name,forward,complete] of [['old-forward',{...attempt,epoch:0},attempt],['old-completion',attempt,{...attempt,epoch:0}],
 ['wrong-stage',{...attempt,stageId:'archive-business'},attempt],['missing',null,attempt],['typed-epoch',{...attempt,epoch:'1'},attempt]]){
 check('refuse-attempt-'+name,()=>assert.equal(attemptLineageMatches(attempt,forward,complete),false));
}
check('unknown-stage-is-not-an-attempt-contract',()=>assert.equal(attemptLineageMatches({epoch:1,stageId:'unknown'},{epoch:1,stageId:'unknown'},{epoch:1,stageId:'unknown'}),false));
for(const [role,index] of [['incoming',0],['incoming',1],['archive',0],['archive',2]]){
 check('new-app-frame-required-'+role+'-'+index,()=>assert.equal(stageDeliveryAllowed(stageSpec(role,index),false,'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'),false));
}
check('identical-replay-query-absence-is-labelled-not-receipt',()=>assert.equal(stageDeliveryAllowed(stageSpec('archive',1),false,'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'),true));
check('query-cannot-claim-app-frame',()=>assert.equal(stageDeliveryAllowed(stageSpec('archive',1),true,'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'),false));
check('prior-frame-cannot-fill-missing-current-delivery',()=>assert.equal(stageDeliveryAllowed(stageSpec('archive',1),false,'ACTUAL_APP_SOCKET_FRAME'),false));
check('unknown-stage-shape-does-not-open-future-scope',()=>assert.equal(stageDeliveryAllowed({...stageSpec('archive',1),id:'unknown'},false,'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'),false));
check('mutated-stage-policy-refuses',()=>assert.equal(stageDeliveryAllowed({...stageSpec('archive',2),requiresNewAppFrame:false},false,'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'),false));
console.log(JSON.stringify({scope:'MINIMUM_ROLE_REPLAY_ORIGIN_METADATA_CONTROLS_ONLY',checks:cases.length,cases,
 cryptoExecuted:false,actualClientExecuted:false,canonicalPromotion:false}));
