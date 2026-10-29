// SOURCE definitions of the actual production stdout path; no real stdout/helper.
import assert from 'node:assert/strict';
import {createByteAccount,createAuditStaging,ALLOCATION} from './capture-allocation.mjs';
import {createControllerStdoutEmitter,createCaptureBudget,captureAccountState,validateFinalObserverRecord,emitFinalObserverRecord} from './capture-budget.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
const cases=[];function model(name,fn){cases.push({name,fn});}
function fixture({write}={}){
 const account=createByteAccount(ALLOCATION.proof,'controller-proof'),faults=[],writes=[];
 const metadata={schema:'e02-controller-guard-audit-v1',reservationIndex:1,instance:'1'.repeat(32),scope:'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',runId:'2'.repeat(32),leaseSha256:'3'.repeat(64),configurationSha256:'4'.repeat(64)};
 const audit=createAuditStaging({account,metadata});audit.append('GUARD_HELPER_CLOSE',{code:0,signal:null,stdoutEOF:true,stderrEOF:true,exitSeen:true});
 const encodedAudit=audit.emit();let callback;
 const emit=createControllerStdoutEmitter({responseEncoding:'{"ok":true,"result":{"fixed":"synthetic"}}',encodedAudit,write:(bytes,cb)=>{writes.push(Buffer.from(bytes));callback=cb;return write?write(bytes,cb):false;},isHealthy:()=>faults.length===0,onFault:error=>{account.poison(error);faults.push(error);}});
 return {account,audit,encodedAudit,emit,writes,faults,callback:()=>callback};
}
model('actual_production_stdout_single_immutable_precharged_emission',()=>{const f=fixture(),record=f.emit();assert.equal(f.writes.length,1);const raw=f.writes[0];assert.equal(raw.at(-1),10);const parsed=JSON.parse(raw);assert.equal(parsed.guardController.reservationIndex,1);assert.equal(parsed.guardController.observations[0].name,'GUARD_HELPER_CLOSE');assert.equal(record.physicalBytes,null);assert.equal(record.intendedBytes,raw.length);assert.equal(f.faults.length,0);assert(Buffer.byteLength(',"guardController":'+f.encodedAudit+'}\n')<=f.account.state().chargedBytes);});
model('actual_duplicate_stdout_emission_poison_no_second_write',()=>{const f=fixture();f.emit();assert.throws(()=>f.emit(),/ALREADY_EMITTED/);assert.equal(f.writes.length,1);assert.equal(f.faults.length,1);});
model('actual_sync_stdout_failure_sticky_original_no_retry',()=>{const original=Error('one intended failed write'),f=fixture({write:()=>{throw original;}});assert.throws(()=>f.emit(),e=>e===original);assert.throws(()=>f.emit(),e=>e===original);assert.equal(f.writes.length,1);assert(f.faults.every(error=>error===original));assert.equal(f.account.state().firstError,original);});
model('actual_async_stdout_failure_no_later_emission',()=>{const f=fixture();f.emit();const original=Error('actual pipe error');f.callback()(original);assert.throws(()=>f.emit(),e=>e===original);assert.equal(f.writes.length,1);assert.equal(f.faults[0],original);});
model('actual_false_write_boolean_is_not_partial_byte_attestation',()=>{const f=fixture({write:()=>false}),result=f.emit();assert.equal(f.writes.length,1);assert.equal(result.physicalBytes,null);assert.equal(f.faults.length,0);});
model('actual_unhealthy_owner_never_writes_stdout_success',()=>{const writes=[],faults=[],account=createByteAccount(ALLOCATION.proof,'failed-controller');const emit=createControllerStdoutEmitter({responseEncoding:'{"ok":true}',encodedAudit:'{}',write:bytes=>writes.push(bytes),isHealthy:()=>false,onFault:error=>{account.poison(error);faults.push(error);}});assert.throws(emit);assert.equal(writes.length,0);assert.equal(faults.length,1);});
model('actual_invalid_or_oversize_encoding_zero_writes',()=>{for(const encodedAudit of [null,'x'.repeat(ALLOCATION.proof)]){const writes=[],faults=[],account=createByteAccount(ALLOCATION.proof,'failed-controller');const emit=createControllerStdoutEmitter({responseEncoding:'{"ok":true}',encodedAudit,write:bytes=>writes.push(bytes),isHealthy:()=>true,onFault:error=>{account.poison(error);faults.push(error);}});assert.throws(emit);assert.equal(writes.length,0);assert.equal(faults.length,1);}});
model('actual_truncated_capture_cannot_be_valid_complete_reply',()=>{const f=fixture();f.emit();const raw=f.writes[0];assert.throws(()=>JSON.parse(raw.subarray(0,raw.length-2)));assert.equal(JSON.parse(raw).guardController.observations.length,1);});
// Actual production final-envelope emitter/extractor, fake writer and clock only.
function finalObserverFixture(){
 const proof=createByteAccount(ALLOCATION.service-ALLOCATION.serviceHeader-ALLOCATION.serviceDiagnostics,'final-observer-proof'),diagnostics=createByteAccount(ALLOCATION.serviceDiagnostics,'final-observer-diagnostics');
 const fs={writeSync:(_fd,raw)=>raw.length},budget=createCaptureBudget({fs,streams:{proxy:1,phase:2},limit:proof.state().limit,account:proof});
 const phase=createPhaseWriter({fs:{writeSync:budget.writeSync},fd:2,clock:()=>1n,utc:()=> '2026-10-28T00:00:00.000Z',limit:proof.state().limit});
 const observer={schema:'e02-minimum-observer-state-v3',budget:budget.state(),phase:phase.state(),allocation:ALLOCATION,serviceDiagnostics:captureAccountState(diagnostics),serviceHeaderPrepaidBytes:4096};
 const writes=[],put=(name,value)=>{writes.push({name,raw:JSON.stringify(value)});return 'MODEL_PIN_RESULT';};
 return {observer,writes,put};
}
const fatalRecord=observer=>({observer,snapshotTiming:'BEFORE_THIS_FINAL_RECORD_WRITE',error:'ORIGINAL_MODEL_FAULT',secondaryErrors:[{label:'cleanup',error:'MODEL_SECONDARY'}]});
const normalRecord=observer=>({observer,snapshotTiming:'BEFORE_THIS_FINAL_RECORD_WRITE',error:null,secondaryErrors:[],normalOwnedHelperClose:true});
model('actual_final_observer_normal_emit_extract_literal_flag_one_put',()=>{
 const f=finalObserverFixture();assert.equal(emitFinalObserverRecord({kind:'normal',observer:f.observer,error:null,secondaryErrors:[],put:f.put}),'MODEL_PIN_RESULT');assert.equal(f.writes.length,1);assert.equal(f.writes[0].name,'observer-final-state.json');
 const extracted=validateFinalObserverRecord(JSON.parse(f.writes[0].raw));assert.equal(extracted.normalOwnedHelperClose,true);assert.equal(extracted.error,null);assert.deepEqual(extracted.secondaryErrors,[]);assert.equal(extracted.snapshotTiming,'BEFORE_THIS_FINAL_RECORD_WRITE');assert.deepEqual(extracted.observer,f.observer);
});
model('actual_final_observer_fatal_emit_extract_no_normal_claim',()=>{
 const f=finalObserverFixture(),secondary=[{label:'owned-cleanup',error:'MODEL_SECONDARY'}];f.observer.budget.poisoned=true;f.observer.budget.firstError='MODEL_CAPTURE_POISON';
 emitFinalObserverRecord({kind:'fatal',observer:f.observer,error:'ORIGINAL_MODEL_FAULT',secondaryErrors:secondary,put:f.put});assert.equal(f.writes.length,1);const extracted=validateFinalObserverRecord(JSON.parse(f.writes[0].raw));assert.equal(Object.hasOwn(extracted,'normalOwnedHelperClose'),false);assert.equal(extracted.error,'ORIGINAL_MODEL_FAULT');assert.deepEqual(extracted.secondaryErrors,secondary);assert.equal(extracted.observer.budget.poisoned,true); // Retained negative, not qualification.
});
model('actual_final_observer_normal_extras_false_or_missing_flag_refused',()=>{
 const f=finalObserverFixture(),normal=normalRecord(f.observer);
 for(const change of [{extra:true},{normalOwnedHelperClose:false},{normalOwnedHelperClose:1},{normalOwnedHelperClose:'true'},{error:'FATAL_DISGUISED'},{secondaryErrors:[{label:'bad',error:'bad'}]}])assert.throws(()=>validateFinalObserverRecord({...normal,...change}));
 const missing={...normal};delete missing.normalOwnedHelperClose;assert.throws(()=>validateFinalObserverRecord(missing));
});
model('actual_final_observer_fatal_cannot_forge_normal_flag_or_error_domain',()=>{
 const f=finalObserverFixture(),fatal=fatalRecord(f.observer);
 for(const flag of [true,false,null,undefined])assert.throws(()=>validateFinalObserverRecord({...fatal,normalOwnedHelperClose:flag}));
 for(const error of ['',null,0,{},Error('not serialized')])assert.throws(()=>validateFinalObserverRecord({...fatal,error}));
});
model('actual_final_observer_snapshot_and_secondary_closed_types_refused',()=>{
 const f=finalObserverFixture(),fatal=fatalRecord(f.observer);
 for(const snapshotTiming of ['AFTER_FINAL_WRITE',null,0])assert.throws(()=>validateFinalObserverRecord({...fatal,snapshotTiming}));
 for(const secondaryErrors of [null,'bad',{},[null],[{label:'cleanup'}],[{label:'cleanup',error:1}],[{label:'cleanup',error:'bad',extra:true}]])assert.throws(()=>validateFinalObserverRecord({...fatal,secondaryErrors}));
});
model('actual_final_observer_current_six_keys_and_schema_no_generic_relaxation',()=>{
 const f=finalObserverFixture(),normal=normalRecord(f.observer);
 for(const change of [{schema:'e02-minimum-observer-state-v2'},{extra:true},{budget:null},{phase:[]},{allocation:'bad'},{serviceDiagnostics:0},{serviceHeaderPrepaidBytes:0}])assert.throws(()=>validateFinalObserverRecord({...normal,observer:{...f.observer,...change}}));
 const missing={...f.observer};delete missing.budget;assert.throws(()=>validateFinalObserverRecord({...normal,observer:missing}));
 for(const observer of [null,[],'opaque'])assert.throws(()=>validateFinalObserverRecord({...normal,observer}));
});
model('actual_final_observer_invalid_builder_inputs_never_reach_put',()=>{
 for(const change of [{kind:'unknown'},{kind:'normal',error:'FATAL_DISGUISED'},{kind:'normal',secondaryErrors:[{label:'cleanup',error:'failure'}]},{kind:'fatal',error:Error('not serialized')},{kind:'fatal',error:''}]){
  const f=finalObserverFixture();assert.throws(()=>emitFinalObserverRecord({kind:'normal',observer:f.observer,error:null,secondaryErrors:[],put:f.put,...change}));assert.equal(f.writes.length,0);
 }
});
model('actual_final_observer_put_failure_once_no_retry_or_replacement',()=>{
 for(const kind of ['normal','fatal']){const f=finalObserverFixture(),original=Error('MODEL_FINAL_WRITE_FAILURE');let calls=0;
  assert.throws(()=>emitFinalObserverRecord({kind,observer:f.observer,error:kind==='normal'?null:'ORIGINAL_MODEL_FAULT',secondaryErrors:[],put:(name,value)=>{calls++;assert.equal(name,'observer-final-state.json');validateFinalObserverRecord(value);throw original;}}),error=>error===original);assert.equal(calls,1);
 }
});
for(const {name,fn} of cases)try{fn();}catch(error){throw Error('CONTROLLER_EMISSION_MODEL '+name+': '+String(error),{cause:error});}
console.log(JSON.stringify({scope:'ACTUAL_PRODUCTION_CONTROLLER_EMITTER_WITH_FAKE_WRITER_ONLY',checks:cases.length,realHelperExecuted:false,realStdoutWritten:false,clientRowsQualified:0}));
