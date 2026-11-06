# Amethyst rebuilt-candidate preparation — SOURCE only

No tool/archive/build/model has been executed by this preparation. Sources are
pinned to commit e6f464a1179def75274512b3c5bab921de3bf3d8, tree
11a90777c85c71912594612f42d9807004834f67. The original checkout stays unchanged.

The acquisition plan pins JDK21.0.13+9 with published SHA256 and three Google
archives with their published SHA1. The primary repository XML reference uses
SHA256 1f0ca6d8b3109ab83afc3e409d53626659b8a233a908e477ac83017919339296,
426356 bytes. No replacement checksum is invented. New measured archive/tree
SHA256 pins are prospective DATA, not previously published checksum claims.

acquire.py proposes one fresh fetch and one extraction per artifact. HTTPS has
fixed public hosts/no credentials/cookies/environment proxies. Only the JDK may
redirect to GitHub/release-assets; Google redirects refuse. Partial files, first
failures and exact receipts remain; no resume/overwrite/retry. Archive paths,
member types, link graph, size/count/time bounds are checked before file writes.
Regular files/directories precede internal links; no link can be an archive
parent or escape its root. Complete original member metadata and normalized
file/directory/link inventories are retained. No acquired binary is activated.

JDK extraction max768MiB, platform512MiB, build-tools768MiB, NDK4GiB;
200000 members, per-file256MiB (NDK512MiB), link body4096B/16 hops. Fetch/extract
phases have proposed1800s each and require a finite outer root supervisor;
Python/DNS/parser wall checks are not a hard process-containment guarantee.
Fresh acquisition disk admission is8GiB. Metadata/ZIP central-directory parsing
uses stdlib under the separately required resource limit; no streaming-memory
attestation is claimed.

Platform destination is the exact primary-metadata package
platforms/android-37.0, with matching API properties and no alias invented for AGP. The source compiles
integer API37. Exact actual platform/AGP resolution remains to be observed; a
missing layout/package is a genuine failure, not permission to rewrite sources.

prepare_source.py proposes a source-only git archive with original HEAD/tree/
status before and after. build_inside.py proposes a fresh tracked-file workcopy
and original-file byte/mode comparison after Gradle, admitting new files only
under known Gradle module build/.gradle/.kotlin/.cxx roots. It never admits changes
to an original source file. Git configuration is absent from the container copy.

The proposed build uses exact image32bb6c..., user1000, capsnone/read-only root,
6GiB/4CPU/pids512, separate writable lab mounts and no host home/socket/secrets.
Both JDK user.home (mavenLocal) and GRADLE_USER_HOME are fresh isolated locations.
SDK/JDK are readonly. No SDK-manager/license-consent/global-config operation is
provided. Source Gradle/Kotlin heap defaults6g/8g are explicitly overridden to
reviewed3g/1536m under the hard6GiB cap; no compiler strategy/app feature changes.
Task stays :amethyst:assembleFdroidDebug -PdisableAbiSplits=true --no-daemon
--max-workers=3. Root must prepare a finite exact-CID/log-bound controller and
separate release before any build; build-plan.json is not an execution grant.

Outputs require natural successful build, unchanged original workcopy files,
source-linked new APK SHA256, debug package/badging and apksigner certificate
metadata plus a fresh private lab debug key. No key bytes are exported; no old
APK hash5165... or ecosystem compatibility is inherited. Actual client admission
will require a separately versioned producer/source/profile binding.

Twenty pure member/path/link/URL model definitions are prepared. They do not
exercise real archive parsing/extraction, network, JDK, SDK or Gradle. Independent
SOURCE reviews and a bounded root release precede model execution/acquisition.
