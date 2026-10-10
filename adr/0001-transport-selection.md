# ADR 0001: Transport selection for NBDP v0.1

- **Status:** Proposed
- **Work item:** NBDP-004
- **Date:** 2026-10-11
- **Decision owner:** Product Owner, with Protocol Architect and Security Reviewer
- **Recommendation:** Option B, conditionally; implementation is not approved
- **Confidence:** Moderate in architectural direction; low in demonstrated runtime interoperability
- **Canonical questions:** Q01–Q27 in [open-questions.md](../docs/research/open-questions.md)

## Context and scope

NBDP exchanges business documents between independent endpoints over Nostr. Satflux may implement the first integration, but no Satflux service, database, API, relay, key manager or approval process belongs to the protocol. The core provides no automatic government reporting or third-party document disclosure. A client may explicitly invoke separately configured compliance adapters; jurisdiction-specific requirements remain outside core conformance.

Participation uses user-controlled keys and interchangeable infrastructure. DNS ownership, government identifiers, a business directory, Peppol membership, one document syntax, one signer service, one relay or one blob host cannot be prerequisites. Permissionless participation does not require every independent operator to provide free or unrestricted storage. These are project constraints, not new claims about legal obligations or universal relay policy.

This decision selects a research and RFC direction. It does not approve exact wire bytes, allocate kinds, propose a NIP, select a production SDK, promise delivery, or declare interoperability. “Proposed controls” below are candidates for normative NBDP RFCs, not modifications to existing NIPs.

All four input reports were read in full:

- [Nostr landscape](../docs/research/nostr-landscape.md)
- [Transport comparison](../docs/research/transport-comparison.md)
- [Library evaluation](../docs/research/library-evaluation.md)
- [Canonical open questions](../docs/research/open-questions.md)

Supporting deliverables are [transport boundaries and preliminary threat model](../docs/research/transport-boundaries.md), [the complete question/risk register](../docs/research/architecture-risk-register.md), and [required experiments](../docs/research/required-experiments.md). The existing reports remain unchanged research inputs.

## Evidence and verification scope

The research NIP snapshot is **a79e21d90fce5465b50ef385dd368bba99ec4a0b**. This review re-read pinned NIP-17/44/59, nostr-tools message/wrap helpers, Rust gift-wrap validation, Blossom authorization and Marmot's README through GitHub. Other claims rely on the reports' pinned source inspections and locally retained specifications. Git remote HEAD refresh was unavailable in this workspace; this ADR makes claims about the pinned corpus, not a newly established latest upstream revision.

Specification facts, source-inspection observations, maintainer claims and architectural reasoning are kept separate. All reference URLs below pin commits; immutable IETF documents are RFC 5116 (January 2008) and RFC 9420 (July 2023). No runtime experiment, production relay change, cryptographic-key generation, deployment or compliance transmission occurred.

### Verification findings and qualifications

