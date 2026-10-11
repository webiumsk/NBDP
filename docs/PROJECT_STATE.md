# NBDP project state

Updated 2026-10-11 for NBDP-005. This file was absent at task start; it records the actual current state, not invented prior governance.

Option B is **Conditionally Accepted — Architecture Direction Only** under [PO-001–PO-006](decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md). Exact wire format, SDK, release and production use are unapproved. No new NIP/kind is authorized. Satflux remains independent and unchanged.

[Experimental summary](research/experimental-validation-summary.md): E01 PASS140, E02 PARTIAL22 (ordinary-client control unavailable), E03 PASS19, E04 NOT EXECUTED, E05 PASS25, E06 NOT EXECUTED. E04/E06 obey E02's dependency gate. Full evidence/reproduction and independent QA/security review are committed in experiments; passing subchecks do not close architecture blockers.

Q01/Q08/Q13/Q15/Q27 remain BLOCKER. [Risk register](research/architecture-risk-register.md) preserves all Q01–Q27: 3 DECIDED, 12 RFC_REQUIRED, 7 EXPERIMENT_REQUIRED, 5 BLOCKER. [Canonical plan](research/required-experiments.md) retains E01–E16. Parallel device authority is required; the prior single-active proposal is superseded. [Current candidate](research/multi-device-authority-design.md) needs signed authority/causal records and independent later concurrency tests.

Immediate milestone: finish E02 ordinary-client evidence, then E04 and E06 with reviewed profile assumptions. [Roadmap](ROADMAP.md) lists subsequent gates. RFC drafting may begin in qualified areas; production SDK work cannot. The dedicated research branch/PR is for review only and must not merge automatically.
