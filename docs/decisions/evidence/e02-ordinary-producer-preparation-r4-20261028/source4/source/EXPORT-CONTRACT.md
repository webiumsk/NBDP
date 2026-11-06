# Minimum ordinary-client export contract v1

This is an experimental **SOURCE contract**, profile
`e02-ordinary-minimum-rs-two-role-v3`. It implements the coordinator's separately
adopted minimum method. It grants no execution or qualification authority.
No aggregate consumer or canonical integration is implemented in this directory.
The original eight-row profile/consumer remains strict and unchanged.


## Current SOURCE2 closed declarations and precedence

For current producer4 SOURCE2, the closed command-v3, observer-v3, budget-v3 and
allocation/account objects below supersede the stale seven-key command,
observer-v2/two-field state and16MiB service-stream declarations in preserved
SOURCE1. The adopted nonblocking guard and controller-audit budget methods are
unchanged. All original business/chat/replay semantics, two fresh windows/five
exports, GUI/account/Tor/custody, isolation, source/SDK/guard/dependency/end checks,
resources and clocks remain mandatory. These corrections create no grant or
qualification and preserve every failed attempt without row donation.

## Closed membership and fresh windows

Exactly two separate finite windows are required, with distinct run IDs, output
directories, original leases and fresh AVD/app/helper/rs-relay states. Maximum
concurrency is one. Each original lease is at most1800s, never renewed. Cleanup,
fresh resource admission and a separate exact grant precede the other window;
there is no automatic second run or inherited deadline. A failed whole window
cannot donate an earlier export or GUI row. Preserve every attempt and refusal.

| Role/window | Actual account | Counterparty | Ordered stages |
| --- | --- | --- | --- |
| `incoming` / `incoming-b` | public scalar2, pubkeyB | pubkeyA | `incoming-business`, `incoming-ordinary-chat` |
| `archive` / `archive-a` | public scalar1, pubkeyA | original inner recipientB | `archive-business`, `archive-identical-replay`, `archive-fresh-wrap-replay` |

Here A is `79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798`
and B is `c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5`.
Both are explicitly public disposable fixtures. Only JS produces these ordinary
wraps. The complete independent JS/TypeScript-package and Rust primary matrix,
both configured relays, peer/self roles, inboxes, negatives, replay and correlation
stubs remain separate mandatory current evidence. This profile asserts no Rust
producer/Amethyst or strfry/Amethyst coverage.

The business input is the exact shared frozen `business-rumor.json`, including
its timestamp and NIP01 ID, in both windows. Its origin is an earlier producer
**expectation input**, never a failed observation donation. The harmless chat is
the distinct frozen `chat-rumor.json`. Both windows require new actual client
exports. The supporting v3 first-cell history is never converted into subrows.

## Primitive types and schema-specific integers

`Pin = {path: absolute canonical string, bytes: nonnegative bounded integer,
sha256: lowercase hex64}` with exactly these fields. Symlink/path escapes,
descriptor drift, duplicate JSON keys, NaN/Infinity and unrecognized fields in
typed evidence contracts refuse qualification. Resolve `/session/fixtures/...`
only to that exact window's `out/session/fixtures/...`; preserve the original
guest descriptor and a separate verified host binding. Do not rewrite raw proof.

Wire/rumor and JS event fields retain the existing strict safe-integer limits;
kind14, timestamp, NIP01 ID, signatures, content and ordered tags retain the
existing validators. No general timestamp exception or arbitrary schema allowlist
is introduced. The future consumer must enumerate metadata operands explicitly:

- `e02-minimum-selection-v1.capturedMonotonicNs`: nonnegative signed64 host ns.
- `e02-clipboard-capture-v1`: original helper `elapsedRealtimeNanos`,
  `wallClockMillis`, `clipboardTimestamp`, bytes/count integer operands only,
  under the original helper contract. Host and guest monotonic values are never
  compared as absolute timestamps.
- Original lease UTC/BOOTTIME/MONOTONIC ns and cleanup/command lifecycle metadata
  retain their exact existing schemas, domains and source-reviewed bounds.
- Proxy `sequence`, connection IDs, request/EOSE sequence values and publication
  attempt epochs are positive JS safe integers. An epoch is1 or2 in the incoming
  window and1 through3 in archive; it is scoped to one window, not globally unique.
- Visible text-node counts are integers1 through3 for archive replay and exactly1
  for initial/chat selection. They are not global bubble or business-effect counts.

Raw command streams and Docker inspections remain separately pinned originals.
Do not parse unrelated opaque fields merely to relax an existing integer rule.
Any genuinely new runtime schema needs an explicit reviewed typed mapping.

For this distinct multi-observation consumer contract the finite DATA admission
ceilings per window are4096 command receipts,140 UI captures,16,777,216 proxy
bytes/262,144 proxy rows,20,000 regular graph files and250,000 descriptor visits.
These are conservative parser/cardinality ceilings, not increased runtime action,
scroll, capture, cgroup or deadline budgets and not measured usage. A source
upper-bound accounting is840 snapshot receipts (140×6),240 UI action receipts
(120×2), at most544 boot/fixed-admission receipts,128 fixture-call receipts
(64×2), plus128 conservative create/cleanup receipts: below1880.4096 leaves
bounded bookkeeping margin. The16MiB raw DATA parser ceiling is not a current
runtime allowance: current service proof representations compete within8380416
bytes under the fixed split below, so a parser-admissible larger stream cannot
qualify this producer. Do not copy the old single-cell512 receipt ceiling
or interpret the new consumer ceiling as permission for arbitrary commands.

