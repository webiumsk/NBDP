// Exact existing transport strictJSON extraction; no crypto imports.
const assert=(ok,reason)=>{if(!ok)throw Error(reason);};
export function strictJSON(text) {
  assert(Buffer.byteLength(text)<=2_000_000, 'resource');
  const stack=[];
  // Scan raw JSON strings and container boundaries before parsing; escaped keys compare decoded.
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(c==='"') {
      const start=i++;
      while(i<text.length) { if(text[i]==='\\') {i+=2;continue;} if(text[i]==='"')break;i++; }
      let next=i+1; while(/\s/.test(text[next]??'X')) next++;
      if(text[next]===':') { const frame=stack.at(-1);assert(frame?.type==='{','json');const key=JSON.parse(text.slice(start,i+1));assert(!frame.keys.has(key),'json');frame.keys.add(key); }
    } else if(/[-0-9]/.test(c)){let end=i+1;while(end<text.length&&!/[\s,}\]]/.test(text[end]))end++;assert(/^(0|[1-9][0-9]*|-[1-9][0-9]*)$/.test(text.slice(i,end)),'json');i=end-1;}
    else if(c==='{'||c==='[') { stack.push({type:c,keys:new Set()});assert(stack.length<=32,'json'); }
    else if(c==='}'||c===']') { const f=stack.pop();assert(f?.type===(c==='}'?'{':'['),'json'); }
  }
  assert(stack.length===0,'json');
  try{return JSON.parse(text);}catch{throw Error('json');}
}

export const same=(a,b)=>typeof a===typeof b&&(a===null||b===null?a===b:Array.isArray(a)||Array.isArray(b)?Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>same(x,b[i])):typeof a==='object'?Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>Object.hasOwn(b,k)&&same(a[k],b[k])):a===b);
