# Codex workflow validation

**Status: PASS — setup and bounded read-only delegation**, 2026-10-11. Native configured-role hot reload/routing is **NOT TESTED** in this active session. [Workflow guide](codex-workflow.md) and [preservation baseline](workflow-baseline.json) define scope. No NBDP experiment, SDK, Satflux modification, deployment or blocker closure occurred.

## Environment and preservation

Initial cwd was `/home/peterhorvath/apps/bitcoin/NBDP`; ordinary Git discovery failed because this workspace mounts an empty `.git` read-only. The existing metadata from this same ongoing task, `/tmp/nbdp-publish-repo/.git`, established branch `research/po-decisions-e01-e06` at `caa856c9881d2d7e58e63515820b7521a89cbe2b`. Status initially showed untracked AGENTS/.codex/.agents user files, with no tracked changes. Their original contents were captured before changes and preserved, not discarded/stashed. A feature branch was created in this cwd without cloning or restarting.

The setup retains original byte prefixes of AGENTS, project config, security role, PROJECT_STATE and ROADMAP. The original protocol-review skill remains byte-identical. The baseline checks **85 protocol/research/experiment/skill evidence files** unchanged. User-level config.toml SHA-256 remained identical; no user authentication, trust, MCP or model settings were rewritten. .codex/.agents scoped writes used reviewed escalation because ordinary sandbox mounts were read-only; no mount or security policy was changed.

## Actual validation results

| Check | Command or actual operation | Result and interpretation |
| --- | --- | --- |
| Installed version | `codex --version` | Exit 0, CLI **0.162.1**; current session preserved |
| Feature inspection | `codex features list` | multi_agent stable true; project feature explicitly added |
| Strict positive parse/effective project layer | `python3 scripts/probe-codex-config.py` | Wrapper exit 0; diagnostic stdio process exit 0, initialize/config-read responses; enabled=true, concurrent-spawn ceiling5, multi_agent=true |
| Strict negative control | Same helper, `codex --strict-config -c nbdp_unknown_schema_probe=true app-server --stdio` | Expected child exit 1 naming unknown field; verifies rejection before task/model execution |
| Root guidance/skill discovery | `codex debug prompt-input` in disposable child-only home and this same cwd; existing Git metadata supplied for restricted discovery | Exit 0; root appended guidance and all five skill names present. Raw prompt/config output stays out of Git |
| Specialist definitions | TOML parsing and required-field/schema checks | Five unique names; research/security/QA default read-only; editing roles inherit sandbox/model/provider/approval settings |
| Skill validation | Bundled `quick_validate.py` for all five skills using `/usr/bin/python3` | Five exit0 checks, PyYAML6.0.1. Initial default-Python attempts failed because yaml was absent; no global package installation was performed |
| Genuine schema-research delegation | Actual spawn of `/root/workflow_schema_review` | Read-only specialist returned installed-version/official-source evidence; no file edits or protocol experiment |
| Genuine QA smoke | Actual spawn of `/root/workflow_qa_smoke`, explicitly instructed to read `.codex/agents/qa.toml` | PASS, validator exit0; correct branch stack and retained next milestone/blockers reported through mailbox |
| Read-only smoke preservation | Before/after hashes of 34 workflow/document/role/skill files | Zero changed files during the child test; coordinator made subsequent report edits separately |
| Repository workflow checks | `python3 scripts/validate-workflow.py` | PASS: config/roles/skills, preserved content/evidence, Markdown links/anchors/fences and retained blockers; no protocol tests executed |

The live spawn interface in this session has no named-role selector. The QA agent read and applied its role instructions explicitly; this is real independent delegation, not proof that the newly authored role catalog was hot-loaded. The CLI prompt constructor verified guidance/skills only and does not prove native role routing. Future trusted sessions discover standalone role files according to the [official schema](https://learn.chatgpt.com/docs/agent-configuration/subagents); startup/trust behavior and CLI version remain conditions, not a tested upgrade guarantee.

Independent final read-only QA re-ran the workflow validator (exit0), checked state/link preservation and found a low-severity failure-cleanup issue in the reusable strict helper. The coordinator replaced success-only cleanup with TemporaryDirectory and try/finally plus bounded terminate/kill/wait, and re-ran the strict positive/negative probe successfully (wrapper exit0). The reviewer confirmed the fix by source review and did not independently execute the strict probe or fault-injection tests.

The strict helper creates only a disposable configuration home/trust record, inherits this cwd, removes API-key environment variables, starts no model thread and closes its no-network-listener stdio diagnostic process. It never copies user credentials or changes the active session. The temporary PATH-helper refusal warning is recorded as a diagnostic warning, not parser failure. `--strict-config features` and `--strict-config debug` are unsupported (observed exit1); neither is used as strict proof. Broad doctor checks encounter read-only state/DNS/provider limitations and are not presented as a passed health check or proof of user-database corruption.

## Development tools and integrations inspected

| Tool | Observed version / status |
| --- | --- |
| Codex | 0.162.1 |
| Git / GitHub CLI | 2.43.0 / 2.93.0 |
| Python / system skill validator | 3.13.12 / system Python with PyYAML6.0.1 |
| Node / npm | 22.18.0 / 11.17.0 |
| Docker | 29.9.0; version inspection only, no container/relay changes |
| OpenSSL | 3.6.1; version inspection only, no crypto experiments |
| Rust/Cargo | Absent from current PATH; previous experimental isolated tools are not installed into this workflow |
| User-configured MCP | `codex mcp list --json`: optional openaiDeveloperDocs at https://developers.openai.com/mcp, enabled, auth unknown |
| Active harness integrations | Collaboration, local execution, GitHub/app connectors and web retrieval exposed; unrelated app integrations unused |

Dedicated documentation MCP tools are not exposed in this active tool catalog; restricted DNS/reachability checks failed. Public official pages were retrieved through web fallback. No MCP integration was installed or removed, and availability of a tool name is not proof of every connected service's credentials. GitHub access verified the existing open PR #1 dependency; workflow publication is separately recorded below.

Official sources used: [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [skills](https://learn.chatgpt.com/docs/build-skills), [AGENTS guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [trust/precedence](https://learn.chatgpt.com/docs/config-file/config-basic). Installed-version checks resolve older-example ambiguity; existing agents.enabled/concurrency/name/description fields are supported and were preserved.

## Boundaries and review handoff

Branch: `feature/persistent-multi-agent-workflow`; base: `research/po-decisions-e01-e06`. The PR is stacked on the unmerged [PR #1](https://github.com/webiumsk/NBDP/pull/1), so its diff contains workflow setup rather than all earlier research. [PR #2](https://github.com/webiumsk/NBDP/pull/2) was created and verified OPEN with no merge, targeting the research branch. Setup commit: `264a88a4f64a216398711072622fad866b16dd23`; publication metadata is recorded in a follow-up commit on the same branch. GitHub verified all 24 changed paths are workflow configuration, skills, state/roadmap, documentation or workflow-only helpers. Nothing merges automatically.

Future sessions recover project context via AGENTS + state/roadmap, or saved conversation via the documented resume command. They do not automatically launch protocol milestones, gain new execution permission or recover an entire conversation from files. Current-session native role refresh remains unverified and no restart was performed to force it.

Option B stays conditionally accepted for architecture direction only. Q01/Q08/Q13/Q15/Q27 remain BLOCKER. The existing E02 control → E04 → E06 milestone is retained with its approval/dependency gates; no experiment result is modified or rerun by this task.
