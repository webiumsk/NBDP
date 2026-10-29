"""SOURCE-only model prerequisite records; no real probe/Root approval is created."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
import consumer
from strict import Files,Refusal,json_bytes
from test_parent_allocation import MemoryFiles
from probe_adapter import validate,expected_request

class ModelFiles(MemoryFiles):
    def verify_raw(self,p):return len(self.read(p))

def model():
    f=ModelFiles()
    def put(name,v):return f.put('/model/'+name,v)
    contracts={}
    for key,p in [('acceptance',consumer.CURRENT_HELPER_PROBE_ACCEPTANCE_CONTRACT),('shape',consumer.CURRENT_HELPER_PROBE_SHAPE_CONTRACT)]:contracts[key]=put(key+'-contract.json',json.loads(Path(p['path']).read_text()))
    producer=put('producer.json',dict(marker='MODEL_NOT_ACTUAL'));producer_accept=put('producer-acceptance.json',dict(marker='MODEL_NOT_ACTUAL'))
    source=put('controller-source.json',dict(schema='e02-one-cid-helper-probe-controller-source-v1',author='/root/model-code',operators=['/root'],sourceContributors=['/root/model-code'],runtimeSourceCount=3,guestProbeSourceCount=8,upstreamProducerSubject=producer,runtimeSources=[dict(path='/model/source/'+n,bytes=1,sha256='a'*64) for n in ('host.py','controller.py','finite_child.py')]))
    prerequisite=put('prerequisite-subject.json',dict(authors=['/root/model-code'],operators=['/root'],marker='MODEL_NOT_ACTUAL'))
    acceptance=put('prerequisite-acceptance.json',dict(actor='/root',subject=prerequisite))
    plan=put('concrete-plan.json',dict(runId='1'*32,creationNonce='2'*32))
    release=put('release.json',dict(schema='e02-one-cid-helper-probe-root-release-v1',actor='/root',executionAuthorized=True,subject=source,plan=plan,runId='1'*32,creationNonce='2'*32,outerCustodyReservationBytes=65536,authors=['/root'],operators=['/root']))
    result=put('result.json',dict(schema='e02-one-cid-helper-probe-result-v1',qualified=True,error=None,secondaryErrors=[],cid='3'*64,cleanup=dict(removed=True,absence=True,unknownIdentity=False),chargedPhysicalBytes=dict(attached=1000,metadata=68000),childEvidence='ACTUAL_HOST_POPEN_ONLY',outerApiEvidence=None,ordinaryRowsQualified=0,backendCause='UNKNOWN'))
    data=dict(schema='e02-one-cid-helper-probe-data-subject-v1',authors=['/root/model-author'],operators=['/root'],producerSource=producer,producerDataAcceptance=producer_accept,controllerSource=source,controllerSourceAcceptance=acceptance,controllerControlDataAcceptance=acceptance,collectorSourceAcceptance=acceptance,collectorControlDataAcceptance=acceptance,rootRelease=release,concretePlan=plan,execution=result,qualified=True,ordinaryRowsQualified=0,backendCause='UNKNOWN')
    request=expected_request(data,f.doc(source))
    origin=put('original-api.json',dict(schema='e02-actual-tool-custody-v1',operator='/root',launch=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(chunk_id='MODEL_ONLY_NOT_A_REAL_TOOL_RETURN',wall_time_seconds=0.1,exit_code=0,output='')),polls=[]))
    manifest=put('raw-manifest.json',dict(schema='e02-one-cid-helper-probe-raw-manifest-v1',files=[result,origin],originalToolOrigin=origin,accounting=dict(controllerChargedBytes=dict(attached=1000,metadata=68000+result['bytes']),rootExternalReservationBytes=65536)))
    data.update(originalToolOrigin=origin,rawArtifactManifest=manifest);subject=put('subject.json',data)
    reviews=[put(role+'-review.json',dict(role=role,session='/root/model-independent-'+role,decision='ACCEPT_ONE_CURRENT_HELPER_PROBE_DATA_ONLY',subject=subject)) for role in ('qa','security')]
    c=f.doc(contracts['acceptance']);ack=dict(c['literals'],subject=subject,reviews=reviews)
    for key in c['pinKeys']:
        if key!='subject':ack[key]=data[key]
    root=put('root-acceptance.json',ack)
    return f,dict(subject=subject,acceptance=root),SimpleNamespace(forbidden={'/root/model-consumer'}),producer,producer_accept,contracts['acceptance'],contracts['shape']

class ProbePrerequisiteModels(unittest.TestCase):
    def replace(self,g,key,mutate):
        f,nodes=g[:2];data=f.doc(nodes['subject']);old=copy.deepcopy(data[key]);value=f.doc(old);mutate(value)
        data[key]=f.put(old['path'],value)
        if key in ('execution','originalToolOrigin'):
            manifest=f.doc(data['rawArtifactManifest'])
            manifest['files']=[data[key] if p['path']==old['path'] else p for p in manifest['files']]
            if key=='originalToolOrigin':manifest['originalToolOrigin']=data[key]
            if key=='execution':manifest['accounting']['controllerChargedBytes']['metadata']=value['chargedPhysicalBytes']['metadata']+data[key]['bytes']
            data['rawArtifactManifest']=f.put(data['rawArtifactManifest']['path'],manifest)
        nodes['subject']=f.put(nodes['subject']['path'],data)
        ack=f.doc(nodes['acceptance']);ack['subject']=nodes['subject']
        contract=f.doc(g[5])
        for field in contract['pinKeys']:
            if field!='subject':ack[field]=data[field]
        for p in ack['reviews']:
            review=f.doc(p);review['subject']=nodes['subject'];replacement=f.put(p['path'],review);p.update(replacement)
        nodes['acceptance']=f.put(nodes['acceptance']['path'],ack)
    def refuse(self,key,mutate):
        g=model();self.replace(g,key,mutate)
        with self.assertRaises((Refusal,ValueError)):validate(*g)
    def test_positive_closed18_root24_manifest4_model(self):self.assertTrue(validate(*model())['qualified'])
    def test_failed_inner_probe_not_qualified(self):self.refuse('execution',lambda v:v.update(qualified=False))
    def test_missing_exact_owned_cleanup(self):self.refuse('execution',lambda v:v['cleanup'].update(absence=False))
    def test_unknown_cleanup_identity(self):self.refuse('execution',lambda v:v['cleanup'].update(unknownIdentity=True))
    def test_helper_result_no_backend_cause_inference(self):self.refuse('execution',lambda v:v.update(backendCause='RELAY'))
    def test_helper_result_no_ordinary_row(self):self.refuse('execution',lambda v:v.update(ordinaryRowsQualified=1))
    def test_actual_host_scope_not_api_lifecycle_inference(self):self.refuse('execution',lambda v:v.update(outerApiEvidence='FAKE_INNER_REAP'))
    def test_manifest_has_no_generic_extra_graph(self):self.refuse('rawArtifactManifest',lambda v:v.update(dependencies=[]))
    def test_manifest_duplicate_members(self):self.refuse('rawArtifactManifest',lambda v:v['files'].append(v['files'][0]))
    def test_reservation_stays_inside_metadata(self):self.refuse('rawArtifactManifest',lambda v:v['accounting'].update(rootExternalReservationBytes=131072))
    def test_metadata_share_not_expanded(self):self.refuse('rawArtifactManifest',lambda v:v['accounting']['controllerChargedBytes'].update(metadata=8388609))
    def test_attached_share_not_expanded(self):self.refuse('rawArtifactManifest',lambda v:v['accounting']['controllerChargedBytes'].update(attached=8388609))
    def test_raw_member_expected_hash_is_checked(self):
        g=model();f,nodes=g[:2];data=f.doc(nodes['subject']);manifest=f.doc(data['rawArtifactManifest']);f.raw[manifest['files'][0]['path']]+=b'bad'
        with self.assertRaises((Refusal,ValueError)):validate(*g)
    def test_api_nonnatural_exit_refuses(self):self.refuse('originalToolOrigin',lambda v:v['launch']['unmodifiedResponse'].update(exit_code=2))
    def test_wrong_outer_controller_request(self):self.refuse('originalToolOrigin',lambda v:v['launch']['actualArguments'].update(cmd='wrong'))
    def test_pending_probe_anchor_hard_refuses(self):
        g=list(model());g[1]=dict(subject=None,acceptance=None)
        with self.assertRaises(Refusal):validate(*g)

class ExplicitRawStreamControls(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.files=Files([str(self.root)])
    def tearDown(self):self.temp.cleanup()
    def pin(self,raw=b'opaque raw bytes'):
        p=self.root/'proof.raw';p.write_bytes(raw);return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    def test_positive_explicit_raw_stream_and_recheck(self):
        p=self.pin();self.assertEqual(self.files.verify_raw(p),p['bytes']);self.files.recheck()
    def test_raw_hash_substitution_refused(self):
        p=self.pin();p['sha256']='a'*64
        with self.assertRaises(Refusal):self.files.verify_raw(p)
    def test_raw_file_drift_on_recheck(self):
        p=self.pin();self.files.verify_raw(p);Path(p['path']).write_bytes(b'changed')
        with self.assertRaises(Refusal):self.files.recheck()
    def test_raw_symlink_refused(self):
        p=self.pin();link=self.root/'linked';link.symlink_to(p['path']);p['path']=str(link)
        with self.assertRaises(OSError):self.files.verify_raw(p)
    def test_raw_above2GiB_refused_before_open(self):
        p=self.pin();p['bytes']=2147483649
        with self.assertRaises(Refusal):self.files.verify_raw(p)
    def test_raw_path_is_not_an_implicit_json_parse(self):
        p=self.pin(b'not JSON \xff\x00');self.assertEqual(self.files.verify_raw(p),p['bytes'])
        with self.assertRaises((Refusal,UnicodeError,ValueError)):self.files.doc(p)

if __name__=='__main__':unittest.main()
