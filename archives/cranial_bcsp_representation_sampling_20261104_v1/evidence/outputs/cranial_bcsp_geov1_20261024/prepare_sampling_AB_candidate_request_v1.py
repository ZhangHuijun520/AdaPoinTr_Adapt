"""Only after formal PASS: freeze initialization evidence and candidate request."""
import copy,gzip,hashlib,io,json,tarfile
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';F=O/'post_V1_training_freeze_audit_v2'
C=O/'Morton_training_request_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,obj):
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 auditfile=F/'audit_report_v2.json';audit=json.loads(auditfile.read_text(encoding='utf-8'))
 assert audit['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and all(audit['checks'].values()) and len(audit['checks'])==38
 assert audit['counts']['updates']==3900 and audit['counts']['epochs']==100 and audit['counts']['case_exposures']==31200 and audit['counts']['dropped_exposures']==300
 C.mkdir(exist_ok=False)
 base=json.loads((O/'V1_training_entry_request_v1.json').read_text(encoding='utf-8'))
 q=copy.deepcopy(base);root=base['implementation']['entry']['path'].split('/implementation/')[0]
 control=root+'/control_Morton_v1';run='bcsp_sampling_ab_foldC_Morton_in8192_out8192_seed0_train_v1'
 output=base['output'].rsplit('/',1)[0]+'/'+run
 init=audit['initialization'];ck=audit['checkpoint']
 assert ck['sha256']==audit['completion']['checkpoint_sha256']
 bypath={r['path']:r for r in audit['all_bound_files']}
 for record in base['implementation'].values():assert bypath[record['path']]['sha256']==record['sha256']
 paired={'schema':'bcsp-sampling-paired-initialization-v1','stage':'BCSP_SAMPLING_AB_V1',
   'baseline_run_id':base['run_id'],'baseline_request_sha256':sha(O/'V1_training_entry_request_v1.json'),
   'baseline_authorized_scope_sha256':'4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62',
   'baseline_freeze_audit_sha256':sha(auditfile),'baseline_completion':bypath[base['output']+'/completion.json'],
   'baseline_initialization':bypath[base['output']+'/initialization.json'],'baseline_checkpoint':ck,
   'baseline_optimizer_defaults':audit['optimizer_defaults'],'verified_updates':3900,
   'identity':base['identity'],'static_config_sha256':base['static_config']['sha256'],
   'runtime_sha256':base['implementation']['runtime']['sha256'],
   'implementation_sha256':{k:v['sha256'] for k,v in base['implementation'].items()},
   'order_plan_sha256':base['order_plan']['sha256'],'order_canonical_sha256':init['order_sha256'],
   'parameter_sha256':init['parameter_sha256'],'persistent_state_sha256':init['persistent_state_sha256'],
   'seed':0,'checkpoint_will_be_loaded':False,'meaning':'Compare scratch initialization metadata before first candidate update; do not resume from final baseline weights'}
 dump(C/'paired_initialization_receipt_v1.json',paired)
 qualified=json.loads((O/'qualified_V1_training_receipt_v1.json').read_text(encoding='utf-8'));qualified['arm']='Morton_area_stratified8k'
 dump(C/'qualified_training_receipt_v1.json',qualified)
 def binding(local,remote):
  p=Path(local);return {'path':remote,'bytes':p.stat().st_size,'sha256':sha(p)}
 q.update(run_id=run,arm='Morton_area_stratified8k',paired_initialization=binding(C/'paired_initialization_receipt_v1.json',control+'/paired_initialization_receipt_v1.json'),
   data_root=base['data_root'].rsplit('/',1)[0]+'/Morton_area_stratified8k',output=output,launch_attempt=control+'/launch_attempt_v1.json')
 q['QC']['qualified_receipt']=binding(C/'qualified_training_receipt_v1.json',control+'/qualified_training_receipt_v1.json')
 assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
 assert all(q[k]==base[k] for k in ['stage','fold','n_input','identity','implementation','static_config','order_plan','model_root','resource_rebind','preflight_scope','GPU_audit','preflight_request_sha256'])
 dump(C/'training_entry_request_v1.json',q)
 inner=binding(C/'training_entry_request_v1.json',control+'/training_entry_request_v1.json')
 mapping=[dict(local_path=str(C/name),member=name,destination=control+'/'+name,bytes=(C/name).stat().st_size,sha256=sha(C/name)) for name in ['paired_initialization_receipt_v1.json','qualified_training_receipt_v1.json','training_entry_request_v1.json']]
 dump(C/'non_overwrite_control_installation_mapping_v1.json',{'status':'FROZEN_NOT_INSTALLED','new_control_root':control,'files':mapping,
   'policy':'All three targets and control directory absent before any exclusive write; no changes to reused code/data or old V1 control/results; reverify on execution'})
 transport=C/'transport_v1';transport.mkdir();stem='bcsp_sampling_ab_foldc_morton_control_v1';archive=transport/(stem+'.tar.gz')
 with archive.open('xb') as f:
  with gzip.GzipFile(fileobj=f,mode='wb',compresslevel=6,mtime=0,filename='') as z:
   with tarfile.open(fileobj=z,mode='w',format=tarfile.USTAR_FORMAT) as tar:
    for r in mapping:
     raw=Path(r['local_path']).read_bytes();info=tarfile.TarInfo(r['member']);info.mode=0o644;info.mtime=0;info.size=len(raw);tar.addfile(info,io.BytesIO(raw))
 with tarfile.open(archive,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==3 and {m.name for m in members}=={r['member'] for r in mapping}
  for m in members:assert m.isfile() and hashlib.sha256(tar.extractfile(m).read()).hexdigest()==next(r['sha256'] for r in mapping if r['member']==m.name)
 files=[archive]
 for suffix,text in [('.tar.gz.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(r['sha256']+'  '+r['member']+'\n' for r in mapping))]:
  p=transport/(stem+suffix)
  with p.open('x',encoding='ascii',newline='\n') as f:f.write(text)
  files.append(p)
 p=transport/(stem+'.contents.sha256.sha256');contents=transport/(stem+'.contents.sha256')
 with p.open('x',encoding='ascii',newline='\n') as f:f.write(sha(contents)+'  '+contents.name+'\n')
 files.append(p)
 previous=json.loads((O/'V1_training_execution_request_v2.json').read_text(encoding='utf-8'))
 env={k:v.replace(base['output'],output) for k,v in previous['launcher_contract']['environment'].items()};env['TMPDIR']=output+'/tmp'
 reused=[q['static_config'],q['order_plan'],q['resource_rebind'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*q['implementation'].values(),q['preflight_scope'],q['GPU_audit']]
 assert all(bypath[r['path']]['sha256']==r['sha256'] for r in reused)
 request={'schema':'bcsp-sampling-candidate-execution-scope-v1','status':'AWAITING_EXPLICIT_USER_AUTHORIZATION','execution_authorized':False,
   'stage':'BCSP_SAMPLING_AB_V1','run_id':run,'arm':'Morton_area_stratified8k','authorized_training_attempts':1,
   'scope':'Install only three new control metadata files without overwrites, reuse exact installed code/candidate315 data, one scratch candidate Fold C seed0 training after separate full-hash authorization',
   'identity':q['identity'],'inner_request':inner,'parent_baseline_audit':{'path':str(auditfile),'sha256':sha(auditfile),'status':audit['status'],'checkpoint_sha256':ck['sha256']},
   'paired_initialization':q['paired_initialization'],'scientific_config':q['static_config'],'order_plan':q['order_plan'],
   'training_counts':previous['training_counts'],'resources_per_run':previous['resources_per_run'],
   'same_science_as_baseline':{'model':'B0 AdaPoinTr, not Mamba','input':8192,'target':8192,'sampler_seed':0,'training_seed':0,
     'target_normalization_and_permutation':'identical fixed targets, D frame and per-case permutation','batch_exposure_order':'byte-identical order plan,3900 updates,31200 exposures,300 drops',
     'numerics':'FP32 deterministic, TF32/AMP off','backend':'same native PointNet2/full-key chunk256 KNN/torch.cdist loss',
     'checkpoint_initialization':'scratch; compare parameter and persistent state fingerprints before first update; never load final V1 weights'},
   'transport':{'files':[{'path':str(p),'filename':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'upload_directory':'/home/jovyan'} for p in files],
     'archive_sha256':sha(archive),'members':3,'installation_mapping':{'path':str(C/'non_overwrite_control_installation_mapping_v1.json'),'sha256':sha(C/'non_overwrite_control_installation_mapping_v1.json')}},
   'reused_bindings':reused,'reused_payload':{'root':q['data_root'],'manifest':q['QC']['manifests']['Morton_area_stratified8k'],'files':315,'already_installed_and_stream_hash_verified':True,
     'audit_sha256':sha(auditfile),'require_recheck_before_execution':True},
   'future_paths':{'control':control,'authorization':control+'/authorization_v1.json','runtime':control+'/runtime_v1.json','launcher':control+'/launch_once_v1.sh',
     'launch_attempt':q['launch_attempt'],'output':output,'log':output+'/launch.log','PID':output+'/worker.pid','exit_code':output+'/exit_code.txt',
     'checkpoint':output+'/ckpt-last.pth','completion':output+'/completion.json','tmux':'bcsp_sampling_ab_foldc_morton_seed0_train_v1'},
   'launcher_contract':{'environment':env,'python':q['identity']['python_realpath'],'flags':['-I','-S','-B'],'entry':q['implementation']['entry']['path'],
     'entry_sha256':q['implementation']['entry']['sha256'],'external_timeout_seconds':86400,'kill_after_seconds':5,
     'order':'recheck identity/source/data/baseline evidence/new paths/idle GPU/disk, exclusive metadata install, authorization -> authorization SHA -> runtime -> launcher; mkdir verified log parent before redirect, attempt marker before sole tmux start, propagate actual exit code including PowerShell LASTEXITCODE',
     'control_initial_filenames':['paired_initialization_receipt_v1.json','qualified_training_receipt_v1.json','training_entry_request_v1.json']},
   'no_materialization_performed':True,'completion_boundary':'stop after this one candidate attempt; independent post-training audit and later two-arm evaluation each require separate explicit scope',
   'forbidden':['no V1 retraining','no baseline checkpoint load/resume','no retry','no development payload/evaluation or BNCal','no Fold D/extra seeds/SkullFix/MUG','no scientific code or parameter changes','no overwrite/delete','no dependency install/rebuild/download or environment upgrade'],
   'limitations':['Formal baseline audit verifies saved initialization records, not independently reconstructed initial weights','Byte hashing does not deserialize checkpoint or NPZ','Baseline loss is not prediction quality; candidate benefit unknown','GPU PIDs remain diagnostic; no exclusive cgroup guarantee']}
 dump(C/'candidate_training_execution_request_v1.json',request)
 p=C/'candidate_training_execution_request_v1.json'
 with (C/'candidate_training_execution_request_v1.json.sha256').open('x',encoding='ascii') as f:f.write(sha(p)+'  '+p.name+'\n')
 dump(C/'candidate_request_freeze_receipt_v1.json',{'status':'AWAITING_EXPLICIT_USER_AUTHORIZATION','request_sha256':sha(p),'metadata_members':3,'reused_candidate_data_files':315,
   'baseline_formal_audit_sha256':sha(auditfile),'actual_authorization_runtime_launcher_files_created':0,'server_writes':0,'training_started':False})
 print(json.dumps({'status':'AWAITING_EXPLICIT_USER_AUTHORIZATION','candidate_request_sha256':sha(p),'metadata_archive_bytes':archive.stat().st_size,'checkpoint_actual_sha256':ck['sha256'],'server_writes':0,'training_started':False}))
if __name__=='__main__':main()
