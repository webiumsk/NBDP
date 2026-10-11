# Independent preliminary security review — NBDP-005

**Date:** 2026-10-11. **Reviewer:** independent security subagent, separate from harness author. **Scope:** experimental JavaScript/Rust transport, attachment and correlation adapters, E01–E06 tests, approved PO decisions and design-only parallel-device authority. This is a limited code/design review, **not a professional cryptographic audit or approval for production**. Findings describe the inspected revision before remediation; subsequent changes must retain their evidence and record retest results.

## Approval recommendation

Keep Option B conditionally approved for architecture direction only. No reviewed finding establishes a need for a new event kind. Do not approve exact wire bytes, SDK development or deployment. Keep Q01/Q08/Q13/Q15/Q27 BLOCKER. Distinguish passing executed checks from satisfying every mandatory criterion of the canonical experiment plan.

## Findings

### S01 — HIGH: independent validators disagree on document revision range

- **Evidence:** `shared/transport.mjs:44` requires a JavaScript safe positive integer for `document.revision`; `shared/rust/src/main.rs:56` originally accepted any positive `u64`.
- **Reproduced:** a valid authenticated envelope with revision `9007199254740992` was rejected as `schema` by JavaScript but accepted and dispatched by Rust. Both decrypted/authenticated correctly; this is an application-validation disagreement, not a cryptographic forgery.
- **Scenario / impact:** an authenticated sender supplies an out-of-range revision; implementations disagree on admissibility or precision, undermining version/correlation/idempotency semantics (Q04/Q07/Q09).
- **Remediation:** freeze one common numeric range in the experimental contract; enforce it independently. Preserve the original mismatch and include lower/upper/exceeding-bound and fractional/negative/type vectors in both validators.
- **Regression criterion:** identical reject/accept categories at those boundaries; old corpus PASS must not be presented as exhaustive validation agreement.

### S02 — HIGH evidence gap: E06 retrieval bypasses received key/nonce metadata

- **Evidence:** `e06-kind15/test.mjs:27` originally decrypted retrieved bytes with original `vector.key`/`vector.nonce`, independently of consumed kind 15 fields. `shared/correlation.mjs:10` and Rust `main.rs:139–140` checked key/nonce syntax only.
- **Reproduced:** syntactically valid all-zero key/nonce tags with matching document/file commitments produced `READY`, one synthetic operation, zero effects in both correlators. This is permissible only as a **correlation-ready** state, not as evidence of successful attachment decryption/integrity verification.
- **Scenario / impact:** sender-authenticated but wrong key/nonce metadata leaves an undecryptable file. A harness that uses original fixture secrets can still demonstrate successful retrieval, masking an interoperability failure (Q08/Q09/Q27).
- **Remediation:** derive retrieval URL, algorithm, key, nonce, lengths and commitments from the received validated wire plus its envelope. Add wrong-key/nonce/URL/commitment vectors; authenticate/decrypt and verify original bytes before an integrity-verified operation state. Keep zero business effects on failure.
- **Regression criterion:** both consumers recover with wire metadata in both directions; altered metadata fails before verified state. Orphan/correlation-ready states cannot become accounting import or business approval.

### S03 — MEDIUM: PASS scope must account for canonical unexecuted checks

- **Evidence:** original E01 `test.mjs:51` recorded a long-vector checksum without executing `encrypt_decrypt_long_msg`; direct message-key vectors were not exposed by Rust's public API. E02 `test.mjs:16` skipped ordinary-client rendering; canonical E02 includes an ordinary-chat control and exact client pin. E05 originally compared only newly written Web Crypto/OpenSSL candidates, although canonical E05 calls for existing producer layout comparison. E04 originally swept note sizes and tags without multifile-reference counts.
- **Impact:** executed-subset PASS can be misread as full canonical acceptance and can improperly satisfy dependent E06 gates. Source inspection/compilation is not runtime interoperability.
- **Remediation:** complete mandatory checks, or record them explicitly as unexecuted with full-experiment PARTIAL/NOT EXECUTED and honest dependency disposition. Optional ecosystem controls must be identified as such in the original plan; do not silently make required evidence optional. Indirect KAT coverage of private message-key internals may be explained separately.
- **Regression criterion:** machine/report status agrees with actual scope; all deviations and unexecuted controls listed; no dependent experiment presented as authorized by a falsely complete prerequisite.

### S04 — MEDIUM: commitment negatives were assertions about fixtures, not rejection tests

