# API35 ordinary-client v2: source-bound identity visibility correction

SOURCE ONLY. This is a separate first-cell candidate with a fresh run/output
namespace. No v2 tests, Android actions, grant, lease or release have executed.
Evidence and proposed configuration: `docs/decisions/evidence/e02-ordinary-api35-preparation-r2/`.

The archived v1 run correctly tapped the current eye centre once. Its PNG and
XML changed Visibility/Hide Password to VisibilityOff/Show Password while the
empty field retained password=true. Exact pinned Amethyst KeyTextField source
uses unconditional Password content/keyboard semantics; the same showCharsKey
selects Show Password/VisibilityOff and VisualTransformation.None. This is a
source inspection plus empty-field runtime observation, not proof of typed NSEC.

v2 keeps closed package/ancestry/bounds/uniqueness checks and at most one known
Hide-to-Show action. It records/typed-checks accessibility password metadata,
requires the pinned source's shown eye state before and after input, and still
requires the exact entire public synthetic NSEC. Fresh post-input PNG/XML and
independent visual review remain mandatory. Missing/truncated/masked/wrong text,
foreign/duplicate/malformed eye, changed structural field identity and eye
reversion refuse. Existing keyboard-dismissal action is unchanged; visible full
identity must also survive that existing action. Bounds are revalidated on each
capture; a multiline/IME geometry reflow alone does not change field identity.

SDK35, pinned APK/helper/images, Lavapipe, containerCPU8/guest4CPU4096MiB,
Android8192MiB memory/swap/PID512, original1800s lease, closed ADB, fixture,
dialog recovery and cleanup remain fixed. Requested2048M/source6GiB floor do
not prove a2GB footprint; all seven retained ordinary hardware files normalized
to6g. Fresh coordinator-measured>=8GiB on the actual output filesystem is needed
before any ordinary grant as a conservative margin, not a minimum/guarantee.

47 UI and26 cleanup test definitions await independent SOURCE review and actual
execution. Byte-identical guard29/fixture27/consumer14 have separately scoped
prior actual accepted control evidence; they prove no v2 ordinary behavior.
E02PARTIAL22 and all architectural blockers remain unchanged. Seven other
producer cells and canonical integration are still missing. No production SDK,
new kind/NIP, payment behavior, deployment, production data or automatic merge.

Original v1 and historical R11 sources/results are preserved; instructions below
are historical context and grant no v2 activation authority.

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
