import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { resolve } from 'node:path';
import { readFileSync } from 'node:fs';
export class RustClient {
  constructor(){
    const executable=process.env.NBDP_RUST_BIN??resolve('shared/rust/target/debug/nbdp-experiment-rust');
    this.process=spawn(executable,[],{stdio:['pipe','pipe','inherit']});this.queue=[];
    this.process.on('error',e=>{for(const q of this.queue.splice(0))q.reject(e)});
    this.process.on('exit',code=>{for(const q of this.queue.splice(0))q.reject(Error('Rust process exited '+code))});
    createInterface({input:this.process.stdout}).on('line',line=>{
      const q=this.queue.shift();if(!q)return;const r=JSON.parse(line);q.resolve(r);
    });
    this.ready=this.raw({op:'source'}).then(r=>{if(!r.ok||r.value!==readFileSync('shared/rust/src/main.rs','utf8'))throw Error('Rust source/binary mismatch; rebuild before testing');});
  }
  async raw(q){return await new Promise((resolve,reject)=>{this.queue.push({resolve,reject});this.process.stdin.write(JSON.stringify(q)+'\n')});}
  async call(q){await this.ready;const r=await this.raw(q);if(!r.ok)throw Error(r.error);return r.value;}
  close(){this.process.stdin.end();}
}
