# API35 ordinary-client v3: semantic shape without positional identity

SOURCE ONLY. No v3 controls or Android actions have executed. New source/config
and plan: `docs/decisions/evidence/e02-ordinary-api35-preparation-r3/`.
The exact failed v2 sources, observations and original wrong-index test case are
preserved. Actual ui009->ui010 showed the whole public synthetic NSEC, same
shown eye and password metadata; only button.index3->2 changed in the added
fingerprint when the preceding placeholder TextView disappeared.

The only driver change excludes positional index from the semantic-shape keys
and clarifies its docstring. All other driver methods are AST-identical to v2:
closed current uniqueness/package/ancestry/bounds, known source-bound shown
state, at most one Hide-to-Show action, exact entire public NSEC, post-input
PNG/XML/evidence, existing keyboard-dismissal check, ANR, fixture/export,
budgets and original1800s lease remain unchanged. Matching class/package and
resource IDs (often empty) establishes semantic shape consistency; it never
proves a persistent object identity across Compose recomposition.

49 UI and26 namespace/release cleanup definitions need actual independent
SOURCE review, then finite current controls and independent result acceptance.
The real disappearing-placeholder/index3->2 regression complements the prior
synthetic geometry-only case. Foreign/duplicate/malformed controls, semantic
resource/class/package/role changes, changed eye, unknown metadata and all
partial/masked/missing/wrong whole-value cases still refuse. Actual PNG/XML
and fresh runtime review remain required; source tests alone prove no client
interop or canonical PASS.

SDK35/APK/helper/images/Lavapipe/containerCPU8/guest4CPU4096MiB/memswap8192MiB/
PID512/requested2048M/source6GiB floor remain unchanged. Fresh coordinator
measured>=8GiB on the actual output filesystem is required before any grant,
as a conservative margin rather than a measured minimum or guarantee.
Identical guard29/fixture27/consumer14 retain only their explicitly pinned prior
pure scopes; no reexecution or transfer to changed UI/cleanup/ordinary behavior.

Same first JS-to-Rust incoming rsrelay cell only. Canonical E02 remains PARTIAL22
and blockers remain open. No producer/matrix extension or gate interpretation
is introduced; canonical coverage reconciliation is a separate architect task.
No new kind/NIP, production SDK, deployment, production data or automatic merge.
Historical instructions below grant no v3 activation authority.

---

# Ordinary-client first-slice prototype

This experimental source prepares one real **JS-to-Rust / incoming / rs-relay** business-envelope observation in pinned Amethyst. It is not a complete E02 implementation or canonical result. The full agreed eight-row coverage remains required separately; one qualified row remains PARTIAL with seven missing rows.

## Components and ownership

- `clipboard-helper/` and `build_helper.py` prepare the separately reviewed disposable foreground helper. It has no INTERNET permission or network/service/provider path. Its exact built APK is a later runtime input; no Amethyst patch/rebuild is required.
- `android_driver.py` exposes only `run(runtime)` and performs no import-time work, direct subprocesses or Docker/ADB escape hatch. `ui-plan.json` freezes its one-cell UI route and finite limits.
- The separately owned supervisor/lease sources supply current-source validation, actual original nonrenewable UTC/BOOTTIME/MONOTONIC lease checks, finite command custody, isolated runtime activation and exact-owned cleanup. The independently authored fixture supplies the actual live app-subscription gate, received EVENT/wire bytes and independent JS/Rust validation requests/results.
- The evidence consumer is separately owned under `../e02_ordinary_control_evidence_v1/`; it cannot manufacture runtime authenticity or promote canonical E02.

No source/build plan, runtime template or documentation file grants activation authority. All actual runtime/configuration/source/QA/security/release joins must be completed first.

## Driver runtime API

The fixed host driver requires:

```
runtime.plan                 # exact materialized run configuration
runtime.plan_pin             # descriptor used as runConfig
runtime.release_pin          # descriptor used as runRelease
runtime.out                  # fresh host run output root
runtime.check()
runtime.sleep(seconds)
runtime.adb(tokens, timeout=20) -> raw bytes
runtime.snapshot(unique_name) -> {png: descriptor, xml: descriptor}
runtime.fixture(prepare|status|publish) -> raw JSON wrapper bytes
runtime.put_bytes(relative_path, raw) -> exclusive immutable descriptor
runtime.put_json(relative_path, integer-only JSON) -> exclusive immutable descriptor
```

`adb` receives tokens after the supervisor's fixed `-s emulator-5554`. The driver types only the public scalar2 nsec and the declared local relay URL. All taps/long presses derive from current hierarchy control bounds; recognized screen/label ambiguity refuses. Bounded scrolling requires an actual known screen anchor and exactly one current scrollable region. There is no guessed-coordinate or unknown-screen fallback.

The fixture wrapper is `{schema,operation,caseId,ok,result}`. Prepared original/expected files exist before login/publication. Every `/session/fixtures/...` descriptor maps only to the same bytes at `runtime.out/session/fixtures/...`; hashes are verified. The driver preserves the original producer transport record and emits a separate path-rebound host transport record without changing any frame/wire/request/result bytes.

## Actual clipboard capture route

The driver records the real conversation, opens the helper with the case ID only, presses **Clear clipboard**, then returns to the same note. It long-presses actual message bounds and selects pinned Amethyst's **More Options → Copy raw JSON**. It then foregrounds the helper and explicitly presses **Capture clipboard** while focused.

The helper accepts one text/plain `ClipData.Item.getText()` value, refuses URI/Intent/coercion, empty/stale sentinel, malformed Unicode and more than64KiB. It neither trims nor normalizes the UTF8 output. Exclusive private files are read back only with `adb exec-out run-as org.nbdp.clipboard.capture cat files/captures/<fixed-case-id>...`. No Amethyst private file, host clipboard, public composer or expected-JSON intent is used.

The driver verifies the helper's raw byte count/hash and exact complete typed six-field inner rumor against the source-bound expected subject. Pretty JSON whitespace may differ. The unsigned Amethyst export may additionally contain strictly `sig:""`; that representation field is excluded only from semantic comparison, while captured bytes remain unchanged. Nonempty/null/nonstring signatures or other extra fields refuse. The driver retains the selected-note PNG/XML, action-sheet transitions, actual capture receipt, original transport proof and own-account public-profile GUI for independent decoding. Guest elapsed and host monotonic clocks are never compared as absolute timestamps. PNG/XML are sequential captures, not an atomic observation.

## Existing findings and activation boundary

The old HIGH finding allowed GUI actions after an expired session. This prototype must use the new reviewed guard before every UI/fixture/container action and after all waits/resumption. No watchdog can promise cleanup while the host cannot execute. The old v7 shared-clock-lock startup failure is preserved; its underlying cause remains unproven. Neither issue is cured by deleting checks or reusing a consumed old grant.

No unsupported `-no-clipboard` flag is assumed. Exact emulator help, headless/no-desktop-socket environment, private network and actual listeners must support the eventual host-clipboard/egress claim. Headless mode alone is insufficient proof.

Before an actual run, independently review all source/configuration/inputs, the exact built helper identity, required lease refusal tests and bounded exact-owned cleanup. Retain every failure and partial capture. Actual observation acceptance still requires independent QA/security review. Ordinary JSON display/export does not establish NBDP business understanding, invoice approval, payment or an SDK capability.
