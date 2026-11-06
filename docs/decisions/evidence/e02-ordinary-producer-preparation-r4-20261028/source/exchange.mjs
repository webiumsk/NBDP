// Producer4 async fresh guards. Terminal callbacks fence immediately outside queue.
export async function exchange(ctx,events,filter,label){
 const {WebSocket,p,guard,phase,put,strictJSON,sha,clock,arm,clear}=ctx;
 let started;
 await guard('exchange:'+label+':exchange-entry',Buffer.from(label),()=>{
  if(typeof label!=='string'||!/^[a-z0-9-]{1,48}$/.test(label))throw Error('FIXED_EXCHANGE_LABEL');
  started=clock();phase('EXCHANGE_START',{label});
 });
 return await new Promise((resolve,reject)=>{
  let ws=null,timer=null,terminalClaimed=false,terminationAttempted=false,open=false;
  const deadline=clock()+BigInt(p.limits.networkTimeoutMilliseconds)*1000000n;
  const handshakeDeadline=clock()+3000000000n;
  const ack=[],received=[],sentFrames=[];let queryEnded=false,eose=null;
  const valid=()=>!terminalClaimed;
  function finish(incomingError,priorSecondary=[]){
   if(terminalClaimed)return;terminalClaimed=true;
   let first=incomingError??null;const secondary=[...priorSecondary];
   const note=(stage,error)=>{if(first===null)first=error;else secondary.push({stage,error:String(error)});};
   const attempt=(stage,fn)=>{try{return fn();}catch(error){note(stage,error);}};
   let elapsedNanoseconds=null;
   try{
    attempt('terminal-clock',()=>{elapsedNanoseconds=Number(clock()-started);});
    if(timer!==null)attempt('clear-timer',()=>clear(timer));
    attempt('terminal-phase',()=>phase(first===null?'EXCHANGE_RESOLVED':'EXCHANGE_REJECTED',{label,elapsedNanoseconds,error:first===null?null:String(first)}));
    attempt('terminal-outcome',()=>put(label+'-outcome.json',Buffer.from(JSON.stringify({label,elapsedNanoseconds,ack,received,eose,sentFrames,error:first===null?null:String(first),secondaryRetentionErrors:secondary,observer:typeof phase.state==='function'?phase.state():null},null,2)+'\n')));
   }catch(error){note('terminal-boundary',error);}
   finally{
    if(ws!==null&&!terminationAttempted){terminationAttempted=true;attempt('terminate-owned-socket',()=>ws.terminate());}
    if(first!==null){ctx.fail(first);reject(first);}else resolve({ack,received,eose,sentFrames,elapsedNanoseconds});
   }
  }
  function active(fn,incomingFault=null){
   if(terminalClaimed)return;
   // Incoming socket faults deny immediately; no wait for fresh guard or queue.
   if(incomingFault!==null){finish(incomingFault);return;}
   try{Promise.resolve(fn()).catch(error=>finish(error));}catch(error){finish(error);}
  }
  function segment(position,context,fn,extra=()=>true,additional=[]){
   return guard('exchange:'+label+':'+position,context,fn,{valid:()=>valid()&&extra(),deadlines:[deadline,...additional]});
  }
  function maybeComplete(){
   if(!sentFrames.length||!sentFrames.every(row=>row.sendCallbackCompleted))return;
   if(events&&events.every(event=>ack.some(row=>row.frame[1]===event.id&&row.frame[2]===true)))finish();
   else if(filter&&queryEnded)finish();
  }
  async function sendKnown(frame,eventId){
   const bytes=Buffer.from(JSON.stringify(frame)),bufferHash=sha(bytes);
   await segment('send-before',bytes,()=>{
    const framePin=put(label+'-'+sentFrames.length+'-sent-frame.json',bytes);
    const row={frame:framePin,eventId,messageType:frame[0],sendInvoked:false,sendCallbackCompleted:false,callbackBufferHash:null};
    sentFrames.push(row);phase('SEND_INTENT',{label,eventId,rawBase64:bytes.toString('base64')});phase('SEND_INVOKE_ENTRY',{label,eventId});
    ws.send(bytes,{binary:false},error=>active(()=>{
     phase('SEND_CALLBACK_ENTRY',{label,eventId,error:error?String(error):null});
     return segment('send-callback',bytes,()=>{
      if(sha(bytes)!==framePin.sha256)throw Error('ACTUAL_SENT_BUFFER_MUTATION');
      row.sendCallbackCompleted=true;row.callbackBufferHash=sha(bytes);phase('SEND_CALLBACK_GUARD_PASSED',{label,eventId});maybeComplete();
     },()=>sha(bytes)===bufferHash);
    },error??null));
    row.sendInvoked=true;phase('SEND_INVOKE_RETURNED',{label,eventId});
   },()=>ws!==null&&open&&sha(bytes)===bufferHash);
  }
  try{
   // Constructor is a protected effect, still at original exchange-entry boundary.
   active(()=>segment('constructor',Buffer.from(p.backendUrl),()=>{
    ws=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
    ws.on('error',error=>finish(error));
    ws.on('close',()=>{if(!terminalClaimed)finish(Error('EARLY_RELAY_CLOSE'));});
    ws.on('open',()=>active(async()=>{
     phase('SOCKET_OPEN_CALLBACK_ENTRY',{label});
     await segment('socket-open',Buffer.from(label),()=>{open=true;},()=>ws!==null,[handshakeDeadline]);
     for(const event of events??[])await sendKnown(['EVENT',event],event.id);
     if(filter)await sendKnown(['REQ','e02-owned-query',filter],null);
    }));
    ws.on('message',data=>active(()=>{
     const bytes=Buffer.from(data),hash=sha(bytes);phase('RAW_BACKEND_CALLBACK_ENTRY',{label,rawBase64:bytes.toString('base64')});
     return segment('backend-message',bytes,()=>{
      if(sha(bytes)!==hash)throw Error('ACTUAL_BACKEND_BUFFER_MUTATION');
      ctx.afterBackendGuard?.(bytes);const frame=strictJSON(bytes.toString('utf8'));phase('BACKEND_MESSAGE_GUARD_PASSED',{label,messageType:frame[0]});
      if(frame[0]==='OK'){ack.push({rawBase64:bytes.toString('base64'),frame});if(frame[2]!==true)throw Error('RELAY_REFUSAL');}
      if(frame[0]==='EVENT'&&frame[1]==='e02-owned-query')received.push({rawBase64:bytes.toString('base64'),frame});
      if(frame[0]==='EOSE'&&frame[1]==='e02-owned-query'){eose={rawBase64:bytes.toString('base64'),frame};queryEnded=true;}
      maybeComplete();
     },()=>sha(bytes)===hash);
    }));
   }));
   timer=arm(()=>{if(terminalClaimed)return;try{phase('TIMER_FIRED',{label});}catch{}finish(Error('RELAY_TIMEOUT'));},p.limits.networkTimeoutMilliseconds);
   phase('TIMER_ARMED',{label,timeoutMilliseconds:p.limits.networkTimeoutMilliseconds});
  }catch(error){finish(error);}
 });
}
