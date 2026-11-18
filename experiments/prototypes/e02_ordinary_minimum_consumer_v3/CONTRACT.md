# Minimum ordinary evidence consumer v3 — producer2 DATA contract

SOURCE preparation only. This standalone DATA consumer is bound to producer
subject `ef91dc64189d7c47a4b4539c4dacd93a4c5c760da8f98bf1b203040bba6eeffd`
and export contract `7fd7b71898584b4b9f90fbe9ae4601df0d1b9f3dfdc995012dfd63824fba9bfc`.
It cannot retarget a repaired producer or the old eight-cell consumer. Preserve
this freeze and prepare a new reviewed version when those operands change.

The adopted method remains supplemental JS-only Amethyst evidence on rs-relay:
two fresh sequential role windows, five fresh exports, three selected-note
contexts and two original rumor IDs. It is not canonical E02 PASS, primary
JS/Rust/both-relay integration, a gate amendment or an SDK release.

## Trust and outcome

`consumer.py` reads no environment credentials, performs no subprocess, Android,
Node, network, crypto, SDK or GUI operation, and writes no files. Its CLI requires
separate externally known SHA256 pins for a consumption manifest and origin
envelope plus explicit canonical read roots. Every read is bounded, nofollow
through every path component, regular-file-only and checked before/after.

The origin envelope is an **external trust input**, supplied only after the
coordinator independently verifies actual agent-session/tool correspondence.
An operator can fabricate internally consistent JSON and synthetic reports;
hashes and this program cannot authenticate them. An origin argument is not a
portable process attestation or an independent approval created by the program.
The caller must preserve original tool responses and actual review messages
and authenticate the envelope outside the author/operator evidence graph.
Never claim runtime qualification from the synthetic controls.

Successful output is `SUPPLEMENTAL_DATA_CONSISTENT_WITH_EXTERNALLY_AUTHENTICATED_ORIGINS`.
Failure emits `REFUSED_NO_CONTRIBUTION`, exit2, zero contributing windows/exports.
All source/control/process/history/cleanup conditions precede contribution.
No earlier observation from a failed window can be donated. A successful
inspection still reports canonical `PARTIAL22_UNCHANGED`, primaryMatrixQualified
false, no measured business effects, no SDK admission or portable attestation.

## Primitive and filesystem rules

`Pin={path,bytes,sha256}` has exactly those keys. Paths are canonical absolute
strings; SHA256 is lowercase64hex. JSON is UTF8, duplicate-key-free, integer
only, no negative zero/nonfinite values, depth<=48/250000 nodes. Wire frames
retain depth<=32 and JS-safe signed integer domains. Booleans are not integers.

Only these exact root-schema paths permit nonnegative signed64 integers:

| Schema | Exact field paths |
| --- | --- |
| e02-minimum-selection-v1 | capturedMonotonicNs |
| e02-clipboard-capture-v1 | elapsedRealtimeNanos |
| e02-single-cell-lease-v1 | issuedUtcNs, deadlineUtcNs, issuedMonoNs, deadlineMonoNs, issuedBootNs, deadlineBootNs |
| e02-ordinary-minimum-role-release-v2 | issuedAtUtcNs, notAfterUtcNs |
| nbdp-e02-acceptance-method-refinement-decision-v1 | decidedAtUtcNs |
| e02-minimum-outer-witness-v1 | startedUtcNs, finishedUtcNs |
| e02-minimum-resource-witness-v1 | measuredAtUtcNs |

Nested schema strings cannot widen a parent document. Helper milliseconds,
counts/bytes and measured Node publication/exchange durations remain SAFE;
the latter are explicitly bounded0..1800000000000. Host and guest monotonic
absolute values are never compared. Rumor/outer timestamps may predate leases.

Per inspection: file<=64MiB (JSON<=16MiB), total distinct read bytes<=512MiB,
20000 distinct files and250000 descriptor visits. Each role window retains
<=4096 commands,140 captures,120 actual UI actions,64 fixture calls,
16MiB proxy/262144 rows and64 connections. These are DATA admission ceilings,
not new runtime budgets. SDK/APK/disk assets are not required inside this graph;
SDK inventory inspection is not a current SDK rehash or a portable replay image.

