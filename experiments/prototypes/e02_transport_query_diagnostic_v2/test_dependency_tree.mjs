// Prepared guest-inventory DATA controls. Standard fs only; generated optional
// module names are inert text and are never imported/evaluated.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {verifyDependencyTree} from './dependency-tree.mjs';
const cases=[];const test=(name,fn)=>{fn();cases.push(name);};
function fixture(fn){const temp=fs.mkdtempSync(path.join(os.tmpdir(),'nbdp-dependency-data-')),root=path.join(temp,'node_modules');fs.mkdirSync(root);fs.mkdirSync(path.join(root,'ws'));const file=path.join(root,'ws/index.js');fs.writeFileSync(file,'INERT_NOT_IMPORTED');const raw=fs.readFileSync(file);const tree={schema:'e02-transport-dependency-tree-v2',sourceRoot:root,runtimeRoot:'/input/node_modules',directories:['ws'],files:['ws/index.js'],symlinks:[]};const files=[{source:file,path:'/input/node_modules/ws/index.js',bytes:raw.length,sha256:createHash('sha256').update(raw).digest('hex')}];try{fn({temp,root,file,tree,files,verify:()=>verifyDependencyTree(root,tree,files)});}finally{fs.rmSync(temp,{recursive:true});}}
test('complete-unchanged-source-runtime-tree',()=>fixture(f=>assert.equal(f.verify().exact,true)));
test('extra-member-and-nested-bufferutil-rejected-before-import',()=>{
 for(const name of ['extra.js','ws/node_modules/bufferutil/index.js'])fixture(f=>{const p=path.join(f.root,name);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,'INERT_NOT_IMPORTED');assert.throws(f.verify,/DEPENDENCY_EXACT_MEMBERSHIP/);});
});
test('missing-and-changed-file-rejected',()=>{
 fixture(f=>{fs.unlinkSync(f.file);assert.throws(f.verify,/DEPENDENCY_EXACT_MEMBERSHIP/);});
 fixture(f=>{fs.appendFileSync(f.file,'CHANGED');assert.throws(f.verify,/DEPENDENCY_BYTES_DRIFT/);});
});
test('safe-added-escape-and-dangling-symlink-rejected',()=>{
 for(const target of ['ws/index.js','../outside','absent'])fixture(f=>{fs.writeFileSync(path.join(f.temp,'outside'),'OUTSIDE_NEVER_READ');fs.symlinkSync(target,path.join(f.root,'link'));assert.throws(f.verify);});
});
test('source-and-runtime-path-mapping-cannot-diverge',()=>{
 for(const patch of [{source:'/wrong'},{path:'/other/index.js'},{path:'/input/node_modules/../ws/index.js'},{extra:true}])fixture(f=>{Object.assign(f.files[0],patch);assert.throws(f.verify);});
});
test('end-boundary-rechecks-added-directory',()=>fixture(f=>{assert.equal(f.verify().exact,true);fs.mkdirSync(path.join(f.root,'late'));assert.throws(f.verify,/DEPENDENCY_EXACT_MEMBERSHIP/);}));
console.log(JSON.stringify({scope:'GUEST_DEPENDENCY_INVENTORY_DATA_ONLY',checks:cases.length,cases,optionalModuleImported:false,networkExecuted:false,containerExecuted:false}));
