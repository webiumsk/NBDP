"""Producer4 current260 retained DATA verification; no execution or SDK walks.

Pure capture schema/parser code is vendored from accepted captureSOURCE4.
Raw proof metadata is checked against expected input pins; input snapshots are
not a fresh independent rehash of external SDK/APK/native inputs.
"""
from pathlib import Path
import json
from strict import closed,equal,hx,integer,json_bytes,need
import capture_contracts as c
from capture_outputs import parse_outcome
from witness import actors

COUNTS=[123,33,29,16,20,10,11,8,7,3]
SUBJECT_KEYS='schema authors operators state producerSource producerSourceAcceptance captureSource captureSourceAcceptance admissionDataAcceptance plan inputManifest rootAcknowledgement execution originalToolOrigin rawArtifactManifest countsSeparate allExpectedInputsUnchanged runtimeAuthorized helperExecutions ordinaryRowsQualified canonicalE02'


def review_pair(files,pins,subject,decision,forbidden):
    need(type(pins) is list and len(pins)==2,'TWO_ORDERED_INDEPENDENT_CURRENT_REVIEWS')
    values=[files.doc(p) for p in pins];c.reviews(values,pins,subject,decision,forbidden)
    return values


def root_acceptance(value,contract,subject,data):
    closed(value,' '.join(contract['closedKeys']))
    for key,expected in contract['literals'].items():equal(value[key],expected,'EXACT_ISSUED_CURRENT260_ROOT_ACCEPTANCE')
    equal(value['subject'],subject)
    for key in contract['pinKeys']:
        if key!='subject':equal(value[key],data[key],'ROOT_CURRENT260_EXACT_DATA_JOIN')
    return value


