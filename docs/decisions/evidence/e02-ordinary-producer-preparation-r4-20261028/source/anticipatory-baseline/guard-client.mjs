// Production transport factory. Imports never start a child or read lease/runtime.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {createGuardClient} from './guard-client-core.mjs';
import {strictGuardJSON} from './guard-wire.mjs';
const need=(x,s)=>{if(!x)throw Error(s);};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const GUARD_SHA='d396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf';
export function productionSample(){
 const start=process.hrtime.bigint();
 const fd=fs.openSync('/proc/uptime',fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);
 let text;try{const b=Buffer.alloc(128),n=fs.readSync(fd,b,0,b.length,null);need(n>0&&n<128,'BOOTTIME_PROC_BOUND');text=b.subarray(0,n).toString('ascii');}finally{fs.closeSync(fd);}
 const m=/^([0-9]{1,16})\.([0-9]{1,9}) [0-9]+\.[0-9]+\n$/.exec(text);need(m,'BOOTTIME_PROC_DECIMAL');
 const boot=(BigInt(m[1])*1000000000n)+BigInt(m[2].padEnd(9,'0'))+10n**BigInt(9-m[2].length);
 const utc=BigInt(Date.now())*1000000n+1000000n;
 const mono=process.hrtime.bigint();
 return {Utc:utc+(mono-start),Mono:mono,Boot:boot+(mono-start)};
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
export function createProductionGuard({helperPin,guardPin,onFatal=()=>{},ownerDeadlines=()=>[]}){
 need(helperPin.path==='/input/guard-helper.py'&&Number.isSafeInteger(helperPin.bytes)&&helperPin.bytes>0&&helperPin.bytes<=8388608&&/^[0-9a-f]{64}$/.test(helperPin.sha256),'PINNED_HELPER');
 need(guardPin.path==='/input/lease_guard.py'&&guardPin.sha256===GUARD_SHA,'BYTE_IDENTICAL_ORIGINAL_CORE');
 const expected=process.env.NBDP_LEASE_SHA256,lease=originalLease(expected),instance=crypto.randomBytes(16).toString('hex');
 let child=null,handlers=null,buffer=Buffer.alloc(0),closedExpected=false,ended=false,exitSeen=false,closeSeen=false,stdoutEOF=false,stderrEOF=false;
 let observer=null,audit=[],auditBytes=0,drainResolve=null,cleanupTimer=null,killTimer=null;
 const record=(name,fields)=>{if(observer)return observer(name,fields);const row={name,fields};auditBytes+=Buffer.byteLength(JSON.stringify(row));need(auditBytes<=1048576,'CONTROLLER_GUARD_AUDIT_BOUND');audit.push(row);};
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
   child.on('error',bad);
   child.stdout.on('data',chunk=>{
    try{
     need(!ended,'EXTRA_GUARD_STDOUT_AFTER_CLOSE');need(buffer.length+chunk.length<=2048,'GUARD_STDOUT_FRAME_BOUND');buffer=Buffer.concat([buffer,chunk]);
     const end=buffer.indexOf(10);if(end<0)return;
     need(end===buffer.length-1,'EXTRA_GUARD_RESPONSE_LINES');const raw=buffer;buffer=Buffer.alloc(0);
     const close=closedExpected;handlers.response(raw);if(close){ended=true;child.stdin.end();}
    }catch(error){bad(error);}
   });
   child.stderr.on('data',chunk=>{try{record('GUARD_HELPER_STDERR',{rawBase64:Buffer.from(chunk).subarray(0,2048).toString('base64')});}finally{bad(Error('GUARD_HELPER_STDERR'));}});
   child.stdout.on('end',()=>{stdoutEOF=true;try{record('GUARD_HELPER_STDOUT_EOF',{});}catch(e){bad(e);}if(!ended)bad(Error('UNEXPECTED_GUARD_STDOUT_EOF'));});
   child.stderr.on('end',()=>{stderrEOF=true;try{record('GUARD_HELPER_STDERR_EOF',{});}catch(e){bad(e);}});
   child.on('exit',(code,signal)=>{exitSeen=true;try{record('GUARD_HELPER_EXIT',{code,signal});}catch(e){bad(e);}if(!ended||code!==0||signal!==null)bad(Error('GUARD_HELPER_UNEXPECTED_EXIT'));});
   child.on('close',(code,signal)=>{
    closeSeen=true;try{record('GUARD_HELPER_CLOSE',{code,signal,stdoutEOF,stderrEOF,exitSeen});}catch(e){bad(e);}
    if(cleanupTimer)clearTimeout(cleanupTimer);if(killTimer)clearTimeout(killTimer);
    if(drainResolve){const done=drainResolve;drainResolve=null;done();}
    if(!ended||code!==0||signal!==null||!stdoutEOF||!stderrEOF||!exitSeen)bad(Error('GUARD_HELPER_LIFECYCLE_NEGATIVE'));
   });
  },
  send(raw){
   if(strictGuardJSON(raw.toString('utf8')).operation==='CLOSE')closedExpected=true;
   need(child!==null&&child.exitCode===null&&child.signalCode===null,'LIVE_OWNED_HELPER');
   child.stdin.write(raw,error=>{if(error)bad(error);});
  },
  abort(error){
   if(!child||closeSeen)return;
   // This exact ChildProcess handle owns signaling; no PID/group lookup.
   try{child.stdin.end();}catch{}
   try{child.kill('SIGTERM');record('GUARD_HELPER_TERMINATE',{signal:'SIGTERM',reason:String(error)});}catch{}
   if(!killTimer)killTimer=setTimeout(()=>{if(!closeSeen)try{child.kill('SIGKILL');record('GUARD_HELPER_TERMINATE',{signal:'SIGKILL'});}catch{}},1000);
  }
 };
 const core=createGuardClient({transport,clock:{sample:productionSample,arm:setTimeout,clear:clearTimeout},lease,leaseSha256:expected,instance,observe:record,onFatal,ownerDeadlines});
 return {...core,
  attachObserver(fn){need(observer===null&&typeof fn==='function','ONE_GUARD_OBSERVER');observer=fn;for(const row of audit)fn(row.name,row.fields);audit=[];auditBytes=0;},
  async finish(){
   await core.close();
   if(!closeSeen)await new Promise((resolve,reject)=>{
    drainResolve=resolve;
    // Two seconds, within original owner deadline; terminal already closed to use.
    const now=productionSample().Mono,deadlines=ownerDeadlines(),end=deadlines.reduce((a,b)=>a<b?a:b,now+2000000000n);
    const ms=Number((end-now)/1000000n);if(ms<=0){transport.abort(Error('GUARD_CLEANUP_OWNER_DEADLINE'));reject(Error('GUARD_CLEANUP_OWNER_DEADLINE'));return;}
    cleanupTimer=setTimeout(()=>{transport.abort(Error('GUARD_CLEANUP_DEADLINE'));reject(Error('GUARD_CLEANUP_DEADLINE'));},ms);
   });
   need(core.state().firstFault===null&&stdoutEOF&&stderrEOF&&exitSeen&&closeSeen,'NATURAL_GUARD_HELPER_LIFECYCLE');return {instance,observations:audit,scope:'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION'};
  }
 };
}
