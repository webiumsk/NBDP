# Android ordinary-client environment readiness — 2026-10-23

Status: **NOT READY for a new control run**. This is a bounded environment/artifact inspection, not an E02 experiment result. Full command outcomes, source descriptors and limits are in [android-environment.json](android-environment.json). No emulator, container, guest, installation, build or network experiment was launched by this task.

## Verified existing inputs

The exact Amethyst Android APK already exists at `/tmp/nbdp-e02-android-artifact/source/amethyst/build/outputs/apk/fdroid/debug/amethyst-fdroid-debug.apk`: **165860063 bytes**, SHA256 `5165a9f79326524c494108b8ab728fb173ac14fa16bf67ebbd86364c895e98b5`. Its current bytes match the retained source-linked build manifest for commit `e6f464a1179def75274512b3c5bab921de3bf3d8`. The recorded package is `com.vitorpamplona.amethyst.debug`, version `1.17.0-DEBUG`/462, minSdk26, targetSdk37, with x86_64 included. Today's check rehashed the APK; it did not repeat signing verification or rebuild the source.

Cached SDK files also exist at `/tmp/nbdp-e02-ingress-runtime/sdk`: platform-tools37.0.1, emulator37.2.12/build16428233, Android36 default/x86_64 image revision2/extension17. These version statements come from current `source.properties` metadata. JDK21.0.12.1 and Gradle9.8.0 are retained under the previous artifact lab. None is on the ordinary PATH. **No APK/tool download or rebuild is needed merely to prepare this existing pinned control.**

Two bounded direct `adb version` calls returned signal6: ADB attempted to create the read-only personal `~/.android` directory, including when `ANDROID_USER_HOME` pointed into the disposable task directory. Both failures are preserved in the machine record; no successful current ADB version output is claimed. Do not repair this by changing personal configuration. Use the already reviewed isolated container environment and capture its actual tool versions before the control.

## Current environment boundary

Managed probes cannot see `/dev/kvm`; Docker read-only `ps`/`images` return permission denied and read-only libvirt listing returns Operation not permitted. These are managed-session observations, **not proof that the host lacks KVM or Docker**. The coordinator subsequently performed a supported scoped read-only host probe, tool chunk `ea914b`/exit0, and reported successful read/write opening of host `/dev/kvm` plus accessible Docker29.9.0. That host observation must remain separately attributed to the coordinator. No user KVM/Docker permission change or repeat PO approval is required.

Host VMware state remains unknown from this child namespace. No existing VM was stopped and no personal Android device/profile or private application cache was inspected.

## Actual resource obstacle

The workspace and `/tmp` share one persistent filesystem. The final managed probe observed **179453952 bytes free** (approximately 171.1MiB); coordinator host observation was180051968 bytes. This is insufficient even to duplicate the old failed run's pre-UI Android state, which currently occupies383266816 allocated bytes. Its configured userdata virtual capacity grew to6GiB; virtual capacity is not measured physical use.

The retained independently reviewed boot-observation driver admits only with **6GiB persistent free space and12GiB MemAvailable**, and uses a10GiB `/state` tmpfs ceiling. The current disk misses that existing guard by **6262996992 bytes**. These are retained admission thresholds, not measurements proving the empirical minimum of a complete UI run. The previous boot probe did not retain peak `/state` usage, so claiming that2GiB would suffice is unsupported. No arbitrary8GiB threshold is introduced.

The smallest straightforward user action is to provide **at least6GiB total persistent free space** on this filesystem, or a separately scoped writable filesystem with equivalent headroom. Do not blindly delete retained experiment evidence. A smaller resource plan is possible only after separate technical review and actual peak/headroom measurement; it cannot silently weaken the existing guard.

## Reproducible next step

1. Recheck disk/RAM on the host and pin the retained exact Android image/tool/source manifests. Verify actual daemon access through the supported scoped execution mechanism. Do not infer access from a socket's existence.
2. Use a fresh disposable AVD/output directory, namespace-local ADB and isolated lab relays. Retain the cached APK/SDK read-only. Do not reuse populated old AVD state or consumed grants.
3. Before activation, independently review the exact synthetic input matrix, bounded runtime/cleanup, relay egress isolation and raw content/tag capture method. The old minimal-rs-v7 startup failed on a shared clock lock; it is not a ready-to-rerun grant.
4. Observe actual guest boot/package identity, install only the verified APK into that disposable guest, then execute the complete ordinary-client control matrix supplied by the researcher.
5. Preserve UI observations and exact relevant content/tag evidence, all skips/refusals/failures and cleanup. Obtain independent QA/security review before changing a canonical experiment result.

Acceptance requires actual complete ordinary-client evidence at the pinned client/source and declared inputs. A successful build, metadata match, guest boot or one Hello observation alone does not establish E02 PASS. E04/E06 and architectural blockers retain their existing gates.

## Historical records retained

The prior `/tmp/nbdp-e02-minimal-rs-v7/runs/c0c1175179794cf3ab1f41bba22a4f2a` has FINISHED/STOP and cleanup records. Its recorded Android image was `sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f`; current Docker image availability was not proven by this child. The prior startup record reports actualReady=false, UIExecuted=false and a shared-clock-lock refusal. A separate historical boot-only observation did capture guest boot properties, while expressly denying UI/interoperability/E02 promotion. These retained observations must not be converted into current control success.

The implementer owns only this report, its JSON companion and disposable probe logs. No canonical result, project state, roadmap, source, Git branch or approval classification was changed. Independent review remains required.
