# Required architecture experiments for NBDP

**Status:** Proposed experiment plan, NBDP-004, 2026-10-11. **No experiments have been implemented or executed in this task.** [ADR 0001](../../adr/0001-transport-selection.md) remains Proposed. Canonical Q01–Q27 are preserved from [open-questions.md](open-questions.md); next-decisive classifications and gates are in [the risk register](architecture-risk-register.md).

## Purpose and decision discipline

Prioritize falsifying the carrier/crypto/file/authority assumptions before optimizing user experience. A positive helper test, same-codebase wrapper pair or one relay success is not independent business interoperability. A failed experiment must identify whether the cause is a normative ambiguity, adapter bug, unsupported standard revision, unsafe cryptographic usage or genuine architectural limitation.

Experiments execute only in a later separately authorized isolated lab. No production/private business documents, account keys, relays, signer sessions, storage credentials or compliance destinations may be used. Use reviewed public crypto vectors and disposable lab identities then; this task generated no keys or test code.

## Required environment and pinned references

| Component | Initial reference / preparation requirement |
| --- | --- |
| Independent client A | nostr-tools commit cb8d22d4c906d99d8996693b37e4d85aa3d5f26e; manifest version 2.25.2; [crypto][T44], [wrap][T59], [message builder][T17] |
| Independent client B | Rust Nostr workspace commit 463f0c2d48e1d3c9e295cc231715d8a3855c65d3; record actual protocol/SDK crate revisions and feature flags; [crypto][R44], [wrap][R59] |
| Legacy compatibility control | go-nostr commit 18369d469538b931c8b80ebf3c77420aec804d95; not a required supported extended-length implementation [source][G44] |
| Relay A / B | strfry 4cd3cf64850caf47dda46c2a2abbbf3525a64d10 [configuration][STR]; nostr-rs-relay b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4 [configuration][RSR]; lab-only independent stores/policies |
| File crypto | Independent Web Crypto and OpenSSL EVP AEAD implementations, versions/builds pinned before execution; standard vectors and exact R05 candidate |
| Blob hosts | blossom-server a492dc61c4a581bbd0992546b2aec6f9aa543f75 plus an independent implementation selected and source-pinned during preparation; selection is an unresolved lab input, not proof of two-host conformity |
| Storage standards | NIP snapshot a79e21d90fce5465b50ef385dd368bba99ec4a0b; Blossom BUD snapshot b5bd2801d1763aa635fc8fea7a76597e0eb18990 [BUD-11][B11] |
| Existing-client/signer controls | Amethyst e6f464a1179def75274512b3c5bab921de3bf3d8 and Amber dc3f672eb6c41e1839c06e09b793777313a09cdc from [library evaluation](library-evaluation.md); exercise actual supported APIs before counting them |
| Harness environment | Isolated endpoints/containers with TLS test certificates, synthetic fixtures, deterministic schedules, persisted local state, bounded CPU/memory/network, controllable clocks and separately captured operator/passive views |

Nostr implementation pins come from the input source evaluation; they are starting references, not automatic current-release recommendations. Capture toolchain/runtime/image digest/OS, dependency lockfiles, source and fixture hashes, RFC candidate version, relay/NIP-11 policy, host/BUD versions and clock settings in each future run. No two-client claim if both adapters share the same underlying crypto/parser code for the tested property.

## Execution order and dependencies

All “start” conditions require a reviewed provisional contract and authorization to execute the lab; none is execution approval in this documentation task. G0 security/product scope precedes design commitment; exact candidates at G1 may be frozen for experiments while ADR remains Proposed.

