"""Finish SOURCE metadata only; no target imports, model/control/test or grants."""
import json
from pathlib import Path
import runpy
import shlex

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
DATA=Path('/Data/nbdp-e02-tooling-20261027/producer-controls-preparation-r3-source4')
OUT=ROOT/'docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source4'
PREP=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2'


def main():
    own=runpy.run_path(str(DATA/'assemble-source-only.py'),run_name='source_metadata_helpers_only')
    pin=own['pin'];load=own['load'];save=own['save']
    python=load(PREP/'control-plan.json')['python']
    contract=pin(ROOT/'docs/decisions/evidence/e02-producer3-data-contract-20261028/contract.json')
    captures={};scopes={}
    leaves=[pin(OUT/name) for name in ('capture-template.py','assemble-source-only.py','test_admission_models.py','prepare-final-source.py')]
    leaves.extend([pin(DATA/'finalize-source-packet.py'),pin(OUT/'freeze-input-spec.json'),contract,
        pin(PREP/'source-acceptance.json'),pin(OUT/'request-from-plan.py'),
        pin(ROOT/'docs/decisions/evidence/e02-producer3-data-contract-20261028/summary-types.json'),
        pin(ROOT/'docs/decisions/evidence/e02-producer3-data-contract-20261028/model-subject-contract.json')])
    for mode in ('capture-a','capture-b'):
        base=OUT/mode;plan=load(base/'control-plan.json')
        # Plans are source-construction outputs and are frozen by the subjects
        # below only after this explicit metadata-finalization step.
        prefix=[python['path'],'-I','-B',str(base/'capture-controls.py'),'--execute-once','--root-ack-sha']
        argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
            '/usr/bin/timeout','--signal=KILL','297',*prefix,'__ACTUAL_ROOT_ACK_SHA256__']
        plan['onceCommandPrefix']=prefix
        plan['sourceGeneration']='SOURCE4'
        plan['freshCaptureRootId']='e02-producer3-source4-'+mode+'-20261028'
        plan['requestDerivationSource']=pin(OUT/'request-from-plan.py')
        plan['rootAckArgument']={'meaning':'DERIVE_HEX_SHA256_FROM_ACTUAL_EXTERNAL_ACK_FILE','placeholder':'__ACTUAL_ROOT_ACK_SHA256__'}
        plan['outerArgvTemplate']=argv
        plan['outerRequestTemplate']={'cmd':shlex.join(argv),'workdir':str(ROOT),'login':False,'yield_time_ms':1000,'max_output_tokens':10000}
        plan['externalAuthorityEdges']={'captureQaReview':None,'captureSecurityReview':None,'admissionModelAcceptance':None,'rootAcknowledgement':None,
            'meaning':'Future exact pins are supplied/checked through root ACK v2 and independent acceptance; excluded from pre-model input manifest to avoid cycles'}
        (base/'control-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
        cp=pin(base/'control-plan.json');inputs=pin(base/'frozen-inputs.json');runner=pin(base/'capture-controls.py')
        rs={'schema':'e02-producer3-fixed-capture-runner-subject-v1','actor':'/root/producer3_capture','captureId':mode,
            'runner':runner,'controlPlan':cp,'frozenInputs':inputs,'preparationArtifacts':leaves}
        save(base/'runner-subject.json',rs)
        captures[mode]={'runner':runner,'runnerSubject':pin(base/'runner-subject.json'),'controlPlan':cp,'frozenInputs':inputs}
        scopes[mode]={'controlPlan':cp,'frozenInputs':inputs}
    model_argv=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',
        '/usr/bin/timeout','--signal=KILL','297',python['path'],'-I','-B',str(OUT/'test_admission_models.py')]
    modelmethod={'schema':'e02-producer3-defined-admission9-method-v1','state':'DEFINED_ONLY_PENDING_INDEPENDENT_SOURCE_REVIEW_AND_ROOT_MODEL_RELEASE',
        'modelSource':pin(OUT/'test_admission_models.py'),'expectedCount':9,'format':'EXACT_QUIET_UNITTEST_DOTS_COUNT_OK_STDERR_EMPTY_STDOUT',
        'argv':model_argv,'outerRequestTemplate':{'cmd':shlex.join(model_argv),'workdir':str(ROOT),'login':False,'yield_time_ms':1000,'max_output_tokens':10000},
        'inputScopes':scopes,'actualExecutions':0,'rootModelRelease':None,'modelDataAcceptance':None}
    save(OUT/'admission9-method.json',modelmethod)
    subject={'schema':'e02-producer3-bound-capture-source-subject-v1','actor':'/root/producer3_capture',
        'sourceGeneration':'SOURCE4',
        'state':'WRITES_STOPPED_SOURCE_MODEL_READINESS_PENDING_INDEPENDENT_CAPTURE_QA_SECURITY',
        'producerSource':pin(PREP/'subject.json'),'producerContract':pin(PREP/'source-packet.json'),
        'producerSourceAcceptance':pin(PREP/'source-acceptance.json'),
        'sourceReviews':{role:pin(PREP/('source-'+role+'.json')) for role in ('qa','security')},
        'normativeDataContract':contract,'modelSource':pin(OUT/'test_admission_models.py'),
        'normativeModelSubjectContract':pin(ROOT/'docs/decisions/evidence/e02-producer3-data-contract-20261028/model-subject-contract.json'),
        'normativeSummaryTypesContract':pin(ROOT/'docs/decisions/evidence/e02-producer3-data-contract-20261028/summary-types.json'),
        'requestDerivationSource':pin(OUT/'request-from-plan.py'),
        'negativeInvocationDisposition':pin(OUT/'negative-invocation-disposition.json'),
        'sourceEquivalence':pin(OUT/'source-equivalence.json'),
        'modelMethod':pin(OUT/'admission9-method.json'),'modelDefinitions':9,'modelExecutions':0,
        'captures':captures,'bothInputScopes':scopes,'fixedInputCount':load(OUT/'capture-a/frozen-inputs.json')['actualInputCount'],
        'externalAuthorityEdges':{'captureQaReviews':None,'captureSecurityReviews':None,'admissionModelAcceptance':None,'rootAcknowledgements':None},
        'acyclicity':'Manifest pins code and input leaves; code reads external input/authority pins from reviewed ACK. Combined subject pins two runner subjects/input manifests/model source. Future model acceptance points to this combined subject; future ACK pins model acceptance. No source hash embeds future acceptance/review/ACK hashes.',
        'actualControls':0,'runtimeAuthorized':False,'ordinaryRowsQualified':0,'canonicalE02':'PARTIAL22_UNCHANGED'}
    save(OUT/'subject.json',subject)
    save(OUT/'source-packet.json',{'schema':'e02-producer3-bound-capture-source-packet-v1','subject':pin(OUT/'subject.json'),
        'state':'FROZEN_SOURCE_PENDING_INDEPENDENT_REVIEW_NO_ACTUAL_MODELS_CONTROLS_OR_GRANTS',
        'files':[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()],'actualModelsControlsRuntime':0})
    print(json.dumps({'state':'FROZEN_CODE_MODEL_READINESS_SOURCE_PENDING_REVIEW','subject':pin(OUT/'subject.json'),
        'sourcePacket':pin(OUT/'source-packet.json'),'actualInputCount':subject['fixedInputCount'],
        'modelSource':subject['modelSource'],'modelMethod':subject['modelMethod'],'captures':captures,'actualModelsControlsRuntime':0}))


if __name__=='__main__':main()
