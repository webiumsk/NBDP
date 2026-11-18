// DATA shape joins only. No runner, consumer, primary, process or service import.
import {need,closed,eq} from './data.mjs';

const CURRENT_CONTROL_ADAPTER_READY=false; // Exact actual schemas/inputs are pending.

export const CONTROL_SCOPES = [
  ['test_data_controls.py',86], ['test_observer.py',36],
  ['test_source_bindings.py',8], ['test_whole_window.py',9],
];

export function unittestShape(stderr, count, names){
  need(Buffer.isBuffer(stderr),'raw unittest stderr');
  const raw = new TextDecoder('utf-8',{fatal:true}).decode(stderr);
  const pattern = /^([a-z0-9_]+) \(__main__\.([A-Za-z][A-Za-z0-9_]*)\.([a-z0-9_]+)\) \.\.\. ok$/;
  const found = [];
  for(const line of raw.split('\n')){
    const match = line.match(pattern);
    if(match){eq(match[1],match[3]);found.push(match[2]+'.'+match[1]);}
  }
  eq(found,[...names].sort());eq(found.length,count);
  need(new RegExp('\\nRan '+count+' tests? in [^\\n]+\\n\\nOK\\n$').test(raw),'actual unittest count/OK');
  return found;
}

export function consumerBatchShape(adapter,p,source,definitions,plan,result,acceptance,release,streams){
  need(CURRENT_CONTROL_ADAPTER_READY===true,'COMPLETION3_CURRENT_CONTROL_ADAPTER_NULL_NOT_READY');
  const contract=p.consumerControlContract;need(contract!==null&&typeof contract==='object','ACTUAL_CURRENT_CONTROL_CONTRACT_REQUIRED');
  closed(adapter,'schema sourceSubject subject authors operators plan capture acceptance release toolReceipts reviewOrigin');
  eq(adapter.schema,'e02-completion-consumer-controls-adapter-v2');
  eq(adapter.sourceSubject,p.consumerSubject);eq(adapter.subject,p.consumerControlResult);
  for(const [key,profileKey] of [['plan','consumerControlPlan'],['capture','consumerControlCapture'],
    ['acceptance','consumerControlAcceptance'],['release','consumerControlRelease'],['toolReceipts','consumerControlToolReceipts']])eq(adapter[key],p[profileKey]);
  for(const key of ['authors','operators'])need(Array.isArray(adapter[key])&&adapter[key].length>0&&adapter[key].every(x=>typeof x==='string'&&x.startsWith('/root')),'actual control participants');
  eq(source.schema,contract.sourceSchema);
  eq(source.profileId,'e02-ordinary-minimum-rs-two-role-v2');
  need(Array.isArray(source.sources)&&source.sources.length===14,'complete current fourteen consumer source files');
  eq(p.consumerSources,source.sources);eq(source.controlPlan,p.consumerControlDefinitions);
  eq(definitions.schema,contract.definitionSchema);
  eq(definitions.scopes.map(r=>r.count),CONTROL_SCOPES.map(r=>r[1]));
  closed(plan,'schema scope inputs commands limits release');
  eq(plan.schema,contract.planSchema);eq(plan.scope,'SYNTHETIC_DATA_ONLY');
  eq(plan.release,p.consumerControlRelease);
  eq(plan.limits,{commandSeconds:60,stdoutRetainedBytes:1048576,stderrRetainedBytes:262144});
  need(Number.isSafeInteger(contract.inputCount)&&contract.inputCount>0&&contract.inputCount<=4096,'closed actual current input count');
  need(Array.isArray(plan.inputs)&&plan.inputs.length===contract.inputCount,'complete current input graph');
  need(new Set(plan.inputs.map(d=>d.path)).size===contract.inputCount,'distinct input paths');
  for(const d of [p.consumerSubject,p.python,...source.sources])need(plan.inputs.some(x=>x.path===d.path&&x.bytes===d.bytes&&x.sha256===d.sha256),'whole current consumer control closure');
  eq(release.schema,contract.releaseSchema);eq(release.actor,'/root');
  eq(release.decision,contract.releaseDecision);eq(release.runner,p.consumerControlCapture);
  eq(release.batch,Object.fromEntries(['schema','scope','inputs','commands','limits'].map(k=>[k,plan[k]])));
  eq(release.ordinaryRows,0);eq(release.runtimeAuthorized,false);
  closed(result,'schema plan commands failure remainingScopesExecuted scope ordinaryRows e02 retentionMeaning resultAcceptance');
  eq(result.schema,contract.resultSchema);eq(result.plan,p.consumerControlPlan);
  eq(result.failure,null);eq(result.remainingScopesExecuted,false);eq(result.scope,'SYNTHETIC_DATA_ONLY');
  eq(result.ordinaryRows,0);eq(result.e02,'PARTIAL22_UNCHANGED');
  eq(result.retentionMeaning,contract.retentionMeaning);
  eq(result.resultAcceptance,'PENDING_INDEPENDENT_QA_SECURITY'); // Original result is never rewritten after review.
  eq(result.commands.length,4);eq(plan.commands.length,4);eq(streams.length,4);
  for(let i=0;i<4;i++){
    const [name,count]=CONTROL_SCOPES[i], row=result.commands[i], proposed=plan.commands[i], definition=definitions.scopes[i];
    closed(proposed,'name argv expectedCases');
    eq(proposed.name,name);eq(proposed.expectedCases,count);
    const testSource=source.sources.find(d=>d.path.endsWith('/'+name));need(testSource,'source-bound test file');
    eq(proposed.argv,[p.python.path,'-I','-B',testSource.path]);eq(definition.source,testSource);
    eq(definition.exactDefinedNames.length,count);need(new Set(definition.exactDefinedNames).size===count,'distinct source-defined controls');
    closed(row,'name argv expectedCases startedUtcNs exitCode timeout naturalExit reaped stdoutEOF stderrEOF stdoutCapturedBytes stderrCapturedBytes stdout stderr truncated elapsedWallNs');
    eq(row.name,name);eq(row.argv,proposed.argv);eq(row.expectedCases,count);eq(row.exitCode,0);eq(row.timeout,false);
    for(const key of ['naturalExit','reaped','stdoutEOF','stderrEOF'])eq(row[key],true);
    eq(row.truncated,false);need(Number.isSafeInteger(row.elapsedWallNs)&&row.elapsedWallNs>=0,'finite wall duration');
    // startedUtcNs remains an opaque, raw-pin-preserved signed64 operand. JSON
    // Number rounding must never become a new clock/chronology attestation.
    need(typeof row.startedUtcNs==='number'&&Number.isFinite(row.startedUtcNs),'present original timestamp operand');
    eq(row.stdoutCapturedBytes,0);eq(streams[i].stdout.length,0);eq(row.stdout.bytes,0);
    eq(row.stderrCapturedBytes,streams[i].stderr.length);eq(row.stderr.bytes,streams[i].stderr.length);
    need(row.stderrCapturedBytes<=262144,'bounded retained stderr');
    unittestShape(streams[i].stderr,count,definition.exactDefinedNames);
  }
  eq(acceptance.schema,contract.acceptanceSchema);eq(acceptance.actor,'/root');
  eq(acceptance.subject,p.consumerControlResult);eq(acceptance.countsSeparate,[86,36,8,9]);
  eq(acceptance.decision,contract.acceptanceDecision);
  eq(acceptance.ordinaryRowsQualified,0);eq(acceptance.canonicalE02,'PARTIAL22_UNCHANGED');eq(acceptance.runtimeAuthorized,false);
  need(Array.isArray(acceptance.reviews)&&acceptance.reviews.length===2,'two actual result review references');
  return adapter;
}

