// Experimental JavaScript adapter over the TypeScript-authored nostr-tools package.
// No crypto primitive is implemented here. Never use public fixtures for real data.
import { getPublicKey, getEventHash, finalizeEvent, verifyEvent } from 'nostr-tools/pure';
import { createSeal, createWrap, unwrapEvent } from 'nostr-tools/nip59';
import { v2 } from 'nostr-tools/nip44';
export { getPublicKey, getEventHash, finalizeEvent, createSeal, createWrap, unwrapEvent, v2 };
export const secret = n => Uint8Array.from(Buffer.from(n.toString(16).padStart(64, '0'), 'hex'));
export const hex = x => Buffer.from(x).toString('hex');
const assert = (ok, reason) => { if (!ok) throw Error(reason); };
const ishex = (s,n) => typeof s==='string' && s.length===n && /^[0-9a-f]+$/.test(s);

export function strictJSON(text) {
  assert(Buffer.byteLength(text)<=2_000_000, 'resource');
  const stack=[];
  // Scan raw JSON strings and container boundaries before parsing; escaped keys compare decoded.
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(c==='"') {
      const start=i++;
      while(i<text.length) { if(text[i]==='\\') {i+=2;continue;} if(text[i]==='"')break;i++; }
      let next=i+1; while(/\s/.test(text[next]??'X')) next++;
      if(text[next]===':') { const frame=stack.at(-1);assert(frame?.type==='{','json');const key=JSON.parse(text.slice(start,i+1));assert(!frame.keys.has(key),'json');frame.keys.add(key); }
    } else if(/[-0-9]/.test(c)){let end=i+1;while(end<text.length&&!/[\s,}\]]/.test(text[end]))end++;assert(/^(0|[1-9][0-9]*|-[1-9][0-9]*)$/.test(text.slice(i,end)),'json');i=end-1;}
    else if(c==='{'||c==='[') { stack.push({type:c,keys:new Set()});assert(stack.length<=32,'json'); }
    else if(c==='}'||c===']') { const f=stack.pop();assert(f?.type===(c==='}'?'{':'['),'json'); }
  }
  assert(stack.length===0,'json');
  try{return JSON.parse(text);}catch{throw Error('json');}
}
function shape(e,signed) {
  const fields=['id','pubkey','created_at','kind','tags','content',...(signed?['sig']:[])];
  assert(e&&typeof e==='object'&&!Array.isArray(e)&&Object.keys(e).length===fields.length&&fields.every(k=>Object.hasOwn(e,k)),'structure');
  assert(ishex(e.id,64)&&ishex(e.pubkey,64)&&(!signed||ishex(e.sig,128)),'structure');
  assert(Number.isSafeInteger(e.kind)&&e.kind>=0&&e.kind<=65535&&Number.isSafeInteger(e.created_at)&&e.created_at>=0&&typeof e.content==='string','structure');
  assert(Array.isArray(e.tags)&&e.tags.length<=64&&e.tags.every(t=>Array.isArray(t)&&t.length<=8&&t.every(x=>typeof x==='string')),'structure');
}
const ps=r=>r.tags.filter(t=>t[0]==='p').map(t=>t[1]);
function schema(e,r) {
  assert(e.version===1,'version');assert(JSON.stringify(e.required)==='[]','extension');
  assert(e.type==='document'&&e.context==='synthetic','schema');
  assert(ishex(e.id,64)&&e.from===r.pubkey&&e.to===ps(r)[0],'binding');
  const allowed=['protocol','version','type','id','from','to','context','required','document','files','note'];
  assert(Object.keys(e).every(k=>allowed.includes(k)),'schema');
  const d=e.document;
  assert(d&&Object.keys(d).length===5&&ishex(d.id,64)&&ishex(d.sha256,64)&&Number.isSafeInteger(d.bytes)&&d.bytes>=0&&d.bytes<=1_048_576&&Number.isSafeInteger(d.revision)&&d.revision>0&&typeof d.media==='string'&&d.media.length>0,'schema');
  if(Object.hasOwn(e,'files')) assert(Array.isArray(e.files)&&e.files.length<=16&&e.files.every(f=>f&&typeof f==='object'&&!Array.isArray(f)&&Object.keys(f).length===3&&ishex(f.x,64)&&ishex(f.ox,64)&&typeof f.size==='string'&&/^[1-9][0-9]*$/.test(f.size)&&Number(f.size)>=16&&Number(f.size)<=1_048_592),'schema');
  if(Object.hasOwn(e,'note')) assert(typeof e.note==='string','schema');
}
export function validate(wire,key,{role='incoming',cap=16384,expectedSender}={}) {
  const decrypts=[0,0];
  try {
    assert(Buffer.byteLength(wire)+10<=cap,'resource');
    const w=strictJSON(wire);shape(w,true);assert(w.kind===1059,'outer-kind');const local=getPublicKey(key);
    assert(JSON.stringify(w.tags)===JSON.stringify([['p',local]]),'recipient');
    // Parse into a fresh object. finalizeEvent/verifyEvent cache state must never be trusted after mutation.
    assert(verifyEvent(w),'outer-auth');decrypts[0]++;
    let sealText;try{sealText=v2.decrypt(w.content,v2.utils.getConversationKey(key,w.pubkey));}catch{throw Error('outer-crypto');}
    const s=strictJSON(sealText);
    shape(s,true);assert(s.kind===13,'seal-kind');assert(s.tags.length===0,'seal-tags');assert(verifyEvent(s),'seal-auth');decrypts[1]++;
    let rumorText;try{rumorText=v2.decrypt(s.content,v2.utils.getConversationKey(key,s.pubkey));}catch{throw Error('seal-crypto');}
    const r=strictJSON(rumorText);
    shape(r,false);assert([14,15].includes(r.kind),'rumor-kind');assert(getEventHash(r)===r.id,'rumor-id');assert(r.pubkey===s.pubkey,'author');
    const recipients=ps(r);assert(recipients.length===1&&ishex(recipients[0],64),'recipient');
    assert(role==='archive'?r.pubkey===local:recipients[0]===local,'recipient');
    if(expectedSender)assert(r.pubkey===expectedSender,'authorization');
    if(r.kind===15)return {ok:true,value:{rumor:r,dispatch:false,role:role==='archive'?'archive':'file'},decrypts};
    const e=r.content.startsWith('{')?strictJSON(r.content):null;
    if(e?.protocol!=='NBDP/experiment')return {ok:true,value:{rumor:r,dispatch:false,role:'chat'},decrypts};
    schema(e,r);
    return {ok:true,value:{rumor:r,envelope:e,dispatch:role!=='archive',role:role==='archive'?'archive':'incoming'},decrypts};
  }catch(e){return {ok:false,error:e.message,decrypts};}
}
export function rumor(envelope,from,to,{kind=14,tags=[['p',to]],timestamp=Math.floor(Date.now()/1000)}={}) {
  const r={pubkey:from,created_at:timestamp,kind,tags,content:typeof envelope==='string'?envelope:JSON.stringify(envelope)};
  return {...r,id:getEventHash(r)};
}
export function wrap(r,key,to){return createWrap(createSeal(r,key,to),to);}
export function sealRaw(raw,key,to,patch={}) {
  return finalizeEvent({kind:13,created_at:Math.floor(Date.now()/1000)-60,tags:[],content:v2.encrypt(raw,v2.utils.getConversationKey(key,to)),...patch},key);
}
export function envelope(from,to,n=1) {
  return {protocol:'NBDP/experiment',version:1,type:'document',id:n.toString(16).padStart(64,'0'),from,to,context:'synthetic',required:[],document:{id:'d'.repeat(64),revision:1,sha256:'a'.repeat(64),bytes:7,media:'application/octet-stream'}};
}