## Exact nested operand types

All objects below have exactly the named keys; `?` denotes a conditional key
only where explicitly stated. `Safe` means a nonnegative JS-safe integer, never
a boolean/float/string coercion. `Seq` is a positive Safe bounded by proxy rows;
`CommandSeq` is1..4096. A subscription is a UTF8 string bounded by the262144-byte
raw frame cap; filters are the exact bounded/depth32 JSON filter array from the
actual REQ, with at least one matching1059/#p filter. No expected filter is
substituted for actual client bytes.

```text
Generation = {connection:1..64, subscription:string,
              requestSequence:Seq, eoseSequence:Seq}
Gate = Generation + {filters: actual JSON filter array}
Attempt = {epoch:1..roleStageCount, stageId: closed StageId}
           // epoch == index+1 for a successful role window
Delivery = {connection:1..64, subscription:string,
            rowSequence:Seq, sentSequence:Seq,
            forwardGeneration:Generation, completionGeneration:Generation,
            forwardAttempt:Attempt, completionAttempt:Attempt}
ValidationPins = {transport:Pin, validation:Pin}
GuestHostBinding = {guest:Pin, host:Pin}
WireOrigin = "ACTUAL_APP_SOCKET_FRAME"|"ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME"
Inner = {id:hex64,pubkey:A,created_at:Safe,kind:14,
         tags:[["p",B]],content:exact frozen string}
Signed1059 = {id:hex64,pubkey:hex64,created_at:Safe,kind:1059,
              tags:[["p",roleAccount]],content:encrypted string,sig:hex128}
```

Every `GuestHostBinding.guest.path` is unique; a repeated reference may resolve
to the same binding, but divergent bytes/host aliases refuse. Host paths must be
the exact corresponding window root, never another run, a shared expected oracle
or an arbitrary alias. Raw validated frame/transport records remain unchanged.

```text
SentFrame = {frame:Pin, eventId:hex64|null, messageType:"EVENT"|"REQ",
             sendInvoked:true, sendCallbackCompleted:true,
             callbackBufferHash:hex64}
ActualReply = {rawBase64:string, frame: ["OK",hex64,true,string]
                                      |["EVENT","e02-owned-query",Signed1059]}
Exchange = {ack:[ActualReply], received:[ActualReply],
            eose:null|{rawBase64:string,frame:["EOSE","e02-owned-query"]},
            sentFrames:[SentFrame], elapsedNanoseconds:Safe[0..1800000000000]}
Prepared = {schema:"e02-minimum-prepared-v2", profileId, windowId, role,
            rumors:{business:Inner,chat:Inner}, events:[Signed1059],
            expected:{closed role StageId -> {stage:Stage,rumor:Pin,content:Pin}}}
PrepareResult = {profileId,windowId,ordinaryRole,expected,prepared:Pin,inboxes:Pin}
StatusResult = {profileId,windowId,stageId:StageId|null,stageIndex:0..roleStageCount,
                complete:boolean,ready:boolean,gate:Gate|null,captureSequence:Safe,
                scope:"SUBSCRIPTION_PREFLIGHT_NOT_CLIENT_RECEIPT"}
PublishResult = {profileId,windowId,stage:Stage,publication:Pin,
                 publicationWindow:Pin,validation:ValidationPins,
                 producerValidation:Pin,actualNewAppFrameObserved:boolean}
```

`SentFrame.frame` pins the exact immutable Buffer passed to `ws.send`, with its
actual send callback and unchanged Buffer hash. The exchange waits for callbacks
and matching ACK/EOSE. A reconstructed event serialization is not this operand.
Compare initial and identical replay sent-frame bytes directly. EVENT IDs match
their frame; a REQ has eventId:null and the exact owned query subscription.
`Exchange.elapsedNanoseconds` is a measured monotonic duration under the original
lease, not absolute host ns, resource usage, or an invented API completion flag.

```text
PublicationWindow = {schema:"e02-minimum-publication-window-v2",
 profileId,windowId,stageId:StageId,eventId:hex64,attempt:Attempt,
 intentSequence:Seq,closeSequence:Seq,actualNewAppFrameObserved:boolean,
 candidateAppFrameSeen:boolean,elapsedNanoseconds:Safe[0..1800000000000],
 clock:"NODE_PROCESS_HRTIME_MONOTONIC",origin:WireOrigin}
FixtureCall = {schema:"e02-minimum-fixture-call-v2",profileId,windowId,
 operation:"prepare"|"status"|"publish",ordinal:1..64,
 commandSequence:CommandSeq,command:Pin,reply:Pin}
CustodySegment = {commandSequenceFirst:CommandSeq,commandSequenceLast:CommandSeq,
 uiCaptureSerialFirst:1..140,uiCaptureSerialLast:1..140,
 uiActionCountBefore:0..120,uiActionCountAfter:0..120,
 uiCaptures:[{png:Pin,xml:Pin}]}
```

Window intent/close sequence values join the actual `PUBLICATION_INTENT` and
`PUBLICATION_WINDOW_CLOSED` rows in `e02-minimum-proxy-row-v1` capture. A query-only
absence requires candidateAppFrameSeen:false within that sealed interval; an
uncompleted candidate forward/callback cannot masquerade as absence. Retain and
inspect all later raw history too: absence in this bounded interval is not a claim
that no later app frame ever existed. Duration is measured, not presumed10s.

