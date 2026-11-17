"""Single artificial CPU child verifies actual training-chain sources and failure exit."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys,traceback
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'CPU_batch_v2'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def main():
 O.mkdir();scope=json.loads((V/'CPU_scope_v2.json').read_text());checks=[]
 def check(n,v):assert v,scope['checks'][n-1];assert len(checks)==n-1;checks.append(scope['checks'][n-1])
 try:
  entry=V/'bcsp_spcg_training_entry_v2.py';e=load('train_v2_static_cpu',entry);old=load('train_old_static_cpu',S/'bcsp_spcg_training_entry_v1.py')
  def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
  a=funcs(S/'bcsp_spcg_training_entry_v1.py');b=funcs(entry);check(1,{n for n in a if a[n]!=b[n]}=={'main'} and set(b)-set(a)=={'load_training_chain','fail_with_traceback'})
  previous=json.loads((S/'CPU_batch_v1/result.json').read_text());check(2,e.COUNTS==old.COUNTS and e.RESOURCES==old.RESOURCES and rec(S/'bcsp_spcg_training_bridge_v1.py')==previous['bridge'])
  B=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload';P=W/'outputs/spcg_implementation_20261116_v1';snapshot=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot'
  paths=dict(entry=entry,bridge=S/'bcsp_spcg_training_bridge_v1.py',head=P/'bcsp_spcg_head_v1.py',observe=P/'bcsp_spcg_runtime_v1.py',training_runtime=B/'bcsp_p1_training_runtime_v1.py',contract=B/'bcsp_training_contract_01dt08_v3.py',adapter=snapshot/'tools/bcsp_adapter.py',native=W/'outputs/cranial_bcsp_fullmamba_20261110/Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py',helper=W/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py')
  owned=O/'owned';owned.mkdir();neighbor=O/'neighbor.py';neighbor.write_text('UNBOUND=1\n');config=dict(records={n:rec(p) for n,p in paths.items()},owned=str(owned.absolute()),neighbor=str(neighbor.absolute()))
  child=r'''
from pathlib import Path
import json,sys,os,types,hashlib,traceback,textwrap,linecache
import torch
c=json.loads(Path(sys.argv[1]).read_text());R=c['records']
def load(n,r):
 import importlib.util
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
e=load('actual_train_entry_v2',R['entry']);parent=load('actual_native',R['native']);helper=load('actual_helper',R['helper'])
if sys.platform=='win32':
 class BinaryReadOS:
  def __getattr__(self,n):return getattr(os,n)
  def open(self,path,flags,*a,**kw):
   assert not flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
   return os.open(path,flags|os.O_BINARY,*a,**kw)
 parent.os=BinaryReadOS()
g=parent.ExactSourceReads(dict(encoder=R['entry'],factory=R['bridge'],f0_decoder=R['head'],f0_factory=R['observe']))
for r in [*R.values(),c['self_source']]:
 p=parent.exact(r)
 if p not in g.records:g.records[p]=r;g.fds[p]=parent.os.open(p,parent.os.O_RDONLY|getattr(parent.os,'O_NOFOLLOW',0));g.verify(p)
tools=types.ModuleType('tools');tools.__path__=[];sys.modules['tools']=tools
# Dependencies are real frozen source, not fake observation/runtime objects.
e.source('bcsp_training_contract_v1',R['contract']);e.source('tools.bcsp_adapter',R['adapter'])
class UTC:
 def allow(self,*a):return False
out=Path(c['owned']);policy=parent.make_policy(helper,[],out,[],[],[],UTC(),g);sys.addaudithook(policy.audit)
q=dict(implementation={k:R[k] for k in ['bridge','head','observe','training_runtime']})
try:
 bridge,observe,runtime=e.load_training_chain(q)
 assert sys.modules['bcsp_spcg_head_v1'].__file__==R['head']['path'] and observe.need is sys.modules['bcsp_spcg_head_v1'].need
 assert runtime.BCSPDataset.__module__=='spcg_frozen_training_runtime' and callable(runtime.train_lifecycle)
 Q=torch.randn(1,256,3,requires_grad=True);Q.square().mean().backward();assert observe.Q_gradient_record(Q)['L2']>0 and 'rms_radius' in observe.geometry(Q)
 def reject(fn):
  try:fn()
  except (RuntimeError,ValueError):return True
  return False
 assert reject(lambda:Path(R['head']['path']).open('wb'))
 assert reject(lambda:Path(c['neighbor']).read_bytes())
 assert reject(lambda:e.exact(dict(R['head'],sha256='0'*64)))
 e.emit(out/'chain_checks.json',dict(real_chain=True,observation_tensors=True,source_write_denied=True,neighbor_read_denied=True,bad_hash_denied=True,load_order=['bridge','head','observe','training_runtime']))
 try:raise RuntimeError('ARTIFICIAL_TRAINING_START_FAILURE')
 except RuntimeError as ex:e.fail_with_traceback(out,ex)
finally:
 e.emit(out/'cleanup_record.json',dict(before_close=True,guard_descriptors_open=bool(g.fds)))
 g.close()
'''
  cp=O/'child_config.json';ch=O/'policy_child.py';ch.write_text(child,encoding='utf-8');config['self_source']=rec(ch);cp.write_text(json.dumps(config),encoding='utf-8')
  result=subprocess.run([sys.executable,'-I','-B',str(ch),str(cp)],capture_output=True,timeout=45);(O/'child_stdout.bin').write_bytes(result.stdout);(O/'child_stderr.bin').write_bytes(result.stderr)
  cc=json.loads((owned/'chain_checks.json').read_text());failure=json.loads((owned/'training_error_traceback.json').read_text());clean=json.loads((owned/'cleanup_record.json').read_text());stderr=result.stderr.decode(errors='replace')
  check(3,cc['real_chain'] and cc['load_order']==['bridge','head','observe','training_runtime']);check(4,cc['observation_tensors']);check(5,cc['source_write_denied']);check(6,cc['neighbor_read_denied']);check(7,cc['bad_hash_denied']);check(8,failure['phase']=='GUARD_ACTIVE_BEFORE_CLEANUP' and 'ARTIFICIAL_TRAINING_START_FAILURE' in failure['traceback']);check(9,result.returncode==1 and 'KeyError' not in stderr and 'sys.excepthook' not in stderr and not stderr.strip());check(10,clean['before_close'] and clean['guard_descriptors_open'])
  q=json.loads((S/'pending_transport_v1/payload/SPCG_G0_C_training_execution_request_v1.json').read_text());check(11,q['arm']=='G0' and q['fold']=='C' and a['validate']==b['validate'])
  check(12,all(rec(paths[k])==v for k,v in config['records'].items()))
  (O/'result.json').write_text(json.dumps(dict(status='SPCG_G0C_STARTUP_CHAIN_CPU_PASS',count=len(checks),checks=checks,entry=rec(entry),test=rec(Path(__file__)),dependencies=config['records'],child_checks=cc,failure_exit_code=result.returncode,cleanup=clean,scope=rec(V/'CPU_scope_v2.json'),server_operations=0,model_forward=0,CUDA=0,limitations=['Actual head/observe/bridge/frozen runtime modules imported under real audit policy usingCPU torch; no realDataset/model/optimizer instantiated.','Windows descriptor adaptation is confined to artificial child.','Inherited16 lifecycle tests reused, not rerun; no actual3900-step training.']),indent=2),encoding='utf-8');print('PASS12_REAL_IMPORT_CHAIN_FAILURE_EXIT_NO_GPU')
 except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
