# Primary LOCAL runtime: preserved unqualified attempt

Actual execution operator: `/root`. DATA mirror operator:
`/root/local_monitor_controls`. This directory does not execute or repair the
workload. It preserves all17 regular native-output files and all3 outer-output
files,278,349 logical bytes, with exact original/mirror lengths and SHA256 values.
Original paths and their receipts remain unchanged. External descriptor referents
are not recursively copied; this is not a portable replay image.

Root's reported actual foreground invocation was68401, launch tool95e9c9,
completionb753cf, exit2. `tool-association.json` is explicitly a transcription of
the root mailbox report, not a claim that the mirror operator executed it.

The53,347ms outer monitor acquired and naturally reaped its qualification child
with exit1, no force/timeout/signals, full EOF and exact4,933-byte stdout/empty
stderr capture. The outer first error is QUALIFICATION_CHILD_NONZERO_EXIT and
monitor exit is2. Original inputs are reported current by the outer record.
Its stdout is byte-identical to the native root `capture.json`.

The qualification capture is UNQUALIFIED/NATIVE_STDERR_NOT_EMPTY. Actual JS
launch and terminal receipts identify one acquired Node child. Its6,276-byte
request was fully written and its observed28-byte stderr is exactly
`Error: OWNED_AUTHORITY_0600` followed by newline. Stdout is empty, reply and JS
sidecar are null, and the whole comparison reports ONE_COMPLETE_NATIVE_REPLY.
The native child was forcibly terminated with SIGTERM and reaped with full EOF;
its exitCode is null, timedOutfalse and forcedtrue. This is not a successful
natural native lifecycle. Native/job cleanup is explicitly unqualified; the
capture's empty cleanup-problems array does not override qualifiedfalse.

Q-RUST is NOT_EXECUTED/EARLIER_FAILURE. Counts are metadataRequests1, while
metadataReplies/dValidations/fValidations remain null (unknown), not zero or
successful validation. Recorded noEffects fields are all0; those counters do not
establish the unexecuted semantic negative/order/replay/conflict test matrix.
There is no accepted13-key reply or recovered-original evidence.

The28-byte stderr reports an authority-mode refusal. Exact operand localization
and any comparison of current0664 mode against required0600 belong to the
separate read-only diagnosis. The message alone does not identify that operand
or justify a silent permission change. No chmod, source correction, retry, grant,
canonical PASS, blocker closure, SDK or production action occurred here.

Independent QA/security review of this preserved whole result remains pending.
The original failed attempt remains visible and must not be replaced by later
remediation evidence.
