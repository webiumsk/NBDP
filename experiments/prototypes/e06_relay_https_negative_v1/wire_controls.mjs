// SOURCE IMPLEMENTATION ONLY; controls are NOT EXECUTED or released. Pure parser/equality/state coverage.
// No socket, child process, OS fault, relay or consumer evidence is claimed.
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {parseStrict,typedEqual,validateAck,validateEose,validateEventFrame,validateClose,createProtocolState,validateShape} from './wire.mjs';

export function runPureControls() {
  const rows=[];
  const check=(id,fn)=>{fn();rows.push({id,qualified:true,scope:'PURE_HELPER_ONLY'});};
  const refuses=fn=>assert.throws(fn);
  const bytes=s=>Buffer.from(s,'utf8');
  const fixture={id:'a'.repeat(64),pubkey:'b'.repeat(64),created_at:1,kind:1059,tags:[['p','x'],['q','y']],content:'é',sig:'c'.repeat(128)};
  const sub='nbdp-N02-SF-JS-F';
  const frame=event=>bytes(JSON.stringify(['EVENT',sub,event]));
  check('duplicate-root',()=>refuses(()=>parseStrict(bytes('{"a":1,"a":2}'))));
  check('duplicate-escaped-nested',()=>refuses(()=>parseStrict(bytes('[{"a":{"x":1,"\\u0078":2}}]'))));
  check('invalid-utf8',()=>refuses(()=>parseStrict(Buffer.from([0x22,0xc0,0xaf,0x22]))));
  check('bom-refused',()=>refuses(()=>parseStrict(Buffer.from([0xef,0xbb,0xbf,0x30]))));
  check('surrogate-high',()=>refuses(()=>parseStrict(bytes('"\\ud800"'))));
  check('surrogate-low',()=>refuses(()=>parseStrict(bytes('"\\udc00"'))));
  check('scalar-pair',()=>assert.equal(parseStrict(bytes('"\\ud83d\\ude00"')).value,'😀'));
  check('unsafe-integer',()=>refuses(()=>parseStrict(bytes('9007199254740992'))));
  check('fraction-refused',()=>refuses(()=>parseStrict(bytes('1.0'))));
  check('exponent-refused',()=>refuses(()=>parseStrict(bytes('1e0'))));
  check('negative-zero-refused',()=>refuses(()=>parseStrict(bytes('-0'))));
  check('trailing-json',()=>refuses(()=>parseStrict(bytes('[] true'))));
  check('trailing-comma',()=>refuses(()=>parseStrict(bytes('[1,]'))));
  check('exact-keyset',()=>refuses(()=>validateEventFrame(frame({...fixture,extra:1}),sub,fixture)));
  check('missing-key',()=>{const f={...fixture};delete f.sig;refuses(()=>validateEventFrame(frame(f),sub,fixture));});
  check('wrong-type',()=>refuses(()=>validateEventFrame(frame({...fixture,kind:'1059'}),sub,fixture)));
  check('tag-order',()=>refuses(()=>validateEventFrame(frame({...fixture,tags:[...fixture.tags].reverse()}),sub,fixture)));
  check('object-order',()=>assert(typedEqual(fixture,Object.fromEntries(Object.entries(fixture).reverse()))));
  check('array-order',()=>assert(!typedEqual([1,2],[2,1])));
  check('prototype-key-is-data',()=>assert.equal(parseStrict(bytes('{"__proto__":1}')).value.__proto__,1));
  check('event-frame-extra',()=>refuses(()=>validateEventFrame(bytes(JSON.stringify(['EVENT',sub,fixture,1])),sub,fixture)));
  check('wrong-subscription',()=>refuses(()=>validateEventFrame(frame(fixture),'other',fixture)));
  check('actual-span-not-fixture',()=>{
    const reordered=Object.fromEntries(Object.entries(fixture).reverse());
    const span=JSON.stringify(reordered,null,2).replace('é','\\u00e9');
    const raw=bytes('[ "EVENT", "'+sub+'", \n'+span+' \t]');
    const result=validateEventFrame(raw,sub,fixture);
    assert.equal(result.wireHex,bytes(span).toString('hex'));
    assert.notEqual(result.wireHex,bytes(JSON.stringify(fixture)).toString('hex'));
  });
  check('ack-false',()=>refuses(()=>validateAck(bytes(JSON.stringify(['OK',fixture.id,false,'blocked'])),fixture.id)));
  check('ack-extra',()=>refuses(()=>validateAck(bytes(JSON.stringify(['OK',fixture.id,true,'',0])),fixture.id)));
  check('eose-wrong',()=>refuses(()=>validateEose(bytes('["EOSE","other"]'),sub)));
  check('close1006',()=>refuses(()=>validateClose(1006,Buffer.alloc(0))));
  check('close-invalid-reason',()=>refuses(()=>validateClose(1000,Buffer.from([0xff]))));
  const state=()=>createProtocolState(fixture.id,sub,fixture);
  const ack=bytes(JSON.stringify(['OK',fixture.id,true,'']));
  const eose=bytes(JSON.stringify(['EOSE',sub]));
  check('req-before-ack',()=>refuses(()=>state().sent('REQ')));
  check('event-before-req',()=>{const s=state();s.sent('EVENT');s.received(ack);refuses(()=>s.received(frame(fixture)));});
  check('duplicate-event',()=>{const s=state();s.sent('EVENT');s.received(ack);s.sent('REQ');s.received(frame(fixture));refuses(()=>s.received(frame(fixture)));});
  check('extra-response-after-eose',()=>{const s=state();s.sent('EVENT');s.received(ack);s.sent('REQ');s.received(frame(fixture));s.received(eose);refuses(()=>s.received(eose));});
  check('binary-refused',()=>{const s=state();s.sent('EVENT');refuses(()=>s.received(ack,true));});
  check('premature-close',()=>refuses(()=>state().closed(1000,Buffer.alloc(0))));
  check('whole-sequence',()=>{
    const s=state();s.sent('EVENT');s.received(ack);s.sent('REQ');s.received(frame(fixture));s.received(eose);s.sent('CLOSE');s.closed(1000,Buffer.alloc(0));
    const snapshot=s.snapshot();assert.equal(snapshot.phase,'CLOSED');assert.equal(snapshot.publicationCount,1);assert.equal(snapshot.queryCount,1);assert.equal(snapshot.eventCount,1);
    assert.equal(snapshot.wireHex,bytes(JSON.stringify(fixture)).toString('hex'));
  });
  check('frame-byte-bound',()=>refuses(()=>parseStrict(bytes('"'+'x'.repeat(262144)+'"'),262144)));
  check('frame-count-not-state-shortcut',()=>{const s=state();refuses(()=>s.sent('CLOSE'));});
  check('extra-publication',()=>{const s=state();s.sent('EVENT');refuses(()=>s.sent('EVENT'));});
  check('duplicate-ack',()=>{const s=state();s.sent('EVENT');s.received(ack);refuses(()=>s.received(ack));});
  check('early-eose',()=>{const s=state();s.sent('EVENT');s.received(ack);s.sent('REQ');refuses(()=>s.received(eose));});
  check('closed-no-extra-event',()=>{const s=state();s.sent('EVENT');s.received(ack);s.sent('REQ');s.received(frame(fixture));s.received(eose);s.sent('CLOSE');s.closed(1000,Buffer.alloc(0));refuses(()=>s.received(frame(fixture)));});
  check('span-utf8-offset',()=>{
    const text='{ "content":"😀é", "id":"'+fixture.id+'" }';
    const f=JSON.parse(text),raw=bytes('["EVENT","'+sub+'",'+text+']');
    const parsed=parseStrict(raw),node=parsed.spans.children[2];
    assert.equal(raw.subarray(node.start,node.end).toString('utf8'),text);
    assert.equal(validateEventFrame(raw,sub,f).wireHex,bytes(text).toString('hex'));
  });
  check('closed-schema-extra-key',()=>refuses(()=>validateShape({a:1,b:2},{record:{a:{integer:[0,1]}}},{})));
  check('closed-schema-wrong-integer',()=>refuses(()=>validateShape('1',{integer:[0,1]},{})));
  check('closed-schema-unknown-reference',()=>refuses(()=>validateShape({},'@absent',{})));
  return {schema:'n02316-wire-pure-controls-v1',qualified:true,scope:'PURE_HELPER_ONLY',rows};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  assert.equal(process.argv.length,2,'No arbitrary control arguments');
  process.stdout.write(JSON.stringify(runPureControls())+'\n');
}
