// Pure scheduling regressions for the exact production upstream callback.
// No socket, helper process, lease file, Docker, VM or real clock is used.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';
import {createGuardClient} from './candidate/guard-client-core.mjs';
import {proxyContinuationValid} from './candidate/proxy-observer.mjs';
import {subscriptionRequestSnapshot,publicationGenerationMatches} from './candidate/fixture.mjs';

const NS=1000000000n;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const baseline=fs.readFileSync(new URL('./baseline/fixture.mjs',import.meta.url),'utf8');
const candidate=fs.readFileSync(new URL('./candidate/fixture.mjs',import.meta.url),'utf8');
const need=(value,reason)=>{if(!value)throw Error(reason);};

function callbackSource(source){
 const begin="    upstream.on('message',(data,binary)=>callback(async()=>{";
 const end='    app.resume();';
 const first=source.indexOf(begin),last=source.indexOf(end,first);
 assert(first>=0&&source.indexOf(begin,first+1)===-1&&last>first);
 const block=source.slice(first,last);
 assert(block.trimEnd().endsWith('}));'));
 return block;
}

function harness(source){
 let now={Utc:100n*NS,Mono:100n*NS,Boot:100n*NS};
 let revoked=false,ownerEnd=1900n*NS,handler,transportHandlers,delivered=0,settled=0;
 const requests=[],guardEvents=[],tasks=[],callbackErrors=[],proxyRows=[],sends=[],contexts=[],timers=new Map();
 let timer=0;
 const lease={runId:'1'.repeat(32),bootId:'synthetic-boot',issuedUtcNs:99n*NS,
  issuedMonoNs:99n*NS,issuedBootNs:99n*NS,deadlineUtcNs:1900n*NS,
  deadlineMonoNs:1900n*NS,deadlineBootNs:1900n*NS};
 const clock={sample:()=>({...now}),arm:fn=>{timers.set(++timer,fn);return timer;},clear:key=>timers.delete(key)};
 const transport={bind:value=>{transportHandlers=value;},start(){},send:raw=>requests.push(Buffer.from(raw)),abort(){}};
 const guard=createGuardClient({transport,clock,lease,leaseSha256:'2'.repeat(64),instance:'3'.repeat(32),
  ownerDeadlines:()=>[ownerEnd],isRevoked:()=>revoked,
  observe:(name,fields)=>guardEvents.push({name,...fields})});
 const c={id:1,active:true,generation:0,appReceiptGeneration:1,
  subscriptions:new Map([['first',{req:1,eose:null,filters:[{kinds:[1059]}]}],
                         ['second',{req:2,eose:null,filters:[{kinds:[1059]}]}]])};
 const app={readyState:1,send(bytes,options,done){assert.equal(options.binary,false);sends.push(Buffer.from(bytes));done(null);}};
 const log=fields=>{const row={sequence:proxyRows.length+1,...fields};proxyRows.push(row);return row;};
 function callback(fn){
  try{
   const value=fn();
   if(value&&typeof value.then==='function'){
    tasks.push(value);value.then(()=>{settled++;},error=>{settled++;callbackErrors.push(error);});
   }
   return value;
  }catch(error){callbackErrors.push(error);guard.cancel(error);}
 }
 const sandbox={Buffer,JSON,need,sha,subscriptionRequestSnapshot,proxyContinuationValid,
  c,app,connections:new Map([[1,c]]),WebSocket:{OPEN:1},
  upstream:{on(name,fn){assert.equal(name,'message');assert.equal(handler,undefined);handler=fn;}},
  callback,proxyPhase(){},log,same:(a,b)=>JSON.stringify(a)===JSON.stringify(b),
  attempted:false,publicationWindowOpen:false,publicationInvalidated:false,publicationGate:null,
  activeAttempt:null,stageIndex:0,spec:{stages:[],account:'synthetic-public-recipient'},delivery:null,
  T:{strictJSON:JSON.parse},closed:false,
  selectedEvent(){throw Error('UNEXPECTED_PUBLICATION_TEST_EFFECT');},
  publicationGenerationMatches(){throw Error('UNEXPECTED_PUBLICATION_TEST_EFFECT');},
  attemptLineageMatches(){throw Error('UNEXPECTED_PUBLICATION_TEST_EFFECT');},
  serviceGuard(label,context,effect,options){
   contexts.push({label,bytes:context});return guard.run(label,context,effect,options);
  }};
 const currentGeneration=source.match(/^function currentGeneration\(c,id\)\{[^\n]+\}$/m)?.[0];
 const invalidate=source.match(/^ function invalidatePublication\(c,id,reason\)\{[^\n]+\}$/m)?.[0];
 const connectionValid=source.match(/^ const connectionValid=[^\n]+;/m)?.[0];
 assert(currentGeneration&&invalidate&&connectionValid);
 vm.runInNewContext(currentGeneration+'\n'+invalidate+'\n'+connectionValid+'\n'+callbackSource(source),sandbox,{timeout:1000});
 function emit(id,type='EOSE'){
  const bytes=Buffer.from(JSON.stringify([type,id]));handler(bytes,false);return bytes;
 }
 function reply(){
  assert(delivered<requests.length,'NO_UNDELIVERED_RPC');
  const raw=requests[delivered],q=JSON.parse(raw);
  return {...q,schema:'e02-fresh-guard-response-v1',requestSha256:sha(raw),ok:true,
   clocks:{Utc:String(now.Utc),Mono:String(now.Mono),Boot:String(now.Boot),bootId:lease.bootId}};
 }
 function deliver(value=reply()){
  assert(delivered<requests.length,'NO_UNDELIVERED_RPC');delivered++;
  transportHandlers.response(Buffer.from(JSON.stringify(value)+'\n'));
 }
 async function tick(){await Promise.resolve();await Promise.resolve();await Promise.resolve();}
 async function drain(){
  for(let i=0;i<64;i++){
   if(delivered<requests.length)deliver();
   await tick();
   if(guard.state().pending===0&&settled===tasks.length){assert.equal(timers.size,0);return;}
  }
  throw Error('PURE_TEST_QUEUE_DID_NOT_SETTLE');
 }
 return {c,guard,lease,emit,reply,deliver,tick,drain,requests,guardEvents,proxyRows,sends,contexts,callbackErrors,sandbox,
  set:(domain,value)=>{now[domain]=value;},advance:delta=>{for(const k of ['Utc','Mono','Boot'])now[k]+=delta;},
  revoke:()=>{revoked=true;},setOwnerEnd:value=>{ownerEnd=value;}};
}

