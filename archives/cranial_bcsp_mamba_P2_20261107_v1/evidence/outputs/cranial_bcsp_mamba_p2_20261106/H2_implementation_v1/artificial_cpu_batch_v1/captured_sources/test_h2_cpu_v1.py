"""One synthetic CPU batch; real parent forward/loss AST, artificial local operators."""
import ast,copy,hashlib,importlib.util,io,json,math,sys,time,types,unittest
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F
S=Path(__file__).resolve().parent;R=S.parents[2];sys.path.insert(0,str(S));torch.set_num_threads(2)
import bcsp_h2_range_v1 as h
import bcsp_h2_model_adapter_v1 as a
SOURCE=R/'outputs/cranial_scqr_v12_qa_github_publish_20261019/models/AdaPoinTr.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'
TREE=ast.parse(SOURCE.read_text(encoding='utf-8'))
def original(classname,method):
 cls=next(n for n in TREE.body if isinstance(n,ast.ClassDef) and n.name==classname);node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
 scope=dict(torch=torch,misc=types.SimpleNamespace(fps=lambda xyz,n:xyz[:,:n]));exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE),'exec'),scope);return scope[method]
class SpyLinear(nn.Linear):
 def forward(self,x):self.last=x;return super().forward(x)
class Decoder(nn.Module):
 def __init__(self):super().__init__();self.pos=nn.Linear(3,8)
 def forward(self,*,q,v,q_pos,v_pos):self.last_pos=q_pos;return q+self.pos(q_pos)+v.mean(1,keepdim=True)
class Decode(nn.Linear):
 def forward(self,x):self.last=super().forward(x).reshape(x.shape[0],256,32,3);return self.last
class Loss(nn.Module):
 def forward(self,x,y):self.last=x;return (x.mean(1)-y.mean(1)).square().sum(-1).mean()+x.square().mean()*.01
class Base(nn.Module):
 forward=original('PCTransformer','forward')
 def __init__(self):
  super().__init__();self.full_instrumentation_enabled=False;self.scqr_contract=types.SimpleNamespace(enabled=False,contact_supervision_enabled=False);self.scqr_local_geometry=None
  self.encoder_adapter=nn.Identity();self.encoder_adapter.enabled=False;self.query_selection='learned_only';self.num_query=256;self.rim_query_enabled=False;self.use_denoise=False
  self.enc=nn.Linear(3,8);self.increase_dim=nn.Linear(8,1024);self.coarse_pred=nn.Linear(1024,768);self.mlp_query=SpyLinear(1027,8);self.mem_link=nn.Identity();self.decoder=Decoder()
 def encode_rim_proxy_tokens(self,x):
  coor=x[:,:256];features=self.enc(coor);return coor,torch.cat([features,coor],-1),features,features
class Model(nn.Module):
 forward=original('AdaPoinTr','forward');get_loss=original('AdaPoinTr','get_loss');get_fine_loss_components=original('AdaPoinTr','get_fine_loss_components')
 def __init__(self):
  super().__init__();self.base_model=Base();self.full_instrumentation_enabled=False;self.num_query=256;self.num_points=8192;self.factor=32;self.decoder_type='fc';self.denoise_weight=0;self.fine_coverage_weight=1;self.fine_local_weight=0
  self.increase_dim=nn.Conv1d(8,1024,1);self.reduce_map=SpyLinear(1035,8);self.decode_head=Decode(8,96);self.loss_func=Loss();self.fine_loss_func=Loss();self.scqr_contract=types.SimpleNamespace(enabled=False,contact_supervision_enabled=False)
  for key in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']:setattr(self,key,False)
  self.flagged=nn.Parameter(torch.ones(2));self.flagged._no_weight_decay=True
class Factory:
 def build_model(self,builder,variant,seed=0):
  assert variant=='M0' and seed==0
  with torch.random.fork_rng(devices=[]):torch.manual_seed(seed);m=builder()
  return m,dict(variant='M0',common_state_unchanged=True,artificial_fixture=True)
def model(mode='COUPLE'):return a.build_h2(Factory(),Model,mode)[0]
def inputs(batch=1):
 x=torch.linspace(-1,1,8192*3).reshape(1,8192,3).repeat(batch,1,1);g=torch.sin(torch.arange(8192*3,dtype=torch.float32)*.03).reshape(1,8192,3).repeat(batch,1,1);return x,g
def nodes(path,names,namespace):
 tree=ast.parse(path.read_text(encoding='utf-8'));body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names];exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),namespace);return namespace
