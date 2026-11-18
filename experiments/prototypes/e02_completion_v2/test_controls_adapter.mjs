// PREPARED NOT EXECUTED: fictional DATA shapes only, no runner/consumer imports.
import assert from 'node:assert/strict';
import {consumerBatchShape,controlToolShape,CONTROL_SCOPES} from './control-data.mjs';
const cases=[];
const check=(name,fn)=>{fn();cases.push(name);};
const clone=v=>structuredClone(v);
const fakePin=name=>({path:'/SYNTHETIC_NOT_ACTUAL/'+name,bytes:1,sha256:'0'.repeat(64)});

function model(){
 const sourceFiles=[...CONTROL_SCOPES.map(([name])=>fakePin(name)),...Array.from({length:10},(_,i)=>fakePin('source'+i))];
 const p={consumerSubject:fakePin('consumer-subject'),consumerSources:sourceFiles,python:fakePin('python'),
   consumerControlResult:fakePin('execution'),consumerControlPlan:fakePin('plan'),consumerControlCapture:fakePin('capture'),
   consumerControlAcceptance:fakePin('acceptance'),consumerControlRelease:fakePin('release'),
   consumerControlDefinitions:fakePin('definitions'),consumerControlToolReceipts:fakePin('tool-receipts')};
 const source={schema:'e02-ordinary-minimum-consumer4-source-subject-v1',profileId:'e02-ordinary-minimum-rs-two-role-v2',
   sources:sourceFiles,controlPlan:p.consumerControlDefinitions};
 const definitions={schema:'e02-consumer4-proposed-data-controls-v1',scopes:CONTROL_SCOPES.map(([name,count],i)=>({
   source:sourceFiles[i],count,exactDefinedNames:Array.from({length:count},(_,j)=>'Model'+i+'.test_'+String(j).padStart(3,'0'))}))};
 const commands=CONTROL_SCOPES.map(([name,count],i)=>({name,expectedCases:count,argv:[p.python.path,'-I','-B',sourceFiles[i].path]}));
 const plan={schema:'nbdp-consumer4-fixed-data-capture-v1',scope:'SYNTHETIC_DATA_ONLY',
   inputs:[p.consumerSubject,p.python,...sourceFiles,...Array.from({length:48},(_,i)=>fakePin('input'+i))],commands,
   limits:{commandSeconds:60,stdoutRetainedBytes:1048576,stderrRetainedBytes:262144},release:p.consumerControlRelease};
 const streams=definitions.scopes.map(scope=>({stdout:Buffer.alloc(0),stderr:Buffer.from([...scope.exactDefinedNames].sort().map(full=>{
   const name=full.split('.')[1];return name+' (__main__.'+full+') ... ok';
 }).join('\n')+'\n\n----------------------------------------------------------------------\nRan '+scope.count+' tests in 0.001s\n\nOK\n')}));
 const result={schema:'nbdp-consumer4-fixed-data-result-v1',plan:p.consumerControlPlan,
   commands:commands.map((row,i)=>({...row,startedUtcNs:1,exitCode:0,timeout:false,naturalExit:true,reaped:true,
     stdoutEOF:true,stderrEOF:true,stdoutCapturedBytes:0,stderrCapturedBytes:streams[i].stderr.length,
     stdout:{...fakePin('stdout'+i),bytes:0},stderr:{...fakePin('stderr'+i),bytes:streams[i].stderr.length},
     truncated:false,elapsedWallNs:100})),failure:null,remainingScopesExecuted:false,scope:'SYNTHETIC_DATA_ONLY',
   ordinaryRows:0,e02:'PARTIAL22_UNCHANGED',retentionMeaning:'communicate() memory buffering; post-capture ceilings, not streaming memory bounds',
   resultAcceptance:'PENDING_INDEPENDENT_QA_SECURITY'};
 const acceptance={schema:'nbdp-consumer4-fixed-data-acceptance-v1',actor:'/root',subject:p.consumerControlResult,
   countsSeparate:[86,36,8,9],decision:'ACCEPT_CONSUMER4_ACTUAL_SYNTHETIC_DATA_ONLY',ordinaryRowsQualified:0,
   canonicalE02:'PARTIAL22_UNCHANGED',runtimeAuthorized:false,reviews:[fakePin('qa'),fakePin('security')]};
 const release={schema:'nbdp-consumer4-once-only-data-release-v1',actor:'/root',decision:'RELEASE_ONE_FIXED_CONSUMER4_DATA_BATCH',
   runner:p.consumerControlCapture,batch:Object.fromEntries(['schema','scope','inputs','commands','limits'].map(k=>[k,plan[k]])),ordinaryRows:0,runtimeAuthorized:false};
 const a={schema:'e02-completion-consumer-controls-adapter-v2',sourceSubject:p.consumerSubject,subject:p.consumerControlResult,
   authors:['/root/SYNTHETIC_AUTHOR'],operators:['/root/SYNTHETIC_OPERATOR'],plan:p.consumerControlPlan,capture:p.consumerControlCapture,
   acceptance:p.consumerControlAcceptance,release:p.consumerControlRelease,toolReceipts:p.consumerControlToolReceipts,reviewOrigin:fakePin('external-origin')};
 return {a,p,source,definitions,plan,result,acceptance,release,streams};
}
function inspect(m){return consumerBatchShape(m.a,m.p,m.source,m.definitions,m.plan,m.result,m.acceptance,m.release,m.streams);}
check('positive-four-separate-synthetic-control-scopes',()=>inspect(model()));
for(const [name,change] of [
 ['old-single86-adapter',m=>m.a.schema='e02-completion-consumer-controls-adapter-v1'],
 ['wrong-consumer-source',m=>m.a.sourceSubject={...m.a.sourceSubject,sha256:'1'.repeat(64)}],
 ['missing-current-source-file',m=>m.source.sources.pop()],
 ['only-old86-result',m=>m.result.commands.splice(1)],
 ['reordered-scopes',m=>m.result.commands.reverse()],
 ['changed-expected-count',m=>m.result.commands[1].expectedCases=35],
 ['nonzero-process',m=>m.result.commands[0].exitCode=2],
 ['timeout',m=>m.result.commands[0].timeout=true],
 ['forced-invented-field',m=>m.result.commands[0].forced=true],
 ['missing-reap',m=>m.result.commands[1].reaped=false],
 ['missing-stdout-eof',m=>m.result.commands[2].stdoutEOF=null],
 ['missing-stderr-eof',m=>m.result.commands[3].stderrEOF=false],
 ['truncation',m=>m.result.commands[0].truncated=true],
 ['stdout-not-empty',m=>m.streams[0].stdout=Buffer.from('SYNTHETIC_UNEXPECTED')],
 ['retained-count-mismatch',m=>m.result.commands[1].stderrCapturedBytes++],
 ['hidden-first-failure',m=>m.result.failure='SYNTHETIC_FIRST_FAILURE'],
 ['ordinary-row-donation',m=>m.result.ordinaryRows=1],
 ['runtime-authority-in-result-acceptance',m=>m.acceptance.runtimeAuthorized=true],
 ['rewritten-original-result-state',m=>m.result.resultAcceptance='ACCEPTED'],
 ['missing-one-review',m=>m.acceptance.reviews.pop()],
 ['wrong-scope-counts',m=>m.acceptance.countsSeparate=[139]],
 ['different-root-release-runner',m=>m.release.runner={...m.release.runner,sha256:'2'.repeat(64)}],
 ['root-release-batch-drift',m=>{m.release.batch=clone(m.release.batch);m.release.batch.limits.commandSeconds=120;}],
 ['one-missing-closure-input',m=>m.plan.inputs.pop()],
 ['duplicate-closure-path',m=>m.plan.inputs[0]=m.plan.inputs[1]],
 ['whole-consumer-source-omitted-from-closure',m=>m.plan.inputs[2]=fakePin('unexpected-source')],
 ['wrong-interpreter-argv',m=>{m.result.commands[0].argv=[...m.result.commands[0].argv];m.result.commands[0].argv[0]='/SYNTHETIC_OTHER_PYTHON';}],
 ['wrong-result-profile-reference',m=>m.result.plan={...m.result.plan,sha256:'3'.repeat(64)}],
 ['wrong-raw-membership',m=>{m.streams[0].stderr=Buffer.from(m.streams[0].stderr.toString().replaceAll('test_000','test_foreign'));m.result.commands[0].stderrCapturedBytes=m.result.commands[0].stderr.bytes=m.streams[0].stderr.length;}],
 ['raw-result-not-ok',m=>{m.streams[0].stderr=Buffer.from(m.streams[0].stderr.toString().replace(/OK\n$/,'FAILED\n'));m.result.commands[0].stderrCapturedBytes=m.result.commands[0].stderr.bytes=m.streams[0].stderr.length;}],
 ['actual-participant-omitted',m=>m.a.operators=[]],
 ['fake-streaming-memory-claim',m=>m.result.retentionMeaning='STREAMING_CAP'],
])check('refuse-'+name,()=>{const m=model();change(m);assert.throws(()=>inspect(m));});

