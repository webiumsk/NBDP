"""Prepare Root's finite Source-only input selection; never invoke the builder.

The predecessor capability registry is a declared, previously audited finite
selection. New edges are enumerated from the typed mapping receipt contract.
Operational descriptors embedded in governance remain opaque.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = HERE.parent
EVIDENCE = FAMILY.parent
SOURCE = FAMILY / 'source3'


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve(strict=True)
    body = path.read_bytes()
    return dict(path=str(path), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')
    return pin(path)


def main():
    api = read(SOURCE / 'final-builder-api.json')
    caps = read(FAMILY / 'source2/input-capabilities.DRAFT-r3.json')
    registry = {}
    additions = []

    def add(value, reason):
        assert type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
        old = registry.get(value['path'])
        assert old is None or old == value, ('conflicting expected pin', value['path'])
        if old is None:
            registry[value['path']] = value
            additions.append(dict(pin=value, reason=reason))
        return value

    for value in caps['inputFiles']:
        add(value, 'preserved finite predecessor capability selection')
    inherited = len(registry)
    additions.clear()
    helper = EVIDENCE / 'e02-helper-component-basis-completion-20261105'
    receipt_pin = pin(helper / 'root-source-preparation-r1/source-mapping-verification.json')
    receipt = read(receipt_pin['path'])
    contract = read(api['mappingReceiptContract']['path'])
    spec = dict(schema=api['schema'], actor='/root',
        rootScope=api['rootScope'], predecessor=pin(FAMILY / 'source1/entrypoint.UNBOUND.json'),
        captureSource=pin(EVIDENCE / 'e02-producer-eose-capture-20261105/source2/capture/code-subject.json'),
        captureSourceAcceptance=pin(EVIDENCE / 'e02-producer-eose-capture-review-20261105/source2/acceptance.json'),
        admissionDataAcceptance=pin(EVIDENCE / 'e02-capture-admission-eose-model-20261105/r1/acceptance.json'),
        producerControlData=read(EVIDENCE / 'e02-producer-eose-current286-data-review-20261105/r1/acceptance.json')['subject'],
        producerControlAcceptance=pin(EVIDENCE / 'e02-producer-eose-current286-data-review-20261105/r1/acceptance.json'),
        helperComponentBasis=receipt['subject'], actorAuthority=pin(FAMILY / 'root-coupled-actor-authority.json'),
        basisVerificationEvidence=[receipt_pin],
        controlClockSelection=pin(FAMILY / 'root-consumer-control-clock-selection.json'),
        historicalNegativeInputAuthority=pin(FAMILY / 'root-historical-negative-opaque-source-decision.json'),
        callerClosure=pin(FAMILY / 'root-caller-closure-r2/caller-closure-input.json'),
        callerClosureEvidence=pin(FAMILY / 'root-caller-closure-r2/preparation-evidence.json'),
        requiredFailedInventorySelection=pin(FAMILY / 'root-required-failed-inventory-selection.json'),
        preparationRecipe=api['preparationRecipe'], mappingReceiptContract=api['mappingReceiptContract'],
        basisAdmissionCode=api['basisAdmissionCode'], inputFiles=[])
    for key, value in spec.items():
        if type(value) is dict:
            add(value, 'Root spec/' + key)
    add(receipt_pin, 'Root spec/basisVerificationEvidence/0')
    for field in contract['receipt']['pinKeys']:
        add(receipt[field], 'typed mapping receipt/' + field)
    for index, value in enumerate(receipt['reviews']):
        add(value, 'typed mapping receipt/reviews/' + str(index))
    method = read(receipt['methodSource']['path'])
    for value in method['sources']:
        add(value, 'accepted mapping method Source member')
    method_ack = read(receipt['methodSourceAcceptance']['path'])
    for value in method_ack['reviews']:
        add(value, 'accepted mapping method review')
    preparation = read(receipt['preparationSpec']['path'])
    for field in ('helperSource', 'readerSubject', 'template', 'designAcceptance', 'root24Governance',
                  'closureGovernance', 'actorAuthority', 'callerClosure', 'callerClosureEvidence'):
        add(preparation[field], 'typed mapping preparation spec/' + field)
    for field in ('producerSource', 'producerSourceAcceptance', 'producerControlData',
                  'producerControlAcceptance', 'captureSource', 'captureSourceAcceptance',
                  'admissionDataAcceptance', 'controlPlan'):
        add(preparation['ordinary'][field], 'typed mapping ordinary/' + field)
    for row in preparation['inputFiles']:
        add(row['pin'], 'typed mapping finite input/' + row['kind'])
    execution = read(receipt['execution']['path'])
    for field in ('preparationSpec', 'methodSource', 'stdout', 'stderr', 'originalToolOrigin'):
        add(execution[field], 'typed mapping execution/' + field)
    opaque = read(spec['historicalNegativeInputAuthority']['path'])['opaqueRows']
    opaque_by_path = {value['path']: value for value in opaque}
    template = read(preparation['template']['path'])
    operational = template['originalBasis']['root24ExpectedPinOperands']
    denied = {operational[k]['sha256'] for k in ('subject', 'concretePlan', 'rootRelease',
              'execution', 'rawArtifactManifest', 'originalToolOrigin')}
    closure = read(preparation['closureGovernance']['path'])
    denied.add(closure['finalF']['sha256'])
    denied.update(value['sha256'] for value in opaque)
    assert len(denied) == 9
    for value in registry.values():
        assert value['sha256'] not in denied or opaque_by_path.get(value['path']) == value
    assert all(registry.get(value['path']) == value for value in opaque)
    spec['inputFiles'] = [registry[path] for path in sorted(registry)]
    spec_pin = write(HERE / 'spec.UNRELEASED.json', spec)
    audit = dict(schema='e02-root-consumer-final-spec-preparation-v1', actor='/root',
        state='UNRELEASED_PENDING_INDEPENDENT_CONCRETE_REVIEW', spec=spec_pin,
        preparer=pin(__file__), predecessorCapabilitySelection=pin(FAMILY / 'source2/input-capabilities.DRAFT-r3.json'),
        inheritedExpectedRows=inherited, addedExpectedRows=additions,
        expectedRows=len(registry), physicalCapabilities=len(registry)-len(opaque),
        opaqueExpectedOnly=opaque, deniedIdentityCount=len(denied),
        recursiveDescriptorWalk=False, actualBuilderInvocations=0, canonicalModelsExecuted=0,
        executionAuthorized=False)
    audit_pin = write(HERE / 'spec-preparation.json', audit)
    print(json.dumps(dict(spec=spec_pin, audit=audit_pin, expectedRows=len(registry),
        addedRows=len(additions), physicalCapabilities=len(registry)-len(opaque))))


if __name__ == '__main__':
    main()
