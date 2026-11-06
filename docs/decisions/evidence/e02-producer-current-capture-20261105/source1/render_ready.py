"""Owned metadata-only current readiness renderer. No installation, process or target imports."""
import copy,hashlib,json,os,pathlib,secrets,shlex,stat,sys
OWNED_ROOT=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-capture-20261105/source1')
HERE=OWNED_ROOT/'capture'
PRODUCER_PIN={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/subject.json', 'bytes': 41959, 'sha256': 'd4229ef2ddf77e79a8f1a9990ea174db4c3dba9e7f2012ed42589d857be443b5'}
PRODUCER_ACCEPTANCE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifact-source-review-20261105/acceptance.json', 'bytes': 1212, 'sha256': '277c4b31273e8e4c703a7fec54f5311ed159e4995d351a3c9017687006b51cdb'}
LINEAGE_PIN={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifact-source-review-20261105/acceptance-lineage.json', 'bytes': 2010, 'sha256': '7e5e7c5f1fe4232ca87035438c72440bb53d3d4bd4f1cd7e74757bb781db6183'}
KNOWN_PIN={'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-capture-root-authority-20261105/root-known-actors.json', 'bytes': 2755, 'sha256': '94fd5716503e40b7472e8432e768e6e381bb71ded02bdae47523affc8fe25673'}
REQUEST_KEYS=['cmd', 'workdir', 'login', 'yield_time_ms', 'max_output_tokens', 'sandbox_permissions', 'justification']
REQUEST_POLICY={'sandbox_permissions': 'require_escalated', 'justification': 'Môžem raz vykonať prijatých 266 syntetických kontrol E02 s výsledkami v izolovanom /Data adresári? Platí aktuálny Root ACK, pôvodné časové a vstupné limity a zákaz automatického opakovania.'}

def need(value, message):
    if not value:
        raise ValueError(message)

def encode(value):
    return (json.dumps(value, indent=2) + '\n').encode()

def pin_bytes(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def read(path, expected=None):
    path = pathlib.Path(path)
    need(path.is_absolute() and str(path) == os.path.normpath(str(path)), 'CANONICAL_METADATA')
    for parent in (path, *path.parents):
        need(not parent.is_symlink(), 'NO_METADATA_ALIAS')
    first = path.lstat()
    need(stat.S_ISREG(first.st_mode) and first.st_size <= 16777216, 'SMALL_REGULAR_METADATA_ONLY')
    def identity(s):
        return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(identity(os.fstat(fd)) == identity(first), 'OPEN_IDENTITY')
        raw = bytearray()
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            raw.extend(block)
            need(len(raw) <= first.st_size, 'METADATA_BOUND')
        need(identity(os.fstat(fd)) == identity(first), 'HANDLE_DRIFT')
    finally:
        os.close(fd)
    need(identity(path.lstat()) == identity(first) and len(raw) == first.st_size, 'PATH_DRIFT')
    raw = bytes(raw)
    descriptor = pin_bytes(path, raw)
    need(expected is None or descriptor == expected, 'EXPECTED_IMMUTABLE_METADATA_PIN')
    return descriptor, raw, first

def doc(path, expected=None):
    descriptor, raw, st = read(path, expected)
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'NO_DUPLICATE_METADATA_KEYS')
            value[key] = item
        return value
    return descriptor, json.loads(raw, object_pairs_hook=pairs), st

def put(path, value):
    path = pathlib.Path(path)
    raw = value if type(value) is bytes else encode(value)
    need(len(raw) <= 16777216 and not path.exists() and not path.is_symlink(), 'ONE_USE_OWNED_PREPARATION_METADATA')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        need(stream.write(raw) == len(raw), 'EXACT_PREPARATION_WRITE')
    return pin_bytes(path, raw)


def actors(value):
    need(type(value) is list and value and all(type(a) is str and (a == '/root' or a.startswith('/root/')) for a in value), 'ACTUAL_DECLARED_ROOT_ACTORS')
    return set(value)


def review_pair(pins, subject, decision, forbidden):
    need(type(pins) is list and len(pins) == 2, 'TWO_ACTUAL_ORDERED_REVIEW_PINS')
    sessions = []
    for role, descriptor in zip(('qa', 'security'), pins):
        _, value, _ = doc(descriptor['path'], descriptor)
        need(set(value) == {'role', 'session', 'decision', 'subject'} and value['role'] == role and value['subject'] == subject and value['decision'] == decision, 'EXACT_ACTUAL_TYPED_REVIEW')
        need(value['session'].startswith('/root/') and value['session'] not in forbidden, 'CURRENT_FULL_UNION_REVIEW_INDEPENDENCE')
        sessions.append(value['session'])
    need(len(set(sessions)) == 2, 'DISTINCT_ACTUAL_REVIEWERS')


def main(args):
    need(len(args) == 4 and args[0] == '--spec' and args[2] == '--output', 'ACTUAL_PINNED_SPEC_AND_FRESH_PROJECT_OUTPUT')
    spec_pin, spec, _ = doc(args[1])
    need(set(spec) == set('schema outputRoot captureSourceAcceptance admissionDataAcceptance admissionSubject authors operators'.split()) and spec['schema'] == 'e02-current-capture-ready-render-spec-v1', 'CLOSED_ACTUAL_READY_RENDER_SPEC')
    output = pathlib.Path(args[3])
    need(output.is_absolute() and output.parent.resolve(strict=True).is_relative_to(OWNED_ROOT) and not output.exists() and not output.is_symlink(), 'ONLY_FRESH_OWNED_PROJECT_METADATA_OUTPUT')
    need(type(spec['outputRoot']) is str and spec['outputRoot'].startswith('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-') and not pathlib.Path(spec['outputRoot']).exists(), 'ROOT_SELECTED_FRESH_UNCREATED_CAPTURE_OUTPUT')
    source_pin, source, _ = doc(PRODUCER_PIN['path'], PRODUCER_PIN)
    _, source_acceptance, _ = doc(PRODUCER_ACCEPTANCE['path'], PRODUCER_ACCEPTANCE)
    method_pin, method, _ = doc(HERE / 'code-subject.json')
    admission_plan_pin, admission_plan, _ = doc(HERE / 'admission-plan.json')
    _, known, _ = doc(KNOWN_PIN['path'], KNOWN_PIN)
    capture_acceptance_pin, capture_acceptance, _ = doc(spec['captureSourceAcceptance']['path'], spec['captureSourceAcceptance'])
    admission_acceptance_pin, admission_acceptance, _ = doc(spec['admissionDataAcceptance']['path'], spec['admissionDataAcceptance'])
    admission_subject_pin, admission_subject, _ = doc(spec['admissionSubject']['path'], spec['admissionSubject'])
    required = actors(known['knownActors'])
    need(len(required) == 18 and {'/root', '/root/native_rebuild_prepare', '/root/helper_apk_binding_scope', '/root/collector_policy_security_553c5bfd'} <= required, 'EXACT_ROOT_CAPTURE_KNOWN18_BEFORE_PAIRS')
    union = required | actors(source['sourceContributors']) | actors(method['authors']) | actors(spec['authors']) | actors(spec['operators']) | actors(admission_subject['authors']) | actors(admission_subject['operators'])
    union |= {source['author'], source['coordinator'], source['predecessorAuthor']}
    n = len(admission_plan['caseNames'])
    need(capture_acceptance['schema'] == 'e02-root-producer4-capture-source-acceptance-v1' and capture_acceptance['actor'] == '/root' and capture_acceptance['decision'] == 'ACCEPT_PRODUCER4_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY' and capture_acceptance['subject'] == method_pin and capture_acceptance['producerSource'] == source_pin and capture_acceptance['admissionModelsDefined'] == n and capture_acceptance['executionAuthorized'] is False, 'ACTUAL_CURRENT_CAPTURE_SOURCE_ACCEPTANCE')
    need(admission_acceptance['schema'] == 'e02-root-producer4-capture-admission-data-acceptance-v1' and admission_acceptance['actor'] == '/root' and admission_acceptance['decision'] == 'ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY' and admission_acceptance['subject'] == admission_subject_pin and admission_acceptance['captureSource'] == method_pin and admission_acceptance['producerSource'] == source_pin and admission_acceptance['admissionPlan'] == admission_plan_pin and admission_acceptance['executionAuthorized'] is False, 'ACTUAL_CURRENT_ADMISSION_ACCEPTANCE')
    need(admission_subject['captureSource'] == method_pin and admission_subject['producerSource'] == source_pin and admission_subject['admissionPlan'] == admission_plan_pin and admission_subject['inputsUnchanged'] is True and admission_subject['truncated'] is False, 'ACTUAL_CURRENT_ADMISSION_SUBJECT')
    need(all(type(admission_subject[k]) is int and admission_subject[k] == n for k in ('modelsDefined', 'modelsExecuted', 'modelsPassed')) and all(type(admission_subject[k]) is int and admission_subject[k] == 0 for k in ('modelsFailed', 'skipped', 'targetModelsExecuted', 'helperExecutions', 'ordinaryRoleExecutions')), 'COMPLETE_CURRENT_ADMISSION_NO_TARGET_EXECUTION')
    # All actual participants are fixed before the first of the three pairs.
    review_pair(source_acceptance['reviews'], source_pin, 'ACCEPT_PRODUCER4_SOURCE4_AND_266_CONTROL_DEFINITIONS_ONLY', union)
    review_pair(capture_acceptance['reviews'], method_pin, 'ACCEPT_PRODUCER4_CAPTURE_SOURCE_AND_ADMISSION_DEFINITIONS_ONLY', union)
    review_pair(admission_acceptance['reviews'], admission_subject_pin, 'ACCEPT_PRODUCER4_CAPTURE_ADMISSION_DATA_ONLY', union)
    proofs = []
    def fields(descriptor, document, keys):
        for key in keys:
            if key not in document:
                continue
            values = list(enumerate(document[key])) if type(document[key]) is list else [(None, document[key])]
            for index, actor in values:
                if actor in union:
                    proofs.append(dict(actor=actor, authority=descriptor, selector='/' + key + ('' if index is None else '/' + str(index))))
    fields(KNOWN_PIN, known, ['knownActors'])
    fields(source_pin, source, ['author', 'coordinator', 'predecessorAuthor', 'sourceContributors'])
    fields(method_pin, method, ['authors'])
    fields(spec_pin, spec, ['authors', 'operators'])
    fields(admission_subject_pin, admission_subject, ['authors', 'operators'])
    need(set(p['actor'] for p in proofs) == union, 'EVERY_ACTUAL_PARTICIPANT_HAS_PINNED_FIELD_PROOF')
    output.mkdir(mode=0o700)
    context_pin = put(output / 'actor-context.json', dict(schema='e02-producer4-capture-current-actor-context-v1', producerSource=source_pin, captureSource=method_pin, sourceBirth=LINEAGE_PIN, participants=sorted(union), participantProofs=proofs))
    _, plan, _ = doc(HERE / 'execution-plan.json')
    plan.update(readiness=True, outputRoot=spec['outputRoot'], actualSourceReviewPins=source_acceptance['reviews'], captureSourceReviews=capture_acceptance['reviews'], captureSourceAcceptance=capture_acceptance_pin, admissionDataAcceptance=admission_acceptance_pin, rootAcknowledgement=None)
    plan_pin = put(output / 'execution-plan.json', plan)
    binding_pin = put(output / 'runtime-bindings.CANDIDATE.json', dict(schema='e02-producer4-capture-runtime-bindings-v1', readiness=True, producerSource=source_pin, producerAcceptance=PRODUCER_ACCEPTANCE, captureSourceAcceptance=capture_acceptance_pin, admissionDataAcceptance=admission_acceptance_pin, rootAcknowledgement='EXTERNALLY_SHA_BOUND_AT_LAUNCH'))
    ack = dict(schema='e02-producer4-control-capture-root-ack-v1', actor='/root', executionAuthorized=False, scope='ONE_CURRENT_SOURCE4_TEN_SELECTED_PURE_CONTROL_GROUPS_ONLY', producerSource=source_pin, producerSourceAcceptance=PRODUCER_ACCEPTANCE, producerReviews=source_acceptance['reviews'], captureSource=method_pin, captureSourceAcceptance=capture_acceptance_pin, captureReviews=capture_acceptance['reviews'], admissionPlan=admission_plan_pin, admissionData=admission_subject_pin, admissionDataAcceptance=admission_acceptance_pin, admissionReviews=admission_acceptance['reviews'], sourceBirth=LINEAGE_PIN, actorContext=context_pin, inputManifest=plan['inputManifest'], plan=plan_pin, clockSelection=plan['clockSelection'], requestContract=pin_bytes(HERE / 'request-template.json', read(HERE / 'request-template.json')[1]), runtimeBindings=binding_pin, authors=spec['authors'], operators=spec['operators'], noRetry=True)
    ack_pin = put(output / 'root-ack.UNISSUED.json', ack)
    workflow_pin = put(output / 'materialization-workflow.json', dict(schema='e02-current-capture-exact7-materialization-workflow-v1', author='/root/native_rebuild_prepare', sourceRenderer='Versioned from exact preserved ready-r2 renderer; original need/encode/read/doc/put helpers unchanged.', sourceReady=False, requestKeys=REQUEST_KEYS, requestPolicy=REQUEST_POLICY, existingGenerator=str(HERE / 'request-from-plan.py'), existingGeneratorArgv=[plan['tools']['python']['path'], '-I', '-B', str(HERE / 'request-from-plan.py'), '--root-ack', str(HERE / 'coordinator-acknowledgement.json')], steps=['Fresh independent concrete review of exact current plan/candidate binding/false UNISSUED_ACK and full7 workflow; preserve all failures.', 'Root separately authorizes installation of reviewed operational metadata. Renderer installs nothing, issues no ACK and creates no Data output.', 'After actual Root ACK issuance use only request-from-plan.py, retain its full returned seven-key JSON without projection, reconstruction or SHA string substitution.', 'Run separately reviewed request_preflight.py on the actual generated request: exact canonical positive and equivalent-argv extraquote negative, no API request.', 'Compare the whole dictionary including exact policy bytes. Submit precisely that generated dictionary once and preserve full genuine direct/yielded launch/polls/terminal. No extra shell/tty/prefix_rule and no automatic retry.', 'Actual capture/assembly/current DATA reviews remain separately required.'], actualAck=None, actualRequest=None, actualPreflight=None, executionAuthorized=False))
    print(json.dumps(dict(plan=plan_pin, context=context_pin, bindingCandidate=binding_pin, unissuedAck=ack_pin, workflow=workflow_pin, rootAckIssued=False, sourceReady=False, dataDirectoryCreated=False, executionAuthorized=False)))


if __name__ == '__main__':
    main(sys.argv[1:])
