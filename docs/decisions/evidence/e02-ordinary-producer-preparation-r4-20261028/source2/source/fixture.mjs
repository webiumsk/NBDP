// SOURCE ONLY: distinct two-role minimum profile; no crypto/runtime executed by preparation.
import fs from 'node:fs';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {verifyDependencyTree} from './dependency-tree.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
import {createCaptureBudget,writeExclusiveProof,captureAccountState,createControllerStdoutEmitter} from './capture-budget.mjs';
import {ALLOCATION,createByteAccount} from './capture-allocation.mjs';
import {createProductionGuard,productionSample} from './guard-client.mjs';
import {observedExchange} from './exchange-adapter.mjs';
import {createCallbackBoundary,observedUpstreamSend,proxyContinuationValid,flowContinuationValid,createProxySocketErrorBoundary} from './proxy-observer.mjs';

const HELPER_SOURCE_PIN={"path":"/input/guard-helper.py","bytes":6219,"sha256":"743e0ed269445a4d59407336e399d1c7bd46c5337408b157e9ef85773e2157cf"};
const ORIGINAL_GUARD_PIN={"path":"/input/lease_guard.py","bytes":14846,"sha256":"d396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf"};

const DIR='/session/fixtures', PLAN='/input/fixture-plan.json';
const A='79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798';
const B='c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5';
const CASE='minimum-two-role-rs', PROFILE='e02-ordinary-minimum-rs-two-role-v3', SOCKET=DIR+'/control.sock';
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const same=(a,b)=>typeof a===typeof b&&(a===null||b===null?a===b:Array.isArray(a)||Array.isArray(b)?Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>same(x,b[i])):typeof a==='object'?Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>Object.hasOwn(b,k)&&same(a[k],b[k])):a===b);
function need(v,why){if(!v)throw Error(why);}
function pin(path){const s=fs.lstatSync(path);need(s.isFile()&&!s.isSymbolicLink(),'REGULAR_FILE');const raw=fs.readFileSync(path);return {path,bytes:raw.length,sha256:sha(raw)};}
function raw(path){const b=fs.readFileSync(path);need(b.length<=16777216,'DATA_BOUND');return b;}
function doc(path){return JSON.parse(raw(path));}
let serviceProofAccount=null,diagnosticAccount=null,activeOwner=null;
function diagnostic(error){
 if(diagnosticAccount===null)return; // No assigned owner/capacity, no proof emission.
 try{const bytes=Buffer.from(String(error).slice(0,2048)+'\n');diagnosticAccount.charge(bytes.length);process.stderr.write(bytes,secondary=>{if(secondary)activeOwner?.cancel(secondary);});}
 catch(secondary){activeOwner?.cancel(secondary);}
}
function put(path,data){const b=Buffer.isBuffer(data)?data:Buffer.from(data);need(serviceProofAccount!==null,'OWNED_SERVICE_PROOF_ACCOUNT');writeExclusiveProof({fs,path,bytes:b,account:serviceProofAccount});return pin(path);}
function putJSON(name,value){return put(DIR+'/'+name,JSON.stringify(value,null,2)+'\n');}

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
 const mode=process.argv[2];need(process.argv.length===3&&['serve','prepare','status','publish'].includes(mode),'FIXED_CLI');
 const ownerEnd=productionSample().Mono+BigInt(mode==='serve'?1800:55)*1000000000n;
 let guardFatal=error=>{process.exitCode=2;diagnostic(error);};
 const proofAccount=createByteAccount(mode==='serve'?ALLOCATION.service-ALLOCATION.serviceHeader-ALLOCATION.serviceDiagnostics:ALLOCATION.proof,'owned-proof');
 let reservationIndex=null;
 if(mode!=='serve'){const token=process.env.NBDP_CONTROLLER_AUDIT_SLOT;need(/^(?:[1-9]|[1-5][0-9]|6[0-4])$/.test(token??''),'PARENT_ASSIGNED_SLOT_BEFORE_PROOF');reservationIndex=Number(token);}
 diagnosticAccount=createByteAccount(mode==='serve'?ALLOCATION.serviceDiagnostics:ALLOCATION.diagnostics,'owned-rpc-diagnostics');
 if(mode==='serve')serviceProofAccount=proofAccount;
 const owner=createProductionGuard({helperPin:HELPER_SOURCE_PIN,guardPin:ORIGINAL_GUARD_PIN,onFatal:error=>guardFatal(error),ownerDeadlines:()=>[ownerEnd-2000000000n],cleanupDeadlines:()=>[ownerEnd],proofAccount,reservationIndex});activeOwner=owner;
 try{
 const globalContext=Buffer.from(JSON.stringify({mode}));
 const guard=(label,context,effect,options={})=>owner.run(label,context,effect,options);
 let p;
 await guard('startup:plan',globalContext,()=>{p=plan();});
 if(mode!=='serve'){
  let c=null,terminal=false,controllerWatchdog=null;const end=productionSample().Mono+45000000000n;
  const response=await new Promise((resolve,reject)=>{
   let b=Buffer.alloc(0);const fail=error=>{if(terminal)return;terminal=true;if(controllerWatchdog)clearInterval(controllerWatchdog);if(c)c.destroy();owner.cancel(error);reject(error);};
   const timer=setTimeout(()=>fail(Error('CONTROL_TIMEOUT')),45000);
   controllerWatchdog=setInterval(()=>{guard('controller:watchdog',globalContext,()=>{},{deadlines:[end]}).catch(fail);},1000);
   guard('controller:socket-create',globalContext,()=>{c=net.connect(SOCKET);
   c.on('connect',()=>{guard('controller:connect',globalContext,()=>{c.end(JSON.stringify({op:mode})+'\n');},{valid:()=>!terminal,deadlines:[end]}).catch(fail);});
   c.on('data',x=>{if(terminal)return;b=Buffer.concat([b,x]);if(b.length>1048576)fail(Error('CONTROL_REPLY_BOUND'));});
   c.on('end',()=>{if(terminal)return;if(productionSample().Mono>=end){fail(Error('CONTROL_TIMEOUT'));return;}terminal=true;clearTimeout(timer);if(controllerWatchdog)clearInterval(controllerWatchdog);try{resolve(JSON.parse(b));}catch(e){owner.cancel(e);reject(e);}});
   c.on('error',error=>{clearTimeout(timer);fail(error);});
   },{valid:()=>!terminal,deadlines:[end]}).catch(fail);
  });
  await guard('controller:response',globalContext,()=>{verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);need(response.ok===true,'FIXTURE_COMMAND_FAILED:'+response.error);},{deadlines:[end]});
  const encodedAudit=await owner.finish();
  // Terminal cleanup retention, not a new protected protocol operation.
  need(owner.state().firstFault===null,'CONTROLLER_HELPER_TERMINAL');
  const emit=createControllerStdoutEmitter({responseEncoding:JSON.stringify(response),encodedAudit,write:(bytes,callback)=>process.stdout.write(bytes,callback),isHealthy:()=>owner.state().firstFault===null,onFault:error=>{proofAccount.poison(error);owner.cancel(error);}});
  emit();return;
 }
 let T,verifyEvent,WebSocket,WebSocketServer;
 const importGuard=async(label,load)=>{const box=await guard(label,globalContext,()=>({pending:load()}));return await box.pending;};
 T=await importGuard('startup:transport-import',()=>import('./transport.mjs'));
 await guard('startup:transport-import-complete',globalContext,()=>{});
 ({verifyEvent}=await importGuard('startup:nostr-import',()=>import('nostr-tools/pure')));
 await guard('startup:verify-event-api',globalContext,()=>{need(typeof verifyEvent==='function','PINNED_VERIFY_EVENT_API');});
 ({default:WebSocket,WebSocketServer}=await importGuard('startup:ws-import',()=>import('ws')));
 let captureFd,phaseFd;
 await guard('startup:streams',globalContext,()=>{
  need(!fs.existsSync(SOCKET),'FRESH_CONTROL_SOCKET');fs.mkdirSync(DIR,{recursive:true,mode:0o700});
  captureFd=fs.openSync(DIR+'/capture.jsonl','wx',0o600);phaseFd=fs.openSync(DIR+'/phase-trace.jsonl','wx',0o600);
 });
 const budget=createCaptureBudget({fs,streams:{proxy:captureFd,phase:phaseFd},limit:proofAccount.state().limit,account:proofAccount});
 const phaseWriter=createPhaseWriter({fs:{writeSync:budget.writeSync},fd:phaseFd,clock:()=>process.hrtime.bigint(),utc:()=>new Date().toISOString(),limit:proofAccount.state().limit});
 let sequence=0,next=0,attempted=false,busy=false,closed=false,stopping=false,delivery=null,publicationGate=null,publicationInvalidated=false;
 const connections=new Map(),controlSockets=new Set();let stageIndex=0,attemptEpoch=0,activeAttempt=null,publicationWindowOpen=false,attemptSawFrame=false;
 const spec=p.roleSpec;
 let firstFailure=null,watchdog=null,control=null,server=null,stopTimer=null,streamsClosed=false;
 const phase=(name,fields={})=>{if(closed)throw firstFailure??Error('SERVICE_CLOSED');try{budget.healthy();const row=phaseWriter(name,{profileId:PROFILE,windowId:spec.windowId,ordinaryRole:p.ordinaryRole,observedAttempt:activeAttempt?{...activeAttempt}:null,...fields});budget.healthy();return row;}catch(error){const e=budget.poison(error);fatal(e);throw e;}};
 phase.state=()=>({schema:'e02-minimum-observer-state-v3',budget:budget.state(),phase:phaseWriter.state(),allocation:ALLOCATION,serviceDiagnostics:captureAccountState(diagnosticAccount),serviceHeaderPrepaidBytes:4096});
 const terminated=new WeakSet(),exchangeSockets=new Set();
 function terminateOwned(socket){if(!socket||terminated.has(socket))return;terminated.add(socket);socket.terminate();}
 class OwnedWebSocket extends WebSocket{constructor(...args){super(...args);exchangeSockets.add(this);}terminate(){if(terminated.has(this))return;terminated.add(this);super.terminate();}}
 function claimFatal(error){
  if(closed)return false;closed=true;firstFailure=error;
  owner.cancel(error); // Queue/in-flight denial before any fallible retention.
  return true;
 }
 function fatal(error){if(claimFatal(error))finishFatalCleanup(error,[]);}
 function finishFatalCleanup(error,secondary){
  const cleanupErrors=secondary.map(row=>({label:row.label,error:String(row.error)}));
  const attempt=(label,fn)=>{try{fn();}catch(e){cleanupErrors.push({label,error:String(e)});}};
  attempt('failure-retention',()=>putJSON('serve-error.json',{error:String(error),sequence,observer:phase.state(),scope:'UNQUALIFIED_NO_E02_PROMOTION'}));
  for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));
  for(const socket of exchangeSockets)attempt('terminate-owned-exchange',()=>socket.terminate());
  if(server)attempt('close-proxy-server',()=>server.close());if(control)attempt('close-control-server',()=>control.close());
  if(watchdog)attempt('clear-watchdog',()=>clearInterval(watchdog));
  if(stopTimer)attempt('clear-owner-timer',()=>clearTimeout(stopTimer));
  for(const socket of controlSockets)attempt('destroy-owned-control',()=>socket.destroy());
  attempt('end-dependency-boundary',()=>verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles));
  process.exitCode=2;
  owner.shutdownAfterFailure(error).catch(failure=>{cleanupErrors.push({label:'helper-owned-drain',error:String(failure)});}).finally(()=>{
   attempt('observer-state-retention',()=>putJSON('observer-final-state.json',{observer:phase.state(),snapshotTiming:'BEFORE_THIS_FINAL_RECORD_WRITE',error:String(firstFailure),secondaryErrors:cleanupErrors}));
   closeProofStreams(attempt);
  });
 }
 guardFatal=fatal;
 const cleanupNames=new Set(['GUARD_TERMINAL','GUARD_HELPER_STDERR','GUARD_HELPER_STDOUT_EOF','GUARD_HELPER_STDERR_EOF','GUARD_HELPER_EXIT','GUARD_HELPER_CLOSE','GUARD_HELPER_TERMINATE','GUARD_HELPER_CLEANUP_DEADLINE_EXHAUSTED']);
 function closeProofStreams(attempt){if(streamsClosed)return;streamsClosed=true;for(const fd of [captureFd,phaseFd]){attempt('fsync-stream',()=>fs.fsyncSync(fd));attempt('close-stream',()=>fs.closeSync(fd));}}
 owner.attachObserver((name,fields)=>{
  if(!closed)return phase(name,fields);
  need(cleanupNames.has(name)&&!streamsClosed,'TERMINAL_HELPER_CLEANUP_FACT_ONLY');
  budget.healthy();return phaseWriter(name,{profileId:PROFILE,windowId:spec.windowId,ordinaryRole:p.ordinaryRole,terminalRetention:true,...fields});
 }); // Startup request/reply bytes now charged to same16MiB.
 const proxySocketError=createProxySocketErrorBoundary({
  claimFault:claimFatal,
  observeFault:(error,{c,origin})=>{
   budget.healthy();
   return phaseWriter('PROXY_SOCKET_ERROR_CALLBACK_ENTRY',{profileId:PROFILE,windowId:spec.windowId,ordinaryRole:p.ordinaryRole,terminalRetention:true,connection:c?.id??null,origin,error:String(error)});
  },
  cleanupFault:(error,secondary,{pendingApp})=>{
   if(pendingApp)try{terminateOwned(pendingApp);}catch(failure){secondary.push({label:'terminate-pending-app',error:failure});}
   finishFatalCleanup(error,secondary);
  }
 });
 const callback=(fn,incomingFault=null)=>{
  if(closed||stopping)return;if(incomingFault!==null){fatal(incomingFault);return;}
  try{budget.healthy();Promise.resolve(fn()).catch(fatal);}catch(error){fatal(error);}
 };
 const live=()=>!closed;
 const serviceGuard=(label,context,effect,options={})=>guard(label,context,effect,{...options,valid:()=>!closed&&!stopping&&(options.valid?.()??true)});
 const context=value=>Buffer.from(JSON.stringify(value));
 function selectedEvent(){return prepared().events[stageIndex];}
 function selectedStage(){return stageSpec(p.ordinaryRole,stageIndex);}
 function log(value){try{budget.healthy();const row={schema:'e02-minimum-proxy-row-v1',sequence:++sequence,utc:new Date().toISOString(),...value};budget.writeSync(captureFd,Buffer.from(JSON.stringify(row)+'\n'));budget.healthy();return row;}catch(error){const e=budget.poison(error);fatal(e);throw e;}}
 function prepared(){
  const d=doc(DIR+'/prepared.json');need(d.schema==='e02-minimum-prepared-v2'&&d.profileId===PROFILE&&d.windowId===spec.windowId,'FIXED_PREPARED_PROFILE');
  for(const name of ['business','chat'])need(exactInnerShape(d.rumors[name])&&d.rumors[name].id===T.getEventHash(d.rumors[name])&&same(d.rumors[name],doc(p.oracles[name].path)),'FROZEN_SHARED_INNER');
  need(d.rumors.business.content===JSON.stringify(T.envelope(A,B,10))&&d.rumors.chat.content==='NBDP harmless ordinary chat control — faktúra 𐐀','FROZEN_CONTENT');
  need(d.events.length===spec.stages.length&&d.events.every(e=>e.kind===1059&&verifyEvent(JSON.parse(JSON.stringify(e)))&&same(e.tags,[['p',spec.account]])),'ROLE_WRAPS');
  if(p.ordinaryRole==='archive')need(same(d.events[0],d.events[1])&&d.events[2].id!==d.events[0].id,'IDENTICAL_AND_FRESH_ARCHIVE_WRAPS');return d;
 }
 function gate(){if(!fs.existsSync(DIR+'/prepared.json')||stageIndex>=spec.stages.length)return null;return matchingSubscription(connections,selectedEvent(),spec.account);}
 function invalidatePublication(c,id,reason){if(attempted&&publicationGate&&c.id===publicationGate.connection&&(id===null||id===publicationGate.subscription)){if(!publicationInvalidated)log({connection:c.id,direction:'PUBLICATION_GENERATION_INVALIDATED',reason,gate:publicationGate});publicationInvalidated=true;delivery=null;}}
 function qualifiedDelivery(before,event){return !publicationInvalidated&&delivery!==null&&attemptLineageMatches(activeAttempt,delivery.forwardAttempt,delivery.completionAttempt)&&publicationGenerationMatches(connections,before,event,spec.account)&&publicationGenerationMatches(connections,delivery.forwardGeneration,event,spec.account)&&same(delivery.forwardGeneration,delivery.completionGeneration);}
 function proxyPhase(name,c,fields={}){return phase(name,{connection:c.id,...fields});}
 function sendUpstream(c,bytes){return observedUpstreamSend({socket:c.upstream,bytes,sha,phase:(name,fields)=>proxyPhase(name,c,fields),callback,isClosed:()=>closed});}
 const connectionValid=(c,generation)=>!closed&&c.active&&c.generation===generation;
 await serviceGuard('proxy:server-create',globalContext,()=>{
  server=new WebSocketServer({host:'127.0.0.1',port:17777,maxPayload:p.limits.messageBytes,perMessageDeflate:false});
  server.on('connection',(app,request)=>callback(async()=>{
   phase('PROXY_CONNECTION_CALLBACK_ENTRY',{nextConnection:next+1});app.pause();let c;
   // Install immediate socket fault/close fences before waiting for helper.
   let pendingClosed=false;
   const pendingError=error=>{pendingClosed=true;proxySocketError(error,{c:null,origin:'APP',pendingApp:app});};
   const pendingClose=()=>{pendingClosed=true;if(!c)try{terminateOwned(app);}catch{}};
   app.on('error',pendingError);app.on('close',pendingClose);
   await serviceGuard('proxy:connection',context({nextConnection:next+1}),()=>{
    need(!pendingClosed,'APP_CLOSED_DURING_CONNECTION_GUARD');need(++next<=p.limits.connections,'CONNECTION_BOUND');
    const upstream=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
    c={id:next,active:true,generation:0,appReceiptGeneration:0,app,upstream,subscriptions:new Map(),pending:[]};connections.set(c.id,c);
    app.off('error',pendingError);app.off('close',pendingClose);
    for(const [origin,socket] of [['APP',app],['RELAY',upstream]]){
     socket.on('error',error=>proxySocketError(error,{c,origin,pendingApp:null}));
     socket.on('close',()=>{
      if(closed)return;
      // Context invalidation is an immediate denial fence, never queued.
      c.active=false;c.generation++;
      callback(()=>{proxyPhase('PROXY_SOCKET_CLOSE_CALLBACK_ENTRY',c,{origin});invalidatePublication(c,null,'CONNECTION_CLOSED');c.subscriptions.clear();terminateOwned(app);terminateOwned(upstream);log({connection:c.id,direction:'CLOSE'});});
     });
    }
    log({connection:c.id,direction:'OPEN',userAgent:String(request.headers['user-agent']??'').slice(0,1024)});
    app.on('message',(data,binary)=>callback(async()=>{
     c.appReceiptGeneration++; // Denial-only receipt fence before any await/parse.
     const bytes=Buffer.from(data),bufferHash=sha(bytes),generation=c.generation;
     proxyPhase('PROXY_RAW_CALLBACK_ENTRY',c,{origin:'APP',rawBase64:bytes.toString('base64'),binary});let forward=false;
     await serviceGuard('proxy:app-message',bytes,()=>{
      need(!binary,'TEXT_ONLY_NOSTR');const f=T.strictJSON(bytes.toString('utf8'));
      const row=log({connection:c.id,direction:'APP_TO_RELAY',rawBase64:bytes.toString('base64')});
      if(Array.isArray(f)&&f[0]==='REQ'&&typeof f[1]==='string'){invalidatePublication(c,f[1],'REQ_REPLACED');c.subscriptions.set(f[1],{req:row.sequence,eose:null,filters:f.slice(2)});}
      if(Array.isArray(f)&&f[0]==='CLOSE'){invalidatePublication(c,f[1],'APP_CLOSE');c.subscriptions.delete(f[1]);}
      if(upstream.readyState===WebSocket.OPEN)forward=true;else{need(c.pending.length<64,'PENDING_FRAME_BOUND');c.pending.push({bytes,bufferHash,generation});}
     },{valid:()=>connectionValid(c,generation)&&sha(bytes)===bufferHash});
     if(forward)await serviceGuard('proxy:app-before-upstream-send',bytes,()=>sendUpstream(c,bytes),{valid:()=>connectionValid(c,generation)&&sha(bytes)===bufferHash&&upstream.readyState===WebSocket.OPEN});
    }));
    upstream.on('open',()=>callback(async()=>{
     const generation=c.generation;proxyPhase('PROXY_SOCKET_OPEN_CALLBACK_ENTRY',c,{origin:'RELAY'});let pending;
     await serviceGuard('proxy:upstream-open',context({connection:c.id,generation}),()=>{pending=c.pending;c.pending=[];},{valid:()=>connectionValid(c,generation)});
     for(const item of pending)await serviceGuard('proxy:pending-before-upstream-send',item.bytes,()=>sendUpstream(c,item.bytes),{valid:()=>connectionValid(c,item.generation)&&sha(item.bytes)===item.bufferHash&&upstream.readyState===WebSocket.OPEN});
    }));
    upstream.on('message',(data,binary)=>callback(async()=>{
     const bytes=Buffer.from(data),bufferHash=sha(bytes),generation=c.generation,appReceiptGeneration=c.appReceiptGeneration,subscriptionSnapshot=JSON.stringify([...c.subscriptions]);let f,row,forwardAttempt,forwardGeneration;
     proxyPhase('PROXY_RAW_CALLBACK_ENTRY',c,{origin:'RELAY',rawBase64:bytes.toString('base64'),binary});
     await serviceGuard('proxy:upstream-message',bytes,()=>{
      need(!binary,'TEXT_ONLY_NOSTR');f=T.strictJSON(bytes.toString('utf8'));
      const candidate=attempted&&publicationWindowOpen&&Array.isArray(f)&&f[0]==='EVENT'&&stageIndex<spec.stages.length&&f[2]?.id===selectedEvent().id&&c.id===publicationGate?.connection&&f[1]===publicationGate?.subscription;
      forwardAttempt=candidate&&activeAttempt?{...activeAttempt}:null;
      forwardGeneration=candidate&&!publicationInvalidated&&publicationGenerationMatches(connections,publicationGate,f[2],spec.account)?currentGeneration(c,f[1]):null;
      if(candidate)attemptSawFrame=true;
      row=log({connection:c.id,direction:'RELAY_TO_APP',rawBase64:bytes.toString('base64'),publicationGeneration:forwardGeneration,publicationAttempt:forwardAttempt});
      if(Array.isArray(f)&&f[0]==='EOSE'&&c.subscriptions.has(f[1]))c.subscriptions.get(f[1]).eose=row.sequence;
      if(Array.isArray(f)&&f[0]==='CLOSED'){invalidatePublication(c,f[1],'RELAY_CLOSED');c.subscriptions.delete(f[1]);}
     },{valid:()=>connectionValid(c,generation)&&c.appReceiptGeneration===appReceiptGeneration&&JSON.stringify([...c.subscriptions])===subscriptionSnapshot&&sha(bytes)===bufferHash});
     await serviceGuard('proxy:before-app-send',bytes,()=>{
      proxyPhase('PROXY_SEND_INVOKE_ENTRY',c,{target:'APP',bufferHash,bytes:bytes.length,sourceSequence:row.sequence});
      app.send(bytes,{binary:false},error=>callback(()=>{
       proxyPhase('PROXY_SEND_CALLBACK_ENTRY',c,{target:'APP',bufferHash,sourceSequence:row.sequence,error:error?String(error):null});
       return serviceGuard('proxy:app-send-callback',bytes,()=>{
        need(sha(bytes)===bufferHash,'ACTUAL_PROXY_BUFFER_MUTATION');
        const completionAttempt=forwardAttempt&&activeAttempt?{...activeAttempt}:null;
        const completionGeneration=forwardGeneration&&publicationWindowOpen&&attemptLineageMatches(activeAttempt,forwardAttempt,completionAttempt)&&!publicationInvalidated&&publicationGenerationMatches(connections,publicationGate,f[2],spec.account)?currentGeneration(c,f[1]):null;
        const sent=log({connection:c.id,direction:'APP_SOCKET_SEND_COMPLETE',sourceSequence:row.sequence,publicationGeneration:completionGeneration,publicationAttempt:completionAttempt});
        proxyPhase('PROXY_SEND_CALLBACK_COMPLETE',c,{target:'APP',bufferHash,sourceSequence:row.sequence,sentSequence:sent.sequence});
        if(!delivery&&forwardGeneration&&completionGeneration&&same(forwardGeneration,completionGeneration))delivery={frame:bytes,event:f[2],connection:c.id,subscription:f[1],rowSequence:row.sequence,sentSequence:sent.sequence,forwardGeneration,completionGeneration,forwardAttempt,completionAttempt};
       },{valid:()=>proxyContinuationValid({connection:c,generation,appReceiptGeneration,bytes,bufferHash,sha,publicationInvalidated,currentAttempt:activeAttempt,expectedAttempt:forwardAttempt})});
      },error??null));
      if(!closed)proxyPhase('PROXY_SEND_INVOKE_RETURNED',c,{target:'APP',bufferHash,sourceSequence:row.sequence});
     },{valid:()=>app.readyState===WebSocket.OPEN&&proxyContinuationValid({connection:c,generation,appReceiptGeneration,bytes,bufferHash,sha,publicationInvalidated,currentGeneration:currentGeneration(c,f[1]),expectedGeneration:forwardGeneration,currentAttempt:activeAttempt,expectedAttempt:forwardAttempt})});
    }));
    app.resume();
   },{valid:()=>!pendingClosed});
  }));server.on('error',fatal);
 });
 async function exchange(events,filter,label){
  return await observedExchange({WebSocket:OwnedWebSocket,p,guard:serviceGuard,fail:fatal,phase,log,put:(name,bytes)=>put(DIR+'/'+name,bytes),strictJSON:T.strictJSON,sha,clock:()=>process.hrtime.bigint(),arm:setTimeout,clear:clearTimeout},events,filter,label);
 }
 function* prepareFlow(){
  yield {guard:'flow:original-01'};need(!fs.existsSync(DIR+'/prepared.json'),'PREPARE_ONCE');
  const from=T.secret(1),local=T.secret(spec.scalar),rumors={business:doc(p.oracles.business.path),chat:doc(p.oracles.chat.path)};
  need(T.getPublicKey(from)===A&&T.getPublicKey(local)===spec.account,'PUBLIC_ROLE_IDENTITIES');
  for(const r of Object.values(rumors))need(exactInnerShape(r)&&r.id===T.getEventHash(r),'FROZEN_INPUT_RUMOR_ID');
  yield {guard:'flow:original-02'};const initial=T.wrap(rumors.business,from,spec.account);
  const events=p.ordinaryRole==='incoming'?[initial,T.wrap(rumors.chat,from,B)]:[initial,initial,T.wrap(rumors.business,from,A)];
  const expected={};for(let i=0;i<spec.stages.length;i++){const s=stageSpec(p.ordinaryRole,i);expected[s.id]={stage:s,rumor:putJSON(s.id+'-expected-rumor.json',rumors[s.oracle]),content:put(DIR+'/'+s.id+'-expected-content.txt',rumors[s.oracle].content)};}
  const preparedPin=putJSON('prepared.json',{schema:'e02-minimum-prepared-v2',profileId:PROFILE,windowId:spec.windowId,role:p.ordinaryRole,rumors,events,expected});
  prepared();yield {guard:'flow:original-03'};const now=Math.floor(Date.now()/1000),inboxes=[T.secret(1),T.secret(2)].map(sk=>T.finalizeEvent({kind:10050,created_at:now,tags:[['relay',p.proxyUrl]],content:''},sk));
  const r=(yield {wait:exchange(inboxes,null,'prepare-inboxes')});yield {guard:'flow:original-04'};const inboxPin=putJSON('inboxes.json',{events:inboxes,...r});
  return {profileId:PROFILE,windowId:spec.windowId,ordinaryRole:p.ordinaryRole,expected,prepared:preparedPin,inboxes:inboxPin};
 }
 function* validateFlow(frame,queried,stage,origin){yield {guard:'flow:original-05'};const f=T.strictJSON(frame.toString('utf8'));need(f[0]==='EVENT'&&same(f[2],queried),'ACTUAL_VALIDATED_FRAME_QUERY_JOIN');const wire=JSON.stringify(f[2]);const request={op:'validate',wire,secret:String(spec.scalar).padStart(64,'0'),role:spec.validationRole,expectedSender:A};const framePin=put(DIR+'/'+stage.id+'-frame.json',frame),wirePin=put(DIR+'/'+stage.id+'-wire.json',wire);const jsRequest=putJSON(stage.id+'-js-request.json',request),rustRequest=putJSON(stage.id+'-rust-request.json',request);yield {guard:'flow:original-06'};const js=T.validate(wire,T.secret(spec.scalar),{role:spec.validationRole,expectedSender:A});const jsResult=putJSON(stage.id+'-js-result.json',js);yield {guard:'flow:original-07'};const requests=[{op:'source'},request],stdin=requests.map(x=>JSON.stringify(x)).join('\n')+'\n';const input=put(DIR+'/'+stage.id+'-Rust-stdin.jsonl',stdin);const native=spawnSync(p.pins.rustBinary.path,[],{input:stdin,timeout:p.limits.rustTimeoutMilliseconds,maxBuffer:1048576,env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8'}});const stdout=put(DIR+'/'+stage.id+'-Rust-stdout.jsonl',native.stdout??Buffer.alloc(0)),stderr=put(DIR+'/'+stage.id+'-Rust-stderr.bin',native.stderr??Buffer.alloc(0));yield {guard:'flow:original-08'};need(!native.error&&native.status===0&&native.signal===null&&(native.stderr?.length??0)===0,'NATURAL_RUST_VALIDATION');const replies=String(native.stdout).trimEnd().split('\n').map(x=>T.strictJSON(x));need(replies.length===2&&replies[0].ok===true&&replies[0].value===fs.readFileSync(p.pins.rustSource.path,'utf8')&&replies[1].ok===true,'CURRENT_RUST_SOURCE_REPLY');const rust=replies[1].value,rustResult=putJSON(stage.id+'-rust-result.json',rust);need(same(js,rust)&&js.ok===true&&same(js.value.rumor,prepared().rumors[stage.oracle])&&js.value.dispatch===stage.dispatch&&js.value.role===stage.normalizedRole,'INDEPENDENT_VALIDATED_FRAME_ROLE_RESULT');const transport=putJSON(stage.id+'-consumer-transport.json',{schema:'e02-minimum-transport-v2',frame:framePin,wire:wirePin,jsRequest,rustRequest,jsResult,rustResult});const validation=putJSON(stage.id+'-validation.json',{schema:'e02-minimum-validated-wire-record-v2',profileId:PROFILE,windowId:spec.windowId,stageId:stage.id,origin,clientReceiptEstablished:origin==='ACTUAL_APP_SOCKET_FRAME',transport,rustBinary:p.pins.rustBinary,rustSource:p.pins.rustSource,rustInput:input,rustStdout:stdout,rustStderr:stderr,rustExit:native.status,rustSignal:native.signal,actualQueriedEvent:queried,js,rust,clientRetention:'NOT_ESTABLISHED_BY_TRANSPORT_VALIDATION'});return {transport,validation};}
 function* publishFlow(){
  const phaseStartSequence=phaseWriter.state().sequence+1;
  yield {guard:'flow:original-09'};need(stageIndex<spec.stages.length&&!publicationInvalidated,'FINITE_ROLE_STAGE_OR_STICKY_FAILURE');
  const d=prepared(),stage=selectedStage(),event=d.events[stageIndex],initial=d.events[0],before=gate();
  need(before!==null&&replayBinding(stage,event,initial),'CURRENT_STAGE_BINDINGS_REQUIRED');
  publicationGate=before;delivery=null;attempted=true;activeAttempt={epoch:++attemptEpoch,stageId:stage.id};
  publicationWindowOpen=true;attemptSawFrame=false;const windowStarted=process.hrtime.bigint();
  const intentRow=log({direction:'PUBLICATION_INTENT',stageId:stage.id,eventId:event.id,attempt:activeAttempt});
  const intent=putJSON(stage.id+'-publish-intent.json',{schema:'e02-minimum-publish-intent-v2',profileId:PROFILE,windowId:spec.windowId,stage,attempt:activeAttempt,intentSequence:intentRow.sequence,prepared:pin(DIR+'/prepared.json'),gate:before,issuedUTC:new Date().toISOString()});
  yield {guard:'flow:original-10'};const publication=(yield {wait:exchange([event],null,stage.id+'-publish')});yield {guard:'flow:original-11'};
  const until=process.hrtime.bigint()+10000000000n;
  while(!delivery&&!publicationInvalidated&&process.hrtime.bigint()<until){yield {guard:'flow:original-12'};yield {wait:new Promise(r=>setTimeout(r,100))};}
  yield {guard:'flow:original-13'};need(!publicationInvalidated&&publicationGenerationMatches(connections,before,event,spec.account),'CURRENT_GENERATION_AFTER_PUBLICATION');
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
  const query=(yield {wait:exchange(null,{ids:[event.id],limit:1},stage.id+'-query')});yield {guard:'flow:original-14'};need(query.received.length===1&&same(query.received[0].frame[2],event),'EXACT_PUBLISHED_EVENT_QUERY');
  const validation=yield* validateFlow(observed?delivery.frame:Buffer.from(query.received[0].rawBase64,'base64'),query.received[0].frame[2],stage,observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME');
  const produced=JSON.stringify(event),producerResult=T.validate(produced,T.secret(spec.scalar),{role:spec.validationRole,expectedSender:A});
  need(producerResult.ok===true&&same(producerResult.value.rumor,d.rumors[stage.oracle])&&producerResult.value.dispatch===stage.dispatch&&producerResult.value.role===stage.normalizedRole,'DECLARED_ROLE_DISPATCH_ELIGIBILITY');
  const producerValidation=putJSON(stage.id+'-producer-validation.json',{schema:'e02-minimum-producer-validation-v2',stageId:stage.id,actualPublishedEvent:event,result:producerResult,meaning:'Producer validation only; not a business effect or substitute for actual app wire/export.'});
  yield {guard:'flow:original-15'};need(!publicationInvalidated&&publicationGenerationMatches(connections,before,event,spec.account),'CURRENT_GENERATION_BEFORE_STAGE_RECORD');
  const observation={schema:'e02-minimum-stage-observation-range-v2',phaseStartSequence,phaseEndSequence:phaseWriter.state().sequence,proxyEndSequence:sequence,observer:phase.state(),phaseTracePath:DIR+'/phase-trace.jsonl',proxyCapturePath:DIR+'/capture.jsonl',streamPins:'FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS'};
  const record=putJSON(stage.id+'-publication.json',{observation,schema:'e02-minimum-stage-publication-v2',profileId:PROFILE,windowId:spec.windowId,stage,attempt:activeAttempt,intent,publicationWindow,gate:before,publication,query,event,
   actualNewAppFrameObserved:observed,delivery:observed?{connection:delivery.connection,subscription:delivery.subscription,rowSequence:delivery.rowSequence,sentSequence:delivery.sentSequence,forwardGeneration:delivery.forwardGeneration,completionGeneration:delivery.completionGeneration,forwardAttempt:delivery.forwardAttempt,completionAttempt:delivery.completionAttempt}:null,
   validation,producerValidation,clientRetention:'UNVERIFIED_REQUIRES_FRESH_CLIENT_SELECTION_EXPORT',validationOrigin:observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME',
   replayLimit:stage.identicalReplay&&!observed?'No new frame observed in bounded interval; retain honest publication/query/history and require post-replay real client export. No synthesized EVENT or earlier-frame donation.':null});
  stageIndex++;attempted=false;activeAttempt=null;
  return {profileId:PROFILE,windowId:spec.windowId,stage,publication:record,publicationWindow,validation,producerValidation,actualNewAppFrameObserved:observed};
 }
 async function runFlow(iterator,name){
  let step=iterator.next();
  while(!step.done){
   if(step.value.guard){
    const index=stageIndex,attempt=activeAttempt?{...activeAttempt}:null;
    const expectedGate=name==='publish'?(publicationGate??gate()):null;
    const connection=expectedGate?(connections.get(expectedGate.connection)??null):null,expectedReceipt=connection?.appReceiptGeneration??null;
    const bytes=context({flow:name,stageIndex:index,attempt,expectedGate,expectedReceipt});
    step=await serviceGuard(step.value.guard,bytes,()=>iterator.next(),{valid:()=>flowContinuationValid({stageIndex,expectedIndex:index,activeAttempt,expectedAttempt:attempt,publish:name==='publish',publicationInvalidated,connection,expectedReceipt,currentGenerationMatches:expectedGate===null||publicationGenerationMatches(connections,expectedGate,selectedEvent(),spec.account)})});
   }else{
    need(Object.keys(step.value).length===1&&step.value.wait instanceof Promise,'CLOSED_FLOW_WAIT');
    // The generator resumes only to lexical assignment/loop predicate and the
    // next guard yield. Original protocol effects remain within guard.next().
    const value=await step.value.wait;step=iterator.next(value);
   }
  }
  return step.value;
 }
 control=net.createServer({allowHalfOpen:true},socket=>{
  controlSockets.add(socket);let b='',terminal=false;
  socket.on('close',()=>{terminal=true;controlSockets.delete(socket);});socket.on('error',fatal);
  socket.on('data',chunk=>{if(closed||terminal)return;b+=chunk.toString('utf8');if(Buffer.byteLength(b)>1024){terminal=true;socket.destroy();fatal(Error('CONTROL_REQUEST_BOUND'));}});
  socket.on('end',()=>callback(async()=>{
   let acquired=false;try{
    let q;
    await serviceGuard('control:command',Buffer.from(b),()=>{
     q=JSON.parse(b);need(Object.keys(q).length===1&&['prepare','status','publish'].includes(q.op),'FIXED_CONTROL_OPERATION');need(!busy,'COMMAND_IN_PROGRESS');busy=true;acquired=true;
    },{valid:()=>!terminal});
    let result;if(q.op==='prepare')result=await runFlow(prepareFlow(),'prepare');else if(q.op==='publish')result=await runFlow(publishFlow(),'publish');
    await serviceGuard('control:response',context({op:q.op}),()=>{
     if(q.op==='status')result={profileId:PROFILE,windowId:spec.windowId,stageId:stageIndex<spec.stages.length?selectedStage().id:null,stageIndex,complete:stageIndex===spec.stages.length,ready:gate()!==null,gate:gate(),captureSequence:sequence,scope:'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT'};
     verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);
     socket.end(JSON.stringify({schema:'e02-minimum-fixture-command-v3',profileId:PROFILE,windowId:spec.windowId,operation:q.op,caseId:CASE,ok:true,result})+'\n');
    },{valid:()=>!terminal});
   }catch(error){fatal(error);try{socket.end(JSON.stringify({ok:false,error:String(error)})+'\n');}catch{}}
   finally{if(acquired)busy=false;}
  }));
 });
 control.on('error',fatal);
 await serviceGuard('control:listen',globalContext,()=>{
  control.listen(SOCKET,()=>callback(()=>serviceGuard('control:ready',globalContext,()=>{fs.chmodSync(SOCKET,0o600);putJSON('serve-ready.json',{schema:'e02-fixture-service-ready-v1',caseId:CASE,proxy:p.proxyUrl,backend:p.backendUrl,scope:'NO_CLIENT_RECEIPT_OR_E02_PASS'});}))); 
 });
 watchdog=setInterval(()=>callback(()=>serviceGuard('watchdog:tick',globalContext,()=>{})),1000);
 // Reserve2s of the ORIGINAL owner clock for owned helper cleanup; no extension.
 stopTimer=setTimeout(()=>fatal(Error('ORIGINAL_OWNER_CLEANUP_RESERVE')),Math.max(0,Number((owner.effectDeadlineMonoNs-productionSample().Mono)/1000000n)));
 for(const sig of ['SIGTERM','SIGINT'])process.on(sig,()=>{try{
  if(closed||stopping)return;
  if(busy||owner.state().pending!==0){fatal(Error('OWNED_SERVICE_SIGNAL_WITH_PENDING:'+sig));return;}
  stopping=true;clearTimeout(stopTimer);clearInterval(watchdog);
  // Zero-pending orderly owner CLOSE; socket shutdown is separately owned cleanup.
  for(const c of connections.values())for(const socket of [c.app,c.upstream])terminateOwned(socket);
  for(const socket of exchangeSockets)socket.terminate();for(const socket of controlSockets)socket.destroy();
  server.close();control.close();
  owner.finish().then(()=>{
   verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);
   putJSON('observer-final-state.json',{observer:phase.state(),snapshotTiming:'BEFORE_THIS_FINAL_RECORD_WRITE',error:null,secondaryErrors:[],normalOwnedHelperClose:true});
   closed=true;streamsClosed=true;for(const fd of [captureFd,phaseFd]){fs.fsyncSync(fd);fs.closeSync(fd);}
  }).catch(fatal);
 }catch(error){fatal(error);}});
 }catch(error){await owner.shutdownAfterFailure(error).catch(cleanup=>{diagnostic('OWNED_GUARD_CLEANUP:'+String(cleanup));});throw error;}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)main().catch(error=>{diagnostic(error);process.exitCode=2;});
