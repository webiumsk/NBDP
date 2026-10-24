# E02 ordinary-client supplementary evidence interface

SOURCE PREPARATION ONLY. No producer/consumer execution, Android control or
canonical result integration has been released by this file. The consumer never
writes `experiments/results` or returns canonical E02 PASS. A first complete
observation is useful PARTIAL evidence; all missing plan IDs stay visible.

This is a proposed concrete observation contract under the existing canonical
E02 criteria. The eight direction/role/relay rows are an explicitly reviewed
coverage proposal, not new protocol semantics. Real Android receipt authenticity
and UI/egress/process facts require actual independent QA/security observation
review; matching hashes or JSON approval words alone do not establish them.

## Descriptor and externally trusted operands

Every artifact descriptor is `{path, bytes, sha256}`. Paths must be absolute,
canonical regular files without symlink components. JSON/data are bounded16MiB;
source/APK hashing streams with a512MiB/file,2GiB aggregate and2048-file guard. No descriptor refresh is made
after drift. CLI operands supply the plan, capture and each actual independent
review path **and their independently known SHA256**. The coordinator checks the
consumer's reviewed source separately before invoking it. No JSON-supplied code,
function, path resolver, tool invocation or network endpoint is executed.

## Proposed plan object

`schema="e02-ordinary-plan-v1"`, `runId`, `operator`, `authors`, `client`,
`sources` (descriptor array), `prerequisites={E01:descriptor,E02:descriptor}`,
`runConfig` and `runRelease` (descriptors), `expected` (ordered rows).

The canonical E01 PASS140 and E02 PARTIAL22 records remain unmodified. Their
recorded source/config/lock pins and recorded Rust executable hash must still
match the actual files. This is provenance rechecking, not a new E01 execution;
actual fresh received-wire requests/results are separate observation inputs.

`client={commit,apk,package,versionName,versionCode}` pins Amethyst
`e6f464a1179def75274512b3c5bab921de3bf3d8`, its cached165860063-byte APK
`5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5`,
package `com.vitorpamplona.amethyst.debug`, version `1.17.0-DEBUG`/462.

Each expected row is `{id,direction,role,relay,account,peer,rumor,visibleToken,dispatch}`:

- `direction`: `js-to-rust` or `rust-to-js`.
- `role`: `incoming` or `archive`; `relay`: `strfry` or `rs-relay`.
- `account`/`peer`: actual disposable hex public identities in the app.
- `rumor`: descriptor of the frozen expected unsigned inner kind14 rumor.
- `visibleToken`: nonempty unique substring in that rumor's exact content that
  must appear in the actual selected-note UI hierarchy.
- `dispatch`: true for the independent adapter incoming envelope validation,
  false for archive. It does not assert an Amethyst business feature exists.

Freeze the full agreed matrix. The initial runtime capture may contain one row;
it remains PARTIAL with seven missing rows. Expected originals are comparison
oracles only. A separately decrypted producer fixture cannot stand in for the
actual client's retained inner rumor.

## Proposed capture object

`schema="e02-ordinary-capture-v1"`, `runId`, `operator`, `plan` (descriptor),
`client` (identical to plan), `executionState` (`COMPLETE`, `PARTIAL`, `FAILED`
or `NOT_EXECUTED`), `runConfig`, `runRelease`, `driverReceipt`
(descriptor), `observations` (ordered subset of plan IDs).

Each observation is `{id,status,transport,selection,uiPng,uiXml,rawClientRumor,error}`.
`status` is `COMPLETE`, `PARTIAL` or `FAILED`; each artifact is a descriptor or
null, and `error` is null or a bounded diagnostic string. A COMPLETE row needs
every artifact and null error. Failed observations are retained as FAIL, never
converted into qualified success or silently omitted. A PARTIAL row cannot
satisfy the corresponding expected ID.

`transport` describes a JSON object:

```
{schema:"e02-ordinary-transport-v1",frame,wire,jsRequest,rustRequest,jsResult,rustResult}
```

