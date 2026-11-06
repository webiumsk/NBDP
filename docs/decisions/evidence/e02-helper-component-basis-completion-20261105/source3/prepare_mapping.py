"""Root-selected SOURCE mapping preparation; never issue a completed basis.

Only explicit Root-approved spec and Code SHA inputs may select operands. The
actor string is not authentication: actual Root must authenticate those exact
pins out of band. No operational helper body or arbitrary descriptor walk.
"""
import argparse
import ast
import copy
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import sysconfig

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bootstrap_strict as b

SPEC_KEYS='schema actor scope issued executionAuthorized helperSource readerSubject template designAcceptance root24Governance closureGovernance actorAuthority callerClosure callerClosureEvidence ordinary inputFiles'
ORDINARY_KEYS='admissionDataAcceptance captureSource captureSourceAcceptance controlPlan countsSeparate modelsDefined producerControlAcceptance producerControlData producerSource producerSourceAcceptance'
COUNTS=[129,33,29,16,20,10,11,8,7,3,20]
KINDS={'READER_CODE','SOURCE','GOVERNANCE','PURE_CONTROL_METADATA'}
VIRTUAL_PATH='/UNISSUED-MEMORY/e02-helper-component-basis/prospective.json'
SCOPE='VERIFY_ORIGINAL_HELPER_COMPONENT_SOURCE_MAPPING_ONLY'
SOURCE_NAMES=('README.md','bootstrap_strict.py','build_package.py','policy.json','prepare_mapping.py','test_prepare.py')
SEALED_CLI_IDENTITIES = ((4980, '786ffa958ed73a04b36537969973522b15867aa5051cfa8127cf533d84deb84b'), (4244, '938124c7f4d4da4f8a84a98e6f1eeb756024f720e2908bf9d37ea05a0263aa02'), (5163, '3712e08db8d52c813a1e6ba6c7fe151e97fe3284fb36c00c8c1c0d79ef036a38'), (415, 'ab29043bb9c535b5e1ccd95b8625834043a3064bb86b2a1c1fc0b3c8f20674b7'), (856, '6ef4c69d724875277e4b11127f923f327dcc3864a2beac434619cef656529efa'), (1612, '26c46563fbbe53107a25ed7177862a07c4ff5f289476e146bcdba525a2d1ec2e'), (20880, 'ca1817971cd4188a6caacc700d54df3351056da7a09a8d56bea918912fc60de9'))
PROTECTED_CLI_PATHS=('65d8116b77bc0af1a108122ec28cfcea','/probe-root-custody-actual/','/producer4-helper-probe-actual-r1/')


def need(value,why):b.need(value,why)
def equal(a,c,why='EXACT_PREPARATION_VALUE'):b.equal(a,c,why)
def closed(value,keys):return b.closed(value,keys)
def pin_bytes(path,raw):return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def identities(pin):return pin['bytes'],pin['sha256']

def admit_external_descriptor(descriptor,expected=None):
    """Pure admission: no stat/open/read to discover a caller-selected pin."""
    b.pin_shape(descriptor)
    need(not any(mark in descriptor['path'] for mark in PROTECTED_CLI_PATHS),'PROTECTED_CLI_PATH_FORBIDDEN_BEFORE_IO')
    need(identities(descriptor) not in set(SEALED_CLI_IDENTITIES),'SEALED_CLI_IDENTITY_FORBIDDEN_BEFORE_IO')
    if expected is not None:equal(descriptor,expected,'EXACT_TRUSTED_CALLER_DESCRIPTOR_BEFORE_IO')
    return descriptor

def sealed_identities(template,closure):
    original=template['originalBasis']['root24ExpectedPinOperands']
    pins=[original[k] for k in ('subject','rootRelease','concretePlan','execution','rawArtifactManifest','originalToolOrigin')]+[closure['finalF']]
    for pin in pins:b.pin_shape(pin)
    return {identities(pin) for pin in pins}

def pre_admit(rows,forbidden_run,denied):
    need(denied is not None,'TRUSTED_SEALED_IDENTITIES_REQUIRED_BEFORE_READ')
    need(type(rows) is list and 1<=len(rows)<=20000,'EXPLICIT_FINITE_INPUT_CLOSURE')
    seen=set()
    for row in rows:
        closed(row,'pin mode kind');b.pin_shape(row['pin']);b.integer(row['mode'],0,0o7777)
        need(row['kind'] in KINDS,'TYPED_INPUT_ROLE')
        path=row['pin']['path'];need(path not in seen,'DUPLICATE_INPUT_PATH');seen.add(path)
        need(forbidden_run not in path,'OPERATIONAL_HELPER_PATH_FORBIDDEN')
        need(identities(row['pin']) not in denied,'SEALED_HELPER_BYTES_FORBIDDEN_BEFORE_ANY_CAPABILITY_READ')
    return True

