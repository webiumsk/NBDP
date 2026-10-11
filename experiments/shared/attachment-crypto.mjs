import { createCipheriv, createDecipheriv,createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
export function decode(s,n){if(typeof s!=='string'||s.length!==n*2||!/^[0-9a-f]*$/.test(s))throw Error('encoding');return Buffer.from(s,'hex');}
export function opensslEncrypt(key,nonce,plain,aad=Buffer.alloc(0)){
 const cipher=createCipheriv('aes-256-gcm',decode(key,32),decode(nonce,12),{authTagLength:16});cipher.setAAD(aad);
 return Buffer.concat([cipher.update(plain),cipher.final(),cipher.getAuthTag()]);
}
export function opensslDecrypt(key,nonce,blob,aad=Buffer.alloc(0)){
 if(blob.length<16)throw Error('truncated');
 const cipher=createDecipheriv('aes-256-gcm',decode(key,32),decode(nonce,12),{authTagLength:16});cipher.setAAD(aad);cipher.setAuthTag(blob.subarray(-16));
 // Never expose update() plaintext until authentication succeeds in final().
 const temp=cipher.update(blob.subarray(0,-16));return Buffer.concat([temp,cipher.final()]);
}
export class NoncePlanner{
 constructor(){this.records=new Map();}
 claim(key,nonce,plaintext){decode(key,32);decode(nonce,12);const id=key+nonce,hash=createHash('sha256').update(plaintext).digest('hex');if(this.records.has(id)&&this.records.get(id)!==hash)throw Error('distinct-plaintext nonce reuse');this.records.set(id,hash);}
}
export function consumeAttachment({key,nonce,blob,x,ox,bytes}){
 const hash=b=>createHash('sha256').update(b).digest('hex');
 if(blob.length>1_048_592||blob.length<16||hash(blob)!==x)throw Error('ciphertext commitment');
 const plain=opensslDecrypt(key,nonce,blob);if(plain.length!==bytes||hash(plain)!==ox)throw Error('plaintext commitment');return plain;
}
export class BrowserCrypto{
 async start(){
  this.server=createServer((req,res)=>{res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'");res.end('<!doctype html><title>NBDP synthetic crypto lab</title>');});
  await new Promise(resolve=>this.server.listen(0,'127.0.0.1',resolve));const port=this.server.address().port;
  this.browser=await chromium.launch({executablePath:process.env.NBDP_CHROME??'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost']});
  this.context=await this.browser.newContext();this.requests=[];
  await this.context.route('**/*',route=>{const url=route.request().url();this.requests.push(url);return url.startsWith('http://127.0.0.1:'+port+'/')?route.continue():route.abort();});
  this.page=await this.context.newPage();await this.page.goto('http://127.0.0.1:'+port+'/');
 }
 async crypt(op,key,nonce,data,aad=''){
  decode(key,32);decode(nonce,12);
  return this.page.evaluate(async({op,key,nonce,data,aad})=>{
   const b=s=>Uint8Array.from(s.match(/../g)??[],x=>parseInt(x,16));
   const k=await crypto.subtle.importKey('raw',b(key),'AES-GCM',false,[op]);
   const out=await crypto.subtle[op]({name:'AES-GCM',iv:b(nonce),additionalData:b(aad),tagLength:128},k,b(data));
   return Array.from(new Uint8Array(out),v=>v.toString(16).padStart(2,'0')).join('');
  },{op,key,nonce,data,aad});
 }
 async consume({key,nonce,blob,x,ox,bytes}){
  decode(key,32);decode(nonce,12);
  return this.page.evaluate(async({key,nonce,blob,x,ox,bytes})=>{
   const b=s=>Uint8Array.from(s.match(/../g)??[],h=>parseInt(h,16));const hex=a=>Array.from(new Uint8Array(a),v=>v.toString(16).padStart(2,'0')).join('');
   const data=b(blob);if(data.length<16||data.length>1048592||hex(await crypto.subtle.digest('SHA-256',data))!==x)throw Error('ciphertext commitment');
   const k=await crypto.subtle.importKey('raw',b(key),'AES-GCM',false,['decrypt']);const p=await crypto.subtle.decrypt({name:'AES-GCM',iv:b(nonce),tagLength:128},k,data);
   if(p.byteLength!==bytes||hex(await crypto.subtle.digest('SHA-256',p))!==ox)throw Error('plaintext commitment');return hex(p);
  },{key,nonce,blob:blob.toString('hex'),x,ox,bytes});
 }
 async close(){await this.browser?.close();if(this.server)await new Promise(resolve=>this.server.close(resolve));}
}
