"""Pure finite declared-input predicate; never walk, stat or observe inputs.

Root's separately reviewed observer supplies genuine current rows and membership
observations. This Source definition is not a snapshot or daemon observation.
"""
from native_metadata import need, closed, integer, equal, pin_shape, I64


def validate_observation(specification, rows, memberships):
    equal(specification['schema'], 'e02-current-helper-generic-input-source-v1')
    need(type(specification['files']) is list and 1 <= len(specification['files']) <= 20000,
         'FINITE_DECLARED_INPUTS')
    expected = {pin_shape(row['pin'])['path']: row for row in specification['files']}
    equal(len(expected), len(specification['files']), 'UNIQUE_WHOLE_INPUT_PATHS')
    need(type(rows) is list and len(rows) == len(expected), 'COMPLETE_CURRENT_ROWS')
    observed = {}
    for row in rows:
        closed(row, ('pin', 'mode', 'uid', 'gid', 'device', 'inode', 'mtimeNs', 'ctimeNs', 'links'))
        path = pin_shape(row['pin'])['path']
        need(path in expected and path not in observed, 'NO_UNKNOWN_DUPLICATE_INPUT')
        equal(row['pin'], expected[path]['pin'])
        equal(row['mode'], expected[path]['mode'], 'EXPECTED_INPUT_MODE')
        for key in ('uid', 'gid', 'device', 'inode'):
            integer(row[key], 0)
        for key in ('mtimeNs', 'ctimeNs'):
            integer(row[key], 0, I64)
        equal(row['links'], 1, 'UNALIASED_CURRENT_INPUT')
        observed[path] = row
    need(type(memberships) is list and len(memberships) == len(specification['memberships']),
         'ALL_DECLARED_MEMBERSHIPS')
    for actual, wanted in zip(memberships, specification['memberships']):
        closed(actual, ('root', 'files', 'directories', 'aliases', 'specialFiles'))
        equal(actual['root'], wanted['root'])
        equal(actual['files'], wanted['files'], 'WHOLE_CURRENT_FILE_MEMBERSHIP')
        equal(actual['directories'], wanted['directories'], 'WHOLE_CURRENT_DIRECTORY_MEMBERSHIP')
        equal(actual['aliases'], [])
        equal(actual['specialFiles'], [])
    return dict(expectedFiles=len(expected), currentRowsMatch=True,
                observationIdentityMeaning='NAMESPACE_LOCAL_NOT_HOST_CONTINUITY_NOT_RACE_FREE',
                daemonImageAdmitted=False, originalLeaseAdmitted=False,
                privatePathsAdmitted=False, runtimeAuthorized=False)


def unchanged(before, after):
    equal(before, after, 'EXACT_CURRENT_BEFORE_AFTER_ROWS')
    return True
