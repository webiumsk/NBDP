"""Once-only reviewed foreground dispatch. SOURCE draft refuses while bindings are NULL."""
import hashlib,json,os,pathlib,re,resource,subprocess,time
HERE=pathlib.Path('/Data/nbdp-e02-tooling-20261027/completion-primary-wrapper-preparation-r4')
AUTHORITY='FIXED_SAME_T0_ENV_CONFIG_AND_PRIMARY_RELEASE_ONLY'

def need(v,m):
    if not v:raise ValueError(m)

def pin(p):
    p=pathlib.Path(p);need(p.is_absolute() and not p.is_symlink(),'CANONICAL_REGULAR_FILE')
    for q in p.parents:need(not q.is_symlink(),'SYMLINK_ANCESTOR')
    need(p.is_file(),'REGULAR_FILE');raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def checked(d):need(type(d) is dict and set(d)=={'path','bytes','sha256'} and pin(d['path'])==d,'EXACT_PIN');return pathlib.Path(d['path'])
def load(p):
    raw=pathlib.Path(p).read_bytes();need(len(raw)<=16777216,'METADATA_BOUND')
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_KEY');out[k]=v
        return out
    def reject(_):raise ValueError('NONFINITE_METADATA')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)
def put(name,data):
    raw=(json.dumps(data,indent=2)+'\n').encode();need(len(raw)<=16777216,'OUTPUT_BOUND')
    with (HERE/name).open('xb') as f:f.write(raw)

def authorize_dispatch(plan_pin,plan,template_pin,t,auth,caller):
    need(plan['runtimeReady'] is True and all(v is not None for v in plan['current'].values()),'SOURCE_ONLY_NULL_FINAL_BINDINGS_NOT_READY')
    need(set(auth)=={'schema','executionAuthorized','scope','caller','template','reviews','renderAuthority'},'CLOSED_COORDINATOR_AUTHORIZATION')
    need(auth['schema']=='e02-wrapper-dispatch-authorization-v2' and auth['executionAuthorized'] is True and auth['scope']=='ONE_CURRENT_COMPLETION_PRIMARY_ONLY' and auth['caller']==caller and auth['template']==template_pin and auth['renderAuthority']==AUTHORITY,'EXPLICIT_ONE_USE_CLOSED_RENDER_AUTHORIZATION')
    for d in auth['reviews']:checked(d)
    need(set(t)==set('schema actor executionAuthorized scope runId plan sourceSubject sourceQa sourceSecurity modelAcceptance inputAcceptance issuedAtUtcNs notAfterUtcNs renderAuthority'.split()),'CLOSED_ROOT_RELEASE_TEMPLATE')
    need(t['schema']=='nbdp-completion-primary-wrapper-root-release-v3' and t['actor']=='/root' and t['executionAuthorized'] is True and t['scope']==auth['scope'] and t['plan']==plan_pin and t['renderAuthority']==AUTHORITY,'EXACT_ROOT_TEMPLATE')
    need(type(t['runId']) is str and re.fullmatch('[0-9a-f]{32}',t['runId']),'EXACT_RUN_ID')
    need(t['issuedAtUtcNs'] is None and t['notAfterUtcNs'] is None,'ONLY_CLOCK_SLOTS_NULL')
    for key in ('plan','sourceSubject','sourceQa','sourceSecurity','modelAcceptance','inputAcceptance'):checked(t[key])
    need(t['sourceSubject']==plan['current']['wrapperSource'],'CURRENT_WRAPPER_SOURCE')
    sources=load(checked(t['sourceSubject']))['sources'];need(caller in sources,'REVIEWED_DISPATCH');[checked(d) for d in sources]
    for d in plan['tools'].values():checked(d)
    need(not (HERE/('attempt-'+t['runId'])).exists(),'FRESH_ATTEMPT')
    return t


def render_once(t):
    # O_EXCL claim is the first mutation; occupied/duplicate dispatch cannot render.
    with (HERE/'dispatch-once.lock').open('xb') as f:f.write((t['runId']+'\n').encode())
    t['issuedAtUtcNs']=time.time_ns();t['notAfterUtcNs']=t['issuedAtUtcNs']+600*10**9
    put('root-release.json',t);release=pin(HERE/'root-release.json')
    return release


def main():
    os.umask(0o077);plan_pin=pin(HERE/'plan-draft.json');plan=load(plan_pin['path'])
    need(plan['runtimeReady'] is True and all(v is not None for v in plan['current'].values()),'SOURCE_ONLY_NULL_FINAL_BINDINGS_NOT_READY')
    template_pin=pin(HERE/'release-template.json');t=load(template_pin['path']);auth=load(HERE/'coordinator-runtime-authorization.json')
    authorize_dispatch(plan_pin,plan,template_pin,t,auth,pin(__file__))
    release=render_once(t)
    argv=[plan['tools']['timeout']['path'],'--signal=TERM','--kill-after=3s','597s',plan['tools']['python']['path'],'-I','-B',str(HERE/'launch.py'),'--plan-sha',plan_pin['sha256'],'--release',release['path'],'--release-sha',release['sha256']]
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}
    put('outer-request.json',dict(schema='e02-wrapper-dispatch-request-v2',argv=argv,cwd=str(HERE),environment=env,release=release,startedUtcNs=time.time_ns(),retryAuthorized=False))
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    start=time.monotonic()
    with (HERE/'outer.stdout').open('xb') as out,(HERE/'outer.stderr').open('xb') as err:
        p=subprocess.Popen(argv,cwd=HERE,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True,preexec_fn=limits)
        put('outer-child.json',dict(pid=p.pid,ownedPopenHandle=True))
        # GNU timeout owns the group; this wait does not invent pipe EOF.
        code=p.wait(timeout=605)
    result=dict(schema='e02-wrapper-dispatch-result-v2',exitCode=code,reaped=True,durationSeconds=time.monotonic()-start,stdout=pin(HERE/'outer.stdout'),stderr=pin(HERE/'outer.stderr'),captureTransport='REGULAR_FILES',pipeEofEstablished=False,cleanupMustBeReviewed=True,retryAuthorized=False,attemptPath=str(HERE/('attempt-'+t['runId'])))
    put('outer-result.json',result)
    print(json.dumps(dict(exitCode=code,attemptPath=result['attemptPath'],durationSeconds=result['durationSeconds'])))
    return code
if __name__=='__main__':raise SystemExit(main())