`/session/fixtures/x` resolves only to the current window's exact
`outputRoot/session/fixtures/x`. The consumer recursively resolves referenced
documents while retaining original descriptor bytes. `/input` pins require
explicit readonly bindings derived from frozen fixture-plan pins. Binding
duplicates in one original list, conflicts, cross-window paths and aliases
refuse. After both windows every actually read host pin is rehashed again.

## Consumer-owned outer schemas

All following objects are closed. Names below are exact keys, not pseudocode
permission to add fields. `Pin` refers to preserved originals; wrappers do not
replace raw records. Author/operator strings use actual canonical agent sessions.
Tables in the frozen producer contract remain authoritative for its nested
Gate/Generation/Attempt/Delivery/Exchange/Stage/FixtureCall/Custody/driver schemas.

```text
ConsumptionManifest = {schema:"e02-minimum-consumption-manifest-v1", profileId,
 candidate:Pin,history:Pin,windows:[incomingWindowPin,archiveWindowPin]}

Candidate = {schema:"e02-minimum-candidate-v1",profileId,authors:[actor],
 operators:[actor],producerSubject:Pin,producerContract:Pin,adoption:Pin,
 oracles:{business:Pin,chat:Pin},sourceControls:Pin,
 primaryEvidenceReferences:[Pin],
 scope:"SUPPLEMENTAL_ORDINARY_JS_RS_ONLY_NOT_CANONICAL_E02_PASS"}

AttemptInventory = {schema:"e02-minimum-attempt-inventory-v1",profileId,
 declaredScope:"ALL_MINIMUM_ATTEMPTS_AND_RELEVANT_LEGACY_NEGATIVE_CONTEXTS_THROUGH_THIS_INVENTORY",
 authors:[actor],operators:[actor],attempts:[AttemptMembership],
 legacyContexts:[LegacyContext]}
AttemptMembership = {subject:Pin,
 disposition:"CONTRIBUTE_WHOLE_WINDOW"|"NO_CONTRIBUTION",
 classification:string,reason:string}
AttemptSubject = {schema:"e02-minimum-attempt-subject-v1",profileId,attemptId,
 ordinaryRole,runId,windowSubject:Pin|null,rawOutcome:Pin,authors:[actor],
 operators:[actor],sourceSubject:Pin,outcomeClassification:string}
LegacyContext = {subject:Pin,authors:[actor],operators:[actor],
 meaning:"HISTORICAL_CONTEXT_NO_ROW_DONATION"}
```

The externally authenticated origin envelope closes the exact entire inventory,
not merely its successful rows. Preserve all failed/refused minimum attempts and
relevant legacy negative contexts with explicit classifications/reasons. Actual
content/tag/identity mismatches remain negative evidence; they cannot be silently
relabelled as benign environment exclusions. Actual same-inventory independent
review is required to verify these semantic classifications. Contributions must
have classification `COMPLETE_PENDING_INDEPENDENT_QUALIFICATION` and a complete
window subject. Other attempts cannot expose a contributing window. Raw outcome,
role/run/source of every contributing attempt equal its window's actual operands.

```text
WindowSubject = {schema:"e02-minimum-window-subject-v1",profileId,ordinaryRole,
 windowId,runId,outputRoot,authors:[actor],operators:[actor],sourceSubject:Pin,
 supervisorSource:Pin,runConfig:Pin,runRelease:Pin,resource:Pin,
 sourceControls:Pin,outer:Pin,lease:Pin,driver:Pin,supervisor:Pin,
 commands:[Pin],ui:[{png:Pin,xml:Pin}],proxy:Pin,phase:Pin,
 readOnlyMountBindings:[{guest:Pin,host:Pin}],graphFiles:[Pin],
 excludedFiles:[{path,reason}],sourcePolicyObservations:PolicyObservation}
PolicyObservation = {
 clockPolicy:"SOURCE_ENFORCED_THREE_DOMAINS_ORIGINAL_LEASE",
 perCommandClockChronology:"UNKNOWN_NOT_RECORDED",sdkAssetsBundled:false,
 guestHealth:"UNKNOWN",businessEffectsMeasured:false}
```

Graph files are exact originals beneath that run root. The command/UI/evidence/
session/cleanup/ownership roots are inspected for omitted regular files and
symlinks, under finite traversal limits. Error files/REVOKED remain failures.
Permitted exclusion reasons are only DISPOSABLE_DISK_IMAGE, PRIVATE_RUNTIME_KEY,
SDK_APK_INPUT, RAW_APPLICATION_DATABASE; none may hide one of those proof roots.
Public fixture scalar/NSEC/requests are retained as public synthetic DATA.