| Finding | Evidence | Architectural disposition / canonical questions |
| --- | --- | --- |
| B's central motivation is supported | [NIP-59][N59] explicitly leaves messaging applications separate; [NIP-17][N17] supplies chat/files but no business receipt protocol | Application semantics are needed for machine business interchange; Q06, Q07, Q11 |
| Kind 14 textual JSON is a plausible carrier, not proven business interoperability | [NIP-17 Chat Message][N17] requires plain text; no NBDP schema or machine-dispatch rule exists | Test textual envelope parsing, ordinary-chat rendering and collision behavior before committing carrier semantics; Q06, Q24 |
| Recipient metadata remains exposed in the outer event | [NIP-59 structure][N59]; NIP-17's “No Metadata Leak” wording is broader | Do not repeat broad anonymity claims; Q01, Q18, Q21 |
| Static ECDH is not forward-secret | [NIP-44 Limitations][N44] conflicts with a literal cryptographic reading of NIP-17's disappearing-message benefit | Expiration/deletion and static-key rotation do not retroactively protect history; Q01, Q17 |
| Passive network observers are different from relay operators | Earlier landscape groups their observations; this review assumes authenticated TLS for wss/https | Passive observers see traffic patterns/endpoints, not necessarily decrypted event tags/AUTH; TLS-terminating operators see application traffic. Architectural reasoning; Q01, Q18, Q21 |
| Seal expiration guidance is internally inconsistent | [NIP-59][N59] requires empty seal tags, while NIP-17 and later NIP-59 text suggest seal expiration tags | Initial profile omits disappearing-message features and preserves empty seal tags; no silent redefinition; Q04, Q07 |
| Kind 15 does not fix all interoperable file bytes | [NIP-17 File Message][N17] names aes-gcm/key/nonce but leaves key/tag/encoding/layout choices; thumbnails say same key/nonce | Attachment profile and vectors are blockers; omit thumbnails, never encrypt distinct plaintexts with a reused GCM key/nonce; Q08, Q27 |
| Encryption limit is not a deployment limit | [NIP-44][N44], [JavaScript][T44], [Rust][R44] support extended lengths; [legacy Go][G44] does not; [NIP-11][N11] has relay constraints | Both nested encryption inputs and complete frames need measurement. 16 KiB is an experiment candidate, not an adopted universal cap; Q07, Q10 |
| SDK helpers have different validation boundaries | [nostr-tools][T59] does not visibly verify outer signature first; [Rust][R59] does, but its inspected seal parser does not visibly check seal kind/empty tags | Define a complete profile validator rather than treating decryption success as acceptance; Q04 |
| Multi-recipient helpers may create different rumors | [nostr-tools NIP-17][T17] builds individual recipient sets; self-copy is mandatory in ordinary NIP-17 | Start with bilateral logical operations and one canonical rumor per operation, separately wrapped to peer and sender; sender-copy validation needs an explicit archive role; Q06, Q12, Q15 |
| Recovery hints cannot prove historical completeness against a hostile relay | [NIP-67][N67] covers matching stored events; [NIP-77][N77] reconciles retained sets | Hints are claims by an operator, not authenticated proof that nothing was deleted/withheld; timestamp ties and caps remain test cases; Q13, Q14 |
| Scores and support tables are not empirical results | Existing comparison scores are judgment; [library evaluation](../docs/research/library-evaluation.md) uses source/README evidence | Do not use scores to certify interoperability, maturity, retention or forward secrecy; Q06, Q08, Q10, Q14, Q19 |
| Monotonic receipt language was underspecified | No business state machine in [NIP-17][N17]; offline replicas can conflict | Separate accumulated technical facts from authorized business decisions; never resolve contradictory business receipts with latest timestamp; Q11, Q15 |
| Deletion/expiration are not retention or erasure guarantees | [NIP-09][N09], [NIP-40][N40], [NIP-59 storage discretion][N59] | Define an offline operational contract; no guaranteed erase, delivery or archive claim; Q01, Q13 |

The research therefore supports B as a direction, but not approval to implement it. Missing evidence includes independent envelope/file exchange, recipient-only relay access under mixed filters, complete-frame budgets, durable recovery, shared-state failures, signer behavior and current BUD runtime conformity.

## Alternatives and decision matrix

A uses existing NIP-17 conventions without common business semantics. B adds a public versioned application specification inside existing encryption. C has three forms: C1 is a profile NIP with B's existing kinds; C2 adds an inner rumor kind; C3 changes relay-visible kinds/messages. C1 and B may have identical wire architecture. Formal publication is separate from kind allocation.

All comparisons are architectural reasoning from [NIP-01][N01], [NIP-17][N17], [NIP-44][N44], [NIP-59][N59] and pinned implementation evidence, not measured scores.