def validate_code_subject(subject):
    closed(subject,'schema author scope sourceCount sources modelsDefined modelsExecuted executionAuthorized bootstrapByteIdentical')
    equal(subject['schema'],'e02-helper-component-basis-preparation-code-v1')
    equal(subject['scope'],'SOURCE_PREPARATION_ONLY_NO_ISSUANCE')
    equal(subject['executionAuthorized'],False);equal(subject['modelsExecuted'],0)
    equal(subject['sourceCount'],len(SOURCE_NAMES));b.integer(subject['modelsDefined'],1,10000)
    need(type(subject['sources']) is list,'CODE_SOURCE_LIST')
    equal([Path(pin['path']).name for pin in subject['sources']],list(SOURCE_NAMES),'EXACT_PREPARATION_CODE_MEMBERSHIP')
    for pin in subject['sources']:
        b.pin_shape(pin);equal(Path(pin['path']).parent,HERE,'EXACT_PREPARATION_CODE_ROOT')
    equal(subject['bootstrapByteIdentical'],True)
    return subject


def validate_spec(spec,policy,helper_pin):
    closed(spec,SPEC_KEYS)
    equal(spec['schema'],'e02-helper-component-basis-preparation-spec-v2')
    equal(spec['actor'],'/root');equal(spec['scope'],SCOPE)
    equal(spec['issued'],True,'ROOT_APPROVED_SPEC_REQUIRED')
    equal(spec['executionAuthorized'],False)
    equal(spec['helperSource'],helper_pin,'EXACT_APPROVED_HELPER_CODE')
    for key in ('readerSubject','template','designAcceptance','root24Governance','closureGovernance'):
        equal(spec[key],policy[key],'PINNED_PREPARATION_POLICY:'+key)
    b.pin_shape(spec['actorAuthority'])
    equal(spec['actorAuthority'],policy['actorAuthority'],'EXACT_AUTHENTICATED_ROOT_ACTOR_AUTHORITY')
    need(spec['callerClosure'] is not None,'ROOT_CALLER_CLOSURE_REQUIRED')
    b.pin_shape(spec['callerClosure'])
    equal(spec['callerClosure'],policy['callerClosure'],'EXACT_ROOT_CALLER_V2_INPUT')
    equal(spec['callerClosureEvidence'],policy['callerClosureEvidence'],'EXACT_ROOT_CALLER_V2_EVIDENCE')
    ordinary=spec['ordinary'];closed(ordinary,ORDINARY_KEYS)
    equal(ordinary['countsSeparate'],COUNTS);equal(ordinary['modelsDefined'],286)
    for key in ORDINARY_KEYS.split():
        if key not in ('countsSeparate','modelsDefined'):b.pin_shape(ordinary[key])
    for key in ('producerSource','producerSourceAcceptance','controlPlan'):
        equal(ordinary[key],policy[key],'ACTUAL_ORDINARY_SOURCE:'+key)
    equal(ordinary['producerControlAcceptance'],policy['producer286RootAcceptance'],'ACTUAL_286_ROOT_RECEIPT')
    pre_admit(spec['inputFiles'],policy['forbiddenRun'],{identities(p) for p in policy['sealedBodyDescriptors']})
    required=[spec[k] for k in ('readerSubject','template','designAcceptance','root24Governance','closureGovernance','actorAuthority','callerClosure','callerClosureEvidence')]
    required += [policy['helperActorAttestation']]
    required += [ordinary[k] for k in ORDINARY_KEYS.split() if k not in ('countsSeparate','modelsDefined')]
    bypath={r['pin']['path']:r for r in spec['inputFiles']}
    for pin in required:equal(bypath.get(pin['path'],{}).get('pin'),pin,'REQUIRED_TYPED_INPUT_DECLARED')
    return spec


