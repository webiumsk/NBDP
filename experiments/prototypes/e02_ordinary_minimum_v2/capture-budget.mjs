// One aggregate budget for the original proxy rows and new phase observations.
// No socket/guard/optional-module import. Model controls use fake fixed fs.
import {createHash} from 'node:crypto';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export function createCaptureBudget({fs,streams,limit}){
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
 function state(){return {schema:'e02-minimum-aggregate-capture-budget-v2',limit,intendedTotalBytes:intended,
  acknowledgedTotalBytes:acknowledged,streams:{proxy:{...totals.proxy},phase:{...totals.phase}},
  poisoned:firstError!==null,firstError:firstError===null?null:String(firstError),
  physicalBytes:null,physicalMeaning:'ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION',
  lastAttempt:lastAttempt===null?null:{...lastAttempt}};}
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
