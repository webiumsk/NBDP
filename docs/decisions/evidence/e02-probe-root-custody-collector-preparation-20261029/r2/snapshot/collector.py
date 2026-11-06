"""One precharged Root-custody slot. No tools, API, helper or process execution."""
import argparse,fcntl,hashlib,json,os,pathlib,re,stat,sys

DATA_PARENT=pathlib.Path('/Data/nbdp-e02-tooling-20261027/probe-root-custody-actual')
REPO_PARENT=pathlib.Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-root-custody-actual-20261029')
SLOT=65536
PARENT_METADATA=8388608
LEDGER_RESERVE=16384
PAYLOAD=SLOT-LEDGER_RESERVE
MAX_WRITES=64
HEADER_MAX=1024
CHARGE_MAX=224
FAILURE_MAX=512
KINDS=('lease','plan','gate','grant','api-request','api-frame','diagnostic')
HEADER_KEYS='schema runId metadataOwnerBytes reservedBytes ledgerPrechargeBytes payloadAvailableBytes maximumWrites chargeRecordMax headerMax failureMax uid gid roots'
CHARGE_KEYS='i n t p h s'

class Refusal(ValueError):pass

def need(ok,code):
 if not ok:raise Refusal(code)
def raw_json(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def strict(raw):
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
  return out
 def reject(_):raise Refusal('INTEGER_METADATA_ONLY')
 return json.loads(raw,object_pairs_hook=pairs,parse_float=reject,parse_constant=reject)
def closed(x,keys):need(type(x) is dict and set(x)==set(keys.split()),'CLOSED_LEDGER_KEYS')
def identity(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def dir_id(s):return dict(device=str(s.st_dev),inode=str(s.st_ino),uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode))
def private_dir(path,create=False):
 path=pathlib.Path(path)
 for p in (path,*path.parents):
  if p.exists() or p.is_symlink():need(not p.is_symlink(),'SYMLINK_DIRECTORY')
 if create:path.mkdir(mode=0o700)
 st=path.lstat();need(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700 and st.st_uid==os.getuid() and st.st_gid==os.getgid(),'PRIVATE_OWNED0700_DIRECTORY')
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:need(dir_id(os.fstat(fd))==dir_id(st),'DIRECTORY_OPEN_IDENTITY')
 except BaseException:os.close(fd);raise
 return fd

def exact_write(fd,name,raw):
 """Single write only. Caller has already charged or prepaid this whole record."""
 out=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
 try:
  need(os.write(out,raw)==len(raw),'SHORT_WRITE_NO_REPAIR')
  os.fsync(out)
  st=os.fstat(out);need(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and st.st_size==len(raw) and st.st_uid==os.getuid() and st.st_gid==os.getgid(),'EXACT_PRIVATE_FILE')
 finally:os.close(out)
 os.fsync(fd)

def read_at(fd,name,limit):
 st=os.stat(name,dir_fd=fd,follow_symlinks=False);need(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and st.st_uid==os.getuid() and st.st_gid==os.getgid() and st.st_size<=limit,'REGULAR_PRIVATE_BOUNDED_RECORD')
 f=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
 try:
  need(identity(os.fstat(f))==identity(st),'RECORD_OPEN_DRIFT');raw=os.read(f,limit+1);need(len(raw)==st.st_size and identity(os.fstat(f))==identity(st),'RECORD_READ_DRIFT')
 finally:os.close(f)
 need(identity(os.stat(name,dir_fd=fd,follow_symlinks=False))==identity(st),'RECORD_PATH_DRIFT');return raw

def run_paths(run_id):
 need(type(run_id) is str and re.fullmatch('[0-9a-f]{32}',run_id),'FIXED_RUN_ID')
 return {'data':DATA_PARENT/run_id,'repo':REPO_PARENT/run_id}
def check_roots(paths,fds,roots):
 for key in ('data','repo'):
  now=paths[key].lstat();need(not paths[key].is_symlink() and dir_id(now)==roots[key] and dir_id(os.fstat(fds[key]))==roots[key],'ROOT_PATH_OR_HANDLE_IDENTITY')
  parent=paths[key].parent.lstat();need(not paths[key].parent.is_symlink() and stat.S_IMODE(parent.st_mode)==0o700 and parent.st_uid==os.getuid() and parent.st_gid==os.getgid(),'PRIVATE_FIXED_PARENT')

def reserve(run_id):
 """The entire same-account65536 slot is durable before ANY proof is admitted."""
 paths=run_paths(run_id);fds={}
 try:
  for p in (DATA_PARENT,REPO_PARENT):
   if not p.exists():fd=private_dir(p,True);os.fsync(fd);os.close(fd)
   fd=private_dir(p);os.close(fd)
  need(not any(p.exists() or p.is_symlink() for p in paths.values()),'NO_ACCOUNT_REUSE_OR_AUTOMATIC_RETRY')
  for key,p in paths.items():fds[key]=private_dir(p,True)
  header=dict(schema='e02-root-probe-custody-slot-v1',runId=run_id,metadataOwnerBytes=PARENT_METADATA,reservedBytes=SLOT,ledgerPrechargeBytes=LEDGER_RESERVE,payloadAvailableBytes=PAYLOAD,maximumWrites=MAX_WRITES,chargeRecordMax=CHARGE_MAX,headerMax=HEADER_MAX,failureMax=FAILURE_MAX,uid=os.getuid(),gid=os.getgid(),roots={k:dir_id(os.fstat(fd)) for k,fd in fds.items()})
  raw=raw_json(header);need(len(raw)<=HEADER_MAX and HEADER_MAX+MAX_WRITES*CHARGE_MAX+FAILURE_MAX<=LEDGER_RESERVE,'LEDGER_OVERHEAD_PREPAID')
  check_roots(paths,fds,header['roots']);exact_write(fds['data'],'reservation.json',raw)
  # Persist directory entries for both fresh roots before returning reservation.
  for p in (DATA_PARENT,REPO_PARENT):fd=private_dir(p);os.fsync(fd);os.close(fd)
  return dict(reservation=dict(path=str(paths['data']/'reservation.json'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),reservedInsideMetadataBytes=SLOT,metadataOwnerBytes=PARENT_METADATA,payloadAvailableBytes=PAYLOAD,grantIssued=False)
 finally:
  for fd in fds.values():os.close(fd)

class Account:
 """A retained lock serializes immutable charge records for both stores."""
 def __init__(self,run_id):self.paths=run_paths(run_id);self.fds={};self.lock=None;self.header=None;self.rows=[];self.used=0;self.failed=None
 def __enter__(self):
  try:
   self.fds['data']=private_dir(self.paths['data'])
   self.lock=os.open('reservation.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=self.fds['data']);fcntl.flock(self.lock,fcntl.LOCK_EX)
   st=os.fstat(self.lock);need(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600,'EXACT_RESERVATION_HANDLE')
   raw=read_at(self.fds['data'],'reservation.json',HEADER_MAX);need(identity(os.stat('reservation.json',dir_fd=self.fds['data'],follow_symlinks=False))==identity(st),'PINNED_RESERVATION_LOCK')
   self.header=strict(raw);closed(self.header,HEADER_KEYS);h=self.header
   closed(h['roots'],'data repo')
   for row in h['roots'].values():closed(row,'device inode uid gid mode')
   need(h['schema']=='e02-root-probe-custody-slot-v1' and h['runId']==self.paths['data'].name and h['uid']==os.getuid() and h['gid']==os.getgid(),'EXACT_RUN_SLOT_IDENTITY')
   need([h[k] for k in ('metadataOwnerBytes','reservedBytes','ledgerPrechargeBytes','payloadAvailableBytes','maximumWrites','chargeRecordMax','headerMax','failureMax')]==[PARENT_METADATA,SLOT,LEDGER_RESERVE,PAYLOAD,MAX_WRITES,CHARGE_MAX,HEADER_MAX,FAILURE_MAX],'ONE_FIXED_PARENT_ACCOUNT_NO_NEW_BUDGET')
   self.fds['repo']=private_dir(self.paths['repo'])
   self.check();self.scan();return self
  except BaseException as error:
   self.poison(error);self.close();raise
 def check(self):check_roots(self.paths,self.fds,self.header['roots'])
 def poison(self,error):
  # Failure bytes are prepaid. Never overwrite a first fault. If identity or
  # storage failure prevents marking, an incomplete ledger/proof still refuses.
  if self.failed is None:self.failed=error
  try:
   if self.header is None:return
   # The retained owned DATA root can safely hold a sticky fault even when
   # the repository root is missing, substituted or has unsafe permissions.
   expected=self.header['roots']['data'];fd=self.fds['data']
   need(dir_id(self.paths['data'].lstat())==expected and dir_id(os.fstat(fd))==expected and not self.paths['data'].is_symlink(),'OWNED_DATA_FAILURE_ROOT')
   if 'failure.json' in os.listdir(self.fds['data']):return
   code=str(error) if isinstance(error,Refusal) else type(error).__name__
   raw=raw_json(dict(schema='e02-root-custody-sticky-failure-v1',code=code,chargedRecords=len(self.rows)))
   need(len(raw)<=FAILURE_MAX,'BOUNDED_FAILURE_RECORD');exact_write(self.fds['data'],'failure.json',raw)
  except BaseException:pass
 def scan(self):
  names={k:set(os.listdir(fd)) for k,fd in self.fds.items()};need('failure.json' not in names['data'],'STICKY_FIRST_FAILURE')
  expected={'data':{'reservation.json'},'repo':set()};self.rows=[];self.used=0
  charge_names=sorted(n for n in names['data'] if re.fullmatch(r'charge-[0-9]{2}\.json',n));need(len(charge_names)<=MAX_WRITES,'WRITE_COUNT_BOUND')
  for i,name in enumerate(charge_names,1):
   need(name=='charge-%02d.json'%i,'NO_LEDGER_GAPS');r=strict(read_at(self.fds['data'],name,CHARGE_MAX));closed(r,CHARGE_KEYS)
   need(type(r['i']) is int and r['i']==i and type(r['n']) is int and 0<=r['n']<=PAYLOAD and r['t'] in ('data','repo') and type(r['p']) is str and re.fullmatch('(lease|plan|gate|grant|api-request|api-frame|diagnostic|copy)--[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',r['p']) and type(r['h']) is str and re.fullmatch('[0-9a-f]{64}',r['h']),'CLOSED_EXPECTED_CHARGE')
   need(r['s'] is None or type(r['s']) is int and 1<=r['s']<i,'PRIOR_REGISTERED_COPY_ONLY');need((r['s'] is None)==(not r['p'].startswith('copy--')),'NO_UNCHARGED_COPY_ALIAS')
   self.used+=r['n'];need(self.used<=PAYLOAD and r['p'] not in expected[r['t']],'MONOTONIC_PAYLOAD_AND_ONE_USE_NAME')
   raw=read_at(self.fds[r['t']],r['p'],r['n']);need(len(raw)==r['n'] and hashlib.sha256(raw).hexdigest()==r['h'],'INCOMPLETE_OR_CHANGED_PRECHARGED_PROOF')
   if r['s'] is not None:
    source=self.rows[r['s']-1];need(source['n']==r['n'] and source['h']==r['h'],'EXACT_COPY_CUSTODY')
   expected['data'].add(name);expected[r['t']].add(r['p']);self.rows.append(r)
  need(names==expected,'NO_UNACCOUNTED_OR_FOREIGN_FILE');self.check()
 def write(self,kind,name,raw,store='data',source=None):
  try:
   need(self.failed is None and 'failure.json' not in os.listdir(self.fds['data']),'STICKY_FIRST_FAILURE')
   self.check();self.scan();need(type(raw) is bytes and kind in KINDS+('copy',) and store in ('data','repo'),'CLOSED_PROOF_OPERATION');need(type(name) is str and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}',name),'FLAT_ONE_USE_PROOF_NAME')
   need((kind=='copy')==(type(source) is int) and (kind=='copy' or store=='data'),'COPIES_ONLY_TO_SECOND_STORE')
   if source is not None:
    need(1<=source<=len(self.rows),'REGISTERED_COPY_SOURCE');old=self.rows[source-1];need(old['n']==len(raw) and old['h']==hashlib.sha256(raw).hexdigest(),'SUPPLIED_COPY_BYTES_MUST_EQUAL_SOURCE')
   filename=kind+'--'+name;i=len(self.rows)+1
   need(i<=MAX_WRITES and self.used+len(raw)<=PAYLOAD,'REFUSE_BEFORE_ANY_OVER_LIMIT_WRITE')
   need(filename not in os.listdir(self.fds[store]),'DUPLICATE_PROOF_NAME')
   row=dict(i=i,n=len(raw),t=store,p=filename,h=hashlib.sha256(raw).hexdigest(),s=source);encoded=raw_json(row);need(len(encoded)<=CHARGE_MAX,'PREPAID_CHARGE_RECORD_BOUND')
   self.check();exact_write(self.fds['data'],'charge-%02d.json'%i,encoded) # durable before proof open
   self.rows.append(row);self.used+=len(raw) # never refunded, including failed physical write
   self.check();exact_write(self.fds[store],filename,raw);self.check();self.scan()
   return dict(index=i,store=store,proof=dict(path=str(self.paths[store]/filename),bytes=len(raw),sha256=row['h']),payloadUsedBytes=self.used,reservedBytes=SLOT,metadataOwnerBytes=PARENT_METADATA)
  except BaseException as error:self.poison(error);raise
 def record(self,kind,name,raw):return self.write(kind,name,raw)
 def copy(self,index,store,name):
  try:
   need(type(index) is int and 1<=index<=len(self.rows),'EXACT_REGISTERED_COPY_INDEX');old=self.rows[index-1];raw=read_at(self.fds[old['t']],old['p'],old['n']);need(hashlib.sha256(raw).hexdigest()==old['h'],'COPY_SOURCE_DRIFT');return self.write('copy',name,raw,store,index)
  except BaseException as error:self.poison(error);raise
 def close(self):
  if self.lock is not None:fcntl.flock(self.lock,fcntl.LOCK_UN);os.close(self.lock);self.lock=None
  for fd in self.fds.values():os.close(fd)
  self.fds={}
 def __exit__(self,kind,error,tb):
  if error is not None:self.poison(error)
  self.close()

def supplied_bytes(path,limit):
 if path is None:return sys.stdin.buffer.read(limit+1)
 p=pathlib.Path(path);need(p.is_absolute(),'ABSOLUTE_READONLY_INPUT')
 for q in (p,*p.parents):need(not q.is_symlink(),'NO_INPUT_SYMLINK')
 st=p.lstat();need(stat.S_ISREG(st.st_mode) and st.st_size<=limit,'BOUNDED_READONLY_INPUT')
 f=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  need(identity(os.fstat(f))==identity(st),'INPUT_OPEN_DRIFT');raw=os.read(f,limit+1);need(identity(os.fstat(f))==identity(st) and len(raw)==st.st_size,'INPUT_HANDLE_DRIFT')
 finally:os.close(f)
 need(identity(p.lstat())==identity(st),'INPUT_PATH_DRIFT');return raw

def structural_status(account):
 # A reopen checks current bytes/membership only. It CANNOT reconstruct a lost
 # fsync/close/postcheck/acknowledgement failure when persistence was unavailable.
 return dict(state='CURRENT_STRUCTURAL_CUSTODY_ONLY',historicalIO='UNKNOWN',reservedBytes=SLOT,ledgerPrechargedBytes=LEDGER_RESERVE,payloadUsedBytes=account.used,recordCount=len(account.rows),physicalBytes=sum(os.stat(n,dir_fd=fd,follow_symlinks=False).st_size for fd in account.fds.values() for n in os.listdir(fd)))

def main(argv):
 p=argparse.ArgumentParser(allow_abbrev=False,description='One65536 Root custody slot; supplies no API/tool execution')
 commands=p.add_subparsers(dest='op',required=True)
 for op in ('reserve','record','copy','status'):
  q=commands.add_parser(op,allow_abbrev=False);q.add_argument('--run-id',required=True)
  if op=='record':q.add_argument('--kind',choices=KINDS,required=True);q.add_argument('--name',required=True);q.add_argument('--input')
  if op=='copy':q.add_argument('--source-index',type=int,required=True);q.add_argument('--store',choices=('data','repo'),required=True);q.add_argument('--name',required=True)
 a=p.parse_args(argv)
 if a.op=='reserve':result=reserve(a.run_id)
 else:
  with Account(a.run_id) as account:
   if a.op=='record':result=account.record(a.kind,a.name,supplied_bytes(a.input,PAYLOAD-account.used))
   elif a.op=='copy':result=account.copy(a.source_index,a.store,a.name)
   else:result=structural_status(account)
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main(sys.argv[1:])
