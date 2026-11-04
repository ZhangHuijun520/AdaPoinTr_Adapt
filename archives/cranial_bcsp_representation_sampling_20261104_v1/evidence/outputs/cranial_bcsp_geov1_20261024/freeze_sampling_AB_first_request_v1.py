"""Freeze local code/data transport and first V1 pending request; no server writes."""
import ast,copy,gzip,hashlib,io,json,tarfile,time
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';I=O/'implementation'
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr';ROOT=PROJECT+'/third_party/bcsp_sampling_ab_foldc_seed0_v1';DATA=PROJECT+'/data/bcsp_sampling_ab_foldc_seed0_v1'
RUN='bcsp_sampling_ab_foldC_V1_in8192_out8192_seed0_train_v1';OUT=PROJECT+'/logs/cranial_bcsp_sampling_ab_v1/'+RUN;CONTROL=ROOT+'/control_V1_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 start=time.monotonic();test=O/'cpu_contract_attempt_v2/result.json';v=json.loads(test.read_text(encoding='utf-8'))
 assert v['status']=='PASS' and v['checks']==12 and v['test_sha256']==sha(I/'test_sampling_training_contract_v1.py')
 for p in I.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 entry=(I/'bcsp_sampling_training_entry_v1.py').read_text(encoding='utf-8')
 assert sha(I/'bcsp_sampling_training_contract_v1.py') in entry and sha(O/'paired_train_data_receipt.json') in entry
 assert "q['n_input'], q['arm'])" in entry and 'validate_pair_initialization(pair_initialization' in entry
 codehash={p.name:sha(p) for p in I.glob('*.py')};assert len(codehash)==4
 dump(O/'local_P3_v1.json',{'status':'LOCAL_CPU_P3_PASS_WITH_EXPLICIT_LIMITS','implementation_hashes':codehash,
   'CPU_tests':{'path':str(test),'sha256':sha(test),'checks':12,'attempt':'v2 after adding pre-update paired-initialization equality checks; prior passing v1 and source snapshot retained'},
   'science_unchanged':['model weights architecture code','3900-step arithmetic','optimizer/LR/BN lifecycle','full-key chunk256 KNN','same PointNet2 and cdist loss'],
   'data':'630 NPZ roundtrip checks; same targets/frames and fixed per-case input permutation verified',
   'authorization_tests':'RAM-only fixtures, no actual user authorization/runtime created',
   'limits':['Metadata/bootstrap CPU tests, no real model or gradient calls','Authorization test replaces file resolution/resource lookup with RAM fixtures; real server entry not run','No current CUDA validation or training claim','Training data only, no development payload read this turn']})
 base=json.loads((P/'training_entry_request_v4.json').read_text(encoding='utf-8'));q=copy.deepcopy(base)
 q.update(schema='bcsp-sampling-training-request-v1',stage='BCSP_SAMPLING_AB_V1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id=RUN,
   arm='V1',paired_initialization=None,fold='C',n_input=8192,data_root=DATA+'/V1',output=OUT,launch_attempt=CONTROL+'/launch_attempt_v1.json')
 assets=[]
 def add(local,member,dest):
  p=Path(local);assert p.is_file() and not p.is_symlink()
  r={'path':dest,'bytes':p.stat().st_size,'sha256':sha(p)}
  assets.append({'local_path':str(p),'member':member,'destination':dest,'bytes':r['bytes'],'sha256':r['sha256']});return r
 q['static_config']=add(O/'static_training_config_v1.json','evidence/static_training_config_v1.json',ROOT+'/evidence/static_training_config_v1.json')
 q['order_plan']=add(O/'shared_order_foldC_seed0_v1.json','evidence/shared_order_foldC_seed0_v1.json',ROOT+'/evidence/shared_order_foldC_seed0_v1.json')
 q['resource_rebind']=add(O/'resource_binding_v1.json','evidence/resource_binding_v1.json',ROOT+'/evidence/resource_binding_v1.json')
 for name in ['server_readonly_observation_v1.json','server_assets_observation_v1.json','comparison_protocol_v1.json','local_P3_v1.json']:
  add(O/name,'evidence/'+name,ROOT+'/evidence/'+name)
 q['identity']=json.loads((O/'resource_binding_v1.json').read_text(encoding='utf-8'))['new_identity']
 q['implementation']={k:add(I/name,'implementation/'+name,ROOT+'/implementation/'+name) for k,name in [('entry','bcsp_sampling_training_entry_v1.py'),('contract','bcsp_sampling_training_contract_v1.py'),('runtime','bcsp_sampling_training_runtime_v1.py')]}
 q['implementation']['preflight_helper']=base['implementation']['preflight_helper']
 add(I/'test_sampling_training_contract_v1.py','implementation/test_sampling_training_contract_v1.py',ROOT+'/implementation/test_sampling_training_contract_v1.py')
 verification=add(O/'paired_train_data_receipt.json','evidence/paired_train_data_receipt.json',ROOT+'/evidence/paired_train_data_receipt.json')
 manifests={}
 for arm in ['V1','Morton_area_stratified8k']:
  records=[json.loads(s) for s in (O/arm/'train_manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()]
  assert len(records)==315
  manifests[arm]=add(O/arm/'train_manifest_8192.jsonl','evidence/'+arm+'_train_manifest_8192.jsonl',ROOT+'/evidence/'+arm+'_train_manifest_8192.jsonl')
  for r in records:
   assert sha(r['source_point_file'])==r['source_point_sha256']
   rec=add(O/arm/r['point_path'],'data/'+arm+'/'+r['point_path'],DATA+'/'+arm+'/'+r['point_path']);assert rec['sha256']==r['sha256']
 foldrec=add(B/'consolidated_binding_v1/fold_binding.json','evidence/fold_binding.json',ROOT+'/evidence/fold_binding.json')
 fold=json.loads((B/'consolidated_binding_v1/fold_binding.json').read_text(encoding='utf-8'))['folds']['C']
 limits=['Separate inner/outer plate coverage not certified','Representation QC is not prediction or clinical accuracy','Artificial GPU zero-update success is not complete training memory proof']
 qualified={'schema':'bcsp-sampling-qualified-v1','stage':'BCSP_SAMPLING_AB_V1','arm':'V1','verification':verification,'manifests':manifests,'fold_binding':foldrec,'fold':'C','n_input':8192,'train_allowlist_sha256':fold['train_allowlist_sha256'],'limitations':limits}
 dump(O/'qualified_V1_training_receipt_v1.json',qualified)
 qualifiedrec=add(O/'qualified_V1_training_receipt_v1.json','evidence/qualified_V1_training_receipt_v1.json',ROOT+'/evidence/qualified_V1_training_receipt_v1.json')
 q['QC']={'qualified_receipt':qualifiedrec,'verification':verification,'manifests':manifests,'fold_binding':foldrec}
 dump(O/'V1_training_entry_request_v1.json',q)
 innerrec=add(O/'V1_training_entry_request_v1.json','control_V1_v1/training_entry_request_v1.json',CONTROL+'/training_entry_request_v1.json')
 assert len({a['member'] for a in assets})==len({a['destination'] for a in assets})==len(assets)
 dump(O/'non_overwrite_installation_mapping_v1.json',{'status':'FROZEN_NOT_INSTALLED','assets':assets,'source_kind':'paired train NPZ/code/metadata only; no raw NRRD or checkpoint','required_new_roots':[ROOT,DATA,PROJECT+'/logs/cranial_bcsp_sampling_ab_v1'],
   'install_contract':'recheck current identity, all archive hashes and all target absence before any write; regular files only, exclusive create, no symlinks, postwrite hashes; any exception stops with no retry'})
 T=O/'transport_v1';T.mkdir();name='bcsp_sampling_ab_foldc_seed0_v1';archive=T/(name+'.tar.gz')
 with archive.open('xb') as f:
  with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,compresslevel=6,filename='') as z:
   with tarfile.open(fileobj=z,mode='w',format=tarfile.USTAR_FORMAT) as tar:
    for a in assets:
     data=Path(a['local_path']).read_bytes();assert hashlib.sha256(data).hexdigest()==a['sha256']
     info=tarfile.TarInfo(a['member']);info.size=len(data);info.mode=0o644;info.mtime=0;tar.addfile(info,io.BytesIO(data))
 with tarfile.open(archive,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==len(assets)
  byname={a['member']:a for a in assets}
  for m in members:assert m.isfile() and m.size==byname[m.name]['bytes'] and hashlib.sha256(tar.extractfile(m).read()).hexdigest()==byname[m.name]['sha256']
 files=[archive]
 for suffix,text in [('.tar.gz.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(a['sha256']+'  '+a['member']+'\n' for a in assets))]:
  p=T/(name+suffix)
  with p.open('x',encoding='ascii',newline='\n') as f:f.write(text)
  files.append(p)
 contents=T/(name+'.contents.sha256');p=T/(name+'.contents.sha256.sha256')
 with p.open('x',encoding='ascii',newline='\n') as f:f.write(sha(contents)+'  '+contents.name+'\n')
 files.append(p)
 env={k:v.replace('<owned_output>',OUT) for k,v in json.loads((B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json').read_text(encoding='utf-8'))['environment'].items()};env['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid']
 request={'schema':'bcsp-sampling-first-model-execution-scope-v1','status':'AWAITING_EXPLICIT_USER_AUTHORIZATION','execution_authorized':False,
   'stage':'BCSP_SAMPLING_AB_V1','scope':'after user upload: exact non-overwrite installation of paired data and four implementation files, then one fresh V1 FoldC seed0 training only',
   'run_id':RUN,'training_runs_authorized_by_this_pending_scope':1,'planned_pair_total_runs':2,'candidate_training_authorized':False,
   'identity':q['identity'],'inner_request':innerrec,'scientific_config':q['static_config'],'order_plan':q['order_plan'],'local_P3':{'path':str(O/'local_P3_v1.json'),'sha256':sha(O/'local_P3_v1.json')},
   'training_counts':{'sources':63,'cases':315,'input':8192,'target':8192,'batch':8,'traversals':100,'updates':3900,'exposures':31200,'dropped_exposures':300},
   'resources_per_run':json.loads((O/'static_training_config_v1.json').read_text(encoding='utf-8'))['resources'],
   'transport':{'files':[{'path':str(p),'filename':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'upload_directory':'/home/jovyan'} for p in files],
       'archive_sha256':sha(archive),'members':len(assets),'installation_mapping':{'path':str(O/'non_overwrite_installation_mapping_v1.json'),'sha256':sha(O/'non_overwrite_installation_mapping_v1.json')}},
   'future_paths':{'control':CONTROL,'authorization':CONTROL+'/authorization_v1.json','runtime':CONTROL+'/runtime_v1.json','launcher':CONTROL+'/launch_once_v1.sh','launch_attempt':q['launch_attempt'],
      'output':OUT,'log':OUT+'/launch.log','PID':OUT+'/worker.pid','exit_code':OUT+'/exit_code.txt','checkpoint':OUT+'/ckpt-last.pth','completion':OUT+'/completion.json','tmux':'bcsp_sampling_ab_foldc_v1_seed0_train_v1'},
   'launcher_contract':{'environment':env,'python':q['identity']['python_realpath'],'flags':['-I','-S','-B'],'entry':q['implementation']['entry']['path'],
      'entry_sha256':q['implementation']['entry']['sha256'],'external_timeout_seconds':86400,'kill_after_seconds':5,
      'order':'verify all source/environment/resource gates; create and verify parents before redirect; claim exclusive attempt before single tmux launch; propagate true exit code including PowerShell exit LASTEXITCODE',
      'one_way_materialization':'frozen inner request -> explicit authorization binds inner/full scope hashes -> compute authorization SHA -> runtime binds request and authorization -> single launcher; no reverse hash edges'},
   'scientific_risk_disclosure':['Both arms have a new common fixed input-permutation policy, therefore no direct reuse of historical weights as main matched arm','Read-only identity/provider match is not current CUDA verification; unchanged arithmetic uses historical GPU evidence','CPU tests include RAM authorization fixtures, not live server execution','Monitored resource stopping only, no strict PID ownership or exclusive cgroup guarantee'],
   'completion_boundary':'stop after this one V1 attempt. Independent post-training freeze audit and exact initialization evidence require the next explicit scope; candidate request is not yet created.',
   'forbidden':['no candidate training','no development payload/evaluation','no BNCal','no FoldD/SkullFix/MUG/Mamba changes','no resume/retry','no source/environment installation or upgrade','no old-file overwrite/delete']}
 dump(O/'V1_training_execution_request_v1.json',request)
 req=O/'V1_training_execution_request_v1.json'
 with (O/'V1_training_execution_request_v1.json.sha256').open('x',encoding='ascii') as f:f.write(sha(req)+'  '+req.name+'\n')
 dump(O/'request_and_transport_freeze_receipt_v1.json',{'status':'PENDING_REQUEST_AND_TRANSPORT_FROZEN_NO_SERVER_WRITES','request_sha256':sha(req),'archive_sha256':sha(archive),
   'members':len(assets),'archive_bytes':archive.stat().st_size,'server_deployments':0,'training_calls':0,'authorization_runtime_launcher_files_created':0,'seconds':time.monotonic()-start})
 print(json.dumps({'request_sha256':sha(req),'archive_bytes':archive.stat().st_size,'members':len(assets),'files':[p.name for p in files]}))
if __name__=='__main__':main()
