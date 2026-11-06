// SOURCE ONLY: one direct backend PUB/REQ diagnostic, never an APP observation.
import fs from 'node:fs';
import net from 'node:net';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {exchange} from './exchange.mjs';
import {createPhaseWriter} from './phase-writer.mjs';
import {verifyDependencyTree} from './dependency-tree.mjs';
import {strictJSON,same} from './strict-json.mjs';
const DIR='/session/fixtures',PLAN='/input/fixture-plan.json',SOCKET=DIR+'/control.sock';
const sha=b=>createHash('sha256').update(b).digest('hex');
function need(v,m){if(!v)throw Error(m);}
function read(p){const b=fs.readFileSync(p);need(b.length<=16777216,'INPUT_BOUND');return b;}
function put(name,b){need(/^[a-z0-9.-]+$/.test(name)&&b.length<=16777216,'BOUNDED_FIXED_OUTPUT');const path=DIR+'/'+name;fs.writeFileSync(path,b,{flag:'wx',mode:0o600});return {path,bytes:b.length,sha256:sha(b)};}
function putJSON(name,v){return put(name,Buffer.from(JSON.stringify(v,null,2)+'\n'));}
// The guard invocation/body is byte-for-byte the original check body, renamed.
function guardCheck(){
 const expected=process.env.NBDP_LEASE_SHA256;need(/^[0-9a-f]{64}$/.test(expected??''),'EXTERNAL_LEASE_SHA');
 const argv=['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/lease_guard.py','check',expected];
 const r=spawnSync('/guard-python/lib/ld-linux-x86-64.so.2',argv,{env:process.env,timeout:5000,maxBuffer:1048576});
 need(!r.error&&r.status===0&&r.signal===null,'FINITE_LEASE_DENIED:'+String(r.stderr??'').slice(0,2048));
}
async function main(){
 need(process.argv.length===3&&['serve','prepare','status','publish'].includes(process.argv[2]),'CLOSED_DIAGNOSTIC_CLI');
 guardCheck();
 const pb=read(PLAN);need(sha(pb)===process.env.NBDP_FIXTURE_PLAN_SHA256,'EXACT_PLAN');const p=strictJSON(pb.toString());
 need(process.version==='v22.18.0','PINNED_NODE_VERSION');
 need(p.schema==='e02-transport-query-diagnostic-fixture-v2'&&p.scenario==='BASELINE_ONE_PUB_THEN_EXACT_QUERY'&&p.backendUrl==='ws://127.0.0.1:8080','CLOSED_BASELINE');
 need(JSON.stringify(p.limits)===JSON.stringify({messageBytes:262144,captureBytes:16777216,networkTimeoutMilliseconds:10000,handshakeTimeoutMilliseconds:3000,controlTimeoutMilliseconds:45000}),'UNCHANGED_LIMITS');
 const tree=strictJSON(read('/input/dependency-tree.json').toString());
 verifyDependencyTree('/input/node_modules',tree,p.dependencyFiles);
 const wsPackage=strictJSON(read('/input/node_modules/ws/package.json').toString());need(wsPackage.version==='8.18.3','PINNED_WS_VERSION');
 const config=read('/input/run-config.json');need(sha(config)===process.env.NBDP_MINIMUM_RUN_CONFIG_SHA256,'EXACT_CONFIG');
 if(process.argv[2]!=='serve'){
  const response=await new Promise((resolve,reject)=>{const c=net.connect(SOCKET);let b=Buffer.alloc(0);const timer=setTimeout(()=>{c.destroy();reject(Error('CONTROL_TIMEOUT'));},45000);c.on('connect',()=>{guardCheck();c.end(JSON.stringify({op:process.argv[2]})+'\n');});c.on('data',x=>{b=Buffer.concat([b,x]);if(b.length>1048576){c.destroy();reject(Error('CONTROL_REPLY_BOUND'));}});c.on('end',()=>{clearTimeout(timer);try{resolve(strictJSON(b.toString()));}catch(error){reject(error);}});c.on('error',error=>{clearTimeout(timer);reject(error);});});
  guardCheck();need(response.ok===true,'DIAGNOSTIC_COMMAND_FAILED:'+response.error);process.stdout.write(JSON.stringify(response)+'\n');return;
 }
 const {default:WebSocket}=await import('ws');guardCheck();
 let closed=false,attempted=false,prepared=false,busy=false;
 const sockets=new Set();const fd=fs.openSync(DIR+'/phase-trace.jsonl','wx',0o600);
 const phase=createPhaseWriter({fs,fd,clock:()=>process.hrtime.bigint(),utc:()=>new Date().toISOString()});
 function check(label){
  phase('GUARD_ENTRY',{label});
  try{guardCheck();}
  catch(error){try{phase('GUARD_EXIT_REFUSED',{label,error:String(error)});}catch(retentionError){try{Object.defineProperty(error,'guardRetentionError',{value:String(retentionError)});}catch{}}throw error;}
  phase('GUARD_EXIT_OK',{label});
 }
 const pub=read('/input/publish-frame.json'),query=read('/input/query-frame.json');
 need(sha(pub)===p.publish.sha256&&pub.length===p.publish.bytes&&sha(query)===p.query.sha256&&query.length===112,'EXACT_FROZEN_PUBLIC_FRAMES');
 const pf=strictJSON(pub.toString()),qf=strictJSON(query.toString());
 need(pf[0]==='EVENT'&&pf.length===2&&pf[1].id===p.eventId&&pf[1].kind===1059,'ORIGINAL_SIGNED_OUTER');
 need(JSON.stringify(qf)===JSON.stringify(['REQ','e02-owned-query',{ids:[p.eventId],limit:1}]),'UNCHANGED_EXACT_QUERY');
 need(Buffer.from(JSON.stringify(pf)).equals(pub)&&Buffer.from(JSON.stringify(qf)).equals(query),'EXACT_SERIALIZED_BUFFERS');
 const terminationAttempts=new WeakSet();
 const ctx={WebSocket:class extends WebSocket{constructor(...a){super(...a);sockets.add(this);}terminate(){if(terminationAttempts.has(this))return;terminationAttempts.add(this);return super.terminate();}},p,check,phase,put,strictJSON,sha,clock:()=>process.hrtime.bigint(),arm:setTimeout,clear:clearTimeout};
 async function baseline(){
  check('baseline-entry');need(prepared&&!attempted,'ONE_PREPARED_BASELINE_ONLY');attempted=true;
  const publication=await exchange(ctx,[pf[1]],null,'baseline-publish');check('after-publication');
  const received=await exchange(ctx,null,qf[2],'baseline-query');check('after-query');
  need(received.received.length===1&&same(received.received[0].frame[2],pf[1])&&received.eose?.frame[1]==='e02-owned-query','EXACT_REAL_QUERY_EVENT_AND_EOSE');
  verifyDependencyTree('/input/node_modules',tree,p.dependencyFiles);
  const result=putJSON('baseline-result.json',{schema:'e02-transport-query-baseline-v2',state:'BASELINE_PUB_QUERY_OBSERVED',publication,query:received,diagnosticOnly:true,ordinaryClientObserved:false,signEncryptDecryptExecuted:false,nativeRustExecuted:false});
  return {state:'BASELINE_PUB_QUERY_OBSERVED',result};
 }
 const server=net.createServer({allowHalfOpen:true},socket=>{let b='';socket.on('data',x=>{b+=x.toString();if(Buffer.byteLength(b)>1024)socket.destroy();});socket.on('end',async()=>{let acquired=false;try{
  check('control-entry');const q=strictJSON(b);need(Object.keys(q).length===1&&['prepare','status','publish'].includes(q.op)&&!busy&&!closed,'CLOSED_FINITE_COMMAND');busy=true;acquired=true;let result;
  if(q.op==='prepare'){need(!prepared&&!attempted,'PREPARE_ONCE');prepared=true;result={ready:true,scenario:p.scenario};}
  else if(q.op==='status')result={prepared,attempted,diagnosticOnly:true};
  else result=await baseline();
  check('control-success');socket.end(JSON.stringify({schema:'e02-transport-query-control-v2',ok:true,operation:q.op,result})+'\n');
 }catch(error){try{phase('CONTROL_REJECTED',{error:String(error)});}catch{}try{putJSON('control-error.json',{error:String(error),secondaryRetentionErrors:error?.diagnosticSecondaryErrors??[],guardRetentionError:error?.guardRetentionError??null,observer:phase.state()});}catch{}socket.end(JSON.stringify({ok:false,error:String(error)})+'\n');closed=true;clearInterval(watchdog);for(const s of sockets)s.terminate();server.close();process.exitCode=2;
 }finally{if(acquired)busy=false;}});});
 const watchdog=setInterval(()=>{if(closed)return;try{check('original-watchdog');}catch(error){try{phase('WATCHDOG_REFUSED',{error:String(error)});}catch{}closed=true;for(const s of sockets)s.terminate();server.close();clearInterval(watchdog);process.exitCode=2;}},1000);
 server.on('error',error=>{try{phase('CONTROL_SERVER_ERROR',{error:String(error)});}catch{}closed=true;clearInterval(watchdog);for(const s of sockets)s.terminate();process.exitCode=2;});
 check('control-listen-before');server.listen(SOCKET,()=>{fs.chmodSync(SOCKET,0o600);putJSON('serve-ready.json',{schema:'e02-transport-query-ready-v2',scope:'DIAGNOSTIC_ONLY_NO_APP_PROXY_OR_OBSERVATIONS',nodeVersion:process.version,nodeExecutable:process.execPath,wsVersion:wsPackage.version});});
 process.once('exit',()=>{try{fs.fsyncSync(fd);fs.closeSync(fd);}catch{}});
 for(const signal of ['SIGTERM','SIGINT'])process.on(signal,()=>{if(closed)return;closed=true;clearInterval(watchdog);for(const s of sockets)s.terminate();server.close();fs.fsyncSync(fd);});
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)main().catch(error=>{process.stderr.write(String(error)+'\n');process.exitCode=2;});
