"""SOURCE-only extraction of existing finite ownership/lease helpers."""
from pathlib import Path
import ast

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
BASE=ROOT/'experiments/prototypes/e02_ordinary_minimum_v1/supervisor.py'
OUT=ROOT/'experiments/prototypes/e02_transport_query_diagnostic_v1'
raw=BASE.read_text();tree=ast.parse(raw)
def take(name):return ast.get_source_segment(raw,next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name))
helpers=['need','strict','digest','pin','checked','put','jsonbytes','exact_cid_absent','load_module','finalize','run_service']
header='''"""SOURCE ONLY: finite isolated transport diagnostic, no Android or service on import."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import time
import uuid
HERE=Path(__file__).resolve().parent
REPO=Path('/home/peterhorvath/apps/bitcoin/NBDP')
LAB=Path('/tmp/nbdp-e02-transport-query-diagnostic-v1')
ROLES=('anchor','rs-relay','fixture')
RUNTIME='sha256:07892c65089b8d11c50b50931a09fb9600a13e0909af4a2b3e27029ab16f1e6f'
RELAY='sha256:fe586a0bc68edefb553a62d21983de469128f7cb785bfcc2ef7c82dbf1cded82'
LIMITS={'anchor':(128,64,1),'rs-relay':(512,128,1),'fixture':(1024,128,1)}
PY=['/guard-python/lib/ld-linux-x86-64.so.2','--inhibit-cache','--library-path','/guard-python/lib','/guard-python/bin/python3.11','-B','-P','-S','-s']
LOG_OPTIONS=['--log-driver','local','--log-opt','max-size=16m','--log-opt','max-file=1','--log-opt','compress=false']
SCOPE='E02_TRANSPORT_QUERY_DIAGNOSTIC_ONLY_NO_ANDROID_NO_E02_COMPLETION'
'''
klass=take('Runtime')
# Remove only inactive Android methods/branches; copied finite command/custody/
# exact-CID cleanup implementations are preserved exactly, not a new manager.
k=ast.parse(klass).body[0]
for name in ('adb','snapshot','map_session_pin'):
 segment=ast.get_source_segment(klass,next(n for n in k.body if isinstance(n,ast.FunctionDef) and n.name==name))
 klass=klass.replace('    '+segment+'\n\n','')
 k=ast.parse(klass).body[0]
klass=klass.replace("        self.check()\n        image = RELAY if role == 'rs-relay' else RUNTIME", "        need(role in ROLES, 'Only three diagnostic roles allowed')\n        self.check()\n        image = RELAY if role == 'rs-relay' else RUNTIME")
klass=klass.replace("        if role == 'rs-relay':\n            mount(self.plan['guardBundleRoot'], '/guard-python')", "        mount(self.plan['guardBundleRoot'], '/guard-python')\n        if role == 'rs-relay':")
a=klass.index("        if role == 'android':\n            mount(self.plan['sdkRoot']");b=klass.index('        memory, pids, cpus = LIMITS[role]',a);klass=klass[:a]+klass[b:]
a=klass.index("        if role == 'android':\n            args += ['--device'");b=klass.index("        entry['command']",a);klass=klass[:a]+klass[b:]
klass=klass.replace("need(devices == ([{'PathOnHost': '/dev/kvm', 'PathInContainer': '/dev/kvm',\n                          'CgroupPermissions': 'rw'}] if role == 'android' else []), 'Exact KVM device only')", "need(devices == [], 'No devices/SDK/Android in diagnostic')")
(OUT/'supervisor.py').write_text(header+'\n\n'+'\n\n'.join(take(n) for n in helpers)+'\n\n'+klass+'\n\n'+(Path(__file__).parent/'supervisor-new-entrypoints.txt').read_text())
(OUT/'lease_guard.py').write_bytes((BASE.parent/'lease_guard.py').read_bytes())
print('Prepared SOURCE extraction only; no helper import, guard issue or services.')
