"""Derive a future original tool request from the frozen SOURCE4 plan.

Metadata only: prints JSON and never executes the returned command. The caller
must submit the returned object unchanged to tools.exec_command and preserve the
actual response. No manual environment, signal, timeout, or argv reconstruction.
"""
import copy
import json
from pathlib import Path
import re
import runpy
import shlex
import sys

ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP')
DATA=Path('/Data/nbdp-e02-tooling-20261027/producer-controls-preparation-r3-source4')
OUT=ROOT/'docs/decisions/evidence/e02-producer3-current-controls-preparation-20261028/source4'


def main():
    assert len(sys.argv)==3 and sys.argv[1]=='--capture-id' and sys.argv[2] in ('capture-a','capture-b')
    mode=sys.argv[2]
    own=runpy.run_path(str(DATA/'assemble-source-only.py'),run_name='source_metadata_helpers_only')
    pin=own['pin'];load=own['load']
    subject=load(OUT/'subject.json');plan_path=OUT/mode/'control-plan.json';plan=load(plan_path)
    assert subject['captures'][mode]['controlPlan']==pin(plan_path)
    assert plan['captureId']==mode and plan['schema']=='e02-producer3-fixed-control-capture-plan-v1'
    ack_path=OUT/mode/'coordinator-acknowledgement.json';ack_pin=pin(ack_path);ack=load(ack_path)
    assert ack['schema']=='e02-producer3-controls-root-ack-v2' and ack['captureId']==mode
    for key in ('runner','runnerSubject','controlPlan','frozenInputs'):
        assert ack[key]==subject['captures'][mode][key]
    request=copy.deepcopy(plan['outerRequestTemplate'])
    assert set(request)=={'cmd','workdir','login','yield_time_ms','max_output_tokens'}
    token='__ACTUAL_ROOT_ACK_SHA256__';assert request['cmd'].count(token)==1
    assert re.fullmatch('[0-9a-f]{64}',ack_pin['sha256'])
    request['cmd']=request['cmd'].replace(token,ack_pin['sha256'])
    argv=[ack_pin['sha256'] if value==token else value for value in plan['outerArgvTemplate']]
    assert shlex.split(request['cmd'])==argv
    print(json.dumps(request,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':main()
