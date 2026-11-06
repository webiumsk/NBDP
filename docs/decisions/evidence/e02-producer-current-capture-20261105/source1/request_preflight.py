"""Pure request predicate preflight; never submit an API request or start capture."""
import json
import pathlib
import shlex
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'capture'))
try:
    from contracts import expected_request, validate_origin, canonical_request, need, REQUEST_KEYS
finally:
    sys.path.pop(0)


def check(plan, ack_sha, here, actual_request, operator):
    expected = expected_request(plan, ack_sha, here)
    need(canonical_request(actual_request) == canonical_request(expected), 'WHOLE_ACTUAL_SEVEN_KEY_REQUEST_EXACT_TYPES_AND_BYTES')
    frame = dict(toolName='tools.exec_command', actualArguments=expected,
                 unmodifiedResponse=dict(exit_code=0, output='SYNTHETIC_PREFLIGHT_ONLY'))
    origin = dict(schema='e02-actual-tool-custody-v1', operator=operator, launch=frame, polls=[])
    need(validate_origin(origin, expected, [operator]) == 'SYNTHETIC_PREFLIGHT_ONLY', 'CANONICAL_REQUEST_ACCEPTED')
    quoted = dict(expected)
    quoted['cmd'] = expected['cmd'][:-len(ack_sha)] + "'" + ack_sha + "'"
    need(shlex.split(quoted['cmd']) == shlex.split(expected['cmd']), 'QUOTED_SHA_IS_SAME_ARGV_BUT_DIFFERENT_REQUEST_BYTES')
    origin['launch']['actualArguments'] = quoted
    refused = False
    try:
        validate_origin(origin, expected, [operator])
    except ValueError:
        refused = True
    need(refused, 'QUOTED_SHA_REQUEST_REFUSED_WITHOUT_REPAIR')
    return dict(schema='e02-current-capture-request7-preflight-result-v1', checks=2,
                canonicalAccepted=True, extraQuoteRefused=True, actualToolCalls=0,
                targetModelsExecuted=0, executionAuthorized=False)


def main(args):
    need(len(args) == 4, 'PLAN ACTUAL_ACK_SHA ACTUAL_GENERATED_REQUEST_JSON OPERATOR')
    plan = json.loads(pathlib.Path(args[0]).read_bytes())
    actual = json.loads(pathlib.Path(args[2]).read_bytes())
    print(json.dumps(check(plan, args[1], str(HERE / 'capture'), actual, args[3])))


if __name__ == '__main__':
    main(sys.argv[1:])
