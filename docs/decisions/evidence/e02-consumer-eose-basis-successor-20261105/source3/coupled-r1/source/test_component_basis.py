"""Pure synthetic Source graph tests; no operational proof or filesystem fallback."""
import copy
import ast
from contextlib import contextmanager
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_adapter as p
import consumer
from strict import Refusal, equal, json_bytes, need


class MemoryFiles:
    def __init__(self):
        self.raw = {}; self.modes = {}; self.reads = []

    def put(self, path, value, mode=0o664):
        raw = value if type(value) is bytes else json_bytes(value)
        self.raw[path] = raw; self.modes[path] = mode
        return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def read(self, pin):
        need('/OPERATIONAL_' not in pin['path'], 'NO_OPERATIONAL_PROOF_READ')
        self.reads.append(pin['path'])
        raw = self.raw[pin['path']]
        equal(len(raw), pin['bytes']); equal(hashlib.sha256(raw).hexdigest(), pin['sha256'])
        return raw

    def read_mode(self, pin, expected_mode):
        equal(self.modes[pin['path']], expected_mode, 'ACTUAL_MODE_REQUIRED')
        return self.read(pin)

    def doc(self, pin):
        return json.loads(self.read(pin))


def model():
    """Return a named, reusable entirely synthetic graph plus validator arguments.

    All approval-shaped records below are synthetic test vectors, not Root
    approvals. ``save_basis`` repins mutations without touching dependencies.
    """
    f = MemoryFiles(); participants = {'/root', '/root/design', '/root/caller'}
    def put(name, value):return f.put('/model/' + name, value)
    def creators(name, schema):
        actor = '/root/' + name; participants.add(actor)
        return dict(schema=schema, author=actor, coordinator=actor,
                    sourceContributors=[actor], operators=[])
    def data(name, **values):
        actor='/root/'+name;participants.add(actor)
        return dict(authors=[actor], operators=[actor], **values)
    def reviews(name, subject, decision):
        return [put(name+'/'+role,dict(role=role,session='/root/review_'+name+'_'+role,
                    subject=subject,decision=decision)) for role in ('qa','security')]
    names=list(p._COMPONENT_NAMES)
    edges={names[0]:[names[1],names[6]], names[1]:[names[2],names[3],names[6],names[7]],
           names[2]:[names[7],names[3]], names[3]:[], names[4]:[names[5]],
           names[5]:[],names[6]:[],names[7]:[]}
    prefix=['/guard-python/lib/ld-linux-x86-64.so.2','--inhibit-cache','--library-path',
            '/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s']
    members={'bin/python3.11':dict(bytes=13,sha256='a'*64),
             'lib/ld-linux-x86-64.so.2':dict(bytes=19,sha256='b'*64)}
    members.update({f'dummy/{i}':dict(bytes=1,sha256='c'*64) for i in range(520)})
    runtime_env={'PYTHONHOME':'/guard-python','OPENSSL_CONF':'/dev/null',
                 'OPENSSL_MODULES':'/guard-python/lib/openssl-modules-disabled'}
    manifest=put('manifest',dict(fileCount=522,files=members,runtimeEntrypointPrefix=prefix,
                                 runtimeRequiredEnvironment=runtime_env))
    bodies={name: b'export const value=1;\n' for name in names}
    bodies[names[5]]=b'import os\nVALUE = 1\n'
    guard_sha=hashlib.sha256(bodies[names[5]]).hexdigest()
    runtime=['/guard-python/bin/python3.11',13,'a'*64]
    loader=['/guard-python/lib/ld-linux-x86-64.so.2',19,'b'*64]
    bodies[names[4]]=("import importlib.util\nGUARD_SHA = %r\nRUNTIME = %r\nLOADER = %r\nspec = importlib.util.spec_from_file_location('guard', '/input/lease_guard.py')\nspec.loader.exec_module(guard)\n"%
                      (guard_sha,tuple(runtime),tuple(loader))).encode()
    for name in (names[0],names[1],names[2]):
        bodies[name]=''.join("import './%s';\n"%target for target in edges[name]).encode()
    bodies[names[1]]+=("import {spawn} from 'node:child_process';\nconst GUARD_SHA = '%s';\nconst argv = %s;\nspawn('/guard-python/lib/ld-linux-x86-64.so.2',argv,{});\n"%
                      (guard_sha,json.dumps(prefix[1:]+['/input/guard-helper.py']))).encode()
    selected={side:[put(side+'/'+name,bodies[name]) for name in names] for side in ('old','new')}
    dynamic=[{'from':names[1],'kind':'PINNED_OWNED_CHILD_VIA_GUARD_PYTHON_LOADER','to':names[4]},
             {'from':names[4],'kind':'EXACT_HASH_CHECKED_DYNAMIC_IMPORT','to':names[5]}]
    host_env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    guest_env=dict(runtime_env,PATH='/usr/local/bin:/usr/bin:/bin',HOME='/tmp',TMPDIR='/tmp',
                   LANG='C.UTF-8',LC_ALL='C.UTF-8',TZ='UTC')
    removed=['ANDROID_HOME','ANDROID_SDK_ROOT','ANDROID_AVD_HOME','ANDROID_USER_HOME']
    image='sha256:'+'d'*64;guard_root='/model/guard-python'
    control_raw=''.join('%s = %r\n'%(k,v) for k,v in dict(IMAGE=image,ENV=host_env,
        GUEST_ENV=guest_env,SOURCE_NAMES=tuple(names),REMOVED_IMAGE_ENV=tuple(removed)).items()).encode()
    host_raw=("import os\nPYTHON = '/model/python'\nDOCKER = '/model/docker'\nGUARD_MANIFEST = %r\ndef exclusive(path, body):\n    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)\n"%manifest).encode()
    runtime_sources=[put('controller/'+name,body) for name,body in
                     [('controller.py',control_raw),('host.py',host_raw),('finite_child.py',b'pass\n')]]
    boundary=dict(controllerRuntimeSources=runtime_sources,guardManifest=manifest,guardRoot=guard_root,
       guardMemberCount=522,image=image,sourceModes={name:0o664 for name in names},
       hostEnvironment=host_env,guestExplicitEnvironment=guest_env,removedImageEnvironmentKeys=removed,
       tools=dict(python=dict(path='/model/python'),docker=dict(path='/model/docker')),
       dynamicExecutionEdges=dynamic,localImportEdges=edges,helperStagingMode='0o600')
    plans={side:put(side+'/control-plan',dict(synthetic=True,side=side)) for side in ('old','new')}
    sources={}; configs={}
    for side,total in [('old',266),('new',286)]:
        all_sources=selected[side]+[put(side+'/dummy%d.py'%i,b'pass\n') for i in range(56)]
        runtime22=all_sources[1:23]
        configs[side]={role:put(side+'/'+role,dict(ordinaryRole=role,sourceAndDependencyPins=runtime22,
             guardBundleRoot=guard_root,guardBundleInventory=manifest,runtimeImage=image)) for role in ('incoming','archive')}
        source=creators(side+'_source','e02-ordinary-producer4-source-subject-v1')
        source.update(sourceRevision='ORIGINAL' if side=='old' else 'FIXTURE_EOSE_QUEUE_CALLER_R1',
            sources=all_sources,sourceCount=64,runtimeSources=runtime22,runtimeSourceCount=22,
            selectedDefinitionCount=total, selectedCountsSeparate=p._COMPONENT_COUNTS[:10 if side=='old' else 11],
            configurations=configs[side],controlPlan=plans[side])
        sources[side]=put(side+'/source',source)
    all_control={}
    for side,total in [('old',266),('new',286)]:
        source=sources[side];counts=p._COMPONENT_COUNTS[:10 if side=='old' else 11]
        source_accept=put(side+'/source-root',dict(actor='/root',subject=source,modelsDefined=total,
            runtimeWorkerCount=22,modelsExecuted=0,runtimeReady=False,runtimeReleased=False))
        actor='/root/'+side+'_capture';participants.add(actor)
        capture=put(side+'/capture',dict(schema='e02-producer4-control-capture-code-subject-v1',
                        producerSource=source,authors=[actor]))
        capture_accept=put(side+'/capture-root',dict(actor='/root',subject=capture))
        admission_data=put(side+'/admission',data(side+'_admission',
             schema='e02-producer4-capture-admission-data-subject-v1',producerSource=source,captureSource=capture))
        admission_accept=put(side+'/admission-root',dict(actor='/root',subject=admission_data))
        joins=dict(producerSource=source,producerSourceAcceptance=source_accept,countsSeparate=counts,
             captureSource=capture,captureSourceAcceptance=capture_accept,admissionDataAcceptance=admission_accept)
        control=put(side+'/control',data(side+'_control',schema='e02-producer4-current-control-data-subject-v1',**joins))
        control_accept=put(side+'/control-root',dict(schema='e02-root-producer4-current-control-data-acceptance-v1',
            actor='/root',subject=control,modelsExecuted=total,modelsPassed=total,modelsFailed=0,helperExecutions=0,
            ordinaryRoleExecutions=0,ordinaryRowsQualified=0,runtimeAuthorized=False,executionAuthorized=False,**joins))
        all_control[side]=dict(producerSource=source,producerSourceAcceptance=source_accept,
           producerData=control,producerDataAcceptance=control_accept,producerCaptureSource=capture,
           producerCaptureSourceAcceptance=capture_accept,producerAdmissionDataAcceptance=admission_accept)
    constants_actor='/root/constants';participants.add(constants_actor)
    constants=put('controller/constants',dict(schema='e02-one-cid-helper-probe-constants-v1',
        acceptedProducerSubject=sources['old'],producerModelsDefined=266,removedImageEnvironmentKeys=removed,
        source8=selected['old'],sourceModes=boundary['sourceModes'],sourceContributors=[constants_actor]))
    boundary['controllerConstants']=constants
    controller=creators('controller_source','e02-one-cid-helper-probe-controller-source-v1')
    controller.update(upstreamProducerSubject=sources['old'],upstreamProducerModelsDefined=266,
        upstreamProducerRuntimeWorkerCount=22,constants=constants,runtimeSources=runtime_sources,guestProbeSources=selected['old'])
    controller_pin=put('controller/source',controller)
    controller_data=put('controller/control',data('controller_control'))
    controller_triple=dict(controllerSource=controller_pin,
        controllerSourceAcceptance=put('controller/source-root',dict(actor='/root',subject=controller_pin)),
        controllerControlDataAcceptance=put('controller/control-root',dict(actor='/root',subject=controller_data)))
    method=put('method/source',creators('method_source','e02-helper-current178-source-subject-v1'))
    method_data=put('method/control',data('method_control'))
    method_control=put('method/control-root',dict(actor='/root',subject=method_data))
    def operational(name):return dict(path='/model/OPERATIONAL_'+name,bytes=1,sha256='e'*64)
    root_subject=operational('S18')
    root_pins=dict(subject=root_subject,producerSource=sources['old'],
        producerDataAcceptance=all_control['old']['producerDataAcceptance'],**controller_triple)
    root_pins.update({name:operational(name) for name in ('rootRelease','concretePlan','execution',
                     'rawArtifactManifest','collectorSource','collectorSourceAcceptance','collectorControlDataAcceptance')})
    root_literals=dict(schema='synthetic-root24',actor='/root',decision='synthetic',helperExecutions=1,
        ordinaryRowsQualified=0,executionAuthorized=False,runtimeAuthorized=False,scope='synthetic',
        helperQualified=True,backendCause='UNKNOWN')
    root_reviews=reviews('helper',root_subject,'ACCEPT_ONE_CURRENT_HELPER_PROBE_DATA_ONLY')
    root=put('helper-root24',dict(root_literals,**root_pins,reviews=root_reviews))
    original=dict(boundary=boundary,controller=controller_triple,producer=all_control['old'],
        helperDataAcceptance=root,helperMethodSource=method,helperMethodControlAcceptance=method_control,
        helperMethodSourceAcceptance=put('method/root',dict(actor='/root',subject=method)),
        helperAcceptanceContract=put('helper-contract',dict(synthetic=True)),
        helperShapeContract=put('helper-shape',dict(synthetic=True)),
        root24ExpectedLiterals=root_literals,root24ExpectedPinOperands=root_pins,root24ExpectedReviews=root_reviews)
    contract=put('contract',dict(synthetic=True))
    ordinary=dict(admissionDataAcceptance=all_control['new']['producerAdmissionDataAcceptance'],
        captureSource=all_control['new']['producerCaptureSource'],captureSourceAcceptance=all_control['new']['producerCaptureSourceAcceptance'],
        controlPlan=plans['new'],countsSeparate=list(p._COMPONENT_COUNTS),modelsDefined=286,
        producerControlAcceptance=all_control['new']['producerDataAcceptance'],producerControlData=all_control['new']['producerData'],
        producerSource=sources['new'],producerSourceAcceptance=all_control['new']['producerSourceAcceptance'])
    rows=[dict(name=name,originalPin=old,newPin=new,originalMode='0o664',newMode='0o664')
          for name,old,new in zip(names,selected['old'],selected['new'])]
    template=dict(actor='/root',actorClosure=None,contract=contract,designAuthor='/root/design',
        executionAuthorized=False,issued=False,ordinarySuccessor=None,originalBasis=original,readiness=False,
        rootDisposition=None,schema='e02-helper-component-basis-binding-v1',scope='ORIGINAL_ACCEPTED_HELPER_GUARD_COMPONENT_BASIS_ONLY',
        sourcePairs=rows,sourceReviews=None,sourceVerification=None,state='UNISSUED')
    template_pin=put('template',template);entry=put('design-entry',dict(template=template_pin))
    design_reviews=reviews('design',entry,'ACCEPT_HELPER_COMPONENT_BASIS_SOURCE_CONTRACT_ONLY')
    design=put('design-root',dict(schema='e02-root-helper-component-basis-source-contract-acceptance-v1',actor='/root',
        decision='ACCEPT_EXPLICIT_ORIGINAL_HELPER_COMPONENT_BASIS_SOURCE_CONTRACT_ONLY',unissuedTemplate=template_pin,
        contract=contract,executionAuthorized=False,helperCarryIssued=False,subject=entry,reviews=design_reviews))
    # Expected evidence is independently assembled from known synthetic facts.
    facts=dict(schema='e02-helper-component-source-verification-v1',originalProducerSource=sources['old'],
        ordinaryProducerSource=sources['new'],controllerSource=controller_pin,controllerConstants=constants,
        sourcePairs=[dict(name=name,originalPin=old,newPin=new,originalMode=0o664,newMode=0o664,
             bytes=old['bytes'],sha256=old['sha256']) for name,old,new in zip(names,selected['old'],selected['new'])],
        importBoundary=dict(localImportEdges=edges,dynamicExecutionEdges=dynamic,runtimeEntrypointPrefix=prefix,
            pythonRuntime=runtime,pythonLoader=loader,guardSha256=guard_sha),
        controllerRuntimeSources=runtime_sources,hostEnvironment=host_env,guestEnvironment=guest_env,image=image,
        guardManifest=manifest,guardMemberCount=522,guardRoot=guard_root,stagingMode=0o600,
        configurations=[dict(role=role,originalConfig=configs['old'][role],ordinaryConfig=configs['new'][role]) for role in ('incoming','archive')],
        originalBoundarySha256=hashlib.sha256(json_bytes(boundary)).hexdigest())
    basis=copy.deepcopy(template);basis.update(actorClosure=dict(schema='e02-helper-component-actor-closure-v1',
        participants=sorted(participants)),issued=True,readiness=True,ordinarySuccessor=ordinary,
        rootDisposition=design,sourceReviews=design_reviews,sourceVerification=facts,state='COMPLETED_SOURCE_COMPONENT_BASIS_ONLY')
    result=dict(files=f,basis=basis,template=template,template_pin=template_pin,design_acceptance_pin=design,
         ordinary_expected=ordinary,forbidden={'/root/caller'},participants=participants,
         selected=selected,bodies=bodies,all_control=all_control)
    def save_basis():result['descriptor']=put('basis',basis);return result['descriptor']
    result['save_basis']=save_basis;save_basis();return result


