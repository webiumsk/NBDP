"""Real __main__ denial regressions with no operational bytes in fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prepare_coupled as builder

PROGRAM = r'''
import argparse,json,os,pathlib,runpy,sys
script=sys.argv[1];arguments=json.loads(sys.argv[2]);watched=set(json.loads(sys.argv[3]))
opens=[];stats=[]
original_open=os.open;original_stat=pathlib.Path.lstat
def open_file(path,*args,**kwargs):
    if str(path) in watched:
        opens.append(str(path));raise AssertionError('FORBIDDEN_TARGET_OPEN')
    return original_open(path,*args,**kwargs)
def stat_file(path,*args,**kwargs):
    if str(path) in watched:
        stats.append(str(path));raise AssertionError('FORBIDDEN_TARGET_STAT')
    return original_stat(path,*args,**kwargs)
os.open=open_file;pathlib.Path.lstat=stat_file;sys.argv=[script,*arguments]
error=None
try:runpy.run_path(script,run_name='__main__')
except (ValueError,SystemExit) as exc:error=type(exc).__name__+':'+str(exc)
finally:os.open=original_open;pathlib.Path.lstat=original_stat
assert error is not None,'ACTUAL_CLI_MUST_REFUSE'
assert not opens and not stats,(opens,stats)
print(json.dumps(dict(actualMain=True,error=error,forbiddenTargetOpens=len(opens),forbiddenTargetStats=len(stats))))
'''


class RealCliDeniedIdentityControls(unittest.TestCase):
    def invoke(self, spec_pin, output, watched):
        args = ['--spec', spec_pin['path'], '--spec-bytes', str(spec_pin['bytes']),
                '--spec-sha256', spec_pin['sha256'], '--output', str(output)]
        process = subprocess.run([sys.executable, '-I', '-B', '-c', PROGRAM,
            str(HERE / 'prepare_coupled.py'), json.dumps(args), json.dumps(list(watched))],
            cwd=str(HERE), env=dict(PATH='/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8'),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=20, check=False)
        self.assertEqual(process.returncode, 0, process.stderr.decode('utf8', 'replace'))
        self.assertEqual(process.stderr, b'')
        self.assertLessEqual(len(process.stdout), 65536)
        value = json.loads(process.stdout)
        self.assertTrue(value['actualMain'])
        self.assertEqual(value['forbiddenTargetOpens'], 0)
        self.assertEqual(value['forbiddenTargetStats'], 0)
        self.assertFalse(Path(output).exists())
        return value

    def test_all_nine_hash_renamed_spec_aliases_actual_main_zero_io(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-source3-cli-spec-alias-') as temp:
            for index, sha in enumerate(sorted(builder.DENIED_OPERATIONAL_HASHES)):
                path = str(Path(temp) / ('renamed-spec-' + str(index) + '.json'))
                value = self.invoke(dict(path=path, bytes=1, sha256=sha),
                                    Path(temp) / ('output-' + str(index)), [path])
                self.assertIn('HASH_FORBIDDEN_BEFORE_READ', value['error'])

    def test_exact_two_old_opaque_spec_paths_actual_main_zero_io(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-source3-cli-opaque-spec-') as temp:
            for index, pin in enumerate(builder.OPAQUE_EXPECTED_FROM_ROOT.values()):
                value = self.invoke(pin, Path(temp) / ('output-' + str(index)), [pin['path']])
                self.assertIn('BODY_FORBIDDEN', value['error'])

    def test_each_nine_poisoned_last_capability_actual_main_zero_target_io(self):
        with tempfile.TemporaryDirectory(prefix='nbdp-source3-cli-cap-alias-') as temp:
            root = Path(temp)
            for index, sha in enumerate(sorted(builder.DENIED_OPERATIONAL_HASHES)):
                alias = str(root / ('history-or-caller-renamed-' + str(index) + '.json'))
                dummy = dict(path=str(root / 'unread-dummy.json'), bytes=1, sha256='a' * 64)
                spec = {key: None for key in builder.SPEC_KEYS}
                spec.update(schema='e02-root-consumer-coupled-source3-spec-v1', actor='/root',
                    rootScope=builder.BOOTSTRAP_EXPECTED[str(builder.SCOPE)],
                    predecessor=builder.BOOTSTRAP_EXPECTED[str(builder.PREDECESSOR / 'entrypoint.UNBOUND.json')],
                    inputFiles=[dummy, dict(path=alias, bytes=1, sha256=sha)])
                for field in builder.FINAL.values():
                    spec[field] = dummy
                raw = json.dumps(spec).encode()
                path = root / ('spec-' + str(index) + '.json');path.write_bytes(raw)
                pin = builder.descriptor(path, raw)
                value = self.invoke(pin, root / ('output-' + str(index)), [alias, dummy['path']])
                self.assertIn('HASH_FORBIDDEN_BEFORE_READ', value['error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