Only the two exact configurations pinned in the frozen producer subject qualify
this version. All sixteen staged source/config inputs must remain identical. New
attempt run IDs/configurations require a separately preserved, independently
reviewed version/subject; no historical failed rows migrate to it.

```text
RoleRelease = {schema:"e02-ordinary-minimum-role-release-v2",
 executionAuthorized:true,rootSession,executionSession,runId,scope,profileId,
 ordinaryRole,windowId,runConfig:Pin,sourceSubject:Pin,issuedAtUtcNs,
 notAfterUtcNs,qaReview:Pin,securityReview:Pin,guardRegressionEvidence:Pin,
 freshResourceAdmission:Pin,resourcePrerequisite:Pin,limits:string}

ResourceWitness = {schema:"e02-minimum-resource-witness-v1",runId,
 measuredAtUtcNs,outputFilesystem,freeBytes,memAvailableBytes,affinityCpus,
 kvmAccessible:true,rawReceipt:Pin,sourceIndex:Pin,
 actualAdmissionMeaning:"ACTUAL_CURRENT_ADMISSION_NOT_MINIMUM_OR_PEAK_OR_GUEST_HEALTH"}

OuterWitness = {schema:"e02-minimum-outer-witness-v1",runId,operator,
 interpreter:Pin,argv:[string],startedUtcNs,finishedUtcNs,launchSession,
 launchResponse:Pin,completionResponse:Pin,naturalExitCode:0,transcript:Pin}
```

Resource wrappers are faithful extractions of an actual immediately preceding
receipt, never new measurements or initialized declarations. They require8GiB
free on the output filesystem/12GiB MemAvailable/8 affinity CPUs/KVM and the
exact accepted SDK inventory. They name no peak/healthy guest guarantee.
Source/whole-window reviews must compare wrapper and original. Grants join the
actual source QA/security reports and raw resource receipt. Actual immutable
lease retains all six ns fields,60..1800seconds, same duration in UTC/MONO/BOOT,
inside grant bounds. No renewal occurs. Source-specific guarded clock behavior
and all command lifecycle receipts are checked; complete per-command timestamps
and clock sample history are **not emitted by this producer** and remain UNKNOWN.

The exact outer argv is `[actualInterpreter,"-I","-B",actualSupervisor,
"--config",path,"--config-sha",hash,"--release",path,"--release-sha",hash,
"--out",root]`, retaining actual order and source bytes. Its real interval
brackets lease issue. Cleanup is the original bounded exact-owned expiry
exception, so outer completion is not falsely required inside a lease deadline
that authorizes runtime actions only. The first window's actual outer completion
and cleanup precede the second launch. Source/journal/tool witnesses are distinct;
do not manufacture EOF/reap/force/Popen fields absent from the real outer API.

## Actual reviews and control lineage

```text
OriginEnvelope = {schema:"e02-minimum-origin-envelope-v1",profileId,
 method:Pin,candidate:Pin,history:Pin,windowSubjects:[Pin],
 attemptSubjects:[Pin],legacyContexts:[LegacyContext],reviews:[ReviewOrigin],
 tools:[ToolOrigin],
 provenanceLimit:"EXTERNALLY_AUTHENTICATED_COORDINATOR_TRANSCRIPTION_NOT_PORTABLE_ATTESTATION"}
ReviewOrigin = {kind:"SOURCE"|"CONTROL"|"WINDOW"|"HISTORY",
 role:"qa"|"security",actor,session,subject:Pin,
 decision:"ACCEPT_EXACT_SCOPED_EVIDENCE",findings:[FindingDisposition],review:Pin,
 rawSessionEvidence:Pin,visualChecks:[string]}
ToolOrigin = {witness:Pin,operator,launchSession,
 launchResponse:Pin,completionResponse:Pin}
FindingDisposition = {id,severity:"LOW",classification:"NONOPERATIVE_UNUSED_PLAN_NSEC",
 disposition:"ACCEPTED_WITHOUT_RUNTIME_INPUT_CHANGE",actualDispositionEvidence:Pin}
```

