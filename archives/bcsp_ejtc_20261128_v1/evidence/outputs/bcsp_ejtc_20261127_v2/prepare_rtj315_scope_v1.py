"""Local preparation only: frozen cohort, checkpoint references and compatibility."""
from pathlib import Path,PurePosixPath
from collections import Counter
import hashlib,json,math
import numpy as np
base=Path(__file__).resolve().parent
out=base/'native_rtj315_preparation_v1';out.mkdir(exist_ok=False)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sha=lambda raw:hashlib.sha256(raw).hexdigest()
load=lambda p:json.loads(p.read_bytes())
def save(name,value):
 with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
locations=dict(R=base/'d1_r_d_preparation_v3/post_training_freeze_audit_v3/formal_post_training_freeze_audit_v3.json',T=base/'d1_t_d_preparation_v1/post_training_freeze_audit_v1/formal_post_training_pair_freeze_audit_v1.json',J=base/'d1_j_d_preparation_v1/post_training_freeze_audit_v1/formal_post_training_pair_freeze_audit_v1.json')
statuses=dict(R='FORMAL_READ_ONLY_R_D_V3_POST_TRAINING_FREEZE_AUDIT_PASS',T='FORMAL_READ_ONLY_T_D_POST_TRAINING_AND_R_T_PAIR_FREEZE_PASS',J='FORMAL_READ_ONLY_J_D_POST_TRAINING_AND_R_T_J_PAIR_FREEZE_PASS')
receipts={};checkpoints={};starts=[]
for arm,p in locations.items():
 r=load(p)
 assert r['status']==statuses[arm] and r['counts']==dict(steps=3900,epochs=100,exposures=31200,drops=300,cases=315,sources=63)
 for name,digest in r['evidence_sha256'].items():assert h(p.parent/'evidence'/name)==digest
 receipts[arm]=dict(local_path=str(p),bytes=p.stat().st_size,sha256=h(p),status=r['status'],training_request_sha256=r['request_sha256'])
 checkpoints[arm]={k:r['checkpoint'][k] for k in ['path','bytes','sha256']}
 starts.append(load(p.parent/'evidence/ejtc_start.json'))
assert starts[0]['rng']==starts[1]['rng']==starts[2]['rng']
assert load(locations['J'])['T_formal_freeze_sha256']==h(locations['T'])
assert len({r['sha256'] for r in checkpoints.values()})==3
q=load(base/'d1_j_d_preparation_v1/EJTC_D1_J_D_training_execution_request_h7vvrr_v1.json')
parent=load(base.parent/'bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json')
geo=base.parent/'cranial_bcsp_geov1_20261024'
fp=geo/'consolidated_binding_v1/fold_binding.json';mp=geo/'real_data_qc_v1/manifest_8192.jsonl'
assert h(fp)==parent['fold']['sha256'] and h(mp)==parent['point_manifest']['sha256']
f=load(fp)['folds']['D'];ids=f['dev_case_ids'];sources=f['dev_sources']
records={r['case_id']:r for r in map(json.loads,mp.read_bytes().splitlines())}
assert len(ids)==len(set(ids))==105 and len(sources)==len(set(sources))==21
assert not set(ids)&set(f['train_case_ids']) and not set(sources)&set(f['train_sources'])
inputs=[]
for cid in ids:
 r=records[cid];p=geo/'real_data_qc_v1'/r['point_path'];assert h(p)==r['sha256']
 assert r['normalization_source']=='defective_bbox' and r['n_input']==r['n_target']==8192
 norm=r['normalization']
 assert len(norm['center'])==3 and all(map(math.isfinite,norm['center'])) and math.isfinite(norm['scale']) and norm['scale']>0
 with np.load(p,allow_pickle=False) as archive:x=archive['partial'].copy()
 assert x.shape==(8192,3) and x.dtype==np.float32 and np.isfinite(x).all()
 inputs.append(dict(case_id=cid,source_id=r['source_id'],input=dict(path=str(PurePosixPath(parent['data_root'])/r['point_path']),bytes=p.stat().st_size,sha256=r['sha256']),partial_array_sha256=sha(x.tobytes()),normalization=norm,n_input=8192))
