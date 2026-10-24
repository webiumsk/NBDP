from pathlib import Path
import hashlib,json,subprocess,re,urllib.parse,tarfile
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');G=['git','--git-dir=/tmp/nbdp-publish-repo/.git','--work-tree='+str(R)];P=R/'docs/decisions/evidence/transport-gate-runtime-publication-r1';paths=subprocess.check_output(G+['diff','--cached','--name-only','-z']).decode().rstrip('\0').split('\0');tracked=set(subprocess.check_output(G+['ls-files','-z']).decode().split('\0'));allow=set(Path('/tmp/nbdp-checkpoint-stage-paths.txt').read_text().splitlines());assert set(paths)<=allow
jsonCount=0
for rel in paths:
 p=R/rel
 if p.suffix=='.json':
  def pairs(rows):
   d={}
   for k,v in rows:
    if k in d:raise ValueError('DuplicateJSONkey:'+rel+':'+k)
    d[k]=v
   return d
  json.loads(p.read_bytes(),object_pairs_hook=pairs);jsonCount+=1
links=[];bad=[];historical=[];index=json.loads((P/'e02-raw-archive-index.json').read_bytes());archiveFiles={e['original']['path']:e['original'] for e in index['members']}
history='docs/decisions/evidence/e02-ordinary-client-resume-r1/source-docs-r10-before-current-profile/SUPERVISOR.md'
for rel in paths:
 p=R/rel
 if p.suffix!='.md':continue
 for dest in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^\s\)]+)(?:\s+[^\)]*)?\)',p.read_text()):
  dest=dest.strip('<>');u=urllib.parse.urlsplit(dest)
  if u.scheme or not u.path:continue
  origin=R/'experiments/prototypes/e02_ordinary_client_v1/SUPERVISOR.md' if rel==history else p
  q=(origin.parent/urllib.parse.unquote(u.path)).resolve()
  if not q.is_relative_to(R):continue
  t=q.relative_to(R).as_posix();ok=t in tracked or any(k.startswith(t.rstrip('/')+'/') for k in tracked)
  row=dict(source=rel,target=t,existsInIndex=ok)
  if rel==history:
   assert str(q) in archiveFiles and q.is_file();raw=q.read_bytes();d=archiveFiles[str(q)];assert len(raw)==d['bytes'] and hashlib.sha256(raw).hexdigest()==d['sha256'];row.update(originalOrigin=str(origin.relative_to(R)),preservedInRawArchive=True);historical.append(row)
  else:
   links.append(row)
   if not ok:bad.append(row)
assert not bad,bad
archiveResults=[]
for index in sorted(P.glob('*-index.json')):
 v=json.loads(index.read_bytes())
 if 'archive' not in v:continue
 arc=Path(v['archive']['path']);raw=arc.read_bytes();assert len(raw)==v['archive']['bytes'] and hashlib.sha256(raw).hexdigest()==v['archive']['sha256']
 expected={e['archivePath']:e['original'] for e in v.get('members',v.get('included',[]))};seen=set()
 with tarfile.open(arc,'r:gz') as tf:
  for m in tf:
   assert m.name in expected and m.name not in seen and m.isfile() and not m.issym() and not m.islnk() and m.name.startswith('repository/') and '..' not in Path(m.name).parts
   d=expected[m.name];assert m.size==d['bytes'] and m.mode==0o600 and m.uid==m.gid==m.mtime==0
   h=hashlib.sha256();n=0;stream=tf.extractfile(m)
   while b:=stream.read(1048576):h.update(b);n+=len(b)
   assert n==d['bytes'] and h.hexdigest()==d['sha256'];seen.add(m.name)
 assert set(expected)==seen
 archiveResults.append(dict(index=index.name,members=len(seen),archiveSha256=v['archive']['sha256'],allMatch=True))
report=dict(schema='nbdp-publication-checkpoint-validation-v1',actor='/root',selectedFiles=len(paths),jsonSyntaxDuplicateKeyChecked=jsonCount,activeRelativeLinksChecked=len(links),unresolvedActiveLinks=bad,historicalSourceLinkContext=historical,archives=archiveResults,whitespace=dict(allStagedFilesExit=0,rawUnifiedPatchPreservation='Two raw patches retain their original blank context markers in exact archives; duplicate normal-tree copies omitted without modifying originals.'),earlierValidationAttempt='Initial active-link scan treated one byte-identical historical source copy as current navigation; failed before archive scan or report publication. Its original-origin referent is now independently checked against raw archive membership, without altering source evidence.',scope='Serialization/archive/index/publication validation only; not experiment execution or PASS.',baselineHead=subprocess.check_output(G+['rev-parse','HEAD']).decode().strip(),branch=subprocess.check_output(G+['branch','--show-current']).decode().strip())
f=P/'checkpoint-current-validation.json';assert not f.exists();f.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
