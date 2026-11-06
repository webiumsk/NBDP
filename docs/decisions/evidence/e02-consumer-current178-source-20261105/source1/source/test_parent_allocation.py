"""SOURCE-only current parent/controller DATA definitions, no process or I/O."""
import copy,hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from strict import Refusal,json_bytes
from async_guard import ALLOCATION
from parent_allocation import validate_parent
from test_async_guard import baseline,INSTANCE,RUN,HELPER,LEASE

class MemoryFiles:
    def __init__(self):self.data={};self.raw={}
    def put(self,path,value):
        raw=value if type(value) is bytes else json_bytes(value)
        p=dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());self.data[path]=value;self.raw[path]=raw;return p
    def read(self,p):
        raw=self.raw[p['path']]
        if (len(raw),hashlib.sha256(raw).hexdigest())!=(p['bytes'],p['sha256']):raise Refusal('MODEL_PIN_DRIFT')
        return raw
    def doc(self,p):self.read(p);return copy.deepcopy(self.data[p['path']])

def graph():
    f=MemoryFiles();root='/model/window';members=[]
    def put(name,value):
        p=f.put(root+'/'+name,value);members.append(p);return p
    lease_pin=put('lease.json',LEASE);config_pin=put('config.json',dict(sourceAndDependencyPins=[HELPER]))
    context=json_bytes({'mode':'prepare'})
    observations=baseline(checks=[(s,context) for s in ('startup:plan','controller:socket-create','controller:connect','controller:response')])
    observations=[r for r in observations if r['name'].startswith('GUARD_')]
    # Bind the mocked request/reply lease/config to this exact memory graph.
    import base64,json
    for row in observations:
        if row['name']=='GUARD_HELPER_LAUNCH':row['fields']['argv'][-3]=lease_pin['sha256']
        if row['name']=='GUARD_RPC_REQUEST':
            q=json.loads(base64.b64decode(row['fields']['rawBase64']));q['leaseSha256']=lease_pin['sha256'];raw=json_bytes(q)+b'\n';row['fields']['rawBase64']=base64.b64encode(raw).decode();last=raw
        if row['name']=='GUARD_RPC_REPLY':
            q=json.loads(base64.b64decode(row['fields']['rawBase64']));q['leaseSha256']=lease_pin['sha256'];q['requestSha256']=hashlib.sha256(last).hexdigest();row['fields']['rawBase64']=base64.b64encode(json_bytes(q)+b'\n').decode()
    audit=dict(schema='e02-controller-guard-audit-v1',reservationIndex=1,instance=INSTANCE,scope='ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',runId=RUN,leaseSha256=lease_pin['sha256'],configurationSha256=config_pin['sha256'],observations=observations)
    reply_pin=put('commands/0001.stdout.raw',dict(guardController=audit));stderr_pin=put('commands/0001.stderr.raw',b'')
    command=dict(argv=['/usr/bin/docker','exec','--env','NBDP_CONTROLLER_AUDIT_SLOT=1','model-cid','/usr/local/bin/node','/input/fixture.mjs','prepare'],stdout=reply_pin,stderr=stderr_pin,stdoutEOF=True,stderrEOF=True,reaped=True,exit=0,forced=False)
    command_pin=put('commands/0001.json',command)
    call=dict(operation='prepare',commandSequence=1,command=command_pin,reply=reply_pin);call_pin=put('call.json',call)
    binding_sha=hashlib.sha256(json_bytes([HELPER])).hexdigest()
    header=dict(schema='e02-controller-capture-parent-allocation-v1',actor='/root',runId=RUN,runConfig=config_pin,sourceBindingsSha256=binding_sha,originalLeaseSha256=lease_pin['sha256'],allocation=ALLOCATION,ledgerRoot=root+'/controller-audit-reservations',ledgerBoundary='HOST_ONLY_OUTSIDE_FIXTURE_WRITABLE_MOUNTS',prechargedServiceBytes=8388608,controllerReservationsRefundable=False)
    status=dict(schema='e02-controller-capture-parent-status-v1',runId=RUN,controllerAttempts=1,controllerPoolPrechargedBytes=131072,servicePrechargedBytes=8388608,globalMaximumBytes=16777216,headerPrechargedLimit=4096,noRefunds=True,scope='CONSISTENCY_ONLY_NOT_POSTHOC_ADMISSION')
    reserve=dict(schema='e02-controller-audit-parent-reservation-v1',actor='/root',index=1,operation='prepare',runId=RUN,runConfig=config_pin,originalLeaseSha256=lease_pin['sha256'],sourceBindingsSha256=binding_sha,slotBytes=131072,proofBytes=122880,ledgerBytes=4096,diagnosticsBytes=4096,poolPrechargedBytes=131072,refundAllowed=False)
    result=dict(schema='e02-controller-audit-parent-completion-v1',index=1,runId=RUN,operation='prepare',commandSequence=1,command=command_pin,stdout=reply_pin,helperInstance=INSTANCE,encodedAuditContributionBytes=len(b',"guardController":'+json_bytes(audit)+b'}\n'),state='NATURAL_COMPLETE_REQUIRES_WHOLE_CONSUMER')
    put('capture-allocation-header.json',header);put('capture-allocation-status.json',status);put('controller-audit-reservations/01-reserved.json',reserve);put('controller-audit-reservations/01-result.json',result)
    window=dict(outputRoot=root,graphFiles=members,runId=RUN,runConfig=config_pin,lease=lease_pin)
    return f,window,[command],{1:(call_pin,call)}

