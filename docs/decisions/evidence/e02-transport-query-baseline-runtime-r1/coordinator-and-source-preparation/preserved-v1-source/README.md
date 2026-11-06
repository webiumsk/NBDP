# One-public-event relay query diagnostic — SOURCE only

The retained incoming failure published successfully and forwarded an actual APP
frame, then timed out on a separate ID query. Its whole window remains failed.
This minimal no-Android diagnostic publishes only the exact existing public
signed outer and its exact112-byte query to the pinned isolated rs-relay.

It reuses the actual unchanged lease/finite custody/owned CID cleanup helpers
and original10s network/3s handshake/55s command/1800s maximum lease limits.
Instrumented phases distinguish intent, send return/callback, raw message entry,
EOSE, synchronous guard latency and timeout/refusal without weakening guards.
No signer/NSEC/crypto/native validator/SDK/app or new profile is introduced.
Modeled background REQ traffic remains deferred beyond this single baseline.

Read CONTRACT.md and the preparation source/control plan. All20 fake-socket
model and10 source/custody definitions are prepared, not run. No Node import,
Docker, service, probe, lease, diagnostic or test was executed in preparation.
Source AST/hash comparison is not runtime qualification. Existing failures,
nonoperative metadata finding, canonical statuses, gates and blockers remain.
