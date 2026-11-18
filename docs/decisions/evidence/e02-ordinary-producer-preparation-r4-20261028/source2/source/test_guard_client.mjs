// SOURCE definitions only until separately released. No real child/fs/network.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createGuardClient} from './guard-client-core.mjs';
import {strictGuardJSON,createGuardFramer} from './guard-wire.mjs';
import {proxyContinuationValid,flowContinuationValid,createProxySocketErrorBoundary} from './proxy-observer.mjs';
import {createCaptureBudget} from './capture-budget.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
import {createByteAccount} from './capture-allocation.mjs';
import {cleanupPlan,dispatchOwnedSignal} from './guard-transport-boundaries.mjs';

const NS=1000000000n,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function fixture({owner=()=>[],observe=()=>{},id='3',lowerUncertainty={}}={}){
 let now={Utc:100n*NS,Mono:100n*NS,Boot:100n*NS},revoked=false,handlers,started=0,aborted=0,effects=0,fatal=0;
 const sent=[],records=[],timers=new Map();let tid=0;
 const lease={runId:'1'.repeat(32),bootId:'b',issuedUtcNs:99n*NS,issuedMonoNs:99n*NS,issuedBootNs:99n*NS,deadlineUtcNs:1900n*NS,deadlineMonoNs:1900n*NS,deadlineBootNs:1900n*NS};
 const clock={sample:()=>({...now,...Object.fromEntries(Object.entries(lowerUncertainty).map(([k,q])=>[k+'Lower',now[k]-q]))}),arm:fn=>{timers.set(++tid,fn);return tid;},clear:id=>timers.delete(id)};
 const transport={bind:h=>{handlers=h;},start:()=>{started++;},send:b=>sent.push(Buffer.from(b)),abort:()=>{aborted++;}};
 const client=createGuardClient({transport,clock,lease,leaseSha256:'2'.repeat(64),instance:id.repeat(32),ownerDeadlines:owner,isRevoked:()=>revoked,observe:(n,f)=>{records.push({name:n,fields:f});observe(n,f);},onFatal:()=>{fatal++;}});
 function reply(index=sent.length-1){const q=JSON.parse(sent[index]);return {schema:'e02-fresh-guard-response-v1',...q,schema:'e02-fresh-guard-response-v1',requestSha256:sha(sent[index]),ok:true,clocks:q.operation==='CLOSE'?null:{Utc:String(now.Utc),Mono:String(now.Mono),Boot:String(now.Boot),bootId:'b'}};}
 function deliver(value=reply()){handlers.response(Buffer.from(JSON.stringify(value)+'\n'));}
 function run(label='test:point',options={}){return client.run(label,Buffer.from('immutable-context'),()=>{effects++;return effects;},options);}
 return {client,lease,run,reply,deliver,sent,records,timers,handlers:()=>handlers,advance:(delta)=>{for(const k of ['Utc','Mono','Boot'])now[k]+=delta;},set:(kind,v)=>{now[kind]=v;},now:()=>({...now}),effects:()=>effects,revokeExternal:()=>{revoked=true;},state:()=>({started,aborted,fatal})};
}
const definitions=[];
function model(name,fn){definitions.push({name,fn});}
async function refused(f,p){await assert.rejects(p);assert.equal(f.effects(),0);assert.notEqual(f.client.state().firstFault,null);}
model('fresh_checks_are_one_use_and_not_cached',async()=>{const f=fixture();const p=f.run();assert.equal(f.effects(),0);f.deliver();assert.equal(await p,1);const q=f.run();assert.equal(f.sent.length,2);assert.equal(f.effects(),1);f.deliver();assert.equal(await q,2);assert.notEqual(f.sent[0].toString(),f.sent[1].toString());});
model('queue_wait_in_original_five_seconds',async()=>{const f=fixture(),a=f.run(),b=f.run();a.catch(()=>{});b.catch(()=>{});assert.equal(f.sent.length,1);const held=f.reply();f.advance(5n*NS);f.deliver(held);await refused(f,a);await assert.rejects(b);assert.equal(f.sent.length,1);});
model('startup_in_original_five_seconds',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});f.advance(5n*NS);f.deliver();await refused(f,p);});
model('queue_sixty_fifth_rejected_without_effect',async()=>{const f=fixture(),pending=Array.from({length:65},()=>f.run());for(const p of pending)p.catch(()=>{});await Promise.all(pending.map(p=>assert.rejects(p)));assert.equal(f.effects(),0);assert.equal(f.sent.length,1);});
model('queue_payload_overflow',async()=>{const f=fixture(),p=f.client.run('point',Buffer.alloc(16777217),()=>{throw Error('must not run');});await assert.rejects(p);assert.equal(f.sent.length,0);});
for(const [field,value] of [['instance','f'.repeat(32)],['runId','f'.repeat(32)],['leaseSha256','f'.repeat(64)],['sequence','2'],['label','other'],['contextSha256','f'.repeat(64)],['requestSha256','f'.repeat(64)],['operation','CLOSE'],['schema','unknown'],['ok',false]])model('response_binding_'+field,async()=>{const f=fixture(),p=f.run();p.catch(()=>{});f.deliver({...f.reply(),[field]:value});await refused(f,p);});
model('response_extra_key_refused',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});f.deliver({...f.reply(),extra:true});await refused(f,p);});
model('duplicate_response_rejected_not_reused',async()=>{const f=fixture(),p=f.run();const r=f.reply();f.deliver(r);await p;f.deliver(r);assert.notEqual(f.client.state().firstFault,null);assert.equal(f.effects(),1);});
for(const text of ['{"x":1,"x":2}','{"x":-0}','{"x":NaN}','{"x":Infinity}','{"x":1.1}','{"x":01}','{"x":1e3}','{"x":"a"} trailing','{"x":"\\u000z"}','{"x":"a\n"}'])model('strict_wire_'+Buffer.from(text).toString('hex'),async()=>assert.throws(()=>strictGuardJSON(text)));
model('missing_newline_refused',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});f.handlers().response(Buffer.from(JSON.stringify(f.reply())));await refused(f,p);});
model('oversize_reply_refused',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});f.handlers().response(Buffer.alloc(2049));await refused(f,p);});
for(const fault of ['DENY','STDERR','CHILD_DEATH','UNEXPECTED_EOF','CANCEL','CAPTURE_POISON'])model('immediate_fence_'+fault+'_then_late_ok',async()=>{const f=fixture(),p=f.run(),q=f.run();p.catch(()=>{});q.catch(()=>{});const held=f.reply();f.handlers().fatal(Error(fault));f.deliver(held);await refused(f,p);await assert.rejects(q);assert.equal(f.state().fatal,1);assert.equal(f.sent.length,1);assert.equal(f.records.some(r=>r.name==='GUARD_EXIT'&&r.fields.ok),false);});
model('held_ok_query_deadline_without_timer',async()=>{const f=fixture(),p=f.run('query',{deadlines:[101n*NS]});p.catch(()=>{});const held=f.reply();f.advance(NS);f.deliver(held);await refused(f,p);});
model('held_ok_handshake_deadline_without_timer',async()=>{const f=fixture(),p=f.run('handshake',{deadlines:[103n*NS]});p.catch(()=>{});const held=f.reply();f.advance(3n*NS);f.deliver(held);await refused(f,p);});
model('held_ok_control45_deadline_without_timer',async()=>{const f=fixture({owner:()=>[145n*NS]});f.advance(44n*NS);const p=f.run('control',{deadlines:[145n*NS]});p.catch(()=>{});const held=f.reply();f.advance(NS);f.deliver(held);await refused(f,p);});
for(const kind of ['Utc','Mono','Boot'])model('held_ok_lease_expiry_'+kind,async()=>{const f=fixture(),p=f.run();p.catch(()=>{});const held=f.reply();f.set(kind,f.lease['deadline'+kind+'Ns']);f.deliver(held);await refused(f,p);});
model('suspend_during_reply_exceeds_boot_five_seconds',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});const held=f.reply();f.set('Utc',120n*NS);f.set('Boot',120n*NS);f.deliver(held);await refused(f,p);});
model('utc_rollback_after_actual_check',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});const held=f.reply();f.set('Utc',99n*NS);f.deliver(held);await refused(f,p);});
model('generation_changes_while_awaiting',async()=>{const f=fixture();let generation=1;const p=f.run('generation',{valid:()=>generation===1});p.catch(()=>{});generation=2;f.deliver();await refused(f,p);});
model('buffer_mutation_context_refuses',async()=>{const f=fixture();const bytes=Buffer.from('original'),hash=sha(bytes);const p=f.run('buffer',{valid:()=>sha(bytes)===hash});p.catch(()=>{});bytes[0]=1;f.deliver();await refused(f,p);});
for(const kind of ['decision','query','lease'])model('valid_callback_crosses_'+kind+'_deadline',async()=>{const f=fixture();const options={valid:()=>{if(kind==='lease')f.set('Boot',1900n*NS);else f.advance(kind==='decision'?5n*NS:NS);return true;},deadlines:kind==='query'?[101n*NS]:[]};const p=f.run('check',options);p.catch(()=>{});f.deliver();await refused(f,p);});
model('synchronous_effect_cancels_no_success_retention',async()=>{const f=fixture();const p=f.client.run('cancel',Buffer.alloc(0),()=>f.client.cancel(Error('effect terminal')));p.catch(()=>{});f.deliver();await assert.rejects(p);assert.equal(f.records.some(r=>r.name==='GUARD_EXIT'&&r.fields.ok),false);});
model('capture_reply_failure_zero_effect',async()=>{const f=fixture({observe:name=>{if(name==='GUARD_RPC_REPLY')throw Error('short capture');}}),p=f.run();p.catch(()=>{});f.deliver();await refused(f,p);});
model('first_socket_fault_preserved_over_secondary',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});f.client.cancel(Error('incoming socket'));f.client.cancel(Error('secondary guard'));await refused(f,p);assert.match(f.client.state().firstFault,/incoming socket/);});
model('watchdog_every_tick_submitted_no_coalescing',async()=>{const f=fixture(),pending=Array.from({length:3},()=>f.run('watchdog:tick'));for(let i=0;i<3;i++){assert.equal(f.sent.length,i+1);f.deliver();await pending[i];}assert.equal(f.effects(),3);});
model('separate_helper_domains_refuse_cross_reply',async()=>{const f=fixture(),g=fixture({id:'4'}),a=f.run(),b=g.run();a.catch(()=>{});b.catch(()=>{});const r=f.reply();g.deliver(r);await refused(g,b);f.deliver();await a;});
model('normal_close_zero_pending_no_further_use',async()=>{const f=fixture(),p=f.run();f.deliver();await p;const close=f.client.close();f.deliver();await close;assert.equal(f.client.state().closed,true);await assert.rejects(f.run());});
model('close_with_pending_refused',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});assert.throws(()=>f.client.close());f.client.cancel(Error('test cleanup'));await assert.rejects(p);});
model('no_global_lock_held_across_network_wait',async()=>{const f=fixture(),a=f.run('publish-start');f.deliver();await a;let release;const network=new Promise(r=>release=r);const callback=f.run('response-callback');f.deliver();await callback;release('reply');assert.equal(await network,'reply');assert.equal(f.effects(),2);});
model('no_thenable_effect_accepted',async()=>{const f=fixture(),p=f.client.run('bad-async',Buffer.alloc(0),()=>Promise.resolve('bad'));p.catch(()=>{});f.deliver();await assert.rejects(p);assert.equal(f.records.some(r=>r.name==='GUARD_EXIT'&&r.fields.ok),false);});
model('phase_global_sequence_not_overridden',async()=>{const f=fixture(),p=f.run();f.deliver();await p;for(const row of f.records)assert.equal(Object.hasOwn(row.fields,'sequence'),false);assert(f.records.some(r=>Object.hasOwn(r.fields,'guardSequence')));});
for(const change of ['REQ_RECEIPT','CLOSE_RECEIPT','SOCKET_CLOSE','SUBSCRIPTION_GENERATION','STAGE_ATTEMPT','PUBLICATION_INVALIDATED'])model('actual_proxy_continuation_held_ok_'+change,async()=>{
 const f=fixture(),bytes=Buffer.from('actual-frame'),bufferHash=sha(bytes),connection={active:true,generation:1,appReceiptGeneration:1};
 const expectedGeneration={requestSequence:1,eoseSequence:2},expectedAttempt={epoch:1,stageId:'incoming-business'};
 let currentGeneration={...expectedGeneration},currentAttempt={...expectedAttempt},publicationInvalidated=false,sends=0;
 const valid=()=>proxyContinuationValid({connection,generation:1,appReceiptGeneration:1,bytes,bufferHash,sha,publicationInvalidated,currentGeneration,expectedGeneration,currentAttempt,expectedAttempt});
 const pending=f.client.run('proxy:before-app-send',bytes,()=>{sends++;},{valid});pending.catch(()=>{});const held=f.reply();
 if(change==='REQ_RECEIPT'||change==='CLOSE_RECEIPT')connection.appReceiptGeneration++;
 if(change==='SOCKET_CLOSE'){connection.active=false;connection.generation++;}
 if(change==='SUBSCRIPTION_GENERATION')currentGeneration={requestSequence:3,eoseSequence:4};
 if(change==='STAGE_ATTEMPT')currentAttempt={epoch:2,stageId:'incoming-ordinary-chat'};
 if(change==='PUBLICATION_INVALIDATED')publicationInvalidated=true;
 f.deliver(held);await assert.rejects(pending);assert.equal(sends,0);assert.equal(f.records.some(r=>r.name==='GUARD_EXIT'&&r.fields.ok),false);
});
model('actual_transport_framer_fragmented_valid_line',async()=>{const f=createGuardFramer(),raw=Buffer.from('{"x":"valid"}\n');assert.equal(f.accept(raw.subarray(0,3)),null);assert.equal(f.pendingBytes(),3);assert.deepEqual(f.accept(raw.subarray(3)),raw);f.end();});
model('actual_transport_framer_partial_eof_refused',async()=>{const f=createGuardFramer();f.accept(Buffer.from('{"x":"partial'));assert.throws(()=>f.end());});
model('actual_transport_framer_extra_lines_refused',async()=>{const f=createGuardFramer();assert.throws(()=>f.accept(Buffer.from('{}\n{}\n')));});
model('actual_transport_framer_fragment_aggregate_bound',async()=>{const f=createGuardFramer();f.accept(Buffer.alloc(2048,120));assert.throws(()=>f.accept(Buffer.from('x')));});
model('controller_watchdog_stop_drain_before_normal_close',async()=>{
 const f=fixture(),service=fixture({id:'4'});let intervalEnabled=true;
 const tick=()=>{if(!intervalEnabled)return null;return f.run('controller:watchdog');};
 const first=tick(),second=tick();intervalEnabled=false;assert.equal(tick(),null);
 const response=f.run('controller:response');for(const promise of [first,second,response]){f.deliver();await promise;}
 assert.equal(f.client.state().pending,0);const close=f.client.close();f.deliver();await close;
 const stillLive=service.run();service.deliver();await stillLive;assert.equal(service.client.state().closed,false);assert.equal(f.client.state().closed,true);
});
model('external_revocation_during_check_before_reply_consumption',async()=>{const f=fixture(),p=f.run();p.catch(()=>{});const held=f.reply();f.revokeExternal();f.deliver(held);await refused(f,p);});
model('external_revocation_from_valid_callback_before_effect',async()=>{const f=fixture(),p=f.run('revoke',{valid:()=>{f.revokeExternal();return true;}});p.catch(()=>{});f.deliver();await refused(f,p);});
model('nanosecond_decimal_clock_precision_above_JS_safe_integer',async()=>{const f=fixture(),exact=1793160000000000001n;f.lease.issuedUtcNs=exact-1000000000n;f.lease.deadlineUtcNs=exact+1800000000000n;f.set('Utc',exact);const p=f.run();const r=f.reply();assert.equal(r.clocks.Utc,'1793160000000000001');f.deliver(r);await p;const exit=f.records.find(r=>r.name==='GUARD_EXIT');assert.equal(exit.fields.consumedUtcUpperNs,'1793160000000000001');});
for(const badClock of [100000000000,'0100000000000','1e11','NaN'])model('noncanonical_reply_clock_'+String(badClock),async()=>{const f=fixture(),p=f.run();p.catch(()=>{});const r=f.reply();r.clocks.Utc=badClock;f.deliver(r);await refused(f,p);});
for(const change of ['APP_RECEIPT','SOCKET_CLOSE','PUBLICATION_INVALIDATION','STAGE','ATTEMPT','SUBSCRIPTION'])model('actual_flow_continuation_held_ok_'+change,async()=>{
 const f=fixture(),connection={active:true,appReceiptGeneration:1};let stageIndex=0,activeAttempt={epoch:1},publicationInvalidated=false,currentGenerationMatches=true,effects=0;
 const valid=()=>flowContinuationValid({stageIndex,expectedIndex:0,activeAttempt,expectedAttempt:{epoch:1},publish:true,publicationInvalidated,connection,expectedReceipt:1,currentGenerationMatches});
 const p=f.client.run('flow:original-06',Buffer.from('flow'),()=>{effects++;},{valid});p.catch(()=>{});const held=f.reply();
 if(change==='APP_RECEIPT')connection.appReceiptGeneration++;if(change==='SOCKET_CLOSE')connection.active=false;
 if(change==='PUBLICATION_INVALIDATION')publicationInvalidated=true;if(change==='STAGE')stageIndex=1;
 if(change==='ATTEMPT')activeAttempt={epoch:2};if(change==='SUBSCRIPTION')currentGenerationMatches=false;
 f.deliver(held);await assert.rejects(p);assert.equal(effects,0);
});
for(const [kind,quantum] of [['Utc',1000000n],['Boot',10000000n]])model('enqueue_lower_'+kind+'_quantum_does_not_extend_five_seconds',async()=>{
 const f=fixture({lowerUncertainty:{[kind]:quantum}}),p=f.run();p.catch(()=>{});const held=f.reply();f.advance(5000000000n-quantum);f.deliver(held);await refused(f,p);
});
for(const origin of ['APP','RELAY'])for(const mode of ['short-write','ENOSPC','exhausted-budget'])model('production_proxy_socket_fault_'+origin+'_'+mode,async()=>{
 let armed=false,primary=null,closed=false,cleanupCalls=0,observationSawFence=false;const events=[],signals=[],secondaryRows=[];
 const account=createByteAccount(262144,'socket-observation-test'),fsCalls=[];
 const fs={writeSync:(fd,bytes)=>{fsCalls.push({fd,bytes:bytes.length});if(armed&&mode==='ENOSPC')throw Error('ENOSPC');return armed&&mode==='short-write'?Math.max(0,bytes.length-1):bytes.length;}};
 const budget=createCaptureBudget({fs,streams:{phase:1,proxy:2},limit:262144,account});
 const phase=createPhaseWriter({fs:{writeSync:budget.writeSync},fd:1,clock:()=>100n*NS,utc:()=> 'SYNTHETIC'});
 const f=fixture({observe:(name,fields)=>phase(name,fields)});
 const inflight=f.run('inflight'),queued=f.run('queued');inflight.catch(()=>{});queued.catch(()=>{});const held=f.reply();
 const original=Error(origin+':ORIGINAL_SOCKET_FAULT');
 const boundary=createProxySocketErrorBoundary({
  claimFault:error=>{if(closed)return false;events.push('claim');closed=true;primary=error;f.client.cancel(error);return true;},
  observeFault:(error,context)=>{events.push('observe');observationSawFence=closed&&primary===original&&f.client.state().pending===0;budget.healthy();phase('PROXY_SOCKET_ERROR_CALLBACK_ENTRY',{origin:context.origin,error:String(error),terminalRetention:true});},
  cleanupFault:(error,secondary)=>{
   events.push('cleanup');cleanupCalls++;assert.equal(error,original);secondaryRows.push(...secondary);
   let now=100n*NS;const end=now+2000000000n,plan=cleanupPlan(now,end),child={kill:signal=>{signals.push(signal);return true;}};
   dispatchOwnedSignal({sample:()=>now,end,child,signal:plan.signal,record:()=>{throw Error('already failed proof capacity');}});
   assert(plan.escalationDelayMs<=1000);now=end;
   dispatchOwnedSignal({sample:()=>now,end,child,signal:'SIGKILL',record:()=>{throw Error('no late retained proof');}});
  }
 });
 if(mode==='exhausted-budget')account.charge(account.state().limit-account.state().chargedBytes);
 armed=true;boundary(original,{origin});
 await assert.rejects(inflight,error=>error===original);await assert.rejects(queued,error=>error===original);
 assert.equal(primary,original);assert(observationSawFence);assert.deepEqual(events,['claim','observe','cleanup']);
 assert.equal(cleanupCalls,1);assert.deepEqual(signals,['SIGTERM']);assert.equal(f.state().aborted,1);
 assert.equal(secondaryRows.length,1);assert.equal(secondaryRows[0].label,'socket-error-observation');assert.notEqual(secondaryRows[0].error,original);
 assert.equal(budget.state().poisoned,true);const retained=f.records.length;f.deliver(held);assert.equal(f.records.length,retained);
 assert.equal(f.records.some(row=>row.name==='GUARD_EXIT'&&row.fields.ok===true),false);
 boundary(Error('late secondary socket fault'),{origin});assert.equal(primary,original);assert.equal(cleanupCalls,1);
});
// Every definition below executes only when this file receives a separate grant.
for(const {name,fn} of definitions){try{await fn();}catch(error){throw Error('MODEL '+name+': '+String(error),{cause:error});}}
console.log(JSON.stringify({scope:'PRODUCER4_MOCK_FRESH_GUARD_SCHEDULER_ONLY',definitions:definitions.length,executed:definitions.length,realHelperExecuted:false,realClockOrSDKObserved:false,clientRowsQualified:0}));
