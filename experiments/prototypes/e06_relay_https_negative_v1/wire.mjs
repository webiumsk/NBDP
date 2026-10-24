// SOURCE IMPLEMENTATION ONLY. No control/configuration/runtime release is supplied here.
// Fixed LAB-N-02-03-16 helper. JSON evidence never authenticates a protocol capability.
import {writeFileSync, statSync, realpathSync, lstatSync, readdirSync, writeSync, openSync, readSync, closeSync, fstatSync, fsyncSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';
const ROOT = '/home/peterhorvath/apps/bitcoin/NBDP';
const HERE = ROOT+'/experiments/prototypes/e06_relay_https_negative_v1';
const WS_ENTRY = ROOT+'/experiments/node_modules/ws/wrapper.mjs';
const NODE = '/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node';
const NODE_PIN = {bytes:121613584,sha256:'ccacb2d6d87ba6d118b2bffc1ae33747a05cc5fc6b1f1ec4fc1d420b687e952d'};
const ENDPOINTS = Object.freeze({strfry:'ws://127.0.0.1:17777','rs-relay':'ws://127.0.0.1:18081'});
const ENV = Object.freeze({PATH:'/usr/bin:/bin',LANG:'C.UTF-8',LC_ALL:'C.UTF-8',TZ:'UTC',WS_NO_BUFFER_UTIL:'1',WS_NO_UTF_8_VALIDATE:'1'});
const MAX_FRAME = 262144, MAX_FRAMES = 16, MAX_RAW = 2097152;
const assert = (ok, message) => {if (!ok) throw Error(message);};
const keys = (value, names) => value!==null && typeof value==='object' && !Array.isArray(value)
  && Object.keys(value).length===names.length && names.every(k=>Object.hasOwn(value,k));
const hash = b => createHash('sha256').update(b).digest('hex');
const pin = file => {
  absoluteFile(file);const fd=openSync(file,'r');let size=0;const digest=createHash('sha256');
  try {const before=fstatSync(fd,{bigint:true}),chunk=Buffer.alloc(1048576);assert(before.isFile(),'Regular source required');
    for(;;){const count=readSync(fd,chunk,0,chunk.length,null);if(!count)break;size+=count;assert(Number.isSafeInteger(size),'Source byte bound');digest.update(chunk.subarray(0,count));}
    const after=fstatSync(fd,{bigint:true});assert(before.dev===after.dev&&before.ino===after.ino&&before.size===after.size&&BigInt(size)===before.size&&before.mtimeNs===after.mtimeNs&&before.ctimeNs===after.ctimeNs,'Source changed while hashing');
  }finally{closeSync(fd);}return {bytes:size,sha256:digest.digest('hex')};
};
const samePin = (a,b) => keys(a,['bytes','sha256']) && keys(b,['bytes','sha256'])
  && a.bytes===b.bytes && a.sha256===b.sha256;

export function typedEqual(a,b) {
  if (typeof a!==typeof b || (a===null)!==(b===null) || Array.isArray(a)!==Array.isArray(b)) return false;
  if (a===null || typeof a!=='object') return Object.is(a,b);
  if (Array.isArray(a)) return a.length===b.length && a.every((v,i)=>typedEqual(v,b[i]));
  return Object.keys(a).length===Object.keys(b).length
    && Object.keys(a).every(k=>Object.hasOwn(b,k)&&typedEqual(a[k],b[k]));
}

function scalar(s) {
  for(let i=0;i<s.length;i++) {
    const c=s.charCodeAt(i);
    if(c>=0xd800&&c<=0xdbff) {const d=s.charCodeAt(++i);assert(d>=0xdc00&&d<=0xdfff,'Unpaired high surrogate');}
    else assert(!(c>=0xdc00&&c<=0xdfff),'Unpaired low surrogate');
  }
  return s;
}

// Inert strict JSON parser. Spans are UTF-8 byte offsets, including nested objects.
// Numeric grammar intentionally admits decimal safe integers only, without -0.
export function parseStrict(raw, limit=MAX_RAW) {
  assert(Buffer.isBuffer(raw)||raw instanceof Uint8Array,'Raw bytes required');
  const bytes=Buffer.from(raw);assert(bytes.length<=limit,'JSON byte bound');
  const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
  let i=0,nodes=0;
  const white=()=>{while(i<text.length&&/[\x20\x09\x0a\x0d]/.test(text[i]))i++;};
  const offsets=new Uint32Array(text.length+1);let byteOffset=0;
  for(let j=0;j<text.length;j++){offsets[j]=byteOffset;const c=text.codePointAt(j);if(c>0xffff){offsets[++j]=byteOffset;byteOffset+=4;}else byteOffset+=c<0x80?1:c<0x800?2:3;}
  offsets[text.length]=byteOffset;const position=x=>offsets[x];
  function string() {
    const start=i;assert(text[i++]==='"','Expected string');
    while(i<text.length) {
      const c=text.charCodeAt(i++);
      if(c===34)return scalar(JSON.parse(text.slice(start,i)));
      assert(c>=32,'Control in string');
      if(c===92) {
        assert(i<text.length,'Incomplete escape');const e=text[i++];
        if(e==='u') {assert(/^[0-9a-fA-F]{4}$/.test(text.slice(i,i+4)),'Invalid Unicode escape');i+=4;}
        else assert('"\\/bfnrt'.includes(e),'Invalid escape');
      }
    }
    throw Error('Unterminated string');
  }
  function value(depth=0) {
    assert(depth<=64&&++nodes<=100000,'JSON structural bound');white();const start=i;let result,children=null;
    const c=text[i];
    if(c==='"')result=string();
    else if(c==='[') {
      i++;result=[];children=[];white();
      if(text[i]!==']')while(true) {
        const child=value(depth+1);result.push(child.value);children.push(child);white();
        if(text[i]!==',')break;i++;
      }
      assert(text[i++ ]===']','Invalid array');
    } else if(c==='{') {
      i++;result=Object.create(null);children=Object.create(null);white();
      if(text[i]!=='}')while(true) {
        white();const key=string();assert(!Object.hasOwn(result,key),'Duplicate object key');white();
        assert(text[i++]===':','Missing colon');const child=value(depth+1);result[key]=child.value;children[key]=child;white();
        if(text[i]!==',')break;i++;
      }
      assert(text[i++]==='}','Invalid object');
    } else if(text.startsWith('true',i)){result=true;i+=4;}
    else if(text.startsWith('false',i)){result=false;i+=5;}
    else if(text.startsWith('null',i)){result=null;i+=4;}
    else {
      const match=/^-?(?:0|[1-9][0-9]*)/.exec(text.slice(i));assert(match,'Invalid JSON value');
      i+=match[0].length;result=Number(match[0]);
      assert(match[0]!=='-0'&&Number.isSafeInteger(result),'Unsupported integer');
    }
    return {value:result,start:position(start),end:position(i),children};
  }
  const root=value();white();assert(i===text.length,'Trailing JSON content');
  return {value:root.value,spans:root,raw:bytes};
}

export function validateAck(raw,id) {
  const a=parseStrict(raw,MAX_FRAME).value;
  assert(Array.isArray(a)&&a.length===4&&a[0]==='OK'&&a[1]===id&&a[2]===true&&typeof a[3]==='string','Exact OK true required');return a;
}
export function validateEose(raw,sub) {
  const a=parseStrict(raw,MAX_FRAME).value;
  assert(Array.isArray(a)&&a.length===2&&a[0]==='EOSE'&&a[1]===sub,'Exact EOSE required');return a;
}
export function validateEventFrame(raw,sub,fixture) {
  const parsed=parseStrict(raw,MAX_FRAME),a=parsed.value;
  assert(Array.isArray(a)&&a.length===3&&a[0]==='EVENT'&&a[1]===sub,'Exact EVENT frame required');
  assert(typedEqual(a[2],fixture),'Whole EVENT mismatch');
  const span=parsed.spans.children[2];
  assert(span.value!==null&&typeof span.value==='object'&&!Array.isArray(span.value),'EVENT object required');
  return {event:a[2],wireHex:parsed.raw.subarray(span.start,span.end).toString('hex')};
}
export function validateClose(code,reason) {
  assert(code===1000,'Strict Close1000 required');
  assert(Buffer.isBuffer(reason)||reason instanceof Uint8Array,'Raw close reason required');
  return {code,reason:scalar(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(reason))};
}

// The same pure state machine is used by callbacks and refusal controls.
export function createProtocolState(id,sub,fixture) {
  let phase='OPEN',wireHex=null,eventCount=0,publicationCount=0,queryCount=0;
  return {
    sent(kind) {
      if(kind==='EVENT'){assert(phase==='OPEN','Premature EVENT publication');phase='ACK';publicationCount++;}
      else if(kind==='REQ'){assert(phase==='ACK_RETAINED','REQ before ACK');phase='EVENT';queryCount++;}
      else if(kind==='CLOSE'){assert(phase==='EOSE_RETAINED','CLOSE before EOSE');phase='CLOSING';}
      else throw Error('Unknown send kind');
    },
    received(raw,binary=false) {
      assert(!binary,'Binary payload refused');
      if(phase==='ACK'){validateAck(raw,id);phase='ACK_RETAINED';return 'OK';}
      if(phase==='EVENT'){const event=validateEventFrame(raw,sub,fixture);wireHex=event.wireHex;eventCount++;phase='EOSE';return 'EVENT';}
      if(phase==='EOSE'){validateEose(raw,sub);phase='EOSE_RETAINED';return 'EOSE';}
      throw Error('Unexpected or premature relay payload in '+phase);
    },
    closed(code,reason) {assert(phase==='CLOSING','Premature socket close');const close=validateClose(code,reason);phase='CLOSED';return close;},
    snapshot() {return {phase,wireHex,eventCount,publicationCount,queryCount};}
  };
}

// All exports below are inert on import. Only fixed builtins are loaded before admission.
export function absoluteFile(file) {
  assert(typeof file==='string'&&path.isAbsolute(file)&&realpathSync(file)===file&&!lstatSync(file).isSymbolicLink()&&statSync(file).isFile(),'Resolved regular absolute file required');
}
export function readBounded(file,limit=1048576) {
  assert(Number.isSafeInteger(limit)&&limit>=0&&limit<=33554432,'Finite data read bound');absoluteFile(file);
  const fd=openSync(file,'r');try {
    const before=fstatSync(fd,{bigint:true});assert(before.size<=BigInt(limit),'Bounded data size');
    const buffer=Buffer.alloc(Number(before.size)+1);let offset=0;
    while(offset<buffer.length){const count=readSync(fd,buffer,offset,buffer.length-offset,null);if(!count)break;offset+=count;}
    const after=fstatSync(fd,{bigint:true});
    assert(BigInt(offset)===before.size&&before.dev===after.dev&&before.ino===after.ino&&before.size===after.size
      &&before.mtimeNs===after.mtimeNs&&before.ctimeNs===after.ctimeNs,'Bounded data changed during read');
    return buffer.subarray(0,offset);
  }finally{closeSync(fd);}
}
export function privateDir(dir) {
  assert(path.isAbsolute(dir)&&realpathSync(dir)===dir,'Resolved absolute directory required');
  const s=statSync(dir);assert(s.isDirectory()&&(s.mode&0o777)===0o700&&s.uid===process.getuid(),'Owned mode0700 directory required');
}
export function checkDescriptor(d) {
  assert(keys(d,['path','bytes','sha256'])&&Number.isSafeInteger(d.bytes)&&d.bytes>=0&&/^[a-f0-9]{64}$/.test(d.sha256),'Closed descriptor required');
  absoluteFile(d.path);assert(samePin(pin(d.path),{bytes:d.bytes,sha256:d.sha256}),'Descriptor bytes changed');return d;
}
export function validateShape(value, shape, definitions, depth=0) {
  assert(depth<=128,'Schema recursion bound');
  const next=(v,s)=>validateShape(v,s,definitions,depth+1);
  if(typeof shape==='string') {
    if(shape.startsWith('@')) {assert(Object.hasOwn(definitions,shape.slice(1)),'Unknown schema reference');return next(value,definitions[shape.slice(1)]);}
    assert(shape==='null'?value===null:shape==='boolean'?typeof value==='boolean':false,'Unsupported primitive or wrong type');return true;
  }
  if(Object.hasOwn(shape,'union')) {for(const s of shape.union)try{next(value,s);return true;}catch{}throw Error('No schema union arm');}
  if(Object.hasOwn(shape,'literal'))assert(typedEqual(value,shape.literal),'Literal mismatch');
  else if(Object.hasOwn(shape,'enum'))assert(shape.enum.some(v=>typedEqual(value,v)),'Enum mismatch');
  else if(Object.hasOwn(shape,'record')) {assert(keys(value,Object.keys(shape.record)),'Closed record keys');for(const [k,s]of Object.entries(shape.record))next(value[k],s);}
  else if(Object.hasOwn(shape,'array')) {assert(Array.isArray(value)&&value.length>=shape.length[0]&&value.length<=shape.length[1],'Bounded array');for(const v of value)next(v,shape.array);}
  else if(Object.hasOwn(shape,'tuple')) {assert(Array.isArray(value)&&value.length===shape.tuple.length,'Tuple arity');shape.tuple.forEach((s,i)=>next(value[i],s));}
  else if(Object.hasOwn(shape,'integer'))assert(Number.isSafeInteger(value)&&!Object.is(value,-0)&&value>=shape.integer[0]&&value<=shape.integer[1],'Safe integer range');
  else if(Object.hasOwn(shape,'stringMax')||Object.hasOwn(shape,'pattern')) {
    assert(typeof value==='string','String required');scalar(value);
    if(Object.hasOwn(shape,'stringMax'))assert(Buffer.byteLength(value,'utf8')<=shape.stringMax,'String byte bound');
    if(Object.hasOwn(shape,'pattern'))assert(new RegExp(shape.pattern,'u').test(value),'String pattern');
  } else throw Error('Unsupported schema grammar');
  return true;
}
const FROZEN_DATA = Object.freeze({"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/SOURCE.md":{"bytes":5474,"sha256":"ac2a85391e583a995950d248cf2af3c8bfefbda363c35e9a51139473885813cc"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/contract.json":{"bytes":22787,"sha256":"5208c3bbfd1dea75577c90c0bdea49b9410ac4163e09ca5d09af8d7702196d13"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/interfaces.md":{"bytes":14702,"sha256":"c04ae8e852b096403c865a6daf22c45eed071dc5248035cea0954762da925af7"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/profile.json":{"bytes":4442,"sha256":"c7167a764d562e6878b8ba35535c8938c4c04a836bd25cea1aeb396f9e8d9bae"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/selection-map.json":{"bytes":32883,"sha256":"d66ec8cf79b9d572eb0268a307ed782047a9cb897a65de83b6b00f430fa6cf09"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/native-oracles.json":{"bytes":27629,"sha256":"12a508cc4060ad920ebcba0aeb0c23f5b7de7c311aaeec575cb4bf5f0ad28a2a"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/NATIVE_ORACLES.md":{"bytes":18655,"sha256":"69388bb061a87bd3bc938154556228fffc9157cca7bb32a67ad8d2e75c0d00a6"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/bridge-schemas.json":{"bytes":158719,"sha256":"89173066418eddd16f1d2a14ecee4b04470072385c1883aab48a01dd6e41281a"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/worker-schemas.json":{"bytes":101686,"sha256":"f6578bba812f4859e853c34c95ce1f4dad6f2363af6bf6b899b4d5684fbe74f5"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/oracles.json":{"bytes":105615,"sha256":"317047707f19f429791b2a3cec730550c18427bb58c25cfcaa0702edf290c0cd"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/protected-deltas.json":{"bytes":12189,"sha256":"70846060c58d5ff5f11ab930a9a0fcd2013a3f69e7c420a2e2bdd358aee24d99"},"/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/BRIDGE.md":{"bytes":16984,"sha256":"1f363f50d5e41413b05e4bb862e8eb53b7288ab8a205000287d69862af5049e7"}});
export function verifyClosure(closure, required=[]) {
  assert(Array.isArray(closure)&&closure.length>=1&&closure.length<=2048,'Finite closure required');const map=new Map();
  for(const d of closure){checkDescriptor(d);assert(!map.has(d.path),'Duplicate/aliased closure path');map.set(d.path,d);}
  for(const [p,d] of Object.entries(FROZEN_DATA))assert(map.has(p)&&samePin(pin(p),d)&&samePin({bytes:map.get(p).bytes,sha256:map.get(p).sha256},d),'Frozen N planning input absent/changed');
  assert(typedEqual(process.env,ENV),'Closed six-variable environment required');
  assert(realpathSync(process.execPath)===NODE&&samePin(pin(NODE),NODE_PIN),'Fixed Node binary required');
  for(const p of [NODE,...required])assert(map.has(p),'Required current runtime absent from closure');
  assert(samePin({bytes:map.get(NODE).bytes,sha256:map.get(NODE).sha256},NODE_PIN),'Fixed Node closure pin');
  return map;
}
export function fixedData() {
  for(const [p,d]of Object.entries(FROZEN_DATA)){absoluteFile(p);assert(samePin(pin(p),d),'Frozen N data changed');}
  const selection=parseStrict(readBounded(HERE+'/selection-map.json')).value;
  const schemas=parseStrict(readBounded(HERE+'/worker-schemas.json')).value;
  return {selection,definitions:schemas.definitions,nativeShapes:schemas.selectedCellNativeShapes};
}
export function selectedCell(selection,cellId) {
  assert(Array.isArray(selection.cells)&&Array.isArray(selection.orderedCells),'Closed N selection required');
  const cells=selection.cells.filter(x=>x.cellId===cellId);
  assert(cells.length===1&&selection.orderedCells.includes(cellId),'Unsupported N lane/cell');return cells[0];
}
export function readBinding(bindingPath,sha,kind) {
  absoluteFile(bindingPath);privateDir(path.dirname(bindingPath));
  const s=statSync(bindingPath);assert(s.uid===process.getuid()&&(s.mode&0o777)===0o600,'Owned mode0600 binding required');
  assert(/^[a-f0-9]{64}$/.test(sha)&&s.size<=1048576&&pin(bindingPath).sha256===sha,'External bounded binding SHA');
  const raw=readBounded(bindingPath),binding=parseStrict(raw,1048576).value;
  const {selection,definitions,nativeShapes}=fixedData();
  assert(['wireBinding','nativeBinding'].includes(kind),'Fixed target binding kind required');
  validateShape(binding,'@'+kind,definitions);return {binding,selection,definitions,nativeShapes};
}
export function writeOneLine(value) {
  const b=Buffer.from(JSON.stringify(value)+'\n');assert(b.length<=16777216,'Reply byte bound');
  let offset=0;while(offset<b.length){const count=writeSync(1,b,offset,b.length-offset);assert(count>0,'Complete synchronous reply required');offset+=count;}
}
function validateBinding(binding,selection) {
  const w=selectedCell(selection,binding.cellId),job=w.jobs.find(j=>j.slot===binding.slot);
  assert(binding.windowId===w.windowId&&binding.relay===w.relay&&job&&typedEqual(binding.wire,job.wire),'Exact N slot/relay/fixture required');
  checkDescriptor(binding.wire);const fixture=parseStrict(readBounded(binding.wire.path,MAX_FRAME),MAX_FRAME).value;
  assert(fixture.id===binding.outerId&&fixture.kind===1059,'Fixed signed outer ID/kind');
  const map=verifyClosure(binding.closure,[fileURLToPath(import.meta.url),WS_ENTRY,binding.wire.path]);
  assert(typedEqual(map.get(binding.wire.path),binding.wire),'Wire descriptor absent from closure');
  privateDir(binding.output);assert(readdirSync(binding.output).length===0,'Fresh empty owned output required');return fixture;
}
async function main() {
  assert(process.argv.length===4,'CLI: node wire.mjs ABS_BINDING SHA256');
  const [bindingPath,sha]=process.argv.slice(2);
  const {binding,selection,definitions}=readBinding(bindingPath,sha,'wireBinding');
  // Parent owns release admission and complete exact closure. This child rechecks all supplied bytes before dependent import.
  const fixture=validateBinding(binding,selection),self=fileURLToPath(import.meta.url);
  const verify=()=>{
    assert(pin(bindingPath).sha256===sha,'Binding changed');
    verifyClosure(binding.closure,[self,WS_ENTRY,binding.wire.path]);privateDir(binding.output);
  };
  const report={schema:'n02316-wire-report-v1',cellId:binding.cellId,slot:binding.slot,qualified:false,publicationCount:0,queryCount:0,eventCount:0,wireHex:null,close:null,frames:[],error:null};
  let ws=null,terminal=null,wake=null,totalBytes=0,closed=false;
  const sub='nbdp-'+binding.cellId+'-'+binding.slot;
  const state=createProtocolState(binding.outerId,sub,fixture);
  const signal=()=>{if(wake){const fn=wake;wake=null;fn();}};
  const fail=error=>{terminal??=error;signal();if(ws&&!closed)ws.terminate();};
  const capture=(direction,raw,kind)=>{
    const remaining=Math.max(0,MAX_RAW-totalBytes);
    if(report.frames.length>=MAX_FRAMES)throw Error('Frame count bound');
    report.frames.push({direction,kind:raw.length>remaining?'BOUND_EXCEEDED_PREFIX':kind,rawHex:raw.subarray(0,remaining).toString('hex')});
    totalBytes+=Math.min(raw.length,remaining);
    assert(raw.length<=MAX_FRAME&&raw.length<=remaining,'Raw stream bound');
  };
  const waitFor=async(predicate,ms,label)=>{
    const deadline=Date.now()+ms;
    while(!predicate()) {
      if(terminal)throw terminal;const remaining=deadline-Date.now();assert(remaining>0,label+' deadline');
      await new Promise(resolve=>{const timer=setTimeout(()=>{wake=null;resolve();},remaining);wake=()=>{clearTimeout(timer);resolve();};});
    }
    if(terminal)throw terminal;
  };
  const send=(kind,raw)=>{
    assert(!terminal&&ws.readyState===1,'Socket not available');state.sent(kind);capture('SEND',raw,kind);ws.send(raw,{binary:false});
  };
  try {
    verify();const {default:WebSocket}=await import(pathToFileURL(WS_ENTRY).href);verify();
    ws=new WebSocket(ENDPOINTS[binding.relay],{handshakeTimeout:3000,maxPayload:MAX_FRAME,followRedirects:false,perMessageDeflate:false});
    ws.on('message',(data,binary)=>{
      const raw=Buffer.from(data);
      try {
        capture('RECEIVE',raw,binary?'BINARY':'UNVALIDATED');
        const kind=state.received(raw,binary);report.frames[report.frames.length-1].kind=kind==='OK'?'ACK':kind;signal();
      } catch(error){fail(error);}
    });
    ws.on('error',fail);
    ws.on('close',(code,reason)=>{
      closed=true;
      try {state.closed(code,Buffer.from(reason));report.close={code,reasonHex:Buffer.from(reason).toString('hex')};assert(reason.length===0,'N empty Close1000 reason required');}
      catch(error){terminal??=error;}
      signal();
    });
    ws.on('open',signal);
    await waitFor(()=>ws.readyState===1,3000,'Open');
    // Publication keeps original signed object bytes; no fixture reserialization.
    verify();checkDescriptor(binding.wire);const signed=readBounded(binding.wire.path,MAX_FRAME);
    send('EVENT',Buffer.concat([Buffer.from('["EVENT",'),signed,Buffer.from(']')]));
    await waitFor(()=>state.snapshot().phase==='ACK_RETAINED',3000,'ACK');
    send('REQ',Buffer.from(JSON.stringify(['REQ',sub,{ids:[binding.outerId],limit:1}])));
    // EVENT and EOSE may arrive back-to-back; state retains both without discarding.
    await waitFor(()=>state.snapshot().eventCount===1,3000,'EVENT');
    await waitFor(()=>state.snapshot().phase==='EOSE_RETAINED',3000,'EOSE');
    send('CLOSE',Buffer.from(JSON.stringify(['CLOSE',sub])));ws.close(1000);
    await waitFor(()=>closed,1000,'Close');
    assert(state.snapshot().phase==='CLOSED','Incomplete wire sequence');assert(report.frames.length===6&&typedEqual(report.frames.map(x=>[x.direction,x.kind]),[['SEND','EVENT'],['RECEIVE','ACK'],['SEND','REQ'],['RECEIVE','EVENT'],['RECEIVE','EOSE'],['SEND','CLOSE']]),'Exact six-frame transcript required');verify();report.qualified=true;
  } catch(error){report.error=(error.name+': '+error.message).slice(0,16000);}
  finally {
    if(ws&&!closed)ws.terminate();
    const s=state.snapshot();for(const k of ['publicationCount','queryCount','eventCount','wireHex'])report[k]=s[k];
    try{verify();}catch(error){report.qualified=false;report.error??=error.name+': '+error.message;}
    assert(report.publicationCount===1||!report.qualified,'Incomplete publication count');
    assert(report.queryCount===1&&report.eventCount===1||!report.qualified,'Incomplete retrieval count');
    validateShape(report,'@wireReport',definitions);
    const fd=openSync(path.join(binding.output,'report.json'),'wx',0o600);try{writeFileSync(fd,JSON.stringify(report,null,2)+'\n');fsyncSync(fd);}finally{closeSync(fd);}const dir=openSync(binding.output,'r');try{fsyncSync(dir);}finally{closeSync(dir);}
  }
  const reportPath=path.join(binding.output,'report.json');
  const reply={schema:'n02316-wire-cli-reply-v1',cellId:binding.cellId,slot:binding.slot,qualified:report.qualified,report:{path:reportPath,...pin(reportPath)}};
  validateShape(reply,'@wireCLIReply',definitions);writeOneLine(reply);return report.qualified?0:1;
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  main().then(code=>{process.exitCode=code;}).catch(error=>{process.stderr.write(error.name+': '+error.message+'\n');process.exitCode=1;});
}
