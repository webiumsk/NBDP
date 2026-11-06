# E02 producer2 minimum evidence consumer — SOURCE revision3

Versioned DATA-only consumer bound to frozen producer2. See [CONTRACT.md](CONTRACT.md)
for exact schemas, observer stream/state/outcome joins, external origin trust and
readiness limits. The old consumer2/completion1/producer2 files remain unchanged.

This packet defines source and controls. No controls, real producer, Android,
network, relay, native validation or completion run is authorized by these files.
The current external runtime closure is NOT_READY: the historical Rust binary
and guard-bundle manifest are absent. No historical PASS transfers to runtime.

After exact SOURCE QA/security and a separate root release, planned DATA commands:

```text
python3.13 -I -B test_data_controls.py
python3.13 -I -B test_observer.py
```

Use the pinned actual interpreter, finite foreground captures,60s per command,
stdout<=1MiB/stderr<=256KiB retained streams and actual launch/completion receipts.
No silent fix/retry. The tests create only owned temporary synthetic DATA.

The old86 definitions are retained with versioned fixtures. Additional positives
cover complete integrated observer+publication graphs; a complete positive whole
consumer two-window graph remains missing and must be considered before activation.
Source syntax parsing is not test execution or runtime interoperability.

The evidence CLI still requires actual pinned manifest/origin and explicit read
roots. Successful DATA consistency remains supplemental, with stock E02 PARTIAL22,
all five architectural blockers and E04/E06/SDK gates unchanged. Completion2 is a
subsequent separately versioned task after this source freezes and is reviewed.