const cases=[];
async function check(name,run){await run();cases.push(name);}
async function refused(f,pattern){
 await f.drain();assert.match(f.guard.state().firstFault,pattern);
 assert.equal(f.sends.length,0);assert(f.callbackErrors.length>0);
}

await check('baseline_actual_callback_reproduces_unrelated_eose_queue_failure',async()=>{
 const f=harness(baseline);f.emit('first');f.emit('second');
 assert.equal(f.requests.length,1);f.deliver();
 await refused(f,/QUEUED_CONTEXT_CHANGED/);
 assert.equal(f.requests.length,1);assert.equal(f.proxyRows.length,1);
 assert.equal(f.c.subscriptions.get('first').eose,1);
 assert.equal(f.c.subscriptions.get('second').eose,null);
});
for(const second of ['second','first'])await check('corrected_actual_callback_queued_eose_'+second,async()=>{
 const f=harness(candidate);const a=f.emit('first'),b=f.emit(second);
 assert.equal(f.requests.length,1);f.deliver();assert.equal(f.requests.length,2);
 await f.drain();assert.equal(f.guard.state().firstFault,null);assert.equal(f.callbackErrors.length,0);
 assert.deepEqual(f.sends,[a,b]);assert.equal(f.proxyRows.filter(r=>r.direction==='RELAY_TO_APP').length,2);
 assert(f.c.subscriptions.get(second).eose!==null);
});

