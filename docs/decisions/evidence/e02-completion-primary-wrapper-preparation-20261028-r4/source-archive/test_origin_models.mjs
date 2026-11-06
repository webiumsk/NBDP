// SOURCE-only PURE definitions against the actual staged adapter. ZERO executions.
// DATA I/O primitives use an in-memory descriptor map; no fixture files/processes.
import assert from 'node:assert/strict';
import {wrapperPrimaryTool} from './wrapper-origin.mjs';
const BASE='/Data/nbdp-e02-tooling-20261027/completion-primary-wrapper-preparation-r4';
const RUNS='/Data/nbdp-e02-tooling-20261027/ordinary-completion-r3/runs/';
const EXP='/home/peterhorvath/apps/bitcoin/NBDP/experiments';
const AUTH='FIXED_SAME_T0_ENV_CONFIG_AND_PRIMARY_RELEASE_ONLY';
const d=(p,bytes=1)=>({path:p,bytes,sha256:'a'.repeat(64)});
function fixture(){
 const docs=new Map(),raw=new Map(),run='b'.repeat(32),attempt=BASE+'/attempt-'+run,out=RUNS+run+'/primary';
 const put=(p,v)=>{const pin=d(p);docs.set(p,v);return pin;};const putRaw=(p,v)=>{const b=Buffer.from(typeof v==='string'?v:JSON.stringify(v));raw.set(p,b);return d(p,b.length);};
 const source=d('/SYNTHETIC/wrapper-source.json'),completionSource=d('/SYNTHETIC/completion-source.json'),runner='/Data/nbdp-e02-tooling-20261027/ordinary-completion-preparation-r3/runner.mjs';
 const p={wrapperSource:source,node:d('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'),python:d('/usr/bin/python3.12'),timeout:d('/usr/bin/timeout'),rustBinary:d('/SYNTHETIC/native'),e01:d('/SYNTHETIC/E01.json'),integrationSources:[d(runner)]};
 const configPin=d(attempt+'/config.json'),phasePin=d(attempt+'/primary-release.json'),envPin=d(attempt+'/environment.json'),subject=d(out+'/primary-subject.json'),planPin=d(BASE+'/plan-draft.json'),inventory=d('/SYNTHETIC/inventory.json');
 const config={runId:run,operator:'/root/OPERATOR',createdAtUtcMillis:1000,outputRoot:RUNS+run,environment:envPin};
 const phase={schema:'e02-completion-root-release-v2',phase:'primary',config:configPin,sourceSubject:completionSource,issuedAtUtcMillis:1200,notAfterUtcMillis:244200,input:null,reviewOrigin:null,primaryTool:null};
 const rawReport=d(out+'/raw-primary-report.json'),wire=d(out+'/E02-bidirectional-wires.json');const argv=[p.node.path,runner,'primary',configPin.path,configPin.sha256,phasePin.path,phasePin.sha256,'NONE','NONE',out];
 const primary={config:configPin,release:phasePin,operator:config.operator,sourceSubject:completionSource,environment:envPin,startedAtUtcMillis:1300,finishedAtUtcMillis:2300,argv,rawReport,saved:[wire]};
 const t={schema:'e02-completion-primary-wrapper-origin-v2',subject,operator:primary.operator,argv,wrapperSource:source,wrapperPlan:planPin,config:configPin,primaryRelease:phasePin,environment:envPin};
 const keys={outerRequest:BASE+'/outer-request.json',outerChild:BASE+'/outer-child.json',outerResult:BASE+'/outer-result.json',rootRelease:BASE+'/root-release.json',innerRequest:attempt+'/primary-request.json',innerCompletion:attempt+'/primary-completion.json',configIntent:attempt+'/config-intent.json',inputBefore:attempt+'/source-before.json',inputAfter:attempt+'/source-after.json',result:attempt+'/result.json'};for(const [k,path] of Object.entries(keys))t[k]=d(path);
 docs.set(source.path,{sources:[d(BASE+'/launch.py'),d(BASE+'/dispatch.py'),d(BASE+'/render_data.py')]});docs.set(planPin.path,{runtimeReady:true,current:{wrapperSource:source,completionSource,completionRunner:d(runner),inputInventory:inventory}});docs.set(configPin.path,config);docs.set(phasePin.path,phase);docs.set(t.configIntent.path,{...config,environment:null});
 const cid1='c'.repeat(64),cid2='d'.repeat(64),nid='e'.repeat(64);const inspect1=put('/SYNTHETIC/strfry-inspect.json',[{Id:cid1,HostConfig:{NetworkMode:nid}}]),inspect2=put('/SYNTHETIC/rs-inspect.json',[{Id:cid2,HostConfig:{NetworkMode:nid}}]);docs.set(envPin.path,{observedAtUtcMillis:1100,relays:[{inspection:inspect1},{inspection:inspect2}]});
 const concrete=put('/SYNTHETIC/concrete.json',{plan:planPin,inventory,sourceSubject:source}),accepted=put('/SYNTHETIC/concrete-acceptance.json',{subject:concrete});
 docs.set(t.rootRelease.path,{schema:'nbdp-completion-primary-wrapper-root-release-v3',actor:'/root',scope:'ONE_CURRENT_COMPLETION_PRIMARY_ONLY',executionAuthorized:true,renderAuthority:AUTH,plan:planPin,sourceSubject:source,runId:run,issuedAtUtcNs:1000000000,notAfterUtcNs:601000000000,sourceQa:d('/SYNTHETIC/qa'),sourceSecurity:d('/SYNTHETIC/sec'),modelAcceptance:d('/SYNTHETIC/models'),inputAcceptance:accepted});
 docs.set(t.outerRequest.path,{schema:'e02-wrapper-dispatch-request-v2',argv:[p.timeout.path,'--signal=TERM','--kill-after=3s','597s',p.python.path,'-I','-B',BASE+'/launch.py','--plan-sha',planPin.sha256,'--release',t.rootRelease.path,'--release-sha',t.rootRelease.sha256],cwd:BASE,environment:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8',TZ:'UTC'},release:t.rootRelease,startedUtcNs:1000000000,retryAuthorized:false});
 docs.set(t.outerChild.path,{pid:123,ownedPopenHandle:true});docs.set(t.outerResult.path,{schema:'e02-wrapper-dispatch-result-v2',exitCode:0,reaped:true,durationSeconds:30,stdout:putRaw(BASE+'/outer.stdout',{result:t.result,exitCode:0}),stderr:putRaw(BASE+'/outer.stderr',''),captureTransport:'REGULAR_FILES',pipeEofEstablished:false,cleanupMustBeReviewed:true,retryAuthorized:false,attemptPath:attempt});
 const apiArguments={cmd:p.python.path+' -I -B '+BASE+'/dispatch.py',workdir:BASE};const terminal={exit_code:0,output:JSON.stringify({exitCode:0,attemptPath:attempt,durationSeconds:30})};t.outerApi=put('/SYNTHETIC/actual-api.json',{schema:'e02-wrapper-actual-outer-api-v1',arguments:apiArguments,records:[{toolName:'tools.exec_command',actualArguments:apiArguments,unmodifiedResponse:terminal}]});
 docs.set(t.innerRequest.path,{schema:'e02-wrapper-inner-process-request-v1',argv:[p.timeout.path,'--signal=TERM','--kill-after=3s','240s',...argv],cwd:EXP,environment:{PATH:'/usr/bin:/bin',HOME:attempt+'/fixture/home',TMPDIR:attempt+'/fixture/tmp',LANG:'C.UTF-8',LC_ALL:'C.UTF-8',TZ:'UTC',NBDP_CHROME:'/usr/bin/false',NBDP_RUST_BIN:p.rustBinary.path},startedUtcNs:1300000000,jobSeconds:240,killGraceSeconds:3,config:configPin,release:phasePin});
 docs.set(t.innerCompletion.path,{schema:'e02-wrapper-inner-process-completion-v2',exitCode:0,stdout:putRaw(attempt+'/primary.stdout',{subject,rawStatus:'PARTIAL',unexpected:null}),stderr:putRaw(attempt+'/primary.stderr',''),finishedUtcNs:2300000000,finishedUtcNsExact:'2300000000',captureTransport:'REGULAR_FILES',pipeEofEstablished:false,innerApiAttestation:false,primarySubject:subject});
 docs.set(t.inputBefore.path,{inventory,rows:[]});docs.set(t.inputAfter.path,{inventory,rows:[],selectedProtectedInputsUnchanged:true,sharedRuntimeUnchanged:true,native:p.rustBinary,e01:p.e01});docs.set(t.result.path,{state:'RAW_PRIMARY22_PARTIAL_PENDING_INDEPENDENT_DATA_REVIEW',firstFault:null,secondary:[],ordinaryRowsQualified:0,canonicalE02Changed:false,stockE04E06Unlocked:false,methodFinishedUtcNs:2400000000});
 t.cleanup={relays:[put(attempt+'/cleanup-strfry.json',{cid:cid1,exactAbsence:true}),put(attempt+'/cleanup-rs-relay.json',{cid:cid2,exactAbsence:true})],network:put(attempt+'/cleanup-network.json',{networkId:nid,exactAbsence:true}),proxy:put(attempt+'/proxy-completion.json',{returnCode:0,reaped:true,ownedPopenHandleOnly:true,terminationRequested:true,killRequested:false,stdout:putRaw(attempt+'/proxy.stdout','SYNTHETIC actual proxy readiness'),stderr:putRaw(attempt+'/proxy.stderr','')})};t.transcript=putRaw('/SYNTHETIC/transcript','SYNTHETIC outer API transcript');
 const descriptor=put('/SYNTHETIC/origin.json',t);docs.set(rawReport.path,{status:'PARTIAL'});docs.set(wire.path,[]);
 const api={need:(v,m)=>assert.ok(v,m),closed:(v,keys)=>{assert.ok(v&&typeof v==='object'&&!Array.isArray(v));assert.deepEqual(Object.keys(v).sort(),keys.split(' ').sort());return v;},eq:assert.deepEqual,pin:path=>d(path),checked:pin=>raw.get(pin.path)??Buffer.from('SYNTHETIC'),doc:pin=>{assert.ok(docs.has(pin.path),'known synthetic descriptor '+pin.path);return docs.get(pin.path);},json:b=>JSON.parse(b),EXP,primaryShape:v=>v,wireFixtures:v=>v};
 return {docs,raw,t,p,primary,subject,descriptor,api,run:()=>wrapperPrimaryTool(descriptor,subject,primary,p,api)};
}
const model=(name,body)=>({name,body});
export const MODELS=[
 model('actual_adapter_direct_within_phase_positive',()=>fixture().run()),
 model('actual_adapter_yielded_same_session_positive',()=>{const f=fixture(),a=f.docs.get(f.t.outerApi.path),terminal=a.records[0].unmodifiedResponse;a.records=[{...a.records[0],unmodifiedResponse:{session_id:17}},{toolName:'tools.write_stdin',actualArguments:{session_id:17,chars:''},unmodifiedResponse:terminal}];f.run();}),
 model('actual_adapter_command_substitution_rejected',()=>{const f=fixture();f.docs.get(f.t.innerRequest.path).argv[4]='/FOREIGN/node';assert.throws(f.run);}),
 model('actual_adapter_config_substitution_rejected',()=>{const f=fixture();f.docs.get(f.t.innerRequest.path).config=d('/FOREIGN/config');assert.throws(f.run);}),
 model('actual_adapter_release_substitution_rejected',()=>{const f=fixture();f.docs.get(f.t.innerRequest.path).release=d('/FOREIGN/release');assert.throws(f.run);}),
 model('actual_adapter_canonical_result_substitution_rejected',()=>{const f=fixture();f.primary.rawReport=d(EXP+'/results/E02.json');assert.throws(f.run);}),
 model('actual_adapter_fabricated_inner_api_rejected',()=>{const f=fixture();f.docs.get(f.t.innerCompletion.path).innerNodeApiReceipt=d('/FAKE/api');assert.throws(f.run);}),
 model('actual_adapter_pipe_eof_substitution_rejected',()=>{const f=fixture();f.docs.get(f.t.innerCompletion.path).pipeEofEstablished=true;assert.throws(f.run);}),
 model('actual_adapter_observed_exit0_one_ns_after_expiry_rejected',()=>{const f=fixture(),done=f.docs.get(f.t.innerCompletion.path),phase=f.docs.get(f.t.primaryRelease.path),late=BigInt(phase.notAfterUtcMillis)*1000000n+1n;done.finishedUtcNsExact=late.toString();done.finishedUtcNs=Number(late);assert.throws(f.run);}),
 model('actual_adapter_primary_subject_after_expiry_rejected',()=>{const f=fixture();f.primary.finishedAtUtcMillis=f.docs.get(f.t.primaryRelease.path).notAfterUtcMillis+1;assert.throws(f.run);}),
 model('actual_adapter_invalid_proxy_cleanup_rejected',()=>{const f=fixture();f.docs.get(f.t.cleanup.proxy.path).returnCode=-15;assert.throws(f.run);})
];
// A later explicitly authorized model runner must call each body and record real
// outcomes. This SOURCE module does not execute MODELS on import or on invocation.
