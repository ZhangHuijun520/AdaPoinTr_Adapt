"""Inert, exact-hash authorized F0 decoder-only diagnostic. No new Native replay."""
import argparse,gc,hashlib,importlib.util,json,os,random,socket,sys,time,shutil
from pathlib import Path

CONDITIONS=('prefix_feature_null','prefix_donor','local_graph_donor')
TYPES=('bilateral','frontoorbital','parietotemporal','random_1','random_2')
LIMITS=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,
            device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)

def require(ok,msg):
 if not ok:raise RuntimeError(msg)

def clean(p):
 p=Path(p).absolute();require(not any(x.is_symlink() for x in (p,*p.parents)),'linked path '+str(p));return p

def exact(r):
 p=clean(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'],'size '+str(p))
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 require(h.hexdigest()==r['sha256'],'SHA '+str(p));return p

def bound(r):return json.loads(exact(r).read_bytes())

def source(name,r):
 require(name not in sys.modules,'preloaded '+name);p=exact(r)
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__);return m

def validate_index(index):
 require(set(index)=={'schema','Native_audit','pairs','runs'},'index keys')
 require(index['schema']=='f0-30-decoder-context-index-v1' and
         index['Native_audit']['sha256']=='69a2438f42a40daeaf068ab77775a5679a30013167ba303a5da5dfa7287ae09e','Native audit')
 require(len(index['pairs'])==10 and len(index['runs'])==2,'ten pairs two folds')
 for i,row in enumerate(index['pairs']):
  fold='C' if i<5 else 'D';r='001' if i<5 else '004';d='003' if i<5 else '005';kind=TYPES[i%5]
  require(row['run']==fold+'_F0' and row['recipient']=='train__'+r+'__'+kind and
          row['donor']=='train__'+d+'__'+kind,'fixed ordered pair')
  require(set(row)=={'run','recipient','donor','recipient_context','donor_context','Native_trace','Native_prediction','normalization'},'pair keys')
  require(row['normalization']['scale']>0,'positive scale')
  for key,folder,case in [('recipient_context','context',row['recipient']),('donor_context','context',row['donor']),('Native_trace','traces',row['recipient']),('Native_prediction','predictions',row['recipient'])]:
   p=Path(row[key]['path']);require(p.name==row['run']+'__'+case+'.npz' and p.parent.name==folder,'cache role')
 require([r['label'] for r in index['runs']]==['C_F0','D_F0'],'run order')
 require([r['checkpoint']['sha256'] for r in index['runs']]==[
 '4fd73dd8c265781225ba63a712a5589b175c94f0ea0878a69ebf466265ebebe9',
 'c4f29a8df3e36af2c87a20dc4888eb4b6a344bb448baa6403fb6c9c86023edaa'],'frozen weights')
 return index

def authorize(qr,ar,rr):
 q,a,r=bound(qr),bound(ar),bound(rr)
 require(q['schema']=='f0-30-decoder-only-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','request status')
 require(q['conditions']==list(CONDITIONS) and q['decoder_calls']==30 and q['head_calls']==30 and q['native_ssm_calls']==720,'30 suffix budget')
 require(all(q[k]==0 for k in ('encoder_calls','coarse_calls','Native_replay','loss_calls','backward','optimizer_steps','BNCal','training','GT_access')),'zero forbidden calls')
 require(q['limits']==LIMITS and q['null_site']=='RAW_F_BEFORE_NORM_V_KEEP_PE_AND_LN_BETA' and
         q['fixed_recipient']==['z','Q','X'] and q['query_groups']==[[0,86],[86,171],[171,256]],'frozen intervention')
 require(q['comparison']==dict(atol=1e-6,rtol=1e-5,relative_denominator_floor=1e-12,response_is_not_performance=True,current_noise_floor_measured=False),'comparison contract')
 require(a==dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text=a.get('user_authorization_text')) and bool(a['user_authorization_text'].strip()),'explicit hash authorization')
 require(r==dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one way runtime')
 validate_index(bound(q['context_index']))
 p3=bound(q['P3']);require(p3['status']=='F0_CONDITION_LOCAL_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'] and p3['adapter_sha256']==q['adapter']['sha256'],'local P3/final source binding')
 return q

def load_npz(np,record,keys=None):
 with np.load(exact(record),allow_pickle=False) as z:
  require(keys is None or set(z.files)==set(keys),'NPZ keys');a={k:z[k].copy() for k in z.files}
 require(all(v.dtype==np.float32 and np.isfinite(v).all() for v in a.values()),'finite FP32 arrays')
 return a

