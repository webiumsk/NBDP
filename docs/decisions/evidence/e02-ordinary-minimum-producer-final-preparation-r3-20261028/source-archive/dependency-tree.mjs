// Closed relative inventory only; no optional module import/evaluation.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const need=(v,m)=>{if(!v)throw Error(m);};
function relative(s){need(typeof s==='string'&&s!==''&&!s.startsWith('/')&&s.split('/').every(x=>x!==''&&x!=='.'&&x!=='..'),'CANONICAL_DEPENDENCY_RELATIVE_PATH');return s;}
export function verifyDependencyTree(root,tree,files){
 need(path.isAbsolute(root)&&path.resolve(root)===root&&fs.realpathSync(root)===root,'CANONICAL_DEPENDENCY_ROOT');
 need(tree&&typeof tree==='object'&&Object.keys(tree).sort().join(',')==='directories,files,runtimeRoot,schema,sourceRoot,symlinks','CLOSED_DEPENDENCY_TREE_KEYS');
 need(tree.schema==='e02-transport-dependency-tree-v2'&&tree.runtimeRoot==='/input/node_modules','CLOSED_DEPENDENCY_TREE');
 const actual={directories:[],files:[],symlinks:[]};
 function walk(folder){for(const name of fs.readdirSync(folder).sort()){
  const p=path.join(folder,name),rel=relative(path.relative(root,p)),s=fs.lstatSync(p);
  if(s.isSymbolicLink()){
   const link=fs.readlinkSync(p),resolved=fs.realpathSync(p);need(resolved.startsWith(root+'/'),'DEPENDENCY_SYMLINK_ESCAPE');
   actual.symlinks.push({path:rel,link,target:relative(path.relative(root,resolved))});
  }else if(s.isDirectory()){actual.directories.push(rel);walk(p);}
  else if(s.isFile())actual.files.push(rel);
  else throw Error('DEPENDENCY_SPECIAL_FILE');
 }}walk(root);
 const ordered=v=>JSON.stringify(v);for(const k of ['directories','files'])actual[k].sort();actual.symlinks.sort((a,b)=>a.path.localeCompare(b.path));
 need(ordered(actual)===ordered({directories:tree.directories,files:tree.files,symlinks:tree.symlinks}),'DEPENDENCY_EXACT_MEMBERSHIP');
 need(Array.isArray(files)&&files.length===actual.files.length&&new Set(files.map(d=>d.path)).size===files.length,'DEPENDENCY_DESCRIPTOR_MEMBERSHIP');
 const expected=[];
 for(const d of files){
  need(Object.keys(d).sort().join(',')==='bytes,path,sha256,source','CLOSED_DEPENDENCY_DESCRIPTOR');
  need(typeof d.path==='string'&&d.path.startsWith(tree.runtimeRoot+'/'),'DEPENDENCY_RUNTIME_PATH');
  const rel=relative(d.path.slice(tree.runtimeRoot.length+1));expected.push(rel);
  need(d.source===tree.sourceRoot+'/'+rel,'DEPENDENCY_SOURCE_RUNTIME_MAPPING');
  const p=path.join(root,rel);need(fs.realpathSync(p)===p&&fs.lstatSync(p).isFile(),'REGULAR_CANONICAL_DEPENDENCY');
  const raw=fs.readFileSync(p);need(raw.length===d.bytes&&createHash('sha256').update(raw).digest('hex')===d.sha256,'DEPENDENCY_BYTES_DRIFT');
 }
 expected.sort();need(ordered(expected)===ordered(actual.files),'DEPENDENCY_ALL_REGULAR_MEMBERS');
 return {schema:'e02-transport-dependency-check-v2',files:actual.files.length,directories:actual.directories.length,symlinks:actual.symlinks.length,exact:true};
}