- **Evidence:** E05 `test.mjs:20` originally compared calculated hashes to fixture values and asserted they differ from all-zero values. It did not pass a wrong expected plaintext/ciphertext commitment through a consumer verifier and observe rejection. `test.mjs:21` checked a set of distinct fixture key/nonce pairs; it was not an implemented nonce-reuse rejection planner.
- **Impact:** byte equality and fixture uniqueness establish useful limited evidence, but do not prove that receiving workflows reject wrong commitments or sender planning rejects reuse (Q08/Q09).
- **Remediation:** add a bounded experimental consumer-verification boundary and supply wrong commitments; record sender/mirror/revision nonce decisions honestly. A separate planner is optional if no production-like planner claim is made; never perform a forbidden distinct-plaintext encryption to demonstrate rejection.
- **Regression criterion:** wrong supplied commitments prevent verified output, exact ciphertext mirrors remain identical, and changed originals select different key/nonce pairs without reusing them in encryption.

### S05 — LOW / boundary qualification: resource evidence is process-scoped

- **Evidence:** `shared/run.mjs:15` collects Node `process.resourceUsage()`/`memoryUsage()`; this excludes Rust/relay/browser peaks. Rust `main.rs:145` reads a complete newline before checking its 5 MB IPC cap. E04 `test.mjs:13` originally tested a size predicate on a local object rather than an actual HTTP metadata boundary.
- **Impact:** these observations do not establish a whole-client/relay memory ceiling or untrusted IPC/HTTP DoS resistance. The adapter is a local test process, not a production server.
- **Remediation:** narrow the report to measured processes/boundaries or separately measure children; label predicate-only and trusted-IPC tests. Keep production resource/security design open.
- **Regression criterion:** reported memory ceilings name the measured process; no unexecuted HTTP or public-network resilience claim.

## Reproduction evidence

Independent synthetic probe executed from `experiments/` with Node and `NBDP_RUST_BIN=/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust`; exit status **0**. It imported the two existing adapters, constructed/signed a valid document envelope with revision `2 ** 53`, and compared `validate()` against Rust `op: validate`. Result: JavaScript `{ok:false,error:"schema",decrypts:[1,1]}`; Rust `{ok:true,...dispatch:true}`. A second probe called each correlator with matching envelope/hash tags and syntactically valid but unverified all-zero file key/nonce: both returned `{state:"READY",operations:1,effects:0}`. No public relay, production key, real data or distinct-plaintext nonce reuse was used. These probes are additional evidence, not completion of E01–E06.

## Controls and architecture review

- Inspected transport validates outer ID/signature before outer decryption, seal kind/empty tags/signature before inner decryption, unsigned rumor ID/author/recipient, archive role and pinned sender. Freshly parsed objects avoid trusting nostr-tools verification cache after mutation. Positive helper decryption is correctly separated from full validation.
- AES candidate uses established implementations, AES-256-GCM, 12-byte nonce, 16-byte tag, ciphertext followed by tag and empty candidate AAD. OpenSSL plaintext is withheld until authentication succeeds (`attachment-crypto.mjs:12–13`). Browser Web Crypto is independent of Node's OpenSSL implementation. No thumbnail production was found. Fixture encryption uses distinct pairs; repeated cross-implementation known-answer encryption uses the same original, not distinct plaintexts.
- Fixture secrets are explicitly public/disposable: Nostr scalars 1/2/3 and committed AES keys. They are forbidden for real use. Random wrap keys are disposable. Runtime TLS keys remain outside committed fixtures. Tests target loopback relays/hosts; bootstrap downloads are separate. This is not proof of perfect host/network sandboxing.
- PO-001–PO-006 preserve approved boundaries, the five blockers and no production SDK/release approval. No new NIP/event kind or invented primitive was found. FS/PCS limitations and non-guaranteed delivery remain explicit.
- Parallel-device design correctly rejects mandatory single-writer fallback, distinguishes device/organization/transport identities, avoids treating NIP-26 as a complete authority system, and separates signed authority records from deferred portable document proof. Revocation under partitions, hidden conflicts, root compromise and non-idempotent disconnected effect sinks remain limits. Proposed deterministic set/causal merges require exact RFC grammar and E08/E09/E12/E13/E14 evidence; **Q15 is not resolved**.

## Specification evidence

