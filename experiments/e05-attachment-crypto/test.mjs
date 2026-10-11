import { BrowserCrypto,opensslEncrypt,opensslDecrypt,decode,NoncePlanner,consumeAttachment } from '../shared/attachment-crypto.mjs';
import { readFileSync } from 'node:fs';
import { digest } from '../shared/evidence.mjs';
export async function execute(ev){
 const producerEvidence=readFileSync('results/producer-profile-evidence.md','utf8');ev.observations.push({producer_inspection:'results/producer-profile-evidence.md',sha256:digest(producerEvidence),evidence_type:'pinned source inspection, no Amethyst runtime'});
 const browser=new BrowserCrypto();try{await browser.start();const vectors=[];
 const plainFixtures=[Buffer.alloc(16),Buffer.alloc(0),Buffer.from([0,255,128,1]),Buffer.from('Synthetic документ 🧾'),Buffer.alloc(65535,0x61),Buffer.alloc(65536,0x62)];
 const seen=new Map(),planner=new NoncePlanner();
 for(let i=0;i<plainFixtures.length;i++)await ev.check('cross-crypto/'+i,async()=>{
  const plain=plainFixtures[i],key=i===0?'00'.repeat(32):digest('public-disposable-key/'+i),nonce=i===0?'00'.repeat(12):digest('public-disposable-nonce/'+i).slice(0,24);
  const pair=key+nonce;ev.truth(!seen.has(pair));seen.set(pair,digest(plain));planner.claim(key,nonce,plain);
  const native=opensslEncrypt(key,nonce,plain),web=await browser.crypt('encrypt',key,nonce,plain.toString('hex'));ev.equal(web,native.toString('hex'));
  if(i===0)ev.equal(web,'cea7403d4d606b6e074ec5d3baf39d18d0d1c8a799996bf0265b98b5d48ab919');
  ev.equal(await browser.crypt('decrypt',key,nonce,native.toString('hex')),plain.toString('hex'));ev.equal(opensslDecrypt(key,nonce,Buffer.from(web,'hex')),plain);
  vectors.push({test_only:true,key,nonce,aad:'',plaintext_hex:plain.toString('hex'),blob_hex:web,plaintext_sha256:digest(plain),ciphertext_sha256:digest(native),plaintext_bytes:plain.length,blob_bytes:native.length});return {plaintext_bytes:plain.length,blob_bytes:native.length,plaintext_sha256:digest(plain),ciphertext_sha256:digest(native)};
 });
 const v=vectors[3];
 const flipped=hex=>{const b=Buffer.from(hex,'hex');b[0]^=1;return b.toString('hex')};
 const cases=[['ciphertext',v.key,v.nonce,flipped(v.blob_hex),''],['tag',v.key,v.nonce,v.blob_hex.slice(0,-2)+(v.blob_hex.endsWith('00')?'01':'00'),''],['key',flipped(v.key),v.nonce,v.blob_hex,''],['nonce',v.key,flipped(v.nonce),v.blob_hex,''],['aad',v.key,v.nonce,v.blob_hex,'01'],['truncated',v.key,v.nonce,v.blob_hex.slice(0,-2),''],['appended',v.key,v.nonce,v.blob_hex+'00',''],['short',v.key,v.nonce,'00','']];
 for(const [name,key,nonce,blob,aad] of cases)await ev.check('reject/'+name,async()=>{let web=false,native=false;try{await browser.crypt('decrypt',key,nonce,blob,aad)}catch{web=true}try{opensslDecrypt(key,nonce,Buffer.from(blob,'hex'),Buffer.from(aad,'hex'))}catch{native=true}ev.equal([web,native],[true,true]);});
 for(const [name,value,length] of [['upper-key',v.key.toUpperCase(),32],['base64-key',Buffer.from(v.key,'hex').toString('base64'),32],['short-key',v.key.slice(2),32],['short-nonce',v.nonce.slice(2),12]])await ev.check('encoding/'+name,()=>{let rejected=false;try{decode(value,length)}catch{rejected=true}ev.truth(rejected)});
 await ev.check('commitment-order-and-mirroring',()=>{const bytes=Buffer.from(v.blob_hex,'hex');ev.equal(digest(bytes),v.ciphertext_sha256);ev.truth(digest(bytes)!=='0'.repeat(64));const plaintext=opensslDecrypt(v.key,v.nonce,bytes);ev.equal(digest(plaintext),v.plaintext_sha256);ev.truth(digest(plaintext)!=='0'.repeat(64));ev.equal(Buffer.from(bytes),bytes);});
 await ev.check('nonce-planner-rejects-distinct-plaintext-reuse',()=>{let rejected=false;try{planner.claim(v.key,v.nonce,Buffer.from('other plaintext'))}catch{rejected=true}ev.truth(rejected);ev.truth(new Set(vectors.map(x=>x.key+x.nonce)).size===vectors.length);});
 for(const [name,patch] of [['wrong-ciphertext-hash',{x:'0'.repeat(64)}],['wrong-plaintext-hash',{ox:'0'.repeat(64)}],['wrong-plaintext-size',{bytes:v.plaintext_bytes+1}]])await ev.check('consumer-reject/'+name,async()=>{const input={key:v.key,nonce:v.nonce,blob:Buffer.from(v.blob_hex,'hex'),x:v.ciphertext_sha256,ox:v.plaintext_sha256,bytes:v.plaintext_bytes,...patch};let native=false,web=false;try{consumeAttachment(input)}catch{native=true}try{await browser.consume(input)}catch{web=true}ev.equal([native,web],[true,true]);});
 await ev.check('existing-producer-16-byte-nonce-not-silently-accepted',()=>{let rejected=false;try{decode('00'.repeat(16),12)}catch{rejected=true}ev.truth(rejected);});
 await ev.check('retry-mirror-revision-planning',()=>{const original=Buffer.from(v.plaintext_hex,'hex'),saved=Buffer.from(v.blob_hex,'hex');planner.claim(v.key,v.nonce,original);const retry=Buffer.from(saved),mirror=Buffer.from(saved);ev.equal(retry,saved);ev.equal(mirror,saved);const revised=Buffer.from('public synthetic revision'),key=digest('public disposable revision key'),nonce=digest('public disposable revision nonce').slice(0,24);ev.truth(key+nonce!==v.key+v.nonce);planner.claim(key,nonce,revised);return {retry:'stored ciphertext',mirror:'identical stored bytes',revision:'different key/nonce; no unsafe encryption executed'};});
 ev.save('E05-aes-gcm-vectors.json',vectors);
 ev.observations.push({known_answer_source:'https://boringssl.googlesource.com/boringssl/+/e8c862cf1421/crypto/cipher/test/aes_256_gcm_tests.txt',browser_version:await browser.browser.version(),requests:browser.requests,profile:{key_bytes:32,nonce_bytes:12,tag_bytes:16,aad:'empty',layout:'ciphertext || tag',encoding:'lowercase hex'},producers:['browser Web Crypto candidate','Node OpenSSL EVP candidate'],thumbnails:'not implemented',ecosystem_compatibility:'not established by crypto-only test'});
 }finally{await browser.close();}
}
