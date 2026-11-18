"""Finite ordinary286 capture SOURCE construction; never executes target scopes.

Development mode writes only a marked mock-test candidate. Final mode requires
the genuine Root producer acceptance, lineage, actor and clock authorities.
"""
import ast
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

R=Path('/home/peterhorvath/apps/bitcoin/NBDP')
E=R/'docs/decisions/evidence'
OUT=E/'e02-producer-eose-capture-20261105/source2'
CAP=OUT/'capture'
B=E/'e02-producer-current-capture-20261105/source1'
P=E/'e02-producer-eose-successor-20261105/source1'
ROOT=OUT.parent
S1=ROOT/'source1'
S2_SCOPE=ROOT/'source2-scope.json'
ACTOR='/root/producer286_capture_source'
ACK_SCOPE='ONE_CURRENT_EOSE_SUCCESSOR_ELEVEN_SELECTED_PURE_CONTROL_GROUPS_ONLY'
SOURCE_DECISION='ACCEPT_PRODUCER_EOSE_SOURCE_AND_286_DEFINITIONS_ONLY'
CODE_NAMES=['assemble.py','capture.py','contracts.py','explicit_inputs.py','outputs.py','request-from-plan.py','test_admission.py','input_authority.py']

def need(v,m):
    if not v:raise ValueError(m)

def encoded(v):return (json.dumps(v,indent=2)+'\n').encode()

def raw(p):
    p=Path(p)
    need(p.is_absolute() and p.resolve(strict=True)==p and not p.is_symlink(),'CANONICAL_SOURCE_PATH')
    a=p.stat();need(stat.S_ISREG(a.st_mode) and a.st_size<=16777216,'SMALL_REGULAR_SOURCE')
    b=p.read_bytes();z=p.stat()
    need(len(b)==a.st_size and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns,a.st_mode)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns,z.st_mode),'STABLE_SOURCE_READ')
    return b

def descriptor(p,b=None):
    p=Path(p);b=raw(p) if b is None else b
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def doc(p):return json.loads(raw(p))

