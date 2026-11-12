"""Report-only compilation from frozen local evidence. No model, scoring, or remote calls."""
import hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'outputs/cranial_bcsp_fullmamba_20261110';S=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(n,v):
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def mean(x):return math.fsum(x)/len(x)
training_paths={'F0_C':'training_entry_v1/post_training_freeze_audit_v1/post_training_freeze_audit_result_v1.json','F0_D':'FoldD_training_entry_v1/post_training_freeze_audit_v1/post_training_freeze_audit_result_v1.json','LQI_C':'lqi_training_entry_v1/post_training_freeze_audit_v1/post_training_freeze_audit_result_v1.json','LQI_D':'lqi_FoldD_training_entry_v1/post_training_freeze_audit_v2/post_training_freeze_audit_result_v1.json'}
sources={
 'E01':R/'docs/cranial_bcsp_fullmamba_20261110/Cranial_BCSP_FullMamba_正式实验计划书_zh_2026-11-10_v2.md',
 'E02':R/'docs/cranial_bcsp_fullmamba_20261110/F0_LQI_唯一公式与替换接口规格_zh_v1.md',
 'E03':B/'gpu_admission_v1/post_CUDA_freeze_audit_v1/post_CUDA_freeze_audit_result_v2.json',
 'E04':B/training_paths['F0_C'],'E05':B/training_paths['F0_D'],
 'E06':B/'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1/post_prediction_freeze_audit_result_v1.json',
 'E07':B/'Native_scoring_implementation_v1/post_scoring_freeze_audit_20261111_v2/audit_report_v1.json',
 'E08':B/'conditional_diagnostic_implementation_v1/post_diagnostic_freeze_audit_v1/formal_post_diagnostic_freeze_audit_result_v1.json',
 'E09':B/'conditional_diagnostic_implementation_v1/post_diagnostic_freeze_audit_v1/30次decoder条件诊断_正式冻结审计与科研解读_zh_v1.md',
 'E10':B/'lqi_gpu_admission_v1/post_CUDA_freeze_audit_v1/formal_post_CUDA_freeze_audit_result_v1.json',
 'E11':B/training_paths['LQI_C'],'E12':B/training_paths['LQI_D'],
 'E13':B/'lqi_training_entry_v1/post_training_freeze_audit_v1/F0_pairing_freeze_audit_result_v1.json',
 'E14':B/'lqi_FoldD_training_entry_v1/post_training_freeze_audit_v2/F0D_LQIC_pairing_freeze_audit_result_v2.json',
 'E15':B/'lqi_native_prediction_implementation_v1/post_prediction_freeze_audit_v1/post_prediction_freeze_audit_result_v1.json',
 'E16':B/'lqi_F0_scoring_implementation_v1/post_scoring_freeze_audit_v1/audit_report_v1.json',
 'E17':B/'lqi_F0_geometry_visualization_v1/visualization_result_v2.json',
 'E18':B/'lqi_F0_geometry_visualization_v1/delivery_QA_v1.json',
 'E19':B/'lqi_F0_scoring_preparation_v1/local_LQI_and_F0_archive_verification_v1.json',
 'E20':B/'lqi_F0_scoring_implementation_v1/startup_lifetime_readonly_investigation_v1/readonly_investigation_result_v1.json',
 'E21':B/'lqi_F0_scoring_implementation_v1/authorized_execution_v1/execution_result_v1.json',
 'E22':B/'implementation_v1/bcsp_f0_decoder_v1.py','E23':B/'implementation_v1/bcsp_f0_factory_v1.py',
 'E24':B/'lqi_implementation_v1/bcsp_lqi_decoder_v1.py','E25':B/'lqi_implementation_v1/bcsp_lqi_factory_v1.py',
 'E26':R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py',
 'E27':B/'conditional_diagnostic_implementation_v1/post_diagnostic_freeze_audit_v1/downloads/output/responses.jsonl',
 'E28':B/'lqi_F0_scoring_implementation_v1/post_scoring_freeze_audit_v1/case_level_reliability_values_v1.json',
}
for k,p in sources.items():assert p.is_file() and not p.is_symlink(),(k,p)
training={}
for name,rel in training_paths.items():
 j=read(B/rel);assert j['status'].endswith('AUDIT_PASS') and j['counts']['updates']==3900 and all(j['checks'].values())
 training[name]={k:j[k] for k in ['status','checks_passed','request_sha256','checkpoint','initialization','counts','parameters','peaks','completion']}
