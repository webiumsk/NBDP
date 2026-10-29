// SOURCE definitions only; this file has not been imported or executed in preparation.
// Every child/event/clock/observer operand below is memory-only. No real helper or timer.
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {createCaptureBudget} from './capture-budget.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
import {createByteAccount,ALLOCATION} from './capture-allocation.mjs';
import {cleanupPlan,dispatchOwnedSignal,terminalValid,registerHelperTerminalCallbacks} from './guard-transport-boundaries.mjs';
export const definitions=[];
const model=(name,fn)=>definitions.push({name,fn});
const NS=1000000000n;
function fixture({now=0n,end=2n*NS,recorder=null}={}){
 const signals=[],records=[],trace=[];let at=now;
 const child={kill(signal){assert.equal(this,child);trace.push('kill:'+signal);signals.push(signal);return true;}};
 const record=(name,fields)=>{trace.push('record:'+name);records.push({name,fields});if(recorder)recorder(name,fields);};
 return {child,signals,records,trace,end,sample:()=>{trace.push('sample');return at;},set:value=>{at=value;},dispatch:signal=>dispatchOwnedSignal({sample:()=>{trace.push('sample');return at;},end,child,record,signal}),record};
}
const natural=()=>({ended:true,code:0,signal:null,stdoutEOF:true,stderrEOF:true,exitSeen:true});

