from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/freeze_scq_BS_scoring_P3_request_v1.py').read_text(encoding='utf-8')
s=s.replace('outputs/scq_score_impl_20261114_v1','outputs/scq_rf_score_impl_20261115_v1').replace('outputs/scq_score_prep_20261114_v1','outputs/scq_rf_score_prep_20261115_v1').replace('outputs/scq_pred_freeze_20261114_v2','outputs/scq_rf_pred_freeze_20261115_v2')
s=s.replace("OLD=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_scoring_implementation_v1'", "OLD=R/'outputs/scq_score_impl_20261114_v1'")
s=s.replace('bcsp_scq_BS_two_arm_score_v1.py','bcsp_scq_rf_three_arm_score_v1.py').replace('test_scq_BS_score_cpu_v1.py','test_RF_three_arm_score_cpu_v1.py')
s=s.replace('SCQ_BS_SCORING_CPU_CONTRACT_PASS','RF_THREE_ARM_SCORING_CPU_CONTRACT_PASS').replace('==43','==48').replace('CPU_tests=43','CPU_tests=48').replace('synthetic_actual_metric_rows=8','synthetic_actual_metric_rows=10').replace("result['synthetic_actual_metric_rows']==8", "result['synthetic_actual_metric_rows']==10").replace('synthetic_orchestrated_rows=840','synthetic_orchestrated_rows=1050').replace("result['synthetic_orchestrated_rows']==840", "result['synthetic_orchestrated_rows']==1050")
s=s.replace("OLD/'bcsp_lqi_F0_two_arm_score_v1.py'", "OLD/'bcsp_scq_BS_two_arm_score_v1.py'")
s=s.replace('SCQ_BS_score_case_index_candidate_v1.json','RF_three_arm_score_case_index_candidate_v1.json').replace('SCQ_BS_unified_CPU_scoring_scope_v1.json','RF_three_arm_unified_CPU_scoring_scope_v1.json')
s=s.replace('LOCAL_SCQ_FOUR_FILES_ALL426_MEMBERS_VERIFIED','LOCAL_SCQ_RF_FOUR_FILES_ALL636_MEMBERS_VERIFIED')
s=s.replace('model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168','model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210')
s=s.replace('bcsp-scq-BS-local-scoring-protocol-v1','bcsp-scq-rf-local-scoring-protocol-v1').replace('LOCAL_SCQ_BS_SCORING_P3_PASS','LOCAL_SCQ_RF_SCORING_P3_PASS')
s=s.replace('one_SCQ_archive_exact426_members','one_RF_archive_exact636_members').replace('strict_four_keys_and_B_zero_delta','strict_nine_keys_and_RF_stage_equations').replace('actual210_case420_prediction_metadata','actual210_case630_prediction_metadata').replace('synthetic840_case168_source_orchestration','synthetic1050_case210_source_orchestration')
s=s.replace("date='2026-11-14'", "date='2026-11-15'").replace("date_Asia_Shanghai='2026-11-14'", "date_Asia_Shanghai='2026-11-15'")
s=s.replace('bcsp-scq-BS-local-scoring-request-v1','bcsp-scq-rf-local-scoring-request-v1').replace('bcsp-scq-BS-score-authorization-v1','bcsp-scq-rf-score-authorization-v1')
s=s.replace('Frozen Native SCQ B/S C/D paired CPU scores; no new inference','Frozen Native SCQ-RF S-ref/Static/Requery C/D CPU scores; no new inference')
s=s.replace('SCQ_BS_CD_input_index_v2.json','RF_sixmodel_input_index_v2.json').replace('SCQ_BS_CD_native_scope_v1.json','RF_sixmodel_native_scope_v1.json')
s=s.replace("q['archive_inputs']={'SCQ':", "q['archive_inputs']={'SCQ_RF':").replace('ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a','5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')
s=s.replace('formal_SCQ_prediction_audit','formal_RF_prediction_audit')
start=s.index("q['scientific_contract']=")
end=s.index("q['future_authorization']=",start)
s=s[:start]+'''q['comparison_qualification']=scope['comparison_qualification']
q['scientific_contract']=dict(arms=['S-ref','RF-Static','RF-Requery'],controls=['Nop_D','GT_8192'],pairs=[['RF-Static','RF-Requery'],['S-ref','RF-Static'],['S-ref','RF-Requery']],delta='candidate minus baseline; negative error and positive coverage indicate improvement',primary='A1 area-weighted E_P95; five defects/source then21 sources equally/fold',geometry=oldq['scientific_contract']['geometry'],risk=oldq['scientific_contract']['risk'],alignment='Native world mm; no GT registration/ICP/postfilter',coarse='Actual Qused256 and P8192 in all630 Native predictions; validate nine saved keys and stage equations without replacing Native output',baseline_archive_handling='One frozen RF archive;630 model rows plus420 shared controls once/case; recomputed controls must exactly equal previously frozen values',diagnostic_cache='No context/full decoder trace; exact empty cache log only',archive_member_byte_limit=scope['archive_binding']['uncompressed_member_bytes'],comparison_qualification=scope['comparison_qualification'])
'''+s[end:]
s=s.replace('SCQarchive','RFarchive').replace('before SCQ B/S effect interpretation','before RF three-arm effect interpretation')
s=s.replace("env=dict(json=json,ARMS=['B','S'],PAIRS=[('B','S')],CONTROLS=['Nop_D','GT_8192'])", "env=dict(json=json,ARMS=['S-ref','RF-Static','RF-Requery'],PAIRS=[('RF-Static','RF-Requery'),('S-ref','RF-Static'),('S-ref','RF-Requery')],CONTROLS=['Nop_D','GT_8192'],QUALIFICATION=scope['comparison_qualification'])")
s=s.replace("checks=dict(final_source_CPU_static_bound=True,", "checks=dict(three_fixed_comparisons_and_D_device_qualification_preserved=True,verified_archive_footprint_bound=True,final_source_CPU_static_bound=True,")
ast.parse(s);compile(s,'RF_score_freezer','exec')
p=R/'local_tools/freeze_RF_scoring_P3_request_v1.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
