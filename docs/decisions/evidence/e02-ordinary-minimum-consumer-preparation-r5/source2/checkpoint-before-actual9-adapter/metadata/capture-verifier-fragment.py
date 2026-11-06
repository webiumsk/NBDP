"""Staged consumer fragment, inserted as SOURCE text; never imported or executed.

These validators consume the capture SOURCE2's literal schemas. Original API
custody and DATA acceptance authority are unresolved until root supplies actual
closed contracts. The draft admission gate refuses before reaching this code.
"""


def current_producer(files, descriptor):
    equal(descriptor, CURRENT_PRODUCER, 'EXACT_CURRENT_PRODUCER_SOURCE2')
    producer = files.doc(descriptor)
    equal(producer['schema'], CURRENT_PRODUCER_SCHEMA)
    equal(producer['typedContract']['sha256'], CONTRACT_SHA)
    equal(producer['controlPlan'], CURRENT_SOURCE_PLAN)
    equal(producer['sourceDataInputClosure'], CURRENT_SOURCE_INPUTS)
    equal(producer['configurations'], CURRENT_CONFIGURATIONS)
    equal(producer['artifactBindings'], CURRENT_ARTIFACT_BINDINGS)
    need(producer['runtimeSourceCount'] == 16 and len(producer['sources']) == 31, 'CURRENT_31_SOURCE_16_WORKERS')
    by_name = {Path(p['path']).name: p for p in producer['sources']}
    need(len(by_name) == 31, 'UNIQUE_PRODUCER_SOURCE_NAMES')
    for p in producer['sources']: files.read(p)
    bindings = files.doc(producer['artifactBindings'])
    equal(bindings['amethystApk'], CURRENT_AMETHYST_APK)
    equal(bindings['helperApk'], CURRENT_HELPER_APK)
    for prefix, schema, decision in (
        ('amethyst', 'nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1', 'ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY'),
        ('helper', 'nbdp-actual-artifact-data-acceptance-v1', 'ACCEPT_REBUILT_HELPER_ARTIFACT_ONLY')):
        acceptance = files.doc(bindings[prefix + 'Acceptance'])
        equal(acceptance['schema'], schema); equal(acceptance['decision'], decision)
        need(acceptance['artifactQualified'] is True, 'EXACT_TRUE_ARTIFACT_QUALIFICATION')
        equal(acceptance['subject'], bindings[prefix + 'Provenance'])
        equal(files.doc(bindings[prefix + 'Provenance'])['apk'], bindings[prefix + 'Apk'])
    for descriptor in producer['configurations']:
        config = files.doc(descriptor)
        equal(config['sourceAndDependencyPins'], CURRENT_WORKERS)
        equal(config['amethystApk'], CURRENT_AMETHYST_APK)
        equal(config['helperApk'], CURRENT_HELPER_APK)
    return producer


def capture_output(files, scope, receipt):
    """Validate retained child streams, independently of the outer tool API."""
    raw = {name: files.read(receipt[name]) for name in ('stdout', 'stderr')}
    equal(receipt['observedStreamBytes'], {name: len(value) for name, value in raw.items()})
    equal(receipt['truncated'], {'stdout': False, 'stderr': False})
    need(len(raw['stdout']) <= 1048576 and len(raw['stderr']) <= 262144, 'POST_CAPTURE_RETENTION_LIMIT')
    if scope['name'] != 'observation-model':
        need(scope['name'] in ('public-identity-metadata','producer2-source-wiring','rebuilt-artifact-bindings'), 'EXACT_CURRENT_PYTHON_SCOPE_NAME')
        equal(raw['stdout'], b'')
        match = re.fullmatch(rb'([.]+)\n-{70}\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n', raw['stderr'])
        need(match and len(match[1]) == scope['count'] and int(match[2]) == scope['count'], 'EXACT_QUIET_PYTHON_OUTPUT')
        equal(receipt['observedPartitions'], {scope['name']: scope['count']})
    else:
        equal(raw['stderr'], b'')
        need(raw['stdout'].endswith(b'\n') and raw['stdout'].count(b'\n') == 1, 'EXACT_NODE_ONE_LINE')
        from strict import loads
        value = loads(raw['stdout'])
        closed(value, 'schema ok checks cases scope')
        equal(value['schema'], 'e02-producer2-observation-model-controls-v1')
        equal(value['ok'], True); equal(value['checks'], 20)
        equal(value['scope'], 'SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME')
        equal(value['cases'], scope['expectedCases'])
        equal(receipt['observedPartitions'], {'shared-budget-guard-proxy-and-exchange-adapter-models': 20})


