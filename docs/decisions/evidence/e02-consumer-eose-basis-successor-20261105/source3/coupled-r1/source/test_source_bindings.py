"""SOURCE definitions: exact current source, DTO, scope and unready gates."""
import ast,hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import consumer,wire,async_guard,observer
from strict import Refusal

class CurrentSourceBindings(unittest.TestCase):
    def producer(self):
        p=consumer.CURRENT_PRODUCER;raw=Path(p['path']).read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(p['bytes'],p['sha256']))
        return json.loads(raw)
    def test_exact_current_source4_metadata_subject(self):
        p=self.producer();self.assertEqual(p['schema'],'e02-ordinary-producer4-source-subject-v1');self.assertEqual(p['version'],'SOURCE4')
    def test_exact22_current_runtime_workers(self):
        p=self.producer();self.assertEqual(p['runtimeSourceCount'],22);self.assertEqual(p['runtimeSources'],consumer.CURRENT_WORKERS);self.assertEqual(len(consumer.CURRENT_WORKERS),22)
    def test_exact61_source_members_no_legacy31(self):
        p=self.producer();self.assertEqual(len(p['sources']),64);self.assertEqual(len({Path(d['path']).name for d in p['sources']}),64)
    def test_exact_current_source4_control260_counts(self):
        p=self.producer();self.assertEqual(sum(p['modelsDefined'].values()),286);self.assertEqual(p['selectedDefinitionCount'],286)
    def test_all22_exact_bytes_declared(self):
        for p in consumer.CURRENT_WORKERS:
            raw=Path(p['path']).read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(p['bytes'],p['sha256']))
    def test_current_profile_matches_actual_supervisor(self):
        p=next(p for p in consumer.CURRENT_WORKERS if Path(p['path']).name=='supervisor.py')
        values={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(Path(p['path']).read_text()).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('SCOPE','PROFILE')}
        self.assertEqual(values,dict(SCOPE=consumer.RUNTIME_SCOPE,PROFILE=wire.PROFILE))
    def test_both_configs_bind22_workers_and_original1800(self):
        for p in consumer.CURRENT_CONFIGURATIONS:
            d=json.loads(Path(p['path']).read_text());self.assertEqual(d['sourceAndDependencyPins'],consumer.CURRENT_WORKERS);self.assertEqual(d['originalLeaseSeconds'],1800);self.assertEqual(d['profileId'],wire.PROFILE)
    def test_current_dto_closed22_worker_list(self):
        p=consumer.CURRENT_GUARD_DTO;d=json.loads(Path(p['path']).read_text());self.assertEqual(d['runtimeWorkerCount'],22);self.assertEqual(d['runtimeWorkerNames'],[Path(p['path']).name for p in consumer.CURRENT_WORKERS])
    def test_current_dto_original16MiB_partition(self):
        p=consumer.CURRENT_GUARD_DTO;d=json.loads(Path(p['path']).read_text());self.assertEqual(d['allocation'],async_guard.ALLOCATION);self.assertEqual(d['serviceProofLimitBytes'],observer.LIMIT)
    def test_current_export_and_guard_dto_are_distinct_operands(self):
        self.assertNotEqual(consumer.CURRENT_EXPORT_CONTRACT,consumer.CURRENT_GUARD_DTO);self.assertEqual(consumer.CONTRACT_SHA,consumer.CURRENT_EXPORT_CONTRACT['sha256']);self.assertEqual(self.producer()['typedContract'],consumer.CURRENT_GUARD_DTO)
    def test_actual260_bound_but_future_probe_data_stays_null(self):
        # Original helper authority stays on the accepted old266 producer. New
        # ordinary DATA must be genuine and is deliberately unbound in Source.
        self.assertEqual(consumer.HELPER_PRODUCER_CONTROL_ACCEPTANCE['sha256'],'91a00b4ec693c7c776a031849d61ab676ceaeed4262085ba0a6fc1b6e81b2d6f')
        self.assertNotEqual(consumer.HELPER_PRODUCER,consumer.CURRENT_PRODUCER)
        if consumer.CURRENT_PRODUCER_CONTROL_DATA is None:
            self.assertIsNone(consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE)
            with self.assertRaisesRegex(Refusal,'UNBOUND_ORDINARY_286_AUTHORITY'):consumer.ordinary_basis_expectations()
        else:
            self.assertIsNotNone(consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE)
            self.assertEqual(consumer.ordinary_basis_expectations()['modelsDefined'],286)
        for value in (consumer.CURRENT_HELPER_PROBE_DATA,consumer.CURRENT_HELPER_PROBE_ACCEPTANCE):self.assertIsNone(value)
    def test_pending_runtime_refuses_before_any_target_read(self):
        class NoReads:
            def doc(self,*args):raise AssertionError('TARGET_READ_BEFORE_GATE')
        with self.assertRaisesRegex(Refusal,'CONSUMER6_SOURCE_ONLY'):consumer.consume(NoReads(),{}, {})
    def test_runtime_leaf_is_unissued_unready_with_null_future_data(self):
        p=Path(__file__).with_name('runtime-gates.json');value=json.loads(p.read_text())
        self.assertEqual(set(value),set(consumer.BINDING_KEYS.split()));self.assertFalse(value['issued']);self.assertFalse(value['readiness']);self.assertIsNone(value['helperProbeData']);self.assertIsNone(value['helperProbeAcceptance'])
        self.assertEqual(value['schema'],'e02-consumer6-runtime-bindings-v2')
    def test_unready_external_leaf_refuses_before_prerequisite_reads(self):
        class OnlyBinding:
            def __init__(self):self.reads=0
            def doc(self,p):
                self.reads+=1
                if self.reads>1:raise AssertionError('TARGET_READ_BEFORE_READY')
                return json.loads(Path(__file__).with_name('runtime-gates.json').read_text())
        files=OnlyBinding()
        with self.assertRaisesRegex(Refusal,'UNREADY_BINDINGS'):consumer.bind_current_profile(files,{})
        self.assertEqual(files.reads,1)
    def test_current_root_data_contract_is_definition_only(self):
        p=consumer.CURRENT_DATA_ACCEPTANCE_CONTRACT;raw=Path(p['path']).read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(p['bytes'],p['sha256']));d=json.loads(raw);self.assertFalse(d['acceptanceIssued']);self.assertEqual(len(d['closedKeys']),24)

    def test_root_selected_authority_clock_is120_seconds_once(self):
        pin=consumer.CURRENT_CONSUMER_CONTROL_CLOCK_SELECTION
        raw=Path(pin['path']).read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(pin['bytes'],pin['sha256']))
        selected=json.loads(raw)
        self.assertEqual(consumer.control_clock_map(selected),consumer.CURRENT_CONTROL_SCOPE_SECONDS)
        group=dict(name='test_current_authority.py',argv=['/synthetic/python','-v'],cwd='/synthetic')
        self.assertIn('--signal=KILL 120s',consumer.current_control_request(group)['cmd'])

    def test_other_twelve_pure_group_clocks_remain63_seconds(self):
        for name in consumer.CONTROL_FILES:
            if name!='test_current_authority.py':
                group=dict(name=name,argv=['/synthetic/python','-v'],cwd='/synthetic')
                self.assertIn('--signal=KILL 63s',consumer.current_control_request(group)['cmd'])
        self.assertEqual(sum(consumer.CURRENT_CONTROL_SCOPE_SECONDS.values()),876)

    def test_clock_metadata_duplicates_omissions_substitution_and_authority_refused(self):
        original=consumer.CURRENT_CONTROL_CLOCK_SELECTION_RECORD
        candidates=[]
        value=json.loads(json.dumps(original));value['groups'][1]=value['groups'][0];candidates.append(value)
        value=json.loads(json.dumps(original));value['groups'].pop();candidates.append(value)
        value=json.loads(json.dumps(original));value['groups'][0]['outerKillSeconds']=120;candidates.append(value)
        value=json.loads(json.dumps(original));value['groups'][8]['outerKillSeconds']=63;candidates.append(value)
        value=json.loads(json.dumps(original));value['executionAuthorized']=True;candidates.append(value)
        value=json.loads(json.dumps(original));value['modelExecutionAuthorized']=True;candidates.append(value)
        for value in candidates:
            with self.assertRaises(Refusal):consumer.control_clock_map(value)

    def test_unknown_control_group_cannot_inherit_another_clock(self):
        with self.assertRaisesRegex(Refusal,'UNKNOWN_CONTROL_CLOCK_GROUP'):
            consumer.current_control_request(dict(name='unknown.py',argv=[],cwd='/synthetic'))

if __name__=='__main__':unittest.main()
