from pathlib import Path
import ast
R=Path(__file__).resolve().parent.parent
s=(R/'local_tools/freeze_RF_Static_C_P3_request_v1.py').read_text(encoding='utf-8')
for old,new in [('scq_rf_Static_C_implementation_20261114_v1','scq_rf_Requery_C_implementation_20261114_v1'),('bcsp_scq_rf_Static_C_training_20261114_v1','bcsp_scq_rf_Requery_C_training_20261114_v1'),('bcsp_scq_rf_Static_C_training_entry_v1','bcsp_scq_rf_Requery_C_training_entry_v1'),('bcsp_scq_rf_Static_C_training_bridge_v1','bcsp_scq_rf_Requery_C_training_bridge_v1'),('test_RF_Static_C_entry_cpu_v1','test_RF_Requery_C_entry_cpu_v1'),('cpu_static_entry_batch_v1','cpu_requery_entry_batch_v1'),('RF_STATIC_C','RF_REQUERY_C'),('Static_C_final_metadata_only','Requery_C_final_metadata_only'),('STATIC_C_FINAL_AUTHORIZE','REQUERY_C_FINAL_AUTHORIZE'),('STATIC_C_LOCAL_P3','REQUERY_C_LOCAL_P3'),('SCQ_RF_Static_C_training_execution_request_v1','SCQ_RF_Requery_C_training_execution_request_v1'),('bcsp_scq_rf_Static_C_pending','bcsp_scq_rf_Requery_C_pending'),('CPU_checks=43','CPU_checks=49'),('==43','==49')]:s=s.replace(old,new)
s=s.replace("admission['models'][1]['phase']=='Static_eval1' and admission['models'][1]['parameters']==40827847 and admission['models'][1]['shared_initial_state_SHA256']", "admission['models'][2]['phase']=='Requery_eval1' and admission['models'][2]['parameters']==40827847 and admission['models'][2]['shared_initial_state_SHA256']")
s=s.replace("old=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3/bcsp_scq_rf_Sref_C_training_entry_v3.py'", "old=R/'outputs/scq_rf_Static_C_implementation_20261114_v1/bcsp_scq_rf_Static_C_training_entry_v1.py'")
s=s.replace("unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','make_budget']", "unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','make_budget','startup_read_records','validate_reference','validate_admission']")
s=s.replace('all43_artificial_CPU_pass=True','all49_artificial_CPU_pass=True').replace('Static_N0_and_Q1_relative_geometry=True','Requery_N1_and_Q1_relative_geometry=True,Static_and_Sref_frozen_references=True,full_initial_state_match_required_before_native_training=True,fixed_changed_neighbor_fixture=True')
needle="emit(O/'training_entry_P3_v1.json',p3)"
s=s.replace(needle,"""sr=q['paired_static'];static_audit_path=mirror[sr['audit']['path']];static_audit=read(static_audit_path)
assert static_audit['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and static_audit['check_count']==34 and all(static_audit['checks'].values())
assert q['expected_full_initialization']==static_audit['initialization'] and static_audit['common_initial_state_SHA256']==ctx['expected_common']
p3['Static_formal_freeze']=sr['audit'];p3['expected_full_initialization']=q['expected_full_initialization']
"""+needle)
s=s.replace("shutil.copyfile(cpu_path,P/'training_CPU_result_v1.json');shutil.copyfile(mirror[q['paired_baseline']['audit']['path']],P/'Sref_C_formal_freeze_v1.json')", """shutil.copyfile(cpu_path,P/'training_CPU_result_v1.json');shutil.copyfile(mirror[q['paired_baseline']['audit']['path']],P/'Sref_C_formal_freeze_v1.json')
shutil.copyfile(static_audit_path,P/'Static_C_formal_freeze_v1.json')
q['paired_baseline']['audit']=rec(P/'Sref_C_formal_freeze_v1.json',C+'/Sref_C_formal_freeze_v1.json');mirror[q['paired_baseline']['audit']['path']]=P/'Sref_C_formal_freeze_v1.json'
q['paired_static']['audit']=rec(P/'Static_C_formal_freeze_v1.json',C+'/Static_C_formal_freeze_v1.json');mirror[q['paired_static']['audit']['path']]=P/'Static_C_formal_freeze_v1.json'""")
s=s.replace('all8 new targets','all9 new targets').replace('fresh from-scratch','fresh from-scratch')
s=s.replace('Fresh from-scratch paired RF-Static_C; never load Sref final checkpoint.', 'Fresh from-scratch paired RF-Requery_C; never load Sref or Static final checkpoint; bind identical full initial parameter/buffer fingerprints.')
s=s.replace("*[v for k,v in q['paired_baseline'].items() if k!='audit']", "*[v for k,v in q['paired_baseline'].items() if k!='audit'],*[v for k,v in q['paired_static'].items() if k!='audit']")
s=s.replace("assert len(mapping['files'])==8", "assert len(mapping['files'])==9")
s=s.replace('len(members)==9','len(members)==10').replace('install_files=8,archive_members=9','install_files=9,archive_members=10')
needle="assert q['output']!=parent['output'] and q['launch_contract']['tmux_session']!=parent['launch_contract']['tmux_session']"
s=s.replace(needle,needle+"\nstatic_request=read(mirror[q['paired_static']['request']['path']]);assert q['rf_initialization']==static_request['rf_initialization'] and q['output']!=static_request['output'] and q['launch_contract']['tmux_session']!=static_request['launch_contract']['tmux_session']")
p=R/'local_tools/freeze_RF_Requery_C_P3_request_v1.py';ast.parse(s);compile(s,str(p),'exec')
with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('REQUERY_C_LOCAL_P3_AND_FREEZE_DRIVER_PREPARED')
