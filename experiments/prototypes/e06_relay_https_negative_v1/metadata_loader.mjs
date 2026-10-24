// SOURCE ONLY / NOT EXECUTED. Fixed LAB-N-02-03-16 one-request JS window.
// Expected replies and checker oracles are never read here. No transport capability
// can be minted by this evidence-only child. Native dependencies load after guards.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
import path from 'node:path';
import {parseStrict,typedEqual,validateShape,verifyClosure,readBinding,selectedCell,checkDescriptor,absoluteFile,privateDir,fixedData,readBounded} from './wire.mjs';
const ROOT='/home/peterhorvath/apps/bitcoin/NBDP';
const HERE=ROOT+'/experiments/prototypes/e06_relay_https_negative_v1';
const ENTRY=ROOT+'/experiments/prototypes/e06_invoice_file_v1/js/metadata.mjs';
const ENTRY_PIN={bytes:16205,sha256:'c9f0cd7055a98e2edcfcc32efc9be99e499077dc6d131472cb4c179b8c4c348c'};
const need=(ok,reason)=>{if(!ok)throw Error(reason);};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const secret='0'.repeat(63)+'2'; // Existing isolated synthetic recipient, never external keys.
const descriptor=file=>{const raw=readBounded(file);return {path:file,bytes:raw.length,sha256:hash(raw)};};
function ownedJSON(d,definitions,shape) {
  checkDescriptor(d);need(d.bytes<=1048576,'BOUNDED_AUTHORITY_DOCUMENT');
  const st=fs.statSync(d.path);need(st.uid===process.getuid()&&(st.mode&0o777)===0o600,'OWNED_AUTHORITY_0600');
  const value=parseStrict(readBounded(d.path),1048576).value;
  if(shape)validateShape(value,'@'+shape,definitions);return value;
}

// Actual received spans are structurally compared, never replaced or reserialized.
export function validateInput(line,binding,selection,definitions,index,local=false) {
  need(index===0,'EXTRA_REQUEST');need(Buffer.isBuffer(line)&&line.length<=131072,'REQUEST_BOUND');
  const req=parseStrict(line,131072).value;validateShape(req,'@nativeRequest',definitions);
  const cell=local?null:selectedCell(selection,binding.cellId);
  need(local||cell.subprofileId!=='N03','N03_NATIVE_FORBIDDEN');
  const fOnly=local||cell.subprofileId==='N02';
  need(req.secretHex===secret&&typedEqual(req.config,binding.scope)&&typedEqual(req.config,selection.fixtureFamily.scope),'FIXED_SCOPE_SECRET');
  need(fOnly?req.dWireHex===null:typeof req.dWireHex==='string','EXACT_NULLABLE_D_BRANCH');
  for(const slot of fOnly?['F']:['D','F']) {
    const desc=slot==='D'?binding.dFixture:binding.fFixture;
    const fixtureDescriptor=local?selection.fixtureFamily.incomingWires[slot]:cell.jobs.find(j=>j.slot===slot)?.wire;
    need(fixtureDescriptor&&typedEqual(desc,fixtureDescriptor),'FIXED_FIXTURE');
    checkDescriptor(desc);const fixture=parseStrict(readBounded(desc.path)).value;
    const wire=req[slot.toLowerCase()+'WireHex'];need(typeof wire==='string'&&/^(?:[0-9a-f]{2})+$/.test(wire),'WIRE_HEX');
    const received=parseStrict(Buffer.from(wire,'hex')).value;need(typedEqual(received,fixture),'WHOLE_EVENT');
  }
  if(local)need(typedEqual(Buffer.concat([line,Buffer.from('\n')]),readBounded(checkDescriptor(binding.request).path)),'EXACT_LOCAL_REQUEST_BYTES');
  return req;
}
function targetContext(bindingPath,sha) {
  const {binding:b,selection,definitions,nativeShapes}=readBinding(bindingPath,sha,'nativeBinding');
  const cell=selectedCell(selection,b.cellId);
  need(cell.subprofileId!=='N03'&&cell.metadataBackend==='JS'&&b.backend==='JS'&&b.windowId===cell.windowId&&b.maxRequests===1,'N_JS_WINDOW');
  need(typedEqual(b.scope,selection.fixtureFamily.scope),'BOUND_SCOPE');
  need(b.metadataEntry.path===ENTRY&&b.metadataEntry.bytes===ENTRY_PIN.bytes&&b.metadataEntry.sha256===ENTRY_PIN.sha256,'FIXED_METADATA_ENTRY');
  need(typedEqual(b.fFixture,cell.jobs.find(j=>j.slot==='F').wire),'FIXED_RAW_F');
  need(cell.subprofileId==='N02'?b.dFixture===null:typedEqual(b.dFixture,cell.jobs.find(j=>j.slot==='D').wire),'FIXED_RAW_D_BRANCH');
  const verify=()=>{
    need(hash(readBounded(bindingPath))===sha,'BINDING_CHANGED');
    const fixtures=[b.fFixture,...(b.dFixture===null?[]:[b.dFixture])];
    const map=verifyClosure(b.closure,[fileURLToPath(import.meta.url),HERE+'/wire.mjs',ENTRY,...fixtures.map(d=>d.path)]);
    need(typedEqual(map.get(ENTRY),b.metadataEntry)&&fixtures.every(d=>typedEqual(map.get(d.path),d)),'NATIVE_CLOSURE_JOIN');
  };
  return {binding:b,selection,definitions,verify,local:false,replyShape:nativeShapes[b.cellId]};
}

