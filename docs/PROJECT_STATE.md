# NBDP project state

Updated 2026-10-11 for NBDP-005. This file was absent at task start; it records the actual current state, not invented prior governance.

Option B is **Conditionally Accepted — Architecture Direction Only** under [PO-001–PO-006](decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md). Exact wire format, SDK, release and production use are unapproved. No new NIP/kind is authorized. Satflux remains independent and unchanged.

[Experimental summary](research/experimental-validation-summary.md): E01 PASS140, E02 PARTIAL22 (ordinary-client control unavailable), E03 PASS19, E04 NOT EXECUTED, E05 PASS25, E06 NOT EXECUTED. E04/E06 obey E02's dependency gate. Full evidence/reproduction and independent QA/security review are committed in experiments; passing subchecks do not close architecture blockers.

Q01/Q08/Q13/Q15/Q27 remain BLOCKER. [Risk register](research/architecture-risk-register.md) preserves all Q01–Q27: 3 DECIDED, 12 RFC_REQUIRED, 7 EXPERIMENT_REQUIRED, 5 BLOCKER. [Canonical plan](research/required-experiments.md) retains E01–E16. Parallel device authority is required; the prior single-active proposal is superseded. [Current candidate](research/multi-device-authority-design.md) needs signed authority/causal records and independent later concurrency tests.

Immediate milestone: finish E02 ordinary-client evidence, then E04 and E06 with reviewed profile assumptions. [Roadmap](ROADMAP.md) lists subsequent gates. RFC drafting may begin in qualified areas; production SDK work cannot. The dedicated research branch/PR is for review only and must not merge automatically.

## Persistent workflow setup — 2026-10-11

The current assignment is project-local multi-agent orchestration only, on
`feature/persistent-multi-agent-workflow`, based on NBDP-005 commit
`caa856c9881d2d7e58e63515820b7521a89cbe2b`. [PR #1](https://github.com/webiumsk/NBDP/pull/1)
is the unmerged research dependency. The workflow PR is stacked onto that research
branch; it does not accept or merge the architecture.

Root AGENTS guidance, five specialist definitions, reusable project-local skills and
[session workflow documentation](development/codex-workflow.md) establish future resume
and handoff behavior. [Validation report](development/workflow-validation.md) records
schema/discovery checks, real read-only delegation, preservation and tool limitations.
User-level configuration and the active conversation are preserved. No NBDP experiment
is run or modified for this setup; the previously recorded results above remain historical.

After workflow review, the protocol milestone remains the existing E02 control → E04 → E06
sequence. A new session must confirm the user's task scope and approval gates before
executing it. Q01/Q08/Q13/Q15/Q27 remain blockers; production SDK is unauthorized.

Workflow setup is complete and published for review in [PR #2](https://github.com/webiumsk/NBDP/pull/2),
targeting `research/po-decisions-e01-e06`. Setup commit:
`264a88a4f64a216398711072622fad866b16dd23`. The PR is open and unmerged.
The user has not authorized any protocol experiment through this workflow task.
