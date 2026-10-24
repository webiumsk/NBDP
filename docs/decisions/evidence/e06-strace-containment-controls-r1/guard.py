"""SOURCE ONLY. Independent bounded subreaper safety owner for7 strace fixtures.

No actual suite may start until source and host-context reviews authorize it.
Every signal uses a held pidfd checked non-exited immediately before signalling.
A fallback means FAIL regardless of eventual cleanup. No numeric-PID kill exists.
No Node, attach, project imports/admission or production access.
"""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,os,re,select,signal,stat,subprocess,sys,time
HERE=Path(__file__).resolve().parent
CASES=['natural-zero','natural-refusal','deadline','interrupt','capture-fault','tracer-death','inner-parent-death']
OUT=HERE/'actual-containment-r1'
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}

def need(ok,message):
 if not ok:raise ValueError(message)
def put(p,v):
 raw=(json.dumps(v,indent=2)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def pin(p):
 b=Path(p).read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600,'PRIVATE_REGULAR_600')
 need(s.st_size<=1048576,'METADATA_CAP');return json.loads(p.read_bytes())
def context():
 return {'uid':os.getuid(),'gid':os.getgid(),'uidMap':Path('/proc/self/uid_map').read_text(),
 'gidMap':Path('/proc/self/gid_map').read_text(),'userNamespace':os.readlink('/proc/self/ns/user'),
 'mountNamespace':os.readlink('/proc/self/ns/mnt')}
def identity(pid):
 p=Path('/proc')/str(pid);s=p.stat();raw=(p/'stat').read_text();f=raw[raw.rindex(')')+2:].split()
 return {'pid':pid,'ppid':int(f[1]),'uid':s.st_uid,'starttime':int(f[19]),'session':int(f[3]),'cmdline':(p/'cmdline').read_bytes().hex()}
def exited(fd):return bool(select.select([fd],[],[],0)[0])
def adopt(row,expected_argv,parent_pid,events):
 pid=row['pid'];need(type(pid) is int and pid>1,'VALID_FIXTURE_PID')
 a=identity(pid);need(a==row and a['uid']==os.getuid() and a['ppid']==parent_pid,'EXACT_OWNED_FIXTURE_PARENT')
 need(bytes.fromhex(a['cmdline']).split(b'\0')[:-1]==[os.fsencode(x) for x in expected_argv],'EXACT_OWNED_CMDLINE')
 fd=os.pidfd_open(pid,0);need(identity(pid)==a and not exited(fd),'HELD_PIDFD_IDENTITY_STABLE')
 info=Path('/proc/self/fdinfo/'+str(fd)).read_text().splitlines()
 need('Pid:\t'+str(pid) in info,'PIDFD_MATCHES_EXACT_PID')
 events.append({'operation':'held-identity','identity':a,'pidfd':fd});return {'identity':a,'fd':fd,'reaped':False}
def send(item,sig,events,reason):
 need(not item['reaped'],'NO_POST_REAP_SIGNAL')
 if exited(item['fd']):events.append({'operation':'signal-skipped-already-exited','pid':item['identity']['pid'],'reason':reason});return False
 # pidfd_send_signal cannot target a later reused numeric PID.
 signal.pidfd_send_signal(item['fd'],sig,None,0)
 events.append({'operation':'pidfd-signal','pid':item['identity']['pid'],'starttime':item['identity']['starttime'],
 'signal':int(sig),'reason':reason});return True

