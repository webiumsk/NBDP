"""Read-only postrun input comparison; no runtime admission or services."""
from pathlib import Path
import hashlib, importlib.util, json, os, stat, sys, time
HERE=Path(__file__).resolve().parent
OUT=HERE/'input-postrun-r2'
def main():
 assert sys.flags.isolated and sys.dont_write_bytecode
 os.umask(0o077); started=time.time_ns()
 original=HERE/'verify-current-inputs-r2.py'
 assert hashlib.sha256(original.read_bytes()).hexdigest()=='4531ed969dc950a0dce492aeab0b5939de4772b310304fc9ebd035b02807ee68'
 spec=importlib.util.spec_from_file_location('reviewed_read_only_preflight',original)
 h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 subject=json.loads(h.checked({'path':str(h.SOURCE),'bytes':12116,'sha256':'553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6'}).read_bytes())
 assert h.pin(h.CONFIG)['sha256']=='cec7ee4aa2701eb8430434345454526bbcdfd35d2fe500e8b766db52939f3023'
 config=json.loads(h.CONFIG.read_bytes())
 before=[h.pin(h.checked(row)) for row in subject['sources']]
 controller=next(row for row in subject['sources'] if row['path']==str(h.PRODUCER/'supervisor.py'))
 spec=importlib.util.spec_from_file_location('reviewed_producer_postrun',h.checked(controller))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.verify_config(config)
 assert h.pin(h.FROZEN)['sha256']=='f9faea2fbae382dbd3bc7d9c9d6d77bd1b47988920b38afce28991f59784ecff'
 trees=[]
 for tree in json.loads(h.FROZEN.read_bytes())['fullReadTrees']:
  base=Path(tree['root']);files=[];dirs=[]
  for p in sorted(base.rglob('*')):
   assert not p.is_symlink()
   if p.is_dir():dirs.append(str(p.relative_to(base)));continue
   files.append(dict(h.pin(p),relativePath=str(p.relative_to(base)),mode=stat.S_IMODE(p.stat().st_mode)))
  files.sort(key=lambda row:row['path'])
  assert files==tree['files'] and len(files)==tree['count']
  trees.append(dict(root=str(base),regularFiles=len(files),directories=dirs,exactFileHashModeMembershipMatched=True))
 assert [h.pin(row['path']) for row in subject['sources']]==before
 staged=[]
 target=Path('/Data/nbdp-e02-tooling-20261027/ordinary-minimum-r3/runs')/config['runId']
 for row in config['sourceAndDependencyPins']:
  p=target/'input'/Path(row['path']).name
  if p.is_file():
   observed=h.pin(p);assert observed['bytes']==row['bytes'] and observed['sha256']==row['sha256'];staged.append(observed)
 v=dict(schema='nbdp-read-only-postrun-input-custody-v1',actor='/root',runId=config['runId'],startedUtcNs=started,finishedUtcNs=time.time_ns(),sourceSubject=h.pin(h.SOURCE),configuration=h.pin(h.CONFIG),sourceBefore=before,sourceAfterEqual=True,stagedExactCopies=staged,trees=trees,unchangedReviewedProducerVerifyConfigCompleted=True,scope='Full SDK434 and guard522 regular-file hash/mode/membership plus unchanged producer verify_config source/artifact/dependency/canonical comparisons. Directory membership retained; no original directory-mode baseline claim. No Docker images/VM/KVM/resources/role/lease actions.',roleQualified=False,originalFailurePreserved=True)
 OUT.mkdir(mode=0o700,exist_ok=False)
 with (OUT/'verification.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps(dict(verification=h.pin(OUT/'verification.json'),sourceFiles=len(before),stagedCopies=len(staged),trees=[dict(root=x['root'],regularFiles=x['regularFiles']) for x in trees])))
if __name__=='__main__':main()
