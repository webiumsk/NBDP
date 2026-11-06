// SOURCE definitions of the actual production stdout path; no real stdout/helper.
import assert from 'node:assert/strict';
import {createByteAccount,createAuditStaging,ALLOCATION} from './capture-allocation.mjs';
import {createControllerStdoutEmitter} from './capture-budget.mjs';
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
for(const {name,fn} of cases)try{fn();}catch(error){throw Error('CONTROLLER_EMISSION_MODEL '+name+': '+String(error),{cause:error});}
console.log(JSON.stringify({scope:'ACTUAL_PRODUCTION_CONTROLLER_EMITTER_WITH_FAKE_WRITER_ONLY',checks:cases.length,realHelperExecuted:false,realStdoutWritten:false,clientRowsQualified:0}));
