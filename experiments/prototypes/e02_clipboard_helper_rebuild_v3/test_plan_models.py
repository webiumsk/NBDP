"""PREPARED NOT EXECUTED: pure helper-plan/CLI DATA refusal models.

Fake descriptors validate shape only; validate_inputs still requires real exact
files and source-reviewed acquired wrappers. No tools, compile, keys or APK run.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_helper as h


def fake_pin(path):return dict(path=str(path),bytes=1,sha256='0'*64)


def shape():
    return dict(schema='e02-clipboard-helper-rebuild-plan-v2',scope='OFFLINE_REBUILT_HELPER_ARTIFACT_ONLY',
        state='PINNED_INPUTS_REQUIRES_SEPARATE_ROOT_RELEASE',outputRoot=str(h.OUT),
        sources=[fake_pin(p) for p in sorted(h.source_paths())],tools=[fake_pin(p) for p in sorted(h.tool_paths())],
        limits=dict(phaseSeconds=180,commandSeconds=60),
        jvm=dict(javaToolOptions=h.JVM_FLAGS,meaning='Configured environment options; acquired wrapper command-line defaults can override heap and need separate source observation.'),
        toolAcceptance=fake_pin('/SYNTHETIC_DATA_ONLY/tool-acceptance.json'),wrapperHeapEvidence=fake_pin('/SYNTHETIC_DATA_ONLY/wrapper-observation.json'))


class PlanModels(unittest.TestCase):
    def reject(self,change):
        value=shape();change(value)
        with self.assertRaises(ValueError):h.validate_shape(value)

    def test_positive_shape_only_not_tool_authentication(self):h.validate_shape(shape())
    def test_not_ready_state_refuses(self):self.reject(lambda p:p.update(state='NOT_READY'))
    def test_missing_tool_hash_refuses(self):self.reject(lambda p:p['tools'][0].pop('sha256'))
    def test_null_tool_hash_refuses(self):self.reject(lambda p:p['tools'][0].update(sha256=None))
    def test_duplicate_tool_alias_refuses(self):self.reject(lambda p:p['tools'].__setitem__(0,copy.deepcopy(p['tools'][1])))
    def test_foreign_tool_path_refuses(self):self.reject(lambda p:p['tools'][0].update(path='/SYNTHETIC_FOREIGN/java'))
    def test_old_source_path_cannot_substitute_new_builder(self):
        self.reject(lambda p:p['sources'][0].update(path='/SYNTHETIC_OLD/build_helper.py'))
    def test_old_apk_identity_field_refuses(self):self.reject(lambda p:p.update(oldApkSha256='a680e513a9b36cab634620507b77bba36532ce13acb465a860c7bef60d23ec20'))
    def test_original_phase_deadline_cannot_increase(self):self.reject(lambda p:p['limits'].update(phaseSeconds=181))
    def test_original_command_deadline_cannot_increase(self):self.reject(lambda p:p['limits'].update(commandSeconds=61))
    def test_jvm_environment_configuration_cannot_silently_change(self):
        self.reject(lambda p:p['jvm'].update(javaToolOptions='-Xmx4g'))
    def test_old_output_root_refuses(self):self.reject(lambda p:p.update(outputRoot='/tmp/nbdp-e02-ordinary-client-v1/helper-build-20261023a'))

    def test_all_eight_original_cli_commands_and_flags_are_preserved(self):
        old=h.HERE.parent/'e02_ordinary_client_v1/build_helper.py'
        raw=old.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'a9df1f4045fa6144a3ae7d36d4a8a46524be37138bd7ec8f5b7b8cd17d4762c8')
        tree=ast.parse(raw)
        # Interpret only literal/path list DATA, never eval/import old source.
        values={'JDK':h.JDK,'TOOLS':h.TOOLS,'ANDROID_JAR':h.ANDROID_JAR,'HERE':h.HERE,'out':h.OUT,
            'java':h.HERE/'clipboard-helper/src/org/nbdp/clipboard/capture/CaptureActivity.java',
            'unsigned':h.OUT/'unsigned.apk','apk':h.OUT/'clipboard-capture.apk'}
        def literal(node):
            if isinstance(node,ast.Constant):return node.value
            if isinstance(node,ast.Name) and node.id in values:return values[node.id]
            if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):return literal(node.left)/literal(node.right)
            if isinstance(node,ast.List):return [literal(x) for x in node.elts]
            raise ValueError('UNEXPECTED_ORIGINAL_COMMAND_AST')
        expected=[literal(node.args[0]) for node in ast.walk(tree) if isinstance(node,ast.Call) and
            isinstance(node.func,ast.Name) and node.func.id=='run']
        self.assertEqual(len(expected),8)
        self.assertEqual(h.command_plan(h.OUT),expected)


class WrapperHeapModels(unittest.TestCase):
    def observation(self,d8=2048,apksigner=1024):
        tools={str(h.TOOLS/name):fake_pin(h.TOOLS/name) for name in ('d8','apksigner')}
        rows={name:dict(tool=tools[str(h.TOOLS/name)],flagsUnchanged=True,
            effectiveHeapMiBFromSource=heap,notRuntimeMeasured=True)
            for name,heap in (('d8',d8),('apksigner',apksigner))}
        return dict(wrappers=rows),tools

    def test_observed_actual_wrapper_defaults_fit_source2_only(self):
        path=h.HERE.parents[2]/'docs/decisions/evidence/e02-clipboard-helper-rebuild-20261027/wrapper-source-observation-r1.json'
        raw=path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'37f8137bee5bf1acb611d1e0ddb4a785ce827a89f82f59065f280a489d925161')
        value=json.loads(raw)
        for name,literal,wanted in (('d8','defaultMx="-Xmx2G"',2048),('apksigner','defaultMx="-Xmx1024M"',1024)):
            row=value['wrappers'][name]
            self.assertIn(literal,''.join(part['raw'] for part in row['rawWrapperSnippets']))
            self.assertEqual(row['effectiveHeapMiBFromSource'],wanted)
        # Actual source-derived record DATA only; no tool/JVM launch or pin authentication.
        tools={r['path']:r for r in value['tools']}
        self.assertIs(h.validate_wrapper_heaps(value,tools),value)

    def test_previous_512_1024_heap_admissions_are_preserved(self):
        for d8 in (512,1024):
            for signer in (512,1024):
                with self.subTest(d8=d8,signer=signer):
                    value,tools=self.observation(d8,signer);h.validate_wrapper_heaps(value,tools)

    def test_unknown_or_noninteger_heap_refuses(self):
        for unknown in (None,'2048',True):
            with self.subTest(heap=unknown):
                value,tools=self.observation(d8=unknown)
                with self.assertRaisesRegex(ValueError,'EFFECTIVE_WRAPPER_HEAP_UNRESOLVED_OR_NEEDS_VERSIONED_REVIEW'):
                    h.validate_wrapper_heaps(value,tools)

    def test_larger_d8_heap_refuses(self):
        value,tools=self.observation(d8=4096)
        with self.assertRaisesRegex(ValueError,'EFFECTIVE_WRAPPER_HEAP_UNRESOLVED_OR_NEEDS_VERSIONED_REVIEW'):
            h.validate_wrapper_heaps(value,tools)

    def test_d8_exception_does_not_admit_apksigner_2048(self):
        value,tools=self.observation(apksigner=2048)
        with self.assertRaisesRegex(ValueError,'EFFECTIVE_WRAPPER_HEAP_UNRESOLVED_OR_NEEDS_VERSIONED_REVIEW'):
            h.validate_wrapper_heaps(value,tools)

    def test_2048_admission_still_requires_exact_wrapper_binding(self):
        value,tools=self.observation()
        value['wrappers']['d8']['tool']=fake_pin('/SYNTHETIC_FOREIGN/d8')
        with self.assertRaisesRegex(ValueError,'EXACT_REVIEWED_WRAPPER_SOURCE_BINDING'):
            h.validate_wrapper_heaps(value,tools)


if __name__=='__main__':unittest.main(verbosity=2)
