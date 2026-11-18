"""Narrow SOURCE-only adaptation; never imports capture or project/test modules."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE=ROOT/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2/current-controls-r1'
PREP=HERE.parent
SOURCE=ROOT/'experiments/prototypes/e02_transport_query_diagnostic_v2'
BASE=ROOT/'docs/decisions/evidence/e02-completion-preparation-r1/current-controls-r1/capture-controls.py'
raw=BASE.read_text()

def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(name,value):
 p=HERE/name;p.write_text(value if type(value) is str else json.dumps(value,indent=2)+'\n');p.chmod(0o600)
def desc(v,out):
 if type(v) is dict:
  if set(v)=={'path','bytes','sha256'}:
   if v['path'] in out and out[v['path']]!=v:raise ValueError('Conflicting pin')
   out[v['path']]=v
  else:
   for x in v.values():desc(x,out)
 elif type(v) is list:
  for x in v:desc(x,out)

subject=json.loads((PREP/'subject.json').read_text());fixture=json.loads((SOURCE/'fixture-plan.json').read_text())
protected=json.loads((PREP/'protected-inputs-after.json').read_text())
rows={};desc(subject,rows);desc(protected,rows)
for p in (PREP/'subject.json',PREP/'artifact-manifest.json',PREP/'control-plan.json',PREP/'proposed-run-config.json',SOURCE/'dependency-tree.json'):
 rows[str(p)]=pin(p)
for d in fixture['dependencyFiles']:rows[d['source']]={'path':d['source'],'bytes':d['bytes'],'sha256':d['sha256']}
for name in ('/home/peterhorvath/.miniforge3/bin/python3.13','/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'):rows[name]=pin(Path(name))
for d in rows.values():
 if pin(Path(d['path']))!=d:raise ValueError('Frozen input changed')
save('frozen-inputs.json',{'schema':'e02-transport-source2-control-frozen-inputs-v1','files':[rows[k] for k in sorted(rows)],'dependencyRegularCount':816,'protectedInputCount':len(protected['files']),'sourceSubject':pin(PREP/'subject.json'),'configuration':pin(PREP/'proposed-run-config.json'),'node':rows['/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'],'python':rows['/home/peterhorvath/.miniforge3/bin/python3.13']})
# Keep the existing clock/pin/strict/doc/save functions and exact owned-child
# observation try/except/finally subtree. Only fixed metadata/scope checks differ.
text=raw[:raw.index('def snapshot(')]
text=text.replace('Fixed once-only54 synthetic DATA capture','Fixed once-only18/27/6 synthetic DATA capture').replace('This finite trusted Python suite creates no child services or descendants.','These finite trusted Python/Node suites create no child services or descendants.')
a=text.index("SOURCE = ROOT /");b=text.index('\n\ndef utc()',a)
text=text[:a]+"SOURCE = ROOT / 'experiments/prototypes/e02_transport_query_diagnostic_v2'\nNODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')\nPYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')\nACTOR = '/root/ordinary_api35_source'\nCAPTURE = HERE\nSOURCE_SHA = 'aece375c76f20d8c738d34e57feb19e50c2ccfc28cb09ffc9347481d2f526b85'\nMANIFEST_SHA = '"+pin(PREP/'artifact-manifest.json')['sha256']+"'\nFROZEN_PLAN_SHA = 'bf227bade861821099eed7f3c664ab8f56259b028000ea5b42024821f3fef1fb'\nLIMITS = {'stdout':1048576,'stderr':262144}\n"+text[b:]
text+='''def installed_membership():
    tree=doc(SOURCE/'dependency-tree.json');root=Path(tree['sourceRoot'])
    assert root==ROOT/'experiments/node_modules' and root.resolve(strict=True)==root
    actual={'directories':[],'files':[],'symlinks':[]}
    def walk(folder):
        for p in sorted(folder.iterdir()):
            rel=p.relative_to(root).as_posix()
            if p.is_symlink():
                target=p.resolve(strict=True);assert target.is_relative_to(root) and target!=root
                actual['symlinks'].append({'path':rel,'link':str(p.readlink()),'target':target.relative_to(root).as_posix()})
            elif p.is_dir():actual['directories'].append(rel);walk(p)
            elif p.is_file():actual['files'].append(rel)
            else:raise ValueError('Installed special file')
    walk(root)
    for k in ('directories','files'):actual[k].sort()
    actual['symlinks'].sort(key=lambda x:x['path'])
    assert actual=={k:tree[k] for k in ('directories','files','symlinks')}
    assert len(actual['files'])==816 and len(actual['directories'])==65 and len(actual['symlinks'])==2
    return actual


def snapshot(ack_sha):
    source=pin(PREP/'subject.json');assert source['sha256']==SOURCE_SHA
    manifest=pin(PREP/'artifact-manifest.json');assert manifest['sha256']==MANIFEST_SHA
    frozen_plan=pin(PREP/'control-plan.json');assert frozen_plan['sha256']==FROZEN_PLAN_SHA
    plan=doc(PREP/'control-plan.json');current_plan=doc(CAPTURE/'control-plan.json')
    assert plan['separateScopes']==current_plan['separateScopes']
    assert plan['rawRetentionBytes']==LIMITS and all(s['timeoutSeconds']==60 for s in plan['separateScopes'])
    inputs=doc(CAPTURE/'frozen-inputs.json');assert inputs['schema']=='e02-transport-source2-control-frozen-inputs-v1'
    expected=inputs['files'];assert 1<=len(expected)<=4096 and len({d['path'] for d in expected})==len(expected)
    actual=[pin(Path(d['path'])) for d in expected];assert actual==expected
    assert inputs['sourceSubject']==source and pin(PREP/'proposed-run-config.json')==inputs['configuration']
    assert pin(NODE)==inputs['node'] and pin(PYTHON)==inputs['python']
    membership=installed_membership()
    ack_path=CAPTURE/'coordinator-acknowledgement.json';ack_pin=pin(ack_path)
    assert ack_pin['sha256']==ack_sha and ack_path.stat().st_mode&0o777==0o600
    ack=doc(ack_path)
    assert set(ack)=={'schema','actor','sourceSubject','runnerSubject','runner','controlPlan',
        'sourceQaReview','sourceSecurityReview','sourceQaDecision','sourceSecurityDecision',
        'captureQaReview','captureSecurityReview','captureQaDecision','captureSecurityDecision',
        'pureControlsAuthorized','allowedScopes','stopFirstFailure','noRetry',
        'diagnosticRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized',
        'servicesAuthorized','cryptoOrNativeAuthorized','sdkAuthorized'}
    assert ack['schema']=='e02-transport-source2-controls-root-ack-v1' and ack['actor']=='/root'
    assert ack['sourceSubject']==source and ack['allowedScopes']=={s['name']:s['count'] for s in plan['separateScopes']}
    assert ack['runner']==pin(Path(__file__).resolve()) and ack['controlPlan']==pin(CAPTURE/'control-plan.json')
    assert ack['runnerSubject']==pin(CAPTURE/'runner-subject.json')
    for key in ('pureControlsAuthorized','stopFirstFailure','noRetry'):assert ack[key] is True
    for key in ('diagnosticRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized','servicesAuthorized','cryptoOrNativeAuthorized','sdkAuthorized'):assert ack[key] is False
    rs=doc(CAPTURE/'runner-subject.json');assert rs['runner']==ack['runner'] and rs['controlPlan']==ack['controlPlan']
    for d in rs['preparationArtifacts']:assert pin(Path(d['path']))==d
    reviews=[]
    for prefix,subject,parent in (('source',source,PREP),('capture',ack['runnerSubject'],CAPTURE)):
        sessions=[]
        for role,title in (('qa','Qa'),('security','Security')):
            d=ack[prefix+title+'Review'];assert Path(d['path']).parent==parent and pin(Path(d['path']))==d
            r=doc(Path(d['path']));assert set(r)=={'role','session','decision','subject'}
            assert r['role']==role and r['subject']==subject and r['decision']==ack[prefix+title+'Decision']
            assert type(r['session']) is str and r['session'].startswith('/root/') and r['session'] not in (ACTOR,'/root')
            if prefix=='source':assert r['decision']=={'qa':'ACCEPT_DIAGNOSTIC_SOURCE_CONFIG_ONLY','security':'ACCEPT_SOURCE_FOR_SCOPED_DATA_CONTROLS_ONLY'}[role]
            sessions.append(r['session']);reviews.append(d)
        assert len(set(sessions))==2
    return {'sourceSubject':source,'sourceManifest':manifest,'frozenSourcePlan':frozen_plan,
        'frozenInputs':actual,'installedMembership':membership,'configuration':inputs['configuration'],
        'interpreters':{'python':inputs['python'],'node':inputs['node']},'monitor':pin(Path(__file__).resolve()),
        'runnerSubject':ack['runnerSubject'],'controlPlan':ack['controlPlan'],
        'sourceAndCaptureReviewRecords':reviews,'coordinatorAcknowledgement':ack_pin,
        'inputManifest':pin(CAPTURE/'frozen-inputs.json')}


def output_shape(scope,raw):
    if scope['name']=='source-custody-and-host-inventory':
        assert raw['stdout']==b''
        match=re.search(rb'\\nRan ([0-9]+) tests? in [^\\n]+\\n\\nOK\\n\\Z',raw['stderr'])
        assert match and int(match[1])==18
        pairs=re.findall(rb'^(test_[a-z0-9_]+) \\(__main__\\.([A-Za-z0-9_]+)\\.(test_[a-z0-9_]+)\\) \\.\\.\\. ok$',raw['stderr'],re.M)
        actual={}
        for one,klass,two in pairs:
            assert one==two;actual.setdefault(klass.decode(),[]).append(one.decode())
        assert sum(map(len,actual.values()))==18 and len(pairs)==18
        assert {k:sorted(v) for k,v in actual.items()}=={k:sorted(v) for k,v in scope['expectedClassCases'].items()}
        return 18,{'SourceCustodyControls':10,'ClosedDependencyControls':8}
    assert raw['stderr']==b'' and raw['stdout'].endswith(b'\\n') and raw['stdout'].count(b'\\n')==1
    v=strict(raw['stdout']);assert type(v['checks']) is int and v['checks']==scope['count']
    assert v['cases']==scope['expectedCases'] and len(v['cases'])==scope['count'] and len(set(v['cases']))==len(v['cases'])
    if scope['name']=='fake-socket-and-physical-prefix-model':
        assert set(v)=={'scope','checks','cases','realGuardExecuted','networkExecuted','cryptoExecuted','ordinaryClientQualified'}
        assert v['scope']=='TRANSPORT_QUERY_FAKE_SOCKET_PHASE_MODEL_ONLY'
        for k in ('realGuardExecuted','networkExecuted','cryptoExecuted','ordinaryClientQualified'):assert v[k] is False
        return 27,{'priorScopeCasesIncludingVersionedLateBehavior':20,'newFaultFamilies':7}
    assert scope['name']=='guest-dependency-inventory-data'
    assert set(v)=={'scope','checks','cases','optionalModuleImported','networkExecuted','containerExecuted'}
    assert v['scope']=='GUEST_DEPENDENCY_INVENTORY_DATA_ONLY'
    for k in ('optionalModuleImported','networkExecuted','containerExecuted'):assert v[k] is False
    return 6,{'guestInventoryFamilies':6}


def one_scope(scope,ack_sha):
    # These are local immutable bindings. Global HERE/CAPTURE remains the reviewed
    # plan/root-ack directory; original observer AST uses local output HERE/ARGV.
    HERE=CAPTURE/'scopes'/scope['name'];HERE.mkdir(parents=True,mode=0o700)
    ARGV=scope['argv']
    def save(name,value):
        return globals()['save']('scopes/'+scope['name']+'/'+name,value)
'''
# Reuse the original pre-observer data fields and observer subtree literally.
a=raw.index('    before = after = None',raw.index('def main('));b=raw.index("    try:\n        assert raw['stderr']",a)
block=raw[a:b].replace("schema='e02-completion-pure-control-execution-v1'", "schema='e02-transport-source2-pure-scope-execution-v1'").replace('expectedCount=54','expectedCount=scope[\'count\']')
text+=block
text+='''    try:
        count,partitions=output_shape(scope,raw)
        receipt['observedCount']=count;receipt['observedPartitions']=partitions
        receipt['countAndOutputShapeMatched']=True
    except BaseException as exc:error('original-output-shape',exc)
'''
a=raw.index('    try:\n        after = snapshot',b);b=raw.index("    save('result-artifact-manifest.json'",a)
text+=raw[a:b]
text+='''    return receipt,pin(HERE/'execution.json')


def main():
    assert len(sys.argv)==4 and sys.argv[1:3]==['--execute-once','--root-ack-sha']
    ack_sha=sys.argv[3];assert re.fullmatch('[0-9a-f]{64}',ack_sha)
    os.umask(0o077)
    save('started.json',{'actor':ACTOR,'utc':utc(),'pid':os.getpid(),'scope':'ONCE_FIXED_18_27_6_DATA_ONLY'})
    before=snapshot(ack_sha);save('sources-before.json',before)
    scopes=doc(PREP/'control-plan.json')['separateScopes'];assert [s['count'] for s in scopes]==[18,27,6]
    results=[]
    for scope in scopes:
        result,descriptor=one_scope(scope,ack_sha)
        results.append({'scope':scope['name'],'expected':scope['count'],'observed':result['observedCount'],
            'partitions':result.get('observedPartitions'),'captureMatched':result['captureMatched'],'execution':descriptor})
        if not result['captureMatched']:break
    after=snapshot(ack_sha);save('sources-after.json',after)
    matched=len(results)==3 and all(r['captureMatched'] for r in results) and before==after
    save('execution.json',{'schema':'e02-transport-source2-current-control-execution-v1','actor':ACTOR,
        'state':'WRITES_STOPPED','result':'ALL_THREE_DATA_SCOPES_MATCHED_PENDING_REVIEW' if matched else 'STOPPED_FIRST_FAILURE_NO_RETRY',
        'sourceSubject':pin(PREP/'subject.json'),'runnerSubject':pin(CAPTURE/'runner-subject.json'),
        'runner':pin(Path(__file__).resolve()),'controlPlan':pin(CAPTURE/'control-plan.json'),
        'rootAcknowledgement':pin(CAPTURE/'coordinator-acknowledgement.json'),'scopes':results,
        'remainingNotExecuted':[s['name'] for s in scopes[len(results):]],'sourceUnchanged':before==after,
        'noRetry':True,'controlResultAcceptedByAuthor':False,'independentResultReview':'PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY',
        'noDiagnosticRuntimePrimaryConsumerGuardNetworkSdkServices':True})
    save('result-artifact-manifest.json',{'schema':'e02-transport-source2-current-control-artifact-manifest-v1',
        'files':[pin(p) for p in sorted(CAPTURE.rglob('*')) if p.is_file()],
        'originalApiResponses':'Actual caller separately persists exact original toolName/arguments/response immediately.'})
    print(json.dumps({'state':'WRITES_STOPPED','captureMatched':matched,'execution':pin(CAPTURE/'execution.json'),'scopes':results}))
    return 0 if matched else 2


if __name__=='__main__':sys.exit(main())
'''
runner=HERE/'capture-controls.py';runner.write_text(text);runner.chmod(0o600)
old_ast=ast.parse(raw);new_ast=ast.parse(text)
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
unchanged=[];changed=[]
for name in ('utc','pin','strict','doc','save'):
 if ast.dump(function(old_ast,name),include_attributes=False)!=ast.dump(function(new_ast,name),include_attributes=False):raise ValueError('Base primitive changed:'+name)
 unchanged.append(name)
old_main=function(old_ast,'main');new_scope=function(new_ast,'one_scope')
old_error=next(n for n in old_main.body if isinstance(n,ast.FunctionDef) and n.name=='error')
new_error=next(n for n in new_scope.body if isinstance(n,ast.FunctionDef) and n.name=='error')
if ast.dump(old_error,include_attributes=False)!=ast.dump(new_error,include_attributes=False):raise ValueError('First error observer changed')
old_try=next(n for n in old_main.body if isinstance(n,ast.Try));new_try=next(n for n in new_scope.body if isinstance(n,ast.Try))
if ast.dump(old_try,include_attributes=False)!=ast.dump(new_try,include_attributes=False):raise ValueError('Owned-child observation subtree changed')
save('observer-ast-equivalence.json',{'schema':'e02-transport-source2-capture-observer-equivalence-v1','base':pin(BASE),'current':pin(runner),'unchangedTopLevelFunctions':unchanged,'nestedFirstErrorFunctionUnchanged':True,'ownedChildPopenCommunicateExceptionCleanupRawRetentionTryAstUnchanged':True,'lexicalContextBindings':'one_scope local HERE is its own output directory and local ARGV is exact frozen scope argv; local save delegates original exclusive writer with fixed scope prefix. Global snapshot/root ack remain CAPTURE.','changedOrAdded':['snapshot','installed_membership','output_shape','one_scope fixed-scope metadata/output context','main three-scope stop-on-first-failure orchestration'],'deleted':'Original single-scope main replaced; no owned-child lifecycle code deleted.'})
a=ast.dump(old_ast,indent=2,include_attributes=False);b=ast.dump(new_ast,indent=2,include_attributes=False)
save('capture-full-typed-ast-before.json',{'source':pin(BASE),'tree':a});save('capture-full-typed-ast-after.json',{'source':pin(runner),'tree':b})
save('capture-full-typed-ast.diff',''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(BASE),tofile=str(runner))))
save('capture-full-source.diff',''.join(difflib.unified_diff(raw.splitlines(True),text.splitlines(True),fromfile=str(BASE),tofile=str(runner))))
plan=json.loads((PREP/'control-plan.json').read_text())
save('control-plan.json',{'schema':'e02-transport-source2-fixed-capture-plan-v1','author':'/root/ordinary_api35_source','state':'PREPARED_NOT_EXECUTED_PENDING_ACTUAL_CAPTURE_SOURCE_QA_SECURITY_AND_ROOT_RELEASE','sourceSubject':pin(PREP/'subject.json'),'frozenSourcePlan':pin(PREP/'control-plan.json'),'runner':pin(runner),'baseCapture':pin(BASE),'observerAstProof':pin(HERE/'observer-ast-equivalence.json'),'frozenInputs':pin(HERE/'frozen-inputs.json'),'frozenInputCount':len(rows),'separateScopes':plan['separateScopes'],'timeoutSeconds':60,'retentionBytes':{'stdout':1048576,'stderr':262144},'retentionMeaning':'Original communicate in-memory; post-capture file retention/refusal NOT streaming cap.','onceCommand':['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(runner),'--execute-once','--root-ack-sha','ACTUAL_FUTURE_ROOT_ACK_SHA256'],'rootAckSchema':'e02-transport-source2-controls-root-ack-v1','rootAckFields':['schema','actor','sourceSubject','runnerSubject','runner','controlPlan','sourceQaReview','sourceSecurityReview','sourceQaDecision','sourceSecurityDecision','captureQaReview','captureSecurityReview','captureQaDecision','captureSecurityDecision','pureControlsAuthorized','allowedScopes','stopFirstFailure','noRetry','diagnosticRuntimeAuthorized','primaryAuthorized','consumerAuthorized','androidAuthorized','servicesAuthorized','cryptoOrNativeAuthorized','sdkAuthorized'],'reviewShape':['role','session','decision','subject'],'sourceDecisionsKnownActual':{'qa':'ACCEPT_DIAGNOSTIC_SOURCE_CONFIG_ONLY','security':'ACCEPT_SOURCE_FOR_SCOPED_DATA_CONTROLS_ONLY'},'captureDecisions':'NOT_MATERIALIZED_ACTUAL_OTHER_AGENT_DECISIONS_REQUIRED','scopePolicy':'All18/27/6 are new actual current executions if authorized; SOURCE1 hadzero, no executed carry. Named partitions18=10+8,27=20+7,guest6 are checked against exact frozen plan.','externalApiResponses':'Caller preserves original exact toolName/actualArguments/unmodifiedResponse immediately; never inferred by journal.','actualControlsExecuted':False,'rootAckMaterializedByAuthor':False,'rootOwnsActualNonoperatorResultReviews':True})
artifacts=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='runner-subject.json']
save('runner-subject.json',{'schema':'e02-transport-source2-fixed-capture-source-subject-v1','author':'/root/ordinary_api35_source','state':'WRITES_STOPPED_CAPTURE_SOURCE_ONLY_PENDING_ACTUAL_INDEPENDENT_REVIEW','sourceSubject':pin(PREP/'subject.json'),'runner':pin(runner),'controlPlan':pin(HERE/'control-plan.json'),'preparationArtifacts':artifacts,'observerAstProof':pin(HERE/'observer-ast-equivalence.json'),'actualControlsExecuted':False,'captureReviewOrRootAckAuthored':False})
print(json.dumps({'state':'WRITES_STOPPED_CAPTURE_READY_NOT_EXECUTED','runner':pin(runner),'plan':pin(HERE/'control-plan.json'),'subject':pin(HERE/'runner-subject.json'),'observerProof':pin(HERE/'observer-ast-equivalence.json'),'frozenInputCount':len(rows)},indent=2))
