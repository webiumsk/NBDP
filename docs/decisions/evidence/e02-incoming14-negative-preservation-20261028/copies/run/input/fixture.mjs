// SOURCE ONLY: distinct two-role minimum profile; no crypto/runtime executed by preparation.
import fs from 'node:fs';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {verifyDependencyTree} from './dependency-tree.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
import {createCaptureBudget,observedGuard} from './capture-budget.mjs';
import {observedExchange} from './exchange-adapter.mjs';
import {createCallbackBoundary,observedUpstreamSend} from './proxy-observer.mjs';

const DIR='/session/fixtures', PLAN='/input/fixture-plan.json';
const A='79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798';
const B='c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5';
const CASE='minimum-two-role-rs', PROFILE='e02-ordinary-minimum-rs-two-role-v2', SOCKET=DIR+'/control.sock';
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const same=(a,b)=>typeof a===typeof b&&(a===null||b===null?a===b:Array.isArray(a)||Array.isArray(b)?Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>same(x,b[i])):typeof a==='object'?Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>Object.hasOwn(b,k)&&same(a[k],b[k])):a===b);
function need(v,why){if(!v)throw Error(why);}
function pin(path){const s=fs.lstatSync(path);need(s.isFile()&&!s.isSymbolicLink(),'REGULAR_FILE');const raw=fs.readFileSync(path);return {path,bytes:raw.length,sha256:sha(raw)};}
function raw(path){const b=fs.readFileSync(path);need(b.length<=16777216,'DATA_BOUND');return b;}
function doc(path){return JSON.parse(raw(path));}
function put(path,data){const b=Buffer.isBuffer(data)?data:Buffer.from(data);need(b.length<=16777216,'WRITE_BOUND');fs.writeFileSync(path,b,{flag:'wx',mode:0o600});return pin(path);}
function putJSON(name,value){return put(DIR+'/'+name,JSON.stringify(value,null,2)+'\n');}
function guardCheck(){
 const expected=process.env.NBDP_LEASE_SHA256;need(/^[0-9a-f]{64}$/.test(expected??''),'EXTERNAL_LEASE_SHA');
 const argv=['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/lease_guard.py','check',expected];
 const r=spawnSync('/guard-python/lib/ld-linux-x86-64.so.2',argv,{env:process.env,timeout:5000,maxBuffer:1048576});
 need(!r.error&&r.status===0&&r.signal===null,'FINITE_LEASE_DENIED:'+String(r.stderr??'').slice(0,2048));
}
let servicePhase=null;
function check(label='original-unlabeled'){
 if(servicePhase!==null)return observedGuard(guardCheck,servicePhase,label);
 return guardCheck(); // Startup/controller guards remain real but untraced.
}

function plan(){
 const b=raw(PLAN);need(sha(b)===process.env.NBDP_FIXTURE_PLAN_SHA256,'EXTERNAL_FIXTURE_PLAN_SHA');const p=JSON.parse(b);
 need(p.schema==='e02-ordinary-minimum-fixture-plan-v2'&&p.caseId===CASE&&p.profileId===PROFILE&&p.direction==='JS_TO_RUST'&&p.relay==='rs-relay'&&p.proxyUrl==='ws://127.0.0.1:17777'&&p.backendUrl==='ws://127.0.0.1:8080'&&p.output===DIR,'FIXED_MINIMUM_PROFILE');
 const configRaw=raw('/input/run-config.json');
 need(sha(configRaw)===process.env.NBDP_MINIMUM_RUN_CONFIG_SHA256,'EXTERNAL_ROLE_CONFIG_SHA');
 const config=JSON.parse(configRaw);need(config.profileId===PROFILE&&['incoming','archive'].includes(config.ordinaryRole),'CLOSED_ROLE_CONFIG');
 const spec=roleSpec(config.ordinaryRole);need(config.windowId===spec.windowId&&config.account===spec.account&&config.peer===spec.peer,'ROLE_ACCOUNT_BINDING');
 p.ordinaryRole=config.ordinaryRole;p.roleSpec=spec;
 for(const d of Object.values(p.oracles)){const q=pin(d.path);need(q.bytes===d.bytes&&q.sha256===d.sha256,'FROZEN_ORACLE_PIN');} 
 need(Array.isArray(p.dependencyFiles)&&p.dependencyFiles.length>0&&p.dependencyFiles.length<=4096,'PINNED_INSTALLED_DEPENDENCIES');for(const d of [...Object.values(p.pins),...p.dependencyFiles]){const q=pin(d.path);need(q.bytes===d.bytes&&q.sha256===d.sha256,'CURRENT_SOURCE_BINARY_PIN');}
 const tree=pin(p.dependencyTree.path);need(tree.bytes===p.dependencyTree.bytes&&tree.sha256===p.dependencyTree.sha256,'EXACT_DEPENDENCY_TREE_PIN');
 verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);
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

