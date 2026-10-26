# Android health CPU8 quota trial B — SOURCE ONLY

This is one separately reviewed configuration trial after the CPU4 diagnostic A.
The only experimental runtime variable changes the Android Docker container CPU
quota from4 to8. Host affinity admission correspondingly requires at least8 CPUs.
The Android guest still has4vCPU/4096MiB RAM. Container memory=swap8192MiB,
PID512, private cgroup, software GPU, image/API/SDK/APK/dependencies, wiped cold
boot/no snapshot, commands, timing and cleanup remain unchanged. The host CPU
quota is not guest-vCPU count, guaranteed scheduling or measured utilization.

The new source directory, private lab path, configuration/release/result schemas,
source pins and fresh identity distinguish B. Generic diagnostic observation scope
is unchanged, so the original guard/driver and29/19 suites remain byte-identical.
The24 cleanup/profile controls bind quota8/affinity8, reject otherwise identical
quota4/7/9 snapshots, and still require guest4vCPU and the unchanged memory limits.
A previous A or ordinary-client release cannot authorize B's exact new config.

## Original A evidence and uncertainty

The preserved A diagnostic reported System UI ANR already in its baseline UI,
before the Amethyst activity intent; the same modal remained in immediate/later
UI. Root and independent reviewers assessed those saved observations. The
[original A runtime package](../../../docs/decisions/evidence/e02-android-health-runtime-r1/)
and its measured-deltas record remain unchanged. Preparation archives their exact
metadata pins and original source copies; these are historical evidence, not B
execution or authority.

A's two private-cgroup samples were21.117398468s apart. They recorded64.6465
CPU-seconds and72 throttled periods out of211 scheduling periods. Those counts
are not a percentage of CPU time lost; throttled_usec is not direct wall time or
ANR causation. Memory.current was5401452544 then5434445824 bytes and the sampled
memory-event deltas were zero. This does not exclude all memory pressure or
measure a peak. Guest PSI was unavailable; lastanr reported none despite the
visible System UI ANR. The cause remains UNRESOLVED. These describe the entire
owned Android container, including emulator/ADB/guard, not the emulator alone.

A→B is a single-variable configuration comparison of fresh sequential cold
boots. Host load, scheduling and boot nondeterminism are not controlled by this
change. A single B observation cannot establish causation, a stable minimum CPU
requirement, healthy OS, or ordinary-client compatibility. Repetition or another
variable requires a separately reviewed next task; no automatic retry is added.

## Preserved diagnostic boundaries

No identity input, login, clipboard, fixture operation, ANR dismissal, GPU change,
snapshot or memory increase is permitted. One pinned activity intent via
`am start -n` without `-W` means INTENT_DISPATCHED only; it supplies no startup
readiness/duration claim. The helper APK remains inert/pinned/mounted and is not
installed or invoked. No ADB reverse is configured. Four owned roles retain the
same isolated loopback/no-egress network and exact image/mount/creation-nonce
checks; cleanup removes only exact-owned IDs and independently checks absence.

Original1800s lease includes setup, with no renewal. The same180s diagnostic
phase observes before/immediate/later system/events logcat tails, lastanr,
cpuinfo, meminfo, optional PSI/private-cgroup and UI XML/PNG. Diagnostic nested
commands stay at most15s/remaining phase time and ADB children10s; explicit
boot/install180s ceilings remain before the phase. Captures retain8MiB stdout
and256KiB stderr bounds. These are finite source-owned controls, not hard
realtime/hostile-host guarantees. Disk6GiB/MemAvailable12GiB admission and total
configured9856MiB memory are unchanged thresholds/caps, not measured minima.

Exactly fixed optional PSI scripts and private read-only cgroup2-root validation
remain unchanged. Missing/denied/unsupported metrics are UNKNOWN with raw
sentinels/original read exits; no host-cgroup path fallback is allowed. CAPTURED
means bytes, not supported metrics or absence of an ANR. Mandatory failures keep
first error/sticky revocation; only bounded own evidence retention/cleanup can
follow, with no later guest action. An observed ANR remains ENVIRONMENT_FAILURE;
no visible ANR in the finite window remains UNKNOWN/DIAGNOSTIC_ONLY. Neither
outcome supplies an ordinary-client matrix row or canonical E02 PASS.

## Required review and proposed controls

The preparation package preserves11 A source files before B edits, original A
source/config/control acceptance and runtime metadata, unified diff and AST/hash
invariants. This author performs source/data preparation only: no project import,
test, service, Android or transport invocation and no release/approval creation.

Proposed controls, NOT EXECUTED for B:

```
python3 -I -B experiments/prototypes/e02_android_health_cpu8_v1/test_lease_guard.py
python3 -I -B experiments/prototypes/e02_android_health_cpu8_v1/test_cleanup.py
python3 -I -B experiments/prototypes/e02_android_health_cpu8_v1/test_diagnostic.py
```

These are29 guard/24 mocked cleanup-profile/19 diagnostic definitions. Guard
controls include bounded owned Python-child lifecycle; none is Android/transport
or an E02 assertion. Earlier source-identical results do not become current B
runtime evidence. Independent QA/security source/config review, actual reviewed
controls and independent result acceptance precede a fresh exact
`e02-android-health-cpu8-release-v1` from root. Root must create the private
`/tmp/nbdp-e02-android-health-cpu8-v1` preparation parent and absent run directory
according to the execution plan. No Product Owner input is needed for this
already authorized isolated trial preparation.
