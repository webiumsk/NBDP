# Persistent NBDP Codex workflow

This setup coordinates project work; it is not NBDP transport, an SDK or an unattended service. Tested CLI: **0.162.1**, 2026-10-11. The current conversation remains active. Project rules inherit the approved [decisions](../decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md), [ADR](../../adr/0001-transport-selection.md) and [risk register](../research/architecture-risk-register.md).

## Entry points and responsibilities

| Surface | Responsibility |
| --- | --- |
| [Root AGENTS.md](../../AGENTS.md) | Project Manager/Lead Architect instructions, Slovak communication, startup state and delegation policy |
| [.codex/config.toml](../../.codex/config.toml) | Existing enabled/concurrency settings plus explicit stable multi_agent feature; no model/provider/approval/MCP overrides |
| [.codex/agents/](../../.codex/agents/) | Standalone specialist definitions; name/description/developer_instructions and scoped sandbox defaults |
| [.agents/skills/](../../.agents/skills/) | Reusable resume, source-evidence, protocol-review, future experiment-gating and review-handoff workflows |
| [PROJECT_STATE.md](../PROJECT_STATE.md) / [ROADMAP.md](../ROADMAP.md) | Actual progress, next authorized task, dependencies, evidence and approval gates |

The coordinator selects bounded work and owns state/Git publication. Researcher investigates pinned primary evidence; architect owns assigned design documents; implementer edits only assigned files after authorization; security and QA review independently. An implementation author cannot approve their own security findings. Read-only specialist defaults are convenience limits subject to runtime/managed policy; instructions are not a substitute for enforced permissions.

A delegation names objective, allowed actions, owned files, canonical Q/E IDs, required inputs, dependencies, acceptance criteria and expected evidence. Avoid parallel writers on the same file. Dependent work and branch/commit/push/PR operations stay sequential. Actual host capacity can be lower than the configured ceiling of five concurrent spawned threads. The current harness exposes four total active slots including the root; five role definitions do not imply five simultaneous workers.

## Future session startup and resume

From this repository, a future interactive `codex` session discovers AGENTS guidance and project-local skills. Project configuration and custom agents depend on repository trust and the supported CLI. The root instructions direct the coordinator to read PROJECT_STATE/ROADMAP and relevant decisions before choosing work. This supplies durable project context; it does not recover an entire private conversation or automatically execute the next milestone.

For a saved conversation use the installed CLI's `codex resume` picker, or `codex resume --last` when the most recent applicable session is intended. These are future user actions, not commands executed during this setup. Do not restart a current session simply to refresh configuration. Existing sessions may retain their original tool/role catalog; do not claim hot reload. New skills can be read explicitly in an active session if they are not yet in its catalog.

On resume, inspect cwd, Git status/branch and current user scope. Preserve uncommitted work. If state and repository evidence disagree, reconcile them and disclose uncertainty before dependent work. Reading state is not authorization for experiments, production SDK, external messages or deployments. Scope-sensitive approval gates remain explicit. No cron, daemon, hook or scheduled execution is installed by this setup.

Before handoff the coordinator records actual completed evidence, active branch/PR dependency, next bounded step, blockers and required decisions. Store durable summaries in Git, not credentials, raw private prompts or session databases. A future session must re-inspect runtime tools/integrations and approval state rather than trusting a stale inventory.

## Configuration compatibility and preservation

CLI 0.162.1 supports existing `[agents] enabled = true` and `max_concurrent_threads_per_session = 5`. Standalone `.codex/agents/*.toml` discovery supports name, description, developer_instructions and ordinary config keys; no duplicate legacy role mapping is added. Models/reasoning inherit available user/session settings. The existing security instructions and protocol-review skill are preserved; only the security sandbox default is appended. Existing AGENTS/state/roadmap text is retained and extended.

User-level configuration, authentication and trust files are never rewritten. A fresh clone may require the user's ordinary trust decision before project settings apply; this setup does not silently trust it or bypass policy. Startup behavior and schema must be revalidated on CLI upgrades. The validation report distinguishes strict parser checks, prompt discovery and live delegation.

Official references: [Subagent schema/discovery](https://learn.chatgpt.com/docs/agent-configuration/subagents), [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), [skills discovery](https://learn.chatgpt.com/docs/build-skills), [AGENTS guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [configuration precedence/trust](https://learn.chatgpt.com/docs/config-file/config-basic). Local installed-version checks take precedence over examples for older versions.

## Git and PR handoff

The baseline is NBDP-005 commit `caa856c9881d2d7e58e63515820b7521a89cbe2b`, on `research/po-decisions-e01-e06`, with [PR #1](https://github.com/webiumsk/NBDP/pull/1) still unmerged at setup. `feature/persistent-multi-agent-workflow` is based on that branch. Its PR targets the research branch as a **stacked configuration-only change**, preserving the research decisions without duplicating their full diff against main. After the dependency merges, an authorized maintainer can retarget/reconcile the stack. Nothing merges automatically.

This managed workspace currently presents a read-only empty `.git` mount, so ordinary git discovery fails. Existing metadata from the same ongoing work is `/tmp/nbdp-publish-repo/.git`. The coordinator uses explicit `--git-dir`/`--work-tree` arguments while remaining in this cwd. No repository is cloned or working directory changed. This is a session-specific fallback, not a portable project setting or an instruction to create metadata. On an ordinary checkout use normal Git; if metadata is unavailable stop Git mutations and preserve work.

The `.codex` and `.agents` mounts are read-only to ordinary sandbox commands. Authorized scoped edits used reviewed escalation; the mount was not remounted and global protections were not changed. Future agents should identify the actual boundary and request the supported scoped action, not attempt permission bypasses.

## Tools and integrations

The [validation report](workflow-validation.md) records inspected versions, available runtime capabilities and limits. `codex mcp list --json` reported optional user-configured `openaiDeveloperDocs`. Dedicated documentation MCP tools are absent from this live tool catalog; reachability was not established under restricted DNS. Official web retrieval provided documentation fallback. No MCP server was installed, removed or made mandatory.

The active harness exposes GitHub/app connectors, local execution, collaboration and web tools. Availability of a tool name does not establish access to every account/service. GitHub access is independently checked for publishing this authorized PR. Unrelated Sites/image/pet/document integrations are unused. They never become dependencies of NBDP core or this workflow's offline project state.

## Safe validation

Run workflow-only validation from the repository root:

```sh
python3 scripts/validate-workflow.py
python3 scripts/probe-codex-config.py
```

It parses config/agent TOML, checks skill structure/links/anchors and preserved protocol evidence without running NBDP experiments. The strict CLI probe uses a disposable child-only configuration home and a stdio diagnostic server to read config; it creates no model thread, uses no credentials and does not restart the active session. The documented live smoke test uses actual subagent tools with read-only inspection, distinct from a simulated persona or a claim of native role hot reload.

Q01/Q08/Q13/Q15/Q27 remain BLOCKER. This setup changes no experiment, architecture approval, Satflux code, production relay, SDK or deployment.

The preserved-evidence manifest is scoped to this workflow setup. Later explicitly authorized protocol changes require their own reviewed preservation/evidence scope; never silently refresh hashes to conceal a change.
