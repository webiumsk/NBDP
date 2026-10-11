# Independent QA review — NBDP-005

**Reviewer:** Independent QA subagent, separate from experimental implementation. **Date:** 2026-10-11. **Review type:** Canonical acceptance-criteria comparison, source inspection and additional isolated runtime probes. This is not security approval or independent ecosystem certification.

The [canonical experiment plan](../../docs/research/required-experiments.md) defines E01 as NIP-44/full validation and E02 as application-envelope exchange. The reversed directory titles and NBDP-005 requested subsection titles do not replace those IDs. The [candidate profile](../shared/candidate-profile.md) is experimental. Q01/Q08/Q13/Q15/Q27 remain BLOCKER regardless of passing lab subchecks.

## Initial review evidence and limitations

At initial inspection, the recorded [E01 evidence](E01.json) contained 124 passing checks and a PASS status; [E05 evidence](E05.json) contained 20 passing checks and a PASS status. E02/E03/E04/E06 had not yet produced machine results. Their harnesses were reviewed but not executed by this reviewer. Source hashes below identify the code probed; later implementation fixes and reruns must not erase this historical finding.

| File | SHA-256 at initial review |
| --- | --- |
| `shared/transport.mjs` | `83e9c4288a6a277223334fbf67c0be241cdb6e5ae01b87dc989b7fafe2873457` |
| `shared/rust/src/main.rs` | `6517a822e96d25ad5ed08f44071b5fc3e72837441fee97f977f06dbc3a648703` |
| `shared/evidence.mjs` | `82750f33ddb00a246188705f5b16267eead2d08c4eb8b0ae7e3d7bf8416d6328` |
| `shared/run.mjs` | `cde9e80b0de1130e3bc6dfbc64028a4c17bddc190e5b9056ecd65f29f6b9db49` |

Environment: Node v22.18.0, Linux x64, executable `/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust`; runtime source/binary identity guard passed before probes. All identities were documented public disposable scalars 1 and 2. No network endpoints, production data, credentials, Satflux files or production services were used. Reviewed sources and package locks provide provenance; successful compilation is not counted as interoperability evidence.

## Runtime finding QA-001 — schema disagreement

**Severity:** Blocks the initial E01 all-outcomes agreement claim and dependent execution until repaired and rerun.

A correctly signed/wrapped document envelope with revision `9007199254740992` was rejected by JavaScript with `schema` and accepted by Rust with `dispatch: true`. JavaScript uses safe-integer checks; Rust initially accepted any positive u64 revision. The cryptographic chain was valid in both cases. This is an experimental validation disagreement, not a failure of NIP-44 or evidence requiring a new kind.

Both adapters also accepted `files: [null]` and `files: ["bogus"]` as dispatchable document envelopes. The correlators assume a structured first file entry. This is missing application schema validation and an unsafe handoff to downstream parsing. `files: []` was accepted; its meaning requires a declared no-file operation policy rather than an implicit first-entry assumption.

The exact additional probe command executed from `experiments/` was:

```sh
NBDP_RUST_BIN=/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust node --input-type=module <<'JS'
import {RustClient} from './shared/rust-client.mjs';
import {secret,hex,getPublicKey,envelope,rumor,wrap,validate,strictJSON} from './shared/transport.mjs';
const rust=new RustClient();await rust.ready;
const a=secret(1),b=secret(2),A=getPublicKey(a),B=getPublicKey(b);
const tests=[
 ['revision-unsafe-integer',{document:{...envelope(A,B).document,revision:9007199254740992}}],
 ['null-file-entry',{files:[null]}],
 ['file-string-entry',{files:['bogus']}],
 ['empty-file-array',{files:[]}]
];
for(const [name,patch] of tests){
 const e={...envelope(A,B),...patch},r=rumor(e,A,B),wire=JSON.stringify(wrap(r,a,B));
 const js=validate(wire,b,{expectedSender:A});
 const rs=await rust.call({op:'validate',wire,secret:hex(b),expectedSender:A});
 console.log(JSON.stringify({name,js,rs}));
}
try{strictJSON('{"x":1,"\\u0078":2}');console.log('duplicate escaped key accepted')}
catch(e){console.log('duplicate escaped key: '+e.message)}
rust.close();
JS
```

**Actual process exit:** 0. **Observed wall time:** approximately 0.50 seconds. This diagnostic command prints outcomes; its exit 0 means execution completed, not that conformance passed. Both adapters rejected the escaped duplicate-key probe with `json`.

