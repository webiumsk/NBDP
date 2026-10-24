// SOURCE ONLY: one synthetic ordinary-client envelope cell; no E02 PASS claim.
import fs from 'node:fs';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';

const DIR='/session/fixtures', PLAN='/input/fixture-plan.json';
const A='79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798';
const B='c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5';
const CASE='js-to-rust-incoming-rs', SOCKET=DIR+'/control.sock';
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const same=(a,b)=>typeof a===typeof b&&(a===null||b===null?a===b:Array.isArray(a)||Array.isArray(b)?Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>same(x,b[i])):typeof a==='object'?Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>Object.hasOwn(b,k)&&same(a[k],b[k])):a===b);
function need(v,why){if(!v)throw Error(why);}
function pin(path){const s=fs.lstatSync(path);need(s.isFile()&&!s.isSymbolicLink(),'REGULAR_FILE');const raw=fs.readFileSync(path);return {path,bytes:raw.length,sha256:sha(raw)};}
function raw(path){const b=fs.readFileSync(path);need(b.length<=16777216,'DATA_BOUND');return b;}
function doc(path){return JSON.parse(raw(path));}
function put(path,data){const b=Buffer.isBuffer(data)?data:Buffer.from(data);need(b.length<=16777216,'WRITE_BOUND');fs.writeFileSync(path,b,{flag:'wx',mode:0o600});return pin(path);}
function putJSON(name,value){return put(DIR+'/'+name,JSON.stringify(value,null,2)+'\n');}
function check(){
 const expected=process.env.NBDP_LEASE_SHA256;need(/^[0-9a-f]{64}$/.test(expected??''),'EXTERNAL_LEASE_SHA');
 const argv=['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/lease_guard.py','check',expected];
 const r=spawnSync('/guard-python/lib/ld-linux-x86-64.so.2',argv,{env:process.env,timeout:5000,maxBuffer:1048576});
 need(!r.error&&r.status===0&&r.signal===null,'FINITE_LEASE_DENIED:'+String(r.stderr??'').slice(0,2048));
}
function plan(){
 const b=raw(PLAN);need(sha(b)===process.env.NBDP_FIXTURE_PLAN_SHA256,'EXTERNAL_FIXTURE_PLAN_SHA');const p=JSON.parse(b);
 need(p.schema==='e02-single-cell-fixture-plan-v1'&&p.caseId===CASE&&p.direction==='JS_TO_RUST'&&p.role==='incoming'&&p.relay==='rs-relay'&&p.senderScalar===1&&p.recipientScalar===2&&p.envelopeNumber===10&&p.proxyUrl==='ws://127.0.0.1:17777'&&p.backendUrl==='ws://127.0.0.1:8080'&&p.output===DIR,'FIXED_FIRST_SLICE');
 need(Array.isArray(p.dependencyFiles)&&p.dependencyFiles.length>0&&p.dependencyFiles.length<=4096,'PINNED_INSTALLED_DEPENDENCIES');for(const d of [...Object.values(p.pins),...p.dependencyFiles]){const q=pin(d.path);need(q.bytes===d.bytes&&q.sha256===d.sha256,'CURRENT_SOURCE_BINARY_PIN');}
 const e01=doc(p.pins.e01.path),e02=doc(p.pins.e02.path);
 need(e01.status==='PASS'&&e01.environment.rust_binary_sha256===p.pins.rustBinary.sha256&&e02.status==='PARTIAL','CURRENT_CANONICAL_CANDIDATE');
 for(const r of [e01,e02])need(r.source_sha256['shared/transport.mjs']===p.pins.transport.sha256&&r.source_sha256['shared/rust/src/main.rs']===p.pins.rustSource.sha256,'CURRENT_ADAPTER_SOURCE_JOIN');
 return p;
}

