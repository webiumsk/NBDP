"""SOURCE-only fixed isolated SDK package-install controller.

No Docker, acquired-tool execution, consent or test runs belong to preparation.
One externally pinned root release is required after independent SOURCE/model/
bootstrap/probe DATA acceptance. No production SDK or NBDP runtime qualification.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import time

WORK=Path('/Data/nbdp-e02-tooling-20261027/controller-r5')
PREP=Path('/tmp/nbdp-e02-sdkmanager-install-20261027-preparation/installation-source-r5')
JDK=Path('/tmp/nbdp-amethyst-rebuild-20261026/tools/jdk')
BOOTSTRAP=Path('/tmp/nbdp-e02-sdkmanager-install-20261027-preparation/bootstrap/cmdline-tools/22.0')
INPUTS=Path('/tmp/nbdp-e02-sdk-install-controller-20261027/input-bundle-r1')
WRITABLE=WORK/'writable-r1'
DOCKER='/usr/bin/docker';TIMEOUT='/usr/bin/timeout'
IMAGE='sha256:32bb6c4c58ee5fe85f1e7229fb15008accb137990093941d2f8e768efd91cf8c'
NAME='nbdp-sdk-install-20261027'
NETWORK='nbdp-amethyst-build-20261026'
NETWORK_ID='acf4c0e2d847dedb7841a18c0713ba9b58ad680d686c2d43d95612f54ff6ff9b'
NETWORK_LABELS={'nbdp.owner':'e02-amethyst-rebuild-20261026','nbdp.scope':'isolated-build-bootstrap'}
LABELS={'nbdp.owner':'e02-sdk-install-20261027','nbdp.scope':'exact-three-package-install','nbdp.role':'sdkmanager-scoped-install'}
RAW_LIMIT=4194304
JOB_FILE_LIMIT=2147483648
TMPFS={'/tmp':'rw,nosuid,nodev,size=134217728'}
PACKAGES=['platforms;android-37.0','build-tools;36.0.0','ndk;30.0.16248370']
LICENSE_SHA='1f8729233617b193fd619213792ae16a41b95d2bbbf525dfe66998252ba68b16'
CREATED_ENDPOINT_SCHEMA='SINGLE_FIXED_NAME_KEY_EMPTY_NETWORK_AND_ENDPOINT_IDS'
ZERO_DOCKER_TIME='0001-01-01T00:00:00Z'

def need(value,message):
    if not value:raise ValueError(message)


def full_cid(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value),'EXACT_FULL_CID_REQUIRED')
    return value


def safe(path):
    path=Path(path)
    need(path.is_absolute() and '..' not in path.parts,'ABSOLUTE_PATH_REQUIRED')
    for parent in (path,*path.parents):need(not parent.is_symlink(),'SYMLINK_COMPONENT_REFUSED')
    return path


def pin(path,maximum=2147483648):
    path=safe(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno());need(stat.S_ISREG(before.st_mode) and before.st_size<=maximum,'REGULAR_BOUNDED_INPUT_REQUIRED')
        count=0;digest=hashlib.sha256()
        while block:=stream.read(1048576):count+=len(block);need(count<=maximum,'INPUT_SIZE_BOUND');digest.update(block)
        after=os.fstat(stream.fileno())
    key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    need(key(before)==key(after) and count==before.st_size,'INPUT_DRIFT')
    return dict(path=str(path),bytes=count,sha256=digest.hexdigest())


def checked(descriptor,maximum=67108864):
    need(type(descriptor) is dict and set(descriptor)=={'path','bytes','sha256'},'CLOSED_PIN')
    need(pin(descriptor['path'],maximum)==descriptor,'INPUT_PIN_MISMATCH')
    return Path(descriptor['path'])


def doc(descriptor,maximum=67108864):
    return json.loads(checked(descriptor,maximum).read_bytes())


def exact_absence(code,stdout,stderr,identifier):
    """False/uncertain replies never become absence. No substring matching."""
    return type(code) is int and code==1 and stdout.strip() in (b'',b'[]') and stderr.rstrip(b'\r\n') in (
        ('Error response from daemon: No such container: '+identifier).encode(),
        ('Error: No such object: '+identifier).encode())


def classify(code,out_size,err_size):
    if out_size>=RAW_LIMIT or err_size>=RAW_LIMIT:return 'CAPTURE_LIMIT_REACHED_REFUSED'
    if code==0:return 'NATURAL_ZERO'
    if code==124:return 'GNU_TIMEOUT_EXPIRED'
    if code<0:return 'CLI_SIGNAL_'+str(-code)
    return 'NONZERO_'+str(code)


def network_binding(value,network_id):
    """Full config ID always; endpoint evidence is explicitly lifecycle-staged."""
    full_cid(network_id)
    need(value['HostConfig']['NetworkMode']==network_id,'EXACT_RELEASED_FULL_NETWORK_ID')
    networks=value['NetworkSettings']['Networks']
    need(type(networks) is dict and len(networks)==1,'EXACT_SINGLE_NETWORK_ENDPOINT')
    name,endpoint=next(iter(networks.items()))
    need(name==NETWORK and type(endpoint) is dict,'NO_FOREIGN_ENDPOINT_NAME_OR_ID')
    need('NetworkID' in endpoint and type(endpoint['NetworkID']) is str,'ENDPOINT_NETWORK_ID_FIELD_REQUIRED')
    actual=endpoint['NetworkID']
    if actual==network_id:return 'ENDPOINT_FULL_NETWORK_ID_OBSERVED'
    need(actual=='','FOREIGN_OR_TRUNCATED_ENDPOINT_NETWORK_ID')
    state=value['State']
    need(state['Status']=='created' and state['Running'] is False,'MISSING_RUNTIME_ENDPOINT_NETWORK_ID_UNKNOWN')
    need(CREATED_ENDPOINT_SCHEMA=='SINGLE_FIXED_NAME_KEY_EMPTY_NETWORK_AND_ENDPOINT_IDS' and
         state['Pid']==0 and state['StartedAt']==state['FinishedAt']==ZERO_DOCKER_TIME,
         'EXACT_EVIDENCED_NEVER_STARTED_CREATED_STATE_REQUIRED')
    for field in ('EndpointID','IPAddress','Gateway','GlobalIPv6Address','IPv6Gateway','MacAddress'):
        need(field in endpoint and endpoint[field]=='','EXACT_EVIDENCED_EMPTY_CREATED_ENDPOINT_FIELDS')
    for field in ('IPPrefixLen','GlobalIPv6PrefixLen'):
        need(field in endpoint and type(endpoint[field]) is int and endpoint[field]==0,'EXACT_EVIDENCED_EMPTY_CREATED_PREFIX_FIELDS')
    return 'CREATED_FULL_CONFIG_ID_ONLY_NO_RUNTIME_ENDPOINT_CLAIM'


def successful_job_state(state,network_stage):
    """Docker created.ExitCode0 is initialized metadata, never build execution."""
    need(state['Status']=='exited' and state['Running'] is False and
         type(state['ExitCode']) is int and state['ExitCode']==0 and state['OOMKilled'] is False and
         state.get('Error')=='' and network_stage=='ENDPOINT_FULL_NETWORK_ID_OBSERVED','ACTUAL_JOB_STATE_OR_NETWORK_JOIN_FAILED')
    times=[]
    for field in ('StartedAt','FinishedAt'):
        value=state[field]
        need(type(value) is str,'REAL_NONZERO_STARTED_FINISHED_TIMES_REQUIRED')
        matched=re.fullmatch(r'([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{1,9}))?Z',value)
        need(matched is not None,'REAL_NONZERO_STARTED_FINISHED_TIMES_REQUIRED')
        base,fraction=matched.groups();fraction=(fraction or '').ljust(9,'0')
        datetime.fromisoformat(base+'+00:00')  # Validate calendar/time fields.
        need(base!='0001-01-01T00:00:00' or int(fraction)>0,'REAL_NONZERO_STARTED_FINISHED_TIMES_REQUIRED')
        times.append((base,fraction))
    need(times[0]<=times[1],'REAL_JOB_STATE_TIME_ORDER')


def tool_inventory(extraction):
    """Rejoin accepted acquisition's complete byte/mode/link inventory."""
    root=safe(extraction['destination']);need(root.is_dir(),'ACQUIRED_TOOL_ROOT_REQUIRED')
    expected={row['path']:row for row in extraction['inventory']}
    need(len(expected)==len(extraction['inventory']) and len(expected)<=200000,'TOOL_INVENTORY_MEMBERSHIP')
    actual={}
    for path in root.rglob('*'):
        relative=str(path.relative_to(root));need(len(actual)<200000,'TOOL_TREE_BOUND')
        st=path.lstat()
        if stat.S_ISLNK(st.st_mode):
            need(path.resolve(strict=True).is_relative_to(root),'TOOL_LINK_ESCAPE')
            row=dict(path=relative,kind='symlink',target=os.readlink(path))
        elif stat.S_ISDIR(st.st_mode):row=dict(path=relative,kind='dir',mode=oct(stat.S_IMODE(st.st_mode)))
        else:
            need(stat.S_ISREG(st.st_mode),'TOOL_SPECIAL_FILE')
            info=pin(path,536870912)
            row=dict(path=relative,kind='file',bytes=info['bytes'],sha256=info['sha256'],mode=oct(stat.S_IMODE(st.st_mode)))
        actual[relative]=row
    need(actual==expected,'COMPLETE_CURRENT_ACQUIRED_TOOL_TREE_MISMATCH')


