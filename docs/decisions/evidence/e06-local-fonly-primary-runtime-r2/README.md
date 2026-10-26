# Primary LOCAL runtime R2: preserved deadline failure

Actual execution operator: `/root`. DATA mirror operator:
`/root/local_monitor_controls`. All17 native-output files and all3 outer-output
files are mirrored byte-exact (279,158 logical bytes). Manifest entries preserve
original/mirror lengths and SHA256 plus source stat identities/modes. Originals
and the first failed R1 attempt remain intact. No external descriptor referents
are recursively copied; this is not a portable replay image.

Root reported foreground95660, launchf68646, completion4b35bf, outer exit2.
`tool-association.json` explicitly transcribes that mailbox report; the mirror
operator did not execute the workload or possess its foreground handles.

The68,263ms outer capture naturally reaped qualification child exit1, with no
outer force, timeout or signal. It retained complete4,949-byte stdout and empty
stderr; stdout is byte-identical to native capture.json. The monitor first error
is QUALIFICATION_CHILD_NONZERO_EXIT, monitor exit2 and originalPinsCurrenttrue
is a reported outer check.

The qualification capture is UNQUALIFIED with first
NATIVE_COMBINED_WRITE_REPLY_DEADLINE. One JS Node process was acquired; its
6,276-byte request was fully written, but no reply or sidecar appeared. Native
stdout and stderr are both empty. The native process timed out, was forcibly
terminated with SIGTERM and reaped with full EOF; exitCode remains null.
The native/job cleanup qualifiedfalse is preserved; an empty top-level cleanup
problems array does not override it. Comparison records ONE_COMPLETE_NATIVE_REPLY.

Q-RUST is NOT_EXECUTED/EARLIER_FAILURE. Counts are metadataRequests1; replies,
D validations and F validations remain null/unknown. Nine recorded noEffects
counters are0; these are not measured proofs of the unexecuted business/integrity
negative matrix. No recovered-original or accepted13-key reply is established.

Empty stderr does not prove exact JS phase progress, the precise blocker, or that
the authority-mode path passed. Acquisition/consumer phase anchors and observation
list are empty. Root's separate authority600 preflight remains its own evidence;
it is not converted into native phase-success evidence here. Read-only diagnosis
will correlate source/timing facts separately.

Original source-defined15s combined write/reply,240s job,1500s LOCAL and1800s
outer budgets remain unchanged. This mirror operator changed no timeout, source,
mode, configuration, grant or approval and executed no experiment or retry.
The complete failure must remain visible alongside later remediation. Independent
QA/security whole-result acceptance remains pending; no canonical PASS or
architectural blocker closure is implied.