class ClosedFiles:
    """One exact immutable capability list over the frozen bounded safe reader."""
    def __init__(self,rows,forbidden_run,raw_files=None,*,denied=None):
        self.preadmitted=pre_admit(rows,forbidden_run,denied)
        self.rows={r['pin']['path']:copy.deepcopy(r) for r in rows}
        need(len(self.rows)==len(rows),'DUPLICATE_INPUT_PATH')
        self.raw=raw_files or b.Files(sorted({str(Path(p).parent) for p in self.rows}))
        self.forbidden_run=forbidden_run;self.denied=set(denied);self.used={};self.virtual={}
    def forbid_operational_descriptors(self,template,closure):
        need(sealed_identities(template,closure)<=self.denied,'COMPLETE_SEALED_IDENTITIES_REQUIRED_BEFORE_READ')
        for row in self.rows.values():need(identities(row['pin']) not in self.denied,'SEALED_HELPER_BYTES_FORBIDDEN')
    def read(self,pin,maximum=b.DATA,*,expected_mode=None):
        need(self.preadmitted,'CAPABILITY_LIST_MUST_BE_PRE_ADMITTED')
        b.pin_shape(pin);path=pin['path']
        if path==VIRTUAL_PATH:
            need(path in self.virtual and self.virtual[path][0]==pin,'EXACT_PROSPECTIVE_MEMORY_PIN')
            need(expected_mode is None,'NO_MEMORY_MODE_ASSERTION')
            need(pin['bytes']<=maximum,'MEMORY_READ_BOUND')
            return self.virtual[path][1]
        need(self.forbidden_run not in path and identities(pin) not in self.denied,'OPERATIONAL_HELPER_READ_FORBIDDEN')
        row=self.rows.get(path);need(row is not None,'UNDECLARED_INPUT_READ')
        equal(row['pin'],pin,'EXACT_INPUT_PIN')
        if expected_mode is not None:equal(expected_mode,row['mode'],'EXPECTED_MODE_MATCHES_SPEC')
        value=self.raw.read_mode(pin,row['mode'],maximum)
        self.used[path]=row
        return value
    def read_mode(self,pin,mode,maximum=b.DATA):return self.read(pin,maximum,expected_mode=mode)
    def doc(self,pin):return b.validate_numbers(b.loads(self.read(pin)))
    def prospective(self,value):
        raw=b.json_bytes(value);pin=pin_bytes(VIRTUAL_PATH,raw);self.virtual[VIRTUAL_PATH]=(pin,raw);return pin
    def recheck(self):self.raw.recheck()
    def closure(self):return [self.used[k] for k in sorted(self.used)]


