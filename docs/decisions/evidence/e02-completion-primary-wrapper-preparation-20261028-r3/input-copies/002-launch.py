"""Completion-primary synchronous wrapper. SOURCE preparation grants no execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import socket
import stat
import subprocess
import sys
import time

HERE=Path('/Data/nbdp-e02-tooling-20261027/completion-primary-wrapper-preparation-r2')
ROOT=Path('/home/peterhorvath/apps/bitcoin/NBDP');EXP=ROOT/'experiments'
OWNER='e02-completion-primary-wrapper-r2'
# Local helper loading is explicit and reviewed; no ambient PYTHONPATH lookup.
import importlib.util
_spec=importlib.util.spec_from_file_location('closed_render',HERE/'render_data.py')
render=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(render)
NATIVE_SHA='4ce385c5b1a713b35d58d787d94fbc298d139aa2e813daec15b2e99289cefd86'
E01_SHA='85905dd8a9de0285ebec8f04c39a59105c27387cd3b5b0bae18f81ab73dc1b06'
RAW_LIMIT=4194304
SKIP={'scope':'Amethyst ordinary-client rendering','reason':'No isolated Android runtime/client installation; adapter ordinary-chat dispatch was exercised. Canonical ordinary-client rendering control was NOT EXECUTED; no ecosystem UI result claimed.','mandatory':True}


def need(ok,why):
    if not ok:raise ValueError(why)


def full(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value),'FULL_ID_REQUIRED');return value


def safe(p):
    p=Path(p);need(p.is_absolute() and '..' not in p.parts,'CANONICAL_PATH')
    for q in (p,*p.parents):need(not q.is_symlink(),'SYMLINK_COMPONENT')
    return p


def pin(p):
    p=safe(p)
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
        before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=2147483648,'REGULAR_BOUNDED_INPUT')
        h=hashlib.sha256();count=0
        while b:=f.read(1048576):h.update(b);count+=len(b)
        after=os.fstat(f.fileno())
    key=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    need(key(before)==key(after)==key(p.stat()) and count==before.st_size,'PIN_DRIFT')
    return dict(path=str(p),bytes=count,sha256=h.hexdigest())


def checked(d):
    need(type(d) is dict and set(d)=={'path','bytes','sha256'} and type(d['bytes']) is int
         and 0<=d['bytes']<=2147483648 and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256'])
         and pin(d['path'])==d,'EXACT_PIN');return Path(d['path'])


def load(p):
    raw=Path(p).read_bytes();need(len(raw)<=16777216,'METADATA_BOUND')
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_KEY');out[k]=v
        return out
    def reject(_):raise ValueError('NONFINITE_METADATA')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)


def scoped_snapshot(descriptors):
    rows=[]
    for d in sorted(descriptors,key=lambda x:x['path']):
        p=checked(d);st=p.stat()
        rows.append(dict(pin=d,mode=stat.S_IMODE(st.st_mode),uid=st.st_uid,gid=st.st_gid))
    need(len({r['pin']['path'] for r in rows})==len(rows),'NO_DUPLICATE_SELECTED_INPUTS')
    return rows


def descriptor_dag(roots):
    """Follow only explicitly selected descriptors, never enumerate the workspace."""
    found={};todo=list(roots)
    while todo:
        d=todo.pop();render.pin_shape(d)
        if d['path'] in found:
            need(found[d['path']]==d,'CONFLICTING_INPUT_DESCRIPTOR');continue
        checked(d);found[d['path']]=d
        need(len(found)<=20000,'SELECTED_DAG_BOUND')
        if Path(d['path']).suffix!='.json':continue
        value=load(d['path']);stack=[value]
        while stack:
            v=stack.pop()
            if type(v) is dict:
                if set(v)=={'path','bytes','sha256'}:todo.append(v)
                else:stack.extend(v.values())
            elif type(v) is list:stack.extend(v)
    return sorted(found.values(),key=lambda x:x['path'])


def closure(actual,expected):need(actual==expected,'COMPLETE_SELECTED_PROTECTED_INPUT_CLOSURE')


def fresh_paths(paths):
    need(all(not p.exists() and not p.is_symlink() for p in paths),'FRESH_OUTPUTS_AND_STORES')


def fixed_plan(p):
    need(p['cwd']==str(EXP) and p['runtimeReady'] is True,'FIXED_IMMUTABLE_ACTUAL_EXPERIMENTS_CWD')
    need(p['tools']['node']['path']=='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node' and p['tools']['timeout']['path']=='/usr/bin/timeout'
         and p['tools']['docker']['path']=='/usr/bin/docker' and p['tools']['python']['path']=='/usr/bin/python3.12','FIXED_TOOL_TARGETS')
    need(p['clocks']==dict(childSeconds=240,killGraceSeconds=3,totalLeaseSeconds=600,setupSeconds=120,cleanupSeconds=90,remainingChildAdmissionSeconds=243,dispatchOuterSeconds=597),'FIXED_OPERATIONAL_MAXIMA')
    need(p['native']['sha256']==NATIVE_SHA and p['e01']['sha256']==E01_SHA,'FIXED_ACCEPTED_NATIVE_E01')
    need(p['images']=={'strfry':'sha256:d72c7eb4e19562e22c24924ea51bc345ea5d22d03ada1429a46e0bb90ea97d40','rs-relay':'sha256:fe586a0bc68edefb553a62d21983de469128f7cb785bfcc2ef7c82dbf1cded82'},'FIXED_TWO_RELAY_IMAGES')
    need(p['labels']=={'nbdp.owner':OWNER,'nbdp.scope':'completion-primary-only'} and p['user']==str(os.getuid())+':'+str(os.getgid()) and os.getuid()!=0,'FIXED_NONROOT_OWNERSHIP')
    need(p['imageLabels']=={'strfry':{},'rs-relay':{'org.opencontainers.image.source':'https://github.com/rust-lang/docker-rust'}} and p['entrypoints']=={'strfry':['/src/strfry'],'rs-relay':['/src/target/release/nostr-rs-relay']},'EXACT_OBSERVED_IMAGE_METADATA')
    need(set(p['configs'])=={'strfry','rs-relay'} and p['configs']['strfry']['path']==str(EXP/'docker/strfry.conf') and p['configs']['rs-relay']['path']==str(EXP/'docker/rs-relay.toml'),'FIXED_READONLY_CONFIGS')
    need(p['proxySource']['path']==str(EXP/'docker/proxy.mjs'),'ABSOLUTE_PINNED_PROXY_SOURCE')
    need(p['renderAuthority']==render.RENDER_AUTHORITY,'NO_ARBITRARY_RENDER_AUTHORITY')
    need(all(v is not None for v in p['current'].values()),'ALL_CURRENT_BINDINGS_REQUIRED')
    for d in p['current'].values():checked(d)


def native_binding(e01,native):
    need(e01['status']=='PASS' and len(e01['tests'])==140 and not e01['skipped']
         and all(t['ok'] is True for t in e01['tests']) and len(e01['source_sha256'])==19,'EXACT_ACCEPTED_E01_SCOPE')
    need(native['bytes']==24100272 and native['sha256']==e01['environment']['rust_binary_sha256']==NATIVE_SHA,'CURRENT_NATIVE_E01_EQUALITY')


def exact_absence(code,out,err,name,network=False):
    errors=(('Error response from daemon: network '+name+' not found').encode(),('Error: No such network: '+name).encode()) if network else (
        ('Error response from daemon: No such container: '+name).encode(),('Error: No such object: '+name).encode())
    return type(code) is int and code==1 and out.strip() in (b'',b'[]') and err.rstrip(b'\r\n') in errors


def remaining(end,seconds):
    left=end-time.monotonic();need(left>seconds,'FINITE_DEADLINE_RESERVE');return seconds


def lease_end(issued,expires,now,started,monotonic_now):
    need(type(issued) is int and type(expires) is int and type(now) is int and 0<=issued<=now<expires
         and 0<expires-issued<=600*10**9,'FINITE_600_SECOND_ROOT_LEASE')
    return min(started+600,monotonic_now+(expires-now)/10**9)


def identity(d,cid,role,p,run,network_id,network_name):
    need(d['Id']==full(cid) and d['Image']==p['images'][role] and d['Name']=='/'+network_name+'-'+role,'OWNED_CID_IMAGE_NAME')
    c,h=d['Config'],d['HostConfig']
    need(c['Labels']==dict(p['imageLabels'][role],**p['labels'],**{'nbdp.run':run,'nbdp.role':role}) and c['User']==p['user'],'OWNED_LABELS_USER')
    need(c['Entrypoint']==p['entrypoints'][role] and c['WorkingDir']=='/src','EXACT_IMAGE_ENTRYPOINT_AND_WORKDIR')
    need(c['Cmd']==(['relay'] if role=='strfry' else ['--db','/data']),'ORIGINAL_RELAY_COMMAND')
    need(h['NetworkMode']==full(network_id) and h['ReadonlyRootfs'] is True and h['Privileged'] is False,'OWNED_NETWORK_READONLY')
    need(h['NanoCpus']==2000000000 and h['Memory']==1073741824 and h['PidsLimit']==128,'ORIGINAL_RELAY_RESOURCE_CAPS')
    need(h.get('CapDrop')==['ALL'] and any(x in ('no-new-privileges','no-new-privileges:true') for x in h.get('SecurityOpt',[])),
         'ADOPTED_DROP_ALL_AND_NO_NEW_PRIVILEGES')
    need(not h.get('CapAdd') and not h.get('PortBindings') and not h.get('Devices') and not h.get('PidMode')
         and not h.get('UTSMode') and h.get('IpcMode') in ('private','shareable'),'NO_HOST_PRIVILEGES_OR_PORTS')
    need(h.get('Tmpfs')=={'/tmp':''} and h['LogConfig']['Type']=='none','PRIVATE_TMPFS_NO_DAEMON_LOG')
    owned_directory(HERE/('attempt-'+run)/'fixture/.runtime'/role)
    expected={(p['configs'][role]['path'],'/src/strfry.conf' if role=='strfry' else '/src/config.toml',False),
        (str(HERE/('attempt-'+run)/'fixture/.runtime'/role),'/data',True)}
    need(len(d['Mounts'])==2 and {(m['Source'],m['Destination'],m['RW']) for m in d['Mounts']}==expected
         and all(m['Type']=='bind' and m['Propagation'] in ('private','rprivate') for m in d['Mounts']),'EXACT_RELAY_MOUNTS')
    nets=d['NetworkSettings']['Networks'];need(set(nets)=={network_name},'ONE_OWNED_NETWORK')
    endpoint=nets[network_name];state=d['State']
    need(type(state['Running']) is bool and state['OOMKilled'] is False,'KNOWN_RELAY_STATE')
    if state['Status']=='created' and state['Running'] is False and state['Pid']==0:
        need(endpoint['NetworkID'] in ('',network_id) and endpoint['IPAddress']==''
             and state['StartedAt']==state['FinishedAt']=='0001-01-01T00:00:00Z'
             and endpoint['EndpointID']=='','CREATED_NETWORK_BINDING')
    else:need(endpoint['NetworkID']==network_id,'ACTUAL_JOINED_NETWORK_ID')
    return d


def network_identity(d,nid,name,labels,allowed):
    need(d['Id']==full(nid) and d['Name']==name and d['Labels']==labels and d['Driver']=='bridge'
         and d['Internal'] is True and not d.get('Ingress') and not d.get('Attachable'),'OWNED_INTERNAL_NETWORK')
    need(set(d['Containers']).issubset(allowed),'NO_UNOWNED_NETWORK_MEMBER');return d


class Replay:
    def __init__(self,p,r,end,started):
        self.p,self.r,self.end=p,r,end;self.work_end=end-90;self.run=r['runId']
        self.name='nbdp-e02-completion-r2-'+self.run;self.out=HERE/('attempt-'+self.run)
        self.fixture=self.out/'fixture';self.runtime=self.fixture/'.runtime';self.final=None;self.intent=None;self.primary_pin=None;self.before=None
        self.ids={};self.nid=None;self.proxy=None;self.first=None;self.secondary=[];self.seq=0;self.records=[];self.setup_end=min(started+120,self.work_end)

    def fault(self,why):
        if self.first is None:self.first=why
        else:self.secondary.append(why)

    def write(self,name,value):
        raw=(json.dumps(value,indent=2)+'\n').encode();need(len(raw)<=16777216,'RECEIPT_BOUND')
        with (self.out/name).open('xb') as f:f.write(raw)

    @staticmethod
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE,(RAW_LIMIT,RAW_LIMIT));resource.setrlimit(resource.RLIMIT_CORE,(0,0))

    def cli(self,args,label,seconds=15,cleanup=False):
        need(0<seconds<=30,'CLI_BOUND');end=self.end if cleanup else min(self.work_end,self.setup_end or self.work_end)
        seconds=min(seconds,int(end-time.monotonic())-3);need(seconds>0,'CLI_LEASE_EXHAUSTED')
        self.seq+=1;stem='%03d-%s'%(self.seq,label)
        argv=[self.p['tools']['timeout']['path'],'--signal=TERM','--kill-after=2s',str(seconds)+'s',self.p['tools']['docker']['path'],*args]
        request=dict(argv=argv,maximumSeconds=seconds,cleanup=cleanup,startedUtcNs=time.time_ns());self.write(stem+'-request.json',request)
        with (self.out/(stem+'.stdout')).open('xb') as out,(self.out/(stem+'.stderr')).open('xb') as err:
            result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,cwd=self.out,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','DOCKER_CONFIG':str(self.out/'docker-config')},preexec_fn=self.limits,check=False)
        op,ep=self.out/(stem+'.stdout'),self.out/(stem+'.stderr');record=dict(request=request,exitCode=result.returncode,stdout=pin(op),stderr=pin(ep))
        self.records.append(record);self.write(stem+'-result.json',record)
        need(op.stat().st_size<RAW_LIMIT and ep.stat().st_size<RAW_LIMIT,'CAPTURE_LIMIT')
        return result.returncode,op.read_bytes(),ep.read_bytes()

    def actual(self,args,label,cleanup=False,seconds=15):
        code,out,err=self.cli(args,label,seconds,cleanup);need(code==0 and not err,'CLI_ZERO_EMPTY_STDERR_REQUIRED:'+label);return json.loads(out)

    def inspect(self,role,cleanup=False):
        value=self.actual(['container','inspect',full(self.ids[role])],'inspect-'+role,cleanup)
        need(type(value) is list and len(value)==1,'ONE_INSPECT')
        return identity(value[0],self.ids[role],role,self.p,self.run,self.nid,self.name)

    def mutate(self,role,args,cleanup=False,seconds=15):
        self.net(cleanup);self.inspect(role,cleanup);code,_,err=self.cli([*args,full(self.ids[role])],'mutate-'+role,seconds,cleanup)
        need(code==0 and not err,'OWNED_MUTATION_FAILED')

    def net(self,cleanup=False,empty=False):
        value=self.actual(['network','inspect',full(self.nid)],'network-inspect',cleanup)
        need(type(value) is list and len(value)==1,'ONE_NETWORK_INSPECT')
        d=network_identity(value[0],self.nid,self.name,dict(self.p['labels'],**{'nbdp.run':self.run}),set(self.ids.values()))
        if empty:need(not d['Containers'],'NETWORK_EMPTY_BEFORE_MUTATION')
        return d

    def admission(self):
        remaining(self.setup_end,0);p=self.p;fixed_plan(p)
        deferred={'inputInventory','wrapperSourceQa','wrapperSourceSecurity'}
        roots=[*p['tools'].values(),p['native'],p['e01'],p['e01Acceptance'],*p['configs'].values(),p['proxySource'],*p['sourceData'],*[v for k,v in p['current'].items() if k not in deferred]]
        inventory=load(checked(p['current']['inputInventory']))
        need(set(inventory)=={'schema','roots','files'} and inventory['schema']=='e02-selected-protected-input-inventory-v1','SELECTED_INVENTORY_SCHEMA')
        # The manifest itself cannot recursively contain its own descriptor.
        expected_roots=roots
        need(inventory['roots']==expected_roots,'EXACT_SELECTED_INPUT_ROOTS')
        files=descriptor_dag(expected_roots);need(inventory['files']==files,'FULL_EXPLICIT_INPUT_DAG')
        self.source_files=descriptor_dag([*files,*[p['current'][k] for k in deferred],self.r['modelAcceptance'],self.r['inputAcceptance']])
        self.before=scoped_snapshot(self.source_files);self.write('source-before.json',dict(inventory=p['current']['inputInventory'],rows=self.before))
        profile=load(checked(p['current']['completionProfile']))
        need(profile['rustBinary']==p['native'] and profile['e01']==p['e01'] and profile['producerSubject']==p['current']['producerSource'] and profile['consumerSubject']==p['current']['consumerSource'],'EXACT_CURRENT_COMPLETION_PROFILE')
        need(profile['producerControl35Prerequisite']==p['current']['producer35'] and profile['producerRebuilt3Prerequisite']==p['current']['producer3'],'EXACT_FRESH_PRODUCER_CONTROLS')
        need(profile['consumerControlAcceptance']==p['current']['consumerControlAcceptance'],'EXACT_CURRENT_CONSUMER_CONTROLS')
        need(p['current']['completionRunner'] in load(checked(p['current']['completionSource']))['sources'],'RUNNER_IN_CURRENT_COMPLETION_SOURCE')
        native_binding(load(checked(p['e01'])),p['native'])
        accepted=load(checked(p['e01Acceptance']));need(accepted['decision']=='ACCEPT_ACTUAL_E01_REPLAY_FOR_EXACT_REBUILT_NATIVE_CANDIDATE' and accepted['nativeSha256']==NATIVE_SHA and accepted['report']['sha256']==E01_SHA,'ACCEPTED_CURRENT_E01_JOIN')
        for rel,sha in load(checked(p['e01']))['source_sha256'].items():need(pin(EXP/rel)['sha256']==sha,'ALL19_CURRENT_E01_SOURCES')
        self.shared_before=shared_runtime_state(EXP/'.runtime')
        self.write('shared-runtime-before.json',self.shared_before)
        fresh_paths([self.fixture,render.RUNS/self.run])
        for port in (17777,18081):
            with socket.socket() as sock:sock.bind(('127.0.0.1',port))

    def setup(self):
        self.fixture.mkdir(mode=0o700);self.runtime.mkdir(mode=0o700)
        owned_directory(self.fixture);owned_directory(self.runtime)
        for name in ('home','tmp'):(self.fixture/name).mkdir(mode=0o700)
        for role in ('strfry','rs-relay'):(self.runtime/role).mkdir(mode=0o700)
        self.env={'PATH':'/usr/bin:/bin','HOME':str(self.fixture/'home'),'TMPDIR':str(self.fixture/'tmp'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC','NBDP_CHROME':'/usr/bin/false','NBDP_RUST_BIN':self.p['native']['path']}
        for role,image in self.p['images'].items():
            value=self.actual(['image','inspect',image],'image-'+role);need(len(value)==1 and value[0]['Id']==image,'EXACT_AVAILABLE_RELAY_IMAGE')
            code,out,err=self.cli(['container','inspect',self.name+'-'+role],'absent-'+role)
            need(exact_absence(code,out,err,self.name+'-'+role),'OCCUPIED_OR_UNKNOWN_CONTAINER_UNTOUCHED')
        code,out,err=self.cli(['network','inspect',self.name],'absent-network')
        need(exact_absence(code,out,err,self.name,True),'OCCUPIED_OR_UNKNOWN_NETWORK_UNTOUCHED')
        labels=dict(self.p['labels'],**{'nbdp.run':self.run});args=['network','create','--internal','--driver','bridge']
        for k,v in labels.items():args+=['--label',k+'='+v]
        try:code,out,err=self.cli([*args,self.name],'network-create')
        finally:
            raw=self.out/('%03d-network-create.stdout'%self.seq)
            if raw.is_file() and raw.stat().st_size<1024:
                value=raw.read_text().strip()
                if re.fullmatch('[0-9a-f]{64}',value):self.nid=value
        need(self.nid is not None and code==0 and not err,'NETWORK_CREATE_FAILED');self.net(empty=True)
        for role in ('strfry','rs-relay'):
            owned_directory(self.runtime/role)
            self.net();config=self.p['configs'][role]['path'];target='/src/strfry.conf' if role=='strfry' else '/src/config.toml';cidfile=self.out/(role+'.cid')
            args=['create','--pull','never','--cidfile',str(cidfile),'--name',self.name+'-'+role,'--network',self.nid,'--user',self.p['user'],
                '--cpus','2','--memory','1073741824','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp','--log-driver','none']
            for k,v in dict(labels,**{'nbdp.role':role}).items():args+=['--label',k+'='+v]
            args+=['--mount','type=bind,src='+config+',dst='+target+',readonly','--mount','type=bind,src='+str(self.runtime/role)+',dst=/data',
                self.p['images'][role],*(['relay'] if role=='strfry' else ['--db','/data'])]
            try:code,out,err=self.cli(args,'create-'+role,30)
            finally:
                if cidfile.is_file() and cidfile.stat().st_size<1024:self.ids[role]=full(cidfile.read_text().strip())
            need(role in self.ids and out.decode().strip()==self.ids[role] and code==0 and not err,'CREATE_IDENTITY_OR_RESULT_FAILED')
            self.mutate(role,['start'],seconds=30)
        ips={}
        for role in ('strfry','rs-relay'):
            d=self.inspect(role);need(d['State']['Running'] is True,'ACTUALLY_RUNNING_RELAY');ip=d['NetworkSettings']['Networks'][self.name]['IPAddress']
            need(re.fullmatch(r'172\.\d+\.\d+\.\d+',ip),'ORIGINAL_PROXY_INTERNAL_IP_DOMAIN');ips[role]=ip
        with (self.runtime/'relay-ips.json').open('x') as f:json.dump(ips,f)
        checked(self.p['proxySource']);argv=[self.p['tools']['node']['path'],self.p['proxySource']['path']];self.write('proxy-launch.json',dict(argv=argv,cwd=str(self.fixture),environment=self.env,ips=ips))
        self.proxy_out=(self.out/'proxy.stdout').open('xb');self.proxy_err=(self.out/'proxy.stderr').open('xb')
        self.proxy=subprocess.Popen(argv,cwd=self.fixture,env=self.env,stdin=subprocess.DEVNULL,stdout=self.proxy_out,stderr=self.proxy_err,preexec_fn=self.limits)
        deadline=min(time.monotonic()+15,self.setup_end,self.work_end)
        expected=[dict(name=k,loopback=port,internal_target=ips[k]+':'+str(target)) for k,port,target in [('strfry',17777,7777),('rs-relay',18081,8080)]]
        while True:
            need(self.proxy.poll() is None,'PROXY_EXITED_BEFORE_PRIMARY')
            raw=(self.out/'proxy.stdout').read_bytes();need(len(raw)<RAW_LIMIT and (self.out/'proxy.stderr').stat().st_size==0,'PROXY_RAW_REFUSAL')
            try:ready=[json.loads(line) for line in raw.splitlines()]
            except ValueError:ready=[]
            if sorted(ready,key=lambda x:x['name'])==sorted(expected,key=lambda x:x['name']):break
            remaining(deadline,0);time.sleep(0.05)
        remaining(self.setup_end,0)

    def primary(self):
        p=self.p;c=p['current'];remaining(self.work_end,243)
        remaining(self.setup_end or self.work_end,0)
        rows=[]
        for role,url in [('strfry','ws://127.0.0.1:17777'),('rs-relay','ws://127.0.0.1:18081')]:
            d=self.inspect(role);need(d['State']['Running'] is True,'CURRENT_RUNNING_RELAY')
            # Preserve the actual full inspection as the completion environment input.
            name='environment-'+role+'.json';self.write(name,[d])
            rows.append(dict(url=url,image=p['images'][role],config=p['configs'][role],inspection=pin(self.out/name)))
        self.net();need(self.proxy.poll() is None,'CURRENT_OWNED_PROXY_RUNNING')
        proxy=pin(self.out/'proxy-launch.json');environment=dict(schema='e02-completion-runtime-environment-v2',runId=self.run,operator=self.intent['operator'],observedAtUtcMillis=time.time_ns()//1000000,relays=rows,proxyReceipt=proxy)
        self.write('environment.json',environment)
        final=render.environment_slot_config(self.intent,pin(self.out/'environment.json'),environment,time.time_ns()//1000000)
        self.write('config.json',final);config=pin(self.out/'config.json');self.final=config
        template=load(checked(c['primaryReleaseTemplate']))
        release=render.primary_release(template,config,c['completionSource'],final['operator'],[c['completionSourceQa'],c['completionSourceSecurity']],time.time_ns()//1000000,self.r['notAfterUtcNs']//1000000)
        self.write('primary-release.json',release);release_pin=pin(self.out/'primary-release.json')
        argv=render.child_command(p['tools']['timeout'],p['tools']['node'],c['completionRunner'],config,release_pin,final['outputRoot']+'/primary')
        for d in [c['completionRunner'],config,release_pin]:checked(d)
        closure(scoped_snapshot(self.source_files),self.before)
        # Recheck after render and health, immediately before actual process launch.
        for role in ('strfry','rs-relay'):need(self.inspect(role)['State']['Running'] is True,'CURRENT_RUNNING_RELAY')
        self.net();need(self.proxy.poll() is None,'CURRENT_OWNED_PROXY_RUNNING')
        request=dict(schema='e02-wrapper-inner-process-request-v1',argv=argv,cwd=str(EXP),environment=self.env,startedUtcNs=time.time_ns(),jobSeconds=240,killGraceSeconds=3,config=config,release=release_pin)
        self.write('primary-request.json',request)
        with (self.out/'primary.stdout').open('xb') as out,(self.out/'primary.stderr').open('xb') as err:
            remaining(self.setup_end,0);self.setup_end=None
            remaining(self.work_end,243)
            result=subprocess.run(argv,cwd=EXP,env=self.env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,preexec_fn=self.limits,check=False)
        subject_path=Path(final['outputRoot'])/'primary/primary-subject.json'
        completion=dict(schema='e02-wrapper-inner-process-completion-v1',exitCode=result.returncode,stdout=pin(self.out/'primary.stdout'),stderr=pin(self.out/'primary.stderr'),finishedUtcNs=time.time_ns(),captureTransport='REGULAR_FILES',pipeEofEstablished=False,innerApiAttestation=False,primarySubject=pin(subject_path) if subject_path.is_file() else None)
        self.write('primary-completion.json',completion)
        render.regular_capture_shape(result.returncode,completion['stdout']['bytes'],completion['stderr']['bytes'])
        self.primary_pin=checked(completion['primarySubject']);subject=load(self.primary_pin)
        render.inner_receipt(request,completion,argv,str(EXP),config,release_pin,completion['primarySubject'])
        need(subject['schema']=='e02-completion-primary-subject-v2' and subject['config']==config and subject['release']==release_pin and subject['sourceSubject']==c['completionSource'] and subject['operator']==final['operator'] and subject['environment']==final['environment'],'PRIVATE_CURRENT_PRIMARY_SUBJECT')
        need(subject['argv']==argv[4:] and subject['unexpected'] is None and subject['sourceBefore']==subject['sourceAfter'],'NATURAL_CURRENT_INNER_PRIMARY')
        need(final['createdAtUtcMillis']<=subject['startedAtUtcMillis']<=subject['finishedAtUtcMillis']<=completion['finishedUtcNs']//1000000,'ACTUAL_CURRENT_PRIMARY_INTERVAL')
        root=subject_path.parent
        need(subject['rawReport']['path']==str(root/'raw-primary-report.json') and len(subject['saved'])==1 and subject['saved'][0]['path']==str(root/'E02-bidirectional-wires.json'),'SOLE_NEW_PRIVATE_REPORT_AND_WIRE')
        report=load(checked(subject['rawReport']));need(set(report)=={'experiment','status','tests','observations','skipped'} and report['experiment']=='E02' and report['status']=='PARTIAL' and len(report['tests'])==22 and all(t['ok'] is True for t in report['tests']) and [t['name'] for t in report['tests']]==p['expectedNames'] and report['skipped']==[SKIP],'ORIGINAL22_RAW_PARTIAL_LITERAL_MANDATORY_SKIP')
        wires=load(checked(subject['saved'][0]));need(type(wires) is list and len(wires)==4,'FOUR_ORIGINAL_WIRES')
        # Full primaryShape/wireFixtures semantics are rechecked by staged candidate adapter.
        printed=json.loads((self.out/'primary.stdout').read_bytes());need(printed==dict(subject=completion['primarySubject'],rawStatus='PARTIAL',unexpected=None),'EXACT_CURRENT_CHILD_STDOUT_JOIN')
        self.write('raw-result-pins.json',dict(subject=completion['primarySubject'],report=subject['rawReport'],wires=subject['saved'][0],ordinaryRows=0,canonicalE02Changed=False))

    def cleanup(self):
        cleanup_end=min(self.end,time.monotonic()+90);self.end=cleanup_end
        if self.proxy is not None:
            try:
                if self.proxy.poll() is None:self.proxy.terminate()
                try:self.proxy.wait(timeout=min(5,remaining(cleanup_end,5)))
                except subprocess.TimeoutExpired:self.proxy.kill();self.proxy.wait(timeout=min(3,remaining(cleanup_end,3)))
                self.proxy_out.close();self.proxy_err.close();self.write('proxy-completion.json',dict(returnCode=self.proxy.returncode,reaped=True,ownedPopenHandleOnly=True,stdout=pin(self.out/'proxy.stdout'),stderr=pin(self.out/'proxy.stderr')))
            except BaseException as e:self.fault('PROXY_CLEANUP:'+type(e).__name__+':'+str(e))
        for role in reversed(tuple(self.ids)):
            try:
                d=self.inspect(role,True)
                if d['State']['Running']:self.mutate(role,['stop','--time','5'],True,15)
                d=self.inspect(role,True)
                if d['State']['Running']:self.mutate(role,['kill'],True,15)
                need(self.inspect(role,True)['State']['Running'] is False,'STOPPED_BEFORE_REMOVE')
                self.mutate(role,['rm'],True)
                code,out,err=self.cli(['container','inspect',self.ids[role]],'absent-final-'+role,cleanup=True)
                need(exact_absence(code,out,err,self.ids[role]),'EXACT_CID_ABSENCE_REQUIRED')
                self.write('cleanup-'+role+'.json',dict(cid=self.ids[role],exactAbsence=True))
            except BaseException as e:self.fault('RELAY_CLEANUP:'+role+':'+type(e).__name__+':'+str(e))
        if self.nid is not None:
            try:
                self.net(True,empty=True);code,_,err=self.cli(['network','rm',self.nid],'network-remove',cleanup=True);need(code==0 and not err,'NETWORK_REMOVE_FAILED')
                code,out,err=self.cli(['network','inspect',self.nid],'network-absence',cleanup=True);need(exact_absence(code,out,err,self.nid,True),'EXACT_NETWORK_ABSENCE_REQUIRED')
                self.write('cleanup-network.json',dict(networkId=self.nid,exactAbsence=True))
            except BaseException as e:self.fault('NETWORK_CLEANUP:'+type(e).__name__+':'+str(e))

    def run_all(self):
        safe(self.out).mkdir(mode=0o700);(self.out/'docker-config').mkdir(mode=0o700)
        try:
            self.admission()
            template=load(checked(self.p['current']['configTemplate']))
            for key in ('ordinaryManifest','ordinaryOrigin','consumerControls'):need(template[key]==self.p['current'][key],'EXACT_CONFIG_CURRENT_OPERAND')
            self.intent=render.config_intent(template,self.run,self.p['current']['completionSource'],time.time_ns()//1000000)
            self.write('config-intent.json',self.intent) # Actual T0 is persisted before environment observations.
            self.setup();self.primary()
        except BaseException as e:self.fault(type(e).__name__+':'+str(e))
        finally:
            self.cleanup()
            try:
                inventory=self.p['current']['inputInventory'];actual=scoped_snapshot(self.source_files);closure(actual,self.before)
                closure(shared_runtime_state(EXP/'.runtime'),self.shared_before)
                self.write('source-after.json',dict(inventory=inventory,rows=actual,selectedProtectedInputsUnchanged=True,sharedRuntimeUnchanged=True,native=pin(self.p['native']['path']),e01=pin(self.p['e01']['path'])))
            except BaseException as e:self.fault('SOURCE_AFTER:'+type(e).__name__+':'+str(e))
            self.write('result.json',dict(state='RAW_PRIMARY22_PARTIAL_PENDING_INDEPENDENT_DATA_REVIEW' if self.first is None else 'FAILED_OR_UNQUALIFIED_NO_RETRY',firstFault=self.first,secondary=self.secondary,cliReceipts=len(self.records),ordinaryRowsQualified=0,canonicalE02Changed=False,stockE04E06Unlocked=False,completion2DropIn=False,hostileAtomicClosureClaimed=False,hostSignals='Owned trusted proxy Popen handle only; GNU timeout controls original primary/CLI job groups.'))
        code=0 if self.first is None else 2
        print(json.dumps(dict(result=pin(self.out/'result.json'),exitCode=code)))
        return code


def owned_directory(p):
    p=safe(p);st=p.stat()
    need(stat.S_ISDIR(st.st_mode) and st.st_uid==os.getuid() and st.st_gid==os.getgid() and stat.S_IMODE(st.st_mode)==0o700,'OWNED_PRIVATE_DIRECTORY_UNCHANGED')
    return p


def source_participants(roots):
    participants={'/root','/root/completion_wrapper'}
    for d in descriptor_dag(roots):
        if Path(d['path']).suffix!='.json':continue
        stack=[load(d['path'])]
        while stack:
            obj=stack.pop()
            if type(obj) is dict:
                for key in ('authors','operators'):
                    if key in obj:
                        need(type(obj[key]) is list and all(type(a) is str for a in obj[key]),'EXPLICIT_SOURCE_PARTICIPANTS')
                        participants.update(obj[key])
                stack.extend(obj.values())
            elif type(obj) is list:stack.extend(obj)
    return participants


def shared_runtime_state(root):
    # Presence is allowed. Refuse symlinks/special files and preserve only this selected
    # protected directory, never snapshot unrelated workspace files.
    if not root.exists():return dict(present=False,rows=[])
    need(root.is_dir() and not root.is_symlink(),'SHARED_RUNTIME_DIRECTORY_ONLY')
    rows=[]
    for q in [root,*sorted(root.rglob('*'))]:
        st=q.lstat();need(not q.is_symlink() and (q.is_dir() or q.is_file()),'SHARED_RUNTIME_SPECIAL_UNTOUCHED')
        row=dict(path=str(q),mode=stat.S_IMODE(st.st_mode),uid=st.st_uid,gid=st.st_gid,type='directory' if q.is_dir() else 'file')
        if q.is_file():row['pin']=pin(q)
        rows.append(row)
    return dict(present=True,rows=rows)


def review(d,subject,role,forbidden):
    value=load(checked(d))
    need(set(value)==set('schema role actor subject decision findings rawSessionEvidence'.split()),'CLOSED_CURRENT_REVIEW')
    need(value['schema']=='e02-wrapper-independent-review-v1' and value['role']==role and value['subject']==subject and value['decision']=='ACCEPT_EXACT_SUBJECT' and value['findings']==[],'CURRENT_INDEPENDENT_REVIEW_ACCEPTANCE')
    need(type(value['actor']) is str and value['actor'].startswith('/root/') and value['actor'] not in forbidden,'INDEPENDENT_REVIEWER')
    checked(value['rawSessionEvidence']);return value['actor']


def main():
    os.umask(0o077);a=argparse.ArgumentParser();a.add_argument('--plan-sha',required=True);a.add_argument('--release',required=True);a.add_argument('--release-sha',required=True);args=a.parse_args()
    started=time.monotonic();pp=pin(HERE/'plan-draft.json');rp=pin(args.release);need(pp['sha256']==args.plan_sha and rp['sha256']==args.release_sha,'EXTERNAL_ROOT_PINS')
    p,r=load(pp['path']),load(rp['path']);need(p['schema']=='nbdp-completion-primary-wrapper-source-plan-v2' and p['runtimeReady'] is True,'SOURCE_ONLY_NULL_FINAL_BINDINGS_NOT_READY')
    need(str(Path(sys.executable).resolve())==p['tools']['python']['path'] and sys.flags.isolated and sys.dont_write_bytecode,'PINNED_ISOLATED_INTERPRETER')
    need(set(r)==set('schema actor executionAuthorized scope runId plan sourceSubject sourceQa sourceSecurity modelAcceptance inputAcceptance issuedAtUtcNs notAfterUtcNs renderAuthority'.split()),'CLOSED_ROOT_RELEASE')
    need(r['schema']=='nbdp-completion-primary-wrapper-root-release-v2' and r['actor']=='/root' and r['executionAuthorized'] is True and r['scope']=='ONE_CURRENT_COMPLETION_PRIMARY_ONLY' and r['plan']==pp and re.fullmatch('[0-9a-f]{32}',r['runId']) and r['renderAuthority']==render.RENDER_AUTHORITY,'ONE_ROOT_AUTHORIZED_CLOSED_RENDER_JOB')
    fixed_plan(p);end=lease_end(r['issuedAtUtcNs'],r['notAfterUtcNs'],time.time_ns(),started,time.monotonic())
    need(r['sourceSubject']==p['current']['wrapperSource'],'EXACT_WRAPPER_SOURCE_SUBJECT')
    sources=load(checked(r['sourceSubject']))['sources'];need(pin(__file__) in sources and pin(HERE/'render_data.py') in sources,'RUNNING_REVIEWED_SOURCE')
    for d in sources:checked(d)
    stable=[p['current'][k] for k in ('wrapperSource','completionSource','producerSource','consumerSource','producer35','producer3','consumerControls')]
    forbidden=set(p['authors']+p['operators'])|source_participants(stable)
    actors=[review(r['sourceQa'],r['sourceSubject'],'qa',forbidden),review(r['sourceSecurity'],r['sourceSubject'],'security',forbidden)]
    need(len(set(actors))==2,'DISTINCT_INDEPENDENT_SOURCE_REVIEWERS')
    completion_actors=[review(p['current']['completionSourceQa'],p['current']['completionSource'],'qa',forbidden),review(p['current']['completionSourceSecurity'],p['current']['completionSource'],'security',forbidden)]
    need(len(set(completion_actors))==2,'DISTINCT_INDEPENDENT_COMPLETION_SOURCE_REVIEWERS')
    for k in ('sourceQa','sourceSecurity'):need(r[k]==p['current'][{'sourceQa':'wrapperSourceQa','sourceSecurity':'wrapperSourceSecurity'}[k]],'CURRENT_SOURCE_REVIEW_JOIN');checked(r[k])
    for k in ('modelAcceptance','inputAcceptance'):
        accepted=load(checked(r[k]));need(set(accepted)=={'schema','decision','sourceSubject','subject','reviews'} and accepted['schema']=='e02-wrapper-reviewed-acceptance-v1' and accepted['decision']=='ACCEPT_EXACT_SUBJECT' and accepted['sourceSubject']==r['sourceSubject'],'EXACT_CURRENT_MODEL_CONCRETE_ACCEPTANCE')
        subject=load(checked(accepted['subject']))
        if k=='inputAcceptance':need(subject['schema']=='e02-wrapper-concrete-input-v1' and subject['plan']==pp and subject['sourceSubject']==r['sourceSubject'] and subject['inventory']==p['current']['inputInventory'],'EXACT_CURRENT_CONCRETE_PLAN_JOIN')
        else:need(subject['schema']=='e02-wrapper-pure-model-result-v1' and subject['sourceSubject']==r['sourceSubject'] and subject['modelsExecuted']==19 and subject['exitCode']==0,'ACTUAL19_CURRENT_MODELS_ONLY')
        need(type(accepted['reviews']) is list and len(accepted['reviews'])==2,'TWO_CURRENT_ACCEPTANCE_REVIEWS')
        reviewers=[review(d,accepted['subject'],role,forbidden) for d,role in zip(accepted['reviews'],('qa','security'))]
        need(len(set(reviewers))==2,'DISTINCT_CURRENT_ACCEPTANCE_REVIEWERS')
    return Replay(p,r,end,started).run_all()


if __name__=='__main__':raise SystemExit(main())
