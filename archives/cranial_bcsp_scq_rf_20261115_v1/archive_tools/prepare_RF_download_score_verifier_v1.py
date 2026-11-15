from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/verify_scq_download_prepare_scoring_v1.py').read_text(encoding='utf-8')
s=s.replace('outputs/scq_score_prep_20261114_v1','outputs/scq_rf_score_prep_20261115_v1').replace('outputs/scq_pred_freeze_20261114_v2','outputs/scq_rf_pred_freeze_20261115_v2').replace('BCSP_FULLMAMBA_SCQ/2026-11-14_native_development_eval','BCSP_FULLMAMBA_SCQ_RF/2026-11-15_native_development_eval')
s=s.replace("OLD=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_scoring_implementation_v1'", "OLD=R/'outputs/scq_score_impl_20261114_v1'")
s=s.replace('FORMAL_SCQ_BS_CD_POST_PREDICTION_FREEZE_AUDIT_PASS','FORMAL_SCQ_RF_SIXMODEL_POST_PREDICTION_FREEZE_AUDIT_PASS').replace('426','636')
s=s.replace("len(inference)==420", "len(inference)==630").replace("['B_C','S_C','B_D','S_D']", "['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D']")
s=s.replace('LOCAL_SCQ_FOUR_FILES_ALL636_MEMBERS_VERIFIED','LOCAL_SCQ_RF_FOUR_FILES_ALL636_MEMBERS_VERIFIED').replace('predictions=420','predictions=630')
s=s.replace('SCQ_BS_input_index_v2.json','RF_sixmodel_input_index_v2.json').replace('SCQ_BS_native_prediction_execution_request_v2.json','SCQ_RF_sixmodel_native_prediction_execution_request_v2.json')
s=s.replace("len(imap)==len(predmap)==420", "len(imap)==len(predmap)==630")
s=s.replace("for arm in ['B','S']:", "for arm,variant in [('S-ref','S'),('RF-Static','RF-Static'),('RF-Requery','RF-Requery')]:")
s=s.replace("row=imap[c['fold'],arm,c['case_id']];pred=predmap[c['fold'],arm,c['case_id']]", "row=imap[c['fold'],variant,c['case_id']];pred=predmap[c['fold'],variant,c['case_id']]")
s=s.replace("archive_key='SCQ'", "archive_key='SCQ_RF'").replace("coarse_saved=True,Qraw_saved=True,delta_saved=True", "coarse_saved=True,Qraw_saved=True,delta_saved=True,RF_stage_arrays_saved=True,native_variant=variant")
s=s.replace("len(predictions)==len({(r['arm'],r['fold'],r['case_id']) for r in predictions})==420", "len(predictions)==len({(r['arm'],r['fold'],r['case_id']) for r in predictions})==630")
s=s.replace('model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168','model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210')
s=s.replace('bcsp-scq-BS-twofold-score-index-candidate-v1','bcsp-scq-rf-three-arm-twofold-score-index-candidate-v1').replace("archive_inputs={'SCQ':files}", "archive_inputs={'SCQ_RF':files}").replace("model_arms=['B','S']", "model_arms=['S-ref','RF-Static','RF-Requery']")
s=s.replace('SCQ_BS_score_case_index_candidate_v1.json','RF_three_arm_score_case_index_candidate_v1.json')
oldscope="R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_F0_scoring_preparation_v1/LQI_F0_unified_scoring_scope_v1.json'"
newscope="R/'outputs/scq_score_prep_20261114_v1/SCQ_BS_unified_CPU_scoring_scope_v1.json'"
s=s.replace(oldscope,newscope)
s=s.replace('bcsp-scq-BS-local-scoring-protocol-v1','bcsp-scq-rf-local-scoring-protocol-v1').replace("arms=['B','S']", "arms=['S-ref','RF-Static','RF-Requery']").replace("paired_directions=['S minus B']", "paired_directions=['RF-Requery minus RF-Static','RF-Static minus S-ref','RF-Requery minus S-ref']")
s=s.replace('All420 Native outputs have actual Qused256/P8192 and same-forward Qraw256/delta256; preserve original metrics.', 'All630 Native outputs have actual Qused256/P8192 and same-forward Q0/Q1/Q2/delta0/delta1; score Native dense and actual coarse with unchanged metrics.')
start=s.index(" protocol['scientific_constraints']=")
end=s.index(" emit('SCQ_BS_unified_CPU_scoring_scope_v1.json'",start)
s=s[:start]+''' protocol['scientific_constraints']=['Same210 opened cases/42sources; no model-outcome selection','Fixed reference bank/metric code/thresholds; D-only inverse normalization to world mm','630 model rows plus420 shared controls counted once per case, total1050; five defects/source equally weighted','C and D separately, then descriptive pooled source-equal summaries; cases are not independent patients','Core contrast RF-Requery minus RF-Static; both versus S-ref are supporting comparisons','C same-device pair is primary mechanism evidence. D Static training GPU/driver differs; D and pooled contrasts must disclose confounding','No registration/Oracle/TTA/postfilter/bootstrap/p-values/formal gate or parameter search','Qraw/stage arrays are diagnostics, never substitute corrected outputs for Native scores','Separate three-arm entry/artificial CPU tests/P3 and separate full-hash execution authorization before scoring']
 protocol['comparison_qualification']=audit['comparison_qualification']
 protocol['archive_binding']=dict(archive_bytes=archive.stat().st_size,uncompressed_member_bytes=total,archive_members=636,source='All636 members independently streamed and hash matched; freeze exact observed archive footprint, do not reuse old64MiB ceiling.')
 protocol['budget_reason']='Retain inherited18000-second/two-thread/8GiB RSS/2GiB output CPU budget for1050 rows; no extra cases or metric changes. Actual runtime remains unknown until execution.'
'''+s[end:]
s=s.replace('SCQ_BS_unified_CPU_scoring_scope_v1.json','RF_three_arm_unified_CPU_scoring_scope_v1.json')
start=s.index(' assert "ARMS=')
end=s.index(" emit('preparation_validation_receipt_v1.json'",start)
s=s[:start]+''' assert "ARMS=['B','S']" in src and "keys=['prediction','coarse','Qraw','delta']" in src and '67108864' in src
 emit('scorer_compatibility_review_v1.json',dict(status='DEDICATED_RF_THREE_ARM_ENTRY_REQUIRED',existing_scorer=record(scorer),frozen_metric=metric,gaps=['Old B/S labels, two-arm lookup and840-row contract require S-ref/Static/Requery dispatch and1050 rows','RF six-model index,630 records,636 archive members and nested RF construction schema require precise validation','Prediction loader must validate nine saved keys and Q0/Q1/Q2 equations, scoring only Native prediction and actual coarse','Old uncompressed64MiB archive cap is smaller than verified current archive members; freeze exact observed bytes rather than reuse it blindly','Preserve metrics, references, thresholds, five-defect/source aggregation, controls once per case, and explicit D device confound','Full authorization/accounting plus targeted artificial CPU tests/P3 before final score request'],metric_or_threshold_changes=False,production_source_changes=0,scoring=0,request_created=False))
'''+s[end:]
s=s.replace('LOCAL_SCQ_BACKUP_VERIFIED_AND_CPU_SCORE_SCOPE_PREPARED_NOT_EXECUTED','LOCAL_RF_BACKUP_VERIFIED_AND_CPU_SCORE_SCOPE_PREPARED_NOT_EXECUTED').replace('LOCAL_SCQ_BACKUP_VERIFIED_SCORE_SCOPE_PREPARED','LOCAL_RF_BACKUP_VERIFIED_SCORE_SCOPE_PREPARED')
ast.parse(s);compile(s,'RF_download_verify','exec')
p=R/'local_tools/verify_RF_download_prepare_scoring_v1.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
