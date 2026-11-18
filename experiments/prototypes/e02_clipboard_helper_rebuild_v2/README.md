# Offline disposable clipboard helper rebuild — SOURCE only

The Java activity and Manifest are exact copies of the original helper. The
eight javac/d8/aapt2/zipalign/keytool/apksigner command phases and flags remain
unchanged apart from explicit new source/tool/output paths. Original files are
untouched. This packet neither compiles nor activates the helper.

New acquired inputs come from the separately reviewed Amethyst tool acquisition:
JDK under `/tmp/nbdp-amethyst-rebuild-20261026/tools/jdk`, build-tools36.0.0 and
`platforms/android-37.0/android.jar`. A new private output/user/debug-key root is
`/tmp/nbdp-e02-clipboard-helper-rebuild-20261027/build-r1`. Every output must be
fresh. The random debug key implies a **REBUILT new APK identity**; historical
APK hash `a680e5...` never transfers.

`helper-build-plan.template.json` is deliberately NOT_READY and cannot be passed
as the executable plan. Actual tool hashes/accepted acquisition evidence and
wrapper heap-source observations are unresolved. The only future accepted CLI
plan path is `helper-build-plan-effective-r1.json`; root must materialize it with
exact actual source/tool/evidence pins and obtain independent review first.

The original180-second phase and60-second command deadlines remain. JAVA_TOOL_OPTIONS
explicitly configures heap512MiB, metaspace256MiB, compressed-class-space128MiB and
code-cache128MiB, plus an isolated JVM `user.home`. The subprocess environment is
closed, with private TMPDIR and no host Java/Android/home settings. No additional
compiler, D8 or signing options are introduced.

**Effective heap remains a prerequisite.** Acquired d8/apksigner wrapper command
lines can override JAVA_TOOL_OPTIONS. No unverified `-J` spelling or heap override
is invented. Before an effective plan may run, source inspection must pin both
actual wrapper files and explicitly record their source-derived effective heap
(512MiB or the root-accepted1024MiB) with unchanged flags. Larger/unknown defaults
require a separately reviewed versioned resource adjustment. This is source
evidence, not a runtime heap/peak measurement or a promise that4GiB AS succeeds.
Root may use an external4GiB address-space bound; no limit increase is inferred.

Like the original builder, listed launchers/jars/android.jar and all source/plan
pins are rechecked before and after commands. The complete acquired JDK/SDK tree
and source acceptance are separately reviewed root prerequisites; this program
does not authenticate a portable complete dynamic-link/runtime environment.

The resulting public artifact report retains APK bytes/hash, public signing
certificate report and actual package/version badging. The private debug keystore
is mode0600 and remains only under the private temporary build root; only its
descriptor is reported. Never archive/publish/export the keystore bytes. No real
keys or user data are used. No network is required by this build method; it makes
no network-isolation attestation and performs no SDK-manager/license-consent step.

Thirteen proposed pure plan/refusal/command-source models are defined, not run.
One compares all eight actual original command AST lists against the new command
plan using a closed literal/path evaluator, without importing/executing the old
builder. Positive DATA shape is not real tool authentication or compilation.

Independent exact SOURCE review, a separate bounded model release, actual tool
acquisition/heap evidence and reviewed effective plan precede compilation. APK
build success would remain artifact-only and grant no Android/client rows or
canonical E02 promotion.
