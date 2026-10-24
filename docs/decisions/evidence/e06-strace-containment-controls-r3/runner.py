"""SOURCE ONLY. One real pinned-strace fixture invokes the SAME observer.capture.

No admission/LOCAL/Node. Only ROOT/fixture caps/time constants and subprocess
recording/capture-fault wrappers are substituted. All7 cases use actual strace.
"""
from pathlib import Path
import importlib.util,json,os,subprocess,sys,time
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
OBSERVER=HERE.parent/'e06-request-phase-diagnostic-source-r4/observer.py'
def put(p,v):
 b=(json.dumps(v,indent=2)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def main():
 out=Path(sys.argv[1]);case=sys.argv[2]
 spec=importlib.util.spec_from_file_location('owned_strace_fixture_observer',OBSERVER)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 # Do not create strace before independent guard records this owned runner.
 put(out/'runner-ready.json',{'pid':os.getpid()})
 ready_deadline=time.monotonic()+3
 while not (out/'runner-ack.json').exists():
  if time.monotonic()>=ready_deadline:raise TimeoutError('RUNNER_PRE_FORK_ACK_DEADLINE')
  time.sleep(.01)
 # Fixed source/config/tool/host pinning is performed by guard BEFORE this process.
 r,w=os.pipe2(os.O_CLOEXEC)
 argv=['/usr/bin/strace',*m.TRACE_OPTIONS,'-o','/proc/self/fd/'+str(w),'--',sys.executable,'-I','-B',
       str(HERE/'fixture.py'),str(out),'parent',case]
 original_popen=subprocess.Popen;original_fdopen=os.fdopen;original_wait=subprocess.Popen.wait;original_killpg=os.killpg
 events=[];reaped=False;writes=[];owned_handles=[]
 def popen(*a,**kw):
  p=original_popen(*a,**kw);owned_handles.append(p)  # retain BEFORE any PID/identity/write
  put(out/'tracer-ready.json',{'pid':p.pid,'argv':a[0]});return p
 def wait(p,*a,**kw):
  nonlocal reaped
  rc=original_wait(p,*a,**kw);reaped=True;events.append({'operation':'tracer-reaped','pid':p.pid,'exit':rc});return rc
 def killpg(pid,sig):
  assert not reaped;events.append({'operation':'observer-signal-owned-tracer-group','pid':pid,'signal':int(sig)})
  return original_killpg(pid,sig)
 class FaultWrite:
  def __init__(self,h):self.h=h
  def write(self,b):
   if (out/'fault-arm.json').exists():
    writes.append({'requested':len(b),'persisted':0,'fault':'FIXTURE_CAPTURE_WRITE_FAILURE'})
    raise OSError('FIXTURE_CAPTURE_WRITE_FAILURE')
   return self.h.write(b)
  def fileno(self):return self.h.fileno()
  def flush(self):return self.h.flush()
  def close(self):return self.h.close()
 def fdopen(fd,*a,**kw):
  h=original_fdopen(fd,*a,**kw)
  if case=='capture-fault' and a and a[0]=='wb' and os.readlink('/proc/self/fd/'+str(fd))==str(out/'trace.bin'):return FaultWrite(h)
  return h
 started=time.monotonic()
 try:
  with patch.object(m,'ROOT',out),patch.object(m,'CAPS',{'trace':1048576,'stdout':65536,'stderr':262144}),\
       patch.object(m,'ACTIVE_SECONDS',4),patch.object(m,'CLEANUP_SECONDS',2),\
       patch.object(m.subprocess,'Popen',popen),patch.object(original_popen,'wait',wait),\
       patch.object(m.os,'killpg',killpg),patch.object(m.os,'fdopen',fdopen):
   result=m.capture(argv,r,w,out,started,started+4,started+6)
  put(out/'observer-capture.json',result)
 finally:put(out/'runner-events.json',{'events':events,'faultWrites':writes,'reaped':reaped})
if __name__=='__main__':main()
