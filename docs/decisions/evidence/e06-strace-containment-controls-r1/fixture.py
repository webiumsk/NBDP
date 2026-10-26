"""SOURCE ONLY. Synthetic3-session topology; run only beneath reviewed fixture guard.

Each role advertises its identity then blocks on a guard-issued private ACK before
creating another descendant. No signal/fault injection occurs before all3 ACKs.
"""
from pathlib import Path
import json,os,signal,subprocess,sys,time

def put(path,value):
 raw=(json.dumps(value,indent=2)+'\n').encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def identity():
 p=Path('/proc/self');raw=(p/'stat').read_text();fields=raw[raw.rindex(')')+2:].split()
 return {'pid':os.getpid(),'ppid':os.getppid(),'uid':os.getuid(),'starttime':int(fields[19]),
   'session':os.getsid(0),'cmdline':(p/'cmdline').read_bytes().hex()}
def main():
 out=Path(sys.argv[1]);role=sys.argv[2];case=sys.argv[3]
 assert role in ('parent','child','grandchild')
 if role=='parent':os.setsid()
 put(out/(role+'-ready.json'),identity())
 deadline=time.monotonic()+8
 while not (out/(role+'-ack.json')).exists():
  if time.monotonic()>=deadline:raise SystemExit(71)
  time.sleep(.01)
 ack=json.loads((out/(role+'-ack.json')).read_bytes());assert ack['pid']==os.getpid() and ack['starttime']==identity()['starttime']
 child=None
 if role!='grandchild':
  next_role='child' if role=='parent' else 'grandchild'
  child=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),str(out),next_role,case],
    stdin=subprocess.DEVNULL,start_new_session=True,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'})
 while not (out/'all-ready.json').exists():
  if time.monotonic()>=deadline:raise SystemExit(72)
  time.sleep(.01)
 # Exercise all6 buffer syscalls with a deliberately recognizable PUBLIC,
 # synthetic privacy sentinel. Raw trace must suppress every buffer rendering.
 marker=b'PUBLIC_SYNTHETIC_BUFFER_SENTINEL_6E06\n'
 fd=os.open(out/(role+'-synthetic.bin'),os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 os.write(fd,marker);os.pwrite(fd,marker,0);os.pread(fd,len(marker),0)
 os.lseek(fd,0,0);os.read(fd,len(marker));os.lseek(fd,0,0)
 os.readv(fd,[bytearray(len(marker))]);os.writev(fd,[marker]);os.close(fd)
 os.write(1,marker);os.write(1,('FIXTURE_READY_'+role+'\n').encode())
 put(out/(role+'-exercised.json'),{'pid':os.getpid(),'sixSyscallsIssued':True})
 if case in ('natural-zero','natural-refusal'):
  if child is not None:
   rc=child.wait(timeout=max(.01,deadline-time.monotonic()));assert rc==0
  raise SystemExit(2 if case=='natural-refusal' and role=='parent' else 0)
 # Normal fault fixtures intentionally wait. This lifetime is a secondary bound,
 # never evidence of strace cleanup; guard deadline and pidfds are independent.
 while time.monotonic()<deadline:
  os.write(1,b'FIXTURE_HEARTBEAT\n');time.sleep(.02)
 if child is not None:
  try:child.wait(timeout=.1)
  except subprocess.TimeoutExpired:pass
 raise SystemExit(73)
if __name__=='__main__':main()
