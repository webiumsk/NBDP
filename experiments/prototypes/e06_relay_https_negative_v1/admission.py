"""SOURCE ONLY: fixed N02/N03/N16 admission. Importing launches no work.

Both entry points require external SHA, session and role operands. Local F-only
qualification deliberately has no qualification prerequisite; all other current
source, controls, configuration, carrier and transport gates remain mandatory.
No target/native/helper is imported until those authority checks pass.
"""
import hashlib
import contextvars
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = ROOT/'docs/decisions/evidence/invoice-authenticated-carrier/e06-https-acquisition-preparation-r1'
DATA = {'SOURCE.md': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/SOURCE.md', 'bytes': 5474, 'sha256': 'ac2a85391e583a995950d248cf2af3c8bfefbda363c35e9a51139473885813cc'}, 'contract.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/contract.json', 'bytes': 22787, 'sha256': '5208c3bbfd1dea75577c90c0bdea49b9410ac4163e09ca5d09af8d7702196d13'}, 'interfaces.md': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/interfaces.md', 'bytes': 14702, 'sha256': 'c04ae8e852b096403c865a6daf22c45eed071dc5248035cea0954762da925af7'}, 'profile.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/profile.json', 'bytes': 4442, 'sha256': 'c7167a764d562e6878b8ba35535c8938c4c04a836bd25cea1aeb396f9e8d9bae'}, 'selection-map.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/selection-map.json', 'bytes': 32883, 'sha256': 'd66ec8cf79b9d572eb0268a307ed782047a9cb897a65de83b6b00f430fa6cf09'}, 'native-oracles.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/native-oracles.json', 'bytes': 27629, 'sha256': '12a508cc4060ad920ebcba0aeb0c23f5b7de7c311aaeec575cb4bf5f0ad28a2a'}, 'NATIVE_ORACLES.md': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/NATIVE_ORACLES.md', 'bytes': 18655, 'sha256': '69388bb061a87bd3bc938154556228fffc9157cca7bb32a67ad8d2e75c0d00a6'}, 'bridge-schemas.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/bridge-schemas.json', 'bytes': 158719, 'sha256': '89173066418eddd16f1d2a14ecee4b04470072385c1883aab48a01dd6e41281a'}, 'worker-schemas.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/worker-schemas.json', 'bytes': 101686, 'sha256': 'f6578bba812f4859e853c34c95ce1f4dad6f2363af6bf6b899b4d5684fbe74f5'}, 'oracles.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/oracles.json', 'bytes': 105615, 'sha256': '317047707f19f429791b2a3cec730550c18427bb58c25cfcaa0702edf290c0cd'}, 'protected-deltas.json': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/protected-deltas.json', 'bytes': 12189, 'sha256': '70846060c58d5ff5f11ab930a9a0fcd2013a3f69e7c420a2e2bdd358aee24d99'}, 'BRIDGE.md': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/BRIDGE.md', 'bytes': 16984, 'sha256': '1f363f50d5e41413b05e4bb862e8eb53b7288ab8a205000287d69862af5049e7'}}
NODE = dict(path='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node', bytes=121613584,
            sha256='ccacb2d6d87ba6d118b2bffc1ae33747a05cc5fc6b1f1ec4fc1d420b687e952d')
PYTHON = dict(path='/home/peterhorvath/.miniforge3/bin/python3.13',bytes=32959480,
              sha256='5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1')
RUST = dict(path='/tmp/nbdp-e06-build-tv5zqp4j/target/debug/nbdp-experiment-rust', bytes=26400472,
            sha256='55205961550c66467be356b13adeafaf43599ca6f59f2db5ebf1de9293c3045d')
POLICY = dict(path=str(ROOT/'docs/decisions/transport-sub-evidence-prerequisite-v1.md'), bytes=3073,
              sha256='0ed885e41d3cbb2d38af33cdd060e5ad5bea3327d0ce2a4306c123c170a15a25')
CURRENT_E01 = dict(path=str(ROOT/'docs/decisions/evidence/invoice-authenticated-carrier/e01-completion-and-next-action.json'),bytes=14812,
                   sha256='52619ef1137a78937f0ab079655e05ac11c7b07d45f5bade6439eed72c7899c5')
TRANSPORT_GATE = dict(path=str(ROOT/'experiments/prototypes/e04_prerequisite_gate_v1/prerequisite_gate.py'), bytes=30015,
                      sha256='fe23d255352863ca2872028116dbac506e85b766d3455972ff775da3773c6f9f')
TRANSPORT_RELEASE = dict(path=str(ROOT/'docs/decisions/evidence/invoice-authenticated-carrier/e04-gate-qualification-r2/runtime-release.json'), bytes=3560,
                         sha256='4dc61f0dc054a5f70a9d42578cd19ad711cf30a21dd14d83884f7be560ced04c')
EXCLUDED = ['/root','/root/negative_outer_implementer','/root/negative_io_implementer',
            '/root/recovery_fixture_parent','/root/negative_lane_architect']
FUTURE_SOURCE_NAMES = ['protocol.mjs','case.mjs','admission.py','runner.py','checker.py',
                       'controls.py','wire.mjs','metadata_loader.mjs','wire_controls.mjs',
                       'qualification.py','IMPLEMENTATION.md','qualification-schemas.json']
INERT_ACCEPTANCE = dict(path=str(EVIDENCE/'composition-negative-freeze-r2/acceptance.json'),bytes=3561,
 sha256='e5cd4e5d51055ee4c2feede53c6cd3e7c83ac51e74d3eafb6cb5514c5d156ffb')
LOCAL_PLAN = dict(path=str(EVIDENCE/'composition-negative-native-qualification-plan-r2/acceptance.json'),bytes=3596,
 sha256='fb29a25955ae9178f7dd9e781c448a1486fbd7267beb02443c78421e1deb0f93')
ENV = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
       'WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'}

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

def descriptor(p):
    p=Path(p);need(p.is_absolute() and str(p.resolve(strict=True))==str(p) and p.is_file() and not p.is_symlink(),'CANONICAL_FILE')
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        while block:=f.read(1048576):size+=len(block);h.update(block)
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())


# Per-verify direct verified referents, independent of sourceClosure/self-reference.
# Finite2048 unique canonical files,512MiB/file,4GiB declared aggregate. Rechecks
# stream; checked JSON reads remain bounded32MiB. No historical graph expansion.
EVIDENCE_MAX_FILES = 2048
EVIDENCE_MAX_FILE_BYTES = 536870912
EVIDENCE_MAX_BYTES = 4294967296
_admission_evidence = contextvars.ContextVar('i4_admission_evidence',default=None)

class _VerifiedEvidenceInventory:
    def __init__(self):self._pins={};self._bytes=0
    def remember(self,d):
        closed(d,('path','bytes','sha256'));p=Path(d['path'])
        need(p.is_absolute() and str(p.resolve(strict=True))==str(p),'EVIDENCE_CANONICAL_PATH')
        need(type(d['bytes']) is int and 0<=d['bytes']<=EVIDENCE_MAX_FILE_BYTES
             and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'EVIDENCE_DESCRIPTOR_BOUND')
        previous=self._pins.get(d['path'])
        if previous is not None:need(previous==(d['path'],d['bytes'],d['sha256']),'EVIDENCE_CONFLICTING_PIN');return
        need(len(self._pins)<EVIDENCE_MAX_FILES and self._bytes+d['bytes']<=EVIDENCE_MAX_BYTES,'EVIDENCE_INVENTORY_BOUND')
        self._pins[d['path']]=(d['path'],d['bytes'],d['sha256']);self._bytes+=d['bytes']
    def recheck(self):
        for name,size,sha in self._pins.values():
            expected=dict(path=name,bytes=size,sha256=sha)
            need(equal(descriptor(name),expected),'EVIDENCE_SOURCE_OR_INPUT_DRIFT')

