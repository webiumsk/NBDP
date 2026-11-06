"""One-shot SOURCE preparation. No project imports, tests, models or tools.

Copies the existing fourteen-file draft, pins genuine current DATA metadata,
and stages the capture SOURCE2 execution adapter. Actual authority contracts and
DATA remain NULL: this program cannot finalize or activate the consumer.
"""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

REPO = Path('/home/peterhorvath/apps/bitcoin/NBDP')
EVIDENCE = REPO / 'docs/decisions/evidence'
OUT = Path(__file__).resolve().parent
OLD = Path('/Data/nbdp-e02-tooling-20261027/ordinary-consumer-preparation-r5')
NEW = Path('/Data/nbdp-e02-tooling-20261027/ordinary-consumer-preparation-r5-source2')
PRODUCER_ROOT = EVIDENCE / 'e02-ordinary-minimum-producer-final-preparation-r3-20261028'
PRODUCER = PRODUCER_ROOT / 'source2/subject.json'
CAPTURE = EVIDENCE / 'e02-producer3-current-controls-preparation-20261028/source4'
CONTRACT = EVIDENCE / 'e02-producer3-data-contract-20261028/contract.json'
MODEL_CONTRACT = CONTRACT.parent/'model-subject-contract.json'
SUMMARY_TYPES = CONTRACT.parent/'summary-types.json'
ACTUAL9 = EVIDENCE/'e02-capture-admission9-actual-20261028-r2'
ACTUAL_CONTROLS = EVIDENCE/'e02-producer3-controls-actual-20261028-r2'
FREEZE = sys.argv[1:] == ['--freeze-accepted-source']
REFRESH = sys.argv[1:] in (['--refresh-draft'],['--freeze-accepted-source'])


def pin(path):
    path = Path(path); raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def doc(path): return json.loads(Path(path).read_bytes())


def save(name, value):
    path = OUT / name
    raw = value if type(value) is bytes else (json.dumps(value, indent=2) + '\n').encode()
    with path.open('wb' if REFRESH else 'xb') as stream: stream.write(raw)
    return pin(path)


def replace(text, before, after):
    if text.count(before) != 1: raise ValueError('EXACT_SOURCE_ANCHOR:' + before[:80])
    return text.replace(before, after)