// Pure metadata filter checks; no claim that a synthetic map is an app observation.
export function matchesFilter(f,event,recipient){
 if(!f||typeof f!=='object'||Array.isArray(f)||!Array.isArray(f.kinds)||!f.kinds.includes(1059)||!Array.isArray(f['#p'])||!f['#p'].includes(recipient))return false;
 if(Object.hasOwn(f,'since')&&(!Number.isSafeInteger(f.since)||f.since>event.created_at))return false;
 if(Object.hasOwn(f,'until')&&(!Number.isSafeInteger(f.until)||f.until<event.created_at))return false;
 for(const name of ['ids','authors'])if(Object.hasOwn(f,name)&&(!Array.isArray(f[name])||!f[name].some(x=>typeof x==='string'&&(name==='ids'?event.id:event.pubkey).startsWith(x))))return false;
 for(const [k,v] of Object.entries(f))if(k.startsWith('#')&&(!Array.isArray(v)||!event.tags.some(t=>t[0]===k.slice(1)&&v.includes(t[1]))))return false;
 return true;
}
export function matchingSubscription(connections,event,recipient){
 for(const c of connections.values())if(c.active)for(const [id,s] of c.subscriptions)if(s.eose!==null&&s.filters.some(f=>matchesFilter(f,event,recipient)))return {connection:c.id,subscription:id,requestSequence:s.req,eoseSequence:s.eose,filters:s.filters};
 return null;
}
function currentGeneration(c,id){const s=c?.subscriptions.get(id);return s?{connection:c.id,subscription:id,requestSequence:s.req,eoseSequence:s.eose}:null;}
// An ID reused by a replacement REQ is a different generation, even after a new EOSE.
export function publicationGenerationMatches(connections,expected,event,recipient){
 if(!expected)return false;
 const c=connections.get(expected.connection),s=c?.subscriptions.get(expected.subscription);
 return c?.active===true&&Number.isSafeInteger(s?.req)&&Number.isSafeInteger(s?.eose)&&s.eose>s.req&&s.req===expected.requestSequence&&s.eose===expected.eoseSequence&&s.filters.some(f=>matchesFilter(f,event,recipient));
}

