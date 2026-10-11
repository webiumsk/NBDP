import { verifyEvent } from 'nostr-tools/pure';
export function discover({candidates,peer,now,seen=0}){
 const valid=candidates.filter(v=>{try{return v.pubkey===peer&&v.kind===10050&&Number.isSafeInteger(v.created_at)&&Array.isArray(v.tags)&&v.tags.length<=64&&verifyEvent(JSON.parse(JSON.stringify(v)))}catch{return false}});
 if(!valid.length)return {state:'inbox-unavailable',destinations:[]};
 valid.sort((a,b)=>a.created_at-b.created_at);const best=valid.at(-1);
 if(valid.some(v=>v.created_at===best.created_at&&v.id!==best.id))return {state:'discovery-conflict',destinations:[]};
 if(best.created_at<seen||best.created_at>now+300||now-best.created_at>864000)return {state:'stale-or-rollback',destinations:[]};
 const urls=[];
 for(const t of best.tags){if(t[0]!=='relay'||t.length!==2)return {state:'malformed-inbox',destinations:[]};try{const u=new URL(t[1]);if(u.protocol!=='ws:'||!['127.0.0.1','localhost'].includes(u.hostname)||u.username||u.password)throw Error('unsafe');urls.push(t[1]);}catch{return {state:'unsafe-lab-route',destinations:[]};}}
 const destinations=[...new Set(urls)].sort();if(!destinations.length)return {state:'inbox-empty',destinations:[]};
 return {state:'ready',destinations,list_id:best.id};
}