def checked(d):
    closed(d,('path','bytes','sha256'))
    need(type(d['bytes']) is int and d['bytes']>=0 and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'DESCRIPTOR')
    need(equal(descriptor(d['path']),d),'PIN_MISMATCH:'+d['path'])
    need(d['bytes']<=33554432,'DATA_READ_BOUND');raw=Path(d['path']).read_bytes()
    need(len(raw)==d['bytes'] and hashlib.sha256(raw).hexdigest()==d['sha256'],'PIN_MISMATCH:'+d['path'])
    inventory=_admission_evidence.get()
    if inventory is not None:inventory.remember(d)
    return raw

def document(d,historical=False):return loads(checked(d),historical)

def validate(v,g,defs):
    if type(g) is str:
        if g.startswith('@'):need(g[1:] in defs,'SCHEMA_REF');return validate(v,defs[g[1:]],defs)
        need(type(v) is bool if g=='boolean' else g=='null' and v is None,'SCHEMA_TYPE');return v
    if 'union' in g:
        for option in g['union']:
            try:validate(v,option,defs);return v
            except (Refusal,KeyError,TypeError,ValueError):pass
        raise Refusal('SCHEMA_UNION')
    if 'record' in g:
        closed(v,g['record']);[validate(v[k],s,defs) for k,s in g['record'].items()]
    elif 'enum' in g:need(any(equal(v,x) for x in g['enum']),'SCHEMA_ENUM')
    elif 'literal' in g:need(equal(v,g['literal']),'SCHEMA_LITERAL')
    elif 'integer' in g:need(type(v) is int and g['integer'][0]<=v<=g['integer'][1],'SCHEMA_INTEGER')
    elif 'tuple' in g:
        need(type(v) is list and len(v)==len(g['tuple']),'SCHEMA_TUPLE')
        [validate(x,s,defs) for x,s in zip(v,g['tuple'])]
    elif 'array' in g:
        need(type(v) is list and g['length'][0]<=len(v)<=g['length'][1],'SCHEMA_ARRAY')
        [validate(x,g['array'],defs) for x in v]
    else:
        need(type(v) is str and len(v.encode('utf-8'))<=g.get('stringMax',131072),'SCHEMA_STRING')
        if 'pattern' in g:need(re.search(g['pattern'],v) is not None,'SCHEMA_PATTERN')
    return v

def closure(ds):
    need(type(ds) is list and 1<=len(ds)<=1024,'FINITE_CLOSURE');result={}
    for d in ds:
        need(d['path'] not in result,'DUPLICATE_CLOSURE_PATH')
        need(equal(descriptor(d['path']),d),'CURRENT_SOURCE_PIN');result[d['path']]=d
    return result

def member(mapping,d):need(equal(mapping.get(d['path']),d),'MISSING_OR_DRIFTED_MEMBER:'+d['path'])

def private_dir(p):
    p=Path(p);s=p.lstat()
    need(str(p.resolve(strict=True))==str(p) and p.is_dir() and s.st_mode&0o777==0o700 and s.st_uid==os.getuid(),'OWNED_0700_DIRECTORY')

def reviews(pack,decision,subject,exclude,defs):
    rows=pack['reviews'];need(len(rows)==2 and len({r['session'] for r in rows})==2 and {r['role'] for r in rows}=={'qa','security'},'DISTINCT_REVIEW_ROLES')
    for r in rows:
        validate(r,'@approvalReview',defs)
        need(r['decision']==decision and r['session'] not in exclude and r['session'] not in pack['authors'],'AUTHOR_OR_SCOPE')
        need(equal(document(r['subject']),subject),'REVIEW_NATIVE_SUBJECT')

def natural(l):
    need(l['launchAttempt'] is True and l['acquisition']=='ACQUIRED' and type(l['pid']) is int and l['pid']>0 and l['exitCode']==0
         and l['signal'] is None and l['reaped'] is True and l['stdoutEOF'] is True and l['stderrEOF'] is True
         and l['timedOut'] is False and l['forced'] is False and l['error'] is None,'NATURAL_OWNED_CHILD')


def qualification_schema():
    return document(descriptor(HERE/'qualification-schemas.json'))


def qualification_definitions():
    schema=qualification_schema();worker=schema['workerDefinitions'];checker=schema['checkerDefinitions']
    need(not set(worker)&set(checker),'SEPARATE_QUALIFICATION_NAMESPACES')
    return dict(worker,**checker)


def fixed_source(source_closure):
    mapping=closure(source_closure)
    for d in DATA.values():member(mapping,d);checked(d)
    for name in FUTURE_SOURCE_NAMES:member(mapping,descriptor(HERE/name))
    for d in (NODE,PYTHON,RUST,POLICY,CURRENT_E01,TRANSPORT_GATE,TRANSPORT_RELEASE,
              INERT_ACCEPTANCE,LOCAL_PLAN):member(mapping,d);checked(d) if d['bytes']<=33554432 else None
    need(equal(descriptor(sys.executable),PYTHON),'FIXED_ADMISSION_PYTHON')
    protected=document(DATA['protected-deltas.json'])
    for relative,pin in protected['wholeSourcePins'].items():
        member(mapping,dict(path=str(ROOT/relative),**pin))
    # Whole protected positive closure remains original. No replacement hash refresh.
    baseline=document(protected['baselineClosure'])
    need(type(baseline) is list and len(baseline)==378,'EXACT_POSITIVE_BASELINE')
    for d in baseline:member(mapping,d)
    return mapping


def source_approval(pin,source_closure,defs):
    pack=document(pin);validate(pack,'@sourceApproval',defs)
    need(equal(pack['sourceClosure'],source_closure) and set(EXCLUDED)<=set(pack['authors']),
         'EXACT_DERIVATIVE_SOURCE_AUTHORS')
    reviews(pack,'ACCEPT_SOURCE_ONLY',source_closure,EXCLUDED,defs)
    return pack


CONTROL_IDS = ['CLOSED_TYPED_JSON','MISSING_EXTRA_KEYS','ORIGINAL_PIN_DRIFT',
 'UNKNOWN_COUNTS_REFUSE','WHOLE_NATIVE_DEEP_COMPARE','N03_NO_NATIVE',
 'N16_DENY_NO_GENERATION','BINDING_CONTEXT_REFUSE','COMMON_WHOLE_AGGREGATE',
 'INDEPENDENT_NONAUTHOR_REVIEWS','ORIGINAL_ERROR_PRESERVED',
 'RETAINED_OWNERSHIP_NO_POST_REAP_SIGNAL','FIXED_DEADLINES','SOURCE_FIRST_NO_CYCLE']