| Criterion | A | B | C1 / C2 / C3 |
| --- | --- | --- | --- |
| Privacy/confidentiality | Existing encryption, no business privacy policy | Same encryption plus bounded private metadata rules; no stronger underlying cryptography | C1/C2 same cryptography; C3 may expose traffic class |
| Sender/recipient authentication | Key authentication; no business authority profile | Explicit validation and pinned endpoint/authority policy | C1 codifies B; C2 can clarify dispatch; no kind establishes company authority |
| Metadata leakage | Recipient tag, timing/size, AUTH and blob correlation | Same residual channels; envelope stays private | C1/C2 preserve outer privacy; C3 adds classification risk |
| Offline delivery | Storage-dependent; manual retries | Durable outbox/reconciliation semantics can be shared, still conditional | All need retention/state evidence; new kinds do not supply durability |
| Relay interoperability | Existing 1059/10050 policies | Same outer transport; AUTH and limits still vary | C1/C2 may reuse relays; C3 needs deployment |
| Attachments | Kind 15 exists; byte ambiguity | Profile can specify commitments and file bytes after Q08/Q27 | C1/C2 still need file profile; a parallel kind is not a nonce fix |
| Receipts | Ordinary replies/reactions | Bound authenticated technical/business actions | C1 standardizes; C2 supplies dispatch; C3 not needed for private receipts |
| Business-document semantics | No independent machine contract | Explicit formats, logical IDs, revisions, errors | C1 equivalent semantics; C2 dedicated purpose if needed |
| Complexity | Low transport work, divergent business work | Moderate transport reuse plus substantial protocol/state work | C1 editorial cost; C2 parser/registry work; C3 relay rollout |
| Existing library support | Chat/files unevenly supported | Crypto helpers exist; complete validator/application layer absent | C2 needs inner-kind support; C3 needs relay support |
| Independent client interoperability | Chat transport possible; business interpretation unspecified | Achievable by shared RFCs and corpus, unproven | Formal NIP alone does not prove independent exchange |
| Deployment | Existing DM infrastructure | New application clients, same relay-visible kinds | C1 no wire rollout; C2 client rollout; C3 infrastructure rollout |
| Long-term maintainability | Business conventions drift | Versioned application layer decoupled from integrations | C1 could improve discoverability; C2/C3 expand compatibility obligations |

**Selected proposed direction: B.** A fails the project's independent machine business-interoperability objective. There is presently no demonstrated reason to add inner kinds and no relay-level requirement for new outer kinds. NIP-78's storage kinds explicitly discourage generic cross-application interchange, so they are not a substitute carrier [NIP-78][N78]. NIP-89 handler announcements do not resolve encrypted capability negotiation [NIP-89][N89].

## Selected architecture and profile scope

Propose a bilateral v0.1 transport profile:

1. Existing NIP-44 v2 inside signed NIP-59 seals and persistent kind 1059 wraps, routed only through each intended identity's signed kind 10050 inbox list.
2. Kind 14 textual envelopes for protocol messages, manifests, capabilities, errors and receipts; kind 15 only for its existing encrypted-file meaning. A document operation may correlate both, without depending on arrival order.
3. One authoritative application envelope per operation; a kind 15 file message does not create an independent invoice import or business decision. Correlation and duplicate commitment agreement need RFC rules.
4. The same logical rumor is separately wrapped for recipient and sender. A sender copy is archival evidence, not a second incoming business operation. Peer keys and private commitments stay inside encryption; outer tags contain only permitted routing metadata.
5. Original document bytes remain format-neutral opaque bytes. Small inline content may eventually be allowed under agreed limits; large documents use locally encrypted blobs and private manifests.
6. Blossom/NIP-B7 is the preferred storage adapter candidate, with independently selectable hosts and exact ciphertext mirroring. No particular host or cloud provider is required.
7. Authenticated application receipts record scoped assertions, not legal delivery, accounting approval, debt acknowledgment or payment. Client business actions require separately authorized policy.
8. Local clients implement durable queues, archives and idempotency mechanisms; the protocol specifies observable behavior, not a mandatory database, daemon, server or accounting system.
9. Compliance adapters are opt-in application integrations with explicit destination/purpose policy. Their failure does not make NBDP transport fail or silently cause core disclosure.

These are proposed selections. Q06/Q24 experiments may invalidate the kind 14 carrier or the combination; Q08/Q27 block file-profile implementation. An envelope-only prototype after a later experiment authorization cannot be presented as proving the full document architecture.

## Security assumptions and consequences

Assume standard cryptographic primitives implemented correctly through reviewed libraries, fresh randomness, authenticated wss/https links, correct full validation, uncompromised intended endpoints/signers and locally trustworthy contact enrollment. No current SDK or full profile is declared audited. Independent operators remain untrusted for plaintext secrecy but indispensable for availability. An authorized recipient/signing service can disclose plaintext; the architecture cannot prevent that.

