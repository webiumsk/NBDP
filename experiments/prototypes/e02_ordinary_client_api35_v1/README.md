# API35 ordinary-client source profile: preparation only

This directory is a SOURCE-only derivative of the original current R11 ordinary
first-cell sources. The authoritative proposed configuration and complete source
subject are in `docs/decisions/evidence/e02-ordinary-api35-preparation-r1/`.
No tests or Android/runtime actions have been executed for this profile, and no
release or lease has been issued. Independent SOURCE QA/security, actual current
controls and independent review of those controls precede any exact root release.

Only declared profile data changes: private run namespace, profile-specific
runtime/release/result schemas, accepted isolated API35 SDK/inventory, Android35
AVD target, Lavapipe renderer, Android container CPU8 and host affinity>=8.
Guest4CPU/4096MiB, container memory/swap8192MiB, PID512, original1800s lease,
original requested2048M data partition, pinned images/APKs and all safety logic
remain unchanged. Emulator37.2.12/platform-tools37.0.1 are the same copied410
inventory rows. The acquired API35 OS fixture is a whole environment change;
this profile is a semantic readiness candidate, not a causal comparison.

The strict current R11 driver remains byte-identical: require actual password
state and whole unmasked public synthetic NSEC, actual reopened TorOff PNG,
bounded known Settings/SystemUI Wait-only<=2 recovery, and refuse unknown or
Quickstep dialogs. No added never-ANR prerequisite and no broadened handling.
Only the first JS-to-Rust incoming rsrelay cell is prepared; all other seven
producer matrix cells and canonical integration remain undone. One successful
cell cannot promote E02 to PASS or close architectural blockers.

The original requested2048M partition and source6GiB free-disk floor remain
unchanged. Requested2048M does not prove a2GB footprint: all seven retained
ordinary hardware-qemu.ini files normalized disk.dataPartition.size to6g.
The separate API35 no-install emulator failed before guest/ADB: available
7326.61MB, required7372.80MB. This supports no guest OS failure inference.
Before any ordinary grant the coordinator requires fresh measured>=8GiB free
on the actual output filesystem. This is a conservative admission margin,
not a measured minimum or boot/readiness guarantee, and does not lower or
replace the source6GiB floor. Hash-bound prerequisite DATA:
`docs/decisions/evidence/e02-ordinary-api35-preparation-r1/coordinator-resource-prerequisite.json`
SHA256 `e836f9de2a50de2dc36c024cf1638de1aac681f0ab8f14052d13a4594c00abc8`.
Only two verified disposable old overlays are being reclaimed by the coordinator;
the reported~9.49GB target is not this author's fresh resource measurement.
Boot/client compatibility remain UNKNOWN. Preserve first failures; no cached
snapshot substitution, blanket healthy-OS gate or broadened dialog handling.

The copied helper build files are historical source provenance only; this
profile reuses the exact already pinned helper APK and does not authorize a new
helper build. The original runtime instructions below are historical context;
their original paths/schema names do not activate this API35 profile.

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
