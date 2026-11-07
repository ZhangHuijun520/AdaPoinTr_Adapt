"""P1 T0/M0 frozen final models, 210 native development predictions. No training/BNCal CLI."""
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
 require(q['schema']=='bcsp-p1-foldD-paired-development-prediction-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['fold']=='D','request type/status')
 require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and
  a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate authorization')
 require(r==dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime binding')
 return q
DEVELOPMENT_DATA_ROOT='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points'

def validate_index(index,folds):
 runs=index['runs'];rows=index['inputs'];fold=folds['folds']['D']
 require(index['schema']=='bcsp-p1-paired-development-index-v1' and index['status']=='FROZEN_FOR_SEPARATE_EXECUTION_AUTHORIZATION','P1 index identity')
 require(len(runs)==2 and len(rows)==210 and [r['label'] for r in runs]==['D_T0','D_M0'],'two ordered arms/210')
 require(len(fold['dev_case_ids'])==105 and len(set(fold['dev_case_ids']))==105 and len(fold['dev_sources'])==21 and len(fold['train_sources'])==63 and set(fold['dev_sources']).isdisjoint(fold['train_sources']),'source separation')
 for run,variant in zip(runs,['T0','M0']):
  part=[r for r in rows if r['run']==run['label']]
  require(run['variant']==variant and run['fold']=='D' and run['seed']==0 and run['n_input']==run['n_output']==8192,'model identity')
  require([r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'ordered105 cases')
  require(run['train_sources']==fold['train_sources'] and run['dev_sources']==fold['dev_sources'],'source fold binding')
  for row in part:
   require(row['variant']==variant and row['fold']=='D' and row['n_input']==8192 and row['source_id']=='train:'+row['case_id'].split('__')[1] and row['source_id'] in fold['dev_sources'],'row identity')
   require(row['input']['path']==DEVELOPMENT_DATA_ROOT+'/'+row['case_id']+'_8192.npz','existing exact input path');clean(row['input']['path'])
   n=row['normalization'];require(len(n['center'])==3 and isinstance(n['scale'],(int,float)) and n['scale']>0,'D-only normalization')
 for a,b in zip(rows[:105],rows[105:]):
  require(a['run']=='D_T0' and b['run']=='D_M0' and all(a[k]==b[k] for k in ['case_id','source_id','input','normalization','normalization_source','target_array_sha256']),'same input/target/frame')
 require(len({r['input']['path'] for r in rows})==105,'105 unique inputs')
 return runs,rows

def validate_source(index,source,manifest):
 original=[r for r in source['inputs'] if r['run']=='D_8192']
 require(len(original)==105,'original input index')
 records={r['case_id']:r for r in manifest}
 require(len(records)==420 and len(manifest)==420,'unique420 manifest')
 for a,b in zip(index['inputs'][:105],original):
  require(all(a[k]==b[k] for k in ['case_id','source_id','input']),'original V1 input provenance')
  m=records[a['case_id']]
  require(all(a[k]==m[k] for k in ['source_id','normalization','normalization_source','target_array_sha256']) and a['input']['sha256']==m['sha256'],'manifest coordinate/target provenance')

def validate_evidence(q,index):
 receipt=bound(q['pair_receipt'])
 require(receipt['status']=='FROZEN_MATCHED_T0_M0_TRAINING_EVIDENCE' and receipt['common_initialization_exact_equal'] and receipt['exposure_and_drops_exact_equal'] and receipt['shared_parameter_decay_exact_equal'] and receipt['paired_actual_batches']==3900,'paired training receipt')
 for run,key in zip(index['runs'],['T0','M0']):
  audit=bound(q['training_audits'][key])
  require(audit['status']==('FORMAL_P1_T0_POST_TRAINING_FREEZE_AUDIT_PASS' if key=='T0' else 'FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'),'formal training audit')
  require(q['training_audits'][key]['sha256']==run['training_freeze_audit_sha256'],'training audit pin')
  require(receipt[key]['checkpoint']['sha256']==run['checkpoint']['sha256'] and receipt[key]['checkpoint']['bytes']==run['checkpoint']['bytes'],'checkpoint receipt')
 for rec in q['implementation'].values():exact(rec)
 for rec in q['dependencies']:exact(rec)
 bound(q['numeric_policy']);bound(q['protocol'])

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
  coarse,dense=result
  require(tuple(coarse.shape)==(1,256,3) and coarse.dtype==torch.float32 and bool(torch.isfinite(coarse).all()),'256 finite FP32 coarse output')
  require(tuple(dense.shape)==(1,8192,3) and dense.dtype==torch.float32 and bool(torch.isfinite(dense).all()),'8192 finite FP32 output')
  return coarse.detach().cpu().numpy().copy(),dense.detach().cpu().numpy().copy()
class ExactSourceReads:
 """Only two pinned source files; fd verification avoids recursive audit-open."""
 def __init__(self,implementation):
  self.records={};self.fds={}
  try:
   for key in ('factory','encoder'):
    r=dict(implementation[key]);p=exact(r);require(p.suffix=='.py','exact source extension')
    fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));self.records[p]=r;self.fds[p]=fd;self.verify(p)
  except BaseException:
   self.close();raise
 def verify(self,p):
  r=self.records[p];fd=self.fds[p];before=clean(p).stat();opened=os.fstat(fd)
  require((before.st_dev,before.st_ino,before.st_size)==(opened.st_dev,opened.st_ino,r['bytes']),'source replaced/size drift')
  os.lseek(fd,0,os.SEEK_SET);data=os.read(fd,r['bytes']+1)
  require(len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'exact source hash drift')
  after=clean(p).stat();require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'source changed during verification')
 def allow(self,filename,write=False):
  p=clean(os.fsdecode(filename))
  if p not in self.records:return False
  require(not write,'bound source write denied');self.verify(p);return True
 def close(self):
  for fd in self.fds.values():os.close(fd)
  self.fds.clear()