def fixed_mounts():
    return [(str(JDK),'/jdk',False),
        (str(BOOTSTRAP),'/bootstrap/cmdline-tools/22.0',False),
        (str(PREP),'/prep',False),(str(INPUTS),'/inputs',False),
        (str(WRITABLE/'sdk'),'/sdk',True),(str(WRITABLE/'user'),'/user',True),
        (str(WRITABLE/'output'),'/output',True)]


def environment():
    return {'PATH':'/jdk/bin:/usr/bin:/bin','JAVA_HOME':'/jdk',
        'JAVA_TOOL_OPTIONS':'-Xmx768m -XX:MaxMetaspaceSize=256m -XX:ActiveProcessorCount=2 -Duser.home=/user/home -Djava.io.tmpdir=/user/tmp',
        'HOME':'/user/home','ANDROID_USER_HOME':'/user/android',
        'XDG_CACHE_HOME':'/user/cache','XDG_CONFIG_HOME':'/user/config',
        'TMPDIR':'/user/tmp','ANDROID_HOME':'/sdk','ANDROID_SDK_ROOT':'/sdk',
        'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC'}


def container_command(plan):
    descriptor=plan['installPlan']
    need(descriptor['path']==str(PREP/'install-plan.json') and
         re.fullmatch('[0-9a-f]{64}',descriptor['sha256']),'EXACT_INNER_PLAN_PATH_AND_HASH')
    return ['-i',*[key+'='+value for key,value in environment().items()],
        TIMEOUT,'--signal=TERM','--kill-after=5s','1050s',
        '/usr/bin/python3','-I','-B','/prep/install.py',
        '--plan','/prep/install-plan.json','--plan-sha',descriptor['sha256']]


