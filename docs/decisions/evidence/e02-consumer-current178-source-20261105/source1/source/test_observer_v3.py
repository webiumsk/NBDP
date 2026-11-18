"""SOURCE definitions for actual v3 service account/state DATA contract."""
import base64,copy,hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from strict import Refusal,json_bytes
from async_guard import ALLOCATION,PROOF_LIMIT
from observer import healthy_state

def state():
    row=dict(phase='GUARD_EXIT');line=json_bytes(row)+b'\n';n=len(line)
    account=dict(limit=PROOF_LIMIT,chargedBytes=n,intendedBytes=n,poisoned=False,firstError=None)
    value=dict(schema='e02-minimum-observer-state-v3',allocation=ALLOCATION,serviceHeaderPrepaidBytes=4096,serviceDiagnostics=dict(limit=4096,chargedBytes=0,intendedBytes=0,poisoned=False,firstError=None),phase=dict(sequence=1,intendedTotalBytes=n,acknowledgedTotalBytes=n,physicalBytes=None,physicalMeaning='NOT_INDEPENDENTLY_MEASURED_ACKNOWLEDGED_PREFIX_IS_NOT_PHYSICAL_ATTESTATION',poisoned=False,firstError=None,lastAttempt=dict(sequence=1,phase='GUARD_EXIT',intendedBytes=n,writeInvoked=True,reportedCount=n,acknowledgedBytes=n,acknowledgedPrefixBase64=base64.b64encode(line).decode(),physicalBytes=None,error=None)),budget=dict(schema='e02-minimum-aggregate-capture-budget-v3',limit=PROOF_LIMIT,intendedTotalBytes=n,acknowledgedTotalBytes=n,streams=dict(phase=dict(intended=n,acknowledged=n),proxy=dict(intended=0,acknowledged=0)),poisoned=False,firstError=None,physicalBytes=None,physicalMeaning='ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION',lastAttempt=dict(stream='phase',intendedBytes=n,writeInvoked=True,reportedCount=n,acknowledgedBytes=n,acknowledgedPrefixSha256=hashlib.sha256(line).hexdigest(),physicalBytes=None,error=None),allocationAccount=account))
    return value,[line],[]

class ObserverV3Controls(unittest.TestCase):
    def check(self,data):return healthy_state(*data,1,0)
    def refuse(self,mutation):
        d=state();mutation(d[0])
        with self.assertRaises(Refusal):self.check(d)
    def test_positive_exact_current_service_state(self):self.check(state())
    def test_old_observer_v2_rejected(self):self.refuse(lambda d:d.update(schema='e02-minimum-observer-state-v2'))
    def test_old_budget_v2_rejected(self):self.refuse(lambda d:d['budget'].update(schema='e02-minimum-aggregate-capture-budget-v2'))
    def test_service_share_not_whole16MiB(self):self.refuse(lambda d:d['budget'].update(limit=16777216))
    def test_global_partition_not_expanded(self):self.refuse(lambda d:d.update(allocation=dict(ALLOCATION,total=33554432)))
    def test_missing_allocation_account(self):self.refuse(lambda d:d['budget'].pop('allocationAccount'))
    def test_undercharged_stream_bytes(self):self.refuse(lambda d:d['budget']['allocationAccount'].update(chargedBytes=0,intendedBytes=0))
    def test_poisoned_service_account(self):self.refuse(lambda d:d['budget']['allocationAccount'].update(poisoned=True,firstError='short'))
    def test_diagnostics_cannot_borrow_proof_share(self):self.refuse(lambda d:d['serviceDiagnostics'].update(limit=8192))
    def test_header_precharge_exact4096(self):self.refuse(lambda d:d.update(serviceHeaderPrepaidBytes=0))
    def test_unknown_physical_write_claim_refused(self):self.refuse(lambda d:d['budget'].update(physicalBytes=10))
    def test_short_retained_phase_prefix_refused(self):self.refuse(lambda d:d['phase']['lastAttempt'].update(reportedCount=1))
    def test_wrong_exact_prefix_hash_refused(self):self.refuse(lambda d:d['budget']['lastAttempt'].update(acknowledgedPrefixSha256='a'*64))

if __name__=='__main__':unittest.main()
