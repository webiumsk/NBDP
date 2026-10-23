# Android health diagnostic v1 — SOURCE ONLY

This is a separately versioned diagnostic after nine unqualified E02 setup/UI
attempts. It is not an ordinary-client control, interoperability result or a new
canonical experiment. The pinned Amethyst/API36/emulator and cold-boot software
GPU/resource profile remain the same. Existing source and negative evidence are
unchanged. Preparation does not authorize activation.

The diagnostic observes baseline state, sends exactly one activity intent and
collects immediate and later read-only evidence. The exact activity is unchanged,
but `am start -n` intentionally omits `-W`: its result means INTENT_DISPATCHED
only. It does not measure full startup duration or establish readiness. There is
no identity input, login, fixture operation, clipboard operation, ANR dismissal,
GPU change, snapshot, resource increase or background retry.

## Finite scope

The inherited original1800s lease includes setup and is never renewed. A distinct
180s monotonic diagnostic phase begins after installation; every nested Docker
command during that phase is capped at15s and remaining original phase time.
Diagnostic ADB children have a10s ceiling, dumpsys receives its own5s option, and
original boot/install180s ceilings remain before that phase. Captures retain the
inherited8MiB stdout/256KiB stderr bounds. Actual timestamps and command receipts
are required. These source-owned timers are not hard realtime/hostile-host proof.

The four original owned roles, exact immutable images/APKs/dependency inventories,
KVM, no-network anchor/shared loopback namespace, read-only mounts/cap-drop,
no-new-privileges, exact ownership and removal/absence checks remain. The helper
APK remains pinned/mounted as an inert baseline input but is not installed or
invoked. There is no ADB reverse. Android stays4vCPU/4GiB guest RAM and8GiB
container memory=swap; aggregate configured memory is9856MiB. Admission retains
6GiB disk/12GiB MemAvailable and affinity4. These are caps/thresholds, not measured
minimum/peak usage or an ANR diagnosis.

The only container configuration delta is explicit `--cgroupns private`, verified
as actual HostConfig.CgroupnsMode=private with no CgroupParent. The optional fixed
cgroup reader additionally requires self `0::/` and one read-only cgroup2 root
mount. It reads only cpu.stat, memory.events and memory.current at that private
root. Missing/denied/unsupported state is UNKNOWN, not a host-path fallback.
These values describe the entire Android container, including emulator/ADB/guard
activity, not the emulator process alone. Snapshots are sequential, not atomic.

## Captures and failure semantics

Before/after the one intent: fixed system/events logcat tail1000, dumpsys lastanr
and cpuinfo, guest /proc/meminfo, optional CPU/memory/I/O PSI and raw UI XML/PNG.
A five-second later logcat/lastanr/UI observation is attempted only inside the
same original180s budget. No later phase extends or resets the deadline. A slow
command can leave a partial prefix; missing suffixes are visible and are not
healthy observations.

Exactly three immutable literal optional PSI scripts accept no interpolation,
path or caller text. They emit explicit UNAVAILABLE or READ_FAILED with the
original read exit. The lease checks and output bounds still enclose them.
Mandatory command failures retain the first error and sticky revocation; no guest
commands run after revocation. A bounded fixed own partial journal can still be
written as evidence, following the inherited command-retention pattern.

Observed ANR titles never authorize an action. The first is retained as
ENVIRONMENT_FAILURE while read-only diagnostics continue before final revocation
and cleanup. Supervisor exit2/FAILED_UNQUALIFIED preserves that outcome. A complete
capture without a visible ANR is DIAGNOSTIC_ONLY with environmentStatus UNKNOWN;
it is not a healthy-OS PASS. CAPTURED means bytes were obtained, not that a service
supports the command, a metric is meaningful or no ANR exists. Independent raw
review determines what the logs actually establish. No ordinary-client row can
be donated by this run under either outcome.

## Review and proposed commands

The evidence preparation directory records byte-identical originals, unified
diffs, AST-only invariants, proposed fresh config and complete source subjects.
There are no project imports, tests, Docker operations or root releases by the
author. Independent QA/security must review source/config and separately released
controls before a fresh root diagnostic-only release can activate anything.

Proposed controls, NOT EXECUTED:

```
python3 -I -B experiments/prototypes/e02_android_health_v1/test_lease_guard.py
python3 -I -B experiments/prototypes/e02_android_health_v1/test_cleanup.py
python3 -I -B experiments/prototypes/e02_android_health_v1/test_diagnostic.py
```

The first suites include bounded owned Python-child lifecycle controls and mocked
cleanup, never Android/transport. Mock diagnostic outputs are DATA only. Proposed
runtime invocation is the new supervisor with exact prepared config hash, a fresh
`e02-android-health-release-v1` hash and absent fixed output directory. The root
must create the private `/tmp/nbdp-e02-android-health-v1` preparation parent before
using its runs directory. A prior E02 first-cell release has the wrong schema and
scope and cannot authorize this diagnostic.

## Source-readiness correction r2

Independent source review rejected r1 before activation: Runtime.adb inherited a
30s default while diagnostic getprop/UI children have a10s ceiling. The default is
now10s, matching the unchanged exact guard ceiling; boot/install keep their
explicit180s calls. No10s/15s bound is increased. New controls call the actual
Runtime.adb setup getprop/fingerprint paths with only owned dispatch mocked.

Additional controls call the actual private-cgroup reader over fixed mocked proc,
mount and cgroup bytes. They cover a valid private read-only cgroup2 root,
nonroot-self/writable/wrong-root/non-cgroup2/duplicate-mount refusal before metric
reads, optional metric failure, fixed paths and propagation of sticky lease
refusal. These are proposed DATA controls, not actual container observations or a
reproduced vulnerability. R1 sources/config/rejections remain immutable in the r2
pre-mutation archive. All new controls still require independent review and
separately authorized actual execution.
