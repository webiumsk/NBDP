"""Pure regression for completed emitted input-authority artifacts.

No filesystem, clock, subprocess or target activity occurs here. The caller
supplies actual completed JSON objects; strict production projection/coverage
validation is imported byte-identically from the accepted predecessor engine.
"""
import copy
from input_authority import validate_expected_authority


def check_emitted(authority, baseline, manifest, inherited_self, source1=None):
    names=[]
    count=validate_expected_authority(authority,baseline,manifest)
    assert count==manifest['actualInputCount']
    names.append('completed_emitted_projection_and_coverage_positive')
    assert 'currentExpectedInputAuthority' not in authority['coverage']
    assert authority['coverage']['historicalPriorExpectedInputAuthority']==[inherited_self]
    assert manifest['requiredCoverage']['currentExpectedInputAuthority']==[manifest['currentExpectedInputAuthority']]
    assert manifest['currentExpectedInputAuthority']!=inherited_self
    actual={r['pin']['path']:r for r in manifest['files']}
    assert actual[inherited_self['path']]['pin']==inherited_self
    names.append('inherited_sidecar_row_and_named_historical_coverage_retained')

    def refused(a,m,expected):
        try:validate_expected_authority(a,baseline,m)
        except ValueError as error:
            assert expected in str(error),(expected,str(error))
            return
        raise AssertionError('UNSAFE_ARTIFACT_ACCEPTANCE:'+expected)

    missing=copy.deepcopy(manifest);missing['requiredCoverage'].pop('historicalPriorExpectedInputAuthority')
    refused(authority,missing,'EXACT_EXPLICIT_READ_SITE_COVERAGE')
    names.append('missing_emitted_historical_coverage_refused')
    substituted=copy.deepcopy(manifest)
    substituted['requiredCoverage']['historicalPriorExpectedInputAuthority']=[manifest['currentExpectedInputAuthority']]
    refused(authority,substituted,'EXACT_EXPLICIT_READ_SITE_COVERAGE')
    names.append('substituted_emitted_historical_coverage_refused')
    duplicate=copy.deepcopy(manifest)
    duplicate['requiredCoverage']['currentExpectedInputAuthority'].append(inherited_self)
    refused(authority,duplicate,'AUTHORITY_PIN_UNIFORMLY_PROTECTED')
    names.append('newself_reserved_coverage_exactly_one_pin')
    polluted=copy.deepcopy(authority)
    polluted['coverage']['currentExpectedInputAuthority']=[inherited_self]
    refused(polluted,manifest,'EXACT_EXPLICIT_READ_SITE_COVERAGE')
    names.append('authority_excludes_reserved_newself_key')
    omission=copy.deepcopy(manifest)
    omission['files']=[r for r in omission['files'] if r['pin']!=inherited_self]
    omission['actualInputCount']-=1
    refused(authority,omission,'COMPLETE_EXACT_CURRENT_PROJECTION_NO_EXTRA_OMISSION_OR_MODE_CHANGE')
    names.append('historical_sidecar_row_cannot_be_dropped')
    if source1 is not None:
        old_authority,old_manifest=source1
        refused(old_authority,old_manifest,'EXACT_EXPLICIT_READ_SITE_COVERAGE')
        names.append('preserved_actual_source1_negative_reproduced')
    return dict(schema='e02-capture-emitted-artifact-regression-v1',checks=len(names),cases=names,
                actualInputCount=count,authorityCoverageGroups=len(authority['coverage']),
                manifestCoverageGroups=len(manifest['requiredCoverage']),
                inheritedAuthorityRetained=True,strictValidatorUnchanged=True,
                targetScopesExecuted=0,executionAuthorized=False)
