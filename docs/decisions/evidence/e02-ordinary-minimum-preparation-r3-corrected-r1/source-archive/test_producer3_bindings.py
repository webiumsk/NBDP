"""Three DRAFT source/DATA binding methods; no execution until accepted APK.

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

    def test_current_accepted_rebuilt_artifacts_and_exact_e01_native(self):
        # Entire scope remains deferred while the four real APK fields are NULL.
        value=producer.verify_rebuilt_artifacts()
        self.assertEqual(value['runtimeSourceCount'],16)
        self.assertEqual(value['amethystAcceptanceDecision'],'ACCEPT_REBUILT_AMETHYST_ARTIFACT_ONLY')
        for key,schema in [('amethystAcceptance','nbdp-actual-rebuilt-amethyst-artifact-acceptance-v1'),('helperAcceptance','nbdp-actual-artifact-data-acceptance-v1')]:
            accepted=json.loads(producer.checked(value[key]).read_bytes())
            self.assertEqual(accepted['schema'],schema);self.assertIs(accepted['artifactQualified'],True)

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
            for decision in (None,'HOLD','FAIL','PARTIAL'):
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

    def test_preflight_before_materialize_and_verify_and_original16_worker_files(self):
        tree=ast.parse((HERE/'supervisor.py').read_bytes());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        first=functions['materialize'].body[1]
        self.assertIsInstance(first,ast.Expr);self.assertEqual(first.value.func.id,'verify_rebuilt_artifacts')
        first=functions['verify_config'].body[0]
        self.assertIsInstance(first,ast.Assign);self.assertEqual(first.targets[0].id,'bindings');self.assertEqual(first.value.func.id,'verify_rebuilt_artifacts')
        for statement in functions['verify_config'].body[1:4]:
            self.assertIsInstance(statement,ast.Expr);self.assertEqual(statement.value.func.id,'need')
        call=functions['source_pins'].body[0].value;self.assertEqual(len(call.generators[0].iter.elts),16)
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


if __name__=='__main__':unittest.main(verbosity=2)