| Probe | JavaScript initial outcome | Rust initial outcome |
| --- | --- | --- |
| Revision above safe integer range | Reject `schema` | Accept, dispatch |
| Null file entry | Accept, dispatch | Accept, dispatch |
| String file entry | Accept, dispatch | Accept, dispatch |
| Empty file array | Accept, dispatch | Accept, dispatch |
| Escaped duplicate JSON key | Reject `json` | Not exercised in this additional command |

Required action: freeze numeric and file-entry constraints explicitly, add independent positive/negative boundary fixtures, repair both validators as necessary, rebuild Rust and rerun E01. Preserve earlier result artifacts as history. This reviewer has not modified implementation code.

## Source-inspection findings

### QA-002 — incomplete official vector execution

The initial E01 harness executes conversation-key, known-answer encrypt/decrypt, invalid key/payload and padding cases plus additional size boundaries. It only records the long-vector checksum as an observation and does not execute the long-vector corpus. Message-key internals are private in Rust and indirectly tested by exact ciphertext KATs, which is an explicitly justified limitation. The planned legacy Go boundary control is absent and is not recorded as skipped. Original corpus invalid length labels are correctly identified as superseded for extended-length NIP-44, but that does not justify omitting all remaining applicable negative length cases.

Required action: execute applicable public long vectors where present; identify empty/unusable source-vector entries explicitly; document unavailable legacy controls as a deviation. Do not claim the entire official corpus passed when only selected groups were executed.

### QA-003 — stale prerequisite evidence can unlock dependent experiments

The initial runner checks stored result status only. It does not compare prerequisite source hashes to current validators, profile, package lock or Cargo lock. A previous PASS can therefore authorize E02/E04/E06 after relevant code changes without rerunning prerequisites. The Rust source/binary guard is helpful but checks `main.rs` only, not the executable's dependency provenance.

Required action: verify prerequisite result hashes before dependent execution or invalidate stale result artifacts. Record executable SHA-256 and build/toolchain/lock provenance. Confirm a deliberately stale PASS refuses E06 before any relay/file activity.

### QA-004 — commitment and nonce-planner negative tests are too weak

The initial E05 `commitment-order-and-mirroring` check verifies known hashes and inequality with zero hashes. It does not pass wrong commitments into a rejecting verified-download function. `nonce-planner-rejects-distinct-plaintext-reuse` checks differing digests and uniqueness of selected fixture pairs, without exercising a planner that rejects an attempted reuse. Actual AES-GCM tamper/key/nonce/AAD/tag/truncation negative tests are useful and execute both engines. This finding concerns policy validation, not a claim of observed nonce reuse.

Required action: add real rejection paths for wrong plaintext/ciphertext commitments and attempted reuse planning without performing the unsafe second encryption. Test retry/revision/mirror policy with saved ciphertext identity. Retain the initial evidence and distinguish passed crypto subchecks from missing mandatory scope.

### QA-005 — E04 resource and multi-file coverage

Initial E04 code measures actual nested rumor/seal/wrap/EVENT bytes, Unicode and extended-length boundaries, tag bounds and a predecode oversized input. It does not sweep attachment-reference arrays as required by the canonical environment/steps. Process-wide Node resource counters do not establish per-operation or Rust/browser/relay ceilings. The large-HTTP-metadata check is a constructed JSON length predicate rather than an HTTP ingestion path. This must be described as a partial scope, unless extended before final execution.

Required action: add reference-count/array fixtures, declare bounded resource ceilings and measurement scope, and record missing HTTP path testing as a deviation rather than claiming it was exercised.

### QA-006 — E06 retrieval is insufficiently connected to received fields

Initial E06 uses committed E05 vector metadata directly when decrypting downloaded blobs. It proves recovery of those bytes, but does not prove that the receiving pipeline fetches, decodes and verifies according to the independently received kind 15 fields. Correlation checks the shape of a key/nonce, not whether those received values decrypt the committed bytes. A valid-length wrong key/nonce can therefore produce a synthetic READY marker before download verification. READY must not be described as document integrity verified.

Required action: drive retrieval/verification from validated received metadata; add wrong-but-well-formed key/nonce, byte length and hash negatives. Preserve file-only no-effect behavior. Exact ciphertext mirrors here are two same-code HTTP instances, correctly distinguished from independent Blossom conformance reserved for E07.

An additional isolated runtime probe replaced only the kind 15 `decryption-key` with 64 zero hex characters, recomputed the unsigned rumor ID, and called both correlators on the envelope/file pair. Both returned `READY`, `operations: 1`, `effects: 0` (diagnostic exit 0, approximately 0.67 seconds). This is compatible with READY meaning metadata readiness only; it must not be relabeled as successful decrypt/integrity verification. The original-vector retrieval test does not exercise this bad received key.

