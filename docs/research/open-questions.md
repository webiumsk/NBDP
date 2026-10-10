# Open questions and decision gates

Research date: **2026-10-11**. NIP revision: **`a79e21d90fce5465b50ef385dd368bba99ec4a0b`**. All linked NIPs pin that snapshot. These questions are an unresolved research backlog, not a request to approve implementation. No protocol design is treated as adopted.

Recommended working direction is option B, contingent on the security and interoperability gates below. A new NIP is optional, and a new event kind is not currently a prerequisite. See [the complete decision matrix](transport-comparison.md#decision-matrix), [landscape evidence](nostr-landscape.md), and [implementation pins](library-evaluation.md).

## Priority definitions

- **P0:** settle before publishing a credible initial interoperable profile.
- **P1:** settle before claiming operational reliability or broader client compatibility.
- **P2:** investigate when the requirement appears in independent implementations.

“Owner” identifies a work area, not a mandatory organization or protocol authority. Evidence can be produced by any independent participant.

## P0: privacy, identity and authentication

| ID / work area | Open question | Current evidence and risk | Candidate direction / evidence needed |
| --- | --- | --- | --- |
| Q01 / threat model | Is reduced public sender metadata sufficient, or are cryptographic forward secrecy, post-compromise recovery and recipient anonymity mandatory? | NIP-44 explicitly lacks forward secrecy and post-compromise security; the outer p-tag exposes the recipient. [NIP-44 Limitations][N44], [NIP-59 structure][N59] | Publish a precise attacker model covering relays, file hosts, network observers, compromised clients/signers and recipients. If forward secrecy is mandatory, stop treating the simple NIP-44 profile as sufficient and evaluate Marmot/MLS separately |
| Q02 / identity | What proves a key is the intended counterparty and authorized business endpoint? | NIP-01 proves signature validity; NIP-05 identifies aliases and requires retaining public-key references. Neither proves an employee's document authority. [NIP-01][N01], [NIP-05 notes][N05] | Raw keys and out-of-band confirmation must work. Define contact trust and optional organization attestations privately, without mandatory DNS, government identity or vendor enrollment |
| Q03 / discovery | How is an inbox list found and refreshed without a mandatory indexer? | Kind 10050 is the normative NIP-17 inbox; absence means do not send. General relay lists and NIP-05 hints require bootstrap discovery. [NIP-17 Publishing][N17], [NIP-65 Discoverability][N65], [NIP-05][N05] | Define configurable bootstrap/contact hints, signed cached lists, expiry/staleness and explicit “inbox unavailable/not ready.” Demonstrate exchange with product-owned services absent |
| Q04 / authentication | Which validation rules are required independently of SDK helper behavior? | Outer signature verification precedes decryption; seal and rumor authors must match. Helpers differ, and rumor IDs may be unverified by convenience paths. [NIP-44 Decryption][N44], [NIP-17 Encrypting][N17], [source findings](library-evaluation.md#security-sensitive-source-findings) | Write a full validation order and negative corpus: ID/signature, expected kinds, empty seal tags, unsigned rumor, computed rumor hash, author, recipients, size/schema/version, trust policy. Require identical accept/reject results in two implementations |
| Q05 / document proof | Are recipient-authenticated messages enough, or must documents/receipts be independently verifiable after export? | A rumor has no signature; seals authenticate encrypted content to recipients and retain a degree of deniability. [NIP-59 Overview][N59] | Select an explicit unsigned-transport baseline and optional signed-object profile. If signed objects are needed, define exact signed bytes, domain separation, recipient/context and canonicalization; document the deniability tradeoff |

An untrusted signer or file host is not resolved by a new event-kind number. A profile should define both whom an endpoint trusts and what a signature/receipt actually attests. This is a design conclusion from the identity and encryption scopes above.

## P0: envelope, attachments and receipt semantics

| ID / work area | Open question | Current evidence and risk | Candidate direction / evidence needed |
| --- | --- | --- | --- |
| Q06 / carrier | Should B's first envelope use text-serialized kind 14, kind 15 metadata/manifest relationships, or eventually a dedicated inner rumor kind? | Kind 14 requires plain text and has chat semantics; kind 15 is an encrypted-file message. Generic gift wraps permit other rumor kinds. [NIP-17 Message Rumor Definitions][N17], [NIP-59][N59] | Start by specifying/test-reading a text envelope and private file manifest; assess ordinary-client rendering, unknown fields and receipt parsing. A demonstrated semantic mismatch may justify C2, not necessarily a new outer kind |
| Q07 / versioning | What are the protocol/schema versions, byte limits, mandatory extensions and downgrade behavior? | NIP-17 has no business schema negotiation; NIP-44 version 2 now includes extended lengths not supported by every legacy implementation. [NIP-17][N17], [NIP-44][N44], [library comparison](library-evaluation.md#nip-44-size-compatibility) | Define exact UTF-8 serialization rules, preserved document bytes, canonical signing/hashing rules, extension bounds, unsupported-version errors and private capability exchange. Reject silent plaintext/NIP-04 downgrade |
| Q08 / file cryptography | What AES-GCM key size, nonce/tag length, encoding and binary layout must independent clients implement? | Kind 15 names aes-gcm and key/nonce fields but does not fully fix every byte detail. The thumbnail text specifies the same key and nonce. [NIP-17 File Message][N17] | Obtain cross-implementation file vectors and clarify upstream profile details. Initially omit thumbnails. Never encrypt distinct plaintexts under the same GCM key/nonce; evidence: [RFC 5116, January 2008, §§2.1/5.1.1](https://www.rfc-editor.org/rfc/rfc5116.html#section-5.1.1) |
| Q09 / file commitments | Which hashes bind ciphertext, original bytes, ordering and document revisions? | Kind 15 x is encrypted bytes and ox original bytes; NIP-94 ox refers to pre-transformation originals. Public hashes can disclose/link content. [NIP-17 File Message][N17], [NIP-94][N94] | Define exact commitment domains and manifest relationships; keep plaintext hashes, names, MIME and business identifiers inside encryption. Verify ciphertext hash before decryption and plaintext commitment afterward |
| Q10 / size and abuse | What small envelope and blob limits are genuinely interoperable? | Format limit (~4 GB) differs from runtime/library/relay budgets; nested encryption increases size; relay limits distinguish bytes/characters. [NIP-44 Implementation considerations][N44], [NIP-11][N11] | Measure complete EVENT frames across two libraries, non-ASCII text, tag limits and large/malformed inputs. Treat the proposed 16 KiB full-frame budget as a test target only; set separate manifest/file/decryption-memory limits |
| Q11 / receipts | What do received, validated, accepted and rejected mean; who can issue them; are receipts mandatory? | Relay OK is acceptance by a relay, not the business recipient; NIP-17 has no business receipt state machine. [NIP-01][N01], [NIP-17][N17] | Correlate each receipt to authenticated endpoints, stable message ID, exact document commitment and state. State whether missing attachments permit “received,” define retryable/permanent rejection, and distinguish processing acknowledgment from business approval |
| Q12 / replay and duplicates | What remains stable across retries, and how long are replay records retained? | Wraps are independently encrypted and have distinct outer IDs; signatures and random nonces do not prevent replay of valid events. [NIP-59][N59], [NIP-01 event IDs][N01] | Scope logical IDs by sender/recipient/context, retain durable deduplication, reject same-ID/different-hash conflicts, and define freshness/deadlines without excluding legitimate offline documents. Demonstrate restart, lost-receipt and restored-backup behavior |

A conformance corpus should preserve original document bytes; two visually identical XML/JSON/PDF documents may have different byte hashes. The profile must distinguish byte preservation from any format-specific semantic canonicalization. This is a design requirement inferred from exact-byte [NIP-01 event hashing][N01] and [NIP-17 attachment hashes][N17], not a claim that one universal business canonicalization exists.

## P1: offline operation, multi-device state and rotation

| ID / work area | Open question | Current evidence and risk | Candidate direction / evidence needed |
| --- | --- | --- | --- |
| Q13 / durable delivery | What offline horizon and minimum relay/blob retention are needed, and how is availability demonstrated? | 1059 is persistent-intended, but relays may not store gift wraps; blob hosts have independent policy. [NIP-59 Other Considerations][N59], [BUD-01 Sunset / retrieval](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/01.md) | Choose a stated offline horizon and retention margin, use independent advertised relays/hosts, retain local outbox/archives, and test eviction/restart/unavailable-host cases. Do not treat a signed list or OK as a storage promise |
| Q14 / history recovery | How do clients reconcile backdated wraps, silent result caps, time ties and newly discovered relays? | Up to two-day backdating; EOSE alone does not prove all history; NIP-67 adds optional finish/more/auth hints. [NIP-17 Encrypting][N17], [NIP-67][N67], [NIP-77][N77] | Specify overlapping recovery windows, ID tracking, complete historical catch-up for a new relay and pagination tie handling. Test with/without hints and negentropy, including authenticated queries and relay-set changes |
| Q15 / multi-device receipts | Can several devices process the same document or emit contradictory business receipts? | Per-identity history is recoverable where retained; the transport has no device processing lock or shared business state. [NIP-17][N17], [NIP-46][N46] | Define authorized processing authority, conflict resolution and monotonic receipt transitions. Demonstrate two devices, crash after business effect but before receipt, and old-device reconnect |
| Q16 / signer trust | Which NIP-46/07/55 permissions and availability assumptions are acceptable? | Remote signers perform plaintext encryption/decryption RPCs and control user keys; client/signer/user keys differ. [NIP-46][N46], [NIP-07][N07], [NIP-55][N55] | Test private-key-free clients, offline signer failure, narrow permissions, consent/revocation, returned-event/request equality, signer-relay switching and no implicit NIP-04 use. Allow local/user-controlled signers |
| Q17 / key continuity | How are routine rotation, compromise recovery, old inboxes and archival decryption handled? | NIP-05 says aliases must not silently replace pinned keys; NIP-46 relay switching is not identity rotation. [NIP-05][N05], [NIP-46][N46] | Specify old/new endorsements where available, key epoch/effective time, rollback/conflict handling, recipient acceptance and old-key decryption retention. Separate ordinary rotation from recovery where the old key cannot be trusted |
| Q18 / AUTH and anti-spam | What privacy is lost when senders authenticate to recipient relays, and what policy is interoperable? | Random wrapper keys defeat reputation-based filtering; NIP-59 recommends user AUTH for spam mitigation. [NIP-59 Spam Protection][N59], [NIP-42][N42] | Document relay knowledge of authenticated publisher and recipient filters; test auth-required/restricted/rate-limited flows and bounded retries. Do not advertise public sender unlinkability against the receiving relay if AUTH reveals it |

“Received” should describe a durable protocol outcome rather than a transient UI view. A shared account key on several devices does not define who is authorized to make the business decision. A remote signer lowers key exposure on clients but does not remove the need to trust signer operations. These conclusions follow from [NIP-46's operation scope][N46] and [NIP-17 recovery model][N17].

## P1: blob-host and HTTP authorization conformance

The preferred file-storage integration is current [NIP-B7][NB7], with Blossom revision **`b5bd2801d1763aa635fc8fea7a76597e0eb18990`** pinned independently of NIPs. Open decisions are:

- **Q19 / host interchange:** Are ordinary opaque encrypted uploads, mirror fallback, hash verification, CORS, redirects, download authorization and expiry discoverable enough for independent clients? Evidence: [BUD-01](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/01.md), [BUD-02](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/02.md), [BUD-03](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/03.md), [BUD-04](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/04.md), [BUD-06](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/06.md). Demonstrate receipt behavior when only some blobs are available and replicas have different retention policies.
- **Q20 / token replay:** Are server/action/hash scoping, expiry and sensitive-action one-use policies sufficient? NIP-98 uses kind 27235 and request URL/method/time, with optional body binding; Blossom uses kind 24242 and BUD-11 scopes, including a warning about cross-server replay of unscoped tokens. Evidence: [NIP-98][N98], [BUD-11](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/11.md). Define server-specific tokens by default, verify request commitments, and distinguish idempotent retries from destructive management authorization.
- **Q21 / host metadata:** Can a host learn the business sender, recipient, MIME type or content from authentication, extensions and download timing? Encryption protects bytes but not access patterns. Evidence: [NIP-17 private file fields][N17], [BUD-01](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/01.md), [BUD-11](https://github.com/hzrd149/blossom/blob/b5bd2801d1763aa635fc8fea7a76597e0eb18990/buds/11.md). Decide whether opaque content types, separate upload principals, proxying or additional network privacy are optional profile features; quantify their operational cost before making claims.
- **Q22 / legacy interoperability:** Is NIP-96 required as an optional adapter for existing clients? It is unrecommended and points to NIP-B7. Its Auth section describes an optional payload hash differently from NIP-98's request-body rule. Evidence: [NIP-96 Auth/deprecation][N96], [NIP-98 payload tag][N98]. If retained, fix/test exact endpoint expectations rather than assuming interchangeable authorization.

The inspected blob-server README and current BUD texts are not perfectly aligned in management labels and auth encoding language; runtime conformance remains unverified. See [library findings](library-evaluation.md#storage-relays-clients-and-signers).

## P2: what could justify a NIP or new kind?

| ID | Proposed gap | Evidence threshold for reconsidering B alone | What would not justify allocation |
| --- | --- | --- | --- |
| Q23 | Reusable business delivery/receipt profile | Two independent applications implement the same envelope/receipt rules and identify value in a formal NIP without wire changes | A name, product identity, or marketing preference |
| Q24 | Dedicated inner machine-document kind | Independent implementations show kind 14/15 semantics are ambiguous or cause incompatible dispatch, and a private inner kind resolves this cleanly | Expecting a new inner kind to improve relay durability or traffic anonymity |
| Q25 | Relay-level offline/recovery capability | A precisely stated behavior cannot be provided inside encryption; implementations demonstrate backward-compatible relay behavior and a meaningful benefit | Treating OK as a recipient receipt or merely wanting “reliable” written in a NIP |
| Q26 | Key continuity / encrypted capability negotiation | Multiple independent use cases need the same safe rules; account-key recovery and metadata implications are explicit | Requiring a centralized business directory or government root to participate |
| Q27 | Encrypted file profile clarification | Cross-client vectors expose precise byte/nonce issues in existing kind 15; resolve by an existing-NIP clarification first where possible | Creating a parallel attachment kind to avoid clarifying existing fields |

NIP-78 explicitly says its kinds are not for generic interchange across applications, so it is not a shortcut around this decision. NIP-89 handler announcements do not standardize encrypted capability discovery. Evidence: [NIP-78][N78], [NIP-89][N89].

The official NIP acceptance criteria require two clients and one relay when applicable, optionality/backward compatibility and avoiding duplicate ways of doing the same thing. A profile NIP may use existing kinds. Evidence: [official criteria][NREADME]. A decentralized protocol can publish its open application specification before any central index accepts it; the same README explicitly discusses standards emerging outside that repository.

## Exit criteria for the next research stage

A next stage can claim a specified initial profile only when:

1. Its threat model precisely states content protection, exposed recipient/network metadata and lack or presence of cryptographic forward secrecy.
2. Two independent implementations parse the same documents/manifests, enforce the same authentication/size rules and agree on negative cases.
3. The attachment crypto layout is exact, has shared test vectors and excludes distinct-plaintext key/nonce reuse.
4. Receipt, duplicate/replay and cross-device state semantics are defined and failure-tested; lost acknowledgment remains an explicit unknown outcome.
5. Offline delivery is demonstrated against independent relay/file-host failures within a stated horizon; retention is an operational assumption with evidence.
6. Public-key discovery, signer choice and key continuity work without any mandatory product, government, DNS domain, relay indexer or central operator.

These are proposed research gates, not tests completed in this task.

## Recommendation, unresolved risks and decision matrix

Recommend **B**, with a public application profile inside existing encrypted transport and no kind allocation now. Resolve Q01–Q12 before claiming initial interoperability, then establish Q13–Q22 reliability evidence. Pursue Q23–Q27 only when independent implementations establish a reusable gap.

Unresolved risks remain key-compromise history exposure, recipient and traffic metadata, file nonce/encoding ambiguity, relay/blob eviction, incomplete recovery, receipt loss/conflict, restored-backup replay and organizational key continuity. If Q01 requires cryptographic forward secrecy, the simple NIP-44 baseline must be reconsidered.

| Choice | Present judgment | Condition that changes the decision |
| --- | --- | --- |
| A: existing conventions only | Useful manual baseline; insufficient machine business semantics | Full requirement becomes human-mediated file exchange |
| B: existing transport + open encrypted application protocol | Recommended research direction | Independent evidence shows carrier semantics or cryptographic requirements cannot be met |
| C: profile NIP and/or new kinds | Defer allocation; profile-only standardization remains possible | A reusable gap and independent conformance evidence justify a profile NIP or private inner kind; new outer kinds need a separate relay/privacy case |

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
