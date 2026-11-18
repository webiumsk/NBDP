from pathlib import Path
import ast,json,hashlib,difflib
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');P=R/'experiments/prototypes/e02_ordinary_minimum_v2';E=R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2';C=E/'current-controls-r1';OLD=R/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2/current-controls-r1/capture-controls.py'
assert not C.exists();C.mkdir()
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
source=pin(E/'subject.json');manifest=pin(E/'artifact-manifest.json');frozenPlan=pin(E/'execution-control-plan.json');mainPlan=json.loads((E/'execution-control-plan.json').read_bytes());old=OLD.read_text();s=old
s=s.replace('once-only18/27/6 synthetic DATA','once-only20/8/7 synthetic DATA').replace("SOURCE = ROOT / 'experiments/prototypes/e02_transport_query_diagnostic_v2'", "SOURCE = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v2'")
s=s.replace("SOURCE_SHA = 'aece375c76f20d8c738d34e57feb19e50c2ccfc28cb09ffc9347481d2f526b85'", "SOURCE_SHA = '"+source['sha256']+"'")
s=s.replace("MANIFEST_SHA = '99c2e428d87ca19cbbc19c3912e3c7ff548217dba540c517ffab81852dd8bb9c'", "MANIFEST_SHA = '"+manifest['sha256']+"'")
s=s.replace("FROZEN_PLAN_SHA = 'bf227bade861821099eed7f3c664ab8f56259b028000ea5b42024821f3fef1fb'", "FROZEN_PLAN_SHA = '"+frozenPlan['sha256']+"'")
s=s.replace("PREP/'control-plan.json'", "PREP/'execution-control-plan.json'")
s=s.replace("assert plan['separateScopes']==current_plan['separateScopes']\n    assert plan['rawRetentionBytes']==LIMITS and all(s['timeoutSeconds']==60 for s in plan['separateScopes'])", "assert len(plan['separateScopes'])==len(current_plan['separateScopes'])==3\n    for original,current in zip(plan['separateScopes'],current_plan['separateScopes']):\n        assert (original['name'],original['argv'],original['plannedChecks'],original['namedCases'])==(current['name'],current['argv'],current['count'],current['expectedCases'])\n        assert original['timeoutSeconds']==current['timeoutSeconds']==60\n        assert original['stdoutRetentionBytes']==LIMITS['stdout'] and original['stderrRetentionBytes']==LIMITS['stderr']")
s=s.replace("inputs['schema']=='e02-transport-source2-control-frozen-inputs-v1'", "inputs['schema']=='e02-producer2-control-frozen-inputs-v1'")
s=s.replace("assert inputs['sourceSubject']==source and pin(PREP/'proposed-run-config.json')==inputs['configuration']", "assert inputs['sourceSubject']==source\n    assert [pin(PREP/('proposed-'+role+'-run-config.json')) for role in ('incoming','archive')]==inputs['configurations']")
s=s.replace("{s['name']:s['count'] for s in plan['separateScopes']}", "{s['name']:s['count'] for s in current_plan['separateScopes']}")
s=s.replace("'e02-transport-source2-controls-root-ack-v1'", "'e02-producer2-controls-root-ack-v1'")
s=s.replace("'diagnosticRuntimeAuthorized'", "'ordinaryRuntimeAuthorized'")
s=s.replace("'cryptoOrNativeAuthorized'", "'protocolCryptoOrNativeAuthorized'")
s=s.replace("if prefix=='source':assert r['decision']=={'qa':'ACCEPT_DIAGNOSTIC_SOURCE_CONFIG_ONLY','security':'ACCEPT_SOURCE_FOR_SCOPED_DATA_CONTROLS_ONLY'}[role]", "assert r['decision'] in ACCEPTED_REVIEW_DECISIONS[prefix][role]")
s=s.replace("'configuration':inputs['configuration']", "'configurations':inputs['configurations']")
a=s.index('def output_shape(');b=s.index('\n\ndef one_scope(',a)
s=s[:a]+'''def output_shape(scope,raw):
    if scope['name'] in ('public-identity-metadata','producer2-source-wiring'):
        assert raw['stdout']==b''
        # Fixed original argv has default unittest verbosity. Exact dots/count/
        # OK, no skip/failure/error/extra output is permitted.
        match=re.fullmatch(rb'([.]+)\\n-{70}\\nRan ([0-9]+) tests? in [^\\n]+\\n\\nOK\\n',raw['stderr'])
        assert match and len(match[1])==scope['count'] and int(match[2])==scope['count']
        return scope['count'],{scope['name']:scope['count']}
    assert scope['name']=='observation-model'
    assert raw['stderr']==b'' and raw['stdout'].endswith(b'\\n') and raw['stdout'].count(b'\\n')==1
    value=strict(raw['stdout'])
    assert set(value)=={'schema','ok','checks','cases','scope'}
    assert value['schema']=='e02-producer2-observation-model-controls-v1' and value['ok'] is True
    assert value['scope']=='SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME'
    assert type(value['checks']) is int and value['checks']==scope['count']==20
    assert value['cases']==scope['expectedCases'] and len(value['cases'])==20 and len(set(value['cases']))==20
    return 20,{'shared-budget-guard-proxy-and-exchange-adapter-models':20}
'''+s[b:]
s=s.replace('e02-transport-source2-pure-scope-execution-v1','e02-producer2-pure-scope-execution-v1')
s=s.replace("Synthetic DATA only; no primary/consumer/runtime/crypto/native/client execution or external/canonicalPASS, SDK or experiment authority.", "Synthetic DATA/model and fixed-public NIP19 encoding/checksum/hash metadata only; no actual guard/network/primary/consumer/runtime/NIP44/sign/encrypt/decrypt/native/client execution or external/canonicalPASS, SDK or experiment authority.")
s=s.replace("'ONCE_FIXED_18_27_6_DATA_ONLY'", "'ONCE_FIXED_20_8_7_DATA_ONLY'")
s=s.replace("scopes=doc(PREP/'execution-control-plan.json')['separateScopes'];assert [s['count'] for s in scopes]==[18,27,6]", "scopes=doc(CAPTURE/'control-plan.json')['separateScopes'];assert [s['count'] for s in scopes]==[20,8,7]")
s=s.replace('e02-transport-source2-current-control-execution-v1','e02-producer2-current-control-execution-v1').replace('e02-transport-source2-current-control-artifact-manifest-v1','e02-producer2-current-control-artifact-manifest-v1')
s=s.replace("'noDiagnosticRuntimePrimaryConsumerGuardNetworkSdkServices'", "'noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices'")
# Decision values must be finalized only from actual SOURCE decisions. The
# pending construction token is NOT an accepted authority or executable grant.
s=s.replace("LIMITS = {'stdout':1048576,'stderr':262144}", "LIMITS = {'stdout':1048576,'stderr':262144}\nACCEPTED_REVIEW_DECISIONS = None  # SOURCE-ONLY DRAFT: awaiting actual SOURCE literals before freeze")
(C/'capture-controls.py').write_text(s)
scopes=[]
for one in mainPlan['separateScopes']:
 scopes.append(dict(name=one['name'],argv=one['argv'],count=one['plannedChecks'],expectedCases=one['namedCases'],timeoutSeconds=60))
