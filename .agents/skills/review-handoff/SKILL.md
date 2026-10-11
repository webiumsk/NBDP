---
name: review-handoff
description: Prepare an NBDP task handoff or reviewable branch and PR with independent evidence and explicit approval gates.
---

# Review Handoff

Inspect Git status/branch and preserve unrelated work. The coordinator publishes only within
current authorization; skills do not authorize pushes, messages, deployments or merges by themselves.
Use a dedicated branch. If its base is an unmerged research PR, disclose the stacked dependency;
do not silently include that entire earlier diff in a main-targeted PR or merge/rebase it.
Collect independent QA/security findings where relevant, with severity, evidence and unresolved scope.
Check changed paths, relative links, canonical IDs, actual result/report consistency and the complete
diff. Do not rerun NBDP experiments merely to validate documentation or workflow settings.
Record work/evidence/limits in project state. Describe concrete behavior, validation and approval
boundaries for a reviewer without conversation history. Preserve failures and unexecuted work.
Report branch, commit, PR and next bounded milestone accurately. Do not automatically merge or
claim that AI review is a professional security audit or Product Owner acceptance.
