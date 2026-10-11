# E05 — AES-GCM byte profile, nonce discipline and cross-crypto vectors

Canonical scope: [original plan](../../docs/research/required-experiments.md#e05). The NBDP-005 section titles interchange E01/E02; this directory preserves the original ID meaning.

Prerequisites: **none**. Read [candidate contract](../shared/candidate-profile.md), [environment](../README.md) and the [result](../results/E05.md) before running. Inputs are the retained public vector corpus and explicitly public/disposable generated fixtures. Every test uses synthetic bytes/keys and bounded inputs; no production service is an endpoint.

Scope: Actual browser Web Crypto versus Node OpenSSL EVP; standard known answer, cross-decryption, malformed/tampered bytes, strict encodings and commitment checks.

```sh
cd experiments
NBDP_RUST_BIN=/tmp/nbdp-005-rust-target/debug/nbdp-experiment-rust node shared/run.mjs E05
```

For a normal local Cargo build omit `NBDP_RUST_BIN`. Actual commands, exit status, duration, source hashes, environment, outcomes and skipped scope are written to [machine-readable evidence](../results/E05.json). Expected success means all mandatory candidate criteria agree; mismatches remain FAIL. A missing mandatory runtime/scope is PARTIAL/NOT EXECUTED, never compilation-as-interoperability. E06 must not run with an unpassed prerequisite.

Hazards/controls: public fixture keys must never secure real data; finite parsing/frame/file budgets; no distinct-plaintext AES-GCM key/nonce reuse; no thumbnails; fresh outer keys; signer authentication separate from business/legal authority; local stores/builds ignored. Relays/blob hosts are loopback-only synthetic fixtures. Chrome is a fresh profile with external requests blocked. Independent producer/library source pins and implementation-sharing limits are in the environment/result records.

No seven-day availability, multi-device authority, accounting effect, forward secrecy, production readiness or ecosystem-wide conformance is inferred. E08/E09/E11/E12 and security review remain later gates.
