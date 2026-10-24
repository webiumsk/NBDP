# Completed runtime evidence checkpoint

This inspection bundle is prepared for coordinator review. Its builder performed
DATA archive/hash validation only. Independent package QA/security review,
staging and publication remain separate coordinator actions.

The [archive](completed-runtime-evidence.tar.gz) contains **1,598 file copies**
from22 fixed roots, totaling **26,994,484 logical bytes**. Its compressed size is
5,260,333 bytes. Copies are not counts of unique experiments, assertions or
successful tests. The [complete index](archive-index.json) records each exact
original path, length, SHA256 and original filesystem metadata. The
[selection](selection.json) declares scope and exclusions; the
[verification](archive-verification.json) records the streamed member checks and
subsequent full original-file rechecks. [Normal-core suggestions](normal-core-suggestion.json)
are a coordinator aid and have not been staged.

## Evidence entry points

Paths below are under `repository/docs/decisions/evidence/` inside the archive.
They preserve the actual reports and their distinct scopes.

| Entry point | Preserved result and practical limit |
| --- | --- |
| `e02-android-boot-trace-runtime-r1/acceptance.json` | Matched System UI startup-ANR event/stack prefix. Whole diagnostic failed at mandatory UI dump; no healthy OS or ordinary-client row. |
| `e02-android-lavapipe-runtime-r1/acceptance.json` | Initialized Lavapipe/Mesa/llvmpipe evidence agrees across emulator and guest records; System UI ANR persists. Completed capture does not establish health or a causal renderer fix. |
| `e02-api35-fixture-preparation-r1/outcome-addendum.json` | Managed-environment DNS refusal before HTTP/TLS or ZIP acquisition. TLS configuration is not a verified peer observation. |
| `e02-api35-fixture-preparation-r2/acceptance.json` | Separately acquired official API35 revision2/ext13 image and434-file isolated SDK accepted as DATA. No emulator boot or client compatibility is established. |
| `e06-local-fonly-primary-runtime-r1/acceptance.json` | First actual LOCAL attempt failed native authority permissions; JS had no reply, forced native cleanup stayed unqualified and Rust was skipped. |
| `e06-local-authority-mode-remediation-r1/result.json` | Exactly two owned approvals tightened0664-to0600 with unchanged bytes and identity. Git does not retain this runtime permission distinction. |
| `e06-local-fonly-primary-runtime-r2/acceptance.json` | Fresh LOCAL attempt failed its original15s combined reply deadline. Child phase is unknown; parent-written input is not proof of parsing. Rust remained skipped and validation counts null. |
| `e06-js-startup-prefix-diagnostic-r1/initial-review-history.json` | Source capture-prefix defect held before execution; initial security acceptance was withdrawn. |
| `e06-js-startup-prefix-diagnostic-r2/failed-controls-qa-review.json` | First seven-control suite had5 passes and2 genuine failures; short fixture windows did not exercise two intended branches. Original modes and failures are preserved. |
| `e06-js-startup-prefix-diagnostic-r3/control-acceptance.json` | All seven fresh owned-Python fixture controls passed with exact partial-write accounting and0600 artifacts. These are not Node/strace or NBDP interoperability results. |
| `e06-js-startup-prefix-diagnostic-r3/actual-preflight-refusal.json` | Host invocation refused before output/Node/trace because root-owned metadata UID/GID differed from the managed namespace; the compared bytes were identical. The unused grant expired unchanged. |

LOCAL `noEffects` zeros are initialized declarations, not independent effect
measurements. Empty child stderr does not establish passing authority, import or
handler phases. Conditional source-derived hashing work is not a measured
runtime cause. Historical effective Android renderer remains UNKNOWN, and new
observation plumbing prevents a controlled renderer-only causal comparison.

## Archival properties and exclusions

All tar members are sorted regular files with mode0600, UID/GID/mtime zero and
safe relative `repository/` names. There are no symbolic links, hard-link
members, special files or executable archive modes. Gzip has no filename and
mtime zero. Original files, permissions and metadata remain unchanged; archived
mode600 does not rewrite historical0664 capture files. Raw `.diff`/`.patch`
context and all binary streams retain their exact bytes.

The only files omitted from the22 selected roots are the two
`current-official-license-text.txt` files in the API35 preparation directories.
Their exact descriptors and original stats are in the index, and originals stay
local. Full license text is not redistributed here. Existing technical license
identifier matching is preserved without a new acceptance action or legal
consent conclusion.

SDK/APK/ZIP/disk-image/key inputs and other external referents are not copied.
The acquired782,404,023-byte API35 ZIP,2.7GB-class SDK and pinned tools remain
external prerequisites. Only their source/provenance/inventory records are in
this bundle. It is not a self-contained portable replay image. Extracted copies
must not be substituted silently into historical absolute-path authority graphs.
Old grants are historical evidence and do not authorize new execution.

Active startup diagnosticR4 and Android35 source-profile preparation, mutable
project indexes and the six earlier checkpoint archives are outside this frozen
selection. No production data, keys, SDK work, deployment, new kind/NIP or
publication was performed by this archive builder. No canonical PASS, gate
waiver or architectural blocker reclassification follows from packaging.

List without execution using `tar -tzf completed-runtime-evidence.tar.gz`.
Extraction into a fresh disposable directory is inspection only. Reproduction
requires current exact inputs, applicable prerequisite/review gates and a fresh
coordinator grant.