def methods(b):
    return [c.name+'.'+f.name for c in ast.parse(b).body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')]

def assignment(source,name,value):
    lines=source.splitlines(True);hits=[i for i,line in enumerate(lines) if line.startswith(name+'=')]
    need(len(hits)==1,'ONE_ASSIGNMENT:'+name);lines[hits[0]]=name+'='+repr(value)+'\n';return ''.join(lines)

def replace_function(source,name,replacement):
    tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
    lines=source.splitlines(True);return ''.join(lines[:node.lineno-1])+replacement.rstrip()+'\n'+''.join(lines[node.end_lineno:])

def once(source,old,new):
    need(source.count(old)==1,'ONE_EXACT_DELTA:'+old[:80]);return source.replace(old,new,1)

def authorities():
    source=descriptor(P/'producer/subject.json');need(source['sha256']=='acbd539bba00aff05dd218d6c6323bf79904a4c14cfa3d0a9c89d32b3d4235a3','EXACT_PRODUCER_SOURCE')
    acceptance=descriptor(E/'e02-producer-eose-source-review-20261105/r1/acceptance.json')
    need(acceptance['sha256']=='2e54ff60fe6026172913a28820f5f2c5e8a28fc2c33e89ad5e6abca7fbfa5ee3','EXACT_ACTUAL_PRODUCER_ACCEPTANCE')
    lineage=descriptor(E/'e02-producer-eose-source-review-20261105/r1/acceptance-lineage.json')
    need(lineage['sha256']=='764491c972fc3653d57dbdad5c73d11992ba873cfa82ddfacd793d214cdc01c2','EXACT_ACTUAL_LINEAGE')
    known=descriptor(ROOT/'root-known-actors.json');need(known['sha256']=='a79d4482fba4ffbf1dc0a6e8719220ca74d430afd86842d6548b22a219ec20a2','EXACT_ROOT_ACTOR_AUTHORITY')
    clock=descriptor(ROOT/'root-clock-source-selection.json');need(clock['sha256']=='9bc04002aaab49d6ee23ae61418dd8cf94e145dd19d6d3a538ddb8805c7172b3','EXACT_ROOT_CLOCK')
    policy=descriptor(ROOT/'request-policy.json');need(policy['sha256']=='db4869c36721a6170790c256852c6ab7b05287e9add61b0c747baa76841aca11','EXACT_ROOT_REQUEST_POLICY')
    return dict(producerSource=source,producerAcceptance=acceptance,lineage=lineage,knownActors=known,clock=clock,requestPolicy=policy)

def code_files(a):
    producer=doc(a['producerSource']['path']);control=doc(producer['controlPlan']['path']);family=doc(producer['externalCallerRegressionFamily']['path'])
    groups=control['selectedGroups'];need([g['count'] for g in groups]==[129,33,29,16,20,10,11,8,7,3,20],'ELEVEN_REAL_COUNTS')
    external=groups[-1];external_code=producer['externalControlSources'];need(len(external_code)==17,'EXTERNAL_SEVENTEEN_CODE')
    tested=next(d for d in external_code if d['path'].endswith('/candidate/fixture.mjs'))
    originals={n:raw(B/'capture'/n).decode() for n in CODE_NAMES}
    files={n:s for n,s in originals.items()}
    c=files['contracts.py']
    old_constants={}
    for n in ast.parse(c).body:
        if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
            try:old_constants[n.targets[0].id]=ast.literal_eval(n.value)
            except (ValueError,TypeError):pass
    c=assignment(c,'FILES',old_constants['FILES']+('fixtureEoseCaller',))
    c=assignment(c,'MODEL_KEYS',old_constants['MODEL_KEYS']+('fixtureEoseCaller',))
    limits=copy.deepcopy(old_constants['LIMITS']);limits.update(controllerSeconds=1263,outerSeconds=1266)
    ledger=copy.deepcopy(old_constants['LEDGER']);ledger['children']=693
    for name,value in [('LIMITS',limits),('LEDGER',ledger),('SOURCE_DECISION',SOURCE_DECISION),('REQUIRED_KNOWN_ACTORS',tuple(doc(a['knownActors']['path'])['knownActors'])),('ROOT_KNOWN_ACTORS_PIN',a['knownActors']),('REQUEST_POLICY',doc(a['requestPolicy']['path']))]:c=assignment(c,name,value)
    constants=dict(EXTERNAL_SOURCE=external['source'],EXTERNAL_CWD=external['cwd'],EXTERNAL_NAMES=tuple(external['definitionNames']),EXTERNAL_FAMILY_PIN=producer['externalCallerRegressionFamily'],EXTERNAL_CODE=external_code,EXTERNAL_TESTED_FIXTURE=tested,EXTERNAL_FIXTURE_MODE=stat.S_IMODE(Path(tested['path']).stat().st_mode),EXTERNAL_MODES={d['path']:stat.S_IMODE(Path(d['path']).stat().st_mode) for d in external_code})
    marker='ACK_KEYS=';pos=c.index(marker);c=c[:pos]+''.join(k+'='+repr(v)+'\n' for k,v in constants.items())+'\n'+c[pos:]
    fragments=raw(OUT/'contracts-functions.fragment').decode();tree=ast.parse(fragments)
    for n in tree.body:
        if isinstance(n,ast.FunctionDef):
            f=''.join(fragments.splitlines(True)[n.lineno-1:n.end_lineno])
            if n.name in ('counts','validate_plan'):c=replace_function(c,n.name,f)
            else:c+='\n'+f
    c=c.replace('import json,math,re','import hashlib,json,math,re').replace("__import__('hashlib').sha256",'hashlib.sha256')
    c=c.replace('ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY',ACK_SCOPE)
    c=c.replace('CURRENT_PRODUCER4_PURE_CONTROL_CAPTURE_AND_ADMISSION','CURRENT_PRODUCER_EOSE_286_PURE_CONTROL_CAPTURE_AND_ADMISSION')
    c=c.replace('COMPLETE_REQUIRED_EIGHTEEN_KNOWN_ACTORS','COMPLETE_REQUIRED_ROOT_KNOWN_ACTORS')
    c=c.replace('e02-root-current-producer4-source-acceptance-v1','e02-root-producer-eose-source-acceptance-v1')
    c=c.replace("s['scope']=='EXACT_CURRENT_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'","s['scope']=='EXACT_ORDINARY_EOSE_SUCCESSOR_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'")
    c=once(c,"'ACCEPT_PRODUCER4_SOURCE4_AND_'+str(total)+'_CONTROL_DEFINITIONS_ONLY'",'SOURCE_DECISION')
    c=c.replace("'1203s'","'1266s'")
    files['contracts.py']=c
    capture=files['capture.py']
    for name,value in [('CURRENT_PRODUCER_SOURCE',a['producerSource']),('CURRENT_PRODUCER_ACCEPTANCE',a['producerAcceptance']),('CURRENT_SOURCE_LINEAGE',a['lineage']),('CLOCK_SELECTION',a['clock'])]:capture=assignment(capture,name,value)
    capture=capture.replace('1200000000000','1263000000000').replace('GLOBAL1200','GLOBAL1263').replace('WHOLE1200','WHOLE1263')
    capture=capture.replace('e02-root-producer4-source4-acceptance-lineage-v1','e02-root-producer-eose-source-acceptance-lineage-v1')
    capture=capture.replace('pool.run(11-i,','pool.run(len(plan[\'scopes\'])+1-i,').replace('pool.admit_child(11-i)','pool.admit_child(len(plan[\'scopes\'])+1-i)').replace('pool.run(10-i,','pool.run(len(plan[\'scopes\'])-i,')
    capture=capture.replace('len(outcomes)==10','len(outcomes)==len(FILES)').replace('pool.deadline(10)','pool.deadline(len(FILES))').replace('pool.run(10,','pool.run(len(FILES),')
    marker="        elif s['scope']=='test_observation_model.mjs':"
    capture=once(capture,marker,"        elif s['scope']=='fixtureEoseCaller':\n            validate_external_source_names(raw,s)\n"+marker)
    files['capture.py']=capture
    out=files['outputs.py'].replace('from contracts import need,closed','from contracts import need,closed,EXTERNAL_NAMES')
    marker="    if name=='test_observation_model.mjs':"
    external_branch="""    if name=='fixtureEoseCaller':
        closed(value,'schema scope checks cases baselineFailureReproduced baselineFailure runtimeExecuted helperExecuted networkExecuted ordinaryRowsQualified canonicalE02')
        need(value['schema']=='e02-fixture-eose-pure-regression-result-v1' and value['scope']=='EXACT_SOURCE_CALLBACK_AND_UNCHANGED_GUARD_CORE_WITH_FAKE_TRANSPORT_AND_CLOCKS','EXACT_EXTERNAL_EOSE20_SCHEMA')
        need(type(value['checks']) is int and value['checks']==count==20 and value['cases']==scope['definitionNames']==list(EXTERNAL_NAMES),'EXACT_EXTERNAL_TWENTY_ORDERED_CASES')
        need(value['baselineFailureReproduced'] is True and value['baselineFailure']=='QUEUED_CONTEXT_CHANGED','ACTUAL_BASELINE_FAILURE_REPRODUCER')
        need(all(value[k] is False for k in ('runtimeExecuted','helperExecuted','networkExecuted')) and type(value['ordinaryRowsQualified']) is int and value['ordinaryRowsQualified']==0 and value['canonicalE02']=='PARTIAL22','EXTERNAL_PURE_LIMITS_NOT_RUNTIME')
        return dict(scope=name,count=count,membershipMeaning='EXACT_REAL_CALLBACK_WITH_SYNTHETIC_TRANSPORT_CLOCKS_NOT_NETWORK_OR_RUNTIME',sourceNames=value['cases'],actualNodeSummary=value,allOk=True)
"""
    out=once(out,marker,external_branch+marker);files['outputs.py']=out
    files['assemble.py']=files['assemble.py'].replace("==10 and 0<=result['elapsedNs']<=1200000000000","==11 and 0<=result['elapsedNs']<=1263000000000").replace('ALL_TEN_NATURAL_CURRENT_SCOPES_ONLY','ALL_ELEVEN_NATURAL_CURRENT_SCOPES_ONLY').replace('ALL20_PER_SCOPE_EXPECTED_CUSTODY_SNAPSHOTS','ALL22_PER_SCOPE_EXPECTED_CUSTODY_SNAPSHOTS')
    tests=files['test_admission.py']
    tests=tests.replace('ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY',ACK_SCOPE).replace('CURRENT_PRODUCER4_PURE_CONTROL_CAPTURE_AND_ADMISSION','CURRENT_PRODUCER_EOSE_286_PURE_CONTROL_CAPTURE_AND_ADMISSION')
    tests=tests.replace('e02-root-current-producer4-source-acceptance-v1','e02-root-producer-eose-source-acceptance-v1').replace('EXACT_CURRENT_SOURCE_AND_CONTROL_DEFINITIONS_ONLY','EXACT_ORDINARY_EOSE_SUCCESSOR_SOURCE_AND_CONTROL_DEFINITIONS_ONLY')
    tests=tests.replace("'ACCEPT_PRODUCER4_SOURCE4_AND_20_CONTROL_DEFINITIONS_ONLY'",'c.SOURCE_DECISION').replace("modelsDefined=20,runtimeWorkerCount",'modelsDefined=40,runtimeWorkerCount')
    tests=tests.replace("testpins=[p('source4/'+n) for n in c.FILES]","testpins=[p('source4/'+n) for n in c.FILES[:10]]")
    tests=tests.replace("modelsDefined=dict.fromkeys(c.MODEL_KEYS,2)","modelsDefined={**dict.fromkeys(c.MODEL_KEYS[:10],2),'fixtureEoseCaller':20}")
    marker=" control=dict(selectedJavaScriptDefinitions="
    pos=tests.index(marker);lineend=tests.index('\n',pos)
    tests=tests[:pos]+"\n source['externalCallerRegressionFamily']=c.EXTERNAL_FAMILY_PIN;source['externalControlSources']=copy.deepcopy(c.EXTERNAL_CODE);source['externalControlSourceCount']=17\n fixture_pin=dict(path='/MOCK/source4/fixture.mjs',bytes=c.EXTERNAL_TESTED_FIXTURE['bytes'],sha256=c.EXTERNAL_TESTED_FIXTURE['sha256']);source['sources'].append(fixture_pin)\n control=dict(selectedJavaScriptDefinitions=[dict(file=n,expandedDefinitions=2) for n in c.FILES[:5]]+[dict(file=c.EXTERNAL_SOURCE['path'],expandedDefinitions=20)],pythonDefinitions=[dict(file=n,methodDefinitions=2) for n in c.FILES[5:10]],externalCallerRegressionFamily=c.EXTERNAL_FAMILY_PIN)"+tests[lineend:]
    tests=tests.replace('countsSeparate=[2]*10','countsSeparate=[2]*10+[20]').replace('self.assertEqual(admit(f)[0],[2]*10)','self.assertEqual(admit(f)[0],[2]*10+[20])')
    marker=" plan=dict(schema='e02-producer4-control-capture-plan-v1'"
    pos=tests.index(marker);tests=tests[:pos]+" scopes.append(dict(scope='fixtureEoseCaller',source=c.EXTERNAL_SOURCE,argv=[tools['node']['path'],c.EXTERNAL_SOURCE['path']],cwd=c.EXTERNAL_CWD,count=20,definitionNames=list(c.EXTERNAL_NAMES),format='EXACT_EXTERNAL_EOSE20_NODE_JSON'))\n control['selectedGroups']=[dict(scope=s['scope'],source=s['source'],cwd=s['cwd'],count=s['count'],definitionNames=s['definitionNames'],**({'externalSourceFamily':c.EXTERNAL_FAMILY_PIN} if s['scope']=='fixtureEoseCaller' else {})) for s in scopes]\n"+tests[pos:]
    tests=tests.replace("files=source['sources']+list(cfgs.values())+list(tools.values())+method['sources'];manifest=", "files=source['sources']+source['externalControlSources']+[c.EXTERNAL_FAMILY_PIN]+list(cfgs.values())+list(tools.values())+method['sources'];manifest=")
    tests=once(tests," clock=dict(schema='e02-root-control-capture-clock-source-selection-v1',actor='/root',controllerSeconds=1200,outerKillSeconds=1203,sharedInputSnapshotPoolSeconds=480,maximumSerialScopes=10,eachScopeSeconds=60,eachOwnedTerminationReserveSeconds=3,sumSeconds=1200)"," for row in manifest['files']:\n  if row['pin']['path'] in c.EXTERNAL_MODES:row['mode']=c.EXTERNAL_MODES[row['pin']['path']]\n  if row['pin']['path']==fixture_pin['path']:row['mode']=c.EXTERNAL_FIXTURE_MODE\n clock=dict(schema='e02-root-control-capture-clock-source-selection-v2',actor='/root',controllerSeconds=1263,outerKillSeconds=1266,sharedInputSnapshotPoolSeconds=480,maximumSerialScopes=11,eachScopeSeconds=60,eachOwnedTerminationReserveSeconds=3,metadataAndCleanupSeconds=30,otherReserveSeconds=60,sumSeconds=1263)")
    tests=tests.replace("self.assertIn('1203s'","self.assertIn('1266s'").replace('pool.admit_child(10)','pool.admit_child(11)').replace('61000000000','64000000000').replace('end=1200000000000','end=1263000000000').replace("len(result['remainingNotExecuted']),9","len(result['remainingNotExecuted']),10")
    marker="if __name__=='__main__':unittest.main(verbosity=2)";tests=once(tests,marker,raw(OUT/'admission-new.fragment').decode()+'\n'+marker)
    tests=tests.replace(' import outputs\n',' import outputs\n import artifact_validation\n',1)
    files['test_admission.py']=tests
    files['artifact_validation.py']=raw(OUT/'artifact_validation.py').decode()
    renderer=raw(B/'render_ready.py').decode()
    renderer=assignment(renderer,'OWNED_ROOT',str(OUT)).replace('OWNED_ROOT='+repr(str(OUT)),'OWNED_ROOT=pathlib.Path('+repr(str(OUT))+')',1)
    for name,value in [('PRODUCER_PIN',a['producerSource']),('PRODUCER_ACCEPTANCE',a['producerAcceptance']),('LINEAGE_PIN',a['lineage']),('KNOWN_PIN',a['knownActors']),('REQUEST_POLICY',doc(a['requestPolicy']['path']))]:renderer=assignment(renderer,name,value)
    renderer=renderer.replace('len(required) == 18','len(required) == '+str(len(doc(a['knownActors']['path'])['knownActors']))).replace('KNOWN18','KNOWN_CURRENT')
    renderer=renderer.replace('ACCEPT_PRODUCER4_SOURCE4_AND_266_CONTROL_DEFINITIONS_ONLY',SOURCE_DECISION).replace('ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY',ACK_SCOPE).replace("author='/root/native_rebuild_prepare'","author="+repr(ACTOR))
    files['../render_ready.py']=renderer
    files['../request_preflight.py']=raw(B/'request_preflight.py').decode()
    files['../input_authority.py']=raw(B/'input_authority.py').decode()
    for name,s in files.items():ast.parse(s,filename=name)
    return {name:s.encode() for name,s in files.items()},dict(limits=limits,ledger=ledger,external=constants)

def write_development(a):
    return freeze_source(a,development_only=True)


def main():
    need(Path(__file__).resolve()==OUT/'prepare_source.py','FIXED_PREPARATION_LOCATION')
    a=authorities()
    if sys.argv[1:]==['--development-only']:write_development(a)
    elif sys.argv[1:]==['--freeze-source']:freeze_source(a)
    else:raise ValueError('EXACT_SOURCE_PREPARATION_MODE')


def freeze_source(a,development_only=False):
    need(not CAP.exists() and not (OUT/'review-entrypoint.json').exists(),'ONE_FINAL_SOURCE_FREEZE')
    code,profile=code_files(a);mem={};modes={};selections=[]
    producer=doc(a['producerSource']['path']);accepted=doc(a['producerAcceptance']['path']);lineage=doc(a['lineage']['path']);known=doc(a['knownActors']['path'])
    need(accepted['subject']==a['producerSource'] and accepted['decision']==SOURCE_DECISION and accepted['modelsDefined']==286 and lineage['acceptance']==a['producerAcceptance'] and known['producerSource']==a['producerSource'],'ACTUAL_CURRENT_ROOT_AUTHORITIES')
    need(len(known['knownActors'])==23 and set(producer['sourceContributors'])<set(known['knownActors']),'FULL_ROOT_KNOWN23')
    def put(path,value):
        path=Path(path);need(path.is_relative_to(OUT) and path not in mem and not path.exists(),'EXCLUSIVE_OWNED_SOURCE_OUTPUT')
        b=value if type(value) is bytes else encoded(value);need(len(b)<=16777216,'FINITE_SOURCE_MEMBER');mem[path]=b;modes[str(path)]=0o600;return descriptor(path,b)
    def p(path):
        path=Path(path);return descriptor(path,mem[path]) if path in mem else descriptor(path)
    def mode(path):return modes[str(path)] if str(path) in modes else stat.S_IMODE(Path(path).lstat().st_mode)
    def typed(path):return json.loads(mem[Path(path)]) if Path(path) in mem else doc(path)
    # Only CODE and pure contract inputs are copied; no operational payloads.
    for name,b in code.items():put((CAP/name).resolve(),b)
    for name in ['producer-source-acceptance-contract.json','capture-source-acceptance-contract.json','capture-admission-data-acceptance-contract.json']:
        value=doc(B/'capture/contracts'/name)
        if name=='producer-source-acceptance-contract.json':
            value['rootAcceptance']['literals']['schema']='e02-root-producer-eose-source-acceptance-v1';value['rootAcceptance']['literals']['decision']=SOURCE_DECISION
            value['rootAcceptance']['literals']['scope']='EXACT_ORDINARY_EOSE_SUCCESSOR_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'
            value['rootAcceptance']['modelsDefined']='Exact sum of eleven CODE-selected current groups, including the fixed external20 family; integer, positive and no caller override.'
            value['reviewEnvelope']['decision']=SOURCE_DECISION
        put(CAP/'contracts'/name,value)
    put(CAP/'contracts/root-clock-source-selection.json',raw(a['clock']['path']))
    put(CAP/'contracts/root-known-actors.json',raw(a['knownActors']['path']))
    data_contract=doc(B/'capture/contracts/current-producer-data-acceptance-contract-266.json')
    data_contract['schema']='e02-root-producer4-current-control-data-acceptance-contract-v2'
    data_contract['literals'].update(decision='ACCEPT_PRODUCER_EOSE_CURRENT_286_PURE_CONTROL_DATA_ONLY',countsSeparate=producer['selectedCountsSeparate'],modelsExecuted=286,modelsPassed=286,scope='CURRENT_EOSE_ELEVEN_PURE_CONTROL_GROUPS_DATA_ONLY')
    data_contract['reviews']['decision']=data_contract['literals']['decision']
    data_contract['evidenceRequirements']=[
        'Exact accepted ordinary EOSE successor Source64/runtime22 plus frozen external17 CODE family; genuine new capture Source and full admission DATA. Original helper d422/266/R10 evidence remains a separate immutable component basis.',
        'One genuine Root ACK, all11 ordered natural child0/reaped/fullEOF; full286 named selected definitions including the exact real callback20 fake-transport family; no old266/development219 transfer.',
        'Whole exact7 outer API launch/all same-session polls/natural terminal0; no inferred inner lifecycle from API.',
        'Uniform expected hash/mode/identity and complete SDK/guard/Node membership before/after each11scope and overall under Root1263/1266 selection. Preserve all2175baseline declarations with six explicit supersessions/2169retained rows and finite new additions.']
    put(CAP/'contracts/current-producer-data-acceptance-contract-286.json',data_contract)
    authors=sorted(set(doc(B/'capture/contributors.json')['authors'])|set(producer['sourceContributors'])|{ACTOR,'/root/bridge_start_bootstrap_architecture','/root/ordinary_current266_templates'})
    need(set(authors)<=set(known['knownActors']),'EVERY_ACTUAL_CODE_DESIGN_AUTHOR_KNOWN')
    contributors=put(CAP/'contributors.json',dict(schema='e02-current-capture-contributors-v1',author=ACTOR,authors=authors,
        inheritedRequiredActors=doc(B/'capture/contracts/root-known-actors.json')['knownActors'],currentRequiredActors=known['knownActors'],producerContributors=producer['sourceContributors'],knownActors=a['knownActors'],requestScope=p(S2_SCOPE),
        noReviewerFabricated=True,unknownHistoricalAuthorship='UNKNOWN',executionAuthorized=False))
    case_names=methods(code['test_admission.py']);old_names=methods(raw(B/'capture/test_admission.py'))
    need(len(old_names)==33 and len(case_names)==42 and len(set(case_names))==42 and set(old_names)<=set(case_names),'ALL41_SOURCE1_PURPOSES_PLUS_REAL_ARTIFACT_REGRESSION')
    source1_names=methods(raw(S1/'capture/test_admission.py'))
    source1_test_asts={n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(raw(S1/'capture/test_admission.py'))) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    source2_test_asts={n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(code['test_admission.py'])) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    need(len(source1_names)==41 and set(source1_names)<=set(case_names) and all(source2_test_asts[n]==v for n,v in source1_test_asts.items()),'ALL41_SOURCE1_ADMISSION_METHOD_BODIES_AST_UNCHANGED')
    admission=put(CAP/'admission-plan.json',dict(schema='e02-producer4-capture-admission-plan-v1',caseNames=case_names,modelsDefined=len(case_names),source=p(CAP/'test_admission.py'),producerSource=a['producerSource'],modelsExecuted=0,scope='PURE_MOCKED_CAPTURE_ADMISSION_ONLY',targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0,sourceReviewRequired=True,releaseRequired=True))
    diff=''.join(line for name in CODE_NAMES+['../render_ready.py','../request_preflight.py','../input_authority.py']
        for line in difflib.unified_diff(raw((B/'capture'/name).resolve()).decode().splitlines(True),code[name].decode().splitlines(True),fromfile=str((B/'capture'/name).resolve()),tofile=str((CAP/name).resolve())))
    diff+=''.join(difflib.unified_diff([],code['artifact_validation.py'].decode().splitlines(True),fromfile='NEW_PURE_EMITTED_ARTIFACT_VALIDATOR',tofile=str(CAP/'artifact_validation.py')))
    diff_pin=put(OUT/'source.diff',diff.encode())
    def functions(b):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    old_functions=functions(raw(B/'capture/capture.py'));new_functions=functions(code['capture.py'])
    stable=[n for n,v in old_functions.items() if new_functions.get(n)==v]
    need(all(n in stable for n in ['signal_owned_group','finish_owned','capture_scope','expected_authorities','snapshot']),'ORIGINAL_OWNED_PIPE_AND_SNAPSHOT_ENGINES_UNCHANGED')
    carry=[n for n in CODE_NAMES if raw(B/'capture'/n)==code[n]]
    need(set(carry)=={'explicit_inputs.py','request-from-plan.py','input_authority.py'},'THREE_CORE_ENGINES_BYTE_IDENTICAL')
    need(raw(B/'request_preflight.py')==code['../request_preflight.py'] and raw(B/'input_authority.py')==code['../input_authority.py'],'UNCHANGED_PARENT_INPUT_AND_REQUEST_PREFLIGHT')
    # Preserve every existing expected row. The immutable2175/six/2169
    # projection remains the base; prior current rows become explicit historical
    # additions rather than being silently dropped or re-labelled current DATA.
    old_manifest_pin=descriptor(B/'capture/input-manifest.json');old_manifest=doc(old_manifest_pin['path'])
    need(old_manifest['actualInputCount']==len(old_manifest['files'])==2392,'EXACT_PREDECESSOR2392_EXPECTED_ROWS')
    old_authority=doc(old_manifest['currentExpectedInputAuthority']['path']);legacy=doc(old_authority['baselineManifest']['path'])
    need(len(legacy['files'])==2175 and len(old_authority['supersessions'])==6 and old_authority['retainedRowCount']==2169,'EXACT_2175_SIX_2169_PRECEDENCE')
    removed={row['before']['pin']['path'] for row in old_authority['supersessions']}
    retained={row['pin']['path']:row for row in legacy['files'] if row['pin']['path'] not in removed}
    need(len(retained)==2169,'EXACT_RETAINED_ROWS')
    seen={row['pin']['path']:copy.deepcopy(row) for row in old_manifest['files']};need(len(seen)==2392 and all(seen[k]==v for k,v in retained.items()),'ALL_PRIOR_ROWS_UNCHANGED')
    for row in seen.values():
        path=Path(row['pin']['path']);need(path.name not in ['PROJECT_STATE.md','ROADMAP.md','checkpoint.json','coordinator-acknowledgement.json','runtime-bindings.json'] and '65d8116b77bc0af1a108122ec28cfcea' not in str(path),'NO_MUTABLE_GLOBAL_OR_SEALED_HELPER_PROOF')
        need(path.is_file() and not path.is_symlink() and path.stat().st_size==row['pin']['bytes'] and mode(path)==row['mode'],'PRIOR_EXPECTED_ROW_BACKING_STAT')
    coverage=copy.deepcopy(old_manifest['requiredCoverage'])
    inherited_self=old_manifest['currentExpectedInputAuthority']
    need(coverage.pop('currentExpectedInputAuthority')==[inherited_self],'EXACT_INHERITED_SELF_COVERAGE_RENAMED_NOT_DROPPED')
    need('historicalPriorExpectedInputAuthority' not in coverage,'NEW_EXPLICIT_HISTORICAL_COVERAGE_NAME')
    coverage['historicalPriorExpectedInputAuthority']=[inherited_self]
    def add(d,group,selector,role='METADATA_AUTHORITY'):
        path=Path(d['path']);need(str(path) not in removed and '65d8116b77bc0af1a108122ec28cfcea' not in str(path),'NO_REMOVED_ALIAS_OR_SEALED_HELPER_READ')
        need(p(path)==d,'EXACT_DECLARED_NEW_SOURCE_PIN')
        row=dict(pin=d,mode=mode(path),role=role,origin=selector)
        if str(path) in seen:need(seen[str(path)]['pin']==d and seen[str(path)]['mode']==row['mode'],'NO_PIN_MODE_CONFLICT')
        else:seen[str(path)]=row
        vector=coverage.setdefault(group,[])
        if d not in vector:vector.append(d)
        selections.append(dict(selector=selector,pin=d,coverageGroup=group,role=role))
    for d in producer['sources']:add(d,'ordinarySuccessor64Source','CURRENT_SOURCE_SELECTED64','SOURCE')
    for d in producer['runtimeSources']:add(d,'ordinarySuccessor22Runtime','CURRENT_RUNTIME22','SOURCE')
    for d in producer['configurations'].values():add(d,'ordinarySuccessorConfigurations','CURRENT_CANONICAL_UNISSUED_CONFIG')
    for d in producer['externalControlSources']:add(d,'externalCaller17Code','EXPLICIT_EXTERNAL_CALLER_SOURCE_IMPORT_READ_CLOSURE','SOURCE')
    add(producer['externalCallerRegressionFamily'],'externalCallerFamily','EXACT_EXTERNAL_TYPED_FAMILY')
    for name in ['manifest.json','complete-freeze.json','review-entrypoint.json','lineage.json','input-read-map.json','helper-eight-source-equivalence.json','failed-history-source-declaration.json']:
        add(descriptor(P/name),'ordinarySuccessorSourceProvenance','DECLARED_SOURCE_PROVENANCE/'+name)
    for key,d in a.items():add(d,'actualRootSourceAndCaptureAuthority','ROOT_AUTHORITY/'+key)
    for d in [a['producerSource'],producer['controlPlan'],*accepted['reviews'],lineage['completeFreeze'],lineage['reviewerBirth']]:add(d,'actualAcceptedProducerSource','ISSUED_SOURCE_ACCEPTANCE_ONLY')
    add(descriptor(ROOT/'source-scope.json'),'actualRootSourceAndCaptureAuthority','ROOT_ORIGINAL_BOUNDED_SOURCE_SCOPE')
    add(descriptor(S2_SCOPE),'actualRootSourceAndCaptureAuthority','ROOT_SOURCE2_CORRECTION_SCOPE')
    for d in doc(OUT/'source1-preservation-before.json')['files']:add(d,'historicalFailedSource1Context','EXACT_SOURCE1_PRESERVED_CONTEXT')
    add(descriptor(E/'e02-producer-eose-capture-review-20261105/source1/source1-negative-disposition.json'),'historicalFailedSource1Context','ACTUAL_ROOT_SOURCE1_HOLD')
    add(old_manifest_pin,'historicalCurrent2392Authority','EXACT_RETAINED_HISTORICAL_CURRENT_INPUT_MANIFEST')
    add(descriptor(B/'capture/code-subject.json'),'historicalCaptureSource','ACCEPTED_PREDECESSOR_CAPTURE_CODE_SUBJECT')
    generator_sources=[OUT/'prepare_source.py',OUT/'contracts-functions.fragment',OUT/'admission-new.fragment',OUT/'artifact_validation.py',OUT/'source1-preservation-before.json']
    core_sources=[p((CAP/name).resolve()) for name in code]+[p(path) for path in sorted(mem) if path.is_relative_to(CAP/'contracts')]+[contributors,admission]
    core_sources += [descriptor(path) for path in generator_sources]
    core_sources=list({d['path']:d for d in core_sources}.values())
    for d in core_sources:add(d,'currentCaptureCodeAndAdmission','CURRENT_CAPTURE_CODE_OR_ADMISSION','SOURCE')
    add(diff_pin,'currentCaptureDelta','EXACT_SOURCE_DELTA','SOURCE')
    delta=put(OUT/'invariance-and-delta.json',dict(schema='e02-ordinary286-capture-source-delta-v1',author=ACTOR,
        baselineCaptureSource=descriptor(B/'capture/code-subject.json'),baselineInputManifest=old_manifest_pin,
        originalBaselineRows=2175,explicitSupersessions=6,retainedOriginalRows=2169,allPrevious2392RowsPreserved=True,
        unchangedCoreEngineFiles=carry,unchangedParentFiles=['input_authority.py','request_preflight.py'],unchangedCaptureFunctionAsts=stable,
        changedCaptureFunctionAsts=[n for n,v in old_functions.items() if new_functions.get(n)!=v],
        originalAdmissionNames=old_names,currentAdmissionNames=case_names,original33PurposesPreserved=True,
        newlyDefinedAdmissionCases=9,source1AdmissionNames=methods(raw(S1/'capture/test_admission.py')),source1PurposesPreserved=True,admissionDefined=42,admissionCanonicalExecuted=0,developmentAdmissionExecuted=42 if (OUT/'development/admission42-native-origin.json').exists() else 0,
        fixedScopeCount=11,countsSeparate=producer['selectedCountsSeparate'],producerModelsDefined=286,producerModelsExecuted=0,
        internalClockChanges=dict(previousController=1200,currentController=1263,previousOuter=1203,currentOuter=1266,snapshotPoolUnchanged=480,perChildUnchanged=[60,3],rootAuthority=a['clock']),
        externalFamilyFixed=producer['externalCallerRegressionFamily'],sourceDiff=diff_pin,
        originalHelper266R10AndOrdinary1800Unchanged=True,wholeInputQualified=False,sourceAccepted=False,executionAuthorized=False))
    add(delta,'currentCaptureDelta','EXPLICIT_BOUNDED_DELTA')
    core_sources += [diff_pin,delta]
    additional=[seen[k] for k in sorted(seen) if k not in retained]
    authority=put(CAP/'expected-input-authority.json',dict(schema='e02-producer4-current-expected-input-authority-v1',author=ACTOR,
        scope=p(S2_SCOPE),state='FROZEN_SOURCE_REQUIRES_INDEPENDENT_ACCEPTANCE',
        baselineManifest=old_authority['baselineManifest'],baselineRowCount=2175,supersessions=old_authority['supersessions'],retainedRowCount=2169,
        retainedRowsSha256=old_authority['retainedRowsSha256'],additionalRows=additional,projectedRowCountExcludingSelf=len(seen),selfMode=0o600,
        coverage=coverage,typedSelectors=selections,readSiteProjection=dict(
            inherited='All prior2392 immutable expected rows are retained; none is current286 DATA or mutable Root state.',
            current='Explicit newproducer64/runtime22/configuration/Source acceptance/lineage/source provenance and17external CODE plus exact family/source-target mode join.',
            capture='All current CODE, admission definitions, Root clock23actor policy and inputauthority are uniformly snapshotted before/after every11scope.',
            external='Only frozen declared17 CODE/read/import members and family metadata, no recursive development proof or helper operational read.',
            dynamic='Ownmethod/plan/reviews/acceptances/ACK/runtimebindings remain external expected_authorities to avoid self-pin cycles.'),wholeInputQualified=False,executionAuthorized=False))
    seen[authority['path']]=dict(pin=authority,mode=0o600,role='METADATA_AUTHORITY',origin='CURRENT_FINITE_EXPECTED_INPUT_AUTHORITY')
    coverage=copy.deepcopy(coverage);coverage['currentExpectedInputAuthority']=[authority]
    method_sources=core_sources+[authority,a['clock'],a['knownActors'],a['requestPolicy']]
    method_sources=list({d['path']:d for d in method_sources}.values())
    method=put(CAP/'code-subject.json',dict(schema='e02-producer4-control-capture-code-subject-v1',authors=authors,producerSource=a['producerSource'],knownActors=a['knownActors'],codeOnly=True,sources=method_sources,
        admissionModelsDefined=42,admissionModelsExecuted=0,targetModelsExecuted=0,helperExecutions=0,ordinaryRoleExecutions=0,
        excludedMutableMetadata=['execution-plan','reviews','acceptances','root-ack','runtime-output'],sourceReadiness='REQUIRES_FRESH_INDEPENDENT_SOURCE_REVIEW_AND_SEPARATE_ADMISSION_DATA',sourceReady=False,
        expectedInputAuthority=authority,requestPolicyScope=p(S2_SCOPE),selfApproval=False))
    proofs=[dict(actor=actor,authority=a['knownActors'],selector='/knownActors/'+str(i)) for i,actor in enumerate(known['knownActors'])]
    context=put(CAP/'actor-context.json',dict(schema='e02-producer4-capture-current-actor-context-v1',producerSource=a['producerSource'],captureSource=method,sourceBirth=a['lineage'],participants=known['knownActors'],participantProofs=proofs))
    manifest=put(CAP/'input-manifest.json',dict(schema='e02-producer4-explicit-host-input-manifest-v1',producerSource=a['producerSource'],closedSourceSubjectKeys=sorted(producer),controlPlan=producer['controlPlan'],files=[seen[k] for k in sorted(seen)],actualInputCount=len(seen),maximumInputCount=20000,requiredCoverage=coverage,fullTrees=old_manifest['fullTrees'],nodeDependencies=old_manifest['nodeDependencies'],baselineInputAuthority=old_authority['baselineManifest'],currentExpectedInputAuthority=authority,scope='EXACT2169_RETAINED_PLUS_ALL_PREVIOUS2392_AND_TYPED_SUCCESSOR_ADDITIONS',baselineDataTransferClaimed=False,privateKeysRead=False,opaqueRawMeaning='Every selected row is uniformly streamed; preparation is not whole-input acceptance.'))
    # Execute only the unchanged pure projection validator, never capture/targets.
    import importlib.util
    need(mem[CAP/'input_authority.py']==raw(B/'capture/input_authority.py'),'STRICT_VALIDATOR_BYTE_IDENTICAL')
    temporary_path=str(B/'capture');sys.path.insert(0,temporary_path)
    try:
        import input_authority
        spec=importlib.util.spec_from_file_location('source2_pure_artifact_validation',OUT/'artifact_validation.py')
        artifact_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(artifact_module)
        old_pair=(doc(S1/'capture/expected-input-authority.json'),doc(S1/'capture/input-manifest.json'))
        artifact_result=artifact_module.check_emitted(typed(authority['path']),legacy,typed(manifest['path']),inherited_self,old_pair)
    finally:sys.path.pop(0)
    artifact_report=put(OUT/'emitted-artifact-validation.json',dict(artifact_result,authority=authority,manifest=manifest,baseline=old_authority['baselineManifest'],source1Authority=descriptor(S1/'capture/expected-input-authority.json'),source1Manifest=descriptor(S1/'capture/input-manifest.json'),phase='ACTUAL_COMPLETED_EMITTED_METADATA_BEFORE_FINAL_WRITES'))
    old_plan=doc(B/'capture/execution-plan.json');scopes=[];control=doc(producer['controlPlan']['path'])
    for i,g in enumerate(control['selectedGroups']):
        ext=i==10;node=i<5 or ext
        scopes.append(dict(scope=g['scope'],source=g['source'],argv=[old_plan['tools']['node']['path'],g['source']['path']] if node else [old_plan['tools']['python']['path'],'-I','-B',g['source']['path']],cwd=g['cwd'],count=g['count'],definitionNames=g['definitionNames'],format='EXACT_EXTERNAL_EOSE20_NODE_JSON' if ext else 'EXACT_SELECTED_NODE_JSON' if node else 'QUIET_UNITTEST_NO_SKIPS'))
    need(len(scopes)==11 and sum(g['count'] for g in scopes)==286,'EXACT_ELEVEN286_PLAN')
    plan=put(CAP/'execution-plan.json',dict(schema='e02-producer4-control-capture-plan-v1',readiness=False,producerSource=a['producerSource'],captureSource=method,inputManifest=manifest,limits=profile['limits'],deadlineLedger=profile['ledger'],scopes=scopes,countsSeparate=producer['selectedCountsSeparate'],tools=old_plan['tools'],outputRoot=None,requiredCoverage=coverage,clockSelection=a['clock'],actualSourceReviewPins=accepted['reviews'],captureSourceReviews=None,captureSourceAcceptance=None,admissionDataAcceptance=None,rootAcknowledgement=None,scope='SOURCE_PREPARATION_ONLY_NO_EXECUTION_AUTHORITY'))
    import shlex
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','1266s',old_plan['tools']['python']['path'],'-I','-B',str(CAP/'capture.py'),'--execute-once','--root-ack-sha','<ACTUAL_ROOT_ACK_SHA256>']
    request=put(CAP/'request-template.json',dict(cmd=shlex.join(argv),workdir=str(CAP),login=False,yield_time_ms=1000,max_output_tokens=2000,**doc(a['requestPolicy']['path'])))
    binding=put(CAP/'runtime-bindings.json',dict(schema='e02-producer4-capture-runtime-bindings-v1',readiness=False,producerSource=a['producerSource'],producerAcceptance=a['producerAcceptance'],captureSourceAcceptance=None,admissionDataAcceptance=None,rootAcknowledgement=None))
    old_ack=doc(B/'capture/root-ack.UNISSUED.json');ack={key:None for key in old_ack}
    ack.update(schema='e02-producer4-control-capture-root-ack-v1',actor='/root',executionAuthorized=False,scope=ACK_SCOPE,producerSource=a['producerSource'],producerSourceAcceptance=a['producerAcceptance'],producerReviews=accepted['reviews'],captureSource=method,admissionPlan=admission,sourceBirth=a['lineage'],actorContext=context,inputManifest=manifest,plan=plan,clockSelection=a['clock'],requestContract=request,runtimeBindings=binding,authors=authors,operators=None,noRetry=True)
    ack_pin=put(CAP/'root-ack.UNISSUED.json',ack)
    development=put(OUT/'development-summary.json',dict(schema='e02-ordinary286-capture-development-evidence-v1',author=ACTOR,admissionDefinitions=42,originalMethodsPreserved=33,newMethods=9,developmentChecksPassed=42 if (OUT/'development/admission42-native-origin.json').exists() else 0,originalToolOrigin=descriptor(OUT/'development/admission42-native-origin.json') if (OUT/'development/admission42-native-origin.json').exists() else None,rawOutput=descriptor(OUT/'development/admission42-output.txt') if (OUT/'development/admission42-output.txt').exists() else None,canonicalAdmissionDataAccepted=False,producerScopesExecuted=0,helperOrRuntimeExecuted=False,executionAuthorized=False))
    put(OUT/'README.md',b'''# Ordinary EOSE286 capture SOURCE

This is a SOURCE-only successor of the accepted266 capture. It selects eleven
fixed families and286 definitions, including the exact external callback20 Node
script under its own reviewed cwd. Its full17-member local CODE/read/import
closure and byte/hash/mode equality to the newproducer fixture are protected.
No test source is rewritten or duplicated into producer64.

All2175 original declarations retain their six explicit supersessions and2169
retained rows. All previous2392 current-input rows remain immutable historical
expected operands, with finite explicit successor additions. They are not
new286 DATA. SDK434, guard522 and Node membership checks and uniform streaming
remain unchanged. No arbitrary descriptor recursion or sealed helper read occurs.

Root explicitly selected internal1263 controller/1266 outer clocks:480 shared
snapshot seconds, eleven60+3 children,30 metadata/cleanup and60 other reserve.
The original ordinary1800 lease and helper/R10/bridge clocks are unchanged.
Original pipe ownership, group closure, absolute reap deadline, raw retention,
first-fault and exact7 typed native API policy remain. Future runtime/model
bindings, reviews, admission DATA, Root ACK and outputRoot are unissued.

All41 Source1 admission purposes remain; a real-emitted-artifact regression adds
fixture join,11-scope clock/execution and stale266-authority cases are added.
Development42 passed with mocks/metadata only; it is not canonical admission DATA. The preserved actualSource1 coverage mismatch is reproduced by unchangedvalidator; inheritedselfcoverage is explicitly historical and newself is reserved onlyfor newmanifest.
Fresh independent Source review, admission42 MODEL5 DATA/reviews, concrete full
input/actor/request review and actual one-use ACK must precede fresh286 capture.
No controller_model_metadata/R10 modification or oldhelper result relabelling.
E02 stays PARTIAL22; all five blockers, SDK/deployment/merge restrictions remain.
''')
    archive=[]
    for i,path in enumerate([p for p in sorted(mem) if p.is_relative_to(CAP)]+[OUT/'render_ready.py',OUT/'request_preflight.py',OUT/'input_authority.py',OUT/'invariance-and-delta.json',OUT/'source.diff'],1):
        copied=put(OUT/'source-archive'/('%03d-'%i+path.name),mem[path]);archive.append(dict(original=p(path),copy=copied))
    entry=put(OUT/'review-entrypoint.json',dict(schema='e02-current-producer-capture-source-review-entrypoint-v1',author=ACTOR,state='FROZEN_SOURCE_ONLY_PENDING_FRESH_INDEPENDENT_QA_SECURITY',rootScope=p(S2_SCOPE),producerSource=a['producerSource'],producerSourceAcceptance=a['producerAcceptance'],producerLineage=a['lineage'],knownActors=a['knownActors'],clockSelection=a['clock'],requestPolicy=a['requestPolicy'],codeSubject=method,expectedInputAuthority=authority,inputManifest=manifest,executionPlan=plan,admissionPlan=admission,actualInputCount=len(seen),retainedRows=2169,allPrevious2392RowsRetained=True,addedRows=len(additional),admissionDefinitions=42,admissionExecuted=0,producerDefinitions=286,producerExecuted=0,requestContract=request,unissuedAck=ack_pin,readinessRenderer=p(OUT/'render_ready.py'),requestPreflight=p(OUT/'request_preflight.py'),diff=diff_pin,invariance=delta,copies=archive,developmentEvidence=development,emittedArtifactRegression=artifact_report,sourceReady=False,runtimeReady=False,executionAuthorized=False,captureSourceAcceptance=None,admissionDataAcceptance=None,concreteRootAck=None,operationalOutputRoot=None,helperExecutions=0,ordinaryRoleExecutions=0,wholeInputQualified=False,selfApproval=False,manifestPinnedExternally=True,canonicalE02='PARTIAL22_UNCHANGED'))
    need(len(seen)<=20000 and len(mem)<=100 and sum(map(len,mem.values()))<=16777216,'FINITE_SOURCE_PACKET')
    if development_only:
        devroot=OUT/'development-candidate';need(not devroot.exists(),'ONE_DEVELOPMENT_CANDIDATE')
        for path,b in mem.items():
            dest=devroot/path.relative_to(OUT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);dest.chmod(0o600)
        (devroot/'DEVELOPMENT_ONLY.json').write_bytes(encoded(dict(schema='e02-capture-development-only-v1',sourceAccepted=False,canonicalDataAccepted=False,executionAuthorized=False,actualEmittedArtifactChecks=artifact_result)))
        print(json.dumps(dict(developmentRoot=str(devroot),admissionDefined=len(case_names),artifactRegression=artifact_result,targetScopesExecuted=0,sourceFrozen=False),sort_keys=True))
        return
    # Complete all derivation and collision checks before the first final write.
    for path in mem:need(not path.exists() and not path.is_symlink(),'NO_SOURCE_OVERWRITE')
    for path,b in mem.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:need(f.write(b)==len(b),'EXACT_SOURCE_WRITE')
    fixed=[p for p in OUT.rglob('*') if p.is_file()]
    packet=dict(schema='e02-current-capture-source-packet-manifest-v1',entrypoint=entry,files=[descriptor(p) for p in sorted(fixed)],actualFilesExcludingManifest=len(fixed),sourceOnly=True,operationalCopies=0,executionAuthorized=False)
    final=OUT/'archive-manifest.json'
    with final.open('xb') as f:f.write(encoded(packet))
    print(json.dumps(dict(entrypoint=entry,codeSubject=method,inputAuthority=authority,inputManifest=manifest,manifest=descriptor(final),actualInputCount=len(seen),admissionDefined=42,targetDefined=286,sourceReady=False,modelsExecuted=0),sort_keys=True))

if __name__=='__main__':main()