Each observation's subscriptionStatusReply pins the exact actual successful
status wrapper; subscriptionStatusCall pins its FixtureCall and
subscriptionStatusCommand pins the corresponding actual command receipt.
Parsed reply.result equals embedded subscriptionStatus. The whole ordered
fixtureCalls array, stage custody segments and complete command/UI inventory
must join without omitted, reordered, duplicated or unexplained commands.
Status is preflight; the publisher must independently bind its own current gate.

`e02-minimum-transport-v2` has exactly schema and six Pin fields:
frame, wire, jsRequest, rustRequest, jsResult and rustResult. The validated-wire
record has exactly schema,profileId,windowId,stageId,origin,
clientReceiptEstablished,transport:Pin,rustBinary:Pin,rustSource:Pin,rustInput:Pin,
rustStdout:Pin,rustStderr:Pin,rustExit:0,rustSignal:null,actualQueriedEvent,
js,rust,clientRetention. `js` and `rust` are the same successful normalized
current-adapter result, with the exact frozen rumor, correct declared role and
dispatch eligibility; business includes the exact parsed frozen envelope and
chat omits envelope. Decrypt counters retain the original validator meanings.

The actual native API is Node `spawnSync`, not Popen. The producer requires no
`native.error`, status0, signal:null, stderr length0, exactly two stdout JSON
lines, first source echo identical to the pinned Rust source and second successful
validation identical to JS. Retain exact stdin/stdout/stderr Pins. The record
does not invent Popen/EOF/reaped/error:false fields the native API never emitted;
outer actual Node command lifecycle/tool witnesses remain separately required.

Frozen rumor.created_at may precede both leases. NIP59 randomized outer/seal
created_at may also precede a lease. Never inherit a one-cell timestamp-inside-
lease test for these protocol fields. Freshness comes from actual current
source-bound preparation/wrapping/sending, fresh exclusive state, guarded
original clocks and authentic tool/history witnesses, not from changing the
shared inner oracle or pretending protocol timestamps are execution witnesses.

The proxy row exact common keys are schema (`e02-minimum-proxy-row-v1`), sequence,
utc (ISO UTC string) and direction. Direction-specific keys are:

```text
OPEN: connection,userAgent(string<=1024chars)
APP_TO_RELAY: connection,rawBase64
RELAY_TO_APP: connection,rawBase64,publicationGeneration:Generation|null,
              publicationAttempt:Attempt|null
APP_SOCKET_SEND_COMPLETE: connection,sourceSequence:Seq,
              publicationGeneration:Generation|null,publicationAttempt:Attempt|null
CLOSE: connection
PUBLICATION_GENERATION_INVALIDATED: connection,
              reason:"REQ_REPLACED"|"APP_CLOSE"|"RELAY_CLOSED"|"CONNECTION_CLOSED",gate:Gate
PRODUCER_TO_RELAY: exchangeLabel,rawBase64,frame:Pin
RELAY_TO_PRODUCER: exchangeLabel,rawBase64
PUBLICATION_INTENT: stageId,eventId,attempt
PUBLICATION_WINDOW_CLOSED: stageId,eventId,attempt,intentSequence,
              actualNewAppFrameObserved,candidateAppFrameSeen,elapsedNanoseconds
```

`exchangeLabel` is the closed preparation or stage publish/query label,1..48
lowercase ASCII letters/digits/hyphens. Backend outgoing and incoming raw bytes,
including unrecognized/negative frames, compete with phase and all other service
proof representations within8380416 bytes. Header4096 and diagnostics4096 complete
the fixed8388608 service share; all64 controller slots occupy the other8388608.
The aggregate ceiling remains16777216, never an additional per-stream allowance. Query EOSE is retained raw, never synthesized.

The close row's own common sequence is closeSequence in PublicationWindow. All
Nostr rawBase64 bytes must decode strictly and join the exact actual decoded
frame, without generating an EVENT/EOSE to repair a missing row. Window duration
and booleans have the exact domains specified above; names alone never widen
integer types. Publication windows do not discard any later raw proxy rows.

## Producer and actual wire lineage

The only fixture CLI/control operations are `serve`, `prepare`, `status` and
`publish`; external requests have exactly `{op}` and cannot supply an event,
key, nonce, role, stage index or recipient. Role/account/window comes exclusively
from the hash-bound fixed run configuration. The prepared stage order is finite;
prepare is once-only and a failed publication remains sticky. Every ordinary
wrap is produced by the same pinned existing `transport.wrap` implementation;
no crypto primitive or nonce profile is introduced.

`e02-minimum-fixture-command-v3` has exactly schema, profileId, windowId,
operation, caseId (`minimum-two-role-rs`), ok, result and guardController: exactly
those eight keys in the retained whole controller stdout. guardController has
exactly schema (`e02-controller-guard-audit-v1`),reservationIndex (1..64),instance
(hex32),scope (`ACTUAL_NODE_CHILD_EVENTS_NOT_POPEN_ATTESTATION`),runId (hex32),
leaseSha256 (hex64),configurationSha256 (hex64),observations (array of exactly
{name,fields} rows). Parent ledger/slot/helper/current source/config/run/original
lease and actual command lifecycle must join. A service/probe audit uses a null
reservationIndex only in its own declared owner context; it is not a controller
capacity token. The intermediate service socket response lacks the controller's
own final audit and cannot substitute for retained command stdout. Failed replies
never qualify. `prepare.result.expected` is keyed by the exact role's stage IDs and
contains `{stage,rumor:Pin,content:Pin}` for each. A status names the current
stage/index and actual current subscription gate; a status alone is not receipt.
`FixtureCall.reply` is the same verified retained `command.stdout` Pin, not a second
RPC-proof file. Full raw stdout byte/hash equality, natural exit, both actual pipe
EOFs and the existing actual command reaping observation remain required. An extra
retained representation needs its full fresh debit; no proof is stripped.

