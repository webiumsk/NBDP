# NBDP architecture risk and decision register

**Status:** Technical review register after NBDP-005 Product Owner decisions, 2026-10-11. Canonical IDs/descriptions originate in [open-questions.md](open-questions.md). All Q01–Q27 are retained; no question is silently merged, dropped or renumbered. [ADR 0001](../../adr/0001-transport-selection.md) is Conditionally Accepted — Architecture Direction Only. [PO-001–PO-006](../decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md) approve scope without closing any question.

This register classifies each question exactly once by its next decisive requirement:

- **DECIDED:** a narrow present-architecture decision with adequate evidence; deferred future research is not declared solved.
- **RFC_REQUIRED:** interoperable behavior must be specified and reviewed before implementation; runtime checks may follow.
- **EXPERIMENT_REQUIRED:** runtime/conformance evidence is decisive; a provisional RFC candidate may be needed to conduct it.
- **BLOCKER:** missing approval or evidence prevents architecture approval for the affected scope or safe implementation. A proposed mitigation does not close it.

Priority P0/P1/P2 follows the original meaning. Q13/Q15 are promoted from P1 to P0 because availability/authority scope affects approval; Q27 is promoted from P2 to P0 because existing kind 15 ambiguity affects the initial file profile. These changes preserve the original question, not redefine it.

## Gates and counts

| Gate | Meaning | Approval/evidence |
| --- | --- | --- |
| G0 | Architecture/security/product scope | Product Owner and Security Reviewer approve threat model, offline objectives, multi-device authority scope and risk acceptance |
| G1 | Normative candidate contract | RFC authors and independent reviewers specify exact bytes, checks, failure/state/authority semantics and vectors |
| G2 | Isolated runtime/conformance evidence | Independent clients/libraries and relay/host policies pass [required experiments](required-experiments.md); privacy/failure results disclosed |
| G3 | SDK implementation authorization | Separate Product Owner authorization after relevant G0/G1/G2 criteria; SDK authorization not granted; experimental evidence recorded separately |

**DECIDED: 3; RFC_REQUIRED: 12; EXPERIMENT_REQUIRED: 7; BLOCKER: 5; total: 27.**

A Product Owner cannot waive an unsafe nonce construction or falsely declare runtime interoperability; approval selects scope/risk objectives while technical evidence still has to pass. Ready-to-draft is separate from safe-to-implement.

## Index

