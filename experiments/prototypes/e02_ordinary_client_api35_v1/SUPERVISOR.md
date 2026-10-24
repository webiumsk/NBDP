# API35 ordinary-client source profile: preparation only

This directory is a SOURCE-only derivative of the original current R11 ordinary
first-cell sources. The authoritative proposed configuration and complete source
subject are in `docs/decisions/evidence/e02-ordinary-api35-preparation-r1/`.
No tests or Android/runtime actions have been executed for this profile, and no
release or lease has been issued. Independent SOURCE QA/security, actual current
controls and independent review of those controls precede any exact root release.

Only declared profile data changes: private run namespace, profile-specific
runtime/release/result schemas, accepted isolated API35 SDK/inventory, Android35
AVD target, Lavapipe renderer, Android container CPU8 and host affinity>=8.
Guest4CPU/4096MiB, container memory/swap8192MiB, PID512, original1800s lease,
original requested2048M data partition, pinned images/APKs and all safety logic
remain unchanged. Emulator37.2.12/platform-tools37.0.1 are the same copied410
inventory rows. The acquired API35 OS fixture is a whole environment change;
this profile is a semantic readiness candidate, not a causal comparison.

The strict current R11 driver remains byte-identical: require actual password
state and whole unmasked public synthetic NSEC, actual reopened TorOff PNG,
bounded known Settings/SystemUI Wait-only<=2 recovery, and refuse unknown or
Quickstep dialogs. No added never-ANR prerequisite and no broadened handling.
Only the first JS-to-Rust incoming rsrelay cell is prepared; all other seven
producer matrix cells and canonical integration remain undone. One successful
cell cannot promote E02 to PASS or close architectural blockers.

The original requested2048M partition and source6GiB free-disk floor remain
unchanged. Requested2048M does not prove a2GB footprint: all seven retained
ordinary hardware-qemu.ini files normalized disk.dataPartition.size to6g.
The separate API35 no-install emulator failed before guest/ADB: available
7326.61MB, required7372.80MB. This supports no guest OS failure inference.
Before any ordinary grant the coordinator requires fresh measured>=8GiB free
on the actual output filesystem. This is a conservative admission margin,
not a measured minimum or boot/readiness guarantee, and does not lower or
replace the source6GiB floor. Hash-bound prerequisite DATA:
`docs/decisions/evidence/e02-ordinary-api35-preparation-r1/coordinator-resource-prerequisite.json`
SHA256 `e836f9de2a50de2dc36c024cf1638de1aac681f0ab8f14052d13a4594c00abc8`.
Only two verified disposable old overlays are being reclaimed by the coordinator;
the reported~9.49GB target is not this author's fresh resource measurement.
Boot/client compatibility remain UNKNOWN. Preserve first failures; no cached
snapshot substitution, blanket healthy-OS gate or broadened dialog handling.

The copied helper build files are historical source provenance only; this
profile reuses the exact already pinned helper APK and does not authorize a new
helper build. The original runtime instructions below are historical context;
their original paths/schema names do not activate this API35 profile.

---

# E02 finite foreground supervisor

This prototype implements one JS-to-Rust peer-incoming control on nostr-rs-relay using the pinned Amethyst APK and public scalar2 account. A completed cell remains scoped PARTIAL. It cannot remove canonical E02's mandatory skip, establish the wider eight-cell matrix or authorize native E06/production work.

The initial R2 preparation notes and their original resource/profile claims are preserved byte-for-byte in [the historical snapshot](../../../docs/decisions/evidence/e02-ordinary-client-resume-r1/source-docs-r10-before-current-profile/SUPERVISOR.md). Use the actual versioned source/configuration reviews, releases and run receipts for current authority; this document grants no execution.

## Current resource and isolation profile

The reviewed headroom trial configures Android with 4 vCPU and 4096 MiB guest RAM, inside a container capped at 8192 MiB memory, memory-swap of 8192 MiB, a CPU quota of 4 and 512 PIDs. Equal memory/swap caps permit no additional swap allocation. Other role limits are unchanged; configured aggregate memory maxima are 9856 MiB (9.625 GiB). Admission requires effective host affinity at least 4, MemAvailable at least 12 GiB and persistent free disk at least 6 GiB before issuing a lease.

These are configuration ceilings and admission guards, not measured peaks, proven minimum requirements or an ANR diagnosis. Actual Docker inspections verify the fixed resource and ownership values. Earlier attempts used guest2048 MiB/2 vCPU and container6144 MiB/CPU 2; their failures remain history.

Every container has an exact immutable CID and fresh run/role/creation-nonce labels. Creation uses cached image IDs with `--pull=never`, dropped capabilities, no-new-privileges, read-only source mounts and fixed owned writable state. Only Android receives the KVM device. There is no host network, published host port, Docker socket, personal directory or GUI/auth socket mount. Services share the exact owned network-none anchor namespace.