def validate_model(m):
    return p.validate_component_basis(m['files'],m['descriptor'],m['template_pin'],
        m['design_acceptance_pin'],m['ordinary_expected'],m['forbidden'])


@contextmanager
def consumer_selectors(m):
    """Bind synthetic metadata only and restore every global even on refusal."""
    expected=m['ordinary_expected']
    values={
        'CURRENT_HELPER_COMPONENT_BASIS':m['descriptor'],
        'CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE':m['template_pin'],
        'CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE':m['design_acceptance_pin'],
        'CURRENT_PRODUCER':expected['producerSource'],
        'CURRENT_PRODUCER_SOURCE_ACCEPTANCE':expected['producerSourceAcceptance'],
        'CURRENT_PRODUCER_CONTROL_DATA':expected['producerControlData'],
        'CURRENT_PRODUCER_CONTROL_ACCEPTANCE':expected['producerControlAcceptance'],
        'CURRENT_CAPTURE_SOURCE':expected['captureSource'],
        'CURRENT_CAPTURE_SOURCE_ACCEPTANCE':expected['captureSourceAcceptance'],
        'CURRENT_ADMISSION_DATA_ACCEPTANCE':expected['admissionDataAcceptance'],
        'CURRENT_SOURCE_PLAN':expected['controlPlan'],
        'CURRENT_PRODUCER_CONTROL_COUNTS':expected['countsSeparate'],
    }
    saved={key:getattr(consumer,key) for key in values}
    try:
        for key,value in values.items():setattr(consumer,key,value)
        yield saved
    finally:
        for key,value in saved.items():setattr(consumer,key,value)


