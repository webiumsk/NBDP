# Containment revision3 — SOURCE ONLY, two findings

Prior revision2 and SOURCE3 stay frozen with actual independent HIGH custody and
MEDIUM census-cleanup HOLD. Source inspection identified possible wrong-process
signalling and skipped known cleanup; neither occurred in an actual run.

The bounded changes are confined to SafetyOwner, required own-path/count/pins and
five new modeled regression families. No fixture/control/production timer changed.

A new ancestry row begins rejected/unsignalable with fd=None. pidfd_open returns
only to a local provisional variable. Full unchanged identity (PID/starttime/UID/
parent/session/cmdline), guard UID, matching fdinfo PID and another stable identity
read must succeed before transfer. Any failure detaches custody before recording
or closing, leaves acquisitionFailed=True and fd=None, and closes the provisional
fd in finally. Failure immediately after transfer also detaches and closes safely.
Rejected custody cannot signal through pidfd OR numeric fallback; close() never
re-closes a rejected provisional descriptor. An actual retained unreaped Popen
handle remains separate direct-child authority for safety cleanup, revalidated
with full identity, owner/parent and WNOWAIT. Every safety action stays FAIL.

Cleanup no longer shares census/signalling/reaping in one try. It separately
records census failure, attempts validated-known pidfd signals, independently
attempts retained direct-handle safety, independently reaps known and retained
handles, and only then attempts absence checks. Persistent census errors cannot
skip those owned cleanup steps. censusUncertain is sticky and forbids complete
absence or qualification even after known child cleanup. Initial fault and bounded
secondary faults are retained. Original absolute11s total remains unextended.

Existing11 modeled families remain;5 new families cover post-open foreign PID
reuse, UID change, identity exception/vanished process, fdinfo mismatch/read
failure, and persistent census failure after validated ownership. Acquisition
families require exactly one provisional close, fd=None, rejection flag and zero
pidfd/numeric signals. Persistent census case requires actual modeled known-child
kill+reap, first census fault retained and FAIL/uncertain absence. All are mocked
DATA controls, not ptrace/runtime or real ownership proof. Their16 definitions
are NOT RUN.14 separate admission DATA and13+3 capture/path definitions also
remain NOT RUN in this revision. Do not run SOURCE3 merely to churn controls.

After BOTH independent SOURCE reviews, root may authorize ONE fresh separately
counted46-control batch (13+3+16+14) over the same frozen current closure. Preserve
first failure and stop without fixes/retries. Actual16+14 acceptance now has fixed
decision ACCEPT_GUARD16_ADMISSION14_MODELED_CONTROLS_ONLY, current whole observer/
helper/fixture subject and actual independent source/result reviews. No acceptance
or grant is manufactured here. The7 real strace/Python controls remain denied
until source/model acceptance and a separate root release; Node/LOCAL remain
additionally denied until actual7 exact pinned tool/HOST/source/lifecycle/privacy
qualification and independent reviews. All old real7 gates and scope unchanged.

No source449 edits, new profile/protocol/architecture, SDK, ptrace policy,
production/network changes or experiments. Python bounds cannot force uninterruptible
kernel work/guard survival; missing cleanup remains failure. No all-host PID claim.
