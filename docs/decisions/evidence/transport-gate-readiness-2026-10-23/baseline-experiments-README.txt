# Isolated NBDP experiments

NBDP-005 authorizes synthetic E01–E06 engineering only. This directory is not an SDK or normative RFC. The [canonical plan](../docs/research/required-experiments.md) controls IDs: E01 is crypto/full validation, E02 is envelope exchange. NBDP-005 §6 reverses those titles; both scopes are tested under their original IDs.

Test private scalars 1, 2 and 3 are **public, disposable, test-only fixtures**. They and all published fixture encryption keys must never secure anything real. Fresh randomized gift-wrap keys are also disposable. No production keys, merchant data, public relays, external blob endpoints, Satflux code or credentials are used. Runs do not send test events to GitHub or public Nostr relays; only synthetic evidence is committed.

## Preparation

Use Node 22.18.0, npm 11.17.0 and Rust 1.90.0. Dependency lockfiles freeze the tested tree. Bootstrap requires public package/source downloads; tests themselves use only local processes and explicitly allowed loopback endpoints. Browser tests use installed Chrome; record its version in each run, and pass `NBDP_CHROME` to reproduce with the same executable. No dependency install scripts are enabled.

```sh
cd experiments
npm ci --ignore-scripts --no-audit --no-fund
cd shared/rust
cargo build --locked
cd ../..
node shared/run.mjs E01
node shared/run.mjs E02
node shared/run.mjs E03
node shared/run.mjs E04
node shared/run.mjs E05
node shared/run.mjs E06
```

E06 refuses to execute unless canonical E01/E02/E05 mandatory prerequisites pass. E04 requires E01/E02. A missing environment or prerequisite produces NOT EXECUTED, not a fabricated PASS. Full experiment status also records unexecuted scope and deviations. Local raw output is under `.runtime/`; reviewable machine evidence is under `results/`. Runtime stores and build/install directories are ignored. See each experiment README and result report for commands actually executed.

The [candidate contract](shared/candidate-profile.md) freezes expectations before runs. Both application validators are independently written (JavaScript and Rust); they share fixtures and assertions, not parser or validation code. nostr-tools uses noble cryptography; Rust Nostr uses Rust crypto and libsecp256k1. Browser Web Crypto AES-GCM and Node's OpenSSL EVP cipher API are separate implementations; Node Web Crypto is not used as the independent browser control.

## Relay preparation

`docker/` records source-pinned relay builds and loopback-only configurations. Only containers with the `nbdp-005-` prefix may be managed by these experiments. No existing containers are stopped or modified. Build/image/package manifests describe any remaining reproducibility limits. Local plaintext ws/http is permitted only for synthetic loopback tests and establishes no TLS/privacy deployment claim. TLS/operator/privacy checks remain later E10/E15 work.

Ordinary-client ecosystem controls, public-network delivery, seven-day real-time recovery and multi-device authority are not inferred from a successful adapter round trip. Reports explicitly identify these limits.

## Evidence quality checks

From the repository root, run `python3 experiments/validate-evidence.py`. It checks all six report/status/hash records, original research hashes, canonical Q/E mappings and local Markdown targets/anchors. This is documentation/evidence validation, not a cryptographic audit or substitute for experiment runtime. Each exact final runtime command is in its result report; blocked E04/E06 commands return 2.

The ordinary-client control needs a separate qualified Android environment (no adb, emulator or /dev/kvm was present in this lab). E02 currently always records that control as unexecuted; an actual control driver/evidence integration must be added before its complete rerun can PASS. Installing a tool or passing an ad hoc JSON approval flag is not that evidence. The following preparation commands are prospective and were NOT executed here:

```sh
git clone https://github.com/vitorpamplona/amethyst.git /tmp/nbdp-005-amethyst-control
git -C /tmp/nbdp-005-amethyst-control checkout e6f464a1179def75274512b3c5bab921de3bf3d8
cd /tmp/nbdp-005-amethyst-control
./gradlew :amethyst:tasks --all
# Choose and record the supported isolated build variant from this exact pin.
adb reverse tcp:17777 tcp:17777
adb reverse tcp:18081 tcp:18081
```

Use fresh app/device state, disposable public test identities and a network policy allowing only the forwarded lab relays. Observe the published E02 kind14 fixtures, ordinary text, unsupported versions/features and retained private fields; save the build/runtime/fixture hashes and exact UI/driver steps. No build variant, APK, install or UI compatibility is asserted here. The remaining dependent reproduction commands are `node shared/run.mjs E04` and `node shared/run.mjs E06` only after their complete prerequisites pass.
