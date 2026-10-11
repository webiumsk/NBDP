# Public disposable fixtures

All private scalars and AES keys in this directory and generated result fixtures are **public, disposable, test-only**. Do not use them for production identities or documents. Data is invented; no real invoice/customer data is included.

`nip44.vectors.json` is copied unchanged from [nostr-tools cb8d22d4c906d99d8996693b37e4d85aa3d5f26e](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/nip44.vectors.json), distributed under the repository's [Unlicense](https://github.com/nbd-wtf/nostr-tools/blob/cb8d22d4c906d99d8996693b37e4d85aa3d5f26e/LICENSE). SHA-256: `eae34c1d4eff1b58b448627d3310e495f7f0722ca6668296e7c31e88edf18171`. This is the library's retained standard corpus; extended-length tests are separately defined against the pinned current NIP-44 revision.

Nostr identity fixtures are public secret scalars 1, 2, 3 (64-character lowercase hex). Official vector keys are also public. Random wrapper keys are disposable and never reused as user identities. Generated authenticated chains and AES-GCM vectors are saved with input/expected-output commitments so they can be independently replayed.