def create_argv(plan,run_id,cidfile,network_id):
    need(type(run_id) is str and re.fullmatch('[0-9a-f]{32}',run_id),'EXACT_RUNID')
    need(full_cid(network_id)==NETWORK_ID,'FIXED_NETWORK_ID')
    argv=[DOCKER,'create','--pull','never','--cidfile',str(cidfile),'--name',NAME,
        '--workdir','/user','--user','1000:1000','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--read-only','--init',
        '--cpus','2','--memory','2147483648','--memory-swap','2147483648',
        '--pids-limit','256','--network',network_id,'--tmpfs',
        '/tmp:rw,nosuid,nodev,size=134217728','--log-driver','none',
        '--ulimit','fsize='+str(JOB_FILE_LIMIT)+':'+str(JOB_FILE_LIMIT)]
    for key,value in dict(LABELS,**{'nbdp.installRun':run_id}).items():argv+=['--label',key+'='+value]
    for host,container,writable in fixed_mounts():
        argv+=['--mount','type=bind,src='+host+',dst='+container+('' if writable else ',readonly')]
    return [*argv,'--entrypoint','/usr/bin/env',IMAGE,*container_command(plan)]


def network_identity(value,network_id,allowed):
    need(full_cid(network_id)==NETWORK_ID and type(value) is list and len(value)==1,'ONE_FIXED_NETWORK')
    d=value[0]
    need(d['Id']==network_id and d['Name']==NETWORK and d['Driver']=='bridge' and
         d['Scope']=='local' and d['Internal'] is False and d['Attachable'] is False and
         d['Ingress'] is False and d.get('ConfigOnly') is False,'FIXED_INTERNET_BRIDGE_CONFIGURATION')
    need(d['Labels']==NETWORK_LABELS and type(d['Containers']) is dict,'EXACT_NETWORK_LABELS_AND_MEMBERS')
    for cid in d['Containers']:full_cid(cid)
    need(set(d['Containers']).issubset(allowed),'NO_UNOWNED_NETWORK_MEMBER')
    return d


