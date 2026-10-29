"""Targeted PURE definitions, zero executions in SOURCE preparation.
All runtime-facing methods are mocked. No fixtures, services or child processes.
"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_data as r
import launch as w
from test_render_data import config,release,d


class WrapperModels(unittest.TestCase):
    def test_remaining243_boundary_and_postrender_delay(self):
        self.assertEqual(r.reserve(400,156.999),243)
        for now in (157,158,400):
            with self.subTest(now=now),self.assertRaises(ValueError):r.reserve(400,now)

    def test_outer_direct_terminal_truth(self):
        args={'cmd':'SYNTHETIC Python dispatcher','workdir':'/SYNTHETIC'}
        records=[dict(toolName='tools.exec_command',actualArguments=args,unmodifiedResponse={'exit_code':0,'output':'recorded'})]
        self.assertEqual(r.actual_outer_responses(records,args),'EXTERNALLY_AUTHENTICATED_OUTER_PYTHON_API_ONLY')

    def test_outer_yielded_all_same_session_truth(self):
        args={'cmd':'SYNTHETIC Python dispatcher'}
        records=[dict(toolName='tools.exec_command',actualArguments=args,unmodifiedResponse={'session_id':17}),dict(toolName='tools.write_stdin',actualArguments={'session_id':17,'chars':''},unmodifiedResponse={'session_id':17}),dict(toolName='tools.write_stdin',actualArguments={'session_id':17},unmodifiedResponse={'exit_code':0})]
        r.actual_outer_responses(records,args)
        for i,key,value in [(1,'session_id',18),(2,'session_id',18)]:
            bad=copy.deepcopy(records);bad[i]['actualArguments'][key]=value
            with self.subTest(i=i),self.assertRaises(ValueError):r.actual_outer_responses(bad,args)

    def test_outer_nonterminal_nonzero_extra_or_substituted_refused(self):
        args={'cmd':'SYNTHETIC'}
        first=dict(toolName='tools.exec_command',actualArguments=args,unmodifiedResponse={'exit_code':0})
        vectors=[[],[dict(first,unmodifiedResponse={'session_id':17})],[dict(first,unmodifiedResponse={'exit_code':124})],[dict(first,actualArguments={'cmd':'OTHER'})],[first,first]]
        for records in vectors:
            with self.subTest(records=records),self.assertRaises(ValueError):r.actual_outer_responses(records,args)

    def request_completion(self):
        request=dict(schema='e02-wrapper-inner-process-request-v1',argv=['SYNTHETIC'],cwd='/SYNTHETIC',environment={},startedUtcNs=100,jobSeconds=240,killGraceSeconds=3,config=d('config'),release=d('release'))
        done=dict(schema='e02-wrapper-inner-process-completion-v1',exitCode=0,stdout=dict(d('stdout'),bytes=40),stderr=dict(d('stderr'),bytes=0),finishedUtcNs=200,captureTransport='REGULAR_FILES',pipeEofEstablished=False,innerApiAttestation=False,primarySubject=d('subject'))
        return request,done

    def test_regular_file_custody_never_inner_api_pid_reap_or_eof(self):
        request,done=self.request_completion();r.inner_receipt(request,done,['SYNTHETIC'],'/SYNTHETIC',d('config'),d('release'),d('subject'))
        for key,value in [('pid',42),('reaped',True),('launchResponse',d('fabricated')),('pipeEofEstablished',True),('innerApiAttestation',True)]:
            bad=dict(done);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.inner_receipt(request,bad,['SYNTHETIC'],'/SYNTHETIC',d('config'),d('release'),d('subject'))

    def test_source_config_release_subject_or_cwd_substitution_refused(self):
        request,done=self.request_completion()
        for key,value in [('argv',['OTHER']),('cwd','/FOREIGN'),('config',d('other-config')),('release',d('other-release')),('jobSeconds',1800)]:
            bad=dict(request);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.inner_receipt(bad,done,['SYNTHETIC'],'/SYNTHETIC',d('config'),d('release'),d('subject'))
        with self.assertRaises(ValueError):r.inner_receipt(request,done,['SYNTHETIC'],'/SYNTHETIC',d('config'),d('release'),d('foreign-subject'))

    def test_native_exact140_and_original19_not_self_certified(self):
        e=dict(status='PASS',tests=[{'ok':True} for _ in range(140)],skipped=[],source_sha256={str(i):'a'*64 for i in range(19)},environment={'rust_binary_sha256':w.NATIVE_SHA})
        n=dict(d('native'),bytes=24100272,sha256=w.NATIVE_SHA);w.native_binding(e,n)
        for change in ('native','status','count','source','skip'):
            bad=copy.deepcopy(e);native=dict(n)
            if change=='native':native['sha256']='b'*64
            elif change=='status':bad['status']='PARTIAL'
            elif change=='count':bad['tests'].pop()
            elif change=='source':bad['source_sha256'].pop('0')
            else:bad['skipped']=[{}]
            with self.subTest(change=change),self.assertRaises(ValueError):w.native_binding(bad,native)

    def test_full_selected_source_mode_membership_or_control_drift(self):
        rows=[dict(pin=d('source'),mode=0o600,uid=1000,gid=1000)]
        w.closure(rows,copy.deepcopy(rows))
        for changed in ([],[dict(rows[0],mode=0o644)],[dict(rows[0],pin=d('foreign-control'))]):
            with self.subTest(changed=changed),self.assertRaises(ValueError):w.closure(changed,rows)

        with patch.object(w,'pin',return_value=d('substituted-source')):
            with self.assertRaises(ValueError):w.checked(d('source'))

    def test_existing_private_or_symlink_paths_refused(self):
        for present,symlink in [(True,False),(False,True)]:
            p=Mock();p.exists.return_value=present;p.is_symlink.return_value=symlink
            with self.subTest(present=present),self.assertRaises(ValueError):w.fresh_paths([p])
        p=Mock();p.exists.return_value=False;p.is_symlink.return_value=False;w.fresh_paths([p])

    def test_foreign_directory_ownership_mode_or_type_refused(self):
        for uid,gid,mode in [(1001,1000,0o40700),(1000,1001,0o40700),(1000,1000,0o40755),(1000,1000,0o100700)]:
            p=Mock();p.stat.return_value=Mock(st_uid=uid,st_gid=gid,st_mode=mode)
            with patch.object(w,'safe',return_value=p),patch.object(w.os,'getuid',return_value=1000),patch.object(w.os,'getgid',return_value=1000):
                with self.subTest(uid=uid,gid=gid,mode=mode),self.assertRaises(ValueError):w.owned_directory('/SYNTHETIC')

    def test_occupied_foreign_network_and_nonliteral_absence_refused(self):
        name='SYNTHETIC';self.assertTrue(w.exact_absence(1,b'',b'Error response from daemon: No such container: '+name.encode(),name))
        for code,out,err in [(0,b'[]',b''),(1,b'',b'permission denied'),(1,b'',b'Error response from daemon: No such container: FOREIGN')]:self.assertFalse(w.exact_absence(code,out,err,name))
        value=dict(Id='a'*64,Name=name,Labels={},Driver='bridge',Internal=True,Ingress=False,Attachable=False,Containers={'FOREIGN':{}})
        with self.assertRaises(ValueError):w.network_identity(value,'a'*64,name,{},set())

    def test_cleanup_failure_is_negative_and_retains_first_fault(self):
        obj=w.Replay.__new__(w.Replay);obj.first=None;obj.secondary=[];obj.fault('ORIGINAL_TIMEOUT');obj.fault('CLEANUP_FAILURE');self.assertEqual(obj.first,'ORIGINAL_TIMEOUT');self.assertEqual(obj.secondary,['CLEANUP_FAILURE'])
        # Exercise cleanup with only symbolic owned network; mutation refuses. No CLI.
        obj.end=1000;obj.proxy=None;obj.ids={};obj.nid='a'*64;obj.net=Mock(side_effect=ValueError('FOREIGN_MEMBER'));obj.cli=Mock()
        with patch.object(w.time,'monotonic',return_value=1):obj.cleanup()
        obj.cli.assert_not_called();self.assertTrue(any('NETWORK_CLEANUP' in f for f in obj.secondary))

    def test_finite_root_lease_and_clock_rewrite_rejected(self):
        self.assertEqual(w.lease_end(100,600000000100,200,1,2),601)
        for issued,expires,now in [(200,300,199),(100,100,100),(100,600000000101,200)]:
            with self.subTest(issued=issued),self.assertRaises(ValueError):w.lease_end(issued,expires,now,1,2)

if __name__=='__main__':unittest.main(verbosity=2)
