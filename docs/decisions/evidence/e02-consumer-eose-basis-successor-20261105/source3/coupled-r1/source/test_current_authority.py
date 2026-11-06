"""SOURCE4 definitions: full ready current authority DATA, never real approvals.

Mock Root/review/API records are memory-only and visibly synthetic. Actual
current CODE bytes and the frozen partition are used; validators are not patched.
"""
import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import consumer,probe_adapter
from strict import Refusal,json_bytes
from test_parent_allocation import MemoryFiles

CURRENT_R8_FIXTURE = {'source': {'path': '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r10/subject.json', 'bytes': 65372, 'sha256': '20f3740d34dfac74d808857315ca338c49a836732bd95bf5315365fe94422855'}, 'sourceAcceptance': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-current-controller-source-review-20261105/r10/acceptance.json', 'bytes': 1216, 'sha256': 'a06e93b82b3dcc32879d8584f463fc1e4fa42fefa843f2ee85a4487ed2829081'}, 'controlAcceptance': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-controller-r10-model178-data-review-20261105/acceptance.json', 'bytes': 2125, 'sha256': '7be2187f5dfbabd8959e7fb75d0817b824921467b05fbe5626d8a2f5cd6327b2'}}
HISTORICAL_R5_FIXTURE = {'source': {'path': '/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r5/subject.json', 'bytes': 22404, 'sha256': '6259e4dae59b27839378ec03c96056c5efab1c21132ac0eda451dbed8d8e4a03'}, 'sourceAcceptance': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-controller-r5-source-acceptance-20261029/acceptance.json', 'bytes': 1217, 'sha256': '378c47f2db9bb2cc445a418126c7f6d1d3faf7af29ae953d3966eb85723d6076'}, 'controlAcceptance': {'path': '/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-probe-controller-r5-model123-capture-r2-20261029/acceptance.json', 'bytes': 2125, 'sha256': 'e3938c437c8bfc80b58541df05e2eb7a6a1aa5a9cadd49b9ad036ce54ea15483'}}

def current_controller_expectations():
    """Selected immutable current Source/plan; no revision or count guess."""
    descriptor=CURRENT_R8_FIXTURE['source'];raw=Path(descriptor['path']).read_bytes()
    assert len(raw)==descriptor['bytes'] and hashlib.sha256(raw).hexdigest()==descriptor['sha256']
    source=json.loads(raw);descriptor=source['controlPlan'];raw=Path(descriptor['path']).read_bytes()
    assert len(raw)==descriptor['bytes'] and hashlib.sha256(raw).hexdigest()==descriptor['sha256']
    return source,json.loads(raw)

class ReadyAuthorityModel(MemoryFiles):
    def __init__(self):
        super().__init__();self.named={};self.modes={};self.here=Path(consumer.__file__).resolve().parent
        # Only memory-local selector records are issued by this fixture. The
        # repository's actual component basis/ordinary DATA remain unissued.
        self.synthetic_ordinary_basis()
        self.source=self.copy_file(self.here/'subject.json')
        self.named['consumer-source']=self.source
        source=self.doc(self.source);self.plan=self.copy_file(source['controlPlan']['path'])
        for p in source['sources']:self.copy_file(p['path'])
        self.copy_file(source['inputManifest']['path'])
        inputs=self.doc(source['inputManifest'])['fixedSourceAndCurrentDataOperands']
        # Other retained upstream operands are modeled snapshot descriptors only;
        # the separate current286 DATA control inspects their actual proof graph.
        self.copy_file(consumer.CURRENT_CONSUMER_ACCEPTANCE_CONTRACT['path'])
        self.contract=self.doc(consumer.CURRENT_CONSUMER_ACCEPTANCE_CONTRACT)
        self.groups=self.doc(self.plan)['groups'];self.counts=[g['count'] for g in self.groups];self.total=sum(self.counts)
        self.source_reviews=self.reviews('source',self.source,self.contract['source']['reviewDecision'])
        sa=dict(self.contract['source']['literals'],subject=self.source,reviews=self.source_reviews,
            producerSource=consumer.CURRENT_PRODUCER,producerControlAcceptance=consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE,
            runtimeSourceCount=len(consumer.RUNTIME_FILES),sourceCount=source['sourceCount'],modelsDefined=self.total)
        source_acceptance=self.record('source-acceptance',sa)
        triple=self.current_controller()
        ctrl=triple['controllerSource'];ctrl_sa=triple['controllerSourceAcceptance'];ctrl_da=triple['controllerControlDataAcceptance']
        collector=self.record('collector-source',dict(schema='e02-probe-root-custody-collector-source-subject-v1',codeOnly=True,authors=['/root/SYNTHETIC_COLLECTOR_CREATOR']))
        collector_sa=self.record('collector-source-acceptance',dict(actor='/root',subject=collector))
        collector_data=self.record('collector-data',dict(authors=['/root/SYNTHETIC_COLLECTOR_CREATOR'],operators=['/root/SYNTHETIC_MODEL_OPERATOR']))
        collector_da=self.record('collector-data-acceptance',dict(actor='/root',subject=collector_data))
        release=self.record('helper-release',dict(authors=['/root/SYNTHETIC_MODEL_OPERATOR'],operators=['/root/SYNTHETIC_MODEL_OPERATOR']))
        probe=self.record('helper-data',dict(authors=['/root/SYNTHETIC_MODEL_OPERATOR'],operators=['/root/SYNTHETIC_MODEL_OPERATOR'],controllerSource=ctrl,controllerSourceAcceptance=ctrl_sa,controllerControlDataAcceptance=ctrl_da,collectorSourceAcceptance=collector_sa,collectorControlDataAcceptance=collector_da,rootRelease=release))
        probe_acceptance=self.record('helper-acceptance',dict(actor='/root',subject=probe))
        expected={p['path']:p for p in [*source['sources'],self.plan,source['inputManifest'],self.source,source_acceptance,*inputs]}
        rows=[dict(pin=p,mode=0o600,uid=1000,gid=1000,device='1',inode=str(i),mtimeNs='100',ctimeNs='100') for i,p in enumerate(expected.values(),1)]
        snapshot=dict(schema='e02-consumer6-current-inputs-v1',rows=rows)
        before=self.record('before',snapshot);after=self.record('after',copy.deepcopy(snapshot))
        recorded=[];origins=[];members=[before,after]
        for i,g in enumerate(self.groups):
            names=sorted(g['definitionNames'])
            output='\n'.join(method+' (__main__.'+name+') ... ok' for name in names for method in [name.split('.',1)[1]])
            output+='\n\n'+'-'*70+'\nRan '+str(g['count'])+' tests in 0.001s\n\nOK\n'
            request=consumer.current_control_request(g)
            api=dict(schema='e02-actual-tool-custody-v1',operator='/root/SYNTHETIC_MODEL_OPERATOR',launch=dict(toolName='tools.exec_command',actualArguments=request,unmodifiedResponse=dict(chunk_id='SYNTHETIC_NOT_REAL_API_'+str(i),wall_time_seconds=0.001,exit_code=0,output=output)),polls=[])
            origin=self.record('group-api-'+str(i),api);raw=self.record('group-output-'+str(i),output.encode())
            recorded.append(dict(name=g['name'],source=g['source'],count=g['count'],definitionNames=g['definitionNames'],request=request,originalToolOrigin=origin,rawOutput=raw,exitCode=0,scope='API_ONLY_MOCK_OR_READ_ONLY_MODELS_NO_TARGET_RUNTIME',innerPidReapEofAttested=False))
            origins.append(dict(group=g['name'],origin=origin));members.extend([origin,raw])
        api_index=self.record('api-index',dict(schema='e02-consumer6-control-api-index-v1',origins=origins))
        execution=self.record('execution',dict(schema='e02-consumer6-control-execution-v1',consumerSource=self.source,controlPlan=self.plan,groups=recorded,countsSeparate=self.counts,modelsExecuted=self.total,modelsPassed=self.total,modelsFailed=0,skipped=0,truncated=False,inputsBefore=before,inputsAfter=after,inputsUnchanged=True,scope='API_ONLY_MOCK_OR_READ_ONLY_MODELS_NO_TARGET_RUNTIME',innerPidReapEofAttested=False))
        members.extend([api_index,execution]);manifest=self.record('manifest',dict(schema='e02-consumer6-control-raw-manifest-v1',files=members,originalToolOrigin=api_index))
        data=self.record('control-data',dict(schema='e02-consumer6-current-control-data-subject-v1',authors=['/root/SYNTHETIC_MODEL_OPERATOR'],operators=['/root/SYNTHETIC_MODEL_OPERATOR'],consumerSource=self.source,consumerSourceAcceptance=source_acceptance,controlPlan=self.plan,producerSource=consumer.CURRENT_PRODUCER,producerControlAcceptance=consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE,execution=execution,originalToolOrigin=api_index,rawArtifactManifest=manifest,countsSeparate=self.counts,modelsDefined=self.total,modelsExecuted=self.total,modelsPassed=self.total,modelsFailed=0,skipped=0,truncated=False,inputsUnchanged=True,helperExecutions=0,dockerExecutions=0,ordinaryRoleExecutions=0,ordinaryRowsQualified=0))
        data_reviews=self.reviews('data',data,self.contract['data']['reviewDecision'])
        da=dict(self.contract['data']['literals'],subject=data,reviews=data_reviews,consumerSource=self.source,consumerSourceAcceptance=source_acceptance,controlPlan=self.plan,producerSource=consumer.CURRENT_PRODUCER,producerControlAcceptance=consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE,countsSeparate=self.counts,modelsDefined=self.total,modelsExecuted=self.total,modelsPassed=self.total)
        data_acceptance=self.record('data-acceptance',da)
        export=dict(path='/model/SYNTHETIC_EXPORT_NOT_REAL',bytes=1,sha256='a'*64)
        leaf=dict(schema='e02-consumer6-runtime-bindings-v2',actor='/root',producerSource=consumer.CURRENT_PRODUCER,producerSourceAcceptance=consumer.CURRENT_PRODUCER_SOURCE_ACCEPTANCE,producerControlData=consumer.CURRENT_PRODUCER_CONTROL_DATA,producerControlAcceptance=consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE,helperProbeData=probe,helperProbeAcceptance=probe_acceptance,controllerSource=ctrl,controllerSourceAcceptance=ctrl_sa,controllerControlDataAcceptance=ctrl_da,consumerSource=self.source,consumerSourceAcceptance=source_acceptance,consumerControlData=data,consumerControlAcceptance=data_acceptance,incomingWindow=export,archiveWindow=export,ordinaryExports=[export]*5,readiness=True,issued=True,executionAuthorized=False)
        self.record('leaf',leaf)
        self.component_basis_fixture(probe)

    def synthetic_ordinary_basis(self):
        """Metadata-only synthetic286 tuple over the genuine new producer Source.

        This never substitutes for the separately required actual capture DATA.
        The fixture exercises consumer joins; no capture/producer code is run.
        """
        producer=self.copy_expected(consumer.CURRENT_PRODUCER)
        self.copy_expected(consumer.CURRENT_PRODUCER_SOURCE_ACCEPTANCE)
        capture=self.record('component-new-capture',dict(schema='e02-producer4-control-capture-code-subject-v1',
            producerSource=producer,authors=['/root/SYNTHETIC_CAPTURE_CREATOR']))
        capture_acceptance=self.record('component-new-capture-acceptance',dict(actor='/root',subject=capture))
        admission=self.record('component-new-admission',dict(schema='e02-producer4-capture-admission-data-subject-v1',
            producerSource=producer,captureSource=capture,authors=['/root/SYNTHETIC_MODEL_OPERATOR'],
            operators=['/root/SYNTHETIC_MODEL_OPERATOR']))
        admission_acceptance=self.record('component-new-admission-acceptance',dict(actor='/root',subject=admission))
        joins=dict(producerSource=producer,producerSourceAcceptance=consumer.CURRENT_PRODUCER_SOURCE_ACCEPTANCE,
            countsSeparate=consumer.CURRENT_PRODUCER_CONTROL_COUNTS,captureSource=capture,
            captureSourceAcceptance=capture_acceptance,admissionDataAcceptance=admission_acceptance)
        data=self.record('component-new-control',dict(schema='e02-producer4-current-control-data-subject-v1',
            authors=['/root/SYNTHETIC_MODEL_OPERATOR'],operators=['/root/SYNTHETIC_MODEL_OPERATOR'],**joins))
        accepted=self.record('component-new-control-acceptance',dict(schema='e02-root-producer4-current-control-data-acceptance-v1',
            actor='/root',subject=data,modelsExecuted=286,modelsPassed=286,modelsFailed=0,
            helperExecutions=0,ordinaryRoleExecutions=0,ordinaryRowsQualified=0,runtimeAuthorized=False,
            executionAuthorized=False,**joins))
        for key,value in [('CURRENT_PRODUCER_CONTROL_DATA',data),('CURRENT_PRODUCER_CONTROL_ACCEPTANCE',accepted),
                          ('CURRENT_CAPTURE_SOURCE',capture),('CURRENT_CAPTURE_SOURCE_ACCEPTANCE',capture_acceptance),
                          ('CURRENT_ADMISSION_DATA_ACCEPTANCE',admission_acceptance)]:setattr(consumer,key,value)

    def component_basis_fixture(self,probe):
        """Copy a finite SOURCE/pure-control closure and build a synthetic basis.

        No actual helper subject, release, plan, result, Host/F/M4 or raw proof
        descriptor is followed. Root24 operands remain descriptors. Its subject
        and acceptance are replaced with the memory-only helper probe above.
        """
        template_pin=self.copy_expected(consumer.CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE)
        template=self.doc(template_pin);original=template['originalBasis'];base=original['producer']
        design_pin=self.copy_expected(consumer.CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE)
        design=self.doc(design_pin)
        # A finite list of typed Source/governance and pure-control metadata.
        for key in ('producerSourceAcceptance','producerData','producerDataAcceptance',
                    'producerCaptureSource','producerCaptureSourceAcceptance','producerAdmissionDataAcceptance'):
            self.copy_expected(base[key])
        admission=self.doc(base['producerAdmissionDataAcceptance']);self.copy_expected(admission['subject'])
        for source_pin in (base['producerSource'],consumer.CURRENT_PRODUCER):
            self.copy_expected(source_pin);source=self.doc(source_pin)
            for descriptor in source['sources']:self.copy_expected(descriptor)
            for descriptor in source['configurations'].values():self.copy_expected(descriptor)
        boundary=original['boundary']
        for descriptor in [boundary['controllerConstants'],boundary['guardManifest'],
                           *boundary['controllerRuntimeSources'],original['helperMethodSource'],
                           original['helperMethodControlAcceptance']]:self.copy_expected(descriptor)
        method_acceptance=self.doc(original['helperMethodControlAcceptance'])
        self.copy_expected(method_acceptance['subject'])
        # Reuse the frozen Root24 literals and original producer/controller
        # operands while replacing only the synthetic helper subject/reviews.
        helper_reviews=self.reviews('component-helper',probe,'ACCEPT_ONE_CURRENT_HELPER_PROBE_DATA_ONLY')
        original['root24ExpectedPinOperands']['subject']=probe
        original['root24ExpectedReviews']=helper_reviews
        root24=dict(original['root24ExpectedLiterals'],**original['root24ExpectedPinOperands'],reviews=helper_reviews)
        def replace_root(value):value.clear();value.update(root24)
        self.change('helper-acceptance',replace_root)
        original['helperDataAcceptance']=self.named['helper-acceptance']
        # New prior design receipts are explicitly synthetic test records. Their
        # subject pins this synthetic template, never the completed basis itself.
        template_pin=self.record('component-template',template)
        entry=self.record('component-design-entry',dict(schema='SYNTHETIC_COMPONENT_DESIGN_SOURCE',unissuedTemplate=template_pin))
        design_reviews=self.reviews('component-design',entry,'ACCEPT_HELPER_COMPONENT_BASIS_SOURCE_CONTRACT_ONLY')
        design.update(unissuedTemplate=template_pin,subject=entry,reviews=design_reviews)
        design_pin=self.record('component-design-acceptance',design)
        ordinary=consumer.ordinary_basis_expectations()
        facts,_,_,_,_=probe_adapter._component_source_verification(self,template,ordinary)
        pairs=[dict(name=row['name'],originalPin=row['originalPin'],originalMode='0o664',
                    newPin=row['newPin'],newMode='0o664') for row in facts['sourcePairs']]
        leaf=self.leaf();consumer_source=self.doc(leaf['consumerSource']);control=self.doc(leaf['consumerControlData'])
        union=set(consumer.CURRENT_CONTROL_ACTORS)|probe_adapter.source_actors(consumer_source)|probe_adapter.data_actors(control)
        union=probe_adapter.participant_union(self,self.doc(probe),union)
        union|={'/root',template['designAuthor']}
        def source_creators(value):
            result={value['author'],value['coordinator']}|set(value['sourceContributors'])
            for key in ('operators','sourcePreparationOperators','designContributors'):result.update(value.get(key,[]))
            if 'predecessorAuthor' in value:result.add(value['predecessorAuthor'])
            return result
        for source_pin,data_pin,capture_pin,admission_pin in (
            (base['producerSource'],base['producerData'],base['producerCaptureSource'],base['producerAdmissionDataAcceptance']),
            (ordinary['producerSource'],ordinary['producerControlData'],ordinary['captureSource'],ordinary['admissionDataAcceptance'])):
            union|=source_creators(self.doc(source_pin))|probe_adapter.data_actors(self.doc(data_pin))
            union.update(self.doc(capture_pin)['authors'])
            union|=probe_adapter.data_actors(self.doc(self.doc(admission_pin)['subject']))
        union|=source_creators(self.doc(original['controller']['controllerSource']))
        union.update(self.doc(boundary['controllerConstants'])['sourceContributors'])
        union|=source_creators(self.doc(original['helperMethodSource']))
        union|=probe_adapter.data_actors(self.doc(method_acceptance['subject']))
        controller_accepted=self.doc(original['controller']['controllerControlDataAcceptance'])
        union|=probe_adapter.data_actors(self.doc(controller_accepted['subject']))
        basis=copy.deepcopy(template)
        basis.update(actor='/root',issued=True,readiness=True,executionAuthorized=False,
            ordinarySuccessor=ordinary,sourcePairs=pairs,sourceVerification=facts,
            actorClosure=dict(schema='e02-helper-component-actor-closure-v1',participants=sorted(union)),
            sourceReviews=design_reviews,rootDisposition=design_pin,state='COMPLETED_SOURCE_COMPONENT_BASIS_ONLY')
        basis_pin=self.record('component-basis',basis)
        consumer.CURRENT_HELPER_COMPONENT_BASIS=basis_pin
        consumer.CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE=template_pin
        consumer.CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE=design_pin
        # Repin every dependent memory descriptor, including the Source anchor,
        # Source acceptance, snapshots, control DATA and final synthetic leaf.
        self.change('consumer-source',lambda value:value.update(helperComponentBasis=basis_pin,
            producerControlAcceptance=consumer.CURRENT_PRODUCER_CONTROL_ACCEPTANCE))

    def current_controller(self):
        # Exact accepted current R10 SOURCE and complete178 retained DATA are read-only
        # inputs. This copies bytes into a memory-only test graph; it issues no
        # helper/consumer/runtime authority. Any change() is synthetic DATA.
        source_pin=self.copy_expected(CURRENT_R8_FIXTURE['source'],'controller-source')
        source=self.doc(source_pin);self.copy_expected(consumer.HELPER_PRODUCER)
        for p in source['sources']:self.copy_expected(p)
        plan_pin=self.copy_expected(source['controlPlan'],'controller-plan')
        self.copy_expected(consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT)
        source_acceptance=self.copy_expected(CURRENT_R8_FIXTURE['sourceAcceptance'],'controller-source-acceptance')
        for role,p in zip(('qa','security'),self.doc(source_acceptance)['reviews']):
            self.copy_expected(p,'controller-source-'+role)
        data_acceptance=self.copy_expected(CURRENT_R8_FIXTURE['controlAcceptance'],'controller-data-acceptance')
        accepted=self.doc(data_acceptance)
        for role,p in zip(('qa','security'),accepted['reviews']):self.copy_expected(p,'controller-data-'+role)
        data_pin=self.copy_expected(accepted['subject'],'controller-data');data=self.doc(data_pin)
        for key,name in [('execution','controller-execution'),('inputsBefore','controller-before'),('inputsAfter','controller-after'),('rawArtifactManifest','controller-manifest'),('rootRelease','controller-model-release')]:
            self.copy_expected(data[key],name)
        for p in self.doc(data['rawArtifactManifest'])['files']:self.copy_expected(p)
        for i,row in enumerate(self.doc(data['execution'])['groups']):
            self.copy_expected(row['originalToolOrigin'],'controller-api-'+str(i))
            self.copy_expected(row['rawOutput'],'controller-output-'+str(i))
        return dict(controllerSource=source_pin,controllerSourceAcceptance=source_acceptance,controllerControlDataAcceptance=data_acceptance)

    def copy_expected(self,descriptor,name=None):
        actual=self.copy_file(descriptor['path'])
        if actual!=descriptor:raise AssertionError('EXACT_RETAINED_CURRENT_CONTROLLER_FIXTURE_PIN')
        if name is not None:self.named[name]=actual
        return actual
    def reviewed_predecessor_cwd(self):
        # Deliberately synthetic reviewed-plan variant over current R10 CODE.
        # R2 is an actual declared member root. No historical plan is rewritten.
        predecessor='/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2'
        self.change('controller-plan',lambda d:d['groups'][1].update(cwd=predecessor))
        self.change('controller-api-1',lambda d:d['launch']['actualArguments'].update(workdir=predecessor))
        # A full production-validator positive precedes the single API mutation
        # tested later, so an unrelated refusal cannot masquerade as coverage.
        consumer.validate_current_consumer_authority(self,self.leaf())
        source=self.doc(self.leaf()['controllerSource'])
        return self.doc(source['controlPlan'])['groups'][1]

    def copy_file(self,path):
        path=Path(path)
        if '65d8116b77bc0af1a108122ec28cfcea' in str(path):raise AssertionError('NO_OPERATIONAL_HELPER_PROOF_READ')
        raw=path.read_bytes();p=dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());self.raw[str(path)]=raw
        self.modes[str(path)]=path.stat().st_mode & 0o7777
        try:self.data[str(path)]=json.loads(raw)
        except (ValueError,UnicodeError):self.data[str(path)]=raw
        return p
    def read_mode(self,descriptor,expected_mode):
        # Modes are captured with the explicitly copied fixture file, with no
        # filesystem fallback from a validator operating on this memory graph.
        if self.modes.get(descriptor['path'])!=expected_mode:raise Refusal('MODEL_SOURCE_MODE_DRIFT')
        return self.read(descriptor)
    def record(self,name,value):
        p=self.put('/model/UNAUTHENTICATED_SYNTHETIC_'+name+'.json',value);self.named[name]=p;return p
    def reviews(self,prefix,subject,decision):
        return [self.record(prefix+'-'+role,dict(role=role,session='/root/SYNTHETIC_INDEPENDENT_'+prefix+'_'+role,decision=decision,subject=subject)) for role in ('qa','security')]
    def leaf(self):return self.doc(self.named['leaf'])
    @staticmethod
    def dependency_order(dependencies):
        """Deterministic dependency-first order; the finite bound is node count."""
        import heapq
        parents={path:set() for path in dependencies}
        for path,children in dependencies.items():
            if not children<=dependencies.keys():raise AssertionError('SYNTHETIC_UNKNOWN_DEPENDENCY')
            for child in children:parents[child].add(path)
        remaining={path:len(children) for path,children in dependencies.items()}
        ready=[path for path,count in remaining.items() if count==0];heapq.heapify(ready);order=[]
        while ready:
            path=heapq.heappop(ready);order.append(path)
            for parent in sorted(parents[path]):
                remaining[parent]-=1
                if remaining[parent]==0:heapq.heappush(ready,parent)
        if len(order)!=len(dependencies):raise AssertionError('SYNTHETIC_DESCRIPTOR_CYCLE')
        return order
    def change(self,name,mutate):
        # Snapshot original identities once. Never adopt a descriptor by path or
        # propagate transient hashes over separate incoming edges of a diamond.
        snapshot=copy.deepcopy(self.data);original_raw=dict(self.raw)
        if snapshot.keys()!=original_raw.keys():raise AssertionError('SYNTHETIC_COLLIDING_PATH')
        pins={path:dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for path,raw in original_raw.items()}
        for path in pins:
            p=Path(path)
            if not p.is_absolute() or str(p)!=path or '..' in p.parts:raise AssertionError('SYNTHETIC_COLLIDING_PATH')
        def key(value):
            if type(value) is dict and set(value)=={'path','bytes','sha256'} and type(value['path']) is str and type(value['bytes']) is int and type(value['sha256']) is str:
                return value['path'],value['bytes'],value['sha256']
            return None
        original={key(p):path for path,p in pins.items()};named_paths={}
        for p in self.named.values():
            identity=key(p)
            if identity is None:raise AssertionError('SYNTHETIC_COLLIDING_PATH')
            if p['path'] in named_paths and named_paths[p['path']]!=identity:raise AssertionError('SYNTHETIC_COLLIDING_PATH')
            named_paths[p['path']]=identity
        target=original.get(key(self.named[name]))
        if target is None:raise AssertionError('SYNTHETIC_COLLIDING_PATH')
        def references(value):
            found=set();stack=[value]
            while stack:
                item=stack.pop();identity=key(item)
                if identity in original:found.add(original[identity])
                elif type(item) is dict:stack.extend(item.values())
                elif type(item) is list:stack.extend(item)
            return found
        dependencies={path:references(value) for path,value in snapshot.items()}
        self.dependency_order(dependencies)
        value=copy.deepcopy(snapshot[target]);mutate(value)
        # Check the proposed edit too; an inserted exact original self/ancestor
        # pin cannot turn this synthetic repinning operation into a cycle.
        dependencies[target]=references(value)
        order=self.dependency_order(dependencies)
        parents={path:set() for path in snapshot}
        for path,children in dependencies.items():
            for child in children:parents[child].add(path)
        affected={target};pending=[target]
        while pending:
            child=pending.pop()
            for parent in sorted(parents[child]-affected):affected.add(parent);pending.append(parent)
        replacements={};updates={};processed=[]
        def replace(item):
            identity=key(item)
            if identity in replacements:return copy.deepcopy(replacements[identity])
            if type(item) is dict:return {k:replace(v) for k,v in item.items()}
            if type(item) is list:return [replace(v) for v in item]
            return item
        for path in order:
            if path not in affected:continue
            processed.append(path)
            changed=replace(value if path==target else snapshot[path])
            if json_bytes(changed)==json_bytes(snapshot[path]):continue
            raw=json_bytes(changed);p=dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            updates[path]=(changed,raw);replacements[key(pins[path])]=p
        # No persistent fixture mutation until topology/collisions are checked.
        updated_named={label:replace(p) for label,p in self.named.items()}
        for path,(changed,raw) in updates.items():self.data[path]=changed;self.raw[path]=raw
        self.named=updated_named
        if 'consumer-source' in self.named:self.source=self.named['consumer-source']
        for key,label in [('CURRENT_HELPER_COMPONENT_BASIS','component-basis'),
                          ('CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE','component-template'),
                          ('CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE','component-design-acceptance')]:
            if label in self.named:setattr(consumer,key,self.named[label])
        return processed

