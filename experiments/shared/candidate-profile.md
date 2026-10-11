# Frozen experimental candidate — NBDP-005, revision 2

This is a test contract, not an approved wire specification. It covers Q04/Q06/Q07/Q08/Q09/Q10/Q27. Kinds and cryptography retain existing NIP meanings. Canonical specifications pin NIPs [a79e21d90fce5465b50ef385dd368bba99ec4a0b](https://github.com/nostr-protocol/nips/tree/a79e21d90fce5465b50ef385dd368bba99ec4a0b).

## Transport/validation

Persistent kind 1059, one exact `p` routing tag, NIP-44 v2, signed kind 13 with empty tags, unsigned kind 14 or 15 rumor with recomputed NIP-01 ID. Verify IDs/signatures before corresponding decryption. Kind 14 rumor has one peer `p` tag. Peer and sender receive separate wraps of the **same** rumor. Sender archive must authenticate local rumor author and preserve remote recipient; it never dispatches incoming effects.

Default candidate complete EVENT frame cap: 16,384 UTF-8 bytes; testing can separately sweep beyond it with a declared lab cap. JSON nesting <=32, inner tags <=64, string-only tag cells, integer timestamps/kinds, exact known event fields, no duplicate object keys. Check these before using parsed fields. Envelope is UTF-8 JSON text; no JSON canonicalization of original document bytes. Separate ordinary chat from recognized `protocol: "NBDP/experiment"`, `version: 1`, `type: "document"` envelopes. Unsupported discriminators do not dispatch; unsupported mandatory versions/features fail explicitly. No NIP-04/plaintext fallback.

Envelope fields: `protocol`, `version`, `type`, 64-lowercase-hex random/test `id`, `from`, `to`, `context: "synthetic"`, `required: []`, `document: {id, revision, sha256, bytes, media}`, optional `files: []` and bounded `note`. Sender/from and recipient/to bind to authenticated rumor/seal and inner tags. Document ID/revision/hash/length are required; revisions and counts are nonnegative safe integers (revision >=1), numeric JSON tokens use integer spelling, no exponent/fraction/negative-zero syntax; optional files has <=16 entries of exact {x, ox, size}, 64-lowercase-hex hashes and canonical decimal blob size 16..1048592; an empty files array signifies no attached blob in this experiment; hash covers exact original bytes, not an invoice's semantic interpretation. A hash is not a signature or company authority.

## Attachment candidate

AES-256-GCM: 32-byte key, 12-byte nonce, 16-byte tag, **empty AAD**, blob = ciphertext || tag; nonce remains private metadata. Key and nonce use exact lowercase hex; hash commitments are lowercase SHA-256 over final ciphertext+tag (`x`) and exact original bytes (`ox`). No compression/normalization. Size refers to final encrypted blob. Suite tag `encryption-algorithm` value `aes-gcm`, `decryption-key`, `decryption-nonce`, `file-type`, `x`, `ox`, and `size` follow [NIP-17](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/17.md); URL is kind 15 content. Correlation uses existing `e` reply reference to the envelope rumor ID plus private manifest file hashes/revision. No additional event kind or thumbnail encryption.

A fresh key/nonce pair for each distinct encryption; retries/mirrors reuse stored ciphertext, not a fresh encryption under reused nonce. Public standard vectors are disposable known-answer tests, never reusable secrets. Modified AAD must fail; empty AAD is a candidate compatibility choice, not a universal NIP mandate. RFC 5116 §5.2 and the 2017 Web Crypto AES-GCM construction supply standard cryptographic parameters; NIP-17 does not fix all byte encodings.

## Discovery and dispatch

Pinned raw keys; signed kind 10050 lists required before release. NIP-65/05 provide discovery hints only. Missing/empty/invalid/known rollback/tied contradictory/stale beyond 10-day **test** age yields explicit local unavailable/conflict and no publication to substitute relays. Only ws://127.0.0.1 or ws://localhost explicit lab endpoints are allowed in experiments. Sender archive readiness/failure is separate from peer publication. Global latestness is never proven by a cache.

Orphan kind 15 is pending; only a validated envelope authorizes a logical operation. Binding includes authenticated endpoint pair, envelope logical ID, document ID/revision, original/ciphertext hashes, byte lengths and canonical envelope rumor ID. Duplicate file or fresh wraps do not create a new effect. Mismatches quarantine. Test effect counters are synthetic markers, not accounting operations or approval. Real receipts, replay persistence, offline retention and parallel-device business authority require E08/E09/E11/E12 and reviewed RFCs.
