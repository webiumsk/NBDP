"""PREPARED NOT EXECUTED: pure fixed identity/absence/lifecycle DATA models.

No Docker, subprocess, tool, job, acquired input or host signal is invoked.
The models exercise real pure predicates with fake inspect/receipt dictionaries.
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import supervise_build as s

CID='1'*64;RUN='2'*32;NETWORK_ID='7'*64
PROBE=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-amethyst-network-probe-20261027/container-inspect.json')
PROBE_SHA='a17fcd76b49c18cf636c90bd58112b0237e9b66fe2763071116aff40fa51a13d'


def fixture():
    # Read DATA only. Actual build plan is pinned by the enclosing SOURCE packet.
    plan=json.loads((s.PREP/'build-plan.json').read_bytes())
    if s.pin(PROBE)['sha256']!=PROBE_SHA:raise ValueError('EXACT_ACTUAL_PRESTART_PROBE')
    probe=json.loads(PROBE.read_bytes())
    base=plan['proposedDockerCreateArgv'];command=base[base.index(s.IMAGE)+1:]
    mounts=[]
    for i,value in enumerate(base):
        if value!='--mount':continue
        parts=base[i+1].split(',');fields=dict(v.split('=',1) for v in parts if '=' in v)
        mounts.append(dict(Type='bind',Source=fields['src'],Destination=fields['dst'],RW='readonly' not in parts,Propagation='rprivate'))
    value=[dict(Id=CID,Image=s.IMAGE,Name='/'+s.NAME,
        Config=dict(User='1000:1000',WorkingDir='/work',Entrypoint=['/usr/bin/env'],
            Cmd=command[:-2]+[s.TIMEOUT,'--signal=TERM','--kill-after=5s','1800s',*command[-2:]],
            Labels={'nbdp.role':'amethyst-source-build','nbdp.owner':'nbdp-amethyst-rebuild-20261026','nbdp.buildRun':RUN}),
        HostConfig=dict(Privileged=False,ReadonlyRootfs=True,NetworkMode=NETWORK_ID,CapAdd=[],CapDrop=['ALL'],
            SecurityOpt=['no-new-privileges:true'],Memory=6442450944,MemorySwap=6442450944,NanoCpus=4000000000,
            PidsLimit=512,Init=True,PortBindings={},Devices=[],PidMode='',UTSMode='',IpcMode='private',
            LogConfig=dict(Type='none'),Ulimits=[dict(Name='fsize',Soft=s.JOB_FILE_LIMIT,Hard=s.JOB_FILE_LIMIT)],
            Tmpfs={'/tmp':'rw,nosuid,nodev,size=1073741824'}),Mounts=mounts,
        State=copy.deepcopy(probe['State']),NetworkSettings=dict(Networks=copy.deepcopy(probe['Networks']))) ]
    return plan,value


class FixedSupervisorModels(unittest.TestCase):
    def reject(self,change):
        plan,value=fixture();change(value[0])
        with self.assertRaises(ValueError):s.owned_identity(value,CID,RUN,plan,NETWORK_ID)

    def test_exact_identity_positive(self):
        plan,value=fixture();self.assertEqual(s.owned_identity(value,CID,RUN,plan,NETWORK_ID)['Id'],CID)

    def test_foreign_cid_refused(self):self.reject(lambda d:d.update(Id='3'*64))
    def test_foreign_image_refused(self):self.reject(lambda d:d.update(Image='sha256:'+'4'*64))
    def test_foreign_creation_run_refused(self):self.reject(lambda d:d['Config']['Labels'].update({'nbdp.buildRun':'5'*32}))
    def test_root_user_refused(self):self.reject(lambda d:d['Config'].update(User='0:0'))
    def test_omitted_job_file_limit_refused(self):self.reject(lambda d:d['HostConfig'].update(Ulimits=[]))
    def test_weaker_job_file_limit_refused(self):
        self.reject(lambda d:d['HostConfig']['Ulimits'][0].update(Hard=s.JOB_FILE_LIMIT*2))
    def test_host_network_refused(self):self.reject(lambda d:d['HostConfig'].update(NetworkMode='host'))
    def test_host_pid_refused(self):self.reject(lambda d:d['HostConfig'].update(PidMode='host'))
    def test_extra_privilege_refused(self):self.reject(lambda d:d['HostConfig'].update(CapAdd=['SYS_ADMIN']))
    def test_credential_mount_refused(self):
        self.reject(lambda d:d['Mounts'].append(dict(Type='bind',Source='/SYNTHETIC_HOME',Destination='/home/user',RW=False,Propagation='rprivate')))
    def test_socket_mount_refused(self):
        self.reject(lambda d:d['Mounts'].append(dict(Type='bind',Source='/SYNTHETIC_SOCKET',Destination='/var/run/docker.sock',RW=True,Propagation='rprivate')))
    def test_source_writable_mount_refused(self):self.reject(lambda d:d['Mounts'][0].update(RW=True))
    def test_missing_internal_timeout_refused(self):
        self.reject(lambda d:d['Config'].update(Cmd=[x for x in d['Config']['Cmd'] if x!='1800s']))
    def test_daemon_log_accumulation_refused(self):self.reject(lambda d:d['HostConfig'].update(LogConfig=dict(Type='json-file')))

    def test_exact_cid_absence_positive(self):
        self.assertTrue(s.exact_absence(1,b'[]\n',('Error response from daemon: No such container: '+CID+'\n').encode(),CID))
    def test_permission_error_is_not_absence(self):
        self.assertFalse(s.exact_absence(1,b'',b'permission denied while connecting to docker daemon',CID))
    def test_daemon_error_is_not_absence(self):
        self.assertFalse(s.exact_absence(1,b'',b'Cannot connect to the Docker daemon',CID))
    def test_wrong_or_truncated_cid_is_not_absence(self):
        for value in ('6'*64,CID[:12],s.NAME):
            self.assertFalse(s.exact_absence(1,b'[]',('Error: No such object: '+value).encode(),CID))
    def test_mixed_error_is_not_absence(self):
        error=('Error: No such object: '+CID+'\npermission denied').encode()
        self.assertFalse(s.exact_absence(1,b'[]',error,CID))
    def test_stdout_or_wrong_exit_is_not_absence(self):
        error=('Error: No such object: '+CID).encode()
        self.assertFalse(s.exact_absence(1,b'[]\nUNEXPECTED',error,CID))
        self.assertFalse(s.exact_absence(124,b'[]',error,CID))

    def test_capture_limit_is_refusal_even_with_zero_exit(self):
        self.assertEqual(s.classify(0,s.RAW_LIMIT,0),'CAPTURE_LIMIT_REACHED_REFUSED')
        self.assertEqual(s.classify(0,0,s.RAW_LIMIT),'CAPTURE_LIMIT_REACHED_REFUSED')
    def test_natural_nonzero_timeout_classification(self):
        self.assertEqual(s.classify(0,1,1),'NATURAL_ZERO')
        self.assertEqual(s.classify(124,0,0),'GNU_TIMEOUT_EXPIRED')
        self.assertEqual(s.classify(2,0,0),'NONZERO_2')

    def test_fixed_create_additions_keep_original_method_and_job_bound(self):
        plan,_=fixture();argv=s.create_argv(plan,RUN,Path('/SYNTHETIC/cidfile'),NETWORK_ID)
        self.assertEqual(argv[argv.index('--ulimit')+1],'fsize=536870912:536870912')
        self.assertEqual(argv[argv.index('--log-driver')+1],'none')
        self.assertEqual(argv[-6:],[s.TIMEOUT,'--signal=TERM','--kill-after=5s','1800s','/usr/bin/python3','/prep/build_inside.py'])

    def test_first_fault_survives_cleanup_failure(self):
        obj=s.Supervisor.__new__(s.Supervisor);obj.first_fault=None;obj.secondary=[]
        obj.fault('MODEL_BUILD_FAILED');obj.fault('MODEL_CLEANUP_UNKNOWN')
        self.assertEqual(obj.first_fault,'MODEL_BUILD_FAILED');self.assertEqual(obj.secondary,['MODEL_CLEANUP_UNKNOWN'])

    def test_mutation_is_preceded_by_fresh_owned_inspect(self):
        obj=s.Supervisor.__new__(s.Supervisor);obj.cid=CID;obj.first_fault=None;obj.secondary=[]
        calls=[]
        def inspect(**kwargs):calls.append('inspect');return {'State':{'Running':True}},{}
        def cli(argv,label,**kwargs):calls.append(('cli',argv));return dict(exitCode=0,classification='NATURAL_ZERO')
        obj.inspect=inspect;obj.cli=cli
        obj.mutation(['stop','--time','10'],'model-stop',seconds=20)
        self.assertEqual(calls,['inspect',('cli',[s.DOCKER,'stop','--time','10',CID])])

    def test_unknown_inspect_prevents_mutation(self):
        obj=s.Supervisor.__new__(s.Supervisor);obj.cid=CID;calls=[]
        def inspect(**kwargs):raise ValueError('MODEL_INSPECT_UNKNOWN')
        obj.inspect=inspect;obj.cli=lambda *args,**kwargs:calls.append(args)
        with self.assertRaisesRegex(ValueError,'MODEL_INSPECT_UNKNOWN'):obj.mutation(['rm'],'model-remove')
        self.assertEqual(calls,[])

    def test_no_create_attempt_never_touches_unknown_container(self):
        obj=s.Supervisor.__new__(s.Supervisor);obj.cid=None;obj.create_attempted=False;calls=[]
        obj.derive_cid=lambda:calls.append('derive');obj.inspect=lambda **kw:calls.append('inspect')
        obj.cleanup();self.assertEqual(calls,[])
        self.assertEqual(obj.cleanup_state,'NOT_CREATED_NO_MUTATION_ATTEMPTED')

    def test_actual_probe_created_shape_has_full_config_id_but_no_runtime_endpoint_claim(self):
        probe=json.loads(PROBE.read_bytes())
        shape=dict(HostConfig=dict(NetworkMode=probe['NetworkMode']),NetworkSettings=dict(Networks=probe['Networks']),State=probe['State'])
        self.assertEqual(s.network_binding(shape,probe['NetworkMode']),'CREATED_FULL_CONFIG_ID_ONLY_NO_RUNTIME_ENDPOINT_CLAIM')
        self.assertEqual(probe['State']['Pid'],0)
        self.assertEqual(probe['State']['ExitCode'],0)

    def test_source_derived_create_uses_released_full_id_instead_of_original_name(self):
        plan,_=fixture();base=plan['proposedDockerCreateArgv']
        self.assertEqual(base[base.index('--network')+1],s.NETWORK)
        actual=s.create_argv(plan,RUN,Path('/SYNTHETIC/cidfile'),NETWORK_ID)
        self.assertEqual(actual[actual.index('--network')+1],NETWORK_ID)

    def test_original_name_only_host_config_binding_refused(self):
        self.reject(lambda d:d['HostConfig'].update(NetworkMode=s.NETWORK))

    def test_foreign_full_host_network_id_refused(self):
        self.reject(lambda d:d['HostConfig'].update(NetworkMode='8'*64))

    def test_foreign_nonempty_endpoint_id_refused(self):
        self.reject(lambda d:d['NetworkSettings']['Networks'][s.NETWORK].update(NetworkID='8'*64))

    def test_extra_network_endpoint_refused(self):
        self.reject(lambda d:d['NetworkSettings']['Networks'].update(foreign=dict(NetworkID='8'*64)))

    def test_missing_endpoint_network_id_not_silently_empty(self):
        self.reject(lambda d:d['NetworkSettings']['Networks'][s.NETWORK].pop('NetworkID'))

    def test_empty_endpoint_map_refused_even_for_created(self):
        self.reject(lambda d:d['NetworkSettings'].update(Networks={}))

    def test_created_empty_id_with_unobserved_key_refused(self):
        def change(d):d['NetworkSettings']['Networks']={NETWORK_ID:d['NetworkSettings']['Networks'][s.NETWORK]}
        self.reject(change)

    def test_created_empty_network_id_with_allocated_endpoint_refused(self):
        self.reject(lambda d:d['NetworkSettings']['Networks'][s.NETWORK].update(EndpointID='9'*64))

    def test_running_empty_endpoint_id_refused(self):
        self.reject(lambda d:d['State'].update(Status='running',Running=True))

    def test_exited_empty_endpoint_id_refused(self):
        self.reject(lambda d:d['State'].update(Status='exited',Running=False))

    def test_failed_start_left_created_is_cleanup_identity_only(self):
        plan,value=fixture();value[0]['State']['Error']='MODEL_FAILED_START'
        self.assertEqual(s.owned_identity(value,CID,RUN,plan,NETWORK_ID)['State']['Status'],'created')
        with self.assertRaises(ValueError):s.successful_job_state(value[0]['State'],'CREATED_FULL_CONFIG_ID_ONLY_NO_RUNTIME_ENDPOINT_CLAIM')

    def test_initialized_created_zero_exit_never_qualifies_build(self):
        probe=json.loads(PROBE.read_bytes())
        with self.assertRaises(ValueError):s.successful_job_state(probe['State'],'ENDPOINT_FULL_NETWORK_ID_OBSERVED')

    def test_exited_state_needs_real_started_and_finished_times(self):
        _,value=fixture();state=copy.deepcopy(value[0]['State']);state.update(Status='exited')
        with self.assertRaises(ValueError):s.successful_job_state(state,'ENDPOINT_FULL_NETWORK_ID_OBSERVED')
        state['StartedAt']='2026-10-27T00:00:00.000000001Z'
        with self.assertRaises(ValueError):s.successful_job_state(state,'ENDPOINT_FULL_NETWORK_ID_OBSERVED')

    def test_modeled_exited_with_exact_full_endpoint_and_real_times(self):
        plan,value=fixture();d=value[0]
        d['NetworkSettings']['Networks'][s.NETWORK]['NetworkID']=NETWORK_ID
        d['State'].update(Status='exited',StartedAt='2026-10-27T00:00:00.000000001Z',FinishedAt='2026-10-27T00:00:01.000000001Z')
        self.assertEqual(s.owned_identity(value,CID,RUN,plan,NETWORK_ID)['State']['Status'],'exited')
        s.successful_job_state(d['State'],s.network_binding(d,NETWORK_ID))

    def test_fractional_initialized_zero_time_is_not_real_start(self):
        _,value=fixture();state=copy.deepcopy(value[0]['State'])
        state.update(Status='exited',StartedAt='0001-01-01T00:00:00.000000000Z',FinishedAt='2026-10-27T00:00:01Z')
        with self.assertRaises(ValueError):s.successful_job_state(state,'ENDPOINT_FULL_NETWORK_ID_OBSERVED')

    def test_finish_before_start_within_same_microsecond_refused(self):
        _,value=fixture();state=copy.deepcopy(value[0]['State'])
        state.update(Status='exited',StartedAt='2026-10-27T00:00:00.000000009Z',FinishedAt='2026-10-27T00:00:00.000000001Z')
        with self.assertRaises(ValueError):s.successful_job_state(state,'ENDPOINT_FULL_NETWORK_ID_OBSERVED')

    def test_inherited_source_working_directory_refused(self):
        self.reject(lambda d:d['Config'].update(WorkingDir='/work/source'))

    def test_missing_working_directory_refused(self):
        self.reject(lambda d:d['Config'].pop('WorkingDir'))

    def test_foreign_working_directories_refused(self):
        for cwd in ('', '/', '/tmp', '/work/', '/work/user'):
            with self.subTest(cwd=cwd):self.reject(lambda d:d['Config'].update(WorkingDir=cwd))

    def test_plan_without_explicit_workdir_refused(self):
        plan,_=fixture();args=plan['proposedDockerCreateArgv'];i=args.index('--workdir');del args[i:i+2]
        with self.assertRaisesRegex(ValueError,'EXPLICIT_FIXED_WORKDIR_REQUIRED'):
            s.create_argv(plan,RUN,Path('/SYNTHETIC/cidfile'),NETWORK_ID)

    def test_plan_wrong_or_duplicate_workdir_refused(self):
        for wrong in ('/work/source','/tmp','DUPLICATE'):
            plan,_=fixture();args=plan['proposedDockerCreateArgv'];i=args.index('--workdir')
            if wrong=='DUPLICATE':args[i:i]=['--workdir','/work']
            else:args[i+1]=wrong
            with self.subTest(wrong=wrong),self.assertRaisesRegex(ValueError,'EXPLICIT_FIXED_WORKDIR_REQUIRED'):
                s.create_argv(plan,RUN,Path('/SYNTHETIC/cidfile'),NETWORK_ID)

    def test_explicit_plan_has_fresh_roots_and_unchanged_readonly_inputs(self):
        plan,value=fixture();args=plan['proposedDockerCreateArgv']
        self.assertEqual(args.count('--workdir'),1);self.assertEqual(args[args.index('--workdir')+1],'/work')
        mounts={m['Destination']:m for m in value[0]['Mounts']}
        self.assertEqual({dst:mounts[dst]['Source'] for dst in ('/work','/cache','/output')},
            {'/work':str(s.ROOT/'user/work-r2'),'/cache':str(s.ROOT/'cache/build-r2'),'/output':str(s.ROOT/'output/build-r2')})
        self.assertEqual(mounts['/prep']['Source'],str(s.PREP))
        self.assertTrue(all(mounts[d]['RW'] for d in ('/work','/cache','/output')))
        for dst,src in {'/input/source.tar':s.ROOT/'output/source.tar','/input/source-archive.json':s.ROOT/'output/source-archive.json',
                '/jdk':s.ROOT/'tools/jdk','/sdk':s.ROOT/'tools/sdk'}.items():
            self.assertEqual(mounts[dst]['Source'],str(src));self.assertFalse(mounts[dst]['RW'])


if __name__=='__main__':unittest.main(verbosity=2)
