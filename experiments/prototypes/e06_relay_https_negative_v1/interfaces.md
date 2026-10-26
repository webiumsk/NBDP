# Closed negative-lane private interface freeze

**Inert design only; no callable implementation or execution authority.**
Scope/order/constants are exactly contract.json, profile.json and selection-map.json.
This isolated derivative changes the shape of `eligibility`; I4's accepted grammar,
sources and capability maps remain unchanged. The dependent bridge freeze encodes
these definitions with a separate worker projection; the coordinator owns the
28 whole-step oracles. Full checker expected objects/bindings never enter workers.

## Ownership and process boundaries

One parent owns isolated relay lab setup/cleanup, sequential case admission and
outer case monitoring. One fresh case process owns all private context, receive,
native-channel, orphan/authenticated-pair, local-policy and seal-refusal registries.
Each N02/N16 case owns exactly one persistent native child, one request and reply;
N03 owns none. Relay wire children are completed sequentially before native start.
No parallel case, restart, reset, later event, retry or fallback is accepted.

Future executable derivative modules must use fixed local imports of the SAME new
negative protocol module instance. Accepted M wire/helper/protocol sources are
read-only source bases, not invocable wrappers accepting new case IDs. Explicitly
review derivative binding/import/case-regex/record changes. Never import M protocol
to mint N capabilities, use import-query resets, copy handles between instances,
accept caller-selected modules/commands, or treat controller JSON as authority.
No acquisition/consumer/browser module is needed or may be imported for this lane.
Unchanged native JS/Rust carrier metadata implementations are usable only under
later admitted exact tool/source bindings; no project import is released here.

Private opaque handles never cross a pipe. Descriptor/report JSON is evidence
only. Context registry identity, owned ChildProcess/pipe observation, fixed source
closure and actual EVENT spans establish source-local custody under the admitted
same-UID workflow, not cryptographic hostile-host attestation.

## Records and common types

All described records are closed: every listed key is mandatory, extras refuse,
native types are exact and no coercion/repair occurs. Descriptor is exactly
`{path,bytes,sha256}`: absolute canonical regular file, safe nonnegative integer,
lowercase64-hex SHA-256, current byte/hash match, no aliases/symlinks. Source
closure entries can describe large binaries; inert data reads and evidence packs
retain their separate profile bounds. Strict UTF-8/scalars, decoded duplicate-key
refusal and safe integer tokens apply before parsing. Raw JSONL has one terminal
LF per message. Owned directories0700, files0600, fresh exclusive writes only.

Every sidecar below binds `cellId` and `windowId` to the exact selected cell;
canonical `stepId` is a template identifier, unique together with cellId. The
23-key observation need not add identity keys: its enclosing case reply, selected
descriptor path `<output>/<cellId>/<stepId>.json` and artifact graph bind identity.
Every referenced record must belong to the same private context; a matching JSON
identifier alone grants nothing.

An owned receive record retains fixed cell/window/slot/relay/subscription/outer ID,
spawn receipt and report descriptors, actual RECEIVE EVENT frame/span offsets and
span descriptor, one publication/query/EVENT, Close1000 and empty close reason.
Require exact publication/ACK/REQ/EVENT/EOSE/CLOSE order, six frames, whole outer
event equality plus actual original EVENT object span equality. All stdout/stderr,
natural exit0/reap/EOF/unforced lifecycle and finite limits must join the owned
child before a receive handle is minted. Uncertain partial attempts are retained.

Native call record keys are exactly
`{schema,cellId,windowId,backend,ordinal,channelReceipt,request,reply,dReceive,
fReceive,replyObserved,channelAlive,pendingOutputBytes,terminalLifecycle}`;
schema=`n02316-native-call-v1`, ordinal=0, backend=selected JS/RUST, replyObserved=true,
channelAlive=true, pendingOutputBytes=0 and terminalLifecycle=null at response.
Request/reply/channel receipt are descriptors. dReceive=null only N02; fReceive
always describes the same actual received F. Later terminal evidence is separate;
do not mutate the original response record. Retain complete raw reply before
shape/authentication/post-integrity checks, including on failure. JS retained
native-reply sidecar must equal owned stdout bytes. A forged record is not a handle.

The native request keeps exactly five keys `op,secretHex,config,dWireHex,fWireHex`.
Native config is the accepted fixed six-key scope with enabled=true. Actual span
hex supplies both wires for N16; only N02 has dWireHex=null. F is never null.
N03 has no native request/record/expected/channel/terminal child, not an empty or
synthetic response. Full backend-native replies keep all13 original top-level
keys and every nested native value; never add local policy fields. N02's D absence
is `dSource=ABSENT`, `dRumorId=null`, `validation.D=null`, not a wrapper with a null
rawReply. Source candidates in native-oracles.json require actual qualification.
N16 must first observe exact paired CORRELATED/ASSOCIATION/EXACT_D_F_METADATA/
ONE_CANONICAL_F and D1/F1, derive subject from actual authenticated nested native
facts, and match the existing full expected object in the separate checker.

