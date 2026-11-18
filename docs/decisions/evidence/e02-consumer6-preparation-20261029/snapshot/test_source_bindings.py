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
        p=self.producer();self.assertEqual(len(p['sources']),61);self.assertEqual(len({Path(d['path']).name for d in p['sources']}),61)
    def test_exact_current_source4_control260_counts(self):
        p=self.producer();self.assertEqual(sum(p['modelsDefined'].values()),260);self.assertEqual(p['selectedDefinitionCount'],260)
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
        self.assertEqual(consumer.CURRENT_PRODUCER_CONTROL_DATA['sha256'],'7381d62ad2ab8f138c00856fa22de3e796c9b6faa76a481a0bbcdbbf0b5f1f66')
        self.assertEqual(consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE['sha256'],'43ff44b93d73e217c1c7f97350e14bcba84106cb102548dd410deabda8fb61a5')
        for value in (consumer.CURRENT_HELPER_PROBE_DATA,consumer.CURRENT_HELPER_PROBE_ACCEPTANCE):self.assertIsNone(value)
    def test_pending_runtime_refuses_before_any_target_read(self):
        class NoReads:
            def doc(self,*args):raise AssertionError('TARGET_READ_BEFORE_GATE')
        with self.assertRaisesRegex(Refusal,'CONSUMER6_SOURCE_ONLY'):consumer.consume(NoReads(),{}, {})
    def test_runtime_leaf_is_unissued_unready_with_null_future_data(self):
        p=Path(__file__).with_name('runtime-gates.json');value=json.loads(p.read_text())
        self.assertEqual(set(value),set(consumer.BINDING_KEYS.split()));self.assertFalse(value['issued']);self.assertFalse(value['readiness']);self.assertIsNone(value['helperProbeData']);self.assertIsNone(value['helperProbeAcceptance'])
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

if __name__=='__main__':unittest.main()