| Question | Priority | Classification | Responsible future role | Target decision gate |
| --- | --- | --- | --- | --- |
| [Q01](#q01) — Privacy threat model and forward secrecy | P0 | BLOCKER | Product Owner + Security Reviewer | G0, before architecture approval; conditional E16 |
| [Q02](#q02) — Counterparty and organizational authority | P0 | RFC_REQUIRED | Identity RFC Editor + Security Reviewer | G1 identity contract; G2 before SDK |
| [Q03](#q03) — Inbox discovery without a required indexer | P0 | RFC_REQUIRED | Identity RFC Editor + Interoperability Engineer | G1, E03 at G2 |
| [Q04](#q04) — Full authentication and validation order | P0 | RFC_REQUIRED | Envelope RFC Editor + Security Reviewer | G1 contract; E01/E02/E08 at G2 |
| [Q05](#q05) — Exportable document and receipt proof | P0 | RFC_REQUIRED | Document RFC Editor + Cryptography Reviewer | G0 optional scope; G1 signed profile before use |
| [Q06](#q06) — Carrier selection and envelope/file combination | P0 | EXPERIMENT_REQUIRED | Protocol Architect + Interoperability Engineer | G2 before final carrier approval |
| [Q07](#q07) — Versioning, serialization and downgrade policy | P0 | RFC_REQUIRED | Envelope/Extensions RFC Editors | G1; E01/E02/E04/E14 at G2 |
| [Q08](#q08) — Exact encrypted-file cryptographic bytes | P0 | BLOCKER | Cryptography Reviewer + Attachments RFC Editor | G1/G2; blocks attachment implementation |
| [Q09](#q09) — Hashes, file commitments and revisions | P0 | RFC_REQUIRED | Document RFC Editor | G1; E06/E07/E09 at G2 |
| [Q10](#q10) — Envelope/file limits and resource exhaustion | P0 | EXPERIMENT_REQUIRED | Interoperability Engineer + Performance/Security Reviewer | G2 before limit finalization |
| [Q11](#q11) — Authenticated receipts and outcome meanings | P0 | RFC_REQUIRED | Receipts RFC Editor + Business Workflow Architect | G1; E08/E12 at G2 |
| [Q12](#q12) — Replay, duplicates and restored state | P0 | RFC_REQUIRED | Receipts RFC Editor + Storage/Workflow Architect | G1; E09/E12 at G2 |
| [Q13](#q13) — Offline horizon and durable availability | P0 | BLOCKER | Product Owner + Operations/Storage Architect | G0 target; G2 evidence before operational SDK claims |
| [Q14](#q14) — Backdated and capped history reconciliation | P1 | EXPERIMENT_REQUIRED | Relay/Recovery Engineer | G2 before recovery contract finalization |
| [Q15](#q15) — Concurrent devices and business receipt authority | P0 | BLOCKER | Product Owner + Workflow/Distributed Systems Architect | G0/G1/G2; blocks safe multi-device effect implementation |
| [Q16](#q16) — Signer trust, sessions and capability conformance | P1 | EXPERIMENT_REQUIRED | Signer Integration Engineer + Security Reviewer | G2 before supported signer claim |
| [Q17](#q17) — Rotation, compromise recovery and archive decryption | P1 | RFC_REQUIRED | Key Management RFC Editor + Security Reviewer | G1; E14 at G2 |
| [Q18](#q18) — Relay AUTH privacy and anti-spam behavior | P1 | EXPERIMENT_REQUIRED | Relay Interoperability Engineer + Privacy Reviewer | G2 before protected-inbox/privacy claim |
| [Q19](#q19) — Blob interchange, fallback and retention | P1 | EXPERIMENT_REQUIRED | Storage Interoperability Engineer | G2 before attachment availability claim |
| [Q20](#q20) — HTTP storage authorization and token replay | P1 | RFC_REQUIRED | Storage Auth RFC Editor + Security Reviewer | G1; E07 at G2 |
| [Q21](#q21) — Host and network metadata privacy | P1 | RFC_REQUIRED | Privacy RFC Editor + Client Security Engineer | G1; E15 at G2 |
| [Q22](#q22) — Mandatory legacy NIP-96 compatibility | P1 | DECIDED | Protocol Architect | G0 present-scope decision; future adapter gate |
| [Q23](#q23) — Formal NIP for reusable business profile | P2 | DECIDED | Protocol Architect + Standards Editor | G0 scope; later independent-evidence review |
| [Q24](#q24) — Need for a dedicated inner rumor kind | P2 | EXPERIMENT_REQUIRED | Interoperability Engineer + Protocol Architect | G2 carrier decision; later separate standardization gate |
| [Q25](#q25) — New outer kind or relay-level recovery extension | P2 | DECIDED | Relay Architect + Standards Editor | G0 present-scope decision; future extension review |
| [Q26](#q26) — Continuity and encrypted capability negotiation | P2 | RFC_REQUIRED | Extensions + Key Management RFC Editors | G1; E14 at G2 |
| [Q27](#q27) — Kind 15 profile clarification and thumbnail ambiguity | P0 | BLOCKER | Attachments RFC Editor + Cryptography Reviewer | G1/G2; blocks safe initial attachment profile |

## Detailed issue records

### Q01

**Privacy threat model and forward secrecy**

- **Priority:** P0
- **Classification:** BLOCKER
- **Relevant specifications and evidence:** [NIP-44 Limitations][N44], [NIP-59 outer structure][N59]; ADR FS analysis. Static ECDH lacks FS/PCS and exposes recipient routing metadata.
- **Proposed decision or approach:** PO-002 accepts no mandatory FS/PCS baseline; publish exact exclusions and permitted sensitivity. This resolves the product tradeoff, not complete threat-model/security review; Q01 remains BLOCKER.
- **Risk, impact and security implications:** Historical documents/file keys and future messages may be exposed after compromise; traffic correlation persists. Stronger security marketing would be misleading.
- **Required next action and evidence:** Record sensitivity, adversaries, endpoint trust and residual-risk acceptance; if FS required, investigate E16 before selecting baseline.
- **Suggested acceptance criteria:** Written G0 approval names absence of FS/PCS and recipient/traffic anonymity; no disappearance/rotation-based FS claim; reject the baseline if approved use requires stronger properties.
- **Responsible future role:** Product Owner + Security Reviewer
- **Target decision gate:** G0, before architecture approval; conditional E16

### Q02

**Counterparty and organizational authority**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-01 signatures][N01], [NIP-05 Identification, not verification][N05]; architectural distinction between key control and company authority.
- **Proposed decision or approach:** Raw keys are first-class; aliases optional. Specify unverified TOFU, pinned and out-of-band confirmed trust states; organization/representative assertions are optional independently verified evidence.
- **Risk, impact and security implications:** First-contact impostors can own valid keys/aliases. Cryptographic validity does not authorize import, payment or company decisions.
- **Required next action and evidence:** Draft R02 authority/enrollment contract with expected endpoint and action scope; E03/E08/E14 negative cases.
- **Suggested acceptance criteria:** Two clients reject unexpected key substitution and unauthorized action issuers; no DNS, government identity or business registry required; TOFU limitations are explicit.
- **Responsible future role:** Identity RFC Editor + Security Reviewer
- **Target decision gate:** G1 identity contract; G2 before SDK

### Q03

**Inbox discovery without a required indexer**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 Publishing][N17], [NIP-65][N65], [NIP-05 relay hints][N05]; signed-list routing requirement is stronger than arbitrary relay hints.
- **Proposed decision or approach:** Use recipient-signed kind 10050; configurable bootstrap and cached/directly exchanged signed metadata locate it. Check sender self-copy route too. Missing/conflicting/unusable inbox keeps queued with explicit local failure.
- **Risk, impact and security implications:** Suppression/rollback and malicious destinations can redirect observation or cause unavailability; a signature alone does not establish globally newest discovery.
- **Required next action and evidence:** Specify R02 list validation, tie/conflict/cache/refresh and no-fallback behavior; run E03.
- **Suggested acceptance criteria:** Absent, invalid, empty or stale-beyond-policy lists yield no wrap publication to substitute relays; a verified directly supplied list works without designated indexer; stale unknown state is not proof of nonexistent user.
- **Responsible future role:** Identity RFC Editor + Interoperability Engineer
- **Target decision gate:** G1, E03 at G2

### Q04

**Full authentication and validation order**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-44][N44], [NIP-17 author comparison][N17], [NIP-59][N59], [nostr-tools helper][T59], [Rust helper][R59]; helpers check different subsets.
- **Proposed decision or approach:** Use the complete bounded validation pipeline in transport-boundaries, including hash/signature before each decrypt, seal kind/empty tags, unsigned rumor/hash/author, inbound vs sender-archive role, schema/trust/commitments.
- **Risk, impact and security implications:** Impersonation, wrong-recipient acceptance, malformed IDs, resource exhaustion and parser ambiguity can survive convenience decryption.
- **Required next action and evidence:** Draft R03 validation order and negative corpus; freeze experimental validation expectations for E01/E02/E08.
- **Suggested acceptance criteria:** All tampered ID/signature/author/kind/recipient cases rejected before effects; genuine sender archive preserved without creating inbound operation; duplicate-key/oversize JSON rejected consistently by both clients.
- **Responsible future role:** Envelope RFC Editor + Security Reviewer
- **Target decision gate:** G1 contract; E01/E02/E08 at G2

### Q05

**Exportable document and receipt proof**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-59 unsigned rumors][N59], [NIP-01 established signatures][N01]; message authentication and exported object proof are distinct.
- **Proposed decision or approach:** Baseline authenticates transport assertions and original-byte commitments. **PO-005 defers** the earlier optional signed-object proposal; if later authorized it must use a reviewed existing algorithm. Specify signed-byte framing/domain separation, identity/context/version and verification; do not declare legal recognition.
- **Risk, impact and security implications:** Exported unsigned rumors/digests are not document signatures. Portable signed objects weaken deniability and can bind the wrong context if underspecified.
- **Required next action and evidence:** PO-005 defers portable proof. Draft baseline R04 authenticity/integrity disclosures and extension boundaries; optional proof design/vectors resume only after separate scope approval. E08 still validates authenticated receipt assertions.
- **Suggested acceptance criteria — current baseline:** Preserve exact document bytes and verify commitments; report transport-authenticated key separately from organizational/legal authority; unsigned rumors and hashes are never labeled portable signatures; E08 checks authenticated receipt assertions. **Historical/future signed extension, superseded for v0.1 by PO-005:** export retains original bytes and proof; modified bytes/domain/context/version fail verification. These signed-profile criteria apply only after separate authorization.
- **Responsible future role:** Document RFC Editor + Cryptography Reviewer
- **Target decision gate:** G0 optional scope; G1 signed profile before use

### Q06

**Carrier selection and envelope/file combination**

- **Priority:** P0
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 kinds 14/15][N17], [NIP-59 generic rumors][N59], [nostr-tools NIP-17 builder][T17]; no independent NBDP carrier exchange demonstrated.
- **Proposed decision or approach:** Propose kind 14 text envelopes plus correlated kind 15 files, one authoritative operation. Preserve existing kind meanings; do not depend on delivery order or generic chat understanding.
- **Risk, impact and security implications:** Independent clients may parse/render differently, create different rumors, import files twice or lose correlation.
- **Required next action and evidence:** Freeze a provisional R03/R04 discriminator/correlation candidate, then E02 and E06; inspect ordinary-client handling as a compatibility control.
- **Suggested acceptance criteria:** Two independent adapters exchange both directions and retain identical operation/commitment meaning across file-first/envelope-first/self-copy/retry cases; no extra outer kind and no generic-chat business-processing claim.
- **Responsible future role:** Protocol Architect + Interoperability Engineer
- **Target decision gate:** G2 before final carrier approval

### Q07

**Versioning, serialization and downgrade policy**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 plain text][N17], [NIP-44 version/length format][N44], [legacy Go][G44]; limits differ under version 2.
- **Proposed decision or approach:** Specify exact textual envelope/schema, discriminator, extension handling, byte/count limits, version negotiation and errors. Preserve document bytes; default to bounded legacy-compatible crypto inputs until experiments justify extension requirements.
- **Risk, impact and security implications:** Ambiguous JSON/canonicalization and unknown mandatory extensions can change commitments or trigger insecure fallback; format limit can cause memory DoS.
- **Required next action and evidence:** Draft R03/R08 with unsupported/duplicate-key/extension/canonical-byte cases; E01/E02/E04/E14.
- **Suggested acceptance criteria:** Unknown required versions/features never reach effects; no NIP-04/plaintext downgrade; independent parsers agree on supported inputs, rejection and document-byte commitments.
- **Responsible future role:** Envelope/Extensions RFC Editors
- **Target decision gate:** G1; E01/E02/E04/E14 at G2

### Q08

**Exact encrypted-file cryptographic bytes**

- **Priority:** P0
- **Classification:** BLOCKER
- **Relevant specifications and evidence:** [NIP-17 File Message][N17], [RFC 5116 §§5.1–5.2][GCM]; file suite/encoding/layout details are not fully fixed in NIP-17.
- **Proposed decision or approach:** Investigate standard AES-GCM profile with exact key/nonce/tag sizes, blob layout, AAD and key/nonce encoding. Fresh per-blob keys and no distinct-plaintext key/nonce reuse; omit thumbnails.
- **Risk, impact and security implications:** Incorrect tag/layout/encoding or repeated nonce can break integrity/confidentiality or interoperability despite successful transport.
- **Required next action and evidence:** Compare actual kind 15 producers; draft R05 alternatives; obtain cross-crypto/file vectors in E05/E06. Safe candidate parameters are not evidence of deployed compatibility.
- **Suggested acceptance criteria:** One reviewed byte profile has unambiguous positive/negative vectors shared by independent crypto implementations and kind 15 clients; nonce policy verified; no incompatible choice is mislabeled universal NIP behavior.
- **Responsible future role:** Cryptography Reviewer + Attachments RFC Editor
- **Target decision gate:** G1/G2; blocks attachment implementation

### Q09

**Hashes, file commitments and revisions**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 x/ox][N17], [NIP-94 metadata context][N94], [NIP-01 hashes][N01].
- **Proposed decision or approach:** Bind exact original document bytes, ciphertext bytes, lengths, document revision, ordered attachment references and logical operation. Keep filenames/plaintext hashes/type/format metadata inside encryption.
- **Risk, impact and security implications:** Host substitution, reordering, altered bytes, incorrect original/transformed hash interpretation and revision replay can misassociate business data.
- **Required next action and evidence:** Draft R04/R05 exact commitment/correlation domains and revision/supersession rules; E06/E07/E09.
- **Suggested acceptance criteria:** Independent clients obtain identical commitments for binary/UTF-8/multifile originals; mismatched hash/length/order/revision rejected; canonicalization is opt-in named document profile, not silent transport behavior.
- **Responsible future role:** Document RFC Editor
- **Target decision gate:** G1; E06/E07/E09 at G2

### Q10

**Envelope/file limits and resource exhaustion**

- **Priority:** P0
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-44 Implementation considerations][N44], [NIP-11][N11], [strfry sample][STR], [JavaScript][T44], [Rust][R44], [legacy Go][G44].
- **Proposed decision or approach:** Measure both encrypted inputs and full publication frame, tags/characters/UTF-8 and memory. Treat 16 KiB frame size as test candidate only; set explicit file/decode/depth limits.
- **Risk, impact and security implications:** Oversized frames fail delivery; unbounded base64/JSON/decryption can exhaust memory/CPU.
- **Required next action and evidence:** Run E04 using actual serialized wraps across crypto boundary lengths and two relay policies; publish a supported budget, not the format maximum.
- **Suggested acceptance criteria:** Accepted profile fixtures fit both measured library inputs and declared relay caps; out-of-budget inputs rejected before disproportionate allocation; final limits approved with measurements and safety margin.
- **Responsible future role:** Interoperability Engineer + Performance/Security Reviewer
- **Target decision gate:** G2 before limit finalization

### Q11

**Authenticated receipts and outcome meanings**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-01 OK][N01], [NIP-17][N17], [NIP-59][N59]; recipient assertions are application semantics.
- **Proposed decision or approach:** Separate publication/relay acceptance from durable receipt, download, integrity, format validation and scoped business decisions. Bind issuer/authority, original endpoint pair, logical ID, digest, revision and action.
- **Risk, impact and security implications:** False/confused receipts can trigger unjustified business effects; a signed claim does not prove truthful execution or legal delivery.
- **Required next action and evidence:** Draft R06 prerequisites, errors/retryability, receipt deduplication/no-ACK-loop behavior and honest unknown outcomes; E08/E12.
- **Suggested acceptance criteria:** Wrong issuer/recipient/hash/version/action receipts rejected; missing files never attest integrity; format checks name validator/profile; contradictory business assertions produce conflict; no acceptance/debt/legal inference from technical ACK.
- **Responsible future role:** Receipts RFC Editor + Business Workflow Architect
- **Target decision gate:** G1; E08/E12 at G2

### Q12

**Replay, duplicates and restored state**

- **Priority:** P0
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-01 event IDs][N01], [NIP-59 fresh wraps][N59], [NIP-17][N17]; outer identity is not logical operation identity.
- **Proposed decision or approach:** Stable logical operation ID with authenticated endpoint/context and exact commitment; durable replay/effect ledger, explicit validity/deadline and record horizon. New wrapper retains original operation; stale restores suspend effects pending reconciliation.
- **Risk, impact and security implications:** Duplicate imports/actions and conflicting-content ID reuse can occur across relays, retries, expiry or backup restoration.
- **Required next action and evidence:** Draft R04/R06 replay/conflict/expiry/recovery contract; set D with Q13; E09 and E12.
- **Suggested acceptance criteria:** Repeated operations produce one effect per declared coordinated consumer domain; same-ID/different-commitment quarantined; delayed valid messages accepted within horizon; expired unknown messages do not create effects; stale restore never silently reprocesses.
- **Responsible future role:** Receipts RFC Editor + Storage/Workflow Architect
- **Target decision gate:** G1; E09/E12 at G2

### Q13

**Offline horizon and durable availability**

- **Priority:** P0
- **Classification:** BLOCKER
- **Relevant specifications and evidence:** [NIP-59 permits storage refusal][N59], [NIP-11 limits][N11], [BUD-01 retrieval/Sunset][B01]; no minimum retention promise.
- **Proposed decision or approach:** Require approved measurable horizon H, retention and retry assumptions, surviving independent relay/blob replicas, local outbox and archives. PO-003 approves experimental H=7 days/R=10 days for test relays and blobs; J=2 days/candidate S=1 day remain explicit lab assumptions. This is not an approved public-network service level; Q13 remains BLOCKER.
- **Risk, impact and security implications:** All storage may disappear after OK; receiver can miss documents/files or be unable to reconstruct history.
- **Required next action and evidence:** H/R objective is selected by PO-003. Operations/security reviewers must fix skew, eviction/deadline/grace and incomplete recovery rules; E07/E10/E11 must demonstrate conditional recovery, separating accelerated and real-duration results.
- **Suggested acceptance criteria:** Within approved horizon all retained fixture operations recover with one surviving advertised relay/blob copy; all-copy loss reports unrecoverable/unknown, not recipient rejection; no guaranteed-global-delivery claim.
- **Responsible future role:** Product Owner + Operations/Storage Architect
- **Target decision gate:** G0 target; G2 evidence before operational SDK claims

### Q14

**Backdated and capped history reconciliation**

- **Priority:** P1
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 backdating][N17], [NIP-01 filters][N01], [NIP-67 hints/ties][N67], [NIP-77][N77].
- **Proposed decision or approach:** Overlap windows by jitter plus skew, retain seen IDs, catch up new relays and handle time ties/caps. Optional hints/negentropy assist but do not establish a hostile relay's completeness.
- **Risk, impact and security implications:** Advancing a single timestamp or treating EOSE/fewer-than-limit as complete can silently lose retained messages.
- **Required next action and evidence:** Run E11 with late backdated arrivals, more equal-time events than relay cap, no hints, auth-gated hints, negentropy modes and relay changes.
- **Suggested acceptance criteria:** Fixture inventory matches recovered stable operation set; unreadable tie/cap cases explicitly report incomplete recovery; no timestamp-only watermark claim; retry/new-relay scans stay bounded.
- **Responsible future role:** Relay/Recovery Engineer
- **Target decision gate:** G2 before recovery contract finalization

### Q15

**Concurrent devices and business receipt authority**

- **Priority:** P0
- **Classification:** BLOCKER
- **Relevant specifications and evidence:** [NIP-17 recoverable copies][N17], [NIP-46 distinct session/account keys][N46]; no global processing lock or company role primitive.
- **Proposed decision or approach:** **Historical proposal superseded by PO-004:** one active business-decision authority per action scope. **Current requirement:** parallel authorized-device decisions, per-device identity/grants/revocations, causal merge and explicit conflict recovery without mandatory central coordination. Technical facts remain distinct from business decisions; consumer-domain effect/idempotency limits remain explicit. See [design analysis](multi-device-authority-design.md).
- **Risk, impact and security implications:** Two devices can both import, sign conflicts or reconnect with stale state; shared account keys do not permit per-device cryptographic revocation.
- **Required next action and evidence:** PO-004 approves parallel scope, not an authority design. R06/R07 must define signed grants/revocations, offline freshness, causal conflict/supersession and effect domains; independent E08/E09/E12/E13 tests crash, partition, removal and rejoin.
- **Suggested acceptance criteria:** Fact union independent of arrival order; accept/reject contradictions always conflict; crash-after-effect does not blind-reimport; unauthorized/revoked devices obtain no authority from old messages; partition-delayed revocation limitations explicitly documented; authorized concurrent devices can decide and converge without a timestamp winner.
- **Responsible future role:** Product Owner + Workflow/Distributed Systems Architect
- **Target decision gate:** G0/G1/G2; blocks safe multi-device effect implementation

### Q16

**Signer trust, sessions and capability conformance**

- **Priority:** P1
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-46][N46], [NIP-07][N07], [NIP-55][N55], [NDK default scheme][NDK46]; signer plaintext access and API defaults matter.
- **Proposed decision or approach:** Permit local/user-controlled signers; remote signer is trusted for plaintext operations. Minimal approved permissions, distinct client/user keys, explicit NIP-44, exact returned-event matching and session lifecycle.
- **Risk, impact and security implications:** Malicious/compromised signer can leak/forge; session theft may exercise approved operations; outage interrupts decryption and signing.
- **Required next action and evidence:** Run E13 using reviewed local and NIP-46 adapters plus optional Android/browser interfaces, including permission denial, key substitution, timeout and relay switch.
- **Suggested acceptance criteria:** Wrong returned bytes/user key rejected; no implicit NIP-04; denied/revoked session cannot perform actions through tested signer; outage is explicit; copied account-key limitations not misrepresented.
- **Responsible future role:** Signer Integration Engineer + Security Reviewer
- **Target decision gate:** G2 before supported signer claim

### Q17

**Rotation, compromise recovery and archive decryption**

- **Priority:** P1
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-05 key pinning][N05], [NIP-46 relay switching][N46], [NIP-44 static-key exposure][N44].
- **Proposed decision or approach:** Separate ordinary old/new endorsed transition from compromised/lost-key recovery. Pin account keys, track epochs/known transitions, require independent out-of-band re-enrollment when old authority is unsafe; choose archive key retention explicitly.
- **Risk, impact and security implications:** Old-key attacker can sign conflicting successor claims; lost old keys can make archives undecryptable; old aliases/lists may roll back.
- **Required next action and evidence:** Draft R07 transition context/conflict/recovery and revocation semantics; E14; no retroactive FS claim or automatic alias upgrade.
- **Suggested acceptance criteria:** Two clients converge on accepted ordinary transition, quarantine forks/rollback, reject obsolete action authority per policy and require explicit confirmation after compromise; archive recovery/loss behavior stated.
- **Responsible future role:** Key Management RFC Editor + Security Reviewer
- **Target decision gate:** G1; E14 at G2

### Q18

**Relay AUTH privacy and anti-spam behavior**

- **Priority:** P1
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-42][N42], [NIP-59 Spam Protection][N59], [strfry][STR], [nostr-rs-relay configuration][RSR].
- **Proposed decision or approach:** Support auth-required/restricted flows and bounded retries. Prefer selected inbox policies restricting other users' wrap access; disclose that AUTH identifies sessions to operators.
- **Risk, impact and security implications:** Mixed filters/count/negentropy may leak metadata; real-key publisher AUTH can reveal sender/recipient activity; arbitrary challenges can cause unintended signing.
- **Required next action and evidence:** Run E10/E15 with intended/wrong recipient, multi-key auth, mixed filters, reconnect, auth denial and rate-limit cases.
- **Suggested acceptance criteria:** Tested honest configured relay does not serve other recipients' fixtures through any tested query mode; writes retry after AUTH only under consent policy; no unbounded retry or operator-anonymity promise.
- **Responsible future role:** Relay Interoperability Engineer + Privacy Reviewer
- **Target decision gate:** G2 before protected-inbox/privacy claim

### Q19

**Blob interchange, fallback and retention**

- **Priority:** P1
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-B7][NB7], [BUD-01][B01], [02][B02], [03][B03], [04][B04], [06][B06]; host behavior remains unverified.
- **Proposed decision or approach:** Prefer Blossom candidate adapter; permit independently specified opaque-storage adapters. Use private manifest commitments/fallbacks, exact ciphertext mirroring, strict fetch/CORS/redirect/size policy; no mandatory host.
- **Risk, impact and security implications:** Deleted/transformed blobs, wrong bytes or fallback misrouting break validation and can expose endpoint network resources.
- **Required next action and evidence:** Run E07 on two independent hosts/implementations including expired source, unavailable mirror, redirected/oversized data and authenticated retrieval.
- **Suggested acceptance criteria:** One intact replica yields exact committed bytes and plaintext; wrong hash/redirect/private-network access rejected; all replicas lost produces technical failure, never false validated receipt.
- **Responsible future role:** Storage Interoperability Engineer
- **Target decision gate:** G2 before attachment availability claim

### Q20

**HTTP storage authorization and token replay**

- **Priority:** P1
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-98][N98], [BUD-11][B11], [BUD-12][B12]; 27235 request auth differs from 24242 scoped blob auth.
- **Proposed decision or approach:** Specify adapter-specific canonical encoding, endpoint/action/hash/server binding, short expiry and sensitive-operation retry/consumption policy. Server-scoped tokens by default; do not redefine standard token formats.
- **Risk, impact and security implications:** Leaked unscoped tokens can be replayed across servers; body/hash ambiguity can authorize unintended operations, especially delete.
- **Required next action and evidence:** Draft R05 storage-auth profile; distinguish standard validation from optional host policy; E07 negative auth cases.
- **Suggested acceptance criteria:** Wrong server/action/hash/time/encoding tokens rejected by supported adapter; replay behavior documented and harmless or detected within scope; no blanket one-use guarantee inferred from expiry.
- **Responsible future role:** Storage Auth RFC Editor + Security Reviewer
- **Target decision gate:** G1; E07 at G2

### Q21

**Host and network metadata privacy**

- **Priority:** P1
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 private file fields][N17], [NIP-59 outer tags][N59], [BUD-01][B01], [BUD-11][B11]; traffic analysis is architectural reasoning.
- **Proposed decision or approach:** Keep sensitive file metadata/keys/original hashes private, use opaque public MIME/extension and avoid public invoice indexes; disclose stable ciphertext hashes/auth/timing. Additional proxy/upload-principal privacy is optional only after evidence.
- **Risk, impact and security implications:** Operators correlate uploads/downloads/identities; filenames/MIME in public paths or logs can leak business meaning even when file bytes are encrypted.
- **Required next action and evidence:** Draft R01/R05 metadata inventory and permitted public fields; E15 inspects packet/operator views and unauthorized egress.
- **Suggested acceptance criteria:** Public/operator captures contain no document plaintext, key, original filename/schema/hash through core operations; expected ciphertext hash/size/recipient/AUTH leakage documented; TLS observer claims remain precise.
- **Responsible future role:** Privacy RFC Editor + Client Security Engineer
- **Target decision gate:** G1; E15 at G2

### Q22

**Mandatory legacy NIP-96 compatibility**

- **Priority:** P1
- **Classification:** DECIDED
- **Relevant specifications and evidence:** [NIP-96 deprecation][N96] explicitly favors [NIP-B7][NB7]; project forbids mandatory provider lock-in.
- **Proposed decision or approach:** NIP-96 is not required for initial core conformance. An independent legacy adapter may be investigated later, with its distinct request/file-hash expectations tested before claiming compatibility.
- **Risk, impact and security implications:** Mandatory legacy auth inconsistencies would enlarge attack/interop surface; excluding it does not prove the preferred adapter works.
- **Required next action and evidence:** Record exclusion in R05/R08; E15 scope audit. Future optional adapter research remains open and is not marked interoperable.
- **Suggested acceptance criteria:** Core/client exchange succeeds with no NIP-96 dependency; no adapter is silently advertised as compatible; exact normative required retrieval surface still needs Q19.
- **Responsible future role:** Protocol Architect
- **Target decision gate:** G0 present-scope decision; future adapter gate

### Q23

**Formal NIP for reusable business profile**

- **Priority:** P2
- **Classification:** DECIDED
- **Relevant specifications and evidence:** [NIP-59 separates applications][N59], [NIP repository acceptance criteria/governance][NREADME]; task prohibits a present NIP proposal.
- **Proposed decision or approach:** No NIP submission in this stage. Draft a vendor-neutral NBDP application specification independently; a later profile NIP could retain the same kinds.
- **Risk, impact and security implications:** Premature standardization could fossilize untested semantics or be mistaken for implementation certification.
- **Required next action and evidence:** Track independent use-case evidence and E02/E08 results; reconsider only in a separately authorized later standardization task.
- **Suggested acceptance criteria:** Current deliverables contain no upstream proposal or allocated kind; future reconsideration cites independent implementations and concrete shared gap. Decision concerns timing, not closure of future standardization research.
- **Responsible future role:** Protocol Architect + Standards Editor
- **Target decision gate:** G0 scope; later independent-evidence review

### Q24

**Need for a dedicated inner rumor kind**

- **Priority:** P2
- **Classification:** EXPERIMENT_REQUIRED
- **Relevant specifications and evidence:** [NIP-17 carrier meanings][N17], [NIP-59 any unsigned rumor kind][N59]; generic encapsulation alone does not prove appropriate machine dispatch.
- **Proposed decision or approach:** Allocate nothing now. Test whether kinds 14/15 preserve discriminator/correlation/unknown-message behavior; a dedicated private inner kind is a future alternative only if a concrete mismatch is shown.
- **Risk, impact and security implications:** Misdispatch and unrecognized content can create semantic incompatibility; new inner kind does not improve transport confidentiality/retention.
- **Required next action and evidence:** Run E02/E06 and ordinary-client control, classify failure as RFC/adapter issue or demonstrated kind-semantic gap; reassess ADR before any future allocation.
- **Suggested acceptance criteria:** Independent clients retain unambiguous operation meaning; if failure arises from existing kind semantics and cannot be safely profiled, record reproducible rationale for C2 without allocating it in this task.
- **Responsible future role:** Interoperability Engineer + Protocol Architect
- **Target decision gate:** G2 carrier decision; later separate standardization gate

### Q25

**New outer kind or relay-level recovery extension**

- **Priority:** P2
- **Classification:** DECIDED
- **Relevant specifications and evidence:** [NIP-01 existing protocol][N01], [NIP-59 persistent 1059][N59], [NIP-67][N67], [NIP-77][N77]; no demonstrated new relay requirement.
- **Proposed decision or approach:** No new outer kinds/messages in the present profile. Resolve retry/receipts inside encryption and clients; retain explicit operational storage assumptions.
- **Risk, impact and security implications:** New outer classification could expose business traffic and fragment relay support without fixing availability.
- **Required next action and evidence:** Audit E10/E11 failure evidence for a real relay-level limitation. A separate later task may review a justified extension; no guarantee created by deferral.
- **Suggested acceptance criteria:** Current profile uses existing outer transport only; retained-data failure or false OK is not described as solved by a kind; future proposal requires reproduced unsupported behavior and privacy/backward-compatibility case.
- **Responsible future role:** Relay Architect + Standards Editor
- **Target decision gate:** G0 present-scope decision; future extension review

### Q26

**Continuity and encrypted capability negotiation**

- **Priority:** P2
- **Classification:** RFC_REQUIRED
- **Relevant specifications and evidence:** [NIP-05][N05], [NIP-46][N46], [NIP-17][N17], [NIP-89 handler limits][N89]; no common business continuity/negotiation contract established.
- **Proposed decision or approach:** Define minimal private authenticated capabilities and continuity context in R07/R08; no public mandatory registry or new NIP. Keep product-level safety contract separate from future broad standardization.
- **Risk, impact and security implications:** Replay/stale offers, downgrade and alias/authority confusion can select wrong versions, keys or processing actions.
- **Required next action and evidence:** Draft offer/response binding, freshness/cache/rollback/unknown-feature rules; E14; collect future multi-use-case evidence independently.
- **Suggested acceptance criteria:** Stale/replayed/foreign-context offers cannot silently change trusted key or security profile; two clients agree on negotiated version; unknown required capabilities yield explicit failure without revealing business profile publicly.
- **Responsible future role:** Extensions + Key Management RFC Editors
- **Target decision gate:** G1; E14 at G2

### Q27

**Kind 15 profile clarification and thumbnail ambiguity**

- **Priority:** P0
- **Classification:** BLOCKER
- **Relevant specifications and evidence:** [NIP-17 File Message][N17], [RFC 5116 nonce rules][GCM]; ambiguity is existing standard scope, not solved by renaming a kind.
- **Proposed decision or approach:** Promote original P2 follow-up to P0 because safe initial attachment interoperability depends on it. Preserve aes-gcm/x/ox/file meaning, omit thumbnails, document candidate byte interpretations without silently redefining NIP-17.
- **Risk, impact and security implications:** Two sound but incompatible byte interpretations can corrupt exchange; literal same-key/nonce thumbnails endanger crypto.
- **Required next action and evidence:** Compare pinned producers and E05/E06 vectors; document clarification evidence and decide whether a compatible NBDP file profile can be frozen. No upstream NIP proposal/change during this task.
- **Suggested acceptance criteria:** Reviewed profile aligns with actual independent producers or explicitly reports incompatibility; no distinct-plaintext nonce reuse; unresolved ambiguity blocks attachment SDK rather than being falsely declared solved.
- **Responsible future role:** Attachments RFC Editor + Cryptography Reviewer
- **Target decision gate:** G1/G2; blocks safe initial attachment profile

## Approval delta for retained blockers

| Issue | Resolved by approval | Still unverified |
| --- | --- | --- |
| Q01 | PO-002 accepts absence of FS/PCS | Complete threat-model/security review and permitted sensitivity |
| Q08 | PO-006 permits safe experimental bytes | Exact independent crypto/producer compatibility and reviewed normative profile |
| Q13 | PO-003 sets seven-day offline/ten-day retention test objective | Eviction/skew/grace, surviving-copy recovery and separate real-duration evidence |
| Q15 | PO-004 requires parallel devices and rejects single-active-authority | Concrete authority/causal-conflict/revocation/effect model and independent concurrency evidence |
| Q27 | PO-001/PO-006 permit existing kind 15 candidate testing | Exact producer/consumer compatibility and safe ambiguity resolution, no thumbnails |

All five remain **BLOCKER**. E01–E06 cannot close Q13/Q15. The original approval assumptions remain historical at [NBDP-004 baseline](https://github.com/webiumsk/NBDP/blob/00a5bfbb5656f2a82c0fb9a746c5137c9ea7f3ce/docs/research/architecture-risk-register.md).

## Cross-cutting risks and approval

The [threat model](transport-boundaries.md#preliminary-threat-model) maps ten adversaries to guarantee categories and experiments. Current blockers are Q01 (security model), Q08 (file crypto bytes), Q13 (offline retention objective), Q15 (concurrent-device authority/effects), and Q27 (kind 15 ambiguity). Their detailed criteria above remain unresolved.

NBDP-005 authorizes E01–E06 isolated experiments; RFC candidate drafting remains provisional and SDK production code remains unauthorized. Complete source evidence from NBDP-004 is retained; new runtime evidence belongs in experiment reports, not retroactively in the old research. Product Owner approvals are listed in [ADR 0001](../../adr/0001-transport-selection.md#current-approval-nbdp-005). Narrow DECIDED exclusions Q22/Q23/Q25 retain optional/future research paths; they are not claimed as general solutions to storage, standardization or delivery.

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

## NBDP-005 runtime evidence overlay

No canonical classification changes follow automatically from these results. [Full summary](experimental-validation-summary.md) distinguishes approved direction, source evidence, executed tests and missing controls.

| Question mapping | New evidence | Remaining gate |
| --- | --- | --- |
| Q01/Q04/Q07/Q10 | E01 PASS140, independent strict-validation/numeric/file-schema regression agreement; helper omissions identified | Complete threat review, normative contract, E04 limits and later attack/privacy evidence |
| Q02/Q03/Q17/Q26 | E03 PASS19, signed 10050/no-fallback/cache-conflict candidate and local alias tests | Normative discovery/freshness and signer support; global latestness not proven |
| Q06/Q07/Q09/Q24 | E02 PARTIAL22, both-direction independent adapter exchange over two relays | Mandatory ordinary-client control; E04/E06 blocked and carrier semantics not final |
| Q08/Q09/Q27 | E05 PASS25, browser/OpenSSL vectors and actual commitments/nonce-policy rejection; producer-source default nonce16 differs from candidate12 | Normative safe profile, full kind15/client/host interoperability; thumbnails omitted; source-level batch reuse concern not copied |
| Q13/Q14/Q18/Q19/Q20/Q21 | No offline-retention/host/AUTH/privacy runtime gate closed | E07/E10/E11/E15 plus real-duration operational evidence |
| Q11/Q12/Q15/Q17/Q26 | Parallel authority design only; no business receipt, replay persistence, grants/revocation or concurrent effects implemented | E08/E09/E12/E13/E14 and reviewed exact causal/authority/effect policy |

Historical failed/subset records are retained in experiments/results/history. Q01/Q08/Q13/Q15/Q27 remain BLOCKER. Prepared E04/E06 harnesses were not executed after E02's incomplete prerequisite. Portable signed-document proof remains deferred under PO-005; baseline authenticity/integrity and receipt gates remain required.
