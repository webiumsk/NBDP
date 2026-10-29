"""Accepted helper-probe prerequisite DATA only, with explicit bounded RAW list.

This reader follows only fields named by the Root fixed contracts. It never
walks arbitrary descriptors or interprets the external collector's ledger.
"""
import shlex
from pathlib import Path
from strict import closed,equal,hx,integer,need,pin_shape
import capture_contracts as c
from witness import actors


def expected_request(data,controller):
    host=next(d for d in controller['runtimeSources'] if Path(d['path']).name=='host.py')
    plan=data['concretePlan'];release=data['rootRelease']
    argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
        '/usr/bin/timeout','--signal=KILL','183s','/home/peterhorvath/.miniforge3/bin/python3.13',
        '-I','-B',host['path'],'--plan',plan['path'],'--plan-sha',plan['sha256'],
        '--root-release',release['path'],'--root-release-sha',release['sha256']]
    return dict(cmd=shlex.join(argv),workdir=str(Path(host['path']).parent),login=False,yield_time_ms=1000,max_output_tokens=2000)


def participant_union(files,data,forbidden):
    result=set(forbidden)|set(c.REQUIRED_KNOWN_ACTORS)|actors(data['authors'])|actors(data['operators'])
    docs=[files.doc(data['controllerSource']),files.doc(data['rootRelease'])]
    for key in ('controllerSourceAcceptance','controllerControlDataAcceptance','collectorSourceAcceptance','collectorControlDataAcceptance'):
        acceptance=files.doc(data[key]);docs.append(acceptance)
        need('subject' in acceptance,'EXPLICIT_ACCEPTED_PREREQUISITE_SUBJECT')
        docs.append(files.doc(acceptance['subject']))
    for doc in docs:
        declared=False
        for key in ('authors','operators','sourceContributors'):
            if key in doc:result|=actors(doc[key]);declared=True
        for key in ('actor','author','coordinator'):
            if key in doc:result|=actors([doc[key]]);declared=True
        need(declared,'UNKNOWN_PREREQUISITE_ACTORS_NOT_EMPTY')
    return result


def validate(files,nodes,origin,producer_source,producer_acceptance,acceptance_contract,shape_contract):
    closed(nodes,'subject acceptance');need(all(x is not None for x in nodes.values()),'ACTUAL_ACCEPTED_HELPER_PROBE_REQUIRED')
    contract=files.doc(acceptance_contract);shape=files.doc(shape_contract)
    data=files.doc(nodes['subject']);closed(data,' '.join(shape['subjectClosedKeys']))
    for k,v in shape['subjectLiterals'].items():equal(data[k],v,'EXACT_HELPER_PROBE_DATA_ONLY')
    equal(data['producerSource'],producer_source);equal(data['producerDataAcceptance'],producer_acceptance)
    for key in shape['subjectPinKeys']:c.pin(data[key])
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
    c.validate_origin(api,expected_request(data,controller),data['operators'])
    # The outer API terminal is distinct from actual host Popen/guest child facts.
    return data
