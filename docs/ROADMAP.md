# NBDP gated roadmap

Updated 2026-10-11. This document was absent at NBDP-005 start. It preserves [canonical experiments](research/required-experiments.md), [Q01–Q27](research/architecture-risk-register.md) and [approved decisions](decisions/PRODUCT_OWNER_DECISIONS_2026-10-11.md).

| Order | Milestone | Prerequisites and exit evidence | Approval boundary |
| --- | --- | --- | --- |
| 1 | Complete transport evidence gate | Isolated ordinary-client control completes E02; then E04 actual frames/resources and E06 exact file/correlation/download interoperability; review 12/16-byte producer nonce alternatives | Product/security review exact carrier, byte profile and limits; no kind allocation |
| 2 | Draft and independently review R01–R08 candidates | Inputs/readiness in [validation summary](research/experimental-validation-summary.md#rfc-readiness); identify unresolved normative clauses and public test vectors | G1 reviewed text; drafting is not SDK permission |
| 3 | Validate storage, authenticated receipts and durable replay | E07/E08/E09 with verified metadata, independent hosts, sender/recipient/action binding, crash/restore/same-ID conflicts | Q08/Q11/Q12/Q19/Q20/Q27 evidence; no legal delivery inference |
| 4 | Validate relay/privacy/offline objective | E10/E11/E15; H7/R10, surviving copies, skew, backdating/pagination/reconciliation; separate accelerated and real-duration trials | Q01/Q13/Q14/Q18/Q21; no arbitrary public relay delivery guarantee |
| 5 | Validate parallel authority and key lifecycle | Reviewed per-device scoped grants/revocations, freshness/causal conflicts/effect domains; E12/E13/E14 and relevant E08/E09 | Q15 remains blocker until independent partition/concurrency tests and Product/security approval |
| 6 | Assess SDK gate | Relevant G0/G1/G2 evidence complete, blockers resolved with evidence and explicit G3 authorization | No SDK implementation currently authorized |

Portable document proof/E14 signature extension is deferred under PO-005; baseline key continuity/capability E14 work remains necessary. A separately versioned stronger security profile may be researched later with E16; static NIP-44 has no FS/PCS. No mandatory Peppol, government, Satflux, Evolu, registry, host or central coordinator is introduced by this roadmap. Deployment, integration and compliance implementations are outside the current task.
