# E06 policy-marker source remediation

The target prerequisite predicate required an absent contiguous marker in an otherwise correctly pinned adopted policy. The correction reads the checked policy once and checks its existing adoption and policy-name markers separately, matching Python admission. Exact policy pins, source membership, manifest joins and other prerequisites are retained.

The archived original, source.patch and prepared-source.json preserve the original source-level finding. This was not a reproduced TARGET failure. Independent QA and security accepted the narrow source change and actual local controls only.

Reproduction in the recorded local environment:

```
/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node --test --experimental-test-isolation=none experiments/prototypes/e06_relay_https_negative_v1/test_policy_marker.mjs
```

[Recorded execution](local-policy-controls-no-isolation/execution.json) and raw stdout contain ten distinct named passes, no skips. The earlier default-isolation run reported one file-level pass only and is insufficient to establish ten callback executions; its reporting difference remains unexplained. A prior absent executable launch ran no tests and is retained separately.

These are source/file prerequisite-slice controls. They do not qualify the complete fixedPrerequisites tail or source closure, inventory/derivation enforcement, original-request custody, LOCAL/TARGET, native interoperability or E06. The old443-member closure and its captures remain historical; no old acceptance transfers to changed source. Next: freeze/review the complete new closure, renew same-source controls/configuration/release and required primary/QA observations before any native target qualification. Canonical E02 remains PARTIAL and E06 NOT EXECUTED; all architectural blockers remain open.

## Further provenance obstruction

A fresh streaming audit of the prior443-member closure found441 current matches and two drifts: the corrected protocol and experiments/README.md. The latter is the coordinator-owned readiness documentation change in commit2760e9f4c225fadf6a45789f7ccaa6bf1ed002e9; current bytes match HEAD and there is no uncommitted user edit. Main989e703 contains the original4909-byte c97f800247936803ff68c38153465c9168775c8fa0405e2ca2d4b2568711bda9 version; current guidance is4996-byte 0d00ac17929309077f4c74ce9ed836e13150319e01a810d159b5c8e6f566dc28.

The README is outside the protected378-member positive baseline, but the native57-role inventory and inert qualification inputs bind its old descriptor. Replacing only its closure pin would therefore be invalid. Retain current correct documentation and prepare an explicitly versioned inventory/derivation/inert-input refresh with dependent pins and independent review. Do not restore obsolete environment claims simply to match a stored hash. The local ten marker controls do not resolve this qualification prerequisite.
