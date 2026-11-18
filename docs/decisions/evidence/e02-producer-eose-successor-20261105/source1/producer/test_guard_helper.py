"""Pure helper request/source/check-dispatch definitions, no live child/lease."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('producer4_source_helper',Path(__file__).with_name('guard-helper.py'))
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)


class HelperProtocol(unittest.TestCase):
    def request(self,**patch):
        q=dict(schema='e02-fresh-guard-request-v1',operation='CHECK',instance='1'*32,runId='2'*32,leaseSha256='3'*64,sequence='1',label='fixed:point',contextSha256='4'*64)
        q.update(patch);return (json.dumps(q,separators=(',',':'))+'\n').encode()

    def parse(self,raw,previous=0):return helper.validate_request(raw,'1'*32,'2'*32,'3'*64,previous)

    def test_exact_check_and_close_domains(self):
        for operation in ['CHECK','CLOSE']:self.assertEqual(self.parse(self.request(operation=operation))['operation'],operation)

    def test_foreign_context_identity_schema_and_operation(self):
        for field,value in [('schema','other'),('operation','EXEC'),('instance','f'*32),('runId','f'*32),('leaseSha256','f'*64),('contextSha256','not-a-hash'),('label','/arbitrary/path')]:
            with self.subTest(field=field),self.assertRaises(ValueError):self.parse(self.request(**{field:value}))

    def test_extra_missing_typed_fields(self):
        for patch in [dict(extra='unknown'),dict(sequence=1),dict(label=True)]:
            with self.assertRaises(ValueError):self.parse(self.request(**patch))
        q=json.loads(self.request());del q['label']
        with self.assertRaises(ValueError):self.parse((json.dumps(q)+'\n').encode())

    def test_sequence_never_duplicate_decrease_wrap_or_skip(self):
        for previous,sequence in [(1,'1'),(2,'1'),(0,'2'),(9007199254740990,'9007199254740991')]:
            with self.subTest(sequence=sequence),self.assertRaises(ValueError):self.parse(self.request(sequence=sequence),previous)

    def test_complete_bounded_utf8_line(self):
        for raw in [b'',self.request()[:-1],b'\xff\n',b'x'*1024+b'\n',self.request()+b'{}\n']:
            with self.subTest(raw=raw[:20]),self.assertRaises((ValueError,UnicodeError)):self.parse(raw)

    def test_duplicate_negative_zero_nonfinite_fraction_refused(self):
        for raw in [b'{"x":"a","x":"b"}\n',b'{"x":-0}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b'{"x":0.1}\n']:
            with self.assertRaises(ValueError):self.parse(raw)

    def test_one_fresh_call_per_check_same_lease_instance(self):
        class Lease:
            def __init__(self):self.calls=0
            def check(self):self.calls+=1;return dict(Utc=100+self.calls,Mono=100+self.calls,Boot=100+self.calls,bootId='boot')
        lease=Lease();source_checks=[]
        for previous in range(3):
            raw=self.request(sequence=str(previous+1));q=self.parse(raw,previous)
            reply=helper.reply_for(q,raw,lease,lambda:source_checks.append(True))
            self.assertEqual(reply['clocks']['Boot'],str(101+previous));self.assertEqual(reply['requestSha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(lease.calls,3);self.assertEqual(len(source_checks),3)

    def test_source_drift_prevents_core_and_reply(self):
        calls=[]
        class Lease:
            def check(self):calls.append('FORBIDDEN');return {}
        def changed():raise ValueError('source changed')
        raw=self.request()
        with self.assertRaisesRegex(ValueError,'source changed'):helper.reply_for(self.parse(raw),raw,Lease(),changed)
        self.assertEqual(calls,[])

    def test_core_denial_produces_no_ok_reply_or_reused_success(self):
        class Lease:
            def __init__(self):self.calls=0
            def check(self):
                self.calls+=1
                if self.calls==2:raise ValueError('original core denial')
                return dict(Utc=100,Mono=100,Boot=100,bootId='boot')
        lease=Lease();raw=self.request();self.assertTrue(helper.reply_for(self.parse(raw),raw,lease,lambda:None)['ok'])
        raw=self.request(sequence='2')
        with self.assertRaisesRegex(ValueError,'core denial'):helper.reply_for(self.parse(raw,1),raw,lease,lambda:None)
        self.assertEqual(lease.calls,2)

    def test_close_is_not_an_authorization_check(self):
        class Lease:
            def check(self):raise AssertionError('CLOSE cannot authorize later work')
        raw=self.request(operation='CLOSE');reply=helper.reply_for(self.parse(raw),raw,Lease(),lambda:None)
        self.assertIsNone(reply['clocks']);self.assertEqual(reply['operation'],'CLOSE')


if __name__=='__main__':unittest.main()
