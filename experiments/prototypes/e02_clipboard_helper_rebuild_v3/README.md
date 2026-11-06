# Offline disposable clipboard helper — heap SOURCE2

This sibling preserves the exact original Java activity and Manifest and all
eight original compiler/signing CLI argument lists. SOURCE2 changes only the
wrapper heap admission policy and versioned source/output/plan paths. Original
SOURCE1, its accepted once-only13 DATA models and the actual wrapper observation
remain preserved. Their outcomes do not count as execution of this version.

Actual acquired d8 source sets `defaultMx="-Xmx2G"`; apksigner sets
`defaultMx="-Xmx1024M"`. With unchanged CLI, neither sees a leading `-J` option.
The explicit wrapper Java argv is therefore expected to override the environment
request under HotSpot option precedence: d82048MiB and apksigner1024MiB. This is
source-derived inference, not a measured JVM heap or peak-resource result.

The root-authorized routine resource adjustment adds2048MiB only for d8. Previous
512/1024 admissions remain; apksigner2048, unknown, noninteger and larger values
refuse. `validate_inputs` still checks exact actual source/tool/evidence pins and
calls the same pure wrapper-policy validator used by the proposed DATA models.
No `-J` flag or compiler/signing strategy is introduced. JAVA_TOOL_OPTIONS still
requests512MiB heap,256MiB metaspace,128MiB compressed-class space and128MiB code
cache, plus the private JVM home. The original180-second phase and60-second
command bounds remain. The parent must retain its proposed4GiB address-space
limit if compiling; this packet does not promise that the JVM or build fits.
An actual startup/resource/compile failure remains a failure.

Tools remain under `/tmp/nbdp-amethyst-rebuild-20261026/tools`: JDK21,
SDK build-tools36.0.0 and platforms/android-37.0/android.jar. The fresh private
output candidate is `/tmp/nbdp-e02-clipboard-helper-rebuild-20261027/build-r2`.
The new private random debug key implies a REBUILT APK identity. No historical
APK hash or runtime/client qualification transfers. Keystore bytes stay private;
only its descriptor and the public signing certificate/package/version reports
may be included in artifact evidence.

`helper-build-plan.template.json` remains NOT_READY. Its actual ten tool pins
are observations from the immutable wrapper report, not acquisition acceptance.
The toolAcceptance descriptor is absent. The only future accepted plan path is
`helper-build-plan-effective-r2.json`, currently absent. Root must first obtain
accepted complete acquisition DATA and independent exact SOURCE review, run and
review a separately released DATA scope, then bind and review an effective plan
and issue a separate bounded compile release. No SDK manager/license consent,
network operation, tool execution, import of the builder, key generation or
compilation was performed here.

Nineteen pure DATA model families are defined: the original13 preserved verbatim
plus six heap-policy families. They include a pinned actual-wrapper-report
2048/1024 positive, previous512/1024 admissions and unknown/larger/signer2048/tool
binding refusals. Zero models for this version have run; AST parsing alone is
recorded. These controls do not authenticate actual files or qualify a client.
