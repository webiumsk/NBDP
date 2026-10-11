# E05 existing producer profile inspection

**Evidence type:** Static source inspection only, completed 2026-10-11. **Scope:** Canonical E05 preparation/producer comparison; Q08 and Q27 remain BLOCKER. No Amethyst build, device, file upload or decryption was executed. This report does not establish existing-client interoperability or approve an attachment wire profile.

## Revision and reproducibility

All Amethyst source links below pin **e6f464a1179def75274512b3c5bab921de3bf3d8**, the existing research control revision. Files were obtained from the public [Git tree](https://api.github.com/repos/vitorpamplona/amethyst/git/trees/e6f464a1179def75274512b3c5bab921de3bf3d8?recursive=1) and `raw.githubusercontent.com` at that revision. Public source reads used Python 3 `urllib.request`; retrieval exited 0. No runtime behavior is inferred from compilation. This environment's `java -version` exited 127 (`java: command not found`); installing or running Amethyst was outside this research subtask.

To reproduce the inspection, retrieve each exact pinned source URL in the references, inspect the stated line ranges, and compare the hashes below. Source was temporarily retained under `/tmp/nbdp-005-amethyst-source-full`, outside the committed fixtures. The report paraphrases evidence rather than committing upstream source.

| Retrieved source | SHA-256 of raw source bytes |
| --- | --- |
| Common `AESGCM.kt` [A] | `8e99bc0c82eb80cc37f72d9d1ef046165613c22d38582b9a313d16be846ecc69` |
| JVM/Android `AESGCM.jvmAndroid.kt` [B] | `6f7dafb5da64cc3e4dd2f9f96405fcf6928f3836dacc10c43f64c1767e2b8302` |
| Android `EncryptFiles.kt` [C] | `9c552c7eceaeb15bec9d8b1adbba918669ec95108a2dc19ea4251e387e1de3b3` |
| `EncryptionKey.kt` [D] | `dc28741c398eeac189411b2cc359d7e1162541b3c7cd927fdd1d30a32c2874ae` |
| `EncryptionNonce.kt` [E] | `7b08ec5788d7c6b78fc52ec96f362c0b4776f78b974d964473ab66b325a15fce` |
| `ChatFileUploader.kt` [H] | `5709df6cc6faaf6bb99f7928ea9a43b60ee5d4a5951ad8cc89feff92fbaae548` |
| `MultiOrchestrator.kt` [I] | `420d23b8cd3691ec11f57e4fec7dd03e00e1aedcfd4541498165e0b6f62e59d4` |

## Producer parameters and candidate comparison

The comparison concerns the Android/JVM producer path, with native observations bounded separately. The NBDP candidate is [revision 2](../shared/candidate-profile.md), an experiment contract, not a normative standard.

| Property | Pinned Amethyst evidence | Experimental NBDP candidate | Consequence |
| --- | --- | --- | --- |
| Primitive/name | Common constructor exposes AES-GCM; JVM uses AES/GCM/NoPadding [A, B] | AES-256-GCM; `aes-gcm` | Existing primitive, no custom algorithm |
| Key | Common default generates 32 bytes; stored constructor key feeds AES SecretKeySpec [A lines 28–33; B lines 30–38] | Exactly 32 bytes | Default key length agrees; this is source evidence |
| Nonce | Common default generates **16 bytes** [A lines 28–33] | Exactly **12 bytes** | Defaults disagree. Candidate rejects a default 16-byte producer nonce; do not advertise drop-in compatibility |
| Authentication tag | JVM GCMParameterSpec requests 128 bits [B line 38] | 16 bytes / 128 bits | Parameter agrees |
| Blob layout | JVM returns JCE `doFinal` bytes; Android writes that array directly [B lines 48–52; C lines 57–66]. JCE documents appended authentication tag [J] | Ciphertext followed by tag, no nonce prefix | Source/API-established layout agrees; actual Amethyst-produced bytes were not observed |
| AAD | Ordinary one-argument JVM encrypt has no updateAAD; the separate two-argument overload adds it [B lines 48–52, 68–75]. Android EncryptFiles calls the ordinary interface [C lines 57–61] | Empty AAD | Ordinary inspected path agrees. Do not infer every producer path uses empty AAD |
| Key/nonce tags | Kind 15 builder forwards keyBytes/nonce to encryptionKey/encryptionNonce; tag assemblers call toHexKey; hex helper specifies lowercase encoding [D, E, F, G] | Exact lowercase hex | Producer encoding agrees. Producer parser accepts hex through its helper and does not itself enforce this candidate's exact lengths |
| Original commitment | Android hashes the exact bytes read before encrypting [C lines 55–61] | SHA-256 exact original bytes, `ox` | Same hash interpretation; compression or sanitization before this point changes which original bytes are committed |
| Ciphertext commitment/size | Android hashes final encrypted array and reports its byte length [C lines 59–75]; kind 15 header accepts hash/size/originalHash parameters [G lines 104–135] | SHA-256 ciphertext+tag `x`; final blob size | Hash production is visible; header fields are caller-supplied/optional, so this inspection does not prove all producers always provide every required commitment |
| Mirrors | Android fallback uploads the already encrypted file [L lines 671–682] | Mirror stored ciphertext exactly | Same-byte retries avoid another encryption; this is distinct from encrypting a different file under the same pair |

A 16-byte GCM nonce is not, merely because of its length, proof of a cryptographic vulnerability. The candidate's 12-byte length follows the standard AEAD_AES_256_GCM profile in [RFC 5116 §5.2][R]. The important finding is a wire-profile disagreement. The JVM constructor can receive a caller-supplied nonce; that alone is not runtime proof that a selected existing client accepts the candidate's 12-byte file profile.

Native AESGCM delegates to `dev.whyoleg.cryptography` AES.GCM with explicit stored nonce [N lines 28–54]. This report did not pin/inspect that provider's implementation or execute its byte layout. JVM tag/layout conclusions must not be extended to all native platforms without separate evidence.

## Conditional source-level nonce-reuse concern

The selected code contains a complete path that warrants independent security investigation:

1. `ChatFileUploader.justUploadNIP17` constructs **one** AESGCM object before the upload batch, passes it into `uploadEncrypted`, and attaches that cipher to each successful result [H lines 55–76].
2. `MultiOrchestrator.uploadEncrypted` maps all selected items and passes the **same** cipher argument to each item's upload orchestrator [I lines 103–139].
3. The common single-file orchestrator forwards that unchanged argument to the media uploader [K lines 87–102].
4. The Android uploader passes it to EncryptFiles, which calls encrypt on each file's bytes [L lines 640–671; C lines 55–61].
5. JVM AESGCM starts a fresh JCE Cipher per call using the object's unchanged key and nonce [B lines 30–51]. Creating a new Cipher object does not create a new cryptographic nonce.

**Architectural inference:** If this branch is reached with multiple distinct files successfully encrypted under one batch cipher, the visible path reuses a key/nonce pair across distinct plaintexts. GCM nonce uniqueness is required by [J] and [RFC 5116 §5.1.1][R]. The source demonstrates a potentially unsafe construction; this task did not reproduce the multi-file UI path, establish all runtime preconditions, or demonstrate exploitation. Report it as a conditional source-level finding, not a confirmed runtime vulnerability or proof that all releases are affected.

NBDP must not copy this batch-cipher pattern. Every distinct encryption needs a fresh unique key/nonce pair; retries and mirrors should copy already stored ciphertext. Thumbnail encryption remains disabled. The current experimental nonce planner must reject distinct-plaintext pair reuse, with independent negative evidence. This report is not authorization to contact upstream maintainers.

## Disposition and remaining tests

- E05's existing-producer inspection establishes an explicit **alternative**, not consensus: Amethyst default 32/16/16 versus candidate 32/12/16 key/nonce/tag bytes, with compatible observed JVM layout and ordinary empty AAD.
- Keep the candidate unchanged during these experiments; reject unsupported 16-byte nonce metadata explicitly rather than silently reinterpret it or truncate it. Any future widening requires documented profile/version rules, vectors and security review.
- E05 runtime browser/OpenSSL results must be assessed separately. A successful comparison and crypto run can support the scoped candidate; it cannot prove Amethyst, native or kind 15 runtime compatibility.
- E06 must consume authenticated received key/nonce/commitment metadata, then verify blob commitments and authentication before any workflow effects. Matching file/envelope hashes alone does not authenticate downloaded plaintext.
- Q08 and Q27 remain blockers pending a reviewed normative profile and sufficient independent carrier/client evidence. Add an existing-producer runtime control in a later qualified environment, covering both nonce alternatives, tampered tags/commitments and unsupported-profile behavior.

## Pinned references

[A]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/commonMain/kotlin/com/vitorpamplona/quartz/utils/ciphers/AESGCM.kt#L28-L33
[B]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/jvmAndroid/kotlin/com/vitorpamplona/quartz/utils/ciphers/AESGCM.jvmAndroid.kt#L30-L85
[C]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/amethyst/src/main/java/com/vitorpamplona/amethyst/service/uploads/EncryptFiles.kt#L46-L76
[D]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/commonMain/kotlin/com/vitorpamplona/quartz/nip17Dm/files/tags/EncryptionKey.kt#L29-L44
[E]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/commonMain/kotlin/com/vitorpamplona/quartz/nip17Dm/files/tags/EncryptionNonce.kt#L29-L44
[F]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/commonMain/kotlin/com/vitorpamplona/quartz/nip01Core/core/HexKey.kt#L50-L61
[G]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/commonMain/kotlin/com/vitorpamplona/quartz/nip17Dm/files/ChatMessageEncryptedFileHeaderEvent.kt#L104-L135
[H]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/commonsUI/src/commonMain/kotlin/com/vitorpamplona/amethyst/commons/ui/screen/loggedIn/chats/privateDM/send/upload/ChatFileUploader.kt#L55-L76
[I]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/commons/src/commonMain/kotlin/com/vitorpamplona/amethyst/commons/service/uploads/MultiOrchestrator.kt#L103-L139
[J]: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/javax/crypto/Cipher.html
[K]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/commons/src/commonMain/kotlin/com/vitorpamplona/amethyst/commons/service/uploads/UploadOrchestrator.kt#L87-L102
[L]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/amethyst/src/main/java/com/vitorpamplona/amethyst/service/uploads/AndroidMediaUploader.kt#L640-L682
[N]: https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/nativeMain/kotlin/com/vitorpamplona/quartz/utils/ciphers/AESGCM.native.kt#L28-L54
[R]: https://www.rfc-editor.org/rfc/rfc5116.html