def control_evidence(value,source_pin,source_closure,mapping,defs):
    closed(value,('schema','sourceApproval','sourceClosure','rows','invocations','finalIntegrity'))
    rows=[dict(id=n,matched=True,scope='PURE_REFUSAL_ONLY') for n in CONTROL_IDS]
    need(value['schema']=='n02316-controls-evidence-v1' and equal(value['sourceApproval'],source_pin)
         and equal(value['sourceClosure'],source_closure) and equal(value['rows'],rows)
         and value['finalIntegrity'] is True,'EXACT_CURRENT_PURE_CONTROLS')
    need(type(value['invocations']) is list and len(value['invocations'])==1,'ONE_PYTHON_CONTROL_INVOCATION')
    row=value['invocations'][0]
    closed(row,('tool','argv','cwd','environment','stdin','stdout','stderr','lifecycle'))
    member(mapping,row['tool']);need(equal(row['tool'],PYTHON),'FIXED_CONTROL_PYTHON')
    validate(row['lifecycle'],'@lifecycle',defs);natural(row['lifecycle'])
    need(equal(row['environment'],ENV) and re.fullmatch('/tmp/e6n-controls-[a-z0-9]{6,12}',row['cwd']),
         'FIXED_CONTROL_ENV_CWD');private_dir(row['cwd'])
    cd=descriptor(Path(row['cwd'])/'source-closure.json')
    need(equal(document(cd),source_closure) and equal(row['argv'],[PYTHON['path'],'-I','-B',
         str(HERE/'controls.py'),cd['path'],cd['sha256'],row['cwd']]),'FIXED_CONTROL_SOURCE_COMMAND')
    need(checked(row['stdin'])==b'' and checked(row['stderr'])==b'','EMPTY_CONTROL_INPUT_ERROR')
    raw=checked(row['stdout']);need(raw.endswith(b'\n') and raw.count(b'\n')==1,'ONE_CONTROL_REPLY')
    reply=loads(raw[:-1]);closed(reply,('schema','sourceClosure','rows','finalIntegrity'))
    need(reply['schema']=='n02316-pure-controls-capture-v1' and equal(reply['sourceClosure'],source_closure)
         and equal(reply['rows'],rows) and reply['finalIntegrity'] is True,'ACTUAL_CONTROL_OUTPUT_JOIN')


def control_approval(pin,source_pin,source_closure,mapping,defs,source):
    pack=document(pin);validate(pack,'@controlApproval',defs)
    need(equal(pack['sourceApproval'],source_pin),'SAME_CONTROL_SOURCE_APPROVAL')
    evidence=document(pack['actualControlEvidence'])
    control_evidence(evidence,source_pin,source_closure,mapping,defs)
    reviews(pack,'ACCEPT_CONTROLS_ONLY',evidence,EXCLUDED+source['authors'],defs)
    return pack


def configuration_approval(pin,core,defs,source,controls):
    pack=document(pin);validate(pack,'@configurationApproval',defs)
    need(equal(pack['configuration'],core),'EXACT_CONFIGURATION_CORE')
    reviews(pack,'ACCEPT_CONFIGURATION_ONLY',core,EXCLUDED+source['authors']+controls['authors'],defs)
    return pack


def fixed_prerequisites(mapping):
    """Current original joins, independent of PARTIAL labels; no TLS reuse gate."""
    # These sources are immutable protected inputs, not imported I4 runtime code.
    old_pin=dict(path=str(ROOT/'experiments/prototypes/e06_https_acquisition_v1/contract.json'),
      bytes=109589,sha256='b7f291a033e4930ed86126cd8b0fe90204614f97e94e66d4716e3be3b7e7b9b8')
    member(mapping,old_pin);old=document(old_pin);c=document(DATA['contract.json']);ev=c['evidence']
    wanted=dict(positivePair=ev['positivePairAcceptance'],acceptedPlan=ev['planAcceptance'],
      r5Materialization=ev['r5MaterializationAcceptance'],r5Input=ev['r5InputAcceptance'],
      relayComponent=old['prerequisites']['relayMetadata']['descriptor'],
      recoveryComponent=old['prerequisites']['recovery']['descriptor'],candidateE02Policy=POLICY,
      sourceRelevantE01=CURRENT_E01,sourceRelevantE05=old['prerequisites']['e05']['descriptor'])
    for d in wanted.values():member(mapping,d);checked(d)
    need(b'ADOPTED_TECHNICAL_POLICY' in checked(POLICY) and b'transport-sub-evidence-v1' in checked(POLICY),'ADOPTED_POLICY')
    for name,key in [('relayComponent','relayMetadata'),('recoveryComponent','recovery'),('sourceRelevantE05','e05')]:
        spec=old['prerequisites'][key];v=document(wanted[name],True)
        for k,expected in spec['nativeFields'].items():need(equal(v.get(k),expected),'PREREQUISITE_NATIVE_SCOPE')
        for k in spec['absentNativeFields']:need(k not in v,'PREREQUISITE_NATIVE_ABSENT')
    e02=document(old['prerequisites']['e02']['descriptor'],True)
    need(e02['status']=='PARTIAL' and e02['exit_status']==0,'E02_REMAINS_PARTIAL')
    e01=document(CURRENT_E01,True)
    need(e01['decision']=='ACCEPT_CURRENT_CARRIER_LEGACY140_RUNTIME_SCOPE_ONLY'
      and e01['qa_decision']=='ACCEPT_CURRENT_CARRIER_REFERENCE140_RUNTIME_SCOPE_ONLY'
      and e01['security_decision']=='ACCEPT_CURRENT_CARRIER_LEGACY140_RUNTIME_SCOPE_ONLY'
      and e01['material_findings']==[],'CURRENT_SOURCE_E01_ACCEPTANCE')
    for run in e01['runs'].values():
        need(run['qualified'] is True and run['natural_outer_exit']==0 and run['checks']==140
             and run['failures']==0,'CURRENT_E01_BOTH140')
    pair=document(wanted['positivePair'],True)
    need(pair['decision']=='ACCEPT_EXACT_FOUR_WINDOW_PAIR_ONLY','EXACT_POSITIVE_PAIR')
    # Exact descriptors are reviewed current primary/QA evidence, not invented PASS flags.
    need(document(wanted['r5Materialization'])['decision']=='ACCEPT_FIXTURE_MATERIALIZATION_ONLY',
         'R5_MATERIALIZATION')
    checked(INERT_ACCEPTANCE);checked(LOCAL_PLAN)
    return wanted


def accepted_transport(mapping):
    # Read-only current prerequisite invocation AFTER all root/source/control/config
    # checks. Never call qualification/main/E04/sentinel or historical experiments.
    member(mapping,TRANSPORT_GATE);member(mapping,TRANSPORT_RELEASE)
    checked(TRANSPORT_GATE);checked(TRANSPORT_RELEASE)
    spec=importlib.util.spec_from_file_location('_n02316_pinned_transport_prerequisites',TRANSPORT_GATE['path'])
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    value=module.verify_transport_prerequisites(TRANSPORT_RELEASE['path'],TRANSPORT_RELEASE['sha256'])
    need(type(value) is dict and type(value.get('verifiedFiles')) is int and value['verifiedFiles']>0
      and type(value.get('verifiedArchives')) is int and value['verifiedArchives']>0,'ACTUAL_TRANSPORT_PREREQUISITE')
    return value


def fresh_output(path,pattern):
    need(type(path) is str and re.fullmatch(pattern,path) and not os.path.lexists(path),'FRESH_EXACT_OUTPUT')
    need(Path(path).parent==Path('/tmp') and Path('/tmp').resolve()==Path('/tmp'),'CANONICAL_TMP')


