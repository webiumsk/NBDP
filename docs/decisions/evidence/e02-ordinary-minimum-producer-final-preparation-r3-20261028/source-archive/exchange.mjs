// Version2: original guard/timer/query positions, deterministic terminal custody
// independent of phase/outcome retention. Late callbacks do no writes/actions.
export async function exchange(ctx,events,filter,label){
 const {WebSocket,p,check,phase,put,strictJSON,sha,clock,arm,clear}=ctx;
 check('exchange-entry');
 if(typeof label!=='string'||!/^[a-z0-9-]{1,48}$/.test(label))throw Error('FIXED_EXCHANGE_LABEL');
 const started=clock();phase('EXCHANGE_START',{label});
 return await new Promise((resolve,reject)=>{
  let ws=null,timer=null,terminalClaimed=false,terminationAttempted=false;
  const ack=[],received=[],sentFrames=[];let queryEnded=false,eose=null;
  function finish(incomingError,priorSecondary=[]){
   if(terminalClaimed)return;
   terminalClaimed=true;
   let first=incomingError??null;const secondary=[...priorSecondary];
   const note=(stage,error)=>{if(first===null)first=error;else secondary.push({stage,error:String(error)});};
   const attempt=(stage,fn)=>{try{return fn();}catch(error){note(stage,error);}};
   let elapsedNanoseconds=null;
   try{
    attempt('terminal-clock',()=>{elapsedNanoseconds=Number(clock()-started);});
    if(timer!==null)attempt('clear-timer',()=>clear(timer));
    attempt('terminal-phase',()=>phase(first===null?'EXCHANGE_RESOLVED':'EXCHANGE_REJECTED',{
     label,elapsedNanoseconds,error:first===null?null:String(first)}));
    attempt('terminal-outcome',()=>put(label+'-outcome.json',Buffer.from(JSON.stringify({label,
     elapsedNanoseconds,ack,received,eose,sentFrames,error:first===null?null:String(first),
     secondaryRetentionErrors:secondary,observer:typeof phase.state==='function'?phase.state():null},null,2)+'\n')));
   }catch(error){note('terminal-boundary',error);}
   finally{
    // No observation write can prevent exact owned-socket termination or Promise
    // rejection. Reentrant/late close/error/timer callbacks are inert.
    if(ws!==null&&!terminationAttempted){terminationAttempted=true;attempt('terminate-owned-socket',()=>ws.terminate());}
    if(first!==null){
     if(first&&typeof first==='object'){try{Object.defineProperty(first,'diagnosticSecondaryErrors',{value:secondary,configurable:true});}catch{}}
     reject(first);
    }else resolve({ack,received,eose,sentFrames,elapsedNanoseconds});
   }
  }
  function active(fn,incomingFault=null){if(terminalClaimed)return;try{fn();}catch(error){finish(incomingFault??error,incomingFault!==null&&incomingFault!==error?[{stage:'callback-observation-or-guard',error:String(error)}]:[]);}}
  function maybeComplete(){
   if(!sentFrames.length||!sentFrames.every(row=>row.sendCallbackCompleted))return;
   if(events&&events.every(event=>ack.some(row=>row.frame[1]===event.id&&row.frame[2]===true)))finish();
   else if(filter&&queryEnded)finish();
  }
  function sendKnown(frame,eventId){
   check('send-before');const bytes=Buffer.from(JSON.stringify(frame));
   const framePin=put(label+'-'+sentFrames.length+'-sent-frame.json',bytes);
   const row={frame:framePin,eventId,messageType:frame[0],sendInvoked:false,sendCallbackCompleted:false,callbackBufferHash:null};
   sentFrames.push(row);phase('SEND_INTENT',{label,eventId,rawBase64:bytes.toString('base64')});
   phase('SEND_INVOKE_ENTRY',{label,eventId});
   ws.send(bytes,{binary:false},error=>active(()=>{
    phase('SEND_CALLBACK_ENTRY',{label,eventId,error:error?String(error):null});
    check('send-callback');if(error)throw error;
    if(sha(bytes)!==framePin.sha256)throw Error('ACTUAL_SENT_BUFFER_MUTATION');
    row.sendCallbackCompleted=true;row.callbackBufferHash=sha(bytes);
    phase('SEND_CALLBACK_GUARD_PASSED',{label,eventId});maybeComplete();
   },error??null));
   row.sendInvoked=true;phase('SEND_INVOKE_RETURNED',{label,eventId});
  }
  try{
   ws=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
   // Install cleanup-safe error/close listeners before any diagnostic write.
   ws.on('error',error=>active(()=>{phase('SOCKET_ERROR_CALLBACK_ENTRY',{label,error:String(error)});finish(error);},error));
   ws.on('close',()=>{const error=Error('EARLY_RELAY_CLOSE');active(()=>{phase('SOCKET_CLOSE_CALLBACK_ENTRY',{label});finish(error);},error);});
   timer=arm(()=>{const error=Error('RELAY_TIMEOUT');active(()=>{phase('TIMER_FIRED',{label});finish(error);},error);},p.limits.networkTimeoutMilliseconds);
   phase('TIMER_ARMED',{label,timeoutMilliseconds:p.limits.networkTimeoutMilliseconds});
   ws.on('open',()=>active(()=>{
    phase('SOCKET_OPEN_CALLBACK_ENTRY',{label});check('socket-open');
    for(const event of events??[])sendKnown(['EVENT',event],event.id);
    if(filter)sendKnown(['REQ','e02-owned-query',filter],null);
   }));
   ws.on('message',data=>active(()=>{
    const bytes=Buffer.from(data);phase('RAW_BACKEND_CALLBACK_ENTRY',{label,rawBase64:bytes.toString('base64')});
    check('backend-message');const frame=strictJSON(bytes.toString('utf8'));
    phase('BACKEND_MESSAGE_GUARD_PASSED',{label,messageType:frame[0]});
    if(frame[0]==='OK'){ack.push({rawBase64:bytes.toString('base64'),frame});if(frame[2]!==true)throw Error('RELAY_REFUSAL');}
    if(frame[0]==='EVENT'&&frame[1]==='e02-owned-query')received.push({rawBase64:bytes.toString('base64'),frame});
    if(frame[0]==='EOSE'&&frame[1]==='e02-owned-query'){eose={rawBase64:bytes.toString('base64'),frame};queryEnded=true;}
    maybeComplete();
   }));
  }catch(error){finish(error);}
 });
}
