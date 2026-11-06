"""Accepted helper-probe prerequisite DATA only, with explicit bounded RAW list.

This reader follows only fields named by the Root fixed contracts. It never
walks arbitrary descriptors or interprets the external collector's ledger.
"""
import shlex
from pathlib import Path
from strict import closed,equal,hx,integer,need,pin_shape,text
import capture_contracts as c
import request_families as families
from witness import actors


def expected_request(data,controller):
    host=next(d for d in controller['runtimeSources'] if Path(d['path']).name=='host.py')
    plan=data['concretePlan'];release=data['rootRelease']
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
        '/usr/bin/timeout','--signal=KILL','183s','/home/peterhorvath/.miniforge3/bin/python3.13',
        '-I','-B',host['path'],'--plan',plan['path'],'--plan-sha',plan['sha256'],
        '--root-release',release['path'],'--root-release-sha',release['sha256']]
    return dict(cmd=shlex.join(argv),workdir=str(Path(host['path']).parent),login=False,yield_time_ms=1000,max_output_tokens=2000,**families.HOST_POLICY)


def source_actors(value):
    """Typed known SOURCE roles; an explicit empty operator list is not DATA."""
    schema=value.get('schema')
    if schema in ('e02-one-cid-helper-probe-controller-source-v1','e02-ordinary-consumer6-source-subject-v1'):
        need(all(k in value for k in ('author','coordinator','sourceContributors','operators')),'KNOWN_SOURCE_CREATORS_AND_OPERATOR_DECLARATION')
        creators=actors([value['author']])|actors([value['coordinator']])|actors(value['sourceContributors'])
        need(type(value['operators']) is list,'EXPLICIT_KNOWN_SOURCE_OPERATOR_LIST')
        return creators|(actors(value['operators']) if value['operators'] else set())
    if schema=='e02-probe-root-custody-collector-source-subject-v1':
        # This closed CODE-only source format declares authors, not executions.
        equal(value.get('codeOnly'),True,'COLLECTOR_CODE_ONLY_SOURCE')
        creators=actors(value.get('authors'))
        need('operators' not in value or value['operators']==[],'NO_UNDECLARED_COLLECTOR_SOURCE_EXECUTION')
        return creators
    if schema == 'e02-collector-actual-request7-typed-origin-composite-source-subject-v2':
        equal(value.get('executionAuthorized'), False, 'COLLECTOR_COMPOSITE_SOURCE_ONLY')
        need(type(value.get('sourceContributorUnion')) is list and value['sourceContributorUnion'], 'DECLARED_COMPOSITE_COLLECTOR_CREATORS')
        creators = actors(value['sourceContributorUnion'])
        need(value.get('actor') in creators, 'COMPOSITE_ACTOR_IN_UNION')
        return creators
    need(False,'UNKNOWN_SOURCE_ACTOR_SCHEMA')


def data_actors(value):
    need('authors' in value and 'operators' in value,'DECLARED_DATA_AUTHORS_AND_OPERATORS')
    return actors(value['authors'])|actors(value['operators'])


def participant_union(files,data,forbidden):
    result=set(forbidden)|set(c.REQUIRED_KNOWN_ACTORS)|data_actors(data)
    result|=source_actors(files.doc(data['controllerSource']))
    result|=data_actors(files.doc(data['rootRelease']))
    for key,kind in [('controllerSourceAcceptance','SOURCE'),('controllerControlDataAcceptance','DATA'),('collectorSourceAcceptance','SOURCE'),('collectorControlDataAcceptance','DATA')]:
        accepted=files.doc(data[key]);need('subject' in accepted and accepted.get('actor')=='/root','EXPLICIT_ROOT_ACCEPTED_PREREQUISITE_SUBJECT')
        result|=actors([accepted['actor']]);value=files.doc(accepted['subject'])
        result|=source_actors(value) if kind=='SOURCE' else data_actors(value)
    return result


