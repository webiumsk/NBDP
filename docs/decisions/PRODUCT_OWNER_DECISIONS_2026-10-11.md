# Product Owner decisions — 2026-10-11

**Authority:** The Product Owner's explicit NBDP-005 instructions, recorded on 2026-10-11. These are approved scope decisions, distinct from the earlier research recommendations. They conditionally accept the architecture direction and authorize isolated E01–E06 experimental engineering, not a production protocol, SDK, release or integration.

The original evidence is preserved in Git at [NBDP-004 baseline](https://github.com/webiumsk/NBDP/tree/00a5bfbb5656f2a82c0fb9a746c5137c9ea7f3ce). Canonical [Q01–Q27](../research/open-questions.md) and [E01–E16](../research/required-experiments.md) retain their identities. The [ADR](../../adr/0001-transport-selection.md), [risk register](../research/architecture-risk-register.md) and [boundaries](../research/transport-boundaries.md) distinguish current decisions from superseded proposals.

## PO-001

- **Date:** 2026-10-11
- **Exact decision:** Conditionally approve Option B.
- **Approved scope:** Existing encrypted Nostr transport plus an independent, openly specified, versioned business-document application protocol. NIP-17 conventions, NIP-44 v2, NIP-59, persistent outer kind 1059 and existing inbox discovery are initial candidates. Kind 14 envelopes and correlated kind 15 files remain experimental candidates, not normative requirements.
- **Rationale:** Reuse existing cryptography and relay infrastructure while supplying interoperable business semantics independently of any vendor. This rationale is architectural reasoning, not a new interoperability result.
- **Consequences:** ADR status becomes **Conditionally Accepted — Architecture Direction Only**. Exact wire format and candidate kinds must pass independent tests and RFC review.
- **Accepted risks:** Candidate carriers may need revision or prove unsuitable; conditional approval does not establish interoperability.
- **Unresolved technical questions:** Carrier dispatch, nested limits, attachment bytes and ecosystem compatibility.
- **Affected questions:** Q04, Q06, Q07, Q08, Q09, Q10, Q23, Q24, Q25, Q27.
- **Required experiments:** E01–E06 initially; later applicable E07–E15 before SDK authorization.
- **Approval boundaries:** No new NIP or event kind. Reconsideration needs independent evidence of a concrete gap and separate authorization. No normative wire approval, release or production use.

## PO-002

- **Date:** 2026-10-11
- **Exact decision:** NIP-44 baseline without mandatory forward secrecy for v0.1.
- **Requirements:** Explicitly disclose no forward secrecy and no post-compromise security. Compromise of relevant long-term keys may expose captured historical documents and file keys. Relay deletion does not guarantee deletion. Static-key rotation does not retroactively protect old ciphertext. Do not market the baseline as forward-secret. Preserve separately versioned stronger security profiles.
- **Rationale:** Accept a known baseline limitation while validating existing transport; this does not approve unsafe cryptography.
- **Consequences:** FS is not a mandatory v0.1 requirement; complete endpoint, metadata and compromise threat-model review remains necessary.
- **Accepted risks:** Historical ciphertext exposure following relevant long-term-key compromise; retained sender copies and backups increase exposure.
- **Unresolved technical questions:** Complete threat model, permitted sensitivity, signer/device compromise and future profile downgrade protections.
- **Affected questions:** Q01, Q15, Q16, Q17, Q18, Q21, Q26.
- **Required experiments:** E01; later E10/E13/E14/E15. E16 is a future separately scoped stronger-profile investigation.
- **Approval boundaries:** Q01 remains BLOCKER; no FS/PCS claim, security certification or waiver of cryptographic validation.

## PO-003

- **Date:** 2026-10-11
- **Exact decision:** Target seven days of recipient offline operation, with ten days of test relay/blob retention.
- **Requirements:** These are experimental objectives, not public-network guarantees. Recover eligible messages when required copies survive within tested assumptions. Account for up to two days of NIP-17 backdating and document clock skew. Use durable local outbox, retries and reconciliation. Relay OK proves neither retention nor receipt. All-copy loss must report unavailable or incomplete recovery. Report accelerated simulations separately from real-duration tests.
- **Rationale:** Set measurable availability objectives without imposing a central relay or storage operator.
- **Consequences:** H=7 days and test relay/blob R=10 days are approved experiment parameters. J=2 days and candidate S=1 day remain explicit lab assumptions; retry/download grace and arrival-versus-created_at eviction need review.
- **Accepted risks:** Arbitrary public relays may refuse/delete; required attachment copies may disappear. Seven-day global delivery is not guaranteed.
- **Unresolved technical questions:** Retention model, clock/skew/grace, pagination, restoration, surviving-copy and soak evidence.
- **Affected questions:** Q03, Q10, Q12, Q13, Q14, Q18, Q19, Q25.
- **Required experiments:** Later E07/E09/E10/E11; E03/E04 provide inputs only. E01–E06 do not prove a seven-day objective.
- **Approval boundaries:** Q13 remains BLOCKER. No operational SLA, archive guarantee or real-duration evidence inferred from simulation.

## PO-004

- **Date:** 2026-10-11
- **Exact decision:** Support parallel business decisions from multiple authorized devices.
- **Superseded recommendation:** The single-active-business-decision-authority proposal in NBDP-004 is rejected as the required v0.1 end-state. It is retained as historical reasoning, not a fallback implementation permission.
- **Requirements:** No mandatory coordinator, Satflux or Evolu dependency, or continuous-online assumption. Devices act concurrently and reconcile. Separate technical facts from business decisions. Compatible actions converge deterministically; contradictions are detected, explained and recoverable, never resolved silently by latest timestamp. Duplicates must not repeat business effects. Old cached messages do not create authority for revoked/unauthorized devices. Shared account secrets do not identify distinct devices. State partition and compromise limits explicitly.
- **Required investigation:** Per-device keys; delegated authorization; signed grants/revocations; device versus organization identity; conflict representation and deterministic merge; causal decision relationships; operation IDs/idempotency; offline authority freshness; convergence; irreconcilable conflicts. CRDTs alone do not supply authorization, revocation or safe non-idempotent accounting effects.
- **Rationale:** Real organizations require concurrent, intermittently connected authorized participants without a compulsory operator.
- **Consequences:** A design-only comparison and candidate model are required in [multi-device-authority-design.md](../research/multi-device-authority-design.md). Global once-only non-idempotent effects across disconnected sinks remain an explicit limitation; no silent single-writer downgrade.
- **Accepted risks:** Partition-delayed revocation and incompatible decisions require conservative handling and later security/interop evidence. Acceptance of a direction does not accept a particular revocation rule.
- **Unresolved technical questions:** Grant trust root/scopes, expiry, observed revocation versus backdated claims, authorization-log forks, causal reconciliation, recovery and effect-domain boundaries.
- **Affected questions:** Q02, Q04, Q11, Q12, Q15, Q16, Q17, Q26.
- **Required experiments:** Later E08/E09/E12/E13/E14, optionally E16 for a different device encryption profile. E01–E06 cannot resolve Q15.
- **Approval boundaries:** Q15 remains BLOCKER until concrete design and independent concurrency tests pass. Unsafe fully decentralized effect requirements must be reported as blockers with alternatives, not weakened.

## PO-005

- **Date:** 2026-10-11
- **Exact decision:** Defer the optional independently verifiable signed-document profile.
- **Requirements:** Preserve authenticated encrypted transport, correct sender/recipient validation, exact-byte cryptographic commitments, authenticated receipt assertions and the distinction between key authentication and legal/business authority. Unsigned rumors and hashes are not portable signatures. Exporting a Nostr message does not automatically confer legally recognized signature status. Preserve future profile extensibility.
- **Rationale:** Avoid adding an unnecessary proof mechanism to the initial scope while retaining baseline integrity/authenticity.
- **Consequences:** Portable document/receipt proof and its vectors are deferred. Q05 remains RFC_REQUIRED for precise baseline disclosure and extension boundaries; a deferred optional mechanism is not an implemented capability.
- **Accepted risks:** Baseline exported document bytes/digests/rumors do not provide the deferred independent document-signature proof.
- **Unresolved technical questions:** Future signed-byte domain, canonicalization, signer/context binding, deniability tradeoff and legal interpretation.
- **Affected questions:** Q05, Q09, Q11, Q17, Q26.
- **Required experiments:** E01/E02/E05/E06 retain baseline validation; E08 remains required for receipt assertions. Portable-proof portions of E14 are deferred.
- **Approval boundaries:** No new signature algorithm or portable-proof implementation is authorized. Authorization-log signatures, if later specified, serve device authority and are not document signatures.

## PO-006

- **Date:** 2026-10-11
- **Exact decision:** Cryptographic and interoperability blockers remain open until demonstrated by reproducible evidence.
- **Requirements:** Q01, Q08, Q13, Q15 and Q27 stay BLOCKER. Each must identify what PO approval resolved and what remains unverified. No production SDK implementation.
- **Rationale:** Product scope approval cannot substitute for safe cryptographic bytes, independent runtime compatibility or operational/concurrency evidence.
- **Consequences:** Conditional architecture acceptance is distinct from implementation readiness. Experiment status PASS requires all mandatory criteria; failures and unexecuted checks remain visible.
- **Accepted risks:** Experimental candidates may fail; experiments are synthetic and isolated, and are not a release/security approval.
- **Unresolved technical questions:** Full threat model; exact attachment bytes; retention/recovery; parallel authority; kind 15 ambiguity.
- **Affected questions:** Q01, Q08, Q13, Q15, Q27; other Q identifiers retain their classifications.
- **Required experiments:** E01–E06 authorized now; later applicable E07–E15 and security/RFC review are separate gates.
- **Approval boundaries:** Test-only keys, local infrastructure and disposable data only. No Satflux changes, production credentials/relays/databases, deployment, new repository/NIP/kind, release or automatic PR merge. Work uses `research/po-decisions-e01-e06` and a reviewable PR to `main`.

## Experiment identifier reconciliation

NBDP-005 §6 labels envelope exchange E01 and validation E02, while the expressly authoritative NBDP-004 plan assigns **E01 = independent NIP-44/full validation** and **E02 = envelope exchange**. Preserve the canonical meanings and dependency graph: validation E01 runs before exchange E02. Both requested scopes are covered under those original IDs, with cross-references in results; no experiment is silently renumbered.

## Technical gates retained

| Question | What approval resolves | What remains required |
| --- | --- | --- |
| Q01 | FS/PCS not mandatory for baseline | Complete security review, sensitivity/endpoint/metadata policy and applicable tests |
| Q08 | Isolated safe AES-GCM candidate testing permitted | Exact bytes/encoding/AAD, independent vectors, producer conformity and security review |
| Q13 | H=7/R=10 experimental objective | Actual retention/recovery evidence, skew/grace and separate real-duration soak |
| Q15 | Parallel decentralized decisions required; single-active-authority rejected | Concrete per-device authority/conflict/effect design, reviewed freshness/revocation and E08/E09/E12/E13 |
| Q27 | Existing kind 15 candidate testing, no thumbnails | Independent producer/consumer bytes and explicit ambiguity disposition; no silent NIP rewrite |

No question changes classification solely because of these approvals. The current count remains DECIDED 3, RFC_REQUIRED 12, EXPERIMENT_REQUIRED 7, BLOCKER 5.
