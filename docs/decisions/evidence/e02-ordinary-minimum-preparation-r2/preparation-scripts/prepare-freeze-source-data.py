from pathlib import Path
import ast,json,hashlib,difflib,re,copy,uuid,shutil
R=Path('/home/peterhorvath/apps/bitcoin/NBDP');P=R/'experiments/prototypes/e02_ordinary_minimum_v2';O=R/'experiments/prototypes/e02_ordinary_minimum_v1';D=R/'experiments/prototypes/e02_transport_query_diagnostic_v2';E=R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r2';OE=R/'docs/decisions/evidence/e02-ordinary-minimum-preparation-r1';DE=R/'docs/decisions/evidence/e02-transport-query-diagnostic-preparation-r2'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def read(p):return json.loads(p.read_bytes())
# Preserve exact source-only preparation programs; no module/SDK/runtime execution.
(E/'preparation-scripts').mkdir(exist_ok=True)
for n in ['prepare','integrate','tighten']:
 shutil.copyfile('/tmp/nbdp-producer2-'+n+'.py',E/'preparation-scripts'/('prepare-'+n+'-source-data.py'))
# Exact configurations are DATA-equivalent to materialize(), not calls into worker.
tree=ast.parse((P/'supervisor.py').read_text());sourceFn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_pins')
names=ast.literal_eval(sourceFn.body[0].value.generators[0].iter)
sourcePins=[pin(P/name) for name in names]
configs=[]
for role in ['incoming','archive']:
 config=read(OE/('proposed-'+role+'-run-config.json'))
 config.update(schema='e02-ordinary-minimum-role-runtime-plan-v2',scope='E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY',profileId='e02-ordinary-minimum-rs-two-role-v2',runId=uuid.uuid4().hex,sourceAndDependencyPins=sourcePins,state='PINNED_CANDIDATE_REQUIRES_SEPARATE_REVIEW_AND_RELEASE')
 save(E/('proposed-'+role+'-run-config.json'),config);configs.append(pin(E/('proposed-'+role+'-run-config.json')))
# Whole Python AST and explicit function-level comparison; namespace-only changes
# are classified separately, never asserted to be literal byte identity.
asts=[];partitions=[]
repls=[('e02_ordinary_minimum_v1','e02_ordinary_minimum_v2'),('e02-ordinary-minimum-v1','e02-ordinary-minimum-v2'),('e02-ordinary-minimum-rs-two-role-v1','e02-ordinary-minimum-rs-two-role-v2'),('E02_ORDINARY_MINIMUM_RS_TWO_ROLE_WINDOW_ONLY','E02_ORDINARY_MINIMUM_RS_TWO_ROLE_V2_WINDOW_ONLY')]
for n in ['ordinary-minimum-role-runtime-plan','ordinary-minimum-role-release','ordinary-minimum-role-supervisor-result','ordinary-minimum-fixture-plan','ordinary-minimum-ui-plan','ordinary-minimum-profile-plan','minimum-prepared','minimum-role-driver-result','minimum-transport','minimum-validated-wire-record','minimum-publish-intent','minimum-publication-window','minimum-producer-validation','minimum-stage-publication','minimum-fixture-command']:
 repls.append(('e02-'+n+'-v1','e02-'+n+'-v2'))
def norm(v):
 for a,b in repls:v=v.replace(a,b)
 return v
for p in sorted(P.glob('*.py')):
 current=ast.parse(p.read_text());old=ast.parse((O/p.name).read_text()) if (O/p.name).exists() else ast.Module(body=[],type_ignores=[])
 before=ast.dump(old,indent=2,include_attributes=False);after=ast.dump(current,indent=2,include_attributes=False)
 (E/(p.name+'-typed-ast-before.txt')).write_text(before+'\n');(E/(p.name+'-typed-ast-after.txt')).write_text(after+'\n')
 (E/(p.name+'-typed-ast.diff')).write_text(''.join(difflib.unified_diff((before+'\n').splitlines(True),(after+'\n').splitlines(True),fromfile='original/'+p.name,tofile='producer2/'+p.name)))
 om={n.name:n for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};nm={n.name:n for n in current.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 funcs=[]
 for name in sorted(om.keys()|nm.keys()):
  a=ast.dump(om[name],include_attributes=False) if name in om else None;b=ast.dump(nm[name],include_attributes=False) if name in nm else None
  kind='UNCHANGED_AST' if a==b else 'VERSION_LITERALS_ONLY_AST' if a is not None and norm(a)==b else 'NEW' if a is None else 'REMOVED' if b is None else 'CHANGED_LOGIC_AST'
  funcs.append(dict(name=name,classification=kind))
 asts.append(dict(file=pin(p),functions=funcs))
save(E/'python-function-carry.json',dict(schema='e02-producer2-python-function-ast-carry-v1',normalization=repls,files=asts,limitation='AST excludes source locations only; namespace literal normalization is explicit. Changed supervisor execution/inventory/source staging does not inherit full runtime qualification.'))
# Full exact text diffs. Copied accepted modules get their own explicit origin.
originModules=['exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json']
lines=[]
for p in sorted(P.iterdir()):
 if not p.is_file():continue
 old=D/p.name if p.name in originModules else O/p.name
 before=old.read_text() if old.exists() else ''
 lines.extend(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile=str(old) if old.exists() else '/dev/null',tofile=str(p)))
