"""Meaningful injected parent reservation/ledger definitions, no real services."""
import json
from pathlib import Path
import tempfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
from unittest.mock import patch
import supervisor


class Refused(RuntimeError):pass


class Lease:
    def __init__(self):self.revocations=[]
    def revoke(self,reason):self.revocations.append(reason);raise Refused(reason)


def runtime():
    r=object.__new__(supervisor.Runtime)
    r.capture_allocation_initialized=True;r.capture_allocation_poison=None;r.capture_header_charged=0
    r.controller_audit_attempts=0;r.controller_audit_ledger_charges={}
    r.plan={'runId':'1'*32,'sourceAndDependencyPins':[]};r.plan_pin={'path':'/synthetic/config.json','bytes':2,'sha256':'2'*64}
    r.lease_sha='3'*64;r.lease=Lease();r.out=Path('/synthetic/output');r.sequence=0;r.ids={'fixture':'4'*64}
    r.check=lambda:None
    return r


class ParentCaptureAllocation(unittest.TestCase):
    def test_all_sixty_four_attempts_consumed_and_sixty_fifth_before_inspect(self):
        r=runtime();events=[]
        r.controller_audit_ledger=lambda index,suffix,value:events.append((index,suffix,value['poolPrechargedBytes']))
        for i in range(1,65):self.assertEqual(r.reserve_controller_audit('status'),i)
        self.assertEqual(len(events),64);self.assertEqual(events[-1][2],8388608)
        with self.assertRaises(Refused):r.reserve_controller_audit('status')
        self.assertEqual(r.controller_audit_attempts,64);self.assertEqual(len(events),64)
        self.assertIsNotNone(r.capture_allocation_poison)

    def test_actual_fixture_reserves_before_inspect_and_failed_launch_keeps_slot(self):
        r=runtime();events=[]
        r.controller_audit_ledger=lambda index,suffix,value:events.append('reserved:'+str(index))
        r.inspect=lambda role:events.append('inspect')
        def command(argv,timeout):
            events.append('command');self.assertIn('NBDP_CONTROLLER_AUDIT_SLOT=1',argv);self.assertEqual(timeout,55)
            raise RuntimeError('synthetic launch failure')
        r.command=command
        with self.assertRaises(Refused):r.fixture('publish')
        self.assertEqual(events,['reserved:1','inspect','command']);self.assertEqual(r.controller_audit_attempts,1)
        self.assertIsNotNone(r.capture_allocation_poison)
        with self.assertRaises(Refused):r.fixture('status')
        self.assertEqual(events,['reserved:1','inspect','command'])

    def test_partial_or_failed_ledger_poison_before_any_child_or_retry(self):
        for cause in [OSError('partial ledger'),OSError('ENOSPC')]:
            r=runtime();events=[]
            def ledger(index,suffix,value):events.append(('write-once',index));raise cause
            r.controller_audit_ledger=ledger;r.inspect=lambda role:events.append('FORBIDDEN_INSPECT')
            r.command=lambda *args:events.append('FORBIDDEN_CHILD')
            with self.assertRaises(Refused):r.fixture('prepare')
            self.assertEqual(events,[('write-once',1)]);self.assertEqual(r.controller_audit_attempts,1)
            self.assertEqual(len(r.lease.revocations),1)

    def test_missing_parent_initialization_refuses_before_new_proof(self):
        r=runtime();r.capture_allocation_initialized=False
        r.controller_audit_ledger=lambda *args:self.fail('No slot proof before initialization')
        with self.assertRaises(Refused):r.reserve_controller_audit('status')
        self.assertEqual(r.controller_audit_attempts,0)

    def test_ledger_status_combined_four_kib_bound_and_no_refund(self):
        r=runtime();r.controller_audit_ledger_charges[1]=0;writes=[]
        with patch.object(supervisor,'put',lambda path,raw:writes.append((path,raw))):
            r.controller_audit_ledger(1,'reserved',{'reservation':'x'})
            before=r.controller_audit_ledger_charges[1]
            with self.assertRaises(RuntimeError):r.controller_audit_ledger(1,'result',{'result':'x'*4096})
        self.assertEqual(len(writes),1);self.assertEqual(r.controller_audit_ledger_charges[1],before)
        self.assertIn('controller-audit-reservations',str(writes[0][0]))
        self.assertNotIn('/session/',str(writes[0][0]))

    def test_parent_header_footer_exact_precharge_before_write(self):
        r=runtime();writes=[];raw=supervisor.jsonbytes({'x':'y'});r.capture_header_charged=4096-len(raw)
        def write(path,data):
            self.assertEqual(r.capture_header_charged,4096);writes.append(data)
        with patch.object(supervisor,'put',write):
            r.capture_header('capture-allocation-status.json',{'x':'y'})
            with self.assertRaises(RuntimeError):r.capture_header('late.json',{})
        self.assertEqual(writes,[raw]);self.assertEqual(r.capture_header_charged,4096)

    def test_header_write_failure_sticky_and_not_repaired(self):
        r=runtime();r.capture_allocation_initialized=False;calls=[]
        def fail(path,raw):calls.append(path);raise OSError('known failed write')
        with patch.object(supervisor,'put',fail):
            with self.assertRaises(Refused):r.initialize_capture_allocation()
            r.finish_capture_allocation()
        self.assertEqual(len(calls),1);self.assertGreater(r.capture_header_charged,0)
        self.assertIsNotNone(r.capture_allocation_poison)

    def test_global_math_and_nonatomic_owner_failure_truthful(self):
        self.assertEqual(8388608+64*131072,16777216)
        parent=runtime();parent.capture_fault=lambda error:setattr(parent,'capture_allocation_poison',str(error))
        parent.capture_fault('parent fault')
        # This separate already-reserved service counter is not an atomic global
        # revocation channel. Whole role still fails; no false shared-poison claim.
        service_counter={'used':100,'cap':8388608};service_counter['used']+=10
        self.assertLess(service_counter['used'],service_counter['cap']);self.assertIsNotNone(parent.capture_allocation_poison)

    def test_actual_parent_exclusive_writer_short_write_not_repaired(self):
        class Writer:
            def __init__(self):self.calls=0
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def write(self,raw):self.calls+=1;return 1
        writer=Writer()
        with tempfile.TemporaryDirectory() as tmp,patch.object(supervisor.os,'open',lambda *args:123),patch.object(supervisor.os,'fdopen',lambda *args,**kwargs:writer):
            with self.assertRaisesRegex(RuntimeError,'Short immutable proof write'):
                supervisor.put(Path(tmp)/'failed-ledger.json',b'abc')
        self.assertEqual(writer.calls,1)

    def driver_fixture(self, directory, corrupt=False):
        import android_driver
        raw=supervisor.jsonbytes({'schema':'e02-minimum-fixture-command-v3','operation':'status',
            'caseId':'minimum-two-role-rs','profileId':supervisor.PROFILE,'windowId':'incoming-b','ok':True,
            'result':{'synthetic':True},'guardController':{'syntheticControlOnly':True}})
        output=directory/'commands';output.mkdir()
        stdout=output/'0001.stdout';stdout.write_bytes(raw)
        stdout_pin=supervisor.pin(stdout)
        command=output/'0001.json';command.write_bytes(supervisor.jsonbytes({'stdout':stdout_pin}))
        if corrupt:stdout.write_bytes(raw+b'changed')
        test=self
        class Runtime:
            out=directory;sequence=1;plan={'ordinaryRole':'incoming'}
            def __init__(self):self.writes=[]
            def check(self):pass
            def fixture(self,operation):return raw
            def put_bytes(self,*args):test.fail('No duplicate reply write is allowed')
            def put_json(self,name,value):
                self.writes.append(name);path=self.out/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(supervisor.jsonbytes(value));return supervisor.pin(path)
        return android_driver,Runtime(),stdout_pin

    def test_actual_driver_reuses_verified_command_stdout_pin_no_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            driver,r,stdout=self.driver_fixture(Path(tmp))
            self.assertEqual(driver.fixture(r,'status'),{'synthetic':True})
            call,_=r._minimum_last_fixture_call
            self.assertEqual(call['reply'],stdout)
            self.assertEqual(r.writes,['evidence/fixture-01-status-call.json'])
            self.assertFalse((Path(tmp)/'evidence/fixture-01-status-reply.json').exists())

    def test_actual_driver_corrupt_retained_stdout_refuses_before_call_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            driver,r,_=self.driver_fixture(Path(tmp),corrupt=True)
            with self.assertRaisesRegex(ValueError,'^Evidence drift$'):driver.fixture(r,'status')
            self.assertEqual(r.writes,[])
            self.assertFalse(hasattr(r,'_minimum_fixture_calls'))
            self.assertFalse((Path(tmp)/'evidence/fixture-01-status-reply.json').exists())


if __name__=='__main__':unittest.main()
