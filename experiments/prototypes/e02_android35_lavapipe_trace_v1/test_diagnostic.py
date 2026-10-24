"""Prepared pure controls only; never invoke Docker, ADB, emulator or network.

Mock observations are DATA, not actual Android diagnostic evidence. Root must
review and separately release these controls; author did not execute them.
"""
import ast
from contextlib import contextmanager
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent

def load(name):
    spec = importlib.util.spec_from_file_location('health_' + name, HERE / (name + '.py'))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value

guard = load('lease_guard')
driver = load('android_driver')
supervisor = load('supervisor')

class FakeRuntime:
    """No real services: exact recorded operations, fake monotonic time only."""
    def __init__(self, title=None, fail=None, advance=0):
        self.guard = guard; self.now = 100.0; self.calls = []; self.saved = []
        self.title, self.fail, self.advance = title, fail, advance
        self.revoked = False; self.journal = None; self.journals = {}
    def check(self):
        if self.revoked: raise guard.LeaseDenied('sticky synthetic refusal')
    def put_bytes(self, path, raw):
        self.check(); self.saved.append((path, raw))
        return {'path': '/synthetic-data-only/' + path, 'bytes': len(raw), 'sha256': '0' * 64}
    def retain_diagnostic_partial(self, value):
        self.journal = json.loads(json.dumps(value)); self.journals[value['phase']] = self.journal
    def guest(self, role, payload, timeout):
        self.check(); self.calls.append(('guest', role, payload, timeout)); self.now += self.advance
        return b'{"schema":"e02-private-cgroup-diagnostic-v1","status":"UNKNOWN","files":{}}'
    def emulator_prefixes(self):
        self.check(); self.calls.append(('emulator-prefixes',))
        return {'stdout': b'synthetic emulator prefix only\n', 'stderr': b''}
    def sleep(self, seconds):
        self.check(); self.calls.append(('sleep', seconds)); self.now += seconds
    def adb(self, args, timeout):
        self.check(); self.calls.append(('adb', args, timeout)); self.now += self.advance
        if self.fail and args == self.fail:
            self.revoked = True; raise guard.LeaseDenied('first synthetic command failure')
        if args == list(guard.HEALTH_UI[1]):
            title = ('<node resource-id="android:id/alertTitle" text="' + self.title + '"/>') if self.title else ''
            return ('<hierarchy>' + title + '</hierarchy>').encode()
        if args == list(guard.HEALTH_UI[2]): return b'\x89PNG\r\n\x1a\nsynthetic-test-only'
        if args[:1] == ['shell'] and len(args) == 2 and args[1] in guard.PRESSURE_READS.values():
            return b'NBDP_OPTIONAL_UNAVAILABLE\n'
        return b'synthetic captured raw data\n'

