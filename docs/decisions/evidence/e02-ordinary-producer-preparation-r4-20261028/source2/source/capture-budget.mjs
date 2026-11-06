// One aggregate budget for the original proxy rows and new phase observations.
// No socket/guard/optional-module import. Model controls use fake fixed fs.
import {createHash} from 'node:crypto';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export function createCaptureBudget({fs,streams,limit,account=null}){
 if(!Number.isSafeInteger(limit)||limit<=0||limit>16777216)throw Error('ORIGINAL_AGGREGATE_CAPTURE_BOUND');
 if(!streams||Object.keys(streams).sort().join(',')!=='phase,proxy'||streams.phase===streams.proxy)throw Error('CLOSED_TWO_CAPTURE_STREAMS');
 const byFd=new Map(Object.entries(streams).map(([name,fd])=>[fd,name]));
 let intended=0,acknowledged=0,firstError=null,lastAttempt=null;
 const totals={proxy:{intended:0,acknowledged:0},phase:{intended:0,acknowledged:0}};
 function poison(error){if(firstError===null)firstError=error;return firstError;}
 function healthy(){if(firstError!==null)throw firstError;}
 function writeSync(fd,bytes){
  healthy();
  const stream=byFd.get(fd);if(!stream)throw poison(Error('UNKNOWN_CAPTURE_STREAM'));
  if(!Buffer.isBuffer(bytes))throw poison(Error('FIXED_CAPTURE_BUFFER'));
  lastAttempt={stream,intendedBytes:bytes.length,writeInvoked:false,reportedCount:null,
   acknowledgedBytes:0,acknowledgedPrefixSha256:hash(Buffer.alloc(0)),physicalBytes:null,error:null};
  intended+=bytes.length;totals[stream].intended+=bytes.length;
  try{
   if(intended>limit)throw Error('ORIGINAL_AGGREGATE_CAPTURE_BOUND');
   if(account!==null)account.charge(bytes.length); // Shared owned service counter, before write.
   lastAttempt.writeInvoked=true;lastAttempt.acknowledgedBytes=null;lastAttempt.acknowledgedPrefixSha256=null;
   const count=fs.writeSync(fd,bytes); // One underlying call; never repair/rewrite.
   lastAttempt.reportedCount=typeof count==='number'&&Number.isFinite(count)?count:String(count).slice(0,80);
   if(!Number.isInteger(count)||count<0||count>bytes.length)throw Error('INVALID_CAPTURE_WRITE_COUNT');
   acknowledged+=count;totals[stream].acknowledged+=count;
   lastAttempt.acknowledgedBytes=count;lastAttempt.acknowledgedPrefixSha256=hash(bytes.subarray(0,count));
   // Return the real short count to the unchanged phase writer. Its own checked
   // count path can retain that known prefix. Every caller then checks healthy.
   if(count!==bytes.length){const error=Error('SHORT_CAPTURE_WRITE');lastAttempt.error=String(error);poison(error);}
   return count;
  }catch(error){lastAttempt.error=String(error);throw poison(error);}
 }
 function state(){return {schema:'e02-minimum-aggregate-capture-budget-v3',limit,intendedTotalBytes:intended,
  acknowledgedTotalBytes:acknowledged,streams:{proxy:{...totals.proxy},phase:{...totals.phase}},
  poisoned:firstError!==null,firstError:firstError===null?null:String(firstError),
  physicalBytes:null,physicalMeaning:'ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION',
  lastAttempt:lastAttempt===null?null:{...lastAttempt},allocationAccount:account===null?null:captureAccountState(account)};}
 return {writeSync,healthy,poison,state};
}
// A new observation never authorizes action after a failed original guard.
// Preserve the actual guard fault over a secondary refusal-retention failure.
export function observedGuard(core,phase,label){
 phase('GUARD_ENTRY',{label});
 try{core();}catch(error){
  try{phase('GUARD_EXIT',{label,ok:false,error:String(error)});}catch(retention){
   if(error&&typeof error==='object')try{Object.defineProperty(error,'guardObservationError',{value:String(retention),configurable:true});}catch{}
  }
  throw error;
 }
 phase('GUARD_EXIT',{label,ok:true,error:null});
}
// Exactly one durable proof write. Short/error is terminal, never repaired.
export function writeExclusiveProof({fs,path,bytes,account}){
 let fd=null;
 try{
  if(!Buffer.isBuffer(bytes)||bytes.length>16777216)throw Error('BOUNDED_PROOF_BUFFER');
  account.charge(bytes.length); // Admission precedes opening/creating the proof.
  fd=fs.openSync(path,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK,0o600);
  if(!fs.fstatSync(fd).isFile())throw Error('REGULAR_OWNED_PROOF_REQUIRED');
  const count=fs.writeSync(fd,bytes);
  if(count!==bytes.length)throw Error('SHORT_PROOF_WRITE_NO_REPAIR');
  fs.fsyncSync(fd);return count;
 }catch(error){throw account.poison(error);}
 finally{if(fd!==null)try{fs.closeSync(fd);}catch(error){throw account.poison(error);}}
}

export function captureAccountState(account){const value=account.state();return {...value,firstError:value.firstError===null?null:String(value.firstError)};}

// Production stdout path: immutable precharged encodings, one intended emission.
// Node write's boolean is backpressure; parent actual capture/EOF is authoritative.
export function createControllerStdoutEmitter({responseEncoding,encodedAudit,write,isHealthy,onFault}){
 let used=false,firstError=null;
 const fail=error=>{if(firstError===null)firstError=error instanceof Error?error:Error(String(error));try{onFault(firstError);}catch{}return firstError;};
 return ()=>{
  try{
   if(firstError!==null)throw firstError;
   if(used)throw Error('CONTROLLER_PROOF_ENCODING_ALREADY_EMITTED');
   used=true; // Never retry/refund after encoding, callback or write failure.
   if(typeof responseEncoding!=='string'||!responseEncoding.endsWith('}')||typeof encodedAudit!=='string'||typeof write!=='function'||typeof isHealthy!=='function'||isHealthy()!==true)throw Error('CLOSED_HEALTHY_CONTROLLER_EMISSION');
   const contribution=',"guardController":'+encodedAudit+'}\n';
   if(Buffer.byteLength(contribution)>122880)throw Error('PRECHARGED_CONTROLLER_PROOF_SHARE');
   const bytes=Buffer.from(responseEncoding.slice(0,-1)+contribution);
   if(bytes.length>8388608)throw Error('ORIGINAL_PARENT_STDOUT_BOUND');
   write(bytes,error=>{if(error)fail(error);}); // ONE invocation, never Boolean→byte count.
   return Object.freeze({intendedBytes:bytes.length,writeInvoked:true,physicalBytes:null});
  }catch(error){throw fail(error);}
 };
}
