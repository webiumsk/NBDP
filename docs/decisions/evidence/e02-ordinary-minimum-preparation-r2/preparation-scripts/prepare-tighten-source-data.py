from pathlib import Path
p=Path('experiments/prototypes/e02_ordinary_minimum_v2/fixture.mjs');s=p.read_text()
s=s.replace(" const phase=(name,fields={})=>{try{budget.healthy();const row=phaseWriter(name,fields);", " const phase=(name,fields={})=>{if(closed)throw firstFailure??Error('SERVICE_CLOSED');try{budget.healthy();const row=phaseWriter(name,{profileId:PROFILE,windowId:p.roleSpec.windowId,ordinaryRole:p.ordinaryRole,observedAttempt:activeAttempt?{...activeAttempt}:null,...fields});")
s=s.replace("const terminated=new WeakSet();let firstFailure=null", "const terminated=new WeakSet(),exchangeSockets=new Set();let firstFailure=null")
s=s.replace("class OwnedWebSocket extends WebSocket{terminate(){", "class OwnedWebSocket extends WebSocket{constructor(...args){super(...args);exchangeSockets.add(this);}terminate(){")
s=s.replace("for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));", "for(const c of connections.values())for(const socket of [c.app,c.upstream])attempt('terminate-owned-proxy',()=>terminateOwned(socket));\n  for(const socket of exchangeSockets)attempt('terminate-owned-exchange',()=>socket.terminate());")
# Install error/close listeners before first fallible OPEN observation.
a=s.index("  for(const [origin,socket] of [['APP',app],['RELAY',upstream]]){")
b=s.index("\n }catch(error){terminateOwned(app);fatal(error);}});",a)
listeners=s[a:b]
s=s[:a]+s[b:]
needle="  log({connection:c.id,direction:'OPEN',userAgent:"
pos=s.index(needle)
s=s[:pos]+listeners+'\n'+s[pos:]
s=s.replace(" }catch(error){terminateOwned(app);fatal(error);}});", " }catch(error){try{terminateOwned(app);}catch{}fatal(error);}});")
# Each completed service operation and controller reply has an explicit guest
# full-tree end boundary; no reliance on Docker rm -f delivering SIGTERM.
s=s.replace("  check();need(response.ok===true", "  check();verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);need(response.ok===true")
s=s.replace(";check();socket.end(JSON.stringify({schema:'e02-minimum-fixture-command-v2'", ";check();verifyDependencyTree('/input/node_modules',doc(p.dependencyTree.path),p.dependencyFiles);socket.end(JSON.stringify({schema:'e02-minimum-fixture-command-v2'")
p.write_text(s)