def literal_values(raw):
    values={}
    for node in ast.parse(raw).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:values[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    return values


class PinnedReaderFinder(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    """Execute only the exact reviewed reader CODE bytes, never DATA payloads."""
    def __init__(self,bodies):self.bodies=bodies
    def find_spec(self,fullname,path=None,target=None):
        if fullname in self.bodies:return importlib.util.spec_from_loader(fullname,self)
        return None
    def create_module(self,spec):return None
    def exec_module(self,module):
        descriptor,raw=self.bodies[module.__name__]
        module.__file__=descriptor['path']
        exec(compile(raw,descriptor['path'],'exec'),module.__dict__)


def load_reader(files,subject_pin):
    subject=files.doc(subject_pin);equal(subject['schema'],'e02-ordinary-consumer6-source-subject-v1')
    equal(subject['version'],'SOURCE5');equal(subject['runtimeSourceCount'],16)
    members=subject['runtimeSources'];need(type(members) is list and len(members)==16,'EXACT_FROZEN_READER16')
    bodies={}
    for pin in members:
        name=Path(pin['path']).stem
        need(name not in bodies and Path(pin['path']).parent==Path(subject['sourceRoot']),'EXACT_READER_MEMBER_PATH')
        need(files.rows.get(pin['path'],{}).get('kind')=='READER_CODE','READER_CODE_ROLE')
        bodies[name]=(pin,files.read(pin))
    expected=literal_values(bodies['consumer'][1])['RUNTIME_FILES']
    equal([Path(p['path']).name for p in members],list(expected),'READER_DECLARED_ORDER')
    need(not(set(bodies)&set(sys.modules)),'FRESH_PINNED_READER_NAMESPACE_REQUIRED')
    finder=PinnedReaderFinder(bodies);sys.meta_path.insert(0,finder)
    try:
        reader=importlib.import_module('probe_adapter')
        for name in set(bodies)&set(sys.modules):equal(sys.modules[name].__file__,bodies[name][0]['path'])
    except BaseException:
        sys.meta_path.remove(finder)
        for name in bodies:sys.modules.pop(name,None)
        raise
    return reader,subject,finder


def actor_inputs(files,spec,policy,template):
    authority=files.doc(spec['actorAuthority'])
    # Preparatory Root input; its actual Root authentication is the approved pin.
    closed(authority,'schema actor participants scope executionAuthorized assignment originalHelperFieldDeclarations provenance')
    equal(authority['schema'],'e02-root-consumer-coupled-actor-authority-v1')
    equal(authority['actor'],'/root');equal(authority['executionAuthorized'],False)
    equal(authority['scope'],'FROZEN_FINAL_CONSUMER_SOURCE_AND_MODEL_CALLER_ACTORS_ONLY')
    participants=authority['participants'];need(type(participants) is list and participants==sorted(set(participants)) and participants,'CLOSED_SORTED_ACTOR_SET')
    for actor in participants:need(type(actor) is str and (actor=='/root' or actor.startswith('/root/')),'TYPED_ACTOR')
    assignment=authority['assignment'];closed(assignment,'sourceOwner operators predecessorSource predecessorActors')
    equal(assignment['sourceOwner'],policy['requiredSourceOwner']);equal(assignment['operators'],[policy['requiredModelOperator']])
    equal(assignment['predecessorSource'],policy['readerSubject'])
    equal(assignment['predecessorActors'],policy['source1Actors'])
    provenance=authority['provenance'];closed(provenance,'actorFieldAttestation assignmentScope method')
    equal(provenance['actorFieldAttestation'],policy['helperActorAttestation'])
    equal(provenance['method'],'ACTUAL_ROOT_VERIFIED_TYPED_FIELDS_NOT_OPERATIONAL_BODY_READS')
    assigned=files.doc(provenance['assignmentScope']);equal(assigned['actor'],'/root')
    equal(assigned['scope'],'PREPARE_IMMUTABLE_CONSUMER_SOURCE2_SUCCESSOR_WITH_ACTUAL_ACCEPTED_CURRENT_EVIDENCE')
    equal(assigned['executionAuthorized'],False)
    equal(Path(assigned['allowedOwnedRoot']).name,'source2')
    source=files.doc(assignment['predecessorSource'])
    code=next(p for p in source['runtimeSources'] if Path(p['path']).name=='consumer.py')
    values=literal_values(files.read(code))
    equal(values['CURRENT_CONTROL_ACTORS'],policy['source1Actors'])
    equal(source['sourceContributors'],policy['source1Contributors'])
    attestation=files.doc(policy['helperActorAttestation'])
    equal(attestation['schema'],'e02-root-original-helper-actor-field-attestation-v1');equal(attestation['actor'],'/root')
    equal(attestation['executionAuthorized'],False)
    equal(attestation['originalHelperAcceptance'],spec['root24Governance'])
    equal(attestation['closureDescriptor'],spec['closureGovernance'])
    declarations=attestation['fieldDeclarations'];equal(authority['originalHelperFieldDeclarations'],declarations)
    need(type(declarations) is list and len(declarations)==2,'BOTH_ORIGINAL_HELPER_ACTOR_FIELDS_REQUIRED')
    original=template['originalBasis']['root24ExpectedPinOperands']
    required=set(policy['source1Actors'])|set(policy['source1Contributors'])|{assignment['sourceOwner'],*assignment['operators']}
    for row,key,index,seq in zip(declarations,('rootRelease','subject'),(8,11),(9,12)):
        closed(row,'originalRecord provenance authors operators');equal(row['originalRecord'],original[key])
        proof=row['provenance'];closed(proof,'kind storeKey recordIndex sequence fields registeredBytesAndSHA256ReverifiedInMemory physicalReads operationalBodyCopies')
        for field,value in [('kind','GENUINE_ROOT_RETAINED_PLATFORM_MEMORY_RECORD'),('storeKey','e02_attempt4_runtime'),('recordIndex',index),('sequence',seq),('fields',['/authors','/operators']),('registeredBytesAndSHA256ReverifiedInMemory',True),('physicalReads',0),('operationalBodyCopies',0)]:equal(proof[field],value)
        for field in ('authors','operators'):
            actors=row[field];need(type(actors) is list and actors and len(actors)==len(set(actors)),'AUTHENTICATED_NONEMPTY_HELPER_ACTORS')
            for actor in actors:need(type(actor) is str and (actor=='/root' or actor.startswith('/root/')),'TYPED_HELPER_ACTOR')
            required.update(actors)
    equal(sorted(required),participants,'EXACT_PRESERVED_AND_ASSIGNED_ACTORS_REQUIRED')
    return set(participants)


def metadata_union(files,reader,template,ordinary,forbidden,facts_objects):
    _,old,new,controller,constants=facts_objects;original=template['originalBasis'];base=original['producer']
    union=set(forbidden)|{'/root',template['designAuthor']}
    union |= reader._component_control_actors(files,base['producerSource'],base['producerSourceAcceptance'],base['producerData'],base['producerDataAcceptance'],266,COUNTS[:-1])
    union |= reader._component_control_actors(files,ordinary['producerSource'],ordinary['producerSourceAcceptance'],ordinary['producerControlData'],ordinary['producerControlAcceptance'],286,COUNTS)
    for capture,admission in [(base['producerCaptureSource'],base['producerAdmissionDataAcceptance']),(ordinary['captureSource'],ordinary['admissionDataAcceptance'])]:
        union |= reader.actors(files.doc(capture)['authors'])
        union |= reader.data_actors(files.doc(files.doc(admission)['subject']))
    union |= reader._component_source_creators(controller)|reader.actors(constants['sourceContributors'])
    union |= reader._component_source_creators(files.doc(original['helperMethodSource']))
    for accepted in (original['helperMethodControlAcceptance'],original['controller']['controllerControlDataAcceptance']):
        union |= reader.data_actors(files.doc(files.doc(accepted)['subject']))
    return union


def select(value,pointer):
    need(type(pointer) is str and pointer.startswith('/') and len(pointer)<=4096,'EXPLICIT_CALLER_SELECTOR')
    for token in pointer[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~')
        value=value[int(token)] if type(value) is list else value[token]
    return value


def selected_actors(value):
    values=value if type(value) is list else [value]
    need(all(type(a) is str and (a=='/root' or a.startswith('/root/')) for a in values),'TYPED_CALLER_ACTORS')
    return sorted(set(values))


def verify_lineage(files,legacy,attempts,evidence,participants):
    """Verify finite Root-attested63-node field/edge lineage, not runtime proof.

    Root previously verified raw node/outcome/source pins. This function checks
    the fixed registry and typed Root field attestations; it never reopens those
    historical operational outcomes or arbitrarily follows their descriptors.
    """
    registry=files.doc(legacy['registry']);nodes=registry['legacyActorNodes']
    need(type(nodes) is dict and len(nodes)==63,'EXACT_63_DECLARED_LEGACY_NODES')
    equal(legacy['finiteNodes'],[nodes[path]['pin'] for path in sorted(nodes)],'EXACT_ROOT_FINITE_NODE_INVENTORY')
    old=files.doc(evidence['priorPreparationEvidence'])
    for key,value in [('historicalRegistry',legacy['registry']),('historicalDeclaredCallers',43),('fixedAllowedCallers',75),('failedAttempts',15),('existingLegacyNodes',63),('helperBodyReads',0),('actualFutureArtifactsIssued',False),('executionAuthorized',False)]:equal(old[key],value,'EXACT_ROOT_LINEAGE_PREPARATION')
    input_pins={q['path']:q for q in old['inputs']}
    equal(len(input_pins),len(old['inputs']),'UNIQUE_ROOT_LINEAGE_INPUT_PATHS')
    expected=[];review=[];local={path:set() for path in nodes}
    for path,rule in nodes.items():
        equal(rule['pin']['path'],path);equal(input_pins.get(path),rule['pin'],'ROOT_PREPARATION_OBSERVED_EACH_FINITE_NODE')
        for pointer in rule['actors']:
            target=review if pointer=='/conservativeReviewerExclusions' else expected
            target.append((rule['pin'],pointer))
        for edge in rule['actorEdges']:
            b.pin_shape(edge['pin']);equal(nodes.get(edge['pin']['path'],{}).get('pin'),edge['pin'],'ACTOR_EDGE_STAYS_IN_FINITE_63')
            need(type(edge['selector']) is str and edge['selector'].startswith('/'),'FINITE_TYPED_ACTOR_EDGE')
    proofs=legacy['selectedFieldProofs'];need(type(proofs) is list and len(proofs)==len(expected),'COMPLETE_ROOT_SELECTED_ACTOR_FIELD_PROOFS')
    for proof,(subject,pointer) in zip(proofs,expected):
        closed(proof,'subject selector actors');equal(proof['subject'],subject);equal(proof['selector'],pointer)
        equal(proof['actors'],selected_actors(proof['actors']))
        need(set(proof['actors'])<=participants,'HISTORICAL_CREATORS_WITHIN_FIXED_AUTHORITY')
        local[subject['path']].update(proof['actors'])
    reviewed=legacy['reviewOnlySelectors'];need(type(reviewed) is list and len(reviewed)==len(review),'REVIEW_ONLY_FIELDS_RETAINED_SEPARATELY')
    for proof,(subject,pointer) in zip(reviewed,review):
        closed(proof,'subject selector actors meaning');equal(proof['subject'],subject);equal(proof['selector'],pointer)
        equal(proof['meaning'],'WRAPPER_CONSERVATIVE_REVIEW_EXCLUSIONS_NOT_CALLER_CREATORS')
        equal(proof['actors'],selected_actors(proof['actors']))
    equal(legacy['legacyActors'],sorted(set().union(*local.values())),'DECLARED_CREATORS_WITHOUT_REVIEW_ONLY_PROMOTION')
    equal(len(legacy['legacyActors']),43);equal(legacy['helperBodyReads'],0);equal(legacy['executionAuthorized'],False)
    runs=registry['requiredFailedRuns'];need(type(runs) is list and len(runs)==len(set(runs))==14,'EXACT_FOURTEEN_PREDECESSOR_RUNS')
    need(len(attempts)==14,'EXACT_FOURTEEN_TYPED_ATTESTATIONS')
    for attempt,run in zip(attempts,runs):
        equal(attempt['runId'],run);equal(attempt['registry'],legacy['registry']);equal(attempt['executionAuthorized'],False)
        rule=registry['failedRunAuthorities'][run]
        equal(attempt['originalOutcomeAuthorities'],rule['outcomes']);equal(attempt['originalSourceSubject'],rule['sourceSubject'])
        pending=[]
        for pin in [*rule['outcomes'],rule['sourceSubject']]:
            equal(input_pins.get(pin['path']),pin,'ROOT_OBSERVED_ORIGINAL_OUTCOME_SOURCE_PIN')
            if pin['path'] in nodes:pending.append(pin['path'])
        seen=set();actors=set()
        while pending:
            path=pending.pop()
            if path in seen:continue
            need(path in nodes,'FINITE_ACTOR_NODE_REQUIRED');seen.add(path);actors|=local[path]
            pending.extend(e['pin']['path'] for e in nodes[path]['actorEdges'])
        need(actors,'KNOWN_NONEMPTY_ATTEMPT_ACTORS');equal(attempt['actors'],sorted(actors))
        equal(attempt['actorEvidenceNodes'],[nodes[path]['pin'] for path in sorted(seen)],'COMPLETE_TYPED_ATTEMPT_LINEAGE')


def caller_closure(files,pin,actor_authority,participants,policy):
    value=files.doc(pin)
    closed(value,'schema actor scope actorAuthority executionAuthorized declarations')
    equal(value['schema'],'e02-helper-component-basis-caller-closure-input-v2','STRICT_CALLER_CLOSURE_V2_ONLY')
    equal(value['actor'],'/root');equal(value['scope'],'SOURCE_MAPPING_CALLER_ACTOR_SUBSETS_ONLY')
    equal(value['executionAuthorized'],False);equal(value['actorAuthority'],actor_authority)
    declarations=value['declarations'];need(type(declarations) is list and len(declarations)==26,'EXACT_ROOT_26_CALLER_DECLARATIONS')
    inventory=[{k:row[k] for k in ('role','subject','selector')} for row in declarations]
    equal(inventory,policy['callerDeclarationInventory'],'EXACT_FROZEN_CALLER_DECLARATION_INVENTORY')
    evidence=files.doc(policy['callerClosureEvidence'])
    equal(evidence['schema'],'e02-root-caller-closure-v2-preparation-evidence-v1');equal(evidence['actor'],'/root')
    equal(evidence['callerClosure'],pin);equal(evidence['executionAuthorized'],False)
    equal(evidence['transform'],dict(changedKeys=['schema'],fromSchema='e02-helper-component-basis-caller-closure-input-v1',toSchema='e02-helper-component-basis-caller-closure-input-v2',declarationsUnchanged=True,authorOperatorSplitsInvented=False))
    prior=files.doc(evidence['priorCallerClosure']);equal(prior['declarations'],declarations,'V2_PRESERVES_GENUINE_V1_DECLARATIONS')
    equal(prior['schema'],'e02-helper-component-basis-caller-closure-input-v1')
    documents={};historical=[];future=None
    for row in declarations:
        closed(row,'role subject selector actors');subject=row['subject']
        if subject['path'] not in documents:documents[subject['path']]=files.doc(subject)
        document=documents[subject['path']]
        equal(document.get('schema'),policy['callerDocumentSchemas'][subject['path']],'EXACT_DECLARED_CALLER_METADATA_SCHEMA')
        observed=selected_actors(select(document,row['selector']))
        need(observed and set(observed)<=participants,'CALLER_ACTORS_MUST_BE_SUBSET_OF_FROZEN_AUTHORITY')
        equal(row['actors'],observed,'EXACT_CALLER_METADATA_ACTOR_FIELD')
        if row['role']=='attempt' and row['selector']=='/actors':historical.append(document)
        if row['role']=='futureWindow':future=document
    attempts={row['subject']['path'] for row in declarations if row['role']=='attempt'}
    equal(len(attempts),15,'ALL_FIFTEEN_DISTINCT_ATTEMPT_SUBJECT_PATHS')
    legacy=documents[declarations[0]['subject']['path']]
    verify_lineage(files,legacy,historical,evidence,participants)
    latest=documents[declarations[15]['subject']['path']]
    equal(latest['runId'],'3b22101922f48ee4daab728aa77b5d38');equal(latest['windowSubject'],None,'FAILED_WINDOW_CANNOT_DONATE_ROWS')
    need(future is not None,'BOTH_SOURCE_BOUND_FUTURE_WINDOW_ROLES')
    equal(future['actorAuthority'],actor_authority);equal(future['executionAuthorized'],False)
    for role in ('futureCandidate','futureHistory','futureSourceControls'):
        equal(future[role]['allowedActors'],sorted(participants));equal(future[role]['operators'],['/root'])
    for role in ('incoming','archive'):
        equal(future['futureWindows'][role]['allowedActors'],sorted(participants));equal(future['futureWindows'][role]['operators'],['/root'])
    return value


def prepare_in_memory(files,reader,spec,forbidden):
    """Pure engine; selected reader functions remain unmodified, no issuance."""
    template=files.doc(spec['template']);design=files.doc(spec['designAcceptance']);closure=files.doc(spec['closureGovernance'])
    files.forbid_operational_descriptors(template,closure)
    files.read(template['contract'])
    equal(template['originalBasis']['helperDataAcceptance'],spec['root24Governance'])
    facts_objects=reader._component_source_verification(files,template,spec['ordinary'])
    facts=facts_objects[0];union=metadata_union(files,reader,template,spec['ordinary'],forbidden,facts_objects)
    basis=copy.deepcopy(template)
    basis.update(issued=True,readiness=True,state='COMPLETED_SOURCE_COMPONENT_BASIS_ONLY',executionAuthorized=False,
      ordinarySuccessor=copy.deepcopy(spec['ordinary']),sourceVerification=facts,
      actorClosure=dict(schema='e02-helper-component-actor-closure-v1',participants=sorted(union)),
      sourceReviews=design['reviews'],rootDisposition=spec['designAcceptance'])
    for row,evidence in zip(basis['sourcePairs'],facts['sourcePairs']):row.update(newPin=evidence['newPin'],newMode='0o664')
    prospective=files.prospective(basis)
    checked,checked_union=reader.validate_component_basis(files,prospective,spec['template'],spec['designAcceptance'],spec['ordinary'],forbidden)
    equal(checked,basis);equal(sorted(checked_union),sorted(union));files.recheck()
    draft=copy.deepcopy(basis);draft.update(issued=False,readiness=False,state='UNISSUED_SOURCE_MAPPING_PREPARATION_ONLY')
    return dict(schema='e02-helper-component-basis-source-preparation-result-v1',state='UNISSUED_SOURCE_MAPPING_PREPARATION_ONLY',
      author='/root/consumer_eose_basis_source',basisIssued=False,executionAuthorized=False,rootIssuanceRequired=True,
      prospectiveCompletedStateUsedOnlyInMemory=True,sourceMappingMetadataVerified=True,actualS18M4Verified=False,
      completedBasis=None,draftBasis=draft,sourceVerification=facts,readClosure=files.closure())


def execute_preparation(files,reader,spec,policy,helper_pin):
    validate_spec(spec,policy,helper_pin)
    control=files.doc(spec['ordinary']['controlPlan'])
    equal(control['schema'],'e02-producer4-source-control-plan-v1')
    template=files.doc(spec['template']);forbidden=actor_inputs(files,spec,policy,template)
    caller_closure(files,spec['callerClosure'],spec['actorAuthority'],forbidden,policy)
    result=prepare_in_memory(files,reader,spec,forbidden)
    equal(result['draftBasis']['actorClosure']['participants'],sorted(forbidden),'ROOT_ACTOR_AUTHORITY_MUST_COVER_ALL_TYPED_METADATA_CREATORS')
    need(set(files.used)==set(files.rows),'COMPLETE_EXACT_TYPED_READ_CLOSURE_NO_UNUSED_INPUTS')
    return result


def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',required=True);parser.add_argument('--spec-sha256',required=True)
    parser.add_argument('--spec-bytes',required=True,type=int)
    parser.add_argument('--helper-source-sha256',required=True)
    parser.add_argument('--helper-source-bytes',required=True,type=int)
    args=parser.parse_args(argv)
    b.integer(args.spec_bytes,1,b.FILE);b.integer(args.helper_source_bytes,1,b.FILE)
    b.hx(args.spec_sha256);b.hx(args.helper_source_sha256)
    return args

def main():
    args=arguments()
    need(sys.flags.isolated==1 and sys.dont_write_bytecode,'ISOLATED_NO_BYTECODE_REQUIRED')
    # Root externally authenticates these two full SHA selections. No permission
    # is inferred from metadata actor strings or a boolean field.
    helper_path=HERE/'code-subject.json';helper=admit_external_descriptor(dict(path=str(helper_path),bytes=args.helper_source_bytes,sha256=args.helper_source_sha256))
    spec_path=Path(args.spec);spec_pin=admit_external_descriptor(dict(path=str(spec_path),bytes=args.spec_bytes,sha256=args.spec_sha256))
    bootstrap=b.Files([str(HERE),str(spec_path.parent)])
    subject=bootstrap.doc(helper)
    validate_code_subject(subject)
    for pin in subject['sources']:bootstrap.read(pin)
    equal(next(p for p in subject['sources'] if Path(p['path']).name=='prepare_mapping.py')['path'],str(Path(__file__).resolve()))
    policy=bootstrap.doc(next(p for p in subject['sources'] if Path(p['path']).name=='policy.json'))
    copied=next(p for p in subject['sources'] if Path(p['path']).name=='bootstrap_strict.py')
    equal(identities(copied),identities(policy['bootstrapSource']),'EXACT_FROZEN_BOOTSTRAP_BYTES')
    trusted=b.Files([str(Path(policy['template']['path']).parent),str(Path(policy['closureGovernance']['path']).parent)])
    denied=sealed_identities(trusted.doc(policy['template']),trusted.doc(policy['closureGovernance']));trusted.recheck()
    equal(denied,{identities(pin) for pin in policy['sealedBodyDescriptors']},'TRUSTED_BOOTSTRAP_SEALED_IDENTITY_JOIN')
    equal(denied,set(SEALED_CLI_IDENTITIES),'FROZEN_CLI_IDENTITY_POLICY_JOIN')
    need(identities(spec_pin) not in denied and policy['forbiddenRun'] not in spec_pin['path'],'SEALED_SPEC_ALIAS_FORBIDDEN_BEFORE_READ')
    spec=bootstrap.doc(spec_pin);validate_spec(spec,policy,helper)
    files=ClosedFiles(spec['inputFiles'],policy['forbiddenRun'],denied=denied)
    stdlib=Path(sysconfig.get_path('stdlib')).resolve()
    permitted={stdlib,stdlib/'lib-dynload',stdlib.parent/('python'+str(sys.version_info.major)+str(sys.version_info.minor)+'.zip')}
    sys.path[:]=[str(HERE),*[p for p in sys.path if p and Path(p).resolve() in permitted]]
    reader,_,finder=load_reader(files,spec['readerSubject'])
    try:
        result=execute_preparation(files,reader,spec,policy,helper)
        bootstrap.recheck();result['rootApprovedSpec']=spec_pin;result['helperSource']=helper
        print(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False))
    finally:
        sys.meta_path.remove(finder)

if __name__=='__main__':main()