The Rust mismatch guard was also independently exercised from `/tmp/nbdp-005-qa-mismatch` with an intentionally different `shared/rust/src/main.rs`. It rejected before any experiment call with `Rust source/binary mismatch; rebuild before testing` (exit 0 for the diagnostic that expected rejection). Only disposable `/tmp` fixture files were created; no implementation files were edited.

## Coverage and status discipline

| Canonical ID | Initial useful evidence / reviewed scope | Mandatory gap or follow-up |
| --- | --- | --- |
| E01 | 124 recorded passing checks, independent transport crypto/validators and negative chain cases | QA-001 disagreement; QA-002 corpus/control scope; rerun after fixes |
| E02 | Bidirectional peer/archive code through independent relays; unknown features/chat non-dispatch | Await actual relay execution; correlated-stub reordering and ordinary-client observation must be reported accurately |
| E03 | Signed discovery negatives and explicit no-fallback policy; local HTTPS alias test | Await runtime results; generated outbox is a policy demonstration, not crash-durable outbox proof; global freshness remains unproven |
| E04 | Full byte-accounting and cross-library limit code | Await runtime; QA-005; distinguish relay normalized event caps from EVENT frame caps |
| E05 | 20 recorded passing checks, real browser Web Crypto versus Node OpenSSL EVP, exact vectors and tamper rejection | QA-004; producer byte-layout comparison must distinguish new experimental producers from existing ecosystem implementations |
| E06 | Independent tag construction/correlation code and exact mirror bytes | Must wait for valid E01/E02/E05 evidence; QA-006; ordinary ecosystem producer control unavailable |

Browser Chromium/BoringSSL and Node OpenSSL EVP are independent implementations for AES-GCM. JavaScript and Rust separately written parsers/validators provide independent application outcomes, although the candidate schema and fixtures are common. Two blob servers sharing code do not prove independent storage implementations. No Amethyst runtime or UI interoperability was demonstrated in the reviewed evidence.

**Initial approval recommendation:** Request corrections and fresh evidence before assigning full canonical PASS or unlocking dependent experiments. PARTIAL is appropriate for unexecuted mandatory scope; FAIL is appropriate for demonstrated disagreements. No claim of production readiness, portable signatures, forward secrecy, guaranteed retention, decentralized multi-device authority or legal delivery follows from these tests. Complete threat-model/security approval remains independent of this QA review.

## Review completion gate

The initial findings above were sent immediately to the coordinating agent. A final follow-up review must identify corrected hashes, rerun outcomes, remaining skipped mandatory scope and whether E06 prerequisites genuinely passed. Until that follow-up is recorded, this file documents initial findings and does not approve the final experiment reports.

## Remediation follow-up — 2026-10-11

This section supersedes the initial implementation findings **only within the retested candidate**; the initial evidence above remains historical. It does not close Q01/Q08/Q13/Q15/Q27. Candidate revision 2 documents safe-integer bounds, integer JSON token spelling, typed file entries and the empty-file-array meaning. The change repairs experimental parser/schema assumptions rather than changing Nostr cryptography or assigning kinds.

| Retested component | SHA-256 |
| --- | --- |
| `shared/transport.mjs` | `0c6f43c1f17b6b898b05cebb72f43dfacf19cfbb2203bbd2d4c7676abf39fb18` |
| `shared/rust/src/main.rs` | `95e05dde513e57d5e32830e8639632f34627bb34239c7e5916096fd3686edcba` |
| `e01-envelope/test.mjs` | `c3e54fbc27bba439f7d957e446307fc16490848f71a4fc09a99123991a10d53b` |
| `e05-attachment-crypto/test.mjs` | `e5b0e7f728c2a775497f33ab97eb686ffaabc3c54877baec877acf1281536254` |
| Rust executable | `ecd1c1ab446782e263ae9e606117486b25d79b16732de5c4fac97e78b31699d9` |

### Independently executed regression and harness checks

Nine additional assertions compared both validators: unsafe revision, safe maximum revision, null file, string file, empty files, and numeric tokens `1.0`, `1e0`, `-0`, `1.5`. All nine passed (exit 0, approximately 0.34 seconds). Unsafe revision/null/string entries now reject `schema`; safe maximum and empty files accept; the four disallowed numeric spellings reject `json`. The source/binary guard passed. The command used the same imports and transport setup as QA-001, added `node:assert/strict` equality and expected-outcome assertions, and constructed numeric-token content by replacing the raw version token before wrapping it.

