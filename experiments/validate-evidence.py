#!/usr/bin/env python3
"""Repository documentation/evidence checks only; no protocol or production code."""
from pathlib import Path
from collections import Counter
from urllib.parse import unquote,urlsplit
import hashlib,json,re
ROOT=Path(__file__).resolve().parent.parent
LAB=ROOT/'experiments'
errors=[]
def check(ok,why):
    if not ok: errors.append(why)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(s):return re.sub(r'```[^\n]*\n.*?```','',s,flags=re.S)
def anchors(p):
    s=clean(p.read_text());found=set(re.findall(r'<a\s+(?:name|id)=["\x27]([^"\x27]+)',s));counts=Counter()
    for h in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',s,re.M):
        h=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',h)
        slug=re.sub(r'[^\w\-\s]','',h.lower()).replace(' ','-')
        suffix='' if counts[slug]==0 else '-'+str(counts[slug]);counts[slug]+=1;found.add(slug+suffix)
    return found
md=list((ROOT/'docs').rglob('*.md'))+list((ROOT/'adr').rglob('*.md'))+list(LAB.glob('README.md'))+list((LAB/'docker').glob('*.md'))+list((LAB/'shared').glob('*.md'))+list((LAB/'fixtures').glob('*.md'))+list(LAB.glob('e*/README.md'))+list((LAB/'results').glob('*.md'))
for p in md:
    s=p.read_text();check(sum(l.startswith('```') for l in s.splitlines())%2==0,f'{p}: unmatched fence')
    check(s.startswith('# '),f'{p}: missing title')
    text=clean(s)
    targets=re.findall(r'\[[^\]]*\]\(([^)]+)\)',text)+re.findall(r'^\[[^\]]+\]:\s*(\S+)',text,re.M)
    for target in targets:
        target=target.strip().split(' "',1)[0].strip('<>');u=urlsplit(target)
        if u.scheme or target.startswith('//'):continue
        dest=(p.parent/unquote(u.path)).resolve() if u.path else p
        check(dest.exists(),f'{p.relative_to(ROOT)}: missing target {target}')
        if u.fragment and dest.exists() and dest.is_file() and dest.suffix=='.md':check(unquote(u.fragment) in anchors(dest),f'{p.relative_to(ROOT)}: missing anchor {target}')
register=(ROOT/'docs/research/architecture-risk-register.md').read_text()
check(set(re.findall(r'^### (Q\d\d)$',register,re.M))=={f'Q{i:02}' for i in range(1,28)},'canonical Q01–Q27 headings missing/extra')
counts=Counter(re.findall(r'^- \*\*Classification:\*\* (DECIDED|RFC_REQUIRED|EXPERIMENT_REQUIRED|BLOCKER)$',register,re.M))
check(dict(counts)=={'DECIDED':3,'RFC_REQUIRED':12,'EXPERIMENT_REQUIRED':7,'BLOCKER':5},'classification counts changed')
for q in ('Q01','Q08','Q13','Q15','Q27'):
    section=register.split('### '+q+'\n',1)[1].split('\n### ',1)[0];check('**Classification:** BLOCKER' in section,q+' blocker closed')
plan=(ROOT/'docs/research/required-experiments.md').read_text();check(set(re.findall(r'^### (E\d\d)$',plan,re.M))=={f'E{i:02}' for i in range(1,17)},'canonical E01–E16 headings missing/extra')
for i in range(1,7):
    id=f'E{i:02}';r=json.loads((LAB/'results'/f'{id}.json').read_text());report=(LAB/'results'/f'{id}.md').read_text();section=plan.split('### '+id+'\n',1)[1].split('\n### ',1)[0]
    mapping=re.search(r'Canonical questions:\*\* ([^\n]+)',section).group(1).rstrip('.')
    check(f'Canonical questions: {mapping}.' in report,id+' canonical Q mapping mismatch')
    failures=[x for x in r['tests'] if not x['ok']];mandatory=any(x['mandatory'] for x in r['skipped'])
    expected='FAIL' if failures else ('PARTIAL' if r['tests'] else 'NOT EXECUTED') if mandatory else 'PASS'
    check(r['status']==expected,id+' status does not follow actual checks')
    check(f'**Status: {r["status"]}**' in report,id+' report/machine status mismatch')
    check(f'**{r["duration_ms"]} ms**' in report,id+' report duration mismatch')
    check(f'**{r["exit_status"]}**' in report,id+' report exit status missing')
    for source,h in r['source_sha256'].items():check((LAB/source).exists() and sha(LAB/source)==h,id+' stale source '+source)
for id in ('E04','E06'):
    r=json.loads((LAB/'results'/f'{id}.json').read_text());check(r['status']=='NOT EXECUTED' and not r['tests'],id+' dependency gate bypassed')
manifest=json.loads((LAB/'fixtures/research-input-manifest.json').read_text())
for p in manifest['unchanged_research_reports']:check(sha(ROOT/p)==manifest['original_sha256'][p],'original research evidence changed '+p)
result={'status':'FAIL' if errors else 'PASS','markdown_files':len(md),'Q_ids':27,'E_ids':16,'experiment_reports':6,'classification_counts':dict(counts),'checks':['Markdown titles/fences','relative paths and Markdown anchors','canonical Q/E IDs and experiment Q mappings','report/machine status, duration, process exit','current source/config/lock hashes','blocked dependent tests','original research hashes'],'errors':errors}
(LAB/'results/documentation-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
