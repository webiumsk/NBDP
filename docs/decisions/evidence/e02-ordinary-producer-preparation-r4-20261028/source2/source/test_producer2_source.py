"""Producer4 SOURCE integration definitions; actual execution separately gated.

These assert preserved isolation/criteria and required operational closure. They
are not client interoperability, source approval or helper throughput evidence.
"""
import ast
import hashlib
import json
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
OLD=Path('/Data/nbdp-e02-tooling-20261027/ordinary-producer-final-preparation-r3')


def assignment(path,name):
    tree=ast.parse(path.read_bytes())
    return next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))


class Producer4SourceBindings(unittest.TestCase):
    def test_original_guard_and_dependency_boundaries_unchanged(self):
        for n in ['lease_guard.py','test_lease_guard.py','dependency-tree.mjs','dependency-tree.json','phase-writer.mjs']:
            self.assertEqual((HERE/n).read_bytes(),(OLD/n).read_bytes())

    def test_original_isolation_and_transport_limits(self):
        for n in ['CONFIG','EMULATOR','LIMITS','ROLES','RUNTIME','RELAY','PY','LOG_OPTIONS']:
            self.assertEqual(ast.dump(assignment(HERE/'supervisor.py',n)),ast.dump(assignment(OLD/'supervisor.py',n)))
        old=json.loads((OLD/'fixture-plan.json').read_bytes());new=json.loads((HERE/'fixture-plan.json').read_bytes())
        self.assertEqual(new['limits'],old['limits'])
        self.assertEqual(new['limits']['networkTimeoutMilliseconds'],10000)
        self.assertEqual(new['limits']['captureBytes'],16777216)

    def test_fresh_source_closure_twenty_two_not_old_sixteen(self):
        tree=ast.parse((HERE/'supervisor.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_pins')
        names=[n.value for n in ast.walk(fn) if isinstance(n,ast.Constant) and type(n.value) is str]
        self.assertEqual(len(names),22)
        for n in ['guard-helper.py','guard-wire.mjs','guard-client-core.mjs','guard-client.mjs','guard-transport-boundaries.mjs','capture-allocation.mjs']:self.assertIn(n,names)
        for role in ['incoming','archive']:
            c=json.loads((HERE/(role+'-run-config.json')).read_bytes())
            self.assertEqual({Path(d['path']).name for d in c['sourceAndDependencyPins']},set(names))
            for d in c['sourceAndDependencyPins']:
                raw=Path(d['path']).read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(d['bytes'],d['sha256']))
            self.assertEqual(c['originalLeaseSeconds'],1800)
            self.assertNotIn(c['runId'],['9d8bad6df86fc113f87e14e2974f9019','1f45958c9bc2c7394cb3df00276a3abb'])

    def test_oracles_and_original_role_replay_criteria_preserved(self):
        for n in ['business-rumor.json','chat-rumor.json']:self.assertEqual((HERE/n).read_bytes(),(OLD/n).read_bytes())
        old=json.loads((OLD/'minimum-plan.json').read_bytes());new=json.loads((HERE/'minimum-plan.json').read_bytes())
        for k in ['roles','businessId','chatId','perWindowOriginalLeaseSeconds','maximumConcurrentWindows']:self.assertEqual(old[k],new[k])
        self.assertEqual(new['perWindowOriginalLeaseSeconds'],1800)

    def test_no_sync_python_spawn_or_cached_authorization_in_fixture(self):
        source=(HERE/'fixture.mjs').read_text()
        self.assertNotIn('function guardCheck()',source)
        self.assertNotIn("spawnSync('/guard-python",source)
        # The original native Rust validation remains synchronous with originalcap.
        self.assertIn('timeout:p.limits.rustTimeoutMilliseconds',source)
        helper=(HERE/'guard-helper.py').read_text()
        self.assertEqual(helper.count('lease = module.Lease('),1)
        self.assertEqual(helper.count('now = lease.check()'),1)
        self.assertNotIn('lease.previous =',helper)

    def test_flow_checkpoints_preserve_all_fifteen_original_internal_guards(self):
        source=(HERE/'fixture.mjs').read_text()
        for i in range(1,16):self.assertEqual(source.count("yield {guard:'flow:original-%02d'}"%i),1)
        self.assertIn('step=await serviceGuard(step.value.guard,bytes,()=>iterator.next()',source)
        self.assertIn('const value=await step.value.wait;step=iterator.next(value)',source)
        self.assertIn("stage.id+'-query'",source)
        self.assertIn('const initial=T.wrap(rumors.business,from,spec.account)',source)

    def test_phase_and_controller_semantic_version_explicit(self):
        contract=json.loads((HERE/'guard-dto-contract.json').read_bytes())
        self.assertEqual(contract['profileId'],'e02-ordinary-minimum-rs-two-role-v3')
        self.assertEqual(contract['globalPhaseSequence'],'Unchanged integer1..N; helper-local decimal sequence is guardSequence only')
        self.assertEqual(contract['serviceCaptureStreams'],['phase','proxy'])
        self.assertEqual(contract['aggregateWindowNewRpcCaptureBytes'],16777216)
        self.assertEqual(contract['aggregateServiceCaptureBytes'],8388608)
        self.assertTrue(contract['requiresVersionedConsumerAndCompletion'])
        self.assertEqual(contract['runtimeExecutions'],0)


if __name__=='__main__':unittest.main()
