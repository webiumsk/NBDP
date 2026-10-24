# One fresh real-request phase observation — implementation plan

PLAN ONLY. No code, worker, binding, configuration approval, grant or workload is
created by this task. Scope: **DIAGNOSTIC_REAL_REQUEST_PHASE_ONLY** around one
existing full LOCAL F-only invocation, preserving its sequential Q-JS then Q-RUST
schedule and every authority/custody check. This is an observation of that scoped
LOCAL path, not complete E06 or a canonical gate/status rewrite.

## Evidence and question

Accepted R4 zero-input startup took14.177s under tracing, reached stdin EOF and
returned EOF_REQUEST_COUNT. Retained selected read returns total3,085,140,131
bytes, including three complete449-member closure read sequences. These are
returned bytes, not CPU/RSS/physical I/O or proof of the R2 failure cause.
R1 refused authority0600; R2 wrote its6,276-byte request but received no reply
before the original combined deadline. R4 supplied no request, so request
validation, handler execution and a complete13-field reply remain unproved.

Observe one fresh real request through the current parent/child contract. The
result may be another bounded failure. Do not extend timeouts, prewarm Node,
remove repeated verification, add phase markers or optimize protocol code.

## Exact next implementation assignment

Implementer owns only this preparation directory and the new sibling
`e06-request-phase-diagnostic-execution-r1/`; root owns approvals, grants, state,
roadmap and publication. Preserve all existing workers' files. Proposed fresh
runId is `0f7c2a38d95b`, role primary, executionSession /root, output
`/tmp/e6n-fonly-primary-0f7c2a38d95b`. The prefix satisfies current admission.
These are planned identities; freshness must be checked at activation.

1. Materialize worker-config.json from genuine preparation-r2, changing ONLY
   runId/outputRoot and the Q-JS/Q-RUST output paths. Keep request, expected
   oracles, tools, source449, current SOURCE/control/prerequisite evidence,
   inventory and derivation unchanged. Whole configuration-core.json changes
   ONLY runId and the actual new worker descriptor. Save exact semantic diff.
2. Actual independent QA/security reviews approve the WHOLE new core/worker.
   Root then creates genuine configuration-approval.json and final
   qualification-config.json, adding only configurationAcceptance. Renew
   workflow evidence without claiming the older failed runs succeeded.
3. Derive execution-r1/monitor.py from the reviewed LOCAL execution-r2 monitor.
   Rebind only literal source/config/worker/approval/review/workflow/output/run
   identity pins. Preserve fixed Python argv, full accepted_transport()/LOCAL
   admission, six-variable environment,13-key whole comparisons, custody and
   lifecycle. Report exact source/AST delta and existing partial-write/capture
   limitations; do not silently transplant startup-only semantics or waive any
   defect found during independent review. No protocol source449 edit is allowed.
4. Implement one small fixed observer.py plus observer-configuration.json and
   focused owned-child tests. It externally traces the exact reviewed
   monitor.py and descendants, rather than directly starting Node with an old
   binding. No generic command, attach PID, backend selector or framework.
   Configuration binds actual monitor/final-config/tool/source descriptors;
   future root grant hashes are external operands, never fabricated.
5. Obtain actual independent SOURCE/config/privacy/lifecycle review and execute
   only meaningful observer fixture controls after review. Record failures and
   obtain actual result acceptance. Root supplies a fresh genuine LOCAL release
   and separate diagnostic observation authorization only afterward. Both are
   closed records with exact actual reviewed descriptors; no LOCAL schema field
   is added for tracing. A diagnostic authorization cannot mint LOCAL admission.

No observer source is emitted here: adding a third trace channel, tracer-owned
descendants and a new outer deadline/cleanup boundary is not demonstrably the
unchanged reviewed lifecycle. The bounded assignment above is the necessary
implementation/review task; copying a startup monitor and changing its15s label
would overstate reuse.

## Fresh binding and real request lineage

The unchanged qualification.py must generate Q-JS/binding.json ONLY after full
admission and fresh private directory creation. It derives config, worker, fresh
LOCAL release, SOURCE/configuration approval, original request descriptor, scope,
F fixture, metadata entry, closure and fresh output from the admitted context.
Node receives that runtime-generated binding's actual descriptor/SHA through the
existing argv; no precomputed/old binding or old release is reused.

