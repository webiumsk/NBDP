// Production transport factory. Imports never start a child or read lease/runtime.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {createGuardClient} from './guard-client-core.mjs';
import {strictGuardJSON,createGuardFramer} from './guard-wire.mjs';
import {ALLOCATION,createAuditStaging} from './capture-allocation.mjs';
import {cleanupPlan,dispatchOwnedSignal,registerHelperTerminalCallbacks} from './guard-transport-boundaries.mjs';
const need=(x,s)=>{if(!x)throw Error(s);};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const GUARD_SHA='d396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf';
export function productionSample(){
 const start=process.hrtime.bigint(),utcLower=BigInt(Date.now())*1000000n;
 const fd=fs.openSync('/proc/uptime',fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);
 let text;try{const b=Buffer.alloc(128),n=fs.readSync(fd,b,0,b.length,null);need(n>0&&n<128,'BOOTTIME_PROC_BOUND');text=b.subarray(0,n).toString('ascii');}finally{fs.closeSync(fd);}
 const m=/^([0-9]{1,16})\.([0-9]{1,9}) [0-9]+\.[0-9]+\n$/.exec(text);need(m,'BOOTTIME_PROC_DECIMAL');
 const bootLower=(BigInt(m[1])*1000000000n)+BigInt(m[2].padEnd(9,'0'));
 const boot=bootLower+10n**BigInt(9-m[2].length);
 const utc=BigInt(Date.now())*1000000n+1000000n;
 const mono=process.hrtime.bigint();
 return {Utc:utc+(mono-start),Mono:mono,Boot:boot+(mono-start),UtcLower:utcLower,MonoLower:start,BootLower:bootLower-(mono-start)};
}
function originalLease(expected){
 need(/^[0-9a-f]{64}$/.test(expected??''),'EXTERNAL_ORIGINAL_LEASE_SHA');
 const fd=fs.openSync('/session/lease.json',fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);
 let raw;try{const st=fs.fstatSync(fd);need(st.isFile()&&st.size<=8192,'BOUNDED_ORIGINAL_LEASE');raw=fs.readFileSync(fd);need(raw.length===st.size&&sha(raw)===expected,'ORIGINAL_LEASE_HASH');}finally{fs.closeSync(fd);}
 // Closed original lease uses only strings and integer values. Preserve ns as
 // exact decimal strings BEFORE parsing, rather than rounding JS Numbers.
 const p=strictGuardJSON(raw.toString('utf8').replace(/:\s*([0-9]+)(?=\s*[,}])/g,':"$1"'));
 const expectedKeys=['schema','runId','issuedUtcNs','deadlineUtcNs','issuedMonoNs','deadlineMonoNs','issuedBootNs','deadlineBootNs','bootId'];
 need(Object.keys(p).sort().join(',')===expectedKeys.sort().join(',')&&p.schema==='e02-single-cell-lease-v1'&&/^[0-9a-f]{32}$/.test(p.runId),'CLOSED_ORIGINAL_LEASE');
 for(const k of ['Utc','Mono','Boot'])for(const stem of ['issued','deadline']){const key=stem+k+'Ns';need(/^[1-9][0-9]{0,23}$/.test(p[key]),'ORIGINAL_DECIMAL_NS');p[key]=BigInt(p[key]);}
 return p;
}
export function createProductionGuard({helperPin,guardPin,onFatal=()=>{},ownerDeadlines=()=>[],cleanupDeadlines=ownerDeadlines,proofAccount,reservationIndex=null}){
 need(helperPin.path==='/input/guard-helper.py'&&Number.isSafeInteger(helperPin.bytes)&&helperPin.bytes>0&&helperPin.bytes<=8388608&&/^[0-9a-f]{64}$/.test(helperPin.sha256),'PINNED_HELPER');
 need(guardPin.path==='/input/lease_guard.py'&&guardPin.sha256===GUARD_SHA,'BYTE_IDENTICAL_ORIGINAL_CORE');
 need(proofAccount&&typeof proofAccount.charge==='function'&&proofAccount.state().limit<=ALLOCATION.service-ALLOCATION.serviceHeader-ALLOCATION.serviceDiagnostics,'PREHELPER_OWNED_PROOF_ACCOUNT');
 if(reservationIndex!==null)need(Number.isInteger(reservationIndex)&&reservationIndex>=1&&reservationIndex<=64&&proofAccount.state().limit===ALLOCATION.proof,'EXACT_ASSIGNED_CONTROLLER_SLOT');
 const expected=process.env.NBDP_LEASE_SHA256,lease=originalLease(expected),instance=crypto.randomBytes(16).toString('hex');
 let child=null,handlers=null,framer=createGuardFramer(),closedExpected=false;
 const life={ended:false,exitSeen:false,closeSeen:false,stdoutEOF:false,stderrEOF:false,secondaryErrors:[]};
 let observer=null,drainResolve=null,cleanupTimer=null,killTimer=null,failureDrain=null;
 const configurationSha256=process.env.NBDP_MINIMUM_RUN_CONFIG_SHA256;
 need(/^[0-9a-f]{64}$/.test(configurationSha256??''),'EXACT_EXTERNAL_CONFIGURATION_SHA');
 const audit=createAuditStaging({account:proofAccount,metadata:{schema:'e02-controller-guard-audit-v1',reservationIndex,instance,scope:'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',runId:lease.runId,leaseSha256:expected,configurationSha256}});
 const record=(name,fields)=>{fields={...fields,helperInstance:instance};if(observer)return observer(name,fields);audit.append(name,fields);};
 const effectiveDeadlines=()=>[...ownerDeadlines(),lease.deadlineMonoNs-2000000000n];

 function bad(error){handlers.fatal(error);}
 const transport={
  bind(value){handlers=value;},
  start(){
   if(child)return;
   const helper=fs.lstatSync(helperPin.path);need(helper.isFile()&&!helper.isSymbolicLink()&&helper.size===helperPin.bytes&&sha(fs.readFileSync(helperPin.path))===helperPin.sha256,'HELPER_SOURCE_PIN');
   const argv=['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/guard-helper.py',instance,expected,String(helperPin.bytes),helperPin.sha256];
   record('GUARD_HELPER_LAUNCH',{executable:'/guard-python/lib/ld-linux-x86-64.so.2',argv});
   child=spawn('/guard-python/lib/ld-linux-x86-64.so.2',argv,{env:process.env,stdio:['pipe','pipe','pipe'],detached:false,shell:false});
   record('GUARD_HELPER_CREATED',{pid:child.pid??null});
   child.stdout.on('data',chunk=>{
    try{
     need(!life.ended,'EXTRA_GUARD_STDOUT_AFTER_CLOSE');const raw=framer.accept(chunk);if(raw===null)return;
     const close=closedExpected;handlers.response(raw);if(close){life.ended=true;child.stdin.end();}
    }catch(error){bad(error);}
   });
   registerHelperTerminalCallbacks({child,state:life,record,bad,framer,onClose:()=>{
    if(cleanupTimer)clearTimeout(cleanupTimer);if(killTimer)clearTimeout(killTimer);
    if(drainResolve){const done=drainResolve;drainResolve=null;done();}
   }});
  },
  send(raw){
   if(strictGuardJSON(raw.toString('utf8')).operation==='CLOSE')closedExpected=true;
   need(child!==null&&child.exitCode===null&&child.signalCode===null,'LIVE_OWNED_HELPER');
   child.stdin.write(raw,error=>{if(error)bad(error);});
  },
  abort(error){
   if(!child||life.closeSeen)return;
   // This exact ChildProcess handle owns signaling; no PID/group lookup.
   try{child.stdin.end();}catch{}
   const now=productionSample().Mono;
   const end=cleanupDeadlines().reduce((a,b)=>a<b?a:b,lease.deadlineMonoNs);
   const plan=cleanupPlan(now,end);
   const dispatch=signal=>dispatchOwnedSignal({sample:()=>productionSample().Mono,end,child,signal,record:(name,fields)=>record(name,{...fields,reason:String(error)})});
   if(plan.signal===null){dispatch('SIGKILL');return;}
   dispatch(plan.signal);
   if(plan.escalationDelayMs!==null&&!killTimer)killTimer=setTimeout(()=>{if(!life.closeSeen)dispatch('SIGKILL');},plan.escalationDelayMs);

  }
 };
 const core=createGuardClient({transport,clock:{sample:productionSample,arm:setTimeout,clear:clearTimeout},lease,leaseSha256:expected,instance,observe:record,onFatal,ownerDeadlines:effectiveDeadlines,isRevoked:()=>{try{fs.lstatSync('/session/control/REVOKED');return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}}});
 return {...core,secondaryErrors:()=>[...core.secondaryErrors(),...life.secondaryErrors].map(row=>({...row})),effectDeadlineMonoNs:effectiveDeadlines().reduce((a,b)=>a<b?a:b),
  attachObserver(fn){need(observer===null&&typeof fn==='function','ONE_GUARD_OBSERVER');observer=fn;for(const row of audit.rows())fn(row.name,row.fields);},
  async shutdownAfterFailure(error){
   core.cancel(error);
   if(failureDrain!==null)return await failureDrain;
   failureDrain=(async()=>{
    if(!child||life.closeSeen)return;
    const now=productionSample().Mono,end=cleanupDeadlines().reduce((a,b)=>a<b?a:b,lease.deadlineMonoNs);
    if(end<=now)throw Error('OWNED_HELPER_DRAIN_DEADLINE_EXHAUSTED');
    await new Promise((resolve,reject)=>{drainResolve=resolve;cleanupTimer=setTimeout(()=>reject(Error('OWNED_HELPER_DRAIN_NOT_OBSERVED')),Math.min(2000,Number((end-now)/1000000n)));});
    need(life.closeSeen&&life.exitSeen&&life.stdoutEOF&&life.stderrEOF,'ACTUAL_OWNED_HELPER_DRAIN_REQUIRED');
   })();
   return await failureDrain;
  },
  async finish(){
   await core.close();
   if(!life.closeSeen)await new Promise((resolve,reject)=>{
    drainResolve=resolve;
    // Two seconds, within original owner deadline; terminal already closed to use.
    const now=productionSample().Mono,deadlines=[...cleanupDeadlines(),lease.deadlineMonoNs],end=deadlines.reduce((a,b)=>a<b?a:b,now+2000000000n);
    const ms=Number((end-now)/1000000n);if(ms<=0){transport.abort(Error('GUARD_CLEANUP_OWNER_DEADLINE'));reject(Error('GUARD_CLEANUP_OWNER_DEADLINE'));return;}
    cleanupTimer=setTimeout(()=>{transport.abort(Error('GUARD_CLEANUP_DEADLINE'));reject(Error('GUARD_CLEANUP_DEADLINE'));},ms);
   });
   need(core.state().firstFault===null&&life.stdoutEOF&&life.stderrEOF&&life.exitSeen&&life.closeSeen,'NATURAL_GUARD_HELPER_LIFECYCLE');return observer===null?audit.emit():null;
  }
 };
}
