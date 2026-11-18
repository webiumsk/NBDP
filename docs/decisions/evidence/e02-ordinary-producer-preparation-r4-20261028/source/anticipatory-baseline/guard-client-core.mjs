// Pure dependency-injected finite scheduler. Production effects are synchronous.
import {createHash} from 'node:crypto';
import {strictGuardJSON} from './guard-wire.mjs';
const sha=raw=>createHash('sha256').update(raw).digest('hex');
const need=(x,why)=>{if(!x)throw Error(why);};
const keys=(o,expected)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).sort().join(',')===expected.sort().join(',');
const REPLY_KEYS=['schema','operation','instance','runId','leaseSha256','sequence','label','contextSha256','requestSha256','ok','clocks'];
export function createGuardClient({transport,clock,lease,leaseSha256,instance,observe=()=>{},onFatal=()=>{},ownerDeadlines=()=>[]}){
 let epoch=0,firstFault=null,sequence=0,active=null,queue=[],closing=false,closed=false,queuedBytes=0;
 const needLive=()=>{if(firstFault)throw firstFault;need(!closed&&!closing,'GUARD_OWNER_CLOSED');};
 function record(name,fields){observe(name,{helperInstance:instance,...fields});}
 function fatal(error){
  if(firstFault!==null)return firstFault;firstFault=error instanceof Error?error:Error(String(error));epoch++;
  const pending=[...(active?[active]:[]),...queue];active=null;queue=[];queuedBytes=0;
  for(const item of pending){clock.clear(item.timer);item.reject(firstFault);}
  // Fencing/rejection precedes observation and cancellation. Never enter queue.
  try{record('GUARD_TERMINAL',{error:String(firstFault),epoch});}catch{}
  try{onFatal(firstFault);}catch{}
  try{transport.abort(firstFault);}catch{}
  return firstFault;
 }
 function clocksBeforeEffect(item){
  const now=clock.sample(); // UTC/BOOT conservative upper bounds in production.
  need(now.Mono<item.deadline,'GUARD_ENQUEUE_INCLUSIVE_DEADLINE');
  for(const end of [...item.deadlines,...ownerDeadlines()])need(now.Mono<end,'ORIGINAL_OPERATION_DEADLINE');
  need(now.Utc<lease.deadlineUtcNs&&now.Mono<lease.deadlineMonoNs&&now.Boot<lease.deadlineBootNs,'ORIGINAL_LEASE_DEADLINE');
  need(now.Utc>=lease.issuedUtcNs&&now.Mono>=lease.issuedMonoNs&&now.Boot>=lease.issuedBootNs,'CLOCK_BEFORE_ORIGINAL_ISSUE');
  return now;
 }
 function response(raw){
  if(firstFault||closed){return;} // Late bytes do not become success evidence.
  try{
   need(active!==null,'UNSOLICITED_GUARD_REPLY');const item=active;
   need(Buffer.isBuffer(raw)&&raw.length<=2048&&raw.at(-1)===10,'BOUNDED_GUARD_REPLY');
   const text=new TextDecoder('utf-8',{fatal:true}).decode(raw),r=strictGuardJSON(text);
   need(keys(r,[...REPLY_KEYS])&&r.schema==='e02-fresh-guard-response-v1'&&r.ok===true,'GUARD_RESPONSE_SHAPE');
   for(const k of ['operation','instance','runId','leaseSha256','sequence','label','contextSha256'])need(r[k]===item.request[k],'GUARD_RESPONSE_CONTEXT');
   need(r.requestSha256===sha(item.raw),'GUARD_REQUEST_BYTES_JOIN');
   need(item.epoch===epoch,'GUARD_EPOCH_CHANGED');
   if(item.request.operation==='CHECK'){
    need(keys(r.clocks,['Utc','Mono','Boot','bootId'])&&r.clocks.bootId===lease.bootId,'ORIGINAL_CLOCK_IDENTITY');
    for(const k of ['Utc','Mono','Boot']){
     need(typeof r.clocks[k]==='string'&&/^(0|[1-9][0-9]{0,23})$/.test(r.clocks[k]),'EXACT_CLOCK_DECIMAL');
     need(BigInt(r.clocks[k])>=lease['issued'+k+'Ns']&&BigInt(r.clocks[k])<lease['deadline'+k+'Ns'],'FRESH_CORE_CLOCK_DEADLINE');
    }
   }else need(r.clocks===null&&closing&&queue.length===0,'ORDERLY_CLOSE_RESPONSE');
   // Raw response is retained before commit; observation failure cannot authorize.
   record('GUARD_RPC_REPLY',{sequence:item.request.sequence,rawBase64:raw.toString('base64')});
   clocksBeforeEffect(item);
   need(item.valid()===true,'CURRENT_GUARD_CONTEXT_CHANGED');
   // No yield occurs between final clocks/context validation and synchronous effect.
   clock.clear(item.timer);
   const result=item.effect();need(!result||typeof result.then!=='function','NO_ASYNC_GUARDED_EFFECT');
   record('GUARD_EXIT',{label:item.request.label,sequence:item.request.sequence,ok:true,error:null,consumed:true});
   active=null;queuedBytes-=item.contextBytes;item.resolve(result);if(item.request.operation==='CLOSE')closed=true;else pump();
  }catch(error){fatal(error);}
 }
 function pump(){
  if(active||firstFault||closed||queue.length===0)return;
  try{const item=queue.shift();active=item;clocksBeforeEffect(item);need(item.epoch===epoch&&item.valid()===true,'QUEUED_CONTEXT_CHANGED');
   record('GUARD_RPC_REQUEST',{label:item.request.label,sequence:item.request.sequence,rawBase64:item.raw.toString('base64'),enqueueMonoNs:String(item.enqueued),decisionDeadlineMonoNs:String(item.deadline)});
   transport.send(item.raw);
  }catch(error){fatal(error);}
 }
 function submit(operation,label,context,effect,valid,deadlines){
  return new Promise((resolve,reject)=>{
   try{
    needLive();need(typeof label==='string'&&/^[a-zA-Z0-9:_-]{1,160}$/.test(label),'CLOSED_GUARD_LABEL');
    need(Buffer.isBuffer(context)&&context.length<=16777216,'GUARD_CONTEXT_BOUND');
    need(queue.length+(active?1:0)<64&&queuedBytes+context.length<=16777216,'GUARD_QUEUE_BOUND');
    need(sequence<9007199254740990&&typeof effect==='function'&&typeof valid==='function','CLOSED_GUARD_CONTINUATION');
    const enqueued=clock.sample().Mono,deadline=enqueued+5000000000n;
    const request={schema:'e02-fresh-guard-request-v1',operation,instance,runId:lease.runId,leaseSha256,sequence:String(++sequence),label,contextSha256:sha(context)};
    const raw=Buffer.from(JSON.stringify(request)+'\n');need(raw.length<=1024,'GUARD_REQUEST_BOUND');
    const item={request,raw,effect,valid,deadlines:[...deadlines],enqueued,deadline,epoch,resolve,reject,contextBytes:context.length,timer:null};
    record('GUARD_ENTRY',{label,sequence:request.sequence,enqueueMonoNs:String(enqueued)});
    item.timer=clock.arm(()=>fatal(Error('GUARD_DECISION_TIMEOUT')),5000);queuedBytes+=context.length;queue.push(item);
    if(operation==='CLOSE')closing=true;
    // Lazy start charges startup to this first request's original5s deadline.
    transport.start();pump();
   }catch(error){reject(fatal(error));}
  });
 }
 transport.bind({response,fatal});
 return {
  run:(label,context,effect,{valid=()=>true,deadlines=[]}={})=>submit('CHECK',label,context,effect,valid,deadlines),
  close:()=>{need(!active&&queue.length===0,'CLOSE_REQUIRES_ZERO_PENDING');return submit('CLOSE','owner-close',Buffer.alloc(0),()=>null,()=>closing,[]);},
  cancel:fatal,state:()=>({epoch,firstFault:firstFault===null?null:String(firstFault),pending:queue.length+(active?1:0),closed,closing,sequence})
 };
}
