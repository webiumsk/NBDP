// SOURCE only. Pure local byte custody; no helper, clock, filesystem or writer.
import {types} from 'node:util';
export const ALLOCATION=Object.freeze({total:16777216,service:8388608,serviceHeader:4096,serviceDiagnostics:4096,controllerSlots:64,slot:131072,proof:122880,ledger:4096,diagnostics:4096,wrapper:1024});
const accounts=new WeakSet();
const fault=error=>error instanceof Error?error:Error('CAPTURE_ACCOUNT_POISON',{cause:error});
export function createByteAccount(cap,name){
 if(!Number.isSafeInteger(cap)||cap<0||cap>ALLOCATION.total||typeof name!=='string'||name.length===0||name.length>256)throw TypeError('CLOSED_CAPTURE_ACCOUNT');
 let chargedBytes=0,intendedBytes=0,firstError=null;
 const poison=error=>{if(firstError===null)firstError=fault(error);return firstError;};
 const account=Object.freeze({
  charge(bytes){
   if(!Number.isSafeInteger(bytes)||bytes<0)throw poison(TypeError('CAPTURE_INTENDED_BYTES_INTEGER'));
   const next=intendedBytes+bytes;if(!Number.isSafeInteger(next))throw poison(RangeError('CAPTURE_INTENDED_BYTES_OVERFLOW'));
   intendedBytes=next;
   if(firstError!==null)throw firstError;
   if(bytes>cap-chargedBytes)throw poison(Error('CAPTURE_ALLOCATION_EXCEEDED:'+name));
   chargedBytes+=bytes;return chargedBytes;
  },
  poison,
  healthy:()=>firstError===null,
  state:()=>Object.freeze({limit:cap,chargedBytes,intendedBytes,poisoned:firstError!==null,firstError})
 });accounts.add(account);return account;
}
// Exact well-formed JSON string UTF8 size, without allocating an escaped copy.
function stringBytes(value){
 let bytes=2;
 for(let i=0;i<value.length;i++){
  const c=value.charCodeAt(i);
  if(c===34||c===92||c===8||c===9||c===10||c===12||c===13)bytes+=2;
  else if(c<32)bytes+=6;
  else if(c<128)bytes++;
  else if(c<2048)bytes+=2;
  else if(c>=0xd800&&c<=0xdbff){const next=value.charCodeAt(i+1);if(next>=0xdc00&&next<=0xdfff){bytes+=4;i++;}else bytes+=6;}
  else if(c>=0xdc00&&c<=0xdfff)bytes+=6;
  else bytes+=3;
 }return bytes;
}
function jsonBytes(value,ancestors=new Set(),depth=0){
 if(depth>64)throw Error('CAPTURE_JSON_DEPTH');
 if(value===null)return 4;
 if(typeof value==='string')return stringBytes(value);
 if(typeof value==='boolean')return value?4:5;
 if(typeof value==='number'){if(!Number.isFinite(value))throw Error('CAPTURE_FINITE_JSON_NUMBER');return JSON.stringify(value).length;}
 if(typeof value!=='object'||types.isProxy(value))throw Error('CAPTURE_PLAIN_JSON_DATA_ONLY');
 const array=Array.isArray(value),proto=Object.getPrototypeOf(value);
 if(!array&&proto!==Object.prototype&&proto!==null)throw Error('CAPTURE_PLAIN_JSON_OBJECT_ONLY');
 if(ancestors.has(value))throw Error('CAPTURE_JSON_CYCLE');ancestors.add(value);
 let bytes=2;const descriptors=Object.getOwnPropertyDescriptors(value);
 for(const descriptor of Object.values(descriptors))if(!Object.hasOwn(descriptor,'value'))throw Error('CAPTURE_JSON_ACCESSOR_REFUSED');
 if(Object.hasOwn(descriptors,'toJSON'))throw Error('CAPTURE_JSON_TOJSON_REFUSED');
 if(array){
  for(let i=0;i<value.length;i++){
   if(i)bytes++;
   bytes+=Object.hasOwn(descriptors,String(i))?jsonBytes(descriptors[i].value,ancestors,depth+1):4;
  }
 }else{
  let count=0;
  for(const key of Object.keys(value)){if(count++)bytes++;bytes+=stringBytes(key)+1+jsonBytes(descriptors[key].value,ancestors,depth+1);}
 }
 ancestors.delete(value);if(!Number.isSafeInteger(bytes))throw Error('CAPTURE_JSON_BYTES_OVERFLOW');return bytes;
}
function deepFreeze(value){if(value&&typeof value==='object'){for(const item of Object.values(value))deepFreeze(item);Object.freeze(value);}return value;}
export function createAuditStaging({account,metadata}){
 if(!accounts.has(account))throw TypeError('OWNED_CAPTURE_BYTE_ACCOUNT_REQUIRED');
 let consumed=false;const encodedRows=[];let rowCredit=0;
 const reject=error=>{throw account.poison(error);};
 const active=()=>{if(!account.healthy())throw account.state().firstError;if(consumed)reject(Error('AUDIT_STAGING_ALREADY_CONSUMED'));};
 let fixed;
 try{
  active();account.charge(ALLOCATION.wrapper);
  if(!metadata||types.isProxy(metadata)||typeof metadata!=='object'||Array.isArray(metadata))throw Error('CLOSED_AUDIT_METADATA');
  const keys=['schema','reservationIndex','instance','scope','runId','leaseSha256','configurationSha256'];
  if(Object.keys(metadata).sort().join('|')!==[...keys].sort().join('|'))throw Error('CLOSED_AUDIT_METADATA_KEYS');
  const descriptors=Object.getOwnPropertyDescriptors(metadata);for(const key of keys)if(!Object.hasOwn(descriptors[key],'value'))throw Error('AUDIT_METADATA_ACCESSOR_REFUSED');
  fixed=Object.fromEntries(keys.map(key=>[key,descriptors[key].value]));
  if(fixed.schema!=='e02-controller-guard-audit-v1'||fixed.scope!=='ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION'||!(fixed.reservationIndex===null||(Number.isInteger(fixed.reservationIndex)&&fixed.reservationIndex>=1&&fixed.reservationIndex<=ALLOCATION.controllerSlots))||!['instance','runId','leaseSha256','configurationSha256'].every(key=>typeof fixed[key]==='string')||!/^[0-9a-f]{32}$/.test(fixed.instance)||!/^[0-9a-f]{32}$/.test(fixed.runId)||!/^[0-9a-f]{64}$/.test(fixed.leaseSha256)||!/^[0-9a-f]{64}$/.test(fixed.configurationSha256))throw Error('AUDIT_METADATA_BOUND_IDENTITY');
 }catch(error){reject(error);}
 const metadataEncoding=JSON.stringify(fixed);
 return Object.freeze({
  append(name,fields){
   active();
   try{
    if(typeof name!=='string'||name.length===0)throw Error('AUDIT_ROW_NAME');
    const row={name,fields},bytes=jsonBytes(row),comma=encodedRows.length?1:0;
    account.charge(bytes+comma); // Exact intended UTF8 bytes, before retained string/push.
    const encoded=JSON.stringify(row);
    if(Buffer.byteLength(encoded)!==bytes)throw Error('AUDIT_ENCODING_CHANGED');
    encodedRows.push(encoded);rowCredit+=bytes+comma;
   }catch(error){reject(error);}
  },
  rows(){
   active();try{const rows=deepFreeze(encodedRows.map(row=>JSON.parse(row)));consumed=true;encodedRows.length=0;return rows;}catch(error){reject(error);}
  },
  emit(){
   active();try{
    const encoded=metadataEncoding.slice(0,-1)+',"observations":['+encodedRows.join(',')+']}';
    // Returned value has no outer property/newline. Credit conservatively includes
    // those retained bytes and the containing result's final closing brace.
    const contribution=Buffer.byteLength(',"guardController":'+encoded+'}\n');
    if(contribution-rowCredit>ALLOCATION.wrapper)throw Error('AUDIT_WRAPPER_PREPAY_EXCEEDED');
    if(contribution>ALLOCATION.wrapper+rowCredit||ALLOCATION.wrapper+rowCredit>account.state().chargedBytes)throw Error('AUDIT_ENCODING_CREDIT_EXCEEDED');
    consumed=true;encodedRows.length=0;return encoded;
   }catch(error){reject(error);}
  }
 });
}
