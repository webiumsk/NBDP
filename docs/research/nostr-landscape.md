# Nostr landscape for NBDP

Research date: **2026-10-11**. Recommendation: use existing Nostr transport with a public, versioned business-document protocol inside encryption (option B). A new event kind is not presently justified. This is a research recommendation, not an adopted NBDP specification.

## Scope and evidence method

NBDP is an open, permissionless document exchange protocol. Participation must not require Satflux, Peppol, government registration, a particular DNS provider, relay, file host, signer service, or central directory. Those systems could implement optional adapters; none defines protocol identity or authorization.

The official NIPs repository was resolved through Git remote HEAD to **`a79e21d90fce5465b50ef385dd368bba99ec4a0b`**, then relevant files were read at that exact commit through the GitHub connector. Every NIP link below pins that snapshot. “Current” means that observed repository state on the research date, not universal deployment. NIPs are optional implementation possibilities; their presence in the repository does not imply every client or relay supports them. The repository also recognizes standards outside its own index. Evidence: [README introduction and repository governance][NREADME].

The evidence categories used across these documents are:

- **Specification:** an explicit rule or property in pinned normative text.
- **Source inspection:** behavior visible in pinned implementation code; not a runtime test.
- **Maintainer claim:** README/support table declaration, with no independent conformance proof.
- **Inference/recommendation:** a conclusion from cited evidence or a proposed NBDP policy.
- **Unverified:** deployment, security, or behavior not established by this research.

No implementation code was written and no live client interoperability, relay retention, signer, or attachment tests were run. Library source and existing tests were inspected, not executed. The implementation pins and limitations are in [library-evaluation.md](library-evaluation.md). Options and the final decision matrix are in [transport-comparison.md](transport-comparison.md); unresolved decisions are in [open-questions.md](open-questions.md).

## Required NIPs: observed capabilities and boundaries

All rows refer to NIPs revision `a79e21d90fce5465b50ef385dd368bba99ec4a0b`. Section names identify the evidence.

| NIP | Status in file | Relevant evidence | Consequence for NBDP |
| --- | --- | --- | --- |
| [17][N17] | draft, optional, relay | Encrypting: unsigned rumors, signed kind 13 seals, kind 1059 wraps; Publishing: kind 10050 DM inboxes; Message Rumor Definitions: kinds 14 and 15 | Established private message and encrypted file transport; no business schema or recipient receipt state machine |
| [44][N44] | optional; encryption version 2 | Limitations; Encryption; Decryption; Implementation considerations | Authenticated encryption and padding; no forward secrecy or post-compromise security; current theoretical plaintext maximum is 2^32−1 bytes |
| [59][N59] | optional, relay | Overview; Protocol Description; Other Considerations | Generic rumor encapsulation hides sender and inner event; persistent 1059 and ephemeral 21059 differ; no messaging semantics by itself |
| [05][N05] | final, optional | Identification, not verification; Clients must always follow public keys | Optional DNS/HTTPS alias discovery; mutable domain mapping must not silently replace a trusted key |
| [65][N65] | draft, optional | kind 10002; read/write routing and Discoverability | Public relay discovery; does not replace NIP-17's dedicated kind 10050 inbox requirement |
| [42][N42] | draft, optional, relay | Canonical authentication event; Protocol flow; Signed Event Verification | Connection-scoped relay authentication using kind 22242, relay URL, challenge, and freshness; does not authenticate a business organization |
| [46][N46] | no status label in file | Terminology; Methods/Commands; Requested permissions; Ending a session | Remote signing and NIP-44 operations; signer, client, and user keys are distinct concepts; no organizational key succession protocol |
| [94][N94] | draft, optional | Event format: kind 1063, URL, MIME, hashes, sizes, fallbacks | File metadata/indexing, not encryption or storage; public publication exposes metadata |
| [96][N96] | draft, unrecommended, optional | Deprecation banner; Server Adaptation; Auth; Upload | Legacy HTTP upload integration, using NIP-98; explicitly superseded by NIP-B7/Blossom |
| [98][N98] | draft, optional | Nostr event validation; Request Flow | HTTP request authorization using kind 27235; URL/method/time binding and optional body binding; no document delivery receipt |

## 1. Sender/recipient identity and discovery

