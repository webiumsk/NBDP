# E02 multi-run supplementary adapter v1

SOURCE PREPARATION ONLY. No import, test, experiment, Android action or canonical
integration is authorized by these files. Existing `e02_ordinary_control_evidence_v1`
and the active first-cell runtime sources remain unchanged. Independent QA/security
source review precedes any pure controls. Runtime use requires separately reviewed
actual operands and reviews, not merely this interface.

This adapter collects the fixed eight cells: `js-to-rust` / `rust-to-js` ×
`incoming` / `archive` × `rs-relay` / `strfry`. A version-one member normalizes
exactly one complete first-slice observation from its own fresh finite run. Thus
eight accepted cells require eight distinct run IDs/configurations/releases and
run roots. It does not turn the current first-cell-only producer into a producer
of the other seven cells. Those producer changes, full matrix observations and
canonical integration remain pending separately.

## Existing artifacts and the explicit adapter boundary

The unchanged consumer is loaded only from its fixed repository path, after its
exact source descriptor is checked; the verified bytes themselves are compiled.
The externally trusted inventory hash pins that descriptor. There is no
JSON-selected module, function, command execution, network access or file write.

The adapter reuses the full existing `inspect_capture`, `inspect_observation`,
`actual_reviews`, `client`, `prerequisites`, rumor ID/export/whole-byte/role/dispatch
and file validation. Its versioned plan adapter preserves all v1 plan checks and
adds full source/configuration joins. It does not claim the unchanged v1 CLI can
read current real release documents: that CLI's `inspect_plan` reads releases with
its SAFE-integer reader and rejects current `notAfterUtcNs` values above 2^53−1.

Only runtime metadata documents use the separate reader. It accepts signed64
integers **only under** `notAfterUtcNs`, `issuedUtcNs`, `deadlineUtcNs`,
`issuedMonoNs`, `deadlineMonoNs`, `issuedBootNs`, `deadlineBootNs`; other integers
remain SAFE. Duplicate keys, fractions, negative zero, nonfinite numbers, invalid
UTF8/surrogates, excessive depth and unknown contract keys refuse. This allowance
never applies to v1 plan/capture, wire, rumor, selection or helper JSON. Host
selection monotonic time is compared only to the host monotonic lease. Guest
elapsed/wall-clock clipboard values are compared only within their own domains.

All descriptors are the existing `{path,bytes,sha256}` shape. Original pins are
never refreshed. Existing per-run 16MiB data, 512MiB file, 2GiB and 2048-file limits
remain. The aggregate adds a union ceiling of 16384 paths and 2GiB unique-path
bytes across at most64 inventoried attempts; shared identical paths count once.
Every run and the complete union are rechecked before a result. Inventory scanning
requires every sequential `commands/0001.json` through the final command, with at
most512 command receipts; each complete stdout/stderr descriptor is checked.

## New candidate and attempt inventory

The new candidate document has exactly:

```text
{schema:"e02-ordinary-aggregate-candidate-v1", id, client,
 prerequisites:{E01,E02}, basis:[descriptor,...],
 scope:"ORDINARY_KIND14_EIGHT_CELL_SUPPLEMENT_ONLY"}
```

`client` and prerequisites have the unchanged v1 meaning and exact checks.
`basis` is a nonempty common immutable source list, included identically in each
contributor's source plan. It identifies the reviewed common candidate, not a
claimed runtime result or release.

The externally pinned inventory has exactly:

```text
{schema:"e02-ordinary-aggregate-inventory-v1",
 evidenceType:"ACTUAL_RUNTIME"|"SYNTHETIC_DATA_CONTROLS_ONLY",
 operator, authors:[session,...], candidate:descriptor, consumer:descriptor,
 runs:[{member:descriptor, disposition:"CONTRIBUTE"|"EXCLUDE",
        classification:"QUALIFIED"|"ENVIRONMENT_FAILURE"|
                       "COMPATIBILITY_FAILURE"|"UNQUALIFIED",
        reason:null|string, reviews:{qa:descriptor,security:descriptor},
        observationReviews:null|{qa:descriptor,security:descriptor}},...]}
```

Every candidate attempt, including failed/unqualified/environment attempts, must
be listed. Exclusions need a concrete reason and independent whole-run exclusion
reviews. Excluded artifacts remain visible in results and contribute no rows.
An inventoried reproducible `COMPATIBILITY_FAILURE` always yields FAIL even if a
later attempt matches the same cell. Duplicate contributing cells refuse,
including byte-identical repetitions; there is no preferred-result selection.