// Closed pure metadata contracts. These functions do not produce/validate crypto.
export function roleSpec(role){
 need(role==='incoming'||role==='archive','CLOSED_ROLE');
 return role==='incoming'?{windowId:'incoming-b',account:B,peer:A,scalar:2,validationRole:'incoming',stages:['incoming-business','incoming-ordinary-chat']}:
 {windowId:'archive-a',account:A,peer:B,scalar:1,validationRole:'archive',stages:['archive-business','archive-identical-replay','archive-fresh-wrap-replay']};
}
export function stageSpec(role,index){
 const r=roleSpec(role);need(Number.isSafeInteger(index)&&index>=0&&index<r.stages.length,'CLOSED_STAGE_INDEX');
 const id=r.stages[index],chat=id==='incoming-ordinary-chat',duplicate=id==='archive-identical-replay';
 return {id,index,oracle:chat?'chat':'business',dispatch:role==='incoming'&&!chat,
   normalizedRole:role==='archive'?'archive':chat?'chat':'incoming',
   identicalReplay:duplicate,freshWrap:!duplicate,requiresNewAppFrame:!duplicate};
}
export function exactInnerShape(r){
 return !!r&&typeof r==='object'&&!Array.isArray(r)&&Object.keys(r).length===6&&
 ['id','pubkey','created_at','kind','tags','content'].every(k=>Object.hasOwn(r,k))&&
 /^[0-9a-f]{64}$/.test(r.id)&&r.pubkey===A&&Number.isSafeInteger(r.created_at)&&r.created_at>=0&&r.kind===14&&
 typeof r.content==='string'&&same(r.tags,[['p',B]]);
}
export function attemptLineageMatches(expected,forward,complete){
 return !!expected&&!!forward&&!!complete&&Number.isSafeInteger(expected.epoch)&&expected.epoch>0&&
 ['incoming-business','incoming-ordinary-chat','archive-business','archive-identical-replay','archive-fresh-wrap-replay'].includes(expected.stageId)&&
 expected.epoch===forward.epoch&&expected.epoch===complete.epoch&&expected.stageId===forward.stageId&&expected.stageId===complete.stageId;
}
export function stageDeliveryAllowed(stage,observed,origin){
 if(typeof observed!=='boolean'||!stage)return false;
 const allowed=[stageSpec('incoming',0),stageSpec('incoming',1),stageSpec('archive',0),stageSpec('archive',1),stageSpec('archive',2)];
 if(!allowed.some(value=>same(value,stage)))return false;
 if(observed)return origin==='ACTUAL_APP_SOCKET_FRAME';
 return stage.id==='archive-identical-replay'&&stage.index===1&&stage.identicalReplay===true&&stage.requiresNewAppFrame===false&&origin==='ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME';
}
export function replayBinding(stage,event,initial){
 if(!stage||!event||!initial)return false;
 return stage.identicalReplay?same(event,initial):stage.index===2?event.id!==initial.id:true;
}