class CurrentReadyAuthorityControls(unittest.TestCase):
    def setUp(self):
        self.saved={key:getattr(consumer,key) for key in ('_ACTIVE_BINDINGS','DRAFT_FINAL_ADAPTER_READY',
            'CURRENT_HELPER_PROBE_DATA','CURRENT_HELPER_PROBE_ACCEPTANCE','CURRENT_HELPER_COMPONENT_BASIS',
            'CURRENT_HELPER_COMPONENT_BASIS_TEMPLATE','CURRENT_HELPER_COMPONENT_BASIS_DESIGN_ACCEPTANCE',
            'CURRENT_PRODUCER_CONTROL_DATA','CURRENT_PRODUCER_CONTROL_ACCEPTANCE','CURRENT_CAPTURE_SOURCE',
            'CURRENT_CAPTURE_SOURCE_ACCEPTANCE','CURRENT_ADMISSION_DATA_ACCEPTANCE')}
    def tearDown(self):
        for key,value in self.saved.items():setattr(consumer,key,value)
    def model(self):return ReadyAuthorityModel()
    def reject(self,name,mutate):
        f=self.model();f.change(name,mutate)
        with self.assertRaises((ValueError,KeyError)):consumer.validate_current_consumer_authority(f,f.leaf())
    def test_positive_full_current_ready_typed_authority_path(self):
        f=self.model();result=consumer.bind_current_profile(f,f.named['leaf']);self.assertTrue(result['readiness']);self.assertEqual(consumer._ACTIVE_BINDINGS['consumerSource'],f.source);consumer.require_current_source_profile()
    def test_current_actual_code_and_ast_partition_are_checked(self):
        f=self.model();s,p,counts,total=consumer.current_code_profile(f,f.source);self.assertEqual(total,sum(g['count'] for g in p['groups']));self.assertEqual(s['runtimeSourceCount'],len(consumer.RUNTIME_FILES))
    def test_stale139_control_authority_refused(self):self.reject('data-acceptance',lambda d:d.update(modelsDefined=139,modelsExecuted=139,modelsPassed=139))
    def test_wrong_source_acceptance_scope(self):self.reject('source-acceptance',lambda d:d.update(scope='UNRELATED_SCOPE'))
    def test_wrong_source_acceptance_decision(self):self.reject('source-acceptance',lambda d:d.update(decision='ACCEPT_UNRELATED_SOURCE'))
    def test_wrong_control_acceptance_scope(self):self.reject('data-acceptance',lambda d:d.update(scope='OLD139_CONTROL_DATA_ONLY'))
    def test_wrong_control_acceptance_decision(self):self.reject('data-acceptance',lambda d:d.update(decision='ACCEPT_OLD139'))
    def test_unrelated_root_stub_without_typed_schema(self):
        f=self.model();f.change('source-acceptance',lambda d:[d.pop(k) for k in list(d) if k not in ('actor','subject')])
        with self.assertRaises(ValueError):consumer.validate_current_consumer_authority(f,f.leaf())
    def test_wrong_control_source_join(self):self.reject('control-data',lambda d:d.update(consumerSource=dict(d['consumerSource'],sha256='b'*64)))
    def test_wrong_control_plan_join(self):self.reject('control-data',lambda d:d.update(controlPlan=dict(d['controlPlan'],sha256='b'*64)))
    def test_incomplete_current_partition(self):self.reject('data-acceptance',lambda d:d.update(countsSeparate=d['countsSeparate'][:-1]))
    def test_old16_runtime_root_field(self):self.reject('source-acceptance',lambda d:d.update(runtimeSourceCount=14))
    def test_old31_source_root_field(self):self.reject('source-acceptance',lambda d:d.update(sourceCount=31))
    def test_source_review_role_order(self):self.reject('source-acceptance',lambda d:d.update(reviews=list(reversed(d['reviews']))))
    def test_control_review_role_order(self):self.reject('data-acceptance',lambda d:d.update(reviews=list(reversed(d['reviews']))))
    def test_source_author_cannot_be_source_reviewer(self):self.reject('source-qa',lambda d:d.update(session='/root/consumer6_source'))
    def test_helper_creator_cannot_be_source_reviewer(self):self.reject('source-qa',lambda d:d.update(session='/root/producer4_nonblocking_source'))
    def test_helper_creator_cannot_be_control_reviewer(self):self.reject('data-security',lambda d:d.update(session='/root/producer4_nonblocking_source'))
    def test_control_data_operator_list_cannot_be_empty(self):self.reject('control-data',lambda d:d.update(operators=[]))
    def test_model_api_inner_reap_eof_cannot_be_fabricated(self):self.reject('execution',lambda d:d.update(innerPidReapEofAttested=True))
    def test_nonzero_model_failure_refused(self):self.reject('control-data',lambda d:d.update(modelsFailed=1))
    def test_skipped_model_refused(self):self.reject('control-data',lambda d:d.update(skipped=1))
    def test_truncated_model_output_refused(self):self.reject('execution',lambda d:d.update(truncated=True))
    def test_nonnatural_actual_api_exit_refused(self):self.reject('group-api-0',lambda d:d['launch']['unmodifiedResponse'].update(exit_code=2))
    def test_source_review_wrong_subject(self):self.reject('source-qa',lambda d:d.update(subject=dict(d['subject'],sha256='b'*64)))
    def test_false_leaf_refuses_before_ready_authority(self):
        f=self.model();f.change('leaf',lambda d:d.update(readiness=False))
        with self.assertRaisesRegex(Refusal,'UNREADY_BINDINGS'):consumer.bind_current_profile(f,f.named['leaf'])
    def test_wrong_current_self_code_hash(self):
        f=self.model();source=f.doc(f.source);p=next(p for p in source['sources'] if Path(p['path']).name=='consumer.py');p['sha256']='b'*64
        bad=f.record('bad-self-source',source)
        with self.assertRaisesRegex(Refusal,'MODEL_PIN_DRIFT'):consumer.current_code_profile(f,bad)
    def test_wrong_current_test_body_hash(self):
        f=self.model();source=f.doc(f.source);p=next(p for p in source['sources'] if Path(p['path']).name=='test_async_guard.py');p['sha256']='b'*64
        bad=f.record('bad-test-source',source)
        with self.assertRaisesRegex(Refusal,'MODEL_PIN_DRIFT'):consumer.current_code_profile(f,bad)
    def test_old_source1_cannot_activate_current_code(self):
        f=self.model();source=f.doc(f.source);source['version']='SOURCE1';bad=f.record('old-source-version',source)
        with self.assertRaises(ValueError):consumer.current_code_profile(f,bad)
    def test_named_model_count_omission_refused(self):
        f=self.model();g=f.groups[0];line=g['definitionNames'][0];output=(line.split('.',1)[1]+' (__main__.'+line+') ... ok\n\n'+'-'*70+'\nRan '+str(g['count'])+' tests in 0.001s\n\nOK\n').encode()
        with self.assertRaises(Refusal):consumer.named_unittest_output(output,g)
    def test_fresh_source5_current_n_external_controller_triple_is_valid(self):
        f=self.model();value=f.leaf();source=f.doc(value['controllerSource'])
        expected,_=current_controller_expectations()
        self.assertEqual(source['version'],expected['version']);self.assertNotEqual(value['controllerSource'],consumer.HISTORICAL_HELPER_CONTROLLER_SOURCE)
        triple={k:value[k] for k in ('controllerSource','controllerSourceAcceptance','controllerControlDataAcceptance')}
        result=probe_adapter.validate_controller_authority(f,triple,consumer.HELPER_PRODUCER,consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT,set(consumer.CURRENT_CONTROL_ACTORS))
        self.assertEqual(result[3],sum(g['count'] for g in result[1]['groups']));consumer.validate_current_consumer_authority(f,value)
    def test_unmodified_source5_mixed_script_roots_and_reviewed_cwds_full_ready(self):
        f=self.model();source=f.doc(f.leaf()['controllerSource']);plan=f.doc(source['controlPlan'])
        expected_source,expected_plan=current_controller_expectations()
        roots=[str(Path(g['source']['path']).parent) for g in plan['groups']]
        cwds=[g['cwd'] for g in plan['groups']]
        self.assertEqual(source['version'],expected_source['version'])
        self.assertEqual(roots,[str(Path(g['source']['path']).parent) for g in expected_plan['groups']])
        self.assertEqual(cwds,[g['cwd'] for g in expected_plan['groups']])
        self.assertGreater(len(set(roots)),1)
        self.assertEqual(set(cwds),{str(Path(CURRENT_R8_FIXTURE['source']['path']).parent)})
        self.assertTrue(any(root!=cwd for root,cwd in zip(roots,cwds)))
        self.assertTrue(consumer.bind_current_profile(f,f.named['leaf'])['readiness'])
    def test_current_controller_request_preserves_frozen_predecessor_cwd(self):
        f=self.model();group=f.reviewed_predecessor_cwd()
        request=probe_adapter.controller_request(group)
        self.assertEqual(request['workdir'],group['cwd']);self.assertNotEqual(request['workdir'],str(Path(group['source']['path']).parent))
        consumer.validate_current_consumer_authority(f,f.leaf())
    def reject_controller_cwd(self,cwd):
        f=self.model();f.change('controller-plan',lambda d:d['groups'][1].update(cwd=cwd))
        with self.assertRaisesRegex(Refusal,'CANONICAL_CURRENT_CONTROLLER_MODEL_CWD|SCOPED_CURRENT_OR_PREDECESSOR_CONTROLLER_MODEL_ROOT|CONTROLLER_CWD_BACKED_BY_VERIFIED_DECLARED_MEMBER'):
            consumer.validate_current_consumer_authority(f,f.leaf())
    def test_current_controller_relative_cwd_refused(self):self.reject_controller_cwd('producer4-helper-probe-controller-preparation-r2')
    def test_current_controller_dot_alias_cwd_refused(self):self.reject_controller_cwd('/Data/nbdp-e02-tooling-20261027/./producer4-helper-probe-controller-preparation-r2')
    def test_current_controller_dotdot_alias_cwd_refused(self):self.reject_controller_cwd('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r5/../producer4-helper-probe-controller-preparation-r2')
    def test_current_controller_trailing_slash_alias_cwd_refused(self):self.reject_controller_cwd('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2/')
    def test_current_controller_repeated_slash_alias_cwd_refused(self):self.reject_controller_cwd('/Data//nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2')
    def test_current_controller_unapproved_foreign_cwd_refused(self):self.reject_controller_cwd('/tmp/producer4-helper-probe-controller-preparation-r2')
    def test_current_controller_other_preparation_namespace_cwd_refused(self):self.reject_controller_cwd('/Data/nbdp-e02-tooling-20261027/ordinary-producer-preparation-r4-source4')
    def test_current_controller_future_revision_cwd_refused(self):
        expected,_=current_controller_expectations();revision=int(expected['version'][1:])
        current=Path(CURRENT_R8_FIXTURE['source']['path']).parent
        future=current.with_name(current.name.rsplit('-r',1)[0]+'-r'+str(revision+1))
        f=self.model();f.change('controller-plan',lambda d:d['groups'][1].update(cwd=str(future)))
        with self.assertRaisesRegex(Refusal,'^SCOPED_CURRENT_OR_PREDECESSOR_CONTROLLER_MODEL_ROOT$'):
            consumer.validate_current_consumer_authority(f,f.leaf())
    def test_current_controller_predecessor_without_declared_member_cwd_refused(self):self.reject_controller_cwd('/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r3')
    def test_current_controller_unbound_version_spelling_cannot_authorize_cwd(self):self.reject('controller-source',lambda d:d.update(version='r05'))
    def test_current_controller_actual_api_cwd_cannot_be_rewritten_to_script_parent(self):
        f=self.model();group=f.reviewed_predecessor_cwd()
        self.assertNotEqual(group['cwd'],str(Path(group['source']['path']).parent))
        f.change('controller-api-1',lambda d:d['launch']['actualArguments'].update(workdir=str(Path(group['source']['path']).parent)))
        with self.assertRaisesRegex(ValueError,'^WHOLE_ACTUAL_REQUEST_FAMILY$'):consumer.validate_current_consumer_authority(f,f.leaf())
    def reject_controller_api_cwd(self,name,cwd):
        f=self.model();f.change(name,lambda d:d['launch']['actualArguments'].update(workdir=cwd))
        with self.assertRaisesRegex(ValueError,'^WHOLE_ACTUAL_REQUEST_FAMILY$'):consumer.validate_current_consumer_authority(f,f.leaf())
    def test_current_controller_actual_api_cwd_cannot_use_other_approved_root(self):
        self.reject_controller_api_cwd('controller-api-0','/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2')
    def test_current_controller_actual_api_cwd_alias_refused(self):
        self.reject_controller_api_cwd('controller-api-1','/Data/nbdp-e02-tooling-20261027/producer4-helper-probe-controller-preparation-r2/')
    def test_partial_external_controller_tuple_refuses(self):
        self.reject('leaf',lambda d:d.pop('controllerSourceAcceptance'))
    def test_external_controller_source_must_equal_probe_operand(self):
        self.reject('leaf',lambda d:d.update(controllerSource=dict(d['controllerSource'],sha256='b'*64)))
    def test_external_controller_source_acceptance_must_equal_probe_operand(self):
        self.reject('leaf',lambda d:d.update(controllerSourceAcceptance=dict(d['controllerSourceAcceptance'],sha256='b'*64)))
    def test_external_controller_control_acceptance_must_equal_probe_operand(self):
        self.reject('leaf',lambda d:d.update(controllerControlDataAcceptance=dict(d['controllerControlDataAcceptance'],sha256='b'*64)))
    def test_current_controller_source_scope_is_typed(self):self.reject('controller-source-acceptance',lambda d:d.update(scope='OLD_R4_ONLY'))
    def test_current_controller_source_decision_is_typed(self):self.reject('controller-source-acceptance',lambda d:d.update(decision='ACCEPT_OLD_R4_SOURCE'))
    def test_current_controller_data_scope_is_typed(self):self.reject('controller-data-acceptance',lambda d:d.update(scope='OLD104_ONLY'))
    def test_current_controller_data_decision_is_typed(self):self.reject('controller-data-acceptance',lambda d:d.update(decision='ACCEPT_OLD104_ONLY'))
    def test_old104_counts_cannot_qualify_new_host_current_n(self):self.reject('controller-data-acceptance',lambda d:d.update(modelsDefined=104,modelsExecuted=104,modelsPassed=104,countsSeparate=[39,36,10,19]))
    def test_controller_control_data_source_must_match_current_tuple(self):self.reject('controller-data',lambda d:d.update(controllerSource=dict(d['controllerSource'],sha256='b'*64)))
    def test_controller_source_review_roles_are_ordered(self):self.reject('controller-source-acceptance',lambda d:d.update(reviews=list(reversed(d['reviews']))))
    def test_controller_data_review_roles_are_ordered(self):self.reject('controller-data-acceptance',lambda d:d.update(reviews=list(reversed(d['reviews']))))
    def test_controller_helper_creator_cannot_review_current_controller_source(self):self.reject('controller-source-qa',lambda d:d.update(session='/root/producer4_nonblocking_source'))
    def test_controller_consumer_author_cannot_review_current_controller_data(self):self.reject('controller-data-security',lambda d:d.update(session='/root/consumer6_source'))
    def test_controller_wrong_host_code_hash_is_not_current_authority(self):
        f=self.model();value=f.leaf();source=f.doc(value['controllerSource']);host=next(p for p in source['sources'] if Path(p['path']).name=='host.py');host['sha256']='b'*64
        bad=f.record('bad-controller-code',source)
        with self.assertRaisesRegex(Refusal,'MODEL_PIN_DRIFT'):probe_adapter.controller_profile(f,bad,consumer.HELPER_PRODUCER)
    def test_controller_missing_current_group_cannot_relabel_old_subset(self):self.reject('controller-data-acceptance',lambda d:d.update(countsSeparate=d['countsSeparate'][:-1]))
    def test_controller_model_skip_is_not_a_full_current_pass(self):self.reject('controller-data',lambda d:d.update(skipped=1))
    def test_controller_api_only_does_not_invent_inner_reap(self):self.reject('controller-execution',lambda d:d.update(innerPidReapEofAttested=True))
    def test_controller_actual_group_api_exit_must_be_natural_zero(self):self.reject('controller-api-0',lambda d:d['launch']['unmodifiedResponse'].update(exit_code=2))
    def test_exact_actual_r4_known_empty_source_operator_shape(self):
        d=json.loads(Path(consumer.HISTORICAL_HELPER_CONTROLLER_SOURCE['path']).read_text());self.assertEqual(d['operators'],[]);self.assertIn('/root/producer4_nonblocking_source',probe_adapter.source_actors(d))
    def test_missing_source_creators_are_not_empty(self):
        with self.assertRaises(Refusal):probe_adapter.source_actors(dict(schema='e02-one-cid-helper-probe-controller-source-v1',operators=[]))
    def test_empty_data_operators_remain_invalid(self):
        with self.assertRaises(Refusal):probe_adapter.data_actors(dict(authors=['/root/a'],operators=[]))
    def test_empty_release_operators_remain_invalid(self):
        with self.assertRaises(Refusal):probe_adapter.data_actors(dict(authors=['/root'],operators=[]))

    def reject_current_r8(self,name,mutate):
        f=self.model();consumer.validate_current_consumer_authority(f,f.leaf())
        f.change(name,mutate)
        with self.assertRaises(ValueError):consumer.validate_current_consumer_authority(f,f.leaf())
    def test_current266_exact_accepted_r8_168_full_ready_production_validator(self):
        f=self.model();value=f.leaf();source=f.doc(value['controllerSource'])
        self.assertEqual(value['controllerSource'],CURRENT_R8_FIXTURE['source'])
        self.assertEqual(value['controllerSourceAcceptance'],CURRENT_R8_FIXTURE['sourceAcceptance'])
        self.assertEqual(value['controllerControlDataAcceptance'],CURRENT_R8_FIXTURE['controlAcceptance'])
        self.assertEqual(source['upstreamProducerSubject'],consumer.HELPER_PRODUCER)
        self.assertEqual(source['upstreamProducerModelsDefined'],266)
        triple={k:value[k] for k in ('controllerSource','controllerSourceAcceptance','controllerControlDataAcceptance')}
        result=probe_adapter.validate_controller_authority(f,triple,consumer.HELPER_PRODUCER,consumer.CURRENT_HELPER_CONTROLLER_ACCEPTANCE_CONTRACT,set(consumer.CURRENT_CONTROL_ACTORS))
        expected,expected_plan=current_controller_expectations();counts=[g['count'] for g in expected_plan['groups']]
        self.assertEqual(result[2],counts);self.assertEqual(result[3],sum(counts));self.assertEqual(result[3],expected['modelsDefined'])
        self.assertTrue(consumer.bind_current_profile(f,f.named['leaf'])['readiness'])
    def test_historical_r5_old260_tuple_cannot_qualify_current266(self):
        f=self.model();consumer.validate_current_consumer_authority(f,f.leaf())
        legacy=f.copy_expected(HISTORICAL_R5_FIXTURE['source'],'historical-r5-negative-source')
        self.assertEqual(f.doc(legacy)['upstreamProducerModelsDefined'],260)
        self.assertNotEqual(f.doc(legacy)['upstreamProducerSubject'],consumer.HELPER_PRODUCER)
        with self.assertRaises(ValueError):probe_adapter.controller_profile(f,legacy,consumer.HELPER_PRODUCER)
    def test_current_r8_old260_upstream_model_count_refused(self):
        self.reject_current_r8('controller-source',lambda d:d.update(upstreamProducerModelsDefined=260))
    def test_current_r8_mixed_historical_producer_subject_refused(self):
        legacy=json.loads(Path(HISTORICAL_R5_FIXTURE['source']['path']).read_bytes())['upstreamProducerSubject']
        self.reject_current_r8('controller-source',lambda d:d.update(upstreamProducerSubject=legacy))
    def test_current_r8_mixed_historical_source_acceptance_refused(self):
        self.reject_current_r8('leaf',lambda d:d.update(controllerSourceAcceptance=HISTORICAL_R5_FIXTURE['sourceAcceptance']))
    def test_current_r8_mixed_historical_control_acceptance_refused(self):
        self.reject_current_r8('leaf',lambda d:d.update(controllerControlDataAcceptance=HISTORICAL_R5_FIXTURE['controlAcceptance']))