### Forward secrecy and alternative security profiles

Propose **not making cryptographic forward secrecy mandatory in the initial v0.1 baseline**, subject to explicit Product Owner/security approval of Q01. Retained ciphertext and sender self-copies expose historical documents after relevant key compromise. Deleting relayed copies or rotating static keys does not retroactively provide forward secrecy [NIP-44][N44].

MLS supplies standardized asynchronous group FS/PCS, conditioned on secret deletion and processed key updates; its epoch/membership state and delayed-message retention add recovery/implementation complexity [RFC 9420, §§9.2, 15.3, 16.6][MLS]. Marmot's pinned specification uses MLS with Nostr identity [Marmot][MSPEC], but this review has not established independent NBDP-compatible runtime implementations. A future optional security profile requires separate evidence for device admission, offline recovery, key deletion, archive policy and downgrade prevention. If Q01 makes FS mandatory, revisit the baseline now rather than labeling static ECDH forward-secret. This is a product/security tradeoff, not evidence that added complexity makes MLS insecure.

### Portable proof

Baseline authentication is seal authentication to the peer plus exact document commitments. Neither a naked unsigned rumor nor a document digest is a portable signature or company authorization proof [NIP-59][N59], [NIP-01][N01]. Recommend a separately versioned optional signed-document profile using an existing standard signature algorithm, with precise signed bytes/domain separation, identity context, verification and canonicalization policy. Preserve original bytes; never silently normalize them before checking a digest. Legal recognition is explicitly not asserted. Signing deliberately changes deniability for that object; Q05 remains RFC_REQUIRED.

### Multi-device, replay and availability boundaries

Recommend technical receipts accumulate authenticated assertions of facts; validating their issuer and bindings does not prove remote honesty. Contradictory business decisions produce a deterministic conflict/quarantine outcome, not a timestamp winner. For v0.1, propose one active business-decision authority per action scope, with observers permitted, and idempotent effects within each explicitly coordinated consumer domain. Two disconnected clients sharing a key cannot guarantee one global effect. Device revocation cannot distinguish possession of the same account secret; independent device keys/delegation require Q17/Q26 rules. Q15 remains BLOCKER until scope/authority and runtime evidence are approved.

Use stable application IDs, exact operation commitments, durable replay records and at-least-once attempts. New wrappers do not create new business operations. Restore of stale replay records suspends effects until reconciliation. Receipt loss leaves sender outcome unknown; retry limits may terminate attempts without claiming rejection. These are proposals grounded in [NIP-01 IDs/OK][N01], [NIP-17][N17] and [NIP-59 wrapping][N59].

Q13 must set an offline horizon and retention assumptions; a lab candidate is 7 days offline, 10 days retention and a 2-day timestamp-jitter window plus agreed skew. These are proposed experiment parameters, not Nostr guarantees, legal archive durations or approved service levels. No surviving copies means no recovery, regardless of kind selection.

## Question classification and gates

Classification indicates the next decisive work, not that subordinate research is unnecessary. DECIDED means a narrow present-scope exclusion supported by evidence; it does not close future standardization needs. Every canonical item is mapped in the [risk register](../docs/research/architecture-risk-register.md).

