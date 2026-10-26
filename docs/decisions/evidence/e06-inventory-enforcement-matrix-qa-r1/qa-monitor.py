from pathlib import Path
import hashlib,json,os,subprocess,sys,time
E=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence')
o=E/'e06-inventory-enforcement-matrix-qa-r1'
c=json.loads((o/'config.json').read_bytes());r=json.loads((o/'release.json').read_bytes())
def pin(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
for d in [r['config'],r['sourceApproval'],r['controlApproval'],r['grammarAcceptance'],r['positiveAcceptance'],r['primaryMatrixAcceptance'],r['matrix'],r['bootstrap']]:assert pin(d['path'])==d
assert r['bootstrap']['sha256']=='a482b3323fa544bee46e157dd311ab2d4813fb5b5f477216246fa746a1bc2479'
assert r['config']['sha256']=='9e83a3de19394d236d2575a1bbfdfb21ba47511f6d5f4d35f09e3242a87ad0ee'
assert r['schema']=='e06-inventory-matrix-qa-release-v1' and r['decision']=='RELEASE_EXACT_ADMISSION_INPUT_MATRIX_QA_ONLY'
assert r['rootSession']=='/root' and r['executionSession']==c['executionSession']=='/root/android_health_qa' and r['runRole']==c['runRole']=='qa'
assert r['primaryMatrixAcceptance']==c['primaryMatrixAcceptance']
for role in ('qa','security'):
 v=json.loads((o/('independent-'+role+'-review.json')).read_bytes());assert v['findings']==[] and v['configuration']==r['config']
assert time.time_ns()//1000000<r['notAfterUtcMs']
out=o/'outer-actual';out.mkdir(mode=0o700)
argv=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(o/'matrix.py'),str(o/'config.json'),r['config']['sha256'],str(o/'release.json'),pin(o/'release.json')['sha256'],'/root/android_health_qa']
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'};ceiling=600
start=time.monotonic();p=subprocess.Popen(argv,cwd='/home/peterhorvath/apps/bitcoin/NBDP',env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE);forced=False;error=None
try:stdout,stderr=p.communicate(timeout=ceiling)
except subprocess.TimeoutExpired:
 forced=True;error='OUTER_TIMEOUT'
 if p.poll() is None:p.terminate()
 try:stdout,stderr=p.communicate(timeout=5)
 except subprocess.TimeoutExpired:
  if p.poll() is None:p.kill()
  stdout,stderr=p.communicate(timeout=5)
for n,b in [('stdout.bin',stdout),('stderr.bin',stderr)]:
 with (out/n).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
v=dict(actor='/root/android_health_qa',argv=argv,environment=env,config=pin(o/'config.json'),release=pin(o/'release.json'),pid=p.pid,pidMeaning='PID in the tool execution namespace; not asserted host PID',exit=p.returncode,reaped=True,stdoutEOF=True,stderrEOF=True,forced=forced,error=error,durationMs=int((time.monotonic()-start)*1000),stdout=pin(out/'stdout.bin'),stderr=pin(out/'stderr.bin'),scope='Actual QA76 caller-memory inventory/mat gate cases only; no filesystem-drift/full LOCAL/native/network/TARGET qualification.')
with (out/'execution.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(v));sys.exit(0 if p.returncode==0 and not forced and error is None else 2)
