"""Defined only: three pure SOURCE clock regressions, no module/tool execution.

Reads explicitly pinned source/JSON operands. Compiles only selected pure
functions or predicate expressions with synthetic values, never a build module.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

OLD=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r7')
NEW=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r8')
ADOPTION=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-amethyst-clock90-correction-20261028/method-adoption.json')
KINDS=(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)


def tree(root,relative):return ast.parse((root/relative).read_text())
def doc(relative):return json.loads((NEW/relative).read_text())
def ast_text(node):return ast.dump(node,include_attributes=False)
def function(module,name):return next(n for n in module.body if isinstance(n,KINDS) and n.name==name)
def method(module,cls,name):return next(n for n in function(module,cls).body if isinstance(n,ast.FunctionDef) and n.name==name)
def need_call(node,message):
    return next(n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value==message)
def assignment(module,name):return next(n for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
def pin(path):
    b=path.read_bytes();return dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def extracted(module,names,environment):
    scope=dict(environment)
    selected=ast.Module(body=[copy.deepcopy(function(module,n)) for n in names],type_ignores=[])
    exec(compile(ast.fix_missing_locations(selected),'<selected-pure-source-definitions>','exec'),scope)
    return scope


class ReverseOnlyClockAndLocation(ast.NodeTransformer):
    def visit_Constant(self,node):
        mapping={5400:3600,5445:3645,5700:3900,6000:4200,'5400s':'3600s'}
        if type(node.value) in (int,str) and node.value in mapping:return ast.copy_location(ast.Constant(mapping[node.value]),node)
        if type(node.value) is str:
            value=node.value.replace(str(NEW),str(OLD)).replace('amethyst-build-r8','amethyst-build-r7')
            return ast.copy_location(ast.Constant(value),node)
        return node


class Clock90(unittest.TestCase):
    def test_full_nonclock_module_ast_and_exact_verified_pinned_cascade(self):
        for relative in ('preparation/build_inside.py','supervisor-source/supervise_build.py','materializer-source/materialize.py'):
            old=tree(OLD,relative);new=tree(NEW,relative)
            if relative=='materializer-source/materialize.py':
                old_assignment=assignment(old,'PINNED');new_assignment=assignment(new,'PINNED')
                prior=ast.literal_eval(old_assignment.value);actual=ast.literal_eval(new_assignment.value)
                expected=[prior[0]]+[pin(NEW/'supervisor-source'/name) for name in ('supervise_build.py','subject.json','plan.json')]
                self.assertEqual(actual,expected)
                new_assignment.value=copy.deepcopy(old_assignment.value)
            self.assertEqual(ast_text(ReverseOnlyClockAndLocation().visit(new)),ast_text(old),relative)
        # Full modules cover identical compiler argv, exact prefix classifier,
        # source/APK/privacy/ownership/resource/admission/cleanup guards.

    def test_actual_clock_graph_owned_argv_and_expired_short_old_mismatch_refusal(self):
        plan=doc('supervisor-source/plan.json');build=doc('preparation/build-plan.json')
        self.assertEqual(json.loads(ADOPTION.read_text())['artifactOnlySeconds'],dict(job=5400,attachedCli=5445,supervisor=5700,cleanupReserve=120,rootLease=6000,outer=5997,outerKillGrace=3,jobKillGrace=5))
        for key,value in dict(jobSeconds=5400,attachedCliSeconds=5445,outerSeconds=5700,cleanupReserveSeconds=120,rootReleaseMaximumSeconds=6000,outerWrapperSeconds=5997,outerWrapperKillGraceSeconds=3,jobKillGraceSeconds=5,memoryBytes=6442450944,cpus=4,pids=512,minimumFreeBuildDiskBytes=12884901888).items():self.assertEqual(plan['limits'][key],value,key)
        for key,value in dict(buildSeconds=5400,outerTotalSeconds=5700,attachedCliSeconds=5445,maximumRootLeaseSeconds=6000,outerWrapperSeconds=5997,outerWrapperKillGraceSeconds=3,gradleHeap='4g',gradleMaxWorkers=1,memoryBytes=6442450944,cpus=4,pids=512,minimumFreeBuildDiskBytes=12884901888).items():self.assertEqual(build['limits'][key],value,key)
        self.assertEqual(plan['state'],'SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_ROOT_RELEASE')
        sup=tree(NEW,'supervisor-source/supervise_build.py')
        scope=extracted(sup,['need','full_cid','create_argv'],dict(re=re,DOCKER='/usr/bin/docker',NAME='nbdp-amethyst-build-20261026',NETWORK='nbdp-amethyst-build-20261026',TIMEOUT='/usr/bin/timeout',JOB_FILE_LIMIT=536870912))
        argv=scope['create_argv'](build,'b'*32,Path('/SYNTHETIC/cidfile'),'a'*64)
        self.assertEqual(argv[-6:],['/usr/bin/timeout','--signal=TERM','--kill-after=5s','5400s','/usr/bin/python3','/prep/build_inside.py'])
        base=build['proposedDockerCreateArgv'];command=base[base.index(plan['image'])+1:]
        condition=need_call(function(sup,'owned_identity'),'EXACT_INTERNAL_JOB_TIMEOUT_COMMAND').args[0]
        expression=compile(ast.Expression(condition),'<actual-owned-command-condition>','eval')
        context=dict(command=command,TIMEOUT='/usr/bin/timeout',config={'Cmd':argv[argv.index(plan['image'])+1:]})
        self.assertTrue(eval(expression,{},context))
        for wrong in ('3600s','1800s','5401s'):
            context['config']['Cmd']=[x if x!='5400s' else wrong for x in argv[argv.index(plan['image'])+1:]]
            with self.subTest(wrongCommand=wrong):self.assertFalse(eval(expression,{},context))
        init=method(sup,'Supervisor','__init__')
        total=next(n for n in ast.walk(init) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='total_end' for t in n.targets))
        self.assertEqual(ast_text(total.value),ast_text(ast.parse('time.monotonic()+5700',mode='eval').body))
        work=next(n for n in ast.walk(init) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='work_end' for t in n.targets))
        self.assertEqual(ast_text(work.value),ast_text(ast.parse('self.total_end-120',mode='eval').body))
        run=method(sup,'Supervisor','run');pre=method(sup,'Supervisor','prerequisites')
        attached=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='cli' and any(k.arg=='attached' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords))
        self.assertEqual(next(k.value.value for k in attached.keywords if k.arg=='seconds'),5445)
        for node,label in [(run,'FULL_ORIGINAL_JOB_ATTACH_BUDGET_BEFORE_START'),(pre,'ENOUGH_ORIGINAL_BUDGET_FOR_JOB_AND_CLI')]:self.assertIn(5445,[n.value for n in ast.walk(need_call(node,label)) if isinstance(n,ast.Constant) and type(n.value) is int])
        inner=tree(NEW,'preparation/build_inside.py')
        child=next(n for n in ast.walk(function(inner,'main')) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='child' for t in n.targets))
        self.assertEqual(next(k.value.value for k in child.value.keywords if k.arg=='timeout'),5400)
        lease=need_call(pre,'CURRENT_ROOT_RELEASE_COVERS_ORIGINAL_FINITE_SCOPE').args[0]
        expression=compile(ast.Expression(lease),'<actual-lease-predicate>','eval');now=10**18
        def allowed(issued,end):return eval(expression,{},dict(issued=issued,end=end,time=SimpleNamespace(time_ns=lambda:now)))
        self.assertTrue(allowed(now,now+6000*10**9))
        for issued,end in [(now,now-1),(now+1,now+6000*10**9),(now,now+4200*10**9),(now,now+5699*10**9),(now,now+6001*10**9),(now-301*10**9,now+5700*10**9)]:
            with self.subTest(issued=issued,end=end):self.assertFalse(allowed(issued,end))

    def test_materializer_null_clocks_only_two_fresh_fields_and_exact_overflow(self):
        mat=tree(NEW,'materializer-source/materialize.py');values={}
        for name in ('PINNED','CLOCKS','RELEASE_KEYS','SDK_RELEASE_FIELDS'):
            values[name]=eval(compile(ast.Expression(assignment(mat,name).value),'<pure-source-constant>','eval'),dict(set=set))
        values.update(Path=Path,re=re,WORK=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-r8/controller'))
        scope=extracted(mat,['need','pin_shape','sdk_release_shape','validate','fresh'],values)
        t=doc('materializer-source/root-authorized-template.example.json');r=t['release']
        r.update(executionAuthorized=True,runId='b'*32,networkId='a'*64,networkLabels={'nbdp.owner':'e02-amethyst-rebuild-20261026','nbdp.scope':'isolated-build-bootstrap'})
        d=dict(path='/SYNTHETIC/pin.json',bytes=1,sha256='c'*64)
        r['sourceReviews']=[copy.deepcopy(d),copy.deepcopy(d)];r['prerequisiteAcceptances']=[copy.deepcopy(d),copy.deepcopy(d),r['installedSdkAcceptance']]
        t.update(decision='AUTHORIZE_ONE_FIXED_AMETHYST_BUILD_DISPATCH',expectedOutput=str(values['WORK']/('attempt-'+r['runId'])),metadata=[copy.deepcopy(d) for _ in range(3)])
        self.assertEqual(scope['validate'](t),r)
        for name in ('issuedAtUtcNs','notAfterUtcNs'):
            bad=copy.deepcopy(t);bad['release'][name]=1
            with self.subTest(nonNullClock=name),self.assertRaisesRegex(ValueError,'FIXED_TARGET_NULL_CLOCK_SLOTS'):scope['validate'](bad)
        now=10**18;live=scope['fresh'](r,now)
        self.assertEqual(live['issuedAtUtcNs'],now);self.assertEqual(live['notAfterUtcNs'],now+6000*10**9)
        self.assertEqual({k:v for k,v in live.items() if k not in ('issuedAtUtcNs','notAfterUtcNs')},{k:v for k,v in r.items() if k not in ('issuedAtUtcNs','notAfterUtcNs')})
        self.assertIsNone(r['issuedAtUtcNs']);self.assertIsNone(r['notAfterUtcNs'])
        maximum=9223372036854775807-6000*10**9
        self.assertEqual(scope['fresh'](r,maximum)['notAfterUtcNs'],9223372036854775807)
        for invalid in (0,-1,maximum+1,1.5,True):
            with self.subTest(invalid=invalid),self.assertRaisesRegex(ValueError,'EXACT_NS_CLOCK'):scope['fresh'](r,invalid)


if __name__=='__main__':unittest.main(verbosity=2)