A Nostr event identifies a cryptographic principal through its public key; its ID is a SHA-256 hash of the specified serialized event fields and its signature uses Schnorr/secp256k1. This establishes control of a signing key, not a company's existence, authority of an employee, or the truth of an invoice. Evidence: [NIP-01 Events and IDs][N01]. The organizational distinction is an **inference** from the cryptographic validation scope.

NIP-05 maps an email-shaped alias to a public key through `https://<domain>/.well-known/nostr.json?name=<local-part>`, cross-checked against profile metadata. Its own text distinguishes identification from verification and tells clients to retain public keys when domain mappings change. DNS and HTTPS create trust and availability dependencies for that alias. Recommendation: accept raw public keys and out-of-band contact exchange as first-class entry points; treat NIP-05 as optional corroboration. Evidence: [NIP-05 lookup, notes, and security constraints][N05].

NIP-19 encodings and NIP-21 URIs are useful contact presentation conventions, listed in the [official index][NREADME]; they should not become a mandatory central identity registry. Discovery has a bootstrap problem: a sender needs somewhere to locate a signed kind 10050 event. NIP-65 kind 10002 lists general read/write relays and recommends wide distribution; NIP-05 may return relay hints. **Inference:** configurable bootstrap relays, peer-supplied hints, cached signed lists, and direct contact exchange can reduce dependence on any single indexer, but cannot prove that an unavailable list does not exist. Evidence: [NIP-65 Discoverability][N65], [NIP-05 relays attribute][N05], [NIP-17 Publishing][N17].

For strict NIP-17 sending, publish recipient wraps only to the recipient's kind 10050 relays. An absent list signals that the user is not ready for DMs and clients should not try sending. Do not silently fall back to arbitrary NIP-65 read relays or a product-owned relay. Sending a copy to the sender means a separate wrap addressed to the sender and routed according to that identity's inbox. Evidence: [NIP-17 Encrypting and Publishing][N17].

## 2. Confidentiality and metadata leakage

The private transport is rumor → NIP-44 encryption → signed seal → NIP-44 encryption → one-time-key gift wrap. The rumor includes the document or a manifest, sender, recipients, real timestamp, and application metadata; the relay sees the outer event. Kind 13 has empty tags and an unsigned inner event. Evidence: [NIP-59 Protocol Description][N59], [NIP-17 Encrypting][N17].