class ConsumerBasisCallsiteTests(unittest.TestCase):
    def test_consumer_accepts_exact_completed_synthetic_basis(self):
        m=model()
        with consumer_selectors(m):
            self.assertEqual(consumer.ordinary_basis_expectations(),m['ordinary_expected'])
            basis,union=consumer.helper_component_basis(m['files'],m['forbidden'])
            self.assertEqual(basis,m['basis']);self.assertEqual(union,m['participants'])
        self.assertFalse(any('/OPERATIONAL_' in path for path in m['files'].reads))

    def test_consumer_null_basis_refuses_before_any_read(self):
        m=model()
        with consumer_selectors(m):
            consumer.CURRENT_HELPER_COMPONENT_BASIS=None
            with self.assertRaisesRegex(Refusal,'UNBOUND_HELPER_COMPONENT_BASIS'):
                consumer.helper_component_basis(m['files'],m['forbidden'])
        self.assertEqual(m['files'].reads,[])

    def test_consumer_unissued_basis_refuses(self):
        m=model();m['basis']['issued']=False;m['save_basis']()
        with consumer_selectors(m):
            with self.assertRaisesRegex(Refusal,'COMPONENT_UNISSUED_BASIS'):
                consumer.helper_component_basis(m['files'],m['forbidden'])

    def test_consumer_null_ordinary_authority_refuses_before_any_read(self):
        m=model()
        with consumer_selectors(m):
            consumer.CURRENT_PRODUCER_CONTROL_DATA=None
            with self.assertRaisesRegex(Refusal,'UNBOUND_ORDINARY_286_AUTHORITY'):
                consumer.helper_component_basis(m['files'],m['forbidden'])
        self.assertEqual(m['files'].reads,[])

    def reject_selector(self,key,old_key):
        m=model()
        with consumer_selectors(m):
            setattr(consumer,key,m['all_control']['old'][old_key])
            with self.assertRaisesRegex(Refusal,'COMPONENT_EXACT_ORDINARY_AUTHORITY'):
                consumer.helper_component_basis(m['files'],m['forbidden'])

    def test_consumer_changed_ordinary_producer_refuses(self):
        self.reject_selector('CURRENT_PRODUCER','producerSource')
    def test_consumer_changed_capture_source_refuses(self):
        self.reject_selector('CURRENT_CAPTURE_SOURCE','producerCaptureSource')
    def test_consumer_changed_data_subject_refuses(self):
        self.reject_selector('CURRENT_PRODUCER_CONTROL_DATA','producerData')
    def test_consumer_changed_data_acceptance_refuses(self):
        self.reject_selector('CURRENT_PRODUCER_CONTROL_ACCEPTANCE','producerDataAcceptance')

    def test_metadata_selectors_restore_on_refusal(self):
        m=model();before=consumer.CURRENT_PRODUCER
        with consumer_selectors(m):
            consumer.CURRENT_HELPER_COMPONENT_BASIS=None
            with self.assertRaises(Refusal):consumer.helper_component_basis(m['files'],m['forbidden'])
        self.assertIs(consumer.CURRENT_PRODUCER,before)

    def test_consumer_strict_controller_call_uses_original_basis_producer(self):
        # Inspect the real call rather than replacing either authority validator.
        tree=ast.parse(Path(consumer.__file__).read_bytes())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='control_actor_union')
        calls=[n for n in ast.walk(function) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute) and n.func.attr=='validate_controller_authority']
        self.assertEqual(len(calls),1)
        self.assertEqual(ast.dump(calls[0].args[2]),ast.dump(ast.parse("original['producer']['producerSource']",mode='eval').body))

    def test_strict_controller_source_profile_requires_original_producer(self):
        m=model();f=m['files'];original=m['basis']['originalBasis'];source=f.doc(original['controller']['controllerSource'])
        # A Source-only synthetic one-method partition. It is parsed, never run.
        cwd='/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r10'
        test_pin=f.put(cwd+'/synthetic_test.py',b'class Synthetic:\n    def test_partition(self): pass\n')
        group=dict(name='synthetic',source=test_pin,format='VERBOSE_UNITTEST_NAMED',
            argv=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',test_pin['path']],
            cwd=cwd,count=1,expectedNames=['Synthetic.test_partition'])
        plan=f.put('/model/strict-controller-plan',dict(schema='e02-one-cid-helper-probe-controller-controls-v1',groups=[group]))
        source.update(sources=source['runtimeSources']+source['guestProbeSources']+[test_pin],sourceCount=12,
            runtimeSourceCount=3,guestProbeSourceCount=8,controlPlan=plan,version='r10',modelsDefined=1,
            modelGroups=1,modelsExecuted=0,helperExecutions=0,probeExecutions=0)
        descriptor=f.put('/model/strict-controller-source',source)
        observed,_,counts,total=p.controller_profile(f,descriptor,original['producer']['producerSource'])
        self.assertEqual(observed['upstreamProducerModelsDefined'],266)
        self.assertEqual((counts,total),([1],1))
        with self.assertRaises(Refusal):p.controller_profile(f,descriptor,m['ordinary_expected']['producerSource'])


