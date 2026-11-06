// SOURCE-only fixed production-path helper latency/timer recipe; no client claim.
import {createProductionGuard,productionSample} from './guard-client.mjs';
import {ALLOCATION,createByteAccount} from './capture-allocation.mjs';
const HELPER_SOURCE_PIN={"path":"/input/guard-helper.py","bytes":6219,"sha256":"743e0ed269445a4d59407336e399d1c7bd46c5337408b157e9ef85773e2157cf"};
const ORIGINAL_GUARD_PIN={"path":"/input/lease_guard.py","bytes":14846,"sha256":"d396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf"};

const start=productionSample().Mono,end=start+55000000000n;
const proof=createByteAccount(ALLOCATION.service-ALLOCATION.serviceHeader-ALLOCATION.serviceDiagnostics,'probe-proof');
const diagnostics=createByteAccount(ALLOCATION.serviceDiagnostics,'probe-diagnostics');
const timerRows=[],durations=[];let last=start,timer=null,guard=null,failure=null,checks=0;
const retain=(rows,value)=>{const encoded=JSON.stringify(value);proof.charge(Buffer.byteLength(encoded)+(rows.length?1:0));rows.push(encoded);};
const diagnostic=error=>{try{const raw=Buffer.from(String(error).slice(0,2048)+'\n');diagnostics.charge(raw.length);process.stderr.write(raw);}catch{}};
try{
 proof.charge(1024); // Timer/duration/result metadata and delimiter envelope.
 guard=createProductionGuard({helperPin:HELPER_SOURCE_PIN,guardPin:ORIGINAL_GUARD_PIN,proofAccount:proof,reservationIndex:null,onFatal:error=>{failure??=error;},ownerDeadlines:()=>[end-2000000000n],cleanupDeadlines:()=>[end]});
 timer=setInterval(()=>{
  try{const now=productionSample().Mono;if(timerRows.length>=5500)throw Error('PROBE_TIMER_CAPTURE_BOUND');retain(timerRows,{monoNs:String(now),gapNs:String(now-last)});last=now;}
  catch(error){failure??=error;guard.cancel(error);clearInterval(timer);}
 },10);
 for(let i=0;i<64;i++){
  const begin=productionSample().Mono;
  await guard.run('probe:warm-'+String(i),Buffer.from(String(i)),()=>{checks++;});
  retain(durations,String(productionSample().Mono-begin));
 }
 await new Promise(resolve=>setTimeout(resolve,100));
 clearInterval(timer);
 const encodedAudit=await guard.finish();if(failure)throw failure;
 const metadata={schema:'e02-owned-fresh-guard-latency-probe-v1',checks,timerMilliseconds:10,elapsedNanoseconds:String(productionSample().Mono-start),clientRowsQualified:0,relayCause:'UNKNOWN',scope:'OWNED_HELPER_LATENCY_TIMER_DISPATCH_ONLY'};
 const header=JSON.stringify(metadata).slice(0,-1)+',"durationsNanoseconds":';
 if(Buffer.byteLength(header)+80>1024)throw Error('PROBE_METADATA_ENVELOPE');
 const output=header+'['+durations.join(',')+'],"timerRows":['+timerRows.join(',')+'],"guardController":'+encodedAudit+'}\n';
 if(Buffer.byteLength(output)>proof.state().chargedBytes)throw Error('PROBE_PRECHARGED_ENCODING_REQUIRED');
 process.stdout.write(output,error=>{if(error){guard.cancel(error);process.exitCode=2;}});
}catch(error){if(timer)clearInterval(timer);if(guard)await guard.shutdownAfterFailure(error).catch(()=>{});diagnostic(error);process.exitCode=2;}
