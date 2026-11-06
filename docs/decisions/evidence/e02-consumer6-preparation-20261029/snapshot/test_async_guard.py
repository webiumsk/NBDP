"""SOURCE definitions only: mock retained guard DATA, no helper/process/time."""
import base64,copy,hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from strict import Refusal,json_bytes
from async_guard import GuardTrace
INSTANCE='1'*32;RUN='2'*32;LEASE_SHA='3'*64;CONFIG_SHA='4'*64
HELPER=dict(path='/input/guard-helper.py',bytes=10,sha256='5'*64)
LEASE=dict(runId=RUN,issuedUtcNs=1,deadlineUtcNs=1000000000000000,issuedMonoNs=1,
 deadlineMonoNs=1000000000000000,issuedBootNs=1,deadlineBootNs=1000000000000000,bootId='mock-boot')

def baseline(label='mock:effect',context=b'context',extra=False,checks=None):
    rows=[]
    def add(name,**fields):rows.append(dict(name=name,fields=dict(helperInstance=INSTANCE,**fields)))
    def check(n,label,context,operation='CHECK'):
        token=str(n);add('GUARD_ENTRY',label=label,guardSequence=token,enqueueMonoNs='100')
        if n==1:
            add('GUARD_HELPER_LAUNCH',executable='/guard-python/lib/ld-linux-x86-64.so.2',argv=['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/guard-helper.py',INSTANCE,LEASE_SHA,str(HELPER['bytes']),HELPER['sha256']]);add('GUARD_HELPER_CREATED',pid=123)
        request=dict(schema='e02-fresh-guard-request-v1',operation=operation,instance=INSTANCE,runId=RUN,leaseSha256=LEASE_SHA,sequence=token,label=label,contextSha256=hashlib.sha256(context).hexdigest())
        raw=json_bytes(request)+b'\n'
        add('GUARD_RPC_REQUEST',label=label,guardSequence=token,rawBase64=base64.b64encode(raw).decode(),enqueueMonoNs='100',decisionDeadlineMonoNs='5000000100',enqueueUtcLowerNs='100',enqueueBootLowerNs='100',decisionDeadlineUtcNs='5000000100',decisionDeadlineBootNs='5000000100')
        reply=dict(request,schema='e02-fresh-guard-response-v1',requestSha256=hashlib.sha256(raw).hexdigest(),ok=True,clocks=None if operation=='CLOSE' else dict(Utc='200',Mono='200',Boot='200',bootId=LEASE['bootId']))
        add('GUARD_RPC_REPLY',guardSequence=token,rawBase64=base64.b64encode(json_bytes(reply)+b'\n').decode())
        if operation=='CHECK':rows.append(dict(name='OBSERVED_EFFECT',fields={}))
        add('GUARD_EXIT',label=label,guardSequence=token,ok=True,error=None,consumed=True,consumedUtcUpperNs='300',consumedMonoNs='300',consumedBootUpperNs='300')
    if checks is None:
        checks=[(label,context)]+([('mock:second',b'second')] if extra else [])
    for n,(name,raw) in enumerate(checks,1):check(n,name,raw)
    check(len(checks)+1,'owner-close',b'','CLOSE')
    add('GUARD_HELPER_STDOUT_EOF');add('GUARD_HELPER_STDERR_EOF');add('GUARD_HELPER_EXIT',code=0,signal=None);add('GUARD_HELPER_CLOSE',code=0,signal=None,stdoutEOF=True,stderrEOF=True,exitSeen=True)
    return rows

def trace(rows):return GuardTrace(rows,LEASE,LEASE_SHA,RUN,HELPER,CONFIG_SHA,controller=False)
def selected(rows,name,n=0):return [r['fields'] for r in rows if r['name']==name][n]
def raw_edit(rows,event,edit):
    fields=selected(rows,event);raw=base64.b64decode(fields['rawBase64']);import json
    value=json.loads(raw);edit(value);fields['rawBase64']=base64.b64encode(json_bytes(value)+b'\n').decode()

