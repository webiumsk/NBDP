"""SOURCE text transformation only; does not import/evaluate any JS module."""
from pathlib import Path

ROOT = Path('/home/peterhorvath/apps/bitcoin/NBDP')
BASE = ROOT / 'experiments/prototypes/e02_ordinary_client_api35_v3/fixture.mjs'
OUT = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v1/fixture.mjs'
text = BASE.read_text()
text = text.replace('// SOURCE ONLY: one synthetic ordinary-client envelope cell; no E02 PASS claim.',
    '// SOURCE ONLY: distinct two-role minimum profile; no crypto/runtime executed by preparation.')
text = text.replace("const CASE='js-to-rust-incoming-rs', SOCKET=DIR+'/control.sock';",
    "const CASE='minimum-two-role-rs', PROFILE='e02-ordinary-minimum-rs-two-role-v1', SOCKET=DIR+'/control.sock';")
old = "need(p.schema==='e02-single-cell-fixture-plan-v1'&&p.caseId===CASE&&p.direction==='JS_TO_RUST'&&p.role==='incoming'&&p.relay==='rs-relay'&&p.senderScalar===1&&p.recipientScalar===2&&p.envelopeNumber===10&&p.proxyUrl==='ws://127.0.0.1:17777'&&p.backendUrl==='ws://127.0.0.1:8080'&&p.output===DIR,'FIXED_FIRST_SLICE');"
new = """need(p.schema==='e02-ordinary-minimum-fixture-plan-v1'&&p.caseId===CASE&&p.profileId===PROFILE&&p.direction==='JS_TO_RUST'&&p.relay==='rs-relay'&&p.proxyUrl==='ws://127.0.0.1:17777'&&p.backendUrl==='ws://127.0.0.1:8080'&&p.output===DIR,'FIXED_MINIMUM_PROFILE');
 const configRaw=raw('/input/run-config.json');
 need(sha(configRaw)===process.env.NBDP_MINIMUM_RUN_CONFIG_SHA256,'EXTERNAL_ROLE_CONFIG_SHA');
 const config=JSON.parse(configRaw);need(config.profileId===PROFILE&&['incoming','archive'].includes(config.ordinaryRole),'CLOSED_ROLE_CONFIG');
 const spec=roleSpec(config.ordinaryRole);need(config.windowId===spec.windowId&&config.account===spec.account&&config.peer===spec.peer,'ROLE_ACCOUNT_BINDING');
 p.ordinaryRole=config.ordinaryRole;p.roleSpec=spec;
 for(const d of Object.values(p.oracles)){const q=pin(d.path);need(q.bytes===d.bytes&&q.sha256===d.sha256,'FROZEN_ORACLE_PIN');} """
