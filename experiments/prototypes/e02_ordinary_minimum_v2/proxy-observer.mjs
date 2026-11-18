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
