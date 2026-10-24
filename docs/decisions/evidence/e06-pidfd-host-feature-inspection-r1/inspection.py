from pathlib import Path
import os,sys,signal,ctypes,json,hashlib,platform,sysconfig
R=Path('/home/peterhorvath/apps/bitcoin/NBDP')
D=R/'docs/decisions/evidence/e06-pidfd-host-feature-inspection-r1'
expected='5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'
p=Path(sys.executable).resolve();b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==expected
assert sys.flags.isolated==1 and sys.flags.dont_write_bytecode==1
D.mkdir(mode=0o700)
def save(name,obj):
 fd=os.open(D/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as f:json.dump(obj,f,indent=2);f.write('\n')
libc=ctypes.CDLL(None,use_errno=True)
obj=dict(schema='nbdp-read-only-host-pidfd-feature-inspection-v1',actor='/root',context='SUPPORTED_HOST_EXECUTION',python=dict(path=str(p),bytes=len(b),sha256=expected,version=sys.version),uid=os.getuid(),kernel=platform.release(),machine=platform.machine(),pythonApi={name:hasattr(module,name) for name,module in [('pidfd_open',os),('pidfd_send_signal',signal),('waitid',os),('P_PIDFD',os),('WNOWAIT',os)]},libcSymbols={name:hasattr(libc,name) for name in ['pidfd_open','pidfd_send_signal']},libcVersion=os.confstr('CS_GNU_LIBC_VERSION'),buildConfig={name:sysconfig.get_config_var(name) for name in ['HAVE_PIDFD_OPEN','HAVE_PIDFD_SEND_SIGNAL']},actualPidfdCalls=0,actualSignals=0,actualSpawnedFixtureProcesses=0,limits=['Read-only feature availability only; no pidfd opened, signal sent, child fixture, strace, Node or protocol test.','Symbol presence is not runtime functionality, permission or containment qualification.','This does not reinterpret the preserved managed-context model-test failure.'])
save('result.json',obj)
raw=Path(__file__).read_bytes();fd=os.open(D/'inspection.py',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'wb') as f:f.write(raw)
out=(D/'result.json').read_bytes();print(json.dumps({'result':str(D/'result.json'),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'pythonApi':obj['pythonApi'],'libcSymbols':obj['libcSymbols'],'actualPidfdCalls':0,'actualSignals':0}))
