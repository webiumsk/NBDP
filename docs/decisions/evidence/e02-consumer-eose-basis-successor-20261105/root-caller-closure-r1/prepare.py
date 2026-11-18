"""Root-only finite declared-caller metadata preparation; never follow helper bodies."""
import hashlib
import json
import os
import stat
from pathlib import Path

BASE = Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence')
ROOT = BASE / 'e02-consumer-eose-basis-successor-20261105'
OUT = ROOT / 'root-caller-closure-r1'
REGISTRY = BASE / 'e02-completion-current266-source-20261105/source1/wrapper/selector-registry.json'
READS = {}

def need(value, message):
    if not value:
        raise ValueError(message)

def descriptor(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, 'DUPLICATE_KEY')
        result[key] = value
    return result

def read(path, expected=None):
    path = Path(path)
    need(path.is_absolute() and str(path) == os.path.normpath(str(path)), 'EXPLICIT_ABSOLUTE_METADATA')
    need('/probe-root-custody-actual/' not in str(path) and '/producer4-helper-probe-actual-r1/' not in str(path), 'NO_OPERATIONAL_HELPER_BODY')
    for parent in (path, *path.parents):
        need(not parent.is_symlink(), 'NO_METADATA_ALIAS')
    first = path.lstat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid,
                          s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    need(stat.S_ISREG(first.st_mode) and first.st_size <= 16777216, 'BOUNDED_REGULAR_METADATA')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(identity(os.fstat(fd)) == identity(first), 'OPEN_IDENTITY')
        blocks = []
        count = 0
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            count += len(block)
            need(count <= first.st_size, 'READ_BOUND')
            blocks.append(block)
        raw = b''.join(blocks)
        need(identity(os.fstat(fd)) == identity(first), 'HANDLE_DRIFT')
    finally:
        os.close(fd)
    need(identity(first) == identity(path.lstat()) and len(raw) == first.st_size, 'METADATA_DRIFT')
    pin = descriptor(path, raw)
    need(expected is None or pin == expected, 'EXACT_PIN')
    READS[str(path)] = pin
    return pin, json.loads(raw, object_pairs_hook=pairs)

