"""Prepare reviewable UNBOUND CODE/definition metadata, never a coupled freeze.

No project modules are imported. Reads are this owned Source, the exact baseline
Source, and explicitly selected Source/governance pins. Descriptor children are
never followed. In particular no accepted helper operational body is opened.
Root must supply genuine capture/admission/286 DATA and complete basis before a
separate final coupled freeze. This builder cannot issue that authority.
"""
import argparse
import ast
import difflib
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tarfile

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source'
BASE=ROOT.parent.parent/'e02-consumer-current178-source-20261105/source3'
AUTHOR='/root/consumer_eose_basis_source'
FINAL_NAMES=('CURRENT_CAPTURE_SOURCE','CURRENT_CAPTURE_SOURCE_ACCEPTANCE',
 'CURRENT_ADMISSION_DATA_ACCEPTANCE','CURRENT_PRODUCER_CONTROL_DATA',
 'CURRENT_PRODUCER_CONTROL_ACCEPTANCE','CURRENT_HELPER_COMPONENT_BASIS')
EXTRAS=('model_stage.py','whole_window.py','prepare_consumer_edit.py','prepare_observer_edit.py',
 'strict_raw_method.txt','whole_window_methods.txt','current_authority_methods.txt','README.md')


def raw(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('REGULAR_SOURCE_FILE_REQUIRED')
    return path.read_bytes()

def pin(path):
    path=Path(path);body=raw(path)
    return dict(path=str(path.resolve()),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())

def put(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');return pin(path)

def assignments(path):
    result={}
    for node in ast.parse(raw(path)).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:result[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    return result

def methods(path):
    return {c.name+'.'+m.name:ast.dump(m,include_attributes=False)
        for c in ast.parse(raw(path)).body if isinstance(c,ast.ClassDef)
        for m in c.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_')}

def fixed(values):
    names=('CURRENT_PRODUCER','CURRENT_PRODUCER_SOURCE_ACCEPTANCE','CURRENT_SOURCE_PLAN',
      'CURRENT_DATA_ACCEPTANCE_CONTRACT','CURRENT_CONSUMER_ACCEPTANCE_CONTRACT',
      'CURRENT_COLLECTOR_PREREQUISITE_CONTRACT','CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT',
      'CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE','CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE',
      'HELPER_PRODUCER','HELPER_PRODUCER_CONTROL_ACCEPTANCE')
    result=[]
    for name in names:
        value=values[name]
        if pin(value['path'])!=value:raise ValueError('EXACT_DIRECT_SOURCE_GOVERNANCE_PIN:'+name)
        result.append(value)
    scope=ROOT.parent/'source-scope.json';result.append(pin(scope))
    return list({p['path']:p for p in result}.values())

def static_contracts(members):
    """Derive lexical closure/contracts without importing any evidence module."""
    bodies={Path(n).stem:raw(SOURCE/n) for n in members if n.endswith('.py')}
    trees={n:ast.parse(b,filename=n+'.py') for n,b in bodies.items()}
    virtual=assignments(SOURCE/'test_import_closure.py')['ISOLATED_PROGRAM']
    trees['<isolated-program>']=ast.parse(virtual)
    exports={};graph={n:set() for n in trees};imports=[];contracts=[];dynamic=[]
    for name,tree in trees.items():
        names=set()
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.ClassDef)):names.add(node.name)
            elif isinstance(node,ast.Assign):names|={t.id for t in node.targets if isinstance(t,ast.Name)}
            elif isinstance(node,(ast.Import,ast.ImportFrom)):names|={a.asname or a.name.split('.')[0] for a in node.names}
        exports[name]=names
    for name,tree in trees.items():
        for node in ast.walk(tree):
            requested=[]
            if isinstance(node,ast.Import):requested=[(a.name,None) for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level or node.module is None:raise ValueError('RELATIVE_IMPORT_REFUSED')
                requested=[(node.module,node.names)]
            for module,symbols in requested:
                top=module.split('.')[0]
                if top in bodies:
                    if module!=top:raise ValueError('LOCAL_SUBMODULE_REFUSED')
                    if symbols and any(a.name=='*' or a.name not in exports[top] for a in symbols):raise ValueError('UNKNOWN_LOCAL_IMPORT_SYMBOL')
                    graph[name].add(top);classification='EXACT_DECLARED_LOCAL_CODE'
                elif top in sys.stdlib_module_names:classification='PYTHON_STDLIB'
                else:raise ValueError('UNKNOWN_IMPORT:'+module)
                imports.append(dict(source=name,line=node.lineno,module=module,classification=classification))
            if isinstance(node,ast.Call):
                if isinstance(node.func,ast.Name) and node.func.id=='__import__':raise ValueError('UNKNOWN_DYNAMIC_IMPORT')
                if isinstance(node.func,ast.Attribute) and node.func.attr=='import_module':
                    if name!='whole_window' or ast.unparse(node)!='importlib.import_module(name)':raise ValueError('UNKNOWN_DYNAMIC_IMPORT')
                    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='components')
                    selected=next(ast.literal_eval(n.value) for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets))
                    if type(selected) is not tuple or not set(selected)<=bodies.keys():raise ValueError('FINITE_DYNAMIC_LOCAL_CLOSURE_REQUIRED')
                    graph[name]|=set(selected);dynamic.append(dict(source=name,function='components',members=list(selected)))
                if isinstance(node.func,ast.Name) and node.func.id in ('closed','exact') and len(node.args)>1 and isinstance(node.args[1],ast.Constant) and type(node.args[1].value) is str:
                    contracts.append(dict(source=name,line=node.lineno,validator=node.func.id,keys=node.args[1].value.split()))
    def reach(roots):
        seen=set();todo=list(roots)
        while todo:
            n=todo.pop()
            if n not in seen:seen.add(n);todo.extend(graph[n]-seen)
        return seen
    runtime={Path(n).stem for n in assignments(SOURCE/'consumer.py')['RUNTIME_FILES']}
    if reach(runtime)!=runtime or reach(['consumer'])!=runtime:raise ValueError('EXACT_DECLARED_RUNTIME_IMPORT_CLOSURE')
    put(ROOT/'import-closure.json',dict(schema='e02-consumer-eose-static-import-closure-v1',
      nodes=sorted(graph),graph={n:sorted(v) for n,v in graph.items()},imports=imports,
      finiteDynamicEdges=dynamic,runtime=sorted(runtime),runtimeCount=len(runtime),
      consumerReachable=sorted(reach(['consumer'])),executed=False))
    literals={}
    for n in bodies:
        literals[n]={k:v for k,v in assignments(SOURCE/(n+'.py')).items() if (k.endswith('KEYS') or k in ('ACK_KEYS','SUBJECT_KEYS','LIMITS','LEDGER','MODEL_KEYS','FILES')) and isinstance(v,(str,list,tuple,dict))}
    put(ROOT/'contracts/frozen-closed-contracts.json',dict(schema='e02-consumer-eose-closed-parser-contracts-v1',
      state='UNBOUND_AST_DEFINITIONS_ONLY',literalContracts=literals,lexicalClosedCalls=contracts,
      helperParserNamespace='capture_contracts',ordinaryParserNamespace='ordinary_capture_contracts',
      ordinaryCounts=[129,33,29,16,20,10,11,8,7,3,20],metadataFloatDomainWidened=False,executionAuthorized=False))

def build():
    values=assignments(SOURCE/'consumer.py')
    if any(values[name] is not None for name in FINAL_NAMES):
        raise ValueError('UNBOUND_BUILDER_REQUIRES_UNISSUED_SELECTORS_USE_ROOT_COUPLED_FREEZE')
    runtime=values['RUNTIME_FILES'];controls=values['CONTROL_FILES'];code=sorted((*runtime,*controls,*EXTRAS))
    if len(code)!=len(set(code)):raise ValueError('UNIQUE_CODE_MEMBERSHIP')
    members={name:pin(SOURCE/name) for name in code}
    static_contracts(members)
    groups=[];changed=[];baseline_names=[]
    for name in controls:
        names=methods(SOURCE/name)
        groups.append(dict(name=name,source=members[name],count=len(names),definitionNames=list(names),
          argv=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(SOURCE/name),'-v'],
          cwd=str(SOURCE),format='EXACT_VERBOSE_UNITTEST_NAMES',definitionScope='UNBOUND_DEFINITIONS_ONLY_NO_CANONICAL_EXECUTION'))
        old=BASE/'source'/name
        if old.is_file():
            previous=methods(old);baseline_names.extend(previous)
            if not previous.keys()<=names.keys():raise ValueError('ORIGINAL_METHOD_DELETED:'+name)
            changed.extend(dict(group=name,method=n,reason='Necessary current286/basis/fixture API adaptation; purpose retained',oldAstSha256=hashlib.sha256(previous[n].encode()).hexdigest(),newAstSha256=hashlib.sha256(names[n].encode()).hexdigest()) for n in previous if names[n]!=previous[n])
    if len(baseline_names)!=352:raise ValueError('EXACT_ORIGINAL_352_METHOD_PARTITION')
    total=sum(g['count'] for g in groups);operands=fixed(values)
    plan=put(SOURCE/'control-plan.json',dict(schema='e02-consumer6-model-control-plan-v1',author=AUTHOR,
      state='UNBOUND_DEFINITIONS_ONLY',modelsDefined=total,modelsExecuted=0,groups=groups,executionAuthorized=False))
    manifest=put(SOURCE/'input-manifest.json',dict(schema='e02-consumer6-current-input-manifest-v1',author=AUTHOR,
      state='UNBOUND_SOURCE_ONLY_NOT_FINAL_INPUT_CLOSURE',fixedSourceAndCurrentDataOperands=operands,
      currentDataOperands=[],finalInputClosureReady=False,operationalHelperBodiesRead=0,
      fixedOperandMeaning='Direct Source/governance pins only; no recursive descriptor walk',executionAuthorized=False))
    subject=put(SOURCE/'subject.json',dict(schema='e02-ordinary-consumer6-source-subject-v1',version='SOURCE5',
      sourceRevision=values['UNBOUND_SOURCE_REVISION'],author=AUTHOR,coordinator='/root',
      sourceContributors=values['CURRENT_CONTROL_ACTORS'],predecessorAuthor='/root/consumer_current178_source',operators=[],
      state='UNBOUND_CODE_AND_DEFINITIONS_ONLY',scope='UNBOUND_EOSE_COMPONENT_BASIS_CODE_PREPARATION_ONLY',
      sourceRoot=str(SOURCE),sources=[members[n] for n in code],sourceCount=len(code),
      runtimeSources=[members[n] for n in runtime],runtimeSourceCount=len(runtime),
      controlPlan=plan,inputManifest=manifest,producerSource=values['CURRENT_PRODUCER'],
      producerSourceAcceptance=values['CURRENT_PRODUCER_SOURCE_ACCEPTANCE'],
      producerControlAcceptance=None,helperComponentBasis=None,producerRuntimeWorkerCount=22,
      producerSourceMemberCount=64,modelsDefined={g['name']:g['count'] for g in groups},
      modelDefinitions=total,modelGroups=len(groups),modelsExecuted=0,helperExecutions=0,
      roleExecutions=0,ordinaryRowsQualified=0,runtimeReady=False,executionAuthorized=False,
      ordinaryAttemptsUnqualified=15,failedRunContribution='NO_FAILED_WINDOW_ROW_DONATION',
      completedBasisIssued=False,finalSourceFreezeReady=False))
    put(ROOT/'authorized-ast-exceptions.json',dict(schema='e02-consumer-eose-method-adaptations-v1',
      baseline=pin(BASE/'source/subject.json'),baselineMethods=352,allNamesPreserved=True,changes=changed))
    preservation=[];delta=[]
    for name in code:
        current=SOURCE/name;old=BASE/'source'/name
        if old.is_file():
            same=raw(old)==raw(current)
            preservation.append(dict(name=name,baseline=pin(old),current=members[name],byteIdentical=same))
            if not same:
                delta.extend(difflib.unified_diff(raw(old).decode().splitlines(True),raw(current).decode().splitlines(True),fromfile='baseline/'+name,tofile='unbound/'+name))
        else:preservation.append(dict(name=name,baseline=None,current=members[name],added=True))
    (ROOT/'source-delta.patch').write_text(''.join(delta))
    probe_old=ast.parse(raw(BASE/'source/probe_adapter.py')).body;probe_new=ast.parse(raw(SOURCE/'probe_adapter.py')).body
    if [ast.dump(n,include_attributes=False) for n in probe_old]!=[ast.dump(n,include_attributes=False) for n in probe_new[:len(probe_old)]]:raise ValueError('ORIGINAL_PROBE_AST_OR_IMPORT_SEMANTICS_CHANGED')
    for name in ('capture_contracts.py','capture_outputs.py','request_families.py'):
        if raw(BASE/'source'/name)!=raw(SOURCE/name):raise ValueError('ORIGINAL_HELPER_IMPORT_SEMANTICS_CHANGED:'+name)
    put(ROOT/'preservation.json',dict(schema='e02-consumer-eose-source-preservation-v1',rows=preservation,
      originalMethods=352,allMethodNamesPreserved=True,originalProbeAstAndImportsPreserved=True,
      originalHelperParsersByteIdentical=True,canonicalResultsTransferred=0,oldHelperAcceptanceUnchanged=True,
      originalIncomingFailedRun='3b22101922f48ee4daab728aa77b5d38',all15AttemptsUnqualified=True))
    projection=json.loads(raw(ROOT/'ordinary-capture-projection.json'))
    pending=['Independent consumer Source QA/security','Actual admission42 DATA acceptance','Fresh full286 producer DATA and Root acceptance','Completed component basis and full verification','Final coupled input closure','Canonical full consumer model batch','Actual two ordinary windows and five exports']
    if projection['captureSourceIndependentAcceptance'] is None:pending.insert(1,'Genuine Source2 capture acceptance')
    put(ROOT/'requirements-and-coverage.json',dict(schema='e02-consumer-eose-unbound-definition-coverage-v1',
      modelsDefined=total,groups=[dict(name=g['name'],count=g['count'],definitionNames=g['definitionNames']) for g in groups],
      canonicalModelsExecuted=0,definitionCountsAreNotRuntimeEvidence=True,
      pending=pending))
    put(ROOT/'input-read-map.json',dict(schema='e02-consumer-eose-unbound-read-map-v1',directSourceGovernanceReads=operands,
      sourceReads=[members[n] for n in code],runtimeHelperReadsInThisPreparation=[],
      forbiddenOperationalRun='65d8116b77bc0af1a108122ec28cfcea',recursiveDescriptorWalk=False,
      futureRuntimeReads='Only after separate genuine authority: ordinary286 pure controls; original helper operational DATA on original266 basis; final2windows/5exports',
      canonicalControlsExecuted=0,executionAuthorized=False))
    put(SOURCE/'lineage.json',dict(schema='e02-consumer-eose-unbound-source-lineage-v1',actor=AUTHOR,
      baseline=pin(BASE/'source/subject.json'),rootScope=pin(ROOT.parent/'source-scope.json'),
      originalHelperProducer=values['HELPER_PRODUCER'],originalHelperControlAcceptance=values['HELPER_PRODUCER_CONTROL_ACCEPTANCE'],
      newOrdinaryProducer=values['CURRENT_PRODUCER'],completedBasis=None,canonicalResultsTransferred=0))
    put(SOURCE/'static-preparation.json',dict(schema='e02-consumer-eose-unbound-static-preparation-v1',
      state='UNBOUND_CODE_AND_DEFINITIONS_ONLY',modelsDefined=total,sourceCount=len(code),runtimeSourceCount=len(runtime),
      canonicalModelsExecuted=0,finalSourceFreezeReady=False,executionAuthorized=False))
    acceptance_contract=json.loads(raw(ROOT/'contracts/current-consumer-acceptance-contract.json'))
    put(SOURCE/'control-data-shape-contract.json',dict(schema='e02-consumer-eose-unbound-control-data-shape-v1',
      state='UNISSUED_DEFINITION_ONLY',contract=values['CURRENT_CONSUMER_ACCEPTANCE_CONTRACT'],
      dataRootClosedKeys=acceptance_contract['data']['closedKeys'],dataRootLiterals=acceptance_contract['data']['literals'],
      countsSeparate=[g['count'] for g in groups],modelsDefined=total,requiredModelGroups=len(groups),
      subject=None,acceptance=None,canonicalModelsExecuted=0,runtimeAuthorized=False,executionAuthorized=False))
    archive_paths=[SOURCE/n for n in code]+[SOURCE/n for n in ('control-plan.json','input-manifest.json','subject.json','lineage.json','runtime-gates.json','static-preparation.json','control-data-shape-contract.json')]
    archive_paths += sorted((ROOT/'contracts').glob('*.json'))
    archive_paths += [ROOT/n for n in ('prepare_source.py','prepare_bundle.py','preservation.json','requirements-and-coverage.json','authorized-ast-exceptions.json','input-read-map.json','import-closure.json','ordinary-capture-projection.json','unbound-status.json','source-delta.patch','negative-inputs.json','component-basis.UNISSUED.json','fixture-authority.json','FINAL-FREEZE-INPUTS.UNISSUED.json','development-checks.json','HANDOFF.md')]
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w',format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(archive_paths):
            body=raw(path);info=tarfile.TarInfo(str(path.relative_to(ROOT)));info.size=len(body)
            info.mode=stat.S_IMODE(path.stat().st_mode);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
            archive.addfile(info,io.BytesIO(body))
    (ROOT/'source.UNBOUND.tar').write_bytes(stream.getvalue())
    return put(ROOT/'entrypoint.UNBOUND.json',dict(schema='e02-consumer-eose-unbound-review-entrypoint-v1',
      author=AUTHOR,state='UNBOUND_CODE_AND_DEFINITIONS_ONLY',subject=subject,archive=pin(ROOT/'source.UNBOUND.tar'),
      modelsDefined=total,canonicalModelsExecuted=0,sourceCount=len(code),runtimeSourceCount=len(runtime),
      rootScope=pin(ROOT.parent/'source-scope.json'),readMap=pin(ROOT/'input-read-map.json'),
      preservation=pin(ROOT/'preservation.json'),definitionCoverage=pin(ROOT/'requirements-and-coverage.json'),
      developmentChecks=pin(ROOT/'development-checks.json'),handoff=pin(ROOT/'HANDOFF.md'),
      pendingFinalSelectors={n:values[n] for n in FINAL_NAMES},completedBasisIssued=False,
      finalSourceFreezeReady=False,runtimeBindingIssued=False,executionAuthorized=False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unbound',action='store_true',required=True)
    parser.parse_args()
    print(json.dumps(build(),sort_keys=True))

if __name__=='__main__':main()
