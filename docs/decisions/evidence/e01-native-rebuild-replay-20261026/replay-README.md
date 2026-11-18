# Isolated E01 replay — SOURCE preparation only

No project module, Node, native binary, crypto test, relay, browser or Android
runtime was executed by this preparation. Only independent Python file-copy,
hashing, JSON and AST parsing operations ran. No project file was changed.

`plan.json` freezes an exact local copy plus explicit external tool pins.
`input-inventory.json` lists839 regular files,78 directories and2 preserved
in-tree symlinks. The883 copied node_modules entries are byte/mode/membership
and symlink-identical. `historical-comparison.json` proves equality of all19
source hashes recorded in the historical canonical E01 PASS140/no-skip report.
The original canonical run.mjs and E01 test.mjs are unmodified.

The new Rust binary snapshot is24100272 bytes with SHA256
`4ce385c5b1a713b35d58d787d94fbc298d139aa2e813daec15b2e99289cefd86`.
Its build acceptance remains an independent prerequisite. A runtime source
reply has not been observed here. Original RustClient requires the `source`
reply to equal the exact copied Rust main.rs before ordinary test calls.

The prospective launcher uses exact Node22.18.0, sanitized explicit environment,
the fresh copied experiments cwd and GNU timeout240s/TERM/2s kill grace.
Canonical writes stay under the copy's results/ and fixtures/generated/.
NBDP_CHROME points to pinned /usr/bin/false: the canonical metadata probe reports
unavailable and launches no browser. E01 contains no network operation; kernel
egress isolation is not established by this preparation. No descendant census,
portable attestation or successful cleanup is fabricated by GNU timeout.

Before execution, independent QA/security must accept this exact SOURCE plan,
the coordinator must accept the completed native build, and root must provide
a fresh externally hash-bound release. Run the launcher only through the plan's
exact pinned /usr/bin/python3.12 interpreter. The four positional arguments are
PLAN EXTERNAL_PLAN_SHA RELEASE EXTERNAL_RELEASE_SHA. No launch command has run.

The release is a closed JSON object with keys:
schema, executionAuthorized, plan, qaReview, securityReview,
nativeBuildAcceptance, issuedAtUtcMillis, notAfterUtcMillis, maximumTestSeconds.
Its schema is nbdp-e01-isolated-replay-root-release-v1; authorization is true;
plan equals the complete descriptor of the accepted plan; the three acceptance
fields are actual externally authenticated descriptor pins; maximumTestSeconds
is240. It must allow242 seconds from the actual launch and span at most600s.
The coordinator authenticates review actors/messages and build acceptance;
JSON/file hashes alone do not establish those facts.

Actual launch/completion tool responses, stderr, exit and outcome require root
collection and independent result review. Acceptance requires PASS140 with
no skips/failures and the exact new native hash. Historical results must remain
unchanged. Preparation is not a current E01 result or an Android release.
