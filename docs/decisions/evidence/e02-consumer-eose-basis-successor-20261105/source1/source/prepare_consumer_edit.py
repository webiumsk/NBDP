"""SOURCE transformation from immutable predecessor, no code imports/evaluation."""
from pathlib import Path
import ast,json,hashlib
root=Path(__file__).parent;p=root/'consumer.py';s=p.read_text();producer_path=Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r4-source4-metadata-r1/subject.json');producer=json.loads(producer_path.read_text())
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def source(n):return next(v for v in producer['sources'] if Path(v['path']).name==n)
constants=dict(PRODUCER_SHA=pin(producer_path)['sha256'],CONTRACT_SHA=source('EXPORT-CONTRACT.md')['sha256'],ADOPTION_SHA='2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287',RUNTIME_SCOPE=producer['scope'],DRAFT_FINAL_ADAPTER_READY=False,CURRENT_PRODUCER_SCHEMA=producer['schema'],CURRENT_PRODUCER=pin(producer_path),CURRENT_SOURCE_PLAN=producer['controlPlan'],CURRENT_GUARD_DTO=producer['typedContract'],CURRENT_EXPORT_CONTRACT=source('EXPORT-CONTRACT.md'),CURRENT_AMETHYST_APK=producer['dataPrerequisitesOnly']['amethystApk'],CURRENT_HELPER_APK=producer['dataPrerequisitesOnly']['helperApk'],CURRENT_ARTIFACT_BINDINGS=source('rebuilt-artifact-bindings.json'),CURRENT_CONFIGURATIONS=list(producer['configurations'].values()),CURRENT_WORKERS=producer['runtimeSources'],CURRENT_PRODUCER_SOURCE_ACCEPTANCE=pin('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-source4-acceptance-20261028/acceptance.json'),CURRENT_CAPTURE_SOURCE=pin('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-preparation-r1/source4/code-subject.json'),CURRENT_CAPTURE_SOURCE_ACCEPTANCE=pin('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-capture-source4-acceptance-20261028/acceptance.json'),CURRENT_ADMISSION_DATA_ACCEPTANCE=pin('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-capture-admission21-canonical-r1-20261028/acceptance.json'),CURRENT_DATA_ACCEPTANCE_CONTRACT=pin('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer4-control-capture-preparation-20261028/current-producer-data-acceptance-contract.json'),CURRENT_CONTROL_ACTORS=['/root','/root/producer4_nonblocking_source','/root/r5_plan_fix','/root/completion_wrapper','/root/consumer6_source'],CURRENT_PRODUCER_CONTROL_DATA=None,CURRENT_PRODUCER_CONTROL_ACCEPTANCE=None,CURRENT_HELPER_PROBE_DATA=None,CURRENT_HELPER_PROBE_ACCEPTANCE=None)
start=s.index('PRODUCER_SHA =');end=s.index('CONFIG_KEYS =');s=s[:start]+'# Current accepted SOURCE only. Actual260/probe anchors stay NULL until issued.\n'+''.join(k+' = '+repr(v)+'\n' for k,v in constants.items())+'\n'+s[end:]
start=s.index('def require_current_source_profile():');end=s.index('\ndef external(',start)
s=s[:start]+'''def require_current_source_profile():
    # No source-only fixture, previous139 controls or mocked admission21 can
    # activate current ordinary-window consumption.
    need(DRAFT_FINAL_ADAPTER_READY is True, 'CONSUMER6_SOURCE_ONLY_NO_CURRENT_RUNTIME_BINDINGS')
    need(all(p is not None for p in (CURRENT_PRODUCER_CONTROL_DATA,CURRENT_PRODUCER_CONTROL_ACCEPTANCE,
         CURRENT_HELPER_PROBE_DATA,CURRENT_HELPER_PROBE_ACCEPTANCE)), 'CURRENT260_AND_ACTUAL_HELPER_PROBE_DATA_REQUIRED')

'''+s[end:]
start=s.index('def current_producer(');end=s.index('\ndef capture_output(',start)
s=s[:start]+'''def current_producer(files,descriptor):
    equal(descriptor,CURRENT_PRODUCER,'EXACT_CURRENT_PRODUCER4_SOURCE4_METADATA_R1')
    producer=files.doc(descriptor);equal(producer['schema'],CURRENT_PRODUCER_SCHEMA)
    equal(producer['version'],'SOURCE4');equal(producer['runtimeSourceCount'],22)
    equal(producer['typedContract'],CURRENT_GUARD_DTO);equal(producer['controlPlan'],CURRENT_SOURCE_PLAN)
    equal(producer['runtimeSources'],CURRENT_WORKERS);equal(list(producer['configurations'].values()),CURRENT_CONFIGURATIONS)
    need(len(producer['sources'])==61 and len({Path(p['path']).name for p in producer['sources']})==61,'EXACT_CURRENT61_SOURCE22_WORKERS')
    for p in producer['sources']:files.read(p)
    bindings=files.doc(CURRENT_ARTIFACT_BINDINGS)
    for prefix,artifact,schema,decision in (
      ('amethyst',CURRENT_AMETHYST_APK,'nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1','ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY'),
      ('helper',CURRENT_HELPER_APK,'nbdp-actual-artifact-data-acceptance-v1','ACCEPT_REBUILT_HELPER_ARTIFACT_ONLY')):
        equal(bindings[prefix+'Apk'],artifact)
        acceptance=files.doc(bindings[prefix+'Acceptance']);equal(acceptance['schema'],schema);equal(acceptance['decision'],decision)
        equal(acceptance['artifactQualified'],True);equal(acceptance['subject'],bindings[prefix+'Provenance'])
        equal(files.doc(bindings[prefix+'Provenance'])['apk'],artifact)
    for p in CURRENT_CONFIGURATIONS:
        config=files.doc(p);equal(config['sourceAndDependencyPins'],CURRENT_WORKERS)
        equal(config['profileId'],wire.PROFILE);equal(config['scope'],RUNTIME_SCOPE)
        equal(config['amethystApk'],CURRENT_AMETHYST_APK);equal(config['helperApk'],CURRENT_HELPER_APK)
        equal(config['originalLeaseSeconds'],1800)
    return producer

'''+s[end:]
# Keep useful generic ordered-review helper, remove old two-group A/B authority
# code entirely from runtime. Original bytes remain pinned predecessor sources.
start=s.index('def capture_output(');end=s.index('def graph(',start)
old=Path('/Data/nbdp-e02-tooling-20261027/ordinary-consumer-preparation-r5-source2/consumer.py').read_text();a=old.index('def capture_data_reviews(');b=old.index('\ndef capture_authority(',a)
control='''def control_evidence(files,descriptor,origin):
    require_current_source_profile()
    value=files.doc(descriptor)
    closed(value,'schema profileId authors operators producerSubject producerControls helperProbe consumerSource consumerControls')
    equal(value['schema'],'e02-minimum-controls-subject-v4');equal(value['profileId'],wire.PROFILE)
    equal(value['producerSubject'],CURRENT_PRODUCER)
    equal(value['producerControls'],dict(subject=CURRENT_PRODUCER_CONTROL_DATA,acceptance=CURRENT_PRODUCER_CONTROL_ACCEPTANCE))
    equal(value['helperProbe'],dict(subject=CURRENT_HELPER_PROBE_DATA,acceptance=CURRENT_HELPER_PROBE_ACCEPTANCE))
    origin.forbidden|=actors(value['authors'])|actors(value['operators'])|actors(CURRENT_CONTROL_ACTORS)
    # Close the new helper DATA actor union before producer/current DATA reviews.
    probe=files.doc(value['helperProbe']['subject'])
    origin.forbidden|=actors(probe['authors'])|actors(probe['operators'])
    from current_controls import validate_data
    validate_data(files,value['producerControls'],origin,CURRENT_PRODUCER,CURRENT_PRODUCER_SOURCE_ACCEPTANCE,
        CURRENT_CAPTURE_SOURCE,CURRENT_CAPTURE_SOURCE_ACCEPTANCE,CURRENT_ADMISSION_DATA_ACCEPTANCE,CURRENT_DATA_ACCEPTANCE_CONTRACT)
    files.read(value['helperProbe']['acceptance']);origin.reviews(value['helperProbe']['subject'],'HELPER_PROBE')
    for key in ('consumerSource','consumerControls'):files.read(value[key])
    origin.reviews(descriptor,'CONTROL')
    return value


'''
s=s[:start]+old[a:b]+'\n\n'+control+s[end:]
s=s.replace("equal(c['schema'], 'e02-minimum-fixture-call-v1')","equal(c['schema'], 'e02-minimum-fixture-call-v2')")
s=s.replace("need(len(argv) == 6 and argv[:2] == ['/usr/bin/docker', 'exec'] and\n             argv[3:] == ['/usr/local/bin/node', '/input/fixture.mjs', c['operation']], 'ACTUAL_FIXED_FIXTURE_COMMAND')", "need(len(argv)==8 and argv[:3]==['/usr/bin/docker','exec','--env'] and\n             argv[3]=='NBDP_CONTROLLER_AUDIT_SLOT='+str(ordinal) and\n             argv[5:]==['/usr/local/bin/node','/input/fixture.mjs',c['operation']],'ACTUAL_FIXED_ASSIGNED_SLOT_FIXTURE_COMMAND')")
s=s.replace("        equal(files.read(c['reply']), files.read(command_rows[seq - 1]['stdout']))", "        equal(c['reply'],command_rows[seq-1]['stdout'],'EXACT_SHARED_RPC_REPLY_PIN')\n        equal(files.read(c['reply']), files.read(command_rows[seq - 1]['stdout']))")
s=s.replace("closed(reply, 'schema profileId windowId operation caseId ok result')","closed(reply, 'schema profileId windowId operation caseId ok result guardController')").replace("'e02-minimum-fixture-command-v2'","'e02-minimum-fixture-command-v3'")
s=s.replace("any(same(s['runConfig'], p) for p in producer['configurations'])","any(same(s['runConfig'], p) for p in producer['configurations'].values())")
start=s.index("    expected_sources = [source_by_name[name] for name in (");end=s.index("    equal(config['sourceAndDependencyPins']",start);s=s[:start]+"    expected_sources = CURRENT_WORKERS\n"+s[end:]
s=s.replace("    calls = fixture_calls(files, driver, command_rows)", "    calls = fixture_calls(files, driver, command_rows)\n    from parent_allocation import validate_parent\n    helper_pin=next(p for p in CURRENT_WORKERS if Path(p['path']).name=='guard-helper.py')\n    controller_instances=validate_parent(files,s,command_rows,calls,helper_pin)\n    need(trace.guards.instance not in controller_instances,'DISTINCT_SERVE_AND_CONTROLLER_HELPER_INSTANCES')")
s=s.replace("nonoperativeMetadataFinding='PRODUCER3_CURRENT_REBUILT_ARTIFACT_SOURCE2_OLD_FINDING_PRESERVED'", "sourceProfile='PRODUCER4_SOURCE4_22_WORKERS_ASYNC_FRESH_GUARD' ")
s=s.replace('Standalone minimum ordinary-client evidence consumer','Current consumer6 minimum ordinary-client evidence consumer')
p.write_text(s)
# Remove only the obsolete nested A/B/model9 control block from generic data tests.
p=root/'test_data_controls.py';s=p.read_text();tree=ast.parse(s);lines=s.splitlines(keepends=True)
for c in tree.body:
 if isinstance(c,ast.ClassDef):
  for f in c.body:
   if isinstance(f,ast.FunctionDef) and f.name=='test_unknown_json_schema_cannot_claim_window':
    # Retain its narrow unknown-document refusal; obsolete A/B loops are separate history.
    replacement="    def test_unknown_json_schema_cannot_claim_window(self):\n        p = pin(self.root / 'unknown.json', strict.json_bytes({'schema':'unknown'}))\n        with self.assertRaises(strict.Refusal): consumer.consume(self.files,p,p)\n"
    lines[f.lineno-1:f.end_lineno]=[replacement]
p.write_text(''.join(lines))