assert old in text
text = text.replace(old, new)
insert = """
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
"""
text = text.replace('\nasync function main(){', insert + '\nasync function main(){')
text = text.replace("const connections=new Map();", "const connections=new Map();let stageIndex=0,attemptEpoch=0,activeAttempt=null,publicationWindowOpen=false,attemptSawFrame=false;\n const spec=p.roleSpec;\n function selectedEvent(){return prepared().events[stageIndex];}\n function selectedStage(){return stageSpec(p.ordinaryRole,stageIndex);}")
a = text.index(' function prepared(){'); b = text.index(' function invalidatePublication', a)
text = text[:a] + """ function prepared(){
  const d=doc(DIR+'/prepared.json');need(d.schema==='e02-minimum-prepared-v1'&&d.profileId===PROFILE&&d.windowId===spec.windowId,'FIXED_PREPARED_PROFILE');
  for(const name of ['business','chat'])need(exactInnerShape(d.rumors[name])&&d.rumors[name].id===T.getEventHash(d.rumors[name])&&same(d.rumors[name],doc(p.oracles[name].path)),'FROZEN_SHARED_INNER');
  need(d.rumors.business.content===JSON.stringify(T.envelope(A,B,10))&&d.rumors.chat.content==='NBDP harmless ordinary chat control — faktúra 𐐀','FROZEN_CONTENT');
  need(d.events.length===spec.stages.length&&d.events.every(e=>e.kind===1059&&verifyEvent(JSON.parse(JSON.stringify(e)))&&same(e.tags,[['p',spec.account]])),'ROLE_WRAPS');
  if(p.ordinaryRole==='archive')need(same(d.events[0],d.events[1])&&d.events[2].id!==d.events[0].id,'IDENTICAL_AND_FRESH_ARCHIVE_WRAPS');
  return d;
 }
 function gate(){if(!fs.existsSync(DIR+'/prepared.json')||stageIndex>=spec.stages.length)return null;return matchingSubscription(connections,selectedEvent(),spec.account);}
""" + text[b:]
text = text.replace('if(publicationGate&&c.id===', 'if(attempted&&publicationGate&&c.id===')
text = text.replace("publicationGenerationMatches(connections,before,event,B)", "publicationGenerationMatches(connections,before,event,spec.account)")
text = text.replace("publicationGenerationMatches(connections,delivery.forwardGeneration,event,B)", "publicationGenerationMatches(connections,delivery.forwardGeneration,event,spec.account)")
text = text.replace("publicationGenerationMatches(connections,delivery.completionGeneration,event,B)", "publicationGenerationMatches(connections,delivery.completionGeneration,event,spec.account)")
text = text.replace("f[2]?.id===prepared().events[0].id", "stageIndex<spec.stages.length&&f[2]?.id===selectedEvent().id")
text = text.replace("publicationGenerationMatches(connections,publicationGate,f[2],B)", "publicationGenerationMatches(connections,publicationGate,f[2],spec.account)")
text = text.replace('return !publicationInvalidated&&delivery!==null&&', 'return !publicationInvalidated&&delivery!==null&&attemptLineageMatches(activeAttempt,delivery.forwardAttempt,delivery.completionAttempt)&&')
text = text.replace('const candidate=attempted&&', 'const candidate=attempted&&publicationWindowOpen&&')
text = text.replace('const row=log({connection:c.id,direction:\'RELAY_TO_APP\'', 'if(candidate)attemptSawFrame=true;\n   const row=log({connection:c.id,direction:\'RELAY_TO_APP\'')
text = text.replace('const forwardGeneration=candidate', 'const forwardAttempt=candidate&&activeAttempt?{...activeAttempt}:null;\n   const forwardGeneration=candidate')
text = text.replace('const completionGeneration=forwardGeneration&&!publicationInvalidated&&', 'const completionAttempt=forwardAttempt&&activeAttempt?{...activeAttempt}:null;\n    const completionGeneration=forwardGeneration&&publicationWindowOpen&&attemptLineageMatches(activeAttempt,forwardAttempt,completionAttempt)&&!publicationInvalidated&&')
text = text.replace('sentSequence:sent.sequence,forwardGeneration,completionGeneration}', 'sentSequence:sent.sequence,forwardGeneration,completionGeneration,forwardAttempt,completionAttempt}')
text = text.replace("rawBase64:bytes.toString('base64'),publicationGeneration:forwardGeneration", "rawBase64:bytes.toString('base64'),publicationGeneration:forwardGeneration,publicationAttempt:forwardAttempt")
text = text.replace("sourceSequence:row.sequence,publicationGeneration:completionGeneration", "sourceSequence:row.sequence,publicationGeneration:completionGeneration,publicationAttempt:completionAttempt")
a = text.index(' async function exchange('); b = text.index(' async function prepare(', a)
text = text[:a] + """ async function exchange(events,filter,label){
  check();need(typeof label==='string'&&/^[a-z0-9-]{1,48}$/.test(label),'FIXED_EXCHANGE_LABEL');
  const started=process.hrtime.bigint();
  return await new Promise((resolve,reject)=>{
   const ws=new WebSocket(p.backendUrl,{perMessageDeflate:false,handshakeTimeout:3000,maxPayload:p.limits.messageBytes});
   const ack=[],received=[],sentFrames=[];let settled=false,queryEnded=false,eose=null;
   const timer=setTimeout(()=>finish(Error('RELAY_TIMEOUT')),p.limits.networkTimeoutMilliseconds);
   function finish(error){
    if(settled)return;settled=true;clearTimeout(timer);ws.terminate();
    const elapsedNanoseconds=Number(process.hrtime.bigint()-started);
    if(error){reject(error);return;}
    resolve({ack,received,eose,sentFrames,elapsedNanoseconds});
   }
   function maybeComplete(){
    if(!sentFrames.length||!sentFrames.every(row=>row.sendCallbackCompleted))return;
    if(events&&events.every(event=>ack.some(row=>row.frame[1]===event.id&&row.frame[2]===true)))finish();
    else if(filter&&queryEnded)finish();
   }
   function sendKnown(frame,eventId){
    check();const bytes=Buffer.from(JSON.stringify(frame));
    const framePin=put(DIR+'/'+label+'-'+sentFrames.length+'-sent-frame.json',bytes);
    const row={frame:framePin,eventId,messageType:frame[0],sendInvoked:true,sendCallbackCompleted:false,callbackBufferHash:null};
    sentFrames.push(row);
    log({direction:'PRODUCER_TO_RELAY',exchangeLabel:label,rawBase64:bytes.toString('base64'),frame:framePin});
    ws.send(bytes,{binary:false},error=>{try{
     check();if(error)throw error;
     need(sha(bytes)===framePin.sha256,'ACTUAL_SENT_BUFFER_MUTATION');
     row.sendCallbackCompleted=true;row.callbackBufferHash=sha(bytes);maybeComplete();
    }catch(error){finish(error);}});
   }
   ws.on('open',()=>{try{
    check();for(const event of events??[])sendKnown(['EVENT',event],event.id);
    if(filter)sendKnown(['REQ','e02-owned-query',filter],null);
   }catch(error){finish(error);}});
   ws.on('message',data=>{try{
    check();const bytes=Buffer.from(data);
    log({direction:'RELAY_TO_PRODUCER',exchangeLabel:label,rawBase64:bytes.toString('base64')});
    const frame=T.strictJSON(bytes.toString('utf8'));
    if(frame[0]==='OK'){ack.push({rawBase64:bytes.toString('base64'),frame});need(frame[2]===true,'RELAY_REFUSAL');}
    if(frame[0]==='EVENT'&&frame[1]==='e02-owned-query')received.push({rawBase64:bytes.toString('base64'),frame});
    if(frame[0]==='EOSE'&&frame[1]==='e02-owned-query'){eose={rawBase64:bytes.toString('base64'),frame};queryEnded=true;}
    maybeComplete();
   }catch(error){finish(error);}});
   ws.on('error',finish);ws.on('close',()=>{if(!settled)finish(Error('EARLY_RELAY_CLOSE'));});
  });
 }
""" + text[b:]
a = text.index(' async function prepare(){'); b = text.index(' function validateActual', a)
text = text[:a] + """ async function prepare(){
  check();need(!fs.existsSync(DIR+'/prepared.json'),'PREPARE_ONCE');
  const from=T.secret(1),local=T.secret(spec.scalar),rumors={business:doc(p.oracles.business.path),chat:doc(p.oracles.chat.path)};
  need(T.getPublicKey(from)===A&&T.getPublicKey(local)===spec.account,'PUBLIC_ROLE_IDENTITIES');
  for(const r of Object.values(rumors))need(exactInnerShape(r)&&r.id===T.getEventHash(r),'FROZEN_INPUT_RUMOR_ID');
  check();const initial=T.wrap(rumors.business,from,spec.account);
  const events=p.ordinaryRole==='incoming'?[initial,T.wrap(rumors.chat,from,B)]:[initial,initial,T.wrap(rumors.business,from,A)];
  const expected={};for(let i=0;i<spec.stages.length;i++){const s=stageSpec(p.ordinaryRole,i);expected[s.id]={stage:s,rumor:putJSON(s.id+'-expected-rumor.json',rumors[s.oracle]),content:put(DIR+'/'+s.id+'-expected-content.txt',rumors[s.oracle].content)};}
  const preparedPin=putJSON('prepared.json',{schema:'e02-minimum-prepared-v1',profileId:PROFILE,windowId:spec.windowId,role:p.ordinaryRole,rumors,events,expected});
  prepared();check();const now=Math.floor(Date.now()/1000),inboxes=[T.secret(1),T.secret(2)].map(sk=>T.finalizeEvent({kind:10050,created_at:now,tags:[['relay',p.proxyUrl]],content:''},sk));
  const r=await exchange(inboxes,null,'prepare-inboxes');check();const inboxPin=putJSON('inboxes.json',{events:inboxes,...r});
  return {profileId:PROFILE,windowId:spec.windowId,ordinaryRole:p.ordinaryRole,expected,prepared:preparedPin,inboxes:inboxPin};
 }
""" + text[b:]
text = text.replace('function validateActual(frame,queried){', 'function validateActual(frame,queried,stage,origin){')
text = text.replace("secret:'2'.padStart(64,'0'),role:'incoming'", "secret:String(spec.scalar).padStart(64,'0'),role:spec.validationRole")
text = text.replace("T.validate(wire,T.secret(2),{role:'incoming',expectedSender:A})", "T.validate(wire,T.secret(spec.scalar),{role:spec.validationRole,expectedSender:A})")
text = text.replace("same(js.value.rumor,prepared().rumor)&&js.value.dispatch===true&&js.value.role==='incoming'", "same(js.value.rumor,prepared().rumors[stage.oracle])&&js.value.dispatch===stage.dispatch&&js.value.role===stage.normalizedRole")
# Every stage receives exclusive proof artifacts; no previous stage may overwrite/donate them.
for filename in ('frame.json','wire.json','js-request.json','rust-request.json','js-result.json','rust-result.json','Rust-stdin.jsonl','Rust-stdout.jsonl','Rust-stderr.bin','consumer-transport.json','validation.json'):
    text = text.replace("'" + filename + "'", "stage.id+'-" + filename + "'")