const mutations=[
 ['request_replacement',f=>{f.c.subscriptions.set('second',{req:3,eose:null,filters:[{kinds:[1059]}]});}],
 ['filter_mutation',f=>{f.c.subscriptions.get('second').filters[0].kinds=[14];}],
 ['subscription_close',f=>{f.c.subscriptions.delete('second');}],
 ['subscription_added',f=>{f.c.subscriptions.set('third',{req:3,eose:null,filters:[]});}],
 ['extra_nonprogress_field',f=>{f.c.subscriptions.get('second').unexpected='changed';}],
 ['connection_close',f=>{f.c.active=false;}],
 ['connection_generation',f=>{f.c.generation++;}],
 ['app_receipt_generation',f=>{f.c.appReceiptGeneration++;}],
 ['queued_raw_buffer_mutation',f=>{f.contexts[1].bytes[0]=0;}]
];
for(const [name,change] of mutations)await check('corrected_refuses_'+name,async()=>{
 const f=harness(candidate);f.emit('first');f.emit('second');
 // Commit the first genuine EOSE, then mutate only the still-queued second
 // context before pump's immediate validity decision after that first effect.
 // The injected mutation runs in the first actual log sink, inside its effect.
 const original=f.sandbox.log;
 f.sandbox.log=fields=>{const row=original(fields);if(row.sequence===1)change(f);return row;};
 f.deliver();await refused(f,/QUEUED_CONTEXT_CHANGED/);
 assert.equal(f.requests.length,1);assert.equal(f.proxyRows.length,1);
});

await check('corrected_guard_enqueue_original_five_seconds',async()=>{
 const f=harness(candidate);f.emit('first');f.emit('second');f.advance(5n*NS);
 await refused(f,/GUARD_ENQUEUE_INCLUSIVE_DEADLINE/);assert.equal(f.proxyRows.length,0);
});
await check('corrected_external_sticky_revocation',async()=>{
 const f=harness(candidate);f.emit('first');f.emit('second');f.revoke();
 await refused(f,/EXTERNAL_STICKY_REVOCATION/);assert.equal(f.proxyRows.length,0);
});
for(const domain of ['Utc','Mono','Boot'])await check('corrected_original_lease_expiry_'+domain,async()=>{
 const f=harness(candidate);f.lease['deadline'+domain+'Ns']=101n*NS;
 f.emit('first');f.emit('second');const held=f.reply();f.set(domain,101n*NS);f.deliver(held);
 await refused(f,/ORIGINAL_LEASE_DEADLINE/);assert.equal(f.proxyRows.length,0);
});
await check('corrected_original_owner_deadline',async()=>{
 const f=harness(candidate);f.setOwnerEnd(101n*NS);f.emit('first');f.emit('second');f.advance(NS);
 await refused(f,/ORIGINAL_OPERATION_DEADLINE/);assert.equal(f.proxyRows.length,0);
});
await check('corrected_before_send_publication_invalidation_stays_fatal',async()=>{
 const f=harness(candidate);f.emit('first');f.deliver();await f.tick();
 assert.equal(JSON.parse(f.requests[1]).label,'proxy:before-app-send');
 f.sandbox.publicationInvalidated=true;
 await refused(f,/CURRENT_GUARD_CONTEXT_CHANGED/);assert.equal(f.sends.length,0);
});
await check('publication_generation_still_binds_exact_eose_sequence',async()=>{
 const recipient='b'.repeat(64),event={id:'a'.repeat(64),pubkey:'c'.repeat(64),kind:1059,created_at:100,tags:[['p',recipient]]};
 const c={id:1,active:true,subscriptions:new Map([['sub',{req:1,eose:2,filters:[{kinds:[1059],'#p':[recipient]}]}]])};
 const m=new Map([[1,c]]),expected={connection:1,subscription:'sub',requestSequence:1,eoseSequence:2};
 assert.equal(publicationGenerationMatches(m,expected,event,recipient),true);
 c.subscriptions.get('sub').eose=3;
 assert.equal(publicationGenerationMatches(m,expected,event,recipient),false);
});
console.log(JSON.stringify({schema:'e02-fixture-eose-pure-regression-result-v1',scope:'EXACT_SOURCE_CALLBACK_AND_UNCHANGED_GUARD_CORE_WITH_FAKE_TRANSPORT_AND_CLOCKS',
 checks:cases.length,cases,baselineFailureReproduced:true,baselineFailure:'QUEUED_CONTEXT_CHANGED',
 runtimeExecuted:false,helperExecuted:false,networkExecuted:false,ordinaryRowsQualified:0,canonicalE02:'PARTIAL22'}));
