# Parallel multi-device authority — design analysis

**Status:** Design-only candidate, NBDP-005, 2026-10-11. [PO-004](../decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md#po-004) requires parallel authorized-device business decisions. Q15 remains **BLOCKER**. No delegation, authorization log, decision merge or accounting implementation is supplied here. E01–E06 do not resolve Q15.

The earlier single-active-authority recommendation is **superseded**, preserved at [NBDP-004](https://github.com/webiumsk/NBDP/blob/00a5bfbb5656f2a82c0fb9a746c5137c9ea7f3ce/docs/research/transport-boundaries.md#delivery-state-receipts-and-business-authority). It is not a fallback required end-state or a permission to downgrade PO-004.

## Evidence and constraints

The following specification facts use NIPs revision **a79e21d90fce5465b50ef385dd368bba99ec4a0b**:

- [NIP-01](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/01.md) authenticates a public key and exact event; it provides no legal organization or device role.
- [NIP-17](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/17.md) specifies per-recipient/sender wraps and room participants, not company-authority synchronization or global effect locking.
- [NIP-59](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/59.md) requires seal/rumor author consistency and unsigned rumors. A delegated device must authenticate as its actual key; an organization claim cannot replace the seal author.
- [NIP-26](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/26.md), re-read for this analysis, is **unrecommended**. Its delegation token conditions cover kind and timestamp. It does not establish document/action scopes, partition-safe revocation or a business decision log. Its relay query/deletion rules cannot be assumed deployed. Inserting its delegation tag into a required-empty kind 13 seal would conflict with the selected profile. Do not adopt it as a mandatory authority mechanism.
- [NIP-46](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/46.md) separates signer/user/client keys and supports sessions. A signer can enforce local permissions, but possession of the same user secret remains one indistinguishable identity. Requiring an always-online bunker would violate offline/operator independence.
- [NIP-09](https://github.com/nostr-protocol/nips/blob/a79e21d90fce5465b50ef385dd368bba99ec4a0b/09.md) deletion is not guaranteed erasure. Removing delivery destinations does not revoke previously decrypted data.
- [RFC 9420, July 2023](https://www.rfc-editor.org/rfc/rfc9420.html) provides MLS membership/epochs and cryptographic FS/PCS with state conditions, not company authorization or accounting idempotency. The [Marmot research pin](https://github.com/marmot-protocol/marmot/blob/7fabb81b3ed6e2fffeb1b267a0d2ae92b0ab2c89/README.md) is a future profile context, not proven NBDP concurrency.

Everything below is explicitly **architectural reasoning/proposed contract**, not a claim these NIPs already standardize it. No government identifier, DNS ownership, registry, central coordinator, Satflux or Evolu is required. Keys and organizations remain separately enrolled concepts.

## Alternative matrix

| Criterion | A Shared organization key | B Per-device keys + delegated grants | C Organization identity + signed append-only logs | D Existing mechanisms / replicated sets |
| --- | --- | --- | --- | --- |
| Identity/authorization | One account principal; no cryptographic device attribution | Actual device issuer, explicit role/scope/expiry grant | B plus retained grant/revocation/decision provenance and forks | NIP-26 too coarse/unrecommended; signer sessions identify clients only to signer |
| Concurrent decisions | Both devices can sign, source indistinguishable | Both authorized devices can decide | Concurrent decisions retained with causal heads | Set/CRDT convergence possible for accepted records; authorization remains separate |
| Conflict detection | Cannot reliably attribute malicious device; still detect contradictory assertions | Detect distinct operation/decision IDs and incompatible actions | Explicit concurrent heads, authorization forks and resolutions | NIP-17 room membership supplies no decision merge |
| Eventual consistency | Needs durable shared records beyond transport | Needs exchange of grants/decisions | Immutable replicated sets converge given same valid inputs and policy | Relay reconciliation aids retained-data recovery only |
| Offline operation | Decryption easy if account key available | Signed grants and contact/device delivery descriptors cached | Log frontier/freshness tracked; stale authority explicit | Remote signer outage blocks operations; MLS retains separate epoch state |
| Compromise | All account traffic/authority compromised | Device compromise bounded by grant scope/time; root compromise remains severe | Auditable conflicts/recovery, no cryptographic truth of malicious assertions | FS profile may reduce history exposure, not authorize decisions |
| Device revocation | Cannot revoke one copy of shared secret | Revoke grant/device for informed clients; partition delay remains | Signed revocation plus frontier, expiry and quarantine on discovery | Deletion/expiration do not revoke signatures or learned plaintext |
| Partition recovery | Ambiguous author/action conflicts | Exchange missing authority/decision records | Validate causal closure; expose missing parents/forks and recompute state | No relay supplies authenticated global completeness |
| Cross-device idempotency | No global once-only effect across disconnected sinks | Stable operation key; sink-local durability still needed | Decision convergence does not undo executed external effects | CRDTs cannot make an uncoordinated non-idempotent payment/import exactly once |
| Independent complexity | Simple crypto, difficult unsafe authority | Moderate grammar/policy plus signed objects | Moderate/high if deliberately limited; avoid a global total-order consensus service | NIP-26 ecosystem burden; MLS higher state/recovery complexity |
| Recommendation | Compatibility/privacy tradeoff only; fails selective revocation requirement | Required identity basis | Simplest credible complete candidate: B plus bounded immutable logs | Reuse primitives and retained-set reconciliation selectively, not as authority substitutes |

Recommend **B + a minimal C**: organization trust anchor, independently keyed devices, bounded signed grants/revocations, and append-only replicated authorization/decision records with causal references. “Append-only” describes locally retained validated records, not immutable guaranteed relay storage or a blockchain. No mandatory total-order service or operator. The trust anchor may be one organization-admin key initially; it is a trust role, not a continuously online decision coordinator. Multi-admin policy/forks/recovery must be reviewed before claims about stronger governance.

## Principal and transport model

1. **Organization principal O:** locally enrolled public-key trust anchor, with optional independent representative evidence. O proves only key control; a counterparty decides whether it represents the intended business. Raw O works without a directory.
2. **Device principal D:** independent key pair with a grant referencing O, grant ID, exact device key, allowed actions/document contexts, validity window and authority epoch. Sharing O's private key is not equivalent to D and supplies no distinct-device revocation.
3. **Transport issuer:** actual seal/rumor author, normally D for device actions. Envelope binds that author plus claimed O and grant context; validators independently verify authority rather than treating `from=O` as a signature substitution. This changes application envelope candidates only after RFC review, not NIP-17/59 authorship rules.
4. **Delivery identity:** must remain explicit. Per-device encryption destinations can be privately advertised through organization-authorized descriptors; each D uses its own signed kind 10050 inbox. Organization-addressed legacy/shared encryption and independently keyed device fanout are different profiles. No experiment here proves safe device-directory distribution, sender archives or first-contact fanout. Loss/withholding of a descriptor must queue explicitly.
5. **Signature format:** future R07 must select precise standard signing bytes and verification/domain separation. Existing NIP-01/BIP-340 signatures are a candidate primitive; this document creates no new algorithm, event kind or finalized token grammar. Signed authority records authenticate grants and decisions, not portable document bytes. PO-005's document-proof deferral remains intact.

Device access to documents and device business-decision authority are separate. A device may still decrypt retained ciphertext or forward plaintext after removal. Revocation can reject future recognized actions and omit future recipient copies; it cannot revoke knowledge or provide baseline FS/PCS.

## Minimum authorization record set

Provisional records must be transported privately over existing encrypted kinds, with an unambiguous versioned discriminator. Do not publish a public organizational participant registry as a shortcut.

| Record | Minimum bindings | Verification / reason |
| --- | --- | --- |
| Organization enrollment | O and locally accepted authority evidence | Out-of-band verification/explicit TOFU; no alias auto-substitution |
| Grant | O, D, grant ID, action/document scope, epoch, expiry, authorization predecessors | Standard signature by accepted authority; reject scope expansion, cycles, unknown mandatory fields and unsupported versions |
| Revocation | O, D/grant ID, epoch, targeted grants, causal parents, revocation scope | Issuer must already have administrative authority; old message or grant possession cannot issue grants |
| Authorization checkpoint | Accepted epoch/frontier, known grant/revocation set commitments, bounded freshness | A signed checkpoint proves an issuer assertion, not global absence of undisclosed revocations; fork/rollback visible |
| Technical assertion | D/O/grant context, message ID, exact digest/revision, processing action, assertion ID | Full transport and action authorization; assertion honesty is not proven |
| Business decision | D/O/grant, operation key, action/value, decision ID, exact document/version, causal predecessor decision IDs | Distinct compatible/concurrent/superseding actions; unsigned timestamps cannot supply global order |
| Conflict resolution | Conflict set/heads, explicit selected outcome or compensating workflow, authorized resolver scope | Requires referencing all known conflicting heads; a new unseen conflicting head reopens conflict |

No normative encoding is selected. G1 must fix signed-byte domain, bounded parent counts, maximum chain length, cycle detection, expiry-clock rules, admin grant delegation depth (prefer zero initially), fork handling, stable IDs and exact hash commitments. A root key signing a dishonest checkpoint remains an adversary, not a proof of complete history.

## Authorization freshness and revocation under partitions

Consider D1 and D2 offline with a valid cached grant. Another participant revokes D2 while D2 cannot receive that record. D2 and a similarly partitioned counterparty cannot distinguish that world from one in which no revocation occurred. Immediate universally effective revocation plus unrestricted offline acceptance therefore cannot both be guaranteed without additional trusted freshness/coordination. This is an indistinguishable-schedule architectural argument, not an empirical result or a claim that CRDTs repair it.

Proposed conservative policy:

- Locally known revocations/epochs always prevent granting fresh action authority from older cached documents or stale grants. Never permit timestamps claimed by D to bypass a known revocation.
- Cached grants have bounded expiry and require a named accepted checkpoint/frontier. A device can record a **provisional** offline decision while freshness is uncertain. Expired or unverifiable grants allow storage/read-only review, not newly authorized effects.
- Concurrent decisions from authorized devices are legitimate records. A later discovered revocation may make provisional records inadmissible or disputed; preserve evidence and explicitly recompute authorization status. Do not silently erase history or treat it as confirmed at creation time.
- Irreversible effects need an application risk/freshness policy or an idempotent shared effect endpoint. When required certainty is unavailable, keep the decision provisional and expose an unresolved effect. This does not prohibit parallel decisions or require a mandatory central coordinator.
- Claim only tested bounded-staleness assumptions. Ten-day transport retention and seven-day offline objectives do not imply seven-day delegation validity or safe offline effect authority.

Product/security review must choose the permitted stale-authority window, actions eligible for provisional offline decisions, checkpoint trust and root-compromise recovery. If Product requires immediate revocation and irreversible offline effects with no coordination, **Q15 cannot close under those constraints**. Alternatives are accepting bounded revocation delay for selected reversible actions, deferring irreversible effects until freshness/reconciliation, or choosing optional business-domain coordination/idempotent sinks. These alternatives preserve multiple concurrent decision writers.

## Deterministic decision merge

`action` denotes a shared review scope; accept and reject are alternative **outcomes of the same document-review action**, never distinct action keys. Otherwise two contradictory decisions could incorrectly appear compatible. Separate genuinely independent actions must be explicitly profiled.

Each device retains immutable records with unique operation/decision IDs and exact subject commitments. Given identical complete valid records and policy, both implementations should compute the same result:

1. Verify transport and signed authority objects; require causal parents or label pending dependencies. Quarantine unknown issuers, stale/expired/forked authority and same-ID/different-bytes records.
2. Merge compatible **technical assertions** by keyed set union with issuer/action/document provenance. `received`, `integrity-verified` and named format validation are assertions, not business acceptance or legal delivery.
3. Group **business decisions** by operation key: organization/peer context, stable logical operation ID, exact document ID/revision/hash and action. Different revisions/actions are separate scopes with explicit relationships, not implicit overwrites.
4. Deduplicate identical decision IDs. Compatible concurrent outcomes retain every author, but derive one agreed semantic outcome for that action. They do not authorize duplicate effects.
5. Identify maximal causal decision heads. Opposing accepted/rejected heads yield **CONFLICT**, preserving heads/provenance and suspending automatic irreversible effects. No last-write-wins, clock or lexical-hash winner.
6. An authorized resolution explicitly references the known conflict heads and its effect/compensation policy. Concurrent resolutions or newly learned contradictory heads keep/reopen conflict. A missing head remains pending, not globally complete.
7. Later revocation/fork evidence recomputes authority and can produce **AUTHORITY_DISPUTED**; root recovery requires independently reenrolled trust. No old-key signature alone proves recovery after root compromise.

Example: D1 accepts and D2 rejects revision 3 while partitioned. Both decisions survive merge; state is CONFLICT. A resolver R, permitted by a reviewed grant, references both and chooses a correction/revision or explicit agreed outcome. If D3 subsequently supplies a conflicting unreferenced authorized decision, the conflict reopens. Two identical accepts converge semantically but retain distinct authors and decision IDs.

Eventual convergence requires eventually exchanging the same relevant retained records and applying the same policy. Relay acceptance, EOSE and a checkpoint cannot prove a malicious participant/relay supplied the complete set. Operation histories may remain incomplete when copies disappear. No total order or global exactly-once network delivery is promised.

## Effect and crash boundaries

Decision convergence and accounting effects are separate state machines. Use one stable business operation key at each effect sink; maintain durable effect intent/outcome and a receipt outbox. Crash after effect before ACK must reconcile by that same key. Two disconnected non-idempotent sinks can both import/post/pay before learning each other's decision: eventual set merge cannot undo that physical action.

No mandatory global coordinator is proposed. Implementations must declare effect domains and support idempotent/recoverable sinks or hold irreversible effects when authority/result is uncertain. Two independent client databases are not automatically a shared idempotency domain. A replicated intent record alone is not an atomic commit with an external payment/accounting system. Compensations may require human or business authorization and are not automatic legal reversals.

## Required evidence and gates

| Question / experiment | Required evidence | Acceptance condition |
| --- | --- | --- |
| Q02/Q04/Q17/Q26; R02/R07 | Exact device/grant/organization/recipient grammar, signatures and trusted enrollment | Actual issuer cannot impersonate O; no government/DNS/operator prerequisite; wrong scope/epoch/parent rejects |
| Q11/Q15; E08 | Authorized technical and business assertions independently parsed | Wrong principal/hash/revision/action rejected; technical fact never becomes business approval |
| Q12/Q15; E09 | Crash/retry/restored-backup operation/effect schedules | Duplicate deliveries do not blindly repeat effects; uncertain external outcome remains uncertain |
| Q15; E12 | Two independent concurrent implementations, partition/reorder/crash/forks/rejoin | Same complete set produces same fact/decision/conflict state; parallel authorized decisions work; no timestamp winner; revoked/stale authority handled per approved limits |
| Q15/Q16; E13 | Per-device signer/session mapping and revoked session tests | Session identity is not confused with shared account key; returned events exactly match requests; copied-secret limitation explicit |
| Q17/Q26; E14 | Root/device transitions, rollback/forks and recovery | Compromised old authority cannot silently recover itself; checkpoint freshness assumptions tested |
| Q01/Q15; optional E16 | Separate device-key encryption/MLS membership/archive profile | Independent membership/offline/recovery evidence without replacing company authorization by group membership |

Minimum E12 corpus: compatible parallel accepts; opposing accept/reject; concurrent resolutions; late third head; missing/cyclic parents; stale/expired grant; known revocation; partition-hidden revocation; attacker backdating after known revocation; authorization fork; root compromise; removed device reconnect; duplicate operation effects; crash after import before ACK; restored stale log; inaccessible logs; uncoordinated sinks. Record the latter's duplicate-effect counterexample honestly.

No concurrency experiment was executed in NBDP-005. Normative R06/R07 drafting may begin with these alternatives, but safe SDK/device authority waits for exact contracts, Product Owner freshness/effect policy, independent security review and E08/E09/E12/E13/E14. Q15 remains BLOCKER.