async function main(){
 const mode=process.argv[2];need(process.argv.length===3&&['serve','prepare','status','publish'].includes(mode),'FIXED_CLI');check();const p=plan();
 if(mode!=='serve'){
  const response=await new Promise((resolve,reject)=>{const c=net.connect(SOCKET);let b=Buffer.alloc(0);const timer=setTimeout(()=>{c.destroy();reject(Error('CONTROL_TIMEOUT'));},45000);c.on('connect',()=>{check();c.end(JSON.stringify({op:mode})+'\n');});c.on('data',x=>{b=Buffer.concat([b,x]);if(b.length>1048576){c.destroy();reject(Error('CONTROL_REPLY_BOUND'));}});c.on('end',()=>{clearTimeout(timer);try{resolve(JSON.parse(b));}catch(e){reject(e);}});c.on('error',e=>{clearTimeout(timer);reject(e);});});
  check();need(response.ok===true,'FIXTURE_COMMAND_FAILED:'+response.error);process.stdout.write(JSON.stringify(response)+'\n');return;
 }
 const T=await import('./transport.mjs');check();
 // The unchanged canonical adapter uses verifyEvent internally but does not export it.
 // Import the same pinned installed dependency only after the plan/source/lease gates.
 const {verifyEvent}=await import('nostr-tools/pure');check();need(typeof verifyEvent==='function','PINNED_VERIFY_EVENT_API');
 const {default:WebSocket,WebSocketServer}=await import('ws');check();
 need(!fs.existsSync(SOCKET),'FRESH_CONTROL_SOCKET');fs.mkdirSync(DIR,{recursive:true,mode:0o700});
 const captureFd=fs.openSync(DIR+'/capture.jsonl','wx',0o600);let sequence=0,total=0,next=0,attempted=false,busy=false,closed=false,delivery=null,publicationGate=null,publicationInvalidated=false;
 const connections=new Map();
 function log(value){const row={schema:'e02-app-proxy-row-v1',sequence:++sequence,utc:new Date().toISOString(),...value};const b=Buffer.from(JSON.stringify(row)+'\n');total+=b.length;need(total<=p.limits.captureBytes,'CAPTURE_BOUND');fs.writeSync(captureFd,b);return row;}
 function prepared(){const d=doc(DIR+'/prepared.json');need(d.schema==='e02-first-cell-prepared-v1'&&d.caseId===CASE&&d.senderPub===A&&d.recipientPub===B&&d.rumor.id===T.getEventHash(d.rumor)&&d.rumor.content===JSON.stringify(T.envelope(A,B,10))&&same(d.rumor.tags,[['p',B]]),'FIXED_PREPARED_RUMOR');need(d.events.length===2&&d.events.every((e,i)=>e.kind===1059&&verifyEvent(JSON.parse(JSON.stringify(e)))&&same(e.tags,[['p',i===0?B:A]])),'PREPARED_WRAPS');return d;}
 function gate(){if(!fs.existsSync(DIR+'/prepared.json'))return null;return matchingSubscription(connections,prepared().events[0],B);}
 function invalidatePublication(c,id,reason){if(publicationGate&&c.id===publicationGate.connection&&(id===null||id===publicationGate.subscription)){if(!publicationInvalidated)log({connection:c.id,direction:'PUBLICATION_GENERATION_INVALIDATED',reason,gate:publicationGate});publicationInvalidated=true;delivery=null;}}
 function qualifiedDelivery(before,event){return !publicationInvalidated&&delivery!==null&&publicationGenerationMatches(connections,before,event,B)&&publicationGenerationMatches(connections,delivery.forwardGeneration,event,B)&&same(delivery.forwardGeneration,delivery.completionGeneration);}
 function fatal(error){if(closed)return;closed=true;try{putJSON('serve-error.json',{error:String(error),sequence,scope:'UNQUALIFIED_NO_E02_PROMOTION'});}catch{}for(const c of connections.values()){c.app.terminate();c.upstream.terminate();}server.close();control.close();clearInterval(watchdog);process.exitCode=2;}
 const server=new WebSocketServer({host:'127.0.0.1',port:17777,maxPayload:p.limits.messageBytes,perMessageDeflate:false});
 server.on('connection',(app,request)=>{try{check();need(++next<=p.limits.connections,'CONNECTION_BOUND');const upstream=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});const c={id:next,active:true,app,upstream,subscriptions:new Map(),pending:[]};connections.set(c.id,c);log({connection:c.id,direction:'OPEN',userAgent:String(request.headers['user-agent']??'').slice(0,1024)});
  app.on('message',(data,binary)=>{try{check();need(!binary,'TEXT_ONLY_NOSTR');const bytes=Buffer.from(data);const f=T.strictJSON(bytes.toString('utf8'));const row=log({connection:c.id,direction:'APP_TO_RELAY',rawBase64:bytes.toString('base64')});if(Array.isArray(f)&&f[0]==='REQ'&&typeof f[1]==='string'){invalidatePublication(c,f[1],'REQ_REPLACED');c.subscriptions.set(f[1],{req:row.sequence,eose:null,filters:f.slice(2)});}if(Array.isArray(f)&&f[0]==='CLOSE'){invalidatePublication(c,f[1],'APP_CLOSE');c.subscriptions.delete(f[1]);}if(upstream.readyState===WebSocket.OPEN){check();upstream.send(bytes,{binary:false});}else{need(c.pending.length<64,'PENDING_FRAME_BOUND');c.pending.push(bytes);}}catch(e){fatal(e);}});
  upstream.on('open',()=>{try{check();for(const bytes of c.pending){check();upstream.send(bytes,{binary:false});}c.pending=[];}catch(e){fatal(e);}});
  upstream.on('message',(data,binary)=>{try{
   check();need(!binary,'TEXT_ONLY_NOSTR');const bytes=Buffer.from(data);const f=T.strictJSON(bytes.toString('utf8'));
   const candidate=attempted&&Array.isArray(f)&&f[0]==='EVENT'&&f[2]?.id===prepared().events[0].id&&c.id===publicationGate?.connection&&f[1]===publicationGate?.subscription;
   const forwardGeneration=candidate&&!publicationInvalidated&&publicationGenerationMatches(connections,publicationGate,f[2],B)?currentGeneration(c,f[1]):null;
   const row=log({connection:c.id,direction:'RELAY_TO_APP',rawBase64:bytes.toString('base64'),publicationGeneration:forwardGeneration});
   if(Array.isArray(f)&&f[0]==='EOSE'&&c.subscriptions.has(f[1]))c.subscriptions.get(f[1]).eose=row.sequence;
   if(Array.isArray(f)&&f[0]==='CLOSED'){invalidatePublication(c,f[1],'RELAY_CLOSED');c.subscriptions.delete(f[1]);}
   check();app.send(bytes,{binary:false},error=>{try{
    check();if(error)throw error;
    const completionGeneration=forwardGeneration&&!publicationInvalidated&&publicationGenerationMatches(connections,publicationGate,f[2],B)?currentGeneration(c,f[1]):null;
    const sent=log({connection:c.id,direction:'APP_SOCKET_SEND_COMPLETE',sourceSequence:row.sequence,publicationGeneration:completionGeneration});
    if(!delivery&&forwardGeneration&&completionGeneration&&same(forwardGeneration,completionGeneration))delivery={frame:bytes,event:f[2],connection:c.id,subscription:f[1],rowSequence:row.sequence,sentSequence:sent.sequence,forwardGeneration,completionGeneration};
   }catch(e){fatal(e);}});
  }catch(e){fatal(e);}});
  for(const socket of [app,upstream]){socket.on('error',error=>fatal(error));socket.on('close',()=>{try{invalidatePublication(c,null,'CONNECTION_CLOSED');c.active=false;c.subscriptions.clear();app.terminate();upstream.terminate();log({connection:c.id,direction:'CLOSE'});}catch(e){fatal(e);}});}
 }catch(e){fatal(e);}});
 server.on('error',fatal);
 async function exchange(events,filter){check();return await new Promise((resolve,reject)=>{const ws=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});const ack=[],received=[];let settled=false;const timer=setTimeout(()=>finish(Error('RELAY_TIMEOUT')),p.limits.networkTimeoutMilliseconds);function finish(error){if(settled)return;settled=true;clearTimeout(timer);ws.terminate();error?reject(error):resolve({ack,received});}ws.on('open',()=>{try{check();for(const event of events??[]){check();ws.send(JSON.stringify(['EVENT',event]));}if(filter){check();ws.send(JSON.stringify(['REQ','e02-owned-query',filter]));}}catch(e){finish(e);}});ws.on('message',data=>{try{check();const bytes=Buffer.from(data);const f=T.strictJSON(bytes.toString('utf8'));if(f[0]==='OK'){ack.push({rawBase64:bytes.toString('base64'),frame:f});need(f[2]===true,'RELAY_REFUSAL');if(events&&events.every(e=>ack.some(r=>r.frame[1]===e.id&&r.frame[2]===true)))finish();}if(f[0]==='EVENT'&&f[1]==='e02-owned-query')received.push({rawBase64:bytes.toString('base64'),frame:f});if(f[0]==='EOSE'&&f[1]==='e02-owned-query')finish();}catch(e){finish(e);}});ws.on('error',finish);ws.on('close',()=>{if(!settled)finish(Error('EARLY_RELAY_CLOSE'));});});}
 async function prepare(){check();need(!fs.existsSync(DIR+'/prepared.json'),'PREPARE_ONCE');const from=T.secret(1),to=T.secret(2),envelope=T.envelope(A,B,10),rumor=T.rumor(envelope,A,B);need(T.getPublicKey(from)===A&&T.getPublicKey(to)===B,'PUBLIC_TEST_IDENTITIES');check();const events=[T.wrap(rumor,from,B),T.wrap(rumor,from,A)];const expectedRumor=putJSON('expected-rumor.json',rumor),expectedContent=put(DIR+'/expected-content.txt',rumor.content);const expected=putJSON('expected.json',{schema:'e02-first-cell-expected-v1',caseId:CASE,direction:'js-to-rust',role:'incoming',relay:'rs-relay',senderPub:A,recipientPub:B,envelope,rumor,createdUTC:new Date().toISOString()});const preparedPin=putJSON('prepared.json',{schema:'e02-first-cell-prepared-v1',caseId:CASE,senderPub:A,recipientPub:B,rumor,events,expected});check();const now=Math.floor(Date.now()/1000),inboxes=[from,to].map(sk=>T.finalizeEvent({kind:10050,created_at:now,tags:[['relay',p.proxyUrl]],content:''},sk));const r=await exchange(inboxes,null);check();const inboxPin=putJSON('inboxes.json',{events:inboxes,...r});return {expected,expectedRumor,expectedContent,prepared:preparedPin,inboxes:inboxPin};}
 function validateActual(frame,queried){check();const f=T.strictJSON(frame.toString('utf8'));need(f[0]==='EVENT'&&same(f[2],queried),'ACTUAL_APP_RELAY_EVENT_JOIN');const wire=JSON.stringify(f[2]);const request={op:'validate',wire,secret:'2'.padStart(64,'0'),role:'incoming',expectedSender:A};const framePin=put(DIR+'/frame.json',frame),wirePin=put(DIR+'/wire.json',wire);const jsRequest=putJSON('js-request.json',request),rustRequest=putJSON('rust-request.json',request);check();const js=T.validate(wire,T.secret(2),{role:'incoming',expectedSender:A});const jsResult=putJSON('js-result.json',js);check();const requests=[{op:'source'},request],stdin=requests.map(x=>JSON.stringify(x)).join('\n')+'\n';const input=put(DIR+'/Rust-stdin.jsonl',stdin);const native=spawnSync(p.pins.rustBinary.path,[],{input:stdin,timeout:p.limits.rustTimeoutMilliseconds,maxBuffer:1048576,env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8'}});const stdout=put(DIR+'/Rust-stdout.jsonl',native.stdout??Buffer.alloc(0)),stderr=put(DIR+'/Rust-stderr.bin',native.stderr??Buffer.alloc(0));check();need(!native.error&&native.status===0&&native.signal===null&&(native.stderr?.length??0)===0,'NATURAL_RUST_VALIDATION');const replies=String(native.stdout).trimEnd().split('\n').map(x=>T.strictJSON(x));need(replies.length===2&&replies[0].ok===true&&replies[0].value===fs.readFileSync(p.pins.rustSource.path,'utf8')&&replies[1].ok===true,'CURRENT_RUST_SOURCE_REPLY');const rust=replies[1].value,rustResult=putJSON('rust-result.json',rust);need(same(js,rust)&&js.ok===true&&same(js.value.rumor,prepared().rumor)&&js.value.dispatch===true&&js.value.role==='incoming','INDEPENDENT_ACTUAL_RECEIVED_VALIDATION');const transport=putJSON('consumer-transport.json',{schema:'e02-ordinary-transport-v1',frame:framePin,wire:wirePin,jsRequest,rustRequest,jsResult,rustResult});const validation=putJSON('validation.json',{schema:'e02-received-validation-record-v1',caseId:CASE,transport,rustBinary:p.pins.rustBinary,rustSource:p.pins.rustSource,rustInput:input,rustStdout:stdout,rustStderr:stderr,rustExit:native.status,rustSignal:native.signal,actualQueriedEvent:queried,js,rust,clientRetention:'NOT_ESTABLISHED_BY_TRANSPORT_VALIDATION'});return {transport,validation};}
 async function publish(){check();need(!attempted,'PUBLISH_ONCE');const before=gate();need(before!==null,'NO_CURRENT_APP_SUBSCRIPTION_EOSE');const d=prepared();publicationGate=before;attempted=true;putJSON('publish-intent.json',{schema:'e02-publish-intent-v1',caseId:CASE,prepared:pin(DIR+'/prepared.json'),gate:before,issuedUTC:new Date().toISOString()});check();const result=await exchange(d.events,null);check();const until=process.hrtime.bigint()+10000000000n;while(!delivery&&!publicationInvalidated&&process.hrtime.bigint()<until){check();await new Promise(r=>setTimeout(r,100));}check();need(qualifiedDelivery(before,d.events[0]),'NO_MATCHING_ACTUAL_APP_BOUND_GENERATION');const query=await exchange(null,{ids:[d.events[0].id],limit:1});check();need(query.received.length===1,'EXACT_QUERIED_EVENT');need(qualifiedDelivery(before,d.events[0]),'GENERATION_CHANGED_DURING_RELAY_QUERY');const queried=query.received[0].frame[2];const v=validateActual(delivery.frame,queried);check();need(qualifiedDelivery(before,d.events[0]),'GENERATION_CHANGED_BEFORE_RECORD');const publication=putJSON('publish.json',{schema:'e02-first-cell-publication-v1',caseId:CASE,prepared:pin(DIR+'/prepared.json'),gate:before,publication:result,query,delivery:{connection:delivery.connection,subscription:delivery.subscription,rowSequence:delivery.rowSequence,sentSequence:delivery.sentSequence,forwardGeneration:delivery.forwardGeneration,completionGeneration:delivery.completionGeneration},...v,clientRetention:'UNVERIFIED_UNTIL_REAL_CLIENT_EXPORT',scope:'FIRST_INCOMING_CELL_ONLY_E02_PARTIAL'});return {publication,...v};}
 const control=net.createServer({allowHalfOpen:true},socket=>{let b='';socket.on('data',chunk=>{b+=chunk.toString('utf8');if(Buffer.byteLength(b)>1024)socket.destroy();});socket.on('end',async()=>{let acquired=false;try{check();const q=JSON.parse(b);need(Object.keys(q).length===1&&['prepare','status','publish'].includes(q.op),'FIXED_CONTROL_OPERATION');need(!busy,'COMMAND_IN_PROGRESS');busy=true;acquired=true;let result;if(q.op==='prepare')result=await prepare();else if(q.op==='publish')result=await publish();else result={caseId:CASE,ready:gate()!==null,gate:gate(),captureSequence:sequence,scope:'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT'};check();socket.end(JSON.stringify({schema:'e02-fixture-command-v1',operation:q.op,caseId:CASE,ok:true,result})+'\n');}catch(error){try{putJSON('command-error-'+Date.now()+'.json',{operation:'CONTROL',error:String(error)});}catch{}socket.end(JSON.stringify({ok:false,error:String(error)})+'\n');}finally{if(acquired)busy=false;}});});
 control.on('error',fatal);check();control.listen(SOCKET,()=>{fs.chmodSync(SOCKET,0o600);putJSON('serve-ready.json',{schema:'e02-fixture-service-ready-v1',caseId:CASE,proxy:p.proxyUrl,backend:p.backendUrl,scope:'NO_CLIENT_RECEIPT_OR_E02_PASS'});});
 const watchdog=setInterval(()=>{try{check();}catch(e){fatal(e);}},1000);
 for(const sig of ['SIGTERM','SIGINT'])process.on(sig,()=>{if(closed)return;closed=true;clearInterval(watchdog);for(const c of connections.values()){c.app.terminate();c.upstream.terminate();}server.close();control.close();try{fs.fsyncSync(captureFd);fs.closeSync(captureFd);}catch{}});
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)main().catch(error=>{process.stderr.write(String(error)+'\n');process.exitCode=2;});