def owned_identity(value,cid,run_id,plan,network_id):
    full_cid(cid);full_cid(network_id)
    need(type(value) is list and len(value)==1 and type(value[0]) is dict,'ONE_CONTAINER_INSPECT_OBJECT')
    d=value[0];need(d['Id']==cid and d['Image']==IMAGE and d['Name']=='/'+NAME,'EXACT_CID_IMAGE_NAME')
    config=d['Config'];host=d['HostConfig']
    need(config.get('WorkingDir')=='/user' and config['User']=='1000:1000' and config['Image']==IMAGE and
         config['Entrypoint']==['/usr/bin/env'] and config['Cmd']==container_command(plan),'EXACT_NONROOT_CLOSED_COMMAND')
    need(config['Labels']==dict(LABELS,**{'nbdp.installRun':run_id}),'EXACT_INSTALL_CREATION_LABELS')
    need(config['Env']==['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'] and
         config['OpenStdin'] is False and config['Tty'] is False,'EXACT_IMAGE_ENV_NO_HOST_STDIN_TTY')
    need(host['Privileged'] is False and host['ReadonlyRootfs'] is True and
         host['NetworkMode']==network_id,'EXACT_RELEASED_NETWORK_READONLY_ROOT')
    need(not host.get('CapAdd') and host['CapDrop']==['ALL'] and
         any(x in ('no-new-privileges','no-new-privileges:true') for x in host['SecurityOpt']),'FIXED_CAPABILITIES')
    need(host['Memory']==host['MemorySwap']==2147483648 and host['NanoCpus']==2000000000 and
         host['PidsLimit']==256,'EXACT_INSTALL_RESOURCE_CAPS')
    need(host.get('Init') is True and not host.get('PortBindings') and not host.get('PublishAllPorts') and
         not host.get('Devices') and not host.get('DeviceRequests') and not host.get('VolumesFrom') and
         not host.get('PidMode') and not host.get('UTSMode') and host.get('IpcMode') in ('private','shareable'),
         'INIT_NO_HOST_PRIVILEGES_PORTS_DEVICES')
    need(host.get('RestartPolicy')=={'Name':'no','MaximumRetryCount':0} and host.get('AutoRemove') is False and
         host.get('CgroupnsMode')=='private' and
         host.get('ContainerIDFile')==str(WORK/('attempt-'+run_id)/'cidfile'),'NO_RESTART_AUTO_REMOVE_OR_FOREIGN_CIDFILE')
    need(host['LogConfig']['Type']=='none' and host.get('Tmpfs')==TMPFS and
         host.get('Ulimits')==[{'Name':'fsize','Soft':JOB_FILE_LIMIT,'Hard':JOB_FILE_LIMIT}],
         'FIXED_LOG_TMPFS_AND_TWO_GIB_JOB_FILE_BOUND')
    actual=[]
    for mount in d['Mounts']:
        need(mount['Type']=='bind' and mount['Propagation'] in ('private','rprivate'),'PRIVATE_BINDS_ONLY')
        actual.append((mount['Source'],mount['Destination'],mount['RW']))
    need(sorted(actual)==sorted(fixed_mounts()),'EXACT_RO_INPUTS_AND_NEW_RW_OUTPUT_MOUNTS')
    need(type(d['State']['Running']) is bool and type(d['State']['OOMKilled']) is bool and
         type(d['State']['ExitCode']) is int,'TYPED_ACTUAL_JOB_STATE')
    network_binding(d,network_id)
    return d


def inner_success(value):
    need(value['state']=='SDKMANAGER_FINISHED_PENDING_INDEPENDENT_INSTALLED_DATA_REVIEW' and
         value['firstFault'] is None and value['secondary']==[] and value['packages']==PACKAGES,
         'EXACT_INNER_INSTALL_RESULT_SCOPE')
    need(value['rawEOF']=={'stdout':True,'stderr':True} and value['cleanup']['leaderReaped'] is True and
         value['cleanup']['returnCode']==0 and value['cleanup']['sampledLiveGroupAfter']==[],
         'INNER_NATURAL_REAPED_CAPTURE')
    c=value['consent']
    need(c['affirmativeAttempted'] is True and c['stdinWriteInvoked'] is True and
         c['writeReturnedBytes']==2 and c['flushAndSentRecorded'] is True and c['consumption']=='UNKNOWN',
         'HONEST_SINGLE_ANSWER_WRITE_OBSERVATION')


def lease_end(issued,expires,now,started,monotonic_now):
    need(type(issued) is int and type(expires) is int and type(now) is int and
         0<=issued<=now<expires and 0<expires-issued<=1200*10**9,'FINITE_1200_SECOND_ROOT_LEASE')
    return min(started+1200,monotonic_now+(expires-now)/10**9)


def exact_bundle(extraction):
    need(extraction['destination']==str(INPUTS),'FIXED_READONLY_INPUT_BUNDLE')
    need(all(r['kind'] in ('file','dir') for r in extraction['inventory']),'INPUT_BUNDLE_NO_LINKS')
    tool_inventory(extraction)


def inner_source_membership(subject):
    paths=[Path(d['path']) for d in subject['sources']]
    need(len(paths)<=256 and all(p.parent==PREP for p in paths) and
         len({p.name for p in paths})==len(paths),'FLAT_EXACT_INNER_SOURCE_MEMBERSHIP')
    expected={p.name for p in paths}|{'subject.json'}
    actual=list(PREP.iterdir())
    need({p.name for p in actual}==expected and all(p.is_file() and not p.is_symlink() for p in actual),
         'NO_EXTRA_INNER_SOURCE_LOADER_OR_DIRECTORY')




