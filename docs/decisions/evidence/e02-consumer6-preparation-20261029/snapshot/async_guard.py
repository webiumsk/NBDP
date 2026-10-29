"""Closed producer4 asynchronous guard DATA joins; no target/clock/process use.

Replies are one-use evidence of the original helper call, never cached permits.
Effects are matched inside reply..consumed-exit intervals, not adjacent row pairs.
The caller supplies the original lease and exact expected scope/run/config.
"""
import hashlib
import re
from strict import closed, equal, hx, integer, json_bytes, loads, need
from wire import decode64

ALLOCATION = dict(total=16777216, service=8388608, serviceHeader=4096,
    serviceDiagnostics=4096, controllerSlots=64, slot=131072, proof=122880,
    ledger=4096, diagnostics=4096, wrapper=1024)
PROOF_LIMIT = 8380416
FIELDS = {
 'GUARD_ENTRY':'helperInstance label guardSequence enqueueMonoNs',
 'GUARD_EXIT':'helperInstance label guardSequence ok error consumed consumedUtcUpperNs consumedMonoNs consumedBootUpperNs',
 'GUARD_RPC_REQUEST':'helperInstance label guardSequence rawBase64 enqueueMonoNs decisionDeadlineMonoNs enqueueUtcLowerNs enqueueBootLowerNs decisionDeadlineUtcNs decisionDeadlineBootNs',
 'GUARD_RPC_REPLY':'helperInstance guardSequence rawBase64',
 'GUARD_HELPER_LAUNCH':'helperInstance executable argv',
 'GUARD_HELPER_CREATED':'helperInstance pid',
 'GUARD_HELPER_STDOUT_EOF':'helperInstance', 'GUARD_HELPER_STDERR_EOF':'helperInstance',
 'GUARD_HELPER_EXIT':'helperInstance code signal',
 'GUARD_HELPER_CLOSE':'helperInstance code signal stdoutEOF stderrEOF exitSeen',
}
REQUEST_KEYS = 'schema operation instance runId leaseSha256 sequence label contextSha256'
REPLY_KEYS = REQUEST_KEYS + ' requestSha256 ok clocks'
FORBIDDEN = frozenset(('GUARD_TERMINAL','GUARD_HELPER_STDERR','GUARD_HELPER_TERMINATE',
 'GUARD_HELPER_CLEANUP_DEADLINE_EXHAUSTED'))


def decimal(value):
    need(type(value) is str and re.fullmatch(r'(?:0|[1-9][0-9]{0,23})',value), 'EXACT_GUARD_DECIMAL')
    return int(value)


def compact(value):
    return json_bytes(value)


def rpc(raw, limit):
    need(type(raw) is bytes and 0 < len(raw) <= limit and raw.endswith(b'\n')
         and raw.count(b'\n') == 1, 'ONE_COMPLETE_BOUNDED_GUARD_FRAME')
    value=loads(raw)
    # Numeric identity/clock tokens are prohibited by the actual helper protocol.
    def walk(v):
        if type(v) is dict:
            for x in v.values(): walk(x)
        else: need(v is None or type(v) in (str,bool), 'GUARD_JSON_STRING_BOOL_NULL_ONLY')
    walk(value)
    return value


