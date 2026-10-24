"""SOURCE ONLY. Dedicated subreaper owns finite Python/strace fixtures, never Node.

All descendants of this otherwise child-free guard are owned fixture processes.
Registration is readiness, not ownership: census cleanup also owns unregistered
children through actual ancestry, held pidfds and an unreaped direct-child handle.
"""
from pathlib import Path
import ctypes,hashlib,json,os,re,select,signal,stat,subprocess,sys,time
HERE=Path(__file__).resolve().parent
CASES=['natural-zero','natural-refusal','deadline','interrupt','capture-fault','tracer-death','inner-parent-death']
OUT=HERE/'actual-containment-r1'
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
READY_SECONDS=3
CAPTURE_CUTOFF_SECONDS=7
ABSENCE_CUTOFF_SECONDS=7.25
GUARD_TOTAL_SECONDS=11
FAULT_SELF_EXPIRY_SECONDS=30
MAX_DESCENDANTS=16

def need(ok,message):
 if not ok:raise ValueError(message)
def put(p,v):
 raw=(json.dumps(v,indent=2)+'\n').encode();fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:need(f.write(raw)==len(raw),'COMPLETE_PRIVATE_METADATA_WRITE');f.flush();os.fsync(f.fileno())
def pin(p):
 p=Path(p);need(p.resolve(strict=True)==p and not p.is_symlink(),'CANONICAL_INPUT_PATH')
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):
 s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600,'PRIVATE_REGULAR_600')
 need(s.st_size<=1048576,'METADATA_CAP')
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'DUPLICATE_METADATA_KEY');d[k]=v
  return d
 return json.loads(p.read_bytes(),object_pairs_hook=pairs)
def context():
 return {'uid':os.getuid(),'gid':os.getgid(),'uidMap':Path('/proc/self/uid_map').read_text(),
 'gidMap':Path('/proc/self/gid_map').read_text(),'userNamespace':os.readlink('/proc/self/ns/user'),
 'mountNamespace':os.readlink('/proc/self/ns/mnt')}
def identity(pid):
 p=Path('/proc')/str(pid);s=p.stat();raw=(p/'stat').read_text();f=raw[raw.rindex(')')+2:].split()
 return {'pid':pid,'ppid':int(f[1]),'uid':s.st_uid,'starttime':int(f[19]),'session':int(f[3]),'cmdline':(p/'cmdline').read_bytes().hex()}
def children(pid):
 # Every fixture and guard is single-threaded; task children is actual Linux
 # parentage. Reparented tracees appear as guard children through subreaping.
 raw=(Path('/proc')/str(pid)/'task'/str(pid)/'children').read_text()
 pids=[int(x) for x in raw.split()];need(len(pids)<=MAX_DESCENDANTS,'FINITE_DIRECT_CHILDREN');return pids
def exited(fd):return bool(select.select([fd],[],[],0)[0])
def key(row):return row['pid'],row['starttime']
def ancestry_tree(root,deadline):
 queue=[root];seen=set();rows=[]
 while queue:
  need(time.monotonic()<deadline,'CENSUS_ABSOLUTE_DEADLINE');parent=queue.pop(0)
  try:kids=children(parent)
  except FileNotFoundError:continue  # Next full census catches subreaper adoption.
  for pid in kids:
   if pid in seen:continue
   seen.add(pid);need(len(seen)<=MAX_DESCENDANTS,'FINITE_OWNED_CENSUS')
   try:row=identity(pid)
   except FileNotFoundError:continue
   if row['ppid']!=parent:continue  # Parentage changed; next census records it.
   need(row['uid']==os.getuid(),'OWNED_DESCENDANT_UID_REQUIRED')
   rows.append(row);queue.append(pid)
 return rows