Two actual separate reviewer sessions must accept each exact source, control,
whole-window and whole-inventory subject. The forbidden reviewer union includes
all candidate/control/history/window/attempt/legacy authors and operators plus
the known producer, coordinator and this consumer author. This includes excluded
attempts and the other role window. Review-shaped operator JSON is insufficient.
The raw report and real session evidence remain separately pinned originals.
WINDOW reviews additionally carry exact visualChecks:
`["actual-account-gui","tor-off-saved-reopened",
"all-window-selected-note-pngs","helper-clear-copy-capture-custody"]`;
other review kinds have `[]`. Visual assertions are genuine review findings,
not OCR claims manufactured by this checker.

Findings are normally empty. A SOURCE review may retain exactly the known LOW
unused-plan-NSEC finding, with its actual identifier and a pinned actual independent
disposition. This is not self-approval or a generic severity waiver. No MEDIUM,
different finding or unresolved evidence/control/window/history finding is allowed.
Raw original reports and negative facts remain unchanged; the externally verified
origin envelope must confirm the real independent disposition, not an operator's
invented acceptance. The checker does not authenticate that correspondence itself.

```text
ControlsSubject = {schema:"e02-minimum-controls-subject-v2",profileId,
 authors:[actor],operators:[actor],producerSubject:Pin,
 executedScopes:[ExecutedScope],unchangedScopes:[CarryScope],
 componentCarry:Pin,producerActual35:Pin,consumerSource:Pin,consumerControls:Pin}
ExecutedScope = {name,count,skips:0,result:Pin,sourceBefore:[Pin],
 sourceAfter:[Pin],stdout:Pin,stderr:Pin}
CarryScope = {name:"guard",count:29,oldSource:Pin,currentSource:Pin,
 actualResult:Pin,acceptance:Pin,
 meaning:"BYTE_IDENTICAL_CARRY_NOT_NEW_EXECUTION"}
```

The current executed scopes, in order, are observation-model20,
public-identity-metadata8 and producer2-source-wiring7. Older169/guard29
scopes remain separately named reviewed component carry, never new executions. Counts alone never establish acceptance:
same-source raw outcomes/streams and actual independent CONTROL reviews remain
mandatory. SourceBefore/After are equal pinned reviewed source lists; the raw
capture result retains its genuine interpreter/argv/timing/lifecycle operands.
The unchanged guard29 is explicit byte-bound carry, not a new execution. The
old14 eight-profile consumer scope is not a substitute for new consumer controls.
Consumer source/control subjects are pinned separately, not self-approved.
The source packet contains no actual source/control/window acceptance or grant.

## Wire, replay, attribution and clipboard

Every role's actual preparation publishes both10050 inboxes, preserves both
immutable ws.send buffers/callback hashes/positive actual ACKs, and binds the
exact current role, two frozen inner rumors and finite ordered stage set.
All fixture commands/replies and all raw app/backend proxy rows remain in the
whole graph, including unrecognized/late frames. Source-native request/stdin/
stdout/stderr/binary/source pins recursively join the exact readonly mounts.
The producer's real spawnSync success/source-echo conditions remain source-backed;
the consumer introduces no invented Popen fields or new crypto execution.

Four stages require an actual new app socket frame and current successful send
callback with the same connection/REQ/EOSE/attempt epoch. Replaced REQ, reconnect,
CLOSE/CLOSED or new EOSE cannot reuse a generation. Only archive-identical-replay
may use actual relay-query origin with delivery null and clientReceiptEstablished
false. The sealed publication intent/close interval must show no candidate frame;
an incomplete candidate/callback cannot masquerade as absence. Later history is
preserved and inspected without claiming eternal absence. Initial/identical
serialized sent EVENT bytes are equal; fresh wrap has a different outer ID and
the same original inner fields. Archive account/outer recipient=A, inner author=A,
private ordered recipient=B. Incoming chat has normalized role chat/dispatchfalse;
archive always dispatchfalse; these are eligibility, not measured business effects.

All five exports require a fresh case-specific helper CLEAR, actual selected-note
long press, actual More Options/Copy raw JSON taps and helper CAPTURE/read sequence,
with actual bounds/raw command/UI custody. Helper focus, sentinel, timestamps,
one text/plain item, raw bytes/hash and immutable case-specific paths must join.
No fixture/host clipboard substitution is allowed. Only exact six fields or six
plus `sig:""` are accepted; content/tag order/UTF8/NIP01ID remain exact. Replay
visible matches1..3/uniquely lowest position are not global bubble counts.
Global duplicate count stays null/UNKNOWN, businessEffectsMeasuredfalse.

