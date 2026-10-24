"""SOURCE ONLY:14 DATA admission relationships, no subprocess/strace/LOCAL.

All acceptance/report values supplied to the function under test are synthetic
in-memory inputs. No real approval, authority file or future hash is created.
Real descriptor verification is a separate unchanged Originals boundary.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,os,unittest
HERE=Path(__file__).resolve().parent
OUT=HERE/'admission-controls-actual-r1'
FIX=HERE.parent/'e06-strace-containment-controls-r2'
def load_module():
 s=importlib.util.spec_from_file_location('observer_admission_fixture',HERE/'observer.py')
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class SyntheticDocuments:
 def __init__(self):self.docs={};self.remembered=[]
 def add(self,path,obj):
  raw=json.dumps(obj,sort_keys=True).encode();d={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};self.docs[d['path']]=obj;return d
 def document(self,pin):return self.docs[pin['path']]
 def remember(self,pin):self.remembered.append(pin)
class AdmissionControls(unittest.TestCase):
 def setUp(self):
  self.m=load_module();self.o=SyntheticDocuments();self.cfg=json.loads((HERE/'observer-configuration-core.json').read_bytes())
  self.whole=self.m.descriptor(HERE/'subject.json');self.fixture_pin=self.m.descriptor(FIX/'subject.json')
  self.fixtures=json.loads((FIX/'subject.json').read_bytes());self.o.docs[self.fixture_pin['path']]=self.fixtures
  self.cases=['natural-zero','natural-refusal','deadline','interrupt','capture-fault','tracer-death','inner-parent-death'];self.rows=[];records=[]
  for case in self.cases:
   root=FIX/'actual-containment-r1'/case
   row={'case':case,'disposition':'QUALIFIED_FIXTURE_CONTAINMENT_ONLY','realStrace':True,'sameObserverCapture':True,
    'readyBarrierComplete':True,'safetyFallbackUsed':False,'allKnownPidsExitedBeforeFallback':True,
    'allOwnedChildrenReaped':True,'noPostReapSignal':True,'rawCapsRespected':True,'privacyQualified':True}
   raw={n:{'path':str(root/(n+'.bin')),'bytes':1,'sha256':'1'*64} for n in ['trace','stdout','stderr']}
   cap={'reaped':True,'eof':dict.fromkeys(raw,True),'raw':raw,'retainedBytes':dict.fromkeys(raw,1)}
   capture=self.o.add(root/'observer-capture.json',cap)
   record={**row,'firstError':None,'completeOwnedDescendantCensusEmpty':True,'faultSelfExpirySeconds':30,
    'guardTotalCeilingSeconds':11,'captureReceiptAtElapsedNs':5000000000,'absenceAtElapsedNs':5100000000,
    'observerCapture':capture,'rawDescriptors':raw}
   d=self.o.add(root/'guard-result.json',record);records.append(d);row['record']=d;self.rows.append(row)
  result={'schema':'e06-actual-strace-containment-subject-v1','sourceSubject':self.fixture_pin,
   'observerSourceSubject':self.whole,'tools':self.cfg['tools'],'hostContext':self.cfg['expectedHostContext'],
   'cases':self.rows,'files':records}
  self.result_pin=self.o.add('/synthetic-only/result-subject.json',result)
  modeled={'schema':'e06-modeled-guard-controls-actual-subject-v1','sourceSubject':self.fixture_pin,
   'observerWholeSourceSubject':self.whole,'actualControls':11,'passed':11,'failed':0,'errors':0,'skipped':0,
   'actualAdmissionControls':14,'admissionPassed':14,'admissionFailed':0,'admissionErrors':0,'admissionSkipped':0,'files':[]}
  model_pin=self.o.add('/synthetic-only/modeled-result-subject.json',modeled)
  def reviews(subject,decision):return [{'role':r,'session':'/synthetic-independent/'+r,'decision':decision,'subject':subject} for r in ['qa','security']]
  pure={'schema':'e06-strace-guard-pure-acceptance-v1','decision':'ACCEPT_GUARD11_ADMISSION14_MODELED_CONTROLS_ONLY',
   'sourceSubject':self.fixture_pin,'observerWholeSourceSubject':self.whole,'actualControls':11,'actualAdmissionControls':14,
   'controlSubject':model_pin,'operator':'/synthetic-operator','authors':['/synthetic-author'],
   'reviews':reviews(model_pin,'ACCEPT_GUARD11_ADMISSION14_MODELED_CONTROLS_ONLY')}
  pure_pin=self.o.add('/synthetic-only/modeled-acceptance.json',pure)
  self.acceptance={'schema':'e06-strace-containment-acceptance-v1','decision':'ACCEPT_ACTUAL_PINNED_STRACE_CONTAINMENT_ONLY',
   'sourceSubject':self.whole,'testedWholeSourceSubject':self.whole,'containmentSourceSubject':self.fixture_pin,
   'guardRegressionAcceptance':pure_pin,'controlSubject':self.result_pin,'tools':self.cfg['tools'],
   'hostContext':self.cfg['expectedHostContext'],'fixtureCases':self.cases,'captureFunctionAstSha256':self.fixtures['captureFunctionAstSha256'],
   'results':self.rows,'operator':'/synthetic-operator','authors':['/synthetic-author'],
   'reviews':reviews(self.result_pin,'ACCEPT_ACTUAL_PINNED_STRACE_CONTAINMENT_ONLY')}
  self.accept_pin=self.o.add('/synthetic-only/containment-acceptance.json',self.acceptance)
 def check(self,refused=True):
  if refused:
   with self.assertRaises((self.m.Refusal,KeyError)):self.m.require_containment_acceptance(self.o,self.cfg,self.whole,self.accept_pin)
  else:self.m.require_containment_acceptance(self.o,self.cfg,self.whole,self.accept_pin)
  raw=json.dumps({'test':self.id(),'syntheticInMemoryOnly':True,'refused':refused,'realAuthorityCreated':False}).encode()
  p=OUT/(self._testMethodName+'.json');fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 def test_01_missing_mandatory_acceptance(self):del self.acceptance['guardRegressionAcceptance'];self.check()
 def test_02_stale_whole_source(self):self.acceptance['testedWholeSourceSubject']={**self.whole,'sha256':'0'*64};self.check()
 def test_03_wrong_strace_tool(self):self.acceptance['tools']=copy.deepcopy(self.cfg['tools']);self.acceptance['tools']['strace']['sha256']='0'*64;self.check()
 def test_04_wrong_HOST_context(self):self.acceptance['hostContext']={**self.cfg['expectedHostContext'],'uidMap':'wrong'};self.check()
 def test_05_missing_independent_review(self):self.acceptance['reviews']=self.acceptance['reviews'][:1];self.check()
 def test_06_author_cannot_review(self):self.acceptance['reviews'][0]['session']=self.m.AUTHORS[0];self.check()
 def test_07_any_safety_fallback_refused(self):self.rows[0]['safetyFallbackUsed']=True;self.check()
 def test_08_incomplete_seven_cases_refused(self):self.rows.pop();self.check()
 def test_09_wrong_observer_source_refused(self):self.fixtures['observer']={**self.fixtures['observer'],'sha256':'0'*64};self.check()
 def test_10_wrong_helper_closure_refused(self):self.fixtures['observerHelper']={**self.fixtures['observerHelper'],'sha256':'0'*64};self.check()
 def test_11_late_capture_refused(self):self.o.docs[self.rows[0]['record']['path']]['captureReceiptAtElapsedNs']=8000000000;self.check()
 def test_12_late_absence_refused(self):self.o.docs[self.rows[0]['record']['path']]['absenceAtElapsedNs']=8000000000;self.check()
 def test_13_actual_raw_size_mismatch_refused(self):self.o.docs[self.o.docs[self.rows[0]['record']['path']]['observerCapture']['path']]['retainedBytes']['trace']=2;self.check()
 def test_14_complete_synthetic_relationships_only(self):self.check(False)
if __name__=='__main__':OUT.mkdir(mode=0o700,exist_ok=False);unittest.main(verbosity=2)
