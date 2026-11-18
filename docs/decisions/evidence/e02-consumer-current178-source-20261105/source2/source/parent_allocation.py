"""Current producer4 parent slot and actual command custody DATA validation."""
import hashlib
from pathlib import Path
from strict import closed,equal,integer,json_bytes,need
from async_guard import ALLOCATION,GuardTrace


def validate_audit(value, rows, window, lease, helper_pin, index, operation):
    closed(value,'schema reservationIndex instance scope runId leaseSha256 configurationSha256 observations')
    equal(value['schema'],'e02-controller-guard-audit-v1');equal(value['reservationIndex'],index)
    equal(value['scope'],'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION')
    equal(value['runId'],window['runId']);equal(value['leaseSha256'],window['lease']['sha256'])
    equal(value['configurationSha256'],window['runConfig']['sha256'])
    contribution=b',"guardController":'+json_bytes(value)+b'}\n'
    need(len(contribution)<=ALLOCATION['proof'],'ENCODED_CONTROLLER_CONTRIBUTION_IN_PRECHARGED_SHARE')
    trace=GuardTrace(value['observations'],lease,window['lease']['sha256'],window['runId'],helper_pin,window['runConfig']['sha256'],controller=True)
    equal(value['instance'],trace.instance)
    expected_context=hashlib.sha256(json_bytes({'mode':operation})).hexdigest()
    labels=[x['requestValue']['label'] for x in trace.items.values()]
    for label in ('startup:plan','controller:socket-create','controller:connect','controller:response','owner-close'):
        equal(labels.count(label),1,'EXACT_CONTROLLER_REQUIRED_GUARD')
    need(all(label in ('startup:plan','controller:socket-create','controller:connect','controller:response','owner-close','controller:watchdog') for label in labels),'CLOSED_CONTROLLER_GUARD_LABELS')
    for item in trace.items.values():
        if item['requestValue']['operation']=='CHECK':equal(item['requestValue']['contextSha256'],expected_context,'EXACT_CONTROLLER_OPERATION_CONTEXT')
    return trace,len(contribution)


