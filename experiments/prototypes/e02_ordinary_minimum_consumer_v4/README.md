# E02 producer2 minimum evidence consumer — SOURCE revision4

Versioned DATA-only consumer bound to frozen producer2. See [CONTRACT.md](CONTRACT.md)
for exact schemas, observer stream/state/outcome joins, external origin trust and
readiness limits. The old consumer2/completion1/producer2 files remain unchanged.

This packet defines source and controls. No controls, real producer, Android,
network, relay, native validation or completion run is authorized by these files.
The current external runtime closure is NOT_READY: the historical Rust binary and SDK/APK inputs are absent. The coordinator
recovered the exact original guard bundle separately; this is DATA only. No historical PASS transfers to runtime.

After exact SOURCE QA/security and a separate root release, planned DATA commands:

```text
python3.13 -I -B test_data_controls.py
python3.13 -I -B test_observer.py
python3.13 -I -B test_source_bindings.py
python3.13 -I -B test_whole_window.py
```

Use the pinned actual interpreter, finite foreground captures,60s per command,
stdout<=1MiB/stderr<=256KiB retained streams and actual launch/completion receipts.
No silent fix/retry. The tests create only owned temporary synthetic DATA.

The old86 definitions are retained with versioned fixtures. Additional positives
cover complete integrated observer+publication graphs; complete per-window incoming/archive positives are also defined. The top-level
consume() immutable closure still lacks a positive model and needs independent
coverage assessment before activation.
Source syntax parsing is not test execution or runtime interoperability.

The evidence CLI still requires actual pinned manifest/origin and explicit read
roots. Successful DATA consistency remains supplemental, with stock E02 PARTIAL22,
all five architectural blockers and E04/E06/SDK gates unchanged. Completion2 is a
subsequent separately versioned task after this source freezes and is reviewed.

Consumer3's held SOURCE is preserved exactly. Revision4 corrects the actual proxy
guard literal, frozen runtime scope and send callback ordering; exact-source
regressions and valid callback-before-return coverage are prepared, never run.
Complete two-role synthetic window graphs are prepared in whole_window.py and
test_whole_window.py; these call the real unpatched window/Origin/Files evaluators.
The full consume() graph remains outside this synthetic scope because its genuine
immutable producer/control closure cannot be replaced with model operands.