def validate(files,nodes,origin,producer_source,producer_acceptance,acceptance_contract,shape_contract,expected_controller=None):
    closed(nodes,'subject acceptance');need(all(x is not None for x in nodes.values()),'ACTUAL_ACCEPTED_HELPER_PROBE_REQUIRED')
    contract=files.doc(acceptance_contract);shape=files.doc(shape_contract)
    data=files.doc(nodes['subject']);closed(data,' '.join(shape['subjectClosedKeys']))
    for k,v in shape['subjectLiterals'].items():equal(data[k],v,'EXACT_HELPER_PROBE_DATA_ONLY')
    equal(data['producerSource'],producer_source);equal(data['producerDataAcceptance'],producer_acceptance)
    for key in shape['subjectPinKeys']:c.pin(data[key])
    if expected_controller is not None:
        for key,expected in [('controllerSource',expected_controller['source']),('controllerSourceAcceptance',expected_controller['sourceAcceptance']),('controllerControlDataAcceptance',expected_controller['controlAcceptance'])]:equal(data[key],expected,'EXACT_EXTERNALLY_SELECTED_CURRENT_CONTROLLER_TRIPLE')
    controller=files.doc(data['controllerSource'])
    equal(controller['schema'],'e02-one-cid-helper-probe-controller-source-v1')
    equal(controller['runtimeSourceCount'],3);equal(controller['guestProbeSourceCount'],8)
    equal(controller['upstreamProducerSubject'],producer_source)
    forbidden=participant_union(files,data,origin.forbidden)
    origin.forbidden|=forbidden
    acceptance=files.doc(nodes['acceptance']);closed(acceptance,' '.join(contract['closedKeys']))
    for k,v in contract['literals'].items():equal(acceptance[k],v,'EXACT_ISSUED_HELPER_PROBE_ROOT_DATA_ACCEPTANCE')
    equal(acceptance['subject'],nodes['subject'])
    for key in contract['pinKeys']:
        if key!='subject':equal(acceptance[key],data[key],'ROOT_HELPER_PROBE_CURRENT_DATA_JOIN')
    from current_controls import review_pair
    review_pair(files,acceptance['reviews'],nodes['subject'],contract['reviews']['decision'],forbidden)
    release=files.doc(data['rootRelease']);plan=files.doc(data['concretePlan'])
    equal(release['schema'],'e02-one-cid-helper-probe-root-release-v1');equal(release['actor'],'/root');equal(release['executionAuthorized'],True)
    equal(release['subject'],data['controllerSource']);equal(release['plan'],data['concretePlan']);equal(release['runId'],plan['runId'])
    equal(release['creationNonce'],plan['creationNonce']);equal(release['outerCustodyReservationBytes'],65536)
    result=files.doc(data['execution'])
    closed(result,'schema qualified error secondaryErrors cid cleanup chargedPhysicalBytes childEvidence outerApiEvidence ordinaryRowsQualified backendCause')
    for k,v in [('schema','e02-one-cid-helper-probe-result-v1'),('qualified',True),('error',None),('secondaryErrors',[]),('childEvidence','ACTUAL_HOST_POPEN_ONLY'),('outerApiEvidence',None),('ordinaryRowsQualified',0),('backendCause','UNKNOWN')]:equal(result[k],v,'ONE_QUALIFIED_HELPER_PROBE_ONLY')
    hx(result['cid']);closed(result['cleanup'],'removed absence unknownIdentity');equal(result['cleanup'],dict(removed=True,absence=True,unknownIdentity=False),'EXACT_OWNED_PROBE_REMOVED_ABSENT')
    closed(result['chargedPhysicalBytes'],'attached metadata')
    manifest=files.doc(data['rawArtifactManifest']);closed(manifest,' '.join(shape['rawManifestClosedKeys']))
    equal(manifest['schema'],shape['rawManifestSchema']);equal(manifest['originalToolOrigin'],data['originalToolOrigin'])
    accounting=manifest['accounting'];closed(accounting,' '.join(shape['accountingClosedKeys']))
    charged=accounting['controllerChargedBytes'];closed(charged,' '.join(shape['controllerChargedBytesClosedKeys']))
    equal(accounting['rootExternalReservationBytes'],65536)
    for key in ('attached','metadata'):
        integer(charged[key],0,8388608);integer(result['chargedPhysicalBytes'][key],0,8388608)
    need(sum(charged.values())<=16777216 and charged['metadata']>=65536,'SAME_PHYSICAL16MiB_ROOT_RESERVATION_INSIDE_METADATA')
    equal(charged['attached'],result['chargedPhysicalBytes']['attached'])
    equal(charged['metadata'],result['chargedPhysicalBytes']['metadata']+data['execution']['bytes'],'FINAL_RESULT_PRECHARGE_WITHOUT_REFUND')
    need(type(manifest['files']) is list and 1<=len(manifest['files'])<=20000,'FINITE_EXPLICIT_SELECTED_PROOF')
    index={d['path']:d for d in manifest['files']};equal(len(index),len(manifest['files']),'UNIQUE_PHYSICAL_PROOF_PINS')
    need(data['rawArtifactManifest']['path'] not in index,'RAW_MANIFEST_NO_SELF_CYCLE')
    for p in (data['execution'],data['originalToolOrigin']):equal(index.get(p['path']),p,'EXECUTION_AND_API_ORIGIN_IN_SELECTED_PROOF')
    total=0
    for d in manifest['files']:c.pin(d);total+=files.verify_raw(d)
    need(total<=sum(charged.values()),'SELECTED_PHYSICAL_PROOF_WITHIN_SAME_CHARGED_TOTAL')
    api=c.decode_tool_origin(files.read(data['originalToolOrigin']))
    c.validate_origin(api,expected_request(data,controller),data['operators'],family='HOST7')
    # The outer API terminal is distinct from actual host Popen/guest child facts.
    return data


