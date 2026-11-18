"""Three current SOURCE/DATA binding methods; separate reviewed capture required.

Counterfactual acceptance records and alternate genuine-helper APK/config
copies live only in owned temporary negative fixtures. They are not approvals.
No native, Android, SDK, services, crypto or runtime grants are executed.
"""
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import supervisor as producer

HERE=Path(__file__).resolve().parent


class Producer3RebuiltBindings(unittest.TestCase):
    def bindings(self):return json.loads((HERE/'rebuilt-artifact-bindings.json').read_bytes())

    def metadata_copy(self,directory,name,value):
        path=directory/(name+'.json')
        with path.open('xb') as stream:stream.write((json.dumps(value,indent=2)+'\n').encode())
        os.chmod(path,0o600)
        return producer.pin(path)

    def role_config(self,role,bindings):
        # Same DATA projection as materialize, without invoking it or writing config.
        runtime=json.loads((HERE/'runtime-plan.json').read_bytes())
        minimum=json.loads((HERE/'minimum-plan.json').read_bytes());fixed=minimum['roles'][role]
        value={k:runtime[k] for k in ('schema','scope','runtimeImage','relayImage','sdkRoot','amethystApk','helperApk')}
        value.update(profileId=producer.PROFILE,ordinaryRole=role,windowId=fixed['windowId'],account=fixed['account'],peer=fixed['peer'],
                     runId='a'*32,originalLeaseSeconds=1800,sourceAndDependencyPins=producer.source_pins(),
                     guardBundleRoot=str(producer.OLD/'guard-python'),state='PINNED_CANDIDATE_REQUIRES_SEPARATE_REVIEW_AND_RELEASE',canonicalE02='PARTIAL22_UNCHANGED')
        value.update(copy.deepcopy(producer.REVIEWED_RUNTIME_INPUTS))
        self.assertEqual(value['amethystApk'],bindings['amethystApk']);self.assertEqual(value['helperApk'],bindings['helperApk'])
        return value

    def actual_inventory_tail(self,config):
        # Execute only the unchanged actual SDK/guard validation statements on
        # owned miniature trees. This is not caller admission or real SDK use.
        tree=ast.parse((HERE/'supervisor.py').read_bytes())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_config')
        start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='inventory' for t in n.targets))
        stop=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='fixture' for t in n.targets))
        statements=ast.Module(body=copy.deepcopy(fn.body[start:stop]),type_ignores=[])
        scope=dict(config=config,Path=Path,strict=producer.strict,checked=producer.checked,digest=producer.digest,need=producer.need)
        exec(compile(ast.fix_missing_locations(statements),'<actual-owned-inventory-tail>','exec'),scope)

    def miniature_trees(self,directory):
        sdk=directory/'sdk';guard=directory/'guard';sdk.mkdir(mode=0o700);guard.mkdir(mode=0o700)
        tool=sdk/'tool.bin';tool.write_bytes(b'good');os.chmod(tool,0o600)
        interpreter=guard/'guard.py';interpreter.write_bytes(b'safe');os.chmod(interpreter,0o600)
        inventory={'files':[{'path':'tool.bin','size':4,'mode':'0o600','sha256':producer.digest(tool)}]}
        bundle={'files':{'guard.py':{'bytes':4,'sha256':producer.digest(interpreter)}}}
        config=dict(sdkRoot=str(sdk),guardBundleRoot=str(guard),sdkInventory=self.metadata_copy(directory,'sdk-index',inventory),guardBundleInventory=self.metadata_copy(directory,'guard-index',bundle))
        return config,tool,interpreter

    def test_current_accepted_rebuilt_artifacts_and_exact_e01_native(self):
        # Real accepted APK bindings are present; this test requires separate execution release.
        value=producer.verify_rebuilt_artifacts()
        self.assertEqual(value['runtimeSourceCount'],22)
        self.assertEqual(value['amethystAcceptanceDecision'],'ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY')
        for key,schema in [('amethystAcceptance','nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1'),('helperAcceptance','nbdp-actual-artifact-data-acceptance-v1')]:
            accepted=json.loads(producer.checked(value[key]).read_bytes())
            self.assertEqual(accepted['schema'],schema);self.assertIs(accepted['artifactQualified'],True)
        for role in ('incoming','archive'):
            with self.subTest(validRole=role):producer.verify_config(self.role_config(role,value))

    def test_missing_apk_wrong_native_e01_and_build_sdk_substitution_refused(self):
        for mutation in ('missing-apk','wrong-native','wrong-e01','build-sdk'):
            value=copy.deepcopy(self.bindings())
            if mutation=='missing-apk':value['amethystApk']=None
            elif mutation=='wrong-native':value['rustBinary']['sha256']='0'*64
            elif mutation=='wrong-e01':value['acceptedE01']['sha256']='0'*64
            else:value['runtimeSdk']='/Data/NOT_RUNTIME_BUILD_SDK37'
            with self.subTest(mutation=mutation),self.assertRaises(RuntimeError):producer.verify_rebuilt_artifacts(value)
        with tempfile.TemporaryDirectory(prefix='nbdp-producer3-acceptance-negatives-') as temporary:
            directory=Path(temporary);original=self.bindings()
            # Matching non-acceptance strings must never become artifact acceptance.
            for decision in (None,'HOLD','FAIL','PARTIAL','UNKNOWN_DECISION'):
                value=copy.deepcopy(original);record=json.loads(producer.checked(value['amethystAcceptance']).read_bytes())
                value['amethystAcceptanceDecision']=decision;record['decision']=decision
                value['amethystAcceptance']=self.metadata_copy(directory,'amethyst-decision-'+str(decision),record)
                with self.subTest(amethystDecision=decision),self.assertRaises(RuntimeError):producer.verify_rebuilt_artifacts(value)
            for key,field,changed,tag,message in [
                ('amethystAcceptance','schema','WRONG_SCHEMA','amethyst-schema','Actual accepted rebuilt APK provenance join'),
                ('amethystAcceptance','artifactQualified',False,'amethyst-false','Actual accepted rebuilt APK provenance join'),
                ('amethystAcceptance','artifactQualified',1,'amethyst-truthy','Actual accepted rebuilt APK provenance join'),
                ('helperAcceptance','schema','WRONG_SCHEMA','helper-schema','Actual accepted rebuilt helper join'),
                ('helperAcceptance','artifactQualified',False,'helper-false','Actual accepted rebuilt helper join'),
                ('helperAcceptance','artifactQualified',1,'helper-truthy','Actual accepted rebuilt helper join')]:
                value=copy.deepcopy(original);record=json.loads(producer.checked(value[key]).read_bytes());record[field]=changed
                value[key]=self.metadata_copy(directory,tag,record)
                with self.subTest(mutation=tag),self.assertRaisesRegex(RuntimeError,message):producer.verify_rebuilt_artifacts(value)

            for key,provenance,message in [
                ('amethystAcceptance','amethystProvenance','Actual accepted rebuilt APK provenance join'),
                ('helperAcceptance','helperProvenance','Actual accepted rebuilt helper join')]:
                for field in ('schema','decision','artifactQualified','subject'):
                    value=copy.deepcopy(original);record=json.loads(producer.checked(value[key]).read_bytes());record.pop(field,None)
                    value[key]=self.metadata_copy(directory,key+'-absent-'+field,record)
                    with self.subTest(artifact=key,absent=field),self.assertRaisesRegex(RuntimeError,message):producer.verify_rebuilt_artifacts(value)
                for field,changed,tag in [('schema','UNKNOWN_SCHEMA','unknown-schema'),('decision','UNKNOWN_DECISION','unknown-decision'),('artifactQualified',None,'qualification-null'),('artifactQualified','true','qualification-string')]:
                    value=copy.deepcopy(original);record=json.loads(producer.checked(value[key]).read_bytes());record[field]=changed
                    value[key]=self.metadata_copy(directory,key+'-'+tag,record)
                    with self.subTest(artifact=key,mutation=tag),self.assertRaisesRegex(RuntimeError,message):producer.verify_rebuilt_artifacts(value)
                value=copy.deepcopy(original);record=json.loads(producer.checked(value[key]).read_bytes())
                record['subject']=original['helperProvenance' if key=='amethystAcceptance' else 'amethystProvenance']
                value[key]=self.metadata_copy(directory,key+'-wrong-subject',record)
                with self.subTest(artifact=key,wrongSubject=True),self.assertRaisesRegex(RuntimeError,message):producer.verify_rebuilt_artifacts(value)
                for missing in (False,True):
                    value=copy.deepcopy(original);origin=json.loads(producer.checked(value[provenance]).read_bytes())
                    if missing:origin.pop('apk',None)
                    else:origin['apk']=original['helperApk' if key=='amethystAcceptance' else 'amethystApk']
                    value[provenance]=self.metadata_copy(directory,provenance+'-'+str(missing),origin)
                    record=json.loads(producer.checked(value[key]).read_bytes());record['subject']=value[provenance]
                    value[key]=self.metadata_copy(directory,key+'-wrong-provenance-apk-'+str(missing),record)
                    with self.subTest(artifact=key,provenanceApkMissing=missing),self.assertRaisesRegex(RuntimeError,message):producer.verify_rebuilt_artifacts(value)
            for decision in (None,'HOLD','FAIL','PARTIAL'):
                value=copy.deepcopy(original);record=json.loads(producer.checked(value['helperAcceptance']).read_bytes());record['decision']=decision
                value['helperAcceptance']=self.metadata_copy(directory,'helper-decision-'+str(decision),record)
                with self.subTest(helperDecision=decision),self.assertRaisesRegex(RuntimeError,'Actual accepted rebuilt helper join'):producer.verify_rebuilt_artifacts(value)

    def test_preflight_before_materialize_verify_and_exact22_worker_membership(self):
        tree=ast.parse((HERE/'supervisor.py').read_bytes());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        first=functions['materialize'].body[1]
        self.assertIsInstance(first,ast.Expr);self.assertEqual(first.value.func.id,'verify_rebuilt_artifacts')
        first=functions['verify_config'].body[0]
        self.assertIsInstance(first,ast.Assign);self.assertEqual(first.targets[0].id,'bindings');self.assertEqual(first.value.func.id,'verify_rebuilt_artifacts')
        for statement in functions['verify_config'].body[1:4]:
            self.assertIsInstance(statement,ast.Expr);self.assertEqual(statement.value.func.id,'need')
        call=functions['source_pins'].body[0].value;self.assertEqual(len(call.generators[0].iter.elts),22)
        expected_names={'supervisor.py','lease_guard.py','android_driver.py','ui-plan.json','fixture.mjs','fixture-plan.json','minimum-plan.json','business-rumor.json','chat-rumor.json','exchange.mjs','phase-writer.mjs','dependency-tree.mjs','dependency-tree.json','capture-budget.mjs','exchange-adapter.mjs','proxy-observer.mjs','guard-helper.py','guard-wire.mjs','guard-client-core.mjs','guard-client.mjs','guard-transport-boundaries.mjs','capture-allocation.mjs'}
        descriptors=producer.source_pins()
        self.assertEqual(len(descriptors),22)
        self.assertEqual({Path(row['path']).name for row in descriptors},expected_names)
        for row in descriptors:self.assertEqual(producer.pin(Path(row['path'])),row)
        self.assertEqual(json.loads((HERE/'runtime-plan.json').read_bytes())['sdkRoot'],'/tmp/nbdp-e02-api35-fixture-r2/sdk')
        self.assertEqual(producer.LIMITS['android'],(8192,512,8))
        self.assertEqual(set(producer.REVIEWED_RUNTIME_INPUTS),{'relayConfig','sdkInventory','guardBundleInventory'})
        bindings=self.bindings()
        with tempfile.TemporaryDirectory(prefix='nbdp-producer3-config-negatives-') as temporary:
            directory=Path(temporary)
            # Genuine valid APK bytes, different descriptor; no APK tool execution.
            alternate=directory/'alternate-helper.apk';alternate.write_bytes(producer.checked(bindings['helperApk']).read_bytes());os.chmod(alternate,0o600)
            alternate_apk=producer.pin(alternate);producer.checked(alternate_apk)
            metadata_alternates={}
            for name,descriptor in producer.REVIEWED_RUNTIME_INPUTS.items():
                path=directory/(name+'-alternate');path.write_bytes(producer.checked(descriptor).read_bytes());os.chmod(path,0o600)
                metadata_alternates[name]=producer.pin(path);producer.checked(metadata_alternates[name])
            empty_guard=self.metadata_copy(directory,'empty-guard',{'files':{}})
            alternate_sdk=self.metadata_copy(directory,'alternate-sdk',{'root':'/SYNTHETIC_NOT_RUNTIME','files':[]})
            for role in ('incoming','archive'):
                base=self.role_config(role,bindings)
                self.assertEqual(base['sourceAndDependencyPins'],descriptors)
                variants=[descriptors[:-2],descriptors[1:]]
                substituted=copy.deepcopy(descriptors);substituted[-1]=copy.deepcopy(descriptors[-2]);variants.append(substituted)
                changed=copy.deepcopy(descriptors);changed[0]['sha256']='0'*64;variants.append(changed)
                for wrong in variants:
                    value=copy.deepcopy(base);value['sourceAndDependencyPins']=wrong
                    with self.subTest(role=role,workerClosure=len(wrong)),self.assertRaisesRegex(RuntimeError,'Current full worker source pins required'):producer.verify_config(value)
                for key in ('amethystApk','helperApk'):
                    value=copy.deepcopy(base);value[key]=alternate_apk
                    self.assertNotEqual(value[key],bindings[key])
                    with self.subTest(role=role,artifact=key),self.assertRaisesRegex(RuntimeError,'Role configuration artifacts differ from accepted rebuilt bindings'):producer.verify_config(value)
                for key,wrong in [('sdkRoot','/Data/NOT_RUNTIME_BUILD_SDK37'),('runtimeImage','sha256:'+'0'*64)]:
                    value=copy.deepcopy(base);value[key]=wrong
                    with self.subTest(role=role,runtime=key),self.assertRaisesRegex(RuntimeError,'Role configuration runtime SDK/image differs from accepted rebuilt bindings'):producer.verify_config(value)
                for key,wrong in list(metadata_alternates.items())+[('guardBundleInventory',empty_guard),('sdkInventory',alternate_sdk)]:
                    value=copy.deepcopy(base);value[key]=wrong;producer.checked(wrong)
                    with self.subTest(role=role,metadata=key,alternative=wrong['path']),self.assertRaisesRegex(RuntimeError,'Role configuration metadata differs from immutable reviewed blueprint'):producer.verify_config(value)


        with tempfile.TemporaryDirectory(prefix='nbdp-producer3-inventory-negatives-') as temporary:
            directory=Path(temporary);context,tool,guard=self.miniature_trees(directory)
            self.actual_inventory_tail(context)
            # The same expected descriptor must reject current byte changes.
            descriptor=context['sdkInventory'];path=Path(descriptor['path']);raw=path.read_bytes();path.write_bytes(b'{}')
            with self.assertRaises(RuntimeError):producer.checked(descriptor)
            path.write_bytes(raw)
            tool.write_bytes(b'evil')
            with self.assertRaisesRegex(RuntimeError,'SDK installed inventory changed'):self.actual_inventory_tail(context)
            tool.write_bytes(b'good');extra=tool.parent/'unlisted.bin';extra.write_bytes(b'extra');os.chmod(extra,0o600)
            with self.assertRaisesRegex(RuntimeError,'SDK installed inventory changed'):self.actual_inventory_tail(context)
            extra.unlink();guard.write_bytes(b'evil')
            with self.assertRaisesRegex(RuntimeError,'Guard interpreter bundle changed'):self.actual_inventory_tail(context)
            guard.unlink()
            with self.assertRaises((RuntimeError,FileNotFoundError)):self.actual_inventory_tail(context)


if __name__=='__main__':unittest.main(verbosity=1)
