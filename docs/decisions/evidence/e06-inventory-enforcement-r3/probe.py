"""SOURCE ONLY: one strict actual admission input-gate positive probe.
No import activates work. No LOCAL configuration/release or native work exists.
The unchanged actual local_worker_inputs function is called only after exact outer
source/config/release admission. Baseline rejection remains FAIL, never expected.
"""
import ast
import copy
import hashlib
import importlib.util
import importlib.machinery
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
ROOT='/home/peterhorvath/apps/bitcoin/NBDP'
CONFIG={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-r3/config.json', 'bytes': 11393, 'sha256': '0ffd70dae1444616607122249f2f265faca0ea831ea574b8b674e89eedb89dae'}
PYTHON={'path': '/home/peterhorvath/.miniforge3/bin/python3.13', 'bytes': 32959480, 'sha256': '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
ADMISSION={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/admission.py', 'bytes': 53263, 'sha256': '24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'}
SOURCE_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-qualification-current-source-r3/acceptance.json', 'bytes': 2485, 'sha256': 'cd32f47b3e7aa5e178ad82d84175115d87dab6e19c2bd5e99b0f341d668e964e'}
SOURCE_APPROVAL={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-qualification-current-source-r3/source-approval.json', 'bytes': 107717, 'sha256': 'e3e41bb6bae55d80702f9002cc99c72ad3a6345405a5043d3123dcafcbea685e'}
SOURCE_CLOSURE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-qualification-current-source-r3/source-closure.json', 'bytes': 102080, 'sha256': '76cfc1d55602c4c18f7adabde2b67679f3d828517a4cf4abefdf13d57029b100'}
CONTROL_APPROVAL={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-current-controls-r2/control-approval.json', 'bytes': 1488, 'sha256': 'c2c6d2b97ba4f25dbbb9074c079cd3ad29cbf9fa23aac709b31a97a273c0f5ee'}
CONTROL_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-current-controls-r2/control-acceptance.json', 'bytes': 1683, 'sha256': '96fb74a47dc5693bd45271142fc81a0d8e14c35814b9a77e26c73b15448f4ca9'}
QUALIFICATION_SCHEMA={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/qualification-schemas.json', 'bytes': 133680, 'sha256': 'dcbbbd2c9b84d5cd477718896f287f8abc6f6574e148a04421bc3a9043157a2b'}
ENV={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC', 'WS_NO_BUFFER_UTIL': '1', 'WS_NO_UTF_8_VALIDATE': '1'}


class Refusal(ValueError):
    pass

def need(value, code):
    if not value:
        raise Refusal(code)

def closed(value, keys):
    need(type(value) is dict and set(value) == set(keys), 'CLOSED_KEYS')
    return value

def equal(a,b):
    if type(a) is not type(b): return False
    if type(a) is dict: return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
    if type(a) is list: return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b

def pairs(rows):
    result={}
    for k,v in rows:
        need(k not in result,'DUPLICATE_KEY');result[k]=v
    return result

def loads(raw, historical=False):
    need(type(raw) is bytes and len(raw)<=33554432,'JSON_BOUND')
    def number(t):
        need(t!='-0','NEGATIVE_ZERO')
        n=int(t);need(abs(n)<=9007199254740991,'SAFE_INTEGER');return n
    def fraction(t):
        need(historical,'INTEGER_TOKEN_ONLY');n=float(t)
        need(math.isfinite(n) and (not n.is_integer() or abs(n)<=9007199254740991),'FINITE_HISTORICAL_TIMING')
        return n
    value=json.loads(raw.decode('utf-8','strict'),object_pairs_hook=pairs,parse_int=number,
                     parse_float=fraction,parse_constant=lambda _:need(False,'NONFINITE'))
    todo=[(value,0)];nodes=0
    while todo:
        v,depth=todo.pop();nodes+=1;need(depth<=64 and nodes<=100000,'JSON_STRUCTURE')
        if type(v) is str:need(not any(0xd800<=ord(c)<=0xdfff for c in v),'UNICODE_SCALAR')
        elif type(v) is dict:todo.extend((x,depth+1) for x in [*v,*v.values()])
        elif type(v) is list:todo.extend((x,depth+1) for x in v)
    return value

def descriptor(path):
    p=Path(path)
    need(p.is_absolute() and str(p.resolve(strict=True))==str(p) and not p.is_symlink(),'CANONICAL_FILE')
    digest=hashlib.sha256();size=0
    with p.open('rb') as handle:
        before=os.fstat(handle.fileno())
        need(stat.S_ISREG(before.st_mode) and before.st_size<=536870912,'FINITE_REGULAR_FILE')
        while block:=handle.read(1048576):size+=len(block);digest.update(block)
        after=os.fstat(handle.fileno())
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    need(identity(before)==identity(after) and size==before.st_size,'SOURCE_CHANGED_WHILE_HASHING')
    return dict(path=str(p),bytes=size,sha256=digest.hexdigest())


class OriginalPins:
    """Original expected pins never refresh to replacement bytes."""
    def __init__(self):self.values={};self.bytes=0
    def remember(self,pin):
        closed(pin,('path','bytes','sha256'))
        need(type(pin['bytes']) is int and 0<=pin['bytes']<=536870912
          and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']),
          'FINITE_DESCRIPTOR')
        previous=self.values.get(pin['path'])
        if previous is not None:need(equal(previous,pin),'CONFLICTING_ORIGINAL_PIN')
        else:
            need(len(self.values)<2048 and self.bytes+pin['bytes']<=4294967296,'FINITE_ORIGINAL_INVENTORY')
            self.values[pin['path']]=dict(pin);self.bytes+=pin['bytes']
        need(equal(descriptor(pin['path']),pin),'ORIGINAL_PIN_MISMATCH')
        return pin
    def read(self,pin,historical=False):
        self.remember(pin);need(pin['bytes']<=33554432,'BOUNDED_JSON_FILE')
        raw=Path(pin['path']).read_bytes()
        need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'READ_PIN_MISMATCH')
        return loads(raw,historical)
    def recheck(self):
        for pin in self.values.values():need(equal(descriptor(pin['path']),pin),'ORIGINAL_SOURCE_OR_INPUT_DRIFT')



def save(out,name,value):
    raw=(json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    need(len(raw)<=2097152,'BOUNDED_OUTER_OBSERVATION')
    target=out/name
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
    return descriptor(target)


def fact(error):
    return {'type':type(error).__name__,'message':str(error)[:16384]}


class NoCalls:
    """Trusted Python probe tripwires; not hostile-host/OS containment evidence."""
    def __init__(self):
        self.active=False;self.admission_imported=False
        self.counts={k:0 for k in ('processApiAttempts','forbiddenProjectImports',
          'networkApiAttempts','requestDeliveryAttempts','forbiddenFileWrites',
          'fullLocalVerifierAttempts','targetVerifierAttempts','transportVerifierAttempts')}
        self.admissionImports=0;self.restore=[]
    def deny(self,key,label):
        self.counts[key]+=1;raise Refusal('FORBIDDEN_SIDE_EFFECT:'+label)
    def install(self):
        for module,names in ((subprocess,('Popen','run','call','check_call','check_output','getoutput','getstatusoutput')),
          (os,('system','popen','fork','forkpty','posix_spawn','posix_spawnp','spawnl','spawnle',
          'spawnlp','spawnlpe','spawnv','spawnve','spawnvp','spawnvpe','execl','execle','execlp',
          'execlpe','execv','execve','execvp','execvpe','kill','killpg'))):
            for name in names:
                if hasattr(module,name):
                    original=getattr(module,name);self.restore.append((module,name,original))
                    def blocked(*args,_name=module.__name__+'.'+name,**kwargs):
                        self.deny('processApiAttempts',_name)
                    setattr(module,name,blocked)
        for cls in (importlib.machinery.SourceFileLoader,importlib.machinery.SourcelessFileLoader,
                    importlib.machinery.ExtensionFileLoader):
            original=cls.exec_module;self.restore.append((cls,'exec_module',original))
            def load(loader,module,_original=original):
                path=Path(loader.path).resolve(strict=True)
                if path.is_relative_to(Path(ROOT)):
                    if str(path)!=ADMISSION['path'] or self.admission_imported:
                        self.deny('forbiddenProjectImports',str(path))
                    self.admission_imported=True;self.admissionImports+=1
                return _original(loader,module)
            cls.exec_module=load
        def audit(event,args):
            if event in ('subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.exec'):
                self.deny('processApiAttempts',event)
            if event.startswith('socket.'):
                self.deny('networkApiAttempts',event)
            if self.active and event=='open':
                mode=args[1];flags=args[2]
                if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                    self.deny('forbiddenFileWrites','open-for-write')
        sys.addaudithook(audit)
        def profile(frame,event,arg):
            if not self.active:return
            if event=='call' and frame.f_code.co_filename==ADMISSION['path']:
                name=frame.f_code.co_name
                if name in ('verify_qualification','_verify_local','verify_qualification_job'):
                    self.deny('fullLocalVerifierAttempts',name)
                if name in ('verify','_verify_target'):
                    self.deny('targetVerifierAttempts',name)
                if name=='accepted_transport':self.deny('transportVerifierAttempts',name)
            if event=='c_call' and getattr(arg,'__name__','') in ('write','writev','send','sendall','sendto','sendmsg'):
                self.deny('requestDeliveryAttempts',getattr(arg,'__name__','unknown-write'))
        sys.setprofile(profile)
    def finish(self):
        self.active=False;sys.setprofile(None)
        for module,name,original in reversed(self.restore):setattr(module,name,original)


def execute(argv):
    begun=time.monotonic();pins=OriginalPins()
    need(len(argv)==6,'CLI probe.py CONFIG CONFIG_SHA RELEASE RELEASE_SHA SESSION')
    need(dict(os.environ)==ENV,'EXACT_OUTER_ENVIRONMENT');pins.remember(PYTHON)
    need(str(Path(sys.executable).resolve(strict=True))==PYTHON['path'],'FIXED_OUTER_INTERPRETER')
    own=descriptor(Path(__file__).resolve(strict=True));pins.remember(own)
    need(argv[1]==CONFIG['path'] and argv[2]==CONFIG['sha256'],'EXACT_CONFIG')
    config=pins.read(CONFIG)
    closed(config,('schema','state','runId','runRole','executionSession','sourceAcceptance','sourceApproval',
      'sourceClosure','controlApproval','controlAcceptance','qualificationSchema','admission','python',
      'environment','outputRoot','arguments','expectedGateOutcome','maximumPhaseMilliseconds',
      'futureQaOutputRootNotActivated','executionReleased'))
    need(config['schema']=='e06-inventory-real-gate-probe-config-v1'
      and config['state']=='PROPOSED_GATE_ARGUMENTS_ONLY_NOT_A_LOCAL_CONFIG'
      and config['expectedGateOutcome']=='ACCEPT' and config['executionReleased'] is False,
      'STRICT_REAL_GATE_ARGUMENTS_ONLY')
    for key,pin in (('sourceAcceptance',SOURCE_ACCEPTANCE),('sourceApproval',SOURCE_APPROVAL),
      ('sourceClosure',SOURCE_CLOSURE),('controlApproval',CONTROL_APPROVAL),
      ('controlAcceptance',CONTROL_ACCEPTANCE),('qualificationSchema',QUALIFICATION_SCHEMA),
      ('admission',ADMISSION),('python',PYTHON)):
        need(equal(config[key],pin),'EXACT_PINNED_CONFIG_OPERAND');pins.remember(pin)
    need(config['maximumPhaseMilliseconds']==120000 and equal(config['environment'],ENV),'FIXED_BUDGET_ENV')
    release_pin=descriptor(argv[3]);need(release_pin['sha256']==argv[4],'EXTERNAL_RELEASE_SHA')
    release=pins.read(release_pin)
    closed(release,('schema','decision','rootSession','executionSession','runRole','config',
      'sourceApproval','controlApproval','bootstrap','notAfterUtcMs'))
    need(release['schema']=='e06-inventory-input-probe-release-v1'
      and release['decision']=='RELEASE_EXACT_ADMISSION_INPUT_PROBE_ONLY'
      and release['rootSession']=='/root' and release['executionSession']==argv[5]==config['executionSession']
      and release['runRole']==config['runRole']=='primary' and equal(release['config'],CONFIG)
      and equal(release['sourceApproval'],SOURCE_APPROVAL) and equal(release['controlApproval'],CONTROL_APPROVAL)
      and equal(release['bootstrap'],own),'EXACT_OUTER_PROBE_RELEASE_NOT_LOCAL')
    need(type(release['notAfterUtcMs']) is int and 0<release['notAfterUtcMs']-(time.time_ns()//1000000)<=360000,
      'FINITE_ROOT_RELEASE')
    def live():
        need(time.monotonic()-begun<120 and (time.time_ns()//1000000)<release['notAfterUtcMs'],'OUTER_PHASE_OR_RELEASE_EXPIRED')
    source=pins.read(SOURCE_CLOSURE);approval=pins.read(SOURCE_APPROVAL);accepted=pins.read(SOURCE_ACCEPTANCE)
    need(type(source) is list and len(source)==449 and equal(approval['sourceClosure'],source)
      and approval['decision']==accepted['decision']=='ACCEPT_SOURCE_ONLY'
      and equal(accepted['subject'],SOURCE_CLOSURE)
      and equal(accepted['runtimeCompatibleSourceApproval'],SOURCE_APPROVAL)
      and accepted['executionReleased'] is False,'EXACT_CURRENT_SOURCE_PACK')
    need(len(approval['reviews'])==2 and {r['role'] for r in approval['reviews']}=={'qa','security'}
      and len({r['session'] for r in approval['reviews']})==2,'INDEPENDENT_SOURCE_REVIEWS')
    for row in approval['reviews']:
        actual=pins.read(accepted['independentReviews'][row['role']],True)
        need(row['session'] not in approval['authors'] and row['decision']=='ACCEPT_SOURCE_ONLY'
          and equal(row['subject'],SOURCE_CLOSURE) and actual['decision']==row['decision']
          and actual['session']==row['session'] and actual['role']==row['role']
          and equal(actual['subject'],SOURCE_CLOSURE) and actual['findings']==[],
          'ACTUAL_COMPLETE_SOURCE_REVIEW')
    control=pins.read(CONTROL_APPROVAL);control_acceptance=pins.read(CONTROL_ACCEPTANCE)
    need(control['decision']=='ACCEPT_CONTROLS_ONLY' and equal(control['sourceApproval'],SOURCE_APPROVAL),
      'CURRENT_CONTROL_APPROVAL')
    evidence=pins.read(control['actualControlEvidence'])
    need(equal(evidence['sourceApproval'],SOURCE_APPROVAL) and equal(evidence['sourceClosure'],source)
      and evidence['finalIntegrity'] is True and len(evidence['rows'])==14
      and all(r['matched'] is True for r in evidence['rows']),'CURRENT_ACTUAL_FOURTEEN_CONTROLS')
    need(control_acceptance['decision']=='ACCEPT_CONTROLS_ONLY'
      and control_acceptance['executionReleased'] is False
      and equal(control_acceptance['sourceApproval'],SOURCE_APPROVAL)
      and equal(control_acceptance['runtimeCompatibleControlApproval'],CONTROL_APPROVAL)
      and equal(control_acceptance['subject'],control['actualControlEvidence']),
      'ACTUAL_CONTROL_ACCEPTANCE_JOIN')
    need(len(control['reviews'])==2 and {r['role'] for r in control['reviews']}=={'qa','security'}
      and len({r['session'] for r in control['reviews']})==2,'INDEPENDENT_CONTROL_REVIEWS')
    for row in control['reviews']:
        report=pins.read(control_acceptance['independentReviews'][row['role']],True)
        need(row['session'] not in control['authors'] and row['decision']=='ACCEPT_CONTROLS_ONLY'
          and equal(row['subject'],control['actualControlEvidence'])
          and report['session']==row['session'] and report['role']==row['role']
          and report['decision']==row['decision'] and equal(report['subject'],row['subject'])
          and report['findings']==[],'ACTUAL_CONTROL_REVIEW_SCOPE')
    seen=set()
    for pin in source:
        live();need(pin['path'] not in seen,'DUPLICATE_SOURCE');seen.add(pin['path']);pins.remember(pin)
    for pin in (ADMISSION,PYTHON,QUALIFICATION_SCHEMA):need(any(equal(pin,d) for d in source),'FIXED_CURRENT_MEMBER')
    out=Path(config['outputRoot'])
    need(re.fullmatch('/tmp/e6n-inventory-primary-[a-f0-9]{12}',str(out)) and out.parent==Path('/tmp')
      and not os.path.lexists(out),'FRESH_OWNED_OUTER_OUTPUT')
    # This is only an outer observation directory, never the worker/output namespace.
    live();pins.recheck();out.mkdir(mode=0o700)
    args=config['arguments'];closed(args,('config','worker'))
    arguments=save(out,'gate-arguments.json',{'scope':'REAL_GATE_ARGUMENTS_ONLY_NOT_LOCAL_CONFIG',**args})
    traps=NoCalls();continuations=0;gate_error=None;late=[];gate_started=False;verified=[]
    try:
        traps.install();traps.active=True
        spec=importlib.util.spec_from_file_location('_e06_inventory_probe_admission',ADMISSION['path'])
        A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
        def call(inventory):
            nonlocal continuations,gate_started,gate_error
            try:
                live();mapping=A.fixed_source(source);defs=A.qualification_definitions()
                gate_started=True
                A.local_worker_inputs(copy.deepcopy(args['config']),copy.deepcopy(args['worker']),mapping,defs)
                live();continuations+=1
            except BaseException as error:gate_error=fact(error)
            try:inventory.recheck();live()
            except BaseException as error:late.append(fact(error))
            verified.extend({'path':name,'bytes':size,'sha256':sha}
              for name,size,sha in inventory._pins.values())
        A._with_inventory(call)
    except BaseException as error:
        if gate_error is None:gate_error=fact(error)
        else:late.append(fact(error))
    finally:traps.finish()
    try:pins.recheck();live()
    except BaseException as error:late.append(fact(error))
    zero=all(n==0 for n in traps.counts.values())
    qualified=gate_started and gate_error is None and continuations==1 and zero and not late
    result={'schema':'e06-inventory-input-gate-observation-v1','runId':config['runId'],
      'executionSession':config['executionSession'],'runRole':config['runRole'],
      'bootstrap':own,'config':CONFIG,'outerRootRelease':release_pin,
      'scope':'REAL_GATE_ARGUMENTS_ONLY_NOT_LOCAL_ADMISSION',
      'sourceApproval':SOURCE_APPROVAL,'sourceClosure':SOURCE_CLOSURE,'controlApproval':CONTROL_APPROVAL,
      'admission':ADMISSION,'gateFunction':'local_worker_inputs','gateArguments':arguments,
      'gateEntered':gate_started,'expectedGateOutcome':'ACCEPT',
      'observedGateOutcome':'ACCEPT' if gate_error is None and continuations==1 else 'REFUSE',
      'status':'PASS_SCOPED_GATE_PROBE_ONLY' if qualified else 'FAIL_EXPECTED_VALID_INPUT_REJECTED_OR_UNQUALIFIED',
      'firstError':gate_error,'secondaryErrors':late,'continuationCalls':continuations,
      'actualVerifiedReferents':verified,
      'sideEffectAttempts':traps.counts,'allowedAdmissionImports':traps.admissionImports,
      'futureNegativeMatrix':'NOT_EXECUTED; baseline must qualify first',
      'fullLocalVerifierExecuted':False,'nativeJobs':0,'requestDelivered':False,
      'elapsedMilliseconds':round((time.monotonic()-begun)*1000),
      'limits':['Actual one gate function only; no full LOCAL authority or runtime wiring proof.',
        'Tripwires cover trusted Python interfaces; no hostile-host/OS containment claim.',
        'No copied validators or simulated descriptor observations; actual original files and449mapping.']}
    receipt=save(out,'observation.json',result)
    print(json.dumps({'observation':receipt,'qualified':qualified,'continuationCalls':continuations},separators=(',',':')))
    return 0 if qualified else 1


if __name__=='__main__':
    try:code=execute(sys.argv)
    except BaseException as error:
        sys.stderr.write(type(error).__name__+': '+str(error)[:16384]+'\n');code=2
    raise SystemExit(code)
