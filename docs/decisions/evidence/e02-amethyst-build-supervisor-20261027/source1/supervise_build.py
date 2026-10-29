"""Fixed Amethyst build-only supervisor. SOURCE preparation is not a release.

No Docker/tool/import execution belongs to preparation. Runtime needs a fresh
externally authenticated root release with exact source/acquisition input pins.
The controller uses Docker full-CID operations only, never host numeric-PID
signals. GNU timeout owns finite CLI waits; in-container timeout owns the job.
This is cooperative build lifecycle evidence, not hostile atomic containment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import time

WORK=Path('/tmp/nbdp-amethyst-build-supervisor-20261026')
ROOT=Path('/tmp/nbdp-amethyst-rebuild-20261026')
PREP=ROOT/'preparation'
DOCKER='/usr/bin/docker';TIMEOUT='/usr/bin/timeout'
IMAGE='sha256:32bb6c4c58ee5fe85f1e7229fb15008accb137990093941d2f8e768efd91cf8c'
NAME='nbdp-amethyst-build-20261026'
NETWORK='nbdp-amethyst-build-20261026'
RAW_LIMIT=67108864
JOB_FILE_LIMIT=536870912
COMMIT='e6f464a1179def75274512b3c5bab921de3bf3d8'
TREE='11a90777c85c71912594612f42d9807004834f67'


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


def create_argv(plan,run_id,cidfile):
    original=plan['proposedDockerCreateArgv']
    need(original[:4]==[DOCKER,'create','--name',NAME] and original[-2:]==['/usr/bin/python3','/prep/build_inside.py'],'EXACT_FIXED_BUILD_PLAN_ARGV')
    argv=original[:-2]+[TIMEOUT,'--signal=TERM','--kill-after=5s','1800s',*original[-2:]]
    # Outer-only restrictions: no daemon log accumulation; fixed512MiB per-job
    # file ceiling (including inner logs/APKs), and exact creation custody.
    argv[2:2]=['--cidfile',str(cidfile),'--label','nbdp.buildRun='+run_id,
        '--log-driver','none','--ulimit','fsize='+str(JOB_FILE_LIMIT)+':'+str(JOB_FILE_LIMIT)]
    return argv


def owned_identity(value,cid,run_id,plan):
    full_cid(cid)
    need(type(value) is list and len(value)==1 and type(value[0]) is dict,'ONE_CONTAINER_INSPECT_OBJECT')
    d=value[0];need(d['Id']==cid and d['Image']==IMAGE and d['Name']=='/'+NAME,'EXACT_CID_IMAGE_NAME')
    config=d['Config'];labels=config['Labels']
    need(all(labels.get(k)==v for k,v in {'nbdp.role':'amethyst-source-build','nbdp.owner':'nbdp-amethyst-rebuild-20261026','nbdp.buildRun':run_id}.items()),'EXACT_CREATION_LABELS')
    need(config['User']=='1000:1000' and config['Entrypoint']==['/usr/bin/env'],'NONROOT_FIXED_ENTRYPOINT')
    base=plan['proposedDockerCreateArgv'];command=base[base.index(IMAGE)+1:]
    need(config['Cmd']==command[:-2]+[TIMEOUT,'--signal=TERM','--kill-after=5s','1800s',*command[-2:]],'EXACT_INTERNAL_JOB_TIMEOUT_COMMAND')
    host=d['HostConfig']
    need(host['Privileged'] is False and host['ReadonlyRootfs'] is True and host['NetworkMode']==NETWORK,'EXACT_ROOT_NETWORK_BOUNDARY')
    need(not host.get('CapAdd') and host['CapDrop']==['ALL'] and
         any(v in ('no-new-privileges','no-new-privileges:true') for v in host['SecurityOpt']),'FIXED_CAPABILITIES')
    need(host['Memory']==host['MemorySwap']==6442450944 and host['NanoCpus']==4000000000 and host['PidsLimit']==512,'FIXED_RESOURCE_CAPS')
    need(host.get('Init') is True and not host.get('PortBindings') and not host.get('Devices'),'INIT_NO_HOST_PORT_OR_DEVICES')
    need(not host.get('PidMode') and not host.get('UTSMode') and host.get('IpcMode') in ('private','shareable'),'NO_HOST_PID_UTS_IPC')
    need(host['LogConfig']['Type']=='none','NO_DAEMON_LOG_ACCUMULATION')
    need(host.get('Ulimits')==[{'Name':'fsize','Soft':JOB_FILE_LIMIT,'Hard':JOB_FILE_LIMIT}],'FIXED_512MIB_JOB_FILE_CEILING')
    need(host.get('Tmpfs')=={'/tmp':'rw,nosuid,nodev,size=1073741824'},'FIXED_PRIVATE_TMPFS')
    expected=[]
    for at,arg in enumerate(base):
        if arg!='--mount':continue
        parts=base[at+1].split(',');items=dict(p.split('=',1) for p in parts if '=' in p)
        need(items.get('type')=='bind','FIXED_BIND_MOUNTS_ONLY')
        expected.append((items['src'],items['dst'],'readonly' not in parts))
    actual=[]
    for mount in d['Mounts']:
        need(mount['Type']=='bind' and mount['Propagation'] in ('rprivate','private'),'FIXED_PRIVATE_BIND_TYPE')
        actual.append((mount['Source'],mount['Destination'],mount['RW']))
    need(sorted(actual)==sorted(expected),'EXACT_ALLOWED_MOUNT_SET_NO_HOME_SOCKET_CREDENTIALS')
    need(type(d['State']) is dict,'ACTUAL_STATE_REQUIRED')
    need(type(d['State']['Running']) is bool and type(d['State']['OOMKilled']) is bool and
         type(d['State']['ExitCode']) is int,'ACTUAL_TYPED_JOB_STATE')
    return d


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


class Supervisor:
    def __init__(self,release,plan):
        self.release,self.plan=release,plan;self.run_id=release['runId']
        self.root=WORK/('attempt-'+self.run_id);self.cid=None;self.first_fault=None;self.secondary=[]
        self.sequence=0;self.journals=[];self.cleanup_state='NOT_ATTEMPTED';self.job_state=None
        self.create_attempted=False
        self.start_attempted=False
        self.total_end=time.monotonic()+2100;self.work_end=self.total_end-120

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
            limitMeaning='RLIMIT_FSIZE on CLI/attach capture files only; inner job file limit is512MiB.')
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
            attachedBuild=attached,resourceClaim='Configured limits; no measured CPU/RSS/aggregate disk peak or hostile process closure.')
        self.journals.append(record)
        try:self.write(stem+'-result.json',record)
        except BaseException as exc:self.fault('CLI_RECEIPT_RETENTION:'+type(exc).__name__+':'+str(exc)[:1024])
        need(error is None,'CLI_CAPTURE_OR_LAUNCH_FAILURE:'+str(error))
        return record

    @staticmethod
    def streams(record,maximum=4194304):
        for key in ('stdout','stderr'):need(record[key] is not None and record[key]['bytes']<=maximum,'BOUNDED_METADATA_CAPTURE')
        return Path(record['stdout']['path']).read_bytes(),Path(record['stderr']['path']).read_bytes()

    def inspect(self,cleanup=False,allow_absence=False):
        need(self.cid is not None,'NO_KNOWN_CID_NO_MUTATION')
        record=self.cli([DOCKER,'container','inspect',self.cid],'inspect-cid',cleanup=cleanup)
        out,err=self.streams(record)
        if allow_absence and exact_absence(record['exitCode'],out,err,self.cid):return None,record
        need(record['exitCode']==0 and err==b'' and record['classification']=='NATURAL_ZERO','CONTAINER_INSPECT_UNKNOWN')
        current=owned_identity(json.loads(out),self.cid,self.run_id,self.plan)
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
        need(self.release['executionAuthorized'] is True and self.release['scope']=='FIXED_AMETHYST_BUILD_ONLY','FRESH_ROOT_BUILD_RELEASE_REQUIRED')
        need(type(self.run_id) is str and re.fullmatch('[0-9a-f]{32}',self.run_id) is not None,'FRESH_RUNID')
        issued,end=self.release['issuedAtUtcNs'],self.release['notAfterUtcNs']
        need(type(issued) is int and type(end) is int and issued<=time.time_ns()<end and
             0<end-issued<=2400*10**9 and end>=time.time_ns()+2100*10**9,'CURRENT_ROOT_RELEASE_COVERS_ORIGINAL_FINITE_SCOPE')
        method=doc(self.release['buildPreparationSubject'])
        need(self.release['buildPreparationSubject']==self.plan_reference['buildPreparationSubject'],'EXACT_PREPARATION_SUBJECT')
        for descriptor in method['sources']:checked(descriptor)
        for descriptor in self.release['sourceReviews']+self.release['prerequisiteAcceptances']:checked(descriptor)
        need(len(self.release['sourceReviews'])==2 and len(self.release['prerequisiteAcceptances'])>=3,'REQUIRED_INDEPENDENT_SOURCE_AND_DATA_ACCEPTANCES')
        supervisor_subject=doc(self.release['supervisorSubject'])
        need(self.release['supervisorSubject']['path']==str(WORK/'subject.json'),'EXACT_SUPERVISOR_SUBJECT_PATH')
        for descriptor in supervisor_subject['sources']:checked(descriptor)
        actual_sources={p['path']:p for p in supervisor_subject['sources']}
        need(actual_sources.get(str(Path(__file__).resolve()))==pin(Path(__file__).resolve()) and
             actual_sources.get(str(WORK/'plan.json'))==pin(WORK/'plan.json'),'RUNNING_SUPERVISOR_AND_PLAN_SOURCE_JOIN')
        for key,path in (('sourceArchive',ROOT/'output/source.tar'),('sourceArchiveReceipt',ROOT/'output/source-archive.json')):
            need(self.release[key]['path']==str(path),'EXACT_SOURCE_ARCHIVE_PATH');checked(self.release[key],2147483648)
        archive=doc(self.release['sourceArchiveReceipt'])
        need(archive['archive']==self.release['sourceArchive'] and archive['before']==archive['after']==dict(commit=COMMIT,tree=TREE,status=''),'EXACT_SOURCE_ARCHIVE_COMMIT_TREE')
        need(set(self.release['extractions'])=={'jdk','platform','build-tools','ndk'},'ALL_FOUR_ACQUIRED_INPUTS')
        for name,descriptor in self.release['extractions'].items():
            need(descriptor['path']==str(ROOT/'output/acquisition'/(name+'-extraction.json')),'EXACT_ACQUISITION_RECEIPT_PATH')
            extraction=doc(descriptor);need(extraction['toolsExecuted'] is False,'DATA_ONLY_TOOL_ACQUISITION')
            destinations={'jdk':ROOT/'tools/jdk','platform':ROOT/'tools/sdk/platforms/android-37.0',
                'build-tools':ROOT/'tools/sdk/build-tools/36.0.0','ndk':ROOT/'tools/sdk/ndk/30.0.16248370'}
            need(extraction['destination']==str(destinations[name]),'EXACT_ACQUIRED_BUILD_TOOL_PATH')
            tool_inventory(extraction)
        for value in (ROOT/'user/work',ROOT/'cache/build',ROOT/'output/build'):
            safe(value);need(not value.exists(),'FRESH_OWNED_BUILD_ROOT_REQUIRED');value.mkdir(mode=0o700)
        need(os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize>=12884901888,'TWELVE_GIB_BUILD_ADMISSION')
        need(self.work_end-time.monotonic()>1845,'ENOUGH_ORIGINAL_BUDGET_FOR_JOB_AND_CLI')

    def run(self):
        need(not self.root.exists(),'FRESH_SUPERVISOR_ATTEMPT_REQUIRED')
        safe(self.root).mkdir(mode=0o700);(self.root/'docker-config').mkdir(mode=0o700)
        try:
            self.prerequisites()
            existing=self.cli([DOCKER,'container','inspect',NAME],'precreate-name')
            out,err=self.streams(existing)
            need(exact_absence(existing['exitCode'],out,err,NAME),'EXISTING_OR_UNKNOWN_NAMED_CONTAINER_UNTOUCHED')
            network=self.cli([DOCKER,'network','inspect',full_cid(self.release['networkId'])],'network')
            out,err=self.streams(network);need(network['exitCode']==0 and err==b'','NETWORK_INSPECT_UNKNOWN')
            networks=json.loads(out);need(len(networks)==1,'ONE_NETWORK')
            n=networks[0];need(n['Id']==self.release['networkId'] and n['Name']==NETWORK and n['Driver']=='bridge' and not n['Containers'],'EXACT_FRESH_BRIDGE_NETWORK')
            need(n.get('Labels')==self.release['networkLabels'],'ROOT_OWNED_NETWORK_LABELS')
            need(all(n['Labels'].get(k)==v for k,v in {'nbdp.owner':'nbdp-amethyst-rebuild-20261026',
                'nbdp.role':'amethyst-build-network','nbdp.buildRun':self.run_id}.items()),'REQUIRED_NETWORK_OWNER_RUN_LABELS')
            self.create_attempted=True
            created=self.cli(create_argv(self.plan,self.run_id,self.root/'cidfile'),'create')
            self.derive_cid(created)
            need(created['exitCode']==0 and created['classification']=='NATURAL_ZERO','CREATE_FAILED_STOP')
            current,_=self.inspect();need(current['State']['Status']=='created' and current['State']['Running'] is False,'CREATED_ONLY_BEFORE_START')
            need(self.first_fault is None,'PRIOR_FAULT_STOP_BEFORE_START')
            need(self.work_end-time.monotonic()>=1845,'FULL_ORIGINAL_JOB_ATTACH_BUDGET_BEFORE_START')
            self.start_attempted=True
            attached=self.cli([DOCKER,'start','--attach',self.cid],'start-attached',seconds=1845,attached=True)
            current,_=self.inspect();self.job_state=current['State']
            need(attached['classification']=='NATURAL_ZERO','ATTACHED_JOB_FAILED_OR_LOG_CEILING:'+attached['classification'])
            need(current['State']['Running'] is False and current['State']['ExitCode']==0 and current['State']['OOMKilled'] is False,'ACTUAL_JOB_STATE_FAILED')
            result=ROOT/'output/build/rebuilt-apks.json';need(result.is_file(),'ACTUAL_REBUILT_APK_METADATA_REQUIRED')
            self.output_pin=pin(result)
        except BaseException as exc:self.fault(type(exc).__name__+':'+str(exc)[:2048])
        finally:
            self.cleanup()
            result=dict(schema='nbdp-amethyst-build-supervisor-result-v1',runId=self.run_id,cid=self.cid,
                state='BUILD_FINISHED_PENDING_INDEPENDENT_DATA_REVIEW' if self.first_fault is None and self.cleanup_state=='EXACT_CID_ABSENCE_KNOWN' else 'FAILED_OR_UNQUALIFIED_NO_RETRY',
                firstFault=self.first_fault,secondaryErrors=self.secondary,cleanup=self.cleanup_state,jobState=self.job_state,
                jobStateMeaning='Last successful exact-owned inspect after start attempt, including exit/OOM data when observed; UNKNOWN/null if unavailable.',
                rebuiltApks=getattr(self,'output_pin',None),cliReceipts=len(self.journals),
                attachedCapturePerFileLimitBytes=RAW_LIMIT,jobPerFileLimitBytes=JOB_FILE_LIMIT,
                limitsMeaning='Configured per-file/CPU/memory/PID/time limits; no aggregate diskquota or measured peak claim.',
                noHostNumericPidSignalsByController=True,hostileAtomicClosureClaimed=False,canonicalE02Changed=False)
            self.write('result.json',result)
        return result


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release',required=True);parser.add_argument('--release-sha',required=True)
    args=parser.parse_args()
    release_pin=pin(args.release,4194304);need(release_pin['sha256']==args.release_sha,'EXTERNALLY_PINNED_ROOT_RELEASE')
    release=doc(release_pin,4194304)
    plan_reference=json.loads((WORK/'plan.json').read_bytes())
    need(pin(PREP/'build-plan.json')==plan_reference['buildPlan'],'FROZEN_BUILD_METHOD_PLAN')
    supervisor=Supervisor(release,doc(plan_reference['buildPlan']));supervisor.plan_reference=plan_reference
    result=supervisor.run();print(json.dumps(result),flush=True)
    return 0 if result['state']=='BUILD_FINISHED_PENDING_INDEPENDENT_DATA_REVIEW' else 2


if __name__=='__main__':raise SystemExit(main())
