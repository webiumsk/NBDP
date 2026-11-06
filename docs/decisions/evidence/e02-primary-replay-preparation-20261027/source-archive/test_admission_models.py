"""DEFINED ONLY: synthetic admission/ownership/lease models; no real infrastructure."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import launch as s

CID='1'*64;NID='2'*64;RUN='3'*32;NAME='nbdp-e02-primary-20261027-'+RUN


def fixture():
    p=dict(images={'strfry':'sha256:'+'a'*64},imageLabels={'strfry':{}},entrypoints={'strfry':['/src/strfry']},labels={'nbdp.owner':s.OWNER,'nbdp.scope':'primary22-only'},user='1000:1000',
        configs={'strfry':dict(path='/SYNTHETIC/strfry.conf')})
    d=dict(Id=CID,Image=p['images']['strfry'],Name='/'+NAME+'-strfry',
        Config=dict(Labels=dict(p['labels'],**{'nbdp.run':RUN,'nbdp.role':'strfry'}),User='1000:1000',Cmd=['relay'],Entrypoint=['/src/strfry'],WorkingDir='/src'),
        HostConfig=dict(NetworkMode=NID,ReadonlyRootfs=True,Privileged=False,NanoCpus=2000000000,Memory=1073741824,PidsLimit=128,
            CapAdd=[],CapDrop=['ALL'],SecurityOpt=['no-new-privileges:true'],PortBindings={},Devices=[],PidMode='',UTSMode='',IpcMode='private',Tmpfs={'/tmp':''},LogConfig={'Type':'none'}),
        Mounts=[dict(Source='/SYNTHETIC/strfry.conf',Destination='/src/strfry.conf',RW=False,Type='bind',Propagation='rprivate'),
            dict(Source=str(s.EXP/'.runtime/strfry'),Destination='/data',RW=True,Type='bind',Propagation='rprivate')],
        NetworkSettings=dict(Networks={NAME:dict(NetworkID=NID,IPAddress='172.18.0.2')}),State=dict(Status='running',Running=True,OOMKilled=False,Pid=123))
    return p,d


def e01():
    return dict(status='PASS',tests=[dict(ok=True) for _ in range(140)],skipped=[],source_sha256={str(i):'a'*64 for i in range(19)},
        environment=dict(rust_binary_sha256=s.NATIVE_SHA))


class AdmissionModels(unittest.TestCase):
    def reject_identity(self,change):
        p,d=fixture();change(d)
        with self.assertRaises(ValueError):s.identity(d,CID,'strfry',p,RUN,NID,NAME)

    def test_exact_synthetic_ownership(self):
        p,d=fixture();self.assertIs(s.identity(d,CID,'strfry',p,RUN,NID,NAME),d)

    def test_wrong_native_e01_hash_refused(self):
        r=e01();n=dict(bytes=24100272,sha256=s.NATIVE_SHA);s.native_binding(r,n)
        for mutant in ('0'*64,'UNAVAILABLE'):
            n['sha256']=mutant
            with self.subTest(mutant=mutant),self.assertRaises(ValueError):s.native_binding(r,n)

    def test_e01_failure_skip_or_source_omission_refused(self):
        for mutation in ('failure','skip','source','partial'):
            r=e01()
            if mutation=='failure':r['tests'][0]['ok']=False
            elif mutation=='skip':r['skipped']=[dict(mandatory=True)]
            elif mutation=='source':r['source_sha256'].pop('0')
            else:r['status']='PARTIAL'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):s.native_binding(r,dict(bytes=24100272,sha256=s.NATIVE_SHA))

    def test_closed_source_membership_and_hash_drift_refused(self):
        expected=[dict(path='node_modules/x.js',sha256='a'*64)]
        s.closure(copy.deepcopy(expected),expected)
        for actual in ([],expected+[dict(path='node_modules/extra.js',sha256='b'*64)],[dict(path='node_modules/x.js',sha256='b'*64)]):
            with self.assertRaises(ValueError):s.closure(actual,expected)

    def test_runtime_prefix_does_not_hide_extra_dependency(self):
        self.assertTrue(s.mutable('experiments/.runtime/strfry/data'))
        self.assertFalse(s.mutable('experiments/.runtime-foreign/loader.js'))
        self.assertFalse(s.mutable('experiments/node_modules/new-loader.js'))

    def test_occupied_or_symlink_outputs_refused(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-primary22-model-') as root:
            p=Path(root)/'SYNTHETIC_OUTPUT';s.fresh_paths([p]);p.write_bytes(b'old')
            with self.assertRaises(ValueError):s.fresh_paths([p])
            link=Path(root)/'SYNTHETIC_DANGLING_LINK';link.symlink_to('missing')
            with self.assertRaises(ValueError):s.fresh_paths([link])

    def test_foreign_full_cid_refused(self):self.reject_identity(lambda d:d.update(Id='4'*64))
    def test_wrong_relay_image_refused(self):self.reject_identity(lambda d:d.update(Image='sha256:'+'5'*64))
    def test_foreign_owner_run_refused(self):self.reject_identity(lambda d:d['Config']['Labels'].update({'nbdp.run':'6'*32}))
    def test_root_user_refused(self):self.reject_identity(lambda d:d['Config'].update(User='0:0'))
    def test_config_writable_or_changed_path_refused(self):
        self.reject_identity(lambda d:d['Mounts'][0].update(RW=True))
        self.reject_identity(lambda d:d['Mounts'][0].update(Source='/FOREIGN/config'))
    def test_weaker_resource_limit_refused(self):self.reject_identity(lambda d:d['HostConfig'].update(PidsLimit=512))
    def test_cap_drop_and_nnp_required(self):
        self.reject_identity(lambda d:d['HostConfig'].update(CapDrop=[]))
        self.reject_identity(lambda d:d['HostConfig'].update(SecurityOpt=[]))
    def test_foreign_network_or_endpoint_refused(self):
        self.reject_identity(lambda d:d['HostConfig'].update(NetworkMode='7'*64))
        self.reject_identity(lambda d:d['NetworkSettings']['Networks'][NAME].update(NetworkID='7'*64))

    def test_unowned_network_member_and_noninternal_refused(self):
        labels={'nbdp.owner':s.OWNER,'nbdp.run':RUN};d=dict(Id=NID,Name=NAME,Labels=labels,Driver='bridge',Internal=True,Ingress=False,Attachable=False,Containers={CID:{}})
        s.network_identity(d,NID,NAME,labels,{CID})
        d['Containers']['8'*64]={}
        with self.assertRaises(ValueError):s.network_identity(d,NID,NAME,labels,{CID})
        d['Containers']={};d['Internal']=False
        with self.assertRaises(ValueError):s.network_identity(d,NID,NAME,labels,{CID})

    def test_only_exact_absence_is_admitted(self):
        self.assertTrue(s.exact_absence(1,b'[]',('Error: No such object: '+CID).encode(),CID))
        self.assertTrue(s.exact_absence(1,b'[]',('Error response from daemon: network '+NID+' not found').encode(),NID,True))
        for code,out,err in [(1,b'',b'permission denied'),(124,b'[]',('Error: No such object: '+CID).encode()),(1,b'[]',('Error: No such object: '+CID[:12]).encode())]:
            self.assertFalse(s.exact_absence(code,out,err,CID))

    def test_job_reserve_refuses_insufficient_deadline(self):
        with patch.object(s.time,'monotonic',return_value=100):
            self.assertEqual(s.remaining(344,243),243)
            for end in (343,200,99):
                with self.assertRaises(ValueError):s.remaining(end,243)

    def test_first_fault_survives_cleanup_error(self):
        obj=s.Replay.__new__(s.Replay);obj.first=None;obj.secondary=[]
        obj.fault('ORIGINAL_PRIMARY_FAILURE');obj.fault('CLEANUP_UNKNOWN')
        self.assertEqual(obj.first,'ORIGINAL_PRIMARY_FAILURE');self.assertEqual(obj.secondary,['CLEANUP_UNKNOWN'])

    def test_owned_inspect_precedes_every_mutation(self):
        obj=s.Replay.__new__(s.Replay);obj.ids={'strfry':CID};calls=[]
        obj.net=lambda *a:calls.append('network')
        obj.inspect=lambda *a:calls.append('inspect')
        obj.cli=lambda *a:(calls.append(a[0]) or (0,b'',b''))
        obj.mutate('strfry',['stop','--time','5'],True)
        self.assertEqual(calls,['network','inspect',['stop','--time','5',CID]])

    def test_unknown_identity_prevents_mutation(self):
        obj=s.Replay.__new__(s.Replay);obj.ids={'strfry':CID};calls=[]
        def refuse(*a):raise ValueError('UNKNOWN_IDENTITY')
        obj.net=lambda *a:None
        obj.inspect=refuse;obj.cli=lambda *a:calls.append(a)
        with self.assertRaises(ValueError):obj.mutate('strfry',['rm'],True)
        self.assertEqual(calls,[])

    def test_no_owned_objects_never_causes_cleanup_mutation(self):
        obj=s.Replay.__new__(s.Replay);obj.proxy=None;obj.ids={};obj.nid=None;obj.end=10**15
        obj.cli=lambda *a:self.fail('No object means no mutation')
        obj.cleanup()

    def test_exact_inherited_labels_union_and_unknown_labels_refused(self):
        p,d=fixture();p['imageLabels']['strfry']={'org.example.source':'SYNTHETIC_PINNED_IMAGE_METADATA'}
        d['Config']['Labels'].update(p['imageLabels']['strfry'])
        s.identity(d,CID,'strfry',p,RUN,NID,NAME)
        d['Config']['Labels']['UNKNOWN_EXTRA']='foreign'
        with self.assertRaises(ValueError):s.identity(d,CID,'strfry',p,RUN,NID,NAME)

    def test_changed_entrypoint_or_workdir_refused(self):
        self.reject_identity(lambda d:d['Config'].update(Entrypoint=['/FOREIGN/relay']))
        self.reject_identity(lambda d:d['Config'].update(WorkingDir='/FOREIGN'))

    def test_unknown_network_prevents_mutation(self):
        obj=s.Replay.__new__(s.Replay);obj.ids={'strfry':CID};calls=[]
        def refuse(*a):raise ValueError('UNKNOWN_NETWORK')
        obj.net=refuse;obj.inspect=lambda *a:calls.append('inspect');obj.cli=lambda *a:calls.append(a)
        with self.assertRaises(ValueError):obj.mutate('strfry',['rm'],True)
        self.assertEqual(calls,[])

    def test_fixed_plan_rejects_phase_change_and_ambient_loader(self):
        # Frozen SOURCE plan is DATA, not a root grant; no runtime functions called.
        p=json.loads((s.HERE/'plan.json').read_text());s.fixed_plan(p)
        q=copy.deepcopy(p);q['argv'][-1]='E01'
        with self.assertRaises(ValueError):s.fixed_plan(q)
        q=copy.deepcopy(p);q['environment']['NODE_OPTIONS']='--require /FOREIGN'
        with self.assertRaises(ValueError):s.fixed_plan(q)

    def test_root_lease_never_widens_and_rejects_clock_domain(self):
        self.assertEqual(s.lease_end(10**9,601*10**9,11*10**9,100,110),700)
        for issued,end,now in [(True,601*10**9,11*10**9),(10**9,602*10**9,11*10**9),(12*10**9,601*10**9,11*10**9),(10**9,11*10**9,11*10**9)]:
            with self.subTest(issued=issued,end=end,now=now),self.assertRaises(ValueError):s.lease_end(issued,end,now,100,110)

    def test_setup_and_cleanup_reserves_begin_before_preflight(self):
        obj=s.Replay({},dict(runId=RUN),1000,100)
        self.assertEqual(obj.setup_end,220);self.assertEqual(obj.work_end,910)


if __name__=='__main__':unittest.main(verbosity=2)
