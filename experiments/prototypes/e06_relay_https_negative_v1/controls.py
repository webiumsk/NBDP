"""SOURCE ONLY: finite meaningful pure-refusal calibrations, never native PASS.

No import executes a control. A separately reviewed source-only bootstrap must
pin this module/closure and release its fixed CLI. Target and LOCAL admission
both still require actual independently reviewed control evidence. No socket,
crypto, child, target or experiment is used by these pure calibration definitions.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ADMISSION={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/admission.py', 'bytes': 53263, 'sha256': '24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'}
PYTHON={'path':'/home/peterhorvath/.miniforge3/bin/python3.13','bytes':32959480,
 'sha256':'5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
     'WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'}


def load_pinned(path,pin,name):
    raw=Path(path).read_bytes()
    if str(Path(path).resolve(strict=True))!=str(path) or Path(path).is_symlink() \
      or len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise ValueError('FIXED_SOURCE_PIN')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def refuses(A,fn):
    try:fn()
    except (A.Refusal,ValueError,KeyError,TypeError,UnicodeError):return True
    return False


def evaluate(A,R,C,source_closure,directory):
    """Pure control definitions. Execution awaits separate exact bootstrap release."""
    defs=A.document(A.DATA['bridge-schemas.json'])['definitions'];rows=[]
    def group(name,checks):
        if not checks or not all(v is True for v in checks):raise ValueError('CONTROL_MISMATCH:'+name)
        rows.append(dict(id=name,matched=True,scope='PURE_REFUSAL_ONLY'))
    group('CLOSED_TYPED_JSON',[
      refuses(A,lambda:A.loads(b'{"a":1,"a":2}')),
      refuses(A,lambda:A.loads(b'{"n":-0}')),
      refuses(A,lambda:A.loads(b'{"n":1.0}')),
      refuses(A,lambda:A.loads(b'{"n":9007199254740992}')),
      refuses(A,lambda:A.loads(b'{"s":"\\ud800"}')),
      A.equal(A.loads(b'{"a":[true,null,1]}'),{'a':[True,None,1]})])
    shape={'record':{'x':{'integer':[0,2]}}}
    group('MISSING_EXTRA_KEYS',[
      refuses(A,lambda:A.validate({},shape,{})),
      refuses(A,lambda:A.validate({'x':1,'y':0},shape,{})),
      refuses(A,lambda:A.validate({'x':True},shape,{})),
      A.validate({'x':1},shape,{})=={'x':1}])
    file=Path(directory)/'pin-control.bin'
    fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:out.write(b'original')
    expected=A.descriptor(file)
    file.write_bytes(b'changed')
    group('ORIGINAL_PIN_DRIFT',[refuses(A,lambda:A.checked(expected)),expected['sha256']!=A.descriptor(file)['sha256']])
    selection=A.document(A.DATA['selection-map.json']);oracles=A.document(A.DATA['oracles.json'])
    counter_shape=defs['counters'];good=selection['cells'][0]['completedStepCounts'];bad=dict(good,metadataRequests=None)
    group('UNKNOWN_COUNTS_REFUSE',[
      refuses(A,lambda:A.qualified_counts(bad,good)),not A.equal(good,bad),good['metadataRequests']==1])
    native=A.expected_native('JS');wrong=json.loads(json.dumps(native))
    wrong['validation']['F']['rawReply']['value']['rumor']['tags'][0][1]='0'*64
    group('WHOLE_NATIVE_DEEP_COMPARE',[not A.equal(native,wrong),len(native)==13,
      not A.equal(native,dict(native,extra=True)),not A.equal({'n':0},{'n':False})])
    n03=[s for s in oracles['steps'] if s['cellId']=='N03-SF']
    group('N03_NO_NATIVE',[all(s['expectedWhole']['metadataRecord'] is None for s in n03),
      selection['cells'][4]['nativeRequestCount']==0,
      n03[0]['expectedWhole']['counts']['dValidations']==0,
      n03[-1]['expectedTerminal']['metadataTerminal'] is None])
    n16=next(c for c in oracles['cases'] if c['cellId']=='N16-SF-JS')
    group('N16_DENY_NO_GENERATION',[n16['expectedLocalPolicy']['decision']=='DENY',
      n16['expectedLocalPolicy']['scope']=='ATTACHMENT_ACQUISITION_ONLY',
      n16['expectedSealRefusal']['generation'] is None,
      n16['expectedSealRefusal']['attemptReservation'] is None,
      n16['expectedSealRefusal']['reason']=='LOCAL_ACQUISITION_PERMISSION_DENIED'])
    # Actual checker fixed binding resolver; no supplied arbitrary resolver.
    C.A=A;checker=object.__new__(C.Checker);checker.defs=defs
    group('BINDING_CONTEXT_REFUSE',[
      refuses(A,lambda:checker.resolve({'bind':'RECEIVED_F'},{})),
      refuses(A,lambda:checker.resolve({'bind':'NOT_A_BINDING'},{'NOT_A_BINDING':expected})),
      refuses(A,lambda:checker.resolve({'bind':'CASE_PID'},{'CASE_PID':None})),
      refuses(A,lambda:checker.resolve({'bind':'CASE_PID','extra':1},{'CASE_PID':7})),
      checker.resolve({'bind':'CASE_PID'},{'CASE_PID':7})==7])
    source=expected;js=dict(expected);rust=dict(expected,sha256='1'*64)
    aggregate=dict(schema='n02316-native-oracle-evidence-set-v1',candidate=source,sourceApproval=source,
                   actualEvidence=dict(JS=js,RUST=rust))
    pack=dict(candidate=source,sourceApproval=source,actualEvidence=aggregate['actualEvidence'],evidenceSet=source,
      authors=['/root/operator'],reviews=[dict(role=r,session='/root/reviewer-'+r,
      decision='ACCEPT_NATIVE_ORACLES_ONLY',subject=source) for r in ('qa','security')])
    A.check_native_review_set(pack,aggregate,source,[])
    split=json.loads(json.dumps(pack));split['reviews'][1]['subject']=rust
    dropped=dict(aggregate,actualEvidence=dict(JS=js))
    group('COMMON_WHOLE_AGGREGATE',[
      refuses(A,lambda:A.check_native_review_set(split,aggregate,source,[])),
      refuses(A,lambda:A.check_native_review_set(pack,dropped,source,[]))])
    own=json.loads(json.dumps(pack));own['reviews'][0]['session']='/root/operator'
    duplicate=json.loads(json.dumps(pack));duplicate['reviews'][1]['session']=duplicate['reviews'][0]['session']
    group('INDEPENDENT_NONAUTHOR_REVIEWS',[
      refuses(A,lambda:A.check_native_review_set(own,aggregate,source,[])),
      refuses(A,lambda:A.check_native_review_set(duplicate,aggregate,source,[])),
      refuses(A,lambda:A.check_native_review_set(pack,aggregate,source,['/root/reviewer-qa']))])
    # Pure ownership supervisor object; do not start any process or invoke run().
    owner=R.OwnedCase([],Path(directory),ENV,12345,lambda:None,phase_progress=None)
    owner.primary_error(ValueError('first'));owner.primary_error(ValueError('later'))
    group('ORIGINAL_ERROR_PRESERVED',[owner.primary['message']=='first',owner.life['error']['message']=='first'])
    group('RETAINED_OWNERSHIP_NO_POST_REAP_SIGNAL',[
      R.pure_group_signal_allowed('HELD','RUNNING',None) is True,
      R.pure_group_signal_allowed('HELD','EXITED',None) is True,
      R.pure_group_signal_allowed('REAPED','EXITED',0) is False,
      R.pure_group_signal_allowed('UNKNOWN','RUNNING',None) is False,
      owner.phase_progress is None])
    anchors={n:dict(startedNs=None,completedNs=None) for n in ('acquisition','consumer')}
    group('FIXED_DEADLINES',[R.pure_phase_timeout(999,1000,anchors) is None,
      R.pure_phase_timeout(1000,1000,anchors)=='CASE_OUTER_DEADLINE',
      owner.phase_progress is None])
    tree=ast.parse((HERE/'admission.py').read_text())
    local=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_verify_local')
    calls={n.func.id for n in ast.walk(local) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
    group('SOURCE_FIRST_NO_CYCLE',[{'fixed_source','source_approval','control_approval','accepted_transport'}<=calls,
      'native_qualification' not in calls])
    A.need([r['id'] for r in rows]==A.CONTROL_IDS,'EXACT_N_PURE_CONTROL_IDS')
    A.closure(source_closure)
    return dict(schema='n02316-pure-controls-capture-v1',sourceClosure=source_closure,rows=rows,finalIntegrity=True)


def main(argv):
    if len(argv)!=4:raise ValueError('CLI controls.py SOURCE_CLOSURE SHA ABS_CONTROL_OUTPUT')
    if dict(os.environ)!=ENV:raise ValueError('EXACT_CONTROL_ENVIRONMENT')
    if Path(sys.executable).resolve(strict=True)!=Path(PYTHON['path']):raise ValueError('FIXED_CONTROL_PYTHON')
    digest=hashlib.sha256();size=0
    with open(PYTHON['path'],'rb') as handle:
        while block:=handle.read(1048576):digest.update(block);size+=len(block)
    if size!=PYTHON['bytes'] or digest.hexdigest()!=PYTHON['sha256']:raise ValueError('FIXED_CONTROL_PYTHON_PIN')
    A=load_pinned(ADMISSION['path'],ADMISSION,'_n02316_control_admission')
    pin=A.descriptor(argv[1]);A.need(pin['sha256']==argv[2],'EXTERNAL_CONTROL_SOURCE_SUBJECT')
    source_closure=A.document(pin);mapping=A.fixed_source(source_closure)
    directory=Path(argv[3]);A.private_dir(directory)
    A.need(pin['path']==str(directory/'source-closure.json'),'FIXED_CONTROL_SUBJECT_PATH')
    R=load_pinned(str(HERE/'runner.py'),mapping[str(HERE/'runner.py')],'_n02316_control_runner')
    R.init_owned_case_io(A)
    C=load_pinned(str(HERE/'checker.py'),mapping[str(HERE/'checker.py')],'_n02316_control_checker')
    value=evaluate(A,R,C,source_closure,directory)
    sys.stdout.write(json.dumps(value,separators=(',',':'))+'\n')
    return 0


if __name__=='__main__':
    try:code=main(sys.argv)
    except BaseException as exc:sys.stderr.write(type(exc).__name__+': '+str(exc)[:16384]+'\n');code=2
    raise SystemExit(code)
