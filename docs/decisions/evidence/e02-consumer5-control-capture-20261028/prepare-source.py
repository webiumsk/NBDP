"""SOURCE metadata/copy assembly only. Never imports target/capture/test modules."""
import ast
import hashlib
import json
from pathlib import Path

REPO=Path('/home/peterhorvath/apps/bitcoin/NBDP')
OUT=Path(__file__).resolve().parent
HERE=Path('/Data/nbdp-e02-tooling-20261027/consumer5-control-capture-preparation-r1')
CONSUMER=REPO/'docs/decisions/evidence/e02-ordinary-minimum-consumer-preparation-r5/source2'
CORE=Path('/Data/nbdp-e02-tooling-20261027/wrapper46-model-method-preparation-r3/capture46.py')
ACTOR='/root/r5_plan_fix'

def pin(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def load(path):return json.loads(Path(path).read_bytes())

def save(path,value):
    raw=value if type(value) is bytes else (json.dumps(value,indent=2)+'\n').encode()
    with Path(path).open('xb') as f:f.write(raw)
    return pin(path)

def main():
    if (HERE/'capture.py').exists() or (OUT/'method-source.json').exists():raise ValueError('FRESH_SOURCE_ONLY_NO_OVERWRITE')
    if pin(CORE)['sha256']!='9465dbfee3ce335df7d011b778eed960032cc1e8a37f9fd60e925f1d10c4b5d8':raise ValueError('EXACT_REUSED_CORE_SOURCE_REQUIRED')
    if pin(CONSUMER/'subject.json')['sha256']!='bb99b3b11db70a19cd5b6266dbdea381d84bb7f1ccc9ed58a463f01120e20178':raise ValueError('EXACT_CONSUMER_SOURCE2_REQUIRED')
    subject=load(CONSUMER/'subject.json');sourceplan=load(CONSUMER/'control-plan.json')
    core_text=CORE.read_text();core_ast=ast.parse(core_text)
    names=['need','safe','pin','descriptor','checked','load','put','signal_owned_group','finish_owned','capture_scope']
    functions={n.name:ast.get_source_segment(core_text,n) for n in core_ast.body if isinstance(n,ast.FunctionDef)}
    header='''"""Finite once-only consumer5 pure DATA capture; SOURCE review only until root release.
Core child PIPE/session/absolute-reap functions are copied exactly from9465dbfe.
No model/runtime occurs on import. No SDK/Android/native/network/client claim.
"""
import hashlib,json,os,pathlib,re,selectors,signal,stat,subprocess,sys,time
HERE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/consumer5-control-capture-preparation-r1')
OUTPUT=HERE/'actual'
GRANT=HERE/'coordinator-acknowledgement.json'
ROOT=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP')
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
ACTOR='/root/r5_plan_fix'
'''
    extra=(OUT/'capture-adapter.txt').read_text()
    code=header+'\n\n'+'\n\n'.join(functions[n] for n in names)+'\n\n'+extra
    ast.parse(code)
    save(HERE/'capture.py',code.encode());save(OUT/'capture.py',code.encode())
    method_inputs=[]
    def add(d):
        if pin(d['path'])!=d:raise ValueError('CURRENT_INPUT_DRIFT:'+d['path'])
        method_inputs.append(d)
    for d in subject['sources']:add(d)
    producer=load(subject['producerSubject']['path'])
    for d in producer['sources']+producer['configurations']:add(d)
    for name in ('subject.json','source-packet.json','control-plan.json','source-input-manifest.json','source-qa.json','source-security.json','source-acceptance.json'):add(pin(CONSUMER/name))
    for d in (subject['producerSubject'],producer['controlPlan'],subject['currentCaptureGraphs']['capture-b']['plan']):add(d)
    for p in (Path(sourceplan['interpreter']['path']),Path('/usr/bin/env'),Path('/usr/bin/timeout')):add(pin(p))
    # Tests read source/config DTOs and the two literal plan files. Their own
    # synthetic tempfile DATA is not pre-existing evidence. No SDK tree is read.
    indexed={d['path']:d for d in method_inputs}
    inputs=save(HERE/'input-manifest.json',dict(schema='e02-consumer5-capture-known-inputs-v1',scope='EXACT_KNOWN_SOURCE_TEST_READ_OPERANDS_NO_RECURSIVE_SDK_OR_CLIENT_CLOSURE',
        files=[indexed[k] for k in sorted(indexed)],actualInputCount=len(indexed),sourceFiles=subject['sources'],
        producerSources=producer['sources'],configurations=producer['configurations'],consumerSource=pin(CONSUMER/'subject.json'),
        testReadOperands=['All14consumer modules/docs','Producer subject and31sources including16worker fixture inputs','Both frozen role configs',
            'Producer SOURCE2 control-plan for exact API helper','SOURCE4 capture-b plan for synthetic API helper','Pinned interpreter/env/timeout'],
        syntheticWrites='Owned tempfile graphs created only during separately authorized139; no fixture root runtime is started.',
        sdkTreeIncluded=False,fullRuntimeClientClosureClaimed=False))
    scopes=[]
    for s in sourceplan['scopes']:
        scopes.append(dict(scope=s['name'],argv=s['argv'],cwd=s['cwd'],count=s['count'],
            expectedNames=sorted(s['exactDefinedNames']),source=s['source'],format='VERBOSE_UNITTEST_NAMED'))
    plan=save(HERE/'plan.json',dict(schema='e02-consumer5-fixed-control-capture-plan-v1',consumerSource=pin(CONSUMER/'subject.json'),
        consumerPacket=pin(CONSUMER/'source-packet.json'),consumerControlPlan=pin(CONSUMER/'control-plan.json'),
        inputManifest=inputs,scopes=scopes,scopeCounts=[86,36,8,9],environment={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'},
        limits=dict(childSeconds=60,absoluteChildReapSeconds=3,stdoutBytes=1048576,stderrBytes=262144,outerSeconds=297),
        rootAcknowledgementPath=str(HERE/'coordinator-acknowledgement.json'),outputRoot=str(HERE/'actual'),
        outerRequestTemplate=sourceplan['outerRequestTemplate'],outerArgvTemplate=sourceplan['outerArgvTemplate'],
        stopFirstFailure=True,noRetry=True,actualExecutions=0,sourceReviews=None,captureReviews=None,rootGrant=None))
    save(HERE/'outer-request-template.json',sourceplan['outerRequestTemplate'])
    for name in ('input-manifest.json','plan.json','outer-request-template.json'):save(OUT/name,(HERE/name).read_bytes())
    new_ast=ast.parse(code)
    new={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,ast.FunctionDef)}
    old={n.name:ast.dump(n,include_attributes=False) for n in core_ast.body if isinstance(n,ast.FunctionDef)}
    if any(new[n]!=old[n] for n in names):raise ValueError('UNCHANGED_CORE_AST_REQUIRED')
    reuse=save(OUT/'core-reuse.json',dict(schema='e02-consumer5-capture-limited-core-reuse-v1',source=pin(CORE),
        exactUnchangedFunctionASTs=names,lifecycleEvidence=pin(REPO/'docs/decisions/evidence/e02-wrapper-capture-admission9-actual-20261028/acceptance.json'),
        meaning='Limited accepted core/custody evidence only; not consumer whole-method DATA or139 execution. New admission/closure/parser still need independent SOURCE review.',
        methodsExecutedByPreparer=0))
    method=save(HERE/'method-source.json',dict(schema='e02-consumer5-capture-method-source-v1',author=ACTOR,coordinator='/root',
        sourceAuthors=[ACTOR,'/root/completion_wrapper','/root','/root/r5'],
        state='WRITES_STOPPED_PENDING_INDEPENDENT_CAPTURE_SOURCE_QA_SECURITY',consumerSource=pin(CONSUMER/'subject.json'),
        consumerPacket=pin(CONSUMER/'source-packet.json'),plan=plan,inputManifest=inputs,
        sources=[pin(HERE/'capture.py'),pin(HERE/'outer-request-template.json')],coreReuse=reuse,
        scopeCounts=[86,36,8,9],actualExecutions=0,sourceReviews=None,rootGrant=None,runtimeAuthorized=False))
    save(OUT/'method-source.json',(HERE/'method-source.json').read_bytes())
    packet=save(OUT/'source-packet.json',dict(schema='e02-consumer5-capture-source-packet-v1',subject=method,plan=plan,inputManifest=inputs,
        sources=[pin(HERE/name) for name in ('capture.py','plan.json','input-manifest.json','outer-request-template.json','method-source.json')],
        durableCopies=[dict(original=pin(HERE/name),copy=pin(OUT/name)) for name in ('capture.py','plan.json','input-manifest.json','outer-request-template.json','method-source.json')],
        coreReuse=reuse,preparationScript=pin(__file__),adapter=pin(OUT/'capture-adapter.txt'),actualExecutions=0,rootGrantCreated=False,
        consumerSourceUnchanged=True,noClaimFullRuntimeSdkClosure=True))
    save(OUT/'entrypoint.json',dict(schema='e02-consumer5-capture-entrypoint-v1',subject=method,packet=packet,plan=plan,inputManifest=inputs,
        state='SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_EXTERNAL_ROOT_RELEASE',actualExecutions=0))
    print(json.dumps(dict(subject=method,packet=packet,inputs=len(indexed),scopeCounts=[86,36,8,9],actualExecutions=0)))

if __name__=='__main__':main()
