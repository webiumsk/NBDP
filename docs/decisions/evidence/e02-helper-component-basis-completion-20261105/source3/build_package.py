"""Prepare deterministic SOURCE metadata and an UNISSUED Root spec template.

Only explicit typed Source/governance/pure-control metadata selectors below are
followed. Never compute a basis, import the reader or open operational65 bodies.
"""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tarfile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bootstrap_strict as b
import prepare_mapping as engine

NAMES=('README.md','bootstrap_strict.py','build_package.py','policy.json','prepare_mapping.py','test_prepare.py')

def raw(path):
    path=Path(path);b.need(not path.is_symlink() and path.is_file(),'REGULAR_SOURCE_FILE')
    return path.read_bytes()
def pin(path):
    path=Path(path);body=raw(path);return dict(path=str(path),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
def put(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return pin(path)

def input_template(policy,helper,caller_pin=None):
    rows={};docs={};observed=[];run=policy['forbiddenRun']
    # Optional external selection is rejected before even trusted bootstrap I/O.
    if caller_pin is not None:
        b.need(engine.identities(caller_pin) not in {engine.identities(q) for q in policy['sealedBodyDescriptors']} and run not in caller_pin['path'],'SEALED_CALLER_ALIAS_FORBIDDEN_BEFORE_BUILDER_READ')
        b.equal(caller_pin,policy['callerClosure'],'EXACT_ROOT_CALLER_V2_INPUT')
    trusted=b.Files([str(Path(policy['template']['path']).parent),str(Path(policy['closureGovernance']['path']).parent)])
    denied=engine.sealed_identities(trusted.doc(policy['template']),trusted.doc(policy['closureGovernance']));trusted.recheck()
    b.equal(denied,{engine.identities(p) for p in policy['sealedBodyDescriptors']},'TRUSTED_BOOTSTRAP_SEALED_IDENTITY_JOIN')
    if caller_pin is not None:
        b.need(engine.identities(caller_pin) not in denied and run not in caller_pin['path'],'SEALED_CALLER_ALIAS_FORBIDDEN_BEFORE_BUILDER_READ')
        b.equal(caller_pin,policy['callerClosure'],'EXACT_ROOT_CALLER_V2_INPUT')
    def add(descriptor,kind,mode=None,decode=False):
        b.pin_shape(descriptor);path=descriptor['path'];b.need(run not in path,'NO_OPERATIONAL_HELPER_INPUT')
        b.need(engine.identities(descriptor) not in denied,'SEALED_HELPER_BYTES_FORBIDDEN_BEFORE_BUILDER_READ')
        selected=stat.S_IMODE(Path(path).stat().st_mode) if mode is None else mode
        previous=rows.get(path)
        if previous:
            b.equal(previous['pin'],descriptor,'ONE_EXACT_PIN_PER_INPUT_PATH')
            if kind=='READER_CODE':previous['kind']=kind
            if mode is not None:b.equal(previous['mode'],mode)
        else:rows[path]=dict(pin=descriptor,mode=selected,kind=kind)
        if path not in docs:
            reader=b.Files([str(Path(path).parent)]);body=reader.read_mode(descriptor,selected);reader.recheck()
            observed.append(descriptor)
            if decode:docs[path]=b.validate_numbers(b.loads(body))
        return docs.get(path)
    def doc(descriptor,kind='GOVERNANCE'):return add(descriptor,kind,decode=True)
    subject=doc(policy['readerSubject'],'SOURCE')
    for descriptor in subject['runtimeSources']:add(descriptor,'READER_CODE')
    template=doc(policy['template'],'SOURCE');original=template['originalBasis'];base=original['producer'];boundary=original['boundary']
    add(template['contract'],'SOURCE')
    design=doc(policy['designAcceptance']);doc(design['subject'],'SOURCE')
    for descriptor in design['reviews']:doc(descriptor)
    root=doc(policy['root24Governance']);doc(policy['closureGovernance'])
    for descriptor in root['reviews']:doc(descriptor)
    actor=doc(policy['actorAuthority']);doc(policy['helperActorAttestation']);doc(actor['provenance']['assignmentScope'])
    accepted=doc(policy['producer286RootAcceptance'])
    ordinary=dict(producerSource=accepted['producerSource'],producerSourceAcceptance=accepted['producerSourceAcceptance'],
      producerControlData=accepted['subject'],producerControlAcceptance=policy['producer286RootAcceptance'],
      captureSource=accepted['captureSource'],captureSourceAcceptance=accepted['captureSourceAcceptance'],
      admissionDataAcceptance=accepted['admissionDataAcceptance'],controlPlan=policy['controlPlan'],
      countsSeparate=[129,33,29,16,20,10,11,8,7,3,20],modelsDefined=286)
    doc(ordinary['controlPlan'],'SOURCE')
    producers=[]
    for source_pin,src_ack,data_pin,data_ack,capture,capture_ack,admission in (
       (base['producerSource'],base['producerSourceAcceptance'],base['producerData'],base['producerDataAcceptance'],base['producerCaptureSource'],base['producerCaptureSourceAcceptance'],base['producerAdmissionDataAcceptance']),
       (ordinary['producerSource'],ordinary['producerSourceAcceptance'],ordinary['producerControlData'],ordinary['producerControlAcceptance'],ordinary['captureSource'],ordinary['captureSourceAcceptance'],ordinary['admissionDataAcceptance'])):
        producer=doc(source_pin,'SOURCE');producers.append(producer)
        doc(src_ack);doc(data_pin,'PURE_CONTROL_METADATA');doc(data_ack)
        doc(capture,'SOURCE');doc(capture_ack);admitted=doc(admission);doc(admitted['subject'],'PURE_CONTROL_METADATA')
        for descriptor in producer['configurations'].values():doc(descriptor,'SOURCE')
    names=[r['name'] for r in template['sourcePairs']]
    for producer in producers:
        members={Path(q['path']).name:q for q in producer['sources']}
        for name in names:add(members[name],'SOURCE',0o664)
    doc(original['controller']['controllerSource'],'SOURCE');doc(boundary['controllerConstants'],'SOURCE')
    for descriptor in boundary['controllerRuntimeSources']:add(descriptor,'SOURCE')
    add(boundary['guardManifest'],'SOURCE')
    doc(original['helperMethodSource'],'SOURCE')
    for descriptor in (original['helperMethodControlAcceptance'],original['controller']['controllerControlDataAcceptance']):
        accepted=doc(descriptor);doc(accepted['subject'],'PURE_CONTROL_METADATA')
    if caller_pin:
        caller=doc(caller_pin);b.equal(caller['schema'],policy['callerSchema'])
        b.equal(set(caller),{'schema','actor','scope','actorAuthority','executionAuthorized','declarations'})
        for row in caller['declarations']:doc(row['subject'],'GOVERNANCE')
        evidence=doc(policy['callerClosureEvidence'])
        doc(evidence['priorCallerClosure']);doc(evidence['priorPreparationEvidence'])
        legacy=doc(caller['declarations'][0]['subject']);doc(legacy['registry'],'SOURCE')
    engine.pre_admit([rows[k] for k in sorted(rows)],run,denied)
    return dict(schema='e02-helper-component-basis-preparation-spec-v2',actor='/root',scope='VERIFY_ORIGINAL_HELPER_COMPONENT_SOURCE_MAPPING_ONLY',
      issued=False,executionAuthorized=False,helperSource=helper,readerSubject=policy['readerSubject'],template=policy['template'],
      designAcceptance=policy['designAcceptance'],root24Governance=policy['root24Governance'],closureGovernance=policy['closureGovernance'],
      actorAuthority=policy['actorAuthority'],callerClosure=caller_pin,callerClosureEvidence=policy['callerClosureEvidence'],ordinary=ordinary,inputFiles=[rows[k] for k in sorted(rows)]),observed

def build(caller_pin=None):
    policy=json.loads(raw(HERE/'policy.json'))
    engine.admit_external_descriptor(policy['callerClosure'] if caller_pin is None else caller_pin,policy['callerClosure'])
    b.equal(raw(HERE/'bootstrap_strict.py'),raw(Path(policy['bootstrapSource']['path'])),'UNCHANGED_FROZEN_BOOTSTRAP')
    methods=[]
    for path in (HERE/'prepare_mapping.py',HERE/'test_prepare.py',HERE/'build_package.py'):ast.parse(raw(path),filename=str(path))
    for cls in ast.parse(raw(HERE/'test_prepare.py')).body:
        if isinstance(cls,ast.ClassDef):methods.extend(cls.name+'.'+m.name for m in cls.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_'))
    original=[]
    for cls in ast.parse(raw(HERE.parent/'source2/test_prepare.py')).body:
        if isinstance(cls,ast.ClassDef):original.extend(cls.name+'.'+m.name for m in cls.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_'))
    b.equal(len(original),66);b.need(set(original)<=set(methods),'ALL_SOURCE2_PURPOSE_METHOD_NAMES_PRESERVED')
    code=put(HERE/'code-subject.json',dict(schema='e02-helper-component-basis-preparation-code-v1',author='/root/consumer_eose_basis_source',scope='SOURCE_PREPARATION_ONLY_NO_ISSUANCE',sourceCount=len(NAMES),sources=[pin(HERE/n) for n in NAMES],modelsDefined=len(methods),modelsExecuted=0,executionAuthorized=False,bootstrapByteIdentical=True))
    spec,reads=input_template(policy,code,policy['callerClosure'] if caller_pin is None else caller_pin)
    spec_pin=put(HERE/'spec.UNISSUED.json',spec)
    put(HERE/'input-read-map.json',dict(schema='e02-helper-component-basis-preparation-read-map-v1',explicitTypedInputs=spec['inputFiles'],preparationGeneratorReads=reads,
      descriptorWalk='Finite literal selectors in build_package.input_template only',operationalHelperBodiesRead=0,
      actualMappingExecuted=False,completedBasisIssued=False,missingRootInputs=[],
      nonAuthorityNote='Unissued spec and projected input closure; actual Root approval and frozen caller facts required before runner execution'))
    put(HERE/'control-plan.json',dict(schema='e02-helper-component-basis-preparation-definitions-v1',modelsDefined=len(methods),definitionNames=methods,modelsExecuted=0,canonicalBatchIssued=False,scope='NEW_PURE_PREPARATION_REGRESSIONS_ONLY'))
    put(HERE/'caller-closure.UNISSUED.json',dict(schema='e02-helper-component-basis-caller-closure-selection-template-v2',issued=False,readiness=False,executionAuthorized=False,actualRootCallerClosure=policy['callerClosure'],actualRootPreparationEvidence=policy['callerClosureEvidence'],note='Actual Root caller input exists; this selection template grants no preparation execution or basis issuance.'))
    put(HERE/'preservation.json',dict(schema='e02-helper-component-basis-source3-preservation-v1',rootScope=policy['rootScope'],predecessorCode=policy['predecessorCode'],predecessorEntrypoint=policy['predecessorEntrypoint'],predecessorUnchanged=True,predecessorModelsPreserved=66,mediumFirstReadAliasRemediated=True,strictV2Only=True,actualMappingExecuted=False,completedBasisIssued=False))
    paths=[HERE/n for n in (*NAMES,'code-subject.json','spec.UNISSUED.json','caller-closure.UNISSUED.json','input-read-map.json','control-plan.json','preservation.json','HANDOFF.md')]
    paths+=sorted((HERE/'evidence').glob('*.json')) if (HERE/'evidence').exists() else []
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w',format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(paths):
            body=raw(path);info=tarfile.TarInfo(str(path.relative_to(HERE)));info.size=len(body);info.mode=stat.S_IMODE(path.stat().st_mode);info.mtime=0;info.uid=info.gid=0;archive.addfile(info,io.BytesIO(body))
    (HERE/'source.tar').write_bytes(buffer.getvalue())
    return put(HERE/'entrypoint.json',dict(schema='e02-helper-component-basis-preparation-source-entrypoint-v1',author='/root/consumer_eose_basis_source',state='SOURCE3_PREPARATION_ONLY_PENDING_INDEPENDENT_QA_SECURITY',predecessor=policy['predecessorEntrypoint'],rootScope=policy['rootScope'],code=code,archive=pin(HERE/'source.tar'),unissuedSpec=spec_pin,
      readMap=pin(HERE/'input-read-map.json'),controls=pin(HERE/'control-plan.json'),evidence=[pin(p) for p in sorted((HERE/'evidence').glob('*.json'))],
      modelsDefined=len(methods),canonicalModelsExecuted=0,completedBasisIssued=False,actualSourceMappingExecuted=False,actualS18M4Verified=False,executionAuthorized=False))

def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--caller-closure')
    parser.add_argument('--caller-closure-bytes',type=int)
    parser.add_argument('--caller-closure-sha256')
    args=parser.parse_args(argv)
    if args.caller_closure is None:
        b.need(args.caller_closure_bytes is None and args.caller_closure_sha256 is None,'CALLER_CLOSURE_PATH_REQUIRED')
        return None
    b.need(args.caller_closure_bytes is not None and args.caller_closure_sha256 is not None,'COMPLETE_EXPECTED_CALLER_DESCRIPTOR_REQUIRED')
    return engine.admit_external_descriptor(dict(path=args.caller_closure,bytes=args.caller_closure_bytes,sha256=args.caller_closure_sha256))

def main(argv=None):
    caller=arguments(argv)
    # Fixed reviewed policy is bootstrap SOURCE, never the CLI-selected body.
    policy=json.loads(raw(HERE/'policy.json'))
    engine.admit_external_descriptor(policy['callerClosure'] if caller is None else caller,policy['callerClosure'])
    print(json.dumps(build(caller),sort_keys=True))

if __name__=='__main__':main()
