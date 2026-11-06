// Closed bounded guard JSON parser. No target/runtime/service on module import.
export function strictGuardJSON(text){
 if(typeof text!=='string'||Buffer.byteLength(text)>2048)throw Error('GUARD_JSON_BOUND');
 let i=0,nodes=0;const fail=()=>{throw Error('GUARD_STRICT_JSON');};
 const ws=()=>{while(i<text.length&&/[\x20\t\r\n]/.test(text[i]))i++;};
 function string(){const start=i;if(text[i++]!=='"')fail();while(i<text.length){const c=text[i++];if(c==='"'){try{return JSON.parse(text.slice(start,i));}catch{fail();}}if(c==='\\'){if(i>=text.length)fail();const e=text[i++];if(e==='u'){if(!/^[0-9a-fA-F]{4}$/.test(text.slice(i,i+4)))fail();i+=4;}else if(!'"\\/bfnrt'.includes(e))fail();}else if(c.charCodeAt(0)<32)fail();}fail();}
 function value(depth=0){if(++nodes>128||depth>8)fail();ws();if(text[i]==='"')return string();if(text[i]==='{'){i++;ws();const o={};if(text[i]==='}'){i++;return o;}while(true){ws();const k=string();if(Object.hasOwn(o,k))fail();ws();if(text[i++]!==':')fail();Object.defineProperty(o,k,{value:value(depth+1),enumerable:true});ws();const c=text[i++];if(c==='}')return o;if(c!==',')fail();}}for(const [s,v] of [['true',true],['false',false],['null',null]])if(text.slice(i,i+s.length)===s){i+=s.length;return v;}fail();}
 const result=value();ws();if(i!==text.length)fail();return result;
}
export const guardHashPattern=/^[0-9a-f]{64}$/;
