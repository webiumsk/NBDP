"""SOURCE/DATA adaptation only; no capture import or child execution."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
HERE=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1/current-controls-r1'
E=HERE.parent
OLD=ROOT/'docs/decisions/evidence/e02-ordinary-api35-preparation-r3/current-controls-r1/capture-controls.py'
p=HERE/'capture-controls.py'
text=OLD.read_text()
text=text.replace('Finite once-only two-scope control capture','Finite once-only five-scope control capture')
a=text.index("S = ROOT /");b=text.index('\n\ndef utc()',a)
text=text[:a]+'''S = ROOT / 'experiments/prototypes/e02_ordinary_minimum_v1'
PYTHON = Path('/home/peterhorvath/.miniforge3/bin/python3.13')
NODE = Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
ACTOR = '/root/ordinary_api35_source'
TIMEOUT_SECONDS = 60
CAPTURE_LIMIT_BYTES = 1024 * 1024
SUBJECT_SHA = '296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4'
FROZEN_PLAN_SHA = 'dce8eab9bd5436a933d9661b74fb30b1b7dceff64339a22168f378a3d0a2bee2'
SCOPES = [
    ('cleanup', 29, [str(PYTHON), '-I', '-B', str(S / 'test_cleanup.py')]),
    ('ui-regression', 49, [str(PYTHON), '-I', '-B', str(S / 'test_android_driver.py')]),
    ('minimum-ui', 21, [str(PYTHON), '-I', '-B', str(S / 'test_minimum_driver.py')]),
    ('fixture-regression', 27, [str(NODE), str(S / 'test_fixture.mjs')]),
    ('minimum-fixture', 43, [str(NODE), str(S / 'test_minimum_fixture.mjs')]),
]
'''+text[b:]
a=text.index('def snapshot():');b=text.index('\n\ndef one(',a)
text=text[:a]+'''def descriptor_closure(value, out=None):
    if out is None:
        out = {}
    if type(value) is dict:
        if set(value) == {'path', 'bytes', 'sha256'}:
            prior = out.get(value['path'])
            assert prior is None or prior == value, 'Conflicting frozen descriptor'
            out[value['path']] = value
        else:
            for item in value.values():
                descriptor_closure(item, out)
    elif type(value) is list:
        for item in value:
            descriptor_closure(item, out)
    return out


def snapshot():
    subject = json.loads((E / 'subject.json').read_text())
    descriptor = pin(E / 'subject.json')
    assert descriptor['sha256'] == SUBJECT_SHA
    closure = descriptor_closure(subject)
    assert len(closure) == 112, 'Whole original frozen subject closure required'
    actual = [pin(Path(path)) for path in sorted(closure)]
    assert all(row == closure[row['path']] for row in actual), 'Frozen SOURCE/DATA changed'
    frozen_plan_pin = pin(E / 'execution-control-plan.json')
    assert frozen_plan_pin['sha256'] == FROZEN_PLAN_SHA
    frozen_plan = json.loads((E / 'execution-control-plan.json').read_text())
    assert [(r['name'], r['plannedChecks'], r['argv']) for r in frozen_plan['separateScopes']] == SCOPES
    assert all(r['timeoutSeconds'] == TIMEOUT_SECONDS for r in frozen_plan['separateScopes'])
    interpreters = {k: pin(Path(d['path'])) for k, d in frozen_plan['interpreters'].items()}
    assert interpreters == frozen_plan['interpreters']
    data = json.loads((E / 'control-inputs.json').read_text())
    inputs = data['oldTenArchivedUiData'] + data['newFrozenFeedsData']
    assert len(inputs) == 14 and all(pin(Path(d['path'])) == d for d in inputs)
    acknowledgement = json.loads((HERE / 'coordinator-acknowledgement.json').read_text())
    assert acknowledgement['sourceSubjectSha256'] == SUBJECT_SHA
    assert acknowledgement['actor'] == '/root' and acknowledgement['pureControlsAuthorized'] is True
    assert acknowledgement['actualSourceQaAccepted'] is True and acknowledgement['actualSourceSecurityAccepted'] is True
    assert acknowledgement['runner'] == pin(Path(__file__).resolve())
    assert acknowledgement['controlPlan'] == pin(HERE / 'control-plan.json')
    review_pins = [acknowledgement['sourceQaReview'], acknowledgement['sourceSecurityReview']]
    assert all(pin(Path(d['path'])) == d for d in review_pins)
    return {'subject': descriptor, 'all112FrozenDescriptors': actual,
            'configurations': subject['configurations'], 'interpreters': interpreters,
            'archivedReadOnlyControlData': inputs,
            'captureRunner': pin(Path(__file__).resolve()),
            'controlPlan': pin(HERE / 'control-plan.json'), 'frozenControlPlan': frozen_plan_pin,
            'sourceReviewRecords': review_pins,
            'coordinatorAcknowledgement': pin(HERE / 'coordinator-acknowledgement.json')}


def output_shape(name, expected, stdout, stderr):
    if name in ('cleanup', 'ui-regression', 'minimum-ui'):
        match = re.search(rb'\\nRan ([0-9]+) tests? in [^\\n]+\\n\\nOK\\n\\Z', stderr)
        count = int(match[1]) if match else None
        return count, count == expected and stdout == b''
    assert stderr == b'', 'Pure Node controls require empty stderr'
    assert stdout.endswith(b'\\n') and stdout.count(b'\\n') == 1, 'One actual JSON output line required'
    def pairs(items):
        out = {}
        for key, value in items:
            assert key not in out, 'Duplicate output JSON key'
            out[key] = value
        return out
    value = json.loads(stdout, object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite output')))
    assert type(value) is dict and type(value['checks']) is int
    if name == 'fixture-regression':
        assert set(value) == {'scope','checks','installedCryptoAPIEvaluated','clientControlExecuted','E02Promotion'}
        assert value['scope'] == 'PURE_FILTER_GENERATION_AND_SOURCE_SHAPE_CONTROLS_ONLY'
        assert all(value[k] is False for k in ('installedCryptoAPIEvaluated','clientControlExecuted','E02Promotion'))
    else:
        assert name == 'minimum-fixture'
        assert set(value) == {'scope','checks','cases','cryptoExecuted','actualClientExecuted','canonicalPromotion'}
        assert value['scope'] == 'MINIMUM_ROLE_REPLAY_ORIGIN_METADATA_CONTROLS_ONLY'
        assert all(value[k] is False for k in ('cryptoExecuted','actualClientExecuted','canonicalPromotion'))
        cases = value['cases']
        assert type(cases) is list and len(cases) == expected
        assert all(type(s) is str and 1 <= len(s) <= 160 for s in cases) and len(set(cases)) == len(cases)
    return value['checks'], value['checks'] == expected
'''+text[b:]
text=text.replace('e02-ordinary-api35-v3-pure-scope-execution-v1','e02-minimum-pure-scope-execution-v1')
a=text.index("        match = re.search(rb'\\nRan",text.index('def one('));b=text.index("        receipt['countAndOutputShapeMatched']",a)
text=text[:a]+"        observed, count_ok = output_shape(name, expected, stdout, stderr)\n        receipt['observedCount'] = observed\n"+text[b:]
text=text.replace("and receipt['sourcesUnchanged'])","and not receipt['forceRequested'] and receipt['sourcesUnchanged'])")
text=text.replace("'TWO_CHANGED_PURE_CONTROLS_ONLY_NO_ANDROID_OR_SERVICES'","'FIVE_CHANGED_PURE_CONTROLS_ONLY_NO_ANDROID_OR_SERVICES'")
text=text.replace("    ack = json.loads((HERE / 'coordinator-acknowledgement.json').read_text())\n    assert ack['sourceSubjectSha256'] == SUBJECT_SHA and ack['pureControlsAuthorized'] is True\n    assert ack['actualSourceQaAccepted'] is True and ack['actualSourceSecurityAccepted'] is True\n",'')
text=text.replace('complete = len(results) == 2','complete = len(results) == 5')
text=text.replace('e02-ordinary-api35-v3-current-pure-controls-execution-v1','e02-minimum-current-pure-controls-execution-v1')
text=text.replace("'BOTH_CHANGED_SEPARATE_PURE_SCOPES_COMPLETED'","'ALL_FIVE_CHANGED_SEPARATE_PURE_SCOPES_COMPLETED'")
text=text.replace("'configuration': pin(E / 'proposed-run-config.json'),","'configurations': [pin(E / ('proposed-' + role + '-run-config.json')) for role in ('incoming','archive')],")
text=text.replace("{'guard': 29, 'fixture': 27, 'consumer': 14}","{'guard': 29}")
text=text.replace("'unchangedScopeLink': pin(E / 'unchanged-control-scope-link.json')","'unchangedScopeLink': pin(E / 'unchanged-guard-scope-link.json')")
text=text.replace('e02-ordinary-api35-v3-current-controls-artifact-manifest-v1','e02-minimum-current-controls-artifact-manifest-v1')
text=text.replace('completeTwoChangedPureScopes','completeFiveChangedPureScopes')
p.write_text(text);p.chmod(0o600)
# Syntax and complete AST diffs are DATA; do not import/evaluate capture.
a=ast.dump(ast.parse(OLD.read_text()),indent=2,include_attributes=False)
b=ast.dump(ast.parse(text),indent=2,include_attributes=False)
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,value):
    target=HERE/name;target.write_text(value if type(value) is str else json.dumps(value,indent=2)+'\n');target.chmod(0o600)
write('capture-full-typed-ast-before.json',{'source':pin(OLD),'tree':a})
write('capture-full-typed-ast-after.json',{'source':pin(p),'tree':b})
write('capture-full-typed-ast.diff',''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(OLD),tofile=str(p))))
write('capture-full-source.diff',''.join(difflib.unified_diff(OLD.read_text().splitlines(True),text.splitlines(True),fromfile=str(OLD),tofile=str(p))))
write('control-plan.json',{'schema':'e02-minimum-current-pure-control-capture-plan-v1','actor':'/root/ordinary_api35_source','session':'/root/ordinary_api35_source','state':'PREPARED_NOT_EXECUTED_PENDING_ACTUAL_SOURCE_DECISIONS_AND_ROOT_RELEASE','subject':pin(E/'subject.json'),'frozenPlan':pin(E/'execution-control-plan.json'),'runner':pin(p),'previousTrustedCapture':pin(OLD),'separateCountsExpected':{'cleanup':29,'ui-regression':49,'minimum-ui':21,'fixture-regression':27,'minimum-fixture':43},'onceCommand':['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',str(p),'--execute-once'],'closure':'112 unique frozen descriptors plus subject, two configs,14 actually read archived data descriptors, both pinned interpreters, runner, both plans, root acknowledgement and actual review records; before-after per scope and overall.','lifecycle':'Unchanged established Popen.communicate pattern, timeout60s, inherited1MiB output-per-stream capture/truncation refusal, actual status/signal/EOF/reap/force/error/time; trusted finite scopes only, first failure stops without retry.','nodeShape':'One duplicate-free exact-key typed JSON output line, correct separate count and closed scope/false capability fields; minimum cases exact43 unique bounded names.','coordinatorAcknowledgementSchema':{'schema':'e02-minimum-current-controls-root-ack-v1','actor':'/root','sourceSubjectSha256':'296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4','pureControlsAuthorized':'boolean true only after actual root instruction','actualSourceQaAccepted':'boolean true from actual other-agent decision','actualSourceSecurityAccepted':'boolean true from actual other-agent decision','runner':'exact Pin','controlPlan':'exact Pin of this file','sourceQaReview':'actual frozen Pin','sourceSecurityReview':'actual frozen Pin'},'originalExternalToolReceipt':'Root persists original response object immediately; not authored or inferred by process journal.','independentResultReview':'Root-owned actual other-agent QA/security after execution; author does not approve own findings.','noTestsOrRuntimeExecuted':True,'unchangedGuardOnly':29,'noOldConsumer14Reexecution':True,'noAndroidSdkServicesGrants':True})
write('runner-subject.json',{'schema':'e02-minimum-pure-control-runner-source-subject-v1','author':'/root/ordinary_api35_source','state':'WRITES_STOPPED_RUNNER_SOURCE_ONLY_NOT_EXECUTED','frozenProducerSubject':pin(E/'subject.json'),'runner':pin(p),'plan':pin(HERE/'control-plan.json'),'fullTypedAstDiff':pin(HERE/'capture-full-typed-ast.diff'),'fullSourceDiff':pin(HERE/'capture-full-source.diff'),'preparationSource':pin(Path(__file__).resolve()),'actualSourceDecisionsAndRootAcknowledgement':'NOT_AUTHORED_HERE','actualControlsExecuted':False})
print(json.dumps({'state':'WRITES_STOPPED_RUNNER_PREPARED_NOT_EXECUTED','runner':pin(p),'plan':pin(HERE/'control-plan.json'),'subject':pin(HERE/'runner-subject.json')},indent=2))
