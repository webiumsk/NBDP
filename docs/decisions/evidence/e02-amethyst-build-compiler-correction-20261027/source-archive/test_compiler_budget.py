"""Defined only: five pure AST/definition compiler and artifact-clock regressions.

Reads exact source/data operands only. Does not import or execute a build module,
create runtime files, read clocks, invoke tools, compile Amethyst or use keys.
"""
import ast
import copy
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

OLD=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r5')
NEW=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-preparation-r6')
ADOPTION=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-amethyst-build-compiler-correction-20261027/method-adoption.json')
KINDS=(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)


def tree(root,relative):return ast.parse((root/relative).read_text())
def doc(relative):return json.loads((NEW/relative).read_text())
def function(module,name):return next(n for n in module.body if isinstance(n,KINDS) and n.name==name)
def method(module,cls,name):return next(n for n in function(module,cls).body if isinstance(n,ast.FunctionDef) and n.name==name)
def ast_text(node):return ast.dump(node,include_attributes=False)
def need_call(node,message):
    return next(n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value==message)
def assignment(module,function_name,name):
    return next(n for n in ast.walk(function(module,function_name)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
def command_literals(module):
    values=assignment(module,'main','argv').value.elts
    return [n.value for n in values if isinstance(n,ast.Constant)]
def extracted(module,names,environment):
    # Compile only explicitly named pure definitions; never execute a module body.
    selected=ast.Module(body=[copy.deepcopy(function(module,n)) for n in names],type_ignores=[])
    scope=dict(environment)
    exec(compile(ast.fix_missing_locations(selected),'<selected-pure-source-definitions>','exec'),scope)
    return scope


class PriorClockNormalization(ast.NodeTransformer):
    """Reverse only the adopted artifact seconds for full-function equality."""
    def visit_Constant(self,node):
        mapping={3600:1800,3645:1845,3900:2100,4200:2400,'3600s':'1800s'}
        if type(node.value) in (int,str) and node.value in mapping:return ast.copy_location(ast.Constant(mapping[node.value]),node)
        return node


class CompilerAndBudget(unittest.TestCase):
    def test_exact_compiler_command_property_delta_and_inner_clock(self):
        old=tree(OLD,'preparation/build_inside.py');new=tree(NEW,'preparation/build_inside.py')
        before=assignment(old,'main','argv');after=assignment(new,'main','argv')
        expected=copy.deepcopy(before.value)
        mapping={'--max-workers=3':'--max-workers=1',
                 '-Dorg.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=768m -Dfile.encoding=UTF-8 -Duser.home=/work/user':'-Dorg.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=768m -Dfile.encoding=UTF-8 -Duser.home=/work/user',
                 '-Dkotlin.daemon.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=512m':'-Pkotlin.daemon.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=512m'}
        changed=[]
        for element in expected.elts:
            if isinstance(element,ast.Constant) and element.value in mapping:
                changed.append(element.value);element.value=mapping[element.value]
        self.assertEqual(set(changed),set(mapping))
        expected.elts.extend([ast.Constant('-Pkotlin.compiler.execution.strategy=in-process'),ast.Constant('--info')])
        self.assertEqual(ast_text(after.value),ast_text(expected))
        # Remove exactly the reviewed argv delta, then every inner statement is equal
        # after reversing only the adopted subprocess timeout.
        after.value=before.value
        self.assertEqual(ast_text(PriorClockNormalization().visit(new)),ast_text(old))

    def test_entire_non_clock_supervisor_and_materializer_guards_unchanged(self):
        for relative in ('supervisor-source/supervise_build.py','materializer-source/materialize.py'):
            old=tree(OLD,relative);new=tree(NEW,relative)
            before={n.name:ast_text(n) for n in old.body if isinstance(n,KINDS)}
            after={n.name:ast_text(PriorClockNormalization().visit(n)) for n in new.body if isinstance(n,KINDS)}
            self.assertEqual(after,before,relative)
        # Inner source/archive/APK/signature/output predicates are covered by the
        # entire-module equality in the exact-command test, not a reduced list.
        self.assertEqual((NEW/'supervisor-source/test_installed_sdk_bindings.py').read_bytes(),(OLD/'supervisor-source/test_installed_sdk_bindings.py').read_bytes())

    def test_actual_budget_graph_and_exact_owned_timeout_command(self):
        plan=doc('supervisor-source/plan.json');build=doc('preparation/build-plan.json')
        adopted=json.loads(ADOPTION.read_text())['artifactOnlySeconds']
        self.assertEqual(adopted,dict(job=3600,attachedCli=3645,supervisor=3900,cleanupReserve=120,rootLease=4200,outer=4197,outerKillGrace=3,jobKillGrace=5))
        for key,value in dict(jobSeconds=3600,attachedCliSeconds=3645,outerSeconds=3900,cleanupReserveSeconds=120,rootReleaseMaximumSeconds=4200,outerWrapperSeconds=4197,outerWrapperKillGraceSeconds=3,jobKillGraceSeconds=5,memoryBytes=6442450944,cpus=4,pids=512,minimumFreeBuildDiskBytes=12884901888).items():self.assertEqual(plan['limits'][key],value,key)
        for key,value in dict(buildSeconds=3600,outerTotalSeconds=3900,attachedCliSeconds=3645,maximumRootLeaseSeconds=4200,outerWrapperSeconds=4197,outerWrapperKillGraceSeconds=3,gradleHeap='4g',gradleMetaspace='768m',gradleMaxWorkers=1,kotlinHeap='1536m',kotlinMetaspace='512m',memoryBytes=6442450944,cpus=4,pids=512,minimumFreeBuildDiskBytes=12884901888).items():self.assertEqual(build['limits'][key],value,key)
        sup=tree(NEW,'supervisor-source/supervise_build.py')
        scope=extracted(sup,['need','full_cid','create_argv'],dict(re=re,DOCKER='/usr/bin/docker',NAME='nbdp-amethyst-build-20261026',NETWORK='nbdp-amethyst-build-20261026',TIMEOUT='/usr/bin/timeout',JOB_FILE_LIMIT=536870912))
        argv=scope['create_argv'](build,'b'*32,Path('/SYNTHETIC/cidfile'),'a'*64)
        self.assertEqual(argv[-6:],['/usr/bin/timeout','--signal=TERM','--kill-after=5s','3600s','/usr/bin/python3','/prep/build_inside.py'])
        image=plan['image'];base=build['proposedDockerCreateArgv'];command=base[base.index(image)+1:]
        assertion=need_call(function(sup,'owned_identity'),'EXACT_INTERNAL_JOB_TIMEOUT_COMMAND').args[0]
        expression=compile(ast.Expression(assertion),'<owned-timeout-expression>','eval')
        context=dict(command=command,TIMEOUT='/usr/bin/timeout',config={'Cmd':argv[argv.index(image)+1:]})
        self.assertTrue(eval(expression,{},context))
        context['config']['Cmd']=[x if x!='3600s' else '1800s' for x in context['config']['Cmd']]
        self.assertFalse(eval(expression,{},context))
        init=method(sup,'Supervisor','__init__')
        constants=[n.value for n in ast.walk(init) if isinstance(n,ast.Constant) and type(n.value) is int]
        self.assertIn(3900,constants);self.assertIn(120,constants)
        run=method(sup,'Supervisor','run')
        attached=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='cli' and any(isinstance(k,ast.keyword) and k.arg=='attached' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords))
        self.assertEqual(next(k.value.value for k in attached.keywords if k.arg=='seconds'),3645)
        self.assertIn(3645,[n.value for n in ast.walk(need_call(run,'FULL_ORIGINAL_JOB_ATTACH_BUDGET_BEFORE_START')) if isinstance(n,ast.Constant) and type(n.value) is int])
        pre=method(sup,'Supervisor','prerequisites')
        self.assertIn(3645,[n.value for n in ast.walk(need_call(pre,'ENOUGH_ORIGINAL_BUDGET_FOR_JOB_AND_CLI')) if isinstance(n,ast.Constant) and type(n.value) is int])
        self.assertEqual(plan['state'],'SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW_AND_ROOT_RELEASE')

    def test_actual_lease_predicate_rejects_expired_insufficient_old_mismatch(self):
        sup=tree(NEW,'supervisor-source/supervise_build.py')
        condition=need_call(method(sup,'Supervisor','prerequisites'),'CURRENT_ROOT_RELEASE_COVERS_ORIGINAL_FINITE_SCOPE').args[0]
        expression=compile(ast.Expression(condition),'<actual-lease-expression>','eval')
        now=10**18
        def allowed(issued,end):return eval(expression,{},dict(issued=issued,end=end,time=SimpleNamespace(time_ns=lambda:now)))
        self.assertTrue(allowed(now,now+4200*10**9))
        for issued,end in [(now,now-1),(now+1,now+4200*10**9),(now,now+2400*10**9),(now,now+3899*10**9),(now,now+4201*10**9),(now-301*10**9,now+3900*10**9)]:
            with self.subTest(issued=issued,end=end):self.assertFalse(allowed(issued,end))

    def test_materializer_null_clocks_fresh_only_two_fields_and_overflow(self):
        mat=tree(NEW,'materializer-source/materialize.py')
        values={}
        for node in mat.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('PINNED','CLOCKS','RELEASE_KEYS','SDK_RELEASE_FIELDS') for t in node.targets):
                values[node.targets[0].id]=eval(compile(ast.Expression(node.value),'<pure-source-constant>','eval'),dict(set=set))
        values.update(Path=Path,re=re,WORK=Path('/Data/nbdp-e02-tooling-20261027/amethyst-build-r6/controller'))
        scope=extracted(mat,['need','pin_shape','sdk_release_shape','validate','fresh'],values)
        t=doc('materializer-source/root-authorized-template.example.json');r=t['release']
        r.update(executionAuthorized=True,runId='b'*32,networkId='a'*64,networkLabels={'nbdp.owner':'e02-amethyst-rebuild-20261026','nbdp.scope':'isolated-build-bootstrap'})
        d=dict(path='/SYNTHETIC/pin.json',bytes=1,sha256='c'*64)
        r['sourceReviews']=[copy.deepcopy(d),copy.deepcopy(d)]
        r['prerequisiteAcceptances']=[copy.deepcopy(d),copy.deepcopy(d),r['installedSdkAcceptance']]
        t.update(decision='AUTHORIZE_ONE_FIXED_AMETHYST_BUILD_DISPATCH',expectedOutput=str(values['WORK']/('attempt-'+r['runId'])),metadata=[copy.deepcopy(d) for _ in range(3)])
        self.assertEqual(scope['validate'](t),r)
        bad=copy.deepcopy(t);bad['release']['issuedAtUtcNs']=1
        with self.assertRaisesRegex(ValueError,'FIXED_TARGET_NULL_CLOCK_SLOTS'):scope['validate'](bad)
        now=10**18;live=scope['fresh'](r,now)
        self.assertEqual(live['issuedAtUtcNs'],now);self.assertEqual(live['notAfterUtcNs'],now+4200*10**9)
        self.assertEqual({k:v for k,v in live.items() if k not in ('issuedAtUtcNs','notAfterUtcNs')},{k:v for k,v in r.items() if k not in ('issuedAtUtcNs','notAfterUtcNs')})
        self.assertIsNone(r['issuedAtUtcNs']);self.assertIsNone(r['notAfterUtcNs'])
        maximum=9223372036854775807-4200*10**9
        self.assertEqual(scope['fresh'](r,maximum)['notAfterUtcNs'],9223372036854775807)
        for invalid in (0,-1,maximum+1,1.5,True):
            with self.subTest(invalid=invalid),self.assertRaisesRegex(ValueError,'EXACT_NS_CLOCK'):scope['fresh'](r,invalid)


if __name__=='__main__':unittest.main(verbosity=2)
