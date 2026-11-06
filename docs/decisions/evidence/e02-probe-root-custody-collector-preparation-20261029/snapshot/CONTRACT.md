# Root probe custody collector

This SOURCE implements only byte-accounted metadata custody. It does not run a tool, call an API, create a process, infer a CID or fabricate a receipt. Root supplies the exact genuine raw request/response/diagnostic bytes. SOURCE, controls DATA and concrete release remain independent future gates. No experiment, model or collector command has been executed during preparation.

## One existing account

The external Root slot is exactly65536 bytes inside the controller's existing8388608-byte metadata owner. It is not another8MiB owner, another65536 allowance or a refund of the controller's reserve. Root must bind this run's actual reservation receipt to the matching controller release `outerCustodyReservationBytes=65536`. The controller must deduct that SAME65536 before other metadata writes. The collector's reservation is durable before any new run lease, concrete plan, gate, grant, API original, diagnostic or retained copy. A later controller construction cannot retroactively precharge a prior Root write.

`reserve --run-id <32 lower hex>` creates two fresh owned0700 directories under fixed CODE paths: Data `probe-root-custody-actual/<run-id>` and repository `e02-probe-root-custody-actual-20261029/<run-id>`. An exclusive0600 reservation file records the full65536 slot and is fsynced, together with its directory and fixed parent entries, before returning. Existing run roots cannot be reset or retried. Setup/source/control-model files in the preparation namespace are separate from future actual proof; no actual run roots are created by source preparation.

The initial charge permanently prepays16384 bytes for all accounting overhead: reservation<=1024, at most64 immutable charge records each<=224, first failure<=512. Their maximum15872 fits that reserve; the unused512 is not refundable. This leaves49152 bytes for ALL originals and every separately retained copy. The invariant is physical regular-file content<=16384+49152=65536; filesystem directory blocks/inode allocation are not measured as proof content. Zero-byte originals still consume one of64 operation records.

## Durable charge before bytes

A retained exclusive flock on the pinned reservation inode serializes both stores. Closed ledger reconstruction validates the fixed slot/run/root identity, all consecutive charge rows, exact retained sizes/hashes, source-copy joins and exact file membership. Pending/malformed charge, missing/changed proof, extra file or unsafe root never becomes a positive status.

For every proof, immutable `charge-NN.json` is created O_EXCL|O_NOFOLLOW0600 with one exact write, file fsync and directory fsync BEFORE opening the proof output. Its declared complete byte count is consumed monotonically. The proof is also exclusive, non-symlink, single-link, owned0600, one exact write with file/directory fsync. All streams and records are opaque bytes. There is no append, overwrite, short-write repair, truncation, refund or budget renewal. Copy bytes and the copy's new ledger row are charged again, even for an identical digest. Both Data and repository stores share the SAME account.

Overflow, duplicate, invalid flat name, wrong copy source, short write, ENOSPC or drift is sticky in memory and, when the retained Data identity permits it, in the separately prepaid exclusive first-failure record. An existing first failure is never replaced. If storage failure prevents that marker, an incomplete durable charge/proof still refuses on reopen. If the Data root identity itself is unavailable, no foreign path is written and no success is issued; Root must reconcile the unknown filesystem state rather than automatically retry or restore a positive result.

## Closed CLI

- `reserve --run-id ID`
- `record --run-id ID --kind KIND --name NAME [--input ABSOLUTE_READONLY_FILE]`; absent input consumes bounded stdin. KIND is exactly lease, plan, gate, grant, api-request, api-frame or diagnostic. Input is never interpreted as authority or executed.
- `copy --run-id ID --source-index N --store data|repo --name NAME`; source is an already validated registered proof. Every copy is a new physical charge.
- `status --run-id ID`; read-only positive status is available only for a healthy exact account. It is byte-custody status, not probe acceptance or runtime authorization.

Names are flat, at most48 ASCII letters/digits/dot/underscore/hyphen with an alphanumeric first character. Callers cannot choose another root, arbitrary target directory or overwrite an earlier record. Files are stored with CODE-defined kind prefixes. The account roots and their handles must retain the exact reserved device/inode/owner/group/mode; fixed parents must remain owned0700 and non-symlink. Symlinks, special files, hardlink aliases and unregistered output are refused. Supplied files are opened read-only/nonblocking/no-follow and size/identity checked; bounded stdin overrun refuses before any proof open.

Any additionally retained reservation/ledger copy, collector stdout, raw API frame or diagnostic must also use a charged `record`/`copy` operation. A ledger/header may be supplied as exact read-only bytes to `record`, then copied to the repository through `copy`; both new copies consume payload. Output paths outside these two registered stores are not authorized proof outputs. Root's actual workflow/concrete review must inventory all retained records; the program does not claim to attest arbitrary external host writes or authenticate caller-supplied JSON.

## Evidence gates

Twenty named temp-FS/mocked definitions cover ordering, same-owner reservation, each duplicate, raw exact bytes, payload/count edges, sticky errors, first-failure retention, no-write-on-overflow, partial/failed storage, unregistered/symlink/hardlink files, root modes/identity and no account reset. They import the owned collector only when a separately released future control invocation occurs. They do not establish actual API/helper/container/SDK/client DATA. Author preparation used AST/compile and hashing of owned small SOURCE files only. Independent QA/security SOURCE review, actual released controls and independent DATA review, then concrete Root approval remain required. Controller external collector SOURCE/DATA/precharge/actual-byte gates remain NULL here.
