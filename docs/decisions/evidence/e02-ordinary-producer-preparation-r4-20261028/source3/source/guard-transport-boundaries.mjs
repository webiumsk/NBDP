// SOURCE-only dependency-injected boundaries. No child, clock, timer or I/O on import.
// The caller supplies the exact owned ChildProcess and original monotonic deadline.
// This is not an atomic clock-to-signal transaction or a process-reap attestation.
const SECOND_NS=1000000000n,MILLISECOND_NS=1000000n;
const clockPair=(now,end)=>{if(typeof now!=='bigint'||typeof end!=='bigint')throw TypeError('GUARD_CLEANUP_CLOCK_BIGINT_REQUIRED');};

export function cleanupPlan(nowBigInt,endBigInt){
 clockPair(nowBigInt,endBigInt);const remaining=endBigInt-nowBigInt;
 if(remaining<=0n)return {signal:null,escalationDelayMs:null};
 if(remaining<=SECOND_NS)return {signal:'SIGKILL',escalationDelayMs:null};
 // Reserve at least one nanosecond inside the existing end; never renew it.
 const wholeMs=(remaining-1n)/MILLISECOND_NS;
 return {signal:'SIGTERM',escalationDelayMs:Number(wholeMs<1000n?wholeMs:1000n)};
}

export function dispatchOwnedSignal({sample,end,child,record,signal}){
 if(signal!=='SIGTERM'&&signal!=='SIGKILL')throw TypeError('GUARD_OWNED_SIGNAL_NOT_ALLOWED');
 if(typeof sample!=='function'||typeof record!=='function'||typeof end!=='bigint'||!child||typeof child.kill!=='function')throw TypeError('GUARD_OWNED_SIGNAL_OPERANDS');
 const ownedKill=child.kill.bind(child);
 const now=sample();clockPair(now,end);
 if(now>=end){
  try{record('GUARD_HELPER_CLEANUP_DEADLINE_EXHAUSTED',{action:'NO_LATE_SIGNAL',hostOwnedCleanupRequired:true});}catch{}
  return false;
 }
 // No observer, timer or asynchronous yield occurs between this sample and kill.
 try{
  const sent=ownedKill(signal);
  record('GUARD_HELPER_TERMINATE',{signal}); // Attempt only; no delivered/reaped claim.
  return sent===true;
 }catch{return false;} // Caller retains its terminal fence/first fault and owns cleanup.
}

// Known helper failure is primary before any fallible diagnostic/EOF retention.
export function retainAfterFailure({original,bad,retain}){
 try{bad(original);}catch{}
 try{retain();}catch(error){const secondary=error instanceof Error?error:Error('HELPER_FAILURE_RETENTION_ERROR',{cause:error});try{bad(secondary);}catch{}}
 return false;
}
export function observeStderr({record,bad,chunk}){
 return retainAfterFailure({original:Error('GUARD_HELPER_STDERR'),bad,retain:()=>record('GUARD_HELPER_STDERR',{rawBase64:Buffer.from(chunk).subarray(0,2048).toString('base64')})});
}

export function terminalValid({ended,code,signal,stdoutEOF,stderrEOF,exitSeen}){
 return ended===true&&code===0&&signal===null&&stdoutEOF===true&&stderrEOF===true&&exitSeen===true;
}
