"""Read-only stdlib Source checks. Never import project/helper/model code."""
import ast
import hashlib
import json
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
E = HERE.parents[1]
STRICT_NAMES = ('need', 'closed', 'integer', 'text', 'same', 'equal',
                'safe_path', 'pin_shape', 'preflight_json', 'wall_path',
                'validate_tree', 'decode_json', 'response_metadata')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def pin(path):
    need(path.is_absolute() and not path.is_symlink(), 'REGULAR_EXPLICIT_SOURCE')
    info = path.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_size <= 16777216, 'BOUNDED_SOURCE')
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def doc(path):
    return json.loads(path.read_bytes())


def exact(descriptor):
    need(pin(Path(descriptor['path'])) == descriptor, 'EXACT_UNCHANGED_PIN')


def functions(path):
    tree = ast.parse(path.read_bytes(), filename=str(path))
    return {x.name: ast.dump(x, include_attributes=False)
            for x in tree.body if isinstance(x, ast.FunctionDef)}


def names(path):
    tree = ast.parse(path.read_bytes(), filename=str(path))
    return [c.name + '.' + m.name for c in tree.body if isinstance(c, ast.ClassDef)
            for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]


def main():
    scope_path = E/'e02-goal-resume-20261104/helper-current178-source2-root-scope-20261105.json'
    need(pin(scope_path)['sha256'] == 'a21d31ec165fb9a0d6e798462a8bdeb0a37add22cd07644477ac1d35f620334d', 'ROOT_SCOPE')
    scope = doc(scope_path)
    need(scope['ownedWritableRoot'] == str(HERE), 'OWNED_SOURCE2')
    subject, entry = doc(HERE/'subject.json'), doc(HERE/'review-entrypoint.json')
    exact(entry['subject'])
    for descriptor in subject['sourceInputs']:
        exact(descriptor)
    need(len(subject['sourceInputs']) == subject['sourceCount'], 'SOURCE_COUNT')
    need(len({x['path'] for x in subject['sourceInputs']}) == subject['sourceCount'], 'UNIQUE_SOURCE_PATHS')
    archive = doc(HERE/'archive.json')
    exact(subject['archive'])
    for pair in archive['copies']:
        exact(pair['source']); exact(pair['repositoryCopy'])
        need(Path(pair['source']['path']).read_bytes() == Path(pair['repositoryCopy']['path']).read_bytes(), 'EXACT_ARCHIVE_BYTES')
    need(archive['copiedFiles'] == len(archive['copies']), 'ARCHIVE_COUNT')
    need(archive['copiedBytes'] == sum(x['source']['bytes'] for x in archive['copies']), 'ARCHIVE_BYTES')
    freeze = doc(Path(scope['negativePredecessorFreeze']['path']))
    exact(scope['negativePredecessorFreeze'])
    need(len(freeze['inputs']) == 201, 'ALL201_NEGATIVE_PINS')
    for descriptor in freeze['inputs']:
        exact(descriptor)
    for descriptor in [scope['negativePredecessor'], scope['negativeDisposition'],
                       *scope['negativeReviews'], *scope['negativeFindings']]:
        exact(descriptor)
    old_names = names(Path(scope['negativePredecessor']['path']).parent/'test_helpers.py')
    current_names = names(HERE/'test_helpers.py')
    need(len(old_names) == 38 and set(old_names) <= set(current_names), 'PRESERVED38_NAMES')
    need(len(set(current_names)) == len(current_names), 'UNIQUE_MODEL_NAMES')
    plan = doc(HERE/'control-plan.json')
    need(plan['modelsDefined'] == len(current_names) == subject['modelsDefined'] == entry['modelsDefined'], 'ACTUAL_AST_COUNT')
    need(plan['groups'][0]['expectedNames'] == current_names, 'EXACT_CONTROL_PLAN')
    strict = E/'e02-controller-current-model-preparation-20261105/source2/controller_model_metadata.py'
    accepted, current = functions(strict), functions(HERE/'native_metadata.py')
    need(all(accepted[x] == current[x] for x in STRICT_NAMES), 'ALL13_STRICT_AST_IDENTICAL')
    # Parse all executable Source files without loading any of them.
    pyfiles = sorted(HERE.glob('*.py'))
    for path in pyfiles:
        ast.parse(path.read_bytes(), filename=str(path))
    fixed = doc(HERE/'templates.json')
    literals = {}
    for node in ast.parse((HERE/'current_bindings.py').read_bytes()).body:
        if isinstance(node, ast.Assign):
            need(len(node.targets) == 1 and isinstance(node.targets[0], ast.Name), 'LITERAL_ONLY_BINDING')
            literals[node.targets[0].id] = ast.literal_eval(node.value)
    need(literals['CURRENT'] == scope['currentTuple'] == subject['currentTuple'], 'EXACT_CURRENT_TUPLE')
    need(fixed['trueAuthors'] == literals['TRUE_AUTHORS'] == subject['sourceContributors'], 'IMMUTABLE_AUTHOR_LITERALS')
    need(fixed['conservativeReviewerExclusions'] == literals['EXCLUSIONS'] == subject['reviewerExclusions'], 'IMMUTABLE_EXCLUSIONS')
    need(len(literals['EXCLUSIONS']) == 41 and set(literals['TRUE_AUTHORS']) <= set(literals['EXCLUSIONS']), 'FULL41_UNION')
    need({'/root/helper_source_qa_19b50833','/root/helper_source_security_19b50833'} <= set(literals['TRUE_AUTHORS']), 'ACTUAL_DESIGN_CONTRIBUTORS')
    need(fixed['compiledControllerBindings']['sourceModes'] == literals['SOURCE_MODES'], 'EXACT_SOURCE_MODES')
    need(all(type(x) is int and x == 0o664 for x in literals['SOURCE_MODES'].values()), 'SOURCE0664')
    need(pin(HERE/'helper-probe-data-acceptance-contract.json')['sha256'] == '14f859491411c84ec03bc552f0be287269f6ff94a9d4b43cf7cdf22e650fdacc', 'ROOT24_UNCHANGED')
    predecessor = Path(scope['negativePredecessor']['path']).parent
    for filename in ('native_metadata.py', 'custody_bridge.py', 'generic_inputs.py'):
        need((HERE/filename).read_bytes() == (predecessor/filename).read_bytes(), 'UNCHANGED_TYPED_AND_CUSTODY_SOURCE')
    need(subject['modelsExecuted'] == plan['modelsExecuted'] == entry['modelsExecuted'] == 0, 'ZERO_MODELS')
    need(subject['targetImports'] == plan['targetImports'] == entry['targetImports'] == 0, 'ZERO_TARGET_IMPORTS')
    need(subject['selfApproval'] is False and subject['executionAuthorized'] is False, 'SOURCE_ONLY')
    need(subject['actualHelperData'] is subject['actualAccount'] is subject['actualOriginalLease'] is subject['actualRootRelease'] is None, 'UNISSUED_ROOT_AUTHORITIES')
    need(fixed['bridgeDependency']['source'] is fixed['bridgeDependency']['sourceAcceptance'] is fixed['bridgeDependency']['actualForegroundSession'] is None, 'UNISSUED_BRIDGE')
    method = doc(HERE/'method-contract.json')
    need(method['runtimeAudit'] == dict(freshChecks=64, closeCalls=1, joins=65,
         auditObservations=266, controllerMockControls=178, countsAreDifferentDomains=True), 'UNCHANGED_RUNTIME_DOMAIN')
    need(entry['actualRendererInvocations'] == entry['actualCollectorCalls'] == entry['actualSizingExperiments'] == 0, 'ZERO_TARGET_ACTIONS')
    print(json.dumps(dict(schema='e02-helper-current178-source2-static-result-v1',
        entrypoint=pin(HERE/'review-entrypoint.json'), subject=pin(HERE/'subject.json'),
        sourceInputs=subject['sourceCount'], archiveCopies=archive['copiedFiles'],
        archiveBytes=archive['copiedBytes'], predecessorUnchangedPins=201,
        predecessorNames=38, modelsDefined=len(current_names), newModels=len(current_names)-38,
        strictAstPrimitives=13, pythonSourcesParsed=len(pyfiles), reviewerExclusions=41,
        trueAuthors=len(literals['TRUE_AUTHORS']), modelsExecuted=0, targetImports=0,
        runtimeActions=0, acceptedSource=False, executionAuthorized=False), sort_keys=True))


if __name__ == '__main__':
    main()