model('cleanup_exhausted_zero_or_negative_has_no_signal_or_timer',()=>{
 for(const now of [10n,11n])assert.deepEqual(cleanupPlan(now,10n),{signal:null,escalationDelayMs:null});
});
model('cleanup_remaining_one_ns_or_one_second_uses_kill',()=>{
 for(const left of [1n,NS])assert.deepEqual(cleanupPlan(100n,100n+left),{signal:'SIGKILL',escalationDelayMs:null});
});
model('cleanup_one_second_plus_one_ns_uses_term_inside_original_end',()=>{
 const end=NS+1n,plan=cleanupPlan(0n,end);assert.deepEqual(plan,{signal:'SIGTERM',escalationDelayMs:1000});assert(BigInt(plan.escalationDelayMs)*1000000n<end);
});
model('cleanup_long_budget_delay_capped_without_bigint_precision_loss',()=>{
 for(const end of [2n*NS,10n**100n]){const plan=cleanupPlan(0n,end);assert.equal(plan.escalationDelayMs,1000);assert(BigInt(plan.escalationDelayMs)*1000000n<end);}
});
model('cleanup_clock_type_refuses_floating_or_numeric_milliseconds',()=>{
 for(const pair of [[0,1n],[0n,1],[0.1,1n]])assert.throws(()=>cleanupPlan(...pair),/BIGINT_REQUIRED/);
});
model('expired_owned_signal_records_host_cleanup_without_child_call',()=>{
 for(const now of [NS,NS+1n]){const f=fixture({now,end:NS});assert.equal(f.dispatch('SIGKILL'),false);assert.deepEqual(f.signals,[]);assert.deepEqual(f.records,[{name:'GUARD_HELPER_CLEANUP_DEADLINE_EXHAUSTED',fields:{action:'NO_LATE_SIGNAL',hostOwnedCleanupRequired:true}}]);}
});
model('live_owned_signal_samples_immediately_before_exact_child_kill',()=>{
 for(const signal of ['SIGTERM','SIGKILL']){const f=fixture({now:NS-1n,end:NS});assert.equal(f.dispatch(signal),true);assert.deepEqual(f.signals,[signal]);assert.deepEqual(f.trace,['sample','kill:'+signal,'record:GUARD_HELPER_TERMINATE']);}
});
model('held_initial_dispatch_cannot_reuse_earlier_cleanup_plan',()=>{
 const f=fixture({end:2n*NS}),plan=cleanupPlan(0n,f.end);f.set(f.end);assert.equal(f.dispatch(plan.signal),false);assert.deepEqual(f.signals,[]);
});
model('held_escalation_timer_refuses_signal_at_original_deadline',()=>{
 const f=fixture({end:2n*NS}),plan=cleanupPlan(0n,f.end);assert.equal(f.dispatch(plan.signal),true);
 const heldTimer=()=>f.dispatch('SIGKILL');assert.equal(plan.escalationDelayMs,1000);f.set(f.end);assert.equal(heldTimer(),false);assert.deepEqual(f.signals,['SIGTERM']);
 assert.equal(f.records.at(-1).fields.hostOwnedCleanupRequired,true);
});
model('kill_one_ns_before_end_allowed_but_late_followup_refused',()=>{
 const f=fixture({now:NS-1n,end:NS});assert.equal(f.dispatch(cleanupPlan(NS-1n,NS).signal),true);f.set(NS+1n);assert.equal(f.dispatch('SIGKILL'),false);assert.deepEqual(f.signals,['SIGKILL']);
});
model('unknown_signal_refused_without_clock_or_child_pid_mutation',()=>{
 const f=fixture();for(const signal of ['SIGUSR1','SIGSTOP',null,9])assert.throws(()=>f.dispatch(signal),/NOT_ALLOWED/);assert.deepEqual(f.trace,[]);assert.deepEqual(f.signals,[]);
});
model('signal_record_poison_returns_false_without_event_throw_or_success',()=>{
 const poison=Error('CAPTURE_POISON'),f=fixture({recorder:()=>{throw poison;}});let result;
 assert.doesNotThrow(()=>{result=f.dispatch('SIGTERM');});assert.equal(result,false);assert.deepEqual(f.signals,['SIGTERM']);
});
model('expired_deadline_record_poison_never_escapes_or_signals',()=>{
 const f=fixture({now:1n,end:1n,recorder:()=>{throw Error('CAPTURE_POISON');}});assert.doesNotThrow(()=>assert.equal(f.dispatch('SIGKILL'),false));assert.deepEqual(f.signals,[]);
});
model('owned_child_signal_false_or_throw_cannot_report_success',()=>{
 for(const throwing of [false,true]){const f=fixture();f.child.kill=()=>{if(throwing)throw Error('OWNED_CHILD_SIGNAL_ERROR');return false;};assert.equal(f.dispatch('SIGKILL'),false);}
});
// Actual registered helper handlers and actual budget/phase writer. Only the
// child/streams/fs/clock callbacks are fakes; no copied handler implementation.
function helperFixture({sink='healthy',original=null,framerError=null,ended=false}={}){
 const child=new EventEmitter();child.stdout=new EventEmitter();child.stderr=new EventEmitter();child.stdin=new EventEmitter();
 const state={ended,stdoutEOF:false,stderrEOF:false,exitSeen:false,closeSeen:false,secondaryErrors:[]},trace=[],records=[],writes=[],notified=[];
 let first=original,closeCalls=0,framerEnds=0;
 const account=createByteAccount(ALLOCATION.service-ALLOCATION.serviceHeader-ALLOCATION.serviceDiagnostics,'helper-retention');if(sink==='exhausted')account.charge(account.state().limit);
 const fs={writeSync:(fd,raw)=>{trace.push('write');writes.push({fd,bytes:raw.length});if(sink==='ENOSPC')throw Error('MODEL_ENOSPC');return sink==='short'?raw.length-1:raw.length;}};
 const budget=createCaptureBudget({fs,streams:{phase:1,proxy:2},limit:account.state().limit,account});
 const phase=createPhaseWriter({fs:{writeSync:budget.writeSync},fd:1,clock:()=>1n,utc:()=> '2026-10-28T00:00:00.000Z',limit:account.state().limit});
 const bad=error=>{trace.push('bad:'+error.message);notified.push(error);if(first===null)first=error;};
 const record=(name,fields)=>{trace.push('record:'+name);records.push({name,fields});const row=phase(name,fields);budget.healthy();return row;};
 const framer={end(){trace.push('framer.end');framerEnds++;if(framerError)throw framerError;}};
 registerHelperTerminalCallbacks({child,state,record,bad,framer,onClose:(code,signal)=>{trace.push('onClose');closeCalls++;assert.equal(typeof code==='number'||code===null,true);assert.equal(signal===null||typeof signal==='string',true);}});
 const emit={stderr:()=>child.stderr.emit('data',Buffer.from('actual fake-child stderr')),stdoutEOF:()=>child.stdout.emit('end'),exit:()=>child.emit('exit',2,null),close:()=>child.emit('close',2,null)};
 return {child,state,trace,records,writes,budget,phase,account,notified,emit,first:()=>first,closeCalls:()=>closeCalls,framerEnds:()=>framerEnds};
}
function helperFailureCase(event,sink){
 const f=helperFixture({sink}),expected={stderr:['GUARD_HELPER_STDERR','helper-stderr-retention','GUARD_HELPER_STDERR'],stdoutEOF:['UNEXPECTED_GUARD_STDOUT_EOF','helper-stdout-eof-retention','GUARD_HELPER_STDOUT_EOF'],exit:['GUARD_HELPER_UNEXPECTED_EXIT','helper-exit-retention','GUARD_HELPER_EXIT'],close:['GUARD_HELPER_LIFECYCLE_NEGATIVE','helper-close-retention','GUARD_HELPER_CLOSE']}[event];
 assert.doesNotThrow(f.emit[event]);assert.equal(f.first().message,expected[0]);assert.equal(f.trace[0],'bad:'+expected[0]);assert.equal(f.records[0].name,expected[2]);assert(f.trace.indexOf('bad:'+expected[0])<f.trace.indexOf('record:'+expected[2]));
 assert.equal(f.state.secondaryErrors.length,1);assert.deepEqual(Object.keys(f.state.secondaryErrors[0]).sort(),['error','label']);assert.equal(f.state.secondaryErrors[0].label,expected[1]);assert(f.state.secondaryErrors[0].error.includes(sink==='short'?'SHORT_PHASE_WRITE':sink==='ENOSPC'?'MODEL_ENOSPC':'CAPTURE_ALLOCATION_EXCEEDED'));
 assert.equal(f.notified.length,2);assert.equal(f.notified[0],f.first());assert.equal(f.budget.state().poisoned,true);assert.equal(f.phase.state().poisoned,true);assert.equal(f.writes.length,sink==='exhausted'?0:1);
 assert.equal(f.state.stdoutEOF,event==='stdoutEOF');assert.equal(f.state.exitSeen,event==='exit');assert.equal(f.state.closeSeen,event==='close');assert.equal(f.framerEnds(),event==='stdoutEOF'?1:0);
 if(event==='stderr')assert.equal(Buffer.from(f.records[0].fields.rawBase64,'base64').toString(),'actual fake-child stderr');
 if(event==='exit')assert.deepEqual(f.records[0].fields,{code:2,signal:null});
 if(event==='close')assert.deepEqual(f.records[0].fields,{code:2,signal:null,stdoutEOF:false,stderrEOF:false,exitSeen:false});
 const original=f.first();if(event!=='close')assert.doesNotThrow(()=>f.child.emit('close',2,null));assert.equal(f.closeCalls(),1);assert.equal(f.first(),original);assert.equal(f.trace.at(-1),'onClose');assert.equal(f.writes.length,sink==='exhausted'?0:1);
}
model('registered_stderr_short_retention_original_then_secondary',()=>helperFailureCase('stderr','short'));
model('registered_stderr_enospc_retention_original_then_secondary',()=>helperFailureCase('stderr','ENOSPC'));
model('registered_stderr_exhausted_retention_original_then_secondary',()=>helperFailureCase('stderr','exhausted'));
model('registered_natural_helper_close_all_events_and_flags_actual_path',()=>{
 const f=helperFixture({ended:true});assert.equal(f.child.listenerCount('close'),1);assert.equal(f.child.stdout.listenerCount('end'),1);f.child.stdout.emit('end');f.child.stderr.emit('end');f.child.emit('exit',0,null);f.child.emit('close',0,null);
 assert.equal(f.first(),null);assert.deepEqual(f.records.map(row=>row.name),['GUARD_HELPER_STDOUT_EOF','GUARD_HELPER_STDERR_EOF','GUARD_HELPER_EXIT','GUARD_HELPER_CLOSE']);assert.equal(f.writes.length,4);assert.equal(f.framerEnds(),1);assert.equal(f.closeCalls(),1);assert.equal(terminalValid({...f.state,code:0,signal:null}),true);
});
model('registered_close_rejects_unexpected_or_missing_lifecycle_events',()=>{
 for(const change of [{ended:false},{stdoutEOF:false},{stderrEOF:false},{exitSeen:false},{code:1},{signal:'SIGTERM'},{code:null}]){const f=helperFixture({ended:true});Object.assign(f.state,{stdoutEOF:true,stderrEOF:true,exitSeen:true},change);assert.doesNotThrow(()=>f.child.emit('close',Object.hasOwn(change,'code')?change.code:0,Object.hasOwn(change,'signal')?change.signal:null));assert.equal(f.first().message,'GUARD_HELPER_LIFECYCLE_NEGATIVE');assert.equal(f.closeCalls(),1);assert.equal(f.state.closeSeen,true);}
});
model('registered_controller_close_cannot_establish_separate_helper_events',()=>{
 const controller=helperFixture({ended:true}),service=helperFixture();controller.child.stdout.emit('end');controller.child.stderr.emit('end');controller.child.emit('exit',0,null);controller.child.emit('close',0,null);
 assert.equal(controller.first(),null);assert.equal(controller.closeCalls(),1);assert.equal(service.state.ended,false);assert.equal(service.state.stdoutEOF,false);assert.equal(service.state.exitSeen,false);assert.equal(service.closeCalls(),0);
 service.child.emit('close',0,null);assert.equal(service.first().message,'GUARD_HELPER_LIFECYCLE_NEGATIVE');assert.equal(controller.first(),null);
});
model('registered_stdout_eof_short_retention_original_then_secondary',()=>helperFailureCase('stdoutEOF','short'));
model('registered_stdout_eof_enospc_retention_original_then_secondary',()=>helperFailureCase('stdoutEOF','ENOSPC'));
model('registered_stdout_eof_exhausted_retention_original_then_secondary',()=>helperFailureCase('stdoutEOF','exhausted'));
model('registered_exit_short_retention_original_then_secondary',()=>helperFailureCase('exit','short'));
model('registered_exit_enospc_retention_original_then_secondary',()=>helperFailureCase('exit','ENOSPC'));
model('registered_exit_exhausted_retention_original_then_secondary',()=>helperFailureCase('exit','exhausted'));
model('registered_close_short_retention_original_then_secondary',()=>helperFailureCase('close','short'));
model('registered_close_enospc_retention_original_then_secondary',()=>helperFailureCase('close','ENOSPC'));
model('registered_close_exhausted_retention_original_then_secondary',()=>helperFailureCase('close','exhausted'));
model('registered_child_and_stdin_error_deliver_exact_original_without_observation',()=>{
 for(const source of ['child','stdin']){const f=helperFixture(),original=Error('ORIGINAL_'+source);assert.doesNotThrow(()=>source==='child'?f.child.emit('error',original):f.child.stdin.emit('error',original));assert.equal(f.first(),original);assert.equal(f.records.length,0);assert.equal(f.writes.length,0);assert.equal(f.state.secondaryErrors.length,0);}
});
model('registered_stderr_eof_observation_failure_is_primary_not_fake_known_death',()=>{
 const f=helperFixture({sink:'ENOSPC'});assert.doesNotThrow(()=>f.child.stderr.emit('end'));assert.equal(f.state.stderrEOF,true);assert.equal(f.first().message,'MODEL_ENOSPC');assert.equal(f.records[0].name,'GUARD_HELPER_STDERR_EOF');assert.equal(f.state.secondaryErrors.length,0);assert.equal(f.writes.length,1);
});
model('registered_stdout_framer_failure_distinguishes_unexpected_eof_from_closed_owner',()=>{
 for(const ended of [false,true]){const framing=Error('ORIGINAL_FRAMER_FAILURE'),f=helperFixture({ended,framerError:framing});assert.doesNotThrow(()=>f.child.stdout.emit('end'));assert.equal(f.framerEnds(),1);assert.equal(f.records.length,0);assert.equal(f.writes.length,0);assert.equal(f.first().message,ended?'ORIGINAL_FRAMER_FAILURE':'UNEXPECTED_GUARD_STDOUT_EOF');assert.equal(f.state.secondaryErrors.length,ended?0:1);if(!ended)assert.equal(f.state.secondaryErrors[0].label,'helper-stdout-eof-retention');}
});
model('registered_repeated_retention_poison_bounded_secondaries_no_repair',()=>{
 const f=helperFixture({sink:'ENOSPC'});for(let i=0;i<65;i++)assert.doesNotThrow(f.emit.stderr);assert.equal(f.state.secondaryErrors.length,64);assert.equal(f.first().message,'GUARD_HELPER_STDERR');assert.equal(f.writes.length,1);for(const row of f.state.secondaryErrors){assert.deepEqual(Object.keys(row).sort(),['error','label']);assert.equal(row.label,'helper-stderr-retention');assert(row.label.length<=128&&row.error.length<=2048);}
});

// A separate actual grant is required before invoking this file. Syntax --check
// does not run this loop and establishes no helper/model/runtime evidence.
for(const {name,fn} of definitions){try{await fn();}catch(error){throw Error('MODEL '+name+': '+String(error),{cause:error});}}
console.log(JSON.stringify({scope:'PRODUCER4_ACTUAL_REGISTERED_HELPER_CALLBACKS_AND_OWNED_SIGNAL_MOCKS_ONLY',definitions:definitions.length,executed:definitions.length,realHelperExecuted:false,realTimerObserved:false,processReapAttested:false,clientRowsQualified:0}));