All six values are descriptors. `frame` is the actual relay-delivered
`["EVENT", subscriptionId, outerEvent]`; `wire` is the exact outer-event JSON
passed to both validators. The parsed wire must match the received frame event.
Actual independent JS and Rust result files must be equal successful validation
objects whose retained rumor exactly equals the plan rumor, role and dispatch.
Both saved request objects are exactly `{op:"validate",wire,secret,role,expectedSender}`,
where `wire` is the exact UTF8 wire artifact string and `secret` is only the
public disposable scalar1/2 matching the planned account. The JS wrapper uses
these same operands for the existing JS validator; Rust consumes its exact RPC
request. Request bytes are saved before invoking their fixed validators.
Their command/input custody is part of the pinned driver's receipt and
actual independent review; this consumer does not re-execute crypto to manufacture
delivery evidence.

`selection` describes a JSON object:

```
{schema:"e02-ordinary-selection-v1",observationId,account,peer,rumorId,
 action:"COPY_RAW_JSON",method:"ANDROID_LOCAL_FOREGROUND",
 helperPackage,helperArtifact,helperReceipt,capturedMonotonicNs}
```

`helperArtifact` is a descriptor of the exact reviewed Android-local helper APK.
`helperReceipt` pins the guest CAPTURED receipt and its case ID, MIME, raw byte
count/hash, guest elapsed clock, foregroundFocus, wallClockMillis,
clipboardItemCount and clipboardTimestamp. Guest elapsed and host monotonic clocks are
different domains and are never compared as absolute timestamps.
The capture driver must use actual selected-note Copy Raw JSON, foreground
ClipboardManager text access and exact UTF8 output; no URI coercion, host
clipboard synchronization, fixture replacement or public composer. The helper
package and APK must match the fresh run configuration checked by actual review.
`rawClientRumor` contains that selected client's exported inner JSON. Its original
bytes and descriptor remain unchanged. Pretty JSON formatting can differ. The
client-export-only normalizer accepts exactly the six canonical unsigned rumor
fields (`id`, `pubkey`, `created_at`, `kind`, `tags`, `content`), optionally plus
`sig` whose value must be the empty string. It rejects a nonempty, null or
nonstring `sig` and all other extra fields. After removing only that empty
signature representation, all six fields, types, ordered tags and exact content
must match; the NIP01 rumor ID is recomputed. The pinned client's
`EventSerializer.kt` always serializes `sig`, while `EventDeserializer.kt`
defaults it to `""`; this is source inspection, not an observed runtime export.
Expected rumors and JS/Rust validated rumors remain closed six-field objects;
the client-export normalization does not apply to them or the received wire.

`uiPng` is actual screencap PNG; `uiXml` is the actual corresponding settled
Android hierarchy. Their sequence/timing/selected note is reviewed, not assumed
atomic. Minimal magic/root/token checks are data consistency only, not image
authenticity or proof of runtime capture.

`driverReceipt` is pinned, bounded JSON with matching `runId`, `runConfig` and
`runRelease` referents. Other driver-specific fields remain opaque to this compact
consumer and are inspected by actual independent reviewers, including real input
requests, guest/package identity, UI action order, egress, lease and cleanup.

## Actual observation review and integration boundary

Each externally pinned independent review uses
`schema="e02-ordinary-observation-review-v1"`, `role`, `session`,
`decision="ACCEPT_ORDINARY_CLIENT_OBSERVATIONS_ONLY"`, `plan`, `subject`
(exact capture descriptor), `acceptedObservationIds` (exact captured IDs),
`findings=[]`. Two distinct qa/security sessions must be outside plan authors
and operator. This accepts evidence quality, including an honest PARTIAL/FAIL
observation; it is not a claim all mandatory outcomes passed.

Output is `MATCHED_SUPPLEMENT_ONLY`, `PARTIAL`, `NOT_EXECUTED`, `FAIL` or
`QUALIFICATION_REFUSED`, always `canonicalE02Changed=false`. A capture header of
`PARTIAL` retains that outcome even when all eight rows match; a recorded failure
still takes precedence as FAIL. Missing rows or unexecuted scope prevent complete
supplemental matching. Canonical E02 remains
PARTIAL until a separately reviewed integration consumes genuine qualified
supplement and reruns/reconciles all required current adapter/control criteria.
The old unconditional mandatory Amethyst skip is not altered by this prototype.

Synthetic test fixtures exercise data refusals only. Their fake receipts/reviews
are explicitly CONTROL_FIXTURE objects, never real Android observations or
ordinary-client interoperability evidence.
