"""SOURCE3 capture-admission definitions only; NOT part of the target46.
Zero execution during preparation. Every process/clock/pipe/file operand is mocked.
"""
import contextlib,io
from pathlib import Path
from types import SimpleNamespace
import sys,unittest
from unittest.mock import MagicMock,Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capture46 as c

def d(name):return dict(path='/SYNTHETIC/'+name,bytes=1,sha256='a'*64)
def owned():return dict(pid=123,groupId=123,sessionId=123,startNewSession=True,ownedPopenHandle=True)
def child():
    p=Mock();p.pid=123;p.returncode=None;p.poll.side_effect=AssertionError('MUST_NOT_POLL_OR_REAP_LEADER_BEFORE_FAULT_SIGNAL');p.stdout=MagicMock();p.stderr=MagicMock();p.stdout.fileno.return_value=11;p.stderr.fileno.return_value=12;return p

class CaptureLifecycleAdmission(unittest.TestCase):
    def held_pipe(self,kind):
        p=child();events=[];sel=Mock();sel.get_map.return_value={'stdout':True};sel.select.return_value=[(SimpleNamespace(data=('stdout',1048576),fd=11),1)]
        # Leader has exited in the OS but is deliberately unreaped by this owner;
        # returncode staysNone until wait, preserving PID/PGID reservation.
        def wait(timeout):events.append(('WAIT',timeout));p.returncode=0;return 0
        p.wait.side_effect=wait
        clock=[0,60000000001,60000000002,60000000003,60000000004] if kind=='TIMEOUT' else [0]+[1000000000]*129+[2000000000,2000000001,2000000002]
        scope=dict(scope='SYNTHETIC_HELD_PIPE',argv=['SYNTHETIC'],cwd='/SYNTHETIC',format='NODE_ACTUAL_MODEL_ROWS')
        with patch.object(c.subprocess,'Popen',return_value=p),patch.object(c.selectors,'DefaultSelector',return_value=sel),patch.object(c.os,'getpgid',return_value=123),patch.object(c.os,'getsid',return_value=123),patch.object(c.os,'set_blocking'),patch.object(c.os,'read',return_value=b'x'*8192),patch.object(c.os,'killpg',side_effect=lambda group,sig:events.append(('KILL',group))),patch.object(c.time,'monotonic_ns',side_effect=clock),patch.object(c,'put'),patch.object(c,'pin',side_effect=lambda path:dict(d(str(path)),mode='0o600')):
            result,stdout,stderr=c.capture_scope(Path('/SYNTHETIC'),scope,1)
        self.assertEqual(result['fault'],kind);self.assertEqual(result['exitCode'],0);self.assertTrue(result['reaped']);self.assertEqual(result['eof'],{'stdout':False,'stderr':False});self.assertEqual(events[0],('KILL',123));self.assertEqual(events[1][0],'WAIT');p.poll.assert_not_called()
        with self.assertRaises(ValueError):c.outcome(scope,result,stdout,stderr)
        return result

    def test_actual_timeout_exited_unreaped_leader_held_pipe_group_killed_first(self):self.held_pipe('TIMEOUT')
    def test_actual_cap_exited_unreaped_leader_held_pipe_group_killed_first(self):self.held_pipe('CAPTURE_LIMIT')

    def test_actual_absent_owned_group_is_recorded_still_negative(self):
        p=child();p.wait.return_value=0
        with patch.object(c.os,'killpg',side_effect=ProcessLookupError('SYNTHETIC_ABSENT')) as kill,patch.object(c.time,'monotonic_ns',side_effect=[60000000000,60000000001]):result=c.finish_owned(p,owned(),'TIMEOUT',60000000000)
        kill.assert_called_once_with(123,c.signal.SIGKILL);self.assertEqual(result['groupClosure']['status'],'OWNED_GROUP_ABSENT');self.assertEqual(result['fault'],'TIMEOUT');self.assertTrue(result['reaped']);p.poll.assert_not_called()

    def test_actual_multiple_waits_share_one_absolute_three_second_deadline(self):
        p=child();p.wait.side_effect=[c.subprocess.TimeoutExpired(['SYNTHETIC'],3),c.subprocess.TimeoutExpired(['SYNTHETIC'],0)]
        with patch.object(c.time,'monotonic_ns',side_effect=[0,0,3000000000]),patch.object(c.os,'killpg') as kill:result=c.finish_owned(p,owned(),None,60000000000)
        self.assertEqual(result['reapDeadlineMonotonicNs'],3000000000);self.assertEqual([call.kwargs['timeout'] for call in p.wait.call_args_list],[3,0]);kill.assert_called_once_with(123,c.signal.SIGKILL);self.assertFalse(result['reaped']);self.assertEqual(result['fault'],'REAP_TIMEOUT')

    def test_actual_fault_wait_retry_never_gets_a_second_three_seconds(self):
        p=child();p.wait.side_effect=[c.subprocess.TimeoutExpired(['SYNTHETIC'],2.5),0]
        with patch.object(c.time,'monotonic_ns',side_effect=[60000000000,60500000000,62500000000]),patch.object(c.os,'killpg') as kill:result=c.finish_owned(p,owned(),'TIMEOUT',60000000000)
        self.assertEqual([call.kwargs['timeout'] for call in p.wait.call_args_list],[2.5,0.5]);self.assertEqual(result['reapDeadlineMonotonicNs'],63000000000);self.assertEqual(result['fault'],'TIMEOUT');kill.assert_called_once_with(123,c.signal.SIGKILL)

    def test_actual_reaped_or_foreign_identity_never_signals_arbitrary_group(self):
        for change in ('reaped','foreign-group','foreign-session'):
            p=child();identity=owned()
            if change=='reaped':p.returncode=0
            elif change=='foreign-group':identity['groupId']=999
            else:identity['sessionId']=999
            with self.subTest(change=change),patch.object(c.os,'killpg') as kill:
                with self.assertRaises(ValueError):c.signal_owned_group(p,identity)
                kill.assert_not_called()

    def test_actual_capture_fault_stops_before_any_later_scope(self):
        scope={'scope':'SYNTHETIC_FIRST','format':'NODE_ACTUAL_MODEL_ROWS'};result=dict(exitCode=0,reaped=True,fault='TIMEOUT',eof={'stdout':False,'stderr':False});plan={'scopes':[scope]*4,'r3SourcePacket':d('R3')};grant={'authors':['/root/SYNTHETIC_AUTHOR'],'operators':['/root/SYNTHETIC_OPERATOR']}
        with patch.object(c,'admission',return_value=(plan,[],grant,d('grant'))),patch.object(c,'safe',return_value=MagicMock()),patch.object(c,'put') as put,patch.object(c,'descriptor',return_value=d('SYNTHETIC')),patch.object(c.time,'monotonic_ns',side_effect=[0,1]),patch.object(c,'capture_scope',return_value=(result,b'',b'')) as capture,contextlib.redirect_stdout(io.StringIO()):code=c.main()
        self.assertEqual(code,2);self.assertEqual(capture.call_count,1);summary=put.call_args.args[2];self.assertEqual(summary['scopesAttempted'],1);self.assertEqual(summary['modelsExecutedQualified'],0);self.assertEqual(summary['state'],'FAILED_OR_UNQUALIFIED_NO_RETRY')

    def test_actual_selector_constructor_failure_precedes_popen(self):
        scope=dict(scope='SYNTHETIC_SELECTOR_FAILURE',argv=['SYNTHETIC'],cwd='/SYNTHETIC')
        with patch.object(c,'put'),patch.object(c.time,'monotonic_ns',return_value=0),patch.object(c.selectors,'DefaultSelector',side_effect=OSError('SYNTHETIC_SELECTOR_CONSTRUCTOR_FAILURE')),patch.object(c.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(OSError,'SYNTHETIC_SELECTOR_CONSTRUCTOR_FAILURE'):c.capture_scope(Path('/SYNTHETIC'),scope,1)
            spawn.assert_not_called()

    def test_actual_full_pipe_eof_is_required_even_with_natural_zero(self):
        for eof in ({'stdout':True,'stderr':False},{'stdout':False,'stderr':True}):
            with self.subTest(eof=eof),self.assertRaises(ValueError):c.outcome({'format':'NODE_ACTUAL_MODEL_ROWS'},dict(exitCode=0,reaped=True,fault=None,eof=eof),b'',b'')

if __name__=='__main__':unittest.main(verbosity=2)
