# Before-install boot-trace runtime: acquired prefix

This is a DATA-only archive of the root-operated finite run
`a378eba11798416a8c992f371b61f93b`. The run ended with exit2 and
`FAILED_UNQUALIFIED`; no final diagnostic result or ordinary-client row exists.
The archiver neither ran Android nor retried, repaired or extended this run.
Independent QA/security acceptance is a separate coordinator-owned gate.

The fixed archiver copied475 files/3,933,822bytes:471 selected run members and
four preparation bindings. Every copied member has its original path, mirror,
byte length and SHA-256 in `mirror-manifest.json`, with byte equality checked
again against the original. The11 current source pins were independently
rehashed as DATA, without imports. The archive includes all132 raw command
receipts and264 streams, lease/revocation, ownership, namespace/build evidence,
cleanup,16 diagnostic raw captures and both early/postboot partial journals.
Entire Android mutable state, disk/encryption images, ADB keys/tokens, relay DB,
Docker configuration and mounted input copies are excluded. External SDK/APK,
image and dependency caches were not traversed or copied. Exclusions/counts are
explicit in the manifest. No PNG/XML was produced and none is silently omitted.

The first preserved sticky reason is the control file's exact text:
`owned command failed: LeaseDenied: command deadline`.
Command0132 attempted the fixed `uiautomator dump` after successful command0131
ownership inspection. It is the only abnormal command receipt: `forced=true`,
`reaped=true`, `error="LeaseDenied: sticky revocation"`, empty streams with
both EOFs, `timedOut=false`, and `exit=0`. That exit does not make the operation
successful. The control file records the prior owned-command deadline; the
outer receipt observes the resulting sticky revocation. There is no retained
nested ADB-child receipt or individual elapsed clock sample, so exact nested
completion timing is unknown. No later diagnostic command was attempted.
Cleanup is separately recorded and confirms identity and absence for all four
exact-owned containers, with no cleanup or secondary errors.

Early ADB capture completed three observations in4.999714024s within its30s
phase. The postboot acquired prefix contains13 observations over39.010088515s
of its180s phase. Its partial journal ends230.573806808s after original lease
issuance on the recorded monotonic clock, inside the original1800s deadline.
The12.296857813s between the last observation and partial-journal end includes
UI capture setup/failure handling; it is not a measured nested-child duration.
No phase or lease was renewed. Late checkpoint, UI XML/PNG and final result are
missing because capture stopped at the first refusal.

The acquired prefix includes full retained early/system/event logs,
`lastanr`, `lastanr-traces`, fixed-tag DropBox and guest PID/name snapshots.
`lastanr` reports no entry while the other two contain candidate payloads.
Matching their process/PID/time/reason/stack belongs to independent raw-data
research/review; the driver conservatively leaves correlation UNKNOWN.
One private whole-container cgroup sample is present; all three PSI reads are
explicitly unavailable. Neither a single sample nor absent lastanr state proves
health, peak usage or ANR cause. No APK install, client intent, identity/login,
fixture operation or clipboard action is claimed. E02 remains PARTIAL and
architectural blockers are unchanged.

`root-tool-association.json` explicitly transcribes the parent's mailbox report
of foreground30292 and chunksb8a98d/1c3a5f, exit2. It is not a claim that this
archiver operated or independently witnessed that foreground session.
`archive-execution.json` separately records the actual DATA-only archival tool.

Next: independent QA/security review of this acquired-prefix archive and the
researcher's raw ANR correlation; no automatic rerun or source change follows.