assert Counter(r['source_id'] for r in inputs)==Counter({s:5 for s in sources})
schedule=[dict(index=i*105+j+1,arm=arm,fold='D',case_id=cid) for i,arm in enumerate(['R','T','J']) for j,cid in enumerate(ids)]
assert len(schedule)==315 and len({(r['arm'],r['case_id']) for r in schedule})==315
scope=dict(status='NATIVE_RTJ315_SCOPE_FROZEN_PENDING_ENTRY_ADAPTATION',fold='D',arms=['R','T','J'],seeds=q['seeds'],cases_per_arm=105,sources=21,input_points=8192,output_points=8192,batch_size=1,counts=dict(forward=315,loss=0,backward=0,optimizer_steps=0,BNCal=0,warmup=0,TTA=0,scoring=0),case_ids=ids,inputs=inputs,checkpoints=checkpoints,training_freeze_receipts=receipts,shared_initial_fingerprint=q['initial_state_sha256'],schedule=schedule,schedule_sha256=sha(json.dumps(schedule,sort_keys=True,separators=(',',':')).encode()),fold_binding=parent['fold'],point_manifest=parent['point_manifest'],source_split='Fold D development, 21 sources; not a held-out final test set',input_policy='Read only partial array from frozen NPZ; same defective-bbox normalization across arms. No labels/GT, sampling, augmentation, alignment or output correction.',native_policy='Same frozen prefix.build_model constructor and seeds as training; strict load correctly arm-tagged epoch99/step3900 checkpoint; eval plus inference_mode; exactly one full forward per case. No training-worker import or loss attachment.',outputs='315 prediction NPZs with native coarse/dense and existing OASG S/delta/parent-index diagnostics; paired manifest, attempt journal, state/RNG evidence, resource records and checksum archive',state_policy='Within each arm, require parameter/buffer and four RNG fingerprints unchanged over 105 eval forwards. Trained parameters are not required to match across arms.',execution_authorized=False,remote_operations=0)
save('EJTC_RTJ_D_native315_scope_v1.json',scope)
paths=dict(native_loader=base.parent/'bcsp_oasg_20261124_v1/skullfix_prediction_v2/oasg_sf_native_v2.py',old_rbss_entry=base.parent/'bcsp_rbss_20261126_v2/foldd_native315_v1/rbss_native315_v1.py',old_oasg_entry=base.parent/'bcsp_oasg_20261124_v1/p4_ba_d_v2/oasg_native_ba_d_v2.py',prefix=base.parent/'bcsp_rbss_20261126_v2/p0b_prefix16_v1/rbss_prefix16_v1.py')
assert h(paths['native_loader'])==q['files']['native_loader']['sha256'] and h(paths['prefix'])==q['files']['prefix']['sha256']
compat=dict(status='MINIMAL_RTJ_NATIVE_ENTRY_ADAPTATION_REQUIRED',model_architecture_compatible=True,strict_runtime_checkpoint_loading_required=True,no_actual_checkpoint_deserialization_performed=True,existing_sources={k:dict(local_path=str(p),bytes=p.stat().st_size,sha256=h(p)) for k,p in paths.items()},reusable=['Frozen training prefix.build_model and native prepare_models','Existing Native coarse/FC observations and OASG S/delta/parent-index diagnostics','Partial-only reading, Fold D selection, state/RNG observations and archive conventions'],cannot_reuse_verbatim=['OASG entry hardcodes old B/A identities, seed2026112101 and 210 calls','RBSS entry hardcodes old R/C/S identities, seed2026112701/03 and injects permutations which EJTC must not use','Training launchers enforce 3900 training steps and cannot launch zero-update Native prediction'],minimum_changes=['EJTC R/T/J Native entry and necessary prediction-only short launcher, actual seed2026112801/03 and checkpoint/freeze schemas','Reject wrong arm/fold/seed/epoch/update checkpoint payloads; load each state strictly','315 ordered forward claims, no warm-up/extra forward/retry; preserve true R/T/J tags in manifests while observing common OASG head format','Targeted CPU build/load boundary, wrong identity/split, partial-only array-access spy, forward order/budget, payload and state/RNG evidence tests','Bounded P3, then read-only current server checkpoint/GPU/105 actual input paths/new-target verification before final request and transport freeze'],GPU_preflight_repeat_required=False,execution_authorized=False)
save('EJTC_RTJ_D_native_entry_compatibility_v1.json',compat)
root=PurePosixPath('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_ejtc_native315_20261128_v1')
draft=dict(schema='bcsp-ejtc-rtj-native315-preparation-v1',status='DRAFT_NOT_EXECUTABLE_PENDING_NATIVE_ENTRY_CPU_P3',execution_authorized=False,scope_sha256=h(out/'EJTC_RTJ_D_native315_scope_v1.json'),compatibility_sha256=h(out/'EJTC_RTJ_D_native_entry_compatibility_v1.json'),proposed_install_root=str(root),proposed_output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/EJTC_RTJ_D_native315_h7vvrr_v1',proposed_controls={k:str(root/name) for k,name in dict(request='EJTC_RTJ_D_native315_execution_request_h7vvrr_v1.json',authorization='Native315_authorization_v1.json',runtime='Native315_runtime_v1.json',single_attempt_log='Native315_single_attempt_v1.log',resource_log='Native315_resource_v1.jsonl',dispatch_log='Native315_dispatch_v1.log',exit_code='Native315_exit_code_v1.txt').items()},proposed_session='bcsp_ejtc_native315_h7vvrr_v1',proposed_identity=q['binding']['identity'],proposed_resources=q['binding']['resources'],deadline=q['launch']['deadline'],boundary=dict(single_attempt=True,resume=False,automatic_retry=False,loss=False,backward=False,optimizer=False,BNCal=False,scoring=False),final_request_condition='Final executable request and authorization SHA256 require minimal Native entry, targeted CPU contracts, P3 and current server readiness. This draft is not an execution authorization target.',current_server_paths_verified=False)
save('EJTC_RTJ_D_native315_request_preparation_draft_v1.json',draft)
receipt=dict(status='EJTC_RTJ315_LOCAL_PREDICTION_PREPARATION_COMPLETE_PENDING_ENTRY_ADAPTATION',case_count=105,source_count=21,predictions=315,arms=['R','T','J'],local_input_files_hash_checked=105,partial_arrays_only_read=True,checkpoint_identities_bound=True,training_freezes_verified=True,scope_sha256=h(out/'EJTC_RTJ_D_native315_scope_v1.json'),request_draft_sha256=h(out/'EJTC_RTJ_D_native315_request_preparation_draft_v1.json'),final_executable_request_created=False,remote_operations=0,model_forwards=0,predictions_started=False)
save('native315_preparation_receipt_v1.json',receipt)
print(json.dumps(receipt))