PARENT=R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_training_runtime_v1.py'
runtime=nodes(S/'bcsp_h2_training_runtime_v1.py',{'optimizer_groups'},dict(torch=torch,require=h.require))
spec=importlib.util.spec_from_file_location('h2_frozen_adapter',R/'outputs/cranial_bcsp_geov1_20261024/implementation_candidate_v4/overlay/tools/bcsp_adapter.py');guardmod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=guardmod;spec.loader.exec_module(guardmod)
class Tests(unittest.TestCase):
 def test01_parent_source_frozen(self):self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4')
 def test02_OFF_is_exact_original(self):
  m=Factory().build_model(Model,'M0')[0];keys=set(m.state_dict());rng=torch.get_rng_state().clone();self.assertIs(a.install_h2(m,'OFF'),m);self.assertEqual(keys,set(m.state_dict()));self.assertFalse(m.base_model.coarse_pred._forward_hooks);self.assertTrue(torch.equal(rng,torch.get_rng_state()));self.assertFalse(hasattr(m,'h2_range_head'))
 def test03_common_state_and_rng(self):
  off=model('OFF');aux=model('AUX');couple=model();self.assertEqual(sum(p.numel() for p in aux.h2_range_head.parameters()),1025)
  for name,v in off.state_dict().items():self.assertTrue(torch.equal(v,aux.state_dict()[name]) and torch.equal(v,couple.state_dict()[name]))
  self.assertEqual(set(aux.state_dict())-set(off.state_dict()),{'h2_range_head.weight','h2_range_head.bias'})
 def test04_neutral_initialization_forward_loss(self):
  x,g=inputs();ms=[model(k) for k in ['OFF','AUX','COUPLE']];ret=[m(x) for m in ms]
  for r in ret[1:]:torch.testing.assert_close(r[0],ret[0][0],rtol=0,atol=0);torch.testing.assert_close(r[3],ret[0][3],rtol=0,atol=0)
  base=ms[0].get_loss(ret[0],g);s,d=ms[1].get_loss(ret[1],g);log=ms[1].h2_runtime_record();self.assertAlmostEqual(float(d-base[1]),log['H2_aux_weighted'],places=6);self.assertEqual(float(s),float(base[0]))
 def test05_actual_five_coordinate_consumers(self):
  m=model();m.h2_range_head.bias.data.fill_(.2);x,g=inputs();ret=m(x);used=m._h2_controller.context['used'];raw=m._h2_controller.context['raw']
  self.assertGreater(float((used-raw).abs().max()),0)
  for v in [m.base_model.mlp_query.last[:,:,-3:],m.base_model.decoder.last_pos,m.reduce_map.last[:,:,-3:],ret[0]]:torch.testing.assert_close(v,used,rtol=0,atol=0)
  torch.testing.assert_close(ret[3].reshape(1,256,32,3),used.unsqueeze(2)+m.decode_head.last,rtol=0,atol=0)
  m.get_loss(ret,g);torch.testing.assert_close(m.loss_func.last,used,rtol=0,atol=0)
 def test06_AUX_never_couples(self):
  x,_=inputs();m=model('AUX');m.h2_range_head.bias.data.fill_(2);r=m(x);b=model('OFF')(x);torch.testing.assert_close(r[0],b[0],rtol=0,atol=0);torch.testing.assert_close(r[3],b[3],rtol=0,atol=0)
 def test07_center_radius_identities(self):
  q=torch.linspace(-.2,.3,256*3,dtype=torch.float64).reshape(1,256,3);used,s,r=h.soft_couple(q,torch.tensor([[.25]],dtype=torch.float64));mu,ru=h.moments(used);mq,_=h.moments(q);torch.testing.assert_close(mu,mq,rtol=1e-12,atol=1e-12);torch.testing.assert_close(ru,r*s[:,0],rtol=1e-12,atol=1e-12)
 def test08_extreme_bounds(self):
  q=torch.linspace(-1,1,256*3).reshape(1,256,3).repeat(2,1,1);_,s,_=h.soft_couple(q,torch.tensor([[1e8],[-1e8]]));torch.testing.assert_close(s[:,0],torch.tensor([1.25,.8]),rtol=1e-6,atol=1e-7)
 def test09_nonfinite_points_reject(self):
  with self.assertRaises(ValueError):h.moments(torch.full((1,256,3),float('nan')))
 def test10_nonfinite_delta_reject(self):
  with self.assertRaises(ValueError):h.soft_couple(torch.arange(768,dtype=torch.float32).reshape(1,256,3),torch.tensor([[float('inf')]]))
 def test11_degenerate_reject(self):
  with self.assertRaises(ValueError):h.moments(torch.zeros(1,256,3))
 def test12_no_epsilon_added(self):
  p=torch.tensor([[[-2e-6,0.,0.],[2e-6,0.,0.]]],dtype=torch.float64);_,r=h.moments(p);torch.testing.assert_close(r,torch.tensor([2e-6],dtype=torch.float64),rtol=0,atol=1e-20)
 def test13_GT_gradient_reject(self):
  x,g=inputs();q=torch.linspace(-1,1,768).reshape(1,256,3)
  with self.assertRaises(ValueError):h.auxiliary(torch.zeros(1,1),q,g.requires_grad_())
 def test14_batch_smoothL1_contract(self):
  _,g=inputs(2);q=torch.linspace(-.1,.1,768).reshape(1,256,3).repeat(2,1,1);delta=torch.tensor([[.02],[.4]]);loss,t=h.auxiliary(delta,q,g);manual=F.smooth_l1_loss(delta[:,0],t,beta=.1,reduction='none').mean();torch.testing.assert_close(loss,manual,rtol=0,atol=0)
 def test15_equal_radius_not_shape(self):
  g=torch.zeros(1,8192,3);g[0,:,1]=torch.tensor([-1.,1.]).repeat(4096);q=torch.zeros(1,256,3);q[0,:,0]=torch.tensor([-1.,1.]).repeat(128);loss,t=h.auxiliary(torch.zeros(1,1),q,g);self.assertEqual(float(loss),0.);self.assertEqual(float(t),0.);self.assertFalse(torch.equal(q[0,0],g[0,0]))
 def test16_aux_gradient_contract(self):
  m=model();m.h2_range_head.weight.data.fill_(.001);x,g=inputs();m(x);c=m._h2_controller.context;loss,_=h.auxiliary(c['delta'],c['raw'],g);p=[m.base_model.coarse_pred.weight,m.h2_range_head.weight,m.base_model.enc.weight];grad=torch.autograd.grad(loss,p,allow_unused=True);self.assertIsNone(grad[0]);self.assertGreater(float(grad[1].abs().sum()),0);self.assertGreater(float(grad[2].abs().sum()),0)
 def test17_reconstruction_gradient_contract(self):
  m=model();m.h2_range_head.bias.data.fill_(.2);x,g=inputs();r=m(x);s,d=m._h2_controller.original_get_loss(r,g);p=[m.h2_range_head.weight,m.h2_range_head.bias,m.base_model.coarse_pred.weight,m.base_model.enc.weight];grad=torch.autograd.grad(s+d,p,allow_unused=True);self.assertIsNone(grad[0]);self.assertIsNone(grad[1]);self.assertGreater(float(grad[2].abs().sum()),0);self.assertGreater(float(grad[3].abs().sum()),0)
 def test18_total_actual_loss_backward(self):
  m=model();x,g=inputs();r=m(x);s,d=m.get_loss(r,g);(s+d).backward();self.assertIsNotNone(m.h2_range_head.weight.grad);self.assertGreater(float(m.h2_range_head.weight.grad.abs().sum()),0);self.assertGreater(float(m.base_model.coarse_pred.weight.grad.abs().sum()),0)
 def test19_exact_once_weight_and_target_rawQ(self):
  m=model();m.h2_range_head.bias.data.fill_(.4);x,g=inputs();ret=m(x);c=m._h2_controller.context;_,old=m._h2_controller.original_get_loss(ret,g);_,new=m.get_loss(ret,g);loss,t=h.auxiliary(c['delta'],c['raw'],g);torch.testing.assert_close(new,old+.1*loss,rtol=0,atol=0);_,rq=h.moments(c['raw']);_,rg=h.moments(g);torch.testing.assert_close(t,rg.log()-rq.log(),rtol=0,atol=0);self.assertNotEqual(float(rq),float(h.moments(c['used'])[1]))
 def test20_duplicate_loss_reject(self):
  m=model();x,g=inputs();r=m(x);m.get_loss(r,g)
  with self.assertRaises(ValueError):m.get_loss(r,g)
 def test21_stale_training_forward_reject(self):
  m=model();x,_=inputs();m(x)
  with self.assertRaises(ValueError):m(x)
 def test22_training_intervention_reject(self):
  with self.assertRaises(ValueError):model().h2_intervention(0.)
 def test23_eval_zero_condition_only(self):
  m=model().eval();m.h2_range_head.bias.data.fill_(.2);x,_=inputs()
  with torch.inference_mode():native=m(x);raw=m._h2_controller.context['raw'].clone();m.h2_intervention(0.);off=m(x)
  torch.testing.assert_close(off[0],raw,rtol=0,atol=0);self.assertGreater(float((native[0]-off[0]).abs().max()),0)
 def test24_other_modes_reject(self):
  m=Factory().build_model(Model,'M0')[0];m.base_model.query_selection='ranking'
  with self.assertRaises(ValueError):a.install_h2(m,'COUPLE')
 def test25_duplicate_install_reject(self):
  with self.assertRaises(ValueError):a.install_h2(model(),'COUPLE')
 def test26_optimizer_groups_common_unchanged(self):
  off=model('OFF');m=model();before={r['name']:r for r in runtime['optimizer_groups'](off)[1]};after={r['name']:r for r in runtime['optimizer_groups'](m)[1]}
  for k,v in before.items():self.assertEqual(v,after[k])
  self.assertEqual(after['h2_range_head.weight']['weight_decay'],.0005);self.assertEqual(after['h2_range_head.bias']['weight_decay'],0);self.assertEqual(after['flagged']['weight_decay'],0)
 def test27_head_does_not_consume_RNG(self):
  rng=torch.get_rng_state().clone();head=h.RangeHead();self.assertTrue(torch.equal(rng,torch.get_rng_state()));self.assertEqual(float(head.weight.sum()+head.bias.sum()),0)
 def test28_runtime_only_approved_AST_delta(self):
  old=ast.parse(PARENT.read_text());new=ast.parse((S/'bcsp_h2_training_runtime_v1.py').read_text())
  class Strip(ast.NodeTransformer):
   def visit_Assign(self,node):
    if any(isinstance(t,ast.Name) and t.id=='h2_event' for t in node.targets):return None
    return self.generic_visit(node)
   def visit_Expr(self,node):
    if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='update' and len(node.value.args)==1 and isinstance(node.value.args[0],ast.Name) and node.value.args[0].id=='h2_event':return None
    return self.generic_visit(node)
   def visit_Dict(self,node):
    self.generic_visit(node);pairs=[(k,v) for k,v in zip(node.keys,node.values) if not(isinstance(k,ast.Constant) and k.value=='H2')];node.keys=[k for k,v in pairs];node.values=[v for k,v in pairs];return node
  self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(Strip().visit(new),include_attributes=False))
 def test29_exact3900_guard_no_optimizer(self):
  guard=guardmod.UpdateGuard(guardmod.Contract())
  for epoch in range(100):
   guard.begin_epoch(epoch,39)
   for _ in range(39):guard.before_step(8);guard.after_step()
   guard.end_epoch()
  self.assertEqual(guard.finish()['optimizer_updates'],3900);self.assertEqual(guard.finish()['case_exposures'],31200)
 def test30_checkpoint_strict_roundtrip(self):
  m=model('AUX');buf=io.BytesIO();payload=dict(base_model=m.state_dict(),stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,H2=m.h2_metadata());torch.save(payload,buf);buf.seek(0);saved=torch.load(buf,weights_only=True);a.validate_checkpoint_contract(saved,'AUX');model('AUX').load_state_dict(saved['base_model'],strict=True)
 def test31_runtime_log_finite_and_repeatable(self):
  m=model();x,g=inputs();r=m(x);m.get_loss(r,g);before=m.h2_runtime_record();after=m.h2_runtime_record();self.assertEqual(before,after);json.dumps(before,allow_nan=False);self.assertEqual(len(before['H2_delta']),1)
 def test32_wrong_checkpoint_mode_reject(self):
  m=model('AUX');payload=dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,H2=m.h2_metadata())
  with self.assertRaises(ValueError):a.validate_checkpoint_contract(payload,'COUPLE')
if __name__=='__main__':
 out=S/'artificial_cpu_batch_v1';out.mkdir();start=time.monotonic()
 with (out/'stdout_v1.txt').open('x',encoding='utf-8') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 files=[S/n for n in ['bcsp_h2_range_v1.py','bcsp_h2_model_adapter_v1.py','bcsp_h2_training_runtime_v1.py','test_h2_cpu_v1.py']]
 report=dict(status='H2_ARTIFICIAL_CPU_CONTRACT_PASS' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),seconds=time.monotonic()-start,python=sys.executable,torch=torch.__version__,source_bindings=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],stdout_sha256=hashlib.sha256((out/'stdout_v1.txt').read_bytes()).hexdigest(),real_data_reads=0,real_checkpoint_loads=0,GPU_calls=0,optimizer_steps=0,simulated_counter_commits=3900,real_training_runs=0,limits=['Actual frozen parent forward/get_loss AST used with artificial encoders,decoder and loss modules','No native Mamba,PointNet2,Chamfer or CUDA execution','3900 commits are guard simulation only, not optimizer steps'])
 with (out/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
 print(json.dumps(report));sys.exit(0 if result.wasSuccessful() else 1)
