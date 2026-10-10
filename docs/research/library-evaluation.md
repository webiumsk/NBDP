# Library and implementation evaluation

Research date: **2026-10-11**. Recommendation: use pinned **nostr-tools** and **Rust Nostr** as independent reference candidates for later conformance work; evaluate **NDK** for higher-level client operations. Treat legacy **go-nostr** as a compatibility target with a maintenance/format limitation. No library is established here as an audited, complete NBDP implementation.

## Method and reproducible pins

Remote HEADs were resolved with Git, and the following files were read at those commits through the GitHub connector. Package versions are manifest values at the pinned source revision, not proof that published packages contain the same source. “Implemented” below means observed code or a maintainer declaration, as labeled. Existing tests were read, not run. No runtime performance, deployed-relay behavior, live client cross-tests, vulnerability audit or dependency audit was performed.

| Repository / role | Exact observed commit | Version / evidence |
| --- | --- | --- |
| nostr-protocol/nips / official source | `a79e21d90fce5465b50ef385dd368bba99ec4a0b` | [Pinned NIP index][NREADME] |
| nbd-wtf/nostr-tools / TypeScript primitives | `cb8d22d4c906d99d8996693b37e4d85aa3d5f26e` | [package.json](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/package.json): 2.25.2, Unlicense |
| nostrdevkit/nostr / Rust protocol and SDK workspace | `463f0c2d48e1d3c9e295cc231715d8a3855c65d3` | [nostr/Cargo.toml](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/Cargo.toml): protocol crate 0.45.5; [Cargo.toml](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/Cargo.toml): MIT, Rust 1.85.0 minimum |
| nostr-dev-kit/ndk / TypeScript higher-level SDK | `4b86acd13fe3c1284fddcb81a7f0d63e491db64a` | [core/package.json](https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/core/package.json): core 3.0.3, MIT |
| nbd-wtf/go-nostr / Go library, historical fiatjaf URL redirects here | `18369d469538b931c8b80ebf3c77420aec804d95` | [README.md](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/README.md): maintenance mode; points users to a successor |
| vitorpamplona/amethyst / Android client | `e6f464a1179def75274512b3c5bab921de3bf3d8` | [README.md](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/README.md): NIP support checklist |
| greenart7c3/Amber / Android signer | `dc3f672eb6c41e1839c06e09b793777313a09cdc` | [README.md](https://github.com/greenart7c3/Amber/blob/dc3f672eb6c41e1839c06e09b793777313a09cdc/README.md): segregated key custody and NIP-46 device goal |
| hoytech/strfry / relay | `4cd3cf64850caf47dda46c2a2abbbf3525a64d10` | [README.md](https://github.com/hoytech/strfry/blob/4cd3cf64850caf47dda46c2a2abbbf3525a64d10/README.md), [strfry.conf](https://github.com/hoytech/strfry/blob/4cd3cf64850caf47dda46c2a2abbbf3525a64d10/strfry.conf) |
| scsibug/nostr-rs-relay / relay | `b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4` | [README.md](https://github.com/scsibug/nostr-rs-relay/blob/b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4/README.md), [config.toml](https://github.com/scsibug/nostr-rs-relay/blob/b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4/config.toml) |
| hzrd149/blossom / BUD specifications | `b5bd2801d1763aa635fc8fea7a76597e0eb18990` | [README.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/README.md) and BUDs below |
| hzrd149/blossom-server / blob server | `a492dc61c4a581bbd0992546b2aec6f9aa543f75` | [README.md](https://github.com/hzrd149/blossom-server/blob/a492dc61c4a581bbd0992546b2aec6f9aa543f75/README.md): capabilities, settings, retention |
| marmot-protocol/marmot / alternative messaging specification | `7fabb81b3ed6e2fffeb1b267a0d2ae92b0ab2c89` | [README.md](https://github.com/marmot-protocol/marmot/blob/7fabb81b3ed6e2fffeb1b267a0d2ae92b0ab2c89/README.md): adopted spec; deprecated MIP-era documents |

This is a purposive sample, not an exhaustive census of all languages or Nostr projects. It prioritizes two independent crypto implementations, a higher-level SDK, a legacy implementation, and the operational dependencies needed for offline document exchange.

## Capability and maturity assessment

| Candidate | Observed capabilities | Evidence strength / limitation | Fit for NBDP research |
| --- | --- | --- | --- |
| nostr-tools | NIP-17 text builders; NIP-44 encryption; NIP-59 wrapping; NIP-42 AUTH template; NIP-46 BunkerSigner; NIP-05/94/98 module exports | Source-inspected central crypto/wrap/signer paths and tests; helpers do not constitute a durable business queue | Strong lightweight TypeScript reference candidate; application must own routing, validation and state |
| Rust Nostr + nostr-sdk/nostr-connect | NIP-44/59 code, signer abstraction and SDK; README lists 05/17/42/44/46/59/65/94/98/B7; storage/gossip/blossom workspace crates | Core source inspected; support table says tests exist behind feature flags; README explicitly calls the libraries ALPHA with breaking APIs | Strong independent reference candidate; pin revisions/features and avoid assuming API stability |
| NDK core + messages | README lists 17/42/44/46/59/65; messages package claims kind 10050 discovery, 1059 subscriptions, deduplication, persistence adapters | High-level messaging behavior is a maintainer claim; NIP-46 source inspected; complete message validation and current file profile were not verified | Promising integration candidate after conformance; SDK convenience must not define NBDP semantics |
| go-nostr | `GetDMRelays`, `PublishMessage`, AUTH retry; NIP-44 and NIP-59 source | Source inspected; old length format and differing unwrap behavior; maintenance-mode README, archived repository UI | Legacy compatibility target; not preferred for a new dependency without separate successor evaluation |

Sources for the first row: [exports/manifest](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/package.json), [nip17.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip17.ts), [nip44.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip44.ts), [nip59.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip59.ts), [nip42.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip42.ts), [nip46.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip46.ts), [nip98.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip98.ts). Second row: [support table / state](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/README.md), [nostr/src/nips/nip44/v2.rs](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip44/v2.rs), [nostr/src/nips/nip59.rs](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip59.rs), [nostr-sdk/src/client/mod.rs](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr-sdk/src/client/mod.rs). Third: [README.md](https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/README.md), [messages/README.md](https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/messages/README.md), [core/src/signers/nip46/index.ts](https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/core/src/signers/nip46/index.ts). Fourth: [README.md](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/README.md), [nip17/nip17.go](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/nip17/nip17.go), [nip44/nip44.go](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/nip44/nip44.go), [nip59/nip59.go](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/nip59/nip59.go).

The [go-nostr repository page](https://github.com/nbd-wtf/go-nostr) was observed as archived, showing January 24, 2026 as the archive date. Archive status is administrative metadata, not a property encoded by a Git commit. The pinned README's maintenance-mode/successor notice is the reproducible source-level basis for the recommendation. The successor was not successfully source-evaluated here; no compatibility or maturity conclusion is made about it.

## NIP-44 size compatibility

| Implementation | Source evidence | Consequence |
| --- | --- | --- |
| Current official NIP-44 v2 | [Encryption / length prefixes][N44]: max 2^32−1; 2-byte prefix below 65,536, 6-byte prefix at/above it | Current format differs from older implementations while keeping version 2 |
| nostr-tools pin | [nip44.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip44.ts): `maxPlaintextSize = 0xffffffff`, `extendedPrefixThreshold = 0x10000`, extended pad/unpad paths | Supports extended lengths in inspected source; runtime allocation ceilings still apply |
| Rust Nostr pin | [nostr/src/nips/nip44/v2.rs](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip44/v2.rs): `MAX_PLAINTEXT_SIZE = u32::MAX`, extended-prefix handling and platform allocation checks | Supports extension in source, with explicit platform-size checks |
| go-nostr pin | [nip44/nip44.go](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/nip44/nip44.go): `MaxPlaintextSize = 0xffff` and legacy padding | Extended payloads cannot be assumed interoperable with this pin |
| NDK pin | [core/package.json](https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/core/package.json) and inspected signer API do not establish all execution paths' size support | Treat as unverified; test the chosen signer, crypto dependency and messages package together |

nostr-tools [existing tests](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip44.test.ts) include 65,535/65,536/65,537 boundaries, UTF-8 byte-length boundaries, malformed extended headers and spec checksum vectors. Rust [tests in v2.rs](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip44/v2.rs) contains vector tests, extended-prefix boundaries and layout/overflow cases. These are evidence of test coverage in source, not a claim that this research ran them or that every emitted wrap works cross-library.

Both encryption inputs matter: rumor JSON goes into the seal, and seal JSON goes into the wrap. Keeping document content below 65,535 bytes alone does not guarantee compatibility with an older implementation. Enforce a full-wrap envelope limit and test actual serialization. Evidence: [NIP-17 Encrypting][N17], [NIP-44][N44], and the source constants above.

## Security-sensitive source findings

These are bounded code observations, not a formal security audit or new vulnerability disclosure.

| Path | Observed behavior | Requirement for an NBDP integration |
| --- | --- | --- |
| nostr-tools `unwrapEvent` | Checks outer kind, decrypts, checks seal kind/signature, compares rumor pubkey to seal pubkey. The inspected function does not first call `verifyEvent(wrap)` or visibly recompute rumor ID / enforce empty seal tags | Verify outer signature/ID before invoking it, check complete structure/recipient, recompute rumor ID; do not equate a helper return with full profile validity |
| Rust `UnwrappedGift` | Checks kind and verifies outer event before decrypting; verifies seal; `parse_unwrapped_gift` rejects author mismatch. The inspected helper does not visibly enforce all NBDP rumor/recipient/tag rules | Still perform profile checks and inspect `UnsignedEvent` parsing/ID semantics before trusting externally supplied rumor IDs |
| go-nostr `GiftUnwrap` | Verifies seal signature, then overwrites rumor pubkey with seal pubkey and recomputes rumor ID, rather than rejecting author mismatch; no outer-signature/kind check is visible in that helper | Explicit validation wrapper or another evaluated implementation needed for strict NIP-17 author-matching behavior |
| nostr-tools `nip17.wrapManyEvents` | Calls the one-recipient builder per recipient, including self, so each inner event has a different recipient set. The group room is defined by sender + inner p-tags | Do not use this helper unexamined for a stable multi-recipient conversation/document identity; construct/verify one canonical rumor and wrap it per recipient |
| NDK NIP-46 `encrypt/decrypt` | Inspected methods default their scheme argument to `nip04` | Explicitly select NIP-44 for NBDP; test that the higher-level path does not silently downgrade |
| nostr-tools NIP-44 `decodePayload` | Minimum-length checks and base64 decoding are visible, with no configurable small application cap in that function | Bound input before decoding; a theoretical 4 GB format maximum is not an acceptable application allocation budget |

Exact source URLs/revisions: [nip59.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip59.ts), [nostr/src/nips/nip59.rs](https://github.com/nostrdevkit/nostr/blob/463f0c2d48e1d3c9e295cc231715d8a3855c65d3/nostr/src/nips/nip59.rs), [nip59/nip59.go](https://github.com/nbd-wtf/go-nostr/blob/18369d469538b931c8b80ebf3c77420aec804d95/nip59/nip59.go), [nip17.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip17.ts), [core/src/signers/nip46/index.ts](https://github.com/nostr-dev-kit/ndk/blob/4b86acd13fe3c1284fddcb81a7f0d63e491db64a/core/src/signers/nip46/index.ts), [nip44.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip44.ts). Specification comparison: [NIP-44 signature-before-decryption][N44], [NIP-17 mandatory author comparison and room definition][N17], [NIP-59 empty seal tags][N59].

nostr-tools [unwrap tests](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip59.test.ts) cover sender mismatch, invalid seal signatures, wrong wrap kind and bad-event skipping. That does not establish every unchecked condition above. The group-builder finding is based on static source reading, not an executed interoperability failure; one-to-one use has different implications than a group.

Remote signers add another trust boundary: verify both returned signatures and agreement with the requested author, kind, content, timestamp and tags. A valid signature alone does not prove the signer returned the requested event. nostr-tools `BunkerSigner.signEvent` visibly calls `verifyEvent` on its response; the integration should establish exact request/response matching independently. Evidence: [nip46.ts](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip46.ts), [NIP-46 user/signer/client distinction][N46].

## Storage, relays, clients and signers

| Component | Pin-specific evidence | Implication and verification still needed |
| --- | --- | --- |
| Amethyst | [README.md](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/README.md): declares 17/42/44/46/59/65/94/96/98, Android client and MIT license | Demonstrates a maintainer-declared existing client surface; not proof of current kind 15 byte compatibility, extended-size interoperability, or NBDP parsing |
| Amber | [README.md](https://github.com/greenart7c3/Amber/blob/dc3f672eb6c41e1839c06e09b793777313a09cdc/README.md): Android event signer, key segregation and phone as NIP-46 device | Candidate user-controlled signer; evaluate consent/session/revocation and NIP-44 file/document operations with actual clients. README badge and contribution license wording differ, so audit LICENSE before adopting |
| strfry | [strfry.conf](https://github.com/hoytech/strfry/blob/4cd3cf64850caf47dda46c2a2abbbf3525a64d10/strfry.conf): `maxEventSize = 65536`; auth section enables NIP-42 with restricted read kinds `4,1059` and involved-key filter policy | Shows available configuration, not deployed guarantees. Test per-event recipient enforcement, mixed filters, COUNT/negentropy leakage, service URL configuration, timestamp acceptance and restart retention |
| nostr-rs-relay | [README.md](https://github.com/scsibug/nostr-rs-relay/blob/b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4/README.md): NIP-42 checklist; [config.toml](https://github.com/scsibug/nostr-rs-relay/blob/b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4/config.toml): commented `nip42_auth` and `nip42_dms` settings mentioning kind 1059 | Access protection requires correct configuration; README support alone does not establish recipient-only privacy |
| Blossom BUD-01/02 | [buds/01.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/01.md): hash-addressed GET/HEAD, CORS, optional redirects and Sunset; [buds/02.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/02.md): upload and descriptors | Ciphertext can be stored independently of relays; HTTP host sees access timing/size. Hash validation remains essential; no indefinite storage guarantee |
| Blossom BUD-03/04/06 | [buds/03.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/03.md): kind 10063 server lists; [buds/04.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/04.md): mirroring; [buds/06.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/06.md): upload preflight | Interchangeable hosts and replicas, with optional preflight; availability and retention remain operational |
| Blossom BUD-11/12 | [buds/11.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/11.md): kind 24242, expiration/action/server/hash scoping, base64url without padding; [buds/12.md](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/12.md): management endpoints | Distinct from NIP-98 kind 27235. Server-bound tokens reduce cross-host replay; management authorization is not recipient confidentiality |
| blossom-server | [README.md](https://github.com/hzrd149/blossom-server/blob/a492dc61c4a581bbd0992546b2aec6f9aa543f75/README.md): BUD features, configurable retention/allowlist rules, auth and list settings | Candidate self-hostable storage; confirm exact current BUD token encoding/hash requirements and non-transforming opaque upload behavior in runtime tests |

The blossom-server README still describes some management operations under BUD-02 and uses general “base64” language, while the pinned current BUD-02 delegates management to BUD-12 and BUD-11 explicitly requires unpadded base64url. **Inference:** documentation labels do not establish exact protocol revision conformance; verify actual source/runtime before choosing an adapter. Evidence: the pinned BUD and server README links above.

Neither AUTH configuration nor a paid storage plan supplies authenticated recipient delivery or an independent archival guarantee. NIP-42 proves a connection's key control; NIP-01 OK proves relay acceptance. File-server retention remains an explicit operator policy. Evidence: [NIP-42][N42], [NIP-01][N01], blossom-server retention rules above.

## Other relevant protocol work

NIP-B7 is now in the official NIP snapshot; [NIP-96][N96] is unrecommended. Use [NIP-B7][NB7] and the separately pinned BUD revision when specifying a preferred storage adapter. Maintaining legacy NIP-96 compatibility is different from recommending it for a new profile.

[NIP-EE][NEE] points to Marmot and is unrecommended. At the pinned Marmot revision, [README.md](https://github.com/marmot-protocol/marmot/blob/7fabb81b3ed6e2fffeb1b267a0d2ae92b0ab2c89/README.md) describes an adopted specification using Nostr identity and event-shaped unsigned application payloads with MLS continuous group key agreement; [principles.md](https://github.com/marmot-protocol/marmot/blob/7fabb81b3ed6e2fffeb1b267a0d2ae92b0ab2c89/principles.md) requires redundant transport and precise conformance semantics. Its README marks the MIP-era documents deprecated. This research did not evaluate Marmot's full state machine, implementations or security guarantees; it is an investigation candidate if forward secrecy, post-compromise recovery or device-group membership becomes mandatory, not a drop-in conclusion.

NIP-44's [Audit section][N44] references a **December 2023** Cure53 report at [commit ce63c2eaf345e9f7f93b48f829e6bdeb7e7d7964](https://github.com/paulmillr/nip44/blob/ce63c2eaf345e9f7f93b48f829e6bdeb7e7d7964/audit-2023.12.pdf). The existence/date of that audit is specification evidence; no current SDK, extended-prefix change, attachment implementation, deployed relay or NBDP business state machine is declared audited here.

## Recommended next evaluation

Prefer a pinned nostr-tools/Rust pair for independent transport corpus comparisons, then separately exercise local and remote signer adapters. Consider NDK only after confirming its message package preserves the same wire/validation rules. Keep the old Go implementation in the corpus to expose length/strictness compatibility boundaries, without making it the default.

The later test corpus should cover official vectors, outer and seal signature tampering, author mismatch, malformed rumor IDs/tags, multi-recipient identity, UTF-8/size limits at both layers, kind 10050 discovery failure, AUTH reconnect, backdated history/pagination, durable deduplication/receipts, exact GCM blob bytes and unavailable mirrors. This is a proposed research plan; it was not executed and introduces no repository implementation.

The decision matrix remains in [transport-comparison.md](transport-comparison.md#decision-matrix). Library availability supports starting with option B, while maturity evidence does not yet support declaring an NBDP production profile interoperable.

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
[N66]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/66.md
[N67]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/67.md
[N70]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/70.md
[N77]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/77.md
[N78]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/78.md
[N89]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/89.md
[N92]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/92.md
[N94]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/94.md
[N96]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/96.md
[N98]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/98.md
[NB7]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/B7.md
[NEE]: https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/EE.md
