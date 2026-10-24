 async function exchange(events,filter,label){
  check();need(typeof label==='string'&&/^[a-z0-9-]{1,48}$/.test(label),'FIXED_EXCHANGE_LABEL');
  const started=process.hrtime.bigint();
  return await new Promise((resolve,reject)=>{
   const ws=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
   const ack=[],received=[],sentFrames=[];let settled=false,queryEnded=false,eose=null;
   const timer=setTimeout(()=>finish(Error('RELAY_TIMEOUT')),p.limits.networkTimeoutMilliseconds);
   function finish(error){
    if(settled)return;settled=true;clearTimeout(timer);ws.terminate();
    const elapsedNanoseconds=Number(process.hrtime.bigint()-started);
    if(error){reject(error);return;}
    resolve({ack,received,eose,sentFrames,elapsedNanoseconds});
   }
   function maybeComplete(){
    if(!sentFrames.length||!sentFrames.every(row=>row.sendCallbackCompleted))return;
    if(events&&events.every(event=>ack.some(row=>row.frame[1]===event.id&&row.frame[2]===true)))finish();
    else if(filter&&queryEnded)finish();
   }
   function sendKnown(frame,eventId){
    check();const bytes=Buffer.from(JSON.stringify(frame));
    const framePin=put(DIR+'/'+label+'-'+sentFrames.length+'-sent-frame.json',bytes);
    const row={frame:framePin,eventId,messageType:frame[0],sendInvoked:true,sendCallbackCompleted:false,callbackBufferHash:null};
    sentFrames.push(row);
    log({direction:'PRODUCER_TO_RELAY',exchangeLabel:label,rawBase64:bytes.toString('base64'),frame:framePin});
    ws.send(bytes,{binary:false},error=>{try{
     check();if(error)throw error;
     need(sha(bytes)===framePin.sha256,'ACTUAL_SENT_BUFFER_MUTATION');
     row.sendCallbackCompleted=true;row.callbackBufferHash=sha(bytes);maybeComplete();
    }catch(error){finish(error);}});
   }
   ws.on('open',()=>{try{
    check();for(const event of events??[])sendKnown(['EVENT',event],event.id);
    if(filter)sendKnown(['REQ','e02-owned-query',filter],null);
   }catch(error){finish(error);}});
   ws.on('message',data=>{try{
    check();const bytes=Buffer.from(data);
    log({direction:'RELAY_TO_PRODUCER',exchangeLabel:label,rawBase64:bytes.toString('base64')});
    const frame=T.strictJSON(bytes.toString('utf8'));
    if(frame[0]==='OK'){ack.push({rawBase64:bytes.toString('base64'),frame});need(frame[2]===true,'RELAY_REFUSAL');}
    if(frame[0]==='EVENT'&&frame[1]==='e02-owned-query')received.push({rawBase64:bytes.toString('base64'),frame});
    if(frame[0]==='EOSE'&&frame[1]==='e02-owned-query'){eose={rawBase64:bytes.toString('base64'),frame};queryEnded=true;}
    maybeComplete();
   }catch(error){finish(error);}});
   ws.on('error',finish);ws.on('close',()=>{if(!settled)finish(Error('EARLY_RELAY_CLOSE'));});
  });
 }
