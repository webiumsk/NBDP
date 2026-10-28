// SOURCE-only fixed bootstrap. No model execution during preparation.
import assert from 'node:assert/strict';
import {MODELS} from 'file:///Data/nbdp-e02-tooling-20261027/completion-primary-wrapper-preparation-r3/test_origin_models.mjs';
const EXPECTED=["actual_adapter_direct_within_phase_positive", "actual_adapter_yielded_same_session_positive", "actual_adapter_command_substitution_rejected", "actual_adapter_config_substitution_rejected", "actual_adapter_release_substitution_rejected", "actual_adapter_canonical_result_substitution_rejected", "actual_adapter_fabricated_inner_api_rejected", "actual_adapter_pipe_eof_substitution_rejected", "actual_adapter_observed_exit0_one_ns_after_expiry_rejected", "actual_adapter_primary_subject_after_expiry_rejected", "actual_adapter_invalid_proxy_cleanup_rejected"];
assert.equal(process.argv.length,2);assert.deepEqual(process.execArgv,[]);
assert.equal(process.execPath,'/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node');
assert.equal(MODELS.length,11);assert.deepEqual(MODELS.map(row=>row.name),EXPECTED);
assert.equal(new Set(EXPECTED).size,11);assert.ok(MODELS.every(row=>typeof row.body==='function'));
const started=process.hrtime.bigint(),rows=[];
for(const model of MODELS){
 const t0=process.hrtime.bigint();
 try{await model.body();rows.push({name:model.name,ok:true,elapsedNs:Number(process.hrtime.bigint()-t0)});}
 catch(error){rows.push({name:model.name,ok:false,elapsedNs:Number(process.hrtime.bigint()-t0),error:{name:error.name,message:error.message,stack:error.stack??null}});}
}
const elapsedNs=Number(process.hrtime.bigint()-started);assert.ok(Number.isSafeInteger(elapsedNs));
console.log(JSON.stringify({schema:'e02-wrapper-origin11-actual-model-result-v1',scopeVersion:'E02_WRAPPER_R3_REVIEW_EXPIRY_IDENTITY_DISPATCH_ORIGIN',modelsDefined:11,modelsExecuted:rows.length,models:rows,elapsedNs}));
process.exitCode=rows.length===11&&rows.every(row=>row.ok===true)?0:2;
