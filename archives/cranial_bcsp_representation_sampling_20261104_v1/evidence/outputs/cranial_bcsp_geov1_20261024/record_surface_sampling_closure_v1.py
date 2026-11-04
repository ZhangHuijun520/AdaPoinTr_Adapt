"""Record the user's scientific decision and exact evidence identities, locally."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];O=B/'sampling_decision_20261104_v1'
def bind(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
doc=ROOT/'docs/cranial_bcsp_geov1_20261024/surface_sampling_freeze_and_search_closure_zh_v1_20261104.md'
evidence=[doc,ROOT/'docs/cranial_bcsp_geov1_20261024/main_data_scope_and_surface_sampling_decision_zh_v1_20261102.md',B/'real_data_qc_v1.py',B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1/post_scoring_freeze_audit_v1/formal_audit_and_scientific_interpretation_zh_v1.md',B/'blue_pair_eval_v1/post_scoring_freeze_audit_v1/formal_audit_and_scientific_interpretation_zh_v1.md',B/'blue_pair_eval_v1/geometry_review_8cases_v1/geometry_review_report_zh_v1.md']
assert all(p.is_file() for p in evidence)
records=[bind(p) for p in evidence];O.mkdir()
record={'status':'SAMPLING_SEARCH_CLOSED_V1_DEFAULT_FIXED','date_Asia_Shanghai':'2026-11-04','user_confirmation_verbatim':'好的，现在固定采样方案，收束采样搜索','default_sampler':'V1_D_only_area_weighted_exposed_faces','representation':'complete bone-background boundary, not outer-only','input':'boundary(D), D-only sampling and normalization','target':'complete boundary(G) of missing solid bone','current_working_input_points':8192,'current_working_output_points':8192,'existing_dataset_bytes_and_random_order_preserved':True,'optimality_claimed':False,'candidate_policy':{'Morton':'retain evidence; search closed; not default','Euclidean_elimination':'retain evidence; search closed; not promoted over historical V1','surface_graph':'retain evidence; search closed; not default'},'automatic_new_sampling_runs_authorized':False,'next_research_direction':'model defect-position conditioning, whole-fragment placement and coverage; exact cause remains unresolved','evidence':records,'actions_this_turn':{'server_calls':0,'GPU_calls':0,'model_calls':0,'sampling_calls':0,'score_calls':0,'production_code_or_data_changes':0,'deletions':0},'new_execution_authorization':False}
with (O/'sampling_decision_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
with (O/'artifact_manifest_v1.json').open('x') as f:json.dump({'files':[bind(doc),bind(O/'sampling_decision_v1.json')]},f,indent=2)
print(json.dumps({'status':record['status'],'decision_file':str(doc),'sampling_calls':0}))
