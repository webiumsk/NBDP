// Small observation-only helpers; production caller retains original guards and
// original protocol actions. Fake callbacks/sinks are used by DATA definitions.
export function createCallbackBoundary({isClosed,healthy,fatal}){
 return (fn,incomingFault=null)=>{
  if(isClosed())return;
  try{healthy();fn();}catch(error){fatal(incomingFault??error);}
 };
}
export function observedUpstreamSend({socket,bytes,sha,phase,callback,isClosed}){
 const bufferHash=sha(bytes);
 phase('PROXY_SEND_INVOKE_ENTRY',{target:'RELAY',bufferHash,bytes:bytes.length});
 socket.send(bytes,{binary:false},error=>callback(()=>{
  phase('PROXY_SEND_CALLBACK_ENTRY',{target:'RELAY',bufferHash,error:error?String(error):null});
  if(error)throw error;if(sha(bytes)!==bufferHash)throw Error('ACTUAL_PROXY_BUFFER_MUTATION');
  phase('PROXY_SEND_CALLBACK_COMPLETE',{target:'RELAY',bufferHash});
  // Evidence-only callback: no new guard, decode, send or protocol state.
 },error??null));
 if(!isClosed())phase('PROXY_SEND_INVOKE_RETURNED',{target:'RELAY',bufferHash});
}
// Actual producer4 pre-send/callback fence shared with memory-mocked regressions.
// receipt generation increments synchronously at APP callback receipt before await.
export function proxyContinuationValid({connection,generation,appReceiptGeneration,bytes,bufferHash,sha,publicationInvalidated,currentGeneration=null,expectedGeneration=null,currentAttempt=null,expectedAttempt=null}){
 if(connection.active!==true||connection.generation!==generation||connection.appReceiptGeneration!==appReceiptGeneration||sha(bytes)!==bufferHash||publicationInvalidated)return false;
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 return (expectedGeneration===null||same(currentGeneration,expectedGeneration))&&(expectedAttempt===null||same(currentAttempt,expectedAttempt));
}
export function flowContinuationValid({stageIndex,expectedIndex,activeAttempt,expectedAttempt,publish,publicationInvalidated,connection,expectedReceipt,currentGenerationMatches}){
 if(stageIndex!==expectedIndex||JSON.stringify(activeAttempt)!==JSON.stringify(expectedAttempt))return false;
 if(!publish)return true;
 return !publicationInvalidated&&currentGenerationMatches===true&&(connection===null||(connection.active===true&&connection.appReceiptGeneration===expectedReceipt));
}
// Shared ACTUAL APP/RELAY error entrypoint. Claim/fence original fault before
// any fallible observation; observation failure is secondary, cleanup still runs.
export function createProxySocketErrorBoundary({claimFault,observeFault,cleanupFault}){
 return (originalSocketError,context)=>{
  if(claimFault(originalSocketError)!==true)return;
  const secondary=[];
  try{observeFault(originalSocketError,context);}
  catch(error){secondary.push({label:'socket-error-observation',error});}
  finally{cleanupFault(originalSocketError,secondary,context);}
 };
}
