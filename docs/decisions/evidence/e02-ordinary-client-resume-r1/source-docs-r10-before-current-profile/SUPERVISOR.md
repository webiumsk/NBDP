# E02 finite supervisor preparation

This is source preparation, not a launch release. `supervisor.py` implements the
fixed first cell and a separate config-materialization mode. The current R2 source
requires fresh independent review. Root ran the original R1 four pure controls
successfully; its preserved [record](../../../docs/decisions/evidence/e02-ordinary-client-resume-r1/guard-r1-inert/execution.json)
does not qualify changed R2 source. No tests or runtime were executed by this author.

The existing ingress HIGH expired-action finding and v7 startup negative remain
history. Freed disk does not close either finding. The new lease has immutable
original UTC, MONOTONIC and BOOTTIME deadlines, includes all setup, has a sticky
revoke marker and observes before/after dispatch and continuously while waiting.
There is no shared clock flock across a child. Process-group cancellation occurs
only while the direct child remains unreaped under WNOWAIT ownership; no numeric
group signal follows a consuming wait. Cleanup while the host cannot execute is
not promised. Already dispatched Android/native work is not atomically cancelled.

The in-container guard accepts only fixed synthetic ADB operations, the fixed
helper component/case identifier, and read-only `ss`/`ip` metadata probes. It does
not accept arbitrary shell, URI reads or expected clipboard content. Amethyst's
fixed `/artifact.apk` installation has a180s command ceiling, other ADB commands
30s, read-only probes10s, all within the original total lease. No new deadline is
issued after READY. Expired/revoked result bytes can be retained as raw evidence
but cannot become accepted observations.

The four original `test_lease_guard.py` cases are nominal dispatch, already
expired zero payload, expiration during a simulated wait withholding its result
and later payload, and explicit revocation during a simulated wait. They use a
private temporary directory and a callable sentinel. R2 adds clock rollback and
resumption controls plus bounded owned local Python children: natural exit/EOF,
timeout, capture overflow, nonzero exit and a post-reap expiry with zero signals.
Failure tests require durable revocation before cancellation and zero later
payloads. No Docker/ADB/emulator or host-clock changes occur in these controls.
Actual independent source review and later root-authorized execution remain
required. They are not Android/native race or hostile-host tests.

## Fixed integration and reviewable invocation

The fixed `android_driver.py::run(runtime)` uses `runtime.check()`,
`sleep(seconds)`, `adb(tokens, timeout) -> bytes`, `snapshot(unique_name)` returning
PNG/XML descriptors, `fixture(prepare|status|publish) -> bytes`, and exclusive
`put_bytes`/`put_json` under `runtime.out`. ADB tokens omit the supplied fixed
`-s emulator-5554`. No generic exec or arbitrary shell interface is exposed.

The first scope is JS-to-Rust/peer-incoming/public scalar2/nostr-rs-relay only.
The selected actual inner kind14 note must be exported through Amethyst Copy raw
JSON and the separately built foreground helper. One cell remains PARTIAL.

After source review, root may materialize a fresh configuration (this preparation
command issues no lease and starts no services):

```text
python3 -B supervisor.py --materialize /tmp/nbdp-e02-ordinary-client-v1/run-config.json --run-id <fresh32hex> --seconds 1800
```

The separate externally pinned root release is JSON with schema
`e02-first-cell-release-v1`, `executionAuthorized:true`, the exact `runId`,
`scope`, `runConfig` descriptor, integer `notAfterUtcNs`, and descriptors
`qaReview`, `securityReview`, `guardRegressionEvidence`. A config materialization
or a file merely named release is not independent acceptance. Root creates the
release only after actual reviews and controls have accepted that exact graph.
The single foreground invocation is:

```text
python3 -B supervisor.py --config <absolute-config> --config-sha <sha256> --release <absolute-release> --release-sha <sha256> --out /tmp/nbdp-e02-ordinary-client-v1/runs/<fresh32hex>
```

No execution is released by these example commands. The root foreground tool
must remain supervised/polled; stopping it requires exact-owned cleanup and
retained results. `supervisor-result.json` records raw failure or scoped PARTIAL,
never canonical PASS. `driver-result.json` exists only after the full fixed cell.

The supervisor R2 cleanup amendment preserves the raw driver result and earliest
primary error. Any cleanup diagnostic error, failed removal or uncertain exact-CID
absence produces `FAILED_UNQUALIFIED` and nonzero exit. A final result-write
failure also returns nonzero and emits the failure through the supervised stderr.
Cleanup first proves immutable CID/name/run/role/creation-nonce/image ownership.
It then independently attempts diagnostics, exact-CID removal and absence
inspection. Log/write failures and failed runtime isolation cannot prevent removal
of an already proven owned container; a foreign identity is never removed.
Docker creation uses `--pull=never` with the fixed cached image IDs.

`test_cleanup.py` prepares eight mocked controls for diagnostic-write/size errors,
isolation mismatch, foreign nonce refusal, failed removal/outer failure, uncertain
rows, final evidence-write failure and inert module initialization at
`/input/supervisor.py`. These controls do not execute Docker, Android or native
experiments. Their source and actual results require independent review. The
guest import path uses a fixed host-only checkout constant so module initialization
does not index nonexistent ancestors of `/input`.

Fixture worker owns fixed `fixture.mjs serve|prepare|status|publish`, read-only
`/input/fixture-plan.json`, writable `/session/fixtures`, proxy17777→RS8080, and
actual app-subscription/EOSE/delivery plus independent JS/Rust validation. It uses
`lease_guard.py check SHA` with external `NBDP_LEASE_SHA256` instead of duplicating
clock arithmetic in Node. Plan/metadata nanoseconds are Python integer metadata,
not Nostr safe-integer fields; Node should treat the lease file as opaque bytes.

Fresh launch must first verify actual source/helper/APK/tool/image/dependency
pins and independent reviews, recheck6GiB disk/12GiB MemAvailable, then issue one
lease before any Docker action. Containers have exact immutable IDs and fresh
nonce labels; no host network, Docker socket, published ports or personal mounts.
Android6GiB/swap6GiB/PID512/CPU2, guest2048MiB. Other services join the exact owned
network-none namespace and communicate only through its loopback.

Cached emulator help proves `-ports5554,5555` disables implicit gRPC unless
explicitly requested. Use `-no-window`, no grpc/grpc-ui option, no DISPLAY,
WAYLAND_DISPLAY, DBUS, XAUTHORITY or GUI/auth/socket mount. Retain actual private
namespace listener inspection; do not invent an unsupported `-no-clipboard` flag.

The old v7 image may supply tools, but its consumed grant/launch/source authority
does not authorize this new workload. The fixed runtime plan stays `ready:false`
until the supervisor, driver/fixture, helper artifact, actual pins, precise
configuration, guard tests and independent review/release are complete.