def capture_child(files, scope, row, capture_root, artifact_index):
    closed(row, 'scope expected observed partitions captureMatched execution')
    equal(row['scope'], scope['name']); equal(row['expected'], scope['count'])
    equal(row['observed'], scope['count']); equal(row['captureMatched'], True)
    folder = Path(capture_root) / 'scopes' / scope['name']
    equal(row['execution']['path'], str(folder / 'execution.json'))
    receipt = files.doc(row['execution'])
    equal(receipt['schema'], 'e02-producer3-pure-scope-execution-v1')
    equal(receipt['actor'], '/root/producer3_capture'); equal(receipt['parentCoordinator'], '/root')
    equal(receipt['argv'], scope['argv']); equal(receipt['cwd'], CURRENT_EXPERIMENT_REPOSITORY)
    equal(receipt['expectedCount'], scope['count']); equal(receipt['observedCount'], scope['count'])
    equal(receipt['timeoutSeconds'], 60)
    equal(receipt['retentionBytes'], {'stdout': 1048576, 'stderr': 262144})
    equal(receipt['retentionMeaning'], 'POST_CAPTURE_FILE_PREFIX_LIMIT_NOT_STREAMING_MEMORY_CAP')
    integer(receipt['pid'], 1); integer(receipt['elapsedNanoseconds'], 0, 63000000000)
    equal(receipt['exitCode'], 0); equal(receipt['signal'], None)
    for key in ('reaped', 'naturalExit', 'stdoutEOF', 'stderrEOF', 'sourceUnchanged',
                'countAndOutputShapeMatched', 'captureMatched'): equal(receipt[key], True)
    equal(receipt['forceRequested'], False); equal(receipt['forceReason'], None)
    equal(receipt['firstError'], None); equal(receipt['secondaryErrors'], [])
    equal(receipt['controlResultAcceptedByAuthor'], False)
    equal(receipt['state'], 'WRITES_STOPPED')
    equal(receipt['result'], 'SCOPED_DATA_CAPTURE_MATCHED_PENDING_INDEPENDENT_REVIEW')
    equal(row['partitions'], receipt['observedPartitions'])
    for stream in ('stdout', 'stderr'): equal(receipt[stream]['path'], str(folder / ('data.' + stream)))
    capture_output(files, scope, receipt)
    before = files.doc(artifact_index[str(folder / 'sources-before.json')])
    after = files.doc(artifact_index[str(folder / 'sources-after.json')])
    equal(before, after, 'EVERY_SCOPE_FULL_BEFORE_AFTER_UNCHANGED')
    return before


def capture_inputs(files, descriptor, producer, plan):
    inputs = files.doc(descriptor)
    closed(inputs, 'schema sourceSubject sourceManifest sourceControlPlan node python actualSourceReviews requiredCoverage files actualInputCount maximumInputCount fullReadTrees scope')
    equal(inputs['schema'], 'e02-producer3-control-frozen-inputs-v1')
    equal(inputs['sourceSubject'], CURRENT_PRODUCER); equal(inputs['sourceManifest'], CURRENT_SOURCE_PACKET)
    equal(inputs['sourceControlPlan'], CURRENT_SOURCE_PLAN)
    equal(inputs['maximumInputCount'], 4096)
    integer(inputs['actualInputCount'], 1, 4096); equal(len(inputs['files']), inputs['actualInputCount'])
    indexed = {d['path']: d for d in inputs['files']}
    need(len(indexed) == len(inputs['files']), 'UNIQUE_CURRENT_CAPTURE_CLOSURE')
    for d in inputs['files']:
        closed(d, 'path bytes sha256'); hx(d['sha256']); integer(d['bytes'], 0, 8589934592)
        path = Path(text(d['path'],4096))
        need(path.is_absolute() and '..' not in path.parts and str(path) == d['path'], 'CURRENT_INPUT_CANONICAL_DESCRIPTOR')
    required = inputs['requiredCoverage']
    closed(required, 'finalSubjectManifestPlan all16Workers all4Tests runtimeFixtureBindings bothConfigurations acceptedApkHelperNativeE01 provenanceAcceptances original19 diagnosticV2 oldV1ReadOperands interpreters baselineScalarAndOracle')
    for group in required.values():
        need(type(group) is list and group, 'NONEMPTY_EXACT_COVERAGE_CATEGORY')
        for d in group: equal(indexed.get(d['path']), d)
    equal(required['finalSubjectManifestPlan'], [CURRENT_PRODUCER, CURRENT_SOURCE_PACKET, CURRENT_SOURCE_PLAN])
    equal(required['all16Workers'], CURRENT_WORKERS); equal(required['bothConfigurations'], CURRENT_CONFIGURATIONS)
    source_plan = files.doc(CURRENT_SOURCE_PLAN)
    equal(required['all4Tests'], [s['source'] for s in source_plan['scopes']])
    equal(required['interpreters'], [inputs['node'], inputs['python']])
    for key in ('node', 'python'): equal(inputs[key], source_plan[key])
    for d in producer['sources']: equal(indexed.get(d['path']), d)
    equal(indexed.get(CURRENT_SOURCE_INPUTS['path']), CURRENT_SOURCE_INPUTS)
    for row in files.doc(CURRENT_SOURCE_INPUTS)['files']:
        d = {key:row[key] for key in ('path','bytes','sha256')}
        equal(indexed.get(d['path']), d, 'ALL_PRODUCER_DECLARED_READ_INPUTS')
    trees = inputs['fullReadTrees']
    need(type(trees) is list and len(trees) == 2, 'EXACT_TWO_FULL_READ_TREES')
    for tree, (root, count) in zip(trees, CURRENT_READ_TREE_ROOTS):
        closed(tree, 'root count files'); equal(tree['root'], root); equal(tree['count'], count)
        equal(len(tree['files']), count)
        for row in tree['files']:
            closed(row, 'path bytes sha256 relativePath mode')
            d = {k: row[k] for k in ('path', 'bytes', 'sha256')}
            equal(indexed.get(d['path']), d)
            equal(str(Path(root) / row['relativePath']), row['path'])
            need(not Path(row['relativePath']).is_absolute() and '..' not in Path(row['relativePath']).parts, 'TREE_MEMBER_ESCAPE')
    equal(plan['actualInputCount'], inputs['actualInputCount'])
    return inputs


