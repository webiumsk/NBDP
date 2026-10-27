# Fixed Amethyst supervisor SOURCE2 — full network-ID binding

SOURCE1 stays unchanged and HOLD for build activation. SOURCE2 changes only its
versioned work directory, the network binding/qualification correction, and
corresponding DATA model definitions. No model, Docker/tool or build ran here.

Create now requires the root-released full64 network ID and substitutes that ID
for the original proposal's name-only `--network` value. Every owned-container
inspection requires `HostConfig.NetworkMode` to equal that exact released ID.
The endpoint map must contain exactly the fixed expected network name; foreign
or additional endpoints and any foreign/truncated nonempty NetworkID refuse.

The coordinator's actual **stopped, never-started** probe used the same pinned
image and a full network-ID create argument. It observed:

- `State.Status=created`, Runningfalse, Pid0 and zero StartedAt/FinishedAt.
- Initialized `ExitCode=0`, which supplies no execution-success evidence.
- Exact full network ID in HostConfig.NetworkMode.
- One endpoint keyed by the fixed network name, with empty NetworkID,
  EndpointID, address/gateway/MAC strings and zero address-prefix lengths.

Immutable exact copies of that raw inspect and original coordinator tool
receipts are pinned here. These are SOURCE evidence of prestart field shape,
not a build run or runtime attachment qualification. The original coordinator
records remain unchanged by this worker. Later probe-removal evidence is separate.

The missing-endpoint-ID exception matches only that observed **actual created
state**, including Pid0 and both zero timestamps. It is reported as full creation
configuration binding only; no runtime endpoint claim follows. This also permits
safe owned cleanup when a failed start leaves precisely that created state.
The policy does not depend on the controller merely having attempted a start.

Running/exited states require the actual nonempty endpoint NetworkID to match
the released full ID. Missing runtime IDs remain UNKNOWN/refuse. A successful
job additionally requires actual exited state, zero exit, no OOM/error, real
nonzero StartedAt and FinishedAt in order, natural attached completion and the
existing inner rebuilt-APK receipt. Created.ExitCode0 can never qualify. Timestamp
comparison preserves the recorded nanosecond fraction rather than truncating it.

The actual root-created bridge's observed owner/scope labels are required:
`nbdp.owner=e02-amethyst-rebuild-20261026` and
`nbdp.scope=isolated-build-bootstrap`. The full actual label map must also equal
the externally pinned release's map. SOURCE1's proposed role/run network labels
were not present in that real bridge; SOURCE2 derives this binding from the
actual source evidence instead of inventing fields. The container's fresh run
label/full CID/image/mount/user/capability/limit requirements remain unchanged.

All previous logging/time/resource/first-fault/cleanup restrictions remain:
64MiB CLI-capture files, 512MiB every inner job file, 1800+5s job, 2100s outer
including cleanup reserve, no controller host numeric-PID signals, fresh owned
writable roots and exact-CID cleanup with strict known-not-found proof. No host
home/credential/socket mounts, no retry or hostile atomic-closure claim.

Forty-six pure DATA model definitions retain the original28 families and add
source-derived full-ID, endpoint, created-state and actual-exit regressions.
They have not run. The actual probe regression reads its pinned DATA; fabricated
runtime/exit examples remain explicitly models, never tool observations.

Independent exact SOURCE2 QA/security and a separate model release precede any
control execution. Build remains NOT_READY pending accepted current acquired
inputs, exact source archive, final SOURCE/model reviews and fresh root release.
No runtime permission or canonical experiment/blocker change follows here.
