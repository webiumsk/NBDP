"""Read-only development audit of finite typed selectors before final inputs.

The in-memory Source-pair draft is explicitly not an issued completed basis.
No consumer packet is frozen and operational helper pins are not followed.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_coupled as builder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capabilities-output', required=True)
    args = parser.parse_args()
    capability_path = Path(args.capabilities_output)
    builder.need(capability_path.is_absolute() and capability_path.parent == builder.OWNED
                 and not capability_path.exists() and not capability_path.is_symlink(),
                 'FRESH_OWNED_DRAFT_CAPABILITY_OUTPUT')
    reader = builder.Reader()
    values = builder.assignments(reader.read(builder.PREDECESSOR / 'source/consumer.py')[1])
    evidence = builder.OWNED.parents[1]
    def pin(path):
        return reader.read(path)[0]
    template = reader.doc(values['CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE'])
    producer = reader.doc(values['CURRENT_PRODUCER'])
    by_name = {Path(p['path']).name: p for p in producer['sources']}
    pairs = [dict(row, newPin=by_name[row['name']], newMode='0o664')
             for row in template['sourcePairs']]
    source = evidence / 'e02-producer-eose-capture-20261105/source2'
    spec = dict(schema='e02-root-consumer-coupled-source2-spec-v1', actor='/root',
        rootScope=pin(builder.SCOPE), predecessor=pin(builder.PREDECESSOR / 'entrypoint.UNBOUND.json'),
        captureSource=pin(source / 'capture/code-subject.json'),
        captureSourceAcceptance=pin(evidence / 'e02-producer-eose-capture-review-20261105/source2/acceptance.json'),
        admissionDataAcceptance=pin(evidence / 'e02-capture-admission-eose-model-20261105/r1/acceptance.json'),
        producerControlData=pin(Path('/Data/nbdp-e02-tooling-20261027/producer4-control-capture-actual-eose-6ea9fb8bcdd736d1d54000e4/assembled/subject.json')),
        producerControlAcceptance=pin(evidence / 'e02-producer-eose-current286-data-review-20261105/r1/acceptance.json'),
        helperComponentBasis=None, actorAuthority=pin(builder.OWNED.parent / 'root-coupled-actor-authority.json'),
        basisVerificationEvidence=[],
        controlClockSelection=pin(builder.OWNED.parent / 'root-consumer-control-clock-selection.json'),
        historicalNegativeInputAuthority=pin(builder.OWNED.parent / 'root-historical-negative-opaque-source-decision.json'),
        callerClosure=pin(builder.OWNED.parent / 'root-caller-closure-r2/caller-closure-input.json'),
        callerClosureEvidence=pin(builder.OWNED.parent / 'root-caller-closure-r2/preparation-evidence.json'),
        requiredFailedInventorySelection=pin(builder.OWNED.parent / 'root-required-failed-inventory-selection.json'),
        preparationRecipe=None, inputFiles=[])
    authority = reader.doc(spec['actorAuthority'])
    builder.validate_caller_closure(reader, spec['callerClosure'], spec['callerClosureEvidence'],
                                   spec['actorAuthority'], set(authority['participants']))
    # Only the selector program is exercised. Neither validate_spec nor build is
    # bypassed to write a packet: no output directory or actual basis is issued.
    draft = dict(originalBasis=template['originalBasis'], sourcePairs=pairs)
    closure = builder.fixed_closure(reader, spec, values, draft, template)
    reader.recheck()
    builder.put(capability_path, dict(schema='e02-consumer-source2-input-capabilities-draft-v1',
        author=builder.AUTHOR, inputFiles=[closure.rows[path] for path in sorted(closure.rows)],
        sourceOnly=True, historicalNegativeOpaqueOperands=[closure.opaque[path] for path in sorted(closure.opaque)],
        missingInputs=['Completed genuine basis and verification receipts', 'Final preparation recipe pin', 'Actual Root spec'],
        finalInputAuthorityComplete=False, executionAuthorized=False))
    print(json.dumps(dict(schema='e02-consumer-source2-typed-closure-development-audit-v1',
        declaredInputs=len(closure.rows), actualObservedInputs=len(reader.observed),
        typedReadSites=sum(len(rows) for rows in closure.uses.values()),
        explicitHistoricalInputs=len(reader.doc(pin(builder.PREDECESSOR / 'baseline-metadata/input-manifest.json'))['fixedSourceAndCurrentDataOperands']),
        totalDeclaredBytes=sum(p['bytes'] for p in closure.rows.values()),
        opaqueHistoricalNegativeInputs=len(closure.opaque),
        opaqueHistoricalNegativePhysicalReads=0,
        sourcePairRows=len(pairs), allFinalInputAuthorityVerified=False,
        callerV2Verified=True, callerDeclarations=26, historicalAttempts=15, legacyNodes=63,
        capabilitiesDraft=str(capability_path),
        missingInputs=['Genuine completed basis', 'External completed Source-mapping verification', 'Final preparation recipe pin'],
        finalFreezeIssued=False, canonicalModelsExecuted=0,
        operationalHelperBodiesRead=0, recursiveDescriptorWalk=False)))


if __name__ == '__main__':
    main()
