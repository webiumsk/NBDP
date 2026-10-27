# Amethyst platform API37.0 — SOURCE2 correction only

SOURCE1 fetched/extracted the JDK and fetched the exact official platform archive.
Its platform extraction safely refused EXPECTED_PLATFORM_API before placement:
actual343-byte source.properties encodes stable API37.0, revision2/version17,
extension22/baseSDKtrue, preview0 and empty code/beta fields. The original
failure receipt, old stage, source bytes and helper/controller/source archive
remain untouched. This is a reader-format defect, not evidence of a bad archive.

SOURCE2 accepts only canonical decimal major.minor37.0; it never coerces through
float/int; it rejects36/37.1/37/37.00, preview/codename/beta and unknown revisions.
Exact stable package fields are validated. Platform destination remains precisely
sdk/platforms/android-37.0; no android-37 alias or byte edit is provided.

A new .stage-platform-r2 and platform-extraction-r2.json/failure receipt preserve
old evidence. The cached platform archive is reused read-only with the original
size/SHA1 and before/after SHA256 checks. No second JDK/platform fetch is allowed.
CLI scope permits only corrected platform extract and the still-unrun build-tools/
NDK fetch/extract pairs. Root's new grant must preserve this sequence and stop on
first failure; no root grant is created by this packet.

All old policy helper functions and the original20 model definitions remain
unchanged except scoped extract/main edits and the added property parser.24 new
parser definitions bind the exact observed343B/SHAfa890... fixture; wrong major,
minor, preview, codename, revision and unknown numeric/text formats refuse.
Only AST/source comparisons ran. No models, imports, downloads, archives, tools
or build ran here. Same-subject independent SOURCE review and separate bounded
model/root release precede any execution. Existing bounds/checksums/URLs remain.
