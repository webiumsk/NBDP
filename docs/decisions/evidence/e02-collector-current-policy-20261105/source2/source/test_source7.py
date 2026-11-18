"""Future one-shot whole ACTUAL_REQUEST7_SOURCE2 controls; author defines but does not run."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:
 import test_collector
 import test_history_prefix
 import test_request_policy
 import test_typed_origin
finally:sys.path.pop(0)

def suite():
 loader=unittest.TestLoader()
 return unittest.TestSuite([loader.loadTestsFromModule(test_collector),loader.loadTestsFromModule(test_history_prefix),loader.loadTestsFromModule(test_request_policy),loader.loadTestsFromModule(test_typed_origin)])

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(suite())
 raise SystemExit(0 if result.wasSuccessful() and result.testsRun==81 and not result.skipped else 2)
