---
name: experiment-gates
description: Plan or coordinate separately authorized NBDP experiments while preserving canonical dependencies and evidence gates.
---

# Experiment Gates

Read docs/research/required-experiments.md and the complete assigned experiment before acting.
Preserve canonical IDs: E01 is crypto/full validation; E02 is envelope exchange. Check the
current pinned candidate, authorization, dependency statuses/source hashes and isolated environment.
PARTIAL/FAIL cannot unlock a mandatory PASS prerequisite. A missing environment is NOT EXECUTED;
a failed assertion remains FAIL. Do not weaken assertions or alter expected answers for a pass.
When execution is explicitly authorized, use synthetic public disposable keys/data, existing crypto
libraries and allowed local endpoints; record commands, actual exits, duration, environment and
independent implementation limits. Preserve negative results and distinguish simulations from real time.
The coordinator owns shared state/publication; workers own assigned experiment files. Obtain
independent QA/security review for relevant changes. No SDK, Satflux integration, production relay
changes or blocker closure follows from running an experiment. Workflow setup tasks must not run
NBDP experiments. Planning alone does not authorize execution.
