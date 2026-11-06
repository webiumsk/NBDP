"""Finite owned stdio guard; SOURCE preparation, not an authorization daemon.

No code runs on import. One original Lease instance, one fresh check per CHECK.
The parent owns startup/queue/decision/cleanup clocks and child lifecycle.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys

GUARD_SHA = 'd396cde2829a230760d1ecd97c9f37fecedb7734082986181cf1a6c05122d5bf'
RUNTIME = ('/guard-python/bin/python3.11', 6809944, '9bee109da0dce17a7c9eeaca9f420cc6770a9fe143b9382d73bd22fe59b21a5f')
LOADER = ('/guard-python/lib/ld-linux-x86-64.so.2', 215000, '02bcda52c1a5dfc236f94d9e5255b4a0e26347d8a372a5223b650e31f291ce3c')
KEYS = {'schema','operation','instance','runId','leaseSha256','sequence','label','contextSha256'}


def need(ok, why):
    if not ok: raise ValueError(why)


def checked(path, count, digest):
    p = Path(path)
    need(p.is_absolute() and p.resolve(strict=True) == p, 'closed regular source path')
    first = p.lstat()
    need(stat.S_ISREG(first.st_mode) and first.st_size == count and count <= 8388608, 'bounded regular source')
    identity = lambda s: (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        need(identity(first) == identity(os.fstat(stream.fileno())), 'source descriptor changed')
        raw = stream.read(count + 1)
        need(identity(first) == identity(os.fstat(stream.fileno())), 'source descriptor drift')
    need(identity(first) == identity(p.lstat()) and len(raw) == count and hashlib.sha256(raw).hexdigest() == digest, 'source pin drift')
    return raw


def strict(raw):
    def pairs(items):
        out = {}
        for k,v in items:
            need(k not in out, 'duplicate key'); out[k] = v
        return out
    def integer(token):
        need(token != '-0', 'negative zero'); return int(token)
    return json.loads(raw.decode('utf-8',errors='strict'), object_pairs_hook=pairs,parse_int=integer,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError('fraction not allowed')),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite not allowed')))


def main(argv):
    need(len(argv) == 5 and argv[0] == '/input/guard-helper.py', 'fixed helper CLI')
    instance, expected, own_bytes, own_sha = argv[1:]
    need(re.fullmatch('[0-9a-f]{32}',instance) and re.fullmatch('[0-9a-f]{64}',expected)
        and re.fullmatch('[1-9][0-9]{0,6}',own_bytes) and re.fullmatch('[0-9a-f]{64}',own_sha), 'closed identity')
    need(sys.dont_write_bytecode and sys.flags.no_site and sys.flags.no_user_site and sys.flags.safe_path, 'isolated original runtime flags')
    own = ('/input/guard-helper.py', int(own_bytes), own_sha)
    checked(*own); checked(*RUNTIME); checked(*LOADER)
    guard_bytes = Path('/input/lease_guard.py').stat().st_size
    checked('/input/lease_guard.py', guard_bytes, GUARD_SHA)
    spec = importlib.util.spec_from_file_location('pinned_original_lease_guard','/input/lease_guard.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    lease = module.Lease('/session/lease.json',expected,'/session/control')
    raw = Path('/session/lease.json').read_bytes()
    need(len(raw) <= 8192 and hashlib.sha256(raw).hexdigest() == expected, 'original lease identity')
    original = strict(raw); run_id = original['runId']
    need(re.fullmatch('[0-9a-f]{32}',run_id), 'run identity')
    sequence = 0
    def revoke(reason):
        try: lease.revoke(reason)
        except BaseException: pass
    def interrupted(signum, _):
        revoke('owned guard helper interrupted'); raise SystemExit(124)
    signal.signal(signal.SIGTERM,interrupted); signal.signal(signal.SIGINT,interrupted)
    try:
        while True:
            raw = sys.stdin.buffer.readline(1025)
            need(raw and len(raw) <= 1024 and raw.endswith(b'\n'), 'bounded complete request/EOF')
            q = strict(raw)
            need(type(q) is dict and set(q) == KEYS and all(type(v) is str for v in q.values()), 'closed request')
            need(q['schema'] == 'e02-fresh-guard-request-v1' and q['operation'] in ('CHECK','CLOSE')
                and q['instance'] == instance and q['runId'] == run_id and q['leaseSha256'] == expected
                and q['sequence'] == str(sequence + 1) and sequence < 9007199254740990
                and re.fullmatch('[a-zA-Z0-9:_-]{1,160}',q['label'])
                and re.fullmatch('[0-9a-f]{64}',q['contextSha256']), 'request binding/order')
            sequence += 1
            checked(*own); checked('/input/lease_guard.py',guard_bytes,GUARD_SHA)
            if q['operation'] == 'CHECK':
                now = lease.check()  # Exact unchanged fresh core, ONE per CHECK.
                clocks = {k:str(now[k]) for k in ('Utc','Mono','Boot')}
                clocks['bootId'] = now['bootId']
            else: clocks = None
            reply = dict(schema='e02-fresh-guard-response-v1',operation=q['operation'],instance=instance,
                runId=run_id,leaseSha256=expected,sequence=q['sequence'],label=q['label'],
                contextSha256=q['contextSha256'],requestSha256=hashlib.sha256(raw).hexdigest(),ok=True,clocks=clocks)
            data = (json.dumps(reply,separators=(',',':'),ensure_ascii=True)+'\n').encode()
            need(len(data) <= 2048, 'bounded response')
            need(sys.stdout.buffer.write(data) == len(data), 'short response write');sys.stdout.buffer.flush()
            if q['operation'] == 'CLOSE': return 0
    except BaseException as error:
        revoke('owned guard helper failed: '+str(error)[:512]);raise


if __name__ == '__main__':
    try: result = main(sys.argv)
    except BaseException as error: sys.stderr.write(type(error).__name__+': '+str(error)[:1024]+'\n'); result = 124
    raise SystemExit(result)
