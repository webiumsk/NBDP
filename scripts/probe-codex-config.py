#!/usr/bin/env python3
"""Probe installed CLI project parsing only; no model thread or experiment execution.
Temporary child-only config home keeps user credentials and configuration untouched.
"""
import os
import json
import subprocess
import tempfile
import select
import time
from pathlib import Path


def stop_process(process):
    """Bound shutdown even when parsing or assertions fail."""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is not None and not stream.closed:
            stream.close()


root = Path(__file__).resolve().parent.parent
assert Path.cwd() == root, 'Run from the existing repository root; this script does not change cwd.'
with tempfile.TemporaryDirectory(prefix='nbdp-workflow-cli-home-') as directory:
    home = Path(directory)
    (home / 'config.toml').write_text(
        '[projects.' + json.dumps(str(root)) + ']\ntrust_level = "trusted"\n'
    )
    env = {k: v for k, v in os.environ.items() if k not in ('OPENAI_API_KEY', 'CODEX_API_KEY')}
    env['CODEX_HOME'] = str(home)
    process = subprocess.Popen(
        ['codex', '--strict-config', 'app-server', '--stdio'], cwd=root, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        def send(value):
            process.stdin.write(json.dumps(value) + '\n')
            process.stdin.flush()

        send({'id': 1, 'method': 'initialize', 'params': {
            'clientInfo': {'name': 'nbdp-workflow-config-probe', 'version': '1'},
            'capabilities': {'experimentalApi': True},
        }})
        responses = []
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if select.select([process.stdout], [], [], 1)[0]:
                line = process.stdout.readline()
                if not line:
                    break
                value = json.loads(line)
                responses.append(value)
                if value.get('id') == 1:
                    send({'method': 'initialized', 'params': {}})
                    send({'id': 2, 'method': 'config/read', 'params': {
                        'cwd': str(root), 'includeLayers': True,
                    }})
                if value.get('id') == 2:
                    break
        process.stdin.close()
        process.wait(timeout=5)
        err = process.stderr.read()
        config = next((x for x in responses if x.get('id') == 2), {})
        # Do not persist raw effective configuration, credentials or private prompts.
        effective = config.get('result', {}).get('config', {})
        assert effective.get('agents', {}).get('enabled') is True
        assert effective.get('agents', {}).get('max_concurrent_threads_per_session') == 5
        assert effective.get('features', {}).get('multi_agent') is True
        assert process.returncode == 0 and config.get('result')
        print(json.dumps({
            'exit_status': process.returncode,
            'response_ids': [x.get('id') for x in responses if 'id' in x],
            'config_error': config.get('error'),
            'config_result_keys': list(config.get('result', {})),
            'stderr_tail': err[-1000:],
        }, indent=2))
    finally:
        stop_process(process)

    # Negative control: prove strict parser rejects unknown configuration before RPC.
    negative = subprocess.run(
        ['codex', '--strict-config', '-c', 'nbdp_unknown_schema_probe=true', 'app-server', '--stdio'],
        cwd=root, env=env, input='', capture_output=True, text=True, timeout=15,
    )
    print(json.dumps({
        'negative_exit': negative.returncode,
        'unknown_rejected': 'nbdp_unknown_schema_probe' in negative.stderr,
        'negative_stderr': negative.stderr[-1000:],
    }, indent=2))
    assert negative.returncode == 1 and 'nbdp_unknown_schema_probe' in negative.stderr
print('PASS: strict configuration and project layer verified; unsupported field rejected; disposable home removed.')
