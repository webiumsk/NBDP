"""SOURCE ONLY: exact current-source grammar-control outer runner.
No project import or activation on module import. Source/control review and a new
root grammar-only release are mandatory. No full input gate, LOCAL or native job.
"""
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
CONFIG={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-opaque-inventory-controls-r1/config.json', 'bytes': 2982, 'sha256': '265c005523b2fbb8a79ef0ed0561f1ab2e02b416c763275a48f89a10a7b8e37c'}
PYTHON={'path': '/home/peterhorvath/.miniforge3/bin/python3.13', 'bytes': 32959480, 'sha256': '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
ADMISSION={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/admission.py', 'bytes': 53263, 'sha256': '24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'}
SUITE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-opaque-inventory-remediation-r1/grammar_controls.py', 'bytes': 8326, 'sha256': '77fb47deff4657ebcd4717f0f8992d350468923aa22c4ee7551588e5acc317ce'}
SOURCE_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-qualification-current-source-r3/acceptance.json', 'bytes': 2485, 'sha256': 'cd32f47b3e7aa5e178ad82d84175115d87dab6e19c2bd5e99b0f341d668e964e'}
SOURCE_APPROVAL={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-qualification-current-source-r3/source-approval.json', 'bytes': 107717, 'sha256': 'e3e41bb6bae55d80702f9002cc99c72ad3a6345405a5043d3123dcafcbea685e'}
SOURCE_CLOSURE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-qualification-current-source-r3/source-closure.json', 'bytes': 102080, 'sha256': '76cfc1d55602c4c18f7adabde2b67679f3d828517a4cf4abefdf13d57029b100'}
BRIDGE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/bridge-schemas.json', 'bytes': 158719, 'sha256': '89173066418eddd16f1d2a14ecee4b04470072385c1883aab48a01dd6e41281a'}
SYNTHETIC_FILE='/tmp/e6n-opaque-grammar-6de715bf226e/raw-read-boundary.bin'
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
          'fullLocalVerifierAttempts','targetVerifierAttempts','transportVerifierAttempts','inputGateProbeAttempts')}
        self.admissionImports=0;self.restore=[];self.moduleImports={};self.syntheticOpens=0;self.syntheticTruncates=0;self.truncating=False
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
                    if str(path) not in (ADMISSION['path'],SUITE['path']) or self.moduleImports.get(str(path),0):
                        self.deny('forbiddenProjectImports',str(path))
                    self.moduleImports[str(path)]=1
                    if str(path)==ADMISSION['path']:self.admissionImports+=1
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
                    required=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW
                    relevant=required|os.O_RDWR|os.O_TRUNC|os.O_APPEND
                    if str(args[0])!=SYNTHETIC_FILE or mode is not None or not isinstance(flags,int) or flags&relevant!=required or self.syntheticOpens!=0:
                        self.deny('forbiddenFileWrites','open-for-write')
                    self.syntheticOpens+=1
            if self.active and event=='os.truncate' and not self.truncating:
                self.deny('forbiddenFileWrites','unapproved-truncate')
        original_truncate=os.ftruncate;self.restore.append((os,'ftruncate',original_truncate))
        def sparse(fd,length):
            if type(fd) is not int or type(length) is not int or length!=33554433 or self.syntheticTruncates or os.readlink('/proc/self/fd/'+str(fd))!=SYNTHETIC_FILE:
                self.deny('forbiddenFileWrites','unapproved-ftruncate')
            st=os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o600 or st.st_size!=0:
                self.deny('forbiddenFileWrites','unowned-sparse-file')
            self.syntheticTruncates+=1;self.truncating=True
            try:return original_truncate(fd,length)
            finally:self.truncating=False
        os.ftruncate=sparse
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
                if name=='local_worker_inputs':self.deny('inputGateProbeAttempts',name)
            if event=='c_call' and getattr(arg,'__name__','') in ('write','writev','send','sendall','sendto','sendmsg'):
                self.deny('requestDeliveryAttempts',getattr(arg,'__name__','unknown-write'))
        sys.setprofile(profile)
    def finish(self):
        self.active=False;sys.setprofile(None)
        for module,name,original in reversed(self.restore):setattr(module,name,original)



def execute(argv):
    started=time.monotonic();pins=OriginalPins()
    need(len(argv)==6,'CLI outer.py CONFIG CONFIG_SHA RELEASE RELEASE_SHA SESSION')
    need(dict(os.environ)==ENV,'EXACT_OUTER_ENVIRONMENT');pins.remember(PYTHON)
    need(str(Path(sys.executable).resolve(strict=True))==PYTHON['path'],'FIXED_OUTER_INTERPRETER')
    own=descriptor(Path(__file__).resolve(strict=True));pins.remember(own)
    need(argv[1]==CONFIG['path'] and argv[2]==CONFIG['sha256'],'EXACT_EXTERNAL_CONFIG')
    c=pins.read(CONFIG)
    closed(c,('schema','state','ready','runId','executionSession','runRole','sourceAcceptance',
      'sourceApproval','sourceClosure','admission','suite','bridgeSchema','python','environment',
      'outputRoot','maximumSyntheticFileBytes','maximumPhaseMilliseconds','expectedControlIds','executionReleased'))
    need(c['schema']=='e06-opaque-grammar-controls-config-v1'
      and c['state']=='PROPOSED_SOURCE_GRAMMAR_ONLY_NOT_LOCAL_OR_GATE_PROBE'
      and c['ready'] is True and c['executionReleased'] is False,'PROPOSED_GRAMMAR_CONFIG_ONLY')
    for key,pin in (('sourceAcceptance',SOURCE_ACCEPTANCE),('sourceApproval',SOURCE_APPROVAL),
      ('sourceClosure',SOURCE_CLOSURE),('admission',ADMISSION),('suite',SUITE),('bridgeSchema',BRIDGE),('python',PYTHON)):
        need(equal(c[key],pin),'EXACT_FIXED_CONFIG_PIN');pins.remember(pin)
    need(equal(c['environment'],ENV) and c['maximumPhaseMilliseconds']==120000
      and c['maximumSyntheticFileBytes']==33554433 and len(c['expectedControlIds'])==21
      and len(set(c['expectedControlIds']))==21,'FIXED_ENV_BUDGET_EXPECTATIONS')
    rd=descriptor(argv[3]);need(rd['sha256']==argv[4],'EXTERNAL_RELEASE_SHA');release=pins.read(rd)
    closed(release,('schema','decision','rootSession','executionSession','runRole','config','sourceApproval','bootstrap','suite','notAfterUtcMs'))
    need(release['schema']=='e06-opaque-grammar-control-release-v1'
      and release['decision']=='RELEASE_EXACT_OPAQUE_GRAMMAR_CONTROLS_ONLY'
      and release['rootSession']=='/root' and release['executionSession']==argv[5]==c['executionSession']
      and release['runRole']==c['runRole']=='primary' and equal(release['config'],CONFIG)
      and equal(release['sourceApproval'],SOURCE_APPROVAL) and equal(release['bootstrap'],own)
      and equal(release['suite'],SUITE),'EXACT_ROOT_GRAMMAR_ONLY_RELEASE')
    need(type(release['notAfterUtcMs']) is int and 0<release['notAfterUtcMs']-time.time_ns()//1000000<=360000,'FINITE_ROOT_RELEASE')
    def live():
        need(time.monotonic()-started<120 and time.time_ns()//1000000<release['notAfterUtcMs'],'PHASE_OR_RELEASE_EXPIRED')
    closure=pins.read(SOURCE_CLOSURE);approval=pins.read(SOURCE_APPROVAL);accepted=pins.read(SOURCE_ACCEPTANCE)
    need(type(closure) is list and len(closure)==449 and equal(approval['sourceClosure'],closure)
      and approval['decision']==accepted['decision']=='ACCEPT_SOURCE_ONLY'
      and equal(accepted['subject'],SOURCE_CLOSURE)
      and equal(accepted['runtimeCompatibleSourceApproval'],SOURCE_APPROVAL)
      and accepted['executionReleased'] is False,'ACTUAL_COMPLETE_SOURCE_PACK')
    rows=approval['reviews'];need(len(rows)==2 and {r['role'] for r in rows}=={'qa','security'}
      and len({r['session'] for r in rows})==2,'INDEPENDENT_SOURCE_REVIEWS')
    for row in rows:
        report=pins.read(accepted['independentReviews'][row['role']],True)
        need(row['session'] not in approval['authors'] and row['decision']=='ACCEPT_SOURCE_ONLY'
          and equal(row['subject'],SOURCE_CLOSURE) and report['decision']==row['decision']
          and report['session']==row['session'] and report['role']==row['role']
          and equal(report['subject'],SOURCE_CLOSURE) and report['findings']==[],'ACTUAL_SOURCE_REVIEW_JOIN')
    mapping={}
    for pin in closure:
        live();need(pin['path'] not in mapping,'DUPLICATE_SOURCE');pins.remember(pin);mapping[pin['path']]=pin
    for pin in (ADMISSION,PYTHON,BRIDGE):need(equal(mapping.get(pin['path']),pin),'CURRENT_SOURCE_MEMBER')
    out=Path(c['outputRoot']);need(re.fullmatch('/tmp/e6n-opaque-grammar-[a-f0-9]{12}',str(out))
      and str(out/'raw-read-boundary.bin')==SYNTHETIC_FILE and not os.path.lexists(out),'FRESH_EXACT_OWNED_OUTPUT')
    live();pins.recheck();out.mkdir(mode=0o700)
    traps=NoCalls();first=None;secondary=[];result=None;source_refs=[];partial_rows=[]
    try:
        traps.install();traps.active=True
        spec=importlib.util.spec_from_file_location('_e06_grammar_admission',ADMISSION['path'])
        A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
        def source_only(inventory):
            original=None
            try:
                amap=A.fixed_source(closure);defs=A.document(A.DATA['bridge-schemas.json'])['definitions']
                A.source_approval(SOURCE_APPROVAL,closure,defs);A.fixed_prerequisites(amap)
            except BaseException as error:original=error
            try:inventory.recheck();live()
            except BaseException as error:
                if original is None:original=error
                else:secondary.append(fact(error))
            source_refs.extend({'path':name,'bytes':size,'sha256':sha} for name,size,sha in inventory._pins.values())
            if original is not None:raise original
        A._with_inventory(source_only)
        spec=importlib.util.spec_from_file_location('_e06_grammar_suite',SUITE['path'])
        G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
        live();result=G.evaluate(A,c);live()
        need(result['matched'] is True and result['checks']==21
          and [r['id'] for r in result['rows']]==c['expectedControlIds']
          and all(r['matched'] is True for r in result['rows'])
          and equal(result['admission'],ADMISSION) and equal(result['sourceApproval'],SOURCE_APPROVAL)
          and equal(result['sourceClosure'],SOURCE_CLOSURE)
          and result['actualFullInventoryGateExecuted'] is False and result['nativeJobs']==0,
          'EXACT_ACTUAL_TWENTY_ONE_SCOPED_ROWS')
        need(all(n==0 for n in traps.counts.values()) and traps.admissionImports==1
          and traps.moduleImports=={ADMISSION['path']:1,SUITE['path']:1}
          and traps.syntheticOpens==1 and traps.syntheticTruncates==1,'ZERO_FORBIDDEN_EFFECTS_EXACT_ALLOWED_ARTIFACT')
    except BaseException as error:
        first=fact(error)
        tb=error.__traceback__
        while tb is not None:
            frame=tb.tb_frame
            if frame.f_code.co_filename==SUITE['path'] and frame.f_code.co_name=='evaluate':
                observed=frame.f_locals.get('rows')
                if type(observed) is list:partial_rows=[dict(row) for row in observed]
            tb=tb.tb_next
    finally:traps.finish()
    try:pins.recheck();live()
    except BaseException as error:secondary.append(fact(error))
    actual=save(out,'suite-result.json',result) if result is not None else None
    partial=save(out,'partial-suite-rows.json',partial_rows) if partial_rows else None
    sparse=descriptor(SYNTHETIC_FILE) if Path(SYNTHETIC_FILE).is_file() else None
    qualified=first is None and not secondary and actual is not None
    capture={'schema':'e06-opaque-grammar-control-capture-v1','bootstrap':own,'config':CONFIG,
      'release':rd,'sourceApproval':SOURCE_APPROVAL,'sourceClosure':SOURCE_CLOSURE,'suite':SUITE,
      'suiteResult':actual,'partialSuiteRows':partial,'firstError':first,'secondaryErrors':secondary,'qualified':qualified,
      'forbiddenAttempts':traps.counts,'allowedProjectImports':traps.moduleImports,
      'allowedSparseFileOpens':traps.syntheticOpens,'allowedSparseTruncates':traps.syntheticTruncates,
      'actualSparseFile':sparse,'sourceVerifiedReferents':source_refs,
      'fullInputGateCalls':0,'localVerifierCalls':0,'targetVerifierCalls':0,'nativeJobs':0,
      'elapsedMilliseconds':round((time.monotonic()-started)*1000),
      'limits':['Seventeen private-helper grammar rows, one source-AST-order row, three raw/output boundary rows; separate scopes.',
        'Trusted Python tripwires, not OS/hostile-interpreter containment.',
        'No full real input gate, LOCAL/TARGET/native, architecture or canonical PASS proof.']}
    receipt=save(out,'capture.json',capture)
    print(json.dumps({'capture':receipt,'qualified':qualified,'suiteRows':len(result['rows']) if result else None},separators=(',',':')))
    return 0 if qualified else 1


if __name__=='__main__':
    try:code=execute(sys.argv)
    except BaseException as error:sys.stderr.write(type(error).__name__+': '+str(error)[:16384]+'\n');code=2
    raise SystemExit(code)
