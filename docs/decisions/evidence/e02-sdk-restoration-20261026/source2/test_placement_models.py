"""PREPARED NOT EXECUTED: pure fake-operation placement-state regressions.

These tests call the real Restore.publish/run state and failure-receipt wiring
with fake filesystem/FFI/deadline/receipt operations. They never instantiate a
real Restore, download/extract an archive, manipulate an SDK or call renameat2.
They establish modeled state handling only, not filesystem/runtime qualification.
"""
import errno
import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import restore_sdk as sdk


class FakeRename:
    def __init__(self,result=0,error=None,effect_before_error=False):
        self.result,self.error,self.effect_before_error=result,error,effect_before_error
        self.calls=[];self.model_destination_placed=False

    def __call__(self,*args):
        self.calls.append(args)
        if self.effect_before_error:self.model_destination_placed=True
        if self.error is not None:raise self.error
        if self.result==0:self.model_destination_placed=True
        return self.result


class PlacementModels(unittest.TestCase):
    def model(self):
        restore=sdk.Restore.__new__(sdk.Restore)
        restore.plan={'archives':[]}
        restore.stage=Path('/SYNTHETIC_ONLY_NO_FILESYSTEM_ACCESS/stage-sdk')
        restore.attempt_fd,restore.parent_fd,restore.stage_fd=10,11,12
        restore.remaining=0;restore.disk_samples=0;restore.lowest_free=None
        restore.placement_state='NOT_ATTEMPTED'
        restore.rename_return=restore.rename_errno=None
        restore.deadline=SimpleNamespace(failure_receipt=lambda:None)
        restore.initialize=lambda:None
        restore.inventory=lambda:[]
        restore.check=lambda:None
        restore.receipts={}
        restore.receipt=lambda name,value:restore.receipts.__setitem__(name,value)
        return restore

    def run_model(self,restore,rename,expected_error=None,code=errno.EEXIST,
                  open_error=None,identity_mismatch=False,fsync_error=None,
                  close_error=None,library_error=None):
        original={'files':[],'sha256':hashlib.sha256(b'[]').hexdigest()}
        library=SimpleNamespace(renameat2=rename)
        def close(fd):
            if fd==77 and close_error is not None:raise close_error
        with patch.object(sdk.ctypes,'CDLL',side_effect=library_error,return_value=library), \
             patch.object(sdk.ctypes,'get_errno',return_value=code), \
             patch.object(sdk.os,'open',side_effect=open_error,return_value=77), \
             patch.object(sdk.os,'fstat',side_effect=[SimpleNamespace(st_dev=1,st_ino=2),
                 SimpleNamespace(st_dev=1,st_ino=3 if identity_mismatch else 2)]), \
             patch.object(sdk.os,'close',side_effect=close), \
             patch.object(sdk.os,'fsync',side_effect=fsync_error), \
             patch.object(sdk.signal,'setitimer'), \
             patch.object(sdk,'hash_file',return_value={'sha256':sdk.INVENTORY_SHA}):
            if expected_error is None:restore.run(original)
            else:
                with self.assertRaises(expected_error):restore.run(original)
        return restore.receipts['result.json' if expected_error is None else 'failure.json']

    def test_pre_rename_deadline_failure_records_not_attempted(self):
        restore=self.model();rename=FakeRename()
        def fail():raise TimeoutError('SYNTHETIC_PRE_RENAME_DEADLINE')
        restore.check=fail
        receipt=self.run_model(restore,rename,TimeoutError)
        self.assertEqual(receipt['placementState'],'NOT_ATTEMPTED')
        self.assertIs(receipt['placed'],False);self.assertEqual(rename.calls,[])

    def test_pre_rename_symbol_load_failure_records_not_attempted(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename,OSError,library_error=OSError('SYNTHETIC_LIBC_LOAD'))
        self.assertEqual(receipt['placementState'],'NOT_ATTEMPTED')
        self.assertIs(receipt['placed'],False);self.assertEqual(rename.calls,[])

    def test_known_eexist_refusal_records_no_placement_not_destination_absence(self):
        restore=self.model();rename=FakeRename(result=-1)
        receipt=self.run_model(restore,rename,ValueError,code=errno.EEXIST)
        self.assertEqual(receipt['placementState'],'NOT_PLACED')
        self.assertIs(receipt['placed'],False)
        self.assertEqual(receipt['renameReportedReturn'],-1)
        self.assertEqual(receipt['renameReportedErrno'],errno.EEXIST)
        self.assertIn('false never means destination absent',receipt['placementMeaning'])
        self.assertFalse(rename.model_destination_placed)

    def test_known_permission_refusal_records_no_placement(self):
        restore=self.model();rename=FakeRename(result=-1)
        receipt=self.run_model(restore,rename,ValueError,code=errno.EACCES)
        self.assertEqual(receipt['placementState'],'NOT_PLACED');self.assertIs(receipt['placed'],False)

    def test_post_rename_open_failure_preserves_known_placement_in_failure_receipt(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename,OSError,open_error=OSError('SYNTHETIC_POST_RENAME_OPEN'))
        self.assertTrue(rename.model_destination_placed)
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)

    def test_post_rename_inode_check_failure_preserves_placement(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename,ValueError,identity_mismatch=True)
        self.assertIn('PLACED_DIRECTORY_IDENTITY_MISMATCH',receipt['error'])
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)

    def test_post_rename_fd_close_failure_preserves_placement(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename,OSError,close_error=OSError('SYNTHETIC_POST_RENAME_CLOSE'))
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)

    def test_post_rename_fsync_failure_preserves_placement(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename,OSError,fsync_error=OSError('SYNTHETIC_POST_RENAME_FSYNC'))
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)

    def post_check(self,error):
        restore=self.model();rename=FakeRename();calls=[]
        def check():
            calls.append(None)
            if len(calls)==2:raise error
        restore.check=check
        receipt=self.run_model(restore,rename,type(error))
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)
        self.assertEqual(len(calls),2)

    def test_post_rename_deadline_failure_preserves_placement(self):
        self.post_check(TimeoutError('SYNTHETIC_POST_RENAME_DEADLINE'))

    def test_post_rename_free_space_failure_preserves_placement(self):
        self.post_check(ValueError('SYNTHETIC_POST_RENAME_RESERVE'))

    def test_interrupted_call_after_fake_effect_records_unknown_not_false(self):
        restore=self.model();rename=FakeRename(error=KeyboardInterrupt(),effect_before_error=True)
        receipt=self.run_model(restore,rename,KeyboardInterrupt)
        self.assertTrue(rename.model_destination_placed)
        self.assertEqual(receipt['placementState'],'UNKNOWN');self.assertIsNone(receipt['placed'])
        self.assertIsNone(receipt['renameReportedReturn'])

    def test_interrupted_call_without_known_effect_also_records_unknown(self):
        restore=self.model();rename=FakeRename(error=KeyboardInterrupt())
        receipt=self.run_model(restore,rename,KeyboardInterrupt)
        self.assertFalse(rename.model_destination_placed)
        self.assertEqual(receipt['placementState'],'UNKNOWN');self.assertIsNone(receipt['placed'])

    def test_ambiguous_eio_return_records_unknown(self):
        restore=self.model();rename=FakeRename(result=-1)
        receipt=self.run_model(restore,rename,ValueError,code=errno.EIO)
        self.assertEqual(receipt['placementState'],'UNKNOWN');self.assertIsNone(receipt['placed'])
        self.assertEqual(receipt['renameReportedErrno'],errno.EIO)

    def test_ambiguous_eintr_return_records_unknown(self):
        restore=self.model();rename=FakeRename(result=-1)
        receipt=self.run_model(restore,rename,ValueError,code=errno.EINTR)
        self.assertEqual(receipt['placementState'],'UNKNOWN');self.assertIsNone(receipt['placed'])

    def test_unrecognized_return_records_unknown(self):
        restore=self.model();rename=FakeRename(result=1)
        receipt=self.run_model(restore,rename,ValueError)
        self.assertEqual(receipt['placementState'],'UNKNOWN');self.assertIsNone(receipt['placed'])

    def test_interrupt_after_observed_success_preserves_known_placement(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename,KeyboardInterrupt,open_error=KeyboardInterrupt())
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)

    def test_success_state_and_result_receipt_record_placed(self):
        restore=self.model();rename=FakeRename()
        receipt=self.run_model(restore,rename)
        self.assertEqual(receipt['placementState'],'PLACED');self.assertIs(receipt['placed'],True)
        self.assertEqual(receipt['renameReportedReturn'],0)
        self.assertIsNone(receipt['renameReportedErrno'])
        self.assertFalse(receipt['sdkToolsExecuted'])


if __name__=='__main__':unittest.main(verbosity=2)