| Questions | Classification | Required gate |
| --- | --- | --- |
| Q01 | BLOCKER | G0: accepted threat model/FS residual risk |
| Q02, Q03, Q04, Q05 | RFC_REQUIRED | G1: identity, discovery, validation and proof contracts |
| Q06 | EXPERIMENT_REQUIRED | G2: independent carrier experiment |
| Q07 | RFC_REQUIRED | G1: serialization/version/extension contract |
| Q08 | BLOCKER | G1/G2: exact file crypto profile and vectors |
| Q09 | RFC_REQUIRED | G1: exact commitments and revisions |
| Q10 | EXPERIMENT_REQUIRED | G2: complete nested-frame bounds |
| Q11, Q12 | RFC_REQUIRED | G1/G2: receipt/replay contracts and evidence |
| Q13 | BLOCKER | G0/G2: offline objective and retention evidence |
| Q14 | EXPERIMENT_REQUIRED | G2: pagination/backdating reconciliation |
| Q15 | BLOCKER | G0/G1/G2: business authority and concurrency scope |
| Q16 | EXPERIMENT_REQUIRED | G2: signer conformance and trust |
| Q17 | RFC_REQUIRED | G1/G2: continuity and compromise recovery |
| Q18, Q19 | EXPERIMENT_REQUIRED | G2: relay policy/privacy and blob interchange |
| Q20, Q21 | RFC_REQUIRED | G1/G2: storage auth and metadata policy |
| Q22, Q23 | DECIDED | G0: no mandatory legacy storage or present NIP proposal |
| Q24 | EXPERIMENT_REQUIRED | G2: dedicated-inner-kind necessity |
| Q25 | DECIDED | G0: no present outer-kind/relay extension |
| Q26 | RFC_REQUIRED | G1/G2: local continuity/private negotiation; wider NIP work deferred |
| Q27 | BLOCKER | G1/G2: kind 15 ambiguity cannot be silently resolved |

**Counts: DECIDED 3; RFC_REQUIRED 12; EXPERIMENT_REQUIRED 7; BLOCKER 5.**

G0 is Product Owner/security architecture-scope approval. G1 is review of exact normative RFC candidates, including independent security review. G2 is the required isolated runtime/conformance evidence. G3 is a separate SDK implementation authorization after relevant G0/G1/G2 criteria. No approval is implied by creating these documents.

## RFC readiness assessment

Drafting is ready now; finalizing safe interoperable RFCs and SDK implementation are not ready. Outlines and unresolved alternatives may be written immediately. An experiment needs a frozen, explicitly provisional wire candidate rather than two implementations guessing their own bytes.

| Proposed RFC work area | Required inputs | Unresolved dependencies | Security requirements / required vectors | May drafting begin now? |
| --- | --- | --- | --- | --- |
| R01 Principles and terminology | Project principles, this ADR, threat model | Q01/Q13/Q15 scope approval | Name key vs organization, fact vs decision, core vs adapter; terminology/state examples | Yes; security claims remain conditional |
| R02 Identity and discovery | NIP-01/05/17/65, trust policy | Q02/Q03/Q17; E03/E14 | Signed inbox validation, no arbitrary fallback/alias substitution, TOFU and out-of-band states; stale/conflicting/forged list vectors | Yes; recovery and cache policies need review/tests |
| R03 Encrypted envelope | NIP-17/44/59, validation pipeline | Q04/Q06/Q07/Q10/Q24; E01/E02/E04 | Exact UTF-8/schema/ID/recipient checks, bounded parsing, no downgrade; malformed rumor and version vectors | Yes as alternatives; carrier cannot be finalized before experiments |
| R04 Document transport and commitments | Format-neutral bytes, proposed manifests | Q09/Q12/Q13; E07/E09/E11 | Exact-byte hashes, revision/correlation and operation identity, retention/error semantics; digest/multipart/order/revision vectors | Yes; numeric limits/availability assumptions unresolved |
| R05 Encrypted attachments | NIP-17 kind 15, GCM and BUD evidence | Q08/Q19/Q20/Q21/Q27; E05/E06/E07 | Key/nonce/tag/layout/encoding and no thumbnails; cross-crypto and kind 15 vectors | Outline/comparison only; normative byte selection blocked |
| R06 Receipts and delivery state | Proposed facts/decision model | Q11/Q12/Q15; E08/E09/E12 | Endpoint/ID/hash/version/action binding, conflict and no ACK loops; reorder/conflict/crash/restore vectors | Yes; multi-device authority approval required |
| R07 Key management | NIP-46/07/49/55, pinning | Q01/Q15/Q16/Q17; E13/E14 | Local custody, session trust, revocation, recovery with no retroactive FS; rotation/rollback/signer substitution vectors | Yes for baseline; advanced delegation/FS needs more research |
| R08 Extensions and capabilities | Version model and private messaging | Q07/Q22/Q23/Q24/Q25/Q26; E02/E14/E15 | Authenticated offers, replay/freshness, unknown mandatory features, privacy and downgrade policy; offer/response replay vectors | Yes; no new kinds or public capability registry |

