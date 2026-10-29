"""Derive one exact foreground request from real current Root ACK. No launch."""
import json,pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
try:
    import capture
    from contracts import expected_request,need
    from explicit_inputs import metadata
finally:sys.path.pop(0)
def main(args):
    capture.require_runtime_ready()
    need(len(args)==2 and args[0]=='--root-ack','EXACT_ROOT_ACK_ARGUMENT');p=pathlib.Path(args[1]);ap=capture.descriptor(p);d=time.monotonic_ns()+30000000000;ack=metadata(ap,d);plan=metadata(ack['plan'],d);need(plan['readiness'] is True and ack['producerSource']==capture.CURRENT_PRODUCER_SOURCE and ack['producerSourceAcceptance']==capture.CURRENT_PRODUCER_ACCEPTANCE,'EXACT_CURRENT_ACCEPTED_PLAN')
    print(json.dumps(expected_request(plan,ap['sha256'],str(capture.HERE))))
if __name__=='__main__':main(sys.argv[1:])