| Observer | Visible or inferable | Protected by the standard construction | Residual risk / evidence |
| --- | --- | --- | --- |
| Anyone obtaining the outer event | kind 1059, recipient `p` tag, wrapper key, event ID/signature, randomized timestamp, ciphertext length, any additional outer tags | Sender key, document, inner kind/tags, full participant set | Recipient is explicitly public in event structure; avoid public document type, invoice ID, hashes, or subject [NIP-59][N59] |
| Receiving relay | Above plus publication arrival time, connection/IP, queried recipient filters, AUTH keys if used | Plaintext and sender from ciphertext alone | AUTH and traffic analysis can link publisher/recipient activity [NIP-42][N42], [NIP-44 Limitations][N44] |
| Colluding relays / network observers | Timing, connection patterns, event sizes, multiple wraps arriving together | Encryption content | Padding and backdated timestamps reduce some correlation; they do not conceal actual arrival times. This is an inference from [NIP-17 Encrypting][N17] and [NIP-44 Limitations][N44] |
| File host/CDN | Encrypted blob bytes, sizes, hash/URL, upload/download timing/IP and any authentication key | Document bytes if encrypted locally | Blob retrieval can correlate peers; a stable ciphertext hash correlates mirrors [NIP-B7][NB7], [Blossom BUD-01 and BUD-11](library-evaluation.md#storage-relays-clients-and-signers) |
| Intended recipient / compromised endpoint | Plaintext document, secret file keys, full rumor metadata | Nothing after successful decryption | A recipient may disclose or retain copies; encryption cannot revoke downloaded bytes [NIP-59][N59], [NIP-09 warning][N09] |

NIP-17's benefits section uses broad metadata-hiding and disappearing-message language. Interpret it against the actual wire format and NIP-44's explicit limitations: the recipient tag is exposed if an outer event is accessible, and static-key ECDH does **not** provide cryptographic forward secrecy. Deletion, expiration, and omitting a sender backup copy are retention choices; a stored ciphertext can still be decrypted after relevant key compromise. NIP-40 explicitly permits indefinite retention and says expiration is not a conversation security feature. Evidence: [NIP-44 Limitations][N44], [NIP-17 Benefits & Limitations][N17], [NIP-40 Relay Behavior and Warning][N40].

**Recommendation:** define privacy as content confidentiality and reduced public sender metadata, with an explicit relay/file-host traffic-analysis limitation. Recipient-only relay access is a SHOULD in NIP-17/59, enforced through AUTH; it is neither universal nor protection against the operator. Evidence: [NIP-17 Relays][N17], [NIP-59 Other Considerations][N59].

## 3. Authenticated document delivery

Successful decryption alone is not the sender-authentication boundary. NIP-44 requires signed-event verification before decrypting. NIP-17 additionally requires seal author = rumor author to prevent impersonation. Proposed NBDP validation should also check expected kinds, empty seal tags, unsigned rumor structure, canonical rumor ID, intended recipient, application version, document commitments, and local trust/authorization policy. The additional checks are **NBDP recommendations**, not a claim that every helper performs them. Evidence: [NIP-44 Decryption][N44], [NIP-17 Encrypting][N17], [NIP-59 Protocol Description][N59]; implementation differences: [library evaluation](library-evaluation.md#security-sensitive-source-findings).

A NIP-01 `OK true` says the relay accepted an event; it is not a recipient signature, proof of decryption, durable archive promise, schema validation result, or business acceptance. The recipient may be offline, a relay may discard a wrap, or an attachment may be unavailable. Evidence: [NIP-01 relay messages][N01], [NIP-59 Other Considerations][N59]. These missing guarantees are **inferences** from the scope of those messages.

NIP-59 rumors are unsigned for deniability, while the seal authenticates sender-originated ciphertext to the recipient. A bare exported rumor is not an independently verifiable document signature. If third-party-verifiable documents or receipts are needed, separately define an optional signed document/receipt object inside the encrypted payload, including exactly what bytes and context are signed. That intentionally weakens deniability for that object and still does not establish legal-person authority. Evidence: [NIP-59 Overview][N59], [NIP-01 signatures][N01]. The signed-object profile is a **proposal**, not an existing NIP guarantee.

## 4. Attachments and size limitations

NIP-17 already defines kind 15 encrypted file messages: `aes-gcm`, file MIME type, decryption key/nonce, URL in content, `x` for encrypted-file SHA-256, `ox` for original-file SHA-256, optional encrypted size and fallbacks. Keep all of those inside the encrypted rumor. NIP-94 has similar descriptive fields but different context: it indexes files and does not supply confidential delivery. NIP-92's `imeta` adds media metadata, not file encryption. Evidence: [NIP-17 File Message][N17], [NIP-94 Event format][N94], [NIP-92][N92].

Current NIP-44 v2 permits 1 through 4,294,967,295 plaintext bytes: lengths below 65,536 use a two-byte prefix, larger lengths use a six-byte extended prefix. The version remains 2. This is a format maximum, not a relay, runtime, SDK, or NBDP envelope limit. Implementations are advised to reject excessive sizes before costly decoding. Archived go-nostr still caps plaintext at 65,535 bytes; inspected JavaScript/Rust heads implement the extension. Evidence: [NIP-44 Encryption and Implementation considerations][N44], [pinned source comparison](library-evaluation.md#nip-44-size-compatibility).

The rumor and serialized seal are encrypted separately, so both encryption calls must fit the selected library limit. Padding, base64 at each layer, JSON, and event signatures make a 64 KiB document much larger on the wire. NIP-11 distinguishes incoming JSON frame bytes from content character count, and exposes maximum tags and timestamp limits. The pinned strfry sample configuration sets normalized event JSON to 65,536 bytes; that is a configuration example, not a network-wide cap. Evidence: [NIP-11 Server Limitations][N11], [strfry configuration](library-evaluation.md#storage-relays-clients-and-signers). **Recommendation:** small encrypted manifests on relays; locally encrypted blobs on independently selectable hosts; bound and measure the complete serialized wrap.

NIP-96 is explicitly unrecommended. NIP-B7 integrates Blossom's content-addressed blob storage and kind 10063 server lists. Blossom BUDs are separately versioned standards, not all official NIPs. Hash-addressed downloads and mirroring improve relocation, but cannot guarantee availability. Blossom uses kind 24242 authorization under BUD-11, not NIP-98's kind 27235; the formats and encodings must not be confused. Evidence: [NIP-96 banner][N96], [NIP-B7][NB7], [pinned Blossom sources](library-evaluation.md#storage-relays-clients-and-signers).

NIP-17's file profile leaves interoperability details to settle, including precise key/nonce encoding, AES-GCM key/tag parameters and blob byte layout. Its thumbnail text also says the same key and nonce are used; encrypting distinct thumbnail and original bytes that way would violate GCM nonce uniqueness. **Security inference:** disable that optional thumbnail feature until clarified; mirroring identical encrypted bytes is different from re-encrypting distinct plaintext. Evidence: [NIP-17 File Message][N17], [RFC 5116, January 2008, §§2.1 and 5.1.1](https://www.rfc-editor.org/rfc/rfc5116.html#section-5.1.1).

## 5. Offline delivery and relay retention

Kind 1059 is a regular event intended for asynchronous/offline delivery; kind 21059 is ephemeral and unsuitable for durable document delivery. NIP-59 nonetheless permits relays to decline storing gift wraps. No cited NIP promises a minimum retention period, redundancy, recipient availability, or recovery after all copies disappear. Evidence: [NIP-01 event categories][N01], [NIP-59 kinds and Other Considerations][N59].

**Recommendation:** maintain a durable local outbox, publish separately to the selected advertised inbox relays, track each relay's acceptance, retain retry material until a defined recipient acknowledgment/deadline, and archive decrypted documents locally. Redundancy should span independently operated relays and blob hosts, not several URLs belonging to one operator. NIP-65 and kind 10050 remain announcements, not storage contracts. Evidence for the underlying boundary: [NIP-65][N65], [NIP-17 Publishing][N17], [NIP-11 limitations][N11].

Subscription recovery must account for up to two days of backdating at the seal and wrap layers. Advancing `since` to the last received timestamp can miss new arrivals with older outer timestamps. Use overlapping windows, ID deduplication, pagination, and periodic reconciliation. NIP-67 now distinguishes completion of available stored results, additional results, and AUTH-gated results; absent hints retain ambiguity. NIP-77 can reconcile stored event sets but cannot recover data no participant retains. Ties, relay caps, missing hints, and new relays require explicit recovery policy. Evidence: [NIP-17 Encrypting][N17], [NIP-01 filters][N01], [NIP-67 Motivation and semantics][N67], [NIP-77][N77]. Recovery policy is an **inference/recommendation**.

## 6. Multi-device use and key rotation

NIP-17 requires a separate copy to the sender; devices able to use that identity's NIP-44 decryption capability can recover retained inbox history. This depends on retention and does not supply synchronization of local processing state, receipt ownership, employee roles, or duplicate suppression across devices. Evidence: [NIP-17 Encrypting and Benefits & Limitations][N17]. A new device cannot recover messages whose wraps or file blobs have disappeared.

For several business participants, encryption/publication fanout grows with the recipient count, and the full inner recipient set is visible to every intended recipient. NIP-17 defines a room by sender plus recipient tags; changing that set creates a new room, with no invitation/admin/ban mechanism. Its limitations recommend a more suitable scheme for groups larger than ten participants. Removing a key from future sends does not revoke previously downloaded documents. Evidence: [NIP-17 Chat Rooms and Benefits & Limitations][N17], [NIP-59 separate recipient wraps][N59]. Distinguish business participant authorization from chat-room membership and device synchronization.

NIP-46 allows remote signing/encryption/decryption without placing the account secret directly in every client. It separates user, remote-signer, and disposable client keys; calls `get_public_key`; supports requested permissions, relay switching, and logout. The signer becomes an availability and authorization dependency, and NIP-44 RPC methods necessarily expose document plaintext to that signer. **Inference:** client-key possession can enable approved actions even without account-key possession. Choose user-controlled signers and narrow permissions; avoid a mandatory operator-hosted bunker. Evidence: [NIP-46 Terminology and Methods/Commands][N46].

NIP-07 and NIP-55 provide browser and Android signer interfaces; NIP-49 encrypts a private key at rest. None of these scopes is an organizational key succession scheme. Sharing one secret across devices creates shared compromise exposure; separate recipient keys increase routing/recovery complexity. Evidence: [NIP-07][N07], [NIP-55][N55], [NIP-49][N49], [NIP-44 Limitations][N44].

Within the evaluated standards, no common business-key rotation/revocation mechanism was established. Changing a NIP-05 alias must not silently replace a pinned contact. NIP-46 relay switching changes signer transport, not account identity. A proposed continuity profile could include old/new-key endorsements, effective time/epoch, rollback handling, recipient consent, and recovery policy; compromise recovery needs external trust if the old key is unavailable or hostile. Evidence: [NIP-05 public-key pinning][N05], [NIP-46 Switching relays][N46]. The absence finding is bounded to the research scope, not proof that no experimental proposal exists.

## 7. Receipts, retries, duplicates and replay attacks

NIP-01 event IDs suppress identical outer-event duplication; rewrapping the same rumor creates a new outer event ID. Neither an event signature nor NIP-44's random nonce prevents replay of an already valid message. NIP-17 reply references and reactions provide conversation relationships but no standardized distinction between received, validated, accepted, and rejected business documents. Evidence: [NIP-01 Events and IDs / duplicate OK][N01], [NIP-59 separate wraps][N59], [NIP-17 Message Rumor Definitions][N17]. Replay and business-semantics findings are **inferences** from these scopes.

**Proposed requirements for option B:** stable application message/document IDs; exact-byte content hashes; authenticated sender and intended recipient; schema and protocol versions; correlation and response type; freshness/expiry policy; durable deduplication; contradictory-ID/hash rejection; bounded retries; and explicit receipt states. Use outer IDs for relay publication tracking, rumor IDs for transport-level logical identity when stable, and application IDs for durable business idempotency. Do not identify an invoice solely by a publicly guessable invoice number or by an outer wrap ID.

Multiple devices can all receive one message and emit conflicting receipts. Require a profile for receipt authority and monotonic state transitions. Persist acknowledgment and deduplication decisions across restart/restore; process with effectively-once business effects on top of at-least-once transport. Unknown status remains unknown when receipts are lost; silence is not rejection or acceptance. These are **design recommendations** derived from the absence of business receipt semantics in [NIP-17][N17] and relay-only acceptance in [NIP-01][N01].

NIP-42 uses connection challenges and freshness to limit AUTH reuse; NIP-98 binds request URL, method and time but has no universal one-use nonce/consumption rule, with body hash checking optional. Require request binding and replay policy for sensitive HTTP actions. Blossom BUD-11 warns that unscoped tokens can be replayed on other servers until expiration. Evidence: [NIP-42 Signed Event Verification][N42], [NIP-98 validation][N98], [BUD-11 source](library-evaluation.md#storage-relays-clients-and-signers). HTTP authorization is a separate replay surface from document processing.

## 8. Independent client interoperability

Transport interoperability means two clients can validate and decrypt the same wrap. Business interoperability additionally requires independently implemented document formats, manifests, receipts, version negotiation, limits, attachment byte encodings, duplicate rules, and failure semantics. NIP-17 kind 14 requires plain-text content; an application serialization could use UTF-8 textual content but ordinary chat clients will treat it as text, not an invoice workflow. Evidence: [NIP-17 Chat Message][N17]; this distinction is an **inference**.

A shared open application specification can provide business interoperability without a new event kind. NIP-78 explicitly discourages using its storage kinds as a generic interchange format between applications; use it, if at all, for encrypted personal settings/state after reviewing exposure and replaceability. NIP-89 advertises handlers for kinds; it does not establish encrypted payload capabilities or business conformance by itself. Evidence: [NIP-78 goal and event types][N78], [NIP-89][N89].

Library support tables and an existing DM client demonstrate ecosystem implementation, not two-client NBDP conformance. The next evidence needed is a common corpus consumed by two independent clients/libraries and relays with different policies. See [library evaluation](library-evaluation.md) and [open questions](open-questions.md).

## 9. Library support and maturity

Source inspection found implemented NIP-44/59 primitives in nostr-tools, Rust Nostr, and archived go-nostr; NDK documents higher-level NIP-17 inbox discovery and messaging. Amethyst declares the required private-message NIPs. These are practical starting points, with materially different validation boundaries, signer APIs and size support. None was demonstrated as an NBDP business-document implementation. Exact pins and per-file evidence are in [library-evaluation.md](library-evaluation.md).

NIP-44 references a December 2023 Cure53 audit at an immutable report commit. That supports the existence of an audit of that historical v2 design/implementations; it must not be generalized to all current SDKs, the later extended-length format, NIP-17 attachments, NBDP state machines, or deployed clients. Evidence: [NIP-44 Audit][N44] and [audit artifact, commit ce63c2eaf345e9f7f93b48f829e6bdeb7e7d7964](https://github.com/paulmillr/nip44/blob/ce63c2eaf345e9f7f93b48f829e6bdeb7e7d7964/audit-2023.12.pdf).

## 10. Additional NIPs and possible standardization gaps

| Discovered standard | Relevant evidence | Bounded use / gap |
| --- | --- | --- |
| [01][N01] | IDs, signatures, filters, categories, OK/EOSE/CLOSED | Foundation; relay acceptance is not a recipient receipt |
| [09][N09], [40][N40] | Deletion requests and expiration | Hygiene/retention hints; no guaranteed erasure or forward secrecy |
| [11][N11] | Information document and limitations | Discover practical caps; verify actual policy, no durable delivery promise |
| [07][N07], [49][N49], [55][N55] | Browser/Android signers and key-at-rest encryption | Key custody components, not key rotation or organizational authorization |
| [66][N66] | Relay monitoring/discovery events | Optional liveness hints, not trustworthy retention proof |
| [67][N67], [77][N77] | EOSE completeness hints and negentropy | Recovery/reconciliation assistance; deployment support must be checked |
| [70][N70] | Protected-event author AUTH requirement | Restricts compliant-relay republication; no confidentiality; outer one-time author complicates use with wraps |
| [78][N78] | App-specific storage, including normal kind 78 and addressable 30078 | Personal state only; explicitly unsuitable as a generic cross-app interchange shortcut |
| [89][N89] | Application handler recommendations | Optional discoverability; a new handler kind does not prove document compatibility |
| [92][N92], [94][N94] | Media/file metadata | Reuse field conventions privately; avoid public business indexes |
| [B7][NB7] | Blossom server lists and hash verification | Preferred current file-storage integration; assess pinned BUDs separately |
| [EE][NEE] | Unrecommended, superseded by Marmot | Investigate Marmot/MLS if forward secrecy or device/group membership becomes mandatory; do not adopt deprecated NIP-EE |

Potentially reusable gaps are encrypted capability negotiation, authenticated receipt semantics, key continuity/recovery, precise encrypted-file byte profiles, and retention/recovery expectations. A new NIP could document a profile without introducing any new kind. A new inner kind could eventually distinguish machine documents from chat, while retaining kind 1059 transport. A new public outer kind would reveal traffic classification and require relay/client support without automatically solving those gaps. These are **design conclusions** based on [NIP-17][N17], [NIP-59][N59], [NIP-44][N44], and [NIP-89][N89].

The official acceptance criteria ask for implementation in at least two clients and one relay when applicable, backward compatibility, optionality, and avoiding duplicate ways of doing the same thing. Establish a reusable gap and independent implementation evidence before requesting new kinds. Evidence: [README Criteria for acceptance][NREADME].

## Recommendation and unresolved risks

Proceed with option B: existing persistent NIP-17/44/59 transport and a publicly specified NBDP application envelope/receipt profile. Keep identity and discovery independent of any vendor, registry, government, or required DNS name. Use optional NIP-05, kind 10050 inbox routing, AUTH-aware relays, small encrypted manifests, and independently hosted encrypted blobs through Blossom. Establish conformance limits conservatively.

The unresolved blockers are the acceptable metadata/compromise threat model, encrypted-file byte interoperability and thumbnail nonce conflict, durable offline retention, receipt/deduplication semantics across devices, organizational key continuity, and a second independent implementation. If cryptographic forward secrecy is mandatory, this transport baseline is insufficient and a separate Marmot/MLS evaluation is required. The complete three-option [decision matrix](transport-comparison.md#decision-matrix) records why option B is favored and what would change that choice.

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