def execute(torch,np,h,p,adapter,index,out,budget,builder,device='cuda:0',artificial=False):
 attempted=successful=0;files=[];states=[];journal=out/'calls.jsonl';responses=out/'responses.jsonl';isolation=out/'isolation.jsonl'
 for f in (journal,responses,isolation):f.open('x').close()
 for run in index['runs']:
  random.seed(0);np.random.seed(0);torch.manual_seed(0)
  model,evidence=builder(run);p.validate_model(model,evidence,artificial);p.load_checkpoint(torch,model,run)
  model.eval().to(device);cuda=device.startswith('cuda')
  if cuda:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
  before=h.state_sha(model);rng=p.rng_state(torch,np,h,cuda)
  for row in [r for r in index['pairs'] if r['run']==run['label']]:
   rec={k:torch.from_numpy(v).to(device) for k,v in load_npz(np,row['recipient_context'],('F','S','z','Q','X')).items()}
   donor={k:torch.from_numpy(v).to(device) for k,v in load_npz(np,row['donor_context'],('F','S','z','Q','X')).items()}
   native={k:torch.from_numpy(v).to(device) for k,v in load_npz(np,row['Native_trace']).items()}
   require(set(native)=={'layer_'+str(i)+'__'+k for i in range(8) for k in adapter.TRACE_KEYS},'40 Native trace arrays')
   native_p=load_npz(np,row['Native_prediction'],('prediction','coarse'))
   require(np.array_equal(rec['Q'].cpu().numpy()[0],native_p['coarse']),'cached Q Native agreement')
   dense_ref=torch.from_numpy(native_p['prediction']).unsqueeze(0).to(device)
   for condition in CONDITIONS:
    h.assert_numeric(torch);budget.sample('before_suffix',attempted);require(attempted<30,'budget exhausted');attempted+=1
    label=row['run']+'__'+row['recipient']+'__'+condition
    p.append_event(journal,dict(index=attempted,label=label,status='CLAIMED_BEFORE_SUFFIX'))
    with torch.inference_mode():
     dense,layers,proof=adapter.intervene(model,rec,donor,condition)
     stage,dense_response=adapter.compare(layers,native,dense,dense_ref,rec,row['normalization']['scale'])
     if condition=='local_graph_donor':require(torch.allclose(layers[0]['prefix_suffix'],native['layer_0__prefix_suffix'],atol=1e-6,rtol=1e-5),'local-only first prefix isolation')
    if cuda:torch.cuda.synchronize()
    arrays={'layer_'+str(i)+'__'+k:v.detach().cpu().numpy().copy() for i,l in enumerate(layers) for k,v in l.items() if k in adapter.TRACE_KEYS}
    for folder,values in [('predictions',dict(prediction=dense[0].cpu().numpy(),coarse=rec['Q'][0].cpu().numpy())),('traces',arrays)]:
     path=out/folder/(label+'.npz')
     with path.open('xb') as f:np.savez_compressed(f,**values)
     files.append(path)
    p.append_event(responses,dict(index=attempted,label=label,donor=row['donor'],layers=stage,dense=dense_response))
    p.append_event(isolation,dict(index=attempted,label=label,**proof));successful+=1
    p.append_event(journal,dict(index=attempted,label=label,status='SUFFIX_COMPLETE'))
    del dense,layers,arrays;budget.sample('after_suffix',attempted)
   del rec,donor,native,native_p,dense_ref
  after=h.state_sha(model);rng_after=p.rng_state(torch,np,h,cuda)
  require(before==after and rng==rng_after,'state or RNG changed')
  states.append(dict(run=run['label'],state_before=before,state_after=after,RNG_before=rng,RNG_after=rng_after))
  del model;gc.collect()
  if cuda:torch.cuda.empty_cache()
 require(attempted==successful==30 and len(files)==60,'exact30 suffix 60 NPZ')
 return files+[journal,responses,isolation],states

