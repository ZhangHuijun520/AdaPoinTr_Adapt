"""Local metadata-only derivation. No arrays, checkpoint loading or server calls."""
import hashlib,json,ast
from pathlib import Path
S=Path(__file__).resolve().parent;BASE=S.parent
AF=BASE/'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(name,x):
 with (S/name).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False)
def main():
 old=json.loads((BASE/'Native_prediction_implementation_v1/resource_rebind_v2/transport_payload/F0_CD_native_prediction_execution_request_v2.json').read_bytes())
 index=json.loads((BASE/'Native_prediction_preparation_v1/F0_CD_Native_input_index_candidate_v1.json').read_bytes())
 hashes={r['name']:r for r in json.loads((AF/'hashes_after_result_v1.json').read_bytes())['files']}
 contexts={r['name']:r for r in map(json.loads,(AF/'downloads/output/cache_manifest.jsonl').read_text().splitlines())}
 pairs=[]
 for fold,r,d in [('C','001','003'),('D','004','005')]:
  run=fold+'_F0'
  for kind in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
   recipient='train__'+r+'__'+kind;donor='train__'+d+'__'+kind
   row=dict(run=run,recipient=recipient,donor=donor)
   for key,folder,case in [('recipient_context','context',recipient),('donor_context','context',donor),('Native_trace','traces',recipient),('Native_prediction','predictions',recipient)]:
    name=folder+'/'+run+'__'+case+'.npz';h=hashes[name]
    row[key]=dict(path=old['output']+'/'+name,bytes=h['bytes'],sha256=h['sha256'])
   row['normalization']=contexts['context/'+run+'__'+recipient+'.npz']['normalization'];pairs.append(row)
 emit('context_index_candidate_v1.json',dict(schema='f0-30-decoder-context-index-v1',Native_audit=rec(AF/'post_prediction_freeze_audit_result_v1.json'),pairs=pairs,runs=index['runs']))
 emit('diagnostic_scope_v1.json',dict(status='FROZEN_FOR_LOCAL_VALIDATION_NOT_EXECUTION',formal_plan=rec(BASE.parents[1]/'docs/cranial_bcsp_fullmamba_20261110/Cranial_BCSP_FullMamba_正式实验计划书_zh_2026-11-10_v2.md'),
 selection=rec(BASE/'Native_prediction_preparation_v1/recipient_donor_registration_addendum_v1.json'),registration_timing='RULE_PRETRAINING_LITERAL_IDS_PRE_NATIVE_NOT_PRETRAINING',
 conditions=['prefix_feature_null','prefix_donor','local_graph_donor'],null_site='RAW_F_BEFORE_NORM_V_KEEP_PE_AND_LN_BETA',fixed_recipient=['z','Q','X'],
 prefix_donor='paired F/S plus coordinate PE/order only; recipient local F/S unchanged',local_graph_donor='recipient prefix; donor norm_v(F), S, recomputed KNN(8,Sdon,Qrec)',
 decoder_calls=30,head_calls=30,native_ssm_calls=720,encoder_calls=0,coarse_calls=0,Native_replay=0,GT_access=0,backward=0,optimizer_steps=0,
 query_groups=[[0,86],[86,171],[171,256]],query_order='frozen recipient Q lexicographic ordering',
 head='exact original increase_dim/global max -> reduce_map -> SimpleRebuildFC (includes own max) -> fixed Q addition; cached z is NOT head global feature',
 comparison=dict(atol=1e-6,rtol=1e-5,relative_denominator_floor=1e-12,response_is_not_performance=True,current_noise_floor_measured=False),
 interpretation='OOD offline condition sensitivity only. No response is not a uselessness proof; response is not correct conditioning. No donor/recipient reselection, parameter scan, training or structural change.',
 output='30 dense+fixed Q NPZ;30 full40-array traces;1920 layer/group response rows;30 dense responses;30 isolation proofs;2 state/RNG proofs;exact manifest/archive',
 native_accuracy_context='use already frozen Native scoring summaries only, no OOD performance recomputation',
 limits=old['limits'],fail_stop='one claim; first exception/resource/isolation failure stops; no retry/resume',formal_freeze_audit_required_after_execution=True))
 static=[]
 for name in ['bcsp_f0_condition_adapter_v1.py','bcsp_f0_condition_diagnostic_v1.py','test_f0_condition_cpu_v1.py']:
  p=S/name;tree=ast.parse(p.read_text(encoding='utf-8'));compile(tree,str(p),'exec');static.append(rec(p))
 emit('static_review_v1.json',dict(status='STATIC_PASS',sources=static,production_model_source_modified=False,notes=['No AST import execution during static review','Dedicated hooks only; frozen model/weights/config unchanged','No server or CUDA call in local preparation']))
 print('metadata scope/index/static frozen')
if __name__=='__main__':main()
