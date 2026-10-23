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
CONFIG={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-matrix-qa-r1/config.json', 'bytes': 13544, 'sha256': '9e83a3de19394d236d2575a1bbfdfb21ba47511f6d5f4d35f09e3242a87ad0ee'}
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


MATRIX={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-matrix-qa-r1/matrix.json', 'bytes': 59112, 'sha256': '91f18a2966cac243faff09e1e7e3750febb799443b6cf684e17d27aa79c003bf'}
GRAMMAR_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-opaque-inventory-controls-r1/acceptance.json', 'bytes': 1210, 'sha256': '8e55d89c5ee7e8173012818c5b8f5e902f6d2c7f16b818c3ca200bf292ea5af0'}
POSITIVE_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-r3/positive-baseline-acceptance.json', 'bytes': 1201, 'sha256': '335181094d00987325263e8731b8f8c43854113b9f30d333f5f3ae97d87f3bd6'}
SCOPE_REVIEW_DECISIONS={
    'grammar':{'qa':'ACCEPT_OPAQUE_GRAMMAR_CONTROLS_ONLY','security':'ACCEPT_OPAQUE_GRAMMAR_CONTROLS_ONLY'},
    'positive':{'qa':'ACCEPT_REAL_INPUT_GATE_POSITIVE_ONLY','security':'ACCEPT_ACTUAL_INPUT_GATE_POSITIVE_ONLY'}}


def accepted_scope(pins, acceptance_pin, decision, review_decisions, source_approval, source_closure, excluded):
    pack=pins.read(acceptance_pin)
    need(pack['decision']==decision and pack['executionReleased'] is False,'CURRENT_SCOPED_ACCEPTANCE')
    observed=pins.read(pack['subject'])
    need(equal(observed['sourceApproval'],source_approval) and equal(observed['sourceClosure'],source_closure),
      'SCOPED_EVIDENCE_EXACT_CURRENT_SOURCE')
    need(set(pack['independentReviews'])=={'qa','security'},'SCOPED_TWO_REVIEW_ROLES')
    sessions=[]
    for role,pin in pack['independentReviews'].items():
        report=pins.read(pin,True);sessions.append(report['session'])
        need(report['session'] not in excluded and report['role']==role and report['decision']==review_decisions[role]
          and equal(report['subject'],pack['subject']) and report['findings']==[],
          'ACTUAL_INDEPENDENT_SCOPED_REVIEW')
    need(len(set(sessions))==2,'SCOPED_DISTINCT_REVIEW_SESSIONS')
    return observed


def mutate_case(case,config,worker,mapping):
    # Caller-memory mutations only. No validators, observations or original files replaced.
    mutation=case['mutation'];op=mutation['operation']
    if op=='none':closed(mutation,('operation',))
    elif op=='removeMapping':
        need(set(mutation) in ({'operation','descriptor'},{'operation','descriptor','role'}),'REMOVE_MUTATION_KEYS')
        d=mutation['descriptor'];need(equal(mapping.get(d['path']),d),'ORIGINAL_MAPPING_MUTATION_TARGET')
        del mapping[d['path']]
    elif op=='replaceMapping':
        closed(mutation,('operation','original','replacement'));d=mutation['original'];replacement=mutation['replacement']
        need(equal(mapping.get(d['path']),d) and replacement['path']==d['path'],'ORIGINAL_MAPPING_DRIFT_TARGET')
        mapping[d['path']]=copy.deepcopy(replacement)
    elif op in ('setConfig','setWorker'):
        closed(mutation,('operation','key','value'));target=config if op=='setConfig' else worker
        need(mutation['key'] in target,'EXISTING_CALLER_KEY');target[mutation['key']]=copy.deepcopy(mutation['value'])
    elif op=='swapExpected':
        closed(mutation,('operation',))
        config['expectedReplies']['JS'],config['expectedReplies']['RUST']=config['expectedReplies']['RUST'],config['expectedReplies']['JS']
    elif op=='setJobOutput':
        closed(mutation,('operation','index','value'));need(type(mutation['index']) is int and mutation['index'] in (0,1),'JOB_INDEX')
        worker['jobs'][mutation['index']]['output']=mutation['value']
    else:need(False,'UNRECOGNIZED_FIXED_MATRIX_MUTATION')



QA_OPERATOR='/root/android_health_qa'
PRIMARY_MATRIX_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-matrix-r1/acceptance.json', 'bytes': 1416, 'sha256': '834526802dce0ab821d6d6447511f707b7086a810f2c21a1fe3ae29534d7ccc1'}
PRIMARY_MATRIX_CONFIG={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-matrix-r1/config.json', 'bytes': 12481, 'sha256': 'c0665fdd17af7518845507d9ad3a9aa6c9ebd1cfee479cff402d0bd3c85b7098'}
PRIMARY_MATRIX={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e06-inventory-enforcement-matrix-r1/matrix.json', 'bytes': 59107, 'sha256': '9b3ad58b74470fff7c73e3a0d0b65645b8c4a69dec3ae092edaa40be71c99e55'}
PRIMARY_MATRIX_REVIEWERS={'qa': {'reviewer': '/root/transport_evidence_qa', 'decision': 'ACCEPT_REAL_INPUT_GATE_MATRIX_ONLY'}, 'security': {'reviewer': '/root/attachment_profile_security', 'decision': 'ACCEPT_ACTUAL_CALLER_MEMORY_INPUT_GATE_MATRIX_ONLY'}}

def accepted_primary_matrix(pins,excluded):
    # Exact existing PRIMARY authority/report shapes; no generic field/decision alias.
    pack=pins.read(PRIMARY_MATRIX_ACCEPTANCE)
    need(pack['schema']=='e06-real-input-gate-matrix-acceptance-v1'
      and pack['decision']=='ACCEPT_REAL_INPUT_GATE_MATRIX_ONLY' and pack['scope']=='PRIMARY_CALLER_MEMORY_MATRIX_ONLY'
      and pack['executionReleased'] is False and equal(pack['counts'],{'accept':1,'exactRefuse':75,'total':76}),
      'EXACT_ACCEPTED_PRIMARY_MATRIX_SCOPE')
    observed=pins.read(pack['subject']);original_config=pins.read(PRIMARY_MATRIX_CONFIG);original_matrix=pins.read(PRIMARY_MATRIX)
    need(equal(observed['config'],PRIMARY_MATRIX_CONFIG) and equal(observed['matrix'],PRIMARY_MATRIX)
      and equal(observed['sourceApproval'],SOURCE_APPROVAL) and equal(observed['sourceClosure'],SOURCE_CLOSURE)
      and equal(observed['controlApproval'],CONTROL_APPROVAL) and equal(observed['grammarAcceptance'],GRAMMAR_ACCEPTANCE)
      and equal(observed['positiveAcceptance'],POSITIVE_ACCEPTANCE)
      and observed['runRole']==original_config['runRole']=='primary' and observed['executionSession']==original_config['executionSession']=='/root'
      and observed['executionSession']!=QA_OPERATOR and observed['qualified'] is True
      and observed['status']=='PASS_SCOPED_CALLER_MEMORY_MATRIX_ONLY' and observed['actualRows']==observed['expectedRows']==76
      and observed['firstError'] is None and observed['secondaryErrors']==[]
      and all(n==0 for n in observed['sideEffectAttempts'].values()) and observed['allowedAdmissionImports']==1
      and observed['nativeJobs']==0 and observed['fullLocalVerifierExecuted'] is False,
      'ACTUAL_DISTINCT_ACCEPTED_PRIMARY_MATRIX')
    need(set(pack['independentReviews'])=={'qa','security'},'PRIMARY_EXACT_TWO_REVIEW_ROLES')
    reviewers=[]
    for role,rp in pack['independentReviews'].items():
        report=pins.read(rp,True);expected=PRIMARY_MATRIX_REVIEWERS[role];reviewers.append(report['reviewer'])
        need(report['role']==role and report['reviewer']==expected['reviewer'] and report['reviewer'] not in excluded
          and report['reviewer']!=observed['executionSession'] and report['reviewer']!=QA_OPERATOR
          and report['decision']==expected['decision'] and equal(report['subject'],pack['subject'])
          and equal(report['configuration'],PRIMARY_MATRIX_CONFIG) and report['findings']==[],
          'ACTUAL_NONAUTHOR_NONOPERATOR_PRIMARY_MATRIX_REVIEW')
        lifecycle=pins.read(report['outerExecution'],True)
        need(lifecycle['actor']=='/root' and lifecycle['exit']==0 and lifecycle['reaped'] is True
          and lifecycle['stdoutEOF'] is True and lifecycle['stderrEOF'] is True
          and lifecycle['forced'] is False and lifecycle['error'] is None,'ACCEPTED_PRIMARY_NATURAL_LIFECYCLE')
        pins.remember(lifecycle['stdout']);pins.remember(lifecycle['stderr'])
    need(len(set(reviewers))==2,'PRIMARY_DISTINCT_REVIEWERS')
    need(len(observed['rows'])==len(original_matrix['rows'])==76,'PRIMARY_COMPLETE_ORDERED_ROWS')
    for summary,expected in zip(observed['rows'],original_matrix['rows']):
        need(summary['id']==expected['id'] and summary['state']=='EXECUTED' and summary['matched'] is True,
          'PRIMARY_EXACT_MATCHED_ROW_SUMMARY')
        row=pins.read(summary['observation'])
        wanted_error=None if expected['expectedFirstError'] is None else {'type':'Refusal','message':expected['expectedFirstError']}
        need(row['id']==expected['id'] and equal(row['mutation'],expected['mutation'])
          and row['expectedOutcome']==row['actualOutcome']==expected['expectedOutcome']
          and row['expectedFirstError']==expected['expectedFirstError'] and equal(row['firstError'],wanted_error)
          and row['gateEntered'] is True and row['matched'] is True and row['secondaryErrors']==[]
          and row['continuationCalls']==(1 if wanted_error is None else 0)
          and all(n==0 for n in row['sideEffectAttempts'].values()) and row['nativeJobs']==0,
          'PRIMARY_ACTUAL_PRECOMMITTED_ROW_EVIDENCE')
    return pack['subject']


def execute(argv):
    begun=time.monotonic();pins=OriginalPins()
    need(len(argv)==6,'CLI matrix.py CONFIG CONFIG_SHA RELEASE RELEASE_SHA SESSION')
    need(dict(os.environ)==ENV,'EXACT_OUTER_ENVIRONMENT');pins.remember(PYTHON)
    need(str(Path(sys.executable).resolve(strict=True))==PYTHON['path'],'FIXED_OUTER_INTERPRETER')
    own=descriptor(Path(__file__).resolve(strict=True));pins.remember(own)
    need(argv[1]==CONFIG['path'] and argv[2]==CONFIG['sha256'],'EXACT_CONFIG')
    config=pins.read(CONFIG)
    closed(config,('schema','state','runId','runRole','executionSession','sourceAcceptance','sourceApproval',
      'sourceClosure','controlApproval','controlAcceptance','qualificationSchema','admission','python',
      'environment','outputRoot','arguments','expectedGateOutcome','maximumPhaseMilliseconds',
      'futureQaOutputRootNotActivated','executionReleased','matrix','grammarAcceptance','positiveAcceptance',
      'scopeReviewDecisions','primaryMatrixAcceptance','primaryMatrixConfig','primaryMatrix','primaryMatrixReviewers'))
    need(config['schema']=='e06-inventory-real-matrix-config-v1'
      and config['state']=='PROPOSED_REAL_GATE_MATRIX_ARGUMENTS_ONLY_NOT_LOCAL_CONFIG'
      and config['expectedGateOutcome']=='ACCEPT' and config['executionReleased'] is False
      and config['executionSession']==QA_OPERATOR and config['runRole']=='qa',
      'STRICT_REAL_MATRIX_ARGUMENTS_ONLY')
    for key,pin in (('sourceAcceptance',SOURCE_ACCEPTANCE),('sourceApproval',SOURCE_APPROVAL),
      ('sourceClosure',SOURCE_CLOSURE),('controlApproval',CONTROL_APPROVAL),
      ('controlAcceptance',CONTROL_ACCEPTANCE),('qualificationSchema',QUALIFICATION_SCHEMA),
      ('admission',ADMISSION),('python',PYTHON),('matrix',MATRIX),
      ('grammarAcceptance',GRAMMAR_ACCEPTANCE),('positiveAcceptance',POSITIVE_ACCEPTANCE),
      ('primaryMatrixAcceptance',PRIMARY_MATRIX_ACCEPTANCE),('primaryMatrixConfig',PRIMARY_MATRIX_CONFIG),
      ('primaryMatrix',PRIMARY_MATRIX)):
        need(equal(config[key],pin),'EXACT_PINNED_CONFIG_OPERAND');pins.remember(pin)
    need(config['maximumPhaseMilliseconds']==540000 and equal(config['environment'],ENV)
      and equal(config['scopeReviewDecisions'],SCOPE_REVIEW_DECISIONS)
      and equal(config['primaryMatrixReviewers'],PRIMARY_MATRIX_REVIEWERS),'FIXED_NEW_MATRIX_BUDGET_ENV_REVIEW_VOCABULARY')
    release_pin=descriptor(argv[3]);need(release_pin['sha256']==argv[4],'EXTERNAL_RELEASE_SHA')
    release=pins.read(release_pin)
    closed(release,('schema','decision','rootSession','executionSession','runRole','config',
      'sourceApproval','controlApproval','grammarAcceptance','positiveAcceptance','primaryMatrixAcceptance','matrix','bootstrap','notAfterUtcMs'))
    need(release['schema']=='e06-inventory-matrix-qa-release-v1'
      and release['decision']=='RELEASE_EXACT_ADMISSION_INPUT_MATRIX_QA_ONLY'
      and release['rootSession']=='/root' and release['executionSession']==argv[5]==config['executionSession']
      and release['runRole']==config['runRole']=='qa' and release['executionSession']==QA_OPERATOR
      and equal(release['config'],CONFIG)
      and equal(release['sourceApproval'],SOURCE_APPROVAL) and equal(release['controlApproval'],CONTROL_APPROVAL)
      and equal(release['grammarAcceptance'],GRAMMAR_ACCEPTANCE) and equal(release['positiveAcceptance'],POSITIVE_ACCEPTANCE)
      and equal(release['primaryMatrixAcceptance'],PRIMARY_MATRIX_ACCEPTANCE)
      and equal(release['matrix'],MATRIX) and equal(release['bootstrap'],own),'EXACT_NEW_MATRIX_ROOT_RELEASE_NOT_LOCAL')
    need(type(release['notAfterUtcMs']) is int and 0<release['notAfterUtcMs']-(time.time_ns()//1000000)<=570000,
      'FINITE_NEW_MATRIX_ROOT_RELEASE')
    def live():
        need(time.monotonic()-begun<540 and (time.time_ns()//1000000)<release['notAfterUtcMs'],'MATRIX_PHASE_OR_RELEASE_EXPIRED')
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
    excluded=approval['authors']+['/root','/root/e06_policy_marker_implementer',QA_OPERATOR]
    grammar=accepted_scope(pins,GRAMMAR_ACCEPTANCE,'ACCEPT_OPAQUE_GRAMMAR_CONTROLS_ONLY',
      SCOPE_REVIEW_DECISIONS['grammar'],SOURCE_APPROVAL,SOURCE_CLOSURE,excluded)
    need(grammar['qualified'] is True and grammar['firstError'] is None and grammar['secondaryErrors']==[]
      and all(n==0 for n in grammar['forbiddenAttempts'].values()) and grammar['nativeJobs']==0
      and grammar['fullInputGateCalls']==0,'CURRENT_ACTUAL_GRAMMAR_QUALIFIED')
    grammar_suite=pins.read(grammar['suiteResult'])
    need(len(grammar_suite['rows'])==21 and all(r['matched'] is True for r in grammar_suite['rows'])
      and equal(grammar_suite['sourceApproval'],SOURCE_APPROVAL)
      and equal(grammar_suite['sourceClosure'],SOURCE_CLOSURE),'ACTUAL_TWENTY_ONE_GRAMMAR_ROWS')
    positive=accepted_scope(pins,POSITIVE_ACCEPTANCE,'ACCEPT_REAL_INPUT_GATE_POSITIVE_ONLY',
      SCOPE_REVIEW_DECISIONS['positive'],SOURCE_APPROVAL,SOURCE_CLOSURE,excluded)
    need(positive['gateEntered'] is True and positive['expectedGateOutcome']==positive['observedGateOutcome']=='ACCEPT'
      and positive['status']=='PASS_SCOPED_GATE_PROBE_ONLY' and positive['firstError'] is None
      and positive['secondaryErrors']==[] and positive['continuationCalls']==1
      and all(n==0 for n in positive['sideEffectAttempts'].values()) and positive['allowedAdmissionImports']==1
      and positive['nativeJobs']==0 and positive['fullLocalVerifierExecuted'] is False,'ACTUAL_PREVIOUS_REAL_POSITIVE')
    primary_matrix_subject=accepted_primary_matrix(pins,excluded)
    matrix=pins.read(MATRIX)
    closed(matrix,('schema','state','sourceAdmission','inventory','materialization','rows','rowCount',
      'missingRoleRows','negativeRows','mutationDomain'))
    cases=matrix['rows']
    need(matrix['schema']=='e06-inventory-fixed-refusal-matrix-v1' and matrix['state']=='SOURCE_ONLY_PRECOMMITTED_EXPECTATIONS_NOT_EXECUTED'
      and equal(matrix['sourceAdmission'],ADMISSION) and matrix['rowCount']==len(cases)==76
      and matrix['missingRoleRows']==57 and matrix['negativeRows']==75
      and len({r['id'] for r in cases})==76 and cases[0]['id']=='BASELINE_CURRENT_VALID'
      and cases[0]['expectedOutcome']=='ACCEPT' and cases[0]['expectedFirstError'] is None
      and all(r['expectedOutcome']=='REFUSE' and type(r['expectedFirstError']) is str for r in cases[1:]),'EXACT_FIXED_MATRIX')
    for row in cases:closed(row,('id','mutation','expectedOutcome','expectedFirstError','firstCheckAttribution','scope'))
    out=Path(config['outputRoot'])
    need(re.fullmatch('/tmp/e6n-inventory-matrix-qa-[a-f0-9]{12}',str(out)) and out.parent==Path('/tmp')
      and not os.path.lexists(out),'FRESH_OWNED_MATRIX_OUTPUT')
    args=config['arguments'];closed(args,('config','worker'))
    live();pins.recheck();out.mkdir(mode=0o700)
    argument_pin=save(out,'gate-arguments.json',{'scope':'REAL_GATE_ARGUMENTS_ONLY_NOT_LOCAL_CONFIG',**args})
    traps=NoCalls();rows=[];first=None;late=[];setup_refs=[];base_mapping=None;defs=None
    try:
        traps.install();traps.active=True
        spec=importlib.util.spec_from_file_location('_e06_inventory_matrix_admission',ADMISSION['path'])
        A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
        def setup(inventory):
            nonlocal base_mapping,defs
            live();base_mapping=A.fixed_source(source);defs=A.qualification_definitions()
            inventory.recheck();live()
            setup_refs.extend({'path':p,'bytes':n,'sha256':sha} for p,n,sha in inventory._pins.values())
        A._with_inventory(setup)
        for index,case in enumerate(cases):
            live();started=time.monotonic();continuations=0;gate_started=False;error=None;actual_error=None;secondary=[];referents=[]
            before=dict(traps.counts);cc=copy.deepcopy(args['config']);wc=copy.deepcopy(args['worker']);mapping=copy.deepcopy(base_mapping)
            try:mutate_case(case,cc,wc,mapping)
            except BaseException as exc:error=fact(exc);actual_error=exc
            if error is None:
                def run(inventory):
                    nonlocal continuations,gate_started,error,actual_error
                    try:
                        live();gate_started=True
                        A.local_worker_inputs(cc,wc,mapping,defs)
                        live();continuations+=1
                    except BaseException as exc:error=fact(exc);actual_error=exc
                    try:inventory.recheck();live()
                    except BaseException as exc:secondary.append(fact(exc))
                    referents.extend({'path':p,'bytes':n,'sha256':sha} for p,n,sha in inventory._pins.values())
                try:A._with_inventory(run)
                except BaseException as exc:
                    if error is None:error=fact(exc);actual_error=exc
                    else:secondary.append(fact(exc))
            effects={key:traps.counts[key]-before[key] for key in before}
            expected=case['expectedFirstError']
            strict_error=(actual_error is None and continuations==1) if expected is None else (type(actual_error) is A.Refusal and str(actual_error)==expected and continuations==0)
            baseline_complete=True
            if index==0:
                try:
                    inventory_map=pins.read(matrix['inventory'])
                    needed={d['path'] for d in inventory_map.values()}|{matrix['materialization']['path']}
                    material=pins.read(matrix['materialization']);needed.update(d['path'] for d in material['outputs'].values())
                    baseline_complete=needed<={d['path'] for d in referents}
                except BaseException as exc:
                    baseline_complete=False;secondary.append(fact(exc))
            matched=gate_started and strict_error and not secondary and all(n==0 for n in effects.values()) and baseline_complete
            record={'schema':'e06-inventory-real-matrix-row-v1','index':index,'id':case['id'],
              'scope':case['scope'],'mutation':case['mutation'],'expectedOutcome':case['expectedOutcome'],
              'expectedFirstError':expected,'firstCheckAttribution':case['firstCheckAttribution'],
              'actualOutcome':'ACCEPT' if actual_error is None and continuations==1 else 'REFUSE' if type(actual_error) is A.Refusal else 'ERROR',
              'gateEntered':gate_started,'firstError':error,'secondaryErrors':secondary,
              'continuationCalls':continuations,'sideEffectAttempts':effects,'actualVerifiedReferents':referents,
              'elapsedMilliseconds':round((time.monotonic()-started)*1000),'matched':matched,
              'baselineInventoryDerivationOutputsCovered':baseline_complete if index==0 else None,
              'mappingMutationOnly':True,'onDiskDriftOrFilesystemRaceTest':False,'nativeJobs':0}
            # Actual gate/context has returned. Only bounded own observation writes here.
            traps.active=False
            rp=save(out,'row-'+str(index).zfill(3)+'.json',record)
            rows.append({'id':case['id'],'state':'EXECUTED','matched':matched,'observation':rp})
            traps.active=True
            if not matched:
                first={'rowId':case['id'],'kind':'UNEXPECTED_OR_UNQUALIFIED_MATRIX_ROW','actualFirstError':error}
                break
    except BaseException as exc:
        if first is None:first=fact(exc)
        else:late.append(fact(exc))
    finally:traps.finish()
    try:pins.recheck();live()
    except BaseException as exc:late.append(fact(exc))
    executed={r['id'] for r in rows}
    for case in cases:
        if case['id'] not in executed:rows.append({'id':case['id'],'state':'NOT_EXECUTED','matched':False,'reason':'Earlier baseline/row/preflight error, budget or release expiry; no retry.'})
    qualified=len(executed)==76 and all(r['matched'] for r in rows) and first is None and not late and all(n==0 for n in traps.counts.values()) and traps.admissionImports==1
    result={'schema':'e06-inventory-real-matrix-observation-v1','bootstrap':own,'config':CONFIG,'matrix':MATRIX,
      'outerRootRelease':release_pin,'sourceApproval':SOURCE_APPROVAL,'sourceClosure':SOURCE_CLOSURE,
      'controlApproval':CONTROL_APPROVAL,'grammarAcceptance':GRAMMAR_ACCEPTANCE,'positiveAcceptance':POSITIVE_ACCEPTANCE,
      'primaryMatrixAcceptance':PRIMARY_MATRIX_ACCEPTANCE,'acceptedPrimarySubject':primary_matrix_subject,
      'runId':config['runId'],'runRole':config['runRole'],'executionSession':config['executionSession'],
      'gateArguments':argument_pin,'sourceSetupVerifiedReferents':setup_refs,'rows':rows,'expectedRows':76,
      'actualRows':len(executed),'firstError':first,'secondaryErrors':late,'sideEffectAttempts':traps.counts,
      'allowedAdmissionImports':traps.admissionImports,'qualified':qualified,
      'status':'PASS_SCOPED_CALLER_MEMORY_MATRIX_ONLY' if qualified else 'FAIL_OR_UNQUALIFIED_MATRIX',
      'fullLocalVerifierExecuted':False,'nativeJobs':0,'requestDelivered':False,
      'elapsedMilliseconds':round((time.monotonic()-begun)*1000),
      'limits':['Caller-memory/mapping mutation only; no original-file mutation or FS-race evidence.',
        'One real gate primitive; no full LOCAL/TARGET/native authority or runtime wiring proof.',
        'Strict exact A.Refusal/message only; unexpected exception never accepted.',
        'Pristine actual449mapping prepared once; each row fresh caller clone and actual _with_inventory/recheck.',
        'Trusted Python tripwires; no hostile-host or OS sandbox claim.']}
    receipt=save(out,'observation.json',result)
    print(json.dumps({'observation':receipt,'qualified':qualified,'actualRows':len(executed)},separators=(',',':')))
    return 0 if qualified else 1


if __name__=='__main__':
    try:code=execute(sys.argv)
    except BaseException as error:
        sys.stderr.write(type(error).__name__+': '+str(error)[:16384]+'\n');code=2
    raise SystemExit(code)
