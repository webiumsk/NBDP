// SOURCE ONLY fixed negative case CLI. No dependent import before source/release pins.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const HERE=path.dirname(fileURLToPath(import.meta.url));
const NODE={path:'/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node',bytes:121613584,sha256:'ccacb2d6d87ba6d118b2bffc1ae33747a05cc5fc6b1f1ec4fc1d420b687e952d'};
const WORKER={path:path.join(HERE,'worker-schemas.json'),bytes:101686,sha256:'f6578bba812f4859e853c34c95ce1f4dad6f2363af6bf6b899b4d5684fbe74f5'};
const AUTHORS=['/root','/root/recovery_fixture_parent','/root/negative_io_implementer','/root/negative_outer_implementer','/root/negative_lane_architect'];
function need(ok,code){if(!ok)throw Object.assign(Error(code),{code});}
function same(a,b){if(typeof a!==typeof b||a===null||b===null)return a===b;if(Array.isArray(a)||Array.isArray(b))return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>same(v,b[i]));if(typeof a==='object')return Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));return Object.is(a,b);}
function hash(bytes){return createHash('sha256').update(bytes).digest('hex');}
function descriptor(p){need(typeof p==='string'&&path.isAbsolute(p)&&fs.realpathSync(p)===p,'CANONICAL_FILE');const st=fs.lstatSync(p);need(st.isFile()&&!st.isSymbolicLink(),'REGULAR_FILE');const fd=fs.openSync(p,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW),buf=Buffer.alloc(1048576),h=createHash('sha256');let size=0;try{for(;;){const n=fs.readSync(fd,buf,0,buf.length,null);if(!n)break;size+=n;h.update(buf.subarray(0,n));}}finally{fs.closeSync(fd);}return {path:p,bytes:size,sha256:h.digest('hex')};}
function read(d){need(same(Object.keys(d).sort(),['bytes','path','sha256'])&&same(descriptor(d.path),d)&&d.bytes<=33554432,'PIN_OR_DATA_BOUND');const bytes=fs.readFileSync(d.path);need(bytes.length===d.bytes&&hash(bytes)===d.sha256,'INPUT_READ_CHANGED');return parse(bytes);}
function parse(raw,limit=33554432,historicalNative=false){
 need(Buffer.isBuffer(raw)&&raw.length<=limit,'JSON_BOUND');const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(raw);let i=0,nodes=0;
 const ws=()=>{while(i<text.length&&/[\x20\t\r\n]/.test(text[i]))i++;};
 function str(){const start=i;need(text[i++]==='"','JSON_STRING');while(i<text.length){const c=text.charCodeAt(i++);if(c===34){const s=JSON.parse(text.slice(start,i));for(let j=0;j<s.length;j++){const x=s.charCodeAt(j);if(x>=0xd800&&x<=0xdbff){const y=s.charCodeAt(++j);need(y>=0xdc00&&y<=0xdfff,'UNICODE_SCALAR');}else need(x<0xdc00||x>0xdfff,'UNICODE_SCALAR');}return s;}need(c>=32,'JSON_STRING');if(c===92){const e=text[i++];if(e==='u'){need(/^[0-9a-fA-F]{4}$/.test(text.slice(i,i+4)),'JSON_ESCAPE');i+=4;}else need('"\\/bfnrt'.includes(e),'JSON_ESCAPE');}}need(false,'JSON_STRING');}
 function val(depth=0){need(depth<=64&&++nodes<=100000,'JSON_STRUCTURE');ws();let v;const c=text[i];if(c==='"')v=str();else if(c==='{'){i++;v=Object.create(null);ws();if(text[i]!=='}')for(;;){ws();const k=str();need(!Object.hasOwn(v,k),'DUPLICATE_KEY');ws();need(text[i++]===':','JSON_COLON');v[k]=val(depth+1);ws();if(text[i]!==',')break;i++;}need(text[i++]==='}','JSON_OBJECT');}else if(c==='['){i++;v=[];ws();if(text[i]!==']')for(;;){v.push(val(depth+1));ws();if(text[i]!==',')break;i++;}need(text[i++]===']','JSON_ARRAY');}else if(text.startsWith('true',i)){i+=4;v=true;}else if(text.startsWith('false',i)){i+=5;v=false;}else if(text.startsWith('null',i)){i+=4;v=null;}else{const m=(historicalNative?/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/:/^-?(?:0|[1-9][0-9]*)/).exec(text.slice(i));need(m&&m[0]!=='-0','JSON_INTEGER');i+=m[0].length;v=Number(m[0]);need(historicalNative?Number.isFinite(v)&&(!Number.isInteger(v)||Number.isSafeInteger(v)):Number.isSafeInteger(v),'SAFE_INTEGER');}return v;}
 const v=val();ws();need(i===text.length,'JSON_TRAILING');return v;
}

