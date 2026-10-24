# Containment source revision2 — not executed

This revision preserves controls-r1 and SOURCE-r2 with actual WHOLE HOLD findings
QA-E06-CONTAINMENT-SELF-EXPIRY-003, SEC-E06-CONTAINMENT-EXPIRY-003 and
SEC-E06-CONTAINMENT-REGISTRATION-004. No actual strace defect or leak is proven.

Registration (3s) and fault lifetime (30s after ready) are separate. Guard requires
actual capture receipt by7s and complete owned absence by7.25s since case entry,
before its11s cleanup bound and strictly before30s fixture expiry. Missing/late
capture or late absence FAIL even if EOF/reaping eventually succeeds. Natural
fixtures finish explicitly through child.wait; fault self-expiry is never success.
Fixture capture remains4s active+2s cleanup; production15/240/1500/1800+30 stays.

Dedicated, single-threaded, child-free subreaper guard owns all its descendants.
SafetyOwner retains Popen handle IMMEDIATELY before pidfd/identity/census calls.
Runner waits for guard ACK before launching strace. Traced parent and child each
wait for independent one-child spawn-intent ACK before Popen; every role still
waits for identity/pidfd ACK before it may create the next descendant. Registration
is readiness, not ownership. Repeated actual Linux ancestry census finds even
unregistered/reparented children after failed Popen/identity/pidfd/ready JSON.
Post-ready unregistered descendants FAIL. Every failure invokes independent
finite census->kill->reap until two empty censuses, never registered-items only.

Normal signals use held pidfds and exact UID/starttime/cmdline/ancestry records.
If pidfd open itself fails, safety fallback may signal ONLY exact direct unreaped
guard children after stable UID/starttime/parent and WNOWAIT checks. Such a PID
cannot be reused until this guard reaps it. Nonchildren never use numeric fallback;
killing/reaping known parents exposes adoption in the next full census. Every
fallback is FAIL. This explicitly narrow numeric cleanup branch needs security
review; it does not weaken readiness's mandatory live-held-pidfd requirement.
Reaping checks starttime before numeric wait; reused identities are never waited
or signalled, and reaped identities never receive another signal. An exited
nonchild pidfd alone no longer claims reaping while its owned parent still lives.

11 modeled DATA regressions (test_guard_faults.py) cover Popen failure; pidfd open
failure with retained handle; identity failure; unregistered descendant cleanup;
ready ACK write failure; missing, corrupt and late registration; late capture;
self-expiry/late absence; no reused/reaped signals/waits. They patch kernel/process
operations with explicit synthetic identities and NEVER spawn anything. They are
not actual ptrace evidence. Persist all future inputs/results, no retry.

Before any real7 case, guard requires externally pinned actual11 guard-model +14
admission-DATA acceptance, full actual current observer/helper/fixture SOURCE
closure, exact source and result subjects, and two independent nonauthor/nonoperator
reviews for SOURCE and actual models. Both modeled counts remain distinct. Nothing
in this prep creates these future records or grants.

Only after matching independent SOURCE review and actual modeled acceptance may
root separately authorize the7 real pinned-strace Python cases: natural0,
refusal2, observerdeadline, observerinterrupt, capturewritefault, abrupt tracer
death and innerparentdeath. Same observer.capture AST, exact cached tools/HOST,
private bounded trace/stdout/stderr, raw6 buffer syscalls and positive privacy
sentinel retained. Each requires all3 separate-session identities registered,
all6 syscalls exercised before intentional fault, complete timely absence,
WNOWAIT/reap/EOF receipts, no safety fallback and raw caps/privacy. First failure
stops. No case is preclassified as passing. Root external foreground ceiling90s
for7*11s plus finite setup; retain tool exit/raw streams/source before+after.

All assertions require actual runtime evidence: SOURCE code, fake proc DATA,
requested EXITKILL, exit0 or a configured deadline alone prove no containment.
Kernel uninterruptible sleep, host failure or killing the independent guard can
prevent Python cleanup; missing cleanup stays FAIL. Unknown/unowned/changed-UID
processes are not signalled. Finite ancestry scope is this disposable fixture,
not arbitrary all-host/native Node containment. No Node/LOCAL unlock from models.
