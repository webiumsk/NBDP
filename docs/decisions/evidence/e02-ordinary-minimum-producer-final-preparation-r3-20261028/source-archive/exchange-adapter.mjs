// Versioned adapter around accepted SOURCE2 exchange; protocol module unchanged.
// Preserve original producer proxy-row schema and original guard positions.
import {exchange} from './exchange.mjs';
export async function observedExchange(base,events,filter,label){
 let pendingRaw=null;
 const pins=new Map();
 const phase=(name,fields={})=>{
  const row=base.phase(name,fields);
  if(name==='SEND_INTENT'){
   const bytes=Buffer.from(fields.rawBase64,'base64'),frame=pins.get(base.sha(bytes));
   if(!frame||frame.bytes!==bytes.length)throw Error('ACTUAL_SENT_FRAME_PIN_REQUIRED');
   base.log({direction:'PRODUCER_TO_RELAY',exchangeLabel:label,rawBase64:fields.rawBase64,frame});
  }
  if(name==='RAW_BACKEND_CALLBACK_ENTRY'){
   if(pendingRaw!==null)throw Error('UNCONSUMED_BACKEND_CALLBACK_CONTEXT');
   pendingRaw=fields.rawBase64;
  }
  return row;
 };
 phase.state=base.phase.state;
 const check=position=>{
  base.check('exchange:'+label+':'+position); // Exactly one original guard call.
  if(position==='backend-message'){
   if(pendingRaw===null)throw Error('RAW_BACKEND_CONTEXT_REQUIRED');
   base.log({direction:'RELAY_TO_PRODUCER',exchangeLabel:label,rawBase64:pendingRaw});
   pendingRaw=null; // Original raw row is after guard, before protocol parse.
  }
 };
 const put=(name,bytes)=>{const descriptor=base.put(name,bytes);if(name.endsWith('-sent-frame.json'))pins.set(base.sha(bytes),descriptor);return descriptor;};
 return await exchange({...base,phase,check,put},events,filter,label);
}