def put(path, value):
    raw = (json.dumps(value, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(raw) == len(raw), 'COMPLETE_WRITE')
    return descriptor(path, raw)

def select(value, pointer):
    need(type(pointer) is str and pointer.startswith('/'), 'EXPLICIT_POINTER')
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if type(value) is list else value[token]
    return value

def actors(value):
    result = value if type(value) is list else [value]
    need(all(type(x) is str and (x == '/root' or x.startswith('/root/')) for x in result), 'TYPED_ACTOR_VALUES')
    return set(result)

def main():
    authority_pin, authority = read(ROOT / 'root-coupled-actor-authority.json')
    need(authority_pin['sha256'] == 'f80baccad749289f022e45784c288548bece4ad72c527f86e9e1da2e4f54f16d', 'FROZEN_75_AUTHORITY')
    allowed = set(authority['participants'])
    registry_pin, registry = read(REGISTRY)
    need(registry_pin['sha256'] == '6bafb1a3cd067bbfe6c3b7be8f56254204a400738901df57005f36497797661d', 'FROZEN_LEGACY_REGISTRY')
    nodes = registry['legacyActorNodes']
    need(len(nodes) == 63 and len(registry['requiredFailedRuns']) == 14, 'FINITE_63_NODE_14_RUN_PREDECESSOR')
    values = {}
    local = {}
    proofs = []
    review_only = []
    for path, rule in nodes.items():
        need(rule['pin']['path'] == path, 'NODE_KEY_PIN')
        pin, value = read(path, rule['pin'])
        need(sorted(value) == sorted(rule['keys']) and value.get('schema') == rule['schema'], 'CLOSED_LEGACY_SCHEMA')
        values[path] = value
        local[path] = set()
        for pointer in rule['actors']:
            selected = select(value, pointer)
            selected_actors = actors(selected)
            record = dict(subject=pin, selector=pointer, actors=sorted(selected_actors))
            if pointer == '/conservativeReviewerExclusions':
                record['meaning'] = 'WRAPPER_CONSERVATIVE_REVIEW_EXCLUSIONS_NOT_CALLER_CREATORS'
                review_only.append(record)
                continue
            need(selected_actors <= allowed, 'HISTORICAL_CALLER_OUTSIDE_FIXED_75')
            local[path].update(selected_actors)
            proofs.append(record)
        for edge in rule['actorEdges']:
            need(select(value, edge['selector']) == edge['pin'], 'EXACT_FINITE_ACTOR_EDGE')
            need(edge['pin']['path'] in nodes and nodes[edge['pin']['path']]['pin'] == edge['pin'], 'EDGE_STAYS_IN_DECLARED_63')
    def reachable(start_paths):
        pending = list(start_paths)
        seen = set()
        result = set()
        while pending:
            path = pending.pop()
            if path in seen:
                continue
            need(path in nodes, 'EXPLICIT_LEGACY_NODE_REQUIRED')
            seen.add(path)
            result.update(local[path])
            pending.extend(edge['pin']['path'] for edge in nodes[path]['actorEdges'])
        return sorted(result), [nodes[path]['pin'] for path in sorted(seen)]
    declarations = []
    legacy_actors = sorted(set().union(*local.values()))
    historical = put(OUT / 'historical-declared-callers.json', dict(schema='e02-root-historical-declared-caller-attestation-v1', actor='/root', registry=registry_pin, finiteNodes=[nodes[p]['pin'] for p in sorted(nodes)], selectedFieldProofs=proofs, legacyActors=legacy_actors, reviewOnlySelectors=review_only, completeness='DECLARED_ACTORS_ONLY_NOT_UNRECORDED_CODE_CONTRIBUTORS', helperBodyReads=0, executionAuthorized=False))
    declarations.append(dict(role='legacy', subject=historical, selector='/legacyActors', actors=legacy_actors))
    for run_id in registry['requiredFailedRuns']:
        rule = registry['failedRunAuthorities'][run_id]
        outcome_pins = []
        start_paths = []
        for expected in rule['outcomes']:
            pin, outcome = read(expected['path'], expected)
            need(outcome.get('runId') == run_id, 'EXACT_HISTORICAL_FAILED_RUN_ID')
            outcome_pins.append(pin)
            if pin['path'] in nodes:
                start_paths.append(pin['path'])
        source_pin, _ = read(rule['sourceSubject']['path'], rule['sourceSubject'])
        if source_pin['path'] in nodes:
            start_paths.append(source_pin['path'])
        need(start_paths, 'KNOWN_FINITE_ACTOR_ROOTS_FOR_EACH_ATTEMPT')
        run_actors, used_nodes = reachable(start_paths)
        need(run_actors and set(run_actors) <= allowed, 'NONEMPTY_KNOWN_FAILED_ATTEMPT_ACTORS')
        pin = put(OUT / ('historical-attempt-' + run_id + '.json'), dict(schema='e02-root-historical-attempt-declared-caller-attestation-v1', actor='/root', runId=run_id, originalOutcomeAuthorities=outcome_pins, originalSourceSubject=source_pin, registry=registry_pin, actorEvidenceNodes=used_nodes, actors=run_actors, meaning='Finite declared Source/release caller union; not invented original authors/operators fields.', executionAuthorized=False))
        declarations.append(dict(role='attempt', subject=pin, selector='/actors', actors=run_actors))
    latest = BASE / 'e02-ordinary-current266-concrete-preparation-20261105/root-r1/incoming-failed-attempt.json'
    latest_pin, latest_value = read(latest)
    need(latest_pin['sha256'] == '3912722df63599781a8b91a70c8fe3e80b44a84168f9372e1e9a2f1c4060c4d9' and latest_value['windowSubject'] is None, 'FIFTEENTH_FAILED_ONLY_ATTEMPT')
    for key in ('authors', 'operators'):
        selected = sorted(actors(latest_value[key]))
        need(set(selected) <= allowed, 'LATEST_ATTEMPT_ACTORS_FIXED')
        declarations.append(dict(role='attempt', subject=latest_pin, selector='/' + key, actors=selected))
    for role, relative in [('candidate', 'e02-ordinary-minimum-runtime-r1/coordinator-preparation/candidate.json'), ('sourceControls', 'e02-minimum-runtime-preparation-r1/source-controls-subject.json')]:
        pin, value = read(BASE / relative)
        for key in ('authors', 'operators'):
            selected = sorted(actors(value[key]))
            need(set(selected) <= allowed, 'EXISTING_CALLER_ACTORS_FIXED')
            declarations.append(dict(role=role, subject=pin, selector='/' + key, actors=selected))
    planning = dict(schema='e02-root-future-consumer-caller-source-policy-v1', actor='/root', actorAuthority=authority_pin, meaning='Source-bound allowed caller sets, not genuine future artifacts, identities, clocks or execution grants.', futureCandidate=dict(allowedActors=sorted(allowed), operators=['/root']), futureHistory=dict(allowedActors=sorted(allowed), operators=['/root']), futureSourceControls=dict(allowedActors=sorted(allowed), operators=['/root']), futureWindows=dict(incoming=dict(allowedActors=sorted(allowed), operators=['/root']), archive=dict(allowedActors=sorted(allowed), operators=['/root'])), requirements=['Actual declarations must remain subsets of this fixed actor set and actual operators Root only.', 'Real history must retain all15 failures and actual legacy contexts; no failed-row donation.', 'Final21 binding, genuine windows/five exports and independent reviews remain required.'], executionAuthorized=False)
    planning_pin = put(OUT / 'future-caller-source-policy.json', planning)
    for role, pointer in [('candidate', '/futureCandidate/allowedActors'), ('history', '/futureHistory/allowedActors'), ('sourceControls', '/futureSourceControls/allowedActors'), ('futureWindow', '/futureWindows/incoming/allowedActors'), ('futureWindow', '/futureWindows/archive/allowedActors')]:
        declarations.append(dict(role=role, subject=planning_pin, selector=pointer, actors=sorted(allowed)))
    need(len({r['subject']['path'] for r in declarations if r['role'] == 'attempt'}) == 15, 'EXACT_FIFTEEN_DISTINCT_ATTEMPT_DECLARATIONS')
    closure = dict(schema='e02-helper-component-basis-caller-closure-input-v1', actor='/root', scope='SOURCE_MAPPING_CALLER_ACTOR_SUBSETS_ONLY', actorAuthority=authority_pin, executionAuthorized=False, declarations=declarations)
    closure_pin = put(OUT / 'caller-closure-input.json', closure)
    method_pin, _ = descriptor(Path(__file__), Path(__file__).read_bytes()), None
    evidence = put(OUT / 'preparation-evidence.json', dict(schema='e02-root-caller-closure-preparation-evidence-v1', actor='/root', method=method_pin, inputs=list(READS.values()), callerClosure=closure_pin, historicalRegistry=registry_pin, historicalDeclaredCallers=len(legacy_actors), fixedAllowedCallers=len(allowed), failedAttempts=15, existingLegacyNodes=63, helperBodyReads=0, actualFutureArtifactsIssued=False, executionAuthorized=False))
    print(json.dumps(dict(callerClosure=closure_pin, preparationEvidence=evidence, historicalDeclaredCallers=len(legacy_actors), fixedAllowedCallers=len(allowed), failedAttempts=15, helperBodyReads=0)))

if __name__ == '__main__':
    main()