function bootstrap(framePath,externalSHA){
 need(process.execPath===NODE.path&&same(descriptor(process.execPath),NODE),'NODE_EXECUTABLE');
 const fd=descriptor(framePath);need(fd.bytes<=1048576&&fd.sha256===externalSHA,'EXTERNAL_FRAME_SHA');const f=read(fd);need(same(Object.keys(f).sort(),['cellId','lane','manifest','output','release','schema','windowId','workerData']),'CLOSED_FRAME');need(f.schema==='n02316-case-private-frame-v1'&&f.lane==='LAB-N-02-03-16','N_FRAME_ONLY');
 const m=read(f.manifest),r=read(f.release);need(m.schema==='n02316-exact-manifest-v1'&&r.schema==='n02316-root-exact-release-v1'&&r.decision==='RELEASE_EXACT_N02316_RUN_ONLY'&&r.rootSession==='/root'&&same(r.manifest,f.manifest)&&same(r.sourceReviews,m.sourceReviews)&&same(r.controlAcceptance,m.controlAcceptance)&&same(r.configurationAcceptance,m.configurationAcceptance),'ROOT_RELEASE_BINDING');
 need(Array.isArray(m.sourceClosure)&&m.sourceClosure.length>0&&m.sourceClosure.length<=1024,'FINITE_SOURCE_CLOSURE');const map=new Map();for(const d of m.sourceClosure){need(!map.has(d.path)&&same(descriptor(d.path),d),'CURRENT_SOURCE_PIN');map.set(d.path,d);}for(const name of ['case.mjs','protocol.mjs'])need(same(map.get(path.join(HERE,name)),descriptor(path.join(HERE,name))),'SOURCE_ENTRY_MEMBER');need(same(map.get(WORKER.path),WORKER),'FIXED_PROJECTED_SCHEMA');
 const s=read(m.sourceReviews);need(s.schema==='n02316-source-approval-v1'&&s.decision==='ACCEPT_SOURCE_ONLY'&&same(s.sourceClosure,m.sourceClosure)&&AUTHORS.every(a=>s.authors.includes(a)),'REVIEWED_SOURCE_CLOSURE');need(s.reviews.length===2&&new Set(s.reviews.map(v=>v.session)).size===2&&same(s.reviews.map(v=>v.role).sort(),['qa','security']),'SOURCE_REVIEW_ROLES');for(const review of s.reviews)need(review.decision==='ACCEPT_SOURCE_ONLY'&&!s.authors.includes(review.session)&&!AUTHORS.includes(review.session)&&same(read(review.subject),m.sourceClosure),'SOURCE_REVIEW_SUBJECT');
 // The source-reviewed protocol repeats complete projected-schema/root/control/
 // configuration/native qualification/current prerequisite admission BEFORE any IO import.
 return {frame:fd,protocol:map.get(path.join(HERE,'protocol.mjs'))};
}
function diagnostic(error){try{const raw=Buffer.from(JSON.stringify({qualified:false,name:String(error?.name??'Error'),message:String(error?.message??error),code:typeof error?.code==='string'?error.code:null,stack:typeof error?.stack==='string'?error.stack:null}));const bytes=raw.length<=65535?Buffer.concat([raw,Buffer.from('\n')]):Buffer.from(JSON.stringify({qualified:false,complete:false,utf8PrefixHex:raw.subarray(0,16000).toString('hex')})+'\n');fs.writeSync(2,bytes);}catch{}}
async function main(){
 let ctx=null,api=null,boundary='admission';
 try{
  need(process.argv.length===4&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url),'FIXED_CASE_CLI');const [framePath,sha]=process.argv.slice(2);need(path.isAbsolute(framePath)&&/^[0-9a-f]{64}$/.test(sha),'ABS_FRAME_EXTERNAL_SHA');const admitted=bootstrap(framePath,sha);
  need(same(descriptor(admitted.protocol.path),admitted.protocol),'PREIMPORT_PROTOCOL_PIN');api=await import(pathToFileURL(admitted.protocol.path).href);need(same(descriptor(admitted.protocol.path),admitted.protocol),'POSTIMPORT_PROTOCOL_PIN');ctx=await api.loadCaseContext(framePath,sha);
  if(ctx.subprofile==='N02'){boundary='relay';const f=await api.runOwnedWire(ctx,'F');boundary='metadata';await api.startNative(ctx);await api.authenticateFOnly(ctx,f);boundary='lifecycle';await api.closeNativeForNegative(ctx);}
  else if(ctx.subprofile==='N03'){boundary='relay';await api.runOwnedWire(ctx,'D');}
  else if(ctx.subprofile==='N16'){boundary='relay';const d=await api.runOwnedWire(ctx,'D'),f=await api.runOwnedWire(ctx,'F');boundary='metadata';await api.startNative(ctx);const auth=await api.authenticatePair(ctx,d,f);boundary='policy';const deny=await api.recordLocalDeny(ctx,auth);await api.attemptSealRefusal(ctx,auth,deny);boundary='lifecycle';await api.closeNativeForNegative(ctx);}
  else throw Error('CLOSED_NEGATIVE_SCHEDULE');
  boundary='cleanup';await api.closeoutNoSeal(ctx);
 }catch(error){if(ctx===null){diagnostic(error);return 2;}try{await api.retainFailure(ctx,error,boundary);}catch(capture){diagnostic(error);diagnostic(capture);return 1;}}
 try{return await api.writeCaseReply(ctx)?0:1;}catch(error){diagnostic(error);return 1;}
}
process.exitCode=await main();
