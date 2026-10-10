# Transport comparison for NBDP

Research date: **2026-10-11**. NIP source snapshot: **`a79e21d90fce5465b50ef385dd368bba99ec4a0b`**. All NIP links pin this commit. This document compares architectural choices; proposed envelope fields and policies are research recommendations, not implementation code or an adopted specification.

## Decision

**Recommend B: existing NIPs plus an openly specified business-document application protocol inside encrypted payloads.** Retain persistent kind 1059 gift wraps and the NIP-17 inbox/discovery model. Do not allocate a new kind now. Publish the application specification independently, require no operator's permission to implement it, and later consider a profile NIP only if independent implementations establish a reusable interoperability gap.

This follows from available encrypted messaging/file primitives in [NIP-17][N17], general encapsulation in [NIP-59][N59], and the absence of business receipt/idempotency semantics in those texts. It is a design conclusion, not an official Nostr recommendation. Evidence and caveats are developed below and in [nostr-landscape.md](nostr-landscape.md).

## Precisely defining the three options

| Option | Meaning in this comparison | Example | Does it introduce a kind? |
| --- | --- | --- | --- |
| A | Existing message/file conventions, with no shared NBDP business envelope/state machine | Send a plain-text DM and an encrypted PDF/XML file, discuss acceptance in ordinary messages | No |
| B | Existing transport plus a versioned, vendor-neutral NBDP envelope, manifest and receipt protocol inside encryption | A text-encoded envelope correlates a document, exact-byte digest and receipt state | No |
| C | Formal NIP standardization and/or new kind allocation | A profile NIP codifying B; a new encrypted inner document rumor; or a new outer transport kind | Depends on the suboption |

A and B both satisfy “without a new Nostr event kind.” They differ in application semantics, not cryptography. A new NIP is also not synonymous with a new kind: a profile NIP could describe B unchanged. Comparisons that equate A with “unstructured public events” or C with “better encryption” would obscure the actual decision. Evidence: [NIP-44 defines no messaging kind][N44], [NIP-59 does not define a messaging protocol][N59], [NIP-17 Message Rumor Definitions][N17].

## Shared transport foundation

For all three options, identity can remain a public key and documents can remain independently exchanged over relays. Optional NIP-05 identifiers improve contact discovery but must not be required for membership. NIP-65 helps locate public relay metadata; strict NIP-17 delivery requires recipient kind 10050 inboxes, and absence must not cause arbitrary fallback sending. NIP-42 enables recipient-access restrictions and authenticated publication where required. Evidence: [NIP-05][N05], [NIP-65][N65], [NIP-17 Publishing and Relays][N17], [NIP-42][N42].

The recommended shared choices are:

- Persistent kind 1059 rather than ephemeral kind 21059 for offline documents and receipts. Evidence: [NIP-59 Protocol Description][N59].
- Per-recipient and sender copies, with randomized outer/seal timestamps and no public business classifications. Evidence: [NIP-17 Encrypting][N17].
- Local encryption of blobs, private file URLs/keys/hashes, independently selectable hosts, and optional mirroring. Evidence: [NIP-17 File Message][N17], [NIP-B7][NB7].
- Mandatory application validation beyond relay acceptance, with local outbox and archives. This is a recommendation based on [NIP-01 OK semantics][N01] and [NIP-59 storage discretion][N59].
- Explicit NIP-44 capability and resource limits. Evidence: [NIP-44 Implementation considerations][N44] and [library size differences](library-evaluation.md#nip-44-size-compatibility).

None of these choices requires Satflux, Peppol, government-issued identity, one relay operator, one directory, or a proprietary signer service. Paid/authenticated relay access can exist as an optional commercial service; permissionless protocol participation does not mean every operator must offer unrestricted free storage. This is a design interpretation of optional, independently implemented [Nostr specifications][NREADME].

## A. Existing NIPs without application business semantics

A can deliver a human-readable document exchange using kind 14 text and kind 15 files. Replies can refer to prior messages, and encrypted reactions can convey informal approval. Existing chat clients can potentially render those conventions without an NBDP parser, subject to actual file support. Evidence: [NIP-17 Chat Message, File Message and reaction convention][N17]; deployed support is bounded by [library evaluation](library-evaluation.md).

A is suitable for a manual exchange experiment. Its weakness is machine interpretation: the NIPs do not standardize business document type, schema version, transaction/document identifiers, exact-byte business commitments, acknowledgment authority, accepted/rejected state, or invoice deduplication. A text reply saying “received” can be authenticated as a sender's message but has no specified processing meaning. Evidence: [NIP-17 Message Rumor Definitions][N17], [NIP-59 application scope][N59]. This is an absence finding within the inspected standards.

A does not escape the need for policy; each implementation would invent its own receipt interpretation, naming, routing edge cases and replay state. Once those rules become a common business interchange contract, the result is B. **Conclusion:** A is a useful baseline/control and human fallback, but insufficient as the full interoperable business protocol.

## B. Existing NIPs with an encrypted business application protocol

B keeps relay-visible events unchanged. For a first profile, a kind 14 rumor can carry a textual UTF-8 serialization of a versioned envelope, possibly alongside separate kind 15 file messages or a private manifest referencing blobs. NIP-17 requires plain-text content; treating text-serialized JSON as such is a reasonable interpretation, but chat clients will render raw text and client UX compatibility needs testing. Do not claim existing chat clients understand the business envelope. Evidence: [NIP-17 Chat Message][N17].

Proposed envelope subjects, to be specified before implementation:

| Subject | Required shared meaning | Why transport alone is insufficient |
| --- | --- | --- |
| Protocol/profile identifier and version | Unambiguous discriminator; supported versions; reject unknown mandatory features; bounded extension behavior | NIP-17 is a messaging profile, not a business schema [NIP-17][N17] |
| Sender/recipient/context | Authenticated seal key; intended business endpoint; capability/trust context; no silent key replacement | Cryptographic identity and organization authority differ [NIP-01][N01], [NIP-05][N05] |
| Message and document identity | Stable random logical ID; revision/relationship; exact-byte digest; sender/recipient scope | New wraps have new outer IDs [NIP-59][N59] |
| Document description | Media/schema identifier and version, byte size, content commitments, optional human summary | Kind 15 defines file fields but not business document meaning [NIP-17][N17] |
| Attachment manifest | Ciphertext and plaintext commitments, crypto suite/encoding, keys/nonces, source/fallbacks, ordering and size limits | NIP-94 supplies metadata conventions, not a complete confidential business manifest [NIP-94][N94] |
| Receipt | Correlation, document digest, authenticated responder, receipt type/state, error vocabulary | Relay OK is only event acceptance [NIP-01][N01] |
| Freshness/idempotency | Validity policy, retained deduplication state, conflict handling, bounded retries | Encryption/signatures do not define business replay handling [NIP-17][N17], [NIP-44][N44] |
| Optional portable proof | Exact signed bytes and domain separation for documents/receipts | Unsigned rumors alone have no public document signature [NIP-59 Overview][N59] |

These are **proposed application requirements**, not existing NIP fields. Do not standardize a vendor's database model, internal billing APIs, mandatory invoice format, or national registration system. A transport manifest can carry multiple document syntaxes; document schemas remain separate, explicitly versioned profiles.

Capabilities should be exchanged privately with a known contact or supplied through independent contact exchange. A public capability event could be considered later, but exposes business roles/service information and creates discovery freshness/rollback questions. Unknown contacts and unsupported versions must produce explicit local outcomes rather than silent encryption downgrade. These are privacy/interoperability recommendations derived from [NIP-59 metadata boundaries][N59] and [NIP-44 version handling][N44].

### Receipt and retry semantics that B must settle

A minimal proposed state sequence separates:

1. **Queued:** local preparation exists.
2. **Relay accepted:** one or more advertised relay(s) accepted that recipient wrap.
3. **Recipient received:** an authorized recipient client authenticated and durably recorded the envelope.
4. **Document validated:** referenced bytes were fetched, decrypted, hashed and structurally checked.
5. **Business accepted or rejected:** an authorized endpoint made a defined application decision.

Only stage 2 corresponds to existing relay `OK`; the remaining states need explicit application meaning. A receipt should not claim validation until required attachments are available, and business acceptance should not be automatic merely because XML parses. Evidence for the transport boundary: [NIP-01 relay messages][N01], [NIP-17 file references][N17]. This proposed sequence does not claim payment, accounting posting or legal acceptance.

A retry can republish the identical wrap or create another wrap with fresh outer key/nonces/timestamps. In both cases, retain the same application ID and exact document commitment for the same operation. Rewrapping should preserve logical rumor identity where possible. An ID reused with another hash is a conflict requiring rejection/quarantine, not a new processing request. Keep per-recipient delivery tracking, since one peer's acknowledgment says nothing about another's copy. Basis: [NIP-59 separate recipient wraps][N59]; these replay rules are **proposals**.

The target is at-least-once delivery attempts with durable, idempotent business effects. “Exactly once” cannot be guaranteed by changing a kind: a recipient can crash after recording an effect and before emitting a receipt, and receipts can be lost. Cross-device decision state and business action authority must converge. This is a distributed-systems inference from independent async relay delivery in [NIP-17][N17] and no recipient acknowledgment in [NIP-01][N01].

### Attachment and size policy for B

Use small private manifests rather than large documents inline. Current NIP-44's approximately 4 GB format limit is not a practical interoperability budget. Old implementations still have a 65,535-byte encryption-input cap, and the serialized seal is a second encryption input, potentially larger than the original rumor. Evidence: [NIP-44 length prefixes][N44], [library source comparison](library-evaluation.md#nip-44-size-compatibility).

For a plaintext input of P bytes, let pad(P) be the NIP-44 padded content length and prefix(P) be 2 or 6 bytes. A single encrypted payload has base64 length:

**4 × ceil((65 + prefix(P) + pad(P)) / 3).**

The 65 bytes are version, nonce and MAC. Apply this separately to rumor JSON and seal JSON, then include complete outer event JSON and the NIP-01 EVENT array when checking relay limits. This formula is derived directly from [NIP-44 Encryption and pseudocode][N44]; it is not a measured SDK result. Base64/padding therefore amplify size twice.

**Provisional research target:** test a small-manifest profile against a 16 KiB complete publication frame ceiling, with separate application and file limits. This is a candidate test budget, not a proven network capability or adopted NBDP limit. Choose the final budget from two-client/relay measurements. Respect both NIP-11 character and frame-byte constraints and reject malicious oversized decrypted structures. Evidence: [NIP-11 Server Limitations][N11].

Blossom stores hash-addressable bytes and allows server lists/mirrors; locally encrypt before uploading, use opaque MIME/extension where possible, and avoid file-host media transformation paths for encrypted document bytes. Specify exact GCM byte layout, key size and nonce encoding; omit the optional thumbnail behavior pending clarification. NIP-96 should be a legacy adapter if needed, not the normative preferred storage API. Evidence: [NIP-17 File Message][N17], [NIP-B7][NB7], [NIP-96 deprecation][N96], [Blossom source evaluation](library-evaluation.md#storage-relays-clients-and-signers).

## C. A new NIP and/or new kinds

C has three materially different forms:

| Form | What it gains | What it costs / does not solve |
| --- | --- | --- |
| C1: Profile NIP, existing kinds | Formal shared reference for B's envelope/receipt conventions | Standardization work; no new relay behavior, cryptographic property or retention guarantee |
| C2: New inner rumor kind, existing 1059 transport | Distinguishes business objects after decryption; purpose-specific schema and client dispatch | New parser/handler support; generic messaging clients may ignore unknown rumors; no public classification if correctly wrapped |
| C3: New outer kind and/or relay messages | Could introduce specialized relay behavior if a concrete need is demonstrated | New relay/client deployment; potentially visible business classification; does not itself provide confidentiality, replay protection or durable delivery |

C2 follows NIP-59's ability to encapsulate any unsigned event kind. It could avoid stretching kind 14's chat semantics, but requires meaningful client agreement and allocated semantics. C3 should be evaluated only for behavior that cannot live inside encryption, such as a genuinely useful relay-level extension; confidential application receipts ordinarily do not need it. Evidence: [NIP-59 rumor definition][N59], [NIP-17 kind conventions][N17], [NIP-01 kind categories][N01].

Do not choose NIP-78 kinds merely because they already exist: its specification explicitly excludes generic interchange between applications. Do not allocate an ephemeral or replaceable kind for immutable delivery/history unless its consequences are intentional. Outer 1059 already supplies persistent encapsulation, independently of the inner business object's semantics. Evidence: [NIP-78][N78], [NIP-01 event categories][N01].

A new NIP/kind does not produce organizational identity trust, forward secrecy, traffic anonymity, retention, file availability, or exactly-once processing automatically. Such gains require concrete cryptography, state semantics, storage behavior, and deployment. Existing NIP-44 lacks forward secrecy and post-compromise security regardless of the event-kind number. If those properties become mandatory, investigate Marmot/MLS independently; deprecated NIP-EE is not the current specification. Evidence: [NIP-44 Limitations][N44], [NIP-EE deprecation][NEE], [Marmot pin and scope](library-evaluation.md#other-relevant-protocol-work).

## Interoperability and independence gates

Before considering a first profile sufficiently specified, require a public conformance corpus and two independent implementations to agree on authenticating wraps, malformed input, exact attachment bytes, logical duplicates, conflicting IDs, receipt transitions, bounded replay, backdated/offline recovery and key continuity. Require at least two relay implementations/policies in that exercise; do not confuse that research target with the official NIP acceptance criterion of one relay where applicable. Evidence for the latter: [README Criteria for acceptance][NREADME].

No mandatory dependency may bind participants to a specific operator for identity creation, discovery, publication, file retrieval, signing, schema hosting or conformance authorization. A self-hosted/configurable bootstrap and signer path is required by NBDP's independence objective. Multiple library wrappers around the same undocumented vendor backend are not independent protocol interoperability.

## Unresolved risks

The principal remaining risks are public recipient and network/file-host correlation; historical decryption after key compromise; lack of minimum offline retention; attachment crypto/encoding ambiguity and nonce reuse wording; lost or conflicting receipts; cross-device duplicate effects; mutable discovery under key rotation; and uneven SDK/relay support. All affect B and most affect A/C equally. [Open questions](open-questions.md) assigns decision evidence to each; [landscape analysis](nostr-landscape.md) identifies exact spec boundaries.

A mandatory forward-secrecy requirement would invalidate the simple NIP-44 baseline for all options as presented. Inability to fit machine-object semantics cleanly into existing inner message conventions could favor C2 after conformance evidence. A wish for a recognizable protocol name or a dedicated UI badge is not sufficient evidence for a new outer kind.

## Decision matrix

Scores are **research judgments**: 1 = weak fit, 5 = strong fit. C is shown as C2 (a new inner kind with the same encrypted transport), the most plausible kind-changing variant. C1 has B's wire properties; C3 has additional deployment/privacy costs. The evidence column links the capability or limitation underlying each judgment.

| Criterion | A | B | C2 | Evidence / interpretation |
| --- | --- | --- | --- | --- |
| Independence / permissionless participation | 5 | 5 | 5 | All can use public-key identity and interchangeable operators [NIP-01][N01], [NIP-05][N05] |
| Sender/recipient discovery | 4 | 4 | 4 | Existing inbox discovery works; bootstrap/key trust unresolved [NIP-17][N17], [NIP-65][N65] |
| Content confidentiality / metadata minimization | 3 | 3 | 3 | Same wrapper, visible recipient and traffic; no forward secrecy [NIP-44][N44], [NIP-59][N59] |
| Authenticated business delivery semantics | 2 | 4 | 4 | Authentication exists; receipt/schema semantics need B/C definition [NIP-17][N17], [NIP-01][N01] |
| Attachment interoperability | 3 | 4 | 4 | Kind 15 exists; strict shared byte profile still needed [NIP-17][N17] |
| Offline availability / retention | 2 | 3 | 3 | B/C can define retry/archive policy; no transport durability promise [NIP-59][N59], [NIP-11][N11] |
| Multi-device processing / key rotation | 2 | 3 | 3 | Signers exist; common processing/continuity profile absent [NIP-46][N46], [NIP-05][N05] |
| Receipts / retries / duplicates / replay | 1 | 4 | 4 | Application semantics supply the gain, kind allocation does not [NIP-01][N01], [NIP-17][N17] |
| Independent business-client interoperability | 2 | 4 | 4 | Requires open schema and conformance in B/C; not yet demonstrated |
| Existing library/relay reuse | 5 | 4 | 3 | B preserves kinds; C2 needs inner dispatch support [library evaluation](library-evaluation.md) |
| Low deployment / standardization burden | 5 | 4 | 2 | B needs application agreement; C2 also needs kind agreement [NIP acceptance criteria][NREADME] |
| Ability to start research without premature allocation | 5 | 5 | 2 | Existing encapsulation already supports an application profile [NIP-59][N59] |

**Recommendation:** choose B for the initial open NBDP profile, keep A as a human exchange baseline, and defer C until independent implementations identify a gap that requires formal profile standardization or a dedicated inner kind. Do not introduce a public outer business kind without a concrete relay-level requirement and a metadata review. The scores deliberately do not total away unresolved security requirements: threat-model approval, file byte-profile clarification and independent conformance evidence remain gates.

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
