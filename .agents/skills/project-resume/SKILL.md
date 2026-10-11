---
name: project-resume
description: Resume or hand off NBDP work using persistent state, actual Git status and approval boundaries.
---

# Project Resume

Read the root AGENTS.md, docs/PROJECT_STATE.md and docs/ROADMAP.md from the repository root.
Inspect the actual cwd, Git status/branch and current PR dependency; preserve uncommitted work.
Read the approved decisions, relevant ADR and risk records when they affect the task.
Reconcile the latest user instruction with the recorded active task; do not treat a roadmap
item as execution authorization. Canonical Q01–Q27/E01–E16 remain traceable.
Report completed evidence, the next bounded authorized action, dependencies and approval gates.
Use real subagents for independent work within runtime capacity and disjoint ownership.
Before handoff, the coordinator updates state with actual outcomes and unresolved work.
For session/trust and restricted Git behavior, read docs/development/codex-workflow.md.
Never infer that a new session recovered private conversation history merely by reading files.