def main():
 ap=argparse.ArgumentParser()
 for name in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):ap.add_argument('--'+name,required=True)
 a=ap.parse_args();r=lambda p,s:dict(path=p,bytes=clean(p).stat().st_size,sha256=s)
 qr=r(a.request,a.request_sha256);q=authorize(qr,r(a.authorization,a.authorization_sha256),r(a.runtime,a.runtime_sha256))
 I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
 require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
 require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity')
 require(Path.cwd()==Path(I['project']) and Path(__file__).resolve()==exact(q['entry']),'cwd/entry')
 require(out.parent==Path(I['project'])/'logs/cranial_bcsp_fullmamba','output parent')
 parent=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
 require(parent[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s'],'external timeout')
 require(json.loads(clean(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single claim')
 p=source('f0_condition_native_helpers',q['native_helper']);h=source('f0_condition_source_helper',q['helper']);h._MONITOR=None
 utc_module=source('f0_condition_utc',q['implementation']['timezone']);utc=utc_module.ExactUTCReader(utc_module.UTC_RESOURCE);guards=[]
 try:
  index=validate_index(bound(q['context_index']));scope=bound(q['preflight_scope']);static=bound(q['static_config'])
  for asset in q['dependencies']:exact(asset)
  records=h.source_map(scope)
  for rel,rec in records.items():h.exact(root/rel,rec['sha256'],rec['bytes'])
  h.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
  for rec in scope['bindings']['provider']+scope['bindings']['environment_metadata']:h.exact(rec['path'],rec['sha256'],rec['bytes'])
  inputs=[row[k]['path'] for row in index['pairs'] for k in ('recipient_context','donor_context','Native_trace','Native_prediction')]
  for row in index['pairs']:
   for k in ('recipient_context','donor_context','Native_trace','Native_prediction'):exact(row[k])
  for run in index['runs']:exact(run['checkpoint'])
  for k,v in q['environment'].items():require(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
  smi=[s.strip() for s in h.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
  require(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'GPU identity/idle')
  require(out.is_dir() and {x.name for x in out.iterdir()}=={'launch.log'},'fresh output')
  for name in ('predictions','traces','tmp'):(out/name).mkdir()
  with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
  guards.append(p.ExactSourceReads(q['implementation']))
  # Add exactly one pinned source to the existing fd-backed finite reader.
  apath=exact(q['adapter']);fd=os.open(apath,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
  guards[0].records[apath]=q['adapter'];guards[0].fds[apath]=fd;guards[0].verify(apath)
  class Combined:
   def allow(self,filename,write=False):return any(g.allow(filename,write) for g in guards)
  envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
  sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
  h.namespace_packages(root);sys.meta_path.insert(0,h.FiniteProjectImports(root,records))
  outputs=[out/folder/(row['run']+'__'+row['recipient']+'__'+condition+'.npz') for row in index['pairs'] for condition in CONDITIONS for folder in ('predictions','traces')]
  policy=p.make_policy(h,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,inputs,[r['checkpoint']['path'] for r in index['runs']],outputs,utc,Combined());sys.addaudithook(policy.audit)
  import numpy as np
  import torch,timm,yaml,importlib
  from easydict import EasyDict
  require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
  require(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'one admitted CUDA device');torch.cuda.set_device(0);h.configure_numeric(torch)
  chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');native=importlib.import_module('pointnet2_ops._ext')
  require(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(native.__file__).resolve())==scope['bindings']['provider'][2]['path'],'provider identity');h.check_backend(chamfer,pn,pm)
  transformer=importlib.import_module('models.Transformer_utils');cls=importlib.import_module('models.AdaPoinTr').AdaPoinTr
  require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'model config');transformer.enable_bcsp_knn()
  factory=p.load_f0_builder(q['implementation']);adapter=source('f0_condition_adapter',q['adapter'])
  builder=lambda run:factory.build_model(lambda:cls(EasyDict(static['model'])),seed=0)
  budget=p.Budget(q,out,torch,h)
  files,states=execute(torch,np,h,p,adapter,index,out,budget,builder)
  for row in index['pairs']:
   for k in ('recipient_context','donor_context','Native_trace','Native_prediction'):exact(row[k])
  done=out/'diagnostic_complete.json';p.emit(done,dict(status='30_DECODER_ONLY_COMPLETE_AWAITING_FREEZE_AUDIT',decoder_calls=30,head_calls=30,native_ssm_calls=720,encoder_calls=0,coarse_calls=0,Native_replay=0,backward=0,optimizer_steps=0,models=states,request_sha256=qr['sha256']))
  budget.sample('all_complete',30);archive=p.pack(out,files+[done,budget.path])
  require(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=q['limits']['output_bytes'] and time.monotonic()-budget.start<=q['limits']['wall_seconds'] and shutil.disk_usage(out).free>=q['limits']['minimum_free_disk_bytes'],'post-archive budgets')
  p.emit(out/'completion.json',dict(status='DIAGNOSTICS_ARCHIVED_AWAITING_FREEZE_AUDIT',archive=archive,request_sha256=qr['sha256']))
 except BaseException as exc:
  if out.exists() and not (out/'failure.json').exists():p.emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
  raise
 finally:
  for g in guards:g.close()
  utc.close()

if __name__=='__main__':main()
