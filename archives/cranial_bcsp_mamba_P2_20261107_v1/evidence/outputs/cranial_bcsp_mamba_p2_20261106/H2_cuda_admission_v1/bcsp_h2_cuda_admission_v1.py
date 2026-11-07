"""H2-only synthetic CUDA admission: two eval/autograd F/B, no optimizer."""
import argparse,ast,gc,hashlib,importlib.util,json,os,random,socket,sys
from pathlib import Path

def need(ok,msg):
 if not ok:raise ValueError(msg)
def clean(path):
 p=Path(path).absolute();need(not any(x.is_symlink() for x in (p,*p.parents)),'linked path '+str(p));need(not {'.ssh','.aws','.credentials','.git'}&set(p.parts) and p.name not in ['.env','.netrc'],'secret path');return p
def sha(path):
 h=hashlib.sha256()
 with clean(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def exact(r):
 p=clean(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'binding '+str(p));return p
def bound(r):return json.loads(exact(r).read_bytes())
def emit(p,data):
 with clean(p).open('x',encoding='ascii') as f:json.dump(data,f,indent=2,allow_nan=False)
def module(name,record):
 spec=importlib.util.spec_from_file_location(name,exact(record));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def authorize(qr,ar,rr):
 q=bound(qr);a=bound(ar);r=bound(rr)
 need(q['schema']=='bcsp-h2-synthetic-cuda-admission-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','request')
 need(q['science']==dict(models=['AUX','COUPLE'],forward_attempt_limit=2,backward_attempt_limit=2,optimizer_steps=0,loss_calls=2,real_data_reads=0,checkpoint_loads=0,mode='eval_with_autograd',batch_size=1,n_input=8192,n_output=8192),'2F/2B/0 fixed contract')
 need(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-h2-cuda-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate authorization')
 need(r==dict(schema='bcsp-h2-cuda-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime binding')
 return q
def load_artificial(np,record):
 p=exact(record)
 with np.load(p,allow_pickle=False) as z:
  need(set(z.files)=={'partial','target'},'synthetic schema');x=z['partial'].copy();g=z['target'].copy()
 need(x.shape==g.shape==(8192,3) and x.dtype==g.dtype==np.float32 and np.isfinite(x).all() and np.isfinite(g).all(),'synthetic finite FP32 tensors')
 return x,g
def optimizer_group_records(torch,record,model):
 tree=ast.parse(exact(record).read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');scope=dict(require=need);exec(compile(ast.Module(body=[fn],type_ignores=[]),'<frozen_H2_optimizer_groups>','exec'),scope);groups,rows=scope['optimizer_groups'](model);del groups;return rows
def evaluate_pair(torch,np,parent,helper,h2_adapter,builder,x,target,out,budget,*,device='cuda:0',artificial=False):
 counts=dict(forward_attempts=0,forward_returns=0,loss_calls=0,backward_attempts=0,backward_returns=0,optimizer_steps=0);results=[]
 journal=out/'attempts.jsonl';journal.open('x').close();cuda=device=='cuda:0'
 try:
  common=None
  for mode in ['AUX','COUPLE']:
   random.seed(0);np.random.seed(0);torch.manual_seed(0)
   model,construction=builder(mode);helper.validate_model(model)
   need(construction['variant']=='M0' and construction['artificial_fixture'] is artificial and construction['common_state_after_H2_unchanged'] and construction['replaced_global_branches']==6,'native M0 construction')
   need(model.h2_metadata()['mode']==mode,'H2 mode')
   if common is None:common=construction['common_state']
   need(common==construction['common_state'],'paired common initialization')
   need(bool((model.h2_range_head.weight==0).all()) and bool((model.h2_range_head.bias==0).all()),'training head starts zero')
   # Explicit synthetic fixture setting BEFORE before/after snapshot; not trained weights.
   with torch.no_grad():model.h2_range_head.weight.fill_(1e-3/1024);model.h2_range_head.bias.fill_(.1)
   model.eval().to(device);model.zero_grad(set_to_none=True)
   if cuda:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
   need(not any(m.training for m in model.modules()),'all eval, BN frozen')
   state_before=helper.state_sha(model);rng_before=parent.rng_state(torch,np,helper,cuda);budget.sample('before_forward:'+mode,counts['forward_attempts']);helper.assert_numeric(torch)
   need(counts['forward_attempts']<2,'forward budget');counts['forward_attempts']+=1
   parent.append_event(journal,dict(event='CLAIMED_BEFORE_FORWARD',mode=mode,index=counts['forward_attempts']))
   with torch.enable_grad():
    output=model(x)
    need(isinstance(output,(tuple,list)) and len(output)==2,'native eval tuple')
    coarse,dense=output;need(tuple(coarse.shape)==(1,256,3) and tuple(dense.shape)==(1,8192,3) and bool(torch.isfinite(coarse).all()) and bool(torch.isfinite(dense).all()),'native output counts/finite');counts['forward_returns']+=1
    # Frozen no-denoise loss interface; no second forward or BN mode change.
    ret=(coarse,coarse[:,:0],dense[:,:0],dense);sparse,recon=model.get_loss(ret,target);counts['loss_calls']+=1;loss=sparse+recon
    need(loss.ndim==0 and bool(torch.isfinite(loss)),'finite true original+H2 loss');log=model.h2_runtime_record()
    budget.sample('before_backward:'+mode,counts['forward_attempts']);need(counts['backward_attempts']<2,'backward budget');counts['backward_attempts']+=1
    parent.append_event(journal,dict(event='CLAIMED_BEFORE_BACKWARD',mode=mode,index=counts['backward_attempts']))
    loss.backward();counts['backward_returns']+=1
   if cuda:torch.cuda.synchronize()
   gradients={}
   for name,p in model.named_parameters():
    if p.grad is not None:
     need(bool(torch.isfinite(p.grad).all()),'nonfinite gradient '+name);gradients[name]=float(p.grad.detach().double().norm())
   need('h2_range_head.weight' in gradients and gradients['h2_range_head.weight']>0 and gradients.get('h2_range_head.bias',0)>0,'nonzero condition head gradient')
   need(any(n.startswith('base_model.coarse_pred.') and v>0 for n,v in gradients.items()),'coarse reconstruction gradients')
   need(any(n.startswith('base_model.encoder.') and v>0 for n,v in gradients.items()),'encoder gradients')
   state_after=helper.state_sha(model);rng_after=parent.rng_state(torch,np,helper,cuda)
   need(state_before==state_after and rng_before==rng_after,'weight/BN/RNG drift')
   c=model._h2_controller.context
   if mode=='COUPLE':need(bool((c['scale']-1).abs().max()>1e-6),'nonneutral fixture exercises coupling')
   else:need(bool((c['scale']==1).all()),'AUX remains uncoupled')
   result=dict(mode=mode,loss=float(loss.detach()),counts=dict(counts),state_before=state_before,state_after=state_after,RNG_before=rng_before,RNG_after=rng_after,gradient_norms=gradients,H2_log=log,construction=construction,fixture_head=dict(weight=1e-3/1024,bias=.1,configured_before_snapshot=True),model_mode='eval_with_autograd',optimizer_constructed=False)
   emit(out/(mode+'_result.json'),result);results.append(result);budget.sample('after_backward:'+mode,counts['forward_attempts']);helper.assert_numeric(torch)
   del model,construction,output,coarse,dense,ret,sparse,recon,loss,c;gc.collect()
   if cuda:torch.cuda.empty_cache()
  need(counts==dict(forward_attempts=2,forward_returns=2,loss_calls=2,backward_attempts=2,backward_returns=2,optimizer_steps=0),'exact final counts')
  budget.sample('all_complete',2);return counts,results
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',counts=counts,error=repr(exc),real_data_reads=0,optimizer_constructed=False));raise

def main():
 parser=argparse.ArgumentParser()
 for k in ['request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256']:parser.add_argument('--'+k,required=True)
 args=parser.parse_args()
 def rec(p,h):return dict(path=p,bytes=clean(p).stat().st_size,sha256=h)
 qr=rec(args.request,args.request_sha256);q=authorize(qr,rec(args.authorization,args.authorization_sha256),rec(args.runtime,args.runtime_sha256));I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
 need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
 need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'resource identity')
 need(Path(__file__).resolve()==exact(q['entry']),'entry hash');parent_command=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
 need(parent_command[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s',str(q['limits']['wall_seconds'])+'s'],'external timeout')
 need(json.loads(clean(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single-use attempt')
 for b in [q['h2_range'],q['h2_adapter'],q['h2_training_runtime'],q['artificial_input'],*q['implementation'].values(),*q['dependencies']]:exact(b)
 p3=bound(q['P3']);need(p3['status']=='LOCAL_H2_CUDA_ENTRY_CPU_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'bound entry P3')
 parent=module('h2_frozen_parent',q['parent_entry']);static=bound(q['static_config']);scope=bound(q['preflight_scope']);bound(q['numeric_policy']);helper=parent.module('h2_frozen_helper',q['helper']);helper._MONITOR=None;records=helper.source_map(scope)
 for rel,b in records.items():helper.exact(root/rel,b['sha256'],b['bytes'])
 helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
 for b in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(b['path'],b['sha256'],b['bytes'])
 for k,v in q['environment'].items():need(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
 smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')];need(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'physical device/idle')
 need(out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2'),'output boundary')
 if out.exists():need({p.name for p in out.iterdir()}=={'launch.log'},'new output')
 else:out.mkdir()
 (out/'tmp').mkdir();(out/'worker.pid').write_text(str(os.getpid()))
 timezone=parent.module('h2_exact_utc',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE);source_guard=parent.ExactSourceReads(q['implementation'])
 try:
  envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
  sys.path[:0]=[str(Path(__file__).parent),str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
  helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
  policy=parent.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[q['artificial_input']['path']],[],[],utc,source_guard);sys.addaudithook(policy.audit)
  import numpy as np
  import torch,timm,yaml,importlib
  from easydict import EasyDict
  need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions');need(torch.cuda.is_available() and torch.cuda.device_count()==1,'one CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
  ch=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext');helper.check_backend(ch,pn,pm);need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'native provider origins')
  transformer=importlib.import_module('models.Transformer_utils');cls=importlib.import_module('models.AdaPoinTr').AdaPoinTr;need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'unchanged base config');transformer.enable_bcsp_knn()
  factory=parent.load_p1_factory(q['implementation']);need(Path(sys.modules['bcsp_mamba_encoder_v1'].__file__).resolve()==exact(q['implementation']['encoder']),'encoder source origin')
  module('bcsp_h2_range_v1',q['h2_range']);adapter=module('bcsp_h2_model_adapter_v1',q['h2_adapter'])
  def builder(mode):
   m,evidence=adapter.build_h2(factory,lambda:cls(EasyDict(static['model'])),mode,seed=0)
   groups=optimizer_group_records(torch,q['h2_training_runtime'],m);emit(out/(mode+'_optimizer_groups.json'),groups)
   if mode=='AUX':
    names=['mamba_ssm','mamba_ssm.modules.mamba_simple','mamba_ssm.ops.selective_scan_interface','causal_conv1d','causal_conv1d.causal_conv1d_interface','selective_scan_cuda','causal_conv1d_cuda'];mods=[importlib.import_module(n) for n in names];origins=[str(Path(v.__file__).resolve()) for v in mods];need(set(origins)<=set(r['path'] for r in q['dependencies']),'Mamba native origins');emit(out/'native_SSM_origins.json',dict(origins=origins,version=mods[0].__version__));need(mods[0].__version__=='2.3.1','Mamba version')
   return m,evidence
  x,g=load_artificial(np,q['artificial_input']);x=torch.from_numpy(x).unsqueeze(0).to('cuda:0');g=torch.from_numpy(g).unsqueeze(0).to('cuda:0');budget=parent.Budget(q,out,torch,helper)
  counts,results=evaluate_pair(torch,np,parent,helper,adapter,builder,x,g,out,budget)
  emit(out/'completion.json',dict(status='H2_SYNTHETIC_CUDA_COMPLETE_PENDING_FREEZE_AUDIT',request_sha256=qr['sha256'],counts=counts,model_modes=[r['mode'] for r in results],weight_BN_RNG_equal=True,real_data_reads=0,checkpoint_loads=0,optimizer_constructed=False,training_executed=False,BNCal=False))
  files=[p for p in out.iterdir() if p.is_file() and p.name not in ['launch.log','worker.pid']];emit(out/'payload_manifest.json',dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
 except BaseException as exc:
  if not (out/'failure.json').exists():emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),optimizer_constructed=False))
  raise
 finally:source_guard.close();utc.close()
if __name__=='__main__':main()
