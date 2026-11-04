"""Artificial CPU authorization files only; real authorize/exact/rebind functions, no mocks."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,unittest

N=Path(__file__).resolve().parent;B=N.parent.parent
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
F=N/'cpu_contract_v1';META=F/'metadata';CASES=F/'fixtures'
PROTO=None;CONTRACT=None;ENTRY=None
def sha(b):return hashlib.sha256(b).hexdigest()
def binding(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
def write(p,obj):
 with p.open('x',encoding='ascii') as f:json.dump(obj,f,ensure_ascii=True,indent=2)
 return binding(p)
def copy_exact(src,name,expected):
 raw=src.read_bytes();assert len(raw)==expected['bytes'] and sha(raw)==expected['sha256']
 p=META/name
 with p.open('xb') as f:f.write(raw)
 return binding(p)

class FullAuthorize(unittest.TestCase):
 def build(self,qchange=None,achange=None,rchange=None,static_change=False,gpu_change=False):
  case=CASES/self._testMethodName.split('_')[1];case.mkdir()
  q=copy.deepcopy(PROTO)
  if static_change:
   cfg=json.loads(Path(q['static_config']['path']).read_bytes());cfg['training']['lr']=.0002
   q['static_config']=write(case/'static.json',cfg)
  if gpu_change:
   cfg=json.loads(Path(q['GPU_audit']['path']).read_bytes());cfg['status']='FAKE_BOOLEAN_READINESS'
   q['GPU_audit']=write(case/'gpu.json',cfg)
  if qchange:qchange(q)
  qr=write(case/'request_ARTIFICIAL.json',q)
  a=dict(schema='bcsp-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,
         user_authorization_text='ARTIFICIAL_CPU_CONTRACT_FIXTURE_ONLY_NOT_REAL_TRAINING_AUTHORIZATION')
  if achange:achange(a)
  ar=write(case/'authorization_ARTIFICIAL.json',a)
  r=dict(schema='bcsp-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
  if rchange:rchange(r)
  rr=write(case/'runtime_ARTIFICIAL.json',r)
  return q,(qr,ar,rr)

 def rejected(self,text,**kw):
  q,args=self.build(**kw)
  with self.assertRaisesRegex(ValueError,text):ENTRY.authorize(*args)

 def test_01_C16_full_authorize_exact_static_gpu_rebind_pass(self):
  q,args=self.build();got,cfg=ENTRY.authorize(*args)
  self.assertEqual(got,q);self.assertEqual(cfg['counts']['updates'],3900)
  self.assertIs(ENTRY.authorize,CONTRACT.authorize)

 def test_02_C8_rejected_by_dedicated_16k_gate(self):
  self.rejected('Fold C 16k arm only',qchange=lambda q:q.update(n_input=8192))

 def test_03_D16_rejected_by_dedicated_fold_gate(self):
  self.rejected('Fold C 16k arm only',qchange=lambda q:q.update(fold='D'))

 def test_04_unsupported_input_rejected(self):
  self.rejected('fold/input',qchange=lambda q:q.update(n_input=16383))

 def test_05_explicit_authorization_required(self):
  self.rejected('separate authorization',achange=lambda a:a.update(explicit_user_authorization=False))

 def test_06_authorization_request_hash_must_match(self):
  self.rejected('separate authorization',achange=lambda a:a.update(request_sha256='0'*64))

 def test_07_runtime_authorization_hash_must_match(self):
  self.rejected('one-way runtime binding',rchange=lambda r:r.update(authorization_sha256='0'*64))

 def test_08_reverse_runtime_binding_rejected(self):
  self.rejected('separate authorization',achange=lambda a:a.update(runtime_sha256='0'*64))

 def test_09_static_training_drift_rejected(self):
  self.rejected('training scientific contract',static_change=True)

 def test_10_GPU_identity_drift_rejected(self):
  self.rejected('request rebound identity',qchange=lambda q:q['identity'].update(gpu_uuid='WRONG'))

 def test_11_runtime_implementation_hash_drift_rejected(self):
  self.rejected('unchanged scientific',qchange=lambda q:q['implementation']['runtime'].update(sha256='0'*64))

 def test_12_actual_GPU_evidence_required(self):
  self.rejected('actual frozen GPU evidence',gpu_change=True)

 def test_13_authorize_then_actual_qualified_reader_pass(self):
  q,args=self.build();ENTRY.authorize(*args)
  receipt=CONTRACT.json_bound(q['QC']['qualified_receipt'])
  selected,fold=CONTRACT.verify_qualified_receipt(receipt,q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',16384)
  self.assertEqual(len(selected),315);self.assertEqual(len(fold['train_sources']),63)
  self.assertTrue(all(r['n_input']==16384 and r['n_target']==8192 for r in selected))

 def test_14_authorize_then_wrong_qualified_arm_rejected(self):
  q,args=self.build();ENTRY.authorize(*args)
  receipt=CONTRACT.json_bound(q['QC']['qualified_receipt']);receipt['n_input']=8192
  with self.assertRaisesRegex(ValueError,'qualified receipt drift'):
   CONTRACT.verify_qualified_receipt(receipt,q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',16384)

def main():
 global PROTO,CONTRACT,ENTRY
 F.mkdir(exist_ok=False);META.mkdir();CASES.mkdir()
 entry=N/'bcsp_training_entry_foldC_16384_v6.py'
 spec=importlib.util.spec_from_file_location('dedicated16k_entry_CPU_import',entry)
 ENTRY=importlib.util.module_from_spec(spec);spec.loader.exec_module(ENTRY)
 CONTRACT=sys.modules['bcsp_training_contract_v1']
 PROTO=json.loads((N.parent/'training_entry_request_v1.json').read_bytes())
 original=copy.deepcopy(PROTO)
 for key,name in [('entry','bcsp_training_entry_foldC_16384_v6.py'),('contract','bcsp_training_contract_foldC_16384_v4.py')]:
  value=binding(N/name);value['path']=original['implementation'][key]['path'].rsplit('/',1)[0]+'/'+name
  PROTO['implementation'][key]=value
 paths=[('static_config',B/'first_run_freeze_foldC_8192_v1/static_training_config_v1.json','static_training_config_v1.json'),
        ('GPU_audit',B/'gpu_preflight_plotting_lazy_v3/authorized_execution_v3/post_preflight_freeze_audit_report_v1.json','GPU_audit.json'),
        ('preflight_scope',B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json','scope.json'),
        ('resource_rebind',P/'resource_rebind_01dt08_v1.json','resource_rebind_01dt08_v1.json')]
 for key,src,name in paths:PROTO[key]=copy_exact(src,name,original[key])
 receipt=json.loads((P/'resource_rebind_01dt08_v1.json').read_bytes())
 report=receipt['new_readonly_report'];copy_exact(P/report['path'],report['path'],report)
 PROTO['QC']['verification']=copy_exact(B/'real_data_qc_verification_v1.json','QC.json',original['QC']['verification'])
 PROTO['QC']['fold_binding']=copy_exact(B/'consolidated_binding_v1/fold_binding.json','fold.json',original['QC']['fold_binding'])
 for arm in ['8192','16384']:
  PROTO['QC']['manifests'][arm]=copy_exact(B/('real_data_qc_v1/manifest_'+arm+'.jsonl'),'manifest_'+arm+'.jsonl',original['QC']['manifests'][arm])
 receipt,_,_=CONTRACT.bind_metadata(PROTO['QC']['verification'],PROTO['QC']['manifests'],PROTO['QC']['fold_binding'],'C',16384)
 PROTO['QC']['qualified_receipt']=write(META/'qualified_ARTIFICIAL.json',receipt)
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(FullAuthorize);assert suite.countTestCases()==14
 result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
 report=dict(status='PASS_14_FULL_AUTHORIZE_CPU_CONTRACTS' if result.wasSuccessful() and result.testsRun==14 else 'FAILED_STOP_NO_RETRY',
 testsRun=result.testsRun,failures=len(result.failures),errors=len(result.errors),authorize_function_executed_without_mocking=True,
 exact_json_static_rebind_functions_not_mocked=True,entry_sibling_hash_bootstrap_executed=True,real_GPU_audit_and_rebind_bytes_used=True,
 artificial_authorization_files_only=True,production_authorization_created=False,server_operations=0,model_imports=0,CUDA_calls=0,real_point_payload_reads=0)
 with (F/'results_v1.json').open('x') as f:json.dump(report,f,indent=2)
 return 0 if report['status'].startswith('PASS_14') else 1

if __name__=='__main__':raise SystemExit(main())
