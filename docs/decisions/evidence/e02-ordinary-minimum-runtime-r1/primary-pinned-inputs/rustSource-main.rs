//! Disposable experiment adapter. Not an SDK. No cryptographic algorithms implemented here.
use std::io::{self, BufRead, Write};
use std::fmt;
use base64::{Engine, engine::general_purpose::STANDARD};
use nostr::prelude::*;
use nostr::nips::{nip44::v2, nip59::GiftWrapBuilder};
use serde::de::{self, Visitor, MapAccess, SeqAccess};
use serde::{Deserialize, Deserializer};
use serde_json::{Value, json, Map};

// Independent duplicate-key rejecting parser; serde_json normally retains the last key.
struct Unique(Value);
impl<'de> Deserialize<'de> for Unique {
 fn deserialize<D: Deserializer<'de>>(d:D)->Result<Self,D::Error>{
  struct V;
  impl<'de> Visitor<'de> for V {
   type Value=Unique;
   fn expecting(&self,f:&mut fmt::Formatter)->fmt::Result{write!(f,"unambiguous JSON")}
   fn visit_bool<E:de::Error>(self,v:bool)->Result<Unique,E>{Ok(Unique(json!(v)))}
   fn visit_i64<E:de::Error>(self,v:i64)->Result<Unique,E>{Ok(Unique(json!(v)))}
   fn visit_u64<E:de::Error>(self,v:u64)->Result<Unique,E>{Ok(Unique(json!(v)))}
   fn visit_f64<E:de::Error>(self,_v:f64)->Result<Unique,E>{Err(de::Error::custom("integer tokens required"))}
   fn visit_str<E:de::Error>(self,v:&str)->Result<Unique,E>{Ok(Unique(json!(v)))}
   fn visit_unit<E:de::Error>(self)->Result<Unique,E>{Ok(Unique(Value::Null))}
   fn visit_seq<A:SeqAccess<'de>>(self,mut a:A)->Result<Unique,A::Error>{let mut v=vec![];while let Some(Unique(x))=a.next_element()?{v.push(x)}Ok(Unique(Value::Array(v)))}
   fn visit_map<A:MapAccess<'de>>(self,mut a:A)->Result<Unique,A::Error>{let mut m=Map::new();while let Some(k)=a.next_key::<String>()?{if m.contains_key(&k){return Err(de::Error::custom("duplicate key"))}let Unique(v)=a.next_value()?;m.insert(k,v);}Ok(Unique(Value::Object(m)))}
  }
  d.deserialize_any(V)
 }
}
fn depth(v:&Value)->usize{match v{Value::Array(a)=>1+a.iter().map(depth).max().unwrap_or(0),Value::Object(m)=>1+m.values().map(depth).max().unwrap_or(0),_=>0}}
fn parse(s:&str)->Result<Value,String>{if s.len()>2_000_000{return Err("resource".into())}let Unique(v)=serde_json::from_str(s).map_err(|_|"json")?;if depth(&v)>32{return Err("json".into())}Ok(v)}
fn st<'a>(v:&'a Value,k:&str)->Result<&'a str,String>{v[k].as_str().ok_or("schema".into())}
fn hexlen(s:&str,n:usize)->bool{s.len()==n&&s.bytes().all(|b|b.is_ascii_digit()||(b'a'..=b'f').contains(&b))}
fn guard(c:bool,e:&str)->Result<(),String>{if c{Ok(())}else{Err(e.into())}}
fn shape(v:&Value,signed:bool)->Result<(),String>{
 let keys=if signed{vec!["id","pubkey","created_at","kind","tags","content","sig"]}else{vec!["id","pubkey","created_at","kind","tags","content"]};
 let m=v.as_object().ok_or("structure")?;
 guard(m.len()==keys.len()&&keys.iter().all(|k|m.contains_key(*k)),"structure")?;
 guard(hexlen(st(v,"id")?,64)&&hexlen(st(v,"pubkey")?,64),"structure")?;
 if signed{guard(hexlen(st(v,"sig")?,128),"structure")?;}
 guard(v["kind"].as_u64().is_some_and(|x|x<=65535)&&v["created_at"].as_u64().is_some_and(|x|x<=9_007_199_254_740_991),"structure")?;
 st(v,"content")?;
 let tags=v["tags"].as_array().ok_or("structure")?;
 guard(tags.len()<=64&&tags.iter().all(|t|t.as_array().is_some_and(|a|a.len()<=8&&a.iter().all(|x|x.is_string()))),"structure")
}
fn peers(v:&Value)->Vec<String>{v["tags"].as_array().unwrap().iter().filter(|t|t[0]=="p").filter_map(|t|t[1].as_str().map(String::from)).collect()}
fn schema(e:&Value,r:&Value)->Result<(),String>{
 guard(e["version"]==1,"version")?;
 guard(e["required"]==json!([]),"extension")?;
 guard(e["type"]=="document"&&e["context"]=="synthetic","schema")?;
 guard(hexlen(st(e,"id")?,64)&&e["from"]==r["pubkey"]&&Some(st(e,"to")?.to_owned())==peers(r).first().cloned(),"binding")?;
 let allowed=["protocol","version","type","id","from","to","context","required","document","files","note"];
 guard(e.as_object().is_some_and(|m|m.keys().all(|k|allowed.contains(&k.as_str()))),"schema")?;
 let d=&e["document"];
 guard(d.as_object().is_some_and(|m|m.len()==5)&&hexlen(st(d,"id")?,64)&&hexlen(st(d,"sha256")?,64)&&d["bytes"].as_u64().is_some_and(|x|x<=1_048_576)&&d["revision"].as_u64().is_some_and(|x|x>0&&x<=9_007_199_254_740_991)&&!st(d,"media")?.is_empty(),"schema")?;
 if let Some(f)=e.get("files"){
  let a=f.as_array().ok_or("schema")?;guard(a.len()<=16,"schema")?;
  for x in a{let size=x["size"].as_str().ok_or("schema")?;let n=size.parse::<u64>().map_err(|_|"schema")?;guard(x.as_object().is_some_and(|m|m.len()==3)&&hexlen(st(x,"x")?,64)&&hexlen(st(x,"ox")?,64)&&n>=16&&n<=1_048_592&&n.to_string()==size,"schema")?;}
 }
 if let Some(n)=e.get("note"){guard(n.is_string(),"schema")?;}
 Ok(())
}
fn validate(q:&Value,trace:&mut [usize;2])->Result<Value,String>{
 let wire=st(q,"wire")?;let cap=q["cap"].as_u64().unwrap_or(16384) as usize;
 guard(wire.len()+10<=cap,"resource")?;
 let w=parse(wire)?;shape(&w,true)?;guard(w["kind"]==1059,"outer-kind")?;
 let keys=Keys::parse(st(q,"secret")?).map_err(|_|"key")?;let local=keys.public_key().to_hex();
 guard(w["tags"]==json!([["p",local]]),"recipient")?;
 let event=Event::from_json(w.to_string()).map_err(|_|"structure")?;event.verify().map_err(|_|"outer-auth")?;
 trace[0]+=1;
 let raw=keys.nip44_decrypt(&event.pubkey,&event.content).map_err(|_|"outer-crypto")?;
 let s=parse(&raw)?;shape(&s,true)?;guard(s["kind"]==13,"seal-kind")?;guard(s["tags"]==json!([]),"seal-tags")?;
 let seal=Event::from_json(s.to_string()).map_err(|_|"structure")?;seal.verify().map_err(|_|"seal-auth")?;
 trace[1]+=1;
 let raw=keys.nip44_decrypt(&seal.pubkey,&seal.content).map_err(|_|"seal-crypto")?;
 let r=parse(&raw)?;shape(&r,false)?;guard(r["kind"]==14||r["kind"]==15,"rumor-kind")?;
 let rumor=UnsignedEvent::from_json(r.to_string()).map_err(|_|"structure")?;rumor.verify_id().map_err(|_|"rumor-id")?;
 guard(r["pubkey"]==s["pubkey"],"author")?;let p=peers(&r);guard(p.len()==1&&hexlen(&p[0],64),"recipient")?;
 let archive=q["role"]=="archive";
 guard(if archive{r["pubkey"]==local}else{p[0]==local},"recipient")?;
 if let Some(peer)=q["expectedSender"].as_str(){guard(r["pubkey"]==peer,"authorization")?;}
 if r["kind"]==15{return Ok(json!({"rumor":r,"dispatch":false,"role":if archive{"archive"}else{"file"}}))}
 let content=st(&r,"content")?;
 let e=if content.starts_with('{'){parse(content)?}else{Value::Null};
 if e["protocol"]!="NBDP/experiment"{return Ok(json!({"rumor":r,"dispatch":false,"role":"chat"}))}
 schema(&e,&r)?;
 Ok(json!({"rumor":r,"envelope":e,"dispatch":!archive,"role":if archive{"archive"}else{"incoming"}}))
}
fn run(q:Value)->Result<Value,String>{
 match st(&q,"op")?{
 "source"=>Ok(json!(include_str!("main.rs"))),
 "pubkey"=>Ok(json!(Keys::parse(st(&q,"secret")?).map_err(|e|e.to_string())?.public_key().to_hex())),
 "wrap"=>{let keys=Keys::parse(st(&q,"secret")?).map_err(|e|e.to_string())?;let p=PublicKey::from_hex(st(&q,"to")?).map_err(|e|e.to_string())?;let r=UnsignedEvent::from_json(q["rumor"].to_string()).map_err(|e|e.to_string())?;let w=GiftWrapBuilder::new(p,r).finalize(&keys).map_err(|e|e.to_string())?;Ok(serde_json::from_str(&w.as_json()).unwrap())},
 "encrypt"=>{let k=Keys::parse(st(&q,"secret")?).map_err(|e|e.to_string())?;let p=PublicKey::from_hex(st(&q,"to")?).map_err(|e|e.to_string())?;Ok(json!(k.nip44_encrypt(&p,st(&q,"plaintext")?).map_err(|e|e.to_string())?))},
 "decrypt"=>{let k=Keys::parse(st(&q,"secret")?).map_err(|e|e.to_string())?;let p=PublicKey::from_hex(st(&q,"from")?).map_err(|e|e.to_string())?;Ok(json!(k.nip44_decrypt(&p,st(&q,"payload")?).map_err(|e|e.to_string())?))},
 "conversation"=>{let k=Keys::parse(st(&q,"secret")?).map_err(|e|e.to_string())?;let p=PublicKey::from_hex(st(&q,"to")?).map_err(|e|e.to_string())?;Ok(json!(hex::encode(v2::ConversationKey::derive(k.secret_key(),&p).map_err(|e|e.to_string())?.as_bytes())))},
 "vector-encrypt"=>{let c=v2::ConversationKey::from_slice(&hex::decode(st(&q,"key")?).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;let n:[u8;32]=hex::decode(st(&q,"nonce")?).map_err(|e|e.to_string())?.try_into().map_err(|_|"nonce")?;Ok(json!(STANDARD.encode(v2::encrypt_to_bytes_with_nonce(&c,st(&q,"plaintext")?.as_bytes(),n).map_err(|e|e.to_string())?)))},
 "vector-decrypt"=>{let c=v2::ConversationKey::from_slice(&hex::decode(st(&q,"key")?).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;let bytes=STANDARD.decode(st(&q,"payload")?).map_err(|e|e.to_string())?;guard(bytes.first()==Some(&2),"version")?;Ok(json!(String::from_utf8(v2::decrypt_to_bytes(&c,&bytes).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?))},
 "validate"=>{let mut trace=[0,0];let result=validate(&q,&mut trace);Ok(match result{Ok(v)=>json!({"ok":true,"value":v,"decrypts":trace}),Err(e)=>json!({"ok":false,"error":e,"decrypts":trace})})},
 "discover"=>discover(&q),
 "correlate"=>correlate(&q),
 "file-rumor"=>{
  let from=st(&q,"from")?;let to=st(&q,"to")?;let f=&q["file"];
  let mut r=json!({"pubkey":from,"created_at":q["timestamp"],"kind":15,"tags":[["p",to],["e",q["parent"],"","reply"],["file-type",q["media"]],["encryption-algorithm","aes-gcm"],["decryption-key",f["key"]],["decryption-nonce",f["nonce"]],["x",f["ciphertext_sha256"]],["ox",f["plaintext_sha256"]],["size",f["blob_bytes"].as_u64().unwrap().to_string()]],"content":q["url"]});
  let mut u=UnsignedEvent::from_json(r.to_string()).map_err(|e|e.to_string())?;u.ensure_id();r["id"]=json!(u.id.unwrap().to_hex());Ok(r)
 },
 _=>Err("unsupported operation".into())
 }
}
fn discover(q:&Value)->Result<Value,String>{
 let peer=st(q,"peer")?;let now=q["now"].as_u64().ok_or("clock")?;let seen=q["seen"].as_u64().unwrap_or(0);
 let mut valid=vec![];
 for v in q["candidates"].as_array().ok_or("candidates")?{
  if shape(v,true).is_err()||v["kind"]!=10050||v["pubkey"]!=peer{continue}
  if Event::from_json(v.to_string()).and_then(|e|e.verify()).is_ok(){valid.push(v)}
 }
 if valid.is_empty(){return Ok(json!({"state":"inbox-unavailable","destinations":[]}))}
 valid.sort_by_key(|v|v["created_at"].as_u64().unwrap());let best=valid.last().unwrap();let timestamp=best["created_at"].as_u64().unwrap();
 let same:Vec<_>=valid.iter().filter(|v|v["created_at"].as_u64()==Some(timestamp)).collect();
 if same.iter().any(|v|v["id"]!=best["id"]){return Ok(json!({"state":"discovery-conflict","destinations":[]}))}
 if timestamp<seen||timestamp>now+300||now.saturating_sub(timestamp)>864000{return Ok(json!({"state":"stale-or-rollback","destinations":[]}))}
 let tags=best["tags"].as_array().unwrap();let mut urls=vec![];
 for tag in tags{if tag[0]!="relay"||tag.as_array().unwrap().len()!=2{return Ok(json!({"state":"malformed-inbox","destinations":[]}))}let u=tag[1].as_str().unwrap();
  let parsed=nostr::types::Url::parse(u);match parsed{Ok(p) if p.scheme()=="ws"&&matches!(p.host_str(),Some("127.0.0.1")|Some("localhost"))&&p.username().is_empty()&&p.password().is_none()=>urls.push(u.to_owned()),_=>return Ok(json!({"state":"unsafe-lab-route","destinations":[]}))}
 }
 urls.sort();urls.dedup();if urls.is_empty(){return Ok(json!({"state":"inbox-empty","destinations":[]}))}
 Ok(json!({"state":"ready","destinations":urls,"list_id":best["id"]}))
}
fn correlate(q:&Value)->Result<Value,String>{
 let events=q["events"].as_array().ok_or("events")?;
 let envs:Vec<_>=events.iter().filter(|e|e["kind"]==14).collect();
 if envs.is_empty(){return Ok(json!({"state":"PENDING","operations":0,"effects":0}))}
 let base=envs[0];let e=parse(st(base,"content")?)?;let d=&e["document"];
 if envs.iter().any(|r|r["id"]!=base["id"]){return Ok(json!({"state":"CONFLICT","operations":0,"effects":0}))}
 let file= &e["files"][0];let mut matching=false;
 for r in events.iter().filter(|r|r["kind"]==15){
  let get=|name:&str|->Option<&Value>{let tags=r["tags"].as_array()?;let values:Vec<_>=tags.iter().filter(|t|t[0]==name).collect();if values.len()!=1{return None}values[0].get(1)};
  if r["pubkey"]!=base["pubkey"]||peers(r)!=peers(base){return Ok(json!({"state":"CONFLICT","operations":0,"effects":0}))}
  if get("encryption-algorithm")!=Some(&json!("aes-gcm")){return Ok(json!({"state":"UNSUPPORTED","operations":0,"effects":0}))}
  if get("e")!=base.get("id"){continue}
  let key=get("decryption-key").and_then(Value::as_str).unwrap_or("");let nonce=get("decryption-nonce").and_then(Value::as_str).unwrap_or("");
  if !hexlen(key,64)||!hexlen(nonce,24)||get("x")!=file.get("x")||get("ox")!=d.get("sha256")||get("file-type")!=d.get("media")||get("size").and_then(Value::as_str)!=file["size"].as_str(){return Ok(json!({"state":"CONFLICT","operations":0,"effects":0}))}
  matching=true;
 }
 Ok(json!({"state":if matching{"READY"}else{"INCOMPLETE"},"operations":if matching{1}else{0},"effects":0}))
}
fn main(){for line in io::stdin().lock().lines(){let line=line.unwrap();let result=if line.len()>5_000_000{Err("request cap".into())}else{serde_json::from_str(&line).map_err(|e|e.to_string()).and_then(run)};let output=match result{Ok(v)=>json!({"ok":true,"value":v}),Err(e)=>json!({"ok":false,"error":e})};println!("{}",output);io::stdout().flush().unwrap();}}