`Stage = {id,index,oracle,dispatch,normalizedRole,identicalReplay,freshWrap,
requiresNewAppFrame}`, exactly the closed `stageSpec` outputs. Business incoming
has dispatch eligibilitytrue/roleincoming; harmless chatfalse/rolechat; every
archive stagefalse/rolearchive. These are validator eligibility results, never
measurements of NBDP handler effects.

Every publication requires a current actual app1059 `#p` account subscription
and same-generation EOSE before publishing. Bind raw REQ/EOSE, connection and
subscription IDs, request/EOSE sequences, before gate, forwarding/callback gates,
publication attempt epoch/stage, raw app EVENT and relay query. Replaced REQ,
CLOSE, reconnect or changed EOSE cannot reuse a stale generation. A fresh gate
after a between-stage reconnect is distinct; a change during an active attempt
refuses that attempt. A delayed prior callback cannot qualify a new attempt.

The three evidence origins are deliberately distinct:

1. Initial business, incoming chat and fresh-wrap replay **require a newly
   observed actual app socket frame** with current attempt/generation custody.
2. An identical archive event replay may be deduplicated by the relay. If no
   new app frame is observed in the bounded interval, record that absence,
   actual publication/OK, exact relay query and complete proxy history. No prior
   frame or synthesized EVENT/EOSE can fill this position.
3. In that duplicate case, native/JS validation can use the **actual relay query
   frame**, explicitly `ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME`. It establishes
   retained relay wire/role eligibility, not that Amethyst received or handled
   the identical outer twice. A fresh post-replay client GUI/export is still
   mandatory.

`e02-minimum-validated-wire-record-v2.origin` is exactly
`ACTUAL_APP_SOCKET_FRAME` or `ACTUAL_RELAY_QUERY_NO_NEW_APP_FRAME`;
`clientReceiptEstablished` must equal the first origin. Preserve native source
echo, exact native stdin/stdout/stderr, exit0/natural completion, independent
normalized JS/Rust results, frame/wire pins and the six-field frozen rumor join.
The associated `e02-minimum-transport-v2` cannot be passed to the old consumer as
an old-profile observation. A query-origin record is forbidden for any stage
whose `requiresNewAppFrame` istrue.

`e02-minimum-stage-publication-v2` binds profile/window/stage, attempt, intent,
gate, publicationWindow, actual publication, actual query and event, `actualNewAppFrameObserved`,
delivery ornull, validation, producerValidation, clientRetention,
validationOrigin and replayLimit. Forward/completion attempt and generation
fields are required on actual delivery; absence isnull, never a cached delivery.

For identical replay the complete outer event and serialized Nostr application
EVENT payload are identical; WebSocket connection/header/masking bytes need not
be. Fresh replay must have a different genuinely produced outer ID and the same
original inner rumor. In every archive stage the outer recipient isA while the
inner author remainsA and ordered private recipient tag remainsB.

## Actual GUI, attribution and client-origin exports

The fixed client/APK/helper/source/SDK/dependency pins, fresh own-account GUI and
saved/reopened TorOff evidence apply independently to each window. Decode the
actual nprofile GUI using a pinned reviewed decoder and join its resulting
pubkey to the expected role account. A declared account field or Known tab alone
is not account/attribution proof. The driver emits the actual profile GUI and
explicitly leaves independent decoding/review pending.

The incoming conversation is selected from New Requests; sender archive from
Known, as supported by pinned Amethyst source. Exact source-backed live selectors
remain **NOT_RUNTIME_VALIDATED** until actual use. Missing or ambiguous controls
refuse; there is no guessed coordinate or unknown-screen fallback. Voice calling
is an optional feature in the pinned source and is not a chat recognition gate.
Recognition requires the actual Back control, matching enabled Amethyst expected
note text and either the unique empty private Message composer or the exact
source-backed missing-recipient-DM-relays footer. That warning replaces the
composer in the pinned source; it is never sufficient without the known room
navigation/Back/actual expected note. The warning is read only and never clicked.
Both branches still require the actual selected-note export.
No composer is used to insert a fixture or trigger a business operation.

Every stage, including both replay stages, gets a fresh selected-note PNG/XML,
foreground helper CLEAR receipt, actual long-press/More Options/Copy raw JSON,
foreground helper CAPTURE receipt and helper-owned raw bytes. Case IDs are the
closed stage IDs, so exclusive helper files cannot overwrite an earlier stage.
Require focus, one text/plain item, sentinel/fresh timestamp custody and exact
byte count/SHA256. No expected JSON may enter clipboard/composer/helper intent,
no host clipboard synchronization and no Amethyst private-file extraction.

The raw client JSON must equal the frozen typed inner rumor in all six fields:
id, pubkey, created_at, kind, tags and content. UTF8 content and private tag order
are exact; no Unicode normalization/trim/reinterpretation. The only permitted
additional representation field is exactly `sig:""`; retain raw bytes unchanged
while excluding that empty representation field for semantic comparison.
Wrong conversation/author/recipient, missing or changed tags/content or any
other extra/signature field is negative evidence, not an ordinary UI limitation.