class ComponentBasisTests(unittest.TestCase):
    def reject(self,change):
        m=model();change(m);m['save_basis']()
        with self.assertRaises((Refusal,KeyError,TypeError,ValueError)):validate_model(m)

    def test_complete_source_basis_and_exact_actor_union(self):
        m=model();basis,union=validate_model(m)
        self.assertEqual(basis,m['basis']);self.assertEqual(union,m['participants'])
        self.assertFalse(any('/OPERATIONAL_' in path for path in m['files'].reads))
        for pins in m['selected'].values():
            self.assertTrue(all(pin['path'] in m['files'].reads for pin in pins))

    def test_unissued_basis(self):self.reject(lambda m:m['basis'].update(issued=False))
    def test_unready_basis(self):self.reject(lambda m:m['basis'].update(readiness=False))
    def test_execution_authorized(self):self.reject(lambda m:m['basis'].update(executionAuthorized=True))
    def test_wrong_state(self):self.reject(lambda m:m['basis'].update(state='UNISSUED'))
    def test_extra_top_level_field(self):self.reject(lambda m:m['basis'].update(bindingSchema='v1'))
    def test_root_actor_required(self):self.reject(lambda m:m['basis'].update(actor='/root/other'))
    def test_original_basis_cannot_be_recast(self):self.reject(lambda m:m['basis']['originalBasis']['producer'].update(producerSource=m['ordinary_expected']['producerSource']))
    def test_null_ordinary_pin(self):self.reject(lambda m:m['ordinary_expected'].update(captureSource=None))
    def test_old_producer_cannot_be_ordinary(self):self.reject(lambda m:m['ordinary_expected'].update(producerSource=m['all_control']['old']['producerSource']))
    def test_mixed_control_acceptance(self):self.reject(lambda m:m['ordinary_expected'].update(producerControlAcceptance=m['all_control']['old']['producerDataAcceptance']))
    def test_ordinary_count_bool(self):self.reject(lambda m:m['ordinary_expected'].update(modelsDefined=True))
    def test_ordinary_ten_groups(self):self.reject(lambda m:m['ordinary_expected'].update(countsSeparate=p._COMPONENT_COUNTS[:-1]))
    def test_missing_eighth_pair(self):self.reject(lambda m:m['basis']['sourcePairs'].pop())
    def test_duplicate_pair(self):self.reject(lambda m:m['basis']['sourcePairs'].__setitem__(7,m['basis']['sourcePairs'][0]))
    def test_pair_order(self):self.reject(lambda m:m['basis']['sourcePairs'].reverse())
    def test_hash_only_alias(self):self.reject(lambda m:m['basis']['sourcePairs'][0]['newPin'].update(path='/model/alias/'+p._COMPONENT_NAMES[0]))
    def test_wrong_pair_hash(self):self.reject(lambda m:m['basis']['sourcePairs'][0]['newPin'].update(sha256='f'*64))
    def test_declared_mode_wrong(self):self.reject(lambda m:m['basis']['sourcePairs'][0].update(newMode='0o600'))
    def test_actual_new_mode_wrong_despite_declared_equal(self):self.reject(lambda m:m['files'].modes.update({m['selected']['new'][0]['path']:0o600}))
    def test_actual_old_mode_wrong_despite_declared_equal(self):self.reject(lambda m:m['files'].modes.update({m['selected']['old'][0]['path']:0o600}))
    def test_source_verification_not_boolean(self):self.reject(lambda m:m['basis'].update(sourceVerification=True))
    def test_recomputed_environment_not_assertion(self):self.reject(lambda m:m['basis']['sourceVerification']['guestEnvironment'].update(PYTHONHOME='/wrong'))
    def test_recomputed_mode_not_assertion(self):self.reject(lambda m:m['basis']['sourceVerification'].update(stagingMode=0o664))
    def test_actor_omission(self):self.reject(lambda m:m['basis']['actorClosure']['participants'].remove('/root/old_capture'))
    def test_actor_extra(self):self.reject(lambda m:m['basis']['actorClosure']['participants'].append('/root/unrelated'))
    def test_source_review_swapped(self):self.reject(lambda m:m['basis']['sourceReviews'].reverse())
    def test_own_disposition_pin(self):self.reject(lambda m:m['basis'].update(rootDisposition=m['descriptor']))
    def test_original_root24_governance_mutation(self):
        def change(m):
            pin=m['basis']['originalBasis']['helperDataAcceptance'];value=m['files'].doc(pin)
            value['helperExecutions']=2;m['files'].raw[pin['path']]=json_bytes(value)
        self.reject(change)
    def test_operational_bodies_are_never_available(self):
        m=model();validate_model(m)
        self.assertFalse(any('/OPERATIONAL_' in path for path in m['files'].raw))

    def test_prior_design_reviewer_cannot_be_source_creator(self):
        m=model();f=m['files'];design=f.doc(m['design_acceptance_pin'])
        review=f.doc(design['reviews'][0]);review['session']='/root/old_capture'
        design['reviews'][0]=f.put('/model/changed-design-qa',review)
        design_pin=f.put('/model/changed-design-root',design)
        m['design_acceptance_pin']=design_pin;m['basis']['rootDisposition']=design_pin
        m['basis']['sourceReviews']=design['reviews'];m['save_basis']()
        with self.assertRaisesRegex((Refusal,ValueError),'INDEPENDENT_REVIEWER'):validate_model(m)

    def test_source_creator_predecessor_is_in_union(self):
        value=dict(schema='e02-ordinary-producer4-source-subject-v1',author='/root/a',
            coordinator='/root/b',sourceContributors=['/root/c'],predecessorAuthor='/root/d')
        self.assertEqual(p._component_source_creators(value),{'/root/a','/root/b','/root/c','/root/d'})

    def import_fixture(self):
        m=model();boundary=copy.deepcopy(m['template']['originalBasis']['boundary'])
        boundary['sourcePairsByName']=dict(zip(p._COMPONENT_NAMES,m['selected']['old']))
        return m,boundary,m['files'].doc(boundary['guardManifest'])

    def reject_import(self,name,addition):
        m,boundary,manifest=self.import_fixture();bodies=copy.deepcopy(m['bodies'])
        bodies[name]+=addition
        with self.assertRaises(Refusal):p._component_import_facts(bodies,boundary,manifest)

    def test_extra_local_import_outside_eight(self):self.reject_import('guard-wire.mjs',b"import './ninth.mjs';\n")
    def test_undeclared_eighth_member_edge(self):self.reject_import('guard-wire.mjs',b"import './guard-client.mjs';\n")
    def test_dynamic_javascript_import(self):self.reject_import('guard-wire.mjs',b"await import('./guard-client.mjs');\n")
    def test_external_package_import(self):self.reject_import('guard-wire.mjs',b"import 'external-package';\n")
    def test_python_nonstdlib_import(self):self.reject_import('lease_guard.py',b'import external_package\n')
    def test_python_dynamic_builtin_import(self):self.reject_import('lease_guard.py',b"__import__('os')\n")
    def test_python_eval(self):self.reject_import('lease_guard.py',b"eval('1')\n")
    def test_python_import_module(self):self.reject_import('lease_guard.py',b"importlib.import_module('os')\n")
    def test_second_python_dynamic_execution_edge(self):self.reject_import('lease_guard.py',b"importlib.util.spec_from_file_location('x','/outside.py')\n")
    def test_runtime_manifest_hash_change(self):
        m,boundary,manifest=self.import_fixture();manifest['files']['bin/python3.11']['sha256']='f'*64
        with self.assertRaises(Refusal):p._component_import_facts(m['bodies'],boundary,manifest)
    def test_loader_prefix_change(self):
        m,boundary,manifest=self.import_fixture();manifest['runtimeEntrypointPrefix'].append('-E')
        with self.assertRaises(Refusal):p._component_import_facts(m['bodies'],boundary,manifest)


if __name__=='__main__':unittest.main()
