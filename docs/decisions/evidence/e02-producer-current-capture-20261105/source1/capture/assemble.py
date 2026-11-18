"""Explicit post-capture assembler. Requires genuine external Root API bytes."""
import json,pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:
    import capture
    from contracts import *
    from explicit_inputs import metadata,read_expected
    from outputs import parse_outcome
finally:sys.path.pop(0)

def assemble(result_pin,origin_pin,ack_pin,ack_sha,output):
    capture.require_runtime_ready()
    deadline=time.monotonic_ns()+30000000000
    need(ack_pin['sha256']==ack_sha,'EXACT_ROOT_ACK');ack=metadata(ack_pin,deadline);docs,records=capture.load_bundle(ack,deadline);values,_=capture.validate_bundle(ack,docs,records,ack_sha)
    plan=docs['plan'];root=pathlib.Path(plan['outputRoot']);need(result_pin['path']==str(root/'result.json'),'EXACT_ONCE_CAPTURE_RESULT_PATH');result=metadata(result_pin,deadline)
    need(result['schema']=='e02-producer4-current-control-execution-v1' and result['rootAcknowledgement']==ack_pin and result['producerSource']==ack['producerSource'] and result['captureSource']==ack['captureSource'] and result['plan']==ack['plan'] and result['inputManifest']==ack['inputManifest'] and result['countsSeparate']==values,'EXACT_RESULT_CURRENT_JOINS')
    need(result['exitCode']==0 and result['firstFault'] is None and result['sourceUnchanged'] is True and result['remainingNotExecuted']==[] and len(result['scopes'])==len(result['outcomes'])==10 and 0<=result['elapsedNs']<=1200000000000,'ALL_TEN_NATURAL_CURRENT_SCOPES_ONLY')
    manifest_pin=capture.descriptor(root/'raw-artifact-manifest.json');manifest=metadata(manifest_pin,deadline);closed(manifest,'schema files originalToolOrigin outerApiMeaning');need(manifest['schema']=='e02-producer4-control-raw-artifact-manifest-v1' and manifest['originalToolOrigin'] is None,'ORIGINAL_CAPTURE_MANIFEST_NO_FAKE_PARENT_API')
    indexed={d['path']:d for d in manifest['files']};need(len(indexed)==len(manifest['files']),'UNIQUE_COMPLETE_RAW_MANIFEST');actual={str(p) for p in root.iterdir() if p.name!='raw-artifact-manifest.json'};need(actual==set(indexed),'NO_MISSING_EXTRA_LATE_RAW_PROOF')
    for d in manifest['files']:read_expected(d,deadline)
    before=metadata(result['overallBefore'],deadline);after=metadata(result['overallAfter'],deadline);need(before==after,'EXACT_OVERALL_BEFORE_AFTER')
    for i,(scope,row,outcome) in enumerate(zip(plan['scopes'],result['scopes'],result['outcomes']),1):
        need(row['scope']==scope['scope'] and row['argv']==scope['argv'] and row['elapsedNs']<=63000000000,'EXACT_ORDERED_CHILD_SCOPE')
        stdout=read_expected({k:v for k,v in row['stdout'].items() if k!='mode'},deadline,True)[1];stderr=read_expected({k:v for k,v in row['stderr'].items() if k!='mode'},deadline,True)[1]
        need(parse_outcome(scope,row,stdout,stderr)==outcome,'RAW_STREAM_OUTCOME_MATCH')
        for tail in ('before','after'):
            p=root/('%02d-%s.json'%(i,tail));need(str(p) in indexed and metadata(indexed[str(p)],deadline)==before,'ALL20_PER_SCOPE_EXPECTED_CUSTODY_SNAPSHOTS')
    origin=decode_tool_origin(read_expected(origin_pin,deadline,True)[1]);printed=validate_origin(origin,expected_request(plan,ack_sha,str(capture.HERE)),ack['operators'])
    summary=json.loads(printed.strip());need(summary==dict(result=result_pin,rawManifest=manifest_pin,exitCode=0),'GENUINE_TERMINAL_CAPTURE_SUMMARY')
    out=pathlib.Path(output);need(out.parent==root.parent and out.name=='assembled' and not out.exists() and not out.is_symlink(),'FRESH_FIXED_ASSEMBLY_ONLY');out.mkdir(mode=0o700)
    combined=list(manifest['files'])+[manifest_pin,origin_pin];capture.put(out,'raw-artifact-manifest.json',dict(schema='e02-producer4-control-combined-raw-manifest-v1',files=combined,runtimeManifest=manifest_pin,originalToolOrigin=origin_pin))
    subject=dict(schema='e02-producer4-current-control-data-subject-v1',authors=docs['captureSource']['authors'],operators=ack['operators'],state='WRITES_STOPPED_PENDING_INDEPENDENT_DATA_QA_SECURITY',producerSource=ack['producerSource'],producerSourceAcceptance=ack['producerSourceAcceptance'],captureSource=ack['captureSource'],captureSourceAcceptance=ack['captureSourceAcceptance'],admissionDataAcceptance=ack['admissionDataAcceptance'],plan=ack['plan'],inputManifest=ack['inputManifest'],rootAcknowledgement=ack_pin,execution=result_pin,originalToolOrigin=origin_pin,rawArtifactManifest=capture.descriptor(out/'raw-artifact-manifest.json'),countsSeparate=values,allExpectedInputsUnchanged=True,runtimeAuthorized=False,helperExecutions=0,ordinaryRowsQualified=0,canonicalE02='PARTIAL22_UNCHANGED')
    capture.put(out,'subject.json',subject);return capture.descriptor(out/'subject.json')

def main(args):
    capture.require_runtime_ready()
    need(len(args)==8 and args[0]=='--result' and args[2]=='--origin' and args[4]=='--ack' and args[6]=='--output','EXACT_ASSEMBLER_ARGUMENTS')
    result=capture.descriptor(pathlib.Path(args[1]));origin=capture.descriptor(pathlib.Path(args[3]));ack=capture.descriptor(pathlib.Path(args[5]));print(json.dumps(assemble(result,origin,ack,ack['sha256'],args[7])))
if __name__=='__main__':main(sys.argv[1:])