`e02-minimum-selection-v1` binds profile/window/observation/account/peer,
originalAuthor/originalOrderedTags/rumorId, action/method, helperPackage,
helperArtifact/receipt, capturedMonotonicNs, selectedGui,
matchingVisibleTextNodes and explicit limits. The actual inner bindings and
account GUI/wire lineage, not a display name alone, establish attribution.

On replay, preserve actual visible matching text-node positions/count and the
selected uniquely lowest match. An ambiguous equal position refuses. The source
does not claim these text nodes equal bubble counts. `duplicateObservation`
records the current viewport scope, visibleMatchingTextNodeCount,
globalDuplicateBubbleCount:null, globalDuplicateBubbleCountStatus:
`UNKNOWN_UNMEASURED`, and businessEffectsMeasured:false. No initialized zero
counter or dispatchfalse value establishes absence of business effects.

## Whole-run witnesses and future qualification boundary

`e02-minimum-role-driver-result-v2` contains exactly schema, profileId, windowId,
ordinaryRole, runId, runConfig, runRelease, executionState (`PARTIAL`),
accountIdentityGUI, expectedAccountPubkey, accountIdentityQualification,
torConfigurationGUI, environmentAnrEvidence, allUICaptures, fixtureCalls, observations, limits
and canonicalE02Changed:false. Each ordered observation contains id, state
(`EXPORTED_PENDING_INDEPENDENT_WHOLE_RUN_REVIEW`), selection, uiPng/uiXml,
rawClientRumor, clipboardClear, visibleMatchingTextNodeCount,
duplicateObservation, expectedRumor, publication, actualNewAppFrameObserved,
originalGuestToHostBindings, subscriptionStatus, subscriptionStatusReply,
subscriptionStatusCall, subscriptionStatusCommand and custodySegment.

A separately versioned root-owned consumer must also bind:

- adopted-method descriptor and exact author/source/configuration/membership;
- actual independent SOURCE/control acceptances, with byte-identical carry
  scopes explicit and changed controls actually rerun;
- fresh actual resource receipt (including coordinator>=8GiB output filesystem
  margin), exact original1800s grant/lease, complete clock/command/GUI history;
- actual fixed interpreter/argv launch and completion tool witnesses, raw streams,
  fields genuinely returned by that tool API, complete supervisor and all-four-owned
  cleanup/absence result. Original tool response objects may be persisted immediately
  by the coordinator. Process command journals separately provide their actual
  status/reap/EOF/force/error/time operands; neither journal nor tool receipt is
  relabelled as the other. No fabricated portable Popen attestation, source-constructor
  proof or unavailable API field is required. Preserve actual argv order and source bytes;
- complete attempt inventory and all failed/refused histories;
- actual nonauthor/nonoperator QA and security reviews of the **same whole
  window graph**, externally hash-bound with authentic agent-session provenance.

Approval-shaped JSON authored by the operator is not independent review.
A source fix, compiled module, exit0, assertion count, producer decrypt or partial
GUI step cannot qualify a failed whole window. The new aggregate and canonical
integration are root-owned next tasks, not implemented or approved here.
Canonical E02 remains PARTIAL until all applicable current ordinary and primary
criteria and reviewed integration are complete; the dependency gates and
architectural blockers remain unchanged. Ordinary JSON/chat UI understanding
does not assert invoice approval, payment capability or NBDP business dispatch.


## Current producer4 observer/allocation delta (SOURCE only; versioned consumer/completion separate)

This version refuses old profile/config/release/driver/fixture/transport/
publication DTO schemas. The raw wire/proxy schema intentionally remains
`e02-minimum-proxy-row-v1` with the exact original direction-specific fields.
The original Amethyst/helper/source custody and complete two-role requirements
above remain mandatory. New ordinary wraps come from the unchanged `T.wrap`
procedure; opaque diagnostic frames and old failed rows are never contributors.

`StagePublication` now additionally has exactly one `observation` object:

