"""Bounded SOURCE2 authoring transform of preserved R9 generator; no imports."""
import ast
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'r9/prepare_source.py'
NEW = HERE / 'prepare_source.py'


BOUNDARY = '''
def selected_producer_count(producer, accepted_receipt):
    """One strict count-domain boundary used by generation and future models.

    The caller pins the full current producer and actual accepted Root receipt.
    This method does not authenticate a receipt or grant runtime authority.
    The producer's structured modelsDefined map remains untouched.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(type(producer) is dict and type(accepted_receipt) is dict, 'COUNT_INPUT_OBJECTS')
    count = producer.get('selectedDefinitionCount')
    require(type(count) is int and count == 266, 'PLAIN_INTEGER_SELECTED_PRODUCER266')
    partition = producer.get('selectedCountsSeparate')
    require(type(partition) is list and len(partition) == 10 and
            all(type(value) is int and value > 0 for value in partition),
            'PLAIN_INTEGER_SELECTED_PARTITION')
    require(sum(partition) == count, 'SELECTED_PARTITION_TOTAL_EQUALS_SCALAR')
    accepted_partition = accepted_receipt.get('countsSeparate')
    require(type(accepted_partition) is list and len(accepted_partition) == 10 and
            all(type(value) is int and value > 0 for value in accepted_partition),
            'PLAIN_INTEGER_ACCEPTED_PARTITION')
    require(partition == accepted_partition and sum(accepted_partition) == count,
            'CURRENT_ACCEPTED_PARTITION_EXACT_ORDER_AND_TOTAL')
    for field, expected in (('modelsExecuted', count), ('modelsPassed', count), ('modelsFailed', 0)):
        actual = accepted_receipt.get(field)
        require(type(actual) is int and actual == expected, 'PLAIN_INTEGER_ACCEPTED_' + field)
    return count

'''


COUNT_TESTS = '''

class CurrentProducerCountMetadataControls(unittest.TestCase):
    """Actual generator metadata boundary; definitions only until Root releases models."""
    def boundary_and_inputs(self):
        generator = load('current_source2_count_metadata_subject', Path('@GENERATOR@'))
        producer = json.loads(Path('@PRODUCER@').read_bytes())
        receipt = json.loads(Path('@RECEIPT@').read_bytes())
        return generator.selected_producer_count, producer, receipt

    def test_actual_generated_constants_and_subject_are_plain266_from_same_boundary(self):
        boundary, producer, receipt = self.boundary_and_inputs()
        original_map = copy.deepcopy(producer['modelsDefined'])
        value = boundary(producer, receipt)
        self.assertIs(type(value), int)
        self.assertEqual(value, 266)
        constants = json.loads((H.HERE / 'constants.json').read_bytes())
        subject = json.loads((H.HERE / 'subject.json').read_bytes())
        for actual in (constants['producerModelsDefined'], subject['upstreamProducerModelsDefined']):
            self.assertIs(type(actual), int)
            self.assertEqual(actual, value)
        self.assertIs(type(producer['modelsDefined']), dict)
        self.assertEqual(producer['modelsDefined'], original_map)

    def test_actual_count_boundary_refuses_dictionary_boolean_float_or_disagreeing_scalar(self):
        boundary, producer, receipt = self.boundary_and_inputs()
        for bad in (copy.deepcopy(producer['modelsDefined']), True, False, 266.0, '266', 265, 267):
            with self.subTest(value=repr(bad)):
                altered = copy.deepcopy(producer)
                altered['selectedDefinitionCount'] = bad
                with self.assertRaisesRegex(ValueError, 'PLAIN_INTEGER_SELECTED_PRODUCER266'):
                    boundary(altered, receipt)

    def test_actual_count_boundary_refuses_partition_container_type_aliases_or_disagreement(self):
        boundary, producer, receipt = self.boundary_and_inputs()
        baseline = producer['selectedCountsSeparate']
        bad_partitions = [dict(enumerate(baseline)), True, 266.0, tuple(baseline), [],
                          [float(baseline[0]), *baseline[1:]],
                          [True, *baseline[1:]],
                          [baseline[0] + 1, *baseline[1:]],
                          [baseline[1], baseline[0], *baseline[2:]]]
        for bad in bad_partitions:
            with self.subTest(value=repr(bad)):
                altered = copy.deepcopy(producer)
                altered['selectedCountsSeparate'] = bad
                with self.assertRaises(ValueError):
                    boundary(altered, receipt)

    def test_actual_count_boundary_refuses_accepted_receipt_type_aliases_or_count_disagreement(self):
        boundary, producer, receipt = self.boundary_and_inputs()
        cases = [('modelsExecuted', {'count': 266}), ('modelsExecuted', True),
                 ('modelsExecuted', 266.0), ('modelsPassed', 265), ('modelsFailed', False),
                 ('countsSeparate', dict(enumerate(receipt['countsSeparate']))),
                 ('countsSeparate', True), ('countsSeparate', 266.0),
                 ('countsSeparate', [float(receipt['countsSeparate'][0]), *receipt['countsSeparate'][1:]]),
                 ('countsSeparate', [receipt['countsSeparate'][1], receipt['countsSeparate'][0],
                                     *receipt['countsSeparate'][2:]])]
        for field, bad in cases:
            with self.subTest(field=field, value=repr(bad)):
                altered = copy.deepcopy(receipt)
                altered[field] = bad
                with self.assertRaises(ValueError):
                    boundary(producer, altered)
'''