def validate_parent(files, window, command_rows, calls, helper_pin):
    root=Path(window['outputRoot']);members={p['path']:p for p in window['graphFiles']}
    def member(name):
        path=str(root/name);need(path in members,'PARENT_ALLOCATION_REQUIRED_MEMBER');return members[path]
    header_pin=member('capture-allocation-header.json');status_pin=member('capture-allocation-status.json')
    header=files.doc(header_pin);status=files.doc(status_pin)
    closed(header,'schema actor runId runConfig sourceBindingsSha256 originalLeaseSha256 allocation ledgerRoot ledgerBoundary prechargedServiceBytes controllerReservationsRefundable')
    equal(header['schema'],'e02-controller-capture-parent-allocation-v1');equal(header['actor'],'/root')
    config=files.doc(window['runConfig']);binding_sha=hashlib.sha256(json_bytes(config['sourceAndDependencyPins'])).hexdigest()
    for key,expected in [('runId',window['runId']),('runConfig',window['runConfig']),('originalLeaseSha256',window['lease']['sha256']),('sourceBindingsSha256',binding_sha),('allocation',ALLOCATION),('ledgerRoot',str(root/'controller-audit-reservations')),('ledgerBoundary','HOST_ONLY_OUTSIDE_FIXTURE_WRITABLE_MOUNTS'),('prechargedServiceBytes',8388608),('controllerReservationsRefundable',False)]:equal(header[key],expected,'PARENT_HEADER_CURRENT_JOIN')
    closed(status,'schema runId controllerAttempts controllerPoolPrechargedBytes servicePrechargedBytes globalMaximumBytes headerPrechargedLimit noRefunds scope')
    equal(status['schema'],'e02-controller-capture-parent-status-v1');equal(status['runId'],window['runId'])
    attempts=status['controllerAttempts'];integer(attempts,1,64);equal(attempts,len(calls),'ALL_ATTEMPTS_HAVE_WHOLE_CALL_CUSTODY')
    for key,expected in [('controllerPoolPrechargedBytes',attempts*131072),('servicePrechargedBytes',8388608),('globalMaximumBytes',16777216),('headerPrechargedLimit',4096),('noRefunds',True),('scope','CONSISTENCY_ONLY_NOT_POSTHOC_ADMISSION')]:equal(status[key],expected)
    need(header_pin['bytes']+status_pin['bytes']<=4096,'PARENT_HEADER_PREPAY_NOT_EXPANDED')
    lease=files.doc(window['lease']);instances=set();expected_paths=set()
    for index,(seq,(_,call)) in enumerate(calls.items(),1):
        reserve_pin=member('controller-audit-reservations/%02d-reserved.json'%index)
        result_pin=member('controller-audit-reservations/%02d-result.json'%index)
        expected_paths|={reserve_pin['path'],result_pin['path']}
        reserve=files.doc(reserve_pin);result=files.doc(result_pin)
        closed(reserve,'schema actor index operation runId runConfig originalLeaseSha256 sourceBindingsSha256 slotBytes proofBytes ledgerBytes diagnosticsBytes poolPrechargedBytes refundAllowed')
        for key,expected in [('schema','e02-controller-audit-parent-reservation-v1'),('actor','/root'),('index',index),('operation',call['operation']),('runId',window['runId']),('runConfig',window['runConfig']),('originalLeaseSha256',window['lease']['sha256']),('sourceBindingsSha256',binding_sha),('slotBytes',131072),('proofBytes',122880),('ledgerBytes',4096),('diagnosticsBytes',4096),('poolPrechargedBytes',index*131072),('refundAllowed',False)]:equal(reserve[key],expected,'EXACT_NONREFUNDABLE_PARENT_RESERVATION')
        closed(result,'schema index runId operation commandSequence command stdout helperInstance encodedAuditContributionBytes state')
        command=command_rows[seq-1]
        for key,expected in [('schema','e02-controller-audit-parent-completion-v1'),('index',index),('runId',window['runId']),('operation',call['operation']),('commandSequence',seq),('command',call['command']),('stdout',command['stdout']),('state','NATURAL_COMPLETE_REQUIRES_WHOLE_CONSUMER')]:equal(result[key],expected,'EXACT_PARENT_COMPLETION_COMMAND_JOIN')
        need(reserve_pin['bytes']+result_pin['bytes']<=4096,'SLOT_LEDGER_BOUND')
        # Exact already retained command stdout, no duplicate reply allocation.
        equal(call['reply'],command['stdout'],'SAME_RETAINED_REPLY_PIN_NO_SECOND_RPC_COPY')
        for key in ('stdoutEOF','stderrEOF','reaped'):equal(command[key],True)
        equal(command['exit'],0);equal(command['forced'],False);equal(files.read(command['stderr']),b'')
        audit=files.doc(call['reply'])['guardController']
        trace,contribution=validate_audit(audit,command_rows,window,lease,helper_pin,index,call['operation'])
        equal(result['helperInstance'],trace.instance);equal(result['encodedAuditContributionBytes'],contribution)
        need(trace.instance not in instances,'DISTINCT_CONTROLLER_OWNED_HELPER');instances.add(trace.instance)
        argv=command['argv'];equal(argv[:4],['/usr/bin/docker','exec','--env','NBDP_CONTROLLER_AUDIT_SLOT='+str(index)])
    ledger_paths={p for p in members if Path(p).is_relative_to(root/'controller-audit-reservations')}
    equal(ledger_paths,expected_paths,'NO_EXTRA_REUSED_OR_MISSING_PARENT_SLOT')
    need(8388608+attempts*131072<=16777216,'UNCHANGED_GLOBAL_NEW_CAPTURE_BOUND')
    return instances
