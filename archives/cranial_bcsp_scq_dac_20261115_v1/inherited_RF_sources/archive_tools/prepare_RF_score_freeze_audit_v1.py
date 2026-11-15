from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/audit_scq_BS_scores_v1.py').read_text(encoding='utf-8')
s=s.replace('outputs/scq_score_impl_20261114_v1','outputs/scq_rf_score_impl_20261115_v1').replace('outputs/scq_score_freeze_20261114_v1','outputs/scq_rf_score_freeze_20261115_v1').replace('7e5cb8f286e215b4b1712254d7c1068a5bc5d4048a8ec128fa446997a3ef4ad9','284b215e16c3e394db4e30420cd8ca309cfa9f09d9831573c9329b28d7e8e7f4')
s=s.replace("ARMS=['B','S'];PAIRS=[('B','S')]", "ARMS=['S-ref','RF-Static','RF-Requery'];PAIRS=[('RF-Static','RF-Requery'),('S-ref','RF-Static'),('S-ref','RF-Requery')]")
s=s.replace('LOCAL_SCQ_BS_SCORING_P3_PASS','LOCAL_SCQ_RF_SCORING_P3_PASS').replace("p3['CPU_tests']==43", "p3['CPU_tests']==48").replace('SCQ_BS_SCORING_CPU_CONTRACT_PASS','RF_THREE_ARM_SCORING_CPU_CONTRACT_PASS').replace('final_P3_and43','final_P3_and48')
s=s.replace('bcsp-scq-BS-score-authorization-v1','bcsp-scq-rf-score-authorization-v1').replace('LOCAL_SCQ_BS_TWO_ARM_TWOFOLD_CPU_SCORING_COMPLETE','LOCAL_SCQ_RF_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE')
s=s.replace('[420,420,840,168]','[630,420,1050,210]').replace('len(rows)==len(lookup)==840','len(rows)==len(lookup)==1050').replace('len(expected)==168','len(expected)==210')
s=s.replace('outputs/scq_pred_freeze_20261114_v2','outputs/scq_rf_pred_freeze_20261115_v2').replace("need(len(part)==420,'420 Native geometry summaries')", "need(len(part)==630,'630 Native geometry summaries')")
s=s.replace("g=native[r['arm'],r['arm']+'_'+r['fold'],r['case_id']]", "prefix={'S-ref':'Sref','RF-Static':'Static','RF-Requery':'Requery'}[r['arm']];g=native[prefix,prefix+'_'+r['fold'],r['case_id']]")
s=s.replace("comparison['status']=='SCQ_BS_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS' and comparison['fixed_comparisons']==['S_minus_B']", "comparison['status']=='SCQ_RF_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS' and comparison['fixed_comparisons']==[b+'_minus_'+a for a,b in PAIRS]")
s=s.replace("comparison['model_predictions']==420", "comparison['model_predictions']==630")
s=s.replace("==[210,210]", "==[210,210,210]")
s=s.replace('FORMAL_SCQ_BS_POST_SCORING_FREEZE_AUDIT_PASS','FORMAL_SCQ_RF_POST_SCORING_FREEZE_AUDIT_PASS').replace('model_scores=420,controls=420,case_rows=840,source_rows=168,source_pair_summaries=2,case_pair_deltas=210','model_scores=630,controls=420,case_rows=1050,source_rows=210,source_pair_summaries=6,case_pair_deltas=630')
s=s.replace('completion840case168source','completion1050case210source').replace('ordered840_unique','ordered1050_unique').replace('all840_selected','all1050_selected').replace('168_independently','210_independently').replace('actual420_coarse','actual630_coarse').replace('two_risk_tables','six_risk_tables').replace('one_fixed_descriptive_comparison','three_fixed_descriptive_comparisons').replace('rankings210_case_deltas_and10_defect','rankings630_case_deltas_and30_defect')
s=s.replace("'Both arms have210 actual Qused tensors.", "'All three arms each have210 actual Qused tensors.")
needle="  equal(result['completion'],complete);"
s=s.replace(needle,"""  qualification=dict(C_pair='SAME_DEVICE_PRIMARY_MECHANISM_EVIDENCE',D_Static_vs_Requery='DEVICE_AND_DRIVER_CONFOUNDED_SUPPLEMENTARY_EVIDENCE',strict_same_device_D_pair=False,do_not_attribute_all_differences_to_requery=True)
  good('D_device_driver_confound_and_C_primary_qualification_preserved',q['comparison_qualification']==qualification and complete['comparison_qualification']==qualification)
  equal(result['completion'],complete);""")
needle="  for f in ids:\n   defects[f]={}"
s=s.replace(needle,"  good('paired_summary_D_confound_qualification_not_dropped',comparison['comparison_qualification']==qualification)\n"+needle)
s=s.replace("formal_gate=False,limitations=", "formal_gate=False,comparison_qualification=qualification,limitations=")
s=s.replace("'Single seed/fold, repeated development data; no significance/bootstrap/clinical or formal gate claim'", "'One seed per fold, repeated development data; no significance/bootstrap/clinical or formal gate claim; D Static comparisons device/driver-confounded, C same-device pair primary.'")
ast.parse(s);compile(s,'RF_score_audit','exec')
p=R/'local_tools/audit_RF_three_arm_scores_v1.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
