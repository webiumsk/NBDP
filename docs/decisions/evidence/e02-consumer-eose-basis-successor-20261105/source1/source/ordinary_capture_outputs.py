"""Pure file-specific target output validators; no target execution."""
import re
from ordinary_capture_contracts import need,closed,EXTERNAL_NAMES
from strict import loads as decode_metadata
JS_SHAPES={
 'test_guard_client.mjs':dict(scope='PRODUCER4_MOCK_FRESH_GUARD_SCHEDULER_ONLY',keys='scope definitions executed realHelperExecuted realClockOrSDKObserved clientRowsQualified',false=['realHelperExecuted','realClockOrSDKObserved'],zero=['clientRowsQualified']),
 'test_guard_transport_boundaries.mjs':dict(scope='PRODUCER4_ACTUAL_REGISTERED_HELPER_CALLBACKS_AND_OWNED_SIGNAL_MOCKS_ONLY',keys='scope definitions executed realHelperExecuted realTimerObserved processReapAttested clientRowsQualified',false=['realHelperExecuted','realTimerObserved','processReapAttested'],zero=['clientRowsQualified']),
 'test_capture_allocation.mjs':dict(scope='PRODUCER4_PURE_CAPTURE_ALLOCATION_MODELS_ONLY',keys='scope definitions executed realWritesObserved realHelperExecuted wholeConsumerQualified atomicGlobalFenceClaimed',false=['realWritesObserved','realHelperExecuted','wholeConsumerQualified','atomicGlobalFenceClaimed'],zero=[]),
 'test_controller_emission.mjs':dict(scope='ACTUAL_PRODUCTION_CONTROLLER_EMITTER_WITH_FAKE_WRITER_ONLY',keys='scope checks realHelperExecuted realStdoutWritten clientRowsQualified',false=['realHelperExecuted','realStdoutWritten'],zero=['clientRowsQualified'])}

def parse_outcome(scope,result,stdout,stderr):
    need(not result.get('retentionErrors') and result['exitCode']==0 and result['reaped'] is True and result['eof']==dict(stdout=True,stderr=True) and result['fault'] is None and result['groupClosure'] is None and result['groupClosureFault'] is None,'NATURAL_EXACT_OWNED_SCOPE')
    count=scope['count'];name=scope['scope'];need(type(count) is int and count>0,'FINAL_COUNT_REQUIRED')
    if name.endswith('.py'):
        need(stdout==b'','QUIET_PYTHON_STDOUT_EMPTY')
        m=re.fullmatch(rb'([.]+)\n-{70}\nRan ([0-9]+) tests? in [^\n]+\n\nOK\n',stderr)
        need(m and len(m[1])==int(m[2])==count,'EXACT_QUIET_NO_SKIP_UNITTEST_COUNT')
        need(type(scope['definitionNames']) is list and len(scope['definitionNames'])==count and len(set(scope['definitionNames']))==count,'EXACT_SOURCE_DEFINED_METHODS')
        return dict(scope=name,count=count,membershipMeaning='QUIET_DOTS_COUNT_WITH_FROZEN_SOURCE_METHOD_NAMES_NOT_RAW_NAME_PRINTING',sourceNames=scope['definitionNames'],allOk=True)
    need(stderr==b'' and stdout.endswith(b'\n') and stdout.count(b'\n')==1,'ONE_COMPLETE_NODE_JSON_LINE')
    value=decode_metadata(stdout)
    if name=='fixtureEoseCaller':
        closed(value,'schema scope checks cases baselineFailureReproduced baselineFailure runtimeExecuted helperExecuted networkExecuted ordinaryRowsQualified canonicalE02')
        need(value['schema']=='e02-fixture-eose-pure-regression-result-v1' and value['scope']=='EXACT_SOURCE_CALLBACK_AND_UNCHANGED_GUARD_CORE_WITH_FAKE_TRANSPORT_AND_CLOCKS','EXACT_EXTERNAL_EOSE20_SCHEMA')
        need(type(value['checks']) is int and value['checks']==count==20 and value['cases']==scope['definitionNames']==list(EXTERNAL_NAMES),'EXACT_EXTERNAL_TWENTY_ORDERED_CASES')
        need(value['baselineFailureReproduced'] is True and value['baselineFailure']=='QUEUED_CONTEXT_CHANGED','ACTUAL_BASELINE_FAILURE_REPRODUCER')
        need(all(value[k] is False for k in ('runtimeExecuted','helperExecuted','networkExecuted')) and type(value['ordinaryRowsQualified']) is int and value['ordinaryRowsQualified']==0 and value['canonicalE02']=='PARTIAL22','EXTERNAL_PURE_LIMITS_NOT_RUNTIME')
        return dict(scope=name,count=count,membershipMeaning='EXACT_REAL_CALLBACK_WITH_SYNTHETIC_TRANSPORT_CLOCKS_NOT_NETWORK_OR_RUNTIME',sourceNames=value['cases'],actualNodeSummary=value,allOk=True)
    if name=='test_observation_model.mjs':
        closed(value,'schema ok checks cases scope');need(value['schema']=='e02-producer4-observation-model-controls-v1' and value['scope']=='SYNTHETIC_FS_SOCKET_GUARD_DATA_ONLY_NO_RUNTIME' and value['ok'] is True and value['checks']==count,'EXACT_OBSERVATION_MODEL_SHAPE');need(value['cases']==scope['definitionNames'] and len(value['cases'])==count,'ALL_SOURCE_NAMED_OBSERVATION_CASES')
    else:
        rule=JS_SHAPES[name];closed(value,rule['keys']);need(value['scope']==rule['scope'],'EXACT_NODE_SCOPE')
        for k in rule['false']:need(value[k] is False,'EXACT_FALSE_MODEL_LIMIT')
        for k in rule['zero']:need(type(value[k]) is int and value[k]==0,'NO_CLIENT_QUALIFICATION')
        if name=='test_controller_emission.mjs':need(value['checks']==count,'EXACT_CONTROLLER_SUCCESS_LOOP_COUNT')
        else:need(value['definitions']==value['executed']==count,'ALL_REVIEWED_DEFINITIONS_SUCCESS_LOOP')
    return dict(scope=name,count=count,membershipMeaning='FROZEN_SCRIPT_ALL_BODIES_SUCCESS_LOOP_PLUS_EXACT_STDOUT_NOT_INDEPENDENT_PER_BODY_ATTESTATION',actualNodeSummary=value,allOk=True)

