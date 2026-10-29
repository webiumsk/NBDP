"""One-time SOURCE transformation; no module imports or execution."""
from pathlib import Path
p=Path(__file__).with_name('observer.py');s=p.read_text();s=s.replace('Producer2 observation DATA joins.','Producer4 asynchronous observation DATA joins.').replace('import wire\n','import wire\nfrom async_guard import ALLOCATION, PROOF_LIMIT, FIELDS as GUARD_FIELDS, GuardTrace\n')
s=s.replace('LIMIT = 16777216','LIMIT = PROOF_LIMIT')
s=s.replace("closed(value, 'schema budget phase'); equal(value['schema'], 'e02-minimum-observer-state-v2')", "closed(value, 'schema budget phase allocation serviceDiagnostics serviceHeaderPrepaidBytes'); equal(value['schema'], 'e02-minimum-observer-state-v3')\n    equal(value['allocation'], ALLOCATION);equal(value['serviceHeaderPrepaidBytes'],4096)\n    account_state(value['serviceDiagnostics'],4096)")
s=s.replace("closed(b, 'schema limit intendedTotalBytes acknowledgedTotalBytes streams poisoned firstError physicalBytes physicalMeaning lastAttempt')", "closed(b, 'schema limit intendedTotalBytes acknowledgedTotalBytes streams poisoned firstError physicalBytes physicalMeaning lastAttempt allocationAccount')\n    account_state(b['allocationAccount'],PROOF_LIMIT)")
s=s.replace("'e02-minimum-aggregate-capture-budget-v2'","'e02-minimum-aggregate-capture-budget-v3'")
s=s.replace("equal(b['acknowledgedTotalBytes'], len(phase_raw) + len(proxy_raw))", "equal(b['acknowledgedTotalBytes'], len(phase_raw) + len(proxy_raw))\n    need(b['allocationAccount']['chargedBytes']>=b['intendedTotalBytes'],'SERVICE_ACCOUNT_COVERS_BOTH_STREAMS')")
# Closed actual guard fields override legacy pair fields; other phase DTOs remain exact.
s=s.replace("        self.files, self.window, self.proxy = files, window, proxy", "        self.files, self.window, self.proxy = files, window, proxy\n        self.lease=files.doc(window['lease'])\n        from consumer import CURRENT_WORKERS\n        self.helper_pin=next(p for p in CURRENT_WORKERS if Path(p['path']).name=='guard-helper.py')")
s=s.replace("            name = row.get('phase'); need(name in FIELDS, 'CLOSED_PHASE_NAME')\n            keys = COMMON + ' ' + FIELDS[name]", "            name = row.get('phase'); need(name in FIELDS or name in GUARD_FIELDS, 'CLOSED_PHASE_NAME')\n            keys = COMMON + ' ' + (GUARD_FIELDS[name] if name in GUARD_FIELDS else FIELDS[name])")
start=s.index("                if name not in ('GUARD_ENTRY', 'GUARD_EXIT'):")
end=s.index("            if 'connection' in row:",start)
s=s[:start]+"                if name not in GUARD_FIELDS: need(row['label'] in labels, 'CLOSED_EXCHANGE_PHASE_LABEL')\n"+s[end:]
start=s.index("            if name == 'GUARD_ENTRY':")
end=s.index("            if name == 'TIMER_ARMED':",start)
s=s[:start]+s[end:]
s=s.replace("        self.labels = labels", "        self.labels = labels\n        self.guards=GuardTrace(self.rows,self.lease,window['lease']['sha256'],window['runId'],self.helper_pin,window['runConfig']['sha256'])")
s=s.replace("            value = files.doc(members[str(final)]); closed(value, 'observer error secondaryErrors')\n            equal(value['error'], None); equal(value['secondaryErrors'], [])", "            value = files.doc(members[str(final)]); closed(value, 'observer snapshotTiming error secondaryErrors normalOwnedHelperClose')\n            equal(value['snapshotTiming'],'BEFORE_THIS_FINAL_RECORD_WRITE');equal(value['normalOwnedHelperClose'],True)\n            equal(value['error'], None); equal(value['secondaryErrors'], [])\n            service_members=[d for d in window['graphFiles'] if Path(d['path']).is_relative_to(root/'session/fixtures')]\n            retained_before=sum(d['bytes'] for d in service_members if d['path']!=str(final))\n            charged=value['observer']['budget']['allocationAccount']['chargedBytes']\n            need(retained_before<=charged and charged+members[str(final)]['bytes']<=PROOF_LIMIT,'ALL_RETAINED_SERVICE_PROOF_IN_SAME_SHARE')")
s=s.replace("        if str(final) in members:","        need(str(final) in members,'WHOLE_NORMAL_FINAL_OBSERVER_REQUIRED')\n        if str(final) in members:")
s=s.replace("            for row in rows: self.guard_after(row['sequence'], guard)","            for row in rows: self.guard_after(row['sequence'],guard,wire.decode64(row['rawBase64']))")
start=s.index("            self.guard_after(row['sequence'], 'exchange:'")
end=s.index("        completions =",start)
s=s[:start]+"            label='exchange:'+row['label']+':backend-message'\n            item=self.guard_after(row['sequence'],label,wire.decode64(row['rawBase64']))\n            passed=[(j,r) for j,r in enumerate(self.rows) if r['phase']=='BACKEND_MESSAGE_GUARD_PASSED' and r['label']==row['label'] and item['reply']<j<item['exit']]\n            need(len(passed)==1,'RAW_PARSE_FRESH_GUARD_EFFECT_REQUIRED')\n            equal(passed[0][1]['messageType'],wire.frame(wire.decode64(row['rawBase64']))[0],'RAW_GUARD_PARSE_ORDER')\n"+s[end:]
start=s.index('    def guard_after(');end=s.index('    def _proxy_send_chains',start)
s=s[:start]+'''    def guard_after(self, sequence, label, context):
        # Callback rows may interleave; request identity/context and consumed fence
        # determine causality. Global sequence remains independent of guardSequence.
        digest=hashlib.sha256(context).hexdigest()
        matches=[item for item in self.guards.items.values() if item['entry']>=sequence
            and item['requestValue']['label']==label
            and item['requestValue']['contextSha256']==digest]
        need(matches,'CALLBACK_REQUIRES_FRESH_ASYNC_GUARD')
        item=min(matches,key=lambda x:x['entry'])
        equal(self.rows[sequence-1]['observedAttempt'],item['entryFields']['observedAttempt'],'CALLBACK_GUARD_STAGE_CONTEXT')
        return item

'''+s[end:]
s=s.replace("            if field == 'callback' and row['target'] == 'APP': self.guard_after(row['sequence'], 'proxy:app-send-callback')", "            if field == 'complete' and row['target']=='APP':\n                source=self.proxy.row(row['sourceSequence'],'RELAY_TO_APP')\n                callback=item['entry']\n                callbacks=[r for r in self.rows if r['phase']=='PROXY_SEND_CALLBACK_ENTRY' and r['connection']==row['connection'] and r['target']=='APP' and r.get('sourceSequence')==row['sourceSequence']]\n                need(len(callbacks)==1,'ONE_APP_SEND_CALLBACK')\n                self.guards.effect(row['sequence']-1,'proxy:app-send-callback',wire.decode64(source['rawBase64']),before=callbacks[0]['sequence']-1)")
s=s.replace("            equal(send_phases['SEND_CALLBACK_GUARD_PASSED']['sequence'], callback['sequence'] + 3, 'SEND_PASSED_AFTER_ORIGINAL_GUARD_PAIR')\n            self.guard_after(callback['sequence'], 'exchange:' + label + ':send-callback')", "            self.guards.effect(send_phases['SEND_CALLBACK_GUARD_PASSED']['sequence']-1,'exchange:'+label+':send-callback',raw,before=callback['sequence']-1)\n            self.guards.effect(intent[0]['sequence']-1,'exchange:'+label+':send-before',raw)")
s=s.replace("    closed(value, 'schema budget phase allocation", "    closed(value, 'schema budget phase allocation")
insert=s.index('\ndef raw_lines')
s=s[:insert]+'''
def account_state(value,limit):
    closed(value,'limit chargedBytes intendedBytes poisoned firstError')
    equal(value['limit'],limit);equal(value['poisoned'],False);equal(value['firstError'],None)
    integer(value['chargedBytes'],0,limit);equal(value['chargedBytes'],value['intendedBytes'])

'''+s[insert:]
p.write_text(s)