assert len({x['initialization']['parameter_sha256'] for x in training.values()})==1
assert len({x['initialization']['persistent_state_sha256'] for x in training.values()})==1
scoring={}
for label,code,sub in [('F0_T0_M0','E07','Native_scoring_implementation_v1'),('LQI_F0','E16','lqi_F0_scoring_implementation_v1')]:
 audit=read(sources[code]);assert audit['status'].endswith('_PASS')
 path=B/sub/'unified_scores_v1/case_metrics.jsonl';binding=next(r for r in audit['output_manifest'] if Path(r['path']).name==path.name)
 assert sha(path)==binding['sha256'] and path.stat().st_size==binding['bytes']
 rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
 scoring[label]=rows;sources['S_'+label]=path
old={(r['fold'],r['case_id'],r['arm']):r for r in scoring['F0_T0_M0']}
assert all(old[r['fold'],r['case_id'],r['arm']]==r for r in scoring['LQI_F0'] if r['arm']!='LQI')
rows=scoring['F0_T0_M0']+[r for r in scoring['LQI_F0'] if r['arm']=='LQI'];assert len(rows)==1260
assert len({(r['fold'],r['case_id'],r['arm']) for r in rows})==1260
keys=['E_P95_mm','J_P95_mm','E_coverage_2.0mm','J_coverage_2.0mm','CD_L1_mm','reverse_A2_outlier_20.0mm','centroid_offset_mm','radius_gyration_ratio']
groups={}
for row in rows:groups.setdefault((row['fold'],row['source_id'],row['arm']),[]).append(row)
assert all(len(v)==5 for v in groups.values())
source_means={k:{metric:mean([r['metrics'][metric] for r in v]) for metric in keys} for k,v in groups.items()}
summary={}
for fold in ['C','D','ALL']:
 summary[fold]={}
 for arm in ['T0','M0','F0','LQI','Nop_D','GT_8192']:
  chosen=[v for (f,src,a),v in source_means.items() if a==arm and (fold=='ALL' or f==fold)]
  case_rows=[r for r in rows if r['arm']==arm and (fold=='ALL' or r['fold']==fold)]
  summary[fold][arm]=dict(metrics={metric:mean([v[metric] for v in chosen]) for metric in keys},sources=len(chosen),cases=len(case_rows),risk={k:sum(r['risk_labels'][k] for r in case_rows) for k in ['severe_geometry','placement_tail','compact_distribution']})
responses=[json.loads(x) for x in sources['E27'].read_text().splitlines()];assert len(responses)==30
diagnostic={}
for fold in ['C','D','ALL']:
 diagnostic[fold]={}
 for kind in ['prefix_feature_null','prefix_donor','local_graph_donor']:
  part=[r for r in responses if r['label'].endswith('__'+kind) and (fold=='ALL' or r['label'].startswith(fold+'_'))]
  values=[r['dense']['world_mm']['RMSE'] for r in part]
  diagnostic[fold][kind]=dict(n=len(part),mean_mm=mean(values),min_mm=min(values),max_mm=max(values))
gpu={name:read(sources[code]) for name,code in [('F0','E03'),('LQI','E10')]}
prediction={name:read(sources[code]) for name,code in [('F0','E06'),('LQI','E15')]}
identities={}
for name,p in [('F0_C',B/'training_entry_v1/F0_FoldC_training_execution_request_v1.json'),('F0_D',B/'FoldD_training_entry_v1/F0_FoldD_training_execution_request_v1.json'),('LQI_C',B/'lqi_training_entry_v1/LQI_FoldC_training_execution_request_v1.json'),('LQI_D',B/'lqi_FoldD_training_entry_v1/failed_startup_freeze_and_bridge_fix_v2/pending_transport_v2/LQI_FoldD_training_execution_request_v2.json')]:
 identities[name]=read(p)['identity'];sources['Q_'+name]=p
assert identities['F0_C']['gpu_uuid']!=identities['LQI_C']['gpu_uuid'] and identities['F0_C']['driver_version']!=identities['LQI_C']['driver_version']
emit('verified_report_values_v1.json',dict(status='REPORT_VALUES_COMPILED_FROM_FROZEN_EVIDENCE',training=training,identities=identities,performance=summary,diagnostic=diagnostic,GPU_admission={k:{key:v[key] for key in ['status','counts'] if key in v} for k,v in gpu.items()},prediction={k:{key:v[key] for key in ['status','counts','archive'] if key in v} for k,v in prediction.items()},combined_record_count=1260,new_scoring=0,new_model_calls=0))
emit('source_evidence_manifest_v1.json',dict(status='REPORT_SOURCE_REFERENCES_HASHED',date_Asia_Shanghai='2026-11-12',sources={k:rec(p) for k,p in sources.items()},server_operations=0,checkpoint_deserialization=0,prediction_or_GT_array_reads=0,new_scoring=0))
print(json.dumps(dict(status='FROZEN_REPORT_EVIDENCE_COMPILED',sources=len(sources),training_runs=4,combined_descriptive_records=1260,formal_scoring_audits=[read(sources[k])['checks_passed'] for k in ['E07','E16']]),ensure_ascii=True))