The repaired complete E01 and E05 harnesses were then independently executed without overwriting official evidence or fixtures. Exact reproduction commands from `experiments/`:

```sh
NBDP_RUST_BIN=/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust node --input-type=module <<'JS'
import {Evidence} from './shared/evidence.mjs';
import {execute} from './e01-envelope/test.mjs';
const ev=new Evidence('E01-independent-QA-rerun');ev.save=()=>{};
await execute(ev);const r=ev.finish();
console.log(JSON.stringify({status:r.status,tests:r.tests.length,failed:r.tests.filter(x=>!x.ok),skipped:r.skipped}));
process.exitCode=r.status==='PASS'?0:1;
JS

node --input-type=module <<'JS'
import {Evidence} from './shared/evidence.mjs';
import {execute} from './e05-attachment-crypto/test.mjs';
const ev=new Evidence('E05-independent-QA-rerun');ev.save=()=>{};
await execute(ev);const r=ev.finish();
console.log(JSON.stringify({status:r.status,tests:r.tests.length,failed:r.tests.filter(x=>!x.ok),browser:r.observations.find(x=>x.browser_version)?.browser_version,requests:r.observations.find(x=>x.requests)?.requests}));
process.exitCode=r.status==='PASS'?0:1;
JS
```

| Independent check | Actual outcome | Process exit | Observed wall time |
| --- | --- | --- | --- |
| Complete repaired E01 | PASS, 140 checks, zero failed/skipped | 0 | 2.66 seconds |
| Complete repaired E05 | PASS, 25 checks, zero failed | 0 | 1.35 seconds |

The first E05 diagnostic in the default filesystem/network sandbox failed before tests with `listen EPERM` for `127.0.0.1` (exit 1). The same explicitly authorized command then ran with the loopback-server sandbox restriction lifted and succeeded. Chrome version was `151.0.7922.137`; the browser request log contained only its local test page, `http://127.0.0.1:42221/`. The failed environment attempt is preserved here and is not a cryptographic failure or an automatic-approval rejection.

A separate `/tmp/nbdp-005-qa-prerequisite` fixture copied current source/result records, changed only E02 to a synthetic PASS with a wrong recorded transport hash, and executed `node shared/run.mjs E06`. The child returned **exit 2**, `NOT EXECUTED`, zero tests, with reason `Prerequisite E02 missing, not PASS, or source hashes stale` (approximately 0.06-second recorded runner duration). No dependent file/relay tests ran. The outer Python diagnostic exited 0 because it asserted that rejection was required. No workspace source or official result records were modified.

### Disposition of initial findings

| Finding | Follow-up disposition |
| --- | --- |
| QA-001 schema disagreement | Repaired and independently retested; common positive/negative outcomes for the stated regressions |
| QA-002 vector execution | Long-message corpus now cross-executed; its empty published checksum is explicitly qualified; three pinned extended-boundary checksum KATs now pass. Legacy Go remains NOT EXECUTED and source-only, outside the two primary implementation claim |
| QA-003 stale prerequisites | Repaired; shared-source/fixture/lock hashes checked, executable hash recorded; deliberately stale result blocks E06 in independent runtime test |
| QA-004 weak policy assertions | Repaired; actual native/browser consumers reject wrong ciphertext/plaintext commitments and lengths, and a planner rejects distinct-plaintext reuse without performing unsafe encryption. Independent complete E05 rerun passes |
| QA-005 E04 coverage | **NOT EXECUTED** due E02 prerequisite; no byte-budget/resource/relay-limit result approved. Retain coverage requirements for later execution |
| QA-006 received file metadata | Source now uses received authenticated key/nonce/hash/size fields and includes wrong-key/nonce rejection checks. **E06 remains NOT EXECUTED**; source inspection is not runtime proof |

The [producer inspection](producer-profile-evidence.md) explicitly finds an existing Amethyst 16-byte default nonce versus candidate 12-byte nonce. This is a profile disagreement requiring resolution, not proof of unsafe 16-byte GCM nonces. Its potential multi-file pair-reuse path is an explicitly conditional source-level finding; no runtime vulnerability or exploitation is claimed. E05 establishes the independently executed candidate cryptography, not existing-client kind 15 interoperability.

### Final status discipline at follow-up

