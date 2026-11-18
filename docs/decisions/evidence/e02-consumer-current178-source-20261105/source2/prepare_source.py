"""Bounded SOURCE2 metadata generation; no target imports or models."""
import ast
import hashlib
import json
from pathlib import Path
import shutil

OWNED=Path(__file__).resolve().parent
EVIDENCE=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence')
PREVIOUS=OWNED.parent/'source1'
SOURCE=OWNED/'source'
SCOPE_PATH=EVIDENCE/'e02-goal-resume-20261104/consumer-current178-source2-root-scope-20261105.json'
ACTOR='/root/consumer_current178_source'


def pin(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n');return pin(path)


def assigned(text):
    values={}
    for node in ast.parse(text).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:values[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    return values


def replacements(text,changes):
    lines=text.splitlines(keepends=True);edits=[]
    for node in ast.parse(text).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in changes:
            name=node.targets[0].id;edits.append((node.lineno-1,node.end_lineno,name+' = '+repr(changes[name])+'\n'))
    assert len(edits)==len(changes)
    for start,end,value in reversed(edits):lines[start:end]=[value]
    return ''.join(lines)


def main():
    scope=json.loads(SCOPE_PATH.read_bytes())
    assert pin(SCOPE_PATH)['sha256']=='675975d6d23b472f40983fa60c66996911580011e7182eb343a876750a9011eb'
    assert scope['owner']==ACTOR and scope['ownedWritableRoot']==str(OWNED)
    freeze=json.loads(Path(scope['negativePredecessorFreeze']['path']).read_bytes())
    assert len(freeze['inputs'])==695 and len(scope['reviewerExclusions'])==45
    for p in freeze['inputs']:assert pin(p['path'])==p
    for key in ('negativePredecessor','negativePredecessorEntry','negativePredecessorFreeze','negativeDisposition'):
        assert pin(scope[key]['path'])==scope[key]
    for key in ('negativeReviews','negativeFindings'):
        for p in scope[key]:assert pin(p['path'])==p
    assert json.loads(Path(scope['negativeDisposition']['path']).read_bytes())['decision']=='HOLD_SOURCE1_UNCHANGED_NO342_EXECUTION'
    for p in (PREVIOUS/'source').iterdir():
        if p.is_file():shutil.copyfile(p,SOURCE/p.name)
    for p in (PREVIOUS/'contracts').iterdir():
        if p.is_file():shutil.copyfile(p,OWNED/'contracts'/p.name)
    for name in ('current-inputs.json','immutable-validation-reuse.json','collector_reader_method.txt'):
        shutil.copyfile(PREVIOUS/name,OWNED/name)
    code=(SOURCE/'consumer.py').read_text();constants=assigned(code)
    changes=dict(CONTROL_FILES=constants['CONTROL_FILES']+('test_import_closure.py',),
        CURRENT_CONSUMER_ACCEPTANCE_CONTRACT=pin(OWNED/'contracts/current-consumer-acceptance-contract.json'),
        CURRENT_COLLECTOR_PREREQUISITE_CONTRACT=pin(OWNED/'contracts/current-collector-prerequisite-contract.json'),
        CURRENT_CONTROL_ACTORS=sorted(set(constants['CURRENT_CONTROL_ACTORS'])|{'/root/consumer_source_qa_e0e55c4e','/root/consumer_source_security_e0e55c4e'}))
    (SOURCE/'consumer.py').write_text(replacements(code,changes))
    outputs=(SOURCE/'capture_outputs.py').read_text()
    assert outputs.count('from contracts import need,closed\n')==1 and outputs.count('from explicit_inputs import decode_metadata\n')==1
    outputs=outputs.replace('from contracts import need,closed\n','from capture_contracts import need,closed\n').replace('from explicit_inputs import decode_metadata\n','from strict import loads as decode_metadata\n')
    accepted=EVIDENCE/'e02-consumer266-source-preparation-20261104/r2/source/capture_outputs.py'
    assert outputs.encode()==accepted.read_bytes()
    (SOURCE/'capture_outputs.py').write_text(outputs)
    save(OWNED/'negative-inputs.json',dict(schema='e02-consumer-current178-source2-negative-inputs-v1',actor=ACTOR,
        source1CaptureOutputs=pin(PREVIOUS/'source/capture_outputs.py'),source1Subject=scope['negativePredecessor'],
        source1Entry=scope['negativePredecessorEntry'],source1Freeze=scope['negativePredecessorFreeze'],
        source1Disposition=scope['negativeDisposition'],source1Reviews=scope['negativeReviews'],source1Findings=scope['negativeFindings'],
        negativeMeaning='Preserved original HOLD; no Source1 approval or model result exists.',modelsExecuted=0,executionAuthorized=False))
    save(OWNED/'preparation-stage.json',dict(schema='e02-consumer-current178-source2-preparation-v1',actor=ACTOR,
        rootScope=pin(SCOPE_PATH),sourceRoot=str(SOURCE),negativePredecessor=scope['negativePredecessor'],
        negativeFreezeInputsPreserved=695,strictOutputBodyRestoredByteExactlyToAcceptedBaseline=True,
        runtimeFiles=constants['RUNTIME_FILES'],controlFiles=changes['CONTROL_FILES'],modelsExecuted=0,targetImports=0,
        phase='SOURCE2_GENERATION_ONLY_PENDING_STATIC_BUNDLE_AND_INDEPENDENT_REVIEW',executionAuthorized=False))
    for p in SOURCE.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
    print(json.dumps(dict(sourceRoot=str(SOURCE),preservedNegativeFreezeInputs=695,
        runtimeFiles=len(constants['RUNTIME_FILES']),controlGroups=len(changes['CONTROL_FILES']),modelsExecuted=0,targetImports=0)))


if __name__=='__main__':main()