```text
ObservationRange = {schema:"e02-minimum-stage-observation-range-v2",
 phaseStartSequence:PositiveSafe, phaseEndSequence:PositiveSafe,
 proxyEndSequence:PositiveSafe, observer:ObserverState,
 phaseTracePath:"/session/fixtures/phase-trace.jsonl",
 proxyCapturePath:"/session/fixtures/capture.jsonl",
 streamPins:"FINAL_WHOLE_WINDOW_MEMBER_PINS_REQUIRED_NOT_MUTABLE_STAGE_PINS"}
ObserverState = {schema:"e02-minimum-observer-state-v3",
 budget:BudgetState,phase:PhaseWriterState,allocation:Allocation,
 serviceDiagnostics:ByteAccountState,serviceHeaderPrepaidBytes:4096}
Allocation = {total:16777216,service:8388608,serviceHeader:4096,
 serviceDiagnostics:4096,controllerSlots:64,slot:131072,proof:122880,
 ledger:4096,diagnostics:4096,wrapper:1024}
ByteAccountState = {limit:NonnegativeSafe,chargedBytes:NonnegativeSafe,
 intendedBytes:NonnegativeSafe,poisoned:boolean,firstError:null|string}
BudgetState = {schema:"e02-minimum-aggregate-capture-budget-v3",limit:8380416,
 intendedTotalBytes:NonnegativeSafe,acknowledgedTotalBytes:NonnegativeSafe,
 streams:{proxy:{intended:NonnegativeSafe,acknowledged:NonnegativeSafe},
          phase:{intended:NonnegativeSafe,acknowledged:NonnegativeSafe}},
 poisoned:boolean,firstError:null|string,physicalBytes:null,
 physicalMeaning:"ACKNOWLEDGED_PREFIX_IS_NOT_INDEPENDENT_PHYSICAL_ATTESTATION",
 lastAttempt:null|{stream:"proxy"|"phase",intendedBytes:NonnegativeSafe,
 writeInvoked:boolean,reportedCount:null|number|string,
 acknowledgedBytes:null|NonnegativeSafe,acknowledgedPrefixSha256:null|hex64,
 physicalBytes:null,error:null|string},allocationAccount:ByteAccountState}
PhaseWriterState = {sequence:NonnegativeSafe,intendedTotalBytes:NonnegativeSafe,
 acknowledgedTotalBytes:NonnegativeSafe,physicalBytes:null,
 physicalMeaning:"NOT_INDEPENDENTLY_MEASURED_ACKNOWLEDGED_PREFIX_IS_NOT_PHYSICAL_ATTESTATION",
 poisoned:boolean,firstError:null|string,lastAttempt:null|PhaseWriteAttempt}
PhaseWriteAttempt = {sequence:PositiveSafe,phase:string,
 intendedBytes:null|NonnegativeSafe,writeInvoked:boolean,
 reportedCount:null|number|string,acknowledgedBytes:null|NonnegativeSafe,
 acknowledgedPrefixBase64:null|string,physicalBytes:null,error:null|string}
```

The shared budget checks actual single-write returned counts. A zero/partial
returned count proves an acknowledged prefix only; a thrown write or invalid
count leaves its prefix UNKNOWN. No retry, repair, successful send/query or
successful stage follows a poisoned stream. The unchanged accepted phase writer
also has its own checked-count state; on a phase partial write its error string
can differ from the first shared-budget error. Consumer3 must require both
healthy for every contributor, not collapse the two states by string equality.
Per-stream acknowledged sums equal shared acknowledged total; shared intended
sum equals both stream intended sums. Successful exact stream bytes across the
whole service phase/proxy window are together <=8380416, never separate stream
allowances. Current production budget.allocationAccount is nonnull and its limit
is8380416; serviceDiagnostics.limit is4096. chargedBytes counts admitted intended
proof bytes, not physical bytes. It also includes startup staging and other
service proof files, so it need not equal phase/proxy acknowledged stream sums.
Rejected intendedBytes may exceed the cap; chargedBytes never does. All local
poison/first-error states remain independently relevant and no write is repaired.
The service/header/diagnostic/controller accounting is exactly
8388608+64*131072=16777216. Each controller slot is122880 proof+4096 ledger+4096
RPC diagnostics;1024 wrapper bytes are prepaid inside proof. Every attempted launch
is permanently reserved before inspect/spawn/first proof, including failures and
cancellations. Attempt65 refuses; success-only FixtureCall.ordinal is not the
reservation counter. The parent ledger is outside all fixture-writable mounts.
Early service audit memory and its later distinct phase encoding are both charged.
Proof/header/diagnostic failures fence locally and propagate through original
Root/Lease failure and cleanup; this is not an atomic cross-owner global fence. A stage
snapshot binds a trace prefix; it does not claim to seal later callbacks.
Complete late raw history is still mandatory. A failed whole window donates zero.

All phase rows use the accepted `e02-transport-query-phase-v2` common fields:
schema,sequence:PositiveSafe,utc:ISO-UTC,monotonicNanoseconds:canonical unsigned
decimal string,phase:string, plus current context profileId,windowId,ordinaryRole
and, for ordinary nonterminal rows, observedAttempt:Attempt|null. Allowlisted
terminalRetention:true rows below retain profileId/windowId/ordinaryRole but omit
observedAttempt; that absence cannot turn them into protocol/contribution rows. This is callback-time context, not a replacement
for raw forward/completion attempt and generation joins. Nanoseconds are process
monotonic observations, not host absolute int64Ns or measured CPU. Guard timing
is interpreted using the current enqueue/reply/consume fields, not CPU time or an
atomic cross-process check-to-effect claim. Early service guards are precharged
in immutable staging and their phase flush is charged again. Controller guards
are in the command.stdout guardController audit; they are not invented service
phase rows or Python Popen/waitpid attestations.

Additional phase-specific keys remain closed. For the new guard RPC/helper rows
and conditional consumed GUARD_EXIT fields, the current `guard-dto-contract.json`
and pinned guard client emitters are authoritative; the older two-field guard
observation declaration is superseded. Existing unchanged exchange/proxy rows
below retain their exact fields (absent conditional keys remain absent):

