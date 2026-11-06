"""DEFINED ONLY: synthetic prompt and single-write failure models; no real consent."""
from pathlib import Path
import sys
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


if __name__=='__main__':unittest.main(verbosity=2)
