# API35 Lavapipe runtime R1 — userdata allocation failure

The root-operated finite run `50f907e3e77b4cff9137030fcaef1086` ended exit2,
`FAILED_UNQUALIFIED`, before guest ADB/early/postboot diagnostics. Its actual
live emulator stdout retains the original FATAL: not enough space to create the
userdata partition; available7326.61MB, need7372.80MB at the reported AVD path.
Units and decimal values are retained as emitted, without a GiB conversion.
The earlier broad emulator disk compatibility check printed OK, then this more
specific allocation check failed. Neither that OK nor host6GiB admission proves
enough space for every later emulator allocation.

The shared first revocation is `owned command exited unsuccessfully`.
The13 preceding Docker receipts completed naturally with exit0/reaped/full EOF;
receipt14 for wait-for-device records exit137, forced cancellation and sticky
revocation, with empty streams, reaped/full EOF and timedOut=false. These later
wrapper/ADB facts do not replace the emulator FATAL. No nested emulator receipt
or per-command elapsed sample was retained, so exact nested exit timing and the
reason for exit137 are not invented. Docker's final Android service state is
exited/ExitCode2/OOMKilled=false; that flag is not an independent RAM diagnosis.
All four exact-owned cleanup rows confirm identity and absence without errors.

The DATA-only archive copies100 files/234,625bytes:97 selected run members and
three preparation bindings. Every original/mirror path, length and SHA256 is in
`mirror-manifest.json`. It includes all14 receipts/28 raw streams, ownership,
lease/revocation, cleanup, actual final emulator stdout1265bytes/stderr0bytes,
the staged actual configuration and small AVD/config/launch text. Hardware QEMU
profile, namespace probes, guest properties, UI and early/postboot observations
are explicitly absent. Only Docker isolation/network-sharing inspect evidence
exists; guest loopback/listener qualification was not reached.

Actual inspect retains CPU8, memory=memory-swap8GiB, PID512, private cgroup,
read-only nonprivileged root and no published ports. Guest CPU4/RAM4096MiB and
API35/Lavapipe remain configuration values, not measured running-guest values.
The correct runtime-plan schema was checked directly against the staged config
and source validator AST. Actual issued release/config/source bindings are
preserved verbatim. Coordinator grant-preparation-history prose labels are not
copied or treated as facts; any correction belongs to its metadata owner.

No SDK, ZIP, image, key or APK was copied. Unselected mutable guest/ADB-key/lock,
mounted-input, Docker-config and relay DB contents remain excluded. This author
did not rerun, alter SDK/source/disk partition/reserve/timer, reclaim files, invoke
services or change shared/Git state. Root foreground74027 and chunksfa3729/1be1cc
are explicitly a parent-mailbox transcription, not this archiver's run.
The separate DATA archiver4f903d completed exit0.

This result establishes a preserved initialization/allocation failure, not an
API35 OS/ANR/client-compatibility observation, healthy baseline, causal fix or
ordinary-client row. Effective runtime renderer/vendor remains unqualified.
E02 and architectural blocker classes are unchanged. Next: independent actual
QA/security review, then a separate coordinator decision on bounded reclamation
and fresh context; this archive grants no retry or runtime authority.
