"""Metadata-only exact request renderer; never executes a capture or tool."""
import hashlib
import json
from pathlib import Path
import shlex

HERE=Path('/Data/nbdp-e02-tooling-20261027/consumer5-control-capture-preparation-r1')

def pin(path):
    raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def main():
    plan=json.loads((HERE/'plan.json').read_bytes())
    method=json.loads((HERE/'method-source.json').read_bytes())
    grant_path=HERE/'coordinator-acknowledgement.json'
    grant=json.loads(grant_path.read_bytes())
    keys='schema actor executionAuthorized purpose consumerSource methodSource plan inputManifest outerRequest authors operators consumerSourceReviews captureSourceReviews noRetry runtimeAuthorized servicesAuthorized sdkAuthorized nativeAuthorized androidAuthorized'.split()
    assert set(grant)==set(keys) and len(keys)==19
    assert grant['schema']=='e02-consumer5-control-capture-root-ack-v1'
    assert grant['actor']=='/root' and grant['executionAuthorized'] is True and grant['noRetry'] is True
    assert grant['purpose']=='ONE_FIXED_CONSUMER5_86_36_8_9_DATA_BATCH_ONLY'
    assert grant['methodSource']==pin(HERE/'method-source.json')
    assert grant['plan']==method['plan']==pin(HERE/'plan.json')
    assert grant['inputManifest']==method['inputManifest']==pin(HERE/'input-manifest.json')
    assert grant['consumerSource']==plan['consumerSource']
    assert grant['outerRequest']==pin(HERE/'outer-request-template.json')
    request=json.loads((HERE/'outer-request-template.json').read_bytes())
    assert request==plan['outerRequestTemplate'] and set(request)=={'cmd','workdir','login','yield_time_ms','max_output_tokens'}
    token='__ACTUAL_ROOT_ACK_SHA256__';digest=pin(grant_path)['sha256']
    assert request['cmd'].count(token)==1
    request['cmd']=request['cmd'].replace(token,digest)
    assert shlex.split(request['cmd'])==[digest if value==token else value for value in plan['outerArgvTemplate']]
    print(json.dumps(request,ensure_ascii=False,allow_nan=False))

if __name__=='__main__':main()