def validate_data(files,nodes,origin,producer_pin,source_acceptance,capture_pin,capture_acceptance,admission_acceptance,contract_pin):
    closed(nodes,'subject acceptance')
    need(all(x is not None for x in nodes.values()),'ACTUAL_CURRENT260_DATA_NODES_REQUIRED')
    data=files.doc(nodes['subject']);closed(data,SUBJECT_KEYS)
    equal(data['schema'],'e02-producer4-current-control-data-subject-v1');equal(data['producerSource'],producer_pin)
    for key,value in [('producerSourceAcceptance',source_acceptance),('captureSource',capture_pin),('captureSourceAcceptance',capture_acceptance),('admissionDataAcceptance',admission_acceptance),('countsSeparate',COUNTS),('allExpectedInputsUnchanged',True),('runtimeAuthorized',False),('helperExecutions',0),('ordinaryRowsQualified',0),('canonicalE02','PARTIAL22_UNCHANGED')]:equal(data[key],value,'CURRENT260_SUBJECT_SOURCE_AND_LIMIT_JOIN')
    equal(data['state'],'WRITES_STOPPED_PENDING_INDEPENDENT_DATA_QA_SECURITY')
    acceptance=files.doc(nodes['acceptance']);contract=files.doc(contract_pin)
    root_acceptance(acceptance,contract,nodes['subject'],data)
    producer=files.doc(producer_pin);method=files.doc(capture_pin)
    forbidden=set(origin.forbidden)|actors(data['authors'])|actors(data['operators'])|actors(producer['sourceContributors'])|{producer['author'],producer['coordinator'],producer['predecessorAuthor']}|actors(method['authors'])|set(c.REQUIRED_KNOWN_ACTORS)
    # Full union, including admission DATA creators/operators, is closed before
    # ANY new producer/capture/admission/current-DATA review pair is admitted.
    ack=files.doc(data['rootAcknowledgement'])
    adm=files.doc(ack['admissionData']);context=files.doc(ack['actorContext'])
    forbidden|=actors(adm['authors'])|actors(adm['operators'])|actors(ack['authors'])|actors(ack['operators'])|actors(context['participants'])
    origin.forbidden|=forbidden
    review_pair(files,acceptance['reviews'],nodes['subject'],contract['reviews']['decision'],forbidden)
    for key,value in [('producerSource',producer_pin),('producerSourceAcceptance',source_acceptance),('captureSource',capture_pin),('captureSourceAcceptance',capture_acceptance),('admissionDataAcceptance',admission_acceptance)]:equal(ack[key],value,'ACTUAL_ONCE_ACK_EXACT_CURRENT_SOURCE')
    records=dict(knownActors=files.doc(c.ROOT_KNOWN_ACTORS_PIN),producerAcceptance=files.doc(ack['producerSourceAcceptance']),captureAcceptance=files.doc(ack['captureSourceAcceptance']),admissionAcceptance=files.doc(ack['admissionDataAcceptance']),admissionSubject=adm)
    for key in ('producerReviews','captureReviews','admissionReviews'):records[key]=[files.doc(p) for p in ack[key]]
    control=files.doc(producer['controlPlan']);plan=files.doc(ack['plan']);manifest=files.doc(ack['inputManifest']);clock=files.doc(ack['clockSelection'])
    values,union=c.validate_acceptances(ack,producer,control,method,files.doc(ack['admissionPlan']),records,context)
    c.validate_plan(plan,ack,producer,control,method,manifest,clock);equal(values,COUNTS)
    for proof in context['participantProofs']:
        closed(proof,'actor authority selector');value=files.doc(proof['authority']);need(proof['selector'].startswith('/'),'ACTUAL_ACTOR_PROOF_POINTER')
        for token in proof['selector'][1:].split('/'):
            key=token.replace('~1','/').replace('~0','~');value=value[int(key)] if type(value) is list else value[key]
        equal(value,proof['actor'],'ACTUAL_KNOWN_PARTICIPANT_FIELD')
    equal(set(p['actor'] for p in context['participantProofs']),set(context['participants']))
    state=files.doc(ack['runtimeBindings']);closed(state,'schema readiness producerSource producerAcceptance captureSourceAcceptance admissionDataAcceptance rootAcknowledgement')
    for key,value in [('schema','e02-producer4-capture-runtime-bindings-v1'),('readiness',True),('producerSource',producer_pin),('producerAcceptance',source_acceptance),('captureSourceAcceptance',capture_acceptance),('admissionDataAcceptance',admission_acceptance),('rootAcknowledgement','EXTERNALLY_SHA_BOUND_AT_LAUNCH')]:equal(state[key],value)
    equal(files.doc(ack['requestContract']),c.request_template(plan,str(Path(capture_pin['path']).parent)))
    birth=files.doc(ack['sourceBirth']);equal(birth['schema'],'e02-root-producer4-source4-acceptance-lineage-v1');equal(birth['actor'],'/root');equal(birth['acceptance'],source_acceptance)
    execution=files.doc(data['execution'])
    equal(execution['schema'],'e02-producer4-current-control-execution-v1')
    for key in ('producerSource','captureSource','rootAcknowledgement','plan','inputManifest','countsSeparate'):equal(execution[key],data[key])
    for key,value in [('exitCode',0),('firstFault',None),('secondaryFaults',[]),('sourceUnchanged',True),('remainingNotExecuted',[]),('ordinaryRowsQualified',0),('canonicalE02','PARTIAL22_UNCHANGED')]:equal(execution[key],value,'ALL_TEN_EXACT_CURRENT_CONTROLS_ONLY')
    integer(execution['elapsedNs'],0,1200000000000);equal(len(execution['scopes']),10);equal(len(execution['outcomes']),10)
    before=files.doc(execution['overallBefore']);after=files.doc(execution['overallAfter']);equal(before,after,'ALL_CURRENT_EXPECTED_INPUTS_UNCHANGED')
    closed(before,'rows memberships snapshotNotRaceFree');equal(before['snapshotNotRaceFree'],True)
    indexed={r['pin']['path']:r for r in before['rows']};equal(len(indexed),len(before['rows']))
    required={x['pin']['path']:x['pin'] for x in manifest['files']}
    authority_keys='producerSource producerSourceAcceptance captureSource captureSourceAcceptance admissionPlan admissionData admissionDataAcceptance sourceBirth actorContext inputManifest plan clockSelection requestContract runtimeBindings'.split()
    for key in authority_keys:required[ack[key]['path']]=ack[key]
    for key in ('producerReviews','captureReviews','admissionReviews'):
        for p in ack[key]:required[p['path']]=p
    for p in [data['rootAcknowledgement'],c.ROOT_KNOWN_ACTORS_PIN,*[p['authority'] for p in context['participantProofs']],*[adm[k] for k in ('execution','originalToolOrigin','rawArtifactManifest','inputsBefore','inputsAfter')]]:required[p['path']]=p
    equal(set(indexed),set(required),'COMPLETE_EXPECTED_METADATA_AND_INPUT_SET')
    for path,pin in required.items():
        row=indexed[path];closed(row,'pin mode uid gid device inode mtimeNs ctimeNs');equal(row['pin'],pin)
        integer(row['mode'],0,4095);integer(row['uid']);integer(row['gid'])
        for k in ('device','inode','mtimeNs','ctimeNs'):c.need(type(row[k]) is str and row[k].isdigit(),'EXACT_CUSTODY_DECIMAL_IDENTITY')
    for item in manifest['files']:equal(indexed[item['pin']['path']]['mode'],item['mode'],'EXPECTED_FILE_MODE_NOT_OBSERVED_BASELINE')
    equal(before['memberships'],[dict(root=t['root'],membership=t['membership']) for t in manifest['fullTrees']]+[manifest['nodeDependencies']])
    raw_manifest=files.doc(data['rawArtifactManifest']);closed(raw_manifest,'schema files runtimeManifest originalToolOrigin');equal(raw_manifest['schema'],'e02-producer4-control-combined-raw-manifest-v1');equal(raw_manifest['originalToolOrigin'],data['originalToolOrigin'])
    raw_index={p['path']:p for p in raw_manifest['files']};equal(len(raw_index),len(raw_manifest['files']))
    for p in raw_manifest['files']:files.read(p)
    runtime_manifest=files.doc(raw_manifest['runtimeManifest']);closed(runtime_manifest,'schema files originalToolOrigin outerApiMeaning');equal(runtime_manifest['schema'],'e02-producer4-control-raw-artifact-manifest-v1');equal(runtime_manifest['originalToolOrigin'],None)
    equal(raw_manifest['files'],runtime_manifest['files']+[raw_manifest['runtimeManifest'],data['originalToolOrigin']])
    root=Path(plan['outputRoot']);equal(data['execution']['path'],str(root/'result.json'))
    for i,(scope,row,outcome) in enumerate(zip(plan['scopes'],execution['scopes'],execution['outcomes']),1):
        equal(row['scope'],scope['scope']);equal(row['argv'],scope['argv']);integer(row['elapsedNs'],0,63000000000)
        streams={}
        for name in ('stdout','stderr'):
            pin={k:v for k,v in row[name].items() if k!='mode'};equal(raw_index.get(pin['path']),pin);streams[name]=files.read(pin)
        equal(parse_outcome(scope,row,streams['stdout'],streams['stderr']),outcome,'RETAINED_RAW_CURRENT_SCOPE_VALIDATION')
        for tail in ('before','after'):
            p=raw_index[str(root/('%02d-%s.json'%(i,tail)))];equal(files.doc(p),before,'ALL20_EXPECTED_SCOPE_CUSTODY_SNAPSHOTS')
    api=c.decode_tool_origin(files.read(data['originalToolOrigin']))
    printed=c.validate_origin(api,c.expected_request(plan,data['rootAcknowledgement']['sha256'],str(Path(capture_pin['path']).parent)),ack['operators'])
    equal(json.loads(printed.strip()),dict(result=data['execution'],rawManifest=raw_manifest['runtimeManifest'],exitCode=0),'GENUINE_CURRENT_OUTER_API_TERMINAL_SUMMARY')
    return data