def expected_native(backend,paired=False):
    candidate=document(DATA['native-oracles.json'])
    return document(candidate['N16']['pairedExpected'][backend]) if paired else candidate['N02']['expectedByBackend'][backend]


def matched_local(value):
    need(value['status']=='MATCHED' and value['error'] is None and value['secondaryErrors']==[],
         'ACTUAL_MATCHED_LOCAL_CAPTURE')
    need(equal(value['integrity'],dict(sourceCurrent=True,inputsCurrent=True,evidenceComplete=True))
      and equal(value['cleanup'],dict(qualified=True,problems=[])),'LOCAL_CURRENT_CLEAN_CAPTURE')
    need(all(type(v) is int and v==0 for v in value['noEffects'].values()),'LOCAL_MEASURED_NO_EFFECTS_NOT_UNKNOWN')


def qualified_local_capture(capture,config_pin,config,worker_pin,worker,release_pin,defs):
    validate(capture,'@localCapture',defs);matched_local(capture)
    need(equal(capture['config'],config_pin) and equal(capture['workerConfig'],worker_pin)
      and equal(capture['release'],release_pin) and equal(capture['candidate'],config['candidate'])
      and equal(capture['sourceApproval'],config['sourceApproval'])
      and capture['runRole']==config['runRole'] and capture['executionSession']==config['executionSession']
      and capture['runId']==config['runId'] and capture['outputRoot']==worker['outputRoot']
      and equal(capture['environment'],ENV) and capture['notExecuted']==[] and len(capture['jobs'])==2,
      'WHOLE_LOCAL_CAPTURE_OPERANDS')
    need(equal(capture['counts'],dict(metadataRequests=2,metadataReplies=2,dValidations=0,fValidations=2)),
         'ACTUAL_TWO_LOCAL_JOB_COUNTS')
    for artifact in capture['artifacts']:checked(artifact)
    jobs=[]
    for backend,job_pin in zip(('JS','RUST'),capture['jobs']):
        need(job_pin['path']==str(Path(worker['outputRoot'])/('Q-'+backend)/'job.json'),'EXACT_OWNED_LOCAL_JOB_PATH')
        job=document(job_pin);validate(job,'@localJobCapture',defs)
        need(job['backend']==backend and job['jobId']=='Q-'+backend
          and equal(job['config'],config_pin) and equal(job['workerConfig'],worker_pin)
          and equal(job['release'],release_pin),'EXACT_ORDERED_LOCAL_JOB_GRAPH')
        verify_qualification_job(job,worker,backend,defs,config)
        jobs.append((job_pin,job))
    return jobs


def checked_local_graph(run,source_pin,source_closure,role,defs):
    validate(run,'@backendEvidenceRun',defs)
    config=document(run['config']);validate(config,'@qualificationConfig',defs)
    worker=document(run['workerConfig']);validate(worker,'@qualificationWorkerConfig',defs)
    release=document(run['release']);validate(release,'@localRelease',defs)
    need(equal(config['workerConfig'],run['workerConfig']) and equal(config['sourceApproval'],source_pin)
      and equal(worker['sourceApproval'],source_pin) and equal(worker['sourceClosure'],source_closure)
      and config['runRole']==role and worker['runRole']==role
      and config['executionSession']==worker['executionSession'] and config['runId']==worker['runId']
      and equal(config['controlAcceptance'],worker['controlAcceptance']),
      'SAME_SOURCE_INDEPENDENT_LOCAL_GRAPH')
    need(equal(release['config'],run['config']) and equal(release['workerConfig'],run['workerConfig'])
      and release['executionSession']==config['executionSession'] and release['runRole']==role,
      'LOCAL_GRAPH_EXACT_ROOT_RELEASE')
    for key in ('sourceApproval','controlAcceptance','configurationAcceptance'):
        need(equal(release[key],config[key]),'LOCAL_GRAPH_APPROVAL_RELEASE_JOIN')
    mapping=closure(source_closure);local_worker_inputs(config,worker,mapping,defs)
    source=source_approval(source_pin,source_closure,
      document(DATA['bridge-schemas.json'])['definitions'])
    controls=control_approval(config['controlAcceptance'],source_pin,source_closure,mapping,
      document(DATA['bridge-schemas.json'])['definitions'],source)
    approval=document(config['configurationAcceptance']);validate(approval,'@qualificationConfigurationApproval',defs)
    core={k:v for k,v in config.items() if k!='configurationAcceptance'}
    need(equal(approval['configuration'],core),'EXACT_CAPTURED_LOCAL_CONFIGURATION_CORE')
    reviews(approval,'ACCEPT_CONFIGURATION_ONLY',core,EXCLUDED+source['authors']+controls['authors'],
            document(DATA['bridge-schemas.json'])['definitions'])
    need(run['capture']['path']==str(Path(worker['outputRoot'])/'capture.json'),'EXACT_LOCAL_CAPTURE_PATH')
    capture=document(run['capture']);jobs=qualified_local_capture(capture,run['config'],config,
      run['workerConfig'],worker,run['release'],defs)
    return config,worker,capture,jobs


def verified_entry_graph(value,pin,worker,backend,defs):
    validate(value,'@backendEvidence',defs)
    need(equal(value['candidate'],DATA['native-oracles.json']) and equal(value['sourceApproval'],pin)
      and equal(value['sourceClosure'],worker['sourceClosure']) and value['backend']==backend,
      'QUALIFICATION_BACKEND_SOURCE_JOIN')
    requests=[];replies=[];captures={};configs={}
    for role in ('primary','qa'):
        run=value['runs'][role]
        config,wc,capture,jobs=checked_local_graph(run,pin,worker['sourceClosure'],role,defs)
        captures[role]=capture;configs[role]=config
        job_pin,job=next((d,j) for d,j in jobs if j['backend']==backend)
        need(equal(run['job'],job_pin) and equal(run['comparison'],job['comparison']),
             'BACKEND_ACTUAL_CAPTURE_JOB_MEMBER')
        requests.append(checked(job['request']));replies.append(checked(job['reply']))
    need(captures['primary']['executionSession']!=captures['qa']['executionSession'],
         'SEPARATE_QUALIFICATION_OPERATOR_SESSIONS')
    need(requests[0]==requests[1] and replies[0]==replies[1]
      and value['wholeRepliesEqual'] is True and value['wholeRequestsEqual'] is True,
      'ACTUAL_WHOLE_PRIMARY_QA_REQUEST_REPLY_EQUALITY')
    primary=document(value['primaryAcceptance']);validate(primary,'@qualificationPrimaryAcceptance',defs)
    need(equal(primary['capture'],value['runs']['primary']['capture']) and equal(primary['candidate'],value['candidate'])
      and equal(primary['sourceApproval'],pin) and equal(configs['qa']['primaryAcceptance'],value['primaryAcceptance'])
      and configs['primary']['primaryAcceptance'] is None,'ACTUAL_ACCEPTED_PRIMARY_QA_DEPENDENCY')
    for report in primary['reviewReports']:checked(report)
    return {captures[r]['executionSession'] for r in ('primary','qa')}