`localPolicy` sidecar keys are exactly
`{schema,cellId,windowId,stepId,nativeCall,dRumorId,fRumorId,scope,decision,
permitted,reason,boundary}`. Values: schema=`n02316-local-policy-v1`,
stepId=N16-S02, nativeCall=same own paired native-call descriptor, canonical IDs
from that actual paired authentication, scope=`ATTACHMENT_ACQUISITION_ONLY`,
decision=`DENY`, permitted=false, reason=`LOCAL_ACQUISITION_PERMISSION_DENIED`,
boundary=`AFTER_PAIRED_NATIVE_AUTH`. Record only after genuine paired auth; no
native disabled-config shortcut. Policy state is UNDECIDED through N16-S01.
No ALLOW state/handle exists in this lane. This is not business-invoice approval.

`sealRefusal` sidecar keys are exactly
`{schema,cellId,windowId,stepId,nativeCall,localPolicy,outcome,stage,reason,
generation,attemptReservation}`. Values: schema=`n02316-seal-refusal-v1`,
stepId=N16-S03, same nativeCall and immutable localPolicy descriptors,
outcome=`REFUSED`, stage=`policy`, reason=`LOCAL_ACQUISITION_PERMISSION_DENIED`,
generation=null, attemptReservation=null. Mint a private refusal handle only when
an actual serial source-local seal gate receives its own authenticated pair and
its own DENY handle and refuses specifically for that policy. Caller-supplied
false, generic thrown errors or foreign handles do not qualify. Never mint a
generation or reservation and then discard it to manufacture zero evidence.

`eligibility` in each whole observation is exactly
`{state,localPolicy,sealRefusal}`. State values are in contract.json's transition
table: N03 INCOMPLETE_NOT_AUTHENTICATED, N02 INCOMPLETE_ORPHAN,
N16-S01 AUTHENTICATED_POLICY_UNDECIDED, N16-S02 onward DENIED. Both pointers are
null for all N02/N03. N16 localPolicy is null at S01 then the same descriptor
through terminal; sealRefusal null until S03 then the same descriptor through
terminal. Failure state UNKNOWN retains earlier real pointers when available.
None of these states is an eligible permission to acquire bytes.

`terminal` sidecar keys are exactly
`{schema,cellId,windowId,stepId,wireTerminals,metadataTerminal,localPolicy,
sealRefusal,noCall,cleanupQualified,sourceCurrent,inputsCurrent,evidenceComplete}`.
Schema=`n02316-terminal-v1`; stepId is the selected final step. wireTerminals is
closed `{D,F}` with owned terminal-receipt descriptors/null per selected slots;
metadataTerminal is the same owned one-request channel terminal descriptor for
N02/N16 and null for N03. Policy/refusal pointers equal eligibility's pointers.
noCall is closed `{generations,reservations,httpsListeners,httpsServers,
acquisitionClients,acquisitionConnections,httpGets,receivedEntityBytes,
consumerCalls,browserLaunches,originalReleases}` with each value0 for qualification.
The four trailing flags must be true. This zero record requires actual same-case
entry ledger/current-source/no-call joins and resource ownership evidence; it is
not a caller assertion or proof of no work elsewhere on the host.

Native terminal receipt must bind the same owned channel/tool/argv/environment,
full stdin/request and stdout/reply streams, empty stderr, natural exit0/reaped/
both EOF, no force/timeout/error and exactly one consumed reply with no extra
pending output. N03 records metadata NOT_STARTED; it does not fabricate a terminal
receipt. No seal/generation/private-consumer prerequisite is required for this
new negative terminal operation. All wire children must already be terminal.

## Future private operations and exact scheduling

These signatures are design contracts only:

