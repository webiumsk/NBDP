import { strictJSON } from './transport.mjs';
export function correlate(events){
 const envs=events.filter(e=>e.kind===14);if(!envs.length)return {state:'PENDING',operations:0,effects:0};
 const base=envs[0],e=strictJSON(base.content),d=e.document,file=e.files[0];
 const fail=state=>({state,operations:0,effects:0});if(envs.some(r=>r.id!==base.id))return fail('CONFLICT');let match=false;
 for(const r of events.filter(e=>e.kind===15)){
  const get=name=>{const tags=r.tags.filter(t=>t[0]===name);return tags.length===1?tags[0][1]:undefined};
  if(r.pubkey!==base.pubkey||JSON.stringify(r.tags.filter(t=>t[0]==='p'))!==JSON.stringify(base.tags.filter(t=>t[0]==='p')))return fail('CONFLICT');
  if(get('encryption-algorithm')!=='aes-gcm')return fail('UNSUPPORTED');if(get('e')!==base.id)continue;
  if(!/^[0-9a-f]{64}$/.test(get('decryption-key')??'')||!/^[0-9a-f]{24}$/.test(get('decryption-nonce')??'')||get('x')!==file.x||get('ox')!==d.sha256||get('file-type')!==d.media||get('size')!==file.size)return fail('CONFLICT');match=true;
 }
 return {state:match?'READY':'INCOMPLETE',operations:match?1:0,effects:0};
}