def enforce_times(began,now,ready,receipt,absence):
 need(FAULT_SELF_EXPIRY_SECONDS>GUARD_TOTAL_SECONDS,'FAULT_LIFETIME_MUST_EXCEED_WHOLE_GUARD')
 if not ready:need(now<began+READY_SECONDS,'REGISTRATION_READY_DEADLINE')
 if receipt is None:need(now<began+CAPTURE_CUTOFF_SECONDS,'CAPTURE_RECEIPT_CUTOFF')
 else:need(receipt<=began+CAPTURE_CUTOFF_SECONDS,'LATE_CAPTURE_RECEIPT')
 if absence is not None:need(absence<=began+ABSENCE_CUTOFF_SECONDS,'LATE_OWNED_ABSENCE')
 need(now<=began+ABSENCE_CUTOFF_SECONDS,'OWNED_ABSENCE_CUTOFF')

class SafetyOwner:
 """Dedicated scope only. Never relies on successful registration to clean up."""
 def __init__(self,root,deadline):
  self.root=root;self.deadline=deadline;self.handles=[];self.known={};self.events=[];self.faults=[];self.fallback=False
 def fault(self,e):
  item={'type':type(e).__name__,'message':str(e)[:4096]}
  if len(self.faults)<32:self.faults.append(item)
 def launch(self,*args,**kwargs):
  handle=subprocess.Popen(*args,**kwargs)
  self.handles.append({'handle':handle,'pid':handle.pid,'reaped':False})  # FIRST operation after Popen.
  # A pidfd/identity/ready-write exception cannot discard this owned unreaped
  # direct-child handle. Failure path census/reap is independent of this call.
  self.census()
  return handle
 def census(self):
  rows=ancestry_tree(self.root,self.deadline)
  for row in rows:
   k=key(row)
   if k in self.known:continue
   held={'identity':row,'fd':None,'reaped':False,'registered':False}
   self.known[k]=held  # Retain ancestry/identity BEFORE pidfd open can fail.
   try:
    fd=os.pidfd_open(row['pid'],0);held['fd']=fd
    after=identity(row['pid'])
    need(key(after)==k and after['uid']==row['uid'],'PIDFD_STARTTIME_UID_IDENTITY')
    need('Pid:\t'+str(row['pid']) in Path('/proc/self/fdinfo/'+str(fd)).read_text().splitlines(),'PIDFD_EXACT_PID')
    self.events.append({'operation':'held-owned-descendant','identity':after,'pidfd':fd})
   except ProcessLookupError:pass  # Already exited; retain identity/actual reap.
   except BaseException as e:self.fault(e)
  return rows
 def find(self,pid):
  rows=[v for k,v in self.known.items() if k[0]==pid and not v['reaped']]
  need(len(rows)==1,'EXACT_ONE_OWNED_UNREAPED_IDENTITY');return rows[0]
 def register(self,row,argv,parent):
  self.census();v=self.find(row['pid']);actual=identity(row['pid'])
  need(row==actual and key(actual)==key(v['identity']) and actual['uid']==os.getuid()
    and actual['ppid']==parent,'EXACT_READY_OWNED_PARENT_IDENTITY')
  need(v['fd'] is not None and not exited(v['fd']),'READY_REQUIRES_LIVE_HELD_PIDFD')
  need(bytes.fromhex(actual['cmdline']).split(b'\0')[:-1]==[os.fsencode(x) for x in argv],'EXACT_READY_CMDLINE')
  v['registered']=True;self.events.append({'operation':'ready-registered','identity':actual});return v
 def send(self,v,sig,reason):
  need(not v['reaped'],'NO_POST_REAP_SIGNAL')
  if v['fd'] is not None:
   if exited(v['fd']):return False
   signal.pidfd_send_signal(v['fd'],sig,None,0)
  else:
   # Only an actual immediate unreaped direct child may use numeric fallback.
   # WNOWAIT confirms it is still our child and cannot have a reused PID.
   # Nonchildren with failed pidfd are NOT signalled numerically.
   row=v['identity'];live=identity(row['pid'])
   need(key(live)==key(row) and live['uid']==os.getuid() and live['ppid']==self.root,'DIRECT_UNREAPED_FALLBACK_IDENTITY')
   info=os.waitid(os.P_PID,row['pid'],os.WEXITED|os.WNOHANG|os.WNOWAIT)
   if info is not None:return False
   os.kill(row['pid'],sig)
  self.events.append({'operation':'signal-owned-identity','pid':v['identity']['pid'],
   'starttime':v['identity']['starttime'],'signal':int(sig),'reason':reason,'pidfd':v['fd']})
  return True
 def reap(self):
  # Actual direct adopted descendants are reaped only after WNOWAIT. ECHILD plus
  # an exited held pidfd records original-parent reaping, never live absence.
  for v in self.known.values():
   if v['reaped']:continue
   pid=v['identity']['pid']
   try:
    current=identity(pid)
    if key(current)!=key(v['identity']):
     need(v['fd'] is not None and exited(v['fd']),'OLD_IDENTITY_EXIT_BEFORE_REUSE')
     v['reaped']=True;self.events.append({'operation':'original-reaped-before-pid-reuse','pid':pid,'starttime':v['identity']['starttime']});continue
    need(current['uid']==v['identity']['uid'],'EXACT_REAP_OWNER_UID')
    info=os.waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
    if info is None:continue
    need(not any(x['pid']==pid and x['reaped'] for x in self.handles),'NO_DOUBLE_REAP')
    handle=next((x for x in self.handles if x['pid']==pid),None)
    if handle is not None:status=handle['handle'].wait(timeout=0);handle['reaped']=True
    else:
     got,status=os.waitpid(pid,os.WNOHANG);need(got==pid,'EXACT_WNOWAIT_REAP_PID')
    v['reaped']=True;self.events.append({'operation':'reaped-owned','pid':pid,'starttime':v['identity']['starttime'],'status':status})
   except FileNotFoundError:
    if not children(self.root) and all(x['reaped'] for x in self.handles):
     v['reaped']=True;self.events.append({'operation':'original-identity-absent-after-parent-reap','pid':pid,'starttime':v['identity']['starttime']})
   except ChildProcessError:
    if v['fd'] is not None and exited(v['fd']) and not children(self.root) and all(x['reaped'] for x in self.handles):
     v['reaped']=True;self.events.append({'operation':'already-reaped-by-owned-parent','pid':pid,'starttime':v['identity']['starttime']})
   except BaseException as e:self.fault(e)
  # Handles are retained even if initial census/identity failed completely.
  for item in self.handles:
   if item['reaped']:continue
   try:
    info=os.waitid(os.P_PID,item['pid'],os.WEXITED|os.WNOHANG|os.WNOWAIT)
    if info is not None:
     status=item['handle'].wait(timeout=0);item['reaped']=True
     self.events.append({'operation':'reaped-retained-launch-handle','pid':item['pid'],'status':status})
   except BaseException as e:self.fault(e)
 def no_live(self):
  rows=self.census();self.reap()
  return not rows and not children(self.root) and all(x['reaped'] for x in self.handles) and all(v['reaped'] for v in self.known.values())
 def cleanup(self):
  self.fallback=True;empty=0
  # Repeated complete actual ancestry census catches formerly unregistered or
  # adopted children even after Popen/pidfd/identity/ready-JSON failures.
  while time.monotonic()<self.deadline:
   try:
    self.census()
    # If census previously failed, held actual launch handles still retain PID
    # ownership until reap. Reacquire actual direct children, never unowned PIDs.
    for item in self.handles:
     if item['reaped']:continue
     try:
      row=identity(item['pid'])
      need(row['ppid']==self.root and row['uid']==os.getuid(),'RETAINED_HANDLE_PARENT_UID')
      if key(row) not in self.known:self.known[key(row)]={'identity':row,'fd':None,'reaped':False,'registered':False}
     except FileNotFoundError:pass
    for v in reversed(list(self.known.values())):
     if v['reaped']:continue
     try:self.send(v,signal.SIGKILL,'SAFETY_FALLBACK_ALWAYS_FAIL')
     except ProcessLookupError:pass
     except BaseException as e:self.fault(e)
    self.reap()
    if self.no_live():
     empty+=1
     if empty>=2:return True
    else:empty=0
   except BaseException as e:self.fault(e)
   time.sleep(.01)
  self.fault(TimeoutError('OWNED_DESCENDANT_CENSUS_CLEANUP_INCOMPLETE'));return False
 def close(self):
  for v in self.known.values():
   if v['fd'] is not None:os.close(v['fd'])

