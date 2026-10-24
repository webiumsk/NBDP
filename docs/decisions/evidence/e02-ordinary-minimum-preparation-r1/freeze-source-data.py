"""SOURCE/DATA-only freeze: stdlib reads, hashes, AST, JSON and owned writes.
Never imports worker modules, executes controls, issues grants or starts services.
"""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import uuid

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
P=ROOT/'experiments/prototypes/e02_ordinary_minimum_v1'
E=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1'
B=ROOT/'experiments/prototypes/e02_ordinary_client_api35_v3'
V3=ROOT/'docs/decisions/evidence/e02-ordinary-api35-preparation-r3'
PROFILE='e02-ordinary-minimum-rs-two-role-v1'
SCOPE='E02_ORDINARY_MINIMUM_RS_TWO_ROLE_WINDOW_ONLY'
PYTHON='/home/peterhorvath/.miniforge3/bin/python3.13'
NODE='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node'


def pin(p):
    p=Path(p);raw=p.read_bytes()
    if p.is_symlink() or p.resolve()!=p:raise ValueError('Noncanonical file')
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    raw=v.encode() if isinstance(v,str) else (json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode()
    p.write_bytes(raw);p.chmod(0o600)


def same(d):
    return pin(d['path'])==d


baseline=json.loads((V3/'subject.json').read_text())
old_sources=baseline['sources']
if len(old_sources)!=21 or not all(same(d) for d in old_sources):raise ValueError('Original21 sources changed')
write(E/'preserved-v3-source-pins.json',{'schema':'e02-minimum-baseline-preservation-v1','subject':pin(V3/'subject.json'),'configuration':pin(V3/'proposed-run-config.json'),'original21Sources':old_sources,'allOriginal21Exact':True})

write(P/'README.md', '''# Adopted minimum ordinary-client SOURCE profile

Profile `e02-ordinary-minimum-rs-two-role-v1` is a distinct two-window laboratory
method adopted by the coordinator after independent proposal review. This is
SOURCE preparation, not execution approval or E02 completion. The immutable old
eight-row contract and every failed API35/v3 observation remain preserved.

Incoming account B receives a business rumor from A and a distinct harmless
ordinary chat. Archive account A receives its own business self-wrap while the
original inner author A and recipient pB remain unchanged; the exact outer is
replayed and then a genuinely fresh wrap of the same frozen rumor is published.
These are two independently fresh sequential app/helper/AVD/rs-relay states,
with fixed per-role configs and separate finite original1800s grants. No failed
whole window can donate early rows. Only JS produces ordinary-client wraps;
current independent primary JS/Rust directions, both relays and every remaining
canonical criterion still require separate evidence.

Every stage requires source-bound actual subscription/EOSE, actual publication
and wire lineage, selected-note PNG/XML, real foreground helper custody and an
exact whole six-field client-origin export with ordered private tags. An empty
unsigned representation sig is preserved and compared under the explicit
contract. Identical replay may have NO_NEW_APP_FRAME because the relay deduplicates;
its bounded absence, exact original sent Buffer, actual publication/query and
fresh post-replay client export remain mandatory. It is never evidence that the
app handled the same outer twice. Fresh-wrap replay requires a new app frame.
Visible text nodes are not global bubble counts or business-effect measurements.

The frozen business oracle is an earlier producer EXPECTATION INPUT, not an
observation from a failed run. Historical inner and randomized NIP59 timestamps
need not lie inside the new lease; actual fresh preparation/wrapping/tool/window
custody establishes runtime freshness. Public scalar1 NSEC was encoded once by
a separately authorized pinned nip19 format-only operation, with raw lifecycle
and before/after inventory; no signing/encryption/transport test occurred.

Source-audited navigation uses one exact expanded Feeds collapse under the
original scroll/action/capture budgets, then actual System/Relays; Relay Settings,
Local Relays, owned Add a Relay field/trailing Add, exact local text row and Save.
No invented row DM flags exist. Known/New Requests are role-bound, with Back and
the expected note plus either the empty Message composer or the precise read-only
missing-recipient-relays warning. More Options/Copy raw JSON are source-backed.
All new DOM exposure assumptions are NOT_RUNTIME_VALIDATED and must fail closed.
Pinned-source label/line mapping and frozen failed-v3 Feeds XML are in preparation.

One source-backed Hide→Show visibility action, whole exact public NSEC and fresh
PNG/XML remain mandatory per role. Password accessibility metadata alone does not
prove masking; semantic class/package/resource-id shape never proves persistent
Android object identity. Tor saved/reopened Off, unknown/Quickstep refusal and
at most two known Settings/SystemUI Wait actions remain unchanged.

Read [EXPORT-CONTRACT.md](EXPORT-CONTRACT.md) for exact operands and evidence
origins, and [SUPERVISOR.md](SUPERVISOR.md) for authority/resource boundaries.
New whole-history aggregation/canonical integration is root-owned and absent.
All changed control suites are prepared, NOT RUN; only byte-identical guard29
has an explicit prior accepted scope link. Canonical E02 remains PARTIAL22;
Q01/Q08/Q13/Q15/Q27 remain BLOCKER. No production SDK/kind/NIP/deployment or merge.
''')
write(P/'SUPERVISOR.md', '''# Minimum profile finite supervisor

This supervisor executes exactly one fixed incoming OR archive role, never two
windows automatically. Materialized DATA configs are not grants. The separately
external-hash-bound root release must name the exact config/profile/role/window
and fresh run ID; no v3 release/schema is accepted. Each role gets fresh exclusive
output, app/helper/AVD/relay state and its own original1800s lease. A subsequent
role requires completed cleanup, fresh admission and a new separate grant.

Nine runtime source/data files are staged from exact config Pins. The fixed
run-config SHA is passed and verified in owned containers and fixture service.
The original source/SDK/APK/helper/guard-bundle/installed dependency checks remain.
The unchanged lease guard binds UTC/BOOTTIME/MONOTONIC; closed commands, original
namespace isolation, readonly mounts, capabilities, cgroups, limits, first error
and all-four-container cleanup/absence behavior remain inherited. The actual
source/config/typed AST diff identifies every changed method.

API35 SDK434-file inventory, Amethyst e6f464... APK5165a9f..., helpera680e5...,
Lavapipe, Android container8CPU/8GiB/PID512, guest4CPU/4096MiB are retained.
Requested userdata2048M and source6GiB admission floor are unchanged. All seven
retained old hardware files normalized userdata to6g; requested2048M is not proof
of a2GiB footprint. The separate SDK35 no-install6G profile failed before guest
startup with7326.61MB available versus7372.80MB required; this is no OS-failure
inference. Root additionally requires fresh>=8GiB free on the actual output
filesystem before EACH role grant. It is a conservative coordinator margin,
not a measured minimum, peak or guarantee, and does not lower the source6GiB
floor. Fresh12GiB MemAvailable, at least8 affinity CPUs and actual KVM are required.
No never-ANR health gate or larger deadline/resource allowance is introduced.

Original runtime caps remain120 UI actions,140 captures, seven generic scroll
attempts, one specifically source-backed Feeds collapse and at most two known
Settings/SystemUI Wait recoveries. Unknown/Quickstep dialogs refuse. Each native
validator must naturally satisfy actual spawnSync error/status/signal/stderr and
two-line source/validation conditions; no fabricated Popen EOF/reap fields exist.
Actual command journals retain their own lifecycle; original external tool
responses are separately preserved with exactly the fields that tool returned.

The source floor is not fresh runtime admission evidence. No SDK tools, Docker,
Android, lease/grant or control test was executed by this SOURCE preparation.
Current runtime plans/configs remain candidates pending independent SOURCE review,
changed pure controls, new root consumer review and exact activation decisions.
''')

# Fresh offline config materialization without importing or calling supervisor.
old=json.loads((V3/'proposed-run-config.json').read_text())
minimum=json.loads((P/'minimum-plan.json').read_text())
names=('supervisor.py','lease_guard.py','android_driver.py','ui-plan.json','fixture.mjs','fixture-plan.json','minimum-plan.json','business-rumor.json','chat-rumor.json')
configs=[]
for role,spec in minimum['roles'].items():
    path=E/('proposed-'+role+'-run-config.json')
    run_id=json.loads(path.read_text())['runId'] if path.exists() else uuid.uuid4().hex
    out=Path('/tmp/nbdp-e02-ordinary-minimum-v1/runs')/run_id
    if out.exists():raise ValueError('Fresh candidate output already exists')
    config={k:old[k] for k in ('runtimeImage','relayImage','sdkRoot','amethystApk','helperApk','sdkInventory','guardBundleInventory','guardBundleRoot','relayConfig')}
    config.update(schema='e02-ordinary-minimum-role-runtime-plan-v1',scope=SCOPE,profileId=PROFILE,ordinaryRole=role,windowId=spec['windowId'],account=spec['account'],peer=spec['peer'],runId=run_id,originalLeaseSeconds=1800,sourceAndDependencyPins=[pin(P/n) for n in names],state='SOURCE_ONLY_CANDIDATE_NOT_RELEASED',canonicalE02='PARTIAL22_UNCHANGED')
    write(path,config);configs.append(pin(path))

# Source-only syntax/tree inspection, never imports/compiles/evaluates workers.
python_changes=[];text_diffs=[]
def functions(tree):
    out={}
    def walk(items,prefix=''):
        for node in items:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                name=prefix+node.name;out[name]=ast.dump(node,include_attributes=False)
                if isinstance(node,ast.ClassDef):walk(node.body,name+'.')
    walk(tree.body);return out
for p in sorted(P.glob('*.py')):
    tree=ast.parse(p.read_text(),filename=str(p))
    before=B/p.name
    if before.exists():
        old_tree=ast.parse(before.read_text(),filename=str(before))
        dump_old=ast.dump(old_tree,include_attributes=False,indent=2)
        dump_new=ast.dump(tree,include_attributes=False,indent=2)
        write(E/(p.stem+'-full-typed-ast-before.json'),{'source':pin(before),'tree':dump_old})
        write(E/(p.stem+'-full-typed-ast-after.json'),{'source':pin(p),'tree':dump_new})
        ast_diff=''.join(difflib.unified_diff(dump_old.splitlines(True),dump_new.splitlines(True),fromfile=str(before),tofile=str(p)))
        write(E/(p.stem+'-full-typed-ast.diff'),ast_diff)
        a,b=functions(old_tree),functions(tree)
        python_changes.append({'file':p.name,'before':pin(before),'after':pin(p),'changedOrAddedFunctions':[k for k in b if a.get(k)!=b[k]],'removedFunctions':[k for k in a if k not in b],'unchangedFunctions':[k for k in b if a.get(k)==b[k]],'fullAstDiff':pin(E/(p.stem+'-full-typed-ast.diff'))})
    else:python_changes.append({'file':p.name,'after':pin(p),'newSourceOnly':True})
for p in sorted(P.iterdir()):
    if not p.is_file():continue
    before=B/p.name
    old_text=before.read_text() if before.exists() else ''
    text_diffs.extend(difflib.unified_diff(old_text.splitlines(True),p.read_text().splitlines(True),fromfile=str(before) if before.exists() else '/dev/null',tofile=str(p)))
write(E/'full-source.diff',''.join(text_diffs))
write(E/'python-function-diff.json',{'schema':'e02-minimum-full-python-ast-function-diff-v1','method':'stdlib ast.parse and dump only; JS full text diff, no JS engine parse/import/evaluation','changes':python_changes})
counts={p.name:sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_') for n in ast.walk(ast.parse(p.read_text()))) for p in P.glob('test_*.py')}
write(E/'static-source-checks.json',{'schema':'e02-minimum-static-source-partition-v1','allPythonSyntaxParsed':True,'pythonTestDefinitionsNotExecuted':counts,'javascriptEngineParseImportOrExecution':False,'guardCodeByteIdentical':(P/'lease_guard.py').read_bytes()==(B/'lease_guard.py').read_bytes(),'guardTestByteIdentical':(P/'test_lease_guard.py').read_bytes()==(B/'test_lease_guard.py').read_bytes(),'originalAvdConfigLiteralUnchanged':next(n.value.value for n in ast.parse((P/'supervisor.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONFIG' for t in n.targets))==next(n.value.value for n in ast.parse((B/'supervisor.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONFIG' for t in n.targets)),'actualExperimentsOrControlTests':0,'allOld21SourcePinsUnchanged':all(same(d) for d in old_sources),'requestedPartition':'2048M_UNCHANGED','sourceDiskFloorBytes':6*1024**3,'coordinatorExternalFreshAdmissionBytes':8*1024**3,'admissionMeaning':'Conservative per-role fresh output-filesystem margin; not measured minimum/peak or guarantee.'})

old_control=json.loads((V3/'current-controls-r1/subject.json').read_text())
archived=old_control['allTenArchivedReadOnlyControlData']
if not all(same(d) for d in archived):raise ValueError('Read-only oldUI DATA drift')
new_inputs=json.loads((E/'navigation-fixtures.json').read_text())['files']
control_data=[{k:d[k] for k in ('path','bytes','sha256')} for d in new_inputs]
write(E/'control-inputs.json',{'schema':'e02-minimum-prepared-control-inputs-v1','oldTenArchivedUiData':archived,'newFrozenFeedsData':control_data,'meaning':'Failed-history data and source-backed synthetic controls only, no successful observation donation.'})
write(E/'unchanged-guard-scope-link.json',{'schema':'e02-minimum-unchanged-guard-control-link-v1','scope':'29_PRIOR_GUARD_CONTROLS_ONLY_NO_NEW_EXECUTION','code':{'baseline':pin(B/'lease_guard.py'),'current':pin(P/'lease_guard.py')},'tests':{'baseline':pin(B/'test_lease_guard.py'),'current':pin(P/'test_lease_guard.py')},'priorAcceptedScope':pin(ROOT/'docs/decisions/evidence/e02-ordinary-api35-preparation-r1/current-controls-r1/control-acceptance.json'),'priorActualQa':pin(ROOT/'docs/decisions/evidence/e02-ordinary-api35-preparation-r1/current-controls-r1/actual-qa-review.json'),'priorActualSecurity':pin(ROOT/'docs/decisions/evidence/e02-ordinary-api35-preparation-r1/current-controls-r1/actual-security-review.json'),'exclusions':['Changed fixture27, UI49, newUI21 and cleanup29 require new meaningful current executions after SOURCE review.','Old consumer14 is not this new aggregate and provides no minimum acceptance.','No runtime qualification is carried.']})
scopes=[]
for name,file,count,kind in [('cleanup','test_cleanup.py',29,'PYTHON_MOCK_ONLY'),('ui-regression','test_android_driver.py',49,'PYTHON_XML_MOCK_ONLY'),('minimum-ui','test_minimum_driver.py',21,'PYTHON_ROLE_NAV_EXPORT_MOCK_ONLY'),('fixture-regression','test_fixture.mjs',27,'NODE_METADATA_ONLY'),('minimum-fixture','test_minimum_fixture.mjs',43,'NODE_ROLE_REPLAY_ORIGIN_METADATA_ONLY')]:
    argv=[PYTHON,'-I','-B',str(P/file)] if file.endswith('.py') else [NODE,str(P/file)]
    scopes.append({'name':name,'argv':argv,'plannedChecks':count,'meaning':kind,'timeoutSeconds':60,'executed':False})
write(E/'execution-control-plan.json',{'schema':'e02-minimum-changed-control-plan-v1','state':'PREPARED_NOT_EXECUTED_NOT_AUTHORIZED_BY_THIS_FILE','actor':'/root/ordinary_api35_source','sourceReviewPrerequisite':'Actual same-frozen-subject independent QA and security decisions plus explicit root instruction; no self-authored approval.','configuration':configs,'interpreters':{'python':pin(PYTHON),'node':pin(NODE)},'data':pin(E/'control-inputs.json'),'separateScopes':scopes,'captureRequirements':['Finite trusted foreground subprocess capture; original tool response saved separately with actual API fields, not fabricated portable attestation.','Exclusive one attempt per scope, stop first failure, preserve raw stdout/stderr0600, no retry.','Record actual child status/signal/error/force/elapsed/EOF/reap from capture API, without claiming unavailable fields.','Pin complete current source/config/interpreter/actually-read archived inputs before and after each scope and overall; retain raw first failure.','No Node crypto module main/sign/encrypt/native/network/services/Android/SDK invoked by metadata suites; dynamic imports only within never-called guarded main.','Do not rerun unchanged29guard or old14consumer; prior guard scope byte-bound only.','No experimentPASS or client runtime evidence follows from pure controls.'],'runtimeNext':'Root-owned strict minimum consumer/canonical integration SOURCE + independent review/control acceptance; fresh resource/grant per role, no activation here.'})

write(E/'README.md','''# Minimum ordinary-client SOURCE preparation r1

The coordinator adopted a distinct criterion-preserving two-role rs-relay method;
this preparation implements only its producer/driver/supervisor and typed export
contract. No new strict aggregate or canonical integration is implemented here.
All original files/failures and old eight-row scope remain unchanged. V3 is
supporting failure/source history, never a qualified donor row.

`subject.json` freezes exact sources, two independent fresh role configurations,
method adoption, full text/Python typed AST diffs, source/nav/oracle DATA,
interpreter and future control plans. Files outside the two delegated prefixes
were read only. Original21-source/config pin verification is in preservation
DATA; the actual source text confirms original clock/guard/caps/AVD2048M/cleanup.
Source6GiB floor and root fresh8GiB conservative output-filesystem admission are
both explicit. Actual normalized6g historical hardware prevents claiming a2GiB
runtime footprint. Every runtime prerequisite remains fresh/UNKNOWN until measured.

Python syntax/typed AST, source JSON and SHA inventories are SOURCE/DATA checks,
not compilation/tests/runtime interoperability. JS engine parse is pending its
reviewed pure suites. Separately authorized public scalar1 nip19 format encoding
ran exactly once and naturally exited0; full raw/custody pins are retained in
`scalar1-format-data`. It performed no encryption/signing/transport test. The
initial navigation DATA collector's basename ambiguity/exit1 and display-layer
JSONL inspection correction are explicitly retained, not erased.

New pure suites are PREPARED/NOT RUN: cleanup29, existing UI49, minimum UI21,
fixture metadata27 and minimum role/replay/origin metadata43. Counts are separate
planned definitions/cases, not actual passes. Only exact unchanged guard29 links
to its actual prior nonauthor QA/security acceptance. No old consumer14 scope is
relabelled as the new consumer. `execution-control-plan.json` states strict future
capture/first-failure requirements and original tool-response/process-journal
separation. No grants, leases, Android, SDK, Docker or services ran here.

All actual new navigation/account-role/export/duplicate behavior remains
NOT_RUNTIME_VALIDATED, with bounded source-backed selectors and fail-closed missing
controls. External tool witness schemas must reflect only fields actually
returned; no fabricated portable Popen or source-constructor attestation. The
root-owned consumer still needs whole-attempt membership, actual tool/command
custody, nonauthor/nonoperator same-window reviews and strict failed-history joins.
Canonical full current independent primary matrix and integration remain required;
E02PARTIAL22 and five architecture blockers are unchanged. Independent SOURCE
QA/security are pending. This author's record is not acceptance or execution authority.
''')
write(E/'preparation-execution.json',{'schema':'e02-minimum-source-data-preparation-record-v1','actor':'/root/ordinary_api35_source','session':'/root/ordinary_api35_source','actions':['Owned raw byte copies and SOURCE string transformations from immutable v3.','Pinned primary source read/hash/copy/read-only git diff33 upstream files and2 helper files.','Stdlib JSON/oracle/source inventories and ast.parse/full typed AST/text diffs; no worker imports.','Two fresh UUID/config DATA candidates; output roots absent; no lease or release.'],'knownActualCommands':{'sourceAudit':{'argv':['python3',str(E/'prepare-audit-data.py')],'toolChunk':'35b24b','exitCode':0},'negativeHistory':pin(E/'source-preparation-failures.json'),'formatOnlyOnce':pin(E/'scalar1-format-data/execution.json')},'preparationGenerators':[pin(p) for p in sorted(E.glob('prepare-*-source.py'))],'freezeGenerator':pin(E/'freeze-source-data.py'),'controlSuitesExecuted':0,'NbdpExperimentsExecuted':0,'AndroidSdkDockerServicesExecuted':0,'compilationExecuted':False,'independentSourceReviews':'PENDING_ACTUAL_ROOT_ASSIGNED_QA_AND_SECURITY','canonicalPromotion':False})

# Complete immutable subject: own prototype, DATA and explicit external authority.
artifacts=[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ('subject.json','artifact-manifest.json')]
sources=[pin(p) for p in sorted(P.rglob('*')) if p.is_file()]
external=[pin(ROOT/'docs/decisions/evidence/e02-ordinary-minimum-profile-proposal-r1/coordinator-adoption.json'),pin(ROOT/'docs/research/required-experiments.md'),pin(V3/'subject.json'),pin(V3/'proposed-run-config.json')]
write(E/'subject.json',{'schema':'e02-minimum-source-config-subject-v1','author':'/root/ordinary_api35_source','coordinator':'/root','state':'WRITES_STOPPED_PENDING_ACTUAL_INDEPENDENT_SOURCE_QA_SECURITY','scope':SCOPE,'profileId':PROFILE,'sources':sources,'configurations':configs,'sourcePreparationArtifacts':artifacts,'externalAuthority':external,'typedExportContract':pin(P/'EXPORT-CONTRACT.md'),'controlPlan':pin(E/'execution-control-plan.json'),'fullSourceDiff':pin(E/'full-source.diff'),'typedPythonFunctionDiff':pin(E/'python-function-diff.json'),'staticSourcePartition':pin(E/'static-source-checks.json'),'oldOriginal21SourcePinsPreserved':True,'actualChangedControlsExecuted':False,'runtimeExecuted':False,'minimumConsumerImplemented':False,'canonicalIntegrationImplemented':False,'noGrantLeaseApprovalWritten':True,'remainingGaps':['Independent SOURCE QA/security and actual changed pure controls with independent result acceptance.','Root-owned new strict whole-history consumer/canonical integration source and controls.','Fresh resource/grants and two whole-window runtime observations, actual account decoding/selected export/custody/cleanup.','Full current primary independent JS/Rust/both-relay canonical E02 workload and reviewed integration.'],'canonicalE02':'PARTIAL22_UNCHANGED','architecturalBlockersUnchanged':['Q01','Q08','Q13','Q15','Q27']})
write(E/'artifact-manifest.json',{'schema':'e02-minimum-source-preparation-artifact-manifest-v1','files':[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'],'manifestExcludesSelf':True})
for root in (P,E):
    for p in root.rglob('*'):
        if p.is_file():p.chmod(0o600)
        elif p.is_dir():p.chmod(0o700)
print(json.dumps({'state':'WRITES_STOPPED','subject':pin(E/'subject.json'),'configs':configs,'sourceDiff':pin(E/'full-source.diff'),'controlPlan':pin(E/'execution-control-plan.json'),'pythonDefinitionCounts':counts,'actualChangedTests':0,'actualRuntime':0},indent=2))
