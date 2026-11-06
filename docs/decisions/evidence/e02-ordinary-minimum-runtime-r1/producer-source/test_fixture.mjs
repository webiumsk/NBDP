// Pure source controls only: these synthetic maps are not app/relay observations.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {matchesFilter,matchingSubscription,publicationGenerationMatches} from './fixture.mjs';
const recipient='b'.repeat(64),event={id:'a'.repeat(64),pubkey:'c'.repeat(64),kind:1059,created_at:100,tags:[['p',recipient]]};
const good={kinds:[1059],'#p':[recipient],since:99,until:101};
assert.equal(matchesFilter(good,event,recipient),true);
for(const f of [{...good,kinds:[14]},{...good,'#p':['d'.repeat(64)]},{...good,since:101},{...good,until:99},{...good,since:true},{...good,authors:['d']},{...good,ids:['d']},{...good,'#x':['missing']},null])assert.equal(matchesFilter(f,event,recipient),false);
const c={id:1,active:true,subscriptions:new Map([['sub',{req:1,eose:null,filters:[good]}]])};
const m=new Map([[1,c]]);assert.equal(matchingSubscription(m,event,recipient),null);
c.subscriptions.get('sub').eose=2;assert.equal(matchingSubscription(m,event,recipient).eoseSequence,2);
c.active=false;assert.equal(matchingSubscription(m,event,recipient),null);c.active=true;c.subscriptions.delete('sub');assert.equal(matchingSubscription(m,event,recipient),null);
// Original generation custody: identical connection/subscription IDs are insufficient.
const original={req:10,eose:11,filters:[good]};c.subscriptions.set('sub',original);
const before=matchingSubscription(m,event,recipient);
assert.equal(publicationGenerationMatches(m,before,event,recipient),true);
c.subscriptions.set('sub',{req:12,eose:null,filters:[good]});
assert.equal(publicationGenerationMatches(m,before,event,recipient),false);
c.subscriptions.get('sub').eose=13;
assert.equal(publicationGenerationMatches(m,before,event,recipient),false);
c.subscriptions.set('sub',{...original,eose:14});
assert.equal(publicationGenerationMatches(m,before,event,recipient),false);
c.subscriptions.set('sub',original);c.active=false;
assert.equal(publicationGenerationMatches(m,before,event,recipient),false);
c.active=true;c.subscriptions.delete('sub');
assert.equal(publicationGenerationMatches(m,before,event,recipient),false);
c.subscriptions.set('sub',original);
assert.equal(publicationGenerationMatches(m,{...before,connection:2},event,recipient),false);
assert.equal(publicationGenerationMatches(m,{...before,subscription:'other'},event,recipient),false);
assert.equal(publicationGenerationMatches(m,null,event,recipient),false);
assert.equal(publicationGenerationMatches(m,before,{...event,created_at:102},recipient),false);
// Source-shape regression only: no nostr-tools import/evaluation or API invocation.
// Actual installed API availability requires a separately released guarded run.
const source=fs.readFileSync(new URL('./fixture.mjs',import.meta.url),'utf8');
assert.equal(source.includes('T.verifyEvent'),false);
assert.match(source,/async function main\(\)[\s\S]*const p=plan\(\)[\s\S]*const \{verifyEvent\}=await import\('nostr-tools\/pure'\)/);
assert.match(source,/const \{verifyEvent\}=await import\('nostr-tools\/pure'\);check\(\);need\(typeof verifyEvent==='function','PINNED_VERIFY_EVENT_API'\)/);
console.log(JSON.stringify({scope:'PURE_FILTER_GENERATION_AND_SOURCE_SHAPE_CONTROLS_ONLY',checks:27,installedCryptoAPIEvaluated:false,clientControlExecuted:false,E02Promotion:false}));
