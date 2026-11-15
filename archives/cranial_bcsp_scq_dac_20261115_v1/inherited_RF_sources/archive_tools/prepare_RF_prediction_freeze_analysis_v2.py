from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/analyze_scq_post_prediction_freeze_v2.py').read_text(encoding='utf-8')
s=s.replace('outputs/scq_pred_freeze_20261114_v2','outputs/scq_rf_pred_freeze_20261115_v2').replace('outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/pending_request_v2','outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/pending_request_v2')
s=s.replace('ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a','5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9').replace('SCQ_BS_CD_native_prediction_execution_request_v2.json','SCQ_RF_sixmodel_native_prediction_execution_request_v2.json').replace('SCQ_BS_CD_input_index_v2.json','RF_sixmodel_input_index_v2.json').replace('bcsp_scq_fourmodel_native_predict_v2.py','bcsp_scq_rf_sixmodel_native_predict_v2.py')
s=s.replace('420','630').replace('421','631').replace('426','636').replace('434','644').replace('845','1267')
s=s.replace('native_prediction_single_attempt_claim_v2.json','attempt_claim_v2.json')
s=s.replace("len(mapping['files'])==18 and len(installed)==22", "len(mapping['files'])==20 and len(installed)==24").replace("len(meta['files'])==35", "len(meta['files'])==37")
s=s.replace('exact18_installed_and4_controls','exact20_installed_and4_controls').replace('all18_installed_files','all20_installed_files').replace('all35_metadata_copies','all37_metadata_copies')
s=s.replace("['entry','input_index','protocol','P3','resource_rebind','numeric_policy']", "['entry','input_index','protocol','P3','path_resolution','numeric_policy']")
s=s.replace('entry_index_scope_P3_rebind_numeric_bindings','entry_index_scope_P3_path_resolution_numeric_bindings')
s=s.replace("p3['status']=='LOCAL_SCQ_NATIVE_PREDICTION_P3_PASS'", "p3['status']=='LOCAL_RF_NATIVE_PREDICTION_P3_PASS'").replace("p3['CPU_checks']==22 and p3['inherited_original_CPU_checks']==42", "p3['CPU_checks']==24 and p3['inherited_CPU_checks']==51").replace('new22_and_inherited42_CPU_P3_preserved','new24_and_inherited51_CPU_P3_preserved')
start=s.index(" rebind=read(");end=s.index(" for run in idx['runs']:",start)
s=s[:start]+''' resolution=read(I/'input_path_resolution_v2.json')
 check('only_frozen_input_paths_changed_current_identity_and_D_confound_preserved',resolution['unique_cases']==210 and resolution['prediction_rows_changed']==630 and resolution['case_source_fold_order_hash_size_normalization_unchanged'] and resolution['roots']==e.DATA_ROOTS and q['identity']==e.CURRENT_IDENTITY and q['comparison_qualification']==e.QUALIFICATION and q['comparison_qualification']['strict_same_device_D_pair'] is False)
 check('frozen_index_validator_current_input_metadata',len(e.validate_index(idx,read(Path(read(B/'local_mirror_v2.json')[q['fold_binding']['path']])))[1])==630)
'''+s[end:]
s=s.replace("a['status']=='FORMAL_SCQ_POST_TRAINING_FREEZE_AUDIT_PASS'", "a['status']==e.FROZEN_MODELS[run['label']]['audit_status']").replace("a['identity']==q['training_identity']", "a['identity']==e.FROZEN_MODELS[run['label']]['identity']").replace('all4_training_freezes','all6_training_freezes')
s=s.replace('SCQ_BS_CD_630_NATIVE_FORWARD_COMPLETE','SCQ_RF_SIXMODEL_630_NATIVE_FORWARD_COMPLETE')
start=s.index(" for f in 'CD':");end=s.index(" check('all630_saved_arrays",start)
s=s[:start]+''' for f in 'CD':
  parts=[[v for v in manifest if v['run']==arm+'_'+f] for arm in ['Sref','Static','Requery']]
  assert all(all(x[k]==y[k]==z[k] for k in ['case_id','source_id','input_sha256','normalization']) for x,y,z in zip(*parts))
 check('three_arms_same_fold_paired_inputs_frames_order',len({r['input']['path'] for r in idx['inputs']})==210)
'''+s[end:]
s=s.replace("len(models)==4 and [m['run'] for m in models]==['B_C','S_C','B_D','S_D']", "len(models)==6 and [m['run'] for m in models]==['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D']").replace('four_models_in_fixed_order','six_models_in_fixed_order')
s=s.replace("ev=m['construction'];v=ev['parent'];s=ev['scq'];arm=runs[m['run']]['variant']", "ev=m['construction'];is_rf='rf' in ev;scq_ev=ev['parent'] if is_rf else ev;v=scq_ev['parent'];s=scq_ev['scq'];arm=runs[m['run']]['variant'];assert is_rf is (arm!='S')")
s=s.replace("s['variant']==arm", "s['variant']=='S'")
s=s.replace("assert s['new_parameters']==(0 if arm=='B' else 693507) and s['total_parameters']==(39903169 if arm=='B' else 40596676)\n  if arm=='S':assert s['initialization_sha256']==q['initialization']['sha256']", "assert s['new_parameters']==693507 and s['total_parameters']==40596676 and s['initialization_sha256']==q['initialization']['sha256']\n  if is_rf:\n   rf=ev['rf'];assert rf['variant']==arm and rf['additional_parameters']==231171 and rf['total_parameters']==40827847 and rf['initialization_sha256']==q['rf_initialization']['sha256'] and rf['common_state_preserved'] and rf['CPU_RNG_preserved']")
s=s.replace('all4_parameter','all6_parameter').replace('all4_CPU','all6_CPU').replace('actual_native_LQI_SCQ_construction','actual_native_LQI_SCQ_RF_construction')
s=s.replace("['B_C','S_C','B_D','S_D']", "['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D']")
s=s.replace("len(assets)==14 and len(cps)==4", "len(assets)==15 and len(cps)==6").replace('assets_four_checkpoints','assets_six_checkpoints')
s=s.replace("status='FORMAL_SCQ_BS_CD_POST_PREDICTION_FREEZE_AUDIT_PASS',date='2026-11-14'", "status='FORMAL_SCQ_RF_SIXMODEL_POST_PREDICTION_FREEZE_AUDIT_PASS',date='2026-11-15'")
s=s.replace("training_identity=q['training_identity']", "training_identities={k:v['identity'] for k,v in e.FROZEN_MODELS.items()},comparison_qualification=q['comparison_qualification']")
s=s.replace('counts=dict(models=4','counts=dict(models=6').replace('installed_files=18','installed_files=20')
s=s.replace('BCSP_FULLMAMBA_SCQ/2026-11-14_native_development_eval','BCSP_FULLMAMBA_SCQ_RF/2026-11-15_native_development_eval')
s=s.replace("'Training and prediction GPU UUID/driver differ; no cross-driver bitwise-equivalence assertion.'", "'D Static training GPU UUID/driver differ from D Sref/Requery; D comparison is supplementary device-confounded evidence, C remains same-device primary mechanism evidence. All six predictions use the same current device.'")
s=s.replace("'Long local save path failure preserved; metadata copied from existing raw return into short directory, no repeated prediction.'", "'Previous v1 input-path failure preserved. This audit targets only the authorized successful v2 prediction; no repeated model inference.'")
needle=" check('all6_parameter_and_persistent_BN_fingerprints_unchanged',True)"
s=s.replace(needle," check('all630_RF_stage_centroids_independently_recomputed',read(F/'RF_stages_result_v1.json')['status']=='ALL630_RF_STAGE_CENTROID_LOGS_RECOMPUTED_PASS')\n"+needle)
ast.parse(s);compile(s,'RF_audit_analysis','exec')
p=R/'local_tools/analyze_RF_post_prediction_freeze_v2.py'
with p.open('x',encoding='utf-8') as f:f.write(s)
print(p)
