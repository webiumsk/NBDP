# Independent architecture review — NBDP-005

**Date:** 2026-10-11. **Scope:** Documentation and design review, separate from experiment implementation. This is not a cryptographic audit, legal review, normative wire approval or SDK authorization. The review applies the repository's `protocol-review` skill to the [PO decisions](../decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md), [ADR](../../adr/0001-transport-selection.md), [boundaries](transport-boundaries.md), [risk register](architecture-risk-register.md), [canonical experiments](required-experiments.md) and [multi-device design](multi-device-authority-design.md).

`docs/PROJECT_STATE.md` and `docs/ROADMAP.md` were absent at the start of this review. This review uses the explicit NBDP-005 instructions and retained [NBDP-004 baseline](https://github.com/webiumsk/NBDP/tree/00a5bfbb5656f2a82c0fb9a746c5137c9ea7f3ce) rather than inventing prior governance decisions.

## Approval accuracy and architecture conflicts

| Decision | Review result | Boundary that remains open |
| --- | --- | --- |
| PO-001 | Option B's conditional direction is accurately recorded. ADR status explicitly excludes exact bytes, demonstrated kind 14/15 compatibility, SDK, release and production use. | Independent application/client evidence and normative review remain necessary; no new NIP/kind is authorized. |
| PO-002 | The approved baseline omits mandatory FS/PCS and states historical exposure and non-retroactive rotation. | Q01 is still BLOCKER; accepted product tradeoff is not complete threat-model approval. |
| PO-003 | H=7/R=10 are experimental targets, with candidate skew and timestamp backdating qualified. | Q13 requires retention/recovery evidence and distinct accelerated versus real-duration results; no public-relay guarantee follows. |
| PO-004 | Earlier single-active-authority recommendation is explicitly superseded. Concurrent per-device decisions, causal conflict detection and partition limits are required. | Q15 remains BLOCKER; the design is a candidate with unresolved authority freshness, delivery and effects. |
| PO-005 | Portable document proof is deferred, while baseline transport authentication, commitments and receipt assertions remain. | Current baseline acceptance criteria must not inadvertently require the deferred signature mechanism. |
| PO-006 | All five designated blockers remain BLOCKER; Product approval is separated from evidence gates. | No production SDK gate is passed by documentation or partial experiments. |

The revised direction is consistent with permissionless participation and independently selectable relays, hosts and signers. A locally enrolled organization-admin key is an authority trust anchor, not a mandatory central service or global registry. Its possession still proves key control, not legal company representation.

The identifier discrepancy is handled correctly: the canonical plan defines **E01 as cryptography/full validation** and **E02 as envelope exchange**, whereas NBDP-005's descriptive headings reverse these labels. Recording this explicitly preserves the original identifiers and validation-before-exchange dependency; no silent renumbering is appropriate.

## Findings and required clarifications

| Finding | Severity / question | Evidence and required disposition |
| --- | --- | --- |
| Historical execution wording can be read as current | Documentation / Q04,Q06 | The ADR's retained evidence section says no runtime experiment or key generation occurred. Qualify that sentence as NBDP-004; NBDP-005 must link actual results and disclose partial/unexecuted checks separately. |
| Deferred proof retains old acceptance wording | Documentation / Q05 | The risk register's Q05 originally retains exported-proof and signature-negative criteria after deferral. Split current baseline disclosures from future, separately authorized signed-profile criteria. Do not remove baseline authenticity/integrity checks. |
| Decision scope could accidentally separate contradictory outcomes | Security design / Q11,Q15 | The proposed operation key contains an `action`; accept/reject must be alternative outcomes of the same document-review action, not separate keys. Define that distinction explicitly before independent E12 tests. |
| Revocation cannot be universally immediate during partitions | Architectural blocker / Q15,Q17 | The design correctly identifies indistinguishable offline schedules. Product/security must choose a bounded-staleness policy and eligible provisional actions. An issuer-controlled timestamp cannot bypass known revocation or establish historical authorization. |
| Per-device delivery is not supplied by an organization grant | Architectural blocker / Q03,Q15,Q26 | Independently keyed devices need verified destination descriptors, enrollment/fanout and archive rules. Receiving a valid grant does not prove discovery completeness or possession of organization-addressed decryption keys. |
| Causal convergence does not make external effects once-only | Architectural blocker / Q12,Q15 | Replicated decision records cannot atomically commit disconnected accounting/payment sinks. Declare effect domains, require sink-local durable idempotency/reconciliation, and keep ambiguous irreversible outcomes visible. |
| Authority records need an exact standard signature profile | RFC dependency / Q02,Q15,Q17,Q26 | No signed-byte framing, scope grammar or token encoding is finalized. Specify domain separation, bounded chains/parents, trusted issuer, expiry, forks and recovery; do not substitute claimed organization identity for actual seal author. |

These are required clarifications or retained design blockers, not evidence that another carrier or new kind is necessary. No critical architecture conflict with PO-001–PO-006 was identified in the candidate design itself. Address documentation findings before treating the PR as ready for architectural review.

## Standards cross-check and backward compatibility

The pinned [NIP-59](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/59.md) leaves application messaging separately specified, defines unsigned rumors, requires empty kind 13 tags, and permits per-recipient copies. Its storage discretion prevents treating persistent kind 1059 as a retention guarantee. The design must preserve these transport boundaries while specifying application authorization; adding grants to seal tags would conflict with the selected candidate.

The pinned [NIP-44 limitations](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/44.md#limitations) explicitly exclude FS/PCS. PO-002 correctly accepts that limitation rather than claiming static-key rotation or deletion repairs prior exposure. A stronger future profile needs separate versioning and downgrade review.

The pinned [NIP-26](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/26.md) is unrecommended and constrains delegated event kind/time. It does not furnish the candidate's document/action scopes or partition-safe authority rules. The design appropriately investigates it without adopting it as a mandatory dependency. The report does not claim public relay support or runtime delegation interoperability.

Keeping authorization objects inside encrypted application messages does not introduce a new event kind. Ordinary NIP-17 clients may render envelope JSON as chat or ignore machine fields; this compatibility behavior still needs empirical evidence. Authority-log signatures would authenticate authorization/decision operations, not automatically supply the deferred portable document-signature profile or legal proof. Their reduced deniability for those specific objects needs disclosure and security review.

## Required positive and negative vectors

These are later RFC/E08/E09/E12/E13/E14 requirements, not tests executed in this review:

- Two independently keyed authorized devices make compatible decisions; all delivery permutations converge to one semantic outcome with both provenances.
- Accept/reject outcomes share the same review-operation scope and always produce an explicit conflict when causally concurrent.
- Concurrent resolutions, a late third head, missing parents, cycles and same-ID/different-bytes never silently select a timestamp winner.
- Wrong device, grant issuer, action/document scope, organization, revision, authority epoch and unsupported signature/token version reject or remain pending according to explicit rules.
- A known revocation blocks new authority from old messages; a hidden partitioned revocation produces only the approved provisional/freshness outcome. Backdated claims cannot upgrade that outcome.
- A root/device fork, rollback, expired checkpoint, restored stale backup or compromised old root cannot establish safe recovery merely by signing again.
- Crash after effect before receipt and fresh-wrap retries reuse one effect operation key; disconnected non-idempotent sinks demonstrate the duplicate-effect limitation rather than claiming global exactly once.
- Removed devices retaining plaintext or a copied account secret remain capable of disclosure; tests distinguish action revocation from secrecy or retroactive erasure.

## Required decisions and approval recommendation

Retain all canonical Q01–Q27 and E01–E16 identities. The architecture register remains DECIDED 3, RFC_REQUIRED 12, EXPERIMENT_REQUIRED 7, BLOCKER 5. In particular **Q01/Q08/Q13/Q15/Q27 remain BLOCKER**; E01–E06 do not resolve multi-device authority or seven-day availability.

Recommend continued conditional Option B research and review of the experimental PR after documentation corrections and independent result review. There is presently no architecture-review evidence requiring a new inner kind and no relay-level case for a new outer kind. Carrier suitability depends on actual E02/E06 evidence, not this recommendation.

RFC drafting can proceed for principles, identity/discovery and explicitly provisional envelope/commitment alternatives. Final attachment requirements, business-receipt concurrency and authority/revocation contracts require exact byte/security decisions and independent tests. No final normative profile, production SDK, deployment or release approval is recommended.

The next Product/security gate must decide authority freshness and eligible offline actions, revocation/fork recovery, effect-domain guarantees and permitted sensitivity of the no-FS baseline. Parallel writers must remain supported; deferring unsafe irreversible effects is not permission to silently revert to a single-writer protocol. Independent implementations must then prove E08/E09/E12/E13 and applicable E14 behavior before Q15 can close.

## Coordinator disposition after experimental execution

This disposition is recorded by the coordinating engineer, not a claim of a second independent architect approval. The historical ADR execution wording is now explicitly NBDP-004; Q05 current baseline criteria are distinct from the deferred signed extension; accept/reject are outcomes within one shared review action. Remaining authority/freshness/effect findings retain Q15 and related gates. Actual runtime statuses and independent QA/security remediation evidence are linked in the [validation summary](experimental-validation-summary.md). The architecture direction remains conditional; E02 is PARTIAL and E04/E06 are unexecuted.
