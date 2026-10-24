# Transport gate runtime evidence publication

This package preserves the isolated work after disk space was freed. It does not
promote canonical experiment results, close architectural blockers or authorize
production work. The canonical results remain E01 PASS140, E02 PARTIAL22, E03
PASS19, E04 NOT_EXECUTED, E05 PASS25 and E06 NOT_EXECUTED.

## Review entry points

- [Current project state](../../../PROJECT_STATE.md) and
  [action board](../../../research/transport-gate-readiness-2026-10-23.md).
- [E06 current source acceptance](../e06-qualification-current-source-r3/acceptance.json).
- [E06 fourteen pure controls](../e06-current-controls-r2/control-acceptance.json),
  [ten policy controls](../e06-current-marker-controls-r2/acceptance.json), and
  [21 scoped grammar/boundary controls](../e06-opaque-inventory-controls-r1/acceptance.json).
- [Actual real input-gate positive](../e06-inventory-enforcement-r3/positive-baseline-acceptance.json).
- [Primary 76-case input matrix](../e06-inventory-enforcement-matrix-r1/acceptance.json):
  one actual ACCEPT and 75 exact refusals, without native effects.
- [Actual primary/QA matrix pair](../e06-inventory-enforcement-matrix-qa-r1/pair-acceptance.json):
  the QA operator executed in a separate real subagent session; nonoperators
  reviewed both complete runs. This repeats the same implementation.
- [Ninth ordinary-client attempt](../e02-ordinary-client-resume-r1/runtime-attempt-09/root-observation.json):
  Quickstep framework ANR, safe refusal and four qualified owned removals. No
  ordinary-client row qualified.
- [Independent Android diagnosis](../e02-android-anr-diagnosis-r1/report.json).
- [Actual Android failure diagnostic](../e02-android-health-runtime-r1/acceptance.json):
  baseline System UI ANR predates the Amethyst intent; measured CPU throttling
  does not establish its cause.
- [Actual CPU8 diagnostic comparison](../e02-android-health-cpu8-runtime-r1/acceptance.json):
  the ANR persisted. No further resource increase or healthy-client conclusion
  follows; before-install process/reason/stack correlation is next.
- [28 synthetic aggregate DATA controls](../e02-ordinary-aggregate-controls-r1/acceptance.json):
  these qualify no actual ordinary-client observation.

## Archives and exact membership

| Archive | Included evidence | Limits |
| --- | --- | --- |
| `e02-raw-attempts-and-readiness.tar.gz` | All 3,698 files in the frozen coordinator-owned ordinary-client readiness and nine-attempt evidence directory | No APK, SDK, keystore or AVD disk; all nine attempts remain unqualified |
| `e06-source-graph-repository-files.tar.gz` | Exact 380 repository files from the accepted 449-member source graph | 69 external originals are inventoried but not distributed |
| `e06-control-and-input-runtime.tar.gz` | 346 source/control/preparation/runtime files, including the preserved wrapper and real-gate failures and all 76 primary rows | Primary caller-memory evidence only; no independent repetition or native qualification |
| `e02-health-and-aggregate.tar.gz` | 683 original source/review/control/diagnostic files, including all 596 raw diagnostic mirrors | Failure diagnosis and synthetic DATA controls; no ordinary-client row |
| `e06-qa-input-matrix-runtime.tar.gz` | 112 exact source/configuration/review/operator/runtime files, including all 78 QA outputs | 76 cases per operator; no independent implementation or native qualification |
| `e02-cpu8-diagnostic-runtime.tar.gz` | 620 preparation/control/review/runtime files, including all 565 raw B mirrors and small AVD text addenda | Persistent environment failure; no ordinary-client row |

[E02 archive index](e02-raw-archive-index.json) and
[E06 source archive index](e06-source-archive-index.json),
[E06 runtime index](e06-control-and-input-runtime-index.json) and
[health/aggregate index](e02-health-and-aggregate-index.json),
[QA matrix index](e06-qa-input-matrix-runtime-index.json) and
[CPU8 diagnostic index](e02-cpu8-diagnostic-runtime-index.json) record every archive
member, original path, byte count and SHA256. All archives use sorted regular
members, relative `repository/` paths, zero timestamps and no executable modes,
symlinks or special files. Originals and local evidence are retained.

List an archive with `tar -tzf ARCHIVE`. Inspection or extraction into a fresh
disposable directory does not execute it. Original absolute descriptors retain
their historical meaning; extracted copies must not be substituted into accepted
authority graphs. Old releases are evidence, not fresh execution permission.

The external inventory includes interpreter, browser, native binaries and local
synthetic runtime/TLS fixtures. Replaying a workload requires the exact admitted
environment, current source/configuration checks and a fresh independently
reviewed release. This package is not a self-contained portable replay image.
No production credentials, personal identities or real documents were used.

## Interpretation

The 14, ten and 21 control scopes are separate. The 21 observations comprise 17
private-helper metadata checks, one source-AST order check and three raw/output
boundary checks. A real 33,554,433-byte sparse file was stream-hashed and refused
by the unchanged 32MiB raw reader. Acceptance at 512MiB is metadata grammar
evidence; it is not a real 512MiB acquisition or resource measurement.

The real input primitive accepted all 57 original inventory roles and the separate
derivation/output descriptors. The primary matrix additionally refused all 75
precommitted invalid caller-memory/configuration/mapping cases. It did not invoke
full LOCAL admission, native backends, request delivery or TARGET. Its original
SCHEMA_INTEGER failure remains preserved. Independent repetition and subsequent
gates require their own exact evidence and independent review. The input matrix
now has actual independent-operator repetition and whole-pair acceptance; full
LOCAL/native/custody/TARGET qualification remains separate.

One byte-identical historical supervisor document retains relative links from its
original source location. The validation record checks that original referent
against the raw archive, rather than rewriting historical bytes. Unified patch
files retain their required blank context markers inside the exact raw archives.
Their duplicate normal-tree copies are omitted; all staged files pass whitespace
checks. Full PNG/XML and large duplicate control records likewise remain in the
indexed archives.

The ordinary-client failure is an environment/UI admission result. It establishes
neither business-envelope incompatibility nor successful rendering/export. A
chat client's lack of an invoice-specific interface does not itself violate NBDP.

The initial publication subject was held by independent QA/security for stale current-status text. See [preserved findings](publication-initial-review.json) and the exact superseded documents. The corrected checkpoint is [publication-subject-r2.json](publication-subject-r2.json); its separate acceptance is required before publication. Historical experiment failures are unchanged.