class Supervisor:
    def __init__(self,release,plan,end):
        self.release,self.plan=release,plan;self.run_id=release['runId']
        self.root=WORK/('attempt-'+self.run_id);self.cid=None;self.first_fault=None;self.secondary=[]
        self.sequence=0;self.journals=[];self.cleanup_state='NOT_ATTEMPTED';self.job_state=None
        self.create_attempted=False;self.start_attempted=False;self.network_binding_stage='UNKNOWN'
        self.total_end=end;self.work_end=end-90

    def fault(self,message):
        if self.first_fault is None:self.first_fault=message
        else:self.secondary.append(message)


    def write(self,name,value):
        raw=(json.dumps(value,indent=2)+'\n').encode();need(len(raw)<=4194304,'RECEIPT_SIZE_BOUND')
        fd=os.open(self.root/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:
            need(stream.write(raw)==len(raw),'SHORT_RECEIPT_WRITE');stream.flush();os.fsync(stream.fileno())


    def cli(self,argv,label,seconds=30,cleanup=False,attached=False):
        end=self.total_end if cleanup else self.work_end
        remaining=end-time.monotonic();need(remaining>6,'FINITE_SUPERVISOR_BUDGET')
        seconds=min(seconds,int(remaining)-5);need(seconds>0,'FINITE_CLI_BUDGET')
        self.sequence+=1;stem='%03d-%s'%(self.sequence,label)
        out=self.root/(stem+'.stdout');err=self.root/(stem+'.stderr')
        wrapped=[TIMEOUT,'--signal=TERM','--kill-after=5s',str(seconds)+'s',*argv]
        request=dict(schema='nbdp-amethyst-actual-cli-request-v1',argv=argv,wrappedArgv=wrapped,
            startedUtcNs=time.time_ns(),maximumSeconds=seconds,capturePerFileLimitBytes=RAW_LIMIT,
            limitMeaning='RLIMIT_FSIZE on CLI/attach capture files only; inner install job file limit is2GiB.')
        self.write(stem+'-request.json',request)
        code=None;error=None;started=time.monotonic()
        def child_limits():
            resource.setrlimit(resource.RLIMIT_FSIZE,(RAW_LIMIT,RAW_LIMIT))
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        try:
            ofd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(ofd,'wb') as stdout:
                efd=os.open(err,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                with os.fdopen(efd,'wb') as stderr:
                    result=subprocess.run(wrapped,input=b'',stdout=stdout,stderr=stderr,cwd=self.root,
                        env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','DOCKER_CONFIG':str(self.root/'docker-config')},
                        preexec_fn=child_limits,check=False)
                    code=result.returncode
        except BaseException as exc:error=type(exc).__name__+':'+str(exc)[:2048]
        sizes=[p.stat().st_size if p.exists() else 0 for p in (out,err)]
        record=dict(request=request,exitCode=code,error=error,elapsedWallSeconds=time.monotonic()-started,
            classification=classify(code,*sizes) if code is not None else 'CLI_LAUNCH_OR_CAPTURE_ERROR',
            stdout=pin(out,RAW_LIMIT) if out.exists() else None,stderr=pin(err,RAW_LIMIT) if err.exists() else None,
            attachedInstall=attached,resourceClaim='Configured limits; no measured CPU/RSS/aggregate disk peak or hostile process closure.')
        self.journals.append(record)
        try:self.write(stem+'-result.json',record)
        except BaseException as exc:self.fault('CLI_RECEIPT_RETENTION:'+type(exc).__name__+':'+str(exc)[:1024])
        need(error is None,'CLI_CAPTURE_OR_LAUNCH_FAILURE:'+str(error))
        return record


    @staticmethod
    def streams(record,maximum=4194304):
        for key in ('stdout','stderr'):need(record[key] is not None and record[key]['bytes']<=maximum,'BOUNDED_METADATA_CAPTURE')
        return Path(record['stdout']['path']).read_bytes(),Path(record['stderr']['path']).read_bytes()


    def net(self,cleanup=False):
        record=self.cli([DOCKER,'network','inspect',NETWORK_ID],'network-inspect',cleanup=cleanup)
        out,err=self.streams(record)
        need(record['exitCode']==0 and err==b'' and record['classification']=='NATURAL_ZERO','NETWORK_INSPECT_UNKNOWN')
        return network_identity(json.loads(out),NETWORK_ID,{self.cid} if self.cid else set())

    def inspect(self,cleanup=False,allow_absence=False):
        need(self.cid is not None,'NO_KNOWN_CID_NO_MUTATION')
        self.net(cleanup)
        record=self.cli([DOCKER,'container','inspect',self.cid],'inspect-cid',cleanup=cleanup)
        out,err=self.streams(record)
        if allow_absence and exact_absence(record['exitCode'],out,err,self.cid):return None,record
        need(record['exitCode']==0 and err==b'' and record['classification']=='NATURAL_ZERO','CONTAINER_INSPECT_UNKNOWN')
        current=owned_identity(json.loads(out),self.cid,self.run_id,self.plan,NETWORK_ID)
        self.network_binding_stage=network_binding(current,NETWORK_ID)
        if self.start_attempted:self.job_state=current['State']
        return current,record

    def derive_cid(self,create_record=None):
        values=[];file=self.root/'cidfile'
        if file.exists():
            need(file.stat().st_size<=128,'CIDFILE_BOUND');values.append(full_cid(safe(file).read_text().strip()))
        if create_record is not None:
            out,_=self.streams(create_record)
            if out:values.append(full_cid(out.decode('ascii').strip()))
        need(values and len(set(values))==1,'UNAMBIGUOUS_CREATE_CID_REQUIRED')
        self.cid=values[0]


    def mutation(self,args,label,seconds=30):
        current,_=self.inspect(cleanup=True,allow_absence=True)
        if current is None:self.cleanup_state='EXACT_CID_ABSENCE_KNOWN';return None
        record=self.cli([DOCKER,*args,self.cid],label,seconds=seconds,cleanup=True)
        if record['exitCode']!=0 or record['classification']!='NATURAL_ZERO':self.fault(label+':'+record['classification'])
        return record


    def cleanup(self):
        if self.cid is None and not self.create_attempted:
            self.cleanup_state='NOT_CREATED_NO_MUTATION_ATTEMPTED';return
        if self.cid is None:
            try:self.derive_cid()
            except BaseException as exc:
                self.cleanup_state='UNKNOWN_NO_TRUSTED_CID';self.secondary.append(str(exc)[:1024]);return
        try:
            current,_=self.inspect(cleanup=True,allow_absence=True)
            if current is None:self.cleanup_state='EXACT_CID_ABSENCE_KNOWN';return
            if current['State']['Running']:
                self.mutation(['stop','--time','10'],'stop',seconds=20)
                current,_=self.inspect(cleanup=True,allow_absence=True)
                if current is None:self.cleanup_state='EXACT_CID_ABSENCE_KNOWN';return
                if current['State']['Running']:self.mutation(['kill','--signal','KILL'],'kill',seconds=15)
            current,_=self.inspect(cleanup=True,allow_absence=True)
            if current is None:self.cleanup_state='EXACT_CID_ABSENCE_KNOWN';return
            need(current['State']['Running'] is False,'OWNED_CONTAINER_STILL_RUNNING_NO_REMOVE')
            self.mutation(['rm'],'remove',seconds=20)
            current,_=self.inspect(cleanup=True,allow_absence=True)
            need(current is None,'REMOVAL_NOT_PROVEN')
            self.cleanup_state='EXACT_CID_ABSENCE_KNOWN'
        except BaseException as exc:
            self.cleanup_state='UNKNOWN';self.fault('CLEANUP:'+type(exc).__name__+':'+str(exc)[:2048])

    def prerequisites(self):
        r=self.release;p=self.plan
        need(r['executionAuthorized'] is True and r['scope']=='EXACT_THREE_PACKAGE_SDK_INSTALL_ONLY','ROOT_FIXED_INSTALL_RELEASE')
        need(type(self.run_id) is str and re.fullmatch('[0-9a-f]{32}',self.run_id),'FRESH_RUNID')
        need(p['state']=='SOURCE_ONLY_NOT_EXECUTION_AUTHORITY' and p['schema']=='nbdp-scoped-sdk-install-controller-plan-v1',
             'FROZEN_CONTROLLER_SOURCE_PLAN')
        need(r['networkId']==NETWORK_ID and r['networkLabels']==NETWORK_LABELS,'FIXED_RELEASED_NETWORK')
        need(p['packages']==PACKAGES and p['image']==IMAGE and p['mounts']==[
            {'host':a,'container':b,'writable':c} for a,b,c in fixed_mounts()],'FIXED_PACKAGE_IMAGE_MOUNT_PLAN')
        need(len(r['sourceReviews'])==2 and len(r['prerequisiteAcceptances'])>=4,'INDEPENDENT_SOURCE_AND_DATA_ACCEPTANCES')
        for d in r['sourceReviews']+r['prerequisiteAcceptances']:checked(d)
        decision=doc(r['sdkLicenseDecision'])
        need(decision['licenseConsentAuthorized'] is True and decision['userReplyVerbatim']=='true' and
             decision['exactLicenseText']['sha256']==LICENSE_SHA,'EXACT_USER_APPROVED_2019_LICENSE')
        checked(decision['exactLicenseText'])
        own=doc(r['controllerSubject'])
        need(r['controllerSubject']['path']==str(WORK/'subject.json'),'EXACT_CONTROLLER_SUBJECT')
        for d in own['sources']:checked(d)
        sources={d['path']:d for d in own['sources']}
        need(sources.get(str(Path(__file__).resolve()))==pin(Path(__file__).resolve()) and
             sources.get(str(WORK/'plan.json'))==pin(WORK/'plan.json'),'RUNNING_REVIEWED_CONTROLLER_PLAN')
        need(r['installSubject']==p['installSubject'] and r['installPlan']==p['installPlan'],'EXACT_FROZEN_INNER_BINDING')
        inner=doc(r['installSubject'])
        need(r['installSubject']['path']==str(PREP/'subject.json'),'EXACT_INNER_SUBJECT_PATH')
        inner_source_membership(inner)
        for d in inner['sources']:checked(d)
        inner_sources={d['path']:d for d in inner['sources']}
        for name in ('install.py','prompt.py','install-plan.json'):
            need(inner_sources.get(str(PREP/name))==pin(PREP/name),'FROZEN_INNER_SOURCE:'+name)
        need(r['installPlan']['path']==str(PREP/'install-plan.json'),'EXACT_INNER_PLAN_PATH')
        inner_plan=doc(r['installPlan'])
        need(inner_plan['environment']==environment() and inner_plan['argv']==[
            '/bootstrap/cmdline-tools/22.0/bin/sdkmanager','--sdk_root=/sdk','--channel=0','--install',*PACKAGES],
            'EXACT_SHARED_INNER_ENVIRONMENT_AND_PACKAGE_COMMAND')
        need(inner_plan['outerReadOnlyPrerequisites']==[
            {'root':'/jdk','receipt':r['jdkExtraction']},
            {'root':'/bootstrap/cmdline-tools/22.0','receipt':r['bootstrapExtraction']}]
            and inner_plan['hostInputBundleInventory']==r['inputBundleInventory'],
            'SHARED_READONLY_TOOL_AND_BUNDLE_BINDINGS')
        need(inner_plan['bounds']['innerSeconds']==1050 and inner_plan['bounds']['bodySeconds']==1020 and
             inner_plan['bounds']['outerWholeSeconds']==1200 and inner_plan['bounds']['outerCleanupSeconds']==90 and
             inner_plan['bounds']['jobPerFileUlimitBytes']==JOB_FILE_LIMIT,'COORDINATED_FINITE_INNER_OUTER_BOUNDS')
        for field,root in (('jdkExtraction',JDK),('bootstrapExtraction',BOOTSTRAP)):
            need(r[field]==p[field],'EXACT_ACCEPTED_TOOL_RECEIPT_BINDING')
            extraction=doc(r[field]);need(extraction['destination']==str(root),'EXACT_READONLY_TOOL_ROOT')
            tool_inventory(extraction)
        need(r['inputBundleInventory']==p['inputBundleInventory'],'EXACT_READONLY_BUNDLE_BINDING')
        exact_bundle(doc(r['inputBundleInventory']))
        need(os.statvfs(WORK).f_bavail*os.statvfs(WORK).f_frsize>=17179869184,'SIXTEEN_GIB_INSTALL_ADMISSION')
        for path in (WRITABLE,WRITABLE/'sdk',WRITABLE/'user',WRITABLE/'output'):
            safe(path);need(not path.exists(),'FRESH_OWNED_INSTALL_ROOT');path.mkdir(mode=0o700)
        need(self.work_end-time.monotonic()>1085,'FULL_ATTACH_AND_CLEANUP_RESERVE_BEFORE_CREATE')

    def source_after(self):
        for field in ('jdkExtraction','bootstrapExtraction'):
            tool_inventory(doc(self.release[field]))
        exact_bundle(doc(self.release['inputBundleInventory']))
        for field in ('controllerSubject','installSubject'):
            subject=doc(self.release[field])
            if field=='installSubject':inner_source_membership(subject)
            for d in subject['sources']:checked(d)
        self.write('readonly-inputs-after.json',{'allAcceptedReadonlyToolSourceBundleInputsUnchanged':True,
            'snapshotNotRaceFree':True})

    def retain_inner_evidence(self):
        evidence={}
        for name in ('installation-result.json','consent-attempted.json','consent-sent.json'):
            p=WRITABLE/'output'/name
            evidence[name]=pin(p,16777216) if p.exists() else None
        return evidence

    def run(self):
        need(not self.root.exists(),'FRESH_CONTROLLER_ATTEMPT_REQUIRED')
        safe(self.root).mkdir(mode=0o700);(self.root/'docker-config').mkdir(mode=0o700)
        try:
            self.prerequisites()
            existing=self.cli([DOCKER,'container','inspect',NAME],'precreate-name')
            out,err=self.streams(existing)
            need(exact_absence(existing['exitCode'],out,err,NAME),'EXISTING_OR_UNKNOWN_CONTAINER_UNTOUCHED')
            self.net()
            image=self.cli([DOCKER,'image','inspect',IMAGE],'image-present')
            out,err=self.streams(image);need(image['exitCode']==0 and err==b'','IMAGE_INSPECT_UNKNOWN')
            images=json.loads(out);need(len(images)==1 and images[0]['Id']==IMAGE,'EXACT_AVAILABLE_IMAGE')
            self.create_attempted=True
            created=self.cli(create_argv(self.plan,self.run_id,self.root/'cidfile',NETWORK_ID),'create')
            self.derive_cid(created)
            need(created['exitCode']==0 and created['classification']=='NATURAL_ZERO','CREATE_FAILED_STOP')
            current,_=self.inspect()
            need(current['State']['Status']=='created' and current['State']['Running'] is False and
                 current['State']['Error']=='','CREATED_ONLY_BEFORE_START')
            need(self.first_fault is None and self.work_end-time.monotonic()>1085,'FULL_ORIGINAL_ATTACH_RESERVE_BEFORE_START')
            self.start_attempted=True
            # Last source-controlled operations before start are fresh network and
            # full container checks; no host numeric-PID mutation is used.
            current,_=self.inspect()
            attached=self.cli([DOCKER,'start','--attach',self.cid],'start-attached',seconds=1080,attached=True)
            current,_=self.inspect();self.job_state=current['State']
            need(attached['classification']=='NATURAL_ZERO','ATTACHED_INSTALL_FAILED_OR_LOG_CEILING:'+attached['classification'])
            successful_job_state(current['State'],self.network_binding_stage)
            result=WRITABLE/'output/installation-result.json'
            value=json.loads(checked(pin(result,16777216),16777216).read_bytes());inner_success(value)
            self.output_pin=pin(result,16777216)
        except BaseException as exc:self.fault(type(exc).__name__+':'+str(exc)[:2048])
        finally:
            self.cleanup()
            try:self.source_after()
            except BaseException as exc:self.fault('READONLY_INPUTS_AFTER:'+type(exc).__name__+':'+str(exc)[:1024])
            try:evidence=self.retain_inner_evidence()
            except BaseException as exc:
                evidence=None;self.fault('INNER_EVIDENCE_RETENTION:'+type(exc).__name__+':'+str(exc)[:1024])
            result={'schema':'nbdp-scoped-sdk-install-controller-result-v1','runId':self.run_id,'cid':self.cid,
                'state':'INSTALL_EXIT0_PENDING_INDEPENDENT_DATA_REVIEW' if self.first_fault is None and
                    self.cleanup_state=='EXACT_CID_ABSENCE_KNOWN' else 'FAILED_OR_UNQUALIFIED_NO_RETRY',
                'firstFault':self.first_fault,'secondaryErrors':self.secondary,'cleanup':self.cleanup_state,
                'jobState':self.job_state,'networkBindingStage':self.network_binding_stage,
                'innerEvidence':evidence,'cliReceipts':len(self.journals),
                'consentStatus':'INSPECT_INNER_JOURNALS_UNKNOWN_UNTIL_INDEPENDENT_REVIEW',
                'configuredLimits':{'wholeSeconds':1200,'cleanupReserveSeconds':90,'jobSeconds':1050,
                    'attachSeconds':1080,'memoryBytes':2147483648,'cpus':2,'pids':256,
                    'jobPerFileBytes':JOB_FILE_LIMIT,'cliCapturePerFileBytes':RAW_LIMIT},
                'limitsMeaning':'Configured bounds only; no aggregate diskquota, measured peak, hostile atomic custody or egress guarantee.',
                'networkMutationPerformed':False,'sdkQualificationClaimed':False,'canonicalE02Changed':False,
                'noHostNumericPidSignalsByController':True,'hostileAtomicClosureClaimed':False}
            self.write('result.json',result)
        return result


def main():
    os.umask(0o077);started=time.monotonic()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',required=True);parser.add_argument('--release-sha',required=True)
    args=parser.parse_args()
    release_pin=pin(args.release,4194304)
    need(release_pin['sha256']==args.release_sha,'EXTERNALLY_PINNED_ROOT_RELEASE')
    release=doc(release_pin,4194304)
    need(set(release)=={'schema','actor','executionAuthorized','scope','runId','plan','controllerSubject',
        'installSubject','installPlan','sourceReviews','prerequisiteAcceptances','sdkLicenseDecision',
        'jdkExtraction','bootstrapExtraction','inputBundleInventory','networkId','networkLabels',
        'issuedAtUtcNs','notAfterUtcNs'},'CLOSED_ROOT_RELEASE')
    need(release['schema']=='nbdp-scoped-sdk-install-root-release-v1' and release['actor']=='/root',
         'EXACT_ROOT_RELEASE_SCHEMA_ACTOR')
    need(release['plan']==pin(WORK/'plan.json'),'EXTERNALLY_PINNED_CONTROLLER_PLAN')
    end=lease_end(release['issuedAtUtcNs'],release['notAfterUtcNs'],time.time_ns(),started,time.monotonic())
    supervisor=Supervisor(release,doc(release['plan']),end)
    result=supervisor.run();print(json.dumps(result),flush=True)
    return 0 if result['state']=='INSTALL_EXIT0_PENDING_INDEPENDENT_DATA_REVIEW' else 2


if __name__=='__main__':raise SystemExit(main())