def main():
    os.umask(0o077)
    if sys.argv[1:] not in ([], ['--refresh-draft'],['--freeze-accepted-source']): raise ValueError('CLOSED_SOURCE_PREPARATION_ARGUMENTS')
    if (OUT/'subject.json').exists() or (OUT/'source-packet.json').exists():raise ValueError('FROZEN_FINAL_SOURCE_ALREADY_EXISTS_NO_REFRESH')
    if REFRESH:
        previous=doc(OUT/'draft-pointer.json')
        if previous['finalSubjectCreated'] is not False or previous['sourceReadiness'] is not False:
            raise ValueError('ONLY_OWN_UNFROZEN_DRAFT_MAY_REFRESH')
        for d in previous['sourceFiles']:
            if pin(d['path'])!=d: raise ValueError('CONCURRENT_SOURCE_WRITER_OR_DRAFT_DRIFT')
    elif NEW.exists() or NEW.is_symlink(): raise ValueError('FRESH_SUCCESSOR_SOURCE_REQUIRED')
    preserved = [pin(p) for p in sorted(OLD.iterdir()) if p.is_file()]
    original_evidence = [pin(p) for p in sorted(OUT.parent.iterdir()) if p.is_file()]
    if len(preserved) != 14: raise ValueError('ORIGINAL_FOURTEEN_SOURCE_FILES_REQUIRED')
    expected = {'subject.json': '553d513b4625b8d40e95f475246acc2a4520e1a90b35ee88290c9ddbc617def6',
        'source-packet.json': 'bd2e2e330984fe739045f2259e38b66a64fe6074d222b6dcd1d8d244c9b3fe46',
        'control-plan.json': 'cf0351831f88dff7685bc53cd8977962526529b65bf13aeb740ef7c7ba0487d6',
        'source-input-manifest.json': 'c9c80039e0af9af4124c00bc87d42a94fcfa2dfa0e8216187b5404856e473ddc'}
    for name, sha in expected.items():
        if pin(PRODUCER.parent / name)['sha256'] != sha: raise ValueError('CURRENT_PRODUCER_PIN_DRIFT')
    producer = doc(PRODUCER)
    bindings = doc(producer['artifactBindings']['path'])
    configs = [doc(d['path']) for d in producer['configurations']]
    workers = configs[0]['sourceAndDependencyPins']
    if workers != configs[1]['sourceAndDependencyPins'] or len(workers) != 16: raise ValueError('CURRENT_WORKER_CONFIG_JOIN')
    for d in producer['sources'] + producer['configurations']:
        if pin(d['path']) != d: raise ValueError('CURRENT_SOURCE_OR_CONFIG_DRIFT')
    known = [pin(PRODUCER.parent / name) for name in expected]
    known += producer['configurations'] + producer['sources']
    known += [pin(PRODUCER.parent / name) for name in ('source-qa.json', 'source-security.json', 'source-acceptance.json')]
    known += [pin(CAPTURE / name) for name in ('capture-template.py', 'assemble-source-only.py', 'test_admission_models.py')]
    if pin(CONTRACT)['sha256']!='441165a0212a6e806c03790b61a3135451ab76477b6a685d234207b8a264a10d':raise ValueError('NORMATIVE_CONTRACT_DRIFT')
    if pin(MODEL_CONTRACT)['sha256']!='4ffaab275275a8782b5cc3a82a84087f5541f1c9b8b7b8e026f23a96caed6367':raise ValueError('NORMATIVE_MODEL_CONTRACT_DRIFT')
    if pin(CAPTURE/'subject.json')['sha256']!='de130703d0daecd16719fde5ed1a64e5109c4633f1254fc31a0c45001f1e2050':raise ValueError('CAPTURE4_SUBJECT_DRIFT')
    if pin(CAPTURE/'source-packet.json')['sha256']!='67f5f4fed2c55a130dcdc973273452c25451c834ae29c23be862511ee906d549':raise ValueError('CAPTURE4_PACKET_DRIFT')
    if pin(SUMMARY_TYPES)['sha256']!='f093a5ad1383a28e98f389e6adfc579746145f6194314204653412f3c5b1611d':raise ValueError('SUMMARY_TYPE_CONTRACT_DRIFT')
    known += [pin(CONTRACT),pin(MODEL_CONTRACT),pin(CAPTURE/'subject.json'),pin(CAPTURE/'source-packet.json'),pin(CAPTURE/'admission9-method.json')]
    known += [pin(SUMMARY_TYPES),pin(CAPTURE/'negative-invocation-disposition.json'),pin(CAPTURE/'request-from-plan.py')]
    historical_source3_checkpoint=pin(OUT/'checkpoint-source3-unqualified-bindings/copies.json')
    actual_actor_union={'/root','/root/r5_plan_fix','/root/producer3_capture','/root/r5'}
    if pin(ACTUAL9/'acceptance.json')['sha256']!='d090ebc9a4df08172c08782e16171bcf6fccd116e7ec94530e2c5f228c7eb807':raise ValueError('FRESH_SOURCE4_MODEL9_ACCEPTANCE_DRIFT')
    model_acceptance=doc(ACTUAL9/'acceptance.json')
    if model_acceptance['captureSource']!=pin(CAPTURE/'subject.json'):raise ValueError('NO_OLD_SOURCE3_MODEL9_TRANSFER')
    model_subject=doc(model_acceptance['subject']['path'])
    actual_actor_union.update(model_subject['authors']);actual_actor_union.update(model_subject['operators'])
    for path in sorted(ACTUAL9.iterdir()):
        if path.is_file():known.append(pin(path))
    actual_subjects={}
    actual_sha={'capture-a':'5ec2f6bf547f38413fbeef2db0253e7d82eb3efeb5c25e5184fd6076f74175d4',
        'capture-b':'23bcf2cc249f6b5909895dd5f3c0edda335d04266aae64e3994d170784bcf9ee'}
    for mode in ('capture-a','capture-b'):
        path=ACTUAL_CONTROLS/mode/'subject.json'
        if pin(path)['sha256']!=actual_sha[mode]:raise ValueError('FRESH_SOURCE4_A_B_SUBJECT_DRIFT')
        actual=doc(path);actual_subjects[mode]=actual
        if actual['captureSource']!=pin(CAPTURE/'subject.json'):raise ValueError('NO_OLD_SOURCE3_CONTROL_TRANSFER')
        actual_actor_union.update(actual['authors']);actual_actor_union.update(actual['operators'])
        known.append(pin(path))
        for key in ('rootAcknowledgement','originalToolOrigin','execution','rawArtifactManifest','overallSourcesBefore','overallSourcesAfter'):
            known.append(actual[key])
    for capture in doc(CAPTURE/'subject.json')['captures'].values():
        for d in capture.values():
            if pin(d['path'])!=d:raise ValueError('CAPTURE4_LEAF_DRIFT')
            known.append(d)
    if not REFRESH: NEW.mkdir(mode=0o700)
    for d in preserved: shutil.copyfile(d['path'], NEW / Path(d['path']).name)
    source = (NEW / 'consumer.py').read_text()
    start = source.index('PRODUCER_SHA = '); end = source.index('CONFIG_KEYS = ', start)
    source_plan = doc(PRODUCER.parent / 'control-plan.json')
    node_map = {}
    node_keys = 'producerSource testSource inputClosure plan release capture originalToolResponses result acceptance qaReview securityReview admissionModelAcceptance upstreamRootACK'.split()
    for mode, scopes in [('capture-a', source_plan['scopes'][:3]), ('capture-b', source_plan['scopes'][3:])]:
        node_map[mode] = {key: None for key in node_keys}
        node_map[mode]['producerSource'] = pin(PRODUCER)
        node_map[mode]['testSource'] = [s['source'] for s in scopes]
        for key,name in [('inputClosure','frozen-inputs.json'),('plan','control-plan.json')]:
            if (CAPTURE/mode/name).is_file(): node_map[mode][key]=pin(CAPTURE/mode/name)
        if (CAPTURE/'subject.json').is_file(): node_map[mode]['capture']=pin(CAPTURE/'subject.json')
        actual=actual_subjects[mode]
        node_map[mode]['result']=pin(ACTUAL_CONTROLS/mode/'subject.json')
        node_map[mode]['release']=actual['rootAcknowledgement']
        node_map[mode]['originalToolResponses']=actual['originalToolOrigin']
        node_map[mode]['admissionModelAcceptance']=actual['admissionModelAcceptance']
        node_map[mode]['upstreamRootACK']=model_subject['rootAcknowledgement']
        if FREEZE:
            expected={
                'capture-a':{'acceptance.json':'6116b898c7d99aa92b21f1347959d7a0b688b866db95155e98238e6994d3bfc9',
                    'data-qa.json':'562153064fc74e449c392756a3da39c5bc6867a8923200c414a07c427330a064',
                    'data-security.json':'565eab1dad09bda57aa29b779a522f6b6582e84e7583ad62b6cc564be8e75ae8'},
                'capture-b':{'acceptance.json':'4b8319c8764e07a2b715dbefb3068f09faa2371838b8f98055f994d916e6a5bb',
                    'data-qa.json':'7c2640b2600f506dfb4583b4e938012127d96f10a17ee072df7eb12e4168d769',
                    'data-security.json':'36a7a76b794c9b54e7317380b22c87a397e98c1fc4fe2ef37f3373e1aad056cd'}}[mode]
            for name,sha in expected.items():
                d=pin(ACTUAL_CONTROLS/mode/name)
                if d['sha256']!=sha:raise ValueError('ACTUAL_A_B_ACCEPTANCE_OR_REVIEW_DRIFT')
                known.append(d)
            node_map[mode]['acceptance']=pin(ACTUAL_CONTROLS/mode/'acceptance.json')
            node_map[mode]['qaReview']=pin(ACTUAL_CONTROLS/mode/'data-qa.json')
            node_map[mode]['securityReview']=pin(ACTUAL_CONTROLS/mode/'data-security.json')
            acceptance=doc(node_map[mode]['acceptance']['path'])
            if acceptance['subject']!=node_map[mode]['result'] or acceptance['reviews']!=[node_map[mode]['qaReview'],node_map[mode]['securityReview']]:raise ValueError('CURRENT_ACCEPTED_DATA_GRAPH_REQUIRED')
        # The actual SOURCE4 A/B QA/security and acceptance nodes stay NULL
        # until root explicitly issues the independently reviewed DATA pins.
    values = dict(PRODUCER_SHA=pin(PRODUCER)['sha256'], CONTRACT_SHA=producer['typedContract']['sha256'],
        ADOPTION_SHA='2675f6906c3ab234f4d460960f4cc950eb8847b051b3e0d8cedaebdf38a75287',
        RUNTIME_SCOPE='E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY',
        DRAFT_FINAL_ADAPTER_READY=FREEZE, CURRENT_PRODUCER_SCHEMA=producer['schema'],
        CURRENT_PRODUCER=pin(PRODUCER), CURRENT_SOURCE_PACKET=pin(PRODUCER.parent / 'source-packet.json'),
        CURRENT_SOURCE_PLAN=pin(PRODUCER.parent / 'control-plan.json'),
        CURRENT_SOURCE_INPUTS=pin(PRODUCER.parent / 'source-input-manifest.json'),
        CURRENT_AMETHYST_APK=bindings['amethystApk'], CURRENT_HELPER_APK=bindings['helperApk'],
        CURRENT_ARTIFACT_BINDINGS=producer['artifactBindings'], CURRENT_CONFIGURATIONS=producer['configurations'],
        CURRENT_WORKERS=workers, CURRENT_CAPTURE_BINDINGS=node_map,
        CURRENT_AUTHORITY_CONTRACT=pin(CONTRACT), CURRENT_CONTROL_ACTORS=sorted(actual_actor_union),
        CURRENT_ADMISSION_MODEL_CONTRACT=pin(MODEL_CONTRACT),
        CURRENT_SUMMARY_TYPES=pin(SUMMARY_TYPES),
        CURRENT_SOURCE_CAPTURE_DECISIONS={'source':{'qa':'ACCEPT_PRODUCER3_SOURCE_FOR_FRESH35_AND_SEPARATE3_CONTROLS_ONLY',
            'security':'ACCEPT_FINAL_PRODUCER3_SOURCE_AND_CONTROL_DEFINITIONS_ONLY'},
            'capture':{'qa':'ACCEPT_PRODUCER3_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY',
            'security':'ACCEPT_PRODUCER3_CAPTURE_SOURCE_FOR_FIXED_DATA_CONTROLS_ONLY'}},
        CURRENT_EXPERIMENT_REPOSITORY=str(REPO),
        CURRENT_READ_TREE_ROOTS=[('/tmp/nbdp-e02-api35-fixture-r2/sdk',434),('/tmp/nbdp-e02-minimal-rs-v7/guard-python',522)])
    source = source[:start] + ''.join(name + ' = ' + repr(value) + '\n' for name,value in values.items()) + '\n' + source[end:]
    start = source.index('def require_current_source_profile():'); end = source.index('\n\ndef external(', start)
    source = source[:start] + '''def require_current_source_profile():
    """Known source pins alone never activate pending actual control authority."""
    need(DRAFT_FINAL_ADAPTER_READY is True, 'CONSUMER5_SOURCE2_NULL_NOT_READY_REQUIRES_CURRENT_DATA')
    need(CURRENT_AUTHORITY_CONTRACT is not None and CURRENT_CONTROL_ACTORS is not None
         and CURRENT_ADMISSION_MODEL_CONTRACT is not None, 'CURRENT_API_ACCEPTANCE_ACTORS_AND_CONTRACT_REQUIRED')
    need(all(value is not None for nodes in CURRENT_CAPTURE_BINDINGS.values() for value in nodes.values()),
         'ALL_A_B_CAPTURE_SOURCE_INPUT_PLAN_ROOT_RELEASE_TOOL_RESULT_INDEPENDENT_ACCEPTANCE_REQUIRED')
''' + source[end:]
    fragment = (OUT / 'capture-verifier-fragment.py').read_text()
    fragment = fragment[fragment.index('def current_producer('):]
    start = source.index('def control_evidence('); end = source.index('\n\ndef graph(',start)
    source = source[:start] + fragment.rstrip() + source[end:]
    source = replace(source, "    producer = files.doc(candidate['producerSubject'])\n    equal(producer['schema'], CURRENT_PRODUCER_SCHEMA)\n    for p in producer['sources']: files.read(p)", "    producer = current_producer(files, candidate['producerSubject'])")
    source = replace(source, "    forbidden |= actors(controls['authors']) | actors(controls['operators'])", "    forbidden |= actors(controls['authors']) | actors(controls['operators'])\n    forbidden |= actors(CURRENT_CONTROL_ACTORS)")
    source = replace(source, "PRODUCER2_PUBLIC_SCALAR_METADATA_CORRECTED_OLD_FINDING_PRESERVED", "PRODUCER3_CURRENT_REBUILT_ARTIFACT_SOURCE2_OLD_FINDING_PRESERVED")
    (NEW/'consumer.py').write_text(source)
    path=NEW/'test_data_controls.py'; text=path.read_text()
    text=replace(text, "        with self.assertRaises(strict.Refusal): consumer.consume(self.files, p, p)\n\n    def test_actor_union_and_same_session_review_refused", """        with self.assertRaises(strict.Refusal): consumer.consume(self.files, p, p)
        # SOURCE2 subcases remain inside the original86-method scope. Synthetic
        # quiet streams are parser inputs, never actual tool/control receipts.
        for index, (count, dots, output_count, suffix, good) in enumerate([
            (3, 3, 3, b'OK\\n', True), (8, 8, 8, b'OK\\n', True), (7, 7, 7, b'OK\\n', True),
            (3, 2, 3, b'OK\\n', False), (3, 3, 7, b'OK\\n', False),
            (3, 3, 3, b'OK (skipped=1)\\n', False), (3, 3, 3, b'FAILED (failures=1)\\n', False)]):
            with self.subTest(captureQuietParser=index):
                stdout = pin(self.root / ('capture-%d.stdout' % index), b'')
                raw = b'.' * dots + b'\\n' + b'-' * 70 + b'\\nRan ' + str(output_count).encode() + b' tests in 0.001s\\n\\n' + suffix
                stderr = pin(self.root / ('capture-%d.stderr' % index), raw)
                name = {3:'rebuilt-artifact-bindings', 8:'public-identity-metadata', 7:'producer2-source-wiring'}[count]
                scope = dict(name=name, count=count)
                receipt = dict(stdout=stdout, stderr=stderr, observedStreamBytes=dict(stdout=0, stderr=len(raw)),
                    truncated=dict(stdout=False, stderr=False), observedPartitions={name:count})
                if good: consumer.capture_output(self.files, scope, receipt)
                else:
                    with self.assertRaises(strict.Refusal): consumer.capture_output(self.files, scope, receipt)

    def test_actor_union_and_same_session_review_refused""")
    text=replace(text, '    def test_actor_union_and_same_session_review_refused',
        (OUT/'custody-subtests-fragment.txt').read_text()+'\n\n    def test_actor_union_and_same_session_review_refused')
    review_subtests='''        # The new closed four-key DATA review helper uses synthetic DATA only.
        from types import SimpleNamespace
        decision='ACCEPT_CURRENT_PRODUCER3_REBUILT_BINDINGS3_DATA_ONLY'
        target=pin(self.root/'SYNTHETIC-review-target',b'SYNTHETIC_NOT_ACTUAL_CAPTURE')
        for index,(qa_actor,sec_actor,change,good) in enumerate([
            ('/root/SYNTHETIC_QA','/root/SYNTHETIC_SEC',None,True),
            ('/root/operator','/root/SYNTHETIC_SEC',None,False),
            ('/root/SYNTHETIC_QA','/root/SYNTHETIC_QA',None,False),
            ('/root/SYNTHETIC_QA','/root/SYNTHETIC_SEC','HOLD',False)]):
            with self.subTest(SYNTHETIC_current_capture_reviews=index):
                documents=[dict(role=role,session=session,decision=change or decision,subject=target)
                    for role,session in [('qa',qa_actor),('security',sec_actor)]]
                pins=[pin(self.root/('SYNTHETIC-review-%d-%d.json'%(index,i)),strict.json_bytes(value))
                    for i,value in enumerate(documents)]
                if good:consumer.capture_data_reviews(self.files,pins,target,decision,SimpleNamespace(forbidden={'/root/operator'}))
                else:
                    with self.assertRaises(strict.Refusal):consumer.capture_data_reviews(self.files,pins,target,decision,SimpleNamespace(forbidden={'/root/operator'}))

'''
    text=replace(text, '    def test_missing_entire_history_witness_refused', review_subtests+'    def test_missing_entire_history_witness_refused')
    path.write_text(text)
    path=NEW/'test_source_bindings.py'; text=path.read_text()
    text=replace(text, 'PRODUCER = None  # Actual final producer3 subject path is not available.', 'PRODUCER = Path(' + repr(str(PRODUCER)) + ')')
    text=replace(text, "            self.assertEqual(config['schema'], 'e02-ordinary-minimum-role-runtime-plan-v2')", "            self.assertEqual(config['schema'], 'e02-ordinary-minimum-role-runtime-plan-v2')\n            self.assertEqual(config['amethystApk'], consumer.CURRENT_AMETHYST_APK)\n            self.assertEqual(config['helperApk'], consumer.CURRENT_HELPER_APK)\n            self.assertEqual(config['sourceAndDependencyPins'], consumer.CURRENT_WORKERS)")
    text=replace(text, "        self.assertIn('e02-minimum-fixture-command-v2', consumer_source)", "        self.assertIn('e02-minimum-fixture-command-v2', consumer_source)\n        self.assertEqual(self.frozen_producer()['schema'], consumer.CURRENT_PRODUCER_SCHEMA)\n        self.assertEqual(consumer.CURRENT_SOURCE_PLAN, self.frozen_producer()['controlPlan'])\n        self.assertEqual(consumer.CURRENT_SOURCE_INPUTS, self.frozen_producer()['sourceDataInputClosure'])\n        expected = [('capture-a', [20,8,7]), ('capture-b', [3])]\n        for mode, counts in expected:\n            with self.subTest(mode=mode):\n                nodes = consumer.CURRENT_CAPTURE_BINDINGS[mode]\n                self.assertEqual(nodes['producerSource'], consumer.CURRENT_PRODUCER)\n                self.assertEqual(len(nodes['testSource']), len(counts))\n                self.assertEqual(len(nodes), 13)\n                self.assertIn('admissionModelAcceptance', nodes)\n                self.assertIn('upstreamRootACK', nodes)")
    path.write_text(text)
    path=NEW/'test_whole_window.py'; text=path.read_text().replace(str(OLD),str(NEW))
    text=replace(text, "        cls.producer = None  # Actual immutable producer3 snapshot path required.\n        if cls.producer is None: raise ValueError('CONSUMER5_FINAL_WHOLE_WINDOW_PRODUCER_REQUIRED')", "        cls.producer = Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')")
    path.write_text(text)
    path=NEW/'whole_window.py'; text=path.read_text()
    text=replace(text, "        cfg_path = self.producer_dir.parents[2] / 'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2' / ('proposed-' + self.role + '-run-config.json')", "        cfg_path = Path("+repr(str(PRODUCER_ROOT))+ ") / (self.role + '-run-config.json')")
    path.write_text(text)
    (NEW/'README.md').write_text('''# Consumer5 SOURCE2 staged preparation

Current producer3 SOURCE2, accepted APK368255/helper589031, both immutable role
configs and sixteen workers are bound. The capture-a20/8/7 and capture-b3 literal
SOURCE4 execution/schema/child-output/closure verifier is staged. Real SOURCE4
A/B subjects/ACK/API and fresh accepted9 are bound. DATAacceptance/QA/security
nodes per group remain NULL, and the entry gate remains false. SOURCE3
target assertions passed but A/B method qualification is HOLD: actual parent
TZ/TERM mutation had no exact pre-execution override. All old DATA/checkpoints
are preserved, no positive A/B acceptance exists, and no old9/ACK carry occurs.
Root summary-type clarification f093 treats three fields as bounded descriptive
strings; actual facts remain receipt/graph predicates. Exact KILL297/noTZ
request binding is unchanged and observed parent mutations are negative
subcases inside the existing86-method definitions (zero executed).
The exact
root-adopted441165/4ffaab authority schemas and frozen captureSOURCE3 joins are
implemented without fabricating records. Both control groups require current
admission9 acceptance and its actual upstream root ACK plus independent DATA
reviews excluding declared source/DATA authors and operators.
No final subject, readiness, model execution, runtime or grant is created.

Both genuine API forms (direct terminal or genuine same-session launch+all
polls) must be rendered from actual records. Child EOF/reap is exclusively from
the child journals. Source preparation never manufactures receipts or review
decisions. Scope86/36/8/9 definitions, ordinary1800, original10s/3s/55s,
unknown-query cause, UI/wire/replay/lease/cleanup/oracles remain unchanged.
The whole-window builder remains synthetic and is not a complete consume test.
''')
    if FREEZE:
        (NEW/'README.md').write_text('''# Consumer5 current SOURCE

Current producer3 SOURCE2, accepted rebuilt artifacts, both configs/16workers,
capture SOURCE4 and independently accepted fresh9/A20-8-7/B3 are source-bound.
The exact bounded DATA adapter is implemented. Code readiness is not execution
authority: independent SOURCE QA/security and a separately reviewed/released
finite capture precede86/36/8/9 DATA controls. No ordinary window/client/primary
qualification or canonical promotion follows. Full consume requires genuine
whole history/windows and external origins; window fixtures stay synthetic.

Three descriptive strings are metadata only. Exact current requests, closed
schemas/decisions, raw output/counts/EOF/reap/source/membership/retention/actor
joins remain enforced. Original SOURCE3 invocation HOLD/negative DATA and all
earlier checkpoints remain preserved. No old ACK/9/result qualification carry.
Original10s/3s/55s/1800, unknown query cause, wire/UI/private-tag/replay/lease/
cleanup/oracles and strict numeric/file bounds are unchanged. Separate bounded
metadata decoders preserve actual API/model duration decimals without changing
protocol parsing. No producer/SDK/native/service/tool execution is performed.
''')
        path=NEW/'CONTRACT.md';body=path.read_text();body=body.split('\n\n',1)[1]
        path.write_text('''CURRENT CONSUMER5 SOURCE: current code and source packet bind producer3,
captureSOURCE4 and actual accepted fresh9/A35/B3. Control subject v3 has separate
producerCaptureA/producerCaptureB thirteen-node DAGs; runtime flags remainfalse.
Candidate producerContract still means EXPORT7fd7; typed control DATA uses
packetbd2e. Baseline criterion text below is retained; superseded SOURCE/hash/
control-DTO references are historical and do not override current code/packet.
No criterion, wire/UI grammar, lease, cleanup or ordinary qualification change.

'''+body)
    files=sorted(p for p in NEW.iterdir() if p.is_file())
    if len(files)!=14: raise ValueError('EXACT14SOURCECLOSURE')
    definitions=[]
    for name,count in [('test_data_controls.py',86),('test_observer.py',36),('test_source_bindings.py',8),('test_whole_window.py',9)]:
        tree=ast.parse((NEW/name).read_text()); names=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
        if len(names)!=count: raise ValueError('CONTROL_DEFINITION_SCOPE_CHANGED')
        definitions.append(dict(source=pin(NEW/name),count=count,exactDefinedNames=names))
    for p in files:
        if p.suffix=='.py': ast.parse(p.read_text())
    # No runtime/evaluator admission guard may change with source path/bindings.
    for name in ('gui.py','observer.py','strict.py','wire.py','witness.py','test_observer.py'):
        if (OLD/name).read_bytes()!=(NEW/name).read_bytes():raise ValueError('PROTECTED_SOURCE_BYTE_DRIFT:'+name)
    for d in preserved+original_evidence:
        if pin(d['path'])!=d: raise ValueError('ORIGINAL_DRAFT_CHANGED')
    preservation=save('preserved-original-draft.json',dict(schema='e02-consumer5-source2-preserved-draft-v1',sourceFiles=preserved,evidenceFiles=original_evidence,allUnchanged=True))
    copies=[]
    (OUT/'source-archive').mkdir(mode=0o700,exist_ok=REFRESH)
    for p in files:
        shutil.copyfile(p,OUT/'source-archive'/p.name)
        copies.append(dict(original=pin(p),copy=pin(OUT/'source-archive'/p.name)))
    diffs=''.join(''.join(difflib.unified_diff((OLD/p.name).read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(OLD/p.name),tofile=str(p))) for p in files)
    diff=save('staged-source.diff',diffs.encode())
    dag=save('input-dag.json',dict(schema='e02-consumer5-source2-pending-dag-v1',knownInputs=known,
        producer=pin(PRODUCER),sourcePacket=pin(PRODUCER.parent/'source-packet.json'),sourcePlan=pin(PRODUCER.parent/'control-plan.json'),
        sourceInputManifest=pin(PRODUCER.parent/'source-input-manifest.json'),configurations=producer['configurations'],workers=workers,
        captures=node_map,currentAuthorityContract=pin(CONTRACT),currentControlActors=sorted(actual_actor_union),
        currentAdmissionModelContract=pin(MODEL_CONTRACT),
        source3History=historical_source3_checkpoint,source3DataQualification='HOLD_EXACT_INVOCATION_BINDING_NO_POSITIVE_ACCEPTANCE_OR_TRANSFER',
        currentSummaryTypes=pin(SUMMARY_TYPES),
        freshSource4Model9Acceptance=pin(ACTUAL9/'acceptance.json'),
        rawApi='IMPLEMENTED_EXACT_CONTRACT_DIRECT_TERMINAL_OR_GENUINE_SAME_SESSION_ALL_POLLS_ACTUAL_RECORDS_PENDING',
        provenance='Externally authenticated coordinator origin; pinned DATA is not portable attestation.',
        noHistoricalControlTransfer=True,sourceReadiness=False,actualExecutions=0))
    plan=save('control-definitions.json',dict(schema='e02-consumer5-source2-control-definitions-v1',scopes=definitions,modelsExecuted=0,
        releaseRequired=True,blocked='Pending actual current A/B graphs and exact authority adapter, final SOURCE/independent reviews, finite control capture/root release.',
        wholeWindow='Synthetic complete window models; complete top-level consume remains distinct.'))
    pointer=save('draft-pointer.json',dict(schema='e02-consumer5-source2-draft-pointer-v1',state='UNFROZEN_STAGED_SOURCE_PENDING_CURRENT_DATA_AND_AUTHORITY_RENDER',
        sourceRoot=str(NEW),sourceFiles=[pin(p) for p in files],sourceCount=14,durableCopies=copies,
        preservation=preservation,inputDag=dag,controlDefinitions=plan,diff=diff,preparationScript=pin(__file__),
        captureVerifierFragment=pin(OUT/'capture-verifier-fragment.py'),sourceReadiness=False,finalSubjectCreated=False,
        custodySubtestFragment=pin(OUT/'custody-subtests-fragment.txt'),
        modelsExecuted=0,actualControlsExecuted=0,runtimeCreated=False,grantCreated=False,
        unresolved=['Independent current SOURCE4 A/B DATA acceptance/QA/security pins required; remain NULL pending root issuance',
            'Final current14-source packet and independent SOURCE review; no SOURCE3 DATA/ACK/model transfer',
            'Fresh full SOURCE review and86/36/8/9DATA after separate finite root release']))
    if FREEZE:
        scopes=[]
        python=source_plan['python']
        for row in definitions:
            tree=ast.parse(Path(row['source']['path']).read_text())
            names=[cls.name+'.'+method.name for cls in tree.body if isinstance(cls,ast.ClassDef)
                for method in cls.body if isinstance(method,ast.FunctionDef) and method.name.startswith('test_')]
            if len(names)!=row['count']:raise ValueError('EXACT_NAMED_CLASS_METHOD_MEMBERSHIP')
            scopes.append(dict(name=Path(row['source']['path']).name,source=row['source'],count=row['count'],
                exactDefinedNames=names,argv=[python['path'],'-I','-B',row['source']['path']],cwd=str(NEW),
                format='VERBOSE_UNITTEST_EXACT_SOURCE_MEMBERSHIP_AND_COUNT_NO_SKIPS_STDOUT_EMPTY'))
        capture_path='/Data/nbdp-e02-tooling-20261027/consumer5-control-capture-preparation-r1/capture.py'
        outer_argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
            '/usr/bin/timeout','--signal=KILL','297',python['path'],'-I','-B',capture_path,
            '--execute-once','--root-ack-sha','__ACTUAL_ROOT_ACK_SHA256__']
        control_plan=save('control-plan.json',dict(schema='e02-consumer5-current-pure-control-plan-v1',
            state='FROZEN_SOURCE_DEFINITIONS_ONLY_NO_EXECUTION_AUTHORITY',sourceRoot=str(NEW),interpreter=python,
            scopes=scopes,limits=dict(commandSeconds=60,absoluteOwnedReapSeconds=3,
                stdoutRetainedBytes=1048576,stderrRetainedBytes=262144,outerSeconds=297),
            stopFirstFailure=True,noRetry=True,retentionMeaning='POST_CAPTURE_REFUSAL_NOT_STREAMING_MEMORY_CAP',
            outerArgvTemplate=outer_argv,outerRequestTemplate=dict(cmd=' '.join(outer_argv),workdir=str(REPO),
                login=False,yield_time_ms=1000,max_output_tokens=10000),
            externalCaptureSource=None,externalCaptureSourceReviews=None,externalRootGrant=None,actualExecutions=0))
        unique={d['path']:d for d in known+[pin(p) for p in files]+[python]}
        input_manifest=save('source-input-manifest.json',dict(schema='e02-consumer5-source-and-current-data-input-manifest-v1',
            scope='Explicit consumer source/current DATA authority and test operand seeds; finite capture must close actual test read operands before release.',
            files=[unique[k] for k in sorted(unique)],actualDeclaredFiles=len(unique),
            allSourceFiles=[pin(p) for p in files],sourceCount=14,producerSource=pin(PRODUCER),
            captureSource=pin(CAPTURE/'subject.json'),acceptedCurrentCaptureGraphs=node_map,
            opaqueProofSnapshots='SDK/APK and other snapshot-internal descriptors remain DATA proof references; this consumer manifest is not a claim to rehash every snapshot body.',
            captureClosureRequirement='Actual capture adds frozen source subject/packet/plan/self/ACK/reviews and exact test read operands; no assumed old64/1889 input count.',
            actualExecutions=0))
        subject=save('subject.json',dict(schema='e02-ordinary-minimum-consumer5-source-subject-v1',author='/root/r5_plan_fix',coordinator='/root',
            state='WRITES_STOPPED_PENDING_INDEPENDENT_SOURCE_QA_SECURITY',scope='SOURCE_COMPLETE_DATA_VERIFIER_AND_MODEL_DEFINITIONS_NO_EXECUTION_AUTHORITY',
            profileId=producer['profileId'],sourceRoot=str(NEW),sources=[pin(p) for p in files],sourceCount=14,
            producerSubject=pin(PRODUCER),producerContract=producer['typedContract'],producerSourcePacket=pin(PRODUCER.parent/'source-packet.json'),
            captureSource=pin(CAPTURE/'subject.json'),currentCaptureGraphs=node_map,controlPlan=control_plan,sourceInputManifest=input_manifest,
            actualControlDefinitions=[86,36,8,9],actualControlsExecuted=0,wholeWindowMeaning='Synthetic whole window fixtures; complete consume/candidate/history/origin/runtime remains separate.',
            sourceReadiness='REQUIRES_INDEPENDENT_SOURCE_AND_FINITE_CAPTURE_REVIEW_AND_ROOT_RELEASE',runtimeAuthorized=False,
            ordinaryRowsQualified=0,canonicalE02='PARTIAL22_UNCHANGED',historicalSource3Transfer=False))
        packet=save('source-packet.json',dict(schema='e02-consumer5-current-source-packet-v1',subject=subject,sourceRoot=str(NEW),
            sources=[pin(p) for p in files],sourceCount=14,durableCopies=copies,producerSource=pin(PRODUCER),
            currentSource4=pin(CAPTURE/'subject.json'),currentAcceptedCaptureGraphs=node_map,
            controlPlan=control_plan,sourceInputManifest=input_manifest,definedControls=plan,
            preservation=preservation,source3History=historical_source3_checkpoint,diff=diff,
            preparationScript=pin(__file__),captureVerifierFragment=pin(OUT/'capture-verifier-fragment.py'),
            custodySubtestFragment=pin(OUT/'custody-subtests-fragment.txt'),modelsExecuted=0,
            runtimeAuthorized=False,ordinaryRowsQualified=0,authorApprovesOwnFindings=False))
        pointer=save('current-source-entrypoint.json',dict(schema='e02-consumer5-current-source-entrypoint-v1',
            state='FROZEN_SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW',subject=subject,packet=packet,
            sourceInputManifest=input_manifest,controlPlan=control_plan,sourceCount=14,definedControls=[86,36,8,9],
            actualControlsExecuted=0,runtimeAuthorized=False,finalSourceFrozen=True))
    print(json.dumps(dict(entrypoint=pointer,sourceRoot=str(NEW),definedScopes=[86,36,8,9],modelsExecuted=0,finalSubjectCreated=FREEZE)))


if __name__=='__main__':main()
