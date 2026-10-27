# Fixed Amethyst build supervisor — SOURCE preparation

This is a single-build controller for the existing frozen Amethyst build plan
and `build_inside.py`. It does not change those sources, the app, dependencies,
SDK licenses, protocol, experiment gates or production systems. No imports,
Docker/tool commands, models, acquired programs or build ran during preparation.
Runtime remains NOT_READY pending exact acquired inputs and fresh root release.

The proposed Docker create command preserves the fixed image/user/environment,
read-only source archive/preparation/JDK/SDK mounts and fresh isolated writable
work/cache/output mounts. It adds only explicit execution/custody restrictions:

- A fresh root run label and private CID file, compared against create stdout.
- A whole-job internal GNU timeout of 1800 seconds with a 5-second kill grace.
- Docker log driver `none`; attached CLI stdout/stderr are private files, each
  bounded by child `RLIMIT_FSIZE` at 64 MiB. Reaching a capture ceiling refuses
  qualification even if the CLI reports zero.
- Root-authorized container `--ulimit fsize=536870912:536870912`, independently
  checked through `HostConfig.Ulimits`. This limits **every inner job file**,
  including the separately redirected Gradle logs, cache objects and APKs, to
  512 MiB. A legitimate larger build file may fail and remains a real failure.
  It is not a 64 MiB limit on inner logs or an aggregate disk quota.

The hard job settings remain 6 GiB memory/swap, 4 CPU, pids512, user1000:1000,
all capabilities dropped, no-new-privileges, read-only root and private tmpfs.
The original source checkout is not mounted; its exact Git archive is read-only.
No host home, credentials, personal Android state or Docker socket is mounted.
The host Docker CLI receives an empty private Docker configuration directory.

Before any start, the controller requires a pinned root release, its exact own
source/plan subject, the original preparation subject and all source pins, two
supervisor-source review references and independently accepted acquisition /
source-archive / build-method prerequisite references. Full acquired tool trees
are rehashed against their accepted extraction inventories. The source archive
must bind the exact approved commit/tree and original clean-source receipt.
Writable build roots must be absent and are created fresh. The build needs at
least 12 GiB sampled free disk; that is admission, not peak-usage measurement.

The dedicated root-created bridge must have its exact full network ID, owner/
role/run labels and no existing members. The controller never creates/removes
networks. A pre-existing or uncertain named container is never touched.

Create must yield one unambiguous full64 CID from its CID file/stdout. The actual
CID, image, name, run labels, full mount set, user, command, internal timeout,
network, capabilities, tmpfs, ulimits and resource configuration are inspected
before start and again before every stop, kill or remove. These Docker mutations
use full CIDs only. No controller code sends host numeric-PID signals. Standard
GNU timeout owns its CLI child lifecycle; this is not E06 hostile process-custody
or atomic-closure evidence.

Finite waits are 30 seconds per ordinary metadata command, up to 1845 seconds for
the attached build, and separately bounded stop/kill/remove operations. Overall
controller time is 2100 seconds, reserving its last120 seconds for cleanup.
No build starts without a complete original attached-job budget. A fresh root
release may last at most2400 seconds and must cover the entire controller scope.
An independent outer timeout2110+5 is proposed as a final foreground bound.

Every CLI request/response, wrapper argv, return status, private stream pins and
classification is retained. The last successful owned inspect after start also
retains actual job exit/OOM state when available. Failure preserves the first
fault, partial logs and build outputs. Cleanup attempts one stop and, if needed,
one kill, with fresh ownership inspection before each, then removes only a
verified stopped owned container. No build retry occurs.

Only exit1 plus an exact known-full-CID not-found error and empty/`[]` stdout can
prove removal. Daemon/permission/mixed/foreign/truncated responses remain UNKNOWN.
If fresh inspection/capture becomes unavailable, cleanup cannot be falsely
qualified; the internal job timeout remains the independent finite job limit.
No previous unknown container or foreign destination is removed.

A successful controller result is still `PENDING_INDEPENDENT_DATA_REVIEW` and
does not establish APK reproducibility, client interoperability, E02 PASS, runtime
admission, a production SDK or any architectural blocker closure.

Twenty-eight pure DATA model definitions cover identity/settings, exact absence,
capture classification and inspect-before-mutation/first-fault wiring. They have
not run and do not establish Docker behavior. Independent SOURCE QA/security and
a separate bounded root release precede model execution. Build activation also
needs accepted actual acquisition/source artifacts and a separate fresh release.

Proposed model command after release:

```text
/home/peterhorvath/.miniforge3/bin/python3.13 -I -B /tmp/nbdp-amethyst-build-supervisor-20261026/test_supervisor_models.py
```

Proposed build command after every prerequisite and root release:

```text
timeout --signal=TERM --kill-after=5s 2110s /home/peterhorvath/.miniforge3/bin/python3.13 -I -B /tmp/nbdp-amethyst-build-supervisor-20261026/supervise_build.py --release FRESH_ROOT_RELEASE_JSON --release-sha EXACT_ROOT_RELEASE_SHA256
```

The JSON release's authenticity comes from the externally pinned actual root
invocation and independent review origins. This parser checks exact references;
operator-authored JSON alone is not portable attestation or independent approval.
