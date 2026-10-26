"""SOURCE ONLY: three DATA regressions, distinct from the13 capture controls."""
from pathlib import Path
import importlib.util,os,unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE/'snapshot-controls-actual-r1'
def module():
 s=importlib.util.spec_from_file_location('capture_snapshot_fixture',HERE/'capture-controls.py')
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def put(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
class SnapshotPaths(unittest.TestCase):
 def test_01_same_basename_preserves_distinct_full_members(self):
  m=module();d=ROOT/'collision';d.mkdir();a=d/'one';b=d/'two';a.mkdir();b.mkdir()
  put(a/'PLAN.md',b'one');put(b/'PLAN.md',b'two')
  expected={str(p):m.pin(p) for p in (a/'PLAN.md',b/'PLAN.md')}
  self.assertEqual(m.snapshot_paths(expected),expected);self.assertEqual(len(expected),2)
 def test_02_external_prefix_reads_actual_original_and_detects_drift(self):
  m=module();d=ROOT/'external-prefix';d.mkdir();external=d/'external';projected=d/'here';external.mkdir();projected.mkdir()
  p=external/'subject.json';put(p,b'original');put(projected/'subject.json',b'original')
  before={str(p):m.pin(p)}
  with p.open('ab') as f:f.write(b'drift');f.flush();os.fsync(f.fileno())
  after=m.snapshot_paths(before);self.assertNotEqual(before,after);self.assertEqual(list(after),[str(p)])
  put(d/'observed.json',__import__('json').dumps({'before':before,'after':after}).encode())
 def test_03_missing_actual_path_refuses_even_with_same_basename_elsewhere(self):
  m=module();d=ROOT/'missing';d.mkdir();p=d/'subject.json';put(p,b'exists');expected={str(p):m.pin(p)}
  p.rename(d/'preserved-original.json')
  with self.assertRaises(FileNotFoundError):m.snapshot_paths(expected)
if __name__=='__main__':ROOT.mkdir(mode=0o700,exist_ok=False);unittest.main(verbosity=2)
