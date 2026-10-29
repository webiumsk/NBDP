"""SOURCE-only exact five-key request derivation. No tool/process execution."""
import hashlib,json,shlex,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def need(v,m):
    if not v:raise ValueError(m)
def read(p):
    p=Path(p);need(p.is_file() and not p.is_symlink() and p.stat().st_size<=16777216,'SMALL_REGULAR_METADATA');raw=p.read_bytes();return json.loads(raw),dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def main(args):
    need(len(args)==6 and args[0]=='--plan' and args[2]=='--plan-sha' and args[4]=='--root-ack','EXACT_METADATA_ARGUMENTS')
    plan,pp=read(args[1]);need(pp['sha256']==args[3] and plan['readiness'] is True and plan['sourceContractReady'] is True,'ACTUAL_FROZEN_SOURCE2_PLAN_REQUIRED')
    ack,ap=read(args[5]);need(ack['plan']==pp and ack['actor']=='/root' and ack['executionAuthorized'] is True and ack['noRetry'] is True,'ACTUAL_EXTERNAL_ROOT_ACK')
    need(all(v is not None for v in plan['pendingBindings'].values()),'NULL_FINAL_BINDING_REFUSAL')
    tools=plan['tools'];tokens=['/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8',tools['timeout']['path'],'--signal=KILL','1203s',tools['python']['path'],'-I','-B',str(HERE/'capture.py'),'--execute-once','--root-ack-sha',ap['sha256']]
    request=dict(cmd=shlex.join(tokens),workdir=str(HERE),login=False,yield_time_ms=1000,max_output_tokens=2000)
    need(set(request)==set('cmd workdir login yield_time_ms max_output_tokens'.split()),'EXACT_FIVE_KEY_REQUEST')
    print(json.dumps(request))
if __name__=='__main__':main(sys.argv[1:])
