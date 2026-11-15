"""SCQ B/S C/D: exactly630 Native forwards. Inert import; separate exact-hash authorization."""
import argparse,gc,hashlib,importlib.util,json,os,random,shlex,shutil,socket,subprocess,sys,tarfile,time
from pathlib import Path,PurePosixPath
from collections import Counter

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

def load_partial(np,row):
 p=exact(row['input'])
 with np.load(p,allow_pickle=False) as z:x=z['partial'].copy()
 require(x.shape==(row['n_input'],3) and x.dtype==np.float32 and np.isfinite(x).all(),'partial tensor contract')
 return x

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
 """Four exact pinned source files; fd verification avoids recursive audit-open."""
 def __init__(self,implementation):
  self.records={};self.fds={}
  try:
   for key in ('encoder','factory','lqi_decoder','lqi_factory'):
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

INITIALIZATION={'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin', 'bytes': 2784780, 'sha256': 'e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416'}
TRAINING_IDENTITY={'hostname': 'shu-common-25721452-notebook-t6ibfm-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '570.190', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}
CURRENT_IDENTITY={'hostname': 'shu-common-25721452-notebook-qx2k0r-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-383d118a-368c-94e3-166a-cad3efab8fd7', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '570.190', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}
REBIND_SHA='bd77f417c1a1c6212d7e2b9f9b43138670296f6c183e4639edd2b8137583b6e9'
INDEX_SHA='527f4447c953f575bbdf92c2ee935cfa2d13d6081345c71694c49aefbc9c9183'
PROTOCOL_SHA='26a211772a72728d298b3d1f9847df688d5321b40957fe19c7fae2441d34ff9e'
SELECTION_SHA='2c09e5bf53ae44ab66f14afc4a235d49c1d17a7d2ffa2899ad1ed53e7c6925cd'
DATA_ROOTS={'C': '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points', 'D': '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points'}
PINS={'encoder': '5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8', 'factory': '59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4', 'lqi_decoder': '92a52949ec037edd13bac7bfae7395bfafad84c5ffc204e1d178ea1f68507ea8', 'lqi_factory': '56d4cbe89660106f255a0d58e28c7cbaf38374c7788219d5a21779bd97aaf106', 'scq_residual': '2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404', 'scq_factory': 'fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5', 'rf_residual': 'c50cbdb0986fafe3ff2309ef8c02d74fdc5e651218c71f4bb13a87bacefc726a', 'rf_factory': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570', 'timezone': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e', 'cuda_entry': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}
FROZEN_MODELS={'Sref_C': {'fold': 'C', 'variant': 'S', 'checkpoint': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/ckpt-last.pth', 'bytes': 487148386, 'sha256': '10502e41cd089d50b905a99bce272cee61323180c2299cc02f9f3132c012e1a5'}, 'request_sha256': '6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88', 'audit_sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149', 'audit_status': 'FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS', 'identity': {'hostname': 'shu-common-25721452-notebook-zbpgzu-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '575.51.03', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}}, 'Static_C': {'fold': 'C', 'variant': 'RF-Static', 'checkpoint': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': '237ecd116dc8fccbfd4c0814e3ab17ff4b5fb835601de97b1e131c5c493d0a52'}, 'request_sha256': 'a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f', 'audit_sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab', 'audit_status': 'FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS', 'identity': {'hostname': 'shu-common-25721452-notebook-zbpgzu-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '575.51.03', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}}, 'Requery_C': {'fold': 'C', 'variant': 'RF-Requery', 'checkpoint': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldC_seed0_train_20261114_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': '4816c8768da60de7c8153fcd0793524b2fb3c1dddba04de9cdf0c6eb13f2602b'}, 'request_sha256': '27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497', 'audit_sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56', 'audit_status': 'FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS', 'identity': {'hostname': 'shu-common-25721452-notebook-zbpgzu-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '575.51.03', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}}, 'Sref_D': {'fold': 'D', 'variant': 'S', 'checkpoint': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/ckpt-last.pth', 'bytes': 487148386, 'sha256': 'f9c9190ea29750caf49e3d6b6c545a3e8b5912a8b6ec8fced043dafde215cc43'}, 'request_sha256': '888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d', 'audit_sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd', 'audit_status': 'FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS', 'identity': {'hostname': 'shu-common-25721452-notebook-zbpgzu-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '575.51.03', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}}, 'Static_D': {'fold': 'D', 'variant': 'RF-Static', 'checkpoint': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v2/ckpt-last.pth', 'bytes': 489927058, 'sha256': 'c2acf8d8f8587db465e0f46dacb14cc25f10a585c3573ff7521c8eceb75bab93'}, 'request_sha256': '9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b', 'audit_sha256': '100770541377b1473c9cb8610375c9e2de336cb702e60189cb0ffb68194f2697', 'audit_status': 'FORMAL_RF_STATIC_D_TRAINING_PAIR_FREEZE_AUDIT_PASS', 'identity': {'hostname': 'shu-common-25721452-notebook-qx2k0r-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-383d118a-368c-94e3-166a-cad3efab8fd7', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '570.190', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}}, 'Requery_D': {'fold': 'D', 'variant': 'RF-Requery', 'checkpoint': {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': '068288d4beb237dfe820286e22e122a5f427e4e32846c63087320aabc5b25bba'}, 'request_sha256': '4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed', 'audit_sha256': '51cfba6ead7ab7d15fe3b2fd2fd7463fa6105084fd9a76fb2071d115a6c66cb4', 'audit_status': 'FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS', 'identity': {'hostname': 'shu-common-25721452-notebook-zbpgzu-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '575.51.03', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}}}
LIMITS=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)

