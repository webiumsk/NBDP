"""Pure finite Root command-custody qualification; no IO/tools/caller execution.

Root externally pins the approved full command sequence and genuine receipts.
Structural reopening never clears this per-run failstop or authenticates history.
"""
import base64,binascii,hashlib,json,math,re,shlex
SCRIPT_PIN={'path': '/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r4/collector.py', 'bytes': 14974, 'sha256': '27ded9b13436412ed0bfc3309669f3524dff43a8930f053388d8e782df806de7'}
PYTHON='/home/peterhorvath/.miniforge3/bin/python3.13'
DATA_PARENT='/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual'
REPO_PARENT='/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-root-custody-actual-20261029'
PREFIX=('/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','10s')
KINDS=('lease','plan','gate','grant','api-request','api-frame','diagnostic')
REQUEST_KEYS=('cmd','workdir','login','yield_time_ms','max_output_tokens','sandbox_permissions','justification')
JUSTIFICATION_MAX_UTF8_BYTES=1024

def need(v,m):
 if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_CUSTODY_KEYS')
def encoded(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def pin(d,maximum=65536):
 closed(d,'path bytes sha256');need(type(d['path']) is str and d['path'].startswith('/') and type(d['bytes']) is int and 0<=d['bytes']<=maximum and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'BOUNDED_DESCRIPTOR')
def command_words(request):
 words=shlex.split(request['cmd']);need(shlex.join(words)==request['cmd'],'CANONICAL_EXACT_COMMAND')
 if words and words[0]=='/usr/bin/env':
  need(words[:len(PREFIX)]==list(PREFIX),'EXACT_CLEANENV_KILL10S_PREFIX');return words[len(PREFIX):],'ROOT_CLEANENV_KILL10S'
 return words,'DIRECT_FIXTURE_ONLY'

def command(request,run):
 closed(request,' '.join(REQUEST_KEYS))
 need(request['sandbox_permissions']=='require_escalated','EXACT_REQUIRE_ESCALATED_POLICY')
 justification=request['justification'];need(type(justification) is str and bool(justification.strip()) and 1<=len(justification.encode('utf8','strict'))<=JUSTIFICATION_MAX_UTF8_BYTES,'NONBLANK_BOUNDED_EXACT_JUSTIFICATION')
 need(request['login'] is False and request['workdir']==SCRIPT_PIN['path'].rsplit('/',1)[0] and type(request['yield_time_ms']) is int and 1<=request['yield_time_ms']<=10000 and type(request['max_output_tokens']) is int and 1<=request['max_output_tokens']<=20000,'EXACT_SEVEN_KEY_COLLECTOR_REQUEST')
 words,_route=command_words(request);need(words[:4]==[PYTHON,'-I','-B',SCRIPT_PIN['path']] and len(words)>=7 and words[5:7]==['--run-id',run],'EXACT_DIRECT_PINNED_COLLECTOR_CLI')
 op=words[4];tail=words[7:]
 if op in ('reserve','status'):need(tail==[],'CLOSED_RESERVE_STATUS')
 elif op=='record':
  need(len(tail) in (4,6) and tail[0]=='--kind' and tail[1] in KINDS and tail[2]=='--name' and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',tail[3]),'CLOSED_RECORD')
  if len(tail)==6:
   need(tail[4] in ('--input','--input-base64'),'EXACT_INPUT_ROUTE')
   if tail[4]=='--input':need(tail[5].startswith('/') and '\x00' not in tail[5],'READONLY_INPUT_ARGUMENT')
   else:decode_input(tail[5],49152)
 elif op=='copy':need(len(tail)==6 and tail[0]=='--source-index' and re.fullmatch('[1-9][0-9]?',tail[1]) and tail[2]=='--store' and tail[3] in ('data','repo') and tail[4]=='--name' and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',tail[5]),'CLOSED_COPY')
 else:raise ValueError('UNKNOWN_COLLECTOR_OPERATION')
 return op

def output_object(raw):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_ACK_KEY');out[k]=v
  return out
 def reject(_):raise ValueError('INTEGER_COLLECTOR_ACK_ONLY')
 value=json.loads(raw,object_pairs_hook=pairs,parse_float=reject,parse_constant=reject);need(type(value) is dict,'COMPLETE_JSON_ACKNOWLEDGEMENT');return value

def complete_origin(origin,expected):
 closed(origin,'schema operator launch polls');need(origin['schema']=='e02-actual-tool-custody-v1' and origin['operator']=='/root' and type(origin['polls']) is list and len(origin['polls'])<=16,'GENUINE_ROOT_CUSTODY_ENVELOPE')
 session=None;terminal=False;parts=[];total=0
 for i,frame in enumerate([origin['launch'],*origin['polls']]):
  need(not terminal,'NO_FRAMES_AFTER_TERMINAL');closed(frame,'toolName actualArguments unmodifiedResponse');args=frame['actualArguments'];response=frame['unmodifiedResponse'];need(type(response) is dict,'ACTUAL_UNMODIFIED_RESPONSE')
  if i==0:
   need(frame['toolName']=='tools.exec_command','EXACT_PINNED_LAUNCH')
   expected_words,_route=command_words(expected);need(len(expected_words)>=7,'COMPLETE_PINNED_EXPECTED_REQUEST')
   command(expected,expected_words[6]);command(args,expected_words[6])
   need(encoded(args)==encoded(expected),'EXACT_TYPED_WHOLE_PINNED_LAUNCH')
  else:
   need(frame['toolName']=='tools.write_stdin' and type(args) is dict and set(args)<=set('session_id chars yield_time_ms max_output_tokens'.split()) and type(args.get('session_id')) is int and args['session_id']>0 and args['session_id']==session and args.get('chars','')=='' and ('yield_time_ms' not in args or type(args['yield_time_ms']) is int),'SAME_SESSION_ALL_POLLS')
  cap=args.get('max_output_tokens',10000);count=response.get('original_token_count');wall=response.get('wall_time_seconds')
  need(type(cap) is int and type(count) is int and 0<=count<=cap and type(wall) in (int,float) and math.isfinite(wall) and wall>=0,'NO_UNKNOWN_OR_TRUNCATED_FRAME_METADATA')
  need(type(response.get('output')) is str and not any(response.get(k) for k in ('truncated','output_truncated','interrupted','error','isError')),'COMPLETE_NO_ERROR_OUTPUT')
  out=response['output'];need(not any(s in out for s in ('tokens truncated','Warning: truncated output','Output exceeded the available','[output truncated]')),'NO_TRUNCATION_MARKER');total+=len(out.encode());need(total<=65536,'FINITE_RAW_API_OUTPUT');parts.append(out)
  if response.get('exit_code') is not None:need(type(response['exit_code']) is int and response['exit_code']==0 and ('session_id' not in response or response['session_id'] is None or (type(response['session_id']) is int and response['session_id']==session)),'ACTUAL_TERMINAL0');terminal=True
  else:
   observed=response.get('session_id');need(type(observed) is int and observed>0,'ACTUAL_YIELDED_SESSION');session=session or observed;need(session==observed,'SAME_RESPONSE_SESSION')
 need(terminal,'MISSING_OR_UNKNOWN_TERMINAL');return output_object(''.join(parts))

def decode_input(text,remaining):
 need(type(text) is str and text.isascii() and len(text)<=4*((remaining+2)//3),'BOUNDED_MEMORY_INPUT')
 try:raw=base64.b64decode(text,validate=True)
 except (ValueError,binascii.Error):raise ValueError('STRICT_MEMORY_INPUT')
 need(len(raw)<=remaining and base64.b64encode(raw).decode('ascii')==text,'CANONICAL_MEMORY_INPUT');return raw

def exact_ack(op,request,expected,ack,run,model):
 words,_route=command_words(request);tail=words[7:]
 if op=='reserve':
  closed(ack,'reservation reservedInsideMetadataBytes metadataOwnerBytes payloadAvailableBytes grantIssued');pin(ack['reservation'],1024);pin(expected,1024)
  need(ack['reservation']==expected and expected['bytes']>0 and expected['path']==DATA_PARENT+'/'+run+'/reservation.json' and ack['reservedInsideMetadataBytes']==65536 and type(ack['reservedInsideMetadataBytes']) is int and ack['metadataOwnerBytes']==8388608 and ack['payloadAvailableBytes']==49152 and ack['grantIssued'] is False,'EXACT_RESERVATION_ACK_AND_PIN');model['physical']=expected['bytes'];return
 if op=='status':
  closed(ack,'state historicalIO reservedBytes ledgerPrechargedBytes payloadUsedBytes recordCount physicalBytes')
  need(expected is None and ack['state']=='CURRENT_STRUCTURAL_CUSTODY_ONLY' and ack['historicalIO']=='UNKNOWN' and all(type(ack[k]) is int for k in ('reservedBytes','ledgerPrechargedBytes','payloadUsedBytes','recordCount','physicalBytes')),'STRUCTURAL_STATUS_CLOSED_TYPES')
  need([ack[k] for k in ('reservedBytes','ledgerPrechargedBytes','payloadUsedBytes','recordCount','physicalBytes')]==[65536,16384,model['used'],len(model['rows']),model['physical']],'EXACT_CURRENT_COUNTERS_NOT_HISTORY');return
 closed(ack,'index store proof payloadUsedBytes reservedBytes metadataOwnerBytes');pin(ack['proof'],49152);pin(expected,49152)
 index=len(model['rows'])+1
 if op=='record':
  store='data';name=tail[1]+'--'+tail[3];source=None
  if len(tail)==4:raw=b''
  elif tail[4]=='--input-base64':raw=decode_input(tail[5],49152-model['used'])
  else:raw=None # Read-only bytes must have an independently Root-pinned model.
  if raw is not None:need(expected['bytes']==len(raw) and expected['sha256']==hashlib.sha256(raw).hexdigest(),'EXACT_MEMORY_PAYLOAD_HASH')
 else:
  source=int(tail[1]);need(1<=source<index,'KNOWN_COPY_SOURCE');old=model['rows'][source-1];store=tail[3];name='copy--'+tail[5]
  need(expected['bytes']==old['n'] and expected['sha256']==old['h'],'EXACT_REGISTERED_COPY_MODEL')
 path=(DATA_PARENT if store=='data' else REPO_PARENT)+'/'+run+'/'+name
 need(expected['path']==path and ack['proof']==expected and type(ack['index']) is int and ack['index']==index and ack['store']==store,'EXACT_RUN_STORE_PATH_INDEX_AND_PROOF')
 used=model['used']+expected['bytes'];need(used<=49152 and type(ack['payloadUsedBytes']) is int and ack['payloadUsedBytes']==used and type(ack['reservedBytes']) is int and ack['reservedBytes']==65536 and type(ack['metadataOwnerBytes']) is int and ack['metadataOwnerBytes']==8388608,'EXACT_MONOTONIC_WRITE_COUNTERS')
 charge=dict(i=index,n=expected['bytes'],t=store,p=name,h=expected['sha256'],s=source);charge_size=len(encoded(charge));need(charge_size<=224,'EXACT_CHARGE_OVERHEAD_MODEL');model['used']=used;model['rows'].append(charge);model['physical']+=expected['bytes']+charge_size;need(model['physical']<=65536,'SAME_PHYSICAL_SLOT')

class RootFailstop:
 def __init__(self,run_id,previously_unqualified=False,fixture_mode=False):
  need(type(run_id) is str and re.fullmatch('[0-9a-f]{32}',run_id),'EXACT_RUN_ID');need(type(fixture_mode) is bool,'EXPLICIT_FIXTURE_TYPE');self.fixture_mode=fixture_mode;self.run=run_id;self.denied=previously_unqualified is not False;self.first='PRIOR_ROOT_UNQUALIFIED' if self.denied else None
 def evaluate(self,plan,origins):
  try:
   need(not self.denied,'PERMANENT_ROOT_RUNID_FAILSTOP');closed(plan,'schema runId collectorScript commands')
   need(plan['schema']=='e02-root-collector-approved-command-sequence-v1' and plan['runId']==self.run and plan['collectorScript']==SCRIPT_PIN,'EXTERNALLY_FROZEN_CURRENT_COMMAND_PLAN')
   need(type(plan['commands']) is list and 1<=len(plan['commands'])<=128 and type(origins) is list and len(origins)==len(plan['commands']),'ALL_COMMAND_RECEIPTS_REQUIRED_NO_OMISSIONS')
   writes=0;model=dict(used=0,rows=[],physical=0)
   for i,(row,origin) in enumerate(zip(plan['commands'],origins)):
    closed(row,'request requestPin expectedProof');pin(row['requestPin'],16777216);raw=encoded(row['request']);need(len(raw)==row['requestPin']['bytes'] and hashlib.sha256(raw).hexdigest()==row['requestPin']['sha256'],'EXACT_APPROVED_REQUEST_PIN')
    _words,route=command_words(row['request']);need(route=='ROOT_CLEANENV_KILL10S' or self.fixture_mode is True,'ACTUAL_ROOT_REQUIRES_CLEANENV_KILL10S')
    op=command(row['request'],self.run);need((i==0)==(op=='reserve'),'ONE_RESERVATION_FIRST');writes+=int(op in ('record','copy'));need(writes<=64,'FINITE_WRITE_COUNT')
    ack=complete_origin(origin,row['request'])
    exact_ack(op,row['request'],row['expectedProof'],ack,self.run,model)
  except BaseException as error:
   self.denied=True
   if self.first is None:self.first=type(error).__name__+':'+str(error)
  return dict(schema='e02-root-collector-command-qualification-v1',runId=self.run,collectorCommandsQualified=not self.denied,firstFault=self.first,runtimeAuthorized=False,structuralReopenCanClearFailstop=False,fixtureOnly=self.fixture_mode)
