# One-use Amethyst build release materializer — SOURCE only

This is a narrow dispatch adapter for an already authorized single build. It does
not approve its own template, create missing prerequisites, change payloads or
waive freshness. The Root must first fill and independently review an entirely
concrete root-authorized-template.json, with executionAuthorized already true,
fixed runId/output, actual accepted source/controller/data pins and only the two
clock fields null. The external exact template SHA remains the caller's trust
input; actor strings and JSON themselves do not authenticate authorization.

The example remains NOT_READY and cannot execute. No actual authorized template,
dispatch marker, live grant, source dispatch or build is created by preparation.

Future interface, only after exact SOURCE/model/template/root approvals:

```text
/home/peterhorvath/.miniforge3/bin/python3.13 -I -B \
  /tmp/nbdp-amethyst-build-release-materializer-20261027/materialize.py \
  --template-sha EXACT_SHA256_OF_ROOT_REVIEWED_CONCRETE_TEMPLATE
```

The program reads only the fixed template filename and verifies its bytes/hash
before parsing that same retained buffer, all direct metadata pins, and fixed
Python/SOURCE2 supervisor/subject/plan pins. It refuses foreign targets/outputs,
unfilled data, old clocks, extra payload/budget/exec fields, and an existing job
or grant. No executable/path/argv is supplied by the template.

Immediately at actual tool dispatch, O_EXCL marker and live-grant creation make
this directory one-use. Failure consumes the marker rather than silently retry.
Only issuedAtUtcNs and notAfterUtcNs are filled with exact now/now+2400 seconds;
all other release fields remain structurally equal. Then execve replaces the
same process with the exact pinned isolated SOURCE2 supervisor, passing the new
live grant's explicit SHA. No shell, arbitrary exec, scheduler or background
service is involved. The Root-authorized payload survives approval delay; the
original supervisor's freshness checks still apply after dispatch.

No actual2100-second outer,1800-second job or120-second cleanup budget changes.
Slow/failing materialization or later checks may still refuse honestly; there
is no automatic second window or clock fallback. Metadata hashes and authority
correspondence are not portable/race-free provider attestations.

Fourteen model definitions cover time-only mutation, template/target/root/budget
refusal, exact-byte hash drift and O_EXCL one-use behavior in owned temporary
DATA files. They never import/execute the supervisor, Docker, tools or a real
grant. All remain unexecuted pending independent review and a bounded root grant.
