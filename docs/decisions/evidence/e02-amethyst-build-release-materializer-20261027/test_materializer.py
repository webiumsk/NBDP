"""PREPARED NOT EXECUTED: DATA-only clock/template/one-use refusal models."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import materialize as m


def template():
    p=dict(path='/tmp/SYNTHETIC_NOT_REAL_METADATA',bytes=1,sha256='a'*64)
    r=dict(schema='nbdp-amethyst-build-only-root-release-v1',actor='/root',executionAuthorized=True,
        scope='FIXED_AMETHYST_BUILD_ONLY',runId='1'*32,issuedAtUtcNs=None,notAfterUtcNs=None,
        supervisorSubject=copy.deepcopy(m.PINNED[2]),buildPreparationSubject=p,
        sourceReviews=[p,p],prerequisiteAcceptances=[p,p,p],sourceArchive=p,sourceArchiveReceipt=p,
        extractions={k:p for k in ('jdk','platform','build-tools','ndk')},networkId='b'*64,
        networkLabels={'nbdp.owner':'SYNTHETIC_NOT_REAL_AUTHORITY'},meaning='SYNTHETIC_MODEL_ONLY')
    return dict(schema='nbdp-amethyst-one-build-dispatch-template-v1',actor='/root',
        decision='AUTHORIZE_ONE_FIXED_AMETHYST_BUILD_DISPATCH',expectedOutput=str(m.WORK/('attempt-'+'1'*32)),release=r,metadata=[p,p,p])


class DispatchModels(unittest.TestCase):
    def test_template_shape_only_never_authenticates_origin(self):m.validate(template())
    def test_only_two_clock_fields_change_exact2400_seconds(self):
        t=template();before=copy.deepcopy(t);now=1793050000000000000
        live=m.fresh(m.validate(t),now)
        self.assertEqual(t,before)
        self.assertEqual(live['issuedAtUtcNs'],now)
        self.assertEqual(live['notAfterUtcNs']-now,2400*10**9)
        self.assertEqual({k:v for k,v in live.items() if k not in m.CLOCKS},
            {k:v for k,v in t['release'].items() if k not in m.CLOCKS})
    def test_wrong_clock_domains_refused(self):
        for now in (True,1.5,-1,0,9223372036854775807):
            with self.subTest(now=now),self.assertRaises(ValueError):m.fresh(template()['release'],now)
    def test_wrong_scope_refused(self):
        t=template();t['release']['scope']='OTHER_JOB'
        with self.assertRaises(ValueError):m.validate(t)
    def test_nonroot_authority_refused(self):
        t=template();t['actor']='/root/SYNTHETIC_OPERATOR'
        with self.assertRaises(ValueError):m.validate(t)
    def test_not_ready_template_refused(self):
        t=template();t['release']['executionAuthorized']=False
        with self.assertRaises(ValueError):m.validate(t)
    def test_unaccepted_missing_metadata_refused(self):
        t=template();t['metadata'][0]=None
        with self.assertRaises(ValueError):m.validate(t)
    def test_arbitrary_exec_field_refused(self):
        t=template();t['argv']=['/bin/sh','-c','SYNTHETIC_DO_NOT_EXECUTE']
        with self.assertRaises(ValueError):m.validate(t)
    def test_foreign_supervisor_target_refused(self):
        t=template();t['release']['supervisorSubject']['path']='/tmp/FOREIGN_SUBJECT'
        with self.assertRaises(ValueError):m.validate(t)
    def test_foreign_output_or_runid_refused(self):
        for key,value in (('expectedOutput','/tmp/FOREIGN_OUTPUT'),('runId','../escape')):
            t=template()
            if key=='runId':t['release'][key]=value
            else:t[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(t)
    def test_existing_clock_or_budget_edit_refused(self):
        for key,value in (('issuedAtUtcNs',1),('outerSeconds',9999)):
            t=template();t['release'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate(t)
    def test_duplicate_and_lossy_json_refused(self):
        for raw in (b'{"actor":"/root","actor":"other"}',b'{"x":-0}',b'{"x":1.0}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):m.load(raw)
    def test_one_use_writer_refuses_second_without_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-dispatch-once-model-') as folder:
            p=Path(folder)/'SYNTHETIC_NOT_A_GRANT';m.write_once(p,b'first')
            with self.assertRaises(FileExistsError):m.write_once(p,b'second')
            self.assertEqual(p.read_bytes(),b'first')
    def test_template_pinned_bytes_then_drift_refused(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-dispatch-pin-model-') as folder:
            p=Path(folder)/'SYNTHETIC_NOT_A_TEMPLATE';p.write_bytes(b'one')
            d=dict(path=str(p),bytes=3,sha256=hashlib.sha256(b'one').hexdigest())
            self.assertEqual(m.checked(d,keep=True),b'one');p.write_bytes(b'two')
            with self.assertRaises(ValueError):m.checked(d,keep=True)


if __name__=='__main__':unittest.main(verbosity=2)