def process_registrations(out,owner,runner,case,registered):
 # A private pre-fork ACK gates runner->strace; each role's ACK gates its
 # declaration of a one-child spawn intent before the next subprocess is born.
 if 'runner' not in registered and (out/'runner-ready.json').exists():
  data=read(out/'runner-ready.json');need(set(data)=={'pid'} and data['pid']==runner.pid,'EXACT_RUNNER_READY')
  row=identity(runner.pid);argv=[sys.executable,'-I','-B',str(HERE/'runner.py'),str(out),case]
  registered['runner']=owner.register(row,argv,os.getpid());put(out/'runner-ack.json',{'pid':runner.pid})
 if 'tracer' not in registered and (out/'tracer-ready.json').exists():
  d=read(out/'tracer-ready.json');registered['tracer']=owner.register(identity(d['pid']),d['argv'],runner.pid)
 for role,parent_role in [('parent','tracer'),('child','parent'),('grandchild','child')]:
  if role not in registered and parent_role in registered and (out/(role+'-ready.json')).exists():
   d=read(out/(role+'-ready.json'));argv=[sys.executable,'-I','-B',str(HERE/'fixture.py'),str(out),role,case]
   registered[role]=owner.register(d,argv,registered[parent_role]['identity']['pid'])
   put(out/(role+'-ack.json'),{'pid':d['pid'],'starttime':d['starttime']})
 for role,next_role in [('parent','child'),('child','grandchild')]:
  ack=out/(role+'-spawn-ack.json');intent=out/(role+'-spawn-intent.json')
  if role in registered and intent.exists() and not ack.exists():
   d=read(intent);need(set(d)=={'parent','nextRole'} and d['nextRole']==next_role
     and key(d['parent'])==key(registered[role]['identity']),'EXACT_PRE_FORK_INTENT')
   put(ack,{'nextRole':next_role,'parentPid':d['parent']['pid']})


