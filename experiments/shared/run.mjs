import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { platform, release, arch, cpus } from 'node:os';
import { Evidence, digest } from './evidence.mjs';
const id=process.argv[2];const dirs={E01:'e01-envelope',E02:'e02-validation',E03:'e03-discovery',E04:'e04-frame-limits',E05:'e05-attachment-crypto',E06:'e06-kind15'};
if(!dirs[id])throw Error('Use canonical E01–E06');
const start=Date.now(),ev=new Evidence(id);
const deps={E02:['E01'],E03:['E01'],E04:['E01','E02'],E06:['E01','E02','E05']};
let blocked=false;
for(const d of deps[id]??[]){const path='results/'+d+'.json';const record=existsSync(path)?JSON.parse(readFileSync(path)):null;const stale=record&&Object.entries(record.source_sha256??{}).some(([p,h])=>!existsSync(p)||digest(readFileSync(p))!==h);if(!record||record.status!=='PASS'||stale){ev.skip('entire experiment','Prerequisite '+d+' missing, not PASS, or source hashes stale');blocked=true;}}
if(!blocked){try{const module=await import('../'+dirs[id]+'/test.mjs');await module.execute(ev);}catch(e){if(['ENOENT','EPERM','EACCES','ECONNREFUSED','EADDRINUSE'].includes(e.code)||/Executable doesn't exist/.test(e.message))ev.skip('environment/execution',e.stack);else await ev.check('unexpected execution exception',async()=>{throw e;});}}
const result=ev.finish();let chrome;try{chrome=execFileSync(process.env.NBDP_CHROME??'/usr/bin/google-chrome',['--version'],{encoding:'utf8'}).trim()}catch{chrome='unavailable'}
const sourceFiles=['fixtures/nip44.vectors.json','package.json','shared/rust/Cargo.toml','shared/rust/rust-toolchain.toml','docker/strfry.conf','docker/rs-relay.toml',...(id==='E05'?['results/producer-profile-evidence.md']:[]),...(id==='E06'?['fixtures/generated/E05-aes-gcm-vectors.json']:[]),'shared/run.mjs','shared/evidence.mjs','shared/rust-client.mjs','shared/attachment-crypto.mjs','shared/correlation.mjs','shared/discovery.mjs','shared/relay.mjs','shared/transport.mjs','shared/rust/src/main.rs','shared/candidate-profile.md',dirs[id]+'/test.mjs','package-lock.json','shared/rust/Cargo.lock'];
const hashes=Object.fromEntries(sourceFiles.filter(existsSync).map(p=>[p,digest(readFileSync(p))]));
Object.assign(result,{started_at:new Date(start).toISOString(),duration_ms:Date.now()-start,command:process.argv.join(' '),exit_status:result.status==='FAIL'?1:result.status==='NOT EXECUTED'?2:0,environment:{node:process.version,openssl:process.versions.openssl,chrome,os:platform(),release:release(),arch:arch(),cpu:cpus()[0].model,resource_usage:process.resourceUsage(),memory:process.memoryUsage(),rust_binary_sha256:existsSync(process.env.NBDP_RUST_BIN??'shared/rust/target/debug/nbdp-experiment-rust')?digest(readFileSync(process.env.NBDP_RUST_BIN??'shared/rust/target/debug/nbdp-experiment-rust')):'unavailable',rust_binary:process.env.NBDP_RUST_BIN??'shared/rust/target/debug/nbdp-experiment-rust'},source_sha256:hashes});
mkdirSync('results',{recursive:true});writeFileSync('results/'+id+'.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({id,status:result.status,tests:result.tests.length,failed:result.tests.filter(t=>!t.ok).map(t=>({name:t.name,error:t.error})),skipped:result.skipped,duration_ms:result.duration_ms},null,2));
process.exitCode=result.exit_status;