```text
GUARD_ENTRY: helperInstance:hex32,guardSequence:canonical unsigned decimal string,
 enqueueMonoNs:canonical unsigned decimal string,label:string
GUARD_EXIT: helperInstance:hex32,guardSequence:canonical unsigned decimal string,
 label:string,ok:boolean,error:null|string,consumed:boolean,
 consumedUtcUpperNs?:canonical unsigned decimal string,
 consumedMonoNs?:canonical unsigned decimal string,
 consumedBootUpperNs?:canonical unsigned decimal string
EXCHANGE_START: label
TIMER_ARMED: label,timeoutMilliseconds:10000
SEND_INTENT: label,eventId:hex64|null,rawBase64
SEND_INVOKE_ENTRY|SEND_INVOKE_RETURNED: label,eventId
SEND_CALLBACK_ENTRY: label,eventId,error:null|string
SEND_CALLBACK_GUARD_PASSED: label,eventId
SOCKET_OPEN_CALLBACK_ENTRY: label
RAW_BACKEND_CALLBACK_ENTRY: label,rawBase64
BACKEND_MESSAGE_GUARD_PASSED: label,messageType:string
SOCKET_ERROR_CALLBACK_ENTRY: label,error:string
SOCKET_CLOSE_CALLBACK_ENTRY: label
TIMER_FIRED: label,terminalRetention:true
EXCHANGE_RESOLVED: label,elapsedNanoseconds:null|Safe[0..1800000000000],error:null|string
EXCHANGE_REJECTED: label,elapsedNanoseconds:null|Safe[0..1800000000000],error:string,terminalRetention:true
PROXY_CONNECTION_CALLBACK_ENTRY: nextConnection:1..65
PROXY_SOCKET_OPEN_CALLBACK_ENTRY: connection,origin:"RELAY"
PROXY_RAW_CALLBACK_ENTRY: connection,origin:"APP"|"RELAY",rawBase64,binary:boolean
PROXY_SEND_INVOKE_ENTRY: connection,target:"APP"|"RELAY",bufferHash:hex64,bytes:Safe[0..262144],sourceSequence?:Seq
PROXY_SEND_INVOKE_RETURNED: connection,target,bufferHash,sourceSequence?:Seq
PROXY_SEND_CALLBACK_ENTRY: connection,target,bufferHash,error:null|string,sourceSequence?:Seq
PROXY_SEND_CALLBACK_COMPLETE: connection,target,bufferHash,sourceSequence?:Seq,sentSequence?:Seq
PROXY_SOCKET_ERROR_CALLBACK_ENTRY: connection:null|Safe[1..64],origin,error:string,terminalRetention:true
PROXY_SOCKET_CLOSE_CALLBACK_ENTRY: connection,origin
```

`connection` is1..64 on ordinary rows. A terminal socket-error denial fact may
carry null only if no connection identity was retained; it cannot establish an
accepted socket/frame lineage. sourceSequence is present exactly for APP-target callbacks
and joins the original RELAY_TO_APP row; APP completion additionally has
sentSequence joining APP_SOCKET_SEND_COMPLETE. RELAY-target send callbacks are
new observations only; they add no guard/protocol state/decode/forward action.
Raw backend phase entry precedes the original guard. The original
RELAY_TO_PRODUCER raw row still occurs after that guard and before strict JSON
parse. Raw-entry context when a guard refuses is refusal evidence only, never
accepted transport content. All known callbacks check terminal/fatal state;
late callbacks make no protocol writes/actions. The narrowly allowlisted
terminal facts below are bounded refusal/owned-cleanup retention only. The accepted exchange terminal path
settles once and attempts exact socket termination even if required retention
fails; known protocol/guard/socket error stays first and retention is secondary.

The phase trace includes original-label guard observations `original-unlabeled`,
fixed `proxy:*` positions and `exchange:<fixed label>:<original position>`.
Labels are source-defined and are not arbitrary authority or a substitute for
actual guard replies. No guard is memoized or omitted. Original exchange
positions remain entry/open/send-before/send-callback/backend-message. Original
proxy positions remain connection/app-message/before-upstream-send/upstream-open/
pending-before-send/upstream-message/before-app-send/app-send-callback. Whole
source diff and carry matrix bind the actual labels/positions precisely.


### Closed terminal retention after original service/helper failure

Current SOURCE4 first claims the original proxy/exchange socket, send or timeout
error, sets its local closed/firstFailure fence and cancels/fences its guard owner
and queued/inflight continuations BEFORE fallible error-clock sampling, phase,
outcome or queue work. Only these denial phases may follow that original claim:
PROXY_SOCKET_ERROR_CALLBACK_ENTRY, EXCHANGE_REJECTED and TIMER_FIRED, each marked
terminalRetention:true. Exchange's terminalPhase entrypoint accepts exactly the
latter two names; this is not a generic post-terminal writer. An error/timeout
fact is attempted only for its corresponding first original fault. Capture
short-write, ENOSPC or exhausted budget is secondary to that original error;
finishFatalCleanup still executes. No late protocol/send/GUARD_EXITsuccess,
retry/repair or additional capture allowance is introduced. The same single phase
writer and current8380416 proof budget own retention; no third stream is added.

Core onFatal runs before GUARD_TERMINAL observation. Known helper STDERR,
unexpected EOF, exit and close paths call bad(original) before fallible retention;
a later observation/cleanup error cannot replace that original first fault.
The other allowed post-fence phases remain exactly GUARD_TERMINAL,
GUARD_HELPER_STDERR, GUARD_HELPER_STDOUT_EOF, GUARD_HELPER_STDERR_EOF,
GUARD_HELPER_EXIT, GUARD_HELPER_CLOSE, GUARD_HELPER_TERMINATE and
GUARD_HELPER_CLEANUP_DEADLINE_EXHAUSTED. These are actual local denial/owned-helper
cleanup facts, not new guard success or portable reaping attestations. Once proof
streams are closed, no phase row is admitted. Missing refusal retention on a
failed sink stays missing; it never changes the failed whole-window outcome.

