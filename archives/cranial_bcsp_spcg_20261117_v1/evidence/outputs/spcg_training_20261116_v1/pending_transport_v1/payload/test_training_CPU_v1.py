"""One frozen16-item batch; actual metadata/bridge with artificial CPU lifecycle."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,traceback
import torch
from torch import nn
S=Path(__file__).resolve().parent;W=S.parents[1];O=S/'CPU_batch_v1'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[];scope=json.loads((S/'CPU_scope_v1.json').read_text());torch.set_num_threads(2)
 def check(n,v):assert v,scope['checks'][n-1];assert len(checks)==n-1;checks.append(scope['checks'][n-1])
 def reject(fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError):return True
  return False
 try:
  e=load('spcg_train_entry_cpu',S/'bcsp_spcg_training_entry_v1.py');b=load('spcg_train_bridge_cpu',S/'bcsp_spcg_training_bridge_v1.py');q=json.loads((S/'draft_G0_C_request_v1.json').read_text(encoding='utf-8'));check(1,e.COUNTS==q['counts'] and q['resources']==e.RESOURCES and e.RESOURCES['output_bytes']==1073741824)
  original=copy.deepcopy(q);audit=O/'audit.json';audit.write_text(json.dumps(dict(status='FORMAL_POST_CUDA_FREEZE_PASS',checks=dict(real=True))),encoding='utf-8');p3=O/'P3.json';p3.write_text(json.dumps(dict(status='SPCG_G0C_TRAINING_LOCAL_P3_PASS',entry_sha256=q['implementation']['entry']['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'])),encoding='utf-8');q['CUDA_freeze']=rec(audit);q['P3']=rec(p3)
  a=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256='a'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY');r=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256='a'*64,authorization_sha256='b'*64)
  bad=copy.deepcopy(q);bad['arm']='G2';check(2,e.validate(q,'a'*64,a,'b'*64,r) is q and reject(lambda:e.validate(bad,'a'*64,a,'b'*64,r)))
  bad=copy.deepcopy(q);bad['environment']['CUDA_VISIBLE_DEVICES']='GPU-old';check(3,reject(lambda:e.validate(bad,'a'*64,a,'b'*64,r)))
  ctx=json.loads((W/'outputs/scq_rive_training_implementation_20261115_v1/implementation_context_v1.json').read_text(encoding='utf-8'));mirror={k:Path(v) for k,v in ctx['mirror'].items()};B=W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload'
  def mapped(record):
   p=Path(record['path'])
   if '/bcsp_scq_foldC_training_20261113_v1/' in record['path']:p=B/PureName(record['path'])
   elif record['path'] in mirror:p=mirror[record['path']]
   elif record['path']==q['implementation']['observe']['path']:p=W/'outputs/spcg_implementation_20261116_v1/bcsp_spcg_runtime_v1.py'
   if p.exists():assert p.stat().st_size==record['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'];return p
   raise ValueError('missing precise local mirror '+record['path'])
  def PureName(p):return p.replace('\\','/').split('/')[-1]
  metadata=load('bcsp_training_contract_v1',B/'bcsp_training_contract_01dt08_v3.py');metadata.exact=mapped
  static=metadata.validate_static(json.loads(mapped(q['static_config']).read_text()));selected,fold=metadata.verify_qualified_receipt(json.loads(mapped(q['QC']['qualified_receipt']).read_text()),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192);plan=metadata.validate_order(json.loads(mapped(q['order_plan']).read_text()),fold['train_case_ids']);check(4,len(selected)==315 and len(plan['epochs'])==100)
  check(5,reject(lambda:e.validate(q,'a'*64,dict(a,runtime_sha256='c'*64),'b'*64,r)) and reject(lambda:e.validate(q,'a'*64,a,'c'*64,r)))
  launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64);check(6,'3600s' in launcher and launcher.index('mkdir -p')<launcher.index(' >') and '\\' not in launcher.replace('\\n',''))
  frozen=json.loads((W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json').read_text());completion=json.loads(frozen['output']['completion.json']['text']);check(7,q['expected_initial_state_sha256']==completion['result']['models']['G0']['initial_state_sha256'])
  check(8,'runtime.train_lifecycle(' in (S/'bcsp_spcg_training_bridge_v1.py').read_text() and 'optimizer.step' not in (S/'bcsp_spcg_training_bridge_v1.py').read_text())
  class CD(nn.Module):
   def forward(self,x,y):return x.mean().square()+.01*x.square().mean()
  class Model(nn.Module):
   def __init__(self):super().__init__();self.weight=nn.Parameter(torch.tensor(.3));self.loss_func=CD();self.fine_loss_func=CD();self.f0_evidence=dict(artificial_fixture=True)
   def forward(self,D):
    Q=self.weight.expand(1,256,3);P=self.weight.expand(1,8192,3);return Q,Q[:,:0],P[:,:0],P
  out=O/'run';out.mkdir();q['output']=str(out);m=Model();stats=dict(forward=0,loss=0,backward=0,step=0);final=[]
  observe=types.SimpleNamespace(geometry=lambda Q:dict(radius=float(Q.detach().std())),Q_gradient_record=lambda Q:dict(origin='TOTAL_LOSS_NOT_ISOLATED_COARSE',norm=float(Q.grad.norm())))
  budget=types.SimpleNamespace(after_step=lambda step:None,before_final=lambda:final.append(True));helper=types.SimpleNamespace(assert_numeric=lambda t:None,state_sha=lambda *a:'fixture')
  runtime=types.SimpleNamespace(__file__=str(B/'bcsp_p1_training_runtime_v1.py'),BCSPDataset=lambda *args:'ARTIFICIAL_DATASET',make_loader=lambda *args:None)
  def lifecycle(model,loader,*args,**kwargs):
   for step in range(1,3901):
    model.zero_grad();ret=model(torch.zeros(1,1,3));stats['forward']+=1;loss=model.loss_func(ret[0],None)+model.fine_loss_func(ret[-1],None);stats['loss']+=1;loss.backward();stats['backward']+=1;stats['step']+=1;kwargs['resources'].after_step(step)
   kwargs['resources'].before_final();return dict(status='ARTIFICIAL_LIFECYCLE_COMPLETE',counts=stats)
  runtime.train_lifecycle=lifecycle
  result=b.dispatch(q,m,runtime,selected,fold,plan,helper,budget,observe,device='cpu',artificial_cpu=True)
  rows=[json.loads(x) for x in (out/'SPCG_geometry.jsonl').read_text().splitlines()];check(9,[x['step'] for x in rows if 'total_loss_Q_gradient' in x]==list(b.LOG_STEPS))
  check(10,all(set(x['loss_components'])=={'coarse_CD','dense_CD'} for x in rows))
  check(11,len(rows)==3900 and result['counts']==dict(forward=3900,loss=3900,backward=3900,step=3900) and final==[True])
  runtime.train_lifecycle=lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('ARTIFICIAL_FAIL'))
  check(12,reject(lambda:b.dispatch(q,m,runtime,selected,fold,plan,helper,budget,observe,device='cpu',artificial_cpu=True)) and not m._forward_hooks and not m.loss_func._forward_hooks)
  source=(B/'bcsp_p1_training_runtime_v1.py').read_text();check(13,"getattr(p, '_no_weight_decay', False)" in source and 'torch.optim.AdamW' in source)
  # Exact source policy was exercised by final v6 inherited file-policy batch; bind it, do not repeat.
  policy=json.loads((W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/CPU_batch_v6/result.json').read_text());check(14,policy['count']==12 and policy['child']['source_write_denied'] and policy['child']['negative_hash_binding_rejected'])
  # Full authorize() with actual metadata verifier and local record mapping; no real payloads.
  q['output']=original['output'];qfile=O/'q.json';qfile.write_text(json.dumps(q),encoding='utf-8');qh=rec(qfile);a['request_sha256']=qh['sha256'];afile=O/'a.json';afile.write_text(json.dumps(a));ar=rec(afile);rfile=O/'r.json';rfile.write_text(json.dumps(dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh['sha256'],authorization_sha256=ar['sha256'])));rr=rec(rfile)
  oldexact=e.exact;oldsource=e.source
  def mapping(record):
   if record['path']==q['implementation']['entry']['path']:return S/'bcsp_spcg_training_entry_v1.py'
   if record['path']==q['implementation']['bridge']['path']:return S/'bcsp_spcg_training_bridge_v1.py'
   return mapped(record)
  # mapped falls back to e.exact; local paths are handled directly to avoid recursion.
  def safe(record):
   p=Path(record['path'])
   if p.is_file():return oldexact(record)
   return mapping(record)
  e.exact=safe;e.source=lambda n,r:metadata
  try:authorized=e.authorize(qh,ar,rr)
  finally:e.exact=oldexact;e.source=oldsource
  check(15,len(authorized[2])==315 and authorized[4]==plan)
  [ast.parse(p.read_text(encoding='utf-8')) for p in [S/'bcsp_spcg_training_entry_v1.py',S/'bcsp_spcg_training_bridge_v1.py']];check(16,hashlib.sha256((B/'bcsp_p1_training_runtime_v1.py').read_bytes()).hexdigest()==q['implementation']['training_runtime']['sha256'])
  (O/'result.json').write_text(json.dumps(dict(status='SPCG_G0C_TRAINING_CPU_PASS',count=len(checks),checks=checks,entry=rec(S/'bcsp_spcg_training_entry_v1.py'),bridge=rec(S/'bcsp_spcg_training_bridge_v1.py'),test=rec(Path(__file__)),artificial_counts=stats,logged_rows=len(rows),real_payload_reads=0,GPU=0,server_operations=0,limitations=['Artificial lifecycle substitutes the optimizer loop; original runtime not executed and actual3900step training not certified.','Same-forward model/loss/gradient hooks executed3900times on tiny artificial CPU tensors; no actual Mamba/cdist/data.','Existing policy regression evidence reused, not newly run.']),indent=2),encoding='utf-8');print('PASS16_ARTIFICIAL_CPU')
 except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
