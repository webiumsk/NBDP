// SOURCE definitions only. No helper/fs/clock/stdio/model ran in preparation.
// Parent-ledger/write cases are memory models using the actual accounting utility;
// they do not establish real mount, parent writer, whole-consumer or lifecycle DATA.
import assert from 'node:assert/strict';
import {ALLOCATION as A,createByteAccount,createAuditStaging} from './capture-allocation.mjs';
import {writeExclusiveProof} from './capture-budget.mjs';
export const definitions=[];
const model=(name,fn)=>definitions.push({name,fn});
const metadata=(reservationIndex=1)=>({schema:'e02-controller-guard-audit-v1',reservationIndex,instance:'a'.repeat(32),scope:'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',runId:'b'.repeat(32),leaseSha256:'c'.repeat(64),configurationSha256:'d'.repeat(64)});
const bytes=value=>Buffer.byteLength(typeof value==='string'?value:JSON.stringify(value));
const contribution=value=>bytes(',"guardController":'+value+'}\n');
const staging=(cap=A.proof,index=1)=>{const account=createByteAccount(cap,'proof');return {account,stage:createAuditStaging({account,metadata:metadata(index)})};};

model('exact_frozen_allocation_and_wrapper_inside_proof',()=>{
 assert.deepEqual(A,{total:16777216,service:8388608,serviceHeader:4096,serviceDiagnostics:4096,controllerSlots:64,slot:131072,proof:122880,ledger:4096,diagnostics:4096,wrapper:1024});assert(Object.isFrozen(A));
 assert.equal(A.service+A.controllerSlots*A.slot,A.total);assert.equal(A.proof+A.ledger+A.diagnostics,A.slot);assert.equal(A.service-A.serviceHeader-A.serviceDiagnostics,8380416);
});
model('controller_proof_below_equal_above_exact_encoded_limit',()=>{
 const base=bytes({name:'x',fields:{payload:''}}),room=A.proof-A.wrapper-base;
 for(const delta of [-1,0,1]){const f=staging();const append=()=>f.stage.append('x',{payload:'x'.repeat(room+delta)});if(delta>0){assert.throws(append);assert.equal(f.account.state().chargedBytes,A.wrapper);assert.equal(f.account.state().intendedBytes,A.proof+1);}else{append();assert.equal(f.account.state().chargedBytes,A.proof+delta);assert(contribution(f.stage.emit())<=A.proof);}}
});
model('service_share_headers_diagnostics_and_proof_below_equal_above',()=>{
 for(const delta of [-1,0,1]){const service=createByteAccount(A.service,'service');service.charge(A.serviceHeader);service.charge(A.serviceDiagnostics);const write=()=>service.charge(A.service-A.serviceHeader-A.serviceDiagnostics+delta);if(delta>0){assert.throws(write);assert.equal(service.state().chargedBytes,8192);assert.equal(service.state().intendedBytes,A.service+1);}else{write();assert.equal(service.state().chargedBytes,A.service+delta);}}
});
model('combined_owners_exact_16mib_no_one_byte_extension',()=>{
 const global=createByteAccount(A.total,'global');global.charge(A.service);for(let i=0;i<A.controllerSlots;i++)global.charge(A.slot);assert.equal(global.state().chargedBytes,A.total);assert.throws(()=>global.charge(1));assert.equal(global.state().chargedBytes,A.total);assert.equal(global.state().intendedBytes,A.total+1);
});
model('all_64_attempts_including_failed_cancelled_65th_before_launch',()=>{
 const global=createByteAccount(A.total,'parent-model');global.charge(A.service);let attempts=0,inspected=0;const statuses=[];
 const launch=()=>{const slot=++attempts;global.charge(A.slot);inspected++;statuses.push(slot%3===0?'CANCELLED':slot%3===1?'FAILED':'COMPLETE');};
 for(let i=0;i<64;i++)launch();assert.equal(inspected,64);assert(statuses.includes('FAILED')&&statuses.includes('CANCELLED'));assert.throws(launch);assert.equal(attempts,65);assert.equal(inspected,64);assert.equal(global.state().chargedBytes,A.total);assert(43<=A.controllerSlots&&64<=A.controllerSlots);
});
model('reservation_and_ledger_before_helper_or_first_proof_model',()=>{
 const order=[],global=createByteAccount(A.total,'parent'),ledger=createByteAccount(A.ledger,'ledger');global.charge(A.service);global.charge(A.slot);order.push('RESERVED');
 const row=JSON.stringify({reservationIndex:1,cap:A.slot});ledger.charge(bytes(row));order.push('LEDGER_ADMITTED');order.push('LEDGER_WRITTEN');
 const f=staging();assert.equal(f.account.state().chargedBytes,A.wrapper);order.push('WRAPPER_ADMITTED');order.push('HELPER_MODEL');f.stage.append('first',{ok:true});order.push('PROOF_ADMITTED');assert.deepEqual(order,['RESERVED','LEDGER_ADMITTED','LEDGER_WRITTEN','WRAPPER_ADMITTED','HELPER_MODEL','PROOF_ADMITTED']);
 const missing=createByteAccount(A.wrapper-1,'missing-proof-capacity');let helpers=0;assert.throws(()=>{createAuditStaging({account:missing,metadata:metadata()});helpers++;});assert.equal(helpers,0);
});
model('utf8_base64_escaping_commas_and_exact_row_credit',()=>{
 const f=staging(),first={name:'é😀',fields:{rawBase64:Buffer.from([0,1,2,255]).toString('base64'),text:'"\\\n漢字'}},second={name:'second',fields:{ok:true}};
 f.stage.append(first.name,first.fields);f.stage.append(second.name,second.fields);assert.equal(f.account.state().chargedBytes,A.wrapper+bytes(first)+1+bytes(second));
 const encoded=f.stage.emit(),value=JSON.parse(encoded);assert.deepEqual(value.observations,[first,second]);assert(contribution(encoded)<=f.account.state().chargedBytes);assert(contribution(encoded)-bytes(first)-1-bytes(second)<=A.wrapper);
});
model('metadata_closed_seven_fields_and_actual_wrapper_bound',()=>{
 for(const index of [1,64,null]){const f=staging(A.proof,index),value=f.stage.emit();assert.equal(JSON.parse(value).reservationIndex,index);assert(contribution(value)<=A.wrapper);assert.equal(f.account.state().chargedBytes,A.wrapper);}
});
model('immutable_row_and_metadata_encodings_not_mutable_credit',()=>{
 const account=createByteAccount(A.proof,'immutable'),header=metadata(),fields={nested:{value:'original'}},stage=createAuditStaging({account,metadata:header});stage.append('row',fields);const admitted=account.state().chargedBytes;
 fields.nested.value='changed'.repeat(1000);header.instance='f'.repeat(32);const emitted=JSON.parse(stage.emit());assert.equal(emitted.instance,'a'.repeat(32));assert.equal(emitted.observations[0].fields.nested.value,'original');assert.equal(account.state().chargedBytes,admitted);
});
model('rows_one_use_parsed_frozen_service_flush_then_no_emit_append',()=>{
 const f=staging();f.stage.append('early',{nested:{value:1}});const charged=f.account.state().chargedBytes,rows=f.stage.rows();assert(Object.isFrozen(rows)&&Object.isFrozen(rows[0].fields.nested));assert.throws(()=>{rows[0].fields.nested.value=2;});assert.throws(()=>f.stage.rows());assert.throws(()=>f.stage.emit());assert.throws(()=>f.stage.append('late',{}));assert.equal(f.account.state().chargedBytes,charged);
});
model('emit_one_use_no_second_emission_or_row_reuse_refund',()=>{
 const f=staging();f.stage.append('proof',{value:1});const emitted=f.stage.emit(),charged=f.account.state().chargedBytes;assert.equal(typeof emitted,'string');assert.throws(()=>f.stage.emit());assert.throws(()=>f.stage.rows());assert.throws(()=>f.stage.append('extra',{}));assert.equal(f.account.state().chargedBytes,charged);assert.equal(f.account.healthy(),false);
});
model('distinct_retained_copy_requires_full_fresh_debit_before_write',()=>{
 const base=bytes({name:'x',fields:{payload:''}}),f=staging();f.stage.append('x',{payload:'x'.repeat(A.proof-A.wrapper-base)});const emitted=f.stage.emit();let copied=0;assert.throws(()=>{f.account.charge(contribution(emitted));copied++;});assert.equal(copied,0);assert.equal(f.account.state().chargedBytes,A.proof);assert(f.account.state().intendedBytes>A.proof);
 const small=staging();small.stage.append('small',{});const text=small.stage.emit(),before=small.account.state().chargedBytes;small.account.charge(contribution(text));assert.equal(small.account.state().chargedBytes,before+contribution(text));
});
model('serve_account_before_startup_and_double_debited_phase_flush',()=>{
 const service=createByteAccount(A.service,'service');service.charge(A.serviceHeader);service.charge(A.serviceDiagnostics);const stage=createAuditStaging({account:service,metadata:metadata(null)});assert.equal(service.state().chargedBytes,8192+A.wrapper);
 stage.append('GUARD_HELPER_CREATED',{pid:123});const early=service.state().chargedBytes,rows=stage.rows(),phase=JSON.stringify({schema:'phase-model',observations:rows})+'\n';service.charge(bytes(phase));assert.equal(service.state().chargedBytes,early+bytes(phase));assert.throws(()=>stage.emit());
});
model('partial_ledger_write_poison_preserves_reservation_and_no_retry',()=>{
 const global=createByteAccount(A.total,'parent'),ledger=createByteAccount(A.ledger,'ledger');global.charge(A.service);global.charge(A.slot);const raw=JSON.stringify({slot:1,state:'RESERVED'});ledger.charge(bytes(raw));let writes=1,actions=0;const partial=Error('MODEL_SHORT_LEDGER_WRITE');global.poison(partial);ledger.poison(partial);
 assert.throws(()=>{ledger.charge(bytes(raw));writes++;actions++;},error=>error===partial);assert.equal(writes,1);assert.equal(actions,0);assert.equal(global.state().chargedBytes,A.service+A.slot);assert.equal(ledger.state().chargedBytes,bytes(raw));
});
model('stdout_backpressure_not_byte_count_missing_capture_has_no_retry',()=>{
 const f=staging();f.stage.append('stdout',{});const encoded=f.stage.emit();let writes=0;const write=()=>{writes++;return false;};const backpressure=write(encoded);assert.equal(typeof backpressure,'boolean');assert.notEqual(typeof backpressure,'number');
 const missing=Error('MODEL_CAPTURE_MISSING_OR_TRUNCATED');f.account.poison(missing);assert.throws(()=>f.stage.emit(),error=>error===missing);assert.equal(writes,1);assert(f.account.state().chargedBytes>=contribution(encoded));
});
model('diagnostics_exhaustion_keeps_original_fault_cleanup_without_log_escape',()=>{
 const diag=createByteAccount(A.diagnostics,'diagnostics'),first=Error('ORIGINAL_COMMAND_FAULT');diag.charge(A.diagnostics);diag.poison(first);let writes=0,cleanup=0;
 assert.throws(()=>{diag.charge(1);writes++;},error=>error===first);diag.poison(Error('SECONDARY_DIAGNOSTIC_FAILURE'));cleanup++;assert.equal(diag.state().firstError,first);assert.equal(diag.state().chargedBytes,A.diagnostics);assert.equal(writes,0);assert.equal(cleanup,1);
});
model('late_cancel_or_success_cannot_encode_append_emit_or_advance_action',()=>{
 const f=staging(),cancel=Error('CANCELLED');f.account.poison(cancel);let touched=0,actions=0;const fields={get proof(){touched++;return true;}};
 assert.throws(()=>{f.stage.append('LATE_OK',fields);actions++;},error=>error===cancel);assert.throws(()=>f.stage.emit(),error=>error===cancel);assert.equal(touched,0);assert.equal(actions,0);
});
model('owner_fault_nonatomic_service_healthy_until_observed_revocation',()=>{
 const parent=createByteAccount(A.total,'parent'),serve=createByteAccount(A.service,'service'),first=Error('PARENT_LEDGER_FAILURE');parent.charge(A.slot);parent.poison(first);
 assert.equal(serve.healthy(),true);serve.charge(10);assert.equal(serve.state().chargedBytes,10);serve.poison(Error('EXISTING_LEASE_REVOCATION_OBSERVED'));assert.throws(()=>serve.charge(1));assert.equal(parent.state().firstError,first);assert.equal(parent.healthy(),false);
});
model('missing_slot_self_capacity_unknown_identity_or_foreign_account_refused',()=>{
 for(const change of [{reservationIndex:0},{reservationIndex:65},{reservationIndex:undefined},{capacity:A.total},{runId:'foreign'},{leaseSha256:'f'},{configurationSha256:'f'},{instance:'f'},{scope:'SELF_ASSIGNED_CAPACITY'}]){
  const account=createByteAccount(A.proof,'metadata');assert.throws(()=>createAuditStaging({account,metadata:{...metadata(),...change}}));assert.equal(account.healthy(),false);assert.equal(account.state().chargedBytes,A.wrapper);
 }
 assert.throws(()=>createAuditStaging({account:{charge:()=>A.proof,healthy:()=>true,state:()=>({chargedBytes:A.proof})},metadata:metadata()}),/OWNED_CAPTURE_BYTE_ACCOUNT_REQUIRED/);
});
model('malformed_encoding_sticky_fault_and_exact_unicode_scalar_accounting',()=>{
 const cycle={};cycle.self=cycle;
 for(const fields of [cycle,{value:undefined},{value:NaN},{toJSON(){return 'forged';}},{get value(){throw Error('GETTER_NOT_ALLOWED');}}]){const f=staging();assert.throws(()=>f.stage.append('invalid',fields));const first=f.account.state().firstError;assert.throws(()=>f.stage.emit(),error=>error===first);assert.equal(f.account.state().chargedBytes,A.wrapper);}
 for(const text of ['\ud800','\udc00','😀','\u0000\b\f\n\r\t','é漢']){const f=staging(),row={name:'unicode',fields:{text}};f.stage.append(row.name,row.fields);assert.equal(f.account.state().chargedBytes,A.wrapper+bytes(row));assert.deepEqual(JSON.parse(f.stage.emit()).observations,[row]);}
 const a=createByteAccount(3,'sticky');a.charge(3);assert.throws(()=>a.charge(1));const first=a.state().firstError;assert.throws(()=>a.charge(2),error=>error===first);assert.equal(a.state().chargedBytes,3);assert.equal(a.state().intendedBytes,6);assert(Object.isFrozen(a)&&Object.isFrozen(a.state()));
});