def current_capture(files, nodes, mode, origin, producer):
    """No skipped prerequisite, old result or count-equivalent scope can qualify."""
    closed(nodes, 'producerSource testSource inputClosure plan release capture originalToolResponses result acceptance qaReview securityReview admissionModelAcceptance upstreamRootACK')
    need(all(value is not None for value in nodes.values()), 'ALL_CURRENT_CAPTURE_NODES_REQUIRED')
    equal(nodes, CURRENT_CAPTURE_BINDINGS[mode], 'EXACT_FROZEN_CURRENT_CAPTURE_DAG')
    equal(nodes['producerSource'], CURRENT_PRODUCER)
    source_plan = files.doc(CURRENT_SOURCE_PLAN)
    chosen = source_plan['scopes'][:3] if mode == 'capture-a' else source_plan['scopes'][3:]
    equal(nodes['testSource'], [s['source'] for s in chosen])
    data = files.doc(nodes['result'])
    contract = files.doc(CURRENT_AUTHORITY_CONTRACT)
    closed(data, ' '.join(contract['dataSubject']['requiredKeys']))
    equal(data['schema'], 'e02-producer3-actual-control-data-subject-v1')
    equal(data['captureId'], mode); equal(data['producerSource'], CURRENT_PRODUCER)
    equal(data['producerContract'], CURRENT_SOURCE_PACKET); equal(data['captureSource'], nodes['capture'])
    equal(data['controlPlan'], nodes['plan']); equal(data['rootAcknowledgement'], nodes['release'])
    equal(data['frozenInputs'], nodes['inputClosure']); equal(data['originalToolOrigin'], nodes['originalToolResponses'])
    equal(data['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
    equal(data['coordinator'], '/root'); equal(data['state'], contract['dataSubject']['state'])
    equal(data['operators'], ['/root'])
    forbidden = actors(data['authors']) | actors(data['operators'])
    need({'/root', '/root/producer3_capture'} <= forbidden, 'CURRENT_CAPTURE_ACTORS_REQUIRED')
    origin.forbidden |= forbidden | actors(CURRENT_CONTROL_ACTORS)
    group = contract['groups'][mode]
    capture_source = files.doc(nodes['capture'])
    equal(capture_source['schema'], 'e02-producer3-bound-capture-source-subject-v1')
    equal(capture_source['producerSource'], CURRENT_PRODUCER)
    equal(capture_source['producerContract'], CURRENT_SOURCE_PACKET)
    equal(capture_source['normativeDataContract'], CURRENT_AUTHORITY_CONTRACT)
    selected_capture = capture_source['captures'][mode]
    equal(selected_capture['runner'], data['captureScript'])
    equal(selected_capture['controlPlan'], nodes['plan']); equal(selected_capture['frozenInputs'], nodes['inputClosure'])
    equal(data['scopeNames'], group['scopeNames']); equal(data['countsSeparate'], group['counts'])
    for key in ('allNatural0NoForceNoErrorNoTruncation', 'sourceUnchangedBeforeAfterEveryScopeAndOverall', 'completeInstalledMembership'): equal(data[key], True)
    equal(data['pythonNamesMeaning'], contract['dataSubject']['pythonNamesMeaning'])
    equal(data['retentionMeaning'], contract['dataSubject']['retentionMeaning'])
    equal(data['runtimeAuthorized'], False); equal(data['ordinaryRowsQualified'], 0)
    equal(data['canonicalE02'], 'PARTIAL22_UNCHANGED')
    plan = files.doc(nodes['plan'])
    equal(plan['schema'], 'e02-producer3-fixed-control-capture-plan-v1'); equal(plan['captureId'], mode)
    equal(plan['sourceSubject'], CURRENT_PRODUCER); equal(plan['sourceManifest'], CURRENT_SOURCE_PACKET)
    equal(plan['frozenSourcePlan'], CURRENT_SOURCE_PLAN); equal(plan['runner'], data['captureScript'])
    equal(plan['rawRetentionBytes'], {'stdout': 1048576, 'stderr': 262144})
    equal(plan['timeoutSeconds'], 60); equal(plan['cleanupReapSeconds'], 3)
    for key in ('stopFirstFailure', 'noRetry'): equal(plan[key], True)
    scopes = plan['separateScopes']
    equal([(s['name'], s['count']) for s in scopes], [(s['scope'], s['count']) for s in chosen])
    for scope, source_scope in zip(scopes, chosen):
        closed(scope, 'name argv count expectedCases timeoutSeconds')
        equal(scope['timeoutSeconds'], 60)
        argv = [source_plan['node']['path'], source_scope['source']['path']] if scope['name'] == 'observation-model' else [source_plan['python']['path'], '-I', '-B', source_scope['source']['path']]
        equal(scope['argv'], argv)
        if scope['name'] != 'observation-model': equal(scope['expectedCases'], source_scope['exactDefinedPythonNames'])
    inputs = capture_inputs(files, nodes['inputClosure'], producer, plan)
    equal(data['fixedInputCount'], inputs['actualInputCount'])
    execution = files.doc(data['execution'])
    closed(execution, 'schema actor captureId state result sourceSubject runnerSubject runner sourceManifest frozenSourcePlan frozenInputs captureSource admissionModelAcceptance controlPlan rootAcknowledgement scopes remainingNotExecuted sourceUnchanged terminalError noRetry controlResultAcceptedByAuthor independentResultReview noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices')
    equal(execution['schema'], 'e02-producer3-current-control-execution-v1'); equal(execution['captureId'], mode)
    equal(execution['sourceSubject'], CURRENT_PRODUCER); equal(execution['runner'], data['captureScript'])
    equal(execution['controlPlan'], nodes['plan']); equal(execution['rootAcknowledgement'], nodes['release'])
    equal(execution['runnerSubject'], selected_capture['runnerSubject'])
    equal(execution['sourceManifest'], CURRENT_SOURCE_PACKET); equal(execution['frozenSourcePlan'], CURRENT_SOURCE_PLAN)
    equal(execution['frozenInputs'], nodes['inputClosure']); equal(execution['captureSource'], nodes['capture'])
    equal(execution['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
    equal(execution['actor'], '/root/producer3_capture'); equal(execution['state'], 'WRITES_STOPPED')
    equal(execution['result'], 'FIXED_DATA_SCOPES_MATCHED_PENDING_REVIEW')
    for key in ('sourceUnchanged', 'noRetry', 'noOrdinaryRuntimePrimaryConsumerActualGuardNetworkSdkServices'): equal(execution[key], True)
    equal(execution['controlResultAcceptedByAuthor'], False)
    equal(execution['remainingNotExecuted'], []); equal(execution['terminalError'], None)
    equal(len(execution['scopes']), len(scopes))
    capture_root = Path(nodes['plan']['path']).parent
    manifest = files.doc(data['rawArtifactManifest'])
    closed(manifest, 'schema captureId files originalApiResponses')
    equal(manifest['schema'], 'e02-producer3-current-control-artifact-manifest-v1')
    equal(manifest['captureId'], mode)
    artifact_index = {d['path']:d for d in manifest['files']}
    need(len(artifact_index) == len(manifest['files']) and len(artifact_index) <= 4096, 'RAW_ARTIFACT_MEMBERSHIP')
    snapshots = [capture_child(files, scope, row, capture_root, artifact_index) for scope, row in zip(scopes, execution['scopes'])]
    overall_before = files.doc(data['overallSourcesBefore']); overall_after = files.doc(data['overallSourcesAfter'])
    equal(overall_before, overall_after, 'OVERALL_FULL_SOURCE_SNAPSHOT_UNCHANGED')
    for snap in snapshots + [overall_before, overall_after]:
        equal(snap['sourceSubject'], CURRENT_PRODUCER); equal(snap['sourceManifest'], CURRENT_SOURCE_PACKET)
        equal(snap['frozenSourcePlan'], CURRENT_SOURCE_PLAN); equal(snap['monitor'], data['captureScript'])
        equal(snap['runnerSubject'], execution['runnerSubject']); equal(snap['controlPlan'], nodes['plan'])
        equal(snap['coordinatorAcknowledgement'], nodes['release']); equal(snap['inputManifest'], nodes['inputClosure'])
        equal(snap['frozenInputs'], inputs['files']); equal(snap['fullActualReadTrees'], inputs['fullReadTrees'])
        equal(snap['captureSource'], nodes['capture']); equal(snap['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
        equal(snap['sourceAndCaptureReviewRecords'], data['sourceReviews'] + data['captureReviews'])
        equal(snap['interpreters'], {'python':inputs['python'],'node':inputs['node']})
        model_acceptance = files.doc(nodes['admissionModelAcceptance'])
        equal(snap['admissionModelDataSubject'], model_acceptance['subject'])
        equal(snap['admissionModelReviews'], model_acceptance['reviews'])
        tree_pin = next(d for d in producer['sources'] if Path(d['path']).name == 'dependency-tree.json')
        tree = files.doc(tree_pin)
        equal(snap['installedMembership'], {k:tree[k] for k in ('directories','files','symlinks')})
        equal([len(snap['installedMembership'][k]) for k in ('files','directories','symlinks')], [816,65,2])
    # These methods are SOURCE-staged separately from the already literal child
    # schema. No absent contract or generic truthy acceptance may admit a result.
    capture_authority(files, nodes, data, execution, inputs, origin)
    return data


def capture_data_reviews(files, descriptors, subject, decision, origin):
    need(type(descriptors) is list and len(descriptors) == 2, 'CURRENT_EXACT_QA_SECURITY_PAIR')
    roles, sessions = set(), set()
    for descriptor in descriptors:
        review = files.doc(descriptor)
        closed(review, 'role session decision subject')
        need(review['role'] in ('qa', 'security') and review['role'] not in roles, 'CURRENT_EXACT_REVIEW_ROLE')
        text(review['session'], 256)
        need(review['session'].startswith('/root/') and review['session'] not in origin.forbidden,
             'CURRENT_DATA_AUTHOR_OPERATOR_CANNOT_REVIEW')
        equal(review['subject'], subject); equal(review['decision'], decision)
        roles.add(review['role']); sessions.add(review['session'])
    equal(roles, {'qa', 'security'}); need(len(sessions) == 2, 'DISTINCT_CURRENT_REVIEW_SESSIONS')
    need(descriptors[0]['sha256'] != descriptors[1]['sha256'], 'DISTINCT_CURRENT_REVIEW_DOCUMENTS')


def capture_authority(files, nodes, data, execution, inputs, origin):
    need(CURRENT_AUTHORITY_CONTRACT is not None, 'CURRENT_ACTUAL_AUTHORITY_CONTRACT_UNRENDERED')
    contract = files.doc(CURRENT_AUTHORITY_CONTRACT)
    equal(contract['schema'], 'e02-producer3-planned-data-contract-v1')
    capture_admission_models(files, nodes, data, origin)
    capture_root_ack(files, nodes, data, execution, inputs, origin)
    capture_original_tool(files, nodes, data, origin)
    manifest = files.doc(data['rawArtifactManifest'])
    closed(manifest, 'schema captureId files originalApiResponses')
    equal(manifest['schema'], 'e02-producer3-current-control-artifact-manifest-v1')
    equal(manifest['captureId'], data['captureId'])
    need(type(manifest['files']) is list and 1 <= len(manifest['files']) <= 4096, 'CURRENT_ARTIFACT_MEMBERSHIP_BOUND')
    indexed = {d['path']: d for d in manifest['files']}
    need(len(indexed) == len(manifest['files']), 'UNIQUE_CURRENT_RAW_ARTIFACT_PATHS')
    for key in ('execution', 'overallSourcesBefore', 'overallSourcesAfter', 'frozenInputs', 'controlPlan', 'captureScript', 'rootAcknowledgement'):
        d = data[key]; equal(indexed.get(d['path']), d, 'CURRENT_RAW_ARTIFACT_REQUIRED_MEMBER')
    for row in execution['scopes']:
        d = row['execution']; equal(indexed.get(d['path']), d)
        receipt = files.doc(d)
        for key in ('stdout', 'stderr'):
            p = receipt[key]; equal(indexed.get(p['path']), p)
    acceptance = files.doc(nodes['acceptance'])
    closed(acceptance, ' '.join(contract['dataAcceptance']['requiredKeys']))
    equal(acceptance['schema'], 'e02-producer3-actual-control-data-acceptance-v1')
    equal(acceptance['actor'], '/root'); equal(acceptance['subject'], nodes['result'])
    group = contract['groups'][data['captureId']]
    equal(acceptance['decision'], group['decision']); equal(acceptance['captureId'], data['captureId'])
    equal(acceptance['countsSeparate'], group['counts']); equal(acceptance['runtimeAuthorized'], False)
    equal(acceptance['ordinaryRowsQualified'], 0); equal(acceptance['canonicalE02'], 'PARTIAL22_UNCHANGED')
    equal(acceptance['reviews'], [nodes['qaReview'], nodes['securityReview']])
    capture_data_reviews(files, acceptance['reviews'], nodes['result'], group['decision'], origin)
    # External authenticated origins remain mandatory in addition to four-key
    # pinned review transcriptions. JSON authorship alone proves no identity.
    origin.reviews(nodes['result'], 'CONTROL')


def capture_admission_models(files, nodes, data, origin):
    contract = files.doc(CURRENT_AUTHORITY_CONTRACT)
    acceptance = files.doc(nodes['admissionModelAcceptance'])
    closed(acceptance, ' '.join(contract['model9Acceptance']['requiredKeys']))
    equal(acceptance['schema'], 'e02-producer3-capture-admission-model-acceptance-v1')
    equal(acceptance['actor'], '/root')
    equal(acceptance['decision'], 'ACCEPT_ACTUAL_PRODUCER3_CAPTURE_9_ADMISSION_MODELS_ONLY')
    equal(acceptance['captureSource'], nodes['capture']); equal(acceptance['countsSeparate'], [9])
    equal(acceptance['runtimeAuthorized'], False); equal(acceptance['ordinaryRowsQualified'], 0)
    need(CURRENT_ADMISSION_MODEL_CONTRACT is not None, 'CURRENT_MODEL9_SUBJECT_CONTRACT_REQUIRED')
    model_contract = files.doc(CURRENT_ADMISSION_MODEL_CONTRACT)
    equal(model_contract['schema'], 'e02-producer3-planned-model-subject-contract-v1')
    equal(model_contract['baseContractSha256'], CURRENT_AUTHORITY_CONTRACT['sha256'])
    subject = files.doc(acceptance['subject'])
    closed(subject, ' '.join(model_contract['modelDataSubject']['requiredKeys']))
    equal(subject['schema'], 'e02-producer3-capture-admission-model-data-subject-v1')
    equal(subject['state'], 'WRITES_STOPPED_PENDING_ACTUAL_NONAUTHOR_NONOPERATOR_QA_SECURITY')
    equal(subject['coordinator'], '/root'); equal(subject['operators'], ['/root'])
    origin.forbidden |= actors(subject['authors']) | actors(subject['operators'])
    capture_source = files.doc(nodes['capture'])
    equal(subject['captureSource'], nodes['capture'])
    equal(subject['modelSource'], capture_source['modelSource'])
    equal(subject['bothInputScopes'], [capture_source['captures'][mode]['runner'] for mode in ('capture-a','capture-b')])
    equal(subject['countsSeparate'], [9]); equal(subject['allNatural0NoForceNoErrorNoTruncation'], True)
    equal(subject['inputsUnchanged'], True); equal(subject['runtimeAuthorized'], False); equal(subject['ordinaryRowsQualified'], 0)
    for key in model_contract['modelDataSubject']['pinFields']: files.read(subject[key])
    equal(files.read(subject['overallSourcesBefore']), files.read(subject['overallSourcesAfter']))
    equal(nodes['upstreamRootACK'], subject['rootAcknowledgement'])
    closed(acceptance['reviews'], 'qa security')
    capture_data_reviews(files, [acceptance['reviews']['qa'], acceptance['reviews']['security']], acceptance['subject'], acceptance['decision'], origin)
    # The exact upstream root ACK pin is frozen in the consumer DAG and the
    # independently reviewed model subject. No unrelated ACK can be substituted.
    files.read(nodes['upstreamRootACK'])
    origin.reviews(acceptance['subject'], 'CONTROL')


def capture_original_tool(files, nodes, data, origin):
    """Original outer API custody; pipeEOF/reap comes only from capture_child."""
    import decimal
    import json
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'DUPLICATE_ORIGINAL_API_KEY'); result[key] = value
        return result
    def number(token):
        need(token != '-0', 'ORIGINAL_API_NEGATIVE_ZERO')
        return integer(int(token), -I64, I64)
    def invalid(_):
        need(False, 'ORIGINAL_API_NONFINITE')
    def fraction(token):
        need(len(token) <= 128, 'ORIGINAL_API_DECIMAL_BOUND')
        value = decimal.Decimal(token)
        need(value.is_finite() and not (value.is_zero() and value.is_signed()), 'ORIGINAL_API_DECIMAL_DOMAIN')
        return value
    value = json.loads(files.read(nodes['originalToolResponses']).decode('utf-8', 'strict'),
        object_pairs_hook=pairs, parse_float=fraction, parse_int=number, parse_constant=invalid)
    stack, count = [(value, ())], 0
    while stack:
        item, path = stack.pop(); count += 1
        need(len(path) <= 48 and count <= 250000, 'ORIGINAL_API_STRUCTURE_BOUND')
        if type(item) is decimal.Decimal:
            need(path == ('launch', 'unmodifiedResponse', 'wall_time_seconds') or
                 (len(path) == 4 and path[0] == 'polls' and type(path[1]) is int and path[2:] == ('unmodifiedResponse', 'wall_time_seconds')),
                 'DECIMAL_ONLY_ORIGINAL_API_WALL_TIME')
        elif type(item) is str: text(item, 16777216)
        elif type(item) is dict: stack.extend((v, path + (k,)) for k,v in item.items())
        elif type(item) is list: stack.extend((v, path + (i,)) for i,v in enumerate(item))
    closed(value, 'schema operator launch polls'); equal(value['schema'], 'e02-actual-tool-custody-v1')
    equal(value['operator'], '/root'); need(value['operator'] in origin.forbidden, 'CURRENT_API_OPERATOR_DISCLOSURE')
    need(type(value['polls']) is list and len(value['polls']) <= 128, 'CURRENT_API_POLL_BOUND')
    def response(frame, tool):
        closed(frame, 'toolName actualArguments unmodifiedResponse'); equal(frame['toolName'], tool)
        r = frame['unmodifiedResponse']
        need(type(r) is dict and {'output', 'wall_time_seconds'} <= set(r)
             and set(r) <= {'chunk_id', 'exit_code', 'output', 'session_id', 'wall_time_seconds', 'original_token_count'}, 'ORIGINAL_API_RESPONSE_SHAPE')
        text(r['output'], 16777216)
        duration = r['wall_time_seconds']
        need(type(duration) is int or (type(duration) is decimal.Decimal and duration.is_finite()), 'ORIGINAL_API_WALL_TIME_TYPE')
        need(0 <= duration <= 10000000 and not (type(duration) is decimal.Decimal and duration.is_signed()), 'ORIGINAL_API_WALL_TIME_DOMAIN')
        if 'chunk_id' in r: text(r['chunk_id'], 256)
        if 'original_token_count' in r: integer(r['original_token_count'])
        if r.get('session_id') is not None: integer(r['session_id'], 1)
        if r.get('exit_code') is not None: integer(r['exit_code'], -255, 255)
        return r
    first = response(value['launch'], 'tools.exec_command')
    import shlex
    plan = files.doc(nodes['plan'])
    closed(plan['rootAckArgument'], 'meaning placeholder')
    equal(plan['rootAckArgument']['meaning'], 'DERIVE_HEX_SHA256_FROM_ACTUAL_EXTERNAL_ACK_FILE')
    equal(plan['rootAckArgument']['placeholder'], '__ACTUAL_ROOT_ACK_SHA256__')
    placeholder = plan['rootAckArgument']['placeholder']
    template = plan['outerRequestTemplate']
    closed(template, 'cmd workdir login yield_time_ms max_output_tokens')
    need(template['cmd'].count(placeholder) == 1, 'ONE_ACK_DIGEST_PLACEHOLDER')
    request = dict(template, cmd=template['cmd'].replace(placeholder, nodes['release']['sha256']))
    equal(request['workdir'], CURRENT_EXPERIMENT_REPOSITORY); equal(request['login'], False)
    equal(request['yield_time_ms'], 1000); equal(request['max_output_tokens'], 10000)
    argv = [nodes['release']['sha256'] if token == placeholder else token for token in plan['outerArgvTemplate']]
    equal(shlex.split(request['cmd']), argv, 'EXACT_CAPTURE_OUTER_TOKENIZATION')
    source_plan = files.doc(CURRENT_SOURCE_PLAN)
    equal(argv[:8], ['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','297'])
    equal(argv[8:], [source_plan['python']['path'],'-I','-B',data['captureScript']['path'],
                     '--execute-once','--root-ack-sha',nodes['release']['sha256']])
    equal(plan['onceCommandPrefix'], argv[8:-1])
    equal(value['launch']['actualArguments'], request, 'EXACT_CAPTURE_APPROVED_OUTER_API_REQUEST')
    outputs = [first['output']]
    if first.get('exit_code') is not None:
        equal(first['exit_code'], 0); equal(first.get('session_id'), None); equal(value['polls'], [])
    else:
        session = first.get('session_id'); integer(session, 1)
        need(value['polls'], 'ALL_GENUINE_SAME_SESSION_POLLS_REQUIRED')
        for index, frame in enumerate(value['polls']):
            r = response(frame, 'tools.write_stdin')
            outputs.append(r['output'])
            args = frame['actualArguments']; closed(args, 'session_id chars yield_time_ms max_output_tokens')
            equal(args['session_id'], session); equal(args['chars'], '')
            integer(args['yield_time_ms'], 1, 300000); integer(args['max_output_tokens'], 1, 10000)
            if index == len(value['polls']) - 1:
                equal(r.get('exit_code'), 0); equal(r.get('session_id'), None)
            else:
                equal(r.get('exit_code'), None); equal(r.get('session_id'), session)
    from strict import loads
    raw = ''.join(outputs).encode('utf-8', 'strict')
    need(raw.endswith(b'\n') and raw.count(b'\n') == 1, 'EXACT_ORIGINAL_API_CAPTURE_SUMMARY')
    summary = loads(raw)
    closed(summary, 'state captureId captureMatched execution scopes')
    equal(summary['state'], 'WRITES_STOPPED'); equal(summary['captureId'], data['captureId'])
    equal(summary['captureMatched'], True); equal(summary['execution'], data['execution'])
    equal(summary['scopes'], files.doc(data['execution'])['scopes'])
    # An authenticated CONTROL origin additionally binds this pinned document;
    # no claimed inner API/PID/EOF field is admitted into the closed envelope.


def capture_root_ack(files, nodes, data, execution, inputs, origin):
    ack = files.doc(nodes['release'])
    closed(ack, 'schema actor captureId sourceSubject runnerSubject runner controlPlan frozenInputs sourceQaReview sourceSecurityReview sourceQaDecision sourceSecurityDecision captureQaReview captureSecurityReview captureQaDecision captureSecurityDecision pureControlsAuthorized allowedScopes stopFirstFailure noRetry ordinaryRuntimeAuthorized primaryAuthorized consumerAuthorized androidAuthorized servicesAuthorized protocolCryptoOrNativeAuthorized sdkAuthorized roleMaterializationAuthorized admissionModelAcceptance')
    equal(ack['schema'], 'e02-producer3-controls-root-ack-v2'); equal(ack['actor'], '/root')
    equal(ack['captureId'], execution['captureId']); equal(ack['sourceSubject'], CURRENT_PRODUCER)
    equal(ack['runnerSubject'], execution['runnerSubject']); equal(ack['runner'], data['captureScript'])
    equal(ack['admissionModelAcceptance'], nodes['admissionModelAcceptance'])
    equal(ack['controlPlan'], nodes['plan']); equal(ack['frozenInputs'], nodes['inputClosure'])
    names = {'capture-a': {'observation-model': 20, 'public-identity-metadata': 8, 'producer2-source-wiring': 7},
             'capture-b': {'rebuilt-artifact-bindings': 3}}
    equal(ack['allowedScopes'], names[execution['captureId']])
    for key in ('pureControlsAuthorized', 'stopFirstFailure', 'noRetry'): equal(ack[key], True)
    for key in ('ordinaryRuntimeAuthorized', 'primaryAuthorized', 'consumerAuthorized', 'androidAuthorized',
                'servicesAuthorized', 'protocolCryptoOrNativeAuthorized', 'sdkAuthorized', 'roleMaterializationAuthorized'): equal(ack[key], False)
    runner = files.doc(execution['runnerSubject'])
    for key in ('runner', 'controlPlan', 'frozenInputs', 'captureId'): equal(runner[key], ack[key])
    for d in runner['preparationArtifacts']: files.read(d)
    for prefix, subject in (('source', CURRENT_PRODUCER), ('capture', execution['runnerSubject'])):
        sessions = []
        for role, title in (('qa', 'Qa'), ('security', 'Security')):
            descriptor = ack[prefix + title + 'Review']
            if prefix == 'source': equal(descriptor, inputs['actualSourceReviews'][role])
            review = files.doc(descriptor)
            closed(review, 'role session decision subject')
            equal(review['role'], role); equal(review['subject'], subject)
            equal(review['decision'], ack[prefix + title + 'Decision'])
            need(CURRENT_SOURCE_CAPTURE_DECISIONS is not None, 'CURRENT_REVIEW_DECISIONS_UNRENDERED')
            equal(review['decision'], CURRENT_SOURCE_CAPTURE_DECISIONS[prefix][role])
            text(review['session'], 256)
            need(review['session'].startswith('/root/') and review['session'] not in origin.forbidden,
                 'CURRENT_CAPTURE_SOURCE_AUTHOR_OPERATOR_REVIEW_LAUNDERING')
            sessions.append(review['session'])
        need(sessions[0] != sessions[1], 'DISTINCT_CURRENT_QA_SECURITY_SESSIONS')
    equal(data['sourceReviews'], [ack['sourceQaReview'], ack['sourceSecurityReview']])
    equal(data['captureReviews'], [ack['captureQaReview'], ack['captureSecurityReview']])


def control_evidence(files, descriptor, origin):
    require_current_source_profile()
    value = files.doc(descriptor)
    closed(value, 'schema profileId authors operators producerSubject producerCaptureA producerCaptureB componentCarry unchangedScopes consumerSource consumerControls')
    equal(value['schema'], 'e02-minimum-controls-subject-v3'); equal(value['profileId'], wire.PROFILE)
    producer = current_producer(files, value['producerSubject'])
    # Close the actor union across BOTH groups and their upstream model DATA
    # before reviewing either group. Later groups cannot hide a reviewer who is
    # already an author/operator of other newly admitted DATA.
    origin.forbidden |= actors(value['authors']) | actors(value['operators']) | actors(CURRENT_CONTROL_ACTORS)
    for field in ('producerCaptureA', 'producerCaptureB'):
        nodes = value[field]
        actual = files.doc(nodes['result'])
        origin.forbidden |= actors(actual['authors']) | actors(actual['operators'])
        model_acceptance = files.doc(nodes['admissionModelAcceptance'])
        model = files.doc(model_acceptance['subject'])
        origin.forbidden |= actors(model['authors']) | actors(model['operators'])
    current_capture(files, value['producerCaptureA'], 'capture-a', origin, producer)
    current_capture(files, value['producerCaptureB'], 'capture-b', origin, producer)
    # Existing unchanged guard/component custody remains supplemental history;
    # none can replace either current capture or donate ordinary rows.
    equal(value['componentCarry'], producer['componentCarry'])
    component = files.doc(value['componentCarry'])
    for pair in component['modules']:
        equal(pair['classification'], 'BYTE_IDENTICAL')
        equal(files.read(pair['original']), files.read(pair['current']))
    need(type(value['unchangedScopes']) is list and len(value['unchangedScopes']) == 1, 'GUARD_CARRY_ONLY')
    carry = value['unchangedScopes'][0]
    closed(carry, 'name count oldSource currentSource actualResult acceptance meaning')
    equal(carry['name'], 'guard'); equal(carry['count'], 29)
    equal(carry['meaning'], 'BYTE_IDENTICAL_CARRY_NOT_NEW_EXECUTION')
    equal(files.read(carry['oldSource']), files.read(carry['currentSource']))
    for key in ('actualResult', 'acceptance'): files.read(carry[key])
    for key in ('source', 'actualControls', 'actualAcceptance', 'bridgeAcceptance'):
        if key in component['ordinaryBaseline']: files.read(component['ordinaryBaseline'][key])
    for key in ('source', 'actualControls', 'actualAcceptance', 'runtimeAcceptance'):
        if key in component['diagnosticBaseline']: files.read(component['diagnosticBaseline'][key])
    for d in component['functionProofs']: files.read(d)
    files.read(value['consumerSource']); files.read(value['consumerControls'])
    origin.reviews(descriptor, 'CONTROL')
    return value
