# Pinned strace containment controls — SOURCE ONLY

This separately reviewed scope addresses QA-E06-OBSERVER-TRACE-LIFECYCLE-002 and
SEC-E06-OBSERVER-DESCENDANT-READINESS-002. No runtime leak or EXITKILL defect has
been observed. No controls, strace, Node or LOCAL runs were executed for this prep.

The independent non-traced guard becomes a process-local child subreaper, launches
one owned runner, and holds its pidfd before any exec assertion. Runner invokes the
exact new observer.capture function, with only fixture ROOT,4s active/2s cleanup,
1MiB trace/64KiB stdout/256KiB stderr and fixed Python fixture argv substitution.
Actual pinned strace receives the exact production trace options, all6 read/write
syscalls raw, no attach/environment/buffer dumps. Nothing imports qualification,
admission, producer, consumer or project protocol code.

Traced fixture parent becomes a separate session and creates a separate-session
child, which creates a separate-session grandchild. Each blocks before creating
the next descendant until guard has verified canonical cmdline, parent, UID,
starttime, session and held pidfd with matching fdinfo. All3 registration ACKs
precede all-ready. All3 exercise all6 buffer syscalls with a public synthetic
sentinel before intentional interruption/death/fault is armed. Natural cases
finish through child.wait; failure cases keep their own8s fallback lifetime.

Seven separately retained cases, exact order: natural-zero; natural-refusal2;
observer4s deadline; observer SIGINT; capture-write failure after readiness;
SIGKILL of held tracer; SIGKILL of held inner parent. Every case uses real strace
and SAME capture. Expected failures remain observed failures, not conformance.
No pooling, skips, timeout-as-success or automatic retry. Initial failed case stops.

Guard admission pins complete source subject, current cached strace/Python,
private0600 source and exact HOST namespace context. The guard stays outside
ptrace;9s ownership/absence deadline and11s total per case remain absolute.
After capture record appears, absence must occur within250ms rather than waiting
for8s fixture lifetime and falsely attributing that exit to ptrace cleanup.
Any pidfd safety fallback, readiness error, stale identity, reaping uncertainty,
raw cap/privacy mismatch or original first-fault mismatch is FAIL. No numeric PID
kill or wildcard wait is used. Known adopted children are WNOWAIT-observed and
reaped; exited non-child pidfds plus ECHILD preserve original-parent reaping facts.
No signal after reaping or reuse can target another process: pidfds remain held
until cleanup records are formed. Root must retain the external foreground tool
association/exit/raw stdout+stderr; suggested outer tool ceiling90s for7*11s plus
finite admission. A whole suite's elapsed time is still an actual measurement.

Readiness and limitations requiring independent SOURCE review:
- The guard's assurance covers the finite acknowledged graph, not arbitrary host
  process containment. Initial registration failures stop and remain unqualified;
  no intentional fault is armed before the known graph is held.
- Kernel uninterruptible sleep, simultaneous guard SIGKILL or host failure cannot
  be hard-preempted by Python deadlines. Missing cleanup is an explicit failure,
  never an unlock. Do not claim all-PID containment or native Node cleanup.
- Guard exception handling independently kills only held known identities and
  continues finite reaping. No claim is made about an unregistered unknown PID.
- Guard results are candidates until actual raw full7 scope, privacy rendering,
  current host/tool/source lineage and independent QA/security review are joined.
- SOURCE alone proves neither strace runtime behavior nor acceptable timing. The
  proposed250ms post-capture absence window is strict and may cause a genuine
  FAIL under scheduling pressure; do not silently relax it or retry.

All fixture artifacts persist under actual-containment-r1/case. Capture uses
exclusive600 files, raw counts, poisoned failed stream and first-fault retention.
The guard never creates an activation acceptance. Root must build an actual result
subject only from real complete records and actual independent reviews. No future
hash, grant or approval is invented here. Node activation separately joins this
scope plus13 pure and3 path controls, actual source reviews and fresh dual grants.

Original fullLOCAL/15/240/1500/1800+30 and exact6276 request are unchanged.
