# Controller guard-audit accounting addendum

SOURCE method proposal only; Root and independent security adoption precede implementation. No model, helper, service, grant or role execution is authorized here. Preserve the original MEDIUM finding and all14 unqualified ordinary attempts.

The retained P4 baseline creates controller RPC observations before the service's CaptureBudget exists, buffers them under an unrelated1MiB local bound and emits them in stdout. Consequently the original16MiB aggregate service-plus-new-RPC-proof requirement is not enforced. This addendum replaces that allowance with a conservative static reservation inside the same16MiB. It adds no broker, shared phase writer or authorization permit.

## Exact allocation and ownership

Before any new RPC proof is buffered or written, the frozen allocation is:

- Total:16777216 bytes.
- Service:8388608 bytes, including its two existing phase/proxy streams, early startup observations, RPC diagnostics and service accounting metadata. Prepay4096 bytes for the parent allocation header/footer and4096 for service RPC stderr/terminal diagnostics; neither lies outside this service share. All remaining service proof representations compete within the remaining8380416 bytes. No third service capture stream is created.
- Controllers: at most64 launch-attempt slots, each131072 bytes. Each slot contains122880 bytes for the exact encoded guardController proof,4096 bytes for its parent reservation/status/metadata and4096 bytes for new RPC stderr/error/cleanup diagnostics. No independent1MiB RPC audit allowance remains.

Thus8388608 +64×131072 =16777216. A lower actual write total does not release or refund a reservation. The stricter partition can refuse a workload that formerly consumed the entire service allowance; this is an explicit operational restriction, never a positive acceptance waiver or a claim of measured fit.

Only the existing serial host Runtime.fixture caller assigns slots. It increments and permanently debits a slot BEFORE inspect, Docker exec, helper launch or any slot ledger/proof write. Count every launch attempt, including failures and cancellations; do not use the driver's success-only fixture-call ordinal as the allocator. Attempt65 rejects before launch. The existing driver can require43 incoming calls or64 archive calls at its20-status-per-stage bound, so a32-slot design is not used.

The sole parent ledger lives under the host role output's controller-audit-reservations directory, outside every fixture-writable session/control/fixtures mount. Concrete mount evidence must prove that boundary. The parent records Root/current source/config/run/original lease/slot ordinal/operation and assigned cap. Actual helper instance and command sequence are joined in the bounded completion record. The child cannot self-assign capacity, replace a ledger or convert a slot into execution permission. Every original fresh guard still applies.

## Pre-write encoding and one-use credit

A local pure accounting object must exist before createProductionGuard/helper startup, including the serve path. Its cap comes from CODE-pinned allocation constants and must later join the exact validated plan's original16MiB. No unaccounted startup buffer is permitted.

For controllers, prepay1024 bytes of the122880-byte proof share for the closed guardController envelope, its encoded property name, fixed instance/reservation fields, array brackets and required outer comma/newline delimiters. Before each audit append, obtain the bounded UTF-8 JSON encoding of that immutable row, including already expanded base64 strings, and debit its exact length plus any array comma. Only then append the immutable encoded row. JSON/base64/header growth is not measured as raw RPC payload length.

At final emission, the actual closed envelope overhead must fit the prepaid1024 bytes, and the complete encoded guardController contribution must fit the already charged proof share BEFORE stdout is written. Reuse those exact immutable row encodings once. The memory buffer is staging for this one emission, not a second output allowance; consuming its encoding credit is not a refund or post-hoc admission. A changed row, extra wrapper field, second emission or additional retained RPC representation needs a fresh debit within the same slot and otherwise rejects.

The preferred versioned driver change reuses the already retained, verified command.stdout Pin as the fixture reply Pin. Read/hash and byte equality with the actual returned raw stdout remain mandatory. This avoids writing a second copy of the new RPC proof. If any distinct retained RPC copy is kept, charge its entire encoded contribution separately within the same slot. Record the changed source/consumer join explicitly; no bytes are stripped or substituted.

Service early memory observations are debited before append. If their later phase flush uses a different representation, conservatively debit that complete encoded phase representation before writing as well; do not recover the earlier debit. After attachment, the original single phase/proxy writer remains sole owner and charges every intended encoded write before the underlying write. All new service RPC stderr and cleanup diagnostics use the prepaid service diagnostic share; no unchecked error-log escape exists.

Parent ledger/status/header/footer encodings and all controller RPC diagnostics are measured before writing within their assigned4096-byte shares. The global allocation header/footer uses only the prepaid service4096 bytes. No extra summary, traceback, base64 copy or diagnostic file is exempt. Temporary serialization for length calculation is bounded and cannot publish or retain proof before admission.

## Failure, custody and propagation

Reservation refusal, missing capacity, unknown owner, encoding overflow, ledger mismatch or failed/short proof write poisons its owner before further protected actions. Parent reservation/ledger failure invokes the existing sticky Root role-failure/revocation and exact-owned cleanup path. Controller failure immediately fences that client and propagates through the existing command failure path. Service local capture failure preserves its original poison/first-fault fence. Preserve the first fault over later diagnostic failures.

Do not claim an atomic cross-process global fence: before the service observes the parent's fault through the existing fresh Lease checks or owned cleanup, it may still process work within its already reserved service share. The whole role is unqualified regardless. No budget reservation authorizes such work or replaces any guard.

Do not retry, repair, overwrite or refund a partial ledger, phase, proxy, stdout or diagnostic write. Retain actual prefix/count/EOF/exit facts where observed. Node stdout.write's boolean is backpressure, not a byte count; perform one intended emission and require the parent's actual complete capture/EOF/natural lifecycle for positive data. Missing/truncated audit, missing ledger, nonzero lifecycle or unmatched helper/slot/command is negative. Cleanup proceeds even when no diagnostic capacity remains; it cannot manufacture a successful record or write outside the allocation.

## Required source and consumer checks

A new version must pin the allocation, ledger layout, pre-helper accounting, exact encoders and changed driver reply reference. The consumer must join all attempted slots, parent command records, exact stdout/audit/helper IDs, current run/config/source/lease and local service budget state. It must prove caps and no missing/duplicate/reused slot, all intended representation charges and original guard/effect/custody conditions. A final sum checks consistency; producer pre-write enforcement supplies admission. A post-hoc sum alone never qualifies.

Meaningful controls must cover below/equal/above limits, wrapper/base64/non-ASCII/delimiter growth, combined service/controller owners at16MiB,64/65 attempts including failed launches, reserve-before-any-write ordering, early serve startup, denied/partial ledger and stdout writes, missing/truncated audit, duplicate copy/emission, late cancel/OK, diagnostics exhaustion, sticky first fault and honest delayed cross-owner propagation. Definitions and actual runs are future separate work.

All55s command/45s control/5s guard/10s query/3s handshake/1800s lease, fresh guard/effect points, resources, original lease core and cleanup limits remain unchanged. No new PO scope is needed for this internal restriction. New SOURCE/control/consumer/completion review and a separate future Root concrete decision remain mandatory; this method grants no archive or retry.