function tool(m){return {origin:'Actual structured tool responses retained by coordinator; not child-generated command journals.',
 launch:{args:{cmd:m.p.python.path+' -I -B docs/decisions/evidence/e02-consumer4-data-run-r1/capture.py '+m.p.consumerControlPlan.sha256},
   result:{session_id:123}},polls:[{args:{session_id:123,chars:''},result:{session_id:123}},
   {args:{session_id:123,chars:''},result:{exit_code:0,output:JSON.stringify({execution:m.p.consumerControlResult,failure:null})}}]};}
check('positive-synthetic-original-api-envelope-shape-only',()=>{const m=model();controlToolShape(tool(m),m.p,m.result);});
for(const [name,change] of [
 ['changed-command',t=>t.launch.args.cmd+=' --bypass'],['wrong-tool-session',t=>t.polls[1].args.session_id++],
 ['injected-stdin',t=>t.polls[0].args.chars='SYNTHETIC_INPUT'],['failed-outer',t=>t.polls[1].result.exit_code=2],
 ['hidden-earlier-completion',t=>t.polls[0].result.exit_code=2],['missing-polls',t=>t.polls=[]],
 ['wrong-output-subject',t=>{const r=JSON.parse(t.polls[1].result.output);r.execution.sha256='f'.repeat(64);t.polls[1].result.output=JSON.stringify(r);}],
])check('refuse-tool-'+name,()=>{const m=model(),t=tool(m);change(t);assert.throws(()=>controlToolShape(t,m.p,m.result));});
console.log(JSON.stringify({scope:'E02_COMPLETION2_ADAPTER_SYNTHETIC_DATA_ONLY',checks:cases.length,cases,
  primaryExecuted:false,consumerExecuted:false,cryptoExecuted:false,actualToolOrReviewAuthenticated:false,completionPassClaimed:false}));