// LOCAL_JS_CONTEXT_IMPLEMENTATION follows the separately closed worker-only schema.
// This is a distinct source-first local qualification mode, never a target bypass.
function localContext(bindingPath,sha) {
  const {selection,nativeShapes}=fixedData(),schemaPath=HERE+'/qualification-schemas.json';absoluteFile(schemaPath);
  need(fs.statSync(schemaPath).size<=1048576,'LOCAL_SCHEMA_BOUND');
  const schemas=parseStrict(readBounded(schemaPath),1048576).value,definitions=schemas.workerDefinitions;
  need(schemas.workerEntrySchemas?.localJSBinding==='@localJSBinding'&&schemas.workerEntrySchemas?.qualificationWorkerConfig==='@qualificationWorkerConfig','WORKER_SCHEMA_NAMESPACE');
  const b=parseStrict(readBounded(bindingPath),1048576).value;validateShape(b,'@localJSBinding',definitions);
  const wc=ownedJSON(b.workerConfig,definitions,'qualificationWorkerConfig');
  const release=ownedJSON(b.release,definitions,'localRelease');
  need(typedEqual(b.closure,wc.sourceClosure)&&typedEqual(b.sourceApproval,wc.sourceApproval),'LOCAL_SAME_SOURCE');
  need(typedEqual(b.scope,wc.scope)&&typedEqual(b.scope,selection.fixtureFamily.scope),'LOCAL_FIXED_SCOPE');
  need(typedEqual(b.fFixture,wc.fFixture)&&typedEqual(b.fFixture,selection.fixtureFamily.incomingWires.F),'LOCAL_FIXED_F');
  need(typedEqual(b.request,wc.request)&&typedEqual(b.metadataEntry,wc.tools.jsMetadata),'LOCAL_REQUEST_TOOL_JOIN');
  need(b.metadataEntry.path===ENTRY&&b.metadataEntry.bytes===ENTRY_PIN.bytes&&b.metadataEntry.sha256===ENTRY_PIN.sha256,'LOCAL_FIXED_METADATA_ENTRY');
  need(typedEqual(wc.tools,schemas.fixedTools),'LOCAL_FIXED_TOOLS');
  need(b.maxRequests===1&&wc.jobs[0].jobId==='Q-JS'&&wc.jobs[0].backend==='JS'&&b.output===wc.jobs[0].output,'LOCAL_EXACT_JOB');
  need(path.dirname(bindingPath)===b.output&&b.output===path.join(wc.outputRoot,'Q-JS'),'LOCAL_OWNED_JOB_OUTPUT');
  need(release.executionSession===wc.executionSession&&release.runRole===wc.runRole
    &&typedEqual(release.config,b.config)&&typedEqual(release.workerConfig,b.workerConfig)
    &&typedEqual(release.sourceApproval,b.sourceApproval)&&typedEqual(release.controlAcceptance,wc.controlAcceptance)
    &&typedEqual(release.configurationAcceptance,b.configurationAcceptance),'LOCAL_EXTERNAL_RELEASE_JOIN');
  // Full checker configuration remains opaque; the fixed admitted parent enforces its
  // independent configuration reviews. This worker binds its exact bytes to root release.
  checkDescriptor(b.config);checkDescriptor(b.configurationAcceptance);
  need(typedEqual(wc.acceptedInertFreeze,schemas.acceptedInertFreeze)&&typedEqual(wc.acceptedPlan,schemas.acceptedQualificationPlan)
    &&typedEqual(wc.inputInventory,schemas.qualificationInputInventory)&&typedEqual(wc.sourcePrerequisites,schemas.fixedSourcePrerequisites),'LOCAL_FIXED_PREREQUISITES');
  need(wc.workerSchema.path===HERE+'/worker-schemas.json'&&typedEqual(wc.qualificationSchema,descriptor(schemaPath)),'LOCAL_WORKER_SCHEMA_JOIN');
  const source=ownedJSON(b.sourceApproval,definitions,'sourceApproval');
  need(['/root','/root/negative_outer_implementer','/root/negative_io_implementer','/root/recovery_fixture_parent','/root/negative_lane_architect'].every(author=>source.authors.includes(author)),'EXACT_DERIVATIVE_AUTHORS');
  need(typedEqual(source.sourceClosure,b.closure),'LOCAL_SOURCE_APPROVAL_CLOSURE');
  const controls=ownedJSON(wc.controlAcceptance,definitions,'controlApproval');
  need(typedEqual(controls.sourceApproval,b.sourceApproval),'LOCAL_CONTROL_SOURCE_JOIN');
  const controlEvidence=ownedJSON(controls.actualControlEvidence,definitions,'controlEvidence');
  need(typedEqual(controlEvidence.sourceClosure,b.closure)&&typedEqual(controlEvidence.sourceApproval,b.sourceApproval),'LOCAL_ACTUAL_CONTROL_JOIN');
  function reviews(pack,decision,expected) {
    need(pack.reviews.length===2&&new Set(pack.reviews.map(r=>r.role)).size===2
      &&new Set(pack.reviews.map(r=>r.session)).size===2,'DISTINCT_INDEPENDENT_REVIEWS');
    for(const review of pack.reviews) {
      need(review.decision===decision&&!pack.authors.includes(review.session)&&!source.authors.includes(review.session),'NONAUTHOR_REVIEW_DECISION');
      const subject=ownedJSON(review.subject,definitions,null);need(typedEqual(subject,expected),'COMPLETE_REVIEW_SUBJECT');
    }
  }
  reviews(source,'ACCEPT_SOURCE_ONLY',b.closure);reviews(controls,'ACCEPT_CONTROLS_ONLY',controlEvidence);
  const inventory=parseStrict(readBounded(checkDescriptor(wc.inputInventory).path),1048576).value;
  need(Object.keys(inventory).length===57,'FIXED_LOCAL_INPUT_INVENTORY');
  const evidence=[b.workerConfig,b.config,b.release,b.sourceApproval,b.configurationAcceptance,wc.controlAcceptance,
    controls.actualControlEvidence,wc.request,wc.fFixture,wc.workerSchema,wc.qualificationSchema,
    wc.acceptedInertFreeze,wc.acceptedPlan,wc.inputInventory,...Object.values(wc.sourcePrerequisites),
    ...Object.values(inventory),...source.reviews.map(r=>r.subject),...controls.reviews.map(r=>r.subject)];
  const original=new Map();for(const d of evidence){checkDescriptor(d);const previous=original.get(d.path);need(!previous||typedEqual(previous,d),'CONFLICTING_ORIGINAL_EVIDENCE_PIN');original.set(d.path,d);}
  const verify=()=>{
    need(hash(readBounded(bindingPath))===sha,'LOCAL_BINDING_CHANGED');privateDir(b.output);
    const map=verifyClosure(b.closure,[fileURLToPath(import.meta.url),HERE+'/wire.mjs',schemaPath,ENTRY,b.fFixture.path]);
    need(typedEqual(map.get(ENTRY),b.metadataEntry)&&typedEqual(map.get(b.fFixture.path),b.fFixture)
      &&typedEqual(map.get(wc.workerSchema.path),wc.workerSchema)&&typedEqual(map.get(schemaPath),wc.qualificationSchema),'LOCAL_COMPLETE_SOURCE_TOOL_JOIN');
    for(const d of original.values())checkDescriptor(d);
  };
  verify();return {binding:b,selection,definitions,verify,local:true,replyShape:nativeShapes['N02-SF-JS']};
}
async function main() {
  need(process.argv.length===4,'CLI node metadata_loader.mjs ABS_BINDING SHA');
  const [bindingPath,sha]=process.argv.slice(2);absoluteFile(bindingPath);privateDir(path.dirname(bindingPath));
  const initial=fs.statSync(bindingPath);need(initial.uid===process.getuid()&&(initial.mode&0o777)===0o600&&initial.size<=1048576&&/^[a-f0-9]{64}$/.test(sha),'OWNED_BOUNDED_BINDING');
  const raw=readBounded(bindingPath);need(hash(raw)===sha,'EXTERNAL_BINDING_HASH');
  const header=parseStrict(raw,1048576).value;
  const ctx=header.schema==='n02316-local-js-binding-v1'?localContext(bindingPath,sha):targetContext(bindingPath,sha);
  const {binding:b,selection,definitions,verify,local,replyShape}=ctx;
  need(typeof replyShape==='string'&&replyShape.startsWith('@'),'SELECTED_WHOLE_NATIVE_SHAPE');
  verify();const metadata=await import(pathToFileURL(ENTRY).href);verify();
  need(typeof metadata._handleLine==='function','METADATA_EXPORT');
  let pending=Buffer.alloc(0),count=0,total=0;
  for await(const chunk of process.stdin) {
    total+=chunk.length;need(total<=131072,'TOTAL_STDIN_BOUND');pending=Buffer.concat([pending,chunk]);
    let lf;
    while((lf=pending.indexOf(10))!==-1) {
      const line=pending.subarray(0,lf);pending=pending.subarray(lf+1);
      validateInput(line,b,selection,definitions,count,local);verify();
      const reply=await metadata._handleLine(new TextDecoder('utf-8',{fatal:true}).decode(line));
      // Preserve ACTUAL complete native JSONL before shape or post-integrity refusal.
      const serialized=JSON.stringify(reply);need(typeof serialized==='string','NATIVE_REPLY_JSON');
      const replyBytes=Buffer.from(serialized+'\n');need(replyBytes.length<=16777216,'NATIVE_REPLY_BOUND');
      const replyPath=path.join(path.dirname(bindingPath),'native-reply.jsonl');
      const replyFd=fs.openSync(replyPath,'wx',0o600);
      try {fs.writeFileSync(replyFd,replyBytes);fs.fsyncSync(replyFd);}finally {fs.closeSync(replyFd);}
      const dirFd=fs.openSync(path.dirname(bindingPath),fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);
      try {fs.fsyncSync(dirFd);}finally {fs.closeSync(dirFd);}
      count++;
      validateShape(reply,replyShape,definitions);verify();
      let offset=0;while(offset<replyBytes.length){const wrote=fs.writeSync(1,replyBytes,offset,replyBytes.length-offset);need(wrote>0,'NATIVE_REPLY_COMPLETE_WRITE');offset+=wrote;}
    }
    need(pending.length<=131072,'LINE_BOUND');
    // Deliberately persistent/quiescent until the owner closes stdin after sole reply.
  }
  need(pending.length===0&&count===1,'EOF_REQUEST_COUNT');verify();
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  main().catch(error=>{process.stderr.write((error.name+': '+error.message).slice(0,16000)+'\n');process.exitCode=1;});
}