Pinned NIPs revision `a79e21d90fce5465b50ef385dd368bba99ec4a0b` was independently opened during review: [NIP-17](https://raw.githubusercontent.com/nostr-protocol/nips/a79e21d90fce5465b50ef385dd368bba99ec4a0b/17.md), [NIP-59](https://raw.githubusercontent.com/nostr-protocol/nips/a79e21d90fce5465b50ef385dd368bba99ec4a0b/59.md), [NIP-44](https://raw.githubusercontent.com/nostr-protocol/nips/a79e21d90fce5465b50ef385dd368bba99ec4a0b/44.md). Relevant evidence: author equality and signed inbox publication policy; required-empty seals and unsigned rumors; existing AES-GCM file metadata without a fully fixed byte profile; static-key encryption limitations. The thumbnail wording must never justify distinct-plaintext key/nonce reuse.

**Required decision:** Product/security owners must approve exact identity/device authorization freshness and irreversible-effect policy separately from transport direction. Independent review of revisions and reruns is required before treating remediated findings as closed.

## Follow-up appendix — 2026-10-11

Original findings above remain historical evidence. This appendix independently reviews the remediation rather than replacing the observations.

### Retest scope and actual outcome

An additional disposable-key probe exercised **13 checks**, all passing: six revision cases (`1`, `9007199254740991`, `9007199254740992`, `-1`, `0`, `1.5`); positive original-byte recovery in both OpenSSL and browser consumers; both consumers rejecting wrong ciphertext hash, plaintext hash, plaintext length, key and nonce; and planner rejection of distinct-original pair reuse **before encryption**. No distinct plaintext was encrypted under a reused pair. The duplicate claim for identical original bytes was accepted, consistent with stored-ciphertext retry/mirroring.

The first probe attempt exited **1** because the default sandbox rejected the browser's `127.0.0.1` listener with `listen EPERM`. The same authorized synthetic loopback-only probe subsequently ran with sandbox escalation and exited **0**, taking **656.598101 ms**. Environment: Node **v22.18.0**, Node OpenSSL **3.0.16**, Chrome **151.0.7922.137**. No fixture, implementation or canonical result file was overwritten by this probe.

| Independently retested source | SHA-256 |
| --- | --- |
| `shared/transport.mjs` | `0c6f43c1f17b6b898b05cebb72f43dfacf19cfbb2203bbd2d4c7676abf39fb18` |
| `shared/rust/src/main.rs` | `95e05dde513e57d5e32830e8639632f34627bb34239c7e5916096fd3686edcba` |
| `shared/attachment-crypto.mjs` | `e52aaa588b4ff6315bbc7ebc08b2d8786965687e18c6c9f56a75d4b08cc05f16` |

Reproduction command with the same assertions and shortened diagnostic output, from `experiments/`:

```sh
NBDP_RUST_BIN=/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust node --input-type=module <<'JS'
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {secret,hex,getPublicKey,envelope,rumor,wrap,validate} from './shared/transport.mjs';
import {RustClient} from './shared/rust-client.mjs';
import {BrowserCrypto,consumeAttachment,NoncePlanner} from './shared/attachment-crypto.mjs';
const rust=new RustClient(),browser=new BrowserCrypto();
try {
 const a=secret(1),b=secret(2),A=getPublicKey(a),B=getPublicKey(b);
 for(const [revision,ok] of [[1,true],[Number.MAX_SAFE_INTEGER,true],[2**53,false],[-1,false],[0,false],[1.5,false]]){
  const e=envelope(A,B);e.document.revision=revision;
  const wire=JSON.stringify(wrap(rumor(e,A,B),a,B));
  const js=validate(wire,b),rs=await rust.call({op:'validate',wire,secret:hex(b)});
  assert.deepEqual(js,rs);assert.equal(js.ok,ok);
 }
 await browser.start();
 const v=JSON.parse(readFileSync('fixtures/generated/E05-aes-gcm-vectors.json'))[3];
 const input={key:v.key,nonce:v.nonce,blob:Buffer.from(v.blob_hex,'hex'),x:v.ciphertext_sha256,ox:v.plaintext_sha256,bytes:v.plaintext_bytes};
 assert.equal(consumeAttachment(input).toString('hex'),v.plaintext_hex);
 assert.equal(await browser.consume(input),v.plaintext_hex);
 for(const patch of [{x:'0'.repeat(64)},{ox:'0'.repeat(64)},{bytes:v.plaintext_bytes+1},{key:'ff'.repeat(32)},{nonce:'ff'.repeat(12)}]){
  assert.throws(()=>consumeAttachment({...input,...patch}));
  await assert.rejects(()=>browser.consume({...input,...patch}));
 }
 const planner=new NoncePlanner(),plain=Buffer.from(v.plaintext_hex,'hex');
 planner.claim(v.key,v.nonce,plain);planner.claim(v.key,v.nonce,plain);
 assert.throws(()=>planner.claim(v.key,v.nonce,Buffer.from('different synthetic original')));
 console.log('Independent follow-up: 13 checks PASS');
}finally{rust.close();await browser.close()}
JS
```

For another checkout use its built Rust adapter path. The executed shell command used this same heredoc invocation and assertions, additionally emitting per-case JSON, duration, environment and source hashes recorded above; those diagnostics do not change test assertions. This probe is a scoped regression control, **not E06 execution** or full architectural conformance.

### Finding dispositions

| Finding | Follow-up disposition |
| --- | --- |
| S01 | **Remediated and independently retested for the reported range bug.** Both validators now accept the common positive safe-integer range and reject the reproduced `2 ** 53` case. E01 also adds strict integer-token/file-schema controls and expanded regression coverage; this is not proof every malformed input is covered. |
| S02 | **Source repair observed; full runtime closure pending.** E06 now obtains key/nonce/hash/size/URL from validated received kind 15, with wrong-key/nonce negative controls. E06 remains unexecuted because its prerequisite E02 is PARTIAL. Consumers independently rejected wrong crypto inputs in this follow-up; relay-carried kind 15 end-to-end evidence is still absent. `READY` remains correlation-ready, with zero business effects, not verified delivery. |
| S03 | **Status discipline improved.** E02 treats unavailable ordinary-client rendering as mandatory unexecuted evidence and reports PARTIAL; dependent E04/E06 are gated. E01 now executes retained long-vector agreement and documents legacy Go/private internal API limitations. E05 includes explicit pinned existing-producer source comparison, not a fabricated ecosystem runtime result. Review final reports against the same distinctions. |
| S04 | **Remediated and independently retested for wrong-commitment rejection and planner behavior.** Both actual consumers reject supplied wrong commitments/size; nonce planner rejects different original bytes before encryption. The planner is ephemeral experimental state, not crash-safe/global production nonce management. |
| S05 | **Residual boundary qualification retained.** Test-process IPC and process-specific measurements do not establish public-network DoS safety or whole-stack resource ceilings. E04 remains gated; no runtime closure is asserted. |

### S06 — HIGH conditional source-level concern: existing producer batch cipher reuse

The [producer profile comparison](producer-profile-evidence.md) was independently checked against locally retained upstream source pinned at **e6f464a1179def75274512b3c5bab921de3bf3d8**. The path is visible: [ChatFileUploader lines 55–76](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/commonsUI/src/commonMain/kotlin/com/vitorpamplona/amethyst/commons/ui/screen/loggedIn/chats/privateDM/send/upload/ChatFileUploader.kt#L55-L76) creates one cipher for the batch; [MultiOrchestrator lines 103–139](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/commons/src/commonMain/kotlin/com/vitorpamplona/amethyst/commons/service/uploads/MultiOrchestrator.kt#L103-L139) passes it to each item; [UploadOrchestrator lines 87–102](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/commons/src/commonMain/kotlin/com/vitorpamplona/amethyst/commons/service/uploads/UploadOrchestrator.kt#L87-L102) and [AndroidMediaUploader lines 640–671](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/amethyst/src/main/java/com/vitorpamplona/amethyst/service/uploads/AndroidMediaUploader.kt#L640-L671) forward it; [EncryptFiles lines 55–61](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/amethyst/src/main/java/com/vitorpamplona/amethyst/service/uploads/EncryptFiles.kt#L55-L61) invokes encryption; [JVM AESGCM lines 30–51](https://github.com/vitorpamplona/amethyst/blob/e6f464a1179def75274512b3c5bab921de3bf3d8/quartz/src/jvmAndroid/kotlin/com/vitorpamplona/quartz/utils/ciphers/AESGCM.jvmAndroid.kt#L30-L51) initializes encryption with unchanged object key/nonce.

**Scenario / impact:** if the inspected branch processes distinct originals in one encrypted batch, the visible construction reuses GCM key/nonce across those originals, compromising AEAD confidentiality/authenticity assumptions. The full UI/runtime branch was **not executed**; this is a conditional source-level finding at the exact pin, not a confirmed exploited vulnerability or statement about all releases. No unsafe reuse experiment or upstream communication was performed.

**Required remediation for NBDP:** never copy the batch-cipher construction; keep fresh per-distinct-encryption pairs and copy stored ciphertext for retries/mirrors. Require per-file/revision planner tests and later existing-producer runtime controls. Producer compatibility must not override GCM uniqueness.

Separately, the upstream default **16-byte nonce** and NBDP experimental **12-byte nonce** disagree. Sixteen bytes alone does not prove insecurity; this is an explicit profile/interoperability difference. The NBDP candidate must reject unsupported lengths without truncation or silent reinterpretation, pending Q08/Q27 normative decisions.

### Follow-up recommendation

The reported validator and consumer regression repairs support continuing **limited research and RFC candidate drafting**. Source comparisons and the scoped independent crypto probe do not establish kind 15 ecosystem compatibility. Maintain conditional architecture direction and all five blockers; no SDK, release, production use, new kind/NIP or single-writer downgrade is approved. Later concurrency/authority tests and Product Owner freshness/effect decisions remain necessary.
