// Producer4 observer: raw callback context is local to each guarded continuation.
import {exchange} from './exchange.mjs';
export async function observedExchange(base,events,filter,label){
 const pins=new Map();
 const phase=(name,fields={})=>{
  const row=base.phase(name,fields);
  if(name==='SEND_INTENT'){
   const bytes=Buffer.from(fields.rawBase64,'base64'),frame=pins.get(base.sha(bytes));
   if(!frame||frame.bytes!==bytes.length)throw Error('ACTUAL_SENT_FRAME_PIN_REQUIRED');
   base.log({direction:'PRODUCER_TO_RELAY',exchangeLabel:label,rawBase64:fields.rawBase64,frame});
  }
  return row;
 };
 phase.state=base.phase.state;
 const afterBackendGuard=bytes=>base.log({direction:'RELAY_TO_PRODUCER',exchangeLabel:label,rawBase64:bytes.toString('base64')});
 const put=(name,bytes)=>{const descriptor=base.put(name,bytes);if(name.endsWith('-sent-frame.json'))pins.set(base.sha(bytes),descriptor);return descriptor;};
 return await exchange({...base,phase,put,afterBackendGuard},events,filter,label);
}