async function main(){
 const mode=process.argv[2];need(process.argv.length===3&&['serve','prepare','status','publish'].includes(mode),'FIXED_CLI');check();const p=plan();
 if(mode!=='serve'){
  const response=await new Promise((resolve,reject)=>{const c=net.connect(SOCKET);let b=Buffer.alloc(0);const timer=setTimeout(()=>{c.destroy();reject(Error('CONTROL_TIMEOUT'));},45000);c.on('connect',()=>{check();c.end(JSON.stringify({op:mode})+'\n');});c.on('data',x=>{b=Buffer.concat([b,x]);if(b.length>1048576){c.destroy();reject(Error('CONTROL_REPLY_BOUND'));}});c.on('end',()=>{clearTimeout(timer);try{resolve(JSON.parse(b));}catch(e){reject(e);}});c.on('error',e=>{clearTimeout(timer);reject(e);});});
  check();verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);need(response.ok===true,'FIXTURE_COMMAND_FAILED:'+response.error);process.stdout.write(JSON.stringify(response)+'\n');return;
 }
 const T=await import('./transport.mjs');check();
 // The unchanged canonical adapter uses verifyEvent internally but does not export it.
 // Import the same pinned installed dependency only after the plan/source/lease gates.
 const {verifyEvent}=await import('nostr-tools/pure');check();need(typeof verifyEvent==='function','PINNED_VERIFY_EVENT_API');
 const {default:WebSocket,WebSocketServer}=await import('ws');check();
 need(!fs.existsSync(SOCKET),'FRESH_CONTROL_SOCKET');fs.mkdirSync(DIR,{recursive:true,mode:0o700});
 const captureFd=fs.openSync(DIR+'/capture.jsonl','wx',0o600),phaseFd=fs.openSync(DIR+'/phase-trace.jsonl','wx',0o600);
 const budget=createCaptureBudget({fs,streams:{proxy:captureFd,phase:phaseFd},limit:p.limits.captureBytes});
 const phaseWriter=createPhaseWriter({fs:{writeSync:budget.writeSync},fd:phaseFd,clock:()=>process.hrtime.bigint(),utc:()=>new Date().toISOString(),limit:p.limits.captureBytes});
 const phase=(name,fields={})=>{if(closed)throw firstFailure??Error('SERVICE_CLOSED');try{budget.healthy();const row=phaseWriter(name,{profileId:PROFILE,windowId:p.roleSpec.windowId,ordinaryRole:p.ordinaryRole,observedAttempt:activeAttempt?{...activeAttempt}:null,...fields});budget.healthy();return row;}catch(error){throw budget.poison(error);}};
 phase.state=()=>({schema:'e02-minimum-observer-state-v2',budget:budget.state(),phase:phaseWriter.state()});servicePhase=phase;
 let sequence=0,next=0,attempted=false,busy=false,closed=false,delivery=null,publicationGate=null,publicationInvalidated=false;
 const connections=new Map();let stageIndex=0,attemptEpoch=0,activeAttempt=null,publicationWindowOpen=false,attemptSawFrame=false;
 const spec=p.roleSpec;
 function selectedEvent(){return prepared().events[stageIndex];}
 function selectedStage(){return stageSpec(p.ordinaryRole,stageIndex);}
 function log(value){try{budget.healthy();const row={schema:'e02-minimum-proxy-row-v1',sequence:++sequence,utc:new Date().toISOString(),...value};const b=Buffer.from(JSON.stringify(row)+'\n');budget.writeSync(captureFd,b);budget.healthy();return row;}catch(error){throw budget.poison(error);}}
 function prepared(){
  const d=doc(DIR+'/prepared.json');need(d.schema==='e02-minimum-prepared-v2'&&d.profileId===PROFILE&&d.windowId===spec.windowId,'FIXED_PREPARED_PROFILE');
  for(const name of ['business','chat'])need(exactInnerShape(d.rumors[name])&&d.rumors[name].id===T.getEventHash(d.rumors[name])&&same(d.rumors[name],doc(p.oracles[name].path)),'FROZEN_SHARED_INNER');
  need(d.rumors.business.content===JSON.stringify(T.envelope(A,B,10))&&d.rumors.chat.content==='NBDP harmless ordinary chat control — faktúra 𐐀','FROZEN_CONTENT');
  need(d.events.length===spec.stages.length&&d.events.every(e=>e.kind===1059&&verifyEvent(JSON.parse(JSON.stringify(e)))&&same(e.tags,[['p',spec.account]])),'ROLE_WRAPS');
  if(p.ordinaryRole==='archive')need(same(d.events[0],d.events[1])&&d.events[2].id!==d.events[0].id,'IDENTICAL_AND_FRESH_ARCHIVE_WRAPS');
  return d;
 }
 function gate(){if(!fs.existsSync(DIR+'/prepared.json')||stageIndex>=spec.stages.length)return null;return matchingSubscription(connections,selectedEvent(),spec.account);}
 function invalidatePublication(c,id,reason){if(attempted&&publicationGate&&c.id===publicationGate.connection&&(id===null||id===publicationGate.subscription)){if(!publicationInvalidated)log({connection:c.id,direction:'PUBLICATION_GENERATION_INVALIDATED',reason,gate:publicationGate});publicationInvalidated=true;delivery=null;}}
 function qualifiedDelivery(before,event){return !publicationInvalidated&&delivery!==null&&attemptLineageMatches(activeAttempt,delivery.forwardAttempt,delivery.completionAttempt)&&publicationGenerationMatches(connections,before,event,spec.account)&&publicationGenerationMatches(connections,delivery.forwardGeneration,event,spec.account)&&same(delivery.forwardGeneration,delivery.completionGeneration);}
 const terminated=new WeakSet(),exchangeSockets=new Set();let firstFailure=null,watchdog=null,control=null;
 function terminateOwned(socket){if(!socket||terminated.has(socket))return;terminated.add(socket);socket.terminate();}
 class OwnedWebSocket extends WebSocket{constructor(...args){super(...args);exchangeSockets.add(this);}terminate(){if(terminated.has(this))return;terminated.add(this);super.terminate();}}
 // Exchange owns its exact sockets; proxy owns the paired app/backend sockets.
 // Observation failure cannot skip cleanup or replace an incoming socket fault.
 function fatal(error){
  if(closed)return;closed=true;firstFailure=error;
  const cleanupErrors=[];
  const attempt=(label,fn)=>{try{fn();}catch(e){cleanupErrors.push({label,error:String(e)});}};
  attempt('failure-retention',()=>putJSON('serve-error.json',{error:String(error),sequence,
   observer:phase.state(),scope:'UNQUALIFIED_NO_E02_PROMOTION'}));
  for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));
  for(const socket of exchangeSockets)attempt('terminate-owned-exchange',()=>socket.terminate());
  for(const fd of [captureFd,phaseFd]){attempt('fsync-stream',()=>fs.fsyncSync(fd));attempt('close-stream',()=>fs.closeSync(fd));}
  attempt('close-proxy-server',()=>server.close());if(control)attempt('close-control-server',()=>control.close());
  if(watchdog)attempt('clear-watchdog',()=>clearInterval(watchdog));
  attempt('end-dependency-boundary',()=>verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles));
  attempt('observer-state-retention',()=>putJSON('observer-final-state.json',{observer:phase.state(),error:String(firstFailure),secondaryErrors:cleanupErrors}));
  process.exitCode=2;
 }
 const callback=createCallbackBoundary({isClosed:()=>closed,healthy:budget.healthy,fatal});
 function proxyPhase(name,c,fields={}){return phase(name,{connection:c.id,...fields});}
 function sendUpstream(c,bytes){return observedUpstreamSend({socket:c.upstream,bytes,sha,
  phase:(name,fields)=>proxyPhase(name,c,fields),callback,isClosed:()=>closed});}
 const server=new WebSocketServer({host:'127.0.0.1',port:17777,maxPayload:p.limits.messageBytes,perMessageDeflate:false});
 server.on('connection',(app,request)=>{try{
  if(closed){terminateOwned(app);return;}
  phase('PROXY_CONNECTION_CALLBACK_ENTRY',{nextConnection:next+1});check('proxy:connection');
  need(++next<=p.limits.connections,'CONNECTION_BOUND');
  const upstream=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
  const c={id:next,active:true,app,upstream,subscriptions:new Map(),pending:[]};connections.set(c.id,c);
  for(const [origin,socket] of [['APP',app],['RELAY',upstream]]){
   socket.on('error',error=>callback(()=>{proxyPhase('PROXY_SOCKET_ERROR_CALLBACK_ENTRY',c,{origin,error:String(error)});throw error;},error));
   socket.on('close',()=>callback(()=>{
    proxyPhase('PROXY_SOCKET_CLOSE_CALLBACK_ENTRY',c,{origin});invalidatePublication(c,null,'CONNECTION_CLOSED');
    c.active=false;c.subscriptions.clear();terminateOwned(app);terminateOwned(upstream);log({connection:c.id,direction:'CLOSE'});
   }));
  }
  log({connection:c.id,direction:'OPEN',userAgent:String(request.headers['user-agent']??'').slice(0,1024)});
  app.on('message',(data,binary)=>callback(()=>{
   proxyPhase('PROXY_RAW_CALLBACK_ENTRY',c,{origin:'APP',rawBase64:Buffer.from(data).toString('base64'),binary});
   check('proxy:app-message');need(!binary,'TEXT_ONLY_NOSTR');const bytes=Buffer.from(data);const f=T.strictJSON(bytes.toString('utf8'));
   const row=log({connection:c.id,direction:'APP_TO_RELAY',rawBase64:bytes.toString('base64')});
   if(Array.isArray(f)&&f[0]==='REQ'&&typeof f[1]==='string'){invalidatePublication(c,f[1],'REQ_REPLACED');c.subscriptions.set(f[1],{req:row.sequence,eose:null,filters:f.slice(2)});}
   if(Array.isArray(f)&&f[0]==='CLOSE'){invalidatePublication(c,f[1],'APP_CLOSE');c.subscriptions.delete(f[1]);}
   if(upstream.readyState===WebSocket.OPEN){check('proxy:app-before-upstream-send');sendUpstream(c,bytes);}
   else{need(c.pending.length<64,'PENDING_FRAME_BOUND');c.pending.push(bytes);}
  }));
  upstream.on('open',()=>callback(()=>{
   proxyPhase('PROXY_SOCKET_OPEN_CALLBACK_ENTRY',c,{origin:'RELAY'});check('proxy:upstream-open');
   for(const bytes of c.pending){check('proxy:pending-before-upstream-send');sendUpstream(c,bytes);}c.pending=[];
  }));
  upstream.on('message',(data,binary)=>callback(()=>{
   proxyPhase('PROXY_RAW_CALLBACK_ENTRY',c,{origin:'RELAY',rawBase64:Buffer.from(data).toString('base64'),binary});
   check('proxy:upstream-message');need(!binary,'TEXT_ONLY_NOSTR');const bytes=Buffer.from(data);const f=T.strictJSON(bytes.toString('utf8'));
   const candidate=attempted&&publicationWindowOpen&&Array.isArray(f)&&f[0]==='EVENT'&&stageIndex<spec.stages.length&&f[2]?.id===selectedEvent().id&&c.id===publicationGate?.connection&&f[1]===publicationGate?.subscription;
   const forwardAttempt=candidate&&activeAttempt?{...activeAttempt}:null;
   const forwardGeneration=candidate&&!publicationInvalidated&&publicationGenerationMatches(connections,publicationGate,f[2],spec.account)?currentGeneration(c,f[1]):null;
   if(candidate)attemptSawFrame=true;
   const row=log({connection:c.id,direction:'RELAY_TO_APP',rawBase64:bytes.toString('base64'),publicationGeneration:forwardGeneration,publicationAttempt:forwardAttempt});
   if(Array.isArray(f)&&f[0]==='EOSE'&&c.subscriptions.has(f[1]))c.subscriptions.get(f[1]).eose=row.sequence;
   if(Array.isArray(f)&&f[0]==='CLOSED'){invalidatePublication(c,f[1],'RELAY_CLOSED');c.subscriptions.delete(f[1]);}
   check('proxy:before-app-send');const bufferHash=sha(bytes);
   proxyPhase('PROXY_SEND_INVOKE_ENTRY',c,{target:'APP',bufferHash,bytes:bytes.length,sourceSequence:row.sequence});
   app.send(bytes,{binary:false},error=>callback(()=>{
    proxyPhase('PROXY_SEND_CALLBACK_ENTRY',c,{target:'APP',bufferHash,sourceSequence:row.sequence,error:error?String(error):null});
    check('proxy:app-send-callback');if(error)throw error;need(sha(bytes)===bufferHash,'ACTUAL_PROXY_BUFFER_MUTATION');
    const completionAttempt=forwardAttempt&&activeAttempt?{...activeAttempt}:null;
    const completionGeneration=forwardGeneration&&publicationWindowOpen&&attemptLineageMatches(activeAttempt,forwardAttempt,completionAttempt)&&!publicationInvalidated&&publicationGenerationMatches(connections,publicationGate,f[2],spec.account)?currentGeneration(c,f[1]):null;
    const sent=log({connection:c.id,direction:'APP_SOCKET_SEND_COMPLETE',sourceSequence:row.sequence,publicationGeneration:completionGeneration,publicationAttempt:completionAttempt});
    proxyPhase('PROXY_SEND_CALLBACK_COMPLETE',c,{target:'APP',bufferHash,sourceSequence:row.sequence,sentSequence:sent.sequence});
    if(!delivery&&forwardGeneration&&completionGeneration&&same(forwardGeneration,completionGeneration))delivery={frame:bytes,event:f[2],connection:c.id,subscription:f[1],rowSequence:row.sequence,sentSequence:sent.sequence,forwardGeneration,completionGeneration,forwardAttempt,completionAttempt};
   },error??null));
   if(!closed)proxyPhase('PROXY_SEND_INVOKE_RETURNED',c,{target:'APP',bufferHash,sourceSequence:row.sequence});
  }));

 }catch(error){try{terminateOwned(app);}catch{}fatal(error);}});
 server.on('error',fatal);
 async function exchange(events,filter,label){
  return await observedExchange({WebSocket:OwnedWebSocket,p,check,phase,log,
   put:(name,bytes)=>put(DIR+'/'+name,bytes),strictJSON:T.strictJSON,sha,
   clock:()=>process.hrtime.bigint(),arm:setTimeout,clear:clearTimeout},events,filter,label);
 }
 async function prepare(){
  check();need(!fs.existsSync(DIR+'/prepared.json'),'PREPARE_ONCE');
  const from=T.secret(1),local=T.secret(spec.scalar),rumors={business:doc(p.oracles.business.path),chat:doc(p.oracles.chat.path)};
  need(T.getPublicKey(from)===A&&T.getPublicKey(local)===spec.account,'PUBLIC_ROLE_IDENTITIES');
  for(const r of Object.values(rumors))need(exactInnerShape(r)&&r.id===T.getEventHash(r),'FROZEN_INPUT_RUMOR_ID');
  check();const initial=T.wrap(rumors.business,from,spec.account);
  const events=p.ordinaryRole==='incoming'?[initial,T.wrap(rumors.chat,from,B)]:[initial,initial,T.wrap(rumors.business,from,A)];
  const expected={};for(let i=0;i<spec.stages.length;i++){const s=stageSpec(p.ordinaryRole,i);expected[s.id]={stage:s,rumor:putJSON(s.id+'-expected-rumor.json',rumors[s.oracle]),content:put(DIR+'/'+s.id+'-expected-content.txt',rumors[s.oracle].content)};}
  const preparedPin=putJSON('prepared.json',{schema:'e02-minimum-prepared-v2',profileId:PROFILE,windowId:spec.windowId,role:p.ordinaryRole,rumors,events,expected});
  prepared();check();const now=Math.floor(Date.now()/1000),inboxes=[T.secret(1),T.secret(2)].map(sk=>T.finalizeEvent({kind:10050,created_at:now,tags:[['relay',p.proxyUrl]],content:''},sk));
  const r=await exchange(inboxes,null,'prepare-inboxes');check();const inboxPin=putJSON('inboxes.json',{events:inboxes,...r});
  return {profileId:PROFILE,windowId:spec.windowId,ordinaryRole:p.ordinaryRole,expected,prepared:preparedPin,inboxes:inboxPin};
 }
 function validateActual(frame,queried,stage,origin){check();const f=T.strictJSON(frame.toString('utf8'));need(f[0]==='EVENT'&&same(f[2],queried),'ACTUAL_VALIDATED_FRAME_QUERY_JOIN');const wire=JSON.stringify(f[2]);const request={op:'validate',wire,secret:String(spec.scalar).padStart(64,'0'),role:spec.validationRole,expectedSender:A};const framePin=put(DIR+'/'+stage.id+'-frame.json',frame),wirePin=put(DIR+'/'+stage.id+'-wire.json',wire);const jsRequest=putJSON(stage.id+'-js-request.json',request),rustRequest=putJSON(stage.id+'-rust-request.json',request);check();const js=T.validate(wire,T.secret(spec.scalar),{role:spec.validationRole,expectedSender:A});const jsResult=putJSON(stage.id+'-js-result.json',js);check();const requests=[{op:'source'},request],stdin=requests.map(x=>JSON.stringify(x)).join('\n')+'\n';const input=put(DIR+'/'+stage.id+'-Rust-stdin.jsonl',stdin);const native=spawnSync(p.pins.rustBinary.path,[],{input:stdin,timeout:p.limits.rustTimeoutMilliseconds,maxBuffer:1048576,env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8'}});const stdout=put(DIR+'/'+stage.id+'-Rust-stdout.jsonl',native.stdout??Buffer.alloc(0)),stderr=put(DIR+'/'+stage.id+'-Rust-stderr.bin',native.stderr??Buffer.alloc(0));check();need(!native.error&&native.status===0&&native.signal===null&&(native.stderr?.length??0)===0,'NATURAL_RUST_VALIDATION');const replies=String(native.stdout).trimEnd().split('\n').map(x=>T.strictJSON(x));need(replies.length===2&&replies[0].ok===true&&replies[0].value===fs.readFileSync(p.pins.rustSource.path,'utf8')&&replies[1].ok===true,'CURRENT_RUST_SOURCE_REPLY');const rust=replies[1].value,rustResult=putJSON(stage.id+'-rust-result.json',rust);need(same(js,rust)&&js.ok===true&&same(js.value.rumor,prepared().rumors[stage.oracle])&&js.value.dispatch===stage.dispatch&&js.value.role===stage.normalizedRole,'INDEPENDENT_VALIDATED_FRAME_ROLE_RESULT');const transport=putJSON(stage.id+'-consumer-transport.json',{schema:'e02-minimum-transport-v2',frame:framePin,wire:wirePin,jsRequest,rustRequest,jsResult,rustResult});const validation=putJSON(stage.id+'-validation.json',{schema:'e02-minimum-validated-wire-record-v2',profileId:PROFILE,windowId:spec.windowId,stageId:stage.id,origin,clientReceiptEstablished:origin==='ACTUAL_APP_SOCKET_FRAME',transport,rustBinary:p.pins.rustBinary,rustSource:p.pins.rustSource,rustInput:input,rustStdout:stdout,rustStderr:stderr,rustExit:native.status,rustSignal:native.signal,actualQueriedEvent:queried,js,rust,clientRetention:'NOT_ESTABLISHED_BY_TRANSPORT_VALIDATION'});return {transport,validation};}
 async function publish(){
  const phaseStartSequence=phaseWriter.state().sequence+1;
  check();need(stageIndex<spec.stages.length&&!publicationInvalidated,'FINITE_ROLE_STAGE_OR_STICKY_FAILURE');
  const d=prepared(),stage=selectedStage(),event=d.events[stageIndex],initial=d.events[0],before=gate();
  need(before!==null&&replayBinding(stage,event,initial),'CURRENT_STAGE_BINDINGS_REQUIRED');
  publicationGate=before;delivery=null;attempted=true;activeAttempt={epoch:++attemptEpoch,stageId:stage.id};
  publicationWindowOpen=true;attemptSawFrame=false;const windowStarted=process.hrtime.bigint();
  const intentRow=log({direction:'PUBLICATION_INTENT',stageId:stage.id,eventId:event.id,attempt:activeAttempt});
  const intent=putJSON(stage.id+'-publish-intent.json',{schema:'e02-minimum-publish-intent-v2',profileId:PROFILE,windowId:spec.windowId,stage,attempt:activeAttempt,intentSequence:intentRow.sequence,prepared:pin(DIR+'/prepared.json'),gate:before,issuedUTC:new Date().toISOString()});
  check();const publication=await exchange([event],null,stage.id+'-publish');check();
  const until=process.hrtime.bigint()+10000000000n;
  while(!delivery&&!publicationInvalidated&&process.hrtime.bigint()<until){check();await new Promise(r=>setTimeout(r,100));}
  check();need(!publicationInvalidated&&publicationGenerationMatches(connections,before,event,spec.account),'CURRENT_GENERATION_AFTER_PUBLICATION');
  const observed=qualifiedDelivery(before,event);
  need(observed||!attemptSawFrame,'UNCOMPLETED_APP_FRAME_IS_NOT_QUERY_ONLY_ABSENCE');
  need(stageDeliveryAllowed(stage,observed,observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'),'MISSING_REQUIRED_NEW_APP_EVENT_FRAME');
  publicationWindowOpen=false;
  const elapsedNanoseconds=Number(process.hrtime.bigint()-windowStarted);
  need(Number.isSafeInteger(elapsedNanoseconds)&&elapsedNanoseconds>=0&&elapsedNanoseconds<=1800000000000,'BOUNDED_MEASURED_WINDOW_TIME');
  const closedRow=log({direction:'PUBLICATION_WINDOW_CLOSED',stageId:stage.id,eventId:event.id,attempt:activeAttempt,
   intentSequence:intentRow.sequence,actualNewAppFrameObserved:observed,candidateAppFrameSeen:attemptSawFrame,elapsedNanoseconds});
  const publicationWindow=putJSON(stage.id+'-publication-window.json',{schema:'e02-minimum-publication-window-v2',
   profileId:PROFILE,windowId:spec.windowId,stageId:stage.id,eventId:event.id,attempt:activeAttempt,
   intentSequence:intentRow.sequence,closeSequence:closedRow.sequence,actualNewAppFrameObserved:observed,
   candidateAppFrameSeen:attemptSawFrame,elapsedNanoseconds,clock:'NODE_PROCESS_HRTIME_MONOTONIC',
   origin:observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'});
  const query=await exchange(null,{ids:[event.id],limit:1},stage.id+'-query');check();need(query.received.length===1&&same(query.received[0].frame[2],event),'EXACT_PUBLISHED_EVENT_QUERY');
  const validation=validateActual(observed?delivery.frame:Buffer.from(query.received[0].rawBase64,'base64'),query.received[0].frame[2],stage,observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME');
  const produced=JSON.stringify(event),producerResult=T.validate(produced,T.secret(spec.scalar),{role:spec.validationRole,expectedSender:A});
  need(producerResult.ok===true&&same(producerResult.value.rumor,d.rumors[stage.oracle])&&producerResult.value.dispatch===stage.dispatch&&producerResult.value.role===stage.normalizedRole,'DECLARED_ROLE_DISPATCH_ELIGIBILITY');
  const producerValidation=putJSON(stage.id+'-producer-validation.json',{schema:'e02-minimum-producer-validation-v2',stageId:stage.id,actualPublishedEvent:event,result:producerResult,meaning:'Producer validation only; not a business effect or substitute for actual app wire/export.'});
  check();need(!publicationInvalidated&&publicationGenerationMatches(connections,before,event,spec.account),'CURRENT_GENERATION_BEFORE_STAGE_RECORD');
  const observation={schema:'e02-minimum-stage-observation-range-v2',phaseStartSequence,phaseEndSequence:phaseWriter.state().sequence,proxyEndSequence:sequence,observer:phase.state(),phaseTracePath:DIR+'/phase-trace.jsonl',proxyCapturePath:DIR+'/capture.jsonl',streamPins:'FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS'};
  const record=putJSON(stage.id+'-publication.json',{observation,schema:'e02-minimum-stage-publication-v2',profileId:PROFILE,windowId:spec.windowId,stage,attempt:activeAttempt,intent,publicationWindow,gate:before,publication,query,event,
   actualNewAppFrameObserved:observed,delivery:observed?{connection:delivery.connection,subscription:delivery.subscription,rowSequence:delivery.rowSequence,sentSequence:delivery.sentSequence,forwardGeneration:delivery.forwardGeneration,completionGeneration:delivery.completionGeneration,forwardAttempt:delivery.forwardAttempt,completionAttempt:delivery.completionAttempt}:null,
   validation,producerValidation,clientRetention:'UNVERIFIED_REQUIRES_FRESH_CLIENT_SELECTION_EXPORT',validationOrigin:observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME',
   replayLimit:stage.identicalReplay&&!observed?'No new frame observed in bounded interval; retain honest publication/query/history and require post-replay real client export. No synthesized EVENT or earlier-frame donation.':null});
  stageIndex++;attempted=false;activeAttempt=null;
  return {profileId:PROFILE,windowId:spec.windowId,stage,publication:record,publicationWindow,validation,producerValidation,actualNewAppFrameObserved:observed};
 }
 control=net.createServer({allowHalfOpen:true},socket=>{let b='';socket.on('data',chunk=>{b+=chunk.toString('utf8');if(Buffer.byteLength(b)>1024)socket.destroy();});socket.on('end',async()=>{let acquired=false;try{check();const q=JSON.parse(b);need(Object.keys(q).length===1&&['prepare','status','publish'].includes(q.op),'FIXED_CONTROL_OPERATION');need(!busy,'COMMAND_IN_PROGRESS');busy=true;acquired=true;let result;if(q.op==='prepare')result=await prepare();else if(q.op==='publish')result=await publish();else result={profileId:PROFILE,windowId:spec.windowId,stageId:stageIndex<spec.stages.length?selectedStage().id:null,stageIndex,complete:stageIndex===spec.stages.length,ready:gate()!==null,gate:gate(),captureSequence:sequence,scope:'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT'};check();verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);socket.end(JSON.stringify({schema:'e02-minimum-fixture-command-v2',profileId:PROFILE,windowId:spec.windowId,operation:q.op,caseId:CASE,ok:true,result})+'\n');}catch(error){if(budget.state().poisoned)fatal(error);try{putJSON('command-error-'+Date.now()+'.json',{operation:'CONTROL',error:String(error)});}catch{}socket.end(JSON.stringify({ok:false,error:String(error)})+'\n');}finally{if(acquired)busy=false;}});});
 control.on('error',fatal);check();control.listen(SOCKET,()=>{fs.chmodSync(SOCKET,0o600);putJSON('serve-ready.json',{schema:'e02-fixture-service-ready-v1',caseId:CASE,proxy:p.proxyUrl,backend:p.backendUrl,scope:'NO_CLIENT_RECEIPT_OR_E02_PASS'});});
 watchdog=setInterval(()=>{try{check();}catch(e){fatal(e);}},1000);
 for(const sig of ['SIGTERM','SIGINT'])process.on(sig,()=>{
  if(closed)return;closed=true;let error=null;const secondary=[];
  const attempt=(name,fn)=>{try{fn();}catch(e){if(error===null)error=e;else secondary.push({name,error:String(e)});}};
  clearInterval(watchdog);
  for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));
  for(const socket of exchangeSockets)attempt('terminate-owned-exchange',()=>socket.terminate());
  attempt('close-server',()=>server.close());attempt('close-control',()=>control.close());
  attempt('end-dependency-boundary',()=>verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles));
  for(const fd of [captureFd,phaseFd]){attempt('fsync-stream',()=>fs.fsyncSync(fd));attempt('close-stream',()=>fs.closeSync(fd));}
  attempt('observer-state-retention',()=>putJSON('observer-final-state.json',{observer:phase.state(),error:error===null?null:String(error),secondaryErrors:secondary}));
  if(error!==null){process.exitCode=2;process.stderr.write(String(error)+'\n');}
 });
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)main().catch(error=>{process.stderr.write(String(error)+'\n');process.exitCode=2;});