def source_module(name,record):
 # Compile bound .py bytes directly: never consult a neighboring .pyc.
 require(name not in sys.modules,'preloaded source module: '+name)
 p=exact(record);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 try:exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__)
 except BaseException:
  sys.modules.pop(name,None);raise
 return m

def load_p1_factory(implementation):
 source_module('bcsp_mamba_encoder_v1',implementation['encoder'])
 return source_module('p1_frozen_factory',implementation['factory'])

def make_policy(helper,roots,output,inputs,checkpoints,predictions,utc_guard,source_guard):
 allowed_read={clean(p) for p in inputs+checkpoints};allowed_write={clean(p) for p in predictions}
 class Policy(helper.FilePolicy):
  def check(self,filename,write=False):
   if isinstance(filename,int):return
   if utc_guard.allow(filename,write):return
   if source_guard.allow(filename,write):return
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
def append_event(path,event):
 with path.open('a',encoding='ascii') as f:
  f.write(json.dumps(event,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def geometry_summary(np,coarse,dense):
 c=coarse[0].astype('float64');d=dense[0].astype('float64')
 def stats(x):
  mean=x.mean(0);z=x-mean
  return dict(centroid=mean.tolist(),bbox_min=x.min(0).tolist(),bbox_max=x.max(0).tolist(),radius_gyration=float(np.sqrt((z*z).sum(1).mean())),covariance_eigenvalues=np.linalg.eigvalsh(z.T@z/len(x)).tolist())
 offsets=d.reshape(256,32,3)-c[:,None,:]
 return dict(frame='native_D_only_normalized_no_GT',coarse=stats(c),dense=stats(d),mean_dense_minus_coarse=offsets.mean((0,1)).tolist(),offset_mean_squared_radius=float((offsets**2).sum(2).mean()))

def rng_state(torch,np,helper,cuda):
 return dict(CPU=helper.tensor_sha(torch.get_rng_state()),CUDA=helper.tensor_sha(torch.cuda.get_rng_state(0)) if cuda else None,Python=repr(random.getstate()),numpy=repr(np.random.get_state()[0])+np.random.get_state()[1].tobytes().hex()+repr(np.random.get_state()[2:]))

def execute_pair(torch,np,helper,runs,rows,out,budget,builder,representatives,device='cuda:0'):
 # Production only calls with cuda:0. CPU device is used solely by artificial tests.
 cuda=device=='cuda:0';attempts=successful=0;model_evidence=[];predictions=[]
 manifest=out/'inference_manifest.jsonl';journal=out/'forward_attempts.jsonl';geometry=out/'geometry_summary.jsonl'
 for p in (manifest,journal,geometry):p.open('x').close()
 try:
  for run in runs:
   random.seed(0);np.random.seed(0);torch.manual_seed(0)
   model,construction=builder(run);helper.validate_model(model)
   require(construction['variant']==run['variant'] and construction['replaced_global_branches']==(6 if run['variant']=='M0' else 0) and construction['common_state_unchanged'] and not construction['artificial_fixture'],'factory identity')
   load_checkpoint(torch,model,run['checkpoint']);model.eval();model.to(device)
   if cuda:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
   before=helper.state_sha(model);rng_before=rng_state(torch,np,helper,cuda);budget.sample('model_start:'+run['label'],attempts)
   selected=[row for row in rows if row['run']==run['label']]
   for row in selected:
    helper.assert_numeric(torch);budget.sample('before_forward',attempts)
    x=torch.from_numpy(load_partial(np,row)).unsqueeze(0).to(device);start=time.monotonic()
    require(attempts<210,'forward budget exhausted');attempts+=1
    append_event(journal,dict(forward_index=attempts,run=run['label'],case_id=row['case_id'],status='CLAIMED_BEFORE_FORWARD'))
    coarse,dense=predict_once(torch,model,x)
    if cuda:torch.cuda.synchronize()
    successful+=1
    path=out/'predictions'/(run['label']+'__'+row['case_id']+'.npz')
    with path.open('xb') as f:
     arrays=dict(prediction=dense[0])
     if row['case_id'] in representatives:arrays['coarse']=coarse[0]
     np.savez_compressed(f,**arrays)
    predictions.append(path)
    append_event(geometry,dict(run=run['label'],case_id=row['case_id'],**geometry_summary(np,coarse,dense)))
    append_event(manifest,dict(run=run['label'],variant=run['variant'],case_id=row['case_id'],source_id=row['source_id'],fold='D',n_input=8192,n_output=8192,input_sha256=row['input']['sha256'],checkpoint_sha256=run['checkpoint']['sha256'],normalization=row['normalization'],prediction=dict(name='predictions/'+path.name,bytes=path.stat().st_size,sha256=sha(path)),forward_index=attempts,operational_seconds=time.monotonic()-start))
    del x,coarse,dense;helper.assert_numeric(torch);budget.sample('after_forward',attempts)
   after=helper.state_sha(model);rng_after=rng_state(torch,np,helper,cuda)
   require(before==after,'model parameters/BN state changed');require(rng_before==rng_after,'eval RNG state changed')
   model_evidence.append(dict(run=run['label'],forwards=len(selected),state_before=before,state_after=after,RNG_before=rng_before,RNG_after=rng_after,mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0,construction=construction))
   del model;gc.collect()
   if cuda:torch.cuda.empty_cache()
  require(attempts==successful==210,'exact210 forwards');budget.sample('all_complete',attempts)
  return predictions,[manifest,journal,geometry],model_evidence
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',forward_attempts=attempts,valid_forward_returns=successful,error=repr(exc),training_updates=0,BNCal=0));raise

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
 validate_source(index,bound(q['source_index']),[json.loads(line) for line in exact(q['source_manifest']).read_text().splitlines()]);validate_evidence(q,index)
 protocol=bound(q['protocol']);require(protocol['forward_budget']==210 and protocol['BNCal']==0,'prediction protocol')
 timezone=module('p1_exact_utc',q['implementation']['timezone']);utc_guard=timezone.ExactUTCReader(timezone.UTC_RESOURCE)
 static=bound(q['static_config']);scope=bound(q['preflight_scope']);helper=module('bcsp_eval_frozen_helper',q['helper']);helper._MONITOR=None
 records=helper.source_map(scope)
 for rel,rec in records.items():helper.exact(root/rel,rec['sha256'],rec['bytes'])
 helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
 for rec in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(rec['path'],rec['sha256'],rec['bytes'])
 for key,value in q['environment'].items():require(os.environ.get(key)==value.replace('<owned_output>',str(out)),'environment: '+key)
 smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
 require(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'GPU identity/idle gate')
 require(out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1'),'output root')
 if out.exists():require({p.name for p in out.iterdir()}=={'launch.log'},'fresh output')
 else:out.mkdir()
 (out/'predictions').mkdir();(out/'tmp').mkdir()
 with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
 forwards=0;successful=0;source_guard=None
 try:
  source_guard=ExactSourceReads(q['implementation'])
  envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
  sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
  helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
  predictions=[out/'predictions'/(row['run']+'__'+row['case_id']+'.npz') for row in rows]
  policy=make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows],[r['checkpoint']['path'] for r in runs],predictions,utc_guard,source_guard)
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
  factory=load_p1_factory(q['implementation'])
  require(Path(sys.modules['bcsp_mamba_encoder_v1'].__file__).resolve()==exact(q['implementation']['encoder']),'encoder origin')
  def builder(run):return factory.build_model(lambda:model_class(EasyDict(static['model'])),run['variant'],seed=0)
  budget=Budget(q,out,torch,helper)
  predictions,extra,model_evidence=execute_pair(torch,np,helper,runs,rows,out,budget,builder,protocol['coarse_tensor_cases'])
  done=out/'inference_complete.json';emit(done,dict(status='P1_PAIR_210_FORWARD_COMPLETE',forwards=210,models=model_evidence,training_updates=0,BNCal=0,loss=0,backward=0,request_sha256=qr['sha256']))
  archive=pack(out,predictions+extra+[done,budget.path]);emit(out/'completion.json',dict(status='PREDICTIONS_ARCHIVED_AWAITING_LOCAL_SCORING',forwards=210,archive=archive,request_sha256=qr['sha256']))

 except BaseException as exc:
  if not (out/'failure.json').exists():emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),training_updates=0,BNCal=0))
  raise
 finally:
  if source_guard is not None:source_guard.close()
  utc_guard.close()

if __name__=='__main__':main()