class GuardTrace:
    def __init__(self, rows, lease, lease_sha, run_id, helper_pin, configuration_sha, *, controller=False):
        self.rows=rows;self.items={};self.used_effects=set();self.used_effect_permits=set()
        hx(lease_sha);hx(run_id,32);hx(configuration_sha)
        equal(lease['runId'],run_id)
        need(type(rows) is list and 1<=len(rows)<=262144,'GUARD_TRACE_BOUND')
        self.instance=None;entry_counter=0;request_counter=0;active=None;closed_owner=False
        life={};launched=False;created=False
        for index,row in enumerate(rows):
            name=row.get('phase',row.get('name')); fields=row if 'phase' in row else row.get('fields')
            need(type(name) is str,'CLOSED_OBSERVATION_NAME')
            need(name not in FORBIDDEN,'FAILED_GUARD_CANNOT_CONTRIBUTE')
            if not name.startswith('GUARD_'):
                need(not controller,'CLOSED_CONTROLLER_OBSERVATION_EVENT');need(not closed_owner,'NO_OBSERVED_EFFECT_AFTER_OWNER_CLOSE');continue
            need(name in FIELDS,'CLOSED_CURRENT_GUARD_EVENT')
            if controller or 'phase' not in row:closed(row,'name fields');closed(fields,FIELDS[name])
            instance=fields['helperInstance'];hx(instance,32)
            if self.instance is None:self.instance=instance
            equal(instance,self.instance,'ONE_HELPER_INSTANCE_PER_OWNER')
            if closed_owner:need(name in ('GUARD_HELPER_STDOUT_EOF','GUARD_HELPER_STDERR_EOF','GUARD_HELPER_EXIT','GUARD_HELPER_CLOSE'),'NO_PROTECTED_USE_AFTER_CLOSE')
            if name=='GUARD_ENTRY':
                n=decimal(fields['guardSequence']);entry_counter+=1;equal(n,entry_counter,'FRESH_CONTIGUOUS_GUARD_SEQUENCE')
                need(n not in self.items,'NO_REUSED_GUARD_PERMIT')
                label=fields['label'];need(type(label) is str and re.fullmatch(r'[a-zA-Z0-9:_-]{1,160}',label),'CLOSED_GUARD_LABEL')
                self.items[n]=dict(entry=index,entryFields=fields,request=None,reply=None,exit=None)
            elif name=='GUARD_RPC_REQUEST':
                need(created,'REQUEST_REQUIRES_OWNED_CREATED_HELPER')
                n=decimal(fields['guardSequence']);request_counter+=1;equal(n,request_counter,'ORDERED_HELPER_REQUESTS');need(active is None,'ONE_HELPER_RPC_ACTIVE')
                need(n in self.items,'RPC_WITHOUT_ENTRY');item=self.items[n];need(item['request'] is None,'REUSED_REQUEST')
                raw=decode64(fields['rawBase64']);r=rpc(raw,1024);closed(r,REQUEST_KEYS)
                equal(r['schema'],'e02-fresh-guard-request-v1');need(r['operation'] in ('CHECK','CLOSE'),'CLOSED_GUARD_OPERATION')
                for key,value in [('instance',instance),('runId',run_id),('leaseSha256',lease_sha),('sequence',fields['guardSequence']),('label',fields['label'])]:equal(r[key],value,'EXACT_REQUEST_AUTHORITY')
                hx(r['contextSha256']);equal(fields['label'],item['entryFields']['label']);equal(fields['enqueueMonoNs'],item['entryFields']['enqueueMonoNs'])
                for lower,upper in [('enqueueMonoNs','decisionDeadlineMonoNs'),('enqueueUtcLowerNs','decisionDeadlineUtcNs'),('enqueueBootLowerNs','decisionDeadlineBootNs')]:equal(decimal(fields[upper]),decimal(fields[lower])+5000000000,'ORIGINAL_ENQUEUE_INCLUSIVE_FIVE_SECONDS')
                if r['operation']=='CLOSE':equal(r['label'],'owner-close');equal(r['contextSha256'],hashlib.sha256(b'').hexdigest());need(n==entry_counter,'CLOSE_ZERO_PENDING')
                item.update(request=index,requestFields=fields,requestValue=r,requestRaw=raw);active=n
            elif name=='GUARD_RPC_REPLY':
                n=decimal(fields['guardSequence']);equal(n,active,'REPLY_REQUIRES_EXACT_CURRENT_REQUEST');item=self.items[n];need(item['reply'] is None,'ONE_USE_REPLY')
                raw=decode64(fields['rawBase64']);r=rpc(raw,2048);closed(r,REPLY_KEYS)
                equal(r['schema'],'e02-fresh-guard-response-v1');equal(r['ok'],True,'DENIED_GUARD_CANNOT_CONTRIBUTE')
                for k in REQUEST_KEYS.split()[1:]:equal(r[k],item['requestValue'][k],'EXACT_REPLY_REQUEST_CONTEXT')
                equal(r['requestSha256'],hashlib.sha256(item['requestRaw']).hexdigest(),'RAW_REQUEST_SHA_JOIN')
                if r['operation']=='CLOSE':equal(r['clocks'],None)
                else:
                    closed(r['clocks'],'Utc Mono Boot bootId');equal(r['clocks']['bootId'],lease['bootId'])
                    for k in ('Utc','Mono','Boot'):need(lease['issued'+k+'Ns']<=decimal(r['clocks'][k])<lease['deadline'+k+'Ns'],'CORE_CLOCK_WITHIN_ORIGINAL_LEASE')
                item.update(reply=index,replyFields=fields,replyValue=r)
            elif name=='GUARD_EXIT':
                n=decimal(fields['guardSequence']);equal(n,active,'CONSUMPTION_REQUIRES_CURRENT_RPC');item=self.items[n];need(item['reply'] is not None and item['exit'] is None,'ONE_CONSUMED_SUCCESS_AFTER_REPLY')
                equal(fields['label'],item['requestValue']['label']);equal(fields['ok'],True);equal(fields['error'],None);equal(fields['consumed'],True)
                q=item['requestFields'];r=item['replyValue']
                for clock,key,deadline in [('Utc','consumedUtcUpperNs','decisionDeadlineUtcNs'),('Mono','consumedMonoNs','decisionDeadlineMonoNs'),('Boot','consumedBootUpperNs','decisionDeadlineBootNs')]:
                    consumed=decimal(fields[key]);need(lease['issued'+clock+'Ns']<=consumed<lease['deadline'+clock+'Ns'] and consumed<decimal(q[deadline]),'NO_STALE_HELD_OK_OR_LATE_EFFECT')
                    if r['clocks'] is not None:need(consumed>=decimal(r['clocks'][clock]),'NO_POST_REPLY_CLOCK_ROLLBACK')
                # observedAttempt is a live phase annotation, not the immutable RPC
                # context. Global watchdogs may queue across a stage transition, and
                # flow09/15 deliberately change the stage inside the protected effect.
                item['exit']=index;active=None
                if r['operation']=='CLOSE':closed_owner=True
            elif name=='GUARD_HELPER_LAUNCH':
                need(not launched and entry_counter==1 and not created,'ONE_LAZY_HELPER_LAUNCH');launched=True
                equal(fields['executable'],'/guard-python/lib/ld-linux-x86-64.so.2')
                equal(fields['argv'],['--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s','/input/guard-helper.py',instance,lease_sha,str(helper_pin['bytes']),helper_pin['sha256']],'EXACT_PINNED_HELPER_ARGV')
            elif name=='GUARD_HELPER_CREATED':
                need(launched and not created,'ONE_HELPER_CREATED');integer(fields['pid'],1);created=True
            else:
                need(closed_owner and name not in life,'NATURAL_LIFECYCLE_AFTER_CLOSE_ONCE');life[name]=index
                if name in ('GUARD_HELPER_EXIT','GUARD_HELPER_CLOSE'):equal(fields['code'],0);equal(fields['signal'],None)
                if name=='GUARD_HELPER_CLOSE':
                    for k in ('stdoutEOF','stderrEOF','exitSeen'):equal(fields[k],True)
                    need(all(k in life for k in ('GUARD_HELPER_STDOUT_EOF','GUARD_HELPER_STDERR_EOF','GUARD_HELPER_EXIT')),'ACTUAL_CHILD_CLOSE_AFTER_BOTH_EOF_AND_EXIT')
        need(created and closed_owner and active is None and entry_counter==request_counter and all(x['exit'] is not None for x in self.items.values()),'COMPLETE_CLOSED_GUARD_OWNER')
        equal(set(life),{'GUARD_HELPER_STDOUT_EOF','GUARD_HELPER_STDERR_EOF','GUARD_HELPER_EXIT','GUARD_HELPER_CLOSE'},'WHOLE_OWNED_HELPER_LIFECYCLE')

    def effect(self, row_index, label, context, *, before=None, after=None):
        """Match one concrete observed effect to its consuming original RPC."""
        digest=hashlib.sha256(context).hexdigest()
        matches=[(n,x) for n,x in self.items.items() if x['requestValue']['operation']=='CHECK'
            and x['requestValue']['label']==label and x['requestValue']['contextSha256']==digest
            and x['reply']<row_index<x['exit'] and (before is None or before<x['entry'])
            and (after is None or x['exit']<after)]
        need(len(matches)==1,'EXACT_FRESH_RPC_EFFECT_CAUSAL_JOIN')
        n,item=matches[0]
        if 'observedAttempt' in item['entryFields']:
            equal(self.rows[row_index]['observedAttempt'],item['entryFields']['observedAttempt'],'CURRENT_EFFECT_STAGE_CONTEXT')
        key=(row_index,label);need(key not in self.used_effects and n not in self.used_effect_permits,'NO_EFFECT_DOUBLE_CONSUMPTION');self.used_effects.add(key);self.used_effect_permits.add(n)
        return n,item
