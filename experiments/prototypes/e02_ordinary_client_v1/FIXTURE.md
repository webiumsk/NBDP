# First-cell fixture and app-bound transport observer

SOURCE PREPARATION ONLY. No source in this directory grants execution. Independent source/configuration review and an exact fresh root release are required. Canonical E02 remains PARTIAL22.

## Fixed API and scope

Run `node /input/fixture.mjs serve` as the owned fixture service; `prepare`, `status`, and `publish` are the only client commands. They use a private0600 Unix socket at `/session/fixtures/control.sock`. The fixed immutable plan is `/input/fixture-plan.json`, externally SHA-bound by `NBDP_FIXTURE_PLAN_SHA256`. The shared immutable `/session/lease.json` and `NBDP_LEASE_SHA256` are enforced by the supervisor-owned `lease_guard.py` through the pinned guard interpreter before actions/callbacks and after waits. No shared clock lock is held across children.

The first slice is JS scalar1→Rust validator / ordinary Amethyst scalar2 incoming, rs-relay only, canonical envelope n10. No accounting effect or NBDP business implementation is introduced. Both peer and sender-archive wraps are constructed and published, but only the incoming ordinary-client cell is observed; archive client retention is not claimed.

The WebSocket proxy binds127.0.0.1:17777 and forwards only to127.0.0.1:8080 in the owned network-none namespace. Only Amethyst uses the proxy; producer publications and validation queries use the backend directly. Actual message payload bytes are retained as base64 with connection/direction/sequence. These are application-frame payloads, not raw TCP/WebSocket header/mask captures.

## Preparation and publication

`prepare` writes fresh immutable `expected.json` and `prepared.json` using the unchanged canonical JS transport builder and publishes signed kind10050 inbox records. `status` requires a currently active app kind1059/pRecipient subscription whose filters cover the peer wrap timestamp and whose EOSE arrived on the same connection/subscription. Replacement REQ, CLOSE, CLOSED and connection closure invalidate prior state.

`publish` has one attempt, persists its intent, checks the current gate and original finite lease, and then publishes the prepared wraps. It requires app-bound peer EVENT forwarding and socket-send completion under the original active connection/subscription/REQ-sequence/EOSE-sequence generation. Both observations and the final relay-query join use the same generation predicate. A matching REQ replacement, CLOSE, CLOSED or connection closure permanently invalidates the attempt and clears its delivery candidate, even if the same IDs obtain another EOSE. Actual capture rows and the publication record retain forwarding/completion generations. It queries the actual relay event and joins those objects. Relay ACK alone is insufficient. A completed socket send is not by itself app receipt or retention; actual GUI and Android-local selected-note export remain mandatory.

## Received-wire validators and consumer contract

`frame.json` contains the actual app-bound EVENT payload. `wire.json` is serialization of its actual outer object and is the exact string fed to both validators. Actual relay-queried outer data must agree. `js-request.json`, `rust-request.json`, `js-result.json`, and `rust-result.json` expose the closed `e02-ordinary-transport-v1` descriptor wrapper in `consumer-transport.json`.

The JS function is the unchanged canonical `transport.mjs`. The pinned original Rust executable must echo the current source before returning validation; actual stdin/stdout/stderr, exit/signal and normalized result are retained. Binary hashes match the canonical candidate record; this is not a new build. Fixture original is an expectation oracle only, never substituted for actual app-bound wire input or client export.

Required read-only mounts: original canonical `transport.mjs`→`/input/transport.mjs`; original `experiments/node_modules`→`/input/node_modules`; canonical Rust binary→`/input/nbdp-experiment-rust`; Rust source→`/input/rust-source.rs`; canonical E01/E02 records and package lock at their fixed plan paths. Do not mount the whole repository, personal credentials or Docker socket. The fixture plan pins every installed regular dependency file used in the read-only node_modules mount. .bin symlink launchers are not executed; no lockfile-only installed-code provenance claim is made. The external configuration review must bind that exact tree and mount.

## Limits and controls

`test_fixture.mjs` contains14 pure metadata filter/state controls,10 pure generation controls and3 source-shape assertions; executing it is a separately authorized source-control check, not an ordinary-client or relay experiment. Generation controls distinguish the unchanged original from replacement REQ with/without EOSE, changed EOSE, inactive/closed and wrong-ID cases. The source assertions check the direct dynamic import, its function-type guard and absence of the unavailable adapter export; they do not evaluate the installed crypto API. No crypto/native/network operation occurs merely by importing `fixture.mjs`; actual source evaluation waits for review. Guarding is cooperative, not a hard realtime or suspended-host cleanup guarantee. Current source uses synchronous guarded native validation with an8s limit; complete native errors remain unqualified.

Unknown/missing subscription, late result, drift, capture truncation, bad native result or absent real-client inner export must remain failed/unqualified or PARTIAL; never fill from fixture bytes. The one positive cell cannot establish the complete direction/role/relay/replay/negative matrix or canonical E02 PASS. No new kind/NIP, SDK, profile adoption or blocker closure.

## R2 source remediation

R1 source inspection found that `prepared()` called `transport.verifyEvent`, although the unchanged canonical adapter imports that function internally without exporting it. No runtime failure was observed. R2 imports `verifyEvent` directly from the same pinned `nostr-tools/pure` installed tree inside `main()`, after the original lease, plan, dependency and source gates, checks its function type and uses it on freshly parsed prepared wraps. The canonical shared adapter and fixture plan remain unchanged. This corrects a static API mismatch only; installed API evaluation, cryptographic verification and actual-client retention remain unexecuted until independent review and release.

## R3 source remediation

Independent R2 security review found that a replacement REQ reusing the same connection/subscription IDs could qualify against the old publication gate. This was a source-level generation-custody finding, not an observed runtime exploit. R3 binds the actual EVENT forwarding, send callback and final join to the original request and EOSE sequence values, retains both observed generations and permanently invalidates affected publication attempts on subscription/connection closure or replacement. The original frame/query/JS/Rust validation and lease checks are retained. The prepared pure controls have not been executed; independent exact-delta review remains required before any execution.
