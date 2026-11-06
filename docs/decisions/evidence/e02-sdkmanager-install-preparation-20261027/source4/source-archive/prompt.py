"""DRAFT: expected-only AOSP mapping and a literal, single-use stdout prompt gate."""
import codecs
import hashlib
import re
import xml.etree.ElementTree as ET

RAW_BYTES=16962
RAW_SHA='1f8729233617b193fd619213792ae16a41b95d2bbbf525dfe66998252ba68b16'
LICENSE='android-sdk-license'
RULE='---------------------------------------'
QUESTION='Accept? (y/N): '


def need(ok,why):
    if not ok:raise ValueError(why)


def expected_only_java_mapping(value):
    # Java default Pattern \\s is ASCII unless UNICODE_CHARACTER_CLASS is set.
    # Java String.trim removes code units <=U+0020, unlike Python str.strip.
    value=re.sub(r'(?<=\s)[ \t]*','',value,flags=re.ASCII)
    value=re.sub(r'(?<!\n)\n(?!\n)',' ',value)
    value=re.sub(' +',' ',value)
    return re.sub(r'^[\x00-\x20]+|[\x00-\x20]+$','',value)


def approved_from_xml(raw):
    need(type(raw) is bytes and len(raw)<=1048576,'BOUNDED_PRIMARY_XML')
    root=ET.fromstring(raw)
    matches=[n for n in root.iter() if n.tag.rsplit('}',1)[-1]=='license' and n.attrib.get('id')==LICENSE]
    need(len(matches)==1 and len(matches[0])==0,'ONE_TEXT_LICENSE')
    value=matches[0].text;need(type(value) is str,'LICENSE_TEXT')
    encoded=value.encode('utf-8')
    need(len(encoded)==RAW_BYTES and hashlib.sha256(encoded).hexdigest()==RAW_SHA,'EXACT_APPROVED_RAW_XML_LICENSE')
    return value,expected_only_java_mapping(value)


class Prompt:
    """Only CRLF framing normalization is permitted on observed output.

    There is no observed-text TrimStringAdapter, whitespace collapse, reflow,
    ANSI stripping, case folding or general prompt auto-answer mechanism.
    """
    def __init__(self,expected):
        need(type(expected) is str and 0<len(expected.encode())<=65536,'EXPECTED_BODY_BOUND')
        self.expected=expected;self.frame='License '+LICENSE+':\n'+RULE+'\n'+expected+'\n'+RULE+'\n'+QUESTION
        self.decoder=codecs.getincrementaldecoder('utf-8')('strict')
        self.text='';self.ready=False;self.attempted=False;self.sent=False

    def feed(self,raw,final=False):
        need(type(raw) is bytes,'RAW_UTF8_BYTES')
        self.text+=self.decoder.decode(raw,final=final)
        need(len(self.text.encode())<=16777216,'PROMPT_OUTPUT_BOUND')
        text=self.text.replace('\r\n','\n')
        if not final and text.endswith('\r'):text=text[:-1] # Wait for split CRLF.
        headers=list(re.finditer(r'(?:\A|(?<=\n))License ([^:\r\n]{1,128}):\n',text))
        need(len(headers)<=1,'REPEATED_LICENSE_HEADER')
        if not headers:
            need('Accept?' not in text,'QUESTION_WITHOUT_EXACT_LICENSE_FRAME')
            if final:raise ValueError('NO_COMPLETE_APPROVED_PROMPT')
            return False
        header=headers[0];need(header.group(1)==LICENSE,'OTHER_LICENSE')
        prefix=text[:header.start()]
        need('Accept?' not in prefix and not re.search(r'(?:\A|\n)License ',prefix), 'RESERVED_PROMPT_MATERIAL_BEFORE_APPROVED_HEADER')
        observed=text[header.start():]
        need(observed[:len(self.frame)]==self.frame[:len(observed[:len(self.frame)])],'CHANGED_LICENSE_BODY_OR_FRAMING')
        tail=observed[len(self.frame):] if len(observed)>=len(self.frame) else ''
        need('Accept?' not in tail and not re.search(r'(?:\A|\n)License ',tail),'REPEATED_OR_OTHER_PROMPT')
        if len(observed)>=len(self.frame):self.ready=True
        if final:
            need(self.ready and self.attempted,'INCOMPLETE_OR_UNANSWERED_PROMPT')
            last=tail.rsplit('\n',1)[-1]
            need(not last or not any(token.startswith(last) for token in ('License ',QUESTION)), 'INCOMPLETE_REPEATED_PROMPT')
        return self.ready and not self.attempted

    def mark_attempted(self):
        need(self.ready and not self.attempted,'ONE_GLOBAL_AFFIRMATIVE_ONLY')
        self.attempted=True

    def mark_sent(self):
        need(self.attempted and not self.sent,'ONE_SENT_RECORD_ONLY');self.sent=True


def reject_stderr_prompt(text):
    need('Accept?' not in text and not re.search(r'(?:\A|\n)License [^:\n]{1,128}:',text),'UNEXPECTED_STDERR_PROMPT')


def initial_consent():
    return dict(affirmativeAttempted=False,attemptJournalCommitted=False,stdinWriteInvoked=False,
        writeReturnedBytes=None,flushReturned=False,sent=False,sentJournalCommitted=False)


def dispatch_once(gate,state,journal,write,flush,close):
    """Fixed y\n only, with durable intent before invocation; never retry."""
    gate.mark_attempted();state['affirmativeAttempted']=True
    identity=dict(expectedDisplaySha256=hashlib.sha256(gate.expected.encode()).hexdigest(),approvedRawSha256=RAW_SHA)
    journal('consent-attempted.json',dict(identity,affirmativeAttempted=True,stdinWriteInvoked=False,answerBytes=2))
    state['attemptJournalCommitted']=True;state['stdinWriteInvoked']=True
    state['writeReturnedBytes']=write(b'y\n');need(state['writeReturnedBytes']==2,'SHORT_CONSENT_WRITE')
    flush();state['flushReturned']=True;gate.mark_sent();state['sent']=True
    journal('consent-sent.json',dict(identity,affirmativeAttempted=True,stdinWriteInvoked=True,writeReturnedBytes=2,flushReturned=True,consumption='UNKNOWN'))
    state['sentJournalCommitted']=True;close()
