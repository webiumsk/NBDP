import ast,json,hashlib,sys
from pathlib import Path
owned=Path('/home/peterhorvath/apps/bitcoin/NBDP/docs/decisions/evidence/e02-consumer-eose-basis-successor-20261105/source3');sys.path.insert(0,str(owned));import prepare_coupled as b
source=b.PREDECESSOR/'source';values=b.assignments((source/'consumer.py').read_bytes());code=sorted((*values['RUNTIME_FILES'],*values['CONTROL_FILES'],*b.EXTRAS));bodies={name:(source/name).read_bytes() for name in code}
clockpath=owned.parent/'root-consumer-control-clock-selection.json';raw=clockpath.read_bytes();clockpin=b.descriptor(clockpath,raw);assert clockpin['sha256']==b.CLOCK_SHA
bodies['consumer.py']=b.install_clock_source(bodies['consumer.py'],clockpin,json.loads(raw),values['CONTROL_FILES']);bodies['test_request_families.py']=b.adapt_request_fixture(bodies['test_request_families.py']);bodies['test_source_bindings.py']=b.add_clock_controls(bodies['test_source_bindings.py']);fp=owned.parent/'root-required-failed-inventory-selection.json';fr=fp.read_bytes();fpin=b.descriptor(fp,fr);assert fpin['sha256']==b.FAILED_SHA;bodies['consumer.py']=b.install_failed_inventory_source(bodies['consumer.py'],fpin,json.loads(fr));bodies['test_data_controls.py']=b.add_failed_inventory_controls(bodies['test_data_controls.py']);graph,_=b.static_import_closure(bodies,values['RUNTIME_FILES'])
groups=[];changes=[];added=[]
for name in values['CONTROL_FILES']:
 old=b.methods((source/name).read_bytes());new=b.methods(bodies[name]);assert old.keys()<=new.keys()
 groups.append(dict(name=name,count=len(new)));changes.extend(name+':'+m for m in old if old[m]!=new[m]);added.extend(name+':'+m for m in new if m not in old)
assert len(changes)==2 and len(added)==10
baseline=b.PREDECESSOR.parent.parent/'e02-consumer-current178-source-20261105/source3/source';original=0
for name in values['CONTROL_FILES']:
 old=baseline/name
 if old.exists():
  methods=b.methods(old.read_bytes());assert methods.keys()<=b.methods(bodies[name]).keys();original+=len(methods)
assert original==352
for name in ('capture_contracts.py','capture_outputs.py','request_families.py'):assert bodies[name]==(baseline/name).read_bytes()
prefix=ast.parse((baseline/'probe_adapter.py').read_bytes()).body;after=ast.parse(bodies['probe_adapter.py']).body;assert [ast.dump(n,include_attributes=False) for n in prefix]==[ast.dump(n,include_attributes=False) for n in after[:len(prefix)]]
out=dict(schema='e02-consumer-source3-draft-static-audit-v1',author=b.AUTHOR,sourceCount=len(code),runtimeSourceCount=len(values['RUNTIME_FILES']),controlGroups=groups,modelsDefined=sum(g['count'] for g in groups),canonicalModelsExecuted=0,predecessorNamesPreserved=440,originalPurposesPreserved=352,changedPredecessorMethods=changes,addedMethods=added,requiredFailedInventorySelection=fpin,originalProbeAstPrefixNodes=len(prefix),originalProbeAstAndImportsUnchanged=True,legacyHelperParsersByteIdentical=True,runtimeClosureDerived=graph['runtimeCount'],clockSelection=clockpin,finalFreezeIssued=False,sourceSelectorsStillUnbound=True)
path=owned/'draft-static-audit.json';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