### Actual registered helper and service-control fault paths

Current production registerHelperTerminalCallbacks binds the owned child's stderr
`data`, stdout/stderr `end`, child `exit`/`close`/`error` and stdin `error` handlers.
Regressions dispatch those actual handlers through fake child/stream events and
the actual capture-budget/phase-writer functions. Naming six aliases which all
call the same retention helper/phase is not coverage of six production paths.
The guard-core DENY and service-control data/error paths likewise require their
actual production response/registered callbacks in separate current controls.

The private state records ended/stdoutEOF/stderrEOF/exitSeen/closeSeen from their
actual paths. Known stderr/unexpected-stdoutEOF/abnormal-exit/invalid-close faults
are claimed via bad(original) BEFORE framer/observation fallibility. On retention
failure the corresponding helper-stderr-retention/helper-stdout-eof-retention/
helper-exit-retention/helper-close-retention row is appended as exact {label,error}
secondary evidence, then bad(secondary) is notified without replacing the original.
Stderr EOF alone does not manufacture helper death. onClose executes in finally
after close retention; controller normal close cannot establish a separate helper's
EOF/exit/close history. No portable reaping or atomic process closure is claimed.

Each local helper/core secondary collection retains at most64 rows, with label
bounded to128 and error to2048 JavaScript string code units. This is a memory
bound, not a new diagnostic/capture allowance or a claim of an exhaustive global
error list after truncation. Combining local collections does not invent a shared
64-row global count. Every retained encoded representation remains within the
same adopted allocations and strict final observer union; no retry/repair/refund.

The actual service-control oversized-data callback creates CONTROL_REQUEST_BOUND,
claims/fences that original service/guard failure and only then calls the exact
owned socket.destroy. A throwing destroy becomes a bounded secondary row labelled
destroy-oversized-service-control; failure completion/owned cleanup still runs.
The original error cannot be displaced by destroy, short-write, ENOSPC or exhausted
retention. Late OK/callbacks cannot advance protocol actions or success evidence.
This correction adds no ordinary-success phase, general post-terminal writer,
worker/schema expansion, deadline extension or source/consumer gate waiver.

Exchange's additive `<label>-outcome.json` has exactly label,elapsedNanoseconds,
ack,received,eose,sentFrames,error:null|string,secondaryRetentionErrors:[{stage,
error:string}],observer:ObserverState. Required outcome retention failure rejects
the exchange even on an otherwise successful protocol path; it cannot yield a
stage. Outcome files may be missing on a failed sink; absence is preserved and
unqualified, never filled later. Actual successful `Exchange` result keeps the
unchanged ack/received/eose/sentFrames/elapsedNanoseconds object.

Future consumer3 must join the final two stream member Pins from the actual
whole-window inventory, per-stage observation ranges/states, actual command and
UI history, immutable sent/outcome operands, exact installed-tree sources and
actual nonauthor/nonoperator review origins. Complete original API response
objects are external tool receipts, not inferred fields in a child journal.
`observer-final-state.json` has exactly one of these two closed branches:

```text
FinalObserverFatal = {observer:ObserverState,
 snapshotTiming:"BEFORE_THIS_FINAL_RECORD_WRITE",error:NonemptyString,
 secondaryErrors:[{label:NonemptyString,error:string}]}
FinalObserverNormal = {observer:ObserverState,
 snapshotTiming:"BEFORE_THIS_FINAL_RECORD_WRITE",error:null,
 secondaryErrors:[],normalOwnedHelperClose:true}
```

Presence of the own normalOwnedHelperClose key selects the normal branch; its
value is literal true. False, unknown keys, wrong types, nonempty normal secondary
errors or any nonnull normal error refuse. A fatal record has no such key and
requires a nonempty error string: a fatal record plus a forged true/false flag is
not a normal record. Normal error:null without its true flag is also invalid.
Secondary fatal rows have exactly label/error strings, with nonempty label.

Both branches require the exact current six-key ObserverState/schema-v3 above.
All existing nested budget/phase/allocation/account domains, poison checks and
whole-history reader criteria remain mandatory; the envelope validator is not a
generic JSON or qualification relaxation. The literal snapshot marks counters
BEFORE the final record's own separately admitted write, not an after-write total.

The producer's actual normal and fatal paths use emitFinalObserverRecord with
kind normal/fatal. It builds the literal branch flags/keys, validates via
validateFinalObserverRecord, then invokes put("observer-final-state.json",value)
exactly once. Validation or put failure does not trigger a retry, repair or
positive fallback. Extraction validates the same closed record before reading its
observer; no manual field drop or normal/fatal coercion is allowed.

Normal output exists only after the actual owned helper orderly CLOSE path. Its
true flag establishes that limited local fact, not Python Popen/waitpid attestation,
a complete service/whole-window qualification or canonical promotion. Fatal
output is only actual delivered signal/failure retention. Missing output after
Docker removal or sink failure stays missing; never synthesize either branch.

Mandatory operation/controller end inventory checks and host post-cleanup check
remain real required source boundaries; raw file history is never silently
truncated to the last stage. Any actual final-state/error file must be consumed
and a poisoned/failed window refused. No current consumer2/completion1 pin may
be retargeted. They remain preserved; consumer3 then completion2 require separate
SOURCE definitions/reviews/controls and actual fresh qualified windows.
