"""Pure HISTORY_PREFIX framing/validation. No filesystem, tool or API calls.

Actual-request7 qualification is supplied by this versioned peer qualification.py.
Actual Root platform custody/authenticity and permanent runId quarantine remain
external authority; this module never invents an F response or IO durability.
"""
import base64,hashlib,json,math,re,struct,zlib
import qualification as q
MAGIC=b'NBDP-HISTORY-PREFIX\x00\x01'
HEADER_MAX=2048
RESTORED_MAX=16777216
PHYSICAL_MAX=49152
HEADER_SCHEMA='e02-root-history-prefix-header-v1'
BODY_SCHEMA='e02-root-collector-history-prefix-v1'
SOURCE_PATH='/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-collector-current-policy-20261105/source2/source-subject.json'
FINAL_NAME='history-prefix.bin'

def need(v,m):
 if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_HISTORY_FIELDS')
def encoded(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def source_pin(d):
 q.pin(d,RESTORED_MAX);need(d['path']==SOURCE_PATH and d['bytes']>0,'EXACT_CURRENT_REQUEST7_COMPOSITE_SUBJECT')
def run_id(run):need(type(run) is str and re.fullmatch('[0-9a-f]{32}',run),'EXACT_RUN')
def final_path(run):run_id(run);return q.DATA_PARENT+'/'+run+'/diagnostic--'+FINAL_NAME

def strict(raw,floats=False):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_HISTORY_KEY');out[k]=v
  return out
 def number(s):
  need(floats,'NO_HEADER_FLOAT');v=float(s);need(math.isfinite(v),'FINITE_API_NUMBER');return v
 def reject(_):raise ValueError('NONFINITE_HISTORY_NUMBER')
 value=json.loads(raw.decode('utf8','strict'),object_pairs_hook=pairs,parse_float=number,parse_constant=reject)
 nodes=0
 def walk(v,depth=0):
  nonlocal nodes
  nodes+=1;need(depth<=64 and nodes<=250000,'BOUNDED_HISTORY_STRUCTURE')
  if type(v) is dict:
   for x in v.values():walk(x,depth+1)
  elif type(v) is list:
   for x in v:walk(x,depth+1)
 walk(value);need(encoded(value)==raw,'EXACT_CANONICAL_HISTORY_JSON');return value

def validate_prefix(value,run,source):
 run_id(run);source_pin(source);closed(value,'schema runId collectorSource expectedCommands origins')
 need(value['schema']==BODY_SCHEMA and value['runId']==run and value['collectorSource']==source,'EXACT_PREFIX_PURPOSE_RUN_SOURCE')
 commands=value['expectedCommands'];origins=value['origins'];need(type(commands) is list and 1<=len(commands)<=127 and type(origins) is list and len(origins)==len(commands),'FINITE_COMPLETE_PREFIX')
 target=final_path(run)
 for row,origin in zip(commands,origins):
  closed(row,'request requestPin expectedProof');words,_route=q.command_words(row['request']);op=q.command(row['request'],run)
  need(not (op=='record' and words[7:11]==['--kind','diagnostic','--name',FINAL_NAME]),'FINAL_F_COMMAND_FORBIDDEN_IN_PREFIX')
  need(row['expectedProof'] is None or row['expectedProof'].get('path')!=target,'FINAL_F_PROOF_FORBIDDEN_IN_PREFIX')
  if op=='record' and len(words)==13 and words[11]=='--input-base64':
   raw_control=q.decode_input(words[12],PHYSICAL_MAX)
   need(target.encode() not in raw_control,'NO_FINAL_F_PIN_IN_PRE_F_OPERATIONAL_CONTROL')
  # Exact actualArguments/request equality, stores/order/counters and complete
  # successful API custody are checked by this exact7 qualifier, not a parallel oracle.
 plan=dict(schema='e02-root-collector-approved-command-sequence-v1',runId=run,collectorScript=q.SCRIPT_PIN,commands=commands)
 result=q.RootFailstop(run_id=run).evaluate(plan,origins)
 need(result['collectorCommandsQualified'] is True and result['fixtureOnly'] is False,'CURRENT_PREFIX_ROOT_CUSTODY_FAILED')
 return value

def freeze_prefix(value,run,source,remaining_payload_bytes):
 need(type(remaining_payload_bytes) is int and 0<=remaining_payload_bytes<=PHYSICAL_MAX,'SAME_REMAINING_PHYSICAL_SLOT')
 validate_prefix(value,run,source);raw=encoded(value);need(len(raw)<=RESTORED_MAX,'PREFIX_BOUND_BEFORE_ENCODING')
 header=encoded(dict(schema=HEADER_SCHEMA,purpose='HISTORY_PREFIX',runId=run,collectorSource=source,decodedBytes=len(raw),decodedSha256=hashlib.sha256(raw).hexdigest(),payloadSchema=BODY_SCHEMA));need(len(header)<=HEADER_MAX,'SMALL_CLOSED_HEADER')
 co=zlib.compressobj(9,zlib.DEFLATED,-zlib.MAX_WBITS);gzip=b'\x1f\x8b\x08\x00'+b'\x00'*4+b'\x02\xff'+co.compress(raw)+co.flush()+struct.pack('<II',zlib.crc32(raw)&0xffffffff,len(raw))
 envelope=MAGIC+struct.pack('>I',len(header))+header+gzip;need(len(envelope)<=remaining_payload_bytes,'ENVELOPE_FITS_EXISTING_REMAINING_SLOT')
 return envelope

def restore_prefix(envelope,run,source):
 run_id(run);source_pin(source);need(type(envelope) is bytes and len(envelope)<=PHYSICAL_MAX and envelope.startswith(MAGIC) and len(envelope)>=len(MAGIC)+4,'EXACT_HISTORY_FRAMING')
 n=struct.unpack('>I',envelope[len(MAGIC):len(MAGIC)+4])[0];offset=len(MAGIC)+4;need(0<n<=HEADER_MAX and offset+n+18<=len(envelope),'BOUNDED_FRAMING_HEADER_LENGTH')
 header=strict(envelope[offset:offset+n]);closed(header,'schema purpose runId collectorSource decodedBytes decodedSha256 payloadSchema')
 need(header['schema']==HEADER_SCHEMA and header['purpose']=='HISTORY_PREFIX' and header['runId']==run and header['collectorSource']==source and header['payloadSchema']==BODY_SCHEMA,'HEADER_PURPOSE_RUN_SOURCE')
 need(type(header['decodedBytes']) is int and 0<header['decodedBytes']<=RESTORED_MAX and type(header['decodedSha256']) is str and re.fullmatch('[0-9a-f]{64}',header['decodedSha256']),'BOUND_BEFORE_DECOMPRESSION_AND_JSON')
 gzip=envelope[offset+n:];need(gzip[:10]==b'\x1f\x8b\x08\x00'+b'\x00'*4+b'\x02\xff','EXACT_SINGLE_GZIP_HEADER');de=zlib.decompressobj(31);raw=de.decompress(gzip,RESTORED_MAX+1)
 need(len(raw)<=RESTORED_MAX and de.eof and not de.unused_data and not de.unconsumed_tail,'ONE_COMPLETE_MEMBER_NO_BOMB_TRAILING_CONCAT')
 need(len(raw)==header['decodedBytes'] and hashlib.sha256(raw).hexdigest()==header['decodedSha256'],'EXACT_DECODED_LENGTH_SHA')
 value=strict(raw,True);validate_prefix(value,run,source);return value

def deny(gate,error):
 gate.denied=True
 if gate.first is None:gate.first=type(error).__name__+':'+str(error)
 return dict(schema='e02-root-collector-command-qualification-v1',runId=gate.run,collectorCommandsQualified=False,firstFault=gate.first,runtimeAuthorized=False,structuralReopenCanClearFailstop=False,fixtureOnly=gate.fixture_mode)

def qualify_with_final_witness(envelope,run,source,final_row,actual_final_origin,root_failstop):
 """F witness is genuine platform launch/allpolls ONLY; never stored by us.

No post-F commands are accepted as inputs. Root externally guarantees this is
its full final custody cut, not a selectively omitted later command/history.
"""
 gate=root_failstop
 need(isinstance(gate,q.RootFailstop),'EXTERNAL_ROOT_FAILSTOP_STATE_REQUIRED')
 try:
  need(isinstance(gate,q.RootFailstop) and gate.run==run and gate.fixture_mode is False and not gate.denied,'EXISTING_ACTUAL_ROOT_FAILSTOP_REQUIRED')
  value=restore_prefix(envelope,run,source);closed(final_row,'request requestPin expectedProof');expected=final_row['expectedProof'];q.pin(expected,PHYSICAL_MAX)
  digest=hashlib.sha256(envelope).hexdigest();need(expected==dict(path=final_path(run),bytes=len(envelope),sha256=digest),'FINAL_PIN_DERIVED_AFTER_FROZEN_PAYLOAD')
  words,route=q.command_words(final_row['request']);need(route=='ROOT_CLEANENV_KILL10S' and q.command(final_row['request'],run)=='record' and words[7:12]==['--kind','diagnostic','--name',FINAL_NAME,'--input-base64'] and len(words)==13,'EXACT_LAST_DIAGNOSTIC_F_REQUEST')
  need(q.decode_input(words[12],PHYSICAL_MAX)==envelope,'EXTERNAL_F_REQUEST_CONTAINS_EXACT_FROZEN_BYTES')
  prefix_raw=encoded(value);need(digest.encode() not in prefix_raw and expected['path'].encode() not in prefix_raw,'NO_OWN_F_HASH_OR_PIN_IN_PREFIX')
  need(encoded(final_row['request']) not in prefix_raw,'NO_OWN_F_REQUEST_IN_PREFIX')
  for row in value['expectedCommands']:
   earlier,_route=q.command_words(row['request'])
   if len(earlier)==13 and earlier[4]=='record' and earlier[11]=='--input-base64':
    payload=q.decode_input(earlier[12],PHYSICAL_MAX);need(digest.encode() not in payload and encoded(final_row['request']) not in payload,'NO_OWN_F_HASH_OR_REQUEST_IN_RETAINED_PREFIX_CONTROL')
  ack=q.complete_origin(actual_final_origin,final_row['request']);q.closed(ack,'index store proof payloadUsedBytes reservedBytes metadataOwnerBytes');need(ack['proof']==expected,'GENUINE_PLATFORM_F_ACK_IS_ONLY_PIN_WITNESS')
  plan=dict(schema='e02-root-collector-approved-command-sequence-v1',runId=run,collectorScript=q.SCRIPT_PIN,commands=value['expectedCommands']+[final_row])
  return gate.evaluate(plan,value['origins']+[actual_final_origin])
 except BaseException as error:return deny(gate,error)
