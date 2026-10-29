"""Finite SOURCE metadata assembly only. Never imports producer/capture/model code.

Only this owned assembler's stdlib hashing helpers are loaded. No subprocess,
target import, control/model/test, native/SDK, service or grant operation occurs.
Future authority pins remain explicit external edges to avoid hash cycles.
"""
import json
from pathlib import Path
import runpy

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
DATA=Path('/Data/nbdp-e02-tooling-20261027/producer-controls-preparation-r3-source3')
OUT=ROOT/'docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source3'
PREP=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-producer-final-preparation-r3-20261028/source2'


def main():
    own=runpy.run_path(str(DATA/'assemble-source-only.py'),run_name='source_metadata_helpers_only')
    pin=own['pin'];load=own['load'];save=own['save']
    subject=load(PREP/'subject.json');plan=load(PREP/'control-plan.json')
    seed=load(subject['sourceDataInputClosure']['path'])['files']
    rows=[{k:d[k] for k in ('path','bytes','sha256')} for d in seed]
    configs=[load(d['path']) for d in subject['configurations']]
    bindings=load(subject['artifactBindings']['path'])
    source=pin(PREP/'subject.json');manifest=pin(PREP/'source-packet.json');sourceplan=pin(PREP/'control-plan.json')
    reviews={role:pin(PREP/('source-'+role+'.json')) for role in ('qa','security')}
    producer_acceptance=pin(PREP/'source-acceptance.json')
    contract=pin(ROOT/'docs/decisions/evidence/e02-producer3-data-contract-20261028/contract.json')
    old_node_plan=ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2/current-controls-r1/control-plan.json'
    canonical=load(ROOT/'experiments/results/E01.json')['source_sha256']
    extras=[producer_acceptance,contract,pin(old_node_plan),pin(subject['sourceDataInputClosure']['path'])]
    for base in (DATA,OUT):
        for name in ('capture-template.py','assemble-source-only.py','test_admission_models.py'):
            extras.append(pin(base/name))
    extras.append(pin(DATA/'prepare-final-source.py'))
    for mode in ('capture-a','capture-b'):extras.append(pin(OUT/mode/'capture-controls.py'))
    required={
      'finalSubjectManifestPlan':[source,manifest,sourceplan],
      'all16Workers':configs[0]['sourceAndDependencyPins'],
      'all4Tests':[s['source'] for s in plan['scopes']],
      'runtimeFixtureBindings':subject['sources'],
      'bothConfigurations':subject['configurations'],
      'acceptedApkHelperNativeE01':[bindings[k] for k in ('amethystApk','helperApk','rustBinary','acceptedE01')],
      'provenanceAcceptances':[bindings[k] for k in ('amethystProvenance','amethystAcceptance','helperProvenance','helperAcceptance','acceptedE01Acceptance')],
      'original19':[pin(ROOT/'experiments'/relative) for relative in canonical],
      'diagnosticV2':[d for d in rows if '/experiments/prototypes/e02_transport_query_diagnostic_v2/' in d['path']],
      'oldV1ReadOperands':[d for d in rows if '/experiments/prototypes/e02_ordinary_minimum_v1/' in d['path']],
      'interpreters':[plan['node'],plan['python']],
      'baselineScalarAndOracle':[pin(ROOT/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2'/name)
        for name in ('public-scalar-format-data.json','oracle-provenance.json')]}
    spec={'schema':'e02-producer3-control-freeze-input-spec-v1','state':'COMPLETE_SOURCE_INPUT_SPEC_PENDING_INDEPENDENT_REVIEW',
      'sourceSubject':source,'sourceManifest':manifest,'sourceControlPlan':sourceplan,'node':plan['node'],'python':plan['python'],
      'actualSourceReviews':reviews,'requiredCoverage':required,'additionalReadOperands':extras,
      'nodeExpectedCases':load(old_node_plan)['separateScopes'][0]['expectedCases'],
      'fullReadTreeRoots':own['READ_TREE_ROOTS']}
    save(OUT/'freeze-input-spec.json',spec)
    # The assembler is invoked explicitly by root's SOURCE-only command, not here.
    print(json.dumps({'state':'COMPLETE_SOURCE_SPEC_WRITTEN_NO_CONTROLS','spec':pin(OUT/'freeze-input-spec.json'),
      'producerSourceAcceptance':producer_acceptance,'normativeDataContract':contract}))


if __name__=='__main__':main()
