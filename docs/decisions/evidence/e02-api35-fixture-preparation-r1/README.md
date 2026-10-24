# API35 fixture acquisition — first network failure preserved

The one authorized DATA-only attempt stopped with natural exit2 after
`URLError(gaierror(-2, 'Name or service not known'))`. No retry, escalation,
SDKManager, license acceptance, emulator/ADB, service or experiment occurred.
No HTTP response or TLS handshake was observed. `download.json` retains the
original `tlsVerified:true` configuration field: it describes the verifying SSL
context requested by the downloader, **not a successfully verified connection**.
The separate outcome addendum makes this distinction explicit.

The exact official API35 metadata and1114byte package fragment were rehashed
against the supplied pins. Before and after the failed request, the cached
emulator/platform-tools tree was fully hashed with file/directory metadata.
Both snapshots are equal:398 emulator and12 platform-tools regular files,
903,291,301 and22,198,160bytes respectively; no symlinks/specials. The original
SDK was not modified. The request failed before the first ZIP file was opened;
zero archive bytes exist. Tool copying, ZIP validation and extraction never
began. The new fixture contains only an empty `sdk` directory. There is no
qualified SDK inventory, image properties/fingerprint or archive SHA256.
Runtime compatibility remains UNKNOWN_NOT_EXECUTED.

The six-GiB reserve was retained:2,407 checks sampled a minimum11,198,066,688bytes
free, above6,442,450,944bytes. The failed attempt's final sample was
11,198,615,552bytes. These are sampled filesystem observations; other workers
share the filesystem, so they are not a reservation against concurrent writes.
The result extent was preallocated before acquisition so a space refusal could
preserve bounded failure evidence without allocating new blocks below the limit.
The script retained all output and did not delete or retry anything.

The referenced current official license text and existing accepted-license file
descriptor are retained. Raw UTF8 text SHA1 did not equal an existing acceptance
line; undocumented normalization was not guessed. Normalized license identity
remains UNKNOWN, and no acceptance/global setting was added or modified.

`acquire-fixture.py` preserves the exact finite proposed download/copy/extraction
procedure, but only the preflight/source snapshot and single unsuccessful network
request actually executed. Its unexecuted CRC/local-header/copy/extract paths
are not evidence of a complete fixture. No source profile, source SDK, shared
document or Git mutation occurred. Independent QA/security may review this
failure evidence; any new acquisition attempt requires the coordinator to select
an authorized network-capable path in a separately recorded task. This is a
preparation failure, not an E02 ordinary-client failure or architectural result.
