// Bounded observation writer; runtime supplies only the real fixed fs/fd/clocks.
// Model tests supply fake fs. No socket, guard, module loader or service here.
export function createPhaseWriter({fs,fd,clock,utc,limit=16777216}){
 let sequence=0,intendedTotalBytes=0,acknowledgedTotalBytes=0,poisoned=false,firstError=null,lastAttempt=null;
 function fail(error){poisoned=true;if(firstError===null)firstError=error;throw firstError;}
 function write(phase,fields={}){
  if(poisoned)throw firstError; // Never rewrite/retry a partial or unknown write.
  lastAttempt={sequence:++sequence,phase,intendedBytes:null,writeInvoked:false,reportedCount:null,
   acknowledgedBytes:0,acknowledgedPrefixBase64:'',physicalBytes:null,error:null};
  try{
   const row={schema:'e02-transport-query-phase-v2',sequence,utc:utc(),monotonicNanoseconds:clock().toString(),phase,...fields};
   const raw=Buffer.from(JSON.stringify(row)+'\n');lastAttempt.intendedBytes=raw.length;intendedTotalBytes+=raw.length;
   if(intendedTotalBytes>limit)throw Error('ORIGINAL_CAPTURE_BOUND');
   lastAttempt.writeInvoked=true;lastAttempt.acknowledgedBytes=null;lastAttempt.acknowledgedPrefixBase64=null;
   const count=fs.writeSync(fd,raw); // Exactly ONE call; no repairing write loop.
   lastAttempt.reportedCount=typeof count==='number'&&Number.isFinite(count)?count:String(count).slice(0,80);
   if(!Number.isInteger(count)||count<0||count>raw.length)throw Error('INVALID_PHASE_WRITE_COUNT');
   lastAttempt.acknowledgedBytes=count;lastAttempt.acknowledgedPrefixBase64=raw.subarray(0,count).toString('base64');
   acknowledgedTotalBytes+=count;
   if(count!==raw.length)throw Error('SHORT_PHASE_WRITE');
   return row;
  }catch(error){lastAttempt.error=String(error);return fail(error);}
 }
 write.state=()=>({sequence,intendedTotalBytes,acknowledgedTotalBytes,physicalBytes:null,
  physicalMeaning:'NOT_INDEPENDENTLY_MEASURED_ACKNOWLEDGED_PREFIX_IS_NOT_PHYSICAL_ATTESTATION',
  poisoned,firstError:firstError===null?null:String(firstError),lastAttempt:lastAttempt===null?null:{...lastAttempt}});
 return write;
}
