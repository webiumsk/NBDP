"""Six helper-level pure definitions only; not full wrapper models/readiness."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_data as r


def d(name):return dict(path='/SYNTHETIC_SOURCE_MODEL/'+name,bytes=1,sha256='a'*64)
def config():return dict(schema='e02-completion-run-config-v2',runId='b'*32,operator='/root/SYNTHETIC',createdAtUtcMillis=None,outputRoot=str(r.RUNS/('b'*32)),environment=None,ordinaryManifest=d('manifest'),ordinaryOrigin=d('origin'),readRoots=['/SYNTHETIC_SOURCE_MODEL'],sourceSubject=d('source'),consumerControls=d('controls'))
def release():return dict(schema='e02-completion-root-release-v2',phase='primary',config=None,sourceSubject=d('source'),operator='/root/SYNTHETIC',issuedAtUtcMillis=None,notAfterUtcMillis=None,sourceQa=d('qa'),sourceSecurity=d('security'),input=None,reviewOrigin=None,primaryTool=None)


class RenderDataOnly(unittest.TestCase):
    def test_only_actual_t0_intent_slot(self):
        value=config();out=r.config_intent(value,value['runId'],d('source'),1000)
        self.assertEqual(out['createdAtUtcMillis'],1000);self.assertIsNone(out['environment']);self.assertIsNone(value['createdAtUtcMillis'])

    def test_config_substitution_and_nonnull_slot_refused(self):
        for key,value in [('sourceSubject',d('other')),('outputRoot','/SYNTHETIC_SOURCE_MODEL/other'),('createdAtUtcMillis',1),('environment',d('env'))]:
            c=config();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.config_intent(c,'b'*32,d('source'),1000)

    def test_environment_slot_same_t0_and_stale_run_refused(self):
        c=r.config_intent(config(),'b'*32,d('source'),1000)
        env=dict(schema='e02-completion-runtime-environment-v2',runId='b'*32,operator='/root/SYNTHETIC',observedAtUtcMillis=1100,relays=[{},{}],proxyReceipt=d('proxy'))
        out=r.environment_slot_config(c,d('env'),env,1200);self.assertEqual(out['createdAtUtcMillis'],1000);self.assertEqual(out['environment'],d('env'))
        for key,value in [('runId','c'*32),('operator','/root/OTHER'),('observedAtUtcMillis',999)]:
            bad=copy.deepcopy(env);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.environment_slot_config(c,d('env'),bad,1200)

    def test_primary_release_exact_source_reviews_phase_and_time(self):
        t=release();out=r.primary_release(t,d('config'),d('source'),'/root/SYNTHETIC',[d('qa'),d('security')],2000,245000)
        self.assertEqual(out['notAfterUtcMillis'],245000);self.assertIsNone(t['config'])
        for key,value in [('phase','candidate'),('sourceSubject',d('wrong')),('sourceQa',d('wrong')),('input',d('arbitrary'))]:
            bad=copy.deepcopy(t);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.primary_release(bad,d('config'),d('source'),'/root/SYNTHETIC',[d('qa'),d('security')],2000,245000)
        with self.assertRaises(ValueError):r.primary_release(t,d('config'),d('source'),'/root/SYNTHETIC',[d('qa'),d('security')],2000,244999)

    def test_exact_timeout_child_never_shared_run(self):
        timeout=dict(d('timeout'),path='/usr/bin/timeout');node=dict(d('node'),path='/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node')
        argv=r.child_command(timeout,node,d('runner.mjs'),d('config'),d('release'),'/SYNTHETIC_SOURCE_MODEL/primary')
        self.assertEqual(argv[:5],['/usr/bin/timeout','--signal=TERM','--kill-after=3s','240s',node['path']]);self.assertEqual(argv[6],'primary')
        with self.assertRaises(ValueError):r.child_command(timeout,node,d('shared/run.mjs'),d('config'),d('release'),'/SYNTHETIC_SOURCE_MODEL/primary')

    def test_nonzero_timeout_and_regularfile_capture_ceiling(self):
        self.assertEqual(r.regular_capture_shape(0,40,0),'REGULAR_FILES_NO_PIPE_EOF_OR_NODE_API_ATTESTATION')
        for code,out,err in [(124,40,0),(1,40,0),(0,4194304,0),(0,40,1),(0,0,0)]:
            with self.subTest(code=code,out=out,err=err),self.assertRaises(ValueError):r.regular_capture_shape(code,out,err)


if __name__=='__main__':unittest.main(verbosity=2)
