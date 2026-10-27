# Exact SDK434 restoration — SOURCE preparation

Restore only the original 434 public SDK files from three fixed Google archives.
The original index remains immutable: SHA256
`5c996f67fd8aba0ea618adc7f7f9e6a2c27c641cc95910deb07bdfa8a10562a8`.
The result must match every original path, size, SHA256 and file mode, plus the
original aggregate `ca45354d996965c19b5d9c1149b94ad747d21877e228aa391acbe0081456435f`.

This task has prepared source and parsed its AST only. No downloader, extractor,
SDK tool, license consent, emulator, process/service or protocol experiment ran.
Independent exact-source QA/security and a separate coordinator release must
precede any acquisition. Creating these files does not grant execution.

`plan.json` explicitly maps 398 emulator, 12 platform-tools and 24 system-image
archive members. The source reads the pinned original index and checks all 434
selected rows against it. Archive URLs, lengths and official SHA1 values came
from the coordinator's primary metadata research. The system image also has a
prior exact archive SHA256. Emulator/platform-tools archive SHA256 values remain
unknown until actual acquisition; every extracted file has a pinned SHA256.

The downloader uses verified TLS, exact HTTPS URLs, HTTP200 and Content-Length,
identity encoding, no proxies, authentication, redirects, retry or resume.
Network limits are 15 seconds per socket operation and 300 seconds per archive.
An alarm bounds normal work to 1170 seconds and reserves receipt handling within
the original 1200-second total deadline. A separate outer timeout of 1210 seconds
is proposed to bound interpreter/kernel failure; it does not renew work time.

The compressed inputs total 1,141,112,381 bytes; selected output totals
2,703,224,655 bytes. Admission and every streamed write sample available disk
space against **8 GiB reserve + all remaining planned archive/output bytes +
64 MiB filesystem/receipt margin**. These are sampled admission checks, not a
guarantee against concurrent unrelated disk writers or a measured usage peak.

Before extraction, the complete archive metadata and local headers/descriptors
are checked for exact selected file membership, canonical names, duplicate or
missing members, links/special types, encryption, size mismatches and overlapping
local extents/central-directory overlap. A bounded classic-ZIP footer check caps
the central directory at 4 MiB and 4096 members before Python parses it; multi-disk
and ZIP64 archives are refused. Directory entries must be selected-file
ancestors. Only regular members with stored/deflate compression are allowed.
Streaming extraction checks full length, ZIP CRC and exact original SHA256.
Only the pinned original public file modes (0644/0664/0755) are applied.

Fresh private attempt/stage directories use checked exclusive/no-follow file
creation. Complete inventory comparison occurs before Linux
`renameat2(RENAME_NOREPLACE)` atomically places the SDK at its original absent
path. Existing destinations cannot be overwritten. The same inode is checked
at the destination; the complete tree is re-read after placement. Directory
modes remain private restoration modes and are not represented as original
directory metadata, which the index does not supply.

Failures preserve partial archives and the stage. No failure cleanup deletes
or replaces a previous destination. Exact per-download/extraction receipts and
the first fault are retained; receipt failures are reported separately. A
post-placement failure leaves the new SDK unqualified for independent review.

Proposed command after source review and a separate root release:

```text
timeout --signal=TERM --kill-after=5s 1210s /home/peterhorvath/.miniforge3/bin/python3.13 -I -B /tmp/nbdp-sdk-restoration-20261026/restore_sdk.py --plan /tmp/nbdp-sdk-restoration-20261026/plan.json --plan-sha REVIEWED_PLAN_SHA256 --execute-reviewed-data-restoration
```

The runtime attempt directory must be fresh. No rerun, source pin refresh,
SDK-manager action, license consent or runtime admission follows from an exact
DATA restoration result. The canonical experiment statuses and architectural
blockers remain unchanged.
