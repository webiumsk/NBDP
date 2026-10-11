#!/usr/bin/env python3
"""Read-only project workflow validation; never executes NBDP experiments."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
import hashlib,json,re,tomllib
ROOT=Path(__file__).resolve().parent.parent
errors=[]
def require(ok,message):
    if not ok:errors.append(message)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def anchors(path):
    text=re.sub(r'```[^\n]*\n.*?```','',path.read_text(),flags=re.S)
    result=set(re.findall(r'<a\s+(?:id|name)=["\x27]([^"\x27]+)',text));seen={}
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',text,re.M):
        slug=re.sub(r'[^\w\-\s]','',title.lower()).replace(' ','-');n=seen.get(slug,0);seen[slug]=n+1;result.add(slug+('-'+str(n) if n else ''))
    return result
config=tomllib.loads((ROOT/'.codex/config.toml').read_text())
require(config.get('agents',{}).get('enabled') is True,'agents.enabled must remain true')
require(config.get('agents',{}).get('max_concurrent_threads_per_session')==5,'preserved concurrency preference changed')
require(config.get('features',{}).get('multi_agent') is True,'multi_agent feature missing')
require(not any(k in config for k in ['model','model_provider','approval_policy','mcp_servers','projects','hooks']),'unexpected global-like project override')
roles={}
for path in sorted((ROOT/'.codex/agents').glob('*.toml')):
    v=tomllib.loads(path.read_text());name=v.get('name');require(name not in roles,'duplicate agent '+str(name));roles[name]=path.name
    require(all(isinstance(v.get(k),str) and v[k].strip() for k in ('name','description','developer_instructions')),str(path)+': required agent field missing')
    require(not any(k in v for k in ('model','model_provider','approval_policy')),'agent overrides inherited defaults '+str(name))
    if name in ('researcher','security','qa'):require(v.get('sandbox_mode')=='read-only',str(name)+': reviewer default must be read-only')
require(set(roles)=={'researcher','architect','security','implementer','qa'},'specialist set incomplete')
skills=[]
for p in sorted((ROOT/'.agents/skills').glob('*/SKILL.md')):
    text=p.read_text();front=re.match(r'^---\n(.*?)\n---\n',text,re.S);require(bool(front),str(p)+': frontmatter missing')
    if not front:continue
    require(bool(re.search(r'^name:\s*'+re.escape(p.parent.name)+r'\s*$',front[1],re.M)),str(p)+': name mismatch')
    require(bool(re.search(r'^description:\s*\S',front[1],re.M)),str(p)+': description missing')
    require('[TODO' not in text,str(p)+': unfinished scaffold');skills.append(p.parent.name)
    ui=p.parent/'agents/openai.yaml'
    if ui.exists():require('$'+p.parent.name in ui.read_text(),str(ui)+': invocation example mismatch')
require(set(skills)=={'protocol-review','project-resume','research-evidence','experiment-gates','review-handoff'},'skill set incomplete')
manifest=json.loads((ROOT/'docs/development/workflow-baseline.json').read_text())
for rel,expected in manifest['preserved_evidence_sha256'].items():require(sha(ROOT/rel)==expected,'protocol evidence changed '+rel)
for rel,expected in manifest['preserved_prefix_sha256'].items():
    data=(ROOT/rel).read_bytes();require(len(data)>=expected['bytes'] and hashlib.sha256(data[:expected['bytes']]).hexdigest()==expected['sha256'],'original content overwritten '+rel)
md=[ROOT/'AGENTS.md',ROOT/'docs/PROJECT_STATE.md',ROOT/'docs/ROADMAP.md',*sorted((ROOT/'docs/development').glob('*.md')),*sorted((ROOT/'.agents/skills').glob('*/SKILL.md'))]
for p in md:
    text=p.read_text();require(sum(x.startswith('```') for x in text.splitlines())%2==0,str(p)+': unmatched fence')
    visible=re.sub(r'```[^\n]*\n.*?```','',text,flags=re.S)
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',visible):
        u=urlsplit(target.strip().strip('<>'))
        if u.scheme:continue
        dest=(p.parent/unquote(u.path)).resolve() if u.path else p;require(dest.exists(),str(p)+': missing link '+target)
        if u.fragment and dest.exists() and dest.is_file() and dest.suffix=='.md':require(unquote(u.fragment) in anchors(dest),str(p)+': missing anchor '+target)
register=(ROOT/'docs/research/architecture-risk-register.md').read_text()
for q in ('Q01','Q08','Q13','Q15','Q27'):
    section=register.split('### '+q+'\n',1)[1].split('\n### ',1)[0];require('**Classification:** BLOCKER' in section,q+' must remain blocker')
print(json.dumps({'status':'FAIL' if errors else 'PASS','roles':roles,'skills':skills,'preserved_evidence_files':len(manifest['preserved_evidence_sha256']),'preserved_original_prefixes':len(manifest['preserved_prefix_sha256']),'markdown_files':len(md),'errors':errors},indent=2));raise SystemExit(bool(errors))
