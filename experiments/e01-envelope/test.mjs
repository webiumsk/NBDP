// Canonical E01: NIP-44 and full validation; requested envelope scope also exercised in E02.
import { readFileSync } from 'node:fs';
import { secret,hex,getPublicKey,getEventHash,finalizeEvent,createWrap,v2,rumor,wrap,sealRaw,envelope,validate,unwrapEvent } from '../shared/transport.mjs';
import { RustClient } from '../shared/rust-client.mjs';
import { digest } from '../shared/evidence.mjs';
export async function execute(ev){
 const rust=new RustClient();const a=secret(1),b=secret(2),pkA=getPublicKey(a),pkB=getPublicKey(b),third=getPublicKey(secret(3));
 try{
 const corpus=JSON.parse(readFileSync('fixtures/nip44.vectors.json')).v2;
 for(const [i,v] of corpus.valid.get_conversation_key.entries())await ev.check('conversation/'+i,async()=>{const js=hex(v2.utils.getConversationKey(Buffer.from(v.sec1,'hex'),v.pub2));const rs=await rust.call({op:'conversation',secret:v.sec1,to:v.pub2});ev.equal([js,rs],[v.conversation_key,v.conversation_key]);});
 for(const [i,v] of corpus.valid.encrypt_decrypt.entries())await ev.check('known-answer/'+i,async()=>{const ck=Buffer.from(v.conversation_key,'hex'),nonce=Buffer.from(v.nonce,'hex');const js=v2.encrypt(v.plaintext,ck,nonce);const rs=await rust.call({op:'vector-encrypt',key:v.conversation_key,nonce:v.nonce,plaintext:v.plaintext});ev.equal([js,rs],[v.payload,v.payload]);ev.equal(v2.decrypt(rs,ck),v.plaintext);ev.equal(await rust.call({op:'vector-decrypt',key:v.conversation_key,payload:js}),v.plaintext);});
 for(const [i,v] of corpus.invalid.get_conversation_key.entries())await ev.check('invalid-conversation/'+i,async()=>{let rejected=false;try{v2.utils.getConversationKey(Buffer.from(v.sec1,'hex'),v.pub2)}catch{rejected=true}ev.truth(rejected);ev.equal((await rust.raw({op:'conversation',secret:v.sec1,to:v.pub2})).ok,false);});
 for(const [i,v] of corpus.invalid.decrypt.entries())await ev.check('invalid-payload/'+i,async()=>{let rejected=false;try{v2.decrypt(v.payload,Buffer.from(v.conversation_key,'hex'))}catch{rejected=true}ev.truth(rejected);ev.equal((await rust.raw({op:'vector-decrypt',key:v.conversation_key,payload:v.payload})).ok,false);});
 for(const [length,padded] of corpus.valid.calc_padded_len)await ev.check('padding/'+length,async()=>{ev.equal(v2.utils.calcPaddedLen(length),padded);if(length<=1_000_000){const key='42'.repeat(32),nonce=length.toString(16).padStart(64,'0');const p=await rust.call({op:'vector-encrypt',key,nonce,plaintext:'x'.repeat(length)});ev.equal(Buffer.from(p,'base64').length-65-(length<65536?2:6),padded);}});
 for(const n of [1,31,32,33,65535,65536,65537,131070])await ev.check('cross-length/'+n,async()=>{const plaintext=n===131070?'ф'.repeat(65535):'x'.repeat(n);const js=v2.encrypt(plaintext,v2.utils.getConversationKey(a,pkB));ev.equal(await rust.call({op:'decrypt',secret:hex(b),from:pkA,payload:js}),plaintext);const rs=await rust.call({op:'encrypt',secret:hex(b),to:pkA,plaintext});ev.equal(v2.decrypt(rs,v2.utils.getConversationKey(a,pkB)),plaintext);return {bytes:Buffer.byteLength(plaintext),payload_bytes:js.length};});
 await ev.check('empty-encryption-rejected',async()=>{let no=false;try{v2.encrypt('',Buffer.alloc(32))}catch{no=true}ev.truth(no);ev.equal((await rust.raw({op:'encrypt',secret:hex(a),to:pkB,plaintext:''})).ok,false);});
 for(const [n,checksum] of [[65535,'6d8c2810d1e870fbaa1f0a0937126cca837a15f9260e27060c331d70a3c0bc84'],[65536,'b7b4edb36ba92e267d322d56d9aebc22e7fa96ff52e3c12adc07f07a43cbc616'],[65537,'eeb7c7c5373894ea2c1547cfd3ccb15d5a0b2d619da852e5c79df792dcc9e435']])await ev.check('pinned-boundary-known-answer/'+n,async()=>{const key='c41c775356fd92eadc63ff5a0dc1da211b268cbea22316767095b2871ea1412d',nonce='1'.padStart(64,'0'),plaintext='a'.repeat(n);const js=v2.encrypt(plaintext,Buffer.from(key,'hex'),Buffer.from(nonce,'hex')),rs=await rust.call({op:'vector-encrypt',key,nonce,plaintext});ev.equal(digest(Buffer.from(js,'utf8')),checksum);ev.equal(digest(Buffer.from(rs,'utf8')),checksum);ev.equal(await rust.call({op:'vector-decrypt',key,payload:js}),plaintext);ev.equal(v2.decrypt(rs,Buffer.from(key,'hex')),plaintext);return {checksum,source:'nostr-tools pinned nip44.test.ts; hash over UTF-8 base64 payload string'};});
 for(const v of corpus.valid.encrypt_decrypt_long_msg)await ev.check('retained-long-vector-independent-agreement',async()=>{const plaintext=v.letter.repeat(v.repeat),key=v.conversation_key,nonce=v.nonce;const js=v2.encrypt(plaintext,Buffer.from(key,'hex'),Buffer.from(nonce,'hex')),rs=await rust.call({op:'vector-encrypt',key,nonce,plaintext});ev.equal(js,rs);ev.equal(v2.decrypt(rs,Buffer.from(key,'hex')),plaintext);ev.equal(await rust.call({op:'vector-decrypt',key,payload:js}),plaintext);return {bytes:Buffer.byteLength(plaintext),payload_sha256:digest(Buffer.from(js,'base64')),published_checksum:v.payload_checksum_sha256,qualification:'Empty published checksum; independent agreement only. Supplemented by pinned boundary KATs.'};});
 ev.observations.push({legacy_go_control:'NOT EXECUTED: Go toolchain/control not installed; old Go 65535-byte limit is source evidence only, not a current runtime result',source:'See canonical plan G44 pinned source; not a second primary implementation'});
 const e=envelope(pkA,pkB);const r=rumor(e,pkA,pkB);const good=wrap(r,a,pkB);
 const cases=[];
 const put=(name,event,error,options={})=>cases.push({name,wire:typeof event==='string'?event:JSON.stringify(event),error,...options});
 put('positive-peer',good,null);
 put('positive-archive',wrap(r,a,pkA),null,{secret:hex(a),role:'archive'});
 put('wrong-role-archive',wrap(r,a,pkA),'recipient',{secret:hex(a)});
 put('outer-id',{...good,id:'0'.repeat(64)},'outer-auth');
 put('outer-signature',{...good,sig:'0'.repeat(128)},'outer-auth');
 put('outer-kind',{...good,kind:21059},'outer-kind');
 put('outer-recipient',{...good,tags:[['p',third]]},'recipient');
 put('outer-json','{"id":1,"id":2}','json');
 const seal=sealRaw(JSON.stringify(r),a,pkB);
 for(const [name,changed,error] of [['seal-kind',finalizeEvent({...seal,kind:12},a),'seal-kind'],['seal-tags',finalizeEvent({...seal,tags:[['expiration','9999999999']]},a),'seal-tags'],['seal-signature',{...seal,sig:'0'.repeat(128)},'seal-auth']])put(name,createWrap(changed,pkB),error);
 function inner(name,changed,error){put(name,createWrap(sealRaw(typeof changed==='string'?changed:JSON.stringify(changed),a,pkB),pkB),error);}
 inner('rumor-id',{...r,id:'0'.repeat(64)},'rumor-id');
 inner('signed-rumor',{...r,sig:'0'.repeat(128)},'structure');
 inner('author-mismatch',rumor(e,third,pkB),'author');
 inner('rumor-recipient',rumor(e,pkA,third),'recipient');
 inner('rumor-kind',rumor(e,pkA,pkB,{kind:1}),'rumor-kind');
 inner('rumor-json-duplicate',JSON.stringify(r).replace('"kind":14','"kind":14,"kind":14'),'json');
 inner('wrong-rumor-types',{...r,created_at:'1'},'structure');
 inner('excessive-tags',rumor(e,pkA,pkB,{tags:Array.from({length:65},()=>['p',pkB])}),'structure');
 for(const [name,change,error] of [['version',{version:99},'version'],['extension',{required:['unknown']},'extension'],['binding',{from:third},'binding'],['schema',{document:{...e.document,bytes:-1}},'schema']])inner(name,rumor({...e,...change},pkA,pkB),error);
 inner('envelope-duplicate-key',rumor(JSON.stringify(e).replace('"version":1','"version":1,"version":99'),pkA,pkB),'json');
 inner('json-depth',rumor('{"nested":'+ '['.repeat(33)+'0'+']'.repeat(33)+'}',pkA,pkB),'json');
 const cipher=Buffer.from(seal.content,'base64');cipher[0]=3;put('unsupported-crypto-version',createWrap(finalizeEvent({...seal,content:cipher.toString('base64')},a),pkB),'seal-crypto');
 const tamper=Buffer.from(seal.content,'base64');tamper[40]^=1;put('ciphertext-tamper',createWrap(finalizeEvent({...seal,content:tamper.toString('base64')},a),pkB),'seal-crypto');
 put('oversized-input','x'.repeat(20000),'resource');
 put('unauthorized-valid-sender',wrap(rumor(envelope(third,pkB),third,pkB),secret(3),pkB),'authorization');
 for(const [name,change,error] of [['unsafe-revision',{document:{...e.document,revision:9007199254740992}},'schema'],['null-file',{files:[null]},'schema'],['string-file',{files:['bogus']},'schema'],['bad-file-hash',{files:[{x:'bad',ox:'a'.repeat(64),size:'16'}]},'schema'],['too-many-files',{files:Array(17).fill({x:'a'.repeat(64),ox:'a'.repeat(64),size:'16'})},'schema']])inner(name,rumor({...e,...change},pkA,pkB),error);
 for(const [name,revision,error] of [['revision-one',1,null],['revision-safe-max',9007199254740991,null],['revision-zero',0,'schema'],['revision-negative',-1,'schema'],['revision-string','1','schema'],['revision-fractional',1.5,'json']])inner(name,rumor({...e,document:{...e.document,revision}},pkA,pkB),error);
 inner('decimal-version-token',rumor(JSON.stringify(e).replace('"version":1','"version":1.0'),pkA,pkB),'json');
 for(const c of cases)await ev.check('validation/'+c.name,async()=>{const key=Buffer.from(c.secret??hex(b),'hex'),options={role:c.role??'incoming',expectedSender:pkA};const js=validate(c.wire,key,options);const rs=await rust.call({op:'validate',wire:c.wire,secret:hex(key),...options});ev.equal(js,rs);ev.equal(js.ok,c.error===null);if(c.error)ev.equal(js.error,c.error);if(['outer-auth','recipient','outer-kind','json','resource'].includes(c.error)&&['outer-id','outer-signature','outer-recipient','outer-kind','outer-json','oversized-input'].includes(c.name))ev.equal(js.decrypts,[0,0]);if(c.name==='seal-signature')ev.equal(js.decrypts,[1,0]);return js;});
 await ev.check('rust-producer-js-consumer',async()=>{const rr=rumor(envelope(pkB,pkA,2),pkB,pkA);const event=await rust.call({op:'wrap',secret:hex(b),to:pkA,rumor:rr});const result=validate(JSON.stringify(event),a);ev.truth(result.ok);ev.equal(result.value.rumor,rr);ev.save('rust-positive-wrap.json',event);});
 // Observe helper boundaries separately, never use them as conformance validators.
 const bad={...good,sig:'0'.repeat(128)};let helperAccepted=false;try{unwrapEvent(bad,b);helperAccepted=true}catch{}
 ev.observations.push({name:'nostr-tools-helper-invalid-outer-signature',helperAccepted,strictAccepted:validate(JSON.stringify(bad),b).ok});
 ev.observations.push({name:'vector-scope',message_key_internal_vectors:'Rust API private; covered indirectly by exact ciphertext KATs',legacy_invalid_lengths:corpus.invalid.encrypt_msg_lengths,extended_lengths:'65536/65537 now valid under pinned NIP44; old corpus length labels not normative',long_vector_checksum:corpus.valid.encrypt_decrypt_long_msg[0].payload_checksum_sha256});
 ev.save('E01-validation-corpus.json',cases);ev.save('E01-positive-rumor.json',r);
 }finally{rust.close();}
}