| Experiment | Machine status reviewed | Checks | Review conclusion |
| --- | --- | --- | --- |
| E01 | PASS | 140 | Independent repaired harness rerun agrees; claim limited to frozen profile and declared vector/control scope |
| E02 | PARTIAL | 22 passing | Canonical ordinary-client rendering control unavailable and recorded mandatory; adapter/relay exchanges do not prove that control |
| E03 | PASS | 19 | Machine results/source inspected; this reviewer did not separately rerun relay/HTTPS tests; no retention or global freshness guarantee |
| E04 | NOT EXECUTED | 0 | Correctly blocked by E02; no complete-frame budget conclusion |
| E05 | PASS | 25 | Independent repaired browser/OpenSSL rerun agrees; Q08/Q27 remain unresolved |
| E06 | NOT EXECUTED | 0 | Correctly blocked by E02; no kind 15 runtime interoperability claim |

The dependency graph was preserved; missing ordinary-client control was not silently waived. E02's process exit 0 is consistent with the runner's documented PARTIAL convention and must never be summarized as full PASS. E04/E06 exit 2 is a deliberate dependency refusal. Further experimental execution requires satisfying E02's control or an explicit reviewed change to the canonical experiment plan, not manually setting PASS.

**Follow-up recommendation:** The repaired executed candidate evidence is suitable for review and provisional RFC drafting within its demonstrated scope. Do not authorize attachment wire-format finalization, frame-budget approval, independent-client ecosystem claims, SDK development or production use. E04/E06 remain unexecuted; the five canonical blockers remain open. Final Markdown reports/link checks were not yet available when this follow-up was written.

**Residual harness limitation identified:** At this inspection, the runner unconditionally reads the Rust binary to hash it even after an unavailable-environment result. If that file is absent, the runner can terminate without writing the intended NOT EXECUTED record. This does not invalidate the successful recorded executable's results, but environment-failure reporting should guard the missing-file case. The coordinator was notified.

## Final prose, provenance and link review — 2026-10-11

Final [E01](E01.md), [E02](E02.md), [E03](E03.md), [E04](E04.md), [E05](E05.md), [E06](E06.md) and [summary](../../docs/research/experimental-validation-summary.md) are now present. Independently compared all six Markdown statuses, assertion counts, duration and process-exit fields with machine records. All agree with the reviewed status table above. All recorded source/configuration/fixture/lock hashes match current files; the final runner hash is `71f749240adb43b2dc92863f19a60d101a09365b0ca7976c1d55b238dc13e107`.

The initial final-report draft contained incorrect Q mappings for E03/E04 and omitted Q24 for E06. These documentation findings were reported to the coordinator and corrected. A follow-up automated comparison of each report's canonical question set against the authoritative plan now passes for all E01–E06. Canonical experiment meanings and the five blockers are retained.

Independent Markdown check of the six reports, QA report, summary, [project state](../../docs/PROJECT_STATE.md) and [roadmap](../../docs/ROADMAP.md), including this appendix, found **zero missing local paths or heading anchors across 112 local links**, with balanced fenced-code blocks in all ten files. No external-link availability or upstream runtime certification is implied by local-link checks.

The missing-binary hash guard is now repaired. Reviewed [coordinator diagnostic](runner-missing-binary.json) and independently recreated the blocking-path probe in `/tmp/nbdp-005-qa-missing-binary`: copied final `shared/run.mjs` and `shared/evidence.mjs`, then invoked E06 with `NBDP_RUST_BIN=/tmp/nbdp-005-qa-deliberately-absent` and no prerequisite artifacts. The child wrote a result with `NOT EXECUTED`, zero tests, **exit 2**, and binary SHA `unavailable` (recorded runner duration 28 ms). The outer diagnostic exited 0 after asserting those outcomes. This confirms the repaired reporting guard when execution is dependency-blocked; it does not assert that every possible child-process/environment failure path has been tested.

The final prose accurately distinguishes executed candidate evidence, source-only producer comparisons, unexecuted ordinary-client rendering, blocked E04/E06 modules, scoped Node resource counters and remaining architecture approvals. No seven-day availability, frame-limit recommendation, kind 15 runtime interoperability, multi-device resolution, portable signature, forward secrecy or production readiness is inferred. Initial failures and review findings remain preserved as historical evidence.

**Final QA recommendation:** Ready to submit the research PR for review with the recorded PARTIAL/NOT EXECUTED limitations. Preserve the conditional architecture direction and five blockers. The next evidence milestone remains completing E02's ordinary-client control, followed by E04/E06 under unchanged prerequisite gates. No merge, normative wire finalization, SDK or deployment approval is given by this review.