def controller_profile(files,descriptor,producer_source):
    """Externally selected controller CODE/AST closure; no version/count hardpin."""
    import ast
    source=files.doc(descriptor);equal(source['schema'],'e02-one-cid-helper-probe-controller-source-v1')
    source_actors(source)
    equal(source['upstreamProducerSubject'],producer_source)
    equal(source['upstreamProducerRuntimeWorkerCount'],22);equal(source['upstreamProducerModelsDefined'],266)
    declared=source['sources'];need(type(declared) is list and 1<=len(declared)<=20000,'FINITE_CURRENT_CONTROLLER_CODE')
    by_path={p['path']:p for p in declared};equal(len(by_path),len(declared));equal(source['sourceCount'],len(declared))
    bodies={}
    for p in declared:pin_shape(p);bodies[p['path']]=files.read(p)
    runtime=source['runtimeSources'];guest=source['guestProbeSources']
    equal(source['runtimeSourceCount'],3);equal(len(runtime),3)
    equal({Path(p['path']).name for p in runtime},{'controller.py','host.py','finite_child.py'})
    equal(source['guestProbeSourceCount'],8);equal(len(guest),8)
    expected_guest=('probe-guard-helper.mjs','guard-client.mjs','guard-client-core.mjs','guard-wire.mjs','guard-helper.py','lease_guard.py','capture-allocation.mjs','guard-transport-boundaries.mjs')
    producer=files.doc(producer_source);producer_names={Path(p['path']).name:p for p in producer['sources']}
    equal(guest,[producer_names[name] for name in expected_guest],'SAME_CURRENT_PRODUCER_EIGHT_GUEST_SOURCES')
    for p in runtime+guest:equal(by_path.get(p['path']),p,'ALL_CURRENT_RUNTIME_AND_GUEST_CODE_MEMBERS')
    plan=files.doc(source['controlPlan']);equal(plan['schema'],'e02-one-cid-helper-probe-controller-controls-v1')
    groups=plan['groups'];need(type(groups) is list and groups and len({g['name'] for g in groups})==len(groups),'COMPLETE_ORDERED_CURRENT_CONTROLLER_GROUPS')
    counts=[]
    for group in groups:
        closed(group,'name source format argv cwd count expectedNames')
        p=group['source'];equal(by_path.get(p['path']),p,'CURRENT_CONTROLLER_TEST_SOURCE_MEMBER')
        tree=ast.parse(bodies[p['path']],filename=p['path'])
        names=[cls.name+'.'+method.name for cls in tree.body if isinstance(cls,ast.ClassDef) for method in cls.body if isinstance(method,ast.FunctionDef) and method.name.startswith('test_')]
        equal(group['expectedNames'],names,'CURRENT_CONTROLLER_AST_NAMES');integer(group['count'],1,10000);equal(group['count'],len(names))
        equal(group['format'],'VERBOSE_UNITTEST_NAMED')
        # The reviewed plan may run a current script from a predecessor model
        # root. Honor its exact cwd; never derive or rewrite it from the script.
        # A declared member beneath cwd was read above via Files.read's
        # O_NOFOLLOW ancestor walk, so this is not an unverified directory alias.
        import re
        version=re.fullmatch(r'r([1-9][0-9]{0,3})',source['version'])
        need(version is not None,'CURRENT_CONTROLLER_VERSION_FOR_MODEL_ROOT')
        cwd=Path(text(group['cwd'],4096))
        need(cwd.is_absolute() and str(cwd)==group['cwd'] and '..' not in cwd.parts,
             'CANONICAL_CURRENT_CONTROLLER_MODEL_CWD')
        prefix='/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r'
        revision=re.fullmatch(re.escape(prefix)+r'([1-9][0-9]{0,3})',group['cwd'])
        need(revision is not None and 1<=int(revision[1])<=int(version[1]),
             'SCOPED_CURRENT_OR_PREDECESSOR_CONTROLLER_MODEL_ROOT')
        need(any(Path(member).parent==cwd for member in by_path),
             'CONTROLLER_CWD_BACKED_BY_VERIFIED_DECLARED_MEMBER')
        base=['/home/peterhorvath/.miniforge3/bin/python3.13','-I','-B',p['path']]
        need(group['argv'] in (base,base+['-v']),'EXACT_CURRENT_CONTROLLER_MODEL_ARGV')
        counts.append(group['count'])
    total=sum(counts);equal(source['modelsDefined'],total);equal(source['modelGroups'],len(groups))
    equal(source['modelsExecuted'],0);equal(source['helperExecutions'],0);equal(source['probeExecutions'],0)
    return source,plan,counts,total