The program cannot discover attempts omitted from an externally supplied
inventory. Actual independent inventory reviews therefore must audit its
completeness against the coordinator's actual launch/failure history. The two
external inventory review operands are new proposed records, each exactly:

```text
{schema:"e02-ordinary-aggregate-inventory-review-v1", role:"qa"|"security",
 session, decision:"ACCEPT_COMPLETE_CANDIDATE_ATTEMPT_INVENTORY_ONLY",
 inventory:descriptor, candidate:descriptor, completeAttemptInventory:true,
 findings:[], rawReviewEvidence:descriptor}
```

Sessions must be distinct and outside the union of inventory authors/operator
and **all inventoried members' authors/operators, including excluded attempts**.
Every member must disclose a valid nonempty author list and operator before any
inventory review can be accepted; omission from the inventory's own author list
does not confer independence. Missing member identity disclosure refuses.
`rawReviewEvidence`
is the actual independent report/transcript. Hashes, role strings and positive
words do not authenticate a review. The coordinator must independently know the
inventory and both review hashes and verify their actual reviewer provenance.
No old source review, synthetic control or self-review supplies this authority.

## New run member

The member has exactly these fields:

```text
{schema:"e02-ordinary-run-member-v1", runId, runRoot, operator, authors,
 candidate, client, cell:{direction,role,relay}, sourceSubject,
 runConfig, runRelease, lease, supervisor, outer, driver, plan, capture,
 fixturePrepare, commandReceipts:[descriptor,...]}
```

All artifact fields except `client`/`cell` are descriptors. `runId` is32 lowercase
hex; `runRoot` is its canonical existing directory. Every contributor has its own
original config/release/lease, six activated input copies, complete source subject
and source reviews, real client/helper identity, fixture prepare reply, driver
result, supervisor result, natural outer completion witness, v1 plan/capture,
all child command receipts and two sets of actual results reviews. Fields for
artifacts absent from an excluded failed attempt may be null; these members never
enter qualification or donate earlier apparently successful rows.

The current runtime metadata schemas are explicitly supported, without rewriting:

- `e02-single-cell-runtime-plan-v1`, full current closed field set;
- `e02-first-cell-release-v1`, actual root/source/config/source-review joins;
- `e02-first-cell-complete-source-config-subject-v1`, current17-field subject;
- `e02-single-cell-lease-v1`, original1800s deadlines in all three clock domains;
- `e02-first-cell-supervisor-result-v1`, original PARTIAL header, null error,
  empty secondary errors, exact run/config/release/lease and qualified cleanup;
- `e02-first-slice-driver-result-v1`, original PARTIAL header and complete single
  observation; account/Tor/environment captures are retained and hash checked;
- actual complete child receipts: natural exit0, no error/force/timeout, reaped
  child and both EOF flags, whole stdout/stderr custody. These facts are **child
  receipt facts**, never invented outer-process facts.

Cleanup requires all four exact-owned Android/fixture/anchor/selected-relay rows,
unique CIDs, verified identity, remove0 and qualified absence1, empty errors and
an identical separately saved cleanup record. A failed supervisor, cleanup,
revoked lease, interrupted child or outer process cannot donate an earlier row.
Unknown metadata versions/fields require a separately reviewed adapter revision.

Fixture lineage preserves original guest descriptors and verifies their exact
host mapping under the same `runRoot/session/fixtures`. Frozen rumor/content,
prepared rumor/wraps, actual received transport and driver originals must join.
The rumor timestamp must fall inside the original UTC lease. The selected UI
must occur in the actual driver's capture array. Helper artifact equals that
run's config; actual focused CLEAR precedes its CAPTURE in guest clock domains;
raw helper bytes/hash and all six retained inner fields use unchanged v1 checks.
Expected fixture bytes and independently decrypted transport cannot substitute
for the actual selected-note export.

## New outer completion normalization

No existing outer witness is claimed. Root must retain the actual launch/final
tool result before creating this proposed closed normalization:

