"""New pure preparation regressions; no actual mapping, approval or helper reads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import prepare_mapping as p
SOURCE1=HERE.parent.parent/'e02-consumer-eose-basis-successor-20261105/source1/source'
sys.path.insert(0,str(SOURCE1))
import test_component_basis as fixture
import probe_adapter as reader

class RawAdapter:
    def __init__(self,source):self.source=source;self.seen={}
    def read_mode(self,pin,mode,maximum):
        p.need(pin['bytes']<=maximum,'MODEL_MAXIMUM');self.seen[pin['path']]=(pin,mode)
        return self.source.read_mode(pin,mode)
    def recheck(self):
        for pin,mode in list(self.seen.values()):self.source.read_mode(pin,mode)


def model():
    m=fixture.model();f=m['files']
    closure=f.put('/model/closure',dict(finalF=dict(path='/OPERATIONAL_F',bytes=17,sha256='f'*64)))
    # The original fixture leaves its source-contract pin opaque. This new
    # preparation engine explicitly reads that Source operand, so model bytes
    # are supplied with matching descriptors before the graph is constructed.
    template=m['template']
    # The earlier mapping fixture used a spare collectorSource pin in its13
    # opaque operands. This runner also denies plain HOST-origin aliases, so
    # give this new vector the actual Root24 originalToolOrigin field instead.
    original=template['originalBasis'];root_pins=original['root24ExpectedPinOperands']
    root_pins['originalToolOrigin']=root_pins.pop('collectorSource')
    root=f.doc(original['helperDataAcceptance']);root['originalToolOrigin']=root.pop('collectorSource')
    original['helperDataAcceptance']=f.put(original['helperDataAcceptance']['path'],root)
    contract=f.put('/model/preparation-contract',b'SYNTHETIC_SOURCE_CONTRACT')
    old_contract=template['contract'];template['contract']=contract;m['basis']['contract']=contract
    design=f.doc(m['design_acceptance_pin']);design['contract']=contract
    template_pin=f.put(m['template_pin']['path'],template)
    entry=f.doc(design['subject'])
    def replace(value):
        if value==m['template_pin']:return template_pin
        if type(value) is dict:return {k:replace(v) for k,v in value.items()}
        if type(value) is list:return [replace(v) for v in value]
        return value
    design['subject']=f.put(design['subject']['path'],replace(entry));design['unissuedTemplate']=template_pin
    for pin in design['reviews']:
        value=f.doc(pin);value['subject']=design['subject'];new=f.put(pin['path'],value)
        design['reviews']=[new if q==pin else q for q in design['reviews']]
    design_pin=f.put(m['design_acceptance_pin']['path'],design)
    spec=dict(template=template_pin,designAcceptance=design_pin,closureGovernance=closure,
              root24Governance=template['originalBasis']['helperDataAcceptance'],ordinary=m['ordinary_expected'])
    rows=[dict(pin=p.pin_bytes(path,raw),mode=f.modes[path],kind='SOURCE') for path,raw in f.raw.items()]
    gate=p.ClosedFiles(rows,'65d8116b77bc0af1a108122ec28cfcea',RawAdapter(f),denied=p.sealed_identities(template,f.doc(closure)))
    return m,spec,gate

class PreparationModels(unittest.TestCase):
    def test_positive_real_frozen_validator_with_pure_synthetic_graph(self):
        m,s,g=model();r=p.prepare_in_memory(g,reader,s,m['forbidden'])
        self.assertTrue(r['sourceMappingMetadataVerified']);self.assertFalse(r['actualS18M4Verified'])
        self.assertFalse(r['basisIssued']);self.assertIsNone(r['completedBasis'])
        self.assertFalse(r['draftBasis']['issued']);self.assertFalse(r['draftBasis']['readiness'])
        self.assertEqual(set(r['draftBasis']),set(reader._COMPONENT_KEYS.split()))
        self.assertNotIn(p.VIRTUAL_PATH,{x['pin']['path'] for x in r['readClosure']})
    def test_unissued_draft_cannot_activate_frozen_reader(self):
        m,s,g=model();r=p.prepare_in_memory(g,reader,s,m['forbidden'])
        pin=g.prospective(r['draftBasis'])
        with self.assertRaisesRegex(ValueError,'COMPONENT_UNISSUED_BASIS'):
            reader.validate_component_basis(g,pin,s['template'],s['designAcceptance'],s['ordinary'],m['forbidden'])
    def test_original_template_unchanged(self):
        m,s,g=model();before=copy.deepcopy(m['template']);p.prepare_in_memory(g,reader,s,m['forbidden']);self.assertEqual(m['template'],before)
    def test_wrong_new286_control_tuple_refused(self):
        m,s,g=model();s['ordinary']=dict(s['ordinary'],producerControlAcceptance=s['ordinary']['producerControlData'])
        with self.assertRaises(ValueError):p.prepare_in_memory(g,reader,s,m['forbidden'])
    def test_wrong_source_mode_refused(self):
        m,s,g=model();pin=m['selected']['new'][0];g.rows[pin['path']]['mode']=0o600
        with self.assertRaisesRegex(ValueError,'EXPECTED_MODE_MATCHES_SPEC'):p.prepare_in_memory(g,reader,s,m['forbidden'])
    def test_mode_change_after_spec_refused(self):
        m,s,g=model();m['files'].modes[m['selected']['old'][0]['path']]=0o600
        with self.assertRaisesRegex(ValueError,'ACTUAL_MODE_REQUIRED'):p.prepare_in_memory(g,reader,s,m['forbidden'])
    def test_missing_source_capability_refused(self):
        m,s,g=model();del g.rows[m['selected']['new'][0]['path']]
        with self.assertRaisesRegex(ValueError,'UNDECLARED_INPUT_READ'):p.prepare_in_memory(g,reader,s,m['forbidden'])
    def test_same_path_wrong_hash_refused_before_raw_read(self):
        m,s,g=model();pin=dict(m['selected']['new'][0],sha256='e'*64)
        with self.assertRaisesRegex(ValueError,'EXACT_INPUT_PIN'):g.read(pin)
    def test_operational_path_never_reaches_raw_reader(self):
        m,s,g=model();before=len(m['files'].reads)
        with self.assertRaisesRegex(ValueError,'OPERATIONAL_HELPER_READ_FORBIDDEN'):
            g.read(dict(path='/tmp/65d8116b77bc0af1a108122ec28cfcea/S18',bytes=1,sha256='a'*64))
        self.assertEqual(len(m['files'].reads),before)
    def test_original_body_hash_alias_capability_refused(self):
        m,s,g=model();pin=dict(m['template']['originalBasis']['root24ExpectedPinOperands']['subject'],path='/model/copied-helper')
        g.rows[pin['path']]=dict(pin=pin,mode=0o600,kind='PURE_CONTROL_METADATA')
        with self.assertRaisesRegex(ValueError,'SEALED_HELPER_BYTES_FORBIDDEN'):g.forbid_operational_descriptors(m['template'],m['files'].doc(s['closureGovernance']))
    def test_final_f_hash_alias_capability_refused(self):
        m,s,g=model();pin=dict(path='/model/copied-F',bytes=17,sha256='f'*64)
        g.rows[pin['path']]=dict(pin=pin,mode=0o600,kind='SOURCE')
        with self.assertRaisesRegex(ValueError,'SEALED_HELPER_BYTES_FORBIDDEN'):g.forbid_operational_descriptors(m['template'],m['files'].doc(s['closureGovernance']))
    def test_unregistered_memory_record_refused(self):
        _,_,g=model()
        with self.assertRaisesRegex(ValueError,'EXACT_PROSPECTIVE_MEMORY_PIN'):g.read(dict(path=p.VIRTUAL_PATH,bytes=1,sha256='a'*64))
    def test_memory_record_cannot_claim_filesystem_mode(self):
        _,_,g=model();pin=g.prospective(dict(synthetic=True))
        with self.assertRaisesRegex(ValueError,'NO_MEMORY_MODE_ASSERTION'):g.read_mode(pin,0o664)
    def test_pinned_code_loader_executes_exact_supplied_code_bytes(self):
        name='_basis_preparation_synthetic_reader';raw=b'VALUE = 42\n';pin=p.pin_bytes('/model/synthetic_reader.py',raw)
        loader=p.PinnedReaderFinder({name:(pin,raw)});sys.meta_path.insert(0,loader)
        try:
            module=__import__(name);self.assertEqual(module.VALUE,42);self.assertEqual(module.__file__,pin['path'])
        finally:sys.meta_path.remove(loader);sys.modules.pop(name,None)
    def test_actual_temp_reader_wrong_mode_and_recheck(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-basis-preparation-') as d:
            path=Path(d)/'metadata';path.write_bytes(b'{}');path.chmod(0o664);pin=p.pin_bytes(str(path),b'{}')
            gate=p.ClosedFiles([dict(pin=pin,mode=0o664,kind='SOURCE')],'forbidden',denied=set())
            self.assertEqual(gate.read(pin),b'{}');path.chmod(0o600)
            with self.assertRaises(ValueError):gate.recheck()
    def test_actual_temp_reader_symlink_refused(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-basis-preparation-') as d:
            target=Path(d)/'target';target.write_bytes(b'{}');target.chmod(0o664);path=Path(d)/'link';path.symlink_to(target)
            pin=p.pin_bytes(str(path),b'{}');gate=p.ClosedFiles([dict(pin=pin,mode=0o664,kind='SOURCE')],'forbidden',denied=set())
            with self.assertRaises((ValueError,OSError)):gate.read(pin)


def spec_model():
    policy=json.loads((HERE/'policy.json').read_bytes());ordinary={}
    def pin(name):return dict(path='/model/'+name,bytes=1,sha256='a'*64)
    for key in p.ORDINARY_KEYS.split():ordinary[key]=pin(key)
    ordinary.update(countsSeparate=p.COUNTS,modelsDefined=286)
    for key in ('producerSource','producerSourceAcceptance','controlPlan'):ordinary[key]=policy[key]
    ordinary['producerControlAcceptance']=policy['producer286RootAcceptance']
    helper=pin('helper-source')
    spec=dict(schema='e02-helper-component-basis-preparation-spec-v2',actor='/root',scope=p.SCOPE,issued=True,executionAuthorized=False,
       helperSource=helper,readerSubject=policy['readerSubject'],template=policy['template'],designAcceptance=policy['designAcceptance'],
       root24Governance=policy['root24Governance'],closureGovernance=policy['closureGovernance'],actorAuthority=policy['actorAuthority'],callerClosure=policy['callerClosure'],callerClosureEvidence=policy['callerClosureEvidence'],ordinary=ordinary,inputFiles=[])
    required=[spec[k] for k in ('readerSubject','template','designAcceptance','root24Governance','closureGovernance','actorAuthority','callerClosure','callerClosureEvidence')]+[policy['helperActorAttestation']]+[ordinary[k] for k in p.ORDINARY_KEYS.split() if k not in ('countsSeparate','modelsDefined')]
    spec['inputFiles']=[dict(pin=v,mode=0o664,kind='SOURCE') for v in {v['path']:v for v in required}.values()]
    return spec,policy,helper

class RootSpecRefusals(unittest.TestCase):
    def reject(self,change,reason=None):
        s,policy,helper=spec_model();change(s)
        with self.assertRaisesRegex(ValueError,reason or '.') :p.validate_spec(s,policy,helper)
    def test_exact_actual_pin_policy_shape(self):
        s,policy,helper=spec_model();self.assertIs(p.validate_spec(s,policy,helper),s)
    def test_missing_caller_closure_refused(self):self.reject(lambda s:s.update(callerClosure=None),'ROOT_CALLER_CLOSURE_REQUIRED')
    def test_unissued_spec_refused(self):self.reject(lambda s:s.update(issued=False),'ROOT_APPROVED_SPEC_REQUIRED')
    def test_actor_string_not_runtime_permission(self):self.reject(lambda s:s.update(executionAuthorized=True))
    def test_wrong_root_actor_refused(self):self.reject(lambda s:s.update(actor='/root/worker'))
    def test_missing_actual286_receipt_refused(self):self.reject(lambda s:s['ordinary'].update(producerControlAcceptance=None))
    def test_old266_receipt_refused(self):self.reject(lambda s:s['ordinary'].update(producerControlAcceptance=s['ordinary']['producerControlData']),'ACTUAL_286_ROOT_RECEIPT')
    def test_other_producer_is_not_arbitrary_equivalence(self):self.reject(lambda s:s['ordinary'].update(producerSource=s['ordinary']['captureSource']),'ACTUAL_ORDINARY_SOURCE')
    def test_266_partition_refused(self):self.reject(lambda s:s['ordinary'].update(countsSeparate=p.COUNTS[:-1]))
    def test_extra_basis_issuance_flag_refused(self):self.reject(lambda s:s.update(issueBasis=True))
    def test_unapproved_actor_authority_refused(self):self.reject(lambda s:s.update(actorAuthority=s['ordinary']['producerSource']),'EXACT_AUTHENTICATED_ROOT_ACTOR_AUTHORITY')
    def test_duplicate_capability_refused(self):self.reject(lambda s:s['inputFiles'].append(s['inputFiles'][0]),'DUPLICATE_INPUT_PATH')
    def test_operational_capability_refused(self):self.reject(lambda s:s['inputFiles'].append(dict(pin=dict(path='/tmp/65d8116b77bc0af1a108122ec28cfcea/F',bytes=1,sha256='a'*64),mode=0o600,kind='SOURCE')),'OPERATIONAL_HELPER_PATH_FORBIDDEN')
    def test_wrong_input_mode_type_refused(self):self.reject(lambda s:s['inputFiles'][0].update(mode=True))
    def test_untyped_input_capability_refused(self):self.reject(lambda s:s['inputFiles'][0].update(kind='UNKNOWN'))
    def test_missing_mandatory_capability_refused(self):self.reject(lambda s:s['inputFiles'].pop(0),'REQUIRED_TYPED_INPUT_DECLARED')



def actor_model():
    # Explicit genuine Source/governance inputs only; selected operational record
    # descriptors are never followed. Every mutation below remains in memory.
    policy=json.loads((HERE/'policy.json').read_bytes());f=fixture.MemoryFiles()
    pins=[policy[k] for k in ('actorAuthority','helperActorAttestation','readerSubject','template')]
    authority=json.loads(Path(policy['actorAuthority']['path']).read_bytes())
    pins.append(authority['provenance']['assignmentScope'])
    source=json.loads(Path(policy['readerSubject']['path']).read_bytes())
    pins.append(next(v for v in source['runtimeSources'] if Path(v['path']).name=='consumer.py'))
    for pin in pins:
        raw=Path(pin['path']).read_bytes()
        assert p.pin_bytes(pin['path'],raw)==pin
        f.raw[pin['path']]=raw;f.modes[pin['path']]=0o664
    rows=[dict(pin=p.pin_bytes(path,raw),mode=0o664,kind='GOVERNANCE') for path,raw in f.raw.items()]
    gate=p.ClosedFiles(rows,policy['forbiddenRun'],RawAdapter(f),denied={p.identities(x) for x in policy['sealedBodyDescriptors']})
    spec=dict(actorAuthority=policy['actorAuthority'],root24Governance=policy['root24Governance'],closureGovernance=policy['closureGovernance'])
    return f,gate,spec,policy,f.doc(policy['template'])

class TypedActorModels(unittest.TestCase):
    def changed_authority(self,change):
        f,g,s,policy,t=actor_model();value=f.doc(s['actorAuthority']);change(value)
        pin=f.put(s['actorAuthority']['path'],value);s['actorAuthority']=pin;g.rows[pin['path']]['pin']=pin
        return g,s,policy,t
    def test_actual_root_opaque_attestation_yields_exact75(self):
        f,g,s,policy,t=actor_model();actors=p.actor_inputs(g,s,policy,t)
        self.assertEqual(len(actors),75);self.assertIn('/root/consumer_coupled_source2',actors)
        self.assertTrue(set(policy['source1Actors'])<=actors)
        self.assertTrue(all(policy['forbiddenRun'] not in path for path in f.reads))
    def test_missing_original_helper_author_refused(self):
        g,s,policy,t=self.changed_authority(lambda a:a['originalHelperFieldDeclarations'][0]['authors'].pop())
        with self.assertRaises(ValueError):p.actor_inputs(g,s,policy,t)
    def test_root_operator_cannot_be_empty(self):
        g,s,policy,t=self.changed_authority(lambda a:a['assignment'].update(operators=[]))
        with self.assertRaises(ValueError):p.actor_inputs(g,s,policy,t)
    def test_new_source_owner_cannot_be_omitted(self):
        g,s,policy,t=self.changed_authority(lambda a:a['participants'].remove('/root/consumer_coupled_source2'))
        with self.assertRaisesRegex(ValueError,'EXACT_PRESERVED_AND_ASSIGNED_ACTORS_REQUIRED'):p.actor_inputs(g,s,policy,t)
    def test_arbitrary_extra_actor_needs_successor(self):
        g,s,policy,t=self.changed_authority(lambda a:a.update(participants=sorted(a['participants']+['/root/unapproved'])))
        with self.assertRaisesRegex(ValueError,'EXACT_PRESERVED_AND_ASSIGNED_ACTORS_REQUIRED'):p.actor_inputs(g,s,policy,t)
    def test_operational_record_descriptor_must_match_original_root24(self):
        g,s,policy,t=self.changed_authority(lambda a:a['originalHelperFieldDeclarations'][1]['originalRecord'].update(sha256='b'*64))
        with self.assertRaises(ValueError):p.actor_inputs(g,s,policy,t)
    def test_fake_memory_provenance_is_not_root_attestation(self):
        g,s,policy,t=self.changed_authority(lambda a:a['originalHelperFieldDeclarations'][0]['provenance'].update(recordIndex=11))
        with self.assertRaises(ValueError):p.actor_inputs(g,s,policy,t)
    def test_predecessor_actor_set_cannot_drop_creator(self):
        g,s,policy,t=self.changed_authority(lambda a:a['assignment']['predecessorActors'].pop())
        with self.assertRaises(ValueError):p.actor_inputs(g,s,policy,t)


class CodeSelectionModels(unittest.TestCase):
    def value(self):
        return dict(schema='e02-helper-component-basis-preparation-code-v1',author='/root/consumer_eose_basis_source',
            scope='SOURCE_PREPARATION_ONLY_NO_ISSUANCE',sourceCount=6,
            sources=[dict(path=str(HERE/name),bytes=1,sha256='a'*64) for name in p.SOURCE_NAMES],
            modelsDefined=43,modelsExecuted=0,executionAuthorized=False,bootstrapByteIdentical=True)
    def test_exact_code_selection(self):
        value=self.value();self.assertIs(p.validate_code_subject(value),value)
    def test_omitted_bootstrap_cannot_hide_unpinned_code(self):
        value=self.value();value['sources']=value['sources'][1:]
        with self.assertRaises(ValueError):p.validate_code_subject(value)
    def test_foreign_source_directory_refused(self):
        value=self.value();value['sources'][0]['path']='/tmp/README.md'
        with self.assertRaisesRegex(ValueError,'EXACT_PREPARATION_CODE_ROOT'):p.validate_code_subject(value)
    def test_reordered_code_sources_refused(self):
        value=self.value();value['sources'].reverse()
        with self.assertRaises(ValueError):p.validate_code_subject(value)



def caller_model():
    f=fixture.MemoryFiles();participants={'/root'}|{'/root/a%02d'%i for i in range(74)}
    authority=f.put('/model/caller-authority',dict(synthetic=True))
    names=['/model/node-%02d'%i for i in range(63)];nodes={};local={};proofs=[];inputs=[]
    for i,path in enumerate(names):
        actor='/root/a%02d'%(i%42) if i else '/root'
        pin=f.put(path,dict(schema='synthetic-source',author=actor))
        nodes[path]=dict(pin=pin,keys=['schema','author'],schema='synthetic-source',actors=['/author'],actorEdges=[])
        if i:nodes[path]['actorEdges']=[dict(selector='/prior',pin=nodes[names[i-1]]['pin'])]
        local[path]={actor};proofs.append(dict(subject=pin,selector='/author',actors=[actor]));inputs.append(pin)
    runs=['%032x'%(i+1) for i in range(14)]
    rules={run:dict(outcomes=[nodes[names[i]]['pin']],sourceSubject=nodes[names[i]]['pin']) for i,run in enumerate(runs)}
    registry=f.put('/model/registry',dict(legacyActorNodes=nodes,requiredFailedRuns=runs,failedRunAuthorities=rules))
    legacy_actors=sorted(set().union(*local.values()))
    legacy=f.put('/model/legacy',dict(schema='e02-root-historical-declared-caller-attestation-v1',actor='/root',registry=registry,finiteNodes=[nodes[k]['pin'] for k in sorted(nodes)],selectedFieldProofs=proofs,legacyActors=legacy_actors,reviewOnlySelectors=[],helperBodyReads=0,executionAuthorized=False))
    declarations=[dict(role='legacy',subject=legacy,selector='/legacyActors',actors=legacy_actors)]
    for i,run in enumerate(runs):
        seen=names[:i+1];actors=sorted(set().union(*(local[x] for x in seen)))
        pin=f.put('/model/attempt-'+run,dict(schema='e02-root-historical-attempt-declared-caller-attestation-v1',actor='/root',runId=run,registry=registry,originalOutcomeAuthorities=rules[run]['outcomes'],originalSourceSubject=rules[run]['sourceSubject'],actors=actors,actorEvidenceNodes=[nodes[k]['pin'] for k in sorted(seen)],executionAuthorized=False))
        declarations.append(dict(role='attempt',subject=pin,selector='/actors',actors=actors))
    latest=f.put('/model/latest',dict(schema='e02-minimum-attempt-subject-v1',runId='3b22101922f48ee4daab728aa77b5d38',windowSubject=None,authors=['/root/a00'],operators=['/root']))
    for key in ('authors','operators'):declarations.append(dict(role='attempt',subject=latest,selector='/'+key,actors=['/root/a00'] if key=='authors' else ['/root']))
    for role in ('candidate','sourceControls'):
        pin=f.put('/model/'+role,dict(schema='synthetic-'+role,authors=['/root/a00'],operators=['/root']))
        for key in ('authors','operators'):declarations.append(dict(role=role,subject=pin,selector='/'+key,actors=['/root/a00'] if key=='authors' else ['/root']))
    future=f.put('/model/future',dict(schema='e02-root-future-consumer-caller-source-policy-v1',actor='/root',actorAuthority=authority,executionAuthorized=False,
      futureCandidate=dict(allowedActors=sorted(participants),operators=['/root']),futureHistory=dict(allowedActors=sorted(participants),operators=['/root']),futureSourceControls=dict(allowedActors=sorted(participants),operators=['/root']),futureWindows={role:dict(allowedActors=sorted(participants),operators=['/root']) for role in ('incoming','archive')}))
    for role,selector in [('candidate','/futureCandidate/allowedActors'),('history','/futureHistory/allowedActors'),('sourceControls','/futureSourceControls/allowedActors'),('futureWindow','/futureWindows/incoming/allowedActors'),('futureWindow','/futureWindows/archive/allowedActors')]:declarations.append(dict(role=role,subject=future,selector=selector,actors=sorted(participants)))
    value=dict(schema='e02-helper-component-basis-caller-closure-input-v2',actor='/root',scope='SOURCE_MAPPING_CALLER_ACTOR_SUBSETS_ONLY',actorAuthority=authority,declarations=declarations,executionAuthorized=False)
    prior_value=dict(value,schema='e02-helper-component-basis-caller-closure-input-v1');prior=f.put('/model/prior-caller',prior_value)
    prior_evidence=f.put('/model/prior-evidence',dict(historicalRegistry=registry,historicalDeclaredCallers=43,fixedAllowedCallers=75,failedAttempts=15,existingLegacyNodes=63,helperBodyReads=0,actualFutureArtifactsIssued=False,executionAuthorized=False,inputs=inputs))
    f.preparation_evidence=dict(schema='e02-root-caller-closure-v2-preparation-evidence-v1',actor='/root',callerClosure=None,executionAuthorized=False,priorPreparationEvidence=prior_evidence,priorCallerClosure=prior,transform=dict(changedKeys=['schema'],fromSchema='e02-helper-component-basis-caller-closure-input-v1',toSchema='e02-helper-component-basis-caller-closure-input-v2',declarationsUnchanged=True,authorOperatorSplitsInvented=False))
    f.policy=dict(callerDeclarationInventory=[{k:r[k] for k in ('role','subject','selector')} for r in declarations],callerDocumentSchemas={r['subject']['path']:f.doc(r['subject'])['schema'] for r in declarations})
    return f,participants,authority,value

class CallerClosureModels(unittest.TestCase):
    def run_value(self,f,a,authority,value):
        pin=f.put('/model/caller-closure',value)
        rows=[dict(pin=p.pin_bytes(path,raw),mode=f.modes[path],kind='GOVERNANCE') for path,raw in f.raw.items()]
        prior_value=f.doc(f.preparation_evidence['priorCallerClosure']);prior_value['declarations']=copy.deepcopy(value['declarations'])
        prior_pin=f.put(f.preparation_evidence['priorCallerClosure']['path'],prior_value)
        evidence=dict(f.preparation_evidence,callerClosure=pin,priorCallerClosure=prior_pin);evidence_pin=f.put('/model/evidence',evidence)
        f.policy['callerClosureEvidence']=evidence_pin
        rows=[dict(pin=p.pin_bytes(path,raw),mode=f.modes[path],kind='GOVERNANCE') for path,raw in f.raw.items()]
        return p.caller_closure(p.ClosedFiles(rows,'65d8116b77bc0af1a108122ec28cfcea',RawAdapter(f),denied=set()),pin,authority,a,f.policy)
    def test_fifteen_history_metadata_and_explicit_future_roles(self):
        f,a,auth,value=caller_model();self.assertEqual(self.run_value(f,a,auth,value),value)
    def test_future_consumer_data_pin_not_required_avoids_cycle(self):
        f,a,auth,value=caller_model();self.run_value(f,a,auth,value)
        self.assertNotIn('consumerControlData',f.raw)
    def test_historical_actor_not_in_frozen_set_refused(self):
        f,a,auth,value=caller_model()
        with self.assertRaisesRegex(ValueError,'CALLER_ACTORS_MUST_BE_SUBSET'):self.run_value(f,{'/root'},auth,value)
    def test_omitted_historical_field_refused(self):
        f,a,auth,value=caller_model();value['declarations'].pop()
        with self.assertRaisesRegex(ValueError,'EXACT_ROOT_26_CALLER_DECLARATIONS'):self.run_value(f,a,auth,value)
    def test_missing_future_control_actor_declaration_refused(self):
        f,a,auth,value=caller_model();value['declarations'].pop()
        with self.assertRaisesRegex(ValueError,'EXACT_ROOT_26_CALLER_DECLARATIONS'):self.run_value(f,a,auth,value)
    def test_undeclared_future_writer_refused(self):
        f,a,auth,value=caller_model();value['declarations'][-1]['actors']=['/root/unknown']
        with self.assertRaisesRegex(ValueError,'EXACT_CALLER_METADATA_ACTOR_FIELD'):self.run_value(f,a,auth,value)
    def test_forged_metadata_projection_refused(self):
        f,a,auth,value=caller_model();value['declarations'][0]['actors']=['/root']
        with self.assertRaisesRegex(ValueError,'EXACT_CALLER_METADATA_ACTOR_FIELD'):self.run_value(f,a,auth,value)


class FirstReadAliasModels(unittest.TestCase):
    class NoRawReads:
        def __init__(self):self.calls=0
        def read_mode(self,*args):self.calls+=1;raise AssertionError('RAW_ALIAS_READ')
        def recheck(self):self.calls+=1;raise AssertionError('RAW_ALIAS_RECHECK')
    def check_role(self,role):
        policy=json.loads((HERE/'policy.json').read_bytes());denied={p.identities(v) for v in policy['sealedBodyDescriptors']}
        for original in policy['sealedBodyDescriptors']:
            with self.subTest(role=role,sha=original['sha256']):
                pin=dict(original,path='/model/renamed-'+role+'.json');raw=self.NoRawReads()
                rows=[dict(pin=dict(path='/model/innocent',bytes=2,sha256=hashlib.sha256(b'{}').hexdigest()),mode=0o664,kind='SOURCE'),dict(pin=pin,mode=0o664,kind='READER_CODE' if role=='reader' else 'GOVERNANCE')]
                with self.assertRaisesRegex(ValueError,'SEALED_HELPER_BYTES_FORBIDDEN_BEFORE_ANY_CAPABILITY_READ'):
                    files=p.ClosedFiles(rows,policy['forbiddenRun'],raw,denied=denied)
                    if role=='reader':p.load_reader(files,pin)
                    else:files.doc(pin)
                self.assertEqual(raw.calls,0)
    def test_all_seven_aliases_refused_before_reader_load(self):self.check_role('reader')
    def test_all_seven_aliases_refused_before_caller_read(self):self.check_role('caller')
    def test_all_seven_aliases_refused_before_history_read(self):self.check_role('history')
    def test_all_seven_aliases_refused_before_attempt_read(self):self.check_role('attempt')
    def test_missing_trusted_denial_set_cannot_read(self):
        raw=self.NoRawReads()
        with self.assertRaisesRegex(ValueError,'TRUSTED_SEALED_IDENTITIES_REQUIRED_BEFORE_READ'):
            p.ClosedFiles([dict(pin=dict(path='/model/source',bytes=1,sha256='a'*64),mode=0o664,kind='SOURCE')],'forbidden',raw)
        self.assertEqual(raw.calls,0)
    def test_entire_spec_rejects_unused_sealed_alias_before_reads(self):
        spec,policy,helper=spec_model()
        for original in policy['sealedBodyDescriptors']:
            changed=copy.deepcopy(spec);changed['inputFiles'].append(dict(pin=dict(original,path='/model/unused-alias'),mode=0o664,kind='SOURCE'))
            with self.assertRaisesRegex(ValueError,'SEALED_HELPER_BYTES_FORBIDDEN_BEFORE_ANY_CAPABILITY_READ'):p.validate_spec(changed,policy,helper)

class StrictV2Models(unittest.TestCase):
    def run_changed(self,change):
        f,a,auth,value=caller_model();change(f,a,auth,value)
        return CallerClosureModels().run_value(f,a,auth,value)
    def test_v1_six_key_input_cannot_fallback(self):
        with self.assertRaisesRegex(ValueError,'STRICT_CALLER_CLOSURE_V2_ONLY'):
            self.run_changed(lambda f,a,auth,v:v.update(schema='e02-helper-component-basis-caller-closure-input-v1'))
    def test_v1_eight_key_input_cannot_fallback(self):
        with self.assertRaises(ValueError):self.run_changed(lambda f,a,auth,v:v.update(history={},futureDeclarations=[]))
    def test_swapped_named_inventory_refused(self):
        def change(f,a,auth,v):v['declarations'][1],v['declarations'][2]=v['declarations'][2],v['declarations'][1]
        with self.assertRaisesRegex(ValueError,'EXACT_FROZEN_CALLER_DECLARATION_INVENTORY'):self.run_changed(change)
    def test_tampered_registry_node_descriptor_refused(self):
        def change(f,a,auth,v):
            pin=v['declarations'][0]['subject'];legacy=f.doc(pin);legacy['finiteNodes'].pop();new=f.put(pin['path'],legacy)
            for row in v['declarations']:
                if row['subject']==pin:row['subject']=new
            f.policy['callerDeclarationInventory'][0]['subject']=new
        with self.assertRaisesRegex(ValueError,'EXACT_ROOT_FINITE_NODE_INVENTORY'):self.run_changed(change)
    def test_changed_failed_attempt_lineage_refused(self):
        def change(f,a,auth,v):
            pin=v['declarations'][1]['subject'];value=f.doc(pin);value['actorEvidenceNodes']=[];new=f.put(pin['path'],value);v['declarations'][1]['subject']=new;f.policy['callerDeclarationInventory'][1]['subject']=new
        with self.assertRaisesRegex(ValueError,'COMPLETE_TYPED_ATTEMPT_LINEAGE'):self.run_changed(change)


class ApprovedPinArgumentModels(unittest.TestCase):
    def test_explicit_root_approved_lengths_and_hashes(self):
        args=p.arguments(['--spec','/model/spec','--spec-bytes','123','--spec-sha256','a'*64,'--helper-source-bytes','456','--helper-source-sha256','b'*64])
        self.assertEqual((args.spec_bytes,args.helper_source_bytes),(123,456))
    def test_zero_length_root_spec_refused_before_read(self):
        with self.assertRaises(ValueError):p.arguments(['--spec','/model/spec','--spec-bytes','0','--spec-sha256','a'*64,'--helper-source-bytes','456','--helper-source-sha256','b'*64])


class CanonicalActorSetModels(unittest.TestCase):
    def model_value(self):
        f,a,auth,value=caller_model();old=value['declarations'][17]['subject'];doc=f.doc(old)
        doc['authors']=['/root/a00','/root'];new=f.put(old['path'],doc)
        for i in (17,18):value['declarations'][i]['subject']=new;f.policy['callerDeclarationInventory'][i]['subject']=new
        value['declarations'][17]['actors']=['/root','/root/a00']
        return f,a,auth,value,new
    def test_raw_actor_order_projects_canonical_set_without_rewriting_raw(self):
        f,a,auth,value,pin=self.model_value();before=f.raw[pin['path']]
        CallerClosureModels().run_value(f,a,auth,value)
        self.assertEqual(f.raw[pin['path']],before)
        self.assertEqual(f.doc(pin)['authors'],['/root/a00','/root'])
    def test_noncanonical_declared_actor_list_refused(self):
        f,a,auth,value,pin=self.model_value();value['declarations'][17]['actors'].reverse()
        with self.assertRaisesRegex(ValueError,'EXACT_CALLER_METADATA_ACTOR_FIELD'):CallerClosureModels().run_value(f,a,auth,value)


# Actual unmodified __main__ bytecode is executed from a temporary package.
# Instrumentation observes target I/O; it does not replace build/validation.
CLI_OBSERVER=r'''
import builtins,contextlib,io,json,os,pathlib,runpy,sys
script,target,arguments=sys.argv[1],sys.argv[2],json.loads(sys.argv[3])
counts=dict(targetReadBytes=0,targetStat=0,targetOpen=0,writes=0)
oldread=pathlib.Path.read_bytes;oldstat=pathlib.Path.stat
name=pathlib.Path(target).name

def read(self,*args,**kwargs):
    if str(self)==target:counts['targetReadBytes']+=1
    return oldread(self,*args,**kwargs)
def status(self,*args,**kwargs):
    if str(self)==target:counts['targetStat']+=1
    return oldstat(self,*args,**kwargs)
pathlib.Path.read_bytes=read;pathlib.Path.stat=status

def audit(event,args):
    if event!='open':return
    path,mode,flags=args
    if isinstance(path,(str,bytes)) and (str(path)==target or str(path)==name):counts['targetOpen']+=1
    if isinstance(mode,str) and any(c in mode for c in ('w','a','x','+')):counts['writes']+=1
    elif isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):counts['writes']+=1
sys.addaudithook(audit)
sys.argv=[script,*arguments];out=io.StringIO();err=io.StringIO();failure=None
try:
    with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):runpy.run_path(script,run_name='__main__')
except BaseException as exc:failure=dict(type=type(exc).__name__,message=str(exc))
print(json.dumps(dict(counts=counts,failure=failure,stdout=out.getvalue(),stderr=err.getvalue()),sort_keys=True))
'''


def cli_package(root):
    """Minimal synthetic metadata for the real builder, not fake approvals."""
    import shutil
    source=root/'source3';source.mkdir();previous=root/'source2';previous.mkdir()
    for name in p.SOURCE_NAMES:shutil.copyfile(HERE/name,source/name)
    shutil.copyfile(HERE.parent/'source2/test_prepare.py',previous/'test_prepare.py')
    (source/'HANDOFF.md').write_text('SYNTHETIC TEMPORARY SOURCE PREPARATION ONLY\n')
    metadata=root/'metadata';metadata.mkdir();serial=[0]
    def put(value,name=None,mode=0o664):
        serial[0]+=1;path=metadata/(name or ('m%03d'%serial[0]));raw=value if type(value) is bytes else json.dumps(value).encode()
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(mode);return p.pin_bytes(str(path),raw)
    empty=put({});ack=put(dict(subject=empty));capture=put({})
    names=list(reader._COMPONENT_NAMES)
    members={side:[put(b'SYNTHETIC_SOURCE',side+'/'+name) for name in names] for side in ('old','new')}
    producers={}
    for side in ('old','new'):
        producers[side]=put(dict(sources=members[side],configurations={role:put({}) for role in ('incoming','archive')}))
    consumer=put(b'RUNTIME_FILES=("consumer.py",)\n','consumer.py')
    reader_subject=put(dict(runtimeSources=[consumer]))
    actual=json.loads((HERE/'policy.json').read_bytes());sealed=actual['sealedBodyDescriptors']
    original=dict(producer=dict(producerSource=producers['old'],producerSourceAcceptance=ack,producerData=empty,producerDataAcceptance=ack,
       producerCaptureSource=capture,producerCaptureSourceAcceptance=ack,producerAdmissionDataAcceptance=ack),
       root24ExpectedPinOperands={key:pin for key,pin in zip(('subject','rootRelease','concretePlan','execution','rawArtifactManifest','originalToolOrigin'),sealed[:6])},
       controller=dict(controllerSource=empty,controllerControlDataAcceptance=ack),
       boundary=dict(controllerConstants=empty,controllerRuntimeSources=[put(b'pass\n')],guardManifest=empty),
       helperMethodSource=empty,helperMethodControlAcceptance=ack)
    template=put(dict(contract=put(b'SYNTHETIC_CONTRACT'),originalBasis=original,sourcePairs=[dict(name=n) for n in names]))
    closure=put(dict(finalF=sealed[-1]));root24=put(dict(reviews=[empty]))
    design=put(dict(subject=empty,reviews=[empty]));actor=put(dict(provenance=dict(assignmentScope=empty)))
    root286=put(dict(producerSource=producers['new'],producerSourceAcceptance=ack,subject=empty,captureSource=capture,captureSourceAcceptance=ack,admissionDataAcceptance=ack))
    legacy=put(dict(registry=empty));caller=put(dict(schema='e02-helper-component-basis-caller-closure-input-v2',actor='/root',scope='SOURCE_MAPPING_CALLER_ACTOR_SUBSETS_ONLY',actorAuthority=actor,executionAuthorized=False,declarations=[dict(subject=legacy)]),'selected-caller.json')
    evidence=put(dict(priorCallerClosure=empty,priorPreparationEvidence=empty))
    bootstrap=p.pin_bytes(str(source/'bootstrap_strict.py'),(source/'bootstrap_strict.py').read_bytes())
    policy=dict(actual,bootstrapSource=bootstrap,readerSubject=reader_subject,template=template,closureGovernance=closure,root24Governance=root24,
       designAcceptance=design,actorAuthority=actor,helperActorAttestation=empty,producer286RootAcceptance=root286,controlPlan=empty,
       callerClosure=caller,callerClosureEvidence=evidence,rootScope=empty,predecessorCode=empty,predecessorEntrypoint=empty)
    (source/'policy.json').write_text(json.dumps(policy))
    return source,policy


class RealCliAdmissionModels(unittest.TestCase):
    observations=[]
    @classmethod
    def tearDownClass(cls):
        print('REAL_CLI_IO_OBSERVATIONS='+json.dumps(cls.observations,sort_keys=True,separators=(',',':')))
    def observe(self,source,script,target,args):
        import subprocess
        result=subprocess.run([sys.executable,'-I','-B','-c',CLI_OBSERVER,str(source/script),str(target),json.dumps(args)],
           cwd=source,env=dict(PATH='/usr/bin:/bin',LANG='C.UTF-8',LC_ALL='C.UTF-8'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,check=False)
        self.assertEqual(result.returncode,0,result.stderr.decode());self.assertEqual(result.stderr,b'')
        observed=json.loads(result.stdout)
        self.observations.append(dict(script=script,scriptSha256=hashlib.sha256((source/script).read_bytes()).hexdigest(),target=str(target),arguments=args,returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode()))
        return observed
    def zero(self,result):
        self.assertIsNotNone(result['failure']);self.assertEqual(result['counts'],dict(targetReadBytes=0,targetStat=0,targetOpen=0,writes=0))
    def test_real_builder_main_rejects_all_seven_aliases_before_io(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d));target=Path(d)/'renamed-body';target.write_bytes(b'SYNTHETIC_NOT_OPERATIONAL_DATA')
            for protected in policy['sealedBodyDescriptors']:
                with self.subTest(sha=protected['sha256']):
                    result=self.observe(source,'build_package.py',target,['--caller-closure',str(target),'--caller-closure-bytes',str(protected['bytes']),'--caller-closure-sha256',protected['sha256']])
                    self.zero(result);self.assertIn('SEALED_CLI_IDENTITY_FORBIDDEN_BEFORE_IO',result['failure']['message'])
    def test_real_builder_main_protected_paths_refuse_before_stat(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d))
            for target in ('/tmp/65d8116b77bc0af1a108122ec28cfcea/body','/tmp/probe-root-custody-actual/another/body','/tmp/producer4-helper-probe-actual-r1/another/body'):
                self.zero(self.observe(source,'build_package.py',target,['--caller-closure',target,'--caller-closure-bytes','1','--caller-closure-sha256','a'*64]))
    def test_real_builder_main_missing_or_malformed_expected_descriptor(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d));target=Path(d)/'selected';target.write_bytes(b'{}')
            cases=[['--caller-closure',str(target)],['--caller-closure',str(target),'--caller-closure-sha256','a'*64],['--caller-closure',str(target),'--caller-closure-bytes','1'],['--caller-closure',str(target),'--caller-closure-bytes','bad','--caller-closure-sha256','a'*64],['--caller-closure',str(target),'--caller-closure-bytes','1','--caller-closure-sha256','bad']]
            for args in cases:self.zero(self.observe(source,'build_package.py',target,args))
    def test_real_builder_main_wrong_full_descriptor_refuses_before_write(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d));pin=policy['callerClosure']
            self.zero(self.observe(source,'build_package.py',pin['path'],['--caller-closure',pin['path'],'--caller-closure-bytes',str(pin['bytes']+1),'--caller-closure-sha256',pin['sha256']]))
    def test_real_builder_main_valid_descriptor_builds_only_temp_unissued_metadata(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d));pin=policy['callerClosure']
            result=self.observe(source,'build_package.py',pin['path'],['--caller-closure',pin['path'],'--caller-closure-bytes',str(pin['bytes']),'--caller-closure-sha256',pin['sha256']])
            self.assertIsNone(result['failure'],result);self.assertEqual(result['counts']['targetReadBytes'],0)
            spec=json.loads((source/'spec.UNISSUED.json').read_bytes());self.assertFalse(spec['issued']);self.assertEqual(spec['callerClosure'],pin)
            entry=json.loads((source/'entrypoint.json').read_bytes());self.assertFalse(entry['actualSourceMappingExecuted']);self.assertFalse(entry['completedBasisIssued'])
    def test_real_runner_main_rejects_seven_spec_aliases_before_io(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d));target=Path(d)/'renamed-spec';target.write_bytes(b'SYNTHETIC_NOT_OPERATIONAL_DATA')
            for protected in policy['sealedBodyDescriptors']:
                args=['--spec',str(target),'--spec-bytes',str(protected['bytes']),'--spec-sha256',protected['sha256'],'--helper-source-bytes','1','--helper-source-sha256','a'*64]
                self.zero(self.observe(source,'prepare_mapping.py',target,args))
    def test_real_runner_main_rejects_seven_code_subject_aliases_before_io(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-real-cli-') as d:
            source,policy=cli_package(Path(d));target=source/'code-subject.json';target.write_bytes(b'SYNTHETIC_NOT_OPERATIONAL_DATA')
            for protected in policy['sealedBodyDescriptors']:
                args=['--spec','/model/spec','--spec-bytes','1','--spec-sha256','a'*64,'--helper-source-bytes',str(protected['bytes']),'--helper-source-sha256',protected['sha256']]
                self.zero(self.observe(source,'prepare_mapping.py',target,args))

if __name__=='__main__':unittest.main()
