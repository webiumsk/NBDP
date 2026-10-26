# Android control preparation preflight

The standalone [readiness probe](../../../../experiments/tools/check-android-control-readiness.py) emits one JSON object and starts no Android or NBDP experiment. Review the exact source before its first invocation:

```sh
python3 -I -B experiments/tools/check-android-control-readiness.py
```

Run it from the repository checkout. It accepts no arguments and writes only stdout. The coordinator may separately retain stdout, stderr, the actual exit and tool execution context. This source preparation performed AST parsing/in-memory compilation only; the probe has not yet been executed by its author.

| Exit | JSON status | Meaning |
| --- | --- | --- |
| 0 | `READY_FOR_REVIEWED_PREPARATION` | All declared environment checks passed in this execution context. Exact UI/export harness review and actual controls are still required. |
| 2 | `PREPARATION_BLOCKED` | At least one required input, resource, permission or bounded local Docker query failed, or unexpected arguments were provided. Preserve the observations; do not infer experiment failure or host absence from a managed-only failure. |

## Checks and limits

- Stream-hash the existing 165860063-byte APK against SHA256 `5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5`, and verify the exact retained build-manifest bytes and source/package/version record. Build exit0 in that record establishes artifact provenance only.
- Verify the retained SDK metadata pins and required cached emulator, ADB and Android36 x86_64 image files. Presence/metadata checks do not constitute full SDK provenance or runtime qualification.
- Require at least **6GiB persistent free space** at the workspace and `/tmp`, and **12GiB MemAvailable**. These are retained reviewed boot-driver admission guards, not an experimentally established minimum, reserved resources or measured peak usage. Shared filesystem values are reported with device identities rather than added together.
- Open and immediately close `/dev/kvm` read/write; verify a character device and issue no ioctl. The probe changes no device permissions and starts no VM.
- Query only the explicit local Docker socket with fixed shell-free argv and a12-second timeout. The command is `/usr/bin/docker --host unix:///var/run/docker.sock --config /tmp/nbdp-android-readiness-20261023/docker-readonly-no-config version --format '{{.Server.Version}}'`. The child receives a minimal environment, so inherited remote Docker contexts/endpoints are not selected. No Docker service, container, image import or network is started. The probe itself does not create a Docker configuration directory.

No `adb`, emulator, Java, Gradle, build, install, download, relay, guest or NBDP control command is executed. The previous direct ADB version failures caused by the read-only personal Android directory are not repaired through HOME/global configuration changes. No existing data is deleted.

## Execution scope and next gate

Every result is scoped to the current process namespace and permissions. A managed execution may not see KVM or access Docker even when the host supports both. A coordinator may use an already authorized supported scoped host execution after independent review and retain that result separately. The script neither escalates itself nor requests host configuration changes.

Even exit0 explicitly reports `controlExecuted=false` and `E02Promotion=false`. A fresh isolated input/egress plan, exact pinned client identity, bounded lifecycle/cleanup and a usable full UI plus raw-content/tag-export harness remain mandatory. Actual rendering/preservation observations and independent QA/security acceptance are required before assigning a canonical experiment result. This probe cannot unlock E04/E06, close an architectural blocker or authorize an SDK.