Optional portable document signatures can be a later independently reviewed profile under R04 or a separate RFC after Q05. A future FS profile needs additional research and conditional E16; it is not required for drafting the proposed baseline. Research, experiments and approval remain distinct activities.

## Rejected/deferred alternatives and revisit conditions

A is rejected for the complete automated protocol, while remaining a useful human exchange comparison. C1 is deferred as a publication decision; it could codify the same architecture later. C2 is deferred pending Q06/Q24 carrier evidence. C3 has no demonstrated relay-level requirement and is excluded from this stage (Q25). Mandatory NIP-96, NIP-78 interchange, custom cryptography, automatic compliance reporting and centrally issued identities are excluded.

Revisit the architecture if FS becomes mandatory; independent kind 14/15 exchange cannot preserve the required semantics; exact safe kind 15 bytes conflict with deployed conventions; required manifests cannot fit interoperable bounds; offline objectives require unsupported infrastructure; single-authority multi-device scope is unacceptable; or independent implementations cannot agree on validation/recovery. A runtime failure may call for RFC changes before kind changes; failure of retention does not by itself justify a new event kind.

## Product Owner approval and stopping point

The Product Owner must explicitly approve:

1. The conditional B direction and bilateral kind 14 plus existing kind 15 scope, pending experiments.
2. Q01: baseline without FS/PCS, the disclosed recipient/traffic risks and permitted sensitivity/use cases.
3. Q13: a measurable offline horizon, retention assumptions, retry deadlines and failure outcomes.
4. Q15: single business-decision authority scope, deterministic conflict quarantine and limits of disconnected multi-device effects.
5. Optional portable proof, its deniability implications, and Q05 drafting scope.
6. Attachment risk treatment: omit thumbnails, resolve Q08/Q27 before file implementation; do not choose byte encodings merely by preference.
7. The independent conformance/security experiment budget and RFC review gates before SDK work.

Approval of drafting does not accept the ADR, waive blockers, authorize production code, or establish legal signature/delivery recognition. Status remains **Proposed**. Stop at documentation; no experiments, deployments, integrations, upstream NIP proposals or SDK implementation are authorized by this ADR.

[NREADME]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/README.md
[N01]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/01.md
[N05]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/05.md
[N07]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/07.md
[N09]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/09.md
[N11]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/11.md
[N17]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/17.md
[N40]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/40.md
[N42]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/42.md
[N44]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/44.md
[N46]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/46.md
[N49]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/49.md
[N55]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/55.md
[N59]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/59.md
[N65]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/65.md
[N67]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/67.md
[N77]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/77.md
[N78]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/78.md
[N89]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/89.md
[N94]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/94.md
[N96]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/96.md
[N98]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/98.md
[NB7]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/B7.md
[NEE]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/EE.md
[T17]: https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip17.ts
[T59]: https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip59.ts
[T44]: https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip44.ts
[R59]: https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip59.rs
[R44]: https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip44/v2.rs
[G44]: https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/nip44/nip44.go
[NDK46]: https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/core/src/signers/nip46/index.ts
[STR]: https://github.com/hoytech/strfry/blob/4cd3cf64850caf47dda46c2a2abbbf3525a64d10/strfry.conf
[RSR]: https://github.com/scsibug/nostr-rs-relay/blob/b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4/config.toml
[MSPEC]: https://github.com/marmot-protocol/marmot/blob/7fabb81b3ed6e2fffeb1b267a0d2ae92b0ab2c89/README.md
[AUDIT]: https://github.com/paulmillr/nip44/blob/ce63c2eaf345e9f7f93b48f829e6bdeb7e7d7964/audit-2023.12.pdf
[B01]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/01.md
[B02]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/02.md
[B03]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/03.md
[B04]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/04.md
[B06]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/06.md
[B11]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/11.md
[B12]: https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/12.md
[MLS]: https://www.rfc-editor.org/rfc/rfc9420.html
[GCM]: https://www.rfc-editor.org/rfc/rfc5116.html
