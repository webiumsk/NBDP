# API35 ordinary-client v2: source-bound identity visibility correction

SOURCE ONLY. This is a separate first-cell candidate with a fresh run/output
namespace. No v2 tests, Android actions, grant, lease or release have executed.
Evidence and proposed configuration: `docs/decisions/evidence/e02-ordinary-api35-preparation-r2/`.

The archived v1 run correctly tapped the current eye centre once. Its PNG and
XML changed Visibility/Hide Password to VisibilityOff/Show Password while the
empty field retained password=true. Exact pinned Amethyst KeyTextField source
uses unconditional Password content/keyboard semantics; the same showCharsKey
selects Show Password/VisibilityOff and VisualTransformation.None. This is a
source inspection plus empty-field runtime observation, not proof of typed NSEC.

v2 keeps closed package/ancestry/bounds/uniqueness checks and at most one known
Hide-to-Show action. It records/typed-checks accessibility password metadata,
requires the pinned source's shown eye state before and after input, and still
requires the exact entire public synthetic NSEC. Fresh post-input PNG/XML and
independent visual review remain mandatory. Missing/truncated/masked/wrong text,
foreign/duplicate/malformed eye, changed structural field identity and eye
reversion refuse. Existing keyboard-dismissal action is unchanged; visible full
identity must also survive that existing action. Bounds are revalidated on each
capture; a multiline/IME geometry reflow alone does not change field identity.

SDK35, pinned APK/helper/images, Lavapipe, containerCPU8/guest4CPU4096MiB,
Android8192MiB memory/swap/PID512, original1800s lease, closed ADB, fixture,
dialog recovery and cleanup remain fixed. Requested2048M/source6GiB floor do
not prove a2GB footprint; all seven retained ordinary hardware files normalized
to6g. Fresh coordinator-measured>=8GiB on the actual output filesystem is needed
before any ordinary grant as a conservative margin, not a minimum/guarantee.

47 UI and26 cleanup test definitions await independent SOURCE review and actual
execution. Byte-identical guard29/fixture27/consumer14 have separately scoped
prior actual accepted control evidence; they prove no v2 ordinary behavior.
E02PARTIAL22 and all architectural blockers remain unchanged. Seven other
producer cells and canonical integration are still missing. No production SDK,
new kind/NIP, payment behavior, deployment, production data or automatic merge.

Original v1 and historical R11 sources/results are preserved; instructions below
are historical context and grant no v2 activation authority.

---


Evidence: `subject.json`, `diagnosis.json`, `source.diff`, `driver-full-typed-ast.diff`,
`historical-test-intent-ledger.json`, `unchanged-control-scope-link.json` and `execution-plan.json`.
