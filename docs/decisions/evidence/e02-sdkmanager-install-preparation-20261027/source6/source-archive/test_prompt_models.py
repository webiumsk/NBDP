"""DEFINED ONLY: synthetic prompt and single-write failure models; no real consent."""
from pathlib import Path
import sys
import hashlib
import errno
import tempfile
import stat
from types import SimpleNamespace
from unittest.mock import patch
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prompt as p
import install as installer

BODY='SYNTHETIC approved body \u20ac\n\nSecond paragraph.'


def gate():return p.Prompt(BODY)


def ready():
    value=gate();value.feed(value.frame.encode());return value


class PromptModels(unittest.TestCase):
    def test_expected_only_java_ascii_mapping(self):
        self.assertEqual(p.expected_only_java_mapping('\t A  \n B\n\nC \t '),'A B\n\nC')
        self.assertEqual(p.expected_only_java_mapping('\u00a0 A \u00a0'),'\u00a0 A \u00a0')

    def test_fragmented_utf8_and_crlf_wait_for_complete_exact_question(self):
        value=gate();raw=value.frame.replace('\n','\r\n').encode()
        for byte in raw[:-1]:self.assertFalse(value.feed(bytes([byte])))
        self.assertTrue(value.feed(raw[-1:]));value.mark_attempted();value.mark_sent();value.feed(b'',final=True)

    def test_changed_observed_whitespace_or_body_is_never_normalized(self):
        for body in (BODY.replace('approved','changed'),BODY.replace(' body','  body'),BODY.replace('\n\n','\n')):
            value=gate()
            with self.assertRaises(ValueError):value.feed(value.frame.replace(BODY,body).encode())

    def test_other_license_and_question_without_frame_refused(self):
        for raw in (gate().frame.replace('android-sdk-license','other-license').encode(),b'Accept? (y/N): '):
            with self.assertRaises(ValueError):gate().feed(raw)

    def test_incomplete_frame_or_utf8_at_eof_refused(self):
        value=gate();value.feed(value.frame[:-1].encode())
        with self.assertRaises(ValueError):value.feed(b'',final=True)
        value=gate();value.feed(b'prefix \xe2')
        with self.assertRaises(UnicodeDecodeError):value.feed(b'',final=True)

    def test_repeated_and_stderr_prompts_refused(self):
        value=ready();value.mark_attempted()
        with self.assertRaises(ValueError):value.feed(('\n'+value.frame).encode())
        with self.assertRaises(ValueError):p.reject_stderr_prompt('License android-sdk-license:\n')
        with self.assertRaises(ValueError):p.reject_stderr_prompt('Accept? (y/N): ')

    def test_one_fixed_yes_after_durable_intent_and_flush(self):
        value=ready();state=p.initial_consent();calls=[]
        def journal(name,data):calls.append(('journal',name));self.assertTrue(state['affirmativeAttempted'])
        def write(raw):calls.append(('write',raw));self.assertTrue(state['attemptJournalCommitted']);return len(raw)
        p.dispatch_once(value,state,journal,write,lambda:calls.append('flush'),lambda:calls.append('close'))
        self.assertEqual(calls,[('journal','consent-attempted.json'),('write',b'y\n'),'flush',('journal','consent-sent.json'),'close'])
        self.assertTrue(state['sentJournalCommitted'])
        with self.assertRaises(ValueError):p.dispatch_once(value,state,journal,write,lambda:None,lambda:None)

    def test_failed_intent_journal_never_calls_stdin(self):
        value=ready();state=p.initial_consent();writes=[]
        def fail(*args):raise OSError('SYNTHETIC_DISK_FAILURE')
        with self.assertRaises(OSError):p.dispatch_once(value,state,fail,lambda raw:writes.append(raw),lambda:None,lambda:None)
        self.assertTrue(state['affirmativeAttempted']);self.assertFalse(state['stdinWriteInvoked']);self.assertEqual(writes,[])

    def test_partial_write_preserves_attempt_and_unknown_consumption(self):
        value=ready();state=p.initial_consent()
        with self.assertRaises(ValueError):p.dispatch_once(value,state,lambda *a:None,lambda raw:1,lambda:None,lambda:None)
        self.assertTrue(state['stdinWriteInvoked']);self.assertEqual(state['writeReturnedBytes'],1);self.assertFalse(state['sent'])
        with self.assertRaises(ValueError):value.mark_attempted()

    def test_failed_flush_never_reports_sent_or_allows_retry(self):
        value=ready();state=p.initial_consent()
        def fail():raise BrokenPipeError('SYNTHETIC_FLUSH_FAILURE')
        with self.assertRaises(BrokenPipeError):p.dispatch_once(value,state,lambda *a:None,lambda raw:2,fail,lambda:None)
        self.assertTrue(state['stdinWriteInvoked']);self.assertFalse(state['flushReturned']);self.assertFalse(state['sent'])
        with self.assertRaises(ValueError):value.mark_attempted()

    def test_failed_sent_journal_keeps_actual_flush_fact_separate(self):
        value=ready();state=p.initial_consent()
        def journal(name,data):
            if name=='consent-sent.json':raise OSError('SYNTHETIC_SENT_RECEIPT_FAILURE')
        with self.assertRaises(OSError):p.dispatch_once(value,state,journal,lambda raw:2,lambda:None,lambda:None)
        self.assertTrue(state['flushReturned']);self.assertTrue(state['sent']);self.assertFalse(state['sentJournalCommitted'])

    def test_reserved_prefix_coalesced_or_split_refuses_before_any_write(self):
        # Same logical bytes must refuse regardless of transport chunk boundaries.
        for prefix in (b'Accept? (y/N): \n',b'License other-license without-colon\n'):
            raw=prefix+gate().frame.encode()
            for split in range(len(raw)+1):
                value=gate();state=p.initial_consent();writes=[]
                def consume():
                    for chunk in (raw[:split],raw[split:]):
                        if value.feed(chunk):
                            p.dispatch_once(value,state,lambda *a:None,lambda data:(writes.append(data) or len(data)),lambda:None,lambda:None)
                with self.subTest(prefix=prefix,split=split),self.assertRaises(ValueError):consume()
                self.assertEqual(writes,[]);self.assertFalse(state['stdinWriteInvoked'])
                self.assertFalse(value.attempted)

    def test_legitimate_progress_prefix_keeps_fragmented_prompt_positive(self):
        value=gate();raw=b'Loading local repository...\rLoading remote repository...\nPreparing packages...\n'+value.frame.encode()
        for byte in raw[:-1]:self.assertFalse(value.feed(bytes([byte])))
        self.assertTrue(value.feed(raw[-1:]));writes=[];state=p.initial_consent()
        p.dispatch_once(value,state,lambda *a:None,lambda data:(writes.append(data) or len(data)),lambda:None,lambda:None)
        self.assertEqual(writes,[b'y\n']);self.assertTrue(state['sentJournalCommitted'])

    def test_actual_sdkmanager_cr_progress_frame_at_critical_splits(self):
        raw=Path(__file__).with_name('actual-sdkmanager-prompt.stdout').read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(18138,'e495bf2922648f84575498e921868128e5a624ae7dd779a32736bddea487c342'))
        approved=Path('/tmp/nbdp-e02-sdk-install-controller-20261027/input-bundle-r1/approved-license.txt').read_bytes()
        self.assertEqual((len(approved),hashlib.sha256(approved).hexdigest()),(p.RAW_BYTES,p.RAW_SHA))
        expected=p.expected_only_java_mapping(approved.decode('utf-8'))
        self.assertEqual((len(expected.encode()),hashlib.sha256(expected.encode()).hexdigest()),
            (16960,'aaf80cd0aee7e569ffa8a4be1b61189c0fefccf23068e38dfafe336289b8c723'))
        header=raw.index(b'License android-sdk-license:');self.assertEqual(raw[header-1],13)
        question=raw.index(p.QUESTION.encode());self.assertEqual(question+len(p.QUESTION.encode()),len(raw))
        cuts={0,1,header-1,header,header+1,raw.index(b'\n',header)+1,question-1,question,question+1,len(raw)-1,len(raw)}
        for i,byte in enumerate(raw):
            if byte>=128:cuts.add(i+1);break
        for split in sorted(cuts):
            with self.subTest(split=split):
                value=p.Prompt(expected);state=p.initial_consent();writes=[];seen=0
                for chunk in (raw[:split],raw[split:]):
                    seen+=len(chunk);ready_to_write=value.feed(chunk)
                    if seen<len(raw):self.assertFalse(ready_to_write)
                    if ready_to_write:p.dispatch_once(value,state,lambda *a:None,lambda data:(writes.append(data) or len(data)),lambda:None,lambda:None)
                self.assertEqual(writes,[b'y\n']);self.assertTrue(state['sentJournalCommitted']);value.feed(b'',final=True)

    def test_cr_reserved_prefixes_refuse_before_write_and_body_cr_is_literal(self):
        for prefix in (b'Accept? (y/N): \r',b'License other-license malformed\r'):
            raw=prefix+gate().frame.encode()
            for split in range(len(raw)+1):
                value=gate();state=p.initial_consent();writes=[]
                def consume():
                    for chunk in (raw[:split],raw[split:]):
                        if value.feed(chunk):p.dispatch_once(value,state,lambda *a:None,lambda data:(writes.append(data) or len(data)),lambda:None,lambda:None)
                with self.subTest(prefix=prefix,split=split),self.assertRaises(ValueError):consume()
                self.assertEqual(writes,[]);self.assertFalse(state['stdinWriteInvoked'])
        value=gate()
        with self.assertRaises(ValueError):value.feed(value.frame.replace(BODY,BODY.replace('approved','ap\rproved')).encode())
        value=gate()
        with self.assertRaises(ValueError):value.feed((value.frame+'\rLicense other-license malformed').encode())
        with self.assertRaises(ValueError):p.reject_stderr_prompt('progress\rLicense other-license:')

    def test_live_enumerated_rename_races_are_recorded_for_lstat_and_scandir(self):
        for operation in ('lstat','scandir'):
            with self.subTest(operation=operation),tempfile.TemporaryDirectory(prefix='nbdp-sdk-live-sample-') as folder:
                roots=[Path(folder)/name for name in ('sdk','user','output')]
                for root in roots:root.mkdir()
                victim=roots[0]/'moving'
                if operation=='lstat':victim.write_bytes(b'SYNTHETIC')
                else:victim.mkdir()
                def walk(root,followlinks=False,onerror=None):
                    if root==roots[0]:
                        if operation=='lstat':
                            names=['moving'];victim.rename(roots[0]/'moved');yield str(root),[],names
                        else:
                            yield str(root),['moving'],[]
                            victim.rename(roots[0]/'moved')
                            onerror(FileNotFoundError(errno.ENOENT,'SYNTHETIC_RENAME',str(victim)))
                    else:yield str(root),[],[]
                observed=installer.sampling_observations()
                with patch.object(installer,'SDK',roots[0]),patch.object(installer,'USER',roots[1]),patch.object(installer,'OUTPUT',roots[2]),patch.object(installer.os,'walk',walk):
                    result=installer.usage(live=True,observations=observed)
                self.assertEqual(result['vanishedInThisSample'],1);self.assertTrue(result['samplingIncomplete'])
                self.assertEqual(observed['vanishedCount'],1);self.assertEqual(observed['examples'][0]['operation'],operation)
                self.assertEqual(observed['examples'][0]['path'],'moving');self.assertTrue(observed['samplingIncomplete'])

    def test_quiescent_races_and_live_non_enoent_or_root_errors_remain_fatal(self):
        for operation,error_number,live in (('lstat',errno.ENOENT,False),('scandir',errno.ENOENT,False),
                ('lstat',errno.EACCES,True),('lstat',errno.EIO,True),('scandir',errno.EACCES,True),('scandir',errno.EIO,True),('root',errno.ENOENT,True)):
            with self.subTest(operation=operation,error=error_number,live=live),tempfile.TemporaryDirectory(prefix='nbdp-sdk-strict-sample-') as folder:
                roots=[Path(folder)/name for name in ('sdk','user','output')]
                for root in roots:root.mkdir()
                victim=roots[0]/'moving'
                if operation=='lstat':victim.write_bytes(b'SYNTHETIC')
                else:victim.mkdir()
                original_lstat=Path.lstat
                def stat_path(path,*args,**kwargs):
                    if path==victim and operation=='lstat':
                        if error_number==errno.ENOENT:victim.rename(roots[0]/'moved')
                        raise OSError(error_number,'SYNTHETIC_STAT_FAILURE',str(path))
                    return original_lstat(path,*args,**kwargs)
                def walk(root,followlinks=False,onerror=None):
                    if root==roots[0]:
                        if operation=='root':onerror(FileNotFoundError(errno.ENOENT,'SYNTHETIC_ROOT_ERROR',str(root)))
                        yield str(root),([] if operation=='lstat' else ['moving']),(['moving'] if operation=='lstat' else [])
                        if operation=='scandir':
                            if error_number==errno.ENOENT:victim.rename(roots[0]/'moved')
                            onerror(OSError(error_number,'SYNTHETIC_TRAVERSAL_FAILURE',str(victim)))
                    else:yield str(root),[],[]
                observed=installer.sampling_observations()
                with patch.object(installer,'SDK',roots[0]),patch.object(installer,'USER',roots[1]),patch.object(installer,'OUTPUT',roots[2]),patch.object(installer.os,'walk',walk),patch.object(Path,'lstat',stat_path),self.assertRaises(OSError):
                    installer.usage(live=live,observations=observed)
                self.assertEqual(observed['vanishedCount'],0);self.assertFalse(observed['samplingIncomplete'])

        # Bounded synthetic stat rows exercise unchanged8GiB/200000 checks using
        # tiny patched thresholds; no large tree, archive or resource workload.
        for guard in ('members','bytes'):
            with self.subTest(guard=guard),tempfile.TemporaryDirectory(prefix='nbdp-sdk-sampling-cap-') as folder:
                roots=[Path(folder)/name for name in ('sdk','user','output')]
                for root in roots:root.mkdir()
                def walk(root,followlinks=False,onerror=None):yield str(root),[],(['a','b','c'] if root==roots[0] else [])
                def row(path,*args,**kwargs):return SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_size=9 if guard=='bytes' else 0)
                with patch.object(installer,'SDK',roots[0]),patch.object(installer,'USER',roots[1]),patch.object(installer,'OUTPUT',roots[2]),patch.object(installer.os,'walk',walk),patch.object(Path,'lstat',row),patch.object(installer,'TREE_MEMBER_CAP',2 if guard=='members' else 200000),patch.object(installer,'TREE_BYTE_CAP',8 if guard=='bytes' else 8589934592),self.assertRaises(ValueError):
                    installer.usage(live=True,observations=installer.sampling_observations())


if __name__=='__main__':unittest.main(verbosity=2)
