"""Four frozen B0 models,420 native development predictions. No training/BNCal CLI."""
import argparse,gc,hashlib,importlib.util,json,os,random,shutil,socket,subprocess,sys,tarfile,time
from pathlib import Path

def require(ok,text):
 if not ok:raise RuntimeError(text)
def clean(p):
 p=Path(p).absolute()
 require(not any(x.is_symlink() for x in (p,*p.parents)),'symlink: '+str(p))
 require(not ({'.ssh','.aws','.credentials','.git'}&set(p.parts)) and p.name not in {'.env','.netrc'},'secret path')
 return p
def sha(p):
 h=hashlib.sha256()
 with clean(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def exact(r):
 p=clean(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'file identity: '+str(p));return p
def bound(r):return json.loads(exact(r).read_bytes())
def emit(p,x):
 with clean(p).open('x',encoding='ascii') as f:json.dump(x,f,indent=2,allow_nan=False)
def authorize(qr,ar,rr):
 q=bound(qr);a=bound(ar);r=bound(rr)
 require(q['schema']=='bcsp-four-model-development-prediction-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','request type/status')
 require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and
  a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate authorization')
 require(r==dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime binding')
 return q
def validate_index(index,folds):
 runs=index['runs'];rows=index['inputs']
 require(len(runs)==4 and len(rows)==420 and {r['label'] for r in runs}=={'C_8192','C_16384','D_8192','D_16384'},'four runs/420 forwards')
 require(set(folds['folds']['C']['dev_sources']).isdisjoint(folds['folds']['D']['dev_sources']),'unique OOF sources')
 for run in runs:
  fold=folds['folds'][run['fold']];part=[r for r in rows if r['run']==run['label']]
  require(run['label']==run['fold']+'_'+str(run['n_input']) and run['n_input'] in (8192,16384),'arm label')
  require(len(part)==105 and [r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'exact ordered dev identities')
  require(run['train_sources']==fold['train_sources'] and run['dev_sources']==fold['dev_sources'] and not set(run['dev_sources'])&set(run['train_sources']),'own-fold source exclusion')
  require(len(set(r['case_id'] for r in part))==105 and len(set(r['source_id'] for r in part))==21,'105cases/21sources')
  for row in part:
   require(row['fold']==run['fold'] and row['n_input']==run['n_input'] and row['source_id'] in run['dev_sources'],'row arm/source')
   require(row['case_id'].startswith('train__') and row['source_id']=='train:'+row['case_id'].split('__')[1],'case source identity')
   other='foldd' if run['fold']=='C' else 'foldc'
   root='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_'+other+'_'+str(run['n_input'])+'_seed0_v1/points/'
   require(row['input']['path'].startswith(root) and Path(row['input']['path']).name==row['case_id']+'_'+str(run['n_input'])+'.npz','exact opposite-fold point location')
 return runs,rows
def load_partial(np,row):
 p=exact(row['input'])
 with np.load(p,allow_pickle=False) as z:x=z['partial'].copy()
 require(x.shape==(row['n_input'],3) and x.dtype==np.float32 and np.isfinite(x).all(),'partial tensor contract')
 return x
def load_checkpoint(torch,model,record):
 data=torch.load(exact(record),map_location='cpu',weights_only=True)
 require(isinstance(data,dict) and data.get('stage')=='BCSP_INPUT_DENSITY_V1' and data.get('epoch')==99 and data.get('updates')==3900,'final frozen checkpoint metadata')
 model.load_state_dict(data['base_model'],strict=True)
 del data;gc.collect()
def predict_once(torch,model,x):
 require(not model.training and not any(m.training for m in model.modules()),'eval mode required')
 with torch.inference_mode():
  result=model(x)
  require(isinstance(result,(tuple,list)) and len(result)==2,'native eval output tuple')
  dense=result[1]
  require(tuple(dense.shape)==(1,8192,3) and dense.dtype==torch.float32 and bool(torch.isfinite(dense).all()),'8192 finite FP32 output')
  return dense.detach().cpu().numpy().copy()
def make_policy(helper,roots,output,inputs,checkpoints,predictions):
 allowed_read={clean(p) for p in inputs+checkpoints};allowed_write={clean(p) for p in predictions}
 class Policy(helper.FilePolicy):
  def check(self,filename,write=False):
   if isinstance(filename,int):return
   p=clean(os.fsdecode(filename))
   if p.suffix.lower() in helper.PAYLOAD or p.name.lower().endswith('.nii.gz'):
    require(p in allowed_write if write else p in allowed_read or p in allowed_write,'non-allowlisted evaluation payload: '+str(p));return
   return super().check(filename,write)
 return Policy(roots,output)
class Budget:
 def __init__(self,q,out,torch,helper):
  self.q,self.out,self.t,self.h=q,Path(out),torch,helper;self.start=time.monotonic()
  self.path=self.out/'resources.jsonl';self.path.open('x').close()
 def sample(self,label,count):
  L=self.q['limits'];t=self.t
  status=Path('/proc/'+str(os.getpid())+'/status').read_text()
  rss=int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:')))*1024
  size=sum(p.stat().st_size for p in self.out.rglob('*') if p.is_file())
  used=int(self.h.smi('memory.used')[0]);err=None
  try:pids=self.h.smi('pid',True)
  except Exception as exc:pids=None;err=repr(exc)[:512]
  elapsed=time.monotonic()-self.start
  values=dict(RSS_bytes=rss,output_bytes=size,device_MiB=used,peak_allocated=t.cuda.max_memory_allocated(0),peak_reserved=t.cuda.max_memory_reserved(0),elapsed_seconds=elapsed,free_disk_bytes=shutil.disk_usage(self.out).free)
  checks=dict(RSS=rss<=L['RSS_bytes'],output=size<=L['output_bytes'],device=used<=L['device_MiB'],allocated=values['peak_allocated']<=L['torch_peak_bytes'],reserved=values['peak_reserved']<=L['torch_peak_bytes'],wall=elapsed<=L['wall_seconds'],disk=values['free_disk_bytes']>=L['minimum_free_disk_bytes'])
  event=dict(phase=label,forwards=count,values=values,checks=checks,failed_checks=[k for k,v in checks.items() if not v],SMI_PIDs=pids,container_PID=os.getpid(),PID_query_error=err,PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE')
  with self.path.open('a') as f:f.write(json.dumps(event)+'\n');f.flush();os.fsync(f.fileno())
  require(all(checks.values()),'resource limit: '+repr(event['failed_checks']))
def module(name,record):
 p=exact(record);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def pack(out,files):
 records=[dict(name=str(p.relative_to(out)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
 archive=out/'development_predictions_v1.tar.gz'
 with archive.open('xb') as raw:
  with tarfile.open(fileobj=raw,mode='w:gz') as tar:
   for p in files:tar.add(p,arcname=str(p.relative_to(out)).replace('\\','/'),recursive=False)
 for suffix,text in [('sha256',sha(archive)+'  '+archive.name+'\n'),('bytes',str(archive.stat().st_size)+'\n'),('contents.sha256',''.join(r['sha256']+'  '+r['name']+'\n' for r in records))]:
  with (out/(archive.name+'.'+suffix)).open('x') as f:f.write(text)
 return dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=records)
def main():
 parser=argparse.ArgumentParser()
 for k in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+k,required=True)
 args=parser.parse_args()
 def r(p,s):return dict(path=p,bytes=clean(p).stat().st_size,sha256=s)
 qr=r(args.request,args.request_sha256);q=authorize(qr,r(args.authorization,args.authorization_sha256),r(args.runtime,args.runtime_sha256))
 I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
 require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
 require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'container/Python identity')
 require(Path(__file__).resolve()==exact(q['entry']),'entry binding')
 parent=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
 require(parent[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s',str(q['limits']['wall_seconds'])+'s'],'external timeout')
 marker=json.loads(clean(q['launch_attempt']).read_bytes())
 require(marker==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single-use launch claim')
 index=bound(q['input_index']);runs,rows=validate_index(index,bound(q['fold_binding']))
 static=bound(q['static_config']);scope=bound(q['preflight_scope']);helper=module('bcsp_eval_frozen_helper',q['helper']);helper._MONITOR=None
 records=helper.source_map(scope)
 for rel,rec in records.items():helper.exact(root/rel,rec['sha256'],rec['bytes'])
 helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
 for rec in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(rec['path'],rec['sha256'],rec['bytes'])
 for key,value in q['environment'].items():require(os.environ.get(key)==value.replace('<owned_output>',str(out)),'environment: '+key)
 smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
 require(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256 and not helper.smi('pid',True),'GPU identity/idle gate')
 require(out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1'),'output root')
 if out.exists():require({p.name for p in out.iterdir()}=={'launch.log'},'fresh output')
 else:out.mkdir()
 (out/'predictions').mkdir();(out/'tmp').mkdir()
 with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
 forwards=0;successful=0
 try:
  envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
  sys.path[:0]=[str(provider),str(envroot/'lib/python3.10/site-packages')]
  helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
  predictions=[out/'predictions'/(row['run']+'__'+row['case_id']+'.npz') for row in rows]
  policy=make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows],[r['checkpoint']['path'] for r in runs],predictions)
  sys.addaudithook(policy.audit)
  import numpy as np
  import torch,timm,yaml
  from easydict import EasyDict
  import importlib
  require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
  require(torch.cuda.is_available() and torch.cuda.device_count()==1,'one visible CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
  chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');provider_m=importlib.import_module('pointnet2_ops.pointnet2_utils');native=importlib.import_module('pointnet2_ops._ext')
  require(str(Path(provider_m.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(native.__file__).resolve())==scope['bindings']['provider'][2]['path'],'native origins')
  helper.check_backend(chamfer,pn,provider_m)
  transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr
  require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'unchanged model config');transformer.enable_bcsp_knn()
  budget=Budget(q,out,torch,helper);manifest=out/'inference_manifest.jsonl';manifest.open('x').close();model_evidence=[]
  for run in runs:
   random.seed(0);np.random.seed(0);torch.manual_seed(0)
   model=model_class(EasyDict(static['model']));helper.validate_model(model);load_checkpoint(torch,model,run['checkpoint']);model.eval();model.to('cuda:0')
   torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0);before=helper.state_sha(model)
   rng_before=helper.tensor_sha(torch.get_rng_state());budget.sample('model_start:'+run['label'],forwards)
   selected=[(row,p) for row,p in zip(rows,predictions) if row['run']==run['label']]
   for row,path in selected:
    helper.assert_numeric(torch);budget.sample('before_forward',forwards)
    x=torch.from_numpy(load_partial(np,row)).unsqueeze(0).to('cuda:0');start=time.monotonic()
    forwards+=1
    y=predict_once(torch,model,x);torch.cuda.synchronize();successful+=1
    with path.open('xb') as f:np.savez_compressed(f,prediction=y[0])
    event=dict(run=run['label'],case_id=row['case_id'],source_id=row['source_id'],fold=run['fold'],n_input=run['n_input'],n_output=8192,input_sha256=row['input']['sha256'],checkpoint_sha256=run['checkpoint']['sha256'],prediction=dict(name='predictions/'+path.name,bytes=path.stat().st_size,sha256=sha(path)),forward_index=forwards,operational_seconds=time.monotonic()-start)
    with manifest.open('a') as f:f.write(json.dumps(event)+'\n');f.flush()
    del x,y;helper.assert_numeric(torch);budget.sample('after_forward',forwards)
   after=helper.state_sha(model);require(before==after,'model parameters/BN state changed')
   model_evidence.append(dict(run=run['label'],forwards=len(selected),state_before=before,state_after=after,CPU_rng_before=rng_before,CPU_rng_after=helper.tensor_sha(torch.get_rng_state()),mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0))
   del model;gc.collect();torch.cuda.empty_cache()
  require(forwards==420,'exact420 forwards');budget.sample('all_complete',forwards)
  done=out/'inference_complete.json';emit(done,dict(status='FOUR_MODEL_420_FORWARD_COMPLETE',forwards=420,models=model_evidence,training_updates=0,BNCal=0,loss=0,backward=0,request_sha256=qr['sha256']))
  archive=pack(out,predictions+[manifest,done,budget.path]);emit(out/'completion.json',dict(status='PREDICTIONS_ARCHIVED_AWAITING_LOCAL_SCORING',forwards=420,archive=archive,request_sha256=qr['sha256']))
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',forward_attempts=forwards,valid_forward_returns=successful,error=repr(exc),training_updates=0,BNCal=0));raise

if __name__=='__main__':main()
