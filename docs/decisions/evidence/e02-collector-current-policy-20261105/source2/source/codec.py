"""Optional pure lossless collector-API derivative. Never writes decoded/temp data."""
import hashlib,json,math,re,shlex,struct,zlib
RESTORED_MAX=16777216
COMPRESSED_MAX=49152
SCRIPT='/Data/nbdp-e02-tooling-20261027/probe-root-custody-collector-preparation-r4/collector.py'
PYTHON='/home/peterhorvath/.miniforge3/bin/python3.13'
PREFIX=('/usr/bin/env','-i','PATH=/usr/bin:/bin','LANG=C.UTF-8','LC_ALL=C.UTF-8','/usr/bin/timeout','--signal=KILL','10s')
DATA='/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual'
REPO='/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-root-custody-actual-20261029'

def need(v,m):
 if not v:raise ValueError(m)
def closed(v,keys):need(type(v) is dict and set(v)==set(keys.split()),'CLOSED_CODEC_FIELDS')
def target(path):
 need(type(path) is str and (re.fullmatch(re.escape(DATA)+r'/[0-9a-f]{32}/api-frame--[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',path) or re.fullmatch(re.escape(REPO)+r'/[0-9a-f]{32}/copy--[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',path)),'FIXED_ACCOUNTED_COLLECTOR_API_TARGET')
def origin(raw):
 need(type(raw) is bytes and len(raw)<=RESTORED_MAX,'RESTORED_BOUND_BEFORE_JSON')
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_API_KEY');out[k]=v
  return out
 def number(s):
  n=float(s);need(math.isfinite(n),'FINITE_API_DURATION');return n
 def reject(_):raise ValueError('NONFINITE_API_CONSTANT')
 value=json.loads(raw.decode('utf8','strict'),object_pairs_hook=pairs,parse_float=number,parse_constant=reject);closed(value,'schema operator launch polls');need(value['schema']=='e02-actual-tool-custody-v1' and value['operator']=='/root','COLLECTOR_API_METADATA_ONLY')
 launch=value['launch'];closed(launch,'toolName actualArguments unmodifiedResponse');need(launch['toolName']=='tools.exec_command' and type(launch['actualArguments']) is dict,'ACTUAL_COLLECTOR_LAUNCH')
 words=shlex.split(launch['actualArguments']['cmd']);need(shlex.join(words)==launch['actualArguments']['cmd'],'EXACT_CANONICAL_CODEC_REQUEST')
 if words and words[0]=='/usr/bin/env':
  need(words[:len(PREFIX)]==list(PREFIX),'EXACT_CODEC_CLEANENV_KILL10S');words=words[len(PREFIX):]
 need(len(words)>=7 and words[:4]==[PYTHON,'-I','-B',SCRIPT] and words[4] in ('reserve','record','copy','status') and words[5]=='--run-id' and re.fullmatch('[0-9a-f]{32}',words[6]),'NOT_HELPER_PROBE_OR_OTHER_API_CUSTODY')
 nodes=0
 def walk(v,depth=0):
  nonlocal nodes
  nodes+=1;need(depth<=64 and nodes<=250000,'FINITE_API_METADATA_STRUCTURE')
  if type(v) is dict:
   for x in v.values():walk(x,depth+1)
  elif type(v) is list:
   for x in v:walk(x,depth+1)
 walk(value);return value

def encode_api(raw,path):
 target(path);origin(raw) # Never rewrites or normalizes the original bytes.
 co=zlib.compressobj(9,zlib.DEFLATED,-zlib.MAX_WBITS);body=co.compress(raw)+co.flush()
 compressed=b'\x1f\x8b\x08\x00'+b'\x00'*4+b'\x02\xff'+body+struct.pack('<II',zlib.crc32(raw)&0xffffffff,len(raw))
 need(len(compressed)<=COMPRESSED_MAX,'COMPRESSED_PHYSICAL_PAYLOAD_BOUND')
 index=dict(schema='e02-collector-api-gzip-custody-v1',encoding='GZIP_SINGLE_MEMBER_MTIME0',compressed=dict(path=path,bytes=len(compressed),sha256=hashlib.sha256(compressed).hexdigest()),restored=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 return compressed,index

def restore_api(compressed,index):
 closed(index,'schema encoding compressed restored');need(index['schema']=='e02-collector-api-gzip-custody-v1' and index['encoding']=='GZIP_SINGLE_MEMBER_MTIME0','EXACT_OPTIONAL_API_CODEC');p=index['compressed'];r=index['restored'];closed(p,'path bytes sha256');closed(r,'bytes sha256');target(p['path'])
 need(type(compressed) is bytes and type(p['bytes']) is int and len(compressed)==p['bytes']<=COMPRESSED_MAX and p['sha256']==hashlib.sha256(compressed).hexdigest(),'EXACT_COMPRESSED_PHYSICAL_PIN')
 need(compressed[:10]==b'\x1f\x8b\x08\x00'+b'\x00'*4+b'\x02\xff','EXACT_DETERMINISTIC_GZIP_HEADER')
 need(type(r['bytes']) is int and 0<=r['bytes']<=RESTORED_MAX and type(r['sha256']) is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'RESTORED_LENGTH_HASH_BOUND')
 de=zlib.decompressobj(31);raw=de.decompress(compressed,RESTORED_MAX+1)
 need(len(raw)<=RESTORED_MAX and de.eof and not de.unused_data and not de.unconsumed_tail,'ONE_COMPLETE_GZIP_MEMBER_NO_TRAILING_OR_BOMB')
 need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'EXACT_RESTORED_ORIGIN_BYTES')
 return raw,origin(raw)
