# Companion progress publication: source preparation only

The coordinator assigned this directory for a small DATA-only companion to the prior publication packages. The fixed eight roots are listed in [selection-plan.json](selection-plan.json). Source preparation does not snapshot or qualify their active contents. The ordinary API35 controls/runtime may still be active, and the runtime directory may not yet exist.

**No archive has been built at this source-preparation checkpoint.** No source/runtime PASS, independent acceptance, ordinary-client matrix qualification, canonical experiment completion, gate change or blocker promotion follows from this packaging task. Prior P1/P2 archives, indexes, subjects and original evidence remain untouched.

## Activation requires a separate explicit freeze

The coordinator must first obtain `WRITES_STOPPED` from all owners of every selected root, including completion of the ordinary API35 runtime record. An active or absent root is not a frozen input. Independent source review of this builder is still required. Do not treat this README or an old experiment grant as execution authority.

Only after an explicit coordinator instruction to build the DATA archive, create the regular private `freeze-authorization.json` in this directory with exactly the keys and values described by `requiredFreeze` in the plan. Its `roots` value must be the exact ordered list, and `script`/`selectionPlan` must be whole-file descriptors with `path`, `bytes` and `sha256`. The required state is `CLOSED_INPUTS_WRITES_STOPPED`; both boolean attestations must be `true`. This is a coordinator attestation about closure, not independently measured proof or a new experiment grant.

Then, and only then, run:

```sh
python3 -I -B docs/decisions/evidence/transport-runtime-progress-publication-r3/build_archive.py --build-after-explicit-freeze
```

The builder refuses an absent freeze, changed source/plan pins, absent/empty roots, unsafe paths, links/specials, forbidden bodies and any existing output. Its initial directory membership must be exactly this README, the source, the plan and the later freeze manifest. It never overwrites outputs or writes outside this directory. A partial failed build must be retained and reviewed; do not silently delete its artifacts or reuse this revision.

## Intended outputs and limits

The builder emits one `completed-runtime-evidence.tar.gz`, a complete `archive-index.json`, `selection.json`, `archive-verification.json` and `normal-core-suggestion.json`. Every selected original regular file is copied under a sorted `repository/<repository-relative-path>` member. There are no silent member exclusions; a forbidden body fails the build for separate disposition. External SDK/APK/tool/archive/disk-image/key bodies and full external license texts are not authorized inputs. Existing metadata may name external paths and pins, but the builder never recursively follows or copies them.

Tar members are regular mode `0600`, uid/gid/mtime zero, empty owner names, USTAR without PAX or links. Gzip has an empty filename and zero timestamp. The complete index preserves each original absolute path, byte count, SHA-256 and actual mode/device/inode/uid/gid/link count/size/mtime/ctime. Originals are not chmodded, rewritten or removed. Raw `.diff`/`.patch` files remain byte-exact inside the archive; they are excluded from normal-tree suggestions.

Verification streams every member and checks exact bytes, metadata and sorted membership, rereads every original hash/stat, then re-enumerates all roots to detect membership drift. This verifies one serialized copy; it does not execute archived source, measure application behavior, establish independence or prove portable replay. File-copy counts are not distinct tests. Deterministic metadata and ordering do not assert byte equality across arbitrary Python/zlib implementations.

Suggested readable entrypoints and prototype source paths are suggestions only. The coordinator must inspect their links and decide normal-tree publication separately. No raw nested `actual-run` streams or `.diff`/`.patch` are proposed as ordinary files. No path is staged by this script. Independent QA/security must review the eventual archive and its exact index before the coordinator publishes it.

The final runtime README and publication subject are deliberately not fabricated here. They must describe the then-frozen actual ordinary API35 outcome and preserve the Android35 accepted failure/DATA-addendum scopes and the E06 R4 trace-analysis scope without transferring PASS or widening authority.
