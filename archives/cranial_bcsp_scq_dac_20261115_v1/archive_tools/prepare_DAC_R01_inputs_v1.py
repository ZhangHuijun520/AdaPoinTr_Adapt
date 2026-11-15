"""Local preparation only: metadata selection, frozen archive members, checkpoint hashes."""
from pathlib import Path,PurePosixPath
import hashlib,importlib.util,json,tarfile
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_dac_r01_preparation_20261115_v1'
REMOTE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def rec(p,remote=None):
 p=Path(p);return dict(path=str(p) if remote is None else remote,bytes=p.stat().st_size,sha256=sha(p))
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
source=O/'bcsp_scq_dac_r1_core_v1.py';sp=importlib.util.spec_from_file_location('dac_prepare_core',source);c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
prior=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2'
ip=prior/'RF_sixmodel_input_index_v2.json';qp=prior/'pending_request_v2/payload/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
index=json.loads(ip.read_bytes());q=json.loads(qp.read_bytes());selected=c.select_cases(index)
plan=R/'docs/cranial_bcsp_scq_dac_plan_20261115/Cranial_BCSP_FullMamba_SCQ_DAC_正式实验计划书_审阅修订v2_2026-11-15.md'
assert sha(plan)=='a721117bf1b19a2bb51cbb89de5084cb9c4c2f4bc8eae2bfc64a8c4800c445ed'
backup=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_key_checkpoints_v1/local_verification_receipt_v1.json')
weights=json.loads(backup.read_bytes())['weights'];models=[];mapping=[]
for run in ('Requery_C','Requery_D'):
 w=next(x for x in weights if x['run']==run);p=Path(w['local_path']);assert rec(p)['bytes']==w['bytes'] and sha(p)==w['sha256']
 old=next(x for x in index['runs'] if x['label']==run)
 remote=REMOTE+'/weights/'+run+'_epoch99_step3900.pth'
 models.append(dict(label=run,variant='RF-Requery',fold=run[-1],checkpoint=rec(p,remote),original_checkpoint_sha256=old['checkpoint']['sha256']))
 assert models[-1]['checkpoint']['sha256']==old['checkpoint']['sha256']
 mapping.append(dict(local=str(p),remote=remote,bytes=w['bytes'],sha256=w['sha256'],action='RESTORE_ONLY_AFTER_SEPARATE_DEPLOYMENT_AUTHORIZATION'))
archive=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_native_development_eval/development_predictions_v1.tar.gz')
assert sha(archive)=='e6462382010d3061c4aa32936c052416c9bb1d6fa93233cb4159036bd51e9df0'
contents=Path(str(archive)+'.contents.sha256').read_text().splitlines();catalog={}
for line in contents:
 h,name=line.split(None,1);catalog[name.strip()]=h
replays=O/'replay';replays.mkdir()
wanted={'predictions/'+r['run']+'__'+r['case_id']+'.npz':r for r in selected};found=set()
with tarfile.open(archive,'r:gz') as t:
 for member in t:
  if member.name not in wanted:continue
  assert member.isfile() and member.name not in found;found.add(member.name)
  row=wanted[member.name];raw=t.extractfile(member).read();assert hashlib.sha256(raw).hexdigest()==catalog[member.name] and len(raw)==member.size
  p=replays/PurePosixPath(member.name).name
  with p.open('xb') as f:f.write(raw)
  remote=REMOTE+'/replay/'+p.name;row['replay']=rec(p,remote);row['replay_member_sha256']=catalog[member.name]
  mapping.append(dict(local=str(p),remote=remote,bytes=p.stat().st_size,sha256=sha(p),action='NEW_NO_OVERWRITE'))
assert found==set(wanted)
selection=O/'selected20_cases_v1.json';save(selection,dict(schema='dac-r1-selected20-v1',cases=selected,rule='SCQ_DAC_R1_v2|fold|source_id|defect_type',seven_fixed=list(c.FIXED),counts=c.COUNTS,not_independent_validation=True))
protocol=O/'R01_protocol_v1.json';save(protocol,dict(status='PREPARED_NOT_EXECUTED',plan=rec(plan),GT_access=False,geometry_scoring=False,counts=c.COUNTS,formula=dict(version='DAC-plan-v2',epsilon_norm=1e-6,alpha='0.5+0.5*relu(cosine)',near_zero='alpha=0.5',detach='alpha_only'),replay=dict(atol=1e-5,rtol=1e-4,frame='D_only_normalized',failure='STOP_NO_RETRY'),readiness=dict(fresh_remote_recheck_required=True,verified_this_preparation=False),timeouts=dict(worker_seconds=600),checkpoint_deserialized=False,server_operations=0,models=models))
save(O/'local_R0_asset_review_v1.json',dict(status='LOCAL_TWO_CHECKPOINT_BYTES_AND20_REPLAY_MEMBERS_VERIFIED',original_request=rec(qp),original_index=rec(ip),archive=rec(archive),backup_receipt=rec(backup),models=models,checkpoint_deserialized=False,actual_GPU_verified=False,source_or_environment_changed=False))
save(O/'candidate_restore_and_install_mapping_v1.json',dict(status='CANDIDATE_NOT_DEPLOYED',root=REMOTE,files=mapping,unmatched_files_to_delete=[],no_overwrite=True,old_deleted_server_paths_reused=False))
save(O/'preparation_bindings_v1.json',dict(remote=REMOTE,prior_request=rec(qp),prior_index=rec(ip),selection=rec(selection,REMOTE+'/selected20_cases_v1.json'),protocol=rec(protocol,REMOTE+'/R01_protocol_v1.json'),models=models))
print(json.dumps(dict(status='LOCAL_R0_SELECTION_REPLAY_READY_NO_EXECUTION',cases=[r['fold']+'/'+r['case_id'] for r in selected],checkpoint_hashes_verified=2,replay_members_verified=20),ensure_ascii=True))
