"""SOURCE ONLY. Whole frozen observations reconstructed from actual owned graphs.

No project import or target work at import. Runner injects its already admitted
fixed admission module as A; JSON never supplies a binding dictionary or function.
"""
import hashlib
import json
import os
from pathlib import Path
import stat

HERE=Path(__file__).resolve().parent
A=None
ENV={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TZ':'UTC',
     'WS_NO_BUFFER_UTIL':'1','WS_NO_UTF_8_VALIDATE':'1'}

def one_line(raw):
    A.need(type(raw) is bytes and len(raw)<=16777216 and raw.endswith(b'\n') and raw.count(b'\n')==1,'EXACT_ONE_JSONL')
    return A.loads(raw[:-1])

class Checker:
    def __init__(self,ctx):
        self.ctx=ctx
        self.defs=A.document(A.DATA['bridge-schemas.json'])['definitions']
        self.oracles=A.document(A.DATA['oracles.json'])
        self.selection=A.document(A.DATA['selection-map.json'])
        self.verified={};self.checked_cases=[]

    def selected_native_shape(self):
        selected=A.document(A.DATA['bridge-schemas.json'])['selectedCellNativeShapes']
        shape=selected[self.cell['cellId']]
        A.need(shape is not None,'N03_NO_NATIVE_SHAPE')
        return shape

    def raw(self,d):
        A.validate(d,'@descriptor',self.defs);p=Path(d['path'])
        A.need(p.is_relative_to(self.case) and p!=self.case,'OWNED_CASE_EVIDENCE_PATH')
        st=p.lstat();A.need(stat.S_IMODE(st.st_mode)==0o600 and st.st_uid==os.getuid(),'OWNED_0600_EVIDENCE')
        raw=A.checked(d);previous=self.verified.get(d['path']);A.need(previous is None or A.equal(previous,d),'IMMUTABLE_EVIDENCE_DESCRIPTOR')
        self.verified[d['path']]=d;return raw
    def doc(self,d,shape=None):
        value=A.loads(self.raw(d))
        if shape:A.validate(value,'@'+shape,self.defs)
        return value
    def common_spawn(self,d,kind,terminal):
        r=self.doc(d,'spawnReceipt');A.need(r['cellId']==self.cell['cellId'] and r['kind']==kind,'SAME_CASE_CHILD_KIND')
        A.need(A.equal(r['environment'],ENV),'EXACT_NATIVE_CHILD_ENV');life=r['lifecycle']
        if terminal:A.natural(life)
        else:
            A.need(life['launchAttempt'] is True and life['acquisition']=='ACQUIRED' and type(life['pid']) is int and life['pid']>0
                and life['exitCode'] is None and life['signal'] is None and life['reaped'] is False and life['stdoutEOF'] is False
                and life['stderrEOF'] is False and life['forced'] is False and life['timedOut'] is False and life['error'] is None,'LIVE_QUIESCENT_NATIVE_RECEIPT')
        A.need(self.raw(r['streams']['stderr'])==b'','EMPTY_NATIVE_STDERR')
        return r
    def receive(self,d,slot):
        r=self.doc(d,'receiveRecord');worker=self.worker;fixture_d=worker['dWire' if slot=='D' else 'fWire'];A.need(fixture_d is not None,'SELECTED_RECEIVE_SLOT');fixture=A.loads(A.checked(fixture_d))
        A.need(r['cellId']==self.cell['cellId'] and r['windowId']==self.cell['windowId'] and r['slot']==slot
            and r['subscription']=='nbdp-'+self.cell['cellId']+'-'+slot and r['outerId']==fixture['id'],'RECEIVE_ID_JOIN')
        spawn=self.common_spawn(r['spawn'],'WIRE_'+slot,True)
        A.need(A.equal(spawn['tool'],A.NODE) and spawn['cwd']==str(self.case/('wire-'+slot)),'WIRE_TOOL_CWD')
        binding_d=A.descriptor(self.case/('wire-'+slot)/'binding.json');binding=self.doc(binding_d,'wireBinding')
        A.need(A.equal(spawn['argv'],[A.NODE['path'],str(HERE/'wire.mjs'),binding_d['path'],binding_d['sha256']]),'FIXED_WIRE_COMMAND')
        A.need(binding['cellId']==self.cell['cellId'] and binding['slot']==slot and binding['relay']==self.cell['relay']
            and binding['outerId']==fixture['id'] and A.equal(binding['wire'],fixture_d)
            and A.equal(binding['closure'],self.ctx['sourceClosure']) and binding['output']==str(self.case/('wire-'+slot)/'output'),'WIRE_BINDING_JOIN')
        cli=one_line(self.raw(spawn['streams']['stdout']));A.validate(cli,'@wireCLIReply',self.defs)
        A.need(cli['qualified'] is True and cli['cellId']==r['cellId'] and cli['slot']==slot and A.equal(cli['report'],r['report']),'WIRE_CLI_JOIN')
        report=self.doc(r['report'],'wireReport');A.need(report['qualified'] is True and report['cellId']==r['cellId'] and report['slot']==slot
            and report['error'] is None and report['publicationCount']==report['queryCount']==report['eventCount']==1
            and A.equal(report['close'],{'code':1000,'reasonHex':''}),'WHOLE_WIRE_REPORT')
        sequence=[('SEND','EVENT'),('RECEIVE','ACK'),('SEND','REQ'),('RECEIVE','EVENT'),('RECEIVE','EOSE'),('SEND','CLOSE')]
        A.need(len(report['frames'])==6,'SIX_WIRE_FRAMES');raw_total=0;span=None
        for i,(direction,kind) in enumerate(sequence):
            frame=report['frames'][i];A.need(frame['direction']==direction and frame['kind']==kind,'WIRE_FRAME_ORDER')
            raw=bytes.fromhex(frame['rawHex']);raw_total+=len(raw);A.need(len(raw)<=262144 and raw_total<=2097152,'WIRE_RAW_BOUND');value=A.loads(raw)
            if i==0:A.need(raw==b'["EVENT",'+A.checked(fixture_d)+b']','EXACT_SIGNED_PUBLICATION_BYTES')
            elif i==1:A.need(type(value) is list and len(value)==4 and value[:3]==['OK',fixture['id'],True] and value[2] is True and type(value[3]) is str,'EXACT_TRUE_ACK')
            elif i==2:A.need(A.equal(value,['REQ',r['subscription'],{'ids':[fixture['id']],'limit':1}]),'EXACT_ID_QUERY')
            elif i==3:
                A.need(type(value) is list and len(value)==3 and value[:2]==['EVENT',r['subscription']] and A.equal(value[2],fixture),'EXACT_RECEIVED_TYPED_EVENT')
                text=raw.decode('utf-8');decoder=json.JSONDecoder();offset=1
                for _ in range(2):
                    while text[offset] in ' \t\r\n':offset+=1
                    _,offset=decoder.raw_decode(text,offset)
                    while text[offset] in ' \t\r\n':offset+=1
                    A.need(text[offset]==',','RAW_EVENT_SEPARATOR');offset+=1
                while text[offset] in ' \t\r\n':offset+=1
                _,end=decoder.raw_decode(text,offset);start_byte=len(text[:offset].encode());end_byte=len(text[:end].encode());span=raw[start_byte:end_byte]
                A.need(r['eventFrameIndex']==3 and r['spanStart']==start_byte and r['spanEnd']==end_byte
                    and self.raw(r['eventSpan'])==span and report['wireHex']==span.hex(),'ACTUAL_EVENT_RAW_SPAN')
            elif i==4:A.need(A.equal(value,['EOSE',r['subscription']]),'EXACT_EOSE')
            else:A.need(A.equal(value,['CLOSE',r['subscription']]),'EXACT_CLOSE_REQUEST')
        A.need(span is not None and self.raw(spawn['streams']['stdin'])==b'','WIRE_RAW_CUSTODY')
        self.receives[slot]=(d,r,span,spawn);return r
    def metadata(self,d):
        n=self.doc(d,'nativeCallRecord');A.need(n['cellId']==self.cell['cellId'] and n['windowId']==self.cell['windowId'] and n['backend']==self.cell['metadataBackend']
            and n['ordinal']==0 and n['replyObserved'] is True and n['channelAlive'] is True and n['pendingOutputBytes']==0 and n['terminalLifecycle'] is None,'WHOLE_NATIVE_CALL_RECORD')
        A.need(A.equal(n['dReceive'],self.receives['D'][0] if 'D' in self.receives else None) and A.equal(n['fReceive'],self.receives['F'][0]),'NATIVE_RECEIVE_BINDINGS')
        request_raw=self.raw(n['request']);request=one_line(request_raw);A.validate(request,'@nativeRequestN02' if self.cell['subprofileId']=='N02' else '@nativeRequestN16',self.defs)
        wanted={'op':'correlate-file-metadata','secretHex':self.worker['secretHex'],'config':self.worker['scope'],
                'dWireHex':self.receives['D'][2].hex() if 'D' in self.receives else None,'fWireHex':self.receives['F'][2].hex()}
        A.need(A.equal(request,wanted),'ACTUAL_REQUEST_SPAN_JOIN')
        reply_raw=self.raw(n['reply']);reply=one_line(reply_raw);A.validate(reply,self.selected_native_shape(),self.defs)
        expected=A.expected_native(self.cell['metadataBackend'],self.cell['subprofileId']=='N16');A.need(A.equal(reply,expected),'WHOLE_NATIVE_EXPECTED_REPLY')
        live=self.common_spawn(n['channelReceipt'],'METADATA',False)
        A.need(self.raw(live['streams']['stdin'])==request_raw and self.raw(live['streams']['stdout'])==reply_raw,'LIVE_NATIVE_PIPE_CAPTURE')
        if self.cell['metadataBackend']=='JS':
            A.need(A.equal(live['tool'],A.NODE),'JS_TOOL');bd=A.descriptor(self.case/'metadata'/'binding.json');binding=self.doc(bd,'nativeBinding')
            A.need(A.equal(live['argv'],[A.NODE['path'],str(HERE/'metadata_loader.mjs'),bd['path'],bd['sha256']]) and binding['cellId']==self.cell['cellId']
                and binding['windowId']==self.cell['windowId'] and A.equal(binding['scope'],self.worker['scope']) and A.equal(binding['closure'],self.ctx['sourceClosure'])
                and A.equal(binding['dFixture'],self.worker['dWire']) and A.equal(binding['fFixture'],self.worker['fWire']),'JS_NATIVE_BINDING_JOIN')
            A.member(A.closure(self.ctx['sourceClosure']),binding['metadataEntry'])
            A.need(binding['metadataEntry']['path']==str(HERE.parent/'e06_invoice_file_v1/js/metadata.mjs'),'FIXED_JS_METADATA_ENTRY')
            A.need(self.raw(A.descriptor(self.case/'metadata'/'native-reply.jsonl'))==reply_raw,'JS_RETAINED_REPLY_CUSTODY')
        else:A.need(A.equal(live['tool'],A.RUST) and A.equal(live['argv'],[A.RUST['path']]),'RUST_TOOL_COMMAND')
        A.need(live['cwd']==str(self.case/'metadata'),'NATIVE_CWD');self.native=(d,n,live,reply)
    def resolve(self,pattern,bindings):
        """Only twelve fixed typed names, recursively literal data; absent refuses."""
        if type(pattern) is dict:
            if 'bind' in pattern:
                A.closed(pattern,('bind',));name=pattern['bind']
                catalogue=A.document(A.DATA['bridge-schemas.json'])['bindingCatalogue']
                A.need(name in catalogue and name in bindings,'UNAVAILABLE_CHECKER_BINDING')
                value=bindings[name]
                A.validate(value,catalogue[name]['resolvedType'],self.defs)
                return value
            return {k:self.resolve(v,bindings) for k,v in pattern.items()}
        if type(pattern) is list:return [self.resolve(v,bindings) for v in pattern]
        return pattern

    def same_whole(self,actual,pattern,bindings,code):
        A.need(A.equal(actual,self.resolve(pattern,bindings)),code)

    def owned_outer(self,row):
        A.closed(row,('cellId','frame','qualified','outer','reply','comparison','error'))
        d=row['outer'];A.need(d is not None,'ACTUAL_OUTER_RECEIPT')
        # OwnedCase has a separate Python receipt shape; retain its complete bytes
        # and require acquired natural lifecycle before trusting any case reply.
        receipt=self.doc(d)
        A.closed(receipt,('schema','argv','cwd','environment','lifecycle','ownership','primaryError','secondaryErrors','secondaryOverflow','captureComplete','streams','observedBytes','retainedBytes','phaseMonitor'))
        A.need(receipt['schema']=='i4-python-owned-case-v2','BYTE_IDENTICAL_SUPERVISOR_RECEIPT_SCHEMA')
        A.natural(receipt['lifecycle'])
        A.need(receipt['captureComplete'] is True and receipt['primaryError'] is None,
               'COMPLETE_OUTER_CAPTURE')
        A.need(receipt['ownership']=='REAPED' and receipt['secondaryErrors']==[]
               and receipt['secondaryOverflow'] is False,'UNAMBIGUOUS_OUTER_OWNERSHIP')
        phase=receipt['phaseMonitor']
        A.need(phase['timeoutCause'] is None and phase['observations']==[]
          and all(v['startedNs'] is None and v['completedNs'] is None for v in phase['anchors'].values()),
          'NO_N_ACQUISITION_CONSUMER_PHASE_REINTERPRETATION')
        for name in ('stdout','stderr'):
            raw=self.raw(receipt['streams'][name])
            A.need(type(receipt['observedBytes'][name]) is int
              and receipt['observedBytes'][name]==receipt['retainedBytes'][name]==len(raw),'FULL_OUTER_BYTE_ACCOUNTING')
        return receipt

    def check_case(self,cell,row):
        """One exact cell, no retries/subsets, source-owned graphs then28whole checks."""
        self.cell=cell;ident=cell['cellId'];self.case=Path(self.ctx['output'])/ident
        self.worker=self.ctx['workers'][ident];self.receives={};self.native=None
        A.need(row['cellId']==ident and ident not in self.checked_cases,'EXACT_FRESH_CASE')
        outer=self.owned_outer(row);life=outer['lifecycle']
        A.need(type(life['pid']) is int and life['pid']>0,'ACTUAL_OWNED_CASE_PID')
        A.need(A.equal(outer['argv'],[A.NODE['path'],str(HERE/'case.mjs'),row['frame']['path'],row['frame']['sha256']])
          and A.equal(outer['environment'],ENV) and outer['cwd']==str(self.case/'outer-monitor'),
          'FIXED_CASE_COMMAND_ENV_CWD')
        A.need(self.raw(outer['streams']['stdin'])==b'' and self.raw(outer['streams']['stderr'])==b'',
               'CASE_RAW_STREAMS')
        cli=one_line(self.raw(outer['streams']['stdout']));A.validate(cli,'@caseCLIReply',self.defs)
        A.need(A.equal(cli,row['reply']),'ACTUAL_CASE_STDOUT_REPLY')
        frame=self.doc(row['frame'],'frame')
        A.need(frame['cellId']==ident and frame['windowId']==cell['windowId']
          and A.equal(frame['manifest'],self.ctx['manifestDescriptor'])
          and A.equal(frame['release'],self.ctx['releaseDescriptor'])
          and A.equal(frame['workerData'],self.ctx['manifest']['workerInputs'][ident])
          and frame['output']==str(self.case),'FRAME_ADMISSION_CELL_JOIN')
        wanted=next(c for c in self.oracles['cases'] if c['cellId']==ident)
        rows=[s for s in self.oracles['steps'] if s['cellId']==ident]
        ds=cli['stepRecords'];A.need(len(ds)==len(rows),'EXACT_SELECTED_STEP_COUNT')
        records=[]
        for d,rule in zip(ds,rows):
            A.need(d['path']==str(self.case/(rule['canonicalStepId']+'.json')),'FIXED_STEP_PATH_CELL_ORDER')
            records.append(self.doc(d,'step'))
        A.need([s['stepId'] for s in records]==wanted['expectedStepIds'],'EXACT_CANONICAL_STEP_ORDER')
        bindings={'CASE_PID':life['pid'],'STEP_RECORDS':ds,'FINAL_STEP_RECORD':ds[-1]}
        first=records[0]
        # Receive graph is derived from selected exact jobs, never arbitrary bindings.
        for job in cell['jobs']:
            slot=job['slot'];d=first['eventProvenance'][slot]
            A.need(d is not None,'SELECTED_RECEIVE_PRESENT');self.receive(d,slot)
            bindings['RECEIVED_'+slot]=d;bindings['WIRE_'+slot+'_RECEIPT']=self.receives[slot][1]['spawn']
        missing={'D','F'}-{j['slot'] for j in cell['jobs']}
        for slot in missing:A.need(first['eventProvenance'][slot] is None,'NO_UNSELECTED_RECEIVE')
        if cell['subprofileId']=='N03':
            A.need(first['metadataRecord'] is None and cli['metadataTerminal'] is None,'N03_NO_NATIVE_RECORD_OR_TERMINAL')
            # No native artifact directory may exist in this fresh source-owned case.
            A.need(not os.path.lexists(self.case/'metadata'),'N03_NO_NATIVE_ARTIFACTS')
        else:
            d=first['metadataRecord'];A.need(d is not None,'ACTUAL_NATIVE_CALL_REQUIRED')
            self.metadata(d);bindings['NATIVE_CALL']=d
            terminal=self.common_spawn(cli['metadataTerminal'],'METADATA',True);live=self.native[2]
            for key in ('tool','argv','cwd','environment'):
                A.need(A.equal(terminal[key],live[key]),'SAME_TERMINAL_NATIVE_CHILD')
            A.need(terminal['lifecycle']['pid']==live['lifecycle']['pid']
              and self.raw(terminal['streams']['stdin'])==self.raw(self.native[1]['request'])
              and self.raw(terminal['streams']['stdout'])==self.raw(self.native[1]['reply']),
              'NATURAL_TERMINAL_EXACT_ONE_NATIVE_REQUEST_REPLY')
            bindings['NATIVE_TERMINAL']=cli['metadataTerminal']
        if cell['subprofileId']=='N16':
            policy=records[1]['eligibility']['localPolicy'];refusal=records[2]['eligibility']['sealRefusal']
            A.need(policy is not None and refusal is not None,'ACTUAL_LOCAL_DENY_AND_SEAL_REFUSAL')
            bindings['LOCAL_POLICY']=policy;bindings['SEAL_REFUSAL']=refusal
            self.same_whole(self.doc(policy,'localPolicy'),wanted['expectedLocalPolicy'],bindings,'WHOLE_LOCAL_POLICY_AFTER_PAIRED_AUTH')
            self.same_whole(self.doc(refusal,'sealRefusal'),wanted['expectedSealRefusal'],bindings,'WHOLE_SPECIFIC_SEAL_REFUSAL')
        A.need(cli['terminal'] is not None,'ACTUAL_TERMINAL_RECORD');bindings['TERMINAL_RECORD']=cli['terminal']
        terminal=self.doc(cli['terminal'],'terminal')
        self.same_whole(terminal,rows[-1]['expectedTerminal'],bindings,'WHOLE_THIRTEEN_KEY_TERMINAL')
        for actual,rule in zip(records,rows):
            self.same_whole(actual,rule['expectedWhole'],bindings,'WHOLE_TWENTY_THREE_KEY_STEP')
            # Count facts independently reconstructed from actual wire/native graphs.
            counts=actual['counts'];A.need(type(counts) is dict,'COUNTS_NOT_UNKNOWN')
            jobs=len(self.receives);native=0 if self.native is None else 1
            expected=dict(cell['completedStepCounts'])
            A.need(expected['publications']==expected['queries']==expected['events']==jobs
              and expected['metadataRequests']==expected['metadataReplies']==native,
              'COUNTERS_ACTUAL_GRAPH_JOIN')
            if self.native is not None:
                reply=self.native[3]
                A.need(expected['dValidations']==reply['validationCallCounts']['D']
                  and expected['fValidations']==reply['validationCallCounts']['F'],'NATIVE_VALIDATION_COUNT_JOIN')
            A.qualified_counts(counts,expected)
        self.same_whole(cli,wanted['expectedCaseReply'],bindings,'WHOLE_TWELVE_KEY_CASE_REPLY')
        for descriptor in self.verified.values():A.checked(descriptor)
        self.checked_cases.append(ident)
        return dict(matched=True,scope='EXACT_N02_N03_N16_SELECTED_CELL_ONLY',cellId=ident,
          stepRecords=ds,verifiedEvidence=list(self.verified.values()))

    def check_run(self,capture):
        A.need(self.checked_cases==self.selection['orderedCells'],'EXACT_TEN_SERIAL_CELLS')
        A.need([r['cellId'] for r in capture['cases']]==self.selection['orderedCells']
          and all(r['qualified'] is True and r['error'] is None for r in capture['cases'])
          and capture['notExecuted']==[],'COMPLETE_TEN_CASE_RUN')
        A.need(sum(len(r['reply']['stepRecords']) for r in capture['cases'])==28,'EXACT_TWENTY_EIGHT_STEPS')
        A.need(capture['labCleanup'] is not None,'OWNED_LAB_CLEANUP_REQUIRED')
        cleanup=A.document(capture['labCleanup'])
        A.need(cleanup['qualified'] is True and cleanup['problems']==[] and cleanup['uncertain_creates']==[],
               'ACTUAL_OWNED_LAB_CLEANUP')
        A.need(capture['finalIntegrity'] is True and capture['errors']==[],'FINAL_CURRENT_QUALIFIED_RUN')
        return dict(matched=True,scope='LAB_N_02_03_16_ONLY',cells=10,wholeSteps=28,wireJobs=14,
          nativeRequests=8,acquisitionConnections=0,consumerAttempts=0,publicReleases=0)