class DiagnosticTests(unittest.TestCase):
    def test_closed_readonly_allowlist_and_exact_three_optional_literals(self):
        self.assertEqual(len(guard.PRESSURE_READS), 3)
        for name, args, optional in guard.HEALTH_READS:
            self.assertTrue(guard.allowed_adb(list(args)))
            self.assertEqual(guard.adb_timeout(list(args)), 10)
            if optional:
                self.assertEqual(args, ('shell', guard.PRESSURE_READS[name]))
                for text in (args[1] + '; id', args[1].replace('/proc/pressure/', '/tmp/'),
                             args[1].replace('cat ', 'rm '), args[1] + ' '):
                    self.assertFalse(guard.allowed_adb(['shell', text]))
    def test_diagnostic_guard_denies_identity_login_helper_reverse_and_generic_shell(self):
        for args in (['shell','input','text','nsec1publicsynthetic'], ['shell','input','tap','5','5'],
                     ['shell','sh','-c','cat /proc/meminfo'], ['shell','cat','/proc/self/environ'],
                     ['shell','am','start','-W','-n',guard.PACKAGE + '/com.vitorpamplona.amethyst.ui.MainActivity'],
                     ['reverse','tcp:17777','tcp:17777'], ['install','-t','--no-streaming','/helper.apk']):
            self.assertFalse(guard.allowed_adb(args))
        self.assertFalse(guard.allowed_adb(['shell','am','start','-n',guard.PACKAGE+'/com.vitorpamplona.amethyst.ui.MainActivity']))
        self.assertFalse(guard.allowed_adb(['install','--no-streaming','/artifact.apk']))
    def test_optional_unsupported_and_original_read_failure_remain_unknown(self):
        self.assertEqual(driver.optional_status(b'NBDP_OPTIONAL_UNAVAILABLE\n'),
                         {'status':'UNKNOWN_UNAVAILABLE','originalReadExit':None})
        self.assertEqual(driver.optional_status(b'partial\nNBDP_OPTIONAL_READ_FAILED:13\n'),
                         {'status':'UNKNOWN_READ_FAILED','originalReadExit':13})
        self.assertEqual(driver.optional_status(b'some avg10=0.00 total=1\n')['status'],'CAPTURED')
        for raw in (b'', b'NBDP_OPTIONAL_READ_FAILED:0\n', b'NBDP_OPTIONAL_UNKNOWN\n'):
            with self.assertRaises(RuntimeError): driver.optional_status(raw)
    def test_zero_install_intent_identity_fixture_and_no_healthy_result(self):
        runtime=FakeRuntime(); result=driver.run(runtime,clock=lambda:runtime.now)
        self.assertEqual(result['activityIntents'],0); self.assertEqual(result['apkInstalls'],0)
        self.assertEqual(result['environmentStatus'],'UNKNOWN')
        self.assertFalse(result['ordinaryControlQualified'])
        self.assertEqual(result['identityInputs']+result['loginActions']+result['fixtureOperations']+result['clipboardOperations'],0)
        self.assertTrue(runtime.journal)
        for call in runtime.calls:
            if call[0]=='adb':
                self.assertTrue(guard.allowed_adb(call[1])); self.assertLessEqual(call[2],10)
                self.assertNotEqual(call[1][:1],['install']); self.assertNotEqual(call[1][:3],['shell','am','start'])
            if call[0]=='guest': self.assertLessEqual(call[3],15)

    def test_observed_anr_preserved_until_after_late_capture_without_any_dialog_action(self):
        runtime=FakeRuntime(title="Quickstep isn't responding")
        result=driver.run(runtime, clock=lambda:runtime.now)
        self.assertEqual(result['environmentStatus'],'ENVIRONMENT_FAILURE')
        self.assertIn('Quickstep',result['firstEnvironmentError'])
        self.assertIn('late',[x['phase'] for x in result['observations']])
        self.assertFalse(any(x[0]=='adb' and x[1][:2]==['shell','input'] for x in runtime.calls))
    def test_first_mandatory_failure_sticky_and_partial_retained_without_later_guest_commands(self):
        failed=list(guard.HEALTH_READS[0][1]);runtime=FakeRuntime(fail=failed)
        with self.assertRaisesRegex(guard.LeaseDenied,'first synthetic command failure'):
            driver.run(runtime, clock=lambda:runtime.now)
        self.assertTrue(runtime.revoked)
        self.assertIn('first synthetic command failure',runtime.journal['firstError'])
        self.assertEqual(runtime.calls[-1][1],failed)
        self.assertEqual(runtime.journal['activityIntents'],0)
    def test_original_diagnostic_budget_not_renewed_or_extended_by_phases(self):
        runtime=FakeRuntime(advance=181)
        with self.assertRaisesRegex(RuntimeError,'Original trace phase'):
            driver.run(runtime,clock=lambda:runtime.now)
        self.assertEqual(runtime.trace_phase_deadlines['postboot'],280); self.assertFalse(hasattr(runtime,'diagnostic_deadline'))
        self.assertEqual(len(runtime.calls),1)
        self.assertEqual(runtime.journal['activityIntents'],0)
    def test_private_cgroup_absence_unknown_and_lease_refusal_propagates(self):
        lease=SimpleNamespace(check=lambda:None)
        with patch.object(guard.os,'open',side_effect=FileNotFoundError('synthetic unavailable')):
            self.assertEqual(guard.health_cgroup(lease)['status'],'UNKNOWN')
        lease=SimpleNamespace(check=lambda:(_ for _ in ()).throw(guard.LeaseDenied('original expired')))
        with self.assertRaisesRegex(guard.LeaseDenied,'original expired'): guard.health_cgroup(lease)
    def test_diagnostic_source_no_actions_and_original_cleanup_guard_ast_unchanged(self):
        tree=ast.parse((HERE/'android_driver.py').read_bytes())
        methods=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertNotIn('fixture',methods)
        self.assertNotIn('snapshot',methods)
        # AST observation only: actual guard/cleanup controls are separate.
        self.assertEqual(driver.BUDGET_SECONDS,180)
        self.assertEqual(supervisor.SCOPE,'ANDROID35_LAVAPIPE_TRACE_ONLY_NO_INSTALL_OR_INTENT')
    def test_fixture_operations_denied_even_if_diagnostic_driver_changes(self):
        runtime=supervisor.Runtime.__new__(supervisor.Runtime)
        for operation in ('prepare','status','publish'):
            with self.assertRaisesRegex(RuntimeError,'no fixture-operation authority'): runtime.fixture(operation)

    def test_original_phase_deadline_refuses_before_docker_dispatch(self):
        runtime=supervisor.Runtime.__new__(supervisor.Runtime)
        runtime.check=lambda:None; runtime.diagnostic_deadline=99; runtime.sequence=0
        calls=[]
        runtime.lease=SimpleNamespace(run_checked=lambda *a,**kw:calls.append(a))
        with patch.object(supervisor.time,'monotonic',return_value=100):
            with self.assertRaisesRegex(RuntimeError,'Original diagnostic phase'): runtime.command(['inspect','not-executed'])
        self.assertEqual(calls,[]); self.assertEqual(runtime.sequence,0)
    def test_phase_bounds_each_nested_command_to15s(self):
        runtime=supervisor.Runtime.__new__(supervisor.Runtime)
        runtime.check=lambda:None; runtime.diagnostic_deadline=280; runtime.sequence=0
        runtime.docker='/synthetic-not-run/docker'; runtime.host_env={}; calls=[]
        def run(argv,timeout,env):
            calls.append(timeout)
            return dict(exit=0,error=None,reaped=True,forced=False,stdoutEOF=True,stderrEOF=True,stdout=b'',stderr=b'')
        runtime.lease=SimpleNamespace(run_checked=run); runtime.record_command=lambda *a:None
        with patch.object(supervisor.time,'monotonic',return_value=100): runtime.command(['inspect','not-executed'])
        self.assertEqual(calls,[15])
    def test_private_cgroup_admission_refuses_host_namespace_or_parent(self):
        cleanup=load('test_cleanup'); fixture=cleanup.CleanupTests()
        runtime,data=fixture.runtime(Path('/synthetic-owned-unused'))
        for mode,parent in [('host',''),('',''),('private','foreign-parent')]:
            modified=json.loads(json.dumps(data)); modified['HostConfig'].update(CgroupnsMode=mode,CgroupParent=parent)
            with self.assertRaisesRegex(RuntimeError,'isolation/resource mismatch'):
                runtime.validate_owned('anchor',modified)

    @contextmanager
    def mocked_cgroup_files(self, files):
        """Fixed DATA byte provider; actual reader/grammar/lease stay unchanged.

        No host file is read. Unexpected paths, writes and unknown descriptors
        fail the control rather than being normalized into an expected result.
        """
        allowed = {'/proc/self/cgroup', '/proc/self/mountinfo',
                   '/sys/fs/cgroup/cpu.stat', '/sys/fs/cgroup/memory.events',
                   '/sys/fs/cgroup/memory.current'}
        opened=[]; handles={}; serial=[1000]
        def open_fixed(path, flags):
            self.assertIn(path, allowed)
            self.assertEqual(flags, guard.os.O_RDONLY | guard.os.O_NOFOLLOW)
            opened.append(path)
            if path not in files: raise FileNotFoundError('synthetic optional metric absent')
            serial[0]+=1; handles[serial[0]]=[files[path],0]
            return serial[0]
        def read_fixed(fd, size):
            self.assertIn(fd,handles)
            self.assertTrue(0 < size <= 8192)
            value,offset=handles[fd]; block=value[offset:offset+size]
            handles[fd][1]+=len(block); return block
        def close_fixed(fd):
            self.assertIn(fd,handles); del handles[fd]
        with (patch.object(guard.os,'open',side_effect=open_fixed),
              patch.object(guard.os,'read',side_effect=read_fixed),
              patch.object(guard.os,'close',side_effect=close_fixed)):
            try: yield opened
            finally: self.assertEqual(handles,{})

    def cgroup_data(self):
        return {'/proc/self/cgroup':b'0::/\n',
                '/proc/self/mountinfo':b'10 1 0:10 / /sys/fs/cgroup ro,nosuid,nodev,noexec,relatime - cgroup2 cgroup rw\n',
                '/sys/fs/cgroup/cpu.stat':b'usage_usec 7\nnr_throttled 1\nthrottled_usec 2\n',
                '/sys/fs/cgroup/memory.events':b'oom 0\noom_kill 0\n',
                '/sys/fs/cgroup/memory.current':b'123456\n'}

    def test_actual_runtime_adb_default_accepts_setup_boot_and_fingerprint_getprop(self):
        # This regression uses the actual Runtime.adb, actual allowlist and
        # actual adb_timeout. Only downstream owned dispatch is mocked.
        runtime=supervisor.Runtime.__new__(supervisor.Runtime)
        runtime.guard=guard; calls=[]
        def dispatch(role,payload,timeout):
            calls.append((role,payload,timeout)); return b'1\n'
        runtime.guest=dispatch
        for prop in ('sys.boot_completed','ro.build.fingerprint','ro.build.version.sdk'):
            self.assertEqual(runtime.adb(['shell','getprop',prop]),b'1\n')
        self.assertEqual(calls,[('android',['adb','shell','getprop',prop],15)
          for prop in ('sys.boot_completed','ro.build.fingerprint','ro.build.version.sdk')])
        # Also exercise a UI default without calling a real UI or SDK.
        runtime.adb(list(guard.HEALTH_UI[1])); self.assertEqual(calls[-1][2],15)

    def test_actual_runtime_adb_still_refuses_above10_and_preserves_explicit180_setup(self):
        runtime=supervisor.Runtime.__new__(supervisor.Runtime); runtime.guard=guard; calls=[]
        runtime.guest=lambda role,payload,timeout:calls.append((role,payload,timeout))
        with self.assertRaisesRegex(RuntimeError,'Fixed ADB ceiling'):
            runtime.adb(['shell','getprop','sys.boot_completed'],timeout=15)
        self.assertEqual(calls,[])
        runtime.adb(['wait-for-device'],timeout=180)
        with self.assertRaisesRegex(RuntimeError,'Closed ADB allowlist'):
            runtime.adb(['install','--no-streaming','/artifact.apk'],timeout=180)
        self.assertEqual([x[2] for x in calls],[185])
        self.assertEqual(guard.adb_timeout(['shell','getprop','sys.boot_completed']),10)

    def test_actual_cgroup_reader_valid_private_ro_root_and_fixed_paths(self):
        files=self.cgroup_data(); lease=SimpleNamespace(check=lambda:None)
        with self.mocked_cgroup_files(files) as opened:
            result=guard.health_cgroup(lease)
        self.assertEqual(result['status'],'CAPTURED')
        self.assertEqual(opened,['/proc/self/cgroup','/proc/self/mountinfo',
          '/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/memory.events','/sys/fs/cgroup/memory.current'])
        self.assertEqual(result['files']['cpu.stat']['raw'],files['/sys/fs/cgroup/cpu.stat'].decode())
        self.assertEqual(result['files']['memory.events']['raw'],files['/sys/fs/cgroup/memory.events'].decode())
        self.assertEqual(result['files']['memory.current']['raw'],'123456\n')
        self.assertEqual(result['measuredProcessScope'],'Entire owned Android Docker container cgroup')

    def test_actual_cgroup_reader_rejects_unqualified_root_before_any_metric_read(self):
        base=self.cgroup_data(); mount=base['/proc/self/mountinfo']
        variants=[('nonroot_self',{'/proc/self/cgroup':b'0::/nested\n'}),
          ('writable_mount',{'/proc/self/mountinfo':mount.replace(b' ro,',b' rw,')}),
          ('wrong_mount_root',{'/proc/self/mountinfo':mount.replace(b' / /sys/fs/cgroup ',b' /nested /sys/fs/cgroup ')}),
          ('noncgroup2',{'/proc/self/mountinfo':mount.replace(b'- cgroup2 ',b'- cgroup ')}),
          ('duplicate_mount',{'/proc/self/mountinfo':mount+mount})]
        for name,changes in variants:
            with self.subTest(case=name):
                with self.mocked_cgroup_files(dict(base,**changes)) as opened:
                    result=guard.health_cgroup(SimpleNamespace(check=lambda:None))
                self.assertEqual(result['status'],'UNKNOWN')
                self.assertEqual(result['files'],{})
                self.assertFalse(any(path.startswith('/sys/fs/cgroup/') for path in opened))
                self.assertEqual(opened,['/proc/self/cgroup','/proc/self/mountinfo'])

    def test_actual_cgroup_reader_missing_optional_metric_is_explicit_partial_unknown(self):
        files=self.cgroup_data(); del files['/sys/fs/cgroup/memory.events']
        with self.mocked_cgroup_files(files) as opened:
            result=guard.health_cgroup(SimpleNamespace(check=lambda:None))
        self.assertEqual(result['status'],'UNKNOWN_PARTIAL')
        self.assertEqual(result['files']['memory.events']['status'],'UNKNOWN')
        self.assertIn('FileNotFoundError',result['files']['memory.events']['error'])
        self.assertEqual(result['files']['cpu.stat']['status'],'CAPTURED')
        self.assertEqual(result['files']['memory.current']['status'],'CAPTURED')
        self.assertEqual(len(opened),5)

    def test_actual_cgroup_reader_propagates_sticky_lease_without_later_reads(self):
        # Lease behavior itself is separately covered by the unchanged real
        # guard suite. This DATA lease verifies the reader cannot swallow it.
        class StickyLease:
            def __init__(self): self.calls=0; self.revoked=False
            def check(self):
                self.calls+=1
                if self.revoked or self.calls>=3:
                    self.revoked=True; raise guard.LeaseDenied('synthetic original lease expired')
        lease=StickyLease()
        with self.mocked_cgroup_files(self.cgroup_data()) as opened:
            with self.assertRaisesRegex(guard.LeaseDenied,'original lease expired'):
                guard.health_cgroup(lease)
            first=list(opened)
            with self.assertRaisesRegex(guard.LeaseDenied,'original lease expired'):
                guard.health_cgroup(lease)
            self.assertEqual(opened,first)
        self.assertEqual(opened,['/proc/self/cgroup']); self.assertTrue(lease.revoked)

    def test_new_trace_tuples_exact_and_altered_flags_paths_or_shell_refused(self):
        exact=[['shell','dumpsys','-t','5','activity','lastanr-traces'],
          ['shell','dumpsys','-t','5','dropbox','--print','system_app_anr'],
          ['shell','cat','/proc/uptime'],
          ['shell','logcat','-b','events','-d','-v','epoch'],
          ['shell','logcat','-b','system','-d','-v','epoch'],
          ['shell','ps','-A','-o','PID,NAME']]
        for args in exact:
            self.assertTrue(guard.allowed_adb(args)); self.assertEqual(guard.adb_timeout(args),10)
            self.assertFalse(guard.allowed_adb(args+['--unexpected']))
        for args in (['shell','dumpsys','-t','15','activity','lastanr-traces'],
          ['shell','dumpsys','-t','5','dropbox','--print','data_app_anr'],
          ['shell','cat','/proc/1/stack'], ['shell','logcat','-b','events','-d','-v','epoch','-t','1000'],
          ['shell','logcat','-b','crash','-d','-v','epoch'], ['shell','ps','-A','-o','PID,ARGS'],
          ['shell','sh','-c','dumpsys activity lastanr-traces'],['root'],
          ['shell','kill','-3','1'], ['shell','settings','put','global','show_first_crash_dialog','0']):
            self.assertFalse(guard.allowed_adb(args))
    def test_early_phase_exact_three_readonly_commands30s_and_no_actions(self):
        runtime=FakeRuntime(); result=driver.early(runtime,clock=lambda:runtime.now)
        self.assertEqual(result['phase'],'early'); self.assertEqual(result['phaseBudgetSeconds'],30)
        self.assertTrue(result['completed']); self.assertEqual(result['environmentStatus'],'UNKNOWN')
        self.assertEqual([x[1] for x in runtime.calls if x[0]=='adb'],[list(x[1]) for x in guard.EARLY_BOOT_READS])
        self.assertEqual(runtime.trace_phase_deadlines['early'],130)
        self.assertFalse(hasattr(runtime,'diagnostic_deadline'))
        self.assertEqual(result['apkInstalls']+result['activityIntents']+result['identityInputs']+result['loginActions'],0)
    def test_early_expiry_retains_partial_prefix_and_never_reopens_deadline(self):
        runtime=FakeRuntime(advance=31)
        with self.assertRaisesRegex(RuntimeError,'Original trace phase deadline expired'):
            driver.early(runtime,clock=lambda:runtime.now)
        self.assertEqual(len(runtime.calls),1); self.assertEqual(runtime.trace_phase_deadlines['early'],130)
        self.assertFalse(runtime.journal['completed']); self.assertEqual(runtime.journal['phase'],'early')
        with self.assertRaisesRegex(RuntimeError,'cannot be renewed'):
            driver.early(runtime,clock=lambda:runtime.now)
        self.assertEqual(len(runtime.calls),1)
    def test_separate_phase_ledgers_not_renewable_and_postboot180_after_boot_wait(self):
        runtime=FakeRuntime(); early=driver.early(runtime,clock=lambda:runtime.now)
        runtime.now+=11  # DATA model of original boot-wait interval, not a lease renewal.
        post=driver.run(runtime,clock=lambda:runtime.now)
        self.assertEqual(early['phaseDeadlineMonotonicNs'],130000000000)
        self.assertEqual(post['phaseDeadlineMonotonicNs'],291000000000)
        self.assertEqual(runtime.trace_phase_deadlines,{'early':130,'postboot':291})
        self.assertEqual(set(runtime.journals),{'early','postboot'})
        with self.assertRaisesRegex(RuntimeError,'cannot be renewed'):
            driver.run(runtime,clock=lambda:runtime.now)
        for seconds in (30.0,True,31,180):
            with self.assertRaisesRegex(RuntimeError,'Fixed independent'):
                driver.TracePhase(FakeRuntime(),'early',seconds,lambda:100)
    def test_supervisor_source_order_early_before_boot_wait_and_no_install_intent(self):
        # SOURCE_AST_ORDER_ONLY; this is not executed Android setup evidence.
        tree=ast.parse((HERE/'supervisor.py').read_bytes())
        execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
        calls=[n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        early=next(n.lineno for n in calls if n.func.attr=='early')
        post=next(n.lineno for n in calls if n.func.attr=='run')
        boot=[]; wait=[]
        for n in calls:
            if n.func.attr!='adb' or not n.args or not isinstance(n.args[0],ast.List): continue
            parts=[x.value if isinstance(x,ast.Constant) else None for x in n.args[0].elts]
            if parts==['wait-for-device']: wait.append(n.lineno)
            if parts==['shell','getprop','sys.boot_completed']: boot.append(n.lineno)
            self.assertNotEqual(parts[:1],['install']); self.assertNotEqual(parts[:3],['shell','am','start'])
        self.assertEqual(len(wait),1); self.assertEqual(len(boot),1)
        self.assertLess(wait[0],early); self.assertLess(early,boot[0]); self.assertLess(boot[0],post)
    def test_trace_support_permission_no_entry_and_unrelated_candidates_never_match_pid_stack(self):
        cases=[(b'', 'UNKNOWN_EMPTY'),(b'Permission Denial: dump denied\n','UNKNOWN_PERMISSION_DENIED'),
          (b'Unknown command: lastanr-traces\n','UNKNOWN_EXPLICIT_UNSUPPORTED'),
          (b'ACTIVITY MANAGER LAST ANR\n(nothing)\n','UNKNOWN_EXPLICIT_NO_ENTRY'),
          (b'(No entries found.)\n','UNKNOWN_EXPLICIT_NO_ENTRY'),
          (b'(contents lost)\n','UNKNOWN_CONTENTS_LOST'),
          (b'----- pid 123 at 2026-10-24 -----\nReason: unrelated process\n stack data\n','CANDIDATE_UNMATCHED'),
          (b'\xff','UNKNOWN_NON_UTF8')]
        for raw,expected in cases:
            row=driver.trace_observation(raw); self.assertEqual(row['availability'],expected)
            self.assertEqual(row['runtimeSupport'],'UNKNOWN')
            for field in ('matchingAnr','pid','reason','stack'): self.assertEqual(row[field],'UNKNOWN')
        runtime=FakeRuntime(title="System UI isn't responding")
        report=driver.run(runtime,clock=lambda:runtime.now)
        self.assertEqual(report['traceCorrelation'],'UNKNOWN')
    def test_trace_capture8mib_overflow_refuses_before_own_raw_retention(self):
        runtime=FakeRuntime(); phase=driver.TracePhase(runtime,'early',30,lambda:runtime.now)
        try:
            with self.assertRaisesRegex(RuntimeError,'Bounded actual trace output'):
                phase.capture('early','synthetic-overflow',lambda:b'x'*(8388608+1))
            self.assertEqual(runtime.saved,[]); self.assertEqual(runtime.calls,[])
        finally: phase.release_cap()
    def test_fixed_partial_journal_paths_are_unique_and_unknown_phase_refuses(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-boot-trace-controls-') as directory:
            runtime=supervisor.Runtime.__new__(supervisor.Runtime);runtime.out=Path(directory)
            runtime.retain_diagnostic_partial({'phase':'early','firstError':'original early'})
            runtime.retain_diagnostic_partial({'phase':'postboot','firstError':None})
            self.assertEqual(set(p.name for p in runtime.out.iterdir()),{'early-boot-partial.json','diagnostic-partial.json'})
            with self.assertRaises(FileExistsError): runtime.retain_diagnostic_partial({'phase':'early','firstError':'replacement'})
            with self.assertRaisesRegex(RuntimeError,'Fixed trace journal phase'):
                runtime.retain_diagnostic_partial({'phase':'../foreign'})
            self.assertEqual(json.loads((runtime.out/'early-boot-partial.json').read_bytes())['firstError'],'original early')
    def test_new_mandatory_trace_failure_sticky_no_allow_failure_or_later_commands(self):
        names={'lastanr-traces','dropbox-system-app-anr','logcat-events','logcat-system'}
        for name,args,optional in guard.HEALTH_READS:
            if name not in names: continue
            self.assertFalse(optional)
            runtime=FakeRuntime(fail=list(args))
            with self.assertRaisesRegex(guard.LeaseDenied,'first synthetic command failure'):
                driver.run(runtime,clock=lambda:runtime.now)
            self.assertTrue(runtime.revoked);self.assertEqual(runtime.calls[-1][1],list(args))
            self.assertIn('first synthetic command failure',runtime.journal['firstError'])
            self.assertFalse(hasattr(runtime,'diagnostic_deadline'))
            self.assertEqual(runtime.journal['apkInstalls']+runtime.journal['activityIntents'],0)

if __name__=='__main__': unittest.main()
