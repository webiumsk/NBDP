# Minimum incoming query timeout — bounded read-only diagnosis

The preserved whole incoming window is FAILED_UNQUALIFIED and contributes zero
ordinary rows. Raw receipt0360 uses **exit:2**, reapedtrue, forcedfalse,
timedOutfalse, errornull and both EOFtrue. Its51-byte stderr is
`Error: FIXTURE_COMMAND_FAILED:Error: RELAY_TIMEOUT`. The separate command-error
record names RELAY_TIMEOUT. Sticky revocation/FINITE_LEASE_DENIED and subsequent
service exits follow that failed command; they are secondary. Original1800s lease
still had roughly1331s at the command-error filename timestamp. All four owned
containers have actual identity/remove/absence cleanup evidence.

Before the failure: actual account/login/Tor/one Feeds-collapse/Local-relay GUI
steps and subscription/EOSE were retained. Sequence49 is relay OKtrue for the
published business outer. Sequence50 is its actual APP EVENT with current
connection1/subscription mghfqw/request10/EOSE21,51 completes forwarding and52
seals actualNewAppFrameObservedtrue. That proves scoped wire forwarding, not
Amethyst decryption, selected rendering, private tag retention or business effects.
No GUI capture after publication, selected-note export, independent native
validation record or complete stage publication exists.

The failure is later: sequence56 retains the exact112-byte REQ with the published
outer ID and limit1. Source logs it BEFORE ws.send. No query reply is recorded;
no failed-exchange send callback or phase timing object is persisted. Therefore
backend receipt, actual reply absence, socket-send completion and timer-start
instant remain UNKNOWN. The10s query timer expired, not the parent55s command
ceiling or original30-minute lease.

Two source-supported hypotheses remain unproven. First, repeated synchronous
Python guard checks share the Node loop with open/send/message/watchdog/timer
callbacks. Observed unrelated APP REQ/EOSE callbacks continue between query intent
and error, but their timestamps are post-guard log times and cannot measure
kernel arrival, individual guard duration or CPU cause. Second, the pinned relay
has a >5s queued DB load-shed branch that omits normal EOSE. No operational relay
logs/DB queue timings establish that branch. Captured relay stdout is empty;
stderr is only later sticky revocation. Configured cgroup limits/OOMKilledfalse
are not CPU/RSS/PSI/guest-health measurements. Neither a relay bug, CPU shortage
nor Amethyst business incompatibility is established.

No functional assertion/deadline/profile fix is justified yet. In particular,
do not lengthen/restart the10s timer, remove the exact query, donate early rows,
relax EOSE/current generation/export, increase resources or retry the same cold
Android attempt without a reviewed evidence plan. A source-only observability
revision is justified: bounded monotonic phase records for exchange start,
open, guard entry/exit, send invocation/callback, raw backend callback entry,
timer firing and rejected outcome. Preserve exact raw operands and original
10s/3s/55s/1800s limits. A callback-entry evidence write before a guard may record
refusal context only; it must authorize no forwarding or action after failure.
Keep such records in a separately versioned diagnostic schema/profile so the
old strict consumer is not silently retargeted. Relay-specific bounded logging
would need reviewed configuration/guard environment handling and actual retained
logs, never assumed availability.

The smallest next runtime proposal is an isolated **transport-only diagnostic**,
first without Android traffic, using the same pinned relay and the already public
synthetic signed event/112-byte exact query. Require actual send callback, backend
receive/send, EVENT+EOSE or a precisely recorded refusal under the original timer.
A second separately declared synthetic case may add the frozen observed APP REQ
burst to test scheduling interference. The captured post-guard times are not an
exact reproduction of original socket arrivals; label that case modeled traffic.
No new encryption/signing/profile/nonce handling is needed. Keep all negative
and timeout histories. This would diagnose the transport/harness boundary only,
not qualify ordinary-client UI or unlock E02/E04/E06. Source, targeted controls,
independent QA/security and a fresh explicit finite diagnostic grant precede it.
No such source change, diagnostic, service, PID probe, import or retry was run.
