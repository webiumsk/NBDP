# Attachment profile decision brief

Prepared 2026-10-23 from independent security research and current provenance checks. This recommends experimental work; it does not adopt a normative profile or close Q08/Q27.

| Question | Experimental candidate | Pinned Amethyst |
| --- | --- | --- |
| Key / nonce / tag | 32 / 12 / 16 bytes | Default32 / 16 / 16 bytes |
| AAD / blob | Empty / ciphertext followed by tag | Inspected JVM path has no AAD update; JCE output is written directly |
| Evidence type | Historical E05 PASS25, browser Web Crypto and OpenSSL EVP | Source inspection at `e6f464a1179def75274512b3c5bab921de3bf3d8`; no actual client-produced file bytes tested |
| Current check | All20 recorded E05 source/config/lock pins match | Five cached producer source files match the recorded hashes |
| Compatibility conclusion | Candidate bytes tested within declared scope | Default producer interoperability remains unproven |

See [canonical producer evidence](../../experiments/results/producer-profile-evidence.md), [E05](../../experiments/results/E05.md) and [current audit](transport-gate-readiness-2026-10-23.md). Provenance checks are not new crypto executions or present-toolchain qualification.

General GCM permits IV lengths beyond96bits, while RFC5116's named AES-GCM AEAD fixes12octets. The IV uniqueness requirement is separate. **A16-byte nonce alone is not evidence of a cryptographic vulnerability.** Sources: [RFC5116 §§5.1–5.2](https://www.rfc-editor.org/rfc/rfc5116.html), [SP800-38D §§5.2.1,8](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf), [JCE Cipher](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/javax/crypto/Cipher.html).

## Options and recommendation

1. **Retain12-byte candidate for existing isolated experiments.** Reject unsupported16-byte metadata explicitly. This is the minimum path; it makes no claim of default Amethyst file compatibility.
2. **Test an explicit16-byte alternative separately.** Freeze key/nonce/tag/AAD/layout/encoding and authenticated metadata, execute independent crypto vectors and actual pinned-client producer→consumer and consumer←producer exchanges, including valid-length wrong parameters, hash/size/profile negatives. Never widen the old candidate silently.
3. **Consider explicit multiple profiles only after evidence.** Authenticated version/profile selection and downgrade negatives need review. Length guessing, trial decryption and unauthenticated hints cannot choose the profile.

Recommendation: option1 for current tests, option2 as a separately reviewed comparison before eventual profile selection. Confidence is high in the inspected mismatch and scoped historical crypto evidence, low in ecosystem interoperability. Eventual normative adoption remains a separate G1/product/security decision.

No nonce truncation/padding, UTF-8/hex reinterpretation, AAD fallback or key/nonce reuse for different plaintexts is permitted. Retries/mirrors reuse immutable ciphertext, not a second encryption. Two local servers using identical code demonstrate mirroring only, not independent storage interoperability.

## Separate batch-reuse finding

The prior HIGH finding is a **conditional source path**, not a reproduced runtime vulnerability: one AESGCM object can be forwarded across multiple upload items, with unchanged key/nonce at encryption. The UI/runtime preconditions and actual distinct-plaintext reuse were not demonstrated. Preserve that distinction and the original finding.

Next safe test: instrument the pinned disposable client's encryption entry, record pair identity and synthetic plaintext commitments, and veto a second same-pair/different-plaintext call **before encryption executes**. Report attempted entry separately from completed encryption or exploitation. No upstream disclosure/message is authorized by this task.

The experimental `NoncePlanner` is also an in-memory claim checker, not durable reservation. Restart/restore/concurrent-device and crash-after-encryption tests require a reviewed custody contract that recovers exact stored ciphertext or fails closed before an uncertain new encryption. E05 planning checks do not establish this property.