RF_INITIALIZATION={'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}
QUALIFICATION={'C_pair': 'SAME_DEVICE_PRIMARY_MECHANISM_EVIDENCE', 'D_Static_vs_Requery': 'DEVICE_AND_DRIVER_CONFOUNDED_SUPPLEMENTARY_EVIDENCE', 'strict_same_device_D_pair': False, 'do_not_attribute_all_differences_to_requery': True}

def authorize(qr,ar,rr):
 q,a,r=bound(qr),bound(ar),bound(rr)
 require(q['schema']=='bcsp-scq-rf-sixmodel-native-prediction-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'request type/status')
 require(q['forward_budget']==630 and q['batch_size']==1 and q['unique_cases']==210 and all(q[k]==0 for k in ('backward','optimizer_steps','BNCal','loss_calls','warmup','TTA')),'Native630 only')
 require(q['limits']==LIMITS and q['identity']==CURRENT_IDENTITY and q['environment']['CUDA_VISIBLE_DEVICES']==CURRENT_IDENTITY['gpu_uuid'],'current identity/resources')
 require(q['input_index']['sha256']==INDEX_SHA and q['protocol']['sha256']==PROTOCOL_SHA and q['scope_origin']=='EXACT_FROZEN_SCQ_RF_SIX_DEVELOPMENT_RUNS_NO_RESELECTION','frozen scope')
 require(q['comparison_qualification']==QUALIFICATION,'accepted D device confound disclosure')
 require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate explicit authorization')
 require(r==dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
 return q


def validate_index(index,folds,selection=None):
 require(index['schema']=='bcsp-scq-rf-sixmodel-native-index-v1','index schema')
 runs,rows=index['runs'],index['inputs'];require([r['label'] for r in runs]==['Sref_C', 'Static_C', 'Requery_C', 'Sref_D', 'Static_D', 'Requery_D'] and len(rows)==630,'four ordered runs420')
 for run in runs:
  pin=FROZEN_MODELS[run['label']];f=pin['fold'];fold=folds['folds'][f];part=[r for r in rows if r['run']==run['label']]
  require(run['fold']==f and run['variant']==pin['variant'] and run['seed']==0 and run['n_input']==run['n_output']==8192,'model identity')
  require(run['checkpoint']==pin['checkpoint'] and run['training_request']['sha256']==pin['request_sha256'] and run['training_audit']['sha256']==pin['audit_sha256'],'frozen model pins')
  require(len(part)==105 and [r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'ordered105')
  require(run['train_sources']==fold['train_sources'] and run['dev_sources']==fold['dev_sources'] and len(set(fold['dev_sources']))==21 and len(set(fold['train_sources']))==63 and not set(fold['dev_sources'])&set(fold['train_sources']),'source split')
  require(set(Counter(r['source_id'] for r in part).values())=={5} and set(r['source_id'] for r in part)==set(fold['dev_sources']),'five defects/source')
  for row in part:
   cid=row['case_id'];require(row['variant']==run['variant'] and row['fold']==f and row['n_input']==row['n_output']==8192 and row['source_id']=='train:'+cid.split('__')[1] and row['defect_type']==cid.split('__',2)[2] and row['defect_type'] in {'bilateral','frontoorbital','parietotemporal','random_1','random_2'},'row identity')
   require(row['input']['path']==DATA_ROOTS[f]+'/'+cid+'_8192.npz' and row['prediction_filename']=='predictions/'+run['label']+'__'+cid+'.npz','exact paths')
   require(row['save_coarse'] is row['save_Qraw'] is True and row['cache_context'] is row['save_full_decoder_trace'] is False,'all Qraw/Qused/P no trace')
   clean(row['input']['path']);n=row['normalization'];require(row['normalization_source']=='defective_bbox' and len(n['center'])==3 and all(isinstance(x,(int,float)) and abs(x)<1e6 for x in n['center']) and 0<n['scale']<1e6,'D-only frame')
 require(len({(r['run'],r['case_id']) for r in rows})==630 and len({r['input']['path'] for r in rows})==210,'unique paths')
 require(not set(folds['folds']['C']['dev_sources'])&set(folds['folds']['D']['dev_sources']),'disjoint folds')
 for f in 'CD':
  parts=[[r for r in rows if r['run']==a+'_'+f] for a in ('Sref','Static','Requery')]
  require(all(all(x[k]==y[k]==z[k] for k in ('case_id','source_id','input','normalization')) for x,y,z in zip(*parts)),'three arms paired identical inputs')
 return runs,rows



def validate_source(index,source,manifest):
 records={r['case_id']:r for r in manifest};require(len(records)==len(manifest)==420,'original420 manifest')
 for row in index['inputs']:
  m=records[row['case_id']]
  require(all(row[k]==m[k] for k in ('source_id','normalization','normalization_source')) and row['input']['sha256']==m['sha256'],'input provenance')


def validate_evidence(q,index):
 require(set(q['training_audits'])==set(FROZEN_MODELS),'six audit records')
 for run in index['runs']:
  pin=FROZEN_MODELS[run['label']];r=q['training_audits'][run['label']]
  require(r['sha256']==pin['audit_sha256'],'audit pin');a=bound(r)
  require(a['status']==pin['audit_status'] and a['variant']==pin['variant'] and a['fold']==pin['fold'] and a['identity']==pin['identity'] and a['request_sha256']==pin['request_sha256'],'formal historical freeze identity')
  require(a['check_count']==len(a['checks'])>0 and all(a['checks'].values()),'formal audit checks')
  require(a['checkpoint']=={k:run['checkpoint'][k] for k in ('bytes','sha256')} and (a['updates'],a['traversals'],a['exposures'],a['drops'])==(3900,100,31200,300) and not any(a[k] for k in ('BNCal','evaluation','resume')),'checkpoint and counts')
 for k,h in PINS.items():require(q['implementation'][k]['sha256']==h,'implementation pin '+k)
 for r in q['implementation'].values():exact(r)
 for r in q['dependencies']:exact(r)
 require(q['initialization']==INITIALIZATION and q['rf_initialization']==RF_INITIALIZATION,'frozen initializer records')
 exact(q['initialization']);exact(q['rf_initialization']);exact(q['entry']);bound(q['numeric_policy'])
 admission=bound(q['prior_native_admission']['audit'])
 require(admission['status']=='FORMAL_RF_POST_CUDA_FREEZE_AUDIT_PASS' and all(admission['checks'].values()),'historical admitted implementation; no current-device equivalence claim')
 p=bound(q['protocol']);require(p['inference']['forward_attempt_budget']==630 and p['numeric']['repeat_GPU_preflight'] is False and p['outputs']['context_caches']==p['outputs']['full_decoder_traces']==0 and p['comparison_qualification']==QUALIFICATION,'Native scope')
 p3=bound(q['P3']);require(p3['status']=='LOCAL_RF_NATIVE_PREDICTION_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'] and all(p3['checks'].values()),'final P3')



def load_scq_builder(implementation):
 for name,key in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_scq_residual_v1','scq_residual')]:source_module(name,implementation[key])
 scq=source_module('bcsp_scq_factory_v1',implementation['scq_factory'])
 source_module('bcsp_scq_rf_residual_v1',implementation['rf_residual'])
 rf=source_module('bcsp_scq_rf_factory_v1',implementation['rf_factory'])
 return dict(scq=scq,rf=rf)



def validate_lqi_model(model,evidence,artificial_cpu=False):
 require(evidence['version']=='F0-LQI-implementation-v1' and evidence['artificial_fixture'] is artificial_cpu and evidence['new_mamba_mixers']==16 and evidence['shared_coordinate_pe_parameters']==1152 and evidence['common_initialization_preserved'],'F0 construction')
 require(evidence['variant']=='F0-LQI-v1' and evidence['conditional_sequence']=='query_aligned_local_memory_interleaving' and evidence['trace_prefix_suffix_semantics']=='interleaved conditional query-position output' and evidence['additional_learned_parameters']==0,'LQI semantics')
 require(evidence['parent']['variant']=='M0' and evidence['parent']['replaced_global_branches']==6 and evidence['parent']['common_state_unchanged'],'parent initialization')
 require(evidence['inventory']['forbidden_registered_modules']==[],'no registered attention')
 require(model.num_query==256 and model.num_points==8192 and model.factor==32 and model.decoder_type=='fc' and model.denoise_weight==0 and model.fine_coverage_weight==1 and model.fine_local_weight==0,'unchanged model')
 b=model.base_model
 require(b.center_num==[512,256] and b.encoder_type=='graph' and b.query_selection=='learned_only' and not b.use_denoise and not b.encoder_adapter.enabled and not model.scqr_contract.enabled,'backbone contract')
 require(all(getattr(model,k) is False for k in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']),'optional objectives disabled')
 require(len(b.decoder.blocks)==8 and not hasattr(model,'h2_range_head') and not hasattr(model,'h2_head'),'eight layers and no H2')
 

def validate_scq_model(model,evidence,artificial_cpu=False,check_total=True):
 validate_lqi_model(model,evidence['parent'],artificial_cpu)
 s=evidence['scq'];variant=s['variant'];require(variant in ('B','S') and s['version']=='SCQ-v2-implementation-v1' and s['common_initialization_preserved'],'SCQ construction')
 require(s['mother_sha256']=='1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4','mother binding')
 require(s['new_parameters']==(0 if variant=='B' else 693507) and hasattr(model.base_model,'scq') is (variant=='S'),'variant modules')
 if not artificial_cpu and check_total:require(s['total_parameters']==sum(p.numel() for p in model.parameters())==(39903169 if variant=='B' else 40596676),'trained parameter count')
 if variant=='S':require(s['initialization_sha256']==INITIALIZATION['sha256'],'initializer evidence')

def validate_model(model,evidence,artificial_cpu=False):
 is_rf='rf' in evidence
 scq=evidence['parent'] if is_rf else evidence
 # SCQ parent records its pre-RF count; total model count is checked below.
 validate_scq_model(model,scq,artificial_cpu,check_total=not is_rf)
 if is_rf:
  require(scq['parent']['artificial_fixture'] is artificial_cpu,'actual RF parent fixture flag')
  rf=evidence['rf'];require(rf['variant'] in ('RF-Static','RF-Requery') and rf['additional_parameters']==231171 and rf['common_state_preserved'] and rf['CPU_RNG_preserved'] and rf['initialization_sha256']==RF_INITIALIZATION['sha256'],'RF construction contract')
  require(hasattr(model.base_model,'rf') and model.base_model.rf.variant==rf['variant'],'actual RF module arm')
  if not artificial_cpu:require(rf['total_parameters']==sum(p.numel() for p in model.parameters())==40827847,'RF exact total count')
 else:require(not hasattr(model.base_model,'rf') and scq['scq']['variant']=='S','Sref unmodified S')


def build_scq_model(factory,legacy_builder,run,initialization,rf_initialization):
 variant=run['variant'];require(variant in ('S','RF-Static','RF-Requery'),'only Sref/Static/Requery')
 if variant=='S':return factory['scq'].build_model(legacy_builder,'S',initialization,seed=0)
 model,evidence=factory['rf'].build_model(legacy_builder,variant,initialization,rf_initialization,seed=0)
 require(evidence['rf']['variant']==variant,'RF builder variant dispatch');return model,evidence


def make_source_guard(implementation,initialization,rf_initialization,extra_read_records=()):
 reader=source_module('scq_native_exact_reader',implementation['cuda_entry'])
 return reader.ExactSCQReads(ExactSourceReads(implementation),[implementation[k] for k in ('scq_residual','scq_factory','rf_residual','rf_factory','cuda_entry','timezone')]+[initialization,rf_initialization]+list(extra_read_records))


def scq_arrays(torch,np,model,coarse):
 info=model.base_model._scq_last_info;require(isinstance(info,dict),'SCQ diagnostic record')
 def array(key):return info[key].detach().cpu().numpy().copy()
 q0=array('Q0');q2=array('Qused');delta=array('delta');rf=hasattr(model.base_model,'rf')
 if rf:q1=array('Q1');d0=array('delta0');d1=array('delta1')
 else:q1=q2.copy();d0=delta.copy();d1=np.zeros_like(delta)
 arrays=dict(Q0=q0,Q1=q1,Q2=q2,delta0=d0,delta1=d1)
 require(all(x.shape==(1,256,3) and x.dtype==np.float32 and np.isfinite(x).all() for x in [q0,q1,q2,delta,d0,d1]),'finite native stage arrays')
 require(np.array_equal(q2,coarse) and np.allclose(q0+d0,q1,rtol=2e-5,atol=2e-6) and np.allclose(q1+d1,q2,rtol=2e-5,atol=2e-6) and np.allclose(q0+delta,q2,rtol=2e-5,atol=2e-6),'native row aligned Q0/Q1/Q2 equations')
 model.base_model._scq_last_info=None
 return q0,delta,arrays,rf



def load_checkpoint(torch,model,run):
 data=torch.load(exact(run['checkpoint']),map_location='cpu',weights_only=True)
 require(isinstance(data,dict) and data.get('stage')=='BCSP_INPUT_DENSITY_V1' and data.get('epoch')==99 and data.get('updates')==3900 and isinstance(data.get('base_model'),dict),'final3900 checkpoint')
 model.load_state_dict(data['base_model'],strict=True)
 del data;gc.collect()

def capture_context(torch,np,trace,coarse,save_layers):
 require(isinstance(trace,dict) and isinstance(trace.get('backbone'),dict),'mother instrumentation record')
 b=trace['backbone'];arrays={}
 for key,field,shape in [('F','encoder_memory',(1,256,384)),('S','encoder_coordinates',(1,256,3)),('z','global_feature',(1,1024)),('Q','coarse',(1,256,3)),('X','query_pre_decoder',(1,256,384))]:
  t=b[field];require(tuple(t.shape)==shape and t.dtype==torch.float32 and bool(torch.isfinite(t).all()),'context '+key)
  arrays[key]=t.detach().cpu().numpy().copy()
 require(np.array_equal(arrays['Q'],coarse) and np.array_equal(trace['coarse_point_cloud'].detach().cpu().numpy(),coarse),'saved Q matches output')
 layers=b['decoder_layers'];require(len(layers)==8,'eight trace layers')
 layer_arrays={}
 for idx,row in enumerate(layers):
  require(row['layer_index']==idx,'layer order')
  for key in ('input','after_self','prefix_suffix','after_cross','output'):
   t=row[key];require(tuple(t.shape)==(1,256,384) and t.dtype==torch.float32 and bool(torch.isfinite(t).all()),'layer tensor '+key)
   if save_layers:layer_arrays['layer_'+str(idx)+'__'+key]=t.detach().cpu().numpy().copy()
 return arrays,layer_arrays

def cache_paths(out,rows):
 return [out/'context'/(r['run']+'__'+r['case_id']+'.npz') for r in rows if r['cache_context']]+[out/'traces'/(r['run']+'__'+r['case_id']+'.npz') for r in rows if r['save_full_decoder_trace']]

def execute_pair(torch,np,helper,runs,rows,out,budget,builder,device='cuda:0',artificial_cpu=False):
 require((device=='cpu') is artificial_cpu,'production CUDA only; CPU fixture explicit')
 cuda=not artificial_cpu;attempts=successful=0;files=[];states=[]
 manifest=out/'inference_manifest.jsonl';journal=out/'forward_attempts.jsonl';geometry=out/'geometry_summary.jsonl';caches=out/'cache_manifest.jsonl'
 for p in (manifest,journal,geometry,caches):p.open('x').close()
 try:
  for run in runs:
   random.seed(0);np.random.seed(0);torch.manual_seed(0)
   model,construction=builder(run);validate_model(model,construction,artificial_cpu)
   load_checkpoint(torch,model,run);model.eval();model.to(device)
   if cuda:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
   model.enable_full_instrumentation(False)
   before=helper.state_sha(model);rng_before=rng_state(torch,np,helper,cuda);budget.sample('model_start:'+run['label'],attempts)
   selected=[r for r in rows if r['run']==run['label']]
   for row in selected:
    helper.assert_numeric(torch);budget.sample('before_forward',attempts)
    x=torch.from_numpy(load_partial(np,row)).unsqueeze(0).to(device);start=time.monotonic()
    require(attempts<630,'forward budget exhausted');attempts+=1
    append_event(journal,dict(forward_index=attempts,run=run['label'],case_id=row['case_id'],status='CLAIMED_BEFORE_FORWARD'))
    model.enable_full_instrumentation(row['cache_context'])
    try:
     coarse,dense=predict_once(torch,model,x)
     trace=model.pop_full_instrumentation()
     if row['cache_context']:
      context,layers=capture_context(torch,np,trace,coarse,row['save_full_decoder_trace'])
      cf=out/'context'/(row['run']+'__'+row['case_id']+'.npz')
      with cf.open('xb') as f:np.savez_compressed(f,**context)
      saved=[cf]
      if row['save_full_decoder_trace']:
       tf=out/'traces'/cf.name
       with tf.open('xb') as f:np.savez_compressed(f,**layers)
       saved.append(tf)
      for p in saved:append_event(caches,dict(run=run['label'],case_id=row['case_id'],name=str(p.relative_to(out)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p),normalization=row['normalization'],input_sha256=row['input']['sha256'],checkpoint_sha256=run['checkpoint']['sha256'],forward_index=attempts,z_definition='backbone.global_feature before query, not rebuild_global_feature'))
      files+=saved;del context,layers,saved
     else:require(trace is None,'unexpected unselected instrumentation')
    finally:
     model.enable_full_instrumentation(False)
    require(model.pop_full_instrumentation() is None and not model.full_instrumentation_enabled and not model.base_model.full_instrumentation_enabled,'instrumentation cleared')
    del trace
    if cuda:torch.cuda.synchronize()
    successful+=1;raw,delta,stages,rf_applicable=scq_arrays(torch,np,model,coarse);path=out/row['prediction_filename']
    with path.open('xb') as f:np.savez_compressed(f,prediction=dense[0],coarse=coarse[0],Qraw=raw[0],delta=delta[0],**{k:v[0] for k,v in stages.items()})
    files.append(path);stats=geometry_summary(np,coarse,dense);stats['Qraw']=geometry_summary(np,raw,dense)['coarse'];stats['delta_mean_norm']=float(np.linalg.norm(delta,axis=-1).mean());stats['delta_max_norm']=float(np.linalg.norm(delta,axis=-1).max())
    stats['RF_second_stage_applicable']=rf_applicable;stats['stage_centroids']={k:v[0].mean(0).tolist() for k,v in stages.items()};stats['coarse']['finite_count']=int(np.isfinite(coarse).all(-1).sum());stats['dense']['finite_count']=int(np.isfinite(dense).all(-1).sum())
    append_event(geometry,dict(run=run['label'],case_id=row['case_id'],**stats))
    append_event(manifest,dict(run=run['label'],variant=run['variant'],case_id=row['case_id'],source_id=row['source_id'],fold=run['fold'],n_input=8192,n_output=8192,input_sha256=row['input']['sha256'],checkpoint_sha256=run['checkpoint']['sha256'],normalization=row['normalization'],prediction=dict(name=row['prediction_filename'],bytes=path.stat().st_size,sha256=sha(path)),forward_index=attempts,operational_seconds=time.monotonic()-start))
    del x,coarse,dense,raw,delta,stages;helper.assert_numeric(torch);budget.sample('after_forward',attempts)
   after=helper.state_sha(model);rng_after=rng_state(torch,np,helper,cuda)
   require(before==after,'parameters/BN state changed');require(rng_before==rng_after,'RNG changed')
   states.append(dict(run=run['label'],forwards=len(selected),state_before=before,state_after=after,RNG_before=rng_before,RNG_after=rng_after,mode='eval_inference_mode',BNCal=0,optimizer=0,backward=0,construction=construction))
   del model;gc.collect()
   if cuda:torch.cuda.empty_cache()
  require(attempts==successful==630 and len(files)==630,'exact630 Native predictions no caches')
  budget.sample('all_complete',attempts)
  return files,[manifest,journal,geometry,caches],states
 except BaseException as exc:
  emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',forward_attempts=attempts,valid_forward_returns=successful,error=repr(exc),training_updates=0,BNCal=0));raise

def render_launcher(q,qsha,asha,rsha):
 for h in (qsha,asha,rsha):require(len(h)==64 and all(c in '0123456789abcdef' for c in h),'full SHA256')
 out=PurePosixPath(q['output']);L=q['launch_contract']
 command=['/usr/bin/timeout','--signal=TERM','--kill-after=5s',str(q['limits']['wall_seconds'])+'s',q['identity']['python_realpath'],'-I','-S','-B',q['entry']['path'],'--request',L['request_path'],'--request-sha256',qsha,'--authorization',L['authorization'],'--authorization-sha256',asha,'--runtime',L['runtime'],'--runtime-sha256',rsha]
 lines=['#!/bin/bash','set -eu','umask 077','cd '+shlex.quote(q['identity']['project'])]
 for p in reversed((out,*out.parents)):
  if str(p)!='/':lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
 lines+=['mkdir -p -- '+shlex.quote(str(out.parent)),'mkdir -- '+shlex.quote(str(out))]
 lines+=['export '+k+'='+shlex.quote(v.replace('<owned_output>',str(out))) for k,v in q['environment'].items()]
 lines+=['set +e',shlex.join(command)+' >'+shlex.quote(L['log'])+' 2>&1','rc=$?','set -e','printf "%s\\n" "$rc" >'+shlex.quote(L['exit_code']),'exit "$rc"']
 require(max(map(len,lines))<=2048,'launcher line bound')
 return '\n'.join(lines)+'\n'

def main():
 parser=argparse.ArgumentParser()
 for k in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+k,required=True)
 args=parser.parse_args()
 def r(p,s):return dict(path=p,bytes=clean(p).stat().st_size,sha256=s)
 qr=r(args.request,args.request_sha256);q=authorize(qr,r(args.authorization,args.authorization_sha256),r(args.runtime,args.runtime_sha256))
 I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
 require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
 require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'current container/Python')
 require(Path.cwd().resolve()==Path(I['project']) and out.parent==Path(I['project'])/'logs/cranial_bcsp_fullmamba','project/output')
 require(Path(__file__).resolve()==exact(q['entry']),'entry binding')
 parent=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
 require(parent[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s'],'external timeout')
 marker=json.loads(clean(q['launch_attempt']).read_bytes());require(marker==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single attempt claim')
 index=bound(q['input_index']);runs,rows=validate_index(index,bound(q['fold_binding']))
 validate_source(index,None,[json.loads(x) for x in exact(q['source_manifest']).read_text().splitlines()]);validate_evidence(q,index)
 timezone=source_module('f0_native_exact_utc',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE)
 source_guard=None
 try:
  static=bound(q['static_config']);scope=bound(q['preflight_scope']);helper=source_module('f0_native_helper',q['helper']);helper._MONITOR=None
  records=helper.source_map(scope)
  for rel,rec in records.items():helper.exact(root/rel,rec['sha256'],rec['bytes'])
  helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
  for rec in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(rec['path'],rec['sha256'],rec['bytes'])
  for row in rows:exact(row['input'])
  for run in runs:exact(run['checkpoint'])
  for k,v in q['environment'].items():require(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment: '+k)
  smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
  require(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'GPU identity/idle')
  require(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'},'fresh launcher-only output')
  for name in ('predictions','context','traces','tmp'):(out/name).mkdir()
  with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
  source_guard=make_source_guard(q['implementation'],q['initialization'],q['rf_initialization'],[q['entry'],q['helper']])
  envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
  sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
  helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
  outputs=[out/row['prediction_filename'] for row in rows]+cache_paths(out,rows)
  policy=make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows],[r['checkpoint']['path'] for r in runs],outputs,utc,source_guard)
  sys.addaudithook(policy.audit)
  import numpy as np
  import torch,timm,yaml,importlib
  from easydict import EasyDict
  require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
  require(torch.cuda.is_available() and torch.cuda.device_count()==1,'one visible CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
  require(torch.version.cuda==I['torch_cuda_version'],'admitted torch CUDA')
  chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');native=importlib.import_module('pointnet2_ops._ext')
  require(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(native.__file__).resolve())==scope['bindings']['provider'][2]['path'],'PointNet2 origins');helper.check_backend(chamfer,pn,pm)
  transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr
  require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'unchanged model config');transformer.enable_bcsp_knn()
  factory=load_scq_builder(q['implementation'])
  def builder(run):return build_scq_model(factory,lambda:model_class(EasyDict(static['model'])),run,q['initialization'],q['rf_initialization'])
  budget=Budget(q,out,torch,helper)
  files,extra,states=execute_pair(torch,np,helper,runs,rows,out,budget,builder)
  done=out/'inference_complete.json';emit(done,dict(status='SCQ_RF_SIXMODEL_630_NATIVE_FORWARD_COMPLETE',forwards=630,context_cases=0,trace_cases=0,models=states,training_updates=0,BNCal=0,loss=0,backward=0,request_sha256=qr['sha256']))
  archive=pack(out,files+extra+[done,budget.path])
  require(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=q['limits']['output_bytes'] and time.monotonic()-budget.start<=q['limits']['wall_seconds'] and shutil.disk_usage(out).free>=q['limits']['minimum_free_disk_bytes'],'post-archive output/time/disk budgets')
  emit(out/'completion.json',dict(status='PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT',forwards=630,archive=archive,request_sha256=qr['sha256']))
 except BaseException as exc:
  if out.exists() and not (out/'failure.json').exists():emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),training_updates=0,BNCal=0))
  raise
 finally:
  if source_guard is not None:source_guard.close()
  utc.close()

if __name__=='__main__':main()
