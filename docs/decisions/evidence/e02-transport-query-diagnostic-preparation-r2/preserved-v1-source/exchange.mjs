// SOURCE-only instrumented sibling of the exact original exchange.
// Dependencies are explicit for synthetic model tests; runtime binds only reviewed
// real ws, unchanged sync lease guard, process.hrtime, and built-in timers.
export async function exchange(ctx,events,filter,label){
 const {WebSocket,p,check,phase,put,strictJSON,sha,clock,arm,clear}=ctx;
 check('exchange-entry');
 if(typeof label!=='string'||!/^[a-z0-9-]{1,48}$/.test(label))throw Error('FIXED_EXCHANGE_LABEL');
 const started=clock();phase('EXCHANGE_START',{label});
 return await new Promise((resolve,reject)=>{
  const ws=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
  const ack=[],received=[],sentFrames=[];let settled=false,queryEnded=false,eose=null;
  const timer=arm(()=>{phase('TIMER_FIRED',{label});finish(Error('RELAY_TIMEOUT'));},p.limits.networkTimeoutMilliseconds);
  phase('TIMER_ARMED',{label,timeoutMilliseconds:p.limits.networkTimeoutMilliseconds});
  function finish(error){
   if(settled)return;settled=true;clear(timer);
   // Terminal evidence is retained even when a guard refused; cleanup touches
   // only this owned socket. No new send/forward/validation is authorized here.
   const elapsedNanoseconds=Number(clock()-started);
   const outcome={label,elapsedNanoseconds,ack,received,eose,sentFrames,error:error?String(error):null};
   phase(error?'EXCHANGE_REJECTED':'EXCHANGE_RESOLVED',{label,elapsedNanoseconds,error:error?String(error):null});
   put(label+'-outcome.json',Buffer.from(JSON.stringify(outcome,null,2)+'\n'));
   ws.terminate();
   if(error){reject(error);return;}
   resolve({ack,received,eose,sentFrames,elapsedNanoseconds});
  }
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
   // An intent record is explicitly not a completed send callback/backend receipt.
   phase('SEND_INVOKE_ENTRY',{label,eventId});
   ws.send(bytes,{binary:false},error=>{try{
    phase('SEND_CALLBACK_ENTRY',{label,eventId,error:error?String(error):null});
    if(settled){phase('TERMINAL_CALLBACK_CONTEXT_ONLY',{label});return;}
    check('send-callback');if(error)throw error;
    if(sha(bytes)!==framePin.sha256)throw Error('ACTUAL_SENT_BUFFER_MUTATION');
    row.sendCallbackCompleted=true;row.callbackBufferHash=sha(bytes);
    phase('SEND_CALLBACK_GUARD_PASSED',{label,eventId});maybeComplete();
   }catch(error){finish(error);}});
   row.sendInvoked=true;phase('SEND_INVOKE_RETURNED',{label,eventId});
  }
  ws.on('open',()=>{try{
   phase('SOCKET_OPEN_CALLBACK_ENTRY',{label});
   if(settled){phase('TERMINAL_CALLBACK_CONTEXT_ONLY',{label});return;}
   check('socket-open');for(const event of events??[])sendKnown(['EVENT',event],event.id);
   if(filter)sendKnown(['REQ','e02-owned-query',filter],null);
  }catch(error){finish(error);}});
  ws.on('message',data=>{try{
   const bytes=Buffer.from(data);
   phase('RAW_BACKEND_CALLBACK_ENTRY',{label,rawBase64:bytes.toString('base64')});
   if(settled){phase('TERMINAL_CALLBACK_CONTEXT_ONLY',{label});return;}
   check('backend-message');
   const frame=strictJSON(bytes.toString('utf8'));phase('BACKEND_MESSAGE_GUARD_PASSED',{label,messageType:frame[0]});
   if(frame[0]==='OK'){ack.push({rawBase64:bytes.toString('base64'),frame});if(frame[2]!==true)throw Error('RELAY_REFUSAL');}
   if(frame[0]==='EVENT'&&frame[1]==='e02-owned-query')received.push({rawBase64:bytes.toString('base64'),frame});
   if(frame[0]==='EOSE'&&frame[1]==='e02-owned-query'){eose={rawBase64:bytes.toString('base64'),frame};queryEnded=true;}
   maybeComplete();
  }catch(error){finish(error);}});
  ws.on('error',error=>{phase('SOCKET_ERROR_CALLBACK_ENTRY',{label,error:String(error)});finish(error);});
  ws.on('close',()=>{phase('SOCKET_CLOSE_CALLBACK_ENTRY',{label});if(!settled)finish(Error('EARLY_RELAY_CLOSE'));});
 });
}
