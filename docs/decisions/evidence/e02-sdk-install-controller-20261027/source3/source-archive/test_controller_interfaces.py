"""DEFINED ONLY: eight pure concrete install-controller interface/refusal models."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import controller as c

CID='a'*64
RUN='b'*32


def fixture():
    plan={'installPlan':{'path':str(c.PREP/'install-plan.json'),'bytes':100,'sha256':'c'*64}}
    endpoint={'NetworkID':'','EndpointID':'','IPAddress':'','Gateway':'','GlobalIPv6Address':'',
        'IPv6Gateway':'','MacAddress':'','IPPrefixLen':0,'GlobalIPv6PrefixLen':0}
    state={'Status':'created','Running':False,'Pid':0,'StartedAt':c.ZERO_DOCKER_TIME,
        'FinishedAt':c.ZERO_DOCKER_TIME,'OOMKilled':False,'ExitCode':0,'Error':''}
    d={'Id':CID,'Image':c.IMAGE,'Name':'/'+c.NAME,
        'Config':{'WorkingDir':'/user','User':'1000:1000','Image':c.IMAGE,
            'Entrypoint':['/usr/bin/env'],'Cmd':c.container_command(plan),
            'Labels':dict(c.LABELS,**{'nbdp.installRun':RUN}),
            'Env':['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'],
            'OpenStdin':False,'Tty':False},
        'HostConfig':{'Privileged':False,'ReadonlyRootfs':True,'NetworkMode':c.NETWORK_ID,
            'CapAdd':[],'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],
            'Memory':2147483648,'MemorySwap':2147483648,'NanoCpus':2000000000,'PidsLimit':256,
            'Init':True,'PortBindings':{},'PublishAllPorts':False,'Devices':[],
            'DeviceRequests':[],'VolumesFrom':None,'PidMode':'','UTSMode':'','IpcMode':'private',
            'RestartPolicy':{'Name':'no','MaximumRetryCount':0},'AutoRemove':False,
            'CgroupnsMode':'private','ContainerIDFile':str(c.WORK/('attempt-'+RUN)/'cidfile'),
            'LogConfig':{'Type':'none'},'Tmpfs':c.TMPFS,
            'Ulimits':[{'Name':'fsize','Soft':2147483648,'Hard':2147483648}]},
        'Mounts':[{'Type':'bind','Propagation':'rprivate','Source':a,'Destination':b,'RW':rw}
            for a,b,rw in c.fixed_mounts()],
        'State':state,'NetworkSettings':{'Networks':{c.NETWORK:endpoint}}}
    return plan,d


def network():
    return {'Id':c.NETWORK_ID,'Name':c.NETWORK,'Driver':'bridge','Scope':'local',
        'Internal':False,'Attachable':False,'Ingress':False,'ConfigOnly':False,
        'Labels':c.NETWORK_LABELS,'Containers':{}}


def success():
    return {'state':'SDKMANAGER_FINISHED_PENDING_INDEPENDENT_INSTALLED_DATA_REVIEW',
        'firstFault':None,'secondary':[],'packages':list(c.PACKAGES),
        'rawEOF':{'stdout':True,'stderr':True},
        'cleanup':{'leaderReaped':True,'returnCode':0,'sampledLiveGroupAfter':[]},
        'consent':{'affirmativeAttempted':True,'stdinWriteInvoked':True,'writeReturnedBytes':2,
            'flushAndSentRecorded':True,'consumption':'UNKNOWN'}}


class ControllerInterfaces(unittest.TestCase):
    def test_exact_created_identity_and_scoped_command(self):
        p,d=fixture();self.assertIs(c.owned_identity([d],CID,RUN,p,c.NETWORK_ID),d)
        argv=c.create_argv(p,RUN,c.WORK/('attempt-'+RUN)/'cidfile',c.NETWORK_ID)
        self.assertEqual(argv[argv.index('--workdir')+1],'/user')
        self.assertEqual(argv[argv.index('--pull')+1],'never')
        self.assertEqual(argv[argv.index(c.IMAGE)+1:],c.container_command(p))

    def test_readonly_inputs_and_fresh_sdk_mounts_cannot_drift(self):
        for target in ('/jdk','/bootstrap/cmdline-tools/22.0','/prep','/inputs','/sdk'):
            p,d=fixture();mount=next(m for m in d['Mounts'] if m['Destination']==target);mount['RW']=not mount['RW']
            with self.subTest(target=target),self.assertRaises(ValueError):c.owned_identity([d],CID,RUN,p,c.NETWORK_ID)
        p,d=fixture();d['Mounts'].append({'Type':'bind','Propagation':'rprivate','Source':'/FOREIGN/home','Destination':'/foreign','RW':True})
        with self.assertRaises(ValueError):c.owned_identity([d],CID,RUN,p,c.NETWORK_ID)

    def test_install_resource_and_large_archive_file_caps_are_exact(self):
        for key,value in (('PidsLimit',512),('Memory',4294967296),('NanoCpus',4000000000),
                ('Ulimits',[{'Name':'fsize','Soft':536870912,'Hard':536870912}])):
            p,d=fixture();d['HostConfig'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.owned_identity([d],CID,RUN,p,c.NETWORK_ID)

    def test_foreign_identity_labels_and_device_requests_are_refused(self):
        p,d=fixture()
        with self.assertRaises(ValueError):c.owned_identity([d],'d'*64,RUN,p,c.NETWORK_ID)
        for mutate in (lambda x:x['Config']['Labels'].update({'foreign':'value'}),
                lambda x:x['HostConfig'].update(DeviceRequests=[{'Count':-1}]),
                lambda x:x['Config'].update(WorkingDir='/work/source')):
            p,d=fixture();mutate(d)
            with self.assertRaises(ValueError):c.owned_identity([d],CID,RUN,p,c.NETWORK_ID)

    def test_network_full_id_labels_and_foreign_member_refuse(self):
        n=network();self.assertIs(c.network_identity([n],c.NETWORK_ID,set()),n)
        for mutate in (lambda x:x.update(Id='d'*64),lambda x:x.update(Internal=True),
                lambda x:x.update(Labels={}),lambda x:x['Containers'].update({'d'*64:{}})):
            n=network();mutate(n)
            with self.assertRaises(ValueError):c.network_identity([n],c.NETWORK_ID,{CID})

    def test_mutation_never_calls_cli_after_unknown_identity(self):
        obj=c.Supervisor.__new__(c.Supervisor);obj.cid=CID;obj.cleanup_state='NOT_ATTEMPTED';calls=[]
        def refuse(**kwargs):calls.append('fresh-network-and-cid-guard');raise ValueError('UNKNOWN')
        obj.inspect=refuse;obj.cli=lambda *a,**k:calls.append('MUTATION')
        with self.assertRaises(ValueError):obj.mutation(['rm'],'remove')
        self.assertEqual(calls,['fresh-network-and-cid-guard'])

    def test_inner_success_requires_exact_packages_and_honest_consent(self):
        c.inner_success(success())
        for mutate in (lambda x:x.update(packages=x['packages']+['platform-tools']),
                lambda x:x['consent'].update(flushAndSentRecorded=False),
                lambda x:x['consent'].update(consumption='PROVEN'),
                lambda x:x['cleanup'].update(returnCode=1)):
            d=success();mutate(d)
            with self.assertRaises(ValueError):c.inner_success(d)

    def test_root_lease_cannot_extend_or_use_boolean_clock(self):
        self.assertEqual(c.lease_end(10**9,1201*10**9,11*10**9,100,110),1300)
        for issued,end,now in ((True,1201*10**9,11*10**9),(10**9,1202*10**9,11*10**9),
                (12*10**9,1201*10**9,11*10**9),(10**9,11*10**9,11*10**9)):
            with self.assertRaises(ValueError):c.lease_end(issued,end,now,100,110)


if __name__=='__main__':unittest.main(verbosity=2)
