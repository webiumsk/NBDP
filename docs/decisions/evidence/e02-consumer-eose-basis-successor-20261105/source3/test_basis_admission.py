"""Synthetic Source-only receipt graphs; real immutable public verifier CODE.

No fixture is a Root approval, Source mapping execution or final consumer packet.
The trusted production contract is replaced only as an explicit synthetic input
to this pure metadata API; no verifier function is patched.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prepare_coupled as builder
import basis_admission as admission

SOURCE1 = HERE.parent / 'source1/source'
CONTRACT = HERE.parents[1] / 'e02-helper-component-basis-completion-20261105/source-mapping-receipt-contract.json'


class MemoryReader:
    require_pre_admission = True

    def __init__(self, memory):
        self.memory = memory
        self.reads = []
        self.capabilities = {}
        self.rechecks = 0
        self.refresh()

    def refresh(self):
        self.capabilities = {path: dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                             for path, raw in self.memory.raw.items()}

    def admit(self, pins):
        for pin in pins:
            if pin['sha256'] in builder.DENIED_OPERATIONAL_HASHES:
                raise ValueError('SYNTHETIC_PRE_READ_NINE_IDENTITY_DENIAL')
            admission.equal(self.capabilities.get(pin['path']), pin, 'SYNTHETIC_ALREADY_ADMITTED_PIN')

    def read(self, path, expected=None, mode=None):
        admission.need(expected is not None and expected['sha256'] not in builder.DENIED_OPERATIONAL_HASHES,
                       'SYNTHETIC_EXPECTED_NOT_OPERATIONAL')
        admission.equal(self.capabilities.get(str(path)), expected, 'SYNTHETIC_EXACT_CAPABILITY')
        if mode is not None:
            admission.equal(self.memory.modes[str(path)], mode, 'SYNTHETIC_ACTUAL_MODE')
        raw = self.memory.read(expected)
        self.reads.append(str(path))
        return expected, raw

    def doc(self, pin):
        return json.loads(self.read(pin['path'], pin)[1])

    def recheck(self):
        self.rechecks += 1


def source_model():
    """Load the existing synthetic Source graph fixture, then clear its imports."""
    sys.path.insert(0, str(SOURCE1))
    module_spec = importlib.util.spec_from_file_location('source3_model_fixture', SOURCE1 / 'test_component_basis.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    model = module.model()
    names = builder.assignments((SOURCE1 / 'consumer.py').read_bytes())['RUNTIME_FILES']
    for name in names:
        sys.modules.pop(Path(name).stem, None)
    sys.path.remove(str(SOURCE1))
    return model


def fixture():
    model = source_model()
    memory = model['files']
    def put(name, value, mode=0o600):
        return memory.put('/model/RECEIPT_SYNTHETIC/' + name, value, mode)
    contract = json.loads(CONTRACT.read_bytes())
    root = Path('/model/RECEIPT_SYNTHETIC/helper-source3')
    reader_subject_raw = (SOURCE1 / 'subject.json').read_bytes()
    reader_subject = memory.put(str(SOURCE1 / 'subject.json'), reader_subject_raw)
    runtime_pins = []
    for pin in json.loads(reader_subject_raw)['runtimeSources']:
        body = Path(pin['path']).read_bytes()
        actual = memory.put(pin['path'], body, 0o664)
        admission.equal(actual, pin, 'FIXTURE_UNCHANGED_REAL_FROZEN_READER_CODE')
        runtime_pins.append(pin)
    actor_authority = put('actor-authority', dict(actors=sorted(model['participants']), synthetic=True))
    caller = put('caller-v2', dict(synthetic=True))
    caller_evidence = put('caller-evidence', dict(synthetic=True))
    closure = put('closure-governance', dict(synthetic=True))
    bootstrap_body = b'"""SYNTHETIC SOURCE metadata, never executed."""\n'
    original_bootstrap = put('original-bootstrap', bootstrap_body)
    policy = dict(readerSubject=reader_subject, template=model['template_pin'],
        designAcceptance=model['design_acceptance_pin'],
        root24Governance=model['template']['originalBasis']['helperDataAcceptance'],
        closureGovernance=closure, actorAuthority=actor_authority, callerClosure=caller,
        callerClosureEvidence=caller_evidence, bootstrapSource=original_bootstrap)
    sources = []
    for name in admission.METHOD_MEMBERS:
        body = policy if name == 'policy.json' else bootstrap_body
        sources.append(memory.put(str(root / name), body, 0o600))
    method = memory.put(str(root / 'code-subject.json'), dict(
        schema='e02-helper-component-basis-preparation-code-v1', author='/root/caller',
        scope='SOURCE_PREPARATION_ONLY_NO_ISSUANCE', sourceCount=6, sources=sources,
        modelsDefined=73, modelsExecuted=0, executionAuthorized=False, bootstrapByteIdentical=True), 0o600)
    def reviews(name, subject, decision):
        return [put(name + '-' + role, dict(role=role, session='/root/SYNTHETIC_' + name + '_' + role,
                    decision=decision, subject=subject)) for role in ('qa', 'security')]
    method_reviews = reviews('METHOD', method, contract['approvedMethod']['sourceReviewDecision'])
    method_ack = put('method-acceptance', dict(schema=contract['approvedMethod']['sourceAcceptanceSchema'],
        actor='/root', decision=contract['approvedMethod']['sourceAcceptanceDecision'], subject=method,
        reviews=method_reviews, modelsDefined=73, sourceMappingExecutions=0, completedBasisIssued=False,
        scope='METADATA_ONLY_SOURCE_MAPPING_PREPARATION_CODE_AND_DEFINITIONS_ONLY', executionAuthorized=False))
    contract['approvedMethod']['code'] = method
    contract['approvedMethod']['sourceAcceptance'] = method_ack
    runtime_paths = {pin['path'] for pin in runtime_pins}
    rows = []
    for path, raw in sorted(memory.raw.items()):
        if path == model['descriptor']['path']:
            continue
        rows.append(dict(pin=dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
            mode=memory.modes[path], kind='READER_CODE' if path in runtime_paths else 'GOVERNANCE'))
    preparation = dict(schema='e02-helper-component-basis-preparation-spec-v2', actor='/root',
        scope='VERIFY_ORIGINAL_HELPER_COMPONENT_SOURCE_MAPPING_ONLY', issued=True,
        executionAuthorized=False, helperSource=method, ordinary=model['ordinary_expected'], inputFiles=rows,
        **{key: policy[key] for key in ('readerSubject', 'template', 'designAcceptance', 'root24Governance',
                                     'closureGovernance', 'actorAuthority', 'callerClosure', 'callerClosureEvidence')})
    preparation_pin = put('preparation-spec', preparation)
    draft = copy.deepcopy(model['basis'])
    draft.update(issued=False, readiness=False, state='UNISSUED_SOURCE_MAPPING_PREPARATION_ONLY')
    result = dict(schema=contract['preparationResult']['schema'], author='/root/caller',
        draftBasis=draft, sourceVerification=copy.deepcopy(model['basis']['sourceVerification']),
        readClosure=rows, rootApprovedSpec=preparation_pin, helperSource=method,
        **contract['preparationResult']['required'])
    result_pin = put('preparation-result.json', result)
    stderr = put('stderr.log', b'')
    request = admission.expected_request(preparation_pin, method, result_pin, stderr)
    native = dict(schema='e02-actual-tool-custody-v1', operator='/root', launch=dict(
        toolName='tools.exec_command', actualArguments=request,
        unmodifiedResponse=dict(chunk_id='SYNTHETIC_NEVER_NATIVE', wall_time_seconds=0.001,
            exit_code=0, output='', original_token_count=0)), polls=[])
    origin_pin = put('native-origin', json.dumps(native).encode())
    execution = dict(schema='e02-helper-component-source-preparation-execution-v1', operator='/root',
        request=request, preparationSpec=preparation_pin, methodSource=method, stdout=result_pin,
        stderr=stderr, originalToolOrigin=origin_pin, exitCode=0)
    execution_pin = put('execution', execution)
    result_reviews = reviews('RESULT', result_pin, contract['reviewEnvelope']['decision'])
    receipt = dict(contract['receipt']['literals'], subject=model['descriptor'], preparationResult=result_pin,
        preparationSpec=preparation_pin, methodSource=method, methodSourceAcceptance=method_ack,
        execution=execution_pin, originalToolOrigin=origin_pin, reviews=result_reviews)
    receipt_pin = put('receipt', receipt)
    ordinary = model['ordinary_expected']
    spec = dict(helperComponentBasis=model['descriptor'], basisVerificationEvidence=[receipt_pin],
        actorAuthority=actor_authority, callerClosure=caller, callerClosureEvidence=caller_evidence,
        producerControlData=ordinary['producerControlData'], producerControlAcceptance=ordinary['producerControlAcceptance'],
        captureSource=ordinary['captureSource'], captureSourceAcceptance=ordinary['captureSourceAcceptance'],
        admissionDataAcceptance=ordinary['admissionDataAcceptance'])
    values = dict(CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE=model['template_pin'],
        CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE=model['design_acceptance_pin'],
        CURRENT_PRODUCER=ordinary['producerSource'], CURRENT_PRODUCER_SOURCE_ACCEPTANCE=ordinary['producerSourceAcceptance'],
        CURRENT_SOURCE_PLAN=ordinary['controlPlan'])
    result = dict(model=model, memory=memory, reader=MemoryReader(memory), contract=contract,
        spec=spec, values=values, participants=model['participants'], receipt=receipt,
        receipt_pin=receipt_pin, execution=execution, native=native, result=result, preparation=preparation)
    def replace(which, value):
        pin = put('mutation-' + which, value)
        if which == 'receipt':
            result['spec']['basisVerificationEvidence'] = [pin]
        else:
            receipt = copy.deepcopy(result['receipt'])
            key = {'execution': 'execution', 'result': 'preparationResult', 'preparation': 'preparationSpec',
                   'native': 'originalToolOrigin'}[which]
            receipt[key] = pin
            result['spec']['basisVerificationEvidence'] = [put('mutated-receipt', receipt)]
        result['reader'].refresh()
        return pin
    result['replace'] = replace
    return result


def validate(value):
    return admission.validate_mapping_receipt(value['reader'], value['spec'], value['values'],
                                             value['participants'], value['contract'])


def coherent_bad_basis(value, change):
    """Repin every synthetic envelope, so the real Source verifier is reached."""
    basis = copy.deepcopy(value['model']['basis'])
    change(basis)
    memory = value['memory']
    basis_pin = memory.put(value['model']['descriptor']['path'], basis)
    result = copy.deepcopy(value['result'])
    result['draftBasis'] = copy.deepcopy(basis)
    result['draftBasis'].update(issued=False, readiness=False, state='UNISSUED_SOURCE_MAPPING_PREPARATION_ONLY')
    result['sourceVerification'] = copy.deepcopy(basis['sourceVerification'])
    result_pin = memory.put(value['receipt']['preparationResult']['path'], result, 0o600)
    execution = copy.deepcopy(value['execution']); execution['stdout'] = result_pin
    execution_pin = memory.put(value['receipt']['execution']['path'], execution, 0o600)
    receipt = copy.deepcopy(value['receipt'])
    receipt.update(subject=basis_pin, preparationResult=result_pin, execution=execution_pin)
    for index, pin in enumerate(receipt['reviews']):
        review = json.loads(memory.raw[pin['path']]); review['subject'] = result_pin
        receipt['reviews'][index] = memory.put(pin['path'], review, 0o600)
    receipt_pin = memory.put(value['receipt_pin']['path'], receipt, 0o600)
    value['spec'].update(helperComponentBasis=basis_pin, basisVerificationEvidence=[receipt_pin])
    value['reader'].refresh()


class TypedMappingAdmissionControls(unittest.TestCase):
    def test_complete_synthetic_receipt_and_unchanged_real_public_verifier_accept(self):
        value = fixture()
        self.assertEqual(validate(value), value['receipt_pin'])
        self.assertGreater(value['reader'].rechecks, 0)
        self.assertFalse(any('/OPERATIONAL_' in path for path in value['reader'].reads))

    def test_arbitrary_json_is_not_a_mapping_receipt(self):
        value = fixture(); value['replace']('receipt', dict(arbitrary=True))
        with self.assertRaisesRegex(ValueError, 'CLOSED_FIFTEEN_KEY_MAPPING_RECEIPT'):
            validate(value)

    def test_multiple_or_empty_receipts_are_refused(self):
        for count in (0, 2):
            value = fixture(); value['spec']['basisVerificationEvidence'] = [value['receipt_pin']] * count
            with self.assertRaisesRegex(ValueError, 'EXACT_ONE_TYPED_MAPPING_RECEIPT'):
                validate(value)

    def test_wrong_actual_result_review_subject_is_refused(self):
        value = fixture(); receipt = copy.deepcopy(value['receipt'])
        review = value['reader'].doc(receipt['reviews'][0]); review['subject'] = value['model']['descriptor']
        receipt['reviews'][0] = value['memory'].put('/model/RECEIPT_SYNTHETIC/wrong-review', review)
        value['replace']('receipt', receipt)
        with self.assertRaisesRegex(ValueError, 'MAPPING_REVIEW_PREPARATION_RESULT_SUBJECT'):
            validate(value)

    def test_changed_method_pin_is_refused(self):
        value = fixture(); receipt = copy.deepcopy(value['receipt']); receipt['methodSource']['sha256'] = '0' * 64
        value['replace']('receipt', receipt)
        with self.assertRaisesRegex(ValueError, 'MAPPING_APPROVED_METHOD_CODE_PIN'):
            validate(value)

    def test_missing_terminal_native_origin_is_refused(self):
        value = fixture(); native = copy.deepcopy(value['native'])
        response = native['launch']['unmodifiedResponse']; response.pop('exit_code'); response['session_id'] = 11
        raw = json.dumps(native).encode()
        pin = value['memory'].put('/model/RECEIPT_SYNTHETIC/native-origin-mutated', raw)
        execution = copy.deepcopy(value['execution']); execution['originalToolOrigin'] = pin
        execution_pin = value['memory'].put('/model/RECEIPT_SYNTHETIC/execution-mutated', execution)
        receipt = copy.deepcopy(value['receipt']); receipt.update(execution=execution_pin, originalToolOrigin=pin)
        value['replace']('receipt', receipt)
        with self.assertRaisesRegex(ValueError, 'MAPPING_COMPLETE_TERMINAL_ORIGIN_REQUIRED'):
            validate(value)

    def test_equivalent_argv_but_changed_command_bytes_is_refused(self):
        value = fixture(); execution = copy.deepcopy(value['execution']); execution['request']['cmd'] += ' '
        value['replace']('execution', execution)
        with self.assertRaisesRegex(ValueError, 'MAPPING_EXACT_REVIEWED_CANONICAL_MODEL5_REQUEST'):
            validate(value)

    def test_consistent_forged_empty_eight_source_pairs_reach_real_refusal(self):
        value = fixture()
        coherent_bad_basis(value, lambda basis: basis.update(sourcePairs=[]))
        with self.assertRaisesRegex(ValueError, 'COMPONENT_EXACT_EIGHT'):
            validate(value)

    def test_consistent_forged_empty_source_facts_reach_real_refusal(self):
        value = fixture()
        coherent_bad_basis(value, lambda basis: basis.update(sourceVerification={}))
        with self.assertRaisesRegex(ValueError, 'COMPONENT_RECOMPUTED_SOURCE_FACTS'):
            validate(value)

    def test_consistent_forged_empty_actor_union_reaches_real_refusal(self):
        value = fixture()
        coherent_bad_basis(value, lambda basis: basis['actorClosure'].update(participants=[]))
        with self.assertRaises(ValueError):
            validate(value)

    def test_consistent_forged_source_mode_reaches_real_refusal(self):
        value = fixture()
        coherent_bad_basis(value, lambda basis: basis['sourcePairs'][0].update(newMode='0o600'))
        with self.assertRaisesRegex(ValueError, 'VALUE_MISMATCH'):
            validate(value)

    def test_wrong_physical_source_mode_cannot_be_covered_by_equal_declarations(self):
        value = fixture()
        path = value['model']['selected']['new'][0]['path']
        value['memory'].modes[path] = 0o600
        with self.assertRaisesRegex(ValueError, 'SYNTHETIC_ACTUAL_MODE'):
            validate(value)

    def test_author_reviewer_cannot_approve_actual_preparation_result(self):
        value = fixture(); receipt = copy.deepcopy(value['receipt'])
        review = value['reader'].doc(receipt['reviews'][0]); review['session'] = '/root/caller'
        receipt['reviews'][0] = value['memory'].put('/model/RECEIPT_SYNTHETIC/self-review', review)
        value['replace']('receipt', receipt)
        with self.assertRaisesRegex(ValueError, 'MAPPING_REVIEWER_INDEPENDENCE'):
            validate(value)

    def test_review_decision_or_order_cannot_be_projected_or_repaired(self):
        for mode in ('decision', 'order'):
            value = fixture(); receipt = copy.deepcopy(value['receipt'])
            if mode == 'order':
                receipt['reviews'].reverse()
            else:
                review = value['reader'].doc(receipt['reviews'][0]); review['decision'] = 'SYNTHETIC_WRONG_DECISION'
                receipt['reviews'][0] = value['memory'].put('/model/RECEIPT_SYNTHETIC/wrong-decision', review)
            value['replace']('receipt', receipt)
            with self.assertRaisesRegex(ValueError, 'MAPPING_(EXACT_REVIEW_DECISION|ORDERED_REVIEW_ROLE)'):
                validate(value)

    def test_changed_preparation_spec_or_method_acceptance_is_refused(self):
        for mode in ('spec', 'acceptance'):
            value = fixture(); receipt = copy.deepcopy(value['receipt'])
            if mode == 'spec':
                preparation = copy.deepcopy(value['preparation']); preparation['issued'] = False
                receipt['preparationSpec'] = value['memory'].put('/model/RECEIPT_SYNTHETIC/unissued-spec', preparation)
                reason = 'MAPPING_PREPARATION_SPEC_JOIN'
            else:
                receipt['methodSourceAcceptance']['sha256'] = '0' * 64
                reason = 'MAPPING_APPROVED_METHOD_SOURCE_RECEIPT'
            value['replace']('receipt', receipt)
            with self.assertRaisesRegex(ValueError, reason):
                validate(value)

    def test_extra_root_completion_value_change_is_refused_before_public_verifier(self):
        value = fixture(); basis = copy.deepcopy(value['model']['basis']); basis['executionAuthorized'] = True
        pin = value['memory'].put(value['model']['descriptor']['path'], basis)
        receipt = copy.deepcopy(value['receipt']); receipt['subject'] = pin
        value['spec']['helperComponentBasis'] = pin; value['replace']('receipt', receipt)
        with self.assertRaisesRegex(ValueError, 'MAPPING_EXACT_THREE_VALUE_ROOT_COMPLETION_ONLY'):
            validate(value)

    def test_duplicate_native_key_or_float_outside_wall_duration_is_refused(self):
        for raw in (b'{"x":1,"x":2}', b'{"launch":{"original_token_count":0.5}}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                admission.decode_native(raw)

    def test_nonempty_stderr_and_nonzero_terminal_are_refused(self):
        value = fixture(); execution = copy.deepcopy(value['execution'])
        execution['stderr'] = value['memory'].put('/model/RECEIPT_SYNTHETIC/stderr-bad', b'failure')
        value['replace']('execution', execution)
        with self.assertRaisesRegex(ValueError, 'MAPPING_COMPLETE_EMPTY_STDERR'):
            validate(value)
        value = fixture(); native = copy.deepcopy(value['native'])
        native['launch']['unmodifiedResponse']['exit_code'] = 2
        pin = value['memory'].put('/model/RECEIPT_SYNTHETIC/nonzero-native', json.dumps(native).encode())
        execution = copy.deepcopy(value['execution']); execution['originalToolOrigin'] = pin
        execution_pin = value['memory'].put('/model/RECEIPT_SYNTHETIC/execution-nonzero', execution)
        receipt = copy.deepcopy(value['receipt']); receipt.update(execution=execution_pin, originalToolOrigin=pin)
        value['replace']('receipt', receipt)
        with self.assertRaisesRegex(ValueError, 'MAPPING_NATURAL_TERMINAL_ZERO'):
            validate(value)


if __name__ == '__main__':
    unittest.main(verbosity=2)
