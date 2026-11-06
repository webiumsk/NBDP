"""Pure finite expected-input projection checks. No filesystem or target imports."""
import hashlib
import json


def need(value, message):
    if not value:
        raise ValueError(message)


def retained_digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_expected_authority(authority, baseline, manifest):
    need(authority['schema'] == 'e02-producer4-current-expected-input-authority-v1', 'TYPED_CURRENT_EXPECTED_AUTHORITY')
    need(authority['baselineManifest'] == manifest['baselineInputAuthority'], 'EXACT_PINNED2175_PREDECESSOR')
    need(authority['baselineRowCount'] == len(baseline['files']) == baseline['actualInputCount'] == 2175, 'EXACT2175_PREDECESSOR_ROWS')
    original = {row['pin']['path']: row for row in baseline['files']}
    removed = authority['supersessions']
    need(len(original) == 2175 and len(removed) == 6, 'EXACT_SIX_EXPLICIT_SUPERSESSIONS')
    removed_paths = {row['before']['pin']['path'] for row in removed}
    need(len(removed_paths) == 6 and all(original.get(row['before']['pin']['path']) == row['before'] for row in removed), 'EXACT_OLD_DESCRIPTOR_MODE_ROLE_ORIGIN')
    retained = [original[path] for path in sorted(original) if path not in removed_paths]
    need(len(retained) == authority['retainedRowCount'] == 2169 and retained_digest(retained) == authority['retainedRowsSha256'], 'ALL2169_ROWS_RETAINED_EXACTLY')
    expected = {row['pin']['path']: row for row in retained}
    for row in authority['additionalRows']:
        path = row['pin']['path']
        need(path not in expected and path not in removed_paths, 'NO_DUPLICATE_OR_REMOVED_ALIAS_ADDITION')
        expected[path] = row
    need(len(expected) == authority['projectedRowCountExcludingSelf'], 'DERIVED_CURRENT_INPUT_COUNT')
    sidecar = manifest['currentExpectedInputAuthority']
    need(sidecar['path'] not in expected and sidecar['path'] not in removed_paths, 'ACYCLIC_AUTHORITY_SELF_ROW_EXTERNAL')
    expected[sidecar['path']] = dict(pin=sidecar, mode=authority['selfMode'], role='METADATA_AUTHORITY', origin='CURRENT_FINITE_EXPECTED_INPUT_AUTHORITY')
    actual = {row['pin']['path']: row for row in manifest['files']}
    need(len(actual) == len(manifest['files']) == manifest['actualInputCount'] == len(expected) and actual == expected, 'COMPLETE_EXACT_CURRENT_PROJECTION_NO_EXTRA_OMISSION_OR_MODE_CHANGE')
    need(manifest['requiredCoverage']['currentExpectedInputAuthority'] == [sidecar], 'AUTHORITY_PIN_UNIFORMLY_PROTECTED')
    coverage = {key: value for key, value in manifest['requiredCoverage'].items() if key != 'currentExpectedInputAuthority'}
    need(coverage == authority['coverage'], 'EXACT_EXPLICIT_READ_SITE_COVERAGE')
    for group in coverage.values():
        need(type(group) is list and group, 'NONEMPTY_EXPECTED_COVERAGE')
        for pin in group:
            need(pin['path'] not in removed_paths and actual.get(pin['path'], {}).get('pin') == pin, 'NO_DANGLING_OR_REMOVED_READ_OPERAND')
    need(manifest['fullTrees'] == baseline['fullTrees'] and manifest['nodeDependencies'] == baseline['nodeDependencies'], 'SDK434_GUARD522_NODE_MEMBERSHIP_IDENTICAL')
    need(authority['wholeInputQualified'] is False and authority['executionAuthorized'] is False, 'PREPARATION_IS_NOT_INPUT_QUALIFICATION_OR_AUTHORITY')
    return len(actual)
