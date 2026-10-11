import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
export const digest=x=>createHash('sha256').update(x).digest('hex');
export class Evidence {
  constructor(id){this.id=id;this.tests=[];this.observations=[];this.skipped=[];}
  async check(name,f){const start=performance.now();try{const data=await f();this.tests.push({name,ok:true,duration_ms:performance.now()-start,data});}catch(e){this.tests.push({name,ok:false,duration_ms:performance.now()-start,error:e.stack});}}
  equal(a,b){assert.deepEqual(a,b);}
  truth(x){assert.ok(x);}
  save(name,value){mkdirSync('fixtures/generated',{recursive:true});writeFileSync('fixtures/generated/'+name,JSON.stringify(value,null,2)+'\n');}
  skip(scope,reason,mandatory=true){this.skipped.push({scope,reason,mandatory});}
  finish(){const failures=this.tests.filter(t=>!t.ok);return {experiment:this.id,status:failures.length?'FAIL':this.skipped.some(x=>x.mandatory)?(this.tests.length?'PARTIAL':'NOT EXECUTED'):'PASS',tests:this.tests,observations:this.observations,skipped:this.skipped};}
}
