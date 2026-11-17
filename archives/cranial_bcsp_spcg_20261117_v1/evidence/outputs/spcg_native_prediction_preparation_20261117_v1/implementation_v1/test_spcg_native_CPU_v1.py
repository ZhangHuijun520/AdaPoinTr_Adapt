"""Single24-check artificial CPU batch. No real NPZ/checkpoint or GPU access."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types,textwrap,traceback,os
import numpy as np
import torch
from torch import nn
V=Path(__file__).resolve().parent;W=V.parents[2];O=V/'CPU_batch_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
 O.mkdir();checks=[];scope=read(V/'CPU_scope_v1.json');torch.set_num_threads(2)
 def check(i,x):assert x,scope['checks'][i-1];assert len(checks)==i-1;checks.append(scope['checks'][i-1])
 def reject(fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError,KeyError):return True
  return False
 try:
  entry=V/'bcsp_spcg_sixmodel_native_predict_v1.py';e=load('SPCG_native_CPU',entry);q=read(V/'draft_request_v1.json');index=read(V/'SPCG_sixmodel_input_index_v1.json');aliases=read(V/'local_metadata_map_v1.json');oldexact=e.exact
  def mapped(r):
   if r['path'] in aliases:
    p=Path(aliases[r['path']]);a=rec(p);assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']);return p
   return oldexact(r)
  e.exact=mapped
  proofs=[read(mapped(r['training_audit'])) for r in index['runs']];check(1,len(proofs)==6 and all(all(x['checks'].values()) and x['checkpoint']==r['checkpoint'] for x,r in zip(proofs,index['runs'])))
  folds=read(mapped(q['fold_binding']));runs,rows=e.validate_index(index,folds);check(2,len(runs)==6 and len(rows)==630 and len({r['input']['path'] for r in rows})==210)
  manifest=[json.loads(l) for l in mapped(q['source_manifest']).read_text(encoding='utf-8').splitlines()];e.validate_source(index,None,manifest);check(3,all(r['normalization_source']=='defective_bbox' for r in rows))
  bad=copy.deepcopy(index);bad['inputs'][0]['input']['sha256']='0'*64;frame=copy.deepcopy(index);frame['inputs'][0]['normalization']['scale']+=1
  check(4,reject(lambda:e.validate_source(bad,None,manifest)) and reject(lambda:e.validate_source(frame,None,manifest)))
  bad=copy.deepcopy(index);bad['runs'][0]['arm']='G2';duplicate=copy.deepcopy(index);duplicate['inputs'][1]=copy.deepcopy(duplicate['inputs'][0]);check(5,reject(lambda:e.validate_index(bad,folds)) and reject(lambda:e.validate_index(duplicate,folds)))
  auth=dict(schema='bcsp-development-authorization-v1',request_sha256=rec(V/'draft_request_v1.json')['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY_NOT_EXECUTION_AUTHORITY');ap=O/'auth_fixture.json';ap.write_text(json.dumps(auth),encoding='utf-8');rp=O/'runtime_fixture.json';rp.write_text(json.dumps(dict(schema='bcsp-development-runtime-v1',request_sha256=auth['request_sha256'],authorization_sha256=rec(ap)['sha256'])),encoding='utf-8')
  check(6,e.authorize(rec(V/'draft_request_v1.json'),rec(ap),rec(rp))==q)
  for key in ['identity','environment','limits']:
   bad=copy.deepcopy(q)
   if key=='identity':bad[key]['hostname']='wrong'
   elif key=='environment':bad[key]['CUDA_VISIBLE_DEVICES']='GPU-wrong'
   else:bad[key]['wall_seconds']=1
   p=O/(key+'_bad_request.json');p.write_text(json.dumps(bad),encoding='utf-8');assert reject(lambda:e.authorize(rec(p),rec(ap),rec(rp)))
  check(7,True)
  base=W/'outputs/spcg_implementation_20261116_v1';MOTHER=Path(aliases[q['mother_source']['path']]);h=load('bcsp_spcg_head_v1',base/'bcsp_spcg_head_v1.py');f=load('bcsp_spcg_factory_v1',base/'bcsp_spcg_factory_v1.py')
  source=(base/'test_spcg_cpu_v1.py').read_text(encoding='utf-8');fixture=source[source.index('        env=dict(torch=torch'):source.index('        def build(arm):')];env=dict(torch=torch,nn=nn,ast=ast,types=types,W=W,MOTHER=MOTHER);exec(compile(textwrap.dedent(fixture),'actual_mother_fixture_definitions','exec'),env)
  factories=dict(head=h,spcg=f,lqi=types.SimpleNamespace(build_model=lambda legacy,seed:(legacy(),dict(artificial_fixture=True))))
  models={};D=torch.randn(1,8192,3)
  for arm in ['G0','G1','G2']:
   with torch.random.fork_rng(devices=[]):torch.manual_seed(11);model,ev=e.build_spcg_model(factories,env['Model'],dict(arm=arm),q,artificial_cpu=True)
   e.validate_model(model,ev,True);model.eval();run=dict(checkpoint=rec(O/(arm+'_synthetic.pth'))) if False else {}
   cp=O/(arm+'_synthetic.pth');torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=model.state_dict()),cp);run['checkpoint']=rec(cp);e.load_checkpoint(torch,model,run);e.predict_once(torch,model,D);models[arm]=(model,run)
  check(8,len(models)==3)
  models['G2'][0].base_model.spcg_head.capture=True;e.predict_once(torch,models['G2'][0],D)
  check(9,not hasattr(models['G1'][0].base_model,'coarse_pred') and models['G2'][0].base_model.spcg_head.last['index'].shape==(1,256,8) and hasattr(models['G0'][0].base_model,'coarse_pred'))
  cp=O/'missing_key.pth';state=dict(models['G0'][0].state_dict());state.pop(next(iter(state)));torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=state),cp)
  check(10,reject(lambda:e.load_checkpoint(torch,models['G0'][0],dict(checkpoint=rec(cp)))))
  cp=O/'wrong_stage.pth';torch.save(dict(stage='WRONG',epoch=98,updates=3899,base_model={}),cp);check(11,reject(lambda:e.load_checkpoint(torch,models['G0'][0],dict(checkpoint=rec(cp)))))
  class Head(nn.Module):
   def __init__(self,arm):super().__init__();self.arm=arm;self.weight=nn.Parameter(torch.ones(1))
  class Tiny(nn.Module):
   calls=0
   def __init__(self,arm,mode='ok'):
    super().__init__();self.base_model=nn.Module();self.base_model.bn=nn.BatchNorm1d(3);self.base_model.add_module('coarse_pred' if arm=='G0' else 'spcg_head',Head(arm));self.mode=mode
   def forward(self,x):
    Tiny.calls+=1
    if self.mode=='fail':raise RuntimeError('ARTIFICIAL_FAIL')
    y=self.base_model.bn(x.mean(1));Q=y[:,None,:].expand(-1,256,-1).contiguous();P=Q.repeat_interleave(32,1)
    if self.mode=='state':self.base_model.bn.running_mean.add_(1)
    if self.mode=='rng':torch.rand(1)
    return Q,P
  fixture_rows=copy.deepcopy(rows);fixture_runs=copy.deepcopy(runs);input_dir=O/'inputs';input_dir.mkdir();inputs={}
  for row in fixture_rows:
   key=(row['fold'],row['case_id'])
   if key not in inputs:
    cp=input_dir/(row['fold']+'__'+row['case_id']+'.npz')
    with cp.open('xb') as fobj:np.savez_compressed(fobj,partial=np.full((8192,3),.125,dtype=np.float32))
    inputs[key]=rec(cp)
   row['input']=inputs[key]
  for run in fixture_runs:
   model=Tiny(run['arm']);cp=O/(run['label']+'_tiny.pth');torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=model.state_dict()),cp);run['checkpoint']=rec(cp)
  helper=types.SimpleNamespace(assert_numeric=lambda t:None,tensor_sha=lambda t:hashlib.sha256(t.cpu().numpy().tobytes()).hexdigest(),state_sha=e.raw_state_fingerprint)
  samples=[];budget=types.SimpleNamespace(sample=lambda phase,count:samples.append((phase,count)))
  def builder(run,mode='ok'):return Tiny(run['arm'],mode),dict(arm=run['arm'],artificial_fixture=True,change=None if run['arm']=='G0' else dict(old_head_removed=True,head_parameters=1845763))
  out=O/'synthetic630';out.mkdir();(out/'predictions').mkdir();files,extra,states=e.execute_pair(torch,np,helper,fixture_runs,fixture_rows,out,budget,builder,device='cpu',artificial_cpu=True)
  check(12,len(files)==630 and len(states)==6 and all(x['forwards']==105 for x in states))
  with np.load(files[0],allow_pickle=False) as z:check(13,set(z.files)=={'prediction','coarse'} and z['prediction'].shape==(8192,3) and z['coarse'].shape==(256,3) and z['prediction'].dtype==np.float32 and np.allclose(z['prediction'],.125/np.sqrt(1+1e-5)))
  check(14,all(x['state_before']==x['state_after'] and x['RNG_before']==x['RNG_after'] for x in states))
  attempts=[json.loads(l) for l in (out/'forward_attempts.jsonl').read_text().splitlines()];check(15,Tiny.calls==630 and [x['forward_index'] for x in attempts]==list(range(1,631)))
  check(16,set(x.name for x in out.iterdir())=={'predictions','inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl'} and all(x['BNCal']==x['optimizer']==x['backward']==0 for x in states))
  manifests=[json.loads(l) for l in (out/'inference_manifest.jsonl').read_text().splitlines()];check(17,len(manifests)==630 and all(rec(out/x['prediction']['name'])['sha256']==x['prediction']['sha256'] and x['normalization']==r['normalization'] for x,r in zip(manifests,fixture_rows)))
  archive=e.pack(out,files+extra)
  import tarfile
  with tarfile.open(archive['path']) as tar:members=tar.getmembers();assert all(x.isfile() for x in members);assert len(members)==633
  check(18,rec(Path(archive['path']))['sha256']==archive['sha256'] and int(Path(archive['path']+'.bytes').read_text())==archive['bytes'] and len(Path(archive['path']+'.contents.sha256').read_text().splitlines())==633)
  for number,mode in [(19,'fail'),(20,'state'),(21,'rng')]:
   failed=O/('negative_'+mode);failed.mkdir();(failed/'predictions').mkdir();before=Tiny.calls
   assert reject(lambda:e.execute_pair(torch,np,helper,fixture_runs,fixture_rows,failed,budget,lambda r:builder(r,mode),device='cpu',artificial_cpu=True))
   report=read(failed/'failure.json')
   check(number,report['status']=='FAILED_STOP_NO_RETRY' and (Tiny.calls-before==1 and report['forward_attempts']==1 if mode=='fail' else report['forward_attempts']==105))
  originalos=e.os;attributes=dict(vars(os));attributes['O_RDONLY']=os.O_RDONLY|getattr(os,'O_BINARY',0);e.os=types.SimpleNamespace(**attributes)
  guard=e.make_source_guard(q)
  try:assert guard.allow(mapped(q['head_initialization'])) and reject(lambda:guard.allow(mapped(q['probe_asset']),write=True))
  finally:guard.close();e.os=originalos
  check(22,True)
  launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64);check(23,launcher.index('mkdir -p')<launcher.index(' >') and '7200s' in launcher and all('\\' not in q['launch_contract'][k] for k in ['request_path','authorization','runtime','launcher']))
  text=entry.read_text(encoding='utf-8');check(24,q['limits']['minimum_free_disk_bytes']==4*1024**3 and q['startup_free_disk_bytes']==6*1024**3 and text.index('if utc_guard.allow')<text.index('if source_guard.allow') and 'GUARD_ACTIVE_BEFORE_CLEANUP' in text and q['implementation']['spcg_factory']['sha256']==rec(base/'bcsp_spcg_factory_v1.py')['sha256'])
  result=dict(status='SPCG_NATIVE_CPU24_PASS',count=len(checks),checks=checks,entry=rec(entry),test=rec(Path(__file__)),CPU_scope=rec(V/'CPU_scope_v1.json'),synthetic_outputs=630,synthetic_failures=['one forward failure','state mutation after105','RNG mutation after105'],server_operations=0,GPU=0,real_checkpoint_loads=0,real_payload_reads=0,limitations=['Actual SPCG factory/head and mother interfaces tested with artificial backbone and surrogate loss; actual Mamba/CUDA not repeated.','630-loop test uses tiny artificial models and generated partial arrays; it is not scientific prediction.','Checkpoint tests deserialize artificial CPU state_dict files only; real weights remain unopened.','Auth/runtime fixtures provide no execution authority; fresh server readiness remains required.'])
  (O/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS24_SPCG_NATIVE_CPU_NO_SERVER')
 except BaseException as exc:
  (O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