The original one-line request remains6276 bytes, SHA256
`dc586e609758fb6656c76ab5698985b9620d91e1852c8abfb85b2aaf9da636b0`.
Keep original request, owned request.jsonl, actual captured stdin and binding
request joins. The parent writes one complete line and closes stdin only after
the complete reply, as existing source requires. JS then Rust each receive the
existing request if the earlier job succeeds. JS failure leaves Rust visibly
NOT_EXECUTED/EARLIER_FAILURE; no separate ad hoc Rust run bypasses that schedule.

## External trace, privacy and bounds

Observer builds one fixed command from current pins:

```text
STRACE --kill-on-exit --interruptible=1 -f -qq -ttt -s 256
  -e trace=execve,clone,clone3,fork,vfork,pipe,pipe2,dup,dup2,dup3,fcntl,openat,read,pread64,readv,write,pwrite64,writev,close
  -e raw=read,pread64,readv,write,pwrite64,writev
  -o /proc/self/fd/OWNED_TRACE_PIPE_FD --
  PYTHON -I -B EXECUTION/monitor.py --monitor-sha ACTUAL_REVIEWED_SHA
  --release ACTUAL_FRESH_LOCAL_RELEASE --release-sha ACTUAL_FRESH_LOCAL_SHA
```

Uppercase operands are pending actual values, not runnable fake pins. Trace only
this owned invocation; no attach or ptrace-policy change. Raw read/write-family
arguments suppress buffers; no read/write dumps or verbose environment output.
Native argv/environment stay unchanged. Keep tracer/monitor/qualification/native
PID and FD associations separate. Retain trace16MiB, observer stdout64KiB and
stderr256KiB in a separate fresh trace-actual/ directory, exclusive600/unbuffered
files with fsync. Never put trace files in the native job tree. Overflow is an
actual unqualified prefix; no silent cap increase.

Original limits remain15s combined request-write/reply,240s native job,1500s
LOCAL,1800s outer with30s cleanup reserve. External observation shares the1800s
maximum starting before tracer launch; active capture cannot consume the cleanup
reserve. Native clock origins remain unchanged and are never reset. Preflight
and postflight fit the outer budget. No time/CPU/RSS or untraced-cause claim.

Use actual HOST context for all byte/stat/ownership checks. Preserve the R4
namespace evidence, but do not compare HOST UID0 files against managed65534
without explicit context accounting. Check all actual ownedJSON operands for
UID/current process and0600. Preserve source449, authorities, originals and old
R1/R2/R4 evidence before/after. No mode normalization, cache priming or validator
optimization.

Hold the owned tracer with WNOWAIT until all possible signals finish; never
signal after reap. --kill-on-exit is a containment aid, not proof of native
cleanup. Native processes can have separate sessions. If observation forces the
tracer/tracees or loses lifecycle certainty, preserve that first fault and mark
native cleanup unqualified; do not synthesize graceful receipts. Qualified
LOCAL evidence requires its own natural lifecycle and cleanup graph regardless
of observer exit.

## Strict evidence acceptance and stop conditions

- Admission refusal: retain actual stderr/exit, no bypass, no claimed native run.
- Useful failure prefix: exact current authority/request lineage; trace captures
  actual parent pipe writes and child reads or explicitly missing edges; preserve
  original deadline/refusal, null reply counters, skipped Rust and forced cleanup.
  Byte counts alone do not prove validation or handler entry. This can be
  meaningful DIAGNOSTIC evidence while LOCAL remains UNQUALIFIED.
- Scoped LOCAL success candidate: both genuine whole13-field typed replies match
  original per-backend oracles; JS stdout equals actual sidecar; exact original/
  owned request custody; natural exit/EOF, empty native stderr, current source/
  authority pins and qualified cleanup. Exit0/assertion counts alone do not pass.
- Independent nonauthor/nonoperator QA/security reviews inspect the whole trace,
  requests, bindings, receipts, comparisons and source-supported phase attribution.
  Literal noEffects zeros are not measured no-business-effect proof.

First failure is retained; no retry, changed budget or direct old-binding request
follows automatically. Trace paths/syscalls are source-supported phase inference,
not direct JS markers or a complete process audit. A matched primary F-only
observation still requires later independent QA native repetition/aggregate and
remaining custody/TARGET/negative/order/replay scope. It never completes E06,
changes the E02 mandatory skip, closes architectural blockers or authorizes SDK.
