from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
src=(R/'local_tools/freeze_RF_native_prediction_request_v1.py').read_text(encoding='utf-8')
src=src.replace("S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1'", "S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2';PARENT=S.parent")
src=src.replace("context_v1.json","context_v2.json").replace('bcsp_scq_rf_sixmodel_native_predict_v1.py','bcsp_scq_rf_sixmodel_native_predict_v2.py').replace('test_RF_native_prediction_cpu_v1.py','test_RF_input_path_cpu_v2.py').replace('artificial_cpu_batch_v1/result_v1.json','CPU_contract_v2/result_v2.json').replace('static_review_v1.json','static_review_v2.json')
start=src.index("assert result['status']")
end=src.index("emit(S/'implementation_P3_v1.json'",start)
replacement='''assert result['status']=='RF_INPUT_PATH_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==len(set(result['checks']))==24 and not (cpu.parent/'failure_v2.json').exists()
assert result['entry']==rec(entry)==static['entry'] and result['test']==rec(test)
assert static['status']=='STATIC_S0_S1_PASS' and static['all_functions_and_classes_AST_identical'] and static['all_other_constants_AST_identical']
old=PARENT/'bcsp_scq_rf_sixmodel_native_predict_v1.py'
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert nodes(old)==nodes(entry)
oldp3=read(PARENT/'implementation_P3_v1.json');oldcpu=read(PARENT/'artificial_cpu_batch_v1/result_v1.json')
assert oldcpu['checks_passed']==51 and oldcpu['status']=='RF_NATIVE_CPU_CONTRACT_PASS' and all(oldp3['checks'].values()) and oldcpu['entry']==rec(old)
assert result['inherited_CPU_result']==rec(PARENT/'artificial_cpu_batch_v1/result_v1.json') and result['inherited_P3']==rec(PARENT/'implementation_P3_v1.json')
p3=copy.deepcopy(oldp3);p3.update(entry_sha256=rec(entry)['sha256'],test_sha256=rec(test)['sha256'],CPU_checks=24,CPU_result=rec(cpu),inherited_CPU_checks=51,inherited_CPU_result=rec(PARENT/'artificial_cpu_batch_v1/result_v1.json'),inherited_P3=rec(PARENT/'implementation_P3_v1.json'),static_review=rec(S/'static_review_v2.json'),changed_functions=[],changed_constants=['INDEX_SHA','DATA_ROOTS'],all_production_function_class_AST_unchanged=True,input_path_resolution=rec(S/'input_path_resolution_v2.json'))
p3['checks'].update(path_only24_CPU_checks_pass=True,all630_occurrences_only_path_changed=True,all210_unique_path_hashes_readonly_verified=True,all_functions_AST_identical=True,old_roots_and_wrong_fold_hash_budget_denied=True,final_v2_authorize_path_tested=True)
p3['limitations']+=['Only24 path/authorization/metadata checks rerun; previous51 and630 artificial forwards inherited by exact AST/source preservation.','No server calls or arrays in this implementation; fresh server identity/input/asset/checkpoint checks are mandatory at activation.']
'''
src=src[:start]+replacement+src[end:]
src=src.replace('implementation_P3_v1.json','implementation_P3_v2.json')
# Parent v1 evidence must keep its actual filename.
src=src.replace("PARENT/'implementation_P3_v2.json'", "PARENT/'implementation_P3_v1.json'")
src=src.replace("O=S/'pending_request_v1'", "O=S/'pending_request_v2'").replace('RF_sixmodel_input_index_v1.json','RF_sixmodel_input_index_v2.json')
src=src.replace("S/'RF_sixmodel_native_scope_v1.json'", "PARENT/'RF_sixmodel_native_scope_v1.json'")
src=src.replace("(cpu,'CPU_contract_result_v1.json')", "(cpu,'CPU_contract_result_v2.json')")
src=src.replace("(cpu.parent/'source_policy_stdout.bin','source_policy_result_v1.json')", "(PARENT/'artificial_cpu_batch_v1/source_policy_stdout.bin','source_policy_result_v1.json')")
src=src.replace("for label,path in ctx['audit_local_files'].items():q['training_audits'][label]=stage(Path(path),'frozen_'+label+'_training_audit_v1.json')", "for label,r in list(q['training_audits'].items()):q['training_audits'][label]=stage(Path(mirror[r['path']]),'frozen_'+label+'_training_audit_v1.json')\nq['path_resolution']=stage(S/'input_path_resolution_v2.json')\nresolution=read(S/'input_path_resolution_v2.json');stage(Path(resolution['observation']['path']),'input_path_readonly_observation_v1.json')\nstage(PARENT/'implementation_P3_v1.json','inherited_implementation_P3_v1.json');stage(PARENT/'artificial_cpu_batch_v1/result_v1.json','inherited_CPU_contract_result_v1.json')")
src=src.replace('SCQ_RF_sixmodel_native_prediction_execution_request_v1.json','SCQ_RF_sixmodel_native_prediction_execution_request_v2.json')
src=src.replace("S/'RF_sixmodel_input_index_v2.json'", "S/'RF_sixmodel_input_index_v2.json'")
src=src.replace('installation_mapping_v1.json','installation_mapping_v2.json').replace('bcsp_scq_rf_sixmodel_native_pending_20261115_v1.tar.gz','bcsp_scq_rf_sixmodel_native_pending_20261115_v2.tar.gz').replace('local_mirror_v1.json','local_mirror_v2.json').replace('final_static_freeze_v1.json','final_static_freeze_v2.json').replace('delivery_receipt_v1.json','delivery_receipt_v2.json').replace('CPU_checks=51','CPU_checks=24,inherited_CPU_checks=51')
# Versioned protocol is unchanged byte content; no numeric or science modifications.
ast.parse(src)
p=R/'local_tools/freeze_RF_input_path_request_v2_generated.py'
with p.open('x',encoding='utf-8') as f:f.write(src)
print(p)