export function controlToolShape(tool,p,result){
  need(CURRENT_CONTROL_ADAPTER_READY===true,'COMPLETION3_CURRENT_TOOL_ADAPTER_NULL_NOT_READY');
  closed(tool,'origin launch polls');
  eq(tool.origin,'Actual structured tool responses retained by coordinator; not child-generated command journals.');
  closed(tool.launch,'args result');
  need(p.consumerControlToolInvocation!==null&&typeof p.consumerControlToolInvocation==='object','ACTUAL_CURRENT_TOOL_INVOCATION_REQUIRED');
  eq(tool.launch.args,p.consumerControlToolInvocation);
  need(Array.isArray(tool.polls)&&tool.polls.length<=16,'bounded actual polls');
  const launch=tool.launch.result;let terminal;
  if(launch.session_id===undefined){
    eq(launch.exit_code,0);eq(tool.polls,[]);terminal=launch;
  }else{
    const session=launch.session_id;need(Number.isSafeInteger(session)&&session>0,'actual yielded session');
    need(launch.exit_code===undefined&&tool.polls.length>=1,'yielded launch and final poll required');
    for(const poll of tool.polls){closed(poll,'args result');eq(poll.args.session_id,session);eq(poll.args.chars,'');}
    for(const poll of tool.polls.slice(0,-1)){eq(poll.result.session_id,session);need(poll.result.exit_code===undefined,'no hidden earlier completion');}
    terminal=tool.polls.at(-1).result;eq(terminal.exit_code,0);need(terminal.session_id===undefined,'actual completed response');
  }
  const summary=JSON.parse(terminal.output.trim());eq(summary.execution,p.consumerControlResult);eq(summary.failure,result.failure);
  return tool;
}
