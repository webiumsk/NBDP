// Loopback TCP forwarding only, for Docker --internal networks that omit host NAT.
// Container IPs must come from docker inspect of the two named disposable containers.
import { createServer,connect } from 'node:net';
import { readFileSync } from 'node:fs';
const ips=JSON.parse(readFileSync('.runtime/relay-ips.json'));
const servers=[];
for(const [name,listen,target] of [['strfry',17777,7777],['rs-relay',18081,8080]]){
 const host=ips[name];if(!/^172\.\d+\.\d+\.\d+$/.test(host))throw Error('Expected inspected internal lab IP');
 const server=createServer(client=>{const upstream=connect({host,port:target});client.pipe(upstream);upstream.pipe(client);client.on('error',()=>upstream.destroy());upstream.on('error',()=>client.destroy());client.on('close',()=>upstream.destroy());upstream.on('close',()=>client.destroy());});
 server.listen(listen,'127.0.0.1',()=>console.log(JSON.stringify({name,loopback:listen,internal_target:host+':'+target})));servers.push(server);
}
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{for(const s of servers)s.close();});