The actual complete nprofile GUI token is independently Bech32/TLV decoded and
joined to the role account; the decoder is part of this source/review/control
scope. GUI context requires actual enabled Amethyst note and Back plus empty
owned composer or exact read-only missing-recipient-relays warning. Saved/reopened
TorOff and selected PNGs require genuine independent visual review of this graph.

## Known source-only metadata finding

The frozen minimum/ui/fixture plans contain an unused65-character incoming NSEC
literal. This is preserved and **not normalized**. The actual driver uses its
correct63-character scalar2 constant; the supervisor does not consume plan.nsec.
This consumer binds actual input commands to that exact used constant, independently
decodes actual account GUI and joins actual wire/inner tags. It never asserts that
all documentary plan NSECs decode correctly. The coordinator's visible finding
and future versioned repair/regression remain separate; no runtime success or
key leak follows from the nonoperative literal or this source inspection.

## Remaining preparation and independent review

No tests or consumer invocation have run in this source task. Prepared86 controls
are targeted synthetic DATA positives/negatives, including full publication/native
joins and whole-history refusal/actor union, not an authenticated Android window.
They do not yet construct a full end-to-end positive `consume()` graph. Actual
source review must assess that integration coverage gap before activation; passing
individual controls cannot imply whole consumer/runtime readiness. All outer
wrappers/origin witnesses and two actual complete windows remain future inputs,
not fabricated examples of completed work. Independent source QA/security precede
any controls; actual control results require independent review before any later
separately authorized evidence inspection or experiment.

## Narrow revision2 remediation

This source revision preserves all input schemas, producer pins, bounds, gates
and external-origin limitations. The original v1 subject and actual independent
QA/security HOLD reports remain immutable in the preparation provenance.

- `QA-E02-CONSUMER-COMPOSER-001` /
  `SEC-E02-MIN-CONSUMER-COMPOSER-002`: match the frozen producer's unique owned,
  enabled empty EditText **ancestor containing** the Message label. Descendant
  search from the TextView was a false refusal. The existing Back/note/copy/
  helper/PNG/raw custody gates remain. Source-backed synthetic full `selection()`
  positives and foreign/disabled/nonempty/detached/ambiguous/warning negatives
  are definitions only, not observed Android compatibility.
- `QA-E02-CONSUMER-RPC-WRAPPER-002` /
  `SEC-E02-MIN-CONSUMER-RPC-001`: exact raw second reply is
  `{ok:true,value:normalized}` as emitted by pinned Rust `main.rs`; compare
  `.value` with `record.rust`. Do not unwrap arbitrary layers or reinterpret
  errors, extra keys, missing/count/changed replies. Source echo and all other
  raw input/output/role/native pin joins remain unchanged.
- `QA-E02-CONSUMER-CANDIDATE-003`: candidate presence uses the frozen producer
  predicate: selected connection/subscription EVENT whose event object's ID
  equals the selected event ID. Altered payload or an uncompleted callback
  cannot masquerade as query-only absence. Qualified delivery still requires
  exact whole-event equality and existing current generation/attempt/callback
  custody. Only the sealed interval establishes that bounded absence; later
  raw frames remain visible without inventing eternal absence or a blanket
  late-frame failure.

No v1 controls ran. Revision2 retains the54 original test method bodies and
adds32 targeted definitions; only the synthetic publication fixture's RPC form
and candidate injection operands change. Full positive whole `consume()` coverage
remains absent and explicit. Later genuine complete evidence may exercise that
path; no new normative gate or positive runtime acceptance is introduced here.


## Producer2 observer binding

The producer subject schema is `e02-ordinary-minimum-producer2-source-subject-v1`.
Current profile is `e02-ordinary-minimum-rs-two-role-v2`. The producer-owned runtime
configuration, release, driver/supervisor result, prepared, publication/intent/
window, transport, validated-wire, producer-validation and fixture-command DTOs
use their producer2 `-v2` schemas. Unchanged clipboard/selection/lease/fixture-call/
raw-proxy and consumer-owned witness DTOs retain their original schema names.
The strict schema-specific ns registration adds only the exact v2 role-release
fields; arbitrary nested schemas still cannot widen integer domains.