def one(case,subject):
 out=OUT/case;out.mkdir(mode=0o700);began=time.monotonic();owner=SafetyOwner(os.getpid(),began+GUARD_TOTAL_SECONDS)
 need(not children(os.getpid()),'DEDICATED_CHILD_FREE_GUARD_BEFORE_CASE')
 registered={};ready=False;trigger=False;receipt=None;absence=None;record={};runner=None;stdout_fd=None;stderr_fd=None
 try:
  stdout_fd=os.open(out/'runner-stdout.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  stderr_fd=os.open(out/'runner-stderr.bin',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  def limits():
   import resource
   resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
  argv=[sys.executable,'-I','-B',str(HERE/'runner.py'),str(out),case]
  runner=owner.launch(argv,cwd=HERE,env=ENV,stdin=subprocess.DEVNULL,stdout=stdout_fd,stderr=stderr_fd,
    start_new_session=True,preexec_fn=limits)
  while True:
   now=time.monotonic();enforce_times(began,now,ready,receipt,absence)
   owner.census();need(not owner.faults,'OWNERSHIP_CENSUS_FAULT')
   process_registrations(out,owner,runner,case,registered)
   if not ready and all(k in registered for k in ['runner','tracer','parent','child','grandchild']):
    sessions=[registered[k]['identity']['session'] for k in ['parent','child','grandchild']]
    need(len(set(sessions))==3,'THREE_DISTINCT_SESSIONS');ready=True
    put(out/'all-ready.json',{'sessions':sessions,'allHeldBeforeFault':True,'atMonotonicNs':time.monotonic_ns()})
   if ready:need(all(v['registered'] for v in owner.known.values()),'UNREGISTERED_OWNED_DESCENDANT_AFTER_READY')
   exercised=ready and all((out/(role+'-exercised.json')).exists() for role in ['parent','child','grandchild'])
   if exercised and not trigger:
    if case=='capture-fault':put(out/'fault-arm.json',{'allThreeExercised':True});trigger=True
    elif case=='interrupt':owner.send(registered['runner'],signal.SIGINT,'INTENTIONAL_OBSERVER_INTERRUPT');trigger=True
    elif case=='tracer-death':owner.send(registered['tracer'],signal.SIGKILL,'INTENTIONAL_TRACER_DEATH');trigger=True
    elif case=='inner-parent-death':owner.send(registered['parent'],signal.SIGKILL,'INTENTIONAL_INNER_PARENT_DEATH');trigger=True
   if (out/'observer-capture.json').exists() and receipt is None:
    # A late receipt is an explicit failure even if the fixture independently dies.
    receipt=time.monotonic();enforce_times(began,receipt,ready,receipt,None)
   if ready and receipt is not None and owner.no_live():
    absence=time.monotonic();enforce_times(began,absence,ready,receipt,absence);break
   time.sleep(.01)
 except BaseException as e:owner.fault(e)
 finally:
  if owner.faults or absence is None:cleanup_complete=owner.cleanup()
  else:cleanup_complete=True
  for fd in [stdout_fd,stderr_fd]:
   if fd is not None:os.close(fd)
 record={'schema':'e06-strace-owned-fixture-guard-v2','case':case,'readyBarrierComplete':ready,
  'safetyFallbackUsed':owner.fallback,'allKnownPidsExitedBeforeFallback':absence is not None and not owner.fallback,
  'completeOwnedDescendantCensusEmpty':cleanup_complete and not children(os.getpid()),
  'allOwnedChildrenReaped':all(x['reaped'] for x in owner.handles) and all(v['reaped'] for v in owner.known.values()),
  'events':owner.events,'firstError':owner.faults[0] if owner.faults else None,'secondaryErrors':owner.faults[1:16],
  'elapsedNs':int((time.monotonic()-began)*1000000000),'guardTotalCeilingSeconds':GUARD_TOTAL_SECONDS,
  'readyDeadlineSeconds':READY_SECONDS,'captureReceiptCutoffSeconds':CAPTURE_CUTOFF_SECONDS,
  'absenceCutoffSeconds':ABSENCE_CUTOFF_SECONDS,'faultSelfExpirySeconds':FAULT_SELF_EXPIRY_SECONDS,
  'captureReceiptAtElapsedNs':None if receipt is None else int((receipt-began)*1000000000),
  'absenceAtElapsedNs':None if absence is None else int((absence-began)*1000000000),
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
  record['observerCapture']=pin(out/'observer-capture.json')
  record['rawSixSyscallCounts']={n:len(v) for n,v in calls.items()}
  record['originalCaptureFirstError']=cap['firstError'];record['captureForced']=cap['forced']
  need(record['readyBarrierComplete'] and not record['safetyFallbackUsed']
    and record['allKnownPidsExitedBeforeFallback'] and record['allOwnedChildrenReaped']
    and record['completeOwnedDescendantCensusEmpty'] and not owner.faults,
    'READY_COMPLETE_NO_FALLBACK_WITH_EXACT_OWNED_REAP')
  record['disposition']='QUALIFIED_FIXTURE_CONTAINMENT_ONLY'
 except BaseException as err:
  item={'type':type(err).__name__,'message':str(err)[:4096]}
  if record['firstError'] is None:record['firstError']=item
  else:record['secondaryErrors'].append(item)
  record.setdefault('rawCapsRespected',False);record.setdefault('privacyQualified',False)
  record['disposition']='UNQUALIFIED_FIXTURE_CONTAINMENT'
 owner.close();put(out/'guard-result.json',record);return record

def require_modeled_acceptance(subject_pin,subject,pure_pin):
    a=read(Path(pure_pin['path']));need(pin(pure_pin['path'])==pure_pin,'ACTUAL_MODELED_ACCEPTANCE_PIN')
    need(a['schema']=='e06-strace-guard-pure-acceptance-v1'
      and a['decision']=='ACCEPT_GUARD11_ADMISSION14_MODELED_CONTROLS_ONLY'
      and a['sourceSubject']==subject_pin and a['actualControls']==11 and a['actualAdmissionControls']==14,'ACTUAL_ELEVEN_GUARD_MODELS')
    whole_pin=a['observerWholeSourceSubject'];need(pin(whole_pin['path'])==whole_pin,'ACTUAL_REVIEWED_WHOLE_SOURCE_PIN')
    whole=read(Path(whole_pin['path']));need(whole['containmentSourceSubject']==subject_pin
      and whole['observer']==subject['observer'] and whole['captureHelper']==subject['observerHelper'],
      'WHOLE_REVIEWED_OBSERVER_HELPER_FIXTURE_JOIN')
    for d in whole['files']:need(pin(d['path'])==d,'WHOLE_CURRENT_SOURCE_CLOSURE')
    result_pin=a['controlSubject'];need(pin(result_pin['path'])==result_pin,'ACTUAL_GUARD_RESULT_PIN')
    result=read(Path(result_pin['path']))
    need(result['schema']=='e06-modeled-guard-controls-actual-subject-v1'
      and result['sourceSubject']==subject_pin and result['observerWholeSourceSubject']==whole_pin
      and result['actualControls']==result['passed']==11 and result['failed']==result['errors']==result['skipped']==0
      and result['actualAdmissionControls']==result['admissionPassed']==14
      and result['admissionFailed']==result['admissionErrors']==result['admissionSkipped']==0,
      'COMPLETE_ACTUAL_GUARD_MODEL_RESULT')
    for d in result['files']:need(pin(d['path'])==d,'GUARD_MODEL_ACTUAL_RAW_PIN')
    for field,decision,review_subject in [('reviews','ACCEPT_GUARD11_ADMISSION14_MODELED_CONTROLS_ONLY',result_pin),
      ('sourceReviews','ACCEPT_DIAGNOSTIC_SOURCE_CONFIG_ONLY',whole_pin)]:
        need(len(a[field])==2 and {r['role'] for r in a[field]}=={'qa','security'}
          and len({r['session'] for r in a[field]})==2,'TWO_INDEPENDENT_ACTUAL_SOURCE_AND_RESULT_REVIEWS')
        for r in a[field]:
            need(set(r)=={'role','session','decision','subject'} and r['decision']==decision
              and r['subject']==review_subject and r['session'] not in whole['authors']
              and r['session'] not in a['authors'] and r['session']!=a['operator'],
              'NONAUTHOR_NONOPERATOR_ACTUAL_GUARD_REVIEW')


def main():
 # No wrapper can guarantee termination during uninterruptible kernel sleep or
 # SIGKILL of the independent guard. The actual known-pid cleanup receipts are
 # mandatory; a failure stays unqualified, and Node remains locked.
 need(len(sys.argv)==5 and sys.argv[1]=='--subject-sha' and sys.argv[3]=='--pure-acceptance-sha',
   'EXTERNAL_SOURCE_AND_ACTUAL_MODELED_ACCEPTANCE_PINS_REQUIRED')
 subject_path=HERE/'subject.json';need(pin(subject_path)['sha256']==sys.argv[2],'EXACT_CONTAINMENT_SOURCE_SUBJECT')
 subject=read(subject_path)
 need(context()==subject['hostContext'],'EXACT_HOST_CONTEXT')
 need(pin(Path(sys.executable).resolve())==subject['tools']['python'],'EXACT_PYTHON')
 for d in subject['files']:
  need(pin(d['path'])==d,'FROZEN_SOURCE_PIN');readable=Path(d['path']).lstat()
  need(stat.S_ISREG(readable.st_mode) and stat.S_IMODE(readable.st_mode)==0o600 and readable.st_uid==os.getuid(),'SOURCE_PRIVATE600')
 need(pin('/usr/bin/strace')==subject['tools']['strace'],'EXACT_CACHED_STRACE')
 pure_path=HERE/'actual-guard-regression-acceptance.json';pure_pin=pin(pure_path)
 need(pure_pin['sha256']==sys.argv[4],'EXTERNAL_ACTUAL_MODELED_ACCEPTANCE_SHA')
 require_modeled_acceptance(pin(subject_path),subject,pure_pin)
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
