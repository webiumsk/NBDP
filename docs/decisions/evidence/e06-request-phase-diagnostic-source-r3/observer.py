"""SOURCE ONLY: fixed external observation of a genuine fresh LOCAL run.

Inert on import. No generic command, attach PID or admission bypass is exposed.
Root must supply actual reviewed activation metadata and two fresh authorizations.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import time

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE=ROOT/'docs/decisions/evidence/e06-request-phase-diagnostic-source-r3'
PREP=ROOT/'docs/decisions/evidence/e06-local-fonly-primary-preparation-r3'
EXEC=ROOT/'docs/decisions/evidence/e06-local-fonly-primary-execution-r3'
CONFIG=HERE/'observer-configuration-core.json'
OUTPUT=HERE/'actual-request-phase-r1'
NATIVE_OUTPUT=Path('/tmp/e6n-fonly-primary-0f7c2a38d95b')
RUN_ID='0f7c2a38d95b'
SCOPE='DIAGNOSTIC_REAL_REQUEST_PHASE_ONLY'
AUTHORS=['/root','/root/e06_local_configuration','/root/local_monitor_controls']
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
     'WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'}
CAPS={'trace':16777216,'stdout':65536,'stderr':262144}
TOTAL_SECONDS=1800
ACTIVE_SECONDS=1770
CLEANUP_SECONDS=30
TRACE_OPTIONS=['--kill-on-exit','--interruptible=1','-f','-qq','-ttt','-s','256',
 '-e','trace=execve,clone,clone3,fork,vfork,pipe,pipe2,dup,dup2,dup3,fcntl,openat,read,pread64,readv,write,pwrite64,writev,close',
 '-e','raw=read,pread64,readv,write,pwrite64,writev']
READ_WRITE_SYSCALLS={'read','pread64','readv','write','pwrite64','writev'}


class Refusal(ValueError):pass

def need(ok,message):
    if not ok:raise Refusal(message)

def strict(raw):
    need(type(raw) is bytes and len(raw)<=4194304,'DATA_JSON_BOUND')
    def pairs(rows):
        result={}
        for k,v in rows:need(k not in result,'DUPLICATE_JSON_KEY');result[k]=v
        return result
    return json.loads(raw.decode('utf-8','strict'),object_pairs_hook=pairs,
      parse_float=lambda _:need(False,'INTEGER_METADATA_ONLY'),
      parse_constant=lambda _:need(False,'FINITE_METADATA_ONLY'))

def closed(value,keys):need(type(value) is dict and set(value)==set(keys),'CLOSED_KEYS')

def descriptor(path,live=lambda:None):
    p=Path(path);live()
    need(p.is_absolute() and p.resolve(strict=True)==p and not p.is_symlink(),'CANONICAL_REGULAR_PATH')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);h=hashlib.sha256();size=0
    with os.fdopen(fd,'rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=536870912,'REGULAR_BOUNDED_ORIGINAL')
        while block:=f.read(1048576):live();size+=len(block);h.update(block)
        after=os.fstat(f.fileno())
    ident=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_uid,s.st_gid)
    need(ident(before)==ident(after) and size==before.st_size,'ORIGINAL_CHANGED_DURING_HASH');live()
    return {'path':str(p),'bytes':size,'sha256':h.hexdigest()}

def file_state(path,live=lambda:None):
    d=descriptor(path,live);s=Path(path).lstat()
    return {'descriptor':d,'stat':{'device':s.st_dev,'inode':s.st_ino,'size':s.st_size,
       'mtimeNs':s.st_mtime_ns,'ctimeNs':s.st_ctime_ns,'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid}}

def checked(pin,live=lambda:None):
    closed(pin,('path','bytes','sha256'));need(descriptor(pin['path'],live)==pin,'EXACT_DESCRIPTOR:'+pin['path']);return pin

def doc(pin,live=lambda:None):
    checked(pin,live);need(pin['bytes']<=4194304,'DATA_DOCUMENT_BOUND');raw=Path(pin['path']).read_bytes()
    need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'DOCUMENT_REREAD_CHANGED')
    live();return strict(raw)

def owned(path):
    p=Path(path);s=p.lstat();need(stat.S_ISREG(s.st_mode) and not p.is_symlink()
      and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600,'OWNED_REGULAR_0600')

def write(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return descriptor(path)

def tree_paths(root):
    p=Path(root);need(p.resolve(strict=True)==p and p.is_dir(),'FIXED_ORIGINAL_TREE')
    files=[]
    for f in sorted(p.rglob('*')):
        s=f.lstat();need(not stat.S_ISLNK(s.st_mode),'NO_ORIGINAL_TREE_LINKS')
        if stat.S_ISDIR(s.st_mode):continue
        need(stat.S_ISREG(s.st_mode),'NO_ORIGINAL_TREE_SPECIALS');files.append(str(f))
    return files

class Originals:
    def __init__(self,live):self.live=live;self.rows={};self.total=0
    def remember(self,pin):
        closed(pin,('path','bytes','sha256'))
        if pin['path'] in self.rows:
            need(self.rows[pin['path']]['descriptor']==pin,'CONFLICTING_ORIGINAL_DESCRIPTOR');return
        need(len(self.rows)<4096 and self.total+pin['bytes']<=2147483648,'FINITE_ORIGINAL_INVENTORY')
        row=file_state(pin['path'],self.live);need(row['descriptor']==pin,'CURRENT_ORIGINAL_PIN:'+pin['path'])
        self.rows[pin['path']]=row;self.total+=pin['bytes']
    def document(self,pin):
        self.remember(pin);return doc(pin,self.live)
    def recheck(self):
        for path,row in self.rows.items():need(file_state(path,self.live)==row,'ORIGINAL_BYTES_OR_STAT_DRIFT:'+path)


def host_context():
    return {'uid':os.getuid(),'gid':os.getgid(),'uidMap':Path('/proc/self/uid_map').read_text(),
      'gidMap':Path('/proc/self/gid_map').read_text(),'userNamespace':os.readlink('/proc/self/ns/user'),
      'mountNamespace':os.readlink('/proc/self/ns/mnt')}


def require_host(expected,actual):need(actual==expected,'EXACT_REVIEWED_HOST_CONTEXT_REQUIRED')


def trace_policy(options):
    need(options==TRACE_OPTIONS,'FIXED_PRIVACY_REVIEWED_TRACE_OPTIONS')
    selected=options[options.index('trace=execve,clone,clone3,fork,vfork,pipe,pipe2,dup,dup2,dup3,fcntl,openat,read,pread64,readv,write,pwrite64,writev,close')].split('=',1)[1].split(',')
    raw=set(options[-1].split('=',1)[1].split(','))
    need(set(selected)&READ_WRITE_SYSCALLS<=raw and '--kill-on-exit' in options
      and not any(x in ('-p','--attach','-v','--verbose') or x.startswith(('read=','write=','inject=')) for x in options),
      'NO_BUFFER_DUMP_ATTACH_ENVIRONMENT_OR_SYSCALL_INJECTION')


def tree_membership(trees):
    for root,pins in trees.items():need(tree_paths(root)==[p['path'] for p in pins],'PROTECTED_HISTORY_MEMBERSHIP_DRIFT')


def actual_local_data(originals,cfg):
    core=originals.document(cfg['localCore']);worker=originals.document(cfg['worker'])
    fp=descriptor(EXEC/'qualification-config.json',originals.live);owned(fp['path']);final=originals.document(fp)
    ap=descriptor(EXEC/'configuration-approval.json',originals.live);owned(ap['path']);approval=originals.document(ap)
    need({k:v for k,v in final.items() if k!='configurationAcceptance'}==core
      and final.get('configurationAcceptance')==ap and final.get('workerConfig')==cfg['worker'],
      'ONLY_GENUINE_CONFIGURATION_ACCEPTANCE_ADDED_TO_WHOLE_CORE')
    need(final['runId']==worker['runId']==RUN_ID and final['runRole']==worker['runRole']=='primary'
      and final['executionSession']==worker['executionSession']=='/root'
      and final['primaryAcceptance'] is None and worker['outputRoot']==str(NATIVE_OUTPUT)
      and worker['environment']==ENV,'EXACT_FRESH_REAL_REQUEST_PROFILE')
    need(approval['schema']=='n02316-local-configuration-approval-v1' and approval['decision']=='ACCEPT_CONFIGURATION_ONLY'
      and approval['configuration']==core and approval['authors']==AUTHORS,
      'GENUINE_WHOLE_CORE_CONFIGURATION_APPROVAL')
    need(len(approval['reviews'])==2 and {r['role'] for r in approval['reviews']}=={'qa','security'}
      and len({r['session'] for r in approval['reviews']})==2,'INDEPENDENT_CORE_REVIEW_ROLES')
    for r in approval['reviews']:
        closed(r,('role','session','decision','subject'))
        need(r['decision']=='ACCEPT_CONFIGURATION_ONLY' and r['subject']==cfg['localCore']
          and r['session'] not in AUTHORS,'ACTUAL_NONAUTHOR_WHOLE_CORE_REVIEW')
    for key in ('sourceApproval','controlAcceptance'):
        need(final[key]==cfg[key] and worker[key]==cfg[key],'CURRENT_SOURCE_AND_CONTROL_JOINS')
    source=originals.document(cfg['sourceClosure'])
    need(len(source)==449 and len({x['path'] for x in source})==449 and worker['sourceClosure']==source,'EXACT_CURRENT449_SOURCE')
    for d in source:originals.remember(d)
    for d in (worker['request'],*final['expectedReplies'].values()):originals.remember(d)
    request=Path(worker['request']['path']).read_bytes()
    need(len(request)==6276 and request.endswith(b'\n') and request.count(b'\n')==1
      and hashlib.sha256(request).hexdigest()=='dc586e609758fb6656c76ab5698985b9620d91e1852c8abfb85b2aaf9da636b0',
      'ORIGINAL_REQUEST_BYTES_UNCHANGED')
    return fp,final,ap


def admission(args,started,active_deadline):
    def live():need(time.monotonic()<active_deadline,'OBSERVER_ORIGINAL_ACTIVE_DEADLINE')
    for x in (args.observer_sha,args.configuration_sha,args.local_release_sha,args.observation_release_sha):
        need(re.fullmatch('[0-9a-f]{64}',x),'EXTERNALLY_TRUSTED_ACTUAL_SHA_REQUIRED')
    originals=Originals(live);own=descriptor(Path(__file__),live)
    need(Path(__file__).resolve()==HERE/'observer.py' and own['sha256']==args.observer_sha,'EXTERNAL_OBSERVER_SOURCE_PIN')
    originals.remember(own);cp=descriptor(CONFIG,live);need(cp['sha256']==args.configuration_sha,'EXTERNAL_CONFIGURATION_CORE_PIN')
    cfg=originals.document(cp)
    closed(cfg,('schema','scope','runId','runRole','executionSession','authors','observer','localCore','worker',
      'sourceClosure','sourceApproval','controlAcceptance','pairAcceptance','baselineHostInventory','protectedTrees',
      'tools','expectedHostContext','environment','traceOptions','caps','timers','output'))
    need(cfg['schema']=='e06-real-request-observer-configuration-core-v1' and cfg['scope']==SCOPE
      and cfg['runId']==RUN_ID and cfg['runRole']=='primary' and cfg['executionSession']=='/root'
      and cfg['authors']==AUTHORS and cfg['observer']==own,'FIXED_REAL_REQUEST_OBSERVER_SCOPE')
    need(cfg['environment']==ENV and cfg['caps']==CAPS and cfg['output']==str(OUTPUT)
      and cfg['timers']=={'outer':1800,'active':1770,'cleanup':30,'nativeCombinedWriteReply':15,'nativeJob':240,'LOCAL':1500},
      'UNCHANGED_NATIVE_AND_OUTER_BOUNDS')
    trace_policy(cfg['traceOptions']);require_host(cfg['expectedHostContext'],host_context())
    for key,path in [('python','/home/peterhorvath/.miniforge3/bin/python3.13'),('strace','/usr/bin/strace')]:
        need(cfg['tools'][key]['path']==path,'FIXED_CACHED_TOOL_PATH');originals.remember(cfg['tools'][key])
    owned(cfg['localCore']['path']);owned(cfg['worker']['path'])
    baseline=originals.document(cfg['baselineHostInventory'])
    need(baseline['sourceMemberCount']==449 and baseline['originalR2FileCount']==20 and len(baseline['files'])==471,
      'EXACT_PRIOR_HOST_BASELINE')
    for row in baseline['files']:
        need(file_state(row['descriptor']['path'],live)==row,'PRIOR_HOST_BYTES_OR_STAT_DRIFT:'+row['descriptor']['path'])
        originals.remember(row['descriptor'])
    for pins in cfg['protectedTrees'].values():
        for d in pins:originals.remember(d)
    tree_membership(cfg['protectedTrees'])
    for key in ('sourceApproval','controlAcceptance','pairAcceptance'):originals.remember(cfg[key])
    fp,final,ap=actual_local_data(originals,cfg)
    monitor=descriptor(EXEC/'monitor.py',live);owned(monitor['path']);originals.remember(monitor)
    lp=Path(args.local_release);need(lp==EXEC/'exact-root-local-release.json','FIXED_FRESH_LOCAL_RELEASE_PATH');owned(lp)
    local_pin=descriptor(lp,live);need(local_pin['sha256']==args.local_release_sha,'EXTERNAL_FRESH_LOCAL_RELEASE_PIN')
    local=originals.document(local_pin)
    need(local=={'schema':'n02316-local-qualification-release-v1','decision':'RELEASE_EXACT_LOCAL_F_ONLY_RUN_ONLY',
      'rootSession':'/root','executionSession':'/root','runRole':'primary','config':fp,'workerConfig':cfg['worker'],
      'sourceApproval':cfg['sourceApproval'],'controlAcceptance':cfg['controlAcceptance'],'configurationAcceptance':ap},
      'GENUINE_CLOSED_LOCAL_RELEASE_NO_TRACE_FIELD_OR_BYPASS')
    op=Path(args.observation_release);need(op==HERE/'exact-root-observation-release.json','FIXED_FRESH_OBSERVATION_RELEASE_PATH');owned(op)
    gp=descriptor(op,live);need(gp['sha256']==args.observation_release_sha,'EXTERNAL_OBSERVATION_RELEASE_PIN')
    grant=originals.document(gp)
    closed(grant,('schema','decision','scope','runId','rootSession','executionSession','observer','configurationCore',
      'sourceSubject','localMonitor','localConfiguration','localRelease','qaReview','securityReview',
      'actualControlAcceptance','actualContainmentAcceptance','issuedAtUtcNs','notAfterUtcNs'))
    need(grant['schema']=='e06-real-request-observer-release-v1' and grant['decision']=='RELEASE_EXACT_REAL_REQUEST_OBSERVATION_ONLY'
      and grant['scope']==SCOPE and grant['runId']==RUN_ID and grant['rootSession']==grant['executionSession']=='/root'
      and grant['observer']==own and grant['configurationCore']==cp and grant['localMonitor']==monitor
      and grant['localConfiguration']==fp and grant['localRelease']==local_pin,'EXACT_OBSERVATION_ROOT_AUTHORITY')
    need(grant['sourceSubject']['path']==str(HERE/'subject.json'),'FIXED_COMPLETE_SOURCE_SUBJECT')
    subject=originals.document(grant['sourceSubject'])
    need(subject['authors']==AUTHORS and subject['observer']==own and subject['configurationCore']==cp
      and subject['localMonitor']==monitor and subject['localConfiguration']==fp
      and subject['wholeLocalCore']==cfg['localCore'] and subject['worker']==cfg['worker'],'COMPLETE_ACTUAL_SOURCE_CONFIGURATION_REVIEW_SUBJECT')
    for d in subject['files']:originals.remember(d)
    sessions=[]
    for role,key in [('qa','qaReview'),('security','securityReview')]:
        review=originals.document(grant[key]);closed(review,('role','session','decision','subject'))
        need(review['role']==role and review['decision']=='ACCEPT_DIAGNOSTIC_SOURCE_CONFIG_ONLY'
          and review['subject']==grant['sourceSubject'] and review['session'] not in AUTHORS,'ACTUAL_INDEPENDENT_OBSERVER_SOURCE_REVIEW')
        sessions.append(review['session'])
    need(len(set(sessions))==2,'DISTINCT_SOURCE_REVIEW_SESSIONS')
    controls=originals.document(grant['actualControlAcceptance'])
    need(controls['schema']=='e06-request-observer-control-acceptance-v1'
      and controls['decision']=='ACCEPT_OBSERVER_PURE_CONTROLS_ONLY'
      and controls['sourceSubject']==grant['sourceSubject'] and controls['actualControls']==13
      and controls['actualSnapshotRegressions']==3
      and type(controls['operator']) is str and type(controls['authors']) is list
      and len(controls['reviews'])==2 and {r['role'] for r in controls['reviews']}=={'qa','security'}
      and len({r['session'] for r in controls['reviews']})==2,'ACTUAL_THIRTEEN_OBSERVER_CONTROL_ACCEPTANCE')
    require_whole_pure_receipts(originals,controls,grant['sourceSubject'],subject)
    for row in controls['reviews']:
        closed(row,('role','session','decision','subject'))
        need(row['decision']=='ACCEPT_OBSERVER_PURE_CONTROLS_ONLY' and row['subject']==controls['controlSubject']
          and row['session'] not in AUTHORS and row['session'] not in controls['authors']
          and row['session']!=controls['operator'],'NONAUTHOR_NONOPERATOR_CONTROL_REVIEW')
    require_containment_acceptance(originals,cfg,grant['sourceSubject'],grant['actualContainmentAcceptance'])
    now=time.time_ns();issued=grant['issuedAtUtcNs'];expiry=grant['notAfterUtcNs']
    need(type(issued) is int and type(expiry) is int and 0<=issued<=now and now+1_800_000_000_000<=expiry
      and 0<expiry-issued<=1_860_000_000_000,'FRESH_FINITE_OBSERVATION_AUTHORITY_NO_RENEWAL')
    need(not os.path.lexists(OUTPUT) and not os.path.lexists(EXEC/'outer-actual') and not os.path.lexists(NATIVE_OUTPUT),
      'ALL_THREE_OUTPUT_NAMESPACES_FRESH')
    originals.recheck();live()
    return originals,cp,cfg,fp,monitor,local_pin,gp



def require_whole_pure_receipts(originals,controls,whole_pin,whole):
    """Current entire observer/helper closure, never just unchanged capture AST."""
    result=originals.document(controls['controlSubject'])
    need(result['schema']=='e06-actual-sixteen-controls-subject-v1' and result['sourceSubject']==whole_pin
      and result['actualScopes']=={'pure':13,'snapshotData':3} and result['realStrace']==result['nodeLocal']==0,
      'ACTUAL_CURRENT_WHOLE_SOURCE_SIXTEEN_SCOPE')
    actual=originals.document(result['results'])
    need(actual['sourceSubject']==whole_pin and actual['retries']==0,'CURRENT_WHOLE_SOURCE_NO_RETRY_RECEIPT')
    expected={d['path']:d for d in whole['files']};need(len(expected)==len(whole['files']),'WHOLE_SOURCE_NO_PATH_COLLAPSE')
    expected[whole_pin['path']]=whole_pin
    for name,count,test in [('pure13',13,'test_observer.py'),('snapshot3',3,'test_snapshot_paths.py')]:
        scope=actual[name]
        need(scope['actual']==scope['passed']==count and scope['failed']==scope['errors']==scope['skipped']==0,
          'ALL_CURRENT_MANDATORY_PURE_CONTROLS_COMPLETE')
        raw=originals.document(scope['capture'])
        need(raw['frozenBefore']==raw['frozenAfter']==expected and raw['exit']==0 and raw['reaped'] is True
          and raw['forced'] is False and raw['firstError'] is None and raw['source']==descriptor(HERE/test),
          'WHOLE_CURRENT_SOURCE_TESTED_BEFORE_AFTER_NATURAL_CAPTURE')
        if name=='pure13':
            need(raw['captureSource']==descriptor(HERE/'capture-controls.py')
              and raw['stdoutEOF'] is True and raw['stderrEOF'] is True,'EXACT_CURRENT_HELPER_AND_EOF')
        else:need(raw['EOF']=={'stdout':True,'stderr':True},'SNAPSHOT_RAW_EOF')
        for d in raw['raw'].values():originals.remember(d)
    for d in result['files']:originals.remember(d)


def validate_guard_regression_acceptance(originals,pin,fixture_source,whole_source):
    a=originals.document(pin)
    need(a['schema']=='e06-strace-guard-pure-acceptance-v1'
      and a['decision']=='ACCEPT_GUARD11_ADMISSION14_MODELED_CONTROLS_ONLY'
      and a['sourceSubject']==fixture_source and a['observerWholeSourceSubject']==whole_source
      and a['actualControls']==11 and a['actualAdmissionControls']==14,'ACTUAL_ELEVEN_GUARD_MODELS_EXACT_WHOLE_SOURCE')
    result=originals.document(a['controlSubject'])
    need(result['schema']=='e06-modeled-guard-controls-actual-subject-v1'
      and result['sourceSubject']==fixture_source and result['observerWholeSourceSubject']==whole_source
      and result['actualControls']==result['passed']==11 and result['failed']==result['errors']==result['skipped']==0
      and result['actualAdmissionControls']==result['admissionPassed']==14
      and result['admissionFailed']==result['admissionErrors']==result['admissionSkipped']==0,
      'NO_MISSING_GUARD_MODELS_OR_SUBSTITUTED_SOURCE')
    for d in result['files']:originals.remember(d)
    need(len(a['reviews'])==2 and {r['role'] for r in a['reviews']}=={'qa','security'}
      and len({r['session'] for r in a['reviews']})==2,'TWO_ACTUAL_GUARD_MODEL_REVIEWS')
    for r in a['reviews']:
        closed(r,('role','session','decision','subject'))
        need(r['decision']=='ACCEPT_GUARD11_ADMISSION14_MODELED_CONTROLS_ONLY' and r['subject']==a['controlSubject']
          and r['session'] not in AUTHORS and r['session'] not in a['authors'] and r['session']!=a['operator'],
          'INDEPENDENT_GUARD_MODEL_RESULTS_REVIEW')


def require_containment_acceptance(originals,cfg,source_subject,acceptance_pin):
    """No Node launch without actual, independently accepted pinned-strace controls."""
    acceptance=originals.document(acceptance_pin)
    closed(acceptance,('schema','decision','sourceSubject','containmentSourceSubject','controlSubject',
      'tools','hostContext','fixtureCases','captureFunctionAstSha256','results','operator','authors','reviews',
      'testedWholeSourceSubject','guardRegressionAcceptance'))
    need(acceptance['schema']=='e06-strace-containment-acceptance-v1'
      and acceptance['decision']=='ACCEPT_ACTUAL_PINNED_STRACE_CONTAINMENT_ONLY'
      and acceptance['sourceSubject']==source_subject and acceptance['testedWholeSourceSubject']==source_subject
      and acceptance['tools']==cfg['tools']
      and acceptance['hostContext']==cfg['expectedHostContext'],'ACTUAL_TOOL_HOST_SOURCE_CONTAINMENT_JOIN')
    need(acceptance['containmentSourceSubject']['path']==str(HERE.parent/'e06-strace-containment-controls-r2/subject.json'),
      'FIXED_CONTAINMENT_SOURCE_SUBJECT')
    fixtures=originals.document(acceptance['containmentSourceSubject'])
    need(fixtures['observer']==descriptor(HERE/'observer.py')
      and fixtures['observerConfiguration']==descriptor(CONFIG)
      and fixtures['observerHelper']==descriptor(HERE/'capture-controls.py')
      and fixtures['tools']==cfg['tools']
      and fixtures['hostContext']==cfg['expectedHostContext'],'EXACT_REVIEWED_FIXTURE_SOURCE_CONFIG_TOOLS_HOST')
    for d in fixtures['files']:originals.remember(d)
    cases=['natural-zero','natural-refusal','deadline','interrupt','capture-fault','tracer-death','inner-parent-death']
    need(acceptance['fixtureCases']==cases and fixtures['fixtureCases']==cases
      and acceptance['captureFunctionAstSha256']==fixtures['captureFunctionAstSha256'],
      'EXACT_SAME_CAPTURE_AND_SEVEN_REAL_STRACE_CASES')
    validate_guard_regression_acceptance(originals,acceptance['guardRegressionAcceptance'],
      acceptance['containmentSourceSubject'],source_subject)
    result=originals.document(acceptance['controlSubject'])
    need(result['schema']=='e06-actual-strace-containment-subject-v1'
      and result['sourceSubject']==acceptance['containmentSourceSubject']
      and result['observerSourceSubject']==source_subject and result['tools']==cfg['tools']
      and result['hostContext']==cfg['expectedHostContext']
      and result['cases']==acceptance['results'] and len(result['cases'])==7,'ACTUAL_CONTAINMENT_RESULT_SCOPE')
    need(type(result['files']) is list and len(result['files'])>=7,'ACTUAL_SEVEN_RAW_RECEIPTS_REQUIRED')
    for d in result['files']:originals.remember(d)
    need([r['case'] for r in result['cases']]==cases,'EXACT_REAL_CASE_ORDER_NO_POOLING')
    for r in result['cases']:
        need(r['disposition']=='QUALIFIED_FIXTURE_CONTAINMENT_ONLY' and r['realStrace'] is True
          and r['sameObserverCapture'] is True and r['readyBarrierComplete'] is True
          and r['safetyFallbackUsed'] is False and r['allKnownPidsExitedBeforeFallback'] is True
          and r['allOwnedChildrenReaped'] is True and r['noPostReapSignal'] is True
          and r['rawCapsRespected'] is True and r['privacyQualified'] is True,
          'ALL_SEVEN_ACTUAL_CONTAINMENT_CASES_QUALIFIED')
        expected_path=HERE.parent/'e06-strace-containment-controls-r2/actual-containment-r1'/r['case']/'guard-result.json'
        need(r['record']['path']==str(expected_path) and r['record'] in result['files'],'EXACT_ACTUAL_CASE_RECORD_MEMBER')
        actual=originals.document(r['record'])
        for k in ('case','disposition','realStrace','sameObserverCapture','readyBarrierComplete','safetyFallbackUsed',
          'allKnownPidsExitedBeforeFallback','allOwnedChildrenReaped','noPostReapSignal','rawCapsRespected','privacyQualified'):
            need(actual[k]==r[k],'ACTUAL_CASE_RECORD_SUMMARY_AGREES')
        need(actual['firstError'] is None and actual['completeOwnedDescendantCensusEmpty'] is True
          and actual['faultSelfExpirySeconds']>actual['guardTotalCeilingSeconds']
          and 0<actual['captureReceiptAtElapsedNs']<=7_000_000_000
          and 0<actual['absenceAtElapsedNs']<=7_250_000_000,'TIMELY_ACTUAL_ABSENCE_WITH_NO_SELF_EXPIRY')
        need(actual['observerCapture']['path']==str(expected_path.with_name('observer-capture.json')),
          'EXACT_SAME_OBSERVER_CAPTURE_RECEIPT')
        cap=originals.document(actual['observerCapture'])
        need(cap['reaped'] is True and all(cap['eof'].values()),'ACTUAL_OBSERVER_REAP_AND_ALL_EOF')
        for name,bound in [('trace',1048576),('stdout',65536),('stderr',262144)]:
            raw=actual['rawDescriptors'][name];need(raw['path']==str(expected_path.with_name(name+'.bin'))
              and 0<=raw['bytes']<=bound and cap['raw'][name]==raw
              and cap['retainedBytes'][name]==raw['bytes'],'ACTUAL_RAW_CAPTURE_PINS_AND_CAPS')
            originals.remember(raw)

    need(type(acceptance['operator']) is str and type(acceptance['authors']) is list
      and len(acceptance['reviews'])==2 and {r['role'] for r in acceptance['reviews']}=={'qa','security'}
      and len({r['session'] for r in acceptance['reviews']})==2,'TWO_ACTUAL_CONTAINMENT_REVIEW_SESSIONS')
    for r in acceptance['reviews']:
        closed(r,('role','session','decision','subject'))
        need(r['decision']=='ACCEPT_ACTUAL_PINNED_STRACE_CONTAINMENT_ONLY'
          and r['subject']==acceptance['controlSubject'] and r['session'] not in AUTHORS
          and r['session'] not in acceptance['authors'] and r['session']!=acceptance['operator'],
          'INDEPENDENT_NONAUTHOR_NONOPERATOR_CONTAINMENT_REVIEW')


def capture(argv,trace_r,trace_w,out,started,active_deadline,total_deadline):
    deadline=active_deadline
    record={'argv':argv,'stdin':'DEVNULL_ZERO_BYTES','phaseCeilingSeconds':ACTIVE_SECONDS,
      'phaseIncludesObserverAdmissionAndTracerStartup':True,'cleanupCeilingSeconds':CLEANUP_SECONDS,'launchAttempted':False,
      'pid':None,'pidMeaning':'Owned tracer PID in tool execution namespace','exit':None,'reaped':False,
      'forced':False,'timedOut':False,'signals':[],'firstError':None,'secondaryErrors':[],
      'observedBytes':dict.fromkeys(CAPS,0),'retainedBytes':dict.fromkeys(CAPS,0),
      'acknowledgedWriteBytes':dict.fromkeys(CAPS,0),'writeState':dict.fromkeys(CAPS,'WRITABLE'),
      'eof':dict.fromkeys(CAPS,False)}
    process=None;selector=None;streams={};interrupted=[];handlers={};reaped=False
    def fault(error):
        item={'type':type(error).__name__,'message':str(error)[:4096]}
        if record['firstError'] is None:record['firstError']=item
        elif len(record['secondaryErrors'])<16:record['secondaryErrors'].append(item)
    def observe():
        need(process is not None and not reaped and process.returncode is None,'OWNED_UNREAPED_TRACER_REQUIRED')
        return os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
    def pump(delay):
        try:events=selector.select(delay)
        except BaseException as error:fault(error);return
        for key,_ in events:
            name=key.data
            try:block=os.read(key.fd,65536)
            except BlockingIOError:continue
            except BaseException as error:fault(error);continue
            if not block:
                record['eof'][name]=True;selector.unregister(key.fileobj);continue
            record['observedBytes'][name]+=len(block)
            keep=block[:max(0,CAPS[name]-record['retainedBytes'][name])]
            if keep and record['writeState'][name]=='WRITABLE':
                try:
                    n=streams[name].write(keep)
                    # Account every acknowledged positive prefix BEFORE asserting
                    # completeness. Failed/uncertain streams never write again,
                    # including while cleanup continues independent draining.
                    if type(n) is int and 0<=n<=len(keep):
                        record['acknowledgedWriteBytes'][name]+=n
                        record['retainedBytes'][name]+=n
                    need(type(n) is int and n==len(keep),'COMPLETE_CAPTURE_WRITE')
                except BaseException as error:
                    record['writeState'][name]='POISONED_FAILED_OR_UNCERTAIN';fault(error)
            if len(keep)!=len(block):fault(Refusal('DIAGNOSTIC_'+name.upper()+'_CAP'))
    try:
        for name in CAPS:
            fd=os.open(out/(name+'.bin'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            # Unbuffered capture has no latent buffered write to flush after a
            # stream is poisoned. Every write attempt is bounded in pump().
            streams[name]=os.fdopen(fd,'wb',buffering=0)
        for signum in (signal.SIGINT,signal.SIGTERM):
            handlers[signum]=signal.getsignal(signum);signal.signal(signum,lambda n,f:interrupted.append(n) if not interrupted else None)
        record['launchAttempted']=True
        process=subprocess.Popen(argv,cwd=ROOT,env=ENV,
          stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,
          pass_fds=(trace_w,),bufsize=0)
        record['pid']=process.pid;os.close(trace_w);trace_w=None
        selector=selectors.DefaultSelector()
        for name,pipe in [('trace',trace_r),('stdout',process.stdout),('stderr',process.stderr)]:
            fd=pipe if type(pipe) is int else pipe.fileno();os.set_blocking(fd,False);selector.register(pipe,selectors.EVENT_READ,name)
        while True:
            need(not interrupted,'OBSERVER_INTERRUPTED')
            if time.monotonic()>=deadline:record['timedOut']=True;raise TimeoutError('OBSERVER_ACTIVE_DEADLINE')
            if observe() is not None and all(record['eof'].values()):break
            pump(min(.05,max(0,deadline-time.monotonic())))
            if record['firstError'] is not None:break
    except BaseException as error:fault(error)
    finally:
        if trace_w is not None:os.close(trace_w)
        if process is not None:
            try:
                exited=observe();complete=exited is not None and all(record['eof'].values())
                cleanup_deadline=min(time.monotonic()+CLEANUP_SECONDS,total_deadline)
                for signum,seconds in [(signal.SIGINT,20),(signal.SIGTERM,5),(signal.SIGKILL,5)]:
                    if complete:break
                    observe()
                    try:os.killpg(process.pid,signum);record['signals'].append(int(signum));record['forced']=True
                    except ProcessLookupError:pass
                    until=min(cleanup_deadline,time.monotonic()+seconds)
                    while time.monotonic()<until:
                        if selector is not None:pump(min(.05,max(0,until-time.monotonic())))
                        exited=observe();complete=exited is not None and all(record['eof'].values())
                        if complete:break
                if exited is not None:record['exit']=process.wait(timeout=0);reaped=True;record['reaped']=True
                else:fault(Refusal('OWNED_TRACER_NOT_REAPED_IN_BOUND'))
            except BaseException as error:fault(error)
        if selector is not None:selector.close()
        for pipe in (() if process is None else (process.stdout,process.stderr)):
            try:pipe.close()
            except BaseException as error:fault(error)
        try:os.close(trace_r)
        except OSError as error:fault(error)
        for name,handle in streams.items():
            try:handle.flush();os.fsync(handle.fileno())
            except BaseException as error:
                record['writeState'][name]='POISONED_FAILED_OR_UNCERTAIN';fault(error)
            finally:
                try:handle.close()
                except BaseException as error:
                    record['writeState'][name]='POISONED_FAILED_OR_UNCERTAIN';fault(error)
        for signum,handler in handlers.items():signal.signal(signum,handler)
    record['elapsedMilliseconds']=int((time.monotonic()-started)*1000)
    record['receivedSignals']=interrupted
    record['raw']={name:descriptor(out/(name+'.bin')) for name in CAPS if (out/(name+'.bin')).is_file()}
    # A write may persist a prefix and raise before acknowledging its length.
    # Final retained counts therefore come from the actual closed raw files.
    # Poisoning bounds uncertain writes to the one already bounded keep prefix.
    for name,pin in record['raw'].items():
        actual=pin['bytes'];record['retainedBytes'][name]=actual
        if actual>CAPS[name]:fault(Refusal('FINAL_CAPTURE_'+name.upper()+'_CAP'))
        if actual>record['observedBytes'][name]:fault(Refusal('FINAL_CAPTURE_EXCEEDS_OBSERVED_'+name.upper()))
        if actual!=record['acknowledgedWriteBytes'][name]:
            fault(Refusal('FINAL_CAPTURE_WRITE_ACCOUNTING_DIFFERENCE_'+name.upper()))
    record['retainedAccounting']='FINAL_RAW_FILE_DESCRIPTOR_BYTES'
    record['captureComplete']=(all(record['eof'].values()) and record['observedBytes']==record['retainedBytes']
      and all(value=='WRITABLE' for value in record['writeState'].values()))
    record['nativeCleanupQualified']=False
    record['nativeCleanupMeaning']='Never established by observer capture; forced/uncertain tracer cleanup remains unqualified.'
    record['traceeContainment']='UNKNOWN_REQUIRES_ACTUAL_NATIVE_AND_TRACE_GRAPH_REVIEW'
    record['killOnExit']='REQUESTED_NOT_HOST_ATTESTED'
    return record

def read_inner_summary(capture_record,originals):
    path=OUTPUT/'stdout.bin';raw=path.read_bytes() if path.is_file() else b''
    if not raw:return {'status':'SUMMARY_ABSENT_STAGE_UNKNOWN','record':None}
    need(raw.endswith(b'\n') and raw.count(b'\n')==1,'ONE_COMPLETE_FIXED_MONITOR_SUMMARY')
    summary=strict(raw[:-1]);need(type(summary) is dict and type(summary.get('execution')) is dict,'FIXED_MONITOR_SUMMARY_OBJECT')
    pin=summary['execution'];need(pin['path']==str(EXEC/'outer-actual/execution.json'),'EXACT_MONITOR_EXECUTION_RECORD_PATH')
    owned(pin['path']);inner=doc(pin)
    need(inner['configuration']['path']==str(EXEC/'qualification-config.json') and inner['release']['path']==str(EXEC/'exact-root-local-release.json')
      and inner['monitor']['path']==str(EXEC/'monitor.py'),'INNER_RECORD_SCOPE_NO_OTHER_RUN')
    need(summary.get('monitorExit')==inner['monitorExit'] and summary.get('childExit')==inner['exit'],'INNER_SUMMARY_AND_RECORD_AGREE')
    return {'status':'ACTUAL_LOCAL_CAPTURE_REQUIRES_INDEPENDENT_GRAPH_REVIEW','record':pin,
      'monitorExit':inner['monitorExit'],'qualificationChildExit':inner['exit'],
      'originalLocalFirstError':inner['firstError'],'originalLocalSecondaryErrors':inner['secondaryErrors'],
      'candidateResult':inner['candidateResult'],'nativeExecutionReported':inner['nativeExecution'],
      'forced':inner['forced'],'reaped':inner['reaped'],'captureComplete':inner['captureComplete'],
      'meaning':'Readback of retained inner monitor facts; not native lifecycle or13-field graph approval.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observer-sha',required=True);parser.add_argument('--configuration-sha',required=True)
    parser.add_argument('--local-release',required=True);parser.add_argument('--local-release-sha',required=True)
    parser.add_argument('--observation-release',required=True);parser.add_argument('--observation-release-sha',required=True)
    args=parser.parse_args();started=time.monotonic();active_deadline=started+ACTIVE_SECONDS;total_deadline=started+TOTAL_SECONDS
    originals,cp,cfg,fp,monitor,local_pin,grant=admission(args,started,active_deadline)
    OUTPUT.mkdir(mode=0o700);trace_r,trace_w=os.pipe2(os.O_CLOEXEC)
    argv=[cfg['tools']['strace']['path'],*TRACE_OPTIONS,'-o','/proc/self/fd/'+str(trace_w),'--',
      cfg['tools']['python']['path'],'-I','-B',monitor['path'],'--monitor-sha',monitor['sha256'],
      '--release',local_pin['path'],'--release-sha',local_pin['sha256']]
    record={'schema':'e06-real-request-observation-capture-v1','scope':SCOPE,'runId':RUN_ID,
      'operator':'/root','configurationCore':cp,'localConfiguration':fp,'localMonitor':monitor,
      'freshLocalRelease':local_pin,'freshObservationRelease':grant,'hostContext':host_context(),
      'originalsBefore':list(originals.rows.values()),'firstError':None,'secondaryErrors':[],
      'source449EditsAuthorized':False,'canonicalMutationPerformedByObserver':False,
      'limits':['Fresh full LOCAL admission remains inside fixed monitor/qualification; observer grants no transport capability.',
        'Syscall lengths/paths support phase inference, not direct JS markers, validation, CPU/RSS or physical I/O attribution.',
        'Raw buffers suppressed; original synthetic request/custody resides only in private native records.',
        'Forced/uncertain observer cleanup is UNQUALIFIED and never proves absence of escaped descendants.',
        'Natural observer/monitor exit and initialized noEffects zeros do not prove complete native/business conformance.',
        'No canonical E06 PASS, architectural blocker closure, SDK or production authority.']}
    record['capture']=capture(argv,trace_r,trace_w,OUTPUT,started,active_deadline,total_deadline)
    record['firstError']=record['capture']['firstError'];record['secondaryErrors']=list(record['capture']['secondaryErrors'])
    def fault(error):
        fact={'type':type(error).__name__,'message':str(error)[:4096]}
        if record['firstError'] is None:record['firstError']=fact
        elif len(record['secondaryErrors'])<16:record['secondaryErrors'].append(fact)
    try:record['innerMonitor']=read_inner_summary(record['capture'],originals)
    except BaseException as error:record['innerMonitor']=None;fault(error)
    try:
        def remaining():need(time.monotonic()<total_deadline,'OBSERVER_ORIGINAL_TOTAL_DEADLINE')
        originals.live=remaining;originals.recheck();tree_membership(cfg['protectedTrees'])
        require_host(cfg['expectedHostContext'],host_context());record['originalsUnchanged']=True
    except BaseException as error:record['originalsUnchanged']=False;fault(error)
    record['originalsAfter']=list(originals.rows.values())
    cap=record['capture'];inner=record.get('innerMonitor') or {}
    natural=(cap['reaped'] and not cap['forced'] and cap['captureComplete'] and cap['firstError'] is None
      and record['firstError'] is None and record['secondaryErrors']==[] and record['originalsUnchanged'])
    candidate=(natural and cap['exit']==0 and inner.get('monitorExit')==0
      and (inner.get('candidateResult') or {}).get('status')=='MATCHED')
    record['disposition']='LOCAL_MATCHED_CANDIDATE_UNREVIEWED' if candidate else 'DIAGNOSTIC_PREFIX_OR_LOCAL_FAILURE_UNQUALIFIED'
    record['observerExit']=0 if candidate else 2;record['independentWholeResultReviewRequired']=True
    record['elapsedMilliseconds']=int((time.monotonic()-started)*1000)
    try:result=write(OUTPUT/'result.json',(json.dumps(record,indent=2)+'\n').encode())
    except BaseException as error:
        fault(error);os.write(2,(json.dumps({'schema':'e06-observer-record-write-failure-v1',
          'firstError':record['firstError'],'secondaryErrors':record['secondaryErrors'],
          'tracerExit':cap['exit'],'reaped':cap['reaped'],'forced':cap['forced'],
          'nativeCleanupQualified':False})+'\n')[:16384].encode());return 2
    print(json.dumps({'result':result,'observerExit':record['observerExit'],'disposition':record['disposition'],
      'independentReviewRequired':True}))
    return record['observerExit']

if __name__=='__main__':
    try:raise SystemExit(main())
    except BaseException as error:
        if isinstance(error,SystemExit):raise
        os.write(2,('OBSERVER_PREFLIGHT_OR_CAPTURE_FAILURE: '+type(error).__name__+': '+str(error))[:16384].encode('utf-8','backslashreplace')+b'\n')
        raise SystemExit(2)