plan=dict(schema='e02-producer2-fixed-control-capture-plan-v1',state='CAPTURE_SOURCE_DRAFT_NOT_EXECUTABLE_NO_GRANT',actor='/root/ordinary_api35_source',sourceSubject=source,frozenSourcePlan=frozenPlan,runner=pin(C/'capture-controls.py'),separateScopes=scopes,rawRetentionBytes={'stdout':1048576,'stderr':262144},retentionMeaning='POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP',scopeMeaning='20 fake fs/socket/guard observer models,8 fixed public NIP19 format DATA,7 source AST/hash wiring; no real protocol crypto/native/network/guard/SDK/services',onceCommand=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(C/'capture-controls.py'),'--execute-once','--root-ack-sha','EXTERNAL_ACTUAL_ROOT_ACK_SHA256_REQUIRED_NOT_AN_APPROVAL'],stopFirstFailure=True,noRetry=True,originalApiResponses='Caller persists exact actual toolName/actualArguments/unmodifiedResponse immediately and separately; no invented outer lifecycle fields.',unmodifiedMainSourceSubject=source)
save(C/'control-plan.json',plan)
# Fixed input closure supplied by main source, plus explicit SDK inventory
# manifests only; binary input Pins remain binary and are never JSON-decoded.
inputs=json.loads((E/'frozen-input-closure.json').read_bytes())['descriptors']
configs=[json.loads((E/('proposed-'+role+'-run-config.json')).read_bytes()) for role in ('incoming','archive')]
extra=[pin(E/'subject.json'),pin(E/'artifact-manifest.json'),pin(E/'frozen-input-closure.json')]
for config in configs:extra+=[config['sdkInventory'],config['guardBundleInventory']]
by={d['path']:d for d in inputs}
for d in extra:
 assert d['path'] not in by or by[d['path']]==d;by[d['path']]=d
save(C/'frozen-inputs.json',dict(schema='e02-producer2-control-frozen-inputs-v1',sourceSubject=source,configurations=[pin(E/('proposed-'+role+'-run-config.json')) for role in ('incoming','archive')],node=mainPlan['interpreters']['node'],python=mainPlan['interpreters']['python'],files=[by[k] for k in sorted(by)],sdkScope='Read/hash fixed SDK and guard inventory JSON manifests. No SDK tools, guest provisioning or JSON decoding of APK/SDK/binary bodies. Current runtime SDK434/APK/helper validation remains separately mandatory before any actual ordinary grant.'))
# AST/source artifacts may be produced without import/evaluation.
before=ast.dump(ast.parse(old),indent=2,include_attributes=False);after=ast.dump(ast.parse(s),indent=2,include_attributes=False)
(C/'capture-full-typed-ast-before.txt').write_text(before+'\n');(C/'capture-full-typed-ast-after.txt').write_text(after+'\n');(C/'capture-full-typed-ast.diff').write_text(''.join(difflib.unified_diff((before+'\n').splitlines(True),(after+'\n').splitlines(True),fromfile=str(OLD),tofile=str(C/'capture-controls.py'))))
(C/'capture-full-source.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(OLD),tofile=str(C/'capture-controls.py'))))
print(json.dumps({'state':'DRAFT_CAPTURE_SOURCE_ONLY_WAITING_ACTUAL_SOURCE_LITERALS_BEFORE_FREEZE','runner':pin(C/'capture-controls.py'),'inputCount':len(by),'mainSourceUnchanged':pin(E/'subject.json')==source,'sourceControlsExecuted':0}))