def controller_request(group):
    argv=list(group['argv'])
    if argv[-1]!='-v':argv.append('-v')
    cmd=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','63s',*argv]
    return dict(cmd=shlex.join(cmd),workdir=group['cwd'],login=False,yield_time_ms=1000,max_output_tokens=20000)


def controller_snapshot(raw,total):
    """Only these typed row time paths admit signed64; no global JSON widening."""
    import re
    from strict import loads,I64,SAFE
    value=loads(raw);closed(value,'schema actor rows')
    equal(value['schema'],'e02-controller'+str(total)+'-current-inputs-v1');equal(value['actor'],'/root')
    need(type(value['rows']) is list and value['rows'],'NONEMPTY_CONTROLLER_EXPECTED_INPUTS')
    rows={row['pin']['path']:row for row in value['rows']};equal(len(rows),len(value['rows']))
    for row in value['rows']:
        closed(row,'pin mode uid gid device inode mtimeNs ctimeNs');pin_shape(row['pin'])
        need(type(row['mode']) is str and re.fullmatch(r'0o[0-7]{3,4}',row['mode']),'CONTROLLER_SNAPSHOT_MODE')
        for key in ('uid','gid','device','inode'):integer(row[key],0,SAFE)
        for key in ('mtimeNs','ctimeNs'):integer(row[key],0,I64)
    return value,rows


