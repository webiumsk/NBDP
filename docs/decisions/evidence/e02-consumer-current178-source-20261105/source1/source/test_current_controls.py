"""SOURCE definitions: current Root266 closed metadata and retained real DATA.

The one current DATA read below is a planned future read-only consumer control,
not another execution of the266 producer models or a helper/ordinary run.
"""
import copy,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
import consumer
from current_controls import root_acceptance,validate_data,review_pair
from strict import Refusal,Files
from test_parent_allocation import MemoryFiles


def fixture():
    contract=json.loads(Path(consumer.CURRENT_DATA_ACCEPTANCE_CONTRACT['path']).read_text())
    def pin(key):return dict(path='/model/'+key,bytes=1,sha256='a'*64)
    data={key:pin(key) for key in contract['pinKeys'] if key!='subject'}
    value=dict(contract['literals'],subject=pin('subject'),reviews=[pin('qa'),pin('security')],**data)
    return contract,data,value

class CurrentControlAuthorityModels(unittest.TestCase):
    def refuse(self,change):
        contract,data,value=fixture();change(value)
        with self.assertRaises(Refusal):root_acceptance(value,contract,value.get('subject'),data)
    def test_positive_exact_closed24_root_shape(self):
        c,d,v=fixture();self.assertEqual(root_acceptance(v,c,v['subject'],d),v)
    def test_legacy_a_b_split_not_current_data(self):self.refuse(lambda v:v.update(schema='e02-producer3-data-acceptance-v1'))
    def test_root_actor_must_be_actual_root(self):self.refuse(lambda v:v.update(actor='/root/implementer'))
    def test_root_decision_scope_not_runtime_grant(self):self.refuse(lambda v:v.update(executionAuthorized=True))
    def test_models259_not_all260(self):self.refuse(lambda v:v.update(modelsPassed=259))
    def test_one_failed_model_is_not_current_pass(self):self.refuse(lambda v:v.update(modelsFailed=1))
    def test_boolean_not_integer_count(self):self.refuse(lambda v:v.update(modelsFailed=False))
    def test_missing_scope_partition(self):self.refuse(lambda v:v.update(countsSeparate=v['countsSeparate'][:-1]))
    def test_wrong_source4_source_pin(self):self.refuse(lambda v:v.update(producerSource=dict(v['producerSource'],sha256='b'*64)))
    def test_helper_execution_not_in_pure_model_scope(self):self.refuse(lambda v:v.update(helperExecutions=1))
    def test_no_ordinary_rows_from_pure_controls(self):self.refuse(lambda v:v.update(ordinaryRowsQualified=1))
    def test_extra_self_approval_key_refused(self):self.refuse(lambda v:v.update(selfApproved=True))
    def test_review_pair_author_cannot_review_own_data(self):
        f=MemoryFiles();subject=dict(path='/model/subject',bytes=1,sha256='a'*64);pins=[]
        for role,session in [('qa','/root/author'),('security','/root/independent')]:pins.append(f.put('/model/'+role,dict(role=role,session=session,decision='DATA',subject=subject)))
        with self.assertRaises(ValueError):review_pair(f,pins,subject,'DATA',{'/root/author'})
    def test_review_pair_exact_role_order(self):
        f=MemoryFiles();subject=dict(path='/model/subject',bytes=1,sha256='a'*64);pins=[]
        for role in ('security','qa'):pins.append(f.put('/model/'+role,dict(role=role,session='/root/'+role,decision='DATA',subject=subject)))
        with self.assertRaises(ValueError):review_pair(f,pins,subject,'DATA',set())
    def test_exact_actual_current260_retained_data_consumer(self):
        files=Files(['/Data/nbdp-e02-tooling-20261027','/home/peterhorvath/apps/bitcoin/NBDP','/tmp/nbdp-e02-minimal-rs-v7','/home/peterhorvath/.nvm','/home/peterhorvath/.miniforge3','/usr/bin'])
        origin=SimpleNamespace(forbidden=set(consumer.CURRENT_CONTROL_ACTORS))
        data=validate_data(files,dict(subject=consumer.CURRENT_PRODUCER_CONTROL_DATA,acceptance=consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE),origin,consumer.CURRENT_PRODUCER,consumer.CURRENT_PRODUCER_SOURCE_ACCEPTANCE,consumer.CURRENT_CAPTURE_SOURCE,consumer.CURRENT_CAPTURE_SOURCE_ACCEPTANCE,consumer.CURRENT_ADMISSION_DATA_ACCEPTANCE,consumer.CURRENT_DATA_ACCEPTANCE_CONTRACT)
        self.assertEqual(data['countsSeparate'],[129,33,29,16,20,10,11,8,7,3]);files.recheck()

    def test_whole_legacy260_root_acceptance_cannot_qualify266(self):
        contract,data,current=fixture()
        legacy=json.loads(Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-260-control-actual-20261029/acceptance.json').read_bytes())
        with self.assertRaises(Refusal):root_acceptance(legacy,contract,current['subject'],data)
    def test_legacy260_partition_with_current266_totals_refused(self):
        self.refuse(lambda value:value.update(countsSeparate=[123,33,29,16,20,10,11,8,7,3]))
    def test_models265_not_all266(self):
        self.refuse(lambda value:value.update(modelsPassed=265))
    def test_current266_mixed_legacy_producer_source_refused(self):
        self.refuse(lambda value:value.update(producerSource=dict(path='/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r4-source4-metadata-r1/subject.json',bytes=30532,sha256='34802f702c863e5cd81e865eec5de7736615ceffc683a8a9f9eb4192e857e66e')))
    def test_current266_cannot_join_legacy_data_subject(self):
        contract,data,value=fixture()
        legacy=dict(path='/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-95487249f27a7187a4cbced6c9d4aa0e/assembled/subject.json',bytes=3350,sha256='7381d62ad2ab8f138c00856fa22de3e796c9b6faa76a481a0bbcdbbf0b5f1f66')
        with self.assertRaises(Refusal):root_acceptance(value,contract,legacy,data)
    def test_current266_mixed_legacy_capture_source_refused(self):
        self.refuse(lambda value:value.update(captureSource=dict(path='/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r1/source4/code-subject.json',bytes=4759,sha256='eff0594e20268670588e03948dd6bc7f9b14a6b91b55e7eb11e9ad11fe61e822')))
    def test_current266_mixed_legacy_admission_acceptance_refused(self):
        self.refuse(lambda value:value.update(admissionDataAcceptance=dict(path='/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-capture-admission21-canonical-r1-20261028/acceptance.json',bytes=1955,sha256='5c2cd0767fba10bf5196591887db61aa54566cec24ebe7cda38e248680ed9700')))

if __name__=='__main__':unittest.main()
