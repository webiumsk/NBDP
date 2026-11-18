"""PREPARED source/custody mock controls. No guard issue, tools or containers."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ROOT/'experiments/prototypes/e02_ordinary_minimum_v1'
SPEC=importlib.util.spec_from_file_location('query_diagnostic_subject',HERE/'supervisor.py')
subject=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)
CID='c'*64


def function_ast(source,name,klass=None):
 tree=ast.parse(source)
 if klass:tree=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==klass)
 return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)


class SourceCustodyControls(unittest.TestCase):
 def test_guard_is_exact_original_unchanged_bytes(self):
  self.assertEqual((HERE/'lease_guard.py').read_bytes(),(BASE/'lease_guard.py').read_bytes())

 def test_original_clock_command_identity_cleanup_methods_unchanged(self):
  for name in ('check','command','record_command','validate_identity','cleanup'):
   with self.subTest(name=name):self.assertEqual(function_ast((HERE/'supervisor.py').read_text(),name,'Runtime'),function_ast((BASE/'supervisor.py').read_text(),name,'Runtime'))

 def test_original_owned_child_lifecycle_forwarding_unchanged(self):
  for name in ('run_service','finalize','exact_cid_absent'):
   self.assertEqual(function_ast((HERE/'supervisor.py').read_text(),name),function_ast((BASE/'supervisor.py').read_text(),name))

 def test_only_three_roles_no_adb_snapshot_or_sdk_route(self):
  self.assertEqual(subject.ROLES,('anchor','rs-relay','fixture'))
  self.assertFalse(hasattr(subject.Runtime,'adb'));self.assertFalse(hasattr(subject.Runtime,'snapshot'))
  with self.assertRaisesRegex(RuntimeError,'three diagnostic roles'):subject.Runtime.start(object(),'android')

 def test_signed_public_input_and_query_exact_frozen_hashes(self):
  self.assertEqual(hashlib.sha256((HERE/'publish-frame.json').read_bytes()).hexdigest(),'844e64e2790a9833880aedc3016e9da82130a29d9e415858d0d46fdcb8946494')
  self.assertEqual(len((HERE/'query-frame.json').read_bytes()),112)
  self.assertEqual(hashlib.sha256((HERE/'query-frame.json').read_bytes()).hexdigest(),'ae042185e892c9a385b7add6442e478834817d8ed310f8967e7dc3d4bd689389')

 def test_no_signing_key_or_nonce_input_in_diagnostic_plan(self):
  plan=json.loads((HERE/'fixture-plan.json').read_text())
  self.assertEqual(plan['pins'],{})
  self.assertNotIn('roles',plan);self.assertNotIn('nsec',plan)
  self.assertNotIn('decryption-key',(HERE/'fixture.mjs').read_text())

 def test_closed_cid_absence_is_not_generic_exit1(self):
  self.assertTrue(subject.exact_cid_absent(subprocess.CompletedProcess([],1,b'[]\n',b'Error: No such object: '+CID.encode()+b'\n'),CID))
  self.assertFalse(subject.exact_cid_absent(subprocess.CompletedProcess([],1,b'',b'permission denied'),CID))

 def runtime(self,out,foreign=False):
  r=subject.Runtime.__new__(subject.Runtime);r.out=out;r.docker='/NO_TOOL_EXECUTED/docker';r.host_env={}
  r.ids={'anchor':CID};r.plan_pin={'sha256':'e'*64};r.lease_sha='d'*64
  entry={'name':'owned-diagnostic-anchor','image':subject.RUNTIME,'labels':{'nbdp.run':'a'*32,'nbdp.role':'anchor','nbdp.creation':'b'*32},'command':['fixed'],'mounts':[]};r.intents={'anchor':entry}
  labels=dict(entry['labels'])
  if foreign:labels['nbdp.creation']='f'*32
  data={'Id':CID,'Name':'/'+entry['name'],'Image':subject.RUNTIME,'Config':{'Labels':labels,'Env':['NBDP_LEASE_SHA256='+r.lease_sha,'NBDP_FIXTURE_PLAN_SHA256='+subject.digest(HERE/'fixture-plan.json'),'NBDP_MINIMUM_RUN_CONFIG_SHA256='+r.plan_pin['sha256']],'Entrypoint':[subject.PY[0]],'Cmd':entry['command'],'User':str(subject.os.getuid())+':'+str(subject.os.getgid())},'HostConfig':{'NetworkMode':'none','Privileged':False,'PortBindings':{},'CapAdd':[],'ReadonlyRootfs':True,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],'Memory':128*1048576,'MemorySwap':128*1048576,'PidsLimit':64,'NanoCpus':1000000000,'Devices':[]},'Mounts':[]}
  return r,data

 def cleanup_model(self,out,foreign=False,absence=False):
  r,data=self.runtime(out,foreign);calls=[];inspect=0
  def run(argv,**unused):
   nonlocal inspect
   args=argv[1:];calls.append(args)
   if args[0]=='inspect':
    inspect+=1
    if inspect==1:return subprocess.CompletedProcess(argv,0,json.dumps([data]).encode(),b'')
    return subprocess.CompletedProcess(argv,1,b'[]\n',b'permission denied' if absence else b'Error: No such object: '+CID.encode()+b'\n')
   return subprocess.CompletedProcess(argv,0,b'',b'')
  with patch.object(subject.subprocess,'run',run):result=r.cleanup()
  return result,calls

 def test_exact_owned_cleanup_remove_and_absence_positive(self):
  with tempfile.TemporaryDirectory() as tmp:
   result,calls=self.cleanup_model(Path(tmp));self.assertTrue(result['ok']);self.assertIn(['rm','-f',CID],calls);self.assertTrue(result['rows'][0]['absenceConfirmed'])

 def test_foreign_creation_identity_never_removed(self):
  with tempfile.TemporaryDirectory() as tmp:
   result,calls=self.cleanup_model(Path(tmp),foreign=True);self.assertFalse(result['ok']);self.assertFalse(any(c[0]=='rm' for c in calls))

 def test_uncertain_absence_remains_failure(self):
  with tempfile.TemporaryDirectory() as tmp:
   result,calls=self.cleanup_model(Path(tmp),absence=True);self.assertFalse(result['ok']);self.assertIn(['rm','-f',CID],calls);self.assertFalse(result['rows'][0]['absenceConfirmed'])

class ClosedDependencyControls(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name);self.root=self.base/'node_modules';(self.root/'ws').mkdir(parents=True)
  (self.root/'ws/index.js').write_text('SYNTHETIC_DATA_NEVER_IMPORTED')
  self.tree={'schema':'e02-transport-dependency-tree-v2','sourceRoot':str(self.root),'runtimeRoot':'/input/node_modules',**subject.dependency_snapshot(self.root)}
  p=self.root/'ws/index.js';self.fixture={'dependencyFiles':[{'source':str(p),'path':'/input/node_modules/ws/index.js','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}

 def verify(self):return subject.verify_dependency_inventory(self.fixture,self.tree,self.root)

 def test_unchanged_complete_tree_accepted(self):
  self.assertTrue(self.verify()['exact'])

 def test_extra_regular_and_nested_optional_bufferutil_refused(self):
  for name in ('extra.js','ws/node_modules/bufferutil/index.js'):
   with self.subTest(name=name):
    p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('DO_NOT_IMPORT')
    with self.assertRaisesRegex(RuntimeError,'exact membership'):self.verify()
    p.unlink()
    for folder in (self.root/'ws/node_modules/bufferutil',self.root/'ws/node_modules'):
     if folder.exists():folder.rmdir()

 def test_missing_and_changed_regular_member_refused(self):
  p=self.root/'ws/index.js';raw=p.read_bytes();p.unlink()
  with self.assertRaises(RuntimeError):self.verify()
  p.write_bytes(raw+b'changed')
  with self.assertRaises(RuntimeError):self.verify()

 def test_new_safe_escape_and_dangling_symlinks_refused(self):
  for target in ('ws/index.js','../external','missing'):
   with self.subTest(target=target):
    (self.base/'external').write_text('OUTSIDE_NEVER_READ');p=self.root/'added-link';p.symlink_to(target)
    with self.assertRaises((RuntimeError,OSError)):self.verify()
    p.unlink()

 def test_special_fifo_refused_without_read(self):
  subject.os.mkfifo(self.root/'special')
  with self.assertRaisesRegex(RuntimeError,'special file'):self.verify()

 def test_source_runtime_canonical_mapping_and_unknown_fields_refused(self):
  original=dict(self.fixture['dependencyFiles'][0])
  for patcher in ({'source':str(self.root/'wrong')},{'path':'/input/node_modules/../ws/index.js'},{'path':'/other/ws/index.js'},{'extra':True}):
   with self.subTest(patcher=patcher):
    self.fixture['dependencyFiles'][0]={**original,**patcher}
    with self.assertRaises(RuntimeError):self.verify()
  self.fixture['dependencyFiles'][0]=original

 def test_actual_inventory_gate_refuses_before_host_import_or_container(self):
  p=self.root/'ws/node_modules/bufferutil/index.js';p.parent.mkdir(parents=True);p.write_text('NEVER_IMPORT')
  config=self.base/'config.json';release=self.base/'release.json';config.write_text('{}');release.write_text('{}')
  with patch.object(subject,'verify_config',side_effect=lambda _value:self.verify()),patch.object(subject,'load_module') as imports,patch.object(subject.Runtime,'start') as starts:
   with self.assertRaises(RuntimeError):subject.execute(config,subject.digest(config),release,subject.digest(release),self.base/'out')
   imports.assert_not_called();starts.assert_not_called()

 def test_end_boundary_rechecks_current_membership_not_cached_success(self):
  self.assertTrue(self.verify()['exact']);(self.root/'new.js').write_text('LATE_ADDITION')
  with self.assertRaisesRegex(RuntimeError,'exact membership'):self.verify()


if __name__=='__main__':unittest.main(verbosity=2)