| Operation | Preconditions and result |
| --- | --- |
| loadCaseContext(framePath,externalSHA) → ctx | Fresh output, exact N lane/cell/closure/current prerequisites/reviews and external release before dependent imports/spawns. Reject I4, mixed/unknown cases, unsupported cardinalities and unresolved artifacts. Root later freezes frame/manifest/release schemas; this freeze supplies none. |
| runOwnedWire(ctx,slot) → received | Only next declared slot; complete observed provenance above. No fixture buffer substitution. |
| startNative(ctx) → channel | N02/N16 only; one fixed selected admitted backend, no pending output, fixed scope and one-request bound. |
| authenticateFOnly(ctx,fReceived) → orphan | N02 only, same owned channel and actual F span; preserve complete native reply and native F authentication. Orphan never becomes paired-subject authority. |
| authenticatePair(ctx,dReceived,fReceived) → auth | N16 only; fresh native full paired authentication/projection, canonical IDs/parent/URL/descriptor/scope equality. Native enabled=true. |
| recordLocalDeny(ctx,auth) → deny | N16-S02 only, own auth/current pins and one completed request, immutable sidecar above. No arbitrary supplied permission or scope mutation. |
| attemptSealRefusal(ctx,auth,deny) → refusal | N16-S03 only, exact completed declared frontier, no pending work/current pins/owned live quiescent native channel; serial policy gate refuses. Expected negative result, no generation/reservation. |
| closeNativeForNegative(ctx) → terminalReceipt | N02-S02 or N16-S04 only; close stdin once and require exact qualified native terminal. N03 must reject this call before spawn/work. |
| closeoutNoSeal(ctx) → finalStepDescriptor | Declared terminal only; same orphan for N02, D receive only N03, auth+deny+refusal N16; owned terminal cleanup, actual no-call joins and full current integrity before synchronous final publication. No generation/private result arguments or consumer success required. |
| retainFailure(ctx,error,boundary) → unqualifiedCase | Retain earliest raw primary error, partial streams/counters, separate bounded secondary diagnostics and bounded owned cleanup; later steps NOT_EXECUTED/EARLIER_FAILURE. No conversion of arbitrary errors into qualified negatives. |

N02-S01 comprises receive F → native start → one F-only native call; S02 closes
that channel and publishes no-seal terminal. N03-S01 receives D only; S02 checks
terminal without starting metadata. N16-S01 comprises receive D → receive F →
native start → paired auth; S02 denies locally, S03 attempts/refuses seal, S04
closes metadata and publishes terminal. Sidecars retain suboperation order within
each observation. No additional whole step or hidden request is introduced.

All23 top-level observation keys are contract.closedStepKeys, exactly once.
TransitionTable supplies exact phase/decision/status/stage/reason/state values.
eventProvenance is closed `{D,F}` descriptors/null, metadataRecord is own call/null,
associationState follows the table and constantStepFields remain exact null/false/0.
At every completed step, counts equal its selected cell.completedStepCounts;
terminal cleanup changes no work count. Before a complete observation, attempted
but uncertain work sets affected counters null, preserving earlier measured facts.
Verified non-entry paths stay0 only while source/entry/ownership evidence supports
them. UNKNOWN never becomes0 to meet an oracle. Metadata decryption work is not
attachment encryption and is not hidden by a zero consumer count.

Whole lifecycle remains closed `{wireD,wireF,metadataChannel,metadataTerminal,
caseHostPID,caseOuterReap}`. Wire pointers are last actual owned receipts/null.
metadataChannel is NOT_STARTED (N03), ALIVE_QUIESCENT (N02/N16 before terminal),
TERMINAL_QUALIFIED at qualified terminal or UNKNOWN on uncertainty. Actual case
PID or null is captured, never predicted; caseOuterReap=null until independent
parent evidence outside case output. Cleanup remains closed
`{relayWireChildren,https,consumer,metadata,problems}`: wire children QUALIFIED on
completed steps, HTTPS/consumer NOT_STARTED, metadata NOT_STARTED/ALIVE_QUIESCENT/
QUALIFIED per branch, empty problems for qualification. Integrity is exactly
`{sourceCurrent,inputsCurrent,evidenceComplete}`; completed qualified steps require
true/true/true, while failures retain actual true/false/null observations.

Final case reply keys are exactly `{schema,cellId,windowId,qualified,stepRecords,
notExecuted,finalObservation,metadataTerminal,terminal,caseCleanupQualified,
finalIntegrity,error}`; schema=`n02316-case-cli-reply-v1`. Qualified negative means
all selected steps and their whole observations match, terminal graph/current
integrity/owned cleanup qualify, notExecuted=[], error=null and actual observed
zero prohibited entries; it never means acquired bytes or application success.
On failure qualified=false, finalIntegrity/caseCleanupQualified reflect actual
checks, finalObservation=null, and unexecuted steps remain explicit. Do not reuse
I4's seven-step success/failure writer or generic nonzero-exit negative acceptance.

Root's exact inert-bundle acceptance must bind these closed definitions, the
deterministic worker-schemas.json projection, stopped native-oracle/whole-oracle
files, independent reviews and unchanged protected originals. BRIDGE.md defines
the checker/worker separation; source-only candidate headers do not waive later
actual native qualification.
Independent QA/security reviews, separately assigned implementation, native-oracle
qualification, controls/configuration/admission and distinct primary/QA releases
remain required. No design author approves its own security finding.