(E/'full-source.diff').write_text(''.join(lines))
# Source-function body extractor, explicit lexical partition (NOT a JS AST).
def function_text(source,name):
 m=re.search(r'(?:(?:export|async)\s+)*function\s+'+re.escape(name)+r'\s*\(',source)
 if not m:raise ValueError(name)
 start=m.start();i=source.index('{',m.end());level=0;quote=None;escape=False;comment=None;j=i
 while j<len(source):
  c=source[j];n=source[j:j+2]
  if comment=='line':
   if c=='\n':comment=None
  elif comment=='block':
   if n=='*/':comment=None;j+=1
  elif quote:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c==quote:quote=None
  elif n=='//':comment='line';j+=1
  elif n=='/*':comment='block';j+=1
  elif c in "'\"`":quote=c
  elif c=='{':level+=1
  elif c=='}':
   level-=1
   if level==0:return source[start:j+1]
  j+=1
 raise ValueError('Unclosed source function '+name)
old=(O/'fixture.mjs').read_text();new=(P/'fixture.mjs').read_text()
jsCarry=[]
for name in ['matchesFilter','matchingSubscription','currentGeneration','publicationGenerationMatches','roleSpec','stageSpec','exactInnerShape','attemptLineageMatches','stageDeliveryAllowed','replayBinding','selectedEvent','selectedStage','gate','invalidatePublication','qualifiedDelivery','prepared','prepare','validateActual']:
 a=function_text(old,name);b=function_text(new,name)
 jsCarry.append(dict(name=name,classification='BYTE_IDENTICAL_FUNCTION' if a==b else 'EXPLICIT_VERSION_LITERALS_ONLY' if norm(a)==b else 'CHANGED_SOURCE',beforeSha256=hashlib.sha256(a.encode()).hexdigest(),afterSha256=hashlib.sha256(b.encode()).hexdigest()))
a=function_text(old,'check');b=function_text(new,'guardCheck');oldbody=a[a.index('{'):];newbody=b[b.index('{'):]
assert oldbody==newbody
save(E/'javascript-function-source-carry.json',dict(schema='e02-producer2-javascript-lexical-function-carry-v1',method='Balanced source function slices excluding quoted strings/comments; NOT a JavaScript AST/parser/interoperability result',functions=jsCarry,originalGuardCoreBodyByteIdentical=True,guardCoreBodySha256=hashlib.sha256(oldbody.encode()).hexdigest(),textualCheckCount=dict(oldFixtureIncludingDefinition=len(re.findall(r'\bcheck\(',old)),newFixtureIncludingDefinition=len(re.findall(r'\bcheck\(',new)),acceptedExchangeCalls=len(re.findall(r'\bcheck\(',(P/'exchange.mjs').read_text()))),guardCountMeaning='Original38 call sites retained: new33 fixture call sites +5 accepted exchange positions. This source count alone is not authority/runtime proof.'))
# Guard/source preservation and component carry are evidence limits, not grants.
prior1=read(OE/'subject.json');priorD=read(DE/'subject.json')
oldPins=[*prior1['sources'],*priorD.get('source',priorD.get('sources',[]))] if isinstance(priorD.get('source',priorD.get('sources',[])),list) else prior1['sources']
# Every original prototype regular file also protected independent of descriptor layout.
protected=[pin(p) for root in [O,D] for p in sorted(root.iterdir()) if p.is_file()]
save(E/'protected-old-source-pins.json',dict(schema='e02-producer2-protected-old-source-pins-v1',files=protected,originalProducerSubject=pin(OE/'subject.json'),acceptedDiagnosticSubject=pin(DE/'subject.json'),note='Read-only old files preserved, no original retargeting.'))
modules=[]
for name in originModules:
 a=pin(D/name);b=pin(P/name);assert a['sha256']==b['sha256'] and a['bytes']==b['bytes'];modules.append(dict(original=a,current=b,classification='BYTE_IDENTICAL'))
host=[]
for name in ['dependency_relative','dependency_snapshot','verify_dependency_inventory']:
 def get(root):
  s=(root/'supervisor.py').read_text();t=ast.parse(s);n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name);return ast.get_source_segment(s,n)
 a=get(D);b=get(P);assert a==b;host.append(dict(name=name,sourceSha256=hashlib.sha256(a.encode()).hexdigest(),classification='BYTE_IDENTICAL_FUNCTION_AND_AST'))
