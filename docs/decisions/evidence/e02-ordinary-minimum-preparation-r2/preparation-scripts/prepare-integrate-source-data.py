from pathlib import Path
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');P=R/'experiments/prototypes/e02_ordinary_minimum_v2'
s=(P/'fixture.mjs').read_text()
s=s.replace("import {pathToFileURL} from 'node:url';", "import {pathToFileURL} from 'node:url';\nimport {verifyDependencyTree} from './dependency-tree.mjs';\nimport {createPhaseWriter} from './phase-writer.mjs';\nimport {createCaptureBudget,observedGuard} from './capture-budget.mjs';\nimport {observedExchange} from './exchange-adapter.mjs';")
s=s.replace('function check(){','function guardCheck(){',1)
pos=s.index('\nfunction plan()')
s=s[:pos]+"\nlet servicePhase=null;\nfunction check(label='original-unlabeled'){\n if(servicePhase!==null)return observedGuard(guardCheck,servicePhase,label);\n return guardCheck(); // Startup/controller guards remain real but untraced.\n}\n"+s[pos:]
s=s.replace(" const e01=doc(p.pins.e01.path),e02=doc(p.pins.e02.path);", " const tree=pin(p.dependencyTree.path);need(tree.bytes===p.dependencyTree.bytes&&tree.sha256===p.dependencyTree.sha256,'EXACT_DEPENDENCY_TREE_PIN');\n verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);\n const e01=doc(p.pins.e01.path),e02=doc(p.pins.e02.path);")
s=s.replace("const captureFd=fs.openSync(DIR+'/capture.jsonl','wx',0o600);let sequence=0,total=0,", "const captureFd=fs.openSync(DIR+'/capture.jsonl','wx',0o600),phaseFd=fs.openSync(DIR+'/phase-trace.jsonl','wx',0o600);\n const budget=createCaptureBudget({fs,streams:{proxy:captureFd,phase:phaseFd},limit:p.limits.captureBytes});\n const phaseWriter=createPhaseWriter({fs:{writeSync:budget.writeSync},fd:phaseFd,clock:()=>process.hrtime.bigint(),utc:()=>new Date().toISOString(),limit:p.limits.captureBytes});\n const phase=(name,fields={})=>{try{budget.healthy();const row=phaseWriter(name,fields);budget.healthy();return row;}catch(error){throw budget.poison(error);}};\n phase.state=()=>({schema:'e02-minimum-observer-state-v2',budget:budget.state(),phase:phaseWriter.state()});servicePhase=phase;\n let sequence=0,")
old="function log(value){const row={schema:'e02-minimum-proxy-row-v1',sequence:++sequence,utc:new Date().toISOString(),...value};const b=Buffer.from(JSON.stringify(row)+'\\n');total+=b.length;need(total<=p.limits.captureBytes,'CAPTURE_BOUND');fs.writeSync(captureFd,b);return row;}"
assert old in s
s=s.replace(old,"function log(value){try{budget.healthy();const row={schema:'e02-minimum-proxy-row-v1',sequence:++sequence,utc:new Date().toISOString(),...value};const b=Buffer.from(JSON.stringify(row)+'\\n');budget.writeSync(captureFd,b);budget.healthy();return row;}catch(error){throw budget.poison(error);}}")
a=s.index(' function fatal(error)');b=s.index(' async function prepare()',a)
proxy=r''' const terminated=new WeakSet();let firstFailure=null,watchdog=null,control=null;
 function terminateOwned(socket){if(!socket||terminated.has(socket))return;terminated.add(socket);socket.terminate();}
 class OwnedWebSocket extends WebSocket{terminate(){if(terminated.has(this))return;terminated.add(this);super.terminate();}}
 // Exchange owns its exact sockets; proxy owns the paired app/backend sockets.
 // Observation failure cannot skip cleanup or replace an incoming socket fault.
 function fatal(error){
  if(closed)return;closed=true;firstFailure=error;
  const cleanupErrors=[];
  const attempt=(label,fn)=>{try{fn();}catch(e){cleanupErrors.push({label,error:String(e)});}};
  attempt('failure-retention',()=>putJSON('serve-error.json',{error:String(error),sequence,
   observer:phase.state(),scope:'UNQUALIFIED_NO_E02_PROMOTION'}));
  for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));
  attempt('close-proxy-server',()=>server.close());if(control)attempt('close-control-server',()=>control.close());
  if(watchdog)attempt('clear-watchdog',()=>clearInterval(watchdog));
  attempt('end-dependency-boundary',()=>verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles));
  attempt('observer-state-retention',()=>putJSON('observer-final-state.json',{observer:phase.state(),error:String(firstFailure),secondaryErrors:cleanupErrors}));
  process.exitCode=2;
 }
 function callback(fn,incomingFault=null){if(closed)return;try{budget.healthy();fn();}catch(error){fatal(incomingFault??error);}}
 function proxyPhase(name,c,fields={}){return phase(name,{connection:c.id,...fields});}
 function sendUpstream(c,bytes){
  const bufferHash=sha(bytes);
  proxyPhase('PROXY_SEND_INVOKE_ENTRY',c,{target:'RELAY',bufferHash,bytes:bytes.length});
  c.upstream.send(bytes,{binary:false},error=>callback(()=>{
   proxyPhase('PROXY_SEND_CALLBACK_ENTRY',c,{target:'RELAY',bufferHash,error:error?String(error):null});
   if(error)throw error;need(sha(bytes)===bufferHash,'ACTUAL_PROXY_BUFFER_MUTATION');
   proxyPhase('PROXY_SEND_CALLBACK_COMPLETE',c,{target:'RELAY',bufferHash});
   // Evidence-only callback: no new guard, protocol state, decode or send.
  },error??null));
  if(!closed)proxyPhase('PROXY_SEND_INVOKE_RETURNED',c,{target:'RELAY',bufferHash});
 }
 const server=new WebSocketServer({host:'127.0.0.1',port:17777,maxPayload:p.limits.messageBytes,perMessageDeflate:false});
 server.on('connection',(app,request)=>{try{
  if(closed){terminateOwned(app);return;}
  phase('PROXY_CONNECTION_CALLBACK_ENTRY',{nextConnection:next+1});check('proxy:connection');
  need(++next<=p.limits.connections,'CONNECTION_BOUND');
  const upstream=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
  const c={id:next,active:true,app,upstream,subscriptions:new Map(),pending:[]};connections.set(c.id,c);
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
  for(const [origin,socket] of [['APP',app],['RELAY',upstream]]){
   socket.on('error',error=>callback(()=>{proxyPhase('PROXY_SOCKET_ERROR_CALLBACK_ENTRY',c,{origin,error:String(error)});throw error;},error));
   socket.on('close',()=>callback(()=>{
    proxyPhase('PROXY_SOCKET_CLOSE_CALLBACK_ENTRY',c,{origin});invalidatePublication(c,null,'CONNECTION_CLOSED');
    c.active=false;c.subscriptions.clear();terminateOwned(app);terminateOwned(upstream);log({connection:c.id,direction:'CLOSE'});
   }));
  }
 }catch(error){terminateOwned(app);fatal(error);}});
 server.on('error',fatal);
 async function exchange(events,filter,label){
  return await observedExchange({WebSocket:OwnedWebSocket,p,check,phase,log,
   put:(name,bytes)=>put(DIR+'/'+name,bytes),strictJSON:T.strictJSON,sha,
   clock:()=>process.hrtime.bigint(),arm:setTimeout,clear:clearTimeout},events,filter,label);
 }
'''
s=s[:a]+proxy+s[b:]
# Emit additive range/state operands without prematurely pinning mutable streams.
s=s.replace("  check();need(stageIndex<spec.stages.length", "  const phaseStartSequence=phaseWriter.state().sequence+1;\n  check();need(stageIndex<spec.stages.length")
s=s.replace("  const record=putJSON(stage.id+'-publication.json',{schema:", "  const observation={schema:'e02-minimum-stage-observation-range-v2',phaseStartSequence,phaseEndSequence:phaseWriter.state().sequence,proxyEndSequence:sequence,observer:phase.state(),phaseTracePath:DIR+'/phase-trace.jsonl',proxyCapturePath:DIR+'/capture.jsonl',streamPins:'FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS'};\n  const record=putJSON(stage.id+'-publication.json',{observation,schema:")
# Avoid changing original failure response semantics for a healthy service. A
# poisoned observer is fatal and may not accept a subsequent command/query.
s=s.replace(" const control=net.createServer", " control=net.createServer")
s=s.replace(" const watchdog=setInterval", " watchdog=setInterval")
s=s.replace("}catch(error){try{putJSON('command-error-'", "}catch(error){if(budget.state().poisoned)fatal(error);try{putJSON('command-error-'")
# End closure and fsync of BOTH streams retain actual failures, preservefirst.
a=s.index(" for(const sig of ['SIGTERM','SIGINT'])")
b=s.index('\n}',a)
s=s[:a]+r''' for(const sig of ['SIGTERM','SIGINT'])process.on(sig,()=>{
  if(closed)return;closed=true;let error=null;const secondary=[];
  const attempt=(name,fn)=>{try{fn();}catch(e){if(error===null)error=e;else secondary.push({name,error:String(e)});}};
  clearInterval(watchdog);
  for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));
  attempt('close-server',()=>server.close());attempt('close-control',()=>control.close());
  attempt('end-dependency-boundary',()=>verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles));
  for(const fd of [captureFd,phaseFd]){attempt('fsync-stream',()=>fs.fsyncSync(fd));attempt('close-stream',()=>fs.closeSync(fd));}
  attempt('observer-state-retention',()=>putJSON('observer-final-state.json',{observer:phase.state(),error:error===null?null:String(error),secondaryErrors:secondary}));
  if(error!==null){process.exitCode=2;process.stderr.write(String(error)+'\n');}
 });'''+s[b:]
(P/'fixture.mjs').write_text(s)
print('SOURCE_ADAPTERS_WRITTEN_NO_EVALUATION')