| Order | Experiment | Primary risk reduction | Dependencies |
| --- | --- | --- | --- |
| 1 | [E01 — Independent NIP-44 and full gift-wrap validation](#e01) | Critical; first transport falsification | Frozen provisional R03 validation checklist; no runtime experiment dependency |
| 2 | [E02 — Two independent clients exchange text application envelopes](#e02) | Critical; carrier can invalidate B's present kind 14 selection | E01; provisional R03 discriminator/schema and R04 operation/correlation fixtures |
| 3 | [E03 — Inbox discovery, cache freshness and no arbitrary fallback](#e03) | Critical; recipient selection and disclosure boundary | E01; provisional R02 discovery/trust/cache rules |
| 4 | [E04 — Complete nested wrap, frame and resource limits](#e04) | Critical; interoperability and memory exhaustion | E01, E02; frozen fixture serializer and proposed limits |
| 5 | [E05 — AES-GCM byte profile, nonce discipline and cross-crypto vectors](#e05) | Critical; attachment security blocker, can run alongside E01–E04 | Reviewed provisional R05 alternatives and existing producer byte-layout inspection; no dependency on carrier runtime |
| 6 | [E06 — Independent kind 15 encrypted-file exchange and envelope correlation](#e06) | Critical; kind 15 adoption can invalidate the proposed combination | E01, E02, E05; provisional R04/R05 correlation rules |
| 7 | [E07 — Independent encrypted blob hosts, fallback and authorization](#e07) | High; attachment availability/privacy and HTTP attack boundary | E05; E06 for full end-to-end operation; provisional storage auth/fetch policy |
| 8 | [E08 — Authenticated receipt assertions, authority and prerequisite checks](#e08) | High; business safety before replay/concurrency experiments | E01, E02; frozen R06 receipt/authority candidate; E06/E07 for attachment states |
| 9 | [E09 — Replay, logical duplicates, expiry and backup restore](#e09) | High; repeated business effects and unknown-outcome recovery | E02, E08; provisional validity/record-retention rules and instrumented idempotent local effect |
| 10 | [E10 — Relay AUTH, refusal, restart, censorship and retention failure](#e10) | High; can run before offline catch-up and alongside file work | E01, E02, E03; lab relay policies and provisional retry/error rules |
| 11 | [E11 — Offline history with backdating, caps, ties and relay changes](#e11) | High; proves or rejects proposed offline operational scope | E03, E09, E10; Product Owner candidate H/R/S and optional 67/77 modes; E07 for retained blobs |
| 12 | [E12 — Multi-device authority, receipt conflicts and crash-after-import](#e12) | Critical for safe multi-device business effects; depends on receipt/replay contracts | E08, E09; Product Owner decision on authority/consumer scope and provisional R06/R07 rules |
| 13 | [E13 — Signer operations, returned-event equality and revocation](#e13) | High for any remotely signed client | E01, E02; reviewed R07 signer consent/session policy |
| 14 | [E14 — Key continuity, capability negotiation and optional portable proof](#e14) | High; identity rollback/downgrade and recovery | E02, E03, E08; provisional R07/R08; E13 for signer-supported transfer |
| 15 | [E15 — Metadata exposure and core/compliance independence audit](#e15) | High; privacy claims and project-independence conformance | E02, E03, E07, E10; optional E13; preliminary threat model and permitted egress policy |
| Conditional | [E16 — Forward-secret profile investigation](#e16) | Q01 baseline can be invalidated if FS becomes mandatory | Separate scope approval; protocol/implementation research first |

The listed order is a dependency-respecting working sequence, not a claim that E12's business-authority risk is lower than all earlier tests. E05 can run in parallel with transport foundations; E10 can move ahead of file work once E01–E03 are ready. Carrier, crypto and attachment failures should be discovered early; complete offline/multi-device confidence depends on their outcomes.

## Reproducible experiment records

### E01

**Independent NIP-44 and full gift-wrap validation**

- **Canonical questions:** Q01, Q04, Q07, Q10
- **Risk rank / dependencies:** Critical; first transport falsification; Frozen provisional R03 validation checklist; no runtime experiment dependency.
- **Objective:** Establish that independently implemented cryptography and full validation agree, including negative cases; helper success is not the acceptance oracle.
- **Assumption tested:** The pinned TypeScript/Rust paths can support the same NIP-44 profile and reject invalid wrapper/seal/rumor structures.
- **Environment / independent implementations:** Two independent adapters using nostr-tools and Rust Nostr pins; reviewed public test vectors and bounded JSON fixtures; no network required initially. Legacy go-nostr is a compatibility control, not the second primary.
- **Specification / implementation evidence:** [NIP-44][N44], [NIP-17][N17], [NIP-59][N59], [TypeScript][T44], [Rust][R44], [wrap helper][T59], [legacy Go][G44].

**Reproducible steps for the later lab:**

1. Run official NIP-44 vector corpus independently, then cross-encrypt/decrypt small UTF-8/binary-encoded-text fixtures in both directions.
2. Test 65,535/65,536/65,537 encryption-input boundaries and unsupported-version behavior separately from nested-wrap size acceptance; record the old Go limit.
3. Validate positive kind 1059 → 13 → unsigned rumor chain, sender archive and peer delivery roles.
4. Mutate event ID/signature, seal kind/tags/signature, author equality, rumor hash/unsigned structure, recipient and JSON types/depth/duplicate keys; compare normalized reject categories.

**Expected result / acceptance criteria:** Both primary implementations agree on all in-profile positive/negative outcomes; invalid signatures fail before corresponding payload decryption; legacy failures are declared and large payloads never trigger unbounded allocation.

**Failure criteria:** Any forged author/ID/recipient is accepted, unsupported version downgrades, helpers are used as complete validator without evidence, or independent crypto differs on in-profile vectors.

**Expected outputs:** Versioned vector manifest, hashes, per-implementation results and mismatch triage; no private/business fixture data.

**Architecture implication:** Cryptographic/profile mismatch blocks B's implementation and requires validator/library/profile changes. A helper bug is not proof a new kind is required.

### E02

**Two independent clients exchange text application envelopes**

- **Canonical questions:** Q06, Q07, Q09, Q24
- **Risk rank / dependencies:** Critical; carrier can invalidate B's present kind 14 selection; E01; provisional R03 discriminator/schema and R04 operation/correlation fixtures.
- **Objective:** Test existing kind 14 as an interoperable application carrier rather than assuming text JSON is a business standard.
- **Assumption tested:** A recognizable bounded text envelope survives existing private-message transport and has the same meaning in independent clients.
- **Environment / independent implementations:** Independent TypeScript and Rust adapters; isolated strfry and nostr-rs-relay fixtures; signed test inbox lists. Existing Amethyst client is an ordinary-chat control, not claimed NBDP interpreter.
- **Specification / implementation evidence:** [NIP-17 Chat Message][N17], [NIP-59][N59], [nostr-tools NIP-17 builder][T17].

**Reproducible steps for the later lab:**

1. Publish a signed inbox fixture for each identity on configured lab discovery sources; exchange canonical kind 14 rumors both directions with separate peer/self wraps.
2. Compare decoded envelope bytes, logical ID, sender/recipient/context, digest/revision and independent schema outcomes.
3. Deliver unknown protocol/version/mandatory extension, harmless ordinary chat and malformed discriminator; verify no unintended business dispatch.
4. Replay self-copies and reorder correlated file-reference/envelope stubs; inspect ordinary chat rendering and whether private tags/content are retained.

**Expected result / acceptance criteria:** Both primary clients recognize the same in-profile operation; ordinary chat never triggers business processing; self-copy produces no incoming effect; unknown required features fail explicitly.

**Failure criteria:** Different operation meaning, inconsistent canonical rumor construction, destructive renderer/parser behavior or ambiguous kind 14 semantics requiring silent reinterpretation.

**Expected outputs:** Bidirectional wire/rumor/envelope fixtures and dispatch matrix, ordinary-client control observations with exact client pin.

**Architecture implication:** Revise envelope/adapter first; if a reproducible existing-kind semantic conflict cannot be profiled safely, revisit C2 under Q24 without allocating a kind in this task.

### E03

**Inbox discovery, cache freshness and no arbitrary fallback**

- **Canonical questions:** Q02, Q03, Q17, Q26
- **Risk rank / dependencies:** Critical; recipient selection and disclosure boundary; E01; provisional R02 discovery/trust/cache rules.
- **Objective:** Verify recipient/sender inbox readiness and explicit failure when required signed routing information is not usable.
- **Assumption tested:** Configured bootstrap, cached signed announcements and directly exchanged contact metadata can work without a mandated indexer or DNS identity.
- **Environment / independent implementations:** Both adapters, two lab discovery/inbox relays, optional local NIP-05 HTTPS fixture; one controlled dishonest discovery source.
- **Specification / implementation evidence:** [NIP-17 Publishing][N17], [NIP-05][N05], [NIP-65][N65].

**Reproducible steps for the later lab:**

1. Exchange raw keys plus signed kind 10050 announcements with no external indexer; route only to advertised fixtures.
2. Return missing/empty/invalid-signature lists, valid NIP-65 hints without a 10050, stale cached lists, known rollback and conflicting/tied candidates.
3. Change NIP-05 alias to another key and verify the pinned endpoint remains unchanged; follow the NIP-05 no-redirect rule.
4. Remove sender inbox or fail sender-copy publication independently; inspect queued/peer-result/archival-failure distinctions and all attempted destinations.

**Expected result / acceptance criteria:** Valid direct metadata permits exchange; invalid/unusable list prevents release to substitute relays; alias change cannot authorize a new counterparty; sender archive failure is visible.

**Failure criteria:** Any public/key hint overrides required inbox policy, forged/stale/conflicting metadata silently routes documents, or absent list is reported as proven nonexistence.

**Expected outputs:** Discovery candidate/cache history, signed fixture hashes, destination log and expected local failure categories.

**Architecture implication:** Revise R02 or scope the supported discovery model. A requirement for a central indexer would contradict NBDP principles and block approval.

### E04

**Complete nested wrap, frame and resource limits**

- **Canonical questions:** Q04, Q07, Q10
- **Risk rank / dependencies:** Critical; interoperability and memory exhaustion; E01, E02; frozen fixture serializer and proposed limits.
- **Objective:** Determine the measured interoperable envelope budget including both encrypted inputs and full relay publication frame.
- **Assumption tested:** A useful manifest fits conservative limits across selected libraries/relays without unsafe allocations.
- **Environment / independent implementations:** Both adapters, two relay configurations with distinct NIP-11/message/content/tag caps, UTF-8/multifile fixtures and CPU/memory measurement. Record runtime/build architecture.
- **Specification / implementation evidence:** [NIP-44 lengths][N44], [NIP-11][N11], [strfry sample][STR], [TypeScript][T44], [Rust][R44], [Go][G44].

**Reproducible steps for the later lab:**

1. Sweep rumor JSON sizes, tag counts, unicode byte/character counts and attachment-reference counts; record rumor bytes, seal JSON bytes, wrap JSON and EVENT frame bytes.
2. Exercise below/equal/above candidate 16 KiB frame limit and actual relay caps, including normalized event vs full frame differences.
3. Exercise nested inputs around legacy/extended NIP-44 boundaries; use bounded stress fixtures rather than allocate theoretical multi-GB maxima.
4. Inject overlong base64, deep JSON, excessive tags/arrays and large HTTP metadata; verify rejection before expensive decoding/effects.

**Expected result / acceptance criteria:** In-profile useful manifests fit both primary deployments with declared margin; exact accepted/rejected measurements and memory/CPU ceilings are reproducible.

**Failure criteria:** Minimum required manifest exceeds supported budget; serializers disagree on boundaries; advertised caps differ without handling; rejected input exhausts resources.

**Expected outputs:** Byte-accounting/latency/memory tables, complete-frame fixtures and proposed final limits with rationale.

**Architecture implication:** Reduce metadata, externalize documents or revise profile budgets before SDK work; no automatic fragmentation protocol or kind change is inferred.

### E05

**AES-GCM byte profile, nonce discipline and cross-crypto vectors**

- **Canonical questions:** Q08, Q09, Q27
- **Risk rank / dependencies:** Critical; attachment security blocker, can run alongside E01–E04; Reviewed provisional R05 alternatives and existing producer byte-layout inspection; no dependency on carrier runtime.
- **Objective:** Identify one precise standard AEAD/layout/encoding candidate, verify independent crypto results and prevent unsafe thumbnails/nonces.
- **Assumption tested:** An existing standard AES-GCM construction can be profiled without custom primitives or incompatible guessed bytes.
- **Environment / independent implementations:** Independent browser Web Crypto AES-GCM and OpenSSL EVP implementations, versions pinned at lab preparation; public/reference test vectors and synthetic original bytes. Use existing candidate producers for encoding comparison.
- **Specification / implementation evidence:** [NIP-17 File Message][N17], [RFC 5116][GCM], [Web Crypto 2017 Recommendation](https://www.w3.org/TR/2017/REC-WebCryptoAPI-20170126/#aes-gcm), [OpenSSL 3.5 EVP documentation](https://docs.openssl.org/3.5/man3/EVP_EncryptInit/#gcm-and-ocb-modes).

**Reproducible steps for the later lab:**

1. Compare supported producers' key size/encoding, nonce size/encoding, tag placement/size and AAD; record alternatives instead of assuming their agreement.
2. Freeze candidate AEAD_AES_256_GCM parameters/layout and apply fixed reviewed vectors in both crypto implementations.
3. Cross-decrypt empty, binary, unicode-original-byte, boundary-size fixtures; mutate nonce/key/AAD/tag, truncate/append/alter ciphertext and verify rejection.
4. Exercise sender retry/revision/mirror planning; assert mirrors replicate identical ciphertext and every distinct plaintext has a distinct key/nonce pair. Thumbnail production remains disabled.

**Expected result / acceptance criteria:** Both implementations agree on exact candidate ciphertext/plaintext/tag/layout vector bytes, reject all tampering, and supported producer encoding assumptions are explicitly established.

**Failure criteria:** Distinct-plaintext key/nonce reuse, ignored/truncated authentication tag, incompatible ambiguous encodings/layouts or exposing unauthenticated plaintext to the workflow.

**Expected outputs:** Reviewed public crypto/encoding vector set, producer comparison, nonce-policy evidence and selected/rejected candidate rationale.

**Architecture implication:** Q08/Q27 remain blocking until safe byte profile and interoperability evidence exist. Crypto-vector success alone does not prove kind 15 client compatibility.

### E06

**Independent kind 15 encrypted-file exchange and envelope correlation**

- **Canonical questions:** Q06, Q08, Q09, Q24, Q27
- **Risk rank / dependencies:** Critical; kind 15 adoption can invalidate the proposed combination; E01, E02, E05; provisional R04/R05 correlation rules.
- **Objective:** Establish actual file-message interoperability using an exact safe crypto profile and existing kind 15 meaning.
- **Assumption tested:** Independent NIP-17 producers/consumers agree on file fields/bytes and can correlate them to one business operation.
- **Environment / independent implementations:** TypeScript and Rust adapters using independent E05 file implementations, two lab relays, local opaque host; Amethyst pinned file producer/consumer as optional compatibility control if its capabilities are demonstrated.
- **Specification / implementation evidence:** [NIP-17 File Message][N17], [NIP-59][N59], [library evidence](library-evaluation.md).

**Reproducible steps for the later lab:**

1. Send kind 15 URL/file-type/aes-gcm/key/nonce/x/ox metadata inside gift wraps and decrypt original bytes in each direction.
2. Check private field encodings and tag/hash semantics against independently emitted client file messages; report inability to exercise a client, rather than checking its README box.
3. Deliver file-before-envelope, missing file, duplicate file, same correlation/different hashes, mismatched document revision and fallback to same encrypted blob.
4. Repeat sender/self-copy and fresh-wrap retries; verify one operation authority and no import triggered by orphan kind 15; omit thumbnails entirely.

**Expected result / acceptance criteria:** Both primary clients recover exactly original bytes and agree on private metadata/correlation, orphan/conflict outcomes and operation identity; ordinary-client compatibility is reported separately.

**Failure criteria:** Different encodings/layout/hash interpretations, reliance on a new file kind, file-driven duplicate business operation or unsafe nonce/thumbnail behavior.

**Expected outputs:** Cross-client kind 15/rumor/blob fixtures, correlation acceptance matrix and ecosystem-control compatibility report.

**Architecture implication:** Revise/clarify attachment profile or defer full file support; do not silently redefine NIP-17. Revisit carrier scope if file semantics cannot be composed safely.

### E07

**Independent encrypted blob hosts, fallback and authorization**

- **Canonical questions:** Q08, Q09, Q13, Q19, Q20, Q21, Q22, Q27
- **Risk rank / dependencies:** High; attachment availability/privacy and HTTP attack boundary; E05; E06 for full end-to-end operation; provisional storage auth/fetch policy.
- **Objective:** Verify interchange of exact ciphertext through independently implemented/operated hosts with correct verification and scoped authorization.
- **Assumption tested:** Blossom's adapter candidate supplies replaceable storage without trusting host metadata or requiring one vendor.
- **Environment / independent implementations:** Two isolated hosts with different implementations/policies; one pinned blossom-server and a independently validated existing BUD-compatible host chosen/pinned during lab preparation, not two aliases of one operator. Browser CORS and controlled redirect fixtures.
- **Specification / implementation evidence:** [NIP-B7][NB7], [BUD-01][B01], [02][B02], [03][B03], [04][B04], [06][B06], [11][B11], [12][B12], [NIP-96][N96].

**Reproducible steps for the later lab:**

1. Upload opaque ciphertext with correct BUD-11 authorization and compare returned/downloaded bytes to local commitment; mirror identical bytes to independent host.
2. Retrieve with original host down/expired/deleted; try absent fallback, wrong hash/transform, truncated/oversized body, harmless approved redirect and local/private-network redirect.
3. Test CORS and preflight; wrong-server/action/hash/expiry/base64url tokens; repeated upload and delete tokens; compare current BUD-11/12 expectations to actual implementation.
4. Inspect public URL/type/extension/auth/log data; no plaintext keys/names or NIP-96 dependency; all-copy loss must prevent integrity/validated receipts.

**Expected result / acceptance criteria:** Any intact allowed mirror yields the committed original document after verification; unsupported/unsafe fetches fail before side effects; authorization behavior matches declared supported BUD revision.

**Failure criteria:** Host's hash is trusted without checking, transforms accepted, malicious redirect fetches protected network data, unscoped token policy exposes deletion across hosts, or false validated receipt emitted after loss.

**Expected outputs:** Host revision/config/token matrix, ciphertext inventories, redirect/CORS/error traces and access-metadata report.

**Architecture implication:** Select/fix an adapter profile or scope supported hosts; no mandatory specific host. Unavailable intact replicas affect operational assumptions, not document authentication.

### E08

**Authenticated receipt assertions, authority and prerequisite checks**

- **Canonical questions:** Q02, Q04, Q05, Q11, Q15
- **Risk rank / dependencies:** High; business safety before replay/concurrency experiments; E01, E02; frozen R06 receipt/authority candidate; E06/E07 for attachment states.
- **Objective:** Validate exactly what a recipient receipt asserts and prevent technical ACK confusion or foreign-operation acceptance.
- **Assumption tested:** Receipts can use the same encrypted carrier and unambiguously bind endpoint identities, document commitment/revision and action.
- **Environment / independent implementations:** Independent adapters and synthetic authorized/unauthorized issuer keys in isolated lab; receipt/effect ledger snapshots and named test format validator.
- **Specification / implementation evidence:** [NIP-01 OK][N01], [NIP-17][N17], [NIP-59][N59].

**Reproducible steps for the later lab:**

1. Generate later test-only assertions for received/downloaded/integrity/format/business states, with exact original endpoint pair, logical ID, digest/revision and action.
2. Alter each binding and issuer/authority context; use valid transport signatures on semantically unauthorized receipts.
3. Delay receipts, omit blobs, fail format validation and inspect sender's outcome; test relay OK without any recipient response.
4. Replay receipt itself, reorder compatible facts, contradict business outcomes and attempt receipt-triggered ACK loops; optionally test a separately reviewed portable-proof candidate.

**Expected result / acceptance criteria:** Only correctly scoped authorized assertions influence matching state; prerequisites enforced; missing ACK leaves unknown; receipt duplicates cause no repeated effect/response loop.

**Failure criteria:** Relay OK implies business acceptance; wrong-hash/version/action receipt passes; signed false claim is described as externally proven; orphan/contradictory receipt triggers automatic accounting action.

**Expected outputs:** Positive/negative receipt corpus, binding/provenance results and fact/business-state transition traces.

**Architecture implication:** Revise R06 or authority scope before SDK business hooks; no need for a new outer event to carry receipts.

### E09

**Replay, logical duplicates, expiry and backup restore**

- **Canonical questions:** Q07, Q09, Q11, Q12, Q13
- **Risk rank / dependencies:** High; repeated business effects and unknown-outcome recovery; E02, E08; provisional validity/record-retention rules and instrumented idempotent local effect.
- **Objective:** Demonstrate durable idempotency within declared consumer scope on top of at-least-once attempts.
- **Assumption tested:** Stable application identity and durable record/effect/receipt recovery can prevent replay-induced duplicate local effects.
- **Environment / independent implementations:** Both adapters with independent persistent ledgers, two lab relays, controllable clock, effect sink with observable counters and old/new backup snapshots.
- **Specification / implementation evidence:** [NIP-01 IDs][N01], [NIP-59 wrapping][N59], architectural reasoning and R06 candidate.

**Reproducible steps for the later lab:**

1. Send one operation through multiple relays as identical wrap and as several fresh wraps; preserve application ID and exact operation commitment.
2. Reuse same scoped ID with different document/digest/revision/action; retry expired unknown messages and delayed valid offline messages.
3. Crash before durable receive, after receive, after effect but before receipt and after receipt outbox enqueue; restart and retry.
4. Restore an older ledger backup, replay the message/receipt and require reconciliation/explicit unknown-state quarantine before effects; inspect tombstone horizon and receipt deduplication.

**Expected result / acceptance criteria:** Declared coordinated consumer records at most one effect for the operation across tested retry/restart cases; conflicting identity never becomes new effect; stale restore does not silently import.

**Failure criteria:** Outer IDs are used as business identity, ledger expiry allows valid old actions unchecked, old backups reprocess, or ambiguous external effect blindly retries.

**Expected outputs:** Effect/ledger/receipt inventories, reproducible crash schedules, validity/retention matrix and restore recovery outcomes.

**Architecture implication:** Change persistence/contract/scope; this proves only tested consumer-domain idempotency, never exactly-once network delivery or cross-company global effects.

### E10

**Relay AUTH, refusal, restart, censorship and retention failure**

- **Canonical questions:** Q01, Q03, Q13, Q18, Q25
- **Risk rank / dependencies:** High; can run before offline catch-up and alongside file work; E01, E02, E03; lab relay policies and provisional retry/error rules.
- **Objective:** Establish observed relay-policy compatibility and honest failure outcomes, including recipient-access limitations.
- **Assumption tested:** Existing 1059 transport with AUTH can support selected inbox policies while clients tolerate failures without arbitrary rerouting or false receipt.
- **Environment / independent implementations:** Pinned strfry and nostr-rs-relay lab instances with independent data directories and policies; read/write/refusal/eviction controls, two test recipients and optional protocol simulator for dishonest replies.
- **Specification / implementation evidence:** [NIP-42][N42], [NIP-17 Relays][N17], [NIP-59 storage/spam scope][N59], [strfry][STR], [nostr-rs-relay][RSR].

**Reproducible steps for the later lab:**

1. Publish/subscribe with missing, correct, wrong and multiple authenticated keys; reconnect and verify fresh challenge behavior.
2. Query mixed recipients/authors, broad filters, COUNT and supported negentropy paths; check that tested recipient policy cannot expose another recipient's fixtures.
3. Refuse writes, rate-limit, disconnect before/after OK, restart storage, accept-then-evict and simulate false OK without durable storage.
4. Inspect per-relay/per-recipient status, sender archive failures, bounded retries/backoff and no fallback outside advertised inboxes.

**Expected result / acceptance criteria:** Supported honest policy paths satisfy access/validation expectations; failure states remain explicit and bounded; an accepted-then-lost event is never called recipient received.

**Failure criteria:** Privacy claim survives a bypass, auth-required retry signs unintended identity, all failures route to arbitrary product relay or an OK is treated as retention proof.

**Expected outputs:** Config/image/revision manifest, access-policy matrix, event inventory before/after restart/eviction and retry traces.

**Architecture implication:** Narrow supported relay/privacy policy or improve adapters; if required operational behavior cannot be achieved, revisit scope. No automatic new relay kind/protocol extension.

### E11

**Offline history with backdating, caps, ties and relay changes**

- **Canonical questions:** Q12, Q13, Q14, Q18, Q25
- **Risk rank / dependencies:** High; proves or rejects proposed offline operational scope; E03, E09, E10; Product Owner candidate H/R/S and optional 67/77 modes; E07 for retained blobs.
- **Objective:** Recover the complete surviving in-profile operation set after disconnection without trusting a timestamp-only watermark.
- **Assumption tested:** Overlapping recovery and safe reconciliation can recover retained backdated wraps within stated horizon and expose incomplete cases.
- **Environment / independent implementations:** Controlled clocks/simulation plus a separately scheduled real-time soak; two relay stores with known inventories, small result caps, supported/unsupported 67/77 modes and optional authenticated queries.
- **Specification / implementation evidence:** [NIP-17 backdating][N17], [NIP-01 filters][N01], [NIP-67][N67], [NIP-77][N77], [NIP-59][N59].

**Reproducible steps for the later lab:**

1. Create timestamp-jittered wraps over candidate H=7 days, with retained history R=10 days and declared skew margin; record exact arrival/created_at and fixture inventory.
2. Inject new arrivals backdated behind the last seen timestamp, many events with identical timestamps beyond cap, hidden AUTH results and absent/misleading hints.
3. Disconnect one recipient, restart, remove one relay and add another; paginate/reconcile and deduplicate while retrieving retained files.
4. Delete some/all wraps or expire blobs deliberately; compare recovered inventory and local outcomes. Report accelerated clock evidence separately from a true-duration soak.

**Expected result / acceptance criteria:** Complete retained fixture set recovers when one eligible relay/blob copy survives; tie/cap limits that prevent proof of catch-up report incomplete; deleted data is never fabricated.

**Failure criteria:** A missing retained message is silently treated as complete, duplicate effects recur, malicious finish hint is accepted as global truth or real-time duration is claimed from simulation alone.

**Expected outputs:** Inventory-difference report, time/overlap diagrams, pagination/auth/negentropy traces, retention/soak result and explicit uncertainty cases.

**Architecture implication:** Revise recovery or offline horizon assumptions; no SDK reliability claim before the chosen horizon is measured. Failure of all-copy retention is an availability limit.

### E12

**Multi-device authority, receipt conflicts and crash-after-import**

- **Canonical questions:** Q02, Q11, Q12, Q15, Q17
- **Risk rank / dependencies:** Critical for safe multi-device business effects; depends on receipt/replay contracts; E08, E09; Product Owner decision on authority/consumer scope and provisional R06/R07 rules.
- **Objective:** Demonstrate deterministic observable conflict and idempotency behavior without asserting global exactly-once processing.
- **Assumption tested:** Single active business-decision authority and explicit coordinated consumer domain can coexist with observer devices and offline delivery.
- **Environment / independent implementations:** Two independently implemented recipient clients with same-account and distinct-device-key test scenarios, controllable partition, coordinated vs disconnected effect sinks, authority epoch fixtures.
- **Specification / implementation evidence:** [NIP-17 copies][N17], [NIP-46 key/session scope][N46], architectural reasoning in [transport boundaries](transport-boundaries.md).

**Reproducible steps for the later lab:**

1. Receive one operation concurrently; merge technical facts, emit identical receipts and contradictory accepted/rejected decisions in all arrival orders.
2. Partition devices, crash the active authority after import before ACK and reconnect an observer with stale backup/state.
3. Remove/revoke a signer session, then reconnect; separately test a device retaining copied account secret and show revocation limitation.
4. Exercise approved authority transfer/supersession and foreign-device assertions; freeze automatic effects on contradictory/ambiguous authority.

**Expected result / acceptance criteria:** Every schedule yields same fact union/conflict classification; no timestamp winner; authorized scoped action and tested coordinated effect execute at most once; disconnected uncoordinated devices are explicitly outside guarantee.

**Failure criteria:** Removed copied-key device is falsely claimed unable to sign, authority ambiguity silently imports, contradictory receipts overwrite each other or cross-domain exactly-once is claimed.

**Expected outputs:** Schedule/authority/state/effect traces and consumer-domain limits; compare both client results.

**Architecture implication:** Narrow v0.1 scope or change authority/state contract; Q15 remains a blocker until approved criteria pass. A mandatory operator coordinator would violate project constraints.

### E13

**Signer operations, returned-event equality and revocation**

- **Canonical questions:** Q04, Q15, Q16, Q17
- **Risk rank / dependencies:** High for any remotely signed client; E01, E02; reviewed R07 signer consent/session policy.
- **Objective:** Validate signer integration independently from the transport crypto implementation and inventory plaintext/key trust.
- **Assumption tested:** Explicit NIP-44 and permissioned sessions can support user-controlled key custody without silent output/key substitution.
- **Environment / independent implementations:** Local signer and a pinned test NIP-46 implementation selected during preparation; TypeScript/Rust adapters; optional Amber/browser extension only after pinning supported APIs. No production account or signer.
- **Specification / implementation evidence:** [NIP-46][N46], [NIP-07][N07], [NIP-55][N55], [NDK signer defaults][NDK46].

**Reproducible steps for the later lab:**

1. Connect with distinct client, signer and user test keys; fetch actual user key; approve minimum encryption/decryption/signing permissions.
2. Compare returned event signature and every requested field/author; return a valid signature over substituted content/key to exercise rejection.
3. Deny permission, timeout, sign out/revoke, reconnect, switch signer relays and replay stale session messages.
4. Inspect signer-visible plaintext/session metadata and invoke explicit NIP-44 through adapters with known default NIP-04 pitfalls.

**Expected result / acceptance criteria:** Correct requests interoperate; substituted signed event/key rejected; unsupported/denied/outage cases explicit; revocation works under tested no-secret-copy model.

**Failure criteria:** Valid signature over wrong bytes accepted, client/signer key confused with account key, default downgrade or claimed secrecy from signer plaintext operations.

**Expected outputs:** Permission/request-response/relay-switch traces and plaintext trust-boundary inventory.

**Architecture implication:** Limit supported signers or improve integration contract; user-controlled local custody remains allowed and no central signer is required.

### E14

**Key continuity, capability negotiation and optional portable proof**

- **Canonical questions:** Q02, Q03, Q05, Q07, Q17, Q26
- **Risk rank / dependencies:** High; identity rollback/downgrade and recovery; E02, E03, E08; provisional R07/R08; E13 for signer-supported transfer.
- **Objective:** Verify ordinary rotation is distinct from compromised-key recovery and capability offers cannot silently change trusted identity/security.
- **Assumption tested:** Pinned local continuity/private negotiation can be interoperable without a business directory or public capability event.
- **Environment / independent implementations:** Both clients with synthetic old/new/recovery contact keys, signed candidate transitions and private offers; fixed document export/proof fixtures only if optional proof candidate reviewed.
- **Specification / implementation evidence:** [NIP-05][N05], [NIP-46][N46], [NIP-44][N44], [NIP-59][N59].

**Reproducible steps for the later lab:**

1. Perform ordinary old/new endorsed transition, replay an old alias/list/offer and introduce two conflicting successor claims.
2. Mark old key compromised/unavailable; require independent out-of-band re-enrollment rather than accepting any old-key endorsement; test archive decryption available/lost cases.
3. Exchange version/security/format offers privately; replay stale foreign-context offers and unknown required features; preserve existing key pin and minimum security profile.
4. If optional signatures enabled, export original document plus proof, verify independently, then alter exact bytes/domain/context/version and distinguish key identity from claimed company/legal role.

**Expected result / acceptance criteria:** Both clients agree on selected policy outcomes, quarantine conflicting/obsolete transitions, prevent downgrade/alias replacement and explicitly distinguish archive key loss and portable proof absence.

**Failure criteria:** Compromised old key unilaterally restores trusted company identity, static rotation claims retroactive FS or optional proof is described as legally recognized by cryptographic validity.

**Expected outputs:** Transition/negotiation/proof vector corpus, conflict and recovery transcript, interoperability outcomes.

**Architecture implication:** Revise R02/R07/R08 or defer advanced continuity/proof; broad NIP standardization remains separate future evidence work.

### E15

**Metadata exposure and core/compliance independence audit**

- **Canonical questions:** Q01, Q03, Q18, Q20, Q21, Q22, Q23, Q25, Q26
- **Risk rank / dependencies:** High; privacy claims and project-independence conformance; E02, E03, E07, E10; optional E13; preliminary threat model and permitted egress policy.
- **Objective:** Establish actual observer views and demonstrate absence of mandatory vendor/compliance disclosure paths.
- **Assumption tested:** Core can keep sensitive metadata private while explicitly disclosing unavoidable recipient/AUTH/traffic/blob correlation.
- **Environment / independent implementations:** Test sender/recipient, both relay/host operators, passive packet capture without TLS keys, separate TLS-terminating operator logs, strict destination allowlists and optional independently configured mock compliance adapter.
- **Specification / implementation evidence:** [NIP-17][N17], [NIP-42][N42], [NIP-59][N59], [BUD-01][B01], [BUD-11][B11]; project principles and architectural reasoning.

**Reproducible steps for the later lab:**

1. Send known synthetic documents with marker filenames/type/schema/plaintext hashes and capture public wrap/operator/host/passive-network views separately.
2. Compare unauthenticated observer and real-key AUTH publisher/subscriber views; correlate mirror hashes, timings/sizes and connection endpoints.
3. Remove DNS/NIP-05, central bootstrap, product-owned servers, Peppol/reporting/analytics endpoints and legacy NIP-96 services; exchange using raw keys/direct signed inbox metadata and independent hosts.
4. Audit egress/logs before adapter invocation; explicitly authorize a bounded mock compliance export, fail that adapter and verify core transport/receipt behavior stays independent.

**Expected result / acceptance criteria:** No sensitive markers/file keys/plaintext commitments leak outside permitted encrypted/authorized endpoint paths; documented outer/operator metadata remains visible; passive TLS observer is not described as reading JSON; no automatic third-party reporting.

**Failure criteria:** Core sends plaintext/metadata to unapproved destination, compliance outage breaks protocol conformance, a mandatory vendor/registry/host is needed or operator correlation is hidden from the threat model.

**Expected outputs:** Observer-view/redaction matrix, destination and permission manifest, before/after adapter audit and corrected privacy/independence claims.

**Architecture implication:** Any mandatory compliance/vendor dependency or unexpected core disclosure blocks approval. Expected metadata requires Q01 residual-risk acceptance, not an anonymity guarantee.

### E16

**Conditional forward-secret profile investigation**

- **Canonical questions:** Q01, Q15, Q16, Q17, Q26.
- **Status:** Conditional research experiment outside the minimum baseline; no MLS/Marmot implementation is selected or run.
- **Objective/assumption:** Determine whether a separately profiled standardized forward-secret transport can meet approved identity/device/offline/archive objectives when the baseline is insufficient.
- **Environment/implementations:** First inventory and pin independent Marmot/MLS implementations, exact spec surfaces and vectors; no pair has been established by this research.
- **Dependencies:** Q01 Product Owner/security scope; reviewed membership/recovery policy, then isolated authorization.

**Later reproducible steps:**

1. Identify two independent implementations and published vectors; document if no adequate pair exists.
2. Freeze one reviewed profile; exercise device add/remove, delayed/reordered messages, rejoin, key deletion and backup restoration under synthetic schedules.
3. Test traffic/availability and archive requirements; record whether retained keys/backups weaken intended history protection.
4. Compare state-loss/recovery, complexity and interoperation to the measured baseline.

**Expected/failure results:** Evidence must match claimed security and recovery scope; undocumented compatibility, retained obsolete secrets or failed offline objectives prevent selecting the stronger profile. Do not label baseline rotation as FS.

**Outputs/architecture consequences:** Separate security-profile ADR/evidence if authorized. If FS is mandatory and no adequate independently interoperable profile is established, implementation stays blocked. [RFC 9420][MLS] supplies standardized MLS semantics; [Marmot pin][MSPEC] supplies Nostr-related profile context, not proven NBDP conformity.

## Minimum requirement coverage

| Required experiment area | Backlog coverage |
| --- | --- |
| Two independent NIP-17 clients exchange application envelopes | E01, E02 |
| Complete gift-wrap/frame limits | E04 |
| NIP-44 cross-library compatibility | E01, E04 |
| Kind 15 encrypted attachment interoperability | E06 |
| AES-GCM encoding/key/nonce/layout vectors | E05 |
| Recipient kind 10050 inbox discovery | E03 |
| Authenticated receipt validation | E08 |
| Replay/duplicate business processing | E09 |
| Timestamp-backdated offline recovery | E11 |
| Relay refusal/disconnection/retention failures | E10, E11 |
| Concurrent multi-device receipts/effects | E12 |
| Independent encrypted blob retrieval | E07 |
| Signer trust and key/capability continuity | E13, E14 |
| Privacy/mandatory-service/compliance boundaries | E15 |

## Canonical question traceability

| Question | Required evidence / decision contribution |
| --- | --- |
| Q01 | [E01](#e01), [E10](#e10), [E15](#e15), [conditional E16](#e16); BLOCKER in [risk register](architecture-risk-register.md#q01) |
| Q02 | [E03](#e03), [E08](#e08), [E12](#e12), [E14](#e14); RFC_REQUIRED in [risk register](architecture-risk-register.md#q02) |
| Q03 | [E03](#e03), [E10](#e10), [E14](#e14), [E15](#e15); RFC_REQUIRED in [risk register](architecture-risk-register.md#q03) |
| Q04 | [E01](#e01), [E04](#e04), [E08](#e08), [E13](#e13); RFC_REQUIRED in [risk register](architecture-risk-register.md#q04) |
| Q05 | [E08](#e08), [E14](#e14); RFC_REQUIRED in [risk register](architecture-risk-register.md#q05) |
| Q06 | [E02](#e02), [E06](#e06); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q06) |
| Q07 | [E01](#e01), [E02](#e02), [E04](#e04), [E09](#e09), [E14](#e14); RFC_REQUIRED in [risk register](architecture-risk-register.md#q07) |
| Q08 | [E05](#e05), [E06](#e06), [E07](#e07); BLOCKER in [risk register](architecture-risk-register.md#q08) |
| Q09 | [E02](#e02), [E05](#e05), [E06](#e06), [E07](#e07), [E09](#e09); RFC_REQUIRED in [risk register](architecture-risk-register.md#q09) |
| Q10 | [E01](#e01), [E04](#e04); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q10) |
| Q11 | [E08](#e08), [E09](#e09), [E12](#e12); RFC_REQUIRED in [risk register](architecture-risk-register.md#q11) |
| Q12 | [E09](#e09), [E11](#e11), [E12](#e12); RFC_REQUIRED in [risk register](architecture-risk-register.md#q12) |
| Q13 | [E07](#e07), [E09](#e09), [E10](#e10), [E11](#e11); BLOCKER in [risk register](architecture-risk-register.md#q13) |
| Q14 | [E11](#e11); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q14) |
| Q15 | [E08](#e08), [E12](#e12), [E13](#e13), [conditional E16](#e16); BLOCKER in [risk register](architecture-risk-register.md#q15) |
| Q16 | [E13](#e13), [conditional E16](#e16); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q16) |
| Q17 | [E03](#e03), [E12](#e12), [E13](#e13), [E14](#e14), [conditional E16](#e16); RFC_REQUIRED in [risk register](architecture-risk-register.md#q17) |
| Q18 | [E10](#e10), [E11](#e11), [E15](#e15); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q18) |
| Q19 | [E07](#e07); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q19) |
| Q20 | [E07](#e07), [E15](#e15); RFC_REQUIRED in [risk register](architecture-risk-register.md#q20) |
| Q21 | [E07](#e07), [E15](#e15); RFC_REQUIRED in [risk register](architecture-risk-register.md#q21) |
| Q22 | [E07](#e07), [E15](#e15); DECIDED in [risk register](architecture-risk-register.md#q22) |
| Q23 | [E15](#e15); DECIDED in [risk register](architecture-risk-register.md#q23) |
| Q24 | [E02](#e02), [E06](#e06); EXPERIMENT_REQUIRED in [risk register](architecture-risk-register.md#q24) |
| Q25 | [E10](#e10), [E11](#e11), [E15](#e15); DECIDED in [risk register](architecture-risk-register.md#q25) |
| Q26 | [E03](#e03), [E14](#e14), [E15](#e15), [conditional E16](#e16); RFC_REQUIRED in [risk register](architecture-risk-register.md#q26) |
| Q27 | [E05](#e05), [E06](#e06), [E07](#e07); BLOCKER in [risk register](architecture-risk-register.md#q27) |

Runtime evidence does not replace RFC requirements or Product Owner risk acceptance. Q22/Q23/Q25 are present exclusions audited by E15 or relay scope evidence, not proof that legacy storage, wider standardization or all delivery problems are solved.

## Experiment acceptance and SDK gate

Each future run produces a reproducible fixture/source/config manifest, accept/reject and observer-state outcomes, resource bounds, mismatch/failure explanations and architecture consequences. Publish synthetic artifacts without real keys/documents. Do not report all tests “passed” if a skipped independent implementation, missing blob host, unsupported feature or simulated-time-only result leaves required evidence absent.

Before G3 SDK implementation authorization:

1. G0 approves Q01/Q13/Q15 scope and the Proposed ADR direction.
2. G1 fixes applicable R02–R08 contracts; Q08/Q27 attachment blockers resolve with independent crypto/file vectors and security review.
3. E01–E15 pass the selected profile's applicable acceptance criteria with genuine implementation independence; unsupported optional signer/legacy features are explicitly excluded rather than falsely claimed.
4. Offline objectives have measured evidence appropriate to the claim; restored state and multi-device effect scope are tested.
5. Product Owner separately authorizes SDK implementation. Approval does not create legal signature/delivery recognition, erase residual metadata exposure or guarantee all-operator availability.

Stop after documenting this plan. No test implementation code, production code, production keys, new kinds/NIP proposals, deployments or relay changes are part of NBDP-004.

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