WindowSubject additionally requires `phase:Pin`, exactly the final whole-window
`outputRoot/session/fixtures/phase-trace.jsonl` member. Both it and the final proxy
stream must be0600, complete newline-terminated JSONL, fully retained in graphFiles,
and together fit one16777216-byte ceiling. These are DATA admission checks, not
proof of peak memory or physical persistence. Each stage contains the exact
producer2 observation object from the frozen export contract; no mutable per-stage
stream Pin may substitute for final stream membership.

`observer.py` validates every retained phase's closed fields, profile/window/role,
sequence, process-monotonic decimal string, optional actual callback context and
original fixed guard label. Synchronous guard ENTRY/EXIT pairs must be healthy.
All raw backend and app/proxy callbacks join the complete original raw streams in
order; backend raw callback precedes the original guard pair and parse observation.
APP send completion joins the original source/send raw sequences and buffer hash.
Proxy send invocation/return/callback chains retain their own original observations.
No error, rejection or timeout in late history is discarded to qualify an early
stage. Callback-time observedAttempt never replaces original generation/attempt
lineage, which remains checked by the preserved wire validator.

Each successful exchange needs its exact immutable `label-N-sent-frame.json`
files and `label-outcome.json` whole-window member, one source-defined timer/open/
resolved span, matching callbacks, result bytes and healthy observer snapshot.
Preparation requires its own two-inbox outcome; stages bind their publish/query
spans inside fresh nonoverlapping stage phase ranges. Healthy budget and phase
writer states are checked separately against exact acknowledged retained-prefix
bytes/count/hash. They may have different failure strings in rejected evidence;
no rejected state can contribute. Neither acknowledged prefixes nor file hashes
claim independent physical-write attestation.

An actual observer-final-state.json, when present, must be healthy and bind final
whole streams. Absence is permitted because Docker force-removal need not deliver
a signal; no fictional final state, Popen lifecycle or signal receipt is required.
The original host/operation/controller source boundaries remain pinned reviewed
behavior; a successful source inspection does not invent their runtime receipts.

The current controls wrapper requires exact producerActual35, its separately
preserved20/8/7 execution/stream records and actual independent CONTROL origins,
plus the producer's exact componentCarry/function proofs. Its result subject may
still retain its original pre-review state; actual independent acceptance is a
separate externally authenticated original, never an author rewrite. Guard29 and
older169/diagnostic51 are named historical scopes only. Full wrapper acceptance,
consumer3 source/control pins and external origins remain separately required.

Successful result schema is `e02-minimum-consumption-result-v2`; fixed counts stay
2whole windows/5exports/3contexts/2rumors. Its metadata finding is
`PRODUCER2_PUBLIC_SCALAR_METADATA_CORRECTED_OLD_FINDING_PRESERVED`: producer2 corrects
unused documentary operands from the known public scalars; old malformed records
and their actual dispositions remain preserved history. No live wrong-account
or secret-input incident is inferred. Existing legacy LOW-finding source-origin
handling remains available only with its original narrow disposition; it does
not waive an active unresolved finding.

## Defined controls and readiness limits

The original86 targeted definitions remain in test_data_controls.py, with only
explicit producer2 profile/DTO fixture adaptation and an empty observation marker.
Those layered wire tests deliberately do not invoke observer.Trace. New controls
in test_observer.py define positive complete observer+publication DATA graphs and
field mutation negatives. They use owned temporary public synthetic files only;
no cryptographic validation, real reviewer origin or real client is simulated as
actual evidence. All control execution counts are initially zero.

There is still no complete positive synthetic graph traversing consumer.consume's
entire two-window ownership/UI/tool/review path. The new positive coverage is the
integrated observer+wire subgraph. This remains an explicit coverage gap before
any activation decision; targeted controls alone cannot qualify actual windows.

External runtime prerequisites are NOT_READY when absent. In the current session
the historical Rust binary `/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust`
and guard-bundle manifest referenced by the frozen role configurations are absent.
Historical accepted DATA does not create current tool bytes, runtime grants,
qualified client windows, current primary22, canonical PASS or SDK authorization.
Consumer3 SOURCE acceptance may release bounded DATA controls only; activation
requires those genuine external operands and separate reviews/grants.
