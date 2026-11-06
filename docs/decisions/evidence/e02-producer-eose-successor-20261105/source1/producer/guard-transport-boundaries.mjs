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
export function retainAfterFailure({original,bad,retain,secondaryErrors=null,label='helper-retention'}){
 try{bad(original);}catch{}
 try{retain();}catch(error){const secondary=error instanceof Error?error:Error('HELPER_FAILURE_RETENTION_ERROR',{cause:error});if(secondaryErrors!==null)appendRetentionSecondary(secondaryErrors,label,secondary);try{bad(secondary);}catch{}}
 return false;
}
export function observeStderr({record,bad,chunk,secondaryErrors=null}){
 return retainAfterFailure({original:Error('GUARD_HELPER_STDERR'),bad,secondaryErrors,label:'helper-stderr-retention',retain:()=>record('GUARD_HELPER_STDERR',{rawBase64:Buffer.from(chunk).subarray(0,2048).toString('base64')})});
}

export function terminalValid({ended,code,signal,stdoutEOF,stderrEOF,exitSeen}){
 return ended===true&&code===0&&signal===null&&stdoutEOF===true&&stderrEOF===true&&exitSeen===true;
}

// Bounded secondary diagnostics; these are not a success or extra capture budget.
export function appendRetentionSecondary(rows,label,error){
 if(rows.length>=64)return false;
 let message;try{message=String(error).slice(0,2048);}catch{message='UNPRINTABLE_RETENTION_ERROR';}
 rows.push(Object.freeze({label:String(label).slice(0,128),error:message}));return true;
}
// ACTUAL registration used by production transport and memory-fake regressions.
export function registerHelperTerminalCallbacks({child,state,record,bad,framer,onClose}){
 child.on('error',bad);child.stdin.on('error',bad);
 child.stderr.on('data',chunk=>observeStderr({record,bad,chunk,secondaryErrors:state.secondaryErrors}));
 child.stdout.on('end',()=>{
  state.stdoutEOF=true;const retain=()=>{framer.end();record('GUARD_HELPER_STDOUT_EOF',{});};
  if(!state.ended)retainAfterFailure({original:Error('UNEXPECTED_GUARD_STDOUT_EOF'),bad,retain,secondaryErrors:state.secondaryErrors,label:'helper-stdout-eof-retention'});
  else try{retain();}catch(error){bad(error);}
 });
 child.stderr.on('end',()=>{state.stderrEOF=true;try{record('GUARD_HELPER_STDERR_EOF',{});}catch(error){bad(error);}});
 child.on('exit',(code,signal)=>{
  state.exitSeen=true;const retain=()=>record('GUARD_HELPER_EXIT',{code,signal});
  if(!state.ended||code!==0||signal!==null)retainAfterFailure({original:Error('GUARD_HELPER_UNEXPECTED_EXIT'),bad,retain,secondaryErrors:state.secondaryErrors,label:'helper-exit-retention'});
  else try{retain();}catch(error){bad(error);}
 });
 child.on('close',(code,signal)=>{
  state.closeSeen=true;const retain=()=>record('GUARD_HELPER_CLOSE',{code,signal,stdoutEOF:state.stdoutEOF,stderrEOF:state.stderrEOF,exitSeen:state.exitSeen});
  try{
   if(!terminalValid({ended:state.ended,code,signal,stdoutEOF:state.stdoutEOF,stderrEOF:state.stderrEOF,exitSeen:state.exitSeen}))retainAfterFailure({original:Error('GUARD_HELPER_LIFECYCLE_NEGATIVE'),bad,retain,secondaryErrors:state.secondaryErrors,label:'helper-close-retention'});
   else try{retain();}catch(error){bad(error);}
  }finally{try{onClose(code,signal);}catch(error){appendRetentionSecondary(state.secondaryErrors,'helper-close-hooks',error);try{bad(error);}catch{}}}
 });
}
