"""P2 fixed-feature probe. Reuse P1 loader/budget; no optimizer or dense forward."""
import argparse,gc,hashlib,importlib.util,json,os,random,socket,sys
from pathlib import Path

DEFECTS={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
MODEL_SHA={
 'C_T0':'8671656b5a2b0843ed426868d9d06976a2ead816808f9f7c54ddadb83515ab07',
 'C_M0':'bc6a489bcd4df5123a3bb6616105d7ec4628fc365e71313398ee516bcf72ef9a',
 'D_T0':'ed901f18be2efb84f9b7b159cec2b71a3602e2e960087ac53d510881be9eba7c',
 'D_M0':'9e6f5c3034b051474e0ca78de725ba1579c2ddd25b2acf9848a1f8bf21c79263'}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def clean(path):
 p=Path(path).absolute();need(not any(x.is_symlink() for x in (p,*p.parents)),'link path '+str(p));return p
def exact(r):
 p=clean(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'],'size '+str(p));h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 need(h.hexdigest()==r['sha256'],'hash '+str(p));return p
def bound(r):return json.loads(exact(r).read_bytes())
def load_module(name,record):
 p=exact(record);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def emit(path,data):
 def convert(x):
  if hasattr(x,'tolist'):return x.tolist()
  raise TypeError(type(x).__name__)
 with clean(path).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,allow_nan=False,default=convert)
def authorize(qr,ar,rr):
 q=bound(qr);a=bound(ar);r=bound(rr)
 need(q['schema']=='bcsp-p2-condition-probe-execution-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','request')
 need(q['prefix_budget']==1680 and all(q[k]==0 for k in ['backward','optimizer_steps','dense_forwards','BNCal']),'1680/0 contract')
 need(a==dict(schema='bcsp-condition-probe-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text=a.get('user_authorization_text')) and bool(a['user_authorization_text'].strip()),'authorization')
 need(r==dict(schema='bcsp-condition-probe-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
 return q
def validate_index(index):
 runs=index['runs'];rows=index['inputs'];need([r['label'] for r in runs]==list(MODEL_SHA) and len(rows)==1680,'four corresponding models/1680')
 for run in runs:
  label=run['label'];fold,variant=label.split('_');need(run['fold']==fold and run['variant']==variant and run['seed']==0 and run['checkpoint']['sha256']==MODEL_SHA[label],'fixed model identity')
  part=[r for r in rows if r['run']==label];need(len(part)==420 and len({r['case_id'] for r in part})==420,'unique420/model')
  sets={}
  for role,n,ns in [('train',315,63),('development',105,21)]:
   rs=[r for r in part if r['role']==role];ss={r['source_id'] for r in rs};need(len(rs)==n and len(ss)==ns,'role counts')
   for sid in ss:need({r['case_id'].split('__',2)[2] for r in rs if r['source_id']==sid}==DEFECTS and sum(r['source_id']==sid for r in rs)==5,'five defects')
   sets[role]=ss
  need(not sets['train']&sets['development'],'source leakage')
  need([r['case_id'] for r in part if r['role']=='train']==run['train_case_ids'] and [r['case_id'] for r in part if r['role']=='development']==run['dev_case_ids'],'frozen order')
  for row in part:
   need(row['fold']==fold and row['variant']==variant and row['source_id']=='train:'+row['case_id'].split('__')[1] and row['normalization_source']=='defective_bbox','row identity/frame')
   need(row['input']['path'].startswith('/home/jovyan/adapointr_work/PoinTr/data/') and row['input']['path'].endswith('/'+row['case_id']+'_8192.npz'),'exact point path')
   need(row['normalization']['scale']>0 and len(row['normalization']['center'])==3,'D frame')
   need(('frozen_coarse' in row)==(row['role']=='development'),'native baseline for every dev')
 for fold in ['C','D']:
  a,b=[[r for r in rows if r['run']==fold+'_'+v] for v in ['T0','M0']]
  need([{k:r[k] for k in ['case_id','source_id','role','input','normalization','target_array_sha256']} for r in a]==[{k:r[k] for k in ['case_id','source_id','role','input','normalization','target_array_sha256']} for r in b],'same fold model pair')
 return runs,rows
def load_target(np,row):
 with np.load(exact(row['input']),allow_pickle=False) as z:g=z['implant'].copy()
 need(g.shape==(8192,3) and g.dtype==np.float32 and np.isfinite(g).all(),'GT shape/dtype/finite')
 need(hashlib.sha256(g.tobytes(order='C')).hexdigest()==row['target_array_sha256'],'GT array binding');return g
def check_native(np,qpoints,row):
 if row['role']!='development':return
 s=row['frozen_coarse'];x=qpoints.astype('float64');mu=x.mean(0);radius=np.sqrt(((x-mu)**2).sum(1).mean())
 # Inherited P1 saved-Q/summary tolerance; no tuning on this experiment.
 need(np.allclose(mu,s['centroid'],rtol=1e-9,atol=1e-7) and np.isclose(radius,s['radius_gyration'],rtol=1e-8,atol=1e-7),'coarse prefix/native equivalence')
def save_comparison(np,core,out,run,records):
 result=core.compare([r for r in records if r['role']=='train'],[r for r in records if r['role']=='development'])
 label=run['label'];arrays={}
 for arm,fit in result['fits'].items():
  for k,v in fit.items():
   if isinstance(v,np.ndarray):arrays[arm+'__'+k]=v
 for arm,v in result['predictions'].items():arrays['prediction__'+arm]=v;arrays['error__'+arm]=result['case_errors'][arm]
 with (out/(label+'_readout.npz')).open('xb') as f:np.savez_compressed(f,**arrays)
 summary={};base=result['source_errors']['coarse']
 for arm,ss in result['source_errors'].items():
  ids=sorted(ss);values=np.asarray([ss[s] for s in ids]);delta=values-np.asarray([base[s] for s in ids])
  summary[arm]=dict(source_mean=values.mean(0),source_median=np.median(values,axis=0),mean_delta_vs_coarse=delta.mean(0),improved_sources=(delta<0).sum(0),tied_sources=(delta==0).sum(0),worse_sources=(delta>0).sum(0),source_errors=ss)
 dev=[r for r in records if r['role']=='development'];strata={}
 for defect in sorted(DEFECTS):
  selected=[i for i,r in enumerate(dev) if r['case_id'].split('__',2)[2]==defect];need(len(selected)==21,'stratum count')
  strata[defect]={arm:v[selected].mean(0) for arm,v in result['case_errors'].items()}
 emit(out/(label+'_summary.json'),dict(run=label,metric_order=['centroid_mm','centroid_over_GT_radius','absolute_log_radius_error'],case_ids=[r['case_id'] for r in dev],source_equal=summary,defects=strata,fits={k:{n:v for n,v in fit.items() if not isinstance(v,np.ndarray)} for k,fit in result['fits'].items()},development_fitted=False,formal_gate=False))
 return result
def execute(torch,np,parent,helper,capture,core,runs,rows,out,budget,builder,*,device='cuda:0',artificial=False):
 cuda=device=='cuda:0';attempts=0;files=[];evidence=[]
 for name in ['prefix_attempts.jsonl','tensor_manifest.jsonl']:(out/name).open('x').close()
 try:
  for run in runs:
   random.seed(0);np.random.seed(0);torch.manual_seed(0)
   model,construction=builder(run);helper.validate_model(model)
   need(construction['variant']==run['variant'] and construction['common_state_unchanged'] and construction['artificial_fixture'] is artificial and construction['replaced_global_branches']==(6 if run['variant']=='M0' else 0),'factory')
   parent.load_checkpoint(torch,model,run['checkpoint']);model.eval();model.to(device)
   if cuda:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
   state=helper.state_sha(model);rng=parent.rng_state(torch,np,helper,cuda);records=[];budget.sample('model_start:'+run['label'],attempts)
   for row in [r for r in rows if r['run']==run['label']]:
    helper.assert_numeric(torch);budget.sample('before_prefix',attempts);partial=parent.load_partial(np,dict(row,n_input=8192));x=torch.from_numpy(partial).unsqueeze(0).to(device)
    need(attempts<1680,'prefix budget');attempts+=1;parent.append_event(out/'prefix_attempts.jsonl',dict(attempt=attempts,run=run['label'],case_id=row['case_id'],status='CLAIMED_BEFORE_PREFIX'))
    tensors=capture.capture_prefix(torch,model,x)
    if cuda:torch.cuda.synchronize()
    z=tensors['feature1024'][0].cpu().numpy().copy();coarse=tensors['coarse'][0].cpu().numpy().copy();check_native(np,coarse,row)
    # GT is read only after the D-only model prefix has returned.
    target=load_target(np,row);record=dict(run=run['label'],fold=run['fold'],variant=run['variant'],role=row['role'],case_id=row['case_id'],source_id=row['source_id'],scale=row['normalization']['scale'],feature1024=z,coarse4=core.moments(coarse),target4=core.moments(target),geometry18=core.geometry18(partial))
    path=out/'features'/(run['label']+'__'+row['case_id']+'.npz')
    with path.open('xb') as f:np.savez_compressed(f,feature1024=z,coarse4=record['coarse4'],target4=record['target4'],geometry18=record['geometry18'])
    parent.append_event(out/'tensor_manifest.jsonl',{**{k:v for k,v in record.items() if k not in ['feature1024','coarse4','target4','geometry18']},'input_sha256':row['input']['sha256'],'target_array_sha256':row['target_array_sha256'],'checkpoint_sha256':run['checkpoint']['sha256'],'normalization':row['normalization'],'file':dict(name=str(path.relative_to(out)).replace('\\','/'),bytes=path.stat().st_size,sha256=parent.sha(path))})
    files.append(path);records.append(record);del tensors,x,target;helper.assert_numeric(torch);budget.sample('after_prefix',attempts)
   need(state==helper.state_sha(model) and rng==parent.rng_state(torch,np,helper,cuda),'state/BN/RNG changed')
   del model;gc.collect()
   if cuda:torch.cuda.empty_cache()
   evidence.append(dict(run=run['label'],prefix_calls=len(records),state_unchanged=True,RNG_unchanged=True))
   budget.sample('before_CPU_readout',attempts);save_comparison(np,core,out,run,records);budget.sample('after_CPU_readout',attempts)
   files.extend([out/(run['label']+'_readout.npz'),out/(run['label']+'_summary.json')]);del records
  need(attempts==1680,'exact1680 prefixes')
  emit(out/'probe_complete.json',dict(status='CONDITION_PROBE_COMPLETE_PENDING_FREEZE_AUDIT',prefixes=1680,model_evidence=evidence,backward=0,optimizer_steps=0,dense_forwards=0,BNCal=0,formal_gate=False))
  return files+[out/'prefix_attempts.jsonl',out/'tensor_manifest.jsonl',out/'probe_complete.json',budget.path]
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',prefix_attempts=attempts,error=repr(exc),automatic_retry=False));raise

def main():
 parser=argparse.ArgumentParser()
 for k in ['request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256']:parser.add_argument('--'+k,required=True)
 args=parser.parse_args()
 def rec(p,h):return dict(path=p,bytes=clean(p).stat().st_size,sha256=h)
 qr=rec(args.request,args.request_sha256);q=authorize(qr,rec(args.authorization,args.authorization_sha256),rec(args.runtime,args.runtime_sha256))
 I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
 need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
 need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'container/python')
 need(Path(__file__).resolve()==exact(q['entry']),'entry hash')
 parent_cmd=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0');need(parent_cmd[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s',str(q['limits']['wall_seconds'])+'s'],'external bounded timeout')
 need(json.loads(clean(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single attempt claim')
 parent=load_module('condition_frozen_P1_parent',q['parent_entry']);runs,rows=validate_index(bound(q['input_index']))
 for b in q['implementation'].values():exact(b)
 for b in q['dependencies']:exact(b)
 p3=bound(q['P3']);need(p3['status']=='LOCAL_CONDITION_PROBE_INTEGRATION_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'final P3')
 for run in runs:exact(run['checkpoint'])
 scope=bound(q['preflight_scope']);static=bound(q['static_config']);helper=parent.module('condition_helper',q['helper']);helper._MONITOR=None;records=helper.source_map(scope)
 for rel,b in records.items():helper.exact(root/rel,b['sha256'],b['bytes'])
 helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
 for b in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(b['path'],b['sha256'],b['bytes'])
 bound(q['numeric_policy'])
 for key,value in q['environment'].items():need(os.environ.get(key)==value.replace('<owned_output>',str(out)),'environment '+key)
 smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')];need(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'device/idle')
 need(out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2'),'output boundary')
 if out.exists():need({p.name for p in out.iterdir()}=={'launch.log'},'new output')
 else:out.mkdir()
 (out/'features').mkdir();(out/'tmp').mkdir();(out/'worker.pid').write_text(str(os.getpid()))
 timezone=parent.module('condition_exact_UTC',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE);source_guard=parent.ExactSourceReads(q['implementation'])
 try:
  envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
  sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
  helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
  payloads=[out/'features'/(r['run']+'__'+r['case_id']+'.npz') for r in rows]+[out/(r['label']+'_readout.npz') for r in runs]
  policy=parent.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows],[r['checkpoint']['path'] for r in runs],payloads,utc,source_guard);sys.addaudithook(policy.audit)
  import numpy as np
  import torch,timm,yaml,importlib
  from easydict import EasyDict
  need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions');need(torch.cuda.is_available() and torch.cuda.device_count()==1,'one visible CUDA');torch.cuda.set_device(0);helper.configure_numeric(torch)
  chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');native=importlib.import_module('pointnet2_ops._ext');need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(native.__file__).resolve())==scope['bindings']['provider'][2]['path'],'provider origins');helper.check_backend(chamfer,pn,pm)
  transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr;need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'static baseline config');transformer.enable_bcsp_knn()
  factory=parent.load_p1_factory(q['implementation']);need(Path(sys.modules['bcsp_mamba_encoder_v1'].__file__).resolve()==exact(q['implementation']['encoder']),'encoder origin')
  capture=load_module('condition_prefix_capture',q['capture']);core=load_module('condition_readout_core',q['core'])
  def builder(run):return factory.build_model(lambda:model_class(EasyDict(static['model'])),run['variant'],seed=0)
  budget=parent.Budget(q,out,torch,helper);files=execute(torch,np,parent,helper,capture,core,runs,rows,out,budget,builder)
  archive=parent.pack(out,files);emit(out/'completion.json',dict(status='CONDITION_PROBE_ARCHIVED_PENDING_FREEZE_AUDIT',prefixes=1680,archive=archive,request_sha256=qr['sha256']))
 except BaseException as exc:
  if not (out/'failure.json').exists():emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
  raise
 finally:source_guard.close();utc.close()
if __name__=='__main__':main()