```text
{schema:"e02-outer-tool-completion-v1", runId, runConfig, runRelease,
 launchTool, launchSession, finalTool, finalSession, argv,
 finalToolResult:descriptor, exit:0, sessionFinished:true,
 interruptionSent:false, terminateSent:false, timeoutSent:false,
 completionProof:"ACTUAL_FINAL_TOOL_RESULT"}
```

Tool/session identifiers are nonempty strings; integer tool session IDs are
transcribed to their exact decimal strings. Launch/final session must agree.
`argv` must be the exact actual14-token `python3` or `/usr/bin/python3`, `-I`, `-B`, pinned
supervisor path, `--config PATH --config-sha SHA --release PATH --release-sha SHA
--out RUNROOT` invocation. `finalToolResult` is the original final tool JSON/text,
hash checked as opaque tool evidence. Actual reviewers check that it supports the
normalized facts and that no interrupt/terminate/timeout was sent. Missing or
unknown proof refuses. No PID, reaping or full-EOF assertion is inferred from a
tool session finishing. A completed supervisor child receipt alone does not
prove natural completion of the outer foreground tool session.

The original13-token `python3 -B` adapter contract and its synthetic controls are
preserved in the remediation archive; they do not qualify this changed source.
This revision refuses that old form, reordered/missing isolation flags and other
interpreters. It never removes or normalizes flags. The retained
[R11 launch-tool input](../../../docs/decisions/evidence/e02-ordinary-client-resume-r1/runtime-attempt-09/outer-launch-tool-input.json)
is a concrete `-I -B` contract exemplar from a FAILED_UNQUALIFIED run only;
it supplies no contributing row and no interpreter/Popen/host attestation.

## Actual observation and whole-run reviews

Each contributor retains both unchanged v1
`e02-ordinary-observation-review-v1` records, exact plan/capture/observed IDs,
independent nonauthor/nonoperator sessions and empty findings. The complete
unchanged v1 observation validator runs; no prior standalone consumer result is
accepted as a replacement.

Those records do not cover whole-run admission. Two additional **new proposed**
whole-run records bind the member and its whole outcome, exactly:

```text
{schema:"e02-ordinary-whole-run-review-v1", role:"qa"|"security", session,
 decision:"ACCEPT_QUALIFIED_RUN_FOR_SUPPLEMENT_ONLY"|"ACCEPT_EXCLUSION_RECORD_ONLY",
 member, outer, supervisor, driver, capture, candidate, sourceSubject,
 acceptedObservationIds:[id,...], classification, findings:[string,...],
 rawReviewEvidence:descriptor}
```

All bound artifacts equal the member's exact descriptors. Contribution requires
QUALIFIED, the qualified decision, exact captured IDs and no findings. Exclusion
requires the exclusion decision and no accepted IDs; bounded actual findings may
remain. Sessions must be distinct and outside that run's authors/operator. Raw
actual independent reports remain necessary. No records are generated by this
program and no existing source-only review is relabeled as a results review.

## Result and future invocation

The adapter reports every attempted member, exclusions/refusals, missing cells
and duplicates/conflicts. Qualification errors are visible and donate no rows;
actual retained-content/rendering mismatches yield FAIL. Whole-run qualification
is required before any row enters the matrix. Limited-run PARTIAL headers and
unchanged consumer PARTIAL status are reported verbatim.

Eight complete reviewed cells yield only `MATRIX_MATCHED_SUPPLEMENT_ONLY` with
`canonicalE02Changed=false`, `canonicalStatus="PARTIAL22_UNCHANGED"` and
`fullMatrixAndCanonicalIntegration="PENDING_SEPARATE_REVIEW"`. Synthetic inventories
can yield only `DATA_CONSISTENCY_ONLY`, retaining the matrix calculation in
`matrixState` and an explicit synthetic evidence label. They are not runtime
evidence. Other statuses are PARTIAL, FAIL and QUALIFICATION_REFUSED. Exit0 means
only actual supplemental matrix consistency; FAIL returns1, all other states2.

After independent source review and separate actual operand qualification:

```text
python3 -B aggregate.py INVENTORY INVENTORY_SHA QA_INVENTORY_REVIEW QA_SHA SECURITY_INVENTORY_REVIEW SECURITY_SHA
```

This command does not remove the canonical mandatory Amethyst skip, run adapters,
promote E02 to PASS, close Q01/Q08/Q13/Q15/Q27 or authorize SDK/production work.
Full canonical evidence integration and remaining mandatory controls remain open.