text = text.replace("DIR+'/'+stage.id+", "DIR+'/'+stage.id+")
# put(DIR+'/name',...) paths are complete string operands in the original source.
for filename in ('frame.json','wire.json','Rust-stdin.jsonl','Rust-stdout.jsonl','Rust-stderr.bin'):
    text = text.replace("DIR+'/" + filename + "'", "DIR+'/'+stage.id+'-" + filename + "'")
text = text.replace('ACTUAL_APP_RELAY_EVENT_JOIN','ACTUAL_VALIDATED_FRAME_QUERY_JOIN')
text = text.replace('INDEPENDENT_ACTUAL_RECEIVED_VALIDATION','INDEPENDENT_VALIDATED_FRAME_ROLE_RESULT')
text = text.replace("schema:'e02-app-proxy-row-v1'", "schema:'e02-minimum-proxy-row-v1'")
text = text.replace("schema:'e02-received-validation-record-v1'", "schema:'e02-minimum-validated-wire-record-v1'")
text = text.replace("schema:'e02-ordinary-transport-v1'", "schema:'e02-minimum-transport-v1'")
text = text.replace("caseId:CASE,transport,rustBinary", "profileId:PROFILE,windowId:spec.windowId,stageId:stage.id,origin,clientReceiptEstablished:origin==='ACTUAL_APP_SOCKET_FRAME',transport,rustBinary")
a = text.index(' async function publish(){'); b = text.index(' const control=', a)
text = text[:a] + """ async function publish(){
  check();need(stageIndex<spec.stages.length&&!publicationInvalidated,'FINITE_ROLE_STAGE_OR_STICKY_FAILURE');
  const d=prepared(),stage=selectedStage(),event=d.events[stageIndex],initial=d.events[0],before=gate();
  need(before!==null&&replayBinding(stage,event,initial),'CURRENT_STAGE_BINDINGS_REQUIRED');
  publicationGate=before;delivery=null;attempted=true;activeAttempt={epoch:++attemptEpoch,stageId:stage.id};
  publicationWindowOpen=true;attemptSawFrame=false;const windowStarted=process.hrtime.bigint();
  const intentRow=log({direction:'PUBLICATION_INTENT',stageId:stage.id,eventId:event.id,attempt:activeAttempt});
  const intent=putJSON(stage.id+'-publish-intent.json',{schema:'e02-minimum-publish-intent-v1',profileId:PROFILE,windowId:spec.windowId,stage,attempt:activeAttempt,intentSequence:intentRow.sequence,prepared:pin(DIR+'/prepared.json'),gate:before,issuedUTC:new Date().toISOString()});
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
  const publicationWindow=putJSON(stage.id+'-publication-window.json',{schema:'e02-minimum-publication-window-v1',
   profileId:PROFILE,windowId:spec.windowId,stageId:stage.id,eventId:event.id,attempt:activeAttempt,
   intentSequence:intentRow.sequence,closeSequence:closedRow.sequence,actualNewAppFrameObserved:observed,
   candidateAppFrameSeen:attemptSawFrame,elapsedNanoseconds,clock:'NODE_PROCESS_HRTIME_MONOTONIC',
   origin:observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME'});
  const query=await exchange(null,{ids:[event.id],limit:1},stage.id+'-query');check();need(query.received.length===1&&same(query.received[0].frame[2],event),'EXACT_PUBLISHED_EVENT_QUERY');
  const validation=validateActual(observed?delivery.frame:Buffer.from(query.received[0].rawBase64,'base64'),query.received[0].frame[2],stage,observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME');
  const produced=JSON.stringify(event),producerResult=T.validate(produced,T.secret(spec.scalar),{role:spec.validationRole,expectedSender:A});
  need(producerResult.ok===true&&same(producerResult.value.rumor,d.rumors[stage.oracle])&&producerResult.value.dispatch===stage.dispatch&&producerResult.value.role===stage.normalizedRole,'DECLARED_ROLE_DISPATCH_ELIGIBILITY');
  const producerValidation=putJSON(stage.id+'-producer-validation.json',{schema:'e02-minimum-producer-validation-v1',stageId:stage.id,actualPublishedEvent:event,result:producerResult,meaning:'Producer validation only; not a business effect or substitute for actual app wire/export.'});
  check();need(!publicationInvalidated&&publicationGenerationMatches(connections,before,event,spec.account),'CURRENT_GENERATION_BEFORE_STAGE_RECORD');
  const record=putJSON(stage.id+'-publication.json',{schema:'e02-minimum-stage-publication-v1',profileId:PROFILE,windowId:spec.windowId,stage,attempt:activeAttempt,intent,publicationWindow,gate:before,publication,query,event,
   actualNewAppFrameObserved:observed,delivery:observed?{connection:delivery.connection,subscription:delivery.subscription,rowSequence:delivery.rowSequence,sentSequence:delivery.sentSequence,forwardGeneration:delivery.forwardGeneration,completionGeneration:delivery.completionGeneration,forwardAttempt:delivery.forwardAttempt,completionAttempt:delivery.completionAttempt}:null,
   validation,producerValidation,clientRetention:'UNVERIFIED_REQUIRES_FRESH_CLIENT_SELECTION_EXPORT',validationOrigin:observed?'ACTUAL_APP_SOCKET_FRAME':'ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME',
   replayLimit:stage.identicalReplay&&!observed?'No new frame observed in bounded interval; retain honest publication/query/history and require post-replay real client export. No synthesized EVENT or earlier-frame donation.':null});
  stageIndex++;attempted=false;activeAttempt=null;
  return {profileId:PROFILE,windowId:spec.windowId,stage,publication:record,publicationWindow,validation,producerValidation,actualNewAppFrameObserved:observed};
 }
""" + text[b:]
text = text.replace("else result={caseId:CASE,ready:gate()!==null,gate:gate(),captureSequence:sequence,scope:'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT'};",
    "else result={profileId:PROFILE,windowId:spec.windowId,stageId:stageIndex<spec.stages.length?selectedStage().id:null,stageIndex,complete:stageIndex===spec.stages.length,ready:gate()!==null,gate:gate(),captureSequence:sequence,scope:'SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT'};")
text = text.replace("schema:'e02-fixture-command-v1',operation:q.op,caseId:CASE,ok:true,result", "schema:'e02-minimum-fixture-command-v1',profileId:PROFILE,windowId:spec.windowId,operation:q.op,caseId:CASE,ok:true,result")
OUT.write_text(text)
print('Prepared minimum fixture SOURCE only; no JS module parsed/evaluated or crypto/network executed.')
