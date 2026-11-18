"""SOURCE metadata/AST/archive preparation only; never imports target code."""
import ast
import difflib
import hashlib
import io
import json
from pathlib import Path
import tarfile

OWNED=Path(__file__).resolve().parent
SOURCE=OWNED/'source'
REPO=Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE=REPO/'docs/decisions/evidence'
BASE=EVIDENCE/'e02-consumer266-source-preparation-20261104/r2/source'
SCOPE_PATH=EVIDENCE/'e02-goal-resume-20261104/consumer-current178-root-scope-20261105.json'
SCOPE=json.loads(SCOPE_PATH.read_bytes());TUPLE=SCOPE['currentTuple']
ACTOR='/root/consumer_current178_source'


def pin(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n');return pin(path)


def doc(p):
    return json.loads(Path(p['path'] if isinstance(p,dict) else p).read_bytes())


def methods(p):
    tree=ast.parse(p.read_bytes(),filename=str(p))
    return {c.name+'.'+m.name:ast.dump(m,include_attributes=False) for c in tree.body if isinstance(c,ast.ClassDef)
            for m in c.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_')}


def assignments(p):
    tree=ast.parse(p.read_bytes());out={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            try:out[n.targets[0].id]=ast.literal_eval(n.value)
            except (ValueError,TypeError):pass
    return out


def fixed_inputs(constants,code_pins):
    rows={};uses={}
    def add(p,selector):
        assert type(p) is dict and set(p)=={'path','bytes','sha256'},(selector,p)
        assert p['path'].startswith('/') and type(p['bytes']) is int
        if p['path'] in rows:assert rows[p['path']]==p,('CONFLICTING_EXPECTED_PIN',p['path'])
        rows[p['path']]=p;uses.setdefault(p['path'],[]).append(selector)
    def fields(value,keys,selector):
        for k in keys:add(value[k],selector+'/'+k)
    def reviews(p,selector):
        d=doc(p)
        for i,x in enumerate(d.get('reviews',[])):add(x,selector+'/reviews/'+str(i))
    # Finite historical inputs remain explicit because preserved negative/old
    # fixture definitions still reference them. No arbitrary descriptor walk.
    old=doc(BASE/'input-manifest.json')
    for i,p in enumerate(old['fixedSourceAndCurrentDataOperands']):add(p,'baseline/input-manifest/fixedSourceAndCurrentDataOperands/'+str(i))
    for name,value in constants.items():
        if name.startswith(('CURRENT_','HISTORICAL_')) and type(value) is dict and set(value)=={'path','bytes','sha256'}:
            if name not in ('CURRENT_NATIVE','CURRENT_AMETHYST_APK','CURRENT_HELPER_APK'):add(value,'consumer.py/'+name)
    for key in ('producerSource','producerSourceAcceptance','producerData','producerDataAcceptance','producerCaptureSource',
                'producerCaptureSourceAcceptance','producerAdmissionDataAcceptance','producerOriginalToolOrigin','producerRawArtifactManifest',
                'controllerSource','controllerSourceAcceptance','controllerControlPlan','controllerData','controllerDataAcceptance',
                'controllerDataRawManifest','controllerDataBefore','controllerDataAfter','collectorSource','collectorSourceAcceptance',
                'collectorData','collectorDataAcceptance','operationalCollector','operationalQualifier','historyPrefix','losslessCollectorCodec',
                'strictMetadataMethod','strictMetadataMethodSource','strictMetadataMethodAcceptance','host7Policy','host7Skeleton'):
        add(TUPLE[key],'rootScope/currentTuple/'+key)
    for key in ('producerSource','controllerSource','collectorSource'):
        obj=doc(TUPLE[key])
        for i,p in enumerate(obj['sources']):add(p,key+'/sources/'+str(i))
    producer=doc(TUPLE['producerSource']);bindings=doc(constants['CURRENT_ARTIFACT_BINDINGS'])
    fields(bindings,['amethystAcceptance','amethystProvenance','helperAcceptance','helperProvenance',
                     'nativeBuildAcceptance','acceptedE01','acceptedE01Acceptance'],'currentArtifactBindings')
    for key in ('producerSourceAcceptance','producerDataAcceptance','producerCaptureSourceAcceptance',
                'producerAdmissionDataAcceptance','controllerSourceAcceptance','controllerDataAcceptance',
                'collectorSourceAcceptance','collectorDataAcceptance'):reviews(TUPLE[key],key)
    # Current producer metadata read closure: only these source-level selectors.
    data=doc(TUPLE['producerData'])
    fields(data,['plan','inputManifest','rootAcknowledgement','execution','originalToolOrigin','rawArtifactManifest'],'producerData')
    ack=doc(data['rootAcknowledgement'])
    fields(ack,'producerSource producerSourceAcceptance captureSource captureSourceAcceptance admissionPlan admissionData admissionDataAcceptance sourceBirth actorContext inputManifest plan clockSelection requestContract runtimeBindings'.split(),'producerAck')
    for k in ('producerReviews','captureReviews','admissionReviews'):
        for i,p in enumerate(ack[k]):add(p,'producerAck/'+k+'/'+str(i))
    context=doc(ack['actorContext'])
    for i,x in enumerate(context['participantProofs']):add(x['authority'],'producerActorContext/participantProofs/'+str(i)+'/authority')
    admission=doc(ack['admissionData'])
    fields(admission,['execution','originalToolOrigin','rawArtifactManifest','inputsBefore','inputsAfter'],'producerAdmissionData')
    capture_constants=assignments(SOURCE/'capture_contracts.py')
    add(capture_constants['ROOT_KNOWN_ACTORS_PIN'],'capture_contracts.py/ROOT_KNOWN_ACTORS_PIN')
    raw=doc(data['rawArtifactManifest']);add(raw['runtimeManifest'],'producerRaw/runtimeManifest')
    for i,p in enumerate(raw['files']):add(p,'producerRaw/files/'+str(i))
    # Snapshots contain expected external SDK/APK/native hashes; those payloads
    # are deliberately not followed/rehashed by this Source or future readers.
    for key in ('controllerData','collectorData'):
        d=doc(TUPLE[key]);fields(d,['execution','rawArtifactManifest','inputsBefore','inputsAfter'],'currentTuple/'+key)
        raw=doc(d['rawArtifactManifest'])
        for i,p in enumerate(raw['files']):add(p,key+'/rawManifest/files/'+str(i))
    for i,p in enumerate(TUPLE['controllerDataOriginalToolOrigins']):add(p,'controllerDataOriginalToolOrigins/'+str(i))
    add(pin(OWNED/'current-inputs.json'),'test_request_families/current-inputs.json')
    add(pin(SCOPE_PATH),'preparation/rootScope');add(SCOPE['requestFamilyAuthority'],'preparation/requestFamilyAuthority');add(SCOPE['bindingMap'],'preparation/bindingMap')
    for path,p in rows.items():
        assert pin(path)==p,('DECLARED_METADATA_PIN_DRIFT',path)
    return [rows[k] for k in sorted(rows)],[dict(pin=rows[k],selectors=sorted(set(uses[k]))) for k in sorted(rows)]


def main():
    assert pin(SCOPE_PATH)['sha256']=='101ad3f34c69eaffcc0f1c5f6a9af876bdae45ffc40ef4f4d0aaf65b52db75c2'
    constants=assignments(SOURCE/'consumer.py');runtime=list(constants['RUNTIME_FILES']);controls=list(constants['CONTROL_FILES'])
    code=sorted(runtime+controls+['model_stage.py','whole_window.py','prepare_consumer_edit.py','prepare_observer_edit.py',
                                'strict_raw_method.txt','whole_window_methods.txt','current_authority_methods.txt','README.md'])
    assert len(code)==len(set(code))
    # README is a frozen CODE member; it describes the actual successor.
    (SOURCE/'README.md').write_text('''# Current178 consumer SOURCE preparation

This successor reads the accepted current producer266/capture33, controller
R10/178 and typed Collector Source2/81 prerequisite tuples. Helper DATA,
helper Root24, consumer DATA24 and ordinary role/export authorities remain
unissued. Runtime binding cannot override the exact current frozen CODE.

Four origin readers explicitly select PRODUCER_CAPTURE7, HOST7, COLLECTOR7
or MODEL5. Whole typed requests, exact policy strings, argv/cwd, native
responses and identity are retained. MODEL5 optional token metadata never
changes operational Collector7's required native counter.

All original business/role/replay/lifecycle/budget/five-export predicates and
315 original definition names remain. Old R8/R5 fixture variable/test names
remain for preservation; the positive CURRENT_R8_FIXTURE now explicitly loads
the accepted current R10/178 tuple. Historical R5 remains a negative fixture.

The parent entrypoint pins the actual AST-derived inventory and requirements.
This is unexecuted Source. Independent post-freeze QA/security, Root Source
acceptance and a separate release must precede any full current model run.
No helper or ordinary runtime authorization follows from this preparation.
''')
    code_pins=[pin(SOURCE/n) for n in code]
    groups=[];old_names=[];added=[];changed=[];all_names=[]
    for name in controls:
        actual=methods(SOURCE/name);previous=methods(BASE/name) if (BASE/name).exists() else {}
        assert set(previous)<=set(actual),(name,'LOST_OLD_METHOD')
        old_names.extend(name+':'+n for n in previous)
        added.extend(name+':'+n for n in actual if n not in previous)
        changed.extend(name+':'+n for n in previous if previous[n]!=actual[n])
        names=list(actual);all_names.extend(name+':'+n for n in names)
        groups.append(dict(name=name,source=pin(SOURCE/name),count=len(names),definitionNames=names,
            argv=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(SOURCE/name),'-v'],cwd=str(SOURCE),
            format='EXACT_VERBOSE_UNITTEST_NAMES',definitionScope='SYNTHETIC_OR_READ_ONLY_DATA_ONLY_NO_TARGET_RUNTIME'))
    assert len(old_names)==315 and len(all_names)==len(set(all_names))
    total=sum(g['count'] for g in groups)
    for p in SOURCE.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
    plan=doc(BASE/'control-plan.json');plan.update(author=ACTOR,groups=groups,modelsDefined=total,modelsExecuted=0,
        testRevision='SOURCE4-CURRENT178-EXPLICIT-FOUR-FAMILY-SOURCE1',
        actualDataPrerequisiteRead='Retained accepted current producer266, R10/178, typed Collector Source2/81 metadata/proof only. No producer/helper/collector command rerun.')
    plan_pin=put(SOURCE/'control-plan.json',plan)
    # The existing closed Source15/Data24 formats are read directly from the
    # current frozen code/contract; counts are derived, never copied from 315.
    acceptance=doc(constants['CURRENT_CONSUMER_ACCEPTANCE_CONTRACT'])
    shape=doc(BASE/'control-data-shape-contract.json')
    for code_key,shape_key in [('CONTROL_DATA_KEYS','dataSubjectClosedKeys'),('CONTROL_EXECUTION_KEYS','executionClosedKeys'),('CONTROL_GROUP_KEYS','orderedGroupClosedKeys')]:
        assert set(constants[code_key].split())==set(shape[shape_key])
    closed=put(OWNED/'contracts/frozen-closed-contracts.json',dict(schema='e02-consumer-current178-derived-closed-contracts-v1',actor=ACTOR,
        derivation='stdlib AST literal extraction and exact contract lists; no target import',
        sourceAcceptanceClosedKeys=acceptance['source']['closedKeys'],sourceAcceptanceKeyCount=len(acceptance['source']['closedKeys']),
        dataAcceptanceClosedKeys=acceptance['data']['closedKeys'],dataAcceptanceKeyCount=len(acceptance['data']['closedKeys']),
        sourceAcceptanceLiterals=acceptance['source']['literals'],dataAcceptanceLiterals=acceptance['data']['literals'],
        runtimeBindingsClosedKeys=constants['BINDING_KEYS'].split(),dataSubjectClosedKeys=constants['CONTROL_DATA_KEYS'].split(),
        executionClosedKeys=constants['CONTROL_EXECUTION_KEYS'].split(),groupClosedKeys=constants['CONTROL_GROUP_KEYS'].split(),
        currentModelsDefined=total,countsSeparate=[g['count'] for g in groups],executionAuthorized=False))
    runtime_gates=doc(BASE/'runtime-gates.json')
    for key,name in [('producerSource','CURRENT_PRODUCER'),('producerSourceAcceptance','CURRENT_PRODUCER_SOURCE_ACCEPTANCE'),
                     ('producerControlData','CURRENT_PRODUCER_CONTROL_DATA'),('producerControlAcceptance','CURRENT_PRODUCER_CONTROL_ACCEPTANCE')]:runtime_gates[key]=constants[name]
    gate_pin=put(SOURCE/'runtime-gates.json',runtime_gates)
    inputs,readmap=fixed_inputs(constants,code_pins)
    input_pin=put(SOURCE/'input-manifest.json',dict(schema='e02-consumer6-explicit-source-input-manifest-v1',author=ACTOR,
        ownCodeAndModelSources=code_pins,fixedSourceAndCurrentDataOperands=inputs,selectedMutableModelLeaf=gate_pin,
        fixtureMeaning='Current positive R10/178 and typed Collector Source2/81 are retained accepted metadata; synthetic surrounding helper/consumer records do not create actual helper or runtime approval. Historical negative fixtures are explicitly retained.',
        scope='EXPLICIT_CODE_AND_RETAINED_METADATA_ONLY_NO_SDK_APK_NATIVE_OR_GUARD_WALKS',newActualInputRehashClaimed=False,executionAuthorized=False))
    readmap_pin=put(OWNED/'input-read-map.json',dict(schema='e02-consumer-current178-finite-typed-input-read-map-v1',actor=ACTOR,
        rootScope=pin(SCOPE_PATH),rows=readmap,finiteFullPaths=[x['pin']['path'] for x in readmap],count=len(readmap),
        selectorPolicy='Only explicitly named fields/arrays in the recorded reader; no recursive descriptor discovery.',
        forbiddenPayloadWalks=['SDK','APK','native binary','guard trees'],
        snapshotMeaning='Expected hashes/membership remain retained historical custody facts, not fresh external rehash or race-free claim.',executionAuthorized=False))
    (OWNED/'diffs').mkdir(exist_ok=True)
    diff_rows=[];same=[];members_changed=[]
    for name in code:
        p=SOURCE/name;old=BASE/name
        if old.exists() and old.read_bytes()==p.read_bytes():same.append(name)
        else:members_changed.append(name)
        diff=''.join(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],p.read_text().splitlines(True),fromfile=str(old),tofile=str(p)))
        dpath=OWNED/'diffs'/(name+'.diff');dpath.write_text(diff)
        diff_rows.append(dict(name=name,before=pin(old) if old.exists() else None,after=pin(p),diff=pin(dpath)))
    diff_pin=put(OWNED/'source-diff.json',dict(schema='e02-consumer-current178-full-source-diff-v1',actor=ACTOR,
        baseline=SCOPE['baseline'],members=diff_rows,changedMembers=members_changed,byteIdenticalMembers=same))
    preservation=put(OWNED/'preservation.json',dict(schema='e02-consumer-current178-preservation-v1',actor=ACTOR,
        baseline=SCOPE['baseline'],baselineSourceAcceptance=SCOPE['baselineSourceAcceptance'],oldDefinitionNames=old_names,
        preservedNames=len(old_names),newDefinitionNames=added,changedOriginalMethodAST=changed,
        legitimateFixtureChanges=['test_source_bindings.py: current actual266/Root91a0 expected literal pins',
           'test_current_authority.py: exact currentR10/178 positive fixture tuple and AST-derived runtime count; old CURRENT_R8_FIXTURE name retained',
           'Helper Root24 editorial minimum-join text successor retains identical closed keys/literals/decisions'],
        unchangedBusinessCode=['wire.py','gui.py','witness.py','observer.py','async_guard.py','parent_allocation.py','strict.py','whole_window.py'],
        byteIdenticalMembers=same,modelsDefined=total,modelsExecuted=0,historical315DataTransferred=False,
        historical309DataTransferred=False,historical302DataTransferred=False,all14PriorFailures='NO_CONTRIBUTION',
        originalCriteriaPreserved=True,canonicalE02='PARTIAL22_UNCHANGED',executionAuthorized=False))
    static=put(SOURCE/'static-preparation.json',dict(schema='e02-consumer-current178-stdlib-static-inspection-v1',actor=ACTOR,
        allPythonASTParsed=True,pythonSources=[pin(p) for p in sorted(SOURCE.glob('*.py'))],
        sourceCount=len(code),runtimeSourceCount=len(runtime),controlGroups=len(groups),countsSeparate=[g['count'] for g in groups],
        modelsDefined=total,modelsExecuted=0,targetImports=0,helperExecutions=0,dockerExecutions=0,ordinaryRoleExecutions=0,
        preserved315Names=True,newDefinitions=len(added),changedOriginalMethods=changed,sourceDiff=diff_pin,preservation=preservation,
        scope='AST syntax/names/literals and immutable file pins only; no runtime interoperability claimed',executionAuthorized=False))
    lineage=put(SOURCE/'lineage.json',dict(schema='e02-consumer-current178-source-lineage-v1',author=ACTOR,
        predecessorSubject=SCOPE['baseline'],predecessorSourceAcceptance=SCOPE['baselineSourceAcceptance'],
        predecessorDisposition='ACCEPTED_SOURCE_AND_HISTORICAL315_DATA_ONLY_NO_SUCCESSOR_RESULT_TRANSFER',
        currentTuple=TUPLE,sourceDiff=diff_pin,preservation=preservation,modelsDefined=total,modelsExecuted=0,executionAuthorized=False))
    baseline=doc(BASE/'subject.json');contrib=sorted(set(baseline['sourceContributors'])|set(SCOPE['knownPrerequisiteActors'])|{ACTOR})
    exclusions=sorted(set(SCOPE['reviewerExclusions'])|set(contrib)|{'/root/root_failstop_bridge_source'})
    authors=put(OWNED/'creator-union-and-exclusions.json',dict(schema='e02-consumer-current178-source-creators-and-reviewer-exclusions-v1',actor=ACTOR,
        baselineAuthors=baseline['sourceContributors'],currentPrerequisiteCreators=SCOPE['creatorEvidence'],
        conservativeSourceContributors=contrib,rootScopeConservative38=SCOPE['reviewerExclusions'],
        additionalConservativeExclusions=sorted(set(exclusions)-set(SCOPE['reviewerExclusions'])),reviewerExclusions=exclusions,
        actualBridgeAuthor='/root/root_failstop_bridge_source',
        provenance='Actual author of this successor plus preserved/reused source/design creators; bridge author excluded conservatively, no bridge runtime imported.',
        rule='Fresh post-freeze independent QA/security cannot be any creator/operator or conservative exclusion. Root owns selection and acceptance.',selfApproval=False))
    baseline.update(author=ACTOR,coordinator='/root',sourceContributors=contrib,sourceRevision='CURRENT178_EXPLICIT_FOUR_FAMILY_SOURCE1',
        state='WRITES_STOPPED_PENDING_FRESH_INDEPENDENT_CURRENT178_SOURCE_QA_SECURITY',
        scope='CURRENT_CONSUMER_SOURCE4_CURRENT178_340_UNEXECUTED_DEFINITIONS_ONLY',sourceRoot=str(SOURCE),sources=code_pins,sourceCount=len(code),
        runtimeSources=[pin(SOURCE/n) for n in runtime],runtimeSourceCount=len(runtime),controlPlan=plan_pin,inputManifest=input_pin,
        staticPreparation=static,lineage=lineage,predecessorSubject=SCOPE['baseline'],predecessorControlDataAcceptance=None,
        producerSource=constants['CURRENT_PRODUCER'],producerSourceAcceptance=constants['CURRENT_PRODUCER_SOURCE_ACCEPTANCE'],
        producerControlData=constants['CURRENT_PRODUCER_CONTROL_DATA'],producerControlAcceptance=constants['CURRENT_PRODUCER_CONTROL_ACCEPTANCE'],
        producerExportContract=constants['CURRENT_EXPORT_CONTRACT'],producerGuardDto=constants['CURRENT_GUARD_DTO'],
        helperProbeAcceptanceContract=constants['CURRENT_HELPER_PROBE_ACCEPTANCE_CONTRACT'],helperProbeShapeContract=constants['CURRENT_HELPER_PROBE_SHAPE_CONTRACT'],
        currentConsumerAcceptanceContract=constants['CURRENT_CONSUMER_ACCEPTANCE_CONTRACT'],currentControllerAcceptanceContract=constants['CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT'],
        controlDataShapeContract=pin(SOURCE/'control-data-shape-contract.json'),modelsDefined={g['name']:g['count'] for g in groups},modelGroups=len(groups),modelDefinitions=total,
        modelsExecuted=0,runtimeReady=False,executionAuthorized=False,actualHelperProbeData=None,actualHelperProbeAcceptance=None,
        actualConsumerControlData=None,actualConsumerControlAcceptance=None,currentActualControllerTuple=None,
        currentControllerPrerequisites={k:TUPLE[k] for k in ('controllerSource','controllerSourceAcceptance','controllerData','controllerDataAcceptance')},
        collectorPrerequisiteContract=constants['CURRENT_COLLECTOR_PREREQUISITE_CONTRACT'],
        conservativeReviewerExclusions=exclusions,creatorUnion=authors,rootScope=pin(SCOPE_PATH),requestFamilyAuthority=SCOPE['requestFamilyAuthority'],
        currentReadMap=readmap_pin,derivedClosedContracts=closed,preservation=preservation,sourceDiff=diff_pin,historical315ControlsTransferred=False,
        independentSourceReviews=None,rootSourceAcceptance=None,
        declaredCurrentR8Fixture=dict(source=TUPLE['controllerSource'],sourceAcceptance=TUPLE['controllerSourceAcceptance'],controlAcceptance=TUPLE['controllerDataAcceptance']),
        remainingGates=['Fresh independent exact post-freeze Source QA/security and Root Source acceptance',
            'Separate explicit Root release for complete current AST-derived model batch, then independent DATA review/Root acceptance',
            'Accepted actual helper DATA18/Root24, current external authority leaf and full current consumer DATA24 before activation',
            'Original two ordinary role windows/five genuine exports/full consumer and separately authorized completion integration'])
    baseline['scope']='CURRENT_CONSUMER_SOURCE4_CURRENT178_'+str(total)+'_UNEXECUTED_DEFINITIONS_ONLY'
    subject=put(SOURCE/'subject.json',baseline)
    requirements=put(OWNED/'requirements-and-coverage.json',dict(schema='e02-consumer-current178-requirements-and-coverage-v1',actor=ACTOR,
        rootRequiredChanges=SCOPE['requiredChanges'],sourceSubject=subject,controlPlan=plan_pin,
        originalDefinitionNamesPreserved=315,newDefinitions=added,actualModelDefinitions=total,
        actualReaders=['consumer.current_producer','current_controls.validate_data','probe_adapter.validate_controller_authority',
            'probe_adapter.validate_collector_authority','probe_adapter.validate_collector_origin','request_families.validate_origin'],
        familyCallsites=dict(PRODUCER_CAPTURE7=['current_controls.validate_data'],HOST7=['probe_adapter.validate'],
            COLLECTOR7=['probe_adapter.validate_collector_origin'],MODEL5=['consumer.validate_current_consumer_authority',
                'probe_adapter.validate_controller_authority','probe_adapter.validate_collector_authority']),
        preservedCriteria=['Business document wire/role semantics','replay and lifecycle','original clocks and leases','same physical budgets',
            'two whole ordinary windows','five original exports','Source15/Data24 exact closed formats','Source14/Data20 controller dynamic counts and reviewed rN/predecessor cwd'],
        gates=dict(actualHelperData=None,actualHelperRoot24=None,currentConsumerData24=None,ordinaryWindows=None,completionWrapper=None),
        modelsExecuted=0,executionAuthorized=False,selfApproval=False))
    effect=put(OWNED/'effect-and-limits.json',dict(schema='e02-consumer-current178-source-effect-v1',actor=ACTOR,
        codeEffect='Exact accepted current prerequisite readers and four explicit typed origin families; current runtime activation remains gated.',
        sourceSubject=subject,modelsDefined=total,modelsExecuted=0,targetImports=0,
        helperDataManufactured=False,actualHelperExecution=False,ordinaryRoleExecutions=0,ordinaryRowsQualified=0,
        noRuntimeGrant=True,noSDKAuthorization=True,canonicalE02='PARTIAL22_UNCHANGED',
        unresolved=['Independent post-freeze Source QA/security','Root Source acceptance','Separate complete current control release and DATA acceptance',
          'Actual positive helper DATA18/Root24','Actual persistent Root failstop continuity acceptance','Current consumer activation and ordinary evidence'],
        sourceCompilationIsRuntimeInteroperability=False))
    negative=put(OWNED/'negative-fixture-index.json',dict(schema='e02-consumer-current178-negative-definition-index-v1',actor=ACTOR,
        priorDefinitions=old_names,newFamilyAndCurrentInputDefinitions=added,
        fixtureMeaning='All generated API/platform-shaped objects are synthetic memory fixtures; retained accepted DATA is read-only. No synthetic object qualifies helper custody.',
        realHelperPositiveDefined=False,modelsExecuted=0))
    stage=doc(OWNED/'preparation-stage.json')
    stage.update(phase='SOURCE_GENERATION_COMPLETE_PENDING_POST_FREEZE_INDEPENDENT_REVIEW',modelsDefined=total,
                 modelsExecuted=0,targetImports=0,executionAuthorized=False)
    put(OWNED/'preparation-stage.json',stage)
    # Archive membership is explicitly finite and has no entrypoint/self cycle.
    archived=sorted(p for p in OWNED.rglob('*') if p.is_file() and p.name not in ('source-archive.tar','entrypoint.json','archive-membership.json'))
    archive=OWNED/'source-archive.tar'
    with tarfile.open(archive,'w',format=tarfile.USTAR_FORMAT) as tar:
        for p in archived:
            raw=p.read_bytes();info=tarfile.TarInfo(str(p.relative_to(OWNED)));info.size=len(raw);info.mode=0o644;info.mtime=0;info.uid=info.gid=0
            tar.addfile(info,io.BytesIO(raw))
    membership=put(OWNED/'archive-membership.json',dict(schema='e02-consumer-current178-finite-source-archive-v1',actor=ACTOR,
        archive=pin(archive),members=[dict(relativePath=str(p.relative_to(OWNED)),pin=pin(p)) for p in archived],
        count=len(archived),includesRuntimeProof=False,executionAuthorized=False))
    frozen=sorted(p for p in OWNED.rglob('*') if p.is_file() and p.name!='entrypoint.json')
    entry=put(OWNED/'entrypoint.json',dict(schema='e02-consumer-current178-frozen-source-entrypoint-v1',actor=ACTOR,
        rootScope=pin(SCOPE_PATH),subject=subject,controlPlan=plan_pin,derivedClosedContracts=closed,readMap=readmap_pin,
        requirements=requirements,effect=effect,preservation=preservation,sourceDiff=diff_pin,negativeFixtures=negative,
        creatorUnion=authors,archive=pin(archive),archiveMembership=membership,
        sourceCount=len(code),runtimeSourceCount=len(runtime),controlGroups=len(groups),countsSeparate=[g['count'] for g in groups],
        modelsDefined=total,modelsExecuted=0,targetImports=0,actualHelperData=None,actualHelperAcceptance=None,
        runtimeReady=False,executionAuthorized=False,sourceAccepted=False,independentReviews=None,
        state='WRITES_STOPPED_PENDING_FRESH_INDEPENDENT_SOURCE_QA_SECURITY',frozenFiles=[pin(p) for p in frozen],
        nextOwner='/root',nextAction='Independent read-only exact post-freeze Source QA/security, then Root Source decision; separate release needed for any models.'))
    print(json.dumps(dict(entrypoint=entry,subject=subject,controlPlan=plan_pin,archive=pin(archive),
        sourceCount=len(code),runtimeSourceCount=len(runtime),groups=len(groups),partition=[g['count'] for g in groups],
        modelDefinitions=total,modelsExecuted=0,metadataInputs=len(inputs),archivedFiles=len(archived))))


if __name__=='__main__':main()
