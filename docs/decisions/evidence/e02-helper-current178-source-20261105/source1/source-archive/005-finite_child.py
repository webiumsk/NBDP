"""Narrow adaptation of capture46 retained-unreaped Popen ownership.

No subprocess on import. One absolute run deadline and one bounded reap deadline;
actual pipe EOF only. Target55 replaces historical60, output limits are explicit.
"""
import os
import selectors
import signal
import subprocess
import time

NS = 1_000_000_000


def need(ok, message):
    if not ok:
        raise ValueError(message)


def signal_owned_group(child, owned):
    need(owned['retainedPopen'] is True and owned['startNewSession'] is True and
         owned['pid'] == owned['pgid'] == owned['sid'] == child.pid and child.returncode is None,
         'RETAINED_UNREAPED_OWNED_GROUP')
    try:
        os.killpg(owned['pgid'], signal.SIGKILL)
        return {'signal': 'SIGKILL', 'group': owned['pgid'], 'status': 'SIGNALLED_BEFORE_REAP'}
    except ProcessLookupError:
        return {'signal': 'SIGKILL', 'group': owned['pgid'], 'status': 'GROUP_ABSENT_BEFORE_REAP'}


def capture(argv, *, run_ns, ends, check, finish_check, capture, target, ordinal,
            environment, cwd, popen=subprocess.Popen, selector=selectors.DefaultSelector,
            mono=time.monotonic_ns, read=os.read, getpgid=os.getpgid, getsid=os.getsid,
            signal_group=signal_owned_group, set_blocking=os.set_blocking):
    """Injected OS calls permit controls against this exact production function.

    A forced pipe close never becomes EOF. No poll()/wait() before fault signaling.
    stdout/stderr retained once, with no Docker logs duplication.
    """
    check()
    child = None
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    eof = {'stdout': False, 'stderr': False}
    caps = {'stdout': 8_384_512 if target else 262_144, 'stderr': 4096}
    fault = closure = None
    code = None
    reaped = False
    start = mono()
    # check returns remaining of the earliest UTC/MONO/BOOT absolute fence.
    # Reserve3 belongs to the same caller phase, never another relative lease.
    job_end = start + min(run_ns, check() - 3 * NS)
    need(job_end > start, 'NO_BOUNDED_RUN')
    sel = selector()  # Selector failure precedes spawn.
    owned = {'retainedPopen': True, 'startNewSession': True, 'pid': None, 'pgid': None, 'sid': None}
    try:
        check()  # Immediately before actual Popen; no proof callback between.
        need(mono() < job_end, 'STARTUP_INSIDE_ORIGINAL_RUN_DEADLINE')
        child = popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE, cwd=cwd, env=environment, start_new_session=True)
        owned.update(pid=child.pid, pgid=getpgid(child.pid), sid=getsid(child.pid))
        need(owned['pid'] == owned['pgid'] == owned['sid'], 'ACTUAL_SESSION_GROUP')
        for name, pipe in (('stdout', child.stdout), ('stderr', child.stderr)):
            set_blocking(pipe.fileno(), False)
            sel.register(pipe, selectors.EVENT_READ, name)
        while sel.get_map():
            check()
            need(mono() < job_end, 'CHILD_RUN_DEADLINE')
            for key, _ in sel.select(min(.05, max(0, (job_end - mono()) / NS))):
                check()
                need(mono() < job_end, 'CHILD_RUN_DEADLINE')
                block = read(key.fd, 8192)
                name = key.data
                if not block:
                    sel.unregister(key.fileobj)
                    eof[name] = True
                    continue
                need(len(buffers[name]) + len(block) <= caps[name], 'CAPTURE_STREAM_LIMIT')
                buffers[name].extend(block)
    except BaseException as error:
        fault = error
    finally:
        if child is not None:
            # A single absolute3 interval, clamped to original phase remaining.
            # On lease failure cleanup is still bounded by caller phase clocks;
            # caller check may deny; then no extra wait budget is invented.
            now = mono()
            reap_end = min(job_end + 3 * NS, now + 3 * NS)
            try:
                reap_end = min(reap_end, now + finish_check())
            except BaseException as error:
                fault = fault or error
                reap_end = now
            if fault is not None:
                try:
                    need(mono() < reap_end and finish_check() > 0, 'NO_LATE_GROUP_SIGNAL')
                    closure = signal_group(child, owned)
                except BaseException as error:
                    fault = fault or error
            try:
                code = child.wait(timeout=max(0, (reap_end - mono()) / NS))
                reaped = True
            except BaseException as error:
                fault = fault or error
                if closure is None and mono() < reap_end:
                    try:
                        need(finish_check() > 0, 'NO_LATE_GROUP_SIGNAL')
                        closure = signal_group(child, owned)
                    except BaseException as extra:
                        fault = fault or extra
                try:
                    code = child.wait(timeout=max(0, (reap_end - mono()) / NS))
                    reaped = True
                except BaseException as extra:
                    fault = fault or extra
            for pipe in (child.stdout, child.stderr):
                try:
                    pipe.close()
                except BaseException as error:
                    fault = fault or error
        try:
            sel.close()
        except BaseException as error:
            fault = fault or error
    raw = {name: bytes(value) for name, value in buffers.items()}
    for name in ('stdout', 'stderr'):
        capture(name, raw[name])  # One intended physical copy each, precharged.
    return {'code': code, 'fault': None if fault is None else str(fault), 'reaped': reaped,
            'stdoutEOF': eof['stdout'], 'stderrEOF': eof['stderr'], 'groupClosure': closure,
            'ownership': owned, 'elapsedNs': mono() - start, 'reapDeadlineMonoNs': reap_end if child else None,
            'stdout': raw['stdout'], 'stderr': raw['stderr']}