def validate_controller_authority(files,triple,producer_source,contract_pin,forbidden):
    """Current controller Source14/controlDATA20, exact externally selected triple."""
    closed(triple,'controllerSource controllerSourceAcceptance controllerControlDataAcceptance')
    for p in triple.values():pin_shape(p)
    contract=files.doc(contract_pin)
    source,plan,counts,total=controller_profile(files,triple['controllerSource'],producer_source)
    source_acceptance=files.doc(triple['controllerSourceAcceptance'])
    acceptance=files.doc(triple['controllerControlDataAcceptance']);data=files.doc(acceptance['subject'])
    union=set(forbidden)|source_actors(source)|data_actors(data)
    src=contract['source'];closed(source_acceptance,' '.join(src['closedKeys']))
    for key,value in src['literals'].items():equal(source_acceptance[key],value,'EXACT_TYPED_CURRENT_CONTROLLER_SOURCE_ACCEPTANCE')
    for key,value in [('subject',triple['controllerSource']),('modelsDefined',total),('modelGroups',len(counts))]:equal(source_acceptance[key],value,'CURRENT_CONTROLLER_SOURCE_PARTITION_JOIN')
    c.reviews([files.doc(p) for p in source_acceptance['reviews']],source_acceptance['reviews'],triple['controllerSource'],src['reviewDecision'],union)
    rule=contract['data'];closed(acceptance,' '.join(rule['closedKeys']))
    for key,value in rule['literals'].items():equal(acceptance[key],value,'EXACT_TYPED_CURRENT_CONTROLLER_DATA_ACCEPTANCE')
    for key,value in [('controllerSource',triple['controllerSource']),('controllerSourceAcceptance',triple['controllerSourceAcceptance']),('controlPlan',source['controlPlan']),('countsSeparate',counts),('modelsDefined',total),('modelsExecuted',total),('modelsPassed',total)]:equal(acceptance[key],value,'CURRENT_CONTROLLER_DATA_SOURCE_AND_PARTITION_JOIN')
    equal(data['schema'],rule['subjectSchema'])
    for key,value in [('controllerSource',triple['controllerSource']),('controllerSourceAcceptance',triple['controllerSourceAcceptance']),('controlPlan',source['controlPlan']),('countsSeparate',counts),('modelsDefined',total),('modelsExecuted',total),('modelsPassed',total),('modelsFailed',0),('skipped',0),('truncated',False),('inputsUnchanged',True),('guardHelperExecutions',0),('dockerExecutions',0),('ordinaryRoleExecutions',0),('ordinaryRowsQualified',0),('innerPidReapEofAttested',False),('executionAuthorized',False)]:equal(data[key],value,'COMPLETE_CURRENT_CONTROLLER_MODEL_DATA')
    c.reviews([files.doc(p) for p in acceptance['reviews']],acceptance['reviews'],acceptance['subject'],rule['reviewDecision'],union)
    execution=files.doc(data['execution'])
    closed(execution,'schema actor groups modelsDefined modelsExecuted modelsPassed modelsFailed skipped truncated inputsUnchanged protectedInputs actualApiOnly innerPidReapEofAttested guardHelperExecutions dockerExecutions ordinaryRoleExecutions')
    equal(execution['schema'],'e02-probe-controller-'+source['version'].lower()+'-'+str(total)+'-mock-execution-v1')
    for key,value in [('actor','/root'),('modelsDefined',total),('modelsExecuted',total),('modelsPassed',total),('modelsFailed',0),('skipped',0),('truncated',False),('inputsUnchanged',True),('actualApiOnly',True),('innerPidReapEofAttested',False),('guardHelperExecutions',0),('dockerExecutions',0),('ordinaryRoleExecutions',0)]:equal(execution[key],value,'CURRENT_CONTROLLER_API_ONLY_EXECUTION')
    before,rows=controller_snapshot(files.read(data['inputsBefore']),total)
    after,_=controller_snapshot(files.read(data['inputsAfter']),total);equal(before,after,'CURRENT_CONTROLLER_INPUTS_UNCHANGED')
    equal(execution['protectedInputs'],len(rows))
    for p in [*source['sources'],triple['controllerSource'],triple['controllerSourceAcceptance'],source['controlPlan']]:need(p['path'] in rows,'ALL_CURRENT_CONTROLLER_CODE_AND_AUTHORITY_INPUTS');equal(rows[p['path']]['pin'],p,'EXPECTED_CURRENT_CONTROLLER_INPUT_HASH')
    manifest=files.doc(data['rawArtifactManifest']);closed(manifest,'schema actor files semantics')
    equal(manifest['schema'],'e02-controller'+str(total)+'-mock-raw-artifact-manifest-v1');equal(manifest['actor'],'/root')
    need(type(manifest['files']) is list and 1<=len(manifest['files'])<=20000,'FINITE_CURRENT_CONTROLLER_RAW_PROOF')
    members={p['path']:p for p in manifest['files']};equal(len(members),len(manifest['files']))
    for p in manifest['files']:files.read(p)
    for p in (data['execution'],data['inputsBefore'],data['inputsAfter']):equal(members.get(p['path']),p,'CONTROLLER_RAW_MANIFEST_CLOSURE')
    groups=execution['groups'];equal(len(groups),len(plan['groups']));equal(len(data['originalToolOrigins']),len(groups))
    from consumer import named_unittest_output
    for expected,row,origin_pin in zip(plan['groups'],groups,data['originalToolOrigins']):
        closed(row,'group modelsExecuted modelsPassed modelsFailed actualNames reportedSeconds terminalExitCode originalToolOrigin rawOutput')
        for key,value in [('group',expected['name']),('modelsExecuted',expected['count']),('modelsPassed',expected['count']),('modelsFailed',0),('actualNames',sorted(expected['expectedNames'])),('terminalExitCode',0),('originalToolOrigin',origin_pin)]:equal(row[key],value,'ALL_CURRENT_CONTROLLER_NAMED_GROUPS')
        for p in (origin_pin,row['rawOutput']):equal(members.get(p['path']),p,'ALL_CURRENT_CONTROLLER_API_AND_OUTPUT_MEMBERS')
        api=c.decode_tool_origin(files.read(origin_pin));actual=c.validate_origin(api,controller_request(expected),data['operators'],family='MODEL5').encode('utf8')
        equal(files.read(row['rawOutput']),actual,'GENUINE_CURRENT_CONTROLLER_API_OUTPUT')
        named_unittest_output(actual,dict(count=expected['count'],definitionNames=expected['expectedNames']))
    return source,plan,counts,total,union


