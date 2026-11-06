// SOURCE definitions only; this file has not been imported or executed in preparation.
// Every child/event/clock/observer operand below is memory-only. No real helper or timer.
import assert from 'node:assert/strict';
import {cleanupPlan,dispatchOwnedSignal,observeStderr,terminalValid} from './guard-transport-boundaries.mjs';
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
model('stderr_claims_terminal_fault_before_bounded_retention',()=>{
 const rows=[],faults=[],order=[];assert.equal(observeStderr({record:(name,fields)=>{order.push('record');rows.push({name,fields});},bad:error=>{order.push('claim');faults.push(error);},chunk:Buffer.alloc(4096,65)}),false);
 assert.deepEqual(order,['claim','record']);assert.equal(rows[0].name,'GUARD_HELPER_STDERR');assert.equal(Buffer.from(rows[0].fields.rawBase64,'base64').length,2048);assert.equal(faults.length,1);assert.equal(faults[0].message,'GUARD_HELPER_STDERR');
});
model('stderr_record_poison_routes_first_fault_without_uncaught_event_throw',()=>{
 const poison=Error('CAPTURE_POISON'),primary=Error('ORIGINAL_SOCKET_FAULT');let first=primary;const observed=[];
 assert.doesNotThrow(()=>observeStderr({record:()=>{throw poison;},bad:error=>{observed.push(error);if(first===null)first=error;},chunk:Buffer.from('stderr')}));
 assert.equal(first,primary);assert.equal(observed.length,2);assert.equal(observed[0].message,'GUARD_HELPER_STDERR');assert.equal(observed[1],poison);
});
model('stderr_fatal_observer_throw_also_stays_inside_event_boundary',()=>{
 assert.doesNotThrow(()=>observeStderr({record:()=>{},bad:()=>{throw Error('FATAL_OBSERVER_POISON');},chunk:Buffer.from('stderr')}));
 const poison={toString(){throw Error('POISON_STRINGIFICATION');}};let reported=null;assert.doesNotThrow(()=>observeStderr({record:()=>{throw poison;},bad:error=>{reported=error;},chunk:Buffer.from('stderr')}));assert(reported instanceof Error);assert.equal(reported.cause,poison);
});
model('natural_close_requires_end_zero_null_signal_both_eof_and_exit',()=>{
 assert.equal(terminalValid(natural()),true);
});
model('unexpected_eof_exit_signal_death_or_missing_event_refuses_terminal',()=>{
 for(const change of [{ended:false},{code:1},{code:null},{signal:'SIGTERM'},{signal:undefined},{stdoutEOF:false},{stderrEOF:false},{exitSeen:false},{ended:1},{code:'0'}])assert.equal(terminalValid({...natural(),...change}),false);
});
model('controller_normal_close_does_not_establish_separate_helper_terminal',()=>{
 const controller=natural(),helper={ended:false,code:null,signal:null,stdoutEOF:false,stderrEOF:false,exitSeen:false};
 assert.equal(terminalValid(controller),true);assert.equal(terminalValid(helper),false);
 Object.assign(helper,natural());assert.equal(terminalValid(helper),true);controller.code=2;assert.equal(terminalValid(helper),true);assert.equal(terminalValid(controller),false);
});

// A separate actual grant is required before invoking this file. Syntax --check
// does not run this loop and establishes no helper/model/runtime evidence.
for(const {name,fn} of definitions){try{await fn();}catch(error){throw Error('MODEL '+name+': '+String(error),{cause:error});}}
console.log(JSON.stringify({scope:'PRODUCER4_MOCK_GUARD_TRANSPORT_BOUNDARIES_ONLY',definitions:definitions.length,executed:definitions.length,realHelperExecuted:false,realTimerObserved:false,processReapAttested:false,clientRowsQualified:0}));
