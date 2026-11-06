"""Pure finite Root command-custody qualification; no IO/tools/caller execution.

Root externally pins the approved full command sequence and genuine receipts.
Structural reopening never clears this per-run failstop or authenticates history.
"""
import hashlib,json,math,re,shlex
SCRIPT_PIN={'path': '/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r2/collector.py', 'bytes': 14269, 'sha256': 'a60ee12b96850356bb9dd8e4e1e8219720c17ee0ae009c336f2869c59d74e328'}
PYTHON='/home/peterhorvath/.miniforge3/bin/python3.13'
DATA_PARENT='/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual'
KINDS=('lease','plan','gate','grant','api-request','api-frame','diagnostic')

def need(v,m):
 if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_CUSTODY_KEYS')
def encoded(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def pin(d):
 closed(d,'path bytes sha256');need(type(d['path']) is str and d['path'].startswith('/') and type(d['bytes']) is int and 0<=d['bytes']<=65536 and type(d['sha256']) is str and re.fullmatch('[0-9a-f]{64}',d['sha256']),'BOUNDED_DESCRIPTOR')
def command(request,run):
 closed(request,'cmd workdir login yield_time_ms max_output_tokens')
 need(request['login'] is False and request['workdir']==SCRIPT_PIN['path'].rsplit('/',1)[0] and type(request['yield_time_ms']) is int and 1<=request['yield_time_ms']<=10000 and type(request['max_output_tokens']) is int and 1<=request['max_output_tokens']<=20000,'EXACT_FIVE_KEY_COLLECTOR_REQUEST')
 words=shlex.split(request['cmd']);need(shlex.join(words)==request['cmd'] and words[:4]==[PYTHON,'-I','-B',SCRIPT_PIN['path']] and len(words)>=7 and words[5:7]==['--run-id',run],'EXACT_DIRECT_PINNED_COLLECTOR_CLI')
 op=words[4];tail=words[7:]
 if op in ('reserve','status'):need(tail==[],'CLOSED_RESERVE_STATUS')
 elif op=='record':
  need(len(tail) in (4,6) and tail[0]=='--kind' and tail[1] in KINDS and tail[2]=='--name' and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',tail[3]),'CLOSED_RECORD')
  if len(tail)==6:need(tail[4]=='--input' and tail[5].startswith('/') and '\x00' not in tail[5],'READONLY_INPUT_ARGUMENT')
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
  if i==0:need(frame['toolName']=='tools.exec_command' and args==expected,'EXACT_PINNED_LAUNCH')
  else:
   need(frame['toolName']=='tools.write_stdin' and type(args) is dict and set(args)<=set('session_id chars yield_time_ms max_output_tokens'.split()) and args.get('session_id')==session and args.get('chars','')=='','SAME_SESSION_ALL_POLLS')
  cap=args.get('max_output_tokens',10000);count=response.get('original_token_count');wall=response.get('wall_time_seconds')
  need(type(cap) is int and type(count) is int and 0<=count<=cap and type(wall) in (int,float) and math.isfinite(wall) and wall>=0,'NO_UNKNOWN_OR_TRUNCATED_FRAME_METADATA')
  need(type(response.get('output')) is str and not any(response.get(k) for k in ('truncated','output_truncated','interrupted','error','isError')),'COMPLETE_NO_ERROR_OUTPUT')
  out=response['output'];need(not any(s in out for s in ('tokens truncated','Warning: truncated output','Output exceeded the available','[output truncated]')),'NO_TRUNCATION_MARKER');total+=len(out.encode());need(total<=65536,'FINITE_RAW_API_OUTPUT');parts.append(out)
  if response.get('exit_code') is not None:need(type(response['exit_code']) is int and response['exit_code']==0 and ('session_id' not in response or response['session_id'] is None or response['session_id']==session),'ACTUAL_TERMINAL0');terminal=True
  else:
   observed=response.get('session_id');need(type(observed) is int and observed>0,'ACTUAL_YIELDED_SESSION');session=session or observed;need(session==observed,'SAME_RESPONSE_SESSION')
 need(terminal,'MISSING_OR_UNKNOWN_TERMINAL');return output_object(''.join(parts))

class RootFailstop:
 def __init__(self,run_id,previously_unqualified=False):
  need(type(run_id) is str and re.fullmatch('[0-9a-f]{32}',run_id),'EXACT_RUN_ID');self.run=run_id;self.denied=previously_unqualified is not False;self.first='PRIOR_ROOT_UNQUALIFIED' if self.denied else None
 def evaluate(self,plan,origins):
  try:
   need(not self.denied,'PERMANENT_ROOT_RUNID_FAILSTOP');closed(plan,'schema runId collectorScript commands')
   need(plan['schema']=='e02-root-collector-approved-command-sequence-v1' and plan['runId']==self.run and plan['collectorScript']==SCRIPT_PIN,'EXTERNALLY_FROZEN_CURRENT_COMMAND_PLAN')
   need(type(plan['commands']) is list and 1<=len(plan['commands'])<=128 and type(origins) is list and len(origins)==len(plan['commands']),'ALL_COMMAND_RECEIPTS_REQUIRED_NO_OMISSIONS')
   writes=0
   for i,(row,origin) in enumerate(zip(plan['commands'],origins)):
    closed(row,'request requestPin');pin(row['requestPin']);raw=encoded(row['request']);need(len(raw)==row['requestPin']['bytes'] and hashlib.sha256(raw).hexdigest()==row['requestPin']['sha256'],'EXACT_APPROVED_REQUEST_PIN')
    op=command(row['request'],self.run);need((i==0)==(op=='reserve'),'ONE_RESERVATION_FIRST');writes+=int(op in ('record','copy'));need(writes<=64,'FINITE_WRITE_COUNT')
    ack=complete_origin(origin,row['request'])
    if op=='status':need(ack.get('state')=='CURRENT_STRUCTURAL_CUSTODY_ONLY' and ack.get('historicalIO')=='UNKNOWN' and 'failed' not in ack,'STRUCTURAL_OBSERVATION_NEVER_HISTORICAL_SUCCESS')
    elif op=='reserve':need(ack.get('reservedInsideMetadataBytes')==65536 and ack.get('metadataOwnerBytes')==8388608 and ack.get('payloadAvailableBytes')==49152 and ack.get('grantIssued') is False,'RESERVATION_ACK_REQUIRED')
    else:need(ack.get('reservedBytes')==65536 and ack.get('metadataOwnerBytes')==8388608 and type(ack.get('index')) is int and ack['index']==writes and type(ack.get('payloadUsedBytes')) is int and 0<=ack['payloadUsedBytes']<=49152 and type(ack.get('proof')) is dict,'COMPLETE_WRITE_ACK_REQUIRED')
  except BaseException as error:
   self.denied=True
   if self.first is None:self.first=type(error).__name__+':'+str(error)
  return dict(schema='e02-root-collector-command-qualification-v1',runId=self.run,collectorCommandsQualified=not self.denied,firstFault=self.first,runtimeAuthorized=False,structuralReopenCanClearFailstop=False)
