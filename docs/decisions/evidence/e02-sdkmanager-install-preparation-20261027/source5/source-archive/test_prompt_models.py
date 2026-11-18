"""DEFINED ONLY: synthetic prompt and single-write failure models; no real consent."""
from pathlib import Path
import sys
import hashlib
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prompt as p

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


if __name__=='__main__':unittest.main(verbosity=2)