def main():
    raw = OLD.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '98efb84f02e97f4612ddd90da32d6f0ed4be26f749f4d2915b967ce41ed352da'
    source = raw.decode()
    # Remove unused old append strings. The actual R9 test modules already
    # contain their six definitions and are copied without method AST changes.
    tree = ast.parse(source)
    lines = source.splitlines(True)
    for node in reversed(tree.body):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('HOST_TESTS', 'LEASE_TESTS'):
            del lines[node.lineno - 1:node.end_lineno]
    source = ''.join(lines)
    replacements = [
        ("OUT = EVIDENCE / 'e02-current-controller-source-20261105/r9'", "OUT = EVIDENCE / 'e02-current-controller-source-20261105/r10'"),
        ("OLD = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r8')", "OLD = Path('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r9')"),
        ("NEW = OLD.with_name('producer4-helper-probe-controller-preparation-r9')", "NEW = OLD.with_name('producer4-helper-probe-controller-preparation-r10')"),
        ("SCOPE = EVIDENCE / 'e02-goal-resume-20261104/controller-successor-root-scope-20261105.json'", "SCOPE = EVIDENCE / 'e02-goal-resume-20261104/controller-source2-r10-root-scope-20261105.json'"),
        ("'eaa1b3eb010a3412f37353024be164bfcba23f1f14ca45fde0114beed6183cd9'", "'530781445fbfd498347b541d68958c6fc21c7bde769b75c765043f9522c43219'"),
        ("assert pin(OLD / 'subject.json') == scope['immutablePredecessor']", "assert pin(OLD / 'subject.json') == scope['immutableNegativeR9']"),
        ("constants['producerModelsDefined'] = producer['modelsDefined']", "constants['producerModelsDefined'] = producer_count"),
        ("upstreamProducerModelsDefined=producer['modelsDefined']", "upstreamProducerModelsDefined=producer_count"),
        ("for name in owned_code:\n", "for name in owned_code:\n"),
    ]
    for before, after in replacements:
        assert source.count(before) == 1, before
        source = source.replace(before, after, 1)
    source = source.replace("version='r9'", "version='r10'")
    source = source.replace('Bounded stdlib-only R9 SOURCE preparation', 'Bounded stdlib-only R10 SOURCE2 preparation')
    source = source.replace('Only NEW R9 Data and repository packet roots are writable.', 'Only NEW R10 Data and repository packet roots are writable.')
    source = source.replace("e02-current-controller-r9-", "e02-current-controller-r10-")
    source = source.replace("'CONTRACT-R9.md'", "'CONTRACT-R10.md'")
    source = source.replace("'r8-r9-source.diff'", "'r9-r10-source.diff'")
    source = source.replace("SOURCE9:", "SOURCE10:")
    source = source.replace("literal to R9", "literal to R10")
    source = source.replace("loads select R9", "loads select R10")
    source = source.replace("FROZEN_SOURCE9_CURRENT_ACCEPTED_ARTIFACT_AND_TYPED_COLLECTOR_BINDINGS_PENDING_INDEPENDENT_REVIEW", "FROZEN_SOURCE10_CURRENT_ACCEPTED_ARTIFACT_TYPED_COLLECTOR_AND_SCALAR_COUNT_CORRECTION_PENDING_INDEPENDENT_REVIEW")
    source = source.replace("CURRENT_ACCEPTED_ARTIFACT_TYPED_REQUEST7_BINDINGS_R1", "CURRENT_ACCEPTED_ARTIFACT_TYPED_REQUEST7_SCALAR266_BINDINGS_R2")
    source = source.replace("'Fresh independent currentR9 SOURCE QA/security outside complete creator/design/operator union'", "'Fresh independent currentR10 SOURCE QA/security outside complete creator/design/operator union'")
    # The complete R9 test module already uses the current qualifier/full7.
    start = source.index("        if name == 'test_lease_composition.py':")
    end = source.index("        ast.parse(raw, filename=str(NEW / name))", start)
    source = source[:start] + '''        if name == 'test_host.py':
            text = raw.decode()
            needle = "\\n\\nif __name__ == '__main__':"
            assert text.count(needle) == 1
            raw = text.replace(needle, COUNT_TESTS + needle).encode()
''' + source[end:]
    count_tests = COUNT_TESTS.replace('@GENERATOR@', str(NEW)).replace(
        '@PRODUCER@', '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer-current-artifacts-20261105/source1/producer/subject.json').replace(
        '@RECEIPT@', '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-current-producer266-data-20261105/acceptance.json')
    needle = '\ndef main():\n'
    assert source.count(needle) == 1
    source = source.replace(needle, BOUNDARY + '\nCOUNT_TESTS = ' + repr(count_tests) + '\n' + needle)
    needle = "    constants = doc(OLD / 'constants.json')\n"
    assert source.count(needle) == 1
    source = source.replace(needle, "    producer_count = selected_producer_count(producer, producer_data_receipt)\n" + needle)
    needle = "    old = doc(OLD / 'subject.json')\n"
    assert source.count(needle) == 1
    source = source.replace(needle, needle + "    negative_disposition = doc(Path(scope['negativeR9Disposition']['path']))\n    assert pin(Path(scope['negativeR9Disposition']['path'])) == scope['negativeR9Disposition']\n    assert pin(Path(negative_disposition['freeze']['path'])) == negative_disposition['freeze']\n    negative_frozen = doc(Path(negative_disposition['freeze']['path']))\n    assert len(negative_frozen['inputs']) == 156\n    assert all(pin(Path(item['path'])) == item for item in negative_frozen['inputs'])\n")
    needle = "    exclusions = sorted(set(scope['reviewerExclusions']) | set(contributors))\n"
    assert source.count(needle) == 1
    source = source.replace(needle, "    contributors = sorted(set(contributors) | {'/root/controller_r9_qa_e7c43daa', '/root/controller_r9_security_e7c43daa'})\n    exclusions = sorted(set(scope['reviewerExclusions']) | set(contributors) | {'/root/controller_model_metadata_source2'})\n")
    source = source.replace("== 168\n", "== 174\n")
    source = source.replace("priorDefinitionCount=168", "priorDefinitionCount=174")
    source = source.replace("sum(counts)-168", "sum(counts)-174")
    source = source.replace("all168PriorMethodsASTIdentical=True", "all174PriorMethodsASTIdentical=True, all168BaselineMethodsRetained=True")
    source = source.replace("all168PriorDefinitionNamesAndMethodBodiesRetained=True", "all174PriorDefinitionNamesAndMethodBodiesRetained=True, all168PriorDefinitionNamesAndMethodBodiesRetained=True")
    source = source.replace("prior168DataTransferred=False,\n        newCurrentBindingDefinitions", "prior168DataTransferred=False, prior174DataTransferred=False,\n        newCurrentBindingDefinitions")
    source = source.replace("priorDefinitionsRetained=168", "priorDefinitionsRetained=174")
    source = source.replace("priorNamesAndASTsRetained=168", "priorNamesAndASTsRetained=174")
    source = source.replace("all168PriorTestMethodASTsRetained=True", "all174PriorTestMethodASTsRetained=True")
    source = source.replace("hostTopLevelOnlyChange='HERE literal r8 to r9'", "hostTopLevelOnlyChange='HERE literal r9 to r10'")
    # Current R9 metadata replacements use exact R9 names; R8 remains accepted
    # baseline provenance and is not renamed as R9 acceptance.
    source = source.replace("replacements[str(OLD / 'CONTRACT-R8.md')]", "replacements[str(OLD / 'CONTRACT-R9.md')]")
    source = source.replace("replacements[str(OLD / 'r7-r8-source.diff')]", "replacements[str(OLD / 'r8-r9-source.diff')]")
    needle = "        'delta-proof.json', 'preservation.json', 'static-preparation.json']}"
    assert source.count(needle) == 1
    source = source.replace(needle, "        'delta-proof.json', 'preservation.json', 'static-preparation.json',\n        'read-map.json', 'outer-request7-policy.json', 'outer-request7-skeleton.json']}")
    needle = "    selected = {str(replacements.get(x['path'], Path(x['path']))): replacements.get(x['path'], Path(x['path'])) for x in old['sources']}\n"
    assert source.count(needle) == 1
    source = source.replace(needle, "    replacements[str(OUT.parent / 'r9/prepare_source.py')] = OUT / 'prepare_source.py'\n" + needle)
    needle = "    prerequisites += [Path(old['predecessorSourceAcceptance']['path']), OLD / 'subject.json',\n                      R8_SOURCE_ACCEPTANCE, R8_DATA_ACCEPTANCE, MODEL5_ORIGINAL]\n"
    assert source.count(needle) == 1
    source = source.replace(needle, needle + "    prerequisites += [Path(scope['negativeR9Disposition']['path']), Path(scope['predecessorScope']['path']),\n                      *[Path(x['path']) for x in scope['negativeR9Reviews']],\n                      *[Path(x['path']) for x in scope['negativeR9Findings']]]\n    negative_disposition = doc(Path(scope['negativeR9Disposition']['path']))\n    prerequisites += [Path(negative_disposition['freeze']['path']), OUT / 'write_source2_generator.py']\n")
    source = source.replace("predecessorSubject=scope['immutablePredecessor']", "predecessorSubject=scope['immutableNegativeR9']")
    source = source.replace("predecessor=scope['immutablePredecessor']", "predecessor=scope['immutableNegativeR9']")
    source = source.replace("predecessorSourceAcceptance=pin(R8_SOURCE_ACCEPTANCE),", "predecessorSourceAcceptance=None, negativePredecessor=scope['immutableNegativeR9'],\n        negativePredecessorDisposition=scope['negativeR9Disposition'],\n        acceptedSourceBaseline=scope['immutablePredecessor'], acceptedSourceBaselineAcceptance=pin(R8_SOURCE_ACCEPTANCE),")
    # Replace the inherited unqualified168 statement with precise lineage.
    source = source.replace("All168 prior test names and method ASTs remain. New named controls cover the", "All174 R9 test names and method ASTs (including168 baseline) remain. Existing six controls cover the")
    source = source.replace("Root explicitly selected all eight current producer source modes0664.", "R9 was held for copying the producer's structured modelsDefined dictionary into\\nscalar count fields. Its complete frozen SOURCE and both negative reviews remain\\nunchanged. The actual generator boundary now derives plain-int266 only from\\nselectedDefinitionCount, checks the strict10-part selectedCountsSeparate and\\nactual accepted current266 receipt, and supplies both generated scalar fields.\\nNew definitions exercise the same generator helper and generated fields, with\\ndictionary/bool/float/count/partition disagreement refusals. No producer map or\\nconsumer predicate changes; no174 result transfer.\\n\\nRoot explicitly selected all eight current producer source modes0664.")
    source = source.replace("prior168DataTransferred=False, priorCollector50DataTransferred=False", "prior168DataTransferred=False, prior174DataTransferred=False, priorCollector50DataTransferred=False")
    source = source.replace("        predecessorSourceInputs=old['sources'], allPredecessorPinsUnchanged=True,", "        predecessorSourceInputs=old['sources'], allPredecessorPinsUnchanged=True,\n        negativePredecessorFreeze=negative_disposition['freeze'], negativeFrozenPinsUnchanged=156,")
    needle = "    assert all(pin(Path(x['path'])) == x for x in source_pins)\n"
    assert source.count(needle) == 1
    source = source.replace(needle, needle + "    assert all(pin(Path(item['path'])) == item for item in negative_frozen['inputs'])\n")
    # Explicitly expose the actual boundary/code input and negative provenance
    # without recursively walking the old frozen metadata graph.
    needle = "        recursionPolicy='No recursive descriptor/JSON/source-tree discovery; source paths are a finite explicit old-membership replacement map plus named additions.',\n"
    assert source.count(needle) == 1
    source = source.replace(needle, "        scalarCountBoundary=dict(source=pin(OUT / 'prepare_source.py'), callable='selected_producer_count',\n                                 selectedCountOperand='producer.selectedDefinitionCount',\n                                 selectedPartitionOperand='producer.selectedCountsSeparate',\n                                 acceptedCountOperand='current accepted Root266 receipt',\n                                 tests='CurrentProducerCountMetadataControls uses the same actual function; definitions unexecuted'),\n        negativePredecessor=scope['immutableNegativeR9'], negativeDisposition=scope['negativeR9Disposition'],\n" + needle)
    source = source.replace("currentDefinitionCounts=counts, modelsDefined=sum(counts), priorDefinitionsRetained=174,", "currentDefinitionCounts=counts, modelsDefined=sum(counts), priorDefinitionsRetained=174,\n        selectedUpstreamProducerCount=producer_count, selectedUpstreamProducerCountType='PLAIN_INT',")
    source = source.replace("        productionBindingChanged=True, currentCollectorTyped81TransferredAsControllerData=False,", "        productionBindingChanged=True, currentCollectorTyped81TransferredAsControllerData=False,\n        scalarCountBoundary=dict(generator=pin(OUT / 'prepare_source.py'), callable='selected_producer_count',\n                                 selectedScalar=producer_count, structuredProducerMapChanged=False),\n        conservativeCurrentMetadataMethodExclusion=dict(actor='/root/controller_model_metadata_source2',\n            reason='Separately owned current Root metadata-method author excluded conservatively, not relabeled as this SOURCE writer.'),")
    ast.parse(source, filename=str(NEW))
    compile(source, str(NEW), 'exec')
    with NEW.open('x') as stream:
        stream.write(source)
    print('WROTE_SOURCE2_GENERATOR', len(source.encode()), hashlib.sha256(source.encode()).hexdigest())


if __name__ == '__main__':
    main()
