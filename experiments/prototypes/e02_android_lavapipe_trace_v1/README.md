# Lavapipe before-install trace v1 — source preparation

This separate diagnostic-only profile copies the accepted boot-trace source and
changes the requested renderer from `swiftshader_indirect` to `lavapipe` in both
the emulator argv and AVD config. Its namespace, scope, schemas and future release
are distinct. The baseline files, negative runs and canonical E02 remain intact.
This author ran no tests, Android, services, imports or experiment. Independent
source review, actual pure controls, their independent review and a new exact
root release are required before activation.

The emulator/image/SDK pins, guest4vCPU/4096MiB, containerCPU8/8192MiB with equal
memory-swap and PID512, headless cold wipe/no-snapshot, KVM, private namespaces,
closed egress, admission6GiB disk/12GiB MemAvailable/affinity8, original1800s lease,
early30s/postboot180s phases and nested command10s/outer15s remain unchanged.
There is no install, activity intent, identity/login, clipboard, publication or
UI recovery. Uiautomator remains mandatory with its original10s child deadline;
unknown ANR titles and all mandatory command failures remain refusals.

## Live emulator evidence

The old service forwarded captured child bytes only after exit, so forced Docker
removal could lose emulator logs. This profile adds one exact existing-run
`session/fixtures` RW bind to the Android container. Only the exact immutable
Lavapipe emulator argv may request internal `emulator_capture=True` in
`Lease.run_checked`. All other callers retain the default behavior.

The guard opens only `/session/fixtures/emulator.stdout` and `emulator.stderr`:
no path input, no symlink following, exclusive creation, regular single-link
owned files with0600 mode in a private0700 directory. It writes/fsyncs acquired
chunks before the child exits. The unchanged in-memory stdout8MiB/stderr256KiB
bounds also bound each spool. Overflow, create/write/fsync/close error or child
failure keeps the first error, revokes the original lease and uses existing
owned-child cancellation/reaping. Secondary spool-close errors cannot replace
an earlier failure. File/fsync scheduling is not hard realtime or hostile-host
attestation. The shared disposable fixture directory is trusted experiment
infrastructure, not a cryptographic custody boundary.

After the existing trace/metrics prefix and before uiautomator, the coordinator
reads the two fixed owned regular0600 file prefixes through no-follow directory
FDs, within15s and the original active180s phase. It freezes the size observed at
each open; growth afterwards is omitted explicitly. A truncated/over-cap/missing
or invalid file fails with sticky revocation. Raw prefixes persist in the bind
even if no UI or final diagnostic result is obtained. The driver also captures
exact mandatory read-only `logcat -b main -d -v epoch` and
`dumpsys -t 5 SurfaceFlinger` at this point. Unsupported/permission text or empty
successful output is evidence of unknown availability; a nonzero exit, timeout
or overflow is still a mandatory failure. No allow-failure wrapper is added.

## Interpretation and proposed controls

The requested renderer is `lavapipe`; effective backend and vendor remain
UNKNOWN pending actual raw review. CLI/config, cached library names and a source
claim do not establish the loaded renderer. Readiness requires actual emulator
backend initialization plus a coherent runtime GLES/vendor/renderer report;
main/SurfaceFlinger output corroborates rather than replaces the raw backend
record. Explicit fallback, incomplete identity or conflicting outputs remain
UNKNOWN/FAIL as applicable. Historical effective backend is UNKNOWN, so this is
an alternative environment-readiness trial, not a causal A/B proof or a fix.
An absent ANR in a limited window does not establish health. No ordinary-client
rendering, business compatibility, E02 PASS or blocker closure follows.

Prepared pure suites:29 original guard controls,24 cleanup/profile controls
(one directory fixture adapted for the new exact mount),28 diagnostic DATA/AST
controls (new prefix stub/scope/closed allowlist binding), and11 additional
Lavapipe/spool controls. The latter map the fixed emulator argv only inside a
mock Popen to a bounded owned Python child; no Android execution is implied.
They exercise live prefixes before child exit, both stream overflows, original
write/fsync and secondary-close faults, exclusive/private paths, fixed argv,
default-off behavior, actual bounded prefix reader and unchanged resource caps.
The source-only static AST/diff report is not evidence these controls passed.
