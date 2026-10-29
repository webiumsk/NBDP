"""SOURCE editor only. Never imports producer or executes experiment code."""
from pathlib import Path
p=Path(__file__).resolve().parent
f=p/'supervisor.py';s=f.read_text()
s=s.replace("        stream.write(raw)\n", "        need(stream.write(raw) == len(raw), 'Short immutable proof write; no repair')\n",1)
s=s.replace("        self.inputs_sealed = False", "        self.controller_audit_attempts = 0\n        self.controller_audit_ledger_charges = {}\n        self.capture_header_charged = 0\n        self.capture_allocation_poison = None\n        self.capture_allocation_initialized = False\n        self.inputs_sealed = False",1)
a=s.index('    def fixture(self, operation):');b=s.index('\n    def snapshot',a)
s=s[:a]+'''    def capture_fault(self, error):
        if self.capture_allocation_poison is None:
            self.capture_allocation_poison = str(error)[:1024]
        self.lease.revoke('Controller audit allocation failed: ' + self.capture_allocation_poison)

    def capture_header(self, name, value):
        raw = jsonbytes(value)
        need(self.capture_allocation_poison is None, 'Sticky capture allocation fault')
        need(self.capture_header_charged + len(raw) <= 4096, 'Prepaid service header/footer bound')
        self.capture_header_charged += len(raw)  # No refund, before proof write.
        return put(self.out / name, raw)

    def initialize_capture_allocation(self):
        try:
            need(not self.capture_allocation_initialized, 'One capture allocation header')
            self.capture_allocation_initialized = True
            self.capture_header('capture-allocation-header.json', {
                'schema':'e02-controller-capture-parent-allocation-v1', 'actor':'/root',
                'runId':self.plan['runId'], 'runConfig':self.plan_pin,
                'sourceBindingsSha256':hashlib.sha256(jsonbytes(self.plan['sourceAndDependencyPins'])).hexdigest(),
                'originalLeaseSha256':self.lease_sha,
                'allocation':{'total':16777216,'service':8388608,'serviceHeader':4096,
                    'serviceDiagnostics':4096,'controllerSlots':64,'slot':131072,
                    'proof':122880,'ledger':4096,'diagnostics':4096,'wrapper':1024},
                'ledgerRoot':str(self.out/'controller-audit-reservations'),
                'ledgerBoundary':'HOST_ONLY_OUTSIDE_FIXTURE_WRITABLE_MOUNTS',
                'prechargedServiceBytes':8388608,'controllerReservationsRefundable':False})
        except BaseException as error:
            self.capture_fault(error)

    def reserve_controller_audit(self, operation):
        try:
            need(self.capture_allocation_initialized and self.capture_allocation_poison is None,
                 'Parent allocation required before controller proof')
            need(operation in ('prepare','status','publish'), 'Fixed fixture operations')
            need(self.controller_audit_attempts < 64, 'Controller attempt65 denied before inspect/launch')
            self.controller_audit_attempts += 1  # Permanent predebit, including failed attempts.
            index = self.controller_audit_attempts
            self.controller_audit_ledger_charges[index] = 0
            self.controller_audit_ledger(index,'reserved',{
                'schema':'e02-controller-audit-parent-reservation-v1','actor':'/root',
                'index':index,'operation':operation,'runId':self.plan['runId'],
                'runConfig':self.plan_pin,'originalLeaseSha256':self.lease_sha,
                'sourceBindingsSha256':hashlib.sha256(jsonbytes(self.plan['sourceAndDependencyPins'])).hexdigest(),
                'slotBytes':131072,'proofBytes':122880,'ledgerBytes':4096,'diagnosticsBytes':4096,
                'poolPrechargedBytes':index*131072,'refundAllowed':False})
            return index
        except BaseException as error:
            self.capture_fault(error)

    def controller_audit_ledger(self, index, suffix, value):
        raw = jsonbytes(value)
        need(index in self.controller_audit_ledger_charges and suffix in ('reserved','result'),
             'Parent-owned existing slot only')
        need(self.controller_audit_ledger_charges[index] + len(raw) <= 4096,
             'Controller slot ledger/status overflow')
        self.controller_audit_ledger_charges[index] += len(raw)
        # Root output ledger is never within /session/fixtures, /session/control,
        # /input or any other fixture-writable bind. No child-assigned capacity.
        return put(self.out / 'controller-audit-reservations' / ('%02d-%s.json' % (index,suffix)),raw)

    def finish_capture_allocation(self):
        if self.capture_allocation_poison is not None:
            return  # No repair/refund or positive fallback after poisoned ledger.
        try:
            self.capture_header('capture-allocation-status.json',{
                'schema':'e02-controller-capture-parent-status-v1','runId':self.plan['runId'],
                'controllerAttempts':self.controller_audit_attempts,
                'controllerPoolPrechargedBytes':self.controller_audit_attempts*131072,
                'servicePrechargedBytes':8388608,'globalMaximumBytes':16777216,
                'headerPrechargedLimit':4096,'noRefunds':True,
                'scope':'CONSISTENCY_ONLY_NOT_POSTHOC_ADMISSION'})
        except BaseException as error:
            self.capture_fault(error)

    def fixture(self, operation):
        index = self.reserve_controller_audit(operation)  # Before inspect/spawn/first slot proof.
        command_sequence = None
        try:
            self.check(); self.inspect('fixture')
            command_sequence = self.sequence + 1
            raw = self.command(['exec','--env','NBDP_CONTROLLER_AUDIT_SLOT='+str(index),
                self.ids['fixture'],'/usr/local/bin/node','/input/fixture.mjs',operation],55)
            value = strict(raw); audit = value['guardController']
            need(set(audit) == {'schema','reservationIndex','instance','scope','runId',
                 'leaseSha256','configurationSha256','observations'}
                 and audit['schema'] == 'e02-controller-guard-audit-v1'
                 and audit['reservationIndex'] == index
                 and audit['runId'] == self.plan['runId']
                 and audit['leaseSha256'] == self.lease_sha
                 and audit['configurationSha256'] == self.plan_pin['sha256']
                 and re.fullmatch('[0-9a-f]{32}',audit['instance'])
                 and audit['scope'] == 'ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION',
                 'Exact assigned controller audit binding required')
            contribution = b',"guardController":' + json.dumps(audit,separators=(',',':'),ensure_ascii=False).encode() + b'\\n'
            need(len(contribution) <= 122880, 'Actual encoded controller proof share')
            command = strict((self.out / ('commands/%04d.json' % command_sequence)).read_bytes())
            need(checked(command['stdout']).read_bytes() == raw and command['stdoutEOF']
                 and command['stderrEOF'] and command['reaped'] and command['exit'] == 0
                 and not command['forced'] and len(checked(command['stderr']).read_bytes()) == 0,
                 'Whole actual controller command custody required')
            self.controller_audit_ledger(index,'result',{
                'schema':'e02-controller-audit-parent-completion-v1','index':index,
                'runId':self.plan['runId'],'operation':operation,
                'commandSequence':command_sequence,'command':pin(self.out/('commands/%04d.json'%command_sequence)),
                'stdout':command['stdout'],'helperInstance':audit['instance'],
                'encodedAuditContributionBytes':len(contribution),'state':'NATURAL_COMPLETE_REQUIRES_WHOLE_CONSUMER'})
            self.check(); return raw
        except BaseException as error:
            # No successful ordinal reuse, overwritten status or partial ledger repair.
            self.capture_fault(error)
''' +s[b:]
s=s.replace("    try:\n        for descriptor in config['sourceAndDependencyPins']:","    try:\n        runtime.initialize_capture_allocation()\n        for descriptor in config['sourceAndDependencyPins']:",1)
s=s.replace("        final_code = finalize(out,", "        try:\n            runtime.finish_capture_allocation()\n        except BaseException as failure:\n            error = error or ('Capture allocation footer failed: ' + repr(failure))\n        final_code = finalize(out,",1)
f.write_text(s)
# Driver binds exact already-retained stdout; no duplicate RPC proof write.
f=p/'android_driver.py';s=f.read_text();s=s.replace("    reply_pin = runtime.put_bytes('evidence/fixture-%02d-%s-reply.json' % (sequence, operation), raw)","    retained_command = loads((runtime.out / ('commands/%04d.json' % runtime.sequence)).read_bytes())\n    reply_pin = retained_command['stdout']\n    need(read(reply_pin, 16777216) == raw, 'Exact retained command.stdout reply required; no duplicate RPC copy')")
f.write_text(s)
