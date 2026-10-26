# Before-install Android boot trace v1 — SOURCE ONLY

CPU4 diagnostic A and CPU8 diagnostic B both retained failure-only evidence of a
System UI ANR before the Amethyst activity intent. CPU8 is not an established fix
or causal explanation. This next diagnostic keeps B's exact container CPU quota8,
guest4vCPU/4096MiB RAM, container8192MiB memory=swap/PID512, software GPU, wiped
cold boot/no snapshot, pinned SDK/image/APK/dependencies/KVM and isolation.
Original A/B/ordinary sources and evidence remain unchanged. The current PR
checkpoint excludes this future prepared profile until reviewed.

This profile never installs the pinned APK/helper, never starts Amethyst, and
never types an identity, logs in, publishes, copies clipboard data or dismisses
an ANR. Cached APK/helper bytes remain inert pinned/read-only mounts for the
otherwise unchanged provenance/isolation configuration. Copied fixture/UI plans
are inert baseline inputs: this driver never consumes their identity/transport
paths and the fixture-operation API remains denied. The closed guard removes
install/pm/activity-start capabilities. No ADB root, kill-3, settings suppression
or generic shell/allow-failure path is introduced.

## Two bounded phases inside the original lease

The original1800s lease includes staging, all services, ADB wait, both trace
phases and the original boot wait. It is never renewed. Immediately after the
existing wait-for-device returns, one30s early phase captures guest uptime and
separate finite events/system logcat dumps with epoch formatting. This establishes
ordering before the boot-wait calls, not a claim that Android boot is incomplete.
The original240-step boot property loop then runs unchanged. After boot/namespace
qualification and build-property capture, one180s postboot phase collects the
before-install and five-second-later checkpoints. No APK installation or activity
intent occurs between checkpoints.

Each named phase has one original deadline stored in a ledger and cannot be
opened again. Removing the completed early phase's active cap allows the original
boot wait; it does not change that deadline or the shared lease. The postboot
phase has its own independently declared180s budget, never rebased at the late
checkpoint. Every nested command during either phase remains at most15s and
remaining phase time; ADB children remain10s and dumpsys receives5s. Original
ADB wait180s remains before the early phase. Captures stay8MiB stdout/256KiB
stderr. Full finite logcat buffers can exceed that bound: overflow fails and
retains the partial prefix instead of silently raising limits or using a tail.
These are source-owned finite controls, not hard realtime/hostile-host guarantees.

Postboot checkpoints retain raw UI XML/PNG, private-container cgroup metrics,
logcat events/system, uptime, lastanr, lastanr-traces, system_app_anr DropBox output,
PID/name process snapshot, cpuinfo/meminfo and the unchanged optional PSI reads.
Optional unsupported metrics remain UNKNOWN under their precommitted readers.
All new trace/logcat/process commands are mandatory: nonzero exit, timeout or
overflow keeps the first error, sticky revocation and visible partial capture;
no later guest action follows. Fixed early/postboot partial-journal paths cannot
overwrite one another or write arbitrary paths. Exact-owned cleanup is unchanged.

## Trace meaning and support limits

AOSP Android16r2 distinguishes `lastanr` task-manager state from `lastanr-traces`,
which reads the newest trace file. Their missing-state/file cases can both report
no ANR since boot, and newest does not establish a matching PID/time/cause.
[ATMS source](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-16.0.0_r2/services/core/java/com/android/server/wm/ActivityTaskManagerService.java),
Git blob `a0c38dd82037736359cccc616e40a3e9a31076de`, is inspection evidence only.

DropBox dumping checks dump/usage permissions, `--print` prints contents, and
`system_app_anr` is an exact tag filter. No entries, lost contents, disabled tags,
retention or rate limiting can omit information; they do not establish no ANR.
[DropBox source](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-16.0.0_r2/services/core/java/com/android/server/DropBoxManagerService.java),
blob `75b0fc24bea607b558d4d9b50fdee5acd8c35a16`, and
[AMS source](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-16.0.0_r2/services/core/java/com/android/server/am/ActivityManagerService.java),
blob `59c5e0e7fc2c4fe7f492a1018ee8819202836dfe`, do not prove target-image runtime
support or permissions. The exact commands still require execution and review.

The prepared stdout classifier recognizes explicit permission/unsupported/no-entry
or lost-content markers only as UNKNOWN dispositions. Otherwise it retains a
candidate-unmatched label; empty/non-UTF8 output also stays UNKNOWN. Raw stderr
must be reviewed separately. PID/reason/stack/matchingAnr and overall correlation
stay UNKNOWN, even for candidate traces. No PID or reason/stack is inferred from
a dialog title, ps name or focus-timeout text. Independent review must correlate
actual trace headers, timestamps, reason and stacks with the observed event, or
retain the evidence gap. Log availability can omit older events. No ANR visible
in a finite window remains UNKNOWN/DIAGNOSTIC_ONLY, not healthy OS or E02 PASS.

## Review and proposed controls

The preparation package archives all11 B source files, B source/control/runtime
acceptance and rejection history before new-profile edits. AST/hash comparisons
preserve original core lease/clock/lifecycle/ownership/cleanup, CPU/RAM/GPU/image
parameters and source/dependency checks. Only the declared new trace capability,
sequence, fixed journals and profile bindings change. No production data/keys,
new kind/NIP, architectural/blocker decision, Git/publication or deployment changes.

Proposed pure controls, NOT EXECUTED:

```
python3 -I -B experiments/prototypes/e02_android_boot_trace_v1/test_lease_guard.py
python3 -I -B experiments/prototypes/e02_android_boot_trace_v1/test_cleanup.py
python3 -I -B experiments/prototypes/e02_android_boot_trace_v1/test_diagnostic.py
```

Controls include bounded owned Python-child lifecycle and mocked data/files only,
never Android or transport. Earlier A/B source results are not transferred.
Independent QA/security exact source/config review, actual controls and independent
result acceptance precede a fresh `e02-android-boot-trace-release-v1` from root.
The private `/tmp/nbdp-e02-android-boot-trace-v1` parent/output must be fresh.
No actual diagnostic release or experiment is created/executed by this author.
No additional Product Owner input is required for the authorized source task.
