"""Definitions only: four actual reader families and current retained operands.

All generated API/release-shaped values are explicitly synthetic memory data.
No API command, helper, SDK, Docker or model is dispatched by these fixtures.
"""
import copy
import json
from pathlib import Path
import shlex
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consumer
import capture_contracts as capture
import collector_contracts as collector
import probe_adapter
import request_families as family
from strict import Refusal, Files

RUN = '1' * 32


def requests():
    model = dict(cmd='/synthetic/model -v', workdir='/synthetic', login=False,
                 yield_time_ms=1000, max_output_tokens=20000)
    host = probe_adapter.expected_request(
        dict(concretePlan=dict(path='/synthetic/plan', sha256='a' * 64),
             rootRelease=dict(path='/synthetic/release', sha256='b' * 64)),
        dict(runtimeSources=[dict(path='/synthetic/host.py', bytes=1, sha256='c' * 64)]))
    capture_request = capture.expected_request(
        dict(tools=dict(timeout=dict(path='/usr/bin/timeout'),
                        python=dict(path='/home/peterhorvath/.miniforge3/bin/python3.13'))),
        'd' * 64, '/synthetic/capture')
    argv = [*collector.PREFIX, collector.PYTHON, '-I', '-B', collector.SCRIPT_PIN['path'],
            'reserve', '--run-id', RUN]
    collection = dict(cmd=shlex.join(argv), workdir=collector.SCRIPT_PIN['path'].rsplit('/', 1)[0],
                      login=False, yield_time_ms=1000, max_output_tokens=2000,
                      sandbox_permissions='require_escalated',
                      justification='Synthetic collector reader fixture only; never dispatched.')
    return dict(MODEL5=model, HOST7=host, COLLECTOR7=collection, PRODUCER_CAPTURE7=capture_request)


def origin(request, output='SYNTHETIC_NOT_NATIVE_CUSTODY', counter=True):
    response = dict(chunk_id='SYNTHETIC_NOT_PLATFORM', wall_time_seconds=0.001,
                    exit_code=0, output=output)
    if counter:
        response['original_token_count'] = 1
    return dict(schema='e02-actual-tool-custody-v1', operator='/root',
                launch=dict(toolName='tools.exec_command', actualArguments=copy.deepcopy(request),
                            unmodifiedResponse=response), polls=[])


def check(value, request, name):
    return family.validate_origin(value, request, ['/root'], family=name)


