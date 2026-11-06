"""R3 SOURCE-only model definitions against actual code paths. ZERO executions.
All file/process/clock operands are in-memory mocks; no service or child is run.
"""
import copy,json
from pathlib import Path
import sys,unittest
from unittest.mock import Mock,MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import launch as w
import dispatch as dp
import render_data as r

def d(name):return dict(path='/SYNTHETIC/'+name,bytes=1,sha256='a'*64)

class ActualDecisionPaths(unittest.TestCase):
    def identity_fixture(self):
        obj=w.Replay.__new__(w.Replay);run='b'*32;cid='c'*64;nid='d'*64;name='SYNTHETIC';obj.run=run;obj.name=name;obj.nid=nid;obj.ids={'strfry':cid}
        obj.p=dict(images={'strfry':'sha256:'+'e'*64},configs={'strfry':d('strfry.conf')},labels={'owner':'SYNTHETIC'},imageLabels={'strfry':{}},user='1000:1000',entrypoints={'strfry':['/src/strfry']})
        config=dict(Labels=dict(obj.p['labels'],**{'nbdp.run':run,'nbdp.role':'strfry'}),User='1000:1000',Entrypoint=['/src/strfry'],WorkingDir='/src',Cmd=['relay'])
        host=dict(NetworkMode=nid,ReadonlyRootfs=True,Privileged=False,NanoCpus=2000000000,Memory=1073741824,PidsLimit=128,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Tmpfs={'/tmp':''},LogConfig={'Type':'none'},IpcMode='private')
        mounts=[dict(Source=d('strfry.conf')['path'],Destination='/src/strfry.conf',RW=False,Type='bind',Propagation='rprivate'),dict(Source=str(w.HERE/('attempt-'+run)/'fixture/.runtime/strfry'),Destination='/data',RW=True,Type='bind',Propagation='rprivate')]
        container=dict(Id=cid,Image=obj.p['images']['strfry'],Name='/'+name+'-strfry',Config=config,HostConfig=host,Mounts=mounts,NetworkSettings={'Networks':{name:{'NetworkID':nid}}},State={'Running':True,'OOMKilled':False,'Status':'running'})
        network=dict(Id=nid,Name=name,Labels=dict(obj.p['labels'],**{'nbdp.run':run}),Driver='bridge',Internal=True,Containers={cid:{}},Ingress=False,Attachable=False)
        obj.actual=lambda args,*a,**kw:[network if args[0]=='network' else container];obj.cli=Mock(return_value=(0,b'',b''))
        return obj,container,network

    def test_actual_mutation_rejects_wrong_cid_image_run_network_mount(self):
        for field in ('cid','image','run','network','mount','foreign-network-member'):
            obj,c,n=self.identity_fixture()
            if field=='cid':c['Id']='f'*64
            elif field=='image':c['Image']='sha256:'+'f'*64
            elif field=='run':c['Config']['Labels']['nbdp.run']='f'*32
            elif field=='network':c['HostConfig']['NetworkMode']='f'*64
            elif field=='mount':c['Mounts'][1]['Source']='/FOREIGN/.runtime'
            else:n['Containers']['FOREIGN']={}
            with self.subTest(field=field),patch.object(w,'owned_directory'):
                with self.assertRaises(ValueError):obj.mutate('strfry',['rm'])
            obj.cli.assert_not_called()

    def test_actual_owned_identity_allows_only_full_cid_mutation(self):
        obj,c,n=self.identity_fixture()
        with patch.object(w,'owned_directory'):obj.mutate('strfry',['rm'])
        self.assertEqual(obj.cli.call_args.args[0],['rm',obj.ids['strfry']])

    def test_actual_source_participants_recursive_excludes_reviewers(self):
        root=d('subject.json');child=d('child.json');review=d('review.json')
        docs={root['path']:{'authors':['/root/A'],'operators':['/root/O'],'input':child,'reviews':[review]},child['path']:{'authors':['/root/HELPER'],'operators':[]},review['path']:{'schema':'e02-wrapper-independent-review-v1','authors':['/root/QA'],'actor':'/root/QA'}}
        with patch.object(w,'checked',side_effect=lambda v:v['path']),patch.object(w,'load',side_effect=lambda p:docs[str(p)]):actors=w.source_participants([root])
        self.assertTrue({'/root/A','/root/O','/root/HELPER','/root/r5_plan_fix'}.issubset(actors));self.assertNotIn('/root/QA',actors)

    def acceptance_fixture(self,kind):
        source=d('source.json');subject=d('data.json');accept=d('acceptance.json');qa=d('qa.json');security=d('security.json');plan=d('plan.json');inventory=d('inventory.json')
        data=dict(schema='e02-wrapper-concrete-input-v1' if kind=='inputAcceptance' else 'e02-wrapper-pure-model-result-v2',sourceSubject=source,authors=['/root/NEW_AUTHOR'],operators=['/root/NEW_OPERATOR'])
        if kind=='inputAcceptance':data.update(plan=plan,inventory=inventory)
        else:data.update(scopeVersion='SYNTHETIC_SCOPE',modelsExecuted=1,exitCode=0)
        docs={subject['path']:data,accept['path']:dict(schema='e02-wrapper-reviewed-acceptance-v1',decision='ACCEPT_EXACT_SUBJECT',sourceSubject=source,subject=subject,reviews=[qa,security])}
        docs[source['path']]={'sources':[]};docs[plan['path']]={'authors':[],'operators':[]};docs[inventory['path']]={'roots':[],'files':[]}
        for role,p,actor in [('qa',qa,'/root/QA'),('security',security,'/root/SEC')]:docs[p['path']]=dict(schema='e02-wrapper-independent-review-v1',role=role,actor=actor,subject=subject,decision='ACCEPT_EXACT_SUBJECT',findings=[],rawSessionEvidence=d(role+'.raw'))
        p={'current':{'inputInventory':inventory},'models':{'scopeVersion':'SYNTHETIC_SCOPE','totalDefined':1}};return docs,accept,p,{'sourceSubject':source},plan,qa

    def test_actual_model_and_concrete_operator_author_selfreviews_refused(self):
        for kind in ('modelAcceptance','inputAcceptance'):
            for actor in ('/root/NEW_AUTHOR','/root/NEW_OPERATOR','/root/r5_plan_fix'):
                docs,accept,p,root,plan,qa=self.acceptance_fixture(kind);docs[qa['path']]['actor']=actor
                with self.subTest(kind=kind,actor=actor),patch.object(w,'checked',side_effect=lambda v:v['path']),patch.object(w,'load',side_effect=lambda path:docs[str(path)]):
                    with self.assertRaises(ValueError):w.acceptance_reviews(accept,kind,p,root,plan,set())

    def test_actual_recursive_data_helper_selfreview_refused(self):
        for kind in ('modelAcceptance','inputAcceptance'):
            docs,accept,p,root,plan,qa=self.acceptance_fixture(kind);helper=d('helper.json');docs['/SYNTHETIC/data.json']['input']=helper;docs[helper['path']]={'authors':['/root/NESTED_HELPER'],'operators':[]};docs[qa['path']]['actor']='/root/NESTED_HELPER'
            with self.subTest(kind=kind),patch.object(w,'checked',side_effect=lambda v:v['path']),patch.object(w,'load',side_effect=lambda path:docs[str(path)]):
                with self.assertRaises(ValueError):w.acceptance_reviews(accept,kind,p,root,plan,set())

    def test_actual_data_requires_explicit_authors_and_operators(self):
        for kind in ('modelAcceptance','inputAcceptance'):
            for key in ('authors','operators'):
                docs,accept,p,root,plan,qa=self.acceptance_fixture(kind);del docs['/SYNTHETIC/data.json'][key]
                with self.subTest(kind=kind,key=key),patch.object(w,'checked',side_effect=lambda v:v['path']),patch.object(w,'load',side_effect=lambda path:docs[str(path)]):
                    with self.assertRaises(ValueError):w.acceptance_reviews(accept,kind,p,root,plan,set())

    def test_actual_data_independent_qa_security_positive(self):
        for kind in ('modelAcceptance','inputAcceptance'):
            docs,accept,p,root,plan,qa=self.acceptance_fixture(kind)
            with self.subTest(kind=kind),patch.object(w,'checked',side_effect=lambda v:v['path']),patch.object(w,'load',side_effect=lambda path:docs[str(path)]):actors=w.acceptance_reviews(accept,kind,p,root,plan,set())
            self.assertIn('/root/NEW_OPERATOR',actors);self.assertNotIn('/root/QA',actors);self.assertNotIn('/root/SEC',actors)

    def dispatch_fixture(self):
        caller=d('dispatch.py');source=d('source.json');pp=d('plan.json');tp=d('template.json')
        p=dict(runtimeReady=True,current={'wrapperSource':source},tools={'python':d('python')})
        t=dict(schema='nbdp-completion-primary-wrapper-root-release-v3',actor='/root',executionAuthorized=True,scope='ONE_CURRENT_COMPLETION_PRIMARY_ONLY',runId='b'*32,plan=pp,sourceSubject=source,sourceQa=d('qa'),sourceSecurity=d('sec'),modelAcceptance=d('model'),inputAcceptance=d('concrete'),issuedAtUtcNs=None,notAfterUtcNs=None,renderAuthority=dp.AUTHORITY)
        auth=dict(schema='e02-wrapper-dispatch-authorization-v2',executionAuthorized=True,scope=t['scope'],caller=caller,template=tp,reviews=[],renderAuthority=dp.AUTHORITY)
        here=MagicMock();here.__truediv__.return_value.exists.return_value=False
        return caller,source,pp,tp,p,t,auth,here

    def test_actual_dispatch_wrong_authority_and_occupied_attempt_prevent_render(self):
        for kind in ('caller','template','authority','scope','occupied'):
            caller,source,pp,tp,p,t,auth,here=self.dispatch_fixture()
            if kind=='caller':auth['caller']=d('FOREIGN')
            elif kind=='template':auth['template']=d('FOREIGN')
            elif kind=='authority':auth['renderAuthority']='ARBITRARY_WRITER'
            elif kind=='scope':auth['scope']='OTHER'
            else:here.__truediv__.return_value.exists.return_value=True
            with self.subTest(kind=kind),patch.object(dp,'HERE',here),patch.object(dp,'checked',side_effect=lambda v:v['path']),patch.object(dp,'load',return_value={'sources':[caller]}),patch.object(dp,'put') as put:
                with self.assertRaises(ValueError):dp.authorize_dispatch(pp,p,tp,t,auth,caller)
                put.assert_not_called()

    def test_actual_dispatch_valid_admission_and_duplicate_exclusive_claim(self):
        caller,source,pp,tp,p,t,auth,here=self.dispatch_fixture()
        with patch.object(dp,'HERE',here),patch.object(dp,'checked',side_effect=lambda v:v['path']),patch.object(dp,'load',return_value={'sources':[caller]}):self.assertEqual(dp.authorize_dispatch(pp,p,tp,t,auth,caller),t)
        here.__truediv__.return_value.open.side_effect=FileExistsError('SYNTHETIC_DUPLICATE')
        with patch.object(dp,'HERE',here),patch.object(dp,'put') as put:
            with self.assertRaises(FileExistsError):dp.render_once(t)
            put.assert_not_called()

    def test_actual_dispatch_oneuse_claim_precedes_exact_clock_render(self):
        caller,source,pp,tp,p,t,auth,here=self.dispatch_fixture();events=[]
        here.__truediv__.return_value.open.side_effect=lambda *a,**kw:(events.append('CLAIM') or MagicMock())
        with patch.object(dp,'HERE',here),patch.object(dp.time,'time_ns',return_value=100),patch.object(dp,'put',side_effect=lambda *a:events.append('RENDER')),patch.object(dp,'pin',return_value=d('release')):dp.render_once(t)
        self.assertEqual(events,['CLAIM','RENDER']);self.assertEqual(t['notAfterUtcNs']-t['issuedAtUtcNs'],600000000000)

    def primary_fixture(self):
        obj=w.Replay.__new__(w.Replay);obj.out=MagicMock();obj.env={};obj.work_end=600;obj.setup_end=120;obj.first=None;obj.secondary=[];saved={};obj.write=lambda name,value:saved.__setitem__(name,value)
        release=dict(schema='e02-completion-root-release-v2',phase='primary',config=d('config'),issuedAtUtcMillis=1000,notAfterUtcMillis=244000)
        subject=MagicMock();subject.is_file.return_value=True;subject.__str__.return_value='/SYNTHETIC/primary-subject.json'
        # Separate stdout/stderr paths are symbolic Path objects; opening stays mocked.
        paths={name:MagicMock(name=name) for name in ('primary.stdout','primary.stderr')};obj.out.__truediv__.side_effect=lambda name:paths[name]
        def pin(path):return dict(d('subject' if path is subject else ('stderr' if path is paths['primary.stderr'] else 'stdout')),bytes=0 if path is paths['primary.stderr'] else 40)
        child=Mock();child.wait.return_value=0;child.poll.return_value=0
        return obj,release,subject,saved,pin,child

    def test_actual_primary_postrender40s_delay_refuses_before_popen(self):
        obj,release,subject,saved,pin,child=self.primary_fixture()
        with patch.object(w.time,'time_ns',return_value=41000000000),patch.object(w.time,'monotonic',return_value=1),patch.object(w.subprocess,'Popen') as popen,patch.object(w,'pin',side_effect=pin),patch.object(w,'checked',side_effect=lambda v:v['path']):
            with self.assertRaises(ValueError):obj.record_primary_process(['SYNTHETIC'],d('config'),d('release'),release,subject)
            popen.assert_not_called()

    def test_actual_primary_within_phase_positive_and_observation_before_digest(self):
        obj,release,subject,saved,pin,child=self.primary_fixture()
        with patch.object(w.time,'time_ns',side_effect=[2000000000,2000000000,2000000000,12000000000]),patch.object(w.time,'monotonic',return_value=1),patch.object(w.subprocess,'Popen',return_value=child),patch.object(w,'pin',side_effect=pin),patch.object(w,'checked',side_effect=lambda v:v['path']):done=obj.record_primary_process(['SYNTHETIC'],d('config'),d('release'),release,subject)
        self.assertEqual(done['finishedUtcNs'],12000000000);self.assertEqual(done['finishedUtcNsExact'],'12000000000');self.assertGreater(child.wait.call_args.kwargs['timeout'],0);self.assertLessEqual(child.wait.call_args.kwargs['timeout'],240)

    def test_actual_primary_fake_exit0_beyond_phase_records_then_rejects(self):
        obj,release,subject,saved,pin,child=self.primary_fixture();late=244000000001
        with patch.object(w.time,'time_ns',side_effect=[2000000000,2000000000,2000000000,late]),patch.object(w.time,'monotonic',return_value=1),patch.object(w.subprocess,'Popen',return_value=child),patch.object(w,'pin',side_effect=pin),patch.object(w,'checked',side_effect=lambda v:v['path']):
            with self.assertRaises(ValueError):obj.record_primary_process(['SYNTHETIC'],d('config'),d('release'),release,subject)
        self.assertEqual(saved['primary-completion.json']['exitCode'],0);self.assertEqual(saved['primary-completion.json']['finishedUtcNsExact'],str(late))

    def test_actual_phase_parent_deadline_terminates_owned_group_negative(self):
        obj,release,subject,saved,pin,child=self.primary_fixture();child.pid=123;child.poll.return_value=None;child.wait.side_effect=[w.subprocess.TimeoutExpired(['SYNTHETIC'],239),-15]
        with patch.object(w.time,'time_ns',side_effect=[2000000000,2000000000,2000000000,2000000000,242000000000]),patch.object(w.time,'monotonic',return_value=1),patch.object(w.subprocess,'Popen',return_value=child),patch.object(w.os,'killpg') as killpg,patch.object(w,'pin',side_effect=pin),patch.object(w,'checked',side_effect=lambda v:v['path']):
            with self.assertRaises(ValueError):obj.record_primary_process(['SYNTHETIC'],d('config'),d('release'),release,subject)
        killpg.assert_called_once_with(123,w.signal.SIGTERM);self.assertIn('PRIMARY_PHASE_PARENT_DEADLINE',obj.first);self.assertEqual(saved['primary-completion.json']['exitCode'],-15)

    def test_actual_proxy_cleanup_nonzero_stderr_ceiling_or_kill_faults(self):
        for code,outsize,errsize,killed,preexited in [(-15,40,0,False,False),(1,40,0,False,False),(0,40,1,False,False),(0,4194304,0,False,False),(-9,40,0,True,False),(0,40,0,False,True)]:
            obj=w.Replay.__new__(w.Replay);obj.end=1000;obj.first=None;obj.secondary=[];obj.ids={};obj.nid=None;obj.out=MagicMock();obj.proxy=Mock();obj.proxy.poll.return_value=0 if preexited else None;obj.proxy.returncode=code;obj.proxy_out=Mock();obj.proxy_err=Mock();obj.write=Mock()
            obj.proxy.wait.side_effect=[w.subprocess.TimeoutExpired(['SYNTHETIC'],5),code] if killed else None
            paths={'proxy.stdout':object(),'proxy.stderr':object()};obj.out.__truediv__.side_effect=lambda n:paths[n]
            with self.subTest(code=code,outsize=outsize,errsize=errsize,killed=killed,preexited=preexited),patch.object(w.time,'monotonic',return_value=1),patch.object(w,'pin',side_effect=lambda p:dict(d('capture'),bytes=outsize if p is paths['proxy.stdout'] else errsize)):obj.cleanup()
            self.assertIn('PROXY_CLEANUP',obj.first)

    def test_actual_proxy_cleanup_controlled_sigterm_zero_positive(self):
        obj=w.Replay.__new__(w.Replay);obj.end=1000;obj.first=None;obj.secondary=[];obj.ids={};obj.nid=None;obj.out=MagicMock();obj.proxy=Mock();obj.proxy.poll.return_value=None;obj.proxy.returncode=0;obj.proxy_out=Mock();obj.proxy_err=Mock();obj.write=Mock();paths={'proxy.stdout':object(),'proxy.stderr':object()};obj.out.__truediv__.side_effect=lambda n:paths[n]
        with patch.object(w.time,'monotonic',return_value=1),patch.object(w,'pin',side_effect=lambda p:dict(d('capture'),bytes=40 if p is paths['proxy.stdout'] else 0)):obj.cleanup()
        self.assertIsNone(obj.first);obj.proxy.terminate.assert_called_once();self.assertTrue(obj.write.call_args.args[1]['terminationRequested']);self.assertFalse(obj.write.call_args.args[1]['killRequested'])

if __name__=='__main__':unittest.main(verbosity=2)