class ParentAllocationControls(unittest.TestCase):
    def check(self,g):return validate_parent(*g,HELPER)
    def changed(self,name,key,value):
        f,w,commands,calls=graph();path=w['outputRoot']+'/'+name;doc=f.data[path];doc[key]=value;pin=f.put(path,doc);w['graphFiles']=[pin if p['path']==path else p for p in w['graphFiles']]
        with self.assertRaises((Refusal,ValueError)):self.check((f,w,commands,calls))
    def test_positive_whole_parent_controller_join(self):self.assertEqual(self.check(graph()),{INSTANCE})
    def test_global_budget_not_expanded(self):self.changed('capture-allocation-status.json','globalMaximumBytes',33554432)
    def test_attempt65_refused(self):self.changed('capture-allocation-status.json','controllerAttempts',65)
    def test_nonrefundable_slot(self):self.changed('controller-audit-reservations/01-reserved.json','refundAllowed',True)
    def test_wrong_slot_precharge(self):self.changed('controller-audit-reservations/01-reserved.json','poolPrechargedBytes',0)
    def test_wrong_original_lease(self):self.changed('controller-audit-reservations/01-reserved.json','originalLeaseSha256','a'*64)
    def test_wrong_current_source_binding(self):self.changed('capture-allocation-header.json','sourceBindingsSha256','a'*64)
    def test_fixture_writable_ledger_location(self):self.changed('capture-allocation-header.json','ledgerRoot','/session/fixtures/ledger')
    def test_child_cannot_assign_capacity(self):self.changed('controller-audit-reservations/01-reserved.json','slotBytes',262144)
    def test_wrong_helper_instance(self):self.changed('controller-audit-reservations/01-result.json','helperInstance','a'*32)
    def test_wrong_encoded_audit_charge(self):self.changed('controller-audit-reservations/01-result.json','encodedAuditContributionBytes',1)
    def test_duplicate_reply_copy_refused(self):
        f,w,commands,calls=graph();call=calls[1][1];call['reply']=f.put('/model/window/copied-reply.json',f.data[call['reply']['path']])
        with self.assertRaises(Refusal):self.check((f,w,commands,calls))
    def test_missing_ledger_result(self):
        g=graph();g[1]['graphFiles']=[p for p in g[1]['graphFiles'] if not p['path'].endswith('01-result.json')]
        with self.assertRaises(Refusal):self.check(g)
    def test_extra_unaccounted_ledger_file(self):
        g=graph();g[1]['graphFiles'].append(g[0].put('/model/window/controller-audit-reservations/02-reserved.json',{}))
        with self.assertRaises(Refusal):self.check(g)
    def test_truncated_controller_stdout_eof(self):
        g=graph();g[2][0]['stdoutEOF']=False
        with self.assertRaises(Refusal):self.check(g)
    def test_controller_nonnatural_exit(self):
        g=graph();g[2][0]['exit']=2
        with self.assertRaises(Refusal):self.check(g)
    def test_controller_forced_lifecycle(self):
        g=graph();g[2][0]['forced']=True
        with self.assertRaises(Refusal):self.check(g)

if __name__=='__main__':unittest.main()