Before installing APKs or touching the UI, the supervisor captures and validates actual `ip -j addr`: exactly one loopback interface with typed LOOPBACK flags and numeric host-scope loopback addresses. It then validates actual five-column `ss -H -lnt` rows. Numeric loopback and IPv4-mapped loopback endpoints may use valid ports; wildcard exceptions are only the fixed relay port 8080 forms. This classifies reachability inside the private namespace. It does not attribute every listener to a service or prove emulator APIs disabled.

The pinned emulator runs with `-ports 5554,5555`, `-no-window`, no explicit grpc/grpc-ui options and no DISPLAY/WAYLAND/DBUS/XAUTHORITY environment or host desktop mounts. Headless mode/options alone do not prove absence of internal gRPC or clipboard APIs. The experiment deliberately uses Android's guest clipboard through a foreground helper. Do not invent an unsupported `-no-clipboard` option or claim all clipboard APIs are disabled.

## Immutable lease and owned cleanup

The original UTC, MONOTONIC and BOOTTIME 1800 s lease includes setup and is never renewed after READY. Each fresh clock sample validates boot/time-namespace metadata before a tight clock-only bracket, with at most three 50 ms candidates. Metadata latency remains charged against original expiry, rollback, drift and 15 s observation-gap checks. This assumes the reviewed capability/no-setns path and no privileged-host adversary; it is not hostile-host or hard realtime protection.

Checks surround each action and continue while owned commands run. A refusal persists sticky revocation before cancellation. Process-group signals occur only while the direct child remains retained under WNOWAIT ownership; no numeric group signal follows a consuming wait. Already dispatched work is not atomically cancelled, and cleanup while the host cannot execute is not promised. Historical ingress HIGH findings are not globally closed by these controls.

Cleanup first proves exact CID/name/run/role/creation-nonce/image ownership, then independently attempts diagnostics, exact-CID removal and absence inspection. Diagnostic or isolation failure cannot prevent removal of a proven owned resource; foreign identities are not removed. Uncertain cleanup, failed retention or removal produces FAILED_UNQUALIFIED/nonzero while retaining the first error and raw driver evidence. Guest service failure bytes are forwarded when available; missing buffered logs do not establish an emulator root cause.

## Fixed observation and command surface

`android_driver.run(runtime)` uses only guarded check/sleep/ADB/snapshot, fixed fixture prepare/status/publish and exclusive bounded output writes. No arbitrary shell, URI reader, generic exec or expected clipboard content is exposed. ADB targets the fixed disposable emulator. Initial wait-for-device and pinned Amethyst installation have 180 s ceilings; other allowed ADB commands use 30 s, read-only probes 10 s, all within the original lease.

Known Tor and Android Settings/SystemUI ANR dialogs have exact bounded recognition during login. Only regular-connection selection or Wait is allowed respectively. Every before/after frame is retained; persistent/unknown dialogs refuse, and OS health remains UNKNOWN after Wait. The driver explicitly selects Off, saves, reopens settings and preserves PNG/XML. XML does not expose the spinner value, so independent visual inspection of the reopened PNG must verify saved Off before accepting that configuration.

Only fixed public disposable identity/relay inputs enter the app. Whole intended login text must be observed before submission. Actual current app REQ/EOSE generation must qualify before publication. Retain the forwarded EVENT/query and actual independent JS/Rust request/reply evidence. Select the rendered note, clear the guest clipboard, use Copy raw JSON and extract the foreground helper's private receipt/raw bytes through the fixed run-as operation. Expected JSON must never be supplied to the helper or clipboard. Preserve exact captured bytes and typed rumor/tag comparison; the pinned serializer's empty unsigned `sig` is the only documented normalization.

## Reviews, controls and invocation

Source-only controls cover lease refusal/ownership, namespace/resource configuration and mocked UI behavior. They are distinct preparation scopes; their counts must not be pooled into E02 assertions or represented as real client observations. Source inspection, APK build/installation, boot and a screenshot alone do not qualify the ordinary-client control. The current versioned readiness record names the actual executed control/source pins.

After independent review, config materialization writes metadata only:

```text
python3 -I -B supervisor.py --materialize <fresh-absolute-config> --run-id <fresh32hex> --seconds 1800
```

Materialization starts no lease, Docker or device. A separate root release must bind exact runId/scope/configuration, integer notAfterUtcNs and actual QA/security/control-evidence descriptors. Verify fresh APK/helper/SDK/bundle/dependency/image/source pins and resource admission before activation.

```text
python3 -I -B supervisor.py --config <absolute-config> --config-sha <sha256> --release <absolute-release> --release-sha <sha256> --out /tmp/nbdp-e02-ordinary-client-v1/runs/<fresh32hex>
```

Keep the foreground controller supervised and retain natural exit, raw streams, supervisor/driver results and exact-owned cleanup. A consumed grant/output cannot be reused. `supervisor-result.json` reports raw failure or scoped PARTIAL, never canonical PASS; `driver-result.json` exists only after the complete fixed cell. Further cells require a separately reviewed versioned procedure and evidence integration; no runtime authority comes from a plan or this README.