def validate_collector_origin(raw, expected, operators=('/root',)):
    """Collector-specific CLI and strict present-counter family, no dispatch."""
    import collector_contracts as collector
    api = c.decode_tool_origin(raw)
    output = c.validate_origin(api, expected, operators, family='COLLECTOR7')
    words, _ = collector.command_words(expected)
    need(len(words) >= 7, 'COMPLETE_COLLECTOR_COMMAND')
    collector.command(expected, words[6])
    return collector.output_object(output)


def validate_collector_authority(files, contract_pin, forbidden):
    """Read accepted Source2/81 prerequisites; no operational collector proof.

    Each historical prerequisite review is checked against that prerequisite's
    complete creators/operators. Their receipt actors join the returned union
    before any later helper/consumer review. Later authors cannot retroactively
    invalidate a genuinely accepted earlier prerequisite review.
    """
    import ast
    import re
    contract=files.doc(contract_pin)
    equal(contract['schema'],'e02-current-collector-source2-prerequisite-contract-v1')
    equal(contract['executionAuthorized'],False)
    source=files.doc(contract['source']);data=files.doc(contract['data'])
    local_union=source_actors(source)|data_actors(data)|{'/root'}
    src=files.doc(contract['sourceAcceptance']);accepted=files.doc(contract['dataAcceptance'])
    closed(src,' '.join(contract['sourceAcceptanceClosedKeys']))
    closed(data,' '.join(contract['dataClosedKeys']))
    closed(accepted,' '.join(contract['dataAcceptanceClosedKeys']))
    for obj,decision,scope in ((src,contract['sourceDecision'],contract['sourceScope']),
                               (accepted,contract['dataDecision'],contract['dataScope'])):
        equal(obj['actor'],'/root');equal(obj['decision'],decision);equal(obj['scope'],scope)
        equal(obj['executionAuthorized'],False)
    equal(src['schema'],'e02-root-custody-collector-source-acceptance-v1')
    equal(src['subject'],contract['source']);equal(src['modelsExecuted'],0)
    equal(src['actualCollectorCommands'],0);equal(src['actualProbeExecutions'],0)
    equal(accepted['schema'],'e02-root-custody-collector-control-data-acceptance-v1')
    equal(accepted['subject'],contract['data'])
    for key,value in [('collectorSource',contract['source']),('collectorSourceAcceptance',contract['sourceAcceptance']),
                      ('controlPlan',contract['controlPlan'])]:
        equal(data[key],value);equal(accepted[key],value)
    equal(data['schema'],'e02-root-custody-collector-mock-control-data-subject-v1')
    for key,value in [('modelsFailed',0),('skipped',0),('inputsUnchanged',True),
                      ('actualReleasedCollectorCommands',0),('actualProbeExecutions',0),
                      ('ordinaryRoleExecutions',0),('executionAuthorized',False)]:
        equal(data[key],value);equal(accepted[key],value)
    equal(data['truncated'],False);equal(data['innerPidReapEofAttested'],False)
    by_path={p['path']:p for p in source['sources']}
    equal(len(by_path),len(source['sources']))
    for p in source['sources']:files.read(p)
    for key,source_key in [('qualifier','operationalQualifier'),('history','historyPrefixSource'),
                           ('codec','losslessPerOriginCodec')]:
        equal(source[source_key],contract[key]);equal(by_path.get(contract[key]['path']),contract[key])
    equal(source['operationalCollector'],contract['operationalCollector']);files.read(contract['operationalCollector'])
    equal(by_path.get(contract['controlPlan']['path']),contract['controlPlan'])
    plan=files.doc(contract['controlPlan']);names=[]
    for group in plan['groups']:
        closed(group,'source defined caseNames')
        equal(by_path.get(group['source']['path']),group['source'])
        tree=ast.parse(files.read(group['source']),filename=group['source']['path'])
        actual=[cls.name+'.'+method.name for cls in tree.body if isinstance(cls,ast.ClassDef)
                for method in cls.body if isinstance(method,ast.FunctionDef) and method.name.startswith('test_')]
        equal(group['caseNames'],sorted(actual));equal(group['defined'],len(actual));names.extend(sorted(actual))
    equal(len(names),len(set(names)));equal(plan['caseNames'],names)
    total=len(names);need(total>0,'CURRENT_COLLECTOR_AST_PARTITION')
    for obj in (source,src,data,accepted):equal(obj['modelsDefined'],total)
    equal(source['modelsExecuted'],0);equal(source['executionAuthorized'],False)
    for obj in (data,accepted):equal(obj['modelsExecuted'],total);equal(obj['modelsPassed'],total)
    # Both review pairs see the complete actual component union first.
    c.reviews([files.doc(p) for p in src['reviews']],src['reviews'],contract['source'],contract['sourceReviewDecision'],local_union)
    c.reviews([files.doc(p) for p in accepted['reviews']],accepted['reviews'],contract['data'],contract['dataReviewDecision'],local_union)
    manifest=files.doc(contract['rawManifest']);closed(manifest,'schema files modelsExecuted operationalCollectorCommands helperExecutions')
    equal(manifest['schema'],'e02-current-model-raw-artifact-manifest-v1')
    equal(manifest['files'],contract['rawFiles']);equal(manifest['modelsExecuted'],total)
    equal(manifest['operationalCollectorCommands'],0);equal(manifest['helperExecutions'],0)
    raw_index={p['path']:p for p in manifest['files']};equal(len(raw_index),len(manifest['files']))
    for p in manifest['files']:files.read(p)
    for key in ('execution','originalToolOrigin','inputsBefore','inputsAfter','rootRelease'):
        equal(raw_index.get(data[key]['path']),data[key])
    equal(data['execution'],contract['execution']);equal(data['rawArtifactManifest'],contract['rawManifest'])
    # RAW execution remains exactly pinned, including its scientific report
    # duration. The only API floats decoded below are native wall metadata.
    files.read(contract['execution'])
    before=files.doc(data['inputsBefore']);after=files.doc(data['inputsAfter']);equal(before,after)
    closed(before,'schema rows');equal(before['schema'],'e02-current-model-protected-input-snapshot-v1')
    rows={r['pin']['path']:r for r in before['rows']};equal(len(rows),len(before['rows']))
    for row in before['rows']:
        closed(row,'pin mode owner device inode');pin_shape(row['pin'])
        need(type(row['mode']) is str and re.fullmatch(r'0o[0-7]{3,4}',row['mode']),'TYPED_COLLECTOR_SNAPSHOT_MODE')
        need(type(row['owner']) is list and len(row['owner'])==2,'TYPED_COLLECTOR_SNAPSHOT_OWNER')
        for v in [*row['owner'],row['device'],row['inode']]:integer(v)
    for p in [*source['sources'],contract['source'],contract['sourceAcceptance']]:
        need(p['path'] in rows,'ALL_CURRENT_COLLECTOR_CODE_INPUTS');equal(rows[p['path']]['pin'],p)
    api=c.decode_tool_origin(files.read(data['originalToolOrigin']))
    equal(c.validate_origin(api,contract['modelRequest'],data['operators'],family='MODEL5'),'')
    equal(files.read(contract['stdout']),b'')
    raw=files.read(contract['stderr']);text_value=raw.decode('utf8','strict')
    trailer=re.search(r'\n\n-{70}\nRan ([0-9]+) tests? in [0-9]+(?:\.[0-9]+)?s\n\nOK\n\Z',text_value)
    need(trailer is not None and int(trailer[1])==total,'COMPLETE_CURRENT_COLLECTOR_NAMED_TRAILER')
    observed=[]
    for line in text_value[:trailer.start()].splitlines():
        m=re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*) \(([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_][A-Za-z_0-9]*)\) \.\.\. ok',line)
        need(m is not None and m[1]==m[4],'EVERY_CURRENT_COLLECTOR_NAMED_SUCCESS')
        observed.append(m[3]+'.'+m[4])
    equal(observed,names,'ALL_CURRENT_COLLECTOR_AST_NAMES_ONCE')
    receipt_actors={files.doc(p)['session'] for p in [*src['reviews'],*accepted['reviews']]}
    return set(forbidden)|local_union|receipt_actors
