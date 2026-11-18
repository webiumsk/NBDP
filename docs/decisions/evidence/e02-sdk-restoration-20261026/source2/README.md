# SDK434 restoration SOURCE2 — placement failure-evidence correction

The original SOURCE1 subject, script and plan remain byte-for-byte unchanged.
QA identified a MEDIUM reporting defect: a successful rename followed by a
post-placement failure could previously produce `failure.json` with `placed:false`.
SOURCE2 changes placement reporting and its isolated work directory only. The
original 434-file inventory, member mappings, URLs, hashes, modes, SDK destination,
download/extraction rules, reserve and time budgets remain unchanged.

Placement state is explicit:

- `NOT_ATTEMPTED`: the rename boundary has not been entered.
- `UNKNOWN` / `placed:null`: the call may have taken effect but no definite
  success/refusal was observed, including exceptions and ambiguous I/O/interruption
  results. Unknown return values remain unknown.
- `PLACED`: return0 was observed and recorded immediately, before opening the
  destination, checking inode identity, closing the descriptor, fsync, deadline
  or disk checks. Every later failure retains this state.
- `NOT_PLACED`: a recognized refusal result was returned. This means only that
  this invocation did not place its stage. It never means the destination is
  absent; a foreign existing destination is neither modified nor removed.

Both success and failure receipts use the same placement-state projection.
`renameReportedReturn`/`renameReportedErrno` retain available observations. An
interruption between the actual call and Python observing its return is recorded
honestly as unknown rather than inferred from a later path check.

Seventeen proposed pure fake-operation controls call the real `publish()` and
`run()` failure-receipt wiring with modeled FFI/filesystem/deadline/receipt
operations. They cover pre-rename refusal, rename errors, post-rename open/inode/
close/fsync/deadline/disk failures, interrupted and ambiguous outcomes, and success.
No real filesystem placement, SDK, network, download, extraction, tools or license
operation occurs in those models. They do not qualify real runtime behavior.

This packet is SOURCE preparation only. Python AST parsing passed; controls are
defined and have not run. Independent SOURCE QA/security and a separate bounded
control release must precede model execution. Acquisition remains separately
unauthorized until those results and the source are independently reviewed.

Proposed model command after release:

```text
/home/peterhorvath/.miniforge3/bin/python3.13 -I -B /tmp/nbdp-sdk-restoration-20261026-r2/test_placement_models.py
```

The copied acquisition plan is exactly SOURCE1's plan. SOURCE2's script uses a
fresh sibling work directory and keeps the original SDK destination. No existing
runtime/evidence is overwritten, and canonical experiment/security gates remain.