def one(case,subject):
 out=OUT/case;out.mkdir(mode=0o700);events=[];items={};fallback=False;faults=[];trigger=False;ready=False
 began=time.monotonic();guard_deadline=began+9;cleanup_deadline=began+11
 stdout_fd=os.open(out/'runner-stdout.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 stderr_fd=os.open(out/'runner-stderr.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 # Runner output is its own source-controlled short summary/errors only. Disk cap
 # RLIMIT_FSIZE also bounds all runner/tracer inherited regular output writes.
 def limits():
  import resource
  resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
 runner=None
 try:
  argv=[sys.executable,'-I','-B',str(HERE/'runner.py'),str(out),case]
  runner=subprocess.Popen(argv,cwd=HERE,env=ENV,stdin=subprocess.DEVNULL,stdout=stdout_fd,stderr=stderr_fd,
    start_new_session=True,preexec_fn=limits)
  immediate_fd=os.pidfd_open(runner.pid,0)
  immediate_identity=identity(runner.pid)
  items['runner']={'identity':immediate_identity,'fd':immediate_fd,'reaped':False}
  settle=min(guard_deadline,time.monotonic()+1)
  while True:
   row=identity(runner.pid)
   if bytes.fromhex(row['cmdline']).split(b'\0')[:-1]==[os.fsencode(x) for x in argv]:break
   need(time.monotonic()<settle,'RUNNER_EXEC_IDENTITY_DEADLINE');time.sleep(.005)
  verified=adopt(row,argv,os.getpid(),events)
  os.close(items['runner']['fd']);items['runner']=verified
  capture_seen=None
  while time.monotonic()<guard_deadline:
   if 'tracer' not in items and (out/'tracer-ready.json').exists():
    d=read(out/'tracer-ready.json');row=identity(d['pid']);items['tracer']=adopt(row,d['argv'],runner.pid,events)
   for role,parent_role in [('parent','tracer'),('child','parent'),('grandchild','child')]:
    p=out/(role+'-ready.json')
    if role not in items and parent_role in items and p.exists():
     row=read(p);argv=[sys.executable,'-I','-B',str(HERE/'fixture.py'),str(out),role,case]
     items[role]=adopt(row,argv,items[parent_role]['identity']['pid'],events)
     put(out/(role+'-ack.json'),{'pid':row['pid'],'starttime':row['starttime']})
   if not ready and all(k in items for k in ['tracer','parent','child','grandchild']):
    sessions=[items[k]['identity']['session'] for k in ['parent','child','grandchild']]
    need(len(set(sessions))==3,'THREE_DISTINCT_FIXTURE_SESSIONS');ready=True
    put(out/'all-ready.json',{'allHeldPidfds':True,'sessions':sessions,'guardPid':os.getpid()})
   exercised=ready and all((out/(role+'-exercised.json')).exists() for role in ['parent','child','grandchild'])
   if exercised and not trigger:
    if case=='capture-fault':put(out/'fault-arm.json',{'allThreeExercised':True});trigger=True
    elif case=='interrupt':send(items['runner'],signal.SIGINT,events,'INTENTIONAL_OBSERVER_INTERRUPT');trigger=True
    elif case=='tracer-death':send(items['tracer'],signal.SIGKILL,events,'INTENTIONAL_TRACER_DEATH');trigger=True
    elif case=='inner-parent-death':send(items['parent'],signal.SIGKILL,events,'INTENTIONAL_INNER_PARENT_DEATH');trigger=True
   # Do not kill the runner as soon as it exits: tracees may already be adopted.
   if ready and all(exited(v['fd']) for v in items.values()):break
   if (out/'observer-capture.json').exists():
    if capture_seen is None:capture_seen=time.monotonic()
    if time.monotonic()-capture_seen>=.25:break  # No waiting for8s fixture expiry as false containment evidence.
   time.sleep(.01)
  natural_absence=ready and all(exited(v['fd']) for v in items.values())
  if not natural_absence:
   fallback=True
   for k in ['grandchild','child','parent','tracer','runner']:
    if k in items:send(items[k],signal.SIGKILL,events,'SAFETY_FALLBACK_CONTAINMENT_FAIL')
  while time.monotonic()<cleanup_deadline and any(not exited(v['fd']) for v in items.values()):time.sleep(.01)
  need(all(exited(v['fd']) for v in items.values()),'SAFETY_CLEANUP_INCOMPLETE')
  # Reap direct runner once WNOWAIT confirms exit; then subreaper-adopted known
  # tracees only. No unknown PID is ever signalled or reaped by numeric wildcard.
  need(os.waitid(os.P_PID,runner.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is not None,'RUNNER_WNOWAIT')
  rc=runner.wait(timeout=0);items['runner']['reaped']=True;events.append({'operation':'reaped','role':'runner','pid':runner.pid,'exit':rc})
  for k in ['tracer','parent','child','grandchild']:
   if k not in items:continue
   v=items[k]
   try:
    observed=os.waitid(os.P_PID,v['identity']['pid'],os.WEXITED|os.WNOHANG|os.WNOWAIT)
    if observed is not None:
     w=os.waitpid(v['identity']['pid'],os.WNOHANG);need(w[0]==v['identity']['pid'],'OWNED_REAP_MATCH')
     events.append({'operation':'reaped','role':k,'pid':w[0],'waitStatus':w[1]})
    else:raise ValueError('KNOWN_ADOPTED_CHILD_NOT_REAPABLE')
   except ChildProcessError:
    # An original fixture/strace parent may have reaped it already; exited held
    # pidfd + ECHILD after root runner reap establishes no live owned child.
    events.append({'operation':'already-reaped-by-original-parent','role':k,'pid':v['identity']['pid']})
   v['reaped']=True
 except BaseException as e:
  faults.append({'type':type(e).__name__,'message':str(e)[:4096]});fallback=True
  # Cleanup continues independently even if readiness/adoption/trace capture fails.
  for k,v in reversed(list(items.items())):
   try:send(v,signal.SIGKILL,events,'SAFETY_EXCEPTION_FALLBACK_CONTAINMENT_FAIL')
   except BaseException as err:faults.append({'type':type(err).__name__,'message':str(err)[:4096]})
 finally:
  # Also exercised after assertion/write/registration failures; preserve initial
  # fault and continue cleanup. The finite bound is original began+11, never reset.
  if fallback:
   for v in reversed(list(items.values())):
    try:send(v,signal.SIGKILL,events,'SAFETY_FINAL_FALLBACK_CONTAINMENT_FAIL')
    except BaseException as err:faults.append({'type':type(err).__name__,'message':str(err)[:4096]})
   while time.monotonic()<cleanup_deadline and any(not exited(v['fd']) for v in items.values()):time.sleep(.01)
   for role,v in items.items():
    if v['reaped'] or not exited(v['fd']):continue
    try:
     observed=os.waitid(os.P_PID,v['identity']['pid'],os.WEXITED|os.WNOHANG|os.WNOWAIT)
     if observed is not None:
      if role=='runner':rc=runner.wait(timeout=0)
      else:rc=os.waitpid(v['identity']['pid'],os.WNOHANG)[1]
      events.append({'operation':'fallback-reaped','role':role,'pid':v['identity']['pid'],'status':rc})
     else:continue
     v['reaped']=True
    except ChildProcessError:
     v['reaped']=True;events.append({'operation':'already-reaped-by-original-parent','role':role,'pid':v['identity']['pid']})
    except BaseException as err:faults.append({'type':type(err).__name__,'message':str(err)[:4096]})
  os.close(stdout_fd);os.close(stderr_fd)
  for v in items.values():os.close(v['fd'])
 record={'schema':'e06-strace-owned-fixture-guard-v1','case':case,'readyBarrierComplete':ready,
  'safetyFallbackUsed':fallback,'allKnownPidsExitedBeforeFallback':locals().get('natural_absence',False),
  'allOwnedChildrenReaped':bool(items) and all(v['reaped'] for v in items.values()),
  'events':events,'firstError':faults[0] if faults else None,'secondaryErrors':faults[1:16],
  'elapsedNs':int((time.monotonic()-began)*1000000000),'guardTotalCeilingSeconds':11,
  'realStrace':True,'sameObserverCapture':True,'noPostReapSignal':True,
  'disposition':'UNQUALIFIED_PENDING_RAW_ASSERTIONS_AND_INDEPENDENT_REVIEW'}
 try:
  cap=read(out/'observer-capture.json');raw={n:(out/(n+'.bin')).read_bytes() for n in ('trace','stdout','stderr')}
  limits={'trace':1048576,'stdout':65536,'stderr':262144}
  need(cap['reaped'] and all(cap['eof'].values()),'REAL_OBSERVER_EOF_REAP_REQUIRED')
  need(cap['retainedBytes']=={n:len(b) for n,b in raw.items()},'ACTUAL_RAW_RETAINED_COUNTS')
  need(all(len(raw[n])<=limits[n] for n in raw),'ACTUAL_RAW_CAPS')
  need(all(cap['raw'][n]==pin(out/(n+'.bin')) for n in raw),'EXACT_ACTUAL_RAW_PINS')
  trace=raw['trace'];sentinel=b'PUBLIC_SYNTHETIC_BUFFER_SENTINEL_6E06'
  need(sentinel not in trace and sentinel in raw['stdout'],'BUFFER_PRIVACY_POSITIVE_AND_NEGATIVE_CONTROL')
  calls={n:[] for n in ('read','pread64','readv','write','pwrite64','writev')}
  for line in trace.splitlines():
   match=re.search(rb'\b(read|pread64|readv|write|pwrite64|writev)\((.*)',line)
   if match:
    args=match.group(2).split(b')',1)[0]
    need(b'"' not in args and b"'" not in args,'NO_BUFFER_TEXT_IN_SIX_RAW_SYSCALLS')
    calls[match.group(1).decode()].append(line[:256].decode('ascii','backslashreplace'))
  need(all(calls.values()),'ALL_SIX_RAW_SYSCALLS_OBSERVED')
  expected={'deadline':'OBSERVER_ACTIVE_DEADLINE','interrupt':'OBSERVER_INTERRUPTED','capture-fault':'FIXTURE_CAPTURE_WRITE_FAILURE'}
  if case in ('natural-zero','natural-refusal'):
   need(cap['exit']==(0 if case=='natural-zero' else 2) and cap['firstError'] is None and not cap['forced']
     and cap['captureComplete'],'EXACT_NATURAL_EXIT_NO_FORCE')
  elif case in expected:
   need(cap['firstError'] is not None and cap['firstError']['message']==expected[case],'EXACT_INJECTED_FIRST_ERROR')
   need(cap['forced'],'OBSERVER_FORCED_CLEANUP_EXPECTED')
  elif case=='tracer-death':need(cap['exit']==-9,'ACTUAL_TRACER_SIGKILL')
  elif case=='inner-parent-death':need(trigger,'ACTUAL_INNER_PARENT_PIDFD_SIGKILL')
  if case=='capture-fault':
   need(cap['writeState']['trace']=='POISONED_FAILED_OR_UNCERTAIN','CAPTURE_FAILURE_POISON')
   run=read(out/'runner-events.json');need(len(run['faultWrites'])==1,'SINGLE_FAULTED_WRITE_NO_CLEANUP_REWRITE')
  record['rawCapsRespected']=True;record['privacyQualified']=True
  record['rawDescriptors']={n:pin(out/(n+'.bin')) for n in raw}
  record['rawSixSyscallCounts']={n:len(v) for n,v in calls.items()}
  record['originalCaptureFirstError']=cap['firstError'];record['captureForced']=cap['forced']
  need(record['readyBarrierComplete'] and not record['safetyFallbackUsed']
    and record['allKnownPidsExitedBeforeFallback'] and record['allOwnedChildrenReaped'] and not faults,
    'READY_COMPLETE_NO_FALLBACK_WITH_EXACT_OWNED_REAP')
  record['disposition']='QUALIFIED_FIXTURE_CONTAINMENT_ONLY'
 except BaseException as err:
  item={'type':type(err).__name__,'message':str(err)[:4096]}
  if record['firstError'] is None:record['firstError']=item
  else:record['secondaryErrors'].append(item)
  record.setdefault('rawCapsRespected',False);record.setdefault('privacyQualified',False)
  record['disposition']='UNQUALIFIED_FIXTURE_CONTAINMENT'
 put(out/'guard-result.json',record);return record

def main():
 # No wrapper can guarantee termination during uninterruptible kernel sleep or
 # SIGKILL of the independent guard. The actual known-pid cleanup receipts are
 # mandatory; a failure stays unqualified, and Node remains locked.
 need(len(sys.argv)==3 and sys.argv[1]=='--subject-sha','EXTERNAL_COMPLETE_SOURCE_PIN_REQUIRED')
 subject_path=HERE/'subject.json';need(pin(subject_path)['sha256']==sys.argv[2],'EXACT_CONTAINMENT_SOURCE_SUBJECT')
 subject=read(subject_path)
 need(context()==subject['hostContext'],'EXACT_HOST_CONTEXT')
 need(pin(Path(sys.executable).resolve())==subject['tools']['python'],'EXACT_PYTHON')
 for d in subject['files']:
  need(pin(d['path'])==d,'FROZEN_SOURCE_PIN');readable=Path(d['path']).lstat()
  need(stat.S_ISREG(readable.st_mode) and stat.S_IMODE(readable.st_mode)==0o600 and readable.st_uid==os.getuid(),'SOURCE_PRIVATE600')
 need(pin('/usr/bin/strace')==subject['tools']['strace'],'EXACT_CACHED_STRACE')
 # Guard is a separate process outside ptrace. Its subreaper role contains the
 # finite owned fixture graph only; no global ptrace/cgroup policy changes.
 libc=ctypes.CDLL(None,use_errno=True);need(libc.prctl(36,1,0,0,0)==0,'PR_SET_CHILD_SUBREAPER_REQUIRED')
 value=ctypes.c_int();need(libc.prctl(37,ctypes.byref(value),0,0,0)==0 and value.value==1,'SUBREAPER_CONFIRMED')
 OUT.mkdir(mode=0o700,exist_ok=False);records=[]
 for case in CASES:
  row=one(case,subject);records.append(row)
  # Initial failure preserved and stops subsequent cases; no automatic retries.
  if row['disposition']!='QUALIFIED_FIXTURE_CONTAINMENT_ONLY':break
 put(OUT/'raw-suite.json',{'schema':'e06-strace-guard-suite-unreviewed-v1','cases':records,
   'sourceSubject':pin(subject_path),'frozenAfter':[pin(d['path']) for d in subject['files']],
   'countsAreActual':True,'canonicalPass':False,'activationAcceptanceCreated':False})
 # This source does NOT emit trusted acceptance. Actual raw expectations/privacy
 # and real independent reviews must supply a separately pinned result subject.
 return 0 if len(records)==7 and all(r['disposition']=='QUALIFIED_FIXTURE_CONTAINMENT_ONLY' for r in records) else 2
if __name__=='__main__':raise SystemExit(main())
