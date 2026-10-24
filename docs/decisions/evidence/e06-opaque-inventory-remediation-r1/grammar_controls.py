"""Prepared source/grammar controls: importing activates nothing.

A separately reviewed CONTROL-only outer launcher must verify current complete
source approvals/config/release and import the actual fixed admission module.
This module does not grant authority or import project code. No test was run by
the author. Metadata-only cases do not confer accepted inventory membership.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

ADMISSION={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/admission.py', 'bytes': 53263, 'sha256': '24d928e46fa538b139c0e8418eeae777d682a99173a8f1a03334374b1626ec9f'}
BRIDGE={'path': '/home/peterhorvath/apps/bitcoin/NBDP/experiments/prototypes/e06_relay_https_negative_v1/bridge-schemas.json', 'bytes': 158719, 'sha256': '89173066418eddd16f1d2a14ecee4b04470072385c1883aab48a01dd6e41281a'}
PYTHON={'path': '/home/peterhorvath/.miniforge3/bin/python3.13', 'bytes': 32959480, 'sha256': '5e2f62ca6ab9c6992460493de8a8867e84f8e6078f0e5c197b5232b79e4b35f1'}
ENV={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC', 'WS_NO_BUFFER_UTIL': '1', 'WS_NO_UTF_8_VALIDATE': '1'}

def need(ok,message):
    if not ok:raise AssertionError(message)


def descriptor(file):
    p=Path(file);need(p.is_absolute() and not p.is_symlink() and p.resolve(strict=True)==p,'Canonical original file')
    h=hashlib.sha256();n=0
    with p.open('rb') as stream:
        while block:=stream.read(1048576):h.update(block);n+=len(block)
    return {'path':str(p),'bytes':n,'sha256':h.hexdigest()}


def evaluate(A,config):
    """Definitions only; outer admission/lifecycle capture is mandatory separately."""
    need(config['ready'] is True and config['executionReleased'] is False,'PENDING_CURRENT_SOURCE_PACK_OR_OUTER_RELEASE')
    need(config['sourceApproval'] is not None and config['sourceClosure'] is not None,
         'Fresh actual SOURCE approval/closure required; previous449 is historical')
    need(dict(os.environ)==ENV and str(Path(sys.executable).resolve())==PYTHON['path'],'Exact interpreter/environment')
    need(descriptor(PYTHON['path'])==PYTHON,'Original interpreter pin')
    need(str(Path(A.__file__).resolve(strict=True))==ADMISSION['path'] and descriptor(A.__file__)==ADMISSION,'Actual current admission module')
    need(descriptor(BRIDGE['path'])==BRIDGE,'Original unchanged bridge schema')
    out=Path(config['outputRoot']);st=out.lstat()
    need(out.is_dir() and not out.is_symlink() and out.resolve(strict=True)==out
      and st.st_uid==os.getuid() and st.st_mode&0o777==0o700,'Fresh root-owned outer0700 output')
    defs=A.document(BRIDGE)['definitions'];rows=[];reads=[];active=[False]
    def audit(event,args):
        if active[0] and event=='open':reads.append({'path':str(args[0]),'mode':str(args[1]),'flags':args[2]})
    sys.addaudithook(audit)
    def record(name,fn,expected=None,no_reads=False,scope='ACTUAL_PRIVATE_HELPER_GRAMMAR_ONLY'):
        first=None;value=None;start=len(reads);active[0]=True
        try:value=fn()
        except A.Refusal as error:first=str(error)
        finally:active[0]=False
        observed=reads[start:]
        matched=(first is None if expected is None else first==expected) and (not no_reads or not observed)
        row={'id':name,'scope':scope,'expectedError':expected,'observedError':first,
          'metadataAccepted':first is None,'matched':matched,'actualFileOpenObservations':observed,
          'noFileReadRequired':no_reads}
        rows.append(row)
        need(matched,'CONTROL_MISMATCH:'+name+':'+str(first))
        return value
    # These synthetic descriptors test metadata grammar only. They are never
    # inserted into an accepted inventory/mapping or treated as source authority.
    base={'path':'/opaque-grammar-metadata-only/not-read','bytes':0,'sha256':'0'*64}
    def candidate(**changes):return dict(base,**changes)
    for n,size in [('zero',0),('raw32_boundary',33554432),('above_raw32',33554433),
      ('actual_node_metadata',121613584),('opaque512_boundary',536870912)]:
        record('OPAQUE_ACCEPT_'+n,lambda size=size:A._local_inventory_descriptor(candidate(bytes=size),defs),no_reads=True)
    invalid=[('negative',candidate(bytes=-1),'SCHEMA_INTEGER'),
      ('bool',candidate(bytes=True),'SCHEMA_INTEGER'),
      ('float',candidate(bytes=1.0),'SCHEMA_INTEGER'),
      ('string_size',candidate(bytes='1'),'SCHEMA_INTEGER'),
      ('above512',candidate(bytes=536870913),'LOCAL_INVENTORY_OPAQUE_FILE_BOUND'),
      ('above_safe_integer',candidate(bytes=9007199254740992),'SCHEMA_INTEGER'),
      ('relative_path',candidate(path='relative'),'SCHEMA_PATTERN'),
      ('bad_hash',candidate(sha256='bad'),'SCHEMA_PATTERN'),
      ('hash_type',candidate(sha256=1),'SCHEMA_STRING'),
      ('extra_key',dict(base,extra=True),'CLOSED_KEYS'),
      ('missing_key',{k:v for k,v in base.items() if k!='sha256'},'CLOSED_KEYS')]
    for name,pin,error in invalid:
        record('OPAQUE_REFUSE_'+name,lambda pin=pin:A._local_inventory_descriptor(pin,defs),error,no_reads=True)
    need(A._admission_evidence.get() is None,'Nominal helper context is absent')
    record('OPAQUE_CAP_WITH_ACTUAL_INVENTORY_CONTEXT',
      lambda:A._with_inventory(lambda inventory:A._local_inventory_descriptor(candidate(bytes=536870913),defs)),
      'LOCAL_INVENTORY_OPAQUE_FILE_BOUND',no_reads=True)
    # Confirm the actual loop uses this helper BEFORE unchanged member/hash/remember.
    tree=ast.parse(Path(ADMISSION['path']).read_bytes())
    local=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='local_worker_inputs')
    loop=next(n for n in ast.walk(local) if isinstance(n,ast.For)
      and isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Attribute)
      and isinstance(n.iter.func.value,ast.Name) and n.iter.func.value.id=='role_map')
    names=[n.value.func.id for n in loop.body[:3] if isinstance(n,ast.Expr)
      and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)]
    need(names==['_local_inventory_descriptor','member','need'],'Real inventory helper/member/hash order')
    need(isinstance(loop.body[3],ast.If),'Actual optional remember remains after stream hash')
    rows.append({'id':'REAL_LOOP_ORDER','scope':'SOURCE_AST_ORDER_ONLY','matched':True})
    record('OUTPUT_DESCRIPTOR_STILL_RAW32',lambda:A.validate(candidate(bytes=33554433),'@descriptor',defs),
      'SCHEMA_INTEGER',no_reads=True,scope='ACTUAL_UNCHANGED_OUTPUT_DESCRIPTOR_GRAMMAR')
    record('LOADS_STILL_RAW32',lambda:A.loads(b' '*(33554432+1)),
      'JSON_BOUND',no_reads=True,scope='ACTUAL_UNCHANGED_BOUNDED_JSON_READER')
    # A real exclusive own sparse file exercises actual streaming descriptor I/O.
    # No descriptor result, membership validator or returned bytes are mocked.
    testfile=out/'raw-read-boundary.bin';fd=os.open(testfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:os.ftruncate(fd,33554433);os.fsync(fd)
    finally:os.close(fd)
    real=descriptor(testfile)
    record('CHECKED_STILL_RAW32',lambda:A.checked(real),'DATA_READ_BOUND',
      scope='ACTUAL_REAL_SPARSE_FILE_STREAM_HASH_THEN_RAW_READ_REFUSAL')
    rows[-1]['actualSparseFile']=real
    need(len(rows[-1]['actualFileOpenObservations'])==1,'Exactly streaming hash open; no buffered JSON read')
    need(descriptor(ADMISSION['path'])==ADMISSION and descriptor(BRIDGE['path'])==BRIDGE,'Original sources unchanged')
    return {'schema':'e06-opaque-inventory-source-grammar-controls-v1','rows':rows,
      'checks':len(rows),'matched':all(r['matched'] for r in rows),'sourceApproval':config['sourceApproval'],
      'sourceClosure':config['sourceClosure'],'admission':ADMISSION,'originalBridgeSchema':BRIDGE,
      'actualFullInventoryGateExecuted':False,'nativeJobs':0,'rawPayloadsRegenerated':False,
      'limits':['Actual private helper/unchanged readers plus labelled source-order inspection only.',
        'Synthetic metadata cases are not accepted inventory artifacts or native interoperability.',
        'Fresh controlled outer admission, process/no-call traps and raw lifecycle capture required.']}


if __name__=='__main__':
    sys.stderr.write('SOURCE DEFINITIONS ONLY: use a separately reviewed/released trusted outer CONTROL runner.\n')
    raise SystemExit(2)
