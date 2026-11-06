// PREPARED model controls only: fake sockets, fake clock/timers, no real guard,
// network, crypto primitive, native child, Docker, relay, Android or SDK.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {exchange} from './exchange.mjs';
import {strictJSON,same} from './strict-json.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
const EVENT={id:'a'.repeat(64),kind:1059,tags:[['p','b'.repeat(64)]],content:'MODEL_NOT_CIPHERTEXT'};
const cases=[];const test=async(name,fn)=>{await fn();cases.push(name);};
function model(options={}){
 const phases=[],files=new Map(),sockets=[],timers=[];let tick=0n,held=null;
 const sha=b=>createHash('sha256').update(b).digest('hex');
 const phase=(name,v={})=>{phases.push({phase:name,...v});if(options.failPhase===name)throw Error('MODEL_PHASE_WRITE_FAILURE:'+name);};
 function responses(socket,frame){if(options.silent)return;
  const values=frame[0]==='EVENT'?[['OK',EVENT.id,options.refusal!==true,'']]:[['EVENT','e02-owned-query',options.wrongEvent?{...EVENT,id:'c'.repeat(64)}:EVENT],['EOSE',options.wrongEose?'wrong-subscription':'e02-owned-query']];
  for(const value of values)socket.emit('message',Buffer.from(JSON.stringify(value)));
 }
 class FakeSocket{
  constructor(url,settings){this.url=url;this.settings=settings;this.handlers={};this.sent=[];this.terminated=false;this.terminationCount=0;sockets.push(this);queueMicrotask(()=>{if(options.socketError)this.emit('error',Error('MODEL_SOCKET_ERROR'));else if(options.earlyClose)this.emit('close');else this.emit('open');});}
  on(name,fn){(this.handlers[name]??=[]).push(fn);}
  emit(name,...args){for(const f of this.handlers[name]??[])f(...args);}
  send(bytes,settings,callback){this.sent.push(Buffer.from(bytes));const f=JSON.parse(bytes);if(options.mutate)bytes[0]=32;
   queueMicrotask(()=>{if(options.holdCallback){held=()=>callback(null);responses(this,f);}else if(options.replyBeforeCallback){responses(this,f);callback(null);}else{callback(options.sendError?Error('MODEL_SEND_ERROR'):null);if(!this.terminated)responses(this,f);}});
  }
  terminate(){this.terminationCount++;this.terminated=true;queueMicrotask(()=>this.emit('close'));}
 }
 const ctx={WebSocket:FakeSocket,p:{backendUrl:'ws://127.0.0.1:8080',limits:{messageBytes:262144,networkTimeoutMilliseconds:10000}},
  check:label=>{phase('MODEL_GUARD_ENTRY',{label});if(options.deny===label){phase('MODEL_GUARD_REFUSED',{label});throw Error('MODEL_GUARD_DENIED');}phase('MODEL_GUARD_OK',{label});},phase,
  put:(name,raw)=>{if(options.failOutcome&&name.endsWith('-outcome.json'))throw Error('MODEL_OUTCOME_WRITE_FAILURE');assert.equal(files.has(name),false);files.set(name,Buffer.from(raw));return {path:'/MODEL_ONLY/'+name,bytes:raw.length,sha256:sha(raw)};},strictJSON,sha,clock:()=>{tick+=1000n;return tick;},
  arm:(fn,ms)=>{const t={fn,ms,cleared:false};timers.push(t);return t;},clear:t=>{t.cleared=true;}};
 return {ctx,phases,files,sockets,timers,fire:()=>{for(const t of timers)if(!t.cleared)t.fn();},release:()=>held(),drain:async()=>{await Promise.resolve();await Promise.resolve();await Promise.resolve();}};
}
await test('original10s3s-ack-and-real-send-callback-model',async()=>{const m=model();const r=await exchange(m.ctx,[EVENT],null,'model-publish');assert.equal(m.timers[0].ms,10000);assert.equal(m.sockets[0].settings.handshakeTimeout,3000);assert.equal(r.ack[0].frame[2],true);assert.equal(r.sentFrames[0].sendInvoked,true);assert.equal(r.sentFrames[0].sendCallbackCompleted,true);assert.equal(r.sentFrames[0].callbackBufferHash,r.sentFrames[0].frame.sha256);});
await test('query-event-and-exact-eose-model',async()=>{const m=model();const r=await exchange(m.ctx,null,{ids:[EVENT.id],limit:1},'model-query');assert.equal(r.received.length,1);assert.deepEqual(r.eose.frame,['EOSE','e02-owned-query']);});
await test('eose-before-send-callback-does-not-require-packet-order',async()=>{const m=model({replyBeforeCallback:true});const r=await exchange(m.ctx,null,{ids:[EVENT.id],limit:1},'model-query');assert.equal(r.sentFrames[0].sendCallbackCompleted,true);});
await test('no-success-until-actual-model-send-callback',async()=>{const m=model({holdCallback:true});let resolved=false;const p=exchange(m.ctx,null,{ids:[EVENT.id],limit:1},'model-query').then(r=>{resolved=true;return r;});await m.drain();assert.equal(resolved,false);m.release();await p;});
await test('timeout-retains-partial-send-state-and-rejection',async()=>{const m=model({silent:true});const p=exchange(m.ctx,null,{ids:[EVENT.id],limit:1},'model-query');await m.drain();m.fire();await assert.rejects(p,/RELAY_TIMEOUT/);const outcome=JSON.parse(m.files.get('model-query-outcome.json'));assert.equal(outcome.sentFrames[0].sendCallbackCompleted,true);assert.equal(outcome.eose,null);assert.match(outcome.error,/RELAY_TIMEOUT/);});
await test('intent-is-before-send-invoke-not-callback-proof',async()=>{const m=model();await exchange(m.ctx,[EVENT],null,'model-publish');const names=m.phases.map(x=>x.phase);assert.ok(names.indexOf('SEND_INTENT')<names.indexOf('SEND_INVOKE_ENTRY'));assert.ok(names.indexOf('SEND_INVOKE_RETURNED')<names.indexOf('SEND_CALLBACK_ENTRY'));});
await test('raw-backend-callback-precedes-original-guard',async()=>{const m=model();await exchange(m.ctx,[EVENT],null,'model-publish');const i=m.phases.findIndex(x=>x.phase==='RAW_BACKEND_CALLBACK_ENTRY');assert.equal(m.phases[i+1].phase,'MODEL_GUARD_ENTRY');assert.equal(m.phases[i+1].label,'backend-message');});
await test('guard-refused-open-sends-nothing',async()=>{const m=model({deny:'socket-open'});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/MODEL_GUARD_DENIED/);assert.equal(m.sockets[0].sent.length,0);});
await test('guard-refused-before-send-sends-nothing',async()=>{const m=model({deny:'send-before'});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/MODEL_GUARD_DENIED/);assert.equal(m.sockets[0].sent.length,0);});
await test('guard-refused-message-keeps-raw-context-without-success',async()=>{const m=model({deny:'backend-message'});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/MODEL_GUARD_DENIED/);assert.equal(m.phases.some(x=>x.phase==='RAW_BACKEND_CALLBACK_ENTRY'),true);assert.equal(m.phases.some(x=>x.phase==='BACKEND_MESSAGE_GUARD_PASSED'),false);});
await test('guard-refused-send-callback-is-not-completed',async()=>{const m=model({deny:'send-callback'});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/MODEL_GUARD_DENIED/);const o=JSON.parse(m.files.get('model-publish-outcome.json'));assert.equal(o.sentFrames[0].sendCallbackCompleted,false);});
await test('send-error-preserves-error-no-success',async()=>{const m=model({sendError:true});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/MODEL_SEND_ERROR/);});
await test('same-buffer-mutation-refuses',async()=>{const m=model({mutate:true});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/ACTUAL_SENT_BUFFER_MUTATION/);});
await test('relay-negative-ack-refuses',async()=>{const m=model({refusal:true});await assert.rejects(exchange(m.ctx,[EVENT],null,'model-publish'),/RELAY_REFUSAL/);});
await test('wrong-eose-subscription-never-completes',async()=>{const m=model({wrongEose:true});const p=exchange(m.ctx,null,{ids:[EVENT.id],limit:1},'model-query');await m.drain();m.fire();await assert.rejects(p,/RELAY_TIMEOUT/);});
await test('late-message-after-terminal-has-no-writes-actions',async()=>{const m=model();await exchange(m.ctx,[EVENT],null,'model-publish');const before=m.phases.length;m.sockets[0].emit('message',Buffer.from('["EOSE","e02-owned-query"]'));assert.equal(m.phases.length,before);assert.equal(m.sockets[0].terminationCount,1);});
await test('same-original-query-result-object-key-order-independent',()=>assert.equal(same({id:'x',kind:1059},{kind:1059,id:'x'}),true));
await test('same-query-result-content-change-refuses',()=>assert.equal(same(EVENT,{...EVENT,content:'changed'}),false));
await test('original-strict-json-duplicate-key-refuses',()=>assert.throws(()=>strictJSON('{"id":"x","id":"y"}')));
await test('unknown-exchange-label-refuses-before-socket',async()=>{const m=model();await assert.rejects(exchange(m.ctx,[EVENT],null,'../outside'),/FIXED_EXCHANGE_LABEL/);assert.equal(m.sockets.length,0);});
// Focused new fault families exercise the real exchange with synthetic sinks;
// microtask settlement checks deliberately do NOT fire an outer timeout.
async function terminalFault(options,expected,{fire=false,query=false}={}){
 const m=model(options);let settled=0,result=null,error=null;
 const promise=exchange(m.ctx,query?null:[EVENT],query?{ids:[EVENT.id],limit:1}:null,query?'model-query':'model-publish');
 promise.then(r=>{settled++;result=r;},e=>{settled++;error=e;});
 await m.drain();await m.drain();if(fire){m.fire();await m.drain();}
 assert.equal(settled,1,'must settle without an outer watchdog');assert.equal(result,null);assert.match(String(error),expected);
 assert.equal(m.sockets[0].terminationCount,1);const n=m.phases.length;
 m.sockets[0].emit('error',Error('LATE'));m.sockets[0].emit('close');m.sockets[0].emit('message',Buffer.from('[]'));m.timers[0]?.fn();await m.drain();
 assert.equal(settled,1);assert.equal(m.sockets[0].terminationCount,1);assert.equal(m.phases.length,n);
 return {m,error};
}
await test('terminal-phase-and-outcome-failure-success-path-rejects-once',async()=>{
 await terminalFault({failPhase:'EXCHANGE_RESOLVED'},/MODEL_PHASE_WRITE_FAILURE/);
 await terminalFault({failOutcome:true},/MODEL_OUTCOME_WRITE_FAILURE/);
});
await test('terminal-retention-failure-preserves-original-protocol-fault',async()=>{
 for(const extra of [{failPhase:'EXCHANGE_REJECTED'},{failOutcome:true}]){
  const {error}=await terminalFault({refusal:true,...extra},/RELAY_REFUSAL/);
  assert.ok(error.diagnosticSecondaryErrors.length>0);
 }
});
await test('raw-timer-error-close-callback-write-fault-boundaries',async()=>{
 await terminalFault({failPhase:'RAW_BACKEND_CALLBACK_ENTRY'},/MODEL_PHASE_WRITE_FAILURE/);
 await terminalFault({silent:true,failPhase:'TIMER_FIRED'},/RELAY_TIMEOUT/,{fire:true});
 await terminalFault({socketError:true,failPhase:'SOCKET_ERROR_CALLBACK_ENTRY'},/MODEL_SOCKET_ERROR/);
 await terminalFault({earlyClose:true,failPhase:'SOCKET_CLOSE_CALLBACK_ENTRY'},/EARLY_RELAY_CLOSE/);
 await terminalFault({sendError:true,failPhase:'SEND_CALLBACK_ENTRY'},/MODEL_SEND_ERROR/);
 await terminalFault({failPhase:'TIMER_ARMED'},/MODEL_PHASE_WRITE_FAILURE/);
});
await test('required-publication-write-failure-prevents-followup-query',async()=>{
 const m=model({failOutcome:true});let queryStarted=false;
 await assert.rejects((async()=>{await exchange(m.ctx,[EVENT],null,'model-publish');queryStarted=true;await exchange(m.ctx,null,{ids:[EVENT.id],limit:1},'model-query');})(),/MODEL_OUTCOME_WRITE_FAILURE/);
 assert.equal(queryStarted,false);assert.equal(m.sockets.length,1);
});
function writerModel(write,limit=16777216){let calls=0,physical=Buffer.alloc(0);const fs={writeSync:(_fd,raw)=>{calls++;return write(raw,b=>{physical=Buffer.concat([physical,b]);});}};const writer=createPhaseWriter({fs,fd:123,clock:()=>1n,utc:()=> 'MODEL',limit});return {writer,calls:()=>calls,physical:()=>physical};}
await test('writer-full-write-and-acknowledged-short-prefix-are-distinct',()=>{
 const full=writerModel((raw,persist)=>{persist(raw);return raw.length;});full.writer('FULL');assert.equal(full.calls(),1);assert.equal(full.writer.state().poisoned,false);assert.equal(full.writer.state().physicalBytes,null);
 for(const count of [0,3]){
  const m=writerModel((raw,persist)=>{persist(raw.subarray(0,count));return count;});assert.throws(()=>m.writer('SHORT'),/SHORT_PHASE_WRITE/);
  const state=m.writer.state();assert.equal(state.lastAttempt.acknowledgedBytes,count);assert.equal(m.physical().length,count);assert.equal(Buffer.from(state.lastAttempt.acknowledgedPrefixBase64,'base64').length,count);assert.equal(state.physicalBytes,null);
  assert.throws(()=>m.writer('NO_RETRY'));assert.equal(m.calls(),1);
 }
});
await test('writer-throw-invalid-count-overflow-poisons-with-no-retry',()=>{
 const thrown=writerModel((raw,persist)=>{persist(raw.subarray(0,2));throw Error('MODEL_SINK_THROW');});assert.throws(()=>thrown.writer('THROW'),/MODEL_SINK_THROW/);assert.equal(thrown.writer.state().lastAttempt.acknowledgedBytes,null);assert.equal(thrown.writer.state().physicalBytes,null);assert.equal(thrown.physical().length,2);assert.throws(()=>thrown.writer('NO_RETRY'));assert.equal(thrown.calls(),1);
 for(const count of [-1,1.5,'bad',999999,NaN]){const m=writerModel(()=>count);assert.throws(()=>m.writer('INVALID'),/INVALID_PHASE_WRITE_COUNT/);assert.equal(m.writer.state().lastAttempt.acknowledgedBytes,null);assert.throws(()=>m.writer('NO_RETRY'));assert.equal(m.calls(),1);}
 const overflow=writerModel(()=>{throw Error('MUST_NOT_WRITE');},1);assert.throws(()=>overflow.writer('OVERFLOW'),/ORIGINAL_CAPTURE_BOUND/);assert.equal(overflow.calls(),0);assert.equal(overflow.writer.state().lastAttempt.acknowledgedBytes,0);assert.throws(()=>overflow.writer('NO_RETRY'));assert.equal(overflow.calls(),0);
});
await test('poisoned-real-writer-forces-exchange-reject-no-second-send',async()=>{
 const m=model();let calls=0;const writer=createPhaseWriter({fs:{writeSync:(_fd,raw)=>{calls++;return calls===4?0:raw.length;}},fd:123,clock:()=>1n,utc:()=> 'MODEL'});
 m.ctx.phase=writer;let settled=0,error=null;exchange(m.ctx,[EVENT],null,'model-publish').then(()=>settled++,e=>{settled++;error=e;});await m.drain();await m.drain();assert.equal(settled,1);assert.match(String(error),/SHORT_PHASE_WRITE/);assert.equal(m.sockets[0].terminationCount,1);assert.equal(m.sockets[0].sent.length,0);const n=calls;assert.throws(()=>writer('AFTER_POISON'));assert.equal(calls,n);
});
console.log(JSON.stringify({scope:'TRANSPORT_QUERY_FAKE_SOCKET_PHASE_MODEL_ONLY',checks:cases.length,cases,realGuardExecuted:false,networkExecuted:false,cryptoExecuted:false,ordinaryClientQualified:false}));
