# Minimum ordinary evidence consumer v1

SOURCE preparation only. This standalone DATA consumer is bound to producer
subject `296acf346bb034bcb8becc22562494e5f37e78c3f78537d061e83455135315b4`
and export contract `69ad2717aeeb23ebdfcc326e79de7a3b1f9f8819a02157c97f6c91926f617943`.
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
| e02-ordinary-minimum-role-release-v1 | issuedAtUtcNs, notAfterUtcNs |
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
 commands:[Pin],ui:[{png:Pin,xml:Pin}],proxy:Pin,
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
this version. All nine staged source/config inputs must remain identical. New
attempt run IDs/configurations require a separately preserved, independently
reviewed version/subject; no historical failed rows migrate to it.

```text
RoleRelease = {schema:"e02-ordinary-minimum-role-release-v1",
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
ControlsSubject = {schema:"e02-minimum-controls-subject-v1",profileId,
 authors:[actor],operators:[actor],producerSubject:Pin,
 executedScopes:[ExecutedScope],unchangedScopes:[CarryScope],
 consumerSource:Pin,consumerControls:Pin}
ExecutedScope = {name,count,skips:0,result:Pin,sourceBefore:[Pin],
 sourceAfter:[Pin],stdout:Pin,stderr:Pin}
CarryScope = {name:"guard",count:29,oldSource:Pin,currentSource:Pin,
 actualResult:Pin,acceptance:Pin,
 meaning:"BYTE_IDENTICAL_CARRY_NOT_NEW_EXECUTION"}
```

The frozen producer plan requires cleanup29, ui-regression49, minimum-ui21,
fixture-regression27, minimum-fixture43. Counts alone never establish acceptance:
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

No tests or consumer invocation have run in this source task. Prepared54 controls
are targeted synthetic DATA positives/negatives, including full publication/native
joins and whole-history refusal/actor union, not an authenticated Android window.
They do not yet construct a full end-to-end positive `consume()` graph. Actual
source review must assess that integration coverage gap before activation; passing
individual controls cannot imply whole consumer/runtime readiness. All outer
wrappers/origin witnesses and two actual complete windows remain future inputs,
not fabricated examples of completed work. Independent source QA/security precede
any controls; actual control results require independent review before any later
separately authorized evidence inspection or experiment.