def verify_qualification_job(job,worker,backend,defs,config):
    validate(job,'@localJobCapture',defs);matched_local(job)
    need(job['backend']==backend and job['jobId']=='Q-'+backend
      and equal(job['candidate'],config['candidate']) and equal(job['sourceApproval'],worker['sourceApproval'])
      and job['runId']==worker['runId'] and job['runRole']==worker['runRole']
      and job['executionSession']==worker['executionSession'],'LOCAL_JOB_SOURCE_IDENTITY')
    need(equal(job['counts'],dict(metadataRequests=1,metadataReplies=1,dValidations=0,fValidations=1)),
         'LOCAL_ONE_REQUEST_REPLY_F_ONLY_COUNTS')
    request=checked(job['request']);reply=checked(job['reply'])
    for raw in (request,reply):need(raw.endswith(b'\n') and raw.count(b'\n')==1,'ONE_NATIVE_JSONL')
    need(request==checked(worker['request']),'EXACT_NATIVE_MATERIALIZED_REQUEST_BYTES')
    need(equal(loads(reply[:-1]),expected_native(backend)),'WHOLE_THIRTEEN_KEY_QUALIFICATION_REPLY')
    comparison=document(job['comparison']);validate(comparison,'@localComparison',defs)
    need(comparison['runId']==job['runId'] and comparison['jobId']==job['jobId'] and comparison['backend']==backend
      and checked(comparison['request'])==request and equal(comparison['reply'],job['reply'])
      and equal(comparison['candidate'],config['candidate']) and equal(comparison['sourceApproval'],worker['sourceApproval'])
      and equal(comparison['expectedRequest'],worker['request'])
      and equal(comparison['expectedReply'],config['expectedReplies'][backend])
      and comparison['requestByteEqual'] is True and comparison['replyWholeEqual'] is True
      and comparison['firstDifference'] is None and comparison['status']=='MATCHED' and comparison['error'] is None,
      'WHOLE_OBSERVED_COMPARISON_JOIN')
    need(equal(document(config['expectedReplies'][backend]),expected_native(backend)),'EXACT_CAPTURED_EXPECTED_WHOLE')
    receipts={}
    for phase,key in [('launch','launchReceipt'),('response','responseReceipt'),('terminal','terminalReceipt')]:
        need(job[key]['path']==str(Path(worker['outputRoot'])/('Q-'+backend)/(phase+'-receipt.json')),'FIXED_PHASE_RECEIPT_PATH')
        receipt=document(job[key]);validate(receipt,'@localSpawnReceipt',defs);receipts[phase]=receipt
        need(receipt['phase']==phase and receipt['backend']==backend and receipt['jobId']==job['jobId']
          and receipt['runId']==worker['runId'] and receipt['executionSession']==worker['executionSession']
          and receipt['runRole']==worker['runRole'] and equal(receipt['environment'],ENV),'SAME_LOCAL_NATIVE_RECEIPTS')
    terminal=receipts['terminal'];natural(terminal['lifecycle'])
    for phase in ('launch','response'):
        r=receipts[phase];life=r['lifecycle']
        need(life['launchAttempt'] is True and life['acquisition']=='ACQUIRED'
          and life['pid']==terminal['lifecycle']['pid'] and life['exitCode'] is None and life['signal'] is None
          and life['reaped'] is False and life['stdoutEOF'] is False and life['stderrEOF'] is False
          and life['timedOut'] is False and life['forced'] is False and life['error'] is None,
          'LIVE_QUIESCENT_UNREAPED_NATIVE_FRONTIER')
        for k in ('tool','argv','cwd','environment'):need(equal(r[k],terminal[k]),'SAME_OWNED_LOCAL_NATIVE_CHILD')
    need(checked(terminal['streams']['stdin'])==request and checked(terminal['streams']['stdout'])==reply
      and checked(terminal['streams']['stderr'])==b'','ACTUAL_TERMINAL_NATIVE_PIPE_CUSTODY')
    response=receipts['response']
    need(checked(response['streams']['stdin'])==request and checked(response['streams']['stdout'])==reply
      and checked(response['streams']['stderr'])==b'','ACTUAL_LIVE_NATIVE_PIPE_CUSTODY')
    launch=receipts['launch']
    need(all(checked(d)==b'' for d in launch['streams'].values()),'ACTUAL_EMPTY_LAUNCH_CAPTURE')
    tool=NODE if backend=='JS' else RUST;need(equal(terminal['tool'],tool),'FIXED_LOCAL_NATIVE_TOOL')
    directory=str(Path(worker['outputRoot'])/('Q-'+backend));need(terminal['cwd']==directory,'FIXED_LOCAL_JOB_DIRECTORY')
    need(comparison['request']['path']==str(Path(directory)/'request.jsonl')
      and equal(job['request'],worker['request']),'ACTUAL_OWNED_REQUEST_AND_SAVED_SOURCE_JOIN')
    if backend=='RUST':
        need(job['binding'] is None and job['sidecar'] is None and equal(terminal['argv'],[RUST['path']]),'FIXED_LOCAL_RUST_COMMAND')
    else:
        binding=document(job['binding']);validate(binding,'@localJSBinding',defs)
        need(equal(binding['scope'],worker['scope']) and equal(binding['closure'],worker['sourceClosure'])
          and equal(binding['fFixture'],worker['fFixture']) and equal(binding['request'],worker['request'])
          and equal(binding['workerConfig'],job['workerConfig']) and equal(binding['config'],job['config'])
          and equal(binding['release'],job['release']) and equal(binding['sourceApproval'],worker['sourceApproval'])
          and equal(binding['configurationAcceptance'],config['configurationAcceptance'])
          and equal(binding['metadataEntry'],worker['tools']['jsMetadata'])
          and binding['output']==directory,'LOCAL_JS_WHOLE_BINDING_JOIN')
        need(equal(terminal['argv'],[NODE['path'],str(HERE/'metadata_loader.mjs'),job['binding']['path'],job['binding']['sha256']]),
             'FIXED_LOCAL_JS_COMMAND')
        need(job['sidecar']['path']==str(Path(directory)/'native-reply.jsonl') and checked(job['sidecar'])==reply,
             'LOCAL_JS_RETAINED_REPLY_CUSTODY')
    internal=document(descriptor(Path(directory)/'receipt.json'))
    closed(internal,('schema','argv','cwd','environment','lifecycle','ownership','primaryError',
      'secondaryErrors','secondaryOverflow','captureComplete','streams','request','inputComplete','writtenBytes',
      'observedBytes','retainedBytes','timing','phaseMonitor'))
    need(internal['schema']=='n02316-python-owned-local-native-v1' and internal['ownership']=='REAPED'
      and internal['primaryError'] is None and internal['secondaryErrors']==[]
      and internal['secondaryOverflow'] is False and internal['captureComplete'] is True
      and internal['inputComplete'] is True and internal['writtenBytes']==len(request),
      'OWNED_INTERNAL_NATIVE_TERMINAL_CUSTODY')
    for key in ('argv','cwd','environment','lifecycle'):
        need(equal(internal[key],terminal[key]),'SAME_INTERNAL_TERMINAL_CHILD')
    need(equal(internal['request'],comparison['request']) and checked(internal['request'])==request,
         'ORIGINAL_OWNED_REQUEST_DESCRIPTOR')
    for name in ('stdin','stdout','stderr'):
        need(checked(internal['streams'][name])==checked(terminal['streams'][name]),'SAME_TERMINAL_CAPTURED_STREAM')
    for name in ('stdout','stderr'):
        raw=checked(internal['streams'][name])
        need(type(internal['observedBytes'][name]) is int
          and internal['observedBytes'][name]==internal['retainedBytes'][name]==len(raw),'FULL_NATIVE_BYTE_ACCOUNTING')
    times=internal['timing'];closed(times,('launchStartedNs','acquiredNs','requestStartedNs','requestCompletedNs',
      'replyCompletedNs','stdinClosedNs','exitObservedNs','terminalCompletedNs'))
    need(all(type(v) is int and v>=0 for v in times.values()),'ACTUAL_MEASURED_NATIVE_TIMES')
    launch,acquired,request_start,request_end,response_at,closed_at,exit_at,end=[times[k] for k in
      ('launchStartedNs','acquiredNs','requestStartedNs','requestCompletedNs','replyCompletedNs',
       'stdinClosedNs','exitObservedNs','terminalCompletedNs')]
    need(launch<=acquired<=request_start<=request_end<=response_at<=closed_at<=exit_at<=end
      and acquired-launch<15000000000 and response_at-request_start<15000000000
      and end-closed_at<5000000000,'ACTUAL_SEPARATE_START_COMBINED_REPLY_TERMINAL_BOUNDS')
    need(equal(terminal['timing'],dict(startedMonotonicMs=launch//1000000,
      responseMonotonicMs=response_at//1000000,terminalMonotonicMs=end//1000000,
      elapsedMilliseconds=(end-launch)//1000000)),'EXACT_PUBLIC_NATIVE_TIMING_PROJECTION')
    phase=internal['phaseMonitor']
    need(phase['timeoutCause'] is None and phase['observations']==[]
      and all(v['startedNs'] is None and v['completedNs'] is None for v in phase['anchors'].values()),
      'LOCAL_NO_ACQUISITION_CONSUMER_PHASE_REINTERPRETATION')




def qualified_counts(actual,expected):
    need(type(actual) is dict and all(type(v) is int and v>=0 for v in actual.values())
      and equal(actual,expected),'MEASURED_COUNTS_NO_DEFAULT_ZERO')
    return actual


def check_native_review_set(pack,aggregate,source_pin,source_authors):
    need(equal(aggregate,dict(schema='n02316-native-oracle-evidence-set-v1',candidate=pack['candidate'],
      sourceApproval=source_pin,actualEvidence=pack['actualEvidence'])),'WHOLE_NATIVE_AGGREGATE_JOIN')
    rows=pack['reviews']
    need(type(rows) is list and len(rows)==2 and {r['role'] for r in rows}=={'qa','security'}
      and len({r['session'] for r in rows})==2,'NATIVE_DISTINCT_REVIEW_ROLES')
    for row in rows:
        need(row['decision']=='ACCEPT_NATIVE_ORACLES_ONLY' and equal(row['subject'],pack['evidenceSet'])
          and row['session'] not in EXCLUDED+pack['authors']+source_authors,
          'COMMON_FULL_NONAUTHOR_AGGREGATE_REVIEW')


def native_qualification(pin,source_pin,source_closure,defs,qualification_defs):
    pack=document(pin);validate(pack,'@nativeOracleQualification',defs)
    need(equal(pack['candidate'],DATA['native-oracles.json']) and equal(pack['sourceApproval'],source_pin),
         'EXACT_NATIVE_CANDIDATE_SOURCE_APPROVAL')
    aggregate=document(pack['evidenceSet']);validate(aggregate,'@nativeOracleEvidenceSet',defs)
    need(equal(aggregate,dict(schema='n02316-native-oracle-evidence-set-v1',candidate=pack['candidate'],
      sourceApproval=source_pin,actualEvidence=pack['actualEvidence'])),'WHOLE_NATIVE_AGGREGATE_JOIN')
    source=document(source_pin)
    check_native_review_set(pack,aggregate,source_pin,source['authors'])
    rows=pack['reviews'];need({r['role'] for r in rows}=={'qa','security'} and len(rows)==2
      and len({r['session'] for r in rows})==2,'NATIVE_DISTINCT_REVIEW_ROLES')
    for row in rows:
        validate(row,'@nativeOracleQualificationReview',defs)
        need(row['decision']=='ACCEPT_NATIVE_ORACLES_ONLY' and equal(row['subject'],pack['evidenceSet'])
          and row['session'] not in EXCLUDED+pack['authors']+source['authors'],'COMMON_FULL_NONAUTHOR_AGGREGATE_REVIEW')
        checked(row['subject'])
    operators=set();graphs={}
    for backend in ('JS','RUST'):
        evidence=document(pack['actualEvidence'][backend]);graphs[backend]=evidence
        operators.update(verified_entry_graph(evidence,source_pin,dict(sourceClosure=source_closure),backend,qualification_defs))
    need(operators<=set(pack['authors']),'ALL_NATIVE_OPERATORS_DISCLOSED_AUTHORS')
    for row in pack['reviews']:need(row['session'] not in operators,'NATIVE_OPERATOR_CANNOT_APPROVE_OWN_RUN')
    for role in ('primary','qa'):
        for key in ('capture','config','workerConfig','release'):
            need(equal(graphs['JS']['runs'][role][key],graphs['RUST']['runs'][role][key]),'SAME_COMPLETE_TWO_BACKEND_RUN_GRAPH')
    need(equal(graphs['JS']['primaryAcceptance'],graphs['RUST']['primaryAcceptance']),'SAME_PRIMARY_ACCEPTANCE_BOTH_BACKENDS')
    return pack


def _with_inventory(fn,*args):
    inventory=_VerifiedEvidenceInventory();token=_admission_evidence.set(inventory)
    try:return fn(*args,inventory)
    finally:_admission_evidence.reset(token)


def verify(manifest_path,manifest_sha,release_path,release_sha,execution_session,run_role):
    return _with_inventory(_verify_target,manifest_path,manifest_sha,release_path,release_sha,execution_session,run_role)


def _external_inputs(path,sha,release_path,release_sha):
    pin=descriptor(path);release_pin=descriptor(release_path)
    need(pin['sha256']==sha and release_pin['sha256']==release_sha,'EXTERNAL_INPUT_RELEASE_SHA')
    return pin,release_pin,document(pin),document(release_pin)


def _verify_target(path,sha,rpath,rsha,session,role,inventory):
    md,rd,m,r=_external_inputs(path,sha,rpath,rsha)
    schemas=document(DATA['bridge-schemas.json']);defs=schemas['definitions']
    validate(m,'@manifest',defs);validate(r,'@release',defs)
    need(r['decision']=='RELEASE_EXACT_N02316_RUN_ONLY' and r['rootSession']=='/root'
      and r['executionSession']==session and r['runRole']==role and role in ('primary','qa')
      and equal(r['manifest'],md),'EXACT_EXTERNAL_ROOT_RELEASE')
    for name in ('sourceReviews','controlAcceptance','configurationAcceptance'):
        need(equal(r[name],m[name]),'RELEASE_EXACT_APPROVALS')
    mapping=fixed_source(m['sourceClosure']);source=source_approval(m['sourceReviews'],m['sourceClosure'],defs)
    controls=control_approval(m['controlAcceptance'],m['sourceReviews'],m['sourceClosure'],mapping,defs,source)
    configuration_approval(m['configurationAcceptance'],{k:v for k,v in m.items() if k!='configurationAcceptance'},defs,source,controls)
    for key,file in [('workerSchema','worker-schemas.json'),('profile','profile.json'),
                     ('selection','selection-map.json'),('protectedDeltas','protected-deltas.json')]:
        need(equal(m[key],DATA[file]),'FIXED_N_DATA_BINDING')
    expected=fixed_prerequisites(mapping)
    need(equal({k:v for k,v in m['prerequisites'].items() if k!='nativeOracleQualification'},expected),
         'EXACT_TARGET_PREREQUISITES')
    qdefs=qualification_definitions()
    native_qualification(m['prerequisites']['nativeOracleQualification'],m['sourceReviews'],m['sourceClosure'],defs,qdefs)
    profile=document(DATA['profile.json']);selection=document(DATA['selection-map.json'])
    need(equal(m['orderedCells'],selection['orderedCells']),'EXACT_TEN_CELL_ORDER')
    fresh_output(m['outputRoot'],'/tmp/e6n02316-'+role+'-[a-z0-9]{6,12}')
    workers={};family=selection['fixtureFamily']
    for cell in selection['cells']:
        name=cell['cellId'];w=document(m['workerInputs'][name]);validate(w,'@workerData',defs)
        need(w['cellId']==name and w['windowId']==cell['windowId'] and w['relay']==cell['relay']
          and w['backend']==cell['metadataBackend'],'SAME_SELECTED_WORKER_CELL')
        native=cell['subprofileId']!='N03'
        need(equal(w['scope'],family['scope'] if native else None)
          and w['secretHex']==('0'*63+'2' if native else None),'FIXED_NATIVE_SCOPE_SECRET')
        for slot,key in [('D','dWire'),('F','fWire')]:
            wanted=next((j['wire'] for j in cell['jobs'] if j['slot']==slot),None)
            need(equal(w[key],wanted),'EXACT_SELECTED_EXISTING_WIRE')
            if wanted:member(mapping,wanted);checked(wanted)
        workers[name]=w
    transport=accepted_transport(mapping)
    closure(m['sourceClosure']);inventory.recheck()
    return dict(mode='TARGET',manifest=m,manifestDescriptor=md,releaseDescriptor=rd,profile=profile,
      sourceClosure=m['sourceClosure'],sourceApproval=m['sourceReviews'],workers=workers,
      output=m['outputRoot'],definitions=defs,transportPrerequisites=transport,
      recheckAuthorityEvidence=inventory.recheck)


def verify_qualification(config_path,config_sha,release_path,release_sha,execution_session,run_role):
    return _with_inventory(_verify_local,config_path,config_sha,release_path,release_sha,execution_session,run_role)


def _local_inventory_descriptor(pin,descriptor_defs):
    """Opaque source metadata only; bounded before membership/hash/remember."""
    validate(pin,'@closureEntry',descriptor_defs)
    need(pin['bytes']<=EVIDENCE_MAX_FILE_BYTES,'LOCAL_INVENTORY_OPAQUE_FILE_BOUND')


def local_worker_inputs(config,worker,mapping,defs):
    expected=fixed_prerequisites(mapping)
    expected.update(currentCarrierGate=TRANSPORT_GATE,currentCarrierRelease=TRANSPORT_RELEASE)
    need(equal(worker['sourcePrerequisites'],expected),'CURRENT_COMPLETE_LOCAL_PREREQUISITES')
    need(equal(worker['acceptedPlan'],LOCAL_PLAN) and equal(worker['acceptedInertFreeze'],INERT_ACCEPTANCE)
      and equal(worker['workerSchema'],DATA['worker-schemas.json'])
      and equal(worker['qualificationSchema'],descriptor(HERE/'qualification-schemas.json')),
      'FIXED_LOCAL_DEPENDENCIES')
    family=document(DATA['selection-map.json'])['fixtureFamily'];candidate=document(DATA['native-oracles.json'])
    need(equal(config['candidate'],DATA['native-oracles.json']) and equal(worker['environment'],ENV)
      and equal(worker['scope'],family['scope']) and equal(worker['fFixture'],family['incomingWires']['F']),
      'SAVED_F_ONLY_SOURCE_INPUTS')
    for key,pin in worker['tools'].items():member(mapping,pin)
    metadata=str(ROOT/'experiments/prototypes/e06_invoice_file_v1/js/metadata.mjs')
    need(equal(worker['tools']['node'],NODE) and equal(worker['tools']['python'],PYTHON)
      and equal(worker['tools']['nativeRust'],RUST) and worker['tools']['jsMetadata']['path']==metadata,
      'FIXED_LOCAL_ALL_TOOLS')
    # The accepted57-role map is an inventory, not a materialization record.
    # Keep every original role/pin current independently, including large tools:
    # stream their hashes; never feed a >32MiB tool into the bounded JSON reader.
    qschema=qualification_schema();inventory=worker['inputInventory']
    need(equal(inventory,qschema['qualificationInputInventory']),'EXACT_SAVED_INPUT_INVENTORY')
    member(mapping,inventory);role_map=document(inventory)
    closed(role_map,('acceptedInertFreeze', 'acceptedInertSourceDataClosure', 'N_SOURCE.md', 'N_contract.json', 'N_interfaces.md', 'N_profile.json', 'N_selection-map.json', 'N_native-oracles.json', 'N_NATIVE_ORACLES.md', 'N_bridge-schemas.json', 'N_worker-schemas.json', 'N_oracles.json', 'N_protected-deltas.json', 'N_BRIDGE.md', 'inertFreezeReview_qa', 'inertFreezeReview_security', 'acceptedPositivePair', 'positivePairComparison', 'positive_sourceClosure', 'positive_sourceApproval', 'canonicalE06Plan', 'experimentReadme', 'canonicalE06Record', 'nativeSource_JS_METADATA', 'nativeSource_RUST_METADATA', 'nativeSource_JS_TRANSPORT', 'nativeSource_RUST_ADAPTER', 'nativeSource_RUST_BASELINE', 'existing_fWire', 'existing_F', 'existing_preparationProofs', 'existing_catalogue', 'existing_R5MaterializationAcceptance', 'existing_R5InputAcceptance', 'unchangedN16PairedExpected_JS', 'unchangedN16PairedExpected_RUST', 'existingIncomingFInspector_JS_request', 'existingIncomingFInspector_JS_rawReply', 'existingIncomingFInspector_RUST_request', 'existingIncomingFInspector_RUST_rawReply', 'positivePrimaryManifest', 'pinnedNode', 'pinnedPython', 'pinnedNativeRust', 'protectedI4_metadata_loader.mjs', 'protectedI4_wire.mjs', 'protectedI4_protocol.mjs', 'positive_primary_capture', 'positive_primary_JS_nativeCall', 'positive_primary_JS_nativeTerminal', 'positive_primary_RUST_nativeCall', 'positive_primary_RUST_nativeTerminal', 'positive_qa_capture', 'positive_qa_JS_nativeCall', 'positive_qa_JS_nativeTerminal', 'positive_qa_RUST_nativeCall', 'positive_qa_RUST_nativeTerminal'))
    evidence_inventory=_admission_evidence.get()
    descriptor_defs=document(DATA['bridge-schemas.json'])['definitions']
    for pin in role_map.values():
        _local_inventory_descriptor(pin,descriptor_defs);member(mapping,pin)
        need(equal(descriptor(pin['path']),pin),'CURRENT_ORIGINAL_LOCAL_INVENTORY_MEMBER')
        if evidence_inventory is not None:evidence_inventory.remember(pin)
    # Distinct immutable derivation: no worker field is added or repurposed.
    materialization=qschema['qualificationMaterialization']
    member(mapping,materialization);materialized=document(materialization)
    closed(materialized,('schema','state','coordinator','source','acceptedPlan','outputs',
      'derivation','serialization','workerCheckerSeparation','limits','executionReleased'))
    need(materialized['schema']=='e06-n02316-local-qualification-input-materialization-v1'
      and materialized['state']=='SOURCE_DATA_ONLY_NOT_OBSERVED' and materialized['coordinator']=='/root'
      and materialized['executionReleased'] is False
      and equal(materialized['source'],DATA['native-oracles.json'])
      and equal(materialized['acceptedPlan'],LOCAL_PLAN),'LOCAL_INPUT_ORIGINAL_CANDIDATE_LINEAGE')
    need(equal(materialized['derivation'],{'request.jsonl':'/N02/requestCandidate',
      'JS.expected.json':'/N02/expectedByBackend/JS','RUST.expected.json':'/N02/expectedByBackend/RUST'}),
      'EXACT_LOCAL_MATERIALIZATION_DERIVATION')
    outputs=materialized['outputs'];closed(outputs,('request.jsonl','JS.expected.json','RUST.expected.json'))
    for name,pin in outputs.items():
        validate(pin,'@descriptor',descriptor_defs);member(mapping,pin)
        need(pin['path']==str(Path(materialization['path']).parent/name),'EXACT_LOCAL_MATERIALIZED_OUTPUT_PATH')
        checked(pin)
    need(equal(worker['request'],outputs['request.jsonl'])
      and equal(config['expectedReplies'],{b:outputs[b+'.expected.json'] for b in ('JS','RUST')}),
      'FIXED_MATERIALIZED_INPUT_DESCRIPTORS')
    raw=checked(worker['request']);need(raw.endswith(b'\n') and raw.count(b'\n')==1,'ONE_SOURCE_F_ONLY_REQUEST')
    request=loads(raw[:-1]);validate(request,'@nativeRequestN02',document(DATA['bridge-schemas.json'])['definitions'])
    need(equal(request,candidate['N02']['requestCandidate']),'EXACT_MATERIALIZED_REQUEST_WHOLE')
    for backend in ('JS','RUST'):
        need(equal(document(config['expectedReplies'][backend]),expected_native(backend)),'EXACT_MATERIALIZED_EXPECTED_WHOLE')
    need(config['runId']==worker['runId'] and config['runRole']==worker['runRole']
      and config['executionSession']==worker['executionSession'],'SAME_LOCAL_CONFIG_WORKER_IDENTITY')
    need(re.fullmatch('/tmp/e6n-fonly-'+config['runRole']+'-[a-z0-9]{6,12}',worker['outputRoot']),
         'EXACT_LOCAL_OUTPUT_NAMESPACE')
    for job in worker['jobs']:
        need(job['output']==str(Path(worker['outputRoot'])/job['jobId']),'EXACT_LOCAL_JOB_DIRECTORY_JOIN')


def _verify_local(path,sha,rpath,rsha,session,role,inventory):
    cd,rd,c,r=_external_inputs(path,sha,rpath,rsha)
    # Source input bytes are verified before any target or helper imports. The
    # source-first path does not call native_qualification or demand its result.
    defs=document(DATA['bridge-schemas.json'])['definitions']
    qdefs=qualification_definitions()
    validate(c,'@qualificationConfig',qdefs);validate(r,'@localRelease',qdefs)
    wc=document(c['workerConfig']);validate(wc,'@qualificationWorkerConfig',qdefs)
    need(c['executionSession']==session and wc['executionSession']==session and r['executionSession']==session
      and c['runRole']==role and wc['runRole']==role and r['runRole']==role and role in ('primary','qa')
      and r['rootSession']=='/root' and r['decision']=='RELEASE_EXACT_LOCAL_F_ONLY_RUN_ONLY'
      and equal(r['config'],cd) and equal(r['workerConfig'],c['workerConfig']),'EXACT_LOCAL_EXTERNAL_ROOT_RELEASE')
    for key in ('sourceApproval','controlAcceptance','configurationAcceptance'):
        need(equal(r[key],c[key]),'LOCAL_RELEASE_APPROVAL_JOIN')
    mapping=fixed_source(wc['sourceClosure']);local_worker_inputs(c,wc,mapping,qdefs)
    need(equal(c['sourceApproval'],wc['sourceApproval']) and equal(c['controlAcceptance'],wc['controlAcceptance']),
         'LOCAL_SHARED_APPROVALS')
    source=source_approval(c['sourceApproval'],wc['sourceClosure'],defs)
    controls=control_approval(c['controlAcceptance'],c['sourceApproval'],wc['sourceClosure'],mapping,defs,source)
    approval=document(c['configurationAcceptance']);validate(approval,'@qualificationConfigurationApproval',qdefs)
    core={k:v for k,v in c.items() if k!='configurationAcceptance'}
    need(equal(approval['configuration'],core),'EXACT_LOCAL_CONFIGURATION_CORE')
    reviews(approval,'ACCEPT_CONFIGURATION_ONLY',core,EXCLUDED+source['authors']+controls['authors'],defs)
    if role=='primary':need(c['primaryAcceptance'] is None,'PRIMARY_NO_PRIOR_ACCEPTANCE')
    else:
        primary=document(c['primaryAcceptance']);validate(primary,'@qualificationPrimaryAcceptance',qdefs)
        primary_capture=document(primary['capture']);validate(primary_capture,'@localCapture',qdefs)
        need(primary['decision']=='ACCEPT_PRIMARY_LOCAL_F_ONLY_OBSERVATION_ONLY' and primary_capture['runRole']=='primary'
          and primary_capture['executionSession']!=session and equal(primary['candidate'],c['candidate'])
          and equal(primary['sourceApproval'],c['sourceApproval']),'QA_DISTINCT_ACCEPTED_PRIMARY')
        need(len(primary_capture['jobs'])==2,'QA_REQUIRES_COMPLETE_PRIMARY_TWO_JOBS')
        first_job=document(primary_capture['jobs'][0]);validate(first_job,'@localJobCapture',qdefs)
        graph=dict(capture=primary['capture'],job=primary_capture['jobs'][0],config=primary_capture['config'],
          workerConfig=primary_capture['workerConfig'],release=primary_capture['release'],comparison=first_job['comparison'])
        checked_local_graph(graph,c['sourceApproval'],wc['sourceClosure'],'primary',qdefs)
        for report in primary['reviewReports']:checked(report)
    fresh_output(wc['outputRoot'],'/tmp/e6n-fonly-'+role+'-[a-z0-9]{6,12}')
    transport=accepted_transport(mapping)
    closure(wc['sourceClosure']);inventory.recheck()
    return dict(mode='LOCAL_F_ONLY',config=c,configDescriptor=cd,workerConfig=wc,
      workerConfigDescriptor=c['workerConfig'],release=r,releaseDescriptor=rd,
      sourceClosure=wc['sourceClosure'],sourceApproval=c['sourceApproval'],controlAcceptance=c['controlAcceptance'],
      definitions=qdefs,workerDefinitions=qualification_schema()['workerDefinitions'],output=wc['outputRoot'],
      verifiedEvidence=[dict(path=p,bytes=n,sha256=h) for p,n,h in inventory._pins.values()],
      transportPrerequisites=transport,
      recheckAuthorityEvidence=inventory.recheck)
