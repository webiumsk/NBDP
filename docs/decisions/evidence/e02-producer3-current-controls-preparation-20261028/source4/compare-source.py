"""Static SOURCE AST comparison only; no target import/evaluation/execution."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028')
DATA=Path('/Data/nbdp-e02-tooling-20261027')


def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def functions(path):
    tree=ast.parse(path.read_text())
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}


def main():
    rows=[]
    for name in ('capture-template.py','test_admission_models.py','capture-a/capture-controls.py','capture-b/capture-controls.py','assemble-source-only.py'):
        before=ROOT/'source3'/name;after=ROOT/'source4'/name
        a=functions(before);b=functions(after)
        assert a==b,'Capture/admission helper function AST drift: '+name
        identical=before.read_bytes()==after.read_bytes()
        if name!='assemble-source-only.py':assert identical,'Target source byte drift: '+name
        rows.append({'name':name,'before':pin(before),'after':pin(after),'wholeFileByteIdentical':identical,
            'allTopLevelFunctionClassAstsIdentical':True,'definitions':list(a)})
    result={'schema':'e02-producer3-source4-static-source-equivalence-v1','evidenceType':'ACTUAL_SOURCE_AST_PARSE_ONLY_NOT_RUNTIME_MODELS',
        'scope':'SOURCE3-to-SOURCE4 target capture/model/helper code equality; metadata assembler OUT path differs only',
        'files':rows,'metadataConstructionChanges':['New source4 paths','Explicit supplemental contract leaf','Fresh source4 metadata root IDs',
            'Negative invocation disposition custody','Metadata-only frozen-plan request derivation utility'],
        'modelsControlsExecuted':0,'targetImports':0}
    out=ROOT/'source4/source-equivalence.json'
    with out.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sourceEquivalence':pin(out),'allTargetFunctionsIdentical':True,'modelsControlsExecuted':0}))


if __name__=='__main__':main()