class CurrentRequestFamilyModels(unittest.TestCase):
    def test_all_four_exact_actual_reader_paths_positive(self):
        for name, request in requests().items():
            value = origin(request)
            self.assertEqual(check(value, request, name), 'SYNTHETIC_NOT_NATIVE_CUSTODY')

    def test_model5_never_requires_or_invents_optional_native_counter(self):
        request = requests()['MODEL5']; value = origin(request, counter=False)
        self.assertEqual(check(value, request, 'MODEL5'), 'SYNTHETIC_NOT_NATIVE_CUSTODY')
        self.assertNotIn('original_token_count', value['launch']['unmodifiedResponse'])

    def test_host7_and_capture7_native_counter_absence_preserved(self):
        for name in ('HOST7', 'PRODUCER_CAPTURE7'):
            request = requests()[name]; value = origin(request, counter=False)
            self.assertEqual(check(value, request, name), 'SYNTHETIC_NOT_NATIVE_CUSTODY')
            self.assertNotIn('original_token_count', value['launch']['unmodifiedResponse'])

    def test_collector7_missing_counter_is_permanent_family_refusal(self):
        request = requests()['COLLECTOR7']; value = origin(request, counter=False)
        with self.assertRaisesRegex(Refusal, 'COLLECTOR_PRESENT_NATIVE_COUNTER_REQUIRED'):
            check(value, request, 'COLLECTOR7')
        self.assertNotIn('original_token_count', value['launch']['unmodifiedResponse'])

    def test_legacy5_does_not_qualify_current_host_or_capture7(self):
        for name in ('HOST7', 'PRODUCER_CAPTURE7'):
            request = requests()[name]; value = origin(request)
            for key in ('sandbox_permissions', 'justification'):
                del value['launch']['actualArguments'][key]
            with self.assertRaises(Refusal):check(value, request, name)

    def test_operational7_does_not_widen_model5(self):
        request = requests()['MODEL5']; value = origin(request)
        value['launch']['actualArguments'].update(family.HOST_POLICY)
        with self.assertRaises(Refusal):check(value, request, 'MODEL5')

    def test_all_family_pairs_are_distinct_readers(self):
        values = requests()
        for selected, request in values.items():
            for other, foreign in values.items():
                if selected != other:
                    with self.assertRaises((Refusal, ValueError)):
                        check(origin(foreign), request, selected)

    def test_unknown_family_refused_before_any_fallback(self):
        request = requests()['MODEL5']
        with self.assertRaisesRegex(Refusal, 'EXPLICIT_KNOWN_REQUEST_FAMILY'):
            check(origin(request), request, 'UNKNOWN')

    def test_host7_policy_strings_are_exact_unprojected_fields(self):
        request = requests()['HOST7']
        for key, bad in [('sandbox_permissions', 'use_default'), ('justification', 'different')]:
            value = origin(request); value['launch']['actualArguments'][key] = bad
            with self.assertRaises(Refusal):check(value, request, 'HOST7')

    def test_capture7_bare_actual_sha_never_quoted_substitution(self):
        request = requests()['PRODUCER_CAPTURE7']; value = origin(request)
        value['launch']['actualArguments']['cmd'] = request['cmd'][:-64] + "'" + 'd' * 64 + "'"
        self.assertEqual(shlex.split(value['launch']['actualArguments']['cmd']), shlex.split(request['cmd']))
        with self.assertRaises(Refusal):check(value, request, 'PRODUCER_CAPTURE7')

    def test_full_request_false_int_and_float_aliases_refused(self):
        request = requests()['MODEL5']
        for key, bad in [('login', 0), ('yield_time_ms', 1000.0), ('max_output_tokens', True)]:
            value = origin(request); value['launch']['actualArguments'][key] = bad
            with self.assertRaises(Refusal):check(value, request, 'MODEL5')

    def test_true_null_integer_string_native_flags_refused(self):
        request = requests()['MODEL5']
        for flag in family.FLAGS:
            for bad in (True, None, 0, '', 'false'):
                value = origin(request); value['launch']['unmodifiedResponse'][flag] = bad
                with self.assertRaises(Refusal):check(value, request, 'MODEL5')

    def test_absent_or_exact_false_native_flags_remain_lossless(self):
        request = requests()['MODEL5']; value = origin(request)
        value['launch']['unmodifiedResponse'].update({key: False for key in family.FLAGS})
        saved = copy.deepcopy(value)
        self.assertEqual(check(value, request, 'MODEL5'), 'SYNTHETIC_NOT_NATIVE_CUSTODY')
        self.assertEqual(value, saved)

    def test_token_counter_type_and_cap_boundaries(self):
        request = requests()['MODEL5']
        for bad in (False, 1.0, -1, 20001):
            value = origin(request); value['launch']['unmodifiedResponse']['original_token_count'] = bad
            with self.assertRaises(Refusal):check(value, request, 'MODEL5')

    def test_wall_domains_and_only_wall_float_path(self):
        request = requests()['MODEL5']
        for bad in (False, '0.1', -0.1, float('nan'), float('inf')):
            value = origin(request); value['launch']['unmodifiedResponse']['wall_time_seconds'] = bad
            with self.assertRaises(Refusal):check(value, request, 'MODEL5')
        value = origin(request); value['launch']['unmodifiedResponse']['original_token_count'] = 1.0
        with self.assertRaises(Refusal):family.decode_tool_origin(json.dumps(value).encode())

    def test_direct_and_yielded_complete_session_lossless(self):
        request = requests()['MODEL5']; value = origin(request, output='first')
        value['launch']['unmodifiedResponse'].pop('exit_code')
        value['launch']['unmodifiedResponse']['session_id'] = 77
        value['polls'] = [dict(toolName='tools.write_stdin', actualArguments=dict(session_id=77,
            chars='', yield_time_ms=1000, max_output_tokens=20000),
            unmodifiedResponse=dict(wall_time_seconds=0.01, exit_code=0, output='last', original_token_count=1))]
        saved = copy.deepcopy(value)
        self.assertEqual(check(value, request, 'MODEL5'), 'firstlast')
        self.assertEqual(value, saved)

    def test_session_and_terminal_aliases_and_late_frames_refused(self):
        request = requests()['MODEL5']
        for bad in (False, 0.0, '0'):
            value = origin(request); value['launch']['unmodifiedResponse']['exit_code'] = bad
            with self.assertRaises(Refusal):check(value, request, 'MODEL5')
        value = origin(request); value['polls'] = [copy.deepcopy(value['launch'])]
        with self.assertRaisesRegex(Refusal, 'NO_FRAME_AFTER_TERMINAL'):check(value, request, 'MODEL5')

    def test_duplicate_nonfinite_negativezero_and_depth_api_json_refused(self):
        for raw in (b'{"x":0,"x":1}', b'{"x":NaN}', b'{"x":-0}', ('[' * 66 + '0' + ']' * 66).encode()):
            with self.assertRaises((Refusal, ValueError)):family.decode_tool_origin(raw)

    def test_collector_cli_reader_is_not_a_host_or_model_decoder(self):
        request = requests()['COLLECTOR7']; value = origin(request, output='{"synthetic":true}')
        raw = json.dumps(value).encode()
        self.assertEqual(probe_adapter.validate_collector_origin(raw, request,
            ['/root']), dict(synthetic=True))
        for name in ('HOST7', 'MODEL5'):
            with self.assertRaises((Refusal, ValueError)):
                probe_adapter.validate_collector_origin(json.dumps(origin(requests()[name])).encode(),
                    requests()[name], ['/root'])

    def test_collector_direct_fixture_route_cannot_be_operational_evidence(self):
        request = requests()['COLLECTOR7']; request['cmd'] = shlex.join(shlex.split(request['cmd'])[len(collector.PREFIX):])
        with self.assertRaisesRegex(Refusal, 'OPERATIONAL_COLLECTOR_REQUIRES_CLEANENV'):
            check(origin(request), request, 'COLLECTOR7')

    def test_exact_current_composite_collector_actor_schema(self):
        value = dict(schema='e02-collector-actual-request7-typed-origin-composite-source-subject-v2',
                     actor='/root/SYNTHETIC_CREATOR', sourceContributorUnion=['/root/SYNTHETIC_CREATOR'], executionAuthorized=False)
        self.assertEqual(probe_adapter.source_actors(value), {'/root/SYNTHETIC_CREATOR'})
        for field, bad in [('executionAuthorized', 0), ('sourceContributorUnion', []), ('actor', None)]:
            candidate = copy.deepcopy(value); candidate[field] = bad
            with self.assertRaises((Refusal, ValueError)):probe_adapter.source_actors(candidate)

    def test_current_accepted_r10_178_model_data_is_consumed_without_activation(self):
        import json
        root = Path(__file__).resolve().parents[1] / 'current-inputs.json'
        selected = json.loads(root.read_bytes())
        files = Files(['/Data/nbdp-e02-tooling-20261027', '/home/peterhorvath/apps/bitcoin/NBDP',
                       '/home/peterhorvath/.miniforge3', '/usr/bin'])
        triple = {key: selected[key] for key in ('controllerSource', 'controllerSourceAcceptance', 'controllerControlDataAcceptance')}
        source, plan, counts, total, _ = probe_adapter.validate_controller_authority(files, triple,
            consumer.HELPER_PRODUCER, consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT,
            set(consumer.CURRENT_CONTROL_ACTORS))
        self.assertEqual(total,178);self.assertEqual(counts,[39,42,10,19,23,19,26]);files.recheck()
        self.assertIsNone(consumer.CURRENT_HELPER_PROBE_DATA)
        self.assertIsNone(consumer.CURRENT_HELPER_PROBE_ACCEPTANCE)

    def test_actual_accepted_typed_collector81_prerequisites_read_without_command_dispatch(self):
        files=Files(['/Data/nbdp-e02-tooling-20261027','/home/peterhorvath/apps/bitcoin/NBDP',
                     '/home/peterhorvath/.miniforge3','/usr/bin'])
        actors=probe_adapter.validate_collector_authority(files,consumer.CURRENT_COLLECTOR_PREREQUISITE_CONTRACT,set())
        self.assertIn('/root/helper_policy_source7',actors)
        self.assertIn('/root/collector_typed_qa_1592707b',actors)
        files.recheck()

    def test_typed_collector_composite_actor_must_be_in_explicit_union(self):
        value=dict(schema='e02-collector-actual-request7-typed-origin-composite-source-subject-v2',
                   actor='/root/UNDECLARED_SYNTHETIC',sourceContributorUnion=['/root/OTHER_SYNTHETIC'],executionAuthorized=False)
        with self.assertRaisesRegex(Refusal,'COMPOSITE_ACTOR_IN_UNION'):probe_adapter.source_actors(value)

    def test_collector7_operational_operator_cannot_be_nonroot_actor(self):
        request=requests()['COLLECTOR7'];value=origin(request);value['operator']='/root/SYNTHETIC_OTHER'
        with self.assertRaisesRegex(Refusal,'OPERATIONAL_COLLECTOR_ROOT_OPERATOR'):
            family.validate_origin(value,request,['/root/SYNTHETIC_OTHER'],family='COLLECTOR7')

    def test_actual_current_producer_reader_binds_ab6_native4ce_and_fresh_e01(self):
        files=Files(['/Data/nbdp-e02-tooling-20261027','/home/peterhorvath/apps/bitcoin/NBDP'])
        value=consumer.current_producer(files,consumer.CURRENT_PRODUCER)
        self.assertEqual(value['sourceRevision'],'FIXTURE_EOSE_QUEUE_CALLER_R1')
        self.assertEqual(value['sourceCount'],64);self.assertEqual(value['runtimeSourceCount'],22)
        self.assertEqual(consumer.CURRENT_HELPER_APK['sha256'],'ab6e2628677d563fe3214e92ef1f25942aaf5e720de974db77bd4927beca2f83')
        self.assertEqual(consumer.CURRENT_NATIVE['sha256'],'4ce385c5b1a713b35d58d787d94fbc298d139aa2e813daec15b2e99289cefd86')
        files.recheck()

    def test_old_producer_tuple_refused_by_actual_current_producer_reader(self):
        legacy={'path': '/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r5-source4-lease-r1/subject.json', 'bytes': 35901, 'sha256': 'fe619502879cd18a7c1e5be36891f679497406c56a4a60b36368595f9bfb897e'}
        files=Files(['/Data/nbdp-e02-tooling-20261027','/home/peterhorvath/apps/bitcoin/NBDP'])
        with self.assertRaisesRegex(Refusal,'EXACT_CURRENT_PRODUCER4_SOURCE4_CURRENT_ARTIFACT_BINDINGS'):
            consumer.current_producer(files,legacy)


if __name__ == '__main__':
    unittest.main()