class FixturePropagationControls(unittest.TestCase):
    def model(self):
        f=object.__new__(ReadyAuthorityModel);MemoryFiles.__init__(f);f.named={};return f
    def test_convergent_original_pin_diamond_rehashes_dependency_first_once(self):
        f=self.model();base=f.record('base',dict(value=1));left=f.record('left',dict(child=base));right=f.record('right',dict(child=base));f.record('top',dict(left=left,right=right,base=base))
        untouched=f.record('untouched',dict(value='unchanged'));processed=f.change('base',lambda d:d.update(value=2))
        self.assertEqual(processed,[base['path'],left['path'],right['path'],f.named['top']['path']]);self.assertEqual(len(processed),len(set(processed)))
        self.assertEqual(f.doc(f.named['left'])['child'],f.named['base']);self.assertEqual(f.doc(f.named['right'])['child'],f.named['base'])
        self.assertEqual(f.doc(f.named['top']),dict(left=f.named['left'],right=f.named['right'],base=f.named['base']));self.assertEqual(f.named['untouched'],untouched)
    def test_more_than256_convergent_edges_have_one_rehash_per_reachable_node(self):
        f=self.model();base=f.record('base',dict(value=1));branches=[f.record('branch-'+str(i),dict(child=base)) for i in range(140)]
        f.record('top',dict(children=branches,base=base));self.assertGreater(2*len(branches)+1,256)
        processed=f.change('base',lambda d:d.update(value=2));self.assertEqual(len(processed),len(branches)+2);self.assertEqual(len(processed),len(set(processed)))
        for i in range(len(branches)):self.assertEqual(f.doc(f.named['branch-'+str(i)])['child'],f.named['base'])
        self.assertEqual(f.doc(f.named['top'])['children'],[f.named['branch-'+str(i)] for i in range(len(branches))]);self.assertEqual(f.doc(f.named['top'])['base'],f.named['base'])
    def test_only_complete_exact_original_pin_replaced_wrong_hash_size_extra_and_partial_preserved(self):
        f=self.model();base=f.record('base',dict(value=1));wrong_hash=dict(base,sha256='b'*64);wrong_size=dict(base,bytes=base['bytes']+1);extra=dict(base,note='NOT_A_THREE_KEY_PIN');partial=dict(path=base['path'],sha256=base['sha256'])
        f.record('parent',dict(good=base,wrongHash=wrong_hash,wrongSize=wrong_size,extra=extra,partial=partial));f.change('base',lambda d:d.update(value=2));parent=f.doc(f.named['parent'])
        self.assertEqual(parent['good'],f.named['base']);self.assertNotEqual(parent['good'],base);self.assertEqual(parent['wrongHash'],wrong_hash);self.assertEqual(parent['wrongSize'],wrong_size);self.assertEqual(parent['extra'],extra);self.assertEqual(parent['partial'],partial)
    def test_proposed_exact_original_self_cycle_fails_before_fixture_mutation(self):
        f=self.model();base=f.record('base',dict(value=1));before=copy.deepcopy((f.data,f.raw,f.named))
        with self.assertRaisesRegex(AssertionError,'SYNTHETIC_DESCRIPTOR_CYCLE'):f.change('base',lambda d:d.update(child=base))
        self.assertEqual((f.data,f.raw,f.named),before)
    def test_original_cycle_is_not_repaired_by_the_requested_mutation(self):
        f=self.model();base=f.record('base',dict(value=1));f.data[base['path']]['child']=base;before=copy.deepcopy((f.data,f.raw,f.named))
        with self.assertRaisesRegex(AssertionError,'SYNTHETIC_DESCRIPTOR_CYCLE'):f.change('base',lambda d:d.pop('child'))
        self.assertEqual((f.data,f.raw,f.named),before)
    def test_dependency_cycle_is_failstop_in_finite_topological_order(self):
        with self.assertRaisesRegex(AssertionError,'SYNTHETIC_DESCRIPTOR_CYCLE'):ReadyAuthorityModel.dependency_order({'left':{'right'},'right':{'left'}})
        self.assertEqual(ReadyAuthorityModel.dependency_order({'top':{'left','right'},'right':{'base'},'left':{'base'},'base':set()}),['base','left','right','top'])
    def test_colliding_named_path_versions_fail_before_fixture_mutation(self):
        f=self.model();base=f.record('base',dict(value=1));f.named['collision']=dict(base,sha256='b'*64);before=copy.deepcopy((f.data,f.raw,f.named))
        with self.assertRaisesRegex(AssertionError,'SYNTHETIC_COLLIDING_PATH'):f.change('base',lambda d:d.update(value=2))
        self.assertEqual((f.data,f.raw,f.named),before)
    def test_alias_storage_path_is_not_another_graph_identity(self):
        f=self.model();base=f.record('base',dict(value=1));alias='/model/./UNAUTHENTICATED_SYNTHETIC_base.json';f.raw[alias]=f.raw[base['path']];f.data[alias]=copy.deepcopy(f.data[base['path']]);before=copy.deepcopy((f.data,f.raw,f.named))
        with self.assertRaisesRegex(AssertionError,'SYNTHETIC_COLLIDING_PATH'):f.change('base',lambda d:d.update(value=2))
        self.assertEqual((f.data,f.raw,f.named),before)
    def test_noop_mutation_preserves_original_bytes_and_pins(self):
        f=self.model();base=f.record('base',dict(value=1));f.record('parent',dict(child=base));before=copy.deepcopy((f.data,f.raw,f.named));processed=f.change('base',lambda d:None)
        self.assertEqual(len(processed),2);self.assertEqual(len(processed),len(set(processed)));self.assertEqual((f.data,f.raw,f.named),before)

if __name__=='__main__':unittest.main()