class AsyncGuardControls(unittest.TestCase):
    def refuse(self,mutate):
        rows=baseline();mutate(rows)
        with self.assertRaises(Refusal):trace(rows)
    def test_positive_complete_owner_and_effect(self):
        rows=baseline();t=trace(rows);n,_=t.effect(5,'mock:effect',b'context');self.assertEqual(n,1)
    def test_unrelated_observation_interleaving_is_causal(self):
        rows=baseline();rows.insert(5,dict(name='UNRELATED_OBSERVATION',fields={}));self.assertEqual(trace(rows).effect(6,'mock:effect',b'context')[0],1)
    def test_wrong_instance(self):self.refuse(lambda r:selected(r,'GUARD_RPC_REPLY').update(helperInstance='a'*32))
    def test_wrong_run(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REQUEST',lambda v:v.update(runId='a'*32)))
    def test_wrong_lease_hash(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REQUEST',lambda v:v.update(leaseSha256='a'*64)))
    def test_wrong_reply_sequence(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v.update(sequence='9')))
    def test_wrong_request_hash(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v.update(requestSha256='a'*64)))
    def test_wrong_context_hash(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v.update(contextSha256='a'*64)))
    def test_wrong_label(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v.update(label='wrong')))
    def test_replayed_reply(self):self.refuse(lambda r:r.insert(5,copy.deepcopy(r[4])))
    def test_missing_request(self):self.refuse(lambda r:r.pop(3))
    def test_missing_reply(self):self.refuse(lambda r:r.pop(4))
    def test_missing_consumption(self):self.refuse(lambda r:r.pop(6))
    def test_nonconsumed_exit(self):self.refuse(lambda r:selected(r,'GUARD_EXIT').update(consumed=False))
    def test_denied_reply(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v.update(ok=False)))
    def test_held_ok_past_enqueue_deadline(self):self.refuse(lambda r:selected(r,'GUARD_EXIT').update(consumedMonoNs='5000000100'))
    def test_utc_held_ok_deadline(self):self.refuse(lambda r:selected(r,'GUARD_EXIT').update(consumedUtcUpperNs='5000000100'))
    def test_boot_held_ok_deadline(self):self.refuse(lambda r:selected(r,'GUARD_EXIT').update(consumedBootUpperNs='5000000100'))
    def test_reply_clock_rollback(self):self.refuse(lambda r:selected(r,'GUARD_EXIT').update(consumedMonoNs='199'))
    def test_original_core_lease_expiry(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v['clocks'].update(Mono=str(LEASE['deadlineMonoNs']))))
    def test_boot_identity_substitution(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v['clocks'].update(bootId='other')))
    def test_extended_five_second_window(self):self.refuse(lambda r:selected(r,'GUARD_RPC_REQUEST').update(decisionDeadlineMonoNs='5000000101'))
    def test_terminal_fence_forbids_success(self):self.refuse(lambda r:r.insert(5,dict(name='GUARD_TERMINAL',fields=dict(helperInstance=INSTANCE,error='bad',epoch=1))))
    def test_missing_orderly_close(self):self.refuse(lambda r:r.__delitem__(slice(7,11)))
    def test_close_nonnull_clocks(self):
        rows=baseline();field=selected(rows,'GUARD_RPC_REPLY',1);import json
        value=json.loads(base64.b64decode(field['rawBase64']));value['clocks']={};field['rawBase64']=base64.b64encode(json_bytes(value)+b'\n').decode()
        with self.assertRaises(Refusal):trace(rows)
    def test_wrong_helper_source(self):self.refuse(lambda r:selected(r,'GUARD_HELPER_LAUNCH')['argv'].__setitem__(-1,'a'*64))
    def test_missing_stderr_eof(self):self.refuse(lambda r:r.__delitem__(-3))
    def test_missing_stdout_eof(self):self.refuse(lambda r:r.__delitem__(-4))
    def test_nonnatural_helper_exit(self):self.refuse(lambda r:selected(r,'GUARD_HELPER_EXIT').update(code=2))
    def test_close_without_actual_exit(self):self.refuse(lambda r:r.__delitem__(-2))
    def test_wrong_effect_context(self):
        with self.assertRaises(Refusal):trace(baseline()).effect(5,'mock:effect',b'other')
    def test_effect_after_consumption_refused(self):
        with self.assertRaises(Refusal):trace(baseline()).effect(7,'mock:effect',b'context')
    def test_same_effect_not_reused(self):
        t=trace(baseline());t.effect(5,'mock:effect',b'context')
        with self.assertRaises(Refusal):t.effect(5,'mock:effect',b'context')
    def test_observed_effect_after_close_is_refused(self):
        self.refuse(lambda rows:rows.insert(-1,dict(name='OBSERVED_EFFECT',fields={})))
    def test_extra_reply_key(self):self.refuse(lambda r:raw_edit(r,'GUARD_RPC_REPLY',lambda v:v.update(cached=True)))
    def test_incomplete_raw_reply(self):
        def mutate(rows):
            f=selected(rows,'GUARD_RPC_REPLY');f['rawBase64']=base64.b64encode(base64.b64decode(f['rawBase64'])[:-1]).decode()
        self.refuse(mutate)
    def test_old_sync_pair_is_not_fresh_rpc(self):
        with self.assertRaises(Refusal):trace([dict(name='GUARD_ENTRY',fields=dict(label='old'))])

if __name__=='__main__':unittest.main()