save(E/'component-carry-matrix.json',dict(schema='e02-producer2-component-evidence-carry-v1',state='PROPOSED_SCOPE_MAPPING_REQUIRES_ACTUAL_INDEPENDENT_REVIEW_NOT_AUTHOR_ACCEPTANCE',modules=modules,hostFunctions=host,ordinaryBaseline=dict(source=pin(OE/'subject.json'),actualControls=pin(OE/'current-controls-r1/results-r1/subject.json'),actualAcceptance=pin(OE/'current-controls-r1/results-r1/acceptance.json'),bridgeAcceptance=pin(R/'docs/decisions/evidence/e02-minimum-runtime-preparation-r1/bridge-acceptance.json'),scope='Old29cleanup/49UI/21minimumUI/27filter/43rolemetadata definitions; only unchanged functions or explicit version-literal-normalized methods may carry. No full producer2/runtime acceptance, no new execution counts.'),diagnosticBaseline=dict(source=pin(DE/'subject.json'),actualControls=pin(DE/'current-controls-r1/results-r1/subject.json'),actualAcceptance=pin(DE/'current-controls-r1/results-r1/acceptance.json'),runtimeAcceptance=pin(R/'docs/decisions/evidence/e02-transport-query-baseline-runtime-r1/acceptance.json'),scope='Prior18 host/DATA,27 exchange/writer models and6 guest inventory controls; reuse only exact modules/three host functions. No new executions or ordinary-client rows.'),unchangedGuard=dict(current=pin(P/'lease_guard.py'),original=pin(O/'lease_guard.py'),scope='Prior exact29guard scope referenced by original subject/bridge; no new guard test execution.'),functionProofs=[pin(E/'python-function-carry.json'),pin(E/'javascript-function-source-carry.json')],newControlsRequireCurrentResultReview=True,noFailedRowDonation=True))
node=Path('/home/peterhorvath/.nvm/versions/node/v22.18.0/bin/node');python=Path('/home/peterhorvath/.miniforge3/bin/python3.13')
# Freeze meaningful new definitions only; do not repeat unchanged tests for counts.
nodeNames=re.findall(r"await test\('([^']+)'",(P/'test_observation_model.mjs').read_text())
scopes=[]
for name,file,count,kind in [('observation-model','test_observation_model.mjs',20,'SYNTHETIC_FS_SOCKET_GUARD_ONLY'),('public-identity-metadata','test_public_identity_metadata.py',8,'PUBLIC_FIXED_FORMAT_DATA_ONLY'),('producer2-source-wiring','test_producer2_source.py',7,'SOURCE_AST_AND_PIN_WIRING_ONLY')]:
 argv=[str(node),str(P/file)] if file.endswith('.mjs') else [str(python),'-I','-B',str(P/file)]
 actual=len(nodeNames) if file.endswith('.mjs') else len([n for n in ast.walk(ast.parse((P/file).read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]);assert actual==count,(file,actual,count)
 names=nodeNames if file.endswith('.mjs') else [n.name for n in ast.walk(ast.parse((P/file).read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
 scopes.append(dict(name=name,argv=argv,plannedChecks=count,namedCases=names,meaning=kind,timeoutSeconds=60,stdoutRetentionBytes=1048576,stderrRetentionBytes=262144,outputShape='JSON_SINGLE_LINE_CLOSED_SCHEMA_OK_TRUE_CHECKS_CASES_SCOPE' if file.endswith('.mjs') else 'UNittest_NATURAL_EXIT0_RAN_EXACT_COUNT_OK_NO_SKIP',executed=False))
save(E/'execution-control-plan.json',dict(schema='e02-producer2-changed-data-control-plan-v1',state='DEFINITIONS_ONLY_NOT_EXECUTED_NO_EXECUTION_GRANT',actor='/root/ordinary_api35_source',sourceReviewPrerequisite='Actual same frozen subject independent QA/security decisions; reviewed fixed capture reuse; root explicit once-only release. Author cannot self-approve.',interpreters=dict(node=pin(node),python=pin(python)),configurations=configs,separateScopes=scopes,scopeCountsAreSeparate=True,totalDefinedChecks=35,oldSuitesNotRerun=['29guard','29cleanup','49UI','21minimumUI','27fixture','43minimumfixture','18diagnostic-host','27diagnostic-model','6diagnostic-inventory'],requiredCapture='Reuse existing finite capture actual-source adaptation only. Exact source/closure/config/interpreter/input/review/root-ack before/after; private0600 raw;60s scope; actual natural exit/EOF/reap/error/signal/force; stop firstfailure/no retry/fix. Original outer API objects saved separately with unmodified fields. Retention caps apply after capture, no streaming-memory claim.',excluded=['prepared primary/runtime module main','sign/encrypt/decrypt/curve/native validation','actual guard/lease/grant','SDK/Android/Docker/services/network','consumer3/completion2 implementation or execution'],syntaxOnly=pin(E/'syntax-only-checks.json'),componentCarry=pin(E/'component-carry-matrix.json')))
# Authority/current frozen input graph; no mutable state docs as code dependency.
authorities=[R/'docs/decisions/evidence/e02-transport-query-baseline-analysis-r1/source-next-step-decision.json',R/'docs/decisions/evidence/e02-ordinary-minimum-profile-proposal-r1/coordinator-adoption.json',R/'docs/decisions/evidence/e02-transport-query-baseline-runtime-r1/acceptance.json',R/'docs/decisions/evidence/e02-ordinary-minimum-runtime-r1/acceptance.json',R/'docs/decisions/evidence/e02-ordinary-minimum-relay-diagnosis-r1/subject.json']
fixture=read(P/'fixture-plan.json');oldControlInputs=read(OE/'control-inputs.json')
save(E/'control-inputs.json',dict(schema='e02-producer2-source-data-input-closure-v1',authorities=[pin(p) for p in authorities],newSources=[pin(p) for p in sorted(P.iterdir()) if p.is_file()],configurations=configs,externalFixturePins=[{**d,'path':d['source']} for d in [*fixture['pins'].values()]],dependencyFiles=fixture['dependencyFiles'],dependencyTree=pin(P/'dependency-tree.json'),oldAcceptedInputClosure=pin(OE/'control-inputs.json'),publicFormatData=pin(E/'public-scalar-format-data.json'),newOracleProvenance=pin(E/'oracle-provenance.json'),protectedOldSource=pin(E/'protected-old-source-pins.json'),mutableProjectStatePinned=False,meaning='Exact descriptors are SOURCE/current DATA prerequisites; no authority/state freshness or runtime success is fabricated. Controls only actually read declared source/metadata/old inputs and fake operands. Runtime SDK434/guard522/image inputs remain separately verified by config/supervisor/root grant.'))
# Existing imported archived UI input paths remain unchanged in inherited tests;
# they are not actual new35-scope inputs and are not rerun.
save(E/'next-consumer-contract-inputs.json',dict(schema='e02-producer2-next-consumer3-source-inputs-v1',state='CONSUMER3_NOT_IMPLEMENTED_NO_REAL_WINDOWS',profileId='e02-ordinary-minimum-rs-two-role-v2',typedContract=pin(P/'EXPORT-CONTRACT.md'),fixture=pin(P/'fixture.mjs'),producerPlan=pin(P/'fixture-plan.json'),roleConfigs=configs,authority=pin(authorities[0]),additiveOperands=['StagePublication.observation bounded phase-range/state and explicit mutable stream paths','Final whole-window Pins for raw proxy and phase streams, full late-history (no per-stage copy pretending final)','Shared healthy budget sums/one16MiB ceiling, checked count prefix versus UNKNOWN physical persistence','Per-exchange required immutable sent/outcome files, exact raw context→original guard→raw row→protocol parse ordering','Exact existing publication attempt/EOSE generation, genuine APP-vs-relay-query origin, fresh helper GUI exports/attribution','Real actual external tool API objects distinct from child journals; actual operator/nonoperator author/session review joins','Mandatory preimport/operation/controller/host-end full tree checks; optional signal/fatal final-state is honest, never fabricated'],preserve=['two fresh complete role windows/five actual exports/three note contexts/two original rumor IDs','historical frozen rumor/randomized wrap timestamps not forced into lease','original six fields/ordered privatepB/archiveouterA/identical/fresh wrap replay','all22 current independent primary and canonical prerequisites','v1 failure whole-window0, raw PARTIAL/mandatoryskip and canonical E04/E06 gates unchanged'],remainingGenuinePrerequisites=['actual independent producer2 SOURCE reviews','current35 pure controls and independent result reviews before any producer2 activation','sequential separately versioned strict consumer3 then completion2 SOURCE/controls/reviews','fresh root role admission/release(s) and exact SDK/APK/helper/images/current source checks','actual incoming then archive complete qualified windows and whole accepted consume/current primary reconciliation'],noProductOwnerInputNeeded=True))
# Freeze index/subject is completed later after README and this script are saved.
print(json.dumps(dict(configurations=configs,runtimeSourceCount=len(sourcePins),newControls=[(x['name'],x['plannedChecks']) for x in scopes],pythonChanged=[(x['file']['path'].split('/')[-1],[(f['name'],f['classification']) for f in x['functions'] if f['classification'] not in ['UNCHANGED_AST']]) for x in asts if x['file']['path'].endswith(('supervisor.py','android_driver.py'))],javascriptCarry=jsCarry),indent=2))