function proofFs({short=false,writeError=null,syncError=null,closeError=null,regular=true}={}){
 const calls=[],constants={O_WRONLY:1,O_CREAT:2,O_EXCL:4,O_NOFOLLOW:8,O_NONBLOCK:16};
 const fs={constants,openSync(path,flags,mode){calls.push({op:'open',path,flags,mode});return 7;},fstatSync(fd){calls.push({op:'fstat',fd});return {isFile:()=>regular};},writeSync(fd,raw){calls.push({op:'write',fd,bytes:raw.length});if(writeError)throw writeError;return short?raw.length-1:raw.length;},fsyncSync(fd){calls.push({op:'fsync',fd});if(syncError)throw syncError;},closeSync(fd){calls.push({op:'close',fd});if(closeError)throw closeError;}};
 return {fs,calls};
}
model('actual_exclusive_writer_short_once_closes_no_retry_or_refund',()=>{
 const f=proofFs({short:true}),account=createByteAccount(A.ledger,'actual-ledger-model'),raw=Buffer.from('reserved');
 assert.throws(()=>writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/reservation.json',bytes:raw,account}),/SHORT_PROOF_WRITE_NO_REPAIR/);
 assert.deepEqual(f.calls.map(c=>c.op),['open','fstat','write','close']);assert.equal(account.state().chargedBytes,raw.length);const first=account.state().firstError;
 assert.throws(()=>writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/reservation.json',bytes:raw,account}),error=>error===first);assert.equal(f.calls.filter(c=>c.op==='write').length,1);assert.equal(f.calls.filter(c=>c.op==='close').length,1);assert.equal(account.state().intendedBytes,2*raw.length);
});
model('actual_exclusive_writer_fsync_or_write_and_close_preserve_first_fault',()=>{
 for(const where of ['fsync','write']){const first=Error('ORIGINAL_'+where),secondary=Error('SECONDARY_CLOSE'),f=proofFs({syncError:where==='fsync'?first:null,writeError:where==='write'?first:null,closeError:secondary}),account=createByteAccount(A.ledger,'actual-error-model');
  assert.throws(()=>writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/proof.json',bytes:Buffer.from('proof'),account}),error=>error===first);assert.equal(account.state().firstError,first);assert.equal(f.calls.filter(c=>c.op==='close').length,1);assert.equal(f.calls.filter(c=>c.op==='write').length,1);
 }
});
model('actual_exclusive_writer_overflow_before_open_zero_underlying_effects',()=>{
 const f=proofFs(),account=createByteAccount(3,'actual-overflow-model');assert.throws(()=>writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/proof.json',bytes:Buffer.from('four'),account}));assert.deepEqual(f.calls,[]);assert.equal(account.state().chargedBytes,0);assert.equal(account.state().intendedBytes,4);assert.equal(account.healthy(),false);
});
model('actual_exclusive_writer_complete_flags_or_nonregular_handle_gate',()=>{
 const f=proofFs(),account=createByteAccount(A.ledger,'actual-complete-model'),raw=Buffer.from('proof');assert.equal(writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/proof.json',bytes:raw,account}),raw.length);
 assert.deepEqual(f.calls.map(c=>c.op),['open','fstat','write','fsync','close']);assert.equal(f.calls[0].flags,31);assert.equal(f.calls[0].mode,0o600);assert.equal(account.state().chargedBytes,raw.length);
 const bad=proofFs({regular:false}),badAccount=createByteAccount(A.ledger,'actual-nonregular-model');assert.throws(()=>writeExclusiveProof({fs:bad.fs,path:'/SYNTHETIC/proof.json',bytes:raw,account:badAccount}),/REGULAR_OWNED_PROOF_REQUIRED/);assert.deepEqual(bad.calls.map(c=>c.op),['open','fstat','close']);
});


model('custom_array_inherited_tojson_refused_without_hook_or_emission',()=>{
 const f=staging();let invoked=0;const array=[];Object.setPrototypeOf(array,{toJSON(){invoked++;return 'unbounded'.repeat(1000000);}});
 assert.throws(()=>f.stage.append('custom-array',{array}),/CANONICAL_ARRAY_PROTOTYPE_REQUIRED/);assert.equal(invoked,0);assert.equal(f.account.healthy(),false);assert.equal(f.account.state().chargedBytes,A.wrapper);const first=f.account.state().firstError;assert.throws(()=>f.stage.emit(),error=>error===first);assert.equal(invoked,0);
});
model('canonical_array_tojson_getter_or_hook_refused_without_invocation',()=>{
 for(const getter of [false,true]){const f=staging(),prior=Object.getOwnPropertyDescriptor(Array.prototype,'toJSON');let invoked=0;
  try{
   Object.defineProperty(Array.prototype,'toJSON',getter?{configurable:true,get(){invoked++;return ()=>{invoked++;return 'forged';};}}:{configurable:true,value(){invoked++;return 'forged';}});
   assert.throws(()=>f.stage.append('canonical-array',{array:[]}),/INHERITED_SERIALIZATION_REFUSED/);assert.equal(invoked,0);assert.equal(f.account.healthy(),false);assert.equal(f.account.state().chargedBytes,A.wrapper);
  }finally{if(prior)Object.defineProperty(Array.prototype,'toJSON',prior);else delete Array.prototype.toJSON;}
 }
});
model('object_prototype_tojson_pollution_refuses_rows_and_constructor_no_hook',()=>{
 for(const getter of [false,true]){const f=staging(),account=createByteAccount(A.proof,'constructor-prototype-model'),prior=Object.getOwnPropertyDescriptor(Object.prototype,'toJSON');let invoked=0;
  try{
   Object.defineProperty(Object.prototype,'toJSON',getter?{configurable:true,get(){invoked++;return ()=>{invoked++;return 'forged';};}}:{configurable:true,value(){invoked++;return 'forged';}});
   assert.throws(()=>f.stage.append('object-pollution',{value:1}),/INHERITED_SERIALIZATION_REFUSED/);
   assert.throws(()=>createAuditStaging({account,metadata:metadata()}),/INHERITED_SERIALIZATION_REFUSED/);
   assert.equal(invoked,0);assert.equal(f.account.healthy(),false);assert.equal(account.healthy(),false);assert.equal(account.state().chargedBytes,A.wrapper);
  }finally{if(prior)Object.defineProperty(Object.prototype,'toJSON',prior);else delete Object.prototype.toJSON;}
 }
});
model('actual_exclusive_writer_invalid_type_or_oversize_poison_before_open',()=>{
 for(const raw of ['not-a-buffer',Buffer.alloc(A.total+1)]){const f=proofFs(),account=createByteAccount(A.ledger,'invalid-write-model');
  assert.throws(()=>writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/invalid.json',bytes:raw,account}),/BOUNDED_PROOF_BUFFER/);assert.deepEqual(f.calls,[]);assert.equal(account.healthy(),false);assert.equal(account.state().chargedBytes,0);
 }
});
model('actual_exclusive_writer_invalid_input_cannot_replace_existing_first_fault',()=>{
 for(const raw of [null,Buffer.alloc(A.total+1)]){const f=proofFs(),account=createByteAccount(A.ledger,'invalid-prior-fault-model'),first=Error('ORIGINAL_FAILURE');account.poison(first);
  assert.throws(()=>writeExclusiveProof({fs:f.fs,path:'/SYNTHETIC/invalid.json',bytes:raw,account}),error=>error===first);assert.deepEqual(f.calls,[]);assert.equal(account.state().firstError,first);assert.equal(account.state().chargedBytes,0);
 }
});

// Separate Root grant only. --check parses syntax and never evaluates this loop.
for(const {name,fn} of definitions){try{await fn();}catch(error){throw Error('MODEL '+name+': '+String(error),{cause:error});}}
console.log(JSON.stringify({scope:'PRODUCER4_PURE_CAPTURE_ALLOCATION_MODELS_ONLY',definitions:definitions.length,executed:definitions.length,realWritesObserved:false,realHelperExecuted:false,wholeConsumerQualified:false,atomicGlobalFenceClaimed:false}));
